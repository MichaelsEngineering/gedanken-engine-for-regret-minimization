"""Fixtures for CLI integration tests."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from src import runner


@dataclass
class DummyEnv:
    """Minimal deterministic environment."""

    agent_ids: list[str]

    def reset(self, init: Any, rng: random.Random) -> dict[str, Any]:
        return {"t": 0, "done": False, "init": init}

    def observe(self, state: dict[str, Any]) -> dict[str, Any]:
        return {agent_id: {"t": state["t"]} for agent_id in self.agent_ids}

    def validate_action(
        self, state: dict[str, Any], agent_id: str, action: Any
    ) -> runner.ValidationResult:
        return runner.ValidationResult(ok=True)

    def step(
        self,
        state: dict[str, Any],
        joint_action: dict[str, Any],
        exogenous_x_t: Any,
        rng: random.Random,
    ) -> tuple[dict[str, Any], int, int, dict[str, Any]]:
        next_state = {"t": state["t"] + 1, "done": True}
        info = {"done": True}
        return next_state, 1, 0, info


@dataclass
class DummyPolicy:
    """Deterministic policy that echoes observations."""

    agent_id: str

    def act(self, obs: Any, ctx: dict[str, Any]) -> dict[str, Any]:
        return {"agent_id": self.agent_id, "obs": obs, "t": ctx["t"]}


@dataclass
class DummyMetrics:
    """No-op metrics for tests."""

    def per_step(
        self,
        t: int,
        state_hash_pre: str,
        action: dict[str, Any],
        reward: Any,
        cost: Any,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        return {"t": t}

    def aggregate(self, contribs_stream: Any) -> dict[str, Any]:
        return {"count": len(list(contribs_stream))}


def make_env() -> DummyEnv:
    return DummyEnv(agent_ids=["agent2", "agent1"])


def make_policies() -> dict[str, DummyPolicy]:
    return {"agent2": DummyPolicy("agent2"), "agent1": DummyPolicy("agent1")}


def make_metrics() -> DummyMetrics:
    return DummyMetrics()
