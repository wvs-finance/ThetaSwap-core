# Angstrom LP Risk Mitigation Analysis

## Executive Summary

Angstrom's architecture makes a fundamental trade: it replaces the open, permissionless MEV extraction pipeline with a controlled, node-mediated auction that redistributes surplus to LPs. This genuinely addresses the largest LP risk (LVR/adverse selection) but introduces a novel trust dependency on the node layer. Several other LP risks from academic literature remain partially or fully unaddressed because they are structural properties of concentrated liquidity AMMs rather than MEV-specific problems.

---

## Summary Table

| # | Risk | Classification | Primary Mechanism |
|---|------|---------------|-------------------|
| 1 | LVR / Adverse Selection | MOSTLY MITIGATED | Hook-gated swaps + ToB auction surplus redistribution |
| 2 | Fee Yield Compression | UNCHANGED | Same per-unit-liquidity dilution as V3 |
| 3 | Gas Cost Drag | UNCHANGED | Standard V4 modify + additional hook overhead |
| 4 | JIT Liquidity Dilution | MOSTLY MITIGATED | expectedLiquidity check + rewardChecksum |
| 5 | Range Management Complexity | UNCHANGED | No automation or simplification |
| 6 | High-Vol Profitability Asymmetry | PARTIALLY MITIGATED | ToB captures vol-surplus, but unlock swaps leak value |
| 7 | Concentration / Oligopoly | UNCHANGED | Proportional reward, no diversity incentive |
| 8 | Node Trust / Reward Allocation | NEW RISK INTRODUCED | Off-chain reward computation, pullFee, gas discretion |
| 9 | Unlock Swap Fee Leakage | NEW RISK INTRODUCED | Post-bundle swaps; protocol fee to collector, not LPs |

---

## Risk-by-Risk Analysis

### 1. LVR / Adverse Selection (IL from Arb Trades)

**Classification: MOSTLY MITIGATED**

This is Angstrom's flagship protection. The mechanism works in two layers:

**Layer 1 -- Hook-gated swap access.** The `beforeSwap` hook in `UnlockHook.sol` (lines 38-67) enforces that no external party can swap against Angstrom-controlled pools unless the block has been "unlocked" (either via `execute` or `unlockWithEmptyAttestation`). The critical gate at line 49: `revert CannotSwapWhileLocked()`. This prevents the classic LVR pathway where an external arbitrageur extracts the stale-price delta from the AMM.

**Layer 2 -- ToB auction surplus redistribution.** Per `bundle-building.md` (lines 88-101), the node computes the arb surplus as:
```python
bid_in_asset0 = order.quantity_in - swap_input  # (zero_for_one case)
```
This surplus, plus user order fees, flows into `lpReward` distributed via `_decodeAndReward` in `GrowthOutsideUpdater.sol` (lines 31-107). The reward is added to `poolRewards_.globalGrowth` (line 55 for currentOnly; line 103 for multi-tick) and distributed pro-rata to active liquidity.

**Why "mostly" not "eliminated":** The node constructs the reward quantities off-chain. The contract verifies a `rewardChecksum` (line 97) and checks `expectedLiquidity` matches actual pool liquidity (line 51), but it does NOT verify the economic optimality of the split. A colluding node could under-report the arb surplus, pocketing a fraction. The mitigation relies on the "sufficiently staked assumption" from `overview.md` (lines 39-43) -- slashing compensates for worst-case extraction. Additionally, the unlock-swap pathway (discussed under Risk 9) allows post-bundle swaps that can extract residual LVR at a fee, but this fee goes to a protocol fee collector, not directly to LPs.

**Key files:**
- `/contracts/src/modules/UnlockHook.sol` lines 38-67 (beforeSwap gate)
- `/contracts/src/modules/GrowthOutsideUpdater.sol` lines 31-107 (reward distribution)
- `/contracts/docs/bundle-building.md` lines 88-101 (surplus formula)
- `/contracts/docs/overview.md` lines 39-43 (staking assumptions)

---

### 2. Fee Yield Compression (Competition Among LPs)

**Classification: UNCHANGED**

Angstrom uses the same concentrated liquidity model as Uniswap V3/V4. Reward distribution in `PoolRewards.sol` (line 26, `getGrowthInside`) is per-unit-of-liquidity within the active range. When more LPs concentrate in the same tick range, each LP's share of `globalGrowth` dilutes proportionally because the denominator (`pooLiquidity` at `GrowthOutsideUpdater.sol` line 50) increases.

