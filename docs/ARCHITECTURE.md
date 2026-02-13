# Architecture: Deterministic Replay and Offline Regret Analysis

## Purpose and Authority

This document defines the engineering architecture for deterministic replay and offline analysis.

Authority chain:

- Pre-approval authority: `theory/theory.pdf` is used for invariant extraction while forming the plan.
- Post-approval authority: `plans/PLAN.md` is the sole operational authority for implementation and evaluation.
- After explicit approval of `plans/PLAN.md`, implementation and testing must not re-interpret `theory/theory.pdf`.

## System Data Flow

The execution and analysis pipeline is deterministic and stage-based:

1. Inputs: approved spec (`plans/PLAN.md`), frozen workload trace, and declared `seed` or `tape`.
2. Admissibility boundary: alternatives must satisfy admissibility constraints (`A_adm`) before comparison.
3. Deterministic execution: replay CLI invokes deterministic runner over fixed inputs.
4. Append-only artifacts: run emits ordered JSONL events for audit and replay.
5. Offline analysis: analyzer consumes emitted events after execution completes.
6. Outputs: dimensionless regret summary plus deterministic-input validity checks.

## Artifact Contracts

| artifact | producer | consumer | path | required fields | immutability |
| --- | --- | --- | --- | --- | --- |
| Approved plan/spec | manager workflow | replay, gate, reviewers | `plans/PLAN.md` | authoritative invariants/spec/gates | append-only by approved updates |
| Fixture traces manifest | fixture tooling | replay, gate | `traces/fixtures/manifest.sha256` | `<sha256><space><space><relative_path>` entries | immutable for a pinned fixture set |
| Fixture traces | fixture authoring | replay | `traces/fixtures/*.jsonl` | JSONL domain events with deterministic ordering fields expected by replay | append-only; no in-place edits |
| Replay event stream | `src.replay` / `src.runner` | analyzer, audit, gate | `runs/<run_id>/events.jsonl` | event objects with `kind`; `STEP` events include `seq` (strictly increasing), `t`, `state_hash_pre`, `actions`, `reward`, `cost` | append-only per run |
| Analysis report | `src.analyze` | audit, gate, reviewers | `runs/<run_id>/report.json` | `report_version`, `run_id`, `source_events_path`, `source_events_sha256`, `event_count`, `analysis.deterministic_input_valid`, `analysis.scalar_summary` | immutable output per analyzed event file |
| Swarm logs (optional) | swarm scripts | audit/review | `runs/run-<id>-manager.jsonl`, `runs/run-<id>-agent*.jsonl`, `runs/run-<id>-swarm.jsonl` | append-only JSONL log events | append-only |

## Replay Boundaries and Determinism Contract

Boundary tuple:

- `spec`: approved `plans/PLAN.md`
- `trace`: frozen workload trace (`traces/fixtures/*.jsonl` or declared tape input)
- `seed|tape`: exactly one deterministic driver input

Determinism requirements:

- Identical boundary tuple must produce identical ordered event streams and derived hashes.
- Event ordering is deterministic and represented by monotonic, non-duplicate `seq` values.
- Replay can tee emitted events to `runs/<run_id>/events.jsonl` for reproducible audit.

Hash linkage:

- Replay run handle includes `RunHandle.log_bundle_sha256` for tee output integrity.
- Analyzer report includes `source_events_sha256` binding report content to a concrete events file.

## Admissibility and Offline Measurement Boundaries

- Comparator alternatives must exclude hidden/private state and future information.
- Admissibility is enforced before regret attribution.
- Measurement and attribution are offline only; analyzer runs after execution and does not mutate execution outcomes.
- No online learning behavior is permitted during measurement.

## Failure Modes

Hard-fail conditions include:

- Invalid action emitted by a policy for the current state.
- Malformed JSONL or non-object event entries where object events are required.
- Nondeterministic ordering evidence (missing/non-integer/duplicate/out-of-order `seq`).
- Admissibility violations (hidden state, future RNG outcomes, or oracle comparator paths).

Expected failure behavior:

- Emit deterministic error payloads.
- Return non-zero status for failing commands.
- Do not emit a valid regret attribution on inadmissible evaluation paths.

## Verification Commands

Run locally:

```bash
make check
make gate
make smoke
```
