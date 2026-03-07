-- FCI Fork Test: WETH/USDC V4 Event Stream
-- Pool ID: 0x4f88f7c99022eace4740c6898f59ce6a2e798a1e64ce54589720b7153eb224a7
-- Pool: WETH/USDC 5bps on Uniswap V4 Ethereum mainnet
-- Block range: 23656000-23668000 (dense lifecycle region)
-- Dune query ID: 6795594
--
-- Discovery query (bucket analysis): 6795601
-- ModifyLiquidity-only query: 6795602

-- Query 1: Balanced event stream — all non-zero ModifyLiquidity + sampled swaps
WITH liq_events AS (
    SELECT
        evt_block_number as block_number,
        evt_tx_hash as tx_hash,
        CAST(evt_index AS BIGINT) as log_index,
        'ModifyLiquidity' as event_type,
        sender,
        tickLower as tick_lower,
        tickUpper as tick_upper,
        liquidityDelta as liquidity_delta,
        salt,
        CAST(NULL AS INTEGER) as swap_tick,
        CAST(NULL AS uint256) as swap_sqrtPriceX96,
        1 as priority
    FROM uniswap_v4_ethereum.poolmanager_evt_modifyliquidity
    WHERE id = 0x4f88f7c99022eace4740c6898f59ce6a2e798a1e64ce54589720b7153eb224a7
      AND evt_block_number BETWEEN 23656000 AND 23668000
      AND liquidityDelta != 0
),
swap_ranked AS (
    SELECT
        evt_block_number as block_number,
        evt_tx_hash as tx_hash,
        CAST(evt_index AS BIGINT) as log_index,
        'Swap' as event_type,
        sender,
        CAST(NULL AS INTEGER) as tick_lower,
        CAST(NULL AS INTEGER) as tick_upper,
        CAST(NULL AS int256) as liquidity_delta,
        CAST(NULL AS varbinary) as salt,
        tick as swap_tick,
        sqrtPriceX96 as swap_sqrtPriceX96,
        2 as priority,
        ROW_NUMBER() OVER (
            PARTITION BY (evt_block_number / 200)
            ORDER BY evt_block_number ASC, evt_index ASC
        ) as rn
    FROM uniswap_v4_ethereum.poolmanager_evt_swap
    WHERE id = 0x4f88f7c99022eace4740c6898f59ce6a2e798a1e64ce54589720b7153eb224a7
      AND evt_block_number BETWEEN 23656000 AND 23668000
),
swap_events AS (
    SELECT block_number, tx_hash, log_index, event_type, sender,
           tick_lower, tick_upper, liquidity_delta, salt,
           swap_tick, swap_sqrtPriceX96, priority
    FROM swap_ranked
    WHERE rn = 1
),
all_events AS (
    SELECT * FROM liq_events
    UNION ALL
    SELECT * FROM swap_events
)
SELECT block_number, tx_hash, log_index, event_type, sender,
       tick_lower, tick_upper, liquidity_delta, salt,
       swap_tick, swap_sqrtPriceX96
FROM all_events
ORDER BY block_number ASC, log_index ASC;
