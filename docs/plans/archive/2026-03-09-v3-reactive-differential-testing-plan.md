# V3 Reactive Differential Testing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Run equilibrium, mild, and crowdout FCI scenarios through V3 on Sepolia via Reactive Network, and assert deltaPlus matches the V4 local hook result.

**Architecture:** A V3CallbackRouter contract enables EOA-broadcast V3 interactions. The ReactiveHookAdapter on Sepolia receives event callbacks from the Reactive Network. Fresh pools (fee=3000) on both V3 and V4 ensure clean FCI state. Per-scenario deltaPlus increments are compared.

**Tech Stack:** Solidity 0.8.26, Forge scripts, Uniswap V3/V4 core, Reactive Network (reactive-lib), FeeConcentrationIndex

---

### Task 1: V3CallbackRouter Contract

**Files:**
- Create: `src/reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol`

**Step 1: Write the V3CallbackRouter**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {IUniswapV3MintCallback} from "@uniswap/v3-core/contracts/interfaces/callback/IUniswapV3MintCallback.sol";
import {IUniswapV3SwapCallback} from "@uniswap/v3-core/contracts/interfaces/callback/IUniswapV3SwapCallback.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";

/// @notice Minimal router enabling EOAs to mint/swap on V3 pools via broadcast.
/// Callbacks pull tokens from tx.origin. Not for production — test/script use only.
contract V3CallbackRouter is IUniswapV3MintCallback, IUniswapV3SwapCallback {
    struct CallbackData {
        address token0;
        address token1;
        address payer;
    }

    function mint(
        IUniswapV3Pool pool,
        address recipient,
        int24 tickLower,
        int24 tickUpper,
        uint128 amount
    ) external returns (uint256 amount0, uint256 amount1) {
        bytes memory data = abi.encode(CallbackData({
            token0: pool.token0(),
            token1: pool.token1(),
            payer: msg.sender
        }));
        (amount0, amount1) = pool.mint(recipient, tickLower, tickUpper, amount, data);
    }

    function swap(
        IUniswapV3Pool pool,
        address recipient,
        bool zeroForOne,
        int256 amountSpecified,
        uint160 sqrtPriceLimitX96
    ) external returns (int256 amount0, int256 amount1) {
        bytes memory data = abi.encode(CallbackData({
            token0: pool.token0(),
            token1: pool.token1(),
            payer: msg.sender
        }));
        (amount0, amount1) = pool.swap(recipient, zeroForOne, amountSpecified, sqrtPriceLimitX96, data);
    }

    function uniswapV3MintCallback(uint256 amount0Owed, uint256 amount1Owed, bytes calldata data) external override {
        CallbackData memory cb = abi.decode(data, (CallbackData));
        if (amount0Owed > 0) IERC20(cb.token0).transferFrom(cb.payer, msg.sender, amount0Owed);
        if (amount1Owed > 0) IERC20(cb.token1).transferFrom(cb.payer, msg.sender, amount1Owed);
    }

    function uniswapV3SwapCallback(int256 amount0Delta, int256 amount1Delta, bytes calldata data) external override {
        CallbackData memory cb = abi.decode(data, (CallbackData));
        if (amount0Delta > 0) IERC20(cb.token0).transferFrom(cb.payer, msg.sender, uint256(amount0Delta));
        if (amount1Delta > 0) IERC20(cb.token1).transferFrom(cb.payer, msg.sender, uint256(amount1Delta));
    }
}
```

**Step 2: Verify it compiles**

Run: `forge build --match-path "src/reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol"`
Expected: success

**Step 3: Commit**

```bash
git add src/reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol
git commit -m "feat(003): V3CallbackRouter for EOA mint/swap via broadcast"
```

---

### Task 2: Deploy V3CallbackRouter Script

**Files:**
- Create: `script/deploy/DeployV3CallbackRouter.s.sol`

**Step 1: Write the deploy script**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {V3CallbackRouter} from
    "../../src/reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol";
import {Accounts, initAccounts} from "../types/Accounts.sol";

contract DeployV3CallbackRouterScript is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        vm.startBroadcast(accounts.deployer.privateKey);
        V3CallbackRouter router = new V3CallbackRouter();
        vm.stopBroadcast();
        console2.log("V3_CALLBACK_ROUTER=%s", address(router));
    }
}
```

