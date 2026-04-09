# Code Review: EMAGrowthTransformationStorageMod vs BTT Spec

**File:** `contracts/src/modules/EMAGrowthTransformationStorageMod.sol`
**Spec:** `.scratch/ema-growth-transformation-storage-mod-btt-spec.md`
**Date:** 2026-04-09

---

## Checkpoint Results

| # | Check | Result | Notes |
|---|---|---|---|
| 1 | Diamond storage struct matches spec (4 mappings: oraclePacks, initialized, emaPeriodsConfig, clampDeltaConfig) | PASS | Struct at L15-20 has all 4 mappings with correct names, key types, and value types. Field order matches spec. |
| 2 | Storage slot hex matches `keccak256("thetaswap.storage.EMAGrowthTransformation")` | PASS | Verified via `cast keccak`: `0x343bdefdc18c4e700c86da83b816cde11ce64f06179e4a37d2d13986269d2913` matches constant at L23-24. |
| 3 | initializeEMA: EMAAlreadyInitialized check BEFORE any writes (C7) | PASS | L51 checks `$.initialized[poolId]` and reverts before any of the writes at L52-55. |
| 4 | initializeEMA: stores config, sets OraclePack.wrap(0), sets initialized = true -- in correct order | PASS | L52: emaPeriodsConfig, L53: clampDeltaConfig, L54: oraclePack = wrap(0), L55: initialized = true. Config before state before flag, matching spec intent. |
| 5 | updateEMA: EMANotInitialized check BEFORE any reads (C6) | PASS | L67 checks `!$.initialized[poolId]` and reverts before the buffer read (L70-71), OraclePack read (L74), and config reads (L75-76). |
| 6 | updateEMA: reads Layer 1 buffer via imported `_growthObservationStorage()` (C9 -- no hardcoded slot) | PASS | L70-71 calls `_growthObservationStorage().buffers[poolId]` -- the imported function from GrowthObservationStorageMod (imported at L9-11). No hardcoded Layer 1 slot constant. |
| 7 | updateEMA: reads own config + OraclePack, delegates to `updateGrowthEMA`, stores result | PASS | L74-76 read state/config, L79 delegates to `updateGrowthEMA`, L82 stores result. All four parameters match the library signature exactly. |
| 8 | getOraclePack: direct mapping read, returns zero for uninitialized | PASS | L88-90: single-expression return from mapping. Solidity default for uninitialized mapping entry is 0, which equals `OraclePack.wrap(0)`. |
| 9 | getEMAConfig: reads both config fields, returns zero for uninitialized | PASS | L95-98: reads both `emaPeriodsConfig` and `clampDeltaConfig`. Solidity defaults produce `(0, 0)` for uninitialized pools. |
| 10 | Free function pattern (C1), no access control (C4), no events (C5) | PASS | All functions are file-level free functions (not inside `library` or `contract`). No `onlyOwner`/auth modifiers. No `emit` statements. |

---

## Summary

**10/10 checkpoints pass.** The implementation is a faithful, clean translation of the BTT spec. No blockers, no suggestions, no nits.

### Minor spec-vs-code naming divergence (informational, not a defect)

The spec refers to the Layer 1 storage accessor as `getGrowthObservationStorage()` while the actual GrowthObservationStorageMod exports it as `_growthObservationStorage()` (with underscore prefix, matching the private-by-convention naming used across all ThetaSwap modules). The implementation correctly uses the actual exported name. The spec's naming is illustrative, not prescriptive -- no action needed.

### _emaStorage visibility

The spec shows `_emaStorage()` as `private pure` while the implementation declares it as `pure` (no explicit visibility). For free functions in Solidity >= 0.8.26, visibility specifiers are not permitted (free functions are always internal to the compilation unit), so the implementation is correct and the spec's `private` annotation is aspirational rather than literal.
