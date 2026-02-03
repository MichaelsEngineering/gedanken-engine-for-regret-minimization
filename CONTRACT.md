# Contract: Deterministic Replay Runner

## Goal
Provide a deterministic replay runner (CLI + library) that replays a fixed trace with a declared seed or tape and produces a stable derived-state hash while streaming JSONL to stdout.

## Scope
- Implement a replay runner that consumes `trace`, `seed|tape`, `env`, `policies`, and `metrics`.
- Provide a CLI: `replay --env ... --policies ... --metrics ... --trace ... --seed|--tape ... --out ... [--tee]`.
- Provide a stable library entrypoint: `run = replay.run(config) -> RunHandle`.
- Produce a `RunHandle` with `run_dir`, `log_bundle_sha256`, `exit_code`, and machine-readable error payload on failure.
- Enforce step ordering: observe -> act -> validate -> transition -> score -> log.
- Enforce deterministic replay and complete causal declaration.

## Out of Scope
- Analyzer outputs and regret metrics.
- New schema files or schema versioning changes.
- Changes to manager-locked files.
- Coordination/executor runtime changes beyond replay runner.

## Non-negotiable Invariants
- Deterministic replay: identical spec + seed + trace yields identical derived-state hash.
- Complete causal declaration: no hidden exogenous inputs outside the trace/tape and declared seed.
- Append-only JSONL logging; no in-place edits or reordering.
- Policies never receive raw state; only declared observation and non-causal metadata.

## Closed-system Boundary Tuple
The replay boundary is an explicit tuple:
`(spec_ref, trace_ref, seed_or_tape_ref, env_id, policies_id, metrics_id)`.
Any change to any element invalidates deterministic equivalence.

## Acceptance
- CLI runs with declared inputs and prints JSONL replay stream to stdout.
- Running the same replay twice yields the same derived-state hash.
- Unit tests cover CLI wiring, deterministic replay, and step ordering.
- `make check` passes.

## Constraints
- Python 3.11.
- No new schema files under `schemas/**`.
- Honor CODEOWNERS and manager-locked files.
- Stop work at 5 minutes if not complete.
