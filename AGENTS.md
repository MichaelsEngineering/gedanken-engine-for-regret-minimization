# AGENTS.md

# Gedanken Engine for Regret Minimization

## Coordination Lab

## 1. Goals and Invariants

- Spec-first, replayable agent coordination.
- Keep a clean, linear history with a rebase-first workflow.

Invariants:

- Spec is the source of truth.
- Ledger is append-only.
- Coordination can only append intents.
- Execution can only append results.
- Human intervention must be explicitly logged.
- Replay determinism: same spec + seed + ledger => same derived-state hash.

Example usage to demonstrate Minimal falsifier:
Two agents. One turn. Two actions. Asymmetric private information plus an externality cost.

Out of scope

- Publishing packages.
- Modifying secrets or CI credentials.
- Long-running expensive cloud jobs without explicit user request.

---

## 2. Agent Roles

- **Planner**: Turn a user request into a concrete plan and a small diff set.
- **Implementer**: Write code that passes tests, typing, and docstrings.
- **Reviewer**: Self-review and propose alternatives or rollbacks.
- **Tester**: run tests of functions

---

## 3. Decision Policy (Impact, Risk, Cost)

Impact

- Low: comments, docs, config toggles.
- Medium: new small module or function, minor refactors.
- High: API changes, train loop edits, data schema changes.

Risk

- Low: local lints, added tests, non-executable docs.
- Medium: isolated module change with tests.
- High: touching training loop, logging schema, or configs used in CI.

Cost

- Low: < 30 seconds unit tests and static checks.
- Medium: quick CPU-only script runs.
- High: GPU training or large dataset downloads.

Rule

- Only proceed when Impact + Risk + Cost fits the user instruction and guardrails.
- Default to the smallest diff that satisfies the requirement.
- For high-risk changes, split into staged PRs: interface first, behavior second, performance third.

---

## 4. Repository Guardrails

- Python 3.11.
- `pyproject.toml` is the single source of dependency truth. Use `uv` for dev and CI.
- Use rebase-first Git workflow. No merge commits on feature branches.
- All changes must pass `make check` (ruff + black + mypy + pytest + coverage).
- Use `make smoke` whenever training/eval code paths change.

---

## 5. Standard Working Branch Flow

1. Create a small feature branch

```bash
git switch -c feat/<short-task-name>
```

2. Make minimal changes with tight commits

```bash
git add -p
git commit -m "feat: <concise change>"
```

3. Rebase often

```bash
git fetch origin
git pull --rebase origin main
```

4. Push when checks pass

```bash
git push -u origin HEAD
```

---

## 6. Coding Standard

- Typing: mypy-clean public APIs, explicit return types.
- Style: black, ruff.
- Tests: pytest unit tests for new functions and bug fixes.
- Docs: docstring for every public function.
- Config: do not break existing configs. Add new ones as opt-in.

---

## 7. Safe-Run Protocol

Default quick checks:

```bash
uv sync --dev
make check
```

Experiment smoke test

- CPU-only tiny run with fixed seed.
- Writes logs to a temp run directory.
- Generates tiny plots to verify pipeline wiring.

Never do by default

- Long GPU training.
- Network downloads > few MB.
- Any destructive operation.
- Modifying CI secrets or repo settings.

---

## 8. Spec, Ledger, and Traces

Spec locations:

- `specs/spec.md` (authoritative spec)
- `specs/*.yaml` (scenario/config inputs)

Ledger / trace locations (default):

- `traces/<trace_id>.jsonl` (ad hoc runs)
- `traces/demo.jsonl` (README demo)
- `traces/golden/<scenario_name>.jsonl` (committed regression traces)
- `traces/evals/<dataset_name>/<run_name>.jsonl` (eval outputs)

Optional alternative (not default; use only if you need artifacts per run):

- `runs/<trace_id>/events.jsonl`
- `runs/<trace_id>/spec_snapshot.yaml`
- `runs/<trace_id>/report.json`

Event schema rules:

- JSONL, one DomainEvent per line (append-only).
- Required keys: `kind`, `trace_id`, `seq`, `ts`, `meta`, plus event-specific fields.
- `seq` strictly increases within a file.
- No in-place edits. If you need compaction, generate a new file and keep the original.

Why JSONL:

- Maps 1:1 to append-only semantics.
- Streaming-friendly and easy to diff.
- Stable per-line schema validation and efficient replay/tail/seek.

## 9. Config and Backend Guidance

- TO DO

## 10. Logging and Metrics

- To Do

---

## 11. PR Checklist

- [ ] Focused branch and diff.
- [ ] Spec documented
- [ ] Unit tests added/updated as specs instruct.
- [ ] Write code until unit tests pass
- [ ] Write code until all tests pass
- [ ] "make smoke" command runs.
- [ ] Check README updated if needed.
- [ ] Changelog entry.

---

## 12. Run Permission Matrix

| Action type                         | Default | Needs explicit user ok |
| ----------------------------------- | ------- | ---------------------- |
| Lint, type check, unit tests        | Allowed | No                     |
| Edit docs, comments                 | Allowed | No                     |
| Add small pure-Python helper        | Allowed | No                     |
| Modify train loop or logging schema | Ask     | Yes                    |
| Download datasets > 10 MB           | Ask     | Yes                    |
| Long training > 2 minutes           | Ask     | Yes                    |
| Change CI config                    | Ask     | Yes                    |

---

## 13. Prompt Protocol

Planning prompt

- Summarize goal in 1 sentence.
- List 3–5 minimal steps.
- Identify changes.
- Confirm spec exists
- State a test for the spec.

Implementation prompt

- Minimal diff with signatures, tests, docstrings to passes tests.
- Config flags and defaults.
- Run commands.

Review prompt

- Self-critique implementation.
- Verify checklist.
- Rollback plan.
- Check for alternatives

Tester prompt

- Run tests of functions

---

## 14. Failure Handling & Rollback

- If a check fails, post exact command and error.
- Propose hotfix or revert.
- Never push failing main.

---

## 15. Communication Style

- Concise. Commands always listed.
- Reference paths.
- Prefer small diffs.

---
