---
title: Abrigo Phase-A.0 — Remittance-surprise → TRM-RV — formal spec (Rev-1)
date: 2026-04-20
author: Claude (foreground-authored; structural-econometrics skill invoked, Phases -1/0/1/2 inherited from design doc)
status: REV-1 (reviewed CR+RC+TW 2026-04-20, fixes applied)
parent_design_doc: contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-design.md
parent_design_doc_hash: 437fd8bd2
supersedes: none
reference_rev4_spec: contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md
---

# Rev-1 Formal Spec — Remittance-surprise → TRM realized volatility (Colombia, Phase-A.0)

## 1. Research question

Does the Colombian aggregate-monthly remittance AR(1) surprise carry detectable information content for COP/USD weekly realized volatility, on the frozen 947-observation Colombia weekly panel (2008-2026), under identical Rev-4 structural-econometric discipline?

- Unit of observation: weekly (Friday close), identical to Rev-4.
- Outcome variable (LHS): TRM weekly realized volatility, transformed as RV^(1/3), unchanged from Rev-4 frozen panel.
- Primary explanatory variable (RHS): remittance-flow AR(1) surprise, derived from BanRep aggregate monthly remittance inflows, step-interpolated to weekly (see §4.6 for interpolation protocol).

## 2. Economic model (inherited from design doc §Scope and §Scientific question)

### 2.1 Environment
Small open economy (Colombia) with floating exchange rate regime, managed inflation-target regime (Banrep, since 2001). TRM = COP/USD daily official rate; COP/USD spot market integrates (a) trade flows, (b) commodity-export receipts, (c) portfolio capital flows, (d) remittance inflows, and (e) non-resident intervention.

### 2.2 Actors (abbreviated from design doc)
- Colombian households receiving USD-denominated remittances from diaspora (primarily US, ~53%; Spain ~11%).
- FX-market participants (banks, brokerages, intervention desks) who price TRM against realized flow pressure.
- Informed and noise traders who form beliefs about future TRM level and vol.

### 2.3 Information structure
Market participants observe: prior TRM levels, BanRep remittance releases (monthly with 45-day lag), contemporaneous global macro (VIX, DXY, oil), and Colombian fiscal/monetary signals. Remittance releases are low-salience relative to CPI releases — minimal market-anticipation protocol (BanRep Borradores de Economía series, methodology placeholder — Borrador number and authors to be confirmed during Phase-1 data acquisition).

### 2.4 Primitives
- Remittance inflow process: Colombian diaspora labor income → transfer decision → conversion to COP → domestic spending.
- Exchange-rate determination: supply-demand for USD via trade + capital + remittance flows.
- Volatility process: conditional heteroskedasticity driven by flow-shock clustering.

### 2.5 Exogenous variables (as controls, unchanged from Rev-4)
VIX (global risk-off), DXY (USD strength), EMBI Colombia (sovereign-credit), Fed Funds rate, Oil (WTI), Banrep Repo rate.

### 2.6 Agent objectives (abbreviated)
Households minimize variance of consumption; FX participants maximize risk-adjusted returns; policy-makers minimize deviation from inflation target subject to flexible exchange rate.

### 2.7 Equilibrium concept
Partial-equilibrium, single-market FX determination. TRM is the equilibrium price of USD/COP clearing flow-pressure + speculative positioning. No cross-market contagion modeled (controls absorb global risk-off + EM-premium channels).

## 3. Stochastic model (inherited from design doc)

Error decomposition (per Reiss & Wolak 2007 §4.2):

- **η (unobserved heterogeneity):** unpriced Colombian-specific macro news, fiscal-policy announcements, political-event surprises (e.g., Petro-Trump Jan-2025 episode — see §5 for event-dummy handling).
- **u (agent uncertainty):** ex-ante unknowable future flow shocks, within-week high-frequency news, unanticipated intervention.
- **v (measurement error):** BanRep remittance revisions (up to 3-month lag); monthly→weekly step-interpolation artifact; vintage drift.

