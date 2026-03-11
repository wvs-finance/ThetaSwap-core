# Reactive Network FCI Integration Design

**Date**: 2026-03-06
**Feature**: 003-reactive-integration
**Platform**: Reactive Network (dual-instance ReactVM)
**Branch**: 001-fci-coprimary-diamond

## Overview

Extend FeeConcentrationIndex coverage to Uniswap V3 pools via Reactive Network cross-chain event monitoring. A single reactive contract per chain subscribes to V3 Swap/Mint/Burn/Collect events, processes them in ReactVM, and emits callbacks to a destination-chain adapter that maintains parallel FCI state.

## Architecture: Three Layers

```
Layer 3: Destination Chain (same chain as V3 pool origin)
  ReactiveHookAdapter
  - Auth: callback proxy + rvm_id verification
  - onV3Swap/onV3Mint/onV3Burn → adapt*() → parameterized FCI logic
  - REACTIVE_FCI_STORAGE_SLOT (parallel, isolated from V4 FCI)
  - getIndex() view

Layer 2: ReactVM (isolated, no gas cost)
  ThetaSwapReactive.react(LogRecord)
  - Route by topic_0 (V3 event sig) and _contract (pool whitelist)
  - Collect → accumulate fees in ReactVM state (no callback)
  - Swap/Mint → emit Callback directly
  - Burn → read accumulated fees, clear, emit Callback with fee data
  - Self-subscription sync for pool whitelist

Layer 1: Reactive Network Instance
  ThetaSwapReactive (RN instance)
  - constructor: payable, self-subscribe for whitelist sync
  - registerPool/unregisterPool: 4 subscriptions per pool (Swap/Mint/Burn/Collect)
  - receive(): auto-debt coverage
  - Owner-gated pool management
```

## Key Design Decisions

### 1. One reactive contract per chain, pool whitelist

Single deployment per chain monitors all whitelisted V3 pools. Pool registration via `registerPool(chainId, pool)` on RN instance, synced to ReactVM via self-subscription pattern. Unregistering stops subscriptions (4 per pool) and debt accumulation.

### 2. Collect fees accumulate in ReactVM

Collect events mutate ReactVM state only — no callback emitted. `CollectedFees` stored per position key. On Burn, accumulated fees are read, cleared, and included in the Burn callback payload. Saves callback gas for the most frequent non-swap event.

### 3. Callback target is same chain as origin

Origin chain == destination chain. The callback proxy relays back to `ReactiveHookAdapter` on the same chain where the V3 pool lives.

### 4. Parallel FCI storage, isolated from V4

Adapter owns `REACTIVE_FCI_STORAGE_SLOT`, completely independent from V4's `FCI_STORAGE_SLOT`. V3 pools have synthetic feeGrowth (derived from Collect/Burn amounts), not native V4 feeGrowthInside. Mixing would corrupt the index.

### 5. Parameterized FCI storage functions

Existing FCI storage wrappers (`registerPosition`, `setFeeGrowthBaseline`, `incrementOverlappingRanges`, etc.) refactored to accept `FeeConcentrationIndexStorage storage $` as first parameter. V4 FCI passes `fciStorage()`, reactive adapter passes `reactiveFciStorage()`. Same logic, different slot. Current no-arg overloads remain as thin pass-throughs.

### 6. adapt* translation layer

WP02's existing free functions (`adaptV3Swap`, `adaptV3Mint`, `adaptV3Burn`) translate V3 typed data into V4-compatible calldata. The adapter calls these, then feeds results into the shared parameterized FCI logic.

### 7. Funding-agnostic

Contract implements `receive() external payable` with auto-debt coverage. Who funds (protocol treasury, per-pool sponsors, etc.) is an operational decision, not a contract concern.

## Data Flows

### V3 Swap

1. V3 pool emits `Swap(..., tick)`
2. Reactive Network delivers LogRecord to ReactVM
3. `react()`: check whitelist, decode tick via `V3EventDecoderMod`, emit `Callback(chainId, adapter, GAS, abi.encodeCall(onV3Swap, swapData))`
4. Callback proxy relays to `ReactiveHookAdapter.onV3Swap(V3SwapData)`
5. Adapter: `adaptV3Swap(data)` → `incrementOverlappingRanges(reactiveFciStorage(), poolId, tick, tick)`

### V3 Collect (no callback)

1. V3 pool emits `Collect(owner, ..., amount0, amount1)`
2. ReactVM decodes via `V3EventDecoderMod` → `V3CollectData`
3. `accumulate(collectedFees[posKey], amount0, amount1)` in ReactVM state
4. No callback emitted

