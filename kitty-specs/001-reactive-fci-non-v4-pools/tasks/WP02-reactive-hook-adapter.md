---
work_package_id: "WP02"
title: "ReactiveHookAdapter Contract"
lane: "planned"
dependencies: ["WP01"]
subtasks: ["T004", "T005", "T006", "T007", "T008", "T009", "T010"]
requirement_refs: ["FR-001", "FR-002", "FR-003", "FR-004", "FR-005", "FR-006", "FR-008", "FR-009", "FR-010", "FR-011", "FR-012", "FR-016"]
history:
  - date: "2026-03-06"
    action: "created"
    by: "spec-kitty.tasks"
---

# WP02: ReactiveHookAdapter Contract

**Objective**: Implement the adapter contract with 4 typed callbacks, whitelist auth, and index query. This is the core of the reactive FCI integration.

**Implementation command**: `spec-kitty implement WP02 --base WP01`

## Context

The ReactiveHookAdapter sits at `src/reactive-integration/adapters/uniswapV3/` and:
- Receives V3 events via 4 separate typed callbacks (onV3Swap, onV3Mint, onV3Burn, onV3Collect)
- Authenticates callers via whitelist mapping
- Owns a parallel FCI storage instance (from WP01)
- Reuses existing FCI Mod files for all computation
- Constructs synthetic PoolKeys via `fromV3Pool()` from `PoolKeyExtMod.sol`

**Reference files**:
- `src/fee-concentration-index/FeeConcentrationIndex.sol` — the V4 FCI contract (lines 59-191 show the processing logic to mirror)
- `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapterStorageMod.sol` — storage from WP01
- `src/reactive-integration/libraries/PoolKeyExtMod.sol` — PoolKey mapping
- `src/reactive-integration/types/ReactiveCallbackDataMod.sol` — V3SwapData, V3MintData, V3BurnData, V3CollectData
- `src/reactive-integration/types/SyntheticFeeGrowthMod.sol` — fromBurnAmount, toFeeShareRatio

**Target location**: `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol`

## Subtasks

### T004: Create ReactiveHookAdapter Contract Shell

**Purpose**: Set up the contract with constructor, immutable state, and auth mapping.

**Steps**:
1. Create `ReactiveHookAdapter.sol`
2. Define state:
   - `address public immutable owner`
   - `IUniswapV3Factory public immutable factory`
   - `mapping(address => bool) public authorizedCallers`
3. Constructor takes `(address _owner, IUniswapV3Factory _factory)`
4. Define custom errors:
   - `error Unauthorized()`
   - `error NotOwner()`

**SCOP constraints**:
- Contract MAY NOT use `is` (no inheritance)
- No `modifier` keyword — use inline `if`/`revert` checks
- All `external` functions (no `public`)

**Validation**:
- [ ] Contract compiles
- [ ] No inheritance, no modifiers

### T005: Implement setAuthorized

**Purpose**: Owner-only function to add/remove authorized callers.

**Steps**:
1. `function setAuthorized(address caller, bool authorized) external`
2. Inline auth: `if (msg.sender != owner) revert NotOwner();`
3. `authorizedCallers[caller] = authorized;`
4. Emit an event: `event AuthorizedCallerUpdated(address indexed caller, bool authorized);`

**Validation**:
- [ ] Only owner can call
- [ ] Non-owner reverts with NotOwner()
- [ ] Event emitted on state change

### T006: Implement onV3Swap(V3SwapData)

**Purpose**: Process V3 Swap events — increment swap counts for overlapping tick ranges.

**Steps**:
1. `function onV3Swap(V3SwapData calldata data) external`
2. Inline auth: `if (!authorizedCallers[msg.sender]) revert Unauthorized();`
3. Construct synthetic PoolKey: `PoolKey memory key = fromV3Pool(data.pool, address(this));`
4. Compute PoolId: `PoolId poolId = PoolIdLibrary.toId(key);`
5. Call `incrementOverlappingRanges(poolId, data.tick, data.tick)` on own storage

**Key difference from V4 FCI**: V4 uses beforeSwap/afterSwap pair with transient storage for tick caching. The reactive path receives the final tick directly from the Swap event — no before/after pair needed. The tick range is `(tick, tick)` for a single swap event. If block-based deduplication is active in the subscription layer, the tick range spans `(minTick, maxTick)` of all swaps in the block.

**Important**: `incrementOverlappingRanges` is a free function in `FeeConcentrationIndexStorageMod.sol` that operates on `fciStorage()`. The adapter must call an equivalent function on its own storage. Either:
- Import and adapt the function to accept a storage pointer, OR
- Write an adapter-specific version that calls `reactiveFciStorage()` instead

**Validation**:
- [ ] Unauthorized sender reverts
- [ ] Swap count increments for overlapping ranges
- [ ] Non-overlapping ranges untouched

### T007: Implement onV3Mint(V3MintData)

**Purpose**: Register a new V3 position in the adapter's FCI registry.

**Steps**:
1. `function onV3Mint(V3MintData calldata data) external`
2. Inline auth check
3. Construct PoolKey and PoolId
4. Derive positionKey: `bytes32 posKey = keccak256(abi.encodePacked(data.owner, data.tickLower, data.tickUpper));`
5. Create TickRange: `TickRange rk = fromTicks(data.tickLower, data.tickUpper);`
6. Call `registry.register(rk, posKey, data.tickLower, data.tickUpper, data.liquidity)` on own storage
7. Set feeGrowthBaseline to 0 (Collect events will supply fee data, not feeGrowthInside reads)

