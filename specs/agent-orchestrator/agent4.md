# Agent 4 Task Spec: Analyzer

## Authority
- Analyzer outputs are out of scope for this request.

## Scope
- Allowed files: `src/analyzer.py`, `src/metrics/**`, `src/scalarization/**`, `tests/**`.
- Add a minimal unit test that asserts analyzer modules are importable and deterministic stubs do not mutate state.
- Stage changes and produce git diff evidence.
- Write output to `runs/<run_id>/agent4/out.yaml`.

## Acceptance
- `runs/<run_id>/agent4/out.yaml` result includes:
  - `diff_name_status` from `git diff --cached --name-status`
  - `diff_patch` from `git diff --cached`
  - `test_files` list (non-empty)
- Emit `runs/<run_id>/agent4/out.yaml` with `contract_version`, `status`, and exactly one of `result` or `error`.
