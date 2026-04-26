# Model QA Review: Econ Notebook Design (2026-04-17)

**Reviewer:** Model QA Specialist
**Scope:** Econometric methodology correctness
**Design under review:** `docs/superpowers/specs/2026-04-17-econ-notebook-design.md`
**Upstream authority:** `notes/structural-econometrics/specs/2026-04-15-fx-vol-cpi-surprise.md` (Rev 4)

---

## 1. Specification Fidelity — NEEDS FIX

**Evidence:** Design §7 item 3 (line 149) names "Column 6 = pre-committed primary" with "Newey-West HAC(4)". Rev 4 §4.1 (line 28) specifies 5 controls after CPI surprise: `s^{US CPI}, s^{BanRep}, VIX, I_t, r^{oil}`. Design §4.4 (line 74) states "β̂ on CPI surprise + 5 controls" which matches spec. HAC(4) matches Rev 4 §4.2 (line 192). LHS naming `RV^{1/3}` matches Rev 4 §1 (line 20, 28).

**Issue:** The user prompt claims "6 controls" but Rev 4 lists 5 (US CPI, BanRep, VIX, I, oil). Design correctly encodes 5. However, design §7 item 4 labels diagnostics as "displayed, not branching" — Rev 4 §5 T5 (line 262) says JB rejection triggers Student-t (R3); treating as "displayed" without branching deviates from Rev 4 unless Student-t is unconditionally re-estimated. Design §7 item 5 does unconditionally re-estimate Student-t, resolving the tension — but the handoff JSON in §4.4 omits the Student-t fit. **Fix:** add `ols_student_t` block to `nb2_params_point.json`.

---

## 2. GARCH(1,1)-X Correctness — APPROVED

**Evidence:** Design §7 item 6 (line 152) names `|s_t^CPI|` in the variance equation, cites Han-Kristensen 2014, and specifies BFGS + 500-iter ceiling + Hessian PD check. Matches Rev 4 §6.2 A7 (line 290) verbatim. QMLE fallback on JB-reject per Bollerslev-Wooldridge 1992 is implicitly covered by design §5.3 ("JB-fallback trials happen in Analytics Reporter's private scratch") but the fallback rule must surface in the published notebook, not scratch.

**Minor:** Design §7 item 6 should explicitly state "QMLE SEs reported if JB rejects standardized residual normality" to match Rev 4 §6.2 A7. **Fix:** one-line addition to §7 item 6.

---

## 3. Reconciliation Protocol — APPROVED

**Evidence:** Design §4.4 (line 78) and §7 item 10 (line 156) implement Rev 4 §1 (line 43) protocol: AGREE within ±1 SE feeds mean/variance separately; DISAGREE → both bands to Layer 2. Design §7 item 9 (line 155) correctly isolates T3b as OLS-primary-only with explicit "GARCH-X cannot override" note, matching Rev 4 §5 T3b (line 260, "PRE-COMMITTED PRIMARY spec only"). Proper treatment of the asymmetric gate.

---

## 4. Test Grouping (NB3 §8) — NEEDS FIX

**Evidence:** Design §8 orders groups as: Residual (T4, T5) → Stability (T6, T7) → Effect (T3a) → Variance (T2) → Exogeneity (T1). Two methodological issues:

1. **T1 ordering**: Consensus rationality (T1) is an identification pre-condition. If T1 fails, β is biased and all downstream tests are conditional on a biased estimator. T1 should run **first**, not last. Rev 4 §5 lists T1 first for this reason.
2. **T7 placement**: T7 (intervention control adequacy) is an exogeneity/omitted-variable diagnostic on `I_t`, not a stability test. Grouping it with T6 (Chow/Bai-Perron structural break) conflates regime stability with control-variable adequacy.

**Fix:** Reorder NB3 §8 as: (a) Exogeneity/ID (T1), (b) Channel existence (T2), (c) Residual diagnostics (T4, T5), (d) Stability (T6), (e) Control adequacy (T7), (f) Effect sign (T3a re-ref). T3b stays in NB2 as noted.

---

## 5. Sensitivity Completeness — APPROVED

**Evidence:** Design §8 item 7 (line 176) forest plot enumerates primary + GARCH-X + decomposition (CPI, PPI) + 3 subsamples + A1, A4, A5, A6, A8 = 11 rows (primary counts as row 1). A9 noted as open question (§12). A2/A3/A7 cross-referenced to NB2 is correct — they are co-primary/regime estimates, not re-runs. Treatment matches Simonsohn et al. 2020 specification-curve convention.

**Minor:** Design §8 says "12 rows" but enumerates 11 explicit plus A9 (deferred). **Fix:** clarify count contingent on A9 two-row rendering.

---

## 6. Material-Mover Rule — NEEDS FIX

