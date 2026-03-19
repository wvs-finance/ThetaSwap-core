-- ThetaSwap FCI: Lifetime Fees (all Collects - all Decreases) Dec 20-26 2025
-- Dune Query ID: 6815916
-- Execution ID: 01KKFB8WHX57FX0G5PG0QB0HWJ
-- Cost: 0.111 credits
--
-- Tracks ALL Collect and DecreaseLiquidity events across each position's
-- full lifetime. fee = SUM(all_collects) - SUM(all_decreases).
-- This captures fees collected in SEPARATE transactions before the burn,
-- which the exit-only query (6815901) missed for 54% of positions.
--
-- fee_share_x_k = lifetime_fee_usdc / pool_daily_swap_fee_usdc
-- where pool daily fees are computed from 0.3% of Swap event input volume.
--
-- Result: x_k values now range from 0 to 0.548 (vs max 0.017 from total-value proxy).
-- 15/50 positions still show 0 (very short-lived JIT positions with no measurable USDC fees).

WITH
-- Pool-level burns at ETH/USDC 0.3%, Dec 20-26
pool_burns AS (
    SELECT
        b.evt_tx_hash,
        b.evt_block_number,
        b.evt_block_time,
        DATE(b.evt_block_time) as burn_date
    FROM uniswap_v3_ethereum.uniswapv3pool_evt_burn b
    WHERE b.contract_address = 0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8
    AND b.evt_block_date BETWEEN DATE '2025-12-20' AND DATE '2025-12-26'
    AND CAST(b.amount AS DOUBLE) > 0
),

-- Link to NFT tokenIds
nft_exits AS (
    SELECT
        d.tokenId as token_id,
        MAX(pb.evt_block_number) as burn_block,
        MAX(pb.evt_block_time) as burn_time,
        MAX(pb.burn_date) as burn_date
    FROM pool_burns pb
    JOIN uniswap_v3_ethereum.nonfungiblepositionmanager_evt_decreaseliquidity d
        ON pb.evt_tx_hash = d.evt_tx_hash
    WHERE d.evt_block_date BETWEEN DATE '2025-12-20' AND DATE '2025-12-26'
    GROUP BY d.tokenId
),

-- Mint block per position
mints AS (
    SELECT
        m.output_tokenId as token_id,
        MIN(m.call_block_number) as mint_block,
        MIN(m.call_block_date) as mint_date
    FROM uniswap_v3_ethereum.nonfungiblepositionmanager_call_mint m
    WHERE m.call_success = true
    AND m.output_tokenId IN (SELECT token_id FROM nft_exits)
    AND m.call_block_date >= DATE '2025-01-01'
    GROUP BY m.output_tokenId
),

-- ALL Collect events for these positions (full lifetime, from mint onwards)
lifetime_collects AS (
    SELECT
        c.tokenId as token_id,
        SUM(CAST(c.amount0 AS DOUBLE)) as total_collect_amount0,
        SUM(CAST(c.amount1 AS DOUBLE)) as total_collect_amount1,
        COUNT(*) as collect_count
    FROM uniswap_v3_ethereum.nonfungiblepositionmanager_evt_collect c
    WHERE c.tokenId IN (SELECT token_id FROM nft_exits)
    AND c.evt_block_date >= DATE '2025-01-01'
    GROUP BY c.tokenId
),

-- ALL DecreaseLiquidity events for these positions (full lifetime)
lifetime_decreases AS (
    SELECT
        d.tokenId as token_id,
        SUM(CAST(d.amount0 AS DOUBLE)) as total_decrease_amount0,
        SUM(CAST(d.amount1 AS DOUBLE)) as total_decrease_amount1,
        COUNT(*) as decrease_count
    FROM uniswap_v3_ethereum.nonfungiblepositionmanager_evt_decreaseliquidity d
    WHERE d.tokenId IN (SELECT token_id FROM nft_exits)
    AND d.evt_block_date >= DATE '2025-01-01'
    GROUP BY d.tokenId
),

-- Lifetime fees = total collects - total decreases
lifetime_fees AS (
    SELECT
        ne.token_id,
        ne.burn_block,
        ne.burn_time,
        ne.burn_date,
        m.mint_block,
        lc.collect_count,
        ld.decrease_count,
        GREATEST(0, COALESCE(lc.total_collect_amount0, 0) - COALESCE(ld.total_decrease_amount0, 0)) / 1e18 as lifetime_fee_eth,
        GREATEST(0, COALESCE(lc.total_collect_amount1, 0) - COALESCE(ld.total_decrease_amount1, 0)) / 1e6 as lifetime_fee_usdc
    FROM nft_exits ne
    JOIN mints m ON ne.token_id = m.token_id
    LEFT JOIN lifetime_collects lc ON ne.token_id = lc.token_id
    LEFT JOIN lifetime_decreases ld ON ne.token_id = ld.token_id
),

-- Total daily fees from Swap events (0.3% of input volume in USDC terms)
swap_daily_fees AS (
    SELECT
        DATE(s.evt_block_time) as day,
        SUM(
            CASE
                WHEN CAST(s.amount1 AS DOUBLE) > 0
                THEN CAST(s.amount1 AS DOUBLE) * 0.003
                WHEN CAST(s.amount0 AS DOUBLE) > 0
                THEN ABS(CAST(s.amount1 AS DOUBLE)) * 0.003
                ELSE 0
            END
        ) / 1e6 as total_swap_fee_usdc
    FROM uniswap_v3_ethereum.uniswapv3pool_evt_swap s
    WHERE s.contract_address = 0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8
    AND s.evt_block_date BETWEEN DATE '2025-12-20' AND DATE '2025-12-26'
    GROUP BY DATE(s.evt_block_time)
)

SELECT
    lf.token_id,
    lf.mint_block,
    lf.burn_block,
    lf.burn_time as burn_timestamp,
    CAST(lf.burn_date AS VARCHAR) as burn_date,
    (lf.burn_block - lf.mint_block) as block_lifetime,
    lf.collect_count,
    lf.decrease_count,
    lf.lifetime_fee_eth,
    lf.lifetime_fee_usdc,
    sdf.total_swap_fee_usdc as pool_daily_fee_usdc,
    CASE WHEN sdf.total_swap_fee_usdc > 0
         THEN lf.lifetime_fee_usdc / sdf.total_swap_fee_usdc
         ELSE 0.0
    END as fee_share_x_k
FROM lifetime_fees lf
LEFT JOIN swap_daily_fees sdf ON lf.burn_date = sdf.day
WHERE lf.mint_block < lf.burn_block
ORDER BY lf.burn_date, lf.burn_block
LIMIT 50
