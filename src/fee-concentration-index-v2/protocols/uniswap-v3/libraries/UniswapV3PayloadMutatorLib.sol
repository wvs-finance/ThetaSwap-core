// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {V3_SWAP_SIG, V3_MINT_SIG, V3_BURN_SIG} from "./EventSignatures.sol";
import {
    getLastTick, setLastTick,
    getPositionShadow, setPositionShadow
} from "../modules/UniswapV3ReactVMStorageMod.sol";

/// @dev Enriches raw V3 log data before callback emission.
/// Swap: injects tickBefore from shadow. Mint/Burn: updates position shadow.
/// Returns uniform 3-field: abi.encode(LogRecord, int24 tickBefore, uint128 posLiqBefore)
function mutateV3Payload(IReactive.LogRecord memory log) returns (bytes memory) {
    uint256 sig = log.topic_0;
    uint256 chainId_ = log.chain_id;
    address pool = log._contract;

    if (sig == V3_SWAP_SIG) {
        (,,,, int24 tickAfter) = abi.decode(log.data, (int256, int256, uint160, uint128, int24));
        (int24 prevTick, bool isSet) = getLastTick(chainId_, pool);
        int24 tickBefore = isSet ? prevTick : tickAfter;
        setLastTick(chainId_, pool, tickAfter);
        return abi.encode(log, tickBefore, uint128(0));
    }

    if (sig == V3_MINT_SIG) {
        address owner = address(uint160(log.topic_1));
        int24 tickLower = int24(int256(log.topic_2));
        int24 tickUpper = int24(int256(log.topic_3));
        (, uint128 liquidity,,) = abi.decode(log.data, (address, uint128, uint256, uint256));
        bytes32 posKey = keccak256(abi.encodePacked(owner, tickLower, tickUpper));
        (uint128 shadowLiq,) = getPositionShadow(chainId_, pool, posKey);
        setPositionShadow(chainId_, pool, posKey, shadowLiq + liquidity);
        return abi.encode(log, int24(0), uint128(0));
    }

    if (sig == V3_BURN_SIG) {
        address owner = address(uint160(log.topic_1));
        int24 tickLower = int24(int256(log.topic_2));
        int24 tickUpper = int24(int256(log.topic_3));
        (uint128 liquidity,,) = abi.decode(log.data, (uint128, uint256, uint256));
        if (liquidity == 0) return abi.encode(log, int24(0), uint128(0));
        bytes32 posKey = keccak256(abi.encodePacked(owner, tickLower, tickUpper));
        (uint128 posLiqBefore,) = getPositionShadow(chainId_, pool, posKey);
        unchecked {
            setPositionShadow(chainId_, pool, posKey, posLiqBefore - liquidity);
        }
        return abi.encode(log, int24(0), posLiqBefore);
    }

    return abi.encode(log, int24(0), uint128(0));
}
