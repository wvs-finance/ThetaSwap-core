// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {V3MintData} from "reactive-hooks/types/ReactiveCallbackDataMod.sol";
import {UNISWAP_V3_REACTIVE} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";
import {AFTER_ADD_LIQUIDITY} from "./V3ActionTypes.sol";

// hookData layout: FLAG (2) | pool (20) | action (1)

function encodeAfterAddLiquidity(address pool) pure returns (bytes memory) {
    return abi.encodePacked(UNISWAP_V3_REACTIVE, pool, AFTER_ADD_LIQUIDITY);
}

// ── Common decoders (header) ──

function decodePoolAddress(bytes calldata hookData) pure returns (address pool) {
    assembly { pool := shr(96, calldataload(add(hookData.offset, 2))) }
}

function decodeActionType(bytes calldata hookData) pure returns (uint8 action) {
    action = uint8(hookData[22]);
}

// ── Memory-compatible log decoders ──
// Mirrors reactive-hooks/types/V3EventDecoderMod.sol but accepts memory LogRecord.

function decodeV3MintFromLog(IReactive.LogRecord memory log) pure returns (V3MintData memory) {
    address owner = address(uint160(log.topic_1));
    int24 tickLower = int24(int256(log.topic_2));
    int24 tickUpper = int24(int256(log.topic_3));
    (, uint128 liquidity,,) = abi.decode(log.data, (address, uint128, uint256, uint256));
    return V3MintData({
        pool: IUniswapV3Pool(log._contract),
        owner: owner,
        tickLower: tickLower,
        tickUpper: tickUpper,
        liquidity: liquidity
    });
}
