# Security Audit: AngstromAccumulatorConsumer.sol

**File:** `contracts/src/_adapters/AngstromAccumulatorConsumer.sol`
**Auditor:** Blockchain Security Auditor
**Date:** 2026-04-09
**Commit:** thetaswap-patches branch (994d3d2)

---

## Summary

| Severity      | Count |
|---------------|-------|
| Critical      | 0     |
| High          | 0     |
| Medium        | 0     |
| Low           | 1     |
| Informational | 3     |

The contract is a faithful read-only mirror of Angstrom's internal storage access patterns. No exploitable vulnerabilities were found. All seven focus areas pass with notes.

---

## Findings

### [L-01] Unused constant POOLS_SLOT = 6

**Severity:** Low
**Status:** Open
**Location:** Line 20

`POOLS_SLOT = 6` is declared but never referenced in any function. It corresponds to Uniswap V4's PoolManager `_POOLS_SLOT`, not Angstrom's slot 6 (which is `positions`). Dead code in constants is benign but creates confusion for future maintainers who might misinterpret it as an Angstrom slot.

**Recommendation:** Remove the unused constant.

---

### [I-01] `>> 0` is a semantic no-op in lastBlockUpdated

**Severity:** Informational
**Status:** Open
**Location:** Line 76

```solidity
return uint64(ANGSTROM.extsload(LAST_BLOCK_CONFIG_STORE_SLOT) >> LAST_BLOCK_BIT_OFFSET);
```

`LAST_BLOCK_BIT_OFFSET = 0`, so `>> 0` is a no-op. This is a direct copy of AngstromView's pattern (line 27) and serves a documentation purpose: it makes the bit-extraction symmetric with `>> STORE_BIT_OFFSET` on line 82. The compiler optimizes it away. No action required, but a comment would clarify intent.

---

### [I-02] No constructor validation on zero addresses

**Severity:** Informational
**Status:** Open (by design per BTT spec)
**Location:** Lines 35-38

Deploying with `ANGSTROM = address(0)` or `UNI_V4 = address(0)` produces a contract where all view functions revert (extsload/staticcall to address(0) fails). The BTT spec explicitly acknowledges this as "correct fail-safe behavior." No remediation needed, but the behavior is worth documenting in NatSpec.

---

### [I-03] POOLS_SLOT naming ambiguity

**Severity:** Informational
**Status:** Open
**Location:** Line 20

The constant `POOLS_SLOT = 6` shares its name with `IUniV4._POOLS_SLOT = 6` (Uniswap V4 PoolManager) but in Angstrom's storage layout, slot 6 is `positions` (from PoolUpdates). If a future developer uses this constant to read from ANGSTROM (rather than UNI_V4), they would read incorrect data. Covered by L-01; removing the constant eliminates the ambiguity.

---

## Focus Area Results

### 1. Slot constant correctness -- PASS

| Constant                      | Value      | Angstrom Source                           | Match |
|-------------------------------|------------|-------------------------------------------|-------|
| `POOL_REWARDS_SLOT`           | `7`        | `mapping(PoolId => PoolRewards)` in PoolUpdates (slot 7 via C3 linearization) | Yes |
| `REWARD_GROWTH_SIZE`          | `16777216` | `uint256 constant REWARD_GROWTH_SIZE` in PoolRewards.sol (line 10) | Yes |
| `LAST_BLOCK_CONFIG_STORE_SLOT`| `3`        | `AngstromView.LAST_BLOCK_CONFIG_STORE_SLOT = 3` (line 16) | Yes |
| `LAST_BLOCK_BIT_OFFSET`       | `0`        | `AngstromView.LAST_BLOCK_BIT_OFFSET = 0` (line 17) | Yes |
| `STORE_BIT_OFFSET`            | `64`       | `AngstromView.STORE_BIT_OFFSET = 64` (line 18) | Yes |

Storage layout verified through C3 linearization of `Angstrom is EIP712, OrderInvalidation, Settlement, PoolUpdates, UnlockHook, IUnlockCallback, PermitSubmitterHook`:
- TopLevelAuth state: slots 0-3 (`_controller`, `_isNode`, `_unlockedFees`, packed `_lastBlockUpdated`+`_configStore`)
- Settlement state: slots 4-5 (`bundleDeltas`, `_balances`)
- PoolUpdates state: slots 6-7 (`positions`, `poolRewards`)

