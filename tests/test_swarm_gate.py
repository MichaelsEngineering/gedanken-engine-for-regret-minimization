from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from scripts.swarm_gate import validate_gate


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def _build_valid_run(run_dir: Path) -> None:
    _write_yaml(
        run_dir / "manager_tasks.yaml",
        {
            "contract_version": "1",
            "tasks": [
                {"id": "agent1", "spec_path": "scripts/agent-orchestrator/agent1.md"},
                {"id": "agent2", "spec_path": "scripts/agent-orchestrator/agent2.md"},
                {"id": "agent3", "spec_path": "scripts/agent-orchestrator/agent3.md"},
                {"id": "agent4", "spec_path": "scripts/agent-orchestrator/agent4.md"},
                {"id": "agent5", "spec_path": "scripts/agent-orchestrator/agent5.md"},
            ],
        },
    )
    _write_yaml(
        run_dir / "manager_verdict.yaml",
        {
            "contract_version": "1",
            "verdict": "PASS",
            "per_agent": {
                "agent1": "PASS",
                "agent2": "PASS",
                "agent3": "PASS",
                "agent4": "PASS",
                "agent5": "PASS",
            },
            "tests": {
                "command": ["make", "check"],
                "exit_code": 0,
                "summary": ["ok"],
            },
        },
    )
    for agent_id in ("agent1", "agent2", "agent3", "agent4", "agent5"):
        _write_yaml(
            run_dir / agent_id / "out.yaml",
            {
                "contract_version": "1",
                "status": "PASS",
                "result": {
                    "summary": "ok",
                    "diff_name_status": "M file.txt",
                    "diff_patch": "diff --git a/file.txt b/file.txt\n",
                    "test_files": ["tests/test_example.py"],
                },
            },
        )


def test_validate_gate_passes_on_valid_run(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    _build_valid_run(run_dir)

    report = validate_gate(run_dir, run_tests=False)

    assert report.verdict == "PASS"
    assert report.errors == []
    assert all(not result.errors for result in report.per_agent.values())


def test_validate_gate_fails_on_duplicate_spec_paths(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    _build_valid_run(run_dir)
    tasks_path = run_dir / "manager_tasks.yaml"
    data = yaml.safe_load(tasks_path.read_text(encoding="utf-8"))
    data["tasks"][1]["spec_path"] = data["tasks"][0]["spec_path"]
    _write_yaml(tasks_path, data)

    report = validate_gate(run_dir, run_tests=False)

    assert report.verdict == "FAIL"
    assert any("spec_path values must be unique" in error for error in report.errors)


def test_validate_gate_fails_on_missing_agent_out(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    _build_valid_run(run_dir)
    missing_path = run_dir / "agent3" / "out.yaml"
    missing_path.unlink()

    report = validate_gate(run_dir, run_tests=False)

    assert report.verdict == "FAIL"
    assert report.per_agent["agent3"].errors


def test_validate_gate_fails_on_fixture_outside_root(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    _build_valid_run(run_dir)
    fixture_path = tmp_path / "fixture.jsonl"
    fixture_path.write_text('{"ok": true}\n', encoding="utf-8")
    digest = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    verdict_path = run_dir / "manager_verdict.yaml"
    data = yaml.safe_load(verdict_path.read_text(encoding="utf-8"))
    data["fixtures"] = [{"path": str(fixture_path), "sha256": digest}]
    _write_yaml(verdict_path, data)

    report = validate_gate(run_dir, run_tests=False)

    assert report.verdict == "FAIL"
    assert any(
        "fixtures[*].path must live under traces/fixtures" in error
        for error in report.errors
    )
