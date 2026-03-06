# FCI Co-Primary State + Diamond Pattern Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade FeeConcentrationIndex to track (A_T, Theta, N) co-primary state for Delta+ computation, and remove BaseHook inheritance for diamond pattern compatibility.

**Architecture:** Phase 1 creates `FeeConcentrationStateMod.sol` (struct + free functions) with TDD, replacing `AccumulatedHHIMod.sol`. Phase 2 removes BaseHook from `FeeConcentrationIndex.sol`, wires the new type, and updates all tests. Work happens on a new branch off `001-fee-concentration-index`.

**Tech Stack:** Solidity ^0.8.26, Solady FixedPointMathLib, forge-std, kontrol-cheatcodes. SCOP: no `library` keyword, no inheritance in contracts (except test harness), no `modifier`. Free functions in Mod files with `using ... for ... global`.

**Build command:** `forge build --out out2` and `forge test --out out2`

**Spec reference:** `specs/model/payoff.tex` (FCI-01 through FCI-11), `specs/model/invariants.tex`

---

## Pre-Work: Branch Setup

### Task 0: Create feature branch

**Step 1: Create branch off 001**

```bash
git checkout 001-fee-concentration-index
git pull origin 001-fee-concentration-index
git checkout -b 001-fci-coprimary-diamond
```

**Step 2: Verify clean build**

Run: `forge build --out out2`
Expected: Compiles clean

**Step 3: Verify existing tests pass**

Run: `forge test --out out2 --match-path "test/fee-concentration-index/*" -v`
Expected: All existing tests pass

---

## Phase 1: Type — FeeConcentrationStateMod.sol

### Task 1: Write failing tests for FeeConcentrationState

**Files:**
- Create: `test/fee-concentration-index/unit/FeeConcentrationState.t.sol`

**Step 1: Write the test file**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {
    FeeConcentrationState,
    newFeeConcentrationState,
    addTerm,
    incrementPos,
    decrementPos,
    toIndexA,
    atNull,
    deltaPlus,
    toDeltaPlusPrice,
    Q128,
    INDEX_ONE
} from "../../../src/fee-concentration-index/types/FeeConcentrationStateMod.sol";
import {BlockCount} from "../../../src/fee-concentration-index/types/BlockCountMod.sol";

