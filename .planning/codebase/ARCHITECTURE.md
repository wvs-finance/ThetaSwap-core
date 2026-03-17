# Architecture

**Analysis Date:** 2026-03-17

## Pattern Overview

**Overall:** Protocol-Agnostic Delegatecall Orchestrator with Reactive Network Integration

**Key Characteristics:**
- Multi-protocol adapter pattern: FeeConcentrationIndexV2 acts as protocol-agnostic orchestrator, delegatecalling protocol-specific facets (UniswapV3Facet, NativeUniswapV4Facet)
- Diamond storage pattern with disjoint slots: each module/facet owns isolated keccak256 hashed storage slots, preventing collisions
- Event-driven reactive architecture: Uniswap V3 events streamed via Reactive Network → destination adapter translates to FCI state updates
- SCOP-compliant code organization: no inheritance (`is`), no library keyword, no modifiers—all logic in standalone Mod files with free functions

## Layers

**Orchestration Layer:**
- Purpose: Protocol-agnostic FCI algorithm execution; coordinates delegatecalls to protocol facets
- Location: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol`
- Contains: Hook handlers (afterAddLiquidity, afterRemoveLiquidity, afterSwap, afterDonate), event emission (FCITermAccumulated), delegatecall routing
- Depends on: `IFCIProtocolFacet` (interface), FeeConcentrationIndexV2Storage (diamond storage), protocol facets via registry
- Used by: Hook infrastructure (PoolManager on V4), test harnesses, deployment scripts

**Protocol Facet Layer:**
- Purpose: Protocol-specific behavioral implementations (position key derivation, fee growth reads, tick resolution)
- Location: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol` (V3), `src/fee-concentration-index-v2/protocols/uniswap-v4/NativeUniswapV4Facet.sol` (V4)
- Contains: IFCIProtocolFacet function implementations (positionKey, latestPositionFeeGrowthInside, currentTick, etc.), pool registration (listen function)
- Depends on: Protocol-specific SDKs (IUniswapV3Pool, IUniswapV4PoolManager), FeeConcentrationIndexRegistryStorageMod, protocol admin storage
- Used by: FeeConcentrationIndexV2 via delegatecall, FCI initialization/admin flows

**Reactive Integration Layer:**
- Purpose: Bridge Uniswap V3 events from source chain → FCI state updates on destination chain via Reactive Network
- Location: `src/reactive-integration/` (top-level coordinator), `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol` (destination), `src/reactive-integration/ThetaSwapReactive.sol` (ReactVM consumer)
- Contains: Event callbacks (onV3Swap, onV3Mint, onV3Burn), pool registration/deregistration, tick shadow tracking
- Depends on: reactive-hooks library, reactive-lib (IReactive, ISubscriptionService), V3 event signatures
- Used by: Reactive Network infrastructure (ReactVM processes logs, emits callbacks to adapter)

**Storage Layer:**
- Purpose: Diamond storage implementation with disjoint slots for modularity
- Location: `src/fee-concentration-index-v2/modules/*StorageMod.sol` (FeeConcentrationIndexStorageV2Mod, FeeConcentrationIndexRegistryStorageMod, FCIProtocolFacetStorageMod)
- Contains: Storage struct definitions, keccak256 slot functions (fciV2Storage, fciRegistryStorage, protocolFciStorage), accessors/mutators
- Depends on: typed-uniswap-v4 types (FeeConcentrationState, TickRangeRegistryV2), disjoint slot isolation
- Used by: All contract layers (orchestration, facets, adapters)

**Type Layer:**
- Purpose: Strongly typed representations of FCI concepts (positions, ranges, snapshots)
- Location: `src/fee-concentration-index-v2/types/` (LiquidityPositionSnapshot, RangeSnapshot, EpochSnapshot, FlagsRegistry)
- Contains: Data structures for position state (liquidity, fee growth), range metadata, epoch statistics
- Depends on: V4-core types (PoolId, PoolKey), V3 types (via adapters)
- Used by: Storage layer, facets, orchestration layer

**Utility Layer:**
- Purpose: Shared helpers, libraries, and constants
- Location: `src/libraries/`, `src/utils/`, `src/reactive-integration/libraries/`
- Contains: HookUtilsMod (tick sorting), PoolKeyExtMod, FeeGrowthReaderExt, encoding/decoding utilities
- Depends on: Uniswap types and math libraries (Solady FixedPointMathLib)
- Used by: Facets, adapters, orchestration

