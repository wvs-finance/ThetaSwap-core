# FCI Multi-Metric Oracle Implementation Plan (Revised)

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add epoch-reset and sliding-window Δ⁺ metrics as parallel oracle APIs alongside the existing cumulative metric, 
so the FCI oracle exposes three independent concentration signals from the same position-exit data.

**Architecture:** 
Epoch reuses `FeeConcentrationState` directly via an epoch-indexed mapping 
(Option C: destruction by abandonment). 

On epoch expiry, `currentEpochId` advances to a new timestamp key — the old `FeeConcentrationState` at the old key becomes unreachable, and a fresh zero-initialized state is used. 
No separate epoch type file needed.

**Why a mapping, not a CircularBuffer or other OZ data structure:**
We only ever access the *current* epoch — never historical ones. A `mapping(uint256 => FeeConcentrationState)` with an advancing timestamp key gives O(1) access with zero bookkeeping. Abandoned slots cost nothing at runtime (no `delete`, no SSTORE zeroing). Dead storage is ~4 slots/pool/epoch (~46 KB/year at daily epochs) — negligible. OZ `CircularBuffer` (5.1) adds fixed-capacity tracking and modular indexing for no benefit when you only need the current entry. OZ `Checkpoints` is designed for governance snapshots with binary search over history — overkill here. A ring buffer becomes relevant only for the Window metric (deferred), which needs per-position contribution history.

Window (deferred) needs per-position contributions in a ring buffer — fundamentally new data.

**Design decision (Option C):** Each epoch is keyed by `epochStates[poolId][epochId]` where `epochId = block.timestamp` at epoch start. When the epoch expires, advancing `currentEpochId` naturally creates a new zero mapping slot. Old state is abandoned — no `delete`, no zeroing SSTOREs, no gas overhead. Dead storage is negligible (~4 slots per pool per epoch).

**Tech Stack:** Solidity ^0.8.26, Foundry (forge), Solady FixedPointMathLib, typed-uniswap-v4 types (BlockCount, Q128, FeeConcentrationState), SCOP pattern (file-level free functions, no `library` keyword, no contract inheritance in production)

**Phase 2 Results (from backtest):**
- epoch(1d): corr=1.000 to daily-snapshot Δ⁺ (trivially perfect — IS the daily snapshot)
- window(10): corr=0.909 (best non-trivial, exceeds 0.8 threshold)
- decay(*): corr<0.72 (dropped — not implemented)

**Constraints:**
- No modifications to existing files except `FeeConcentrationIndex.sol` (fan-out + views) and `IFeeConcentrationIndex.sol` (new view functions)
- No modifications to existing tests
- Each code change: user review → forge build → forge test (zero regressions)
- SCOP: no `library` keyword, no `is` inheritance in production, no `modifier` keyword
- Diamond storage: each module gets its own `keccak256("thetaSwap.fci.<mechanism>")` slot

**Task order:** Epoch first (reuses existing `FeeConcentrationState`), window deferred to end (needs new ring buffer data structure).

---

## File Structure

### New files (created):

| File | Responsibility |
|------|---------------|
| `src/fee-concentration-index/modules/FeeConcentrationEpochStorageMod.sol` | Epoch diamond storage: epoch-indexed `mapping(PoolId => mapping(uint256 => FeeConcentrationState))`, `addEpochTerm()`, `epochDeltaPlus()`, `initializeEpoch()` |
| `src/fee-concentration-index/modules/FeeConcentrationEpochReactiveExtMod.sol` | Reactive dispatch wrapper for epoch: `addEpochTerm(hookData, ...)` |
| `test/fee-concentration-index/unit/EpochMetric.t.sol` | Unit tests for epoch storage module |
| `test/fee-concentration-index/fuzz/EpochMetric.fuzz.t.sol` | Fuzz tests for epoch metric invariants |
| `research/data/scripts/fci_epoch_oracle.py` | Python reference for epoch metric (differential testing) |

### Deferred (window — future work):

| File | Responsibility |
|------|---------------|
| `src/fee-concentration-index/modules/FeeConcentrationWindowStorageMod.sol` | Window diamond storage with ring buffer of per-position contributions |
| `src/fee-concentration-index/modules/FeeConcentrationWindowReactiveExtMod.sol` | Reactive dispatch wrapper for window |
| `test/fee-concentration-index/unit/WindowMetric.t.sol` | Unit tests for window |
| `test/fee-concentration-index/fuzz/WindowMetric.fuzz.t.sol` | Fuzz tests for window |
| `research/data/scripts/fci_window_oracle.py` | Python reference for window metric |

### Modified files (minimal additions only):

| File | Change |
|------|--------|
| `src/fee-concentration-index/FeeConcentrationIndex.sol:163-165` | After `addStateTerm(...)`, add `addEpochTerm(...)` call |
| `src/fee-concentration-index/FeeConcentrationIndex.sol:173-196` | Add `getDeltaPlusEpoch()` view function |
| `src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol` | Add `getDeltaPlusEpoch()` to interface |

### Untouched (verified by zero test regressions):

- `FeeConcentrationIndexStorageMod.sol` — existing cumulative storage
- `FeeConcentrationStateMod.sol` — existing cumulative state (in typed-uniswap-v4 dep, **reused** by epoch)
- All existing tests
- `FciTokenVaultMod.sol` — vault still calls `getDeltaPlus()` (cumulative)
- Reactive integration modules

---

## Chunk 1: Epoch Core

### Task 1: Epoch Storage Module [DONE]

**Files:**
- Create: `src/fee-concentration-index/modules/FeeConcentrationEpochStorageMod.sol`

**Design:** Epoch-indexed mapping (Option C — destruction by abandonment). Reuses `FeeConcentrationState` from `typed-uniswap-v4`. No separate epoch type file.

- [x] **Step 1: Write epoch storage struct + slot constant** — DONE
- [x] **Step 2: Write `epochFciStorage()` diamond pointer** — DONE
- [x] **Step 3: Write `addEpochTerm()` with epoch expiry check** — DONE
- [x] **Step 4: Write no-arg `addEpochTerm()` overload** — DONE
- [x] **Step 5: Write `epochDeltaPlus()` read function + no-arg overload** — DONE
- [x] **Step 6: Write `initializeEpoch()` + no-arg overload** — DONE
- [x] **Step 7: Verify compilation** — DONE (forge build clean)
- [x] **Step 8: Verify no test regressions** — DONE (47/47 pass)
- [x] **Step 9: Add `reactiveEpochFciStorage()`** — DONE (review feedback: needed for Chunk 3 Task 9)

