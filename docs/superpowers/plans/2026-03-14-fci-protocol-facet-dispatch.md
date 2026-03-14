# FCI Protocol Facet Dispatch — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FCI V2 template scaffold — interfaces, registry storage, facet storage primitives, dispatch preamble — and validate via differential tests against V1.

**Architecture:** FCI V2 copies V1's V4 inlined logic and adds a dispatch preamble: if `hookData.length > 0`, read `hookData[0]` as a flag byte, look up `fciRegistryStorage().protocolFacets[flags]`, and delegatecall the entire hook handler to the registered facet. V4 fast path (empty hookData) is unchanged. Registry lives in a separate diamond slot (`FeeConcentrationIndexRegistryStorage`) so protocol facets don't inherit unused fields.

**Tech Stack:** Solidity ^0.8.26, Uniswap V4 core (PoolManager, Hooks, StateLibrary), forge-std, diamond storage pattern.

**Scope:** Template + scaffold only. V3 facet, callback, and socket are deferred to a follow-up plan.

**Spec:** `docs/superpowers/specs/2026-03-14-fci-protocol-facet-dispatch-design.md`

**Incremental review:** Every piece of code (interface, struct, function) is presented individually for user approval before writing to file.

---

## Design Decisions (locked in spec, referenced by tasks)

1. **Registry storage separation:** `FeeConcentrationIndexRegistryStorage` at its own slot `keccak256("thetaSwap.fci.registry")` — NOT inside `FeeConcentrationIndexStorage`. This is a beneficial deviation from the spec's "New Files" table which listed a single `V2StorageMod`; the plan splits it into `RegistryStorageMod` (registry) + `V2StorageMod` (re-exports + slot routing).

2. **V2 import strategy:** V2's V4 fast path imports **directly** from `FeeConcentrationIndexStorageMod` (V1 storage), NOT through `ProtocolAdapterMod`. Since the V4 fast path always has empty hookData, the `ProtocolAdapterMod` dispatch is unnecessary indirection. V2 calls `fciStorage()` directly for V4 state, `registerPosition($, ...)` directly. The `ProtocolAdapterMod` wrappers are bypassed entirely in V2.

3. **`beforeRemoveLiquidity` dispatch:** Gets the same dispatch preamble as the other 4 hooks, even though the V4 fast path ignores hookData for position key derivation (uses 3-arg `derivePoolAndPosition`). The facet path receives full `msg.data` including hookData and uses its own position key derivation.

4. **Epoch storage V4 path:** V2's V4 fast path calls `addEpochTerm(poolId, ...)` unchanged from V1 — writes to the default epoch slot `keccak256("thetaSwap.fci.epoch")`. Protocol-scoped epoch terms are the facet's responsibility (each facet calls its own `protocolEpochFciStorage(flag)`).

5. **View function routing for all views:** V2 adds `bytes1 flags` overloads for ALL view functions: `getDeltaPlus`, `getDeltaPlusEpoch`, `getIndex`, `getAtNull`, `getThetaSum`. The `bool reactive` overloads are preserved for backward compat (`reactive=true` maps to `flags=0x03`).

6. **Import resolution:** V2 imports V1's `FeeConcentrationIndexStorage` struct via `@fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol`. This is the same struct that protocol facets use for their own storage. No duplicate definition — Solidity handles same-file imports idempotently.

