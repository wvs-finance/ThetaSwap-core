# Invariants: Fee Concentration Index

**Feature**: [spec.md](./spec.md) | **Data Model**: [data-model.md](./data-model.md)
**Count**: 10 invariants

---

## INV-001: SwapCount Monotonicity

| Field | Value |
|-------|-------|
| ID | INV-001 |
| Description | A position's swap count never decreases. It can only be incremented by 1 or remain unchanged. |
| Category | System-level |
| Hoare Triple | `{swapCount[pos] == n}` → `afterSwap(...)` → `{swapCount[pos] == n \|\| swapCount[pos] == n + 1}` |
| Affected | SwapCountMod, PositionLifetimeMod |
| Verification | Kontrol proof (`prove_swapCount_increment_monotonic`) + fuzz test |

---

## INV-002: SwapCount Initial Zero

| Field | Value |
|-------|-------|
| ID | INV-002 |
| Description | Every newly registered position starts with swap count exactly 0. |
| Category | Function-level |
| Hoare Triple | `{pos not in swapCounts}` → `afterAddLiquidity(pos)` → `{swapCount[pos] == 0}` |
| Affected | PositionLifetimeMod |
| Verification | Kontrol proof (`prove_swapCount_initial_zero`) + fuzz test |

---

## INV-003: Tick Range Selective Increment

| Field | Value |
|-------|-------|
| ID | INV-003 |
| Description | afterSwap only increments swap count for positions whose tick range overlaps the swap's traversed tick range. Positions outside the range are untouched. |
| Category | System-level |
| Hoare Triple | `{swapCount[pos] == n, pos.tickRange NOT overlapping swap range}` → `afterSwap(...)` → `{swapCount[pos] == n}` |
| Affected | PositionLifetimeMod, TickRangeRegistryMod |
| Verification | Fuzz test (`testFuzz_only_active_range_incremented`) |

---

## INV-004: Registry Consistency

| Field | Value |
|-------|-------|
| ID | INV-004 |
| Description | A position key exists in exactly one tick range's array, and the reverse mapping (positionRangeKey) is consistent with the forward mapping (positionsByRange). |
| Category | System-level |
| Hoare Triple | `{positionsByRange[rk][idx] == pk}` → `any operation` → `{positionIndex[pk] == idx AND positionRangeKey[pk] == rk}` |
| Affected | TickRangeRegistryMod |
| Verification | Kontrol proof (`prove_register_adds_position`, `prove_deregister_removes_position`) + fuzz test |

---

## INV-005: Empty Range Cleanup

| Field | Value |
|-------|-------|
| ID | INV-005 |
| Description | When the last position is deregistered from a tick range, the range entry is deleted entirely. No ghost entries remain. |
| Category | System-level |
| Hoare Triple | `{positionsByRange[rk].length == 1}` → `deregister(rk, pk)` → `{positionsByRange[rk].length == 0}` |
| Affected | TickRangeRegistryMod |
| Verification | Kontrol proof (`prove_deregister_last_deletes_range`) |

---

## INV-006: Fee Share Ratio Bounds

| Field | Value |
|-------|-------|
| ID | INV-006 |
| Description | The fee share ratio x_k is always in [0, 1], stored as Q128 in [0, 2^128]. |
| Category | Type-level |
| Hoare Triple | `{feeGrowthInside >= 0, feeGrowthGlobal >= 0}` → `computeFeeShare(inside, global)` → `{0 <= x_k <= 2^128}` |
| Affected | FeeShareRatioMod, FeeConcentrationIndexMod |
| Verification | Kontrol proof (`prove_feeShareRatio_bounds`) + fuzz test |

---

## INV-007: Fee Share Zero When No Fees

| Field | Value |
|-------|-------|
| ID | INV-007 |
| Description | When feeGrowthGlobal is 0 (no swaps occurred), the fee share ratio returns 0. Division by zero is avoided. |
| Category | Function-level |
| Hoare Triple | `{feeGrowthGlobal == 0}` → `computeFeeShare(inside, 0)` → `{x_k == 0}` |
| Affected | FeeShareRatioMod, FeeConcentrationIndexMod |
| Verification | Kontrol proof (`prove_feeShareRatio_zero_when_no_global_fees`) |

---

## INV-008: Accumulated Sum Monotonicity

| Field | Value |
|-------|-------|
| ID | INV-008 |
| Description | The accumulated HHI sum only increases. Each afterRemoveLiquidity adds a non-negative term (theta_k * x_k^2 >= 0). |
| Category | System-level |
| Hoare Triple | `{accumulatedHHI == S}` → `afterRemoveLiquidity(...)` → `{accumulatedHHI >= S}` |
| Affected | AccumulatedHHIMod, FeeConcentrationIndexMod |
| Verification | Kontrol proof (`prove_accumulatedHHI_monotonic`) + fuzz test |

---

## INV-009: Index A Capped at One

| Field | Value |
|-------|-------|
| ID | INV-009 |
| Description | The fee concentration index A_T = sqrt(accumulatedSum) is capped at 1 (Q128: 2^128). B_T = 1 - A_T is capped at 0. Rounding cannot produce out-of-range values. |
| Category | Type-level |
| Hoare Triple | `{accumulatedHHI == S}` → `readIndex()` → `{0 <= A_T <= 2^128 AND B_T == 2^128 - A_T AND B_T >= 0}` |
| Affected | AccumulatedHHIMod |
| Verification | Kontrol proof (`prove_indexA_capped_at_one`, `prove_indexB_complement`) |

---

## INV-010: Zero Lifetime Skips Index Update

| Field | Value |
|-------|-------|
| ID | INV-010 |
| Description | When a position has lifetime == 0 (no swap ever used its liquidity), the index is not updated. theta is undefined and x_k must be 0. |
| Category | System-level |
| Hoare Triple | `{swapCount[pos] == 0, accumulatedHHI == S}` → `afterRemoveLiquidity(pos)` → `{accumulatedHHI == S}` |
| Affected | FeeConcentrationIndexMod, PositionLifetimeMod |
| Verification | Kontrol proof (`prove_zero_lifetime_skipped`) + fuzz test |