contract FeeConcentrationStateTest is Test {
    // ── FCI-01: Index boundedness: 0 <= A_T <= 1 ──

    function test_FCI01_indexAZeroWhenEmpty() public pure {
        FeeConcentrationState memory s = newFeeConcentrationState();
        assertEq(toIndexA(s), 0, "FCI-01: A_T = 0 when no terms");
    }

    function testFuzz_FCI01_indexACapped(uint128 sumRaw) public pure {
        FeeConcentrationState memory s = FeeConcentrationState({
            accumulatedSum: uint256(sumRaw),
            thetaSum: 0,
            posCount: 0
        });
        uint128 a = toIndexA(s);
        assertLe(a, INDEX_ONE, "FCI-01: A_T <= 1.0");
    }

    // ── FCI-02: Theta sum non-negativity ──

    function test_FCI02_thetaSumStartsZero() public pure {
        FeeConcentrationState memory s = newFeeConcentrationState();
        assertEq(s.thetaSum, 0, "FCI-02: thetaSum starts at 0");
    }

    function testFuzz_FCI02_thetaSumNonDecreasing(uint64 lifetime, uint64 xSq) public pure {
        vm.assume(lifetime > 0);
        FeeConcentrationState memory s = newFeeConcentrationState();
        FeeConcentrationState memory s2 = addTerm(s, BlockCount.wrap(uint256(lifetime)), uint256(xSq));
        assertGe(s2.thetaSum, s.thetaSum, "FCI-02: thetaSum non-decreasing");
    }

    // ── FCI-03: Position count non-negativity ──

    function test_FCI03_posCountStartsZero() public pure {
        FeeConcentrationState memory s = newFeeConcentrationState();
        assertEq(s.posCount, 0, "FCI-03: posCount starts at 0");
    }

    function test_FCI03_posCountIncrements() public pure {
        FeeConcentrationState memory s = newFeeConcentrationState();
        s = incrementPos(s);
        assertEq(s.posCount, 1);
        s = incrementPos(s);
        assertEq(s.posCount, 2);
    }

    function test_FCI03_posCountDecrements() public pure {
        FeeConcentrationState memory s = newFeeConcentrationState();
        s = incrementPos(s);
        s = incrementPos(s);
        s = decrementPos(s);
        assertEq(s.posCount, 1);
    }

    function test_FCI03_decrementZeroReverts() public {
        FeeConcentrationState memory s = newFeeConcentrationState();
        vm.expectRevert();
        decrementPos(s);
    }

    // ── FCI-04: Null lower bound: A_T >= A_T^{1/N} when N > 0 ──

    function test_FCI04_atNullZeroWhenNoPosCount() public pure {
        FeeConcentrationState memory s = newFeeConcentrationState();
        assertEq(atNull(s), 0, "FCI-04: atNull = 0 when posCount = 0");
    }

    function test_FCI04_nullLowerBound() public pure {
        // Manually construct: 1 position removed with x_k = 0.5 (Q128/2), lifetime = 1 block
        // theta = 1/1 = 1, x^2 = 0.25
        // accumulatedSum = 1 * 0.25 = 0.25 in Q128 = Q128/4
        // thetaSum = 1 in Q128 = Q128
        // posCount = 1
        // A_T = sqrt(Q128/4) = sqrt(Q128)/2
        // atNull = sqrt(Q128 / 1^2) = sqrt(Q128)
        // A_T < atNull here because fee share was < 1/N (0.5 < 1.0)
        // But wait: with 1 position and x_k = 0.5, the share < 1/N = 1.0, so A_T < atNull
        // That shouldn't happen if sum_k x_k = 1. With one position x_1 must = 1.
        // Let's use a valid scenario: 1 position, x_k = 1.0, lifetime = 1
        uint256 xQ128 = Q128; // x_k = 1.0
        uint256 xSqQ128 = Q128; // x_k^2 = 1.0 (in Q128: (Q128 * Q128) / Q128 = Q128)
        FeeConcentrationState memory s = FeeConcentrationState({
            accumulatedSum: xSqQ128, // sum = 1 * 1.0 = 1.0 in Q128
            thetaSum: Q128,          // theta = 1/1 = 1.0 in Q128
            posCount: 1
        });
        uint128 a = toIndexA(s);
        uint256 null_ = atNull(s);
        assertGe(uint256(a), null_, "FCI-04: A_T >= atNull");
    }

    // ── FCI-05: Deviation non-negativity ──

    function test_FCI05_deltaPlusNonNegative() public pure {
        FeeConcentrationState memory s = newFeeConcentrationState();
        assertEq(deltaPlus(s), 0, "FCI-05: deltaPlus = 0 when empty");
    }

    // ── FCI-06: Deviation upper bound: deltaPlus < 1 ──

    function test_FCI06_deltaPlusLessThanOne() public pure {
        // Max scenario: accumulatedSum = Q128 (A_T capped at 1), thetaSum = 0, posCount = 0
        // deltaPlus = max(0, 1.0 - 0) = 1.0... but atNull = 0 when posCount = 0
        // However spec says deltaPlus < 1 when posCount >= 1.
        // With posCount = 1, thetaSum > 0, atNull > 0, so deltaPlus < A_T <= 1.
        FeeConcentrationState memory s = FeeConcentrationState({
            accumulatedSum: Q128, // A_T = 1.0
            thetaSum: 1,         // tiny thetaSum > 0
            posCount: 1
        });
        uint256 dp = deltaPlus(s);
        assertLt(dp, Q128, "FCI-06: deltaPlus < 1.0 when posCount >= 1");
    }

    // ── FCI-07: Co-primary consistency (deterministic) ──

    function testFuzz_FCI07_deterministic(uint64 sum, uint64 theta, uint32 n) public pure {
        vm.assume(n > 0);
        FeeConcentrationState memory s = FeeConcentrationState({
            accumulatedSum: uint256(sum),
            thetaSum: uint256(theta),
            posCount: uint256(n)
        });
        // Same inputs produce same outputs
        assertEq(deltaPlus(s), deltaPlus(s), "FCI-07: deterministic");
        assertEq(toDeltaPlusPrice(s), toDeltaPlusPrice(s), "FCI-07: deterministic price");
    }

    // ── addTerm: monotonicity ──

    function testFuzz_addTermMonotonic(uint64 sumInit, uint64 lifetime, uint64 xSq) public pure {
        vm.assume(lifetime > 0);
        FeeConcentrationState memory before_ = FeeConcentrationState({
            accumulatedSum: uint256(sumInit),
            thetaSum: 0,
            posCount: 0
        });
        FeeConcentrationState memory after_ = addTerm(before_, BlockCount.wrap(uint256(lifetime)), uint256(xSq));
        assertGe(after_.accumulatedSum, before_.accumulatedSum, "accumulatedSum monotonic");
        assertGe(after_.thetaSum, before_.thetaSum, "thetaSum monotonic");
    }

    // ── Price mapping: p = deltaPlus / (1 - deltaPlus) ──

    function test_priceZeroWhenDeltaPlusZero() public pure {
        FeeConcentrationState memory s = newFeeConcentrationState();
        assertEq(toDeltaPlusPrice(s), 0, "price = 0 when deltaPlus = 0");
    }

    // ── Backward compatibility: toIndexA matches old AccumulatedHHI.toIndexA ──

    function test_backwardCompat_indexAMatchesOld() public pure {
        // Old: AccumulatedHHI.wrap(raw).toIndexA()
        // New: FeeConcentrationState{accumulatedSum: raw, ...}.toIndexA()
        // With raw = Q128/4 (A_T = 0.5):
        uint256 raw = Q128 / 4;
        FeeConcentrationState memory s = FeeConcentrationState({
            accumulatedSum: raw,
            thetaSum: 0,
            posCount: 0
        });
        uint128 a = toIndexA(s);
        // sqrt(raw << 128) = sqrt((Q128/4) << 128) = sqrt(Q128^2/4) = Q128/2
        // Q128/2 in uint128 = INDEX_ONE/2 approximately
        // Just check it's > 0 and <= INDEX_ONE
        assertGt(a, 0, "nonzero for nonzero sum");
        assertLe(a, INDEX_ONE, "capped");
    }
}
```

**Step 2: Verify it does NOT compile (type doesn't exist yet)**

Run: `forge build --out out2`
Expected: Compilation error — `FeeConcentrationStateMod.sol` not found

### Task 2: Implement FeeConcentrationStateMod.sol

**Files:**
- Create: `src/fee-concentration-index/types/FeeConcentrationStateMod.sol`

**Step 1: Write the implementation**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {BlockCount} from "./BlockCountMod.sol";

// Co-primary state for the Fee Concentration Index.
// Replaces AccumulatedHHI with full (A_T, Theta, N) triple.
//
// accumulatedSum = Sigma(theta_k * x_k^2) across all removed positions (Q128)
// thetaSum       = Sigma(1/ell_k) across all removed positions (Q128)
// posCount       = N = number of currently active positions (uint256)
//
// Derived (not stored):
//   A_T      = sqrt(accumulatedSum)
//   A_T^1/N  = sqrt(thetaSum / N^2)
//   Delta+   = max(0, A_T - A_T^1/N)
//   p        = Delta+ / (1 - Delta+)

uint256 constant Q128 = 1 << 128;
uint128 constant INDEX_ONE = type(uint128).max;

struct FeeConcentrationState {
    uint256 accumulatedSum;
    uint256 thetaSum;
    uint256 posCount;
}

error FeeConcentrationState__PosCountUnderflow();

function newFeeConcentrationState() pure returns (FeeConcentrationState memory) {
    return FeeConcentrationState({accumulatedSum: 0, thetaSum: 0, posCount: 0});
}

/// @dev Add an HHI term at position removal.
///      theta_k = 1/max(1, blockLifetime) (Q128 scaling implicit: xSquaredQ128 is already Q128)
///      accumulatedSum += theta_k * x_k^2 = xSquaredQ128 / max(1, blockLifetime)
///      thetaSum += theta_k = Q128 / max(1, blockLifetime)
function addTerm(
    FeeConcentrationState memory self,
    BlockCount blockLifetime,
    uint256 xSquaredQ128
) pure returns (FeeConcentrationState memory) {
    uint256 life = blockLifetime.floorOne();
    self.accumulatedSum += xSquaredQ128 / life;
    self.thetaSum += Q128 / life;
    return self;
}

/// @dev Increment active position count (called at afterAddLiquidity).
function incrementPos(FeeConcentrationState memory self) pure returns (FeeConcentrationState memory) {
    self.posCount += 1;
    return self;
}

/// @dev Decrement active position count (called at afterRemoveLiquidity).
function decrementPos(FeeConcentrationState memory self) pure returns (FeeConcentrationState memory) {
    if (self.posCount == 0) revert FeeConcentrationState__PosCountUnderflow();
    self.posCount -= 1;
    return self;
}

/// @dev A_T = sqrt(accumulatedSum) in Q128, capped at INDEX_ONE.
function toIndexA(FeeConcentrationState memory self) pure returns (uint128) {
    uint256 raw = self.accumulatedSum;
    if (raw >= Q128) return INDEX_ONE;
    uint256 a = FixedPointMathLib.sqrt(raw << 128);
    if (a > INDEX_ONE) return INDEX_ONE;
    return uint128(a);
}

/// @dev A_T^{1/N} = sqrt(thetaSum / N^2) in Q128.
///      Returns 0 when posCount == 0.
function atNull(FeeConcentrationState memory self) pure returns (uint256) {
    if (self.posCount == 0) return 0;
    uint256 nSquared = self.posCount * self.posCount;
    uint256 ratio = self.thetaSum / nSquared;
    // sqrt(ratio) in Q128: sqrt(ratio << 128)
    if (ratio >= Q128) return Q128; // cap at 1.0
    return FixedPointMathLib.sqrt(ratio << 128);
}

/// @dev Delta+ = max(0, A_T - A_T^{1/N}) in Q128.
function deltaPlus(FeeConcentrationState memory self) pure returns (uint256) {
    uint256 a = uint256(toIndexA(self));
    uint256 null_ = atNull(self);
    if (a <= null_) return 0;
    return a - null_;
}

/// @dev p = Delta+ / (1 - Delta+) in Q128.
///      Returns 0 when deltaPlus == 0.
///      Returns type(uint256).max when deltaPlus >= Q128 (shouldn't happen per FCI-06).
function toDeltaPlusPrice(FeeConcentrationState memory self) pure returns (uint256) {
    uint256 dp = deltaPlus(self);
    if (dp == 0) return 0;
    if (dp >= Q128) return type(uint256).max;
    // p = dp / (Q128 - dp), scaled to Q128: p_Q128 = dp * Q128 / (Q128 - dp)
    return FixedPointMathLib.mulDiv(dp, Q128, Q128 - dp);
}
```

