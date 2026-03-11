# Reactive Network FCI Integration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable FeeConcentrationIndex tracking on Uniswap V3 pools via Reactive Network's cross-chain event monitoring.

**Architecture:** Three-layer system — (1) Reactive Network instance manages subscriptions + pool whitelist, (2) ReactVM processes V3 events and accumulates Collect fees, emitting callbacks for Swap/Mint/Burn, (3) destination-chain adapter receives callbacks and writes to parallel FCI storage using shared parameterized logic.

**Tech Stack:** Solidity ^0.8.26, reactive-lib (AbstractReactive, AbstractCallback, IReactive), Uniswap V3 core interfaces, existing FCI types (FeeConcentrationState, TickRangeRegistry, FeeShareRatio, SyntheticFeeGrowth).

**Design doc:** `docs/plans/2026-03-06-reactive-network-fci-integration-design.md`

---

## Task 0: Install reactive-lib and merge existing worktree code

**Files:**
- Modify: `foundry.toml` (add remapping)
- Merge from: `.worktrees/001-reactive-fci-non-v4-pools-WP01/` (storage mod)
- Merge from: `.worktrees/001-reactive-fci-non-v4-pools-WP02/` (adapt* functions)

**Step 1: Install reactive-lib as a git submodule**

```bash
forge install Reactive-Network/reactive-lib --no-commit
```

**Step 2: Add remapping to foundry.toml**

Add to remappings array:
```toml
"reactive-lib/=lib/reactive-lib/src/",
"@uniswap/v3-core/=lib/v3-core/",
```

Also install v3-core if not present:
```bash
forge install Uniswap/v3-core --no-commit
```

**Step 3: Cherry-pick worktree commits into current branch**

```bash
git cherry-pick 5b01065  # WP01: adapter diamond storage
git cherry-pick 05fd418  # WP01: remove CollectedFees refactor
git cherry-pick a6dd8e5  # WP02: adapt* free functions
```

If conflicts arise, resolve keeping current branch's FCI changes (parameterized wrappers come in Task 1).

**Step 4: Verify build**

Run: `forge build --out out2`
Expected: compiles (existing WP01/WP02 code + reactive-lib)

**Step 5: Commit**

```bash
git add -A && git commit -m "chore: install reactive-lib, v3-core, merge WP01+WP02 worktree code"
```

---

## Task 1: Parameterize FCI storage wrappers

**Files:**
- Modify: `src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol`
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol` (no changes needed — uses no-arg overloads)
- Test: `forge test --match-path "test/fee-concentration-index/*"`

**Step 1: Write the parameterized versions of each wrapper**

In `FeeConcentrationIndexStorageMod.sol`, rename existing functions to accept `FeeConcentrationIndexStorage storage $` as first param, then add no-arg overloads that delegate to `fciStorage()`.

```solidity
// ── Registry wrappers (parameterized) ──

function registerPosition(
    FeeConcentrationIndexStorage storage $,
    PoolId poolId,
    TickRange rk,
    bytes32 positionKey,
    int24 tickLower,
    int24 tickUpper,
    uint128 posLiquidity
) {
    $.registries[poolId].register(rk, positionKey, tickLower, tickUpper, posLiquidity);
}

// No-arg overload — V4 FCI convenience
function registerPosition(
    PoolId poolId,
    TickRange rk,
    bytes32 positionKey,
    int24 tickLower,
    int24 tickUpper,
    uint128 posLiquidity
) {
    registerPosition(fciStorage(), poolId, rk, positionKey, tickLower, tickUpper, posLiquidity);
}

// ── Fee growth baseline wrappers (parameterized) ──

function setFeeGrowthBaseline(FeeConcentrationIndexStorage storage $, PoolId poolId, bytes32 positionKey, uint256 feeGrowth0X128) {
    $.feeGrowthBaseline0[poolId][positionKey] = feeGrowth0X128;
}

function setFeeGrowthBaseline(PoolId poolId, bytes32 positionKey, uint256 feeGrowth0X128) {
    setFeeGrowthBaseline(fciStorage(), poolId, positionKey, feeGrowth0X128);
}

function getFeeGrowthBaseline(FeeConcentrationIndexStorage storage $, PoolId poolId, bytes32 positionKey) view returns (uint256) {
    return $.feeGrowthBaseline0[poolId][positionKey];
}

function getFeeGrowthBaseline(PoolId poolId, bytes32 positionKey) view returns (uint256) {
    return getFeeGrowthBaseline(fciStorage(), poolId, positionKey);
}

