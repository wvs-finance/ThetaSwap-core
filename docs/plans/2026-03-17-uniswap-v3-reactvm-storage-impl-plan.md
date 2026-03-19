# UniswapV3 ReactVM Storage Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement ReactVM shadow state for position liquidity so V3 reactive burns produce correct FCI accumulation.

**Architecture:** The ReactVM (Lasna) shadows position liquidity from Mint/Burn events. Callbacks carry a uniform 3-field payload `(LogRecord, int24 tickBefore, uint128 posLiqBefore)`. The destination-chain callback decodes `posLiqBefore` and passes it through hookData to FCI V2, which uses it instead of reading the (stale) V3 pool.

**Tech Stack:** Solidity ^0.8.26, Forge, Reactive Network, diamond storage pattern.

**Spec:** `docs/plans/2026-03-17-uniswap-v3-reactvm-storage-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/fee-concentration-index-v2/protocols/uniswap-v3/modules/UniswapV3ReactVMStorageMod.sol` | Replace | Diamond storage: TickShadow, PositionShadow, poolWhitelist |
| `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PayloadMutatorLib.sol` | Modify | Enrich payloads with shadow state; uniform 3-field encoding |
| `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol` | Modify | Call mutator for all event types (not just swap) |
| `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol` | Modify | Decode 3-field payload; pass posLiqBefore to _handleBurn |
| `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/V3HookDataLib.sol` | Modify | Add posLiqBefore to burn hookData encoding/decoding |
| `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol` | Modify | Override posLiquidity from hookData when present |
| `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol` | Modify | Remove async fallback; read posLiqBefore from facet |

---

### Task 1: UniswapV3ReactVMStorageMod.sol — Replace with V2

**Files:**
- Replace: `src/fee-concentration-index-v2/protocols/uniswap-v3/modules/UniswapV3ReactVMStorageMod.sol`

- [ ] **Step 1: Write the new storage module**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

struct TickShadow {
    int24 tick;
    bool isSet;
}

struct PositionShadow {
    uint128 liquidity;
    bool isSet;
}

struct UniswapV3ReactVMStorage {
    mapping(uint256 => mapping(address => bool)) poolWhitelist;
    mapping(uint256 => mapping(address => TickShadow)) tickShadow;
    mapping(uint256 => mapping(address => mapping(bytes32 => PositionShadow))) positionShadow;
}

bytes32 constant UNISWAP_V3_REACTVM_SLOT = keccak256("thetaSwap.fci.v3.reactvm");

function uniswapV3ReactVMStorage() pure returns (UniswapV3ReactVMStorage storage $) {
    bytes32 slot = UNISWAP_V3_REACTVM_SLOT;
    assembly ("memory-safe") { $.slot := slot }
}

// ── Tick shadow ──

function getLastTick(uint256 chainId, address pool) view returns (int24 tick, bool isSet) {
    TickShadow storage ts = uniswapV3ReactVMStorage().tickShadow[chainId][pool];
    tick = ts.tick;
    isSet = ts.isSet;
}

function setLastTick(uint256 chainId, address pool, int24 tick) {
    TickShadow storage ts = uniswapV3ReactVMStorage().tickShadow[chainId][pool];
    ts.tick = tick;
    ts.isSet = true;
}

// ── Position shadow ──

function getPositionShadow(uint256 chainId, address pool, bytes32 posKey)
    view
    returns (uint128 liquidity, bool isSet)
{
    PositionShadow storage ps = uniswapV3ReactVMStorage().positionShadow[chainId][pool][posKey];
    liquidity = ps.liquidity;
    isSet = ps.isSet;
}

function setPositionShadow(uint256 chainId, address pool, bytes32 posKey, uint128 liquidity) {
    PositionShadow storage ps = uniswapV3ReactVMStorage().positionShadow[chainId][pool][posKey];
    ps.liquidity = liquidity;
    ps.isSet = true;
}

// ── Pool whitelist ──

function isWhitelisted(uint256 chainId, address pool) view returns (bool) {
    return uniswapV3ReactVMStorage().poolWhitelist[chainId][pool];
}

