# cCOP / mCOP (COPM) On-Chain Observables — Corpus Search Report

**Date:** 2026-04-20
**Scope:** Existing research across `/home/jmsbpp/apps/liq-soldk-dev/notes/` indexing cCOP (Mento / Celo Colombia DAO), COPM / mCOP (Minteo / via Littio), COPW (Wenia / Bancolombia), and nCOP (Num Finance) as candidate on-chain observables for the Abrigo Colombia macro-hedge RAN.
**Parent context:** Post-T3b-FAIL on the off-chain CPI→TRM-vol exercise (`gate_verdict.json` = FAIL, β̂ = −0.000685). User is pivoting to on-chain observables since payoffs settle on-chain.
**Produced by:** Explore sub-agent (medium thoroughness); foreground persisted to disk.

---

## Part 1 — Catalog of research files referencing Colombian peso stablecoins

**Total files indexed:** 54 (references to cCOP/mCOP/COPM/COPW/Mento/Minteo/Littio/Wenia/Colombian-peso stablecoin).

**Top-priority files (directly actionable):**

| File | Summary |
|---|---|
| `/home/jmsbpp/apps/liq-soldk-dev/notes/research-ccop-stablecoin.md` | Master taxonomy — contract addresses, chain deployments, DEX venues, issuer governance comparisons (cCOP vs COPW) |
| `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/COPM_MINTEO_DEEP_DIVE.md` | COPM commercial profile: 100K users (via Littio), $200M/mo volume, 1:1 BDO-audited; primary use = salary/income conversion |
| `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/CCOP_BEHAVIORAL_FINGERPRINTS.md` | Dune queries #6939996–#6940887; 4,913 "real user" senders post-cleaning; income-sized tx range $100–$2K |
| `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/CELO_COLOMBIA_EVENT_TIMELINE.md` | Forensic event log Oct 2024 – Apr 2026; identifies Isthmus Hardfork (2025-07-09) as activity-spike cause |
| `/home/jmsbpp/apps/liq-soldk-dev/notes/structural-econometrics/specs/INCOME_SETTLEMENT/2026-04-02-ccop-cop-usd-flow-response.md` | Reiss-Wolak-style econometric spec over 540-day window; joint-test β₁+β₂ on macro content of flow response |
| `/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/research/CONTEXT_MAP.md` | Three-arrow identification chain (net_flow → remittance → household income), tiered country-feasibility table |

---

## Part 2 — Hard facts

### Contract addresses and deployments

| Token | Issuer | Primary chain | Contract | Secondary chains |
|---|---|---|---|---|
| cCOP (symbol rename → COPm 2026-01-25) | Mento / Celo Colombia DAO | Celo | `0x8a56...` + Mento broker `0x777a8255ca72412f0d706dc03c9d1987306b4cad` | Celo-only |
| COPM | Minteo | Polygon (primary, $200M/mo) | (Celo contract `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606`) | Celo, Solana, Ethereum |
| COPW | Wenia (Bancolombia) | Polygon | `0x55cF6b630d8AE6477DF63e194F0fd80ACFf05f86` | none |
| nCOP | Num Finance | Polygon | — | — |

### Supply, volume, user base

- **cCOP (Mento):** 278–360M tokens outstanding (~$70–86K USD equivalent), launch Oct 2024. Primary venue = Mento vAMM (protocol mint/redeem, not an LP pool).
- **COPM (Minteo):** $200M/month volume, 100K+ real retail users via Littio neobank integration, 50+ B2B corporate clients, launch April 2024.
- **COPW (Wenia):** Custodial within Wenia exchange; no public DeFi pool.

### DEX venues (observable at source)

| Token/pair | Venue | Chain | Activity (latest) |
|---|---|---|---|
| cCOP ↔ USDT / cUSD / USDC | Mento vAMM | Celo | 24.5K trades / 30d, 3,578 unique traders |
| cCOP ↔ USDT | Uniswap V3 (Celo) | Celo | 96.6K trades / 30d, peak $11.9K/day volume |
| COPM ↔ USDT | Uniswap V3 (Celo) | Celo | ~$22K pool TVL |
| COPM (retail conversion) | Minteo API (off-chain rails) | Polygon | ~$6.7M/day on-chain-equivalent |
| COPM | Kraken (CEX) | global | Listed Dec 23, 2025 |

