from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


RUN_DIR = Path("runs/1")
AGENT_IDS = ("agent1", "agent2", "agent3", "agent4", "agent5")


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict), f"expected mapping in {path}"
    return data


def test_gate_fixture_required_files_exist() -> None:
    required = [
        RUN_DIR / "manager_tasks.yaml",
        RUN_DIR / "manager_verdict.yaml",
        RUN_DIR / "agent1" / "out.yaml",
        RUN_DIR / "agent2" / "out.yaml",
        RUN_DIR / "agent3" / "out.yaml",
        RUN_DIR / "agent4" / "out.yaml",
        RUN_DIR / "agent5" / "out.yaml",
    ]
    for path in required:
        assert path.exists(), f"missing required gate fixture file: {path}"
        assert path.is_file(), f"expected file: {path}"


def test_gate_fixture_manager_tasks_contract() -> None:
    payload = _load_yaml(RUN_DIR / "manager_tasks.yaml")
    assert payload.get("contract_version") == "1"
    tasks = payload.get("tasks")
    assert isinstance(tasks, list)
    assert len(tasks) == len(AGENT_IDS)

    ids: list[str] = []
    spec_paths: list[str] = []
    for index, task in enumerate(tasks):
        assert isinstance(task, dict), f"tasks[{index}] must be a mapping"
        task_id = task.get("id")
        assert isinstance(task_id, str)
        assert task_id in AGENT_IDS
        ids.append(task_id)
        spec_path = task.get("spec_path")
        assert isinstance(spec_path, str)
        assert spec_path
        spec_paths.append(spec_path)

    assert set(ids) == set(AGENT_IDS)
    assert len(spec_paths) == len(set(spec_paths))


def test_gate_fixture_manager_verdict_contract() -> None:
    payload = _load_yaml(RUN_DIR / "manager_verdict.yaml")
    assert payload.get("contract_version") == "1"

    tests = payload.get("tests")
    assert isinstance(tests, dict)
    command = tests.get("command")
    exit_code = tests.get("exit_code")
    summary = tests.get("summary")
    assert isinstance(command, list)
    assert all(isinstance(item, str) and item for item in command)
    assert isinstance(exit_code, int)
    assert isinstance(summary, list)
    assert all(isinstance(item, str) and item for item in summary)


def test_gate_fixture_agent_outputs_contract() -> None:
    for agent_id in AGENT_IDS:
        payload = _load_yaml(RUN_DIR / agent_id / "out.yaml")
        assert payload.get("contract_version") == "1"
        status = payload.get("status")
        assert isinstance(status, str)
        assert status
        has_result = "result" in payload
        has_error = "error" in payload
        assert has_result != has_error