7. **Slot derivation formulas (spec fidelity anchors):**
   - FCI state: `keccak256(abi.encode("thetaSwap.fci", flag))` for new protocols; V3 uses legacy `keccak256("ReactiveHookAdapter.fci.storage")`
   - Epoch state: `keccak256(abi.encode("thetaSwap.fci.epoch", flag))`
   - Transient base: `keccak256(abi.encode("thetaSwap.fci.transient", flag))`, then `+0/+1/+2/+3` for tick/feeGrowthLast/posLiquidity/rangeFeeGrowth
   - Registry: `keccak256("thetaSwap.fci.registry")`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/reactive-integration/template/interfaces/IFCIProtocolHooks.sol` | Create | 5 hook handler signatures (delegatecall targets) |
| `src/reactive-integration/template/interfaces/IFCIProtocolAdmin.sol` | Create | `listen()` signature (direct call) |
| `src/fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol` | Create | `FeeConcentrationIndexRegistryStorage` struct, slot constant, accessor |
| `src/reactive-integration/template/modules/FCIProtocolFacetStorageMod.sol` | Create | Per-protocol FCI storage slot derivation, transient storage helpers |
| `src/fee-concentration-index-v2/modules/FeeConcentrationIndexV2StorageMod.sol` | Create | Re-exports V1 storage + `_protocolFciStorage()` + `_protocolEpochFciStorage()` |
| `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol` | Create | Copy of V1 + dispatch preamble in all 5 hooks + registration + view routing |
| `test/fee-concentration-index-v2/FeeConcentrationIndexRegistryStorage.t.sol` | Create | Registry storage unit tests |
| `test/reactive-integration/template/FCIProtocolFacetStorageMod.t.sol` | Create | Facet storage + transient unit tests |
| `test/fee-concentration-index-v2/FeeConcentrationIndexV2Dispatch.t.sol` | Create | Dispatch unit tests (mock facet, unknown flag revert) |
| `test/fee-concentration-index-v2/differential/V4Differential.t.sol` | Create | V4 path: V2 == V1 state equivalence (fork test) |
| `foundry.toml` | Modify | Add `@fee-concentration-index-v2/` remapping |

---

## Chunk 1: Template Interfaces + Registry Storage

### Task 1: foundry.toml remapping

**Files:**
- Modify: `foundry.toml`

- [ ] **Step 1: Add remapping**

Add `"@fee-concentration-index-v2/=src/fee-concentration-index-v2/"` to the remappings array in `foundry.toml`, after the existing `@fee-concentration-index/` entry.

- [ ] **Step 2: Verify build still passes**

Run: `forge build`
Expected: Compiles with no errors (no new files reference the remapping yet).

- [ ] **Step 3: Commit**

```
feat(006): add @fee-concentration-index-v2/ remapping
```

---

### Task 2: IFCIProtocolHooks interface

**Files:**
- Create: `src/reactive-integration/template/interfaces/IFCIProtocolHooks.sol`

- [ ] **Step 1: Write interface**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {BeforeSwapDelta} from "v4-core/src/types/BeforeSwapDelta.sol";
import {SwapParams, ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";

/// @title IFCIProtocolHooks
/// @dev Called via delegatecall from FCI V2 dispatcher. Each protocol facet
/// implements these with protocol-specific behavioral logic.
interface IFCIProtocolHooks {
    function afterAddLiquidity(
        address sender, PoolKey calldata key, ModifyLiquidityParams calldata params,
        BalanceDelta delta0, BalanceDelta delta1, bytes calldata hookData
    ) external returns (bytes4, BalanceDelta);

    function beforeSwap(
        address sender, PoolKey calldata key, SwapParams calldata params,
        bytes calldata hookData
    ) external returns (bytes4, BeforeSwapDelta, uint24);

    function afterSwap(
        address sender, PoolKey calldata key, SwapParams calldata params,
        BalanceDelta delta, bytes calldata hookData
    ) external returns (bytes4, int128);

    function beforeRemoveLiquidity(
        address sender, PoolKey calldata key, ModifyLiquidityParams calldata params,
        bytes calldata hookData
    ) external returns (bytes4);

    function afterRemoveLiquidity(
        address sender, PoolKey calldata key, ModifyLiquidityParams calldata params,
        BalanceDelta delta0, BalanceDelta delta1, bytes calldata hookData
    ) external returns (bytes4, BalanceDelta);
}
```

- [ ] **Step 2: Verify build**

Run: `forge build`
Expected: Compiles.

- [ ] **Step 3: Commit**

```
feat(006): add IFCIProtocolHooks — delegatecall hook interface
```

---

### Task 3: IFCIProtocolAdmin interface

**Files:**
- Create: `src/reactive-integration/template/interfaces/IFCIProtocolAdmin.sol`

- [ ] **Step 1: Write interface**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";

