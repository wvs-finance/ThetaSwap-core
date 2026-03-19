# Flow 3.1: listen() -> PoolAdded -> EDT Bind -> V3 Event Dispatch -> Callback Arrival

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the first testable reactive flow — from `listen(poolRpt)` on the origin chain through EDT dispatch on ReactVM to callback event emission confirmed via `vm.expectEmit`.

**Architecture:** Three-layer composition: EDT primitives (imported from reactive-hooks), protocol-agnostic ReactiveDispatchMod (new), V3-specific libs (new). SCOP style — file-level free functions, no inheritance, no `library` keyword.

**Tech Stack:** Solidity ^0.8.26, reactive-hooks EDT (commit `01bbb3e`), Forge tests, Uniswap V3 core interfaces

**Spec:** `docs/plans/2026-03-16-uniswap-v3-reactive-edt-flow-3-1-design.md`

---

## Known Type & Environment Issues (from plan review)

These affect multiple tasks and must be kept in mind throughout:

1. **`calldata` vs `memory`**: Dispatch functions (`handlePoolAdded`, `dispatchEvent`, `mutateV3Payload`) accept `IReactive.LogRecord`. In production they receive `calldata` from `react()`. In tests, logs are constructed in `memory`. **Solution**: Use `memory` parameters in all dispatch functions. This works for both production (Solidity passes calldata through memory-accepting free functions) and tests.

2. **`bytes32` vs `uint256` casts**: `OriginEndpoint.eventSig` is `bytes32`; `EventSignatures` constants are `uint256`; `IReactive.LogRecord.topic_0` is `uint256`. Cast explicitly: `bytes32(sig)` when building `OriginEndpoint`, `uint256(eventSig)` when passing to subscription functions.

3. **`uint64` gas_limit in Callback event**: `IReactive.Callback` declares `gas_limit` as `uint64 indexed`. `CallbackEndpoint.gasLimit` is `uint256`. Cast to `uint64` at emit site.

4. **Storage accessor underscore prefix**: reactive-hooks exports `_originRegistryStorage()`, `_callbackRegistryStorage()`, `_eventDispatchStorage()` (with leading `_`). Import with aliases or use the underscored names directly.

5. **ReactVM guard (`requireVM`) in tests**: `reactVMBatchSubscription` calls `requireVM()` which checks `extcodesize(0x...fffFfF)`. In Forge tests, use `vm.etch(address(0x0000000000000000000000000000000000fffFfF), hex"00")` to fake ReactVM environment.

6. **`decodeV3PoolAddedData` calldata/memory**: The outer `abi.decode` produces `bytes memory`. The decode function must accept `bytes memory`, not `bytes calldata`.

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `lib/reactive-hooks` | Update submodule | Pull EDT primitives at `01bbb3e` |
| `src/fee-concentration-index-v2/FCIProtocolFacet.sol` | Modify | Add `bytes data` to `PoolAdded` event |
| `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol` | Modify | Add `bytes data` to `PoolAdded` event + encode V3 data in `listen()` |
| `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/EventSignatures.sol` | Modify | Add `POOL_ADDED_SIG` import |
| `src/fee-concentration-index-v2/libraries/PoolAddedSig.sol` | Create | Shared `POOL_ADDED_SIG` constant |
| `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PoolAddedLib.sol` | Create | Encode/decode `PoolAdded` data for V3 |
| `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PayloadMutatorLib.sol` | Create | V3 log enrichment (pre-swap tick injection) |
| `src/fee-concentration-index-v2/modules/ReactiveDispatchMod.sol` | Create | Protocol-agnostic self-sync handler + EDT dispatch |
| `test/fee-concentration-index-v2/protocols/uniswap-v3/mocks/MockCallbackReceiver.sol` | Create | Test double for `unlockCallbackReactive` |
| `test/fee-concentration-index-v2/protocols/uniswap-v3/Flow3_1_ListenDispatch.t.sol` | Create | End-to-end flow test |

---

## Task 0: Update reactive-hooks submodule

**Files:**
- Modify: `lib/reactive-hooks` (submodule pointer)

- [ ] **Step 1: Update submodule to latest origin/main**

```bash
cd lib/reactive-hooks && git checkout origin/main && cd ../..
```

- [ ] **Step 2: Verify EDT files exist**