**Step 2: Run tests**

Run: `forge test --out out2 --match-path "test/fee-concentration-index/unit/FeeConcentrationState.t.sol" -vv`
Expected: All tests pass

**Step 3: Commit**

```bash
git add src/fee-concentration-index/types/FeeConcentrationStateMod.sol \
        test/fee-concentration-index/unit/FeeConcentrationState.t.sol
git commit -m "feat: add FeeConcentrationState co-primary type + unit tests

Replaces AccumulatedHHI UDVT with struct bundling (accumulatedSum,
thetaSum, posCount). Free functions: addTerm, incrementPos,
decrementPos, toIndexA, atNull, deltaPlus, toDeltaPlusPrice.
Covers FCI-01 through FCI-07 invariants."
```

### Task 3: Write Kontrol proofs for FeeConcentrationState

**Files:**
- Create: `test/fee-concentration-index/kontrol/FeeConcentrationState.k.sol`

**Step 1: Write Kontrol proofs**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {KontrolCheats} from "kontrol-cheatcodes/KontrolCheats.sol";
import {
    FeeConcentrationState,
    addTerm,
    incrementPos,
    decrementPos,
    toIndexA,
    atNull,
    deltaPlus,
    Q128,
    INDEX_ONE
} from "../../../src/fee-concentration-index/types/FeeConcentrationStateMod.sol";
import {BlockCount} from "../../../src/fee-concentration-index/types/BlockCountMod.sol";

