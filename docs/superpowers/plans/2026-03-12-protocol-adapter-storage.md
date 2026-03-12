# Protocol Adapter Storage Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce per-protocol adapter storage with centralized dispatch, replacing inline ternary duplication in the ext mod and simplifying OraclePayoffStorage.

**Architecture:** Three new files under `src/reactive-integration/template/` (storage, lib, mod) provide the protocol-adapter pattern. The existing ext mod becomes a re-export shim. OraclePayoffStorage drops `PoolKey + reactive` in favor of a `bytes32 adapterSlot` reference. Primary callers (`FeeConcentrationIndex.sol`, `FeeConcentrationIndexForkHarness.sol`) migrate imports; out-of-scope callers (`ReactiveHookAdapter.sol`, reactive-integration tests) keep working via the shim.

**Tech Stack:** Solidity ^0.8.26, Foundry (forge test), diamond storage pattern (keccak256 slot hashing), free functions (SCOP convention — no `library` keyword).

**Spec:** `docs/superpowers/specs/2026-03-12-protocol-adapter-storage-design.md`

---

## Chunk 1: New Primitives

### Task 1: foundry.toml remapping + ProtocolAdapterStorage.sol

**Files:**
- Modify: `foundry.toml:14-41` — add `@protocol-adapter/` remapping
- Create: `src/reactive-integration/template/storage/ProtocolAdapterStorage.sol`

- [ ] **Step 1: Add foundry.toml remapping**

In `foundry.toml`, add this line after the existing `@reactive-integration/` remapping (line 36):

```toml
"@protocol-adapter/=src/reactive-integration/template/",
```

- [ ] **Step 2: Create ProtocolAdapterStorage.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";

/// @dev Per-protocol adapter storage. One instance per protocol at a distinct diamond slot.
/// See docs/superpowers/specs/2026-03-12-protocol-adapter-storage-design.md
struct ProtocolAdapterStorage {
    address protocolState;   // V4: IPoolManager, V3: IUniswapV3Factory — cast at call site
    IHooks  fciEntryPoint;   // typed IHooks for assignment compat with PoolKey.hooks; cast to IFeeConcentrationIndex at call sites
    PoolKey poolKey;          // V4-shaped PoolKey (V3 adapters construct via fromV3Pool). For V4 native, consumed only by vault oracle path
    bool    reactive;         // per-pool flag — true for V3, also true for V4 pools that missed initial hook registration
}

bytes32 constant V4_ADAPTER_SLOT = keccak256("thetaSwap.protocolAdapter.uniswapV4");
bytes32 constant V3_ADAPTER_SLOT = keccak256("thetaSwap.protocolAdapter.uniswapV3");

function protocolAdapterStorage(bytes32 slot) pure returns (ProtocolAdapterStorage storage $) {
    assembly { $.slot := slot }
}

function v4AdapterStorage() pure returns (ProtocolAdapterStorage storage $) {
    return protocolAdapterStorage(V4_ADAPTER_SLOT);
}

function v3AdapterStorage() pure returns (ProtocolAdapterStorage storage $) {
    return protocolAdapterStorage(V3_ADAPTER_SLOT);
}
```

- [ ] **Step 3: Verify compilation**

Run: `forge build`
Expected: compiles without errors

- [ ] **Step 4: Commit**

```bash
git add -f foundry.toml src/reactive-integration/template/storage/ProtocolAdapterStorage.sol
git commit -m "feat(protocol-adapter): add ProtocolAdapterStorage struct, slot constants, accessors"
```

---

### Task 2: ProtocolAdapterStorage unit test

**Files:**
- Create: `test/reactive-integration/template/ProtocolAdapterStorage.t.sol`

- [ ] **Step 1: Write the test**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {
    ProtocolAdapterStorage,
    V4_ADAPTER_SLOT, V3_ADAPTER_SLOT,
    protocolAdapterStorage,
    v4AdapterStorage, v3AdapterStorage
} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";

contract ProtocolAdapterStorageTest is Test {
    /// @dev V4 and V3 slots are disjoint
    function test_slots_are_disjoint() public pure {
        assertTrue(V4_ADAPTER_SLOT != V3_ADAPTER_SLOT);
    }

    /// @dev Convenience aliases return same storage as parameterized accessor
    function test_v4_alias_matches_parameterized() public {
        ProtocolAdapterStorage storage a = v4AdapterStorage();
        ProtocolAdapterStorage storage b = protocolAdapterStorage(V4_ADAPTER_SLOT);
        // Write via a, read via b
        a.protocolState = address(0xBEEF);
        assertEq(b.protocolState, address(0xBEEF));
    }

    function test_v3_alias_matches_parameterized() public {
        ProtocolAdapterStorage storage a = v3AdapterStorage();
        ProtocolAdapterStorage storage b = protocolAdapterStorage(V3_ADAPTER_SLOT);
        a.protocolState = address(0xCAFE);
        assertEq(b.protocolState, address(0xCAFE));
    }

    /// @dev V4 and V3 storage do not collide
    function test_v4_v3_storage_isolated() public {
        ProtocolAdapterStorage storage v4 = v4AdapterStorage();
        ProtocolAdapterStorage storage v3 = v3AdapterStorage();
        v4.protocolState = address(0x1111);
        v3.protocolState = address(0x2222);
        assertEq(v4.protocolState, address(0x1111));
        assertEq(v3.protocolState, address(0x2222));
    }

    /// @dev All struct fields are writable and readable
    function test_all_fields_roundtrip() public {
        ProtocolAdapterStorage storage $ = v4AdapterStorage();
        $.protocolState = address(0xAAAA);
        $.fciEntryPoint = IHooks(address(0xBBBB));
        $.poolKey = PoolKey({
            currency0: Currency.wrap(address(0x1)),
            currency1: Currency.wrap(address(0x2)),
            fee: 3000,
            tickSpacing: 60,
            hooks: IHooks(address(0xBBBB))
        });
        $.reactive = true;

        assertEq($.protocolState, address(0xAAAA));
        assertEq(address($.fciEntryPoint), address(0xBBBB));
        assertEq($.poolKey.fee, 3000);
        assertTrue($.reactive);
    }
}
```

