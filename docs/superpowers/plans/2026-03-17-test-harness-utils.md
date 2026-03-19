# Test Harness Utils Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a unified, free-function test/script harness in `src/utils/` that handles token creation, account setup, funding, and approval wiring — eliminating boilerplate duplication across all tests and scripts.

**Architecture:** Three files in `src/utils/` (`Mode.sol`, `TokenPair.sol`, `Accounts.sol`) plus an optional `Pool.sol`. A `Mode` enum switches between `Test` (vm.prank/MockERC20.mint) and `Script` (vm.broadcast/transfer) behavior. All functions are free functions operating on structs — no inheritance, no `library` keyword.

**Tech Stack:** Solidity ^0.8.26, forge-std (Vm, Vm.Wallet), solmate MockERC20

**Spec:** `docs/superpowers/specs/2026-03-17-test-harness-utils-design.md`

---

## File Structure

| File | Responsibility | Action |
|------|---------------|--------|
| `src/utils/Mode.sol` | `Mode` enum (Test/Script) | Create |
| `src/utils/TokenPair.sol` | `TokenPair` struct, `mockPair()`, `existingPair()` | Create |
| `src/utils/Accounts.sol` | `Accounts` struct, `ApprovalTarget`, `makeTestAccounts()`, `initAccounts()`, `seed()`, `approveAll()` | Create |
| `src/utils/Pool.sol` | `createPoolV3()`, `createPoolV4()` — optional composable | Create |
| `test/utils/TokenPair.t.sol` | Tests for TokenPair | Create |
| `test/utils/Accounts.t.sol` | Tests for Accounts, seed, approveAll | Create |
| `test/utils/Pool.t.sol` | Tests for Pool creation | Create |
| `foundry-script/types/Accounts.sol` | Old accounts — becomes re-export | Modify |
| `foundry.toml` | Add `@utils/` remapping | Modify |

---

### Task 1: Mode.sol + TokenPair.sol

**Files:**
- Create: `src/utils/Mode.sol`
- Create: `src/utils/TokenPair.sol`
- Create: `test/utils/TokenPair.t.sol`
- Modify: `foundry.toml` (add remapping)

- [ ] **Step 1: Add remapping to foundry.toml**

Add `"@utils/=src/utils/"` to the remappings array in `foundry.toml`.

```toml
    "@utils/=src/utils/",
```

- [ ] **Step 2: Write Mode.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

enum Mode { Test, Script }
```

- [ ] **Step 3: Write the failing test for TokenPair**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {TokenPair, mockPair, existingPair} from "@utils/TokenPair.sol";

contract TokenPairTest is Test {
    function test_existingPair_sortsTokens() public pure {
        address a = address(0xBBBB);
        address b = address(0xAAAA);
        TokenPair memory pair = existingPair(a, b);
        assertEq(pair.token0, b);
        assertEq(pair.token1, a);
    }

    function test_existingPair_alreadySorted() public pure {
        address a = address(0xAAAA);
        address b = address(0xBBBB);
        TokenPair memory pair = existingPair(a, b);
        assertEq(pair.token0, a);
        assertEq(pair.token1, b);
    }

    function test_existingPair_revertsOnIdentical() public {
        address a = address(0xAAAA);
        vm.expectRevert("TokenPair: identical addresses");
        existingPair(a, a);
    }

    function test_mockPair_deploysAndSorts() public {
        uint256 supply = 1_000_000e18;
        TokenPair memory pair = mockPair(supply, address(this));
        assertTrue(pair.token0 < pair.token1, "not sorted");
        assertTrue(pair.token0 != address(0), "token0 is zero");
        assertTrue(pair.token1 != address(0), "token1 is zero");
    }

    function test_mockPair_mintsSupplyToRecipient() public {
        uint256 supply = 500e18;
        address recipient = makeAddr("recipient");
        TokenPair memory pair = mockPair(supply, recipient);
        assertEq(
            MockERC20(pair.token0).balanceOf(recipient),
            supply
        );
        assertEq(
            MockERC20(pair.token1).balanceOf(recipient),
            supply
        );
    }
}
```

- [ ] **Step 4: Run test to verify it fails**

Run: `forge test --match-path "test/utils/TokenPair.t.sol" -vv`
Expected: FAIL — `TokenPair.sol` does not exist yet.

