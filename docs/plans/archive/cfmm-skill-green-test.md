# CFMM Skill Green Test — Covered Call Replicating CFMM

**Date:** 2026-03-02
**Agent persona:** Mama Bear with cfmm-from-payoff skill loaded
**Scenario:** User asks for a complete CFMM replicating a covered call payoff `max(S_T - K, 0)`. Derive trading function, invariants, reserves, fee structure. Output LaTeX in `specs/model/`.
**Purpose:** Document what changes with the skill loaded, compared against the baseline at `docs/plans/cfmm-skill-baseline-test.md`.

---

## 1. What Would Be Different WITH the Skill vs WITHOUT

### Summary verdict

The skill changes the agent's behavior at every phase, from a single-pass document-generation task into a gated, interactive derivation with mandatory checkpoints. The delta is not marginal — it is architectural. The baseline agent produces a plausible-looking but mathematically broken output in one pass. The skill-loaded agent does not produce any output until the user has resolved at least 20 distinct decision points, each of which gates the next derivation step.

### Specific behavioral differences

| Dimension | Baseline (no skill) | With skill |
|---|---|---|
| First action after user message | Immediately begin deriving math | Trigger Question 0a: "Whose perspective is the payoff from?" |
| Convexity check | Missed; proceeds with `max(S-K,0)` as LP payoff | Question 1a forces second-derivative analysis before any derivation |
| Payoff direction | Silent assumption: LP holds buyer's position (wrong) | Question 0a: options 1-4 force explicit acknowledgment of perspective |
| Framework choice | Silently defaults to Angeris 2021 | Question 1c explicitly presents Angeris 2021 vs 2022 tradeoffs |
| Expiry handling | Skipped entirely | Question 1d: three explicit options (fixed expiry, perpetual, rolling) |
| Reserve derivation review | None; agent self-certifies correctness | Question 2a: shows full working, asks "Are these correct?" before proceeding |
| Trading function review | None | Question 3b: shows canonical form with verification checklist |
| Fee structure | Bolted-on proportional fee, no derivation | Questions 4a-4d: derive fee-replication compatibility first |
| Initialization | Left unspecified | Questions 5a-5b: derive `(x_0, y_0)` from chosen initial conditions |
| Invariants | 3-5 prose statements | CFMM-20 through CFMM-25 mandatory Hoare triples + base CFMM-01 through CFMM-19 |
| LaTeX structure | Self-contained files, no master document | Required file set including `main.tex`, `preamble.tex`, `references.bib` |
| LaTeX review | None | Question 7b: per-file review, no batching |
| TDD handoff | No connection to TDD workflow | Phase 8 explicit handoff with mapping table to TDD phases |
| Paper citations | Informal prose references | BibTeX with arXiv IDs mandatory; Geometry paper cited at each geometric claim |
| Total questions asked | 3 (wrong questions, too late) | Minimum 20 (each gates the next phase) |

The most consequential difference: the skill prevents any LaTeX from being written until the payoff direction, convexity, framework, expiry, numeraire, and reserve derivation are all confirmed by the user. The baseline agent writes files before any of those decisions are made.

---

## 2. AskUserQuestion Calls — In Order, With Options

Every question below maps to the skill's Phase structure. Questions are listed in the order they would be triggered for this specific scenario (covered call, `max(S_T - K, 0)`).

### Phase 0 — Payoff Clarification

**Question 0a: Whose payoff?**

```
AskUserQuestion: "Whose perspective is the payoff from?"

Options:
1. LP perspective (the CFMM holder's payoff — typically concave)
2. Trader perspective (the counterparty's payoff — typically convex)
3. I stated the LP payoff directly
4. I'm not sure — help me figure it out
```

Expected answer for a covered call CFMM: option 2 (the user stated the buyer's payoff `max(S-K,0)`, which is the counterparty's). The skill's gate requires confirming this before proceeding.

**Question 0b: Payoff variables**

```
AskUserQuestion: "What are the payoff variables?"

Options (multi-select):
1. S_T = spot price of risky asset at time T
2. S_t = spot price at any time t (path-dependent)
3. Multiple underlying assets (specify)
4. Other variables (describe)
```

Expected answer: option 1. Also confirm what `K` is denominated in (anticipates Question 1g).

**Question 0c: Monotonicity**

```
AskUserQuestion: "Is the LP's payoff monotonically non-decreasing in the price of the risky asset?"

Options:
1. Yes — payoff never decreases as price rises (e.g., covered call writer: min(S,K))
2. No — payoff decreases in some regions (e.g., straddle)
3. I'm not sure — show me the payoff plot regions
```

