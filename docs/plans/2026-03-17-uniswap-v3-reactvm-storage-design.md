# UniswapV3 ReactVM Storage Design

**Branch:** 008-uniswap-v3-reactive-integration
**Date:** 2026-03-17

## Problem

Native V4 hooks run synchronously — `beforeSwap` and `beforeRemoveLiquidity` read pool state before mutation and cache it via tstore for `after*` hooks. V3 reactive callbacks only receive post-event logs. By callback time, the V3 pool state is already mutated:

- **Swap:** `slot0().tick` is the post-swap tick, but `beforeSwap` needs `tickBefore`.
- **Burn:** `positions(posKey).liquidity` is 0 (or reduced), but `beforeRemoveLiquidity` needs pre-burn `posLiquidity`.
- **Burn:** `positions(posKey).feeGrowthInside0LastX128` is updated to current by V3's `burn()`, destroying the pre-burn snapshot.

The ReactVM must shadow state that `before*` hooks would read synchronously.

## Design Decisions

### What the ReactVM shadows

| State | Why | Source |
|-------|-----|--------|
| `tickBefore` (per pool) | `beforeSwap` caches tick for `afterSwap` to compute overlapping range delta | Swap event emits `tickAfter`; shadow stores previous tick |
| `positionLiquidity` (per position) | `beforeRemoveLiquidity` reads `posLiquidity` for partial-remove guard and FCI x_k computation | Mint/Burn events emit liquidity delta |

### What the ReactVM does NOT shadow

| State | Why not |
|-------|---------|
| `feeGrowthInside0LastX128` | Not needed for x_k computation. The FCI V2 code (`fromFeeGrowthDelta`) uses fee growth deltas with all five parameters, but `rangeFeeGrowth0` is still readable at callback time (pool-level, unchanged by burns). The `baseline` stored by FCI during `afterAddLiquidity` provides the entry-time snapshot. For positions with no intermediate modifications, `feeLast0 == baseline`. |
| `totalRangeLiquidity` | Tracked on the destination chain by `TickRangeRegistryV2` inside FCI V2. Returned by `removePositionInRange`. Not available from V3 events without full history. |
| `rangeFeeGrowth0` | Pool-level state (from `ticks()` + `feeGrowthGlobal0X128`). Unchanged by burns — safe to read at callback time. |

### x_k computation

The FCI V2 `afterRemoveLiquidity` calls `fromFeeGrowthDelta(rangeFeeGrowthNow, positionFeeLast, baseline, posLiq, totalRangeLiq)` using all five parameters. For V3 positions with a single add/remove lifecycle, `positionFeeLast == baseline`, so the formula reduces to `x_k = posLiq / totalRangeLiq`. This liquidity-ratio approach is:

- Proportional to fee growth (V3 distributes fees pro-rata by liquidity within a range)
- Token-denomination-agnostic (no dependency on token0 vs token1 fee growth)
- Consistent with the V1 `ReactiveHookAdapter` approach: `fromFeeGrowth(posLiq, totalRangeLiq)`

The full `fromFeeGrowthDelta` formula remains in use — the simplification is a consequence of the V3 reactive lifecycle, not a code change.

## Storage Module

**File:** `src/fee-concentration-index-v2/protocols/uniswap-v3/modules/UniswapV3ReactVMStorageMod.sol`

This is a **new file** replacing the existing V1-era module at the same path. The V1 slot `keccak256("ThetaSwapReactive.vm.storage")` is abandoned — all V2 reactive contracts are fresh deployments.

**Slot:** `keccak256("thetaSwap.fci.v3.reactvm")` — V2-scoped, no collision with V1 slot.

```solidity
struct TickShadow {
    int24 tick;
    bool isSet;
}

struct PositionShadow {
    uint128 liquidity;
    bool isSet;
}

struct UniswapV3ReactVMStorage {
    mapping(uint256 => mapping(address => bool)) poolWhitelist;
    mapping(uint256 => mapping(address => TickShadow)) tickShadow;
    mapping(uint256 => mapping(address => mapping(bytes32 => PositionShadow))) positionShadow;
}
```