---

### Task 2: Interface + Fan-out + View Function

**Files:**
- Modify: `src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol`
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol`

- [ ] **Step 1: Add `getDeltaPlusEpoch` to the interface**

Add after `getThetaSum` (line 40):

```solidity
    /// @notice Returns epoch-reset Δ⁺ for the pool, Q128-scaled.
    /// @dev Accumulators reset each epoch (destruction by abandonment).
    /// Returns current epoch's Δ⁺, or 0 if epoch expired with no new data.
    function getDeltaPlusEpoch(PoolKey calldata key, bool reactive)
        external
        view
        returns (uint128 deltaPlus_);
```

- [ ] **Step 2: Add import + fan-out call in FeeConcentrationIndex.sol**

Add import after line 24:

```solidity
import {
    FeeConcentrationEpochStorage, epochFciStorage,
    addEpochTerm, epochDeltaPlus, initializeEpoch
} from "./modules/FeeConcentrationEpochStorageMod.sol";
```

Add after line 165 (`addStateTerm(hookData, poolId, blockLifetime, xSquaredQ128);`):

Note: Uses no-arg overload (V4-only for now). Reactive dispatch added later in Chunk 3 after epoch passes integration tests.

```solidity
            addEpochTerm(poolId, blockLifetime, xSquaredQ128);
```

- [ ] **Step 3: Add `getDeltaPlusEpoch` view function + `initializeEpochPool` admin function**

Add after `getThetaSum` (line 196):

Note: `reactive` param kept in signature for interface compatibility. Reactive storage routing added in Chunk 3.

```solidity
    function getDeltaPlusEpoch(PoolKey calldata key, bool reactive) external view returns (uint128 deltaPlus_) {
        // TODO(chunk-3): reactive ? reactiveEpochFciStorage() : epochFciStorage()
        deltaPlus_ = epochDeltaPlus(PoolIdLibrary.toId(key));
    }

    /// @notice Initialize epoch metric for a pool. Must be called before epoch accumulation begins.
    /// @param key The pool key.
    /// @param epochLengthSeconds Epoch duration in seconds (e.g. 86400 for 1 day).
    function initializeEpochPool(PoolKey calldata key, uint256 epochLengthSeconds) external {
        initializeEpoch(PoolIdLibrary.toId(key), epochLengthSeconds);
    }
```

Also add to `IFeeConcentrationIndex.sol`:

```solidity
    /// @notice Initialize epoch metric for a pool.
    function initializeEpochPool(PoolKey calldata key, uint256 epochLengthSeconds) external;
```

- [ ] **Step 4: Verify compilation**

Run: `forge build`

- [ ] **Step 5: Verify no test regressions**

Run: `forge test --match-path "test/fee-concentration-index/**" -v`

- [ ] **Step 6: Commit**

```bash
git add src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol \
        src/fee-concentration-index/FeeConcentrationIndex.sol
git commit -m "feat(004): wire epoch fan-out in afterRemoveLiquidity + getDeltaPlusEpoch view"
```

---

### Task 3: Epoch Unit Tests

**Files:**
- Create: `test/fee-concentration-index/unit/EpochMetric.t.sol`

- [ ] **Step 1: Write unit tests**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "forge-std/Test.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {FeeConcentrationState} from "typed-uniswap-v4/fee-concentration-index/types/FeeConcentrationStateMod.sol";
import {BlockCount} from "typed-uniswap-v4/fee-concentration-index/types/BlockCountMod.sol";
import {
    FeeConcentrationEpochStorage,
    epochFciStorage,
    addEpochTerm,
    epochDeltaPlus,
    initializeEpoch
} from "@fee-concentration-index/modules/FeeConcentrationEpochStorageMod.sol";

contract EpochMetricTest is Test {
    uint256 constant Q128 = 1 << 128;
    uint256 constant EPOCH_1D = 86400;

    PoolId constant POOL = PoolId.wrap(bytes32(uint256(1)));

    function setUp() public {
        vm.warp(1000);
        initializeEpoch(POOL, EPOCH_1D);
    }

    function test_initializeEpoch() public view {
        FeeConcentrationEpochStorage storage $ = epochFciStorage();
        assertEq($.epochLength[POOL], EPOCH_1D);
        assertEq($.currentEpochId[POOL], 1000);
    }

    function test_addTerm_incrementsState() public {
        uint256 xSqQ128 = Q128 / 4; // x_k² = 0.25
        BlockCount bl = BlockCount.wrap(100);

        vm.warp(1500);
        addEpochTerm(POOL, bl, xSqQ128);

        FeeConcentrationEpochStorage storage $ = epochFciStorage();
        FeeConcentrationState storage state = $.epochStates[POOL][1000];
        assertEq(state.removedPosCount, 1);
        assertGt(state.accumulatedSum, 0);
        assertGt(state.thetaSum, 0);
    }

    function test_deltaPlus_zeroWhenEmpty() public view {
        assertEq(epochDeltaPlus(POOL), 0);
    }

    function test_epochExpiry_returnsZero() public {
        uint256 xSqQ128 = Q128 / 4;
        BlockCount bl = BlockCount.wrap(100);

        vm.warp(1500);
        addEpochTerm(POOL, bl, xSqQ128);
        assertGt(epochDeltaPlus(POOL), 0);

        // Advance past epoch boundary — no new data in new epoch
        vm.warp(1000 + EPOCH_1D + 1);
        assertEq(epochDeltaPlus(POOL), 0, "Expired epoch with no new data should return 0");
    }

    function test_epochAdvance_abandonsOldState() public {
        uint256 xSqQ128 = Q128 / 4;
        BlockCount bl = BlockCount.wrap(100);

        // Add term in first epoch
        vm.warp(1500);
        addEpochTerm(POOL, bl, xSqQ128);

        // Advance past epoch and add term — new epoch starts
        vm.warp(1000 + EPOCH_1D + 500);
        addEpochTerm(POOL, bl, xSqQ128);

        FeeConcentrationEpochStorage storage $ = epochFciStorage();
        // Old epoch state still has data (abandoned, not deleted)
        assertEq($.epochStates[POOL][1000].removedPosCount, 1);
        // New epoch ID is the new timestamp
        uint256 newEpochId = $.currentEpochId[POOL];
        assertEq(newEpochId, 1000 + EPOCH_1D + 500);
        // New epoch state has only the new term
        assertEq($.epochStates[POOL][newEpochId].removedPosCount, 1);
    }

    function test_uninitializedPool_silentlySkips() public {
        PoolId otherPool = PoolId.wrap(bytes32(uint256(999)));
        // epochLength == 0 for uninitialized pool
        vm.warp(1500);
        addEpochTerm(otherPool, BlockCount.wrap(100), Q128 / 4);
        // Should not revert, deltaPlus returns 0
        assertEq(epochDeltaPlus(otherPool), 0);
    }

    function test_deltaPlus_concentrated() public {
        // JIT: x_k²=0.81, bl=1
        uint256 xSq1 = (Q128 * 81) / 100;
        BlockCount bl1 = BlockCount.wrap(1);
        // Passive: x_k²=0.01, bl=10000
        uint256 xSq2 = Q128 / 100;
        BlockCount bl2 = BlockCount.wrap(10000);

        vm.warp(1500);
        addEpochTerm(POOL, bl1, xSq1);
        addEpochTerm(POOL, bl2, xSq2);

        assertGt(epochDeltaPlus(POOL), 0, "Concentrated positions should produce positive delta-plus");
    }
}
```