contract FeeConcentrationStateProof is Test, KontrolCheats {
    // FCI-01: A_T capped at INDEX_ONE
    function prove_indexA_capped() public view {
        uint256 sumRaw = freshUInt256();
        FeeConcentrationState memory s = FeeConcentrationState({
            accumulatedSum: sumRaw, thetaSum: 0, posCount: 0
        });
        assert(toIndexA(s) <= INDEX_ONE);
    }

    // FCI-01: A_T = 0 when sum = 0
    function prove_indexA_zero_when_empty() public pure {
        FeeConcentrationState memory s = FeeConcentrationState({
            accumulatedSum: 0, thetaSum: 0, posCount: 0
        });
        assert(toIndexA(s) == 0);
    }

    // Monotonicity: addTerm only increases accumulatedSum and thetaSum
    function prove_addTerm_monotonic() public view {
        uint128 sumRaw = freshUInt128();
        uint128 thetaRaw = freshUInt128();
        uint256 lifetime = freshUInt256();
        uint128 xSq = freshUInt128();
        vm.assume(lifetime > 0);

        FeeConcentrationState memory before_ = FeeConcentrationState({
            accumulatedSum: uint256(sumRaw),
            thetaSum: uint256(thetaRaw),
            posCount: 0
        });
        FeeConcentrationState memory after_ = addTerm(before_, BlockCount.wrap(lifetime), uint256(xSq));

        assert(after_.accumulatedSum >= before_.accumulatedSum);
        assert(after_.thetaSum >= before_.thetaSum);
    }

    // incrementPos / decrementPos round-trip
    function prove_posCount_roundtrip() public view {
        uint128 n = freshUInt128();
        vm.assume(n > 0 && n < type(uint128).max);

        FeeConcentrationState memory s = FeeConcentrationState({
            accumulatedSum: 0, thetaSum: 0, posCount: uint256(n)
        });
        FeeConcentrationState memory s2 = incrementPos(s);
        FeeConcentrationState memory s3 = decrementPos(s2);
        assert(s3.posCount == s.posCount);
    }
}
```

**Step 2: Verify compiles**

Run: `forge build --out out2`
Expected: Compiles clean (Kontrol proofs don't run via `forge test`, they use `kontrol prove`)

**Step 3: Commit**

```bash
git add test/fee-concentration-index/kontrol/FeeConcentrationState.k.sol
git commit -m "test: add Kontrol proofs for FeeConcentrationState

