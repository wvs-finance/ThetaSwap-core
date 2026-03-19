# FCI V2 Admin Upgradeability Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add mutable cross-contract references, fund recovery, and transferable ownership to `UniswapV3Callback` and `UniswapV3Reactive`.

**Architecture:** New `AdminLib.sol` free-function file provides `migrateFunds`. Both contracts switch from `immutable owner` to `LibOwner` (existing module) for transferable ownership. Immutable cross-contract refs (`fci`, `callback`) become storage vars with onlyOwner setters. `service` and `vm` on `UniswapV3Reactive` stay immutable.

**Tech Stack:** Solidity ^0.8.26, forge-std, LibOwner (compose pattern)

**Spec:** `docs/superpowers/specs/2026-03-17-fci-v2-admin-upgradeability-design.md`

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/fee-concentration-index-v2/modules/dependencies/AdminLib.sol` | `migrateFunds` free function + events/errors |
| Modify | `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol` | LibOwner, mutable `fci`, `setFci`, `migrateFunds` |
| Modify | `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol` | LibOwner, mutable `callback`, `setCallback`, `migrateFunds` |
| Create | `test/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.admin.t.sol` | Admin function tests for Callback |
| Create | `test/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.admin.t.sol` | Admin function tests for Reactive |

---

## Task 1: Create `AdminLib.sol`

**Files:**
- Create: `src/fee-concentration-index-v2/modules/dependencies/AdminLib.sol`

- [ ] **Step 1: Write `AdminLib.sol`**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

event FundsMigrated(address indexed to, uint256 amount);

error NoFunds();
error MigrationTransferFailed();

function migrateFunds(address payable to) {
    uint256 balance = address(this).balance;
    if (balance == 0) revert NoFunds();
    (bool success,) = to.call{value: balance}("");
    if (!success) revert MigrationTransferFailed();
    emit FundsMigrated(to, balance);
}
```

- [ ] **Step 2: Verify compilation**

Run: `forge build --match-path "src/fee-concentration-index-v2/modules/dependencies/AdminLib.sol"`
Expected: PASS (no errors)

- [ ] **Step 3: Commit**

```bash
git add src/fee-concentration-index-v2/modules/dependencies/AdminLib.sol
git commit -m "feat(008): add AdminLib free function for migrateFunds"
```

---

## Task 2: Write failing tests for `UniswapV3Callback` admin functions

**Files:**
- Create: `test/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.admin.t.sol`

- [ ] **Step 1: Write the test file**

Test contract deploys `UniswapV3Callback` and tests all admin functions. The constructor signature stays the same: `(address fci_, address callbackProxy_, address rvmId_)`.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {UniswapV3Callback} from
    "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol";
import {OwnerUnauthorizedAccount} from
    "@fee-concentration-index-v2/modules/dependencies/LibOwner.sol";
import {NoFunds, MigrationTransferFailed, FundsMigrated} from
    "@fee-concentration-index-v2/modules/dependencies/AdminLib.sol";

/// @dev Helper contract that rejects ETH — used to test MigrationTransferFailed
contract RejectETH {}

