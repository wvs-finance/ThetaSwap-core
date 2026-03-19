# Design: Dune MCP Data Extraction for LP Insurance Demand

## Context

Replaces the BigQuery-based pipeline in `2026-03-05-data-pipeline-plan.md`. Dune MCP provides pre-decoded Uniswap V3 event tables, eliminating manual hex decoding and enabling SQL-first computation.

## Decisions

| Decision | Choice |
|---|---|
| Data source | Dune MCP (pre-decoded tables) |
| Budget | 2,500 credits/month free tier (~80 credits estimated usage) |
| Computation split | SQL does JIT classification, lifecycle matching, A_T, panel assembly; Python does estimation only |
| Estimation framework | JAX 0.9.1 (custom logit MLE via autodiff) |
| A_T approximation | Equal-share: `A_T = sqrt(sum(1/blocklife_k)) / N` |
| Pool | ETH/USDC 30bps `0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8` |
| Window | 3 months via `evt_block_date` filter |

## Architecture

```
Dune MCP (DuneSQL)          Python (JAX)
─────────────────          ──────────────
Q1: Gate check (1 row)  →  Pass/fail decision
Q2: Daily panel (90 rows) → ingest.py → estimate.py → EstimationResult
Q3: JIT instrument (90 rows) ↗
Q4: Position-level (optional, 2000 rows) → robustness check
```

## Dune Tables Used

| Table | Columns Used |
|---|---|
| `uniswap_v3_ethereum.uniswapv3pool_evt_mint` | contract_address, evt_tx_hash, evt_block_number, evt_block_date, evt_index, owner, tickLower, tickUpper, amount, amount0, amount1 |
| `uniswap_v3_ethereum.uniswapv3pool_evt_burn` | contract_address, evt_tx_hash, evt_block_number, evt_block_date, evt_index, owner, tickLower, tickUpper, amount, amount0, amount1 |
| `uniswap_v3_ethereum.uniswapv3pool_evt_swap` | contract_address, evt_tx_hash, evt_block_number, evt_block_date, evt_index, amount0, amount1, sqrtPriceX96, liquidity, tick |

## Query Design

### Q1: Gate Check (~0.15 credits)

Validates JIT count >= 50 in the 3-month window. Single row output.

```sql
WITH pool_mints AS (
    SELECT evt_tx_hash, owner, tickLower, tickUpper
    FROM uniswap_v3_ethereum.uniswapv3pool_evt_mint
    WHERE contract_address = 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
      AND evt_block_date >= CURRENT_DATE - INTERVAL '90' DAY
),
pool_burns AS (
    SELECT evt_tx_hash, owner, tickLower, tickUpper
    FROM uniswap_v3_ethereum.uniswapv3pool_evt_burn
    WHERE contract_address = 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
      AND evt_block_date >= CURRENT_DATE - INTERVAL '90' DAY
),
jit_txs AS (
    SELECT DISTINCT m.evt_tx_hash
    FROM pool_mints m
    INNER JOIN pool_burns b
        ON m.evt_tx_hash = b.evt_tx_hash
        AND m.owner = b.owner
        AND m.tickLower = b.tickLower
        AND m.tickUpper = b.tickUpper
)
SELECT
    COUNT(*) AS jit_tx_count,
    (SELECT COUNT(*) FROM pool_mints) AS total_mints,
    (SELECT COUNT(*) FROM pool_burns) AS total_burns
FROM jit_txs
```

Gate: `jit_tx_count >= 50` to proceed.

### Q2: Daily Panel (~1-3 credits)

Full CTE chain: JIT classification -> lifecycle matching (FIFO via ROW_NUMBER) -> daily A_T -> daily panel.

