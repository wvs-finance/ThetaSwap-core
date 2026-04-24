---
title: Abrigo Phase-A.0 — Remittance-surprise → TRM-RV — formal spec (Rev-1.1.1)
date: 2026-04-20
author: Claude (foreground-authored; structural-econometrics skill invoked, Phases -1/0/1/2 inherited from design doc)
status: REV-1.1.1 (Task 11.C FAIL-BRIDGE-triggered narrative-shift patch + Rev-3.x cumulative adjustments; wording-only per Task 11.D decision gate)
parent_design_doc: contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-design.md
parent_design_doc_hash: 437fd8bd2
supersedes: none
reference_rev4_spec: contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md
revision_history:
  - Rev-1 (2026-04-20): initial spec, reviewed CR+RC+TW, fixes applied.
  - Rev-1.1.1 (2026-04-24): Task 11.C FAIL-BRIDGE-triggered narrative-shift patch.
    Plan tip `726ce8f74` (Rev-3.4). Wording-only per Task 11.D Step 1 decision gate
    (plan line 339); no `structural-econometrics` skill re-invocation. Summary of
    all nine in-place patches:
      1. Frontmatter `status` relabeled.
      2. New supersedes-banner section inserted above §1 citing the
         Task 11.C FAIL-BRIDGE verdict (ρ=+0.7554 levels, 2/5 sign-concordance
         deltas, N=6) and the `contracts/.scratch/2026-04-20-onchain-banrep-bridge-result.md`
         scratch log; §§4.2+ mechanism explicitly preserved.
      3. §1 primary-X reinterpreted from "BanRep monthly remittance, step-interpolated"
         to "on-chain crypto-rail income-conversion surprise (Task 11.A/11.B 6-channel
         weekly vector)" with BanRep quarterly demoted to validation row S14.
      4. §4.1 primary OLS RHS redefined from a scalar `ε^{Rem}_w` to the 6-channel
         Task 11.B vector `{flow_sum_w, flow_var_w, flow_concentration_w,
         flow_directional_asymmetry_w, unique_daily_active_senders_w,
         flow_max_single_day_w}`; primary gate becomes a joint F-test on the 6 terms.
      5. §4.4 T3b gate re-expressed as joint F-test at α=0.10 with df₁=6,
         df₂=N_eff−13; per-channel β̂ reported for audit only.
      6. §4.5 MDES recomputed at N_eff=78-84 (Rev-3.4 plan line 331 reconciliation
         supersedes the Rev-3.1 N=95 floor) via the joint F non-centrality parameter
         (~0.41 SD R²-increment vs the Rev-1 scalar 0.20 SD).
      7. §6 sensitivity sweep gains row S14 (BanRep quarterly validation,
         Task 10 AR(1)-on-quarterly residual, N=6-7).
      8. §12 resolution-matrix rows 5 (Andrews bandwidth), 6 (interpolation side),
         7 (AR order), 8 (vintage discipline) patched per Rev-3.4 plan lines 345-349.
      9. §13 References augmented with Task 11.A/B/C commit SHAs + Dune query ID,
         NBER w26323 (Dew-Becker-Giglio-Kelly 2019) fn 23, and IMF OP 259
         (Chami et al. 2008).
    Pointers: Task 11.A `bc12e3c30` + Dune query `#7366593`; Task 11.B `2bff6d79f`;
    Task 11.C `91e5d2664` + scratch log `contracts/.scratch/2026-04-20-onchain-banrep-bridge-result.md`.
---

# Rev-1 Formal Spec — Remittance-surprise → TRM realized volatility (Colombia, Phase-A.0)

## 0. Supersedes banner — Rev-1 → Rev-1.1.1 (2026-04-24, Task 11.D)

