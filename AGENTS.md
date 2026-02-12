# Gedanken Engine for Regret Minimization

## Coordination Lab

## 1. Design Goals and System Invariants

### Design Goals

- Deterministic evaluation of decision policies under identical initial conditions
- Explicit separation of coordination (policy selection) and execution (actuation)
- Replayable, auditable traces suitable for offline evaluation

### Workflow

- Keep a clean, linear history with a rebase-first workflow.

### System Invariants

- Stage 1 authority: `theory/theory.pdf` is the source for invariant extraction while constructing the initial plan.
- Post-approval authority: once `plans/PLAN.md` is created and explicitly user-approved, `plans/PLAN.md` is the sole source of truth for behavior and evaluation, including embedded specs.
- After explicit user approval of `plans/PLAN.md`, do not re-open or re-interpret `theory/theory.pdf` for implementation, testing, or reviews.
- Traces are append-only and immutable.
- Coordination may only emit intents.
- Execution may only emit results.
- All human intervention is logged explicitly.
- Deterministic replay: identical plan (including spec), seed, and trace produce identical derived-state hashes.

### Codex in VS Code checklist: Theory PDF → Plan (with embedded specs) → Swarm → Tests → src/

Plan: `plans/PLAN.md` is canonical and contains the specs used by the swarm.

#### VS Code session setup

- Open repo root in VS Code
- Ensure Codex VS Code extension is set to run with repo context
- Pin working files: README.md, AGENTS.md, theory/theory.pdf
- Disable any "auto-fix on save" for shared docs unless manager lane is active

#### Swarm contract (Manager + up to 5 lanes)

- Manager creates a short plan with explicit file ownership boundaries
- Lanes produce artifacts only in their owned paths; Manager merges and edits shared files

#### Step 1: Extract invariants from the PDF (no theory edits)

- Stage 1 is an active question/answer phase between `theory/theory.pdf` and plan construction.
- Resolve ambiguity during this step, before any implementation begins.

- Produce a list of hard-fail invariants stated as testable predicates
- Map each invariant to (a) a spec key, (b) a test name, (c) minimal code surface area

#### Step 2: Write PLAN artifact for the run

- Create or update a plan file describing lanes, merge order, and "definition of done" gates
- Require a single "gate command" that fails on nondeterminism, trace drift, or unit inconsistency
- Require explicit user approval of `plans/PLAN.md` before entering implementation lanes.
- After approval, do not consult `theory/theory.pdf`; treat `plans/PLAN.md` as operationally authoritative.

#### Step 3: Derive specs that encode admissibility and measurement

- Encode admissible baselines, observation model, and normalization scales
- Specs must be sufficient for a tester to build falsifying cases without reading the PDF

#### Step 4: Generate tests before implementation

- Deterministic replay test: same (spec, seed, trace) yields identical derived-state hash
- Trace invariance test: alternatives do not change workload trace unless modeled inside the frozen system
- Dimensionality test: aggregated regret scalar is dimensionless and invariant to unit changes (ms vs s)
- Admissibility test: comparator excludes hidden state and future RNG outcomes (no clairvoyance regret)

#### Step 5: Implement minimal src/ code to satisfy tests

- Implement only the smallest API needed to make the tests pass
- No online learning, no time, no network, no nondeterministic iteration sources

#### Step 6: Verify and record

- Run: uv sync --dev; make check; make gate (or repo-equivalent)
- Commit golden artifacts for the canonical run if used (trace, report, hashes)
- Update README sections to point to the canonical path and the gate command

### Swarm lane definitions and merge protocol (Codex / VS Code)

This repository assumes a manager-led swarm with explicit lane ownership. The purpose is not parallelism for speed, but controlled decomposition that preserves determinism and reviewability.

#### Manager lane (required)

##### Responsibilities

- During Stage 1 only, interpret the input theory (`theory/theory.pdf`) as an immutable contract for extracting invariants.
- After user approval of `plans/PLAN.md`, stop consulting `theory/theory.pdf` and execute against the approved plan/spec.
- Produce a concrete plan that decomposes theory into falsifiable invariants.
- Assign lanes with strict file ownership boundaries.
- Define explicit gate conditions for completion.

##### Constraints

- The manager is the only lane allowed to modify README.md and AGENTS.md.
- The manager owns `plans/PLAN.md` structure, lane assignments, and gates.
- Workers may edit only their assigned sections inside `plans/PLAN.md` (by SPEC-ID/INV-ID), not the plan structure.
- The manager performs the final merge and rejects any artifact that violates determinism or scope rules.

#### Lane 1: Invariant extraction

##### Owns

- Draft invariant lists and mappings (theory statement → INV-ID → SPEC-ID → test name).

##### Rules

- No code.
- No tests.
- Output must be phrased as executable predicates, not prose summaries.

#### Lane 2: Specification authoring

##### Owns

- `plans/PLAN.md` (Spec sections only, by SPEC-ID assignment)

##### Rules

- Specs must be sufficient to design tests without reading the theory PDF.
- All metrics must be dimensionless or explicitly normalized.
- Any ambiguity must be resolved in the spec, not deferred to code.

