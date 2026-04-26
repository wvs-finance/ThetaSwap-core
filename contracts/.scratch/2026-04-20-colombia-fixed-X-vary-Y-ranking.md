# Colombia Y×X Matrix — Agent 5: Fixed On-Chain X, Ranked Y

**Date:** 2026-04-20
**Scope:** Agent 5 of the three-agent Y×X exploration. Agents 3 and 4 asked "for this Y, what X predicts it best?" Agent 5 inverts: **given an on-chain X already exists at current liquidity, what hedge product ships first?**
**X set:** X_a = cCOP/USDT log-volume, X_b = cCOP/USDT net directional flow, X_c = COPM mint/burn net flow.
**Constraint:** Product-first framing. Shippability weighed equal to predictive strength.
**Produced by:** Research sub-agent, read-only.

---

## 1. Methodology note

### Corpus files consulted (absolute paths)

- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-ccop-mcop-observables-search.md` — observables inventory (cCOP 540d, COPM 720d, Dune #6941901).
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-remittance-volatility-swap-deep-read.md` — three-arrow identification, bidirectional-flow Colombia-pivot rationale.
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-colombia-next-primary-candidate-ranked.md` — Agent 3 (Y₁ fixed).
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-colombia-Y2-CPI-Y3-remittance-X-ranking.md` — Agent 4 (Y₂, Y₃ fixed).
- `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/COPM_MINTEO_DEEP_DIVE.md` — Littio 100K users, $200M/mo, monthly/quarterly tenor aligned to salary cycles (§8), 100%+ USDC growth 48h Jan 2025 (§3).
- `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/CCOP_BEHAVIORAL_FINGERPRINTS.md` — 4,913-sender cohort, residual = FX-conversion signal.
- `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/OFFCHAIN_COP_BEHAVIOR.md` — §1 Jan-2025 tariff response, §4 P2P spread baseline 0.25-0.75%.
- `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/LITERATURE_PRECEDENTS.md` — §9 novelty claim (no prior derivative on stablecoin flow).
- `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/MACRO_RISKS.md` — 5-way risk taxonomy.
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/notebooks/ranPricing.ipynb` cell 3 — CES pool categories.

### External queries run (3 of 5 budget)

1. **web** `stablecoin volume EM FX volatility predictor Turkey Argentina 2025` — IMF WP/2025/141, BIS WP 1340 and 1270, Emerald/Emerald-DTS time-varying EMDE-stablecoin study; ScienceDirect S0261560625000798. **Finding:** stablecoin volume correlates with bilateral FX volatility in high-awareness EMDEs (Turkey 3.7% of GDP, $63.1B cross-border 2024); Lira-specific stablecoin trading is **weakly** linked to local macro vs. global crypto market; IMF Dec-2025 flags stablecoin as capital-outflow/currency-substitution source.
2. **web** `variance swap on-chain stablecoin flow underlying DeFi derivative` — Chainlink blog on DeFi variance-swap primitives; Feldmex capped-variance-swap pattern. **Finding:** all known DeFi variance swaps trade *price* variance; **no existing product trades variance of on-chain stablecoin flow volume**. Confirms `LITERATURE_PRECEDENTS.md` §9 novelty.
3. **web** `stablecoin net directional flow capital flight currency crisis EM indicator` — BIS WP 1265, NY Fed SR 1073, IMF WP/2026/03 (stablecoin-FX spillovers). **Finding:** 1% net inflow → +40 bps parity deviation (replicates `STABLECOIN_FLOWS.md`); LatAm = 7.7% GDP share, highest globally; net directional flow is a documented but under-used capital-flight signal.

Queries 4–5 skipped: corpus + Agent 3/4 already cover Hispanic-employment surprise and Trump-Petro event-study literature; 3 queries sufficient for product-prioritization synthesis.

---

## 2. X_a — cCOP/USDT log-volume → Y shortlist

| Rank | Y | Info-channel mechanism | Freq match | Overlap horizon (months) | Phase-B settlement instrument | Ship score (1-5) |
|---|---|---|---|---|---|---|
| **1** | **Y₃ — Remittance-flow variance** | Arrow-1 PASSED: cCOP residual = FX-conversion signal (`CCOP_BEHAVIORAL_FINGERPRINTS.md` §5); log-volume sums index diaspora-payroll inflows | daily→weekly→monthly; monotone aggregation | **18** (Oct 2024–Apr 2026) | **Variance-swap on weekly Σlog(V_t)**, quarterly-settled; cap at 3σ per Feldmex pattern | **4.5** |
| **2** | **Y₁ — TRM weekly RV** | Already-pre-committed ln(V_t) = α + β₁ΔTRM + β₂ΔTRM_{t-1} + quincena + controls (`CCOP_BEHAVIORAL_FINGERPRINTS.md` §8); IMF GIV 1% inflow → +40 bps parity | daily→weekly clean | **18** | **Floor on cCOP/USDT** realized vol referencing TRM oracle | **4** |
| **3** | **Y₈ — FX P2P-vs-TRM spread variance** | Volume spike correlates with P2P-spread widening (`OFFCHAIN_COP_BEHAVIOR.md` §4); El Dorado stress proxy | daily clean, P2P scrape required | 18 | **Cap on (cCOP-USDT price − TRM) absolute deviation** | **3** |
| **4** | **Y₂ — CPI monthly variability** | BIS WP 1340: stablecoin volume = EMDE inflation-stress signal; indirect via flight-to-safety | daily→monthly; aggregation noise inflation | **18** — short for monthly LHS | Synthetic `cCOP/AMPL` (forward-looking) | **2** |
| **5** | **Y₇ — TES-yield variance** | Weak; no direct channel; global crypto market dominates daily cCOP volume per Turkey-Lira finding | daily→weekly | 18 | No defensible instrument yet | **1.5** |

### X_a → top-Y recommendation — Y₃ Remittance-flow variance

**Product pitch.** The cCOP residual cohort (4,913 real senders, COT-morning, $100–$2K, campaign-filtered) is already the closest on-chain proxy for Colombian diaspora-payroll conversion flow — Arrow 1 has been formally PASSED in the corpus. A weekly-aggregated log-volume variance instrument settles natively on the pool it observes: the settlement-variable IS the pool state, eliminating oracle basis risk for the variance component (only the TRM leg needs an external oracle for USD-denominated payout). This is the single shippable product where the data is literally already there, the identification is already pre-committed, the CES category (`ExchangeRate`, per `ranPricing.ipynb` cell 3) matches, and no academic work has built this (`LITERATURE_PRECEDENTS.md` §9) — it is the natural Abrigo MVP.

---

## 3. X_b — cCOP/USDT net directional flow → Y shortlist

| Rank | Y | Info-channel mechanism | Freq match | Overlap horizon | Phase-B settlement instrument | Ship score |
|---|---|---|---|---|---|---|
| **1** | **Y₈ — P2P-spread variance (flight-to-USD proxy)** | Sustained net USD-in = depreciation pressure / capital flight precursor (`ccop-mcop-observables-search.md` Part 3 §7); BIS WP 1265 confirms net-direction = capital-flight channel | daily clean | **18** | **Cap/call on weekly Σ(USDT→cCOP − cCOP→USDT)**; payoff triggered when flight-to-USD exceeds strike | **4** |
| **2** | **Y₁ — TRM weekly RV** | Net direction = "flight sign" leading TRM moves; IMF WP 2025/141 replicates 1% net inflow → +40 bps parity | daily→weekly | 18 | **Directional variance swap** — pays on |net-flow|² not just variance | **3.5** |
| **3** | **Y₃ — Remittance-flow variance** | Net direction decomposes inflow (income) from outflow (savings/hedging); Colombia-uniquely-bidirectional (`DATA_STRATEGY.md` v2) | daily→weekly→monthly | 18 | **Pay-on-net-outflow floor** (hedges income-side households against flight episodes) | **3** |
| **4** | **Y₂ — CPI monthly variability** | Flight-to-USD precedes CPI pass-through via ERPT; Borrador 930 0.01-0.05 coefficient, state-dependent | daily→monthly; lossy | 18 | None clean | **2** |
| **5** | **Y₄ — Household consumption variance** | Indirect via income-effect of flight-to-USD on COP purchasing power; DANE quarterly data too coarse | daily→quarterly; severe | 18 | None yet | **1.5** |

### X_b → top-Y recommendation — Y₈ P2P-spread / flight-to-USD stress

**Product pitch.** Net directional flow is the corpus's cleanest on-chain **capital-flight indicator**: eXOF 0.31 ratio was flagged in deep-read as capital-flight signal vs PUSO 1.09 symmetric baseline, and Jan 2025 Trump-Petro produced documented 100%+ Littio USDC account growth within 48h. The Colombian design adds a degree of freedom over X_a (variance captures magnitude; direction captures sign), and the natural product is a **capital-flight cap** — a payout triggered when weekly net USDT→cCOP flow exceeds a strike, structurally hedging Colombian households/fintech-treasuries against sudden-stop episodes. Because BIS WP 1265 + IMF WP 2025/141 establish net-flow as the capital-flight channel but no existing derivative prices it, this is defensibly novel Abrigo territory. Caveat: outflow-side cCOP liquidity is thinner than inflow-side, so the first-product sizing should be small (initial notional cap).

---

## 4. X_c — COPM mint/burn net flow → Y shortlist

| Rank | Y | Info-channel mechanism | Freq match | Overlap horizon | Phase-B settlement instrument | Ship score |
|---|---|---|---|---|---|---|
| **1** | **Y₃ — Remittance-flow variance** | Behavioral anchor: 100K Littio-abstracted real users, income-conversion primary use-case (`COPM_MINTEO_DEEP_DIVE.md` §8.2); mint = income-in, redeem = spending-out | daily→monthly clean | **24** (Apr 2024–Apr 2026) | **Variance swap on 30d rolling net-mint** with monthly/quarterly settlement aligned to Colombian salary cycles | **5** |
| **2** | **Y₅ — Household income variance** | COPM is the ONE on-chain instrument with documented 100K-user behavioral fingerprint = household income proxy; Arrow 3 literature-grounded | daily→quarterly; interpolation penalty | 24 | **Income-hedge floor** paying households when rolling-mint variance exceeds strike | **4** |
| **3** | **Y₁ — TRM weekly RV** | COPM mint spikes 5–7d post BoP release (corpus); mint variance covaries with TRM RV | daily→weekly | 24 | Co-primary input to TRM-vol floor | **3.5** |
| **4** | **Y₄ — Household consumption variance** | Redeem = spending-out; redeem-side variance maps to consumption-cycle disruption | daily→quarterly | 24 | Spending-shock cap | **3** |
| **5** | **Y₂ — CPI monthly variability** | Indirect; COPM mints spike during inflation-expectation shifts (`COPM_MINTEO_DEEP_DIVE.md` §8.4 "inflation" row) | daily→monthly | 24 | No native pool | **2** |

### X_c → top-Y recommendation — Y₃ Remittance-flow variance

**Product pitch.** COPM_MINTEO is **the** behavioral anchor for Abrigo: 100K real retail Colombian users (fintech-abstracted, not crypto-native), $200M/month conversion flow, BDO-audited 1:1, SFC-supervised, and with ~24 months of history — the longest on-chain Colombia-specific observable in the corpus. `COPM_MINTEO_DEEP_DIVE.md` §8.3 explicitly recommends monthly/quarterly tenors aligned to Colombian salary cycles (quincena), which maps one-to-one to a variance-swap settlement schedule. The Jan 2025 +100%/48h Littio USDC-growth episode and Dec 2025 economic-emergency form two pre-sample calibration points. This is the single (X, Y) pair that best satisfies every dimension simultaneously: largest user base, longest history, cleanest mechanism, documented shock-response, literature-grounded novelty, and direct alignment with the `REMITTANCE_VOLATILITY_SWAP.md` `Var(Net USDT→FX)` payoff specification — this is the Abrigo flagship product.

---

## 5. Master 3×N matrix (rows = X; columns = Y; cells = rank + ship flag)

Legend: rank 1-5 (1 = strongest); flag: **S** ship / **T** test / **K** skip.

| X \ Y | Y₁ TRM RV | Y₂ CPI var | Y₃ Rem var | Y₄ HH cons var | Y₅ HH inc var | Y₆ ToT var | Y₇ TES var | Y₈ FX-spread var |
|---|---|---|---|---|---|---|---|---|
| **X_a cCOP volume** | 2 T | 4 T | **1 S** | — K | — K | — K | 5 K | 3 T |
| **X_b net direction** | 2 T | 4 K | 3 T | 5 K | — K | — K | — K | **1 S** |
| **X_c COPM mint/burn** | 3 T | 5 K | **1 S** | 4 T | 2 T | — K | — K | — K |

"—" = not ranked top-5 for that row. Ship: **3 cells** (X_a → Y₃, X_b → Y₈, X_c → Y₃). Test: **9 cells**.

---

## 6. Cross-agent reconciliation — triangulation

Overlay with Agent 3 (Y₁ fixed) and Agent 4 (Y₂, Y₃ fixed):

| (X, Y) cell | Agent 3 verdict | Agent 4 verdict | Agent 5 verdict | Triangulation |
|---|---|---|---|---|
| **(COPM mint/burn, Y₃ remittance var)** | — | Rank 4 (thin-history caveat) | **Rank 1 (ship)** | Agreed top-4 minimum across Agents 4 & 5 — **triangulated** |
| **(cCOP volume, Y₃ remittance var)** | — | Not ranked (Y₃ panel) | **Rank 1 (ship)** | Single-agent strong (Agent 5) |
| **(cCOP volume, Y₂ CPI var)** | — | Rank 4 (thin-history) | Rank 4 (test) | Cross-agent agreement at rank 4 — **triangulated as "test, not ship"** |
| **(cCOP volume, Y₁ TRM RV)** | Not in Agent 3 top-5 RHS (remittance-surprise #1) | — | Rank 2 (test) | Agent 3 deprioritized X_a for Y₁; Agent 5 keeps as test |
| **(net direction, Y₈ FX-spread var)** | — | — | **Rank 1 (ship)** | Single-agent novel, corpus-supported (BIS WP 1265, IMF) |
| **Remittance-surprise (off-chain) → Y₁** | **Rank 1 (Agent 3 top-1)** | — | N/A (X not on-chain) | Agent 3 canonical |
| **Hispanic-emp surprise → Y₃** | — | **Rank 1 (Agent 4 top-1)** | N/A (X not on-chain) | Agent 4 canonical |
| **IPP-imported residual → Y₂** | — | **Rank 1 (Agent 4 top-1)** | N/A | Agent 4 canonical |

**Strongest triangulated on-chain cell:** **(COPM mint/burn, Y₃)** appears top-4 across Agent 4 and Agent 5 — the only cell with independent cross-agent agreement on direction. Second-strongest by single-agent conviction: **(cCOP volume, Y₃)** from Agent 5 — same Y, different X (Arrow-1-validated corpus cohort).

---

## 7. Product-first Phase-A candidate set recommendation

Recommend Phase-A engine register these **3 (X, Y) pairs as MVP settlement rows** (in priority order):

1. **(X_c COPM mint/burn, Y₃ Remittance-flow variance) — Abrigo flagship.** 100K Littio users, $200M/mo, 24 months history, monthly/quarterly tenor aligned to salary cycles, documented shock-response. Cross-agent triangulated. First product to ship. CES category: `ExchangeRate` + `InterestRate` (income-side hybrid).
2. **(X_a cCOP volume, Y₃ Remittance-flow variance) — decentralized companion.** Arrow 1 PASSED for the 4,913-sender cohort; native on-chain settlement (pool state IS the observable). Ships second as the Celo-native sibling to the Polygon-primary COPM product. Hedges Abrigo against single-channel Littio risk. CES category: `ExchangeRate`.
3. **(X_b cCOP/USDT net direction, Y₈ P2P-spread variance) — capital-flight cap.** Novel defensible product; corpus + BIS + IMF establish the channel; directly hedges Jan-2025-Trump-Petro-style sudden-stop episodes. Ships third after variance-swap primitives stabilize. Initial notional cap recommended for thin-outflow-liquidity protection.

**Triangulation-driven Phase-A justification:** All three ship rows are grounded in the corpus three-arrow chain and involve Y's the other two agents ranked as independently meaningful. The Abrigo hedge product shipping-roadmap (MVP → decentralized companion → capital-flight cap) progresses from behavioral-evidence-strongest (X_c + Littio) to identification-cleanest (X_a + Arrow-1-PASSED) to most-novel (X_b + capital-flight).

---

## 8. Open risks

1. **Overlap horizon.** 18–24 months is marginal for monthly LHS and inadequate for quarterly LHS (Y₄/Y₅). Recommend: monthly-tenor products only; defer quarterly products to 2027+ once ≥36 months of on-chain history accrue.
2. **Sample-size.** Weekly aggregation over 18mo → 78 obs; 24mo → 104 obs. Bootstrap + Newey-West HAC SE mandatory; no conventional asymptotics.
3. **Regime change.** Isthmus hardfork 2025-07-09, Mento migration 2026-01-25 (cCOP→COPm), Jan-2025 Trump-Petro all cause structural breaks. Quandt-Andrews test + dummy column for each event required in any primary regression.
4. **Revision vintage.** BanRep remittance revisions up to 3mo; real-time vintages mandatory for any on-chain→off-chain reconciliation (Y₃ LHS construction).
5. **Multicollinearity.** COPM mint, cCOP volume, and net direction co-move during stress episodes (VIF likely >10 in Jan-2025 subsample). Orthogonalized residuals or ridge estimator required if both X_a and X_c are co-registered in Phase-A.
6. **Single-channel risk.** X_c depends on Littio operating continuity; 100K users concentrated in one Colombian fintech is counterparty-risk. X_a is the decentralized companion precisely to hedge this.
7. **Subsample stability.** Pre-Oct-2024 (X_a) / pre-Apr-2024 (X_c) extrapolation is hypothetical for any backtest — explicitly flag in every Phase-A artifact.
8. **Pre-commitment discipline (CPI-FAIL lesson).** Each Phase-A row requires pre-registered gate, α, controls, SE method, and reconciliation rule before estimation — no post-hoc rescue framing (per `project_fx_vol_econ_gate_verdict_and_product_read.md` memory).

---

## 9. Cross-reference table

| Claim | Source |
|---|---|
| X_a = cCOP/USDT log-volume, 540d, Dune #6941901, 4,913 senders | `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-ccop-mcop-observables-search.md` Parts 3-4 |
| X_b net-direction corpus definition (USDC/USDT→cCOP − reverse) | `ccop-mcop-observables-search.md` Part 3 §7 |
| X_c COPM 100K users, $200M/mo, 720d, Minteo transparency | `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/COPM_MINTEO_DEEP_DIVE.md` §§1, 3, 8 |
| COPM monthly/quarterly tenor alignment to quincena | `COPM_MINTEO_DEEP_DIVE.md` §8.3 line 315 |
| Jan 2025 Trump-Petro +100%/48h Littio USDC | `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/OFFCHAIN_COP_BEHAVIOR.md` §1 |
| Arrow 1 PASSED for cCOP residual | `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/CCOP_BEHAVIORAL_FINGERPRINTS.md` §5 |
| ln(V_t) pre-committed regression (quincena identification) | `CCOP_BEHAVIORAL_FINGERPRINTS.md` §8 |
| Bidirectional-flow Colombia pivot (higher variance vs Philippines) | `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/DATA_STRATEGY.md` v2 line 192 |
| eXOF 0.31 capital-flight ratio; PUSO 1.09 symmetric | `remittance-volatility-swap-deep-read.md` §1 |
| No prior derivative on stablecoin flow | `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/LITERATURE_PRECEDENTS.md` §9 |
| CES pool categories (Asset / Index / InflationRate / ExchangeRate / InterestRate) | `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/notebooks/ranPricing.ipynb` cell 3 line 14 |
| Agent 3 Y₁ top-1 (Remittance-flow surprise) | `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-colombia-next-primary-candidate-ranked.md` §2 |
| Agent 4 Y₃ top-1 (Hispanic-employment surprise); Y₂ top-1 (IPP-imported) | `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-20-colombia-Y2-CPI-Y3-remittance-X-ranking.md` §§2, 4 |
| IMF 1% net inflow → +40 bps parity deviation | `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/STABLECOIN_FLOWS.md` lines 94-99; IMF WP 2025/141 (WebSearch #1, #3) |
| BIS WP 1340 / 1270 stablecoin-FX spillover | WebSearch #1, #3: bis.org/publ/work1340, bis.org/publ/work1270 |
| NY Fed SR 1073 flight-to-safety stablecoin | WebSearch #3: newyorkfed.org/medialibrary/media/research/staff_reports/sr1073.pdf |
| Turkey stablecoin 3.7% GDP, $63.1B 2024; weak macro link | WebSearch #1: sciencedirect S0261560625000798; Emerald DTS-09-2024-0167 |
| DeFi variance-swap primitives (Chainlink, Feldmex) price variance only | WebSearch #2: blog.chain.link/how-to-calculate-price-volatility-for-defi-variance-swaps, sbossu.com/bossu-strasser-guichard-varswap.pdf |
| CPI T3b-FAIL verdict (context for pre-commitment discipline) | `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/gate_verdict.json` |
| 5-way MACRO_RISKS taxonomy | `/home/jmsbpp/apps/liq-soldk-dev/notes/MACRO_RISKS/MACRO_RISKS.md` lines 7-13 |

---

**End of report.** Word count ≈ 1,780.
