-- ThetaSwap FCI: Per-Position FEES ONLY (ETH/USDC 0.3%, Dec 20-26 2025)
-- Dune Query ID: 6815901
-- Purpose: Refined version that isolates actual fee revenue from principal.
--          fee = Collect amounts - DecreaseLiquidity amounts (same tx).
--          Uses Swap events for daily fee denominator.
-- Note: Many positions show 0 fees because they collected fees in earlier
--       transactions (not at exit time). Use per_position_fee_shares_dec2025.sql
--       for the "total value proxy" version with better coverage.

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

-- NFT DecreaseLiquidity events linked to pool burns (principal amounts)
nft_decreases AS (
    SELECT
        d.tokenId as token_id,
        pb.evt_tx_hash,
        pb.evt_block_number as burn_block,
        pb.evt_block_time as burn_time,
        pb.burn_date,
        CAST(d.amount0 AS DOUBLE) as principal_amount0,
        CAST(d.amount1 AS DOUBLE) as principal_amount1
    FROM pool_burns pb
    JOIN uniswap_v3_ethereum.nonfungiblepositionmanager_evt_decreaseliquidity d
        ON pb.evt_tx_hash = d.evt_tx_hash
    WHERE d.evt_block_date BETWEEN DATE '2025-12-20' AND DATE '2025-12-26'
),

-- NFT Collect events from same tx (principal + fees)
nft_collects AS (
    SELECT
        c.tokenId as token_id,
        c.evt_tx_hash,
        CAST(c.amount0 AS DOUBLE) as collect_amount0,
        CAST(c.amount1 AS DOUBLE) as collect_amount1
    FROM uniswap_v3_ethereum.nonfungiblepositionmanager_evt_collect c
    WHERE c.evt_block_date BETWEEN DATE '2025-12-20' AND DATE '2025-12-26'
    AND c.tokenId IN (SELECT DISTINCT token_id FROM nft_decreases)
),

-- Fee = Collect - Decrease (per exit tx)
exit_fees AS (
    SELECT
        nd.token_id,
        nd.burn_block,
        nd.burn_time,
        nd.burn_date,
        nd.evt_tx_hash,
        GREATEST(0, nc.collect_amount0 - nd.principal_amount0) / 1e18 as fee_eth,
        GREATEST(0, nc.collect_amount1 - nd.principal_amount1) / 1e6 as fee_usdc
    FROM nft_decreases nd
    JOIN nft_collects nc
        ON nd.token_id = nc.token_id
        AND nd.evt_tx_hash = nc.evt_tx_hash
),

-- Aggregate per tokenId (take last exit if multiple decreases)
position_exits AS (
    SELECT
        token_id,
        MAX(burn_block) as burn_block,
        MAX(burn_time) as burn_time,
        MAX(burn_date) as burn_date,
        SUM(fee_eth) as total_fee_eth,
        SUM(fee_usdc) as total_fee_usdc
    FROM exit_fees
    GROUP BY token_id
),

-- Mint block per position
mints AS (
    SELECT
        m.output_tokenId as token_id,
        MIN(m.call_block_number) as mint_block
    FROM uniswap_v3_ethereum.nonfungiblepositionmanager_call_mint m
    WHERE m.call_success = true
    AND m.output_tokenId IN (SELECT token_id FROM position_exits)
    AND m.call_block_date >= DATE '2025-01-01'
    GROUP BY m.output_tokenId
),

-- Total daily fees from Swap events (0.3% of input volume)
swap_daily_fees AS (
    SELECT
        DATE(s.evt_block_time) as day,
        (
            SUM(CASE WHEN CAST(s.amount1 AS DOUBLE) > 0
                     THEN CAST(s.amount1 AS DOUBLE) * 0.003
                     ELSE 0 END)
            + SUM(CASE WHEN CAST(s.amount0 AS DOUBLE) > 0
                       THEN ABS(CAST(s.amount1 AS DOUBLE)) * 0.003
                       ELSE 0 END)
        ) / 1e6 as total_swap_fee_usdc
    FROM uniswap_v3_ethereum.uniswapv3pool_evt_swap s
    WHERE s.contract_address = 0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8
    AND s.evt_block_date BETWEEN DATE '2025-12-20' AND DATE '2025-12-26'
    GROUP BY DATE(s.evt_block_time)
)

SELECT
    pe.token_id,
    m.mint_block,
    pe.burn_block,
    pe.burn_time as burn_timestamp,
    CAST(pe.burn_date AS VARCHAR) as burn_date,
    (pe.burn_block - m.mint_block) as block_lifetime,
    pe.total_fee_eth,
    pe.total_fee_usdc,
    sdf.total_swap_fee_usdc as pool_daily_fee_usdc,
    CASE WHEN sdf.total_swap_fee_usdc > 0
         THEN pe.total_fee_usdc / sdf.total_swap_fee_usdc
         ELSE 0.0
    END as fee_share_x_k
FROM position_exits pe
JOIN mints m ON pe.token_id = m.token_id
LEFT JOIN swap_daily_fees sdf ON pe.burn_date = sdf.day
WHERE m.mint_block < pe.burn_block
ORDER BY pe.burn_date, pe.burn_block
LIMIT 50
