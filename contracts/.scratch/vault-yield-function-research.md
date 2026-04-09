# Vault Yield Function Research: Custom Observable-Driven ERC-4626 Patterns

Date: 2026-04-09

## Executive Summary

No existing library provides a turnkey "pluggable yield function" abstraction for ERC-4626 vaults. However, several production patterns exist that can be composed. The most directly relevant pattern already exists in this codebase -- Panoptic's CollateralTracker.

## Findings Summary

| # | Project | Pattern | Relevance |
|---|---------|---------|-----------|
| 1 | OpenZeppelin ERC-4626 | Virtual `totalAssets()` override | HIGH -- simplest base |
| 2 | Solady ERC-4626 | Virtual `totalAssets()` + fullMulDiv precision | HIGH -- gas-optimized, matches X128MathLib |
| 3 | Solmate ERC-4626 | Abstract `totalAssets()` (no default) | MEDIUM-HIGH -- forces implementation |
| 4 | Panoptic CollateralTracker | `totalAssets = deposits + assetsInAMM + unrealizedInterest()` | CRITICAL -- closest production template |
| 5 | Existing AccrualManagerMod + AngstromRANOracleAdapter | `settleAndCheckpoint()`, `viewAccruedRatio()` | CRITICAL -- 80% of vault logic exists |
| 6 | Yearn V3 Tokenized Strategy | `_harvestAndReport()` periodic yield function | MEDIUM -- push model, adds latency |
| 7 | MetaMorpho (Morpho Vaults) | Sum across market accumulators in `totalAssets()` | MEDIUM -- multi-market overkill |
| 8 | Balancer Rate Providers | `IRateProvider.getRate()` single-function oracle | HIGH -- cleanest observable abstraction |
| 9 | Sommelier Cellar Adaptors | `adaptor.balanceOf()` per-position yield | MEDIUM -- multi-strategy overkill |
| 10 | Bunni V2 | ERC-4626 wrapping Uniswap V4 fee growth accumulators | HIGH -- structurally identical problem |
| 11 | Angle Protocol staked tokens | Linear time-weighted accumulator | LOW-MEDIUM |
| 12 | ERC-7575 Multi-Asset Vaults | Separate share token from vault logic | LOW |
| 13 | Arrakis V2 / PALM | Multi-range LP vault with fee accumulator reads | MEDIUM |

## Architecture Decision Matrix

| Approach | Gas on Read | Complexity | Composability | Best For |
|----------|------------|------------|---------------|----------|
| Override `totalAssets()` on Solady/OZ base | Medium (live read) | Low | High | Simple single-accumulator |
| Panoptic CollateralTracker extension | Low (cached + accumulator) | High | Medium | Full margin vault with interest |
| Yearn-style harvest | Low (cached) | Medium | High | Periodic reporting, keeper-based |
| Balancer IRateProvider | Low (rate lookup) | Low | Very High | When vault consumed by other protocols |

## Key Considerations

1. Q128.128 to token-unit conversion: Angstrom accumulators are Q128.128. X128MathLib handles this.
2. Snapshot vs live read: Live is more accurate but more gas. For ERC-4626 integrators, live is safer.
3. Tick range dependency: growthInside depends on (poolId, tickLower, tickUpper). Vault must commit to range or support multiple.
4. License: Panoptic CT is BUSL-1.1. Bunni is BSL-1.1. OZ/Solady are MIT (safest).
5. The NoteSnapshot + AccrualManagerMod code already in this repo is ~80% of what a vault needs.

## Relevant Files in Codebase

- `contracts/src/ran.sol` -- AngstromRANOracleAdapter (accumulator read layer)
- `contracts/src/modules/AccrualManagerMod.sol` -- Checkpoint + settle logic
- `contracts/src/types/PoolRewards.sol` -- globalGrowth + growthOutside structure
- `contracts/src/types/NoteSnapshot.sol` -- Per-note accumulator snapshots
- `contracts/lib/2025-12-panoptic/contracts/CollateralTracker.sol` -- Closest production pattern
- `contracts/lib/solady/src/tokens/ERC4626.sol` -- Recommended base class
