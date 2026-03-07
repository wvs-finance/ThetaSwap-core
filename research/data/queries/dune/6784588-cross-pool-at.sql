-- Dune Query 6784588: Cross-Pool A_T — Aggregate Concentration Index
--
-- Source: https://dune.com/queries/6784588
-- Purpose: Compute A_T = sqrt(sum(theta_k * x_k^2)) for a given pool
--          over 90 days. Returns single row with A_T, A_T_null,
--          delta_plus, position count, removal count.
--
-- Parameters:
--   {{pool_address}} (text) — V3 pool contract address
--   Default: 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640 (USDC/WETH 500bps)
--
-- Used in: econometrics/cross_pool/data.py (results for 10 pools)
-- Notebook: notebooks/cross-pool-concentration-severity.ipynb
-- Data frozen: 2026-03-05 (90-day window)
-- Cost: ~0.3 credits per pool, ~3 credits total for 10 pools

-- Aggregate A_T computation for cross-pool severity analysis
-- A_T = sqrt(sum(theta_k * fee_share_k^2))
-- theta_k = 1 / blocklife_k
-- fee_share_k = position_fees_k / total_pool_fees
-- Parameters: pool_address (text)
WITH mints AS (
    SELECT
        owner,
        tickLower,
        tickUpper,
        MIN(evt_block_number) AS mint_block
    FROM uniswap_v3_ethereum.uniswapv3pool_evt_mint
    WHERE contract_address = {{pool_address}}
      AND evt_block_date >= CURRENT_DATE - INTERVAL '180' DAY
    GROUP BY owner, tickLower, tickUpper
),
burns AS (
    SELECT
        owner,
        tickLower,
        tickUpper,
        evt_block_number AS burn_block
    FROM uniswap_v3_ethereum.uniswapv3pool_evt_burn
    WHERE contract_address = {{pool_address}}
      AND evt_block_date >= CURRENT_DATE - INTERVAL '90' DAY
      AND (amount0 > UINT256 '0' OR amount1 > UINT256 '0')
),
collects AS (
    SELECT
        owner,
        tickLower,
        tickUpper,
        SUM(CAST(amount0 AS double)) + SUM(CAST(amount1 AS double)) AS pos_fees
    FROM uniswap_v3_ethereum.uniswapv3pool_evt_collect
    WHERE contract_address = {{pool_address}}
      AND evt_block_date >= CURRENT_DATE - INTERVAL '90' DAY
    GROUP BY owner, tickLower, tickUpper
),
positions AS (
    SELECT
        b.owner,
        b.tickLower AS tick_lower,
        b.tickUpper AS tick_upper,
        GREATEST(b.burn_block - COALESCE(m.mint_block, b.burn_block - 1), 1) AS blocklife,
        COALESCE(c.pos_fees, 0) AS pos_fees
    FROM burns b
    LEFT JOIN mints m
        ON b.owner = m.owner
        AND b.tickLower = m.tickLower
        AND b.tickUpper = m.tickUpper
    LEFT JOIN collects c
        ON b.owner = c.owner
        AND b.tickLower = c.tickLower
        AND b.tickUpper = c.tickUpper
),
total AS (
    SELECT SUM(pos_fees) AS pool_total_fees
    FROM positions
    WHERE pos_fees > 0
),
weighted AS (
    SELECT
        p.blocklife,
        CASE WHEN t.pool_total_fees > 0
             THEN p.pos_fees / t.pool_total_fees
             ELSE 0 END AS fee_share,
        1.0 / p.blocklife AS theta_k
    FROM positions p
    CROSS JOIN total t
    WHERE p.pos_fees > 0
)
SELECT
    COUNT(*) AS n_positions,
    (SELECT COUNT(*) FROM burns) AS n_removals,
    SUM(theta_k) AS theta_sum,
    SQRT(SUM(theta_k * fee_share * fee_share)) AS a_t,
    SQRT(SUM(theta_k) / (COUNT(*) * COUNT(*))) AS a_t_null,
    GREATEST(0,
        SQRT(SUM(theta_k * fee_share * fee_share))
        - SQRT(SUM(theta_k) / (COUNT(*) * COUNT(*)))
    ) AS delta_plus,
    AVG(blocklife) AS avg_blocklife,
    MIN(blocklife) AS min_blocklife,
    MAX(blocklife) AS max_blocklife
FROM weighted
