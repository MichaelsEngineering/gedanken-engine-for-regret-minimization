# Gedanken Engine for Regret Minimization

Deterministic, replayable coordination framework for regret-minimizing policies in agent-based decision systems.

## Project Status

Pre-alpha. Specification-first repository.

This repository currently contains formal specifications, invariants, and example scenarios.
No execution engine or training runtime is implemented yet.

## Design Goals and System Invariants

### Design Goals

- Deterministic evaluation of decision policies under identical initial conditions
- Explicit separation of coordination (policy selection) and execution (actuation)
- Replayable, auditable traces suitable for offline evaluation

### System Invariants

- The specification is the sole source of truth
- Traces are append-only and immutable
- Coordination may only emit intents
- Execution may only emit results
- All human intervention is logged explicitly
- Deterministic replay: identical spec, seed, and trace produce identical derived-state hashes

## Minimal Counterexample Scenario

Two agents, one decision step, two admissible actions.
Asymmetric private information with an externality cost.

This scenario is sufficient to falsify naive agent designs that lack explicit counterfactual evaluation or regret accounting.

## Repository Layout

Repository structure follows common patterns from RL experiment repos and physics simulation codes, with explicit separation between theory, specifications, traces, and execution artifacts.

```text
├── AGENTS.md
├── CHANGELOG.md
├── CODEOWNERS
├── coverage.xml
├── dev
│   ├── collect_pr_context.sh
│   └── ship.sh
├── docs
│   ├── agent-orchestrator.md
│   └── ARCHITECTURE.md
├── LICENSE
├── Makefile
├── PLAN.md
├── pyproject.toml
├── README.md
├── runs
│   ├── 1
│   ├── demo
│   ├── run-1-agent1.jsonl
│   ├── run-1-agent2.jsonl
│   ├── run-1-agent3.jsonl
│   ├── run-1-agent4.jsonl
│   ├── run-1-agent5.jsonl
│   ├── run-1-manager.jsonl
│   └── run-1-swarm.jsonl
├── scripts
│   ├── __init__.py
│   ├── __pycache__
│   ├── swarm_gate.py
│   ├── swarm_merge_jsonl.py
│   ├── swarm_pretty.py
│   └── swarm_run.sh
├── specs
│   ├── agent-orchestrator
│   ├── game.yaml
│   ├── policies.yaml
│   └── spec.md
├── src
│   ├── Gedanken_Engine_for_Regret_Minimization.egg-info
│   └── __init__.py
├── tests
│   ├── conftest.py
│   ├── __pycache__
│   ├── test_placeholder.py
│   ├── test_swarm_gate.py
│   ├── test_swarm_merge_jsonl.py
│   └── test_swarm_pretty.py
├── theory
│   └── theory.md
├── traces
└── uv.lock
```

## Implemented Features

- Swarm launcher for 1 manager + 5 workers (`make swarm`).
- Gate validator for orchestrator artifacts (`make gate`).
- Deterministic JSONL merge with lane labels (`scripts/swarm_merge_jsonl.py`).
- Pretty terminal output for swarm runs (`scripts/swarm_pretty.py`).
- Tests covering gate validation and swarm logging utilities.

## Planned Capabilities

- Core coordination and replay engine (`src/`) beyond current scaffolding.
- CLI for running scenarios and emitting traces beyond the swarm launcher.
- Offline replay and policy comparison tooling.
- Deterministic trace validation and hashing beyond the gate contract.
- Reference benchmarks for minimal regret scenarios.

## Reading the Specification

This repository is currently spec-first.

To understand the governing commitments and system model, start with:

```bash
cat theory/theory.md
cat specs/spec.md
```

For the architectural plan, see:

```bash
cat docs/ARCHITECTURE.md
```

The architectural plan is subordinate to the spec; `specs/spec.md` remains the source of truth.

## Quickstart

Prereqs:

- Python >= 3.11 (see `pyproject.toml`).
- `uv` installed (recommended; repo uses it for dependency management).
- `codex` CLI on PATH (required for `make swarm`).

Install deps:

```bash
uv sync --dev
```

Run a swarm (manager + 5 workers):

```bash
RUN_ID=1 make swarm
```

Validate the gate:

```bash
make gate GATE_RUN=runs/1
```

## Multi-agent Workflow

Coordination and ownership rules live in `AGENTS.md`. Highlights:

- Max 6 concurrent lanes total (Managers + up to 5 workers).
- Branch naming: `feat/<lane>-<short-task>`; merge serially in the order listed in `AGENTS.md`.
- Canonical reproduction command (once scripts exist): `./scripts/reproduce.sh canonical`.

Swarm launcher command:

```bash
RUN_ID=1 make swarm
```

Gate demo vs swarm runs:

- `make gate` validates the **static demo fixture** under `runs/demo/` (manager_tasks.yaml, manager_verdict.yaml, and agent*/out.yaml).
- `make swarm` runs the Codex lanes and writes JSONL logs (`runs/run-<id>-*.jsonl` and `runs/run-<id>-swarm.jsonl`).
- If you want to validate a swarm run with the gate, you must also produce the YAML artifacts in `runs/<id>/` (manager_tasks.yaml, manager_verdict.yaml, agent1/out.yaml ... agent5/out.yaml), then run:

```bash
make gate GATE_RUN=runs/1
```

## Implementation Notes

- Python >= 3.11
- Dependencies listed in `pyproject.toml`

## Contributing

Contributions are welcome at the specification and design level.

Please open an issue describing the proposed change, the motivation, and the expected impact on determinism or regret evaluation.

## Changelog

See `CHANGELOG.md`.

## Citation

If you use or reference this repository, please cite:

```bibtex
@software{mcbride_2026_gedanken-engine-for-regret-minimization,
  author = {Michael McBride},
  title = {gedanken-engine-for-regret-minimization: Gedanken Engine for Regret Minimization},
  year = {2026},
  url = {https://github.com/MichaelsEngineering/gedanken-engine-for-regret-minimization},
  version = {0.2}
}
```

## License

See `LICENSE`.
