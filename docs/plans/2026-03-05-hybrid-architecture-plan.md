# Hybrid Fee Concentration Insurance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement hook-based mutual insurance with ERC-6909 claims and donate()-based payouts, replacing the Option 1 custom CFMM.

**Architecture:** Separate insurance hook reads (A_T, Theta, N) from FCI hook via `getIndex()`. Premiums collected via gamma% fee share redirect at removeLiquidity. Payouts via `poolManager.donate()` when Delta-plus > Delta-star. ERC-6909 fungible claims per pool. Pro-rata solvency.

**Tech Stack:** Solidity ^0.8.26, Uniswap V4 core (PoolManager, Hooks, StateLibrary, IERC6909), forge-std, Solady FixedPointMathLib, diamond storage pattern. @type-driven-development for all Solidity.

---

### Task 0: Delete Option 1 Custom CFMM Artifacts

These files implement the superseded `y = s - 1 + e^{-s}` custom CFMM. They must be removed before building the hybrid.

**Files:**
- Delete: `src/theta-swap-insurance/modules/InsurancePoolMod.sol`
- Delete: `src/theta-swap-insurance/types/LogPriceMod.sol`
- Delete: `src/theta-swap-insurance/types/MarginMod.sol`
- Delete: `src/theta-swap-insurance/types/UnderwriterPositionMod.sol`
- Delete: `src/theta-swap-insurance/libraries/LogPriceMath.sol`
- Delete: `src/theta-swap-insurance/libraries/SettleMath.sol`
- Delete: `test/theta-swap-insurance/unit/LogPrice.t.sol`
- Delete: `test/theta-swap-insurance/unit/Margin.t.sol`
- Delete: `test/theta-swap-insurance/unit/UnderwriterPosition.t.sol`
- Delete: `test/theta-swap-insurance/kontrol/Margin.k.sol`

**Step 1: Delete the files**

```bash
rm src/theta-swap-insurance/modules/InsurancePoolMod.sol
rm src/theta-swap-insurance/types/LogPriceMod.sol
rm src/theta-swap-insurance/types/MarginMod.sol
rm src/theta-swap-insurance/types/UnderwriterPositionMod.sol
rm src/theta-swap-insurance/libraries/LogPriceMath.sol
rm src/theta-swap-insurance/libraries/SettleMath.sol
rm test/theta-swap-insurance/unit/LogPrice.t.sol
rm test/theta-swap-insurance/unit/Margin.t.sol
rm test/theta-swap-insurance/unit/UnderwriterPosition.t.sol
rm test/theta-swap-insurance/kontrol/Margin.k.sol
```

**Step 2: Verify remaining insurance code compiles**

Run: `forge build --contracts src/theta-swap-insurance/types/PremiumFactorMod.sol`
Expected: compilation success (PremiumFactorMod.sol has no dependency on deleted files)

**Step 3: Commit**

```bash
git add -A src/theta-swap-insurance/modules/InsurancePoolMod.sol \
  src/theta-swap-insurance/types/LogPriceMod.sol \
  src/theta-swap-insurance/types/MarginMod.sol \
  src/theta-swap-insurance/types/UnderwriterPositionMod.sol \
  src/theta-swap-insurance/libraries/LogPriceMath.sol \
  src/theta-swap-insurance/libraries/SettleMath.sol \
  test/theta-swap-insurance/unit/LogPrice.t.sol \
  test/theta-swap-insurance/unit/Margin.t.sol \
  test/theta-swap-insurance/unit/UnderwriterPosition.t.sol \
  test/theta-swap-insurance/kontrol/Margin.k.sol
git commit -m "refactor(insurance): delete Option 1 custom CFMM artifacts

Removes y = s - 1 + e^{-s} trading function, log-price types, margin,
underwriter positions, and settlement math. Superseded by hybrid
architecture (hook insurance + ERC-6909 + donate() payouts).

See: docs/plans/2026-03-05-hybrid-architecture-design.md"
```

---

### Task 1: Extend FCI Storage — Add thetaSum and posCount

The insurance hook needs `(A_T, Theta, N)` but the FCI hook only stores `accumulatedHHI`. Add two per-pool state variables.

**Files:**
- Modify: `src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol:12-21` (add fields to struct)
- Modify: `src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol` (add accessor functions)
- Test: `test/fee-concentration-index/unit/FeeConcentrationIndexStorage.t.sol` (new)

**Step 1: Write the failing test**

Create `test/fee-concentration-index/unit/FeeConcentrationIndexStorage.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {
    fciStorage, FeeConcentrationIndexStorage,
    getThetaSum, setThetaSum, incrementThetaSum,
    getPosCount, incrementPosCount, decrementPosCount
} from "../../src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";

contract FeeConcentrationIndexStorageTest is Test {
    PoolId constant POOL = PoolId.wrap(bytes32(uint256(1)));

    function test_thetaSum_initiallyZero() public view {
        assertEq(getThetaSum(POOL), 0);
    }

    function test_incrementThetaSum() public {
        incrementThetaSum(POOL, 1e18);
        assertEq(getThetaSum(POOL), 1e18);
        incrementThetaSum(POOL, 2e18);
        assertEq(getThetaSum(POOL), 3e18);
    }

    function test_posCount_initiallyZero() public view {
        assertEq(getPosCount(POOL), 0);
    }

    function test_incrementPosCount() public {
        incrementPosCount(POOL);
        assertEq(getPosCount(POOL), 1);
        incrementPosCount(POOL);
        assertEq(getPosCount(POOL), 2);
    }

    function test_decrementPosCount() public {
        incrementPosCount(POOL);
        incrementPosCount(POOL);
        decrementPosCount(POOL);
        assertEq(getPosCount(POOL), 1);
    }

    function test_decrementPosCount_revertsOnUnderflow() public {
        vm.expectRevert();
        decrementPosCount(POOL);
    }
}
```

