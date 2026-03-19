# CFMM Specification — Submodule of Type-Driven Development

## Overview

**Every CFMM built on Uniswap MUST satisfy 19 mandatory invariants derived from two academic formalizations.** This submodule activates when any feature touches CFMM state: reserves, fees, ticks, liquidity, or prices.

Source papers (non-negotiable foundations):
- Bartoletti et al., "Formalizing Automated Market Makers in the Lean 4 Theorem Prover" (arXiv:2402.06064)
- "Formal State-Machine Models for Uniswap v3" (arXiv:2512.06203)

We do NOT use Lean 4. We translate the same invariants, rules, and formalizations into the Kontrol framework enforced by the parent type-driven-development skill.

## Activation Trigger

This submodule is mandatory when the feature being built touches ANY of: pool state, swap logic, LP add/remove, fee accrual, tick crossing, reserve accounting, price computation, or liquidity management.

If you are unsure whether your feature touches CFMM state, it does. Apply the submodule.

## Phase 1 Override — TLA+ Specification Required

Before writing Hoare triples in Phase 2, Spec Kit output MUST include a TLA+ module that EXTENDS one of the base models from the FSM paper.

### Base Model Selection (MANDATORY)

Before writing TLA+, ask the user:

```
Which base TLA+ model does this feature extend?

1. ToyCLAMM — single-tick, single-direction, no fees
2. ToyCLAMM2Dir — single-tick, bidirectional swaps, no fees
3. ToyCLAMM2DirArb — bidirectional + arbitrage actions
4. ToyCLAMM3Tick — multi-tick with tick crossings

Choose the simplest model that captures your feature's state transitions.
```

Do NOT choose for the user. Do NOT skip this question. Do NOT default to ToyCLAMM3Tick "to be safe."

### Notation Contract

These rules are absolute:

- **Preserve paper variables exactly**: `X`, `Y`, `L_act`, `F_x`, `F_y`, `p`, `i_c`, `i_l`, `i_u`
- **`φ` (phi) = trading fee rate** (project convention from DRAFT.md)
- **Paper's pricing function `φ` becomes `ϕ` (varphi)** to avoid collision with fee rate
- **New variables must use unused letters** — never collide with existing notation
- **Extensions add rules via `EXTENDS`** — never overwrite base rules

### TLA+ Module Template

```tla+
---- MODULE ThetaSwap<FeatureName> ----
EXTENDS <SelectedBaseModel>

\* New state variables (unused letters only)
VARIABLES <new_vars>

\* Feature-specific rules (extend, never override)
<FeatureName>Next == BaseNext \/ NewRule1 \/ NewRule2

\* Invariants from CFMM-01 through CFMM-19 plus feature-specific
<FeatureName>Inv == BaseInv /\ NewInv1 /\ NewInv2

====
```

Output: `specs/<feature>/model.tla` alongside `spec.md`, `plan.md`, `tasks.md`.

## Phase 2 Override — 19 Mandatory Invariants

The parent skill requires ~10 invariants. When this submodule activates, the floor is 19 CFMM invariants (CFMM-01 through CFMM-19). Projects add CFMM-20+ for feature-specific invariants on top.

"~10 is enough for a CFMM" is wrong. CFMMs have structural, economic, rate, and state-machine properties that all require independent verification.

### Tier 1 — Structural (5)

