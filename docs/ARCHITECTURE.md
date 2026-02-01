# Architectural Plan v2 (Public Repo, Deterministic Benchmark)

Goal: a minimal, falsifiable benchmark demonstrating externality regret under strict replay, with machine-verifiable artifacts and CI reproducibility.

Authority: `specs/spec.md` is the source of truth; this document is a plan and must not override the spec.

## Repo layout

/
AGENTS.md
CHANGELOG.md
LICENSE
Makefile
README.md
docs/
ARCHITECTURE.md
pyproject.toml
runs/ # append-only local/CI outputs
specs/
spec.md
theory/
theory.md
src/
tests/
traces/

## A. Minimal benchmark environment (Two-Agent Externality Bandit)

Environment definition:

- Hidden variable `p` (private) assigned to Agent 1 per step.
- Public context `x` observable to all policies.
- Action `a` produces:
  - primary reward component(s) `M_primary`
  - externality cost component(s) `M_externality` driven by mismatch `m(p, a)` (or mismatch between inferred latent and action)
- Observation function per policy defines information set `I(h)`:
  - admissible policies cannot read `p` unless explicitly allowed
  - cheating policies exist for falsification tests but are excluded by default admissibility rules

Determinism:

- All exogenous randomness is generated once, recorded into trace files, and replayed exactly.
- Executor is pure: (state, intent, recorded_rng) -> (next_state, result)
- Deterministic replay: same spec + seed + trace => identical derived-state hash.

## B. Artifact-first pipeline (schemas + hash-gated manifests)

Artifacts are bound by manifests with SHA-256 hashes. Analyzer refuses to run if manifest does not match.

1. specs/ define the benchmark contract (human-readable, machine-validated).
2. traces/ define the frozen workload and all exogenous draws.
3. runs/<run_id>/ are append-only raw outputs (intents/results).
4. artifacts/ publish signed or hash-pinned bundles (canonical reproduction outputs).

## C. Execution boundaries (enforced by interfaces)

Coordination runtime:

- Inputs: specs/_ + traces/_ + seed (for selecting trace only, not generating stochasticity)
- Output: intent.jsonl only
- Prohibited: reading hidden state unless policy marked cheating AND run explicitly opts into cheating policies
- Humans append interventions only (if any), consistent with the spec.

Executor:

- Inputs: env spec + trace row + intent row
- Output: result.jsonl only
- No metric computations beyond reporting decomposed raw components

Analyzer (offline only):

- Inputs: specs + trace + intent + result
- Output: derived.json + table.csv + RESULTS.md fragment
- Computes: M_i, C_i, r_i(s,a), scalarization J, a\*, Regret(a|s), and hashes

Trace rules (must match the spec):

- Append-only trace. No mutation, no delete, no in-place edits.
- Trace header event (e.g., `TraceStarted`) stores seed and spec/policy/prompt references; defer to `specs/spec.md` for schema.
- Reducer API (e.g., `reduce_events`, `state_hash`) is defined by `specs/spec.md`; implementation must conform.

## D. Test matrix (variable isolator + metamorphic checks)

bench/matrix.yaml runs:

- fixed action, vary trace (or trace slice): isolates state/observation variability
- fixed trace, vary policy: isolates policy comparison
- include/exclude cheating policy: tests admissibility gate
- rescale metric units: metamorphic test for normalization C_i
- vary weights: tests w_i sensitivity
- swap scalarization definition: tests J and a\*
- policy identity hashing: policy_id changes if policy code/config changes
- golden reproduction: canonical derived outputs match bench/golden within tolerance rules

## E. What is published

Public, stable:

- specs/ (including schemas + manifest)
- traces/ canonical + adversarial (with manifest)
- src/ runner/executor/analyzer + validate
- artifacts/canonical_bundle (derived + table + manifest)
- RESULTS.md (the human-facing table and interpretation)

Not published by default:

- runs/ (append-only, large, local). CI can upload as workflow artifacts instead.

## F. Reproduction contract

One-command reproduction:

- `./scripts/reproduce.sh canonical`
  Produces:
- runs/<run_id>/{intent.jsonl,result.jsonl,derived.json,table.csv}
- artifacts/canonical_bundle updated only by explicit bundle script

CI contract:

- validates specs and traces against schemas
- runs canonical reproduction
- asserts golden match for canonical.table.csv and canonical.derived.json
- fails PR on drift unless golden update is explicitly committed

## G. Multi-agent execution protocol (max 6)

See `AGENTS.md` for authoritative lane ownership, shared-file locks, branch naming, and merge order.
Cap at 6 concurrent lanes total (Integrator + up to 5 worker lanes). If more work is needed, split into phases.