### Known behavioral cohorts (from `CCOP_BEHAVIORAL_FINGERPRINTS.md`)

- **4,913 senders** remain after removing UBI/bot/campaign artifacts.
- Income-sized transaction range: **$100–$2K**.
- Colombian timezone signature: activity concentrated **8–10am UTC** (≈3–5am COT, consistent with morning payroll / remittance cycles).
- **No campaign-spike artifact** remains in cleaned cohort.

---

## Part 3 — Observables inventory (queryable on-chain)

### Price observables
1. **Uniswap V3 (Celo) TWAP** — cCOP/USDT. 1-hour oracle, **170 days of history**. Sufficient for daily-frequency aggregation. Fallback oracle since **no Chainlink COP/USD feed is deployed on Celo**.
2. **Parity deviation** — cCOP (Mento vAMM price) vs cCOP (Uniswap V3 Celo spot) vs BanRep TRM (official rate). Three-way spread = stress/arb-inefficiency signal.
3. **Rolling realized variance** — 30-day window of ln(V_t) on cCOP flow; *thick enough* over 540 days for daily-to-weekly settlement aggregation.

### Flow observables
4. **Daily cCOP gross volume** — Dune query #6941901, 540 days of history.
5. **Income-volume proxy** — transactions in $200–$2K range, filtered to FX-converter archetype.
6. **COPM mint/burn net flow** — 104.7K on-chain transfers + off-chain via Minteo API; ≈ $100K/day on-chain component alone.
7. **Directional flow (net)** — USDC/USDT→cCOP swaps minus cCOP→USDC/USDT swaps. Macro-stress indicator: sustained net USD-in = depreciation pressure / capital flight precursor.
8. **Unique-sender count (daily)** — 181–276 post-cleaning; directly observable and stable.

### LP / fee observables (for RAN underlying construction per `ranPricing.ipynb`)
9. **feeGrowthGlobal, feeGrowthInside** — Uniswap V3 per-position fee accrual; directly queryable from pool contract state.
10. **Tick liquidity L^{b_k}_i** — current concentrated-liquidity depth by tick.
11. **rewardGrowthInside(i\*)** — growth inside a tick range used as `ranPricing` `g^pool(i\*)` observable.

### Stress observables
12. **Mento Reserve composition changes** — shifts in cCOP backing basket (USDC / CELO / other Mento stables) as governance / redemption pressure indicator.
13. **Flight-to-USD flow spike** — Littio USDC-account growth (from COPM_MINTEO_DEEP_DIVE.md: "100%+ growth in new USDC yield accounts during the Feb 2025 Petro-Trump tariff crisis").

---

## Part 4 — Feasibility per observable

| Observable | History | Queryability | Thickness | Verdict |
|---|---|---|---|---|
| cCOP daily gross volume | 540 d | Dune (free) | $5K–$12K/day | **MARGINAL** alone; combined with COPM OK |
| cCOP realized variance (30-d rolling) | 540 d | Dune + pandas | Thick | **VIABLE** for daily-to-weekly settlement |
| COPM daily net flow | ~720 d (Apr 2024→) | Dune + Minteo API | ~$100K–$6.7M/day | **VERY THICK** |
| Uniswap V3 TWAP (cCOP/USDT Celo) | 170 d | Celo RPC | 100+ trades/day | **VIABLE** (fallback oracle) |
| Mento vAMM swap events | Oct 2024→ | Dune + Celo RPC | Thick | **VIABLE** |
| Price divergence (Mento vs Uniswap vs TRM) | 170 d | multi-source | thick | **VIABLE** (stress signal) |
| Income-sized senders (behavioral cohort) | 540 d post-clean | Dune | 181–276/day | **VIABLE** |
| LP observables (feeGrowth, tick L, rewardGrowthInside) | from deployment | RPC direct | low | **VIABLE** but thin early |

---

## Part 5 — Mapping off-chain β-set candidates to on-chain proxies

