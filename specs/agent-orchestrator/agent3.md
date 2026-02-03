# Agent 3 Task Spec: Core Loop (Replay Runner)

## Authority
- Follow `specs/spec.md` replay semantics.
- Follow `AGENTS.md` ownership boundaries.

## Scope
- Allowed files: `src/replay.py`, `src/runner.py`, `src/env/**`, `src/policy/**`, `tests/**`.
- Implement CLI in `src/replay.py` using `argparse` only.
- Keep `src/runner.py` as a pure library module (no CLI).
- Enforce step ordering: observe -> act -> validate -> transition -> score -> log.
- Enforce synchronous joint action with deterministic tie-break by sorted `agent_id`.
- Override `ArgumentParser.error()` and `ArgumentParser.exit()` to emit deterministic, OS-independent error payloads.
- No dynamic defaults from environment (cwd, time, hostname).
- Stream JSONL to stdout; support `--tee` to write to `run_dir`.
- Stage changes and produce git diff evidence.
- Write output to `runs/<run_id>/agent3/out.yaml`.

## Acceptance
- Unit tests cover CLI wiring, deterministic errors, step ordering, and hash determinism.
- `runs/<run_id>/agent3/out.yaml` result includes:
  - `diff_name_status` from `git diff --cached --name-status`
  - `diff_patch` from `git diff --cached`
  - `test_files` list (non-empty)
- Emit `runs/<run_id>/agent3/out.yaml` with `contract_version`, `status`, and exactly one of `result` or `error`.