**Step 2: Deploy on Sepolia**

Run: `source .env && forge script script/deploy/DeployV3CallbackRouter.s.sol --broadcast --rpc-url sepolia -vv`
Expected: `V3_CALLBACK_ROUTER=0x...`

**Step 3: Add address to Deployments.sol**

Modify: `script/utils/Deployments.sol` — add:
```solidity
function sepoliaV3CallbackRouter() pure returns (address) {
    return 0x...; // fill with deployed address
}
```

**Step 4: Commit**

```bash
git add script/deploy/DeployV3CallbackRouter.s.sol script/utils/Deployments.sol
git commit -m "feat(003): deploy V3CallbackRouter on Sepolia"
```

---

### Task 3: Update Scenario.sol for V3 Router

**Files:**
- Modify: `script/types/Scenario.sol:26-32` (Scenario struct)
- Modify: `script/types/Scenario.sol:99-107` (registerV3Pool)
- Modify: `script/types/Scenario.sol:176-197` (mintPosition V3 path)
- Modify: `script/types/Scenario.sol:238-252` (executeSwap V3 path)

**Step 1: Add v3Router to Scenario struct and imports**

Add import at top:
```solidity
import {V3CallbackRouter} from
    "../../src/reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol";
```

Add to Scenario struct:
```solidity
struct Scenario {
    Vm vm;
    mapping(uint256 chainId => PoolKey pool) pools;
    mapping(uint256 chainId => mapping(Protocol => address)) positionManager;
    mapping(uint256 chainId => address) swapRouter;
    mapping(uint256 chainId => uint256[]) tokenIds;
    mapping(uint256 chainId => address) v3Router;  // NEW
}
```

**Step 2: Update registerV3Pool to accept router**

```solidity
function registerV3Pool(
    Scenario storage s,
    uint256 chainId,
    IUniswapV3Pool pool,
    address adapter,
    address router    // NEW
) {
    s.pools[chainId] = fromV3Pool(pool, adapter);
    s.positionManager[chainId][Protocol.UniswapV3] = address(pool);
    s.v3Router[chainId] = router;   // NEW
}
```

**Step 3: Update mintPosition V3 path**

Replace the V3 branch in `mintPosition()`:
```solidity
    if (isUniswapV3(protocol)) {
        IUniswapV3Pool pool = v3Pool(s, chainId);
        V3CallbackRouter router = V3CallbackRouter(s.v3Router[chainId]);
        s.vm.broadcast(pk);
        router.mint(pool, caller, TICK_LOWER, TICK_UPPER, uint128(liquidity));
    }
```

**Step 4: Update executeSwap V3 path**

Replace the V3 branch in `executeSwap()`:
```solidity
    if (isUniswapV3(protocol)) {
        IUniswapV3Pool pool = v3Pool(s, chainId);
        V3CallbackRouter router = V3CallbackRouter(s.v3Router[chainId]);
        uint160 sqrtPriceLimit = zeroForOne
            ? TickMath.MIN_SQRT_PRICE + 1
            : TickMath.MAX_SQRT_PRICE - 1;
        s.vm.broadcast(pk);
        router.swap(pool, caller, zeroForOne, AMOUNT_SPECIFIED, sqrtPriceLimit);
    }
```

**Step 5: Verify compile**

Run: `forge build`
Expected: success (0 errors)

**Step 6: Run existing tests to check no regressions**

Run: `forge test --match-path "test/fee-concentration-index/**" -vv`
Expected: all 38 tests pass

**Step 7: Commit**

```bash
git add script/types/Scenario.sol
git commit -m "feat(003): route V3 mint/swap through V3CallbackRouter in Scenario"
```

---

### Task 4: Add getDeltaPlus to ReactiveHookAdapter

The adapter has `getIndex()` but no `getDeltaPlus()`. We need it for the comparison script.

**Files:**
- Modify: `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol:96-103`

**Step 1: Add getDeltaPlus function**

Add after the existing `getIndex()` function:
```solidity
    function getDeltaPlus(PoolKey calldata key) external view returns (uint128 deltaPlus_) {
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        deltaPlus_ = $.fciState[PoolIdLibrary.toId(key)].deltaPlus();
    }
```

