# ExecPlan for Deterministic Parallel Execution (Codex 5.2)

## Authority and Scope

PLAN.md is the single source of execution truth for this repository. Any conflicting plan documents are non-authoritative. References to alternative plan documents are removed or reconciled here. The spec remains authoritative for behavior: `specs/spec.md` and `specs/*.yaml` define what the system must do; this plan defines how the work is executed and integrated. The Decision Log in `PLAN.md` is the canonical location for recording plan decisions and justifications.

## Purpose

Make the plan directly executable by up to 6 parallel agents with deterministic integration. The plan declares exact lanes, ownership, handoffs, merge order, determinism requirements, and verification steps so that work can proceed without coordination ambiguity or nondeterministic outcomes.

## Fixed Parallel Lanes (Exactly 6)

1. Manager (single lane)
2. Scaffolder
3. Schema+Validate
4. Core Loop
5. Analyzer
6. Bench+Bundle+Docs
   Worker lanes refer only to lanes 2–6 as enumerated above.

### Lane Responsibilities

- Manager: only agent allowed to merge to `main`. Owns shared/locked files and integration steps. Resolves conflicts, runs full checks, updates goldens, records decisions.
- Scaffolder: repo layout additions, new directories/files only (no edits to shared files).
- Schema+Validate: `schemas/**`, `src/validate.py`, validation tests.
- Core Loop: `src/runner.py`, `src/executor.py`, `src/env/**`, `src/policy/**`.
- Analyzer: `src/analyzer.py`, `src/metrics/**`, `src/scalarization/**`.
- Bench+Bundle+Docs: `bench/**`, `scripts/**`, `artifacts/**`, `docs/**` (except `docs/ARCHITECTURE.md`), golden outputs.

## File Ownership and Locked Files

### Manager-only (shared/locked)

- `AGENTS.md`
- `CHANGELOG.md`
- `Makefile`
- `README.md`
- `pyproject.toml`
- `uv.lock`
- `.github/workflows/**`
- `docs/ARCHITECTURE.md`

### Lane-owned Paths

- Scaffolder: `.gitignore`, new directories/files only (no edits to shared files)
- Schema+Validate: `schemas/**`, `src/validate.py`, validation tests
- Core Loop: `src/runner.py`, `src/executor.py`, `src/env/**`, `src/policy/**`
- Analyzer: `src/analyzer.py`, `src/metrics/**`, `src/scalarization/**`
- Bench+Bundle+Docs: `bench/**`, `scripts/**`, `artifacts/**`, `docs/**` (except `docs/ARCHITECTURE.md`)

### Non-negotiable Rule

Workers never directly edit shared/locked files. If a shared file change is required, the worker must request the Manager to perform it.

## Lane Stop Condition

A lane must stop work immediately after its DoD is satisfied and must not refactor or modify files outside its declared scope.

## Schema Evolution Rule

All schema changes under `schemas/**` must be versioned. Breaking changes require either a new versioned directory (e.g., `schemas/v2/`) or a `$schema_version` bump. Non-breaking changes must preserve backward compatibility. Core Loop and Analyzer must explicitly target the same schema version to prevent desync.

## Determinism and Replay Requirements

- Deterministic replay: identical spec, seed, and trace produce identical derived-state hashes.
- Stable hashes: all derived artifacts must have stable SHA-256 hashes under replay with identical inputs.
- No in-place edits of traces or outputs; append-only JSONL semantics are enforced.

### Required Metamorphic Tests

1. Replay stability: running the same command twice with identical inputs yields byte-identical outputs.
2. Trace immutability: appending new events to a trace does not alter prior event ordering or hashes.
3. Intent/result separation: intents contain only coordination events; results contain only execution events.
4. Hash determinism: derived artifact hashes match a manifest generated from the same inputs.

## Handoff Contracts Between Lanes

Each boundary must specify produced artifacts, schema guarantees, and validation required by the receiving lane.

### Scaffolder -> Schema+Validate

- Artifacts: new directories/files only (e.g., `schemas/`, `src/`, `tests/` stubs if needed)
- Guarantees: no edits to shared/locked files; paths exist for schema placement
- Validation: `rg --files` shows new paths; no changes under manager-only files

### Schema+Validate -> Core Loop

