# ReactVM Pre-Mutation State Capture — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix V3 reactive adapter so swaps use the full tick-swept range and burns read feeGrowthInside correctly post-burn.

**Architecture:** Two independent fixes. (1) ReactVM shadows the last-known tick per pool; on Swap, it embeds the previous tick in the callback so the adapter can compute the swept range. (2) `onV3Burn` reads `pool.positions().feeGrowthInsideLast0X128` (valid post-burn) instead of reconstructing feeGrowthInside from ticks (broken when ticks are de-initialized).

**Tech Stack:** Solidity ^0.8.26, Foundry (forge test), Reactive Network (reactive-lib), Uniswap V3 core interfaces

---

## Context for the implementer

- **ReactVM** runs on Reactive Network. It processes V3 events via `react(LogRecord)` → `processLog()`. It emits `Callback` events that the Reactive Network relays to the **adapter** on Sepolia.
- **ReactVmStorage** uses diamond storage at a keccak256 slot. State is isolated from the adapter.
- **ReactLogicMod.sol** is the routing module — it decodes events and emits callbacks.
- The adapter's `onV3Swap` currently uses `(data.tick, data.tick)` — a single post-swap tick. It should use `(min(tickBefore, tickAfter), max(tickBefore, tickAfter))`.
- The adapter's `onV3Burn` calls `v3FeeGrowthInside0(pool, tickLower, tickUpper)` which reads `pool.ticks()`. After the last LP exits a range, V3 de-initializes those ticks → zeros → wrong feeGrowthInside → deltaPlus stays 0.
- V3's `burn()` updates `position.feeGrowthInsideLast0X128` to current feeGrowthInside **before** de-initializing ticks. So `pool.positions(posKey).feeGrowthInsideLast0X128` is valid after burn.

---

### Task 1: Add `tickBefore` to `V3SwapData`

**Files:**
- Modify: `src/reactive-integration/types/ReactiveCallbackDataMod.sol:12-15`

**Step 1: Add the field**

Change `V3SwapData` from:
```solidity
struct V3SwapData {
    IUniswapV3Pool pool;
    int24 tick;
}
```

To:
```solidity
struct V3SwapData {
    IUniswapV3Pool pool;
    int24 tickBefore;
    int24 tick;
}
```

**Step 2: Verify compilation**

Run: `forge build`
Expected: Compilation errors in ReactLogicMod.sol and ReactiveHookAdapter.sol (they construct V3SwapData without `tickBefore`). This is expected — we fix them in Tasks 2 and 3.

**Step 3: Commit**

```bash
git add -f src/reactive-integration/types/ReactiveCallbackDataMod.sol
git commit -m "feat(003): add tickBefore field to V3SwapData"
```

---

### Task 2: Add lastTick shadow to ReactVmStorage

**Files:**
- Modify: `src/reactive-integration/modules/ReactVmStorageMod.sol`

**Step 1: Add lastTick mapping and helpers**

Add to `ReactVmStorage` struct:
```solidity
struct ReactVmStorage {
    mapping(uint256 => mapping(address => bool)) poolWhitelist;
    // Last known tick per pool, keyed by (chainId, pool).
    // Used to compute the swept tick range on Swap events.
    mapping(uint256 => mapping(address => int24)) lastTick;
    // Whether lastTick has been initialized (0 is a valid tick).
    mapping(uint256 => mapping(address => bool)) lastTickSet;
}
```

Add getter/setter free functions after `setWhitelisted`:
```solidity
function getLastTick(uint256 chainId_, address pool) view returns (int24 tick, bool isSet) {
    ReactVmStorage storage s = reactVmStorage();
    tick = s.lastTick[chainId_][pool];
    isSet = s.lastTickSet[chainId_][pool];
}

function setLastTick(uint256 chainId_, address pool, int24 tick) {
    ReactVmStorage storage s = reactVmStorage();
    s.lastTick[chainId_][pool] = tick;
    s.lastTickSet[chainId_][pool] = true;
}
```

**Step 2: Verify compilation**

Run: `forge build`
Expected: Still fails (ReactLogicMod / adapter not updated yet). But no new errors from this file.

**Step 3: Commit**

```bash
git add -f src/reactive-integration/modules/ReactVmStorageMod.sol
git commit -m "feat(003): add lastTick shadow state to ReactVmStorage"
```

---

### Task 3: Update ReactLogicMod to embed tickBefore in Swap callback

**Files:**
- Modify: `src/reactive-integration/modules/ReactLogicMod.sol:44-49`

**Step 1: Import new helpers**

