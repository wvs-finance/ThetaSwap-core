# Feature Specification: Fee Concentration Index

**Feature Branch**: `001-fee-concentration-index`
**Created**: 2026-03-03
**Status**: Draft
**Input**: Build the FeeConcentrationIndex, an independent on-chain component that tracks the risk of adverse competition in liquidity provision for Uniswap V4 pools via a hook.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Track Position Lifetimes (Priority: P1)

When a liquidity provider adds a position to a Uniswap V4 pool monitored by the hook, the system begins tracking that position's lifetime measured in swap counts **specific to that position**. On each afterSwap, the system checks whether the swap touched ticks within the position's active tick range (i.e., the swap used that position's liquidity). Only swaps that use the position's liquidity increment that position's swap count. When the position is removed, the system records the position's lifetime as its accumulated swap count.

**Why this priority**: Lifetime tracking is the foundational primitive. Without it, the sophistication weight theta cannot be computed, and no index update is possible. This must work correctly before any other component.

**Independent Test**: Can be fully tested by deploying a hook, adding a position covering the active tick, executing N swaps that cross through the position's tick range, removing the position, and verifying that the recorded lifetime equals N.

**Acceptance Scenarios**:

1. **Given** a pool with the hook attached and a position covering the active tick, **When** the position is added and 5 swaps occur that use its liquidity, then it is removed, **Then** the position's recorded lifetime is 5.
2. **Given** a pool with two positions at different tick ranges where only one range is active, **When** 5 swaps occur at the active tick, **Then** only the position whose tick range contains the active tick has its swap count incremented; the other position's swap count remains 0.
3. **Given** a position added and removed within the same block (JIT), **When** exactly one swap occurs that uses the position's liquidity between add and remove, **Then** the position's lifetime is 1 and theta = 1.
4. **Given** a position covering ticks [100, 200] and a swap that moves the price from tick 150 to tick 250, **When** the swap crosses through the position's range, **Then** the position's swap count increments by 1 (the swap used its liquidity).

---

### User Story 2 - Compute Fee Share Ratio (Priority: P1)

When a position is removed, the system computes the fee share ratio x_k for that position. This ratio represents how much of the total fee revenue (per unit of liquidity in the tick range) was captured by this specific position. The ratio is computed as feeGrowthInside(position) / feeGrowth(tickRange) and is always in [0, 1].

**Why this priority**: The fee share ratio is the second foundational input to the index formula. Without accurate fee share computation, the HHI-weighted index is meaningless. Equal priority with Story 1 because both are needed for the index.

**Independent Test**: Can be tested by deploying a hook, adding a single position covering the active tick, executing swaps that generate fees, removing the position, and verifying x_k = 1 (sole position captures all fees).

**Acceptance Scenarios**:

1. **Given** a single position covering the active tick range, **When** it is removed after fees accrue, **Then** x_k = 1 (sole LP captures 100% of fees).
2. **Given** two equal-liquidity positions in the same tick range, **When** both are removed after equal time, **Then** each x_k is approximately 0.5.
3. **Given** a position outside the active tick range, **When** it is removed, **Then** x_k = 0 (no fee revenue captured).

---

### User Story 3 - Update Fee Concentration Index (Priority: P2)

When a position is removed, the system computes the sophistication weight theta_k = 1/lifetime for that position, then updates the running fee concentration index A_T using the HHI-weighted formula: A_T = (sum of theta_k * x_k^2)^{1/2}. The complement B_T = 1 - A_T is also stored as the fee dispersion index.

**Why this priority**: This is the core output of the component. It depends on Stories 1 and 2 being correct. Once the index updates correctly, the component delivers its primary value.

**Independent Test**: Can be tested by deploying a hook, adding a JIT position (lifetime=1), removing it with known fee share, and verifying the index value matches the expected formula output.

**Acceptance Scenarios**:

1. **Given** no positions have been removed yet, **When** the index is queried, **Then** A_T = 0 and B_T = 1.
2. **Given** a JIT position (lifetime=1) capturing 100% of fees (x_k=1), **When** it is removed, **Then** theta_k = 1 and A_T = 1 (maximum concentration), B_T = 0.
3. **Given** a passive position (lifetime=10) capturing 50% of fees (x_k=0.5), **When** it is removed, **Then** theta_k = 0.1, the contribution is 0.1 * 0.25 = 0.025, and the index updates accordingly.

---

### User Story 4 - EVM Number Representation (Priority: P2)

All intermediate and stored values use fixed-point arithmetic compatible with Uniswap V4's existing number formats. The fee share ratio x_k (a value in [0,1]) is stored in a format that allows squaring without overflow. The index value A_T is stored in a format that can interact with sqrtPriceX96 for downstream CFMM operations.

**Why this priority**: Correctness of arithmetic is a prerequisite for deployment. Without proper number representation, overflow or precision loss would make the index unreliable.

**Independent Test**: Can be tested by computing x_k^2 for boundary values (0, 1, and values near 2^128) and verifying no overflow occurs and precision loss is within acceptable bounds.

**Acceptance Scenarios**:

1. **Given** a fee share ratio x_k stored as Q128 fixed-point, **When** x_k = type(uint128).max (representing 1.0), **Then** x_k^2 fits in uint256 without overflow.
2. **Given** the index A_T stored as a fixed-point value, **When** converted to the odds-ratio price p = B_T/(1-B_T), **Then** the result is compatible with sqrtPriceX96 operations.
3. **Given** feeGrowthInsideX128 and feeGrowthX128 values from Uniswap V4, **When** divided to produce x_k, **Then** the quotient preserves at least 64 bits of precision.

---

### Edge Cases

- What happens when a position has lifetime = 0 (no swap ever used the position's liquidity)? The system MUST handle this by skipping the index update for this position (theta is undefined, and x_k = 0 since no fees accrued), or by reverting if x_k > 0 with lifetime = 0 (which would indicate a bug).
- What happens when feeGrowth(tickRange) = 0 (no swaps have occurred in the range)? The system MUST return x_k = 0 since no fees were generated.
- What happens when A_T would exceed 1 due to accumulated rounding? The system MUST cap A_T at 1 (and B_T at 0).
- What happens when many positions are removed in a single block? The index MUST update correctly for each removal in sequence within the same transaction/block.
- What happens when a position spans multiple tick ranges? The system MUST use feeGrowthInside for the position's specific tick range boundaries.

## Clarifications

### Session 2026-03-03

- Q: How does the afterSwap callback determine which positions are active in the current tick range? → A: Positions are grouped/clustered by their (tickLower, tickUpper) pair in a tick-range-indexed data structure. On afterSwap, the swap's price impact defines the tick range traversed; an O(1) lookup per unique tick range retrieves all positions there, and all are signaled to increment swapCount by 1. This avoids O(N) iteration over all positions.
- Q: How does the system determine which tick ranges overlap with a swap's traversed range? → A: Walk initialized ticks in the swap's traversed range using Uniswap V4's existing tick bitmap. Each initialized tick boundary maps to position groups that start or end there. This piggybacks on V4's O(1)-per-tick-spacing structure and avoids maintaining a separate range enumeration.
- Q: Should the accumulated sum in the index formula be stored as the squared sum (before sqrt) or the final sqrt value? → A: Store accumulatedSum = sum of (theta_k * x_k^2). The sqrt is computed lazily only when A_T or B_T is read. This allows additive accumulation on each afterRemoveLiquidity without needing to undo a square root.
- Q: Should the hook emit events for position lifecycle transitions? → A: No events. Minimize gas cost. Observability relies on state reads (view functions) rather than event logs.
- Q: How should afterRemoveLiquidity clean up the position from TickRangePositionSet? → A: Delete the position key from the set. If the set becomes empty, delete the tick range entry entirely. No ghost entries — ensures no gas wasted incrementing swap counts for empty groups on future afterSwap calls.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST track a per-position swap counter that increments on afterSwap ONLY when the swap uses that position's liquidity (i.e., the swap touches ticks within the position's active tick range).
- **FR-001a**: System MUST maintain a tick-range-indexed data structure that groups positions by their (tickLower, tickUpper) pair, enabling O(1) lookup per unique tick range on afterSwap.
- **FR-001b**: On afterSwap, given the swap's price impact (tick range traversed from tick_before to tick_after), the system MUST walk initialized ticks in the traversed range using Uniswap V4's tick bitmap. Each initialized tick boundary maps to position groups that start or end there. The system MUST increment the swap count of every position in overlapping ranges.
- **FR-002**: System MUST initialize each position's swap count to 0 on afterAddLiquidity and register the position in the tick-range-indexed data structure under its (tickLower, tickUpper) key.
- **FR-002b**: On afterRemoveLiquidity, the system MUST remove the position from the TickRangePositionSet. If the position was the last in its (tickLower, tickUpper) group, the system MUST delete the tick range entry entirely.
- **FR-003**: System MUST compute position lifetime as the position's accumulated swap count at the time of afterRemoveLiquidity.
- **FR-004**: System MUST compute the sophistication weight theta_k = 1/lifetime for each removed position, where lifetime is measured in swap counts.
- **FR-005**: System MUST compute the fee share ratio x_k = feeGrowthInside(position) / feeGrowth(tickRange) on afterRemoveLiquidity, using Uniswap V4's StateLibrary.
- **FR-006**: System MUST additively accumulate theta_k * x_k^2 into a persistent accumulatedSum on every afterRemoveLiquidity event. The index A_T = sqrt(accumulatedSum) is computed lazily on read, not stored directly.
- **FR-007**: System MUST expose a view function that computes and returns A_T = sqrt(accumulatedSum) and B_T = 1 - A_T on demand.
- **FR-008**: System MUST use fixed-point arithmetic that avoids overflow when squaring x_k values stored in Q128 format.
- **FR-009**: System MUST cap A_T at 1 and B_T at 0 to prevent rounding-induced out-of-range values.
- **FR-010**: System MUST handle the edge case where lifetime = 0 by either reverting or using a defined maximum theta value.
- **FR-011**: System MUST handle the edge case where feeGrowth(tickRange) = 0 by returning x_k = 0.
- **FR-012**: System MUST expose a view function to read the current index values (A_T, B_T) for a given pool.

### Key Entities

- **PositionLifetime**: Tracks a position's accumulated swap count (incremented only when swaps use the position's liquidity). Key attributes: positionKey (bytes32), swapCount (uint256), tickLower (int24), tickUpper (int24).
- **TickRangePositionSet**: A data structure indexed by (tickLower, tickUpper) pairs that stores the set of position keys sharing that exact tick range. Enables O(1) lookup per unique tick range on afterSwap. Populated on afterAddLiquidity, cleaned on afterRemoveLiquidity.
- **FeeShareRatio**: The ratio x_k computed at position removal. Derived from feeGrowthInside / feeGrowth. Stored as fixed-point Q128.
- **SophisticationWeight**: theta_k = 1/lifetime. Computed at removal, not stored persistently (used only during index update).
- **FeeConcentrationIndex**: The running accumulated sum of (theta_k * x_k^2) terms. A_T and B_T are computed lazily via sqrt on read. Key attributes: poolId (PoolId), accumulatedSum (uint256). A_T = sqrt(accumulatedSum), B_T = 1 - A_T are derived, not stored.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a single JIT position (lifetime=1, x_k=1), the index A_T MUST equal 1.0 exactly (within 1 wei of precision).
- **SC-002**: For N equal passive positions each capturing 1/N of fees with lifetime L, the index MUST match the formula (N * (1/L) * (1/N)^2)^{1/2} = (1/(L*N))^{1/2} within 0.1% relative error.
- **SC-003**: The component MUST NOT revert on any valid Uniswap V4 hook callback (afterAddLiquidity, afterSwap, afterRemoveLiquidity) under normal pool operation.
- **SC-004**: Gas cost for afterSwap (per-position swap counter updates for all active positions in the tick range) MUST be under 50,000 gas for up to 10 active positions.
- **SC-005**: Gas cost for afterRemoveLiquidity (full index update) MUST be under 100,000 gas.
- **SC-006**: All fixed-point arithmetic operations MUST be formally verified to be overflow-free via Kontrol proofs.