Also add the `deltaPlus` import — check if it's already available via `FeeConcentrationIndexStorageMod.sol`. The `deltaPlus()` function lives on `FeeConcentrationState`. Add import if needed:
```solidity
import {FeeConcentrationState} from
    "../../../fee-concentration-index/types/FeeConcentrationStateMod.sol";
```

**Step 2: Verify compile**

Run: `forge build`
Expected: success

**Step 3: Commit**

```bash
git add src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol
git commit -m "feat(003): add getDeltaPlus to ReactiveHookAdapter"
```

---

### Task 5: Create Fresh Pools (fee=3000)

**Files:**
- Create: `script/deploy/CreateFreshPools.s.sol`

This script creates both a fresh V3 pool and a fresh V4 pool with fee=3000 on Sepolia, so both have clean FCI state.

**Step 1: Write the script**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {IUniswapV3Factory} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {Accounts, initAccounts} from "../types/Accounts.sol";
import {
    resolveTokens,
    ethSepoliaPoolManager,
    ethSepoliaFCIHook,
    SEPOLIA
} from "../utils/Deployments.sol";

// V3 factory on Sepolia
address constant V3_FACTORY = 0x0227628f3F023bb0B980b67D528571c95c6DaC1c;

contract CreateFreshPoolsScript is Script {
    using PoolIdLibrary for PoolKey;

    function run() public {
        Accounts memory accounts = initAccounts(vm);
        (address tokenA, address tokenB) = resolveTokens(SEPOLIA);
        (address t0, address t1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);

        uint160 sqrtPriceX96 = 79228162514264337593543950336; // 1:1

        vm.startBroadcast(accounts.deployer.privateKey);

        // Fresh V3 pool (fee=3000)
        address v3Pool = IUniswapV3Factory(V3_FACTORY).createPool(t0, t1, 3000);
        IUniswapV3Pool(v3Pool).initialize(sqrtPriceX96);

        // Fresh V4 pool (fee=3000, same FCI hook)
        address fciHook = ethSepoliaFCIHook();
        PoolKey memory v4Key = PoolKey({
            currency0: Currency.wrap(t0),
            currency1: Currency.wrap(t1),
            fee: 3000,
            tickSpacing: 10,
            hooks: IHooks(fciHook)
        });
        IPoolManager(ethSepoliaPoolManager()).initialize(v4Key, sqrtPriceX96);

        vm.stopBroadcast();

        console2.log("FRESH_V3_POOL=%s", v3Pool);
        console2.log("FRESH_V4_POOL_ID:");
        console2.logBytes32(PoolId.unwrap(v4Key.toId()));
    }
}
```

**Step 2: Deploy**

Run: `source .env && forge script script/deploy/CreateFreshPools.s.sol --broadcast --rpc-url sepolia -vv`
Expected: both pool addresses printed

**Step 3: Add fresh pool addresses to Deployments.sol**

Add to `script/utils/Deployments.sol`:
```solidity
function sepoliaFreshV3Pool() pure returns (IUniswapV3Pool) {
    return IUniswapV3Pool(0x...); // fill after deploy
}
```

**Step 4: Commit**

```bash
git add script/deploy/CreateFreshPools.s.sol script/utils/Deployments.sol
git commit -m "feat(003): create fresh V3+V4 pools (fee=3000) for differential testing"
```

---

### Task 6: Approve Tokens to V3CallbackRouter + Fresh V3 Pool

**Files:**
- Create: `script/deploy/ApproveV3Router.s.sol`

All 3 accounts need to approve TSA/TSB to the V3CallbackRouter. They also need approvals to the fresh V3 pool for `pool.collect()` (which is called in burnPosition).

**Step 1: Write the script**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {Accounts, initAccounts} from "../types/Accounts.sol";
import {resolveTokens, SEPOLIA} from "../utils/Deployments.sol";

contract ApproveV3RouterScript is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        (address tokenA, address tokenB) = resolveTokens(SEPOLIA);
        address router = vm.envAddress("V3_CALLBACK_ROUTER");

        uint256[3] memory pks = [
            accounts.lpPassive.privateKey,
            accounts.lpSophisticated.privateKey,
            accounts.swapper.privateKey
        ];

        for (uint256 i; i < 3; ++i) {
            vm.startBroadcast(pks[i]);
            IERC20(tokenA).approve(router, type(uint256).max);
            IERC20(tokenB).approve(router, type(uint256).max);
            vm.stopBroadcast();
        }

        console2.log("All 3 accounts approved tokens to V3CallbackRouter");
    }
}
```

