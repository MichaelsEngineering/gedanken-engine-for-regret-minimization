# AGENTS.md

# Gedanken Engine for Regret Minimization

## Coordination Lab

## 1. Design Goals and System Invariants

Design Goals

- Deterministic evaluation of decision policies under identical initial conditions
- Explicit separation of coordination (policy selection) and execution (actuation)
- Replayable, auditable traces suitable for offline evaluation

Workflow

- Keep a clean, linear history with a rebase-first workflow.

System Invariants

- The specification is the sole source of truth.
- Traces are append-only and immutable.
- Coordination may only emit intents.
- Execution may only emit results.
- All human intervention is logged explicitly.
- Deterministic replay: identical spec, seed, and trace produce identical derived-state hashes.

Minimal Counterexample Scenario:
Two agents, one decision step, two admissible actions.
Asymmetric private information with an externality cost.

This scenario is sufficient to falsify naive agent designs that lack explicit counterfactual evaluation or regret accounting.

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

## 2.1 Multi-Agent Execution Protocol (Max 6)

Cap at 6 concurrent lanes total (Integrator + up to 5 worker lanes). If more work is needed, split into phases and merge serially.

Integrator (single lane)

- Merges in order, resolves conflicts, runs full checks, updates golden outputs.
- Owns shared files listed under "Documented CODEOWNERS (Social Contract + File)."

Worker lanes (5 max)

- **Scaffolder**: repo layout, `.gitignore`, new directories/files only.
- **Schema+Validate**: `schemas/**`, `src/validate.py`, manifest hashing helpers, validation tests.
- **Core Loop**: `src/runner.py`, `src/executor.py`, `src/env/**`, `src/policy/**`, tests.
- **Analyzer**: `src/analyzer.py`, `src/metrics/**`, `src/scalarization/**`, tests.
- **Bench+Bundle+Docs**: `bench/**`, `scripts/**`, `artifacts/**`, `docs/**` (except `docs/ARCHITECTURE.md`), golden outputs, doc polish.

Merge order (serial)

1. Scaffolding
2. Schemas + validation
3. Core execution loop
4. Offline analysis
5. Bench + bundle + docs

---

## 2.2 Documented CODEOWNERS (Social Contract + File)

These patterns are documented here and mirrored in `CODEOWNERS`. Enforcement depends on repo settings.

Integrator-locked shared files

- `AGENTS.md`
- `CHANGELOG.md`
- `Makefile`
- `README.md`
- `pyproject.toml`
- `uv.lock`
- `.github/workflows/**`
- `docs/ARCHITECTURE.md`

Role ownership (documented)

- Scaffolder: `.gitignore`, repo layout additions (new dirs/files only)
- Schema+Validate: `schemas/**`, `src/validate.py`, validation tests
- Core Loop: `src/runner.py`, `src/executor.py`, `src/env/**`, `src/policy/**`
- Analyzer: `src/analyzer.py`, `src/metrics/**`, `src/scalarization/**`
- Bench+Bundle+Docs: `bench/**`, `scripts/**`, `artifacts/**`, `docs/**` (except `docs/ARCHITECTURE.md`)

---

## 2.3 Per-Agent Definition of Done

- Work only in owned paths; request Integrator changes for shared files.
- Add at least one test for new behavior or determinism checks.
- Run targeted tests and `make check` before PR; run `make smoke` if execution paths change.
- Do not change spec semantics unless explicitly instructed; reference spec sections in PR.
- Record any manual interventions explicitly in trace/log outputs.

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
- All changes must pass `make check` (ruff check + ruff format check + mypy + pytest + coverage).
- Use `make smoke` whenever training/eval code paths change.

---

## 5. Standard Working Branch Flow

1. Create a small feature branch

```bash
git switch -c feat/<lane>-<short-task-name>
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

- `theory/theory.md` (theory source of truth)
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
- [ ] Ownership boundaries respected (see Documented CODEOWNERS).
- [ ] Shared files touched only by Integrator.
- [ ] Spec documented
- [ ] Unit tests added/updated as specs instruct.
- [ ] Write code until unit tests pass
- [ ] Write code until all tests pass
- [ ] "make smoke" command runs.
- [ ] Canonical reproduction run when applicable (`./scripts/reproduce.sh canonical`); golden outputs updated intentionally.
- [ ] Check README updated if needed.
- [ ] Changelog entry in CHANGELOG.md (repo root, 2026 best practice).

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