```bash
ls lib/reactive-hooks/src/libraries/EventDispatchLib.sol
ls lib/reactive-hooks/src/types/OriginEndpoint.sol
ls lib/reactive-hooks/src/types/CallbackEndpoint.sol
ls lib/reactive-hooks/src/types/Binding.sol
```

Expected: All 4 files exist.

- [ ] **Step 3: Verify forge can resolve imports**

```bash
forge build --skip test script 2>&1 | head -20
```

Expected: No import resolution errors for `reactive-hooks/` paths. Other errors are fine (existing TODOs).

- [ ] **Step 4: Commit**

```bash
git add lib/reactive-hooks
git commit -m "chore(008): update reactive-hooks submodule to 01bbb3e (EDT)"
```

---

## Task 1: PoolAddedSig + EventSignatures update

**Files:**
- Create: `src/fee-concentration-index-v2/libraries/PoolAddedSig.sol`
- Modify: `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/EventSignatures.sol`

- [ ] **Step 1: Compute POOL_ADDED_SIG**

```bash
cast sig-event "PoolAdded(address,address,bytes32,bytes2,bytes)"
```

Use the output hash value in the next step.

- [ ] **Step 2: Create PoolAddedSig.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// keccak256("PoolAdded(address,address,bytes32,bytes2,bytes)")
// Shared across all protocol facets — unified topic0.
// This constant lives here (not in V3-specific EventSignatures.sol) because
// it is protocol-agnostic — the RN constructor subscribes to this for all protocols.
uint256 constant POOL_ADDED_SIG = 0x__INSERT_COMPUTED_VALUE__;
```

- [ ] **Step 3: Add import to EventSignatures.sol**

Add at the bottom of `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/EventSignatures.sol` (for co-location convenience — canonical import is from `PoolAddedSig.sol`):

```solidity
import {POOL_ADDED_SIG} from "@fee-concentration-index-v2/libraries/PoolAddedSig.sol";
```

- [ ] **Step 4: Verify build**

```bash
forge build --skip test script 2>&1 | head -20
```

- [ ] **Step 5: Commit**

```bash
git add src/fee-concentration-index-v2/libraries/PoolAddedSig.sol \
        src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/EventSignatures.sol
git commit -m "feat(008): add POOL_ADDED_SIG constant"
```

---

## Task 2: UniswapV3PoolAddedLib — encode/decode

**Files:**
- Create: `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PoolAddedLib.sol`

- [ ] **Step 1: Create UniswapV3PoolAddedLib.sol**

Note: `decodeV3PoolAddedData` accepts `bytes memory` (not `calldata`) because the caller decodes `log.data` into `bytes memory` first via `abi.decode`. See Known Issue #6.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @dev Encode/decode the `bytes data` field of PoolAdded for Uniswap V3.
/// V3 data = (uint256 chainId, address pool, address protocolStateView).
/// For V3, protocolStateView == pool (the pool IS the state source).

function encodeV3PoolAddedData(
    uint256 chainId,
    address pool,
    address protocolStateView
) pure returns (bytes memory) {
    return abi.encode(chainId, pool, protocolStateView);
}

function decodeV3PoolAddedData(
    bytes memory data
) pure returns (uint256 chainId, address pool, address protocolStateView) {
    (chainId, pool, protocolStateView) = abi.decode(data, (uint256, address, address));
}
```

- [ ] **Step 2: Verify build**

```bash
forge build --skip test script 2>&1 | head -20
```

- [ ] **Step 3: Commit**

```bash
git add src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PoolAddedLib.sol
git commit -m "feat(008): add UniswapV3PoolAddedLib — encode/decode PoolAdded data"
```

---

## Task 3: Modify PoolAdded event + listen()

