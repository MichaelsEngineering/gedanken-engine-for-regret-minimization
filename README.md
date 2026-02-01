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
├── dev
│   └── skills
│       └── spec-writer.md
├── docs
│   └── ARCHITECTURE.md
├── LICENSE
├── Makefile
├── pyproject.toml
├── README.md
├── runs
├── specs
│   ├── game.yaml
│   ├── policies.yaml
│   └── spec.md
├── theory
│   └── theory.md
├── src
│   └── __init__.py
└── traces
```

## Planned Capabilities

- Core coordination and replay engine (`src/`)
- CLI for running scenarios and emitting traces
- Offline replay and policy comparison tooling
- Deterministic trace validation and hashing
- Reference benchmarks for minimal regret scenarios
- Tests and CI for replay determinism

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

## Multi-agent Workflow (planned)

Coordination and ownership rules live in `AGENTS.md`. Highlights:

- Max 6 concurrent lanes total (Integrator + up to 5 workers).
- Branch naming: `feat/<lane>-<short-task>`; merge serially in the order listed in `AGENTS.md`.
- Canonical reproduction command (once scripts exist): `./scripts/reproduce.sh canonical`.

## Implementation Notes (planned)

- Python >= 3.11
- Dependencies listed in `pyproject.toml`

Once code lands, this section will include install and run steps.

## Contributing

Contributions are welcome at the specification and design level.

Please open an issue describing the proposed change, the motivation, and the expected impact on determinism or regret evaluation.

## Changelog

See `CHANGELOG.md`.

## License

See `LICENSE`.
