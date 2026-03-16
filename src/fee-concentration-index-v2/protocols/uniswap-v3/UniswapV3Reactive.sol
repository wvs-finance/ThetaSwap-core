// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {ISubscriptionService} from "reactive-lib/interfaces/ISubscriptionService.sol";
import {coverDebt, depositToSystem} from "reactive-hooks/modules/DebtMod.sol";
import {SYSTEM_CONTRACT} from "reactive-hooks/libraries/DebtLib.sol";
import {requireVM} from "reactive-hooks/modules/ReactVMMod.sol";
import {isReactiveVm, isActive} from "reactive-hooks/types/ReactVM.sol";
import {
    reactiveNetworkBatchSubscription,
    reactVMBatchSubscription, reactVMBatchUnsubscription
} from "reactive-hooks/libraries/SubscriptionLib.sol";
import {
    POOL_REGISTERED_SIG, POOL_UNREGISTERED_SIG,
    selfSyncSigs, v3PoolSigs
} from "./libraries/EventSignatures.sol";
import {
    isSelfSync, topic0, logChainId
} from "reactive-hooks/types/LogRecordExtMod.sol";

uint64 constant CALLBACK_GAS_LIMIT = 1_000_000;

/// @title UniswapV3Reactive
/// @dev Reactive Network contract for V3 reactive integration.
/// Dual-instance: RN subscribes to self-sync, ReactVM auto-subscribes to V3 pools
/// when PoolRegistered is received, then forwards raw event data to UniswapV3Callback.
contract UniswapV3Reactive {
    address immutable callback;
    ISubscriptionService immutable service;

    constructor(address callback_) payable {
        callback = callback_;
        service = ISubscriptionService(SYSTEM_CONTRACT);

        if (!isActive(isReactiveVm())) {
            reactiveNetworkBatchSubscription(service, address(this), selfSyncSigs());
            depositToSystem(address(this));
        }
    }

    function react(IReactive.LogRecord calldata log) external {
        requireVM();

        if (isSelfSync(log, address(this))) {
            uint256 sig = topic0(log);
            uint256 chainId_ = log.topic_1;
            address pool = address(uint160(log.topic_2));

            if (sig == POOL_REGISTERED_SIG) {
                reactVMBatchSubscription(service, chainId_, pool, v3PoolSigs());
            } else if (sig == POOL_UNREGISTERED_SIG) {
                reactVMBatchUnsubscription(service, chainId_, pool, v3PoolSigs());
            }
            return;
        }

        emit IReactive.Callback(
            logChainId(log), callback, CALLBACK_GAS_LIMIT,
            abi.encodeWithSignature(
                "unlockCallbackReactive(address,bytes)",
                address(0),
                abi.encode(log)
            )
        );
    }

    function fund() external payable {
        depositToSystem(address(this));
    }

    receive() external payable {
        coverDebt(address(this));
    }
}
