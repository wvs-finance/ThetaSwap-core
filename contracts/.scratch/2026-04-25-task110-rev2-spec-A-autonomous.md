# Task 11.O Rev-2 Spec — Track A (Autonomous) — Inequality-Differential Functional Equation

**Date:** 2026-04-25
**Branch:** `phase0-vb-mvp`
**Track:** A — autonomous spec authoring per Task 11.O dispatch instructions (parallel to user-co-authored Track B; head-to-head review by CR + RC + TW)
**Predecessor commits:**
- `c5cc9b66b` — Task 11.N.2d-rev primary panel (76 weeks joint, gate PASS)
- `2a0377057` — admitted-set fix-up (`_KNOWN_Y3_METHODOLOGY_TAGS` + ValueError guard)
- IMF-IFS sensitivity comparison memo `2026-04-25-y3-imf-only-sensitivity-comparison.md`
- LOCF-tail-excluded reference: Task 11.N.2d-rev memo §CORRIGENDUM
**Skill invoked:** `superpowers:structural-econometrics` (Reiss & Wolak 2007 three-stage decomposition; full skill text loaded in this session)
**Author:** Track-A autonomous agent (no consultation with foreground orchestrator)
**Methodology authority for spec body:** the structural-econometrics skill drives the Reiss-Wolak frame; specific empirical anchors come from the Rev-5.3.2 ingest memos and the FX-vol-CPI-surprise findings digest; analytical specifics (estimator, lag structure, distributional form, control set, specification tests, sensitivity grid) are this Track-A author's pre-registered choices, made transparent and reviewable rather than elicited interactively because the task explicitly designates this as the autonomous parallel track.

---

## 0. Supersession banner (Rev-1 / Rev-1.1 / Rev-1.1.1 retired)

This is **Rev-2** of the Task 11.O analytical spec. It supersedes:

- Rev-1 (initial Colombia-only `Y_asset_leg = (Banrep − Fed)/52 + ΔTRM/TRM` regression on `b2b_to_b2c_net_flow_usd`).
- Rev-1.1 (CR-E2 fix-pass; analytical MDES approximation that overstated λ ≈ 13).
- Rev-1.1.1 (FAIL-BRIDGE narrative shift; pre-Rev-3 transmission re-cast).

Rev-2 reframes the regression for the **Rev-5.3.2 Y₃ inequality-differential / X_d carbon-basket** product thesis:
- **Y₃** = pan-EM working-class-vs-rich return differential (4-country equal-weight aggregate; Rev-5.3.2 primary panel literal `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable`; 76 joint nonzero weekly observations 2024-09-27 → 2026-03-13).
- **X_d** = carbon-basket user volume in USD on Celo (Rev-5.3 primary `proxy_kind = "carbon_basket_user_volume_usd"`; basket-aggregate, user-only filter via `trader != BancorArbitrage`).
- **Asset-leg legacy equation** preserved verbatim in §3.2 as a *component* of the inequality differential's rich-side per the Y₃ design doc, but it is no longer the gate target — Y₃ is.

