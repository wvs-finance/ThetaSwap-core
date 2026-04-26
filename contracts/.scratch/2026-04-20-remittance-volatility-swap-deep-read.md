# REMITTANCE_VOLATILITY_SWAP — Deep Read Report

**Date:** 2026-04-20
**Scope:** Full deep read of `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/` and `research/` subdirectory, cross-referenced with `MACRO_RISKS/`.
**Parent context:** Post-T3b-FAIL on off-chain CPI→TRM-vol; pivot to on-chain observables.
**Produced by:** general-purpose sub-agent; foreground persisted to disk.

---

## Files read

`REMITTANCE_VOLATILITY_SWAP.md`, `STABLECOIN_FLOWS.md`, `research/CONTEXT_MAP.md`, `COPM_MINTEO_DEEP_DIVE.md`, `CCOP_BEHAVIORAL_FINGERPRINTS.md`, `COLOMBIAN_ECONOMY_CRYPTO.md`, `OFFCHAIN_COP_BEHAVIOR.md`, `CURRENCY_SELECTION.md`, `CROSS_CURRENCY_COMPARISON.md`, `DATA_STRATEGY.md`, `CELO_EVENT_CONTROL_VARIABLES.md`, `CELO_COLOMBIA_EVENT_TIMELINE.md`, `LITERATURE_PRECEDENTS.md`, `BANREP_TRM_ACCESS.md`, `DATA_API_AVAILABILITY.md`; plus `MACRO_RISKS/{SIGNAL_TO_INDEX,INCOME_SETTLEMENT,PRICE_SETTLEMENT,MACRO_RISKS,MACRO_DERIVATIVES}.md`.

---

## 1. Full observables catalog

**Payoff target:** variance swap, `Var(Net USDT→FX)` (`REMITTANCE_VOLATILITY_SWAP.md`).

