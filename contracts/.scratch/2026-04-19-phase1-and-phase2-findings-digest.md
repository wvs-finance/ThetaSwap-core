# Phase 1 + Phase 2 findings digest (2026-04-19, post NB2 Task 17)

Disk-local mirror of the persistent-memory digest at
`~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_phase1_and_phase2_findings_digest.md`.

This version is git-tracked and travels with the repo. Prefer it after compaction when a commit-anchored context is needed.

## Context (one paragraph)

Structural econometrics pipeline testing whether Colombian CPI surprises cause COP/USD (TRM) realized volatility. Ultimate product goal: ground the "Abrigo" macro-hedge product (permissionless FX vol insurance for underserved-FX countries via Mento stablecoins). The scientific gate is **T3b: β̂_CPI − 1.28·SE > 0** on the primary OLS. Passing = clean empirical support for the hedge product. Spec Rev 4 pre-committed the primary: OLS on RV^{1/3}, weekly frequency, with 6 controls and HAC(4) SEs. Sample: 2008-01-02 → 2026-03-01, n_weeks=947.

## Twelve Decisions locked across Phase 1

| # | scope | primary | sensitivity alt |
|---|---|---|---|
| 1 | sample window | 2008-01-02 → 2026-03-01, n_weeks=947 | n/a |
| 2 | LHS transform | RV^(1/3) | log(RV) |
| 3 | frequency | weekly | daily |
| 4 | Colombian CPI surprise | `cpi_surprise_ar1` (ABDV 2003 AR(1) expanding over DANE IPC 1954-present) | A9 asymmetric + 60-month rolling AR(1) |
| 5 | US CPI surprise | `us_cpi_surprise_ar1` (AR(1) expanding, FRED CPIAUCSL, 12-mo warmup, BLS cal) | n/a |
| 6 | BanRep rate surprise | event-study daily ΔIBR at Junta decision dates, weekly sign-preserving sum (policy rate is step function, AR(1) would be misspecified) | n/a |
| 7 | VIX aggregation | `vix_avg` (weekly arithmetic mean of daily FRED VIXCLS) | `vix_friday_close` explicitly rejected |
| 8 | oil_return aggregation | log-return of weekly-LAST POSITIVE WTI close (ARG_MAX with value>0 filter) | n/a |
| 9 | intervention regressor | `intervention_dummy` (binary any-activity) | `intervention_amount` (signed continuous); S7 drops 2024-10+ |
| 10 | collinearity adjustment | none — max VIF well below 10, max \|corr\| = 0.142 | n/a |
| 11 | stationarity treatment | levels-primary (RV and surprises stationary under ADF; KPSS flagged with Cavaliere-Taylor 2005 volatility-noise caveat, does not unseat ADF) | first-differenced alt documented |
| 12 | merge policy | listwise complete-case (n=947) | ffill/MICE candidates compared in §7 Trio 2 and rejected |

All twelve respect spec Rev 4 pre-commitments with `anti_fishing_binding = True`.

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
- **Grounding:** Anzoátegui-Zapata & Galvis 2019; Uribe-Gil & Galvis-Ciro 2022 BIS WP 1022 (both added to `references.bib` in commit `3287b8aaa`)
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

## Material finding 7: Joint regressor behavior (§5)

- **Max |corr| across 6 RHS regressors:** **0.142** (vix × oil) — well below BKW 0.7 collinearity threshold
- **Prior-trio correlations confirmed:** banrep × cpi = +0.074; vix × rv = +0.355; intervention × cpi = −0.100
- **VIF (§5 Trio 2, commit `f87bd4075`):** max VIF well below 10 → Decision #10 locks no-collinearity-adjustment
- **Non-linearity signal:** oil_return ↔ rv_cuberoot Pearson −0.114 vs Spearman −0.046 — handful of extreme oil weeks drive Pearson. §5 Trio 3 scatter matrix (commit `a224b80a1`) confirms the signal is local, not a systemic issue.
- **Pearson-Spearman otherwise concordant**
- **Verdict:** **regressor matrix is clean; OLS inference stable at n=947**

## Material finding 8: Stationarity (§6)

Decision #11 (commit `460b08cd4`, strengthened `472b44cc5`):