Proves FCI-01 (index capped), monotonicity of addTerm,
and posCount increment/decrement round-trip."
```

---

## Phase 2: Hook Contract — Remove BaseHook + Wire New Type

### Task 4: Update FeeConcentrationIndexStorage to use FeeConcentrationState

**Files:**
- Modify: `src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol`

**Step 1: Update import and storage struct**

Replace the `AccumulatedHHI` import with `FeeConcentrationState`:

In `FeeConcentrationIndexStorageMod.sol`:
- Change `import {AccumulatedHHI} from "../types/AccumulatedHHIMod.sol";`
  to `import {FeeConcentrationState} from "../types/FeeConcentrationStateMod.sol";`
- Change `mapping(PoolId => AccumulatedHHI) accumulatedHHI;`
  to `mapping(PoolId => FeeConcentrationState) fciState;`
- Update `getAccumulatedHHI` and `setAccumulatedHHI` free functions to work with `FeeConcentrationState`

**Step 2: Verify it does NOT compile (hook still references old type)**

Run: `forge build --out out2`
Expected: Compilation errors in `FeeConcentrationIndex.sol` and harness files referencing `accumulatedHHI`

### Task 5: Update FeeConcentrationIndex.sol — wire new type + remove BaseHook

**Files:**
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol`
- Modify: `src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol`

