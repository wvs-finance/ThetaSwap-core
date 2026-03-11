# ReactVM Pre-Mutation State Capture — Design

## Problem

V4 hooks have `beforeSwap`/`beforeRemoveLiquidity` to capture pre-mutation state in transient storage. V3's reactive model delivers callbacks **after** the event — pool state is already mutated. This causes two failures:

1. **Swap**: `onV3Swap` uses the post-swap tick for `incrementOverlappingRanges`, missing the full swept range `[min(tickBefore, tickAfter), max(tickBefore, tickAfter)]`.
2. **Burn**: `onV3Burn` reads `feeGrowthInside0` from ticks via `v3FeeGrowthInside0()`. After the last LP exits a range, V3 de-initializes the ticks, zeroing `feeGrowthOutside`. The read returns wrong values → deltaPlus stays 0.

## Solution

Two independent fixes:

### Swaps — ReactVM Tick Shadow

- `ReactVmStorage` gains `mapping(address => int24) lastTick` per pool.
- On `V3_SWAP_SIG`, ReactVM reads stored `lastTick`, embeds it as `tickBefore` in the callback payload, then updates `lastTick = data.tick`.
- `V3SwapData` gains a `tickBefore` field.
- Adapter uses `(min(tickBefore, tick), max(tickBefore, tick))` for `incrementOverlappingRanges`.
- **First swap after registration**: `lastTick` is 0 (uninitialized). Skip `incrementOverlappingRanges` on the first swap; just store the tick as baseline.

### Burns — Position feeGrowthInsideLast Read

- Replace `v3FeeGrowthInside0(pool, tickLower, tickUpper)` with `v3PositionFeeGrowthLast0(pool, posKey)` in `onV3Burn`.
- V3's `burn()` flow: `_updatePosition()` computes `feeGrowthInside` correctly (ticks still initialized), sets `position.feeGrowthInsideLast0X128 = feeGrowthInside`, **then** returns to `_modifyPosition` which de-initializes ticks.
- `pool.positions(posKey).feeGrowthInsideLast0X128` remains valid after burn. V3 never zeros the position struct.
- No ReactVM changes needed for burns.

## File Changes

| File | Change |
|------|--------|
| `ReactiveCallbackDataMod.sol` | Add `tickBefore` to `V3SwapData` |
| `ReactVmStorageMod.sol` | Add `lastTick` mapping + getter/setter |
| `ReactLogicMod.sol` | Read/update lastTick on swap, skip first swap, embed tickBefore in callback |
| `ReactiveHookAdapter.sol` | `onV3Swap`: use tickBefore/tick range. `onV3Burn`: use `v3PositionFeeGrowthLast0` |

## Testing

- Unit: `onV3Swap` swept range correctness
- Unit: `onV3Burn` reads position feeGrowthInsideLast, computes deltaPlus
- Fork: verify `positions().feeGrowthInsideLast0X128` persists post-burn
- On-chain: redeploy, run `buildMildV3()`, verify deltaPlus > 0
