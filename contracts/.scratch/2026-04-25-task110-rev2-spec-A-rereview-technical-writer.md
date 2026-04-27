# Technical Writer Re-Review — Task 11.O Rev-2 Spec, Track A (post-fix-up)

**Date:** 2026-04-26
**Reviewer:** Technical Writer agent (re-dispatch)
**Subject:** `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` (now 655 lines, was 604; +51 LOC across 5 fix-up edits per agent `ad4f61bb9d3caf592`)
**Prior review:** `contracts/.scratch/2026-04-25-task110-rev2-spec-A-review-technical-writer.md` (verdict NEEDS-WORK; 2 BLOCKERs + 4 advisories)
**Re-review scope:** verify both BLOCKERs resolved; verify CR-asked Edits 3/4/5 land cleanly; verify no regressions in byte-exact anchors; verify honesty discipline of the new convex-payoff caveat.

---

## Verdict

**PASS-with-non-blocking-advisories.**

Both prior BLOCKERs are resolved with materially correct prose. The CR-asked edits (Edits 3/4/5) land cleanly. No regressions detected in any byte-exact anchor (76/65/56 N anchors, methodology literals, MDES_FORMULATION_HASH, decision_hash, anti-fishing invariants table). The §11.A caveat genuinely refuses to back-door the §10.6 ζ-group deferral as a product-validity rescue claim — it does the honest work the prior review demanded.

This graduates from NEEDS-WORK to PASS. The remaining items are the four prior non-blocking advisories that the fix-up agent declined; the declines are legitimate (out of dispatch scope). One trivial item (§3.4 → §7 typo) survives and is flagged below.

---

## Evidence per re-review checkpoint

### 1. TW BLOCKER §2.1 (product purpose statement) — RESOLVED

Lines 46–55 expand §1.1 with a 4-bullet product-context block that names:
- "**convex (option-like) financial instruments**" (line 48) ✓
- "derivatives with capped-loss / levered-upside payoffs (puts, calls, caps, floors)" (line 48) ✓
- "**MACROECONOMIC shocks**" (line 50) — explicitly contrasted with microeconomic at line 50 ✓
- "WC-CPI **60% food / 25% energy+housing-utilities / 15% transport-fuel** budget-share weighting" (line 51) ✓
- Inequality-lens marker explicitly named: "The 60/25/15 weighting IS the inequality-lens marker" (line 51) ✓
- First-stage / multi-stage framing: "Mean-β identification is the **first stage** of product validity ... necessary-but-insufficient for convex-payoff pricing" (line 55) ✓

Length: ~10 lines of dense prose, well-structured. Required-fix wording from prior review §2.1 is materially incorporated even though the words are paraphrased — the fix-up agent did better than verbatim adoption by tightening to four bullets.

### 2. TW BLOCKER §2.2 (convex-payoff insufficiency caveat) — RESOLVED

§11.A at lines 507–516 contains all four required elements verified one-by-one:

| Required element (prior review §2.2) | Location | Verdict |
|---|---|---|
| Mean-β = first-stage / linear-hedge calibration only | Line 511 ("Mean-β identification is first-stage / linear-hedge calibration only") | ✓ |
| Convex pricing requires conditional variance / quantile / tail evidence | Line 512 ("requires CONDITIONAL VARIANCE / QUANTILE / TAIL evidence — not just mean-shifts"; with vega gradient + Heston/Bates citation) | ✓ |
| Rev-3 deferral via §10.6 ζ-group | Line 513 ("This Rev-2 spec consciously defers tail-risk to Rev-3 (see §10.6 ζ-group roadmap…)") | ✓ |
| T3b PASS framed honestly as mean-shift only, NOT option-pricing readiness | Line 514 ("Y₃'s mean shifts with X_d in a direction consistent with the linear-hedge thesis — NOT 'Abrigo can price options from this β̂.' A future engineer wiring β̂ into a convex-payoff pricer would miscalibrate the product.") | ✓ |