function deleteFeeGrowthBaseline(FeeConcentrationIndexStorage storage $, PoolId poolId, bytes32 positionKey) {
    delete $.feeGrowthBaseline0[poolId][positionKey];
}

function deleteFeeGrowthBaseline(PoolId poolId, bytes32 positionKey) {
    deleteFeeGrowthBaseline(fciStorage(), poolId, positionKey);
}

// ── Overlapping ranges (parameterized) ──

function incrementOverlappingRanges(FeeConcentrationIndexStorage storage $, PoolId poolId, int24 tickMin, int24 tickMax) {
    uint256 count = $.registries[poolId].activeRangeCount();
    for (uint256 i; i < count; ++i) {
        bytes32 rkRaw = $.registries[poolId].activeRangeAt(i);
        int24 lower = $.registries[poolId].rangeLowerTick[rkRaw];
        int24 upper = $.registries[poolId].rangeUpperTick[rkRaw];

        if (intersects(lower, upper, tickMin, tickMax)) {
            $.registries[poolId].incrementRangeSwapCount(TickRange.wrap(rkRaw));
        }
    }
}

function incrementOverlappingRanges(PoolId poolId, int24 tickMin, int24 tickMax) {
    incrementOverlappingRanges(fciStorage(), poolId, tickMin, tickMax);
}
```

**Step 2: Update exports**

Add parameterized versions to the import list used by `FeeConcentrationIndex.sol`. The no-arg overloads have the same names, so existing imports work unchanged.

**Step 3: Run existing FCI tests to verify no regression**

Run: `forge test --match-path "test/fee-concentration-index/*" --out out2 -v`
Expected: all 39 tests pass (no-arg overloads preserve exact behavior)

**Step 4: Commit**

```bash
git add src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol
git commit -m "refactor(fci): parameterize storage wrappers — accept storage ref as first arg"
```

---

## Task 2: Types — LogRecordExtMod.sol

**Files:**
- Create: `src/reactive-integration/types/LogRecordExtMod.sol`

**Step 1: Create the type module**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {LogRecord} from "reactive-lib/interfaces/IReactive.sol";

// Protocol-agnostic LogRecord utilities.
// Typed accessors over raw LogRecord fields.
// No V3/V4-specific logic — reusable across any event source.

function isSelfSync(LogRecord calldata log, address self) pure returns (bool) {
    return log._contract == self;
}

function topic0(LogRecord calldata log) pure returns (uint256) {
    return log.topic_0;
}

function emitter(LogRecord calldata log) pure returns (address) {
    return log._contract;
}

function chainId(LogRecord calldata log) pure returns (uint256) {
    return log.chain_id;
}

function blockNumber(LogRecord calldata log) pure returns (uint256) {
    return log.block_number;
}

function decodeTopic1AsAddress(LogRecord calldata log) pure returns (address) {
    return address(uint160(log.topic_1));
}

function decodeTopic2AsInt24(LogRecord calldata log) pure returns (int24) {
    return int24(int256(log.topic_2));
}

function decodeTopic3AsInt24(LogRecord calldata log) pure returns (int24) {
    return int24(int256(log.topic_3));
}
```

**Step 2: Verify build**

Run: `forge build --out out2`
Expected: compiles (depends on reactive-lib LogRecord struct)

**Step 3: Commit**

```bash
git add src/reactive-integration/types/LogRecordExtMod.sol
git commit -m "feat(003): add LogRecordExtMod — protocol-agnostic LogRecord typed accessors"
```

---

## Task 3: Types — CollectedFeesMod.sol

**Files:**
- Create: `src/reactive-integration/types/CollectedFeesMod.sol`

**Step 1: Create the type module**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Accumulated V3 Collect event fees per position.
// Stored in ReactVM state. Consumed on Burn callback.

struct CollectedFees {
    uint256 fee0;
    uint256 fee1;
}

function accumulate(CollectedFees storage self, uint128 amount0, uint128 amount1) {
    self.fee0 += uint256(amount0);
    self.fee1 += uint256(amount1);
}

function clear(CollectedFees storage self) {
    self.fee0 = 0;
    self.fee1 = 0;
}

function isEmpty(CollectedFees memory self) pure returns (bool) {
    return self.fee0 == 0 && self.fee1 == 0;
}

// Derive position key from V3 event fields.
// Matches V3's internal position key: keccak256(owner, tickLower, tickUpper).
function v3PositionKey(address owner, int24 tickLower, int24 tickUpper) pure returns (bytes32) {
    return keccak256(abi.encodePacked(owner, tickLower, tickUpper));
}

