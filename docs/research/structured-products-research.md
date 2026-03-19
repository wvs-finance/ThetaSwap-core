# Structured DeFi Products Research Report

Date: 2026-03-11
Branch: `004-fci-token-vault`
Purpose: Security foundation and architectural precedent analysis for the FCI Token Vault

---

## Executive Summary

This report analyzes six categories of on-chain structured products relevant to the FCI Token Vault design: power perpetuals (Opyn Squeeth), binary options and prediction markets (Gnosis CTF, Polymarket), DeFi options vaults (Ribbon, Thetanuts), options protocols (Lyra, Premia, Panoptic), perpetual structured products (everlasting options), and cross-cutting security patterns. The FCI Token Vault shares architectural DNA with each category but is not identical to any of them.

**Key finding:** The vault's paired LONG/SHORT mint pattern most closely resembles the Gnosis Conditional Token Framework's `splitPosition`/`mergePositions` mechanism, while the power-squared payoff and HWM decay mechanism have direct analogs in Squeeth's normalization factor. The most critical security lessons come from the Aevo/Ribbon oracle exploit (December 2025) and the well-documented ERC-4626 inflation attack vector.

**Relevance mapping to FCI Token Vault:**

| FCI Vault Feature | Closest Analog | Protocol |
|---|---|---|
| Paired LONG/SHORT mint | `splitPosition` / `mergePositions` | Gnosis CTF / Polymarket |
| Power-squared payoff | ETH^2 index tracking | Opyn Squeeth |
| HWM exponential decay | Normalization factor decay | Opyn Squeeth |
| Collateral-backed redemption | ERC-4626 vault shares | Panoptic CollateralTracker |
| Oracle dependency | Price feed integration | All protocols |
| Permissionless poke | Keeper-free funding updates | Squeeth (block-level updates) |
| Diamond proxy oracle reads | Diamond standard facets | Premia Finance |

---

## 1. Opyn Squeeth (Power Perpetuals)

### 1.1 Power-Squared Payoff Mechanism

Squeeth (Squared ETH) is the first power-2 perpetual, tracking ETH^2. It was introduced by Dave White, Dan Robinson, and the Opyn team in August 2021 based on the Paradigm research paper "Power Perpetuals."

The core insight: a power perpetual indexed to price^p gives convex exposure without strikes or expiries. For p=2, if ETH doubles, the Squeeth position quadruples. This is directly analogous to the FCI vault's `((HWM/p*)^2 - 1)+` payoff, except Squeeth tracks the raw price squared while FCI tracks concentration deviation squared.

**How it works:**
- Users mint oSQTH (the Squeeth ERC-20) by depositing ETH collateral into a vault
- oSQTH trades on Uniswap V3 as a spot token
- The oSQTH price should track `normalizationFactor * ethPrice^2`
- Arbitrageurs keep the market price aligned with this index

### 1.2 Vault Architecture and Collateral Management

Source: `opynfinance/squeeth-monorepo`, specifically `Controller.sol` and `VaultLib.sol`.

**Vault structure:**
- Each short position is a vault (struct) with an owner, collateral amount, and short amount (oSQTH debt)
- Minimum collateralization ratio: 200% (1.5x for partially collateralized vaults)
- Collateral is ETH (not stablecoins)
- Vault ID is a simple incrementing uint256

**Key functions:**
- `mintWPowerPerp(vaultId, amount)` -- mint oSQTH against locked collateral
- `burnWPowerPerp(vaultId, amount)` -- burn oSQTH to reduce debt
- `deposit(vaultId)` -- add collateral
- `withdraw(vaultId, amount)` -- remove excess collateral

**Liquidation:** When vault collateralization falls below minimum, liquidators can burn oSQTH to receive `(burned * indexPrice * normalizationFactor * 110%) / ethPrice` in collateral.

**Relevance to FCI vault:** Our vault is simpler because it is fully collateralized by USDC at all times (no leverage, no liquidation needed). The 1:1 USDC backing per token pair eliminates the need for collateralization ratios entirely. This is a deliberate design choice that trades capital efficiency for simplicity and security.

### 1.3 Funding Rate via Normalization Factor

This is the most directly relevant mechanism to our HWM decay.

**How Squeeth implements funding:**
- A global variable `normalizationFactor` (uint128) adjusts the value of all short debt
- Updated via `_applyFunding()`, which runs at most once per block
- The normalization factor decreases over time, making debt cheaper to repay (shorts profit)
- This decrease IS the funding: longs pay shorts through the erosion of their position's index tracking

**Calculation:**
```
newNormFactor = oldNormFactor * e^(-fundingRate * elapsed)
```

Where `fundingRate` is derived from the premium of oSQTH mark price over the index price (ETH^2).

**Storage optimization:** `normalizationFactor` (uint128) and `lastFundingUpdateTimestamp` (uint128) are packed into a single 256-bit storage slot, so updating both costs only one SSTORE.

**Comparison to FCI HWM decay:**

