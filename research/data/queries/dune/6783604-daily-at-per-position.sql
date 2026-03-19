-- Dune Query 6783604: Daily A_T Per Position (ETH/USDC 30bps)
--
-- Source: https://dune.com/queries/6783604
-- Purpose: Compute real A_T and null A_T per day from position-level
--          Collect fees joined with Burn+Mint events. Used for the
--          exit hazard duration model that calibrates Delta* ≈ 0.09.
--
-- Pool: ETH/USDC 30bps (0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8)
-- Window: 2025-12-05 to 2026-01-14 (41 days)
--
-- Used in: econometrics/data.py (DAILY_AT_MAP, DAILY_AT_NULL_MAP)
-- Notebook: econometrics/run_duration.py
-- Data frozen: 2026-03-05
-- Cost: ~0.386 credits

-- Compute real A_T and null A_T per day from the SAME position set
-- Real: A_T = sqrt(sum(theta_k * x_k^2)) with actual fee shares
-- Null: A_T = sqrt(sum(theta_k) / N^2) with equal shares x_k = 1/N
-- Pool: ETH/USDC 30bps (token0=USDC 6dec, token1=WETH 18dec)
WITH position_fees AS (
  SELECT
    CAST(c.evt_block_time AS date) AS collect_date,
    GREATEST(CAST(c.amount0 AS double) - CAST(b.amount0 AS double), 0) / 1e6 AS fee_usdc,
    GREATEST(CAST(c.amount1 AS double) - CAST(b.amount1 AS double), 0) / 1e18 AS fee_eth,
    CAST(b.evt_block_number AS bigint) - CAST(m.evt_block_number AS bigint) AS blocklife
  FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Collect c
  INNER JOIN uniswap_v3_ethereum.UniswapV3Pool_evt_Burn b
    ON c.evt_tx_hash = b.evt_tx_hash
    AND c.contract_address = b.contract_address
    AND c.tickLower = b.tickLower
    AND c.tickUpper = b.tickUpper
  INNER JOIN (
    SELECT sender, tickLower, tickUpper, contract_address,
           MAX(evt_block_number) AS evt_block_number
    FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Mint
    WHERE contract_address = 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
    GROUP BY sender, tickLower, tickUpper, contract_address
  ) m
    ON b.owner = m.sender
    AND b.tickLower = m.tickLower
    AND b.tickUpper = m.tickUpper
    AND b.contract_address = m.contract_address
    AND m.evt_block_number < b.evt_block_number
  WHERE c.contract_address = 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
    AND c.evt_block_time >= TIMESTAMP '2025-12-05'
    AND c.evt_block_time <= TIMESTAMP '2026-01-14 23:59:59'
),
day_totals AS (
  SELECT
    collect_date,
    SUM(fee_usdc + fee_eth * 3500.0) AS total_fee,
    COUNT(*) AS n_positions,
    SUM(1.0 / CAST(blocklife AS double)) AS sum_theta
  FROM position_fees
  WHERE (fee_usdc + fee_eth * 3500.0) > 0
    AND blocklife > 0
  GROUP BY collect_date
)
SELECT
  dt.collect_date,
  dt.n_positions,
  dt.total_fee,
  dt.sum_theta,
  -- Real A_T (Eq. 1 with actual fee shares)
  SQRT(SUM(
    (1.0 / CAST(pf.blocklife AS double)) * POWER((pf.fee_usdc + pf.fee_eth * 3500.0) / dt.total_fee, 2)
  )) AS a_t_real,
  -- Null A_T (Ma & Crapis equal-share: x_k = 1/N)
  SQRT(dt.sum_theta / POWER(CAST(dt.n_positions AS double), 2)) AS a_t_null
FROM position_fees pf
INNER JOIN day_totals dt ON pf.collect_date = dt.collect_date
WHERE (pf.fee_usdc + pf.fee_eth * 3500.0) > 0
  AND pf.blocklife > 0
GROUP BY dt.collect_date, dt.n_positions, dt.total_fee, dt.sum_theta
ORDER BY dt.collect_date
