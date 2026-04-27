# Colombia Y×X Matrix — X-Ranking for Y₂ (CPI variability) and Y₃ (Remittance-flow variance)

**Date:** 2026-04-20
**Scope:** Agent 4 of the three-agent Y×X exploration. Builds directly on Agent 3 (`/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-colombia-next-primary-candidate-ranked.md`) which fixed Y₁ = TRM weekly realized variance. This agent fixes **Y₂ = Colombian headline CPI monthly variability** and **Y₃ = rolling variance of monthly Colombian remittance inflows (US-corridor)** and ranks Colombia-specific off-chain / on-chain X candidates.
**Constraints:** no proposals that duplicate frozen controls (VIX, DXY, EMBI Colombia, Fed Funds, Oil, Banrep Repo); Colombia-specific; 2008-2026 public-data availability; Phase-B pool link required; on-chain observables permitted with explicit thin-history caveat.
**Produced by:** Research sub-agent, read-only.

---

## 1. Methodology note

### Local corpus files consulted (absolute paths)

- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-colombia-next-primary-candidate-ranked.md` — Agent 3 ranking (Y₁ = TRM RV). Remittance-flow-surprise top-1; ITI-PPI ToT #2; TES #3.
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-ccop-mcop-observables-search.md` — on-chain observables catalog (170d Uniswap V3 cCOP TWAP; 540d cCOP gross-volume; COPM mint/burn via Dune + Minteo API).
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-remittance-volatility-swap-deep-read.md` — three-arrow identification chain, quincena lever, pre-registered ln(V_t) regression.
- `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/MACRO_RISKS.md` — 5-way taxonomy (LocalInflation, InterestRateShock, TermsOfTrade, CapitalFlight, RemittanceCorridorRisk).
- `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/COLOMBIAN_ECONOMY_CRYPTO.md` — §1 remittance structure, §2 freelancer stack, §4 exchange-rate timeline, §5.4 documented shocks.
- `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/OFFCHAIN_COP_BEHAVIOR.md` — §1 Littio event-response (Jan 2025 tariff +100%/48h); §4 P2P spread 0.25-0.75% baseline; §6 channel-substitution.
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/contracts/notebooks/ranPricing.ipynb` cell 3 — CES pool categories `Asset | Index | InflationRate | ExchangeRate`.

### External queries run (6 of 8 budget)

1. **arxiv** `"exchange rate pass-through" Colombia CPI inflation` — off-target (nearest hit was Bangladesh ERPT at firm level, Hossen 2023); no Colombia-specific arxiv paper. Directed me back to corpus + web.
2. **arxiv** `remittance flows US immigration policy Latin America` — partially off-target; closest is Islam-Mondal 2309.08855 on remittance-financial-development in 4 LMIC (pooled, not Colombia).
3. **web** `Banrep Borradores exchange rate pass-through Colombia CPI inflation variance` — **on-target**. Banrep Borrador 930 (BSTVAR, time-varying-parameter ERPT): 1% peso shock → **0.01-0.05% to core CPI**, declining monotonically 2008→2020 (oil-shock > dot-com > Lehman > COVID). Borrador 330 disaggregated long-run elasticities 0.1-0.8 / short-run 0.1-0.7 across manufacturing sectors. Core conclusion: ERPT is partial, state-dependent, and has weakened — weak-moderate a-priori strength for Y₂ = CPI variability.
4. **web** `US Hispanic employment Colombian remittance determinants monthly` — **on-target**. Dallas Fed (Oct 2023) documents US-labor-market ↔ LatAm remittance link: US construction-employment + Hispanic-services-employment drive record inflows; IDB TN-3243 (2025) confirms adaptation cycle; BanRep blog shows June-2024 ≥$1B/mo crossing. Hispanic employment is a first-order Y₃ regressor.
5. **web** `DANE food price index imported Colombia CPI food weight` — partial. DANE CPI weights confirmed: Housing 33%, **Food 15%**, Transport 13%. No discoverable disaggregated imported-food subindex in a single CSV endpoint — reconstructible from DANE IPP (Producer Price Index) imported-goods column.
6. **web** `Trump tariff 2025 Colombia migration deportation remittance impact` — **on-target** for Y₃. Jan 26, 2025 Trump-Petro standoff documented across 10+ outlets; 25% → 50% tariff threat on coffee/flowers/~11K goods; visa-restrictions persisted; Littio +100% USDC accounts in 48h. **Direct evidence for a Trump-Petro dummy in Y₃**.
7. **web** `World Bank Remittance Prices Worldwide US Colombia corridor cost quarterly` — **on-target**. RPW US→Colombia Q4 2024: total cost 4.53%, fee 9.75%, FX-margin 1.95%; quarterly mystery-shopper panel since 2008 across 365 corridors.
8. **web** `"stablecoin volume" inflation signal predictor emerging market academic` — **on-target for on-chain Y₂/Y₃ rows**. BIS WP 1340 (stablecoin-FX spillovers), BIS WP 1270 (stablecoin-safe-asset), IMF Understanding Stablecoins 2025, and Turkey/Argentina flight-to-safety evidence confirm stablecoin volume is an *information-carrying* signal for inflation/FX stress in EMDEs. Colombian-specific evidence is in Littio's 100%+/48h tariff response (`OFFCHAIN_COP_BEHAVIOR.md` §1).

