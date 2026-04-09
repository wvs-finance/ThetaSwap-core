# Security Audit: EMAGrowthTransformationStorageMod

**File:** `contracts/src/modules/EMAGrowthTransformationStorageMod.sol`
**Auditor:** Blockchain Security Auditor
**Date:** 2026-04-09
**Commit:** thetaswap-patches (pre-deployment)

---

## Findings Summary

| # | Focus Area | Severity | Result |
|---|---|---|---|
| 1 | Storage slot collision | -- | PASS |
| 2 | Initialization guard bypass | -- | PASS |
| 3 | Cross-module storage write exploit | -- | PASS |
| 4 | Config immutability | -- | PASS |
| 5 | Stale OraclePack TOCTOU | -- | PASS |
| 6 | Zero EMAperiods division-by-zero | Informational | ACCEPTED RISK |
| 7 | Access control absence (griefing) | Medium | OPEN |

---

## Detailed Findings

### 1. Storage Slot Collision -- PASS

Verified with `cast keccak`:

| Module | Preimage | Slot |
|---|---|---|
| EMAGrowthTransformationStorageMod | `thetaswap.storage.EMAGrowthTransformation` | `0x343bdefd...` |
| GrowthObservationStorageMod | `thetaswap.storage.GrowthObservationStorage` | `0x4f58f0dc...` |
| AccrualManagerMod | `accrualManager.angstrom` | `0xe6f92ab9...` |

All three are distinct. The hex constant on L24 matches the documented preimage exactly. No collision risk.

### 2. Initialization Guard Bypass -- PASS

`initializeEMA` (L49-56) follows check-then-set correctly:
- L51: reads `$.initialized[poolId]` and reverts if true.
- L55: sets `$.initialized[poolId] = true` after all writes.

No reentrancy vector exists because there are no external calls between the check and the set. The function writes only to its own diamond storage mappings (no callbacks, no delegatecall, no ETH transfer). Double-initialization is impossible within a single transaction or across transactions.

### 3. Cross-Module Storage Write Exploit -- PASS

`updateEMA` obtains a `storage` pointer to Layer 1's `GrowthObservationStorage` via `_growthObservationStorage()` (L70-71). However, the pointer is passed to `updateGrowthEMA()` which is declared `view` (EMAGrowthTransformationLib.sol L43). The Solidity compiler enforces that `view` functions cannot perform `SSTORE` operations. The Layer 1 buffer is read-only in this context.

Additionally, `updateEMA` itself does not write through the `buffer` pointer -- it only passes it to the `view` library function. The only `SSTORE` in `updateEMA` is L82 (`$.oraclePacks[poolId] = updatedOraclePack`), which writes to Layer 2 storage exclusively.

### 4. Config Immutability -- PASS

After `initializeEMA` sets `emaPeriodsConfig` and `clampDeltaConfig` (L52-53) and marks the pool as initialized (L55), there is no other function in this module that writes to these mappings:

- `updateEMA` only reads `$.emaPeriodsConfig[poolId]` and `$.clampDeltaConfig[poolId]` (L75-76).
- `getOraclePack` and `getEMAConfig` are `view`.
- `initializeEMA` reverts on re-entry due to the `initialized` guard.

Config is write-once and immutable as designed. No path modifies it post-initialization.

### 5. Stale OraclePack TOCTOU -- PASS

`updateEMA` reads `$.oraclePacks[poolId]` on L74 and writes the updated value on L82. This is within a single EVM execution frame with no external calls, callbacks, or reentrancy opportunities between the read and write. There is no TOCTOU vulnerability. The EVM executes storage operations atomically within a transaction, and no control flow leaves this function between the SLOAD and SSTORE.

### 6. Zero EMAperiods -- Informational (ACCEPTED RISK)

**Severity:** Informational
**Status:** Accepted per BTT spec

If `initializeEMA` is called with `EMAperiods = 0` (all four uint24 periods are zero), the first `updateEMA` call will propagate `EMAperiods = 0` into `OraclePack.insertObservation`. The behavior depends on OraclePackLibrary internals -- division by zero in EMA computation would cause an EVM panic (0x12 revert).

The BTT spec explicitly states: "No validation is performed on individual period values. The caller is responsible for providing sensible parameters." This is a caller responsibility, not a module defect. However, the failure mode is an irrecoverable bricked pool (config is immutable, and every `updateEMA` call would revert forever).

**Recommendation:** Consider adding a `require(EMAperiods != 0)` guard in `initializeEMA` to prevent permanently bricked pools. Cost: ~100 gas on initialization (cold path). Benefit: prevents irrecoverable misconfiguration.

### 7. Access Control Absence -- Medium

**Severity:** Medium
**Status:** Open

Both `initializeEMA` and `updateEMA` are free functions with no access control modifiers. Anyone who imports and calls these functions can:

1. **Initialize any pool with arbitrary config:** An attacker front-running the legitimate `initializeEMA` call can set `EMAperiods` and `clampDelta` to malicious values (e.g., `clampDelta = 0` to freeze the oracle, or `EMAperiods` with extreme values to make the EMA unresponsive). Since config is immutable, this permanently poisons the pool's oracle.

2. **Call updateEMA at attacker-chosen times:** While same-epoch calls are no-ops (the library short-circuits), an attacker can ensure `updateEMA` is called at strategically chosen moments to influence which observations are consumed. This is a weaker concern because the observation buffer is append-only and the EMA clamp limits manipulation, but it is still a deviation from intended behavior if only keepers should trigger updates.

The BTT spec states "Access control (the adapter handles permissions)" is NOT this module's responsibility. This is architecturally correct for the free-function diamond pattern -- the adapter wrapping these functions must enforce access control.

**Risk:** If the adapter is deployed without proper access control on `initializeEMA`, the initialization front-running attack is Critical severity (permanent oracle poisoning). The `updateEMA` permissionlessness is likely acceptable (the spec notes same-epoch calls are no-ops, and the EMA clamp limits manipulation).

**Recommendation:** Verify that the adapter contract wrapping these functions enforces:
- `onlyOwner` or `onlyGovernance` on `initializeEMA`
- At minimum, document whether `updateEMA` is intentionally permissionless or requires keeper restriction

---

## Residual Risks and Out-of-Scope Notes

1. **OraclePack internals not audited:** The `insertObservation` and `clampTick` functions from Panoptic's OraclePackLibrary are trusted dependencies. Bugs in those functions would propagate through this module.

2. **Adapter not yet written:** As of this audit, no adapter imports these free functions (`grep` confirms zero import sites outside this file). The access control finding (7) cannot be fully assessed until the adapter exists.

3. **Epoch rollover:** The 24-bit epoch counter in OraclePack rolls over after ~34 years (`2^24 * 64 seconds`). The `unchecked` subtraction in EMAGrowthTransformationLib L65-67 handles this correctly via uint24 wrapping. No action needed.

4. **GrowthObservation buffer not initialized:** If `updateEMA` is called for a pool where the Layer 1 observation buffer was never initialized, the `observationCount` check in the library (`count < 2`) will revert with `InsufficientObservations`. This is correct fail-safe behavior.