**Step 2: Run test to verify it fails**

Run: `forge test --match-contract FeeConcentrationIndexStorageTest -vv`
Expected: FAIL — `getThetaSum`, `incrementThetaSum`, `getPosCount`, `incrementPosCount`, `decrementPosCount` do not exist

**Step 3: Implement — add fields and accessors**

In `FeeConcentrationIndexStorageMod.sol`, add to the `FeeConcentrationIndexStorage` struct (after line 21):

```solidity
    // Aggregate theta sum per pool: Σ θ_k = Σ (1/blockLifetime_k)
    // Stored as Q128. Used to compute A_T^null = sqrt(thetaSum / posCount²).
    mapping(PoolId => uint256) thetaSum;
    // Active position count per pool. Incremented at add, decremented at remove.
    mapping(PoolId => uint256) posCount;
```

Add accessor functions after `deleteFeeGrowthBaseline0`:

```solidity
// ── Theta sum accessors ──

function getThetaSum(PoolId poolId) view returns (uint256) {
    return fciStorage().thetaSum[poolId];
}

function setThetaSum(PoolId poolId, uint256 value) {
    fciStorage().thetaSum[poolId] = value;
}

function incrementThetaSum(PoolId poolId, uint256 delta) {
    fciStorage().thetaSum[poolId] += delta;
}

// ── Position count accessors ──

function getPosCount(PoolId poolId) view returns (uint256) {
    return fciStorage().posCount[poolId];
}

function incrementPosCount(PoolId poolId) {
    fciStorage().posCount[poolId] += 1;
}

function decrementPosCount(PoolId poolId) {
    fciStorage().posCount[poolId] -= 1; // reverts on underflow (Solidity 0.8 checked math)
}
```

**Step 4: Run test to verify it passes**

Run: `forge test --match-contract FeeConcentrationIndexStorageTest -vv`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add -f src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol \
  test/fee-concentration-index/unit/FeeConcentrationIndexStorage.t.sol
git commit -m "feat(fci): add thetaSum and posCount to FCI storage

Co-primary state variables for insurance hook. thetaSum tracks aggregate
turnover rate Σ θ_k (Q128). posCount tracks active position count.
Both needed to compute A_T^null = sqrt(Θ/N²) and Δ⁺."
```

---

### Task 2: Wire thetaSum and posCount into FCI Hook

Update the FeeConcentrationIndex hook to increment/decrement the new state variables at add/remove liquidity events, and extend `getIndex()`.

**Files:**
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol:59-87` (_afterAddLiquidity — add posCount increment)
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol:143-183` (_afterRemoveLiquidity — add thetaSum increment, posCount decrement)
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol:185-191` (getIndex — extend signature)
- Test: `test/fee-concentration-index/unit/FeeConcentrationIndexFull.unit.t.sol` (modify — add assertion for thetaSum/posCount)

**Step 1: Write the failing test**

Add to the existing unit test file `test/fee-concentration-index/unit/FeeConcentrationIndexFull.unit.t.sol`. Add a new test function that calls `getIndex()` and asserts the extended return values. The exact test depends on the existing test harness — read the file to see the setup pattern, then add:

```solidity
function test_getIndex_returnsThetaSumAndPosCount() public {
    // After adding one position and removing it:
    // - posCount should be 0 (added then removed)
    // - thetaSum should be > 0 (one θ_k term accumulated)
    // Use existing harness setup to add+remove a position
    // then call getIndex and assert 3 return values
    (uint128 aT, uint128 thetaSum, uint256 posCount) = hook.getIndex(poolKey);
    // After setup with no positions, all should be 0
    assertEq(thetaSum, 0);
    assertEq(posCount, 0);
}
```

Note: the implementer should read `test/fee-concentration-index/unit/FeeConcentrationIndexFull.unit.t.sol` and `test/fee-concentration-index/helpers/FCITestHelper.sol` to understand the existing test harness before writing this test.

**Step 2: Run test to verify it fails**

Run: `forge test --match-test test_getIndex_returnsThetaSumAndPosCount -vv`
Expected: FAIL — `getIndex()` returns 2 values, not 3

**Step 3: Implement**

In `FeeConcentrationIndex.sol`:

1. In `_afterAddLiquidity` (line ~78), after `$.registries[poolId].register(...)`, add:
```solidity
incrementPosCount(poolId);
```

2. In `_afterRemoveLiquidity` (line ~176), after `$.accumulatedHHI[poolId] = $.accumulatedHHI[poolId].addTerm(...)`, add:
```solidity
// thetaSum += 1/blockLifetime (Q128 precision)
uint256 thetaTerm = Q128 / blockLifetime.floorOne();
incrementThetaSum(poolId, thetaTerm);
```