- ADF rejects unit root on RV and all surprises → stationary
- KPSS flags residual structure on VIX and oil (expected: volatility-noise shows up as persistent heteroskedasticity in levels). Cavaliere-Taylor 2005 establishes KPSS sensitivity to this structure without invalidating ADF.
- **Decision:** levels-primary. First-differenced alternative documented but not adopted.
- No cointegration concerns (no unit-root regressors survive the ADF screen).

## Material finding 9: Merge policy (§7)

Decision #12 (commit `b3e034141`):

- Per-series missingness audit (Trio 1, commit `d3f936cce`): n=947 complete case
- Merge-policy comparison across listwise / ffill / MICE (Trio 2, commit `3e1e25ed7`)
- **Lock:** listwise complete-case. ffill introduces contaminated values on low-cadence macro series; MICE introduces multiple imputation overhead for marginal gain at n=947.

## Material finding 10: First β̂_CPI estimate — T3b primary FAIL with HAC-bootstrap AGREEMENT (NB2 §3 + §3.5)

### Point estimate and HAC inference

| statistic | value |
|---|---|
| β̂_CPI (Column 6, primary) | **−0.000685** |
| HAC(4) Newey-West SE | 0.001794 |
| T3b statistic (β̂ − 1.28·SE) | **−0.002981** |
| T3b verdict | **FAIL** (must be > 0 to pass) |
| 90% HAC CI | [−0.0036, +0.0023] — contains zero |

**Formal gate evaluation deferred to Task 21 (§8-9).** Task 17 is the point-estimate commit; Task 21 is the formal declaration.

### Coefficient ladder (Column 1 → Column 6, adj-R² progression)

| col | regressors | adj-R² |
|---|---|---|
| 1 | cpi only | ≈ 0 |
| 2 | + us_cpi | ≈ 0 |
| 3 | + banrep | ≈ 0 |
| 4 | + vix_avg | 0.125 |
| 5 | + intervention | 0.190 |
| 6 | + oil_return | **0.1927** |

**Load-bearing qualitative result:** macro-surprise regressors alone explain essentially zero variance in RV^(1/3). Conditional contributions come from global-risk (VIX), FX-policy (intervention), and commodity (oil). This is critical for product framing (see Strategic section).

### Block-bootstrap HAC comparison (§3.5)

Politis-Romano stationary block bootstrap, applied to the full OLS:

- 90% HAC(4) CI = [−0.003605, +0.002236]
- 90% bootstrap CI = [−0.003604, +0.002351]
- Overlap ratio = **1.0** (full containment each way)
- Verdict: **AGREEMENT**

**Implication:** the HAC(4) standard errors are trustworthy. No kernel misspecification. The T3b failure is a **real scientific finding under the pre-committed spec**, not an inference-level artifact.

## Updated T3b risk assessment — predictions held

The prior digest (2026-04-18) listed four risk vectors. Three predicted T3b failure-or-risk modes. All held:

1. **Attenuation bias on Colombian CPI surprise.** Measurement error in the regressor (AR(1) misspec relative to true market expectations) biases β̂ toward zero. The realized β̂ = −0.000685 (tiny negative point estimate close to zero) is **textbook classical errors-in-variables attenuation**. **Prediction held.**
2. **Sign asymmetry reduces effective identifying variation.** 205 neg / 13 pos means the linear OLS fits the negative tail almost exclusively; positive-side inference is essentially absent. The linear-average specification cannot capture an asymmetric response even if one exists. **Prediction held.**
3. **US CPI fat tails (kurt_exc=8.51) + oil kurt_exc=17.79.** HAC(4) vs HAC(12) sensitivity motivated. The HAC-bootstrap AGREEMENT result retires this as a concern for the primary inference — SEs are trustworthy under HAC(4). **Lower priority now; still worth Task 18 diagnostic.**
4. **Intervention data-freshness gap.** 73 weeks (8% of sample) with dummy=0 by absence-of-data not confirmed absence. Relevant for S7 as a robustness check; not a binding failure mode for the primary itself.

The regressor-matrix cleanliness finding (§5) also held: no collinearity-driven SE inflation. The failure is driven by the attenuation + asymmetry mechanisms, not by noisy SEs.