Additionally Scenario A (line 501) is reframed: "Product painkiller framing supported **at the linear-payoff hedge level only**". §12 (line 534) is scope-qualified: "the simulator-calibration claims in this section are valid only for *linear-payoff* hedge instruments". The caveat is propagated to its two consumer sections — not orphaned.

### 3. Cross-reference integrity (§11.A → §10.6) — VERIFIED

§11.A line 513 points to "§10.6 ζ-group roadmap"; §10.6 exists at lines 482–491 with all four ζ rows (ζ.1 quantile regression, ζ.2 GARCH-X, ζ.3 lower-tail conditional, ζ.4 option-implied-vol). §1.1 line 55 also points forward to "§10.6" and "§11.A" — both targets resolve. Round-trip cross-references verified.

### 4. 14-row matrix consistency — CLEAN

Grep over the spec for `13-row|14-row` returns 6 hits, all "14-row". Locations updated:
- Line 328 (header `## 6. The 14-row resolution matrix`) ✓
- Line 338 ("the 14-row pre-committed grid") ✓
- Line 361 ("Why this 14-row specification differs") ✓
- Line 362 ("A 'default reasonable' 14-row grid") ✓
- Line 472 ("The 14-row resolution matrix in §6") ✓
- Line 491 ("Each ζ row … equivalent to the current 14-row matrix") ✓

§17 summary at line 648: "Resolution matrix | 14 rows (§6); Row 14 (WC-CPI weights sensitivity at 50/30/20, 60/25/15-primary, 70/20/10) is first-class inequality-lens product-validity instrumentation". Consistent.

Row 14 itself (lines 355 + 359) reads coherently: pre-registered expectation that β̂ should be of the same sign and within 1·SE across the three weighting regimes, with CORRECTIONS-block discipline if it fails. The framing as "first-class product-validity instrumentation, not 'nice-to-have'" is the right pitch under the corrected product memo.

### 5. No anchor regressions — VERIFIED

| Anchor | Pre-fix-up | Post-fix-up | Verdict |
|---|---|---|---|
| `MDES_FORMULATION_HASH` | `4940360dcd2987…cefa` (§5 line 298, §9 line 444) | byte-exact preserved (§5, §9 line 464) | PRESERVED |
| `decision_hash` | `6a5f9d1b…443c` (§5 line 299) | byte-exact preserved | PRESERVED |
| Y₃ primary methodology literal | `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` | byte-exact across §1, §5 line 300, §13 line 552 | PRESERVED |
| Y₃ IMF-IFS-only sensitivity literal | `y3_v2_imf_only_sensitivity_3country_ke_unavailable` | byte-exact across §1, §5 line 301, §13 line 553 | PRESERVED |
| `carbon_basket_user_volume_usd` | 7 occurrences | preserved across all consumer sections (§13 line 554) | PRESERVED |
| N anchors (76 / 65 / 56) | §1, §5 MDES table, §6 rows 1/3/4, §13 | byte-exact preserved including dual-axis FAIL note at n=56 | PRESERVED |
| Anti-fishing invariants table | §5 lines 311–314 | unmodified | PRESERVED |
| Pre-registered FAIL row 3/4 verdicts + justifications | §6 lines 367–370 | unmodified | PRESERVED |

Functional form `Y_asset_leg_t = (Banrep_rate_t − Fed_funds_t)/52 + (TRM_t − TRM_{t-1})/TRM_{t-1}` preserved byte-exact at line 33.

### 6. Honesty discipline of §11.A — PASSES

The risk in §11.A would be soft-pedalling: "we deferred convex pricing to Rev-3 — therefore Rev-2 is fine for product." The actual prose at lines 511–514 does the opposite. Three honest moves verified:

1. Line 514 explicitly forecloses option-pricing inference: "**NOT** 'Abrigo can price options from this β̂.' A future engineer wiring β̂ into a convex-payoff pricer would miscalibrate the product." This is an *engineering safety disclosure*, not a soft hedge.
2. Line 512 grounds the variance/tail requirement in Black-Scholes vega + Heston/Bates rather than asserting bare claim. Citation discipline.
3. Line 516's closing sentence — "mean-β identification is the **first stage** of a multi-stage product-validity test; Rev-2 ships the first stage cleanly, and the §10.6 ζ-group is the explicit Rev-3 dependency" — does not promise the ζ-group will pass; it acknowledges the dependency exists and is unmet.