- [ ] **Step 2: Run test to verify it passes**

Run: `forge test --match-path "test/reactive-integration/template/ProtocolAdapterStorage.t.sol" -vv`
Expected: 4 tests PASS

- [ ] **Step 3: Commit**

```bash
git add -f test/reactive-integration/template/ProtocolAdapterStorage.t.sol
git commit -m "test(protocol-adapter): unit tests for ProtocolAdapterStorage slots and accessors"
```

---

### Task 3: ProtocolAdapterLib.sol

**Files:**
- Create: `src/reactive-integration/template/libraries/ProtocolAdapterLib.sol`

**Dependencies:** Task 1 (ProtocolAdapterStorage.sol must exist)

**Context:** This file contains two groups of free functions:
1. `fciStorageFor(hookData)` — centralizes the inline ternary dispatch from the ext mod
2. `getDeltaPlusEpoch(adapter)`, `getDeltaPlus(adapter)` — oracle read helpers used by the vault

**Reference files:**
- `src/reactive-integration/modules/FeeConcentrationIndexStorageMultiProtocolReactiveExtMod.sol` — the existing inline ternary pattern being replaced
- `src/reactive-integration/uniswapV3/types/HookDataFlagsMod.sol` — `isUniswapV3Reactive(hookData)` function
- `src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol` — `fciStorage()`, `reactiveFciStorage()` accessors
- `src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol` — `getDeltaPlusEpoch`, `getDeltaPlus` signatures

- [ ] **Step 1: Create ProtocolAdapterLib.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {
    ProtocolAdapterStorage
} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";
import {
    FeeConcentrationIndexStorage,
    fciStorage, reactiveFciStorage
} from "@fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {isUniswapV3Reactive} from "@reactive-integration/uniswapV3/types/HookDataFlagsMod.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";

// ── FCI storage dispatch (Option C: hookData flags) ──

/// @dev Centralizes the inline ternary that was duplicated in every ext mod wrapper.
/// Single place to update when new protocols are added.
function fciStorageFor(bytes calldata hookData) pure returns (FeeConcentrationIndexStorage storage $) {
    if (isUniswapV3Reactive(hookData)) {
        return reactiveFciStorage();
    }
    return fciStorage();
}

// ── Oracle read helpers ──

/// @dev Read epoch-reset Δ⁺ from the FCI oracle via the adapter's entry point.
/// Consumed by OraclePayoffMod.oraclePoke().
function getDeltaPlusEpoch(ProtocolAdapterStorage storage $) view returns (uint128) {
    return IFeeConcentrationIndex(address($.fciEntryPoint))
        .getDeltaPlusEpoch($.poolKey, $.reactive);
}

