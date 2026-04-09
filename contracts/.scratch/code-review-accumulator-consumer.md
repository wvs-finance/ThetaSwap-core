# Code Review: AngstromAccumulatorConsumer vs BTT Spec

**File:** `contracts/src/_adapters/AngstromAccumulatorConsumer.sol`
**Spec:** `contracts/.scratch/angstrom-accumulator-consumer-btt-spec.md`
**Date:** 2026-04-09

---

## Checkpoint Results

| # | Checkpoint | Result | Notes |
|---|-----------|--------|-------|
| 1 | Constructor takes `(IAngstromAuth, IPoolManager)`, stores as immutables | PASS | Lines 35-38. `ANGSTROM` and `UNI_V4` set as immutables, no validation (matches spec). |
| 2 | `globalGrowth`: slot derivation via `SlotDerivation.deriveMapping` + `POOL_REWARDS_SLOT` + `REWARD_GROWTH_SIZE` offset | PASS | Lines 43-46. `deriveMapping(bytes32, bytes32)` resolves to `keccak256(abi.encode(poolId, 7))`, then `.offset(16777216)`. Matches spec formula. |
| 3 | `growthInside`: 3-branch tick logic with unchecked arithmetic | PASS | Lines 49-70. All three branches match spec table exactly: `currentTick < tickLower` -> `below - above`, `currentTick >= tickUpper` -> `above - below`, in-range -> `global - below - above`. All inside `unchecked` block. |
| 4 | `lastBlockUpdated`: extsload slot 3, extract lower 64 bits via `>> LAST_BLOCK_BIT_OFFSET` | PASS | Lines 75-77. `uint64(value >> 0)` == `uint64(value)`, correctly extracts lower 64 bits. Matches AngstromView L26-28 exactly. |
| 5 | `configStore`: extsload slot 3, extract upper bits as address via `>> STORE_BIT_OFFSET` | PASS | Lines 80-83. `address(uint160(value >> 64))` matches AngstromView L30-33 exactly. |
| 6 | `poolExists`: validates `token0 < token1`, derives StoreKey, iterates configStore entries, returns bool | PASS | Lines 90-103. All BTT branches covered: `token0 >= token1` -> false (L91), null configStore -> false (L95), iteration with `getWithDefaultEmpty` + `isEmpty` check (L98-101), fallthrough false (L102). |
| 7 | `getPoolConfig`: derives StoreKey, calls `configStore().get(key, index)` | PASS | Lines 110-117. Delegates to `PoolConfigStoreLib.get` which reverts `NoEntry` on mismatch. No token ordering validation (matches spec's explicit design note). |
| 8 | All functions are `view` (no state writes) | PASS | `globalGrowth` (external view), `growthInside` (external view), `lastBlockUpdated` (external view), `configStore` (public view), `poolExists` (external view), `getPoolConfig` (external view). No storage writes anywhere. |
| 9 | Contract name is `AngstromAccumulatorConsumer` | PASS | Line 16. |
| 10 | Slot constants match spec table | PASS | L18: `POOL_REWARDS_SLOT=7`, L19: `REWARD_GROWTH_SIZE=16777216`, L21: `LAST_BLOCK_CONFIG_STORE_SLOT=3`, L22: `LAST_BLOCK_BIT_OFFSET=0`, L23: `STORE_BIT_OFFSET=64`, L20: `POOLS_SLOT=6`. All match. |

---

## Minor Observations (non-blocking)

**`configStore` visibility: `public` vs spec's `external`.**
The spec declares `configStore() external view` but the implementation uses `public view`. This is intentional and correct -- `poolExists` calls `configStore()` internally (L94), which requires `public`. The `public` visibility is a strict superset of `external` for view functions. No behavioral difference for external callers.

---

## Verdict

**10/10 checkpoints PASS.** Implementation is faithful to the BTT specification. No blockers, no suggestions.