**Key difference from V4 FCI**: V4 reads feeGrowthInside from PoolManager via extsload. The reactive path has no access to V3 pool state — fees come from Collect events instead. Baseline is 0.

**Validation**:
- [ ] Position registered in registry with correct tick range and liquidity
- [ ] feeGrowthBaseline set to 0
- [ ] Duplicate Mint for same position updates rather than creating duplicate

### T008: Implement onV3Collect(V3CollectData)

**Purpose**: Accumulate fee amounts from V3 Collect events per position.

**Steps**:
1. `function onV3Collect(V3CollectData calldata data) external`
2. Inline auth check
3. Construct PoolKey and PoolId
4. Derive positionKey (same derivation as T007)
5. Call `addCollectedFees(poolId, posKey, uint256(data.feeAmount0), uint256(data.feeAmount1))` — accumulates into existing values

**Edge cases**:
- Collect for an unregistered position (never Minted or already Burned): fees accumulate in storage. On Burn, if position not in registry → no-op, fees cleaned up.
- Multiple Collects before Burn: all amounts summed correctly via `+=`

**Validation**:
- [ ] Fees accumulate (not overwrite) across multiple Collect calls
- [ ] Works for unregistered positions without revert

### T009: Implement onV3Burn(V3BurnData)

**Purpose**: Compute fee share ratio from accumulated Collect fees, accumulate HHI, deregister position. This is the most complex callback.

**Steps**:
1. `function onV3Burn(V3BurnData calldata data) external`
2. Inline auth check
3. Construct PoolKey and PoolId
4. Derive positionKey
5. Read accumulated fees: `CollectedFees memory fees = getCollectedFees(poolId, posKey);`
6. Attempt deregister: `(, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) = registry.deregister(posKey, data.liquidity);`
   - If position not in registry → return early (RX-009: no-op for unregistered)
7. Compute synthetic fee growth: `SyntheticFeeGrowth posDelta = fromBurnAmount(fees.amount0, data.liquidity);`
8. For fee share ratio, use liquidity-weighted share since all positions in a range share the same fee growth period:
   ```
   FeeShareRatio xk;
   if (totalRangeLiq == 0) {
       xk = FeeShareRatio.wrap(0);
   } else {
       // x_k = posLiquidity / totalRangeLiquidity (simplified when same fee period)
       xk = fromFeeGrowth(uint256(data.liquidity), uint256(totalRangeLiq));
   }
   ```
9. Accumulate HHI if swaps occurred:
   ```
   if (!swapLifetime.isZero()) {
       uint256 xSquaredQ128 = xk.square();
       setAccumulatedHHI(poolId, getAccumulatedHHI(poolId).addTerm(blockLifetime, xSquaredQ128));
   }
   ```
10. Cleanup: `deleteCollectedFees(poolId, posKey);` and `deleteFeeGrowthBaseline0(poolId, posKey);`

**Key difference from V4 FCI**: V4 uses transient storage for pre-removal fee caching (beforeRemoveLiquidity → afterRemoveLiquidity). The reactive path has no before/after pair — all data comes from the event payload and accumulated Collect fees.

**Edge cases**:
- Zero liquidity position: `fromBurnAmount(amount0, 0)` returns 0 (SyntheticFeeGrowthMod handles this)
- Position never received swaps: `swapLifetime.isZero()` → skip HHI accumulation (INV-010)
- Unregistered position: deregister returns early, no state change

**Validation**:
- [ ] Registered position with swaps → HHI accumulated
- [ ] Registered position without swaps → HHI unchanged (INV-010)
- [ ] Unregistered position → no-op, no revert (RX-009)
- [ ] CollectedFees cleaned up after Burn
- [ ] feeGrowthBaseline cleaned up after Burn

### T010: Implement getIndex(PoolKey)

**Purpose**: Query the FCI index for a V3 pool from the adapter's own storage.

**Steps**:
1. `function getIndex(PoolKey calldata key) external view returns (uint128 indexA, uint128 indexB)`
2. Compute PoolId from key
3. Read own AccumulatedHHI: `AccumulatedHHI hhi = getAccumulatedHHI(poolId);`
4. Return `(hhi.toIndexA(), hhi.toIndexB())`

**Validation**:
- [ ] Returns (0, 0) for pools with no data
- [ ] Returns correct index after Burn processing
- [ ] View function — no state changes

## Definition of Done

- [ ] All 4 callbacks + getIndex + setAuthorized compile
- [ ] All functions are `external` (SCOP: no `public`)
- [ ] No `library`, `modifier`, or `is` keywords
- [ ] Auth reverts on unauthorized sender for all callbacks
- [ ] onV3Burn handles unregistered positions as no-op
- [ ] `forge build` succeeds

## Risks

- **incrementOverlappingRanges coupling**: The existing free function reads from `fciStorage()`. The adapter needs its own version reading from `reactiveFciStorage()`. May need to refactor the function to accept a storage pointer, or duplicate with different storage reference.
- **Registry deregister for unregistered position**: Must verify that `registry.deregister()` handles non-existent positions gracefully (returns early or reverts). If it reverts, wrap in try/catch or add existence check before calling.
- **Position key derivation consistency**: Must use identical key derivation in onV3Mint, onV3Collect, and onV3Burn. Any mismatch → fees lost or wrong position deregistered.