/// @dev Read raw Δ⁺ from the FCI oracle via the adapter's entry point.
/// Provided for script/test callers (CompareDeltaPlus.s.sol, FeeConcentrationIndexBuilder.s.sol).
function getDeltaPlus(ProtocolAdapterStorage storage $) view returns (uint128) {
    return IFeeConcentrationIndex(address($.fciEntryPoint))
        .getDeltaPlus($.poolKey, $.reactive);
}
```

- [ ] **Step 2: Verify compilation**

Run: `forge build`
Expected: compiles without errors

- [ ] **Step 3: Commit**

```bash
git add -f src/reactive-integration/template/libraries/ProtocolAdapterLib.sol
git commit -m "feat(protocol-adapter): add ProtocolAdapterLib — fciStorageFor() + oracle read helpers"
```

---

### Task 4: ProtocolAdapterMod.sol

**Files:**
- Create: `src/reactive-integration/template/modules/ProtocolAdapterMod.sol`

**Dependencies:** Task 1 (storage), Task 3 (lib)

**Context:** This module replaces `FeeConcentrationIndexStorageMultiProtocolReactiveExtMod.sol`. Same 9 function signatures — takes `bytes calldata hookData`, dispatches through `fciStorageFor(hookData)` instead of inline ternaries. Also adds `initializeAdapter()`.

**Reference file:** `src/reactive-integration/modules/FeeConcentrationIndexStorageMultiProtocolReactiveExtMod.sol` — copy the exact function signatures and parameter names from this file (lines 19-93). The only change is the dispatch mechanism.

- [ ] **Step 1: Create ProtocolAdapterMod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId} from "v4-core/src/types/PoolId.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {TickRange} from "typed-uniswap-v4/fee-concentration-index/types/TickRangeMod.sol";
import {SwapCount} from "typed-uniswap-v4/fee-concentration-index/types/SwapCountMod.sol";
import {BlockCount} from "typed-uniswap-v4/fee-concentration-index/types/BlockCountMod.sol";
import {
    FeeConcentrationIndexStorage,
    registerPosition as _registerPosition,
    incrementPosCount as _incrementPosCount,
    decrementPosCount as _decrementPosCount,
    incrementOverlappingRanges as _incrementOverlappingRanges,
    deregisterPosition as _deregisterPosition,
    addStateTerm as _addStateTerm,
    setFeeGrowthBaseline as _setFeeGrowthBaseline,
    getFeeGrowthBaseline as _getFeeGrowthBaseline,
    deleteFeeGrowthBaseline as _deleteFeeGrowthBaseline
} from "@fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {fciStorageFor} from "@protocol-adapter/libraries/ProtocolAdapterLib.sol";
import {
    ProtocolAdapterStorage,
    protocolAdapterStorage
} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";

// ── 9 hookData-aware wrappers ──
// Same signatures as FeeConcentrationIndexStorageMultiProtocolReactiveExtMod.
// Dispatch via fciStorageFor(hookData) instead of inline ternaries.

function registerPosition(
    bytes calldata hookData,
    PoolId poolId,
    TickRange rk,
    bytes32 positionKey,
    int24 tickLower,
    int24 tickUpper,
    uint128 liquidity
) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    _registerPosition($, poolId, rk, positionKey, tickLower, tickUpper, liquidity);
}

function incrementPosCount(bytes calldata hookData, PoolId poolId) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    _incrementPosCount($, poolId);
}

function decrementPosCount(bytes calldata hookData, PoolId poolId) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    _decrementPosCount($, poolId);
}

function incrementOverlappingRanges(bytes calldata hookData, PoolId poolId, int24 tickMin, int24 tickMax) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    _incrementOverlappingRanges($, poolId, tickMin, tickMax);
}

function deregisterPosition(
    bytes calldata hookData,
    PoolId poolId,
    bytes32 positionKey,
    uint128 posLiquidity
) returns (TickRange rk, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    return _deregisterPosition($, poolId, positionKey, posLiquidity);
}

function addStateTerm(bytes calldata hookData, PoolId poolId, BlockCount blockLifetime, uint256 xSquaredQ128) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    _addStateTerm($, poolId, blockLifetime, xSquaredQ128);
}

function setFeeGrowthBaseline(bytes calldata hookData, PoolId poolId, bytes32 positionKey, uint256 feeGrowth0X128) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    _setFeeGrowthBaseline($, poolId, positionKey, feeGrowth0X128);
}

function getFeeGrowthBaseline(bytes calldata hookData, PoolId poolId, bytes32 positionKey) view returns (uint256) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    return _getFeeGrowthBaseline($, poolId, positionKey);
}

function deleteFeeGrowthBaseline(bytes calldata hookData, PoolId poolId, bytes32 positionKey) {
    FeeConcentrationIndexStorage storage $ = fciStorageFor(hookData);
    _deleteFeeGrowthBaseline($, poolId, positionKey);
}

// ── Adapter initialization ──

/// @dev Initialize a ProtocolAdapterStorage instance at the given slot.
/// Access control is enforced at the facet level (diamond proxy onlyOwner or init guard),
/// not within this free function — matches existing patterns (getCustodianStorage, etc.).
function initializeAdapter(
    bytes32 slot,
    address protocolState,
    IHooks fciEntryPoint,
    PoolKey calldata poolKey,
    bool reactive
) {
    ProtocolAdapterStorage storage $ = protocolAdapterStorage(slot);
    $.protocolState = protocolState;
    $.fciEntryPoint = fciEntryPoint;
    $.poolKey = poolKey;
    $.reactive = reactive;
}
```

- [ ] **Step 2: Verify compilation**

Run: `forge build`
Expected: compiles without errors

- [ ] **Step 3: Commit**

