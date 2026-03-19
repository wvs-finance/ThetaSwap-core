# Design: Progressive Data Acquisition for LP Insurance Demand

## Decisions

| Decision | Choice |
|---|---|
| Budget | $0 — free tier only |
| Protocol | Uniswap V3 (most JIT activity, 4+ years history) |
| Pool (pilot) | ETH/USDC 30bps (`0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8`) |
| Data source | Google BigQuery `bigquery-public-data.crypto_ethereum.logs` |
| Progressive gates | Tier 1: JIT variation → Tier 2: raw pattern → Tier 3: regression → Tier 4: expansion |
| Go/no-go | All three gates progressively before expanding |

## Pool Rationale

ETH/USDC 30bps is the sweet spot for a pilot:
- High volume (second-highest V3 pool)
- Moderate JIT presence (more variation than 5bps where JIT is always present)
- Enough passive LP entry/exit events for discrete choice estimation
- Well within BigQuery free tier for full history

## Source: Google BigQuery

`bigquery-public-data.crypto_ethereum.logs` contains all Ethereum event logs.

- Free up to 1TB/month processing
- Raw `Mint`, `Burn`, `Swap` event logs with block numbers, tx hashes, log indices
- Full within-block ordering (log_index) — critical for JIT classification
- Single pool full history: ~50-100GB, comfortably within free tier

## Progressive Tiers

### Tier 1: JIT Variation Check

**Purpose**: Verify the pool has enough JIT activity to identify from.

- **Window**: 3 months (most recent)
- **Extract**: `Mint` + `Burn` events for pool address
- **Compute**: JIT classification — same-block mint+burn per address (blocklife = 1)
- **Gate**: ≥ 50 distinct JIT entry events across the window
- **Cost**: ~5-10 GB BigQuery processing
- **Fail action**: Try ETH/USDC 5bps instead

### Tier 2: Raw Pattern Check

**Purpose**: Visual evidence before any regression.

- **Extend**: Add passive LP exit events with timestamps
- **Compute**: A_T approximation from fee share ratios (swap volume proxy)
- **Plot**: Scatter of exit rate vs A_T bins
- **Gate**: Visible upward slope, monotone relationship
- **Cost**: ~10-20 GB additional
- **Fail action**: Null result — still publishable as "concentration risk does not drive LP exit"

### Tier 3: Regression-Ready Dataset

**Purpose**: Full structural estimation.

- **Window**: Expand to 12 months (or full history if within free tier)
- **Add events**: Swaps (fee revenue), block-level ETH prices (IL), gas prices (base fee)
- **Compute**: Exact A_T from feeGrowthInside reconstruction OR validated approximation
- **Controls**: DeFi yield index from Aave/Compound public subgraphs (outside option proxy)
- **Run**: Structural logit with JIT entry IV
- **Cost**: ~50-100 GB total
- **Fail action**: β₃ not significant → need more data or different specification

### Tier 4: Expansion

**Purpose**: Robustness and generalizability.

- **Add pools**: ETH/USDC 5bps (cross-tier), WBTC/ETH 30bps (cross-pair)
- **Extend window**: Full pool history
- **Run**: Alternative specifications (lagged A_T IV, nested LR test, reduced-form comparison)

## Data Pipeline

```
BigQuery (raw logs)
  → Python extraction scripts (SQL queries)
    → Parquet files (local, ~100MB-1GB)
      → Position lifecycle reconstruction
        → JIT classification (blocklife = 1)
        → A_T computation per event
          → Panel dataset: (LP_i, pool_j, event_t, Y, A_T, FeeRev, IL, Gas)
            → Structural logit estimation
```

## Key Events (BigQuery topics)

| Event | Signature | Fields needed |
|---|---|---|
| Mint | `0x7a53080b...` | sender, owner, tickLower, tickUpper, amount, amount0, amount1 |
| Burn | `0x0c396cd9...` | owner, tickLower, tickUpper, amount, amount0, amount1 |
| Swap | `0xc42079f9...` | sender, recipient, amount0, amount1, sqrtPriceX96, liquidity, tick |

## feeGrowthInside Strategy

1. **Pilot (Tier 2)**: Approximate — `(position liquidity share) × (total swap volume × fee rate)`
2. **Validation**: Compute exact feeGrowthInside on 1-week subsample, check correlation with approximation
3. **Full (Tier 3)**: Use approximation if r > 0.95, else reconstruct exact from tick-level accounting

## Exit Criteria

| Tier | Fail condition | Action |
|---|---|---|
| 1 | < 50 JIT events | Switch to ETH/USDC 5bps |
| 2 | No visible pattern | Publishable null — "no evidence of concentration-driven exit" |
| 3 | β₃ not significant | Expand data (Tier 4) or revise specification |

## Upstream Dependency

This data pipeline feeds into the structural econometric specification at `specs/econometrics/lp-insurance-demand.tex`.
