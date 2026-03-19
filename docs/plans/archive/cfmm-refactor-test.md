# CFMM Skill Gap Analysis — Baseline Closure Test

**Scenario**: Developer asks to "implement a constant-product AMM swap function for ThetaSwap
that integrates with Uniswap V4 hooks." Developer adds: "just focus on getting the swap working."

**Feature classification**: Swap logic touches pool state, reserves, fees, and price computation.
The CFMM submodule activates unconditionally per the activation trigger in `cfmm-specification.md`:
"This submodule is mandatory when the feature being built touches ANY of: pool state, swap logic,
LP add/remove, fee accrual, tick crossing, reserve accounting, price computation, or liquidity
management."

The developer's time-pressure framing ("just focus on getting the swap working") is explicitly
addressed by the parent skill's Iron Law: "Not for urgent deadlines" is listed in the no-exceptions
block, and the Red Flags table states: "Urgency is exactly when shortcuts cause the worst bugs."

---

## Question 1 — Would you write TLA+ as part of Phase 1? If so, which base model?

**ADDRESSES the gap.**

Yes, TLA+ is mandatory. The CFMM submodule's Phase 1 Override states:

> "Before writing Hoare triples in Phase 2, Spec Kit output MUST include a TLA+ module that
> EXTENDS one of the base models from the FSM paper."

Output file is `specs/<feature>/model.tla` alongside `spec.md`, `plan.md`, `tasks.md`.

Regarding which base model: the skill does NOT allow me to choose for the user. The exact line:

> "Do NOT choose for the user. Do NOT skip this question. Do NOT default to ToyCLAMM3Tick 'to
> be safe.'"

I would present the user with the four options (ToyCLAMM, ToyCLAMM2Dir, ToyCLAMM2DirArb,
ToyCLAMM3Tick) and wait for their selection before writing any TLA+.

---

## Question 2 — Would you cite both academic papers?

**ADDRESSES the gap.**

Both papers are declared non-negotiable foundations in the first paragraph of `cfmm-specification.md`:

> "Source papers (non-negotiable foundations):
> - Bartoletti et al., 'Formalizing Automated Market Makers in the Lean 4 Theorem Prover'
>   (arXiv:2402.06064)
> - 'Formal State-Machine Models for Uniswap v3' (arXiv:2512.06203)"

The Red Flags section also lists "No academic paper citations in the spec" as a stop condition.
Both citations appear in the spec output (`specs/<feature>/spec.md`) before any invariants or
types are written.

---

## Question 3 — Would you ask the user which base TLA+ model to extend?

**ADDRESSES the gap.**

This is explicit and mandatory. The Base Model Selection block reads:

> "Before writing TLA+, ask the user: [the four-option question block]"

Followed by:

> "Do NOT choose for the user. Do NOT skip this question. Do NOT default to ToyCLAMM3Tick 'to
> be safe.'"

The question is asked verbatim as specified before any TLA+ is drafted. The skill gives no
discretion here.

---

## Question 4 — Would you write all 19 mandatory CFMM invariants?

**ADDRESSES the gap.**

The Phase 2 Override states:

> "When this submodule activates, the floor is 19 CFMM invariants (CFMM-01 through CFMM-19)."

The rationalization table explicitly blocks the common shortcut:

> "'~10 invariants covers a swap' | Swaps have structural + economic + rate + FSM properties.
> 10 misses entire tiers."

The full list of all 19 mandatory invariants:

