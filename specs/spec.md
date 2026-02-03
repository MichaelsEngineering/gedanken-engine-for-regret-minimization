# Spec: Coordination Lab

Authority model:

- The spec is the source of truth.
- The trace is the ground-truth record of what happened.
- Derived state is computed by replaying the trace via a pure reducer.
- Event schema is planned to be defined in `spec/events.py` (Pydantic models). Runtime, tests, and TUI must use this schema as source of truth once implemented.

Hard invariants (must be enforced by tests):

1. Append-only trace. No mutation, no delete, no in-place edits.
2. Separation of duties:
   - Coordination appends intents only.
   - Execution appends results only.
   - Humans append interventions only.
3. Private info is capability-scoped:
   - Agents only receive their view: public history plus their private observations.
   - No private leakage to other agents or public panes.
4. Replay determinism:
   - Same spec + seed + trace => identical derived-state hash.
5. Complete causal declaration:
   - All exogenous inputs are declared in trace or tape and referenced by the replay boundary tuple.

Reducer API (must be deterministic and side-effect free):

- `reduce_events(trace_id: str, events: Sequence[DomainEvent], *, spec: dict | None = None) -> DerivedState`
- `state_hash(state: DerivedState) -> str`

Replay semantics:

- Replay boundary tuple is explicit and immutable:
  - `(spec_ref, trace_ref, seed_or_tape_ref, env_id, policies_id, metrics_id)`
- Complete causal declaration: all exogenous inputs must be declared in the trace or tape and referenced by the boundary tuple.
- Step ordering is fixed: observe -> act -> validate -> transition -> score -> log.
- Multi-agent concurrency model is synchronous joint action.
  - Tie-breaking for ordering is deterministic by sorted `agent_id`.
- Termination occurs when the trace is exhausted or the environment signals done.
  - If both are available, they must agree or replay fails with a machine-readable error.

Replay runner API (planned):

- CLI:
  - `replay --env ... --policies ... --metrics ... --trace ... --seed|--tape ... --out ... [--tee]`
- Library:
  - `run = replay.run(config) -> RunHandle`
  - `RunHandle` must include `run_dir`, `log_bundle_sha256`, `exit_code`, and `error_payload` on failure.

Required interfaces (planned):

- Environment:
  - `reset(init, rng) -> state`
  - `observe(state) -> dict[agent_id, obs]`
  - `validate_action(state, agent_id, action) -> ValidationResult`
  - `step(state, joint_action, exogenous_x_t, rng) -> (next_state, reward, cost, info)`
- Policy:
  - `act(obs, ctx) -> action`
  - `ctx` may include only declared, non-causal metadata (policy_id, step index, action schema version).
  - Policies must not receive raw state.
- Metrics:
  - `per_step(t, state_hash_pre, action, reward, cost, info) -> metric_contribs`
  - `aggregate(contribs_stream) -> derived_metrics`
  - Must be re-runnable offline from logs only.
- Logger/Ledger:
  - `emit(event_obj)` append-only
  - Enforces event ordering and schema versioning.

Seed handling:

- Seed is immutable run metadata stored in the trace header event.
- The first event in every trace is `TraceStarted`, carrying `seed` and references to spec/policy/prompt.
- If a tape is used, `TraceStarted` must include a `tape_ref` that resolves to the tape source.
- Example:
  - `TraceStarted(kind="TRACE_STARTED", trace_id, seq=0, ts, seed, tape_ref, spec_ref, policy_ref, prompt_ref, meta={...})`

Acceptance criteria (planned):

- `make demo` produces `traces/demo.jsonl` and launches a replay UI.
- `make test` enforces all invariants.
- `make eval` produces an eval trace and a rubric score output.