Primary econometric error ε = η + u + v. HAC Newey-West SE (Bartlett kernel, Andrews 1991 AR(1) plug-in bandwidth) accommodates ε's autocorrelation structure.

## 4. Estimation strategy

### 4.0 Notation (used uniformly throughout §4–§8)

- `β_Rem` — OLS population coefficient on `ε^{Rem}_w` in §4.1.
- `β̂_Rem` — its OLS estimate; the T3b gate (§4.4) is on `β̂_Rem`.
- `SE(β̂_Rem)` — HAC Newey-West standard error (Bartlett kernel, Andrews 1991 plug-in bandwidth; §4.9).
- `φ_Rem`, `φ̂_Rem` — GARCH(1,1)-X mean-equation analogs (§4.2). Reconciliation (§4.3) compares `β̂_Rem` and `φ̂_Rem`.
- `ψ̂_Rem` — GARCH(1,1)-X variance-equation estimate in sensitivity row S11 (§6) only. Not part of the primary reconciliation.
- `SD(RV^{1/3}_w,residualized)` — sample standard deviation of the OLS primary residualized LHS (regression of `RV^{1/3}_w` on the six Rev-4 controls, without `ε^{Rem}_w`). This value is emitted as part of NB2's point-estimate payload; the 0.030 raw-unit MDES in §4.5 is illustrative only.

### 4.1 Primary equation (OLS)

`RV^{1/3}_w = α + β_Rem · ε^{Rem}_w + Σ_j γ_j · Control_{j,w} + ε_w`

where:
- `RV^{1/3}_w` = frozen Rev-4 LHS for week w (realized-vol cube-root transform, daily TRM squared-returns basis).
- `ε^{Rem}_w` = primary RHS; AR(1) residual of `ΔlogRem_m` (BanRep aggregate monthly log-change), step-interpolated to weekly via LOCF anchored on BanRep release dates (see §4.6).
- `Control_j` = 6 Rev-4 controls (VIX, DXY, EMBI Colombia, Fed Funds, Oil WTI, Banrep Repo), each at weekly frequency, synchronized to Rev-4 frozen panel.
- HAC Newey-West SE: Bartlett kernel + Andrews 1991 AR(1) plug-in bandwidth.