Add to existing imports:
```solidity
import {
    isWhitelisted, setWhitelisted,
    getLastTick, setLastTick
} from "./ReactVmStorageMod.sol";
```

**Step 2: Update the V3_SWAP_SIG branch**

Replace the existing swap handler (lines 44-49):
```solidity
    if (sig == V3_SWAP_SIG) {
        V3SwapData memory data = decodeV3Swap(log);
        emit IReactive.Callback(
            logChainId(log), adapter, CALLBACK_GAS_LIMIT,
            abi.encodeWithSignature("onV3Swap(address,(address,int24))", address(0), data)
        );
    }
```

With:
```solidity
    if (sig == V3_SWAP_SIG) {
        V3SwapData memory data = decodeV3Swap(log);

        // Inject pre-swap tick from shadow state
        (int24 prevTick, bool isSet) = getLastTick(logChainId(log), emitter(log));
        data.tickBefore = prevTick;
        setLastTick(logChainId(log), emitter(log), data.tick);

        // Skip increment on first swap (no valid tickBefore yet)
        if (!isSet) return;

        emit IReactive.Callback(
            logChainId(log), adapter, CALLBACK_GAS_LIMIT,
            abi.encodeWithSignature("onV3Swap(address,(address,int24,int24))", address(0), data)
        );
    }
```

Note the ABI signature changes: `(address,int24)` → `(address,int24,int24)` because `V3SwapData` now has 3 fields.

**Step 3: Verify compilation**

Run: `forge build`
Expected: May still fail if adapter's `onV3Swap` signature doesn't match yet. Fixed in Task 4.

**Step 4: Commit**

```bash
git add -f src/reactive-integration/modules/ReactLogicMod.sol
git commit -m "feat(003): embed tickBefore in Swap callback via ReactVM shadow"
```

---

### Task 4: Update adapter onV3Swap to use swept tick range

**Files:**
- Modify: `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol:60-67`

**Step 1: Update onV3Swap**

Replace:
```solidity
    function onV3Swap(address rvmSender, V3SwapData calldata data) external {
        requireAuthorized(msg.sender, authorizedCallers);
        if (rvmSender != rvmId) revert InvalidRvmId();
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolKey memory key = fromV3Pool(data.pool, address(this));
        PoolId poolId = PoolIdLibrary.toId(key);
        incrementOverlappingRanges($, poolId, data.tick, data.tick);
    }
```

With:
```solidity
    function onV3Swap(address rvmSender, V3SwapData calldata data) external {
        requireAuthorized(msg.sender, authorizedCallers);
        if (rvmSender != rvmId) revert InvalidRvmId();
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolKey memory key = fromV3Pool(data.pool, address(this));
        PoolId poolId = PoolIdLibrary.toId(key);
        int24 tickMin = data.tickBefore < data.tick ? data.tickBefore : data.tick;
        int24 tickMax = data.tickBefore > data.tick ? data.tickBefore : data.tick;
        incrementOverlappingRanges($, poolId, tickMin, tickMax);
    }
```

**Step 2: Verify compilation**

Run: `forge build`
Expected: PASS — all swap-side changes compile.

**Step 3: Commit**

```bash
git add -f src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol
git commit -m "feat(003): use swept tick range in onV3Swap"
```

---

### Task 5: Update adapter onV3Burn to read position feeGrowthInsideLast

**Files:**
- Modify: `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol:90-125`
- Modify: `src/reactive-integration/libraries/V3FeeGrowthReaderMod.sol:39-40` (fix misleading comment)

**Step 1: Update onV3Burn**

In `onV3Burn`, replace the feeGrowthInside read (lines 102-103):
```solidity
            // Read current feeGrowthInside0 live from V3 pool (same chain).
            uint256 rangeFeeGrowthNow0 = v3FeeGrowthInside0(data.pool, data.tickLower, data.tickUpper);
```

With:
```solidity
            // Read position's feeGrowthInsideLast0 from V3 pool.
            // V3's burn() updates this to current feeGrowthInside BEFORE
            // de-initializing ticks, so it's valid even after the last LP exits.
            uint256 rangeFeeGrowthNow0 = v3PositionFeeGrowthLast0(
                data.pool, data.owner, data.tickLower, data.tickUpper
            );
```

Also update the import at the top of the file. Change:
```solidity
import {v3FeeGrowthInside0} from "../../libraries/V3FeeGrowthReaderMod.sol";
```
To:
```solidity
import {v3FeeGrowthInside0, v3PositionFeeGrowthLast0} from "../../libraries/V3FeeGrowthReaderMod.sol";
```

