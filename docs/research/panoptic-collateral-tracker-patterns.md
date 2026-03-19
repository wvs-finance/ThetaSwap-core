# Panoptic CollateralTracker Pattern Analysis for ERC-6909 Paired-Mint Vault

**Date**: 2026-03-12
**Branch**: 004-fci-token-vault
**Source**: [code-423n4/2025-12-panoptic](https://github.com/code-423n4/2025-12-panoptic)
**Primary file analyzed**: `contracts/CollateralTracker.sol` (1664 lines)

---

## Executive Summary

The Panoptic CollateralTracker is an ERC-4626 vault that manages one side of a two-token options collateral system. Each Panoptic pool deploys two CollateralTracker instances (one per Uniswap pool token), coordinated by a single PanopticPool contract. The design contains several patterns directly relevant to our ERC-6909 CollateralCustodian with paired LONG/SHORT tokens and the conservation invariant `1 LONG + 1 SHORT = 1 USDC`.

This analysis extracts ten categories of patterns, evaluating each for applicability to our design. The most transferable patterns are: (1) the three-variable internal accounting model, (2) directional rounding discipline, (3) virtual-share inflation resistance, (4) the `onlyPanopticPool` access control model, and (5) insolvency detection with graceful degradation. Several patterns require adaptation because our vault has a fundamentally different share model -- paired mint/burn with deterministic 1:1 backing rather than variable-rate share pricing.

---

## 1. Collateral Accounting Patterns

### What Panoptic Does

The CollateralTracker maintains three core accounting variables beyond ERC-20 `balanceOf`:

| Variable | Type | Purpose |
|----------|------|---------|
| `s_depositedAssets` | `uint128` | Assets physically held by the PanopticPool (line 129) |
| `s_assetsInAMM` | `uint128` | Assets deployed into Uniswap AMM positions (line 132) |
| `s_creditedShares` | `uint256` | Virtual shares credited for long positions exceeding rehypothecation threshold (line 135) |

The key accounting identity is:

```
totalAssets() = s_depositedAssets + s_assetsInAMM + unrealizedInterest
totalSupply() = _internalSupply + s_creditedShares
```

This separation is critical: `totalAssets()` explicitly **excludes** fees reserved for short options and donations (line 500-501). The vault tracks what it *should* have, not what it *does* have via `balanceOf(address(this))`. This makes it immune to donation-based manipulation of the share price.

The per-user interest state is packed into `s_interestState[user]` as a `LeftRightSigned`:
- Left 128 bits: `netBorrows` (shorts minus longs, the borrowing exposure)
- Right 128 bits: User's borrow index snapshot (compound interest checkpoint)

### Applicability to Our Design

**Directly applicable**: The pattern of tracking "what the vault should hold" rather than relying on actual token balances is essential for our CollateralCustodian. We should maintain:

| Our Variable | Panoptic Analog | Purpose |
|---|---|---|
| `s_totalDeposited` | `s_depositedAssets` | Total USDC deposited, tracks the conservation invariant |
| `s_longSupply` | N/A (new) | Total LONG tokens outstanding |
| `s_shortSupply` | N/A (new) | Total SHORT tokens outstanding |

The invariant `s_longSupply == s_shortSupply == s_totalDeposited` enforces conservation at the storage level. We do not need `s_assetsInAMM` or `s_creditedShares` since we have no rehypothecation or AMM deployment.

**Not applicable**: The interest rate accumulator (`s_marketState` with packed borrow index, epoch, rate, unrealized interest) is specific to Panoptic's lending model. We have no borrowing.

---

## 2. Rounding Discipline

### What Panoptic Does

Panoptic applies a strict directional rounding policy across all conversion paths:

| Operation | Direction | Rounding | Rationale | Line |
|-----------|-----------|----------|-----------|------|
| `deposit()` | assets -> shares | Round DOWN (`mulDiv`) | Depositor gets fewer shares, benefits vault | 548 |
| `mint()` | shares -> assets | Round UP (`mulDivRoundingUp`) | Depositor pays more assets, benefits vault | 602 |
| `withdraw()` | assets -> shares-to-burn | Round UP (`mulDivRoundingUp`) | Withdrawer burns more shares, benefits vault | 680 |
| `redeem()` | shares -> assets | Round DOWN (`mulDiv`) via `convertToAssets` | Withdrawer gets fewer assets, benefits vault | 527 |
| Interest settlement | interest -> shares-to-burn | Round UP (`mulDivRoundingUp`) | Borrower pays more, benefits lenders | 906 |
| Commission | notional -> fee shares | Round UP (`mulDivRoundingUp`) | Protocol collects at least the fee | 1557 |
| Credit delta (creation) | long amount -> shares | Round UP (`mulDivRoundingUp`) | More shares credited conservatively | 1422 |
| Credit delta (close) | long amount -> shares | Round DOWN (`mulDiv`) | Fewer shares returned, conservative | 1427 |

The universal principle: **rounding always favors the vault/protocol over the individual user**. This prevents rounding-based value extraction.

Additionally, Panoptic clamps unrealized interest when per-user rounding accumulation exceeds the global accumulator (line 954):
```solidity
if (burntInterestValue > _unrealizedGlobalInterest) {
    _unrealizedGlobalInterest = 0;
} else { ... }
```

This handles the fact that `ceil * ceil` is not idempotent -- repeated rounding up of individual user settlements can exceed the aggregate.

### Applicability to Our Design

**Directly applicable, but simpler**. Our vault has a 1:1 backing ratio by construction: 1 USDC = 1 LONG + 1 SHORT always. There is no variable share price, so the deposit/withdraw paths do not need mulDiv rounding at all -- they are exact integer operations.

However, rounding becomes relevant at **redemption time** when the oracle determines the LONG/SHORT payoff split. If the oracle says LONG gets 0.6 USDC and SHORT gets 0.4 USDC per unit, and a user holds 3 tokens:
- LONG payout: `3 * 0.6 = 1.8` USDC -- but in fixed-point this could be `1_800_000` or `1_799_999` depending on precision
- SHORT payout: `3 * 0.4 = 1.2` USDC

The rounding rule should be: **round DOWN on payout to each side, with any dust (up to 1 wei per redemption) retained by the vault**. This preserves the conservation invariant even under rounding.

**Key takeaway**: Adopt the "always round against the user, in favor of the vault" principle. Document explicitly which direction every conversion rounds and why.

---

## 3. Reentrancy and CEI Patterns

### What Panoptic Does

The CollateralTracker itself does **not** use a reentrancy guard. Instead, the protocol layers defense:

1. **SemiFungiblePositionManager**: Uses `TransientReentrancyGuard` (from Solmate) with `nonReentrant` on `mintTokenizedPosition` and `burnTokenizedPosition` (SFPM line 586, 626). This is the entry point for all AMM interactions.

2. **CollateralTracker CEI ordering**: The deposit/withdraw functions follow a specific order that is **not strict CEI** but relies on the access control boundary:

   - `deposit()` (line 557-588): Accrues interest, computes shares, mints shares, updates `s_depositedAssets`, THEN transfers tokens in (via `_settleCurrencyDelta` for V4 or `safeTransferFrom` for V3). Note: for V3, the transfer happens BEFORE mint+state-update; for V4, it happens AFTER. This is safe because the V4 callback `unlockCallback` validates `msg.sender == poolManager`.

   - `withdraw()` (line 690-733): Accrues interest, checks max, computes shares, checks allowance, burns shares, updates `s_depositedAssets`, THEN transfers tokens out. This is CEI: state changes complete before the external transfer call.

   - `redeem()` (line 817-858): Same pattern as withdraw -- burn, update state, then transfer out.

3. **Transfer restrictions**: `transfer()` and `transferFrom()` first accrue interest, then check that the sender has zero open positions before allowing the transfer (line 400-411). This prevents collateral drain via share transfers.

4. **Callback validation**: The `unlockCallback` validates `msg.sender == poolManager()` (line 450).

### Applicability to Our Design

**Directly applicable with one critical difference**. Our CollateralCustodian performs paired mints via ERC-6909, which means `deposit()` must:
1. Transfer USDC in (external call)
2. Mint LONG token to depositor (state change)
3. Mint SHORT token to depositor (state change)

Recommended ordering:
1. Transfer USDC in first (CEI: get the money before making promises)
2. Update `s_totalDeposited` (internal accounting)
3. Mint LONG + SHORT atomically (ERC-6909 state changes)

For `redeem()`:
1. Verify caller holds both LONG and SHORT (or sufficient of one side after oracle settlement)
2. Burn LONG + SHORT (state changes)
3. Update `s_totalDeposited`
4. Transfer USDC out (external call last)

Since we use ERC-6909 (multi-token on a single contract), there are no external calls between the LONG and SHORT mints -- they are just storage writes on `balanceOf[id][account]`. This is inherently safer than Panoptic's two-contract model.

**Recommendation**: Use a transient reentrancy guard on `deposit()` and `redeem()` to prevent cross-function reentrancy via USDC transfer callbacks (e.g., ERC-777 tokens or future USDC upgrades with hooks). Panoptic delegates this to the SFPM layer, but since we are the outermost contract, we must guard ourselves.

---

## 4. Multi-Token Coordination

### What Panoptic Does

Panoptic deploys **two independent CollateralTracker instances** per pool, one per Uniswap token. They are coordinated by the PanopticPool contract:

- **Immutable pairing**: Each CollateralTracker stores `underlyingIsToken0` (a boolean at calldata offset 20, line 162-168) identifying which side it manages. The PanopticPool stores both addresses as immutable args (`collateralToken0()` at offset 0, `collateralToken1()` at offset 20 in PanopticPool).

- **Parallel settlement**: When a position is minted or burned, PanopticPool calls `settleMint`/`settleBurn` on **both** CollateralTrackers independently (PanopticPool lines 790-811):
  ```
  collateralToken0().settleMint(owner, longAmounts.rightSlot(), shortAmounts.rightSlot(), ...)
  collateralToken1().settleMint(owner, longAmounts.leftSlot(), shortAmounts.leftSlot(), ...)
  ```
  The `LeftRightSigned` type packs token0 amounts in the right slot and token1 amounts in the left slot.

- **Liquidation coordination**: During liquidation, PanopticPool delegates virtual shares on **both** trackers, performs the liquidation logic, then calls `settleLiquidation` on both (PanopticPool lines 1516-1590).

- **Cross-tracker invariant**: The two trackers are independent in share price and utilization but linked through the PanopticPool's solvency checks. A user's total collateral is evaluated as `collateralToken0.assetsOf(user)` + `collateralToken1.assetsOf(user)` (with appropriate cross-collateral haircuts managed by the RiskEngine).

### Applicability to Our Design

**Fundamentally different architecture, but the coordination principle applies**. Panoptic uses two separate ERC-20 contracts with an external coordinator. We use a single ERC-6909 contract with two token IDs (LONG_ID and SHORT_ID).

Our advantages:
- **Atomic paired operations**: Minting LONG + SHORT is two storage writes in the same contract -- no cross-contract coordination needed.
- **Single source of truth**: The conservation invariant `balanceOf[LONG_ID][all_holders] == balanceOf[SHORT_ID][all_holders] == s_totalDeposited` is enforced within one contract.
- **No cross-contract call overhead**: Panoptic's PanopticPool must make 2 external calls per settlement. We make zero.

What to adopt:
- **The `LeftRightSigned` packing pattern** for return values where we need to communicate LONG/SHORT amounts together. Consider a similar packed type for oracle payoff ratios.
- **The parallel-but-independent accounting model**: Even though LONG and SHORT live in one contract, track their supplies independently (`s_longSupply`, `s_shortSupply`) and verify equality as an invariant in critical paths.

---

## 5. Share Price Manipulation Resistance

### What Panoptic Does

Three specific defenses:

#### 5a. Virtual Shares (Inflation Attack Resistance)

At initialization (line 284-300):
```solidity
_internalSupply = 10 ** 6;   // virtual shares
s_depositedAssets = 1;         // virtual assets
```

The initial share price is `1 / 10^6`. This means an attacker trying the classic "first depositor" inflation attack must donate `10^6` times more value to manipulate the share price. The comment explicitly states: "these virtual shares function as a multiplier for the capital requirement to manipulate the pool price" (line 290).

#### 5b. Internal Asset Tracking (Donation Attack Resistance)

`totalAssets()` returns `s_depositedAssets + s_assetsInAMM + unrealizedInterest` (line 503-507). It does **not** read the contract's actual token balance. This means sending tokens directly to the contract (donation) has zero effect on the share price. The surplus is simply untracked and unrecoverable.

#### 5c. Flash Deposit Prevention (Utilization Manipulation Resistance)

The `_poolUtilization()` function uses transient storage to track the **maximum** utilization seen within a transaction (lines 1137-1153):
```solidity
bytes32 slot = UTILIZATION_TRANSIENT_SLOT;
assembly { storedUtilization := tload(slot) }
if (storedUtilization > poolUtilization) {
    return storedUtilization;
} else {
    assembly { tstore(slot, poolUtilization) }
    return poolUtilization;
}
```

This prevents flash deposits from temporarily lowering utilization to reduce interest rates within a single transaction. The utilization can only ratchet **up** within a tx, never down.

#### 5d. Deposit Cap

Deposits are capped at `type(uint104).max` (line 559), roughly 2 * 10^31. This prevents overflow attacks in the accounting math.

### Applicability to Our Design

**5a -- Partially applicable**. Our vault has a fixed 1:1 exchange rate by construction. There is no variable share price to manipulate. However, if the vault ever has zero deposits and someone deposits 1 wei of USDC, they should get exactly 1 wei of LONG + 1 wei of SHORT. No virtual shares needed because there is no price ratio to inflate.

However, we should still consider: **what if `s_totalDeposited` is zero and the contract holds dust USDC from a previous rounding residual?** We should initialize with `s_totalDeposited = 0` and ensure the first deposit path handles the zero-supply case correctly. Since our "share price" is always 1:1 by construction, the inflation attack vector does not apply.

**5b -- Directly applicable and critical**. We MUST track deposited assets internally via `s_totalDeposited` and never rely on `USDC.balanceOf(address(this))`. Someone could donate USDC to the contract to try to break the invariant. Our conservation invariant should be:
```
s_totalDeposited == s_longSupply == s_shortSupply
USDC.balanceOf(address(this)) >= s_totalDeposited  (always, with >= not ==)
```

**5c -- Not applicable**. We have no utilization-based interest rate.

**5d -- Applicable**. Cap deposits at a sane maximum (e.g., `type(uint128).max` or a governance-set parameter) to prevent overflow in any downstream math.

---

## 6. Liquidation and Insolvency Handling

### What Panoptic Does

#### 6a. Interest Insolvency Detection

In `_accrueInterest()` (line 886-976), when a user owes more interest than their share balance can cover:

```solidity
if (shares > userBalance) {
    if (!isDeposit) {
        // Insolvent case: Pay what you can
        burntInterestValue = Math.mulDiv(userBalance, _totalAssets, totalSupply()).toUint128();
        emit InsolvencyPenaltyApplied(owner, userInterestOwed, burntInterestValue, userBalance);
        _burn(_owner, userBalance);
        // DO NOT update index -- debt continues to compound
        userBorrowIndex = userState.rightSlot();
    } else {
        // If depositing, skip settlement entirely -- keep old index
        burntInterestValue = 0;
        userBorrowIndex = userState.rightSlot();
    }
}
```

Key insight: **the user's borrow index is NOT updated when insolvent**. This means their debt continues to compound from the original checkpoint. They burned what they could, but still owe the remainder plus ongoing interest. This is a deliberate design choice -- insolvency does not forgive debt.

The `InsolvencyPenaltyApplied` event (line 83-94) logs the shortfall for off-chain monitoring.

#### 6b. Liquidation Flow

The `settleLiquidation()` function (line 1262-1362) handles two cases:
- **Negative bonus** (liquidatee pays liquidator): Liquidator provides assets, they are deposited, shares minted to liquidatee, then virtual delegation is revoked.
- **Positive bonus** (liquidator receives from liquidatee): Virtual delegation is revoked, then shares are transferred or minted. The protocol-loss case (line 1325-1354) uses a formula `N = Z(Y - T) / (X - Z)` to compute shares to mint when the liquidatee's balance is insufficient, diluting all shareholders proportionally.

#### 6c. Virtual Delegation Mechanism

Before liquidation, the PanopticPool calls `delegate(liquidatee)` which adds `type(uint248).max` to the user's balance WITHOUT updating `_internalSupply` (line 1221-1233). This ensures the liquidatee's position can be closed even if they lack shares. After liquidation, `revoke()` removes the virtual balance and fixes up `_internalSupply` if phantom shares were consumed (line 1242-1255).

### Applicability to Our Design

**6a -- Adapted pattern useful**. We do not have borrowing or interest, but we may have a scenario where the oracle determines that one side's payoff is zero (e.g., LONG payoff = 0, SHORT payoff = 1 USDC). In this case, LONG holders get nothing. This is not "insolvency" but "zero payoff" -- it is expected behavior. No special insolvency handling needed.

However, if we add any fee mechanism that accrues over time, the insolvency detection pattern (checking if `shares_owed > balance`) is directly reusable.

**6b -- Not directly applicable**. We have no liquidation mechanism. The paired LONG/SHORT structure with full USDC backing means the vault is always solvent by construction. 1 LONG + 1 SHORT can always be redeemed for exactly 1 USDC regardless of oracle state.

**6c -- Not applicable**. Virtual delegation is specific to Panoptic's "close position on behalf of liquidatee" flow.

**Key takeaway for our design**: The conservation invariant `1 LONG + 1 SHORT = 1 USDC` makes insolvency impossible at the vault level. This is a significant simplification over Panoptic's model. Document this property prominently as a security invariant.

---

## 7. View Functions for Integrators

### What Panoptic Does

The CollateralTracker exposes a rich set of view functions:

| Function | Purpose | Line |
|----------|---------|------|
| `convertToShares(assets)` | Stateless conversion at current rate | 520 |
| `convertToAssets(shares)` | Stateless conversion at current rate | 527 |
| `previewDeposit(assets)` | Shares you'd get for depositing `assets` | 547 |
| `previewMint(shares)` | Assets you'd need to mint `shares` | 599 |
| `previewWithdraw(assets)` | Shares you'd burn to withdraw `assets` | 677 |
| `previewRedeem(shares)` | Assets you'd get for redeeming `shares` | 807 |
| `maxDeposit(address)` | Max depositable (= `type(uint104).max`) | 540 |
| `maxMint(address)` | Max mintable shares | 592 |
| `maxWithdraw(owner)` | Max withdrawable (limited by available + position check) | 651 |
| `maxRedeem(owner)` | Max redeemable shares | 795 |
| `assetsOf(owner)` | User's share balance converted to assets | 534 |
| `getPoolData()` | Returns (depositedAssets, insideAMM, creditedShares, utilization) | 312 |
| `borrowIndex()` | Current global borrow index | 331 |
| `interestState(user)` | User's borrow index + net borrows | 357 |
| `owedInterest(owner)` | Current interest owed by user | 1083 |
| `previewOwedInterest(owner)` | Simulated interest if compounded now | 1123 |
| `assetsAndInterest(owner)` | Combined assets + owed interest | 1091 |
| `interestRate()` | Current per-second interest rate | 1039 |

**Stale state handling**: View functions like `_poolUtilizationView()` (line 1158) read directly from storage without side effects. They do NOT update transient storage or accrue interest. This means view-function results can be stale by up to one epoch (4 seconds). The `previewOwedInterest` function explicitly simulates accrual to current block.

### Applicability to Our Design

**Directly applicable -- we need an equivalent set**. For the CollateralCustodian with ERC-6909:

| Our Function | Panoptic Analog | Purpose |
|---|---|---|
| `previewDeposit(usdcAmount)` | `previewDeposit` | Returns (longAmount, shortAmount) -- always equal to usdcAmount |
| `previewRedeem(longAmount, shortAmount)` | `previewRedeem` | Returns USDC amount -- requires oracle lookup |
| `previewPayoff(longAmount)` | New | USDC payoff for LONG-only redemption (requires oracle) |
| `previewPayoff(shortAmount)` | New | USDC payoff for SHORT-only redemption (requires oracle) |
| `maxDeposit(address)` | `maxDeposit` | Deposit cap |
| `maxRedeem(owner, tokenId)` | `maxRedeem` | Max redeemable for a given side |
| `totalDeposited()` | `totalAssets` | Total USDC backing |
| `oraclePrice()` | N/A | Current oracle value determining LONG/SHORT split |
| `payoffRatio()` | N/A | Current (longPayoff, shortPayoff) per unit, summing to 1e18 |

**Critical consideration**: Our `previewPayoff` functions depend on the oracle. If the oracle is stale, the preview is stale. We should either:
1. Revert if the oracle is stale beyond a threshold (Panoptic does this via `Errors.StaleOracle`)
2. Return the preview with a staleness flag

Panoptic's approach of separating "view that reads storage" from "state-modifying that updates accumulators" is good practice. All our view functions should be pure reads with no side effects.

---

## 8. Storage Layout and Gas Optimization

### What Panoptic Does

#### 8a. Bit-Packed MarketState (Single Slot)

The `MarketState` type packs four fields into one `uint256` (see `MarketState.sol`):

```
Bits 0-79   (80 bits):  borrowIndex (WAD, starts at 1e18)
Bits 80-111 (32 bits):  marketEpoch (block.timestamp / 4)
Bits 112-149 (38 bits): rateAtTarget (WAD)
Bits 150-255 (106 bits): unrealizedInterest
```

All reads/writes are via assembly with mask operations. One SLOAD/SSTORE for the entire market state.

#### 8b. Clones-with-Immutable-Args

CollateralTracker inherits from `Clone` (clones-with-immutable-args). Seven parameters are encoded directly in the clone's calldata rather than storage:
- `panopticPool` (20 bytes)
- `underlyingIsToken0` (1 byte)
- `underlyingToken` (20 bytes)
- `token0` (20 bytes)
- `token1` (20 bytes)
- `riskEngine` (20 bytes)
- `POOL_MANAGER` (20 bytes)
- `poolFee` (3 bytes)

Total: 124 bytes in calldata, zero storage slots. Each read is a `calldataload` + shift, which costs ~3 gas vs ~2100 gas for a cold SLOAD.

#### 8c. LeftRightSigned Packing

Per-user state (`s_interestState`) packs two `int128` values into one `int256`, using the left/right slot convention from `LeftRight.sol`. One SLOAD per user interest lookup.

#### 8d. Transient Storage for Utilization

Uses EIP-1153 transient storage (`tload`/`tstore`) for the per-transaction utilization high-water mark (line 1140-1151). This costs 100 gas per read/write vs 2100/5000 for cold SLOAD/SSTORE, and auto-clears after the transaction.

#### 8e. Deposit Cap as Type Constraint

Max deposit is `type(uint104).max` (line 559), which means `s_depositedAssets` (uint128) can never overflow even when adding the max deposit to a nearly-full vault.

### Applicability to Our Design

**8a -- Consider for oracle state packing**. If we store oracle-related state (last update timestamp, cached price, staleness flag), packing into a single slot saves gas. Example layout for our vault:
```
Bits 0-127   (128 bits): s_totalDeposited
Bits 128-191 (64 bits):  lastOracleUpdate (timestamp)
Bits 192-255 (64 bits):  cachedPayoffRatio (fixed-point, LONG share of 1 USDC)
```

**8b -- Applicable if we use a factory pattern**. If CollateralCustodian instances are deployed per-market via a factory, clones-with-immutable-args saves ~7 storage slots of gas. Otherwise, use `immutable` variables set in the constructor.

**8c -- Applicable for return values**. When returning paired LONG/SHORT amounts from functions, pack them into a single `uint256` or `int256` using the LeftRight convention.

**8d -- Not directly applicable** unless we add flash-deposit protection or per-tx invariant tracking.

**8e -- Directly applicable**. Define a deposit cap as a type constraint. If `s_totalDeposited` is `uint128`, cap deposits at `type(uint128).max` or a governance-set lower bound.

---

## 9. Access Control

### What Panoptic Does

The CollateralTracker has a single privileged caller: the PanopticPool. This is enforced by the `onlyPanopticPool` modifier (line 265-272):

```solidity
modifier onlyPanopticPool() {
    _onlyPanopticPool();
    _;
}

function _onlyPanopticPool() internal view {
    if (msg.sender != address(panopticPool())) revert Errors.NotPanopticPool();
}
```

The PanopticPool address is an immutable argument (set at clone creation, never changeable). Functions gated by this modifier:

| Function | What it does |
|----------|-------------|
| `delegate(address)` | Add virtual shares for liquidation (line 1221) |
| `revoke(address)` | Remove virtual shares post-liquidation (line 1242) |
| `settleLiquidation(...)` | Settle liquidation bonuses (line 1262) |
| `refund(...)` | Transfer shares between accounts (line 1369) |
| `settleMint(...)` | Handle option creation settlement (line 1531) |
| `settleBurn(...)` | Handle option close settlement (line 1595) |

Public functions (callable by anyone):
- `deposit()`, `mint()`, `withdraw()`, `redeem()`, `donate()` -- standard ERC-4626
- `transfer()`, `transferFrom()` -- restricted to users with zero open positions
- `accrueInterest()` -- anyone can trigger global interest accrual

Transfer restrictions are enforced by checking `panopticPool().numberOfLegs(msg.sender) != 0` (line 408). This external call to PanopticPool determines whether the user has open positions.

### Applicability to Our Design

**Directly applicable access control model**. Our CollateralCustodian should have:

| Caller | Allowed Operations |
|--------|-------------------|
| Anyone | `deposit()`, paired-`redeem()` (burn LONG+SHORT for USDC) |
| Oracle/Settlement contract | `settle()` -- finalize oracle price and enable single-side redemptions |
| Admin (if any) | `pause()`, `setDepositCap()`, parameter updates |

For single-side redemptions (redeem only LONG or only SHORT after oracle settlement), we need to decide: is this callable by anyone, or only through a settlement contract?

**Recommendation**: Follow Panoptic's pattern of a single privileged coordinator. Define a `SettlementManager` contract that calls into the CollateralCustodian for oracle-dependent operations. The custodian itself only handles paired mint/burn (which requires no oracle) and delegates oracle-dependent redemptions to the settlement layer.

Transfer restrictions on LONG/SHORT tokens: unlike Panoptic (which blocks transfers when positions are open), our LONG and SHORT tokens should be **freely transferable** since they are independent financial instruments. No transfer restrictions needed.

---

## 10. Events and Monitoring

### What Panoptic Does

Five events defined:

| Event | Parameters | Purpose |
|-------|-----------|---------|
| `Deposit` | sender, owner, assets, shares | Standard ERC-4626 deposit tracking |
| `Withdraw` | sender, receiver, owner, assets, shares | Standard ERC-4626 withdraw tracking |
| `Donate` | sender, shares | Share donation to all holders |
| `CommissionPaid` | owner, builder, commissionProtocol, commissionBuilder | Fee tracking with builder split |
| `InsolvencyPenaltyApplied` | owner, interestOwed, interestPaid, sharesBurned | Insolvency detection for off-chain monitoring |

The `InsolvencyPenaltyApplied` event is particularly notable -- it fires when a user cannot pay their full interest obligation, enabling off-chain bots to flag the account for potential liquidation.

Additionally, the ERC-20 `Transfer` events from `_mint`, `_burn`, and `_transferFrom` provide a complete audit trail of all share movements.

### Applicability to Our Design

**Directly applicable with adapted events**. Our CollateralCustodian should emit:

| Event | Parameters | Purpose |
|-------|-----------|---------|
| `PairedMint` | depositor, usdcAmount, longMinted, shortMinted | Track deposits with paired token creation |
| `PairedBurn` | redeemer, longBurned, shortBurned, usdcReturned | Track paired redemptions (1:1 path) |
| `OracleSettlement` | epochId, longPayoff, shortPayoff, oracleValue | Record the settlement price for an epoch |
| `SingleSideRedeem` | redeemer, tokenId, amount, usdcPayout | Track post-settlement single-side redemptions |
| `DepositCapUpdated` | oldCap, newCap | Governance event |

The ERC-6909 standard already defines `Transfer(address, address, address, uint256, uint256)` for individual token transfers, providing the audit trail equivalent.

**Key monitoring recommendation**: The `OracleSettlement` event is critical for off-chain systems to verify that the oracle price was applied correctly. Include enough data for independent verification: the raw oracle value, the computed LONG payoff per unit, and the computed SHORT payoff per unit. This enables monitoring bots to detect oracle manipulation.

---

## Summary Matrix

| Pattern | Panoptic Approach | Our Applicability | Adaptation Needed |
|---------|------------------|-------------------|-------------------|
| Internal asset tracking | 3-variable model (deposited, AMM, credited) | 1-variable (`s_totalDeposited`) | Simplification |
| Rounding discipline | Always round against user | Same principle, but simpler (1:1 mint) | Only at oracle payoff calculation |
| Reentrancy defense | Layered (SFPM guard + CEI + access control) | Transient reentrancy guard on deposit/redeem | Direct adoption |
| Multi-token coordination | Two separate ERC-20 contracts + coordinator | Single ERC-6909 contract | Major simplification |
| Inflation attack resistance | Virtual shares (10^6 : 1) + internal tracking | Internal tracking only (no variable price) | Partial -- no virtual shares needed |
| Donation attack resistance | Internal accounting ignores actual balance | Same -- track `s_totalDeposited` not `balanceOf` | Direct adoption |
| Flash manipulation resistance | Transient storage utilization high-water mark | Not needed (no utilization rate) | Not applicable |
| Insolvency detection | Check `shares_owed > balance`, emit event, partial pay | Not needed (vault is always solvent by construction) | Not applicable |
| Liquidation protocol loss | Dilute all shareholders via share minting | Not needed (full backing invariant) | Not applicable |
| View functions | Full ERC-4626 preview set + interest previews | Adapted preview set + oracle-dependent payoff queries | Moderate adaptation |
| Storage packing | MarketState in 1 slot, LeftRight for pairs | Pack oracle state, use LeftRight for returns | Moderate adaptation |
| Access control | `onlyPanopticPool` + position-gated transfers | `onlySettlementManager` + free LONG/SHORT transfers | Moderate adaptation |
| Events | 5 domain events + ERC-20 Transfer | 5 domain events + ERC-6909 Transfer | Moderate adaptation |

---

## Recommended Next Steps

1. **Define the storage layout** for CollateralCustodian using the single-slot packing pattern from MarketState for oracle-related state.

2. **Implement the rounding spec** as a table (like section 2 above) before writing any conversion code. Every `mulDiv` call should have a documented rounding direction and rationale.

3. **Write invariant tests** for `s_totalDeposited == s_longSupply == s_shortSupply` and `USDC.balanceOf(address(this)) >= s_totalDeposited`. These are the conservation invariants that replace Panoptic's share-price invariants.

4. **Design the oracle settlement flow** as a state machine: `OPEN -> SETTLING -> SETTLED`, where single-side redemptions are only available in `SETTLED` state. This replaces Panoptic's continuous interest accrual model with a discrete epoch-based settlement.

5. **Adopt the "internal tracking, not balance" principle** as an absolute rule. Never use `USDC.balanceOf(address(this))` in any accounting logic. Only use it in emergency recovery or admin functions.
