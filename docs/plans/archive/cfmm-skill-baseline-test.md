# CFMM Skill Baseline Test — Covered Call Replicating CFMM

**Date:** 2026-03-02
**Agent persona:** Baseline Claude Code — no type-driven-development skill, no cfmm-specification submodule loaded
**Scenario:** User asks for a complete CFMM that replicates a covered call payoff `max(S_T - K, 0)`. Derive trading function, invariants, reserves, fee structure. Output LaTeX in `specs/model/`.
**Purpose:** Find gaps the skill and submodule need to close. Document natural tendencies, not ideal behavior.

---

## 1. What I Would Do — Step by Step

### Step 1 — Immediately start deriving math

I would not ask clarifying questions first. The request is technically specific enough that I would interpret it as "go derive the CFMM" and start writing. This is the first gap: I would skip the Spec Kit phase entirely.

I would recall that Angeris et al. ("Replicating Market Makers," 2021) established that a CFMM with trading function `\psi(x, y)` replicates a payoff `V(p)` if:

```
V(p) = \psi(x(p), y(p)) + x(p) * p
```

where `x(p)` and `y(p)` are the reserve curves as functions of the spot price `p`, and `V` is the portfolio value at price `p`.

I would recognize that a covered call payoff is `max(S_T - K, 0)` and that this is the convex conjugate framework from the Angeris replication paper. I would proceed with a derivation.

### Step 2 — Attempt the trading function derivation

I would derive as follows (what I would actually write):

The covered call payoff is `V(p) = max(p - K, 0)`. To find the reserves:

From Angeris et al., the reserve `x(p)` (risky asset) satisfies:

```
x(p) = -V'(p)
```

where `V'` is the derivative of the payoff with respect to spot price. So:

```
V'(p) = 0      if p < K
V'(p) = 1      if p > K
```

Therefore:

```
x(p) = 0   if p < K (no risky asset held below strike)
x(p) = -1  if p > K
```

Here I would immediately get confused. `x(p) = -1` is negative reserves, which is nonsensical for a CFMM holding physical reserves. I would recognize the sign convention issue but handle it poorly — I would probably flip the sign without rigorous justification and say "the LP holds 1 unit of risky asset when in-the-money" without connecting this to an actual CFMM construction.

### Step 3 — Attempt to define the trading function

I would attempt to define `\psi(x, y) = V(p) - x \cdot p` but would not correctly derive what the closed-form trading function is for the covered call case. I would likely write:

```
\psi(x, y) = y - max(K - x \cdot K, 0)
```

or some ad hoc formula that I could not prove satisfies the replication condition. This is wrong. The correct trading function for a covered call replicating CFMM is not trivial to derive and requires working through the convex conjugate of the payoff.

### Step 4 — Write LaTeX files

I would create LaTeX files in `specs/model/`. The structure I would produce:

- `specs/model/trading-function.tex` — containing the incorrectly derived formula with some correct surrounding mathematics
- `specs/model/invariants.tex` — containing 3-5 informal invariants, not structured Hoare triples
- `specs/model/reserves.tex` — containing the reserve curve derivation, which would be partially correct for the `p < K` region and wrong for `p > K`
- `specs/model/fees.tex` — containing a generic fee structure borrowed from constant-product (not derived from the replication framework)

The LaTeX would use `\documentclass{article}`, proper math environments (`align`, `equation`), and would be syntactically valid. It would look professional but be mathematically incomplete.

### Step 5 — Fill in the fee structure

I would reach for the simplest answer: a proportional fee on input amount, identical to Uniswap's `(1 - \phi) \cdot \Delta x`. I would not derive the fee structure from the replication framework. I would not ask whether the fee should preserve the replication property. This is a significant gap: a fee that breaks the replication is useless for the stated purpose.

### Step 6 — Declare the output complete

I would present the files and suggest the user review the math. I would express appropriate uncertainty about the exact form of the trading function but present the overall structure as correct. I would be wrong.

---

## 2. What Questions I Would Ask the User

I would ask very few questions, and they would be the wrong questions:

1. "What is the underlying asset (ERC-20 token address)?" — implementation detail, not mathematical
2. "Is the expiry date fixed or rolling?" — partially relevant but I would ask it too late, after deriving, not before
3. "Do you want the fee expressed in basis points?" — implementation detail

**Questions I would NOT ask (but should):**

