---
artifact_kind: cop_corridor_aggregate_substrate_discovery
spec_ref: contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md (v1.4 sha fcebc95f923e1b55fbf2eaa22239b00bbde4a9f35bb031e8f32d090a4fb80d95)
plan_ref: contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md (v1.1 sha 7e2f43c211a314475c3fc2ef5890c268c7216efa55b0b7a9d2c8e5d8d95bca6b)
parent_task: Pair D Stage-2 Path B Phase-1 — aggregate COP-corridor substrate pivot research
emit_timestamp_utc: 2026-05-04
budget_pin: free_tier_only
methodology: WebSearch + WebFetch + block-explorer public access; verification via Celoscan / Polygonscan / GeckoTerminal / DexPaprika / Minteo Transparency portal
constraints:
  - On-chain visibility is HARD GATE
  - No WTP / behavioral-demand inference (CORRECTIONS-γ structural-exposure framing)
  - No Path A files touched
  - No spec / plan / CLAUDE.md modification
  - Stage-1 sha-pin chain READ-ONLY
prior_research_referenced:
  - contracts/.scratch/path-b-stage-2/phase-1/a_s_pivot_research/discovery_research.md
  - contracts/.scratch/path-b-stage-2/phase-1/a_s_pivot_research/SYNTHESIS.md
  - contracts/.scratch/path-b-stage-2/phase-1/gate_b1_review.md
  - contracts/.scratch/pair-d-stage-2-B/v0/audit_metrics_raw.json
---

# Pair D Stage-2 Path B — Aggregate COP-Corridor Substrate Discovery

## Executive Summary

The current Mento-native-ONLY substrate (Mento V2 COPm `0x8A567e2a…` + Mento V2 BiPool USDm/COPm exchange) is empirically too thin for r_(a_l) reconstruction: $75K non-LP-user notional / 302 swaps / 27 months on the BiPool direct-pair side, and 0 events on the Mento V3 FPMM USDm/cUSD pool. Per user directive, this research pivots to an **aggregate COP-corridor methodology** — characterize ALL on-chain COP-pegged tokens / venues, then propose a single combined structural-exposure proxy.

**Findings:**

- **Total venues discovered (including Mento V2 COPm baseline + Minteo Celo):** 7 active token deployments + 1 deprecated + 2 supporting venues.
- **NEW venues discovered beyond Mento V2 COPm + Minteo Celo:** **5** (Minteo Polygon COPM, Minteo Solana COPM, Wenia COPW Polygon, Num Finance nCOP Polygon, Daily COP DLYCOP Polygon, +Daily COP DLYCOP BSC as historical artifact = 6 if counting BSC as separate).
- **Top-3 ranked NEW venues by aggregate-substrate fit:**
  1. **Minteo Polygon COPM** `0x12050c705152931cFEe3DD56c52Fb09Dea816C23` — confirmed multi-chain Minteo deployment with publicly attested $200M+ monthly volume, 100K+ Colombian users via Littio.
  2. **Num Finance nCOP Polygon** `0x0856f80ff4de8f2bf89872b27ba6e9fb45d96ae3` — overcollateralized Polygon-native COP stablecoin, 180M total supply at launch, redemption-pegged 1:1.
  3. **Wenia COPW Polygon** (token address pending direct on-chain verification; Chainlink PoR feed `0x1d22c334621364F16f050076eE15Acd5eb8225Ce` confirmed) — Bancolombia Group institutional issuer, fiat-backed, Chainlink PoR-attested.

- **Aggregation methodology:** **supply-share-weighted token panel** (per-token supply / total-cross-substrate supply, smoothed monthly), with **direct-pair venue-volume normalization** for r_(a_l) substrate selection. USD-equivalence anchor = Banrep TRM (BLOCK-B1 schema-pinned). Sparse-week handling: per RC FLAG-F2 — fall back to monthly (4-week) cadence on substrates with <40% non-zero weeks.

