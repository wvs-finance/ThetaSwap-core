# Code Reviewer — Tier 1 Feasibility Spec Review

**Spec:** `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md`
**Reviewer role:** Code Reviewer (logical/structural/methodological soundness)
**Date:** 2026-04-14

## OVERALL: APPROVE_WITH_CHANGES

The spec is well-structured, code-agnostic, and honors the memory constraints (no code, read-only on Angstrom and prior research). The literature-first pivot is justified by the infrastructure-check finding. However, the verdict decision procedure has ambiguous boundaries, the τ-gap (0.15 vs 0.10) is stated but not defended, and the Tier 2 handoff leaks assumptions Tier 1 does not produce. Six FLAGs and six NITs below. None are blocking once resolved.

## Findings

### 1. Verdict rules are not mutually exclusive — FLAG
**§9, lines 100–105.** The four verdicts do not partition the input space:
- A paper with `adj-R² ≥ 0.10` on COP/EUR plus EUR wrapper marked `△` (§8 row 2) satisfies both `CONFIRMED_WITH_X` and `CONFIRMED_WITHOUT_X`. §8 is ternary (`✓`/`△`/`✗`) but §9 reads it as binary.
- `MIXED` ("partial literature support", line 105) overlaps `GAP` under strict reading of "no literature meets the threshold for *this* specification."
- Strong literature on COP/USD with no usable USD wrapper is ambiguous between `CONFIRMED_WITHOUT_X` and `MIXED`.

**Fix:** Explicit decision tree with precedence:
1. IF any row has `adj-R² ≥ 0.10` AND wrapper `✓` → `CONFIRMED_WITH_X`.
2. ELSE IF any row has `adj-R² ≥ 0.10` AND wrapper `△` or `✗` → `CONFIRMED_WITHOUT_X`.
3. ELSE IF any row has citation but below threshold OR specification-distance flagged → `MIXED`.
4. ELSE → `GAP`.

Also define what `△` means for the `CONFIRMED_WITH_X` branch — promote to `✓` with caveat or demote. As written the analyst picks.

### 2. τ-gap (0.15 vs 0.10) is asserted without justification — FLAG
**§1 line 15 vs §3 item 1 line 33.** "To allow sampling noise across studies" is not a technical justification:
- Direction is not self-evident: if published studies are better-powered, the literature bar should be *higher*, not lower.
- Conflates between-study heterogeneity (calls for meta-analytic pooling) with within-study sampling error (already in each SE).
- 0.05 is a magic number.

**Fix:** Cite a specific rationale (e.g., "published `adj-R²` is in-sample; τ=0.15 is out-of-sample") or collapse to a single threshold. If gap stays, document it is a design choice, not a derivation.

### 3. Tier 2 handoff has hidden coupling — FLAG
**§11 line 129.** Treating `β_CPI` as "a cited lemma" implicitly requires Tier 1 to produce:
- Exact regression specification of the cited paper (frequency, controls, CPI-surprise construction).
- Statement of whether the cited specification is compatible with the differential-form underlying in `ranPricing.ipynb` §Applications.
- Sample period / recency — a 2008 paper on COP/USD announcement effects may not port to 2025 cCOP/USDT mechanics.

None are in §7 or §10. Tier 2 scoping will stall.

**Fix:** Add columns to §7: `specification frequency`, `CPI-surprise construction`, `sample end year`, `portability-to-cCOP caveat`. Mirror in §10 item 2.

### 4. Non-goals list has gaps — FLAG
**§12 lines 134–139.** Not covered:
- Meta-analysis / pooling of partial studies into a weighted `adj-R²`.
- Paraphrasing translated BanRep findings into "what it would say if re-run on our specification" (crosses into in-house analysis).
- Infrastructure-build side-quest scoping (referenced in §9 but absent from §12).
- Neighboring 2026-04-02 repo — explicit read-allowed / write-forbidden clause.

**Fix:** Add four bullets to §12.

### 5. Success criterion §15 permits under-specified deliverables — FLAG
**§15 lines 151–157.** Criteria 1 and 2 have escape hatches ("documented reason skipped" / "documented exhaustive-search failure") with no minimum floor. A deliverable could mark every source skipped and still pass. Criterion 4 is invalidated by Finding 1 (verdict is not partitioning).

**Fix:**
- Minimum 3 of 4 query patterns per source, or explicit unavailability with evidence.
- N ≥ 2 citations considered and recorded before `GAP` can be declared.
- After Finding 1 is fixed: criterion 4 = "verdict maps deterministically from §7 + §8 via the §9 decision procedure."

