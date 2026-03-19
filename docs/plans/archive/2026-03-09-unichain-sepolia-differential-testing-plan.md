# Unichain Sepolia Differential FCI Testing — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy mock tokens + FCI on both Unichain Sepolia (V4, local hook) and Eth Sepolia (V3, reactive adapter), run identical delta-plus scenarios on both, assert deltaPlus matches.

**Architecture:** 6 deploy scripts (chain-agnostic where possible, protocol-specific for hook/pool creation), a shell orchestrator for differential testing, and a read-only comparison script. All deployed addresses hardcoded in `script/utils/Deployments.sol`.

**Tech Stack:** Forge scripts (vm.broadcast), solmate MockERC20, HookMiner (v4-periphery), Permit2, PoolManager.initialize, V3 factory, reactive adapter, shell orchestration.

---

### Task 1: DeployMockTokens.s.sol

**Files:**
- Create: `script/deploy/DeployMockTokens.s.sol`
- Modify: `script/utils/Deployments.sol` (add token resolver stubs)

**Step 1: Add token resolver stubs to Deployments.sol**

Add to `script/utils/Deployments.sol` after the existing per-chain functions:

```solidity
// ── Mock Tokens ──

function unichainSepoliaTokenA() pure returns (address) {
    return address(0); // TODO: fill after DeployMockTokens
}

function unichainSepoliaTokenB() pure returns (address) {
    return address(0); // TODO: fill after DeployMockTokens
}

function sepoliaTokenA() pure returns (address) {
    return address(0); // TODO: fill after DeployMockTokens
}

function sepoliaTokenB() pure returns (address) {
    return address(0); // TODO: fill after DeployMockTokens
}

function resolveTokens(uint256 chainId) pure returns (address tokenA, address tokenB) {
    if (chainId == UNICHAIN_SEPOLIA) {
        tokenA = unichainSepoliaTokenA();
        tokenB = unichainSepoliaTokenB();
    } else if (chainId == SEPOLIA) {
        tokenA = sepoliaTokenA();
        tokenB = sepoliaTokenB();
    } else {
        revert UnknownDeployment(chainId, Protocol.UniswapV3);
    }
}
```

**Step 2: Create DeployMockTokens.s.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {Accounts, initAccounts} from "../types/Accounts.sol";

contract DeployMockTokensScript is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        uint256 supply = 1_000_000e18;

        vm.startBroadcast(accounts.deployer.privateKey);

        MockERC20 tokenA = new MockERC20("ThetaSwap Token A", "TSA", 18);
        MockERC20 tokenB = new MockERC20("ThetaSwap Token B", "TSB", 18);
        tokenA.mint(accounts.deployer.addr, supply);
        tokenB.mint(accounts.deployer.addr, supply);

        vm.stopBroadcast();

        console2.log("TOKEN_A=%s", address(tokenA));
        console2.log("TOKEN_B=%s", address(tokenB));

        if (address(tokenA) > address(tokenB)) {
            console2.log("currency0=TOKEN_B, currency1=TOKEN_A");
        } else {
            console2.log("currency0=TOKEN_A, currency1=TOKEN_B");
        }
    }
}
```

**Step 3: Verify compilation**

Run: `forge build`
Expected: Compiler run successful

**Step 4: Commit**

```bash
git add script/deploy/DeployMockTokens.s.sol script/utils/Deployments.sol
git commit -m "feat(003): DeployMockTokens script + token resolver stubs in Deployments"
```

---

### Task 2: DeployFCIHookV4.s.sol

**Files:**
- Create: `script/deploy/DeployFCIHookV4.s.sol`

**Step 1: Create DeployFCIHookV4.s.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {FeeConcentrationIndex} from "../../src/fee-concentration-index/FeeConcentrationIndex.sol";
import {Accounts, initAccounts} from "../types/Accounts.sol";
import {unichainSepoliaPoolManager} from "../utils/Deployments.sol";

contract DeployFCIHookV4Script is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        address poolManager = unichainSepoliaPoolManager();

        // FCI implements 5 hook callbacks
        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
                | Hooks.BEFORE_SWAP_FLAG
                | Hooks.AFTER_SWAP_FLAG
                | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
                | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
        );

        bytes memory creationCode = type(FeeConcentrationIndex).creationCode;
        bytes memory constructorArgs = abi.encode(poolManager);

        // Mine CREATE2 salt for valid hook address
        (address hookAddress, bytes32 salt) =
            HookMiner.find(accounts.deployer.addr, flags, creationCode, constructorArgs);

        vm.startBroadcast(accounts.deployer.privateKey);
        FeeConcentrationIndex fci = new FeeConcentrationIndex{salt: salt}(poolManager);
        vm.stopBroadcast();

        require(address(fci) == hookAddress, "hook address mismatch");
        console2.log("FCI_HOOK=%s", address(fci));
    }
}
```