using {accumulate, clear} for CollectedFees global;
```

**Step 2: Verify build**

Run: `forge build --out out2`
Expected: compiles

**Step 3: Commit**

```bash
git add src/reactive-integration/types/CollectedFeesMod.sol
git commit -m "feat(003): add CollectedFeesMod — fee accumulation type for ReactVM state"
```

---

## Task 4: Types — V3EventDecoderMod.sol

**Files:**
- Create: `src/reactive-integration/types/V3EventDecoderMod.sol`
- Depends on: `LogRecordExtMod.sol`, `ReactiveCallbackDataMod.sol`

**Step 1: Create the decoder module**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {LogRecord} from "reactive-lib/interfaces/IReactive.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {V3SwapData, V3MintData, V3BurnData, V3CollectData} from "./ReactiveCallbackDataMod.sol";
import {decodeTopic1AsAddress} from "./LogRecordExtMod.sol";

// V3-specific event decoders. Extracts typed structs from raw LogRecord fields.
// Each V3 event has a known layout of indexed topics and ABI-encoded data.

// V3 event signatures
uint256 constant V3_SWAP_SIG = uint256(keccak256("Swap(address,address,int256,int256,uint160,uint128,int24)"));
uint256 constant V3_MINT_SIG = uint256(keccak256("Mint(address,address,int24,int24,uint128,uint256,uint256)"));
uint256 constant V3_BURN_SIG = uint256(keccak256("Burn(address,int24,int24,uint128,uint256,uint256)"));
uint256 constant V3_COLLECT_SIG = uint256(keccak256("Collect(address,address,int24,int24,uint128,uint128)"));

function decodeV3Swap(LogRecord calldata log) pure returns (V3SwapData memory) {
    // Swap data layout: (int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick)
    (, , , , int24 tick) = abi.decode(log.data, (int256, int256, uint160, uint128, int24));
    return V3SwapData({
        pool: IUniswapV3Pool(log._contract),
        tick: tick
    });
}

function decodeV3Mint(LogRecord calldata log) pure returns (V3MintData memory) {
    // topic_1: sender (indexed), topic_2: owner (indexed — actually topic_1 is sender, owner is in data for Mint)
    // V3 Mint: topic_1 = sender (indexed). owner, tickLower, tickUpper in data.
    // Actually: Mint(address sender, address owner, int24 tickLower, int24 tickUpper, uint128 amount, uint256 amount0, uint256 amount1)
    // sender is indexed (topic_1). Rest in data.
    (address owner, int24 tickLower, int24 tickUpper, uint128 liquidity, , ) =
        abi.decode(log.data, (address, int24, int24, uint128, uint256, uint256));
    return V3MintData({
        pool: IUniswapV3Pool(log._contract),
        owner: owner,
        tickLower: tickLower,
        tickUpper: tickUpper,
        liquidity: liquidity
    });
}

function decodeV3Burn(LogRecord calldata log) pure returns (V3BurnData memory) {
    // Burn(address owner, int24 tickLower, int24 tickUpper, uint128 amount, uint256 amount0, uint256 amount1)
    // owner is indexed (topic_1). Rest in data.
    address owner = decodeTopic1AsAddress(log);
    (int24 tickLower, int24 tickUpper, uint128 liquidity, , ) =
        abi.decode(log.data, (int24, int24, uint128, uint256, uint256));
    return V3BurnData({
        pool: IUniswapV3Pool(log._contract),
        owner: owner,
        tickLower: tickLower,
        tickUpper: tickUpper,
        liquidity: liquidity
    });
}

function decodeV3Collect(LogRecord calldata log) pure returns (V3CollectData memory) {
    // Collect(address owner, address recipient, int24 tickLower, int24 tickUpper, uint128 amount0, uint128 amount1)
    // owner is indexed (topic_1). Rest in data.
    address owner = decodeTopic1AsAddress(log);
    (, int24 tickLower, int24 tickUpper, uint128 feeAmount0, uint128 feeAmount1) =
        abi.decode(log.data, (address, int24, int24, uint128, uint128));
    return V3CollectData({
        pool: IUniswapV3Pool(log._contract),
        owner: owner,
        tickLower: tickLower,
        tickUpper: tickUpper,
        feeAmount0: feeAmount0,
        feeAmount1: feeAmount1
    });
}
```

