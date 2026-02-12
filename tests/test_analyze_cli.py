"""CLI tests for deterministic analyze wiring and report emission."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src import analyze


def test_analyze_writes_report_json(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    events_path.write_text(
        '{"kind":"STEP","seq":0,"t":0}\n'
        '{"analysis_input":{"metrics":[{"name":"latency","candidate_value":120.0,"comparator_value":100.0,"unit":"ms","scale_c_i":20.0,"weight":1.0}]},"kind":"ANALYZE_INPUT","seq":1}\n',
        encoding="utf-8",
    )
    report_path = tmp_path / "report.json"

    exit_code = analyze.main(
        ["--in", str(events_path), "--out", str(report_path), "--run-id", "42"]
    )

    assert exit_code == 0
    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["report_version"] == "1"
    assert payload["run_id"] == "42"
    assert payload["source_events_path"] == str(events_path)
    assert isinstance(payload["source_events_sha256"], str)
    assert payload["event_count"] == 2
    assert payload["analysis"]["deterministic_input_valid"] is True
    summary = payload["analysis"]["scalar_summary"]
    assert summary["valid"] is True
    assert summary["dimensionless"] is True
    assert summary["unit_invariance_pass"] is True
    assert "_analyzer_stub" not in summary


def test_analyze_missing_input_returns_deterministic_error(
    tmp_path: Path, capsys: Any
) -> None:
    missing_path = tmp_path / "missing.jsonl"
    report_path = tmp_path / "report.json"

    exit_code = analyze.main(["--in", str(missing_path), "--out", str(report_path)])

    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["kind"] == "ERROR"
    assert payload["error"]["type"] == "ARG_VALIDATION"


def test_analyze_invalid_jsonl_returns_deterministic_error(
    tmp_path: Path, capsys: Any
) -> None:
    events_path = tmp_path / "events.jsonl"
    events_path.write_text('{"kind":"STEP","seq":0}\n{not-json}\n', encoding="utf-8")
    report_path = tmp_path / "report.json"

    exit_code = analyze.main(["--in", str(events_path), "--out", str(report_path)])

    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["kind"] == "ERROR"
    assert payload["error"]["type"] == "ARG_VALIDATION"
    assert "invalid JSONL" in payload["error"]["message"]


def test_analyze_report_is_byte_identical_on_repeat(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    events_path.write_text('{"kind":"STEP","seq":0}\n', encoding="utf-8")
    report_path = tmp_path / "report.json"

    first_exit = analyze.main(["--in", str(events_path), "--out", str(report_path)])
    first_bytes = report_path.read_bytes()
    second_exit = analyze.main(["--in", str(events_path), "--out", str(report_path)])
    second_bytes = report_path.read_bytes()

    assert first_exit == 0
    assert second_exit == 0
    assert first_bytes == second_bytes


def test_analyze_no_metric_dataset_emits_invalid_summary(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    events_path.write_text('{"kind":"STEP","seq":0,"t":0}\n', encoding="utf-8")
    report_path = tmp_path / "report.json"

    exit_code = analyze.main(["--in", str(events_path), "--out", str(report_path)])

    assert exit_code == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    summary = payload["analysis"]["scalar_summary"]
    assert summary["valid"] is False
    assert summary["aggregate_regret"] is None
    assert any("metrics list is required" in error for error in summary["errors"])
