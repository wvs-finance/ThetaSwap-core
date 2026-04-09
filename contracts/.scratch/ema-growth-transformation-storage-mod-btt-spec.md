# EMAGrowthTransformationStorageMod -- EVM-TDD Phase 1 (SPECIFY)

**Document type:** BTT Specification (Branching Tree Technique)
**Target file:** `contracts/src/modules/EMAGrowthTransformationStorageMod.sol`
**Status:** SPECIFY -- no Solidity code changes in this phase
**Date:** 2026-04-09
**Depends on:**
- EMAGrowthTransformationLib BTT Spec (`ema-growth-transformation-lib-btt-spec.md`)
- GrowthObservationStorageMod BTT Spec (`growth-observation-storage-mod-btt-spec.md`)

---

## Overview

EMAGrowthTransformationStorageMod is the **Layer 2 state module** for the EMA transformation
pipeline. It bridges the stateless EMAGrowthTransformationLib (which takes a `CircularBuffer
storage` parameter and returns an OraclePack value) with persistent per-pool diamond storage
for the OraclePack state, EMA configuration, and initialization guards.

This module provides the persistent state for `extensionFlag = CALLABLE (4)` Range Accrual
Notes. Other extensionFlags have their own storage modules:

| Flag | Value | State Module |
|---|---|---|
| VANILLA | 0 | None or minimal |
| ACCRUAL_DECRUAL | 1 | Windowed-delta-specific (TBD) |
| TARN | 2 | Cap-tracking (TBD) |
| BARRIERS | 3 | Barrier-condition (TBD) |
| CALLABLE | 4 | **EMAGrowthTransformationStorageMod** (this module) |
| BASKET_UNDERLIER | 5 | TBD |
| FLOATING_COUPON | 6 | TBD |

Each is independent. The observation buffer (GrowthObservationStorageMod) is shared across all.

### Pattern

Free functions (not inside a `library` or `abstract contract` block), consistent with all
other ThetaSwap modules and types. Functions compute their storage pointer internally via
keccak256 slot hashing -- the caller does NOT pass storage as a parameter.

### Responsibilities

This module is responsible for exactly four things:

1. **EMA state persistence:** Storing and retrieving the per-pool OraclePack (4 EMAs +
   8-slot median queue packed into a single uint256).
2. **EMA configuration persistence:** Storing the per-pool EMAperiods (packed 4 x uint24)
   and clampDelta (int24) as write-once config.
3. **Initialization lifecycle:** Managing a one-time initialization guard per pool that
   sets config and a zero-state OraclePack.
4. **Cross-module composition:** Orchestrating a complete EMA update by reading the
   observation buffer from GrowthObservationStorageMod's diamond storage, delegating to
   EMAGrowthTransformationLib, and persisting the result.

This module is NOT responsible for:

- Access control (the adapter handles permissions)
- Recording observations (GrowthObservationStorageMod handles that)
- Modifying Angstrom state (Angstrom contracts are read-only)
- EMA mathematics (EMAGrowthTransformationLib handles that)

### Architecture Layer Diagram

```
Adapter (access control, extsload from Angstrom)
    |
    |  1. recordObservation(poolId, ...)
    v
GrowthObservationStorageMod           <-- Layer 1 state
    |  (diamond storage: CircularBuffer per pool)
    |
    |  2. updateEMA(poolId)
    v
EMAGrowthTransformationStorageMod     <-- Layer 2 state (THIS MODULE)
    |  (diamond storage: OraclePack + config per pool)
    |
    |  Reads Layer 1 storage internally
    |  Delegates to:
    v
EMAGrowthTransformationLib            <-- Layer 2 logic (stateless)
    |  (takes buffer storage + OraclePack value, returns OraclePack)
    |
    |  Composes:
    +---> BlockNumberAwareGrowthObserverLib  (observation primitives)
    +---> GrowthToTickLib                    (growth ratio -> tick)
    +---> OraclePackLibrary                  (EMA + median update)
```

### The "Composer" Pattern

The key architectural insight is that `updateEMA(poolId)` takes ONLY a `PoolId` and resolves
everything else internally:

1. It computes **its own** diamond storage pointer (for OraclePack, EMAperiods, clampDelta).
2. It computes **GrowthObservationStorageMod's** diamond storage pointer (for the observation
   CircularBuffer).
3. It reads the per-pool CircularBuffer from Layer 1 storage.
4. It reads the per-pool OraclePack and config from its own storage.
5. It calls `updateGrowthEMA(buffer, oraclePack, periods, clamp)` (the stateless library).
6. It writes the returned OraclePack back to its own storage.

This is the "composer" pattern at the module level: a single free function orchestrates
reads from multiple diamond storage roots and writes to one, with all storage resolution
happening internally.

---

## Diamond Storage Design

### Storage Slot

The module uses a single keccak256-derived storage slot to anchor its state:

```
bytes32 constant EMA_GROWTH_TRANSFORMATION_STORAGE_SLOT =
    keccak256("thetaswap.storage.EMAGrowthTransformation");
```

This string is unique across all modules in the diamond. No other module uses this
hash input, guaranteeing disjoint storage slots.