- Artifacts: JSON Schemas under `schemas/**`, validator in `src/validate.py`, tests in `tests/**`
- Guarantees: schemas validate required inputs; validator exits non-zero on invalid data
- Validation: `pytest -k validate` passes; invalid fixtures fail

### Core Loop -> Analyzer

- Artifacts: deterministic coordination output (`runs/<run_id>/intent.jsonl`), execution output (`runs/<run_id>/result.jsonl`)
- Guarantees: intent/result schema compliance; strict separation of event kinds; deterministic outputs
- Validation: unit tests for determinism; replay stability metamorphic test passes

### Analyzer -> Bench+Bundle+Docs

- Artifacts: `runs/<run_id>/derived.json`, `runs/<run_id>/table.csv`, stable hashes
- Guarantees: derived-state hash stable; regret metrics computed per spec
- Validation: `pytest -k analyzer` passes; hash determinism test passes

### Bench+Bundle+Docs -> Manager

- Artifacts: `bench/**` harness, `bench/golden/**`, `artifacts/**` bundles, `scripts/**` reproduce tooling, docs updates (non-ARCHITECTURE)
- Guarantees: reproducible outputs match goldens; manifest contains stable hashes
- Validation: `./scripts/reproduce.sh canonical` succeeds; golden diffs are intentional and documented

## Merge Order and Integration Protocol

### Required Merge Sequence

1. Scaffolder
2. Schema+Validate
3. Core Loop
4. Analyzer
5. Bench+Bundle+Docs

### Integration Rules

- Manager merges lanes strictly in the sequence above.
- No lane merges to `main` directly; Manager only.
- Each lane must pass its local verification before handing off.
- Manager runs full checks after each merge stage.
- Golden artifacts may only be updated by Manager with explicit justification in the Decision Log and commit message.
- Golden updates must be atomic: a dedicated commit that changes goldens only (no code changes).

## CI and Verification Expectations

### Mandatory Local Commands (per lane)

- Scaffolder: `rg --files` sanity, no changes to shared files; fail if shared files touched: `git diff --name-only <base>... | rg -n "^(README\\.md|Makefile|pyproject\\.toml|uv\\.lock|\\.github/workflows/|docs/ARCHITECTURE\\.md|AGENTS\\.md|CHANGELOG\\.md)$" && exit 1`
- Schema+Validate: `pytest -k validate`, `make check`
- Core Loop: `pytest -k runner or -k executor`, `make check`, `make smoke` if execution paths changed
- Analyzer: `pytest -k analyzer`, `make check`
- Bench+Bundle+Docs: `./scripts/reproduce.sh canonical`, `make check`

### Mandatory CI Checks Before Merge

- `make check` (authoritative per `Makefile`; composite includes ruff check + ruff format check + mypy + pytest + coverage)
- `make smoke` if execution paths changed
- Reproduction script: `./scripts/reproduce.sh canonical`

## Milestones as Parallel Work Packages

Each milestone lists parallel lanes, required inputs, exact outputs, and Definition of Done (DoD) per lane.

### Milestone 1: Scaffolding and Validation Foundations

- Parallel lanes: Scaffolder + Schema+Validate
- Required inputs: `specs/spec.md`, `specs/*.yaml`
- Outputs:
  - Scaffolder: new directories/files only as needed for `schemas/`, `src/`, `tests/`
  - Schema+Validate: `schemas/**`, `src/validate.py`, validation tests
- DoD:
  - Scaffolder: no edits to shared files; paths created
  - Schema+Validate: schemas validate spec inputs; `pytest -k validate` passes

### Milestone 2: Deterministic Core Loop

- Parallel lanes: Core Loop (primary) + Schema+Validate (support for schema changes only)
- Required inputs: schemas, validator, spec
- Outputs:
  - Core Loop: `src/runner.py`, `src/executor.py`, `runs/<run_id>/intent.jsonl`, `runs/<run_id>/result.jsonl`
- DoD:
  - Core Loop: deterministic replay test passes; intent/result separation enforced

### Milestone 3: Offline Analysis and Regret Metrics

- Parallel lanes: Analyzer (primary)
- Required inputs: core outputs, schemas
- Outputs:
  - Analyzer: `src/analyzer.py`, `src/metrics/**`, `src/scalarization/**`, `runs/<run_id>/derived.json`, `runs/<run_id>/table.csv`
- DoD:
  - Analyzer: stable derived-state hashes; regret metrics computed per spec; `pytest -k analyzer` passes

