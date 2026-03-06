---
work_package_id: "WP01"
title: "Adapter Diamond Storage"
lane: "planned"
dependencies: []
subtasks: ["T001", "T002", "T003"]
requirement_refs: ["FR-007"]
history:
  - date: "2026-03-06"
    action: "created"
    by: "spec-kitty.tasks"
---

# WP01: Adapter Diamond Storage

**Objective**: Create the parallel FCI storage module for the ReactiveHookAdapter. This is the foundation — all other WPs depend on it.

**Implementation command**: `spec-kitty implement WP01`

## Context

The ReactiveHookAdapter owns a parallel FCI storage instance isolated from the V4 FCI contract. It uses the same storage pattern (diamond keccak256 slot hashing) but a different slot. Additionally, the adapter needs to accumulate Collect event fees per position, requiring a second storage slot.

**Reference files**:
- `src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol` — existing pattern to follow
- `src/fee-concentration-index/types/AccumulatedHHIMod.sol` — AccumulatedHHI type
- `src/fee-concentration-index/types/TickRangeRegistryMod.sol` — TickRangeRegistry type

**Target location**: `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapterStorageMod.sol`

## Subtasks

### T001: Create ReactiveHookAdapterStorageMod.sol — Diamond Storage

**Purpose**: Define the storage struct and slot for the adapter's parallel FCI state.

**Steps**:
1. Create `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapterStorageMod.sol`
2. Define `ReactiveHookAdapterStorage` struct with:
   - `mapping(PoolId => AccumulatedHHI) accumulatedHHI` — running HHI accumulator per V3 pool
   - `mapping(PoolId => TickRangeRegistry) registries` — per-pool tick range registry
   - `mapping(PoolId => mapping(bytes32 => uint256)) feeGrowthBaseline0` — per-position fee baseline (set at Mint, read at Burn)
3. Define `REACTIVE_FCI_STORAGE_SLOT = keccak256("ReactiveHookAdapter.fci.storage")`
4. Write `reactiveFciStorage()` accessor function with assembly slot assignment
5. Import types from existing FCI modules — do NOT duplicate type definitions

**SCOP constraints**:
- Free function, not inside a contract
- No `library` keyword
- File-level function with assembly for slot access

**Validation**:
- [ ] `REACTIVE_FCI_STORAGE_SLOT != FCI_STORAGE_SLOT` (keccak256 of different strings)
- [ ] Compiles with `forge build`

### T002: Add CollectedFees Struct and Storage

**Purpose**: Define storage for accumulated V3 Collect event fees per position.

**Steps**:
1. Define `CollectedFees` struct: `{ uint256 amount0; uint256 amount1; }`
2. Add to `ReactiveHookAdapterStorage`:
   - `mapping(PoolId => mapping(bytes32 => CollectedFees)) collectedFees` — accumulated Collect amounts per position
3. This mapping is keyed by PoolId + positionKey (same key derivation as registry)
4. On Collect: amounts are added to existing values
5. On Burn: amounts are read, used for fee share computation, then deleted

**Validation**:
- [ ] CollectedFees struct is minimal (only amount0, amount1)
- [ ] Storage layout is clean — no redundant fields

### T003: Create Storage Accessor Free Functions

**Purpose**: Provide typed access to the adapter's storage, following the existing FCI pattern.

**Steps**:
1. Write `getAccumulatedHHI(PoolId) view returns (AccumulatedHHI)` — reads from own slot
2. Write `setAccumulatedHHI(PoolId, AccumulatedHHI)` — writes to own slot
3. Write `getCollectedFees(PoolId, bytes32 posKey) view returns (CollectedFees memory)`
4. Write `addCollectedFees(PoolId, bytes32 posKey, uint256 amount0, uint256 amount1)` — accumulates
5. Write `deleteCollectedFees(PoolId, bytes32 posKey)` — cleanup after Burn
6. Write `setFeeGrowthBaseline0(PoolId, bytes32 posKey, uint256)` and `getFeeGrowthBaseline0(PoolId, bytes32 posKey) view returns (uint256)` and `deleteFeeGrowthBaseline0(PoolId, bytes32 posKey)`

**Pattern reference**: See `FeeConcentrationIndexStorageMod.sol` lines 43-61 for the exact pattern.

**Validation**:
- [ ] All accessors are free functions (not inside a contract)
- [ ] All accessors use `reactiveFciStorage()` to get the storage pointer
- [ ] `addCollectedFees` uses `+=` (accumulation, not overwrite)
- [ ] Compiles with `forge build`

## Definition of Done

- [ ] `ReactiveHookAdapterStorageMod.sol` exists at correct path
- [ ] Storage slot is distinct from FCI_STORAGE_SLOT
- [ ] All accessor functions are file-level free functions
- [ ] No `library`, `modifier`, or inheritance keywords
- [ ] `forge build` succeeds with no errors on new files

## Risks

- **Slot collision**: Mitigated by using a completely different keccak256 preimage ("ReactiveHookAdapter.fci.storage" vs "FeeConcentrationIndex.storage")
- **Import conflicts**: Both storage modules import AccumulatedHHI and TickRangeRegistry — ensure no symbol conflicts (Solidity handles this via file-level scoping)
