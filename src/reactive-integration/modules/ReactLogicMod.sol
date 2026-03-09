// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {
    isSelfSync, topic0, emitter, logChainId
} from "../types/LogRecordExtMod.sol";
import {
    V3_SWAP_SIG, V3_MINT_SIG, V3_BURN_SIG,
    decodeV3Swap, decodeV3Mint, decodeV3Burn
} from "../types/V3EventDecoderMod.sol";
import {V3SwapData, V3MintData, V3BurnData} from "../types/ReactiveCallbackDataMod.sol";

import {
    isWhitelisted, setWhitelisted
} from "./ReactVmStorageMod.sol";

// Self-sync event signatures (emitted by RN instance, consumed by ReactVM)
uint256 constant POOL_REGISTERED_SIG = uint256(keccak256("PoolRegistered(uint256,address)"));
uint256 constant POOL_UNREGISTERED_SIG = uint256(keccak256("PoolUnregistered(uint256,address)"));

uint64 constant CALLBACK_GAS_LIMIT = 1_000_000;

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

    // Reactive Network replaces the first address(0) arg with the actual RVM ID
    // before executing the callback on the destination chain.

    if (sig == V3_SWAP_SIG) {
        V3SwapData memory data = decodeV3Swap(log);
        emit IReactive.Callback(
            logChainId(log), adapter, CALLBACK_GAS_LIMIT,
            abi.encodeWithSignature("onV3Swap(address,(address,int24))", address(0), data)
        );
    } else if (sig == V3_MINT_SIG) {
        V3MintData memory data = decodeV3Mint(log);
        emit IReactive.Callback(
            logChainId(log), adapter, CALLBACK_GAS_LIMIT,
            abi.encodeWithSignature("onV3Mint(address,(address,address,int24,int24,uint128))", address(0), data)
        );
    } else if (sig == V3_BURN_SIG) {
        // No longer deferred — onV3Burn reads fees directly from V3 pool.
        // Still skip zero-burns (fee-accounting only, liq==0) since they
        // don't represent actual position removal.
        V3BurnData memory data = decodeV3Burn(log);
        if (data.liquidity == 0) return;
        emit IReactive.Callback(
            logChainId(log), adapter, CALLBACK_GAS_LIMIT,
            abi.encodeWithSignature("onV3Burn(address,(address,address,int24,int24,uint128))", address(0), data)
        );
    }
    // V3_COLLECT_SIG: no-op — fees are read directly from V3 pool in onV3Burn
}

function _handleSelfSync(IReactive.LogRecord calldata log) {
    uint256 sig = topic0(log);
    // PoolRegistered/PoolUnregistered have both params indexed →
    // chainId is in topic_1, pool address is in topic_2 (not in data).
    if (sig == POOL_REGISTERED_SIG) {
        uint256 chainId_ = log.topic_1;
        address pool = address(uint160(log.topic_2));
        setWhitelisted(chainId_, pool, true);
    } else if (sig == POOL_UNREGISTERED_SIG) {
        uint256 chainId_ = log.topic_1;
        address pool = address(uint160(log.topic_2));
        setWhitelisted(chainId_, pool, false);
    }
}