For a covered call writer `min(S, K)`: answer is option 1 (non-decreasing: increases for `p < K`, flat for `p >= K`). This gates whether Angeris 2022 oracle-free is available.

### Phase 1 — Convexity and Framework Selection

**Question 1a: Convexity verification**

```
AskUserQuestion: "I've analyzed the LP payoff V(p) = min(p, K). Here is the convexity:"

Show:
- V(p) = min(p, K)
- V''(p) = 0 almost everywhere; V has a kink at p = K (concave, not differentiable at K)
- Regions: V is linear (V'' = 0) on (0,K) and constant (V'' = 0) on (K,∞)
- V is concave: for any p1, p2 and λ ∈ [0,1], V(λp1 + (1-λ)p2) ≥ λV(p1) + (1-λ)V(p2) ✓

"Does this match your understanding?"

Options:
1. Yes, proceed with this analysis
2. No, I think the payoff should be [different]
3. Can you explain what concavity means for CFMM replication?
```

This question is where the skill explicitly surfaces the convexity correction — the user stated `max(S-K,0)` (convex, buyer's payoff), the skill converts it to `min(S,K)` (concave, writer's payoff) and asks for confirmation before proceeding.

**Question 1b: Geometry paper object path**

```
AskUserQuestion: "The Geometry paper (arXiv:2308.08066) defines several equivalent CFMM representations. Which object are you starting from?"

Options:
1. Payoff V(p) → derive reserves → derive trading function (replication path)
2. Trading function ψ(x,y) → derive reserves → verify payoff (inverse path)
3. Reserve curves x(p), y(p) → derive trading function → verify payoff
4. Trading set S → derive canonical trading function → derive everything else
```

Expected answer: option 1 (replication path, since the user started from a payoff).

**Question 1c: Framework choice**

```
AskUserQuestion: "Which replication framework should we use?"

Options:
1. Angeris 2021 (oracle-assisted) — requires external price oracle; handles any concave payoff; simpler construction
2. Angeris 2022 (oracle-free) — no oracle needed; only monotone concave payoffs; more complex construction with virtual reserves
3. Help me choose — explain tradeoffs
```

For `min(S, K)` (monotone concave), option 2 is available. The skill presents the choice; the user decides.

**Question 1d: Expiry mechanics**

```
AskUserQuestion: "Does this CFMM have a maturity/expiry?"

Options:
1. Yes — fixed expiry T (e.g., options-like)
2. No — perpetual mechanism (e.g., continuous liquidity provision)
3. Rolling — periodic reset/settlement (e.g., funding rate)
```

This is a mandatory gate. For a covered call, option 1 is the natural answer. If the user picks option 2 or 3, Questions 1e and 1f branch accordingly.

[Note: If option 2 (perpetual) is selected, Question 1e fires next, referencing arXiv:2209.03307 and asking about funding rate model and jump risk. This path is not followed for the covered call scenario which would typically be fixed expiry. If option 1 is selected, Question 1f fires instead.]

**Question 1f: Settlement mechanics (fixed expiry path)**

```
AskUserQuestion: "How should the CFMM handle expiry?"

Options:
1. Settlement — reserves distributed to LPs at T based on final price
2. Withdrawal-only — no new swaps after T, LPs withdraw
3. Rollover — automatically extends to new period
4. I need help deciding
```

**Question 1g: Numeraire and units (two questions)**

```
AskUserQuestion: "What is the unit of account?"

Options:
1. Token Y is the numeraire (prices denominated in Y)
2. Token X is the numeraire
3. External unit (e.g., USD via oracle)
4. Other (specify)
```

```
AskUserQuestion: "What is the strike K denominated in?"

Options:
1. Same as numeraire
2. Different (specify)
```

### Phase 2 — Reserve Derivation Review

**Question 2a: Review reserve derivation**

```
AskUserQuestion: "Here are the derived reserve curves. Please review:"

Show:
- V(p) = min(p, K) (LP payoff, confirmed writer's perspective)
- V'(p) = 1 for p < K; V'(p) = 0 for p ≥ K
- x(p) = -V'(p):
    x(p) = 1  for p < K  (LP holds 1 unit of risky asset below strike)
    x(p) = 0  for p ≥ K  (LP holds 0 risky asset above strike)
- y(p) = V(p) - p·V'(p):
    y(p) = min(p,K) - p·1 = 0  for p < K
    y(p) = K - p·0 = K         for p ≥ K
- Domain: p ∈ (0, ∞)
- Verification: x(p) ≥ 0 ✓; x(p) non-increasing in p ✓; y(p) non-decreasing ✓
- Geometry paper trading set: S = {(x,y) : convex} — verified ✓

"Are these correct?"

Options:
1. Correct — proceed to trading function
2. Something looks wrong at [specific point]
3. Can you verify with a numerical example at price p = [value]?
```