**Note:** V3 event indexed field layouts must be verified against actual V3 source. The decoding above is based on the V3 pool contract events. Verify with `grep "event Swap\|event Mint\|event Burn\|event Collect" lib/v3-core/contracts/interfaces/pool/IUniswapV3PoolEvents.sol`.

**Step 2: Verify build**

Run: `forge build --out out2`

**Step 3: Commit**

```bash
git add src/reactive-integration/types/V3EventDecoderMod.sol
git commit -m "feat(003): add V3EventDecoderMod — decode LogRecord into V3 typed structs"
```

---

## Task 5: Modules — ReactVmStorageMod.sol

**Files:**
- Create: `src/reactive-integration/modules/ReactVmStorageMod.sol`
- Depends on: `CollectedFeesMod.sol`

**Step 1: Create ReactVM-side storage**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {CollectedFees} from "../types/CollectedFeesMod.sol";

// ReactVM-side state. Isolated from destination chain.
// No diamond storage needed — ReactVM is a standard EVM instance.
// This state accumulates Collect fees until consumed by Burn.

struct ReactVmStorage {
    // Accumulated Collect fees per V3 position.
    // Key: v3PositionKey(owner, tickLower, tickUpper) scoped by pool.
    mapping(address => mapping(bytes32 => CollectedFees)) collectedFees;
    // Pool whitelist synced from RN instance via self-subscription.
    mapping(uint256 => mapping(address => bool)) poolWhitelist;
}

// Simple storage — no diamond slot needed in ReactVM (single contract instance).
ReactVmStorage constant _reactVmStorage;
// NOTE: The above won't work. Use a storage pattern:

bytes32 constant REACT_VM_STORAGE_SLOT = keccak256("ThetaSwapReactive.vm.storage");

function reactVmStorage() pure returns (ReactVmStorage storage s) {
    bytes32 slot = REACT_VM_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}

function isWhitelisted(uint256 chainId_, address pool) view returns (bool) {
    return reactVmStorage().poolWhitelist[chainId_][pool];
}

function setWhitelisted(uint256 chainId_, address pool, bool status) {
    reactVmStorage().poolWhitelist[chainId_][pool] = status;
}

function getCollectedFees(address pool, bytes32 posKey) view returns (CollectedFees storage) {
    return reactVmStorage().collectedFees[pool][posKey];
}

function clearCollectedFees(address pool, bytes32 posKey) {
    delete reactVmStorage().collectedFees[pool][posKey];
}
```

**Step 2: Verify build**

Run: `forge build --out out2`

**Step 3: Commit**

```bash
git add src/reactive-integration/modules/ReactVmStorageMod.sol
git commit -m "feat(003): add ReactVmStorageMod — ReactVM state for fee accumulation and pool whitelist"
```

---

## Task 6: Modules — SubscriptionMod.sol

**Files:**
- Create: `src/reactive-integration/modules/SubscriptionMod.sol`
- Depends on: reactive-lib `ISubscriptionService`

**Step 1: Create subscription management module**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {ISubscriptionService} from "reactive-lib/interfaces/ISubscriptionService.sol";
import {V3_SWAP_SIG, V3_MINT_SIG, V3_BURN_SIG, V3_COLLECT_SIG} from "../types/V3EventDecoderMod.sol";

uint256 constant REACTIVE_IGNORE = 0xa65f96fc951c35ead38878e0f0b7a3c744a6f5ccc1476b313353ce31712313ad;

// Subscribe to all 4 V3 event types for a given pool on a given chain.
function subscribeV3Pool(
    ISubscriptionService service,
    uint256 chainId_,
    address pool
) {
    service.subscribe(chainId_, pool, V3_SWAP_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    service.subscribe(chainId_, pool, V3_MINT_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    service.subscribe(chainId_, pool, V3_BURN_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    service.subscribe(chainId_, pool, V3_COLLECT_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
}

// Unsubscribe from all 4 V3 event types for a given pool.
function unsubscribeV3Pool(
    ISubscriptionService service,
    uint256 chainId_,
    address pool
) {
    service.unsubscribe(chainId_, pool, V3_SWAP_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    service.unsubscribe(chainId_, pool, V3_MINT_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    service.unsubscribe(chainId_, pool, V3_BURN_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    service.unsubscribe(chainId_, pool, V3_COLLECT_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
}
```

**Step 2: Verify build**

Run: `forge build --out out2`

**Step 3: Commit**

```bash
git add src/reactive-integration/modules/SubscriptionMod.sol
git commit -m "feat(003): add SubscriptionMod — subscribe/unsubscribe 4 V3 event types per pool"
```