Keying: `chainId => pool => posKey` for positions, `chainId => pool` for ticks and whitelist.

`posKey = keccak256(abi.encodePacked(owner, tickLower, tickUpper))` — standard V3 position key.

## Free Function Accessors

```solidity
// ── Storage root ──
function uniswapV3ReactVMStorage() pure returns (UniswapV3ReactVMStorage storage $);

// ── Tick shadow ──
function getLastTick(uint256 chainId, address pool) view returns (int24 tick, bool isSet);
function setLastTick(uint256 chainId, address pool, int24 tick);

// ── Position shadow ──
function getPositionShadow(uint256 chainId, address pool, bytes32 posKey)
    view returns (uint128 liquidity, bool isSet);
function setPositionShadow(uint256 chainId, address pool, bytes32 posKey, uint128 liquidity);

// ── Pool whitelist ──
function isWhitelisted(uint256 chainId, address pool) view returns (bool);
function setWhitelisted(uint256 chainId, address pool, bool whitelisted);
```

## Callback Payload Encoding

**Uniform 3-field layout for all event types:**

```
abi.encode(LogRecord log, int24 tickBefore, uint128 posLiqBefore)
```

- **Mint:** `tickBefore = 0`, `posLiqBefore = 0` (unused by callback)
- **Swap:** `tickBefore = shadow tick`, `posLiqBefore = 0` (unused)
- **Burn:** `tickBefore = 0`, `posLiqBefore = pre-burn position liquidity from shadow`

Uniform encoding avoids conditional ABI decoding in `UniswapV3Callback.unlockCallbackReactive`. The decoder always does:

```solidity
(IReactive.LogRecord memory log, int24 tickBefore, uint128 posLiqBefore) =
    abi.decode(data, (IReactive.LogRecord, int24, uint128));
```

The 32 extra bytes for the unused field are negligible relative to the 1M gas callback budget.

## ReactVM Update Flow

### On Mint event:
1. Compute `posKey` from event topics (owner, tickLower, tickUpper)
2. Read shadow: `(shadowLiq, isSet) = getPositionShadow(chainId, pool, posKey)`
3. Skip if `burnedLiq == 0` (V3 zero-burn pattern — no shadow update, no callback)
4. Update: `setPositionShadow(chainId, pool, posKey, shadowLiq + mintedLiq)`
5. Emit Callback with `abi.encode(log, int24(0), uint128(0))`

### On Swap event:
1. Read shadow: `(prevTick, isSet) = getLastTick(chainId, pool)`
2. `tickBefore = isSet ? prevTick : tickAfter`
3. Update: `setLastTick(chainId, pool, tickAfter)`
4. Emit Callback with `abi.encode(log, tickBefore, uint128(0))`

### On Burn event:
1. Compute `posKey` from event topics
2. Skip if `burnedLiq == 0` (V3 zero-burn pattern — no shadow update, no callback)
3. Read shadow: `(posLiqBefore, isSet) = getPositionShadow(chainId, pool, posKey)`
4. Update: `setPositionShadow(chainId, pool, posKey, posLiqBefore - burnedLiq)` (unchecked — see edge cases)
5. Emit Callback with `abi.encode(log, int24(0), posLiqBefore)`

## Edge Cases: Callback Delivery Failures

### Dropped Mint, arriving Burn

The ReactVM processes ALL V3 events from subscribed pools, regardless of whether the destination-chain callback succeeds or fails. Shadow state updates happen in `react()` before callback emission. Therefore:

- If a Mint callback fails on the destination chain (OOG, revert), the ReactVM shadow still has the correct `posLiquidity` (updated during `react()` processing of the Mint event).
- The FCI V2 on the destination chain will NOT have registered the position (since `afterAddLiquidity` never ran). When the Burn callback arrives, `removePositionInRange` will fail to find the position in the registry and revert.