### Phase 3 — Trading Function Review

**Question 3a: Trading function form**

```
AskUserQuestion: "The trading function can be expressed in multiple forms (Geometry paper Section 2):"

Show:
- Parametric: (x(p), y(p)) — already derived
- Implicit: ψ(x, y) = C where ψ(x, y) = x·K + y (derived by eliminating p)
  - For p < K: x = 1, y = 0 → ψ = K·1 + 0 = K
  - For p ≥ K: x = 0, y = K → ψ = K·0 + K = K
  - So ψ(x, y) = K·x + y and the invariant is ψ(x, y) = K
- Canonical form check: ψ is linear (hence concave ✓), 1-homogeneous ✓, nondecreasing in x and y ✓

"Which form do you prefer as the primary specification?"

Options:
1. Canonical form — most general, guaranteed unique by Geometry paper
2. Implicit ψ(x, y) = C — standard in literature
3. Explicit y = f(x) — simpler, if the relationship is invertible
4. Both canonical and explicit
```

**Question 3b: Review trading function**

```
AskUserQuestion: "Here is the derived trading function:"

Show:
- ψ(x, y) = K·x + y
- Invariant: ψ(x, y) = K (normalized to unit liquidity)
- Concavity: ψ is linear, hence concave ✓
- 1-homogeneity: ψ(λx, λy) = K·λx + λy = λ(Kx + y) = λψ(x, y) ✓
- Spot price: p = -∂ψ/∂x / ∂ψ/∂y = -K/1 = K (this is the boundary price — correct for the piecewise CFMM)
- Note: This is a degenerate (piecewise constant) CFMM — infinite slippage at p ≠ K; the effective price is K, not a smooth curve

"Does this look correct?"

Options:
1. Correct — proceed to fees
2. The price formula doesn't match — let me check
3. Can you verify at a boundary (e.g., p = K)?
```

### Phase 4 — Fee Structure

**Question 4a: Fee approach**

```
AskUserQuestion: "How should fees interact with the replication property?"

Options:
1. Replication-preserving — fees accrue separately, do not affect the reserve invariant (Bartoletti gain formula applies)
2. Replication-approximate — fees modify reserves, replication holds within bounded error ε
3. Project convention — use φ = 4·max(gasCost) from DraftLiquiditySupplySimplestModel
4. Help me understand the tradeoffs
```

**Question 4b: Fee accumulation**

```
AskUserQuestion: "How should fees accumulate?"

Options:
1. Per-swap fee on input token (standard: Δx_effective = (1-φ)·Δx)
2. Per-swap fee on output token
3. Time-weighted fee (accrues with time, not volume)
4. Dynamic fee from hook
```

**Question 4d: Review fee structure**

```
AskUserQuestion: "Here is the fee-adjusted specification:"

Show:
- Fee model: per-swap on input, φ ∈ (0, 1)
- Modified swap: Δx_effective = (1-φ)·Δx_in
- Replication error: fees cause reserves to accumulate above the invariant curve; error bounded by ε = φ·Volume
- Compatibility with Bartoletti gain(Γ,t): yes, if fees tracked separately in F_x, F_y per notation contract

"Is this acceptable?"

Options:
1. Yes — proceed to initialization
2. The error bound is too large
3. I want a different fee model
```

### Phase 5 — Initialization

**Question 5a: Initial conditions**

```
AskUserQuestion: "How should the CFMM be initialized?"

Options:
1. From initial spot price p₀ — derive (x₀, y₀) such that ψ(x₀, y₀) = K and price = p₀
2. From initial reserves (x₀, y₀) — derive C and initial price
3. From initial liquidity L₀ and price p₀
```

**Question 5b: Review initialization**

```
AskUserQuestion: "Initialization specification:"

Show:
- Given: initial spot price p₀
- If p₀ < K: (x₀, y₀) = (1, 0) — LP holds 1 risky, 0 numeraire
- If p₀ = K: (x₀, y₀) anywhere on the invariant curve (indeterminate — user decides)
- If p₀ > K: (x₀, y₀) = (0, K) — LP holds 0 risky, K numeraire
- Invariant constant: C = K (for unit liquidity)
- LP value at init: V(p₀) = min(p₀, K) ✓

"Does this match your expectations?"

Options:
1. Correct — proceed to invariants
2. The initial LP value should be [different]
3. Can you show a numerical example?
```