### V3 Burn (consumes accumulated fees)

1. V3 pool emits `Burn(owner, tickLower, tickUpper, liquidity, ...)`
2. ReactVM reads `collectedFees[posKey]` → `(fee0, fee1)`, clears entry
3. Emits `Callback(chainId, adapter, GAS, abi.encodeCall(onV3Burn, (burnData, fee0, fee1)))`
4. Adapter: `adaptV3Burn(data, fee0, fee1)` → deregister, compute SyntheticFeeGrowth, FeeShareRatio, addTerm to HHI

### V3 Mint

1. V3 pool emits `Mint(sender, owner, tickLower, tickUpper, liquidity, ...)`
2. ReactVM decodes, emits `Callback(chainId, adapter, GAS, abi.encodeCall(onV3Mint, mintData))`
3. Adapter: `adaptV3Mint(data)` → registerPosition, setFeeGrowthBaseline(0), incrementPos

## File Map

```
src/reactive-integration/
  ThetaSwapReactive.sol                          thin contract shell (react + RN instance)

  modules/
    SubscriptionMod.sol                          V3 event sig constants, subscribe4/unsubscribe4
    ReactiveWhitelistMod.sol                     whitelist storage, add/remove/check
    ReactLogicMod.sol                            processLog(): route by topic_0, accumulate/emit
    ReactVmStorageMod.sol                        ReactVM state: mapping(bytes32 => CollectedFees)
    DebtMod.sol                                  auto-debt coverage free function

  adapters/uniswapV3/
    ReactiveHookAdapter.sol                      thin contract shell (destination chain)
    ReactiveHookAdapterStorageMod.sol            REACTIVE_FCI_STORAGE_SLOT (exists)
    ReactiveAuthMod.sol                          requireAuthorized, requireRvmId

  types/
    LogRecordExtMod.sol                          generic: isSelfSync, topic0, emitter, chainId, typed accessors
    V3EventDecoderMod.sol                        V3-specific: decodeSwap/Mint/Burn/Collect → V3*Data structs
    CollectedFeesMod.sol                         CollectedFees struct + accumulate/clear/isEmpty/positionKey
    ReactiveCallbackDataMod.sol                  (exists) V3SwapData, V3MintData, V3BurnData, V3CollectData
    SyntheticFeeGrowthMod.sol                    (exists) fromBurnAmount, toFeeShareRatio

  libraries/
    PoolKeyExtMod.sol                            (exists) fromV3Pool, toV3Pool, toPoolId

src/fee-concentration-index/modules/
  FeeConcentrationIndexStorageMod.sol            refactor: parameterize wrappers to accept ($ storage, ...)
```

## Refactor: Parameterized FCI Storage Wrappers

Functions to parameterize (add `FeeConcentrationIndexStorage storage $` as first arg):

- `registerPosition($ storage, poolId, rk, posKey, tickLower, tickUpper, liq)`
- `setFeeGrowthBaseline($ storage, poolId, posKey, value)`
- `getFeeGrowthBaseline($ storage, poolId, posKey) view → uint256`
- `deleteFeeGrowthBaseline($ storage, poolId, posKey)`
- `incrementOverlappingRanges($ storage, poolId, tickMin, tickMax)`

Existing no-arg versions become overloads delegating to `fciStorage()`:

```solidity
function registerPosition(PoolId poolId, TickRange rk, ...) {
    registerPosition(fciStorage(), poolId, rk, ...);
}
```

## Economics

| Cost | Payer | Notes |
|------|-------|-------|
| Subscription debt | Anyone via `receive()` | 4 subs per pool, scales linearly |
| ReactVM processing | Free | No gas in ReactVM |
| Collect events | Free | No callback emitted |
| Swap/Mint/Burn callbacks | Reactive contract balance | Gas on origin chain via callback proxy |

## Auth Model

Callback adapter verifies two things (inline checks, no `modifier` keyword):

1. `msg.sender` is in `authorizedCallers` mapping (callback proxy address)
2. First parameter is the stored `rvm_id` (deployer EOA identity)

Owner can update `authorizedCallers` via `setAuthorized(address, bool)`.

## Invariants

Existing RX-001 through RX-010 remain valid. This design adds no new invariants — the parameterized FCI functions preserve all FCI invariants (INV-001-011, FCI-001-011) by construction.

## Constraints

- SCOP: no `is`/`library`/`modifier` in production contracts
- Foundry: cannot simulate SystemContract — deploy via `forge create` / `cast send`
- Reactive Network: state isolated between RN instance and ReactVM
- All logic in Mod files (free functions), contracts are thin shells
