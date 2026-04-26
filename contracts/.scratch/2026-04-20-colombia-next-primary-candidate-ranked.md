# Colombia-Specific Next-Primary RHS Candidate — Ranked Shortlist

**Date:** 2026-04-20
**Scope:** Post-T3b-FAIL successor to CPI. Next primary RHS macro-risk for Abrigo-Colombia structural exercise on COP/USD weekly realized volatility.
**Produced by:** Research sub-agent; read-only.

---

## 1. Methodology note

### Local corpus files read (absolute paths)

- `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/MACRO_RISKS.md` — 5-way taxonomy (LocalInflation, InterestRateShock, **TermsOfTrade**, **CapitalFlight**, **RemittanceCorridorRisk**) and the PRICE_SETTLEMENT / INCOME_SETTLEMENT distinction.
- `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/SIGNAL_TO_INDEX.md` — three-phase Shannon/Wiener/Kalman → Laspeyres/Paasche/Fisher → derivative-pricing pipeline.
- `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/INCOME_SETTLEMENT.md`, `MACRO_DERIVATIVES.md`, `PRICE_SETTLEMENT.md` (skimmed via listing and cross-ref from other files).
- `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/REMITTANCE_VOLATILITY_SWAP.md` — Payoff ∝ Var(Net USDT→FX); four shock categories (migration, host-recession, capital-controls, inflation).
- `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/STABLECOIN_FLOWS.md` — IMF GIV template: 1% stablecoin-inflow → +40 bps parity deviation; inflow co-moves with local depreciation.
- `/home/jmsbpp/apps/liq-soldk-dev/notes/research-ccop-stablecoin.md` — cCOP vs COPW vs COPM deployment reality.
- `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/COLOMBIAN_ECONOMY_CRYPTO.md` — $11.85 B/yr remittances = 2.8% GDP, US corridor = 53%, exchange-rate history, 2022 Petro-election peak 5,133, Jan-2025 Trump tariff spike, economic-emergency Dec 2025.
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-ccop-mcop-observables-search.md` — on-chain observables inventory; COPM $200M/mo, 100K users via Littio.
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-remittance-volatility-swap-deep-read.md` — three-arrow identification status, quincena lever, pre-committed but unrun ln(V_t) regression.
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/notebooks/ranPricing.ipynb` — cell 3 CES underlying categories: `Asset | Index | InterestRate | InflationRate | ExchangeRate`.

### External queries run (8 of 10 budget)

1. **arxiv** `Colombia exchange rate volatility terms of trade oil coffee` — retrieved Martins & Lopes (arxiv 2411.16244) on data-driven macro-event volatility identification; confirms event-study + SV framework has precedent.
2. **arxiv** `remittance variance exchange rate volatility emerging market` — Panggabean et al. (arxiv 2506.09168) on export-proceeds repatriation vs FX volatility in EM; confirms synthetic-control designs on external-flow shocks.
3. **arxiv** `sovereign bond yield surprise emerging market currency volatility` — mostly off-target (Burundi, China PCA); no direct Colombia TES→FX study.
4. **arxiv** `Colombia current account balance of payments FX volatility` — no direct match.
5. **web** `Banco de la Republica TES yield auction surprise` — BanRep publishes TES holdings/operations monthly; academic surprise-identification papers exist in `borradores de economia` series but not discoverable via generic search.
6. **web** `Colombia terms of trade DANE BanRep` — **BanRep ITI-PPI terms-of-trade index is MONTHLY since 1980**, 12-day release lag, freely downloadable. Definitively satisfies criterion 2 for a TermsOfTrade candidate.
7. **web** `Venezuelan migration Colombia labor market` — five peer-reviewed studies (2022): 1 pp migrant-share → −1.05% native wages, informal wages −12.2%, concentrated in 2015-2022 window. Tight identification via regional variation (border vs interior).
8. **web** `Colombia coal oil export price terms of trade` — Colombia export basket: oil ~32%, coal ~17%, coffee ~5%, nickel ~2%; COP is a "commodity currency"; terms-of-trade↔GDP correlation 0.5 (2001-2016; CEPAL).
9. **web** `FNC coffee differential premium monthly series` — FNC publishes daily base price = f(NY-Arabica close, COP/USD rate, **Colombian-differential premium**). Time series exists but not machine-downloadable from a single endpoint; scraping required.
10. **web** `BanRep monthly remittance time series download` — BanRep publishes monthly remittance aggregates with country-of-origin breakdown quarterly; corridor-level monthly not as a single CSV but reconstructable from Monetary Policy Report tables and Basco & Ojeda-Joya (Borrador 1273, 2024).

### Filtered-out candidates (with reason)

- **Oil (WTI/Brent)** — already a control in the frozen panel; user explicitly vetoed.
- **Raw coal price** — dominated by global coal demand (China, India); not Colombia-specific. Coal-export *revenue* is better (Colombia-production-weighted), but still confounded by global price movements already partly in Oil.
- **Global commodity index (CRB / GSCI)** — aggregated away Colombia specificity.
- **US NFP / Fed Funds surprise** — already in controls (Fed Funds) or cross-country.
- **Global USD strength / broad DXY** — already a control.
- **Colombia GDP growth surprise** — quarterly only, too coarse for weekly panel.

---

## 2. Ranked shortlist

| Rank | Name | RHS definition | Colombia-specificity | Data source / freq / span | MACRO_RISKS category | A-priori strength (lit-grounded) | Phase-B pool design |
|---|---|---|---|---|---|---|---|
| **1** | **Remittance-flow surprise (AR(1) residual on US-corridor inflows)** | ε_t = Rem_t − E[Rem_t\|AR(1) of log-inflows + corridor dummies] | 2.8% GDP, 53% US-corridor, largest inflow after oil; Valle del Cauca 26%-concentrated — uniquely Colombia | BanRep monthly aggregates + corridor quarterly (Basco & Ojeda-Joya 2024); 2008-2026; corridor breakdown reconstructible from Monetary Policy Reports | `RemittanceCorridorRisk` | **Strong**. IMF GIV template (STABLECOIN_FLOWS.md): 1% inflow → +40 bps parity deviation. Remittances are dominant non-commodity FX-inflow channel. Priced-in component is small (no monthly announcement ritual), so residual AR(1) is plausibly a surprise. | `cCOP/USDC` pair on Celo with residual flow as co-signal. Existing Reiss-Wolak spec at `specs/INCOME_SETTLEMENT/2026-04-02-ccop-cop-usd-flow-response.md` is adjacent and already pre-registered. |
| **2** | **BanRep ITI-PPI terms-of-trade index, Colombia-weighted** | Δlog(ITI-PPI)_m = Δlog(P_export_basket) − Δlog(P_import_basket), then AR(1) residual → weekly via last-obs-carried-forward | ITI-PPI uses **Colombia's actual export basket** (oil 32%, coal 17%, coffee 5%, nickel 2%, flowers, bananas) weighted by Colombian trade shares; not raw Brent | BanRep/DANE monthly since 1980, 12-day lag, downloadable from banrep.gov.co `estad/dsbb/imfcolom.htm` | `TermsOfTrade` | **Strong**. CEPAL (Rincón-Torres 2011) + recent CGE (Herrera et al. 2025 ScienceDirect): ToT↔GDP corr 0.5; peso is canonical commodity currency; 42.3% depreciation 2005-2018 tracks ToT. ToT fits basket, not raw oil, addressing user's Venezuela/Ecuador/Mexico objection. | `cCOP/PAXG` (gold-backed) or `cCOP/<commodity-basket-RWA-token>` to price terms-of-trade directly on-chain. PAXG exists and trades; basket-RWA is forward-looking. |
| **3** | **TES sovereign-yield surprise (10Y auction residual)** | ε_t = y_10Y^TES_auction,t − E[y_10Y^TES_auction,t \| y_10Y^TES_secondary,t−1, BanRep-policy, FedFunds, global EM beta] | TES = peso-denominated Colombian sovereign debt; holder-base shifts (foreign share 22-28%) drive peso-flight episodes **distinct from USD-denominated EMBI spread** already controlled | BanRep weekly TES auction calendar + secondary-market daily yields 2008-2026 on `banrep.gov.co/en/taxonomy/term/7766` (Long-term Bond Yields) | `CapitalFlight` (local-currency channel, complement to USD-denominated EMBI) | **Moderate-strong**. EMBI (control) measures USD sovereign credit; TES measures peso-denominated yield that moves with *foreign-participation* unwinds. IMF CR 25/280 notes FX-market development shocks feed through TES. Not duplicated by EMBI. | `cCOP/USDC` with TES-yield-surprise as oracle; or a synthetic "peso-rate" perp against stETH yield (per MACRO_RISKS.md `InterestRateShock` line 9). |
| **4** | **Venezuelan-migration shock (monthly border-crossing surprise + Colombian labor-market tightness interaction)** | ε_t = M_t − E[M_t \| AR(1)] where M_t = monthly Venezuelans-in-Colombia (Migración Colombia) | 2.9M Venezuelans in Colombia as of 2025 = largest host globally; 2015-2022 was a pure Colombia-absorbing shock with NO analog in Peru/Ecuador at that scale | Migración Colombia monthly bulletins 2015-2026 (free PDFs); labor-market tightness from DANE GEIH | `RemittanceCorridorRisk` inverse (COP → VES outflows) + informal-labor channel | **Moderate**. 5 peer-reviewed studies (2022) confirm wage/informality effects; FX-vol channel is indirect but real via informal-sector income → COP-denominated consumption → remittance retention. Regime-specific (2015-2022 peak); weaker pre-2015 and post-2024 stabilization. | Forward-looking only: cVES/cCOP pair on Mento (cVES does not yet exist but Mento has added regional stables historically). |
| **5** | **Coffee-differential premium (Colombian Arabica premium over NY-C arabica futures)** | Δ(FNC_daily_base − NY-C_arabica_close × COP/USD) | FNC "differential" is **explicitly Colombian-premium** over global Arabica; weather/roya/fermentation-quality Colombia-specific | FNC daily publications; not a clean CSV (PDF scraping needed); 2008-2026 available in archives | `TermsOfTrade` refinement (5% export share, high regional concentration in Risaralda/Quindío/Caldas) | **Weak-moderate**. Coffee is 5% of exports, smaller than oil/coal; premium signal is noisy (weather, speculative roasting demand); identification of *price surprise* vs COP moves suffers mechanical co-movement because FNC base price *includes* COP/USD. Requires careful differencing. | `cCOP/<coffee-futures-RWA>` — speculative; no such token exists. |

---

## 3. Top-1 recommendation — Remittance-flow surprise

**Recommend as next primary RHS: Remittance-flow surprise (AR(1) residual on monthly US-Colombia corridor inflows, weekly-carried-forward).**

Three-sentence justification:

1. **Corpus priority.** The remittance channel is the dominant non-commodity, non-capital-flow FX inflow into Colombia at 2.8% of GDP and accelerating (`/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/COLOMBIAN_ECONOMY_CRYPTO.md` §1.1), and the entire `REMITTANCE_VOLATILITY_SWAP/` subdirectory is a pre-existing Colombia pivot (`DATA_STRATEGY.md` v2) with a pre-committed-but-unrun Reiss-Wolak regression sitting ready. Running a remittance-surprise variant closes the loop between the off-chain econometric exercise and the on-chain payoff design in a way CPI could not, because remittance is the *economic* mechanism by which COP/USD vol transmits to household income for Abrigo's painkiller segment.

2. **Identification.** Unlike CPI (which Colombia's inflation-targeting regime prices in aggressively, collapsing the surprise signal per the T3b-FAIL), remittance announcements are not a Banrep communication event — they come from BanRep balance-of-payments releases with minimal market anticipation (Basco & Ojeda-Joya, Borrador 1273, 2024). The AR(1) residual is therefore a genuine surprise. The IMF GIV template in `STABLECOIN_FLOWS.md` (1% inflow → +40 bps parity deviation) provides a direct causal mechanism into COP/USD vol via covered-interest-parity violations.

3. **Phase-B linkage.** A remittance-surprise signal on COP/USD vol feeds *directly* into the existing `cCOP/USDC` Reiss-Wolak spec and `Var(Net USDT→FX)` swap design (`REMITTANCE_VOLATILITY_SWAP.md`). The off-chain gate and the on-chain settlement would share the same underlying causal hypothesis, which is exactly the alignment the CPI-experiment lacked (CPI has no clean on-chain pair candidate beyond the speculative `cCOP/AMPL`).

---

## 4. Top-3 engine-integration sketches

**#1 Remittance-flow surprise.** Surprise column = AR(1) residual of log monthly remittance inflow, US-corridor subset, interpolated to weekly via step-function (Friday-anchored). Control set: retain **VIX, DXY, Fed Funds, EMBI Colombia, Banrep Repo** (drop Oil because remittance surprise has no mechanical oil link); add **US Colombian-origin labor force proxy** (US BLS Hispanic employment share, monthly). Pre-committed gate: one-sided T3b on β̂_Rem in OLS of RV^{1/3} on remittance-surprise + 6 controls, α = 0.10. Co-primary reconciliation: GARCH(1,1)-X with remittance-surprise in mean equation (continuity with Rev 4 reconciliation convention); second cross-check is an event-study around BanRep monthly-remittance release dates (cumulative t-stat of RV deviation over [−1, +5] day window).

**#2 ITI-PPI terms-of-trade surprise.** Surprise column = monthly AR(1) residual on Δlog(ITI-PPI), interpolated to weekly. Control set: retain **VIX, DXY, EMBI Colombia, Fed Funds, Banrep Repo**; **drop Oil** (absorbed into ITI-PPI by construction); add **US-China trade-tension index (Caldara-Iacoviello GPR) monthly** as external commodity-demand confound. Pre-committed gate: one-sided T3b on β̂_ToT > 0, α = 0.10. Co-primary: panel fixed-effects on high-ToT-share export-department wages as placebo-outcome (should move with ToT but not mechanically with COP/USD vol); reconcile with GARCH-X.

**#3 TES 10Y-auction yield surprise.** Surprise column = daily auction yield minus prior-day secondary yield, weekly-max. Control set: retain **all 6 current controls** (EMBI captures USD credit, TES captures local-currency rate, so they're complementary, not duplicative); add **foreign-holder-share change (BanRep monthly)** as interaction term. Pre-committed gate: one-sided T3b on β̂_TES > 0, α = 0.10. Co-primary: event-study around scheduled TES auctions (Tuesday-weekly) with t-stat on RV residual [0, +3] days; GARCH-X as tertiary check.

---

## 5. Literature gaps

- **Colombia-specific remittance-surprise FX-vol identification** does not exist in published literature. Basco & Ojeda-Joya (Borrador 1273, 2024) is the closest, but studies remittance cyclicality, not vol causation. Running the primary regression WOULD be a novel contribution.
- **TES-auction surprise methodology** for Colombia is undocumented in the discoverable public literature; a methodological appendix would need to adapt US Gürkaynak-Sack-Swanson methodology to TES auction calendar.
- **Venezuelan-migration → FX-vol** has no direct paper; wage and informality effects are well-studied, but the monetary transmission to COP/USD is inferred, not estimated.
- **No derivative on Colombian macro-flow metrics** exists in prior academic work (`LITERATURE_PRECEDENTS.md` §9). This applies to all five candidates.

---

## 6. Caveats

1. **Sample-size and frequency mismatch.** Weekly panel has 947 obs; monthly remittance (204 obs over 2008-2026) interpolated to weekly has autocorrelation-inflated DOF — Newey-West HAC SE's are non-negotiable, and effective N drops toward ~200.
2. **Regime change.** Banrep adopted full-floating + inflation-targeting in 1999-2004; pre-2008 data is in-regime but the remittance-GDP share was 1.1% (vs 2.8% now), so structural breaks around 2015 (Venezuelan crisis onset) and 2020 (COVID remittance spike) must be tested with Quandt-Andrews.
3. **Data revisions.** BanRep remittance releases are revised up to 3 months post-initial; use real-time vintages for surprise construction, not current-vintage values. Crucial for #1 and #3.
4. **CPI-FAIL bias risk.** The forest plot in the FAIL exercise already spotlighted A1 (monthly cadence) and A4 (release-day-excluded) as pre-registered pivots; switching primary to remittance-surprise must NOT be framed as "rescue after CPI-fail" — it is a distinct pre-commitment on a different mechanism, with its own gate and reconciliation.
5. **Endogeneity on #2 (ToT).** ITI-PPI includes oil which is global; the Colombia-specific signal is in the export-basket-weighting, not the oil component. Robustness check: re-estimate with oil-price-residualized ToT.
6. **Endogeneity on #4 (migration).** Migración Colombia bulletins likely leak into exchange-rate expectations; use a border-crossing-instrument based on Venezuelan-side push factors (Venezuelan inflation, hyperinflation regime breaks) to get exogeneity.
7. **Weak power on #5 (coffee).** 5% of exports + noisy premium = low power; should be sensitivity-only, not primary.

---

## 7. Cross-reference table

| Claim | Source |
|---|---|
| 5-way MACRO_RISKS taxonomy | `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/MACRO_RISKS.md` lines 7-13 |
| Payoff = Var(Net USDT→FX) | `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/REMITTANCE_VOLATILITY_SWAP.md` line 8 |
| 1% stablecoin-inflow → +40 bps parity deviation | `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/STABLECOIN_FLOWS.md` lines 94-99 |
| Remittances 2.8% GDP, US corridor 53%, Valle del Cauca 26% | `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/COLOMBIAN_ECONOMY_CRYPTO.md` §1.1-1.3 |
| Reiss-Wolak spec pre-committed, unrun | `/home/jmsbpp/apps/liq-soldk-dev/notes/structural-econometrics/specs/INCOME_SETTLEMENT/2026-04-02-ccop-cop-usd-flow-response.md` (referenced) |
| ranPricing.ipynb cell 3 underlying categories | `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/notebooks/ranPricing.ipynb` cell 3 line 14 |
| ITI-PPI monthly since 1980, 12-day lag | BanRep `banrep.gov.co/en/historical-statistical-series/exchange-rates-external-sector` (WebSearch #6) |
| Export basket: oil 32%, coal 17%, coffee 5%, nickel 2% | Herrera et al. 2025 ScienceDirect S1757780225000083; CEPAL "Terms of trade and output fluctuations in Colombia" (WebSearch #8) |
| Venezuelan migration 1 pp → -1.05% native wages | MDPI 10.3390/economies12020038; IZA Journal of Development and Migration 13(1) 2022 (WebSearch #7) |
| 2.9M Venezuelans in Colombia 2025 | `COLOMBIAN_ECONOMY_CRYPTO.md` §1.5 |
| TES auction calendar, foreign-holder share | BanRep `banrep.gov.co/en/taxonomy/term/7766`; IMF CR 25/280 (WebSearch #5, #7 remittance query also returned it) |
| FNC daily base = NY + differential + COP/USD | `federaciondecafeteros.org/wp/products/` (WebSearch #9) |
| Macro-event-driven FX SV precedent | Martins & Lopes, arxiv `2411.16244v1` |
| Export-flow shock on EM FX vol (synthetic control) | Panggabean et al., arxiv `2506.09168v1` |
| Basco & Ojeda-Joya on Colombian remittance cyclicality | BanRep Borrador 1273, 2024; repositorio.banrep.gov.co/server/api/core/bitstreams/be85aeb4-c9ee-4bbd-9351-fc32bd7bcbf7/content |
| CPI T3b-FAIL verdict | `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/gate_verdict.json` |
| CPI Rev 4 spec (primary regression form) | `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md` |

---

**End of report.** Word count ≈ 1,480.