---

## Task 7: Modules — DebtMod.sol

**Files:**
- Create: `src/reactive-integration/modules/DebtMod.sol`

**Step 1: Create debt management module**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IPayable} from "reactive-lib/interfaces/IPayable.sol";

address constant SYSTEM_CONTRACT = 0x0000000000000000000000000000000000fffFfF;

// Pay outstanding subscription debt from received ETH/REACT.
// Called from receive() fallback. Funding-source agnostic.
function coverDebt() {
    uint256 debt = IPayable(SYSTEM_CONTRACT).debt(address(this));
    if (debt == 0) return;
    uint256 payment = debt <= address(this).balance ? debt : address(this).balance;
    if (payment == 0) return;
    (bool success,) = payable(SYSTEM_CONTRACT).call{value: payment}("");
    if (!success) revert DebtPaymentFailed();
}

error DebtPaymentFailed();
```

**Step 2: Verify build**

Run: `forge build --out out2`

**Step 3: Commit**

```bash
git add src/reactive-integration/modules/DebtMod.sol
git commit -m "feat(003): add DebtMod — auto-debt coverage free function"
```

---

## Task 8: Modules — ReactiveAuthMod.sol

**Files:**
- Create: `src/reactive-integration/adapters/uniswapV3/ReactiveAuthMod.sol`

**Step 1: Create auth module**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Auth checks for ReactiveHookAdapter callback functions.
// No modifier keyword — inline revert via free functions. SCOP compliant.

error UnauthorizedCaller(address caller);
error InvalidRvmId(address provided, address expected);

function requireAuthorized(address caller, mapping(address => bool) storage authorizedCallers) view {
    if (!authorizedCallers[caller]) revert UnauthorizedCaller(caller);
}

function requireRvmId(address provided, address expected) pure {
    if (provided != expected) revert InvalidRvmId(provided, expected);
}
```

**Step 2: Verify build**

Run: `forge build --out out2`

**Step 3: Commit**

```bash
git add src/reactive-integration/adapters/uniswapV3/ReactiveAuthMod.sol
git commit -m "feat(003): add ReactiveAuthMod — callback auth checks as free functions"
```

---

## Task 9: Modules — ReactLogicMod.sol

**Files:**
- Create: `src/reactive-integration/modules/ReactLogicMod.sol`
- Depends on: `LogRecordExtMod`, `V3EventDecoderMod`, `ReactVmStorageMod`, `CollectedFeesMod`, `ReactiveCallbackDataMod`

**Step 1: Create the ReactVM routing and processing module**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {LogRecord} from "reactive-lib/interfaces/IReactive.sol";
import {
    isSelfSync, topic0, emitter, chainId
} from "../types/LogRecordExtMod.sol";
import {
    V3_SWAP_SIG, V3_MINT_SIG, V3_BURN_SIG, V3_COLLECT_SIG,
    decodeV3Swap, decodeV3Mint, decodeV3Burn, decodeV3Collect
} from "../types/V3EventDecoderMod.sol";
import {V3SwapData, V3MintData, V3BurnData, V3CollectData} from "../types/ReactiveCallbackDataMod.sol";
import {CollectedFees, v3PositionKey} from "../types/CollectedFeesMod.sol";
import {
    isWhitelisted, setWhitelisted,
    getCollectedFees, clearCollectedFees
} from "./ReactVmStorageMod.sol";

// Event emitted by ReactVM to trigger destination chain callback.
// Must match reactive-lib's Callback event signature.
event Callback(uint256 indexed chainId, address indexed target, uint256 gasLimit, bytes payload);

// Self-sync event signatures (emitted by RN instance, consumed by ReactVM)
uint256 constant POOL_REGISTERED_SIG = uint256(keccak256("PoolRegistered(uint256,address)"));
uint256 constant POOL_UNREGISTERED_SIG = uint256(keccak256("PoolUnregistered(uint256,address)"));

uint256 constant CALLBACK_GAS_LIMIT = 300_000;