## Data Flow

**Liquidity Position Lifecycle (V4 Native Hook):**

1. LP calls PoolManager.modifyLiquidity(ModifyLiquidityParams)
2. PoolManager delegatecalls FeeConcentrationIndexV2.afterAddLiquidity/afterRemoveLiquidity hooks
3. FCI extracts protocol flag from hookData → routes delegatecall to UniswapV3Facet or NativeUniswapV4Facet
4. Facet derives position key, reads fee growth, registers position in TickRangeRegistryV2
5. FCI accumulates fee concentration term (xk, xSquaredQ128) in FeeConcentrationIndexV2Storage
6. On removal, facet deregisters, FCI computes block lifetime and swap lifetime metrics
7. FCI emits FCITermAccumulated event with accumulated metrics

**Swap Event Processing (V3 Reactive Network):**

1. LP swaps on Uniswap V3 pool (source chain, e.g., Sepolia)
2. V3 pool emits Swap event: topic0=V3_SWAP_SIG, topics[1:3]=sender/recipient, data includes tick
3. Reactive Network monitors V3 pool, captures log
4. ReactVM (destination chain, e.g., Lasna) processes log → calls ThetaSwapReactive.react(LogRecord)
5. ThetaSwapReactive.react → ReactLogicMod.processLog → routes to ReactiveHookAdapter.onV3Swap
6. Adapter verifies rvmSender (deployer EOA), constructs PoolKey from V3 pool
7. Adapter calls incrementOverlappingRanges on reactiveFciStorage (isolated slot for V3 state)
8. FCI state updated asynchronously; metrics lag behind actual V3 state

**Position Registration (V3 Reactive + Native Hook):**

1. LP mints on V3 pool (source chain)
2. V3 emits Mint event: topic0=V3_MINT_SIG, topics[1:3]=owner/tickLower/tickUpper
3. ReactVM processes, calls ReactiveHookAdapter.onV3Mint
4. Adapter derives v3PositionKey = keccak256(owner, tickLower, tickUpper)
5. Adapter calls registerPosition on reactiveFciStorage with liquidity and tick range
6. Separate callback path: UniswapV3Callback listens to Mint via native hook, reads fee growth baseline

**Fee Growth Accumulation:**

1. During addPosition: FCI reads pool fee growth inside → stores as baseline per position
2. During swap: overlapping ranges increment swap count, block lifetime updates
3. During removePosition: reads fee growth inside, computes delta from baseline
4. Delta × liquidity × omega (theta weight) → fee concentration xSquaredQ128 term
5. Accumulated term stored in protocolFciStorage or protocolEpochFciStorage per pool

**State Management:**

- **V2 Storage** (native hook flow): FeeConcentrationIndexV2Storage at slot keccak256("thetaSwap.fci"), holds fciState[PoolId], registries[PoolId], baseline fees
- **Registry Storage** (facet lookup): FeeConcentrationIndexRegistryStorage at slot keccak256("thetaSwap.fci.registry"), maps bytes2 flag → facet address
- **Protocol Facet Storage** (per-protocol state): FCIProtocolFacetStorage at slot keccak256("fci.facet.storage"), holds protocol-specific counters
- **Reactive FCI Storage** (V3 adapter): reactiveFciStorage at slot keccak256("ReactiveHookAdapter.fci.storage"), isolated FeeConcentrationIndexStorage for async state
- **V3 Adapter Storage** (fee snapshots): V3AdapterStorage at slot keccak256("ReactiveHookAdapter.v3.storage"), maps poolId → positionKey → feeGrowthSnapshot0
- **Reactive VM Storage** (tick shadow): UniswapV3ReactiveStorage at slot keccak256("ThetaSwapReactive.vm.storage"), whitelist[chainId][pool], tickShadow[chainId][pool]

## Key Abstractions

**PoolId:**
- Purpose: Unique identifier for a liquidity pool across protocols (V3, V4)
- Examples: `PoolIdLibrary.toId(key)` derives from PoolKey
- Pattern: Used as map key in all storage layers; enables protocol-agnostic state lookups

**TickRange:**
- Purpose: Represents a contiguous tick interval [lower, upper]
- Examples: `TickRange rk = fromTicks(tickLower, tickUpper)` (V4 native), `fromTicksPacked(tickLower, tickUpper)` (FCI V2)
- Pattern: Used in TickRangeRegistryV2 for position spatial indexing; supports intersection queries for fee concentration computation