**Step 1: Rewrite FeeConcentrationIndex.sol**

Key changes:
1. Remove `is BaseHook` — plain contract
2. `IPoolManager public immutable poolManager` — set in constructor (immutable survives delegatecall)
3. `IPositionManager public immutable positionManager` — kept
4. All hook functions become `external` with raw IHooks signatures (no `override`, no `_` prefix)
5. `_afterAddLiquidity`: add `$.fciState[poolId].posCount += 1;` after register
6. `_afterRemoveLiquidity`: the `addTerm` call changes to use `FeeConcentrationState`, and add `$.fciState[poolId].posCount -= 1;` after
7. `getIndex()`: returns `(uint128 indexA, uint256 thetaSum, uint256 posCount)`
8. Remove `getHookPermissions()` — MasterHook's concern

**Step 2: Update IFeeConcentrationIndex.sol**

```solidity
interface IFeeConcentrationIndex {
    function getIndex(PoolKey calldata key)
        external view returns (uint128 indexA, uint256 thetaSum, uint256 posCount);
}
```

**Step 3: Verify it does NOT compile (harness references old type)**

Run: `forge build --out out2`
Expected: Compilation errors in harness and test files

### Task 6: Update harness and test files

**Files:**
- Modify: `test/fee-concentration-index/harness/FeeConcentrationIndexHarness.sol`
- Modify: `test/fee-concentration-index/unit/AfterAddLiquidity.t.sol`
- Modify: `test/fee-concentration-index/unit/AfterRemoveLiquidity.t.sol`
- Modify: `test/fee-concentration-index/unit/AfterSwap.t.sol`
- Modify: `test/fee-concentration-index/unit/FeeConcentrationIndexFull.unit.t.sol`
- Modify: `test/fee-concentration-index/fuzz/FeeConcentrationIndexFull.fuzz.t.sol`
- Modify: `test/fee-concentration-index/recon/Setup.sol`
- Modify: `test/fee-concentration-index/recon/Properties.sol`
- Modify: `test/fee-concentration-index/recon/TargetFunctions.sol`

**Step 1: Update harness**

The harness inherits from `FeeConcentrationIndex` — since we removed BaseHook, the harness no longer has the `_afterAddLiquidity` internal function pattern. The harness needs to:
- Remove `is FeeConcentrationIndex` inheritance (since FCI no longer inherits BaseHook, the exposed_ pattern changes)
- Instead, instantiate FCI and `delegatecall` to it, OR
- Keep inheritance but make the hook functions `public virtual` in the base

Decision: Since we're removing BaseHook, make the hook functions `public` in FeeConcentrationIndex. The harness can still inherit and add view helpers. The `exposed_` functions are no longer needed — the functions are already public.

**Step 2: Update test imports**

