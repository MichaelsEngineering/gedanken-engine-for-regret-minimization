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

Reducer API (must be deterministic and side-effect free):

- `reduce_events(trace_id: str, events: Sequence[DomainEvent], *, spec: dict | None = None) -> DerivedState`
- `state_hash(state: DerivedState) -> str`

Seed handling:

- Seed is immutable run metadata stored in the trace header event.
- The first event in every trace is `TraceStarted`, carrying `seed` and references to spec/policy/prompt.
- Example:
  - `TraceStarted(kind="TRACE_STARTED", trace_id, seq=0, ts, seed, spec_ref, policy_ref, prompt_ref, meta={...})`

Acceptance criteria (planned):

- `make demo` produces `traces/demo.jsonl` and launches a replay UI.
- `make test` enforces all invariants.
- `make eval` produces an eval trace and a rubric score output.