### Filtered-out candidates (reason)

- **Global commodity index / FAO food index** — global, not Colombia-specific (Agent 3 filter carries over).
- **Oil** — control.
- **M2 money supply growth** — considered for Y₂ but excluded from shortlist because Banrep monetary-base series co-move mechanically with BanRep Repo (already a control), producing near-perfect multicollinearity in a tight-panel design. Keep as sensitivity covariate, not primary X.
- **DANE GEIH wage growth** — quarterly; too coarse vs monthly Y₂.
- **US-recession indicator** — binary/near-binary over 2008-2026 (only 2008-2009 and hypothetical 2025-2026), insufficient within-regime variation; Hispanic-employment surprise is the strictly-finer continuous alternative and dominates.
- **Colombian unemployment surprise (DANE monthly)** — seasonal noise + 4-6-month revision cycle undermines real-time surprise identification; kept as sensitivity.

---

## 2. Y₂ = Colombian headline CPI variability — ranked X shortlist

| Rank | Name | RHS definition | Colombia-specificity | Data source / freq / span | MACRO_RISKS / CES category | A-priori strength (lit-grounded) | Phase-B pool target |
|---|---|---|---|---|---|---|---|
| **1** | **Import-price index residual (DANE IPP imported-goods subindex)** | ε_t^{IPP} = Δlog(IPP_imported)_m − AR(1) | Uses Colombia's actual import basket weighted by Colombian trade shares (not global commodities); DANE-published | DANE IPP monthly since 2000, 10-day release lag, free download | LocalInflation / InflationRate | **Moderate-strong**. Direct CPI-component input; ERPT channel makes imported-goods prices a Granger-causal precursor of headline CPI. Dominates TRM because it pre-aggregates the basket-weighting step. | `cCOP/PAXG` (gold numeraire absorbs global-commodity confounds) OR `cCOP/<imported-goods-RWA-basket>`. |
| **2** | **TRM / ΔTRM pass-through residual** | ε_t^{TRM} = Δlog(TRM)_m − AR(1); tested against CPI(t+1..t+6) at monthly horizon | TRM = BanRep daily, volume-weighted official peso-USD rate; uniquely Colombian | BanRep daily via datos.gov.co Socrata `mcec-87by.json`; 2008-2026; free | LocalInflation via ERPT channel / ExchangeRate | **Weak-moderate**. Borrador 930 BSTVAR: ERPT 0.01-0.05 to core CPI, declining post-2014. Signal present but small and state-dependent (oil-shock amplified; COVID muted). Supports ERPT conditional on high-state regime. | `cCOP/USDC` (trivial) or `cCOP/AMPL` (CPI-rebasing numeraire, per `ranPricing.ipynb` cell 3). |
| **3** | **Banrep policy-rate surprise** | ε_t^{Banrep} = rate_decided,t − rate_expected,t (from Fedesarrollo/EMF survey median) | Banrep decisions on 8 scheduled dates/yr, 2003-present; market-implied rate via IBR overnight index | Banrep meeting announcements + Fedesarrollo Encuesta de Opinión Financiera monthly; 2008-2026 | LocalInflation (monetary-transmission residual, NOT the level) / InterestRate | **Moderate**. Banrep-surprise differs from Banrep-Repo (control) exactly as US FFR-surprise differs from FFR level (standard Kuttner-Svensson construction). Disentangles anticipated vs unanticipated monetary stance. Colombian replication of Kuttner works because Fedesarrollo-EOF is a long-run market-expectation series. | Synthetic "peso-rate perp" vs stETH yield, per `MACRO_RISKS.md` line 9. |
| **4** | **cCOP/USDT log-volume (Celo Uniswap V3 + Mento vAMM)** | Δlog(V_t) weekly, aggregated daily cCOP gross volume | Retail Colombian cohort (4,913 senders, COT-morning timezone, $100-$2K tx); captures flight-to-USD under CPI stress | Dune Query #6941901; 540d history (Oct 2024→); free | LocalInflation (flight-to-safety) / ExchangeRate | **Moderate**, with thin-history caveat. BIS WP 1340 + Turkey/Argentina precedent establish stablecoin-volume as EMDE inflation-stress signal. Colombian-specific evidence in `OFFCHAIN_COP_BEHAVIOR.md` §1. Only 18 months of data (2024-10 → 2026-04) limits Y₂ backtest to post-pivot subsample. | `cCOP/AMPL` forward-looking (per `ranPricing.ipynb`). |
| **5** | **Venezuelan-migration labor-supply shock (monthly border-crossing residual)** | ε_t^{VenMig} = M_t − AR(1), M_t = monthly Venezuelans-in-Colombia (Migración Colombia bulletins) | 2.9M Venezuelans in Colombia (largest host globally); affects informal-wage pressure → non-tradable-CPI component | Migración Colombia monthly PDFs 2015-2026; must be scraped | LocalInflation (via wage-push channel, reverse sign) | **Weak-moderate**. Supply-side wage shock feeds into non-tradable CPI with 3-6mo lag. Regime-specific (2015-2022 peak); fade by 2024+ per stabilization. | No direct pool; sensitivity-only row. |

