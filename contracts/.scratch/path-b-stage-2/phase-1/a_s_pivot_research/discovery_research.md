---
artifact_kind: pivot_research
spec_ref: contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md (§6 typed exception Stage2PathBASOnChainSignalAbsent, Pivot β)
parent_task: Pair D Stage-2 Path B Phase-1 a_s pivot research (post Bitgifty/Walapay on-chain visibility FAIL)
emit_timestamp_utc: 2026-05-03
budget_pin: free_tier_only
methodology: WebSearch + WebFetch only; verification via Celoscan / Etherscan / Arbiscan public access; no paid APIs
constraints:
  - On-chain visibility is HARD GATE
  - No WTP / behavioral-demand inference (CORRECTIONS-γ structural-exposure framing)
  - No Path A files touched
  - No spec / plan modification
---

# Pair D Stage-2 Path B — a_s Pivot Discovery Research

## Executive Summary

The pre-committed Bitgifty + Walapay candidates failed the on-chain visibility gate (parallel agent confirmation). This research investigates Pivot β candidates pre-pinned in spec §6 (MiniPay / GoodDollar / Valora) plus a broader sweep of Latin-American + African stablecoin payment-rail operators with structural a_s archetype fit.

**Findings:**
- **Candidates investigated: 12** (3 Pivot β pre-pinned + 9 expanded sweep)
- **Candidates passing the on-chain visibility gate: 5** (one of which is already in v0 allowlist as Mento Broker baseline)
- **Top a_s structural-fit candidates with verified on-chain footprint:** GoodDollar (UBI scheme on Celo), MXNB / Juno (peso stablecoin on Arbitrum), Mento V2 Broker (multi-pair Mento V2 baseline)
- **Strong commercial fit but FAIL gate:** MiniPay (operator EOAs not publicly attributable), Valora (smart contract accounts per-user, no central operator), Pretium / Kotani Pay / Fonbnk (off-chain payment processors using Mento tokens but no published merchant-settlement contract)

**HALT items:** None. The gate-pass set (5) exceeds the spec §3.5 SUBSTRATE_TOO_NOISY threshold for a single venue of audit_summary, but is concentrated in instruments whose a_s archetype fit is INDIRECT (the canonical model — operator must deliver fixed local-currency obligation by converting Y-currency reserves — is best matched by MXNB issuance/redemption flow against fiat MXN reserves, NOT by user-side wallet operators).

---

## Section 1 — Pivot β Pre-Pinned Candidates

### 1.1 Opera MiniPay

