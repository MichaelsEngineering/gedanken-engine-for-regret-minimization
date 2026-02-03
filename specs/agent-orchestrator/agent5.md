# Agent 5 Task Spec: Bench+Bundle+Docs

## Authority
- Follow `AGENTS.md` ownership boundaries.

## Scope
- Allowed files: `bench/**`, `scripts/**`, `artifacts/**`, `docs/**` (excluding `docs/ARCHITECTURE.md`).
- Add or update a bench or script artifact that validates replay fixtures (e.g., hash manifest check).
- Stage changes and produce git diff evidence.
- Write output to `runs/<run_id>/agent5/out.yaml`.

## Acceptance
- `runs/<run_id>/agent5/out.yaml` result includes:
  - `diff_name_status` from `git diff --cached --name-status`
  - `diff_patch` from `git diff --cached`
  - `test_files` list (non-empty)
- Emit `runs/<run_id>/agent5/out.yaml` with `contract_version`, `status`, and exactly one of `result` or `error`.
