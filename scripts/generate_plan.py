from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

AGENT_IDS = ("agent1", "agent2", "agent3", "agent4", "agent5")


@dataclass(frozen=True)
class ValidationError(Exception):
    code: str
    field_path: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} at {self.field_path}: {self.message}"


@dataclass(frozen=True)
class Invariant:
    inv_id: str
    statement: str
    violation_effect: str
    section_id: str | None
    minimal_code_surface: str | None


@dataclass(frozen=True)
class Observable:
    obs_id: str
    pass_condition: str
    test_name: str | None


@dataclass(frozen=True)
class Variable:
    name: str
    definition: str


@dataclass(frozen=True)
class Assumption:
    asm_id: str
    statement: str
    section_id: str | None


@dataclass(frozen=True)
class Artifact:
    name: str
    producer_lane_hint: str | None


@dataclass(frozen=True)
class ContractModel:
    primary_section_id: str
    invariants: list[Invariant]
    observables: list[Observable]
    admissibility_rule: str
    variables: list[Variable]
    assumptions: list[Assumption]
    artifacts: list[Artifact]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _require_mapping(data: Any, path: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValidationError(
            code="TYPE_ERROR",
            field_path=path,
            message="Expected mapping.",
        )
    return data


def _require_non_empty_str(data: dict[str, Any], key: str, path: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(
            code="MISSING_FIELD",
            field_path=f"{path}.{key}",
            message="Expected non-empty string.",
        )
    return value.strip()


def _require_list(data: dict[str, Any], key: str, path: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise ValidationError(
            code="MISSING_FIELD",
            field_path=f"{path}.{key}",
            message="Expected non-empty list.",
        )
    return value


def _validate_contract(payload: dict[str, Any], *, strict: bool) -> ContractModel:
    if not strict:
        raise ValidationError(
            code="STRICT_REQUIRED",
            field_path="strict",
            message="Strict mode is mandatory for this generator.",
        )

    claim = _require_mapping(payload.get("claim"), "claim")
    primary_section_id = _require_non_empty_str(claim, "primary_section_id", "claim")

    raw_invariants = _require_list(payload, "invariants", "")
    seen_invariants: set[str] = set()
    invariants: list[Invariant] = []
    for idx, raw_item in enumerate(raw_invariants):
        item = _require_mapping(raw_item, f"invariants[{idx}]")
        inv_id = _require_non_empty_str(item, "id", f"invariants[{idx}]")
        if inv_id in seen_invariants:
            raise ValidationError(
                code="DUPLICATE_ID",
                field_path=f"invariants[{idx}].id",
                message=f"Duplicate invariant id '{inv_id}'.",
            )
        seen_invariants.add(inv_id)
        minimal_code_surface = item.get("minimal_code_surface")
        if minimal_code_surface is not None and not isinstance(minimal_code_surface, str):
            raise ValidationError(
                code="TYPE_ERROR",
                field_path=f"invariants[{idx}].minimal_code_surface",
                message="Expected string when present.",
            )
        invariants.append(
            Invariant(
                inv_id=inv_id,
                statement=_require_non_empty_str(item, "statement", f"invariants[{idx}]"),
                violation_effect=_require_non_empty_str(
                    item, "violation_effect", f"invariants[{idx}]"
                ),
                section_id=item.get("section_id") if isinstance(item.get("section_id"), str) else None,
                minimal_code_surface=minimal_code_surface,
            )
        )

    raw_observables = _require_list(payload, "observables", "")
    seen_observables: set[str] = set()
    observables: list[Observable] = []
    for idx, raw_item in enumerate(raw_observables):
        item = _require_mapping(raw_item, f"observables[{idx}]")
        obs_id = _require_non_empty_str(item, "id", f"observables[{idx}]")
        if obs_id in seen_observables:
            raise ValidationError(
                code="DUPLICATE_ID",
                field_path=f"observables[{idx}].id",
                message=f"Duplicate observable id '{obs_id}'.",
            )
        seen_observables.add(obs_id)
        test_name = item.get("test_name")
        if test_name is not None and not isinstance(test_name, str):
            raise ValidationError(
                code="TYPE_ERROR",
                field_path=f"observables[{idx}].test_name",
                message="Expected string when present.",
            )
        observables.append(
            Observable(
                obs_id=obs_id,
                pass_condition=_require_non_empty_str(
                    item, "pass_condition", f"observables[{idx}]"
                ),
                test_name=test_name,
            )
        )

    comparator = _require_mapping(payload.get("comparator"), "comparator")
    admissibility_rule = _require_non_empty_str(
        comparator, "admissibility_rule", "comparator"
    )

    raw_variables = _require_list(payload, "variables", "")
    seen_variables: set[str] = set()
    variables: list[Variable] = []
    for idx, raw_item in enumerate(raw_variables):
        item = _require_mapping(raw_item, f"variables[{idx}]")
        name = _require_non_empty_str(item, "name", f"variables[{idx}]")
        if name in seen_variables:
            raise ValidationError(
                code="DUPLICATE_ID",
                field_path=f"variables[{idx}].name",
                message=f"Duplicate variable name '{name}'.",
            )
        seen_variables.add(name)
        variables.append(
            Variable(
                name=name,
                definition=_require_non_empty_str(item, "definition", f"variables[{idx}]"),
            )
        )

    raw_assumptions = _require_list(payload, "assumptions", "")
    seen_assumptions: set[str] = set()
    assumptions: list[Assumption] = []
    for idx, raw_item in enumerate(raw_assumptions):
        item = _require_mapping(raw_item, f"assumptions[{idx}]")
        asm_id = _require_non_empty_str(item, "id", f"assumptions[{idx}]")
        if asm_id in seen_assumptions:
            raise ValidationError(
                code="DUPLICATE_ID",
                field_path=f"assumptions[{idx}].id",
                message=f"Duplicate assumption id '{asm_id}'.",
            )
        seen_assumptions.add(asm_id)
        assumptions.append(
            Assumption(
                asm_id=asm_id,
                statement=_require_non_empty_str(item, "statement", f"assumptions[{idx}]"),
                section_id=item.get("section_id") if isinstance(item.get("section_id"), str) else None,
            )
        )

    artifacts: list[Artifact] = []
    raw_artifacts = payload.get("artifacts")
    if raw_artifacts is not None:
        if not isinstance(raw_artifacts, list):
            raise ValidationError(
                code="TYPE_ERROR",
                field_path="artifacts",
                message="Expected list when present.",
            )
        for idx, raw_item in enumerate(raw_artifacts):
            item = _require_mapping(raw_item, f"artifacts[{idx}]")
            name = _require_non_empty_str(item, "name", f"artifacts[{idx}]")
            producer_lane_hint = item.get("producer_lane_hint")
            if producer_lane_hint is not None and not isinstance(producer_lane_hint, str):
                raise ValidationError(
                    code="TYPE_ERROR",
                    field_path=f"artifacts[{idx}].producer_lane_hint",
                    message="Expected string when present.",
                )
            artifacts.append(Artifact(name=name, producer_lane_hint=producer_lane_hint))

    return ContractModel(
        primary_section_id=primary_section_id,
        invariants=invariants,
        observables=observables,
        admissibility_rule=admissibility_rule,
        variables=variables,
        assumptions=assumptions,
        artifacts=artifacts,
    )


def _code_surface_for(token: str) -> str:
    key = token.lower()
    if "replay" in key:
        return "`src/runner.py`, `tests/test_runner.py`"
    if "trace" in key:
        return "`traces/*.jsonl`, `tests/test_swarm_gate.py`"
    if "dimension" in key or "regret" in key:
        return (
            "`src/analyzer.py`, `src/scalarization/__init__.py`, "
            "`tests/test_analyzer_stub.py`"
        )
    if "oracle" in key or "admiss" in key:
        return "`src/validate.py`, `tests/test_validate.py`"
    return "`src/`, `tests/`"


def _test_name_for(observable: Observable) -> str:
    if observable.test_name and observable.test_name.strip():
        return observable.test_name.strip()
    return f"test_gate_{_slug(observable.obs_id)}"


def _spec_id(index_1_based: int) -> str:
    return f"SPEC-{index_1_based:03d}"


def _assign_spec_ranges(spec_count: int) -> dict[str, tuple[int, int] | None]:
    ranges: dict[str, tuple[int, int] | None] = {}
    base = spec_count // len(AGENT_IDS)
    extra = spec_count % len(AGENT_IDS)
    cursor = 1
    for idx, agent_id in enumerate(AGENT_IDS):
        size = base + (1 if idx < extra else 0)
        if size == 0:
            ranges[agent_id] = None
            continue
        start = cursor
        end = cursor + size - 1
        ranges[agent_id] = (start, end)
        cursor = end + 1
    return ranges


def _initial_work_items(status_template_path: Path, registry_template_path: Path) -> list[dict[str, Any]]:
    return [
        {
            "id": "WI-001",
            "owner": "agent1",
            "goal": "Finalize invariant-to-spec mapping with explicit hard-fail predicates.",
            "constraints": [
                "No code or test edits.",
                "Keep output deterministic and scoped to assigned SPEC-ID rows.",
            ],
            "touched_paths": ["plans/PLAN.md (SPEC table rows only)"],
            "acceptance_tests": ["pytest -q tests/test_generate_plan.py -k section_order"],
            "artifacts_to_emit": [
                status_template_path.as_posix(),
                "runs/swarm/worker1/YYYYMMDD-HHMM/NOTES.md",
            ],
            "rollback_plan": "Revert SPEC table row edits and regenerate plan from contract.",
        },
        {
            "id": "WI-002",
            "owner": "agent2",
            "goal": "Author/update assigned SPEC sections with executable predicates and tests.",
            "constraints": [
                "Edit only assigned spec sections.",
                "No shared-file restructuring.",
            ],
            "touched_paths": ["plans/PLAN.md (SPEC sections only)"],
            "acceptance_tests": ["pytest -q tests/test_generate_plan.py -k integration"],
            "artifacts_to_emit": [
                status_template_path.as_posix(),
                "runs/swarm/worker2/YYYYMMDD-HHMM/NOTES.md",
            ],
            "rollback_plan": "Restore previous SPEC sections and rerun generator.",
        },
        {
            "id": "WI-003",
            "owner": "agent3",
            "goal": "Implement falsification tests for replay, trace, dimensionality, and admissibility.",
            "constraints": [
                "Tests before implementation changes.",
                "No edits outside tests/.",
            ],
            "touched_paths": ["tests/**"],
            "acceptance_tests": ["pytest -q tests/test_swarm_gate.py tests/test_generate_plan.py"],
            "artifacts_to_emit": [
                status_template_path.as_posix(),
                "runs/swarm/worker3/YYYYMMDD-HHMM/NOTES.md",
                "runs/swarm/worker3/YYYYMMDD-HHMM/DIFFSTAT.txt",
            ],
            "rollback_plan": "Revert test changes to last green commit and re-run targeted tests.",
        },
        {
            "id": "WI-004",
            "owner": "agent4",
            "goal": "Implement minimal src changes required by existing failing tests.",
            "constraints": [
                "No interface expansion without matching tests and docs.",
                "No network, time, or unseeded randomness.",
            ],
            "touched_paths": ["src/**"],
            "acceptance_tests": ["make gate", "pytest -q tests/test_runner.py"],
            "artifacts_to_emit": [
                status_template_path.as_posix(),
                registry_template_path.as_posix(),
                "runs/swarm/worker4/YYYYMMDD-HHMM/NOTES.md",
            ],
            "rollback_plan": "Revert lane-local src edits and validate gate baseline.",
        },
        {
            "id": "WI-005",
            "owner": "agent5",
            "goal": "Produce replay/audit artifacts and register provenance checksums.",
            "constraints": [
                "Append-only trace handling.",
                "Do not change source code paths.",
            ],
            "touched_paths": ["runs/**", "traces/**"],
            "acceptance_tests": ["make gate", "make smoke"],
            "artifacts_to_emit": [
                status_template_path.as_posix(),
                registry_template_path.as_posix(),
                "runs/swarm/worker5/YYYYMMDD-HHMM/NOTES.md",
            ],
            "rollback_plan": "Remove derived run artifacts for the slice and replay from last green gate.",
        },
    ]


def _assert_disjoint_touched_paths(work_items: list[dict[str, Any]]) -> None:
    normalized: list[set[str]] = []
    for item in work_items:
        touched = item.get("touched_paths", [])
        if not isinstance(touched, list):
            raise ValidationError(
                code="TYPE_ERROR",
                field_path=f"work_item.{item.get('id', 'unknown')}.touched_paths",
                message="Expected list.",
            )
        cleaned = {str(path).strip() for path in touched if str(path).strip()}
        normalized.append(cleaned)

    for left in range(len(normalized)):
        for right in range(left + 1, len(normalized)):
            overlap = normalized[left].intersection(normalized[right])
            if overlap:
                raise ValidationError(
                    code="OVERLAP_TOUCHED_PATHS",
                    field_path="initial_work_items",
                    message=f"Touched paths overlap: {sorted(overlap)}",
                )


def _render_plan(
    model: ContractModel,
    *,
    contract_path: Path,
    repo_guardrails_path: Path,
    gate_command: str,
    status_template_path: Path,
    registry_template_path: Path,
) -> str:
    work_items = _initial_work_items(status_template_path, registry_template_path)
    _assert_disjoint_touched_paths(work_items)

    lines: list[str] = []
    lines.append("# PLAN: Deterministic Manager Loop for Claim Contract Execution")
    lines.append("")

    lines.append("## Authority")
    lines.append(
        "- Post-approval authority is `plans/PLAN.md`; this file is operationally canonical for implementation and evaluation."
    )
    lines.append(
        f"- Generated from `{contract_path.as_posix()}` with strict validation enabled."
    )
    lines.append(f"- Primary claim section: `{model.primary_section_id}`.")
    lines.append(
        f"- Repository guardrails source: `{repo_guardrails_path.as_posix()}`."
    )
    lines.append("")

    lines.append("## Invariant Extraction Table")
    lines.append("")
    lines.append("| INV-ID | SPEC-ID | Test Name | Minimal Code Surface |")
    lines.append("| --- | --- | --- | --- |")
    for idx, invariant in enumerate(model.invariants, start=1):
        spec_id = _spec_id(idx)
        observable = model.observables[min(idx - 1, len(model.observables) - 1)]
        test_name = _test_name_for(observable)
        code_surface = invariant.minimal_code_surface or _code_surface_for(observable.obs_id)
        lines.append(
            f"| `{invariant.inv_id}` | `{spec_id}` | `{test_name}` | {code_surface} |"
        )
    lines.append("")

    lines.append("## Lane Assignments and Ownership")
    lines.append("")
    lines.append("- Manager: owns plan structure, delegation, integration, and gate decisions.")
    ranges = _assign_spec_ranges(len(model.invariants))
    for agent_id in AGENT_IDS:
        spec_range = ranges[agent_id]
        range_text = (
            "none" if spec_range is None else f"`{_spec_id(spec_range[0])}..{_spec_id(spec_range[1])}`"
        )
        lines.append(f"- `{agent_id}`: assigned SPEC range {range_text}.")
    lines.append("- Disjoint ownership rule: only one active worker may touch a given `touched_paths` slice.")
    lines.append("")

    lines.append("## Execution Loop")
    lines.append("")
    lines.append("Repeat until deterministic exit gates are green:")
    lines.append("1. `plan`: read repo state and define tranche objective.")
    lines.append("2. `delegate`: emit up to 5 work items with disjoint `touched_paths`.")
    lines.append("3. `workers execute`: workers run only assigned scope and tests.")
    lines.append("4. `integrate`: manager merges worker artifacts and resolves conflicts.")
    lines.append("5. `verify`: run deterministic gate plus targeted tests.")
    lines.append("6. `checkpoint`: update status/registry and tranche record.")
    lines.append("Exit condition: all termination rules satisfied and deterministic gates pass.")
    lines.append("")

    lines.append("## Work Item Schema (Manager -> Worker)")
    lines.append("")
    lines.append("Each delegated task must be a single object with exactly:")
    lines.append("- `goal`")
    lines.append("- `constraints`")
    lines.append("- `touched_paths`")
    lines.append("- `acceptance_tests`")
    lines.append("- `artifacts_to_emit`")
    lines.append("- `rollback_plan`")
    lines.append("")

    lines.append("## Worker Response Schema (Worker -> Manager)")
    lines.append("")
    lines.append("Each worker response must include:")
    lines.append("- `diff_summary` (3-7 bullets)")
    lines.append("- `files_changed`")
    lines.append("- `tests_run`")
    lines.append("- `results` (pass/fail + key output lines)")
    lines.append("- `risks` (0-3 bullets)")
    lines.append("- `next_actions` (0-5 bullets)")
    lines.append("- `open_questions` (only if blocking)")
    lines.append("")

    lines.append("## Initial Tranche Work Items")
    lines.append("")
    for item in work_items:
        lines.append(f"### {item['id']} ({item['owner']})")
        lines.append("```yaml")
        lines.append(f"goal: {item['goal']}")
        lines.append("constraints:")
        for constraint in item["constraints"]:
            lines.append(f"  - {constraint}")
        lines.append("touched_paths:")
        for touched_path in item["touched_paths"]:
            lines.append(f"  - {touched_path}")
        lines.append("acceptance_tests:")
        for test_cmd in item["acceptance_tests"]:
            lines.append(f"  - {test_cmd}")
        lines.append("artifacts_to_emit:")
        for artifact in item["artifacts_to_emit"]:
            lines.append(f"  - {artifact}")
        lines.append(f"rollback_plan: {item['rollback_plan']}")
        lines.append("```")
        lines.append("")

    lines.append("## Spec Sections")
    lines.append("")
    lines.append("### Hard-fail Invariants")
    for invariant in model.invariants:
        lines.append(
            f"- `{invariant.inv_id}`: {invariant.statement} (violation: `{invariant.violation_effect}`)."
        )
    lines.append("")
    lines.append("### Worker-Assignable Specs")
    for idx, invariant in enumerate(model.invariants, start=1):
        spec_id = _spec_id(idx)
        observable = model.observables[min(idx - 1, len(model.observables) - 1)]
        owner = next(
            (
                agent
                for agent, spec_range in ranges.items()
                if spec_range is not None and spec_range[0] <= idx <= spec_range[1]
            ),
            "agent2",
        )
        lines.append("")
        lines.append(f"#### {spec_id}")
        lines.append(f"- Owner lane: `{owner}`")
        lines.append(f"- Source invariant: `{invariant.inv_id}`")
        lines.append(f"- Predicate: {invariant.statement}")
        lines.append(f"- Test name: `{_test_name_for(observable)}`")
        lines.append(f"- Pass condition: {observable.pass_condition}")
        lines.append(
            "- Minimal code surface: "
            + (invariant.minimal_code_surface or _code_surface_for(observable.obs_id))
        )
    lines.append("")
    lines.append("### Spec Glossary")
    for variable in model.variables:
        lines.append(f"- `{variable.name}`: {variable.definition}")
    lines.append("")

    lines.append("## Merge Order")
    lines.append("")
    lines.append("1. `agent1` invariant extraction outputs")
    lines.append("2. `agent2` plan-embedded specs")
    lines.append("3. `agent3` falsification tests")
    lines.append("4. `agent4` minimal implementation")
    lines.append("5. `agent5` replay and audit artifacts")
    lines.append("")

    lines.append("## Gate Definitions")
    lines.append("")
    lines.append("- Deterministic replay gate: identical `(spec, seed, trace)` yields identical derived-state hash.")
    lines.append("- Trace invariance gate: alternatives must not mutate frozen workload trace.")
    lines.append("- Dimensionality gate: aggregate regret is dimensionless and unit-invariant.")
    lines.append(f"- Admissibility gate: {model.admissibility_rule}")
    for observable in model.observables:
        lines.append(
            f"- Observable gate `{observable.obs_id}` via `{_test_name_for(observable)}`: {observable.pass_condition}"
        )
    lines.append("")
    lines.append("Single gate command:")
    lines.append("")
    lines.append("```bash")
    lines.append(gate_command)
    lines.append("```")
    lines.append("")

    lines.append("## Termination Rule (Per Slice)")
    lines.append("")
    lines.append("Stop a slice only when all are true:")
    lines.append("1. All `acceptance_tests` pass.")
    lines.append("2. All `artifacts_to_emit` are created or updated.")
    lines.append("3. Manager acceptance checklist is complete.")
    lines.append("")

    lines.append("## State Externalization")
    lines.append("")
    lines.append(f"- Canonical manager status: `{status_template_path.as_posix()}`")
    lines.append("  - Required fields: `current_objective`, `active_work_items`, `last_green_gate`, `unresolved_risks`, `next_tranche_plan`.")
    lines.append(f"- Artifact registry: `{registry_template_path.as_posix()}`")
    lines.append(
        "  - Columns: `artifact_id,type,inputs_spec_seed_trace,sha256,created_at_utc,purpose,linked_tests,producer`."
    )
    lines.append("- Per-worker scratchpad: `runs/swarm/workerN/YYYYMMDD-HHMM/NOTES.md`")
    lines.append("- Optional per-worker diffstat: `runs/swarm/workerN/YYYYMMDD-HHMM/DIFFSTAT.txt`")
    lines.append("")

    lines.append("## Checkpoint Cadence and Budgets")
    lines.append("")
    lines.append("- Tranche size target: 1-5 files, <400 LOC net unless escalation is approved.")
    lines.append("- Budgets per tranche: tool calls <= 12, test runtime <= 5 minutes cumulative.")
    lines.append("- Required checkpoint steps:")
    lines.append(f"  1. Update `{status_template_path.as_posix()}`.")
    lines.append(f"  2. Run `{gate_command}`.")
    lines.append(f"  3. Record results in status and `{registry_template_path.as_posix()}` when artifacts are emitted.")
    lines.append("- Failure policy: if a gate fails twice for the same slice, reduce scope and serialize changes.")
    lines.append("")

    lines.append("## Conflict Resolution and Escalation")
    lines.append("")
    lines.append("Escalate to manager-only decision when:")
    lines.append("- Touching manager-locked/shared files (gates, workflows, CODEOWNERS, core schemas).")
    lines.append("- Changing SPEC semantics or invariants.")
    lines.append("- Cross-lane dependencies block progress for more than one tranche.")
    lines.append("Tie-break rule: manager records rationale in status and adds/updates a regression test for non-trivial risk.")
    lines.append("")

    lines.append("## End-to-End Verification")
    lines.append("")
    lines.append("Beyond unit gates, run one smoke path:")
    lines.append("```bash")
    lines.append("make smoke")
    lines.append("```")
    lines.append("")

    lines.append("## Manager Acceptance Checklist")
    lines.append("")
    lines.append("- What changed (1 sentence)")
    lines.append("- Why (1 sentence)")
    lines.append("- Commands run + results")
    lines.append("- Known risks + mitigations")
    lines.append("- Follow-ups (if any)")
    lines.append("")

    lines.append("## Required Final Chat Output")
    lines.append("")
    lines.append("1. Tranche summary")
    lines.append("2. Files changed")
    lines.append("3. Commands run")
    lines.append("4. Test results")
    lines.append("5. Risks and follow-ups")
    lines.append("")

    lines.append("## Definition of Done by Lane")
    lines.append("")
    lines.append("- Manager: all tranche checkpoints complete and deterministic gates green.")
    lines.append("- `agent1`: invariant to spec mapping complete and deterministic.")
    lines.append("- `agent2`: spec sections are executable and ambiguity-free.")
    lines.append("- `agent3`: falsification tests are present and passing.")
    lines.append("- `agent4`: minimal implementation passes existing tests without nondeterministic behavior.")
    lines.append("- `agent5`: audit artifacts are append-only and registry entries include checksums.")
    lines.append("")

    lines.append("## Failure and Rollback")
    lines.append("")
    lines.append("- Abort immediately on schema validation errors or gate failures.")
    lines.append("- Post exact failing commands and key output lines in tranche notes.")
    lines.append("- Revert only lane-local changes when rolling back a slice.")
    lines.append("- Never merge failing artifacts.")
    lines.append("")

    lines.append("## Assumptions Log")
    lines.append("")
    for assumption in model.assumptions:
        section_suffix = f" (section `{assumption.section_id}`)" if assumption.section_id else ""
        lines.append(f"- `{assumption.asm_id}`{section_suffix}: {assumption.statement}")
    if model.artifacts:
        lines.append("")
        lines.append("### Artifact Producer Hints")
        for artifact in model.artifacts:
            if artifact.producer_lane_hint:
                lines.append(f"- `{artifact.name}` -> `{artifact.producer_lane_hint}`")

    lines.append("")
    return "\n".join(lines)


def generate_plan(
    contract_path: Path,
    output_path: Path,
    *,
    strict: bool = True,
    repo_guardrails_path: Path = Path("AGENTS.md"),
    gate_command: str = "make gate",
    mirror_output_path: Path | None = Path("PLAN.md"),
    status_template_path: Path = Path("runs/swarm/STATUS.md"),
    registry_template_path: Path = Path("runs/swarm/artifacts/REGISTRY.csv"),
) -> int:
    try:
        if not contract_path.exists():
            raise ValidationError(
                code="MISSING_FILE",
                field_path="contract_path",
                message=f"File not found: {contract_path}",
            )

        with contract_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)

        payload = _require_mapping(payload, "root")
        model = _validate_contract(payload, strict=strict)
        content = _render_plan(
            model,
            contract_path=contract_path,
            repo_guardrails_path=repo_guardrails_path,
            gate_command=gate_command,
            status_template_path=status_template_path,
            registry_template_path=registry_template_path,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

        if mirror_output_path is not None:
            mirror_output_path.parent.mkdir(parents=True, exist_ok=True)
            mirror_output_path.write_text(content, encoding="utf-8")

        return 0
    except ValidationError as exc:
        print(f"{exc.code}:{exc.field_path}:{exc.message}", file=sys.stderr)
        return 1
    except yaml.YAMLError as exc:
        print(f"YAML_ERROR:root:{exc}", file=sys.stderr)
        return 1


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate plans/PLAN.md from a core_claim.contract.yaml file "
            "with strict fail-fast validation."
        )
    )
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("plans/PLAN.md"))
    parser.add_argument("--mirror-out", type=Path, default=Path("PLAN.md"))
    parser.add_argument("--repo-guardrails", type=Path, default=Path("AGENTS.md"))
    parser.add_argument("--gate-command", type=str, default="make gate")
    parser.add_argument(
        "--status-template-path", type=Path, default=Path("runs/swarm/STATUS.md")
    )
    parser.add_argument(
        "--registry-template-path",
        type=Path,
        default=Path("runs/swarm/artifacts/REGISTRY.csv"),
    )
    strict_group = parser.add_mutually_exclusive_group()
    strict_group.add_argument("--strict", dest="strict", action="store_true")
    strict_group.add_argument("--no-strict", dest="strict", action="store_false")
    parser.set_defaults(strict=True)

    mirror_group = parser.add_mutually_exclusive_group()
    mirror_group.add_argument("--mirror", dest="mirror", action="store_true")
    mirror_group.add_argument("--no-mirror", dest="mirror", action="store_false")
    parser.set_defaults(mirror=True)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    mirror_output_path = args.mirror_out if args.mirror else None
    return generate_plan(
        contract_path=args.contract,
        output_path=args.out,
        strict=args.strict,
        repo_guardrails_path=args.repo_guardrails,
        gate_command=args.gate_command,
        mirror_output_path=mirror_output_path,
        status_template_path=args.status_template_path,
        registry_template_path=args.registry_template_path,
    )


if __name__ == "__main__":
    raise SystemExit(main())