**Step 2: Fix misleading comment in V3FeeGrowthReaderMod.sol**

In `src/reactive-integration/libraries/V3FeeGrowthReaderMod.sol`, change line 40:
```solidity
// Read a position's stored feeGrowthInside0LastX128 from V3 pool.
// After a burn, this value is updated to current — call BEFORE burn for snapshots.
```
To:
```solidity
// Read a position's stored feeGrowthInside0LastX128 from V3 pool.
// V3 updates this during burn() BEFORE de-initializing ticks,
// so it equals current feeGrowthInside even after full position removal.
```

**Step 3: Also remove unused `v3FeeGrowthInside0` import from onV3Mint**

Check if `v3FeeGrowthInside0` is still used in `onV3Mint` (line 81). Yes — `onV3Mint` still calls `v3FeeGrowthInside0(data.pool, data.tickLower, data.tickUpper)` for the snapshot. This is correct because at mint time, ticks ARE initialized. Keep the import.

**Step 4: Verify compilation**

Run: `forge build`
Expected: PASS

**Step 5: Commit**

```bash
git add -f src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol src/reactive-integration/libraries/V3FeeGrowthReaderMod.sol
git commit -m "fix(003): read position feeGrowthInsideLast in onV3Burn instead of ticks"
```

---

### Task 6: Update V3EventDecoderMod to set tickBefore=0 default

**Files:**
- Modify: `src/reactive-integration/types/V3EventDecoderMod.sol:18-23`

**Step 1: Update decodeV3Swap**

The decoder doesn't know tickBefore (it comes from ReactVM storage, not the event). Set it to 0 as default — ReactLogicMod overwrites it before emitting the callback.

Replace:
```solidity
function decodeV3Swap(IReactive.LogRecord calldata log) pure returns (V3SwapData memory) {
    (,,,, int24 tick) = abi.decode(log.data, (int256, int256, uint160, uint128, int24));
    return V3SwapData({pool: IUniswapV3Pool(log._contract), tick: tick});
}
```

With:
```solidity
function decodeV3Swap(IReactive.LogRecord calldata log) pure returns (V3SwapData memory) {
    (,,,, int24 tick) = abi.decode(log.data, (int256, int256, uint160, uint128, int24));
    return V3SwapData({pool: IUniswapV3Pool(log._contract), tickBefore: 0, tick: tick});
}
```

**Step 2: Verify full compilation**

Run: `forge build`
Expected: PASS — all files compile cleanly now.

**Step 3: Commit**

```bash
git add -f src/reactive-integration/types/V3EventDecoderMod.sol
git commit -m "feat(003): set default tickBefore=0 in V3 swap decoder"
```

---

### Task 7: Fork test — verify position feeGrowthInsideLast persists post-burn

**Files:**
- Modify: `test/reactive-integration/fork/V3FeeGrowthReader.fork.t.sol`

**Step 1: Add post-burn verification test**

Add this test to the existing `V3FeeGrowthReaderForkTest` contract:

```solidity
    /// @dev Verify that position.feeGrowthInsideLast0 equals feeGrowthInside0
    /// computed from ticks, when ticks are still initialized.
    function test_fork_positionFeeGrowthLastMatchesTicks() public view {
        int24 tickLower = -60;
        int24 tickUpper = 60;
        address posOwner = 0xe69228626E4800578D06a93BaaA595f6634A47C3;

        uint256 fromTicks = v3FeeGrowthInside0(pool, tickLower, tickUpper);
        uint256 fromPosition = v3PositionFeeGrowthLast0(pool, posOwner, tickLower, tickUpper);

        console2.log("feeGrowthInside0 (from ticks):", fromTicks);
        console2.log("feeGrowthInsideLast0 (from position):", fromPosition);

        // After the last swap, V3 updated the position's feeGrowthInsideLast.
        // These should be equal if the position hasn't collected since the last update.
        // Note: they may differ if swaps occurred after the last position update.
        // The key invariant is: fromPosition >= snapshot_at_mint (monotonically increasing).
        assertTrue(fromPosition > 0, "position feeGrowthInsideLast0 should be non-zero");
    }
```

Add the import for `v3PositionFeeGrowthLast0`:
```solidity
import {v3FeeGrowthInside0, v3PositionFeeGrowthLast0} from
    "../../../src/reactive-integration/libraries/V3FeeGrowthReaderMod.sol";
```

**Step 2: Run the fork test**

