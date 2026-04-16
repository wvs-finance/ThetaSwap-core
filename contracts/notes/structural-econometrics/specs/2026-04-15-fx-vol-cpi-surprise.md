# Structural Econometric Specification: Colombian Price-Level Surprise → COP/USD FX Realized Volatility

**Date:** 2026-04-15 (Rev 4: pre-committed primary + fishing-fix)
**Skill:** structural-econometrics (Reiss & Wolak 2007 framework)
**Status:** Rev 4. **Phase 5 CONDITIONALLY UNBLOCKED** — 3 data sources located as free-tier (BanRep EME, IBR via Datos Abiertos, SUAMECA). Download artifacts (filename, row count, date range) must be produced during Phase 5 Step A before estimation starts. SUAMECA intervention series ID unconfirmed.
**Upstream:** Tier 1 literature deliverable (`contracts/notes/structural-econometrics/identification/2026-04-14-inflation-mirror-two-channel-literature.md`, verdict: `PIVOT_TO_TIER_1B`)
**Downstream:** Layer 2 Angstrom pool parameterization (deferred until β estimated)

---

## 1. Research Question

**Economic question (Phase 0a):** Does Colombian price-level surprise (CPI + PPI) explain weekly realized COP/USD FX volatility, and at what magnitude?

**Parameter of interest:** $\beta$ — semi-elasticity of weekly FX realized vol to Colombian price-level surprise. Gate: $\operatorname{adj-}R^2 \geq 0.15$ out-of-sample ($\tau_{\text{op}}$).

**Unit of observation (Phase 0b):** Week (Monday–Friday). Daily COP/USD log-returns from FRED `DEXCOUS` aggregated to weekly realized vol. N ≈ 1,100 weekly observations (~2003–2025); ~260 release weeks, ~840 non-release weeks.

**Outcome variable (Phase 0c):** Three co-primary LHS specifications (Rev 2: log(RV) demoted from sole primary after Model QA flagged ABDE 2001 normality requires high-frequency data, not n=5 daily returns):
- $\text{RV}_t^{1/3}$ (cube-root) — Wilson-Hilferty (1931) normal approximation to chi-squared. **Exploratory** (Rev 4: the chi-squared premise requires iid normal returns; COP/USD daily returns are fat-tailed with vol clustering, violating both. The cube-root mechanically reduces skew but is NOT theoretically justified at n=5 for non-Gaussian data.) Pre-committed primary LHS despite exploratory label — chosen as best available variance-stabilizer at low n, with log(RV) and raw RV as sensitivity.
- $\log(\text{RV}_t)$ — exploratory (ABDE 2001 normality argument does not apply at n=5; treat as candidate, not theoretically justified)
- $\text{RV}_t$ (raw) — direct $g^{\text{pool}}$ mapping for product pitch

**PRE-COMMITTED PRIMARY SPECIFICATION (Rev 4 — anti-fishing):**

The gate decision (adj-R² ≥ τ_op, T3a, T3b) is evaluated on ONE pre-committed specification only:

$$\text{RV}_t^{1/3} = \alpha + \beta \cdot s_t^{\text{CPI}} + \gamma_1 \cdot s_t^{\text{US CPI}} + \gamma_2 \cdot s_t^{\text{BanRep}} + \gamma_3 \cdot \text{VIX}_t + \gamma_4 \cdot I_t + \gamma_5 \cdot r_t^{\text{oil}} + \varepsilon_t$$

- LHS: RV^{1/3} cube-root (exploratory variance-stabilizer; chi-squared premise does not strictly hold for fat-tailed returns but mechanically reduces skew)
- RHS: CPI survey surprise (BanRep EME consensus) if available; AR(1) residual if not (reported as separate result, not substituted silently)
- Controls: full set (US CPI + BanRep rate + VIX + intervention + oil return)
- Estimation: OLS + Newey-West HAC (lag=4)
- Decomposition: CPI-only (PPI enters only in sensitivity)

All other specifications are classified as:
- **Confirmatory** (GARCH-X co-primary): if it agrees with the primary on sign + significance, the result is reinforced; if it disagrees, investigate and report both
- **Sensitivity** (A1–A9): reported for robustness; do NOT determine the gate
- **Exploratory** (log(RV), raw RV, AR(1) fallback, CPI+PPI decomposition): inform interpretation but are not pre-committed