/// @title IFCIProtocolAdmin
/// @dev Called directly on the facet contract (NOT via delegatecall from FCI).
/// Separated from IFCIProtocolHooks to prevent mixing call contexts.
interface IFCIProtocolAdmin {
    function listen(bytes calldata poolRpt) payable external returns (PoolKey memory poolKey);
}
```

- [ ] **Step 2: Verify build**

Run: `forge build`
Expected: Compiles.

- [ ] **Step 3: Commit**

```
feat(006): add IFCIProtocolAdmin — direct-call admin interface
```

---

### Task 4: FeeConcentrationIndexRegistryStorageMod

**Files:**
- Create: `src/fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol`

- [ ] **Step 1: Write storage module**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

struct FeeConcentrationIndexRegistryStorage {
    mapping(bytes1 => address) protocolFacets;
}

bytes32 constant FCI_REGISTRY_SLOT = keccak256("thetaSwap.fci.registry");

function fciRegistryStorage() pure returns (FeeConcentrationIndexRegistryStorage storage $) {
    bytes32 slot = FCI_REGISTRY_SLOT;
    assembly ("memory-safe") { $.slot := slot }
}
```

- [ ] **Step 2: Verify build**

Run: `forge build`
Expected: Compiles.

- [ ] **Step 3: Commit**

```
feat(006): add FeeConcentrationIndexRegistryStorageMod — separate registry slot
```

---

### Task 5: Registry storage unit test

**Files:**
- Create: `test/fee-concentration-index-v2/FeeConcentrationIndexRegistryStorage.t.sol`

- [ ] **Step 1: Write test**

Test that:
1. `FCI_REGISTRY_SLOT` is disjoint from all existing slots (complete list including `ReactiveHookAdapter.v3.storage`).
2. `fciRegistryStorage()` returns a writable pointer — write a facet address, read it back.
3. Different flag bytes map to different entries.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    FeeConcentrationIndexRegistryStorage,
    FCI_REGISTRY_SLOT,
    fciRegistryStorage
} from "@fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol";