| Aspect | Squeeth normalizationFactor | FCI HWM decay |
|---|---|---|
| Direction | Decreases over time (erodes long value) | Decreases over time (decays peak memory) |
| Trigger | Any contract interaction calls `_applyFunding()` | Permissionless `poke()` or any redeem |
| Rate determination | Market-driven (mark vs index premium) | Fixed half-life parameter (14 days) |
| Scale | WAD via ABDK Math64x64 | WAD via Solady expWad |
| Storage | Packed uint128 pair (1 slot) | Packed uint128+uint64 HWM struct |
| Idempotency | Yes (once per block) | Yes (same timestamp returns same result) |

**Key takeaway:** Squeeth's normalization factor is market-adaptive (funding rate depends on mark-index spread), while our HWM decay is parameter-fixed (constant half-life). This makes our system simpler but less responsive. For an insurance product, fixed decay is appropriate -- it provides predictable premium erosion.

### 1.4 Audit Reports and Security Findings

Squeeth has been audited by Trail of Bits, Akira, and Sherlock, with peer reviews. The contracts carry $10M Sherlock smart contract coverage and a $1M ImmuneFi bug bounty.

**OpenZeppelin Bull Strategy audit findings:**
- Recommended extending emergency shutdown so Bull Strategy can redeem crab and leveraged positions without requiring the Squeeth controller to shut down
- Identified issues in `AuctionBull.fullRebalance` regarding whether excess collateral should be sold or used for further borrowing
- Found the codebase "harder than necessary to reason about" due to numerous casts and helper function calls

**Relevant security patterns from Squeeth:**
- Normalization factor updates are batched (once per block) to prevent manipulation
- Oracle reads use Uniswap V3 TWAP, not spot prices
- Settlement includes a grace period and emergency shutdown mechanism
- Liquidation bonus (10%) incentivizes timely liquidation without excessive extraction

### 1.5 Specific Patterns to Adopt from Squeeth

1. **Packed storage for time-sensitive state:** Pack HWM value + timestamp into minimal slots. Squeeth packs normalization factor + timestamp into one slot using uint128 pair. Our HWM struct (uint128 maxPrice + uint64 lastUpdate) fits in one slot already.

2. **Once-per-block update guard:** `_applyFunding()` checks `lastFundingUpdateTimestamp == block.timestamp` and returns early. Our `poke()` should be idempotent within a block (already specified in design doc).

3. **Exponential decay via library:** Squeeth uses ABDK Math64x64 for exponential computation. We use Solady's `expWad()` which is gas-optimized and well-audited.

---

## 2. Binary Options and Prediction Markets On-Chain

### 2.1 Gnosis Conditional Token Framework (CTF)

Source: `gnosis/conditional-tokens-contracts`, specifically `ConditionalTokens.sol`.

The CTF is the most directly relevant architectural precedent for the FCI vault's paired mint/burn pattern.

**Core mechanism:**
- Implements ERC-1155 multi-token standard
- `splitPosition(collateral, parentCollectionId, conditionId, partition, amount)` -- locks collateral, mints outcome tokens for each partition member
- `mergePositions(collateral, parentCollectionId, conditionId, partition, amount)` -- burns equal amounts of all outcome tokens, returns collateral
- `redeemPositions(collateral, parentCollectionId, conditionId, indexSets)` -- after resolution, burns winning tokens for collateral share

**Position ID construction:**
```
conditionId = keccak256(oracle, questionId, outcomeSlotCount)
collectionId = keccak256(parentCollectionId, conditionId, indexSet)
positionId = keccak256(collateralToken, collectionId)
```

**Paired token invariant:** For a binary condition (2 outcomes), `splitPosition` with amount N creates N YES tokens and N NO tokens. `mergePositions` burns N of each and returns N collateral. This is exactly the `1 LONG + 1 SHORT = 1 USDC` invariant in our vault.

**Key difference from FCI vault:** CTF tokens have discrete resolution (YES=1 or NO=1 after oracle reports outcome). FCI tokens have continuous payoff determined by the HWM at redemption time. There is no "resolution" event -- the vault is perpetual.

### 2.2 Polymarket Architecture

Polymarket uses the Gnosis CTF on Polygon with the following additions:

**NegRiskAdapter:** An adapter contract that enables multi-question markets where exactly one question resolves YES. It converts NO tokens to corresponding YES tokens of other questions. ChainSecurity audited this in April 2024, finding a high level of security.

**Key architectural elements:**
- `ConditionId` derived from questionId (UMA ancillary data hash), oracle (UMA adapter V2), and outcomeSlotCount (always 2 for binary)
- CollectionIds and PositionIds use the same hierarchical construction as base CTF
- ERC-1155 IDs correspond to positionIds
- Resolution via UMA oracle with dispute/challenge period

**Relevant patterns for FCI vault:**
- The `splitPosition`/`mergePositions` model is proven at scale (Polymarket handles hundreds of millions in volume)
- The paired mint guarantee (equal YES + NO minted per split) is enforced at the contract level, not by external logic
- Resolution is separated from trading -- a pattern we adopt differently (perpetual payoff vs discrete resolution)

