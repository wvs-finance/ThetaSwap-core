# Invariants: Fee Concentration Index

**Feature**: [spec.md](./spec.md) | **Data Model**: [data-model.md](./data-model.md)
**Updated**: 2026-03-06 (v2 — co-primary state + diamond pattern)
**Count**: 21 invariants (INV-001–010 position tracking, FCI-001–011 co-primary state)

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
| Description | The accumulated sum only increases. Each afterRemoveLiquidity adds a non-negative term (theta_k * x_k^2 >= 0). |
| Category | System-level |
| Hoare Triple | `{fciState.accumulatedSum == S}` → `afterRemoveLiquidity(...)` → `{fciState.accumulatedSum >= S}` |
| Affected | FeeConcentrationStateMod, FeeConcentrationIndex |
| Verification | Kontrol proof (`prove_accumulatedSum_monotonic`) + fuzz test |

---

## INV-009: Index A Capped at One

| Field | Value |
|-------|-------|
| ID | INV-009 |
| Description | The fee concentration index A_T = sqrt(accumulatedSum) is capped at 1 (Q128: 2^128). Rounding cannot produce out-of-range values. |
| Category | Type-level |
| Hoare Triple | `{fciState.accumulatedSum == S}` → `toIndexA(fciState)` → `{0 <= A_T <= 2^128}` |
| Affected | FeeConcentrationStateMod |
| Verification | Kontrol proof (`prove_indexA_capped_at_one`) |

---

## INV-010: Zero Lifetime Skips Index Update

| Field | Value |
|-------|-------|
| ID | INV-010 |
| Description | When a position has lifetime == 0 (no swap ever used its liquidity), the index is not updated. theta is undefined and x_k must be 0. |
| Category | System-level |
| Hoare Triple | `{swapCount[pos] == 0, fciState.accumulatedSum == S}` → `afterRemoveLiquidity(pos)` → `{fciState.accumulatedSum == S}` |
| Affected | FeeConcentrationIndex, PositionLifetimeMod |
| Verification | Kontrol proof (`prove_zero_lifetime_skipped`) + fuzz test |

---

## FCI-001: Index Boundedness

| Field | Value |
|-------|-------|
| ID | FCI-001 |
| Description | The fee concentration index A_T = sqrt(accumulatedSum) is in [0, 1] at all times. A_T = 0 when no positions removed. A_T = 1 is theoretical maximum (single JIT monopoly). |
| Category | Type-level |
| Hoare Triple | `{fciState = any valid state}` → `toIndexA(fciState)` → `{0 <= result <= Q128}` |
| Affected | FeeConcentrationStateMod |
| Verification | Kontrol proof (`prove_fci_indexBoundedness`) |

---

## FCI-002: Theta Sum Non-Negativity

| Field | Value |
|-------|-------|
| ID | FCI-002 |
| Description | The aggregate turnover rate thetaSum = sum(1/blockLifetime_k) is non-negative since each theta_k = 1/blockLifetime_k > 0. Stored as uint256 in Q128. |
| Category | Type-level |
| Hoare Triple | `{fciState.thetaSum == T}` → `addTerm(fciState, blockLifetime, xSquaredQ128)` → `{fciState.thetaSum >= T}` |
| Affected | FeeConcentrationStateMod |
| Verification | Kontrol proof (`prove_fci_thetaSumNonNeg`) |

---

## FCI-003: Position Count Non-Negativity

| Field | Value |
|-------|-------|
| ID | FCI-003 |
| Description | The active position count posCount is a non-negative uint256. It increments on afterAddLiquidity and decrements on afterRemoveLiquidity. |
| Category | Type-level |
| Hoare Triple | `{fciState.posCount == N}` → `decrementPos(fciState)` → `{N > 0 => fciState.posCount == N - 1}` |
| Affected | FeeConcentrationStateMod |
| Verification | Kontrol proof (`prove_fci_posCountNonNeg`) |

---

## FCI-004: Null Lower Bound

| Field | Value |
|-------|-------|
| ID | FCI-004 |
| Description | When posCount > 0, A_T >= atNull (the Ma-Crapis equal-share null). Equivalently, deltaPlus >= 0. The real concentration index is always at least as large as what symmetric competition would produce. |
| Category | System-level |
| Hoare Triple | `{fciState.posCount > 0}` → `deltaPlus(fciState)` → `{result >= 0}` |
| Affected | FeeConcentrationStateMod |
| Verification | Fuzz test (`testFuzz_fci_nullLowerBound`) — formal proof deferred (depends on economic model correctness) |

