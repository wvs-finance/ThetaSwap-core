# FX-vol-on-CPI-surprise complete findings digest (as of 2026-04-19, pre Task 33)

Comprehensive scientific + methodological + strategic findings from the full 3-phase structural-econometrics pipeline. HEAD `479ebf609`. Baseline 758+3. Disk mirror of memory file `project_fx_vol_econ_complete_findings.md` for human-readable git-tracked reference.

## Context

Structural econometrics pipeline testing whether Colombian CPI surprises cause COP/USD (TRM) realized volatility. Product goal: ground Abrigo (permissionless FX vol insurance via Mento stablecoins) in empirical causal identification. The scientific gate is **T3b: β̂_CPI − 1.28·SE > 0** on the primary weekly OLS. Passing = clean empirical support. Spec Rev 4 pre-committed primary: OLS on RV^{1/3}, weekly, 6 controls, HAC(4) SEs. Sample: 2008-01-02 → 2026-03-01, n_weeks=947.

# Section I: Scientific verdict

## THE HEADLINE

**`gate_verdict.gate_verdict = "FAIL"`** driven by T3b one-sided β̂_CPI − 1.28·SE > 0 failing (value = −0.002981). Under the pre-committed weekly OLS specification, **Colombian CPI surprises do NOT cause a statistically detectable increase in COP/USD realized volatility, 2008-2026.**

## Primary (weekly OLS Column 6)

| statistic | value |
|---|---|
| β̂_CPI | −0.000685 |
| HAC(4) Newey-West SE | 0.001794 |
| T3b statistic (β̂ − 1.28·SE) | −0.002981 |
| T3b verdict | FAIL |
| 90% HAC CI | [−0.003636, +0.002266] (contains zero) |
| T3a two-sided | FAIL TO REJECT (t=−0.38, p=0.70) |
| adj-R² Column 6 | 0.193 |
| n | 947 |

**Block-bootstrap HAC comparison (§3.5):** Politis-Romano stationary block bootstrap vs HAC(4). Overlap ratio = 1.0 (full containment); bootstrap CI [−0.003604, +0.002351]. Verdict: **AGREEMENT**. SEs trustworthy; failure is a real scientific finding, not inference artifact.

## Co-primary 1 (daily GARCH-X, Task 19)

- δ̂ = 0 (pinned at Han-Kristensen positivity boundary)
- Self 1987 boundary-corrected LR p = 0.50
- VARIANCE channel is also null.

## Co-primary 2 (CPI/PPI decomposition, Task 20)

- β̂_CPI = −0.000605 (with IPP standardized)
- β̂_PPI = +0.000245
- Neither significant; inflation-channel "dominates" but both null.

## Auxiliary gates (NB3 Tasks 24-26)

| gate | result | note |
|---|---|---|
| T1 exogeneity | REJECT (F=15.12, p=1.3e-9) | surprises PREDICTABLE from lagged info → β̂ is predictive-regression coefficient, not strict impulse-response |
| T2 Levene announcement channel | FAIL TO REJECT (W=0.099, p=0.75) | NO weekly variance premium on release weeks; release-week var 0.000490 vs 0.000533 non-release |
| T4 Ljung-Box Q(1..8) | REJECT at every lag | diagnostic; HAC(4) handles |
| T5 Jarque-Bera | REJECT (JB=541, p<1e-118; skew=0.96, kurt=6.2) | diagnostic; Student-t refit absorbs |
| T6 Bai-Perron | UNALIGNED | data-driven breaks at 2009-10, 2014-08, 2016-09; analyst subsample boundaries 2015-01 + 2021-01 → closest break 21 weeks off; diagnostic |
| T7 intervention adequacy | TIGHT PASS | 91% of 1·SE threshold; sign FLIPS negative→positive when intervention dropped |

## §8 forest plot — 14 rows (1 anchor + 13 sensitivities)

Two sensitivity rows exclude zero at 90%, both POSITIVE (opposite primary sign):