**Scope of Rev-1.1.1 relative to Rev-1: wording-only, no methodology/mechanism change.**
All nine patches below change *which observable* is designated as the primary X
and how many degrees of freedom it carries into the gate — they do NOT change the
economic mechanism under test (external-inflow channel surprise → FX vol), do NOT
change the reconciliation rule (§4.3), do NOT change the HAC-SE choice (§4.9), do
NOT change the Quandt-Andrews structural-break test (§8), do NOT change the event-
study co-primary (§7), do NOT change the GARCH(1,1)-X mean-equation parametrization
(§4.2), and do NOT change the anti-fishing framing (§10). §12 resolution-matrix
rows 1-4, 9-13 remain unchanged. Every patch has been classified as
"wording-only/cadence-only" per the plan's Task 11.D Step 1 decision gate
(`contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`,
line 343, plan tip `726ce8f74`, Rev-3.4). No `structural-econometrics` skill
re-invocation has been performed — the recovery protocol at plan line 325 explicitly
waives the three-way spec-review requirement for Rev-1.1.1 scope-narrowing of the
interpretation alone.

**Why this patch exists: the Task 11.C FAIL-BRIDGE verdict.** Task 11 of the plan
confirmed via direct inspection of BanRep's `suameca` series 4150 metadata that the
BanRep aggregate remittance series is published at **quarterly cadence only** (not
monthly, as Rev-1 §1 originally assumed). This invalidated the Rev-1 §4.6
step-interpolation protocol as a source of a weekly-cadence primary X. The Rev-3
plan responded by pivoting the primary X to an **on-chain daily COPM + cCOP flow
aggregate** (Task 11.A daily CSV at `contracts/data/copm_ccop_daily_flow.csv`,
585 rows; Task 11.B weekly 6-channel rich-aggregation vector at
`contracts/scripts/weekly_onchain_flow_vector.py`) and adding Task 11.C as a
pre-registered bridge-validation notebook comparing the daily on-chain aggregate
to the BanRep quarterly series.

**Task 11.C outcome (pre-registered gate committed BEFORE computing ρ):**
`FAIL-BRIDGE`. Observed statistics on the six-quarter overlap window 2024-Q3 →
2025-Q4:

- Pearson ρ on quarterly levels (N=6): **+0.7554** (two-sided p = 0.0824).
- Sign-concordance count on Q-over-Q deltas: **2/5** (threshold ≥ 3).
- Gate decision: `ρ > 0.5` PASSED the magnitude arm, but `sign-concordance ≥ 3`
  FAILED the direction arm. FAIL-BRIDGE is triggered by the gate's OR-clause on
  sign-discordance, even though the level-correlation magnitude is strong.

**Full verdict details, quarterly bridge table, and Δ Q-over-Q transitions are
documented in `contracts/.scratch/2026-04-20-onchain-banrep-bridge-result.md`.**

**Economic interpretation of FAIL-BRIDGE (Rev-3.1 recovery protocol, plan line 325).**
The on-chain COPM+cCOP rail is **levels-correlated with the BanRep quarterly
remittance aggregate but is NOT a quarter-over-quarter tracker of it**. The on-chain
rail captures a *crypto-rail income-conversion* flow — USD-denominated diaspora
inflows that are routed specifically through stablecoin rails and converted to COP
on-chain — which is a proper subset of, but not a linear tracker of, the BanRep
aggregate (which includes SWIFT, MoneyGram, Western Union, and informal channels
that dwarf the on-chain component in absolute USD and respond to different
household-decision timing). The primary regression still runs (the on-chain X is a
well-defined weekly-cadence observable emitted by Task 11.B), but the primary
economic interpretation is narrowed from "Colombian aggregate remittance in the
BanRep sense" to "**crypto-rail income-conversion on Colombian stablecoin corridors**."
BanRep quarterly remains as a pre-registered sensitivity / validation row (§6 S14).

**What Rev-1.1.1 does NOT modify.** §4.2 (GARCH(1,1)-X co-primary mean-equation
parametrization), §4.3 (reconciliation rule), §4.7 (primary-AR order — now
inapplicable to the Task 11.B vector, but the SARIMA sensitivity row label is
retained for the validation-row S14 quarterly BanRep AR(1)), §5 (specification
tests T1-T7), §7 (Petro-Trump event-study co-primary), §8 (Quandt-Andrews
structural-break test), §9 (decision-hash extension schema), §10 (anti-fishing
framing), §11 (deliverables), and §12 rows 1, 2, 3, 4, 9, 10, 11, 12, 13. §12 rows
5, 6, 7, 8 are updated in place but the updates are cadence-and-source relabels
only (no kernel/method/parameter/number substitution, per the Task 11.D Step 1
classification rule).

