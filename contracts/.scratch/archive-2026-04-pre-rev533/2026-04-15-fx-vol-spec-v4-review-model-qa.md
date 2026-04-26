# Model QA Review: fx-vol-cpi-surprise Rev 4

**Reviewer:** Model QA Specialist
**Date:** 2026-04-16
**Verdict:** CONDITIONAL PASS -- 1 FLAG, 3 NITs, 0 BLOCKs

---

## 1. Pre-committed primary specification -- NIT

The primary spec is well-defined: RV^{1/3} LHS, CPI-only RHS, full controls, OLS + NW(4). Two minor gaps: (a) no explicit winsorization rule for RV outliers (COVID weeks could produce extreme cube-root values that dominate OLS), and (b) missing-data handling is implicit -- spec says "~1100 weeks" but does not state whether weeks with missing FRED quotes, holidays, or <3 trading days are dropped or filled. Pre-commit a rule (e.g., "drop weeks with <4 trading days; no winsorization unless Cook's D > 4/N, reported either way").

**Severity: NIT.** Unlikely to change the sign or significance of beta, but weakens reproducibility.

## 2. Reconciliation protocol "disagree" definition -- FLAG

The protocol says if OLS and GARCH-X "disagree," the gate does not pass. But "disagree" is undefined. Four plausible readings: (i) different sign of beta/delta, (ii) one significant and one not, (iii) point estimates differ by >X%, (iv) confidence intervals do not overlap. These produce materially different gate outcomes. Recommendation: define disagreement as "either different sign OR one insignificant at 10% while the other is significant." This is the tightest reasonable standard and avoids the ambiguity.

**Severity: FLAG.** Without a definition, two honest analysts could reach opposite gate conclusions from the same estimates.

## 3. T3b threshold: 1.28 (90% one-sided) -- NIT

For a product go/no-go gate, 90% one-sided is defensible but not conservative. The spec correctly frames this as "conviction for a product pitch," not regulatory capital. At N~260 release weeks (effective sample for beta identification), power is modest -- moving to 1.645 (95%) risks rejecting a true positive. The 1.28 threshold is acceptable IF the reconciliation protocol (item 2) provides independent confirmation via GARCH-X. If the reconciliation definition remains vague, tighten T3b to 1.645 as a compensating control.

**Severity: NIT.** Acceptable given dual-method confirmation, but document the rationale for 90% vs 95% explicitly.

## 4. Cube-root "exploratory" vs "pre-committed primary" -- NIT

The spec acknowledges the contradiction and resolves it adequately: the chi-squared theoretical justification does not hold at n=5, but the cube-root is chosen as "best available variance-stabilizer" and locked in as the primary LHS to prevent fishing. The label "exploratory" refers to theoretical grounding, not to its role in the testing hierarchy. This is coherent. The residual risk is that if T5 (Jarque-Bera) rejects normality of cube-root residuals, the primary spec's inference is weakened. Recommend pre-committing: "if T5 rejects at 1%, report bootstrap CIs for T3b as supplementary."

**Severity: NIT.** Labeling is confusing but substantively resolved.

## 5. GARCH-X convergence: BFGS / 500 iterations -- PASS

BFGS with analytic gradient and 500 iterations is standard for GARCH(1,1)-X on ~1100 weekly obs. Francq & Zakoian (2019, Ch. 7) and the rugarch/arch Python packages default to similar settings. The QMLE fallback (Bollerslev-Wooldridge 1992) for non-Gaussian residuals is correct. The non-convergence declaration criterion (500 iters or non-PD Hessian) is adequate. One suggestion: also check that estimated alpha1 + beta1 < 1 (stationarity); if violated, flag as sensitivity concern.

**Severity: PASS.**

## 6. Specification classification consistency -- PASS

Primary (1 spec), confirmatory (GARCH-X), sensitivity (A1-A9), exploratory (log-RV, raw-RV, AR(1) fallback). No sensitivity spec feeds the gate. The CPI+PPI decomposition is labeled "co-primary" for interpretation but does not override the CPI-only gate. Classification is internally consistent.

**Severity: PASS.**

## 7. Remaining statistical issues -- PASS with note

The spec's error-structure analysis (Section 3.4) correctly identifies that net bias is ambiguous and the "conservative lower bound" claim does not hold unconditionally. This is a significant improvement over prior revisions. One residual concern: the spec does not discuss multicollinearity between VIX and oil return (both capture global risk). Recommend computing VIF for the control set and reporting; if VIF > 5 for any control, note that beta's SE may be inflated but beta itself is unbiased.

---

**Overall:** The spec is well-constructed for a reduced-form event study. The single actionable item is defining "disagree" in the reconciliation protocol (item 2) before estimation begins. Everything else is documentation hygiene.
