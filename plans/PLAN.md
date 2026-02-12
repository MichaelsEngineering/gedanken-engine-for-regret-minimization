# PLAN: Deterministic Manager Loop for Claim Contract Execution

## Authority
- Post-approval authority is `plans/PLAN.md`; this file is operationally canonical for implementation and evaluation.
- Generated from `plans/claim/definition-sec-001/core_claim.contract.yaml` with strict validation enabled.
- Primary claim section: `SEC-001`.
- Claim summary: Provide a deterministic replay runner (CLI + library) that replays a fixed trace with a declared seed or tape and produces a stable derived-state hash while streaming JSONL to stdout.
- Repository guardrails source: `AGENTS.md`.

## Contract Constraints

- Python 3.11.
- No new schema files under schemas/**.
- Honor CODEOWNERS and manager-locked files.
- Stop work at 5 minutes if not complete.

## Contract Acceptance

- CLI runs with declared inputs and prints JSONL replay stream to stdout.
- Running the same replay twice yields the same derived-state hash.
- Unit tests cover CLI wiring, deterministic replay, and step ordering.
- make check passes.

## Invariant Extraction Table

| INV-ID | SPEC-ID | Test Name | Minimal Code Surface |
| --- | --- | --- | --- |
| `inv_conservation_history` | `SPEC-001` | `test_gate_replay_identity` | `src/runner.py`, `tests/test_runner.py` |
| `inv_conservation_trace` | `SPEC-002` | `test_gate_trace_invariance` | `traces/*.jsonl`, `tests/test_swarm_gate.py` |
| `inv_conservation_dimensionality` | `SPEC-003` | `test_gate_dimensionless_regret` | `src/validation_engine.py`, `src/scalarization/__init__.py`, `tests/test_analyzer_stub.py` |
| `inv_offline_isolation` | `SPEC-004` | `test_gate_oracle_violation_hard_fail` | `src/validate.py`, `tests/test_validate.py` |
| `inv_admissibility` | `SPEC-005` | `test_gate_asymmetric_externality_counterexample` | `src/`, `tests/` |

## Lane Assignments and Ownership

- Manager: owns plan structure, delegation, integration, and gate decisions.
- `agent1`: assigned SPEC range `SPEC-001..SPEC-001`.
- `agent2`: assigned SPEC range `SPEC-002..SPEC-002`.
- `agent3`: assigned SPEC range `SPEC-003..SPEC-003`.
- `agent4`: assigned SPEC range `SPEC-004..SPEC-004`.
- `agent5`: assigned SPEC range `SPEC-005..SPEC-005`.
- Disjoint ownership rule: only one active worker may touch a given `touched_paths` slice.

## Execution Loop

Repeat until deterministic exit gates are green:
1. `plan`: read repo state and define tranche objective.
2. `delegate`: emit up to 5 work items with disjoint `touched_paths`.
3. `workers execute`: workers run only assigned scope and tests.
4. `integrate`: manager merges worker artifacts and resolves conflicts.
5. `verify`: run deterministic gate plus targeted tests.
6. `checkpoint`: update status/registry and tranche record.
Exit condition: all termination rules satisfied and deterministic gates pass.

## Work Item Schema (Manager -> Worker)

Each delegated task must be a single object with exactly:
- `goal`
- `constraints`
- `touched_paths`
- `acceptance_tests`
- `artifacts_to_emit`
- `rollback_plan`

## Worker Response Schema (Worker -> Manager)

Each worker response must include:
- `diff_summary` (3-7 bullets)
- `files_changed`
- `tests_run`
- `results` (pass/fail + key output lines)
- `risks` (0-3 bullets)
- `next_actions` (0-5 bullets)
- `open_questions` (only if blocking)

## Initial Tranche Work Items

### WI-001 (agent1)
```yaml
goal: Finalize invariant-to-spec mapping with explicit hard-fail predicates.
constraints:
  - No code or test edits.
  - Keep output deterministic and scoped to assigned SPEC-ID rows.
touched_paths:
  - plans/PLAN.md (SPEC table rows only)
acceptance_tests:
  - pytest -q tests/test_generate_plan.py -k section_order
artifacts_to_emit:
  - runs/swarm/STATUS.md
  - runs/swarm/worker1/YYYYMMDD-HHMM/NOTES.md
rollback_plan: Revert SPEC table row edits and regenerate plan from contract.
```

### WI-002 (agent2)
```yaml
goal: Author/update assigned SPEC sections with executable predicates and tests.
constraints:
  - Edit only assigned spec sections.
  - No shared-file restructuring.
touched_paths:
  - plans/PLAN.md (SPEC sections only)
acceptance_tests:
  - pytest -q tests/test_generate_plan.py -k integration
artifacts_to_emit:
  - runs/swarm/STATUS.md
  - runs/swarm/worker2/YYYYMMDD-HHMM/NOTES.md
rollback_plan: Restore previous SPEC sections and rerun generator.
```

### WI-003 (agent3)
```yaml
goal: Implement falsification tests for replay, trace, dimensionality, and admissibility.
constraints:
  - Tests before implementation changes.
  - No edits outside tests/.
touched_paths:
  - tests/**
acceptance_tests:
  - pytest -q tests/test_swarm_gate.py tests/test_generate_plan.py
artifacts_to_emit:
  - runs/swarm/STATUS.md
  - runs/swarm/worker3/YYYYMMDD-HHMM/NOTES.md
  - runs/swarm/worker3/YYYYMMDD-HHMM/DIFFSTAT.txt
rollback_plan: Revert test changes to last green commit and re-run targeted tests.
```

### WI-004 (agent4)
```yaml
goal: Implement minimal src changes required by existing failing tests.
constraints:
  - No interface expansion without matching tests and docs.
  - No network, time, or unseeded randomness.
touched_paths:
  - src/**
acceptance_tests:
  - make gate
  - pytest -q tests/test_runner.py
artifacts_to_emit:
  - runs/swarm/STATUS.md
  - runs/swarm/artifacts/REGISTRY.csv
  - runs/swarm/worker4/YYYYMMDD-HHMM/NOTES.md
rollback_plan: Revert lane-local src edits and validate gate baseline.
```

### WI-005 (agent5)
```yaml
goal: Produce replay/audit artifacts and register provenance checksums.
constraints:
  - Append-only trace handling.
  - Do not change source code paths.
touched_paths:
  - runs/**
  - traces/**
acceptance_tests:
  - make gate
  - make smoke
artifacts_to_emit:
  - runs/swarm/STATUS.md
  - runs/swarm/artifacts/REGISTRY.csv
  - runs/swarm/worker5/YYYYMMDD-HHMM/NOTES.md
rollback_plan: Remove derived run artifacts for the slice and replay from last green gate.
```

## Spec Sections

### Hard-fail Invariants
- `inv_conservation_history`: Fixed (spec, seed, trace) and complete state imply pure-function execution with identical metrics, decisions, and hash. (violation: `hard failure`).
- `inv_conservation_trace`: Workload trace is independent of evaluated alternative under frozen boundary conditions. (violation: `hard failure`).
- `inv_conservation_dimensionality`: Aggregated regret is defined only when all components are dimensionless. (violation: `hard failure`).
- `inv_offline_isolation`: Measurement and attribution occur post-execution with no online learning updates during measurement. (violation: `hard failure`).
- `inv_admissibility`: Comparator excludes hidden state and future information; observation horizon cannot exceed evaluated agent horizon. (violation: `hard failure`).

### Worker-Assignable Specs

#### SPEC-001
- Owner lane: `agent1`
- Source invariant: `inv_conservation_history`
- Predicate: Fixed (spec, seed, trace) and complete state imply pure-function execution with identical metrics, decisions, and hash.
- Test name: `test_gate_replay_identity`
- Pass condition: all compared outputs are identical
- Minimal code surface: `src/runner.py`, `tests/test_runner.py`

#### SPEC-002
- Owner lane: `agent2`
- Source invariant: `inv_conservation_trace`
- Predicate: Workload trace is independent of evaluated alternative under frozen boundary conditions.
- Test name: `test_gate_trace_invariance`
- Pass condition: trace equality holds across admissible counterfactual runs
- Minimal code surface: `traces/*.jsonl`, `tests/test_swarm_gate.py`

#### SPEC-003
- Owner lane: `agent3`
- Source invariant: `inv_conservation_dimensionality`
- Predicate: Aggregated regret is defined only when all components are dimensionless.
- Test name: `test_gate_dimensionless_regret`
- Pass condition: all r_i are dimensionless before aggregation
- Minimal code surface: `src/validation_engine.py`, `src/scalarization/__init__.py`, `tests/test_analyzer_stub.py`

#### SPEC-004
- Owner lane: `agent4`
- Source invariant: `inv_offline_isolation`
- Predicate: Measurement and attribution occur post-execution with no online learning updates during measurement.
- Test name: `test_gate_oracle_violation_hard_fail`
- Pass condition: if O(a_star) > O(a_eval), evaluation aborts and no regret value is emitted
- Minimal code surface: `src/validate.py`, `tests/test_validate.py`

#### SPEC-005
- Owner lane: `agent5`
- Source invariant: `inv_admissibility`
- Predicate: Comparator excludes hidden state and future information; observation horizon cannot exceed evaluated agent horizon.
- Test name: `test_gate_asymmetric_externality_counterexample`
- Pass condition: oracle comparator path is marked invalid; admissible comparator path yields decision-regret attribution
- Minimal code surface: `src/`, `tests/`

### Spec Glossary
- `tau`: metric set, units, dimensions, and ordering relations fixed for one evaluation
- `s`: complete boundary conditions including immutable workload trace and RNG seed state
- `a`: admissible action/policy/design candidate
- `a_prime`: second alternative used for admissible comparability checks
- `A_adm`: alternatives admissible under declared information and observation-horizon constraints
- `I_h`: information available at decision time
- `O`: declared horizon of variables/timesteps/signals visible to an alternative
- `M_tau`: task-context-specific deterministic outcome map
- `M_i`: i-th metric component in multi-metric outcome
- `C_i`: normalization scale required for dimensionless component regret
- `r_i`: (M_i(s,a*) - M_i(s,a)) / C_i(s)
- `w_i`: scalarization coefficient for normalized component regret
- `J`: single-metric objective used in scalar regret comparator
- `a_star`: best admissible alternative under objective and horizon constraint
- `Regret`: aggregate counterfactual loss relative to a_star
- `spec`: frozen specification input for replay
- `seed`: deterministic random seed input
- `trace`: immutable workload trace used as boundary condition evidence
- `decision_sequence`: ordered decisions emitted during execution
- `derived_state_hash`: hash of derived replay state for determinism checks
- `scenario_minimal`: minimal counterexample scenario for clairvoyance-regret detection

## Merge Order

1. `agent1` invariant extraction outputs
2. `agent2` plan-embedded specs
3. `agent3` falsification tests
4. `agent4` minimal implementation
5. `agent5` replay and audit artifacts

## Gate Definitions

- Deterministic replay gate: identical `(spec, seed, trace)` yields identical derived-state hash.
- Trace invariance gate: alternatives must not mutate frozen workload trace.
- Dimensionality gate: aggregate regret is dimensionless and unit-invariant.
- Admissibility gate: a is admissible iff a = pi(I(h)) and does not use hidden/private state, future RNG outcomes, or external oracle information
- Observable gate `replay_identity` via `test_gate_replay_identity`: all compared outputs are identical
- Observable gate `trace_invariance` via `test_gate_trace_invariance`: trace equality holds across admissible counterfactual runs
- Observable gate `dimensionless_regret` via `test_gate_dimensionless_regret`: all r_i are dimensionless before aggregation
- Observable gate `oracle_violation_hard_fail` via `test_gate_oracle_violation_hard_fail`: if O(a_star) > O(a_eval), evaluation aborts and no regret value is emitted
- Observable gate `asymmetric_externality_counterexample` via `test_gate_asymmetric_externality_counterexample`: oracle comparator path is marked invalid; admissible comparator path yields decision-regret attribution

Single gate command:

```bash
make gate
```

## Termination Rule (Per Slice)

Stop a slice only when all are true:
1. All `acceptance_tests` pass.
2. All `artifacts_to_emit` are created or updated.
3. Manager acceptance checklist is complete.

## State Externalization

- Canonical manager status: `runs/swarm/STATUS.md`
  - Required fields: `current_objective`, `active_work_items`, `last_green_gate`, `unresolved_risks`, `next_tranche_plan`.
- Artifact registry: `runs/swarm/artifacts/REGISTRY.csv`
  - Columns: `artifact_id,type,inputs_spec_seed_trace,sha256,created_at_utc,purpose,linked_tests,producer`.
- Per-worker scratchpad: `runs/swarm/workerN/YYYYMMDD-HHMM/NOTES.md`
- Optional per-worker diffstat: `runs/swarm/workerN/YYYYMMDD-HHMM/DIFFSTAT.txt`

## Checkpoint Cadence and Budgets

- Tranche size target: 1-5 files, <400 LOC net unless escalation is approved.
- Budgets per tranche: tool calls <= 12, test runtime <= 5 minutes cumulative.
- Required checkpoint steps:
  1. Update `runs/swarm/STATUS.md`.
  2. Run `make gate`.
  3. Record results in status and `runs/swarm/artifacts/REGISTRY.csv` when artifacts are emitted.
- Failure policy: if a gate fails twice for the same slice, reduce scope and serialize changes.

## Conflict Resolution and Escalation

Escalate to manager-only decision when:
- Touching manager-locked/shared files (gates, workflows, CODEOWNERS, core schemas).
- Changing SPEC semantics or invariants.
- Cross-lane dependencies block progress for more than one tranche.
Tie-break rule: manager records rationale in status and adds/updates a regression test for non-trivial risk.

## End-to-End Verification

Beyond unit gates, run one smoke path:
```bash
make smoke
```

## Manager Acceptance Checklist

- What changed (1 sentence)
- Why (1 sentence)
- Commands run + results
- Known risks + mitigations
- Follow-ups (if any)

## Required Final Chat Output

1. Tranche summary
2. Files changed
3. Commands run
4. Test results
5. Risks and follow-ups

## Definition of Done by Lane

- Manager: all tranche checkpoints complete and deterministic gates green.
- `agent1`: invariant to spec mapping complete and deterministic.
- `agent2`: spec sections are executable and ambiguity-free.
- `agent3`: falsification tests are present and passing.
- `agent4`: minimal implementation passes existing tests without nondeterministic behavior.
- `agent5`: audit artifacts are append-only and registry entries include checksums.

## Failure and Rollback

- Abort immediately on schema validation errors or gate failures.
- Post exact failing commands and key output lines in tranche notes.
- Revert only lane-local changes when rolling back a slice.
- Never merge failing artifacts.

## Assumptions Log

- `asm_fixed_context` (section `SEC-001`): Task context tau is fixed and immutable during evaluation.
- `asm_causal_closure` (section `SEC-004`): System and environment are causally closed and replayable from boundary condition s.
- `asm_deterministic_map` (section `SEC-001`): Outcome mapping M_tau(s,a) is deterministic for fixed inputs.
- `asm_resettable_dependencies` (section `SEC-004`): External dependencies are resettable/mocked/replayable; otherwise counterfactual is undefined.

### Artifact Producer Hints