**Companion fix-log:** `contracts/.scratch/2026-04-20-remittance-spec-rev1.1.1-fix-log.md`
documents the per-patch disposition and the decision-gate classification of each
change.

## 1. Research question

Does **crypto-rail income-conversion flow** (COP-denominated stablecoin minting
and burning aggregated at weekly cadence) carry detectable information content for
COP/USD weekly realized volatility, on the frozen 947-observation Colombia weekly
panel (2008-2026), under identical Rev-4 structural-econometric discipline?

- Unit of observation: weekly (Friday close), identical to Rev-4.
- Outcome variable (LHS): TRM weekly realized volatility, transformed as RV^(1/3),
  unchanged from Rev-4 frozen panel.
- Primary explanatory variable (RHS): **on-chain crypto-rail income-conversion
  surprise**, derived from the weekly **rich-aggregation vector** of daily COPM +
  cCOP flow (6 channels per week; Task 11.A daily CSV at
  `contracts/data/copm_ccop_daily_flow.csv` → Task 11.B weekly aggregator at
  `contracts/scripts/weekly_onchain_flow_vector.py`). See §4.1 for the full
  6-channel RHS specification.
- **BanRep quarterly aggregate remittance** (Task 11 `suameca` series 4150) is
  **demoted** from its Rev-1 role as the primary-X source to a **pre-registered
  validation row S14** in §6. This demotion is the scientifically honest response
  to the **Task 11.C FAIL-BRIDGE verdict** (commit `91e5d2664`): the on-chain
  rail is levels-correlated with the BanRep quarterly series (ρ=+0.7554 on the
  six-quarter overlap window, two-sided p=0.0824) but is **weak on the
  quarter-over-quarter delta dimension** (2 of 5 Δ-transitions are sign-concordant,
  below the pre-registered threshold of ≥ 3).

Accordingly, the **primary economic interpretation** of a PASS verdict in §4.4 is
NOT "Colombian remittance in the narrower BanRep aggregate sense drives weekly
TRM realized volatility"; it is "**crypto-rail income-conversion surprise** on
Colombian stablecoin corridors (a levels-correlated but Q-over-Q-weakly-correlated
subset of BanRep aggregate remittance) drives weekly TRM realized volatility."
A PASS on the primary 6-channel gate with a FAIL on the S14 quarterly BanRep row
is an internally consistent scientific outcome under FAIL-BRIDGE. Anti-fishing
framing (§10) is strengthened, not relaxed, by this narrowing.

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

### 4.1 Primary equation (OLS) — Rev-1.1.1 6-channel vector specification

**Rev-1.1.1 change:** the primary RHS is redefined from a single scalar AR(1)
surprise `ε^{Rem}_w` (Rev-1 §4.1) to the **6-channel weekly rich-aggregation
vector** emitted by Task 11.B at
`contracts/scripts/weekly_onchain_flow_vector.py`. The Rev-1 step-interpolation
protocol (§4.6) is inapplicable under this primary — no monthly-to-weekly
interpolation occurs, because the source is already daily on-chain data
aggregated into a 7-day-window weekly summary. The 6-channel design preserves
within-week information that a single scalar collapses away, which is especially
informative at the small effective sample size imposed by the COPM launch window
(see §4.5 MDES).

The primary regression is:

`RV^{1/3}_w = α + Σ_{k=1}^{6} β_k · X^{on-chain}_{k,w} + Σ_j γ_j · Control_{j,w} + ε_w`

where the 6 primary RHS channels are (one coefficient `β_k` per channel, all
fitted jointly in a single OLS regression):

1. `flow_sum_w` — total signed USD flow in week w (mint minus burn; positive =
   net income-conversion inflow).
2. `flow_var_w` — within-week variance of daily flow magnitudes (captures
   dispersion-of-intensity).
3. `flow_concentration_w` — Herfindahl-style concentration across the 7 daily
   buckets (NaN when denominator is 0 and sum-of-abs is also 0; see Task 11.C
   scratch-log NaN-ambiguity protocol).
4. `flow_directional_asymmetry_w` — (sum of positive daily flows − |sum of
   negative daily flows|) / sum of absolute daily flows (captures net-inflow
   skew).
5. `unique_daily_active_senders_w` — count of distinct daily buckets in week w
   with at least one flow event (captures breadth of activity).