- [ ] **Step 5: Write TokenPair.sol implementation**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";

struct TokenPair {
    address token0;
    address token1;
}

/// @notice Deploy 2 fresh MockERC20s, mint `supply` to `mintTo`, return sorted.
///         Does not require Vm — MockERC20.mint() is unrestricted.
function mockPair(uint256 supply, address mintTo) returns (TokenPair memory) {
    MockERC20 a = new MockERC20("Token A", "TKA", 18);
    MockERC20 b = new MockERC20("Token B", "TKB", 18);
    a.mint(mintTo, supply);
    b.mint(mintTo, supply);
    if (address(a) < address(b)) {
        return TokenPair(address(a), address(b));
    }
    return TokenPair(address(b), address(a));
}

/// @notice Wrap two existing addresses into a sorted TokenPair.
function existingPair(address a, address b) pure returns (TokenPair memory) {
    require(a != b, "TokenPair: identical addresses");
    if (a < b) return TokenPair(a, b);
    return TokenPair(b, a);
}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `forge test --match-path "test/utils/TokenPair.t.sol" -vv`
Expected: All 5 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/utils/Mode.sol src/utils/TokenPair.sol test/utils/TokenPair.t.sol foundry.toml
git commit -m "feat: add Mode enum and TokenPair with mockPair/existingPair"
```

---

### Task 2: Accounts.sol — struct + constructors

**Files:**
- Create: `src/utils/Accounts.sol`
- Create: `test/utils/Accounts.t.sol`

- [ ] **Step 1: Write the failing test for makeTestAccounts**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {Accounts, makeTestAccounts, initAccounts} from "@utils/Accounts.sol";

contract AccountsTest is Test {
    function test_makeTestAccounts_creates4Wallets() public {
        Accounts memory accts = makeTestAccounts(vm);
        assertTrue(accts.deployer.addr != address(0), "deployer zero");
        assertTrue(accts.lpPassive.addr != address(0), "lpPassive zero");
        assertTrue(accts.lpSophisticated.addr != address(0), "lpSophisticated zero");
        assertTrue(accts.swapper.addr != address(0), "swapper zero");
    }

    function test_makeTestAccounts_allDistinct() public {
        Accounts memory accts = makeTestAccounts(vm);
        assertTrue(accts.deployer.addr != accts.lpPassive.addr);
        assertTrue(accts.deployer.addr != accts.lpSophisticated.addr);
        assertTrue(accts.deployer.addr != accts.swapper.addr);
        assertTrue(accts.lpPassive.addr != accts.lpSophisticated.addr);
        assertTrue(accts.lpPassive.addr != accts.swapper.addr);
        assertTrue(accts.lpSophisticated.addr != accts.swapper.addr);
    }

    function test_makeTestAccounts_hasPrivateKeys() public {
        Accounts memory accts = makeTestAccounts(vm);
        assertTrue(accts.deployer.privateKey != 0);
        assertTrue(accts.lpPassive.privateKey != 0);
        assertTrue(accts.lpSophisticated.privateKey != 0);
        assertTrue(accts.swapper.privateKey != 0);
    }

    function test_initAccounts_derivesFromMnemonic() public {
        vm.setEnv("MNEMONIC", "test test test test test test test test test test test junk");
        Accounts memory accts = initAccounts(vm);
        assertTrue(accts.deployer.addr != address(0), "deployer zero");
        assertTrue(accts.lpPassive.addr != address(0), "lpPassive zero");
        assertTrue(accts.lpSophisticated.addr != address(0), "lpSophisticated zero");
        assertTrue(accts.swapper.addr != address(0), "swapper zero");
        // All distinct
        assertTrue(accts.deployer.addr != accts.lpPassive.addr);
        assertTrue(accts.deployer.addr != accts.lpSophisticated.addr);
        assertTrue(accts.deployer.addr != accts.swapper.addr);
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `forge test --match-path "test/utils/Accounts.t.sol" -vv`
Expected: FAIL — `Accounts.sol` does not exist yet.

- [ ] **Step 3: Write Accounts.sol — struct + makeTestAccounts + initAccounts**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Vm} from "forge-std/Vm.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {TokenPair} from "./TokenPair.sol";
import {Mode} from "./Mode.sol";

struct Accounts {
    Vm.Wallet deployer;
    Vm.Wallet lpPassive;
    Vm.Wallet lpSophisticated;
    Vm.Wallet swapper;
}

struct ApprovalTarget {
    address spender;
    bool lpPassive;
    bool lpSophisticated;
    bool swapper;
}

string constant DEFAULT_DERIVATION_PATH = "m/44'/60'/0'/0/";

/// @notice Create test accounts using vm.createWallet with labels.
function makeTestAccounts(Vm vm) returns (Accounts memory) {
    return Accounts({
        deployer: vm.createWallet("deployer"),
        lpPassive: vm.createWallet("lpPassive"),
        lpSophisticated: vm.createWallet("lpSophisticated"),
        swapper: vm.createWallet("swapper")
    });
}

/// @notice Create script accounts from MNEMONIC env var (HD indices 0-3).
function initAccounts(Vm vm) returns (Accounts memory) {
    string memory mnemonic = vm.envString("MNEMONIC");
    return Accounts({
        deployer: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 0), "deployer"),
        lpPassive: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 1), "lpPassive"),
        lpSophisticated: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 2), "lpSophisticated"),
        swapper: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 3), "swapper")
    });
}
```

