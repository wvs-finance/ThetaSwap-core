# CFMM Specification Submodule — Design Document

**Date:** 2026-03-02
**Status:** Approved
**Parent Skill:** type-driven-development

## Identity

The cfmm-specification is a **submodule** of the type-driven-development skill. It activates whenever a feature touches CFMM state (reserves, fees, ticks, liquidity, prices). It is NOT a standalone skill.

**Source papers:**
- Bartoletti et al., "Formalizing Automated Market Makers in the Lean 4 Theorem Prover" (arXiv:2402.06064) — swap rate properties, gain formula, no-drain, arbitrage optimality
- "Formal State-Machine Models for Uniswap v3" (arXiv:2512.06203) — TLA+ FSM models, tick-wise invariants, rounding bounds

**Key constraint:** We do NOT use Lean 4. We translate the same invariants, rules, and formalizations into the Kontrol framework enforced by the parent type-driven-development skill.

## Spec Kit + TLA+ Integration

### Base Model Selection

Before writing TLA+ in Phase 1 (Specify), the agent MUST ask:

```
Which base TLA+ model does this feature extend?

1. ToyCLAMM — single-tick, single-direction, no fees
2. ToyCLAMM2Dir — single-tick, bidirectional swaps, no fees
3. ToyCLAMM2DirArb — bidirectional + arbitrage actions
4. ToyCLAMM3Tick — multi-tick with tick crossings

Choose the simplest model that captures your feature's state transitions.
```

The selected model determines inherited state variables, existing rules, and what the extension adds.

### Notation Contract

- Paper variables preserved exactly: `X`, `Y`, `L_act`, `F_x`, `F_y`, `p`, `i_c`, `i_l`, `i_u`
- `φ` (phi) = trading fee rate (project convention from DRAFT.md)
- Paper's pricing function `φ` renamed to `ϕ` (varphi) to avoid collision
- New variables must use different letters from existing notation
- Extensions add rules via `EXTENDS`, never overwrite base rules

### TLA+ Module Structure

```tla+
---- MODULE ThetaSwapFeature ----
EXTENDS ToyCLAMM3Tick  \* or whichever base model selected

\* New state variables (unused letters only)
VARIABLES θ_commitment, θ_feeRevenue

\* New rules extend base, never override
ThetaSwapNext == BaseNext \/ CommitRule \/ ClaimRule

====
```

## Mandatory Kontrol Invariants (19)

### Tier 1 — Structural (5)

| ID | Name | Hoare Triple |
|---|---|---|
| CFMM-01 | No-drain (swap) | {X>0 ∧ Y>0} → swap(Δx) → {X'>0 ∧ Y'>0} |
| CFMM-02 | No-drain (redeem) | {X>0 ∧ Y>0} → redeem(s) → {X'≥0 ∧ Y'≥0} |
| CFMM-03 | Output bound | {swap(Δx)} → {Δy < Y} |
| CFMM-04 | AMM↔supply biconditional | {active(amm)} ↔ {totalSupply > 0} |
| CFMM-05 | Swap preserves LP supply | {S_total} → swap(Δx) → {S_total' == S_total} |

### Tier 2 — Economic (5)

| ID | Name | Source |
|---|---|---|
| CFMM-06 | Gain formula | Bartoletti Theorem 2: gain(Γ,t) = S_t·r(Γ,t) − c_t |
| CFMM-07 | Gain direction | Bartoletti Corollary: gain ≥ 0 iff S_t·r(Γ,t) ≥ c_t |
| CFMM-08 | Rate vs oracle | Bartoletti Prop 6: |SX(Γ,Δx) − π| < ε for small Δx |
| CFMM-09 | Optimality sufficiency | Bartoletti Theorem 4: swap maximizes gain when SX = π |
| CFMM-10 | Arbitrage formula | Bartoletti Theorem 3: optimal Δx* = f(reserves, π) |

### Tier 3 — Rate Properties (4)

| ID | Name | Property |
|---|---|---|
| CFMM-11 | Monotonicity | SX(Γ, Δx₁) ≥ SX(Γ, Δx₂) when Δx₁ ≤ Δx₂ |
| CFMM-12 | Homogeneity | SX(k·Γ, k·Δx) = SX(Γ, Δx) |
| CFMM-13 | Additivity | SX(Γ, Δx₁+Δx₂) ≤ SX(Γ, Δx₁) (no free lunch) |
| CFMM-14 | Reversibility | swap(Δx) then swap(−Δy) returns to original state (fees=0 case) |

### Tier 4 — State Machine (5)

| ID | Name | Source |
|---|---|---|
| CFMM-15 | ε-slack product invariant | FSM paper: |X·Y − L²| ≤ ε for active tick |
| CFMM-16 | Non-negativity | FSM paper: X ≥ 0 ∧ Y ≥ 0 ∧ L_act ≥ 0 |
| CFMM-17 | Resource bounds | FSM paper: X ≤ 2¹²⁸−1 ∧ Y ≤ 2¹²⁸−1 |
| CFMM-18 | No rounding arbitrage | FSM paper: repeated swap cycle cannot extract value |
| CFMM-19 | Cross-tick invariant | FSM paper: L_act updates correctly on tick crossing |

Projects add CFMM-20+ for feature-specific invariants. These 19 are the mandatory floor.

## File Structure & Integration

```
~/.claude/skills/type-driven-development/
  SKILL.md                    # Main skill (gains CFMM Submodule section)
  cfmm-specification.md       # This submodule
```

### TDD Phase Integration

| TDD Phase | cfmm-specification adds |
|---|---|
| Phase 1 (Specify) | TLA+ module extending base model, φ→ϕ notation override |
| Phase 2 (Invariants) | 19 mandatory CFMM invariants as floor, project adds CFMM-20+ |
| Phase 3 (Types) | Mandatory dimensional UDVTs (see below) |
| Phase 4 (Proofs) | Kontrol proofs map 1:1 to invariants, same one-at-a-time rule |
| Phase 5-7 | No changes — same static analysis, implement, verify gates |

### Activation Trigger

The submodule activates when a feature touches any CFMM component: pool, swap, LP, fee, tick, reserve, liquidity, or price state.

## Mandatory UDVT Types

Phase 3 of TDD gains these required dimensional types when cfmm-specification activates:

```solidity
// Reserve types — prevent mixing X and Y reserves
type ReserveX is uint256;
type ReserveY is uint256;

// Liquidity — distinct from reserves
type Liquidity is uint128;

// Price types — sqrt price encoding (Uniswap convention)
type SqrtPriceX96 is uint160;

// Tick types — signed integer range
type TickIndex is int24;

// Fee types — basis points or WAD-scaled
type FeeRate is uint24;

// Fee accumulators — separate per token
type FeeAccumX is uint256;
type FeeAccumY is uint256;
```

**Construction rules:**
- `ReserveX + ReserveY` must not compile (dimensional safety)
- `SqrtPriceX96` created only through validated factory (opaque construction)
- `TickIndex` bounds checked at creation (`MIN_TICK <= i <= MAX_TICK`)
- `FeeRate` capped at factory (`fee <= MAX_FEE`)

Projects may add more types but must not remove or weaken these.

## References

- Bartoletti et al., "Formalizing Automated Market Makers in the Lean 4 Theorem Prover" (arXiv:2402.06064)
- "Formal State-Machine Models for Uniswap v3" (arXiv:2512.06203)
- Type-Driven Development skill (parent)
- ThetaSwap DRAFT.md (project notation conventions)