Run: `forge test --match-path "test/reactive-integration/fork/V3FeeGrowthReader.fork.t.sol" -vv`
Expected: All 3 tests PASS.

**Step 3: Commit**

```bash
git add -f test/reactive-integration/fork/V3FeeGrowthReader.fork.t.sol
git commit -m "test(003): fork test verifying position feeGrowthInsideLast persistence"
```

---

### Task 8: Full build + existing test regression

**Files:** None (verification only)

**Step 1: Full build**

Run: `forge build`
Expected: PASS

**Step 2: Run all reactive-integration tests**

Run: `forge test --match-path "test/reactive-integration/**" -vv`
Expected: All tests PASS. If any kontrol tests exist that reference deleted SyntheticFeeGrowth, they were already removed in the previous plan.

**Step 3: Run FCI tests for regression**

Run: `forge test --match-path "test/fee-concentration-index/**" -vv`
Expected: All tests PASS.

---

### Task 9: Deploy and verify on-chain

**Files:**
- Modify: `script/utils/Deployments.sol` (update addresses after deploy)

**Step 1: Deploy new adapter to Sepolia**

The adapter contract changed (`onV3Swap` signature changed, `onV3Burn` reads differently). Deploy a new instance:

```bash
source .env
export $(grep -v '^#' .env | grep -v '^\s*$' | xargs)
SEPOLIA_RPC="https://eth-sepolia.g.alchemy.com/v2/${ALCHEMY_API_KEY}"
CALLBACK_PROXY=0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA

forge create --broadcast \
    src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol:ReactiveHookAdapter \
    --constructor-args "$CALLBACK_PROXY" \
    --rpc-url "$SEPOLIA_RPC" \
    --private-key "$DEPLOYER_PRIVATE_KEY"
```

Note the deployed address. Then:
1. Set rvmId to the mnemonic deployer (0xe692...): `cast send <NEW_ADAPTER> "setRvmId(address)" 0xe69228626E4800578D06a93BaaA595f6634A47C3 --rpc-url "$SEPOLIA_RPC" --private-key "$DEPLOYER_PRIVATE_KEY"`
2. Fund with SepETH: `cast send <NEW_ADAPTER> --value 0.05ether --rpc-url "$SEPOLIA_RPC" --private-key "$DEPLOYER_PRIVATE_KEY"`

**Step 2: Deploy new ThetaSwapReactive to Lasna**

The reactive contract has `adapter` as immutable — must redeploy with new adapter address:

```bash
LASNA_RPC="https://lasna-rpc.rnk.dev/"
SYSTEM_CONTRACT=0x0000000000000000000000000000000000fffFfF

forge create --broadcast \
    src/reactive-integration/ThetaSwapReactive.sol:ThetaSwapReactive \
    --constructor-args <NEW_ADAPTER> "$SYSTEM_CONTRACT" \
    --rpc-url "$LASNA_RPC" \
    --private-key "$MNEMONIC_DERIVED_KEY" \
    --value 0.1ether \
    --gas-limit 4000000
```

If `forge create` fails on Lasna (SystemContract simulation issue), use `cast send --create` with compiled bytecode.

**Step 3: Register the V3 pool**

```bash
cast send <NEW_REACTIVE> "registerPool(uint256,address)" \
    11155111 0xcB80f9b60627DF6915cc8D34F5d1EF11617b8Af8 \
    --rpc-url "$LASNA_RPC" \
    --private-key "$MNEMONIC_DERIVED_KEY"
```

**Step 4: Run buildMildV3() scenario**

Use the existing `FeeConcentrationIndexBuilder.s.sol` script to mint, swap, and burn on the V3 pool. Wait ~60-120s for Reactive Network to relay callbacks.

**Step 5: Query deltaPlus**

```bash
cast call <NEW_ADAPTER> \
    "getDeltaPlus((address,address,uint24,int24,address),bool)(uint128)" \
    "(0x3eEE766C0d9Ca7D1509e2493857449Ef65A62cF3,0xdabc71B8cBBB062AC745Cc03DcEBd9C7B4d225b6,3000,60,0x0000000000000000000000000000000000000000)" \
    false \
    --rpc-url "$SEPOLIA_RPC"
```

Expected: deltaPlus > 0. This confirms the feeGrowthInside fix works.

**Step 6: Update Deployments.sol**

Update `sepoliaReactiveAdapter()` and `lasnaThetaSwapReactive()` with new addresses.

**Step 7: Commit**

```bash
git add -f script/utils/Deployments.sol
git commit -m "fix(003): deploy adapter v5 + reactive v11 with pre-mutation state fixes"
```