**LiquidityPositionSnapshot:**
- Purpose: Captures immutable position state (config + liquidity + fee growth) at registration time
- Examples: Created in FCI.afterAddLiquidity, passed to addPositionInRange
- Pattern: Frozen copy prevents stale reads; fee growth snapshot enables accurate delta computation at removal

**RangeSnapshot:**
- Purpose: Registry metadata for active ranges (tick range + aggregate liquidity + swap/block lifetime)
- Examples: Stored in TickRangeRegistryV2; queried by metrics facet
- Pattern: Aggregated state per pool enables efficient range queries and metrics aggregation

**IFCIProtocolFacet:**
- Purpose: Protocol adapter interface—all protocol-specific logic implements this
- Examples: UniswapV3Facet, NativeUniswapV4Facet (both implement IFCIProtocolFacet functions)
- Pattern: FCI V2 discovers facet via registry (bytes2 flag), delegatecalls all behavioral functions through this interface

**HookData Encoding:**
- Purpose: Protocol flag + action metadata packed into bytes, passed via PoolManager hook mechanism
- Examples: bytes2 flag = UNISWAP_V3_REACTIVE (0x0001), followed by tick or other action data
- Pattern: getProtocolFlagFromHookData extracts flag; facet decodes remaining data

## Entry Points

**FeeConcentrationIndexV2 Hooks:**
- Location: `src/fee-concentration-index-v2/FeeConcentrationIndexV2.sol`
- Triggers: PoolManager calls afterAddLiquidity/afterRemoveLiquidity/afterSwap/afterDonate when LP/swapper interacts with pool
- Responsibilities: Route to protocol facet, orchestrate position registration/deregistration, accumulate fee concentration metrics

**UniswapV3Facet.listen():**
- Location: `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol:74`
- Triggers: Admin calls to register a V3 pool for monitoring
- Responsibilities: Validate pool, derive V4 PoolKey equivalent, emit PoolAdded event for whitelisting

**ReactiveHookAdapter Callbacks:**
- Location: `src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol`
- Triggers: Reactive Network ReactVM calls onV3Swap/onV3Mint/onV3Burn after observing events on source chain
- Responsibilities: Verify rvmId/caller authorization, translate V3 event data to FCI state updates, increment overlapping ranges

**ThetaSwapReactive.react():**
- Location: `src/reactive-integration/ThetaSwapReactive.sol:76`
- Triggers: ReactVM injects LogRecord (V3 event) when processing subscription callbacks
- Responsibilities: Verify VM identity, delegate to ReactLogicMod.processLog for event routing

## Error Handling

**Strategy:** Explicit revert with custom errors; no silent failures

**Patterns:**
- Authorization checks: `requireAuthorized(msg.sender, authorizedCallers)` in adapter callbacks; `OnlyOwner()` in facet admin
- Protocol flag validation: `InvalidRvmId()` if rvmId mismatch in reactive callbacks
- Storage slot verification: `onlyDelegateCall()` modifier ensures facet functions run under delegatecall context
- Registry lookups: Return zero address if facet not registered; contract calling should validate before delegatecall
- Callback failures: On OOG or revert, adapter does NOT update state; UniswapV3Callback proxy catches and emits CallbackFailure but still calls pay()

## Cross-Cutting Concerns

**Logging:**
- Approach: Solidity events (FCITermAccumulated, PoolAdded, AuthorizedCallerUpdated, RvmIdUpdated, PoolRegistered, PoolUnregistered)
- Format: Event emitted after state commit; enables off-chain indexing and reactive subscriptions

**Validation:**
- Approach: Pre-condition checks (tick ranges, rvmId, authorization) before state mutation; no post-condition validation
- Example: ReactiveHookAdapter.onV3Mint verifies rvmSender matches stored rvmId before processing

**Authentication:**
- Approach: Owner pattern (set at construction, checked on admin ops); RVM identity verification (deployer EOA)
- Modules: ReactiveAuthMod.requireAuthorized, LibOwner (requireOwner/initOwner), ThetaSwapReactive owner checks

**Atomic State:**
- Approach: All FCI state mutations happen within single hook call (hook atomicity guarantees); reactive callbacks are async and may lag behind source chain
- Tradeoff: V3 reactive state is eventual consistency; native V4 hook flow is immediate

---

*Architecture analysis: 2026-03-17*