| Original off-chain candidate (β set) | On-chain cCOP/COPM proxy | Proxy strength | Notes |
|---|---|---|---|
| **C6. CPI-monthly-A1 pivot** | (none direct) | NOT VIABLE as flow-based proxy | CPI→TRM→on-chain flow is indirect. But **pair-based reframe**: `cCOP/AMPL` price directly proxies CPI (AMPL's rebase = purchasing-power target) |
| **C2. Fed/FOMC surprise** | Flight-to-USD flow spike (COPM redeem, Littio USDC-acct growth) | WEAK, 1–3 day lag | Works as event-study LHS, not as continuous signal |
| **C3. VIX risk-off** | Net USD-in flow + variance spike | WEAK, indirect | Correlated but not causal-tight |
| **C4. EMBI Colombia** | Thin-liquidity episodes (observable but noisy) | MARGINAL | Causation direction unclear |
| **C1. Oil terms-of-trade** | None direct; COP depreciation mediates | WEAK | Could be `cCOP/PAXG` pair in reframed design |
| **Realized COP/USD moves** *(new candidate)* | cCOP/COPM flow response; joint β₁+β₂ test per Reiss-Wolak spec | **VIABLE — primary macro-content signal** | 540 obs, spec written but regression NOT YET RUN |
| **Remittance shocks** *(new candidate)* | COPM mint spikes 5–7 days post-BoP-inflow release | **VIABLE** (secondary, lagged) | |
| **Political / macro crisis** *(new candidate)* | Variance spike + flight-to-USD surge | **VIABLE** (stress observable; Feb 2025 event documented) | |

---

## Part 6 — Critical findings

1. **On-chain flow observables ARE queryable** for Colombia: Dune (free), 540-day history, cCOP + COPM combined provide both a decentralized signal (cCOP) and a behavioral reference (COPM = 100K real users).
2. **COPM is the behavioral anchor**, not cCOP: 100K real Colombian users (fintech-abstracted, not crypto-native), $200M/mo conversion volume, primary use = income→stablecoin. This is what grounds "on-chain flow ≈ household income proxy" claims.
3. **Cleaned cCOP cohort** (4,913 senders, $100–$2K tx, COT morning timezone, campaign-artifact-free) is the Layer-1 observable for the Reiss-Wolak flow-response spec.
4. **Realized variance of cCOP/COPM daily flow is the settlement variable** — not spot price vol alone. Macro shocks affect both volume AND variance.
5. **No Chainlink COP/USD feed on Celo** — Uniswap V3 TWAP (170 d, 100+ trades/day) is the viable price oracle fallback, but this constrains any "pool-price → macro-risk" backtest window.
6. **The off-chain CPI→TRM-vol FAIL does not kill the CPI channel on-chain** — it tested surprise→vol causation, not pair-price mimicry. `cCOP/AMPL` remains a live pair-design hypothesis for CPI.
7. **A prior Reiss-Wolak spec already exists** for on-chain flow response to COP/USD moves (`2026-04-02-ccop-cop-usd-flow-response.md`, 540 obs, β₁+β₂ joint test). This regression has **not yet been run** per the documentation. Running it is a cheap, high-information next step.
8. **cCOP symbol renamed to COPm on 2026-01-25** — any historical Dune query pre-dating that needs the old symbol; post-dating uses the new.

---

## Pointers for the active brainstorm

- The pair-based reframe (`cCOP/X` where X's mechanics tie its price to macro risk Y) is consistent with the existing corpus. `cCOP/AMPL` for CPI is explicitly named in `ranPricing.ipynb` and aligns with the `INCOME_SETTLEMENT.md` "universal measurement basis" (AMPL as inflation numeraire).
- The most immediately-valuable next experiment from this corpus is the **already-specified-but-not-run** Reiss-Wolak flow-response regression at `/home/jmsbpp/apps/liq-soldk-dev/notes/structural-econometrics/specs/INCOME_SETTLEMENT/2026-04-02-ccop-cop-usd-flow-response.md`. 540 observations, pre-registered, joint β₁+β₂ gate. It tests on-chain flow response to off-chain COP/USD moves — the bridge between the two worlds.
- Pair viability at present (Apr 2026): `cCOP/USDT` (Celo Uniswap) has 170 d TWAP history, $7–12K daily. `cCOP/AMPL` does not exist yet as a pool — it is a pair-DESIGN hypothesis, not a backtestable observable. Any `cCOP/AMPL` engine candidate will need simulation-based backtest against the Colombia panel, not historical on-chain data.
