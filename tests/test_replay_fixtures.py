from __future__ import annotations

from src import replay_fixtures


def test_make_policies_has_five_agents() -> None:
    policies = replay_fixtures.make_policies()
    assert sorted(policies.keys()) == [
        "agent1",
        "agent2",
        "agent3",
        "agent4",
        "agent5",
    ]


def test_make_env_and_metrics_are_deterministic() -> None:
    env_a = replay_fixtures.make_env()
    env_b = replay_fixtures.make_env()
    assert env_a.agent_ids == env_b.agent_ids

    metrics_a = replay_fixtures.make_metrics()
    metrics_b = replay_fixtures.make_metrics()
    assert metrics_a.aggregate([{"t": 1}, {"t": 2}]) == metrics_b.aggregate(
        [{"t": 1}, {"t": 2}]
    )
