from __future__ import annotations

from copy import deepcopy

from src import validation_engine


def _valid_metrics() -> list[dict[str, float | str]]:
    return [
        {
            "name": "latency",
            "candidate_value": 120.0,
            "comparator_value": 100.0,
            "unit": "ms",
            "scale_c_i": 20.0,
            "weight": 0.5,
        },
        {
            "name": "errors",
            "candidate_value": 5.0,
            "comparator_value": 1.0,
            "unit": "count",
            "scale_c_i": 4.0,
            "weight": 1.5,
        },
    ]


def test_gate_dimensionless_regret() -> None:
    result = validation_engine.analyze({"metrics": _valid_metrics()})

    assert result["valid"] is True
    assert result["dimensionless"] is True
    assert result["unit_invariance_pass"] is True
    assert len(result["components"]) == 2
    expected = (0.5 * ((100.0 - 120.0) / 20.0)) + (1.5 * ((1.0 - 5.0) / 4.0))
    assert abs(float(result["aggregate_regret"]) - expected) <= 1e-12


def test_ci_must_be_positive() -> None:
    metrics = _valid_metrics()
    metrics[0]["scale_c_i"] = 0.0

    result = validation_engine.analyze({"metrics": metrics})

    assert result["valid"] is False
    assert result["aggregate_regret"] is None
    assert any("scale_c_i must be > 0" in error for error in result["errors"])


def test_negative_weight_rejected() -> None:
    metrics = _valid_metrics()
    metrics[0]["weight"] = -0.1

    result = validation_engine.analyze({"metrics": metrics})

    assert result["valid"] is False
    assert result["aggregate_regret"] is None
    assert any("weight must be >= 0" in error for error in result["errors"])


def test_ms_to_s_invariance_passes() -> None:
    metrics = _valid_metrics()
    result = validation_engine.analyze({"metrics": metrics})
    assert result["valid"] is True
    assert result["unit_invariance_pass"] is True


def test_unit_invariance_mismatch_hard_fails() -> None:
    metrics: list[dict[str, float | str]] = [
        {
            "name": "latency",
            "candidate_value": 120.0,
            "comparator_value": 100.0,
            "unit": "ms",
            "scale_c_i": 20.0,
            "weight": 1.0,
            "alt_unit": "s",
            "candidate_value_in_alt_unit": 0.120,
            "comparator_value_in_alt_unit": 0.100,
            "scale_c_i_in_alt_unit": 0.030,
        }
    ]

    result = validation_engine.analyze({"metrics": metrics})

    assert result["valid"] is False
    assert result["aggregate_regret"] is None
    assert result["unit_invariance_pass"] is False
    assert any("unit invariance failed" in error for error in result["errors"])


def test_analyze_no_mutation_deterministic() -> None:
    state = {"metrics": _valid_metrics()}
    original = deepcopy(state)

    first = validation_engine.analyze(state)
    second = validation_engine.analyze(state)

    assert state == original
    assert first == second