```bash
git add -f src/reactive-integration/template/modules/ProtocolAdapterMod.sol
git commit -m "feat(protocol-adapter): add ProtocolAdapterMod — 9 hookData wrappers + initializeAdapter"
```

---

### Task 5: ProtocolAdapterMod unit test

**Files:**
- Create: `test/reactive-integration/template/ProtocolAdapterMod.t.sol`

**Dependencies:** Task 4

**Context:** Verify that `initializeAdapter` correctly writes all fields, and that dispatch behavior matches the old ext mod (V4 hookData → fciStorage, V3 hookData → reactiveFciStorage). The 9 wrapper functions delegate to the same underlying `FeeConcentrationIndexStorageMod` functions that the ext mod did, so functional equivalence is verified by checking storage dispatch correctness.

**Reference:** `src/reactive-integration/uniswapV3/types/HookDataFlagsMod.sol` — check how `isUniswapV3Reactive(hookData)` reads the flag to construct appropriate test hookData.

- [ ] **Step 1: Read HookDataFlagsMod to understand flag encoding**

Read: `src/reactive-integration/uniswapV3/types/HookDataFlagsMod.sol`
Note the flag byte offset and value used by `isUniswapV3Reactive(hookData)`.

- [ ] **Step 2: Write the test**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {
    ProtocolAdapterStorage,
    V4_ADAPTER_SLOT, V3_ADAPTER_SLOT,
    protocolAdapterStorage
} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";
import {
    initializeAdapter,
    incrementPosCount
} from "@protocol-adapter/modules/ProtocolAdapterMod.sol";
import {
    FeeConcentrationIndexStorage,
    fciStorage, reactiveFciStorage
} from "@fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {FeeConcentrationState} from "typed-uniswap-v4/fee-concentration-index/types/FeeConcentrationStateMod.sol";

contract InitializeAdapterCaller {
    function doInit(
        bytes32 slot,
        address protocolState,
        IHooks fciEntryPoint,
        PoolKey calldata poolKey,
        bool reactive
    ) external {
        initializeAdapter(slot, protocolState, fciEntryPoint, poolKey, reactive);
    }

    function readAdapter(bytes32 slot) external view returns (
        address protocolState,
        address fciEntryPoint,
        uint24 fee,
        bool reactive
    ) {
        ProtocolAdapterStorage storage $ = protocolAdapterStorage(slot);
        return ($.protocolState, address($.fciEntryPoint), $.poolKey.fee, $.reactive);
    }
}

/// @dev Wrapper to call incrementPosCount with hookData dispatch.
/// Needed because free functions with calldata params require an external call boundary.
contract DispatchCaller {
    function doIncrementPosCount(bytes calldata hookData, PoolId poolId) external {
        incrementPosCount(hookData, poolId);
    }
}

