"""CLI tests for deterministic errors and wiring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src import replay


def test_cli_deterministic_error(capsys: Any) -> None:
    exit_code = replay.main(["--env", "tests.fixtures_cli:make_env"])
    assert exit_code == 2
    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["kind"] == "ERROR"
    assert payload["error"]["type"].startswith("ARGPARSE")


def test_cli_wiring_runs(tmp_path: Path, capsys: Any) -> None:
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text('{"x": 1}\n', encoding="utf-8")
    out_dir = tmp_path / "run"
    exit_code = replay.main(
        [
            "--env",
            "tests.fixtures_cli:make_env",
            "--policies",
            "tests.fixtures_cli:make_policies",
            "--metrics",
            "tests.fixtures_cli:make_metrics",
            "--trace",
            str(trace_path),
            "--seed",
            "1",
            "--out",
            str(out_dir),
            "--tee",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert lines
    payload = json.loads(lines[0])
    assert payload["kind"] == "STEP"
    assert (out_dir / "events.jsonl").exists()


def test_cli_rejects_disallowed_module(tmp_path: Path, capsys: Any) -> None:
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text('{"x": 1}\n', encoding="utf-8")
    out_dir = tmp_path / "run"
    exit_code = replay.main(
        [
            "--env",
            "json:loads",
            "--policies",
            "json:loads",
            "--metrics",
            "json:loads",
            "--trace",
            str(trace_path),
            "--seed",
            "1",
            "--out",
            str(out_dir),
        ]
    )
    assert exit_code == 2
    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["kind"] == "ERROR"
    assert payload["error"]["type"] == "ARG_VALIDATION"