The §10.6 ζ-group itself (lines 484–491) does the honest work: each ζ row is described in terms of what it *tests* (asymmetric quantile shift, variance amplification, lower-tail compression, option-implied-vol surface fitting), not in terms of what it will demonstrate. No back-door product-validity rescue claim is made.

### 7. Declined advisories — LEGITIMATE DECLINES

The fix-up agent declined four prior advisories. Re-confirming the declines:

| Declined item | Original advisory | Decline legitimacy |
|---|---|---|
| §3.4 → §7 T1 typo | TW §1.4 (trivial) | LEGITIMATE — out of dispatch scope (5-edit-limited fix-up); flag for next-spec-touch |
| §6.5 4-part block for matrix | TW §1.6 (non-blocking) | LEGITIMATE — explicit "non-blocking advisory" in prior review |
| CR §3.1 advisories | (CR-side, not TW) | LEGITIMATE — CR's call, not TW's |
| RC §6 advisories | (RC-side, not TW) | LEGITIMATE — RC's call, not TW's |

All four declines are within the fix-up agent's tight scope of 5 edits ≤ 12 tool uses. None of them are blocking.

---

## Surviving advisories (non-blocking, deferred to next spec touch)

1. **§3.4 → §7 T1 typo (trivial).** Line 264 says "tested by §6 T1" but the T1 specification is at §7 line 378+. One-section drift; not a blocker.
2. **§6.5 resolution-matrix 4-part citation block (recommended).** The 14-row matrix is the spec's largest pre-registration commitment; an overarching 4-part citation block (Reiss-Wolak Phase 4 sensitivity-grid principle + Why used + Relevance + Connection-to-product) would tighten the citation discipline. Per `feedback_notebook_citation_block`. Recommended for Rev-2.1 or next-touch.

Neither blocks Rev-2 commit.

---

## Summary findings table

| Dimension | Pre-fix-up verdict | Post-fix-up verdict |
|---|---|---|
| TW BLOCKER §2.1 — product purpose statement names convex / option-like / macroeconomic / 60-25-15 inequality lens | BLOCKING | **RESOLVED** |
| TW BLOCKER §2.2 — convex-payoff insufficiency caveat with all 4 elements | BLOCKING | **RESOLVED** |
| Cross-reference integrity (§11.A → §10.6 round-trip) | n/a | **PASS** |
| 14-row matrix consistency (5+ in-spec references) | n/a | **PASS** (6/6 updated; §17 summary updated) |
| Anchor preservation (76/65/56, MDES_FORMULATION_HASH, decision_hash, methodology literals, anti-fishing invariants) | n/a | **PASS** (no regressions) |
| §11.A honesty discipline (no back-door product-validity rescue via ζ-group) | n/a | **PASS** |
| §3.4 → §7 typo | non-blocking | unchanged (declined; legitimate decline) |
| §6.5 citation block | non-blocking | unchanged (declined; legitimate decline) |

---

## Final verdict

**PASS-with-non-blocking-advisories.**

Both prior BLOCKERs cleanly resolved. CR-asked Edits 3/4/5 land cleanly. No regressions. Honesty discipline of the convex-payoff caveat is genuine. The two surviving advisories are non-blocking and explicitly declined as out-of-dispatch-scope.

Recommendation: Track A Rev-2 is **commit-ready** from the Technical Writer perspective. Foreground orchestrator should proceed to plan-fold against Track B (when Track B re-review converges). The two surviving advisories (§3.4 typo, §6.5 citation block) should be addressed at the next scheduled touch of this spec — not as gating items.

---

## Files referenced

- **Spec under re-review:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md` (655 lines)
- **Prior TW review:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-spec-A-review-technical-writer.md`
- **Product memo:** `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_abrigo_convex_instruments_inequality.md`
- **This re-review:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-25-task110-rev2-spec-A-rereview-technical-writer.md`

**End of Technical Writer re-review.**