- Which replication framework? Angeris et al. 2021 ("Replicating Market Makers") or Angeris et al. 2022 ("Replicating Monotone Payoffs Without Oracles")? These are materially different constructions.
- Is this a covered call on the risky asset or a covered call written by the LP? The payoff `max(S_T - K, 0)` is from the buyer's perspective. The LP position in a covered call CFMM is the writer's perspective, which is the negative of this.
- Should the CFMM replicate the payoff statically (holds exact replicating portfolio at all times) or dynamically (drifts toward replication)?
- Is the numeraire token the strike currency? What is the unit of account for `K`?
- Does the CFMM need to be oracle-free (Angeris 2022) or oracle-assisted (Angeris 2021)?
- What is the liquidity provision model — constant portfolio size, or does the LP size change with the replicating portfolio?

---

## 3. What I Would Assume Without Asking

I would make the following assumptions silently, without flagging them:

1. **The payoff is the LP's payoff, not the option buyer's payoff.** This is ambiguous. A covered call CFMM replicates the *seller's* (writer's) position, which is `S_T - max(S_T - K, 0) = min(S_T, K)`. I would likely confuse these and derive the wrong sign in the reserve formula.

2. **The fee structure is proportional on input.** I would not verify this preserves the replication property.

3. **The CFMM operates over the full price range `[0, ∞)`.** In practice, covered call replication only makes sense over the price range where the payoff changes, i.e., around `K`. I would not introduce a price range restriction.

4. **`K` is a constant in the trading function.** In reality, for a rolling expiry CFMM, `K` would need to be a state variable updated periodically. I would treat `K` as a hardcoded constant without flagging this.

5. **The invariant is the trading function value itself.** I would state "the invariant is `\psi(x, y) = C`" without specifying what `C` is at initialization, how it changes with liquidity provision, or whether `C` is preserved across fee deductions.

6. **The Angeris 2021 framework applies directly.** The 2021 paper requires the payoff to be concave. `max(S_T - K, 0)` is convex, not concave. This is a fundamental problem I would not catch without careful reading. The covered call *writer's* payoff `min(S_T, K)` is concave. I would likely proceed without noticing the convexity issue.

---

## 4. Mathematical Objects I Would Derive, and in What Order

### Order of derivation:

1. **Reserve curve `x(p)` and `y(p)`** — I would derive these first using `x(p) = -V'(p)` and `y(p) = V(p) + p \cdot x(p)`. Partially correct for the writer's payoff.

2. **Trading function `\psi(x, y)`** — I would attempt to invert the reserve curve to find `\psi`. For the covered call, this requires handling the piecewise nature of `min(S_T, K)`. I would get the form wrong because inverting a piecewise linear function into a two-variable trading function is not straightforward and I would not work through it rigorously.

3. **Invariant condition** — I would state `\psi(x, y) = C` as the invariant and claim it is preserved under swaps. I would not prove it.

4. **Fee structure** — I would bolt on `\phi` as a proportional fee on input and call it done. I would not ask whether the modified trading function `\psi(x(1-\phi)\Delta x, y - \Delta y) = C` still holds, or what the correct fee-adjusted invariant is.

5. **LP share accounting** — I would barely address this. I might write one line saying "LP shares are proportional to reserves" without deriving the correct minting formula for a non-constant-product CFMM.

### Mathematical objects I would NOT derive:

- The closed-form expression for the effective price (spot exchange rate) `p = -\partial\psi/\partial x / \partial\psi/\partial y` verified against `S_T`
- Proof that the LP value function equals the covered call payoff at expiry
- The no-arbitrage condition relating the CFMM price to an external oracle
- Any result about impermanent loss or LP gain from the Bartoletti framework
- The Angeris 2022 oracle-free construction (which handles convex payoffs differently)
- Tick-based concentration of liquidity around `K`

---

## 5. What I Would Get Wrong or Skip

### Wrong: The convexity direction

The most important error. The Angeris 2021 replication theorem applies to **concave** payoffs (which correspond to **convex** trading functions). `max(S_T - K, 0)` is convex, not concave. The LP who holds a covered call position writes the option; their payoff is `min(S_T, K)`, which is concave. I would either:
- Use the wrong payoff function and derive a CFMM that replicates the option buyer's P&L (which cannot be achieved by an LP in a standard CFMM), or
- Silently switch to `min(S_T, K)` without explaining why

Either way, the mathematical object is not what the user asked for, and I would not surface this clearly.

### Wrong: The fee structure derivation

I would use a Uniswap-style proportional fee. For a replicating CFMM, the fee affects whether the replication holds. If fees are not carefully accounted for, the CFMM drifts away from the replication target. The correct approach is to either:
- Define fees as an LP gain that accumulates separately from the reserve invariant, or
- Show that a specific fee structure is compatible with approximate replication within a bounded error

I would do neither. I would write `\phi \in (0, 1)` and call it a "protocol fee parameter" without any derivation.

### Wrong: The invariant as a single scalar

