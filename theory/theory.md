# THEORY.md

## 1. Governing Equations and Scope

This document defines the objective, admissibility constraints, and conservation laws for the Gedanken Engine for Regret Minimization.

It is a constitutive theory for the repository. Any implementation that violates these definitions is considered incorrect, independent of whether it "works" in practice.

This is not an algorithm paper. It defines what must be measured and what must be invariant under replay.

---

## 2. Problem Formulation

We model evaluation as a closed, replayable system.

- **State** $s$: complete boundary conditions for evaluation, including immutable workload traces, environment reset state, and RNG seed state.
- **Alternative** $a \in A$: a finite, enumerated set of admissible actions, policies, or designs.
- **Outcome** $M(s, a)$: deterministic mapping from $(s, a)$ to observed metrics (vector-valued).

### 2.1 Closed-System Assumption (Causal Closure)

All counterfactual evaluations are performed against the same boundary conditions.

If any external dependency cannot be reset to the initial boundary condition, the counterfactual is undefined and regret is invalid.

---

## 3. Regret

Regret is counterfactual loss relative to the best admissible alternative, evaluated under identical boundary conditions.

### 3.1 Scalar Regret (Single Metric)

Let $J(s,a)$ be a scalar objective to maximize. Let $a^*$ be the best admissible alternative as defined in §3.3.

$$
\mathrm{Regret}(a \mid s) = J(s,a^*) - J(s,a)
$$

---

### 3.2 Multi-Metric Regret Requires Nondimensionalization

In engineering systems, metrics have different physical dimensions (latency, throughput, energy, error rate). Direct weighted summation of heterogeneous units is dimensionally invalid and produces scale bias.

Define metric components:

- $M_i(s, a)$ for $i = 1..k$, each with its own physical units.

Define a **characteristic scale** $C_i(s)$ with the same units as $M_i$ and a normalization transform:

$$
r_i(s,a) = \frac{M_i(s, a^*) - M_i(s, a)}{C_i(s)}
$$

Then define dimensionless aggregate regret:

$$
\mathrm{Regret}(a \mid s) = \sum_{i=1}^{k} w_i \, r_i(s,a)
$$

Constraints:

- $w_i \ge 0$
- $\sum_i w_i = 1$ is recommended for interpretability.

ASCII form:

```text
r_i(s,a) = (M_i(s,a*) - M_i(s,a)) / C_i(s)
Regret(a|s) = sum_i w_i * r_i(s,a)
```

#### 3.2.1 Recommended Choices for $C_i(s)$

Pick one and document it per metric:

1. **Range scale (robust default)**

   $$
   C_i(s) = \max_{a \in A_{\text{adm}}} M_i(s,a) - \min_{a \in A_{\text{adm}}} M_i(s,a)
   $$

1. **Tolerance scale (SLO/SLA anchored)**

   $$
   C_i(s) = \text{SLO}_i
   $$

   (for "must not exceed" constraints)

1. **Utopia (fraction-of-optimum, use with care)**

   $$
   C_i(s) = |M_i(s,a^*)|
   $$

   (singular when optimum is 0)

This mirrors nondimensionalization practice in physics codes where equations are commonly expressed in nondimensional form to preserve invariance under unit choice.

---

### 3.3 Comparator Definition: Best Admissible Alternative

The comparator must be **admissible**: it cannot depend on information unavailable to the evaluated agent at decision time.

Let $I(h)$ be the information set induced by observable history $h$.

An alternative $a$ is admissible if it maps $I(h)$ to decisions without using hidden state (private variables, future RNG outcomes, external oracle information).

$$
a \in A_{\text{adm}} \iff a = \pi(I(h))
$$

Then:

$$
a^* = \arg\max_{a \in A_{\text{adm}}} J(s,a)
$$

This prevents "clairvoyance regret" (penalizing agents for not using inaccessible information) and aligns regret with decision quality rather than information advantage.

---

## 4. Scalarization Limits and Pareto Structure

The weighted-sum scalarization restricts optimization to the Pareto frontier. In non-convex tradeoff surfaces, some Pareto-optimal points are not representable by any fixed weight vector.

This is a documented limitation. If non-convex Pareto coverage is required, use a different scalarization (for example Chebyshev / max-norm formulations) and treat it as a separate objective definition.

---

## 5. Conservation Laws (Correctness Invariants)

### 5.1 Conservation of History (Deterministic Replay)

With fixed `(spec, seed, trace)` the execution is a pure function and produces bitwise-identical outputs:

- identical derived metrics
- identical decision sequence
- identical derived-state hash

Any divergence indicates entropy injection (race conditions, nondeterministic iteration order, unseeded randomness, external time, network I/O).

### 5.2 Conservation of Trace (Boundary Condition Invariance)

The workload trace is immutable and independent of the alternative being evaluated.

If choosing $a$ changes the subsequent trace arrival pattern and that feedback is not modeled deterministically inside the frozen system, counterfactual comparison is invalid.

### 5.3 Conservation of Dimensionality

All aggregated regret scalars must be dimensionless.

Implementations must reject any configuration that aggregates heterogeneous units without explicit $C_i(s)$ normalization.

### 5.4 Offline Isolation

Metric computation and regret attribution occur post-execution.

No gradient updates or online learning occurs during measurement.

---

## 6. Validity Checks and Hard Failures

The following are treated as correctness failures, not "bad predictive regret" after admissible maximization:

- **Trace divergence** between alternatives: indicates invalid counterfactual evaluation.
- **Unnormalized aggregation** across heterogeneous units: indicates dimensional inconsistency.
- **Information leakage** into $a^*$: indicates comparator inadmissibility.

---

## 7. Artifact Mapping (Theory -> Repo)

- $s$ (boundary conditions): `traces/` plus frozen environment state
- $A$ and admissibility constraints: `specs/` (policies, action sets, observation model)
- $M_i$: replay-derived metrics in `runs/` or `traces/` append-only outputs
- $C_i$: characteristic scales, defined in spec and versioned with evaluation
- $\mathrm{Regret}$: evaluation artifact emitted by offline analyzer

---

## 8. Minimal Falsification Scenario (Asymmetric Information Externality)

A minimal scenario that falsifies naive regret engines:

- Two agents
- One decision step
- Two actions
- Asymmetric private information
- Externality cost

Naive engines define $a^*$ using hidden state and measure "luck regret".

Correct engines define $a^*$ over admissible strategies and measure "decision regret".

---

## 9. Documentation Conventions

High-fidelity simulation and computational physics begin with theory: governing equations, invariants, and boundary conditions.

This file anchors those commitments for the repository and serves as the reference point for spec, trace, and evaluation logic.
