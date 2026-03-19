# V3 feeGrowthInside Alignment — Design

## Problem

The V3 reactive adapter computes x_k (fee share ratio) using `SyntheticFeeGrowthMod`, which inverts the liquidity ratio compared to V4's `FeeShareRatioMod`:

- **V4:** `x_k = (posFeeDelta / rangeFeeDelta) * (posLiq / totalRangeLiq)`
- **V3 (current):** `x_k = (fee0/posLiq) / (totalFee0/totalRangeLiq) = (fee0/totalFee0) * (totalRangeLiq/posLiq)` — liquidity ratio inverted

Result: V3 deltaPlus = 9.49e37 vs V4 reference = 1.51e38.

## Solution

Read `feeGrowthInside` directly from the V3 pool (same chain as adapter) instead of synthesizing it from Collect event fee amounts. This lets us use V4's exact `FeeShareRatioMod.fromFeeGrowthDelta` formula.

## Architecture

**On `onV3Mint`:** Snapshot `feeGrowthInside0LastX128` from `pool.positions(posKey)` into adapter storage.

**On `onV3Burn`:**
1. Compute current `feeGrowthInside` from `pool.feeGrowthGlobal0X128()` and `pool.ticks(tl/tu).feeGrowthOutside0X128`
2. Delta = current - stored snapshot
3. Get `rangeFeeGrowthDelta` from FCI storage (same as V4 tracks)
4. Call `FeeShareRatioMod.fromFeeGrowthDelta(posDelta, rangeDelta, posLiq, totalRangeLiq)` — identical to V4

## Data Flow & Storage Changes

**New storage:**
```solidity
mapping(bytes32 posKey => uint256 feeGrowthInside0Last) feeGrowthSnapshots;
```

**Removed:**
- `SyntheticFeeGrowthMod.sol` — dead code
- `CollectedFeesMod.sol` / `CollectedFees` accumulation in ReactVM
- `PendingBurn` deferred pattern in ReactVM — `onV3Burn` is self-contained
- `fee0`, `fee1` from `onV3Burn` callback signature

**Modified callback:**
```solidity
// Before: onV3Burn(rvmSender, burnData, fee0, fee1)
// After:  onV3Burn(rvmSender, burnData)
```

**ReactVM simplification:** `react()` no longer defers Burn→Collect. On V3_BURN_SIG (non-zero liquidity), emit callback immediately.

**feeGrowthInside computation (adapter, same chain as pool):**
```solidity
function _feeGrowthInside(IUniswapV3Pool pool, int24 tl, int24 tu) internal view returns (uint256) {
    (,, uint256 feeGrowthOutsideLower,,,,,) = pool.ticks(tl);
    (,, uint256 feeGrowthOutsideUpper,,,,,) = pool.ticks(tu);
    uint256 feeGrowthGlobal = pool.feeGrowthGlobal0X128();
    (, int24 currentTick,,,,,) = pool.slot0();
    uint256 feeGrowthBelow = currentTick >= tl ? feeGrowthOutsideLower : feeGrowthGlobal - feeGrowthOutsideLower;
    uint256 feeGrowthAbove = currentTick < tu ? feeGrowthOutsideUpper : feeGrowthGlobal - feeGrowthOutsideUpper;
    return feeGrowthGlobal - feeGrowthBelow - feeGrowthAbove;
}
```

## Scope

| Change | Location |
|--------|----------|
| Add `feeGrowthSnapshots` storage | `ReactiveHookAdapterStorageMod.sol` |
| Snapshot feeGrowthInside on mint | `ReactiveHookAdapter.onV3Mint` |
| Read live feeGrowthInside + compute delta on burn | `ReactiveHookAdapter.onV3Burn` |
| Use `FeeShareRatioMod.fromFeeGrowthDelta` | `ReactiveHookAdapter.onV3Burn` |
| Remove fee0/fee1 from burn callback | `ReactLogicMod.sol` |
| Remove PendingBurn + CollectedFees | `ReactLogicMod.sol`, `ReactVmStorageMod.sol` |
| Remove SyntheticFeeGrowthMod | Delete file |
| Remove/simplify Collect handler | `ReactLogicMod.sol` |
| Add `_feeGrowthInside` helper | New library or inline in adapter |
| Differential fork test | `test/reactive-integration/fork/` |

## Testing

- **Differential:** Same scenario on V4 hook and V3 adapter, assert deltaPlus matches exactly
- **Unit:** `_feeGrowthInside` matches V3 pool internals (fork test), snapshot/delta correctness, `fromFeeGrowthDelta` produces identical x_k
- **Regression:** Zero-burn skip no longer needed (deferred pattern removed)
