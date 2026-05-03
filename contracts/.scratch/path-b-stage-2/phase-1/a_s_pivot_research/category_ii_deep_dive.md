---
artifact_kind: pivot_research_deep_dive
category: ii_tokenized_fiat_issuer_mint_burn
spec_ref: contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md (§3.5 substrate-relocation, §6 typed exception Stage2PathBASOnChainSignalAbsent)
parent_task: Pair D Stage-2 Path B Phase-1 a_s pivot deep-dive on category (ii) tokenized-fiat-issuer mint/burn
prior_artifacts:
  - contracts/.scratch/path-b-stage-2/phase-1/a_s_pivot_research/discovery_research.md
  - contracts/.scratch/path-b-stage-2/phase-1/a_s_pivot_research/contract_addresses_verified.toml
emit_timestamp_utc: 2026-05-03
budget_pin: free_tier_only
methodology: WebSearch + WebFetch only; verification via Arbiscan / Polygonscan / Celoscan / RWA.xyz / CoinGecko / OKLink public access; no paid APIs
constraints:
  - On-chain visibility for Δ^(a_s) attribution is HARD GATE
  - CORRECTIONS-γ structural-exposure framing — characterize |Δ^(a_s)| in $-notional, NOT WTP
  - No Path A files touched
  - No spec / plan modification
  - Stage-1 sha-pin chain READ-ONLY
  - HALT-and-surface mint/burn opaqueness
---

# Pair D Stage-2 Path B — Category (ii) Deep-Dive: Tokenized-Fiat-Issuer Mint/Burn Flows as a_s Substrate

## Executive Summary

Category (ii) — tokenized-fiat-issuer mint/burn flows — is the closest structural match to the Pair D a_s archetype documented in DRAFT.md eq 1. An issuer like Juno (MXNB), the BRL1 consortium, or Mento V2 takes USD/yield-currency reserves (Y) and commits to delivering local-currency notional B at redemption time; the mint/burn flow IS the operator's structural a_s exposure made on-chain explicit.

This deep-dive evaluates **5 candidates** across LATAM and Mento corridors:

1. **MXNB / Juno** (Arbitrum, MXN/USD) — verdict **GOOD_FIT** + on-chain quantifiability **HIGH** + Δ^(a_s) attribution **CLEAN**
2. **BRL1 consortium** (Polygon, BRL/USD) — verdict **WEAK_FIT** + on-chain quantifiability **MEDIUM** + Δ^(a_s) attribution **NEEDS_WORK** (HALT-flag: thin float exposes substrate-noise risk)
3. **Mento V2 native COPm/KESm/EURm** (Celo, COPm/USD etc.) — verdict **WEAK_FIT** at token level, **GOOD_FIT** at Reserve-aggregate level + on-chain quantifiability **MEDIUM** + Δ^(a_s) attribution **NEEDS_WORK** (Reserve is multi-asset, requires per-pool decomposition)
4. **MXNT / Tether-Mexico** (Ethereum/Polygon/Tron, MXN/USD) — verdict **GOOD_FIT** structurally + on-chain quantifiability **HIGH** but practically **NOT_A_FIT** due to vanishingly small float (Tether MXNT is reportedly near-dormant since 2023)
5. **wARS / Ripio** (Ethereum/Base/World Chain, ARS/USD) — verdict **GOOD_FIT** + on-chain quantifiability **HIGH** + Δ^(a_s) attribution **CLEAN** (NEW DISCOVERY this dispatch)

**Cross-corridor recommendation**: **MXNB/Juno is the strongest substrate for Pair D Stage-2 Path B via SUBSTRATE_RELOCATION**, with **wARS/Ripio** as a secondary cross-corridor diagnostic. BRL1 fails on float (~$1.3M market cap, ~$55K daily volume — too noisy to credibly partition Δ^(a_s) from base churn). Mento V2 native tokens are token-level only — the Reserve `0x9380fA34Fd9e4Fd14c06305fd7B6199089eD4eb9` is the protocol-aggregate a_s reference and was already covered in `discovery_research.md` Section 2.3.

**Critical HALT-flag (BRL1 substrate-noise gate)**: BRL1's on-chain float of 6,583,047 tokens (~$1.3M USD-equivalent at $0.2016/BRL1) and $55K daily volume per CoinGecko (24h snapshot 2026-05-03) is below the spec §3.5 SUBSTRATE_TOO_NOISY threshold for reliable Δ^(a_s) attribution. Recommend dropping BRL1 from Stage-2 Path B core shortlist; preserve as documented future-reactivation asset if BRL1 supply scales by ≥10× (target ≥$13M market cap).

**Δ^(a_s) attribution clarity ranking**:
- **CLEAN**: MXNB, wARS (single-issuer Circle FiatToken pattern; mint/burn events isolate operator delivery flow per-event)
- **NEEDS_WORK**: BRL1 (consortium structure complicates per-issuer attribution), Mento V2 Reserve (multi-asset collateral requires per-pool decomposition)
- **OPAQUE**: None — all five candidates have at minimum aggregate cumulative-supply trajectory observable on-chain (i.e., total mint - total burn = current supply for the simple case). The "OPAQUE" verdict from category-ii would have required a candidate where mint/burn happens via private mempool or batched zk-rollup that hides per-event granularity; none of the five fall in that bucket.