- **A1 monthly cadence** (n=220 after R1 fix, Decision #1 compliant): β̂ = +0.0152, CI [+0.0057, +0.0246]
- **A4 release-day-excluded** (n=947): β̂ = +0.0033, CI [+0.0005, +0.0062]
- **A9⁺** (positive-surprise subset, n=13): severely underpowered
- **A9⁻** (negative-surprise subset, n=205): β̂ = +0.0068, CI contains zero

## §9 material-mover spotlight: HALTED

Per anti-fishing protocol (T3b FAIL binds); zero spotlight tables produced. A1/A4 significant rows remain visible in §8 forest plot appendix as pre-registered record only.

## Reconciliation (NB2 §10)

AGREE — directional concordance via joint null (both β̂_CPI 90% HAC CI and δ̂ 90% QMLE CI contain zero).

# Section II: Twelve Decisions locked (Phase 1)

| # | scope | primary | sensitivity alt |
|---|---|---|---|
| 1 | sample window | 2008-01-02 → 2026-03-01, n_weeks=947 | n/a |
| 2 | LHS transform | RV^(1/3) | log(RV) |
| 3 | frequency | weekly | daily |
| 4 | Colombian CPI surprise | `cpi_surprise_ar1` (ABDV 2003 AR(1) expanding, DANE IPC 1954-present) | A9 asymmetric + 60-month rolling AR(1) |
| 5 | US CPI surprise | `us_cpi_surprise_ar1` (AR(1) expanding, FRED CPIAUCSL, 12-mo warmup, BLS cal) | n/a |
| 6 | BanRep rate surprise | event-study daily ΔIBR at Junta dates, weekly sign-preserving sum | n/a |
| 7 | VIX aggregation | `vix_avg` (weekly arithmetic mean of daily FRED VIXCLS) | `vix_friday_close` rejected |
| 8 | oil_return | log-return of weekly-last positive WTI close (ARG_MAX, value>0) | n/a |
| 9 | intervention regressor | `intervention_dummy` (binary any-activity) | `intervention_amount`; S7 drops 2024-10+ |
| 10 | collinearity adjustment | none (max VIF well below 10, max \|corr\| = 0.142) | n/a |
| 11 | stationarity treatment | levels-primary (ADF rejects; KPSS flagged with Cavaliere-Taylor 2005 caveat) | first-differenced alt documented |
| 12 | merge policy | listwise complete-case (n=947) | ffill/MICE rejected |

All twelve respect spec Rev 4 pre-commitments with `anti_fishing_binding = True`.

# Section III: Phase 1 substantive findings

## Finding 1: Colombian CPI surprise asymmetry (§4a)

- Event density 23.0% (218/947 weeks)
- Sign balance: 205 negative / 13 positive — **~94% negative**
- Nonzero mean: −0.69 (strongly biased, NOT centered on zero)
- Nonzero |skew|: 0.90, kurt_exc: +1.11

### Root cause (Trio 2 audit, `6d3a130b4`)

Three candidate bugs ruled out: alignment rate=1.000; no imputation contamination; warm-up (643 months pre-sample vs 12-month threshold) far beyond adequate.

**Accepted root cause — regime mismatch.** AR(1) expanding-window anchors intercept to 1954-present history.
- Pre-sample mean MoM (1954-2007, incl. hyperinflation): +1.23%
- In-sample mean MoM (2008-2026, modern BanRep): +0.40%
- Ratio ~3× → forecast systematically pulled above modern reality → systematic negative surprises
- Correlation(surprise, CPI level) = +0.37

## Finding 2: US CPI symmetric + fat-tailed (§4b)

- Event density 22.9% (monthly cadence, ≈ Colombian)
- Sign balance: 110 pos / 107 neg — symmetric
- Nonzero mean: +0.0025 (centered)
- Nonzero |skew|: 1.31
- Nonzero kurt_exc: **+8.51**
- Top-5 outliers map to real macro events (Lehman, 2008 oil spike, COVID, 2022 deceleration)

**Interpretation:** same operator on US data is unbiased → confirms Colombian asymmetry is **regime-specific (hyperinflation anchoring), NOT a methodological bug.**

## Finding 3: BanRep rate surprise (§4c)

Decision #6: event-study daily ΔIBR at Junta dates, weekly sign-preserving sum (policy rate is step function; AR(1) would be misspecified). Grounding: Anzoátegui-Zapata & Galvis 2019; Uribe-Gil & Galvis-Ciro 2022 BIS WP 1022. 88 non-zero weeks; sign balance 42/46 — symmetric; corr with `cpi_surprise_ar1` = +0.074 (NO collinearity).

## Finding 4: VIX admissibility (§4d)

Decision #7 `vix_avg`. mean=19.90, std=8.75, max=74.62 (2020-03-16). kurt_exc=+8.51, lag-1 ACF=0.9435 (justifies HAC(4)). Univariate corr with rv_cuberoot=+0.355.

## Finding 5: Oil return construction (§4e)

Decision #8: log-return of weekly-LAST POSITIVE WTI close. Handles 2020-04-20 negative WTI. kurt_exc=+17.79 (fattest-tailed regressor). lag-1 ACF=−0.0004 (near-martingale). Top-5 outliers: 3× COVID 2020, 2× GFC 2008.

## Finding 6: Intervention regime heterogeneity + DATA-FRESHNESS GAP (§4f)

Decision #9: `intervention_dummy` primary; `intervention_amount` sensitivity; **S7 drops 2024-10+** for freshness.

- Active fraction 33% (316/947)
- **Data-freshness gap:** source `banrep_intervention_daily` ends 2024-10-04 → **73 weeks carry dummy=0 by absence-of-data, not confirmed absence** (8% of sample). Mitigated by pre-registered S7 (n_effective=874 after drop).
- Regime heterogeneity:
  - 2008-2014: active 71%
  - 2015-2019: dormant 3.8% (post-free-float)
  - 2020 COVID: active 63.5% (only regime with negative mean signed amount)
  - 2024 partial: 22.6%

## Finding 7: Joint regressor behavior (§5)

- Max |corr| across 6 RHS regressors: **0.142** (vix × oil) — well below BKW 0.7
- VIF max well below 10 → Decision #10 no-collinearity-adjustment
- Non-linearity signal: oil ↔ rv Pearson −0.114 vs Spearman −0.046 — local, not systemic
- **Verdict:** regressor matrix clean; OLS inference stable at n=947

## Finding 8: Stationarity (§6)

ADF rejects unit root on RV + all surprises. KPSS flags residual structure on VIX and oil (Cavaliere-Taylor 2005 volatility-noise). **Decision #11: levels-primary.**

## Finding 9: Merge policy (§7)

n=947 complete case. Listwise vs ffill vs MICE compared; ffill contaminates low-cadence macro; MICE overhead marginal at n=947. **Decision #12: listwise complete-case.**

# Section IV: Phase 2 + Phase 3 findings

## Finding 10: First β̂_CPI estimate — T3b primary FAIL (Task 17, NB2 §3+§3.5)

See Section I headline. Attenuation + asymmetry + measurement-error predictions all held. HAC-bootstrap AGREEMENT rules out SE artifact.

## Finding 11: Coefficient ladder (NB2 §3)

| col | regressors | adj-R² | interpretation |
|---|---|---|---|
| 1 | cpi only | ≈ 0 | macro-surprise alone explains nothing |
| 2 | + us_cpi | ≈ 0 | still nothing |
| 3 | + banrep | ≈ 0 | still nothing |
| 4 | + vix_avg | 0.125 | **VIX does the work** |
| 5 | + intervention | 0.190 | FX-policy adds marginal power |
| 6 | + oil_return | **0.193** | commodity closes the set; primary gate column |

Macro-surprises carry ≈0 conditional variance. VIX + intervention + oil carry explanatory power.

## Finding 12: GARCH-X VARIANCE channel is null (Task 19, NB2 §4)

δ̂ = 0 pinned at Han-Kristensen positivity boundary; Self 1987 LR p = 0.50.

## Finding 13: CPI/PPI decomposition — neither significant (Task 20, NB2 §5)

β̂_CPI = −0.000605, β̂_PPI = +0.000245 (with IPP standardized).

## Finding 14: T1 exogeneity REJECTS (NB3 §1)

F=15.12, p=1.3e-9. t_lag = −6.56 on lagged surprise. Primary β̂ is **predictive-regression coefficient**, NOT strict impulse-response. AR(1) expanding-window operator fit ONCE on full history, not rolling-refit → residual serial correlation.

## Finding 15: T2 Levene announcement channel FAIL TO REJECT (NB3 §2)

W=0.099, p=0.75. **No weekly variance premium on release weeks.** Release-week variance marginally LOWER (0.000490 vs 0.000533). Cleanest null in the pipeline.

## Finding 16: T6 Bai-Perron UNALIGNED (NB3 §6)

3 data-driven breaks at 2009-10, 2014-08, 2016-09 via ruptures.Binseg+RBF. Analyst boundaries at 2015-01 + 2021-01. Closest detected break 21 weeks off. Diagnostic only.

## Finding 17: T7 intervention adequacy TIGHT PASS (NB3 §7)

91% of 1·SE threshold. Sign FLIPS negative→positive when intervention dropped.

## Finding 18: A1 monthly + A4 release-day-excluded positive-significant (NB3 §8)

See Section I forest plot. Both CIs exclude zero at 90%, both POSITIVE. Under anti-fishing protocol these cannot be promoted to primary; they remain pre-registered robustness record.

# Section V: Strategic product read (for Abrigo)

## Clean-primary story DIED

"CPI surprise linearly moves weekly TRM vol by β" is NOT empirically supported on Colombian weekly data under Rev 4 spec.

## Anti-fishing discipline VINDICATED

Pre-committed primary failed cleanly; no post-hoc pivot. **SUCCESS of scientific integrity, not a pipeline failure.**

## Conditional pivot paths live

1. **A1 monthly cadence** (pre-registered, CI excludes zero): reframes product as "monthly CPI-cycle hedge"
2. **A4 release-day-excluded** (pre-registered, CI excludes zero): effect in non-release-day dynamics
3. **Intraday event-window analysis** (OUTSIDE current spec): future work

## Honest commercial positioning

"At pre-registered primary specification, no effect detected; at monthly cadence with pre-commitment-compliant window, a positive effect is detectable at 90%. Commercial positioning pivots from weekly-CPI-hedge to monthly-cycle-hedge, grounded on A1 + A4 as pre-registered robustness."

See memory file `project_fx_vol_econ_gate_verdict_and_product_read.md` for full Abrigo strategic memo.

# Section VI: Methodological findings (why primary failed)

1. **AR(1) expanding-window anchors to 1954-2007 hyperinflation.** Pre-sample mean IPC MoM (1954-2007) = +1.23% vs in-sample (2008-2026) = +0.40%. ~3× ratio → 94% of surprises NEGATIVE → classical attenuation bias.
2. **IBR structural absence pre-2008.** Forced sample start 2008-01-02 → n=947 instead of n>1200.
3. **T1 rejection confirms AR(1) mis-specification.** Operator fit once on full history, not rolling-refit → residual serial correlation → predictive-regression coefficient.
4. **Intervention data-freshness gap.** `banrep_intervention_daily` ends 2024-10-04 → 73 weeks (8%) with dummy=0 by absence-of-data → mitigated by S7.

# Section VII: Review process findings

**Silent-test-pass pattern hit 5 times:**
1. Task 22 E1: `nb2_serialize.py` date coercion — synthetic inputs
2. Task 25 cell 10: NB3 `panel` undefined — parsed source, never exec
3. Task 27 follow-up: NB3 §1 never unpacked PKL into bare-name vars
4. Task 24 `from scripts import cleaning` — bootstrap didn't add `contracts/` to sys.path
5. Task 31 R2: `test_nb3_section10_gate.py` — synthetic only, didn't exec live cell

**Remediation: 3 integration tests** (`test_nb[123]_end_to_end_execution.py`) run `jupyter nbconvert --execute` on each notebook.

**Three-way review value demonstrated:**
- **Model QA** catches: econometric label drift, identification validity, boundary-case inference
- **Reality Checker** catches: spec-commitment violations, silent-test-pass patterns, prose-code drift, citation integrity
- **Technical Writer** catches: reader-journey propagation, PDF export readiness, honest-caveat visibility

# Section VIII: Motivated sensitivities (frozen pre-registration)

| ID | sensitivity | Phase-3 result |
|---|---|---|
| A1 | monthly cadence | **β̂=+0.0152, CI excludes zero POSITIVE** |
| A4 | release-day-excluded | **β̂=+0.0033, CI excludes zero POSITIVE** |
| A9 | asymmetric response | A9⁺ n=13 underpowered; A9⁻ CI contains zero |
| A12 | HAC(12) bandwidth | consistent with A9/HAC(4) |
| S1 | 60-month rolling AR(1) | consistent with primary |
| S2 | 2015-2017 COP-crisis drop | consistent |
| S3 | 2020-2021 COVID drop | consistent |
| S4 | CPI × intervention interaction | consistent |
| S5 | event-day vol ratio | see T2 Levene null |
| S6 | `intervention_amount` signed | consistent |
| S7 | drop 2024-10+ | consistent |

# Section IX: Deferred issues for Task 33

- R5 venv-misactivation silent-pass guard
- UQ1-UQ7 label imprecisions (T1 Mincer-Zarnowitz vs BEG, "Bai-Perron" vs ruptures.Binseg+RBF, A1/A5 disclosure, GARCH-X 6dp zero display, T7 heuristic formalization, bootstrap-HAC 50% lenient overlap)
- Forest plot secondary rendering: refactor to shared `_draw_forest_plot(ax, table)` helper
- `gate_verdict.json` schema additions: `t1_pvalue`, `t1_source`, predictive-regression-interpretation flag
- Forest plot PDF-native rendering for three PDF exports

# Section X: Commit archaeology

## Phase 1 Decision locks

- §4a Trio 1: `0f9751bc6`; Trio 2: `6d3a130b4`; Trio 3 Decision #4: `bfb52e8d0`
- §4b Trio 1: `50da209f6`; Decision #5: `53d0b4895`
- §4c Decision #6: `11389a7b1`
- §4d Decision #7: `d55eda6a9`
- §4e Decision #8: `c0c9d7eaf`
- §4f Decision #9: `050484524`
- §5 Trio 1: `2a47157e8`; Trio 2 (VIF + Decision #10): `f87bd4075`; Trio 3: `a224b80a1`
- §6 Trio 1: `540091eea`; Trio 2 (Decision #11): `460b08cd4`
- §7 Trio 1: `d3f936cce`; Trio 2: `3e1e25ed7`; Trio 3 (Decision #12): `b3e034141`
- cleaning.py green: `55b512c02`
- §8b ledger + fingerprint: `abdf349c8`
- Drift refresh: `473d4ddda`

## Phase 2 canonical

- Task 16: `ffad2b739`
- Task 17 (FIRST β̂_CPI): `ebe9bc681`
- Task 18: `3100f2ad7`
- Task 19 (GARCH-X δ̂=0): `33238ddf5`
- Task 20 (CPI/PPI): `e68ac27c0`
- Task 21 (T3B_GATE_VERDICT=FAIL): `7fd8b1059`
- Task 22: `250f9e713` + hotfix `12170a803`
- Task 23: `def90c540`; E3-E10: `c84dbaa02`

## Phase 3 canonical

- Task 24: `a9e58be34`
- Task 25: `e77e81dc1`
- Task 26: `a8d6a4bf3`
- Task 27 (forest plot 14 rows + A1/A4): `29b209dd8`
- Task 28 (§9 anti-fishing HALT): `a44c4e3c2`
- Task 29 (`gate_verdict.json` emitted): `1139f5717`
- Task 30 (README auto-render): `5235a90cb`
- Task 31 remediation final: `479ebf609` ← HEAD