3. In `_afterRemoveLiquidity`, after the if-block (or unconditionally), add:
```solidity
decrementPosCount(poolId);
```

4. Update `getIndex` signature (line 185):
```solidity
function getIndex(PoolKey calldata key)
    external view
    returns (uint128 aT, uint128 thetaSum, uint256 posCount)
{
    FeeConcentrationIndexStorage storage $ = fciStorage();
    PoolId poolId = PoolIdLibrary.toId(key);
    aT = $.accumulatedHHI[poolId].toIndexA();
    thetaSum = uint128($.thetaSum[poolId] > type(uint128).max
        ? type(uint128).max
        : $.thetaSum[poolId]);
    posCount = $.posCount[poolId];
}
```

5. Add imports at top: `incrementThetaSum, incrementPosCount, decrementPosCount` from storage module.
6. Add import: `Q128` from `AccumulatedHHIMod.sol`.

**Step 4: Run tests**

Run: `forge test --match-contract FeeConcentrationIndex -vv`
Expected: all existing tests pass + new test passes

**Step 5: Commit**

```bash
git add -f src/fee-concentration-index/FeeConcentrationIndex.sol \
  test/fee-concentration-index/unit/FeeConcentrationIndexFull.unit.t.sol
git commit -m "feat(fci): wire thetaSum/posCount into hook + extend getIndex()

posCount incremented at afterAddLiquidity, decremented at afterRemoveLiquidity.
thetaSum += Q128/blockLifetime at each removal. getIndex() now returns
(aT, thetaSum, posCount) for the insurance hook to derive Δ⁺."
```

---

### Task 3: ReserveMod — Per-Pool Reserve Accounting Type

New UDVT for the per-pool insurance reserve with deposit/withdraw/donate operations.

**Files:**
- Create: `src/theta-swap-insurance/types/ReserveMod.sol`
- Test: `test/theta-swap-insurance/unit/Reserve.t.sol`

**Step 1: Write the failing test**

Create `test/theta-swap-insurance/unit/Reserve.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    Reserve, ZERO_RESERVE,
    deposit, withdraw, donateAmount, balance, isEmpty
} from "../../src/theta-swap-insurance/types/ReserveMod.sol";

contract ReserveTest is Test {
    function test_zeroReserve_isEmpty() public pure {
        assertTrue(ZERO_RESERVE.isEmpty());
    }

    function test_deposit_increasesBalance() public pure {
        Reserve r = ZERO_RESERVE.deposit(100);
        assertEq(r.balance(), 100);
        assertFalse(r.isEmpty());
    }

    function test_deposit_accumulates() public pure {
        Reserve r = ZERO_RESERVE.deposit(100).deposit(50);
        assertEq(r.balance(), 150);
    }

    function test_withdraw_decreasesBalance() public pure {
        Reserve r = ZERO_RESERVE.deposit(100).withdraw(40);
        assertEq(r.balance(), 60);
    }

    function test_withdraw_revertsOnUnderflow() public {
        Reserve r = ZERO_RESERVE.deposit(10);
        vm.expectRevert();
        r.withdraw(11);
    }

    function test_donateAmount_capsAtBalance() public pure {
        Reserve r = ZERO_RESERVE.deposit(100);
        (Reserve after_, uint256 donated) = r.donateAmount(150);
        assertEq(donated, 100); // capped at balance (pro-rata haircut)
        assertEq(after_.balance(), 0);
    }

    function test_donateAmount_partialDonate() public pure {
        Reserve r = ZERO_RESERVE.deposit(100);
        (Reserve after_, uint256 donated) = r.donateAmount(40);
        assertEq(donated, 40);
        assertEq(after_.balance(), 60);
    }
}
```

**Step 2: Run test to verify it fails**

Run: `forge test --match-contract ReserveTest -vv`
Expected: FAIL — ReserveMod.sol does not exist

**Step 3: Implement**

Create `src/theta-swap-insurance/types/ReserveMod.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Per-pool insurance reserve balance.
// Funded by γ% fee redirect. Depleted by donate() payouts.
// uint256 to match ERC-20 balance precision.

type Reserve is uint256;

Reserve constant ZERO_RESERVE = Reserve.wrap(0);

function balance(Reserve r) pure returns (uint256) {
    return Reserve.unwrap(r);
}

function isEmpty(Reserve r) pure returns (bool) {
    return Reserve.unwrap(r) == 0;
}

function deposit(Reserve r, uint256 amount) pure returns (Reserve) {
    return Reserve.wrap(Reserve.unwrap(r) + amount); // reverts on overflow
}

function withdraw(Reserve r, uint256 amount) pure returns (Reserve) {
    return Reserve.wrap(Reserve.unwrap(r) - amount); // reverts on underflow
}

/// @dev Compute donate amount with pro-rata haircut.
///      If requested > balance, donates entire balance (haircut).
///      Returns (newReserve, actualDonated).
function donateAmount(Reserve r, uint256 requested)
    pure
    returns (Reserve, uint256)
{
    uint256 bal = Reserve.unwrap(r);
    uint256 actual = requested > bal ? bal : requested;
    return (Reserve.wrap(bal - actual), actual);
}

using {balance, isEmpty, deposit, withdraw, donateAmount} for Reserve global;
```