#### Lane 3: Test generation

##### Owns

- tests/

##### Rules

- Tests are written before implementation.
- Focus on falsification, not confirmation or demonstration.
- Must include nondeterminism detection, trace invariance, and admissibility checks.

#### Lane 4: Minimal implementation

##### Owns

- src/

##### Rules

- Implement only what is required to satisfy existing tests.
- No speculative abstractions.
- No hidden state, wall-clock time, network access, or unseeded randomness.

#### Lane 5 (optional): Audit and replay

##### Owns

- runs/
- traces/

##### Rules

- Ensure runs are replayable with identical outputs.
- Validate that traces are immutable across alternatives.
- Produce hashes and summaries only as derived artifacts.

### Merge and gate rules

All merges are manager-mediated and gated. No lane may self-merge.

#### Required gates

- Deterministic replay gate: identical (spec, seed, trace) produces identical outputs.
- Trace invariance gate: alternative evaluation does not mutate the workload trace.
- Dimensionality gate: regret and aggregates are unit-invariant.
- Admissibility gate: no access to hidden state or future information.

#### A lane's work is considered invalid if

- It modifies files outside its ownership.
- It introduces nondeterminism, implicit state, or external I/O.
- It relies on interpretive reading of the spec rather than explicit, testable specs.

### Running a swarm session in VS Code (Codex workflow)

This checklist describes how to run a complete theory-driven swarm session using Codex inside VS Code.

#### 1. Prepare the workspace

- Open the repository root in VS Code.
- Pin the following files: README.md, AGENTS.md, theory/theory.pdf.
- Ensure Codex is operating with full repo context.
- Confirm no background formatters or linters auto-modify shared documents.

#### 2. Manager: create the plan

- Read `theory/theory.pdf` and extract candidate invariants.
- Write a short plan defining:
  - Lanes and ownership
  - Expected artifacts per lane
  - Explicit gate conditions
- Commit the plan before any lane work begins.

#### 3. Launch lanes

- Assign each lane a single responsibility and path scope.
- Enforce file ownership boundaries.
- Require lanes to produce artifacts only, not commentary.

#### 4. Gate before implementation

- Review `plans/PLAN.md` (invariants + spec sections) and tests together.
- Reject any spec that cannot be falsified.
- Reject any test that relies on narrative interpretation or implicit state.

#### 5. Implement minimally

- Allow src/ work only after tests exist.
- Enforce seeded randomness, frozen traces, and deterministic iteration.
- Fail fast on any external I/O or time dependency.

#### 6. Verify and record

- Run all gates locally.
- Record the run under runs/ with hashes and metadata.
- Confirm traces remain unchanged across alternatives.

#### 7. Review as an engineering artifact

- Read the repo top-down: README -> plans -> specs -> tests -> src.
- Treat passing tests as evidence of theory compliance, not correctness claims.

### Minimal Counterexample Scenario

Two agents, one decision step, two admissible actions.
Asymmetric private information with an externality cost.

This scenario is sufficient to falsify naive agent designs that lack explicit counterfactual evaluation or regret accounting.

### Out of scope

- Publishing packages.
- Modifying secrets or CI credentials.
- Long-running expensive cloud jobs without explicit user request.

---

## 2. Agent Roles (abstract role taxonomy)

- **Planner**: Turn a user request into `plans/PLAN.md`, including embedded spec sections and gate criteria.
- **Test-writer**: Writes tests from specs.
- **Implementer**: Write code that passes tests, typing, and docstrings.
- **Reviewer**: Self-review and propose alternatives or rollbacks.
- **Tester**: Run tests and attempt to falsify invariants.

---

## 2.1 Multi-Agent Execution Protocol (Max 6)

Cap at 6 concurrent lanes total (Manager + up to 5 worker lanes). If more work is needed, split into phases and merge serially.
Workers may edit only their assigned sections inside `plans/PLAN.md` (by INV-ID/SPEC-ID) and their owned paths.

### Manager (single lane)

- Owns `plans/PLAN.md` (plan structure, lane assignments, and gates) and all manager-locked shared files.
- Merges in order, resolves conflicts, runs full checks, and updates golden outputs.
- Coordinates work by assigning INV-ID and SPEC-ID ranges from `plans/PLAN.md`.

### Worker lanes (5 max, implementation-oriented)

- **Scaffolder**: repo layout, `.gitignore`, new directories/files only.
- **Schema+Validate**: `plans/schemas/**`, `src/validate.py`, manifest hashing helpers, validation tests.
- **Core Loop**: `src/runner.py`, `src/executor.py`, `src/env/**`, `src/policy/**`, tests. Must satisfy replay and trace invariance gates.
- **Analyzer**: `src/analyzer.py`, `src/metrics/**`, `src/scalarization/**`, tests.
- **Bench+Bundle+Docs**: `bench/**`, `scripts/**`, `plans/artifacts/**`, `docs/**` (except `docs/ARCHITECTURE.md`), golden outputs, doc polish.

### Merge order (phased, manager-gated)