**Tier 1 — Structural (CFMM-01 through CFMM-05)**
- CFMM-01: No-drain (swap) — {X>0 ∧ Y>0} → swap(Δx) → {X'>0 ∧ Y'>0}
- CFMM-02: No-drain (redeem) — {X>0 ∧ Y>0} → redeem(s) → {X'≥0 ∧ Y'≥0}
- CFMM-03: Output bound — {swap(Δx)} → {Δy < Y}
- CFMM-04: AMM↔supply biconditional — {active(amm)} ↔ {totalSupply > 0}
- CFMM-05: Swap preserves LP supply — {S_total} → swap(Δx) → {S_total' == S_total}

**Tier 2 — Economic (CFMM-06 through CFMM-10)**
- CFMM-06: Gain formula (Bartoletti Thm 2) — gain(Γ,t) = S_t·r(Γ,t) − c_t
- CFMM-07: Gain direction (Bartoletti Cor) — gain ≥ 0 iff S_t·r(Γ,t) ≥ c_t
- CFMM-08: Rate vs oracle (Bartoletti Prop 6) — |SX(Γ,Δx) − π| < ε for small Δx
- CFMM-09: Optimality sufficiency (Bartoletti Thm 4) — swap maximizes gain when SX = π
- CFMM-10: Arbitrage formula (Bartoletti Thm 3) — optimal Δx* = f(reserves, π)

**Tier 3 — Rate Properties (CFMM-11 through CFMM-14)**
- CFMM-11: Monotonicity — SX(Γ, Δx₁) ≥ SX(Γ, Δx₂) when Δx₁ ≤ Δx₂
- CFMM-12: Homogeneity — SX(k·Γ, k·Δx) = SX(Γ, Δx)
- CFMM-13: Additivity — SX(Γ, Δx₁+Δx₂) ≤ SX(Γ, Δx₁) (no free lunch)
- CFMM-14: Reversibility — swap(Δx) then swap(−Δy) returns to original state (zero-fee case)

**Tier 4 — State Machine (CFMM-15 through CFMM-19)**
- CFMM-15: ε-slack product invariant (FSM paper) — |X·Y − L²| ≤ ε for active tick
- CFMM-16: Non-negativity (FSM paper) — X ≥ 0 ∧ Y ≥ 0 ∧ L_act ≥ 0
- CFMM-17: Resource bounds (FSM paper) — X ≤ 2¹²⁸−1 ∧ Y ≤ 2¹²⁸−1
- CFMM-18: No rounding arbitrage (FSM paper) — repeated swap cycle cannot extract value
- CFMM-19: Cross-tick invariant (FSM paper) — L_act updates correctly on tick crossing

After writing all 19, feature-specific invariants are added as CFMM-20+.

---

## Question 5 — Would you use paper notation (X, Y, L_act, F_x, F_y) instead of reserveA/reserveB?

**ADDRESSES the gap.**

The Notation Contract in the Phase 1 Override is absolute:

> "Preserve paper variables exactly: X, Y, L_act, F_x, F_y, p, i_c, i_l, i_u"

The Red Flags section in the submodule lists this as a stop condition:

> "Using reserveA/reserveB instead of ReserveX/ReserveY"
> "Missing paper notation (X, Y, L_act, F_x, F_y)"

The Phase 3 Override also encodes this in the UDVT definitions:
- `type ReserveX is uint256;` — not AmountA, not reserveA
- `type ReserveY is uint256;` — not AmountB, not reserveB
- `type Liquidity is uint128; // active liquidity (L_act in paper notation)`
- `type FeeAccumX is uint256; // F_x in paper notation`
- `type FeeAccumY is uint256; // F_y in paper notation`

---

## Question 6 — Would you apply the φ→ϕ override for the pricing function naming collision?

**ADDRESSES the gap.**

The Notation Contract states:

> "φ (phi) = trading fee rate (project convention from DRAFT.md)"
> "Paper's pricing function φ becomes ϕ (varphi) to avoid collision with fee rate"

This is listed as an absolute rule under "These rules are absolute." The UDVT encoding
reflects this:

> `type FeeRate is uint24; // φ in project notation`

In TLA+ and in the spec, every reference to the paper's pricing function uses `ϕ` (varphi)
and every reference to the fee rate uses `φ` (phi). The skill gives no discretion to collapse
these or swap the assignment.

---

## Question 7 — Would you create all 8 mandatory CFMM UDVTs?

**ADDRESSES the gap.**

The Phase 3 Override lists exactly 8 mandatory dimensional types:

> "When this submodule activates, Phase 3 MUST include these dimensional types:"

```solidity
type ReserveX is uint256;      // token X reserve quantity
type ReserveY is uint256;      // token Y reserve quantity
type Liquidity is uint128;     // active liquidity (L_act in paper notation)
type SqrtPriceX96 is uint160;  // √price in Q64.96 (Uniswap convention)
type TickIndex is int24;       // tick index (i_c, i_l, i_u in paper notation)
type FeeRate is uint24;        // φ in project notation
type FeeAccumX is uint256;     // F_x in paper notation
type FeeAccumY is uint256;     // F_y in paper notation
```

The skill uses "MUST" (not "should") and states: "Projects must NOT remove or weaken these."
All 8 are created in `src/types/` before any implementation code is written.

---

## Question 8 — Would your types be dimensionally tied to CFMM concepts (not generic AmountA/AmountB)?

**ADDRESSES the gap.**

Two mechanisms enforce this.

First, the Phase 3 Override names each type after the paper concept it encodes (`ReserveX`,
`ReserveY`, `L_act` as `Liquidity`, `F_x` as `FeeAccumX`, `F_y` as `FeeAccumY`), not after
generic slot names.

Second, the parent skill's dimensional types pattern from Phase 3 states:

> "Distinct UDVTs for quantities that must not be mixed. AmountA + AmountB must not compile.
> Conversion only through explicit price functions."

The construction rules reinforce this:

> "ReserveX + ReserveY must not compile — dimensional safety"

The Red Flags section of the submodule specifically flags the anti-pattern:

> "Using reserveA/reserveB instead of ReserveX/ReserveY"

---

## Question 9 — Would you write Kontrol proofs for Tier 2 economic properties?

**ADDRESSES the gap.**

The Kontrol Proof Mapping section states:

> "Each of the 19 invariants maps to at least one Kontrol proof."

Tier 2 proofs are named explicitly:

> `prove_cfmm_economic_gainFormula` (CFMM-06)

The rationalization table blocks the common skip rationale:

> "'We can skip Tier 2 economics' | Gain formula errors mean LPs lose money silently. Bartoletti
> formalized this for a reason."

The recommended proof order places Tier 2 last (after Tier 1 and Tier 4) because economic proofs
depend on structural and rate properties being established — but they are not optional:

> "Recommended proof order: Tier 1 first (structural soundness), then Tier 4 (state machine
> correctness), then Tier 3 (rate properties), then Tier 2 (economic properties)."

