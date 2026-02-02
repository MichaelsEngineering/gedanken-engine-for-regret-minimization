# Spec: Agent Orchestrator Swarm Gate

## Authority model
- Treat `specs/spec.md` as the system source of truth; this spec constrains only the orchestration gate.
- Use YAML artifacts under `runs/<run_id>/` as the sole coordination channel for the gate.
- Keep the contract YAML-first; until template files exist, this spec defines required fields.

## Invariants
1. Require exactly 1 manager lane and 5 worker lanes with ids `agent1..agent5`.
2. Require the manager to emit only the plan and merge verdict; require workers to emit only their own `out.yaml`.
3. Require each task to include an explicit `spec_path`, and forbid duplicate `spec_path` values across tasks.
4. Require each task to be independent and bounded; forbid repo-wide refactors or dependency changes during the gate.
5. Require append-only artifacts per run; forbid in-place mutation across phases.
6. Require every YAML artifact to include `contract_version: "1"` (exact match).
7. Require gate execution to be deterministic and read-only for identical inputs.

## API
- `def validate_gate(run_dir: pathlib.Path, *, contract_version: str = "1") -> GateReport`
- `GateReport` fields: `verdict: Literal["PASS", "FAIL"]`, `per_agent: dict[str, AgentResult]`, `errors: list[str]`.
- `manager_tasks.yaml` must include: `contract_version`, `tasks` (length 5), `tasks[*].id` in `agent1..agent5`, and `tasks[*].spec_path` (unique).
- `agent*/out.yaml` must include: `contract_version`, `status`, and exactly one of `result` or `error`.
- `manager_verdict.yaml` must include: `contract_version`, `verdict`, `per_agent` (length 5).
- The validator must be deterministic, read-only, and network-free.
- Optional logging artifacts (non-normative): `runs/run-<id>-manager.jsonl`, `runs/run-<id>-agent*.jsonl`, and a merged `runs/run-<id>-swarm.jsonl` with a `lane` field.

Mapping example:

- `tasks[0].id: agent1` → `runs/<run_id>/agent1/out.yaml`

## Acceptance criteria
- `make gate` validates a sample run directory and fails on any invariant violation.
- `make gate` rejects artifacts missing `contract_version` or using any value other than `"1"`.
- `make gate` rejects plans that do not enumerate exactly `agent1..agent5`.
- `make gate` rejects tasks missing `spec_path` or using duplicate `spec_path` values.
