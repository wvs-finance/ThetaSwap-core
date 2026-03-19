# Cross-Pool Fee Concentration Severity Analysis — Design

## Decision This Resolves

The insurance architecture (CFMM pool vs hook mutual insurance vs hybrid) depends on
whether fee concentration correlates with pool size. If large pools have mild
concentration and small pools have severe concentration, then pools needing insurance
most cannot support a market-based solution — hook insurance wins.

## Literature Grounding

Pool selection follows Aquilina et al. (2024) "Decentralised Dealers" — top pools by
TVL, stratified by pair category:

| Paper | Method | Pools |
|-------|--------|-------|
| Aquilina et al. (2024) | Top 250 by TVL | All V3 fee tiers, Ethereum |
| Capponi & Zhu (2024) | Top 3 WETH/stablecoin | V2, Ethereum |
| Bichuch & Feinstein (2024) | Highest-volume V3 pool | WETH/USDC 5bps |

Aquilina identifies three pool categories: stable/stable (4%), stable/token (47%),
token/token (49%). JIT activity concentrates in pools with >$10M daily volume and
low fee tiers.

## Pool Selection

**10 pools, 2-4-4 stratification:**

| Category | Count | Examples |
|----------|-------|---------|
| Stable/stable | 2 | USDC/USDT, USDC/DAI |
| Stable/token | 4 | ETH/USDC (5bps, 30bps), WBTC/USDC, stablecoin/mid-cap |
| Token/token | 4 | ETH/WBTC, LINK/ETH, UNI/ETH, mid-cap/mid-cap |

Final pool addresses determined by V3 subgraph TVL ranking at query time.

## Data Pipeline

### Tier 1: V3 Subgraph (free)

- Endpoint: `https://gateway.thegraph.com/api/{GRAPH_API_KEY}/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV`
- Query: top pools by `totalValueLockedUSD`, with token symbols, fee tier, volume
- Purpose: pool discovery + metadata + TVL/volume for regression

### Tier 2: Dune MCP (~100-150 credits)

- Query: `Collect` events per pool for 90-day window
- Fields: pool address, owner, tickLower, tickUpper, amount0, amount1, block_number, block_time
- Purpose: position-level fee data to compute A_T
- One query per pool (~10 credits each)

## A_T Computation

Reuse existing logic from `specs/econometrics/`:

```
A_T = sqrt(sum(theta_k * x_k^2))
```

Where:
- x_k = feeGrowthInside(position_k) / feeGrowth(tickRange) — fee share
- theta_k = 1 / blocklife_k — sophistication weight
- blocklife_k = block(removal) - block(creation)

For cross-pool comparison, compute A_T over the full 90-day window per pool
(single aggregate measure, not daily).

## Analysis

1. **Pool metadata table**: address, pair, fee tier, TVL, volume, category, A_T, A_T_null, delta_plus
2. **Scatter plots**: A_T vs log(TVL), A_T vs log(volume), colored by pair category
3. **Correlation**: Spearman rank correlation (robust to outliers with n=10)
4. **Visual architecture decision**: if A_T decreases with TVL, annotate the plot with "hook insurance zone" vs "CFMM viable zone"

With n=10, formal regression is underpowered. Visual + rank correlation is the appropriate method.

## Architecture Decision Matrix

| Finding | Implication | Architecture |
|---------|------------|-------------|
| A_T negatively correlated with TVL | Small pools need insurance but can't support underwriters | Hook mutual insurance |
| A_T uncorrelated with TVL | Concentration is universal; market solution viable everywhere | CFMM pool or hybrid |
| A_T positively correlated with TVL | Large pools need insurance and can support it | CFMM pool |

## Tech Stack

- Python 3.12, JAX 0.9.1, uhi8 venv
- httpx for V3 subgraph queries
- Dune MCP for Collect event queries
- matplotlib for plots
- Jupyter notebook for results

## Constraints

- ~2488 Dune credits remaining; budget ~150 for this analysis
- .gitignore has `*.py` — use `git add -f` for Python files
- .env contains GRAPH_API_KEY (already gitignored)

## Output

`notebooks/cross-pool-concentration-severity.ipynb`