### 2.3 Patterns to Adopt from CTF

1. **Atomic paired mint/burn:** Our `mint()` must atomically transfer USDC and mint equal LONG + SHORT in a single transaction. No intermediate state where supply is unbalanced.

2. **Pair redemption as the "safe" exit:** CTF's `mergePositions` always returns exact collateral regardless of oracle state. Our `redeemPair()` must always return exact USDC regardless of HWM. This is the risk-free exit.

3. **Single-sided redemption depends on oracle state:** CTF's `redeemPositions` depends on resolution. Our `redeemLong`/`redeemShort` depend on current HWM. Both require careful handling of the oracle dependency.

4. **ERC-1155 vs ERC-20 tradeoff:** CTF uses ERC-1155 (one contract, many token IDs). We chose separate ERC-20 contracts per (pool, strike) pair. ERC-20 is more composable with existing DeFi (AMMs, lending protocols) but requires more deployment gas.

---

## 3. Ribbon Finance / Thetanuts / DOVs

### 3.1 Ribbon Theta Vault Architecture

Source: `ribbon-finance/ribbon-v2`, specifically `RibbonThetaVault.sol` and `VaultLifecycle.sol`.

Ribbon's Theta Vaults sell covered calls or cash-secured puts using Opyn oTokens.

**Round/epoch system:**
- Vaults operate in weekly epochs (rounds)
- Users deposit into a "pending" queue during the active round
- At `rollToNextOption()`, pending deposits are committed and shares are minted
- Shares are minted to `address(this)` (the vault) and users claim later
- No withdrawals during active epoch -- must wait for expiry

**Deposit receipt pattern:**
```solidity
struct DepositReceipt {
    uint16 round;
    uint104 amount;
    uint128 unredeemedShares;
}
```

Each user has a `DepositReceipt` tracking which round they deposited in and how many shares they have not yet claimed.

**Options minting:** Ribbon uses Opyn's Gamma protocol to mint oTokens (ERC-20 options representations). These are auctioned to market makers via Gnosis Auction.

**Relevance to FCI vault:** Our vault is simpler -- no epochs, no pending deposits, no auction. Mint is instant and continuous. However, Ribbon's separation of "deposit" from "active" is instructive for understanding timing attacks.

### 3.2 Aevo/Ribbon Oracle Exploit (December 2025)

This is the single most critical case study for our oracle design.

**What happened:**
- On December 12, 2025, legacy Ribbon DOV vaults (now under Aevo) were drained of ~$2.7M
- Root cause: A December 6 oracle upgrade changed precision to support 18-decimal tokens
- Older assets (wstETH, AAVE, LINK, WBTC) still used 8-decimal precision
- The upgrade inadvertently allowed any user to set prices for newly added assets
- Attacker pushed arbitrary expiry prices into the shared oracle

**Attack method:**
- Exploited price-feed proxies in the Opyn/Ribbon oracle stack
- Pushed false expiry prices at a common expiry timestamp
- Drained funds across multiple vault types

**Response:**
- All Ribbon vaults decommissioned immediately
- DAO proposed 19% haircut on withdrawals (vs actual 32% loss), absorbing ~$400K from DAO positions
- The underlying Opyn protocol was NOT compromised -- vulnerability was specific to Ribbon's oracle configuration

**Critical lessons for FCI vault:**
1. **Never mix precision scales in oracle feeds.** Our vault uses a single Q128-to-WAD conversion boundary (`deltaPlusToPrice`). There is exactly one scale throughout the system.
2. **Oracle upgrades are extremely dangerous.** If we ever upgrade the FCI oracle interface, the vault's oracle address is immutable -- a new vault deployment would be required.
3. **Access control on price setting.** Our FCI oracle computes values from on-chain data (fee growth, liquidity events), not from external price feeds. There is no "set price" function to exploit.
4. **Shared oracle state is an attack surface.** Each FCI vault reads from a single pool's oracle. No shared state across pools.

### 3.3 Thetanuts Finance Architecture

Thetanuts operates Basic Vaults that sell OTM European cash-settled options.

**Key architecture:**
- Users deposit collateral, receive LP tokens
- Vaults sell options to accredited market makers via epochs
- Settlement references centralized exchange prices
- In-protocol settlement with no third-party dependencies

**Upcoming v4:** Moving from AMM model to RFQ (Request for Quote) model for pricing.

**Relevance to FCI vault:** Limited direct relevance. Thetanuts is epoch-based with counterparty auction, while our vault is continuous and counterparty-free. The "theta" naming is coincidental -- our "theta" refers to the Greek letter's association with time decay, mirroring HWM decay.

### 3.4 OpenZeppelin Audit Findings for Ribbon

Key findings relevant to our design:

1. **Reentrancy on external calls:** `startAuction` made external calls without reentrancy protection. Fixed by adding `nonReentrant` modifier. Our vault makes external calls during `mint()` (USDC transferFrom) and `redeemLong`/`redeemShort` (USDC transfer). All must follow CEI pattern.

