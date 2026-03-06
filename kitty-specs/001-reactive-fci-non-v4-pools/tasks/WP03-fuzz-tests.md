---
work_package_id: WP03
title: Fuzz Tests
lane: planned
dependencies: [WP02]
subtasks: [T011, T012, T013, T014, T015]
history:
- date: '2026-03-06'
  action: created
  by: spec-kitty.tasks
requirement_refs:
- FR-004
- FR-005
- FR-006
- FR-008
- FR-009
---

# WP03: Fuzz Tests

**Objective**: Write fuzz tests covering system-level invariants that cannot be proven with Kontrol (they require deployed contract state and multi-step interactions).

**Implementation command**: `spec-kitty implement WP03 --base WP02`

## Context

Kontrol proofs (SyntheticFeeGrowth.k.sol, PoolKeyExt.k.sol) cover type-level invariants RX-001..004 and RX-008. The remaining system-level invariants (RX-005, RX-006, RX-007, RX-009) and Collect fee accumulation require fuzz tests with a deployed adapter.

**Reference files**:
- `test/fee-concentration-index/fuzz/FeeConcentrationIndexFull.fuzz.t.sol` — existing fuzz test pattern
- `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol` — adapter from WP02
- `test/reactive-integration/kontrol/PoolKeyExt.k.sol` — MockV3Pool pattern to reuse

**Target location**: `test/reactive-integration/fuzz/ReactiveHookAdapter.fuzz.t.sol`

All tests are independent and can be written in parallel [P].

## Subtasks

### T011: testFuzz_adapter_rejectsUnauthorized (RX-005)

**Purpose**: Verify that all 4 callbacks revert when called by an unauthorized sender.

**Steps**:
1. Deploy adapter with `owner = address(this)`, authorize a known address
2. Fuzz with random `sender` address
3. `vm.assume(sender != authorizedAddress)`
4. `vm.prank(sender)`
5. Call each callback (onV3Swap, onV3Mint, onV3Burn, onV3Collect) with valid data
6. `vm.expectRevert(Unauthorized.selector)` before each call

**Validation**:
- [ ] All 4 callbacks revert with Unauthorized()
- [ ] Authorized address succeeds (sanity check)

### T012: testFuzz_swapTranslation_equivalence (RX-006)

**Purpose**: Verify that processing a V3 Swap event produces the same swap count increments as the equivalent tick range overlap logic.

**Steps**:
1. Deploy adapter, authorize test contract
2. Create a mock V3 pool with known (token0, token1, fee, tickSpacing)
3. Register a position via onV3Mint with (tickLower, tickUpper, liquidity)
4. Fuzz `swapTick` within some range
5. Call `onV3Swap(V3SwapData({ pool: mockPool, tick: swapTick }))`
6. Read swap count for the position's tick range from adapter storage
7. Assert: if `swapTick >= tickLower && swapTick < tickUpper`, swap count incremented by 1. Otherwise unchanged.

**Validation**:
- [ ] Overlapping swap → count incremented
- [ ] Non-overlapping swap → count unchanged
- [ ] Multiple swaps accumulate correctly

### T013: testFuzz_mintTranslation_equivalence (RX-007)

**Purpose**: Verify that onV3Mint registers a position with correct tick range and liquidity.

**Steps**:
1. Deploy adapter, authorize test contract
2. Fuzz `(tickLower, tickUpper, liquidity)` with `vm.assume(tickLower < tickUpper)`
3. Call `onV3Mint` with fuzzed params
4. Verify position exists in registry (check via registry accessor)
5. Verify tick range matches (tickLower, tickUpper)

**Validation**:
- [ ] Position registered after Mint
- [ ] Correct tick range stored
- [ ] Duplicate Mint doesn't create two entries

### T014: testFuzz_unregisteredBurn_noop (RX-009)

**Purpose**: Verify that Burn for an unregistered position is a silent no-op.

**Steps**:
1. Deploy adapter, authorize test contract
2. Register position A via onV3Mint
3. Accumulate some HHI by processing swaps + burning position A
4. Record AccumulatedHHI state
5. Call onV3Burn for position B (never registered) with fuzzed params
6. Assert: AccumulatedHHI unchanged, no revert

**Validation**:
- [ ] No revert
- [ ] AccumulatedHHI unchanged
- [ ] Registry unchanged

### T015: testFuzz_collectAccumulation

**Purpose**: Verify that multiple Collect events accumulate fees correctly and Burn consumes them.

**Steps**:
1. Deploy adapter, authorize test contract
2. Register position via onV3Mint
3. Fuzz `(feeAmount0_1, feeAmount0_2)` — two Collect events
4. Call `onV3Collect` twice with feeAmount0_1 and feeAmount0_2
5. Read CollectedFees from storage: assert `amount0 == feeAmount0_1 + feeAmount0_2`
6. Call onV3Burn — verify CollectedFees cleaned up (returns zero after)

**Edge cases to test**:
- `vm.assume(feeAmount0_1 + feeAmount0_2 >= feeAmount0_1)` — no overflow
- Zero fee amounts → still accumulates (no special case)
- Collect after Burn → starts fresh accumulation for new position lifecycle

**Validation**:
- [ ] Fees sum correctly across multiple Collects
- [ ] Burn cleans up accumulated fees
- [ ] No overflow on fee accumulation

## Definition of Done

- [ ] All 5 fuzz tests compile
- [ ] `forge test --match-contract ReactiveHookAdapterFuzz` passes
- [ ] Each test covers the stated invariant
- [ ] No false positives (tests actually exercise the invariant, not trivially pass)

## Risks

- **MockV3Pool interface**: Fuzz tests need mock V3 pools returning controlled values. Reuse `MockV3Pool` from `test/reactive-integration/kontrol/PoolKeyExt.k.sol`.
- **Registry accessor visibility**: Some registry internals may not be externally readable. May need a test harness or expose via getIndex.