### Storage Struct Layout

```
struct EMAGrowthTransformationStorage {
    mapping(PoolId => OraclePack) oraclePacks;
    mapping(PoolId => bool) initialized;
    mapping(PoolId => uint96) emaPeriodsConfig;
    mapping(PoolId => int24) clampDeltaConfig;
}
```

| Field | Type | Size | Purpose |
|---|---|---|---|
| `oraclePacks` | `mapping(PoolId => OraclePack)` | 256 bits per entry | Per-pool packed EMA state (4 EMAs + 8-slot median queue + epoch + lockMode) |
| `initialized` | `mapping(PoolId => bool)` | 1 bit per entry | One-time initialization guard per pool |
| `emaPeriodsConfig` | `mapping(PoolId => uint96)` | 96 bits per entry | Packed EMA period parameters: 4 x uint24 (spot, fast, slow, eons) |
| `clampDeltaConfig` | `mapping(PoolId => int24)` | 24 bits per entry | Max tick change per update for manipulation resistance |

**Design rationale for separate config mappings (vs. a packed struct):**

The config (EMAperiods + clampDelta) is write-once (set at initialization, never changed).
The OraclePack is updated on every `updateEMA` call. Separating them into distinct mappings
avoids loading 120 bits of immutable config on every OraclePack write, saving gas on the
hot path. The config is only read (not written) during `updateEMA`, and reading two cold
slots is cheaper than writing a combined slot that includes both mutable and immutable data.

### Storage Pointer Computation

Each free function computes the storage pointer internally:

```
function _emaStorage()
    private pure
    returns (EMAGrowthTransformationStorage storage s)
{
    bytes32 slot = EMA_GROWTH_TRANSFORMATION_STORAGE_SLOT;
    assembly ("memory-safe") {
        s.slot := slot
    }
}
```

### Slot Disjointness Guarantee

The diamond storage pattern guarantees disjointness because:

1. This module uses `"thetaswap.storage.EMAGrowthTransformation"` as the keccak256 preimage.
2. GrowthObservationStorageMod uses `"thetaswap.storage.GrowthObservationStorage"` as its
   keccak256 preimage.
3. AccrualManagerMod uses `"accrualManager.angstrom"` as its keccak256 preimage.
4. keccak256 is collision-resistant: distinct preimages produce distinct 32-byte slots.
5. Solidity's mapping derivation (`keccak256(key . slot)`) further isolates per-pool
   entries within each module's mapping.

No two modules can access each other's storage accidentally. Cross-module access (as in
`updateEMA` reading the observation buffer) is deliberate and explicit.

---

## Cross-Module Storage Access Pattern

### The Problem

`updateEMA(poolId)` needs to read from GrowthObservationStorageMod's diamond storage
(the per-pool `CircularBuffer`) while writing to its own diamond storage (the per-pool
`OraclePack`). Since both are free functions with diamond storage, `updateEMA` must compute
two storage pointers in a single call.

### Recommended Approach: Import Shared Storage Pointer Function (Option 1)

GrowthObservationStorageMod exports its storage pointer function:

```
function getGrowthObservationStorage()
    pure
    returns (GrowthObservationStorage storage $)
{
    bytes32 pos = GROWTH_OBSERVATION_STORAGE_SLOT;
    assembly ("memory-safe") {
        $.slot := pos
    }
}
```

EMAGrowthTransformationStorageMod imports and calls this function to obtain the observation
buffer for the given poolId:

```
GrowthObservationStorage storage obs = getGrowthObservationStorage();
CircularBuffer.Bytes32CircularBuffer storage buffer = obs.buffers[poolId];
```

This is the cleanest approach for the Compose pattern because:

1. **Single source of truth:** The slot constant lives in one place (GrowthObservationStorageMod).
   If the slot string changes, only one file needs updating.
2. **Explicit coupling:** The import dependency is visible in the file header, making the
   cross-module access auditable.
3. **Type safety:** The returned storage pointer is typed as `GrowthObservationStorage`,
   so the compiler prevents accessing fields that do not exist.

### Rejected Alternatives

**Option 2: Hard-code both slot constants.** This duplicates the Layer 1 slot constant in
the Layer 2 module. If GrowthObservationStorageMod changes its slot string, the Layer 2
module silently reads from a stale/empty slot. This is a maintenance hazard and violates
DRY.

**Option 3: Shared constants file.** This adds a third file that both modules depend on.
While it avoids duplication, it introduces an indirection layer without benefit. The
storage pointer function (Option 1) already provides both the constant and the typed
accessor, making a separate constants file redundant.

### Coupling Implications

- EMAGrowthTransformationStorageMod has a compile-time dependency on GrowthObservationStorageMod
  (the storage struct type and the pointer function).
- GrowthObservationStorageMod has NO dependency on EMAGrowthTransformationStorageMod.
  The dependency is unidirectional: Layer 2 depends on Layer 1, never the reverse.
- Adding a new Layer 2 transformation module (e.g., for extensionFlag = TARN) would
  import the same `getGrowthObservationStorage()` function without modifying Layer 1.

