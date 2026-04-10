# Dune Analytics — Angstrom Tables Research

Date: 2026-04-10

## Summary

**No usable Dune infrastructure exists for Angstrom accumulator data.**

## Findings

1. **Sorella Labs Dune Profile** (`dune.com/sorellalabs`): zero dashboards, zero queries
2. **Decoded tables**: None. No ABI submitted → no `angstrom_ethereum.Angstrom_evt_*` tables. Even if submitted, tables would be empty (no events emitted).
3. **Raw traces**: `ethereum.traces` can show `execute()` calls but cannot reconstruct storage state changes for `globalGrowth`
4. **Storage values**: NOT directly accessible in Dune's query engine

## What Dune CAN Show (if ABI registered)

- Hook function call frequency and patterns
- Gas usage per `execute()` call
- Hook-to-PoolManager interaction traces
- Fund flows via call data analysis

## What Dune CANNOT Show

- `globalGrowth` values (storage, not events)
- Reward distributions
- Accumulator state snapshots
- Order matching results
- Bundle creation details