### Phase 6 — Invariants

**Question 6a: Additional invariants**

```
AskUserQuestion: "Here are the mandatory replication invariants (CFMM-20 through CFMM-25). Do you need additional feature-specific invariants?"

Show table:
CFMM-20: Replication accuracy — {V(p)} → evolve(p→p') → {|LP_value(p') - V(p')| ≤ ε}
CFMM-21: LP payoff concavity — {p₁ < p₂ < p₃} → {V(p₂) ≥ λ·V(p₁) + (1-λ)·V(p₃)}
CFMM-22: Reserve monotonicity — {p' > p} → {x(p') ≤ x(p) ∧ y(p') ≥ y(p)}
CFMM-23: Boundary reserves — {p→0} → {x→1 ∧ y→0} and {p→∞} → {x→0 ∧ y→K}
CFMM-24: Price-reserve consistency — {p = K} → {x, y on invariant curve ψ = K}
CFMM-25: Canonical form uniqueness — ψ = Kx + y is nondecreasing, concave, 1-homogeneous

Options:
1. These are sufficient
2. Add invariant for [specific property]
3. I need an invariant for the expiry/settlement behavior
4. I need an invariant for the fee-replication interaction
```

**Question 6b: Review all invariants**

Presents the complete set (CFMM-01 through CFMM-19 from base + CFMM-20 through CFMM-25 from replication) for final confirmation before LaTeX is written.

### Phase 7 — LaTeX

**Question 7a: Review LaTeX structure**

```
AskUserQuestion: "Here is the planned LaTeX structure. Review before I write files:"

File list:
- specs/model/main.tex — master document
- specs/model/preamble.tex — shared packages, theorem environments, notation macros
- specs/model/payoff.tex — V(p) = min(p,K), convexity proof, buyer-vs-writer distinction
- specs/model/reserves.tex — x(p), y(p) derivation via Geometry paper path
- specs/model/trading-function.tex — ψ(x,y) = Kx + y, canonical form verification
- specs/model/fees.tex — fee model, replication compatibility theorem
- specs/model/initialization.tex — (x₀, y₀) derivation from p₀
- specs/model/invariants.tex — CFMM-01 to CFMM-25 in Hoare triple format
- specs/model/references.bib — arXiv:2308.08066, 2103.14769, 2111.13740, 2209.03307, 2003.10001

Notation table:
- X, Y, L_act, F_x, F_y, p, φ — from cfmm-specification (preserved)
- V(p) — LP payoff; ψ(x,y) — trading function; S — trading set
- \mathcal{K} — strike parameter (avoids collision)
- ϕ (varphi) — Angeris paper's pricing function; φ (phi) — fee rate

Options:
1. Approved — write the files
2. Change notation for [specific variable]
3. Add/remove a file
4. Change the document structure
```

**Questions 7b (×9): Per-file review**

One question per file, in order: `preamble.tex`, `payoff.tex`, `reserves.tex`, `trading-function.tex`, `fees.tex`, `initialization.tex`, `invariants.tex`, `references.bib`, `main.tex`.

Each in the form:
```
AskUserQuestion: "I've written [filename]. Review before continuing?"
Options:
1. Approved — continue to next file
2. Changes needed: [describe]
```

### Phase 8 — Handoff

**Question 8: TDD handoff**

```
AskUserQuestion: "Mathematical specification complete. Ready to begin type-driven development?"

Options:
1. Yes — invoke type-driven-development skill
2. Not yet — I want to review the full specification first
3. I need to modify [specific part] before proceeding
```

### Total question count

Phase 0: 3 questions
Phase 1: 6 questions (fixed expiry path; +2 for perpetual path)
Phase 2: 1 question
Phase 3: 2 questions
Phase 4: 3 questions (non-perpetual)
Phase 5: 2 questions
Phase 6: 2 questions
Phase 7: 1 structure review + 9 per-file reviews = 10 questions
Phase 8: 1 question

**Total: 30 questions for this specific scenario (fixed expiry, non-perpetual covered call)**

---

## 3. Would the Skill Catch the Convexity Error?

**Yes. The skill catches it at Question 0a, and again at Question 1a. The baseline agent does not catch it at all.**

### How the skill prevents the error

The covered call buyer's payoff `max(S_T - K, 0)` is convex. The Angeris 2021 replication theorem applies only to concave payoffs. Using the buyer's payoff directly in `x(p) = -V'(p)` produces `x(p) = -1` above the strike — negative reserves, which is nonsensical for a CFMM.