---

## Errors

```
error EMAAlreadyInitialized();
error EMANotInitialized();
```

These are the only errors defined by this module. All other errors propagate from
dependencies:

| Error | Source | Trigger |
|---|---|---|
| `EMAAlreadyInitialized` | EMAGrowthTransformationStorageMod | `initializeEMA` called on an already-initialized pool |
| `EMANotInitialized` | EMAGrowthTransformationStorageMod | `updateEMA` called on a pool whose EMA has not been initialized |
| `InsufficientObservations` | EMAGrowthTransformationLib | Observation buffer has < 2 entries (via `updateGrowthEMA`) |
| `EmptyBuffer` | BlockNumberAwareGrowthObserverLib | Observation buffer is empty (via `latestObservation` / `oldestObservation`) |
| EVM Panic 0x12 | `growthToTick` -> `FullMath.mulDiv` | Division by zero when oldest cumulativeGrowth == 0 |
| `InvalidSqrtPrice` | `growthToTick` -> `TickMath.getTickAtSqrtPrice` | Computed sqrtPriceX96 out of TickMath range |

---

## Section 1: BTT Behavior Trees

### 1.1 initializeEMA

**Signature:**

```
function initializeEMA(PoolId poolId, uint96 EMAperiods, int24 clampDelta)
```

**Mutability:** storage-mutating (writes OraclePack, config, and initialized flag)

**Preconditions:**
- `poolId` is a valid Uniswap V4 `PoolId` (bytes32). No validation is performed on the
  value itself -- any bytes32 is accepted.
- `EMAperiods` is a packed uint96 containing four uint24 period values. No validation is
  performed on individual period values (e.g., whether spot < fast < slow < eons). The
  caller is responsible for providing sensible parameters.
- `clampDelta` determines the maximum tick movement per update. No sign or range
  validation is performed. Negative values have well-defined behavior (OraclePackLibrary
  handles symmetric clamping).

```
EMAGrowthTransformationStorageMod::initializeEMA
|
+-- when the pool EMA is already initialized
|   +-- it should revert with EMAAlreadyInitialized.
|   +-- it should NOT modify the existing OraclePack.
|   +-- it should NOT modify the existing EMAperiods config.
|   +-- it should NOT modify the existing clampDelta config.
|   +-- it should NOT reset the initialized flag.
|
+-- when the pool EMA is not yet initialized
    +-- it should store the EMAperiods config for that poolId.
    +-- it should store the clampDelta config for that poolId.
    +-- it should initialize the OraclePack to a zero state (OraclePack.wrap(0)).
    +-- it should mark the pool EMA as initialized (initialized[poolId] = true).
    +-- it should not affect other poolIds' OraclePacks.
    +-- it should not affect other poolIds' initialization flags.
    +-- it should not affect other poolIds' EMAperiods configs.
    +-- it should not affect other poolIds' clampDelta configs.
```

**Design notes:**

- The `initialized` guard exists because `initializeEMA` sets config parameters that
  are intended to be immutable. Without the guard, a second call could change the EMA
  periods, invalidating all previously computed EMA values. This is especially dangerous
  because the OraclePack's EMAs are computed relative to the configured periods -- changing
  periods mid-stream produces discontinuous EMA values that could cause incorrect coupon
  gating.

- The check-then-set pattern (check `initialized[poolId]`, revert if true, set to true)
  is safe against reentrancy because this module has no callbacks or external calls. All
  operations are pure storage writes.

- The `EMAAlreadyInitialized` check MUST come before any storage writes. If config
  were written before the check, a failed re-initialization attempt could still partially
  overwrite config.

- The OraclePack is explicitly initialized to zero (`OraclePack.wrap(0)`). This means:
  - All EMAs start at 0 (int22 representation: tick 0)
  - All residuals start at 0
  - The epoch starts at 0
  - The order map starts at 0
  - The first `updateEMA` call will detect epoch != 0 (assuming current time > 64s)
    and perform a full update, establishing the first observation in the OraclePack

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| First initialization with valid params | Succeeds, config stored, OraclePack = 0, initialized = true |
| Second initialization (same poolId, same params) | Revert EMAAlreadyInitialized |
| Second initialization (same poolId, different params) | Revert EMAAlreadyInitialized |
| Initialize pool A, then pool B | Both succeed independently |
| Initialize pool A, check pool B is not initialized | pool B's initialized flag is false |
| EMAperiods = 0 (all zero periods) | Succeeds (no validation); updateEMA will likely revert with division by zero in OraclePack.updateEMAs |
| clampDelta = 0 | Succeeds; subsequent updateEMA will clamp all ticks to lastTick (oracle frozen) |
| clampDelta = type(int24).max | Succeeds; subsequent updateEMA will never clamp |
| clampDelta = type(int24).min (negative) | Succeeds; behavior depends on OraclePackLibrary's clampTick with negative delta |
| EMAperiods with spot > fast > slow > eons (inverted ordering) | Succeeds (no validation); EMA convergence order will be inverted |

---

### 1.2 updateEMA

**Signature:**

```
function updateEMA(PoolId poolId)
```