contract UniswapV3CallbackAdminTest is Test {
    UniswapV3Callback callback;

    address owner = address(this);
    address fci = makeAddr("fci");
    address callbackProxy = makeAddr("callbackProxy");
    address rvmId = makeAddr("rvmId");
    address notOwner = makeAddr("notOwner");

    function setUp() public {
        callback = new UniswapV3Callback{value: 1 ether}(fci, callbackProxy, rvmId);
    }

    // ── setFci ──

    function test_setFci_updatesReference() public {
        address newFci = makeAddr("newFci");
        callback.setFci(newFci);
        assertEq(address(callback.fci()), newFci);
    }

    function test_setFci_emitsFciUpdated() public {
        address newFci = makeAddr("newFci");
        vm.expectEmit(true, true, false, false);
        emit UniswapV3Callback.FciUpdated(fci, newFci);
        callback.setFci(newFci);
    }

    function test_setFci_revertsIfNotOwner() public {
        vm.prank(notOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        callback.setFci(makeAddr("newFci"));
    }

    function test_setFci_revertsIfZeroAddress() public {
        vm.expectRevert(UniswapV3Callback.ZeroAddress.selector);
        callback.setFci(address(0));
    }

    // ── migrateFunds ──

    function test_migrateFunds_sendsAllETH() public {
        address payable recipient = payable(makeAddr("recipient"));
        uint256 balanceBefore = address(callback).balance;
        assertEq(balanceBefore, 1 ether);

        callback.migrateFunds(recipient);

        assertEq(address(callback).balance, 0);
        assertEq(recipient.balance, 1 ether);
    }

    function test_migrateFunds_emitsFundsMigrated() public {
        address payable recipient = payable(makeAddr("recipient"));
        vm.expectEmit(true, false, false, true);
        // FundsMigrated is a file-level event from AdminLib, import directly
        emit FundsMigrated(recipient, 1 ether);
        callback.migrateFunds(recipient);
    }

    function test_migrateFunds_revertsIfNotOwner() public {
        vm.prank(notOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        callback.migrateFunds(payable(makeAddr("recipient")));
    }

    function test_migrateFunds_revertsIfNoFunds() public {
        // Drain funds first
        callback.migrateFunds(payable(makeAddr("drain")));
        vm.expectRevert(NoFunds.selector);
        callback.migrateFunds(payable(makeAddr("recipient")));
    }

    function test_migrateFunds_revertsIfRecipientRejectsETH() public {
        RejectETH rejector = new RejectETH();
        vm.expectRevert(MigrationTransferFailed.selector);
        callback.migrateFunds(payable(address(rejector)));
    }

    // ── transferOwnership ──

    function test_transferOwnership_updatesOwner() public {
        address newOwner = makeAddr("newOwner");
        callback.transferOwnership(newOwner);

        // Old owner can no longer call admin functions
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        callback.setFci(makeAddr("x"));

        // New owner can
        vm.prank(newOwner);
        callback.setFci(makeAddr("x"));
    }

    function test_transferOwnership_revertsIfNotOwner() public {
        vm.prank(notOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        callback.transferOwnership(notOwner);
    }

    function test_transferOwnership_toZeroRenouncesOwnership() public {
        // LibOwner allows transfer to address(0) — permanently renounces ownership
        callback.transferOwnership(address(0));
        // All admin functions are now permanently locked
        vm.expectRevert(); // OwnerAlreadyRenounced
        callback.transferOwnership(makeAddr("x"));
    }

    // ── existing admin: setRvmId still works ──

    function test_setRvmId_stillWorksWithLibOwner() public {
        address newRvm = makeAddr("newRvm");
        callback.setRvmId(newRvm);
        assertEq(callback.rvmId(), newRvm);
    }

    function test_setRvmId_revertsIfNotOwner() public {
        vm.prank(notOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        callback.setRvmId(makeAddr("x"));
    }

    // ── existing admin: setAuthorized still works ──

    function test_setAuthorized_stillWorksWithLibOwner() public {
        address newCaller = makeAddr("newCaller");
        callback.setAuthorized(newCaller, true);
        assertTrue(callback.authorizedCallers(newCaller));
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `forge test --match-path "test/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.admin.t.sol" -vv`
Expected: FAIL — compilation errors because `UniswapV3Callback` doesn't have `setFci`, `migrateFunds`, `transferOwnership`, `fci()` getter, or `FciUpdated`/`FundsMigrated`/`ZeroAddress` yet.

- [ ] **Step 3: Commit failing tests**

```bash
git add test/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.admin.t.sol
git commit -m "test(008): add failing admin tests for UniswapV3Callback"
```

---

## Task 3: Implement `UniswapV3Callback` admin changes

**Files:**
- Modify: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol`

The full updated contract. Key changes from current:
- Import `LibOwner` functions: `initOwner`, `requireOwner`, `transferOwnership`
- Import `migrateFunds` from `AdminLib`
- `IHooks immutable fci` → `IHooks public fci` (storage)
- `address immutable owner` → removed (LibOwner handles it)
- `error OnlyOwner()` → removed (LibOwner's `OwnerUnauthorizedAccount()`)
- New: `setFci(address)`, `migrateFunds(address payable)`, `transferOwnership(address)`
- New: `error ZeroAddress()`, `event FciUpdated`
- `setRvmId` and `setAuthorized` guards change from `if (msg.sender != owner)` to `requireOwner()`

- [ ] **Step 1: Update `UniswapV3Callback.sol`**

Replace the full contract. The changes are:

1. Add imports at top:
```solidity
import {initOwner, requireOwner, transferOwnership} from "../../modules/dependencies/LibOwner.sol";
import {migrateFunds, FundsMigrated} from "../../modules/dependencies/AdminLib.sol";
```

2. Replace state variables:
```solidity
// Before:
IHooks immutable fci;
address public rvmId;
address immutable owner;

// After:
IHooks public fci;
address public rvmId;
```

3. Replace errors:
```solidity
// Remove: error OnlyOwner();
// Add:
error ZeroAddress();
```

4. Add events:
```solidity
event FciUpdated(address indexed oldFci, address indexed newFci);
```

5. Update constructor:
```solidity
constructor(address fci_, address callbackProxy_, address rvmId_) payable {
    fci = IHooks(fci_);
    initOwner(msg.sender);
    rvmId = rvmId_;
    authorizedCallers[callbackProxy_] = true;
}
```

6. Add new admin functions:
```solidity
function setFci(address newFci) external {
    requireOwner();
    if (newFci == address(0)) revert ZeroAddress();
    address oldFci = address(fci);
    fci = IHooks(newFci);
    emit FciUpdated(oldFci, newFci);
}

function migrateFunds(address payable to) external {
    requireOwner();
    migrateFunds(to);
}

function transferOwnership(address newOwner) external {
    requireOwner();
    transferOwnership(newOwner);
}
```

Note: `migrateFunds` and `transferOwnership` name-shadow the free function imports. Use explicit qualified calls if the compiler complains — wrap as:

```solidity
import {migrateFunds as _migrateFunds, FundsMigrated} from "../../modules/dependencies/AdminLib.sol";
import {initOwner, requireOwner, transferOwnership as _transferOwnership} from "../../modules/dependencies/LibOwner.sol";
```

Then:
```solidity
function migrateFunds(address payable to) external {
    requireOwner();
    _migrateFunds(to);
}

function transferOwnership(address newOwner) external {
    requireOwner();
    _transferOwnership(newOwner);
}
```

7. Update `setRvmId` and `setAuthorized` guards:
```solidity
// Before: if (msg.sender != owner) revert OnlyOwner();
// After:  requireOwner();
```

- [ ] **Step 2: Verify compilation**

Run: `forge build --match-path "src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol"`
Expected: PASS

- [ ] **Step 3: Run admin tests**

Run: `forge test --match-path "test/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.admin.t.sol" -vv`
Expected: ALL PASS

- [ ] **Step 4: Run existing tests to check for regressions**

Run: `forge test --match-path "test/fee-concentration-index-v2/**" -vv`
Expected: ALL PASS (no regressions)

- [ ] **Step 5: Commit**

```bash
git add src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol
git commit -m "feat(008): add admin upgradeability to UniswapV3Callback"
```

---

## Task 4: Write failing tests for `UniswapV3Reactive` admin functions

**Files:**
- Create: `test/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.admin.t.sol`

- [ ] **Step 1: Write the test file**

The existing `UniswapV3ReactiveDebug.t.sol:23` shows how to set up the SystemContract mock. Reuse that pattern.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {UniswapV3Reactive} from
    "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol";
import {OwnerUnauthorizedAccount} from
    "@fee-concentration-index-v2/modules/dependencies/LibOwner.sol";
import {NoFunds, MigrationTransferFailed, FundsMigrated} from
    "@fee-concentration-index-v2/modules/dependencies/AdminLib.sol";

/// @dev Helper contract that rejects ETH — used to test MigrationTransferFailed
contract RejectETH {}

contract UniswapV3ReactiveAdminTest is Test {
    UniswapV3Reactive reactive;

    address owner = address(this);
    address callbackAddr = makeAddr("callback");
    address notOwner = makeAddr("notOwner");

    function setUp() public {
        // Mock SystemContract so constructor doesn't revert
        address systemContract = 0x0000000000000000000000000000000000fffFfF;
        vm.etch(systemContract, hex"00");
        vm.mockCall(systemContract, bytes(""), abi.encode(true));

        reactive = new UniswapV3Reactive{value: 1 ether}(callbackAddr);
    }

    // ── setCallback ──

    function test_setCallback_updatesReference() public {
        address newCallback = makeAddr("newCallback");
        reactive.setCallback(newCallback);
        assertEq(reactive.callback(), newCallback);
    }

    function test_setCallback_emitsCallbackUpdated() public {
        address newCallback = makeAddr("newCallback");
        vm.expectEmit(true, true, false, false);
        emit UniswapV3Reactive.CallbackUpdated(callbackAddr, newCallback);
        reactive.setCallback(newCallback);
    }

    function test_setCallback_revertsIfNotOwner() public {
        vm.prank(notOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        reactive.setCallback(makeAddr("newCallback"));
    }

    function test_setCallback_revertsIfZeroAddress() public {
        vm.expectRevert(UniswapV3Reactive.ZeroAddress.selector);
        reactive.setCallback(address(0));
    }

    // ── migrateFunds ──

    function test_migrateFunds_sendsAllETH() public {
        address payable recipient = payable(makeAddr("recipient"));
        // Note: constructor deposits to SystemContract, so balance may be 0
        // Fund it explicitly after construction
        vm.deal(address(reactive), 1 ether);

        reactive.migrateFunds(recipient);

        assertEq(address(reactive).balance, 0);
        assertEq(recipient.balance, 1 ether);
    }

    function test_migrateFunds_emitsFundsMigrated() public {
        vm.deal(address(reactive), 1 ether);
        address payable recipient = payable(makeAddr("recipient"));
        vm.expectEmit(true, false, false, true);
        // FundsMigrated is a file-level event from AdminLib, import directly
        emit FundsMigrated(recipient, 1 ether);
        reactive.migrateFunds(recipient);
    }

    function test_migrateFunds_revertsIfNotOwner() public {
        vm.deal(address(reactive), 1 ether);
        vm.prank(notOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        reactive.migrateFunds(payable(makeAddr("recipient")));
    }

    function test_migrateFunds_revertsIfNoFunds() public {
        // Ensure zero balance
        vm.deal(address(reactive), 0);
        vm.expectRevert(NoFunds.selector);
        reactive.migrateFunds(payable(makeAddr("recipient")));
    }

    function test_migrateFunds_revertsIfRecipientRejectsETH() public {
        vm.deal(address(reactive), 1 ether);
        RejectETH rejector = new RejectETH();
        vm.expectRevert(MigrationTransferFailed.selector);
        reactive.migrateFunds(payable(address(rejector)));
    }

    // ── transferOwnership ──

    function test_transferOwnership_updatesOwner() public {
        address newOwner = makeAddr("newOwner");
        reactive.transferOwnership(newOwner);

        // Old owner locked out
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        reactive.setCallback(makeAddr("x"));

        // New owner works
        vm.prank(newOwner);
        reactive.setCallback(makeAddr("x"));
    }

    function test_transferOwnership_revertsIfNotOwner() public {
        vm.prank(notOwner);
        vm.expectRevert(OwnerUnauthorizedAccount.selector);
        reactive.transferOwnership(notOwner);
    }

    function test_transferOwnership_toZeroRenouncesOwnership() public {
        // LibOwner allows transfer to address(0) — permanently renounces ownership
        reactive.transferOwnership(address(0));
        vm.expectRevert(); // OwnerAlreadyRenounced
        reactive.transferOwnership(makeAddr("x"));
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `forge test --match-path "test/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.admin.t.sol" -vv`
Expected: FAIL — compilation errors because `UniswapV3Reactive` doesn't have `setCallback`, `migrateFunds`, `transferOwnership`, `callback()` getter, etc.

- [ ] **Step 3: Commit failing tests**

```bash
git add test/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.admin.t.sol
git commit -m "test(008): add failing admin tests for UniswapV3Reactive"
```

---

## Task 5: Implement `UniswapV3Reactive` admin changes

**Files:**
- Modify: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol`

Key changes from current:
- Import `LibOwner` functions and `AdminLib`
- `address immutable owner` → removed (LibOwner)
- `address immutable callback` → `address public callback` (storage)
- `ISubscriptionService immutable service` — stays immutable
- `bool immutable vm` — stays immutable
- `error OnlyOwner()` → removed
- New: `setCallback(address)`, `migrateFunds(address payable)`, `transferOwnership(address)`
- New: `error ZeroAddress()`, `event CallbackUpdated`
- `registerPool` and `unregisterPool` guards change to `requireOwner()`

- [ ] **Step 1: Update `UniswapV3Reactive.sol`**

1. Add imports:
```solidity
import {initOwner, requireOwner, transferOwnership as _transferOwnership} from "../../modules/dependencies/LibOwner.sol";
import {migrateFunds as _migrateFunds} from "../../modules/dependencies/AdminLib.sol";
```

2. Replace state variables:
```solidity
// Before:
address immutable owner;
address immutable callback;
ISubscriptionService immutable service;
bool immutable vm;

// After:
address public callback;
ISubscriptionService immutable service;
bool immutable vm;
```

3. Replace errors:
```solidity
// Remove: error OnlyOwner();
// Add:
error ZeroAddress();
```

4. Add events:
```solidity
event CallbackUpdated(address indexed oldCallback, address indexed newCallback);
```

5. Update constructor:
```solidity
constructor(address callback_) payable {
    initOwner(msg.sender);
    callback = callback_;
    service = ISubscriptionService(SYSTEM_CONTRACT);
    // ... vm detection unchanged ...
}
```

6. Add new admin functions:
```solidity
function setCallback(address newCallback) external {
    requireOwner();
    if (newCallback == address(0)) revert ZeroAddress();
    address oldCallback = callback;
    callback = newCallback;
    emit CallbackUpdated(oldCallback, newCallback);
}

function migrateFunds(address payable to) external {
    requireOwner();
    _migrateFunds(to);
}

function transferOwnership(address newOwner) external {
    requireOwner();
    _transferOwnership(newOwner);
}
```

7. Update `registerPool` and `unregisterPool` guards:
```solidity
// Before: if (msg.sender != owner) revert OnlyOwner();
// After:  requireOwner();
```

- [ ] **Step 2: Verify compilation**

Run: `forge build --match-path "src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol"`
Expected: PASS

- [ ] **Step 3: Run admin tests**

Run: `forge test --match-path "test/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.admin.t.sol" -vv`
Expected: ALL PASS

- [ ] **Step 4: Run all tests to check for regressions**

Run: `forge test --match-path "test/fee-concentration-index-v2/**" -vv`
Expected: ALL PASS (including `UniswapV3ReactiveDebug.t.sol`)

- [ ] **Step 5: Commit**

```bash
git add src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol
git commit -m "feat(008): add admin upgradeability to UniswapV3Reactive"
```

---

## Task 6: Final verification and combined commit

- [ ] **Step 1: Full test suite**

Run: `forge test -vv`
Expected: ALL PASS

- [ ] **Step 2: Verify no untracked files left behind**

Run: `git status`
Expected: clean working tree (all changes committed)
