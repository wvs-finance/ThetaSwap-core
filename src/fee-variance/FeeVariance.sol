// SPDX-License-Identifier: MIT
pragma solidity >=0.7.5 <0.9.0;
pragma abicoder v2;

import "@uniswap/v3-periphery/contracts/libraries/PositionValue.sol";
import "@uniswap/v3-periphery/contracts/interfaces/INonfungiblePositionManager.sol";
import "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import "@uniswap/v3-core/contracts/libraries/FullMath.sol";
import "@uniswap/v3-core/contracts/libraries/FixedPoint128.sol";

/// @title FeeVariance — Cross-sectional fee dispersion measurement
/// @notice Computes variance of (fee_share_i - liquidity_share_i) across NPM positions
/// @dev Uses PositionValue.fees() from v3-periphery for per-position fee accounting
library FeeVariance {
    uint256 internal constant Q128 = FixedPoint128.Q128;

    struct PositionData {
        uint256 feesUSD_X128;  // fees in USD terms, X128 fixed point
        uint256 liquidity;
    }

    /// @notice Compute FeeVarianceX128 for a set of positions at current block
    /// @param npm The NonfungiblePositionManager
    /// @param pool The Uniswap V3 pool
    /// @param tokenIds Array of NPM tokenIds to include
    /// @return varianceX128 Cross-sectional variance of (fee_share - liquidity_share), in X128
    /// @return numPositions Number of positions with nonzero liquidity
    function compute(
        INonfungiblePositionManager npm,
        IUniswapV3Pool pool,
        uint256[] memory tokenIds
    ) internal view returns (uint256 varianceX128, uint256 numPositions) {
        (uint160 sqrtPriceX96, , , , , , ) = pool.slot0();

        // price = sqrtPriceX96^2 / 2^192, in X128 = sqrtPriceX96^2 * 2^128 / 2^192
        // = sqrtPriceX96^2 / 2^64
        // For USDC/WETH pool: gives token1(WETH) price in token0(USDC) terms
        uint256 priceX128 = FullMath.mulDiv(
            uint256(sqrtPriceX96) * uint256(sqrtPriceX96),
            Q128,
            1 << 192
        );

        // Pass 1: collect fees (USD) and liquidity for each active position
        PositionData[] memory positions = new PositionData[](tokenIds.length);
        uint256 totalFeesX128;
        uint256 totalLiquidity;
        uint256 count;

        for (uint256 i = 0; i < tokenIds.length; i++) {
            try npm.positions(tokenIds[i]) returns (
                uint96, address, address, address, uint24,
                int24, int24, uint128 liq,
                uint256, uint256, uint128, uint128
            ) {
                if (liq == 0) continue;

                // Get fees using PositionValue
                (uint256 fees0, uint256 fees1) = PositionValue.fees(npm, tokenIds[i]);

                // USD-denominate: fees0 is USDC (token0), fees1 is WETH (token1)
                // priceX128 = WETH/USDC price in X128
                uint256 feesUSD_X128 = fees0 * Q128 + FullMath.mulDiv(fees1, priceX128, 1);

                positions[count] = PositionData({
                    feesUSD_X128: feesUSD_X128,
                    liquidity: uint256(liq)
                });
                totalFeesX128 += feesUSD_X128;
                totalLiquidity += uint256(liq);
                count++;
            } catch {
                continue;
            }
        }

        if (count < 2 || totalFeesX128 == 0 || totalLiquidity == 0) {
            return (0, count);
        }

        // Pass 2: compute variance of (fee_share - liq_share)
        // C_i = fees_i/totalFees - liq_i/totalLiq
        // Var = (1/N) * sum(C_i^2)   [sum(C_i) = 0 by construction]
        uint256 sumSquaresX128;

        for (uint256 i = 0; i < count; i++) {
            uint256 feeShareX128 = FullMath.mulDiv(
                positions[i].feesUSD_X128, Q128, totalFeesX128
            );
            uint256 liqShareX128 = FullMath.mulDiv(
                positions[i].liquidity, Q128, totalLiquidity
            );

            // C_i = feeShare - liqShare (can be negative)
            int256 ci;
            if (feeShareX128 >= liqShareX128) {
                ci = int256(feeShareX128 - liqShareX128);
            } else {
                ci = -int256(liqShareX128 - feeShareX128);
            }

            uint256 ciAbs = uint256(ci >= 0 ? ci : -ci);
            sumSquaresX128 += FullMath.mulDiv(ciAbs, ciAbs, Q128);
        }

        varianceX128 = sumSquaresX128 / count;
        numPositions = count;
    }
}
