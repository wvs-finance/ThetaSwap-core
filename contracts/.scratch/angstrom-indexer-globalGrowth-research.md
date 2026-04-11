# Angstrom globalGrowth Indexing Research

Date: 2026-04-10
Contract: `0x0000000aa232009084bd71a5797d089aa4edfad4` (Sorella Labs: Angstrom Hook)

## Executive Summary

**No public indexer, subgraph, or API exposes Angstrom's `globalGrowth` accumulator.**

Sorella Labs has not published any Graph Protocol subgraph, Dune dashboard, Goldsky/Envio/Ponder integration, or data API that surfaces `poolRewards` storage values. The no-events design is intentional and universal — nothing in the Angstrom bundle execution path emits logs that could reconstruct `globalGrowth` indirectly. Direct storage slot reads via an archive RPC (`eth_getStorageAt`) are the only viable path today.

## Verdict Table

| Source | Available | Notes |
|--------|-----------|-------|
| The Graph subgraph | No | No subgraph deployed; no events to index |
| Dune Analytics | No | No decoded tables; no event logs |
| Goldsky | No | Event-driven; same structural blocker |
| Envio HyperIndex | No | No public Angstrom deployment |
| Ponder | No | No public Angstrom deployment |
| Shadow (shadow-reth) | No public deployment | Feasible prospectively; zero historical coverage |
| Brontes | No public API | Internal Sorella tool only |
| Angstrom node RPC | Not applicable | Order submission, not accumulator history |

## Root Cause

Angstrom emits **zero events** by design. The `execute()` entrypoint decodes a fully custom PADE-encoded binary blob, opaque to standard ABI-based subgraph decoders. `Angstrom.sol` has zero `emit` statements. The storage mutation is invisible to every log-based indexer.

The only on-chain surface area for `globalGrowth` is:
1. `extsload(uint256 slot)` — a live point-in-time read
2. `eth_getStorageAt` — requires an archive node; provides historical state

## Storage Slot Derivation (Confirmed)

```
POOL_REWARDS_SLOT = 7
base = keccak256(abi.encode(poolId, 7))
globalGrowth_slot = base + 16777216  (2^24, the REWARD_GROWTH_SIZE offset)
```

Confirmed by `AngstromAccumulatorConsumer.sol` using `SlotDerivation.offset(REWARD_GROWTH_SIZE)`.

## Dune Specifics

- Sorella Labs Dune profile (`dune.com/sorellalabs`): zero dashboards, zero queries
- No decoded tables exist for the Angstrom hook address
- Even if ABI were submitted, event tables would be empty (no events)
- Raw `ethereum.traces` can show execution but cannot reconstruct accumulator state

## Shadow (Prospective Only)

Shadow-reth could capture `globalGrowth` on every `execute()` call via custom "shadow events" without gas cost. However:
- No public Shadow deployment for Angstrom exists
- Requires a full Reth archive node with ExEx plugin
- Only works prospectively — does not cover blocks back to 22,972,937

## Conclusion

**`eth_getStorageAt` via archive RPC is the only viable method for historical per-block `globalGrowth` values.** This is a direct consequence of Angstrom's deliberate no-events architecture. The Python data pipeline must use the storage-slot approach with an archive RPC provider (Alchemy, confirmed in foundry.toml).
