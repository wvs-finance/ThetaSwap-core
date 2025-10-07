//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./types/Shared.sol";
import {Exttload} from "@uniswap/v4-core/src/Exttload.sol";
import {IParityTaxExtt} from "./interfaces/IParityTaxExtt.sol";



contract ParityTaxExtt is Exttload, IParityTaxExtt{

    function tstore_plp_liquidity(int256 liquidityChange) external{
        assembly("memory-safe"){
            tstore(PLP_LIQUIDITY_POSITION_LOCATION, liquidityChange)
        }
    }

    function tstore_plp_feesAccrued(uint256 feesAccruedOn0, uint256 feesAccruedOn1) external{
        assembly("memory-safe"){
            tstore(add(PLP_LIQUIDITY_POSITION_LOCATION,0x01), feesAccruedOn0)
            tstore(add(PLP_LIQUIDITY_POSITION_LOCATION,0x02), feesAccruedOn1)

        }
   
    }

    function tstore_plp_tokenId(uint256 tokenId) external {
        _tstore_plp_tokenId(tokenId);
    }
    function _tstore_plp_tokenId(uint256 tokenId) internal {
        assembly("memory-safe") {
            tstore(add(PLP_LIQUIDITY_POSITION_LOCATION, 0x03), tokenId)
        }
    }

    function tstore_swap_beforeSwapTick(int24 tickBeforeSwap) external{
        
    }

    function tstore_swap_beforeSwapSqrtPriceX96(uint160 beforeSwapSqrtPriceX96) external {
        _tstore_swap_beforeSwapSqrtPriceX96(beforeSwapSqrtPriceX96);
    }
    function _tstore_swap_beforeSwapSqrtPriceX96(uint160 beforeSwapSqrtPriceX96) internal {
        assembly("memory-safe") {
            tstore(PRICE_IMPACT_LOCATION, beforeSwapSqrtPriceX96)
        }
    }

    function tstore_swap_beforeSwapExternalSqrtPriceX96(uint160 beforeSwapExternalSqrtPriceX96) external {
        _tstore_swap_beforeSwapExternalSqrtPriceX96(beforeSwapExternalSqrtPriceX96);
    }
    function _tstore_swap_beforeSwapExternalSqrtPriceX96(uint160 beforeSwapExternalSqrtPriceX96) internal {
        assembly("memory-safe") {
            tstore(add(PRICE_IMPACT_LOCATION, 0x01), beforeSwapExternalSqrtPriceX96)
        }
    }

    function tstore_jit_tokenId(uint256 tokenId) external {
        _tstore_jit_tokenId(tokenId);
    }
    function _tstore_jit_tokenId(uint256 tokenId) internal {
        assembly("memory-safe") {
            tstore(JIT_LIQUIDITY_POSITION_LOCATION, tokenId)
        }
    }

    function tstore_jit_feeRevenue(uint256 feeRevenueOn0, uint256 feeRevenueOn1) external {
        _tstore_jit_feeRevenue(feeRevenueOn0, feeRevenueOn1);
    }
    function _tstore_jit_feeRevenue(
        uint256 feeRevenueOn0,
        uint256 feeRevenueOn1
    ) internal {
        assembly("memory-safe") {
            tstore(add(JIT_LIQUIDITY_POSITION_LOCATION, 0x04), feeRevenueOn0)
            tstore(add(JIT_LIQUIDITY_POSITION_LOCATION, 0x05), feeRevenueOn1)
        }
    }

    function tstore_jit_positionInfo(PositionInfo positionInfo) external {
        _tstore_jit_positionInfo(positionInfo);
    }
    function _tstore_jit_positionInfo(
        PositionInfo positionInfo
    ) internal {
        bytes32 lpPositionInfo = bytes32(PositionInfo.unwrap(positionInfo));
        assembly("memory-safe") {
            tstore(add(JIT_LIQUIDITY_POSITION_LOCATION, 0x02), lpPositionInfo)
        }
    }

    function tstore_jit_liquidity(uint256 liquidity) external {
        _tstore_jit_liquidity(liquidity);
    }
    function _tstore_jit_liquidity(
        uint256 liquidity
    ) internal {
        assembly("memory-safe") {
            tstore(add(JIT_LIQUIDITY_POSITION_LOCATION, 0x03), liquidity)
        }
    }

    function tstore_jit_positionKey(bytes32 positionKey) external {
        _tstore_jit_positionKey(positionKey);
    }
    function _tstore_jit_positionKey(
        bytes32 positionKey
    ) internal {
        assembly("memory-safe") {
            tstore(add(JIT_LIQUIDITY_POSITION_LOCATION, 0x01), positionKey)
        }
    }

    function tstore_jit_owner(address owner) external {
        _tstore_jit_owner(owner);
    }
    function _tstore_jit_owner(
        address owner
    ) internal {
        assembly("memory-safe") {
            tstore(add(JIT_LIQUIDITY_POSITION_LOCATION, 0x06), owner)
        }
    }

    
    /**
     * @notice Internal function to store complete JIT liquidity position in transient storage
     * @dev Stores all JIT position data by calling individual storage functions
     * @param jitLiquidityPosition The complete JIT liquidity position data
     */
    function tstore_jit_liquidityPosition(LiquidityPosition memory jitLiquidityPosition) external{
        
        _tstore_jit_positionKey(jitLiquidityPosition.positionKey);
        _tstore_jit_liquidity(
            jitLiquidityPosition.liquidity
        );
        _tstore_jit_positionInfo(jitLiquidityPosition.positionInfo);
        _tstore_jit_feeRevenue(
            jitLiquidityPosition.feeRevenueOnCurrency0,
            jitLiquidityPosition.feeRevenueOnCurrency1
        );
        _tstore_jit_owner(jitLiquidityPosition.owner);
    }



   



}