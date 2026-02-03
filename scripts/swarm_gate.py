from __future__ import annotations

import argparse
import json
import hashlib
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

AGENT_IDS = ("agent1", "agent2", "agent3", "agent4", "agent5")
DEFAULT_ALLOWED_TEST_COMMANDS = {("make", "check")}
DEFAULT_TEST_TIMEOUT_S = 120
FIXTURES_ROOT = (Path.cwd() / "traces" / "fixtures").resolve()


@dataclass(frozen=True)
class AgentResult:
    status: str
    errors: list[str]


@dataclass(frozen=True)
class GateReport:
    verdict: str
    per_agent: dict[str, AgentResult]
    errors: list[str]


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Expected a YAML mapping at top level.")
    return data


def _load_yaml_or_error(path: Path, errors: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        errors.append(f"Missing required file: {path}")
        return None
    try:
        return _load_yaml(path)
    except (yaml.YAMLError, ValueError) as exc:
        errors.append(f"Invalid YAML in {path}: {exc}")
        return None


def _require_contract_version(
    data: dict[str, Any], path: Path, contract_version: str, errors: list[str]
) -> None:
    if data.get("contract_version") != contract_version:
        errors.append(
            f'{path}: contract_version must be "{contract_version}".'
        )


def _require_git_repo(errors: list[str]) -> None:
    if not (Path.cwd() / ".git").exists():
        errors.append("Workspace must be a git repo with a .git directory.")


def _require_diff_evidence(
    out_data: dict[str, Any], path: Path, errors: list[str]
) -> None:
    result = out_data.get("result")
    if not isinstance(result, dict):
        errors.append(f"{path}: result must be a mapping.")
        return
    diff_patch = result.get("diff_patch")
    diff_name_status = result.get("diff_name_status")
    if not isinstance(diff_patch, str) or not diff_patch.strip():
        errors.append(f"{path}: result.diff_patch must be a non-empty string.")
    if not isinstance(diff_name_status, str) or not diff_name_status.strip():
        errors.append(
            f"{path}: result.diff_name_status must be a non-empty string."
        )
    test_files = result.get("test_files")
    if not isinstance(test_files, list) or not all(
        isinstance(item, str) and item for item in test_files
    ):
        errors.append(f"{path}: result.test_files must be a non-empty string list.")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_fixture_path(path_value: str, errors: list[str]) -> Path | None:
    fixture_path = Path(path_value)
    resolved = (
        fixture_path.resolve()
        if fixture_path.is_absolute()
        else (Path.cwd() / fixture_path).resolve()
    )
    try:
        resolved.relative_to(FIXTURES_ROOT)
    except ValueError:
        errors.append(
            "manager_verdict.yaml: fixtures[*].path must live under traces/fixtures/."
        )
        return None
    return resolved


def _require_fixtures(verdict_data: dict[str, Any], errors: list[str]) -> None:
    fixtures = verdict_data.get("fixtures")
    if fixtures is None:
        return
    if not isinstance(fixtures, list):
        errors.append("manager_verdict.yaml: fixtures must be a list.")
        return
    for index, item in enumerate(fixtures):
        if not isinstance(item, dict):
            errors.append(
                f"manager_verdict.yaml: fixtures[{index}] must be a mapping."
            )
            continue
        path_value = item.get("path")
        sha_value = item.get("sha256")
        if not isinstance(path_value, str) or not path_value:
            errors.append(
                f"manager_verdict.yaml: fixtures[{index}].path must be a string."
            )
            continue
        if not isinstance(sha_value, str) or not sha_value:
            errors.append(
                f"manager_verdict.yaml: fixtures[{index}].sha256 must be a string."
            )
            continue
        fixture_path = _resolve_fixture_path(path_value, errors)
        if fixture_path is None:
            continue
        if not fixture_path.exists():
            errors.append(
                f"manager_verdict.yaml: fixture not found at {fixture_path}"
            )
            continue
        actual = _hash_file(fixture_path)
        if actual != sha_value:
            errors.append(
                f"manager_verdict.yaml: fixture hash mismatch for {fixture_path}"
            )


def _require_test_results(
    verdict_data: dict[str, Any], errors: list[str]
) -> tuple[list[str], int] | None:
    tests = verdict_data.get("tests")
    if not isinstance(tests, dict):
        errors.append("manager_verdict.yaml: tests must be a mapping.")
        return None
    command = tests.get("command")
    exit_code = tests.get("exit_code")
    summary = tests.get("summary")
    if not isinstance(command, list) or not all(
        isinstance(item, str) and item for item in command
    ):
        errors.append("manager_verdict.yaml: tests.command must be a list of strings.")
        return None
    if not isinstance(exit_code, int):
        errors.append("manager_verdict.yaml: tests.exit_code must be an int.")
        return None
    if not isinstance(summary, list) or not all(
        isinstance(item, str) and item for item in summary
    ):
        errors.append("manager_verdict.yaml: tests.summary must be a list of strings.")
        return None
    return command, exit_code


def _run_tests(
    command: list[str], errors: list[str], *, timeout_s: int
) -> None:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        errors.append(f"Test command timed out after {timeout_s}s.")
        return
    except FileNotFoundError:
        errors.append(f"Test command not found: {command[0]}")
        return
    if result.returncode != 0:
        errors.append(
            f"Test command failed with exit code {result.returncode}."
        )


def validate_gate(
    run_dir: Path,
    *,
    contract_version: str = "1",
    allowed_test_commands: set[tuple[str, ...]] | None = None,
    run_tests: bool = True,
    test_timeout_s: int = DEFAULT_TEST_TIMEOUT_S,
) -> GateReport:
    errors: list[str] = []
    per_agent: dict[str, AgentResult] = {}
    _require_git_repo(errors)

    tasks_path = run_dir / "manager_tasks.yaml"
    tasks_data = _load_yaml_or_error(tasks_path, errors)
    if tasks_data is not None:
        _require_contract_version(tasks_data, tasks_path, contract_version, errors)
        tasks = tasks_data.get("tasks")
        if not isinstance(tasks, list):
            errors.append(f"{tasks_path}: tasks must be a list.")
        else:
            if len(tasks) != len(AGENT_IDS):
                errors.append(
                    f"{tasks_path}: tasks must have length {len(AGENT_IDS)}."
                )
            ids: list[str] = []
            spec_paths: list[str] = []
            for index, task in enumerate(tasks):
                if not isinstance(task, dict):
                    errors.append(f"{tasks_path}: tasks[{index}] must be a mapping.")
                    continue
                task_id = task.get("id")
                if task_id not in AGENT_IDS:
                    errors.append(
                        f"{tasks_path}: tasks[{index}].id must be one of {AGENT_IDS}."
                    )
                else:
                    ids.append(task_id)
                spec_path = task.get("spec_path")
                if not spec_path or not isinstance(spec_path, str):
                    errors.append(
                        f"{tasks_path}: tasks[{index}].spec_path must be a string."
                    )
                else:
                    spec_paths.append(spec_path)
            if set(ids) != set(AGENT_IDS):
                errors.append(f"{tasks_path}: tasks must enumerate {AGENT_IDS}.")
            if len(spec_paths) != len(set(spec_paths)):
                errors.append(f"{tasks_path}: spec_path values must be unique.")

    verdict_path = run_dir / "manager_verdict.yaml"
    verdict_data = _load_yaml_or_error(verdict_path, errors)
    if verdict_data is not None:
        _require_contract_version(verdict_data, verdict_path, contract_version, errors)
        verdict_value = verdict_data.get("verdict")
        if verdict_value not in {"PASS", "FAIL"}:
            errors.append(f"{verdict_path}: verdict must be PASS or FAIL.")
        test_command = _require_test_results(verdict_data, errors)
        if test_command is not None:
            command, exit_code = test_command
            allowed = (
                allowed_test_commands
                if allowed_test_commands is not None
                else DEFAULT_ALLOWED_TEST_COMMANDS
            )
            if tuple(command) not in allowed:
                errors.append(
                    f"{verdict_path}: tests.command is not in the allowlist."
                )
            if exit_code != 0:
                errors.append(
                    f"{verdict_path}: tests.exit_code must be 0 for PASS."
                )
            if run_tests and tuple(command) in allowed:
                _run_tests(command, errors, timeout_s=test_timeout_s)
        _require_fixtures(verdict_data, errors)
        per_agent_map = verdict_data.get("per_agent")
        if not isinstance(per_agent_map, dict):
            errors.append(f"{verdict_path}: per_agent must be a mapping.")
        else:
            if len(per_agent_map) != len(AGENT_IDS):
                errors.append(
                    f"{verdict_path}: per_agent must have length {len(AGENT_IDS)}."
                )
            if set(per_agent_map.keys()) != set(AGENT_IDS):
                errors.append(
                    f"{verdict_path}: per_agent keys must be {AGENT_IDS}."
                )

    for agent_id in AGENT_IDS:
        agent_errors: list[str] = []
        out_path = run_dir / agent_id / "out.yaml"
        out_data = _load_yaml_or_error(out_path, agent_errors)
        status_value = "FAIL"
        if out_data is not None:
            _require_contract_version(out_data, out_path, contract_version, agent_errors)
            status = out_data.get("status")
            if not isinstance(status, str) or not status:
                agent_errors.append(f"{out_path}: status must be a non-empty string.")
            else:
                status_value = status
            has_result = "result" in out_data
            has_error = "error" in out_data
            if has_result == has_error:
                agent_errors.append(
                    f"{out_path}: must include exactly one of result or error."
                )
            if has_result:
                _require_diff_evidence(out_data, out_path, agent_errors)
        per_agent[agent_id] = AgentResult(
            status=status_value if not agent_errors else "FAIL",
            errors=agent_errors,
        )

    overall_ok = not errors and all(
        not result.errors for result in per_agent.values()
    )
    verdict = "PASS" if overall_ok else "FAIL"
    return GateReport(verdict=verdict, per_agent=per_agent, errors=errors)


def _report_to_dict(report: GateReport) -> dict[str, Any]:
    return {
        "verdict": report.verdict,
        "per_agent": {key: asdict(value) for key, value in report.per_agent.items()},
        "errors": report.errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an orchestrator gate run.")
    parser.add_argument("--run", required=True, help="Path to run directory.")
    args = parser.parse_args(argv)

    report = validate_gate(Path(args.run))
    print(json.dumps(_report_to_dict(report), indent=2, sort_keys=True))
    return 0 if report.verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
