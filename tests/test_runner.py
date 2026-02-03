"""Tests for replay runner ordering and determinism."""

from __future__ import annotations

import io
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src import runner


@dataclass
class RecordingPolicy:
    agent_id: str
    order: list[str]

    def act(self, obs: Any, ctx: dict[str, Any]) -> str:
        self.order.append(f"act:{self.agent_id}")
        return f"action:{self.agent_id}"


@dataclass
class RecordingEnv:
    order: list[str]

    def reset(self, init: Any, rng: random.Random) -> dict[str, Any]:
        return {"t": 0}

    def observe(self, state: dict[str, Any]) -> dict[str, Any]:
        self.order.append("observe")
        return {"agent1": {"t": state["t"]}, "agent2": {"t": state["t"]}}

    def validate_action(
        self, state: dict[str, Any], agent_id: str, action: Any
    ) -> runner.ValidationResult:
        self.order.append(f"validate:{agent_id}")
        return runner.ValidationResult(ok=True)

    def step(
        self,
        state: dict[str, Any],
        joint_action: dict[str, Any],
        exogenous_x_t: Any,
        rng: random.Random,
    ) -> tuple[dict[str, Any], int, int, dict[str, Any]]:
        self.order.append("transition")
        return {"t": state["t"] + 1}, 1, 0, {"done": True}


@dataclass
class RecordingMetrics:
    order: list[str]

    def per_step(
        self,
        t: int,
        state_hash_pre: str,
        action: dict[str, Any],
        reward: Any,
        cost: Any,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        self.order.append("score")
        return {"t": t}

    def aggregate(self, contribs_stream: Any) -> dict[str, Any]:
        return {"count": len(list(contribs_stream))}


class RecordingStream(io.StringIO):
    def __init__(self, order: list[str]) -> None:
        super().__init__()
        self.order = order

    def write(self, s: str) -> int:
        if s.strip():
            self.order.append("log")
        return super().write(s)


def test_step_ordering_and_tie_break() -> None:
    order: list[str] = []
    env = RecordingEnv(order)
    policies: dict[str, runner.Policy] = {
        "agent2": RecordingPolicy("agent2", order),
        "agent1": RecordingPolicy("agent1", order),
    }
    metrics = RecordingMetrics(order)
    out = RecordingStream(order)
    config = runner.RunConfig(
        env=env,
        policies=policies,
        metrics=metrics,
        trace=[{"x": 1}],
        seed=1,
        init={},
        out=out,
        run_dir=Path("/tmp/unused"),
    )
    handle = runner.run(config)
    assert handle.exit_code == 0
    assert order == [
        "observe",
        "act:agent1",
        "act:agent2",
        "validate:agent1",
        "validate:agent2",
        "transition",
        "score",
        "log",
    ]


def test_state_hash_deterministic() -> None:
    first = runner.state_hash({"b": 1, "a": 2})
    second = runner.state_hash({"a": 2, "b": 1})
    assert first == second
    assert first == runner.state_hash({"a": 2, "b": 1})
