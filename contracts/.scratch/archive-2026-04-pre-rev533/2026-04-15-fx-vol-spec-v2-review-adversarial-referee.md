# Adversarial Referee Report: Rev 2 of FX-Vol CPI-Surprise Spec

**Date:** 2026-04-16
**Spec reviewed:** `contracts/notes/structural-econometrics/specs/2026-04-15-fx-vol-cpi-surprise.md` (Rev 2)
**Verdict: MINOR REVISION**

---

## Point-by-Point Assessment

### 1. CPI-only primary vs. consensus availability -- MAJOR

The fix is NOMINAL. The primary equation requires $s_t^{\text{CPI}}$ = DANE release minus BanRep consensus. The consensus source is flagged UNVERIFIED. If BanRep Encuesta is unavailable (be_1171 used Bloomberg, per their fn.16), the fallback is an AR(1) residual. An AR(1) residual is a FORECAST ERROR, not a SURVEY-BASED SURPRISE -- these are econometrically distinct objects with different information sets. The spec must: (a) define the AR(1) fallback as a SEPARATE co-primary specification, not a silent substitution; (b) acknowledge that the AR(1) version tests a weaker hypothesis (predictability-adjusted vol response, not news-impact response). Without this, the "CPI-only primary" claim collapses to "whatever-we-can-get primary."

### 2. GARCH-X buried as A7 -- MAJOR

Cosmetic. be_1171 Section 3 identifies via heteroskedasticity-identified VAR with GARCH(1,1) conditional variances as the IDENTIFICATION MECHANISM (Sentana-Fiorentini 2001). The spec's own identification section (4.4) cites heteroskedasticity backup via the same Sentana-Fiorentini paper. Yet the model that IMPLEMENTS that identification strategy sits at A7. This is internally incoherent: the spec invokes GARCH for identification but relegates it to sensitivity for estimation. GARCH-X should be co-primary. OLS on weekly RV is defensible as a quick pass but treating it as primary over the model the literature actually uses requires explicit justification that the spec does not provide.

### 3. Bias direction ambiguous but implications unchanged -- MINOR

The correction in Section 3.3-3.4 is genuine -- the AMBIGUOUS label and the conditional logic (safety claim holds only if T1 passes) represent real engagement. However, Sections 4.5 and 5 still reason about beta as if it were informative for the product without referencing the ambiguity caveat. The fix: add a forward pointer in Section 5 (T3 interpretation) stating that a significant beta is NECESSARY but its MAGNITUDE is unreliable until the bias direction is resolved via T1.

### 4. Two-sided T3 without economic gate -- MINOR

The statistical change from one-sided to two-sided is correct and more honest. But the spec drops the ECONOMIC requirement entirely. The product needs beta > 0 (CPI surprise increases vol). Beta < 0 would mean higher-than-expected inflation DECREASES vol -- economically anomalous under inflation targeting. The fix is simple: test H0: beta = 0 vs H1: beta != 0 (statistical); then require sign(beta) > 0 as a separate PRODUCT GATE (economic). Add one row to the test table: "T3b: sign gate -- beta > 0 required for product viability, not tested statistically but verified ex post."

### 5. Layer 1 to Layer 2 mapping gap -- SUGGESTION

Genuinely new, not cosmetic. The section correctly identifies that uniform vol distribution across ticks kills the hedge. Missing: the FALSIFIABLE CONDITION. State explicitly: "If empirical tick-level growth data from Angstrom shows coefficient of variation of g(i)/g_pool across tick ranges < X during CPI-release weeks, the differential structure produces insufficient payout and the product thesis fails." Without a falsifiable threshold, the deferral is open-ended.

### 6. Oil control -- SUGGESTION

Genuine addition. Weekly oil RETURN captures terms-of-trade shocks (price change). But Colombia's fiscal channel operates through oil price LEVEL (Ecopetrol dividends fund ~10% of central government revenue). Consider adding log(WTI level) as an additional regressor or at minimum as a sensitivity (A9). The return-only specification risks omitting a slow-moving fiscal channel that matters at weekly frequency through expectations rather than contemporaneous price moves.

### 7. UNVERIFIED flags without status update -- MINOR

The three flags are honest and valuable. But spec status reads "Rev 2" without acknowledging that Phase 5 is BLOCKED. Update the status line to: "Rev 2 -- Phase 5 blocked pending verification of BanRep consensus archive, IBR term structure, and SUAMECA intervention data."

---

## Summary

| # | Issue | Severity |
|---|---|---|
| 1 | CPI-only primary hollow without consensus; AR(1) fallback is a different hypothesis | MAJOR |
| 2 | GARCH-X as A7 contradicts spec's own identification strategy | MAJOR |
| 3 | Ambiguous bias corrected in text but not propagated to test interpretation | MINOR |
| 4 | Two-sided test drops economic sign gate | MINOR |
| 5 | Mapping gap lacks falsifiable closure condition | SUGGESTION |
| 6 | Oil return omits fiscal-level channel | SUGGESTION |
| 7 | Status line does not reflect Phase 5 blockage | MINOR |

Two MAJOR issues remain. Neither requires restructuring the spec -- both require promoting existing content (GARCH-X) or adding a co-primary fallback (AR(1) as distinct specification). The MINORs are text-level fixes. The SUGGESTIONs strengthen but are not blocking.

**Verdict: MINOR REVISION.** The MAJORs are addressable within the current framework. No architectural rework needed.
