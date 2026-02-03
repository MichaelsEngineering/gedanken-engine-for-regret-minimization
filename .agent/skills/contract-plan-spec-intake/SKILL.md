---
name: contract-plan-spec-intake
description: Guided intake to collect all answers needed to draft CONTRACT.md, PLAN.md (from PLAN.template.md), and spec updates in one pass; use for new features or scope changes when the user wants to answer questions once and then activate a swarm to write tests, code, and verify.
---

# Contract + Plan + Spec Intake

## Overview
Use this skill to run a single-pass interview that yields drafts for CONTRACT.md, PLAN.md, and spec patch notes, then emit a swarm activation stub for tests → code → verify. If the repo uses the agent-orchestrator gate, also map the prompts into specs/agent-orchestrator/*, provide expected gate outputs, require concrete coding tasks with diffs and tests, and ensure Codex runs in edit-enabled mode.

## Operating Mode
Ask questions strictly in order. Ask exactly one question at a time. Stop early if the user says "skip" for a section. Do not draft until intake is complete or explicitly terminated. If an answer is underspecified, make the smallest explicit assumption and label it `ASSUMPTION:`.

## Output Format (always)
1. Intake Answers
   - Bulleted list, labeled A1, A2, ... E18
2. Draft Artifacts
   - `CONTRACT.md` (full draft)
   - `PLAN.md` (full draft from template)
   - Spec patch notes (what file, what section, what changes)
3. Swarm Activation Stub
   - Manager prompt
   - Worker role prompts
4. Swarm Prompt Mapping + Gate Outputs
   - specs/agent-orchestrator/spec.md (manager prompt)
   - specs/agent-orchestrator/agent1.md .. agent5.md (worker prompts)
   - Expected runs/<run_id>/manager_tasks.yaml, manager_verdict.yaml, agent*/out.yaml

## Intake Script
Ask in order. Do not paraphrase the questions.

### A) Feature and scope
A1. One-sentence feature intent?  
A2. What "closed-system scenario" means here (boundaries, inputs, outputs)?  
A3. Any explicit exclusions or anti-goals?  
A4. What must never change (non-negotiable invariants)?  
A5. What is explicitly out of scope for this request?

### B) Acceptance and evaluation
B6. Success criteria (measurable)?  
B7. Determinism or replay requirements?  
B8. What traces, metrics, or artifacts must be emitted?  
B9. Failure modes that must be prevented?

### C) Spec-level detail
C10. What new behavior must be specified?  
C11. What existing spec or theory section is authoritative?  
C12. Any required interfaces, schemas, events, or fields?

### D) Plan-level detail
D13. Required file-level changes (paths)?  
D14. Tests required (unit, integration, determinism, regression)?  
D15. Validation commands or checks that must pass?

### E) Swarm constraints
E16. Which roles should be used (manager + how many workers)?  
E17. File ownership boundaries or no-go files?  
E18. Max iterations, time budget, or stop conditions?

## Drafting Rules
Keep CONTRACT minimal, stable, and future-facing. Keep PLAN bounded, testable, and file-scoped. Keep spec authoritative and declarative with no implementation detail. Prefer explicit invariants over prose. Map every acceptance criterion to a test or check.

If the repo uses the agent-orchestrator gate, include concrete prompt mappings into `specs/agent-orchestrator/spec.md` and `specs/agent-orchestrator/agent1.md` .. `agent5.md`, and provide expected `runs/<run_id>` YAML outputs for `make gate`.

Always require concrete coding tasks in CONTRACT, prompts, and agent specs. Prompts must demand staged diffs and tests: `git add -A`, `git diff --cached`, and `git diff --cached --name-status` plus test command and summary. Require a git repo and fail the gate if diffs are empty, tests are missing, or tests fail.

Ensure Codex is invoked in edit-enabled mode for swarm runs using:
`codex exec --json --cd "$REPO_ROOT" --full-auto --sandbox workspace-write`

## Swarm Activation Stub (Template)

### Manager Prompt
You are the manager agent.
- Enforce CONTRACT.md invariants.
- Require concrete code + tests with staged diffs (`git add -A`, `git diff --cached`, `git diff --cached --name-status`).
- Require tests to run and report command, exit code, and summary.
- Keep worker prompts minimal and non-overlapping.
- Coordinate I/O between planner, implementers, and verifier.
- Stop immediately on contract violation.

### Planner Prompt
Produce `PLAN.md` only.
- Use the provided template.
- Do not write code.
- Ensure all acceptance criteria are testable.

### Compiler Prompt
Compile PLAN.md into role-scoped prompts.
- One prompt per worker.
- Each prompt must specify:
  - Allowed files
  - Required outputs
  - Stop condition

### Implementer Prompt
Implement assigned changes.
- Stage changes: `git add -A`.
- Output unified diff only: `git diff --cached`.
- Output name-status: `git diff --cached --name-status`.
- Run required tests and include command, exit code, and summary lines.
- No commentary.
- Do not touch files outside your scope.

### Verifier Prompt
Verify against CONTRACT.md and PLAN.md.
- Confirm staged diffs and test evidence are present.
- Output PASS or a minimal failing diff only.
- No suggestions or commentary.

## Completion Condition
Complete when draft artifacts, the swarm activation stub, prompt mapping + gate outputs, and edit-mode + diff/test enforcement are emitted and no further questions remain.
