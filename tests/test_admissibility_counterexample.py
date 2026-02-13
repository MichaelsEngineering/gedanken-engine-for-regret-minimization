from __future__ import annotations

import json
from pathlib import Path

from src import analyze, validation_engine


def _metrics() -> list[dict[str, float | str]]:
    return [
        {
            "name": "latency",
            "candidate_value": 120.0,
            "comparator_value": 100.0,
            "unit": "ms",
            "scale_c_i": 20.0,
            "weight": 1.0,
        }
    ]


def test_gate_asymmetric_externality_counterexample_oracle_hard_fail() -> None:
    result = validation_engine.analyze(
        {
            "comparator_mode": "oracle",
            "uses_hidden_state": False,
            "uses_future_info": False,
            "metrics": _metrics(),
        }
    )

    assert result["valid"] is False
    assert result["aggregate_regret"] is None
    assert any(
        "oracle comparator mode is inadmissible" in error for error in result["errors"]
    )


def test_gate_asymmetric_externality_counterexample_admissible_pass() -> None:
    result = validation_engine.analyze(
        {
            "comparator_mode": "admissible",
            "uses_hidden_state": False,
            "uses_future_info": False,
            "metrics": _metrics(),
        }
    )

    assert result["valid"] is True
    assert result["dimensionless"] is True
    assert result["aggregate_regret"] is not None
    assert result["errors"] == []


def test_admissibility_result_is_deterministic_on_repeat(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    events_path.write_text(
        '{"kind":"STEP","seq":0}\n'
        '{"analysis_input":{"comparator_mode":"admissible","uses_hidden_state":false,"uses_future_info":false,"metrics":[{"name":"latency","candidate_value":120.0,"comparator_value":100.0,"unit":"ms","scale_c_i":20.0,"weight":1.0}]},"kind":"ANALYZE_INPUT","seq":1}\n',
        encoding="utf-8",
    )
    report_path = tmp_path / "report.json"

    first_exit = analyze.main(["--in", str(events_path), "--out", str(report_path)])
    first_bytes = report_path.read_bytes()
    second_exit = analyze.main(["--in", str(events_path), "--out", str(report_path)])
    second_bytes = report_path.read_bytes()

    assert first_exit == 0
    assert second_exit == 0
    assert first_bytes == second_bytes
    payload = json.loads(first_bytes.decode("utf-8"))
    summary = payload["analysis"]["scalar_summary"]
    assert summary["valid"] is True
    assert summary["dimensionless"] is True
    assert summary["aggregate_regret"] is not None