This eliminates the 24-specification fishing problem: ONE test determines the gate; ~15 additional tests inform interpretation with the caveat that at least one will be significant by chance at 5%.

**Reconciliation protocol (OLS vs GARCH-X, Rev 4):** If the pre-committed OLS primary and the GARCH-X confirmatory AGREE on T3a (β ≠ 0) and T3b (β > 0 with CI): product gate passes, both estimates reported. If they DISAGREE: report both, flag the discrepancy, do NOT claim the gate passed. Investigate source of disagreement (vol persistence, distributional assumption, surprise construction). The OLS primary ALONE does not override a contradicting GARCH-X.

**Why this matters:** The RAN (Range Accrual Note) on a hypothetical cCOP/USDC Angstrom pool hedges purchasing-power erosion from macro shocks. The pool observable $g^{\text{pool}} \approx \phi^2 V(P)/(8L)$ (Milionis 2022) captures FX realized vol. β quantifies how much of that vol is driven by Colombian price-level news — the economic channel the hedge targets.

---

## 2. Economic Model

### 2.1 Economic Environment (Phase 1a)

**Two-layer model:**

- **Layer 1 (empirical):** Colombian FX market (COP/USD, TRM). Real data, reduced-form estimation. β estimated here. Justified by Rincón-Torres, Rojas-Silva, Julio-Román 2021 (BanRep be_1171): FX is the efficient Colombian macro-shock aggregator ($a_{21}=-0.067$ FX→TES, $a_{12}=-0.001$ TES→FX). Macro shocks hit FX directly — no intermediate rate/bond channel needed.

- **Layer 2 (synthetic):** Hypothetical cCOP/USDC Angstrom pool. Parameterized by Layer 1 β. $g^{\text{pool}}$ constructed from β + liquidity assumptions. Deferred until β is in hand.

Layer 1 feeds Layer 2. No circularity.

### 2.2 Economic Actors (Phase 1b)

**Layer 1 (reduced-form — no individual optimization):**

| Actor | Role | Modeled as |
|---|---|---|
| DANE | Information source: publishes CPI + PPI on pre-scheduled calendar | Exogenous |
| FX market (composite) | Price discovery: banks, corporates, pension funds, foreign investors trade COP/USD on SET FX | Reduced-form return/vol process (not individually modeled) |
| BanRep | Monetary policy + FX intervention | Control variables ($s_t^{\text{rate}}$, $I_t$) |
| US authorities (Fed, BLS) | External conditions | Controls ($s_t^{\text{US CPI}}$, VIX) |

**Layer 2 (structural — deferred):**

| Actor | Objective | Decision | Reference |
|---|---|---|---|
| ARB | Max $\Pi^{\text{ARB}} = B - \text{bid cost}$ | Swap size + Angstrom bid | Milionis 2022 |
| LP_short | Max $\Pi^{LP_s} = [LVR + \kappa] - IL - \pi + U_{\text{RAN}}^{\text{payout}}$ | Liquidity + tick range + RAN purchase | Cao-Kogan 2025; notebook §Two-LP |
| LP_long | Max $\Pi^{LP_\ell} = [LVR + \kappa] - IL + \pi - U_{\text{RAN}}^{\text{payout}}$ | Liquidity + tick range + RAN writing | Cao-Kogan 2025; notebook §Two-LP |

### 2.3 Information Structure (Phase 1c)

- **Layer 1:** All public, simultaneous. DANE releases, BanRep decisions, US macro news, VIX — all observable by all market participants at the same time. No private information in the announcement channel.
- **Layer 2:** Pool state + external FX oracle (COP/USD from Layer 1). Standard per Milionis 2022, Cao-Kogan 2025.

### 2.4 Primitives (Phase 1d)

**Layer 1:** Minimal. β_price is the estimated parameter. FX market price-discovery efficiency taken as given (be_1171).

**Layer 2 (deferred):** CLAMM trading function, Angstrom auction fee schedule ($\phi$), LP risk preferences (observation-window heterogeneity), imported β from Layer 1, exogenous liquidity endowment (scenario-parameterized: $50K, $500K, $5M daily).

