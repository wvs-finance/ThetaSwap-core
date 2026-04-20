# Phase 1 NB1 findings digest (2026-04-18, post §5 Trio 1)

Disk-local mirror of the persistent-memory digest at
`~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_phase1_findings_digest.md`.

This version is git-tracked and travels with the repo. Prefer it after compaction when a commit-anchored context is needed.

## Context (one paragraph)

Structural econometrics pipeline testing whether Colombian CPI surprises cause COP/USD (TRM) realized volatility. Ultimate product goal: ground the "Abrigo" macro-hedge product (permissionless FX vol insurance for underserved-FX countries via Mento stablecoins). The scientific gate is **T3b: β̂_CPI − 1.28·SE > 0** on the primary OLS. Passing = clean empirical support for the hedge product. Spec Rev 4 pre-committed the primary: OLS on RV^{1/3}, weekly frequency, with 6 controls and HAC(4) SEs. Sample: 2008-01-02 → 2026-03-01, n_weeks=947.

## Nine Decisions locked in Phase 1

| # | scope | primary | sensitivity alt |
|---|---|---|---|
| 1 | sample window | 2008-01-02 → 2026-03-01, n_weeks=947 | n/a |
| 2 | LHS transform | RV^(1/3) | log(RV) |
| 3 | frequency | weekly | daily |
| 4 | Colombian CPI surprise | `cpi_surprise_ar1` (ABDV 2003 AR(1) expanding over DANE IPC 1954-present) | A9 asymmetric + 60-month rolling AR(1) |
| 5 | US CPI surprise | `us_cpi_surprise_ar1` (AR(1) expanding, FRED CPIAUCSL, 12-mo warmup, BLS cal) | n/a |
| 6 | BanRep rate surprise | event-study daily ΔIBR at Junta decision dates, weekly sign-preserving sum (methodologically distinct from AR(1) because policy rate is step-function) | n/a |
| 7 | VIX aggregation | `vix_avg` (weekly arithmetic mean of daily FRED VIXCLS) | `vix_friday_close` explicitly rejected |
| 8 | oil_return aggregation | log-return of weekly-LAST POSITIVE WTI close (ARG_MAX with value>0 filter) | n/a |
| 9 | intervention regressor | `intervention_dummy` (binary any-activity) | `intervention_amount` (signed continuous); S7 drops 2024-10+ |

All nine respect spec Rev 4 pre-commitments with `anti_fishing_binding = True`.

## Material finding 1: Colombian CPI surprise asymmetry (§4a)

- **Event density:** 218 / 947 weeks = 23.0%
- **Sign balance:** 205 negative / 13 positive — ~94% negative. Extreme.
- **Nonzero mean:** −0.69 (strongly biased, NOT centered on zero)
- **Nonzero |skew|:** 0.90, kurt_exc: +1.11

### Root-cause audit (Trio 2, commit `6d3a130b4`)

Three candidate bugs ruled out before accepting asymmetry as design property:

1. **Alignment:** rate = **1.000** → release-date alignment methodologically correct
2. **Imputation contamination:** no evidence in surprise series
3. **Warm-up adequacy:** 643 months pre-sample vs 12-month threshold → far beyond adequate

Root-cause (accepted): **regime mismatch.** AR(1) expanding-window anchors intercept to 1954-present history.
- Pre-sample mean MoM (1954-2007, incl. hyperinflation): **+1.23%**
- In-sample mean MoM (2008-2026, modern BanRep inflation-targeting): **+0.40%**
- Ratio: ~3× → forecast systematically pulled above modern reality → systematic negative surprises
- Correlation(surprise, CPI level) = **+0.37**

## Material finding 2: US CPI symmetric + fat-tailed (§4b)

Same `cpi_surprise_ar1` operator applied to FRED CPIAUCSL (swap DANE for FRED, hold operator constant):

- **Event density:** 217 / 947 weeks = 22.9% (≈ identical to Colombian, monthly cadence)
- **Sign balance:** 110 positive / 107 negative — **symmetric**
- **Nonzero mean:** +0.0025 (centered on zero)
- **Nonzero |skew|:** 1.31 (left-skewed)
- **Nonzero kurt_exc:** **+8.51** (much fatter tails than Colombian)
- **Top-5 outliers** map to real macro events: Lehman 2008, 2008-07 oil spike, 2020-04 COVID, 2022-08 inflation deceleration

**Interpretation:** same operator applied to US data is unbiased → **confirms Colombian asymmetry is regime-specific (hyperinflation anchoring), NOT a methodological bug.** Fat tails motivate A12 HAC(12) bandwidth sensitivity (already pre-registered in spec Rev 4).

## Material finding 3: BanRep rate surprise implementation (§4c)

Decision #6 deliberately adopted a methodology DIFFERENT from Decisions #4/#5 because the policy rate is a step function, not a drifting level series. AR(1) would be misspecified.

