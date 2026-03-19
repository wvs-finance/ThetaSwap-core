# Unified FCI Hook Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Merge V3 reactive callback handling into the FeeConcentrationIndex hook using composable hookData bitmask flags, eliminating the standalone ReactiveHookAdapter.

**Architecture:** Each IHooks function reads a `uint8 flags` from hookData (via CalldataReader.readU8) to dispatch between V4 native, reactive V3, and future combos. The FCI contract gains callback auth (authorizedCallers, rvmId) and IPayer (pay, receive). ReactLogicMod retargets callbacks from adapter → FCI hook with IHooks-encoded payloads.

**Tech Stack:** Solidity ^0.8.26, Uniswap V4 (IHooks, PoolKey, PoolId), Angstrom CalldataReader, Reactive Network (IReactive, callback proxy), Forge

---

### Task 1: HookData flag constants + codec module

**Files:**
- Create: `src/fee-concentration-index/types/HookDataFlagsMod.sol`
- Test: `test/fee-concentration-index/unit/HookDataFlags.unit.t.sol`

**Step 1: Write the failing test**

Create `test/fee-concentration-index/unit/HookDataFlags.unit.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    REACTIVE_FLAG, V3_FLAG, V4_FLAG,
    isReactive, isV3, isV4,
    encodeSwapHookData, decodeSwapHookData,
    encodeMintHookData, decodeMintHookData,
    encodeBurnHookData, decodeBurnHookData
} from "../../src/fee-concentration-index/types/HookDataFlagsMod.sol";

contract HookDataFlagsTest is Test {
    function test_flagConstants_areSingleBits() public pure {
        assertEq(REACTIVE_FLAG, 0x01);
        assertEq(V3_FLAG, 0x02);
        assertEq(V4_FLAG, 0x04);
    }

    function test_flagChecks_composable() public pure {
        uint8 reactiveV3 = REACTIVE_FLAG | V3_FLAG; // 0x03
        assertTrue(isReactive(reactiveV3));
        assertTrue(isV3(reactiveV3));
        assertFalse(isV4(reactiveV3));
    }

    function test_swapHookData_roundtrip() public pure {
        uint8 flags = REACTIVE_FLAG | V3_FLAG;
        int24 tickBefore = -42;
        int24 tickAfter = 17;
        bytes memory encoded = encodeSwapHookData(flags, tickBefore, tickAfter);
        (uint8 f, int24 tb, int24 ta) = decodeSwapHookData(encoded);
        assertEq(f, flags);
        assertEq(tb, tickBefore);
        assertEq(ta, tickAfter);
    }

    function test_mintHookData_roundtrip() public pure {
        uint8 flags = REACTIVE_FLAG | V3_FLAG;
        address owner = address(0xBEEF);
        int24 tickLower = -60;
        int24 tickUpper = 60;
        uint128 liquidity = 10000;
        bytes memory encoded = encodeMintHookData(flags, owner, tickLower, tickUpper, liquidity);
        (uint8 f, address o, int24 tl, int24 tu, uint128 liq) = decodeMintHookData(encoded);
        assertEq(f, flags);
        assertEq(o, owner);
        assertEq(tl, tickLower);
        assertEq(tu, tickUpper);
        assertEq(liq, liquidity);
    }

    function test_burnHookData_roundtrip() public pure {
        uint8 flags = REACTIVE_FLAG | V3_FLAG;
        address owner = address(0xCAFE);
        int24 tickLower = -120;
        int24 tickUpper = 120;
        uint128 liquidity = 5000;
        bytes memory encoded = encodeBurnHookData(flags, owner, tickLower, tickUpper, liquidity);
        (uint8 f, address o, int24 tl, int24 tu, uint128 liq) = decodeBurnHookData(encoded);
        assertEq(f, flags);
        assertEq(o, owner);
        assertEq(tl, tickLower);
        assertEq(tu, tickUpper);
        assertEq(liq, liquidity);
    }

    function test_emptyHookData_isNotReactive() public pure {
        assertFalse(isReactive(0));
        assertFalse(isV3(0));
        assertFalse(isV4(0));
    }
}
```

**Step 2: Run test to verify it fails**

Run: `forge test --match-path "test/fee-concentration-index/unit/HookDataFlags.unit.t.sol" -vv`
Expected: FAIL — import not found