### 2.5 Exogenous Variables (Phase 1e)

| Variable | Symbol | Exogeneity justification |
|---|---|---|
| CPI+PPI surprise | $s_t^{\text{price}}$ | DANE pre-schedules releases (timing exogenous); consensus orthogonality (Andersen et al. 2003 §II) |
| US CPI surprise | $s_t^{\text{US CPI}}$ | Determined by BLS/Fed, not COP/USD dynamics |
| BanRep policy-rate surprise | $s_t^{\text{BanRep}}$ | Pre-scheduled monthly meetings; surprise is orthogonal to same-week FX vol if consensus is rational |
| VIX | $\text{VIX}_t$ | Determined by US equity options; exogenous to Colombian FX specifically |
| WTI/Brent oil return | $r_t^{\text{oil}}$ | Rev 2 addition: Colombia = oil exporter; COP/USD heavily oil-correlated. Weekly oil return exogenous to Colombian CPI release timing. FRED `DCOILWTICO` or `DCOILBRENTEU`. |
| DANE release calendar | deterministic | Institutional design; fixed annually |

### 2.6 Objectives and Decision Variables (Phase 1f)

- **Layer 1:** No explicit optimization. FX participants' collective behavior produces realized vol. Reduced-form event study.
- **Layer 2:** Three optimization problems (ARB, LP_short, LP_long) producing three first-order conditions. Deferred.

### 2.7 Equilibrium Concept (Phase 1g)

- **Layer 1:** None (reduced-form). Standard for event studies (Andersen et al. 2003).
- **Layer 2:** Competitive / price-taking (Milionis 2022). LPs and ARBs solve independently; no strategic interaction.

---

## 3. Stochastic Model

### 3.1 Unobserved Heterogeneity (Phase 2a)

Variables affecting FX vol that agents observe but the researcher cannot:

| Source | Treatment | Bibliography |
|---|---|---|
| BanRep FX intervention | **5th control** ($I_t$ intervention dummy). Free data from SUAMECA portal. | be_1171 §3; BIS 462 |
| FX dealer inventory positions | Accept in $\varepsilon_t$ — unobservable even in be_1171 | No paper controls for this |
| Foreign investor portfolio flows | Accept in $\varepsilon_t$ — not available at weekly frequency | Ahmed-Akinci-Queralto 2023 treats flows as outcome, not control |
| Market microstructure state | Not needed at weekly frequency — averages out | CLM Ch. 3; be_1171 §3.2 (intraday only) |
| Concurrent non-DANE news (oil, politics) | Partially controlled (US CPI, rate, VIX); residual in $\varepsilon_t$ | ABDV 2003 §V (known limitation at lower frequency) |

### 3.2 Agent Uncertainty (Phase 2b)

Variables that NEITHER agents NOR researcher observe at decision time:

1. Future CPI/PPI values before DANE release (resolved by announcement → generates the surprise)
2. Intra-week timing of vol response (same-day jump vs multi-day absorption)
3. Other agents' reactions to the release (aggregate uncertainty)
4. BanRep intervention timing within the week

All absorbed into the structural error term. Standard for reduced-form event studies.

### 3.3 Optimization and Measurement Error (Phase 2c)

| Source | Type | Bias direction |
|---|---|---|
| BanRep consensus bias (monthly survey, potential staleness) | Optimization error | Attenuation on β (overstated surprise) OR upward (stale consensus overstates) |
| Delayed portfolio rebalancing (sluggish adjustment) | Optimization error | Attenuation (repositioning spills to next week) |
| FRED noon rate vs SET FX close | Measurement error in LHS | Attenuation (inflates residual variance, widens SEs) |
| Monthly consensus vs intra-month updates | Measurement error in RHS | Attenuation (classical errors-in-variables) |
| VIX as proxy for Colombian risk appetite | Measurement error in control | Small, ambiguous direction |

### 3.4 Implied Error Structure

$$\varepsilon_t = \underbrace{\eta_t}_{\text{unobserved heterogeneity}} + \underbrace{u_t}_{\text{agent uncertainty}} + \underbrace{v_t}_{\text{measurement error}}$$