**Files:**
- Modify: `src/fee-concentration-index-v2/FCIProtocolFacet.sol:18,28`
- Modify: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol:43,54-61`

- [ ] **Step 1: Update FCIProtocolFacet.sol PoolAdded event**

Change line 18 from:
```solidity
event PoolAdded(address indexed facet, address indexed callback, PoolId indexed poolId, bytes2 protocolFlag);
```
To:
```solidity
event PoolAdded(address indexed facet, address indexed callback, PoolId indexed poolId, bytes2 protocolFlag, bytes data);
```

Update line 28 `emit` to pass empty data:
```solidity
emit PoolAdded(address(this), address(getProtocolCallback(PROTOCOL_FLAG)), poolId, PROTOCOL_FLAG, "");
```

- [ ] **Step 2: Update UniswapV3Facet.sol PoolAdded event**

Change line 43 from:
```solidity
event PoolAdded(address indexed facet, address indexed callback, PoolId indexed poolId, bytes2 protocolFlag);
```
To:
```solidity
event PoolAdded(address indexed facet, address indexed callback, PoolId indexed poolId, bytes2 protocolFlag, bytes data);
```

- [ ] **Step 3: Update UniswapV3Facet.listen() to encode V3 data**

Add import at top of `UniswapV3Facet.sol`:
```solidity
import {encodeV3PoolAddedData} from "./libraries/UniswapV3PoolAddedLib.sol";
```

Change lines 54-61 `listen()` to:
```solidity
function listen(bytes calldata poolRpt) payable external returns (PoolKey memory poolKey) {
    IUniswapV3Pool v3Pool = abi.decode(poolRpt, (IUniswapV3Pool));
    IHooks fciHook = IHooks(address(fciFacetAdminStorage(UNISWAP_V3).fci));
    poolKey = fromUniswapV3PoolToPoolKey(v3Pool, fciHook);
    PoolId poolId = PoolIdLibrary.toId(poolKey);
    addPool(UNISWAP_V3, poolId);
    emit PoolAdded(
        address(this),
        address(fciFacetAdminStorage(UNISWAP_V3).fci),
        poolId,
        UNISWAP_V3,
        encodeV3PoolAddedData(block.chainid, address(v3Pool), address(v3Pool))
    );
}
```

Note: `callback` changed from `protocolStateView` to `fci` — the actual `unlockCallbackReactive` target.

- [ ] **Step 4: Verify build**

```bash
forge build --skip test script 2>&1 | head -20
```

Expected: Compiles. Check build output for other files referencing the old `PoolAdded` signature.

- [ ] **Step 5: Commit**

```bash
git add src/fee-concentration-index-v2/FCIProtocolFacet.sol \
        src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol
git commit -m "feat(008): add bytes data to PoolAdded event + encode V3 data in listen()"
```

---

## Task 4: MockCallbackReceiver

**Files:**
- Create: `test/fee-concentration-index-v2/protocols/uniswap-v3/mocks/MockCallbackReceiver.sol`

- [ ] **Step 1: Create MockCallbackReceiver.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @dev Test double for unlockCallbackReactive. Stores received data for assertions.
contract MockCallbackReceiver {
    event CallbackReceived(bytes data);

    bytes public lastData;
    address public lastRvmSender;
    uint256 public callbackCount;

    function unlockCallbackReactive(address rvmSender, bytes calldata data) external {
        lastRvmSender = rvmSender;
        lastData = data;
        callbackCount++;
        emit CallbackReceived(data);
    }
}
```

- [ ] **Step 2: Verify build**

```bash
forge build --skip script 2>&1 | head -20
```

- [ ] **Step 3: Commit**

```bash
git add test/fee-concentration-index-v2/protocols/uniswap-v3/mocks/MockCallbackReceiver.sol
git commit -m "feat(008): add MockCallbackReceiver for flow 3.1 testing"
```

---

## Task 5: UniswapV3PayloadMutatorLib

**Files:**
- Create: `src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PayloadMutatorLib.sol`

Depends on: `UniswapV3ReactVMStorageMod.sol` (existing, provides `getLastTick`/`setLastTick`)

- [ ] **Step 1: Create UniswapV3PayloadMutatorLib.sol**

