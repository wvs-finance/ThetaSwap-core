// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {Position} from "v4-core/src/libraries/Position.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {SwapParams} from "v4-core/src/types/PoolOperation.sol";
import {PoolSwapTest} from "v4-core/src/test/PoolSwapTest.sol";
import {LiquidityOperations} from "@uniswap/v4-periphery/test/shared/LiquidityOperations.sol";
import {PositionConfig} from "@uniswap/v4-periphery/test/shared/PositionConfig.sol";

// Thin wrappers around LiquidityOperations (mint/decreaseLiquidity/burn) and PoolSwapTest.
// Each action is pranked as the correct actor: LP for liquidity, swapper for swaps.
// The inheriting test contract must set fciLP, fciSwapper, fciSwapRouter in setUp().

abstract contract FCITestHelper is LiquidityOperations {
    address internal fciLP;
    address internal fciSwapper;
    PoolSwapTest internal fciSwapRouter;

    function _mintPosition(PoolKey memory k, int24 tickLower, int24 tickUpper, uint256 liquidity)
        internal
        returns (uint256 tokenId)
    {
        return _mintPositionAs(fciLP, k, tickLower, tickUpper, liquidity);
    }

    function _mintPositionAs(address lp, PoolKey memory k, int24 tickLower, int24 tickUpper, uint256 liquidity)
        internal
        returns (uint256 tokenId)
    {
        PositionConfig memory config = PositionConfig({
            poolKey: k,
            tickLower: tickLower,
            tickUpper: tickUpper
        });
        tokenId = lpm.nextTokenId();
        vm.prank(lp);
        mint(config, liquidity, lp, "");
    }

    function _burnPosition(PoolKey memory k, uint256 tokenId, int24 tickLower, int24 tickUpper, uint256 liquidity)
        internal
    {
        _burnPositionAs(fciLP, k, tokenId, tickLower, tickUpper, liquidity);
    }

    function _burnPositionAs(address lp, PoolKey memory k, uint256 tokenId, int24 tickLower, int24 tickUpper, uint256 liquidity)
        internal
    {
        PositionConfig memory config = PositionConfig({
            poolKey: k,
            tickLower: tickLower,
            tickUpper: tickUpper
        });
        vm.startPrank(lp);
        decreaseLiquidity(tokenId, config, liquidity, "");
        burn(tokenId, config, "");
        vm.stopPrank();
    }

    function _swap(PoolKey memory k, bool zeroForOne, int256 amountSpecified)
        internal
        returns (BalanceDelta)
    {
        vm.prank(fciSwapper);
        return fciSwapRouter.swap(
            k,
            SwapParams({
                zeroForOne: zeroForOne,
                amountSpecified: amountSpecified,
                sqrtPriceLimitX96: zeroForOne
                    ? TickMath.MIN_SQRT_PRICE + 1
                    : TickMath.MAX_SQRT_PRICE - 1
            }),
            PoolSwapTest.TestSettings({
                takeClaims: false,
                settleUsingBurn: false
            }),
            ""
        );
    }

    /// Position key: owner = address(lpm), salt = tokenId (V4 PositionManager convention)
    function _positionKey(uint256 tokenId, int24 tickLower, int24 tickUpper)
        internal
        view
        returns (bytes32)
    {
        return Position.calculatePositionKey(address(lpm), tickLower, tickUpper, bytes32(tokenId));
    }
}
