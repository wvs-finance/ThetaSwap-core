# Model QA Review: FX Vol CPI Surprise Specification

**Spec:** `specs/2026-04-15-fx-vol-cpi-surprise.md`
**Reviewer:** Model QA Specialist
**Date:** 2026-04-16

## VERDICT: APPROVE_WITH_CHANGES

Three blocking issues must be resolved before estimation. Two flags require documentation or sensitivity analysis. One nit.

---

### 1. BLOCK | Section 4.1 | log(RV) normality does not hold with 5 daily returns

The spec cites ABDE 2001 to justify log(RV) as approximately Gaussian. ABDE 2001 derives this result for RV computed from hundreds of intraday returns per day (5-min sampling, ~78 observations/day). With RV_t = sum of 5 squared daily log-returns per week, the CLT argument that makes log(RV) Gaussian does not apply. At n=5, the chi-squared-like distribution of RV is severely right-skewed even after log-transform. Jarque-Bera (T5) will likely reject, but the spec treats Student-t MLE (R3) as a fallback rather than recognizing that the primary specification's theoretical justification is invalid.

**Fix:** (a) Demote log(RV) from "primary justified by ABDE 2001" to "exploratory transform." (b) Elevate level-RV (R1) to co-primary. (c) Add a third functional form: sqrt(RV), which stabilizes variance of chi-squared-family variables better than log at small n. (d) Make T5 a pre-estimation diagnostic that determines the functional form, not a post-hoc check.

### 2. BLOCK | Section 4.4 | ABDV 2003 identification breaks at weekly frequency

ABDV 2003 identifies macro-announcement effects using narrow intraday windows (5-min to 30-min) where the exclusion restriction -- only the scheduled announcement moves prices in that window -- is credible. At weekly aggregation, this exclusion restriction fails: oil price shocks, political events, global risk repricing, and concurrent non-DANE macro releases all contaminate the same week. The spec acknowledges this in Section 3.1 ("concurrent non-DANE news... residual in epsilon") but still claims identification via ABDV 2003. The controls (US CPI, BanRep rate, VIX, intervention) absorb some confounders but not oil, politics, or EM contagion.

**Fix:** (a) Add WTI weekly return or Brent as a 6th control -- Colombia is an oil exporter and COP/USD is heavily oil-correlated (be_1171 intro and Rincon-Castro 2021 identify oil as a key FX shock source). (b) Reframe identification as "conditional exogeneity given controls" rather than ABDV 2003 event-study identification. (c) Consider the Altavilla-Giannone-Modugno 2017 two-step approach (already cited for Rincon-Torres 2023) that explicitly filters high-frequency announcement responses and projects them to lower frequencies.

### 3. BLOCK | Section 4.3 | CPI+PPI composite surprise is incoherent

The spec defines s_t^price as a "CPI+PPI composite" but Section 4.3 reveals CPI enters as (release - consensus) while PPI enters as raw delta-IPP because PPI has no consensus forecast. These are different objects: a standardized surprise vs. an arbitrary level change. Summing or averaging them produces a variable with no clean economic interpretation. If PPI delta-IPP is large in magnitude relative to the CPI surprise, it will dominate beta and the parameter will not measure "price-level surprise" as claimed.

**Fix:** (a) Make CPI-only surprise the primary specification. (b) Move decomposition (A2: separate beta_CPI and beta_PPI) from sensitivity to primary. (c) If a composite is still desired, normalize delta-IPP by its own historical standard deviation before combining -- but document that PPI "surprise" is actually PPI "change" and the exclusion restriction is weaker for PPI (no consensus to guarantee orthogonality).

### 4. FLAG | Section 4.2 | Newey-West lag = 4 may be insufficient

Lag = 4 weeks covers one CPI release cycle, but Rincon-Torres 2023 documents quarterly persistence in Colombian macro-news effects on asset prices (R-squared rises from <10% daily to 34% quarterly). If the vol response to CPI surprise persists beyond 4 weeks, the HAC estimator underestimates the true long-run variance. The Andrews 1991 automatic bandwidth selector or Newey-West 1994 data-driven lag would be more defensible than a fixed lag.

**Fix:** Report results at lag = 4 (primary) and lag = 12 (quarterly robustness). Add Andrews automatic bandwidth as a third option. Flag in the spec that if SEs change materially between lag 4 and lag 12, the model has a persistence problem that OLS+HAC cannot fully resolve and an ARMA error structure (per T4 fallback) should become primary.

### 5. FLAG | Section 1 + 5 | Power analysis missing for the adj-R-squared gate

N ~ 260 release weeks with 5 regressors + 1 intervention dummy leaves ~254 residual df. The tau_op = 0.15 adj-R-squared gate is applied out-of-sample, but the spec does not document the train/test split, cross-validation scheme, or power calculation. With a population partial R-squared of 0.10 for beta (plausible given Rincon-Torres 2023 adjacent-asset bound), the non-centrality parameter for an F-test at n=260, p=6 gives power > 0.99 for detecting beta != 0 at alpha = 0.05. So power for significance is fine. But the GATE is adj-R-squared >= 0.15 out-of-sample, which is a harder target. Without specifying the OOS evaluation protocol (rolling window? single holdout? k-fold?), the gate is ambiguous.

**Fix:** Specify OOS protocol explicitly: recommend expanding-window with 70/30 initial split and rolling 1-year OOS windows. Document that adj-R-squared >= 0.15 is evaluated on the pooled OOS residuals, not on any single fold.

### 6. NIT | Section 5 | T2 tests the wrong null for the announcement channel

T2 uses a Levene test for Var(RV | release) > Var(RV | non-release). This tests whether the VARIANCE OF RV differs across regimes, not whether the LEVEL of RV differs. The announcement channel predicts E[RV | release] > E[RV | non-release] (higher average vol in release weeks), not necessarily higher dispersion of vol. A two-sample t-test on log(RV) or a Wilcoxon rank-sum test would be more appropriate.

**Fix:** Replace Levene with a one-sided Wilcoxon rank-sum test on RV (or t-test on log(RV) if normality holds). Retain Levene as a supplementary diagnostic for heteroskedasticity across regimes.

---

**Summary of required changes before proceeding to estimation:**

| # | Severity | Fix |
|---|----------|-----|
| 1 | BLOCK | Demote log(RV) justification; add sqrt(RV); make T5 pre-estimation |
| 2 | BLOCK | Add oil control; reframe identification away from ABDV 2003 |
| 3 | BLOCK | Separate CPI and PPI; do not combine unstandardized variables |
| 4 | FLAG | Report HAC at lag 4 and lag 12; add Andrews automatic bandwidth |
| 5 | FLAG | Specify OOS evaluation protocol for the adj-R-squared gate |
| 6 | NIT | Replace Levene with Wilcoxon rank-sum in T2 |