**Step 2: Verify compilation**

Run: `forge build`
Expected: Compiler run successful

**Step 3: Commit**

```bash
git add script/deploy/DeployFCIHookV4.s.sol
git commit -m "feat(003): DeployFCIHookV4 script with HookMiner salt search"
```

---

### Task 3: CreatePoolV4.s.sol

**Files:**
- Create: `script/deploy/CreatePoolV4.s.sol`

**Step 1: Create CreatePoolV4.s.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {Accounts, initAccounts} from "../types/Accounts.sol";
import {
    unichainSepoliaPoolManager,
    unichainSepoliaFCIHook,
    resolveTokens,
    UNICHAIN_SEPOLIA
} from "../utils/Deployments.sol";
import "../utils/Constants.sol";

contract CreatePoolV4Script is Script {
    using PoolIdLibrary for PoolKey;

    function run() public {
        Accounts memory accounts = initAccounts(vm);

        address poolManager = unichainSepoliaPoolManager();
        address fciHook = unichainSepoliaFCIHook();
        (address tokenA, address tokenB) = resolveTokens(UNICHAIN_SEPOLIA);

        // Sort for currency0 < currency1
        (address c0, address c1) = tokenA < tokenB
            ? (tokenA, tokenB)
            : (tokenB, tokenA);

        PoolKey memory key = PoolKey({
            currency0: Currency.wrap(c0),
            currency1: Currency.wrap(c1),
            fee: 500,
            tickSpacing: int24(TICK_SPACING),
            hooks: IHooks(fciHook)
        });

        // 1:1 initial price: sqrt(1) * 2^96
        uint160 sqrtPriceX96 = 79228162514264337593543950336;

        vm.startBroadcast(accounts.deployer.privateKey);
        int24 tick = IPoolManager(poolManager).initialize(key, sqrtPriceX96);
        vm.stopBroadcast();

        console2.log("Pool initialized at tick=%d", tick);
        console2.log("PoolId:");
        console2.logBytes32(PoolId.unwrap(key.toId()));
    }
}
```

**Step 2: Verify compilation**

Run: `forge build`
Expected: Compiler run successful

**Step 3: Commit**

```bash
git add script/deploy/CreatePoolV4.s.sol
git commit -m "feat(003): CreatePoolV4 script — initialize V4 pool on Unichain Sepolia"
```

---

### Task 4: FundAccounts.s.sol

**Files:**
- Create: `script/deploy/FundAccounts.s.sol`

**Step 1: Create FundAccounts.s.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {IAllowanceTransfer} from "permit2/src/interfaces/IAllowanceTransfer.sol";
import {Accounts, initAccounts} from "../types/Accounts.sol";
import {Protocol, isUniswapV4} from "../types/Protocol.sol";
import {
    resolveTokens,
    resolveDeployments,
    Deployments,
    SEPOLIA,
    UNICHAIN_SEPOLIA
} from "../utils/Deployments.sol";

address constant PERMIT2 = 0x000000000022D473030F116dDEE9F6B43aC78BA3;

contract FundAccountsScript is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        uint256 chainId = block.chainid;
        (address tokenA, address tokenB) = resolveTokens(chainId);
        uint256 amount = 100_000e18;

        address[3] memory recipients =
            [accounts.lpPassive.addr, accounts.lpSophisticated.addr, accounts.swapper.addr];
        uint256[3] memory pks =
            [accounts.lpPassive.privateKey, accounts.lpSophisticated.privateKey, accounts.swapper.privateKey];

        // ── Transfer tokens from deployer ──
        vm.startBroadcast(accounts.deployer.privateKey);
        for (uint256 i; i < 3; ++i) {
            MockERC20(tokenA).transfer(recipients[i], amount);
            MockERC20(tokenB).transfer(recipients[i], amount);
        }
        vm.stopBroadcast();

        // ── Approvals (each wallet approves for itself) ──
        if (chainId == UNICHAIN_SEPOLIA) {
            Deployments memory d = resolveDeployments(chainId, Protocol.UniswapV4);
            // V4: token → Permit2 → PositionManager
            for (uint256 i; i < 3; ++i) {
                vm.startBroadcast(pks[i]);
                IERC20(tokenA).approve(PERMIT2, type(uint256).max);
                IERC20(tokenB).approve(PERMIT2, type(uint256).max);
                IAllowanceTransfer(PERMIT2).approve(
                    tokenA, d.positionManager, type(uint160).max, type(uint48).max
                );
                IAllowanceTransfer(PERMIT2).approve(
                    tokenB, d.positionManager, type(uint160).max, type(uint48).max
                );
                vm.stopBroadcast();
            }
        } else if (chainId == SEPOLIA) {
            // V3: token → pool directly
            // V3 pool calls transferFrom on the caller during mint
            // The callback pattern means the LP must approve the pool
            (address pool,,) = resolveV3(chainId);
            for (uint256 i; i < 3; ++i) {
                vm.startBroadcast(pks[i]);
                IERC20(tokenA).approve(address(pool), type(uint256).max);
                IERC20(tokenB).approve(address(pool), type(uint256).max);
                vm.stopBroadcast();
            }
        }

        for (uint256 i; i < 3; ++i) {
            console2.log("Funded %s with %d of each token", recipients[i], amount);
        }
    }
}
```