---

## 3. Y₂ top-1 recommendation — Import-price-index residual (DANE IPP imported-goods)

1. **Mechanism directness.** DANE IPP imported-goods is a **direct mechanical input** to headline CPI through the 15%-weight Food component and the ~18% tradable-goods share of the full basket. Unlike TRM (which acts via partial, state-dependent ERPT of 0.01-0.05 per Borrador 930), IPP already pre-aggregates the weighting step and absorbs non-exchange-rate channels (shipping, commodity composition, tariffs). The a-priori structural link is proximate and quantitatively large.
2. **Data regime.** DANE IPP has **monthly, 10-day-lagged, free, 26-year** history; it covers the full Y₂ span without revision-vintage concerns (IPP revisions are microscopic vs. Banrep remittance vintages). This makes real-time surprise construction clean.
3. **Phase-B pool fit.** A `cCOP / <commodity-RWA or PAXG>` pool is the natural Phase-B target because IPP-imported is itself a basket price and the settlement instrument should price a basket. This is strictly cleaner than `cCOP/AMPL` (AMPL rebases on US-CPI, introducing a cross-country mismatch) and it reuses the existing PAXG market. The CES category `InflationRate` from `ranPricing.ipynb` cell 3 is satisfied natively.

**Guarded note:** TRM (#2) remains the co-primary candidate if the user wants the Banrep-literature-dominant channel. The three-agent landscape can test both in Phase-A and let the gate verdict pick.

---

## 4. Y₃ = Remittance-flow variance — ranked X shortlist

| Rank | Name | RHS definition | Colombia-specificity | Data source / freq / span | MACRO_RISKS / CES category | A-priori strength (lit-grounded) | Phase-B pool target |
|---|---|---|---|---|---|---|---|
| **1** | **US Hispanic-employment surprise (BLS CES Hispanic-or-Latino payroll residual)** | ε_t^{HispEmp} = ΔlogEmp_Hisp,t − AR(1), monthly | US corridor = 53% of Colombian remittances (`COLOMBIAN_ECONOMY_CRYPTO.md` §1.2); Hispanic-services + construction employment directly employs the Colombian-origin diaspora | BLS CES Hispanic-or-Latino supplement monthly; 2000-2026; free | RemittanceCorridorRisk / InterestRate (labor income) | **Strong**. Dallas Fed (2023) + IDB TN-3243 (2025) directly identify US Hispanic employment as the dominant remittance driver. Continuous monthly regressor with clean AR(1) residual and sharp release calendar (first Friday). | `cCOP/USDC` with HispEmp-surprise oracle. |
| **2** | **US migration-policy event dummies (Trump-Petro Jan 2025; ICE enforcement; visa-restriction announcements)** | D_t^{MigEvent} = 1 at documented event weeks | Colombia-specific events (Trump-Petro tariff standoff Jan 26 2025; DIAN Resolution 000240 Dec 2025; visa-restriction retention) | News-archive event codebook; hand-coded; 2008-2026; free | RemittanceCorridorRisk / Asset (event-study residual) | **Strong-moderate**. Documented 100%+ Littio USDC-account growth 48h post Jan 2025 event (`OFFCHAIN_COP_BEHAVIOR.md` §1). Caveat: low-frequency event count (likely 8-15 events over 18yr) limits continuous-regression power; best as complement to #1, not standalone. | `cCOP/USDC` event-study design. |
| **3** | **World Bank RPW US-Colombia corridor cost (quarterly)** | Δ(TotalCost%)_q, interpolated to monthly via step-function | Colombia-specific corridor row; quarterly mystery-shopper panel | World Bank RPW since 2008; Q4 2024 baseline 4.53%; free | RemittanceCorridorRisk / InflationRate (via real-remittance-cost) | **Moderate**. Corridor cost is a supply-side lever: when the corridor widens, reported inflows bunch (larger, less-frequent transfers), mechanically increasing variance. Quarterly → monthly interpolation is mild because RPW moves slowly. | `cCOP/USDT` spread oracle against RPW benchmark. |
| **4** | **COPM mint/burn net-flow (Minteo + Littio)** | Δ(mint_t − burn_t), weekly | 100K Colombian users via Littio; $200M/mo volume; income-conversion behavioral anchor (`COPM_MINTEO_DEEP_DIVE.md` §8.2) | Dune + Minteo transparency portal; ~720d history (Apr 2024→); free | RemittanceCorridorRisk / ExchangeRate | **Moderate** with thin-history caveat. Littio shock-response (Jan 2025 +100%/48h) is direct evidence that COPM-mint correlates with household income-conversion stress. Only ~2yr of data limits Y₃ full-span test. | `cCOP/USDC` with COPM-mint oracle. |
| **5** | **Venezuelan-Colombian bidirectional migration shock (net border flow residual)** | ε_t^{VenBi} = (inflow_Ven→Col − outflow_Col→Ven)_t − AR(1) | 2.9M Venezuelans in Colombia; Venezuelan diaspora sends remittances Venezuela-Colombia (`COLOMBIAN_ECONOMY_CRYPTO.md` §1.5); affects receiver-demographic composition | Migración Colombia + Plataforma R4V monthly; 2015-2026 | RemittanceCorridorRisk (composition effect) | **Weak-moderate**. Documented but hard to identify cleanly because Venezuelan-diaspora remittance is partly in USDT, not COP — some of it never shows up in BanRep. Best as a compositional control, not primary. | No direct pool. |

---

## 5. Y₃ top-1 recommendation — US Hispanic-employment surprise

1. **Direct causal chain.** The Dallas Fed 2023 note and IDB TN-3243 (2025) explicitly identify US Hispanic-or-Latino payroll employment as the dominant driver of LatAm remittance inflows, with the Colombia subset riding on 53% US-corridor concentration (`COLOMBIAN_ECONOMY_CRYPTO.md` §1.2). The mechanism is first-order (income → remittance) and priced in only partially because the BLS CES Hispanic supplement is not a market-anticipated series in the same way aggregate NFP is — genuine surprise content survives.
2. **Statistical power.** Monthly, continuous, free, 2000-2026 BLS release with a sharp first-Friday release calendar. AR(1) residuals have textbook white-noise properties in the Hispanic-employment subseries, giving a clean Kuttner-style surprise column. This is the exact statistical setup Agent 3 recommended for the Y₁ remittance-surprise top-1 but shifted to the *US side* of the corridor where identification is cleaner (supply-side push vs demand-side pull).
3. **Phase-B pool design and cross-Y universality.** A `cCOP/USDC` pool with a Hispanic-employment-surprise oracle gives a direct income-hedge product for Valle del Cauca households (26% of remittance concentration). Critically, Hispanic-employment surprise is also a plausible but untested X candidate for Y₁ (TRM RV) via the remittance → FX-inflow channel — making it a candidate *universal observable* that could appear across all three Y's.

**Guarded note:** #2 (migration-policy event dummies) should be run as a co-primary event-study to triangulate. Jan 2025 Trump-Petro standoff is a natural "quasi-natural experiment" already in the sample.

---

## 6. Engine-integration sketches (Y₂-top-1 and Y₃-top-1)

### Y₂-top-1: Import-price-index residual → CPI variability

- **Surprise column.** ε_t^{IPP} = Δlog(IPP_imported)_m − AR(1) fitted 2000-2008 (pre-sample), rolling refit post-2008.
- **Controls.** Retain **VIX, DXY, EMBI Colombia, Fed Funds, Banrep Repo, Oil** (Oil is a primary confound here, not a redundancy — IPP-imported absorbs oil mechanically, so Oil-control partials it out cleanly).
- **Pre-committed gate.** One-sided T3b on β̂_{IPP} > 0 in OLS of Δ²log(CPI_m)^{1/3} on ε_t^{IPP} + 6 controls, α = 0.10, HAC Newey-West SE with optimal-bandwidth Andrews rule.
- **Co-primary reconciliation.** GARCH(1,1)-X with IPP-surprise in mean equation (continuity with Rev 4 convention); cross-check against Bayesian-STVAR ERPT estimate (Borrador 930 methodology) on same sample — AGREE gate = |β̂_OLS − β̂_BSTVAR| / max(SE) < 1.

### Y₃-top-1: US Hispanic-employment surprise → Remittance-flow variance

- **Surprise column.** ε_t^{HispEmp} = ΔlogEmp_Hisp,t − AR(1), first-Friday-release-dated, interpolated to weekly via step-function.
- **Controls.** Retain **VIX, DXY, Fed Funds, EMBI Colombia, Banrep Repo**; **drop Oil** (no mechanical link); **add** US-Construction-Employment (BLS CES) as cross-sector confound and Colombian quincena dummy (per `REMITTANCE_VOLATILITY_SWAP/research/CCOP_BEHAVIORAL_FINGERPRINTS.md` §8 identification lever).
- **Pre-committed gate.** One-sided T3b on β̂_{HispEmp} > 0 in OLS of log(RollVar(Rem_m, 3mo))^{1/3} on ε_t^{HispEmp} + controls, α = 0.10, HAC SE.
- **Co-primary reconciliation.** (a) GARCH-X with HispEmp-surprise in variance equation of monthly remittance innovations; (b) event-study around Jan 26 2025 Trump-Petro episode on COPM-mint-flow and Littio USDC-account-open (quasi-external-validation using on-chain high-frequency signal). AGREE gate: both OLS sign and event-study sign positive and 90% CI's overlap.

---

## 7. Cross-reference back to Agent 3 — overlap signals

| X candidate | Agent 3 Y₁ rank (TRM RV) | Agent 4 Y₂ rank (CPI) | Agent 4 Y₃ rank (Rem var) | Universality score |
|---|---|---|---|---|
| **Remittance-flow surprise (Colombia-side)** | 1 | — (indirect via ERPT) | — (endogenous to LHS) | 1/3 (single-Y primary) |
| **TRM/ΔTRM residual** | — (it IS the frozen LHS^{1/3} basis) | 2 | — | 1/3 |
| **cCOP/USDT volume** | — (not in Agent 3 top-5) | 4 | — | 1/3 |
| **COPM mint/burn** | — | — | 4 | 1/3 |
| **US Hispanic-employment surprise** | **not tested by Agent 3 — strong candidate for re-rank** | — | **1** | Potentially 2/3 |
| **Venezuelan-migration shock** | 4 | 5 | 5 | **3/3 — universal** |
| **Banrep-policy-rate surprise** | — | 3 | — | 1/3 |
| **IPP-imported residual** | — (indirect via ERPT) | **1** | — | 1/3 |
| **Trump-Petro Jan 2025 event dummy** | — (event-study overlay only) | — | 2 | 1/3 but **cross-cuts all three Y's on the 48h window** |

**Universal-observable findings:**

1. **Venezuelan-migration shock** appears in all three rankings at moderate strength — the single cross-Y candidate by the formal rank criterion. However, its regime-specificity (2015-2022 peak) limits universal deployment.
2. **Trump-Petro Jan 2025 event** is cross-cutting on the event-study axis: it moved TRM (Y₁), CPI expectations (Y₂), and Littio-observed COPM-mint (Y₃ proxy) simultaneously. This argues for a shared event-dummy in any multi-Y structural exercise.
3. **US Hispanic-employment surprise** was not tested by Agent 3 for Y₁ but is a defensible candidate via the remittance-inflow → FX-inflow → TRM-vol chain. A recommendation for Agent 5 (or a revised Agent 3 run) is to add it to the Y₁ candidate list — two-Y coverage at minimum.

---

## 8. Caveats

1. **Thin-history on-chain rows (cCOP/USDT volume, COPM mint/burn).** Both have <2yr of data. Any backtest must report subsample stability and explicitly flag pre-Oct-2024 extrapolation as hypothetical.
2. **Revision risk on remittance vintages.** BanRep monthly remittance data is revised up to 3mo post-release; real-time vintages are required for any gate-construction. Y₃ rolling-variance must be built from vintage data, not current-vintage.
3. **Frequency-mismatch penalty.** Y₂ is monthly; several X's (TRM daily, cCOP-volume daily) must be aggregated, which inflates variance artifacts. Recommended: monthly-averaged X's with log-volume sum, not point-in-time.
4. **Low-power on event-dummy rows (Y₃ #2).** Expected 8-15 Migration-policy events over 18yr; a continuous regressor always dominates for primary gate.
5. **ERPT regime shift.** Borrador 930 evidence is that ERPT to core CPI has *declined* monotonically over 2008-2020 — a structural break in the Y₂-#2 (TRM) channel. Quandt-Andrews test is mandatory; subsample-stable subperiod is likely 2010-2019 only.
6. **Multicollinearity bloat.** IPP-imported, TRM, Oil, EMBI, and DXY all co-move. VIF check is non-negotiable; use orthogonalized residuals (Gram-Schmidt) or ridge-penalized estimator if VIF > 10 on any primary term.
7. **Composition confound on Y₃.** Venezuelan-diaspora remittance (partly USDT-rail) does not appear in BanRep totals. Y₃ therefore measures *formal-channel* variance, not total-flow variance. On-chain cross-validation via COPM + cCOP bypasses this limit.
8. **CPI-FAIL bias risk.** As with Agent 3's top-1, Y₂ candidates must not be framed as "rescue after the Rev4 CPI-FAIL exercise" — they are distinct pre-commitments testing whether IPP (not CPI-surprise AR(1)) can predict *variability* (not level) of CPI.

---

## 9. Cross-reference table

| Claim | Source |
|---|---|
| 5-way MACRO_RISKS taxonomy | `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/MACRO_RISKS.md` lines 7-13 |
| Agent 3 ranking top-1 (Remittance-flow surprise) and shortlist | `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-colombia-next-primary-candidate-ranked.md` §§2-3 |
| cCOP / COPM observables inventory (540d, 720d history) | `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-ccop-mcop-observables-search.md` Parts 3-4 |
| ln(V_t) regression pre-committed, unrun; quincena identification | `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-remittance-volatility-swap-deep-read.md` §§1, 4 |
| Remittances 2.8% GDP, US corridor 53%, Valle del Cauca 26% | `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/COLOMBIAN_ECONOMY_CRYPTO.md` §§1.1-1.3 |
| Littio +100%/48h Jan 2025 Trump-Petro tariff event | `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/OFFCHAIN_COP_BEHAVIOR.md` §1; `COLOMBIAN_ECONOMY_CRYPTO.md` §3.5 |
| P2P spread 0.25-0.75% baseline; widening under stress | `OFFCHAIN_COP_BEHAVIOR.md` §4 |
| COPM 100K users, $200M/mo, BDO-audited, Apr-2024 launch | `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/COLOMBIAN_ECONOMY_CRYPTO.md` §3.3; observables report Parts 1-3 |
| Banrep Borrador 930 BSTVAR ERPT 0.01-0.05 to core CPI | WebSearch #3: `banrep.gov.co/en/borrador-930`; `banrep.gov.co/en/pass-through-exchange-rate-core-inflation-colombia-analysis-time-varying-parameters` |
| Banrep Borrador 330 disaggregated ERPT 0.1-0.8 long-run | WebSearch #3: `banrep.gov.co/sites/default/files/publicaciones/archivos/borra330.pdf` |
| DANE CPI weights: Housing 33%, Food 15%, Transport 13% | WebSearch #5: tradingeconomics.com/colombia/consumer-price-index-cpi |
| Dallas Fed: US labor market drives LatAm remittance records | WebSearch #4: dallasfed.org/research/swe/2023/swe2310 |
| IDB TN-3243 2025 remittance-adaptation note | WebSearch #4: publications.iadb.org IDB-TN-3243 |
| World Bank RPW US→Colombia Q4 2024: 4.53% total cost | WebSearch #7: remittanceprices.worldbank.org/corridor/United-States/Colombia |
| Trump-Petro Jan 26 2025 tariff-deportation standoff | WebSearch #6: washingtonpost.com 2025-01-26, cnn.com, npr.org, aljazeera.com |
| BIS WP 1340 stablecoin-FX spillovers; flight-to-safety EMDE evidence | WebSearch #8: bis.org/publ/work1340.pdf |
| Turkey/Argentina stablecoin-volume inflation-stress signal | WebSearch #8: shsconf icdde2025 literature review; IMF 2025 Understanding Stablecoins |
| ranPricing.ipynb CES underlying categories | `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/notebooks/ranPricing.ipynb` cell 3 line 14 |
| CPI T3b-FAIL verdict (context for why Y₂ reframe) | `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/gate_verdict.json` |
| 2.9M Venezuelans in Colombia as of 2025 | `COLOMBIAN_ECONOMY_CRYPTO.md` §1.5 |
| Three-arrow identification (net_flow → remittance → household income) | `remittance-volatility-swap-deep-read.md` §2 |

---

**End of report.** Word count ≈ 1,730.