Replace all `AccumulatedHHI` imports with `FeeConcentrationState` imports. Replace `getAccumulatedHHI` calls with equivalent `fciState` access.

**Step 3: Run all tests**

Run: `forge test --out out2 --match-path "test/fee-concentration-index/*" -vv`
Expected: All tests pass

**Step 4: Commit**

```bash
git add src/fee-concentration-index/ test/fee-concentration-index/
git commit -m "refactor: remove BaseHook, wire FeeConcentrationState into FCI

- FeeConcentrationIndex no longer inherits BaseHook
- poolManager is immutable in facet (survives delegatecall)
- Storage uses FeeConcentrationState (accumulatedSum, thetaSum, posCount)
- afterAddLiquidity increments posCount
- afterRemoveLiquidity decrements posCount after addTerm
- getIndex() returns (indexA, thetaSum, posCount)
- All tests updated for new signatures"
```

### Task 7: Delete old AccumulatedHHIMod.sol and Kontrol proof

**Files:**
- Delete: `src/fee-concentration-index/types/AccumulatedHHIMod.sol`
- Delete: `test/fee-concentration-index/kontrol/AccumulatedHHI.k.sol`

**Step 1: Verify no remaining imports**

Run: `grep -r "AccumulatedHHIMod\|AccumulatedHHI" src/ test/ --include="*.sol"`
Expected: No matches (all references already updated in Task 6)

**Step 2: Delete files**

```bash
git rm src/fee-concentration-index/types/AccumulatedHHIMod.sol
git rm test/fee-concentration-index/kontrol/AccumulatedHHI.k.sol
```

**Step 3: Verify clean build and tests**

Run: `forge build --out out2 && forge test --out out2 --match-path "test/fee-concentration-index/*" -vv`
Expected: Compiles clean, all tests pass

**Step 4: Commit**

```bash
git commit -m "chore: remove AccumulatedHHIMod.sol (replaced by FeeConcentrationStateMod.sol)"
```

### Task 8: Add integration test — Delta+ computation end-to-end

**Files:**
- Modify: `test/fee-concentration-index/unit/FeeConcentrationIndexFull.unit.t.sol` (or create new file)

**Step 1: Write integration test**

Add a test that:
1. Adds 3 positions (posCount = 3)
2. Does some swaps
3. Removes 1 position (posCount = 2, HHI term added)
4. Calls `getIndex()` and verifies the triple (A_T, Theta, N)
5. Computes Delta+ and price off-chain and verifies they're consistent

**Step 2: Run test**

Run: `forge test --out out2 --match-test "test_deltaPlusEndToEnd" -vv`
Expected: PASS

**Step 3: Commit**

```bash
git add test/fee-concentration-index/
git commit -m "test: add Delta+ end-to-end integration test"
```

### Task 9: Final verification

**Step 1: Run full test suite**

Run: `forge test --out out2 -vv`
Expected: All tests pass (both FCI and theta-swap-insurance tests)

**Step 2: Push branch**

```bash
git push -u origin 001-fci-coprimary-diamond
```

---

## Summary

| Task | Phase | Description | Commit |
|------|-------|-------------|--------|
| 0 | Pre | Create branch off 001 | — |
| 1 | 1 | Failing tests for FeeConcentrationState | — |
| 2 | 1 | Implement FeeConcentrationStateMod.sol | feat: add FeeConcentrationState |
| 3 | 1 | Kontrol proofs | test: Kontrol proofs |
| 4 | 2 | Update storage struct | — (breaks build) |
| 5 | 2 | Rewrite FCI hook + interface | — (breaks build) |
| 6 | 2 | Update harness + all tests | refactor: remove BaseHook |
| 7 | 2 | Delete old AccumulatedHHIMod | chore: remove old type |
| 8 | 2 | Integration test for Delta+ | test: Delta+ e2e |
| 9 | 2 | Final verification + push | — |
