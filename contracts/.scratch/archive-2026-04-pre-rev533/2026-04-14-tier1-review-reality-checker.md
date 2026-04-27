# Reality Checker Review — Tier 1 Inflation-Mirror Feasibility Filter

**Spec reviewed:** `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md`
**Reviewer:** Reality Checker
**Date:** 2026-04-14

## OVERALL VERDICT: NEEDS WORK

Scope fences are clean, verdict taxonomy is concrete, deliverable path is pre-committed. But the plan rests on three load-bearing assumptions that are either unjustified or under-specified, and the success criterion is gameable in a way that makes a `GAP` verdict the path of least resistance.

Three concrete problems must be fixed before execution:

1. The FX-vol vs CPI-surprise literature prior is treated as ~50/50 in prose but the specific four-control regression being hunted has realistically sub-20% odds of being published as specified. The spec must pre-commit to proxy-stretch tolerance or the verdict collapses into searcher discretion.
2. "Liquidity sufficient for the RAN to be constructed" is never operationalized — the single most important gate for `CONFIRMED_WITH_X` is a qualitative judgment call.
3. The cCOP-side bottleneck self-refutation is never wired into verdict rules. A `CONFIRMED_WITH_X=USDC` can fire and still be useless if the cCOP side is $7K/day.

## 1. §1 LVR claim load-bearing? — FLAG

Tier 1 does not consume $g^{\text{pool}}$ or the LVR identity. Context only. Risk: retroactive sunk-cost framing if notebook derivation has a flaw surfacing in Tier 2.

**Fix:** One sentence in §1 or §2 stating Tier 1 does not depend on the LVR identity's correctness, and that independent review of the notebook derivation is a separate Tier 2 prerequisite.

## 2. §2 FX-vol vs CPI-surprise prior — BLOCK

Honest probabilities for finding a Tier A match (weekly realized vol of COP/USD on DANE surprise with 3-of-4 controls):
- P(exact match published): < 5%
- P(close-enough proxy for COP): ~20-30%
- P(basket-level EM paper covers COP as part of a panel): ~40-50%
- P(announcement-effect FX-vol literature includes LatAm CPI-surprise): ~30%

"Sufficiently close proxy" is never defined. Searcher decides stretch during execution, and that decision dominates the verdict.

**Fix: pre-register proxy-closeness hierarchy:**
- Tier A: COP realized vol, DANE surprise, 3-of-4 controls.
- Tier B: COP realized vol, Colombian CPI surprise (any construction), any controls.
- Tier C: LatAm panel with Colombia-specific coefficient reported.
- Tier D: Same four-control framework on non-COP EM currency (MXN, BRL, CLP) sharing Colombia-relevant macro structure.
- Further than Tier D = NOT STUDIED.

§9 verdicts must cite which tier supports them. Downgrade §2's prior from "may already be established" to "P < 30% of finding a Tier A hit; exercise is primarily to distinguish Tier B-D hits from true gaps."

## 3. §3 q3 "liquidity sufficient" undefined — BLOCK

Load-bearing gate for `CONFIRMED_WITH_X` vs `CONFIRMED_WITHOUT_X`. No operational definition.

**Fix: add §8a "Usable-today definition" with numeric thresholds:**
- Pool on EVM-compatible chain with public RPC
- Concentrated-liquidity $L$ and per-tick $g^{\text{pool}}(i)$ computable from canonical pool state
- 30-day avg daily notional ≥ [pick threshold]
- 1% slippage budget supports ≥ [pick trade size]
- Check/triangle/X legend bound to these thresholds, not qualitative

## 4. §7 signal-strength realistic in one day? — FLAG

Realistic distribution: 5-of-7 NOT STUDIED, 2-of-7 marginal. `GAP` or `MIXED` is statistically-dominant outcome.

**Fix:** Add to §9: "Given the narrowness of the hypothesis specification, the prior on `GAP` or `MIXED` is high. Output is primarily to distinguish `GAP` (justifying Tier 1b) from `CONFIRMED_*` (justifying Tier 2). A `GAP` verdict is not a failure; it is a successful gate."

## 5. §8 2026-04-02 availability stale? — FLAG

12 days old for on-chain liquidity is borderline. §13 says "None" for dependencies — contradicts §8's reliance on the 2026-04-02 package.

**Fix:**
1. §13 must list the 2026-04-02 package as a prerequisite.
2. §8 must say: "If the 2026-04-02 cCOP research cannot be located, accessed, or verified structurally current, Tier 1 is blocked pending re-audit (out of Tier 1 scope — separate sibling spec)."
3. Promote staleness from §16 footnote to first-class risk.

## 6. §14 "Approximately one day" underestimate? — FLAG

Realistic decomposition: 12-20 hours (two to three days honest).

**Fix:** "Approximately one day if literature is sparse (most rows NOT STUDIED quickly); two to three days if regional panels turn up partial hits requiring full-text review."

## 7. §15 success criterion gameable? — BLOCK

"Documented reason skipped" is a trap door. Every query can be "skipped, documented as low-prior" and criterion satisfied.