contract ProtocolAdapterModTest is Test {
    InitializeAdapterCaller caller;
    DispatchCaller dispatcher;
    PoolKey testKey;

    function setUp() public {
        caller = new InitializeAdapterCaller();
        dispatcher = new DispatchCaller();
        testKey = PoolKey({
            currency0: Currency.wrap(address(0x1)),
            currency1: Currency.wrap(address(0x2)),
            fee: 3000,
            tickSpacing: 60,
            hooks: IHooks(address(0xBBBB))
        });
    }

    function test_initializeAdapter_writes_all_fields() public {
        caller.doInit(V4_ADAPTER_SLOT, address(0xAAAA), IHooks(address(0xBBBB)), testKey, false);
        (address ps, address fci, uint24 fee, bool reactive) = caller.readAdapter(V4_ADAPTER_SLOT);
        assertEq(ps, address(0xAAAA));
        assertEq(fci, address(0xBBBB));
        assertEq(fee, 3000);
        assertFalse(reactive);
    }

    function test_initializeAdapter_v3_reactive() public {
        caller.doInit(V3_ADAPTER_SLOT, address(0xCCCC), IHooks(address(0xDDDD)), testKey, true);
        (address ps, address fci, uint24 fee, bool reactive) = caller.readAdapter(V3_ADAPTER_SLOT);
        assertEq(ps, address(0xCCCC));
        assertEq(fci, address(0xDDDD));
        assertTrue(reactive);
    }

    function test_initializeAdapter_slots_isolated() public {
        caller.doInit(V4_ADAPTER_SLOT, address(0x1111), IHooks(address(0x2222)), testKey, false);
        caller.doInit(V3_ADAPTER_SLOT, address(0x3333), IHooks(address(0x4444)), testKey, true);
        (address ps4,,,) = caller.readAdapter(V4_ADAPTER_SLOT);
        (address ps3,,,) = caller.readAdapter(V3_ADAPTER_SLOT);
        assertEq(ps4, address(0x1111));
        assertEq(ps3, address(0x3333));
    }

    /// @dev Core dispatch test: V4 hookData (empty) routes to fciStorage(),
    /// V3 reactive hookData (0x03) routes to reactiveFciStorage().
    /// Verifies fciStorageFor() centralization produces same behavior as old inline ternaries.
    function test_fciStorageFor_dispatch_v4_vs_v3() public {
        PoolId poolId = PoolId.wrap(keccak256("test-pool"));

        // V4 hookData: empty bytes → routes to fciStorage()
        bytes memory v4HookData = "";
        dispatcher.doIncrementPosCount(v4HookData, poolId);

        // V3 reactive hookData: first byte = 0x03 (REACTIVE_FLAG | V3_FLAG)
        bytes memory v3HookData = abi.encodePacked(uint8(0x03));
        dispatcher.doIncrementPosCount(v3HookData, poolId);

        // Read both storage slots and verify posCount incremented in the correct one.
        // fciStorage() should have posCount = 1, reactiveFciStorage() should have posCount = 1.
        // If dispatch were broken, one would have 2 and the other 0.
        FeeConcentrationIndexStorage storage v4Store = fciStorage();
        FeeConcentrationIndexStorage storage v3Store = reactiveFciStorage();
        assertEq(v4Store.fciState[poolId].posCount, 1, "V4 hookData should route to fciStorage");
        assertEq(v3Store.fciState[poolId].posCount, 1, "V3 hookData should route to reactiveFciStorage");
    }
}
```

- [ ] **Step 3: Run test to verify it passes**

Run: `forge test --match-path "test/reactive-integration/template/ProtocolAdapterMod.t.sol" -vv`
Expected: 4 tests PASS

- [ ] **Step 4: Commit**

```bash
git add -f test/reactive-integration/template/ProtocolAdapterMod.t.sol
git commit -m "test(protocol-adapter): unit tests for initializeAdapter and slot isolation"
```

---

## Chunk 2: Ext Mod Deprecation + Import Migration

### Task 6: Deprecate ext mod → re-export shim

**Files:**
- Modify: `src/reactive-integration/modules/FeeConcentrationIndexStorageMultiProtocolReactiveExtMod.sol`

**Dependencies:** Task 4 (ProtocolAdapterMod must exist)

**Context:** Replace the entire file body with a deprecation header and re-exports from `ProtocolAdapterMod`. This ensures callers that are out of scope (`ReactiveHookAdapter.sol`, reactive-integration tests) continue to compile without changes.

- [ ] **Step 1: Replace ext mod with re-export shim**

Replace the entire content of `src/reactive-integration/modules/FeeConcentrationIndexStorageMultiProtocolReactiveExtMod.sol` with:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// DEPRECATED: This module is superseded by ProtocolAdapterMod.
// Import path: @protocol-adapter/modules/ProtocolAdapterMod.sol
// This file re-exports for backward compatibility. Remove once all callers migrate.

import {
    registerPosition,
    incrementPosCount, decrementPosCount,
    incrementOverlappingRanges,
    deregisterPosition,
    addStateTerm,
    setFeeGrowthBaseline, getFeeGrowthBaseline, deleteFeeGrowthBaseline,
    initializeAdapter
} from "@protocol-adapter/modules/ProtocolAdapterMod.sol";
```

- [ ] **Step 2: Verify full build**

Run: `forge build`
Expected: compiles without errors. All existing importers of the ext mod still resolve through re-exports.

- [ ] **Step 3: Commit**

```bash
git add src/reactive-integration/modules/FeeConcentrationIndexStorageMultiProtocolReactiveExtMod.sol
git commit -m "refactor: deprecate ext mod — re-export shim delegating to ProtocolAdapterMod"
```

---

### Task 7: Migrate FeeConcentrationIndex.sol and ForkHarness imports