For a covered call CFMM, the "invariant" is not a single constant. The trading function `\psi` is piecewise: it behaves like a constant-numeraire CFMM below `K` and like a constant-risky CFMM above `K`. A single invariant equation does not capture both regimes. I would write a single formula and miss this.

### Skipped: Oracle-free construction

Angeris et al. 2022 ("Replicating Monotone Payoffs Without Oracles") gives a construction that does not require an external price oracle. This is directly relevant to whether the CFMM can work on-chain without oracle manipulation risk. I might mention this paper but would not derive the oracle-free version because it requires understanding the "virtual reserves" construction, which I would not implement correctly under time pressure.

### Skipped: Initialization

I would not specify how the CFMM is initialized. For a replicating CFMM, initialization requires setting reserves `(x_0, y_0)` such that `\psi(x_0, y_0) = C` for a specific `C` that corresponds to an initial spot price `p_0`. I would leave this as "set reserves to initial values" without deriving what those values must be.

### Skipped: Expiry mechanics

A covered call has an expiry `T`. A CFMM is a perpetual mechanism. I would not address how the CFMM handles expiry — whether it allows settlement, what happens to reserves at `T`, whether the CFMM shuts down. This is a core design question the user almost certainly needs answered.

### Skipped: LP position value tracking

I would not derive the LP's marked-to-market value as a function of current spot price. The Bartoletti `gain(Gamma, t)` formula is exactly what the user needs to verify the replication is working, and I would not produce it.

---

## 6. Compatibility with Type-Driven Development Workflow

**Verdict: Not compatible. The output would require a full rewrite to enter the TDD workflow.**

Specific incompatibilities:

### No TLA+ model

I would produce zero TLA+. The CFMM submodule requires `specs/<feature>/model.tla` extending one of the four ToyCLAMM base models before any invariants are written. My output would have no state machine specification, no transition rules, no TLA+ invariants. The entire Phase 1 TLA+ requirement would be absent.

### Wrong notation