**Step 3: Write minimal implementation**

Create `src/fee-concentration-index/types/HookDataFlagsMod.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Composable bitmask flags for hookData protocol dispatch.
// First byte of hookData encodes source + protocol.
uint8 constant REACTIVE_FLAG = 0x01; // callback from Reactive Network
uint8 constant V3_FLAG       = 0x02; // Uniswap V3 source
uint8 constant V4_FLAG       = 0x04; // Uniswap V4 source

function isReactive(uint8 flags) pure returns (bool) {
    return flags & REACTIVE_FLAG != 0;
}

function isV3(uint8 flags) pure returns (bool) {
    return flags & V3_FLAG != 0;
}

function isV4(uint8 flags) pure returns (bool) {
    return flags & V4_FLAG != 0;
}

// ── Encode helpers (used by ReactLogicMod to build callback hookData) ──

function encodeSwapHookData(uint8 flags, int24 tickBefore, int24 tickAfter) pure returns (bytes memory) {
    return abi.encodePacked(flags, tickBefore, tickAfter);
}

function encodeMintHookData(uint8 flags, address owner, int24 tickLower, int24 tickUpper, uint128 liquidity) pure returns (bytes memory) {
    return abi.encodePacked(flags, owner, tickLower, tickUpper, liquidity);
}

function encodeBurnHookData(uint8 flags, address owner, int24 tickLower, int24 tickUpper, uint128 liquidity) pure returns (bytes memory) {
    return abi.encodePacked(flags, owner, tickLower, tickUpper, liquidity);
}

// ── Decode helpers (used by FCI hook to read hookData) ──
// Uses abi.encodePacked layout: tightly packed, no padding.

function decodeSwapHookData(bytes memory data) pure returns (uint8 flags, int24 tickBefore, int24 tickAfter) {
    // Layout: [uint8(1)] [int24(3)] [int24(3)] = 7 bytes
    assembly {
        let ptr := add(data, 32) // skip length prefix
        let word := mload(ptr)
        flags := shr(248, word)                        // first byte
        tickBefore := signextend(2, shr(224, word))    // bytes 1-3
        tickAfter := signextend(2, shr(200, word))     // bytes 4-6
    }
}

function decodeMintHookData(bytes memory data) pure returns (uint8 flags, address owner, int24 tickLower, int24 tickUpper, uint128 liquidity) {
    // Layout: [uint8(1)] [address(20)] [int24(3)] [int24(3)] [uint128(16)] = 43 bytes
    assembly {
        let ptr := add(data, 32)
        let word0 := mload(ptr)
        flags := shr(248, word0)
        owner := and(shr(88, word0), 0xffffffffffffffffffffffffffffffffffffffff)
        tickLower := signextend(2, shr(64, word0))
        // tickUpper spans word boundary at byte 24
        let word1 := mload(add(ptr, 24))
        tickUpper := signextend(2, shr(232, word1))
        liquidity := and(shr(104, word1), 0xffffffffffffffffffffffffffffffff)
    }
}

function decodeBurnHookData(bytes memory data) pure returns (uint8 flags, address owner, int24 tickLower, int24 tickUpper, uint128 liquidity) {
    return decodeMintHookData(data); // same layout
}
```

**Step 4: Run test to verify it passes**

Run: `forge test --match-path "test/fee-concentration-index/unit/HookDataFlags.unit.t.sol" -vv`
Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add src/fee-concentration-index/types/HookDataFlagsMod.sol \
        test/fee-concentration-index/unit/HookDataFlags.unit.t.sol
git commit -m "feat(003): hookData flag constants + codec (REACTIVE, V3, V4 bitmask)"
```

---

### Task 2: FCI hook — callback auth + IPayer

**Files:**
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol:36-40`
- Test: `test/fee-concentration-index/unit/FeeConcentrationIndexAuth.unit.t.sol`

**Context:** The FCI hook needs to accept calls from the callback proxy (reactive V3 path). Add `authorizedCallers`, `rvmId`, `pay()`, and `receive()`. These are **additive** — no existing IHooks logic is touched.

**Step 1: Write the failing test**