contract FeeConcentrationIndexRegistryStorageTest is Test {
    function test_slot_disjoint_from_existing() public pure {
        assertTrue(FCI_REGISTRY_SLOT != keccak256("thetaSwap.fci"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("thetaSwap.fci.reactive"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("ReactiveHookAdapter.fci.storage"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("ReactiveHookAdapter.v3.storage"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("thetaSwap.fci.epoch"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("thetaSwap.protocolAdapter.uniswapV4"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("thetaSwap.protocolAdapter.uniswapV3"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("thetaswap.oracle-payoff"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("thetaswap.collateral-custodian"));
    }

    function test_write_and_read_facet() public {
        FeeConcentrationIndexRegistryStorage storage $ = fciRegistryStorage();
        address facet = address(0xBEEF);
        $.protocolFacets[bytes1(0x03)] = facet;
        assertEq($.protocolFacets[bytes1(0x03)], facet);
    }

    function test_different_flags_isolated() public {
        FeeConcentrationIndexRegistryStorage storage $ = fciRegistryStorage();
        $.protocolFacets[bytes1(0x01)] = address(0xAAAA);
        $.protocolFacets[bytes1(0x03)] = address(0xBBBB);
        assertEq($.protocolFacets[bytes1(0x01)], address(0xAAAA));
        assertEq($.protocolFacets[bytes1(0x03)], address(0xBBBB));
    }
}
```

- [ ] **Step 2: Run tests**

Run: `forge test --match-path "test/fee-concentration-index-v2/FeeConcentrationIndexRegistryStorage*" -v`
Expected: 3 tests pass.

- [ ] **Step 3: Commit**

```
test(006): registry storage unit tests — slot disjointness, read/write, flag isolation
```

---

## Chunk 2: FCIProtocolFacetStorageMod + FCI V2 Scaffold

### Task 6: FCIProtocolFacetStorageMod — facet storage primitives

**Files:**
- Create: `src/reactive-integration/template/modules/FCIProtocolFacetStorageMod.sol`

**Spec fidelity anchors (must match exactly):**

```solidity
// Slot derivation — parameterized by flag argument, NOT compile-time constant
function protocolFciStorage(bytes1 flag) pure returns (FeeConcentrationIndexStorage storage $) {
    bytes32 position = keccak256(abi.encode("thetaSwap.fci", flag));
    assembly ("memory-safe") { $.slot := position }
}

function protocolEpochFciStorage(bytes1 flag) pure returns (FeeConcentrationEpochStorage storage $) {
    bytes32 position = keccak256(abi.encode("thetaSwap.fci.epoch", flag));
    assembly ("memory-safe") { $.slot := position }
}

// Transient storage — per-field tstore/tload with base + offset
function transientBase(bytes1 flag) pure returns (bytes32) {
    return keccak256(abi.encode("thetaSwap.fci.transient", flag));
}
// Offsets: +0 tickBefore, +1 feeGrowthLast, +2 posLiquidity, +3 rangeFeeGrowth
```

Contains:
- `protocolFciStorage(bytes1 flag)` — FCI state at protocol-scoped slot
- `protocolEpochFciStorage(bytes1 flag)` — epoch state at protocol-scoped epoch slot
- `transientBase(bytes1 flag)` — base for transient slot derivation
- `tstoreTick(bytes1 flag, int24 tick)` / `tloadTick(bytes1 flag)` — tick cache
- `tstoreRemovalData(bytes1 flag, uint256 feeLast, uint128 posLiq, uint256 rangeFeeGrowth)` / `tloadRemovalData(bytes1 flag)` — removal data cache

Note: Does NOT include `FCIProtocolFacetStorage` struct — that belongs in the protocol facet implementation, not the template. The template provides only slot derivation and transient helpers.

Exact function bodies to be presented for user review before writing.

- [ ] **Step 1: Present each function for user review**
- [ ] **Step 2: Write to file after approval**
- [ ] **Step 3: Verify build**

Run: `forge build`
Expected: Compiles.

- [ ] **Step 4: Commit**

```
feat(006): add FCIProtocolFacetStorageMod — per-protocol storage + transient helpers
```

---

### Task 7: FCIProtocolFacetStorageMod unit test

**Files:**
- Create: `test/reactive-integration/template/FCIProtocolFacetStorageMod.t.sol`

Test that:
1. `protocolFciStorage(0x03)` and `protocolFciStorage(0x01)` return different slot pointers (write to one, read from other is empty).
2. `protocolFciStorage(0x03)` slot does not collide with V4 `fciStorage()` slot.
3. `tstoreTick(flag, tick)` / `tloadTick(flag)` roundtrip for same flag.
4. `tstoreRemovalData` / `tloadRemovalData` roundtrip — all 3 fields.
5. Transient slots for different protocol flags are isolated (write tick for 0x01, read tick for 0x03 returns 0).

Exact code to be presented for user review before writing.

- [ ] **Step 1: Present test code for user review**
- [ ] **Step 2: Write to file after approval**
- [ ] **Step 3: Run tests**

Run: `forge test --match-path "test/reactive-integration/template/FCIProtocolFacetStorageMod*" -v`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```
test(006): FCIProtocolFacetStorageMod unit tests — slot isolation, transient roundtrip
```

---

### Task 8: FeeConcentrationIndexV2StorageMod — V2 storage helpers

**Files:**
- Create: `src/fee-concentration-index-v2/modules/FeeConcentrationIndexV2StorageMod.sol`

**Spec fidelity anchors:**

```solidity
// Re-export V1 storage (FeeConcentrationIndexStorage, fciStorage, _poolManager, etc.)
// Plus add protocol-scoped slot routing:

function _protocolFciStorage(bytes1 flags) internal pure returns (FeeConcentrationIndexStorage storage $) {
    bytes32 position = flags == bytes1(0x03)
        ? keccak256("ReactiveHookAdapter.fci.storage")  // V3: legacy production slot
        : keccak256(abi.encode("thetaSwap.fci", flags));
    assembly ("memory-safe") { $.slot := position }
}

function _protocolEpochFciStorage(bytes1 flags) internal pure returns (FeeConcentrationEpochStorage storage $) {
    bytes32 position = keccak256(abi.encode("thetaSwap.fci.epoch", flags));
    assembly ("memory-safe") { $.slot := position }
}
```

Exact code to be presented for user review before writing.

- [ ] **Step 1: Present code for user review**
- [ ] **Step 2: Write to file after approval**
- [ ] **Step 3: Verify build**

Run: `forge build`
Expected: Compiles.

- [ ] **Step 4: Commit**

```
feat(006): add FeeConcentrationIndexV2StorageMod — protocol slot routing
```

---

### Task 9: FeeConcentrationIndexV2.sol — V2 with dispatch preamble

**Files:**
- Create: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol`

**Key design decisions for this task:**

1. **V4 fast path imports directly from V1 storage** — uses `fciStorage()`, `_poolManager()`, `registerPosition($, ...)` etc. from `FeeConcentrationIndexStorageMod.sol` directly. Does NOT import from `ProtocolAdapterMod` (unnecessary indirection since V4 fast path always has empty hookData).

2. **Dispatch preamble on ALL 5 hooks** including `beforeRemoveLiquidity` — even though V4 path ignores hookData for position key derivation. The facet path receives full `msg.data` and handles its own derivation.

3. **`addEpochTerm` in V4 path unchanged** — writes to default epoch slot `keccak256("thetaSwap.fci.epoch")`, same as V1.

4. **All view functions get `bytes1 flags` overloads**: `getDeltaPlus`, `getDeltaPlusEpoch`, `getIndex`, `getAtNull`, `getThetaSum`. Existing `(PoolKey, bool reactive)` signatures preserved.

5. **Import note:** V2 imports `FeeConcentrationIndexStorage` from V1's `@fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol`. Same struct, no duplicate definition.

Exact code to be presented for user review before writing — each hook function reviewed individually.

- [ ] **Step 1: Present dispatch preamble pattern for user review**
- [ ] **Step 2: Present each hook function (V4 inlined + dispatch) for user review**
- [ ] **Step 3: Present registration functions for user review**
- [ ] **Step 4: Present view function overloads for user review**
- [ ] **Step 5: Write to file after approval**
- [ ] **Step 6: Verify build**

Run: `forge build`
Expected: Compiles. Note: V2 imports from both `@fee-concentration-index/` (V1 storage) and `@fee-concentration-index-v2/` (registry, slot routing). Solidity handles this via idempotent imports.

- [ ] **Step 7: Commit**

```
feat(006): add FeeConcentrationIndexV2 — protocol dispatch preamble + registration
```

---

## Chunk 3: Tests

### Task 10: V2 dispatch unit test — delegatecall to mock facet

**Files:**
- Create: `test/fee-concentration-index-v2/FeeConcentrationIndexV2Dispatch.t.sol`

Deploy V2 FCI. Register a mock facet at flag `0x05`. Test:

1. Call `afterAddLiquidity` with `hookData = hex"05"` → mock facet's handler is invoked via delegatecall (mock writes to a known storage slot, test reads it from V2's context to confirm delegatecall, not call).
2. Call with unregistered flag → reverts with `"FCI: unknown protocol"`.
3. Call with empty hookData → V4 fast path (no delegatecall, no revert).

Exact code to be presented for user review before writing.

- [ ] **Step 1: Present test code for user review**
- [ ] **Step 2: Write to file after approval**
- [ ] **Step 3: Run tests**

Run: `forge test --match-path "test/fee-concentration-index-v2/FeeConcentrationIndexV2Dispatch*" -v`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```
test(006): V2 dispatch unit tests — mock facet delegatecall, unknown flag revert
```

---

### Task 11: V4 Differential Test — V2 == V1

**Files:**
- Create: `test/fee-concentration-index-v2/differential/V4Differential.t.sol`

**Test strategy:** Fork test using the existing `FeeConcentrationIndexForkHarness` pattern (see `test/fee-concentration-index/differential/FeeConcentrationIndexForkHarness.sol`). Both V1 and V2 are deployed with the same PoolManager against a real forked Uniswap V4 pool. Run identical hook sequences with empty hookData (V4 path) and assert identical FCI state after each operation.

State assertions after each operation:
- `deltaPlus` (via `getDeltaPlus(key, false)`)
- `thetaSum` (via `getThetaSum(key, false)`)
- `removedPosCount` (via `getIndex(key, false)`)
- `indexA` (via `getIndex(key, false)`)

The fork test approach is required because hook functions read real PoolManager state (positions, tick, feeGrowthInside). A local deploy would require initializing a full pool with liquidity — the fork test pattern already handles this.

Exact code to be presented for user review before writing.

- [ ] **Step 1: Present test code for user review**
- [ ] **Step 2: Write to file after approval**
- [ ] **Step 3: Run tests**

Run: `forge test --match-path "test/fee-concentration-index-v2/differential/*" -v`
Expected: All tests pass — V2 V4 path produces identical state to V1.

- [ ] **Step 4: Commit**

```
test(006): V4 differential test — V2 V4 path == V1 state equivalence
```

---

### Task 12: Final verification + push

- [ ] **Step 1: Run full test suite**

Run: `forge test`
Expected: All tests pass (existing 139 + new tests), zero regressions.

- [ ] **Step 2: Push**

Run: `git push origin 006-fci-reactive-integration`