- **Description:** Non-custodial stablecoin wallet built on Celo by Blueboard Limited (Opera company). Uses Celo native stablecoins (cUSD/USDm, cKES/KESm, cCOP/COPm) plus USDT/USDC. Targets unbanked users in Africa primarily; recently expanded to Latin America via PIX (Brazil) and Mercado Pago (Argentina) integration through Noah infrastructure (2025-11).
- **Country / region:** Pan-African + Latin America (Kenya, Ghana, Nigeria primary; Brazil, Argentina via Noah)
- **a_s archetype fit:** WEAK_FIT — MiniPay itself is a non-custodial wallet (each user holds their own stablecoin balance); the operator with structural a_s exposure is **Noah** (the conversion infrastructure between USDT and PIX/Mercado Pago local currency, who must source local fiat to deliver against on-chain stablecoin redemption). MiniPay's own contracts do NOT have the a_s structural pattern.
- **ON-CHAIN VISIBILITY GATE: FAIL**
  - Public docs at https://docs.celo.org/build/build-on-minipay/overview list NO MiniPay-specific contract addresses.
  - MiniPay uses standard Celo stablecoin tokens (already in v0 allowlist via USDm `0x765DE816...`).
  - The Noah conversion infrastructure operates off-chain (custodial conversion); their on-chain redemption EOAs are not publicly disclosed in docs reviewed.
  - GitHub: no public deployment manifest found.
  - Reason for FAIL: Same pattern as Bitgifty/Walapay — operator-side conversion happens off-chain, only user wallet activity is on-chain (which doesn't isolate the a_s flow).
- **Estimated transaction volume:** 10M+ activated wallets per Opera press release (2025-05). Per-user volume disclosed only as "USDT spending" aggregate without per-merchant breakdown.
- **a_s thesis fit (paragraph):** MiniPay's structure is *user-custodial* — each end user holds their own USDT/USDm balance and converts at point-of-payment via Noah's custodial bridge. The a_s archetype (operator must deliver fixed local-currency obligation B at time T from non-local reserves) fits Noah, not MiniPay. Without Noah's settlement EOAs disclosed publicly, the |Δ^(a_s)| structural-exposure quantification cannot proceed for the MiniPay sub-graph. RECOMMENDATION: drop MiniPay; investigate Noah separately if their on-chain redemption EOAs become discoverable post-2025-11 LATAM rollout.

### 1.2 GoodDollar

- **Description:** Universal Basic Income (UBI) protocol issuing G$ token. Daily claim mechanism distributes G$ pro-rata to all verified members. The Reserve / Mento integration (V4) introduces a structural a_s pattern: the protocol must deliver a fixed UBI claim quantity to each user (B), funded from a reserve that earns yield in non-G$ assets.
- **Country / region:** Global; predominantly emerging markets (Africa, Latin America).
- **a_s archetype fit:** GOOD_FIT (with caveat) — GoodDollar's UBIScheme is the closest pre-pinned candidate to the a_s archetype: a protocol with a *committed daily distribution obligation* (the UBI claim) funded from a reserve. The reserve denomination (cUSD / G$) creates a Y/X relationship if X is interpreted as G$ purchasing-power against a yield-currency Y. CAVEAT: G$ purchasing-power volatility is not COP/USD; the Pair D Stage-1 PASS evidence is COP/USD-specific. To use GoodDollar as a_s substrate, the framework must accept the *substrate-noise compromise* per spec §3.5 (the FX volatility a_s tracks is G$-internal not COP/USD).
- **ON-CHAIN VISIBILITY GATE: PASS**
  - **Celo G$ Token:** `0x62B8B11039FcfE5aB0C56E502b1C372A3d2a9c7A` (verified, UUPS proxy, 999K+ transactions)
  - **Celo UBI Scheme Proxy:** `0x43d72Ff17701B2DA814620735C39C620Ce0ea4A1` (verified, EIP-1967 proxy → UBISchemeV2 implementation `0x43f0eb66ea3c2d9552241525aa1af6607227dfbf`, 69M+ transactions)
  - **Celo GOOD Governance:** `0xa9000Aa66903b5E26F88Fa8462739CdCF7956EA6`
  - **Fuse G$ Token:** `0x495d133B938596C9984d462F007B676bDc57eCEC`
  - **Fuse UBI Scheme:** `0xd253A5203817225e9768C05E5996d642fb96bA86`
  - **Ethereum G$ Token:** `0x67C5870b4A41D4Ebef24d2456547A03F1f3e094B`
  - Source: docs.gooddollar.org (V3 contracts page, llms-full.txt corpus)
  - Verification on Celoscan: confirmed exact-match source verification, deployment by GoodDollar Deployer `0x5128e3c1f8846724cc1007af9b4189713922e4bb`
- **Estimated transaction volume:** 69M+ transactions on UBI Scheme alone (Celo). G$ token has 999K+ transactions on Celo. This is high-volume — well above any spec §3.5 SUBSTRATE_TOO_NOISY floor.
- **a_s thesis fit (paragraph):** The UBI Scheme contract is the structural a_s embodiment: the protocol commits to delivering a fixed daily G$ allocation per verified member, sourcing this from a reserve denominated partly in cUSD (Mento V4 Reserve integration). The reserve must convert from yield-bearing assets back into G$ to honor distribution claims, making the protocol short G$-vs-USD volatility (analogous to the Δ^(a_s) < 0 thesis). However the X here is *G$/USD purchasing power*, NOT *COP/USD*, so this is not a direct Pair D match — it's a same-archetype substrate at a different (X, Y) pair. Useful for v0 audit_summary inclusion as a *cross-substrate sanity check*; not a direct Stage-1 PASS regression replicator.

### 1.3 Valora

- **Description:** Mobile cryptocurrency wallet for Celo, with smart-contract-account architecture (each user gets an EOA + Meta-Transaction Wallet smart contract account). Uses Celo native stablecoins.
- **Country / region:** Global, with strong Africa + LATAM user base
- **a_s archetype fit:** NOT_A_FIT — Valora is a wallet-only product; users self-custody. There is NO central operator with a fixed local-currency obligation pattern. Each user is their own counterparty.
- **ON-CHAIN VISIBILITY GATE: FAIL (architectural)**
  - Valora uses *per-user* smart-contract accounts ("Meta-Transaction Wallets") — there is no aggregable single "Valora settlement contract".
  - The Valora wallet repository (https://github.com/valora-xyz/wallet) is a React Native frontend; no central deployment manifest exists.
  - Operating principle from Celo Smart Contract Accounts docs: per-user MTW addresses derived per-user; not a single operator address.
- **Estimated transaction volume:** N/A (no central settlement contract)
- **a_s thesis fit (paragraph):** Valora is structurally OUT-OF-SCOPE for the a_s framework: there is no operator who must deliver a fixed local-currency obligation. Each user IS the operator and counterparty for their own transactions. RECOMMENDATION: drop from candidate pool. If a Valora-aggregated user-side flow is needed for Stage-1 sanity, the proper data source is the Mento V2 Broker / Mento V3 Router transaction stream filtered to Valora-originated MTWs, but identifying such MTWs without a public registry is unfeasible at free-tier.

---

## Section 2 — Other Candidates Discovered

### 2.1 MXNB / Juno (Bitso subsidiary)

- **Description:** Mexican peso stablecoin issued by Juno (Bitso Group subsidiary), launched 2025-Q1, deployed on Arbitrum. 1:1 backed by MXN reserves at Tier-1 banks; monthly Big Four attestations. Juno provides a Mint Platform with APIs for businesses to issue, redeem, and convert MXNB; operates fiat on/off-ramps via Mexico's SPEI banking system.
- **Country / region:** Mexico
- **a_s archetype fit:** GOOD_FIT — Juno IS the a_s archetype made explicit: it must deliver MXN to redeemers (B in local currency), sourced from its USD-denominated treasury reserves (Y). Every redemption converts a fixed MXNB notional into MXN; volatility in MXN/USD raises Juno's expected sourcing cost. This is the cleanest structural a_s match in the entire candidate set.
- **ON-CHAIN VISIBILITY GATE: PASS**
  - **MXNB Arbitrum:** `0xF197FFC28c23E0309B5559e7a166f2c6164C80aA` (verified Circle FiatTokenProxy pattern; CertiK-audited Feb 2025; 6 decimals; 20.4M total supply; 212 holders as of Apr 2026)
  - **Implementation:** `0x72beddf7032eec58f199857b79a8e37020c14e42`
  - Source: arbiscan.io/token/0xf197ffc28c23e0309b5559e7a166f2c6164c80aa, mxnb.mx whitepaper
  - Network: Arbitrum One (also reported on Ethereum + Avalanche — same address per Circle FiatToken pattern)
- **Estimated transaction volume:** 20.4M MXNB outstanding × velocity = active Juno minting/redeeming flow visible via mint() / burn() events on the FiatTokenProxy. Circle FiatToken pattern ensures issuer-only mint/burn discoverable via masterMinter / minter role events.
- **a_s thesis fit (paragraph):** Juno's MXNB operation is the textbook Pair D Path B a_s candidate at a different geography (Mexico instead of Colombia). The mint/burn flow is on-chain and isolates the supply-side delivery obligation. Δ^(a_s) for Juno is computable as: each MXN-redemption obligation B_i × (1 - MXN_received / USD_treasury_drawn × FX_rate_t). The thesis Δ^(a_s) < 0 implies that during MXN/USD volatility spikes, Juno's effective USD-cost-per-MXN-redeemed rises. This is *Mexican-corridor* not Colombian, so it doesn't replicate Pair D Stage-1 PASS variables directly, but it is a clean cross-corridor sanity test for the a_s archetype hypothesis. RECOMMENDATION: high-priority shortlist.

### 2.2 BRL1 (Bitso + Mercado Bitcoin + Foxbit consortium)

- **Description:** Brazilian Real stablecoin issued by a consortium of Bitso, Mercado Bitcoin, and Foxbit. 1:1 backed by BRL reserves; users deposit via PIX, BRL1 minted to wallet; monthly attestations.
- **Country / region:** Brazil
- **a_s archetype fit:** GOOD_FIT — same pattern as MXNB at Brazil corridor. The issuer consortium must deliver BRL on redemption from USD-denominated treasury (or BRL-denominated; details depend on consortium reserve composition).
- **ON-CHAIN VISIBILITY GATE: PASS**
  - **BRL1 Polygon:** `0x5C067C80C00eCd2345b05E83A3e758eF799C40B5`
  - Source: brl1.io, bitso.com/business/products/brl1-brazilian-real-stablecoin
  - Network: Polygon (deployed on Polygon with planned multi-chain expansion)
- **Estimated transaction volume:** Listed on OKX for spot trading, with active CoinMarketCap pricing. Volume not explicitly enumerated in free-tier sources.
- **a_s thesis fit (paragraph):** Identical structural pattern to MXNB at the BRL corridor. Useful for cross-LATAM-corridor consistency check on the a_s archetype. Lower priority than MXNB only because Mexico has cleaner free-tier coverage and Bitso unilaterally controls Juno (single-issuer attribution clear), whereas BRL1's consortium structure makes per-issuer Δ^(a_s) attribution harder. RECOMMENDATION: include in extended shortlist as cross-corridor diagnostic.

### 2.3 Mento V2 Broker (already in v0 allowlist)

- **Description:** Mento V2 routing contract on Celo. Aggregates all Mento V2 stable token swap volume via the Broker.swapIn / swapOut interface.
- **Country / region:** Pan-Mento (Celo-resident; serves COPm, KESm, BRLm, USDm, EURm, XOFm, GBPm, JPYm, CHFm, etc.)
- **a_s archetype fit:** WEAK_FIT — the Broker itself is a routing contract, not a payment operator with a fixed-obligation exposure. However the *Reserve* (which the Broker draws against) IS the structural a_s embodiment for Mento as a whole.
- **ON-CHAIN VISIBILITY GATE: PASS** (already enumerated in v0 allowlist)
  - **Broker:** `0x777A8255cA72412f0d706dc03C9D1987306B4CaD` (verified; 2,121,798 transactions; EIP-1967 proxy; impl `0x1b78f6acd05e7bcb00f74863bfd8a7c264143e37`)
  - **Reserve Proxy:** `0x9380fA34Fd9e4Fd14c06305fd7B6199089eD4eb9` (verified Celo Reserve; impl `0xfd9651862bc1965349e92073152112289393b57d`; holds 5.8M CELO + 29 tokens worth ~$1.9M cross-chain)
  - **BreakerBox:** `0x303ED1df62Fa067659B586EbEe8De0EcE824Ab39` (verified; circuit-breaker for rate feeds)
  - **BiPoolManager:** `0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901` (already in v0 allowlist)
- **Estimated transaction volume:** 2.1M+ Broker transactions lifetime per Celoscan
- **a_s thesis fit (paragraph):** The Mento Reserve is structurally short the FX-volatility of all stable tokens it backs. As COPm circulation grows, the Reserve must hold sufficient collateral to redeem COPm against COP-equivalent value — this matches the a_s archetype. The Broker is the *routing* address; the Reserve is the *obligation-bearing* address. However the Reserve's collateral is multi-asset (CELO, BTC, ETH, USDC, DAI) so per-currency Δ^(a_s) attribution requires per-pool getReserveAddressBalance() decomposition. RECOMMENDATION: Reserve `0x9380fA34Fd9e4Fd14c06305fd7B6199089eD4eb9` is the strongest single-contract a_s embodiment in the Mento ecosystem and should be added to allowlist as a *protocol-aggregate* a_s reference, complementing the per-stable-token TVL series that v0 already enumerates.

### 2.4 cKES / KESm (Mento Kenyan Shilling)

- **Description:** Mento V2 Kenyan Shilling stablecoin. Same StableTokenV2 implementation pattern as COPm.
- **Country / region:** Kenya
- **a_s archetype fit:** WEAK_FIT (token-level, not operator-level) — the token contract itself is just an ERC-20; the a_s exposure is at the Mento Reserve level.
- **ON-CHAIN VISIBILITY GATE: PASS**
  - **cKES / KESm:** `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` (verified StableTokenKESProxy; Solidity v0.5.17; total supply 27.9M; 7,639 holders)
  - Source: celoscan.io/token/0x456a3D042C0DbD3db53D5489e98dFb038553B0d0
- **Estimated transaction volume:** 7,639 holders, ~28M cKES supply — moderate; useful as a parallel Africa-corridor Y if a future iteration switches to Kenyan structural-transformation Y.
- **a_s thesis fit (paragraph):** Direct token contract for Kenyan-corridor structural-exposure tracking. Useful as a placeholder for a future iteration where Y is a Kenyan young-worker variable instead of Colombian. For Pair D specifically (COP/USD as X, Colombian young-worker share as Y), KESm is OUT-OF-SCOPE; it's preserved here as documented future-iteration asset.

### 2.5 Pretium Finance

- **Description:** Stablecoin payment platform integrating cUSD with mobile money providers (M-Pesa Kenya, Opay/Moniepoint/Palmpay Nigeria). Operates in Kenya, Uganda, Tanzania, Nigeria, South Africa.
- **Country / region:** Sub-Saharan Africa
- **a_s archetype fit:** GOOD_FIT (commercially) — Pretium acts as the bridge between cUSD inflows and local-mobile-money payouts; they must deliver KES/NGN/etc. when receiving cUSD, structurally short the FX volatility of the local currency vs USD.
- **ON-CHAIN VISIBILITY GATE: FAIL**
  - No published smart contract addresses found. Pretium's documentation describes it as a "decentralized, non-custodial payment platform" but no operator settlement contract is enumerated in any source reviewed.
  - GitHub presence not found at expected path.
  - The cUSD inflows would be visible at the cUSD token contract (`0x765DE816...`) but cannot be filtered to Pretium-originated flows without a known Pretium operator EOA.
- **Estimated transaction volume:** Not publicly disclosed
- **a_s thesis fit (paragraph):** Pretium's commercial structure is a textbook a_s match (cUSD-denominated inflows, KES/NGN-denominated outflows; structurally short FX volatility on the payout side), but lack of public on-chain attribution makes |Δ^(a_s)| quantification infeasible at free-tier. Same FAIL pattern as Bitgifty/Walapay. RECOMMENDATION: drop from shortlist; flag for re-investigation if Pretium publishes a deployment manifest in the future.

### 2.6 Kotani Pay

- **Description:** On/off-ramp API connecting Web3 to local African currencies via M-Pesa and other mobile money. Uses cUSD on Celo. Tether-invested.
- **Country / region:** Pan-African (Kenya primary)
- **a_s archetype fit:** GOOD_FIT (commercially) — same pattern as Pretium.
- **ON-CHAIN VISIBILITY GATE: FAIL**
  - GitHub `Kotani-Pay/maraswap` exists but is an AMM repo last updated 2020-11, no deployment manifest with verified contracts.
  - GitHub `Kotani-Pay/HTLC` is an HTLC implementation, not a payment-rail settlement contract.
  - No central settlement contract published in docs reviewed.
- **Estimated transaction volume:** Not publicly disclosed
- **a_s thesis fit (paragraph):** Same FAIL pattern as Pretium. Operator-side conversion happens off-chain via direct mobile-money API integration; on-chain footprint is limited to user-side cUSD transfers without operator attribution. DROP.

### 2.7 Fonbnk

- **Description:** Allows users to swap prepaid mobile SIM card airtime / mobile money for stablecoins (USDC, USDT, cUSD) across multiple networks (Ethereum, Polygon, Celo, Stellar, Algorand, Solana, etc.).
- **Country / region:** Sub-Saharan Africa
- **a_s archetype fit:** WEAK_FIT — Fonbnk is the *forward* direction (local-currency airtime → stablecoin), which is the inverse of the a_s pattern (stablecoin obligation → local-currency delivery).
- **ON-CHAIN VISIBILITY GATE: FAIL**
  - No central settlement contract published.
  - Multi-chain operation makes operator-EOA attribution even harder.
- **Estimated transaction volume:** Not publicly disclosed
- **a_s thesis fit (paragraph):** Inverse-direction; structurally LONG FX volatility on inflow side (sells stablecoin to user, holds telecom-airtime receivable in local currency). Wrong sign for Pair D Stage-2 Path B. DROP.

### 2.8 El Dorado

- **Description:** Stablecoin-powered SuperApp for Latin America; #1 crypto app in Venezuela 2024. Uses USDT and USDM (MountainUSD); Arbitrum partnership for Tether infrastructure.
- **Country / region:** Argentina, Bolivia, Brazil, Colombia, Panama, Peru, Venezuela
- **a_s archetype fit:** WEAK_FIT — El Dorado operates as a P2P marketplace (users trade USDT for local currency directly with each other); not a single operator with a fixed obligation. Some operator-side balance sheet exposure exists (custodial accounts) but architecture is closer to an exchange than a fixed-obligation rail.
- **ON-CHAIN VISIBILITY GATE: FAIL**
  - No central settlement contract published; P2P model means most flows are off-chain user-to-user matching with on-chain USDT transfers between user wallets.
  - Tron DAO partnership for gasless USDT adds further off-chain plumbing.
- **Estimated transaction volume:** 1M+ users; volume not publicly enumerated
- **a_s thesis fit (paragraph):** Structurally a marketplace not a payment rail; a_s archetype only fits the marketplace's float-management contracts (if any are published), and none are found. DROP for free-tier; re-investigate if El Dorado publishes their custodial settlement architecture.

### 2.9 Yellow Card

- **Description:** Largest licensed stablecoin infrastructure provider in Africa (20 countries) plus Brazil/India/Mexico/China/Singapore/Hong Kong. Provides API for businesses to access on/off-ramps in 50+ local currencies. Supports Polygon, Celo, Solana, Stellar.
- **Country / region:** Africa primary, expanding globally
- **a_s archetype fit:** GOOD_FIT (commercially) — same operator-side FX exposure pattern as Pretium / Kotani Pay but at much larger scale.
- **ON-CHAIN VISIBILITY GATE: FAIL**
  - Documented as multi-chain stablecoin payments operator; no central settlement contract published in docs reviewed.
  - API documentation at docs.yellowcard.engineering describes the offchain integration surface, not on-chain contracts.
- **Estimated transaction volume:** Largest African stablecoin operator by claimed scale; numbers not publicly broken down by transaction volume in free-tier sources.
- **a_s thesis fit (paragraph):** Strongest commercial fit for the a_s archetype, but operates as a centralized custodial business — no on-chain settlement contract surface. DROP for free-tier; flag for re-investigation if Yellow Card moves to publish on-chain settlement infrastructure (a typical exit for grown stablecoin operators in 2026).

---

## Section 3 — Ranked Shortlist (PASS-the-gate Candidates)

| Rank | Candidate | Network | a_s Fit | Pair-D Direct Match | Recommendation |
|------|-----------|---------|---------|---------------------|----------------|
| 1 | **Mento Reserve** `0x9380fA34Fd9e4Fd14c06305fd7B6199089eD4eb9` | Celo | WEAK_FIT (aggregate-protocol-level) | Indirect (via COPm subgraph of Reserve obligations) | ADD to allowlist as protocol-aggregate a_s reference |
| 2 | **MXNB / Juno** `0xF197FFC28c23E0309B5559e7a166f2c6164C80aA` | Arbitrum | GOOD_FIT | Cross-corridor (MXN/USD not COP/USD) | ADD as cross-corridor a_s archetype validator |
| 3 | **GoodDollar UBI Scheme** `0x43d72Ff17701B2DA814620735C39C620Ce0ea4A1` | Celo | GOOD_FIT (different X) | Substrate-noise compromise (X = G$/USD purchasing power) | ADD as substrate sanity check; flag substrate-noise per spec §3.5 |
| 4 | **BRL1 consortium** `0x5C067C80C00eCd2345b05E83A3e758eF799C40B5` | Polygon | GOOD_FIT | Cross-corridor (BRL/USD) | OPTIONAL — extend if more candidates needed |
| 5 | **cKES / KESm** `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` | Celo | WEAK_FIT (token-level) | Future-iteration only (Kenya not Colombia) | OPTIONAL — preserve as documented future-iteration asset, NOT allowlist-add |

### Top-3 Verdict + Rationale

1. **Mento Reserve** — Direct relevance to Pair D (Reserve backs COPm specifically). Verdict: **WEAK_FIT** at single-currency attribution but **BEST_FIT** for protocol-aggregate a_s embodiment in the Mento ecosystem.
2. **MXNB / Juno** — Textbook a_s archetype: single issuer with fiat-redemption obligation and on-chain mint/burn flow. Verdict: **GOOD_FIT** but **CROSS-CORRIDOR** (Mexico not Colombia); useful as archetype validator, not direct Stage-1 replicator.
3. **GoodDollar UBI Scheme** — Has the structural fixed-obligation pattern (daily UBI claim must be honored from reserve) but the X-variable (G$/USD) does not match Pair D's COP/USD. Verdict: **GOOD_FIT** for a_s archetype, **WRONG_X** for Pair D direct replication.

### CORRECTIONS-γ structural-exposure framing reaffirmed

All three top-shortlist candidates have |Δ^(a_s)| computable in $-notional from on-chain mint/burn or transfer events without resorting to WTP / behavioral inference. Specifically:
- Mento Reserve: |Δ^(a_s)| = sum over redemptions of (USD-equivalent-treasury-drawdown - COPm-redeemed × COP/USD spot)
- Juno MXNB: |Δ^(a_s)| = sum over MXN redemptions of (USD-treasury-drawn - MXNB-burned × MXN/USD spot)
- GoodDollar UBI: |Δ^(a_s)| = sum over UBI claims of (cUSD-reserve-drawdown - G$-distributed × G$/cUSD spot)

---

## Section 4 — Decision Matrix

| Candidate | a_s Fit | Gate | Direct Pair-D Match | Volume | Verdict | Add-to-Allowlist |
|-----------|---------|------|---------------------|--------|---------|-----------------|
| MiniPay | WEAK | FAIL | No (operator-side off-chain) | 10M+ wallets | DROP | NO |
| GoodDollar | GOOD (different X) | PASS | Substrate-noise compromise | 69M+ tx UBI scheme | TOP-3 | YES |
| Valora | NOT_A_FIT | FAIL (architectural) | Per-user MTW, no central op | N/A | DROP | NO |
| Mento Reserve | WEAK (protocol-level) | PASS | Indirect (via COPm subgraph) | Aggregate Mento | TOP-1 | YES |
| MXNB / Juno | GOOD | PASS | Cross-corridor (MXN/USD) | 20M+ supply | TOP-2 | YES |
| BRL1 | GOOD | PASS | Cross-corridor (BRL/USD) | Listed on OKX | OPTIONAL | OPTIONAL |
| cKES / KESm | WEAK (token) | PASS | Future-iteration | 7.6K holders | OPTIONAL | NO |
| Pretium | GOOD (commercial) | FAIL | N/A | Not disclosed | DROP | NO |
| Kotani Pay | GOOD (commercial) | FAIL | N/A | Not disclosed | DROP | NO |
| Fonbnk | WEAK (inverse) | FAIL | N/A | Not disclosed | DROP | NO |
| El Dorado | WEAK (marketplace) | FAIL | N/A | 1M+ users | DROP | NO |
| Yellow Card | GOOD (commercial) | FAIL | N/A | Not disclosed | DROP | NO |

---

## Section 5 — Recommendations to Orchestrator

1. **PROCEED** — the gate-pass set is non-empty. Pivot β has a viable substrate (GoodDollar) plus two adjacent-corridor archetype validators (MXNB, Mento Reserve aggregate).
2. **NO HALT** for Pivot γ defer-to-Stage-3 escalation; the on-chain quantifiability question is answered: the a_s archetype IS quantifiable on-chain at the *protocol-aggregate Reserve* level and at the *cross-corridor stablecoin-issuer* level, but NOT at the individual *consumer-facing payment-rail-operator* level (which was the Bitgifty/Walapay framing that failed).
3. **ALLOWLIST DELTA** — see `contract_addresses_verified.toml` companion file. Three new entries proposed for v1 allowlist update:
   - Mento Reserve (Celo)
   - GoodDollar UBI Scheme (Celo)
   - MXNB (Arbitrum)
4. **CROSS-CORRIDOR FLAG** — Pair D Stage-1 PASS is COP/USD-specific; the strongest single-issuer a_s candidate (MXNB/Juno) is MXN/USD. Adopting MXNB requires explicit acknowledgment that Stage-2 Path B's instrument is being calibrated against an *adjacent-corridor* a_s archetype validator, not a Colombian-corridor direct match. This is a SUBSTRATE_RELOCATION in the spirit of spec §3.5 SUBSTRATE_TOO_NOISY but with a different mechanism: "right archetype, adjacent geography".
5. **NO PATH A IMPACT** — none of the candidates investigated affect Path A files; all Path A invariants preserved.

---

## Sources

- [Opera MiniPay launch (Opera press)](https://press.opera.com/2023/09/13/opera-launches-minipay/)
- [MiniPay LATAM rollout via Noah (CoinDesk Nov 2025)](https://www.coindesk.com/business/2025/11/19/stablecoin-spending-goes-mainstream-with-opera-minipay-s-latam-integration)
- [Noah × MiniPay partnership announcement](https://noah.com/blog/noah-minipay-partnership)
- [GoodDollar Protocol & G$ Token docs](https://docs.gooddollar.org/frequently-asked-questions/gooddollar-protocol-and-gusd-token)
- [GIP-14 Activation of G$ UBI on Celo](https://discourse.gooddollar.org/t/gip-14-activation-of-g-ubi-distribution-on-celo/481)
- [Valora wallet GitHub](https://github.com/valora-xyz/wallet)
- [Celo Smart Contract Accounts docs (Valora architecture)](https://docs.celo.org/what-is-celo/about-celo-l1/protocol/identity/smart-contract-accounts)
- [Mento Reserve dashboard](https://reserve.mento.org/)
- [Mento Reserve docs](https://docs.mento.org/mento/protocol-concepts/reserve)
- [Celo Reserve Proxy on Celoscan](https://celoscan.io/address/0x9380fA34Fd9e4Fd14c06305fd7B6199089eD4eb9)
- [Mento Broker on Celoscan](https://celoscan.io/address/0x777a8255ca72412f0d706dc03c9d1987306b4cad)
- [Mento BreakerBox on Celoscan](https://celoscan.io/address/0x303ed1df62fa067659b586ebee8de0ece824ab39)
- [GoodDollar UBI Scheme Proxy on Celoscan](https://celoscan.io/address/0x43d72Ff17701B2DA814620735C39C620Ce0ea4A1)
- [GoodDollar G$ Token on Celoscan](https://celoscan.io/address/0x62B8B11039FcfE5aB0C56E502b1C372A3d2a9c7A)
- [MXNB stablecoin on Arbiscan](https://arbiscan.io/token/0xf197ffc28c23e0309b5559e7a166f2c6164c80aa)
- [MXNB on Arbitrum (Bitso/Juno docs)](https://docs.bitso.com/juno/docs/mxnb-on-arbitrum)
- [BRL1 stablecoin (Bitso Business)](https://bitso.com/business/products/brl1-brazilian-real-stablecoin)
- [Pretium Finance Mento partnership spotlight](https://www.mento.org/blog/partner-spotlight---pretium-finance-powering-payments-and-cross-border-transactions-across-africa-with-mento-stablecoins)
- [Kotani Pay maraswap GitHub](https://github.com/Kotani-Pay/maraswap)
- [Fonbnk site](https://www.fonbnk.com/)
- [Yellow Card stablecoin infrastructure](https://yellowcard.io/)
- [El Dorado Arbitrum partnership](https://blog.arbitrum.io/el-dorados-stablecoin-powered-superapp-is-driving-tether-adoption-on-arbitrum-in-latam/)
- [Mento Colombian Peso (cCOP/COPm) on Celoscan](https://celoscan.io/address/0x8A567e2aE79CA692Bd748aB832081C45de4041eA)
- [Mento Kenyan Shilling (cKES/KESm) on Celoscan](https://celoscan.io/token/0x456a3D042C0DbD3db53D5489e98dFb038553B0d0)
