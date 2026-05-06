---
emitted_at_utc: 2026-05-06T09:34:22+00:00
emitted_from: notebooks/03_tests_and_sensitivity.ipynb (Trio 6 — §5.5 escalation suite)
spec_decision_hash: 7c72292516f58f3cf2d16464d4f84c3e7d7270ad2c5d3d8ed8fef6b3b2751f5a
plan_tag: v1.1.1
panel_n: 134
window: 2015-01 → 2026-02
anti_fishing_framing: pre-pinned convex-payoff evidence test (per spec §9.6); NOT post-hoc rescue
---

# ESCALATION_RESULTS — Trio 6 §5.5 escalation suite (D-i / D-ii / D-iii)

Spec v1.0.2 §5.5 escalation methodology + §3.4 ESCALATE-PASS disjunction. Per spec §9.6 the suite is PRE-AUTHORIZED co-primary convex-payoff evidence; framing is **pre-pinned convex-payoff evidence test, ran whether or not mean-OLS passed** — anti-fishing-banned to call this a rescue claim. Pair D Stage-1 precedent (`project_pair_d_phase2_pass`): same suite pre-authorized at the same numerics; Pair D PASSed mean-OLS and did not need to invoke the suite, but the inheritance is verbatim.

**Sign anchor (re-fit primary OLS):** `β_composite_primary = -0.14613187` (sign = −).

## §1 — D-i: quantile regression τ=0.90 (spec §5.5 D-i + §3.4 D-i)

**Specification (verbatim from spec §5.5 D-i + §3.4 D-i).** Conditional quantile regression of `Y_t (logit)` on the three lagged-X regressors (`X_lag6`, `X_lag9`, `X_lag12`) plus intercept, estimated at `τ = 0.90`. Per §3.4 D-i the threshold trigger evaluates the lag-9 coefficient `β_qr_lag9 (τ=0.90)` (spec-pinned 'representative middle-of-window lag') against `> 0` AND one-sided `p ≤ 0.10`.

**Numerics.**
- `β_qr_lag9 (τ=0.90)` = `-0.12886752`
- `SE_qr_lag9` = `0.34682126`
- `t-stat_qr_lag9` = `-0.371568`
- `p_one_qr_lag9` = `6.44590116e-01`
- `β_qr_composite (info)` = `-0.16574352` (sum of three lag coefficients; for cross-reference)
- sign match primary: `False` (`sign_primary` = -1, `sign_qr_lag9` = -1)

**§3.4 D-i α = 0.10 threshold evaluation:** `FAIL` (requires `β > 0` AND `p_one ≤ 0.10`).

## §2 — D-ii: GARCH(1,1)-X (spec §5.5 D-ii + §3.4 D-ii)

**Specification (verbatim from spec §5.5 D-ii + §3.4 D-ii).** GARCH(1,1) on `Y_t (logit)` with the three lagged-X regressors (`X_lag6`, `X_lag9`, `X_lag12`) entering the mean equation as exogenous covariates. Composite GARCH-X β = sum of three lag mean-equation coefficients. Per §3.4 D-ii the threshold trigger evaluates the composite β against `> 0` AND one-sided `p ≤ 0.10`.

**Numerics.**
- `β_garch_lag6` = `+0.16692419` (logit-Y units, post-rescaling from y_scale=100 optimizer convenience)
- `β_garch_lag9` = `-0.20494792`
- `β_garch_lag12` = `-0.11570095`
- `β_garch_composite` = `-0.15372468`
- `SE_garch_composite` = `0.06202507` (linear-restriction SE via param covariance)
- `t-stat_garch_composite` = `-2.478428`
- `p_one_garch_composite` = `9.93401861e-01`
- sign match primary: `False` (`sign_primary` = -1, `sign_garch` = -1)

**§3.4 D-ii α = 0.10 threshold evaluation:** `FAIL` (requires `β > 0` AND `p_one ≤ 0.10`).

## §3 — D-iii: EVT POT (spec §5.5 D-iii + §3.4 D-iii)

