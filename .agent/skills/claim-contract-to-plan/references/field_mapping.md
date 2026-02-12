# Field Mapping

Contract to PLAN mappings:

- `claim.primary_section_id` -> authority metadata and plan anchor.
- `invariants[*]` -> invariant extraction table + hard-fail spec predicates.
- `observables[*]` -> deterministic tests and gate clauses.
- `observables[*].test_name` (optional) -> explicit test name override.
- `comparator.admissibility_rule` -> admissibility gate hard-fail condition.
- `variables[*]` -> spec glossary entries.
- `assumptions[*]` -> assumptions log entries.
- `artifacts[*].producer_lane_hint` (optional) -> artifact producer hint table.

Deterministic touched-path ownership (initial tranche):

- `agent1` -> `plans/PLAN.md` (mapping rows only)
- `agent2` -> `plans/PLAN.md` (SPEC sections only)
- `agent3` -> `tests/**`
- `agent4` -> `src/**`
- `agent5` -> `runs/**`, `traces/**`

Default acceptance test mapping:

- Mapping/spec slices -> `pytest -q tests/test_generate_plan.py`
- Test slice -> `pytest -q tests/test_swarm_gate.py tests/test_generate_plan.py`
- Source slice -> `make gate`, `pytest -q tests/test_runner.py`
- Audit slice -> `make gate`, `make smoke`

Default artifacts-to-emit mapping:

- Manager checkpoint -> `runs/swarm/STATUS.md`
- Artifact provenance -> `runs/swarm/artifacts/REGISTRY.csv`
- Worker scratchpad -> `runs/swarm/workerN/YYYYMMDD-HHMM/NOTES.md`
- Optional worker diffstat -> `runs/swarm/workerN/YYYYMMDD-HHMM/DIFFSTAT.txt`

Minimal code surface fallback by observable token:

- contains `replay` -> `src/runner.py`, `tests/test_runner.py`
- contains `trace` -> `traces/*.jsonl`, `tests/test_swarm_gate.py`
- contains `dimension` or `regret` -> `src/analyzer.py`, `src/scalarization/__init__.py`, `tests/test_analyzer_stub.py`
- contains `oracle` or `admiss` -> `src/validate.py`, `tests/test_validate.py`
- fallback -> `src/`, `tests/`