| ID | Name | Hoare Triple |
|---|---|---|
| CFMM-01 | No-drain (swap) | {X>0 ∧ Y>0} → swap(Δx) → {X'>0 ∧ Y'>0} |
| CFMM-02 | No-drain (redeem) | {X>0 ∧ Y>0} → redeem(s) → {X'≥0 ∧ Y'≥0} |
| CFMM-03 | Output bound | {swap(Δx)} → {Δy < Y} |
| CFMM-04 | AMM↔supply biconditional | {active(amm)} ↔ {totalSupply > 0} |
| CFMM-05 | Swap preserves LP supply | {S_total} → swap(Δx) → {S_total' == S_total} |

### Tier 2 — Economic (5)

| ID | Name | Source | Property |
|---|---|---|---|
| CFMM-06 | Gain formula | Bartoletti Thm 2 | gain(Γ,t) = S_t·r(Γ,t) − c_t |
| CFMM-07 | Gain direction | Bartoletti Cor | gain ≥ 0 iff S_t·r(Γ,t) ≥ c_t |
| CFMM-08 | Rate vs oracle | Bartoletti Prop 6 | \|SX(Γ,Δx) − π\| < ε for small Δx |
| CFMM-09 | Optimality sufficiency | Bartoletti Thm 4 | swap maximizes gain when SX = π |
| CFMM-10 | Arbitrage formula | Bartoletti Thm 3 | optimal Δx* = f(reserves, π) |

### Tier 3 — Rate Properties (4)

| ID | Name | Property |
|---|---|---|
| CFMM-11 | Monotonicity | SX(Γ, Δx₁) ≥ SX(Γ, Δx₂) when Δx₁ ≤ Δx₂ |
| CFMM-12 | Homogeneity | SX(k·Γ, k·Δx) = SX(Γ, Δx) |
| CFMM-13 | Additivity | SX(Γ, Δx₁+Δx₂) ≤ SX(Γ, Δx₁) (no free lunch) |
| CFMM-14 | Reversibility | swap(Δx) then swap(−Δy) returns to original state (zero-fee case) |

### Tier 4 — State Machine (5)

| ID | Name | Source | Property |
|---|---|---|---|
| CFMM-15 | ε-slack product invariant | FSM paper | \|X·Y − L²\| ≤ ε for active tick |
| CFMM-16 | Non-negativity | FSM paper | X ≥ 0 ∧ Y ≥ 0 ∧ L_act ≥ 0 |
| CFMM-17 | Resource bounds | FSM paper | X ≤ 2¹²⁸−1 ∧ Y ≤ 2¹²⁸−1 |
| CFMM-18 | No rounding arbitrage | FSM paper | repeated swap cycle cannot extract value |
| CFMM-19 | Cross-tick invariant | FSM paper | L_act updates correctly on tick crossing |

### Adding Feature-Specific Invariants

Projects MUST add CFMM-20+ for invariants specific to their feature. The 19 above are the mandatory floor, not the ceiling.

## Phase 3 Override — Mandatory UDVT Types

When this submodule activates, Phase 3 MUST include these dimensional types:

```solidity
type ReserveX is uint256;    // token X reserve quantity
type ReserveY is uint256;    // token Y reserve quantity
type Liquidity is uint128;   // active liquidity (L_act in paper notation)
type SqrtPriceX96 is uint160; // √price in Q64.96 (Uniswap convention)
type TickIndex is int24;     // tick index (i_c, i_l, i_u in paper notation)
type FeeRate is uint24;      // φ in project notation
type FeeAccumX is uint256;   // F_x in paper notation
type FeeAccumY is uint256;   // F_y in paper notation
```

**Construction rules (enforced, not optional):**
- `ReserveX + ReserveY` must not compile — dimensional safety
- `SqrtPriceX96` only through validated factory — opaque construction
- `TickIndex` bounds-checked at creation: `MIN_TICK ≤ i ≤ MAX_TICK`
- `FeeRate` capped at factory: `fee ≤ MAX_FEE`
- `Liquidity` created only through LP operations, never raw wrap

Projects may add more types. Projects must NOT remove or weaken these.

## Kontrol Proof Mapping

Each of the 19 invariants maps to at least one Kontrol proof. The parent skill's one-at-a-time rule applies — write one, build, prove, review, then next.

Proof naming: `prove_cfmm_<tier>_<name>`. Examples:
- `prove_cfmm_structural_noDrainSwap` (CFMM-01)
- `prove_cfmm_economic_gainFormula` (CFMM-06)
- `prove_cfmm_rate_monotonicity` (CFMM-11)
- `prove_cfmm_fsm_epsilonSlack` (CFMM-15)

Recommended proof order: Tier 1 first (structural soundness), then Tier 4 (state machine correctness), then Tier 3 (rate properties), then Tier 2 (economic properties). Economic proofs depend on structural and rate properties being established.

## Red Flags — STOP and Apply This Submodule

- CFMM feature without TLA+ base model selection
- Fewer than 19 invariants for a CFMM feature
- "~10 invariants is enough for a swap function"
- Using `reserveA`/`reserveB` instead of `ReserveX`/`ReserveY`
- Missing paper notation (`X`, `Y`, `L_act`, `F_x`, `F_y`)
- No academic paper citations in the spec
- "We don't need TLA+ for this"
- "The Bartoletti properties are theoretical, not practical"
- "Rate properties are obvious for constant-product"
- "Cross-tick invariants don't apply to our simple case"
- Overwriting base TLA+ rules instead of extending

| Rationalization | Reality |
|---|---|
| "~10 invariants covers a swap" | Swaps have structural + economic + rate + FSM properties. 10 misses entire tiers. |
| "TLA+ is overkill" | The FSM paper proved bugs in Uniswap v3 using TLA+. It caught what tests missed. |
| "Rate properties are obvious" | Monotonicity and additivity failures enable MEV extraction. Prove them. |
| "We can skip Tier 2 economics" | Gain formula errors mean LPs lose money silently. Bartoletti formalized this for a reason. |
| "Cross-tick doesn't apply" | If you use concentrated liquidity at all, tick crossings are your highest-risk state transition. |
| "Paper notation is academic overhead" | Shared notation lets auditors verify against published proofs. Custom notation requires re-deriving everything. |

## References

- Bartoletti et al., "Formalizing Automated Market Makers in the Lean 4 Theorem Prover" (arXiv:2402.06064)
- "Formal State-Machine Models for Uniswap v3" (arXiv:2512.06203)
- Parent skill: type-driven-development
- ThetaSwap DRAFT.md (project notation: φ = fee rate)