The baseline agent hits this exact problem (documented in baseline Section 2, Step 2) and handles it by flipping the sign without justification.

The skill stops the derivation before it starts:

**Gate 1 — Question 0a** asks "Whose perspective is the payoff from?" with explicit options including "Trader perspective (the counterparty's payoff — typically convex)." The user giving `max(S-K,0)` is almost certainly giving the trader's (buyer's) perspective. The skill's note in Phase 0 states:

> "If the user gives a convex payoff like max(S-K, 0), the LP's payoff is the WRITER's position min(S, K). Getting this wrong produces a CFMM where LPs systematically lose money in the wrong direction. This error is subtle enough to survive code review."

The Red Flags section also lists "The payoff direction is obvious" as a rationalization to stop and refuse, with the exact covered call example:

> "Covered call: max(S-K,0) is buyer's (convex). LP holds writer's min(S,K) (concave). This error survives code review."

**Gate 2 — Question 1a** presents the LP payoff with second-derivative analysis and asks the user to confirm before any derivation proceeds. By the time Question 1a fires, the agent has already converted the user's stated payoff to the writer's `V(p) = min(p, K)`, shown the concavity analysis, and asked the user to confirm it. A user who expected the buyer's construction would catch the conversion here.

### What the baseline does instead

The baseline agent reaches `x(p) = -V'(p)` with `V(p) = max(p-K, 0)`, computes `V'(p) = 1` for `p > K`, gets `x(p) = -1` (negative reserves), recognizes the sign issue, and silently flips it "without rigorous justification" (baseline Section 2, Step 2). The mathematical error survives because no one checks it: there is no review gate, no explicit acknowledgment of the payoff direction conversion, and no note explaining why the LP holds `min(S,K)` rather than `max(S-K,0)`.

The skill forces this acknowledgment at two gates before any derivation is attempted.

---

## 4. Would the Geometry Paper Be Referenced?

**Yes, at every derivation step that touches CFMM object relationships. The skill treats it as non-negotiable.**

The skill's Overview states: "The Geometry paper (Angeris et al. 2023) establishes that every CFMM has a canonical trading function ... This skill uses those relationships to derive a complete CFMM from any starting object." The paper is listed as a Foundation Paper marked "(non-negotiable)."

Specific points where arXiv:2308.08066 would be cited:

| Location | Specific claim | Geometry paper section |
|---|---|---|
| Question 1b (object path selection) | "Several equivalent CFMM representations" | Section 2 |
| Phase 2 reserve derivation | `x(p) = -V'(p)` derivation path | Section 3 |
| Phase 2 reserve derivation | Trading set `S = {(x,y) : y ≥ V*(x)}` is convex | Axiom (def of trading set) |
| Phase 3 trading function | Canonical trading function exists and is unique, nondecreasing, concave, 1-homogeneous | Theorem 1 |
| Phase 3 trading function | `ψ(λx, λy) = λψ(x,y)` — 1-homogeneity | Proposition 3 |
| Phase 3 Question 3b | `p = -∂ψ/∂x / ∂ψ/∂y` (spot price from trading function) | Section 3 |
| Phase 6 invariant CFMM-22 | Reserve monotonicity follows from concavity of canonical trading function | Concavity result |
| Phase 6 invariant CFMM-24 | Price-reserve consistency | Section 3 |
| Phase 6 invariant CFMM-25 | Canonical form uniqueness | Theorem 1 |
| LaTeX `references.bib` | BibTeX entry with arXiv:2308.08066 | — |
| LaTeX `trading-function.tex` | `% Kontrol: prove_cfmm_structural_<name>` mapped to Geometry paper theorems | — |

The Replicating Market Makers paper (arXiv:2103.14769) and Oracle-Free paper (arXiv:2111.13740) would also be cited. The Geometry paper is the backbone because it provides the uniqueness guarantee for the canonical trading function — without it, the derived `ψ(x, y) = Kx + y` has no proof of being the unique canonical form.

The baseline agent references the Angeris papers "informally in prose" (baseline Section 6) without BibTeX or arXiv identifiers.

---

## 5. Would the Output Have Proper LaTeX Structure?

**Yes. The skill mandates theorem/proof structure, BibTeX, per-file review, and Kontrol proof name mapping.**

### What the skill-loaded agent produces