// Main routing function — called by ThetaSwapReactive.react().
function processLog(
    LogRecord calldata log,
    address self,
    address adapter
) {
    // Self-subscription sync: pool whitelist updates from RN instance
    if (isSelfSync(log, self)) {
        _handleSelfSync(log);
        return;
    }

    // Skip events from non-whitelisted pools
    if (!isWhitelisted(chainId(log), emitter(log))) return;

    uint256 sig = topic0(log);

    if (sig == V3_SWAP_SIG) {
        V3SwapData memory data = decodeV3Swap(log);
        emit Callback(
            chainId(log), adapter, CALLBACK_GAS_LIMIT,
            abi.encodeWithSelector(bytes4(keccak256("onV3Swap(V3SwapData)")), data)
        );
    } else if (sig == V3_MINT_SIG) {
        V3MintData memory data = decodeV3Mint(log);
        emit Callback(
            chainId(log), adapter, CALLBACK_GAS_LIMIT,
            abi.encodeWithSelector(bytes4(keccak256("onV3Mint(V3MintData)")), data)
        );
    } else if (sig == V3_COLLECT_SIG) {
        // Accumulate fees in ReactVM state — NO callback
        V3CollectData memory data = decodeV3Collect(log);
        bytes32 posKey = v3PositionKey(data.owner, data.tickLower, data.tickUpper);
        CollectedFees storage fees = getCollectedFees(address(data.pool), posKey);
        fees.accumulate(data.feeAmount0, data.feeAmount1);
    } else if (sig == V3_BURN_SIG) {
        V3BurnData memory data = decodeV3Burn(log);
        bytes32 posKey = v3PositionKey(data.owner, data.tickLower, data.tickUpper);
        // Read and clear accumulated fees
        CollectedFees storage fees = getCollectedFees(address(data.pool), posKey);
        uint256 fee0 = fees.fee0;
        uint256 fee1 = fees.fee1;
        clearCollectedFees(address(data.pool), posKey);
        emit Callback(
            chainId(log), adapter, CALLBACK_GAS_LIMIT,
            abi.encodeWithSelector(
                bytes4(keccak256("onV3Burn(V3BurnData,uint256,uint256)")),
                data, fee0, fee1
            )
        );
    }
}

function _handleSelfSync(LogRecord calldata log) {
    uint256 sig = topic0(log);
    if (sig == POOL_REGISTERED_SIG) {
        (uint256 chainId_, address pool) = abi.decode(log.data, (uint256, address));
        setWhitelisted(chainId_, pool, true);
    } else if (sig == POOL_UNREGISTERED_SIG) {
        (uint256 chainId_, address pool) = abi.decode(log.data, (uint256, address));
        setWhitelisted(chainId_, pool, false);
    }
}
```

**Step 2: Verify build**

Run: `forge build --out out2`

**Step 3: Commit**

```bash
git add src/reactive-integration/modules/ReactLogicMod.sol
git commit -m "feat(003): add ReactLogicMod — ReactVM event routing, fee accumulation, callback emission"
```

---

## Task 10: Contract — ThetaSwapReactive.sol

**Files:**
- Create: `src/reactive-integration/ThetaSwapReactive.sol`
- Depends on: all modules from Tasks 5-9

**Step 1: Create the thin reactive contract shell**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {LogRecord} from "reactive-lib/interfaces/IReactive.sol";
import {ISubscriptionService} from "reactive-lib/interfaces/ISubscriptionService.sol";
import {processLog} from "./modules/ReactLogicMod.sol";
import {subscribeV3Pool, unsubscribeV3Pool} from "./modules/SubscriptionMod.sol";
import {coverDebt, SYSTEM_CONTRACT} from "./modules/DebtMod.sol";
import {setWhitelisted} from "./modules/ReactVmStorageMod.sol";

// Self-sync events — emitted on RN instance, consumed by ReactVM
event PoolRegistered(uint256 indexed chainId, address indexed pool);
event PoolUnregistered(uint256 indexed chainId, address indexed pool);

// Thin shell — all logic lives in Mod files.
// Dual-instance: RN manages subscriptions, ReactVM processes events.
contract ThetaSwapReactive {
    address immutable owner;
    address immutable adapter;
    ISubscriptionService immutable service;
    bool immutable vm;

    error OnlyOwner();
    error OnlyReactVM();
    error OnlyRN();

    constructor(address adapter_, address service_) payable {
        owner = msg.sender;
        adapter = adapter_;
        service = ISubscriptionService(service_);

        // Detect which instance we are
        uint256 size;
        assembly { size := extcodesize(0x0000000000000000000000000000000000fffFfF) }
        vm = size == 0;

        // RN instance: subscribe to own events for whitelist sync
        if (!vm) {
            service.subscribe(
                block.chainid,
                address(this),
                uint256(keccak256("PoolRegistered(uint256,address)")),
                REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE
            );
            service.subscribe(
                block.chainid,
                address(this),
                uint256(keccak256("PoolUnregistered(uint256,address)")),
                REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE
            );
        }
    }

    // ── ReactVM entry point ──

    function react(LogRecord calldata log) external {
        if (!vm) revert OnlyReactVM();
        processLog(log, address(this), adapter);
    }

    // ── RN instance: pool management ──

    function registerPool(uint256 chainId_, address pool) external {
        if (msg.sender != owner) revert OnlyOwner();
        if (vm) revert OnlyRN();
        subscribeV3Pool(service, chainId_, pool);
        emit PoolRegistered(chainId_, pool);
    }

    function unregisterPool(uint256 chainId_, address pool) external {
        if (msg.sender != owner) revert OnlyOwner();
        if (vm) revert OnlyRN();
        unsubscribeV3Pool(service, chainId_, pool);
        emit PoolUnregistered(chainId_, pool);
    }

    // ── Funding ──

    receive() external payable {
        coverDebt();
    }
}
```