**Mitigation:** This is an FCI consistency issue, not a shadow correctness issue. The ReactVM shadow is always correct. Destination-chain recovery (re-registering missed positions) is out of scope for this design.

### Dropped Burn callback

If a Burn is processed by the ReactVM (shadow decremented) but the callback fails on the destination chain:

- ReactVM shadow: correctly decremented
- FCI V2: position still registered, not deregistered

A subsequent burn on the same position would see `posLiqBefore` from the shadow (already decremented). If this is a second partial burn, the shadow value is correct. If the position is fully exited via multiple burns, the final burn's `posLiqBefore` equals `burnedLiq` and the partial-remove guard passes.

**Invariant:** ReactVM shadow tracks the V3 pool's position state faithfully. Destination-chain FCI may lag but never diverges from what the ReactVM reports.

### Shadow underflow protection

The Burn update `posLiqBefore - burnedLiq` uses `unchecked {}` arithmetic. Under normal operation, `burnedLiq <= posLiqBefore` because the ReactVM processes ALL Mint/Burn events in order. If events arrive out of order (should not happen with Reactive Network's ordered delivery), the ReactVM `react()` would revert on underflow, blocking that event. This is acceptable — a corrupted event order indicates a protocol-level failure.

### Zero-burn skip

V3 `burnPosition()` emits a zero-burn (liq=0) followed by the full burn. The ReactVM skips zero-burns: no shadow update, no callback emission. This matches the existing `_handleBurn` guard `if (data.liquidity == 0) return;` on the destination chain and avoids wasting callback gas.

### First swap with `isSet == false`

When the ReactVM processes a swap for a newly registered pool (no prior tick shadow), `tickBefore = tickAfter`. This causes `incrementOverlappingRanges(tickAfter, tickAfter)` — a zero-width range that matches no positions. This is a no-op for the FCI and is benign.

## Impact on FCI V2

The async fallback in `beforeRemoveLiquidity`:

```solidity
if (posLiquidity == 0) {
    posLiquidity = uint128(uint256(-params.liquidityDelta));
}
```

This is replaced by using `posLiqBefore` from the enriched callback payload, carried through hookData. The V3 Facet's `latestPositionFeeGrowthInside` still reads from the pool for `feeGrowthInside0LastX128`, but `posLiquidity` is overridden by the shadow value when present in hookData.

The `afterRemoveLiquidity` partial-remove guard `if (posLiq != removedLiq)` now compares:
- `posLiq` = pre-burn liquidity from ReactVM shadow (via hookData)
- `removedLiq` = burned amount from event (via `params.liquidityDelta`)

For full burns: `posLiq == removedLiq` passes.
For partial burns: `posLiq > removedLiq` triggers guard (correct behavior — skip accumulation until full exit).

## Downstream Changes Required

1. **UniswapV3ReactVMStorageMod.sol** — new file replacing V1 module (this design)
2. **UniswapV3Reactive.sol** — update `react()` to read/write position shadow on Mint/Burn, emit uniform 3-field payload
3. **UniswapV3PayloadMutatorLib.sol** — extend `mutateV3Payload()` to handle position shadow for burns, emit uniform 3-field payload
4. **UniswapV3Callback.sol** — decode 3-field payload `(LogRecord, int24, uint128)`, pass `posLiqBefore` to `_handleBurn`
5. **V3HookDataLib.sol** — extend burn hookData encoding to carry `posLiqBefore`; add decoder
6. **FeeConcentrationIndexV2.sol** — remove the `if (posLiquidity == 0)` fallback; read `posLiqBefore` from hookData when present
7. **UniswapV3Facet.sol** — `latestPositionFeeGrowthInside` may need to accept `posLiqBefore` override from hookData
8. **Test files** — update callback tests for new 3-field payload encoding
