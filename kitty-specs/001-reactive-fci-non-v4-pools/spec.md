# Feature Specification: Reactive FCI for Non-V4 Pools

**Feature Branch**: `003-reactive-integration`
**Created**: 2026-03-06
**Status**: Draft (updated with brainstorm decisions 2026-03-06)
**Input**: User description: "Track FeeConcentrationIndex on non-V4 pools via reactive smart contracts with PoolKeyExtLib mapping and hook wrapper pattern."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Track Fee Concentration on V3 Pools (Priority: P1)

A protocol operator wants to measure fee concentration risk on Uniswap V3 pools using the same FeeConcentrationIndex metric already available for V4 pools. The system monitors V3 pool events (Swap, Mint, Burn, Collect) via reactive smart contracts, translates them into FCI state transitions through a ReactiveHookAdapter, and produces an independent per-pool FCI value for each V3 pool. The adapter owns a parallel FCI storage instance (separate diamond slot) and reuses existing FCI Mod files.

**Why this priority**: Core value proposition — extending FCI coverage beyond V4 is the primary goal. Without this, the feature has no purpose.

**Independent Test**: Can be fully tested by deploying a reactive contract that subscribes to a V3 pool's Swap/Mint/Burn events, verifying that each event triggers the correct hook callback on the ReactiveHookAdapter, and confirming the FCI index updates correctly.

**Acceptance Scenarios**:

1. **Given** a registered V3 pool with an active position, **When** a Swap event occurs on that V3 pool, **Then** the system increments swap counts for all tick ranges that overlap the swap's price traversal — identical behavior to native V4 afterSwap processing.
2. **Given** a V3 pool, **When** a Mint event occurs, **Then** the system registers the new position with its tick range, liquidity, and fee baseline — identical behavior to native V4 afterAddLiquidity processing.
3. **Given** a registered position on a V3 pool, **When** Collect events fire during its lifetime, **Then** the system accumulates fee amounts (amount0, amount1) for that position.
4. **Given** a registered position with accumulated Collect fees, **When** a Burn event occurs, **Then** the system uses the accumulated fees to compute the fee share ratio, accumulates HHI, and deregisters the position.
5. **Given** a V3 pool with accumulated HHI data, **When** a user queries the FCI index, **Then** the system returns an independent (A_T, B_T) pair for that V3 pool, computed via the same formula as V4 pools.

---

### User Story 2 — PoolKey ↔ V3 Pool Bidirectional Mapping (Priority: P1)

A developer needs to reference V3 pools using V4's PoolKey abstraction so that the entire FCI pipeline operates uniformly regardless of pool origin. PoolKeyExtLib provides deterministic, pure-function mappings between PoolKey and IUniswapV3Pool addresses, with the synthetic PoolKey's `hooks` field pointing to the ReactiveHookAdapter.

**Why this priority**: The mapping library is the architectural foundation — every other component depends on it. Co-equal with US1.

**Independent Test**: Can be tested by round-tripping: create a synthetic PoolKey from a V3 pool address, then recover the original V3 pool address from that PoolKey. Verify all five PoolKey fields are correctly populated.

**Acceptance Scenarios**:

1. **Given** a valid IUniswapV3Pool address, **When** PoolKeyExtLib converts it to a PoolKey, **Then** the resulting PoolKey contains the correct currency0, currency1, fee, tickSpacing (all read from the V3 pool), and the ReactiveHookAdapter as the hooks address.
2. **Given** a synthetic PoolKey with a ReactiveHookAdapter hooks address, **When** PoolKeyExtLib converts it back to a V3 pool reference, **Then** the original IUniswapV3Pool address is recovered.
3. **Given** two different V3 pools, **When** both are converted to PoolKeys, **Then** the resulting PoolIds (keccak256 of PoolKey) are distinct.
4. **Given** the same V3 pool converted twice, **When** both PoolKeys are compared, **Then** they are identical (deterministic mapping).

---

### User Story 3 — ReactiveHookAdapter Translates Events to Hook Calls (Priority: P1)

A ReactiveHookAdapter contract receives callbacks from the reactive layer (Reactive Network or Somnia L1) and translates them into V4-compatible hook function calls that the FCI contract processes. The adapter uses PoolKeyExtLib to construct the synthetic PoolKey and invokes the FCI's hook entry points.