---

## FCI-005: Deviation Non-Negativity

| Field | Value |
|-------|-------|
| ID | FCI-005 |
| Description | Delta+ = max(0, A_T - atNull) >= 0 by construction (max with zero). |
| Category | Function-level |
| Hoare Triple | `{fciState = any valid state}` → `deltaPlus(fciState)` → `{result >= 0}` |
| Affected | FeeConcentrationStateMod |
| Verification | Kontrol proof (`prove_fci_deviationNonNeg`) |

---

## FCI-006: Deviation Upper Bound

| Field | Value |
|-------|-------|
| ID | FCI-006 |
| Description | Delta+ < 1 (strictly). Since A_T <= 1 and atNull >= 0, Delta+ <= 1. Strict inequality when posCount >= 1 (atNull > 0). This ensures p = Delta+/(1-Delta+) is well-defined (no division by zero). |
| Category | Type-level |
| Hoare Triple | `{fciState = any valid state}` → `deltaPlus(fciState)` → `{result < Q128}` |
| Affected | FeeConcentrationStateMod |
| Verification | Kontrol proof (`prove_fci_deviationUpperBound`) |

---

## FCI-007: Co-Primary Consistency

| Field | Value |
|-------|-------|
| ID | FCI-007 |
| Description | atNull and deltaPlus are deterministic functions of (accumulatedSum, thetaSum, posCount). No additional state needed. atNull = sqrt(thetaSum / posCount^2), deltaPlus = max(0, toIndexA - atNull). |
| Category | Function-level |
| Hoare Triple | `{fciState1 == fciState2}` → `deltaPlus(fciState1), deltaPlus(fciState2)` → `{result1 == result2}` |
| Affected | FeeConcentrationStateMod |
| Verification | Kontrol proof (`prove_fci_coPrimaryConsistency`) |

---

## FCI-008: Liquidity Event Atomicity

| Field | Value |
|-------|-------|
| ID | FCI-008 |
| Description | All three co-primary state variables (accumulatedSum, thetaSum, posCount) update atomically at each afterRemoveLiquidity. No intermediate state is observable where some are updated and others are not. |
| Category | System-level |
| Hoare Triple | `{fciState = (S, T, N)}` → `afterRemoveLiquidity(...)` → `{fciState = (S', T', N') where all three updated}` |
| Affected | FeeConcentrationIndex, FeeConcentrationStateMod |
| Verification | Kontrol proof (`prove_fci_liquidityEventAtomicity`) |

---

## FCI-009: Price Non-Negativity

| Field | Value |
|-------|-------|
| ID | FCI-009 |
| Description | The concentration price p = deltaPlus / (Q128 - deltaPlus) >= 0. Since deltaPlus >= 0 (FCI-005) and Q128 - deltaPlus > 0 (FCI-006). |
| Category | Function-level |
| Hoare Triple | `{fciState = any valid state}` → `toDeltaPlusPrice(fciState)` → `{result >= 0}` |
| Affected | FeeConcentrationStateMod |
| Verification | Kontrol proof (`prove_fci_priceNonNeg`) |

---

## FCI-010: Price Monotonicity

| Field | Value |
|-------|-------|
| ID | FCI-010 |
| Description | Higher deltaPlus implies higher price. The mapping p = delta/(1-delta) is strictly increasing. |
| Category | Function-level |
| Hoare Triple | `{delta1 < delta2, delta1 < Q128, delta2 < Q128}` → `p1 = delta1/(Q128-delta1), p2 = delta2/(Q128-delta2)` → `{p1 < p2}` |
| Affected | FeeConcentrationStateMod |
| Verification | Kontrol proof (`prove_fci_priceMonotonicity`) |

---

## FCI-011: Price-Deviation Invertibility

| Field | Value |
|-------|-------|
| ID | FCI-011 |
| Description | deltaPlus = p/(1+p) is the unique inverse of p = deltaPlus/(1-deltaPlus). The mapping is a bijection from [0,1) to [0, infinity). |
| Category | Function-level |
| Hoare Triple | `{delta < Q128}` → `p = delta/(Q128-delta), delta' = p*Q128/(Q128+p)` → `{delta' == delta}` |
| Affected | FeeConcentrationStateMod |
| Verification | Kontrol proof (`prove_fci_priceInvertibility`) |
