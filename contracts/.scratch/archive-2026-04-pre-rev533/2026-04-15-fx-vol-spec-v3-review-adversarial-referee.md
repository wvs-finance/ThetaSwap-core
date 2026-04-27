# Adversarial Referee Report: Rev 3 of FX-Vol-CPI-Surprise Spec

**Date:** 2026-04-16
**Verdict:** MINOR REVISION

---

## 1. GARCH-X promoted to co-primary — MINOR

The GARCH-X equation in section 4.1 is genuinely specified: mean equation, variance equation with lag structure (GARCH(1,1)), |s_t^CPI| entry, asymmetric extension (delta+/delta-), Gaussian innovation distribution, MLE estimation. This is real promotion, not cosmetic. However: no convergence criteria are stated (e.g., gradient tolerance, max iterations, what to do if MLE fails to converge on N~1100 weekly obs with 5 regressors in the mean equation). No mention of QMLE robustness if z_t is non-Gaussian. Fix: add one sentence on QMLE + Bollerslev-Wooldridge robust SEs as fallback.

## 2. |s_t| consistency — SUGGESTION

Section 4.1 correctly uses |s_t^CPI| in the GARCH-X variance equation with explicit justification (Rev 3 fix note). However, section 6.2 A7 still contains "$\delta \cdot s_t^{\text{CPI}}$" WITHOUT absolute value bars. This is the original s_t leaking through in the alternatives table. The A7 row contradicts the co-primary equation 15 lines above it. Minor but could confuse an implementer.

## 3. RV^{1/3} cube-root downstream propagation — MINOR

Section 4.1 and 4.3 correctly state three co-primary LHS transforms with cube-root as Rev 3 primary. But the section 4.3 equation table (line 183) still reads "Three co-primary LHS transforms: log, sqrt, identity" -- listing SQRT, not cube-root. This is a direct contradiction with section 4.1 which specifies {(.)^{1/3}, log(.), identity}. The sqrt reference is a Rev 1 fossil. Section 5 (T5) references "Log-transform works" which is acceptable since log is still an exploratory LHS. Section 6 alternatives are clean. One stale reference, but it is load-bearing (the data dictionary row).

## 4. Falsifiable 10% tick-concentration threshold — MAJOR

The 10% one-sided difference in g(i_S)/g(i_T) between surprise and non-surprise weeks (section 4.5) has no scientific basis stated. Why not 5%? Why not 20%? The spec provides no power calculation, no economic derivation, and no reference for this number. A referee would ask: "What is the minimum detectable effect size given your expected Layer 2 simulation sample?" Without that, the threshold is arbitrary and the falsifiability is indeed theater -- it looks testable but the number was chosen to sound reasonable rather than derived from the economics or the statistical design. This needs either (a) a power calculation justifying 10%, or (b) honest language: "we pre-register 10% as our threshold; sensitivity to 5% and 20% will be reported."

## 5. "Necessary but not sufficient" consistency — SUGGESTION

Section 4.5 uses the gate language correctly and explicitly. Section 5 T3b says "beta > 0" is a "product gate" and "economic requirement" -- consistent with necessity, and the reject-arrow says "product thesis fails," not "hedge works." No backsliding detected. The language is clean throughout.

## 6. Specification count — MINOR

Counting total estimable specifications: 3 LHS transforms (cube-root, log, raw) x 1 primary surprise construction x 2 estimation approaches (OLS, GARCH-X) = 6 co-primary. Plus: 1 CPI/PPI decomposition x 3 LHS = 3 more. Plus AR(1) fallback surprise x 3 LHS x 2 methods = 6. Plus 9 alternatives (A1-A9). Plus asymmetric GARCH extension. That is roughly 6 + 3 + 6 + 9 + 1 = 25 estimable specifications. This is well past the ~10 threshold. The spec needs a pre-registration hierarchy: (1) declare ONE primary test for the gate decision (e.g., cube-root OLS with CPI surprise), (2) label everything else as confirmatory or exploratory, (3) apply multiple-testing correction to the gate. Without this, a serious referee will flag p-hacking risk.

## 7. Status line accuracy — MINOR

"Phase 5 UNBLOCKED" is misleading. The status line itself says "series ID to confirm in catalog" for SUAMECA intervention data. An unconfirmed series ID means Phase 5 data pipeline cannot start for the I_t variable. This is a soft block, not unblocked. Accurate status: "Phase 5 CONDITIONALLY UNBLOCKED -- SUAMECA series ID confirmation outstanding."

---

**Summary:** The Rev 3 fixes are mostly genuine, not cosmetic. The GARCH-X promotion, |s_t| fix, and necessary-but-not-sufficient gate are real improvements. Three issues require revision: (1) the sqrt fossil in the section 4.3 table, (2) the unjustified 10% threshold, and (3) the specification count needs a pre-registration hierarchy to survive peer review. The status line overstates readiness.