**Pre-commitment discipline is vindicated.** If post-hoc specification search had replaced RV^(1/3) with log(RV), or replaced the surprise regressor with a demeaned variant, or narrowed the sample to drop the hyperinflation-anchored pre-2010 years, the resulting β̂ might have cleared T3b — inflating Type I. The pre-reg held the line.

## Strategic product read (post-Task-17)

**Product viability has NOT collapsed.** The primary's statistical failure narrows what research can support, not what the product can claim.

### The clean-primary story is unavailable

"A surprising CPI print linearly moves TRM vol by β" cannot be defended on the primary. β̂ is negative, tiny, and its 90% CI brackets zero on both sides. Attempting to pitch this story against the Phase 1 + Phase 2 audit trail would be dishonest.

### The conditional-event-day story is what carries the product

**Sensitivity S5 (event-day vol ratio)** is the clean empirical test of the product hypothesis. It measures mean(|TRM return|) on CPI release days ÷ mean(|TRM return|) on non-release days. Key properties:

- **Bypasses the measurement-error problem.** S5 does not need a clean surprise regressor — it only needs release-day identification (which is methodologically trivial and error-free).
- **Tests exactly what the product sells.** Abrigo's commercial premise is "pre-release hedging has basis because TRM is measurably more volatile around CPI prints". S5 is that statement operationalized.
- **Robust to the 94% asymmetry.** S5 uses |TRM return|, so sign balance of the surprise is irrelevant.
- **Product-facing stat.** A ratio like 1.6× (release vs non-release) is directly explicable in marketing copy without econometric jargon.

### Other sensitivities now load-bearing

- **A9 asymmetric response** (|surprise| or pos-only/neg-only) — decomposes whether there's a real asymmetric effect hidden in the linear average. If pos-only β̂ clears its own threshold, the product can lean on "upside CPI surprises specifically drive TRM vol" rather than the symmetric story.
- **S1 60-month rolling AR(1)** — alternative surprise construction less biased by the hyperinflation anchor. If S1's β̂ is larger (attenuation reduced), strengthens the measurement-error read of primary failure without changing the primary-result commitment.

### Pre-registered two-track strategy (already documented in prior digests)

- **Track 1 (research-facing):** honor pre-commitment. T3b formally fails at Task 21. NB2 final report must state this cleanly.
- **Track 2 (product-facing):** S5 + A9 + S1 supply the commercial-grade evidence. NB3 is where this materializes. Product pitch retains flexibility the research does not.

### Methodological integrity strengthened, not weakened

The HAC-bootstrap AGREEMENT result is a **gift** for the research credibility. It rules out the "maybe the SEs are bad" criticism ex ante. Combined with the Phase 1 audit trail (Colombian asymmetry confirmed regime-specific, not methodological), this is one of the most defensible failed-primary cases possible. Reviewers asking "did you p-hack?" get shown the pre-reg hash + the 4 reviewer cycles passed in Task 15.

## Motivated sensitivities (frozen pre-registration, unchanged by Task 17)

These were frozen in Task 13 and hashed into `nb1_panel_fingerprint.json` as `sensitivity_preregistration_hash` (commit `3fbc1409e`). They remain the authoritative list for NB3. Task 17's outcome does not modify them — re-opening would break `anti_fishing_binding`.