**Files:**
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol:22-25`
- Modify: `test/fee-concentration-index/differential/FeeConcentrationIndexForkHarness.sol:19-23`

**Dependencies:** Task 6 (shim must exist so all other callers still work, but primary callers migrate to direct import)

- [ ] **Step 1: Update FeeConcentrationIndex.sol import**

In `src/fee-concentration-index/FeeConcentrationIndex.sol`, change lines 22-25:

**From:**
```solidity
import {
    registerPosition, setFeeGrowthBaseline, getFeeGrowthBaseline, deleteFeeGrowthBaseline,
    deregisterPosition, addStateTerm, incrementPosCount, decrementPosCount,
    incrementOverlappingRanges
} from "../reactive-integration/modules/FeeConcentrationIndexStorageMultiProtocolReactiveExtMod.sol";
```

**To:**
```solidity
import {
    registerPosition, setFeeGrowthBaseline, getFeeGrowthBaseline, deleteFeeGrowthBaseline,
    deregisterPosition, addStateTerm, incrementPosCount, decrementPosCount,
    incrementOverlappingRanges
} from "@protocol-adapter/modules/ProtocolAdapterMod.sol";
```

- [ ] **Step 2: Update FeeConcentrationIndexForkHarness.sol import**

In `test/fee-concentration-index/differential/FeeConcentrationIndexForkHarness.sol`, change lines 19-23:

**From:**
```solidity
import {
    registerPosition, setFeeGrowthBaseline, getFeeGrowthBaseline, deleteFeeGrowthBaseline,
    deregisterPosition, addStateTerm, incrementPosCount, decrementPosCount,
    incrementOverlappingRanges
} from "../../../src/reactive-integration/modules/FeeConcentrationIndexStorageMultiProtocolReactiveExtMod.sol";
```

**To:**
```solidity
import {
    registerPosition, setFeeGrowthBaseline, getFeeGrowthBaseline, deleteFeeGrowthBaseline,
    deregisterPosition, addStateTerm, incrementPosCount, decrementPosCount,
    incrementOverlappingRanges
} from "@protocol-adapter/modules/ProtocolAdapterMod.sol";
```

- [ ] **Step 3: Verify full build**

Run: `forge build`
Expected: compiles without errors

- [ ] **Step 4: Run existing FCI tests to verify no regressions**

Run: `forge test --match-path "test/fee-concentration-index/**" -vv`
Expected: all existing tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/fee-concentration-index/FeeConcentrationIndex.sol test/fee-concentration-index/differential/FeeConcentrationIndexForkHarness.sol
git commit -m "refactor: migrate FCI primary callers to @protocol-adapter/modules/ProtocolAdapterMod"
```

---

## Chunk 3: OraclePayoffStorage Simplification

### Task 8: Simplify OraclePayoffStorage struct

**Files:**
- Modify: `src/fci-token-vault/storage/OraclePayoffStorage.sol`

**Dependencies:** Task 1 (ProtocolAdapterStorage must exist for the design to make sense, though the struct change itself is independent)

**Context:** Drop `PoolKey poolKey` and `bool reactive` from the struct. Replace with `bytes32 adapterSlot` that references a `ProtocolAdapterStorage` instance. This saves ~5 storage slots per vault.

- [ ] **Step 1: Update OraclePayoffStorage struct**

In `src/fci-token-vault/storage/OraclePayoffStorage.sol`, replace the struct definition:

**From (lines 8-16):**
```solidity
struct OraclePayoffStorage {
    uint160 sqrtPriceStrike;
    uint160 sqrtPriceHWM;
    uint256 expiry;
    bool    settled;
    uint256 longPayoutPerToken; // Q96-scaled
    PoolKey poolKey;
    bool    reactive;
}
```

**To:**
```solidity
struct OraclePayoffStorage {
    uint160 sqrtPriceStrike;
    uint160 sqrtPriceHWM;
    uint256 expiry;
    bool    settled;
    uint256 longPayoutPerToken; // Q96-scaled
    bytes32 adapterSlot;        // references ProtocolAdapterStorage instance
}
```

Also remove the now-unused `PoolKey` import:

**From (line 4):**
```solidity
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
```

**To:** Remove this line entirely.

- [ ] **Step 2: Note — compilation will fail**

This is expected. `OraclePayoffMod.sol` still references `os.poolKey` and `os.reactive`. Task 9 fixes this. The test harnesses also reference these fields — Task 10 fixes those. Do NOT attempt `forge build` yet.

- [ ] **Step 3: Commit (partial, compilation broken)**

```bash
git add src/fci-token-vault/storage/OraclePayoffStorage.sol
git commit -m "refactor(oracle-payoff): drop PoolKey+reactive, add adapterSlot — compilation intentionally broken"
```

---

### Task 9: Update OraclePayoffMod.oraclePoke()

**Files:**
- Modify: `src/fci-token-vault/modules/OraclePayoffMod.sol:4-5,29,47-48`

**Dependencies:** Task 8 (struct must be updated), Task 3 (ProtocolAdapterLib must exist)

**Context:** `oraclePoke()` currently reads `os.poolKey.hooks` and `os.reactive` to call `IFeeConcentrationIndex`. After this change, it reads `os.adapterSlot` to get a `ProtocolAdapterStorage` reference, then uses `getDeltaPlusEpoch(adapter)` from `ProtocolAdapterLib`.

- [ ] **Step 1: Add new imports to OraclePayoffMod.sol**

Add after the existing imports (after line 31):

```solidity
import {
    ProtocolAdapterStorage,
    protocolAdapterStorage
} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";
import {getDeltaPlusEpoch} from "@protocol-adapter/libraries/ProtocolAdapterLib.sol";
```

- [ ] **Step 2: Remove the now-unused IFeeConcentrationIndex import**

Remove line 29:
```solidity
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
```

- [ ] **Step 3: Update oraclePoke() body**

In `oraclePoke()`, replace lines 47-48:

**From:**
```solidity
    uint128 deltaPlus = IFeeConcentrationIndex(address(os.poolKey.hooks))
        .getDeltaPlusEpoch(os.poolKey, os.reactive);
```

