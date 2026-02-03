# Agent 1 Task Spec: Scaffolder (Replay Fixtures)

## Authority
- Follow `AGENTS.md` ownership boundaries.
- This task supports the deterministic replay runner effort.

## Scope
- Allowed files: new files only.
- Create `traces/fixtures/` with minimal deterministic JSONL traces for replay tests.
- Add a fixtures manifest file (new file) listing SHA-256 hashes for each fixture.
- Do not edit existing files or dependencies.
- Produce git diff evidence from staged changes.
- Add or update tests that consume these fixtures (if tests exist in scope).
- Write output to `runs/<run_id>/agent1/out.yaml`.

## Acceptance
- Fixtures are deterministic and minimal.
- Only new files are created.
- `runs/<run_id>/agent1/out.yaml` result includes:
  - `diff_name_status` from `git diff --cached --name-status`
  - `diff_patch` from `git diff --cached`
  - `test_files` list (non-empty)
- Emit `runs/<run_id>/agent1/out.yaml` with `contract_version`, `status`, and exactly one of `result` or `error`.