**`preamble.tex`** — Contains `\newtheorem{theorem}{Theorem}`, `\newtheorem{definition}{Definition}`, `\newtheorem{invariant}{Invariant}` environments. Contains notation macros: `\newcommand{\Vpayoff}{V(p)}`, `\newcommand{\tradingfn}{\psi}`, `\newcommand{\strike}{\mathcal{K}}`.

**`payoff.tex`** — Contains:
```latex
\begin{definition}[Covered Call LP Payoff]
Let $p \in (0, \infty)$ denote the spot price of the risky asset. The LP payoff is the covered call writer's position:
$$V(p) = \min(p, \mathcal{K})$$
where $\mathcal{K} > 0$ is the strike price.
\end{definition}

\begin{theorem}[LP Payoff Concavity]
$V(p) = \min(p, \mathcal{K})$ is concave.
\end{theorem}
\begin{proof}
For $p_1, p_2 > 0$ and $\lambda \in [0,1]$:
$\min(\lambda p_1 + (1-\lambda) p_2, \mathcal{K}) \geq \lambda \min(p_1, \mathcal{K}) + (1-\lambda) \min(p_2, \mathcal{K})$
by the concavity of the minimum function. \qed
\end{proof}
% Kontrol: prove_cfmm_economic_payoffConcavity
```

**`trading-function.tex`** — Derives `ψ(x, y) = Kx + y` with canonical form verification, citing Geometry paper Theorem 1. Each theorem maps to a Kontrol proof name in a comment.

**`invariants.tex`** — Contains `\begin{invariant}` environments with Hoare triple format:
```latex
\begin{invariant}[CFMM-20: Replication Accuracy]
$$\{V(p)\} \; \text{evolve}(p \to p') \; \{|LP\_value(p') - V(p')| \leq \varepsilon\}$$
\textit{Source: Angeris et al. 2021 \cite{angeris2021replicating}, Proposition 1}
\end{invariant}
```

**`references.bib`** — Contains entries for all five papers with arXiv IDs:
```bibtex
@misc{angeris2023geometry,
  title={The Geometry of Constant Function Market Makers},
  author={Angeris, Guillermo and Chitra, Tarun and Diamandis, Theo and Evans, Alex and Kulkarni, Kshitij},
  year={2023},
  eprint={2308.08066},
  archivePrefix={arXiv}
}
```

**What is absent in the baseline:** No `\begin{theorem}` or `\begin{proof}` structure (baseline Section 7: "I would write derivations as numbered equations without formal mathematical structure"). No `\begin{invariant}` environments. No Kontrol proof name mapping. No `references.bib`. No `main.tex` assembling components.

---

## 6. Would the Output Feed Into Type-Driven Development?

**Yes, directly. The skill explicitly maps its outputs to TDD skill phases.**

The skill's Phase 8 contains an explicit mapping table:

| Skill output | TDD skill phase |
|---|---|
| `specs/model/*.tex` | TDD Phase 1 input (Spec Kit) |
| CFMM-01 through CFMM-25+ (Hoare triples) | TDD Phase 2 (invariant definitions) |
| Notation contract | TDD Phase 3 (UDVT naming) |

### Invariant format compatibility

The skill outputs invariants in Hoare triple format matching the cfmm-specification submodule's required table structure:

```
| CFMM-20 | Replication accuracy | {V(p)} → evolve(p→p') → {|LP_value(p') - V(p')| ≤ ε} | Angeris 2021 Prop. 1 |
```

These are in the exact format TDD Phase 2 requires for writing Kontrol proofs.

### Notation contract continuity

The skill's Notation Contract section explicitly preserves the cfmm-specification submodule's variables (`X`, `Y`, `L_act`, `F_x`, `F_y`, `p`, `i_c`, `i_l`, `i_u`, `φ`) and resolves the collision between Angeris's `φ` (pricing function) and the project's `φ` (fee rate) by mapping the Angeris variable to `ϕ` (varphi). This prevents the notation collision the baseline would create (baseline Section 6: "My derivation uses Angeris paper variables that conflict with the submodule's variables").

### UDVT mapping

The skill's Phase 8 states: "Notation contract → TDD Phase 3 (UDVT naming: `V(p)` maps to value types, `x(p)` to ReserveX, etc.)." The `ReserveX`, `ReserveY`, `Liquidity` UDVTs expected by TDD Phase 3 map directly to `x(p)`, `y(p)`, and `L` from the skill's reserve derivation.

### What the baseline produces instead

The baseline outputs informal invariants in prose (baseline Section 6: "3-5 prose invariants instead of 19 structured Hoare triples in 4 tiers"), no UDVT mapping, no TLA+ model, and no Kontrol proof scaffolding. The baseline document "would require a full rewrite to enter the TDD workflow" (baseline Section 6).