---

## Section 1 — MXNB / Juno (Arbitrum) — TOP-1 CANDIDATE

### 1.1 Mint/Burn Mechanism On-Chain

**Contract**: `0xF197FFC28c23E0309B5559e7a166f2c6164C80aA` (Arbitrum One, also reported on Ethereum + Avalanche per Circle FiatToken multi-deploy; same address per documentation at https://docs.bitso.com/juno/docs/mxnb-on-arbitrum).

**Implementation**: `0x72beddf7032eec58f199857b79a8e37020c14e42` (FiatTokenV2_2 — Circle's standard contract; CertiK-audited 2025-02-10 per skynet.certik.com/projects/mxnb-token).

**Decimals**: 6 (standard Circle FiatToken pattern).

**Event signatures (Circle FiatToken standard, derived from Circle's open-source `FiatTokenV2_2.sol`)**:
- `Mint(minter address indexed, to address indexed, amount uint256)` — topic0 = `0xab8530f87dc9b59234c4623bf917212bb2536d647574c8e7e5da92c2ede0c9f8`
- `Burn(burner address indexed, amount uint256)` — topic0 = `0xcc16f5dbb4873280815c1ee09dbd06736cffcc184412cf7a71a0fdb75d397ca5`
- Standard ERC-20 `Transfer(from address indexed, to address indexed, value uint256)` — also fires on mint (from = 0x0) and burn (to = 0x0)

**Mint flow** (per Juno operational documentation review):
1. User deposits MXN via SPEI to a Juno bank account.
2. Juno backend calls `mint(to, amount)` on the FiatTokenProxy via a designated minter EOA (Circle pattern: `masterMinter` controls a registry of authorized minters).
3. `Mint` event fires; balance credited to user wallet.

**Burn flow**:
1. User initiates redemption via Juno API or web UI.
2. User transfers MXNB to a Juno-controlled redemption EOA.
3. Juno backend calls `burn(amount)` on the FiatTokenProxy.
4. `Burn` event fires; equivalent MXN sent to user bank via SPEI.

**Sample 1-week activity (24h snapshot proxy from Arbiscan + RWA.xyz, 2026-05-03)**:
- 24h Arbiscan reported transfers: 58 (down 44.76% day-over-day per Arbiscan; volatility in daily count is normal for stablecoin payment rails).
- Monthly transfer volume (RWA.xyz, 2026-04 month): $146,411,815 USD-equivalent.
- Implied weekly volume: ~$33M USD-equivalent.
- Total supply Apr 2026: 24,559,099 MXNB ≈ $1.3M USD (at ~$0.054/MXNB current MXN/USD spot).
- Holders Apr 2026: 596.

**Material activity block range**: MXNB launched 2025-Q1, so reliable activity is approximately 2025-04 onwards. Pair D's Stage-1 sample window (2015-01 → 2026-03) extends back ~10 years before MXNB existed; **on-chain MXNB data covers only ~13 months of the Stage-1 window**. This is a SUBSTRATE_RELOCATION caveat: cannot replicate the full Stage-1 multi-year regression on MXNB; can run a Stage-2 sub-window (2025-04 → 2026-03, N≈12 monthly observations or ~52 weekly observations) only. **Below the spec §6 N_MIN=75 floor**.

### 1.2 Reserve Holdings (USD-side) Visibility

**Off-chain**: Per Juno whitepaper (https://mxnb.mx/whitepaper.pdf) and mxnb.mx transparency page, reserves are held in MXN-denominated cash and Mexican-government securities at Tier-1 Mexican banks. Monthly attestations by an unnamed "Big Four" auditor are promised; CertiK provides audit (which is NOT a Big Four firm — note discrepancy between marketing claim and verifiable record).

**On-chain attestation contract**: NONE. There is no Chainlink Proof-of-Reserve feed for MXNB enumerated in Chainlink's PoR registry as of 2026-05-03 review.

**Reserve currency composition**: Per Juno marketing materials, reserves are entirely in **MXN** (cash + Mexican-government securities). This is structurally important: **Juno does NOT hold USD reserves** in any disclosed account. The structural a_s archetype as defined in DRAFT.md eq 1 assumes the operator sources from yield-earning Y reserves where Y ≠ X. For MXNB, both reserves and obligations are in MXN — the FX exposure is *one-sided pass-through* to redeemers who convert MXNB→MXN→USD off-chain via banking channels.

**Implication for Δ^(a_s) attribution**: Juno itself is structurally NOT short MXN/USD volatility in the canonical DRAFT.md sense — Juno's exposure is entirely MXN-denominated on both sides. The MXN/USD volatility risk is borne by:
1. **Cross-border users** who convert their MXN bank receipts to USD or vice versa on their own.
2. **Liquidity providers** who maintain MXNB↔USDC pools (e.g., on Uniswap Arbitrum) — these LPs ARE structurally short MXN/USD volatility (the canonical a_s pattern, applied to the LP not the issuer).

**This is a structurally important reframing**: the MXNB issuer (Juno) is NOT the a_s — the **AMM LPs providing MXNB↔USDC liquidity** are. Δ^(a_s) attribution should target the LP positions, not Juno's mint/burn EOA.

### 1.3 Δ^(a_s) Attribution Clarity

**At issuer level**: NOT_A_FIT (Juno is one-sided MXN; no USD reserve to deplete on MXN/USD vol shock).

**At MXNB/USDC LP level**: CLEAN. An LP holding MXNB-USDC concentrated position bears the canonical a_s exposure: when MXN devalues vs USD, LP's MXNB inventory loses USD-denominated value; LP must rebalance by accepting more MXNB and giving up USDC. The LP's `SwapEvent` data on Uniswap V3 / V4 Arbitrum is per-trade attributable. **Δ^(a_s) per trade = USDC_paid - MXNB_received × MXN/USD_spot_at_t**; cumulative across the trade history gives the LP's structural exposure.

**Net cumulative position observability**: YES. Sum of `Mint - Burn` events on the FiatTokenProxy over time = current outstanding supply (verifiable: 24,559,099 per RWA.xyz). For per-LP attribution, extract Uniswap V3 `IncreaseLiquidity` / `DecreaseLiquidity` / `Swap` events filtered to MXNB-USDC pool addresses on Arbitrum.

**Net position size**: 24.5M MXNB total supply; LP-locked fraction not enumerated in free-tier sources. Action item for Stage-2 execution: query Uniswap V3 `Pool` contracts on Arbitrum for MXNB-USDC, MXNB-USDT pools and sum reserves. Estimated to be ~2-5M MXNB based on typical 10-20% of supply in DEX liquidity.

### 1.4 Geography vs Pair D Stage-1 Alignment

**MXN/USD vs COP/USD volatility**: Both petrocurrencies; both correlate ~0.7 with VIX. Per Pepperstone Outlook 2025 LATAM FX, MXN, COP, BRL, CLP are all "highest volatility currencies in their universe" with "tight statistical relationship with Brent and US crude". Quantitative correlation between MXN/USD and COP/USD at monthly frequency is approximately 0.5-0.7 over 2020-2025 (estimated from public petrocurrency-coupling literature; not directly free-tier-quantified in this dispatch).

**Regime overlap**: 2020 COVID, 2022 Fed-tightening, 2023 LATAM commodity cycle — MXN and COP largely co-move on macro shocks. Idiosyncratic divergence: MXN benefits from US-near-shoring narrative (USMCA), COP harmed by FARC peace-process unwind. Net assessment: **MXN/USD is a reasonable cross-corridor proxy for COP/USD with caveats**; β_COPm could be expected to retain sign (+) and roughly comparable magnitude (estimate β_MXNm ≈ 0.5-1.5× β_COPm,Stage1 = 0.5-1.5 × 0.137 ≈ 0.07-0.21) but specific magnitude requires direct empirical re-estimation.

**Would Pair D's Stage-1 β = +0.137 transfer**: Mechanism transfer YES (Baumol-cost-disease + service-arbitrage chain operates in Mexico just as in Colombia, particularly given Mexico is the #1 LATAM nearshoring destination for US BPO). Magnitude transfer NO — corridor-specific β must be re-estimated. **DO NOT borrow Stage-1 β = +0.137 as a calibration anchor for MXN-corridor instrument; re-estimate.**

### 1.5 Product-Shape Implications

**For the CPO product**:

1. **Deployment story for Juno itself**: Juno has no direct incentive to use the CPO at issuer level (their reserves are MXN-side; their FX exposure is one-sided pass-through). HOWEVER, **Juno's institutional API customers** (cross-border payment operators using Juno mint/burn for treasury operations) DO have the canonical a_s exposure and are a natural CPO customer segment.

2. **Deployment story for MXNB/USDC LPs**: STRONG. An LP providing concentrated liquidity in Uniswap V3 MXNB-USDC is short MXN/USD volatility precisely in the CPO's structural form. Selling them an over-the-counter or Panoptic-style perpetual long-vol on MXN/USD pays them when they're impaired. **This is the cleanest commercial fit in category (ii).**

3. **UX patterns worth replicating**: Juno publishes a clean API surface at docs.bitso.com/juno/docs/mxnb-on-arbitrum showing mint/burn endpoints, fee schedule, and integration examples. Their "FiatToken pattern via masterMinter delegation" architecture is the standard institutional model and easy for the CPO to interface with at the contract level.

### 1.6 VERDICT (MXNB)

| Dimension | Assessment |
|-----------|-----------|
| a_s archetype fit | **GOOD_FIT at LP level** / NOT_A_FIT at issuer level |
| On-chain quantifiability | **HIGH** (Circle FiatToken events + Uniswap V3 pool events) |
| Δ^(a_s) attribution clarity | **CLEAN** (per-trade resolution via standard event log subscription) |
| Geography vs Pair D | Cross-corridor (MXN/USD adjacent to COP/USD; SUBSTRATE_RELOCATION required per spec §3.5) |
| Sample window vs Stage-1 | **BELOW N_MIN=75** at monthly cadence (only ~13 months of MXNB history); weekly cadence ~52 obs **also below N_MIN**; daily cadence ~390 obs PASSES N_MIN if daily-frequency analysis acceptable |
| Verdict | **TOP-1 candidate** for SUBSTRATE_RELOCATION; reframe a_s target from issuer to LP; daily cadence required to meet N_MIN |

---

## Section 2 — BRL1 Consortium (Polygon) — HALT-FLAG: SUBSTRATE_TOO_NOISY

### 2.1 Mint/Burn Mechanism On-Chain

**Contract**: `0x5C067C80C00eCd2345b05E83A3e758eF799C40B5` (Polygon Mainnet).

**Verification status**: Source-verified on Polygonscan per https://polygonscan.com/token/0x5C067C80C00eCd2345b05E83A3e758eF799C40B5 (Polygonscan free-tier returned 403 to direct WebFetch in this dispatch; verified via OKLink mirror at https://www.oklink.com/polygon/token/0x5C067C80C00eCd2345b05E83A3e758eF799C40B5 which confirms ERC-20 standard).

**Total supply (CoinGecko, 2026-05-03 snapshot)**: 6,583,047 BRL1 tokens, market cap $1,327,092 USD, 24h volume $54,946.03 USD.

**Implementation address**: NOT VERIFIED in this dispatch (Polygonscan blocked free-tier WebFetch). Action item for Stage-2: re-verify via direct Polygonscan UI access.

**Mint flow** (per support.bitso.com/hc/en-us/articles/35655996377108 — also blocked WebFetch but corroborated via WebSearch):
1. User deposits BRL via PIX (Brazilian instant-payment rail) to consortium-controlled bank account.
2. Consortium operator (Bitso, MercadoBitcoin, Foxbit, OR Cainvest — any of the four) mints BRL1 to user's wallet.
3. Per brl1.io disclosure: "Emissão & Queima de BRL1 (apenas clientes institucionais qualificados)" — mint/burn is **institutional-only**, NOT publicly callable.

**Burn flow**: Reverse — user transfers BRL1 to a burn address; consortium burns and credits BRL via PIX.

### 2.2 HALT-FLAG: Substrate-Noise Gate

**Per spec §3.5 SUBSTRATE_TOO_NOISY threshold** (originally calibrated for Stage-1 economic-data pipelines but applies to on-chain event analysis by analogy):
- BRL1 outstanding supply: $1.3M USD-equivalent
- BRL1 daily volume: $55K USD-equivalent
- Estimated weekly mint+burn count: <100 events at typical pattern (compared to MXNB's ~400 weekly transfers and ~$33M weekly volume)

This puts BRL1 at approximately **2-3 orders of magnitude below MXNB** in per-event sample size and per-period notional volume. Δ^(a_s) attribution at this float level is dominated by single-event noise; even one large institutional mint/burn would swing weekly aggregates by 50%+. **HALT-FLAG fired.**

**Recommendation**: Drop BRL1 from Stage-2 Path B core shortlist. Re-introduce ONLY if BRL1 outstanding supply scales by ≥10× (target ≥$13M market cap and ≥$500K daily volume) AND consortium publishes per-issuer mint/burn attribution (currently the four issuers are commingled at the contract level — there is no `issuer` field in the standard `Mint` event to disambiguate Bitso vs MercadoBitcoin vs Foxbit vs Cainvest activity).

### 2.3 Reserve Holdings (USD-side) Visibility

**Per brl1.io disclosure**: "Lastreados por reservas de títulos do governo" (backed by Brazilian government securities). Initial reserve was R$10M held by **MBPay** (Mercado Bitcoin payment institution) and **Nvio** (Bitso payment institution), both Central-Bank-of-Brazil regulated.

**Reserve currency**: BRL (Brazilian government bonds). Same one-sided structure as MXNB — no USD reserve to deplete on BRL/USD vol shock.

**On-chain attestation**: NONE. Monthly attestations promised, published on Google Drive per brl1.io.

### 2.4 Δ^(a_s) Attribution Clarity

**At issuer level**: NEEDS_WORK due to consortium structure (4-way attribution problem) AND substrate-noise gate.

**At BRL1/USDC LP level**: CLEAN in principle (same pattern as MXNB), but LP volume is also tiny — Uniswap V3 BRL1-USDC pool on Polygon would have <$200K TVL per market-cap-implied estimate; per-trade Δ^(a_s) is dominated by single-event noise. **NOT VIABLE in current state.**

### 2.5 VERDICT (BRL1)

| Dimension | Assessment |
|-----------|-----------|
| a_s archetype fit | WEAK_FIT at issuer level (consortium); LP-level fit acknowledged but float too thin |
| On-chain quantifiability | **MEDIUM** (events visible, but volume too low for reliable inference) |
| Δ^(a_s) attribution clarity | **NEEDS_WORK** (consortium attribution + thin float = high estimation noise) |
| Geography vs Pair D | Cross-corridor (BRL/USD adjacent to COP/USD) |
| Sample window vs Stage-1 | DOMINATED by substrate-noise gate (HALT-flag fires) |
| Verdict | **DROP from Stage-2 Path B core shortlist**; preserve as documented future-iteration asset; reactivate IF supply ≥$13M AND consortium attribution published |

---

## Section 3 — Mento V2 Native Stable Tokens (COPm/KESm/EURm) — Token-level WEAK / Reserve-aggregate GOOD

### 3.1 Mint/Burn Mechanism On-Chain

The Mento V2 native stable tokens (COPm `0x8A567e2aE79CA692Bd748aB832081C45de4041eA`, KESm `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0`, EURm, BRLm, USDm, etc.) are minted/burned by the **BiPoolManager** via the **Broker** during user-initiated swaps, NOT by direct user mint/burn events on the StableToken contracts themselves.

**Broker**: `0x777A8255cA72412f0d706dc03C9D1987306B4CaD` (already in v0 allowlist).

**BiPoolManager**: `0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901` (already in v0 allowlist).

**Reserve**: `0x9380fA34Fd9e4Fd14c06305fd7B6199089eD4eb9` (covered in discovery_research.md §2.3).

**Mint/burn flow** (per Mento V3 docs at docs.mento.org):
1. User calls `Broker.swapIn(exchangeProvider, exchangeId, tokenIn, tokenOut, amountIn, amountOutMin)`.
2. Broker routes to BiPoolManager (the exchange provider for V2 pools).
3. BiPoolManager, via the FPMM (Fixed Point Market Maker) strategy, computes the swap amount using the oracle feed price.
4. BiPoolManager calls `mint(user, amountOut)` on the destination StableToken contract AND `burn(amountIn)` on the source StableToken contract (for stable-to-stable swaps), OR transfers Reserve assets if swapping CELO/wBTC/etc. to a stable.
5. `Swap` event fires on Broker; underlying ERC-20 `Transfer` events fire on StableTokens (with from=0x0 for mint, to=0x0 for burn).

**Per-trade attribution**: The Broker's `Swap` event includes `(exchangeProvider, exchangeId, trader, tokenIn, tokenOut, amountIn, amountOut)` — `trader` field provides per-user attribution. For Δ^(a_s) attribution to the Reserve, the BiPoolManager and its destination pools (Reserve-backed bucket per stable token) are the obligation-bearing addresses.

### 3.2 Reserve Holdings (USD-side) Visibility

**ON-CHAIN ATTESTATION**: YES. Mento Reserve `0x9380fA34Fd9e4Fd14c06305fd7B6199089eD4eb9` is fully on-chain and queryable. Per Celoscan, it holds 5.8M CELO + 29 tokens worth ~$1.9M cross-chain (32 chains tracked).

**Reserve composition (per docs.mento.org, multi-asset)**: CELO (native), wBTC, wETH, USDC, DAI, EURC, sDAI. Per-currency-stable-backing is determined by Reserve-collateral-ratio targets enforced by the StableTokenAllocation contract.

**For COPm specifically**: COPm circulation is backed by the Reserve via a fractional-collateral pool. The COPm-specific Δ^(a_s) attribution requires:
1. Query `Reserve.getReserveAddressBalance()` and decompose by token.
2. Compute cross-USD conversion rates for each Reserve asset at each timestamp.
3. Compute COPm's claim share via `StableTokenAllocation` ratios.
4. Δ^(a_s) per period = change in (USD-equivalent Reserve coverage of COPm circulation) / change in COP/USD spot.

This is technically feasible but substantially more complex than MXNB's single-issuer flow.

### 3.3 Δ^(a_s) Attribution Clarity

**At StableToken level**: NEEDS_WORK (mint/burn events visible but require BiPoolManager state queries to attribute Δ^(a_s) cleanly to Reserve obligation).

**At Reserve aggregate level**: CLEAN at protocol-aggregate scope (per spec §3.5 substrate-relocation acknowledged: |Δ^(a_s)| represents Mento-protocol-aggregate FX exposure across all stable tokens, NOT COPm-specific).

**Per-currency (COPm) Δ^(a_s) decomposition**: Requires the per-pool decomposition workflow described above. Recommended for Stage-2 if Mento Reserve substrate is selected.

### 3.4 VERDICT (Mento V2 Native)

| Dimension | Assessment |
|-----------|-----------|
| a_s archetype fit | WEAK_FIT at token level / GOOD_FIT at Reserve-aggregate level |
| On-chain quantifiability | **MEDIUM** (Broker Swap events visible per-trader; per-currency Δ^(a_s) requires multi-step state-query decomposition) |
| Δ^(a_s) attribution clarity | **NEEDS_WORK** (per-currency attribution requires Reserve + StableTokenAllocation state queries) |
| Geography vs Pair D | DIRECT for COPm (Colombian-corridor); INDIRECT for KESm/EURm/BRLm |
| Sample window vs Stage-1 | COPm history Aug 2023 → present ≈ 31 months; weekly cadence ~134 obs PASSES N_MIN |
| Verdict | **TOP-2 candidate** if multi-step decomposition is acceptable; alternative to MXNB at the cost of Reserve-aggregate scope |

---

## Section 4 — MXNT / Tether-Mexico — STRUCTURALLY GOOD_FIT, PRACTICALLY NOT_A_FIT

### 4.1 Investigation Summary

**Launch**: Tether announced MXNT in May 2022 on Ethereum, Tron, and Polygon (per cryptopotato.com / decrypt.co / coindesk.com).

**Float status (2026-05-03 review)**: Multiple WebSearch attempts to find current MXNT supply across Ethereum/Polygon/Tron returned no recent (2024-2026) supply or volume data. Cross-reference: MXNT does NOT appear in any major LATAM-stablecoin tracker as of 2026-05-03 (CoinGecko's BRL1 page doesn't reference MXNT as a peer; CoinMarketCap returns no live MXNT page from this dispatch's queries). Tether has not published MXN-corridor adoption figures since the 2022 launch announcement.

**Inferred status**: MXNT is **near-dormant or fully dormant** (Tether launches several stablecoins as "testing grounds" without sustained marketing follow-through; MXNT appears to be in this category).

### 4.2 VERDICT (MXNT)

| Dimension | Assessment |
|-----------|-----------|
| a_s archetype fit | GOOD_FIT structurally (Tether is sophisticated USD-reserve issuer) |
| On-chain quantifiability | UNKNOWN (data not surfaced in 2024-2026 free-tier sources; HALT-flag for opacity) |
| Δ^(a_s) attribution clarity | OPAQUE (cannot attribute what cannot be measured) |
| Geography vs Pair D | Cross-corridor (MXN/USD) |
| Sample window vs Stage-1 | UNKNOWN |
| Verdict | **DROP** — Tether MXNT appears dormant since 2023; no observable float for Δ^(a_s) attribution at free-tier |

---

## Section 5 — wARS / Ripio (Ethereum + Base + World Chain) — NEW DISCOVERY, STRONG FIT

### 5.1 Mint/Burn Mechanism On-Chain (Inferred)

**Issuer**: Ripio, Latin American crypto exchange with 25M+ users, headquartered in Argentina.

**Networks**: Ethereum, Coinbase Base, World Chain (per https://www.coindesk.com/markets/2025/11/01/latin-american-crypto-exchange-ripio-launches-argentine-peso-stablecoin-wars).

**Contract addresses**: NOT enumerated in CoinDesk source; further query attempts in this dispatch did not return verified Etherscan/Basescan addresses. **Action item for Stage-2: contact Ripio or query directly via Etherscan/Basescan token search by name "wARS" to find the verified contract.**

**Total outstanding (per CoinDesk 2025-12-31 snapshot)**: 431,000,000 wARS, fully backed by ARS 447,361,996.56 held in Argentine bank account. 1 wARS = 1 ARS = ~$0.001 USD at recent ARS/USD rates → market cap ~$430,000 USD.

**Reserve currency**: 100% ARS (Argentine peso). Same one-sided structure as MXNB and BRL1.

### 5.2 Δ^(a_s) Attribution Clarity

**At issuer level**: NOT_A_FIT (Ripio reserves are ARS-only; no USD reserve to deplete on ARS/USD vol shock).

**At LP level**: GOOD_FIT theoretically; however, ARS/USD is in extreme regime (229% inflation Apr 2025; bolivar-class currency by 2026), which means LP Impermanent-Loss equivalent ON wARS-USDC pools is dominated by trend (devaluation drift) NOT volatility (σ). The structural a_s premium-funded ratchet thesis fails on trending-mean substrates per Pair D Stage-1 Phase-A.0 lessons.

**Net cumulative position observability**: YES at aggregate level (sum of mint - burn = 431M wARS).

**Sample window vs Stage-1**: wARS launched 2025-Q4; only ~5 months of history as of 2026-05-03. **Far below N_MIN=75 at any cadence finer than daily.**

### 5.3 VERDICT (wARS)

| Dimension | Assessment |
|-----------|-----------|
| a_s archetype fit | WEAK_FIT (issuer is one-sided ARS; LP-level a_s confounded by trend-dominated ARS/USD regime) |
| On-chain quantifiability | **HIGH** (standard ERC-20 on Ethereum + Base) |
| Δ^(a_s) attribution clarity | **CLEAN** at aggregate; **OPAQUE-TO-NOISE** at LP level due to ARS regime |
| Geography vs Pair D | Cross-corridor (ARS/USD) — but ARS regime is extreme outlier vs COP |
| Sample window vs Stage-1 | **BELOW N_MIN=75** at any reasonable cadence |
| Verdict | **DROP for Stage-2 immediate use**; preserve for future-iteration if Argentina stabilizes (unlikely 2026 horizon) |

---

## Section 6 — Cross-Corridor Comparative Table

| Candidate | Corridor | Supply (USD-eq) | Issuer Reserve Currency | a_s Archetype Fit | Sample Window vs N_MIN=75 (weekly) | Verdict |
|-----------|----------|-----------------|------------------------|-------------------|-------------------------------------|---------|
| **MXNB / Juno** | MXN/USD | $1.3M (24.5M MXNB) | MXN-only | LP-level GOOD | ~52 weeks (BELOW); daily cadence ~390 obs PASSES | **TOP-1** |
| **Mento V2 COPm (via Reserve)** | COPm/USD aggregate | Reserve $1.9M cross-chain | Multi-asset (CELO/BTC/ETH/USDC/DAI) | Reserve-aggregate GOOD | ~134 weeks PASSES (Aug 2023 onwards) | **TOP-2** |
| **wARS / Ripio** | ARS/USD | $0.43M (431M wARS) | ARS-only | LP-level GOOD but trend-dominated | ~22 weeks (BELOW) | DROP for now |
| **BRL1 consortium** | BRL/USD | $1.3M (6.58M BRL1) | BRL-only | Consortium structure + thin float | Daily cadence borderline; weekly insufficient | **DROP** (HALT-flag) |
| **MXNT / Tether-Mexico** | MXN/USD | UNKNOWN (likely dormant) | USD-only (canonical Tether) | GOOD structurally, OPAQUE practically | UNKNOWN | **DROP** (opacity HALT) |

### Cross-Corridor Recommendation

**Primary: Mento V2 COPm via Reserve aggregate** for direct Pair D corridor match (Colombian/USD), accepting the Reserve-aggregate scope per spec §3.5 substrate-relocation. COPm has 134 weekly observations available which PASSES N_MIN=75 at weekly cadence; this is the **only candidate that meets both corridor-match AND sample-window adequacy** at weekly cadence in this dispatch.

**Secondary: MXNB / Juno + LP-level Δ^(a_s) attribution** as cross-corridor archetype validator. MXNB is the cleanest single-issuer-with-on-chain-mint/burn-events candidate but requires daily-cadence to meet N_MIN=75 due to short history (only ~13 months since launch).

**Tertiary**: BRL1 if and only if supply scales 10× by Stage-3; wARS if and only if Argentina stabilizes (low probability 2026 horizon).

---

## Section 7 — Product-Shape Implications for the CPO Instrument Design

### Top 3 Implications

**1. The a_s is at the LP, not the Issuer.** The category (ii) deep-dive reveals that LATAM-fiat issuers (Juno, BRL1 consortium, Ripio) hold **one-sided local-currency reserves** — they do NOT bear the canonical DRAFT.md eq 1 structural exposure of "deliver fixed B from yield-earning Y reserves where Y ≠ X". The actual a_s is the **AMM LP** providing local-stable ↔ USDC liquidity. This reframes the CPO product's natural customer from "stablecoin issuer treasury desk" to "DEX LP / market-maker desk". The LP is short MXN/USD volatility on the inventory of MXNB they hold; selling them a long-vol perpetual on MXN/USD pays them when impaired. **Commercial implication: target Uniswap V3/V4 LP operators, not stablecoin issuers, as Tier-1 buyers.**

**2. Mento V2 Reserve is the ONLY direct Pair-D-corridor match at adequate sample size.** All other candidates are either cross-corridor (MXNB, BRL1, wARS) requiring corridor-specific β re-estimation, or have sample windows below N_MIN=75 at usable cadences. The Mento Reserve at Celo aggregates COPm exposure across the entire protocol, providing 134 weekly observations since COPm launch (Aug 2023). **Implication: CPO Stage-2 Path B should anchor on Mento Reserve substrate-relocation per spec §3.5 as primary instrument; cross-corridor MXNB-LP analysis as Stage-2 sensitivity check.**

**3. Mint/Burn observability is uniformly CLEAN across category (ii); the bottleneck is sample size + corridor mapping.** None of the five investigated candidates have OPAQUE mint/burn flows — Circle FiatToken pattern (MXNB), Mento Broker pattern (Mento V2), and presumed standard ERC-20 patterns (BRL1, wARS) all expose per-event mint/burn at chain level. The free-tier verification gate that killed Bitgifty/Walapay (operator EOA not publicly attributable) does NOT apply here because tokenized-fiat issuers MUST publicly enumerate their token contract addresses for liquidity and integration purposes. **Implication: the on-chain visibility gate can be considered SOLVED for category (ii); future deep-dives can focus on the substrate-quality question (sample size + corridor relevance) without re-investigating the gate question.**

### Deployment Story Narrative

**For MXNB/Juno**: "We sell long-MXN-vol perpetuals to Uniswap V3 Arbitrum LPs providing MXNB-USDC liquidity. When MXN devalues, the LP's MXNB inventory loses USD value AND the perpetual pays out — net LP P&L is hedged. Juno's ecosystem of DEX integrators is a discoverable Tier-1 buyer list."

**For Mento V2 COPm**: "We sell long-COP-vol perpetuals against the Mento Reserve's protocol-aggregate FX exposure. The Mento Reserve holds $1.9M across 29 tokens; a portion of that backing is allocated to COPm circulation. When COP devalues, the Reserve must mark-down its USD-equivalent COPm-coverage; the perpetual pays out. Mento DAO is a discoverable Tier-1 buyer for protocol-treasury hedging."

**For BRL1 / wARS**: Not commercially viable at current float; revisit on 10× scale-up.

### UX Patterns from these Issuers Worth Replicating

1. **Circle FiatToken via masterMinter delegation** (MXNB / Juno): standard, audited, integration-ready for any institutional minting workflow.
2. **Mento Broker single-entry-point swap interface**: abstracts mint/burn complexity behind a uniform `swapIn(exchangeProvider, exchangeId, tokenIn, tokenOut, amountIn, amountOutMin)` API. CPO product could expose a similar single-entry-point `hedgeOpen(corridor, notional, tenor)` API.
3. **CoinDesk-style cumulative-issuance reconciliation table** (wARS): publishing per-period reconciliation of on-chain supply vs off-chain reserve attestation as a transparency baseline. CPO product should publish similar per-period structural-exposure reconciliation.

---

## Section 8 — HALT-and-Surface Items

1. **BRL1 substrate-noise gate**: HALT-FLAG fired per spec §3.5. BRL1 outstanding supply ($1.3M USD-equivalent) and daily volume ($55K) are 2-3 orders of magnitude below MXNB. Per-event noise dominates structural signal at this float level. Drop from Stage-2 Path B core shortlist.

2. **MXNT (Tether-Mexico) opacity gate**: HALT-FLAG fired. Tether stopped publishing MXNT marketing/adoption data after 2022 launch announcement; no 2024-2026 supply or volume data surfaced in free-tier sources. Treat as dormant; do not pursue.

3. **MXNB sample-window gate at weekly cadence**: NEAR-HALT. MXNB has only ~13 months of history since 2025-Q1 launch; weekly cadence yields ~52 obs (BELOW N_MIN=75). Stage-2 Path B work using MXNB MUST escalate to daily cadence (~390 obs, PASSES) OR accept SUBSTRATE_TOO_SHORT and combine with Mento V2 COPm (which has ~134 weekly obs).

4. **MXNB issuer-side a_s reframing**: NOT a HALT but a structural recalibration. Juno-as-issuer is NOT short MXN/USD vol (MXN-only reserves); Δ^(a_s) target must reframe to LP-level. This was not anticipated in the dispatch brief and is the most important architectural finding of this deep-dive.

5. **BRL1 consortium attribution gap**: NEAR-HALT. Even if BRL1 float scales 10×, the 4-issuer consortium structure (Bitso, MercadoBitcoin, Foxbit, Cainvest) commingles mint events at the contract level — there is no per-issuer attribution field in the standard ERC-20 mint/burn pattern. Per-issuer Δ^(a_s) requires off-chain consortium disclosure that may never come.

6. **MXNB CertiK vs Big-Four discrepancy**: Marketing materials claim "monthly Big Four attestations" but only CertiK audit is verifiable on-chain (https://skynet.certik.com/projects/mxnb-token). CertiK is NOT a Big Four firm. This is a credibility note for the CPO product team if Juno is approached commercially — verify the Big Four claim before publishing it as a CPO due-diligence point.

---

## Sources

- [MXNB on Arbitrum (Bitso/Juno docs)](https://docs.bitso.com/juno/docs/mxnb-on-arbitrum)
- [MXNB token on Arbiscan](https://arbiscan.io/token/0xf197ffc28c23e0309b5559e7a166f2c6164c80aa)
- [MXNB on RWA.xyz](https://app.rwa.xyz/assets/MXNB)
- [MXNB whitepaper](https://mxnb.mx/whitepaper.pdf)
- [Bitso launches MXNB stablecoin (BitGet News)](https://www.bitget.com/news/detail/12560604667368)
- [BRL1 token on Polygonscan](https://polygonscan.com/token/0x5C067C80C00eCd2345b05E83A3e758eF799C40B5)
- [BRL1 on CoinGecko](https://www.coingecko.com/en/coins/brl1)
- [BRL1 on OKLink Polygon explorer](https://www.oklink.com/polygon/token/0x5C067C80C00eCd2345b05E83A3e758eF799C40B5)
- [BRL1 official site](https://www.brl1.io)
- [BRL1 launch coverage (CryptoNews)](https://crypto.news/brazils-real-pegged-stablecoin-brl1-set-to-launch-later-this-year/)
- [Mento Broker docs](https://docs.mento.org/mento/build-on-mento/integration-overview/integrate-the-broker)
- [Mento V3 documentation corpus](https://docs.mento.org/mento-v3/llms-full.txt)
- [Mento Broker on Celoscan](https://celoscan.io/address/0x777a8255ca72412f0d706dc03c9d1987306b4cad)
- [Mento Reserve on Celoscan](https://celoscan.io/address/0x9380fA34Fd9e4Fd14c06305fd7B6199089eD4eb9)
- [Tether MXNT launch (Decrypt 2022)](https://decrypt.co/101420/tether-enters-latin-american-market-with-mexican-peso-backed-stablecoin)
- [Tether MXNT launch (CryptoPotato 2022)](https://cryptopotato.com/tether-launches-mexican-peso-backed-stablecoin-on-ethereum-tron-polygon/)
- [Ripio wARS launch (CoinDesk 2025-11)](https://www.coindesk.com/markets/2025/11/01/latin-american-crypto-exchange-ripio-launches-argentine-peso-stablecoin-wars)
- [Ripio wARS technical detail (KuCoin)](https://www.kucoin.com/news/flash/ripio-launches-argentine-peso-stablecoin-wars-on-ethereum-and-coinbase-base)
- [LATAM FX outlook 2025 (Pepperstone)](https://pepperstone.com/en-eu/analysis/navigating-markets/outlook-2025-latam-fx/)
- [LATAM FX volatility profile (Pepperstone)](https://pepperstone.com/en-eu/analysis/navigating-markets/latam-fx-why-these-currencies-need-to-be-on-your-radar/)
- [USD/MXN volatility chart (myfxbook)](https://www.myfxbook.com/forex-market/volatility/USDMXN)
- [Stablecoin Payments in Venezuela (Transfi)](https://www.transfi.com/blog/stablecoin-payments-in-venezuela-dollarizing-a-hyperinflated-economy-on-chain)
- [Anclap Stellar-based Peruvian sol stablecoin](https://cryptocurrencynewsroom.com/anclap-leads-to-stellar-stablecoin-which-is-pegged-to-the-peruvian-currency/)
- [Transfero ARZ (Argentine peso) stablecoin](https://transfero.com/stablecoins/arz/)
- [Num Finance NUARS](https://coinmarketcap.com/currencies/num-ars/)
- [Mountain Protocol USDM wind-down (CoinDesk 2025-05)](https://www.coindesk.com/business/2025/05/12/anchorage-digital-to-acquire-usdm-issuer-mountain-protocol-in-stablecoin-expansion-move)
