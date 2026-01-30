# Gedanken Engine for Regret Minimization

Spec-first, replayable agent coordination for regret-minimizing decision systems.

## Status

Pre-alpha / spec-only. This repository currently contains specs and placeholders.

Executable code, tests, and CLI tooling are planned but not yet implemented.

## Goals and Invariants

- Spec is the source of truth.
- Ledger is append-only.
- Coordination can only append intents to traces.
- Execution can only append results to traces.
- Human intervention must be explicitly logged to traces.
- Replay determinism: same spec + seed + ledger => same derived-state hash in runs.

Minimal falsifier example:

Two agents. One turn. Two actions. Asymmetric private information plus an externality cost.

## Repository Layout

```bash
├── AGENTS.md
├── CHANGELOG.md
├── dev
│   └── skills
│       └── spec-writer.md
├── LICENSE
├── Makefile
├── pyproject.toml
├── README.md
├── runs
├── specs
│   ├── game.yaml
│   ├── policies.yaml
│   └── spec.md
├── src
│   └── __init__.py
└── traces
```

## Roadmap (planned)

- `src/` engine + coordination runtime
- CLI for running scenarios and writing traces
- Replayer UI (Textual)
- Trace validation and deterministic replay tools
- Tests + CI wiring
- Docs for configuration, policies, and evaluation

## Getting Started (spec-only)

There is no runnable code yet. To explore the design:

```bash
cat specs/spec.md
```

## Development (planned)

- Python >= 3.11
- Dependencies listed in `pyproject.toml`

Once code lands, this section will include install and run steps.

## Contributing

Early-stage project. If you'd like to contribute, open an issue describing the
proposal and intended spec changes.

## Changelog

See `CHANGELOG.md`.

## License

See `LICENSE`.