**On-chain signals:**
- Mento broker swap events: `mento_celo.broker_evt_swap` per pair (Dune #6939814)
- Uniswap V3 cCOP/COPm swap events: 96,660 trades, 276 takers, ~10K/month (`CCOP_BEHAVIORAL_FINGERPRINTS.md` §1)
- Carbon DeFi strategy fills (bot layer)
- ERC-20 Transfer events with mint/burn filters (`from`/`to` = 0x0) for COPM, cCOP, COPm (Query #6940691)
- `stablecoins_multichain.transfers` cross-token aggregator (Query #6939820)
- Top-sender / top-receiver clustering (Queries #6940020, #6940021)
- Address-overlap cCOP↔COPM: **56 dual-token addresses** ground-truth calibration (Query #6940833; §5)
- Transaction-size distribution bucketed (Query #6940855)
- UTC hour-of-day / day-of-week fingerprints (Query #6939997)

**Off-chain signals:**
- BanRep TRM daily COP/USD via `datos.gov.co` Socrata `mcec-87by.json`, free (`BANREP_TRM_ACCESS.md`)
- BanRep monthly remittance aggregates + corridor breakdowns
- World Bank RPW 365-corridor quarterly costs
- DANE GEIH household survey
- El Dorado P2P spread over TRM: 0.25–0.75% normal, widens under stress (`OFFCHAIN_COP_BEHAVIOR.md` §4)
- Littio user growth as tariff-episode proxy (Jan/Feb 2025: 100%+ 48-hour)
- Minteo transparency portal for COPM supply/attestation

**Pre-committed identification choices:**
- Primary regression (`CCOP_BEHAVIORAL_FINGERPRINTS.md` §8):
  ```
  ln(V_t) = α + β₁ΔTRM_t + β₂ΔTRM_{t-1}
          + γ₁·D_quincena + γ₂·D_thursday + γ₃·D_weekend + u_t
  ```
  Joint tests: β₁+β₂ > 0 (macro content), γ₁ > 0 (income-cycle mechanism).
- Full spec at `specs/INCOME_SETTLEMENT/2026-04-02-ccop-cop-usd-flow-response.md` (referenced; external).
- Quincena (15th / last-day Colombian salary dummy) = core identification — Colombian Labor Code Art. 134.
- Event exclusions: Isthmus hardfork Jul 7–12 2025, Mento migration Jan 24–26 2026, campaign days.

---

## 2. Three-arrow identification — current status

| Arrow | Claim | Status |
|---|---|---|
| **Arrow 1** | net_flow(USDC→cCOP) → remittance_inflow | **PASSED for Colombia** (`CCOP_BEHAVIORAL_FINGERPRINTS.md` §5). cCOP residual post-cleaning: 16.6% in $100–$2K bucket vs COPM 2.3%. Establishes cCOP residual as FX-conversion signal; COPM as spending signal. |
| **Arrow 2** | remittance_inflow → household_income_from_transfers | LITERATURE-supported, calibration incomplete. Send-side vs receive-side, timing lag, channel coverage (stables = 3–6% of $12B/yr per `COLOMBIAN_ECONOMY_CRYPTO.md` §1.4). IMF WP/26/056 GIV template cited (1% inflow → 40 bps parity dev). BanRep monthly-corridor ↔ daily-cCOP-residual merge not yet executed. |
| **Arrow 3** | household_income_from_transfers → total_household_income_variation | LITERATURE-grounded. Colombia: 2.8% GDP, 3.6% disposable income, 3.9% household consumption. Exercise 0 literature review unchecked. |

**Proposed designs:**
- Exercise 2: migration-shock event study (treated/control corridors)
- Exercise 3: host-country recession with sector-specific IV
- Exercise 4: capital-controls event study (flagged best near-term for Nigeria — Colombia has no formal capital controls)
- Exercise 5: inflation IV via commodity-price shocks (needs AMPL/Layer-2)

---

## 3. Contamination / basis risk

**Contaminants** (`CONTEXT_MAP.md` §2/§6.4): speculation, arbitrage, yield-seeking, capital flight, MEV.

**Filtering strategies:**
- Size filter $200–$2000
- Frequency/cadence filter via quincena dummy
- Address clustering: ImpactMarket UBI filter, <10-counterparty bot filter, campaign-date exclusion
- Directional-asymmetry test (eXOF 0.31 = capital-flight flag; PUSO 1.09 = symmetric)
- Counterparty fingerprinting (e.g., 0x5bd3… = real-app 1,093 counterparties; 0x2021… = cross-ecosystem arb bot)
- Cross-token address-overlap calibration: 56-address sample, UTC 12–13 hour (= Colombia morning), $730–$1,008 median validates income-size

**Resolved:** cCOP residual and COPM serve *different* economic functions (FX conversion vs spending); residual is the clean income signal.

**Unresolved:**
- Pure-remittance filter vs broader "net purchasing-power transfer"
- Venezuelan diaspora cross-border noise
- Variance window (7d/30d/90d) + realized vs EWMA vs GARCH

---

## 4. Colombia-specific applicability

**Four COP stablecoins:**
- cCOP (Mento, DAO-governed): ~0.25% of Mento reserve, minimal traction; Jan 2026 symbol rename → COPm (same address)
- **COPM (Minteo):** 100k+ users via Littio, $200M/mo, 1:1 fiat, SFC-supervised, BDO monthly attestation, Polygon primary + Celo + Solana + Kraken-listed Dec 2025
- COPW (Wenia / Bancolombia): bank-issued, non-Celo rails
- nCOP (Num Finance, Polygon): over-collateralized, 8% yield, smaller scale

**Feasibility tier:** Colombia #4 in `CURRENCY_SELECTION.md` composite ("good all-around"): 269K historical + 29K monthly transfers; highest trader breadth at 5,903 receivers. **`DATA_STRATEGY.md` v2 explicitly pivoted from Philippines to Colombia** because:
1. cCOP = most organic market (4,913 senders, Colombia UTC-5 timezone, flattest size distribution)
2. Colombia uniquely has **BIDIRECTIONAL flow** (USD→COP income + COP→USD hedging via Littio) — higher variance than unidirectional Philippines

**Known failure modes:**
- Single-channel risk: Littio downtime collapses retail COPM
- DIAN Resolution 000240 reporting may push users off identifiable rails (`COLOMBIAN_ECONOMY_CRYPTO.md` §7.2)
- Data window <2 years → tenor downgrade recommended to quarterly
- DEX liquidity thin (~$22K) → most COPM volume is off-chain Minteo API

**COPM_MINTEO is the behavioral reference:** §8.2 confirms mint = income-in, redeem = spending-out; §8.3 sets monthly/quarterly tenor to salary cycles; §8.4 tabulates variance-increase shocks (COP depreciation, recession, remittance disruption, Petro crisis, inflation).

---

## 5. Open decisions (recommended resolution order)

From `CONTEXT_MAP.md` §6:

1. ~~Country selection~~ — **RESOLVED to Colombia** (`DATA_STRATEGY.md` v2)
2. Predict-vs-explain semantics — recommended contemporaneous (hedgers need realized-risk covariance)
3. Income definition (§6.2, 4 variants a-d) — pre-committed ln(V_t) regression implicitly chooses log-volume
4. Contamination strategy (§6.4) — strict remittance vs broader net purchasing-power transfer (directly affects Arrow 1 basis risk)
5. Variance computation (§6.6) — window, estimator, returns-basis
6. Time granularity (§6.9) — daily (fintech hedgers) vs monthly (LP hedgers)
7. Shorts identity (§6.7) — only resolvable post-PRE_REQ; needs variance-risk-premium evidence
8. Settlement mechanism (§6.8) — custom Layer-3 index contract vs Panoptic/Voltaire decomposition

---

## 6. Cross-reference to MACRO_RISKS 3-phase pipeline

| Phase | Maps onto |
|---|---|
| 1 — Signal Processing (Shannon/Wiener/Kalman) | Mento broker swap events → TWAP/EMA/outlier-removal → residual cCOP net-flow signal. The UBI/bot/Thursday/hardfork filters in `DATA_STRATEGY.md` Step 1 **are** the Wiener/Kalman denoisers. |
| 2 — Index Construction (Laspeyres/Paasche/Fisher) | residual weekly net-flow + ΔTRM + quincena → **Remittance Health Index (RHI)**, named as Layer-3 example in `CONTEXT_MAP.md` §1. Laspeyres/Paasche/Fisher question == unresolved variance-computation choice. |
| 3 — Settlement (derivative pricing / Shiller) | `Var(RHI)` vs strike = cash payout. Basis risk = distance between cCOP residual and actual receiving-household income variance. |

**Income vs price settlement:** `INCOME_SETTLEMENT.md` argues income > price (fees accrue, reads state directly, IS the fundamental). `PRICE_SETTLEMENT.md` applies when cash markets illiquid/heterogeneous (perpetuals fix). **The remittance variance swap is hybrid:** observable is flow (income-settlement style — reads state directly) but derivative pays variance of flow (price-settlement style — perpetual on constructed index).

---

## 7. Next-experiment candidates — feasibility matrix

| Feasible NOW (Colombia, 2026-04-20) | Status |
|---|---|
| Exercise 0 literature foundation (Arrow 3 validation) | desk-only, unchecked |
| Exercise 1 data-feasibility probe | **already executed** — permanent Dune queries #6939996 – #6940887 |
| **Pre-committed ln(V_t) regression on daily cCOP residual vs ΔTRM** | **all inputs ready — unrun** |
| Jan 2025 Trump-Petro tariff crisis mini-event study | 48-h Littio 100%+ spike documented |
| Bidirectional decomposition (Littio-outflow vs remittance-inflow) | queryable from overlap results |

| Feasible LATER | Blocker |
|---|---|
| Exercise 2 migration shock | needs ≥12mo daily corridor data; Colombia window starts ~Oct 2024 — marginal in 2026 |
| Exercise 3 host-country recession IV | harder identification than Ex 4 |
| Exercise 4 capital controls | best for Nigeria (Naira flotation); Colombia has no formal controls |
| Exercise 5 inflation IV via commodity shocks | needs AMPL/Layer-2, not yet implemented |
| Full Reiss-Wolak closure | needs open decisions 2–6 resolved |

| Blocked | Reason |
|---|---|
| Comprehensive COPM on-chain volume | thin DEX liquidity; Minteo-API flows off-chain |
| Robust GARCH monthly variance | data window <2 years; recommend quarterly tenor |

---

## 8. Headline findings for the active brainstorm

1. **Arrow 1 is already PASSED for Colombia** (`CCOP_BEHAVIORAL_FINGERPRINTS.md` §5). cCOP residual = FX-conversion/income signal, cleanly separated from COPM spending signal.
2. **Colombia was explicitly selected over Philippines** because bidirectional flow generates more variance than unidirectional corridors.
3. **The ln(V_t) regression with ΔTRM + quincena dummy is already pre-committed and ready to run** — direct structural successor to the FAILed off-chain CPI→RV exercise, now asking the same macro question from the on-chain observable side.
4. **Quincena (15th/last-day Colombian salary) is the sharpest identification lever** — built into Colombian Labor Code Art. 134.
5. **COPM_MINTEO confirms behavioral reference:** 100K real users via Littio, income-conversion-driven, Wompi/Bancolombia pedigree, BDO-audited. Single-channel Littio risk is the main vulnerability.
6. **No prior academic work has built a derivative on stablecoin flow metrics** (`LITERATURE_PRECEDENTS.md` §9) — genuinely novel vs IMF/BIS flow analysis.
7. **MACRO_RISKS pipeline maps cleanly:** cCOP residual filters = Phase-1 denoisers; RHI construction = Phase 2; Var(RHI) vs strike = Phase 3.
8. **Remaining gating decisions should be resolved in order 2→3→4→5→6** before closing the full spec.