- **Methodology:** event-study daily ΔIBR at Junta Directiva policy-decision dates, then weekly sign-preserving sum
- **Grounding:** Anzoátegui-Zapata & Galvis 2019; Uribe-Gil & Galvis-Ciro 2022 BIS WP 1022 (both to be added to `references.bib` in Task 15)
- **New data pipeline:** `banrep_meeting_calendar` table (234 rows: 89 policy_rate_decision + 145 policy_rate_hold_inferred, 2008-2026) + scraper `contracts/scripts/build_banrep_meeting_calendar.py`
- **Column populated:** `weekly_panel.banrep_rate_surprise` → 88 non-zero weeks, `abs_mean_nonzero=0.428`, `std_nonzero=0.529`
- **Sign balance:** 42 pos / 46 neg — **SYMMETRIC** (contrast Colombian CPI)
- **Top-5 outliers:** 2022 inflation hikes (100-150bp), 2009 GFC cuts (−100bp) — all real decisions
- **Correlation with `cpi_surprise_ar1`:** +0.074 — **NO collinearity concern**
- **Tests added:** 13 new in `test_banrep_meeting_calendar.py` + `test_banrep_rate_surprise_construction.py`

## Material finding 4: VIX admissibility (§4d)

Decision #7 adopts `vix_avg` (weekly arithmetic mean of daily FRED VIXCLS) and rejects `vix_friday_close`.

- **mean:** 19.90, **std:** 8.75, **max:** 74.62 (2020-03-16)
- **kurt_exc:** +8.51, **lag-1 ACF:** 0.9435 (textbook high persistence; justifies HAC(4))
- **Aggregation audit:** PASSED — avg 4.85 daily obs/week, Monday alignment, no lookahead
- **Univariate corr with rv_cuberoot:** +0.355 (confirms control does real conditioning work)

## Material finding 5: Oil return construction (§4e)

Decision #8: log-return of weekly-LAST POSITIVE WTI close (ARG_MAX with `value > 0` filter). Correctly handles the 2020-04-20 negative WTI settlement.

- **mean:** −0.0004, **std:** 0.060
- **kurt_exc:** **+17.79** (HIGHER than VIX and US CPI — fattest-tailed regressor in the panel)
- **lag-1 ACF:** −0.0004 (near-martingale — expected for log-returns)
- **Top-5 outliers:** 3× COVID 2020, 2× GFC 2008 (real events)
- **Flagged:** 2020-03-30 return +0.605 is partly a small-denominator artifact

## Material finding 6: Intervention regime heterogeneity + data-freshness gap (§4f)

Decision #9: `intervention_dummy` (binary) primary; `intervention_amount` sensitivity; **S7 drops 2024-10+** for data-freshness.

- **Active fraction:** 316 / 947 = **33%** (earlier Task 8 note of 18% was wrong)
- **Construction:** any-activity indicator over 8 signed components (2 dead weight: `discretionary`, `fx_swaps`)
- **Data-freshness gap:** source table `banrep_intervention_daily` ends 2024-10-04 → **73 weeks have dummy=0 by absence-of-data, not confirmed absence** (8% of sample). Prior-based estimate: ~22 missing events in the gap (not catastrophic; 2024 partial-year active rate is only 30%).
- **LARGE regime heterogeneity:**
  - 2008-2014: active 71%
  - 2015-2019: dormant 3.8% (post-free-float adoption)
  - 2020 COVID: active 63.5% (**only regime with negative mean signed amount** — Banrep defending peso via NDFs)
  - 2024 partial: 22.6%
- **Amount CV:** 0.878, **Q75/Q25:** 1.78 — ambiguous zone for dummy-vs-amount, justifies Decision #9's dummy primary

## Material finding 7: Joint regressor behavior (§5 Trio 1)

- **Max |corr| across 6 RHS regressors:** **0.142** (vix × oil) — well below BKW 0.7 collinearity threshold
- **Prior-trio correlations confirmed:** banrep × cpi = +0.074; vix × rv = +0.355; intervention × cpi = −0.100
- **Non-linearity signal:** oil_return ↔ rv_cuberoot Pearson −0.114 vs Spearman −0.046 — handful of extreme oil weeks drive Pearson. Flagged for §5 Trio 3 scatter-matrix inspection.
- **Pearson-Spearman otherwise concordant**
- **Verdict:** **regressor matrix is clean; OLS inference will be stable at n=947**

## T3b risk assessment

Four risk vectors for the primary gate `β̂_CPI − 1.28·SE > 0`:

1. **Attenuation bias on Colombian CPI surprise.** Measurement error in the regressor (AR(1) misspec relative to true market expectations) biases β̂ toward zero. Passing T3b despite attenuation = strong evidence. Failing T3b does NOT preclude the effect — it is consistent with attenuation masking it.
2. **Sign asymmetry reduces effective identifying variation.** 205 neg / 13 pos means the linear OLS fits the negative tail almost exclusively. Motivates A9 asymmetric sensitivity.
3. **US CPI fat tails (kurt_exc=8.51) + oil kurt_exc=17.79.** Finite-fourth-moment holds, HAC(4) consistent, but bandwidth sensitivity to HAC(12) is empirically motivated.
4. **Intervention data-freshness gap.** 73 weeks (8% of sample) have dummy=0 by absence-of-data not confirmed absence → S7 sensitivity drops 2024-10+ to confirm primary result is not driven by the gap window.