**Step 4: Run test to verify it passes**

Run: `forge test --match-contract ReserveTest -vv`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add -f src/theta-swap-insurance/types/ReserveMod.sol \
  test/theta-swap-insurance/unit/Reserve.t.sol
git commit -m "feat(insurance): ReserveMod UDVT for per-pool insurance reserve

Wraps uint256 balance with deposit/withdraw/donateAmount operations.
Pro-rata haircut: donateAmount caps at available balance."
```

---

### Task 4: DonateCalcLib — Compute Donate Amount from Delta-plus

Pure library that computes how much to donate from the reserve given Delta-plus, Delta-star, and total insured liquidity.

**Files:**
- Create: `src/theta-swap-insurance/libraries/DonateCalcLib.sol`
- Test: `test/theta-swap-insurance/unit/DonateCalc.t.sol`

**Step 1: Write the failing test**

Create `test/theta-swap-insurance/unit/DonateCalc.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {DonateCalcLib} from "../../src/theta-swap-insurance/libraries/DonateCalcLib.sol";

contract DonateCalcTest is Test {
    // Delta-star = 0.09 in Q128
    uint128 constant DELTA_STAR_Q128 = uint128((9 * (1 << 128)) / 100);

    function test_noDonate_whenBelowThreshold() public pure {
        // Delta-plus = 0.05 < Delta-star = 0.09
        uint128 deltaPlus = uint128((5 * (1 << 128)) / 100);
        uint256 amount = DonateCalcLib.computeDonation(deltaPlus, DELTA_STAR_Q128, 1000e6);
        assertEq(amount, 0);
    }

    function test_noDonate_whenEqual() public pure {
        uint256 amount = DonateCalcLib.computeDonation(DELTA_STAR_Q128, DELTA_STAR_Q128, 1000e6);
        assertEq(amount, 0);
    }

    function test_donates_whenAboveThreshold() public pure {
        // Delta-plus = 0.18 (2x Delta-star)
        uint128 deltaPlus = uint128((18 * (1 << 128)) / 100);
        uint256 amount = DonateCalcLib.computeDonation(deltaPlus, DELTA_STAR_Q128, 1000e6);
        // (0.18 - 0.09) / (1 - 0.09) * reserve = 0.09/0.91 * 1000 ≈ 98.9
        assertTrue(amount > 0);
        assertTrue(amount < 1000e6); // should not exceed reserve
    }

    function test_donates_zero_reserve() public pure {
        uint128 deltaPlus = uint128((18 * (1 << 128)) / 100);
        uint256 amount = DonateCalcLib.computeDonation(deltaPlus, DELTA_STAR_Q128, 0);
        assertEq(amount, 0);
    }
}
```

**Step 2: Run test to verify it fails**

Run: `forge test --match-contract DonateCalcTest -vv`
Expected: FAIL — DonateCalcLib does not exist

**Step 3: Implement**

Create `src/theta-swap-insurance/libraries/DonateCalcLib.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";

/// @dev Compute donate amount from concentration deviation.
///      donation = (Δ⁺ - Δ*) / (1 - Δ*) * reserveBalance
///      This normalizes the excess deviation into a [0, 1) fraction of the reserve.
library DonateCalcLib {
    uint256 internal constant Q128 = 1 << 128;

    function computeDonation(
        uint128 deltaPlusQ128,
        uint128 deltaStarQ128,
        uint256 reserveBalance
    ) internal pure returns (uint256) {
        if (deltaPlusQ128 <= deltaStarQ128) return 0;
        if (reserveBalance == 0) return 0;

        uint256 excess = uint256(deltaPlusQ128) - uint256(deltaStarQ128);
        uint256 denominator = Q128 - uint256(deltaStarQ128);

        return FixedPointMathLib.mulDiv(reserveBalance, excess, denominator);
    }
}
```

**Step 4: Run test to verify it passes**

Run: `forge test --match-contract DonateCalcTest -vv`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add -f src/theta-swap-insurance/libraries/DonateCalcLib.sol \
  test/theta-swap-insurance/unit/DonateCalc.t.sol
git commit -m "feat(insurance): DonateCalcLib — donate amount from Δ⁺ and reserve

Pure library: donation = (Δ⁺ - Δ*) / (1 - Δ*) * reserve.
Zero if Δ⁺ ≤ Δ*, zero if reserve is empty."
```

---

### Task 5: ClaimsMod — ERC-6909 Mint/Burn Logic

Minimal ERC-6909 implementation for the insurance hook. `tokenId = uint256(PoolId)`.

**Files:**
- Create: `src/theta-swap-insurance/types/ClaimsMod.sol`
- Test: `test/theta-swap-insurance/unit/Claims.t.sol`

**Step 1: Write the failing test**

