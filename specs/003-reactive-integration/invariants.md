# Invariants: Reactive FCI for Non-V4 Pools

**Feature**: [spec.md](../../kitty-specs/001-reactive-fci-non-v4-pools/spec.md)
**Depends on**: [FCI invariants](../001-fee-concentration-index/invariants.md) (INV-001–010, FCI-001–011)
**Updated**: 2026-03-06
**Count**: 10 invariants (RX-001–010)

These invariants govern the reactive bridge layer — PoolKeyExtLib mapping, ReactiveHookAdapter translation, and the guarantee that reactive-sourced events produce identical FCI state transitions as native V4 events. All upstream FCI invariants (INV-001–011, FCI-001–011) remain in force; this document adds only bridge-specific properties.

---

## RX-001: PoolKey Round-Trip Identity

| Field | Value |
|-------|-------|
| ID | RX-001 |
| Description | Converting a V3 pool address to a synthetic PoolKey and back recovers the original address. The mapping is a left-inverse. |
| Category | Function-level |
| Hoare Triple | `{pool = valid IUniswapV3Pool}` → `toV3Pool(fromV3Pool(pool, adapter))` → `{result == pool}` |
| Affected | PoolKeyExtLib |
| Verification | Kontrol proof (`prove_poolKey_roundTrip`) + fuzz test |

---

## RX-002: PoolKey Determinism

| Field | Value |
|-------|-------|
| ID | RX-002 |
| Description | The same V3 pool address and adapter always produce the same PoolKey. Two calls with identical inputs yield identical outputs (pure function). |
| Category | Function-level |
| Hoare Triple | `{pool == pool}` → `k1 = fromV3Pool(pool, adapter), k2 = fromV3Pool(pool, adapter)` → `{k1 == k2}` |
| Affected | PoolKeyExtLib |
| Verification | Kontrol proof (`prove_poolKey_deterministic`) |

---

## RX-003: PoolKey Distinctness

| Field | Value |
|-------|-------|
| ID | RX-003 |
| Description | Two distinct V3 pool addresses produce distinct PoolIds. The mapping is injective on pool addresses. |
| Category | Function-level |
| Hoare Triple | `{pool1 != pool2}` → `id1 = toId(fromV3Pool(pool1, adapter)), id2 = toId(fromV3Pool(pool2, adapter))` → `{id1 != id2}` |
| Affected | PoolKeyExtLib |
| Verification | Kontrol proof (`prove_poolKey_distinct`) + fuzz test |

---

## RX-004: Synthetic PoolKey Hooks Field

| Field | Value |
|-------|-------|
| ID | RX-004 |
| Description | Every synthetic PoolKey produced by PoolKeyExtLib has its `hooks` field set to the ReactiveHookAdapter address. This distinguishes reactive-sourced pools from native V4 pools. |
| Category | Type-level |
| Hoare Triple | `{adapter = ReactiveHookAdapter address}` → `k = fromV3Pool(pool, adapter)` → `{k.hooks == adapter}` |
| Affected | PoolKeyExtLib |
| Verification | Kontrol proof (`prove_poolKey_hooksField`) |

---

## RX-005: Adapter Authentication

| Field | Value |
|-------|-------|
| ID | RX-005 |
| Description | The ReactiveHookAdapter reverts on any callback from an unauthorized sender. Only whitelisted reactive contracts or callback proxies may invoke adapter functions. |
| Category | System-level |
| Hoare Triple | `{msg.sender NOT in authorizedCallers}` → `adapter.onSwapCallback(...)` → `{REVERTS}` |
| Affected | ReactiveHookAdapter |
| Verification | Kontrol proof (`prove_adapter_rejectsUnauthorized`) + fuzz test |

---

## RX-006: Swap Translation Equivalence

| Field | Value |
|-------|-------|
| ID | RX-006 |
| Description | Processing a V3 Swap event through the ReactiveHookAdapter produces the same swap count increments on the FCI state as a native V4 afterSwap with the same tick traversal range. The reactive path is observationally equivalent to the native path for swap processing. |
| Category | System-level |
| Hoare Triple | `{fciState_reactive == fciState_native, tickRange identical}` → `adapter.onSwap(v3Event) || fci.afterSwap(v4Params)` → `{fciState_reactive == fciState_native}` |
| Affected | ReactiveHookAdapter, FeeConcentrationIndex |
| Verification | Fuzz test (`testFuzz_swapTranslation_equivalence`) — parallel execution comparison |

---

## RX-007: Mint Translation Equivalence

| Field | Value |
|-------|-------|
| ID | RX-007 |
| Description | Processing a V3 Mint event through the ReactiveHookAdapter registers a position with identical state (tickLower, tickUpper, liquidity, fee baseline) as a native V4 afterAddLiquidity with the same parameters. |
| Category | System-level |
| Hoare Triple | `{fciState_reactive == fciState_native, position params identical}` → `adapter.onMint(v3Event) || fci.afterAddLiquidity(v4Params)` → `{fciState_reactive == fciState_native}` |
| Affected | ReactiveHookAdapter, FeeConcentrationIndex |
| Verification | Fuzz test (`testFuzz_mintTranslation_equivalence`) — parallel execution comparison |

---

## RX-008: Burn Fee Extraction Correctness

| Field | Value |
|-------|-------|
| ID | RX-008 |
| Description | The synthetic feeGrowthDelta computed from V3 Burn event data (amount0 / liquidity, amount1 / liquidity) produces a fee share ratio within [0, 1] and is equivalent to the feeGrowthDelta that would be read from V4 state for a position with the same fee accumulation. Division by zero is avoided when liquidity > 0. |
| Category | Function-level |
| Hoare Triple | `{liquidity > 0, amount0 >= 0, amount1 >= 0}` → `syntheticDelta = computeSyntheticFeeGrowth(amount0, amount1, liquidity)` → `{0 <= feeShareRatio(syntheticDelta) <= Q128}` |
| Affected | ReactiveHookAdapter, FeeShareRatioMod |
| Verification | Kontrol proof (`prove_syntheticFeeGrowth_bounds`) + fuzz test |

---

## RX-009: Unregistered Burn No-Op

| Field | Value |
|-------|-------|
| ID | RX-009 |
| Description | When a V3 Burn event arrives for a position not registered in FCI (e.g., position existed before reactive monitoring started), the system does not revert and does not modify any FCI state. The operation is a silent no-op. |
| Category | System-level |
| Hoare Triple | `{pos NOT in registry, fciState == S}` → `adapter.onBurn(v3Event for pos)` → `{fciState == S, no revert}` |
| Affected | ReactiveHookAdapter, TickRangeRegistryMod |
| Verification | Kontrol proof (`prove_unregisteredBurn_noop`) + fuzz test |

---

## RX-010: Swap Deduplication Per Block

| Field | Value |
|-------|-------|
| ID | RX-010 |
| Description | At most one Swap callback is processed per V3 pool per block. If multiple Swap events occur for the same pool in the same block, they are collapsed into a single tick traversal (min tick → max tick). The swap count for overlapping positions increments by exactly 1 per block, not per swap. |
| Category | System-level |
| Hoare Triple | `{lastSwapBlock[poolId] == B, block.number == B}` → `adapter.onSwap(v3Event for poolId)` → `{callback suppressed OR merged, swapCount increments <= 1}` |
| Affected | ReactiveHookAdapter (or Reactive Subscription Contract) |
| Verification | Fuzz test (`testFuzz_swapDedup_perBlock`) |