| ID | sensitivity | motivating finding | now load-bearing? |
|---|---|---|---|
| A9 | asymmetric response (\|surprise\|, pos-only, neg-only) | Colombian 94% negative asymmetry (§4a) | **YES** — decomposes the linear-average null |
| A12 | HAC bandwidth robustness (HAC(12) alongside HAC(4)) | US CPI kurt_exc=8.51; oil kurt_exc=17.79 | Lower priority post-bootstrap AGREEMENT |
| S1 | 60-month rolling AR(1) surprise | alternative to full-history anchoring (Decision #4 alt) | **YES** — tests attenuation-reduction hypothesis |
| S2 | 2015-2017 COP-crisis sub-sample drop | Colombian regime shock sub-period | standard |
| S3 | 2020-2021 COVID sub-sample drop | US fat-tail outlier concentration; oil/intervention COVID regime | standard |
| S4 | CPI_surprise × intervention_dummy interaction | does BanRep FX intervention mechanically absorb CPI shocks? | exploratory |
| S5 | **event-day vol ratio** (mean(\|TRM return\|) release ÷ non-release) | product-facing statistic; robust to AR(1) misspec | **YES** — THE product-viability test |
| S6 | `intervention_amount` (signed continuous) swap | Decision #9 pre-registered alt | standard |
| S7 | drop 2024-10+ subsample (73 weeks = 8%) | intervention data-freshness gap (Decision #9) | standard |

**Status:** All 9 sensitivities frozen and hashed. NB3 (Tasks 24-31) runs them after NB2 closes.

## Action items ahead

1. **Task 18** — NB2 §4-5 residual diagnostics + Student-t alternative estimator. First opportunity to stress-test Column 6 primary beyond HAC(4).
2. **Task 21** — formal T3b gate evaluation (§8-9). Expected verdict: **FAIL**. Write-up must be honest, no hand-waving around the negative point estimate.
3. **Task 22-23** — NB2 three-way review gate. Particular attention: does the prose accurately report β̂ sign + magnitude, CI bracketing zero, HAC-bootstrap AGREEMENT, and pre-commitment discipline? Does it avoid hedging language that could be read as soft-pedaling?
4. **Tasks 24-31** — NB3 authoring. **S5 is the payoff.** A9 + S1 are load-bearing supporting sensitivities. Standard sensitivities (S2, S3, S4, S6, S7, A12) complete the pre-registered set.

## How to apply

### For the next plan task (Task 18)

1. Read peer resume file + this digest
2. Dispatch Analytics Reporter with Task 18 brief from the plan
3. Strict TDD (red first, then green)
4. HALT between trios

### For NB3 design (Tasks 24+)

1. Every pre-registered sensitivity gets a dedicated subsection
2. **S5 gets highest authorship care** — it's the product-viability gate
3. A9 and S1 subsections must be written to bear the weight of the commercial narrative if their estimates clear the respective robustness thresholds
4. Standard sensitivities (S2-S4, S6-S7, A12) documented completely but without commercial-narrative emphasis

### For the product pitch (separate from research)

S5's outcome determines commercial narrative. Abrigo messaging drafts should remain in `.scratch/` and reference `project_ran_positioning_principles.md` + `project_ran_brand_name.md` + `project_abrigo_painkiller_evidence_base.md` until S5 lands.

## Commit references for verification

### Phase 1 Decisions

- §4a Trio 1 (Colombian CPI inspection): `0f9751bc6`
- §4a Trio 2 (alignment + imputation audit): `6d3a130b4`
- §4a Trio 3 (Decision #4 lock): `bfb52e8d0`
- §4b Trio 1 (US CPI inspection): `50da209f6`
- §4b Decision #5 lock: `53d0b4895`
- §4c Decision #6 lock (BanRep rate surprise): `11389a7b1`
- §4d Decision #7 lock (VIX aggregation): `d55eda6a9`
- §4e Decision #8 lock (oil_return): `c0c9d7eaf`
- §4f Decision #9 lock (intervention dummy + S7): `050484524`
- §5 Trio 1 (regressor correlation matrix): `2a47157e8`
- §5 Trio 2 (VIF + Decision #10 no-collinearity-adjustment lock): `f87bd4075`
- §5 Trio 3 (scatter matrix diagnostic): `a224b80a1`
- §6 Trio 1 (ADF + KPSS on 7 series): `540091eea`
- §6 Trio 2 (Decision #11 stationarity levels-primary lock): `460b08cd4`
- §7 Trio 1 (per-series missingness audit): `d3f936cce`
- §7 Trio 2 (merge-policy candidate comparison): `3e1e25ed7`
- §7 Trio 3 (Decision #12 listwise complete-case lock): `b3e034141`
- cleaning.py red (TDD): `605f5cc79`
- cleaning.py green (pure wrapper, 12-Decision hash): `55b512c02`
- §8b ledger + fingerprint emission (NB2 handoff): `abdf349c8`
- fingerprint `generated_at` drift refresh: `473d4ddda`

### Phase 2 Tasks 16-17

- Task 16 red (TDD): `e5729513d`
- Task 16 green (NB2 §1-2 setup + descriptive stats): `ffad2b739`
- Task 17 red (TDD): `93af8d745`
- Task 17 green (§3 ladder + §3.5 block-bootstrap HAC): **`ebe9bc681`** ← HEAD at digest-write time