**Step 2: Deploy**

Run: `source .env && V3_CALLBACK_ROUTER=0x... forge script script/deploy/ApproveV3Router.s.sol --broadcast --rpc-url sepolia -vv`
Expected: 6 approval transactions

**Step 3: Commit**

```bash
git add script/deploy/ApproveV3Router.s.sol
git commit -m "feat(003): approve tokens to V3CallbackRouter"
```

---

### Task 7: Deploy ReactiveHookAdapter on Sepolia

**Files:**
- Existing: `script/deploy/DeployReactiveAdapterV3.s.sol` (already written)

**Step 1: Deploy**

Run: `source .env && forge script script/deploy/DeployReactiveAdapterV3.s.sol --broadcast --rpc-url sepolia -vv`
Expected: `ADAPTER_ADDRESS=0x...`

**Step 2: Add address to Deployments.sol**

Add to `script/utils/Deployments.sol`:
```solidity
function sepoliaReactiveAdapter() pure returns (address) {
    return 0x...; // fill after deploy
}
```

**Step 3: Commit**

```bash
git add script/utils/Deployments.sol
git commit -m "feat(003): deploy ReactiveHookAdapter on Sepolia"
```

---

### Task 8: Deploy ThetaSwapReactive on Reactive Network + Register Pool

**Files:**
- Create: `script/deploy/DeployThetaSwapReactive.s.sol`

**Step 1: Write the deploy script**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {ThetaSwapReactive} from "../../src/reactive-integration/ThetaSwapReactive.sol";
import {Accounts, initAccounts} from "../types/Accounts.sol";
import {SEPOLIA} from "../utils/Deployments.sol";

// Reactive Network system contract (ISubscriptionService)
address payable constant RN_SERVICE = payable(0x0000000000000000000000000000000000fffFfF);

contract DeployThetaSwapReactiveScript is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        address adapter = vm.envAddress("ADAPTER_ADDRESS");
        address v3Pool = vm.envAddress("FRESH_V3_POOL");

        vm.startBroadcast(accounts.deployer.privateKey);

        ThetaSwapReactive reactive = new ThetaSwapReactive{value: 0.1 ether}(adapter, RN_SERVICE);
        reactive.registerPool(SEPOLIA, v3Pool);

        vm.stopBroadcast();

        console2.log("THETA_SWAP_REACTIVE=%s", address(reactive));
        console2.log("Registered V3 pool %s on chain %d", v3Pool, SEPOLIA);
    }
}
```

**Step 2: Fund deployer on Reactive Network**

The deployer needs RN native tokens. Fund `0xe69228626E4800578D06a93BaaA595f6634A47C3` on Reactive Lasna.

**Step 3: Deploy**

Run: `source .env && ADAPTER_ADDRESS=0x... FRESH_V3_POOL=0x... forge script script/deploy/DeployThetaSwapReactive.s.sol --broadcast --rpc-url reactive -vv`
Expected: `THETA_SWAP_REACTIVE=0x...`

**Step 4: Commit**

```bash
git add script/deploy/DeployThetaSwapReactive.s.sol
git commit -m "feat(003): deploy ThetaSwapReactive on Reactive Network"
```

---

### Task 9: Update Builder with V3/V4 Separate Entry Points

**Files:**
- Modify: `script/reactive-integration/FeeConcentrationIndexBuilder.s.sol`

**Step 1: Update setUp to register both V3 and V4 on Sepolia**

The builder's `setUp()` should register both protocols when on Sepolia. Add V3 registration alongside V4:

```solidity
function setUp() public {
    scenario.vm = vm;
    accounts = initAccounts(vm);
    _chainId = block.chainid;

    (address tokenA, address tokenB) = resolveTokens(_chainId);
    (address c0, address c1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);

    if (_chainId == SEPOLIA) {
        // V4 path
        Deployments memory d = resolveDeployments(_chainId, Protocol.UniswapV4);
        address fciHook = ethSepoliaFCIHook();
        PoolKey memory v4Key = PoolKey({
            currency0: Currency.wrap(c0), currency1: Currency.wrap(c1),
            fee: 3000, tickSpacing: int24(TICK_SPACING), hooks: IHooks(fciHook)
        });
        registerV4Pool(scenario, _chainId, v4Key, d.positionManager, d.swapRouter);

        // V3 path
        IUniswapV3Pool freshV3 = sepoliaFreshV3Pool();
        address adapter = sepoliaReactiveAdapter();
        address router = sepoliaV3CallbackRouter();
        registerV3Pool(scenario, _chainId, freshV3, adapter, router);

        fciIndex = IFeeConcentrationIndex(fciHook);
        reactiveAdapter = ReactiveHookAdapter(adapter);
    }
    // ... UNICHAIN_SEPOLIA branch unchanged
}
```

**Step 2: Add V3-specific build functions**

```solidity
function buildEquilibriumV3() public {
    deltaPlusFactory(scenario, _chainId, Protocol.UniswapV3,
        accounts.lpPassive.privateKey, accounts.lpSophisticated.privateKey,
        accounts.swapper.privateKey, DELTA_EQUILIBRIUM);
    _logDeltaPlusV3("equilibrium");
}

