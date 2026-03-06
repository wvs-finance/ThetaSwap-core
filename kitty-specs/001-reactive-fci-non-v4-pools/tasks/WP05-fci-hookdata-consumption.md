---
work_package_id: WP05
title: FCI hookData Consumption
lane: "doing"
dependencies: [WP02]
base_branch: 001-reactive-fci-non-v4-pools-WP02
base_commit: a6dd8e55f924aaa54dd9a9fe09936656fd73f319
created_at: '2026-03-06T18:11:35.890040+00:00'
subtasks: [T020, T021, T022]
shell_pid: "205020"
history:
- date: '2026-03-06'
  action: created
  by: spec-kitty.tasks
requirement_refs: [FR-001, FR-002, FR-003]
---

# WP05: FCI hookData Consumption

**Objective**: Modify FeeConcentrationIndex to read V3-specific data from hookData when present, enabling the reactive adapter's translated calldata to drive the same FCI logic used by V4 pools.

## Context

The ReactiveHookAdapter (WP02) translates V3 events into V4 hook calldata. The adapter encodes V3-specific data in the `hookData` bytes parameter:

- `afterSwap`: `hookData = abi.encode(int24 tick)` — the V3 swap's resulting tick
- `afterRemoveLiquidity`: `hookData = abi.encode(uint256 feeAmount0, uint256 feeAmount1)` — accumulated Collect fees

Currently FeeConcentrationIndex reads tick and fee data from PoolManager via extsload/StateLibrary. For the reactive path, this data comes from hookData instead. FCI must detect which path to use and handle both.

**Reference files**:
- `src/fee-concentration-index/FeeConcentrationIndex.sol` — current implementation
- `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol` — hookData encoding

**Target**: Modify `src/fee-concentration-index/FeeConcentrationIndex.sol`

## Subtasks

### T020: afterSwap — read tick from hookData when present

**Purpose**: When hookData is non-empty, decode tick from it instead of reading from PoolManager.

**Steps**:
1. In `afterSwap`, check `hookData.length > 0`
2. If non-empty: `int24 tick = abi.decode(hookData, (int24))` — use as both tickBefore and tickAfter (single event, range = tick..tick+1)
3. If empty: existing V4 path — read tickAfter from PoolManager, tickBefore from transient storage
4. Rest of the function (incrementOverlappingRanges) unchanged

**Impact on beforeSwap**: When hookData path is used, `beforeSwap` transient tick cache is not needed. No change to beforeSwap required — it simply won't be called for reactive paths.

**Validation**:
- [ ] V4 path unchanged (hookData empty)
- [ ] V3 path uses decoded tick
- [ ] `forge build` succeeds

### T021: afterRemoveLiquidity — read fees from hookData when present

**Purpose**: When hookData is non-empty, decode accumulated Collect fees from it instead of reading from transient storage.

**Steps**:
1. In `afterRemoveLiquidity`, check `hookData.length > 0`
2. If non-empty: `(uint256 feeAmount0, uint256 feeAmount1) = abi.decode(hookData, (uint256, uint256))`
   - Compute fee share using liquidity-weighted ratio: `xk = fromFeeGrowth(posLiquidity, totalRangeLiquidity)` (same fee growth period for all positions in range)
   - Skip feeGrowthDelta computation (no PoolManager reads needed)
3. If empty: existing V4 path — read from transient storage, compute fromFeeGrowthDelta
4. HHI accumulation, decrementPos, cleanup unchanged

**Impact on beforeRemoveLiquidity**: When hookData path is used, `beforeRemoveLiquidity` transient cache is not needed. No change required — it simply won't be called for reactive paths.

**Validation**:
- [ ] V4 path unchanged (hookData empty)
- [ ] V3 path uses decoded fees with liquidity-weighted share
- [ ] `forge build` succeeds

### T022: afterAddLiquidity — skip PoolManager reads for reactive path

**Purpose**: When called via the reactive path, posLiquidity comes from params and feeGrowthBaseline is 0.

**Steps**:
1. In `afterAddLiquidity`, check if `hookData.length > 0` or if poolManager is unset
2. If reactive path: use `uint128(uint256(params.liquidityDelta))` for posLiquidity, set baseline to 0
3. If V4 path: existing logic — read posLiquidity from PoolManager, read feeGrowthInside for baseline
4. Registration and incrementPos unchanged

**Validation**:
- [ ] V4 path unchanged
- [ ] V3 path uses params.liquidityDelta for liquidity, baseline = 0
- [ ] `forge build` succeeds

## Definition of Done

- [ ] FCI handles both V4 (empty hookData) and V3 (non-empty hookData) paths
- [ ] No behavioral change for existing V4 pools
- [ ] `forge build` succeeds
- [ ] Existing FCI fuzz tests still pass

## Risks

- **hookData collision**: Other V4 hooks might pass non-empty hookData for legitimate V4 reasons. Consider using a magic prefix byte or checking `key.hooks == reactiveAdapter` to distinguish paths.
- **Regression on V4 path**: Must verify existing tests pass unchanged.
