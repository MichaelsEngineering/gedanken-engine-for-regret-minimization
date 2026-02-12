"""Production fixtures for replay CLI wiring."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from src import runner


@dataclass
class ReplayFixtureEnv:
    """Minimal deterministic environment for replay runs."""

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
        del joint_action, exogenous_x_t
        next_state = {"t": state["t"] + 1, "done": True}
        info = {"done": True}
        return next_state, 1, 0, info


@dataclass
class ReplayFixturePolicy:
    """Deterministic policy that echoes the current context."""

    agent_id: str

    def act(self, obs: Any, ctx: dict[str, Any]) -> dict[str, Any]:
        return {"agent_id": self.agent_id, "obs": obs, "t": ctx["t"]}


@dataclass
class ReplayFixtureMetrics:
    """No-op deterministic metrics used by replay runs."""

    def per_step(
        self,
        t: int,
        state_hash_pre: str,
        action: dict[str, Any],
        reward: Any,
        cost: Any,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        del state_hash_pre, action, reward, cost, info
        return {"t": t}

    def aggregate(self, contribs_stream: Any) -> dict[str, Any]:
        return {"count": len(list(contribs_stream))}


def make_env() -> ReplayFixtureEnv:
    """Build the canonical environment for replay CLI runs."""
    return ReplayFixtureEnv(
        agent_ids=["agent5", "agent3", "agent1", "agent4", "agent2"]
    )


def make_policies() -> dict[str, ReplayFixturePolicy]:
    """Build deterministic policies for agent1..agent5."""
    return {
        "agent1": ReplayFixturePolicy("agent1"),
        "agent2": ReplayFixturePolicy("agent2"),
        "agent3": ReplayFixturePolicy("agent3"),
        "agent4": ReplayFixturePolicy("agent4"),
        "agent5": ReplayFixturePolicy("agent5"),
    }


def make_metrics() -> ReplayFixtureMetrics:
    """Build deterministic metrics for replay runs."""
    return ReplayFixtureMetrics()