I would use ad hoc notation throughout:
- `x` and `y` for reserves (this is consistent with the Angeris papers, so partially correct)
- `K` for strike price (not a paper variable — would collide with `K` from constant-product, which is not a paper variable either but is conventional)
- `phi` for fee rate (consistent with DRAFT.md convention, accidentally correct)
- `V(p)` for payoff (not in the CFMM submodule's Notation Contract — the contract specifies `X`, `Y`, `L_act`, `F_x`, `F_y`, `p`, `i_c`, `i_l`, `i_u`)

The Notation Contract requires paper variables preserved exactly. My derivation uses Angeris paper variables (`x(p)`, `y(p)`, `\psi`) which conflict with the submodule's variables (`X`, `Y` from the FSM paper). This notation collision would need to be resolved before any TDD phases could proceed.

### Informal invariants

The 3-5 invariants I would produce would be:
- Written in prose, not Hoare triple format
- Missing the `| ID | Description | Category | Hoare Triple | Affected | Verification |` table structure
- Fewer than the 19 mandatory CFMM invariants (CFMM-01 through CFMM-19)
- Missing the entire Tier 2 (economic) and Tier 4 (state machine) tiers

### No UDVT types

I would produce LaTeX math, not Solidity types. The TDD Phase 3 requires 8 mandatory dimensional UDVTs (`ReserveX`, `ReserveY`, `Liquidity`, `SqrtPriceX96`, `TickIndex`, `FeeRate`, `FeeAccumX`, `FeeAccumY`) before any implementation. My LaTeX output would not map to any typed representation.

### No Kontrol proof scaffolding

I would produce zero Kontrol proofs. The invariants I write would have no corresponding proof obligations. The Phase 4 one-at-a-time proof requirement would be entirely absent from my output.

### No academic paper citations in specs

I would reference the Angeris papers informally in prose ("as shown in the replication paper...") but would not include formal BibTeX citations or arXiv identifiers in the spec output. The CFMM submodule's Red Flags list explicitly names "No academic paper citations in the spec" as a stop condition.

---

## 7. Would I Produce Proper LaTeX?

**Verdict: Syntactically valid LaTeX. Mathematically incomplete. Wrong document structure for the workflow.**

### What I would get right:

- Proper `\documentclass{article}` with `amsmath`, `amssymb` packages
- Correct use of `align`, `equation`, `cases` environments for piecewise functions
- Properly typeset `\max`, `\min`, `\partial`, `\phi`, `\psi`
- Section headers with `\section{}` and `\subsection{}`
- A `\bibliographystyle{plain}` block that I would fill partially

### What I would get wrong:

- No `\begin{definition}`, `\begin{theorem}`, `\begin{proof}` structure — I would write derivations as numbered equations without formal mathematical structure
- No cross-referencing between files — `trading-function.tex` and `invariants.tex` would be self-contained documents, not a coherent mathematical document
- No `\input{}` or `\include{}` structure — I would not produce a master `.tex` file that assembles the components
- The "invariants" file would not be in Hoare triple notation — it would be informal propositions without precondition/postcondition structure
- Fee structure derivation would be a single equation, not a theorem with proof

### What is completely absent:

- Lean 4 or Coq-style formal proof structure (the submodule explicitly opts out of Lean 4 but the LaTeX should at minimum reference the formalization targets)
- Mapping from LaTeX theorems to Kontrol proof names — there would be no connection between `trading-function.tex` and `prove_cfmm_structural_noDrainSwap`
- TLA+ notation in the LaTeX documents

---

## 8. Honest Gap Summary

| Gap | Severity | Description |
|---|---|---|
| Wrong payoff direction | Critical | Would confuse buyer's `max(S-K,0)` with writer's `min(S,K)`; derive wrong CFMM |
| No convexity check | Critical | `max(S-K,0)` is convex; Angeris 2021 requires concave payoff; wrong framework applied |
| No oracle-free path | High | Would not derive the Angeris 2022 oracle-free construction |
| No TLA+ model | High | Phase 1 Override requires TLA+ before invariants; I would skip entirely |
| Wrong notation | High | My variables conflict with both Angeris paper and FSM paper notation contracts |
| Informal invariants | High | 3-5 prose invariants instead of 19 structured Hoare triples in 4 tiers |
| No UDVT types | High | LaTeX math with no Solidity type derivation |
| No Kontrol proofs | High | Zero proof scaffolding |
| Proportional fee assumed | Medium | Fee not derived from replication framework; may break replication |
| No expiry mechanics | Medium | Covered call requires expiry; CFMM is perpetual; I would not address the tension |
| No initialization derivation | Medium | How to set `(x_0, y_0)` from initial spot price not derived |
| No LP value formula | Medium | Bartoletti `gain(Gamma, t)` not produced; user cannot verify replication is working |
| Informal LaTeX | Low | No theorem/proof structure; no cross-references between files; no master document |
| No paper citations | Low | Informal references, no arXiv IDs in spec output |

**Root cause of most gaps:** Without the skill, I would treat this as a math derivation task, not a type-driven development task. I would produce a document, not a specification. The document would contain some correct mathematics alongside incorrect mathematics, and none of it would be structured to enter the TDD workflow (TLA+, Hoare triples, UDVTs, Kontrol proofs).

**The most dangerous gap** is the convexity error. A CFMM built on the wrong payoff sign would have LPs systematically lose money in the direction the user did not intend. This error is subtle enough to survive code review and only manifest at expiry — exactly the kind of bug that the Bartoletti and FSM paper formalizations exist to prevent.

---

## 9. What the Skill Needs to Add for This Scenario

This baseline test reveals gaps the current cfmm-specification submodule does not yet close:

1. **Replication payoff section** — The submodule covers the Bartoletti and FSM papers (constant-product / concentrated liquidity invariants) but does not explicitly cover the Angeris replication theory. A "Replicating CFMM" subsection should be added to `cfmm-specification.md` that:
   - Requires checking payoff convexity/concavity before proceeding
   - Names the correct paper for replicating CFMMs (Angeris 2021 and 2022)
   - Specifies the reserve derivation procedure `x(p) = -V'(p)`, `y(p) = V(p) + p*x(p)`
   - Specifies the oracle-free vs oracle-assisted choice as a mandatory user question

2. **LaTeX document structure** — The submodule specifies `specs/<feature>/model.tla` but does not specify what LaTeX output should look like when the user requests it. A LaTeX output spec should define: required theorem/proof structure, mapping from LaTeX theorems to Kontrol proof names, required BibTeX citations, and whether a master document is required.

3. **Payoff-specific invariants** — The 19 mandatory invariants (CFMM-01 through CFMM-19) cover structural, economic, rate, and FSM properties of a constant-function market maker. For a *replicating* CFMM, additional mandatory invariants are needed:
   - Replication accuracy at expiry: `V(p_T) = LP_value(p_T)` within tolerance `epsilon`
   - Payoff concavity: the LP's value function is concave in spot price
   - Reserve curve monotonicity: `x(p)` is non-increasing, `y(p)` is non-decreasing
   These would be CFMM-20+ but should be listed explicitly for replicating CFMMs rather than left to the project to discover.

4. **Expiry mechanics question** — The submodule should add a mandatory question for any CFMM feature involving a maturity date: how does the CFMM handle expiry? Options include: settlement, withdrawal only, perpetual rolling. This question must be asked before TLA+ is written, since the state machine is fundamentally different for each choice.
