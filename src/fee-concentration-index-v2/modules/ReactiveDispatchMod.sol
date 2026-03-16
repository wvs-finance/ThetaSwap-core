// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {ISubscriptionService} from "reactive-lib/interfaces/ISubscriptionService.sol";

import {OriginEndpoint, originId} from "reactive-hooks/types/OriginEndpoint.sol";
import {CallbackEndpoint, callbackId} from "reactive-hooks/types/CallbackEndpoint.sol";
import {BindingState} from "reactive-hooks/types/Binding.sol";
import {
    OriginRegistryStorage, setOrigin, getOriginExists,
    _originRegistryStorage
} from "reactive-hooks/modules/OriginRegistryStorageMod.sol";
import {
    CallbackRegistryStorage, setCallback, getCallback,
    _callbackRegistryStorage
} from "reactive-hooks/modules/CallbackRegistryStorageMod.sol";
import {
    EventDispatchStorage, getBindingCountByOrigin,
    _eventDispatchStorage
} from "reactive-hooks/modules/EventDispatchStorageMod.sol";
import {
    immediateBind, dispatch, validateBind
} from "reactive-hooks/libraries/EventDispatchLib.sol";
import {reactVMBatchSubscription} from "reactive-hooks/libraries/SubscriptionLib.sol";

import {POOL_ADDED_SIG} from "@fee-concentration-index-v2/libraries/PoolAddedSig.sol";
import {UNISWAP_V3_REACTIVE} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";
import {V3_SWAP_SIG, V3_MINT_SIG, V3_BURN_SIG, v3PoolSigs}
    from "@fee-concentration-index-v2/protocols/uniswap-v3/libraries/EventSignatures.sol";
import {decodeV3PoolAddedData}
    from "@fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PoolAddedLib.sol";
import {mutateV3Payload}
    from "@fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PayloadMutatorLib.sol";

import {IUnlockCallbackReactiveExt}
    from "@reactive-integration/template/interfaces/IUnlockCallbackReactiveExt.sol";

uint64 constant CALLBACK_GAS_LIMIT = 1_000_000;

// ── Self-sync handler ──

/// @dev Called when ReactVM receives a PoolAdded log from cross-chain subscription.
/// Registers origins + callback + bindings in EDT, then subscribes to pool events.
function handlePoolAdded(
    IReactive.LogRecord memory log,
    ISubscriptionService service
) {
    (bytes2 protocolFlag, bytes memory poolData) = abi.decode(log.data, (bytes2, bytes));
    address callbackTarget = address(uint160(log.topic_2));

    if (protocolFlag == UNISWAP_V3_REACTIVE) {
        handleV3PoolAdded(service, callbackTarget, poolData);
    }
}

function handleV3PoolAdded(
    ISubscriptionService service,
    address callbackTarget,
    bytes memory poolData
) {
    (uint256 chainId, address pool, ) = decodeV3PoolAddedData(poolData);

    OriginRegistryStorage storage origins = _originRegistryStorage();
    CallbackRegistryStorage storage callbacks = _callbackRegistryStorage();
    EventDispatchStorage storage edt = _eventDispatchStorage();

    // Register 3 OriginEndpoints (Swap/Mint/Burn × pool)
    uint256[] memory sigs = v3PoolSigs();
    bytes32[] memory originIds = new bytes32[](3);
    for (uint256 i = 0; i < 3; i++) {
        OriginEndpoint memory origin = OriginEndpoint({
            chainId: uint32(chainId),
            emitter: pool,
            eventSig: bytes32(sigs[i])
        });
        originIds[i] = setOrigin(origins, origin);
    }

    // Register 1 CallbackEndpoint (idempotent — same target for all pools)
    CallbackEndpoint memory cb = CallbackEndpoint({
        chainId: uint32(chainId),
        target: callbackTarget,
        selector: IUnlockCallbackReactiveExt.unlockCallbackReactive.selector,
        gasLimit: CALLBACK_GAS_LIMIT
    });
    bytes32 cbId = setCallback(callbacks, cb);

    // Create 3 Bindings (one per origin → same callback)
    for (uint256 i = 0; i < 3; i++) {
        validateBind(origins, callbacks, originIds[i], cbId);
        immediateBind(edt, originIds[i], cbId);
    }

    // Subscribe to V3 pool events on the origin chain
    reactVMBatchSubscription(service, chainId, pool, sigs);
}

// ── Event dispatch (hot path) ──

/// @dev Called when ReactVM receives a V3 pool event (Swap/Mint/Burn).
/// Dispatches through EDT, runs payload mutator, emits Callback per active binding.
function dispatchEvent(IReactive.LogRecord memory log) {
    OriginEndpoint memory origin = OriginEndpoint({
        chainId: uint32(log.chain_id),
        emitter: log._contract,
        eventSig: bytes32(log.topic_0)
    });
    bytes32 oid = originId(origin);

    EventDispatchStorage storage edt = _eventDispatchStorage();
    bytes32[] memory activeCallbackIds = dispatch(edt, oid);

    if (activeCallbackIds.length == 0) return;

    bytes memory enrichedPayload = mutateV3Payload(log);

    CallbackRegistryStorage storage callbacks = _callbackRegistryStorage();
    for (uint256 i = 0; i < activeCallbackIds.length; i++) {
        CallbackEndpoint storage cb = getCallback(callbacks, activeCallbackIds[i]);
        emit IReactive.Callback(
            uint256(cb.chainId),
            cb.target,
            uint64(cb.gasLimit),
            abi.encodeWithSelector(cb.selector, address(0), enrichedPayload)
        );
    }
}
