# AngstromPoolObserver -- EVM-TDD Phase 1 (SPECIFY)

**Document type:** BTT Specification (Branching Tree Technique)
**Target file:** `contracts/src/_adapters/AngstromPoolObserver.sol`
**Status:** SPECIFY -- no Solidity code changes in this phase
**Date:** 2026-04-09
**Depends on:** AngstromAccumulatorConsumer BTT Spec (`angstrom-accumulator-consumer-btt-spec.md`), GrowthObservationStorageMod BTT Spec (`growth-observation-storage-mod-btt-spec.md`), EMAGrowthTransformationStorageMod BTT Spec (`ema-growth-transformation-storage-mod-btt-spec.md`)

---

## Overview

AngstromPoolObserver is the **composer/registry contract** that coordinates observation
recording across Angstrom-hooked Uniswap V4 pools. It sits between the read-only
AngstromAccumulatorConsumer (which reads Angstrom's storage) and the storage modules
(which persist observations and EMA state).

This contract has three distinct responsibilities:

1. **Pool registry:** Manages a set of observed pools, validating each registration
   against Angstrom's live configuration to ensure only legitimate Angstrom-hooked
   pools are tracked.
2. **Observation coordination (Layer 1):** Reads cumulative growth from Angstrom via
   the consumer, computes timing deltas, and delegates to GrowthObservationStorageMod
   for ring buffer writes.
3. **EMA coordination (Layer 2):** Triggers EMAGrowthTransformationStorageMod updates
   after each observation, keeping the EMA oracle in sync with the observation buffer.

This contract is NOT responsible for:

- Reading Angstrom storage directly (delegated to AngstromAccumulatorConsumer)
- Managing ring buffer internals (delegated to GrowthObservationStorageMod)
- Computing EMA transformations (delegated to EMAGrowthTransformationStorageMod)
- Modifying Angstrom state (Angstrom contracts are read-only)

---

## Immutable References

| Name                | Type                          | Description                                                       |
|---------------------|-------------------------------|-------------------------------------------------------------------|
| `CONSUMER`          | `AngstromAccumulatorConsumer`  | The read-only Angstrom client; source of all Angstrom data reads  |
| `ANGSTROM_ADDRESS`  | `address`                     | The Angstrom contract address; used for hook verification during pool registration |

Both are set in the constructor and cannot be changed after deployment.

---

## Access Control

### Roles

| Role    | Description                                                      | Functions                                   |
|---------|------------------------------------------------------------------|---------------------------------------------|
| `admin` | Can register new pools. Initially the deployer.                  | `registerPool`                              |
| `keeper`| Can trigger observation recording. Initially a single address.   | `recordObservation`, `recordObservationBatch` |

**Design decision:** Both roles are initially permissioned (single address each, set at
construction or via an admin setter). The keeper role can be opened to permissionless
access in a future upgrade by setting keeper to `address(0)` as a sentinel, or by
adding a `setKeeperOpen(bool)` toggle. This spec assumes permissioned access for both.

### Access Control Storage

The contract maintains admin and keeper addresses. Whether these use a simple storage
variable, an Ownable pattern, or a role-based system is an implementation detail. The
spec requires only that:

- Unauthorized callers to `registerPool` receive a revert with an Unauthorized-equivalent error.
- Unauthorized callers to `recordObservation` / `recordObservationBatch` receive a revert with an Unauthorized-equivalent error.
- Admin can update the keeper address.

---

## Per-Pool Registration Data

### Storage Layout (Conceptual)

Each registered pool is tracked via a `PoolRegistration` struct stored in a mapping
keyed by `PoolId`:

```
struct PoolRegistration {
    address token0;             // Lower-sorted token address
    address token1;             // Higher-sorted token address
    int24   tickSpacing;        // From Angstrom's PoolConfigStore at registration time
    uint64  lastObservedBlock;  // Block number of the last recorded observation for this pool
    bool    isRegistered;       // Registration flag
}
```

Additionally, the contract stores:

- `mapping(PoolId => PoolRegistration) registrations` -- main registry mapping
- The observation buffer and EMA state are stored in their respective diamond storage
  modules (GrowthObservationStorageMod and EMAGrowthTransformationStorageMod), keyed
  by the same `PoolId`.

### PoolId Derivation

The `PoolId` for an Angstrom pool is derived from a `PoolKey` with the following components:

| Field         | Value                                                      |
|---------------|-------------------------------------------------------------|
| `currency0`   | `Currency.wrap(token0)`                                     |
| `currency1`   | `Currency.wrap(token1)`                                     |
| `fee`         | Dynamic fee flag (`0x800000`)                               |
| `tickSpacing` | From Angstrom's PoolConfigStore (read at registration time) |
| `hooks`       | `IHooks(ANGSTROM_ADDRESS)`                                  |

The `PoolId` is the `keccak256` hash of the ABI-encoded `PoolKey`. This derivation
is deterministic and must match what Uniswap V4 uses internally.

---

## Function Specifications

### 1. registerPool

```
function registerPool(
    address token0,
    address token1,
    uint256 storeIndex,
    uint256 bufferSize,
    uint96  EMAperiods,
    int24   clampDelta
) external
```

**Purpose:** Registers a new pool for observation tracking. Validates the pool exists
in Angstrom's configuration, derives the PoolId, initializes the observation buffer
and EMA state, and stores the registration data.

**Algorithm:**

1. **Auth check:** Revert if `msg.sender` is not admin.
2. **Token sort check:** Revert if `token0 >= token1`.
3. **Angstrom verification:** Call `CONSUMER.getPoolConfig(token0, token1, storeIndex)`.
   This reverts with `NoEntry` if no pool exists at that index for this pair. On
   success, receive `(tickSpacing, bundleFee)`.
4. **PoolId derivation:** Construct `PoolKey(Currency.wrap(token0), Currency.wrap(token1), 0x800000, tickSpacing, IHooks(ANGSTROM_ADDRESS))` and compute `PoolId` via keccak256.
5. **Duplicate check:** Revert if `registrations[poolId].isRegistered` is true.
6. **Store registration:** Write `PoolRegistration(token0, token1, tickSpacing, 0, true)` to `registrations[poolId]`.
7. **Initialize observation buffer:** Call `initializePool(poolId, bufferSize)` from GrowthObservationStorageMod.
8. **Initialize EMA:** Call `initializeEMA(poolId, EMAperiods, clampDelta)` from EMAGrowthTransformationStorageMod.

**Ordering rationale:** The Angstrom verification (step 3) comes before the duplicate
check (step 5) because the PoolId derivation (step 4) requires `tickSpacing` from
step 3. An alternative is to re-derive the StoreKey and read the config store directly,
but using the consumer keeps the data flow clean.

#### BTT Tree

```
AngstromPoolObserver::registerPool
├── when caller is not admin
│   └── it should revert with Unauthorized.
└── when caller is admin
    ├── when token0 >= token1
    │   └── it should revert with TokensNotSorted.
    └── when token0 < token1
        ├── when pool does not exist in Angstrom PoolConfigStore at the given storeIndex
        │   └── it should revert with NoEntry (propagated from PoolConfigStoreLib.get via consumer).
        └── when pool exists in Angstrom PoolConfigStore
            ├── when the derived PoolId is already registered
            │   └── it should revert with PoolAlreadyRegistered.
            └── when the derived PoolId is not yet registered
                ├── it should store token0, token1, and tickSpacing in the registration.
                ├── it should derive and store the correct PoolId from PoolKey.
                ├── it should initialize the observation buffer for this poolId with bufferSize capacity.
                ├── it should initialize the EMA state for this poolId with the given EMAperiods and clampDelta.
                ├── it should mark the pool as registered (isRegistered = true).
                ├── it should set lastObservedBlock to 0.
                └── it should not modify registrations of other pools.
```

**Edge cases:**

- `bufferSize = 0`: Behavior depends on CircularBuffer.setup -- likely reverts. This
  is acceptable; callers should provide bufferSize >= 1.
- `storeIndex` pointing to a valid entry for a DIFFERENT pair: `getPoolConfig` reverts
  with `NoEntry` because the StoreKey will not match. Correct behavior.
- Re-registration after the pool was previously registered: Always reverts with
  `PoolAlreadyRegistered`. There is no deregistration mechanism in this spec.

---

### 2. recordObservation

```
function recordObservation(PoolId poolId) external
```

**Purpose:** Records a single growth observation for a registered pool. Reads the
latest cumulative growth from Angstrom, computes timing metadata, writes to the
observation buffer (Layer 1), and triggers an EMA update (Layer 2).

**Algorithm:**

1. **Auth check:** Revert if `msg.sender` is not authorized keeper.
2. **Registration check:** Revert if `registrations[poolId].isRegistered` is false.
3. **Freshness check:** Call `CONSUMER.lastBlockUpdated()`. If the result is
   `<= registrations[poolId].lastObservedBlock`, return silently (no new bundle data).
4. **Read growth:** Call `CONSUMER.globalGrowth(poolId)` to get the current cumulative growth.
5. **Compute relativeTimeDelta:**
   - Read the latest observation from GrowthObservationStorageMod via `latestObservation(poolId)`.
   - If the latest observation is zero (first observation for this pool), set `relativeTimeDelta = 0`.
   - Otherwise, compute `relativeTimeDelta = block.timestamp - lastObservationTimestamp`.
   - Note: `lastObservationTimestamp` is reconstructed from the latest observation's
     `blockNumber` and `relativeTimeDelta` fields, or tracked separately. The exact
     mechanism is an implementation detail. What matters is that `relativeTimeDelta`
     represents seconds since the previous observation was recorded.
6. **Record observation:** Call `recordObservation(poolId, block.number, relativeTimeDelta, cumulativeGrowth)` from GrowthObservationStorageMod.
7. **Update EMA:** Call `updateEMA(poolId)` from EMAGrowthTransformationStorageMod.
8. **Update last observed:** Set `registrations[poolId].lastObservedBlock` to `CONSUMER.lastBlockUpdated()`.

**relativeTimeDelta computation detail:**

The `relativeTimeDelta` field in GrowthObservation is a uint16 (max 65,535 seconds, ~18.2 hours).
If more than 18.2 hours elapse between observations, the SafeCastLib.toUint16 call inside
`newGrowthObservation` will revert. This is intentional -- it surfaces keeper liveness failures.
The observer does NOT attempt to clamp or work around this. The keeper must observe
frequently enough to stay within the uint16 range.

**Timestamp tracking detail:**

The contract needs to track the timestamp of the last observation to compute
`relativeTimeDelta`. Two approaches:

- **Option A:** Store `lastObservedTimestamp` alongside `lastObservedBlock` in the
  registration struct. Set it to `block.timestamp` after each observation.
- **Option B:** Derive the accumulated timestamp from the observation buffer by summing
  `relativeTimeDelta` values. This is expensive and fragile.

This spec recommends **Option A**. Add a `uint40 lastObservedTimestamp` field to the
registration struct (uint40 supports timestamps until year ~36,812).

#### BTT Tree

```
AngstromPoolObserver::recordObservation
├── when caller is not authorized keeper
│   └── it should revert with Unauthorized.
├── when pool is not registered
│   └── it should revert with PoolNotRegistered.
└── when pool is registered and caller is authorized
    ├── when CONSUMER.lastBlockUpdated() <= pool's lastObservedBlock
    │   └── it should return silently without modifying any state.
    └── when CONSUMER.lastBlockUpdated() > pool's lastObservedBlock
        ├── it should read globalGrowth from Angstrom via CONSUMER.
        ├── it should compute relativeTimeDelta as (block.timestamp - lastObservedTimestamp).
        ├── it should call GrowthObservationStorageMod.recordObservation with block.number, relativeTimeDelta, and globalGrowth.
        ├── it should call EMAGrowthTransformationStorageMod.updateEMA for this poolId.
        ├── it should update lastObservedBlock to CONSUMER.lastBlockUpdated().
        ├── it should update lastObservedTimestamp to block.timestamp.
        └── it should not modify the registration or observation state of any other pool.
```

**Edge cases:**

- First observation (lastObservedBlock == 0, lastObservedTimestamp == 0):
  `relativeTimeDelta` is `block.timestamp - 0 = block.timestamp`. This will overflow
  uint16 if `block.timestamp > 65535` (always true on mainnet). Therefore, the first
  observation must be handled specially: set `relativeTimeDelta = 0` when
  `lastObservedTimestamp == 0`. This is the "genesis" observation.
- Multiple bundles in one block: Not possible -- Angstrom enforces one bundle per block
  via its `lastBlockUpdated` check.
- `globalGrowth` returns 0 for an uninitialized pool: Valid. The observation records
  `cumulativeGrowth = 0`, which is correct for a pool that hasn't accrued rewards yet.

---

### 3. recordObservationBatch

```
function recordObservationBatch(PoolId[] calldata poolIds) external
```

**Purpose:** Records observations for multiple pools in a single transaction. This is
a gas optimization that reads `lastBlockUpdated()` once and reuses the value across
all pools.

**Algorithm:**

1. **Auth check:** Revert if `msg.sender` is not authorized keeper.
2. **Read lastBlockUpdated once:** Call `CONSUMER.lastBlockUpdated()` and cache the result.
3. **Iterate:** For each `poolId` in the array:
   a. Check registration. Skip unregistered pools (or revert -- see design note below).
   b. Check freshness against cached `lastBlockUpdated`. Skip if not fresh.
   c. Read `globalGrowth`, compute `relativeTimeDelta`, record observation, update EMA.
   d. Update `lastObservedBlock` and `lastObservedTimestamp`.

**Design note on unregistered pools in batch:** Two options:

- **Strict:** Revert the entire batch if any pool is unregistered. Simpler, but one bad
  PoolId bricks the entire batch.
- **Lenient:** Skip unregistered pools silently. More gas-efficient for the keeper, but
  masks errors.

This spec chooses **strict** behavior: revert if any pool in the batch is not registered.
The keeper is expected to maintain a correct list of registered pools.

#### BTT Tree

```
AngstromPoolObserver::recordObservationBatch
├── when caller is not authorized keeper
│   └── it should revert with Unauthorized.
├── when array is empty
│   └── it should return without modifying any state (no revert).
└── when array has one or more entries
    ├── when any poolId in the array is not registered
    │   └── it should revert with PoolNotRegistered.
    └── when all poolIds are registered
        ├── it should read CONSUMER.lastBlockUpdated() exactly once.
        ├── for each poolId where lastBlockUpdated <= lastObservedBlock
        │   └── it should skip that pool without modifying its state.
        └── for each poolId where lastBlockUpdated > lastObservedBlock
            ├── it should read globalGrowth from CONSUMER for that pool.
            ├── it should compute relativeTimeDelta for that pool.
            ├── it should record an observation via GrowthObservationStorageMod.
            ├── it should update EMA via EMAGrowthTransformationStorageMod.
            ├── it should update lastObservedBlock and lastObservedTimestamp for that pool.
            └── it should not affect pools not in the batch array.
```

---

### 4. isPoolRegistered

```
function isPoolRegistered(PoolId poolId) external view returns (bool)
```

**Purpose:** Returns whether a pool is registered in the observer.

#### BTT Tree

```
AngstromPoolObserver::isPoolRegistered
├── when poolId has been registered via registerPool
│   └── it should return true.
└── when poolId has not been registered
    └── it should return false.
```

No access control. Public view function.

---

### 5. getPoolRegistration

```
function getPoolRegistration(PoolId poolId) external view returns (
    address token0,
    address token1,
    int24   tickSpacing,
    uint64  lastObservedBlock
)
```

**Purpose:** Returns the registration data for a given pool.

#### BTT Tree

```
AngstromPoolObserver::getPoolRegistration
├── when poolId is not registered
│   └── it should return zero values (address(0), address(0), 0, 0).
└── when poolId is registered
    ├── it should return the token0 address provided at registration.
    ├── it should return the token1 address provided at registration.
    ├── it should return the tickSpacing read from Angstrom at registration time.
    └── it should return the current lastObservedBlock value.
```

No access control. Public view function. Returns zero-defaults for unregistered pools
rather than reverting, allowing callers to check existence via `token0 != address(0)`
or via `isPoolRegistered`.

---

## Algebraic Properties

### P1: Registration uniqueness

```
forall (token0, token1, storeIndex):
    registerPool(token0, token1, storeIndex, ...) succeeds at most once
```

**Rationale:** The PoolId derived from `(token0, token1, tickSpacing, ANGSTROM_ADDRESS)`
is deterministic. Once registered, the `isRegistered` flag prevents re-registration.
Since `tickSpacing` is determined by `storeIndex`, different `storeIndex` values for the
same pair (with different tick spacings) produce different PoolIds and can each be
registered independently.

### P2: Registration-Angstrom consistency

```
forall poolId registered via registerPool:
    at registration time, CONSUMER.getPoolConfig(token0, token1, storeIndex) did not revert
```

**Rationale:** `registerPool` calls `getPoolConfig` and reverts if it fails. A
successfully registered pool was verified to exist in Angstrom's PoolConfigStore at
registration time.

**Caveat:** Angstrom's admin could remove the pool from the config store after
registration. The observer does not re-verify on each observation. This is acceptable
because the accumulator values remain readable via `extsload` even after config removal.

### P3: Observation monotonicity

```
forall poolId, observation_a recorded before observation_b:
    observation_b.lastObservedBlock >= observation_a.lastObservedBlock
```

**Rationale:** `lastObservedBlock` is updated to `CONSUMER.lastBlockUpdated()`, which
is monotonically non-decreasing (Algebraic Property P1 of AngstromAccumulatorConsumer).
The freshness check ensures we only update when `lastBlockUpdated > lastObservedBlock`,
so the value strictly increases with each successful observation.

### P4: Skip idempotence

```
forall poolId, state S:
    let S' = recordObservation(poolId) applied to S
    let S'' = recordObservation(poolId) applied to S'
    if no new Angstrom bundle between S' and S'':
        S'' == S'
```

**Rationale:** The freshness check (`lastBlockUpdated <= lastObservedBlock`) causes
the second call to return without modifying state. The only way state changes is if
Angstrom processes a new bundle between the two calls.

### P5: Batch equivalence

```
forall poolIds = [A, B, C]:
    let S1 = recordObservationBatch([A, B, C]) applied to S
    let S2 = recordObservation(A); recordObservation(B); recordObservation(C) applied to S
    S1 == S2
```

**Rationale:** The batch function performs the same logic as sequential single calls.
The optimization (reading `lastBlockUpdated` once) does not affect correctness because
`lastBlockUpdated` is stable within a block.

**Caveat:** If the batch transaction spans multiple blocks (not possible in EVM, but
noted for completeness), this property would not hold. Since EVM transactions execute
atomically within a single block, this is guaranteed.

### P6: Cross-pool isolation

```
forall poolA != poolB:
    recordObservation(poolA) does not modify:
        - registrations[poolB]
        - GrowthObservationStorageMod state for poolB
        - EMAGrowthTransformationStorageMod state for poolB
```

**Rationale:** All storage writes are keyed by `PoolId`. The diamond storage modules
use per-pool mappings. No cross-pool state is shared or modified.

---

## Error Taxonomy

| Error                    | Source               | Trigger                                                        |
|--------------------------|----------------------|----------------------------------------------------------------|
| `Unauthorized`           | `registerPool`       | Caller is not admin                                            |
| `Unauthorized`           | `recordObservation`  | Caller is not authorized keeper                                |
| `Unauthorized`           | `recordObservationBatch` | Caller is not authorized keeper                            |
| `PoolAlreadyRegistered`  | `registerPool`       | PoolId already has `isRegistered == true`                      |
| `TokensNotSorted`        | `registerPool`       | `token0 >= token1`                                             |
| `NoEntry`                | `registerPool`       | Propagated from `CONSUMER.getPoolConfig` -- pool not in Angstrom |
| `PoolNotRegistered`      | `recordObservation`  | PoolId not in registry                                         |
| `PoolNotRegistered`      | `recordObservationBatch` | Any PoolId in array not in registry                        |
| `PoolAlreadyInitialized` | `registerPool`       | Propagated from `initializePool` -- should not occur if registration guard works correctly |
| `EMAAlreadyInitialized`  | `registerPool`       | Propagated from `initializeEMA` -- should not occur if registration guard works correctly |

**Note on propagated errors:** `PoolAlreadyInitialized` and `EMAAlreadyInitialized` can
only fire if there is a bug in the registration guard (the PoolId was initialized in the
storage modules without being marked as registered). Under correct operation, the
`PoolAlreadyRegistered` check prevents these from ever firing.

---

## Constructor Specification

```
constructor(
    AngstromAccumulatorConsumer _consumer,
    address _angstromAddress,
    address _admin,
    address _keeper
)
```

| Parameter            | Type                          | Validation | Description                          |
|----------------------|-------------------------------|------------|--------------------------------------|
| `_consumer`          | `AngstromAccumulatorConsumer`  | None       | The read-only Angstrom client        |
| `_angstromAddress`   | `address`                     | None       | Angstrom contract for hook verification |
| `_admin`             | `address`                     | None       | Initial admin address                |
| `_keeper`            | `address`                     | None       | Initial keeper address               |

**Design note:** `_angstromAddress` could be derived from `_consumer.ANGSTROM()`, but
storing it separately as an immutable avoids an external call on every registration.
The deployer must ensure `_angstromAddress == address(_consumer.ANGSTROM())`.

---

## Integration Flow Diagram

### Registration Flow

```
Admin → AngstromPoolObserver.registerPool(token0, token1, storeIndex, bufferSize, EMAperiods, clampDelta)
          │
          ├── [1] validates caller is admin
          ├── [2] validates token0 < token1
          ├── [3] calls CONSUMER.getPoolConfig(token0, token1, storeIndex)
          │         └── reads Angstrom PoolConfigStore via extsload + extcodecopy
          │         └── returns (tickSpacing, bundleFee) or reverts NoEntry
          ├── [4] derives PoolId from PoolKey(token0, token1, tickSpacing, 0x800000, ANGSTROM_ADDRESS)
          ├── [5] checks PoolId not already registered
          ├── [6] stores PoolRegistration
          ├── [7] calls GrowthObservationStorageMod.initializePool(poolId, bufferSize)
          │         └── sets up CircularBuffer in diamond storage
          └── [8] calls EMAGrowthTransformationStorageMod.initializeEMA(poolId, EMAperiods, clampDelta)
                    └── initializes OraclePack and config in diamond storage
```

### Observation Flow

```
Keeper → AngstromPoolObserver.recordObservation(poolId)
           │
           ├── [1] validates caller is keeper
           ├── [2] validates pool is registered
           ├── [3] reads CONSUMER.lastBlockUpdated()
           │         └── extsload on Angstrom slot 3, lower 64 bits
           ├── [4] freshness check: lastBlockUpdated > lastObservedBlock?
           │         └── if no: return silently
           │
           ├── [5] reads CONSUMER.globalGrowth(poolId)
           │         └── extsload on Angstrom slot 7 mapping + offset
           │
           ├── [6] computes relativeTimeDelta
           │         └── block.timestamp - lastObservedTimestamp (0 for genesis)
           │
           ├── [7] writes GrowthObservationStorageMod.recordObservation(poolId, ...)
           │         └── Layer 1: raw observation into CircularBuffer
           │
           ├── [8] writes EMAGrowthTransformationStorageMod.updateEMA(poolId)
           │         └── Layer 2: reads Layer 1 buffer, updates OraclePack
           │
           └── [9] updates lastObservedBlock and lastObservedTimestamp
```

### Batch Observation Flow

```
Keeper → AngstromPoolObserver.recordObservationBatch([poolA, poolB, poolC])
           │
           ├── [1] validates caller is keeper
           ├── [2] reads CONSUMER.lastBlockUpdated() once → cached
           └── [3] for each poolId in array:
                 ├── validates pool is registered
                 ├── freshness check against cached lastBlockUpdated
                 ├── reads CONSUMER.globalGrowth(poolId)
                 ├── computes relativeTimeDelta
                 ├── records observation (Layer 1)
                 ├── updates EMA (Layer 2)
                 └── updates lastObservedBlock and lastObservedTimestamp
```

---

## State Transition Summary

### Pool Lifecycle

```
Unregistered ──[registerPool]──> Registered (lastObservedBlock=0, lastObservedTimestamp=0)
                                      │
                                      ├──[recordObservation, fresh]──> Registered (lastObservedBlock=N, lastObservedTimestamp=T)
                                      │                                      │
                                      │                                      └──[recordObservation, stale]──> (no change)
                                      │
                                      └──[registerPool again]──> REVERT (PoolAlreadyRegistered)
```

There is no deregistration transition in this spec. Once registered, a pool remains
registered permanently. Future specs may add deregistration if needed.

### Observation Data Flow (Layered)

```
Layer 0: Angstrom Storage (read-only, external)
    └── globalGrowth accumulator, lastBlockUpdated, PoolConfigStore

Layer 0.5: AngstromAccumulatorConsumer (read-only adapter)
    └── extsload reads, bit extraction, SSTORE2 queries

Layer 1: GrowthObservationStorageMod (observation ring buffer)
    └── CircularBuffer of GrowthObservation, per-pool

Layer 2: EMAGrowthTransformationStorageMod (EMA oracle)
    └── OraclePack, per-pool, reads Layer 1

Coordinator: AngstromPoolObserver (this contract)
    └── Orchestrates reads from Layer 0.5, writes to Layer 1 and Layer 2
```

---

## Open Questions (for IMPLEMENT phase)

1. **Admin transfer:** Should the admin be transferable? If so, two-step transfer
   (propose + accept) is recommended for safety.
2. **Keeper rotation:** Should the keeper be updatable by admin? Recommended yes.
3. **Event emission:** Should `registerPool` and `recordObservation` emit events?
   Events cost gas but are valuable for off-chain indexing. Angstrom's core avoids
   events, but this is a peripheral contract where the trade-off may differ.
4. **Deregistration:** Should there be a mechanism to unregister a pool? If so, what
   happens to the existing observation buffer and EMA state?
5. **Genesis observation value:** Should the first observation use `relativeTimeDelta = 0`
   or some other sentinel? This spec recommends 0 to indicate "no prior observation."
6. **Hook address verification:** The spec mentions verifying the Uniswap V4 pool's hook
   address matches `ANGSTROM_ADDRESS`. This requires reading the pool's hook address
   from Uniswap V4's state. If this is expensive or complex, the verification could be
   deferred to the implementation phase. The PoolKey derivation already embeds
   `ANGSTROM_ADDRESS` as the hooks field, so the PoolId itself encodes this constraint.