Sample: 947 weekly observations, 2008-01-07 to 2026-02-23, identical to Rev-4 frozen panel (authoritative source: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json`, field `weekly_panel.date_min` / `.date_max`). Decision-hash extended (not replaced) per Rev-4 panel invariants.

### 4.2 Co-primary equation (GARCH(1,1)-X)

Mean equation: `r_w = μ + φ_Rem · ε^{Rem}_w + Σ_j λ_j · Control_{j,w} + ε_w`
Variance equation (standard GARCH(1,1)): `σ²_w = ω + α · ε²_{w-1} + β · σ²_{w-1}`

Primary GARCH-X parametrization: surprise enters the **mean equation** (continuity with Rev-4 convention; measures conditional-mean response of RV^(1/3) to surprise, same null as OLS β_Rem). Variance-equation placement is a pre-registered sensitivity row (§5) to address the vol-of-vol alternative hypothesis (per Model-QA FLAG-5).

Implementation: scipy L-BFGS-B custom likelihood (inherited from Rev-4 `nb2_serialize` — `arch` library lacks exogenous variance support).

### 4.3 Reconciliation rule

**Directional concordance** between OLS β̂_Rem and GARCH-X φ̂_Rem: three conditions must all hold for AGREE verdict:

1. sign(β̂_OLS) == sign(φ̂_GARCH-X)
2. "90% CI contains zero" status matches for both
3. Significance category matches: both non-significant, both borderline (|t| ∈ [1.28, 1.645]), or both significant (|t| > 1.645).

Rule inherited verbatim from Rev-4 `contracts/scripts/nb2_serialize.py::reconcile()`. DISAGREE verdict triggers additional sensitivity rows but does not in itself fail the gate.

### 4.4 Pre-committed gate — T3b two-sided

`|β̂_Rem / SE(β̂_Rem)| > 1.645` at α = 0.10 two-sided. (Here `β̂_Rem` unambiguously refers to the OLS estimator defined in §4.1; the GARCH-X analog `φ̂_Rem` is reconciled under §4.3, not gated under T3b.)

**Supersedes banner**: This two-sided resolution supersedes the design-doc §Scientific question one-sided placeholder (`β̂_Rem − 1.28·SE > 0`). The design doc explicitly defers sign-prior resolution to the Rev-1 spec (design-doc Phase-0 mandatory input #1), and Model-QA BLOCK-1 requires a defensible ex-ante sign prior before a one-sided gate is permissible.

**Rationale for two-sided** (resolves Model-QA BLOCK-1): no defensible economic sign prior for remittance surprise on FX vol exists. Literature gives competing predictions:
- Stabilizer hypothesis: remittance inflows smooth household income → reduce FX pressure → negative `β_Rem`.
- Stress-response hypothesis: remittance surprises are upward during stress (diaspora responds to crisis) → coincide with depreciation episodes → positive `β_Rem`.
- IMF GIV template (Aldasoro, Beltran, and Grinberg 2026, IMF WP/26/056): 1% inflow → +40bp parity deviation — a level effect, ambiguous for vol.

Halving the rejection region via one-sided test without an ex-ante sign prior is indefensible. Two-sided gate preserves symmetric inference.

### 4.5 Minimum-detectable-effect-size (MDES) pre-commitment

Effective sample size `N_eff ≈ 200` (HAC-autocorrelation-adjusted from nominal N=947, consistent with Rev-4 CPI exercise effective DOF; see `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb3_forest.json` field `n_eff`).

At α = 0.10 two-sided, 80% power: MDES = 2.80 / √N_eff ≈ 0.198 standard deviations of residualized `RV^{1/3}_w`. **Pre-committed threshold (exactly 0.20)** — rounded up from 0.198 for audit simplicity and to eliminate any borderline boundary ambiguity at the verdict cell. The value 0.20 is the exact threshold used by the verdict rule below.

Illustrative raw-unit translation: `0.20 · SD(RV^{1/3}_w,residualized) ≈ 0.030` at a sample-dependent `SD ≈ 0.15`. This raw-unit figure is illustrative only; the verdict rule operates on standardized units via `|β̂_Rem / SD(RV^{1/3}_w,residualized)|` where the denominator is emitted by NB2's point-estimate payload.

**Three-way verdict rule (resolves Model-QA BLOCK-2):**
- If `|β̂_Rem / SE(β̂_Rem)| < 1.645` AND `|β̂_Rem / SD(RV^{1/3}_w,residualized)| < 0.20` → verdict = **INCONCLUSIVE** (statistically null but underpowered).
- If `|β̂_Rem / SE(β̂_Rem)| < 1.645` AND `|β̂_Rem / SD(RV^{1/3}_w,residualized)| ≥ 0.20` → verdict = **FAIL** (statistically null, sufficiently powered).
- If `|β̂_Rem / SE(β̂_Rem)| > 1.645` → verdict = **PASS** (sign published separately).

### 4.6 Step-interpolation protocol

**LOCF (last-observation-carried-forward) from BanRep monthly release value; no within-month decay, no daily rollup.** The value is step-held from the release date until the next release date. For week w with Friday-close date `d_w`, remittance surprise = AR(1) residual of the monthly release with `max(release_date)` subject to `release_date ≤ d_w`. Ties (two releases on the same date) resolve by earlier reference-period.

**Friday-cutoff rule**: release dates landing on `d_w` itself (Friday ≤ 16:00 Colombia time; BanRep's canonical publication window closes before market close) are included in week w. Release dates after the Friday cutoff roll to week w+1.

**Release date definition**: `release_date` = BanRep's actual publication calendar date, NOT the reference-period month-end.

Rationale: LOCF is the causal interpretation — reflects the information available to FX participants at week w (Kuttner 2001; Gürkaynak-Sack-Swanson 2005). Forward-fill / next-week-fill introduces look-ahead bias.

**Pre-2015 proxy (concession, see §4.8):** when the actual release date is not recovered, the proxy release date = 15th of the month following the reference-period (approximates BanRep's standard ~45-day publication rhythm).

### 4.7 AR order

**Primary: AR(1).** Continuity with Rev-4 CPI spec's AR(1) choice. Parsimony + avoids overfitting on a 216-observation monthly series.

**Sensitivity: SARIMA(1,0,0)(1,0,0)_12** — seasonal-AR to capture documented December remittance spikes. Pre-registered as a sensitivity row in §5.

### 4.8 Vintage discipline

**Primary: real-time (first-printed) vintage.** Remittance surprise is computed from the initial-release value at each BanRep publication date, not subsequent revisions.

**Sensitivity: current-vintage.** Re-computed using the 2026-04 snapshot of the BanRep series (with all revisions applied).

**Caveat on pre-2015 vintage metadata (deferred to Phase-1 acquisition evidence):** The corpus does not document the actual reliability of BanRep's archived release-date metadata for the pre-2015 remittance series (`BANREP_TRM_ACCESS.md` covers the TRM Socrata endpoint only; no remittance publication-calendar archive evidence exists in `/notes/**`). The pre-2015 vintage-metadata recoverability is therefore unverified at spec time. The spec pre-commits to the following conservative protocol:

1. **During Phase-1 data acquisition (Task 9–14):** the data-ingestion script attempts to recover actual BanRep release-date metadata for the full 2008-2026 window. Recovered dates, if any, are the primary `release_date` source.
2. **If actual release-date metadata is not recoverable for a subsample:** that subsample uses the §4.6 pre-2015 proxy (reference-month + 15th-of-following-month) and is flagged in the emitted panel metadata as `release_date_source = "proxy"`.
3. **Subsample-restricted primary (if triggered):** if the proxy applies to more than ~20% of the 947 observations and no external provenance is recovered during Phase-1, the primary regression restricts to the vintage-strict subsample; the full-window result is demoted to a sensitivity row. The size of the vintage-strict subsample is determined empirically in NB1 and emitted to `gate_verdict_remittance.json`.

This protocol replaces the spec-time claim that ~382 of 947 observations are pre-2015 (a claim not supported by the corpus at spec time). The pre-2015 boundary and the size of the affected subsample are pre-registered as Phase-1 empirical outputs, not spec-time constants.

### 4.9 HAC kernel + bandwidth

**Bartlett kernel (Newey-West 1987)** for exact continuity with Rev-4.

**Bandwidth: Andrews 1991 AR(1) plug-in**, formula: `bw = 1.1447 · (α_2 · T)^{1/3}` where `α_2` is the second-moment AR(1) parameter fit to residuals.

Implementation: statsmodels `sm.OLS.fit(cov_type='HAC', cov_kwds={'maxlags': <Andrews-auto>})`.

## 5. Specification tests (T1-T7) — inherited from Rev-4 scaffold

| # | Test | Rev-1 adaptation |
|---|---|---|
| T1 | Mincer-Zarnowitz exogeneity of primary RHS | AR(1) surprise is orthogonal to controls (testable null): regress `ε^{Rem}_w` on lagged controls; joint F-stat with p > 0.10 for PASS. |
| T2 | Levene equality-of-variance between release-week and non-release-week | Tests whether release-day observations induce variance-heterogeneity. |
| T3a | Statistical significance of `β̂_Rem` (two-sided) | `|β̂_Rem / SE(β̂_Rem)|` > 1.645 at α=0.10. |
| T3b | Primary gate verdict (§4.4) | Includes MDES rule (§4.5) to distinguish FAIL from INCONCLUSIVE. |
| T4 | Residual autocorrelation (Ljung-Box Q, lags=4,8,12) | HAC-standard check. |
| T5 | Normality of residuals (Jarque-Bera) | Reported in NB3 as diagnostic output; does not gate verdict. |
| T6 | Heteroskedasticity (Breusch-Pagan + White) | Diagnostic; motivates GARCH-X co-primary. |
| T7 | Specification-curve robustness | Re-estimate across control-set combinations; report median β̂ and % significance. |

## 6. Sensitivity sweep (pre-registered rows for forest plot, labeled S1–S13)

Rows are labeled `S1`–`S13` in the sensitivity sweep to avoid cross-reference collision with the §12 resolution-matrix rows 1–13 (see TW NIT-2 note).

1. **S1 — A1-R (monthly-cadence)**: same surprise series at monthly frequency (n ≈ 216 obs).
2. **S2 — A4 (release-day-excluded weekly)**: exclude weeks containing BanRep remittance release day.
3. **S3 — Release-day-only weekly subsample**: converse of A4 (n ≈ 216 obs).
4. **S4 — Pre-2015 subsample** (proxy-release-date regime, size determined empirically per §4.8 Phase-1 protocol).
5. **S5 — Post-2015 subsample** (vintage-strict regime, size determined empirically per §4.8 Phase-1 protocol).
6. **S6 — Dec-Jan excluded** (removes December and January weeks; n ≈ 789).
7. **S7 — SARIMA(1,0,0)(1,0,0)_12 surprise** (seasonal-AR residual; see §4.7).
8. **S8 — Current-vintage (revised) remittance series**.
9. **S9 — Quarterly corridor reconstruction (US-subset)**: exploratory sensitivity. The operational recipe (BanRep Borradores de Economía series, methodology placeholder — Borrador number and authors to be confirmed during Phase-1 data acquisition) is pinned at Phase-1 ingestion time. If the recipe cannot be verified, this row is marked `SKIPPED` in the forest output with justification.
10. **S10 — Alternate LHS: log(RV_w)** — tests LHS-transform sensitivity (Bollerslev-Zhou 2002).
11. **S11 — GARCH-X variance-equation placement** — surprise in σ² equation (estimate `ψ̂_Rem`) rather than μ equation.
12. **S12 — Petro-Trump Jan-2025 event-dummied** — primary + dummy around 2025-01-21 to 2025-02-02 window.
13. **S13 — Event-study co-primary (Petro-Trump)** — see §7.

**Anti-fishing protocol**: material-mover §9 spotlight in NB3 is emitted ONLY if primary T3b PASSes. Under FAIL or INCONCLUSIVE verdicts, §9 cells emit placeholders referencing the pre-registered S1–S13 rows above and asserting that no post-hoc spotlight is performed.

## 7. Event-study co-primary

**Event**: 2025-01-26 (Sunday) Trump-Petro tariff-deportation standoff. Littio USDC-account opens grew +100% within 48h (documented in `COPM_MINTEO_DEEP_DIVE.md` and `LITERATURE_PRECEDENTS.md`; corpus cites the episode as "Feb 2025" referring to the continuing market-stress period that began on Jan 26).

**Window**: [w = -1, w = +5] weekly, 7 weeks total. Event date = 2025-01-24 (Friday immediately preceding the weekend announcement; the first trading-week boundary that contains the event).

**Test statistic**: cumulative abnormal `RV^{1/3}` over the [-1, +5] weekly window, standardized by the panel-pre-event SD. **SD denominator definition**: sample standard deviation of `RV^{1/3}_w` computed on the 52-week window immediately preceding the event date (weeks w ∈ [2024-01-26, 2025-01-17], 52 weeks). Using the 52-week pre-event window (rather than the full panel) controls for regime-dependent volatility-level drift over the 2008-2026 panel. One-sample t-stat tested at α = 0.10 two-sided.

**Joint-concordance rule**: If OLS primary PASS and event-study PASS with same sign → JOINT-AGREE. If one PASS and other FAIL → REPORT-BOTH (no synthetic verdict). If both FAIL → event-study provides no rescue.

## 8. Structural-break test

**Quandt-Andrews supremum-Wald test** over date-range [2013-01-01, 2017-12-31], testing for a single structural break in `β_Rem` on the primary regression. Significance threshold = 5%.

Window rationale: [2013-2017] is a corpus-cited flanking window around the Venezuelan-migration onset widely reported by UN/UNHCR as ~2015 (see `COLOMBIAN_ECONOMY_CRYPTO.md` §1.5 referencing ~2.9M Venezuelans in Colombia as of Nov 2025; the specific onset-year anchor is conservative rather than strictly cited). The window bracketing avoids a point-anchor commitment while preserving the regime-change hypothesis.

If break detected → emit pre-break and post-break subsample sensitivity rows with date cut at detected break. If no break → emit full-sample primary only.

## 9. Decision-hash extension

Extend the Rev-4 frozen decision-hash (`6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c`, authoritative source: `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json`, field `decision_hash`) with the new remittance-column schema hashes:

`decision_hash_rev1 = SHA256(decision_hash_rev4_bytes || concat(sorted_remittance_col_spec_hashes_bytes))`

**Sort key**: lexicographic ascending on the column-name string (UTF-8 byte comparison), NOT on the hex digest. Column name is the canonical schema identifier; this keeps the sort key invariant under hash-value changes and reproducible across Python/Rust implementations.

**Concatenation semantics**: `||` denotes byte-concatenation. `decision_hash_rev4_bytes` is the 32-byte raw SHA-256 digest of the Rev-4 decision hash (not the hex-string representation). Each `remittance_col_spec_hash` is likewise a 32-byte raw SHA-256 digest. The final SHA-256 is applied once to the concatenated byte sequence:
```
buf = decision_hash_rev4_bytes  # 32 bytes
for col_hash in sorted_remittance_col_spec_hashes_bytes:  # sorted by column-name
    buf += col_hash  # 32 bytes each
decision_hash_rev1 = sha256(buf).digest()
```

`remittance_col_spec_hashes` includes nine column specifications: primary-RHS hash, A1-R hash, regime-dummy hash, event-dummy hash, release-day-indicator hash, LOCF-surrogate flag hash, AR(1) params hash, SARIMA params hash, quarterly-corridor-reconstruction recipe hash (Basco-Ojeda-Joya-style methodology placeholder, recipe to be pinned during Phase-1).

Any mutation of an existing Rev-4 column aborts panel-load with `FrozenPanelViolation`.

## 10. Why this is a fresh pre-commitment (anti-fishing framing)

This Rev-1 spec tests a **different causal mechanism** than the Rev-4 CPI exercise:

- **Rev-4 CPI tested**: inflation-channel surprise → FX vol (domestic-price pass-through).
- **Rev-1 remittance tests**: external-inflow channel surprise → FX vol (stability-stress binary hypothesis, §4.4).

The two exercises differ in:
1. **Primary RHS**: CPI (domestic inflation measure) vs remittance (external transfer flow).
2. **Gate direction**: one-sided T3b (CPI) vs two-sided T3b (remittance, with MDES rule).
3. **Sensitivity sweep composition**: remittance adds vintage + reconstruction + event-study rows absent from Rev-4.
4. **Pre-existence in corpus**: the REMITTANCE_VOLATILITY_SWAP research track files (`STABLECOIN_FLOWS.md`, `CONTEXT_MAP.md`, `DATA_STRATEGY.md`) carry filesystem mtime 2026-04-02, predating the CPI-FAIL verdict (2026-04-19) by 17 days. This establishes remittance as a candidate mechanism before the CPI FAIL was known. (Note: mtime is filesystem metadata and can be altered by `touch`; audit-grade provenance for the pre-existence claim uses the git-blame / commit-SHA history of these files in the corpus repository, which is immutable under normal operation. The mtime figure is the user-facing timestamp; the git-blame is the cryptographic provenance.)

This is NOT a post-hoc rescue of CPI-FAIL. It is an independent hypothesis, pre-registered, with its own gate rule and its own verdict space. A FAIL verdict on remittance is an informative scientific output, not a trigger for further rescue attempts.

## 11. Deliverables

Per the Phase-A.0 plan, this spec enables:
- NB1 (EDA + panel-fingerprint extension): implements §9 decision-hash extension.
- NB2 (OLS ladder + GARCH-X + T3b gate + reconciliation): implements §4-5.
- NB3 (T1-T7 + forest + sensitivity + event-study + gate aggregation): implements §5-8.
- `gate_verdict_remittance.json` emission carrying the §4.4 verdict enum {PASS, FAIL, INCONCLUSIVE}.
- Auto-rendered README (via existing Rev-4 Jinja2 template with remittance wording).

Per-task artifact mapping (finer granularity) is enumerated in the Phase-A.0 implementation plan at `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (Tasks 9–30c).

## 12. 13-input resolution matrix (gating deliverable — Task 1 Step 4)

| # | Item | Resolution | Justification | Reviewer-checkable condition |
|---|---|---|---|---|
| 1 | Economic sign prior for gate direction | Two-sided T3b, α=0.10, critical |t|=1.645 | No defensible ex-ante sign prior; stabilizer vs stress-response hypotheses are both economically grounded. One-sided without a prior is indefensible (Model-QA BLOCK-1). | Spec states "two-sided α=0.10"; primary gate formula uses `|β̂/SE|>1.645`; no sign-restriction appears in primary. |
| 2 | Pre-committed MDES | 0.20 SD of residualized RV^{1/3}; three-way verdict enum {PASS, FAIL, INCONCLUSIVE} | At N_eff≈200, α=0.10, 80% power, MDES=2.80/√N ≈ 0.198 SD. Inconclusive-verdict rule distinguishes power failure from mechanism absence. | Spec §4.5 states MDES formula, numeric value, and the three verdict conditions with explicit |β̂/SE| and |β̂/SD_Y| thresholds. |
| 3 | Alternate-LHS sensitivity | `log(RV_w)` as sensitivity row S10 of §6 | Bollerslev-Zhou 2002 asymptotic-distribution argument; log(RV) and RV^{1/3} are monotone-related so sign-flip is informative. | Forest-plot row S10 (alternate-LHS) appears with `β̂_Rem / SE(β̂_Rem)` computed against log(RV_w). |
| 4 | HAC kernel | Bartlett (Newey-West 1987) | Continuity with Rev-4; optimal MSE for exponentially-decaying autocorrelation. | statsmodels `cov_type='HAC', kernel='bartlett'` cited in spec; implementation matches. |
| 5 | Andrews-bandwidth rule | Andrews 1991 AR(1) plug-in: `bw = 1.1447 · (α_2·T)^{1/3}` | Standard automatic-bandwidth choice; default in statsmodels. | Spec §4.9 states the formula + citation Andrews 1991 eq. 5.3. |
| 6 | Step-interpolation direction | LOCF anchored on BanRep release dates | Causal interpretation; no look-ahead; aligned with Kuttner 2001 surprise-construction convention. | Spec §4.6 specifies "most recent release ≤ week_end" protocol; implementation code will use LOCF strictly. |
| 7 | AR order | Primary: AR(1). Sensitivity row: SARIMA(1,0,0)(1,0,0)_12 | Parsimony + continuity with Rev-4; seasonal sensitivity addresses documented Dec remittance spikes without multiplying primary parameters. | Both residual series computed; sensitivity row S7 in §6 emitted. |
| 8 | Vintage discipline | Primary: real-time (first-printed); sensitivity: current-vintage. Pre-2015: proxy release dates (concession). | Causal + standard (Gürkaynak-Sack-Swanson 2005); pre-2015 caveat is a transparency concession, not a methodology compromise. | Spec §4.8 states both vintages + the pre-2015 proxy concession + post-2015 full-strictness claim. |
| 9 | Reconciliation rule | Directional concordance (sign + CI-contains-zero + significance-category) — verbatim Rev-4 `reconcile()` | Rev-4 continuity; robust under heteroskedasticity; avoids numerical-intersection artifacts. | Spec §4.3 lists the three concordance conditions; NB2 implementation imports Rev-4 `reconcile()`. |
| 10 | Structural-break test | Quandt-Andrews sup-Wald over [2013-2017] at α=0.05 | Pre-registered around Venezuelan-migration-onset regime break (2015); standard supremum-Wald method (Andrews 1993). | Spec §8 specifies date range + significance threshold + break-detection → subsample-sensitivity rule. |
| 11 | GARCH(1,1)-X parametrization | Primary: surprise in MEAN equation (coefficient `φ̂_Rem`). Sensitivity row S11 of §6: surprise in VARIANCE equation (coefficient `ψ̂_Rem`). | Rev-4 continuity for primary (same null as OLS `β_Rem`); MQ-FLAG-5 vol-of-vol alternative handled via sensitivity. | Spec §4.2 states both + which is primary; NB2 implements both. |
| 12 | Dec-Jan seasonality treatment | Sensitivity row S6 of §6: Dec-Jan excluded subsample | AR(1)-residualized surprise already partially absorbs seasonality; Dec-Jan-excluded sensitivity tests whether primary `β̂_Rem` survives seasonal removal. | Sensitivity row S6 emitted with n ≈ 789; comparison to primary reported in NB3. |
| 13 | Event-study co-primary | Petro-Trump Jan-2025 event; window [-1,+5] weeks; cumulative-abnormal-RV t-stat; joint-concordance rule | Single documented exogenous event with corroborating evidence (Littio data); 7-week window standard for weekly event-study (Campbell-Lo-MacKinlay 1997). | Spec §7 specifies event date, window, test statistic, joint-concordance rule. NB3 §9 emits both primary-OLS and event-study verdicts side-by-side. |

---

## 13. References

- Aldasoro, I., Beltran, D., and Grinberg, F. (2026). "Stablecoin Inflows and Spillovers to FX Markets." IMF Working Paper WP/26/056 (published 2026-03-27; also issued as BIS Working Paper No. 1340). URL: https://www.imf.org/en/publications/wp/issues/2026/03/27/stablecoin-inflows-and-spillovers-to-fx-markets-575046
- Andrews, D.W.K. (1991). "Heteroskedasticity and autocorrelation consistent covariance matrix estimation." Econometrica 59(3).
- Andrews, D.W.K. (1993). "Tests for parameter instability and structural change with unknown change point." Econometrica 61(4).
- BanRep Borradores de Economía series (methodology placeholder — exact Borrador number, authors, and publication year to be confirmed during Phase-1 data acquisition; corpus lacks a verified entry at spec time). If verified, the reference provides the quarterly-corridor reconstruction recipe invoked by sensitivity row S9. If not verifiable, row S9 is marked `SKIPPED` per §6.
- Bollerslev, T. and Zhou, H. (2002). "Estimating stochastic volatility diffusion using conditional moments of integrated volatility." Journal of Econometrics 109.
- Campbell, J.Y., Lo, A.W., MacKinlay, A.C. (1997). "The Econometrics of Financial Markets," Chapter 4 (Event-Study Analysis). Princeton.
- Gürkaynak, R.S., Sack, B.P., Swanson, E.T. (2005). "Do actions speak louder than words?" International Journal of Central Banking 1(1).
- Kuttner, K.N. (2001). "Monetary policy surprises and interest rates: Evidence from the Fed funds futures market." Journal of Monetary Economics 47(3).
- Newey, W.K. and West, K.D. (1987). "A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix." Econometrica 55(3).
- Reiss, P.C. and Wolak, F.A. (2007). "Structural Econometric Modeling." Handbook of Econometrics Vol 6A, Ch. 64.