function setWhitelisted(uint256 chainId, address pool, bool whitelisted) {
    uniswapV3ReactVMStorage().poolWhitelist[chainId][pool] = whitelisted;
}
```

- [ ] **Step 2: Compile**

Run: `forge build`
Expected: Compiles with no errors (warnings OK)

- [ ] **Step 3: Commit**

```bash
git add src/fee-concentration-index-v2/protocols/uniswap-v3/modules/UniswapV3ReactVMStorageMod.sol
git commit -m "feat(008): replace UniswapV3ReactVMStorageMod with V2 (PositionShadow)"
```

---

### Task 2: UniswapV3PayloadMutatorLib — Uniform 3-field payload

**Files:**
- Modify: `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PayloadMutatorLib.sol`

**Context:** Currently returns `abi.encode(log, int24 tickBefore)` for swaps and `abi.encode(log, int24(0))` for non-swaps. Must now return `abi.encode(log, int24 tickBefore, uint128 posLiqBefore)` for ALL event types. Mint/Burn shadow updates move here from `react()`.

- [ ] **Step 1: Update mutateV3Payload to handle all 3 event types with shadow**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {V3_SWAP_SIG, V3_MINT_SIG, V3_BURN_SIG} from "./EventSignatures.sol";
import {
    getLastTick, setLastTick,
    getPositionShadow, setPositionShadow
} from "../modules/UniswapV3ReactVMStorageMod.sol";

/// @dev Enriches raw V3 log data before callback emission.
/// Swap: injects tickBefore from shadow. Mint/Burn: updates position shadow.
/// Returns uniform 3-field: abi.encode(LogRecord, int24 tickBefore, uint128 posLiqBefore)
function mutateV3Payload(IReactive.LogRecord memory log) returns (bytes memory) {
    uint256 sig = log.topic_0;
    uint256 chainId_ = log.chain_id;
    address pool = log._contract;

    if (sig == V3_SWAP_SIG) {
        (,,,, int24 tickAfter) = abi.decode(log.data, (int256, int256, uint160, uint128, int24));
        (int24 prevTick, bool isSet) = getLastTick(chainId_, pool);
        int24 tickBefore = isSet ? prevTick : tickAfter;
        setLastTick(chainId_, pool, tickAfter);
        return abi.encode(log, tickBefore, uint128(0));
    }

    if (sig == V3_MINT_SIG) {
        // Mint event topics: (sender indexed, owner indexed, tickLower indexed, tickUpper indexed)
        // Mint event data: (sender, amount, amount0, amount1) — where sender is topic_1 (owner)
        address owner = address(uint160(log.topic_1));
        int24 tickLower = int24(int256(log.topic_2));
        int24 tickUpper = int24(int256(log.topic_3));
        (, uint128 liquidity,,) = abi.decode(log.data, (address, uint128, uint256, uint256));

        bytes32 posKey = keccak256(abi.encodePacked(owner, tickLower, tickUpper));
        (uint128 shadowLiq,) = getPositionShadow(chainId_, pool, posKey);
        setPositionShadow(chainId_, pool, posKey, shadowLiq + liquidity);

        return abi.encode(log, int24(0), uint128(0));
    }

    if (sig == V3_BURN_SIG) {
        address owner = address(uint160(log.topic_1));
        int24 tickLower = int24(int256(log.topic_2));
        int24 tickUpper = int24(int256(log.topic_3));
        (uint128 liquidity,,) = abi.decode(log.data, (uint128, uint256, uint256));

        // Zero-burn skip
        if (liquidity == 0) return abi.encode(log, int24(0), uint128(0));

        bytes32 posKey = keccak256(abi.encodePacked(owner, tickLower, tickUpper));
        (uint128 posLiqBefore,) = getPositionShadow(chainId_, pool, posKey);

        unchecked {
            setPositionShadow(chainId_, pool, posKey, posLiqBefore - liquidity);
        }

        return abi.encode(log, int24(0), posLiqBefore);
    }

    // Unknown event — pass through
    return abi.encode(log, int24(0), uint128(0));
}
```

- [ ] **Step 2: Compile**

Run: `forge build`
Expected: Compiles. The `react()` in UniswapV3Reactive.sol already calls `mutateV3Payload(log)` for all events.

- [ ] **Step 3: Commit**

```bash
git add src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PayloadMutatorLib.sol
git commit -m "feat(008): uniform 3-field payload with position shadow in mutator"
```

---

### Task 3: UniswapV3Reactive — Zero-burn skip in react()