**Mutability:** storage-mutating (reads from Layer 1 storage, reads and writes to Layer 2
storage, reads `block.timestamp`)

**Preconditions:**
- The pool's EMA MUST be initialized (initialized[poolId] == true).
- The pool's observation buffer in GrowthObservationStorageMod SHOULD have at least 2
  observations (enforced by EMAGrowthTransformationLib, not by this module directly).

```
EMAGrowthTransformationStorageMod::updateEMA
|
+-- given the pool EMA is not initialized
|   +-- it should revert with EMANotInitialized.
|   +-- it should NOT read from GrowthObservationStorageMod storage.
|   +-- it should NOT call EMAGrowthTransformationLib.updateGrowthEMA.
|
+-- given the pool EMA is initialized
    |
    +-- it should compute this module's diamond storage pointer
    |   (EMA_GROWTH_TRANSFORMATION_STORAGE_SLOT).
    |
    +-- it should compute GrowthObservationStorageMod's diamond storage pointer
    |   (GROWTH_OBSERVATION_STORAGE_SLOT, via imported getGrowthObservationStorage()).
    |
    +-- it should read the observation buffer for poolId from Layer 1 storage:
    |   buffer = getGrowthObservationStorage().buffers[poolId]
    |
    +-- it should read the current OraclePack for poolId from its own storage:
    |   currentOraclePack = _emaStorage().oraclePacks[poolId]
    |
    +-- it should read the EMAperiods for poolId from its own storage:
    |   periods = _emaStorage().emaPeriodsConfig[poolId]
    |
    +-- it should read the clampDelta for poolId from its own storage:
    |   clamp = _emaStorage().clampDeltaConfig[poolId]
    |
    +-- it should call EMAGrowthTransformationLib.updateGrowthEMA(buffer, currentOraclePack, periods, clamp):
    |   |
    |   +-- (all behavioral branches from EMAGrowthTransformationLib::updateGrowthEMA apply)
    |   |
    |   +-- when the current epoch equals the OraclePack epoch
    |   |   +-- it should return currentOraclePack unchanged.
    |   |   +-- the module should store the unchanged OraclePack (or skip the SSTORE).
    |   |
    |   +-- when the current epoch is newer than the OraclePack epoch
    |   |   +-- it should return a new OraclePack with updated EMAs, median, and epoch.
    |   |
    |   +-- when the observation buffer has < 2 entries
    |   |   +-- it should revert with InsufficientObservations (propagated).
    |   |
    |   +-- when the observation buffer is empty
    |       +-- it should revert with EmptyBuffer (propagated).
    |
    +-- it should store the returned OraclePack back to its own storage:
    |   _emaStorage().oraclePacks[poolId] = returnedOraclePack
    |
    +-- it should not modify the EMAperiods config.
    +-- it should not modify the clampDelta config.
    +-- it should not modify the initialized flag.
    +-- it should not affect other poolIds' OraclePacks.
    +-- it should not affect other poolIds' configs.
    +-- it should not write to GrowthObservationStorageMod's storage.
```

**Design notes:**

- The `EMANotInitialized` check MUST come before any storage reads (config or OraclePack).
  This prevents wasted gas on SLOADs for a pool that will revert anyway. More importantly,
  it prevents reading uninitialized config (all zeros) from being passed to
  `updateGrowthEMA`, where `EMAperiods = 0` would cause division by zero in
  `OraclePackLibrary.updateEMAs`.

- The observation buffer is accessed read-only. `updateGrowthEMA` is a `view` function on
  the buffer (it calls `observationCount`, `oldestObservation`, `latestObservation` -- all
  view). This module never writes to Layer 1 storage.

- The same-epoch case: when `block.timestamp` is in the same 64-second epoch as the stored
  OraclePack's epoch, `updateGrowthEMA` returns the identical OraclePack. The module writes
  it back to storage regardless (the SSTORE is a no-op if the value is unchanged, costing
  only 100 gas for the warm-slot same-value case on EIP-2929 chains). An optimization could
  skip the SSTORE entirely, but this adds branching gas that may exceed the savings.

- **Cross-module storage read pattern:** This function is the canonical example of the
  "composer" pattern. It reads from two diamond storage roots:
  1. `EMA_GROWTH_TRANSFORMATION_STORAGE_SLOT` for its own config and OraclePack
  2. `GROWTH_OBSERVATION_STORAGE_SLOT` (via `getGrowthObservationStorage()`) for the buffer

  Both storage pointer computations are constant-time (the keccak256 preimages are
  compile-time constants). The mapping lookups add one `keccak256(poolId . mapping_slot)`
  computation each.

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| Pool not initialized | Revert EMANotInitialized |
| Pool initialized, observation buffer empty | Revert EmptyBuffer (propagated) |
| Pool initialized, observation buffer has 1 entry | Revert InsufficientObservations (propagated) |
| Pool initialized, buffer has 2+ entries, same epoch | OraclePack stored unchanged |
| Pool initialized, buffer has 2+ entries, new epoch | OraclePack updated with new EMAs/median/epoch |
| Two consecutive calls in same epoch | Second call is a no-op (same OraclePack returned) |
| Two consecutive calls in different epochs | Both produce updated OraclePacks |
| Pool A update does not affect pool B's OraclePack | Pool B's getOraclePack returns unchanged value |
| Growth tick exceeds clampDelta | Clamped tick is stored (clamp < growth tick) |
| OraclePack at zero state (first update after init) | Full update proceeds; epoch advances from 0 |
| Observation buffer in Layer 1 not initialized | Panic 0x32 (array OOB) or EmptyBuffer depending on CircularBuffer internals |

