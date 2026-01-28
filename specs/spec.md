# Spec: Coordination Lab

Authority model:

- The spec is the source of truth.
- The ledger is the ground-truth trace of what happened.
- Derived state is computed by replaying the ledger via a pure reducer.
- Event schema is defined in `spec/events.py` (Pydantic models). Runtime, tests, and TUI must use this schema as source of truth.

Hard invariants (must be enforced by tests):

1. Append-only ledger. No mutation, no delete, no in-place edits.
2. Separation of duties:
   - Coordination appends intents only.
   - Execution appends results only.
   - Humans append interventions only.
3. Private info is capability-scoped:
   - Agents only receive their view: public history plus their private observations.
   - No private leakage to other agents or public panes.
4. Replay determinism:
   - Same spec + seed + ledger => identical derived-state hash.

Reducer API (must be deterministic and side-effect free):

- `reduce_events(trace_id: str, events: Sequence[DomainEvent], *, spec: dict | None = None) -> DerivedState`
- `state_hash(state: DerivedState) -> str`

Seed handling:

- Seed is immutable run metadata stored in the trace header event.
- The first event in every trace is `TraceStarted`, carrying `seed` and references to spec/policy/prompt.
- Example:
  - `TraceStarted(kind="TRACE_STARTED", trace_id, seq=0, ts, seed, spec_ref, policy_ref, prompt_ref, meta={...})`

Acceptance criteria:

- `make demo` produces `traces/demo.jsonl` and launches a replay UI.
- `make test` enforces all invariants.
- `make eval` produces an eval trace and a rubric score output.