1. Scaffolding (structure only, no behavior)
2. Schemas + validation (data contracts only)
3. Core execution loop (must satisfy determinism gates)
4. Offline analysis (pure functions over traces)
5. Bench + bundle + docs (no semantic changes)

---

## 2.2 Documented CODEOWNERS (Social Contract + File)

These patterns are documented here and mirrored in `CODEOWNERS`. Enforcement depends on repo settings.

### Manager-locked shared files

- `plans/PLAN.md` (structure, gates, and section assignment only)
- `AGENTS.md`
- `CHANGELOG.md`
- `Makefile`
- `README.md`
- `pyproject.toml`
- `uv.lock`
- `.github/workflows/**`
- `docs/ARCHITECTURE.md`

### Role ownership (documented)

- Spec Authoring (by assignment): specific `## Spec` sections inside `plans/PLAN.md` only
- Scaffolder: `.gitignore`, repo layout additions (new dirs/files only)
- Schema+Validate: `plans/schemas/**`, `src/validate.py`, validation tests
- Core Loop: `src/runner.py`, `src/executor.py`, `src/env/**`, `src/policy/**`
- Analyzer: `src/analyzer.py`, `src/metrics/**`, `src/scalarization/**`
- Bench+Bundle+Docs: `bench/**`, `scripts/**`, `plans/artifacts/**`, `docs/**` (except `docs/ARCHITECTURE.md`)

---

## 2.3 Per-Agent Definition of Done

- Work only in owned paths; request manager changes for shared files.
- Add at least one test for new behavior or determinism checks.
- Run targeted tests and `make check` before PR; run `make smoke` if execution paths change.
- Do not change spec semantics in `plans/PLAN.md` unless explicitly instructed; reference SPEC-ID sections in PR.
- Record any manual interventions explicitly in trace/log outputs.

---

## 3. Decision Policy (Impact, Risk, Cost)

### Impact

- Low: comments, docs, config toggles.
- Medium: new small module or function, minor refactors.
- High: API changes, train loop edits, data schema changes.

### Risk

- Low: local lints, added tests, non-executable docs.
- Medium: isolated module change with tests.
- High: touching training loop, logging schema, or configs used in CI.

### Cost

- Low: < 30 seconds unit tests and static checks.
- Medium: quick CPU-only script runs.
- High: GPU training or large dataset downloads.

### Rule

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

### Default quick checks

```bash
uv sync --dev
make check
```

### Experiment smoke test

- CPU-only tiny run with fixed seed.
- Writes logs to a temp run directory.
- Generates tiny plots to verify pipeline wiring.

### Never do by default

- Long GPU training.
- Network downloads > few MB.
- Any destructive operation.
- Modifying CI secrets or repo settings.

---

## 8. Spec, Ledger, and Traces

### Spec locations

- `theory/theory.pdf` (Stage 1 input only, pre-approval)
- `plans/PLAN.md` (authoritative plan and embedded specs)
- `scripts/agent-orchestrator/*.md` (swarm role specs used by `make swarm`)

### Ledger / trace locations (current default)

- `traces/fixtures/*.jsonl` (committed deterministic fixture traces)
- `traces/fixtures/manifest.sha256` (pinned fixture integrity manifest)
- `runs/<run_id>/events.jsonl` (runtime replay output when `--tee` is used)
- `runs/run-<id>-manager.jsonl`, `runs/run-<id>-agent*.jsonl`, `runs/run-<id>-swarm.jsonl` (swarm logs)

### Planned trace locations (future-state targets, not yet default)

- `traces/<trace_id>.jsonl` (ad hoc runs)
- `traces/canonical.jsonl` (README canonical example)
- `traces/golden/<scenario_name>.jsonl` (committed regression traces)
- `traces/evals/<dataset_name>/<run_name>.jsonl` (eval outputs)

### Event schema rules

- JSONL, one DomainEvent per line (append-only).
- Required keys: `kind`, `trace_id`, `seq`, `ts`, `meta`, plus event-specific fields.
- `seq` strictly increases within a file.
- No in-place edits. If you need compaction, generate a new file and keep the original.

### Why JSONL

- Maps 1:1 to append-only semantics.
- Streaming-friendly and easy to diff.
- Stable per-line schema validation and efficient replay/tail/seek.

## 9. Config and Backend Guidance

- TODO

## 10. Logging and Metrics

- TODO

---

## 11. PR Checklist

- [ ] Focused branch and diff.
- [ ] Ownership boundaries respected (see Documented CODEOWNERS).
- [ ] Shared files touched only by manager.
- [ ] Spec documented.
- [ ] Unit tests added/updated as specs instruct.
- [ ] Write minimal code until all assigned tests pass.
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

### Planning prompt

- Summarize goal in 1 sentence.
- List 3–5 minimal steps.
- Identify changes.
- Confirm spec exists.
- State a test for the spec.

### Implementation prompt

- Minimal diff with signatures, tests, docstrings to pass tests.
- Config flags and defaults.
- Run commands.

### Review prompt

- Self-critique implementation.
- Verify checklist.
- Rollback plan.
- Check for alternatives.

### Tester prompt

- Run tests of functions.

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