---

### 1.3 getOraclePack

**Signature:**

```
function getOraclePack(PoolId poolId) view returns (OraclePack)
```

**Mutability:** view

```
EMAGrowthTransformationStorageMod::getOraclePack
|
+-- given the pool EMA is not initialized
|   +-- it should return a zero OraclePack (OraclePack.wrap(0)).
|   +-- Rationale: uninitialized mapping entries in Solidity default to 0.
|       A zero OraclePack has epoch = 0, all EMAs = 0, all residuals = 0,
|       median = 0. Callers can distinguish uninitialized from initialized-
|       but-zero by checking the initialized flag separately (or calling
|       getEMAConfig).
|
+-- given the pool EMA is initialized
    |
    +-- given no updateEMA has been called since initialization
    |   +-- it should return OraclePack.wrap(0) (the zero state set during init).
    |
    +-- given updateEMA has been called at least once (in a new epoch)
        +-- it should return the OraclePack that was most recently stored by updateEMA.
        +-- the returned OraclePack should have a non-zero epoch (reflecting the
            epoch at which updateEMA was called).
```

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| Uninitialized pool | OraclePack.wrap(0) |
| Initialized, no updates | OraclePack.wrap(0) |
| After one updateEMA in new epoch | Non-zero OraclePack with current epoch |
| After multiple updateEMAs | Returns the most recently stored OraclePack |
| Pool A initialized and updated, pool B uninitialized | getOraclePack(A) returns non-zero, getOraclePack(B) returns zero |

---

### 1.4 getEMAConfig

**Signature:**

```
function getEMAConfig(PoolId poolId) view returns (uint96 EMAperiods, int24 clampDelta)
```

**Mutability:** view

```
EMAGrowthTransformationStorageMod::getEMAConfig
|
+-- given the pool EMA is not initialized
|   +-- it should return EMAperiods = 0.
|   +-- it should return clampDelta = 0.
|   +-- Rationale: uninitialized mapping entries default to 0.
|
+-- given the pool EMA is initialized
    +-- it should return the EMAperiods that were passed to initializeEMA.
    +-- it should return the clampDelta that was passed to initializeEMA.
    +-- the returned values should be identical regardless of how many
        updateEMA calls have been made (config is write-once).
```

**Edge cases to test:**

| Scenario | Expected |
|---|---|
| Uninitialized pool | (0, 0) |
| Initialized with periods=0x000001000002000003000004, clampDelta=100 | Returns exact values |
| After 100 updateEMA calls | Same config as at initialization |
| Pool A config vs pool B config | Independent; each returns its own |

---

## Section 2: Algebraic Properties (Invariants for Fuzz Testing)

### Property 1: Pool Isolation

**Statement:** For any two distinct poolIds A and B, operations on A never affect the
observable state of B. Specifically:

- `initializeEMA(A, ...)` does not change `getOraclePack(B)`, `getEMAConfig(B)`, or
  whether B is initialized.
- `updateEMA(A)` does not change `getOraclePack(B)` or `getEMAConfig(B)`.

**Formal:**

```
Pre:  Pool B is initialized.
      oracleB = getOraclePack(B)
      (periodsB, clampB) = getEMAConfig(B)
      A != B

Action: initializeEMA(A, anyPeriods, anyClamp)  OR  updateEMA(A)

Post: getOraclePack(B) == oracleB
      getEMAConfig(B) == (periodsB, clampB)
```

**Test approach:** Initialize two pools with different configs. Run updateEMA on pool A
(with sufficient observations). After each operation, verify pool B's OraclePack and
config are unchanged.

---

### Property 2: Initialization Guard (At-Most-Once)

**Statement:** `initializeEMA(poolId, EMAperiods, clampDelta)` succeeds at most once per
poolId. The second call always reverts with `EMAAlreadyInitialized` regardless of
parameters.

**Formal:**

```
Pre:  initializeEMA(poolId, periods1, clamp1) succeeded
Action: initializeEMA(poolId, periods2, clamp2)  // for any periods2, clamp2
Post: reverts with EMAAlreadyInitialized
```

**Corollary:** The EMA config (EMAperiods, clampDelta) for a pool is immutable after
initialization. There is no mechanism to reconfigure or re-initialize.

**Test approach:** Fuzz `periods1`, `clamp1`, `periods2`, `clamp2`. First call succeeds,
second call always reverts.

---

### Property 3: Config Immutability

**Statement:** `getEMAConfig(poolId)` returns the same `(EMAperiods, clampDelta)` that
were passed to `initializeEMA(poolId, EMAperiods, clampDelta)`, regardless of how many
`updateEMA` calls have been made.

