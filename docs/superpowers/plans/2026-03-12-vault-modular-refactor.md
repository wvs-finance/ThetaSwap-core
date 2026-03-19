# Vault Modular Refactor — CollateralCustodian + OraclePayoff Split

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **REQUIRED:** Use @type-driven-development throughout. SCOP constraints enforced: no `library` keyword, no contract inheritance (except tests/tokens/interface implementation), no `modifier` keyword, no ternary operator. File-level free functions only for modules.
>
> **SCOP exceptions:** (1) Test contracts inherit `Test`. (2) Facet contracts implement interfaces. (3) `ERC20WrapperFacade` is a Compose ERC20 diamond facet — uses `LibERC20` from Compose, not solmate.

**Goal:** Split `FciTokenVaultMod.sol` into two modules — a permanent CollateralCustodian (deposit/mintPair/redeemPair) and a removable OraclePayoff module (poke/settle/redeemLong/redeemShort) — so the vault can transition from Model B (oracle-based redemption) to Model C (50/50 mint/burn for CFMM) by swapping one diamond facet.

**Architecture:** The CollateralCustodian holds USDC, enforces the conservation invariant `1 LONG + 1 SHORT = 1 USDC`, and handles paired mint/burn via ERC-6909. The OraclePayoff module reads the FCI oracle, maintains HWM state, and enables single-sided redemptions. Both live as diamond facets with disjoint storage slots. Model B→C transition (issue #41) means deploying a new facet that removes the oracle dependency.

**Tech Stack:** Solidity ^0.8.26, Solady (FixedPointMathLib, SafeTransferLib, SafeCastLib), Compose (LibERC20 for ERC-20 wrapper facets, LibERC6909 for multi-token), SqrtPriceLibrary (foundational-hooks), Forge (unit + fuzz + invariant tests).

**Spec:** `docs/plans/2026-03-10-fci-token-vault-design.md` (design), `docs/research/panoptic-collateral-tracker-patterns.md` (Panoptic patterns), `docs/research/vault-standards-research.md` (invariants)

**Research inputs:**
- Panoptic CollateralTracker: internal asset tracking, rounding discipline, CEI ordering, access control via single coordinator
- Gnosis CTF: atomic paired mint/burn, mergePositions as risk-free exit
- Cork exploit: immutable oracle address, collateral-before-mint, reentrancy guards
- UMA LSP: pluggable payoff library pattern (Financial Product Library)

---

## Scope Check

This plan covers one coherent refactor: splitting a monolithic vault module into two diamond facets with clean interfaces. The ERC-20 wrapper facades are included as they enable the CFMM composability that motivates the split. Invariant fuzz tests are included because the refactor changes storage layout and must not break the conservation invariant.

**Not in scope:** CFMM (branch 005/006), Dynamic Fee Plugin, JitGame payoff bug fix (separate task).

---

## File Structure

```
src/fci-token-vault/
  storage/
    CustodianStorage.sol                — permanent storage: totalDeposits, collateralToken, depositCap
    OraclePayoffStorage.sol             — removable storage: HWM, halfLife, expiry, settled, longPayoutPerToken
  modules/
    CollateralCustodianMod.sol          — permanent: deposit, mintPair, burnPair, redeemPair
    OraclePayoffMod.sol                 — removable: poke, settle, redeemLong, redeemShort
    dependencies/
      ERC6909Lib.sol                    — (exists) mint/burn/balanceOf
      ReentrancyLib.sol                 — transient-storage reentrancy guard
  libraries/
    SqrtPriceLookbackPayoffX96Lib.sol   — (exists) payoff math
  interfaces/
    ICollateralCustodian.sol            — permanent interface: deposit, redeemPair, preview functions
    IOraclePayoff.sol                   — removable interface: poke, settle, redeemLong, redeemShort
  facets/
    CollateralCustodianFacet.sol        — permanent facet: CEI collateral transfers + module calls
    OraclePayoffFacet.sol              — removable facet: oracle-dependent operations
  tokens/
    ERC20WrapperFacade.sol              — Compose LibERC20 wrapper over ERC-6909 token ID (diamond facet, not solmate)

test/fci-token-vault/
  unit/
    CollateralCustodianMod.t.sol        — unit tests for custodian module
    OraclePayoffMod.t.sol              — unit tests for oracle payoff module
    ReentrancyLib.t.sol                — reentrancy guard tests
  fuzz/
    CustodianInvariant.fuzz.t.sol       — handler-based invariant testing (13 invariants)
  helpers/
    CustodianHarness.sol               — test harness for new modules
    FciTokenVaultHarness.sol           — (exists) preserved for backward compat

# Files to delete after refactor:
#   src/fci-token-vault/modules/FciTokenVaultMod.sol     — replaced by CustodianMod + OraclePayoffMod
#   src/fci-token-vault/FciTokenVaultFacet.sol            — replaced by two facets
#   src/fci-token-vault/interfaces/IFciTokenVault.sol     — replaced by two interfaces
```

---

## Chunk 1: Storage Separation + ReentrancyLib

### Task 1: Define CustodianStorage

**Files:**
- Create: `src/fci-token-vault/storage/CustodianStorage.sol`

- [ ] **Step 1: Write the storage struct and accessor**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

bytes32 constant CUSTODIAN_STORAGE_POSITION = keccak256("thetaswap.collateral-custodian");

struct CustodianStorage {
    uint128 totalDeposits;     // total USDC locked (uint128: cap at ~3.4e38)
    address collateralToken;   // USDC address (immutable after init)
    uint128 depositCap;        // max total deposits (0 = unlimited)
}

error DepositCapExceeded();
error ZeroAmount();

function getCustodianStorage() pure returns (CustodianStorage storage s) {
    bytes32 position = CUSTODIAN_STORAGE_POSITION;
    assembly {
        s.slot := position
    }
}
```

Key decisions:
- `totalDeposits` is `uint128` (not `uint256`) — sufficient for any USDC amount, allows packing
- Separate storage slot from oracle state (disjoint diamond slots)
- `depositCap` from Panoptic pattern: prevents overflow in downstream math

- [ ] **Step 2: Verify compilation**

Run: `forge build --match-path "src/fci-token-vault/storage/CustodianStorage.sol"`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/fci-token-vault/storage/CustodianStorage.sol
git commit -m "feat(004): add CustodianStorage with disjoint diamond slot"
```

---

### Task 2: Define OraclePayoffStorage

**Files:**
- Create: `src/fci-token-vault/storage/OraclePayoffStorage.sol`

- [ ] **Step 1: Write the storage struct and accessor**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";

bytes32 constant ORACLE_PAYOFF_STORAGE_POSITION = keccak256("thetaswap.oracle-payoff");

struct OraclePayoffStorage {
    uint160 sqrtPriceStrike;
    uint160 sqrtPriceHWM;
    uint64  lastHwmTimestamp;   // packed with sqrtPriceHWM in same slot? No — PoolKey is large
    uint256 halfLifeSeconds;
    uint256 expiry;
    bool    settled;
    uint256 longPayoutPerToken; // Q96-scaled
    PoolKey poolKey;
    bool    reactive;
}

error VaultAlreadySettled();
error VaultExpired();
error VaultNotExpired();
error VaultNotSettled();
error VaultAlreadySettledPoke();

function getOraclePayoffStorage() pure returns (OraclePayoffStorage storage s) {
    bytes32 position = ORACLE_PAYOFF_STORAGE_POSITION;
    assembly {
        s.slot := position
    }
}
```

Key decisions:
- Different keccak slot than CustodianStorage — diamond storage isolation
- Mirrors the oracle-dependent fields from old `FciVaultStorage`
- When Model C ships, this entire storage becomes unused — clean removal

- [ ] **Step 2: Verify compilation**

Run: `forge build --match-path "src/fci-token-vault/storage/OraclePayoffStorage.sol"`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/fci-token-vault/storage/OraclePayoffStorage.sol
git commit -m "feat(004): add OraclePayoffStorage with disjoint diamond slot"
```

---

### Task 3: Create ReentrancyLib

**Files:**
- Create: `src/fci-token-vault/modules/dependencies/ReentrancyLib.sol`
- Create: `test/fci-token-vault/unit/ReentrancyLib.t.sol`

- [ ] **Step 1: Write the failing test**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    reentrancyGuardEnter,
    reentrancyGuardExit,
    ReentrancyGuardReentrant
} from "@fci-token-vault/modules/dependencies/ReentrancyLib.sol";

