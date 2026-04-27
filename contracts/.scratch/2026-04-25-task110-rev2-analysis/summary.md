# Summary — Task 11.O Rev-2 Phase 5b Analytics Reporter

**Spec:** `contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md`  
**Phase 5a artifacts:** `contracts/.scratch/2026-04-25-task110-rev2-data/` (commits `2eed63994`, reviews `777596b8e`)  
**Phase 5b output:** `contracts/.scratch/2026-04-25-task110-rev2-analysis/`  

---

## Headline gate verdict

- **T3b primary on Row 1:** **FAIL**
- **β̂ (X_d coefficient):** -2.799e-08
- **SE (HAC(4)):** 1.423e-08
- **t-statistic:** -1.966
- **One-sided 90% lower bound (β̂ − 1.28·SE):** -4.621e-08
- **Sample size n:** 76 (pre-committed = 76, MATCH)
- **Bootstrap reconciliation (Row 2):** **AGREE** with HAC at 50% containment-ratio threshold

## Pre-registered FAIL confirmation

- **Row 3 (LOCF-tail-excluded; n=65 < N_MIN=75):** FAIL (actual gate = FAIL)
- **Row 4 (IMF-IFS-only; n=56 < N_MIN=75 AND power=0.7301 < 0.80):** FAIL (actual gate = FAIL)

## Specification tests T1–T7 headline

- **T1 (exogeneity, F-test on lagged Y₃ + controls predicting X_d):** REJECTS at 5% (F = 3.480, p = 0.0031). β̂ is **PREDICTIVE**.
- **T2 (variance premium):** fails to reject (Levene p = 0.2038)
- **T3a (two-sided gate):** REJECTS at 5% (p = 0.0493)
- **T3b (one-sided gate, α = 0.10):** **FAIL**
- **T4 (Ljung-Box serial correlation):** lag-4 p = 0.5014; lag-8 p = 0.3308
- **T5 (Jarque-Bera normality):** fails to reject (p = 0.6833)
- **T6 (Chow break at Carbon-launch):** NOT IDENTIFIED on this panel (F = NaN)
- **T7 (parameter stability primary vs parsimonious):** diverges > 1·SE

---

## Anti-fishing audit invariants (spec §9 — verbatim verification)

| # | Invariant | Status |
|---|---|---|
| 1 | No silent threshold tuning (N_MIN=75, POWER_MIN=0.80, MDES_SD=0.40, MDES_FORMULATION_HASH = `4940360dcd29…cefa`) | preserved |
| 2 | Pre-registered FAIL sensitivities reported regardless of primary outcome (Row 3 = FAIL; Row 4 = FAIL) | preserved |
| 3 | Pre-registered sign β > 0 locked at Rev-2 commit; sign-flip rescue anti-fishing-banned | preserved |
| 4 | No mid-stream X_d swap (primary locked to `carbon_basket_user_volume_usd`; no post-hoc swap to `b2b_to_b2c_net_flow_usd`) | preserved |
| 5 | Sign-flip transparency: if primary FAILS but a sensitivity passes positive-significant, FX-vol §9 spotlight HALT applies | preserved |
| 6 | MDES formulation hash live-recomputed = match | preserved |
| 7 | No code/plan/spec/admitted-set modification at Rev-2 estimation | preserved |
| 8 | Honest framing of identification weakness (T1 REJECTS → predictive flag) | preserved |


## §11.A Convex-payoff insufficiency caveat (verbatim from spec)

A T3b PASS at the mean-β level is **necessary but NOT sufficient** for convex-instrument pricing. The §1.1 product-purpose framing locates Abrigo's product as convex (option-like) instruments hedging macroeconomic shocks viewed through the inequality lens; convex payoffs (puts, calls, caps, floors) are priced from the **conditional distribution** of Y₃ given X_d — its tails, quantiles, and conditional variance — not from the conditional mean alone. Specifically:

1. **Mean-β identification is first-stage / linear-hedge calibration only.** β̂_X_d × X_d_t at §12 is interpretable as a *forward-like* hedge-leg coefficient for linear-payoff instruments (forwards, swaps, fixed-leg constructs). It is NOT interpretable as an option-pricing parameter without further tail-risk evidence.
2. **Convex-instrument pricing requires CONDITIONAL VARIANCE / QUANTILE / TAIL evidence** — not just mean-shifts. In Black-Scholes basics, the option premium's dominant gradient is vega (∂Premium/∂σ); variance behavior dominates the level. In heavier-tailed frameworks (Heston, Bates, GARCH-X), the option premium is explicitly tail-driven. Mean-β tells you only how the *center* of Y₃'s distribution shifts under X_d — the hedge buyer pays for tail behavior, not center behavior.
3. **This Rev-2 spec consciously defers tail-risk to Rev-3** (see §10.6 ζ-group roadmap: quantile regression β̂(τ), GARCH-X conditional-variance, lower-tail conditional regression, option-implied-vol surface fitting). The Q-1b α+β-only ruling applied to Rev-2 scope; it does not preclude Rev-3 from re-introducing distributional-welfare evidence (quantile shifts, variance amplification, lower-tail stabilization) that the convex-instrument purpose analytically requires.
4. **Honest interpretation of the T3b PASS result:** "Y₃'s mean shifts with X_d in a direction consistent with the linear-hedge thesis" — NOT "Abrigo can price options from this β̂." A future engineer wiring β̂ into a convex-payoff pricer would miscalibrate the product. The simulator-pricing claim at §12 is therefore valid only for *linear-payoff* hedge instruments; convex payoffs require Rev-3 ζ-group evidence before any pricing-model calibration.

This caveat is the load-bearing product-validity disclosure for Rev-2: mean-β identification is the **first stage** of a multi-stage product-validity test; Rev-2 ships the first stage cleanly, and the §10.6 ζ-group is the explicit Rev-3 dependency that closes the convex-instrument calibration gap.


## Pivot paths (since T3b primary FAILED)

Per spec §11.B (Scenario B) and §11.C (Scenario C):

- **Rev-3 ζ-group extensions** (spec §10.6) — the natural next step:
  - ζ.1 Quantile regression β̂(τ) at τ ∈ {0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95}
  - ζ.2 GARCH(1,1)-X with X_d in the conditional-variance equation
  - ζ.3 Lower-tail conditional moment regression
  - ζ.4 Option-implied volatility surface fitting
- **Pivot to brainstorm-α (payments/consumption)** per `project_phase_a0_exit_verdict`
- **Pivot to brainstorm-β** (yet-to-be-defined alternative thesis)

**Anti-fishing discipline:** if any sensitivity row passed positive-significant while the primary failed, the FX-vol §9 spotlight HALT applies — sensitivity stays in the record but cannot be promoted to primary. No silent re-tuning of controls or sample to chase a PASS.



---

## Provenance

- **Spec commit:** `d9e7ed4c8` (655 lines)  
- **Phase 5a panels commit:** `2eed63994`; reviews `777596b8e`  
- **Phase 5a verification:** live joint-nonzero counts (76/65/56/45/47) byte-exact match spec.  
- **MDES formulation hash:** `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` (PRESERVED).  
- **TDD evidence:** `scripts/tests/inequality/test_phase5b_analytics.py` (16 passed, 1 schema-conformance check on `gate_verdict.json`).  
- **Estimation kernel:** `scripts/phase5_analytics.py` (frozen dataclasses; free pure functions; full typing per `functional-python` skill).  
- **Orchestrator (this script):** `scripts/run_phase5_analytics.py`.  