**Formal:**

```
Pre:  initializeEMA(poolId, P, C) succeeded

Action: updateEMA(poolId) called N times (N >= 0)

Post: getEMAConfig(poolId) == (P, C)
```

**Test approach:** Initialize a pool. Run a fuzzed number of updateEMA calls (with
appropriate observation buffer setup). After each update, assert getEMAConfig returns
the original values.

---

### Property 4: Update Idempotence Within Epoch

**Statement:** Two consecutive `updateEMA(poolId)` calls in the same 64-second epoch
produce the same stored OraclePack. The second call is a no-op.

**Formal:**

```
Pre:  Pool initialized, observation buffer has >= 2 entries.
      updateEMA(poolId) called at time T.
      oracleAfterFirst = getOraclePack(poolId)

Action: updateEMA(poolId) called at time T' where
        (T >> 6) & 0xFFFFFF == (T' >> 6) & 0xFFFFFF  (same epoch)

Post: getOraclePack(poolId) == oracleAfterFirst
```

**Derivation:** This follows from EMAGrowthTransformationLib's same-epoch short-circuit:
`updateGrowthEMA` returns `currentOraclePack` unchanged when the epoch matches. The
module stores it back (a same-value SSTORE, which is a no-op at the EVM level).

**Test approach:** Call updateEMA twice within 63 seconds (or in the same block). Assert
OraclePack is bitwise identical after both calls.

---

### Property 5: Update-Then-Read Consistency

**Statement:** After a successful `updateEMA(poolId)`, `getOraclePack(poolId)` returns
exactly the OraclePack that `EMAGrowthTransformationLib.updateGrowthEMA` computed.

**Formal:**

```
Pre:  Pool initialized.
      buffer = getGrowthObservationStorage().buffers[poolId]
      currentOP = getOraclePack(poolId)
      (P, C) = getEMAConfig(poolId)

Action: updateEMA(poolId)

Post: getOraclePack(poolId) == updateGrowthEMA(buffer, currentOP, P, C)
```

**Test approach:** In a test harness that exposes the underlying library function,
call `updateGrowthEMA` directly with the same inputs that `updateEMA` would use.
Compare the result to `getOraclePack(poolId)` after calling `updateEMA`. Assert
bitwise equality.

---

### Property 6: Zero-State Reads for Uninitialized Pools

**Statement:** For any poolId that has never been initialized:

```
getOraclePack(poolId) == OraclePack.wrap(0)
getEMAConfig(poolId) == (0, 0)
```

**Derivation:** Solidity mapping entries default to zero. Since no writes have occurred
for this poolId, all reads return the zero value for their type.

**Test approach:** Generate random poolIds (fuzzed bytes32). Assert both view functions
return zero values without any prior setup.

---

## Section 3: Test Matrix -- Cross-Cutting Scenarios

### 3.1 Full Lifecycle (Single Pool)

| Step | Action | Assertion |
|---|---|---|
| 1 | `initializeEMA(A, periods, clamp)` | initialized = true, getOraclePack(A) == 0, getEMAConfig(A) == (periods, clamp) |
| 2 | `initializePool(A, 256)` on GrowthObservationStorageMod | Observation buffer ready (separate module) |
| 3 | Record 3 observations to pool A | observationCount(A) == 3 |
| 4 | `updateEMA(A)` (new epoch) | getOraclePack(A) != 0; epoch == current epoch |
| 5 | `updateEMA(A)` (same epoch) | getOraclePack(A) unchanged from step 4 |
| 6 | Warp to next epoch; record 1 more observation | observationCount(A) == 4 |
| 7 | `updateEMA(A)` (new epoch) | getOraclePack(A) updated; epoch == new epoch; EMAs shifted toward new tick |
| 8 | `getEMAConfig(A)` | Returns same (periods, clamp) as step 1 |

### 3.2 Multi-Pool Independence

| Step | Action | Pool A State | Pool B State |
|---|---|---|---|
| 1 | `initializeEMA(A, periodsA, clampA)` | initialized, OP=0 | uninitialized |
| 2 | `initializeEMA(B, periodsB, clampB)` | initialized, OP=0 | initialized, OP=0 |
| 3 | Setup observation buffers for both | -- | -- |
| 4 | Record observations to A only | has observations | empty |
| 5 | `updateEMA(A)` | OraclePack updated | OraclePack still 0 |
| 6 | `updateEMA(B)` | unchanged | Revert (InsufficientObservations or EmptyBuffer) |
| 7 | Record observations to B | unchanged | has observations |
| 8 | `updateEMA(B)` | unchanged | OraclePack updated |
| 9 | Verify A's OraclePack unchanged after step 8 | same as step 5 | -- |

### 3.3 Initialization Ordering vs. Layer 1