Cross-verified against `AngstromView.BALANCES_SLOT = 5` and `AngstromView.CONTROLLER_SLOT = 0`.

### 2. extsload safety -- PASS

`ANGSTROM.extsload(slot)` is a `staticcall` to a function that does `sload(slot)` and returns the result. If `ANGSTROM` is `address(0)`, the staticcall fails and the transaction reverts. This is safe -- no silent corruption.

For nonexistent slots, `sload` returns 0, which is the correct default for all accumulator reads (zero growth, zero block number, null config store address). The consumer correctly handles these zero values in all code paths.

### 3. growthInside unchecked arithmetic -- PASS

The 3-branch formula uses `unchecked` subtraction on uint256 accumulators. This is **intentionally correct** -- it exactly mirrors `PoolRewardsLib.getGrowthInside()` in `PoolRewards.sol` (lines 26-44), which also uses `unchecked` arithmetic. Angstrom's accumulator semantics rely on modular uint256 arithmetic for growth tracking (same pattern as Uniswap V3/V4 fee growth accumulators). Wrapping underflow produces correct results when the values are later subtracted from each other by the consumer (the observer layer).

Branch conditions match the canonical implementation:
- Consumer: `currentTick < tickLower` / `currentTick >= tickUpper` / else
- PoolRewards: `current < lower` / `upper <= current` / else
- These are logically equivalent.

### 4. poolExists gas griefing -- PASS (bounded risk)

`poolExists` iterates `store.totalEntries()` which is `PoolConfigStore.unwrap(store).code.length / ENTRY_SIZE`. The PoolConfigStore is an SSTORE2 contract deployed by Angstrom's `configurePool`/`batchUpdatePools` admin functions. Only the Angstrom controller (admin) can modify it.

An attacker cannot deploy an arbitrary PoolConfigStore and have this contract read it -- the store address is read from Angstrom's own storage (slot 3). The controller would have to maliciously deploy a store with millions of entries to cause DoS, which is an admin-trust issue, not an external attack vector. The BTT spec acknowledges the linear scan and notes the store is "expected to be small (tens of entries)."

Verdict: Not exploitable by external actors. The admin-trust assumption is documented and acceptable.

### 5. getPoolConfig StoreKey derivation -- PASS

`getPoolConfig` calls `StoreKeyLib.keyFromAssetsUnchecked(token0, token1)` without validating `token0 < token1`. If unsorted, the derived StoreKey will not match any entry, and `PoolConfigStoreLib.get()` reverts with `NoEntry`. This is a safe failure mode -- no incorrect data is returned. The BTT spec documents this as intentional (section 6: "silent failure via revert rather than returning incorrect data").

`poolExists` does validate sorting (`if (token0 >= token1) return false`), which is a reasonable UX choice: existence checks return false, config lookups revert.

### 6. lastBlockUpdated bit extraction -- PASS (see I-01)

`>> 0` is a compile-time no-op. It serves as documentation symmetry with `>> STORE_BIT_OFFSET`. The pattern is copied directly from `AngstromView.lastBlockUpdated()` (line 27). No functional issue.

### 7. configStore null address -- PASS

If `configStore()` returns `address(0)`:
- `poolExists`: Explicitly checks `if (PoolConfigStore.unwrap(store) == address(0)) return false;` (line 95). Safe.
- `getPoolConfig`: Calls `configStore().get(key, index)` which calls `getWithDefaultEmpty` which does `extcodecopy(address(0), ...)`. `extcodecopy` on `address(0)` reads empty bytecode (code length = 0), so the entry will be all zeros, `entry.isEmpty()` returns true, and `get()` reverts with `NoEntry`. Safe.
- `totalEntries()` on `address(0)`: Returns `address(0).code.length / ENTRY_SIZE = 0 / ENTRY_SIZE = 0`. The loop in `poolExists` would execute 0 iterations. But this path is unreachable because the explicit null check on line 95 returns false first. Safe.

---

## Conclusion

AngstromAccumulatorConsumer is a clean, minimal read-only adapter. The storage slot constants are correctly derived from Angstrom's C3-linearized layout. The unchecked accumulator arithmetic matches the canonical implementation. All edge cases (null addresses, unsorted tokens, nonexistent pools) are handled safely. The only actionable item is removing the unused `POOLS_SLOT` constant.