```sql
WITH pool_mints AS (
    SELECT evt_tx_hash, evt_block_number, evt_block_date, evt_index,
           owner, tickLower, tickUpper, amount,
           ROW_NUMBER() OVER (
               PARTITION BY owner, tickLower, tickUpper
               ORDER BY evt_block_number, evt_index
           ) AS seq
    FROM uniswap_v3_ethereum.uniswapv3pool_evt_mint
    WHERE contract_address = 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
      AND evt_block_date >= CURRENT_DATE - INTERVAL '90' DAY
),
pool_burns AS (
    SELECT evt_tx_hash, evt_block_number, evt_block_date, evt_index,
           owner, tickLower, tickUpper, amount,
           ROW_NUMBER() OVER (
               PARTITION BY owner, tickLower, tickUpper
               ORDER BY evt_block_number, evt_index
           ) AS seq
    FROM uniswap_v3_ethereum.uniswapv3pool_evt_burn
    WHERE contract_address = 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
      AND evt_block_date >= CURRENT_DATE - INTERVAL '90' DAY
),
lifecycles AS (
    SELECT
        m.owner,
        m.tickLower,
        m.tickUpper,
        m.evt_block_number AS mint_block,
        b.evt_block_number AS burn_block,
        b.evt_block_date AS burn_date,
        b.evt_block_number - m.evt_block_number + 1 AS blocklife,
        (m.evt_tx_hash = b.evt_tx_hash) AS is_jit
    FROM pool_mints m
    JOIN pool_burns b
        ON m.owner = b.owner
        AND m.tickLower = b.tickLower
        AND m.tickUpper = b.tickUpper
        AND m.seq = b.seq
    WHERE b.evt_block_number >= m.evt_block_number
),
daily_a_t AS (
    SELECT
        burn_date AS day,
        SQRT(SUM(1.0 / blocklife)) / COUNT(*) AS a_t,
        COUNT(*) AS total_positions,
        COUNT(*) FILTER (WHERE is_jit) AS jit_count,
        COUNT(*) FILTER (WHERE NOT is_jit) AS passive_exit_count
    FROM lifecycles
    GROUP BY burn_date
),
daily_swaps AS (
    SELECT
        evt_block_date AS day,
        COUNT(*) AS swap_count
    FROM uniswap_v3_ethereum.uniswapv3pool_evt_swap
    WHERE contract_address = 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
      AND evt_block_date >= CURRENT_DATE - INTERVAL '90' DAY
    GROUP BY evt_block_date
)
SELECT
    a.day,
    a.a_t,
    a.passive_exit_count,
    a.total_positions,
    a.jit_count,
    COALESCE(s.swap_count, 0) AS swap_count
FROM daily_a_t a
LEFT JOIN daily_swaps s ON a.day = s.day
ORDER BY a.day
```

### Q3: Daily JIT Instrument (~0.5 credits)

Lagged JIT count for IV. Computed from Q2 output via LAG() or separately.

```sql
WITH jit_daily AS (
    SELECT evt_block_date AS day, COUNT(DISTINCT m.evt_tx_hash) AS jit_count
    FROM uniswap_v3_ethereum.uniswapv3pool_evt_mint m
    INNER JOIN uniswap_v3_ethereum.uniswapv3pool_evt_burn b
        ON m.evt_tx_hash = b.evt_tx_hash
        AND m.owner = b.owner
        AND m.tickLower = b.tickLower
        AND m.tickUpper = b.tickUpper
    WHERE m.contract_address = 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
      AND m.evt_block_date >= CURRENT_DATE - INTERVAL '91' DAY
    GROUP BY evt_block_date
)
SELECT
    day,
    jit_count,
    LAG(jit_count, 1, 0) OVER (ORDER BY day) AS jit_count_lag1
FROM jit_daily
WHERE day >= CURRENT_DATE - INTERVAL '90' DAY
ORDER BY day
```

### Q4: Position-Level Panel (optional, ~2-5 credits)

Only run if Gate 3 passes. Outputs individual LP exit events for robustness.

Same CTE chain as Q2 but outputs per-lifecycle rows instead of daily aggregates. ~2,000 rows, requires pagination (20 calls at 100 rows/batch).

## Python Files

### `econometrics/types.py`

Frozen dataclasses: `DailyPanelRow`, `EstimationResult`. Constants for pool address.

### `econometrics/ingest.py`

Single pure function: Dune MCP JSON rows -> JAX arrays (a_t, exit, swap_count, jit_lag).

### `econometrics/estimate.py`

JAX logit MLE:
- `nll(params, X, y)` — negative log-likelihood
- `structural_logit(exit, a_t, jit_lag, swap_count)` — full estimation
- SEs via `jax.hessian(nll)` -> inverse diagonal
- p-values via `jax.scipy.stats.norm.sf`
- WTP: `beta_3 * E[A_T] * FeeRevenue`

### `tests/econometrics/test_estimate.py`

Synthetic data: verify beta_3 > 0 when A_T drives exit.

## Progressive Gates

| Gate | Query | Condition | Fail Action |
|------|-------|-----------|-------------|
| G1: JIT existence | Q1 | jit_tx_count >= 50 | Switch to 5bps pool |
| G2: Raw pattern | Q2 | Visual positive A_T vs exit | Publishable null |
| G3: Significance | Python | beta_3 > 0, p < 0.05 | Expand window or revise spec |

## Credit Budget

| Phase | Est. Credits | Cumulative |
|-------|-------------|-----------|
| Development/debug (~20 iterations) | 30-50 | 50 |
| Final extraction (Q1-Q3) | 5 | 55 |
| Q4 robustness (if needed) | 5 | 60 |
| Alternative specs | 20 | 80 |
| **Remaining buffer** | **2,420** | 2,500 |

## Dropped from Original Plan

- `decode.py` — Dune pre-decodes events
- `extract.py` — SQL strings live as Dune saved queries
- `jit.py` — JIT classification in SQL
- `concentration.py` — A_T computed in SQL
- `panel.py` — Panel assembled in SQL
- `pipeline.py` — No orchestration needed
- `run_extraction.py` — No runbook needed

## Dependencies

- JAX 0.9.1 CPU (installed in uhi8 venv)
- Dune MCP (installed, HTTP transport)
- Python 3.14 (uhi8 venv)

## Upstream Spec

`specs/econometrics/lp-insurance-demand.tex`