| Scenario | Action | Expected |
|---|---|---|
| EMA init before observation buffer init | `initializeEMA(X, ...)`; then `updateEMA(X)` | Revert (Layer 1 buffer not set up -> EmptyBuffer or Panic) |
| EMA init after observation buffer init and record | `initializePool(X, 256)`; record 3 obs; `initializeEMA(X, ...)`; `updateEMA(X)` | Succeeds; OraclePack updated |
| Observation buffer init, EMA never initialized | Record observations; `updateEMA(X)` | Revert EMANotInitialized |
| Both initialized, but no observations recorded | `initializePool(X, 256)`; `initializeEMA(X, ...)`; `updateEMA(X)` | Revert InsufficientObservations (buffer has 0 entries, < 2) |

### 3.4 Error Priority

When multiple error conditions apply simultaneously, the first check in the function
determines which error is raised. The required check ordering is:

| Priority | Check | Error |
|---|---|---|
| 1 (first) | `initialized[poolId] == false` | `EMANotInitialized` |
| 2 | `observationCount(buffer) < 2` | `InsufficientObservations` (from lib) |
| 3 | `oldest.cumulativeGrowth() == 0` | EVM Panic 0x12 (from growthToTick) |
| 4 | Ratio out of TickMath range | `InvalidSqrtPrice` (from growthToTick) |

If EMA is not initialized, the function MUST revert with `EMANotInitialized` regardless
of the observation buffer state. This is enforced by checking initialization before
reading the buffer.

---

## Section 4: Relationship to Other Components

### Consumer: Adapter (recordAndUpdateEMA)

The adapter orchestrates the full update flow:

```
Keeper calls adapter.recordAndUpdateEMA(poolId):
  1. Adapter reads globalGrowth from Angstrom via extsload (read-only)
  2. Adapter calls GrowthObservationStorageMod.recordObservation(poolId, ...)
     -> writes to Layer 1 storage
  3. Adapter calls EMAGrowthTransformationStorageMod.updateEMA(poolId)
     -> reads Layer 1 storage, writes to Layer 2 storage
  4. Done.
```

Steps 2 and 3 MUST execute in this order. If updateEMA were called before recordObservation,
the EMA update would use stale observation data (the newly recorded observation would be
missing from the buffer).

### Read Consumer: Coupon Gating Logic

Callers that need the current EMA-smoothed tick for coupon gating read it via:

```
OraclePack op = getOraclePack(poolId);
int24 currentSpotEMA = op.spotEMA();
int24 currentFastEMA = op.fastEMA();
int24 currentMedian  = OraclePackLibrary.getMedianTick(op);
```

This is a direct read from diamond storage -- no computation required beyond the
OraclePack unpacking.

### Sibling: GrowthObservationStorageMod (Layer 1)

This module reads but never writes to Layer 1 storage. The dependency is strictly
one-directional:

```
GrowthObservationStorageMod  <---reads---  EMAGrowthTransformationStorageMod
       (Layer 1)                                    (Layer 2)
```

Layer 1 is unaware of Layer 2's existence. Multiple Layer 2 modules can read from the
same Layer 1 observation buffer without coordination.

### Sibling: AccrualManagerMod

AccrualManagerMod (`contracts/src/modules/AccrualManagerMod.sol`) owns its own diamond
storage at `keccak256("accrualManager.angstrom")`. It has no direct dependency on this
module, but the adapter may compose both: first update the EMA oracle, then use the
resulting OraclePack values to gate accrual computations.

---

## Section 5: Implementation Constraints

### C1: Free Function Pattern

All functions MUST be free functions (not inside a `library` or `abstract contract` block).
This is consistent with GrowthObservationStorageMod, AccrualManagerMod, and all other
ThetaSwap storage modules.

### C2: No Storage Parameter

Unlike EMAGrowthTransformationLib (which takes `CircularBuffer storage` as a parameter),
the functions in this module take `PoolId` and compute the storage pointer internally.
The caller never sees or handles the raw storage struct. This encapsulates the storage
layout and the cross-module access pattern.

### C3: PoolId as First Parameter

All functions take `PoolId` as their first parameter for consistency and to enable
potential `using ... for PoolId` syntax in consuming contracts.

### C4: No Access Control

This module MUST NOT implement access control (e.g., `onlyKeeper`, `onlyAdapter`).
Access control is the adapter's responsibility. This module is a pure storage primitive.

### C5: No Event Emission

Consistent with Angstrom's design decision ("No Events: Contracts avoid events to save
gas"), this module MUST NOT emit events.

### C6: Error Ordering in updateEMA

The `EMANotInitialized` check MUST precede all storage reads and library calls. This
ensures deterministic error priority (see Section 3.4).

### C7: Error Ordering in initializeEMA

The `EMAAlreadyInitialized` check MUST precede all storage writes. This ensures that a
failed re-initialization attempt produces no state changes.

### C8: No Config Mutation After Initialization

There MUST be no function that modifies `emaPeriodsConfig` or `clampDeltaConfig` after
`initializeEMA` has been called. Config is write-once. This is enforced by the absence
of any setter function, combined with the `EMAAlreadyInitialized` guard on `initializeEMA`.

### C9: Cross-Module Import

This module MUST import `getGrowthObservationStorage()` (or equivalent) from
GrowthObservationStorageMod to access Layer 1 storage. It MUST NOT hard-code or
duplicate the Layer 1 storage slot constant.

---