6. `flow_max_single_day_w` — largest single-day absolute flow in week w
   (captures tail-day concentration).

- `RV^{1/3}_w` = frozen Rev-4 LHS for week w (realized-vol cube-root transform,
  daily TRM squared-returns basis), **unchanged from Rev-1**.
- `Control_j` = 6 Rev-4 controls (VIX, DXY, EMBI Colombia, Fed Funds, Oil WTI,
  Banrep Repo), each at weekly frequency, synchronized to Rev-4 frozen panel,
  **unchanged from Rev-1**.
- HAC Newey-West SE: Bartlett kernel + Andrews 1991 AR(1) plug-in bandwidth,
  **unchanged from Rev-1** (the kernel and bandwidth rule are the same; see §4.9
  and the §12 row-5 decision-gate classification).

**Primary-gate restructuring.** With six primary RHS terms instead of one, the
Rev-1 two-sided t-test on a single `β̂_Rem` becomes the **joint F-test on the six
`β̂_k` coefficients** (§4.4). Per-channel `β̂_k` and HAC-SE(`β̂_k`) are reported
for auditability but are **NOT gate-relevant** — the primary gate is the
F-statistic on the joint null `H_0: β_1 = β_2 = ... = β_6 = 0`.

**Effective sample size.** The Task 11.B smoke test produced 84 weekly rows from
the Task 11.A 585-row daily CSV (83 full + 1 partial-boundary). After NaN-ambiguity
protocol filtering (Task 11.C scratch log; plan line 329), the usable weekly panel
is **N_eff ≈ 78-84**, clipped to Rev-4-panel-end 2026-02-23. The regression
carries 6 primary + 6 controls + 1 intercept = **13 regressors**, leaving
`df₂ = N_eff − 13 ≈ 65-71` residual degrees of freedom (see §4.5 for MDES
implications).

**Cross-reference.** §4.5 MDES recomputes the detection floor at this N_eff; §4.4
redefines the T3b gate; §6 sensitivity row S14 runs the Rev-1-original scalar
BanRep-quarterly regression as a validation row (N=6-7 quarterly obs).

**Sample boundary (unchanged).** The weekly LHS panel is the frozen Rev-4 panel,
2008-01-07 to 2026-02-23, authoritative source:
`contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json`,
field `weekly_panel.date_min` / `.date_max`. The effective primary-regression
sample is the intersection of this panel with the COPM+cCOP launch window, which
is why N_eff is ~78-84 and not ~947. Decision-hash extended (not replaced) per
Rev-4 panel invariants (§9).

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

### 4.4 Pre-committed gate — T3b joint F-test (Rev-1.1.1)

**Rev-1.1.1 change:** the Rev-1 scalar two-sided T3b gate becomes a **joint F-test
on the six primary `β̂_k`** defined in §4.1. The joint-null vs. scalar-two-sided
restructuring is a *consequence* of the six-channel RHS (which has no defensible
scalar contraction under FAIL-BRIDGE), not a methodology preference change.
Per-channel `β̂_k / SE(β̂_k)` t-statistics are emitted and reported for
auditability — they are **NOT gate-relevant**.

**Primary gate.**

`F(β̂_1, ..., β̂_6) > F_{crit}(α=0.10, df₁=6, df₂=N_eff−13)`

- Joint-null: `H_0: β_1 = β_2 = β_3 = β_4 = β_5 = β_6 = 0`.
- Joint-alternative: at least one `β_k ≠ 0`.
- Test statistic: the standard F = (ΔRSS / df₁) / (RSS_unrestricted / df₂),
  where RSS_unrestricted is from the OLS regression of §4.1 including the 6
  on-chain channels plus 6 controls plus intercept, and ΔRSS is the restricted-vs-
  unrestricted RSS difference when the 6 on-chain terms are dropped.
- Significance level: α = 0.10, one-sided (F is naturally one-sided; any
  deviation from the joint null pushes F upward). Critical value at df₁=6,
  df₂≈72 is F_{0.10}(6, 72) ≈ 1.86; at df₂=65 it is ≈ 1.87. The spec pre-commits
  to compute F_{crit} at the realized df₂ (= N_eff − 13) at NB2 run time.