Note: `seed` and `approveAll` are added in Task 3. Keep the file minimal for now.

- [ ] **Step 4: Run test to verify it passes**

Run: `forge test --match-path "test/utils/Accounts.t.sol" -vv`
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/utils/Accounts.sol test/utils/Accounts.t.sol
git commit -m "feat: add Accounts struct with makeTestAccounts and initAccounts"
```

---

### Task 3: seed() and approveAll()

**Files:**
- Modify: `src/utils/Accounts.sol` (add seed + approveAll)
- Modify: `test/utils/Accounts.t.sol` (add seed + approveAll tests)

- [ ] **Step 1: Write the failing test for seed (Mode.Test)**

Add to `test/utils/Accounts.t.sol`:

```solidity
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {TokenPair, mockPair} from "@utils/TokenPair.sol";
import {Mode} from "@utils/Mode.sol";
import {Accounts, makeTestAccounts, seed} from "@utils/Accounts.sol";

contract SeedTest is Test {
    function test_seed_testMode_fundsAllNonDeployer() public {
        Accounts memory accts = makeTestAccounts(vm);
        TokenPair memory pair = mockPair(1_000_000e18, address(this));
        uint256 amount = 100_000e18;

        seed(vm, accts, pair, amount, Mode.Test);

        assertEq(MockERC20(pair.token0).balanceOf(accts.lpPassive.addr), amount);
        assertEq(MockERC20(pair.token0).balanceOf(accts.lpSophisticated.addr), amount);
        assertEq(MockERC20(pair.token0).balanceOf(accts.swapper.addr), amount);
        assertEq(MockERC20(pair.token1).balanceOf(accts.lpPassive.addr), amount);
        assertEq(MockERC20(pair.token1).balanceOf(accts.lpSophisticated.addr), amount);
        assertEq(MockERC20(pair.token1).balanceOf(accts.swapper.addr), amount);
    }

    function test_seed_testMode_doesNotFundDeployer() public {
        Accounts memory accts = makeTestAccounts(vm);
        TokenPair memory pair = mockPair(1_000_000e18, address(this));

        seed(vm, accts, pair, 100_000e18, Mode.Test);

        assertEq(MockERC20(pair.token0).balanceOf(accts.deployer.addr), 0);
        assertEq(MockERC20(pair.token1).balanceOf(accts.deployer.addr), 0);
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `forge test --match-path "test/utils/Accounts.t.sol" --match-contract SeedTest -vv`
Expected: FAIL — `seed` not defined.

- [ ] **Step 3: Implement seed() in Accounts.sol**

Add to `src/utils/Accounts.sol`:

```solidity
/// @notice Fund all non-deployer accounts with `amount` of both tokens.
///         Mode.Test  → MockERC20(token).mint(account, amount).
///         Mode.Script → vm.startBroadcast(deployer.pk) + IERC20.transfer().
///         Calling seed in Mode.Test on a TokenPair from existingPair will revert.
function seed(
    Vm vm,
    Accounts memory accts,
    TokenPair memory pair,
    uint256 amount,
    Mode mode
) {
    address[3] memory recipients = [accts.lpPassive.addr, accts.lpSophisticated.addr, accts.swapper.addr];

    if (mode == Mode.Test) {
        for (uint256 i; i < 3; ++i) {
            MockERC20(pair.token0).mint(recipients[i], amount);
            MockERC20(pair.token1).mint(recipients[i], amount);
        }
    } else {
        vm.startBroadcast(accts.deployer.privateKey);
        for (uint256 i; i < 3; ++i) {
            IERC20(pair.token0).transfer(recipients[i], amount);
            IERC20(pair.token1).transfer(recipients[i], amount);
        }
        vm.stopBroadcast();
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `forge test --match-path "test/utils/Accounts.t.sol" --match-contract SeedTest -vv`
Expected: All 2 tests PASS.

- [ ] **Step 5: Write the failing test for approveAll (Mode.Test)**

Add to `test/utils/Accounts.t.sol`:

```solidity
import {Accounts, makeTestAccounts, seed, approveAll, ApprovalTarget} from "@utils/Accounts.sol";

contract ApproveAllTest is Test {
    function test_approveAll_testMode_approvesCorrectRoles() public {
        Accounts memory accts = makeTestAccounts(vm);
        TokenPair memory pair = mockPair(1_000_000e18, address(this));
        seed(vm, accts, pair, 100_000e18, Mode.Test);

        address router = makeAddr("router");

        ApprovalTarget[] memory targets = new ApprovalTarget[](1);
        targets[0] = ApprovalTarget(router, true, false, true); // lpPassive + swapper, not lpSophisticated

        approveAll(vm, accts, pair, targets, Mode.Test);

        // lpPassive approved
        assertEq(IERC20(pair.token0).allowance(accts.lpPassive.addr, router), type(uint256).max);
        assertEq(IERC20(pair.token1).allowance(accts.lpPassive.addr, router), type(uint256).max);

        // swapper approved
        assertEq(IERC20(pair.token0).allowance(accts.swapper.addr, router), type(uint256).max);
        assertEq(IERC20(pair.token1).allowance(accts.swapper.addr, router), type(uint256).max);

        // lpSophisticated NOT approved
        assertEq(IERC20(pair.token0).allowance(accts.lpSophisticated.addr, router), 0);
        assertEq(IERC20(pair.token1).allowance(accts.lpSophisticated.addr, router), 0);
    }

    function test_approveAll_testMode_multipleTargets() public {
        Accounts memory accts = makeTestAccounts(vm);
        TokenPair memory pair = mockPair(1_000_000e18, address(this));

        address posm = makeAddr("posm");
        address swapRouter = makeAddr("swapRouter");

        ApprovalTarget[] memory targets = new ApprovalTarget[](2);
        targets[0] = ApprovalTarget(posm, true, true, false);       // LPs only
        targets[1] = ApprovalTarget(swapRouter, false, false, true); // swapper only

        approveAll(vm, accts, pair, targets, Mode.Test);

        // LPs approved on posm
        assertEq(IERC20(pair.token0).allowance(accts.lpPassive.addr, posm), type(uint256).max);
        assertEq(IERC20(pair.token0).allowance(accts.lpSophisticated.addr, posm), type(uint256).max);

        // Swapper approved on swapRouter
        assertEq(IERC20(pair.token0).allowance(accts.swapper.addr, swapRouter), type(uint256).max);

        // Swapper NOT approved on posm
        assertEq(IERC20(pair.token0).allowance(accts.swapper.addr, posm), 0);

        // LPs NOT approved on swapRouter
        assertEq(IERC20(pair.token0).allowance(accts.lpPassive.addr, swapRouter), 0);
    }
}
```

- [ ] **Step 6: Run test to verify it fails**

Run: `forge test --match-path "test/utils/Accounts.t.sol" --match-contract ApproveAllTest -vv`
Expected: FAIL — `approveAll` not defined.

- [ ] **Step 7: Implement approveAll() in Accounts.sol**

Add to `src/utils/Accounts.sol`:

```solidity
/// @notice Each account approves pair tokens on its assigned spenders.
///         Mode.Test  → vm.startPrank/stopPrank per role.
///         Mode.Script → vm.startBroadcast/stopBroadcast per role. Never nested.
function approveAll(
    Vm vm,
    Accounts memory accts,
    TokenPair memory pair,
    ApprovalTarget[] memory targets,
    Mode mode
) {
    for (uint256 i; i < targets.length; ++i) {
        ApprovalTarget memory t = targets[i];

        if (t.lpPassive) _approveFor(vm, accts.lpPassive, pair, t.spender, mode);
        if (t.lpSophisticated) _approveFor(vm, accts.lpSophisticated, pair, t.spender, mode);
        if (t.swapper) _approveFor(vm, accts.swapper, pair, t.spender, mode);
    }
}

function _approveFor(
    Vm vm,
    Vm.Wallet memory wallet,
    TokenPair memory pair,
    address spender,
    Mode mode
) {
    if (mode == Mode.Test) {
        vm.startPrank(wallet.addr);
    } else {
        vm.startBroadcast(wallet.privateKey);
    }

    IERC20(pair.token0).approve(spender, type(uint256).max);
    IERC20(pair.token1).approve(spender, type(uint256).max);

    if (mode == Mode.Test) {
        vm.stopPrank();
    } else {
        vm.stopBroadcast();
    }
}
```

- [ ] **Step 8: Run test to verify it passes**

Run: `forge test --match-path "test/utils/Accounts.t.sol" -vv`
Expected: All tests PASS (AccountsTest + SeedTest + ApproveAllTest).

- [ ] **Step 9: Commit**

```bash
git add src/utils/Accounts.sol test/utils/Accounts.t.sol
git commit -m "feat: add seed() and approveAll() to Accounts harness"
```

---

### Task 4: Pool.sol (optional composable)

**Files:**
- Create: `src/utils/Pool.sol`
- Create: `test/utils/Pool.t.sol`

- [ ] **Step 1: Write the failing test for createPoolV4**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {Deployers} from "v4-core/test/utils/Deployers.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {TokenPair, mockPair} from "@utils/TokenPair.sol";
import {createPoolV4} from "@utils/Pool.sol";

contract PoolV4Test is Test, Deployers {
    function test_createPoolV4_initializesPool() public {
        deployFreshManagerAndRouters();
        TokenPair memory pair = mockPair(1_000_000e18, address(this));

        (PoolKey memory key, PoolId poolId) = createPoolV4(
            pair,
            address(0),   // no hook
            3000,
            60,           // tickSpacing
            SQRT_PRICE_1_1,
            address(manager)
        );

        assertTrue(PoolId.unwrap(poolId) != bytes32(0), "poolId is zero");
        assertEq(key.fee, 3000);
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `forge test --match-path "test/utils/Pool.t.sol" -vv`
Expected: FAIL — `Pool.sol` does not exist.

- [ ] **Step 3: Write Pool.sol implementation**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {TokenPair} from "./TokenPair.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IUniswapV3Factory} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";

/// @notice Initialize a V4 pool. Optional — not part of seed/approve flow.
function createPoolV4(
    TokenPair memory pair,
    address hookAddress,
    uint24 fee,
    int24 tickSpacing,
    uint160 sqrtPriceX96,
    address poolManager
) returns (PoolKey memory key, PoolId poolId) {
    key = PoolKey({
        currency0: Currency.wrap(pair.token0),
        currency1: Currency.wrap(pair.token1),
        fee: fee,
        tickSpacing: tickSpacing,
        hooks: IHooks(hookAddress)
    });
    poolId = PoolIdLibrary.toId(key);
    IPoolManager(poolManager).initialize(key, sqrtPriceX96);
}

/// @notice Initialize a V3 pool. Optional — not part of seed/approve flow.
///         Calls factory.createPool(token0, token1, fee), then pool.initialize(sqrtPriceX96).
function createPoolV3(
    TokenPair memory pair,
    uint24 fee,
    uint160 sqrtPriceX96,
    address factory
) returns (address pool) {
    pool = IUniswapV3Factory(factory).createPool(pair.token0, pair.token1, fee);
    IUniswapV3Pool(pool).initialize(sqrtPriceX96);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `forge test --match-path "test/utils/Pool.t.sol" -vv`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/utils/Pool.sol test/utils/Pool.t.sol
git commit -m "feat: add optional Pool.sol with createPoolV3/createPoolV4"
```

---

### Task 5: Migration — update old Accounts.sol to re-export

**Files:**
- Modify: `foundry-script/types/Accounts.sol` (replace contents with re-export)

This task makes the old import path (`@foundry-script/types/Accounts.sol`) continue to work by re-exporting from the new location. This avoids touching all 14 consumer files immediately.

- [ ] **Step 1: Replace foundry-script/types/Accounts.sol with re-export**

Replace the entire file contents with:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Re-export from canonical location. New code should import from @utils/Accounts.sol.
import {Accounts, ApprovalTarget, makeTestAccounts, initAccounts, seed, approveAll, DEFAULT_DERIVATION_PATH} from "@utils/Accounts.sol";
```

- [ ] **Step 2: Run full test suite to verify nothing breaks**

Run: `forge test -vv`
Expected: All existing tests continue to pass. The re-export makes the old import path resolve to the new definitions.

- [ ] **Step 3: Commit**

```bash
git add foundry-script/types/Accounts.sol
git commit -m "refactor: re-export Accounts from src/utils for backwards compat"
```

---

### Task 6: Integration smoke test

**Files:**
- Create: `test/utils/HarnessIntegration.t.sol`

A single test that exercises the full pipeline: makeTestAccounts → mockPair → seed → approveAll → createPoolV4, proving the harness works end-to-end.

- [ ] **Step 1: Write the integration test**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {Deployers} from "v4-core/test/utils/Deployers.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";

import {TokenPair, mockPair} from "@utils/TokenPair.sol";
import {Mode} from "@utils/Mode.sol";
import {Accounts, ApprovalTarget, makeTestAccounts, seed, approveAll} from "@utils/Accounts.sol";
import {createPoolV4} from "@utils/Pool.sol";

contract HarnessIntegrationTest is Test, Deployers {
    function test_fullPipeline() public {
        // 1. Deploy V4 infra
        deployFreshManagerAndRouters();

        // 2. Create accounts + tokens
        Accounts memory accts = makeTestAccounts(vm);
        TokenPair memory pair = mockPair(1_000_000e18, address(this));

        // 3. Fund accounts
        seed(vm, accts, pair, 100_000e18, Mode.Test);

        // 4. Approve routers
        ApprovalTarget[] memory targets = new ApprovalTarget[](2);
        targets[0] = ApprovalTarget(address(modifyLiquidityRouter), true, true, false);
        targets[1] = ApprovalTarget(address(swapRouter), false, false, true);
        approveAll(vm, accts, pair, targets, Mode.Test);

        // 5. Create pool
        (PoolKey memory key,) = createPoolV4(
            pair, address(0), 3000, 60, SQRT_PRICE_1_1, address(manager)
        );

        // 6. Verify state
        assertEq(MockERC20(pair.token0).balanceOf(accts.lpPassive.addr), 100_000e18);
        assertEq(
            IERC20(pair.token0).allowance(accts.lpPassive.addr, address(modifyLiquidityRouter)),
            type(uint256).max
        );
        assertEq(
            IERC20(pair.token0).allowance(accts.swapper.addr, address(swapRouter)),
            type(uint256).max
        );
        assertEq(key.fee, 3000);
    }
}
```

- [ ] **Step 2: Run integration test**

Run: `forge test --match-path "test/utils/HarnessIntegration.t.sol" -vv`
Expected: PASS.

- [ ] **Step 3: Run full test suite**

Run: `forge test -vv`
Expected: All tests pass, including all existing tests.

- [ ] **Step 4: Commit**

```bash
git add test/utils/HarnessIntegration.t.sol
git commit -m "test: add integration smoke test for test harness utils"
```

---

## Task Dependencies

```
Task 1 (Mode + TokenPair)
  ├── Task 2 (Accounts struct)
  │     └── Task 3 (seed + approveAll)
  │           └── Task 5 (Migration re-export)
  │
  └── Task 4 (Pool.sol) — only needs TokenPair + Mode from Task 1

Tasks 3+5 and Task 4 are independent and can be parallelized.
Task 6 (Integration smoke) depends on Tasks 3, 4, and 5 all being complete.
```

**Note on test gaps:** `Mode.Script` paths (`seed`, `approveAll` with `vm.broadcast`) and `createPoolV3` are not unit-tested in this plan. They are exercised by existing deployment scripts and will be validated during the migration step (Task 5, full test suite run). Dedicated Script-mode tests can be added in a follow-up.