Create `test/theta-swap-insurance/unit/Claims.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {
    ClaimsStorage, claimsStorage,
    mintClaim, burnClaim, balanceOfClaim, totalSupplyOf, tokenIdFromPool
} from "../../src/theta-swap-insurance/types/ClaimsMod.sol";

contract ClaimsTest is Test {
    PoolId constant POOL = PoolId.wrap(bytes32(uint256(42)));
    address constant ALICE = address(0xA11CE);
    address constant BOB = address(0xB0B);

    function test_tokenIdFromPool() public pure {
        uint256 id = tokenIdFromPool(POOL);
        assertEq(id, uint256(bytes32(uint256(42))));
    }

    function test_mintClaim() public {
        mintClaim(POOL, ALICE, 1000);
        assertEq(balanceOfClaim(POOL, ALICE), 1000);
        assertEq(totalSupplyOf(POOL), 1000);
    }

    function test_mintClaim_twoUsers() public {
        mintClaim(POOL, ALICE, 1000);
        mintClaim(POOL, BOB, 500);
        assertEq(balanceOfClaim(POOL, ALICE), 1000);
        assertEq(balanceOfClaim(POOL, BOB), 500);
        assertEq(totalSupplyOf(POOL), 1500);
    }

    function test_burnClaim() public {
        mintClaim(POOL, ALICE, 1000);
        burnClaim(POOL, ALICE, 400);
        assertEq(balanceOfClaim(POOL, ALICE), 600);
        assertEq(totalSupplyOf(POOL), 600);
    }

    function test_burnClaim_revertsOnUnderflow() public {
        mintClaim(POOL, ALICE, 100);
        vm.expectRevert();
        burnClaim(POOL, ALICE, 101);
    }
}
```

**Step 2: Run test to verify it fails**

Run: `forge test --match-contract ClaimsTest -vv`
Expected: FAIL — ClaimsMod.sol does not exist

**Step 3: Implement**

Create `src/theta-swap-insurance/types/ClaimsMod.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId} from "v4-core/src/types/PoolId.sol";

// Diamond storage for ERC-6909 insurance claims.
// tokenId = uint256(PoolId) — one fungible index asset per insured pool.

struct ClaimsStorage {
    // tokenId => owner => balance
    mapping(uint256 => mapping(address => uint256)) balances;
    // tokenId => totalSupply
    mapping(uint256 => uint256) totalSupply;
}

bytes32 constant CLAIMS_STORAGE_SLOT = keccak256("ThetaSwapInsurance.claims");

function claimsStorage() pure returns (ClaimsStorage storage s) {
    bytes32 slot = CLAIMS_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}

function tokenIdFromPool(PoolId poolId) pure returns (uint256) {
    return uint256(PoolId.unwrap(poolId));
}

function mintClaim(PoolId poolId, address to, uint256 amount) {
    uint256 id = tokenIdFromPool(poolId);
    ClaimsStorage storage $ = claimsStorage();
    $.balances[id][to] += amount;
    $.totalSupply[id] += amount;
}

function burnClaim(PoolId poolId, address from, uint256 amount) {
    uint256 id = tokenIdFromPool(poolId);
    ClaimsStorage storage $ = claimsStorage();
    $.balances[id][from] -= amount; // reverts on underflow
    $.totalSupply[id] -= amount;
}

function balanceOfClaim(PoolId poolId, address owner) view returns (uint256) {
    uint256 id = tokenIdFromPool(poolId);
    return claimsStorage().balances[id][owner];
}

function totalSupplyOf(PoolId poolId) view returns (uint256) {
    uint256 id = tokenIdFromPool(poolId);
    return claimsStorage().totalSupply[id];
}
```

**Step 4: Run test to verify it passes**

Run: `forge test --match-contract ClaimsTest -vv`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add -f src/theta-swap-insurance/types/ClaimsMod.sol \
  test/theta-swap-insurance/unit/Claims.t.sol
git commit -m "feat(insurance): ClaimsMod — ERC-6909 mint/burn for insurance claims

Diamond storage. tokenId = uint256(PoolId). One fungible index asset per pool.
Mint at registration, burn at deregistration."
```

---

### Task 6: Update ThetaSwapStorageMod — Add Reserve and ProtectionGrowth

Extend the existing insurance diamond storage with the reserve and protection growth accumulator.

**Files:**
- Modify: `src/theta-swap-insurance/modules/ThetaSwapStorageMod.sol:16-23` (add fields)
- Modify: `test/theta-swap-insurance/unit/ThetaSwapStorage.t.sol` (add tests)

**Step 1: Write the failing test**

Add to `test/theta-swap-insurance/unit/ThetaSwapStorage.t.sol` (read existing tests first, extend):

```solidity
function test_reserve_initiallyZero() public view {
    assertEq(getReserve(POOL).balance(), 0);
}

function test_setReserve() public {
    setReserve(POOL, ZERO_RESERVE.deposit(1000));
    assertEq(getReserve(POOL).balance(), 1000);
}

function test_protectionGrowth_initiallyZero() public view {
    assertEq(getProtectionGrowth(POOL), 0);
}

function test_incrementProtectionGrowth() public {
    incrementProtectionGrowth(POOL, 500);
    assertEq(getProtectionGrowth(POOL), 500);
    incrementProtectionGrowth(POOL, 300);
    assertEq(getProtectionGrowth(POOL), 800);
}