The `X128MathLib.flatDivX128(amount, pooLiquidity)` call at line 55 makes this explicit: growth per unit = reward / total_active_liquidity. More liquidity means less reward per unit. Angstrom does not introduce any mechanism to cap liquidity, adjust fee tiers dynamically based on LP competition, or otherwise alter this fundamental dynamic.

The only indirect mitigation is that total reward size may be larger (because arb surplus is returned rather than extracted), so absolute yields could be higher even though the competitive dynamic is identical.

**Key files:**
- `/contracts/src/modules/GrowthOutsideUpdater.sol` line 55 (per-unit dilution)
- `/contracts/src/types/PoolRewards.sol` lines 26-44 (growth inside computation)

---

### 3. Gas Cost Drag (Repositioning Costs)

**Classification: UNCHANGED**

Angstrom adds and removes liquidity through Uniswap V4's `modifyLiquidity` pathway, hooking only `beforeAddLiquidity` and `beforeRemoveLiquidity` to manage reward accounting (`PoolUpdates.sol` lines 50-155). The actual position modification still incurs standard Uniswap V4 gas costs -- the hook logic adds incremental gas on top (growth-inside computation, position tracking, reward payment on removal).

In fact, Angstrom may slightly increase repositioning costs because:
- `beforeAddLiquidity` performs a `fullMulDiv` to preserve accrued rewards (lines 113-117)
- `beforeRemoveLiquidity` computes and pays out accumulated rewards via `safeTransfer` + Uniswap settlement (lines 144-151)

No mechanism reduces the frequency or cost of repositioning. Active LPs still need to rebalance ranges around the current price, paying gas each time.

**Key files:**
- `/contracts/src/modules/PoolUpdates.sol` lines 50-155 (add/remove hooks)

---

### 4. JIT Liquidity Dilution (Front-running LP Deposits)

**Classification: MOSTLY MITIGATED**

Angstrom provides a strong on-chain defense against JIT liquidity: the `JustInTimeLiquidityChange` revert in `GrowthOutsideUpdater.sol` (lines 21, 52, 98). The mechanism works as follows:

The node pre-computes the `expectedLiquidity` for each rewarded tick range and embeds it in the bundle payload. When `_decodeAndReward` executes on-chain, it compares `expectedLiquidity` against the actual pool liquidity from Uniswap (`UNI_V4.getPoolLiquidity(id)` at line 50). If any JIT provider modified liquidity between the node's computation and on-chain execution, the liquidity values mismatch, and the entire bundle reverts.

For multi-tick rewards, the checksum mechanism (lines 96-99) hashes together `(tick, liquidity)` pairs across all rewarded ticks. Any JIT injection at any tick within the rewarded range produces a checksum mismatch and revert.

Additionally, since only the node's `execute` call can trigger swaps in the locked state, a JIT provider cannot front-run the swap itself -- they can only try to front-run the `execute` transaction, but the liquidity check catches this.

**Residual risk:** If a JIT provider colludes with a node (or IS the node), the node can simply include the JIT liquidity in its expected values. This is a node trust risk rather than a JIT risk per se, mitigated by staking/slashing.

**Key files:**
- `/contracts/src/modules/GrowthOutsideUpdater.sol` lines 21, 50-52, 96-99 (JIT protection)

---

### 5. Range Management Complexity (Choosing Optimal Tick Ranges)

**Classification: UNCHANGED**

Angstrom does not provide any tooling, automation, or incentive structure that simplifies range selection for LPs. The system is essentially the same as Uniswap V4 concentrated liquidity: positions are defined by `(tickLower, tickUpper, salt)` per `PoolUpdates.sol` line 97, and reward accrual depends on whether the current tick is within the range (`PoolRewards.sol` lines 31-43).

The reward distribution logic in `_rewardBelow` and `_rewardAbove` (`GrowthOutsideUpdater.sol` lines 109-188) does distribute rewards across tick ranges proportional to active liquidity, but this is the same "active = earning, inactive = not earning" mechanic as standard V3-style AMMs.

No vault abstraction, automated rebalancing, or simplified position management is provided at the contract level. The `well behaving routers` assumption in `overview.md` (line 44) suggests this is expected to be handled by external routing infrastructure.