**To:**
```solidity
    ProtocolAdapterStorage storage adapter = protocolAdapterStorage(os.adapterSlot);
    uint128 deltaPlus = getDeltaPlusEpoch(adapter);
```

- [ ] **Step 4: Note — compilation still broken**

Test harnesses still reference `os.poolKey` and `os.reactive`. Task 10 fixes this.

- [ ] **Step 5: Commit (partial)**

```bash
git add src/fci-token-vault/modules/OraclePayoffMod.sol
git commit -m "refactor(oracle-payoff): oraclePoke reads adapter via ProtocolAdapterLib.getDeltaPlusEpoch"
```

---

### Task 10: Update vault harnesses and tests

**Files:**
- Modify: `test/fci-token-vault/helpers/FciTokenVaultHarness.sol:96-111,117-123`
- Modify: `test/fci-token-vault/helpers/CustodianHarness.sol:89-116`
- Modify: `test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol:112-118,343-345`
- Modify: `test/fci-token-vault/FciTokenVaultMod.t.sol:22-34`
- Modify: `test/fci-token-vault/integration/JitGameWelfareComparison.integration.t.sol:111`
- Modify: `test/fci-token-vault/unit/OraclePayoffMod.t.sol:35-39`

**Dependencies:** Task 8, Task 9

**Context:** The harnesses currently accept `PoolKey calldata poolKey` and `bool reactive` in their `harness_initVault` functions, and expose `harness_getPoolKey()` and `harness_getReactive()` getters. These must be updated to accept `bytes32 adapterSlot` instead. The integration test (`HedgedVsUnhedged`) calls `harness_initVault` and must pass the adapter slot plus call `initializeAdapter` separately.

- [ ] **Step 1: Update FciTokenVaultHarness.sol**

In `test/fci-token-vault/helpers/FciTokenVaultHarness.sol`:

Add import at the top (after line 28):
```solidity
import {
    ProtocolAdapterStorage,
    protocolAdapterStorage,
    V4_ADAPTER_SLOT
} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";
import {initializeAdapter} from "@protocol-adapter/modules/ProtocolAdapterMod.sol";
```

Keep the `PoolKey` import — it is still needed by `harness_initAdapter`.

Replace `harness_initVault` (lines 96-111):

**From:**
```solidity
    function harness_initVault(
        uint160 sqrtPriceStrike,
        uint256 expiry,
        PoolKey calldata poolKey,
        bool reactive,
        address collateralToken
    ) external {
        CustodianStorage storage cs = getCustodianStorage();
        cs.collateralToken = collateralToken;

        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceStrike = sqrtPriceStrike;
        os.expiry = expiry;
        os.poolKey = poolKey;
        os.reactive = reactive;
    }
```

**To:**
```solidity
    function harness_initVault(
        uint160 sqrtPriceStrike,
        uint256 expiry,
        bytes32 adapterSlot,
        address collateralToken
    ) external {
        CustodianStorage storage cs = getCustodianStorage();
        cs.collateralToken = collateralToken;

        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceStrike = sqrtPriceStrike;
        os.expiry = expiry;
        os.adapterSlot = adapterSlot;
    }

    /// @dev Initialize the protocol adapter storage for this harness.
    /// Called separately from harness_initVault — mirrors production flow.
    function harness_initAdapter(
        bytes32 slot,
        address protocolState,
        IHooks fciEntryPoint,
        PoolKey calldata poolKey,
        bool reactive
    ) external {
        initializeAdapter(slot, protocolState, fciEntryPoint, poolKey, reactive);
    }
```

Add `IHooks` import if not already present:
```solidity
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
```

Remove `harness_getPoolKey()` and `harness_getReactive()` (lines 117-123):
```solidity
    function harness_getPoolKey() external view returns (PoolKey memory) {
        return getOraclePayoffStorage().poolKey;
    }

    function harness_getReactive() external view returns (bool) {
        return getOraclePayoffStorage().reactive;
    }
```

Replace with:
```solidity
    function harness_getAdapterSlot() external view returns (bytes32) {
        return getOraclePayoffStorage().adapterSlot;
    }
```

- [ ] **Step 2: Update CustodianHarness.sol**

Apply the same pattern as Step 1 to `test/fci-token-vault/helpers/CustodianHarness.sol`. The changes are identical:

Add the same protocol-adapter imports.

Replace `harness_initVault` (lines 89-104) with the same `adapterSlot` version + `harness_initAdapter`.

Replace `harness_getPoolKey()` and `harness_getReactive()` (lines 110-116) with `harness_getAdapterSlot()`.

- [ ] **Step 3: Update HedgedVsUnhedged.integration.t.sol**

In `test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol`:

Add imports:
```solidity
import {V4_ADAPTER_SLOT} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";
```

Update `setUp()` — replace `vault.harness_initVault(...)` call (lines 112-118):