### 6. Infrastructure-check reasoning is load-bearing but unsourced — FLAG
**§2 item 1 line 23.** The claim "`g^pool ≈ φ²V(P)/(8L)` is not measurable at scale on any live cCOP pool today" is the central pivot justification but not traced:
- Mento-vAMM-not-Uniswap: no pointer to the 2026-04-02 files.
- "$7K/day on ~$66–86K market cap": no Dune query ID or snapshot date.
- "Today" is not anchored. If executed two weeks later and cCOP liquidity changes, the premise silently expires.

**Fix:** Add `Evidence anchors` subsection listing 2026-04-02 files / Dune query IDs / snapshot dates, cross-referenced to the files §8/§10 will copy to `.scratch/`.

### 7. "Close proxy" / "sufficiently close peers" is unbounded — NIT→FLAG at execution
**§2 item 2 line 25, §3 item 1 line 33.** An analyst could accept Chilean CPI and Peruvian FX as a "close proxy" and flip the verdict.

**Fix:** Enumerate the admissible set. Suggested: "same-country CPI with different release (headline vs core) OR same-country monetary-policy surprise. Not a different-country CPI." If cross-country proxies are allowed, list them.

### 8. §7 rating scale undefined — NIT
**§7 line 73.** "Literature β strength" has no legend. Number? Qualitative bucket? Binary? Inconsistent encoding breaks §9.

**Fix:** Require `adj-R²` + significance (`0.18*` / `n/s`), with `NOT STUDIED` as sentinel.

### 9. §8 ternary vs §9 binary — NIT
**§8 lines 87–94.** `△` used for EUR/MXN/BRL but §9 treats wrapper as binary. Resolve per Finding 1.

### 10. MIXED lacks tie-break — NIT
**§9 line 105.** What if literature-best ≠ on-chain-best?

**Fix:** Add: "If literature-best ≠ on-chain-best, recommend literature-best with a flagged caveat; Tier 1b scopes the gap on the on-chain-best candidate."

### 11. Time estimate has no stop condition — NIT
**§14 line 147.** Add hard cap: "≤ 3 days; if longer, reopen as Tier 1a with explicit rescoping."

### 12. Deliverable path splits notes/ and .scratch/ — NIT
**§10 line 111.** Deliverable goes to `contracts/notes/structural-econometrics/identification/...`; artifacts to `.scratch/`. Memory `feedback_research_output_folder.md` says research output goes to `.scratch/`. May be intentional (durable vs transient) but must be acknowledged or confirmed with user.

## Summary

| # | Severity | Section | Change |
|---|---|---|---|
| 1 | FLAG | §9 | Decision tree with precedence; resolve `△`. |
| 2 | FLAG | §1 / §3 | Defend or collapse τ=0.15 vs 0.10 gap. |
| 3 | FLAG | §7 / §10 / §11 | Portability columns for Tier 2 handoff. |
| 4 | FLAG | §12 | Forbid meta-analysis, re-running regressions, side-quest scoping, neighboring-repo writes. |
| 5 | FLAG | §15 | Minimum query/citation floor; tie criterion 4 to §9 procedure. |
| 6 | FLAG | §2 | Evidence-anchors subsection. |
| 7 | NIT→FLAG | §2 / §3 | Define admissible "close proxy" set. |
| 8 | NIT | §7 | Fix rating-scale encoding. |
| 9 | NIT | §8 | Reconcile `△` with §9 binary. |
| 10 | NIT | §9 MIXED | Tie-break rule. |
| 11 | NIT | §14 | Hard time cap. |
| 12 | NIT | §10 | Confirm notes/ vs .scratch/ split. |

## What the spec gets right

- Infrastructure-check finding correctly identified as load-bearing; pivot is clean.
- Scope (§4) is crisp; non-goals (§12) carry memory constraints.
- Search order (§5) correctly prioritizes BanRep → IMF → NBER/SSRN → Scholar → arxiv-last; the low-prior-on-arxiv note is correct for macro-econ.
- Deliverable structure (§10) is tight: one file, enumerated sections, explicit citation discipline.
- `CONFIRMED_WITHOUT_X` routes the build-infrastructure decision to the user rather than auto-spawning.
- Read-only access to the 2026-04-02 neighboring repo honors Angstrom-read-only and no-on-chain-queries constraints.

## Recommendation

Address FLAGs 1–6 before execution. NITs 7–12 can be handled inline with documented assumptions, but FLAGs 1 (decidability) and 3 (Tier 2 handoff) are the most consequential — without them, a completed Tier 1 deliverable may still leave Tier 2 scoping blocked.