function buildMildV3() public {
    deltaPlusFactory(scenario, _chainId, Protocol.UniswapV3,
        accounts.lpPassive.privateKey, accounts.lpSophisticated.privateKey,
        accounts.swapper.privateKey, DELTA_MILD);
    _logDeltaPlusV3("mild");
}

function buildEquilibriumV4() public {
    deltaPlusFactory(scenario, _chainId, Protocol.UniswapV4,
        accounts.lpPassive.privateKey, accounts.lpSophisticated.privateKey,
        accounts.swapper.privateKey, DELTA_EQUILIBRIUM);
    _logDeltaPlus("equilibrium");
}

function buildMildV4() public {
    deltaPlusFactory(scenario, _chainId, Protocol.UniswapV4,
        accounts.lpPassive.privateKey, accounts.lpSophisticated.privateKey,
        accounts.swapper.privateKey, DELTA_MILD);
    _logDeltaPlus("mild");
}
```

Add V3 crowdout phase functions similarly (buildCrowdoutPhase1V3, etc.).

**Step 3: Add V3 delta plus logger**

```solidity
function _logDeltaPlusV3(string memory label) internal view {
    PoolKey memory k = poolKey(scenario, _chainId);
    // Adapter uses fromV3Pool internally — we query with the V3-derived key
    uint128 dp = reactiveAdapter.getDeltaPlus(k);
    console2.log("[V3 %s] deltaPlus (reactive) = %d", label, uint256(dp));
}
```

**Step 4: Verify compile**

Run: `forge build`
Expected: success

**Step 5: Commit**

```bash
git add script/reactive-integration/FeeConcentrationIndexBuilder.s.sol
git commit -m "feat(003): V3/V4 separate build functions in builder"
```

---

### Task 10: Update CompareDeltaPlus for Same-Chain Comparison

**Files:**
- Modify: `script/deploy/CompareDeltaPlus.s.sol`

**Step 1: Rewrite for single-chain comparison**

The script reads deltaPlus from both the V4 FCI hook and the ReactiveHookAdapter on Sepolia, and asserts they're equal (5% tolerance).

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {StdAssertions} from "forge-std/StdAssertions.sol";
import {console2} from "forge-std/console2.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IFeeConcentrationIndex} from
    "../../src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {ReactiveHookAdapter} from
    "../../src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol";
import {fromV3Pool} from "../../src/reactive-integration/libraries/PoolKeyExtMod.sol";
import {
    resolveTokens,
    ethSepoliaFCIHook,
    sepoliaFreshV3Pool,
    sepoliaReactiveAdapter,
    SEPOLIA
} from "../utils/Deployments.sol";
import "../utils/Constants.sol";

contract CompareDeltaPlusScript is Script, StdAssertions {
    function run() public {
        (address tA, address tB) = resolveTokens(SEPOLIA);
        (address c0, address c1) = tA < tB ? (tA, tB) : (tB, tA);

        // V4 deltaPlus (local hook, fee=3000)
        address fciHook = ethSepoliaFCIHook();
        PoolKey memory v4Key = PoolKey({
            currency0: Currency.wrap(c0), currency1: Currency.wrap(c1),
            fee: 3000, tickSpacing: int24(TICK_SPACING), hooks: IHooks(fciHook)
        });
        uint128 v4Delta = IFeeConcentrationIndex(fciHook).getDeltaPlus(v4Key, false);
        console2.log("[V4] deltaPlus = %d", uint256(v4Delta));

        // V3 deltaPlus (reactive adapter)
        ReactiveHookAdapter adapter = ReactiveHookAdapter(sepoliaReactiveAdapter());
        PoolKey memory v3Key = fromV3Pool(sepoliaFreshV3Pool(), address(adapter));
        uint128 v3Delta = adapter.getDeltaPlus(v3Key);
        console2.log("[V3] deltaPlus = %d", uint256(v3Delta));

        // Compare
        assertApproxEqRel(
            uint256(v4Delta), uint256(v3Delta), 0.05e18,
            "deltaPlus mismatch: V4 local vs V3 reactive"
        );
        console2.log("=== PASS: deltaPlus matches (5%% tolerance) ===");
    }
}
```