Create `test/fee-concentration-index/unit/FeeConcentrationIndexAuth.unit.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {FeeConcentrationIndex} from "../../src/fee-concentration-index/FeeConcentrationIndex.sol";

contract FeeConcentrationIndexAuthTest is Test {
    FeeConcentrationIndex fci;
    address callbackProxy = address(0xC0FFEE);
    address deployer;

    function setUp() public {
        deployer = address(this);
        fci = new FeeConcentrationIndex{value: 0.1 ether}(address(1), callbackProxy);
    }

    function test_constructor_setsRvmId() public view {
        assertEq(fci.rvmId(), deployer);
    }

    function test_constructor_authorizesCallbackProxy() public view {
        assertTrue(fci.authorizedCallers(callbackProxy));
    }

    function test_pay_sendsETH() public {
        uint256 before = callbackProxy.balance;
        vm.prank(callbackProxy);
        fci.pay(0.01 ether);
        assertEq(callbackProxy.balance, before + 0.01 ether);
    }

    function test_pay_revertsUnauthorized() public {
        vm.prank(address(0xDEAD));
        vm.expectRevert();
        fci.pay(0.01 ether);
    }

    function test_setRvmId_onlyOwner() public {
        address newRvm = address(0xBEEF);
        fci.setRvmId(newRvm);
        assertEq(fci.rvmId(), newRvm);
    }

    function test_setRvmId_revertsNonOwner() public {
        vm.prank(address(0xDEAD));
        vm.expectRevert();
        fci.setRvmId(address(0xBEEF));
    }

    function test_receive_acceptsETH() public {
        (bool ok,) = address(fci).call{value: 0.05 ether}("");
        assertTrue(ok);
        assertEq(address(fci).balance, 0.15 ether); // 0.1 from constructor + 0.05
    }

    receive() external payable {} // so test contract can receive ETH back from pay()
}
```

**Step 2: Run test to verify it fails**

Run: `forge test --match-path "test/fee-concentration-index/unit/FeeConcentrationIndexAuth.unit.t.sol" -vv`
Expected: FAIL — constructor signature mismatch (currently takes 1 arg, test passes 2)

**Step 3: Write minimal implementation**

Modify `src/fee-concentration-index/FeeConcentrationIndex.sol`. Add these fields and functions to the `FeeConcentrationIndex` contract. Do NOT change any existing IHooks function bodies.

Add state variables (after line 36, inside contract):

```solidity
    address public rvmId;
    address immutable owner;
    mapping(address => bool) public authorizedCallers;

    event RvmIdUpdated(address indexed oldRvmId, address indexed newRvmId);
    event AuthorizedCallerUpdated(address indexed caller, bool authorized);

    error OnlyOwner();
    error InvalidRvmId();
    error InsufficientFunds();
    error TransferFailed();
```

Change the constructor (replace line 38-40):

```solidity
    constructor(address poolManager_, address callbackProxy_) payable {
        fciStorage().poolManager = IPoolManager(poolManager_);
        owner = msg.sender;
        rvmId = msg.sender;
        authorizedCallers[callbackProxy_] = true;
    }
```

Add auth + IPayer functions (before the View section, around line 227):

```solidity
    // ── Auth ──

    function setRvmId(address rvmId_) external {
        if (msg.sender != owner) revert OnlyOwner();
        address old = rvmId;
        rvmId = rvmId_;
        emit RvmIdUpdated(old, rvmId_);
    }

    function setAuthorized(address caller, bool authorized) external {
        if (msg.sender != owner) revert OnlyOwner();
        authorizedCallers[caller] = authorized;
        emit AuthorizedCallerUpdated(caller, authorized);
    }

    // ── IPayer (callback proxy gas payment) ──

    function pay(uint256 amount) external {
        if (!authorizedCallers[msg.sender]) revert OnlyOwner();
        if (address(this).balance < amount) revert InsufficientFunds();
        if (amount > 0) {
            (bool success,) = payable(msg.sender).call{value: amount}("");
            if (!success) revert TransferFailed();
        }
    }

    receive() external payable {}
```