## Section 6: Gas Considerations

### Storage Access Pattern for updateEMA

Each `updateEMA(poolId)` call incurs:

1. **Layer 2 reads (this module's storage):**
   - 1 SLOAD for `initialized[poolId]` (warm after first access in tx)
   - 1 SLOAD for `oraclePacks[poolId]` (256 bits, single slot)
   - 1 SLOAD for `emaPeriodsConfig[poolId]` (96 bits, single slot)
   - 1 SLOAD for `clampDeltaConfig[poolId]` (24 bits, single slot)

2. **Layer 1 reads (GrowthObservationStorageMod's storage):**
   - 2+ SLOADs from `updateGrowthEMA`: `observationCount`, `oldestObservation`,
     `latestObservation` (all via CircularBuffer, which reads `_count` + array entries)

3. **Layer 2 write (this module's storage):**
   - 1 SSTORE for `oraclePacks[poolId]` (256 bits, single slot)

4. **Computation:**
   - All EMAGrowthTransformationLib computation (FullMath, TickMath, OraclePack update)
   - Two diamond storage pointer computations (both are compile-time constants)

**Total estimated gas (new-epoch, warm slots):** ~15,000-25,000 gas, dominated by the
OraclePack SSTORE (5,000 gas for a dirty-slot write) and CircularBuffer SLOADs.

**Same-epoch fast path:** ~3,000-5,000 gas (read initialized flag, read OraclePack, detect
same epoch via `updateGrowthEMA`, write back unchanged OraclePack -- same-value SSTORE
costs 100 gas on EIP-2929).

### initializeEMA Gas

`initializeEMA` is a one-time operation per pool. Its gas cost is approximately:

- 1 SLOAD for `initialized[poolId]` check
- 4 SSTOREs for `initialized`, `oraclePacks`, `emaPeriodsConfig`, `clampDeltaConfig`
- Total: ~80,000-100,000 gas (cold SSTOREs at 20,000 each)

### getOraclePack / getEMAConfig Gas

Pure reads: 1-2 SLOADs each, approximately 2,100 gas cold or 100 gas warm per slot.

---

## Section 7: Fuzz Input Ranges

### For initializeEMA:

| Parameter | Type | Min | Max | Notes |
|---|---|---|---|---|
| poolId | bytes32 | 0 | 2^256-1 | Any bytes32 is valid |
| EMAperiods | uint96 | 0 | 2^96-1 | Packed 4 x uint24; no validation |
| clampDelta | int24 | -8388608 | 8388607 | Full int24 range; no validation |

### For updateEMA:

| Parameter | Type | Preconditions |
|---|---|---|
| poolId | bytes32 | Must be initialized (initializeEMA called) |
| -- (implicit) | block.timestamp | Controls epoch; fuzz to cover same-epoch and new-epoch paths |
| -- (implicit) | observation buffer | Must have >= 2 entries; controlled via Layer 1 setup |

### For cross-module fuzz:

| Scenario | Variables to Fuzz |
|---|---|
| Pool isolation | Two distinct poolIds, independent observation buffers |
| Config immutability | Number of updateEMA calls between config reads |
| Epoch boundary | block.timestamp values that straddle 64-second boundaries |
| Clamp effectiveness | Growth tick vs. clampDelta (test clamp binding vs. non-binding) |

---

## Section 8: Security Considerations

### 8.1 Stale Oracle Risk

If the keeper stops calling `updateEMA`, the stored OraclePack becomes stale. Callers
that read `getOraclePack(poolId).epoch()` can detect staleness by comparing against the
current epoch. However, this module provides no built-in staleness check. The adapter or
consuming contract should implement staleness validation if coupon gating depends on
oracle freshness.

### 8.2 Observation Buffer / EMA Initialization Ordering

There is no enforced ordering between `initializePool` (Layer 1) and `initializeEMA`
(Layer 2). Both can be called independently. However, `updateEMA` will fail if the
observation buffer is not set up or has < 2 entries. The adapter SHOULD ensure:

1. `initializePool(poolId, bufferSize)` is called first.
2. At least 2 observations are recorded.
3. `initializeEMA(poolId, periods, clamp)` is called.
4. `updateEMA(poolId)` can then succeed.

Steps 1-3 can occur in any relative order, but step 4 requires all three preconditions.

### 8.3 Zero EMAperiods

If `initializeEMA` is called with `EMAperiods = 0` (all four period values are 0), the
first `updateEMA` will propagate a division-by-zero revert from
`OraclePackLibrary.updateEMAs`. The pool's OraclePack will be permanently stuck at zero.
This module does not validate EMAperiods because validation logic (e.g., minimum period
thresholds, ordering constraints) is a policy decision that belongs in the adapter.

### 8.4 Cross-Module Storage Pointer Stability

If GrowthObservationStorageMod changes its storage slot constant, this module's
`updateEMA` will read from a stale/empty slot, producing EmptyBuffer reverts or
incorrect data. The imported `getGrowthObservationStorage()` function provides
compile-time coupling that ensures the correct slot is always used, but this coupling
must be verified during code review whenever Layer 1's storage slot is modified.