Note: `REACTIVE_IGNORE` must be imported from `SubscriptionMod.sol`.

**Step 2: Verify build**

Run: `forge build --out out2`

**Step 3: Commit**

```bash
git add src/reactive-integration/ThetaSwapReactive.sol
git commit -m "feat(003): add ThetaSwapReactive — thin reactive contract shell with pool management"
```

---

## Task 11: Contract — ReactiveHookAdapter.sol (rewrite)

**Files:**
- Modify: `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol`
- Depends on: `ReactiveAuthMod`, `ReactiveHookAdapterStorageMod`, parameterized FCI wrappers, `adapt*` functions, `PoolKeyExtMod`, `SyntheticFeeGrowthMod`

**Step 1: Rewrite as contract shell with auth + adapt* + parameterized FCI**

The existing file has only free functions (`adaptV3Swap`, etc.). Keep those. Add a contract that uses them:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";

import {V3SwapData, V3MintData, V3BurnData} from "../../types/ReactiveCallbackDataMod.sol";
import {adaptV3Swap, adaptV3Mint, adaptV3Burn} from "./ReactiveHookAdapterTranslateMod.sol";
import {requireAuthorized, requireRvmId} from "./ReactiveAuthMod.sol";
import {reactiveFciStorage} from "./ReactiveHookAdapterStorageMod.sol";
import {
    FeeConcentrationIndexStorage,
    registerPosition, setFeeGrowthBaseline, getFeeGrowthBaseline, deleteFeeGrowthBaseline,
    incrementOverlappingRanges
} from "../../../fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {TickRange, fromTicks} from "../../../fee-concentration-index/types/TickRangeMod.sol";
import {FeeShareRatio} from "../../../fee-concentration-index/types/FeeShareRatioMod.sol";
import {SyntheticFeeGrowth, fromBurnAmount, toFeeShareRatio} from "../../types/SyntheticFeeGrowthMod.sol";
import {SwapCount} from "../../../fee-concentration-index/types/SwapCountMod.sol";
import {BlockCount} from "../../../fee-concentration-index/types/BlockCountMod.sol";
import {derivePoolAndPosition, sortTicks} from "../../../libraries/HookUtilsMod.sol";
import {v3PositionKey} from "../../types/CollectedFeesMod.sol";
import {fromV3Pool} from "../../libraries/PoolKeyExtMod.sol";