function test_getProtectionGrowthSnapshot() public {
    bytes32 posKey = bytes32(uint256(99));
    setProtectionGrowthSnapshot(POOL, posKey, 42);
    assertEq(getProtectionGrowthSnapshot(POOL, posKey), 42);
}
```

**Step 2: Run test to verify it fails**

Run: `forge test --match-contract ThetaSwapStorageTest -vv`
Expected: FAIL — `getReserve`, `setReserve`, `getProtectionGrowth`, etc. do not exist

**Step 3: Implement**

Add to `ThetaSwapInsuranceStorage` struct in `ThetaSwapStorageMod.sol`:

```solidity
    // Per-pool insurance reserve (funded by γ% fee redirect)
    mapping(PoolId => Reserve) reserves;
    // Per-pool protection growth accumulator (Q128, like feeGrowthGlobal)
    // Incremented when Δ⁺ > Δ* at any liquidity event
    mapping(PoolId => uint256) protectionGrowthPerLiquidityX128;
    // Per-position snapshot of protectionGrowth at registration time
    mapping(PoolId => mapping(bytes32 => uint256)) protectionGrowthSnapshot;
    // Delta-star threshold (Q128, set at initialization)
    mapping(PoolId => uint128) deltaStar;
    // FCI hook address (set at initialization)
    address fciHook;
```

Add import: `import {Reserve, ZERO_RESERVE} from "../types/ReserveMod.sol";`

Add accessor functions:

```solidity
function getReserve(PoolId poolId) view returns (Reserve) {
    return tsiStorage().reserves[poolId];
}

function setReserve(PoolId poolId, Reserve value) {
    tsiStorage().reserves[poolId] = value;
}

function getProtectionGrowth(PoolId poolId) view returns (uint256) {
    return tsiStorage().protectionGrowthPerLiquidityX128[poolId];
}

function incrementProtectionGrowth(PoolId poolId, uint256 delta) {
    tsiStorage().protectionGrowthPerLiquidityX128[poolId] += delta;
}

function getProtectionGrowthSnapshot(PoolId poolId, bytes32 positionKey) view returns (uint256) {
    return tsiStorage().protectionGrowthSnapshot[poolId][positionKey];
}

function setProtectionGrowthSnapshot(PoolId poolId, bytes32 positionKey, uint256 value) {
    tsiStorage().protectionGrowthSnapshot[poolId][positionKey] = value;
}

function getDeltaStar(PoolId poolId) view returns (uint128) {
    return tsiStorage().deltaStar[poolId];
}

function setDeltaStar(PoolId poolId, uint128 value) {
    tsiStorage().deltaStar[poolId] = value;
}

function getFciHook() view returns (address) {
    return tsiStorage().fciHook;
}

function setFciHook(address hook) {
    tsiStorage().fciHook = hook;
}
```

**Step 4: Run test to verify it passes**

Run: `forge test --match-contract ThetaSwapStorageTest -vv`
Expected: PASS (existing + new tests)

**Step 5: Commit**

```bash
git add -f src/theta-swap-insurance/modules/ThetaSwapStorageMod.sol \
  test/theta-swap-insurance/unit/ThetaSwapStorage.t.sol
git commit -m "feat(insurance): extend storage with reserve, protectionGrowth, deltaStar

Reserve: per-pool USDC balance for insurance payouts.
protectionGrowthPerLiquidityX128: accumulator like feeGrowthGlobal.
protectionGrowthSnapshot: per-position snapshot at registration.
deltaStar: Q128 threshold per pool. fciHook: address of FCI hook."
```

---

### Task 7: Update IThetaSwapInsurance Interface

Remove underwriter methods (Option 1), add reserve/protection views for hybrid.

**Files:**
- Modify: `src/theta-swap-insurance/interfaces/IThetaSwapInsurance.sol`
- No test (interface only)

**Step 1: Rewrite the interface**

Replace the full contents of `IThetaSwapInsurance.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";

/// @title IThetaSwapInsurance
/// @notice Hybrid fee concentration insurance: hook mutual insurance + ERC-6909 claims.
///         No underwriters — premiums collected via fee redirect, payouts via donate().
interface IThetaSwapInsurance {
    // ── Events ──

    event InsuranceInitialized(PoolId indexed poolId, uint128 deltaStar, uint128 gamma);

    event PLPRegistered(
        PoolId indexed poolId,
        bytes32 indexed positionKey,
        address plp,
        uint128 liquidity,
        uint128 gamma
    );

    event PLPDeregistered(
        PoolId indexed poolId,
        bytes32 indexed positionKey,
        uint256 premiumPaid,
        uint256 protectionReceived
    );

    event ProtectionDonated(
        PoolId indexed poolId,
        uint256 donationAmount,
        uint128 deltaPlus,
        uint128 deltaStar
    );

    event PremiumCollected(
        PoolId indexed poolId,
        bytes32 indexed positionKey,
        uint256 premiumAmount
    );

    // ── Errors ──

    error Insurance__NotInitialized();
    error Insurance__AlreadyInitialized();
    error Insurance__NotRegistered();
    error Insurance__ZeroLiquidity();
    error Insurance__InvalidGamma();
    error Insurance__FCICallFailed();

    // ── Views ──

    function getReserveBalance(PoolKey calldata poolKey) external view returns (uint256);

    function getProtectionGrowth(PoolKey calldata poolKey) external view returns (uint256);

    function getDeltaStar(PoolKey calldata poolKey) external view returns (uint128);

    function getClaimBalance(PoolKey calldata poolKey, address owner) external view returns (uint256);