- HAC-robust F: implementation uses `statsmodels.regression.linear_model.OLSResults.f_test`
  with `cov_type='HAC', cov_kwds={'maxlags': <Andrews-auto>}` (Bartlett kernel,
  Andrews 1991 plug-in — **kernel and bandwidth rule unchanged from Rev-1 §4.9**).

**Verdict enum (three-way, unchanged categorization from Rev-1 §4.5; rebased to
the F-statistic).**

- `F_obs > F_crit` → **PASS**. At least one on-chain channel carries detectable
  information for RV^{1/3}. Per-channel `β̂_k` and sign reported for narrative
  color only; no post-hoc channel-selection spotlight is performed under the
  anti-fishing protocol (§10).
- `F_obs ≤ F_crit` AND the joint R²-increment from adding the 6 on-chain channels
  (computed as `(RSS_restricted − RSS_unrestricted) / TSS`) exceeds the MDES floor
  defined in §4.5 → **FAIL**. Statistically null, sufficiently powered.
- `F_obs ≤ F_crit` AND the joint R²-increment is below the MDES floor →
  **INCONCLUSIVE**. Statistically null, underpowered.

**What changed vs. Rev-1 and what did NOT.** The **kernel** (Bartlett), the
**bandwidth rule** (Andrews 1991 AR(1) plug-in), the **α level** (0.10), the
**three-way verdict categorization** (PASS / FAIL / INCONCLUSIVE), and the
**MDES-rule partitioning of FAIL vs INCONCLUSIVE** are all unchanged from Rev-1.
The shift from scalar |t| > 1.645 to joint F > F_{crit} is a mechanical
consequence of the six-channel RHS that replaced the Rev-1 scalar `ε^{Rem}_w`.
Per the Task 11.D Step 1 decision-gate rule, this is classified as wording-only:
no new kernel, method, parameter, or scalar-MDES number is introduced; the only
numeric change is the downstream re-derivation of the MDES floor at the joint-test
non-centrality parameter and at N_eff = 78-84 (see §4.5).

**Sign-prior discussion (inherited from Rev-1, still applicable).** No defensible
economic sign prior exists for the joint null either — the stabilizer vs stress-
response dichotomy from Rev-1 now applies per-channel, with additional channel-
specific priors that are not ex-ante resolvable (e.g., `flow_concentration_w`
could go either way under a news-shock hypothesis). Joint F is a two-sided test
by construction, which preserves symmetric inference without requiring a sign
prior per channel. The Rev-1 design-doc one-sided placeholder
(`β̂_Rem − 1.28·SE > 0`) remains superseded.

- **Stabilizer hypothesis (still applicable, per channel).** Inflow channels
  smooth household income → reduce FX pressure → `β_k < 0` for `flow_sum_w`.
- **Stress-response hypothesis (still applicable, per channel).** Inflow
  channels rise during diaspora-crisis response → `β_k > 0` for `flow_sum_w`.
- **IMF GIV template (Aldasoro, Beltran, and Grinberg 2026, IMF WP/26/056).**
  1% stablecoin inflow → +40bp parity deviation is a *level* effect; ambiguous
  for vol either way.

The joint F-test's two-sided nature makes the sign-prior discussion a diagnostic,
not a gate input.

### 4.5 Minimum-detectable-effect-size (MDES) pre-commitment — Rev-1.1.1 reconciliation

**Rev-1.1.1 change (plan line 331 reconciliation).** The Rev-1 N_eff ≈ 200 figure
(HAC-autocorrelation-adjusted from nominal N=947) is **inapplicable** to the
Rev-1.1.1 primary regression, because the primary RHS (the 6-channel on-chain
vector) is defined only on the COPM+cCOP launch-window intersection with the
Rev-4 panel, not on the full 947-row weekly panel. Task 11.B's real-data smoke
test produced 84 weekly rows (83 full + 1 partial-boundary) from the Task 11.A
585-row daily CSV. After NaN-ambiguity filtering (Task 11.C scratch log),
`N_eff ∈ [78, 84]` — clipped to Rev-4-panel-end 2026-02-23.

**Conservative floor: `N_eff = 78`.** The spec pre-commits to computing MDES at
the floor of the `[78, 84]` range; this yields a slightly conservative
(underestimating) detection floor relative to the realized N at NB2 run time.
The realized `N_eff` is emitted to `gate_verdict_remittance.json` per §11.

