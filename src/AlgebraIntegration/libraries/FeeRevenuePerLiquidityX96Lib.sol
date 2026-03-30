// SPDX-License-Identifier: BUSL-1.1
pragma solidity >=0.8.20;

import '@cryptoalgebra/integral-core/contracts/interfaces/pool/IAlgebraPoolState.sol';
import '@cryptoalgebra/integral-core/contracts/libraries/TickMath.sol';
import {X128MathLib} from './X128MathLib.sol';

function innerFeeGrowthOnTick(
    address self,
    int24 tick
) view returns (uint256 innerFeeGrowth0TokenX128, uint256 innerFeeGrowth1TokenX128) {
    (, int24 currentTick, , , , ) = IAlgebraPoolState(self).globalState();
    uint256 totalFeeGrowth0 = IAlgebraPoolState(self).totalFeeGrowth0Token();
    uint256 totalFeeGrowth1 = IAlgebraPoolState(self).totalFeeGrowth1Token();

    (, , , , uint256 outerFeeGrowth0Token, uint256 outerFeeGrowth1Token) = IAlgebraPoolState(self).ticks(tick);

    unchecked {
        if (currentTick >= tick) {
            innerFeeGrowth0TokenX128 = totalFeeGrowth0 - outerFeeGrowth0Token;
            innerFeeGrowth1TokenX128 = totalFeeGrowth1 - outerFeeGrowth1Token;
        } else {
            innerFeeGrowth0TokenX128 = outerFeeGrowth0Token;
            innerFeeGrowth1TokenX128 = outerFeeGrowth1Token;
        }
    }
}

function updateFeeRevenuePerLiquidityX96(address self, int24 tick) view returns (uint160) {
    (, int128 liquidityDelta, , , , ) = IAlgebraPoolState(self).ticks(tick);

    if (liquidityDelta == 0) {
        return uint160(0x00);
    }

    (uint256 innerFeeGrowth0TokenX128, uint256 innerFeeGrowth1TokenX128) = innerFeeGrowthOnTick(self, tick);

    uint256 absLiquidityDelta = uint128(liquidityDelta > 0 ? liquidityDelta : -liquidityDelta);
    uint160 sqrtPriceX96 = TickMath.getSqrtRatioAtTick(tick);

    // fullMulX128(fg0_X128, sqrtPriceX96) = (fg0 * sqrtP * 2^224) >> 128 = fg0 * sqrtP * 2^96  → Q96
    // fg1_X128 >> 32 = fg1 * 2^128 >> 32 = fg1 * 2^96                                          → Q96
    return uint160(
        (X128MathLib.fullMulX128(innerFeeGrowth0TokenX128, sqrtPriceX96) + (innerFeeGrowth1TokenX128 >> 32))
        / absLiquidityDelta
    );
}
