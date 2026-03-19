-- ThetaSwap FCI: Per-Position Fee Shares (ETH/USDC 0.3%, Dec 20-26 2025)
-- Dune Query ID: 6815894
-- Purpose: ~50 positions exiting ETH/USDC 0.3% pool around Dec 23 2025 outlier.
--          Per-position: token_id, mint_block, burn_block, block_lifetime, fee_share_x_k
-- Note: fee_share_x_k uses total Collect amounts (principal + fees) as numerator,
--       and pool-level Collect as denominator. This is a "total value" proxy.
--       For fee-only extraction, see per_position_fees_only_dec2025.sql.

WITH
-- Pool-level burns (liquidity removal) at ETH/USDC 0.3%, Dec 20-26
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

-- Link pool burns to NFT tokenIds via same-tx DecreaseLiquidity
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

-- Mint block for each position (lookback to Jan 2025)
mints AS (
    SELECT
        m.output_tokenId as token_id,
        MIN(m.call_block_number) as mint_block
    FROM uniswap_v3_ethereum.nonfungiblepositionmanager_call_mint m
    WHERE m.call_success = true
    AND m.output_tokenId IN (SELECT token_id FROM nft_exits)
    AND m.call_block_date >= DATE '2025-01-01'
    GROUP BY m.output_tokenId
),

-- Per-position lifetime fees (all Collect events, bounded to 2025)
position_fees AS (
    SELECT
        c.tokenId as token_id,
        SUM(CAST(c.amount0 AS DOUBLE)) / 1e18 as total_fee_eth,
        SUM(CAST(c.amount1 AS DOUBLE)) / 1e6 as total_fee_usdc
    FROM uniswap_v3_ethereum.nonfungiblepositionmanager_evt_collect c
    WHERE c.tokenId IN (SELECT token_id FROM nft_exits)
    AND c.evt_block_date >= DATE '2025-01-01'
    GROUP BY c.tokenId
),

-- Total pool fees collected per day (denominator for x_k)
pool_daily_fees AS (
    SELECT
        DATE(c.evt_block_time) as day,
        SUM(CAST(c.amount1 AS DOUBLE)) / 1e6 as total_fee_usdc
    FROM uniswap_v3_ethereum.uniswapv3pool_evt_collect c
    WHERE c.contract_address = 0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8
    AND c.evt_block_date BETWEEN DATE '2025-12-20' AND DATE '2025-12-26'
    GROUP BY DATE(c.evt_block_time)
)

SELECT
    ne.token_id,
    m.mint_block,
    ne.burn_block,
    ne.burn_time as burn_timestamp,
    CAST(ne.burn_date AS VARCHAR) as burn_date,
    (ne.burn_block - m.mint_block) as block_lifetime,
    pf.total_fee_eth,
    pf.total_fee_usdc,
    pdf.total_fee_usdc as pool_daily_fee_usdc,
    CASE WHEN pdf.total_fee_usdc > 0
         THEN pf.total_fee_usdc / pdf.total_fee_usdc
         ELSE 0.0
    END as fee_share_x_k
FROM nft_exits ne
JOIN mints m ON ne.token_id = m.token_id
LEFT JOIN position_fees pf ON ne.token_id = pf.token_id
LEFT JOIN pool_daily_fees pdf ON ne.burn_date = pdf.day
WHERE m.mint_block < ne.burn_block
ORDER BY ne.burn_date, ne.burn_block
LIMIT 50