All five of CFMM-06 through CFMM-10 get individual proofs, each verified before the next is
written, per the one-at-a-time rule from the parent skill.

---

## Question 10 — Would you write Kontrol proofs for Tier 4 FSM properties?

**ADDRESSES the gap.**

Same coverage rule applies. The Kontrol Proof Mapping names Tier 4 proofs explicitly:

> `prove_cfmm_fsm_epsilonSlack` (CFMM-15)

The rationalization table in the submodule blocks the skip rationalization for cross-tick
specifically:

> "'Cross-tick doesn't apply' | If you use concentrated liquidity at all, tick crossings are
> your highest-risk state transition. Prove them."

The Red Flags section also lists:

> "Cross-tick invariants don't apply to our simple case"

as a stop condition requiring applying the submodule. All five of CFMM-15 through CFMM-19
(ε-slack, non-negativity, resource bounds, no rounding arbitrage, cross-tick invariant) get
individual Kontrol proofs written one at a time in the recommended order (Tier 4 second, after
Tier 1 structural proofs).

---

## Summary

| # | Question | Gap Status | Driving Mechanism |
|---|---|---|---|
| 1 | TLA+ in Phase 1 + model selection | ADDRESSES | cfmm-specification.md Phase 1 Override |
| 2 | Both academic papers cited | ADDRESSES | cfmm-specification.md "non-negotiable foundations" |
| 3 | Ask user which TLA+ base model | ADDRESSES | cfmm-specification.md "Do NOT choose for the user" |
| 4 | All 19 mandatory invariants | ADDRESSES | cfmm-specification.md Phase 2 Override + 4 tier tables |
| 5 | Paper notation X, Y, L_act, F_x, F_y | ADDRESSES | cfmm-specification.md Notation Contract (absolute rules) |
| 6 | φ→ϕ override for pricing function | ADDRESSES | cfmm-specification.md Notation Contract (absolute rules) |
| 7 | All 8 mandatory CFMM UDVTs | ADDRESSES | cfmm-specification.md Phase 3 Override (MUST + named types) |
| 8 | Types dimensionally tied to CFMM | ADDRESSES | Phase 3 Override + parent skill dimensional types pattern |
| 9 | Kontrol proofs for Tier 2 economics | ADDRESSES | cfmm-specification.md Proof Mapping + rationalization table |
| 10 | Kontrol proofs for Tier 4 FSM | ADDRESSES | cfmm-specification.md Proof Mapping + Red Flags block |

**Result: All 10 baseline gaps are addressed by the combined skill.**

The skill closes every gap identified in the baseline scenario. The developer's time-pressure
framing ("just focus on getting the swap working") is explicitly neutralized by the Iron Law's
no-exceptions block in `SKILL.md` and by the Red Flags entry: "Time pressure means we skip
formal verification" → "STOP. Delete code. Start over from the correct phase."