**Key files:**
- `/contracts/src/types/PoolRewards.sol` lines 26-44 (growth inside -- range-dependent)
- `/contracts/docs/overview.md` line 44 (router assumption)

---

### 6. High-Volatility Profitability Asymmetry (Retail Loses More During Vol Spikes)

**Classification: PARTIALLY MITIGATED**

In standard AMMs, high-volatility periods are when LVR is worst -- large price moves mean large arb profits extracted from LPs. Angstrom's ToB auction captures this surplus and returns it to LPs, which directly counteracts the volatility-specific loss amplification.

However, the mitigation is only partial because:

1. **The unlock swap pathway** (Risk 9 below) allows post-bundle swaps at a fee. During high volatility, significant residual price movement within a block (after the ToB swap) could be extracted via unlock swaps. The fee charged (`unlockedFee` in `TopLevelAuth.sol` line 53, capped at `MAX_UNLOCK_FEE_E6 = 0.4e6` i.e. 40% at line 21) goes to the `FEE_COLLECTOR` contract, not to LPs. The `afterSwap` hook in `UnlockHook.sol` (lines 76-108) mints the protocol fee to `FEE_COLLECTOR` (line 96-99) and only updates growth-outside accumulators for tick crossings (lines 103-106), NOT for fee distribution to LPs.

2. **One bundle per block.** The `OnlyOncePerBlock` constraint (`TopLevelAuth.sol` line 223-225) means the ToB auction captures the price at one point in the block. Intra-block volatility after the bundle is handled only by the unlock swap mechanism, whose fees do not flow to LPs.

3. **Node timing discretion.** The node chooses WHEN to submit the bundle within the block, potentially optimizing for its own benefit during high-vol periods.

**Key files:**
- `/contracts/src/modules/TopLevelAuth.sol` line 21 (MAX_UNLOCK_FEE_E6 = 40%)
- `/contracts/src/modules/UnlockHook.sol` lines 76-108 (afterSwap fee to collector, not LPs)
- `/contracts/src/modules/TopLevelAuth.sol` lines 222-226 (once per block)

---

### 7. Concentration / Oligopoly (Few LPs Dominate)

**Classification: UNCHANGED**

Angstrom's reward distribution is strictly proportional to liquidity contribution via the `flatDivX128(amount, liquidity)` division in `GrowthOutsideUpdater.sol` (lines 55, 83, 128, 169). Large LPs receive proportionally large rewards. There are no mechanisms for:
- Progressive fee structures that favor smaller LPs
- Caps on per-LP reward share
- Minimum tick-range spreads that would limit concentration
- Governance or incentive structures favoring LP diversity

The `JustInTimeLiquidityChange` protection actually has a subtle pro-incumbency effect: it locks in the liquidity snapshot the node computed off-chain, meaning established LPs who were present when the node built the bundle are the ones who benefit. New entrants cannot add liquidity and earn in the same block.

**Key files:**
- `/contracts/src/modules/GrowthOutsideUpdater.sol` lines 55, 128, 169 (proportional distribution)

---

### 8. Node Trust / Reward Allocation Risk

**Classification: NEW RISK INTRODUCED**

This is Angstrom's primary novel risk. The node has several areas of discretion that are NOT verified on-chain:

**8a. Reward amount discretion.** The node computes `bid_in_asset0` off-chain and includes it in the bundle. The contract only verifies:
- The `rewardChecksum` matches the tick/liquidity structure (`GrowthOutsideUpdater.sol` lines 96-99)
- The total `rewardTotal` is debited from `bundleDeltas` (`PoolUpdates.sol` line 213)
- Solvency is maintained (`Settlement.sol` line 84 -- `BundlDeltaUnresolved`)

It does NOT verify that the reward amount represents the true arb surplus. A node could submit a ToB order with an artificially low bid, keep the surplus off-chain, and pass the solvency check because the delta tracker only requires balanced accounting, not optimal reward distribution.

**8b. Gas fee attribution.** Per `overview.md` lines 59-61, the node sets `gasUsedAsset0` and `extraFeeAsset0` for each order. The contract only checks `gasUsedAsset0 <= buffer.maxGasAsset0` (`Angstrom.sol` line 135). A node can overcharge gas (up to the max), pocketing the difference.

