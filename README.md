# Gedanken Engine for Regret Minimization

This repository is a repo-native demonstration of a repeatable pipeline for compiling theory into executable checks: “Theory → Plan → Specs → Swarm → Tests → Code,” applied to regret minimization.
The input is `theory/theory.pdf`, treated as an executable contract: swarms translate invariants into a concrete plan, derive specs that define admissibility and metrics, generate tests that attempt to falsify the invariants, then implement `src/<code>` only to the extent needed to make the tests pass under deterministic replay. This yields audit-ready counterfactual evaluation where regret is computed against admissible baselines under identical boundary conditions.

## Repository layout as a compilation pipeline

This repository is intentionally structured as a compiler from theory to falsifiable engineering artifacts, rather than as a library or reference implementation.
Each directory corresponds to a compilation stage, not a convenience grouping.

theory/

- Input contracts only. `theory.pdf` is the canonical example.
- Treated as immutable. No edits are required or expected.
- All downstream artifacts must trace back to explicit statements or invariants in this document.

plans/

- Manager-authored run plans for a swarm session.
- Defines lanes, merge order, and “definition of done” gates.
- `plans/PLAN.md` is the canonical spec after user approval.
- The plan is the only place where cross-agent coordination is allowed, and it is treated as a versioned control artifact.

scripts/agent-orchestrator/

- Swarm orchestration role specs used by `make swarm` (`spec.md`, `agent1.md` ... `agent5.md`).
- Defines manager/worker prompt contracts and per-lane scope for replayable runs.

tests/

- Tests are generated before implementation.
- Focus on invariants, counterfactual validity, and nondeterminism detection.
- Any change in behavior must surface as a test failure, not as a reinterpretation of theory or specs.

src/

- Minimal code required to satisfy the tests.
- No speculative features. No hidden state. No online adaptation.
- Exists to verify the theory, not to embellish it.

runs/

- Immutable records of executed canonical runs.
- Each run captures the exact (plan, specs, seed, trace) tuple used.
- Serves as the primary audit surface for reproducibility and review.

traces/

- Current state: committed fixture traces in `traces/fixtures/*.jsonl` plus `traces/fixtures/manifest.sha256`.
- Planned state: broader trace datasets (`canonical`, `golden`, `evals`) as the offline analyzer pipeline is implemented.
- Invariance rule: workload traces are frozen across alternatives unless explicitly modeled inside the system.

## How to run

Prerequisites:

- Python `3.11`
- `uv`
- Optional: `codex` on PATH (required only for `make swarm`)

1. Bootstrap

```bash
make init
```

2. Validate environment

```bash
make check
```

3. See deterministic replay

```bash
make replay RUN_ID=1 TRACE=traces/fixtures/fixture_five_agent.jsonl SEED=7
```

4. See offline analysis

```bash
make analyze RUN_ID=1 ANALYZE_IN=runs/1/events.jsonl ANALYZE_OUT=runs/1/report.json
```

5. Validate orchestrator gate

```bash
make gate GATE_RUN=runs/1
```

6. Optional smoke and swarm

```bash
make smoke
make swarm RUN_ID=1
```

### Feature Tour

- `make replay ...`
  - Stdout: deterministic JSONL stream (`STEP` events or deterministic `ERROR` payload).
  - Artifact: `runs/<run_id>/events.jsonl` when replay runs with tee enabled.
- `make analyze ...`
  - Stdout: quiet on success; deterministic `ERROR` JSON on failure.
  - Artifact: `runs/<run_id>/report.json` with deterministic-input validity and scalar summary.
- `make gate ...`
  - Stdout: JSON gate report with `PASS` or `FAIL`.
  - Inputs: `runs/<run_id>/manager_tasks.yaml`, `runs/<run_id>/manager_verdict.yaml`, `runs/<run_id>/agent*/out.yaml`.
- `make smoke`
  - Stdout: deterministic `TRAIN_SMOKE` JSON payload (or deterministic config error).
- `make swarm ...`
  - Artifacts: `runs/run-<id>-manager.jsonl`, `runs/run-<id>-agent*.jsonl`, `runs/run-<id>-swarm.jsonl`.

### Determinism Contract

- `spec`: approved `plans/PLAN.md`
- `trace`: frozen fixture trace or declared tape input
- `seed|tape`: exactly one deterministic driver input must be declared

Identical boundary tuples must yield identical ordered event streams and deterministic derived hashes.

### Artifact Map

| Artifact              | Path                                                                                     | Purpose                            | Required/Expected fields                                                                              |
| --------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Fixture manifest      | `traces/fixtures/manifest.sha256`                                                        | Pin fixture integrity              | `<sha256><space><space><relative_path>` entries                                                       |
| Fixture traces        | `traces/fixtures/*.jsonl`                                                                | Frozen workload trace input        | Domain events with deterministic ordering fields expected by replay                                   |
| Replay event stream   | `runs/<run_id>/events.jsonl`                                                             | Deterministic replay output        | `kind`; for `STEP`: `seq`, `t`, `state_hash_pre`, `actions`, `reward`, `cost`                         |
| Analysis report       | `runs/<run_id>/report.json`                                                              | Offline measurement output         | `report_version`, `run_id`, `source_events_path`, `source_events_sha256`, `event_count`, `analysis.*` |
| Swarm logs (optional) | `runs/run-<id>-manager.jsonl`, `runs/run-<id>-agent*.jsonl`, `runs/run-<id>-swarm.jsonl` | Manager/worker orchestration audit | Append-only JSONL log events                                                                          |

## Architecture and verification

- Architecture contract: `docs/ARCHITECTURE.md`
- Verification commands:

```bash
make check
make gate
make smoke
```

## CI and Security

The repository uses GitHub-native CI and security automation to enforce deterministic quality gates and supply-chain controls.

Required workflow checks for protected branches:

- `ci / check` (runs `make check`)
- `ci / gate` (runs `make gate`)
- `ci / smoke` (runs `make smoke`)
- `security / codeql`
- `security / dependency-audit`
- `security / sbom`
- `security / attest`

Dependency automation policy:

- Dependabot runs weekly for `pip` and `github-actions`.
- Dependency pull requests are labeled `dependencies` and `security`.
- Security updates are grouped separately from routine updates.

PR security checklist policy:

- PR authors must complete the security/supply-chain checklist in `.github/pull_request_template.md`.
- Required PR notes include security impact, dependency/lockfile changes, threat-model delta, and rollback plan.

Branch protection settings are configured in the GitHub UI (not versioned in this repo). For `main`, enforce required status checks and review requirements in line with `AGENTS.md` guardrails.

## References

- `docs/ARCHITECTURE.md`
- `theory/theory.pdf`

## License

See `LICENSE`.

## Citation

This repository is intended to be cited as a methodology example for operationalizing regret minimization using multi-agent (swarm) workflows under deterministic constraints.

What is being demonstrated:

- A method for compiling theoretical claims into executable, falsifiable checks.
- A controlled use of swarms to decompose research into specs, tests, and minimal code.
- An engineering treatment of regret minimization as a property of a system, not a post-hoc analysis.

What is not being claimed:

- A single optimal regret-minimization algorithm.
- General empirical superiority over other approaches.
- Completeness of the theory input.
  If you use or reference this repository, please cite:

```bibtex
@software{mcbride_2026_gedanken-engine-for-regret-minimization,
  author = {Michael McBride},
  title = {Gedanken Engine for Regret Minimization},
  year = {2026},
  url = {https://github.com/MichaelsEngineering/gedanken-engine-for-regret-minimization},
  version = {0.2}
}
```
