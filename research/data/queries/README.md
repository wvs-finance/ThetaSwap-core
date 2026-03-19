# Data Queries

Reproducible queries backing all empirical results in the ThetaSwap fee concentration model. Reviewers can re-execute these to validate data.

## Subgraph Queries (`.graphql`)

| File | Endpoint | Purpose |
|------|----------|---------|
| `subgraph/pool-discovery.graphql` | Uniswap V3 Subgraph | Top 100 pools by TVL for cross-pool stratification |

## Dune Queries (`.sql`)

| File | Dune ID | Purpose | Pool(s) | Cost |
|------|---------|---------|---------|------|
| `dune/6784588-cross-pool-at.sql` | [6784588](https://dune.com/queries/6784588) | Aggregate A_T per pool (90-day window) | Parameterized: 10 pools | 0.31 credits/pool (~3.1 total) |
| `dune/6783604-daily-at-per-position.sql` | [6783604](https://dune.com/queries/6783604) | Daily A_T from position-level fees | ETH/USDC 30bps | 1.57 credits |

## Data Flow

```
subgraph/pool-discovery.graphql
  → econometrics/cross_pool/subgraph.py (select 10 pools, 2-4-4 stratification)
  → econometrics/cross_pool/data.py (SELECTED_POOLS)

dune/6784588-cross-pool-at.sql (×10 pools)
  → econometrics/cross_pool/data.py (POOL_CONCENTRATIONS)
  → notebooks/cross-pool-concentration-severity.ipynb (architecture decision)

dune/6783604-daily-at-per-position.sql
  → econometrics/data.py (DAILY_AT_MAP, DAILY_AT_NULL_MAP, RAW_POSITIONS)
  → econometrics/run_duration.py (exit hazard model → Δ* ≈ 0.09)
```

## Reproduction

**Subgraph:** Requires `GRAPH_API_KEY` env var. Free tier sufficient.

**Dune:** Requires Dune API key. Total reproduction cost: **~5 credits** (3.1 for 10× cross-pool + 1.57 for daily A_T + ~0.3 for per-position fees). Results are frozen in `econometrics/data.py` and `econometrics/cross_pool/data.py` — re-execution will produce different results due to new on-chain activity since the data freeze date (2026-03-05). Costs verified 2026-03-05.

## Frozen Data

Canonical JSON snapshots of all datasets live in `data/frozen/`. Each file has a `metadata` + `data` structure; SHA-256 is computed over the canonicalized `data` field only (sorted keys, no whitespace). See `data/frozen/README.md` for the full format description.

To verify all hashes: `uhi8/bin/python research/data/scripts/verify_provenance.py`

### Query ID Reference

| Dataset | Dune Query ID | Status |
|---------|--------------|--------|
| DAILY_AT_MAP + DAILY_AT_NULL_MAP | 6783604 | Verified |
| POOL_CONCENTRATIONS | 6784588 | Parameterized ×10 |
| PER_POSITION_DATA | 6815916 | Verified |
| FCI V4 events | 6795594 | Verified |
| RAW_POSITIONS (reconstruction) | 6847717 | Directional match |
| RAW_POSITIONS (original Q4v2) | Unknown | Lost |
| IL_MAP | N/A | Derived |
| SELECTED_POOLS | N/A | GraphQL subgraph |