    function getTotalClaims(PoolKey calldata poolKey) external view returns (uint256);
}
```

**Step 2: Verify compilation**

Run: `forge build --contracts src/theta-swap-insurance/interfaces/IThetaSwapInsurance.sol`
Expected: compilation success

**Step 3: Commit**

```bash
git add -f src/theta-swap-insurance/interfaces/IThetaSwapInsurance.sol
git commit -m "refactor(insurance): update interface for hybrid architecture

Remove underwriter methods (addUnderwriterLiquidity, removeUnderwriterLiquidity).
Remove custom CFMM views (getInsuranceState, getMarkPrice).
Add reserve/protectionGrowth/claims views for hook mutual insurance."
```

---

### Task 8: LaTeX Spec — Resolve Architecture + Add Hybrid Invariants

Update `specs/model/` to reflect the hybrid architecture decision.

**Files:**
- Modify: `specs/model/main.tex` (resolve pending, update abstract)
- Modify: `specs/model/preamble.tex` (add hybrid notation)
- Modify: `specs/model/funding-rate.tex` (update mark price, add donate() settlement)
- Modify: `specs/model/invariants.tex` (replace pending stub with INS-01 through INS-05)
- Create: `specs/model/reserves.tex` (reserve accounting)
- Create: `specs/model/initialization.tex` (hook initialization)

**Step 1: Update preamble.tex**

Replace the "Architecture-dependent (TBD)" comment block (lines 48-58) with:

```latex
% ── Hybrid insurance notation ────────────────────────────────────────────────
\newcommand{\premfactor}{\gamma}            % premium factor (fee redirect fraction)
\newcommand{\Res}{R}                         % per-pool reserve balance
\newcommand{\protgrowth}{g^{\text{prot}}}   % protection growth per liquidity (Q128)
\newcommand{\donateamt}{D}                   % donate amount at a liquidity event
```

**Step 2: Update main.tex**

Replace the abstract's last sentence (line 36) with:
```latex
Cross-pool empirical analysis (Spearman $\rho = +0.19$, weak TVL--concentration
correlation) selects the \textbf{hybrid} architecture: hook-based mutual insurance
with ERC-6909 transferable claims and a deferred CFMM market layer.
```

Replace line 43 (`\input{invariants}`) with:
```latex
\input{reserves}
\input{initialization}
\input{invariants}
```

Replace Section 7 "Architecture Decision: Pending" (lines 214-240) with:
```latex
\section{Architecture Decision: Hybrid}\label{sec:architecture}

Cross-pool empirical analysis (\texttt{cross-pool-concentration-severity.ipynb})
established that fee concentration does not correlate with pool size
(Spearman $\rho = +0.19$). Neither pure hook-insurance nor pure CFMM-pool is
empirically justified. The hybrid architecture is selected:

\begin{enumerate}
  \item \textbf{Base layer:} V4 hook tracks $\AT$, $\ThetaSum$, $\PosCount$ per pool.
  \item \textbf{Insurance:} Separate hook collects $\premfactor\%$ of PLP fees into
    per-pool reserve $\Res$. When $\DeltaPlus > \DeltaStar$, calls
    \texttt{poolManager.donate()} to distribute protection.
  \item \textbf{Claims:} ERC-6909 fungible tokens per pool
    ($\texttt{tokenId} = \texttt{uint256(PoolId)}$). Transferable.
  \item \textbf{Solvency:} Pro-rata haircut if $\Res < \donateamt$.
  \item \textbf{Market layer (deferred):} CFMM pool for ERC-6909 claims
    can emerge for high-TVL pools.
\end{enumerate}
```

**Step 3: Create reserves.tex**

Create `specs/model/reserves.tex`:

```latex
% reserves.tex — Per-pool insurance reserve accounting
% Kontrol: prove_ins_reserveNonNeg, prove_ins_premiumCollection

\section{Reserve Accounting}\label{sec:reserves}

\subsection{Premium Collection}

At each \texttt{afterRemoveLiquidity} event for a registered PLP:
\begin{equation}\label{eq:premium}
  \text{premium}_k = \premfactor \cdot \text{accruedFees}_k
\end{equation}
where $\premfactor \in (0, 1)$ is the premium factor committed at registration.
The reserve updates:
\begin{equation}\label{eq:reserve-deposit}
  \Res' = \Res + \text{premium}_k
\end{equation}

\subsection{Donate Payout}

At each liquidity event where $\DeltaPlus > \DeltaStar$:
\begin{equation}\label{eq:donate-amount}
  \donateamt = \frac{\DeltaPlus - \DeltaStar}{1 - \DeltaStar} \cdot \Res
\end{equation}
The hook calls \texttt{poolManager.donate()} with amount $\min(\donateamt, \Res)$
(pro-rata haircut). The reserve updates:
\begin{equation}\label{eq:reserve-withdraw}
  \Res' = \Res - \min(\donateamt, \Res)
\end{equation}

\begin{remark}[No External Capital]
The reserve is funded solely by PLP premium contributions ($\premfactor$-share of fees).
No external deposits. This ensures self-bootstrapping: any pool with registered PLPs
accumulates a reserve proportional to its fee volume.
\end{remark}
```

**Step 4: Create initialization.tex**

Create `specs/model/initialization.tex`:

```latex
% initialization.tex — Hook initialization parameters
% Kontrol: prove_ins_initOnce