**Why this priority**: The adapter is the bridge between reactive events and FCI processing. Without it, events cannot flow through the pipeline.

**Independent Test**: Can be tested by simulating a reactive callback with V3 Swap event data, verifying the adapter constructs the correct PoolKey and invokes afterSwap on FCI with properly formatted parameters.

**Acceptance Scenarios**:

1. **Given** a reactive callback containing a V3 Swap event, **When** the ReactiveHookAdapter processes it, **Then** it invokes the FCI's afterSwap path with a synthetic PoolKey and the swap's tick traversal range.
2. **Given** a reactive callback containing a V3 Mint event, **When** the ReactiveHookAdapter processes it, **Then** it invokes the FCI's afterAddLiquidity path with position parameters (tickLower, tickUpper, liquidity).
3. **Given** a reactive callback containing a V3 Collect event, **When** the ReactiveHookAdapter processes it, **Then** it accumulates fee amounts (amount0, amount1) for the position in adapter storage.
4. **Given** a reactive callback containing a V3 Burn event, **When** the ReactiveHookAdapter processes it, **Then** it reads accumulated Collect fees, computes the fee share ratio, accumulates HHI, and deregisters the position.
5. **Given** a callback from an unauthorized sender, **When** the ReactiveHookAdapter receives it, **Then** it reverts.

---

### User Story 4 — Portable Across Reactive Platforms (Priority: P2)

The reactive event subscription layer is designed to work on both Reactive Network and Somnia L1. The ReactiveHookAdapter and PoolKeyExtLib are platform-agnostic. Only the event subscription contracts are platform-specific.

**Why this priority**: Portability is a design constraint, not a user-facing feature. The core value is delivered by US1-US3 on either platform.

**Independent Test**: Can be tested by deploying the ReactiveHookAdapter and PoolKeyExtLib without any reactive subscription layer, and manually invoking the adapter's callback functions to verify the pipeline works independently of the reactive platform.

**Acceptance Scenarios**:

1. **Given** the ReactiveHookAdapter deployed on any EVM chain, **When** its callback functions are invoked with correctly formatted event data, **Then** FCI processes the events regardless of which reactive platform originated them.
2. **Given** a Reactive Network subscription contract, **When** it receives a V3 Swap event via `react(LogRecord)`, **Then** it emits a Callback targeting the ReactiveHookAdapter on the destination chain.
3. **Given** a Somnia subscription contract, **When** it receives a V3 Swap event via `_onEvent()`, **Then** it calls the ReactiveHookAdapter directly on-chain.

---

### Edge Cases

- What happens when a V3 pool's tick spacing differs from V4 conventions? PoolKeyExtLib reads tickSpacing directly from the V3 pool — no assumption about V4 conventions.
- What happens when a V3 Burn event fires for a position not registered in FCI (e.g., position existed before reactive monitoring started)? The system skips the HHI accumulation — deregistration of an unregistered position is a no-op.
- What happens when the reactive contract receives a duplicate event (e.g., reorg, replay)? Idempotency: Mint on an already-registered position updates rather than duplicates; Burn on an unregistered position is a no-op; Swap increments are naturally idempotent within a block.
- What happens when the V3 pool is uninitialized or has zero liquidity? Swap events on zero-liquidity pools produce no tick traversal — no ranges overlap, no swap counts increment.
- What happens when the reactive callback arrives out of order (Burn before Mint)? Burn on an unregistered position is a no-op. The position is simply never tracked.
- What happens when a standalone Collect event fires (no subsequent Burn)? The fee amounts are accumulated in adapter storage. No FCI state change occurs. If the position is eventually Burned, the accumulated fees are used. If the position is never Burned, the accumulated fees remain in storage (no leak — bounded by position count).
- What happens when a Collect event fires for a position not registered via Mint? The fees are accumulated in storage keyed by position. On Burn, if the position is not in the FCI registry, it's a no-op and the accumulated fees are cleaned up.

## Clarifications

### Session 2026-03-06