**Step 2: Verify compile**

Run: `forge build`
Expected: success

**Step 3: Commit**

```bash
git add script/deploy/CompareDeltaPlus.s.sol
git commit -m "feat(003): single-chain CompareDeltaPlus for V4 vs V3 reactive"
```

---

### Task 11: Update Shell Orchestrator

**Files:**
- Modify: `scripts/differential-test.sh`

**Step 1: Rewrite for same-chain V3+V4 flow**

```bash
#!/usr/bin/env bash
set -euo pipefail

source .env

RPC="sepolia"
SIG_V4=$1  # e.g. buildEquilibriumV4
SIG_V3=$2  # e.g. buildEquilibriumV3

echo "=== Running V4 scenario: $SIG_V4 ==="
forge script script/reactive-integration/FeeConcentrationIndexBuilder.s.sol \
    --sig "${SIG_V4}()" --broadcast --rpc-url "$RPC" -vv

echo "=== Running V3 scenario: $SIG_V3 ==="
forge script script/reactive-integration/FeeConcentrationIndexBuilder.s.sol \
    --sig "${SIG_V3}()" --broadcast --rpc-url "$RPC" -vv

echo "=== Waiting 60s for Reactive Network callback ==="
sleep 60

echo "=== Comparing deltaPlus ==="
forge script script/deploy/CompareDeltaPlus.s.sol \
    --rpc-url "$RPC" -vv

echo "=== DONE ==="
```

Usage:
```bash
./scripts/differential-test.sh buildEquilibriumV4 buildEquilibriumV3
./scripts/differential-test.sh buildMildV4 buildMildV3
```

**Step 2: Commit**

```bash
git add scripts/differential-test.sh
git commit -m "feat(003): update differential test shell for same-chain V3+V4"
```

---

### Task 12: Run Differential Tests

**No files created — execution only.**

**Step 1: Run V4 equilibrium on fresh pool**

Run: `source .env && forge script script/reactive-integration/FeeConcentrationIndexBuilder.s.sol --sig "buildEquilibriumV4()" --broadcast --rpc-url sepolia -vv`
Expected: success, deltaPlus logged

**Step 2: Run V3 equilibrium on fresh pool**

Run: `source .env && forge script script/reactive-integration/FeeConcentrationIndexBuilder.s.sol --sig "buildEquilibriumV3()" --broadcast --rpc-url sepolia -vv`
Expected: success, V3 events emitted on Sepolia

**Step 3: Wait for Reactive Network callbacks (~60s)**

Run: `sleep 60`

**Step 4: Compare deltaPlus**

Run: `source .env && forge script script/deploy/CompareDeltaPlus.s.sol --rpc-url sepolia -vv`
Expected: `=== PASS: deltaPlus matches ===`

**Step 5: Repeat for mild scenario**

Same flow with `buildMildV4()` / `buildMildV3()`.

**Step 6: Repeat for crowdout (3 phases)**

Same flow with phased V4/V3 functions, with block gaps between phases.

**Step 7: Commit final state**

```bash
git add -A
git commit -m "feat(003): differential testing complete — V4 local == V3 reactive"
```