Note: `resolveV3` import needs to be added to the import block. The Permit2 IAllowanceTransfer interface may need a remapping — check if `permit2/` is in remappings or use the path from v4-periphery's lib.

**Step 2: Verify compilation**

Run: `forge build`
Expected: Compiler run successful. If Permit2 import fails, add remapping: `permit2/=lib/v4-periphery/lib/permit2/`

**Step 3: Commit**

```bash
git add script/deploy/FundAccounts.s.sol
git commit -m "feat(003): FundAccounts script — transfer tokens + approve Permit2/V3"
```

---

### Task 5: CreatePoolV3.s.sol

**Files:**
- Create: `script/deploy/CreatePoolV3.s.sol`

**Step 1: Create CreatePoolV3.s.sol**

V3 pool creation uses the V3 factory's `createPool` or deploys a mock pool directly. Since we're using mock tokens on Sepolia (no existing factory pool), we deploy a UniswapV3Pool directly or use the factory if deployed.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {IUniswapV3Factory} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {Accounts, initAccounts} from "../types/Accounts.sol";
import {resolveTokens, SEPOLIA} from "../utils/Deployments.sol";

// Sepolia V3 factory (canonical Uniswap deployment)
address constant V3_FACTORY = 0x0227628f3F023bb0B980b67D528571c95c6DaC1c;

