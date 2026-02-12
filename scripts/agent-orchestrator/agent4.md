# Agent 4 Task Spec: Analyzer

## Authority
- Analyzer outputs are in scope when assigned SPEC-003 (`inv_conservation_dimensionality`).

## Scope
- Allowed files: `src/validation_engine.py`, `src/metrics/**`, `src/scalarization/**`, `tests/**`.
- Enforce explicit `C_i(s)` normalization, dimensionless `r_i`, and dimensionless aggregate regret.
- Enforce unit-change invariance for time units (`ms` vs `s`) as a hard-fail gate.
- Add/maintain tests that verify:
  - dimensionless regret gate behavior,
  - `scale_c_i > 0` validation,
  - nonnegative weights,
  - invariance pass/fail paths.
- Stage changes and produce git diff evidence.
- Write output to `runs/<run_id>/agent4/out.yaml`.

## Acceptance
- `runs/<run_id>/agent4/out.yaml` result includes:
  - `diff_name_status` from `git diff --cached --name-status`
  - `diff_patch` from `git diff --cached`
  - `test_files` list (non-empty)
- Emit `runs/<run_id>/agent4/out.yaml` with `contract_version`, `status`, and exactly one of `result` or `error`.