**Evidence:** Design §8 item 8 (line 182) locks rule as "β̂ outside primary's 90% CI". Under a one-sided pre-committed gate (T3b requires lower bound > 0), this rule has a known failure mode:

**Edge case:** If primary CI straddles zero (T3b already fails), every sensitivity that pushes β̂ positive becomes a "material mover" even though the headline has already failed — inflating the spotlight table and obscuring the failure. Conversely, if primary CI is entirely positive and narrow, a sensitivity producing β̂ = 2·primary but still within a one-sided upper band is flagged as material when it actually reinforces the result.

**Fix:** condition the rule: "β̂ outside the 90% CI **AND** disagrees on T3b sign/significance classification". This matches I4R 2024 two-pronged rule the design cites, rather than the collapsed form.

---

## 7. Subsample Regime Semantics — APPROVED

**Evidence:** Splits (pre-2015-01-05 / 2015-01-05–2021-01-04 / post-2021-01-04) align with BanRep IT regime chronology and COVID structural break — economically motivated. Design §7 item 8 specifies Wald test for pooling. Rev 4 §6.1 S3 (line 276) lists same regime tripartite. Wald-test-for-pooling is standard (asymptotic χ² on stacked-regression equality of β across regimes).

**Caveat (Info):** small-sample Wald tests with HAC can over-reject. Recommend reporting both Wald and equivalent F-test; but not blocking.

---

## 8. Layer 2 Handoff Covariance — NEEDS FIX

**Evidence:** Design §7 item 11 + §4.4 serialize full Σ̂ for `N(θ̂, Σ̂)` draws. Two concerns:

1. **Gaussian draws for QMLE GARCH-X parameters are suspect**: α₁ + β₁ is bounded above by 1 (covariance stationarity); Gaussian draws will violate the bound with non-trivial probability at realistic persistence (α+β ≈ 0.97 in Colombian FX). Parametric bootstrap or truncated Gaussian is required.
2. **HAC-robust OLS coefficients** are fine under Gaussian draws for the mean (asymptotic normality holds under HAC), but joint draws across OLS and GARCH-X parameters assume **independence** not stated in the design — Σ̂ is block-diagonal by construction since the two fits are separate.

**Fix:** (a) document that draws are block-diagonal by estimator; (b) replace GARCH-X Gaussian draws with either (i) parametric bootstrap from fitted standardized residuals or (ii) truncated Gaussian enforcing α+β < 1 and ω, α, β, δ > 0. Student-t tails on the OLS block are not required (HAC + asymptotic normality handles it), but should be considered if JB rejects strongly.

---

## 9. Bootstrap-Sleeve vs Plug-In — APPROVED WITH CHANGES

**Evidence:** Design §7 bottom note (line 160): "K=500 parameter vectors drawn in Layer 2 itself, not pre-drawn in NB2." Citing Barone-Adesi et al. 2008 JBF is appropriate for filtered historical simulation. Plug-in headline with Layer 2 sleeve is methodologically honest — the NB2 gate verdict uses point estimates with HAC SE, not bootstrap.

**Concern:** if Layer 2's sleeve reveals the RAN payoff distribution is highly non-linear in β (likely — the CLAMM payoff depends on tick-concentration ratios), bootstrap uncertainty should be propagated **upstream into the gate verdict**, not only into downstream scenarios. Recommend adding a **confirmatory** non-parametric block bootstrap (Politis-Romano stationary bootstrap, 4-week block, B=1000) in NB2 to sanity-check HAC SE on β̂. If block-bootstrap 90% CI agrees with HAC 90% CI → plug-in is fine. If they diverge → flag in gate verdict.

**Fix:** add NB2 §3.5 "Block bootstrap confirmation of HAC SE" with agreement check. Does not change headline; raises red flag if HAC is misleading.

---

## Top-Level Verdict: APPROVED WITH CHANGES

Design correctly implements Rev 4's pre-committed primary, GARCH-X co-primary, reconciliation protocol, and three-regime subsamples. Five non-blocking fixes required:

1. Add `ols_student_t` block to `nb2_params_point.json` (§1).
2. Surface QMLE-fallback rule in the published NB2 cell, not scratch (§2).
3. Reorder NB3 §8: T1 first, separate T6 stability from T7 control adequacy (§4).
4. Tighten material-mover rule to two-pronged CI+sign/significance (§6).
5. Replace GARCH-X Gaussian draws with parametric bootstrap or truncated Gaussian; document block-diagonal Σ̂ (§8); add NB2 block-bootstrap confirmation of HAC SE (§9).

No blockers. Design is ready for Code Reviewer + Technical Writer passes and implementation planning after these fixes land. Reconciliation protocol, LHS transform, HAC lag, controls count, regime splits, and Layer 1/Layer 2 separation are all correct.

---
**QA Date:** 2026-04-17
**Next review:** post-fix diff + Reality Checker pass
