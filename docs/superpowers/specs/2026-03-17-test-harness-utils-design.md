# Test Harness Utils — Design Spec

Date: 2026-03-17
Branch: 008-uniswap-v3-reactive-integration
Status: Reviewed (v2)

## Problem

Every test and script reimplements token creation, account setup, approvals, and wiring. The existing helpers (`foundry-script/types/Accounts.sol`, `FundAccounts.s.sol`, `DeployMockTokens.s.sol`, `FCITestHelper.sol`) attack the same problem but are not modular, not reusable across test/script boundaries, and tightly coupled to specific protocols or inheritance chains.

## Goal

A single set of free functions + structs in `src/utils/` that any test or script can import to handle the full "create tokens → create accounts → fund accounts → approve spenders" pipeline. One source of truth, zero inheritance, composable.

## Design Decisions

- **Free functions + structs** — no abstract contracts, no inheritance, no `library` keyword
- **`Mode` enum** — `Test` (uses `vm.prank` + `MockERC20.mint`) vs `Script` (uses `vm.broadcast` + `transfer`) in function signatures, so the same file serves both
- **`Vm.Wallet`** — reuse forge-std's built-in wallet type for accounts, no custom wrapper
- **Auto-sorted `TokenPair`** — enforces `token0 < token1` (Uniswap convention)
- **Role-filtered approvals** — `ApprovalTarget` struct specifies which roles approve which spender
- **Pool creation optional** — separate composable file, not bundled into seed/approve flow

## Files

### `src/utils/Mode.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

enum Mode { Test, Script }
```

Standalone file — avoids coupling `Pool.sol` to `Accounts.sol`.

### `src/utils/TokenPair.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Vm} from "forge-std/Vm.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";

struct TokenPair {
    address token0;
    address token1;
}

/// @notice Deploy 2 fresh MockERC20s, mint `supply` to `mintTo`, return sorted.
function mockPair(Vm vm, uint256 supply, address mintTo) returns (TokenPair memory) { ... }

/// @notice Wrap two existing addresses into a sorted TokenPair.
function existingPair(address a, address b) pure returns (TokenPair memory) { ... }
```

**Invariant:** `token0 < token1` always holds after construction.

**Note on `mockPair`:** The `mintTo` parameter specifies who receives the initial supply. In tests this is typically `address(this)` (the test contract) or `deployer.addr`. The function deploys two `MockERC20` tokens with unrestricted `mint()` — any address can mint. The `mintTo` parameter receives the initial supply at deploy time.

### `src/utils/Accounts.sol`

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
    Vm.Wallet lpPassive;         // HD index 1 (preserves existing order)
    Vm.Wallet lpSophisticated;   // HD index 2
    Vm.Wallet swapper;           // HD index 3
}

struct ApprovalTarget {
    address spender;
    bool lpPassive;
    bool lpSophisticated;
    bool swapper;
}

string constant DEFAULT_DERIVATION_PATH = "m/44'/60'/0'/0/";

/// @notice Create test accounts using vm.createWallet with labels (no mnemonic needed).
///         Labels: "deployer", "lpSophisticated", "lpPassive", "swapper".
function makeTestAccounts(Vm vm) returns (Accounts memory) { ... }

/// @notice Create script accounts from MNEMONIC env var (HD indices 0-3).
function initAccounts(Vm vm) returns (Accounts memory) { ... }

/// @notice Fund all non-deployer accounts with `amount` of both tokens.
///         Mode.Test  → MockERC20(token).mint(account, amount) — mock tokens only.
///         Mode.Script → vm.startBroadcast(deployer.pk) + IERC20.transfer() per recipient,
///                       then vm.stopBroadcast().
///
///         Calling seed in Mode.Test on a TokenPair created via existingPair will
///         revert — the target contracts will not have a mint(address,uint256) function.
///         For fork tests with real (non-mock) tokens, callers must handle funding
///         externally (e.g., deal() from StdCheats or vm.store).
function seed(
    Vm vm,
    Accounts memory accts,
    TokenPair memory pair,
    uint256 amount,
    Mode mode
) { ... }

/// @notice Each account approves pair tokens on its assigned spenders.
///         Mode.Test  → vm.prank(account.addr) + IERC20.approve() for both tokens.
///         Mode.Script → vm.startBroadcast(account.privateKey) + IERC20.approve(),
///                       then vm.stopBroadcast() after each account's approvals.
///
///         Broadcast boundaries: each role gets its own startBroadcast/stopBroadcast
///         cycle. Never nested.
function approveAll(
    Vm vm,
    Accounts memory accts,
    TokenPair memory pair,
    ApprovalTarget[] memory targets,
    Mode mode
) { ... }
```

**`seed` behavior by mode:**
- `Mode.Test`: Uses `MockERC20(token).mint(account, amount)`. Only works with mock tokens (deployed via `mockPair`). For fork tests with real tokens, the caller must fund accounts externally.
- `Mode.Script`: Uses `vm.startBroadcast(deployer.privateKey)` + `IERC20.transfer()` to each recipient, then `vm.stopBroadcast()`. Deployer must hold sufficient balance.

**`approveAll` behavior by mode:**
- `Mode.Test`: For each role that matches a target, `vm.startPrank(account.addr)` then `IERC20.approve(spender, type(uint256).max)` for both tokens, then `vm.stopPrank()`. Uses `startPrank`/`stopPrank` (not single-call `prank`) because two approvals (token0 + token1) are needed per spender.
- `Mode.Script`: For each role that matches a target, `vm.startBroadcast(account.privateKey)` then `IERC20.approve(spender, type(uint256).max)` for both tokens, then `vm.stopBroadcast()`. Each role is a separate broadcast cycle — never nested.

