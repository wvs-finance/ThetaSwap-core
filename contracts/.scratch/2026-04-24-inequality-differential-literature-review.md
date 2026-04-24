# Literature-Landscape Review — Inequality-Differential Construct for Abrigo

**Task:** Rev-5 Task 11.L
**Date:** 2026-04-24
**Plan:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` @ `8db00fe74`
**Protocol:** arxiv MCP primary; WebSearch/WebFetch fallback when <5 relevant hits; ≤15-word quotes; URL + citation per claim.

---

## 1. Executive Summary

The inequality-differential construct Abrigo proposes — a traded instrument on `Y_inequality = Y_asset_leg − Y_consumption_leg` — sits at the intersection of four well-developed literatures and one sparse-to-absent one. **Piketty's r−g framework** (Axis 1), **Lustig-Roussanov-Verdelhan currency carry factors** (Axis 2), **parametric / GDP-linked instruments** (Axis 3), and **consumption-income inequality measurement** (Krueger-Perri; Meyer-Sullivan) all supply the construct with rigorous precedent on individual sides of the differential equation. **DeFi / on-chain instruments that explicitly hedge an inequality differential** (Axis 4) appear **effectively novel** — `LIT_SPARSE_onchain_inequality` fires. **Colombia-specific carry-consumption spread work** (Axis 5) exists primarily in BanRep Borradores grey literature, not arxiv — `LIT_SPARSE_Colombia_arxiv` fires.

**Top-3 functional-equation candidates:**
1. **Carry-factor regression** (Lustig-Roussanov-Verdelhan 2011): `R_carry = α + β·HML_FX + ε`, extended to Y_inequality = f(carry-return, consumption-growth).
2. **Capital-share → top-income transmission** (Akgün-Özsöğüt 2025): structural panel `ΔTopShare_it = β_i·ΔCapitalShare_it + controls`, with emerging-economy time-varying β.
3. **Habit-consumption SDF** (Campbell-Cochrane 1999): asset return spread = −Cov(SDF, R)/E[SDF], where SDF depends on surplus-consumption ratio — the economic foundation for why the differential should be priced.

**Verdict:** The construct is **novel in combination but derivative in parts.** Each individual leg has 20+ years of literature. No prior paper assembles them as a tradable on-chain differential instrument with COPM-like stablecoin X.

---

## 2. Literature Landscape (per-axis)

**Axis 1 — Inequality differentials / r−g.** Dense. r−g has formal emergent-property derivations (Quevedo-Quimbay 2019, `1903.00952`), structural capital-share → top-income estimators (Akgün-Özsöğüt 2025, `2501.02371`), Fokker-Planck wealth reformulations (Fröseth 2026, `2603.16006`). Cognitive-aging and superstar-firm micro-foundations (Kausik 2023, `2308.14982`; Liuh 2025, `2512.03812`). Autor-Kausik 2026 (`2601.06343`) surfaces the non-monotonic wage-labor-share relationship underpinning the hedge-the-differential (not the wage-level) argument.

**Axis 2 — Carry-consumption spread.** Dense. Lustig-Roussanov-Verdelhan 2011 (NBER w14082) canonical carry-factor; Ames-Peters-Bagnarosa tail-dependence (`1406.4322`, `1303.4314`) EM-currency extensions. Campbell-Cochrane habit has continuous-time MFG recasts (Bo-Wang-Yu 2022, `2206.13341`); Olkhov 2022 (`2204.07506`) multi-period consumption-based pricing. Lempérière et al. 2014 (`1409.7720`) skew-return identification intuition.

**Axis 3 — Parametric / GDP-linked / state-contingent.** Moderate. Pang-Choi 2022 (`2209.05307`) data-driven parametric insurance (Bayesian NN); Consiglio-Tumminello-Zenios 2018 (`1804.01475`) S-CoCo pricing; Firouzi 2025 (`2508.00019`) tokenized sovereign debt — closest on-chain analog but settles on debt not inequality.

**Axis 4 — On-chain / DeFi precedents.** `LIT_SPARSE_onchain_inequality`. Jones-Matsui-Knottenbelt 2026 (`2603.23480`) stablecoin-as-indicator; Hossen 2023 (`2303.04101`) pass-through; Mohanty-Krishnamachari 2026 (`2601.18991`) stablecoin MFG; Klages-Mundt-Schuldenzucker 2022 (`2212.12398`) stablecoin AMM monetary policy. **No paper uses on-chain flow as X for inequality-differential Y.**

**Axis 5 — Colombia-specific.** `LIT_SPARSE_Colombia_arxiv`. Near-zero arxiv hits; BanRep Borradores off-arxiv. Martins-Lopes 2024 (`2411.16244`) cross-country macro-event FX-vol; Gasparini-Reyes 2022 (`2202.04591`) Latam inequality-perception.

---

## 3. Top-10 Paper Deep Reads

### 3.1 Lustig-Roussanov-Verdelhan (2011) — "Common Risk Factors in Currency Markets" (RFS 24(11))
- **Finding:** Two-factor model (country-specific + global slope `HML_FX`) explains cross-sectional carry returns; slope loads on global equity volatility.
- **Identification:** Cross-sectional portfolio sort on interest-rate differential.
- **Sign for Abrigo:** `HML_FX` on Y_asset_leg: **positive** during global-stress (when differential widens).
- **Relevance:** Canonical Y_asset_leg functional form; risk-premium compensation intuition.

### 3.2 Akgün-Özsöğüt (2025) — "Effect of Capital Share on Income Inequality" (arxiv:2501.02371)
- **Finding:** 1pp capital-share rise → 0.17pp top-5% share rise; emerging-economy transmission coefficient **time-varying and increasing**.
- **Identification:** Structural panel with country-specific time-varying β; WID + National Accounts.
- **Sign for Abrigo:** Colombian β positive and rising — supports widening thesis.
- **Relevance:** Justifies single-β structural capture of differential-widening; supports pre-committed positive sign.

### 3.3 Campbell-Cochrane (1999) — "By Force of Habit" (JPE 107; recast Bo-Wang-Yu 2022, arxiv:2206.13341)
- **Finding:** External habit → time-varying risk aversion; consumption depends on surplus-consumption ratio S_t.
- **Identification:** Structural calibration to equity-premium and consumption-volatility moments.
- **Sign for Abrigo:** Widening → S_t shock → higher SDF-weighted hedge demand → positive instrument price.
- **Relevance:** Economic foundation for why the differential earns a premium; vault pricing primitive.

### 3.4 Autor-Kausik (2026) — "Resolving the automation paradox" (arxiv:2601.06343)
- **Finding:** Declining labor share **raises** wages above wage-maximizing threshold; 16% of US 1954–2019 real wage growth.
- **Identification:** Competitive-economy constant-returns + 12-country panel.
- **Sign for Abrigo:** Complicates "labor share down → working class suffers"; must control capital-labor ratio.
- **Relevance:** **Red flag** — consumption-leg specification must account for wage-gain coexistence.

### 3.5 Meyer-Sullivan (2023) — "Consumption and Income Inequality" (JPE 131(2))
- **Finding:** Consumption inequality rose **less** than income inequality; sensitive to measurement.
- **Identification:** CEX + NIPA reconciliation; well-measured-subset weighting.
- **Sign for Abrigo:** Y_consumption_leg magnitude smaller than income-gap; differential noisier.
- **Relevance:** DANE EMMV/ECV must mirror "well-measured components" discipline.

### 3.6 Krueger-Perri (2006) — "Does Income Inequality Lead to Consumption Inequality?" (RES 73(1))
- **Finding:** Income inequality rose; consumption inequality barely moved. Within-group channel dominates.
- **Identification:** US CEX 1980–2003; permanent-vs-transitory decomposition.
- **Sign for Abrigo:** Differential dominated by asset-return leg, not consumption-leg.
- **Relevance:** Supports asset-leg as primary predictor, consumption-leg as secondary control.

### 3.7 Quevedo-Quimbay (2019) — "Piketty's second law as emergent property" (arxiv:1903.00952)
- **Finding:** r/g emerges from kinetic wealth-exchange model with saving + Solow growth + labor income.
- **Identification:** Agent-based + mean-field analytical derivation.
- **Sign for Abrigo:** Microfoundation for `Y_asset_leg − Y_consumption_leg` as structural, not ad hoc.
- **Relevance:** Theoretical grounding; simulator calibration reference.

### 3.8 Firouzi (2025) — "Tokenized Sovereign Debt Conversion Mechanism" (arxiv:2508.00019)
- **Finding:** Performance-linked tokens convert debt at debt/GDP + growth thresholds; 20–25% debt reduction in IMF-calibrated sims.
- **Identification:** Two-state regime-switching jump-diffusion + Monte Carlo.
- **Sign for Abrigo:** Closest on-chain architectural precedent; settles on realized macro series.
- **Relevance:** Template for Abrigo vault mechanics (future scope; informs design).

### 3.9 Jones-Matsui-Knottenbelt (2026) — "Stablecoins as Dry Powder" (arxiv:2603.23480)
- **Finding:** Stablecoin volume + upside-volatility **Granger-cause** crypto-market volatility; copula-based.
- **Identification:** Copula causality; OOS MSE reduction.
- **Sign for Abrigo:** Stablecoin flow is legitimate economic indicator; supports COPM-as-X plausibility.
- **Relevance:** Axis-4 precedent; our claim is narrower (country-specific macro).

### 3.10 Martins-Lopes (2024) — "What events matter for exchange rate volatility?" (arxiv:2411.16244)
- **Finding:** Sparse macro-announcement events drive FX vol; intraday seasonality tied to market-opening.
- **Identification:** Stochastic-volatility + LASSO event selection.
- **Sign for Abrigo:** BanRep-policy + Fed-funds pre-register as controls on Y₁ TRM RV.
- **Relevance:** Methodological template for event-augmented vol regression.

---

## 4. Functional-Equation Candidates

### Candidate A — Carry-Factor Regression (Lustig-Roussanov-Verdelhan 2011)
- **Canonical form:** `R_carry_{t+1} = α + β·DOL_t + γ·HML_FX_t + ε_{t+1}`, where `R_carry = (r_COP − r_US)/52 + ΔTRM/TRM`.
- **Data assumed:** BanRep policy rate, Fed funds, weekly TRM.
- **Estimation method:** OLS with Newey-West HAC; could be extended to the X_d augmentation.
- **Expected sign of COPM X_d coefficient:** ambiguous ex-ante; pre-commit as two-sided test given our FX-vol-CPI-FAIL precedent.
- **Abrigo rôle:** **Primary Y_asset_leg specification.** Most canonical form; maximum external validity.

### Candidate B — Capital-Share Transmission (Akgün-Özsöğüt 2025)
- **Canonical form:** `ΔTopShare_it = α_i + β_it·ΔCapitalShare_it + δ·Controls_it + ε_it`.
- **Data assumed:** DANE national accounts (capital/labor split) + World Inequality Database top-shares.
- **Estimation method:** Structural panel with time-varying β.
- **Expected sign:** β > 0 for Colombia (emerging economy); rising over time per paper.
- **Abrigo rôle:** **Secondary structural Y_inequality regression;** identification-assumption source (time-varying transmission).

### Candidate C — Habit-Consumption SDF Pricing (Campbell-Cochrane 1999)
- **Canonical form:** `E[R_asset_leg − R_consumption_leg] = −Cov(SDF_t, R_asset_leg − R_consumption_leg) / E[SDF_t]`, with SDF driven by surplus-consumption ratio `S_t`.
- **Data assumed:** Consumption-growth series (ECV / EMMV).
- **Estimation method:** GMM on Euler equation; alternative is calibration.
- **Expected sign:** Inequality widening → S_t shock → SDF rises for working class → positive hedge premium.
- **Abrigo rôle:** **Theoretical microfoundation and pricing primitive** for the future Abrigo vault.

### Candidate D — Two-Leg Difference Regression (custom, motivated by Lustig-Roussanov-Verdelhan + Meyer-Sullivan)
- **Canonical form:** `Y_inequality_t = R_asset_leg_t − R_consumption_leg_t`; test `E[Y_inequality_{t+1} | X_d_t] ≠ 0`.
- **Data assumed:** Both legs at weekly frequency.
- **Estimation method:** OLS with HAC; predictive regression.
- **Expected sign of X_d coefficient:** **positive** if COPM B2B→B2C flow captures rich-household dollarization (asset-leg proxy); pre-commit one-sided at 5% FWE adjusted.
- **Abrigo rôle:** **Gate-test target (primary).**

---

## 5. Identification Strategies from Prior Work

**Instruments:**
- Global equity volatility index (VIX) — Lustig-Roussanov-Verdelhan 2011 for carry-slope factor.
- Macro-announcement events (BanRep, Fed, DANE releases) — Martins-Lopes 2024 for FX vol.
- Capital-share from national accounts — Akgün-Özsöğüt 2025 for inequality transmission.

**Natural experiments:**
- BanRep policy-rate regime switches (2016 inflation-targeting recalibration; 2021–2022 hiking cycle).
- COVID-19 consumption shock (2020Q2) — Tello-Carvache et al. 2025 (`2501.12358`) dollarization-protection evidence.
- COPM migration event (2025-12-05 MGP-12 per retired remittance-exit memo) — creates on-chain structural break.

**Identification assumptions:**
- *Inheritable:* Cross-sectional exogeneity of global slope factor (Lustig-Roussanov-Verdelhan). Well-measured-consumption subset stability (Meyer-Sullivan).
- *Must re-justify:* Whether COPM B2B→B2C flow is **exogenous** to Y_asset_leg; whether Colombian time-varying β is stable in our 2008–2026 window; whether the CPI-FAIL predictive-regression lesson applies (β̂ as predictive-regression coefficient, not causal).

---

## 6. Novelty Claim

**Novel:**
- **On-chain inequality-differential instrument** — no prior paper combines (stablecoin-flow X) × (carry-consumption differential Y) × (progressive-hedge product framing). Firouzi 2025 is closest architecturally but settles on sovereign debt, not inequality.
- **Progressive-hedge design principle** — explicit welfare-redistribution goal is absent in the carry/habit/S-CoCo literatures, which frame instruments as neutral risk-sharing.
- **COPM-specific X construction** — narrowly novel; no prior paper uses Minteo / regulated-peso-stablecoin flow as a macro-indicator.

**Extension / replication:**
- Extends Lustig-Roussanov-Verdelhan carry-factor to a **single emerging-market currency** with on-chain instrument overlay.
- Replicates Akgün-Özsöğüt emerging-economy rising-transmission finding in the Colombia sub-sample.
- Extends Jones-Matsui-Knottenbelt stablecoin-as-indicator to a **country-specific, macro-Y** application.

**Honest precedent acknowledgement:**
- Piketty's r > g framework anticipates our thesis. We do not claim theoretical novelty of the differential itself — we claim **instrument-design novelty** for settling on that differential on-chain.
- Tello-Carvache et al. 2025 documents that Latam dollarization fails to protect against economic performance (only inflation); our product-framing must not overclaim welfare protection beyond the inflation channel.
- Autor-Kausik 2026 provides a **red-flag counter-result**: declining labor share can raise wages — we must control for the capital-labor ratio to avoid this mechanical mis-specification.

---

## 7. Recommendations for Task 11.O Structural-Econometrics Invocation

**Functional-equation candidates to bring into the 13-input resolution matrix:**
1. **Candidate A (Carry-Factor Regression)** — primary Y_asset_leg spec.
2. **Candidate D (Two-Leg Difference Regression)** — gate-test target.
3. **Candidate C (Habit SDF)** — theoretical microfoundation (not directly estimated in the current exercise, but pre-registered as the welfare-interpretation frame).

**Feasible identification strategies given current data:**
- VIX-as-instrument feasible (freely available, weekly).
- BanRep / Fed event-dummies feasible (both agencies publish schedules).
- Capital-share panel regression deferred — requires DANE national-accounts acquisition track (Tier-2 per memory `project_abrigo_inequality_hedge_thesis.md`).

**Pre-committable expected signs on X_d coefficient:**
- Against Y_asset_leg (carry return): **positive** — COPM flow captures dollarization velocity which co-moves with carry-trade profitability.
- Against Y_consumption_leg: **negative** (if COPM captures rich-household rotation) or **positive** (if COPM captures retail-consumption velocity) — **pre-commit two-sided** given this ambiguity.
- Against Y_inequality differential: **positive** if dominant channel is rich-household dollarization, **negative** if dominant channel is retail velocity. **Pre-commit two-sided at 5% FWE-adjusted.**

**Red-flag findings to carry into the spec:**
- Autor-Kausik 2026 non-monotonic wage-labor-share relationship must be controlled (Variable: capital-labor ratio proxy).
- Meyer-Sullivan 2023 measurement sensitivity — consumption-leg must use only well-measured categories.
- CPI-FAIL predictive-regression β-interpretation discipline carries over: β̂ is a predictive-regression coefficient, **not a causal coefficient** without additional exogeneity evidence. Pre-register this caveat.

**Anti-fishing discipline carry-over:**
- With 2 legs × 3 candidate X-formulations × FWER-naive testing, unadjusted family-wise error ≈ 30% at single-test 5% level. Apply Bonferroni-Holm or Benjamini-Hochberg pre-registered per candidate bundle.

---

## Citations + Sparse-Axis Flags

Full URL-verified citation list and evidence-file details offloaded to companion document:
`contracts/.scratch/2026-04-24-inequality-differential-literature-review-evidence.md`

**Sparse-axis flags (summary):**
- `LIT_SPARSE_onchain_inequality` — no direct precedent for stablecoin-flow-as-X-on-inequality-Y instrument. Opportunity for Abrigo priority claim.
- `LIT_SPARSE_Colombia_arxiv` — BanRep Borradores de Economía grey literature not surfaced via arxiv; Task 11.O should explicitly queue a `https://www.banrep.gov.co/es/publicaciones-investigaciones/borradores-economia` fetch pass.