contract ReactiveHookAdapter {
    address immutable rvmId;
    address immutable owner;
    mapping(address => bool) public authorizedCallers;

    event AuthorizedCallerUpdated(address indexed caller, bool authorized);

    error OnlyOwner();

    constructor(address callbackProxy) {
        owner = msg.sender;
        rvmId = msg.sender;  // rvm_id = deployer EOA
        authorizedCallers[callbackProxy] = true;
    }

    function setAuthorized(address caller, bool authorized) external {
        if (msg.sender != owner) revert OnlyOwner();
        authorizedCallers[caller] = authorized;
        emit AuthorizedCallerUpdated(caller, authorized);
    }

    function onV3Swap(V3SwapData calldata data) external {
        requireAuthorized(msg.sender, authorizedCallers);
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolKey memory key = fromV3Pool(data.pool, address(this));
        PoolId poolId = PoolIdLibrary.toId(key);
        incrementOverlappingRanges($, poolId, data.tick, data.tick);
    }

    function onV3Mint(V3MintData calldata data) external {
        requireAuthorized(msg.sender, authorizedCallers);
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolKey memory key = fromV3Pool(data.pool, address(this));
        PoolId poolId = PoolIdLibrary.toId(key);
        bytes32 posKey = v3PositionKey(data.owner, data.tickLower, data.tickUpper);
        TickRange rk = fromTicks(data.tickLower, data.tickUpper);
        registerPosition($, poolId, rk, posKey, data.tickLower, data.tickUpper, data.liquidity);
        setFeeGrowthBaseline($, poolId, posKey, 0);
        $.fciState[poolId].incrementPos();
    }

    function onV3Burn(V3BurnData calldata data, uint256 fee0, uint256 fee1) external {
        requireAuthorized(msg.sender, authorizedCallers);
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolKey memory key = fromV3Pool(data.pool, address(this));
        PoolId poolId = PoolIdLibrary.toId(key);
        bytes32 posKey = v3PositionKey(data.owner, data.tickLower, data.tickUpper);

        (, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) =
            $.registries[poolId].deregister(posKey, data.liquidity);

        if (!swapLifetime.isZero()) {
            SyntheticFeeGrowth posDelta = fromBurnAmount(fee0, data.liquidity);
            SyntheticFeeGrowth rangeDelta = fromBurnAmount(fee0, totalRangeLiq);
            FeeShareRatio xk = toFeeShareRatio(posDelta, rangeDelta);
            uint256 xSquaredQ128 = xk.square();
            $.fciState[poolId].addTerm(blockLifetime, xSquaredQ128);
        }

        $.fciState[poolId].decrementPos();
        deleteFeeGrowthBaseline($, poolId, posKey);
    }

    function getIndex(PoolKey calldata key) external view returns (uint128 indexA, uint256 thetaSum, uint256 posCount) {
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolId poolId = PoolIdLibrary.toId(key);
        indexA = $.fciState[poolId].toIndexA();
        thetaSum = $.fciState[poolId].thetaSum;
        posCount = $.fciState[poolId].posCount;
    }
}
```

**Step 2: Rename existing ReactiveHookAdapter.sol to ReactiveHookAdapterTranslateMod.sol**

The existing file with `adaptV3Swap`/`adaptV3Mint`/`adaptV3Burn` free functions becomes the translate module.

```bash
mv src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol \
   src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapterTranslateMod.sol
```

Then create the new `ReactiveHookAdapter.sol` with the contract above.

**Step 3: Verify build**

Run: `forge build --out out2`

**Step 4: Run all FCI tests (regression check)**

Run: `forge test --match-path "test/fee-concentration-index/*" --out out2 -v`
Expected: all 39 tests pass

**Step 5: Commit**

```bash
git add src/reactive-integration/adapters/uniswapV3/
git commit -m "feat(003): add ReactiveHookAdapter contract — auth, adapt*, parameterized FCI on reactive slot"
```

---

## Task 12: Build verification and full test run

**Step 1: Full build**

Run: `forge build --out out2`
Expected: zero errors

**Step 2: All existing tests**

Run: `forge test --out out2 -v`
Expected: all tests pass (FCI + any reactive kontrol proofs)

**Step 3: Commit any final fixes**

**Step 4: Push and create PR on upstream targeting uh8**

```bash
git push origin 001-fci-coprimary-diamond
git push upstream 001-fci-coprimary-diamond
gh pr create --repo wvs-finance/ThetaSwap-core --head 001-fci-coprimary-diamond --base uh8 \
  --title "feat(003): Reactive Network FCI integration — 3-layer architecture" \
  --body "..."
```

---

## Dependency Graph

```
Task 0: install reactive-lib + merge worktrees
  └─ Task 1: parameterize FCI storage wrappers
  └─ Task 2: LogRecordExtMod (no deps)
  └─ Task 3: CollectedFeesMod (no deps)
  └─ Task 4: V3EventDecoderMod (depends: Task 2, Task 3)
  └─ Task 5: ReactVmStorageMod (depends: Task 3)
  └─ Task 6: SubscriptionMod (depends: Task 4 for sigs)
  └─ Task 7: DebtMod (no deps)
  └─ Task 8: ReactiveAuthMod (no deps)
  └─ Task 9: ReactLogicMod (depends: Tasks 2-5)
  └─ Task 10: ThetaSwapReactive (depends: Tasks 5-7, 9)
  └─ Task 11: ReactiveHookAdapter (depends: Tasks 1, 8, existing adapt*)
  └─ Task 12: Full build + test + PR
```

Tasks 2, 3, 6, 7, 8 can run in parallel (no interdependencies).