2. **Pending deposit accounting in fee calculations:** Multiple slightly different implementations of the same collateral-per-share calculation existed. OpenZeppelin flagged this as error-prone. Our vault has a single payoff calculation path (`computePayoff`), eliminating this risk.

3. **Admin centralization:** Ribbon's admin could completely overwrite vault implementation. Our vault has no admin functions -- strike grid is immutable, oracle address is immutable, and half-life is immutable.

---

## 4. Lyra Finance / Premia

### 4.1 Lyra Finance Architecture

Source: `lyra-finance/v1-core`

**Market Maker Vaults (MMVs):**
- LPs deposit stablecoins into per-asset MMVs
- MMVs serve as counterparty for all option traders
- Vaults must be delta-hedged to manage directional risk
- Uses Black-Scholes model for option pricing on-chain

**Greeks computation:**
- Delta measures directional exposure
- Vega measures IV sensitivity -- Lyra charges/discounts fees to maintain net-zero Vega for MMVs
- Theta represents time decay of options value
- All Greeks computed on-chain using Black-Scholes

**Newport upgrade specifics:**
- Introduced partial cash collateralization for short positions
- Uses perpetuals for delta hedging instead of spot
- Insolvency risk: if `netOptionValue > totalAssetValue`, long payouts are scaled down
- Audited by Sherlock, Iosiro, and Trust Security
- $5M Sherlock coverage + $500K bug bounty

**Relevance to FCI vault:** Lyra's Greeks computation is instructive but not directly applicable. Our FCI is itself analogous to an options Greek (it measures fee concentration, which is a second-order property of LP positions). The vault does not need to compute traditional Greeks. However, Lyra's approach of computing payoffs on-chain using well-tested math libraries validates our approach of using Solady's FixedPointMathLib.

### 4.2 Premia Finance Architecture

Source: `docs-solidity.premia.finance`

**Diamond standard implementation (EIP-2535):**
- Gas-optimized Diamond proxy for upgradability
- Segmented logic across facets
- Each vault has three facets: VaultAdmin, VaultBase (ERC-4626), VaultView

**Vault structure:**
- Each vault distinguished by collateral asset + option delta
- Queue acts as liquidity buffer (deposits go to Queue, then to Vault at epoch end)
- Vaults automatically sell cash-secured puts
- ERC-4626 standard for deposit/withdraw/mint/redeem

**SourceHat audit findings:**
- No security issues from outside attackers
- Over 150 passing test cases
- ReentrancyGuard on all publicly-accessible functions
- 3/4 multi-sig timelock for admin operations

**Relevance to FCI vault:** Premia's use of the Diamond standard is directly relevant because our FCI oracle runs as a facet inside the MasterHook diamond. The vault reads `getDeltaPlus()` on the MasterHook proxy address, which routes to the FCI facet via diamond dispatch. Key consideration: diamond storage slot isolation must be verified to prevent cross-facet storage collision.

### 4.3 Panoptic -- Perpetual Options on Uniswap

Source: `panoptic-labs/panoptic-v1-core`

Panoptic is the most architecturally sophisticated protocol in this survey, building perpetual options directly on Uniswap V3 LP positions.

**Core architecture (4 components):**

1. **SemiFungiblePositionManager (SFPM):** Gas-efficient alternative to Uniswap's NFPM. Manages multi-leg positions as ERC-1155 tokens. Supports both minting LP positions (short options) and burning LP positions (long options).

2. **PanopticPool:** Main entry point for options trading. Tracks all positions and manages settlements.

3. **PanopticFactory:** Deploys PanopticPools (one per Uniswap V3 pool, mirroring the factory pattern).

4. **CollateralTracker:** Two instances per pool (one per token). ERC-4626 vault for collateral management and margin accounting.

**CollateralTracker details:**
- Implements full ERC-4626 interface
- Handles commission fees, options premia, intrinsic value payments, P&L distribution
- Calculates liquidation bonuses and forced exercise costs
- Two potential empty reverts from Solmate's `mulDivDown`/`mulDivUp` assembly blocks

**Undercollateralized positions:** Panoptic allows up to 5x capital efficiency on short options, requiring sophisticated margin and liquidation systems. This is the opposite of our fully-collateralized approach.

**OpenZeppelin audit findings for Panoptic:**
- Factory owner can call `updateParameters` on deployed pools and their CollateralTrackers, updating margin ratios, commission fees, collateral ratios, utilizations, and exercise costs
- Substantial refactoring between initial audit and fix review meant another audit was "strongly recommended"
- Recommended monitoring underwater accounts and large AMM price changes for liquidation risk
- Assembly-level empty reverts in ERC-4626 math functions

**Relevance to FCI vault:**
- The CollateralTracker's ERC-4626 approach validates using a standardized vault interface for collateral
- Our vault is much simpler (no margin, no liquidation, no multi-leg positions) but the core deposit/withdraw/share-tracking patterns are relevant
- Panoptic's per-pool factory deployment pattern mirrors our "one vault per pool" design

---