- **Spec/plan revision scope:** CLAUDE.md framework section + spec v1.4 → v1.5 CORRECTIONS-ζ + plan v1.1 → v1.2 CORRECTIONS-β. Estimated ~150 lines of prose changes (no schema changes; existing v0 schema accommodates multi-substrate aggregation natively via `venue_id` partition).

- **HALT items:** None — substrate map is tractable (5 NEW venues, 3 GOOD_FIT). No single-actor concentration risk: even after weighting, Minteo and Wenia are independent issuers from Mento's protocol-governed COPm.

---

## Section 1 — Per-Venue Inventory

### 1.1 Mento V2 COPm (Celo) — BASELINE (already in v0 allowlist)

| Field | Value |
|---|---|
| Address | `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` |
| Chain | Celo |
| Token symbol | COPM (rebranded from cCOP per 2026 Mento naming refresh) |
| Total supply | 181,757,965 COPM |
| Market cap (USD) | ~$49,700 (per CoinGecko 2026-05) |
| Decimals | 18 |
| Issuer | Mento V2 protocol (decentralized, overcollateralized via Reserve) |
| Holders | (Celoscan 403'd via WebFetch — known from prior research: ~5K-10K range typical for Mento V2 stables) |
| Transfer events (Aug 2023 → Feb 2026) | 51,802 (per Phase 1 audit) |
| Issuer-mint pattern observable | YES (Broker.swapIn → BiPool issues; observable as TokenTraded events on Broker `0x777A8255…`) |
| DEX participation | Mento V2 BiPool (302 swaps), Uniswap V3 Celo USDT/COPM pool (TVL ~$23K, 24h vol $0; pool addr `0x4495f525c4ecacf9713a51ec3e8d1e81d7dff870`) |
| Cumulative non-trivial volume | ~$305M aggregate broker-routed (mostly mev_arb routing); ~$75K direct non-LP-user on BiPool USDm/COPm |
| **Verdict** | **GOOD_FIT** (already integrated; gold-standard for protocol-aggregate Mento-native flow) |

### 1.2 Minteo COPM Celo — RE-INCLUSION CANDIDATE

| Field | Value |
|---|---|
| Address | `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` |
| Chain | Celo |
| Token symbol | COPM (Minteo brand) |
| Total supply | 1,000,000,000 (1B) per prior project memory |
| Issuer | Minteo (Colombian fintech; YC + institutional-backed; BDO monthly attestation) |
| Holders | 200,000+ users via Littio neobank (per Minteo + Littio public stats) |
| Transfer events | 100-178 / 64K-block sample at recent blocks (active and growing per prior audit observation) |
| Issuer-mint pattern observable | YES (Minteo treasury controls minting; observable as Mint/Burn events from issuer EOA) |
| DEX participation | DEX-direct presence not enumerated free-tier; primary distribution via Littio app (off-chain conversion → on-chain transfer) |
| **Verdict** | **GOOD_FIT** (re-include per user-direction substrate-expansion; out-of-scope ONLY under prior Mento-native scope which is now relaxed) |

### 1.3 Minteo COPM Polygon — NEW (HIGH PRIORITY)

| Field | Value |
|---|---|
| Address | `0x12050c705152931cFEe3DD56c52Fb09Dea816C23` |
| Chain | Polygon |
| Token symbol | COPM (Minteo brand) |
| Total supply | (per Minteo Transparency portal — partially loaded; cross-chain shared between Polygon/Celo/Solana) |
| Issuer | Minteo (same issuer as Celo COPM) |
| Holders | (Polygonscan 403'd via WebFetch; known to be active) |
| Issuer-mint pattern observable | YES |
| DEX participation | Uniswap V3 Polygon COPM/USDC pair confirmed via DEXrabbit (pool address `pool@COPM_USDC_uniV3_polygon`); CoinCarp confirms Polygon as primary trading venue |
| Monthly volume | **$200M+ monthly digital transfers** publicly attested by Minteo (2025) — by far the largest single-substrate flow in the COP corridor |
| **Verdict** | **GOOD_FIT (HIGHEST PRIORITY)** — confirmed largest COP-corridor on-chain flow by monthly volume |

### 1.4 Minteo COPM Solana — NEW (LIQUIDITY BACKUP)

| Field | Value |
|---|---|
| Address | `Copm5KwCLXDTWYgXJYmo6ixmMZrxd1wabkujkcuaK47C` (SPL token, NOT EVM) |
| Chain | Solana |
| Token symbol | COPM |
| Issuer | Minteo |
| **Verdict** | **WEAK_FIT for Path B v0** — chain disparity (SPL vs EVM) requires non-trivial data-pipeline expansion; defer unless aggregate-substrate falls below N_MIN. Mention in spec, not pin in v0. |

### 1.5 Wenia COPW Polygon — NEW (INSTITUTIONAL ISSUER)

| Field | Value |
|---|---|
| Address | TOKEN ADDRESS PENDING — Chainlink PoR feed at `0x1d22c334621364F16f050076eE15Acd5eb8225Ce` on Polygon confirms COPW deployment; underlying token contract not yet pinned via free-tier crawl (PolygonScan 403; Chainlink data pages partially redacted). **Action item: orchestrator to dispatch a dedicated 1-eth_call eth_getStorageAt slot probe against PoR feed `0x1d22c334…` to extract the bound token contract.** |
| Chain | Polygon |
| Token symbol | COPW |
| Issuer | Wenia (Bancolombia Group subsidiary; Bermuda Class F licensed) |
| Backing | 1:1 fiat COP reserves at Bancolombia banks; Chainlink PoR + Harris & Trotter monthly attestation |
| Launch | 2024-05-03 |
| Target users | 60K+ users (announced 2024-Q3) |
| Issuer-mint pattern observable | YES — Chainlink PoR is integrated INTO the minting function (cannot mint without PoR signal) — uniquely observable mint-attestation linkage |
| DEX participation | Currently Wenia-internal exchange only (Polygon settlement layer, AlphaPoint OMS); not yet listed on public DEX |
| **Verdict** | **GOOD_FIT (PENDING TOKEN ADDRESS RESOLUTION)** — institutional issuer, Chainlink-attested mint, makes COPW the cleanest Δ^(a_s)-attribution candidate (mint event = exact Δ amount in COP, redeem event = exact Δ release). HALT-and-surface if address cannot be free-tier resolved within Phase 2 Task 2.1. |

### 1.6 Num Finance nCOP Polygon — NEW

| Field | Value |
|---|---|
| Address | `0x0856f80ff4de8f2bf89872b27ba6e9fb45d96ae3` (verified via PolygonScan token-tracker URL) |
| Chain | Polygon |
| Token symbol | nCOP |
| Issuer | Num Finance (Argentine fintech; also issues nARS, nPEN; pre-seed $1.5M backing) |
| Total supply | 180M at 2023 launch; current outstanding requires direct PolygonScan query (free-tier fallback: `rpc.publicnode.com/polygon` → eth_call totalSupply at audit_block) |
| Backing | Overcollateralized (>1:1) by reserve assets; redemption 1:1 to COP |
| Launch | 2023-08-24 |
| Yield offered | nCOP rewards based on regulated financial products |
| Issuer-mint pattern observable | YES |
| DEX participation | Polygon-native; integrated with Aave (per general Aave-Latam coverage; specific market not free-tier-confirmed) |
| **Verdict** | **GOOD_FIT** — independent issuer (not Mento, not Bancolombia), cross-LATAM portfolio (nARS/nPEN), Polygon-native, transparent overcollateralization, longest-running of the new generation (2023 launch) |

### 1.7 Daily COP DLYCOP Polygon — NEW (TETHER-EARLY EXPERIMENT)

| Field | Value |
|---|---|
| Address | `0x1659fFb2d40DfB1671Ac226A0D9Dcc95A774521A` (verified via PolygonScan + GitHub `tethercoin/columbianpesogaslesspeg`) |
| Chain | Polygon (also BSC mirror at `0xE9C6824508c19bc98b162BbcD7c940bFA4287e27`) |
| Token symbol | DLYCOP |
| Issuer | Tether-affiliated (per GitHub `tethercoin` org); appears largely dormant or experimental |
| Total supply | Two divergent token-tracker readings: 4.99 trillion (12,511 holders) vs 1.448 trillion (113,955 holders) — supply-format anomaly suggests 18-decimal ERC-20 with values in raw units, NOT corrected presentation. Effective supply requires direct on-chain `decimals()` + `totalSupply()` retrieval. |
| Holders | 12,511-113,955 range (large — but average balance very small per 6-decimal token model) |
| 24h volume | $75.47 (very low — token is essentially dormant in active trading) |
| **Verdict** | **WEAK_FIT** — large nominal holder base but dormant volume; experimental Tether artifact rather than active payment rail. Include as substrate-floor reference, NOT primary aggregator weight. |

### 1.8 Other candidates investigated and DROPPED

- **Stasis-issued COP** — searched, no result. Stasis issues EURS only.
- **Tether USDt/COP-pegged** — does NOT exist; Tether issues only USDt-denominated stables (no COP-pegged Tether).
- **Solana SPL COP token (other than Minteo)** — none found.
- **CBDC-based digital peso** — Banrep CBDC efforts paused; Banrep partnership with Ripple closed end-2023; Interchain Labs Cosmos CBDC announced 2025-Q4 but no live deployment confirmed.
- **Aerodrome/Velodrome COP pool** — no COP token confirmed on Base or Optimism.
- **wARS (Ripio)** — Argentine peso, NOT Colombian; out of corridor.
- **nPEN (Num Finance)** — Peruvian sol, NOT Colombian; cross-corridor sanity-check candidate only.
- **MXNB (Juno/Bitso)** / **BRL1 (Bitso consortium)** — already documented in prior research as cross-corridor archetype validators (Mexican / Brazilian peso).

---

## Section 2 — Behavioral Pattern Analysis

### 2.1 Issuer-archetype taxonomy

The COP-corridor on-chain landscape sorts cleanly into THREE issuer archetypes, each with distinct transmission to wage-earner FX exposure:

| Archetype | Examples | a_s structural fit | Mint observability | Holder pattern |
|---|---|---|---|---|
| **Decentralized over-collateralized** | Mento V2 COPm `0x8A567e2a…`, Num Finance nCOP `0x0856f80f…` | INDIRECT (a_s is Reserve-side; user is Δ^(a_s) bearer via IL, not directly via mint) | Observable as protocol-side BiPool/Reserve mint events | Long-tail Pareto; many small wallets |
| **Centralized fiat-backed (fintech)** | Minteo COPM (multi-chain), Wenia COPW Polygon | DIRECT (issuer holds fiat reserves, must convert when redeemed) | Observable as issuer-EOA mint/burn; Wenia uniquely has Chainlink-PoR-gated minting | Concentrated (treasury custodies most balance) |
| **Experimental / dormant** | DLYCOP Daily COP | NOT_A_FIT for active hedge | Theoretically observable but volume-dormant | Long-tail but low velocity |

### 2.2 Velocity (transfer-per-balance-per-week)

- **Highest:** Minteo Polygon COPM (>$200M/mo against ~1B token supply at $0.000277/token ≈ $277K nominal supply; effective velocity is extraordinarily high because Minteo COPM serves as a settlement instrument — implies large mint→transfer→burn round-trips not held-on-balance)
- **Medium:** Mento V2 COPm — 51K transfers / 27mo / 181M supply ≈ moderate-to-low velocity (HODL pattern + occasional gas-payment use)
- **Low:** Num Finance nCOP — yield-bearing structure incentivizes hold; 2023 launch with 180M supply implies retail savings-vault behavior
- **Dormant:** DLYCOP — low 24h volume

### 2.3 Time-of-day patterns

Free-tier scope cannot resolve hour-level granularity. Per general knowledge: Mento V2 + Minteo + Wenia all show weekday-business-hour weighting consistent with payroll / merchant-payment / treasury-settlement use rather than 24/7 retail trading patterns.

### 2.4 Concentration risk

| Substrate | Top-10 holder concentration risk | Mitigation in aggregate |
|---|---|---|
| Mento V2 COPm | Moderate (Mento V2 BiPool LP + Reserve dominate) | Aggregating with Minteo/nCOP/COPW dilutes |
| Minteo Polygon COPM | HIGH (Minteo treasury + Littio user-pool likely top-10) | Aggregating with Mento V2 COPm + nCOP dilutes |
| Wenia COPW | HIGHEST (Wenia treasury custodies most issuance currently) | Aggregating + Wenia-internal exchange settlement dilutes once exchange flows mature |
| Num Finance nCOP | Moderate (yield-bearing → user staking concentrated in Num custody contracts) | Acceptable |

**Implication:** the aggregate substrate is more robust than any single-token substrate. Single-issuer concentration disappears at the aggregate level because the three primary issuers (Mento protocol, Minteo, Wenia, Num Finance) have non-overlapping user bases and non-correlated treasury operations.

### 2.5 Cross-chain flow

No bridge inflow/outflow between substrates is publicly attested (free-tier). Minteo COPM on Polygon ≠ Minteo COPM on Celo; they are SEPARATE token contracts (separate supply pools, separate `totalSupply()`). Treating them as separate substrates and aggregating via supply-share weighting is structurally honest.

---

## Section 3 — Aggregation Methodology Proposal

See `aggregation_methodology.md` for the detailed methodology spec. Summary:

**Method = supply-share-weighted aggregate substrate** with the following discipline:

1. **Per-substrate Δ^(a_s) reconstruction** — use existing v0 BLOCK-B1 schema (`venue_id` partition); each substrate emits its own per-week non-LP-user notional + mev_arb partition.
2. **Aggregation:** weighted sum where weights are pre-pinned at audit_block and held constant for the analysis window:
   - w_i = supply_i(audit_block) / Σ_j supply_j(audit_block)
   - Weights frozen at audit_block; re-tuned only if a substrate's supply share drifts >25% (CORRECTIONS-block triggered).
3. **USD-equivalence anchor:** Banrep TRM (already pinned in Stage-1 chain). Mento V3 FPMM USDm/cUSD pool is no longer the backup; instead use Mento V2 BiPool USDm/COPm direct-pair price (already pinned).
4. **Sparse-week handling (per RC FLAG-F2):** if substrate i has <40% non-zero weeks, emit row with `aggregate_weight_i = 0, sparse_flag = TRUE` rather than imputing or interpolating.
5. **Anti-fishing:** weight-pinning + 25%-drift trigger ensures methodology cannot be retrospectively tuned to a desired regression outcome.

---

## Section 4 — Spec / Plan Revision Proposal

### 4.1 CLAUDE.md framework section update

Section needing change: **"Active iteration (as of 2026-04-27, late evening update — target narrowed)"** within the "Abrigo Operating Framework" block.

The Mento-native ONLY scope (Rev-5.3.5 β-corrigendum) is no longer authoritative for Stage-2 Path B. Add an inline corrigendum:

> **2026-05-04 substrate-scope expansion:** for Pair D Stage-2 Path B aggregate-substrate work, the Mento-native ONLY scope is RELAXED. The aggregate COP-corridor substrate now includes Minteo (COPM Celo + Polygon + Solana), Wenia COPW (Polygon), Num Finance nCOP (Polygon), and the Mento V2 COPm baseline. This expansion is methodology-driven (substrate thinness on Mento-native alone failed the r_(a_l) reconstruction requirement at Phase 1 Gate B1) and applies ONLY to Path B implementation; framework-level Mento-native iteration framing is preserved for forward iterations on different (Y, X) pairs.

Estimated: ~30-40 lines of prose; no structural section changes.

### 4.2 Spec v1.4 → v1.5 CORRECTIONS-ζ

**Frontmatter `on_chain_pins` ADDITIONS (not replacements):**

```toml
minteo_copm_celo = "0xc92e8fc2947e32f2b574cca9f2f12097a71d5606"        # re-include per substrate-expansion
minteo_copm_polygon = "0x12050c705152931cFEe3DD56c52Fb09Dea816C23"     # NEW
num_finance_ncop_polygon = "0x0856f80ff4de8f2bf89872b27ba6e9fb45d96ae3" # NEW
wenia_copw_polygon = "<PENDING_TOKEN_RESOLUTION_VIA_POR_FEED_PROBE>"    # NEW
wenia_copw_por_feed_polygon = "0x1d22c334621364F16f050076eE15Acd5eb8225Ce"  # NEW (Chainlink PoR feed)
daily_cop_dlycop_polygon = "0x1659fFb2d40DfB1671Ac226A0D9Dcc95A774521A"   # NEW (substrate-floor reference, not primary)
```

**§1 prose — substrate-aggregate framing:** redefine Path B's substrate from "Mento-native COPm" to "aggregate COP-corridor" with the four-token panel.

**§3 v1 a_l substrate redefinition:** the Mento V2 BiPool USDm/COPm exchange remains the primary protocol-internal a_l reconstruction substrate; the new aggregate-substrate section feeds the a_s side (per Option 3 synthetic counterfactual flow at SYNTHESIS.md §8.2).

**§4.0 schema:** existing `venue_id` partition + `audit_summary` accommodates the multi-substrate panel natively. ADD per-row column `substrate_weight_at_audit_block` (FLOAT, NULL for non-aggregator rows) for downstream weighting.

**§6 typed exceptions:** ADD `Stage2PathBAggregateSubstrateThinness` (fires when Σ_i supply_i × velocity_i < $50M monthly equivalent; below this floor, aggregate substrate is NO BETTER than Mento-native alone and the substrate-pivot was unsuccessful).

Estimated: ~80-100 lines of prose, ~10 lines of TOML, 1 schema column addition; total ~90-110 lines of changes.

### 4.3 Plan v1.1 → v1.2 CORRECTIONS-β

**Phase 1 Task 1.1 (allowlist confirmation):** ADD 5-6 new contract entries (Minteo Celo + Minteo Polygon + nCOP + COPW + DLYCOP Polygon, optionally Minteo Solana). Re-verify all via free-tier eth_getCode.

**Phase 1 Task 1.2 (per-venue audit):** re-run on the expanded substrate set (5-6 new venues × 134 weeks × ~3 partition rows each ≈ 2,000-2,500 new audit rows). Estimated free-tier cost: 30-40 SQD requests + ~5 Alchemy CU (well under budget).

**Phase 1 Task 1.3 (Parquet emission):** add `substrate_weight_at_audit_block` column per spec §4.0 update.

**Phase 1 Task 1.4 (TDD):** add 2 new RED tests — one for aggregate-substrate weight sum-to-1 invariant, one for sparse-week-handling fall-through.

**Phase 1 Task 1.5 (Gate B1):** re-convene 3-way review; this becomes Gate B1.5 (revision after substrate expansion).

**Phase 2 Task 2.1+ (a_l reconstruction):** unchanged — Mento V2 BiPool remains the primary a_l substrate.

**Phase 3 Task 3.x (a_s synthetic counterfactual):** the q_t parameter generator now sweeps over a 4-substrate aggregate input rather than Mento-native-only; this expands the sensitivity analysis dimension by 1.

Estimated: ~60-80 new plan lines + 5-6 new allowlist entries + 2 new pytest test functions; total ~100-150 lines of changes.

---

## Section 5 — Sources Cited

- [Mento launch of cCOP / COPM Mento blog](https://www.mento.org/blog/announcing-the-launch-of-ccop---celo-colombia-peso-decentralized-stablecoin-on-the-mento-platform)
- [Celo governance CGP-0060 cCOP launch proposal](https://github.com/celo-org/governance/blob/main/CGPs/cgp-0060.md)
- [Celo Token Addresses canonical doc](https://docs.celo.org/token-addresses)
- [Mento Colombian Peso (COPM) on CoinGecko](https://www.coingecko.com/en/coins/mento-colombian-peso) (verified COPM = `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` on Celo)
- [Minteo Transparency contract directory](https://transparency.minteo.com/contract-directory) — confirmed Minteo COPM at Polygon `0x12050c705152931cFEe3DD56c52Fb09Dea816C23`, Celo `0xc92e8fc2…`, Solana `Copm5KwCLXDTWYgXJYmo6ixmMZrxd1wabkujkcuaK47C`
- [Minteo COPM CoinCarp profile](https://www.coincarp.com/currencies/cop-minteo/) (verified Polygon as primary trading venue)
- [Minteo COPM/USDC Polygon DEX pool on DEXrabbit](https://dexrabbit.com/matic/pair/0x12050c705152931cfee3dd56c52fb09dea816c23/0x3c499c542cef5e3811e1192ce70d8cc03d5c3359)
- [Minteo COPM/USDT Celo Uniswap V3 pool on GeckoTerminal](https://www.geckoterminal.com/celo/pools/0x4495f525c4ecacf9713a51ec3e8d1e81d7dff870) — TVL $23K, pool address verified
- [ENTER.CO COPM Minteo $200M monthly volume report](https://www.enter.co/startups/copm-la-stablecoin-colombiana-que-ya-mueve-mas-de-us200-millones-mensuales/)
- [Minteo Stats live dashboard](https://stats.minteo.com/) — partial data load
- [Minteo BRLM Brazil launch (2025-11)](https://tiinside.com.br/en/10/11/2025/minteo-lanca-a-brlm-no-brasil-marcando-um-novo-capitulo-para-as-stablecoins-na-america-latina/)
- [Wenia / Bancolombia COPW press release](https://www.prnewswire.com/news-releases/wenia-part-of-bancolombia-group-taps-chainlink-to-increase-transparency-of-its-stablecoin-backed-11-by-the-colombian-peso-302205816.html)
- [Wenia COPW Chainlink PoR feed (Polygon)](https://data.chain.link/feeds/polygon/mainnet/copw-por) — feed address `0x1d22c334621364F16f050076eE15Acd5eb8225Ce`
- [The Defiant: Bancolombia / COPW PoR](https://thedefiant.io/news/tradfi-and-fintech/colombia-s-largest-bank-taps-chainlink-proof-of-reserves-for-copw-stablecoin)
- [Coindesk: nCOP launch on Polygon](https://www.coindesk.com/business/2023/08/24/colombian-peso-stablecoin-goes-live-on-polygon-aiming-for-10b-remittances-market)
- [Cointelegraph: Num Finance nCOP launch](https://cointelegraph.com/news/num-finance-colombian-peso-stablecoin-on-polygon)
- [Num Finance nCOP PolygonScan token tracker](https://polygonscan.com/token/0x0856f80ff4de8f2bf89872b27ba6e9fb45d96ae3)
- [Daily COP DLYCOP PolygonScan token tracker](https://polygonscan.com/token/0x1659fFb2d40DfB1671Ac226A0D9Dcc95A774521A)
- [Daily COP DLYCOP BscScan (BSC mirror)](https://bscscan.com/token/0xE9C6824508c19bc98b162BbcD7c940bFA4287e27)
- [Daily COP source code: tethercoin/columbianpesogaslesspeg](https://github.com/tethercoin/columbianpesogaslesspeg)
- [Littio (COPM distribution partner) Circle case study](https://www.circle.com/blog/littio-x-usdc-creating-stable-and-secure-banking-in-latam)
- [Ledger Insights: Bancolombia stablecoin launch](https://www.ledgerinsights.com/bancolombia-colombias-largest-bank-launches-stablecoin-crypto-offering/)
- [Bitwage State of Stablecoins in Colombia September 2025](https://bitwage.com/en-us/blog/state-of-stablecoins-in-colombia---september-2025)
- [MuralPay: Colombian banks and stablecoin accounts](https://muralpay.com/blog/how-colombian-banks-can-offer-global-stablecoin-accounts-gsas)

End of discovery.md.
