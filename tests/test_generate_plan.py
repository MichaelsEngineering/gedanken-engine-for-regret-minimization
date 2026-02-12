from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from scripts.generate_plan import generate_plan


def _sample_contract() -> dict[str, Any]:
    return {
        "claim": {"primary_section_id": "SEC-001"},
        "invariants": [
            {
                "id": "inv_alpha",
                "statement": "alpha invariant",
                "violation_effect": "hard failure",
            },
            {
                "id": "inv_beta",
                "statement": "beta invariant",
                "violation_effect": "hard failure",
            },
        ],
        "observables": [
            {"id": "replay_identity", "pass_condition": "identity holds"},
            {"id": "trace_invariance", "pass_condition": "trace stable"},
        ],
        "comparator": {"admissibility_rule": "O(a) <= O(a_eval)"},
        "variables": [
            {"name": "spec", "definition": "frozen specification"},
            {"name": "trace", "definition": "immutable trace"},
        ],
        "assumptions": [
            {"id": "asm_one", "statement": "context fixed", "section_id": "SEC-001"}
        ],
        "artifacts": [
            {
                "name": "trace_events",
                "path_pattern": "traces/*.jsonl",
                "producer_lane_hint": "agent5",
            }
        ],
    }


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_deterministic_output_snapshot_with_mirror(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.yaml"
    out_path = tmp_path / "plans" / "PLAN.md"
    mirror_path = tmp_path / "PLAN.md"
    _write_yaml(contract_path, _sample_contract())

    first = generate_plan(
        contract_path,
        out_path,
        strict=True,
        mirror_output_path=mirror_path,
    )
    first_hash = _sha256(out_path)
    first_mirror_hash = _sha256(mirror_path)
    second = generate_plan(
        contract_path,
        out_path,
        strict=True,
        mirror_output_path=mirror_path,
    )
    second_hash = _sha256(out_path)
    second_mirror_hash = _sha256(mirror_path)

    assert first == 0
    assert second == 0
    assert first_hash == second_hash
    assert first_mirror_hash == second_mirror_hash
    assert first_hash == first_mirror_hash


def test_missing_required_field_fails_with_exact_path(
    tmp_path: Path, capsys: Any
) -> None:
    contract = _sample_contract()
    del contract["claim"]["primary_section_id"]
    contract_path = tmp_path / "contract.yaml"
    out_path = tmp_path / "PLAN.md"
    _write_yaml(contract_path, contract)

    exit_code = generate_plan(
        contract_path, out_path, strict=True, mirror_output_path=None
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "claim.primary_section_id" in captured.err


def test_duplicate_invariant_ids_fail(tmp_path: Path, capsys: Any) -> None:
    contract = _sample_contract()
    contract["invariants"][1]["id"] = contract["invariants"][0]["id"]
    contract_path = tmp_path / "contract.yaml"
    out_path = tmp_path / "PLAN.md"
    _write_yaml(contract_path, contract)

    exit_code = generate_plan(
        contract_path, out_path, strict=True, mirror_output_path=None
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "invariants[1].id" in captured.err


def test_observable_missing_pass_condition_fails(tmp_path: Path, capsys: Any) -> None:
    contract = _sample_contract()
    del contract["observables"][0]["pass_condition"]
    contract_path = tmp_path / "contract.yaml"
    out_path = tmp_path / "PLAN.md"
    _write_yaml(contract_path, contract)

    exit_code = generate_plan(
        contract_path, out_path, strict=True, mirror_output_path=None
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "observables[0].pass_condition" in captured.err


def test_output_section_order_is_stable(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.yaml"
    out_path = tmp_path / "PLAN.md"
    _write_yaml(contract_path, _sample_contract())
    assert (
        generate_plan(contract_path, out_path, strict=True, mirror_output_path=None)
        == 0
    )

    text = out_path.read_text(encoding="utf-8")
    expected_order = [
        "## Authority",
        "## Invariant Extraction Table",
        "## Lane Assignments and Ownership",
        "## Execution Loop",
        "## Work Item Schema (Manager -> Worker)",
        "## Worker Response Schema (Worker -> Manager)",
        "## Initial Tranche Work Items",
        "## Spec Sections",
        "## Merge Order",
        "## Gate Definitions",
        "## Termination Rule (Per Slice)",
        "## State Externalization",
        "## Checkpoint Cadence and Budgets",
        "## Conflict Resolution and Escalation",
        "## End-to-End Verification",
        "## Manager Acceptance Checklist",
        "## Required Final Chat Output",
        "## Definition of Done by Lane",
        "## Failure and Rollback",
        "## Assumptions Log",
    ]
    positions = [text.index(header) for header in expected_order]
    assert positions == sorted(positions)


def test_output_contains_required_loop_schemas_and_paths(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.yaml"
    out_path = tmp_path / "PLAN.md"
    _write_yaml(contract_path, _sample_contract())

    assert (
        generate_plan(contract_path, out_path, strict=True, mirror_output_path=None)
        == 0
    )
    text = out_path.read_text(encoding="utf-8")

    assert "plan`: read repo state" in text
    assert "delegate`: emit up to 5 work items" in text
    assert "workers execute" in text
    assert "integrate" in text
    assert "verify" in text
    assert "checkpoint" in text

    assert "`goal`" in text
    assert "`constraints`" in text
    assert "`touched_paths`" in text
    assert "`acceptance_tests`" in text
    assert "`artifacts_to_emit`" in text
    assert "`rollback_plan`" in text

    assert "`diff_summary`" in text
    assert "`files_changed`" in text
    assert "`tests_run`" in text
    assert "`results`" in text
    assert "`risks`" in text
    assert "`next_actions`" in text
    assert "`open_questions`" in text

    assert "runs/swarm/STATUS.md" in text
    assert "runs/swarm/artifacts/REGISTRY.csv" in text
    assert "runs/swarm/workerN/YYYYMMDD-HHMM/NOTES.md" in text
    assert "make smoke" in text


def test_optional_fields_are_consumed_when_present(tmp_path: Path) -> None:
    contract = _sample_contract()
    contract["observables"][0]["test_name"] = "test_gate_custom_replay"
    contract["invariants"][0]["minimal_code_surface"] = (
        "`src/custom.py`, `tests/test_custom.py`"
    )

    contract_path = tmp_path / "contract.yaml"
    out_path = tmp_path / "PLAN.md"
    _write_yaml(contract_path, contract)

    assert (
        generate_plan(contract_path, out_path, strict=True, mirror_output_path=None)
        == 0
    )
    text = out_path.read_text(encoding="utf-8")

    assert "test_gate_custom_replay" in text
    assert "`src/custom.py`, `tests/test_custom.py`" in text
    assert "`trace_events` -> `agent5`" in text


def test_optional_fields_absent_remain_backward_compatible(tmp_path: Path) -> None:
    contract = _sample_contract()
    del contract["artifacts"]
    contract_path = tmp_path / "contract.yaml"
    out_path = tmp_path / "PLAN.md"
    _write_yaml(contract_path, contract)

    exit_code = generate_plan(
        contract_path, out_path, strict=True, mirror_output_path=None
    )
    text = out_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "test_gate_replay_identity" in text
    assert "`src/runner.py`, `tests/test_runner.py`" in text


def test_integration_generation_from_repo_contract_with_mirror(tmp_path: Path) -> None:
    contract_path = Path("plans/claim/definition-sec-001/core_claim.contract.yaml")
    out_path = tmp_path / "plans" / "PLAN.md"
    mirror_path = tmp_path / "PLAN.md"

    exit_code = generate_plan(
        contract_path,
        out_path,
        strict=True,
        mirror_output_path=mirror_path,
    )
    text = out_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "## Execution Loop" in text
    assert "## Initial Tranche Work Items" in text
    assert "## Required Final Chat Output" in text
    assert "make gate" in text
    assert "make smoke" in text
    assert out_path.read_text(encoding="utf-8") == mirror_path.read_text(
        encoding="utf-8"
    )