contract CreatePoolV3Script is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        (address tokenA, address tokenB) = resolveTokens(SEPOLIA);

        // Sort tokens
        (address t0, address t1) = tokenA < tokenB
            ? (tokenA, tokenB)
            : (tokenB, tokenA);

        vm.startBroadcast(accounts.deployer.privateKey);

        // Create pool via factory (fee=500 → tickSpacing=10)
        address pool = IUniswapV3Factory(V3_FACTORY).createPool(t0, t1, 500);

        // Initialize at 1:1 price
        uint160 sqrtPriceX96 = 79228162514264337593543950336;
        IUniswapV3Pool(pool).initialize(sqrtPriceX96);

        vm.stopBroadcast();

        console2.log("V3_POOL=%s", pool);
    }
}
```

Note: The V3 factory address on Sepolia should be verified. If Uniswap V3 factory is not deployed on Sepolia at that address, we may need to deploy our own mock pool contract.

**Step 2: Verify compilation**

Run: `forge build`
Expected: Compiler run successful

**Step 3: Commit**

```bash
git add script/deploy/CreatePoolV3.s.sol
git commit -m "feat(003): CreatePoolV3 script — create V3 pool on Sepolia via factory"
```

---

### Task 6: DeployReactiveAdapterV3.s.sol

**Files:**
- Create: `script/deploy/DeployReactiveAdapterV3.s.sol`

**Step 1: Create DeployReactiveAdapterV3.s.sol**

This mirrors the existing `scripts/deploy-reactive-testnet.sh` but as a Forge script. It deploys the ReactiveHookAdapter on Sepolia and ThetaSwapReactive on Reactive Lasna.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {ReactiveHookAdapter} from
    "../../src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol";
import {Accounts, initAccounts} from "../types/Accounts.sol";
import {SEPOLIA} from "../utils/Deployments.sol";

contract DeployReactiveAdapterV3Script is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);

        // Sepolia callback proxy (Reactive Network infrastructure)
        address callbackProxy = vm.envAddress("SEPOLIA_CALLBACK_PROXY");

        vm.startBroadcast(accounts.deployer.privateKey);
        ReactiveHookAdapter adapter = new ReactiveHookAdapter(callbackProxy);
        vm.stopBroadcast();

        console2.log("ADAPTER_ADDRESS=%s", address(adapter));
        console2.log("Now deploy ThetaSwapReactive on Reactive Lasna:");
        console2.log("  Pass adapter=%s to ThetaSwapReactive constructor", address(adapter));
        console2.log("  Then call registerPool(chainId, v3Pool) on the Reactive contract");
    }
}
```

Note: ThetaSwapReactive deploys on the Reactive Network (different chain), so it needs a separate `forge create` or script invocation with `--rpc-url reactive`. The shell script `scripts/deploy-reactive-testnet.sh` already handles this two-chain deploy — this Forge script handles the Sepolia side, and the shell script or a second Forge script handles the Reactive side.

**Step 2: Verify compilation**

Run: `forge build`
Expected: Compiler run successful

**Step 3: Commit**

```bash
git add script/deploy/DeployReactiveAdapterV3.s.sol
git commit -m "feat(003): DeployReactiveAdapterV3 script — adapter on Sepolia"
```

---

### Task 7: Update Deployments.sol — unichainSepoliaFCIHook resolver

**Files:**
- Modify: `script/utils/Deployments.sol`

**Step 1: Add unichainSepoliaFCIHook function**

Currently FCI hook address is embedded in `unichainSepoliaFCI()` which returns `IFeeConcentrationIndex`. Add a separate address getter so `CreatePoolV4` and `FeeConcentrationIndexBuilder` can both reference it:

```solidity
function unichainSepoliaFCIHook() pure returns (address) {
    return address(0); // TODO: fill after DeployFCIHookV4
}
```

Update `resolveDeployments` to populate `fciIndex` from the hook address:
```solidity
d.fciIndex = IFeeConcentrationIndex(unichainSepoliaFCIHook());
```

**Step 2: Verify compilation**

Run: `forge build`
Expected: Compiler run successful

**Step 3: Commit**

```bash
git add script/utils/Deployments.sol
git commit -m "feat(003): add unichainSepoliaFCIHook resolver to Deployments"
```