- [ ] **Step 2: Run epoch unit tests**

Run: `forge test --match-path "test/fee-concentration-index/unit/EpochMetric.t.sol" -vv`
Expected: All pass.

- [ ] **Step 3: Run full FCI suite for regressions**

Run: `forge test --match-path "test/fee-concentration-index/**" -v`
Expected: All existing + new tests pass.

- [ ] **Step 4: Commit**

```bash
git add test/fee-concentration-index/unit/EpochMetric.t.sol
git commit -m "test(004): unit tests for epoch metric storage module"
```

---

### Task 4: Epoch Fuzz Tests

**Files:**
- Create: `test/fee-concentration-index/fuzz/EpochMetric.fuzz.t.sol`

Key invariants:
- INV-E1: `epochDeltaPlus()` does not revert after arbitrary addEpochTerm sequences (idempotent reads)
- INV-E2: After epoch expires, `epochDeltaPlus()` returns 0 (no stale data)
- INV-E3: Equal fee shares (x_k = 1/N for all positions with same blocklife) → Δ⁺ = 0
- INV-E4: New epoch gets fresh zero state (abandoned old state doesn't leak)
- INV-E5: Exact epoch boundary (`block.timestamp == epochId + epochLen`) triggers expiry correctly

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "forge-std/Test.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {FeeConcentrationState} from "typed-uniswap-v4/fee-concentration-index/types/FeeConcentrationStateMod.sol";
import {BlockCount} from "typed-uniswap-v4/fee-concentration-index/types/BlockCountMod.sol";
import {
    FeeConcentrationEpochStorage,
    epochFciStorage,
    addEpochTerm,
    epochDeltaPlus,
    initializeEpoch
} from "@fee-concentration-index/modules/FeeConcentrationEpochStorageMod.sol";

contract EpochMetricFuzzTest is Test {
    uint256 constant Q128 = 1 << 128;
    uint256 constant EPOCH_1D = 86400;
    PoolId constant POOL = PoolId.wrap(bytes32(uint256(1)));

    function setUp() public {
        vm.warp(1000);
        initializeEpoch(POOL, EPOCH_1D);
    }

    /// @dev INV-E1: epochDeltaPlus does not revert and reads are idempotent.
    function testFuzz_deltaPlusNoRevertIdempotent(
        uint256 xSqQ128,
        uint256 blockLifetime,
        uint8 count
    ) public {
        blockLifetime = bound(blockLifetime, 1, 1e9);
        xSqQ128 = bound(xSqQ128, 0, Q128 - 1);
        count = uint8(bound(count, 1, 20));

        vm.warp(1500);
        for (uint256 i; i < count; i++) {
            addEpochTerm(POOL, BlockCount.wrap(blockLifetime), xSqQ128);
        }
        uint128 dp1 = epochDeltaPlus(POOL);
        uint128 dp2 = epochDeltaPlus(POOL);
        assertEq(dp1, dp2, "reads must be idempotent");
    }

    /// @dev INV-E2: Expired epoch with no new data returns 0.
    function testFuzz_expiredEpochReturnsZero(uint256 xSqQ128, uint256 blockLifetime) public {
        blockLifetime = bound(blockLifetime, 1, 1e9);
        xSqQ128 = bound(xSqQ128, 1, Q128 - 1);

        vm.warp(1500);
        addEpochTerm(POOL, BlockCount.wrap(blockLifetime), xSqQ128);

        vm.warp(1000 + EPOCH_1D + 1);
        assertEq(epochDeltaPlus(POOL), 0);
    }

    /// @dev INV-E3: Equal shares with same blocklife → Δ⁺ = 0.
    function testFuzz_equalSharesZeroDelta(uint256 blockLifetime, uint8 n) public {
        blockLifetime = bound(blockLifetime, 1, 1e6);
        n = uint8(bound(n, 2, 20));

        uint256 xSqQ128 = Q128 / (uint256(n) * uint256(n));

        vm.warp(1500);
        for (uint256 i; i < n; i++) {
            addEpochTerm(POOL, BlockCount.wrap(blockLifetime), xSqQ128);
        }
        assertEq(epochDeltaPlus(POOL), 0);
    }

    /// @dev INV-E4: New epoch starts with fresh state.
    function testFuzz_newEpochFreshState(uint256 xSqQ128, uint256 blockLifetime) public {
        blockLifetime = bound(blockLifetime, 1, 1e9);
        xSqQ128 = bound(xSqQ128, 1, Q128 - 1);

        // Add in first epoch
        vm.warp(1500);
        addEpochTerm(POOL, BlockCount.wrap(blockLifetime), xSqQ128);

        // Advance to new epoch
        vm.warp(1000 + EPOCH_1D + 500);
        // Only add one term in new epoch
        addEpochTerm(POOL, BlockCount.wrap(blockLifetime), xSqQ128);

        FeeConcentrationEpochStorage storage $ = epochFciStorage();
        uint256 newEpochId = $.currentEpochId[POOL];
        // New epoch should have exactly 1 position
        assertEq($.epochStates[POOL][newEpochId].removedPosCount, 1);
    }

    /// @dev INV-E5: Exact epoch boundary triggers expiry.
    function testFuzz_exactBoundaryTriggersExpiry(uint256 xSqQ128, uint256 blockLifetime) public {
        blockLifetime = bound(blockLifetime, 1, 1e9);
        xSqQ128 = bound(xSqQ128, 1, Q128 - 1);

        vm.warp(1500);
        addEpochTerm(POOL, BlockCount.wrap(blockLifetime), xSqQ128);
        assertGt(epochDeltaPlus(POOL), 0);

        // Warp to EXACT boundary: epochStart(1000) + epochLen(86400) = 87400
        vm.warp(1000 + EPOCH_1D);
        // View should return 0 (>= triggers expiry check)
        assertEq(epochDeltaPlus(POOL), 0, "exact boundary should trigger expiry");
    }
}
```

- [ ] **Step 1: Run fuzz tests**

Run: `forge test --match-path "test/fee-concentration-index/fuzz/EpochMetric.fuzz.t.sol" -vv`
Expected: All pass.

- [ ] **Step 2: Commit**

```bash
git add test/fee-concentration-index/fuzz/EpochMetric.fuzz.t.sol
git commit -m "test(004): fuzz tests for epoch metric invariants"
```

---

## Chunk 2: Validation (Python Oracles + Integration Test)

### Task 5: Python Epoch Oracle

**Files:**
- Create: `research/data/scripts/fci_epoch_oracle.py`

Python reference implementation mirroring the Solidity epoch storage module for differential testing via FFI. Uses the epoch-indexed mapping model (Option C).

- [ ] **Step 1: Write the epoch oracle**

```python
"""Epoch-reset FCI oracle — Python reference for Solidity differential testing.

Mirrors FeeConcentrationEpochStorageMod.sol (Option C: destruction by abandonment):
- Epoch-indexed mapping: each epoch gets a fresh FeeConcentrationState
- On epoch expiry, old state abandoned, new state at new epochId
- addTerm delegates to FeeConcentrationState.addTerm() (same math)
- deltaPlus delegates to FeeConcentrationState.deltaPlus()

Per @functional-python: frozen dataclasses, free pure functions.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass

Q128 = 1 << 128


@dataclass(frozen=True)
class EpochOracleState:
    """Maps to FeeConcentrationEpochStorage in Solidity."""

    current_epoch_id: int  # block.timestamp at epoch start
    epoch_length: int  # seconds
    # Current epoch's accumulator (maps to epochStates[poolId][epochId])
    accumulated_sum: int  # Q128-scaled
    theta_sum: int  # Q128-scaled
    removed_pos_count: int


def init_epoch(epoch_length: int, start_timestamp: int) -> EpochOracleState:
    return EpochOracleState(start_timestamp, epoch_length, 0, 0, 0)


def add_term_epoch(
    state: EpochOracleState,
    block_lifetime: int,
    x_squared_q128: int,
    current_timestamp: int,
) -> EpochOracleState:
    epoch_id = state.current_epoch_id
    acc = state.accumulated_sum
    theta = state.theta_sum
    count = state.removed_pos_count

    if state.epoch_length == 0:
        return state

    if current_timestamp >= epoch_id + state.epoch_length:
        # Epoch expired — new epoch, fresh state
        epoch_id = current_timestamp
        acc = 0
        theta = 0
        count = 0

    lifetime = max(block_lifetime, 1)
    return EpochOracleState(
        current_epoch_id=epoch_id,
        epoch_length=state.epoch_length,
        accumulated_sum=acc + x_squared_q128 // lifetime,
        theta_sum=theta + Q128 // lifetime,
        removed_pos_count=count + 1,
    )


def delta_plus_epoch(state: EpochOracleState) -> int:
    """Compute Δ⁺ for epoch state. Formula must match FeeConcentrationStateMod.deltaPlus().

    See also: research/data/scripts/fci_oracle.py for the canonical Python oracle.
    """
    if state.removed_pos_count == 0:
        return 0
    a_t = math.isqrt(state.accumulated_sum << 128)
    n = state.removed_pos_count
    ratio = state.theta_sum // (n * n)
    at_null = math.isqrt(ratio << 128)
    if a_t <= at_null:
        return 0
    result = a_t - at_null
    return min(result, (1 << 128) - 1)


def delta_plus_epoch_view(state: EpochOracleState, current_timestamp: int) -> int:
    """View function: returns 0 if epoch expired (mirrors epochDeltaPlus view)."""
    if state.current_epoch_id == 0:
        return 0
    if current_timestamp >= state.current_epoch_id + state.epoch_length:
        return 0
    return delta_plus_epoch(state)


if __name__ == "__main__":
    # FFI entry point
    # Usage: python fci_epoch_oracle.py <x_squared_q128> <block_lifetime> <epoch_length> <timestamp>
    x_sq = int(sys.argv[1])
    bl = int(sys.argv[2])
    epoch_len = int(sys.argv[3])
    ts = int(sys.argv[4])

    state = init_epoch(epoch_len, ts)
    state = add_term_epoch(state, bl, x_sq, ts)
    dp = delta_plus_epoch(state)
    print(dp)
```

- [ ] **Step 2: Run Python tests to verify no regressions**

Run: `cd research && PYTHONPATH=. ../uhi8/bin/python -m pytest tests/ -v`
Expected: All existing tests pass.

- [ ] **Step 3: Commit**

```bash
git add research/data/scripts/fci_epoch_oracle.py
git commit -m "feat(004): Python epoch oracle for differential testing"
```

---

### Task 6: Python Tests for Synthetic Exits Module

**Files:**
- Create: `research/tests/backtest/test_synthetic_exits.py`

- [ ] **Step 1: Write tests for the synthetic exit generator (from Phase 2)**

```python
"""Tests for synthetic exit generation calibration."""
from __future__ import annotations

import math

from backtest.oracle_comparison import build_dual_series
from backtest.synthetic_exits import (
    _delta_plus_from_concentration,
    build_from_raw_positions,
    calibrate_concentration,
    generate_synthetic_day,
)
from econometrics.data import DAILY_AT_MAP, DAILY_AT_NULL_MAP, RAW_POSITIONS


def test_uniform_concentration_zero_delta() -> None:
    """Uniform fee shares (c=1/N) should produce Δ⁺=0."""
    bls = (100, 200, 300)
    dp = _delta_plus_from_concentration(1.0 / 3.0, bls)
    assert dp == 0.0


def test_concentration_monotonic() -> None:
    """Higher concentration → higher Δ⁺."""
    bls = (10, 1000, 5000)
    dp_low = _delta_plus_from_concentration(0.3, bls)
    dp_high = _delta_plus_from_concentration(0.9, bls)
    assert dp_high > dp_low


def test_calibrate_zero_target() -> None:
    """Target Δ⁺=0 returns uniform concentration 1/N."""
    bls = (100, 200, 300)
    c = calibrate_concentration(0.0, bls)
    assert abs(c - 1.0 / 3.0) < 1e-10


def test_calibrate_reproduces_target() -> None:
    """Calibrated c reproduces the target Δ⁺ within tolerance."""
    bls = (10, 1000, 5000, 20000)
    target = 0.05
    c = calibrate_concentration(target, bls)
    actual = _delta_plus_from_concentration(c, bls)
    assert abs(actual - target) < 1e-9


def test_generate_synthetic_day_count() -> None:
    """Generates correct number of exits."""
    exits, c = generate_synthetic_day("2025-12-23", 0.1, (10, 100, 1000), 0)
    assert len(exits) == 3
    assert all(e.burn_date == "2025-12-23" for e in exits)


def test_full_stream_reproduces_daily_at_map() -> None:
    """Synthetic stream matches DAILY_AT_MAP Δ⁺ within 1e-8."""
    stream = build_from_raw_positions(RAW_POSITIONS, DAILY_AT_MAP, DAILY_AT_NULL_MAP)
    dual = build_dual_series(list(stream.exits))

    target_dict = {
        d: max(0.0, DAILY_AT_MAP.get(d, 0) - DAILY_AT_NULL_MAP.get(d, 0))
        for d in stream.concentration_params
    }
    synth_dict = dict(zip(dual.days, dual.daily_snapshot_delta_plus))

    for day in stream.concentration_params:
        target = target_dict[day]
        synth = synth_dict.get(day, 0.0)
        assert abs(synth - target) < 1e-8, f"Day {day}: target={target}, synth={synth}"
```

- [ ] **Step 2: Run tests**

Run: `cd research && PYTHONPATH=. ../uhi8/bin/python -m pytest tests/backtest/test_synthetic_exits.py -v`
Expected: All pass.

- [ ] **Step 3: Commit**

```bash
git add research/tests/backtest/test_synthetic_exits.py
git commit -m "test(004): tests for synthetic exit calibration module"
```

---

### Task 7: Epoch Integration Test — Hedged vs Unhedged with Epoch Δ⁺

**Dependency gate:** Task 2 (interface + fan-out + view) must be complete before this task.

**Files:**
- Modify: `test/fci-token-vault/helpers/FciTokenVaultHarness.sol` (add `harness_pokeEpoch`)
- Create: `test/fci-token-vault/integration/HedgedVsUnhedgedEpoch.integration.t.sol`

**Goal:** Run the same JIT crowd-out scenarios from `HedgedVsUnhedged.integration.t.sol` but use `getDeltaPlusEpoch()` instead of `getDeltaPlus()` to drive the vault's HWM. Compare whether the epoch metric gives better signal (cleaner separation between JIT and no-JIT rounds, more responsive to intra-epoch changes).

**Epoch length choice:** Use `EPOCH_LENGTH = 7 days` so that all 3 rounds (`ROUNDS=3`, `ROUND_INTERVAL=1 day`) accumulate within a single epoch. This tests within-epoch accumulation which is the primary use case. A separate test with `EPOCH_LENGTH = 1 day` can verify cross-epoch reset behavior but is not the primary integration test.

**Key differences from cumulative test:**
- Vault's `poke()` reads epoch Δ⁺ (resets each epoch) instead of cumulative Δ⁺ (monotonically growing)
- `setUp()` must call `initializeEpochPool()` on the FCI hook after pool initialization
- Within a 7-day epoch, all 3 rounds accumulate — epoch Δ⁺ grows like cumulative
- After epoch expires (in a hypothetical 4th round), epoch Δ⁺ would reset to 0

- [ ] **Step 1: Add `harness_pokeEpoch()` to FciTokenVaultHarness**

```solidity
// Add these imports to FciTokenVaultHarness.sol:
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {
    applyDecay,
    updateHWM,
    deltaPlusToSqrtPriceX96
} from "@fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol";
// Also add VaultAlreadySettledPoke to the existing FciTokenVaultMod import:
// import { ..., VaultAlreadySettledPoke } from "@fci-token-vault/modules/FciTokenVaultMod.sol";

    /// @dev Same as poke() but reads getDeltaPlusEpoch() instead of getDeltaPlus().
    function harness_pokeEpoch() external {
        FciVaultStorage storage vs = getFciVaultStorage();
        if (vs.settled) revert VaultAlreadySettledPoke();

        uint128 deltaPlus = IFeeConcentrationIndex(address(vs.poolKey.hooks))
            .getDeltaPlusEpoch(vs.poolKey, vs.reactive);

        uint256 dt = block.timestamp - vs.lastHwmTimestamp;
        uint160 decayed = applyDecay(vs.sqrtPriceHWM, dt, vs.halfLifeSeconds);

        if (deltaPlus > 0) {
            uint160 currentSqrtPrice = deltaPlusToSqrtPriceX96(deltaPlus);
            vs.sqrtPriceHWM = updateHWM(decayed, currentSqrtPrice);
        } else {
            vs.sqrtPriceHWM = decayed;
        }
        vs.lastHwmTimestamp = block.timestamp;
    }
```

- [ ] **Step 2: Write the integration test**

The test mirrors `HedgedVsUnhedged.integration.t.sol` structure. Key additions:
- `setUp()` calls `fciHarness.initializeEpochPool(key, EPOCH_LENGTH)` after pool init
- `_runRound()` calls `vault.harness_pokeEpoch()` instead of `vault.harness_poke()`
- Logs both cumulative and epoch Δ⁺ per round for comparison
- Assertions include proportionality: `longPayout > 0 && longPayout < HEDGE_AMOUNT`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test, console} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {PosmTestSetup} from "@uniswap/v4-periphery/test/shared/PosmTestSetup.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {PositionDescriptor} from "@uniswap/v4-periphery/src/PositionDescriptor.sol";

import {FeeConcentrationIndexHarness} from "../../fee-concentration-index/harness/FeeConcentrationIndexHarness.sol";
import {FCITestHelper} from "../../fee-concentration-index/helpers/FCITestHelper.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";

import {Context} from "@foundry-script/types/Context.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";
import {Scenario, mintPosition, burnPosition} from "@foundry-script/types/Scenario.sol";
import {executeSwapWithAmount} from "@foundry-script/simulation/JitGame.sol";
import "@foundry-script/utils/Constants.sol";

import {FciTokenVaultHarness} from "../helpers/FciTokenVaultHarness.sol";
import {LONG, SHORT} from "@fci-token-vault/modules/FciTokenVaultMod.sol";
import {lookbackPayoffX96, applyDecay} from "@fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol";

contract HedgedVsUnhedgedEpochTest is PosmTestSetup, FCITestHelper {
    using PoolIdLibrary for PoolKey;

    Context ctx;
    Scenario scenario;
    FeeConcentrationIndexHarness fciHarness;
    FciTokenVaultHarness vault;
    PoolId poolId;

    uint256 constant CAPITAL = 1e18;
    uint256 constant HEDGE_AMOUNT = 0.1e18;
    uint256 constant TRADE_SIZE = 1e15;
    uint256 constant ROUNDS = 3;
    uint256 constant JIT_CAPITAL = 9e18;
    uint256 constant ROUND_INTERVAL = 1 days;
    uint256 constant EPOCH_LENGTH = 7 days; // All 3 rounds fit in one epoch

    address hedgedPlpAddr;
    uint256 hedgedPlpPk;
    address unhedgedPlpAddr;
    uint256 unhedgedPlpPk;
    address jitLpAddr;
    uint256 jitLpPk;
    address swapperAddr;
    uint256 swapperPk;
    address depositorAddr;
    uint256 depositorPk;

    function setUp() public {
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();
        deployAndApprovePosm(manager);

        fciLP = makeAddr("defaultLP");
        fciSwapper = address(this);
        fciSwapRouter = swapRouter;

        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
                | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
                | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
                | Hooks.BEFORE_SWAP_FLAG
                | Hooks.AFTER_SWAP_FLAG
        );
        bytes memory constructorArgs = abi.encode(address(lpm));
        (address hookAddress, bytes32 salt) = HookMiner.find(
            address(this), flags,
            type(FeeConcentrationIndexHarness).creationCode, constructorArgs
        );
        fciHarness = new FeeConcentrationIndexHarness{salt: salt}(lpm);
        require(address(fciHarness) == hookAddress, "hook address mismatch");

        (key, poolId) = initPool(
            currency0, currency1,
            IHooks(address(fciHarness)),
            3000, SQRT_PRICE_1_1
        );

        // Initialize epoch metric for this pool
        fciHarness.initializeEpochPool(key, EPOCH_LENGTH);

        ctx.vm = vm;
        ctx.v4Pool = key;
        ctx.v4PositionManager = address(lpm);
        ctx.v4SwapRouter = address(swapRouter);
        ctx.chainId = block.chainid;

        vault = new FciTokenVaultHarness();
        uint160 strikePrice = SqrtPriceLibrary.fractionToSqrtPriceX96(30, 70);
        vault.harness_initVault(
            strikePrice, 14 days, block.timestamp + 5 days,
            key, false, Currency.unwrap(currency1)
        );

        Vm.Wallet memory w;
        w = vm.createWallet("hedgedPlp");
        hedgedPlpAddr = w.addr; hedgedPlpPk = w.privateKey;
        w = vm.createWallet("unhedgedPlp");
        unhedgedPlpAddr = w.addr; unhedgedPlpPk = w.privateKey;
        w = vm.createWallet("jitLp");
        jitLpAddr = w.addr; jitLpPk = w.privateKey;
        w = vm.createWallet("swapper");
        swapperAddr = w.addr; swapperPk = w.privateKey;
        w = vm.createWallet("depositor");
        depositorAddr = w.addr; depositorPk = w.privateKey;

        _setupLP(hedgedPlpAddr);
        _setupLP(unhedgedPlpAddr);
        _setupLP(jitLpAddr);
        _setupSwapper(swapperAddr);
        seedBalance(depositorAddr);
    }

    // ── Helpers (same as cumulative test) ──

    function _setupLP(address account) internal {
        seedBalance(account);
        approvePosmFor(account);
    }

    function _setupSwapper(address account) internal {
        seedBalance(account);
        vm.startPrank(account);
        IERC20(Currency.unwrap(currency0)).approve(address(swapRouter), type(uint256).max);
        IERC20(Currency.unwrap(currency1)).approve(address(swapRouter), type(uint256).max);
        vm.stopPrank();
    }

    function _depositToVault(address plpAddr, uint256 amount) internal {
        vm.startPrank(plpAddr);
        IERC20(Currency.unwrap(currency1)).approve(address(vault), amount);
        vault.harness_deposit(plpAddr, amount);
        vm.stopPrank();
    }

    uint256 constant JIT_ENTRY_OFFSET = 49;
    uint256 constant PASSIVE_EXIT_OFFSET = 50;

    function _runRound(
        bool jitEnters, uint256 jitCapital, uint256 hedgedLiq, uint256 unhedgedLiq
    ) internal returns (uint256 hedgedTokenId, uint256 unhedgedTokenId) {
        hedgedTokenId = mintPosition(ctx, scenario, Protocol.UniswapV4, hedgedPlpPk, hedgedLiq);
        unhedgedTokenId = mintPosition(ctx, scenario, Protocol.UniswapV4, unhedgedPlpPk, unhedgedLiq);

        vm.roll(block.number + JIT_ENTRY_OFFSET);

        uint256 jitTokenId;
        if (jitEnters) {
            jitTokenId = mintPosition(ctx, scenario, Protocol.UniswapV4, jitLpPk, jitCapital);
        }

        executeSwapWithAmount(ctx, Protocol.UniswapV4, swapperPk, ZERO_FOR_ONE, int256(TRADE_SIZE));

        vm.roll(block.number + 1);
        if (jitEnters) {
            burnPosition(ctx, Protocol.UniswapV4, jitLpPk, jitTokenId, jitCapital);
        }

        vm.roll(block.number + PASSIVE_EXIT_OFFSET);
        burnPosition(ctx, Protocol.UniswapV4, hedgedPlpPk, hedgedTokenId, hedgedLiq);
        burnPosition(ctx, Protocol.UniswapV4, unhedgedPlpPk, unhedgedTokenId, unhedgedLiq);

        // Log both metrics for comparison
        uint128 cumDp = IFeeConcentrationIndex(address(fciHarness)).getDeltaPlus(key, false);
        uint128 epochDp = IFeeConcentrationIndex(address(fciHarness)).getDeltaPlusEpoch(key, false);
        console.log("  Cumulative delta+:", uint256(cumDp));
        console.log("  Epoch delta+:     ", uint256(epochDp));

        vm.warp(block.timestamp + ROUND_INTERVAL);
        vault.harness_pokeEpoch(); // Uses epoch Δ⁺
    }

    function _settleVault(FciTokenVaultHarness v, uint256 depositAmount)
        internal
        returns (uint256 longPayout, uint256 shortPayout)
    {
        (,,, uint256 expiry,,,,) = v.harness_getVaultStorage();
        vm.warp(expiry + 1);
        v.harness_settle();
        (,,,,,,, uint256 longPayoutPerToken) = v.harness_getVaultStorage();
        longPayout = (depositAmount * longPayoutPerToken) / SqrtPriceLibrary.Q96;
        shortPayout = depositAmount - longPayout;
        vm.prank(depositorAddr);
        v.harness_redeem(depositorAddr, depositAmount);
    }

    function _snapshotBal(address who) internal view returns (uint256 a, uint256 b) {
        a = IERC20(Currency.unwrap(currency0)).balanceOf(who);
        b = IERC20(Currency.unwrap(currency1)).balanceOf(who);
    }

    // ── Scenario 1: Equilibrium ──

    function test_epoch_equilibrium_no_jit() public {
        _depositToVault(depositorAddr, HEDGE_AMOUNT);
        (uint256 hA0, uint256 hB0) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA0, uint256 uB0) = _snapshotBal(unhedgedPlpAddr);

        console.log("=== EPOCH: EQUILIBRIUM (no JIT) ===");
        for (uint256 i; i < ROUNDS; ++i) {
            console.log("Round", i + 1);
            _runRound(false, 0, CAPITAL, CAPITAL);
        }

        (uint256 hA1, uint256 hB1) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA1, uint256 uB1) = _snapshotBal(unhedgedPlpAddr);
        uint256 hedgedPayout = (hA1 + hB1) - (hA0 + hB0);
        uint256 unhedgedPayout = (uA1 + uB1) - (uA0 + uB0);

        (uint256 longPayout, uint256 shortPayout) = _settleVault(vault, HEDGE_AMOUNT);

        assertEq(longPayout, 0, "LONG should be 0 in equilibrium");
        assertEq(longPayout + shortPayout, HEDGE_AMOUNT, "conservation");

        console.log("LONG payout:", longPayout);
    }

    // ── Scenario 2: JIT crowd-out ──

    function test_epoch_jit_crowdout_hedge_compensates() public {
        _depositToVault(depositorAddr, HEDGE_AMOUNT);
        (uint256 hA0, uint256 hB0) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA0, uint256 uB0) = _snapshotBal(unhedgedPlpAddr);

        console.log("=== EPOCH: JIT CROWD-OUT ===");
        for (uint256 i; i < ROUNDS; ++i) {
            console.log("Round", i + 1);
            _runRound(true, JIT_CAPITAL, CAPITAL, CAPITAL);
        }

        (uint256 hA1, uint256 hB1) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA1, uint256 uB1) = _snapshotBal(unhedgedPlpAddr);
        uint256 hedgedPayout = (hA1 + hB1) - (hA0 + hB0);
        uint256 unhedgedPayout = (uA1 + uB1) - (uA0 + uB0);

        (uint256 longPayout, uint256 shortPayout) = _settleVault(vault, HEDGE_AMOUNT);

        uint256 hedgedWelfare = hedgedPayout + longPayout;
        uint256 unhedgedWelfare = unhedgedPayout;

        // Property 1: Hedge compensates
        assertGt(hedgedWelfare, unhedgedWelfare, "hedged should earn more under JIT");
        assertGt(longPayout, 0, "LONG should be positive under JIT");

        // Property: Proportionality — payout is between 0 and full deposit (not binary)
        assertLt(longPayout, HEDGE_AMOUNT, "payout should be proportional, not full deposit");

        // Property: Conservation
        assertEq(longPayout + shortPayout, HEDGE_AMOUNT, "conservation");

        console.log("LONG payout:", longPayout);
        console.log("Hedged welfare:", hedgedWelfare);
        console.log("Unhedged welfare:", unhedgedWelfare);
        console.log("Net hedge benefit:", hedgedWelfare - unhedgedWelfare);
    }

    // ── Scenario 3: Below-strike ──

    function test_epoch_below_strike_no_false_trigger() public {
        FciTokenVaultHarness highStrikeVault = new FciTokenVaultHarness();
        uint160 highStrike = SqrtPriceLibrary.fractionToSqrtPriceX96(99, 1);
        highStrikeVault.harness_initVault(
            highStrike, 14 days, block.timestamp + 5 days,
            key, false, Currency.unwrap(currency1)
        );
        vm.startPrank(depositorAddr);
        IERC20(Currency.unwrap(currency1)).approve(address(highStrikeVault), HEDGE_AMOUNT);
        highStrikeVault.harness_deposit(depositorAddr, HEDGE_AMOUNT);
        vm.stopPrank();

        uint256 smallJitCapital = CAPITAL / 10;
        (uint256 hA0, uint256 hB0) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA0, uint256 uB0) = _snapshotBal(unhedgedPlpAddr);

        console.log("=== EPOCH: BELOW-STRIKE JIT ===");
        for (uint256 i; i < ROUNDS; ++i) {
            console.log("Round", i + 1);
            uint256 hTid = mintPosition(ctx, scenario, Protocol.UniswapV4, hedgedPlpPk, CAPITAL);
            uint256 uTid = mintPosition(ctx, scenario, Protocol.UniswapV4, unhedgedPlpPk, CAPITAL);
            vm.roll(block.number + JIT_ENTRY_OFFSET);
            uint256 jTid = mintPosition(ctx, scenario, Protocol.UniswapV4, jitLpPk, smallJitCapital);
            executeSwapWithAmount(ctx, Protocol.UniswapV4, swapperPk, ZERO_FOR_ONE, int256(TRADE_SIZE));
            vm.roll(block.number + 1);
            burnPosition(ctx, Protocol.UniswapV4, jitLpPk, jTid, smallJitCapital);
            vm.roll(block.number + PASSIVE_EXIT_OFFSET);
            burnPosition(ctx, Protocol.UniswapV4, hedgedPlpPk, hTid, CAPITAL);
            burnPosition(ctx, Protocol.UniswapV4, unhedgedPlpPk, uTid, CAPITAL);

            uint128 epochDp = IFeeConcentrationIndex(address(fciHarness)).getDeltaPlusEpoch(key, false);
            console.log("  Epoch delta+:", uint256(epochDp));

            vm.warp(block.timestamp + ROUND_INTERVAL);
            highStrikeVault.harness_pokeEpoch();
        }

        (uint256 hA1, uint256 hB1) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA1, uint256 uB1) = _snapshotBal(unhedgedPlpAddr);
        uint256 hedgedPayout = (hA1 + hB1) - (hA0 + hB0);
        uint256 unhedgedPayout = (uA1 + uB1) - (uA0 + uB0);

        (uint256 longPayout, uint256 shortPayout) = _settleVault(highStrikeVault, HEDGE_AMOUNT);

        assertEq(longPayout, 0, "LONG should be 0 when below strike");
        assertEq(longPayout + shortPayout, HEDGE_AMOUNT, "conservation");

        console.log("LONG payout:", longPayout);
    }
}
```

- [ ] **Step 3: Run integration test**

Run: `forge test --match-path "test/fci-token-vault/integration/HedgedVsUnhedgedEpoch*" -vv`
Expected: All 3 scenarios pass. Epoch Δ⁺ values logged alongside cumulative for comparison.

- [ ] **Step 4: Run full test suite for regressions**

Run: `forge test -v`
Expected: All existing + new tests pass.

- [ ] **Step 5: Commit**

```bash
git add test/fci-token-vault/helpers/FciTokenVaultHarness.sol \
        test/fci-token-vault/integration/HedgedVsUnhedgedEpoch.integration.t.sol
git commit -m "test(004): epoch-driven hedged vs unhedged integration test"
```

---

### Task 8: Final Regression Check

- [ ] **Step 1: Full Solidity test suite**

Run: `forge test -vv`
Expected: All tests pass. Zero regressions.

- [ ] **Step 2: Full Python test suite**

Run: `cd research && PYTHONPATH=. ../uhi8/bin/python -m pytest tests/ -v`
Expected: All tests pass (existing + new synthetic_exits tests).

- [ ] **Step 3: Verify build is clean**

Run: `forge build`
Expected: No errors (except existing lint warnings).

---

## Chunk 3: Reactive Dispatch + Window (after epoch passes integration tests)

### Task 9: Epoch Reactive Dispatch

**Gate:** Only proceed after Task 7 (epoch integration test) passes all scenarios.

**Files:**
- Create: `src/fee-concentration-index/modules/FeeConcentrationEpochReactiveExtMod.sol`
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol` (swap no-arg for hookData-aware overload)

Reactive dispatch wrapper that selects `epochFciStorage()` vs `reactiveEpochFciStorage()` based on `hookData`. Follows the pattern of `FeeConcentrationIndexStorageMultiProtocolReactiveExtMod.sol`.

- [ ] **Step 1: Write the reactive dispatch file**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId} from "v4-core/src/types/PoolId.sol";
import {BlockCount} from "typed-uniswap-v4/fee-concentration-index/types/BlockCountMod.sol";
import {isUniswapV3Reactive} from "../../reactive-integration/uniswapV3/types/HookDataFlagsMod.sol";
import {
    FeeConcentrationEpochStorage,
    epochFciStorage, reactiveEpochFciStorage,
    addEpochTerm as _addEpochTerm,
    epochDeltaPlus as _epochDeltaPlus
} from "./FeeConcentrationEpochStorageMod.sol";

function addEpochTerm(bytes calldata hookData, PoolId poolId, BlockCount blockLifetime, uint256 xSquaredQ128) {
    FeeConcentrationEpochStorage storage $ = isUniswapV3Reactive(hookData)
        ? reactiveEpochFciStorage()
        : epochFciStorage();
    _addEpochTerm($, poolId, blockLifetime, xSquaredQ128);
}

function epochDeltaPlus(bytes calldata hookData, PoolId poolId) view returns (uint128) {
    FeeConcentrationEpochStorage storage $ = isUniswapV3Reactive(hookData)
        ? reactiveEpochFciStorage()
        : epochFciStorage();
    return _epochDeltaPlus($, poolId);
}
```

- [ ] **Step 2: Update FeeConcentrationIndex.sol fan-out to use hookData-aware overload**

Change import from `FeeConcentrationEpochStorageMod.sol` to `FeeConcentrationEpochReactiveExtMod.sol`. Change fan-out call from `addEpochTerm(poolId, ...)` to `addEpochTerm(hookData, poolId, ...)`. Update view function to use reactive routing.

- [ ] **Step 3: Verify compilation + no regressions**
- [ ] **Step 4: Commit**

---

### Task 10+: Window Metric (Deferred)

Window metric requires per-position contribution pairs `(accContrib, thetaContrib)` in a ring buffer — fundamentally new data not available from the existing `FeeConcentrationState` accumulator. Deferred to a future task after epoch is validated end-to-end.

Tasks when resumed:
- Window storage module with ring buffer
- Window reactive dispatch
- Interface + fan-out for window
- Window unit + fuzz tests
- Python window oracle