## 5. Perpetual Structured Products

### 5.1 Everlasting Options (Dave White, Paradigm)

Introduced in May 2021, everlasting options are to options what perpetual futures are to futures -- they never expire and use funding to track a target payoff.

**Mechanism:**
- Long positions are maintained by paying funding fees to shorts
- Funding fee = MARK - PAYOFF (difference between market price and theoretical payoff)
- This is analogous to perpetual futures funding (MARK - INDEX) but applied to option payoffs

**Key insight for FCI vault:** Our vault achieves perpetuality differently. Instead of funding fees between longs and shorts, we use HWM decay as a time-value erosion mechanism. The SHORT side benefits from decay (their value increases as HWM decays toward the strike), while the LONG side suffers from decay (their value decreases). This is economically similar to funding but implemented structurally rather than through explicit payments.

**Comparison of perpetuality mechanisms:**

| Mechanism | Everlasting Options | Squeeth | FCI Vault |
|---|---|---|---|
| Perpetuality method | Funding fee (mark-payoff) | Normalization factor decay | HWM exponential decay |
| Who pays | Long pays short | Long pays short (via position erosion) | Long pays short (via HWM decay) |
| Rate determination | Market-driven | Market-driven (mark-index spread) | Parameter-fixed (half-life) |
| Implementation | Explicit payment on interaction | Global variable reduction | Per-strike HWM reduction |
| Keeper requirement | Yes (for funding) | No (batched in any interaction) | No (permissionless poke) |

### 5.2 Rolling and Decay in Perpetual Products

Traditional options require "rolling" -- closing an expiring position and opening a new one at a later expiry. This is expensive and creates liquidity fragmentation across strike/expiry pairs.

Perpetual products eliminate rolling through different mechanisms:
- **Squeeth normalization factor:** Continuously decreases, eroding long value. Rate depends on mark-index spread.
- **Everlasting options funding:** Periodic funding payments aligned to option payoff differences.
- **FCI HWM decay:** Exponential decay with fixed half-life. No market dependency for decay rate.