---

### Task 8: Update FeeConcentrationIndexBuilder setUp for V4

**Files:**
- Modify: `script/reactive-integration/FeeConcentrationIndexBuilder.s.sol`

**Step 1: Wire V4 path in setUp**

The builder's setUp currently has a TODO for the V4 path. Complete it:

```solidity
} else if (_chainId == UNICHAIN_SEPOLIA) {
    Deployments memory d = resolveDeployments(_chainId, Protocol.UniswapV4);
    (address tokenA, address tokenB) = resolveTokens(_chainId);
    address fciHook = unichainSepoliaFCIHook();

    // Sort tokens for PoolKey
    (address c0, address c1) = tokenA < tokenB
        ? (tokenA, tokenB)
        : (tokenB, tokenA);

    PoolKey memory key = PoolKey({
        currency0: Currency.wrap(c0),
        currency1: Currency.wrap(c1),
        fee: 500,
        tickSpacing: int24(TICK_SPACING),
        hooks: IHooks(fciHook)
    });

    registerV4Pool(scenario, _chainId, key, d.positionManager, d.swapRouter);
    fciIndex = d.fciIndex;
}
```

Add necessary imports: `resolveTokens`, `unichainSepoliaFCIHook`, `Currency`, `IHooks`, `TICK_SPACING`, `registerV4Pool`.

**Step 2: Verify compilation**

Run: `forge build`
Expected: Compiler run successful

**Step 3: Commit**

```bash
git add script/reactive-integration/FeeConcentrationIndexBuilder.s.sol
git commit -m "feat(003): wire V4 path in builder setUp for Unichain Sepolia"
```

---

### Task 9: CompareDeltaPlus.s.sol

**Files:**
- Create: `script/deploy/CompareDeltaPlus.s.sol`

**Step 1: Create CompareDeltaPlus.s.sol**

Read-only script that forks both chains and compares deltaPlus:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {StdAssertions} from "forge-std/StdAssertions.sol";
import {console2} from "forge-std/console2.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IFeeConcentrationIndex} from "../../src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {
    resolveTokens,
    resolveV3,
    SEPOLIA,
    UNICHAIN_SEPOLIA
} from "../utils/Deployments.sol";
import {rpcAlias} from "../../test/reactive-integration/fork/FeeConcentrationIndexFull.fork.t.sol";

contract CompareDeltaPlusScript is Script, StdAssertions {
    function run() public view {
        // Read V4 deltaPlus from Unichain Sepolia
        // (must be called after builder has run on both chains)
        // This is a view-only comparison — forks both chains to read state

        console2.log("=== Differential FCI Comparison ===");

        // V4 side
        // vm.createSelectFork(vm.rpcUrl("unichain_sepolia"));
        // ... read deltaPlus from FCI hook

        // V3 side
        // vm.createSelectFork(vm.rpcUrl("sepolia"));
        // ... read deltaPlus from reactive FCI

        // assertEq(v4Delta, v3Delta, "deltaPlus mismatch V4 vs V3 reactive");
    }
}
```

Note: Full implementation depends on how PoolKey is reconstructed from Deployments on each fork. The skeleton above will be completed once tokens and hooks are deployed and addresses are in Deployments.sol.

**Step 2: Verify compilation**

Run: `forge build`
Expected: Compiler run successful

**Step 3: Commit**

```bash
git add script/deploy/CompareDeltaPlus.s.sol
git commit -m "feat(003): CompareDeltaPlus script skeleton for differential testing"
```

---

### Task 10: differential-test.sh

**Files:**
- Create: `scripts/differential-test.sh`

**Step 1: Create differential-test.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

SCENARIO=${1:-"buildEquilibrium"}
SCRIPT="FeeConcentrationIndexBuilderScript"

echo "=== Differential Test: $SCENARIO ==="

echo "--- V4: Unichain Sepolia (local FCI hook) ---"
forge script "$SCRIPT" --sig "${SCENARIO}()" \
    --broadcast --rpc-url unichain_sepolia

echo "--- V3: Eth Sepolia (reactive adapter) ---"
forge script "$SCRIPT" --sig "${SCENARIO}()" \
    --broadcast --rpc-url sepolia

echo "--- Waiting for reactive callback (30s) ---"
sleep 30

echo "--- Comparing deltaPlus ---"
forge script CompareDeltaPlusScript --sig "run()" --rpc-url sepolia

echo "=== Done ==="
```