**Important:** Also update any existing tests or scripts that construct `FeeConcentrationIndex` with 1 arg — they now need 2 args `(poolManager, callbackProxy)`. Search for `new FeeConcentrationIndex(` and add a second arg (e.g., `address(0)` for tests that don't test auth).

**Step 4: Run test to verify it passes**

Run: `forge test --match-path "test/fee-concentration-index/unit/FeeConcentrationIndexAuth.unit.t.sol" -vv`
Expected: PASS (all 7 tests)

Also run: `forge build` to ensure no existing code breaks.

**Step 5: Commit**

```bash
git add src/fee-concentration-index/FeeConcentrationIndex.sol \
        test/fee-concentration-index/unit/FeeConcentrationIndexAuth.unit.t.sol
git commit -m "feat(003): FCI hook gains callback auth + IPayer for reactive callbacks"
```

---

### Task 3: afterSwap — REACTIVE_FLAG V3 path

**Files:**
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol:107-136` (afterSwap function)
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol:1-29` (add import)
- Test: `test/fee-concentration-index/unit/FeeConcentrationIndexReactiveSwap.unit.t.sol`

**Context:** Replace the current `hookData.length > 0` check in `afterSwap` with REACTIVE_FLAG-based dispatch. When `REACTIVE | V3` flags are present, decode `(tickBefore, tickAfter)` from hookData and call `incrementOverlappingRanges` on `reactiveFciStorage()`. The existing single-tick logic (`tickMax = tick + 1`) is replaced with the proper swept range (`sortTicks(tickBefore, tickAfter)`).

**Step 1: Write the failing test**

Create a unit test that calls `afterSwap` with REACTIVE|V3 hookData and verifies swap count is incremented on a registered range. This test will initially fail because afterSwap doesn't yet decode the new hookData format.

**Step 2: Modify afterSwap**

Add import for the flag module (at top of FeeConcentrationIndex.sol):

```solidity
import {
    REACTIVE_FLAG, V3_FLAG,
    isReactive, isV3
} from "./types/HookDataFlagsMod.sol";
```

Replace the afterSwap body (lines 113-133) with:

```solidity
        PoolId poolId = PoolIdLibrary.toId(key);

        int24 tickMin;
        int24 tickMax;
        if (hookData.length > 0) {
            CalldataReader reader = CalldataReaderLib.from(hookData);
            uint8 flags;
            (reader, flags) = reader.readU8();

            if (isReactive(flags) && isV3(flags)) {
                // Reactive V3: tickBefore + tickAfter in hookData
                int24 tickBefore;
                int24 tickAfter;
                (reader, tickBefore) = reader.readI24();
                (reader, tickAfter) = reader.readI24();
                reader.requireAtEndOf(hookData);
                (tickMin, tickMax) = sortTicks(tickBefore, tickAfter);
                incrementOverlappingRanges(reactiveFciStorage(), poolId, tickMin, tickMax);
            }
            // Future: else if (isV4(flags)) { ... }
        } else {
            // V4 native path: tickBefore from transient storage, tickAfter from PoolManager
            int24 tickBefore = t_readTick();
            int24 tickAfter = getCurrentTick(_poolManager(), poolId);
            (tickMin, tickMax) = sortTicks(tickBefore, tickAfter);
            incrementOverlappingRanges(poolId, tickMin, tickMax);
        }
```

**Step 3: Run tests, verify pass, commit**

Run: `forge test --match-path "test/fee-concentration-index/**" -vv`

```bash
git add src/fee-concentration-index/FeeConcentrationIndex.sol \
        test/fee-concentration-index/unit/FeeConcentrationIndexReactiveSwap.unit.t.sol
git commit -m "feat(003): afterSwap dispatches on REACTIVE|V3 flags from hookData"
```

---

### Task 4: afterAddLiquidity — REACTIVE_FLAG V3 path

**Files:**
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol:44-88` (afterAddLiquidity)
- Test: `test/fee-concentration-index/unit/FeeConcentrationIndexReactiveMint.unit.t.sol`

**Context:** Replace `hookData.length > 0` in `afterAddLiquidity` with flag dispatch. When `REACTIVE | V3`, decode `(owner, tickLower, tickUpper, liquidity)` from hookData. Use `v3PositionKey(owner, tickLower, tickUpper)` for position key. Call `registerPosition` on `reactiveFciStorage()`. No feeGrowthInside snapshot (liquidity-ratio approach).

**Step 1: Modify afterAddLiquidity**

Add import for v3PositionKey:
```solidity
import {v3PositionKey} from "../reactive-integration/types/CollectedFeesMod.sol";
```

Replace the afterAddLiquidity body (lines 52-85) with:

```solidity
        PoolId poolId = PoolIdLibrary.toId(key);

        if (hookData.length > 0) {
            CalldataReader reader = CalldataReaderLib.from(hookData);
            uint8 flags;
            (reader, flags) = reader.readU8();

            if (isReactive(flags) && isV3(flags)) {
                // Reactive V3: decode owner, ticks, liquidity from hookData
                address posOwner;
                int24 tickLower;
                int24 tickUpper;
                uint128 posLiquidity;
                (reader, posOwner) = reader.readAddr();
                (reader, tickLower) = reader.readI24();
                (reader, tickUpper) = reader.readI24();
                (reader, posLiquidity) = reader.readU128();
                reader.requireAtEndOf(hookData);

                FeeConcentrationIndexStorage storage r$ = reactiveFciStorage();
                bytes32 positionKey = v3PositionKey(posOwner, tickLower, tickUpper);
                TickRange rk = fromTicks(tickLower, tickUpper);
                registerPosition(r$, poolId, rk, positionKey, tickLower, tickUpper, posLiquidity);
                // No feeGrowthInside snapshot: reactive callbacks arrive async,
                // x_k computed from liquidity ratios at burn time.
                incrementPosCount(r$, poolId);
            }
        } else {
            // V4 native path (unchanged)
            (PoolId _, bytes32 positionKey) = derivePoolAndPosition(sender, key, params);
            TickRange rk = fromTicks(params.tickLower, params.tickUpper);
            (uint128 posLiquidity,) = getPositionFeeGrowthInsideLast0(_poolManager(), poolId, positionKey);
            registerPosition(poolId, rk, positionKey, params.tickLower, params.tickUpper, posLiquidity);

            int24 currentTick = getCurrentTick(_poolManager(), poolId);
            uint256 feeGrowthInside0X128 = getFeeGrowthInside0(
                _poolManager(), poolId, currentTick, params.tickLower, params.tickUpper
            );
            setFeeGrowthBaseline(poolId, positionKey, feeGrowthInside0X128);
            incrementPosCount(poolId);
        }
```

**Note:** The V4 path now derives `poolId` from the key at the top, then derives `positionKey` inside the else branch. Adjust variable scoping accordingly — may need to move `derivePoolAndPosition` call inside the else block.

**Step 2: Write test, run, commit**

```bash
git commit -m "feat(003): afterAddLiquidity dispatches on REACTIVE|V3 flags from hookData"
```

---

### Task 5: afterRemoveLiquidity — REACTIVE_FLAG V3 path

**Files:**
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol:163-226` (afterRemoveLiquidity)
- Test: `test/fee-concentration-index/unit/FeeConcentrationIndexReactiveBurn.unit.t.sol`

**Context:** Replace `hookData.length > 0` in `afterRemoveLiquidity` with flag dispatch. When `REACTIVE | V3`, decode `(owner, tickLower, tickUpper, liquidity)`. Use `v3PositionKey` for position key. Use `fromFeeGrowth(posLiquidity, totalRangeLiq)` for x_k (liquidity ratio). Call `deregisterPosition`, `addStateTerm`, `decrementPosCount` on `reactiveFciStorage()`.

**Step 1: Modify afterRemoveLiquidity**

Replace the body (lines 171-223) with:

```solidity
        PoolId poolId = PoolIdLibrary.toId(key);

        if (hookData.length > 0) {
            CalldataReader reader = CalldataReaderLib.from(hookData);
            uint8 flags;
            (reader, flags) = reader.readU8();

            if (isReactive(flags) && isV3(flags)) {
                // Reactive V3: decode owner, ticks, liquidity from hookData
                address posOwner;
                int24 tickLower;
                int24 tickUpper;
                uint128 posLiquidity;
                (reader, posOwner) = reader.readAddr();
                (reader, tickLower) = reader.readI24();
                (reader, tickUpper) = reader.readI24();
                (reader, posLiquidity) = reader.readU128();
                reader.requireAtEndOf(hookData);

                FeeConcentrationIndexStorage storage r$ = reactiveFciStorage();
                bytes32 positionKey = v3PositionKey(posOwner, tickLower, tickUpper);

                (, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) =
                    deregisterPosition(r$, poolId, positionKey, posLiquidity);

                if (!swapLifetime.isZero()) {
                    FeeShareRatio xk = fromFeeGrowth(uint256(posLiquidity), uint256(totalRangeLiq));
                    uint256 xSquaredQ128 = xk.square();
                    addStateTerm(r$, poolId, blockLifetime, xSquaredQ128);
                }
                decrementPosCount(r$, poolId);
            }
        } else {
            // V4 native path (unchanged)
            (, bytes32 positionKey) = derivePoolAndPosition(sender, key, params);
            (uint256 positionFeeLast0X128, uint128 posLiquidity, uint256 rangeFeeGrowthNow0X128) = t_readRemovalData();

            uint128 removedLiq = uint128(uint256(-params.liquidityDelta));
            if (posLiquidity != removedLiq) {
                return (IHooks.afterRemoveLiquidity.selector, BalanceDelta.wrap(0));
            }

            uint256 baseline0X128 = getFeeGrowthBaseline(poolId, positionKey);

            (, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) =
                deregisterPosition(poolId, positionKey, posLiquidity);

            FeeShareRatio xk = fromFeeGrowthDelta(
                rangeFeeGrowthNow0X128, positionFeeLast0X128, baseline0X128,
                posLiquidity, totalRangeLiq
            );

            if (!swapLifetime.isZero()) {
                uint256 xSquaredQ128 = xk.square();
                addStateTerm(poolId, blockLifetime, xSquaredQ128);
            }
            decrementPosCount(poolId);
            deleteFeeGrowthBaseline(poolId, positionKey);
        }
```

**Step 2: Write test, run, commit**

```bash
git commit -m "feat(003): afterRemoveLiquidity dispatches on REACTIVE|V3 flags from hookData"
```

---

### Task 6: ReactLogicMod — retarget callbacks to FCI hook

**Files:**
- Modify: `src/reactive-integration/modules/ReactLogicMod.sol:25-77`
- Modify: `src/reactive-integration/ThetaSwapReactive.sol:18` (adapter → fciHook)
- Test: Deployment verification (fork test or on-chain)

**Context:** Change callback payloads from `onV3Swap(address, V3SwapData)` to `afterSwap(address, PoolKey, SwapParams, BalanceDelta, bytes)` with REACTIVE|V3 hookData. Change `adapter` parameter name to `fciHook` throughout. Import the hookData encode helpers.

**Step 1: Update processLog signature and imports**

Change `adapter` to `fciHook` in `processLog` and `ThetaSwapReactive`.

Add imports to ReactLogicMod.sol:
```solidity
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {fromV3Pool} from "../libraries/PoolKeyExtMod.sol";
import {
    REACTIVE_FLAG, V3_FLAG,
    encodeSwapHookData, encodeMintHookData, encodeBurnHookData
} from "../../fee-concentration-index/types/HookDataFlagsMod.sol";
```

**Step 2: Rewrite V3_SWAP_SIG branch**

The callback must encode `afterSwap(address,PoolKey,SwapParams,BalanceDelta,bytes)` with:
- `sender` = `address(0)` (RN replaces with rvmId)
- `key` = `fromV3Pool(pool, fciHook)` — synthetic PoolKey with hooks=fciHook
- `params` = zero SwapParams (FCI afterSwap ignores it for reactive path)
- `delta` = zero BalanceDelta (FCI afterSwap ignores it for reactive path)
- `hookData` = `encodeSwapHookData(REACTIVE_FLAG | V3_FLAG, tickBefore, tickAfter)`

```solidity
if (sig == V3_SWAP_SIG) {
    V3SwapData memory data = decodeV3Swap(log);
    uint256 chainId_ = logChainId(log);
    address pool = emitter(log);

    (int24 prevTick, bool isSet) = getLastTick(chainId_, pool);
    data.tickBefore = isSet ? prevTick : data.tick;
    setLastTick(chainId_, pool, data.tick);

    PoolKey memory key = fromV3Pool(data.pool, fciHook);
    bytes memory hookData = encodeSwapHookData(
        REACTIVE_FLAG | V3_FLAG, data.tickBefore, data.tick
    );

    emit IReactive.Callback(
        chainId_, fciHook, CALLBACK_GAS_LIMIT,
        abi.encodeWithSelector(
            IHooks.afterSwap.selector,
            address(0),  // rvmSender (injected by RN)
            key,
            SwapParams({zeroForOne: false, amountSpecified: 0, sqrtPriceLimitX96: 0}),
            BalanceDelta.wrap(0),
            hookData
        )
    );
}
```

Apply the same pattern for V3_MINT_SIG → `afterAddLiquidity` and V3_BURN_SIG → `afterRemoveLiquidity`.

**Step 3: Update ThetaSwapReactive**

In `ThetaSwapReactive.sol`, rename `adapter` to `fciHook`:
- Line 18: `address immutable fciHook;` (was `adapter`)
- Constructor: `fciHook = adapter_;` → `fciHook = fciHook_;`
- Line 61: `processLog(log, address(this), fciHook);`

**Step 4: Build and test**

Run: `forge build` — must compile cleanly.

```bash
git commit -m "feat(003): retarget ReactLogicMod callbacks from adapter to FCI hook with REACTIVE|V3 hookData"
```

---

### Task 7: Comment out ReactiveHookAdapter (DO NOT DELETE)

**Files:**
- Modify: `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol`

**Context:** The ReactiveHookAdapter is now replaced by the unified FCI hook. Comment out the entire contract body but keep the file. Do NOT delete the file.

**Step 1: Wrap contract in block comment**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// ── DEPRECATED: ReactiveHookAdapter ──
// Replaced by unified FCI hook with REACTIVE|V3 hookData dispatch.
// Kept for reference. See docs/plans/2026-03-09-unified-fci-hook-design.md.
//
// [entire contract body as comment]
```

**Step 2: Build**

Run: `forge build` — must still compile.

```bash
git commit -m "refactor(003): comment out ReactiveHookAdapter (replaced by unified FCI hook)"
```

---

### Task 8: fetchPositionKey — unified V3/V4 position key

**Files:**
- Modify: `src/libraries/HookUtilsMod.sol`
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol` (afterAddLiquidity, afterRemoveLiquidity)

**Context:** Uncomment the pseudo code in HookUtilsMod.sol and wire it up. Add a `derivePoolAndPosition` overload that takes `uint8 flags` and dispatches to V3 or V4 position key. Update afterAddLiquidity and afterRemoveLiquidity to use the unified helper in the V3 path (replacing inline `v3PositionKey` calls from Tasks 4-5).

**Step 1: Add flagged overload to HookUtilsMod.sol**

```solidity
import {v3PositionKey} from "../reactive-integration/types/CollectedFeesMod.sol";
import {V3_FLAG, isV3} from "../fee-concentration-index/types/HookDataFlagsMod.sol";

function fetchPositionKey(
    uint8 flags,
    address sender,
    int24 tickLower,
    int24 tickUpper,
    bytes32 salt
) pure returns (bytes32) {
    if (isV3(flags)) {
        return v3PositionKey(sender, tickLower, tickUpper);
    }
    return Position.calculatePositionKey(sender, tickLower, tickUpper, salt);
}
```

**Step 2: Build, test, commit**

```bash
git commit -m "feat(003): fetchPositionKey dispatches V3/V4 via hookData flags"
```

---

### Task 9: Integration test — full mint/swap/burn cycle with unified hook

**Files:**
- Test: `test/fee-concentration-index/unit/FeeConcentrationIndexUnified.unit.t.sol`

**Context:** End-to-end unit test: construct FCI hook, call afterAddLiquidity (×2 positions) with REACTIVE|V3 hookData, call afterSwap with REACTIVE|V3 hookData, call afterRemoveLiquidity (×2) with REACTIVE|V3 hookData. Verify deltaPlus > 0. This is the local equivalent of the on-chain `buildMildV3()` scenario.

**Step 1: Write test, run, commit**

```bash
git commit -m "test(003): integration test for unified FCI hook with REACTIVE|V3 hookData"
```

---

### Task 10: Deployment verification (on-chain)

**Files:**
- Modify: `script/utils/Deployments.sol` (update FCI hook address)
- Modify: `script/reactive-integration/FeeConcentrationIndexBuilder.s.sol` (update for unified hook)

**Context:** Deploy unified FCI hook to Sepolia, deploy new ThetaSwapReactive on Lasna pointing to FCI hook (not adapter), register V3 pool, run `buildMildV3()`, wait for callbacks, query `getDeltaPlus`. Should match adapter v7 results (~4.99e37).

**Step 1: Deploy, verify, commit**

```bash
git commit -m "feat(003): deploy unified FCI hook, verify deltaPlus on-chain"
```