**Files:**
- Modify: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol`

**Context:** The mutator now handles zero-burn internally (returns payload with posLiqBefore=0), but we should skip the callback emission entirely for zero-burns to save gas. Add a check in `react()`.

- [ ] **Step 1: Add zero-burn skip in react()**

In `react()`, after `mutateV3Payload`, check if this is a zero-burn and skip callback:

```solidity
function react(IReactive.LogRecord calldata log) external {
    if (!vm) revert OnlyReactVM();

    bytes memory payload = mutateV3Payload(log);

    // Zero-burn skip: V3 burnPosition() emits liq=0 then full burn.
    // mutateV3Payload returns posLiqBefore=0 for zero-burns. Skip callback.
    if (log.topic_0 == V3_BURN_SIG) {
        (uint128 burnedLiq,,) = abi.decode(log.data, (uint128, uint256, uint256));
        if (burnedLiq == 0) return;
    }

    emit IReactive.Callback(
        log.chain_id, callback, CALLBACK_GAS_LIMIT,
        abi.encodeWithSignature(
            "unlockCallbackReactive(address,bytes)",
            address(0),
            payload
        )
    );
}
```

- [ ] **Step 2: Compile**

Run: `forge build`
Expected: Compiles with no errors

- [ ] **Step 3: Commit**

```bash
git add src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol
git commit -m "feat(008): zero-burn skip in react() to save callback gas"
```

---

### Task 4: UniswapV3Callback — Decode 3-field payload

**Files:**
- Modify: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol`

**Context:** Currently decodes `(LogRecord, int24)`. Must decode `(LogRecord, int24, uint128)` and pass `posLiqBefore` to `_handleBurn`.

- [ ] **Step 1: Update unlockCallbackReactive decoder**

Change line 84 from:
```solidity
(IReactive.LogRecord memory log, int24 tickBefore) = abi.decode(data, (IReactive.LogRecord, int24));
```
To:
```solidity
(IReactive.LogRecord memory log, int24 tickBefore, uint128 posLiqBefore) =
    abi.decode(data, (IReactive.LogRecord, int24, uint128));
```

Pass `posLiqBefore` to `_handleBurn`:
```solidity
} else if (sig == V3_BURN_SIG) {
    _handleBurn(decodeV3BurnFromLog(log), posLiqBefore);
}
```

- [ ] **Step 2: Update _handleBurn signature and hookData encoding**

Change `_handleBurn` to accept and forward `posLiqBefore`:

```solidity
function _handleBurn(V3BurnData memory data, uint128 posLiqBefore) internal {
    if (data.liquidity == 0) return;

    PoolKey memory key = fromUniswapV3PoolToPoolKey(data.pool, fci);

    ModifyLiquidityParams memory params = ModifyLiquidityParams({
        tickLower: data.tickLower,
        tickUpper: data.tickUpper,
        liquidityDelta: -int256(uint256(data.liquidity)),
        salt: bytes32(0)
    });

    fci.beforeRemoveLiquidity(
        data.owner, key, params,
        encodeBeforeRemoveLiquidity(address(data.pool), posLiqBefore)
    );
    fci.afterRemoveLiquidity(
        data.owner, key, params,
        BalanceDelta.wrap(0), BalanceDelta.wrap(0),
        encodeAfterRemoveLiquidity(address(data.pool), posLiqBefore)
    );
}
```

- [ ] **Step 3: Compile**

Run: `forge build`
Expected: Fails — `encodeBeforeRemoveLiquidity` and `encodeAfterRemoveLiquidity` don't accept `posLiqBefore` yet. Fixed in Task 5.

- [ ] **Step 4: Commit (WIP)**

```bash
git add src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol
git commit -m "feat(008): decode 3-field payload in callback, pass posLiqBefore to burn"
```

---

### Task 5: V3HookDataLib — Add posLiqBefore to burn hookData

**Files:**
- Modify: `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/V3HookDataLib.sol`

**Context:** Current burn hookData layout: `FLAG (2) | pool (20) | action (1)` = 23 bytes. New layout adds `posLiqBefore (16)` = 39 bytes. Swap hookData (26 bytes with tick) and mint hookData (23 bytes) are unchanged.

- [ ] **Step 1: Update burn encoding functions**

