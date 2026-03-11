-- Dune Query: V3 events for FCI shadow oracle
-- Pool: ETH/USDC 500bps (0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640)
-- Parameterized: {{block_start}}, {{block_end}}

WITH swaps AS (
  SELECT
    'Swap' AS event_type,
    evt_block_number AS block_number,
    evt_tx_hash AS tx_hash,
    evt_index AS log_index,
    NULL AS owner,
    NULL AS tickLower,
    NULL AS tickUpper,
    NULL AS liquidity,
    CAST(amount0 AS varchar) AS amount0,
    CAST(amount1 AS varchar) AS amount1,
    NULL AS fee_amount0,
    NULL AS fee_amount1,
    tick AS swap_tick
  FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Swap
  WHERE contract_address = 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
    AND evt_block_number BETWEEN {{block_start}} AND {{block_end}}
),
mints AS (
  SELECT
    'Mint' AS event_type,
    evt_block_number AS block_number,
    evt_tx_hash AS tx_hash,
    evt_index AS log_index,
    CAST(owner AS varchar) AS owner,
    tickLower,
    tickUpper,
    CAST(amount AS varchar) AS liquidity,
    CAST(amount0 AS varchar) AS amount0,
    CAST(amount1 AS varchar) AS amount1,
    NULL AS fee_amount0,
    NULL AS fee_amount1,
    NULL AS swap_tick
  FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Mint
  WHERE contract_address = 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
    AND evt_block_number BETWEEN {{block_start}} AND {{block_end}}
),
burns AS (
  SELECT
    'Burn' AS event_type,
    evt_block_number AS block_number,
    evt_tx_hash AS tx_hash,
    evt_index AS log_index,
    CAST(owner AS varchar) AS owner,
    tickLower,
    tickUpper,
    CAST(amount AS varchar) AS liquidity,
    CAST(amount0 AS varchar) AS amount0,
    CAST(amount1 AS varchar) AS amount1,
    NULL AS fee_amount0,
    NULL AS fee_amount1,
    NULL AS swap_tick
  FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Burn
  WHERE contract_address = 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
    AND evt_block_number BETWEEN {{block_start}} AND {{block_end}}
),
collects AS (
  SELECT
    'Collect' AS event_type,
    evt_block_number AS block_number,
    evt_tx_hash AS tx_hash,
    evt_index AS log_index,
    CAST(owner AS varchar) AS owner,
    tickLower,
    tickUpper,
    NULL AS liquidity,
    NULL AS amount0,
    NULL AS amount1,
    CAST(amount0 AS varchar) AS fee_amount0,
    CAST(amount1 AS varchar) AS fee_amount1,
    NULL AS swap_tick
  FROM uniswap_v3_ethereum.UniswapV3Pool_evt_Collect
  WHERE contract_address = 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
    AND evt_block_number BETWEEN {{block_start}} AND {{block_end}}
)
SELECT * FROM swaps
UNION ALL SELECT * FROM mints
UNION ALL SELECT * FROM burns
UNION ALL SELECT * FROM collects
ORDER BY block_number, log_index