**Fix:**
- "At least N=5 distinct citations in the findings table, or verdict must explicitly be `GAP` with exhaustive-search failure documented."
- "Skipping a source requires naming it in the deliverable; verdict is downgraded one tier if fewer than 3-of-4 sources were queried."
- "arxiv is the only source pre-authorized to skip without penalty; other three must be queried unless a hard block (paywall/outage) is documented with timestamp."

## 8. §9 verdicts — where do strong-negative results go? — BLOCK

Missing `DISCONFIRMED`: one or more credible papers with specification close to operational gate report $\beta_{\text{CPI}} \approx 0$ or adj-R² < 0.05 with tight CIs. The strongest possible filter finding — the thesis is dead.

Currently a `DISCONFIRMED` outcome mis-classifies as `GAP` and spawns Tier 1b — exactly the wrong next step.

**Fix: add to §9:**
- `DISCONFIRMED` — At least one credible study with specification close to operational gate reports $\beta_{\text{CPI}}$ insignificant or adj-R² below 0.05 with tight CIs. Decision: abandon COP/X inflation-hedge thesis at the economic layer; do not proceed to Tier 1b on the same hypothesis.

Wire into §11: `DISCONFIRMED` → no Tier 2, no Tier 1b; hypothesis retired.

## 9. cCOP self-refutation — BLOCK

§2 line 23 establishes cCOP peaks ~$7K/day. §9 treats X as the binding constraint. But the pair is cCOP/X. If cCOP is $7K/day and X is USDC at $1B/day, effective liquidity is bounded by the thin side.

`CONFIRMED_WITH_X=USDC` would fire (USDC is usable) while the RAN remains unbuildable because the cCOP leg can't support the underlying read at scale.

**Fix: make §3 q3 symmetric:**
> "Does a tokenized on-chain counterparty exist for the literature-favored pair, **and does the cCOP side support sufficient liquidity for joint observability of $g^{\text{pool}}$**, such that the RAN can be constructed against it today?"

And add verdict `CONFIRMED_BUT_cCOP_BLOCKED` (behaviorally matching `CONFIRMED_WITHOUT_X`).

## 10. Other smells

- **10a NIT:** §1's $\phi^2 V(P)/(8L)$ shorthand not cited to notebook cell.
- **10b NIT:** §5 source ordering forces Spanish-first, maximizing wasted work if BanRep turns up nothing. Re-order NBER+SSRN → BanRep → IMF → Scholar → arxiv.
- **10c NIT:** §10 deliverable §§6 and 7 could collapse into "Verdict and gap analysis" to force reconciliation.
- **10d NIT:** §15 bullet 4 "four categories" conflicts with new `DISCONFIRMED`.
- **10e FLAG:** Deliverable has no review pipeline — single-person literature search without sanity-check on "close enough" is exactly where `CONFIRMED_WITH_X` gets stretched. Add second-reader review.
- **10f NIT:** τ=0.15 (Tier 2) vs τ=0.10 (Tier 1) creates provisional-confirm case. Tier 2 must re-verify a marginal `CONFIRMED_WITH_X` at adj-R²=0.11.

## Summary of required changes (priority order)

| # | Issue | Severity | Where |
|---|-------|----------|-------|
| 3 | Operationalize "liquidity sufficient for RAN" with numeric thresholds | BLOCK | §3 q3, §8, new §8a |
| 9 | cCOP-side self-refutation must gate verdict | BLOCK | §3 q3, §9 |
| 8 | Add `DISCONFIRMED` verdict for strong-negative literature | BLOCK | §9, §11, §15 |
| 7 | Tighten §15 beyond "documented skip" checklist | BLOCK | §15 |
| 2 | Pre-register proxy-closeness tiers (A/B/C/D) | BLOCK | §3 q1, §9 |
| 5 | Promote 2026-04-02 data to §13 dependency | FLAG | §13, §8, §16 |
| 6 | Revise time estimate to 1-3 days | FLAG | §14 |
| 4 | Acknowledge high prior on `GAP`/`MIXED` | FLAG | §9 |
| 1 | Clarify Tier 1 doesn't depend on LVR identity | FLAG | §1 or §2 |
| 10e | Add second-reader review of deliverable | FLAG | §15 |
| 10b | Re-order §5 priority: NBER→BanRep→IMF | NIT | §5 |
| 10f | Flag τ=0.10 (Tier 1) < τ=0.15 (Tier 2) | NIT | §10 |
| 10a | Cite notebook cell for φ²V(P)/(8L) | NIT | §1 |
| 10c | Collapse deliverable §§6-7 | NIT | §10 |
| 10d | Update §15 for 5 verdicts | NIT | §15 |

## Bottom line

Five BLOCKs — all in verdict-generation logic, not the search procedure — mean the feasibility filter doesn't currently filter anything load-bearing. Without operational thresholds, proxy-tier pre-registration, `DISCONFIRMED` verdict, cCOP-side gate, and tightened success criterion, execution will produce a document that *looks* like a verdict but is actually a restatement of the searcher's priors.

Fix the five BLOCKs, address the four FLAGs, and this is ready to execute. Without them, `CONFIRMED_WITH_X=USDC` is a specific foreseeable failure mode where the verdict fires on a pair that cannot actually support the RAN.

Re-review required after fixes.