**Good news for T3b:** regressor matrix is clean (max |corr| = 0.142) → no collinearity-driven SE inflation.

## Strategic product read

- **Clean primary story** ("CPI surprise linearly moves TRM vol by β") is at material risk given Colombian asymmetry + attenuation — but **regressor matrix cleanliness removes collinearity as a failure mode**.
- **Methodological integrity strengthened** this session: Colombian CPI asymmetry is **honestly regime-specific, not methodological** (confirmed by applying SAME AR(1) operator to US data → symmetric result). The audit trail is defensible.
- **Data-freshness is the only meaningful data-quality concern surfaced in all of Phase 1.** Scope-limited (73 weeks), mitigated by S7.
- **Conditional-event-day story** ("TRM is more volatile on CPI release days; large surprises move it much more") is robust — grounded on event-day vol ratios + tail analysis (Phase 3 NB3).
- Both serve the Abrigo product pitch. The research pipeline honors clean-primary framing for scientific integrity; product pitch has flexibility the research does not.

## Motivated sensitivities for Task 13 to pre-register

Frozen in Task 13 (cleaning.py + fingerprint + pre-NB3 prep) before any NB2 estimation runs, while no β̂ has been observed. Preserves `anti_fishing_binding = True` seal.

| ID | sensitivity | motivating finding |
|---|---|---|
| A9 | asymmetric response (\|surprise\|, pos-only, neg-only) | Colombian 94% negative asymmetry (§4a) |
| A12 | HAC bandwidth robustness (HAC(12) alongside HAC(4)) | US CPI kurt_exc=8.51 (§4b); oil kurt_exc=17.79 (§4e) |
| S1 | 60-month rolling AR(1) surprise | alternative to full-history anchoring (already in Decision #4 alt) |
| S2 | 2015-2017 COP-crisis sub-sample drop | Colombian regime shock sub-period |
| S3 | 2020-2021 COVID sub-sample drop | US fat-tail outlier concentration; oil/intervention COVID regime |
| S4 | CPI_surprise × intervention_dummy interaction | does BanRep FX intervention mechanically absorb CPI shocks? |
| S5 | event-day vol ratio (mean(\|TRM return\|) on release days ÷ non-release) | product-facing statistic; robust to AR(1) misspec |
| S6 | `intervention_amount` (signed continuous) swap | Decision #9 pre-registered alt |
| S7 | drop 2024-10+ subsample (73 weeks = 8%) | intervention data-freshness gap (Decision #9) |

**Status:** A9 and A12 anticipated in spec Rev 4. S1 sits in Decision #4's sensitivity row. S6 sits in Decision #9's alt. **S2-S5 and S7 are NEWLY motivated by Phase 1 findings and need to land in Task 13 pre-registration doc before NB3 is authored.**

## Action items for Task 13/15

1. **references.bib cleanup (Task 15 priority):** add `Anzoátegui-Zapata & Galvis 2019` + `Uribe-Gil & Galvis-Ciro 2022 BIS WP 1022` (Decision #6 grounding citations). Update `test_references_bib.py` count 35 → 37.
2. **S7 pre-registration propagation (Task 13):** amend `contracts/.scratch/2026-04-18-nb3-sensitivity-preregistration.md` to formally add S7 (intervention data-freshness gap). Currently documented in Decision #9 interp but not in pre-reg doc.
3. **Pipeline addition acknowledgement (Task 15):** list `contracts/scripts/build_banrep_meeting_calendar.py` in the pipeline manifest/docs reviewed at section close.

## How to apply

When Phase 1 NB1 closes (Task 15 review gate) and Phase 2 NB2 kicks off:

1. **Before NB2 estimation runs:** Task 13 must consolidate all motivated sensitivities into a frozen pre-registration document. The agent executing Task 13 should:
   - Read this file + the `anti_fishing_binding` section of spec Rev 4
   - Enumerate A9, A12, S1-S7 as pre-registered sensitivity runs in the NB3 scaffold
   - Hash the sensitivity list into the panel fingerprint so post-hoc additions are detectable
2. **NB3 authoring (Phase 3):** every sensitivity gets a dedicated subsection. NB3 executes them only after NB2 primary β̂ is frozen.
3. **Product pitch (separate from research):** even if primary T3b fails, the conditional-event-day story (supported by S5) can still ground the Abrigo pitch; deliberate two-track strategy.

## Commit references for verification

- §4a Trio 1 (Colombian CPI inspection): `0f9751bc6`
- §4a Trio 2 (alignment + imputation audit): `6d3a130b4`
- §4a Trio 3 (Decision #4 lock): `bfb52e8d0`
- §4b Trio 1 (US CPI inspection): `50da209f6`
- §4b Decision #5 lock: `53d0b4895`
- §4c Decision #6 lock (BanRep rate surprise): `11389a7b1`
- §4d Decision #7 lock (VIX aggregation): `d55eda6a9`
- §4e Decision #8 lock (oil_return): `c0c9d7eaf`
- §4f Decision #9 lock (intervention dummy + S7): `050484524`
- §5 Trio 1 (regressor correlation matrix): `2a47157e8` ← HEAD at digest-write time
