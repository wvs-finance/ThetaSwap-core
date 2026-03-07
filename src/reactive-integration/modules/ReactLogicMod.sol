// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {
    isSelfSync, topic0, emitter, logChainId
} from "../types/LogRecordExtMod.sol";
import {
    V3_SWAP_SIG, V3_MINT_SIG, V3_BURN_SIG, V3_COLLECT_SIG,
    decodeV3Swap, decodeV3Mint, decodeV3Burn, decodeV3Collect
} from "../types/V3EventDecoderMod.sol";
import {V3SwapData, V3MintData, V3BurnData, V3CollectData} from "../types/ReactiveCallbackDataMod.sol";
import {CollectedFees, v3PositionKey} from "../types/CollectedFeesMod.sol";
import {
    isWhitelisted, setWhitelisted,
    getCollectedFees, clearCollectedFees
} from "./ReactVmStorageMod.sol";

// Self-sync event signatures (emitted by RN instance, consumed by ReactVM)
uint256 constant POOL_REGISTERED_SIG = uint256(keccak256("PoolRegistered(uint256,address)"));
uint256 constant POOL_UNREGISTERED_SIG = uint256(keccak256("PoolUnregistered(uint256,address)"));

uint64 constant CALLBACK_GAS_LIMIT = 300_000;

// Main routing function — called by ThetaSwapReactive.react().
function processLog(
    IReactive.LogRecord calldata log,
    address self,
    address adapter
) {
    // Self-subscription sync: pool whitelist updates from RN instance
    if (isSelfSync(log, self)) {
        _handleSelfSync(log);
        return;
    }

    // Skip events from non-whitelisted pools
    if (!isWhitelisted(logChainId(log), emitter(log))) return;

    uint256 sig = topic0(log);

    if (sig == V3_SWAP_SIG) {
        V3SwapData memory data = decodeV3Swap(log);
        emit IReactive.Callback(
            logChainId(log), adapter, CALLBACK_GAS_LIMIT,
            abi.encodeWithSignature("onV3Swap((address,int24))", data)
        );
    } else if (sig == V3_MINT_SIG) {
        V3MintData memory data = decodeV3Mint(log);
        emit IReactive.Callback(
            logChainId(log), adapter, CALLBACK_GAS_LIMIT,
            abi.encodeWithSignature("onV3Mint((address,address,int24,int24,uint128))", data)
        );
    } else if (sig == V3_COLLECT_SIG) {
        // Accumulate fees in ReactVM state — NO callback
        V3CollectData memory data = decodeV3Collect(log);
        bytes32 posKey = v3PositionKey(data.owner, data.tickLower, data.tickUpper);
        CollectedFees storage fees = getCollectedFees(address(data.pool), posKey);
        fees.accumulate(data.feeAmount0, data.feeAmount1);
    } else if (sig == V3_BURN_SIG) {
        V3BurnData memory data = decodeV3Burn(log);
        bytes32 posKey = v3PositionKey(data.owner, data.tickLower, data.tickUpper);
        // Read and clear accumulated fees
        CollectedFees storage fees = getCollectedFees(address(data.pool), posKey);
        uint256 fee0 = fees.fee0;
        uint256 fee1 = fees.fee1;
        clearCollectedFees(address(data.pool), posKey);
        emit IReactive.Callback(
            logChainId(log), adapter, CALLBACK_GAS_LIMIT,
            abi.encodeWithSignature(
                "onV3Burn((address,address,int24,int24,uint128),uint256,uint256)",
                data, fee0, fee1
            )
        );
    }
}

function _handleSelfSync(IReactive.LogRecord calldata log) {
    uint256 sig = topic0(log);
    if (sig == POOL_REGISTERED_SIG) {
        (uint256 chainId_, address pool) = abi.decode(log.data, (uint256, address));
        setWhitelisted(chainId_, pool, true);
    } else if (sig == POOL_UNREGISTERED_SIG) {
        (uint256 chainId_, address pool) = abi.decode(log.data, (uint256, address));
        setWhitelisted(chainId_, pool, false);
    }
}
