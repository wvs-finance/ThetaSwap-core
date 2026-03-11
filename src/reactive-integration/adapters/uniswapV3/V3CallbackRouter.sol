// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {IUniswapV3MintCallback} from "@uniswap/v3-core/contracts/interfaces/callback/IUniswapV3MintCallback.sol";
import {IUniswapV3SwapCallback} from "@uniswap/v3-core/contracts/interfaces/callback/IUniswapV3SwapCallback.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";

/// @notice Minimal router enabling EOAs to mint/swap on V3 pools via broadcast.
/// Callbacks pull tokens from msg.sender (stored in calldata). Not for production.
contract V3CallbackRouter is IUniswapV3MintCallback, IUniswapV3SwapCallback {
    struct CallbackData {
        address token0;
        address token1;
        address payer;
    }

    function mint(
        IUniswapV3Pool pool,
        address recipient,
        int24 tickLower,
        int24 tickUpper,
        uint128 amount
    ) external returns (uint256 amount0, uint256 amount1) {
        bytes memory data = abi.encode(CallbackData({
            token0: pool.token0(),
            token1: pool.token1(),
            payer: msg.sender
        }));
        (amount0, amount1) = pool.mint(recipient, tickLower, tickUpper, amount, data);
    }

    function swap(
        IUniswapV3Pool pool,
        address recipient,
        bool zeroForOne,
        int256 amountSpecified,
        uint160 sqrtPriceLimitX96
    ) external returns (int256 amount0, int256 amount1) {
        bytes memory data = abi.encode(CallbackData({
            token0: pool.token0(),
            token1: pool.token1(),
            payer: msg.sender
        }));
        (amount0, amount1) = pool.swap(recipient, zeroForOne, amountSpecified, sqrtPriceLimitX96, data);
    }

    function uniswapV3MintCallback(uint256 amount0Owed, uint256 amount1Owed, bytes calldata data) external override {
        CallbackData memory cb = abi.decode(data, (CallbackData));
        if (amount0Owed > 0) IERC20(cb.token0).transferFrom(cb.payer, msg.sender, amount0Owed);
        if (amount1Owed > 0) IERC20(cb.token1).transferFrom(cb.payer, msg.sender, amount1Owed);
    }

    function uniswapV3SwapCallback(int256 amount0Delta, int256 amount1Delta, bytes calldata data) external override {
        CallbackData memory cb = abi.decode(data, (CallbackData));
        if (amount0Delta > 0) IERC20(cb.token0).transferFrom(cb.payer, msg.sender, uint256(amount0Delta));
        if (amount1Delta > 0) IERC20(cb.token1).transferFrom(cb.payer, msg.sender, uint256(amount1Delta));
    }
}