```solidity
// hookData layout for burns: FLAG (2) | pool (20) | action (1) | posLiqBefore (16)

function encodeBeforeRemoveLiquidity(address pool, uint128 posLiqBefore) pure returns (bytes memory) {
    return abi.encodePacked(UNISWAP_V3_REACTIVE, pool, BEFORE_REMOVE_LIQUIDITY, posLiqBefore);
}

function encodeAfterRemoveLiquidity(address pool, uint128 posLiqBefore) pure returns (bytes memory) {
    return abi.encodePacked(UNISWAP_V3_REACTIVE, pool, AFTER_REMOVE_LIQUIDITY, posLiqBefore);
}
```

- [ ] **Step 2: Add posLiqBefore decoder**

```solidity
/// @dev Decode posLiqBefore from burn hookData at byte offset 23 (after flag+pool+action).
function decodePosLiqBefore(bytes calldata hookData) pure returns (uint128 posLiqBefore) {
    assembly { posLiqBefore := shr(128, calldataload(add(hookData.offset, 23))) }
}
```

- [ ] **Step 3: Compile**

Run: `forge build`
Expected: Compiles. The callback from Task 4 now resolves.

- [ ] **Step 4: Commit**

```bash
git add src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/V3HookDataLib.sol
git commit -m "feat(008): add posLiqBefore to burn hookData encoding/decoding"
```

---

### Task 6: UniswapV3Facet — Override posLiquidity from hookData

**Files:**
- Modify: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol`

**Context:** `latestPositionFeeGrowthInside` reads `posLiquidity` from `pool.positions()`. For V3 reactive burns, this is stale. The facet should check hookData for `posLiqBefore` and use it when present. The burn hookData has action type `BEFORE_REMOVE_LIQUIDITY` (0x04) or `AFTER_REMOVE_LIQUIDITY` (0x05), and `posLiqBefore` at byte 23.

- [ ] **Step 1: Update latestPositionFeeGrowthInside to use hookData override**

```solidity
function latestPositionFeeGrowthInside(bytes calldata hookData, PoolId, bytes32 posKey)
    external view onlyDelegateCall
    returns (uint128 posLiquidity, uint256 feeGrowthLast)
{
    address pool = decodePoolAddress(hookData);
    (posLiquidity, feeGrowthLast,,,) = IUniswapV3Pool(pool).positions(posKey);

    // Override posLiquidity from hookData when present (V3 reactive burn path).
    // Burn hookData is 39 bytes (23 header + 16 posLiqBefore).
    if (hookData.length >= 39) {
        uint128 posLiqOverride = decodePosLiqBefore(hookData);
        if (posLiqOverride > 0) {
            posLiquidity = posLiqOverride;
        }
    }
}
```

Add import at top of file:
```solidity
import {decodePosLiqBefore} from "./libraries/V3HookDataLib.sol";
```

- [ ] **Step 2: Compile**

Run: `forge build`
Expected: Compiles

- [ ] **Step 3: Commit**

```bash
git add src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol
git commit -m "feat(008): override posLiquidity from hookData in V3 facet"
```

---

### Task 7: FeeConcentrationIndexV2 — Remove async fallback

**Files:**
- Modify: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol`

**Context:** The `if (posLiquidity == 0) { posLiquidity = ... }` fallback in `beforeRemoveLiquidity` (lines 181-185) is no longer needed — the facet now reads `posLiqBefore` from hookData directly.

- [ ] **Step 1: Remove the async fallback**

Remove lines 181-185:
```solidity
        // Async fallback: V3 reactive callbacks arrive after the burn completes,
        // so pool.positions() returns 0 liquidity. Use params.liquidityDelta instead.
        if (posLiquidity == 0) {
            posLiquidity = uint128(uint256(-params.liquidityDelta));
        }
```

- [ ] **Step 2: Compile**

Run: `forge build`
Expected: Compiles

- [ ] **Step 3: Commit**

```bash
git add src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol
git commit -m "fix(008): remove async fallback — posLiqBefore now from hookData"
```

---

### Task 8: Integration compile + deploy verification

**Files:** All modified files

- [ ] **Step 1: Full build**

Run: `forge build --force`
Expected: Compiles with no errors

- [ ] **Step 2: Deploy to Sepolia + Lasna and verify**

Deploy fresh instances of FCI V2, V3 Facet, Callback, and Reactive. Wire them together. Execute: Mint → Swap → full Burn → query `getDeltaPlus`. Verify `removedPosCount > 0` and correct `posLiqBefore` in trace.

- [ ] **Step 3: Push**

```bash
git push origin 008-uniswap-v3-reactive-integration
```
