from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

AGENT_IDS = ("agent1", "agent2", "agent3", "agent4", "agent5")


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


def validate_gate(run_dir: Path, *, contract_version: str = "1") -> GateReport:
    errors: list[str] = []
    per_agent: dict[str, AgentResult] = {}

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