**Specification (verbatim from spec §5.5 D-iii + §3.4 D-iii).** Peaks-over-threshold on upper-tail residuals from the primary OLS at empirical 0.90 residual quantile threshold; exceedances regressed on `log(COP_USD_{t-9})` (= `X_lag9` per env.py panel-construction convention). Per §3.4 D-iii the threshold trigger evaluates the regression coefficient against `> 0` AND one-sided `p ≤ 0.10`.

**Numerics.**
- Primary residual range: `[-0.472197, +0.331884]`
- Threshold u (0.90 quantile): `+0.17732437`
- N exceedances: `14` of `134` (10.4%)
- GPD shape ξ (informational): `-0.797986` (positive ⇒ heavy-tail; near-zero ⇒ exponential-tail; negative ⇒ bounded-tail)
- GPD scale (informational): `+0.126430`
- `β_pot (exceedance ~ X_lag9)` = `+0.11337993`
- `SE_pot` (HC3-robust) = `0.05044813`
- `t-stat_pot` = `+2.247456`
- `p_one_pot` = `1.23054616e-02`
- sign match primary: `False` (`sign_primary` = -1, `sign_pot` = +1)

**§3.4 D-iii α = 0.10 threshold evaluation:** `FAIL` (requires `β > 0` AND `p_one ≤ 0.10`).

## §4 — §3.4 ESCALATE-PASS disjunction status

Per spec §3.4 verbatim: *ESCALATE-PASS fires if any one or more of the three disjuncts hold; otherwise ESCALATE-FAIL.* Per §3.4 structural-disjunction MHT defense: each disjunct estimates a *distinct distributional-moment parameter* (D-i upper-tail conditional response; D-ii conditional-mean under time-varying-volatility; D-iii extreme-residual covariation) mapping to a *distinct convex-instrument design family* (D-i range-LP / covered-call; D-ii volatility-conditional perpetual; D-iii tail-risk OTM put); MHT-correction does NOT apply since this is structural-disjunction over distinct parameters, not multiple identical tests on the same parameter.

**Per-disjunct verdicts:**
- D-i quantile τ=0.90: **FAIL**
- D-ii GARCH(1,1)-X composite: **FAIL**
- D-iii EVT POT: **FAIL**

**Disjuncts passing:** `0` of 3.

**§3.4 disjunction verdict:** **ESCALATE-FAIL** (no disjunct fires).

## §5 — §9.6 pre-authorization framing acknowledgment

Per spec §9.6 verbatim: *Escalation as pre-authorization, not post-hoc rescue. The §5.5 + §3.4 escalation suite was pre-authorized in this spec before any data was pulled. Framing escalation in the result memo as 'rescue' is anti-fishing-banned; the framing must be 'pre-pinned convex-payoff evidence test, ran whether or not mean-OLS passed'.* This Trio 6 emission was authored regardless of Trio 5's routing-branch outcome (PASS-with-κ-clear / PASS-with-κ-not-clear / ESCALATE / FAIL); the escalation-suite execution is governed by §9.6 pre-authorization, not by Trio 5's per-row sign-AGREE tally. Pair D Stage-1 precedent (`project_pair_d_phase2_pass`): the same suite was pre-authorized at the same numerics and Pair D's PASS verdict at §3.1 meant Pair D did not invoke the suite — but the *pre-authorization* discipline is verbatim and cross-iteration-binding.

## §6 — Phase-3 result memo + gate_verdict.json integration directive

Per spec §9.17 invariant (Phase-3 result-memo §11.X disclosure pre-pin), the Phase-3 result memo MUST cite this Trio 6 escalation-suite output verbatim in §11.X(b) (3-row R1/R3 + escalation-suite adjudication table) and §11.X(d) (Stage-2 hedge-geometry mapping conditional on which disjunct(s) fire). Per the dispatch contract, NB02 Trio 3 final-status emission of `output/gate_verdict.json` MUST add a top-level field `escalation_results` containing: per-disjunct β + SE + t + p_one + pass-flag; disjunction-verdict label; ESCALATE-PASS-via list; spec-decision-hash + plan-tag pin. The integration directive is binding for Phase 2 closure prior to Phase 2.5 (Economist Analyst framework application).

**End of ESCALATION_RESULTS.**
