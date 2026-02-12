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

- Immutable records of executed demo runs.
- Each run captures the exact (plan, specs, seed, trace) tuple used.
- Serves as the primary audit surface for reproducibility and review.

traces/

- Current state: committed fixture traces in `traces/fixtures/*.jsonl` plus `traces/fixtures/manifest.sha256`.
- Planned state: broader trace datasets (`demo`, `golden`, `evals`) as the offline analyzer pipeline is implemented.
- Invariance rule: workload traces are frozen across alternatives unless explicitly modeled inside the system.

## Executable demo: regret minimization as a thought experiment

This repository is intended to be reviewed as an executable thought experiment.

Demo contract:

- Input: `theory/theory.pdf`
- Assumptions: frozen workload trace, fixed seed, fixed spec
- Output: regret metrics computed against admissible baselines under identical boundary conditions

Typical demo flow:

1. Read `theory/theory.pdf` to identify explicit invariants and admissibility constraints.
2. Inspect `plans/` to see how the swarm decomposed the theory into owned tasks.
3. Review `plans/PLAN.md` and `scripts/agent-orchestrator/` to confirm evaluation rules and lane contracts are fully specified.
4. Run tests to see where the theory is falsified, upheld, or shown to be underspecified.

5. Inspect `src/` only after tests, to verify minimal compliance rather than feature scope.

## Why this repository exists (engineering motivation)

This repo demonstrates:

- Input a novel theoretical claim (thought experiment) into the theory folder and obtain concrete tests and minimal src code that can be executed.

- A simple framework for multi-agent work that is constrained to remain deterministic and reviewable.

- Moving regret minimization out of an academic “narrative” space and into the engineering stack.

## How to run (engineering quick start)

Prereqs: Python 3.11, `uv`, and `codex` on PATH for swarm runs.

```bash
uv sync --dev
make gate
```

Optional swarm run that produces JSONL logs:

```bash
RUN_ID=1 make swarm
```

TODO placeholder for the core evaluation engine (intentionally not implemented yet):

```bash
# TODO: uv run rc --env <module:callable> --policies <module:callable> --metrics <module:callable> --trace traces/fixtures/<trace>.jsonl --seed <n> --out runs/<run_id> --tee
```

Expected outputs at a high level:

- `make gate` reads `runs/demo/` and prints a JSON gate report with PASS or FAIL.
- `make swarm` writes `runs/run-<id>-manager.jsonl`, `runs/run-<id>-agent*.jsonl`, and `runs/run-<id>-swarm.jsonl`.
- Gate-ready runs live in `runs/<id>/` with `manager_tasks.yaml`, `manager_verdict.yaml`, and `agent*/out.yaml`.
- `uv run rc ... --tee` writes replay events to `runs/<id>/events.jsonl`.
- TODO: the offline analyzer will emit a regret report at `runs/<id>/report.json`.

## Verification checklist (definition of correctness)

- [ ] Re-run with identical spec, seed, and trace produces identical derived-state hashes.
- [ ] Trace files are immutable and identical across all alternatives.
- [ ] Comparator uses only $A_{adm}$ and excludes hidden state or future RNG outcomes.
- [ ] Every metric has an explicit $C_i(s)$ and aggregate regret is dimensionless.
- [ ] Changing units (ms to s) does not change dimensionless regret.
- [ ] Causal closure holds and boundary conditions reset between alternatives.
- [ ] Trace divergence triggers a hard failure.
- [ ] Measurement occurs offline with no online learning during execution.
- [ ] Regret is computed against the best admissible alternative, not clairvoyant baselines.
- [ ] Audit trail is reproducible from spec, seed, and trace alone.

## References

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
