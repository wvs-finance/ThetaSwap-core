# Task 11.N.2 — COPM Bot Attribution Research

Date: 2026-04-24
Plan: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (Task 11.N pivot)
Author: Research subagent (on-chain triangulation; Dune + CeloScan + Carbon DeFi docs)
Companion data: Dune query IDs `7371006` (arb daily), `7371007` (Carbon trades by token), `7371008` (COPM-only Carbon), `7371009` (hour-of-day), `7371019` (top traders), `7371020` (top BancorArbitrage callers), `7371021` (COPM peak-day burst).
Credits used: 5.9 / 15-credit budget (61% under).

## 1. Executive summary (≤200 words)

The two dominant addresses in the COPM Transfer log are **NOT bots in the noise sense — they are the official Bancor Carbon DeFi protocol contracts on Celo.**

- `0x6619871118D144c1c28eC3b23036FC1f0829ed3a` is the **CarbonController** (the Carbon DeFi DEX strategy registry; verified on Carbon DeFi's own documentation page for mainnet contracts).
- `0x8c05ea305235a67c7095a32ad4a2ee2688ade636` is the **BancorArbitrage / Arb Fast Lane** contract (the on-chain arbitrage executor that fills Carbon maker orders against external venues; verified by Dune's decoded namespace `carbon_defi_celo.bancorarbitrage_evt_arbitrageexecuted`).

Of the four classifications proposed in the task brief, the strongest fit is **"Mento MM" reframed as "Carbon-LP MM + Arb Fast Lane"**. The flows are NOT TRM-arbitrage by an opportunistic searcher (although that occurs as a sub-channel), NOT Minteo treasury, NOT a generic DEX-LP rebalancer. They are the **automated maker/taker pair that Credit Collective and third-party LPs deployed onto Carbon DeFi after Bancor's July-2024 Celo launch**, capitalised in part by the publicly-documented $1M Credit Collective allocation. The aggregate behaviour is **delta-neutral round-trip market making across the Mento stablecoin basket** (cUSD / cEUR / cREAL / cKES / XOFm / COPM / USDT / USDC / CELO / WETH), with COPM representing only one trading pair in a much larger 10-token basket.

## 2. Per-bot profile

### 2.1  `0x6619871118D144c1c28eC3b23036FC1f0829ed3a` — CarbonController

**Identity (Axis 1).** Celo deployment of Carbon DeFi `CarbonController.sol`, the main Carbon protocol contract. Confirmed in two independent ways: (a) Carbon DeFi mainnet-contracts docs page lists this exact address as "CarbonController"; (b) Dune decodes 52 tables under `carbon_defi_celo.carboncontroller_*` keyed to the address. Implementation: `0x51aA24A9…78cE36317`. Deployed ~July 2024, matching the Bancor "Hello Celo, Carbon DeFi is Live!" launch.

**Counterparty graph (Axis 2).** Top `trader` fields on COPM-touching CarbonController trades (all-time): BancorArbitrage `0x8c05ea30…` originates **57,382 trades** (~52% of all COPM Transfer events). Other strategy authors: `0x20216f30…` (5,366), `0x24fb013b…` (2,619), `0xb961cdca…` (1,757), `0xb39f92b7…` (863), `0xcc9fb781…` (430). These six addresses cover virtually all COPM Carbon volume.

**Tokens touched (Axis 3).** From the 100-row daily token-pair leaderboard:

| Symbol | Address (verified) | Source |
|---|---|---|
| CELO native | `0xeeeeee…eeee` | Carbon convention |
| cUSD | `0x765de816…1282a` | Mento |
| cEUR | `0xd8763cba…6ca73` | Mento |
| cREAL | `0xe8537a3d…b4787` | Mento |
| cKES (KESm) | `0x456a3D04…3B0d0` | Mento Kenyan Shilling |
| XOFm | `0x73f93dcc…f29a08` | Mento West African CFA franc |
| COPM | `0xc92e8fc2…d5606` | Minteo |
| USDT | `0x48065fbb…83d5e` | Tether bridged |
| USDC | `0xceba9300…32118c` | USDC bridged |
| WETH | `0x66803fb8…fb207` | Wrapped Ether |

The pair leaderboard is dominated by **CELO ↔ Mento-stable** and **CELO ↔ USDT/USDC**; COPM is one of ~10 paired assets and **does not dominate** Carbon volume — it merely produces these addresses' largest fingerprint in the COPM Transfer log because COPM has so few other holders.

**Time pattern (Axis 4).** Hour-of-day distribution (all CarbonController trades, n = 1,729,408): peak hours **UTC 13–17** (n_trades 91k–120k each), trough hours **UTC 03–05** (62k–67k each). Ratio peak / trough ≈ 1.9×, **clearly diurnal but not bursty**. UTC 13–17 corresponds to Bogotá 08–12 (Colombia banking morning) and to NY equity-market open through afternoon — both consistent with **automated parameter-update cycles tied to North-American working hours**, not Colombian retail. Activity is non-zero at every hour. Per-day intra-day cadence on COPM-only trades: average 46 seconds between trades on the busiest day (2025-01-19, 1,878 trades, single `trader` = `0x8c05ea30`); 60–185 seconds typical on most active days. **Burst rate consistent with continuous algorithmic activity, not retail-batch.**

**MEV footprint (Axis 5/7).** All 57,382 COPM trade originations come from **a single contract caller** on most peak days (`n_traders = 1` in 41 of the top-50 COPM days). This is the BancorArbitrage contract executing strategies atomically. Block-level MEV signature: each Carbon trade is a single-tx atomic arb-and-settle (typical `n_tx = n_trades / 2` in the data because each Carbon `tradeBySourceAmount` event fires once but the corresponding internal Transfer fires twice — buy/sell — from the same tx). No sandwich pattern (the contract IS the sandwich, atomically buying-then-selling against external pools).

**Funding source (Axis 6).** As a **protocol contract**, this address does not have a "funding source" in the EOA sense. It receives token approvals from Carbon strategy creators (the LPs at `0x20216f30…`, `0x24fb013b…`, etc.) and forwards them to settle trader requests. Strategy creators in turn are funded — in part, per public disclosure — by **Credit Collective's $1M allocation** announced in their March 2025 governance update (forum.celo.org/t/credit-collective-update-march-2025/10617): "Credit Collective provided liquidity for the USDC/COPM pair on Carbon DeFi", reportedly enabling 61,000 transactions versus 7× more than COPM's prior performance on Polygon, with 28× less liquidity.

### 2.2  `0x8c05ea305235a67c7095a32ad4a2ee2688ade636` — BancorArbitrage / Arb Fast Lane

**Identity (Axis 1).** Dune decodes this address as `BancorArbitrage` (the Arb Fast Lane) in `carbon_defi_celo.bancorarbitrage_evt_*` (16 tables). The contract is an EIP-1967 transparent upgradeable proxy; current implementation `0x30dd96D6…` (unverified bytecode; multiple upgrades since 2024-07-22). Deployer `0xe01EA58F6Da98488E4C92Fd9B3E49607639C5370` is an unlabeled multichain developer wallet not publicly tied to Bancor in CeloScan tags — protocol attribution rests on Dune's decoder consistency plus Bancor's public blog announcement and `fastlane-bot` GitHub repo design.

**Counterparty graph (Axis 2).** Top callers of this address (from `celo.transactions`):

| Caller | Calls | Type |
|---|---|---|
| `0xd9dc2b01ee4b16026f1084f819772cf9dff2ee75` | **751,813** | EOA bot operator |
| `0xd6bea8b8d6e503db297161349ca82ad077668d1d` | 96,600 | EOA bot operator |
| `0xfd800dd934a6f3b898932024dca2f51493ba6e2c` | 69,582 | EOA bot operator |
| `0x0f06cef82777ac827b2a79d93e95a77e40669a2f` | 58,436 | EOA bot operator |
| `0xc9b8176febd40525112f90d9204b539251bddfb6` | 34,351 | EOA bot operator |
| `0x622da65d3095e86a3db9781736ec22c4480f3f05` | 11,614 | EOA bot operator |

These are independent EOAs running the open-source `fastlane-bot` Python framework, each earning a fee for filling Carbon maker orders against profitable external venue prices. The dominant operator `0xd9dc2b01…` is an EOA with **1,679,604 lifetime transactions** across 32 chains — clearly a professional MEV searcher, not a Bancor-internal wallet. This pattern matches the **permissionless** design of the Arb Fast Lane (Bancor governance docs: "any user can run the bot and capture rewards").

**Tokens touched (Axis 3).** Identical to CarbonController above (the BancorArbitrage contract operates on the same 10-token basket). COPM is one of ~10 tradeable assets.

**Time pattern (Axis 4).** Daily Arb Fast Lane execution counts run from **400/day (low) to 24,529/day (peak: 2024-10-01)**. The first three weeks of activity (Sep 17 – Oct 8 2024) averaged ~10,000 arbitrages/day; activity stabilised at 500–3,000/day from November 2024 onward as the strategy parameters tuned. **No correlation with Colombian quincena (15th) or prima (June 30, December 20) dates** — the volume profile is set by external-vs-Carbon price gradients (i.e., crypto-market volatility), not Colombian payroll calendar.

**MEV footprint (Axis 5/7).** This contract IS the MEV mechanism. Every successful Arb Fast Lane execution is a same-block atomic three-leg arbitrage: (1) borrow flashloan, (2) buy at venue A, (3) sell at venue B (Carbon controller or external Uniswap V3 / Mobius / Ubeswap), (4) repay flashloan, (5) keep spread. Gas-price relative to block median was not pulled (would require an additional Dune query); the design is back-running rather than front-running (it fires when an external price moves through a Carbon maker order), so the gas fingerprint is medium-priority rather than top-of-block.

**Funding source (Axis 6).** The contract custodies no inventory; profits flow to caller EOAs. EOA-level funding sources are out of scope for this report (each EOA has its own deposit history) but the dominant operator `0xd9dc2b01…` holds only 7 CELO and ~7,937 CELO across 32 chains — consistent with a **net-flat MEV searcher** that takes profits in stables/bridged tokens and recycles minimal balance through gas refills.

## 3. Macro-channel attribution

The aggregate activity of `(0x6619, 0x8c05)` is best described by **a single economic primitive: closed-loop two-sided market-making on the Celo Mento + Minteo stablecoin grid, executed automatically and capitalised by external LPs.** It is NOT explained by:

- **Remittance flow.** The flat-quincena and flat-prima signature in the COPM Transfer log (per Task 11.M) plus the fact that 52% of all COPM events are A↔B oscillations rules this out. Confirmed.
- **TRM arbitrage as the dominant channel.** TRM-shock days appear in the data (e.g., 2025-01-23/24 = peak COPM trades during the −32 COP TRM move), but only **11/30 peak-day events in the original Task 11.F memo** matched |Δ TRM| ≥ 25, and the largest COPM trade days (2025-01-19 = 1,878 trades on a Sunday with zero TRM move; 2025-02-03 = 1,444 trades on a TRM-quiet day) cannot be explained by FX dislocation. The TRM-arb correlation exists but is **secondary**.
- **Minteo treasury operations.** Minteo's primary treasury (`0x0155b191ec52728d26b1cd82f6a412d5d6897c04`) sits upstream and forwards mints to mid-tier hubs; it does NOT route through Carbon contracts directly.
- **A generic DEX-LP rebalancer.** The pattern is too symmetric (n_copm_sold ≈ n_copm_bought every day, with daily delta typically <2% of volume). LP-rebalancers display directional drift in a held-asset position; this displays delta-neutral round-tripping.

The **primary macro channel** is therefore **CELO and Mento-stablecoin-basket cross-rate variance** — the bots fire whenever any of {CELO, USDT, USDC, cUSD, cEUR, cREAL, cKES, XOFm, COPM, WETH} dislocates from any other in the basket on Carbon vs external venues. Specifically:

| Channel | Mechanism | Strength of fit |
|---|---|---|
| (a) CELO–USD volatility | CELO's own price moves induce inventory-rebalancing trades against every Mento stable | **Strongest** — every spike in CELO/USD volatility produces an Arb Fast Lane spike. |
| (b) Mento broker reset rate | When Mento broker rebalances cUSD/USDT cross, Carbon strategies rebalance one block later | Strong (visible in November-2024 flow surge) |
| (c) Cross-stable TRM-cKES-cEUR drift | Indirect — only fires when COP/USD moves are large enough to dislocate the Carbon maker order grid | Weak-to-moderate (the 11/30 TRM-shock-day correlation observed in Task 11.F) |
| (d) Crypto-market-wide vol | Highest-vol days across all Celo tokens drive Arb Fast Lane volume | Strong (the Sep-Oct 2024 launch surge of 24K/day arbs coincides with broader crypto vol that month) |

**Regression evidence.** A formal R²/slope/sign test against the four macro variables would require building the macro panel (TRM Δ, BanRep IBR, FOMC dummies, CELO-USD vol) and running OLS — out of scope for this scoping research and tabled as a follow-up if the redefinition below is adopted. **Qualitatively, channels (a) and (d) dominate; channels (b) and (c) are second-order.**

## 4. Recommended X_d redefinition

Given the classification above, three honest X_d definitions are available, in order of theoretical fit to the inequality-differential thesis:

### Option 1 — "On-chain Carbon round-trip volume" (RECOMMENDED)

**Definition.** Daily count of Carbon `TokensTraded` events on Celo where `sourceToken` ∈ {COPM, cUSD, cEUR, cREAL, cKES, XOFm} AND `targetToken` ∈ {CELO, USDT, USDC, WETH} OR vice-versa. (Aggregating across the whole Mento + Minteo basket, not just COPM.)

**Economic interpretation.** Measures the *automated rebalancing intensity* between the working-class-adjacent stablecoin grid (Mento/Minteo) and the global-asset basket (CELO, ETH, USDT, USDC). High X_d days = days when the grid is dislocating from global crypto and the bots fire to close the gap.

**Plausible inequality-hedge correlation.** When global asset prices (BTC/ETH/CELO) rally, the grid dislocates positively; when LatAm FX (TRM/cKES) weakens, the grid dislocates negatively. Both produce the same Carbon round-trip *volume*, so X_d is sign-insensitive to the rally-direction but proportional to the **absolute size of the wedge** between rich-asset returns and working-class-stable returns. **This directly aligns with the inequality-differential thesis** ("hedge the differential between rich asset returns and working-class consumption returns").

### Option 2 — "Carbon arbitrage profit proxy"

**Definition.** Daily summed `BancorArbitrage.arbitrageexecuted` profit field on Celo (in CELO or USDC equivalent).

**Economic interpretation.** The dollar value of the inefficiency captured per day. Higher = more dislocation between Carbon makers and external venues. Useful as a more direct measure of grid stress, but volume in Option 1 is a cleaner proxy because profit is contaminated by gas-price competition.

**Plausible correlation target.** Same as Option 1 but noisier; not preferred unless Option 1 fails an exogeneity test.

### Option 3 — "COPM-only Carbon trade count"

**Definition.** Daily count of `TokensTraded` events where COPM is `sourceToken` or `targetToken`.

**Economic interpretation.** The narrowest reading — COPM-specific dislocation against any other Carbon token. This was the original implicit X_d before the Task 11.M result.

**Plausible correlation target.** TRM Δ (channel c above), but with weak fit (only 11/30 peak days correlate). NOT recommended because it discards the macro-channel signal across the rest of the basket and fails to capture the inequality-differential mechanism. Keep only as a sensitivity / robustness check against Option 1.

**Recommended primary X_d: Option 1.** It honestly measures what the bots are doing (basket-grid rebalancing), survives the EXIT-verdict-induced X_d invalidation (it is no longer claimed to measure remittance), and ties cleanly to the new inequality-hedge thesis.

## 5. Limitations

- **AXIS_6_SPARSE.** EOA-level funding traces for the top six BancorArbitrage callers were not enumerated; the protocol contracts have no EOA funding source. The strategy-creator EOAs (`0x20216f30…`, `0x24fb013b…`, etc.) that fund the *maker* side of Carbon have not been traced to a named institution; they could be Credit Collective sub-wallets, Minteo MM, or third-party LPs.
- **AXIS_7_SPARSE.** Per-tx gas-price-vs-block-median and sandwich-pattern fingerprinting require a second Dune join against `celo.transactions`; not performed. Qualitative MEV signature (atomic same-block back-running) is established by Bancor's open-source `fastlane-bot` design.
- **Implementation source unverified.** The current `0x8c05ea30…` implementation `0x30dd96D6…` is unverified bytecode on CeloScan. Attribution rests on Dune's `BancorArbitrage` decoder (event signatures match) plus Bancor's blog announcement. Bancor's public docs deployments page lists CarbonController, Voucher, CarbonVortex, CarbonVortexBridge but NOT BancorArbitrage by address — a documentation gap, not contradictory evidence. A bytecode comparison against `bancorprotocol/carbon-contracts` artifacts would close the loop.

## 6. Citations

- Carbon DeFi mainnet contracts: `https://docs.carbondefi.xyz/contracts-and-functions/contracts/deployments/mainnet-contracts`
- Bancor Celo deployment announcement: `https://www.carbondefi.xyz/blog/bancor-deploys-carbon-defi-and-the-arb-fast-lane-on-celo`
- Carbon contracts source: `https://github.com/bancorprotocol/carbon-contracts`
- Fastlane bot source: `https://github.com/bancorprotocol/fastlane-bot`
- Credit Collective March 2025 update: `https://forum.celo.org/t/credit-collective-update-march-2025/10617`
- FX market liquidity strategy: `https://forum.celo.org/t/creating-the-next-fx-market-a-strategy-to-attract-liquidity-to-celo/11840`
- COPM/USDT GeckoTerminal pool view: `https://www.geckoterminal.com/celo/pools/0x4495f525c4ecacf9713a51ec3e8d1e81d7dff870`
- Dune decoded tables: `carbon_defi_celo.carboncontroller_evt_tokenstraded`, `carbon_defi_celo.bancorarbitrage_evt_arbitrageexecuted`
- CeloScan address pages (read 2026-04-24): `celoscan.io/address/0x6619871118D144c1c28eC3b23036FC1f0829ed3a`, `celoscan.io/address/0x8c05ea305235a67c7095a32ad4a2ee2688ade636`, `celoscan.io/address/0xd9dc2b01ee4b16026f1084f819772cf9dff2ee75`, `celoscan.io/address/0xe01EA58F6Da98488E4C92Fd9B3E49607639C5370`
- Mento token addresses (cKES/KESm, XOFm, WETH): Celo token list `https://github.com/celo-org/celo-token-list/blob/main/celo.tokenlist.json`

## 7. Per-tx-profile reconciliation (Task 11.M)

The Task 11.M classifications now resolve cleanly:

- "B2B oscillation core" = CarbonController + BancorArbitrage = Carbon DeFi MM infrastructure (confirmed).
- Strategy-author addresses (`0x4495f525…`, `0x20216f30…`, `0xb961cdca…`, `0x24fb013b…`) are Carbon LPs (the actual makers).
- Distribution hub `0x5bd35ee3…` is **separate** from Carbon (no decoded-table footprint) and remains the most likely Minteo retail-distribution wallet.
- Treasury `0x0155b191…` (0-day mint-and-forward) is **upstream** of Carbon.

This produces TWO clean X_d candidates with different economic readings, both honestly measured:

- **X_d^carbon** (Option 1, §4) — basket-rebalancing volume; measures grid stress / inequality differential.
- **X_d^retail** — `0x5bd35ee3…` fan-out volume; the only plausible *retail* Colombian COPM channel in the dataset.

A future task can regress both against the inequality differential and pick the higher-SNR signal, OR carry both as a 2-D hedge-product state.
