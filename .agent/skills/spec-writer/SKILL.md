---
name: spec-writer
description: Create or update authoritative specs and aligned YAML scenario/policy configs with a strict template (Authority, Invariants, API, Acceptance). Use when authoring specs/spec.md and specs/*.yaml.
---

# Spec Writer (Strict Template)

Use this skill when the user wants to author or update specs in this repo, especially `specs/spec.md` and `specs/*.yaml`.

## Required user inputs (must ask if missing)

- Task: what is being specified
- Context:
  - Input spec(s): which files or sources to align with
  - Scope: what is in/out
  - Output: expected artifacts (spec, YAML, tests, traces)
- Verify: acceptance criteria to pass

If any are missing, ask concise questions before drafting.

## Working rules

- Read `AGENTS.md` and `specs/spec.md` first.
- Keep diffs minimal; spec is the source of truth.
- Enforce determinism and append-only semantics.
- Use clear section headers and bullet points.
- Prefer concrete, testable requirements over narrative.
- Include exact filenames and schema keys when relevant.

## Output template for specs/spec.md

Use this exact section order and headings:

1. Authority model
2. Invariants
3. API
4. Acceptance criteria

Each section must be short, testable, and written in imperative statements.

### Example skeleton

# Spec: <Title>

## Authority model
- <spec source of truth statement>
- <ledger authority statement>
- <replay authority statement>

## Invariants
1. <invariant>
2. <invariant>
3. <invariant>

## API
- <public function signature(s) with return types>
- <determinism / side effects notes>

## Acceptance criteria
- <make target or test name and expected result>
- <artifact location and expected contents>

## Best-practice 2026 guidance (apply unless user overrides)

- Include explicit versioning or schema identifiers for long-lived specs.
- Define deterministic inputs and outputs; avoid hidden state.
- Tie each invariant to at least one test or acceptance check.
- Use stable names/IDs for traces, policies, and scenarios.
- Document public API signatures with types and error behavior.

## Standard YAML schemas (use these unless user overrides)

### specs/game.yaml

Required keys and types:

```yaml
game:
  name: <string>
  actions: [<string>, ...]
  agents: [<string>, ...]
  turn_limit: <int>
  ground_truth: <string> # domain-specific
  private_signals:
    <agent_id>: <string>
  externality_cost:
    <cost_key>: <number>
rules:
  - if: { action: <string>, ground_truth: <string> }
    then: { outcome: <string>, cost: <cost_key or number> }
```

### specs/policies.yaml

Required keys and types:

```yaml
policies:
  - name: <string>
    description: <string>
    # optional fields:
    params:
      <key>: <value>
```

## Suggestions to include (if relevant)

- Reference the YAML files from `specs/spec.md` to bind narrative and config.
- Add a minimal falsifier scenario for each new invariant.
- If policy order matters, state ordering rules explicitly.
- If any randomness exists, define the seed source and storage.

## When to propose tests

- Any new invariant requires at least one test name or make target.
- Any schema change requires a parsing/validation test.

## Out of scope

- Implementing runtime code, CI, or deployment unless the user asks.