Note: Uses `memory` parameter for `LogRecord` (see Known Issue #1). Tick decoding uses `abi.decode` (not inline assembly) to avoid sign-extension bugs.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {getLastTick, setLastTick} from
    "@fee-concentration-index-v2/protocols/uniswap-v3/modules/UniswapV3ReactVMStorageMod.sol";
import {V3_SWAP_SIG} from
    "@fee-concentration-index-v2/protocols/uniswap-v3/libraries/EventSignatures.sol";

/// @dev Enriches raw V3 log data before callback emission.
/// Open extension point — other protocols implement their own mutator.
///
/// For V3 Swap: injects pre-swap tick (from TickShadow) alongside the raw log.
/// For V3 Mint/Burn: passes raw log through unchanged.
///
/// Returns: abi.encode(IReactive.LogRecord, bytes enrichment)
/// where enrichment is empty for Mint/Burn, or abi.encode(int24 tickBefore) for Swap.

function mutateV3Payload(
    IReactive.LogRecord memory log
) returns (bytes memory) {
    if (log.topic_0 == V3_SWAP_SIG) {
        uint256 chainId = log.chain_id;
        address pool = log._contract;
        (int24 lastTick, bool isSet) = getLastTick(chainId, pool);

        // Decode post-swap tick from V3 Swap event data.
        // V3 Swap data layout (ABI-encoded): (int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick)
        (,,,, int24 postSwapTick) = abi.decode(log.data, (int256, int256, uint160, uint128, int24));

        int24 tickBefore;
        if (isSet) {
            tickBefore = lastTick;
        } else {
            tickBefore = postSwapTick;
        }
        setLastTick(chainId, pool, postSwapTick);
        return abi.encode(log, abi.encode(tickBefore));
    }
    // Mint/Burn: pass through with empty enrichment
    return abi.encode(log, "");
}
```

- [ ] **Step 2: Verify build**

```bash
forge build --skip test script 2>&1 | head -20
```

- [ ] **Step 3: Commit**

```bash
git add src/fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PayloadMutatorLib.sol
git commit -m "feat(008): add UniswapV3PayloadMutatorLib — V3 log enrichment"
```

---

## Task 6: ReactiveDispatchMod — self-sync handler + EDT dispatch

**Files:**
- Create: `src/fee-concentration-index-v2/modules/ReactiveDispatchMod.sol`

Depends on: Tasks 1, 2, 5 (PoolAddedSig, UniswapV3PoolAddedLib, UniswapV3PayloadMutatorLib)

This is the largest file. Two responsibilities:
1. **Self-sync handler**: `PoolAdded` log → EDT registration + subscription
2. **Event dispatch**: V3 event log → EDT dispatch → payload mutator → Callback emit

- [ ] **Step 1: Create ReactiveDispatchMod.sol**

Note: All `IReactive.LogRecord` parameters are `memory` (see Known Issue #1). Storage accessors use `_` prefix (see Known Issue #4). `gas_limit` cast to `uint64` (see Known Issue #3).

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {ISubscriptionService} from "reactive-lib/interfaces/ISubscriptionService.sol";

// EDT primitives (note: storage accessors have _ prefix)
import {OriginEndpoint, originId} from "reactive-hooks/types/OriginEndpoint.sol";
import {CallbackEndpoint, callbackId} from "reactive-hooks/types/CallbackEndpoint.sol";
import {BindingState} from "reactive-hooks/types/Binding.sol";
import {
    OriginRegistryStorage, setOrigin, getOriginExists,
    _originRegistryStorage
} from "reactive-hooks/modules/OriginRegistryStorageMod.sol";
import {
    CallbackRegistryStorage, setCallback, getCallback,
    _callbackRegistryStorage
} from "reactive-hooks/modules/CallbackRegistryStorageMod.sol";
import {
    EventDispatchStorage, getBindingCountByOrigin,
    _eventDispatchStorage
} from "reactive-hooks/modules/EventDispatchStorageMod.sol";
import {
    immediateBind, dispatch, validateBind
} from "reactive-hooks/libraries/EventDispatchLib.sol";
import {reactVMBatchSubscription} from "reactive-hooks/libraries/SubscriptionLib.sol";

// Protocol-specific — V3
import {POOL_ADDED_SIG} from "@fee-concentration-index-v2/libraries/PoolAddedSig.sol";
import {UNISWAP_V3} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";
import {V3_SWAP_SIG, V3_MINT_SIG, V3_BURN_SIG, v3PoolSigs}
    from "@fee-concentration-index-v2/protocols/uniswap-v3/libraries/EventSignatures.sol";
import {decodeV3PoolAddedData}
    from "@fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PoolAddedLib.sol";
import {mutateV3Payload}
    from "@fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PayloadMutatorLib.sol";

// IUnlockCallbackReactiveExt selector
import {IUnlockCallbackReactiveExt}
    from "@reactive-integration/template/interfaces/IUnlockCallbackReactiveExt.sol";

uint64 constant CALLBACK_GAS_LIMIT = 1_000_000;

// ── Self-sync handler ──

/// @dev Called when ReactVM receives a PoolAdded log from cross-chain subscription.
/// Registers origins + callback + bindings in EDT, then subscribes to pool events.
/// Uses `memory` for LogRecord to support both production (calldata forwarded) and tests.
function handlePoolAdded(
    IReactive.LogRecord memory log,
    ISubscriptionService service
) {
    // PoolAdded has 3 indexed topics (facet, callback, poolId).
    // Non-indexed params (protocolFlag, data) are ABI-encoded in log.data.
    (bytes2 protocolFlag, bytes memory poolData) = abi.decode(log.data, (bytes2, bytes));

    // Extract callback target from indexed topic_2 (callback address)
    address callbackTarget = address(uint160(log.topic_2));

    if (protocolFlag == UNISWAP_V3) {
        handleV3PoolAdded(service, callbackTarget, poolData);
    }
    // Future protocols: else if (protocolFlag == UNISWAP_V4) { ... }
}

function handleV3PoolAdded(
    ISubscriptionService service,
    address callbackTarget,
    bytes memory poolData
) {
    (uint256 chainId, address pool, ) = decodeV3PoolAddedData(poolData);

    OriginRegistryStorage storage origins = _originRegistryStorage();
    CallbackRegistryStorage storage callbacks = _callbackRegistryStorage();
    EventDispatchStorage storage edt = _eventDispatchStorage();

    // Register 3 OriginEndpoints (Swap/Mint/Burn × pool)
    uint256[] memory sigs = v3PoolSigs();
    bytes32[] memory originIds = new bytes32[](3);
    for (uint256 i = 0; i < 3; i++) {
        OriginEndpoint memory origin = OriginEndpoint({
            chainId: uint32(chainId),
            emitter: pool,
            eventSig: bytes32(sigs[i])
        });
        originIds[i] = setOrigin(origins, origin);
    }

    // Register 1 CallbackEndpoint (idempotent — same target for all pools)
    CallbackEndpoint memory cb = CallbackEndpoint({
        chainId: uint32(chainId),
        target: callbackTarget,
        selector: IUnlockCallbackReactiveExt.unlockCallbackReactive.selector,
        gasLimit: CALLBACK_GAS_LIMIT
    });
    bytes32 cbId = setCallback(callbacks, cb);

    // Create 3 Bindings (one per origin → same callback)
    for (uint256 i = 0; i < 3; i++) {
        validateBind(origins, callbacks, originIds[i], cbId);
        immediateBind(edt, originIds[i], cbId);
    }

    // Subscribe to V3 pool events on the origin chain
    reactVMBatchSubscription(service, chainId, pool, sigs);
}

// ── Event dispatch (hot path) ──

/// @dev Called when ReactVM receives a V3 pool event (Swap/Mint/Burn).
/// Dispatches through EDT, runs payload mutator, emits Callback per active binding.
function dispatchEvent(IReactive.LogRecord memory log) {
    // Construct OriginEndpoint from log fields
    OriginEndpoint memory origin = OriginEndpoint({
        chainId: uint32(log.chain_id),
        emitter: log._contract,
        eventSig: bytes32(log.topic_0)
    });
    bytes32 oid = originId(origin);

    // Get active callbacks from EDT
    EventDispatchStorage storage edt = _eventDispatchStorage();
    bytes32[] memory activeCallbackIds = dispatch(edt, oid);

    if (activeCallbackIds.length == 0) return;

    // Run protocol payload mutator
    bytes memory enrichedPayload = mutateV3Payload(log);

    // Emit Callback per active callback
    CallbackRegistryStorage storage callbacks = _callbackRegistryStorage();
    for (uint256 i = 0; i < activeCallbackIds.length; i++) {
        CallbackEndpoint storage cb = getCallback(callbacks, activeCallbackIds[i]);
        // address(0) is rvmSender placeholder — callback proxy replaces with deployer EOA
        emit IReactive.Callback(
            uint256(cb.chainId),
            cb.target,
            uint64(cb.gasLimit),
            abi.encodeWithSelector(cb.selector, address(0), enrichedPayload)
        );
    }
}
```

**Implementation notes:**
- `handleV3PoolAdded` is a separate function (not `_handleV3PoolAdded`) to follow free-function naming without misleading `_` prefix.
- `CallbackEndpoint.gasLimit` is `uint256` in reactive-hooks but `IReactive.Callback.gas_limit` is `uint64 indexed`. The `uint64()` cast is explicit at the emit site.
- Idempotency: `setOrigin`, `setCallback`, `setBinding` all return existing ID if already registered. Safe against duplicate `PoolAdded` logs.

- [ ] **Step 2: Verify build**

```bash
forge build --skip test script 2>&1 | head -40
```

Fix any import resolution errors iteratively. The reactive-hooks import names above are based on actual source inspection but may need minor adjustments.

- [ ] **Step 3: Commit**

```bash
git add src/fee-concentration-index-v2/modules/ReactiveDispatchMod.sol
git commit -m "feat(008): add ReactiveDispatchMod — EDT self-sync handler + event dispatch"
```

---

## Task 7: Flow 3.1 end-to-end test

**Files:**
- Create: `test/fee-concentration-index-v2/protocols/uniswap-v3/Flow3_1_ListenDispatch.t.sol`

Depends on: All previous tasks (0-6)

**Key test design decisions:**
- `dispatchEvent` emits `IReactive.Callback` events (does NOT call receiver directly — there's no callback proxy in tests). Phase 2 tests use `vm.expectEmit` to verify the Callback event payload.
- `vm.etch` deploys dummy code at SystemContract address (`0x...fffFfF`) to satisfy `requireVM()` guard in `reactVMBatchSubscription`. Then `vm.mockCall` mocks the actual `subscribe()` call to be a no-op.

- [ ] **Step 1: Write Flow3_1_ListenDispatch.t.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {ISubscriptionService} from "reactive-lib/interfaces/ISubscriptionService.sol";

// EDT + dispatch
import {handlePoolAdded, dispatchEvent} from
    "@fee-concentration-index-v2/modules/ReactiveDispatchMod.sol";
import {
    _originRegistryStorage, getOriginExists, OriginRegistryStorage
} from "reactive-hooks/modules/OriginRegistryStorageMod.sol";
import {
    _eventDispatchStorage, getBindingCountByOrigin, EventDispatchStorage
} from "reactive-hooks/modules/EventDispatchStorageMod.sol";

// Libs
import {encodeV3PoolAddedData} from
    "@fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PoolAddedLib.sol";
import {V3_SWAP_SIG, V3_MINT_SIG, V3_BURN_SIG} from
    "@fee-concentration-index-v2/protocols/uniswap-v3/libraries/EventSignatures.sol";
import {POOL_ADDED_SIG} from "@fee-concentration-index-v2/libraries/PoolAddedSig.sol";
import {UNISWAP_V3} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";
import {OriginEndpoint, originId} from "reactive-hooks/types/OriginEndpoint.sol";

// Test mock
import {MockCallbackReceiver} from "./mocks/MockCallbackReceiver.sol";

contract Flow3_1_ListenDispatch is Test {
    MockCallbackReceiver receiver;

    // Fake SystemContract address for requireVM() guard
    address constant SYSTEM_CONTRACT = 0x0000000000000000000000000000000000fffFfF;

    // Mock subscription service (deployed at a known address)
    address mockService;

    address constant MOCK_POOL = address(0xBEEF);
    uint256 constant ORIGIN_CHAIN = 1;

    function setUp() public {
        receiver = new MockCallbackReceiver();

        // Deploy dummy code at SystemContract to satisfy requireVM() check.
        // requireVM() checks extcodesize(0x...fffFfF) == 0 for ReactVM.
        // In ReactVM: no code at system address → size == 0 → vm = true.
        // So we do NOT etch code there — leave it empty to simulate ReactVM.
        // But reactVMBatchSubscription calls service.subscribe() which would revert
        // on address(0). Deploy a mock service and mock the subscribe call.
        mockService = address(new MockSubscriptionService());
    }

    // ── Phase 1: PoolAdded → EDT registration ──

    function test_handlePoolAdded_registers_3_origins_1_callback_3_bindings() public {
        IReactive.LogRecord memory log = _buildPoolAddedLog(
            ORIGIN_CHAIN, MOCK_POOL, address(receiver)
        );

        handlePoolAdded(log, ISubscriptionService(mockService));

        // Verify 3 origins registered
        _assertOriginExists(ORIGIN_CHAIN, MOCK_POOL, V3_SWAP_SIG);
        _assertOriginExists(ORIGIN_CHAIN, MOCK_POOL, V3_MINT_SIG);
        _assertOriginExists(ORIGIN_CHAIN, MOCK_POOL, V3_BURN_SIG);

        // Verify 3 bindings (1 per origin per pool, all to same callback)
        _assertBindingCount(ORIGIN_CHAIN, MOCK_POOL, V3_SWAP_SIG, 1);
        _assertBindingCount(ORIGIN_CHAIN, MOCK_POOL, V3_MINT_SIG, 1);
        _assertBindingCount(ORIGIN_CHAIN, MOCK_POOL, V3_BURN_SIG, 1);
    }

    // ── Phase 2: V3 event → dispatch → Callback event emitted ──

    function test_dispatchEvent_swap_emits_callback() public {
        _registerPool();

        IReactive.LogRecord memory log = _buildV3SwapLog(ORIGIN_CHAIN, MOCK_POOL);

        // Expect IReactive.Callback event to be emitted.
        // We check topic1 (chain_id) and topic2 (target address).
        vm.expectEmit(true, true, false, false);
        emit IReactive.Callback(ORIGIN_CHAIN, address(receiver), 0, "");

        dispatchEvent(log);
    }

    function test_dispatchEvent_mint_emits_callback() public {
        _registerPool();

        IReactive.LogRecord memory log = _buildV3MintLog(ORIGIN_CHAIN, MOCK_POOL);

        vm.expectEmit(true, true, false, false);
        emit IReactive.Callback(ORIGIN_CHAIN, address(receiver), 0, "");

        dispatchEvent(log);
    }

    function test_dispatchEvent_burn_emits_callback() public {
        _registerPool();

        IReactive.LogRecord memory log = _buildV3BurnLog(ORIGIN_CHAIN, MOCK_POOL);

        vm.expectEmit(true, true, false, false);
        emit IReactive.Callback(ORIGIN_CHAIN, address(receiver), 0, "");

        dispatchEvent(log);
    }

    // ── Helpers ──

    function _registerPool() internal {
        IReactive.LogRecord memory log = _buildPoolAddedLog(
            ORIGIN_CHAIN, MOCK_POOL, address(receiver)
        );
        handlePoolAdded(log, ISubscriptionService(mockService));
    }

    function _buildPoolAddedLog(
        uint256 chainId,
        address pool,
        address callbackTarget
    ) internal pure returns (IReactive.LogRecord memory) {
        bytes memory poolData = encodeV3PoolAddedData(chainId, pool, pool);
        bytes memory logData = abi.encode(UNISWAP_V3, poolData);

        return IReactive.LogRecord({
            chain_id: chainId,
            _contract: address(0),
            topic_0: POOL_ADDED_SIG,
            topic_1: uint256(uint160(address(0))),
            topic_2: uint256(uint160(callbackTarget)),
            topic_3: 0,
            data: logData,
            block_number: 0,
            op_code: 0,
            block_hash: 0,
            tx_hash: 0,
            log_index: 0
        });
    }

    function _buildV3SwapLog(
        uint256 chainId,
        address pool
    ) internal pure returns (IReactive.LogRecord memory) {
        int24 tick = 100;
        bytes memory swapData = abi.encode(
            int256(1e18),
            int256(-1e18),
            uint160(1 << 96),
            uint128(1e18),
            tick
        );

        return IReactive.LogRecord({
            chain_id: chainId,
            _contract: pool,
            topic_0: V3_SWAP_SIG,
            topic_1: uint256(uint160(address(0x1))),
            topic_2: uint256(uint160(address(0x2))),
            topic_3: 0,
            data: swapData,
            block_number: 1,
            op_code: 0,
            block_hash: 0,
            tx_hash: 0,
            log_index: 0
        });
    }

    function _buildV3MintLog(
        uint256 chainId,
        address pool
    ) internal pure returns (IReactive.LogRecord memory) {
        bytes memory mintData = abi.encode(
            address(0x1),
            uint128(1e18),
            uint256(1e18),
            uint256(1e18)
        );

        return IReactive.LogRecord({
            chain_id: chainId,
            _contract: pool,
            topic_0: V3_MINT_SIG,
            topic_1: uint256(uint160(address(0x3))),
            topic_2: uint256(uint24(int24(-100))),
            topic_3: uint256(uint24(int24(100))),
            data: mintData,
            block_number: 2,
            op_code: 0,
            block_hash: 0,
            tx_hash: 0,
            log_index: 0
        });
    }

    function _buildV3BurnLog(
        uint256 chainId,
        address pool
    ) internal pure returns (IReactive.LogRecord memory) {
        bytes memory burnData = abi.encode(
            uint128(1e18),
            uint256(1e18),
            uint256(1e18)
        );

        return IReactive.LogRecord({
            chain_id: chainId,
            _contract: pool,
            topic_0: V3_BURN_SIG,
            topic_1: uint256(uint160(address(0x3))),
            topic_2: uint256(uint24(int24(-100))),
            topic_3: uint256(uint24(int24(100))),
            data: burnData,
            block_number: 3,
            op_code: 0,
            block_hash: 0,
            tx_hash: 0,
            log_index: 0
        });
    }

    function _assertOriginExists(uint256 chainId, address pool, uint256 sig) internal view {
        OriginEndpoint memory o = OriginEndpoint({
            chainId: uint32(chainId),
            emitter: pool,
            eventSig: bytes32(sig)
        });
        bytes32 oid = originId(o);
        assertTrue(getOriginExists(_originRegistryStorage(), oid), "origin not registered");
    }

    function _assertBindingCount(uint256 chainId, address pool, uint256 sig, uint256 expected) internal view {
        OriginEndpoint memory o = OriginEndpoint({
            chainId: uint32(chainId),
            emitter: pool,
            eventSig: bytes32(sig)
        });
        bytes32 oid = originId(o);
        assertEq(getBindingCountByOrigin(_eventDispatchStorage(), oid), expected, "wrong binding count");
    }
}

/// @dev Minimal mock that accepts any subscribe/unsubscribe call without reverting.
contract MockSubscriptionService {
    fallback() external payable {}
    receive() external payable {}
}
```

**Implementation notes:**
- `MockSubscriptionService` is a fallback contract that accepts all calls — `reactVMBatchSubscription` calls `service.subscribe()` which will succeed on the mock.
- The `requireVM()` guard in `SubscriptionLib` checks `extcodesize(0x...fffFfF) == 0` for ReactVM detection. In Forge tests, no code exists at that address by default, so the check should pass (ReactVM = true). If it doesn't, use `vm.etch` to ensure the address has no code.
- Phase 2 tests use `vm.expectEmit(true, true, false, false)` — checks `chain_id` and `_contract` (target) indexed topics, skips `gas_limit` and `payload` data. This verifies the Callback was emitted to the correct chain + target.

- [ ] **Step 2: Run tests**

```bash
forge test --match-path "test/fee-concentration-index-v2/protocols/uniswap-v3/Flow3_1*" -vv
```

Expected: 4 tests pass. If `requireVM()` reverts, check the extcodesize logic and add `vm.etch` if needed.

- [ ] **Step 3: Fix any failures**

Common issues:
1. Import resolution → fix paths against actual reactive-hooks exports
2. `requireVM` revert → verify no code at SystemContract address; if needed, adjust mock setup
3. `calldata`/`memory` compilation errors → ensure all dispatch functions use `memory` params

- [ ] **Step 4: All tests pass**

```bash
forge test --match-path "test/fee-concentration-index-v2/protocols/uniswap-v3/Flow3_1*" -vv
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add test/fee-concentration-index-v2/protocols/uniswap-v3/Flow3_1_ListenDispatch.t.sol
git commit -m "feat(008): add Flow 3.1 end-to-end test — listen → EDT → dispatch → callback"
```

---

## Task Summary

| Task | Description | Depends On |
|------|-------------|------------|
| 0 | Update reactive-hooks submodule | — |
| 1 | PoolAddedSig + EventSignatures | 0 |
| 2 | UniswapV3PoolAddedLib | 0 |
| 3 | Modify PoolAdded event + listen() | 2 |
| 4 | MockCallbackReceiver | 0 |
| 5 | UniswapV3PayloadMutatorLib | 0 |
| 6 | ReactiveDispatchMod | 1, 2, 5 |
| 7 | Flow 3.1 end-to-end test | 0-6 |

**Parallelizable:** Tasks 1, 2, 4, 5 can run in parallel after Task 0.

**Critical path:** 0 → (1 + 2 + 5) → 6 → 7
