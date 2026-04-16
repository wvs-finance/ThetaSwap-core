# Structural Econometric Specification: Colombian Price-Level Surprise → COP/USD FX Realized Volatility

**Date:** 2026-04-15
**Skill:** structural-econometrics (Reiss & Wolak 2007 framework)
**Status:** Specification complete. Ready for Phase 5 (Data Pipeline + Estimation).
**Upstream:** Tier 1 literature deliverable (`contracts/notes/structural-econometrics/identification/2026-04-14-inflation-mirror-two-channel-literature.md`, verdict: `PIVOT_TO_TIER_1B`)
**Downstream:** Layer 2 Angstrom pool parameterization (deferred until β estimated)

---

## 1. Research Question

**Economic question (Phase 0a):** Does Colombian price-level surprise (CPI + PPI) explain weekly realized COP/USD FX volatility, and at what magnitude?

**Parameter of interest:** $\beta$ — semi-elasticity of weekly FX realized vol to Colombian price-level surprise. Gate: $\operatorname{adj-}R^2 \geq 0.15$ out-of-sample ($\tau_{\text{op}}$).

**Unit of observation (Phase 0b):** Week (Monday–Friday). Daily COP/USD log-returns from FRED `DEXCOUS` aggregated to weekly realized vol. N ≈ 1,100 weekly observations (~2003–2025); ~260 release weeks, ~840 non-release weeks.

**Outcome variable (Phase 0c):** $\log(\text{RV}_t)$ primary (ABDE 2001: approximately Gaussian). Raw $\text{RV}_t$ as robustness for direct $g^{\text{pool}}$ mapping.

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

**Net bias: all attenuation.** A significant $\hat{\beta}$ is a LOWER BOUND on the true effect. Conservative for the product claim that the RAN's pool observable responds to price-level shocks.

---

## 4. Estimation Strategy

### 4.1 Functional Forms (Phase 3a)

**Primary:**

$$\log(\text{RV}_t) = \alpha + \beta \cdot s_t^{\text{price}} + \gamma_1 \cdot s_t^{\text{US CPI}} + \gamma_2 \cdot s_t^{\text{BanRep}} + \gamma_3 \cdot \text{VIX}_t + \gamma_4 \cdot I_t + \varepsilon_t$$

Log-transform justified by ABDE (2001): log(RV) approximately Gaussian.

**Robustness:** Level-RV (R1), release-day exclusion (R2).

### 4.2 Distributional Assumptions (Phase 3b)

**Primary:** $\varepsilon_t \sim N(0, \sigma^2)$ with Newey-West HAC standard errors (lag = 4 weeks). OLS estimation.

**Sensitivity:** Student-t MLE (R3) if Jarque-Bera rejects normality of residuals.

Citation: Andersen et al. 2003 (HAC SEs); Newey & West 1987; ABDE 2001 (log-RV normality).

### 4.3 Implied Econometric Equation (Phase 3c)

$$\log(\text{RV}_t) = \alpha + \beta \cdot s_t^{\text{price}} + \gamma_1 \cdot s_t^{\text{US CPI}} + \gamma_2 \cdot s_t^{\text{BanRep}} + \gamma_3 \cdot \text{VIX}_t + \gamma_4 \cdot I_t + \varepsilon_t$$

| Variable | Source | Free-tier? |
|---|---|---|
| $\text{RV}_t = \sum_{d \in \text{week}} r_d^2$ | FRED `DEXCOUS` | ✓ |
| $s_t^{\text{price}}$ (CPI+PPI composite) | DANE IPC + BanRep consensus + DANE IPP | ✓ |
| $s_t^{\text{US CPI}}$ | FRED (AR(1) surprise proxy) | ✓ |
| $s_t^{\text{BanRep}}$ | BanRep rate decisions + IBR-implied consensus | ✓ |
| $\text{VIX}_t$ | FRED `VIXCLS` | ✓ |
| $I_t$ (intervention dummy) | BanRep SUAMECA portal | ✓ |

All inputs free-tier. No Bloomberg required.

### 4.4 Identification

**Source of variation:** Pre-scheduled DANE CPI+PPI release timing.

**Exclusion restriction:** $\mathbb{E}[s_t^{\text{price}} \cdot \varepsilon_t] = 0$ conditional on controls. Backed by:
- Timing exogeneity: DANE pre-schedules (Andersen et al. 2003 §II)
- Surprise orthogonality: consensus is rational (Balduzzi, Elton, Green 2001; testable via T1)
- Heteroskedasticity backup: variance-shift identification (Rigobon & Sack 2003; Sentana & Fiorentini 2001)
- Multi-announcement conditioning: US CPI + BanRep rate + VIX + intervention absorb non-Colombian-price channels (ABDV 2003 eq. 2)
- Colombian implementation: be_1171 §2.4 + §3.1; rinconHortuaSilvaRoman 2023

**Threat investigated and mitigated:** DANE releases CPI and PPI on the same day (DANE calendar 2026). CPI+PPI treated as composite hedge target (not confound). Same-week SIPSA (food) and exports are subcomponents or lower-magnitude. Employment and GDP fall in different weeks by calendar design.

---

## 5. Specification Tests

| # | Implication | Tests | Statement | Method | Reject → |
|---|---|---|---|---|---|
| T1 | Surprise unpredictable | Consensus rationality | $\mathbb{E}[s_t \mid s_{t-1}, \text{RV}_{t-1}, \text{VIX}_{t-1}] = 0$ | F-test on lagged predictors | Consensus biased → β biased |
| T2 | Release weeks higher vol | Announcement channel exists | $\text{Var}(\text{RV} \mid \text{release}) > \text{Var}(\text{RV} \mid \text{non-release})$ | Levene test | No channel → β uninformative |
| T3 | β > 0 | Sign restriction | $\beta > 0$ | One-sided t-test | Hedge doesn't work |
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
| A6 | Bivariate (no controls) | $\log(\text{RV}_t) = \alpha + \beta \cdot s_t^{\text{price}} + \varepsilon$ | Benchmark: do controls matter? |

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
