# Agent Orchestrator Swarm Gate

## Purpose

Define the swarm gate contract for a 6-lane orchestration: 1 manager lane and 5 worker lanes.

## Lane model

- Manager lane: emits the deterministic swarm plan and the final merge verdict.
- Worker lanes (`agent1..agent5`): execute tasks in parallel and emit per-agent artifacts.

## Artifacts (runs/<run_id>/)

- `manager_tasks.yaml`
- `agent1/out.yaml` ... `agent5/out.yaml`
- `manager_verdict.yaml`
- Optional: `agent*/events.jsonl` (append-only event stream)

All YAML artifacts must include `contract_version: "1"` (exact match).

## Spec assignment checklist

Manager lane responsibilities:

- Create the run directories: `runs/<run_id>/agent1` ... `runs/<run_id>/agent5`.
- Write `runs/<run_id>/manager_tasks.yaml` with exactly 5 tasks (`agent1..agent5`).
- Assign each task an explicit `spec_path` so agents do not work on the same files.
- Optional per-task metadata is allowed if it is read-only for the gate.

Example manager_tasks.yaml:

```yaml
  contract_version: "1"
  tasks:
  - id: agent1
    spec_path: scripts/agent-orchestrator/spec.md
    metadata:
      owner: "core-loop"
  - id: agent2
    spec_path: scripts/agent-orchestrator/agent2.md
  - id: agent3
    spec_path: scripts/agent-orchestrator/agent3.md
  - id: agent4
    spec_path: scripts/agent-orchestrator/agent4.md
  - id: agent5
    spec_path: scripts/agent-orchestrator/agent5.md
```

Task → output mapping (1:1):

- `tasks[*].id = agent1` → `runs/<run_id>/agent1/out.yaml`
- `tasks[*].id = agent2` → `runs/<run_id>/agent2/out.yaml`
- `tasks[*].id = agent3` → `runs/<run_id>/agent3/out.yaml`
- `tasks[*].id = agent4` → `runs/<run_id>/agent4/out.yaml`
- `tasks[*].id = agent5` → `runs/<run_id>/agent5/out.yaml`

## Gate command

`make gate` runs the validator against a sample run directory and enforces the
lane model, artifact shapes, and `contract_version` requirement. This is a
doc-first contract; implementation follows the spec.

## Swarm command

`make swarm` launches the manager + 5 worker lanes using `scripts/swarm_run.sh`.

## Swarm logs

- Per-lane JSONL logs: `runs/run-<id>-manager.jsonl` and `runs/run-<id>-agent1.jsonl` ... `runs/run-<id>-agent5.jsonl`.
- Merged JSONL log with lane labels: `runs/run-<id>-swarm.jsonl`.
- Terminal output is a human-readable view derived from JSONL via `scripts/swarm_pretty.py`.