The Colombia-only asset-leg equation is **byte-exactly preserved**:
```
Y_asset_leg_t = (Banrep_rate_t − Fed_funds_t)/52 + (TRM_t − TRM_{t-1})/TRM_{t-1}
```
This is now diagnostic at the per-country level (Colombia's contribution to `copm_diff` in `onchain_y3_weekly`), not the primary gate. The carry-plus-FX construction is preserved as a documented *narrative bridge* between the prior Colombia-pilot framing and the regional-pan-EM framing of Y₃.

---

## 1. Research question (Reiss-Wolak Phase 0 — Track-A pre-registered)

### 1.1 Economic question

**Does carbon-basket user volume on Celo (X_d) cause weekly variation in the regional inequality differential (Y₃)?**

Specifically: under the Rev-5.3.2 76-week primary panel, does the OLS pooled coefficient β̂_X_d on `carbon_basket_user_volume_usd` (the basket-aggregate user-volume on Carbon DeFi protocol) move Y₃ (the equal-weight 4-country `[CO/BR/EU; KE skipped]` differential `Δ = R_equity + Δlog(WC_CPI)`) by a statistically detectable amount under MDES_SD = 0.40 SD?

**Why this question matters for Abrigo (the product context — corrected framing per `project_abrigo_convex_instruments_inequality.md`):**

Abrigo's product is **convex (option-like) financial instruments** — derivatives with capped-loss / levered-upside payoffs (puts, calls, caps, floors) — that hedge **MACROECONOMIC shocks viewed through the INEQUALITY lens**. Specifically:

- **Shocks are MACRO** (not microeconomic / household-level): CPI release surprises, FOMC decisions, oil-price moves, FX shocks, growth-news releases, BanRep intervention-day events. These are country-level / aggregate disturbances; they are the identifying variation source for the regression in §4.
- **The hedged outcome is INEQUALITY-FOCUSED**: Y₃ measures *how* macro shocks differentially impact rich-asset returns (R_equity_c) versus working-class consumption-bundle returns (Δlog(WC_CPI_c)). The inequality lens enters specifically through Y₃'s WC-CPI **60% food / 25% energy+housing-utilities / 15% transport-fuel** budget-share weighting per `2026-04-24-y3-inequality-differential-design.md` §4 — these are working-class-bundle weights, NOT aggregate-CPI weights. The 60/25/15 weighting IS the inequality-lens marker; it distinguishes Y₃ from a generic aggregate-inequality measure and makes the LHS labor-income-tied by construction.
- **Convex payoffs**: laborers buy options (capped-loss, levered-upside) on Y₃ to hedge their disproportionate exposure to inflation-vs-asset-return divergence during macro shocks. Pricing such payoffs requires the *conditional distribution* of Y₃ given X_d (tails, quantiles, conditional variance) — not the *conditional mean* alone.
- **On-chain capture**: X_d (Mento basket user volume on Celo, observed at the Carbon DeFi `carboncontroller` event log) is hypothesized to reflect retail demand for these convex instruments — i.e., laborers crossing the Mento↔global capital boundary in greater volume when inequality-differential pressure rises.

**What this Rev-2 spec tests:** whether on-chain Mento basket activity (X_d) correlates with the inequality-differential outcome (Y₃) at the **mean** level. Mean-β identification is the **first stage** of product validity — it answers "is there *any* signal" — but it is **necessary-but-insufficient** for convex-payoff pricing. The convex-payoff insufficiency caveat is documented at §11.A and the Rev-3 ζ-group roadmap that closes the convex-instrument gap is enumerated at §10.6. If β̂_X_d is statistically distinguishable from zero with the pre-registered sign at T3b, Abrigo's *linear-payoff* hedge calibration is supported; the convex-payoff calibration requires the §10.6 ζ-group extensions. If T3b fails, the painkiller framing must pivot per §11.

### 1.2 Unit of observation

**Weekly Friday-anchored America/Bogota observations** at the regional aggregate level. Each row = one week, with Y₃ a single scalar (equal-weight 4-country aggregate) and X_d a single scalar (basket-aggregate user volume in USD).

**Why pooled / non-panel:**
Y₃ as currently defined is *already aggregated across countries* (4-country equal-weight; KE skipped → effectively 3-country average). It has no country dimension at the row level. A panel decomposition (one observation per country per week, with country fixed effects) would require:
1. Separate per-country regressions Δ_CO ~ X_d, Δ_BR ~ X_d, Δ_EU ~ X_d, OR
2. A panel with `(week, country)` as the row unit and country FE.

Both are pre-registered as Phase A.1 future-revision options (see §10 Sensitivity panel, item ε.1) — they are deferred to a future spec revision because:
- The Y₃ design doc §5 locked equal-weight aggregation as a *design primitive*, not an estimation choice. Decomposing into country-row panel reverses that design lock.
- A 76-week × 3-country = 228-row panel raises power but introduces cross-country correlation that demands two-way clustered SEs (Cameron-Gelbach-Miller 2011). That is a non-trivial methodological extension.
- The user's structural-econometrics skill discipline forbids preempting the panel decomposition without explicit elicitation; Track A respects that forbearance.

### 1.3 Outcome variable

**Y₃_t = (1/3) × (Δ_CO_t + Δ_BR_t + Δ_EU_t)** in the primary panel (KE skipped per design doc §10 row 1; `kes_diff` is 0/116 in the live DuckDB primary panel).

Where `Δ_country_t = R_equity_country_t + Δlog(WC_CPI_country_t)` (sign convention: rises when inequality widens via either rich-side gains OR working-class cost-of-living squeeze).

### 1.4 Distributional form on Y₃ — pre-registered

**Identity transform (no transform).** Y₃ is already in log-difference units (R_equity = Δlog(equity index); Δlog(WC_CPI) is a log-difference). Re-transforming a log-difference is dimensionally unsound. The FX-vol notebook used `RV^(1/3)` because RV is a *variance* (always positive, heavy right-tail); Y₃ is a *signed log-difference sum* and is roughly mean-zero by construction (live empirical mean = 0.00493, std = 0.01473, range [−0.0424, 0.0418] over the joint 76 observations).

**4-part citation block:**
- **Reference:** Cohen 1988 §9; Box-Cox 1964 (transformation theory). For log-difference outcomes, Box-Cox λ→1 is the natural identity.
- **Why used:** Preserves dimensional consistency with the construct (log-differential of returns + log-differential of CPI). Cube-root is appropriate for variance-like, non-negative LHS; identity is appropriate for signed log-differences.
- **Relevance to results:** Identity preserves the symmetric tails that the pre-registered Wald test on β̂_X_d expects. A re-transform would distort the null-hypothesis distribution.
- **Connection to simulator:** The Layer-2 RAN simulator consumes Y₃ as a hedge-payoff variable. It must be in the same units the regression estimates so that β̂_X_d × X_d_t is interpretable as a hedge-leg movement.

---

## 2. Economic model (Reiss-Wolak Phase 1 — 7 components pre-registered)

### 2.1 Economic environment (Reiss-Wolak Q1a)

**Multi-pool / cross-protocol environment** spanning Carbon DeFi (Bancor) on Celo + Mento basket-stable issuance + global-asset bridges (USDT, USDC, CELO native swaps via Carbon).

The pool of interest is the *Mento↔global-asset boundary on Carbon protocol*, observed as `carboncontroller_evt_tokenstraded` events partitioned into user-initiated (`trader != BancorArbitrage`) vs arb-only (`trader == BancorArbitrage`) per `project_carbon_user_arb_partition_rule`.

### 2.2 Economic actors

Three actors enter the model:

1. **Mento basket users** (price-takers crossing Mento↔global boundary; observed as user-volume in `carbon_basket_user_volume_usd`).
2. **Carbon protocol arbitrageurs** (BancorArbitrage contract `0x8c05ea30…`; observed in `carbon_basket_arb_volume_usd` — diagnostic, not in primary X_d).
3. **Working-class consumers and equity-holding rich** (off-chain; their observable proxy is Y₃).

The structural narrative is that actor (1) — Mento basket users — is the on-chain-native channel through which capital crosses the working-class-stable-vs-global-asset boundary. Volume in (1) is a proxy for the *propensity-to-cross-class* of capital. The hypothesis: when this volume rises, off-chain inequality differential (Y₃) moves in a directionally identifiable way.

### 2.3 Information structure

**Pool state only** for the on-chain side; **published statistical-agency releases** for the off-chain Y₃ inputs. The researcher observes:
- X_d weekly: from `onchain_xd_weekly` (Carbon DeFi event log, full Mento↔global basket).
- Y₃ weekly: from `onchain_y3_weekly` (3-country equal-weight differential at LOCF-tail-extended weekly anchor).
- Controls: from `weekly_panel` (Rev-4 panel: VIX, oil, US CPI, BanRep rate, intervention) and `weekly_rate_panel` (Fed funds, Banrep IBR, TRM Friday close).

What the researcher *does NOT* observe (deferred to Phase 2 stochastic model):
- Bottom-quintile household-level consumption (only proxied via 60/25/15 weighted CPI components).
- Per-trader carbon-protocol intent (only partitioned by trader address into user-vs-arb).
- Cross-country heterogeneity in inequality response to the same X_d shock (collapsed by equal-weight aggregation).

### 2.4 Primitives

1. **Carbon CFMM trading function** — `carboncontroller` evt_tokenstraded conserves a private invariant; the contract is a price-discovery mechanism between Mento and global tokens. (Reference: `project_carbon_defi_attribution_celo`.)
2. **Mento basket-stable peg dynamics** — soft peg of cUSD/cEUR/cREAL/cKES to USD/EUR/BRL/KES respectively (post-rebrand 2026: USDm/EURm/BRLm/KESm; address-level identity preserved per `project_mento_canonical_naming_2026`).
3. **CPI-component price-aggregation rules** — Banrep DANE / IBGE BCB / Eurostat HICP component publication mechanics (monthly cadence, ~30-day lag).
4. **Equity-index dividend-and-trading conventions** — COLCAP / IBOVESPA / STOXX 600 daily quotation, Friday-close convention.

### 2.5 Exogenous variables

**Pre-registered as exogenous (held fixed; identifying variation comes from these):**
- VIX_avg (weekly mean of CBOE VIX) — global risk sentiment proxy.
- Oil_return (log-return of weekly-last positive WTI close) — global commodity factor.
- US_CPI_surprise (AR(1)-expanding-window monthly residual) — US monetary surprise factor.
- BanRep_rate_surprise (event-study ΔIBR sign-preserving sum) — Colombian monetary-policy shock.
- Fed_funds_weekly (effective rate weekly mean from FRED DFF) — global rate environment.
- Intervention_dummy (binary BanRep FX-intervention activity flag) — Colombian FX-policy shock.

**Pre-registered as endogenous OR debatably exogenous (flagged with ⚠️):**
- ⚠️ **X_d (carbon_basket_user_volume_usd)** — the variable of interest; treated as exogenous *under the identifying assumption* that Carbon protocol volume is driven by basket-arbitrage opportunity differentials at a higher-frequency timescale than Y₃ aggregates resolve. This identifying assumption is testable and listed in §6 specification tests (T1: Granger / IV exogeneity).
- ⚠️ **Y₃** itself — endogenous by construction (the LHS).

### 2.6 Objectives and decision variables

The Reiss-Wolak frame requires every actor to have an objective. For this regional-aggregate setting:

- **Mento basket users:** maximize utility from cross-class capital allocation (move capital to whichever side has higher real return). Decision variable = volume crossing the boundary per week.
- **Arbitrageurs:** maximize protocol-arbitrage profit. Decision variable = arb-volume per week. (Excluded from primary X_d; in diagnostic.)
- **Equity-holding rich + working-class consumers:** maximize own utility through portfolio choice (rich) and consumption-bundle choice (working-class). These are the *off-chain agents whose decisions Y₃ aggregates*; they are not modeled at the row level.

### 2.7 Equilibrium concept — pre-registered

**Competitive (price-taking) equilibrium with sequential information arrival.**

- Mento basket users take Carbon CFMM prices as given when crossing the boundary; the cumulative-week's volume is a sufficient statistic for cross-class capital flow.
- Off-chain agents (equity, consumption) settle their own equilibria; Y₃ is the aggregated outcome.
- Sequential information: X_d week-t is observable BEFORE Y₃ week-t in real-time (X_d settles continuously on-chain; Y₃ has CPI-publication lag of ~2-4 weeks). For the *researcher* at memo-write time, both are observed retrospectively at the weekly anchor.

**Why competitive (not Nash, not Stackelberg):**
- No actor in the model has market-making power on the Mento↔global boundary at the basket-aggregate level.
- The off-chain inequality outcome aggregates millions of households and listed firms; no strategic interaction with X_d is plausible at the weekly aggregate.
- A Stackelberg framing (e.g., "Carbon protocol moves first; Y₃ follows") would impose the very causal-priority structure we want to test (and could over-claim it). Competitive is the *neutral* equilibrium concept that lets the data speak.

---

## 3. Stochastic model (Reiss-Wolak Phase 2 — three error sources pre-registered)

The structural-econometrics skill demands that errors be decomposed into η (unobserved heterogeneity), u (agent uncertainty), and v (measurement error). Track-A's pre-registered classification:

### 3.1 Unobserved heterogeneity (η)

What agents observe but the researcher cannot:
- **Carbon protocol's per-trader intent** (we partition arb-vs-user by address but cannot distinguish "Mento-conscious user crossing for FX hedge" from "yield-farmer arbitraging stablecoin spreads"). Concentrated in the basket-aggregate at the weekly level.
- **Off-chain equity-holders' private signals** (insider information, proprietary alpha) that drive the rich-side R_equity component of Y₃.
- **Working-class household-level basket-share heterogeneity** that the pre-registered 60/25/15 weights average over.
- **Cross-country idiosyncratic shocks** (e.g., country-specific labor strikes, tax changes) that the equal-weight aggregation averages over but that move per-country differentials.

η lives in ε_t (the regression error) and is the primary endogeneity-bias risk. Identifying assumption: η is uncorrelated with X_d.

### 3.2 Agent uncertainty (u)

What neither agents nor researcher observe at decision time:
- **Future Mento↔global price moves** (drives this-week volume choice).
- **Future global equity returns** (drives this-week portfolio choice).
- **Future CPI-component publications** (CPI is observed with lag; agents at week-t do not know week-t's CPI).

u is the structural error term — present even under perfect optimization.

### 3.3 Optimization and measurement error (v)

- **Weekly LOCF interpolation of monthly CPI** — introduces autocorrelation (per Y₃ design doc §7); creates a measurement error in Y₃ for weeks within a month.
- **Friday-anchor weekly aggregation** — discrete cut-off means a global-market move on Saturday is reported in next-week's row.
- **3-country aggregate dropping KE** — design pre-registered, but KE's weight (1/3 of theoretical weight when present) flows into the other countries' weights at runtime. This is documented in the methodology literal `_3country_ke_unavailable`.
- **Equity-holiday calendar misalignments** — Y₃ design doc §10 row 4 specifies "rolled to last trading day"; introduces small per-country measurement noise.

### 3.4 Implied error structure

ε_t = η_t + u_t + v_t with:
- E[η_t · X_d,t] = 0 (identifying assumption — must be defended; tested by §6 T1).
- E[u_t] = 0; u_t allowed serial correlation up to autoregressive lag-4 (HAC truncation).
- E[v_t] = 0; v_t induces autocorrelation from the LOCF interpolation (Cavaliere-Taylor 2005 caveat).

---

## 4. Estimation strategy (Reiss-Wolak Phase 3)

### 4.1 Primary specification — pre-registered

**OLS pooled (single time series at the regional-aggregate level), Newey-West HAC standard errors with truncation lag 4.**

**Equation (the implied econometric equation; reviewer Question 3c):**

```
Y₃_t  =  α  +  β · X_d,t  +  γ_1 · VIX_avg_t
            +  γ_2 · oil_return_t
            +  γ_3 · US_CPI_surprise_t
            +  γ_4 · BanRep_rate_surprise_t
            +  γ_5 · Fed_funds_weekly_t
            +  γ_6 · intervention_dummy_t
            +  ε_t
```

Where:
- **β** is the structural coefficient of interest (the *inequality-differential elasticity to carbon-basket user volume*).
- γ_1 … γ_6 are the six pre-registered control coefficients (matches Rev-4 control set byte-exactly except for the inflation-surprise channel — see §4.4 below for the specific re-substitution rationale).
- ε_t is the structural residual (3 components per §3.4).
- HAC(4) per Newey-West 1987; truncation lag 4 per Andrews 1991 data-driven optimal at weekly cadence with mild autocorrelation.

**Lag structure:** *contemporaneous X_d,t only*, pre-registered. The pre-registered sensitivity row (S2 in §10) tests X_d_{t-1} as a one-period-lagged alternative.

**Why contemporaneous (not lag):** the FX-vol-CPI-surprise digest's T1 finding is that CPI surprise is *predictable from lagged information* — its β̂ was a predictive-regression coefficient, not a strict impulse-response. Using a lag here would bake in the same predictive-regression interpretation. Contemporaneous lets us read β as the *concurrent association* — the cleanest read at this MDES.

**Why HAC (not bootstrap as primary):** HAC is the prior-art standard from Rev-4; bootstrap is the *reconciliation* not the primary. The FX-vol notebook ran Politis-Romano stationary block bootstrap and HAC AGREE — bootstrap is now treated as ratification, not replacement.

**Pre-registered reconciliation:** Politis-Romano stationary block bootstrap with mean block length 4 weeks (matches HAC(4)), 10000 resamples, 90% CI. Reported alongside HAC. **AGREEMENT criterion:** 90% HAC CI ⊆ 90% bootstrap CI (and vice versa) at containment ratio ≥ 0.50 by length. (Same criterion as FX-vol notebook §3.5.)

### 4.2 Distributional assumption

**Normal innovations on ε_t for inference; t-distribution sensitivity available.**

- Primary inference: Wald test on β under the working assumption ε_t ~ N(0, σ²). This is the prior-art weak-form distributional assumption that justifies the Newey-West kernel.
- Sensitivity (S5 in §10): Student-t refit (df estimated from data) — the FX-vol notebook found JB rejected normality (skew 0.96, kurt 6.2; Y₃ live data has different but possibly similar fat tails). Student-t absorbs.

**4-part citation block:**
- **Reference:** Newey-West 1987; Andrews 1991; Self-Liang 1987 (boundary-corrected LR for variance-channel sensitivity).
- **Why used:** Heavy-tailed weekly returns + LOCF-induced autocorrelation in Y₃ require both a Heteroskedasticity-and-Autocorrelation-Consistent SE estimator AND a sensitivity to non-normal innovations.
- **Relevance to results:** HAC inflates the SE relative to OLS-naive; if HAC SE is too small, the bootstrap reconciliation flags it. Student-t is independent confirmation.
- **Connection to simulator:** The simulator's payoff variance estimate uses HAC σ̂; if HAC is mis-specified the simulator under/over-prices the hedge.

### 4.3 The implied econometric equation (Question 3c review)

Re-stated for review:

```
Y₃_t  =  α  +  β · X_d,t  +  γ_1·VIX_avg_t  +  γ_2·oil_return_t
        +  γ_3·US_CPI_surprise_t  +  γ_4·BanRep_rate_surprise_t
        +  γ_5·Fed_funds_weekly_t  +  γ_6·intervention_dummy_t
        +  ε_t
ε_t   =  η_t + u_t + v_t   (decomposition per §3.4)
n_obs =  76 (Rev-5.3.2 primary panel; joint nonzero X_d × Y₃ × controls)
```

**Endogenous variables flagged with ⚠️:** X_d (treated as exogenous under §6 T1 identifying assumption — testable).

**Identification strategy:**
- **What variation identifies β:** week-to-week variation in X_d controlling for global factors (VIX, oil), US monetary surprise, Colombian monetary surprise, global rate environment, and Colombian FX intervention. The exclusion is that X_d's residual variation (after partialling out the controls) is uncorrelated with η_t (the unobserved heterogeneity).
- **Defense for the exclusion restriction:** The carbon-basket user volume on Celo is a relatively-thin slice of global capital flow; it is plausibly *driven by* Mento↔global price differentials at sub-weekly cadence rather than driven by aggregate-EM inequality dynamics. The 76-week sample is post-Carbon-protocol launch (2024-08-30+) so the question of whether X_d is truly exogenous to Y₃'s drivers is empirically testable via a Granger-causality / Hausman test.

### 4.3.1 Operationalization of the α+β identification (per user's Q-1b decision)

Track A's α+β identification per the user's Q-1b decision is operationalized via **continuous-control partialing**, not via explicit release-event-window dummies. Specifically:

- The six macro-shock controls (`VIX_avg`, `oil_return`, `US_CPI_surprise`, `BanRep_rate_surprise`, `Fed_funds_weekly`, `intervention_dummy`) absorb the macro-event timing as *continuous regressors*. `US_CPI_surprise` is the AR(1)-expanding-window monthly residual loaded on the publication week; `BanRep_rate_surprise` is the event-study ΔIBR sign-preserving weekly sum; `intervention_dummy` is the binary BanRep FX-intervention activity flag.
- The identifying variation in β̂_X_d is therefore the residual variation in X_d *after* partialling out these continuous macro-shock series — the cumulative residual variation, not narrow-bandwidth event-window jumps.
- **Explicit release-event-window dummies** in the Andersen-Bollerslev-Diebold-Vega (2003) style — e.g., `is_cpi_release_week × X_d` and `is_fomc_release_week × X_d` interactions identifying impulse-windows around release days — are **a deliberate Rev-2.1+ extension**, not an oversight. The `weekly_panel` schema already contains `is_cpi_release_week` and `is_ppi_release_week` columns, so the extension is feasibly executable in a future revision.
- This is a Track-A authoring choice: the continuous-control operationalization gives more sample power and is the cleanest first-stage test for a 76-week post-launch panel; if review of the primary outcome determines that continuous-control partialing is insufficient (e.g., Reality Checker Probe 3 advisory), Rev-2.1 will add the release-event-window interaction rows.

### 4.4 Note on the inflation-surprise channel substitution

Rev-4's control set included `cpi_surprise_ar1` (Colombian CPI surprise). Rev-2 *substitutes this* with `intervention_dummy` (Colombian FX-policy shock). Justification:

1. Y₃ already contains `Δlog(WC_CPI)` directly on the LHS as part of its construction. Re-including a CPI surprise on the RHS would double-count the Colombian inflation channel.
2. `intervention_dummy` is the orthogonal Colombian-policy shock not embedded in Y₃ that the FX-vol notebook found contributes adj-R² = +0.07 (Finding 11 in FX-vol digest; from coefficient ladder Column 4 → 5).
3. Pre-registered per design: this is the spec authoring task's choice, locked at Rev-2 commit. Any subsequent revision must justify the *substitution* (not the inclusion).

**4-part citation block:**
- **Reference:** Anzoátegui-Zapata & Galvis 2019; Uribe-Gil & Galvis-Ciro 2022 BIS WP 1022 (Colombian intervention as a meaningful FX-policy shock).
- **Why used:** Provides Colombian-policy-channel orthogonality without double-counting the CPI surprise that is already in Y₃'s construction.
- **Relevance to results:** Without the substitution, β̂_X_d would absorb double-counted CPI variance and be biased. With the substitution, β̂_X_d is the residual carbon-basket effect after the orthogonal Colombian-policy-shock partial.
- **Connection to simulator:** Layer-2 calibrates β̂_X_d as the hedge ratio; double-counting would mis-calibrate.

---

## 5. Pre-committed parameters (anti-fishing audit table — byte-exact preserved)

| Parameter | Value | Source / anchor | Status |
|---|---|---|---|
| `N_MIN` | **75** | Rev-5.3.1 path α user-approved relaxation 80→75 (`project_rev531_n_min_relaxation_path_alpha`) | PRESERVED byte-exact from Rev-5.3.1 |
| `POWER_MIN` | **0.80** | Rev-4 standard | PRESERVED byte-exact |
| `MDES_SD` | **0.40** SD-units of Y₃ | Rev-5.3 RC-CF-1 BLOCKER scipy verification (Cohen 1988 §9) | PRESERVED byte-exact; free-tuning upward is anti-fishing-banned |
| `MDES_FORMULATION_HASH` | `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` | sha256 of `required_power(n,k,mdes_sd)` source in `scripts/carbon_calibration.py` | PRESERVED byte-exact; live SHA at memo-write time recomputed = MATCH |
| Rev-4 `decision_hash` | `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` | `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json:23` | PRESERVED byte-exact through all schema migrations |
| Y₃ primary methodology literal | `y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable` | Task 11.N.2d-rev commit `c5cc9b66b` + admitted-set fix-up `2a0377057` | PRESERVED byte-exact |
| Y₃ IMF-IFS-only sensitivity literal | `y3_v2_imf_only_sensitivity_3country_ke_unavailable` | Task 11.N.2d.1-reframe | PRESERVED byte-exact |
| X_d primary `proxy_kind` | `carbon_basket_user_volume_usd` | Task 11.N.2c calibration RC-CF-1 collapse | PRESERVED byte-exact |
| Y₃ panel window | [2024-09-27, 2026-03-13] (joint-nonzero) | Task 11.N.2d-rev §3.3 + this spec §1.4 | LOCKED |
| Control set | VIX_avg, oil_return, US_CPI_surprise, BanRep_rate_surprise, Fed_funds_weekly, intervention_dummy | This spec §4.1 (Rev-4 Decisions #7/#8/#5/#6/#9 + Rev-5.3.2 weekly_rate_panel) | LOCKED at Rev-2 commit |
| HAC truncation lag | 4 | Newey-West 1987 + FX-vol Rev-4 prior-art | LOCKED |
| Bootstrap mean block length | 4 weeks | Politis-Romano 1994 stationary block; matches HAC(4) | LOCKED |
| Bootstrap resamples | 10000 | FX-vol Rev-4 prior-art | LOCKED |
| α (one-sided) | 0.10 | Rev-4 / Phase A.0 standard | LOCKED |
| df₁ for power | 6 | Primary block of macro regressors: 6 (control γ's) + 1 (X_d) − 1 (constant) = 6 | LOCKED at Rev-2 commit |

**Anti-fishing audit invariants (per `feedback_pathological_halt_anti_fishing_checkpoint`):**
1. Modification of `MDES_SD`, `MDES_FORMULATION_HASH`, `N_MIN`, `POWER_MIN` requires (a) full design-doc revision, (b) CORRECTIONS block in the next plan revision, (c) full 3-way review cycle.
2. Free-tuning `MDES_SD` upward to chase a target power figure is anti-fishing-banned per X_d design doc §1.
3. Pre-registered FAIL sensitivities (LOCF-tail-excluded, IMF-IFS-only) MUST be reported regardless of primary outcome. If a future revision proposes excluding either, it must justify why the pre-registered FAIL is no longer load-bearing.

**MDES recompute table at three operative N (k=13, MDES_SD=0.40, α=0.10, df₁=6) — verified live at spec-author time:**

| N | required_power | vs POWER_MIN=0.80 | Verdict |
|---|---|---|---|
| 76 (primary) | **0.8689** | ≥ | **PASS** |
| 65 (LOCF-tail-excluded) | **0.8027** | ≥ | **PASS** |
| 56 (IMF-IFS-only) | **0.7301** | < | **FAIL** |

Verified via `scripts.carbon_calibration.required_power(n, 13, 0.40)`; sha256 of the function source matches `MDES_FORMULATION_HASH` byte-exact. **Note:** at n=56 both N_MIN and POWER_MIN fail — the IMF-IFS-only sensitivity is pre-registered to FAIL on *both axes*; this dual-fail is not a defect, it is the discipline-locking purpose of the sensitivity.

---

## 6. The 14-row resolution matrix — pre-registered specification grid

Pre-registered axes (locked at Rev-2 commit):

- **Axis A:** X_d series (3 levels — primary user-volume, arb-only diagnostic, per-currency COPM diagnostic).
- **Axis B:** Y₃ specification (3 levels — primary equal-weight 4-country, sensitivity 3-country IMF-only, sensitivity 65-week LOCF-tail-excluded).
- **Axis C:** Control set (2 levels — full 6-control, parsimonious 3-control { VIX, oil, intervention }).
- **Axis D:** Estimator (2 levels — OLS HAC primary, Politis-Romano bootstrap reconciliation).
- **Axis E:** Lag (2 levels — contemporaneous X_d,t primary, X_d,{t-1} sensitivity).

The full Cartesian (3 × 3 × 2 × 2 × 2 = 72) is intractable; the 14-row pre-committed grid is the *operative* resolution matrix:

| # | Row label | Axis-A | Axis-B | Axis-C | Axis-D | Axis-E | Operative N | Pre-registered verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | **Primary** (gate-bearing) | user-vol | y3_v2 76-wk | full 6-ctrl | OLS+HAC(4) | t | 76 | open (gate target) |
| 2 | Bootstrap reconciliation (primary) | user-vol | y3_v2 76-wk | full 6-ctrl | bootstrap | t | 76 | open (AGREE/DISAGREE with row 1) |
| 3 | **LOCF-tail-excluded sensitivity** | user-vol | y3_v2 65-wk | full 6-ctrl | OLS+HAC(4) | t | 65 | **FAIL pre-registered** (gate would re-test on smaller panel) |
| 4 | **IMF-IFS-only sensitivity** | user-vol | y3_v2 imf 56-wk | full 6-ctrl | OLS+HAC(4) | t | 56 | **FAIL pre-registered** (N < 75; Power < 0.80) |
| 5 | Lag sensitivity | user-vol | y3_v2 76-wk | full 6-ctrl | OLS+HAC(4) | t-1 | 75 | open (one-period lag; tests timing) |
| 6 | Parsimonious controls | user-vol | y3_v2 76-wk | parsimonious 3-ctrl | OLS+HAC(4) | t | 76 | open (collinearity diagnostic) |
| 7 | Arb-only diagnostic | arb-only | y3_v2 76-wk | full 6-ctrl | OLS+HAC(4) | t | 45 | open (under-N; diagnostic only) |
| 8 | Per-currency COPM diagnostic | per-ccy COPM | y3_v2 76-wk | full 6-ctrl | OLS+HAC(4) | t | 47 | open (under-N; per-country narrative cross-check) |
| 9 | Y₃-bond diagnostic (rich-side bond instead of equity) | user-vol | Y₃-bond design-defined | full 6-ctrl | OLS+HAC(4) | t | TBD | open (rich-side construct robustness; Y₃-bond not yet ingested — flagged as future-revision) |
| 10 | Population-weighted Y₃ aggregation | user-vol | y3 pop-weighted | full 6-ctrl | OLS+HAC(4) | t | 76 | open (aggregation choice; flagged as currently-unbuilt fetcher in design doc §5) |
| 11 | Student-t innovations | user-vol | y3_v2 76-wk | full 6-ctrl | OLS+HAC(4)+Student-t | t | 76 | open (heavy-tail robustness) |
| 12 | HAC(12) bandwidth | user-vol | y3_v2 76-wk | full 6-ctrl | OLS+HAC(12) | t | 76 | open (bandwidth robustness) |
| 13 | First-differenced Y₃ + X_d | Δlog X_d | ΔY₃ | full 6-ctrl | OLS+HAC(4) | t | 75 | open (stationarity robustness; matches Rev-4 Decision #11 alt) |
| 14 | **WC-CPI weights sensitivity** (inequality-lens robustness) | user-vol | y3_v2 76-wk re-aggregated under {50/30/20, 60/25/15 (primary), 70/20/10} food/energy-housing/transport-fuel weights | full 6-ctrl | OLS+HAC(4) | t | 76 | open (inequality-lens identification robustness; tests whether β̂ depends on the specific 60/25/15 pre-commitment vs. plausible alternative working-class-bundle definitions) |

**Gate-bearing rows (locked):** Row 1 (primary), Row 3 (LOCF-tail-excluded FAIL), Row 4 (IMF-IFS-only FAIL).

**Row 14 — inequality-lens product-validity row (CR-asked):** the 60/25/15 budget-share weights on Y₃'s WC-CPI component are the inequality-lens marker (per §1.1 product-purpose framing and `2026-04-24-y3-inequality-differential-design.md` §4). Row 14 re-aggregates Y₃ under two alternative bundle weights (food-heavier 70/20/10 and energy-heavier 50/30/20) and re-estimates β̂_X_d for each variant, holding everything else fixed. The pre-registered expectation is that β̂ should be of the same sign and within 1·SE across the three weighting regimes; if β̂ flips sign or shifts by > 1·SE, the inequality-lens identification depends on the specific 60/25/15 pre-commitment and would require a CORRECTIONS-block disclosure. Row 14 is *runnable at Rev-2 commit time* — re-aggregation is a runtime weight change on the existing per-country WC-CPI components, no new fetcher required. Under the corrected product framing, this row is first-class product-validity instrumentation, not "nice-to-have."

**Why this 14-row specification differs from a default reasonable choice:**
- A "default reasonable" 14-row grid would have varied X_d only or controls only, leaving aggregation-rule and Y₃-bond robustness implicit. This grid puts those choices on the matrix explicitly so reviewers can see *what was tested and what was not*.
- A "default reasonable" choice would have made bootstrap and HAC each their own row in a competing-primary sense. This grid demotes bootstrap to *reconciliation* — keeping HAC as primary and bootstrap as ratification (matches FX-vol notebook §3.5 prior-art).
- A "default reasonable" choice would have included a CPI-surprise control. This grid *substitutes intervention_dummy* for CPI surprise (per §4.4); the substitution is documented and reviewable.

**Pre-committed sensitivity verdicts (Section 6 anti-fishing lock):**
- Row 3: **FAIL pre-registered** — joint coverage = 65 weeks < N_MIN = 75 (LOCF-tail-excluded reverse-out drops 11 weeks of post-EU-cutoff LOCF-extended observations, byte-exact matching Reality Checker probe-5 in `2026-04-25-y3-rev532-review-reality-checker.md`).
- Row 4: **FAIL pre-registered** — joint coverage = 56 weeks < N_MIN = 75 (IMF-IFS-only source mix drops 20 weeks; binding country drops to CO+BR at 2025-07-01; verified live in `2026-04-25-y3-imf-only-sensitivity-comparison.md`). Power at n=56 also fails (0.7301 < 0.80) — *dual-axis FAIL*.

These two pre-registered FAILs lock the gate against any future revision that proposes (a) tightening the LOCF policy to exclude tail rows, OR (b) reverting CO→IMF-IFS or BR→IMF-IFS source upgrades. If a downstream review proposes either, the pre-registered FAIL outcome is the immediate reference, not a discoverable-later defense.

---

## 7. Specification tests (Reiss-Wolak Phase 3 Q3d)

Pre-registered tests producing testable implications. Each is bound to a specific assumption and a specific output that a 3-way review can audit.

### T1: X_d strict exogeneity (rejects predictive-regression bias)

| | |
|---|---|
| **Mathematical statement** | E[X_d,t · ε_t] = 0; tested via Hausman / Wu-Hausman |
| **Assumption tested** | §2.5 exogeneity flag on X_d |
| **Test** | Regress X_d_t on lagged X_d_{t-1}, lagged Y₃_{t-1}, lagged controls; F-test joint significance of lagged Y₃ + controls. If REJECT → β is *predictive* not *strict-impulse* (FX-vol Finding 14 carry-forward). |
| **Pre-committed expected outcome** | OPEN. (FX-vol's CPI-surprise REJECTED at F=15.12; X_d on Carbon protocol is at sub-weekly cadence so prior is *less* likely to reject — but still must be tested.) |
| **Effect on β̂ interpretation** | If T1 REJECTS: β̂ is interpreted as predictive-regression coefficient; product framing pivots to monthly-cycle hedge per FX-vol product read. If T1 FAILS-TO-REJECT: β̂ is impulse-response interpretation; product framing stays at weekly. |

### T2: announcement-window variance premium

| | |
|---|---|
| **Mathematical statement** | Var[Y₃_t | week is X_d-spike] ≠ Var[Y₃_t | week is X_d-quiet] |
| **Assumption tested** | Whether X_d-active weeks systematically differ in volatility |
| **Test** | Levene's test on Y₃ variance partitioned by week-quantile of X_d (top quartile vs bottom quartile) |
| **Pre-committed expected outcome** | OPEN. (FX-vol T2 FAILED-TO-REJECT for CPI-release weeks; X_d may differ but unclear.) |
| **Effect on result** | If REJECT → variance-channel transmission is also viable; need GARCH-X follow-up. |

### T3a / T3b: gate verdict

| | |
|---|---|
| **T3a (two-sided)** | t-test β̂/SE vs 0 |
| **T3b (one-sided gate)** | β̂ − 1.28 · HAC SE > 0 (one-sided positive 90%) |
| **Pre-committed sign** | **β > 0**: rising X_d → rising inequality differential. (Hypothesis: more carbon-basket user volume = more cross-class capital flow = more *observable* inequality pressure.) |
| **Sign justification** | Per `project_abrigo_inequality_hedge_thesis` and the inequality-differential Y₃ design doc §1: Y₃ rises when inequality widens via either rich-equity gains OR working-class cost-of-living squeeze. If X_d (carbon basket flow) is the on-chain proxy for cross-class capital flow, rising X_d should accompany rising inequality differential. |
| **Effect on gate** | T3b PASS → product painkiller framing supported; T3b FAIL → pivot per §11. |

### T4: Ljung-Box residual serial correlation

| | |
|---|---|
| **Mathematical statement** | Q-statistic on ε̂_t at lags 1..8 |
| **Assumption tested** | HAC(4) is sufficient for autocorrelation correction |
| **Pre-committed expected outcome** | OPEN. If REJECT at lag > 4, HAC(12) sensitivity (row 12) becomes the binding read. |

### T5: Jarque-Bera normality

| | |
|---|---|
| **Test** | JB on ε̂_t |
| **Effect** | If REJECT → Student-t refit (row 11) becomes the gate-binding read. |

### T6: structural break (Bai-Perron)

| | |
|---|---|
| **Test** | Bai-Perron 1998 unknown-break test on the 76-week panel |
| **Pre-committed expected outcome** | OPEN. (Carbon protocol launched 2024-08-30; one structural break at protocol-launch is mechanically expected; the question is whether the 76-week post-launch window itself has further breaks.) |
| **Effect** | If breaks → subsample report; otherwise full-sample is the binding read. |

### T7: identifying-assumption robustness

| | |
|---|---|
| **Test** | Run row 6 (parsimonious controls) and check whether β̂ from row 1 vs row 6 are within 1·SE of each other |
| **Pre-committed expected outcome** | OPEN. If row 1 and row 6 disagree by > 1·SE, the full-control specification is over-fitting; report parsimonious as alternative primary. |

---

## 8. Identification (how each parameter is identified)

| Parameter | Identifying variation | Identifying assumption (testable) |
|---|---|---|
| α | Cross-sample mean of Y₃ at X_d=0 reference | Linearity of mean structure |
| β | Week-to-week variation in X_d after partialling controls | E[X_d · η] = 0 (T1) |
| γ_1 (VIX) | Global risk-sentiment shocks orthogonal to X_d residual | E[VIX · η_residual] = 0 (orthogonality holds at weekly cadence per FX-vol Finding 7 max-corr 0.142) |
| γ_2 (oil) | Global commodity shocks | Same |
| γ_3 (US CPI surprise) | US monetary surprise residual | Same; AR(1) operator pre-fit per Rev-4 Decision #5 |
| γ_4 (BanRep rate surprise) | Colombian monetary surprise event-day | Pre-fit per Rev-4 Decision #6 |
| γ_5 (Fed funds weekly) | Global rate environment | Pre-fit per Task 11.M.6 panel extension |
| γ_6 (intervention dummy) | Colombian FX-policy shock | Pre-fit per Rev-4 Decision #9 + S7 freshness sensitivity acknowledged |

---

## 9. Anti-fishing audit trail (per `feedback_pathological_halt_anti_fishing_checkpoint`)

This spec authoring honors the discipline catalog:

1. **No silent threshold tuning:** All thresholds in §5 are PRESERVED byte-exact from prior commits. Nothing was tuned at Rev-2 to chase a desired N or power.
2. **Pre-registered FAIL sensitivities:** Rows 3 (65-week) and 4 (56-week) are pre-registered to FAIL on N_MIN. They MUST be reported regardless of primary outcome. They lock the gate against silent re-tuning of LOCF policy or source mix.
3. **Pre-registered sign:** β > 0 is locked at Rev-2 commit. If primary β̂ is *negative-significant*, that is a counter-finding (akin to FX-vol's β̂_CPI = −0.000685); honest reporting per the FX-vol product-read pivot is the discipline.
4. **No mid-stream X_d swap:** Primary X_d is locked to `carbon_basket_user_volume_usd`. If the regression fails on that, the fail is reported; substituting `b2b_to_b2c_net_flow_usd` (which has 79 nonzero weeks vs 76 for user-volume — 3 more) post-hoc is anti-fishing-banned.
5. **Sign-flip transparency:** If T3b primary FAILS but a sensitivity row passes positive-significant, the FX-vol §9 anti-fishing-HALT discipline applies: the spotlight is HALTED; sensitivity is kept as pre-registered record only; product framing pivots transparently.
6. **MDES formulation hash:** Live SHA256 of `required_power` source = `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` byte-exact match with PIN at memo-write time.
7. **No code modification:** This spec does not modify any code, plan, design doc, or DuckDB table — pure analytical document.
8. **Honest framing of identification weakness:** Per FX-vol Finding 14, the primary β̂ may be a predictive-regression coefficient if T1 rejects; this spec pre-commits to that interpretation flag rather than insisting on impulse-response under all conditions.

---

## 10. Sensitivity grid (Reiss-Wolak Phase 4)

The 14-row resolution matrix in §6 IS the operative sensitivity grid; this section adds the *future-revision* sensitivity options that are explicitly OUT-OF-SCOPE for Rev-2 but reserved for Phase A.1 if Rev-2's primary returns a positive verdict.

### Future-revision options (deferred per §1.2)

- **ε.1 — Country-level panel decomposition.** Decompose Y₃ into per-country `(week, country)` rows; estimate `Δ_country,t = α + δ_country + β · X_d,t + ...` with country FE and two-way clustered SEs (Cameron-Gelbach-Miller 2011). Requires Y₃ design doc revision; NOT preempted in Rev-2.
- **ε.2 — Bond-anchored Y₃.** Replace `R_equity` with 10Y sovereign-bond yield-change per design doc §3 diagnostic. Requires bond-data fetcher infrastructure; flagged as resolution-matrix Row 9.
- **ε.3 — Population-weighted aggregation.** Replace 1/4 equal-weight with population-weighted (CO/BR/EU shares). Requires extending the aggregator with a weight-vector argument. Flagged as resolution-matrix Row 10.
- **ε.4 — Crypto-vol Y candidate.** Reconsider crypto-portfolio returns as a rich-side add-on per Y₃ design doc §3 (excluded from primary per Q2 ruling). NOT in Rev-2 scope; could re-enter at structural-econometrics future-revision.
- **ε.5 — Intraday event-window.** Sub-weekly event-window analysis around large X_d-day shocks. Outside Rev-4 weekly-cadence prior-art; requires daily Y₃ proxy reconstruction; deferred per FX-vol product-read pivot path 3.

### 10.6 ζ-group: Convex-payoff future-revision extensions (Rev-3 roadmap)

The ε-group above contains *mean-effect* extensions of the same OLS+HAC framework (panel decomposition, alternative aggregations, alternative cadences). Per the corrected product framing in §1.1 and `project_abrigo_convex_instruments_inequality.md`, mean-β identification is **necessary-but-insufficient** for convex-instrument pricing. The ζ-group enumerates the analytical moves that close the convex-instrument identification gap in a future Rev-3 spec — these are the distributional-welfare / tail-risk / variance-channel extensions that the Q-1b α+β-only ruling deferred at Rev-2 scope but does NOT preclude at Rev-3 scope:

- **ζ.1 — Quantile regression β̂(τ) at τ ∈ {0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95}** (Koenker-Bassett 1978). Tests for asymmetric quantile shift — i.e., does X_d shift Y₃'s lower tail (working-class cost-of-living squeeze under stress) more than the upper tail (rich-side gains under stress)? Asymmetry is directly product-relevant: a convex put-floor on Y₃ is priced from lower-tail behavior, while a convex call on Y₃ is priced from upper-tail behavior.
- **ζ.2 — GARCH(1,1)-X with X_d in the conditional-variance equation.** Estimate `σ²_t(Y₃) = ω + α·ε²_{t-1} + β·σ²_{t-1} + δ·X_d,t`. Tests whether X_d amplifies Y₃ volatility (vega-relevant for option premia). FX-vol Rev-4 prior-art ran this as a co-primary reconciliation — directly transplantable. δ̂ > 0 supports option-premium scaling on X_d shocks.
- **ζ.3 — Lower-tail conditional moment regression.** Estimate `E[Y₃ | Y₃ < q_τ, X_d]` at τ ∈ {0.05, 0.10}. Tests whether large positive X_d shocks correspond to lower-tail compression of Y₃ (the convex put-floor downside-protection mechanism). This is the most direct test of the convex-payoff hedging thesis.
- **ζ.4 — Option-implied volatility surface fitting.** Once an Abrigo prototype is live (or a synthetic option-pricing model is calibrated against historical conditional Y₃ distribution from ζ.1–ζ.3), compute the option-implied volatility surface and link β̂ from this Rev-2 to actual option premia under Black-Scholes basics + Heston / Bates extensions. Final-stage product-pricing test.

Each ζ row gets pre-registration discipline equivalent to the current 14-row matrix at Rev-3 authoring time: pre-committed sign hypothesis, pre-committed FAIL sensitivities, anti-fishing-locked thresholds, CORRECTIONS-block discipline on any threshold modification. The ζ-group is the explicit Rev-3 scope handoff; downstream Phase 5 / Task 12 implementation against Rev-2 mean-β should treat the ζ extensions as the next-spec dependency, not as an in-scope amendment to Rev-2.

---

## 11. Failure scenarios + product-read pivot (per FX-vol prior-art lessons)

Three pre-registered scenarios for the Rev-2 estimation outcome, with locked product-framing implications:

### Scenario A: T3b primary PASS (positive-significant)

- Product painkiller framing supported **at the linear-payoff hedge level only**: Abrigo can position as on-chain inequality-differential hedge calibrated on β̂_X_d for *forward-like / swap-like* (linear-payoff) instruments. Convex-payoff (option, cap, floor) calibration requires the §10.6 ζ-group extensions and is NOT supported by Rev-2 evidence alone.
- Sensitivity row 5 (lag) and row 11 (Student-t) reported as robustness.
- Sensitivity row 14 (WC-CPI weights sensitivity) determines whether β̂ is robust to the specific 60/25/15 inequality-lens pre-commitment vs. plausible alternative working-class-bundle weightings — first-class product-validity instrumentation under the inequality-lens framing.
- T1 REJECT vs FAIL-TO-REJECT determines whether β̂ is impulse-response (clean) or predictive (still actionable but framed differently).
- Honest framing: "primary specification supports the *linear-payoff hedge* painkiller at mean-β level; sensitivities AGREE; product calibration anchored on β̂_X_d at Rev-2 spec for linear instruments; convex-payoff calibration deferred to Rev-3 ζ-group per §10.6".

### 11.A Convex-payoff insufficiency caveat (per `project_abrigo_convex_instruments_inequality.md`)

A T3b PASS at the mean-β level is **necessary but NOT sufficient** for convex-instrument pricing. The §1.1 product-purpose framing locates Abrigo's product as convex (option-like) instruments hedging macroeconomic shocks viewed through the inequality lens; convex payoffs (puts, calls, caps, floors) are priced from the **conditional distribution** of Y₃ given X_d — its tails, quantiles, and conditional variance — not from the conditional mean alone. Specifically:

1. **Mean-β identification is first-stage / linear-hedge calibration only.** β̂_X_d × X_d_t at §12 is interpretable as a *forward-like* hedge-leg coefficient for linear-payoff instruments (forwards, swaps, fixed-leg constructs). It is NOT interpretable as an option-pricing parameter without further tail-risk evidence.
2. **Convex-instrument pricing requires CONDITIONAL VARIANCE / QUANTILE / TAIL evidence** — not just mean-shifts. In Black-Scholes basics, the option premium's dominant gradient is vega (∂Premium/∂σ); variance behavior dominates the level. In heavier-tailed frameworks (Heston, Bates, GARCH-X), the option premium is explicitly tail-driven. Mean-β tells you only how the *center* of Y₃'s distribution shifts under X_d — the hedge buyer pays for tail behavior, not center behavior.
3. **This Rev-2 spec consciously defers tail-risk to Rev-3** (see §10.6 ζ-group roadmap: quantile regression β̂(τ), GARCH-X conditional-variance, lower-tail conditional regression, option-implied-vol surface fitting). The Q-1b α+β-only ruling applied to Rev-2 scope; it does not preclude Rev-3 from re-introducing distributional-welfare evidence (quantile shifts, variance amplification, lower-tail stabilization) that the convex-instrument purpose analytically requires.
4. **Honest interpretation of the T3b PASS result:** "Y₃'s mean shifts with X_d in a direction consistent with the linear-hedge thesis" — NOT "Abrigo can price options from this β̂." A future engineer wiring β̂ into a convex-payoff pricer would miscalibrate the product. The simulator-pricing claim at §12 is therefore valid only for *linear-payoff* hedge instruments; convex payoffs require Rev-3 ζ-group evidence before any pricing-model calibration.

This caveat is the load-bearing product-validity disclosure for Rev-2: mean-β identification is the **first stage** of a multi-stage product-validity test; Rev-2 ships the first stage cleanly, and the §10.6 ζ-group is the explicit Rev-3 dependency that closes the convex-instrument calibration gap.

### Scenario B: T3b primary FAIL + sensitivity row positive-significant

- FX-vol prior-art protocol applies: §9 spotlight HALT; sensitivity stays in record but cannot be promoted to primary.
- Product framing pivot: weekly-X_d hedge no longer painkiller; pivots to next-best-available pre-registered row.
- Honest framing: "at pre-registered primary, no effect detected; at [sensitivity], positive effect at 90%; commercial positioning pivots from weekly-X_d hedge to [sensitivity-X_d-window] hedge, grounded as pre-registered robustness".

### Scenario C: T3b primary FAIL + all sensitivities FAIL

- Inequality-differential hedge thesis at this spec is empirically null.
- Product framing: pivot to brainstorm-α (payments/consumption — see `project_phase_a0_exit_verdict`) or brainstorm-β (yet-to-be-defined alternative).
- Honest framing: "the carbon-basket-user-volume → inequality-differential transmission is null at the Rev-5.3.2 panel; Phase A.0 exhausted at this thesis; user-driven Phase A.1 required".

---

## 12. Connection to Layer-2 RAN simulator (per `feedback_notebook_citation_block` requirement #4)

**Scope qualification (per §11.A convex-payoff insufficiency caveat):** the simulator-calibration claims in this section are valid only for *linear-payoff* hedge instruments (forwards, swaps, fixed-leg constructs). Convex-payoff calibration (options, caps, floors, levered structures) requires the §10.6 ζ-group Rev-3 extensions; β̂_X_d alone cannot calibrate a convex-instrument premium without further tail-risk evidence.

If T3b PASS:
- β̂_X_d × X_d_t becomes the *first-stage linear hedge-leg coefficient* in the simulator (linear payoffs only).
- HAC(4) σ̂_β̂ is the *uncertainty band* on the hedge-leg payoff (linear-payoff regime).
- Bootstrap CI at row 2 ratifies the simulator's confidence interval input.
- For convex-payoff calibration: simulator awaits Rev-3 ζ-group quantile / variance-channel parameters.

If T3b FAIL:
- Simulator does NOT calibrate against this spec's β̂.
- Sensitivity rows that pass become *candidate hedge-leg coefficients* at their pre-registered cadence.
- Product framing for the simulator is "no Rev-2 hedge calibration; pending alternative spec".

---

## 13. Files this spec consumes (read-only, no modification at Rev-2 commit)

- `/contracts/data/structural_econ.duckdb` (read-only):
  - `onchain_y3_weekly` filtered to `source_methodology = 'y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable'` (primary; 116 rows, 76 joint with X_d).
  - `onchain_y3_weekly` filtered to `source_methodology = 'y3_v2_imf_only_sensitivity_3country_ke_unavailable'` (sensitivity; 116 rows, 56 joint with X_d).
  - `onchain_xd_weekly` filtered to `proxy_kind = 'carbon_basket_user_volume_usd'` (82 rows, 77 nonzero).
  - `weekly_panel` (Rev-4 panel; controls VIX_avg, oil_return, US_CPI_surprise, BanRep_rate_surprise, intervention_dummy; 76 of 76 covered in joint window).
  - `weekly_rate_panel` (Task 11.M.6 extension; controls Fed_funds_weekly).

- `/contracts/scripts/carbon_calibration.py` (read-only):
  - `required_power(n, k, mdes_sd)` (sha256 hash byte-exact preserved).
  - `MDES_FORMULATION_HASH`, `N_MIN`, `POWER_MIN`, `MDES_SD` constants (byte-exact preserved).

- `/contracts/scripts/econ_query_api.py` (read-only):
  - `load_onchain_y3_weekly(source_methodology=...)` (post-Rev-5.3.2 default flipped to v2 primary literal).
  - `load_onchain_xd_weekly(proxy_kind=...)`.

- `/contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json:23` (read-only):
  - Rev-4 `decision_hash = 6a5f9d1b…` byte-exact preserved.

---

## 14. Out of scope (deferred per `feedback_agent_scope`)

- **No code modification.** This is an analytical spec; downstream Task 11.Q assembles the multi-Y panel and Task 12 (Phase 2b) runs the regression.
- **No DuckDB schema migration.** Existing `onchain_y3_weekly`, `onchain_xd_weekly`, `weekly_panel`, `weekly_rate_panel` are consumed read-only.
- **No plan-body modification.** Task 11.O Step 2b's pre-registered FAIL sensitivities are honored byte-exact; no rewrite at this Rev-2 spec.
- **No design-doc modification.** Y₃ design doc + X_d design doc are PRESERVED byte-exact.
- **No country-level panel decomposition** (per §1.2).
- **No bond-anchored Y₃** (per §10 ε.2).
- **No population-weighted aggregation** (per §10 ε.3).
- **No crypto-vol Y candidate** (per §10 ε.4).
- **No intraday event-window** (per §10 ε.5).

---

## 15. References

### Methodological
- Reiss & Wolak 2007, "Structural Econometric Modeling: Rationales and Examples from Industrial Organization", *Handbook of Econometrics* Vol 6A, Ch. 64, §4.1–4.3 (the three-stage decomposition that drives this spec's Phases 1-3).
- Newey & West 1987, "A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimator", *Econometrica* 55(3): 703-708.
- Andrews 1991, "Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimation", *Econometrica* 59(3): 817-858.
- Politis & Romano 1994, "The Stationary Bootstrap", *JASA* 89(428): 1303-1313.
- Cohen 1988, *Statistical Power Analysis for the Behavioral Sciences*, 2nd ed., Chapter 9 (the f² formulation pinned in `MDES_FORMULATION_HASH`).
- Bai & Perron 1998, "Estimating and Testing Linear Models with Multiple Structural Changes", *Econometrica* 66(1): 47-78.
- Self & Liang 1987, "Asymptotic Properties of Maximum Likelihood Estimators and Likelihood Ratio Tests under Nonstandard Conditions", *JASA* 82(398): 605-610 (boundary-corrected LR for variance-channel sensitivity, prior-art carry-from FX-vol Task 19).
- Cameron, Gelbach & Miller 2011, "Robust Inference with Multiway Clustering", *Journal of Business & Economic Statistics* 29(2): 238-249 (deferred to ε.1 panel-decomposition future revision).
- Cavaliere & Taylor 2005 (LOCF / volatility-noise unit-root caveat per Y₃ design doc §7).
- Hausman 1978, "Specification Tests in Econometrics", *Econometrica* 46(6): 1251-1271 (T1 exogeneity test).
- Box & Cox 1964, "An Analysis of Transformations", *JRSS-B* 26(2): 211-252 (LHS transform pre-commitment).

### Empirical / context
- `project_fx_vol_econ_complete_findings.md` — FX-vol-CPI-surprise prior-art digest (gate_verdict=FAIL; A1 monthly + A4 release-day-excluded sensitivities; predictive-regression caveat from T1 REJECT).
- `project_abrigo_inequality_hedge_thesis.md` — product framing.
- `project_carbon_defi_attribution_celo.md` — Carbon protocol Celo deployment (CarbonController + BancorArbitrage addresses).
- `project_carbon_user_arb_partition_rule.md` — user-vs-arb partition mechanics.
- `project_mento_canonical_naming_2026.md` — Mento basket-stable rebrand context.
- `project_y3_inequality_differential_design.md` — Y₃ construct invariants.
- Anzoátegui-Zapata & Galvis 2019 (Banrep working paper on FX-intervention shock identification).
- Uribe-Gil & Galvis-Ciro 2022, BIS WP 1022 (Colombian monetary policy + intervention shock characterization).

### Files / commits
- Y₃ primary panel ingest memo: `contracts/.scratch/2026-04-25-y3-rev532-ingest-result.md`.
- Y₃ IMF-IFS-only sensitivity comparison memo: `contracts/.scratch/2026-04-25-y3-imf-only-sensitivity-comparison.md`.
- Y₃ coverage HALT disposition: `contracts/.scratch/2026-04-25-y3-coverage-halt-disposition.md` (path ζ frozen).
- Carbon X_d design: `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md`.
- Y₃ design: `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md`.
- Plan: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` §Task 11.O.
- MDES function: `contracts/scripts/carbon_calibration.py` :: `required_power`.

---

## 16. Track-A author's pre-registered analytical position vs "default reasonable"

A "default reasonable" Rev-2 spec on this dataset would have:
1. **Used OLS pooled with bootstrap as primary** (because n=76 is small). Track A makes HAC(4) primary (matching FX-vol Rev-4 prior-art) and bootstrap reconciliation — preserving the prior-art protocol over a small-N defensiveness reflex.
2. **Included Colombian CPI surprise as a control** (since it is in the prior-art Rev-4 panel). Track A *substitutes* `intervention_dummy` because Y₃ already contains Δlog(WC_CPI) on the LHS (§4.4).
3. **Run cube-root or log Y₃ transform** (matching FX-vol RV^(1/3) prior-art). Track A keeps identity transform because Y₃ is already a signed log-difference (§1.4).
4. **Added a country fixed-effects panel decomposition** to recover the additional 228−76 = 152 row-equivalents. Track A defers this to ε.1 future-revision because the Y₃ design doc §5 locked equal-weight aggregation as a *design primitive*, and decomposition reverses that lock.
5. **Treated X_d as endogenous and propose an IV** (e.g., Carbon-protocol arbitrage opportunity index). Track A flags X_d's exogeneity status as **testable via T1** and pre-commits to the predictive-regression interpretation if T1 rejects — rather than fabricating an IV without a defensible exclusion.

Each of these choices is *defensible* but *not default*. The spec's review value to CR / RC / TW is in surfacing exactly these choices for adversarial scrutiny.

---

## 17. Reviewer-facing summary (Track A, autonomous)

| Item | Track A position |
|---|---|
| Product purpose framing | Convex (option-like) instruments hedging MACROECONOMIC shocks viewed through the INEQUALITY lens (per §1.1 + `project_abrigo_convex_instruments_inequality.md`); WC-CPI 60/25/15 weighting is the inequality-lens marker |
| Rev-2 scope | Mean-β identification only (first-stage / linear-hedge calibration); convex-payoff calibration deferred to Rev-3 ζ-group per §10.6 |
| Estimator | OLS pooled, HAC(4) primary; Politis-Romano stationary block bootstrap reconciliation (mean block length 4) |
| α+β operationalization | Continuous-control partialing of 6 macro-shock series (per §4.3.1); explicit release-event-window dummies (Andersen-Bollerslev-Diebold-Vega 2003 style) deferred to Rev-2.1+ |
| Lag | Contemporaneous X_d_t primary; X_d_{t-1} sensitivity row 5 |
| LHS transform | Identity on Y₃ (Y₃ is already log-difference; cube-root is dimensionally inappropriate) |
| Distributional form on ε | Normal primary; Student-t sensitivity row 11 |
| Control set | 6 controls: VIX_avg, oil_return, US_CPI_surprise, BanRep_rate_surprise, Fed_funds_weekly, intervention_dummy. Notable: `cpi_surprise_ar1` SUBSTITUTED with `intervention_dummy` to avoid double-counting Y₃'s own LHS Δlog(WC_CPI) |
| Sign hypothesis | β > 0 (rising X_d → rising inequality differential) |
| Significance threshold | T3b one-sided 90% (β̂ − 1.28·SE > 0) — matches FX-vol Rev-4 prior-art |
| Resolution matrix | 14 rows (§6); Row 14 (WC-CPI weights sensitivity at 50/30/20, 60/25/15-primary, 70/20/10) is first-class inequality-lens product-validity instrumentation |
| Pre-registered FAIL sensitivities | Row 3 (65-week LOCF-tail-excluded) FAIL; Row 4 (56-week IMF-IFS-only) FAIL on both N_MIN and POWER_MIN |
| Pre-registered POSITIVE-significant sensitivities | None at this spec (Track A does NOT pre-register that A1/A4-style positive sensitivities will fire; that is FX-vol-specific and not transplantable to this 76-week post-launch panel) |
| Convex-payoff insufficiency caveat | §11.A: T3b PASS supports linear-payoff hedges only; convex (option/cap/floor) calibration requires §10.6 ζ-group Rev-3 evidence (quantile β̂(τ), GARCH-X variance, lower-tail conditional regression, option-implied-vol surface) |
| Anti-fishing posture | All thresholds in §5 byte-exact preserved; modification requires CORRECTIONS-block + 3-way review cycle |
| Product-pivot map | §11 pre-registered three scenarios (PASS-linear-hedge, primary-FAIL-sensitivity-PASS, all-FAIL); Rev-3 ζ-group is the explicit convex-instrument calibration handoff |

**End of Track A spec.** Awaiting head-to-head review by CR + RC + TW against Track B.
