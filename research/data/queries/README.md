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

**Dune:** Requires Dune API key. Total reproduction cost: **~4.7 credits** (3.1 for 10× cross-pool + 1.57 for daily A_T). Results are frozen in `econometrics/data.py` and `econometrics/cross_pool/data.py` — re-execution will produce different results due to new on-chain activity since the data freeze date (2026-03-05). Costs verified 2026-03-05.
