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
8. Require git diff evidence for all edits (`git diff --cached` and `git diff --cached --name-status`).
9. Require tests to exist for touched behavior and pass (`make check` or equivalent).
10. Require fixtures (if declared) to match pinned SHA-256 hashes.

## API
- `def validate_gate(run_dir: pathlib.Path, *, contract_version: str = "1") -> GateReport`
- `GateReport` fields: `verdict: Literal["PASS", "FAIL"]`, `per_agent: dict[str, AgentResult]`, `errors: list[str]`.
- `manager_tasks.yaml` must include: `contract_version`, `tasks` (length 5), `tasks[*].id` in `agent1..agent5`, and `tasks[*].spec_path` (unique).
- `agent*/out.yaml` must include: `contract_version`, `status`, and exactly one of `result` or `error`.
- `manager_verdict.yaml` must include: `contract_version`, `verdict`, `per_agent` (length 5).
- `manager_verdict.yaml` must include: `tests.command` (list of strings), `tests.exit_code` (int), `tests.summary` (list of strings).
- `manager_verdict.yaml` may include: `fixtures` list of `{path, sha256}`.
- The validator must be deterministic, read-only, and network-free.
- Optional logging artifacts (non-normative): `runs/run-<id>-manager.jsonl`, `runs/run-<id>-agent*.jsonl`, and a merged `runs/run-<id>-swarm.jsonl` with a `lane` field.

Mapping example:

- `tasks[0].id: agent1` → `runs/<run_id>/agent1/out.yaml`

## Acceptance criteria
- `make gate` validates a sample run directory and fails on any invariant violation.
- `make gate` rejects artifacts missing `contract_version` or using any value other than `"1"`.
- `make gate` rejects plans that do not enumerate exactly `agent1..agent5`.
- `make gate` rejects tasks missing `spec_path` or using duplicate `spec_path` values.

## Replay Swarm Prompts (2026-02-03)

Manager prompt (current task):
- Goal: deliver deterministic replay runner (CLI + library) with strict determinism constraints and fixtures pinned by hash in CI.
- Constraints:
  - Write manager outputs to `runs/<run_id>/manager_tasks.yaml` and `runs/<run_id>/manager_verdict.yaml` only.
  - CLI lives in `src/replay.py`.
  - `src/runner.py` is a pure library module (no CLI).
  - Use `argparse` only; override `ArgumentParser.error()` and `ArgumentParser.exit()` to emit deterministic error payloads.
  - No dynamic defaults from environment (cwd, time, hostname). Defaults must be fixed literals or required flags.
  - Parse errors must not rely on argparse built-in output.
  - Fixtures live in `traces/fixtures/` and are pinned by hash in CI.
  - Require staged diffs (`git add -A`, `git diff --cached`, `git diff --cached --name-status`) and test evidence.
  - Run tests and record command, exit code, and summary lines in `manager_verdict.yaml`.
- Responsibilities:
  - Update manager-locked files if needed (including `specs/spec.md`, `PLAN.md`, `CHANGELOG.md`, `.github/workflows/**`).
  - Ensure CI pins `traces/fixtures/` by hash.
  - Final integration and `make check`.
- Stop condition:
  - All lanes complete DoD and manager checks pass.
  - Diff evidence and tests recorded; gate should fail if missing.

Agent role mapping:
- `agent1`: Scaffolder
- `agent2`: Schema+Validate
- `agent3`: Core Loop
- `agent4`: Analyzer
- `agent5`: Bench+Bundle+Docs

## Gate Output Expectations (Replay Swarm)

Manager task plan output:

```yaml
contract_version: "1"
tasks:
  - id: agent1
    spec_path: specs/agent-orchestrator/agent1.md
  - id: agent2
    spec_path: specs/agent-orchestrator/agent2.md
  - id: agent3
    spec_path: specs/agent-orchestrator/agent3.md
  - id: agent4
    spec_path: specs/agent-orchestrator/agent4.md
  - id: agent5
    spec_path: specs/agent-orchestrator/agent5.md
```

Manager verdict output:

```yaml
contract_version: "1"
verdict: PASS
per_agent:
  agent1: PASS
  agent2: PASS
  agent3: PASS
  agent4: PASS
  agent5: PASS
tests:
  command: ["make", "check"]
  exit_code: 0
  summary:
    - "1 passed"
fixtures:
  - path: "traces/fixtures/example.jsonl"
    sha256: "<sha256>"
```

Worker output template:

```yaml
contract_version: "1"
status: PASS
result:
  summary: "<one-line summary>"
  diff_name_status: "<git diff --cached --name-status>"
  diff_patch: "<git diff --cached>"
  test_files:
    - "tests/test_example.py"
# Write to: runs/<run_id>/<agent_id>/out.yaml
```