\section{Initialization}\label{sec:initialization}

The insurance hook is initialized per pool with:
\begin{itemize}
  \item $\DeltaStar$: concentration threshold (Q128). Calibrated from
    econometric turning point $\DeltaStar \approx 0.09$.
  \item \texttt{fciHook}: address of the FeeConcentrationIndex hook
    (source of $\AT$, $\ThetaSum$, $\PosCount$ via \texttt{getIndex()}).
\end{itemize}

The premium factor $\premfactor$ is set per-PLP at registration time
(encoded in \texttt{hookData}).

\begin{remark}[One-Time Initialization]
Each pool can be initialized exactly once. The insurance hook stores
$\DeltaStar$ and verifies $\texttt{fciHook} \neq \texttt{address(0)}$.
\end{remark}
```

**Step 5: Update invariants.tex**

Replace the "Architecture-Dependent Invariants (Pending)" subsection (lines 152-172) with:

```latex
% ══════════════════════════════════════════════════════════════════════════════
\subsection{Hybrid Insurance Invariants (INS-01 through INS-05)}
% ══════════════════════════════════════════════════════════════════════════════

\begin{invariant}{INS-01}{Reserve non-negativity}
% Kontrol: prove_ins_reserveNonNeg
\[
  \Res \geq 0
\]
The per-pool reserve balance is non-negative at all times. Enforced by
checked arithmetic in \texttt{ReserveMod.withdraw}.
\end{invariant}

\begin{invariant}{INS-02}{Premium collection correctness}
% Kontrol: prove_ins_premiumCollection
\[
  \{\texttt{afterRemoveLiquidity}, \text{PLP registered with } \premfactor\}
  \;\longrightarrow\;
  \{\Res' = \Res + \premfactor \cdot \text{accruedFees}\}
\]
Premium is exactly $\premfactor$-fraction of the PLP's accrued fees,
added atomically to the reserve.
\end{invariant}

\begin{invariant}{INS-03}{Donate trigger correctness}
% Kontrol: prove_ins_donateTrigger
\[
  \{\DeltaPlus > \DeltaStar\}
  \;\longrightarrow\;
  \{\texttt{donate}(\min(\donateamt, \Res))\}
  \quad\text{and}\quad
  \{\DeltaPlus \leq \DeltaStar\}
  \;\longrightarrow\;
  \{\text{no donation}\}
\]
The hook donates if and only if concentration exceeds the threshold.
\end{invariant}

\begin{invariant}{INS-04}{Claim mint/burn conservation}
% Kontrol: prove_ins_claimConservation
\[
  \sum_{\text{owner}} \text{balanceOf}(\text{poolId}, \text{owner})
  = \text{totalSupply}(\text{poolId})
\]
Total supply of ERC-6909 claims equals the sum of all holder balances.
Minting increases both by \texttt{liquidity}. Burning decreases both.
\end{invariant}

\begin{invariant}{INS-05}{Pro-rata fairness}
% Kontrol: prove_ins_proRataFairness
\[
  \text{donated}_i = \frac{\text{claimBalance}_i}{\text{totalSupply}} \cdot \donateamt
\]
Each claim holder's share of the donation is proportional to their claim balance.
Guaranteed by V4's \texttt{donate()} distributing via \texttt{feeGrowthGlobal}.
\end{invariant}
```

**Step 6: Update funding-rate.tex**

Replace the mark price definition (lines 21-29) with:

```latex
\begin{definition}[Mark Price]\label{def:mark-price}
The mark price is the implied cost of fee concentration protection, derived
from the accumulated protection growth:
\[
  p_{\text{mark}} = \frac{\protgrowth}{\text{totalInsuredLiquidity}}
\]
where $\protgrowth = \sum_n \donateamt_n / L_{\text{insured},n}$ accumulates
at each donation event.
\end{definition}
```

**Step 7: Compile LaTeX to verify**

Run: `cd specs/model && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex`
Expected: compiles without errors (warnings about missing references are OK)

**Step 8: Commit**

```bash
git add -f specs/model/main.tex specs/model/preamble.tex specs/model/funding-rate.tex \
  specs/model/invariants.tex specs/model/reserves.tex specs/model/initialization.tex
git commit -m "docs(spec): resolve architecture to hybrid — add reserves, initialization, INS invariants

Replace 'Architecture Decision: Pending' with hybrid architecture backed by
cross-pool empirical analysis. Add reserves.tex (γ% fee redirect, donate formula),
initialization.tex (Δ*, fciHook). Replace pending invariant stub with INS-01
through INS-05 (reserve non-neg, premium collection, donate trigger, claim
conservation, pro-rata fairness). Update preamble notation and mark price def."
```

---

### Task 9: Smoke Test — Full Compilation

Verify everything compiles together after all changes.

**Files:**
- No new files

**Step 1: Full forge build**

Run: `forge build`
Expected: compilation success for all contracts

**Step 2: Full forge test**

Run: `forge test -vv`
Expected: all tests pass (existing FCI tests + new Reserve/DonateCalc/Claims/Storage tests)

**Step 3: LaTeX compilation**

Run: `cd specs/model && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex`
Expected: PDF generated without errors

**Step 4: Commit (if any fix-ups needed)**

Only commit if Step 1-3 required fixes. Otherwise, no commit needed.