**Advantage of fixed-rate decay for insurance:** The FCI vault is designed as LP insurance. A predictable, parameter-fixed decay rate means the insurance premium erosion is deterministic and can be priced accurately. Market-adaptive decay (like Squeeth's) would make premium pricing unpredictable.

---

## 6. Key Security Findings Across All Protocols

### 6.1 Common Attack Vectors in Structured Product Vaults

**Oracle manipulation (CRITICAL):**
- The Aevo/Ribbon exploit ($2.7M, December 2025) demonstrated that oracle misconfiguration is the primary risk
- ERC-4626 vault standard does not include safeguards against manipulated exchange rates
- In 2022, over $403.2M was stolen in DeFi via 40+ price oracle manipulation attacks
- Flash loan attacks temporarily skew DEX prices, which oracles propagate to lending/vault protocols

**FCI vault oracle resistance:**
The FCI oracle is structurally resistant to flash-loan manipulation because:
- `getDeltaPlus()` accumulates fee concentration over multiple blocks
- The `addTerm()` function only fires on full position removal (not flash-add/remove)
- `blockLifetime` is floored to 1, limiting same-block manipulation weight
- Cumulative `accumulatedSum` cannot be dominated by a single term

However, the oracle remains vulnerable to:
- Legitimate but extreme fee concentration events (by design -- this is what the insurance covers)
- Oracle staleness if no positions are removed for extended periods
- Diamond proxy misconfiguration (calling wrong address)

**ERC-4626 inflation attack (RELEVANT):**
The "first depositor" attack manipulates exchange rates by front-running the first deposit with a tiny deposit + large donation. Mitigation strategies:
1. Virtual offset (virtual shares + virtual assets in rate computation)
2. Dead shares (initial deposit minted to vault itself)
3. Internal balance tracking (ignore direct transfers)

**FCI vault exposure:** Our vault does NOT use ERC-4626 for the LONG/SHORT tokens. The 1:1 mint ratio (1 USDC = 1 LONG + 1 SHORT) eliminates the share-price-ratio attack surface entirely. There is no exchange rate to manipulate -- tokens are always minted 1:1 with collateral.

**Reentrancy patterns (RELEVANT):**
- Read-only reentrancy exploits view functions during state transitions
- Cross-contract reentrancy through token transfer hooks (ERC-777, ERC-1155 callbacks)
- Settlement/redemption reentrancy during USDC transfer

**FCI vault mitigation:**
- USDC is a standard ERC-20 with no transfer hooks -- no callback reentrancy
- Follow strict CEI (Checks-Effects-Interactions) pattern: update `totalDeposits` and burn tokens BEFORE transferring USDC
- Consider `nonReentrant` modifier on all external state-changing functions as defense-in-depth

### 6.2 Collateral Accounting Edge Cases

**From Ribbon audit:**
- Multiple implementations of the same collateral-per-share calculation led to inconsistency risk
- Pending deposits that are not yet "active" should not participate in profit/loss calculations

**From Panoptic audit:**
- Assembly-level overflows in mulDiv functions can cause empty reverts (hard to debug)
- Parameter updates by privileged roles can change margin requirements on existing positions

**FCI vault considerations:**
- Single payoff calculation path (`computePayoff`) eliminates multiple-implementation risk
- No pending deposits -- mint is instant
- Immutable parameters (strikes, half-life, oracle) prevent privileged parameter changes
- Using Solady's `mulDiv` (well-audited, explicit overflow handling) rather than custom assembly

### 6.3 Invariant Testing Patterns from Audits

Across all audited protocols, the following invariant testing patterns appeared repeatedly:

1. **Conservation of value:** `totalCollateral >= sum(allPositionValues)` -- vault is always solvent
2. **Supply parity:** For paired tokens, `longSupply == shortSupply` at all times
3. **Monotonicity:** Payoffs should be monotonically non-decreasing in the underlying metric
4. **Idempotency:** Repeated state updates within the same block should not change state
5. **Rounding direction:** Always round against the redeemer (vault keeps dust)
6. **Zero-amount handling:** Reject zero-amount mints/redeems to prevent state pollution

**FCI vault invariant checklist (from design spec, validated by this research):**
- `USDC.balanceOf(vault) >= sum(totalDeposits[strike])` -- fully collateralized
- `longToken.totalSupply() == shortToken.totalSupply()` per strike -- paired supply
- `redeemPair(n)` returns exactly `n` USDC -- risk-free unwinding
- `redeemLong(n) + redeemShort(n) = n USDC` -- conservation
- `longPerToken + shortPerToken = WAD` -- payoff sum
- LONG payoff monotonically non-decreasing in HWM
- HWM monotonically non-increasing between oracle spikes
- `poke()` idempotent within same block

---

## 7. Specific Patterns to Adopt and Avoid

### 7.1 Patterns to ADOPT

**A1: Atomic paired mint/burn (from Gnosis CTF)**
The `splitPosition`/`mergePositions` pattern guarantees that LONG and SHORT supply are always equal. Our `mint()` and `redeemPair()` must be atomic -- no intermediate state where one token exists without its pair.

Implementation: In `mint()`, call `longToken.mint()` and `shortToken.mint()` after the USDC transfer succeeds. In `redeemPair()`, burn both tokens before transferring USDC back.

**A2: Packed storage for time-sensitive state (from Squeeth)**
Squeeth packs normalization factor + timestamp into one storage slot. Our `HWM` struct (uint128 maxPrice + uint64 lastUpdate = 192 bits) fits comfortably in one slot with room to spare.

**A3: Once-per-block idempotency guard (from Squeeth)**
The `_applyFunding()` pattern of checking `lastTimestamp == block.timestamp` and returning early prevents redundant computation. Our `poke()` achieves this naturally through the `applyDecay` function (elapsed == 0 returns unchanged).

**A4: CEI pattern for all redemptions (from Ribbon audit)**
Update internal accounting (reduce `totalDeposits`, burn tokens) BEFORE transferring USDC to the redeemer. This prevents reentrancy even without explicit reentrancy guards.

**A5: Immutable configuration (anti-pattern from Ribbon exploit)**
The Aevo/Ribbon exploit was caused by an oracle upgrade. Making oracle address, strikes, and half-life immutable at construction eliminates this entire attack class. If parameters need to change, deploy a new vault.

**A6: Single precision scale throughout (from Ribbon exploit lesson)**
The Ribbon exploit exploited a precision mismatch between 8-decimal and 18-decimal assets. Our vault uses WAD (1e18) for all internal math, with a single Q128-to-WAD conversion at the oracle boundary (`deltaPlusToPrice`). No other precision conversions exist in the system.

**A7: ReentrancyGuard as defense-in-depth (from Premia audit)**
Even though CEI pattern should prevent reentrancy, adding `nonReentrant` modifier to `mint()`, `redeemPair()`, `redeemLong()`, and `redeemShort()` provides defense-in-depth at minimal gas cost.

**A8: Vault-only mint/burn on tokens (from all protocols)**
LONG and SHORT tokens should have `onlyVault` modifiers on `mint()` and `burn()`. This is already specified in the design doc. No protocol surveyed allows arbitrary minting of structured position tokens.

### 7.2 Patterns to AVOID

**X1: Epoch/round-based deposits (from Ribbon)**
Ribbon's weekly epoch system creates complexity with pending deposits, unmatched shares, and withdrawal timing. Our continuous mint/redeem model avoids all epoch-related complexity.

**X2: ERC-4626 for structured position tokens (from Panoptic audit findings)**
ERC-4626's share-price-ratio is vulnerable to inflation attacks and rounding manipulation. Our 1:1 token-to-collateral mint ratio eliminates this entirely. ERC-4626 is appropriate for fungible vault shares but not for structured payoff tokens.

**X3: Upgradeable oracle configuration (from Aevo exploit)**
Never allow oracle address or precision parameters to be changed post-deployment. Immutable is the correct choice.

**X4: Multiple implementations of the same calculation (from Ribbon audit)**
OpenZeppelin flagged Ribbon for having multiple "essentially equivalent" implementations of the collateral-per-share calculation. We must have exactly one `computePayoff` function used by all code paths.

**X5: Admin override on critical parameters (from Panoptic audit)**
Panoptic's Factory owner can update margin ratios, commission fees, and exercise costs on deployed pools. This creates trust assumptions and attack surface. Our vault has zero admin functions.

**X6: Assembly-level math without explicit revert messages (from Panoptic audit)**
Panoptic's CollateralTracker inherits Solmate's assembly-level mulDiv which can empty-revert on overflow. Use Solady's FixedPointMathLib which has explicit overflow checks and is actively maintained.

**X7: Shared oracle state across multiple vaults/products (from Aevo exploit)**
The Aevo attacker pushed false prices into a shared oracle affecting multiple vault types. Each FCI vault reads from its own pool's oracle instance. No shared mutable oracle state exists.

### 7.3 Code Patterns for Key Operations

**Paired mint pattern (inspired by Gnosis CTF `splitPosition`):**
```
1. Validate strikeIndex in range
2. Validate amount > 0
3. transferFrom(msg.sender, address(this), usdcAmount)
4. totalDeposits[strike] += usdcAmount
5. longToken.mint(msg.sender, usdcAmount)
6. shortToken.mint(msg.sender, usdcAmount)
7. emit Mint(msg.sender, strikeIndex, usdcAmount)
```

**Single-sided redemption pattern (CEI):**
```
1. Validate strikeIndex and amount
2. Compute payoff = computePayoff(hwm, strike) // view
3. Compute payout = amount * longPerToken / WAD
4. Burn longToken from msg.sender (checks allowance)
5. totalDeposits[strike] -= amount  // Note: reduces by full token amount
6. Transfer payout USDC to msg.sender
7. emit RedeemLong(msg.sender, strikeIndex, amount, payout)
```

**Note on single-sided redemption accounting:** When only LONG tokens are redeemed, the collateral pool must still back the outstanding SHORT tokens. The `totalDeposits` must track both sides. Specifically: if `n` LONG tokens are redeemed for `payout` USDC, there are still `n` SHORT tokens outstanding that are backed by `(n - payout)` USDC. The accounting must ensure `USDC.balanceOf(vault) >= sum(shortOutstanding * shortValuePerToken)` at all times.

This is a subtle but critical invariant that is not present in the simple CTF model (where resolution is binary). Our continuous payoff model means single-sided redemptions change the collateral ratio for the remaining side.

**Oracle read pattern (inspired by Squeeth `_applyFunding`):**
```
1. Read deltaPlus = oracle.getDeltaPlus(poolKey, reactive)
2. Convert: pIndex = deltaPlusToPrice(deltaPlus)
3. Compute decayed = applyDecay(hwm, block.timestamp, halfLife)
4. newHwm = max(pIndex, decayed)
5. Store newHwm and block.timestamp
6. emit HWMUpdated(strikeIndex, newHwm, pIndex)
```

---

## 8. Summary of Recommendations

### Critical (must implement)

1. **Immutable oracle, strikes, and half-life** -- prevents the Aevo-class oracle upgrade attack
2. **CEI pattern on all redemptions** -- prevents reentrancy during USDC transfer
3. **Single `computePayoff` implementation** -- prevents the Ribbon-class calculation inconsistency
4. **Atomic paired mint/burn** -- ensures supply parity invariant
5. **Q128-to-WAD conversion at a single boundary** -- prevents precision mismatch attacks
6. **Comprehensive fuzz testing of all invariants** -- validated by every audit in this survey

### Important (should implement)

7. **ReentrancyGuard on all external state-changing functions** -- defense-in-depth
8. **Reject zero-amount operations** -- prevents state pollution and gas-griefing
9. **Event emission for all state changes** -- enables off-chain monitoring
10. **Packed HWM storage** -- gas optimization following Squeeth pattern

### Nice-to-have (consider for future)

11. **Emergency pause mechanism** -- but only for pausing new mints, not blocking redemptions
12. **Oracle staleness check** -- revert if oracle has not been updated within N blocks
13. **Factory pattern** -- deploy vaults for new pools via factory (following Panoptic pattern)

---

## Sources

### Opyn Squeeth / Power Perpetuals
- [Opyn Squeeth Controller.sol](https://github.com/opynfinance/squeeth-monorepo/blob/main/packages/hardhat/contracts/core/Controller.sol)
- [Opyn Squeeth VaultLib.sol](https://github.com/opynfinance/squeeth-monorepo/blob/main/packages/hardhat/contracts/libs/VaultLib.sol)
- [Power Perpetuals -- Paradigm](https://www.paradigm.xyz/2021/08/power-perpetuals)
- [Everlasting Options -- Paradigm](https://www.paradigm.xyz/2021/05/everlasting-options)
- [Everything is a Perp -- Paradigm](https://www.paradigm.xyz/2024/03/everything-is-a-perp)
- [Squeeth Primer -- Opyn](https://scribe.rip/opyn/squeeth-primer-a-guide-to-understanding-opyns-implementation-of-squeeth-a0f5e8b95684)
- [Squeeth Insides Volume 1: Funding and Volatility](https://medium.com/opyn/squeeth-insides-volume-1-funding-and-volatility-f16bed146b7d)
- [Squeeth Audits and Insurance](https://opyn.gitbook.io/squeeth/security/audits-and-insurance)
- [OpenZeppelin Opyn Bull Strategy Audit](https://www.openzeppelin.com/news/opyn-bull-strategy-contracts-audit)

### Binary Options / Prediction Markets
- [Gnosis Conditional Tokens -- ConditionalTokens.sol](https://github.com/gnosis/conditional-tokens-contracts/blob/master/contracts/ConditionalTokens.sol)
- [Conditional Tokens Developer Guide](https://conditional-tokens.readthedocs.io/en/latest/developer-guide.html)
- [Splitting and Merging Positions -- Gnosis](https://conditionaltokens-docs.dev.gnosisdev.com/conditionaltokens/docs/devguide05/)
- [Polymarket CTF Overview](https://docs.polymarket.com/developers/CTF/overview)
- [Polymarket Conditional Token Examples](https://github.com/Polymarket/conditional-token-examples)
- [ChainSecurity Polymarket NegRiskAdapter Audit](https://www.chainsecurity.com/security-audit/polymarket-negriskadapter)
- [ChainSecurity Polymarket Conditional Tokens Audit](https://reports.chainsecurity.com/Polymarket/ChainSecurity_Polymarket_ConditionalTokens_Audit.pdf)

### Ribbon Finance / DOVs
- [Ribbon Finance Theta Vault Architecture](https://docs.ribbon.finance/theta-vault/ribbon-v2)
- [Ribbon Finance v2 GitHub](https://github.com/ribbon-finance/ribbon-v2)
- [Ribbon Finance Options Architecture](https://docs.ribbon.finance/theta-vault/theta-vault/options-architecture)
- [OpenZeppelin Ribbon Finance Audit](https://blog.openzeppelin.com/ribbon-finance-audit)
- [Aevo Ribbon Vault Exploit -- The Block](https://www.theblock.co/post/382461/aevos-legacy-ribbon-dov-vaults-exploited-for-2-7-million-following-oracle-upgrade)
- [Halborn Aevo/Ribbon Hack Explained](https://www.halborn.com/blog/post/explained-the-aevo-ribbon-finance-hack-december-2025)
- [Rekt -- Aevo Rekt](https://rekt.news/aevo-rekt)

### Lyra / Premia / Panoptic
- [Lyra Finance v1-core GitHub](https://github.com/lyra-finance/v1-core)
- [Lyra Newport Upgrade](https://insights.derive.xyz/newport-upgrade/)
- [Premia Solidity Docs](https://docs-solidity.premia.finance/)
- [Premia Diamond Audit -- SourceHat](https://sourcehat.com/audits/PremiaDiamond/)
- [Premia Audit -- Hacken](https://audits.hacken.io/premia-finance/)
- [Knox/Premia System Architecture](https://docs.knox.premia.finance/developers/system-architecture)
- [Panoptic v1-core GitHub](https://github.com/panoptic-labs/panoptic-v1-core)
- [Panoptic Smart Contracts Introduction](https://panoptic.xyz/research/introducing-panoptic-smart-contracts)
- [OpenZeppelin Panoptic Audit](https://www.openzeppelin.com/news/panoptic-audit)
- [Panoptic CollateralTracker Docs](https://panoptic.xyz/docs/contracts/V1.1/contract.CollateralTracker)

### Thetanuts
- [Thetanuts Finance Docs](https://docs.thetanuts.finance/)
- [Deep-dive into Thetanuts v3](https://medium.com/@benhwx/a-deep-dive-into-thetanuts-finance-v3-d134b9c7b43d)

### Security / Oracle / ERC-4626
- [OpenZeppelin ERC-4626 Inflation Attack Defense](https://www.openzeppelin.com/news/a-novel-defense-against-erc4626-inflation-attacks)
- [ERC-4626 Inflation Attack Discussion -- EIP Fellowship](https://ethereum-magicians.org/t/address-eip-4626-inflation-attacks-with-virtual-shares-and-assets/12677)
- [Oracle Manipulation $700K Exploit Analysis -- The Block](https://www.theblock.co/post/348785/analysis-of-700k-oracle-manipulation-exploit-highlights-vulnerabilities-in-defi-vaults)
- [Price Oracle Manipulation Attacks Guide -- Cyfrin](https://www.cyfrin.io/blog/price-oracle-manipulation-attacks-with-examples)
- [TWAP Oracle Attacks Paper](https://eprint.iacr.org/2022/445.pdf)
- [Uniswap v3 TWAP Oracles in PoS](https://blog.uniswap.org/uniswap-v3-oracles)
- [DeFi Derivatives Landscape](https://github.com/0xperp/defi-derivatives)