### Milestone 4: Bench Harness, Goldens, and Bundles

- Parallel lanes: Bench+Bundle+Docs (primary)
- Required inputs: analyzer outputs, core outputs
- Outputs:
  - Bench+Bundle+Docs: `bench/**`, `bench/golden/**`, `artifacts/**`, `scripts/**`, docs updates
- DoD:
  - Bench+Bundle+Docs: `./scripts/reproduce.sh canonical` passes; golden changes documented

### Milestone 5: Integration and Release Validation

- Parallel lanes: Manager (only)
- Required inputs: all prior lane outputs
- Outputs:
  - Manager: merged branch to `main`, updated goldens if needed, Decision Log updated
- DoD:
  - Manager: all checks green, determinism tests passing, reproduction script verified

## Failure and Drift Handling

- Unacceptable drift: any change that alters outputs under identical inputs without explicit acknowledgment.
- Rollback rule: if drift is detected, revert or fix-forward must restore determinism; decision logged.
- Intentional behavior changes require:
  1. Spec update (if behavior changes),
  2. Golden update with justification,
  3. Decision Log entry in PLAN.md.

## Feature Plan: Deterministic Replay Runner (2026-02-03)

Summary: add a replay runner (CLI + library) that replays a fixed trace with a declared seed or tape, enforces step ordering and causal declaration, and streams JSONL to stdout.

Scope:
- Replay runner consumes `trace`, `seed|tape`, `env`, `policies`, `metrics`.
- CLI: `replay --env ... --policies ... --metrics ... --trace ... --seed|--tape ... --out ... [--tee]`.
- Library entrypoint: `run = replay.run(config) -> RunHandle`.
- `RunHandle` includes `run_dir`, `log_bundle_sha256`, `exit_code`, `error_payload`.
- Enforce observe -> act -> validate -> transition -> score -> log.

Non-goals:
- No analyzer outputs or regret metrics.
- No new schema files or schema versioning changes.
- No changes to manager-locked files.

Determinism rules:
- Strict hash match for identical spec + seed + trace.
- All randomness must be declared via seed or tape.
- Replay boundary tuple is immutable.

Concurrency model:
- Synchronous joint action.
- Tie-breaking by deterministic sorted `agent_id`.

Termination:
- Stop when trace is exhausted or environment signals done.
- If both are available, they must agree or replay fails.

Interfaces:
Environment:
- `reset(init, rng) -> state`
- `observe(state) -> dict[agent_id, obs]`
- `validate_action(state, agent_id, action) -> ValidationResult`
- `step(state, joint_action, exogenous_x_t, rng) -> (next_state, reward, cost, info)`
Policy:
- `act(obs, ctx) -> action`
- `ctx` includes only `policy_id`, step index, action schema version.
- Policies must not receive raw state.
Metrics:
- `per_step(t, state_hash_pre, action, reward, cost, info) -> metric_contribs`
- `aggregate(contribs_stream) -> derived_metrics`
- Must be re-runnable offline from logs only.
Logger/Ledger:
- `emit(event_obj)` append-only.
- Enforces event ordering and schema versioning.

Steps:
1. Update `specs/spec.md` with replay semantics, boundary tuple, and interfaces.
2. Implement replay runner library and CLI under `src/`.
3. Add deterministic logging and log bundle hashing.
4. Add unit tests for CLI wiring, step ordering, and determinism.
5. Run `make check`.

Tests:
- CLI wiring tests for args and exit codes.
- Determinism test: same inputs -> same derived-state hash.
- Order test: verify observe -> act -> validate -> transition -> score -> log.

Assumptions:
- Trace schema exists per `specs/spec.md` and includes `TraceStarted`.
- `--tape` resolves to a pre-recorded RNG tape referenced by `tape_ref`.

## Final Manager Checklist

- All lanes completed DoD.
- All artifacts validated against schemas.
- Determinism and metamorphic tests passing.
- CI green.
- PLAN.md updated only if scope or invariants changed.

## Progress Log

Progress Log entries are Manager-only; lanes must request the Manager to append updates.

- [ ] 2026-02-01 00:00 UTC: Plan updated for Codex 5.2 parallel lanes and deterministic integration.

## Decision Log

- 2026-02-01: PLAN.md declared the single source of execution truth; lane ownership and merge protocol enforced.
