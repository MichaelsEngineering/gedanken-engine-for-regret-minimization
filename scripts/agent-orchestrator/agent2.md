# Agent 2 Task Spec: Schema+Validate

## Authority
- Follow `AGENTS.md` ownership boundaries.
- No new schema files or schema version bumps.

## Scope
- Allowed files: `src/validate.py`, `tests/**`.
- Add validation for replay config and trace header invariants (TraceStarted, seed, tape_ref when applicable).
- Add unit tests for validation behavior.
- Stage changes and produce git diff evidence.
- Write output to `runs/<run_id>/agent2/out.yaml`.

## Acceptance
- Validation tests cover missing TraceStarted, missing seed, missing tape_ref when tape is requested.
- `runs/<run_id>/agent2/out.yaml` result includes:
  - `diff_name_status` from `git diff --cached --name-status`
  - `diff_patch` from `git diff --cached`
  - `test_files` list (non-empty)
- Emit `runs/<run_id>/agent2/out.yaml` with `contract_version`, `status`, and exactly one of `result` or `error`.
