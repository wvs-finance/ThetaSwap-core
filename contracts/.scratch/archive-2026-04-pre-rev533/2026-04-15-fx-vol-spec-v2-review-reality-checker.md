# Reality Checker Review: FX-Vol CPI-Surprise Spec v2

**Verdict: NEEDS WORK** -- 2 BLOCKs, 3 FLAGs, 2 NITs. Not Phase 5 ready.

---

## 1. UNVERIFIED data vs "Ready for Phase 5" -- BLOCK

The spec flags 3 data sources as UNVERIFIED (BanRep consensus, IBR-implied rate, SUAMECA intervention) and simultaneously claims Rev 2 status implying readiness. These contradict. The fallbacks listed (AR(1) proxy, lag of policy rate, omit intervention) are not trivial substitutions -- each changes the econometric model's identification. AR(1) proxy for CPI consensus is a DIFFERENT variable than survey expectations; omitting intervention removes a control that be_1171 considers essential (their section 3 treats it as structural). The spec must either verify these sources and confirm machine-readable access, or re-derive identification under the fallback variables, BEFORE claiming any phase-readiness.

## 2. Layer 1 to Layer 2 mapping gap -- BLOCK

Section 4.5 is admirably honest about the total-vol vs differential-growth disconnect. But "deferred to post-beta" makes beta estimation an academic exercise disconnected from product validation. If beta > 0 but arb flow distributes uniformly across ticks, U_RAN = 0 and the hedge is worthless. The spec should state explicitly: "Layer 1 beta is a NECESSARY condition test only; it cannot validate the product without Layer 2." Currently the gate (adj-R2 >= 0.15, beta != 0) reads as if passing it means something for the product. It does not, alone. The gate language in section 1 must be amended to say "necessary but not sufficient."

## 3. Beta comparability in co-primary decomposition -- FLAG

Section 4.1 says "if beta_1 >> beta_2: CPI dominates." But beta_1 is on standardized CPI surprise (mean-zero, unit-variance by construction per ABDV 2003 eq in be_1171 section 2.4) while beta_2 is on raw month-on-month PPI change (no consensus, no standardization). These coefficients are on different scales. Comparing magnitudes directly is meaningless. The spec must either standardize both regressors or compare standardized coefficients (beta * sigma_x). This is a first-year econometrics error dressed up in structural language.

## 4. Oil control functional form -- FLAG

The spec adds weekly WTI/Brent log-return. But Colombia's fiscal channel runs through oil PRICE LEVEL: government revenue, Ecopetrol dividends, and current account depend on whether oil is at $40 or $120, not on whether it moved 2% this week. Weekly return can be zero at vastly different price levels with opposite COP implications. The correct control is either log(oil price level) or both level and return. be_1171 itself uses returns because it operates at 5-minute intraday frequency where level vs return distinction vanishes. At weekly frequency it does not vanish.

## 5. Ambiguous net-bias characterization -- FLAG

Section 3.4 says net bias is "AMBIGUOUS" because stale consensus may bias beta upward while measurement error attenuates. This is more honest than claiming pure attenuation -- but the spec does not acknowledge the consequence: if you cannot sign the bias, you cannot claim beta-hat is conservative for the product NOR that it overstates. The confidence interval around beta carries unknown systematic error in an unknown direction. The spec should state this makes the adj-R2 gate WEAKER (not just that the safety claim "does not hold unconditionally") because even a passing gate may reflect upward-biased beta.

## 6. Two-sided T3 vs one-sided product gate -- NIT

Changing to two-sided beta != 0 is statistically correct. But the product gate should remain one-sided: if beta < 0 (surprise DECREASES vol), the hedge mechanism reverses and the product fails. The spec should separate the statistical test (two-sided, honest) from the product gate (one-sided, beta > 0 required). Currently T3 conflates both. Add: "If T3 rejects with beta < 0, the product hypothesis fails regardless of statistical significance."

## 7. GARCH-X as A7 -- NIT

GARCH is the workhorse of the entire Colombian FX-vol literature. be_1171 section 3.1 uses GARCH(1,1) for identification. Burying GARCH-X as the seventh alternative specification understates its importance. It should be A1 or co-primary. If OLS on weekly RV and GARCH-X on daily returns disagree, which do you trust? The spec does not say.

---

**Reality Checker**: TestingRealityChecker
**Date**: 2026-04-16
