---
name: core-claim-qa
description: Extract one falsifiable core claim contract with deterministic structure and compatibility fields for claim-contract-to-plan orchestration.
---

# Core Claim QA

## Purpose

Convert one source document into one falsifiable claim contract with deterministic, structured outputs.

## Required Inputs

- One source document: `.md` or `.tex`
- User prompt `domain_goal`: one sentence for what the paper optimizes or guarantees
- User prompt `claim_focus`: choose exactly one of `theoretical guarantee | empirical result | systems invariant | definition/spec`
- User prompt `evaluation_target`: one sentence for evidence that supports or refutes the claim

Treat the three user prompts as constraints, not extracted content.

## Output Contract

Write all outputs under `plans/claim/<claim_id>/` only.

- `plans/claim/<claim_id>/core_claim.statement`
- `plans/claim/<claim_id>/core_claim.type`
- `plans/claim/<claim_id>/core_claim.contract.yaml`
- `plans/claim/<claim_id>/core_claim.open_questions.yaml` only when blocking gaps exist

### claim_id rule

Derive `claim_id` deterministically as `slug(claim_focus) + '-' + slug(primary_section_id)`.

## Hard Rules

- Produce structured outputs only; do not produce narrative summaries.
- Emit exactly one core claim sentence.
- Abort on heading-index failures before claim selection.
- Emit open questions for unresolved blocking definitions instead of guessing.
- Treat invariants and abort conditions as first-class contract items.

## Compatibility Fields (Additive)

When available from source material, include these optional keys in `core_claim.contract.yaml`:

- `observables[*].test_name`: deterministic test id override for plan generator.
- `invariants[*].minimal_code_surface`: explicit code/test path hint.
- `artifacts[*].producer_lane_hint`: expected producer lane (`manager|agent1..agent5`).

If unavailable, omit these fields; do not fabricate values.

## Workflow

1. Normalize source and build stable heading index (`SEC-001`, ...).
2. Select exactly one falsifiable core claim using prompt constraints.
3. Extract only variables required to test the selected claim.
4. Emit canonical contract keys:
- `claim`, `domain`, `method`, `comparator`, `observables`, `assumptions`, `invariants`, `artifacts`, `variables`
5. Validate sufficiency and emit blocking `open_questions` when needed.

## Non-Goals

- Venue recommendation
- Novelty scoring
- Implementation design beyond what is required for testing