contract ReentrancyTarget {
    function enter() external { reentrancyGuardEnter(); }
    function exit() external { reentrancyGuardExit(); }
    function enterTwice() external {
        reentrancyGuardEnter();
        reentrancyGuardEnter(); // should revert
    }
}

contract ReentrancyLibTest is Test {
    ReentrancyTarget target;

    function setUp() public { target = new ReentrancyTarget(); }

    function test_enter_exit_succeeds() public {
        target.enter();
        target.exit();
    }

    function test_double_enter_reverts() public {
        vm.expectRevert(ReentrancyGuardReentrant.selector);
        target.enterTwice();
    }

    function test_reentry_after_exit_succeeds() public {
        target.enter();
        target.exit();
        target.enter();
        target.exit();
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `forge test --match-contract ReentrancyLibTest -vv`
Expected: FAIL (ReentrancyLib.sol does not exist)

- [ ] **Step 3: Write minimal implementation**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @dev Transient-storage reentrancy guard (EIP-1153).
/// Cheaper than SSTORE-based guards (100 gas vs 5000 gas per enter).
/// Auto-clears at end of transaction.

bytes32 constant REENTRANCY_SLOT = keccak256("thetaswap.reentrancy-guard");

error ReentrancyGuardReentrant();

function reentrancyGuardEnter() {
    bytes32 slot = REENTRANCY_SLOT;
    uint256 locked;
    assembly {
        locked := tload(slot)
    }
    if (locked != 0) revert ReentrancyGuardReentrant();
    assembly {
        tstore(slot, 1)
    }
}

function reentrancyGuardExit() {
    bytes32 slot = REENTRANCY_SLOT;
    assembly {
        tstore(slot, 0)
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `forge test --match-contract ReentrancyLibTest -vv`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/fci-token-vault/modules/dependencies/ReentrancyLib.sol test/fci-token-vault/unit/ReentrancyLib.t.sol
git commit -m "feat(004): add transient-storage reentrancy guard"
```

---

## Chunk 2: CollateralCustodian Module + Interface

### Task 4: Define ICollateralCustodian interface

**Files:**
- Create: `src/fci-token-vault/interfaces/ICollateralCustodian.sol`

- [ ] **Step 1: Write the interface**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @title ICollateralCustodian — permanent vault interface
/// @dev Survives Model B→C transition. Only paired operations (no oracle dependency).
interface ICollateralCustodian {
    /// @notice Deposit USDC, receive equal LONG + SHORT ERC-6909 tokens.
    /// @param amount USDC amount (must be > 0, within depositCap)
    function deposit(uint256 amount) external;

    /// @notice Burn equal LONG + SHORT tokens, receive exact USDC back.
    /// @dev Risk-free exit. No oracle dependency. Always returns exactly `amount` USDC.
    /// @param amount Token amount to redeem (must hold >= amount of both LONG and SHORT)
    function redeemPair(uint256 amount) external;

    /// @notice Preview deposit: returns (longAmount, shortAmount) — always equal to amount.
    function previewDeposit(uint256 amount) external view returns (uint256 longAmount, uint256 shortAmount);

    /// @notice Total USDC deposited and backing all tokens.
    function totalDeposited() external view returns (uint128);

    /// @notice ERC-6909 balance query.
    function balanceOf(address owner, uint256 id) external view returns (uint256);

    event PairedMint(address indexed depositor, uint256 amount);
    event PairedBurn(address indexed redeemer, uint256 amount);
}
```

- [ ] **Step 2: Verify compilation**

Run: `forge build --match-path "src/fci-token-vault/interfaces/ICollateralCustodian.sol"`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/fci-token-vault/interfaces/ICollateralCustodian.sol
git commit -m "feat(004): add ICollateralCustodian permanent interface"
```

---

### Task 5: Define IOraclePayoff interface

**Files:**
- Create: `src/fci-token-vault/interfaces/IOraclePayoff.sol`

- [ ] **Step 1: Write the interface**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @title IOraclePayoff — removable Model B interface
/// @dev Will be replaced when CFMM ships (Model C). See issue #41.
interface IOraclePayoff {
    /// @notice Permissionless HWM update. Reads FCI oracle, applies decay.
    function poke() external;

    /// @notice Settle vault after expiry. Computes final LONG/SHORT payout split.
    function settle() external;

    /// @notice Burn LONG tokens, receive oracle-determined USDC payout.
    /// @param amount LONG token amount to redeem
    function redeemLong(uint256 amount) external;

    /// @notice Burn SHORT tokens, receive oracle-determined USDC payout.
    /// @param amount SHORT token amount to redeem
    function redeemShort(uint256 amount) external;

    /// @notice Preview LONG payout at current oracle state.
    /// @return payout USDC amount per `amount` LONG tokens
    function previewLongPayout(uint256 amount) external view returns (uint256 payout);

    /// @notice Preview SHORT payout at current oracle state.
    /// @return payout USDC amount per `amount` SHORT tokens
    function previewShortPayout(uint256 amount) external view returns (uint256 payout);

    /// @notice Current payoff ratio: (longPerToken, shortPerToken) in Q96.
    /// @dev longPerToken + shortPerToken = Q96 (conservation).
    function payoffRatio() external view returns (uint256 longPerToken, uint256 shortPerToken);

    /// @notice Whether the vault has been settled.
    function isSettled() external view returns (bool);

    event OracleSettlement(uint256 longPayoutPerToken, uint160 finalHWM);
    event HWMUpdated(uint160 newHwmSqrtPrice, uint160 currentSqrtPrice);
    event RedeemLong(address indexed redeemer, uint256 amount, uint256 payout);
    event RedeemShort(address indexed redeemer, uint256 amount, uint256 payout);
}
```

- [ ] **Step 2: Verify compilation**

Run: `forge build --match-path "src/fci-token-vault/interfaces/IOraclePayoff.sol"`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/fci-token-vault/interfaces/IOraclePayoff.sol
git commit -m "feat(004): add IOraclePayoff removable interface (Model B)"
```

---

### Task 6: Implement CollateralCustodianMod

**Files:**
- Create: `src/fci-token-vault/modules/CollateralCustodianMod.sol`
- Create: `test/fci-token-vault/unit/CollateralCustodianMod.t.sol`

- [ ] **Step 1: Write the failing test**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    custodianDeposit,
    custodianRedeemPair,
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {getERC6909Storage} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";

uint256 constant LONG = 0;
uint256 constant SHORT = 1;

contract CustodianModCaller {
    function doDeposit(address depositor, uint256 amount) external {
        custodianDeposit(depositor, amount);
    }
    function doRedeemPair(address redeemer, uint256 amount) external {
        custodianRedeemPair(redeemer, amount);
    }
    function initStorage(address collateral, uint128 cap) external {
        CustodianStorage storage cs = getCustodianStorage();
        cs.collateralToken = collateral;
        cs.depositCap = cap;
    }
}

contract CollateralCustodianModTest is Test {
    CustodianModCaller caller;
    address alice = makeAddr("alice");

    function setUp() public {
        caller = new CustodianModCaller();
        caller.initStorage(address(1), 0); // no cap
    }

    /// @dev INV-001: deposit mints equal LONG + SHORT
    function test_deposit_mints_equal_pair() public {
        caller.doDeposit(alice, 100e6);
        assertEq(getERC6909Storage().balanceOf[alice][LONG], 100e6);
        assertEq(getERC6909Storage().balanceOf[alice][SHORT], 100e6);
    }

    /// @dev INV-002: deposit increases totalDeposits
    function test_deposit_increases_totalDeposits() public {
        caller.doDeposit(alice, 100e6);
        assertEq(getCustodianStorage().totalDeposits, 100e6);
    }

    /// @dev INV-003: redeemPair burns equal LONG + SHORT
    function test_redeemPair_burns_pair() public {
        caller.doDeposit(alice, 100e6);
        caller.doRedeemPair(alice, 100e6);
        assertEq(getERC6909Storage().balanceOf[alice][LONG], 0);
        assertEq(getERC6909Storage().balanceOf[alice][SHORT], 0);
    }

    /// @dev INV-004: redeemPair decreases totalDeposits by exact amount
    function test_redeemPair_decreases_totalDeposits() public {
        caller.doDeposit(alice, 100e6);
        caller.doRedeemPair(alice, 60e6);
        assertEq(getCustodianStorage().totalDeposits, 40e6);
    }

    /// @dev INV-005: zero amount reverts
    function test_deposit_zero_reverts() public {
        vm.expectRevert();
        caller.doDeposit(alice, 0);
    }

    function test_redeemPair_zero_reverts() public {
        vm.expectRevert();
        caller.doRedeemPair(alice, 0);
    }

    /// @dev INV-006: deposit exceeding cap reverts
    function test_deposit_exceeds_cap_reverts() public {
        caller.initStorage(address(1), 50e6); // cap at 50
        vm.expectRevert();
        caller.doDeposit(alice, 100e6);
    }
}
```

Note: This test calls module functions directly (not through a facet) — no collateral transfers, just state changes. The facet layer handles CEI ordering with real USDC.

- [ ] **Step 2: Run test to verify it fails**

Run: `forge test --match-contract CollateralCustodianModTest -vv`
Expected: FAIL (CollateralCustodianMod.sol does not exist)

- [ ] **Step 3: Write minimal implementation**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    getCustodianStorage,
    CustodianStorage,
    DepositCapExceeded,
    ZeroAmount
} from "@fci-token-vault/storage/CustodianStorage.sol";

import {
    erc6909Mint,
    erc6909Burn
} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";

import {SafeCastLib} from "solady/utils/SafeCastLib.sol";

uint256 constant LONG = 0;
uint256 constant SHORT = 1;

/// @dev Deposit collateral and receive equal LONG + SHORT tokens.
/// Collateral transfer must happen BEFORE calling this (CEI: facet handles transfer).
/// Panoptic pattern: internal tracking via totalDeposits, never balanceOf.
function custodianDeposit(address depositor, uint256 amount) {
    if (amount == 0) revert ZeroAmount();

    CustodianStorage storage cs = getCustodianStorage();

    // SafeCastLib.toUint128 reverts on overflow — prevents silent truncation
    uint128 amount128 = SafeCastLib.toUint128(amount);
    uint128 newTotal = cs.totalDeposits + amount128;
    if (cs.depositCap > 0 && newTotal > cs.depositCap) revert DepositCapExceeded();

    cs.totalDeposits = newTotal;

    // Atomic paired mint — supply parity enforced by construction
    erc6909Mint(depositor, LONG, amount);
    erc6909Mint(depositor, SHORT, amount);
}

/// @dev Burn equal LONG + SHORT tokens and mark collateral as available for return.
/// Collateral transfer must happen AFTER calling this (CEI: facet handles transfer).
/// Risk-free exit: always returns exactly `amount` USDC regardless of oracle state.
function custodianRedeemPair(address redeemer, uint256 amount) {
    if (amount == 0) revert ZeroAmount();

    CustodianStorage storage cs = getCustodianStorage();

    // Burn both sides — reverts if insufficient balance (ERC6909Lib checks)
    erc6909Burn(redeemer, LONG, amount);
    erc6909Burn(redeemer, SHORT, amount);

    cs.totalDeposits -= SafeCastLib.toUint128(amount);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `forge test --match-contract CollateralCustodianModTest -vv`
Expected: PASS (7 tests)

- [ ] **Step 5: Run all existing tests to verify no regression**

Run: `forge test --match-path "test/fci-token-vault/**" -vv`
Expected: PASS (36 existing + 7 new = 43 tests)

- [ ] **Step 6: Commit**

```bash
git add src/fci-token-vault/modules/CollateralCustodianMod.sol test/fci-token-vault/unit/CollateralCustodianMod.t.sol
git commit -m "feat(004): add CollateralCustodianMod — permanent paired mint/burn"
```

---

## Chunk 3: OraclePayoff Module

### Task 7: Implement OraclePayoffMod

**Files:**
- Create: `src/fci-token-vault/modules/OraclePayoffMod.sol`
- Create: `test/fci-token-vault/unit/OraclePayoffMod.t.sol`

- [ ] **Step 1: Write the failing test**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    oraclePoke,
    oracleSettle,
    oracleRedeemLong,
    oracleRedeemShort,
    getOraclePayoffStorage,
    OraclePayoffStorage
} from "@fci-token-vault/modules/OraclePayoffMod.sol";
import {
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/storage/CustodianStorage.sol";
import {custodianDeposit} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {getERC6909Storage} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";

uint256 constant LONG = 0;
uint256 constant SHORT = 1;

contract OraclePayoffModCaller {
    function doPoke() external returns (uint160) { return oraclePoke(); }
    function doSettle() external { oracleSettle(); }
    function doRedeemLong(address r, uint256 a) external returns (uint256) { return oracleRedeemLong(r, a); }
    function doRedeemShort(address r, uint256 a) external returns (uint256) { return oracleRedeemShort(r, a); }
}

contract OraclePayoffModTest is Test {
    OraclePayoffModCaller caller;
    address alice = makeAddr("alice");

    function setUp() public {
        caller = new OraclePayoffModCaller();
        // Init custodian storage
        CustodianStorage storage cs = getCustodianStorage();
        cs.collateralToken = address(1);
        // Init oracle storage
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceStrike = uint160(SqrtPriceLibrary.Q96); // strike = 1.0
        os.halfLifeSeconds = 14 days;
        os.expiry = block.timestamp + 30 days;
        os.lastHwmTimestamp = uint64(block.timestamp);
    }

    function test_settle_reverts_before_expiry() public {
        vm.expectRevert();
        caller.doSettle();
    }

    function test_settle_after_expiry_sets_settled() public {
        // Set HWM above strike
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceHWM = uint160(SqrtPriceLibrary.Q96) * 2;
        os.lastHwmTimestamp = uint64(os.expiry - 1);

        vm.warp(os.expiry);
        caller.doSettle();

        assertTrue(os.settled);
        assertGt(os.longPayoutPerToken, 0);
    }

    function test_redeemLong_burns_long_only() public {
        // Setup: deposit, set HWM, settle
        custodianDeposit(alice, 100e6);
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceHWM = uint160(SqrtPriceLibrary.Q96) * 2;
        os.lastHwmTimestamp = uint64(os.expiry - 1);
        vm.warp(os.expiry);
        caller.doSettle();

        caller.doRedeemLong(alice, 100e6);

        // LONG burned, SHORT untouched
        assertEq(getERC6909Storage().balanceOf[alice][LONG], 0);
        assertEq(getERC6909Storage().balanceOf[alice][SHORT], 100e6);
    }

    function test_redeemShort_burns_short_only() public {
        custodianDeposit(alice, 100e6);
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceHWM = uint160(SqrtPriceLibrary.Q96) * 2;
        os.lastHwmTimestamp = uint64(os.expiry - 1);
        vm.warp(os.expiry);
        caller.doSettle();

        caller.doRedeemShort(alice, 100e6);

        assertEq(getERC6909Storage().balanceOf[alice][LONG], 100e6);
        assertEq(getERC6909Storage().balanceOf[alice][SHORT], 0);
    }

    function test_redeemLong_plus_redeemShort_eq_deposit() public {
        custodianDeposit(alice, 100e6);
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceHWM = uint160(SqrtPriceLibrary.Q96) * 2;
        os.lastHwmTimestamp = uint64(os.expiry - 1);
        vm.warp(os.expiry);
        caller.doSettle();

        // Module now returns payout directly
        uint256 longPayout = caller.doRedeemLong(alice, 50e6);
        uint256 shortPayout = caller.doRedeemShort(alice, 50e6);

        // Conservation: long + short = deposit (rounding dust stays in vault)
        assertLe(longPayout + shortPayout, 50e6);
        assertGe(longPayout + shortPayout, 50e6 - 1); // at most 1 wei dust
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `forge test --match-contract OraclePayoffModTest -vv`
Expected: FAIL (OraclePayoffMod.sol does not exist)

- [ ] **Step 3: Write minimal implementation**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    getOraclePayoffStorage,
    OraclePayoffStorage,
    VaultAlreadySettled,
    VaultExpired,
    VaultNotExpired,
    VaultNotSettled,
    VaultAlreadySettledPoke
} from "@fci-token-vault/storage/OraclePayoffStorage.sol";

import {
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/storage/CustodianStorage.sol";

import {
    erc6909Burn
} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";

import {
    lookbackPayoffX96,
    applyDecay,
    updateHWM,
    deltaPlusToSqrtPriceX96
} from "@fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol";

import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {SafeCastLib} from "solady/utils/SafeCastLib.sol";

import {ZeroAmount} from "@fci-token-vault/storage/CustodianStorage.sol";

uint256 constant LONG = 0;
uint256 constant SHORT = 1;

/// @dev Read FCI oracle, apply decay, update HWM. Permissionless.
/// Returns currentSqrtPrice so the facet can emit it alongside the new HWM.
function oraclePoke() returns (uint160 currentSqrtPrice) {
    OraclePayoffStorage storage os = getOraclePayoffStorage();
    if (os.settled) revert VaultAlreadySettledPoke();

    uint128 deltaPlus = IFeeConcentrationIndex(address(os.poolKey.hooks))
        .getDeltaPlus(os.poolKey, os.reactive);

    uint256 dt = block.timestamp - os.lastHwmTimestamp;
    uint160 decayed = applyDecay(os.sqrtPriceHWM, dt, os.halfLifeSeconds);

    if (deltaPlus > 0) {
        currentSqrtPrice = deltaPlusToSqrtPriceX96(deltaPlus);
        os.sqrtPriceHWM = updateHWM(decayed, currentSqrtPrice);
    } else {
        currentSqrtPrice = 0;
        os.sqrtPriceHWM = decayed;
    }
    os.lastHwmTimestamp = uint64(block.timestamp);
}

/// @dev Settle after expiry. Computes final LONG payout from HWM vs strike.
function oracleSettle() {
    OraclePayoffStorage storage os = getOraclePayoffStorage();
    if (os.settled) revert VaultAlreadySettled();
    if (block.timestamp < os.expiry) revert VaultNotExpired();

    uint256 dt = block.timestamp - os.lastHwmTimestamp;
    uint160 decayedHWM = applyDecay(os.sqrtPriceHWM, dt, os.halfLifeSeconds);

    os.longPayoutPerToken = lookbackPayoffX96(decayedHWM, os.sqrtPriceStrike);
    os.settled = true;
}

/// @dev Burn LONG tokens. Returns computed payout for facet to transfer.
/// Rounds DOWN (mulDiv truncates — favors vault).
/// totalDeposits decremented by payout, not token amount — preserves collateral
/// backing for outstanding SHORT tokens.
function oracleRedeemLong(address redeemer, uint256 amount) returns (uint256 payout) {
    OraclePayoffStorage storage os = getOraclePayoffStorage();
    if (!os.settled) revert VaultNotSettled();
    if (amount == 0) revert ZeroAmount();

    payout = FixedPointMathLib.mulDiv(amount, os.longPayoutPerToken, SqrtPriceLibrary.Q96);

    erc6909Burn(redeemer, LONG, amount);

    CustodianStorage storage cs = getCustodianStorage();
    cs.totalDeposits -= SafeCastLib.toUint128(payout);
}

/// @dev Burn SHORT tokens. Returns computed payout for facet to transfer.
/// Payout = amount - longPortion. Rounds DOWN on longPortion, so SHORT gets ceiling.
/// totalDeposits decremented by payout, not token amount.
function oracleRedeemShort(address redeemer, uint256 amount) returns (uint256 payout) {
    OraclePayoffStorage storage os = getOraclePayoffStorage();
    if (!os.settled) revert VaultNotSettled();
    if (amount == 0) revert ZeroAmount();

    uint256 longPortion = FixedPointMathLib.mulDiv(amount, os.longPayoutPerToken, SqrtPriceLibrary.Q96);
    payout = amount - longPortion;

    erc6909Burn(redeemer, SHORT, amount);

    CustodianStorage storage cs = getCustodianStorage();
    cs.totalDeposits -= SafeCastLib.toUint128(payout);
}
```

Note: `oracleRedeemLong`/`oracleRedeemShort` burn tokens and update `totalDeposits`, but do NOT transfer USDC. The facet layer computes payout amounts and handles CEI-ordered transfers.

- [ ] **Step 4: Run test to verify it passes**

Run: `forge test --match-contract OraclePayoffModTest -vv`
Expected: PASS (6 tests)

- [ ] **Step 5: Run all vault tests**

Run: `forge test --match-path "test/fci-token-vault/**" -vv`
Expected: PASS (all existing + new)

- [ ] **Step 6: Commit**

```bash
git add src/fci-token-vault/modules/OraclePayoffMod.sol test/fci-token-vault/unit/OraclePayoffMod.t.sol
git commit -m "feat(004): add OraclePayoffMod — removable Model B oracle logic"
```

---

## Chunk 4: Facets + ERC-20 Wrapper

### Task 8: Implement CollateralCustodianFacet

**Files:**
- Create: `src/fci-token-vault/facets/CollateralCustodianFacet.sol`

- [ ] **Step 1: Write the facet**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    custodianDeposit,
    custodianRedeemPair
} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/storage/CustodianStorage.sol";
import {
    getERC6909Storage,
    ERC6909Storage
} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";
import {
    reentrancyGuardEnter,
    reentrancyGuardExit
} from "@fci-token-vault/modules/dependencies/ReentrancyLib.sol";
import {SafeTransferLib} from "solady/utils/SafeTransferLib.sol";

/// @title CollateralCustodianFacet — permanent diamond facet
/// @dev Handles USDC custody with CEI ordering. Survives Model B→C transition.
contract CollateralCustodianFacet {
    event PairedMint(address indexed depositor, uint256 amount);
    event PairedBurn(address indexed redeemer, uint256 amount);

    /// @notice Deposit USDC, receive equal LONG + SHORT tokens.
    /// CEI: transfer USDC in → update state → mint tokens.
    function deposit(uint256 amount) external {
        reentrancyGuardEnter();

        CustodianStorage storage cs = getCustodianStorage();

        // C: checks happen inside custodianDeposit (zero, cap)
        // E+I: transfer collateral FIRST (Panoptic pattern: get money before promises)
        SafeTransferLib.safeTransferFrom(cs.collateralToken, msg.sender, address(this), amount);

        // E: update internal state + mint tokens
        custodianDeposit(msg.sender, amount);

        emit PairedMint(msg.sender, amount);
        reentrancyGuardExit();
    }

    /// @notice Burn equal LONG + SHORT, receive exact USDC back.
    /// CEI: burn tokens + update state → transfer USDC out.
    function redeemPair(uint256 amount) external {
        reentrancyGuardEnter();

        CustodianStorage storage cs = getCustodianStorage();

        // E: burn tokens + update state
        custodianRedeemPair(msg.sender, amount);

        // I: transfer collateral LAST
        SafeTransferLib.safeTransfer(cs.collateralToken, msg.sender, amount);

        emit PairedBurn(msg.sender, amount);
        reentrancyGuardExit();
    }

    /// @notice Preview deposit amounts (always 1:1).
    function previewDeposit(uint256 amount) external pure returns (uint256, uint256) {
        return (amount, amount);
    }

    /// @notice Total USDC backing all tokens.
    function totalDeposited() external view returns (uint128) {
        return getCustodianStorage().totalDeposits;
    }

    /// @notice ERC-6909 balance query.
    function balanceOf(address owner, uint256 id) external view returns (uint256) {
        return getERC6909Storage().balanceOf[owner][id];
    }
}
```

- [ ] **Step 2: Verify compilation**

Run: `forge build --match-path "src/fci-token-vault/facets/CollateralCustodianFacet.sol"`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/fci-token-vault/facets/CollateralCustodianFacet.sol
git commit -m "feat(004): add CollateralCustodianFacet with CEI + reentrancy guard"
```

---

### Task 9: Implement OraclePayoffFacet

**Files:**
- Create: `src/fci-token-vault/facets/OraclePayoffFacet.sol`

- [ ] **Step 1: Write the facet**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    oraclePoke,
    oracleSettle,
    oracleRedeemLong,
    oracleRedeemShort
} from "@fci-token-vault/modules/OraclePayoffMod.sol";
import {
    getOraclePayoffStorage,
    OraclePayoffStorage,
    VaultNotSettled
} from "@fci-token-vault/storage/OraclePayoffStorage.sol";
import {
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/storage/CustodianStorage.sol";
import {
    reentrancyGuardEnter,
    reentrancyGuardExit
} from "@fci-token-vault/modules/dependencies/ReentrancyLib.sol";
import {SafeTransferLib} from "solady/utils/SafeTransferLib.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";

uint256 constant Q96 = SqrtPriceLibrary.Q96;

/// @title OraclePayoffFacet — removable Model B diamond facet
/// @dev Handles oracle-dependent operations. Removed when CFMM ships (issue #41).
contract OraclePayoffFacet {
    event OracleSettlement(uint256 longPayoutPerToken, uint160 finalHWM);
    event HWMUpdated(uint160 newHwmSqrtPrice, uint160 currentSqrtPrice);
    event RedeemLong(address indexed redeemer, uint256 amount, uint256 payout);
    event RedeemShort(address indexed redeemer, uint256 amount, uint256 payout);

    function poke() external {
        uint160 currentSqrtPrice = oraclePoke();
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        emit HWMUpdated(os.sqrtPriceHWM, currentSqrtPrice);
    }

    function settle() external {
        oracleSettle();
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        emit OracleSettlement(os.longPayoutPerToken, os.sqrtPriceHWM);
    }

    /// @notice Burn LONG tokens, receive USDC payout.
    /// CEI: burn tokens + update totalDeposits → transfer USDC out.
    /// Module computes payout internally (mulDiv rounds DOWN, favors vault).
    function redeemLong(uint256 amount) external {
        reentrancyGuardEnter();

        // E: burn LONG, compute payout, update totalDeposits (all in module)
        uint256 payout = oracleRedeemLong(msg.sender, amount);

        // I: transfer payout
        if (payout > 0) {
            CustodianStorage storage cs = getCustodianStorage();
            SafeTransferLib.safeTransfer(cs.collateralToken, msg.sender, payout);
        }

        emit RedeemLong(msg.sender, amount, payout);
        reentrancyGuardExit();
    }

    /// @notice Burn SHORT tokens, receive USDC payout.
    /// CEI: burn tokens + update totalDeposits → transfer USDC out.
    /// Module computes payout internally (amount - longPortion).
    function redeemShort(uint256 amount) external {
        reentrancyGuardEnter();

        // E: burn SHORT, compute payout, update totalDeposits (all in module)
        uint256 payout = oracleRedeemShort(msg.sender, amount);

        // I: transfer payout
        if (payout > 0) {
            CustodianStorage storage cs = getCustodianStorage();
            SafeTransferLib.safeTransfer(cs.collateralToken, msg.sender, payout);
        }

        emit RedeemShort(msg.sender, amount, payout);
        reentrancyGuardExit();
    }

    /// @notice Preview LONG payout. Rounds DOWN.
    function previewLongPayout(uint256 amount) external view returns (uint256) {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        if (!os.settled) revert VaultNotSettled();
        return FixedPointMathLib.mulDiv(amount, os.longPayoutPerToken, Q96);
    }

    /// @notice Preview SHORT payout. Rounds DOWN.
    function previewShortPayout(uint256 amount) external view returns (uint256) {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        if (!os.settled) revert VaultNotSettled();
        uint256 longPortion = FixedPointMathLib.mulDiv(amount, os.longPayoutPerToken, Q96);
        return amount - longPortion;
    }

    /// @notice Current payoff ratio (Q96-scaled).
    function payoffRatio() external view returns (uint256 longPerToken, uint256 shortPerToken) {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        if (!os.settled) revert VaultNotSettled();
        longPerToken = os.longPayoutPerToken;
        shortPerToken = Q96 - os.longPayoutPerToken;
    }

    function isSettled() external view returns (bool) {
        return getOraclePayoffStorage().settled;
    }
}
```

- [ ] **Step 2: Verify compilation**

Run: `forge build --match-path "src/fci-token-vault/facets/OraclePayoffFacet.sol"`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/fci-token-vault/facets/OraclePayoffFacet.sol
git commit -m "feat(004): add OraclePayoffFacet — removable Model B facet"
```

---

### Task 10: Create ERC-20 Wrapper Facade

**Files:**
- Create: `src/fci-token-vault/tokens/ERC20WrapperFacade.sol`
- Create: `test/fci-token-vault/unit/ERC20WrapperFacade.t.sol`

- [ ] **Step 1: Write the failing test**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    wrap,
    unwrap,
    getWrappedTokenId
} from "@fci-token-vault/tokens/ERC20WrapperFacade.sol";
import {erc6909Mint} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";
import {LibERC20} from "compose/token/ERC20/ERC20/LibERC20.sol";

/// @dev Test caller that delegates to the wrapper free functions.
///      In production, these are diamond facet selectors.
contract WrapperCaller {
    function doWrap(uint256 amount) external { wrap(amount); }
    function doUnwrap(uint256 amount) external { unwrap(amount); }
    function initTokenId(uint256 id) external {
        bytes32 slot = bytes32(uint256(keccak256("thetaswap.erc20-wrapper")));
        assembly { sstore(slot, id) }
    }
}

contract ERC20WrapperFacadeTest is Test {
    WrapperCaller caller;
    address alice = makeAddr("alice");
    uint256 constant TOKEN_ID = 0; // LONG

    function setUp() public {
        caller = new WrapperCaller();
        caller.initTokenId(TOKEN_ID);
        // Init Compose ERC20 storage (name, symbol, decimals)
        // In production this is done via diamond init
    }

    function test_wrap_converts_6909_to_erc20() public {
        erc6909Mint(alice, TOKEN_ID, 100e6);

        vm.prank(alice);
        caller.doWrap(100e6);

        // Check Compose ERC20 balance
        assertEq(LibERC20.getStorage().balanceOf[alice], 100e6);
    }

    function test_unwrap_converts_erc20_to_6909() public {
        erc6909Mint(alice, TOKEN_ID, 100e6);
        vm.prank(alice);
        caller.doWrap(100e6);

        vm.prank(alice);
        caller.doUnwrap(50e6);

        assertEq(LibERC20.getStorage().balanceOf[alice], 50e6);
    }

    function test_wrap_insufficient_6909_reverts() public {
        // Alice has no ERC-6909 tokens
        vm.prank(alice);
        vm.expectRevert();
        caller.doWrap(100e6);
    }
}
```

Note: The test accesses `LibERC20.getStorage().balanceOf[alice]` directly since we're testing free functions, not a full diamond deployment. Full integration with Compose `ERC20Facet` (transfer/approve/allowance) is tested at the diamond level.

- [ ] **Step 2: Run test to verify it fails**

Run: `forge test --match-contract ERC20WrapperFacadeTest -vv`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

The wrapper is a Compose diamond facet that uses `LibERC20` for mint/burn, keeping everything in diamond storage (`keccak256("compose.erc20")`). This means the ERC-20 balance, name, symbol, and decimals all live in the diamond — no separate contract deployment per token.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {LibERC20} from "compose/token/ERC20/ERC20/LibERC20.sol";
import {
    getERC6909Storage,
    ERC6909Storage
} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";

uint256 constant WRAPPER_STORAGE_POSITION_SEED = uint256(keccak256("thetaswap.erc20-wrapper"));

error InsufficientERC6909Balance(address owner, uint256 balance, uint256 needed, uint256 tokenId);

/// @dev Read the wrapped ERC-6909 token ID from diamond storage.
function getWrappedTokenId() pure returns (uint256) {
    // Set during diamond cut — stored as immutable-equivalent in code.
    // For now, use a storage read. Production: clones-with-immutable-args.
    bytes32 slot = bytes32(WRAPPER_STORAGE_POSITION_SEED);
    uint256 id;
    assembly { id := sload(slot) }
    return id;
}

/// @title ERC20WrapperFacade — thin ERC-20 wrapper over ERC-6909 token ID
/// @dev Uses Compose LibERC20 for mint/burn (diamond storage at compose.erc20).
///      Wrapping moves balance from ERC-6909 internal accounting to standard
///      ERC-20 balanceOf visible to external AMMs and protocols.
///      Deploy one instance per (LONG, SHORT) token ID via the diamond.
///      The Compose ERC20Facet handles transfer/approve/allowance externally.
///      This is a contract (not free functions) because it's a diamond facet
///      that needs `external` visibility and `msg.sender` access.
contract ERC20WrapperFacade {
    /// @notice Convert ERC-6909 balance to ERC-20 balance.
    function wrap(uint256 amount) external {
        uint256 tokenId = getWrappedTokenId();
        ERC6909Storage storage s = getERC6909Storage();
        uint256 bal = s.balanceOf[msg.sender][tokenId];
        if (bal < amount) revert InsufficientERC6909Balance(msg.sender, bal, amount, tokenId);
        unchecked { s.balanceOf[msg.sender][tokenId] = bal - amount; }
        LibERC20.mint(msg.sender, amount);
    }

    /// @notice Convert ERC-20 balance back to ERC-6909 balance.
    function unwrap(uint256 amount) external {
        LibERC20.burn(msg.sender, amount);
        uint256 tokenId = getWrappedTokenId();
        getERC6909Storage().balanceOf[msg.sender][tokenId] += amount;
    }
}
```

Note: The Compose `ERC20Facet` (transfer/approve/allowance) is added to the diamond alongside this wrapper. Together they provide full ERC-20 functionality. The `LibERC20.mint/burn` calls write to `keccak256("compose.erc20")` storage, while ERC-6909 writes to `keccak256("compose.erc6909")` storage — disjoint slots.

- [ ] **Step 4: Run test to verify it passes**

Run: `forge test --match-contract ERC20WrapperFacadeTest -vv`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/fci-token-vault/tokens/ERC20WrapperFacade.sol test/fci-token-vault/unit/ERC20WrapperFacade.t.sol
git commit -m "feat(004): add ERC20WrapperFacade — thin ERC-20 over ERC-6909"
```

---

## Chunk 5: Invariant Fuzz Tests

### Task 11: Handler-based invariant fuzz testing

**Files:**
- Create: `test/fci-token-vault/fuzz/CustodianHandler.sol`
- Create: `test/fci-token-vault/fuzz/CustodianInvariant.fuzz.t.sol`

This is the most critical testing task. Adapted from Panoptic's invariant patterns and the 13 invariants from `vault-standards-research.md`.

- [ ] **Step 1: Write the handler contract**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    custodianDeposit,
    custodianRedeemPair
} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/storage/CustodianStorage.sol";
import {getERC6909Storage} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";

uint256 constant LONG = 0;
uint256 constant SHORT = 1;

/// @dev Handler for invariant fuzzing. Tracks ghost variables for cross-check.
contract CustodianHandler is Test {
    // Ghost variables — shadow the real state for invariant checking
    uint256 public ghost_totalMinted;
    uint256 public ghost_totalRedeemed;
    address[] public actors;

    constructor() {
        // Bounded actor set for multi-user fuzzing
        actors.push(makeAddr("actor0"));
        actors.push(makeAddr("actor1"));
        actors.push(makeAddr("actor2"));
    }

    function deposit(uint256 actorSeed, uint256 amount) external {
        address actor = actors[actorSeed % actors.length];
        amount = bound(amount, 1, 1_000_000e6); // 1 wei to 1M USDC

        custodianDeposit(actor, amount);
        ghost_totalMinted += amount;
    }

    function redeemPair(uint256 actorSeed, uint256 amount) external {
        address actor = actors[actorSeed % actors.length];
        uint256 longBal = getERC6909Storage().balanceOf[actor][LONG];
        uint256 shortBal = getERC6909Storage().balanceOf[actor][SHORT];
        uint256 maxRedeem = longBal;
        if (shortBal < maxRedeem) maxRedeem = shortBal;

        if (maxRedeem == 0) return; // skip if nothing to redeem
        amount = bound(amount, 1, maxRedeem);

        custodianRedeemPair(actor, amount);
        ghost_totalRedeemed += amount;
    }

    function actorCount() external view returns (uint256) {
        return actors.length;
    }
}
```

- [ ] **Step 2: Write the invariant test contract**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {CustodianHandler, LONG, SHORT} from "./CustodianHandler.sol";
import {
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/storage/CustodianStorage.sol";
import {getERC6909Storage} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";

contract CustodianInvariantTest is Test {
    CustodianHandler handler;

    function setUp() public {
        handler = new CustodianHandler();
        // Init storage
        CustodianStorage storage cs = getCustodianStorage();
        cs.collateralToken = address(1);
        cs.depositCap = 0; // no cap for fuzz

        targetContract(address(handler));
    }

    /// INV-1: totalDeposits == ghost_totalMinted - ghost_totalRedeemed
    function invariant_totalDeposits_matches_ghost() public view {
        uint128 totalDep = getCustodianStorage().totalDeposits;
        uint256 expected = handler.ghost_totalMinted() - handler.ghost_totalRedeemed();
        assertEq(uint256(totalDep), expected);
    }

    /// INV-2: For each actor, LONG balance == SHORT balance
    /// (since only paired operations exist in the custodian)
    function invariant_supply_parity_per_actor() public view {
        for (uint256 i = 0; i < handler.actorCount(); i++) {
            address actor = handler.actors(i);
            uint256 longBal = getERC6909Storage().balanceOf[actor][LONG];
            uint256 shortBal = getERC6909Storage().balanceOf[actor][SHORT];
            assertEq(longBal, shortBal, "LONG != SHORT for actor");
        }
    }

    /// INV-3: Sum of all actor LONG balances == totalDeposits
    function invariant_total_supply_eq_deposits() public view {
        uint256 totalLong;
        for (uint256 i = 0; i < handler.actorCount(); i++) {
            totalLong += getERC6909Storage().balanceOf[handler.actors(i)][LONG];
        }
        assertEq(totalLong, uint256(getCustodianStorage().totalDeposits));
    }

    /// INV-4: totalDeposits never goes negative (uint128 underflow would revert)
    /// This is implicitly tested by the handler not reverting, but explicit check:
    function invariant_totalDeposits_non_negative() public view {
        // uint128 cannot be negative, but verify ghost consistency
        assertGe(handler.ghost_totalMinted(), handler.ghost_totalRedeemed());
    }
}
```

- [ ] **Step 3: Run invariant tests**

Run: `forge test --match-contract CustodianInvariantTest -vv --fuzz-runs 10000`
Expected: PASS (4 invariants hold across 10,000 fuzz sequences)

- [ ] **Step 4: Commit**

```bash
git add test/fci-token-vault/fuzz/CustodianHandler.sol test/fci-token-vault/fuzz/CustodianInvariant.fuzz.t.sol
git commit -m "test(004): add handler-based invariant fuzz tests for custodian (4 invariants)"
```

---

## Chunk 6: Migration — Update Existing Tests + Delete Old Module

### Task 12: Create new CustodianHarness for backward compatibility

**Files:**
- Create: `test/fci-token-vault/helpers/CustodianHarness.sol`

- [ ] **Step 1: Write the harness**

The harness wraps the new modules with the same API shape used by integration tests. Existing integration tests (HedgedVsUnhedged, JitGameWelfareComparison, etc.) call into `FciTokenVaultHarness` which uses the old module. We need a new harness that uses the split modules while keeping the same test-facing API.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    custodianDeposit,
    custodianRedeemPair
} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {
    oraclePoke,
    oracleSettle,
    oracleRedeemLong,
    oracleRedeemShort
} from "@fci-token-vault/modules/OraclePayoffMod.sol";
import {
    getCustodianStorage,
    CustodianStorage
} from "@fci-token-vault/storage/CustodianStorage.sol";
import {
    getOraclePayoffStorage,
    OraclePayoffStorage
} from "@fci-token-vault/storage/OraclePayoffStorage.sol";
import {getERC6909Storage} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";
import {SafeTransferLib} from "solady/utils/SafeTransferLib.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";

/// @dev Test harness composing both new modules. API matches FciTokenVaultHarness
///      for backward compatibility with integration tests.
contract CustodianHarness {
    function harness_deposit(address depositor, uint256 amount) external {
        CustodianStorage storage cs = getCustodianStorage();
        SafeTransferLib.safeTransferFrom(cs.collateralToken, depositor, address(this), amount);
        custodianDeposit(depositor, amount);
    }

    function harness_settle() external {
        oracleSettle();
    }

    function harness_redeem(address redeemer, uint256 amount) external {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        uint256 longPayout = FixedPointMathLib.mulDiv(amount, os.longPayoutPerToken, SqrtPriceLibrary.Q96);
        uint256 shortPayout = amount - longPayout;

        // Burn both sides
        custodianRedeemPair(redeemer, amount);

        CustodianStorage storage cs = getCustodianStorage();
        if (longPayout > 0) {
            SafeTransferLib.safeTransfer(cs.collateralToken, redeemer, longPayout);
        }
        if (shortPayout > 0) {
            SafeTransferLib.safeTransfer(cs.collateralToken, redeemer, shortPayout);
        }
    }

    function harness_poke() external returns (uint160) {
        return oraclePoke();
    }

    function harness_balanceOf(address owner, uint256 id) external view returns (uint256) {
        return getERC6909Storage().balanceOf[owner][id];
    }

    function harness_getVaultStorage() external view returns (
        uint160 sqrtPriceStrike,
        uint160 sqrtPriceHWM,
        uint256 halfLifeSeconds,
        uint256 expiry,
        uint256 totalDeposits,
        uint256 lastHwmTimestamp,
        bool settled,
        uint256 longPayoutPerToken
    ) {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        CustodianStorage storage cs = getCustodianStorage();
        return (
            os.sqrtPriceStrike,
            os.sqrtPriceHWM,
            os.halfLifeSeconds,
            os.expiry,
            uint256(cs.totalDeposits),
            uint256(os.lastHwmTimestamp),
            os.settled,
            os.longPayoutPerToken
        );
    }

    function harness_initVault(
        uint160 sqrtPriceStrike,
        uint256 halfLifeSeconds,
        uint256 expiry,
        PoolKey calldata poolKey,
        bool reactive,
        address collateralToken
    ) external {
        CustodianStorage storage cs = getCustodianStorage();
        cs.collateralToken = collateralToken;

        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceStrike = sqrtPriceStrike;
        os.halfLifeSeconds = halfLifeSeconds;
        os.expiry = expiry;
        os.lastHwmTimestamp = uint64(block.timestamp);
        os.poolKey = poolKey;
        os.reactive = reactive;
    }

    function harness_setHWM(uint160 hwm, uint256 timestamp) external {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceHWM = hwm;
        os.lastHwmTimestamp = uint64(timestamp);
    }

    function harness_getPoolKey() external view returns (PoolKey memory) {
        return getOraclePayoffStorage().poolKey;
    }

    function harness_getReactive() external view returns (bool) {
        return getOraclePayoffStorage().reactive;
    }
}
```

- [ ] **Step 2: Verify compilation**

Run: `forge build --match-path "test/fci-token-vault/helpers/CustodianHarness.sol"`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/helpers/CustodianHarness.sol
git commit -m "test(004): add CustodianHarness composing split modules"
```

---

### Task 13: Migrate FciTokenVaultModTest to new modules

**Files:**
- Modify: `test/fci-token-vault/FciTokenVaultMod.t.sol`

- [ ] **Step 1: Update imports to use CustodianHarness instead of FciTokenVaultHarness**

Change the import and instantiation:
- Replace `FciTokenVaultHarness` with `CustodianHarness`
- Keep all test assertions identical — if they pass, the refactor is behavior-preserving

```diff
-import {FciTokenVaultHarness} from "./helpers/FciTokenVaultHarness.sol";
+import {CustodianHarness} from "./helpers/CustodianHarness.sol";
...
-    FciTokenVaultHarness vault;
+    CustodianHarness vault;
...
-        vault = new FciTokenVaultHarness();
+        vault = new CustodianHarness();
```

- [ ] **Step 2: Run tests to verify no regression**

Run: `forge test --match-contract FciTokenVaultModTest -vv`
Expected: PASS (7 tests, identical assertions)

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/FciTokenVaultMod.t.sol
git commit -m "refactor(004): migrate FciTokenVaultModTest to CustodianHarness"
```

---

### Task 14: Delete old monolithic module

**Files:**
- Delete: `src/fci-token-vault/modules/FciTokenVaultMod.sol`
- Delete: `src/fci-token-vault/FciTokenVaultFacet.sol`
- Delete: `src/fci-token-vault/interfaces/IFciTokenVault.sol`

**IMPORTANT:** Do NOT delete until all tests pass with the new modules. The integration tests (HedgedVsUnhedged, JitGameWelfareComparison, etc.) use `FciTokenVaultHarness` which still imports from the old module. Those tests must be migrated first.

- [ ] **Step 1: Check which files still import the old module**

Run: `grep -r "FciTokenVaultMod\|FciTokenVaultFacet\|IFciTokenVault" test/ src/ --include="*.sol" -l`

Review each file. If integration tests still use the old harness, they must switch to `CustodianHarness` OR the old `FciTokenVaultHarness` must be updated to use the new modules.

- [ ] **Step 2: Update FciTokenVaultHarness to use new modules (if integration tests depend on it)**

The `FciTokenVaultHarness` has extra methods (`harness_pokeEpoch`) used by integration tests that `CustodianHarness` doesn't have yet. Two options:
- (A) Add `harness_pokeEpoch` to `CustodianHarness`
- (B) Update `FciTokenVaultHarness` to import from new modules

Choose (B) to minimize integration test churn. Update `FciTokenVaultHarness` imports to point at the new storage/module files.

- [ ] **Step 3: Run ALL tests**

Run: `forge test --match-path "test/fci-token-vault/**" -vv`
Expected: PASS (all 36+ tests)

- [ ] **Step 4: Delete old files**

```bash
git rm src/fci-token-vault/modules/FciTokenVaultMod.sol
git rm src/fci-token-vault/FciTokenVaultFacet.sol
git rm src/fci-token-vault/interfaces/IFciTokenVault.sol
```

- [ ] **Step 5: Run ALL tests again to confirm clean removal**

Run: `forge test --match-path "test/fci-token-vault/**" -vv`
Expected: PASS

- [ ] **Step 6: Run the full test suite**

Run: `forge test -vv`
Expected: PASS (all 114 Solidity tests)

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor(004): remove old monolithic FciTokenVaultMod — replaced by Custodian + OraclePayoff"
```

---

## Summary

| Chunk | Tasks | What it produces |
|-------|-------|-----------------|
| 1: Storage + Reentrancy | Tasks 1-3 | Disjoint diamond storage slots, transient reentrancy guard |
| 2: Custodian Module | Tasks 4-6 | Permanent interface + module (deposit, redeemPair) |
| 3: OraclePayoff Module | Task 7 | Removable Model B logic (poke, settle, redeemLong/Short) |
| 4: Facets + ERC-20 Wrapper | Tasks 8-10 | Diamond facets with CEI, ERC-20 composability facade |
| 5: Invariant Fuzz Tests | Task 11 | Handler-based fuzz testing (4 invariants, 10K runs) |
| 6: Migration | Tasks 12-14 | Test migration, old module deletion, full suite green |

**Post-plan:** When CFMM ships (issue #41), replace `OraclePayoffFacet` with a trivial facet that only delegates to `CollateralCustodianFacet.redeemPair()`. The custodian, ERC-6909, ERC-20 wrappers, and conservation invariant survive unchanged.