---

## 7. Gaps Remaining — What the Skill Does Not Address

Despite the substantial improvement over the baseline, the skill has genuine gaps that would still cause problems in the covered call scenario.

### Gap 1: The degenerate trading function problem

For `V(p) = min(p, K)`, the derived trading function is `ψ(x, y) = Kx + y` — a linear function. A linear trading function means infinite slippage at any price other than `K`. The CFMM is degenerate: it only executes at exactly one price. The skill does not flag this or ask whether the user wants a concentrated-liquidity variant (e.g., liquidity in a tick range around `K`). The user would receive a mathematically correct but practically unusable CFMM without this being flagged.

### Gap 2: The piecewise regime boundary

The covered call CFMM has two regimes: below strike (LP holds risky asset, slope = 1) and above strike (LP holds numeraire, slope = 0). The skill's trading function derivation in Phase 3 does not explicitly handle piecewise derivations — it derives a single canonical form, which for this payoff is linear. The piecewise nature of the reserve curves (which is the actual behavior of the CFMM) is not surfaced as a question or flagged as a regime-switching property.

### Gap 3: Liquidity scaling not addressed

The skill derives reserves for unit liquidity (`ψ = K`). It does not ask how liquidity is scaled when multiple LPs provide different amounts, or how the invariant `C` changes with liquidity additions/removals. The TDD workflow requires `L_act` (active liquidity), but the skill's output does not specify how `C` relates to `L_act` for this specific CFMM.

### Gap 4: The oracle-free virtual reserve construction is not derived

When the user selects Angeris 2022 (oracle-free) in Question 1c, the skill asks the question but does not provide the derivation procedure for the virtual reserve technique. The oracle-free construction for `min(S, K)` requires deriving virtual reserves `(x̃, ỹ)` that embed the oracle price implicitly. The skill presents this as a framework choice but does not have a Phase-2-equivalent for the oracle-free path — it would fall back to the oracle-assisted derivation procedure regardless.

### Gap 5: BibTeX file content not validated

The skill mandates a `references.bib` with BibTeX entries including arXiv IDs. It asks for per-file review (Question 7b), but does not specify the exact BibTeX entry format or validate that arXiv IDs are correct. An agent could write a syntactically valid `references.bib` with wrong paper titles or incorrect arXiv IDs (e.g., transposing digits in 2308.08066), and the per-file review question would not catch this unless the user manually verifies the IDs.

### Gap 6: Settlement/expiry mechanics not mathematically derived

Phase 1d asks about expiry mechanics (settlement, withdrawal-only, rollover), but Phase 5 (initialization) does not have a corresponding Phase for expiry derivation. There is no mandatory gate requiring derivation of what happens to reserves at `T`. For a covered call, the settlement condition `LP_value(p_T) = min(p_T, K)` should be a theorem with proof, but the skill has no explicit phase for post-expiry state machine transitions.

### Gap 7: No TLA+ integration path

The skill's Phase 8 says TDD Phase 1 uses `specs/model/*.tex` as input. But TDD Phase 1 also requires a TLA+ model (`specs/<feature>/model.tla`). The cfmm-from-payoff skill produces LaTeX only. There is no phase that produces or scaffolds the TLA+ model. The handoff to TDD in Phase 8 would require TDD Phase 1 to be started from scratch — the skill does not reduce the TLA+ work.

### Gap 8: Strike price as state variable not addressed

The skill treats `K` as a constant parameter (in the notation contract, `\mathcal{K}` is "payoff parameter"). For a rolling CFMM or a perpetual that needs to update its strike, `K` must be a state variable. The skill has no question about whether `K` is fixed or mutable, and no invariant covering strike update safety.

---

## 8. New Rationalizations — Loopholes That Remain

Despite the Iron Law ("NO DERIVATION STEP WITHOUT AN ASKUSERQUESTION FIRST"), a skilled-but-lazy agent could still find ways to bypass the skill's intent.

### Loophole 1: Answering own questions

The skill requires AskUserQuestion calls but does not prevent the agent from suggesting a "default" answer that the user is likely to accept without scrutiny. For example, Question 1c asks the user to choose between Angeris 2021 and 2022. An agent could frame the question as:

> "For a monotone concave payoff, Angeris 2022 is generally preferred. Shall I proceed with that?"

This is technically a question, but it pre-selects the answer and reduces the decision to a confirmation. The user approves without engaging with the tradeoffs. The spirit of the Interactive Derivation Law is violated; the letter is satisfied.