**8c. Order censorship.** The node selects which orders to include. While the economic security assumption claims censorship resistance, a single node within its slot has full discretion.

**8d. `pullFee` extraction.** The controller (which manages nodes) can call `pullFee` (`TopLevelAuth.sol` lines 180-183) to withdraw arbitrary token amounts from the contract. This is assumed to be "accrued validator fees" but is not verified on-chain.

**Mitigations:** Staking, slashing, and the "sufficiently staked assumption" (`overview.md` lines 39-43). The system's integrity requires that rational node behavior under slashing threat aligns with honest behavior.

**Key files:**
- `/contracts/src/modules/TopLevelAuth.sol` lines 180-183 (pullFee -- arbitrary withdrawal)
- `/contracts/src/modules/TopLevelAuth.sol` lines 222-226 (_nodeBundleLock)
- `/contracts/docs/overview.md` lines 36-43 (trust assumptions)
- `/contracts/src/Angstrom.sol` line 135 (gas cap is only upper bound)

---

### 9. Unlock Swap Fee Leakage (Direct Swaps Bypassing the Auction)

**Classification: NEW RISK INTRODUCED (partially mitigated by fee design)**

After the node's bundle executes and "unlocks" the block (`_lastBlockUpdated = block.number`), the `beforeSwap` hook in `UnlockHook.sol` (lines 38-67) allows external swaps against the pool. These swaps bypass the ToB auction entirely.

The fee structure for these swaps has two components:
1. `unlockedFee` (line 62) -- the LP swap fee charged by Uniswap's fee mechanism
2. `protocolUnlockedFee` (line 83) -- an additional protocol fee extracted in `afterSwap` and minted to `FEE_COLLECTOR` (lines 95-99)

Critical observation: the `protocolUnlockedFee` goes to the `UnlockSwapFeeCollector` contract (`UnlockSwapFeeCollector.sol`), which is withdrawable only by the controller via `collect_unlock_swap_fees` (`TopLevelAuth.sol` lines 71-73). This fee does NOT flow to LPs through the reward growth accumulators. While `afterSwap` does call `poolRewards[id].updateAfterTickMove` (lines 103-106), this only updates the growth-outside bookkeeping for tick crossings -- it does not add new rewards.

The `unlockedFee` does go to LPs via Uniswap V4's native fee mechanism (it is set as the `swapFee` return value at line 62), but the `protocolUnlockedFee` is pure leakage from the LP perspective.

The cap of `MAX_UNLOCK_FEE_E6 = 0.4e6` (40%) at `TopLevelAuth.sol` line 21 limits how high these fees can be set, but doesn't limit the total volume of unlock swaps. In volatile markets, significant arb volume could flow through unlock swaps rather than the ToB auction, with the protocol fee portion not reaching LPs.

There is also an alternative unlock path: `unlockWithEmptyAttestation` (`TopLevelAuth.sol` lines 193-210) allows a node to unlock without a bundle by signing an attestation. This enables the swap pathway without any reward distribution at all -- purely fee-based swaps for the rest of the block.

**Key files:**
- `/contracts/src/modules/UnlockHook.sol` lines 38-108 (full beforeSwap/afterSwap flow)
- `/contracts/src/modules/UnlockSwapFeeCollector.sol` (fee goes to collector, not LPs)
- `/contracts/src/modules/TopLevelAuth.sol` lines 21, 71-73, 193-210 (fee cap, collection, empty attestation)

---

## Key Implications

1. **Angstrom's value proposition is narrowly focused on LVR.** It genuinely addresses the single largest LP loss channel through the ToB auction, but the other structural risks of concentrated liquidity remain.

2. **The unlock swap pathway is a significant design tension.** It exists to ensure pools remain usable when no bundle is submitted, but creates a channel for value extraction that bypasses the auction. The `protocolUnlockedFee` going to the controller rather than LPs is a deliberate revenue capture that comes at LP expense.

3. **On-chain verification is intentionally minimal for gas savings.** The `rewardChecksum` and `expectedLiquidity` checks are clever but lightweight. The contract trusts the node for the economic substance of reward allocation. This is an explicit design choice documented in `overview.md` lines 36-43.

4. **The `pullFee` function is an underappreciated trust surface.** It allows the controller to withdraw any token amount. While documented as for "accrued validator fees," it has no on-chain enforcement of what qualifies as a legitimate fee withdrawal.