**Step 2: Make executable**

Run: `chmod +x scripts/differential-test.sh`

**Step 3: Create crowdout variant**

```bash
#!/usr/bin/env bash
set -euo pipefail

# scripts/differential-test-crowdout.sh
SCRIPT="FeeConcentrationIndexBuilderScript"
BLOCK_WAIT=30

echo "=== Differential Crowdout Test ==="

echo "--- Phase 1 ---"
forge script "$SCRIPT" --sig "buildCrowdoutPhase1()" --broadcast --rpc-url unichain_sepolia
forge script "$SCRIPT" --sig "buildCrowdoutPhase1()" --broadcast --rpc-url sepolia
echo "Waiting ${BLOCK_WAIT}s for next block..."
sleep "$BLOCK_WAIT"

echo "--- Phase 2 ---"
forge script "$SCRIPT" --sig "buildCrowdoutPhase2()" --broadcast --rpc-url unichain_sepolia
forge script "$SCRIPT" --sig "buildCrowdoutPhase2()" --broadcast --rpc-url sepolia
echo "Waiting ${BLOCK_WAIT}s for next block..."
sleep "$BLOCK_WAIT"

echo "--- Phase 3 ---"
TOKEN_A="${TOKEN_A:?Set TOKEN_A from phase 1 output}" \
    forge script "$SCRIPT" --sig "buildCrowdoutPhase3()" --broadcast --rpc-url unichain_sepolia
TOKEN_A="$TOKEN_A" \
    forge script "$SCRIPT" --sig "buildCrowdoutPhase3()" --broadcast --rpc-url sepolia

echo "Waiting ${BLOCK_WAIT}s for reactive callback..."
sleep "$BLOCK_WAIT"

echo "--- Comparing deltaPlus ---"
forge script CompareDeltaPlusScript --sig "run()" --rpc-url sepolia

echo "=== Done ==="
```

**Step 4: Commit**

```bash
git add scripts/differential-test.sh scripts/differential-test-crowdout.sh
git commit -m "feat(003): differential test shell scripts for single + multi-block recipes"
```

---

### Task 11: Foundry remappings for Permit2

**Files:**
- Modify: `foundry.toml`

**Step 1: Check if Permit2 is accessible**

Run: `ls lib/v4-periphery/lib/permit2/src/interfaces/IAllowanceTransfer.sol`

If it exists, add remapping to `foundry.toml`:

```toml
"permit2/=lib/v4-periphery/lib/permit2/",
```

If not, check: `find lib/ -path "*/permit2/src/interfaces/IAllowanceTransfer.sol"`

**Step 2: Verify compilation**

Run: `forge build`
Expected: Compiler run successful

**Step 3: Commit**

```bash
git add foundry.toml
git commit -m "chore(003): add permit2 remapping for FundAccounts script"
```

---

### Task 12: End-to-end dry run (local fork)

**Files:** None (verification only)

**Step 1: Dry-run DeployMockTokens on a local fork**

```bash
forge script DeployMockTokensScript --sig "run()" \
    --fork-url unichain_sepolia -vvvv
```

Expected: Simulation succeeds, logs TOKEN_A and TOKEN_B addresses.

**Step 2: Verify all scripts compile cleanly**

```bash
forge build
```

Expected: Compiler run successful with no errors.

**Step 3: Run existing tests to ensure no regressions**

```bash
forge test --match-path "test/fee-concentration-index/**" -vv
```

Expected: All existing tests pass.