**From:**
```solidity
        vault.harness_initVault(
            strikePrice,
            block.timestamp + 5 days,
            key,
            false,
            Currency.unwrap(currency1)
        );
```

**To:**
```solidity
        vault.harness_initAdapter(
            V4_ADAPTER_SLOT,
            address(manager),
            key.hooks,
            key,
            false
        );
        vault.harness_initVault(
            strikePrice,
            block.timestamp + 5 days,
            V4_ADAPTER_SLOT,
            Currency.unwrap(currency1)
        );
```

Update `test_below_strike_no_false_trigger()` — replace `highStrikeVault.harness_initVault(...)` call (lines 343-346):

**From:**
```solidity
        highStrikeVault.harness_initVault(
            highStrike, block.timestamp + 5 days,
            key, false, Currency.unwrap(currency1)
        );
```

**To:**
```solidity
        highStrikeVault.harness_initAdapter(
            V4_ADAPTER_SLOT,
            address(manager),
            key.hooks,
            key,
            false
        );
        highStrikeVault.harness_initVault(
            highStrike, block.timestamp + 5 days,
            V4_ADAPTER_SLOT, Currency.unwrap(currency1)
        );
```

- [ ] **Step 4: Update FciTokenVaultMod.t.sol**

In `test/fci-token-vault/FciTokenVaultMod.t.sol`:

Add import:
```solidity
import {V4_ADAPTER_SLOT} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";
```

Replace lines 22-34:

**From:**
```solidity
        vault.harness_initVault(
            uint160(SqrtPriceLibrary.Q96), // strike = 1.0
            block.timestamp + 30 days,      // expiry
            PoolKey({
                currency0: Currency.wrap(address(0)),
                currency1: Currency.wrap(address(0)),
                fee: 0,
                tickSpacing: 0,
                hooks: IHooks(address(0))
            }),
            false,                          // reactive
            address(collateral)             // collateralToken
        );
```

**To:**
```solidity
        vault.harness_initAdapter(
            V4_ADAPTER_SLOT,
            address(0),
            IHooks(address(0)),
            PoolKey({
                currency0: Currency.wrap(address(0)),
                currency1: Currency.wrap(address(0)),
                fee: 0,
                tickSpacing: 0,
                hooks: IHooks(address(0))
            }),
            false
        );
        vault.harness_initVault(
            uint160(SqrtPriceLibrary.Q96), // strike = 1.0
            block.timestamp + 30 days,      // expiry
            V4_ADAPTER_SLOT,
            address(collateral)             // collateralToken
        );
```

- [ ] **Step 5: Update JitGameWelfareComparison.integration.t.sol**

In `test/fci-token-vault/integration/JitGameWelfareComparison.integration.t.sol`:

Add import:
```solidity
import {V4_ADAPTER_SLOT} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";
```

Replace `_deployVault()` helper — change line 111:

**From:**
```solidity
        v.harness_initVault(strike, block.timestamp + 7 days, key, false, collateral);
```

**To:**
```solidity
        v.harness_initAdapter(V4_ADAPTER_SLOT, address(manager), key.hooks, key, false);
        v.harness_initVault(strike, block.timestamp + 7 days, V4_ADAPTER_SLOT, collateral);
```

- [ ] **Step 6: Update OraclePayoffMod.t.sol**

In `test/fci-token-vault/unit/OraclePayoffMod.t.sol`:

Update `OraclePayoffModCaller.initOracleStorage` to also accept `adapterSlot`:

**From (lines 35-39):**
```solidity
    function initOracleStorage(uint160 strike, uint256 expiry) external {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceStrike = strike;
        os.expiry = expiry;
    }
```

**To:**
```solidity
    function initOracleStorage(uint160 strike, uint256 expiry, bytes32 adapterSlot) external {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceStrike = strike;
        os.expiry = expiry;
        os.adapterSlot = adapterSlot;
    }
```

Update `setUp()` call (line 64-67):

**From:**
```solidity
        caller.initOracleStorage(
            uint160(SqrtPriceLibrary.Q96), // strike = 1.0
            block.timestamp + 30 days       // expiry
        );
```

**To:**
```solidity
        caller.initOracleStorage(
            uint160(SqrtPriceLibrary.Q96), // strike = 1.0
            block.timestamp + 30 days,      // expiry
            bytes32(0)                       // adapterSlot — no poke tests exercise happy path
        );
```

- [ ] **Step 7: Verify full build**

Run: `forge build`
Expected: compiles without errors

- [ ] **Step 8: Run all vault tests**

Run: `forge test --match-path "test/fci-token-vault/**" -vv`
Expected: all tests PASS

- [ ] **Step 9: Run full test suite**

Run: `forge test -vv`
Expected: all tests PASS (no regressions anywhere)

- [ ] **Step 10: Commit**

```bash
git add test/fci-token-vault/
git commit -m "refactor(vault): update all harnesses and tests for adapterSlot-based OraclePayoffStorage"
```