- Q: How should the ReactiveHookAdapter bridge the gap between V3 Burn raw token amounts and FCI's feeGrowthDelta-based fee share formula? → A: Use Collect + Burn event pair. Collect events accumulate fee amounts (amount0, amount1) over the position's lifetime. On Burn, the accumulated fees are used to compute a synthetic feeGrowthDelta by dividing by position liquidity. Standalone Collect events (no Burn) update the running total; the FCI state is only modified on Burn.
- Q: How are V3 pools registered for monitoring? → A: Factory-based discovery — subscribe to V3 Factory PoolCreated events and auto-monitor all new pools. The (tokenA, tokenB, fee) tuple uniquely characterizes a V3 pool.
- Q: Should there be a gas limit constraint or throttling mechanism for reactive callbacks? → A: Fixed gas limit with block-based deduplication — at most one Swap callback per V3 pool per block. Multiple swaps within the same block are collapsed into a single tick traversal (min→max tick), preserving FCI accuracy while reducing subscription cost.

### Brainstorm Session 2026-03-06

- Q: How should the adapter feed data into the FCI pipeline? → A: Parallel FCI instance — adapter owns its own REACTIVE_FCI_STORAGE_SLOT (different diamond slot). Reuses the same FCI Mod files (TickRangeRegistryMod, AccumulatedHHIMod, FeeShareRatioMod, etc.) but keeps state completely separate from V4 FCI.
- Q: How should the adapter authenticate callers? → A: Whitelist mapping — `mapping(address => bool) authorizedCallers` set post-deploy by owner. Platform-agnostic: add callbackProxy for Reactive Network, validator for Somnia.
- Q: How should the adapter handle V3 fee reconstruction? → A: Collect + Burn event pair. Subscribe to V3 Collect events in addition to Swap/Mint/Burn. Collect amounts are accumulated per position over its lifetime. On Burn, the accumulated total is consumed for fee share computation. Standalone Collect events update the running total without triggering FCI state changes.
- Q: Should the reactive subscription contract use multiplexed or separate callbacks? → A: Separate typed callbacks — `onV3Swap(V3SwapData)`, `onV3Mint(V3MintData)`, `onV3Burn(V3BurnData)`, `onV3Collect(V3CollectData)`. Matches ReactiveCallbackDataMod structs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a bidirectional mapping between V4 PoolKey and IUniswapV3Pool addresses via PoolKeyExtLib, using pure functions with no on-chain storage.
- **FR-002**: System MUST produce deterministic synthetic PoolKeys — the same V3 pool address always maps to the same PoolKey and PoolId.
- **FR-003**: Synthetic PoolKeys MUST use the ReactiveHookAdapter address as their `hooks` field to distinguish reactive-sourced events from native V4 events.
- **FR-004**: ReactiveHookAdapter MUST translate V3 Swap events into FCI afterSwap processing, providing the swap's tick traversal range.
- **FR-005**: ReactiveHookAdapter MUST translate V3 Mint events into FCI afterAddLiquidity processing, providing tickLower, tickUpper, liquidity, and fee baseline data.
- **FR-006**: ReactiveHookAdapter MUST accumulate V3 Collect event fee amounts (amount0, amount1) per position over its lifetime. On V3 Burn, the adapter MUST use the accumulated Collect fees to compute a synthetic feeGrowthDelta by dividing by position liquidity, then compute the fee share ratio for HHI accumulation.
- **FR-007**: System MUST produce independent per-pool FCI values — V3 pool indices are separate from V4 pool indices, computed via the same HHI accumulation formula. The ReactiveHookAdapter MUST own a parallel FCI storage instance (REACTIVE_FCI_STORAGE_SLOT) isolated from V4 FCI state.
- **FR-008**: ReactiveHookAdapter MUST authenticate callback senders via a whitelist mapping (mapping(address => bool)). Only addresses added by the owner may invoke callback functions.
- **FR-009**: Burn processing MUST handle positions not registered in FCI as a no-op (graceful skip).
- **FR-010**: The reactive subscription layer MUST be implementable on both Reactive Network (via react(LogRecord) + Callback emission) and Somnia L1 (via SomniaEventHandler._onEvent()) without changes to the ReactiveHookAdapter or PoolKeyExtLib.
- **FR-011**: System MUST decode V3 event data correctly: Swap(sender, amount0, amount1, sqrtPriceX96, liquidity, tick), Mint(sender, owner, tickLower, tickUpper, amount, amount0, amount1), Burn(owner, tickLower, tickUpper, amount, amount0, amount1), Collect(owner, recipient, tickLower, tickUpper, amount0, amount1).
- **FR-012**: PoolKeyExtLib MUST support extension to additional non-V4 protocols in future without breaking the existing V3 mapping interface.
- **FR-013**: The reactive subscription layer MUST subscribe to V3 Factory PoolCreated events to automatically discover new V3 pools and begin monitoring their Swap, Mint, Burn, and Collect events. The (tokenA, tokenB, fee) tuple uniquely identifies each V3 pool.
- **FR-014**: The reactive subscription layer MUST deduplicate Swap events per V3 pool per block — at most one Swap callback per pool per block. Multiple swaps within the same block MUST be collapsed into a single tick traversal representing the block's min→max tick range.
- **FR-015**: Reactive callbacks MUST use fixed gas limits per event type. Mint, Burn, and Collect events are not deduplicated (each position operation is distinct).
- **FR-016**: ReactiveHookAdapter MUST expose separate typed callback functions per V3 event type: `onV3Swap(V3SwapData)`, `onV3Mint(V3MintData)`, `onV3Burn(V3BurnData)`, `onV3Collect(V3CollectData)`. No multiplexed dispatch.

