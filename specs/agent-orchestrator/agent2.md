# Agent 2 Task Spec

## Authority
- Placeholder spec to satisfy the agent-orchestrator gate `spec_path` uniqueness rule.

## Scope
- No code or config changes required.
- Do not change dependencies or repo-wide settings.

## Acceptance
- Emit `runs/<run_id>/agent2/out.yaml` with `contract_version`, `status`, and exactly one of `result` or `error`.
