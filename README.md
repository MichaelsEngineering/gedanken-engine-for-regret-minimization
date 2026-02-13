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

## How to run (engineering quick start)

Prereqs: Python 3.11 and `codex` on PATH for swarm runs.

```bash
make init
make gate
```

Optional swarm run that produces JSONL logs:

```bash
make swarm RUN_ID=1
```

Core evaluation engine command:

```bash
make replay RUN_ID=<id> TRACE=traces/fixtures/<trace>.jsonl SEED=<n>
```

Expected outputs at a high level:

- `make gate` reads `runs/1/` and prints a JSON gate report with PASS or FAIL.
- `make swarm` writes `runs/run-<id>-manager.jsonl`, `runs/run-<id>-agent*.jsonl`, and `runs/run-<id>-swarm.jsonl`.
- Gate-ready runs live in `runs/<id>/` with `manager_tasks.yaml`, `manager_verdict.yaml`, and `agent*/out.yaml`.
- `make replay` writes replay events to `runs/<id>/events.jsonl`.
- `make analyze` emits a regret report at `runs/<id>/report.json`.

## Architecture and verification

- Architecture contract: `docs/ARCHITECTURE.md`
- Verification commands:

```bash
make check
make gate
make smoke
```

- Diagram assets in `docs/diagram/` are informational and not gate-relevant.

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