**Net bias: AMBIGUOUS.** Most error sources attenuate β (measurement error in LHS/RHS, delayed rebalancing, microstructure noise). However, S1 (stale monthly BanRep consensus overstating the surprise) may bias β UPWARD — if the consensus systematically lags true expectations, the constructed surprise is inflated, and β overestimates the true effect. The net direction cannot be signed a priori. A significant $\hat{\beta}$ is NOT guaranteed to be a lower bound. The "conservative for the product" safety claim does NOT hold unconditionally — it depends on the consensus-bias test T1 passing (if T1 rejects, the upward-bias channel is active).

---

## 4. Estimation Strategy

### 4.1 Functional Forms (Phase 3a)

**Primary (Rev 2: CPI-only, three co-primary LHS transforms, oil control added):**

$$f(\text{RV}_t) = \alpha + \beta \cdot s_t^{\text{CPI}} + \gamma_1 \cdot s_t^{\text{US CPI}} + \gamma_2 \cdot s_t^{\text{BanRep}} + \gamma_3 \cdot \text{VIX}_t + \gamma_4 \cdot I_t + \gamma_5 \cdot r_t^{\text{oil}} + \varepsilon_t$$

where $f(\cdot) \in \{(\cdot)^{1/3},\, \log(\cdot),\, \text{identity}\}$ (Rev 3: cube-root primary per Wilson-Hilferty 1931; log exploratory; raw for g^pool mapping).

