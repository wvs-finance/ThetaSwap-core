# Model QA Review: fx-vol-cpi-surprise Spec Rev 2

**Reviewer:** Model QA Specialist
**Date:** 2026-04-16
**Verdict:** APPROVE_WITH_CHANGES (2 BLOCK, 3 FLAG, 2 NIT)

---

## 1. sqrt(RV) variance-stabilization at n=5

**BLOCK | Section 1, line 21**

The spec claims sqrt(RV) is a "variance-stabilizing transform for chi-squared-family data at small n." This is imprecise. The classical result (Bartlett 1947; Johnson, Kotz & Balakrishnan Vol. 1, Ch. 18) states that for X ~ chi-squared(k), the transform sqrt(X) has variance approximately 1/(4k) -- stabilized relative to the mean but only asymptotically as k grows. At k=5 (weekly trading days), the approximation is poor: the exact variance of sqrt(chi-sq(5)) still depends on the non-centrality and the 1/(4k) approximation has ~10% relative error. The Wilson-Hilferty cube-root transform (RV^{1/3}) is the canonical small-df stabilizer. Furthermore, weekly RV = sum of 5 squared log-returns is only chi-squared if returns are iid N(0,sigma^2), which fails empirically (fat tails, autocorrelation). **Fix:** Demote sqrt(RV) to exploratory alongside log(RV), or add RV^{1/3} as the theoretically justified small-n transform. State that no LHS transform has strong theoretical backing at n=5; all three are empirical candidates.

## 2. Oil control functional form

**FLAG | Section 2.5, line 78; Section 4.1, line 148**

Weekly oil log-return is a reasonable starting point but incomplete. The COP-oil literature (Gonzalez & Hernandez 2016, BanRep WP 880; Rincón-Castro & Rodriguez-Niño 2016) documents that COP/USD responds to oil LEVEL changes (terms-of-trade channel) and oil VOLATILITY (risk-premium channel) differentially. be_1171 itself uses 5-minute intraday data and controls for macroeconomic surprises broadly but does not isolate an oil channel at weekly frequency. traspasoAinflacion (Rincón-Castro et al. 2021) estimates ERPT at quarterly frequency where oil enters via the terms-of-trade, not return. At weekly frequency, oil return captures the level-change channel but misses the volatility channel. **Fix:** Add oil realized volatility (weekly RV of WTI) as a sensitivity (A9) to disentangle level vs. volatility channels. Document that oil return alone may leave residual COP-oil vol correlation in epsilon.

## 3. Bias direction ambiguity in S3.4

**NIT | Section 3.4, lines 130-132**

The ambiguity characterization is correct but incomplete. Two additional upward-bias sources: (a) if DANE revises preliminary CPI releases (revision bias), the surprise computed from preliminary data overstates true news; (b) simultaneous PPI release on the same day (Section 4.4, line 194) means the CPI surprise coefficient absorbs some PPI-induced vol when PPI is omitted from the primary equation -- this biases beta upward if PPI and CPI surprises are positively correlated (they are, mechanistically). The spec acknowledges (b) via the co-primary decomposition but does not list it as an upward-bias source in S3.4. **Fix:** Add both sources to the S3.4 bias table.

## 4. GARCH(1,1)-X surprise entry form

**BLOCK | Section 6.2, A7, line 249**

The spec enters s_t^{CPI} in levels into the variance equation. This is mis-specified. The variance equation must be non-negative by construction. A negative CPI surprise with delta > 0 would push h_t negative. The standard GARCH-X specification (Han & Kristensen 2014, JoE; Hwang & Satchell 2005) requires the exogenous variable to enter as |s_t| or s_t^2 to preserve non-negativity. Engle & Rangel (2008) spline-GARCH uses squared macro variables. The GJR-GARCH-X variant can accommodate sign asymmetry via s_t^+ and |s_t^-| separately (linking to A8). **Fix:** Replace s_t^{CPI} with |s_t^{CPI}| in the variance equation. To test sign asymmetry within GARCH, use delta^+ * s_t^{+} + delta^- * |s_t^{-}| (both terms non-negative). Add non-negativity constraint to the spec text.

## 5. Layer 1 to Layer 2 mapping gap (S4.5)

**FLAG | Section 4.5, lines 196-209**

The gap is correctly stated and the three Layer 2 requirements are appropriate. However, the spec understates the severity. The gap is not merely "deferred" -- it is a necessary condition for the product to function. If Layer 2 shows uniform vol distribution across ticks, then beta > 0 has zero product value regardless of statistical significance. The spec should explicitly classify this as a GATE: if Layer 2 cannot demonstrate concentration != uniform, the entire estimation exercise is necessary-but-not-sufficient and the product claim does not follow. **Fix:** Add a gate condition: "Layer 2 must demonstrate non-uniform tick concentration BEFORE beta can be used in product parameterization. If Layer 2 fails this gate, Layer 1 results remain academically valid but have no product application."

## 6. Unverified data source fallbacks

**FLAG | Section 4.3, line 181**

- **BanRep consensus -> AR(1) proxy:** Statistically inadequate. AR(1) on CPI produces a "surprise" that is mechanically correlated with the CPI level, violating the Andersen et al. 2003 orthogonality requirement. The surprise would capture expected + unexpected components, biasing beta toward zero (attenuation). Acceptable only as a lower-bound diagnostic, not as a co-primary specification.
- **IBR -> simple lag of policy rate:** Adequate. BanRep rate changes are discrete, infrequent, and well-telegraphed. The lag captures 90%+ of the surprise content. Minimal information loss.
- **SUAMECA (intervention) -> omit:** Adequate given that T7 tests beta stability with/without I_t. If T7 shows material instability, omission introduces confounding. But intervention weeks are rare (~5-10% of sample), so the bias is bounded.

**Fix:** For BanRep consensus, add Bloomberg/Refinitiv as a hard fallback before AR(1). If both Bloomberg and BanRep survey fail, flag the CPI surprise variable as degraded and widen confidence intervals by the estimated EIV bias factor.

## 7. CPI vs PPI scale incompatibility

**BLOCK (downgraded to NIT) | Section 4.1, lines 151-154**

beta_1 (standardized CPI surprise, unit = standard deviations) and beta_2 (raw delta-IPP, unit = percentage points MoM) are on incommensurable scales. Comparing magnitudes directly is invalid. However, the spec correctly states the comparison is about sign and relative significance ("if beta_1 >> beta_2"), not about coefficient magnitude equality. The real issue is economic interpretation: a 1-unit change in s_t^{CPI} means "1 SD of CPI surprise" while a 1-unit change in delta-IPP means "1 pp MoM PPI change" -- these are not comparable shocks. **Fix (NIT):** Standardize delta-IPP the same way: (delta-IPP - mean) / sigma. Then both coefficients measure "vol response to a 1-SD shock" and are directly comparable. This is trivial to implement and makes the CPI-vs-PPI comparison meaningful.

---

**Summary:** Two specification errors require correction before estimation (sqrt(RV) theoretical claim, GARCH-X non-negativity). Three items need documentation fixes or additional sensitivity runs. The core identification strategy is sound, the bias analysis is honest, and the Layer 1/Layer 2 separation is appropriate.