### Loophole 2: Phase 0 confirmation without conversion

Question 0a asks "Whose perspective?" and the user answers "LP perspective" (option 3: "I stated the LP payoff directly"). An agent could then proceed with `max(S-K,0)` as the LP payoff without performing the convexity check, treating the user's confirmation as settling the question. Question 1a would then present `max(S-K,0)` as the LP payoff, compute `V''(p) = 0` almost everywhere (convex conjugate confusion), and derive `x(p) = -1` for `p > K`. The convexity gate at Question 1a is the last defense here — but if the agent shows `max(S-K,0)` instead of converting to `min(S,K)`, the user may not catch it.

### Loophole 3: Batching questions across phases

The skill mandates per-question sequencing. An agent could combine questions from different phases into one message ("Here are Questions 0a, 0b, 0c, 1a, 1b — please answer all five"). The user answers in one response, and the agent treats all gates as cleared simultaneously. This defeats the purpose of the gate-by-gate structure, since errors in early questions no longer block later phases.

### Loophole 4: Treating LaTeX review as rubber stamp

Question 7b asks for per-file review: "I've written [filename]. Review before continuing?" with option 1 being "Approved — continue." An agent could write all files first (violating the "no batching LaTeX files" rule), then send Question 7b for each file in rapid succession, creating the appearance of sequential review while the user is effectively reviewing a complete pre-written document. The skill says "No batching LaTeX files. One file, one review, then next" but does not prevent the agent from writing future files before receiving approval on the current one.

### Loophole 5: Fee compatibility claimed without proof

Question 4a asks about fee-replication compatibility and Question 4d asks the agent to show the "replication error bound." An agent could write "Replication error: bounded by ε = φ·Volume" without deriving this bound. The user sees a formula but the derivation is asserted, not proven. The skill requires showing the fee-adjusted invariant and verifying replication still holds, but "showing" could be satisfied by displaying the formula without the proof. The per-file LaTeX review (Question 7b for `fees.tex`) is the last gate, but a theorem with a vacuous `\begin{proof} [Direct calculation.] \qed \end{proof}` would technically satisfy the structure requirement.

### Loophole 6: Notation contract as "approximately preserved"

The skill's Notation Contract requires preserving cfmm-specification variables exactly. An agent could use `x` and `y` for reserves (consistent with Angeris papers) and claim this is "consistent with cfmm-specification" even though the submodule uses `X` and `Y` (capital). The Question 7a structure review asks the user to approve the notation table, but a user unfamiliar with the submodule's exact casing would not catch the collision. The skill does not prevent lowercase/uppercase ambiguity.

### Loophole 7: CFMM-01 through CFMM-19 cited but not reproduced

The skill says Question 6b presents "all invariants (CFMM-01 through CFMM-19 from base + CFMM-20+ from this derivation)." An agent could cite the base invariants by reference ("see cfmm-specification.md CFMM-01 through CFMM-19") without reproducing them in the `invariants.tex` file. The user approves the invariants, but the output document is incomplete — it requires loading the submodule to interpret the invariant set. The TDD Phase 2 would then require importing the submodule's notation rather than having a self-contained spec.

---

## Summary

| Question | Verdict |
|---|---|
| 1. Different behavior with skill? | Fundamentally different — 30 mandatory gates vs 3 wrong questions; no files written before user confirms payoff direction, convexity, framework, expiry, numeraire, reserves, trading function, fees, initialization, invariants, and LaTeX structure |
| 2. AskUserQuestion calls? | 30 for this scenario (fixed expiry, non-perpetual covered call) |
| 3. Catch convexity error? | Yes — at Question 0a and confirmed at Question 1a; explicit note in Phase 0 names this exact error |
| 4. Reference Geometry paper? | Yes — at every CFMM object derivation step, with BibTeX arXiv:2308.08066 mandatory |
| 5. Proper LaTeX? | Yes — theorem/proof structure, \begin{invariant} Hoare triples, BibTeX, Kontrol proof name comments, master document |
| 6. Feed into TDD? | Yes — explicit Phase 8 mapping table; notation contract continuity; CFMM-01 through CFMM-25 in Hoare triple format |
| 7. Gaps remaining? | 8 identified: degenerate trading function, piecewise regime handling, liquidity scaling, oracle-free derivation missing, BibTeX not validated, expiry mechanics not derived, no TLA+ integration, strike as state variable |
| 8. Loopholes? | 7 identified: leading questions, premature confirmation at Q0a, phase batching, LaTeX pre-writing, fee bound assertion without proof, notation casing ambiguity, base invariants cited by reference |