### `src/utils/Pool.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Vm} from "forge-std/Vm.sol";
import {TokenPair} from "./TokenPair.sol";
import {Mode} from "./Mode.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";

/// @notice Initialize a V4 pool. Optional — not part of seed/approve flow.
function createPoolV4(
    Vm vm,
    TokenPair memory pair,
    address hookAddress,
    uint24 fee,
    int24 tickSpacing,
    uint160 sqrtPriceX96,
    address poolManager,
    Mode mode
) returns (PoolKey memory, PoolId) { ... }

/// @notice Initialize a V3 pool. Optional — not part of seed/approve flow.
///         Calls factory.createPool(token0, token1, fee), then pool.initialize(sqrtPriceX96).
function createPoolV3(
    Vm vm,
    TokenPair memory pair,
    uint24 fee,
    uint160 sqrtPriceX96,
    address factory,
    Mode mode
) returns (address pool) { ... }
```

## Usage Examples

### Unit test setUp

```solidity
import {Accounts, makeTestAccounts, seed, approveAll, ApprovalTarget} from "src/utils/Accounts.sol";
import {TokenPair, mockPair} from "src/utils/TokenPair.sol";
import {Mode} from "src/utils/Mode.sol";

function setUp() public {
    Accounts memory accts = makeTestAccounts(vm);
    TokenPair memory pair = mockPair(vm, 1_000_000e18, accts.deployer.addr);
    seed(vm, accts, pair, 100_000e18, Mode.Test);

    ApprovalTarget[] memory targets = new ApprovalTarget[](2);
    targets[0] = ApprovalTarget(address(positionManager), true, true, false);  // LPs only
    targets[1] = ApprovalTarget(address(swapRouter), false, false, true);     // swapper only
    approveAll(vm, accts, pair, targets, Mode.Test);
}
```

### Fork test setUp

```solidity
import {Accounts, makeTestAccounts, approveAll, ApprovalTarget} from "src/utils/Accounts.sol";
import {TokenPair, existingPair} from "src/utils/TokenPair.sol";
import {Mode} from "src/utils/Mode.sol";

function setUp() public {
    Accounts memory accts = makeTestAccounts(vm);
    TokenPair memory pair = existingPair(USDC, WETH);

    // Fork tests: fund accounts externally (seed only works with mock tokens)
    deal(pair.token0, accts.lpPassive.addr, 100_000e6);
    deal(pair.token0, accts.lpSophisticated.addr, 100_000e6);
    deal(pair.token0, accts.swapper.addr, 100_000e6);
    // ... repeat for token1

    approveAll(vm, accts, pair, targets, Mode.Test);
}
```

### Deployment script

```solidity
import {Accounts, initAccounts, seed, approveAll, ApprovalTarget} from "src/utils/Accounts.sol";
import {TokenPair, existingPair} from "src/utils/TokenPair.sol";
import {Mode} from "src/utils/Mode.sol";
import {sepoliaTokenA, sepoliaTokenB} from "@foundry-script/utils/Deployments.sol";

function run() public {
    Accounts memory accts = initAccounts(vm);
    TokenPair memory pair = existingPair(sepoliaTokenA(), sepoliaTokenB());
    seed(vm, accts, pair, 100_000e18, Mode.Script);

    ApprovalTarget[] memory targets = new ApprovalTarget[](1);
    targets[0] = ApprovalTarget(address(v3Pool), true, true, true);
    approveAll(vm, accts, pair, targets, Mode.Script);
}
```

## Migration Path

1. Existing `foundry-script/types/Accounts.sol` — delete entirely. Move `initAccounts` into `src/utils/Accounts.sol`. Update all imports project-wide to `src/utils/Accounts.sol`.
2. Existing `foundry-script/deploy/FundAccounts.s.sol` — replaced by `seed(..., Mode.Script)`.
3. Existing `foundry-script/deploy/DeployMockTokens.s.sol` — replaced by `mockPair(vm, supply, mintTo)`.
4. Existing `test/.../FCITestHelper.sol` — continues to exist for FCI-specific mint/burn/swap wrappers, but its setUp boilerplate (accounts, tokens, approvals) is replaced by these utils.

## What This Does NOT Cover

- Protocol-specific operations (mint position, burn, swap) — remains in protocol-specific helpers like `FCITestHelper`, `Scenario.sol`
- Hook deployment and mining — too protocol-specific
- Permit2 approval flows — can be added as a separate `ApprovalTarget` entry later
- Multi-token (>2) scenarios — out of scope, `TokenPair` is explicitly 2 tokens
- Native ETH as a token — `TokenPair` holds two `address` values; `address(0)` for native ETH is not handled (V4 Currency wrapping is caller's responsibility)
- Fork token funding — `seed` only works with mock tokens in `Mode.Test`. Fork tests must fund accounts externally using `deal()` from `StdCheats` inheritance or `vm.store`.

## Research Context

Surveyed forge-std, V4 Deployers, V4 PosmTestSetup, Angstrom BaseTest, Panoptic, Euler, Morpho, Balancer test suites. No existing library provides this pipeline in a free-function style. All use inheritance. Custom implementation (~80-120 lines) is the right path.