**Co-primary estimation approach B: GARCH(1,1)-X** (Rev 3: promoted from A7 per all three reviewers — the Colombian FX-vol literature's workhorse model; OLS on transformed RV and GARCH-X are co-primary, not alternatives):

$$r_t = \mu + \sqrt{h_t}\, z_t, \quad z_t \sim N(0,1)$$
$$h_t = \omega + \alpha_1 \varepsilon_{t-1}^2 + \beta_1 h_{t-1} + \delta \cdot |s_t^{\text{CPI}}|$$

where $|s_t^{\text{CPI}}|$ enters in ABSOLUTE VALUE (Rev 3 fix: $s_t$ in levels would push $h_t$ negative on negative surprises; Han & Kristensen 2014 JoE, Engle & Rangel 2008 require $|s_t|$ or $s_t^2$ in the variance equation). $\delta > 0$ = CPI surprise magnitude increases conditional FX variance. Estimated by MLE. Refs: Sentana & Fiorentini 2001 (identification); be_1171 §3 (Colombian implementation of heteroskedasticity-identified VAR with GARCH).

For asymmetric effects: $\delta^+ \cdot s_t^{+} + \delta^- \cdot |s_t^{-}|$ where $s^+ = \max(s,0)$, $s^- = \min(s,0)$ (tests whether upside CPI surprises are more disruptive than downside under IT regime).

$s_t^{\text{CPI}}$ = Colombian CPI surprise only (standardized: DANE release − BanRep consensus, divided by historical σ). PPI enters via co-primary decomposition below, NOT bundled.

$r_t^{\text{oil}}$ = weekly WTI/Brent log-return (Rev 2 addition: Colombia is an oil exporter; COP/USD is heavily oil-correlated per be_1171. Missing oil control was flagged as identification threat at weekly frequency).

**Co-primary decomposition (Rev 2: promoted from A2 sensitivity):**

$$f(\text{RV}_t) = \alpha + \beta_1 \cdot s_t^{\text{CPI}} + \beta_2 \cdot \Delta\text{IPP}_t + \gamma_1 \cdot s_t^{\text{US CPI}} + \gamma_2 \cdot s_t^{\text{BanRep}} + \gamma_3 \cdot \text{VIX}_t + \gamma_4 \cdot I_t + \gamma_5 \cdot r_t^{\text{oil}} + \varepsilon_t$$

where $\tilde{s}_t^{\text{PPI}} = (\Delta\text{IPP}_t - \overline{\Delta\text{IPP}}) / \hat{\sigma}_{\Delta\text{IPP}}$ is STANDARDIZED PPI change (Rev 3: mean-subtracted and σ-divided, same scale as $s_t^{\text{CPI}}$, so $\beta_1$ and $\beta_2$ both measure "vol response per 1-SD shock" and are directly comparable). If $\beta_1 \gg \beta_2$: CPI dominates → "inflation hedge" claim holds. If $\beta_2 \geq \beta_1$: producer-cost channel dominates → product is "price-level hedge" not "inflation hedge" specifically.

**Fallback if BanRep consensus is unavailable (Rev 3: separate co-primary, not silent substitution per Adversarial Referee):** If the BanRep Encuesta de Expectativas is not machine-readable historically, replace $s_t^{\text{CPI}}$ with an AR(1) forecast residual: $\hat{s}_t^{\text{CPI}} = \Delta\text{IPC}_t - \hat{\mathbb{E}}_{t-1}[\Delta\text{IPC}_t]$ where $\hat{\mathbb{E}}$ is the AR(1) conditional mean. This is a DIFFERENT object than a survey surprise — it tests "does CPI deviate from its own recent trend predict FX vol?" rather than "does CPI deviate from market expectations predict FX vol?" The two are not substitutes; both should be reported if survey data is available, and the AR(1) version alone if not. Ref: Andersen et al. 2003 §II note that survey-based and time-series-based surprises produce quantitatively similar results for US data; verification needed for Colombian CPI.

**Robustness:** Release-day exclusion (R2), Student-t (R3).

### 4.2 Distributional Assumptions (Phase 3b)

**Primary:** $\varepsilon_t \sim N(0, \sigma^2)$ with Newey-West HAC standard errors (lag = 4 weeks). OLS estimation.

**Sensitivity:** Student-t MLE (R3) if Jarque-Bera rejects normality of residuals.

Citation: Andersen et al. 2003 (HAC SEs); Newey & West 1987; ABDE 2001 (log-RV normality).

### 4.3 Implied Econometric Equation (Phase 3c)

$$f(\text{RV}_t) = \alpha + \beta \cdot s_t^{\text{CPI}} + \gamma_1 \cdot s_t^{\text{US CPI}} + \gamma_2 \cdot s_t^{\text{BanRep}} + \gamma_3 \cdot \text{VIX}_t + \gamma_4 \cdot I_t + \gamma_5 \cdot r_t^{\text{oil}} + \varepsilon_t$$

| Variable | Source | Free-tier? | Rev 2 notes |
|---|---|---|---|
| $\text{RV}_t = \sum_{d \in \text{week}} r_d^2$ | FRED `DEXCOUS` | ✓ | Pre-committed primary: RV^{1/3} (cube-root). Exploratory: log(RV), raw RV. |
| $s_t^{\text{CPI}}$ (CPI surprise ONLY) | DANE IPC release + BanRep consensus survey | **⚠️ UNVERIFIED** | Rev 2: BanRep Encuesta de Expectativas historical archive must be verified as free/downloadable before Phase 5. be_1171 used Bloomberg for expectations (§2.4 fn.16). If BanRep survey is not machine-readable historically, Bloomberg dependency is real. |
| $\Delta\text{IPP}_t$ (co-primary decomposition) | DANE IPP release (raw Δ, no consensus) | ✓ | Enters ONLY in co-primary decomposition, not bundled with CPI |
| $s_t^{\text{US CPI}}$ | FRED (AR(1) surprise proxy) | ✓ | |
| $s_t^{\text{BanRep}}$ | BanRep rate decisions + IBR-implied consensus | **⚠️ UNVERIFIED** | Rev 2: may need term IBR data (Bloomberg/Refinitiv) vs overnight IBR (BanRep publishes). Verify before Phase 5. |
| $\text{VIX}_t$ | FRED `VIXCLS` | ✓ | |
| $I_t$ (intervention dummy) | BanRep SUAMECA portal | **⚠️ UNVERIFIED** | Rev 2: machine-readable time-series not confirmed. May be PDF reports only. Verify before Phase 5. |
| $r_t^{\text{oil}}$ (oil return) | FRED `DCOILWTICO` (WTI) or `DCOILBRENTEU` (Brent) | ✓ | Rev 2 addition: Colombia = oil exporter; COP/USD heavily oil-correlated. Missing oil control was a BLOCK from Model QA. |

**Three data sources flagged ⚠️ UNVERIFIED require verification before Phase 5 data pipeline starts.** If any fails, the spec must be amended (BanRep consensus → AR(1) proxy; IBR → simple lag of policy rate; intervention → omit with noted limitation).

### 4.4 Identification

**Source of variation:** Pre-scheduled DANE CPI+PPI release timing.

**Exclusion restriction:** $\mathbb{E}[s_t^{\text{price}} \cdot \varepsilon_t] = 0$ conditional on controls. Backed by:
- Timing exogeneity: DANE pre-schedules (Andersen et al. 2003 §II)
- Surprise orthogonality: consensus is rational (Balduzzi, Elton, Green 2001; testable via T1)
- Heteroskedasticity backup: variance-shift identification (Rigobon & Sack 2003; Sentana & Fiorentini 2001)
- Multi-announcement conditioning: US CPI + BanRep rate + VIX + intervention absorb non-Colombian-price channels (ABDV 2003 eq. 2)
- Colombian implementation: be_1171 §2.4 + §3.1; rinconHortuaSilvaRoman 2023

**Threat investigated and mitigated:** DANE releases CPI and PPI on the same day (DANE calendar 2026). CPI+PPI treated as composite hedge target (not confound). Same-week SIPSA (food) and exports are subcomponents or lower-magnitude. Employment and GDP fall in different weeks by calendar design.

### 4.5 Layer 1 → Layer 2 Mapping Gap (Rev 2, per Adversarial Referee)

**OPEN ISSUE:** The regression estimates β on TOTAL weekly FX realized vol ($\text{RV}_t = \sum r_d^2$). But the RAN underlying $U_{\text{RAN}} = \Phi(A(L) \cdot [f_n(g(i_S)) - f_n(g(i_T))] / f_d(g))$ depends on the DIFFERENTIAL between tail-range and target-range growth — not total vol.

If a CPI surprise raises vol UNIFORMLY across all tick ranges (i.e., arb activity increases proportionally at every tick), then $g(i_S) - g(i_T) \approx 0$ and $U_{\text{RAN}} \approx 0$ — the hedge produces no payout despite β > 0.

The hedge works only if CPI surprise raises vol DISPROPORTIONATELY in the tail ticks relative to the target ticks. This is a LAYER 2 question that Layer 1's β does not answer.

**What Layer 2 must specify (deferred to post-β):**
1. A model of how CPI-surprise-induced arb flow distributes across ticks (uniform vs concentrated).
2. Under what liquidity conditions (LP placement patterns) does the surprise-induced flow concentrate in tails vs target.
3. The functional relationship: $U_{\text{RAN}} = h(\beta, L_{\text{target}}, L_{\text{tail}}, \text{surprise magnitude})$ where $h$ is derived from the CLAMM + differential structure.

**Gate structure (Rev 3: "necessary but not sufficient" per all three reviewers):**

Layer 1 β > 0 is **necessary** — if CPI surprise doesn't increase total FX vol, the pool observable has no signal to read.

Layer 1 β > 0 is **NOT sufficient** — the hedge additionally requires that CPI-surprise-induced vol concentrates disproportionately in tail ticks relative to target ticks.

**Falsifiable closure condition (Rev 4: threshold is a PLACEHOLDER pending Layer 2 power analysis — not derived from a model):** The mapping gap closes IF Layer 2 simulation demonstrates that under the estimated β and realistic LP placement patterns, the ratio $g(i_S)/g(i_T)$ during CPI-surprise weeks DIFFERS from $g(i_S)/g(i_T)$ during non-surprise weeks by a threshold $\tau_{\text{tick}}$ (placeholder: 10%, subject to revision after Layer 2 power analysis determines the minimum detectable effect size given pool liquidity and LP placement assumptions). If the ratio is indistinguishable → vol distributes uniformly across ticks → $U_{\text{RAN}} \approx 0$ despite β > 0 → **product thesis fails at the tick-concentration step**, not the macro-signal step.

**If the gap is unfillable** (uniform distribution is the empirical reality for macro-driven vol on CLAMMs), then the RAN as specified cannot hedge inflation specifically — it can only hedge total FX vol without tick-range discrimination. This would require redesigning $U_{\text{RAN}}$ to depend on total $g^{\text{pool}}$ rather than the differential $g(i_S) - g(i_T)$.

---

## 5. Specification Tests

| # | Implication | Tests | Statement | Method | Reject → |
|---|---|---|---|---|---|
| T1 | Surprise unpredictable | Consensus rationality | $\mathbb{E}[s_t \mid s_{t-1}, \text{RV}_{t-1}, \text{VIX}_{t-1}] = 0$ | F-test on lagged predictors | Consensus biased → β biased |
| T2 | Release weeks higher vol | Announcement channel exists | $\text{Var}(\text{RV} \mid \text{release}) > \text{Var}(\text{RV} \mid \text{non-release})$ | Levene test | No channel → β uninformative |
| T3a | β ≠ 0 (statistical) | Surprise moves vol | $\beta \neq 0$ | Two-sided t-test | β=0 → surprise doesn't move vol → no signal |
| T3b | β > 0 with confidence (product gate, Rev 4) | Surprise INCREASES vol — required for g^pool to accrue more in shock weeks | $\hat{\beta} - 1.28 \cdot \text{SE}(\hat{\beta}) > 0$ (lower bound of 90% one-sided CI exceeds zero) | One-sided CI check on the PRE-COMMITTED PRIMARY spec only | β̂ positive but CI includes zero → insufficient conviction; β̂ < 0 → hedge reverses. Either case: product thesis does not pass. Evaluated ONLY on pre-committed primary (§1), NOT on any sensitivity or exploratory spec. |
| T4 | Residuals uncorrelated | Model captures dynamics | $\mathbb{E}[\varepsilon_t \varepsilon_{t-k}] = 0$, $k=1,...,8$ | Ljung-Box Q | Add lagged RV / ARMA |
| T5 | Residuals normal | Log-transform works | $\varepsilon \sim N$ | Jarque-Bera | Switch to Student-t (R3) |
| T6 | No structural break | β stable across regimes | $\beta_{\text{pre}} = \beta_{\text{post}}$ | Chow / Bai-Perron | Report sub-samples |
| T7 | Intervention control adequate | $I_t$ absorbs intervention | β stable with/without $I_t$ | Compare estimates | Intervention contaminated β |

---

## 6. Sensitivity Analysis

### 6.1 Sensitive Assumptions

| # | Assumption | Sensitivity risk |
|---|---|---|
| S1 | Surprise construction (monthly consensus) | β upward-biased if stale consensus overstates surprise |
| S2 | Weekly aggregation horizon | β scales with horizon (Rincón-Torres 2023) |
| S3 | Sample period / regime stability | β may differ across 2003–14 / 2015–20 / 2021–25 |
| S4 | CPI+PPI composite vs CPI-only | Composite may dilute or amplify relative to CPI-only |
| S5 | VIX as global-risk proxy | Poor proxy → residual global risk in ε |

### 6.2 Alternative Specifications

| # | Variant | Change | Purpose |
|---|---|---|---|
| A1 | Monthly horizon | LHS = log(monthly RV); N ≈ 260 | Test horizon scaling |
| A2 | CPI vs PPI decomposition | Separate $\beta_1 \cdot s^{\text{CPI}} + \beta_2 \cdot \Delta\text{IPP}$ | Which signal dominates |
| A3 | Sub-sample splits | 2003–14, 2015–20, 2021–25 | Regime stability |
| A4 | Release-day exclusion | LHS excludes CPI/PPI release day | Multi-day persistence; CPI-vs-PPI isolation |
| A5 | Lagged RV control | Add $\log(\text{RV}_{t-1})$ as 6th regressor | Announcement effect above vol clustering |
| A6 | Bivariate (no controls) | $f(\text{RV}_t) = \alpha + \beta \cdot s_t^{\text{CPI}} + \varepsilon$ | Benchmark: do controls matter? |
| A7 | **GARCH(1,1)-X** (Rev 4: CONFIRMATORY co-primary, not alternative. Promoted from A7 in Rev 3 but kept numbered for traceability.) | $h_t = \omega + \alpha_1 \varepsilon_{t-1}^2 + \beta_1 h_{t-1} + \delta \cdot |s_t^{\text{CPI}}|$ where $h_t$ is conditional variance of daily COP/USD returns. $\delta > 0$ = CPI surprise MAGNITUDE increases conditional variance. **MUST use $|s_t|$ not $s_t$** (Rev 3: negative surprise in levels → negative $h_t$; Han & Kristensen 2014). MLE with Gaussian likelihood; QMLE fallback (Bollerslev & Wooldridge 1992) if Jarque-Bera rejects normality of standardized residuals. Convergence: BFGS with analytic gradient; declare non-convergence if 500 iterations exceeded or Hessian non-positive-definite. | Confirmatory co-primary per Rev 4 reconciliation protocol (§1). Agrees with OLS primary → reinforced; disagrees → investigate, do not claim gate passed. |
| A8 | **Oil level control** (Rev 3 per RC + MQA + Referee) | Add $\log(P_t^{\text{oil}})$ (oil price level) as 7th regressor alongside oil return. Colombia's fiscal revenue depends on oil LEVEL ($40 vs $120), not return. Weekly return captures terms-of-trade channel; log-level captures fiscal-revenue channel (Ecopetrol). | Test whether oil-level channel confounds β after controlling for oil return. |
| A9 | **Asymmetric effects** (Rev 2 addition per Adversarial Referee) | $f(\text{RV}_t) = \alpha + \beta^+ \cdot s_t^{+} + \beta^- \cdot s_t^{-} + \text{controls} + \varepsilon$ where $s^+ = \max(s,0)$, $s^- = \min(s,0)$ | Test whether upside CPI surprises (inflation > expected) generate more vol than downside (inflation < expected). Under IT regimes, upside may be more disruptive (BanRep tightening). |

---

## 7. References

- Altavilla, C., Giannone, D., Modugno, M. (2017). "Low Frequency Effects of Macroeconomic News on Government Bond Yields." *Journal of Monetary Economics* 92.
- Andersen, T., Bollerslev, T., Diebold, F. X., Ebens, H. (2001). "The Distribution of Realized Stock Return Volatility." *JASA* 96(453).
- Andersen, T., Bollerslev, T., Diebold, F. X., Vega, C. (2003). "Micro Effects of Macro Announcements: Real-Time Price Discovery in Foreign Exchange." *AER* 93(1).
- Andersen, T., Bollerslev, T. (1998). "Answering the Skeptics: Yes, Standard Volatility Models Do Provide Accurate Forecasts." *International Economic Review* 39(4).
- Balduzzi, P., Elton, E. J., Green, T. C. (2001). "Economic News and Bond Prices." *JFQA* 36(4).
- Campbell, J. Y., Lo, A. W., MacKinlay, A. C. (1997). *The Econometrics of Financial Markets.* Princeton.
- Cao, D., Falk, B., Kogan, L., Tsoukalas, G. (2025). "A Structural Model of AMMs." SSRN 4591447.
- Fuentes, M., Pincheira, P., Julio, J. M., Rincón, H., et al. (2014). BIS Working Paper 462 / BanRep Borrador 849.
- Hansen, L. P. (1982). "Large Sample Properties of Generalized Method of Moments Estimators." *Econometrica* 50(4).
- Milionis, J., Moallemi, C. C., Roughgarden, T., Zhang, A. L. (2022). "Automated Market Making and Loss-Versus-Rebalancing." arXiv:2208.06046.
- Newey, W. K., West, K. D. (1987). "A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix." *Econometrica* 55(3).
- Reiss, P. C., Wolak, F. A. (2007). "Structural Econometric Modeling: Rationales and Examples from Industrial Organization." *Handbook of Econometrics* Vol. 6A, Ch. 64.
- Rigobon, R., Sack, B. (2003). "Measuring the Reaction of Monetary Policy to the Stock Market." *QJE* 119(2).
- Rincón-Castro, H., Rubiano-López, M., Yaya-Garzón, A., Zárate-Solano, H. M. (2021). "Traspaso de la tasa de cambio a la inflación básica en Colombia." BanRep Borradores.
- Rincón-Torres, A., Rojas-Silva, K., Julio-Román, J. M. (2021). "The Interdependence of FX and Treasury Bonds Markets: The Case of Colombia." BanRep Borrador 1171.
- Rincón-Torres, A., De la Hortúa-Pulido, E., Rojas-Silva, N., Julio-Román, J. M. (2023). "The Low Frequency Effect of Macroeconomic News on Colombian Government Bond Yields." BanRep Borradores.
- Sentana, E., Fiorentini, G. (2001). "Identification, Estimation and Testing of Conditionally Heteroskedastic Factor Models." *JE* 102(2).
