---
name: claim-contract-to-plan
description: Generate deterministic manager+5-worker `plans/PLAN.md` from `core_claim.contract.yaml` with strict validation, explicit while-loop orchestration, disjoint touched_paths, and mirrored root `PLAN.md` output.
---

# Claim Contract To Plan

Generate a deterministic execution PLAN from a claim contract and fail fast on missing critical fields.

## Required Inputs

- `contract_path`: path to `core_claim.contract.yaml`.
- `output_path`: canonical markdown path (default `plans/PLAN.md`).
- `mirror_output_path`: root mirror path (default `PLAN.md`).
- `repo_guardrails_path`: guardrails source path (default `AGENTS.md`).
- `gate_command`: deterministic gate command (default `make gate`).
- `status_template_path`: manager status artifact path (default `runs/swarm/STATUS.md`).
- `registry_template_path`: artifact registry path (default `runs/swarm/artifacts/REGISTRY.csv`).

## Command

```bash
python scripts/generate_plan.py \
  --contract plans/claim/definition-sec-001/core_claim.contract.yaml \
  --out plans/PLAN.md \
  --mirror-out PLAN.md \
  --strict
```

## Workflow

1. Validate contract fields strictly; abort on missing/duplicate required keys.
2. Resolve optional compatibility fields when present:
- `observables[*].test_name`
- `invariants[*].minimal_code_surface`
- `artifacts[*].producer_lane_hint`
3. Generate fixed-order sections including:
- explicit manager loop (`plan -> delegate -> workers execute -> integrate -> verify -> checkpoint`)
- manager->worker work-item schema
- worker->manager response schema
- deterministic gates and per-slice termination rule
- state externalization artifacts and checkpoint cadence
4. Emit initial tranche work items with disjoint `touched_paths`.
5. Write canonical `plans/PLAN.md` and mirror root `PLAN.md`.

## Guarantees

- Deterministic section ordering and deterministic content for same input contract.
- No overlapping `touched_paths` across concurrently active initial work items.
- Gate command and smoke command are explicitly represented in PLAN output.

## Resources

- `references/field_mapping.md`
- `references/plan_template.md`
- `scripts/generate_plan.py`
