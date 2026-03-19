// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {ISubscriptionService} from "reactive-lib/interfaces/ISubscriptionService.sol";
import {coverDebt, depositToSystem} from "reactive-hooks/modules/DebtMod.sol";
import {SYSTEM_CONTRACT} from "reactive-hooks/libraries/DebtLib.sol";
import {REACTIVE_IGNORE} from "reactive-hooks/libraries/SubscriptionLib.sol";
import {V3_SWAP_SIG, V3_MINT_SIG, V3_BURN_SIG} from "./libraries/EventSignatures.sol";
import {mutateV3Payload} from "./libraries/UniswapV3PayloadMutatorLib.sol";
import {initOwner, requireOwner, transferOwnership as _transferOwnership} from "../../modules/dependencies/LibOwner.sol";
import {migrateFunds as _migrateFunds} from "../../modules/dependencies/AdminLib.sol";

uint64 constant CALLBACK_GAS_LIMIT = 1_000_000;

/// @title UniswapV3Reactive
/// @dev Reactive Network contract for V3 reactive integration.
/// Dual-instance: RN manages subscriptions, ReactVM processes events.
/// V1-proven pattern: bool immutable vm, explicit registerPool, direct subscribe.
contract UniswapV3Reactive {
    address public callback;
    ISubscriptionService immutable service;
    bool immutable vm;

    error ZeroAddress();
    error OnlyReactVM();
    error OnlyRN();

    event CallbackUpdated(address indexed oldCallback, address indexed newCallback);

    constructor(address callback_) payable {
        initOwner(msg.sender);
        callback = callback_;
        service = ISubscriptionService(SYSTEM_CONTRACT);

        uint256 size;
        assembly { size := extcodesize(0x0000000000000000000000000000000000fffFfF) }
        vm = size == 0;

        if (!vm) {
            depositToSystem(address(this));
        }
    }

    function react(IReactive.LogRecord calldata log) external {
        if (!vm) revert OnlyReactVM();

        // Zero-burn skip: V3 burnPosition() emits liq=0 then full burn.
        if (log.topic_0 == V3_BURN_SIG) {
            (uint128 burnedLiq,,) = abi.decode(log.data, (uint128, uint256, uint256));
            if (burnedLiq == 0) return;
        }

        emit IReactive.Callback(
            log.chain_id, callback, CALLBACK_GAS_LIMIT,
            abi.encodeWithSignature(
                "unlockCallbackReactive(address,bytes)",
                address(0),
                mutateV3Payload(log)
            )
        );
    }

    function registerPool(uint256 chainId_, address pool) external {
        requireOwner();
        if (vm) revert OnlyRN();
        service.subscribe(chainId_, pool, V3_SWAP_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        service.subscribe(chainId_, pool, V3_MINT_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        service.subscribe(chainId_, pool, V3_BURN_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    }

    function unregisterPool(uint256 chainId_, address pool) external {
        requireOwner();
        if (vm) revert OnlyRN();
        service.unsubscribe(chainId_, pool, V3_SWAP_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        service.unsubscribe(chainId_, pool, V3_MINT_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        service.unsubscribe(chainId_, pool, V3_BURN_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    }

    function setCallback(address newCallback) external {
        requireOwner();
        if (newCallback == address(0)) revert ZeroAddress();
        address oldCallback = callback;
        callback = newCallback;
        emit CallbackUpdated(oldCallback, newCallback);
    }

    function migrateFunds(address payable to) external {
        requireOwner();
        _migrateFunds(to, address(this).balance);
    }

    function transferOwnership(address newOwner) external {
        requireOwner();
        _transferOwnership(newOwner);
    }

    function fund() external payable {
        depositToSystem(address(this));
    }

    receive() external payable {
        coverDebt(address(this));
    }
}