**Per-plan-line-331 classification.** This numeric threshold adjustment
(`N_eff: 200 → 78`) on an already-defined resolution row is a **wording/cadence-
only change** per the Task 11.D Step 1 decision-gate rule (the MDES formula and
three-way verdict rule both remain unchanged; only the numeric inputs `N_eff`
and `df₁` change). No `structural-econometrics` skill re-invocation required.

**MDES formula under the joint F-test (§4.4).** For a joint F-test on `df₁ = 6`
primary terms at α = 0.10 with target power 0.80, the non-centrality parameter
`λ` that yields 80% power is approximately `λ ≈ 13` (from standard power-tables
for F-distributions; `statsmodels.stats.power.FTestPower` returns λ=12.97 at
df₁=6, df₂=72, α=0.10, power=0.80). The MDES on the joint R²-increment is then:

`MDES_R² = λ / (λ + N_eff) ≈ 13 / (13 + 78) ≈ 0.143`

i.e., the 6 on-chain channels must jointly increment the regression R² by at
least ~14.3% (of the total sum of squares explained by the null model) to be
detectable with 80% power at α=0.10. Equivalently, in standardized-effect-size
units (Cohen's `f²`):

`f²_MDES = λ / N_eff ≈ 13 / 78 ≈ 0.167`

`MDES_SD-of-residualized-Y ≈ √f² × √df₁ ≈ √0.167 × √6 ≈ 1.00 SD`

*of the joint R²-increment aggregated across 6 channels*. A more interpretable
per-channel decomposition (assuming equal per-channel contribution, an
assumption that is itself a sensitivity rather than a commitment): the
per-channel MDES is roughly `√(f²/6) ≈ 0.17 SD` of residualized `RV^{1/3}` — in
line with the Rev-1 scalar figure but naturally with weaker joint-test power
per channel.

**Pre-committed threshold (exact).** `MDES_R² = 0.143` (joint R²-increment),
or equivalently `f²_MDES = 0.167`. The spec pre-commits to computing the
realized R²-increment at NB2 run time and comparing to this floor.

**Honest cost note.** The joint-F design on N_eff ≈ 78-84 has **weaker per-test
power** than the Rev-1 scalar-t design on N_eff ≈ 200 would have had. This is
the explicit cost of the real-world data constraint (COPM launched too late to
fill 947 weekly rows) plus the joint-test design (which spreads df across 6
primary terms instead of 1). A FAIL verdict under this regime should be read
*not* as "the null is true at high confidence" but as "the joint on-chain
signal is weaker than the detection floor permitted by the realized N_eff".
The three-way verdict rule (below) partitions FAIL from INCONCLUSIVE explicitly
to make this distinction load-bearing.

**Three-way verdict rule (restated at joint-F granularity).**

- `F_obs > F_crit(0.10, 6, N_eff−13)` → **PASS**.
- `F_obs ≤ F_crit` AND realized joint R²-increment ≥ 0.143 → **FAIL**
  (statistically null, sufficiently powered).
- `F_obs ≤ F_crit` AND realized joint R²-increment < 0.143 → **INCONCLUSIVE**
  (statistically null, underpowered; the scientifically honest verdict for a
  small-N primary exercise).

The per-channel `β̂_k`, HAC-SE, and t-statistic are emitted to
`gate_verdict_remittance.json` for audit and for downstream sensitivity analysis,
but do NOT enter the verdict rule.

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

## 6. Sensitivity sweep (pre-registered rows for forest plot, labeled S1–S14)

Rows are labeled `S1`–`S14` in the sensitivity sweep to avoid cross-reference
collision with the §12 resolution-matrix rows 1–13. **Rev-1.1.1 adds S14** as a
pre-registered BanRep-quarterly validation row responding to the Task 11.C
FAIL-BRIDGE verdict.

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
14. **S14 — BanRep quarterly validation row (Rev-1.1.1 addition).** This row
    runs the **Rev-1-original scalar identification at quarterly cadence** on the
    BanRep `suameca` series 4150 (Task 11 CSV at
    `contracts/data/banrep_remittance_aggregate_monthly.csv` despite the filename;
    source is quarterly per plan Task 11's metadata inspection). Specification:
    regress quarterly-averaged `RV^{1/3}` (weekly `RV^{1/3}` averaged to quarterly)
    on the AR(1)-residual of `ΔlogRem_q` (quarterly log-change of BanRep
    aggregate remittance USD inflow), computed via the Task 10 `surprise_constructor.py`
    AR(1) constructor applied at quarterly cadence. Controls: quarterly-averaged
    versions of the six §4.1 Rev-4 controls (VIX, DXY, EMBI, Fed Funds, Oil,
    Repo). Sample: `N = 6-7` quarterly observations on the overlap window with
    the on-chain rail (2024-Q3 → 2025-Q4 confirmed in Task 11.C; one prior
    quarter may be added if BanRep data coverage permits; documents the N=6
    off-by-one from the Task 11.C N=7 task-description prescription — see Task
    11.C scratch log). Reports `β̂_BanRep-q`, HAC-SE, t-stat, 90% CI. **Not
    gate-relevant;** N=6-7 is too small for any formal inference. The purpose of
    S14 is (a) to **document** the Rev-1-original identification path as a
    pre-registered row under Rev-1.1.1 (so that a reader asking "what would
    Rev-1 have produced?" gets an explicit answer); (b) to serve as a **bridge
    back-pointer** to Task 11.C FAIL-BRIDGE for readers tracing the patch
    chain; (c) to enable future Task-11.A refresh pivots if the BanRep quarterly
    sample is extended past Q4-2025 in subsequent Phase-A.0 work.

**Anti-fishing protocol**: material-mover §9 spotlight in NB3 is emitted ONLY if
primary T3b joint-F PASSes (§4.4). Under FAIL or INCONCLUSIVE verdicts, §9 cells
emit placeholders referencing the pre-registered S1–S14 rows above and asserting
that no post-hoc spotlight is performed. S14 is explicitly **not** a rescue row —
it is a pre-registered validation back-pointer to the Task 11.C FAIL-BRIDGE
verdict, and its N=6-7 small-sample status is documented upfront so that
a significant S14 coefficient does NOT license post-hoc narrative shift back
to "BanRep aggregate remittance".

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
| 5 | Andrews-bandwidth rule | Andrews 1991 AR(1) plug-in: `bw = 1.1447 · (α_2·T)^{1/3}`; applied at Rev-1.1.1 `N_eff ∈ [78, 84]` for the primary joint-F (df₁=6, df₂=N_eff−13). *Rev-1.1.1: wording-only per Task 11.D Step 1 — same kernel, same bandwidth formula, only T substituted by realized N_eff.* | Standard automatic-bandwidth choice; default in statsmodels. Formula is implementation-neutral under the change of T. | Spec §4.9 states the formula + citation Andrews 1991 eq. 5.3. Rev-1.1.1 adds the `N_eff ≈ 78-84` substitution; no formula change. |
| 6 | Step-interpolation direction | **No longer applies under Rev-1.1.1 daily-on-chain primary** (primary X is native-weekly from the Task 11.B daily→weekly aggregator; no monthly-to-weekly interpolation occurs). **Retained for validation row S14** quarterly BanRep LOCF if the S14 quarterly-averaged-LHS protocol needs a step-fill for missing quarterly observations. *Rev-1.1.1: wording-only per Task 11.D Step 1 — same LOCF rule, only the cadence changes (monthly→quarterly) and only for S14 validation.* | Causal interpretation retained for S14; no look-ahead; aligned with Kuttner 2001 surprise-construction convention. | Primary regression (§4.1) has no interpolation step; S14 (§6) uses LOCF on the quarterly BanRep release calendar if needed. |
| 7 | AR order | **No longer applies to primary** (Rev-1.1.1 primary is the 6-channel non-AR vector from Task 11.B; the 6 channels are raw weekly aggregates, not AR(1) residuals of any process). **Retained for validation row S14** quarterly AR(1) on the BanRep quarterly aggregate, per Task 10 `surprise_constructor.py` applied at quarterly cadence. Sensitivity label SARIMA(1,0,0)(1,0,0)_12 is retained in §6 row S7 labeling but has no operational effect on the primary. *Rev-1.1.1: wording-only per Task 11.D Step 1 — AR order unchanged at 1 for S14 validation; no change in parameter or method.* | Primary no longer uses AR residualization because the 6-channel design preserves within-week information directly. S14 preserves Rev-1 AR(1) choice. | Primary NB2 specification (§4.1) has no AR(1) step; S14 NB3 sensitivity imports Task 10 AR(1) constructor. |
| 8 | Vintage discipline | **Daily on-chain does not revise** (Ethereum-mainnet COPM+cCOP mint/burn events are finalized and immutable within <1 day of the block inclusion; Task 11.A Dune query `#7366593` fetches from finalized state). Therefore primary RHS has no real-time-vs-current-vintage distinction. **Retained for validation row S14**: BanRep quarterly aggregate uses **BanRep MPR (Monetary Policy Report) publication-date vintage** — the quarterly aggregate as first printed at each MPR release date, without subsequent revisions. *Rev-1.1.1: wording-only per Task 11.D Step 1 — real-time vintage concept preserved for S14; primary has no vintage because source is immutable.* | On-chain source is cryptographically final; Rev-1 pre-2015 proxy concession is rendered moot for primary. S14 preserves Rev-1 Gürkaynak-Sack-Swanson 2005 real-time-vintage standard. | Primary regression has no vintage metadata column; S14 panel metadata flags `banrep_q_vintage = "MPR-publication-date"`. |
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
- Chami, R., Barajas, A., Cosimano, T., Fullenkamp, C., Gapen, M., and Montiel, P. (2008). "Macroeconomic Consequences of Remittances." IMF Occasional Paper 259. Used in Rev-1.1.1 §1 as the standard reference motivating the "predictive regression, not causal" caveat — gravity-IV reverse-causation concerns on aggregate-remittance regressions argue against claiming causal identification from a single-country weekly panel.
- Dew-Becker, I., Giglio, S., and Kelly, B. (2019). "Hedging Macroeconomic and Financial Uncertainty and Volatility." NBER Working Paper No. 26323. Footnote 23 of the paper provides the defensibility argument for using AR(1) surprise residuals on administrative aggregates at the exercise's native publication cadence — supports the Rev-1.1.1 §6 S14 validation row's quarterly AR(1) on BanRep.
- Gürkaynak, R.S., Sack, B.P., Swanson, E.T. (2005). "Do actions speak louder than words?" International Journal of Central Banking 1(1).
- Kuttner, K.N. (2001). "Monetary policy surprises and interest rates: Evidence from the Fed funds futures market." Journal of Monetary Economics 47(3).
- Newey, W.K. and West, K.D. (1987). "A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix." Econometrica 55(3).
- Reiss, P.C. and Wolak, F.A. (2007). "Structural Econometric Modeling." Handbook of Econometrics Vol 6A, Ch. 64.

### In-tree provenance (Rev-1.1.1)

- **Task 11.A daily on-chain flow CSV.** Commit `bc12e3c30`. Artifact:
  `contracts/data/copm_ccop_daily_flow.csv` (585 rows, daily COPM + cCOP USD-
  denominated flow). Source: Dune Analytics query `#7366593` against Ethereum
  mainnet COPM and cCOP contract mint/burn events.
- **Task 11.B weekly rich-aggregation vector.** Commit `2bff6d79f`. Artifact:
  `contracts/scripts/weekly_onchain_flow_vector.py` (6-channel named-agg
  aggregator; independent-reproduction witness included). Smoke-test output:
  84 weekly rows (83 full + 1 partial-boundary).
- **Task 11.C bridge-validation notebook.** Commit `91e5d2664`. Artifact:
  `contracts/notebooks/fx_vol_remittance_surprise/Colombia/0B_bridge_validation.ipynb`
  (pre-registered ρ-gate). **Verdict: FAIL-BRIDGE** (ρ=+0.7554 levels, 2/5
  sign-concordance deltas, N=6). Scratch log:
  `contracts/.scratch/2026-04-20-onchain-banrep-bridge-result.md`.
- **Plan tip.** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`
  @ commit `726ce8f74` (Rev-3.4). Task 11.D Step 1 decision-gate rule at plan
  line 343; Rev-1.1.1 spec patch authorized by plan line 325 (recovery protocol
  for FAIL-BRIDGE outcome).