### Key Entities

- **PoolKeyExtLib**: Stateless library providing `fromV3Pool(IUniswapV3Pool, ReactiveHookAdapter) → PoolKey` and `toV3Pool(PoolKey) → IUniswapV3Pool` mappings.
- **ReactiveHookAdapter**: Contract at `src/reactive-integration/adapters/uniswapV3/` that receives reactive callbacks via separate typed functions (onV3Swap, onV3Mint, onV3Burn, onV3Collect). Owns a parallel FCI storage instance (REACTIVE_FCI_STORAGE_SLOT). Accumulates Collect fees per position; on Burn, computes fee share and triggers HHI accumulation. Auth via whitelist mapping.
- **Reactive Subscription Contract**: Platform-specific contract (one for Reactive Network, one for Somnia) that subscribes to V3 Factory PoolCreated events for auto-discovery, then subscribes to Swap/Mint/Burn/Collect events on discovered pools, and routes them to the ReactiveHookAdapter via typed callbacks.
- **Synthetic PoolKey**: A V4 PoolKey struct constructed from V3 pool parameters, uniquely identifying a V3 pool within the FCI system.

### Assumptions

- V3 pool parameters (token0, token1, fee, tickSpacing) are immutable and can be read once during PoolKey construction.
- The FCI Mod files (TickRangeRegistryMod, AccumulatedHHIMod, FeeShareRatioMod, SwapCountMod, BlockCountMod) are reused without modification. The ReactiveHookAdapter calls the same free functions but writes to its own storage slot.
- V3 Collect event fee amounts (amount0, amount1) accumulated over a position's lifetime are converted to synthetic feeGrowthDeltas by dividing by position liquidity. This reverses V3's internal fee accumulation and produces values compatible with FCI's existing fee share ratio formula without reading on-chain state.
- The ReactiveHookAdapter is deployed on the same chain as the FCI contract. Cross-chain callbacks (Reactive Network) target this chain.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every V3 Swap event processed by the system produces the same swap count increment behavior as an equivalent V4 swap through the same tick range — verified by parallel execution tests.
- **SC-002**: Every V3 Mint event processed by the system registers a position with identical state (tick range, liquidity, fee baseline) as an equivalent V4 addLiquidity — verified by state comparison tests.
- **SC-003**: Every V3 Burn event processed by the system produces the same HHI accumulation as an equivalent V4 removeLiquidity with the same fee share and lifetime — verified by index comparison tests.
- **SC-004**: PoolKeyExtLib round-trip mapping (V3→PoolKey→V3) recovers the original pool address with 100% accuracy across all tested V3 pools.
- **SC-005**: The ReactiveHookAdapter rejects 100% of unauthorized callback attempts.
- **SC-006**: The system handles all edge cases (unregistered Burn, duplicate events, zero-liquidity pools) without reverts or incorrect state mutations.
