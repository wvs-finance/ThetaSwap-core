# Model QA Review: fx-vol-cpi-surprise spec Rev 3

**Reviewer:** Model QA Specialist
**Date:** 2026-04-16
**Verdict:** APPROVE_WITH_CHANGES

---

## 1. Wilson-Hilferty cube-root (Spec line 20, Phase 0c) -- FLAG

Wilson-Hilferty 1931 approximates a chi-squared(k) r.v. as normal via cube-root. The spec applies it to RV_t = sum of 5 squared daily returns. This requires those squared returns to be i.i.d. chi-squared(1), i.e., daily returns are i.i.d. N(0, sigma^2). COP/USD daily returns exhibit fat tails (kurtosis >> 3) and serial dependence in volatility -- both violate the chi-squared premise. At n=5 the CLT does not rescue you. The cube-root will reduce right-skew mechanically, but the Wilson-Hilferty variance-stabilization guarantee (relative error < 1% at df >= 10) does NOT hold at df=5 under fat tails. The spec correctly demotes log(RV) for the same reason (ABDE 2001 normality fails at n=5), but then grants cube-root theoretical priority on equally shaky grounds. Treating RV^{1/3} as "theoretically justified" overstates the case; it should be labeled exploratory alongside log(RV), with raw RV as the only transform that requires no distributional assumption. Impact: labeling, not estimation -- all three transforms are estimated anyway.

## 2. OLS-on-RV vs GARCH-X co-primacy (Spec lines 146-153, Phase 3a) -- FLAG

OLS on f(RV_t) estimates a regression of REALIZED variance on surprise. GARCH(1,1)-X estimates how surprise enters CONDITIONAL variance of daily returns. These are different estimands: E[RV_t | s_t] vs h_t in the variance equation. Both being "co-primary" is fine as complementary evidence, but the spec never states they estimate different objects or how to reconcile conflicting results. If OLS finds beta > 0 but GARCH-X finds delta = 0 (or vice versa), what is the product gate decision? Add a reconciliation protocol. No identification conflict exists -- they are separately estimated -- but the interpretive gap is a documentation weakness.

## 3. AR(1) fallback and Andersen 2003 claim (Spec line 165) -- FLAG

The spec states Andersen et al. 2003 section II note survey-based and time-series-based surprises produce "quantitatively similar results for US data." This is approximately accurate for liquid G10 markets where consensus surveys are efficient. The spec correctly flags "verification needed for Colombian CPI." Colombia's BanRep Encuesta is monthly with ~20 respondents and potential staleness -- the gap between survey consensus and AR(1) forecast could be substantially larger than for US Bloomberg surveys with 50+ contributors. The claim does NOT transfer automatically. Recommendation: report both if survey data is available, never substitute silently. The spec already says this (line 165) -- adequate as written.

## 4. 10% tick-concentration threshold (Spec lines 224-226, Phase 4.5) -- NIT

The 10% one-sided difference in g(i_S)/g(i_T) between surprise and non-surprise weeks is not justified by any cited reference. It is arbitrary. However, this is a Layer 2 simulation threshold applied AFTER beta is estimated, and the spec explicitly labels it as a "falsifiable closure condition" -- meaning it is designed to be tested, not assumed. The arbitrariness is acceptable for a gate that will be calibrated empirically. Minor improvement: state that 10% is a placeholder subject to power analysis once Layer 2 simulation sample size is known.

## 5. T3b product gate definition (Spec lines 239, Phase 5) -- BLOCK

T3b is defined as "sign check on point estimate (not a statistical test)." This is underspecified and dangerous. A point estimate beta-hat = +0.001 with SE = 0.05 passes T3b but carries zero economic conviction. The product gate should require at minimum that the LOWER bound of a 90% one-sided CI exceeds zero, i.e., beta-hat - 1.28 * SE > 0. Without this, random noise can greenlight the product. Alternatively, require T3a (two-sided significance) to pass BEFORE T3b is evaluated -- but as written, T3b can pass independently of T3a.

## 6. Oil return + oil level multicollinearity (Spec lines 270, A8) -- FLAG

Weekly log-return r_t = log(P_t) - log(P_{t-1}) and log-level log(P_t) are mechanically correlated (r_t is the first-difference of log(P_t)). In a weekly regression with both, the level captures a near-unit-root process while the return captures innovations -- VIF will be elevated but not infinite since the level is persistent while the return is stationary. They can enter simultaneously as a sensitivity check, but the spec should note: (a) joint entry will inflate SEs on both oil coefficients, (b) the primary spec (line 142) correctly uses return only, and (c) A8 tests whether the LEVEL adds explanatory power above the return, not whether both should be retained. Adequate as a sensitivity. No change needed if A8 remains sensitivity-only.

## 7. CPI vs PPI standardization (Spec lines 155, 162-163) -- NIT

CPI: (release - consensus) / sigma_historical -- a surprise measure. PPI: (delta_IPP - mean) / sigma_{delta_IPP} -- a mean-deviation measure. These are conceptually different: CPI measures deviation from expectations, PPI measures deviation from own history. The spec claims they are "directly comparable" because both are in "per 1-SD shock" units (line 163). The units ARE comparable for regression coefficient interpretation (both betas measure RV response per 1-SD of their respective RHS). But the ECONOMIC content differs: a 1-SD CPI surprise is unexpected inflation news; a 1-SD PPI deviation is just an unusual PPI print (which may have been partially expected). If PPI consensus becomes available, re-standardize identically. As-is, the comparison beta_1 vs beta_2 is valid statistically but the "CPI dominates" interpretation requires the caveat that PPI's beta_2 is attenuated by the cruder surprise proxy.

---

**Summary:** One BLOCK (T3b product gate needs a confidence requirement), two FLAGs requiring documentation fixes (cube-root justification downgrade, OLS/GARCH reconciliation protocol), and two NITs. The econometric architecture is sound. The identification strategy, control set, and sensitivity matrix are well-constructed for the data constraints.
