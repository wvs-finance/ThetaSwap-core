// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {ISubscriptionService} from "reactive-lib/interfaces/ISubscriptionService.sol";
import {processLog} from "reactive-hooks/modules/ReactLogicMod.sol";
import {subscribeV3Pool, unsubscribeV3Pool, REACTIVE_IGNORE} from "reactive-hooks/modules/SubscriptionMod.sol";
import {coverDebt, depositToSystem} from "reactive-hooks/modules/DebtMod.sol";
import {requireVM} from "reactive-hooks/modules/ReactVMMod.sol";
import {requireSolvency} from "reactive-hooks/libraries/DebtLib.sol";

// Self-sync events — emitted on RN instance, consumed by ReactVM
event PoolRegistered(uint256 indexed chainId, address indexed pool);
event PoolUnregistered(uint256 indexed chainId, address indexed pool);

// Thin shell — all logic lives in Mod files.
// Dual-instance: RN manages subscriptions, ReactVM processes events.

// note: This is to be named ReactiveShell
// --> Uses OwnerMod
// --> receives a callback (adapter) --> CallbackMod or lib
// --> receivs a service --> SystemServiceMod or lib
// --> VM --> ReactVM (type, lib,. mod)
//                     
//                        -- > ReactVMSubscriptionsLib  
//                       / 
// --> SubscriptionsMod         <- require ReactVM
//                       \
//                        --> ReactiveNetworkSubscriptionsLib
// --> DebtMod

// on uniswapV3 --> ThetaSwapReactiveFacet
contract ThetaSwapReactive {
    address immutable owner;
    address immutable adapter;
    ISubscriptionService immutable service;
    bool immutable vm;

    error OnlyOwner();
    error OnlyReactVM();
    error OnlyRN();

    constructor(address adapter_, address payable service_) payable {
        owner = msg.sender;
        adapter = adapter_;
        service = ISubscriptionService(service_);

        // Detect which instance we are
        uint256 size;
        assembly { size := extcodesize(0x0000000000000000000000000000000000fffFfF) }
        vm = size == 0;

        // RN instance: subscribe to own events for whitelist sync,
        // then deposit remaining balance into SystemContract as pre-funded reserve.
        if (!vm) {
            service.subscribe(
                block.chainid,
                address(this),
                uint256(keccak256("PoolRegistered(uint256,address)")),
                REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE
            );
            service.subscribe(
                block.chainid,
                address(this),
                uint256(keccak256("PoolUnregistered(uint256,address)")),
                REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE
            );
            // Pre-fund: deposit all remaining balance into SystemContract
            // so subscription costs are drawn from the reserve, not debt.
            depositToSystem(address(this));
        }
    }

    // ── ReactVM entry point ──

    function react(IReactive.LogRecord calldata log) external {
        if (!vm) revert OnlyReactVM();
        processLog(log, address(this), adapter);
    }

    // ── RN instance: pool management ──

    function registerPool(uint256 chainId_, address pool) external {
        if (msg.sender != owner) revert OnlyOwner();
        if (vm) revert OnlyRN();
        subscribeV3Pool(service, chainId_, pool);
        emit PoolRegistered(chainId_, pool);
    }

    function unregisterPool(uint256 chainId_, address pool) external {
        if (msg.sender != owner) revert OnlyOwner();
        if (vm) revert OnlyRN();
        unsubscribeV3Pool(service, chainId_, pool);
        emit PoolUnregistered(chainId_, pool);
    }

    // ── Funding ──

    // Owner can top up the SystemContract reserve at any time.
    function fund() external payable {
        depositToSystem(address(this));
    }

    receive() external payable {
        coverDebt(address(this));
    }
}


// template to fill out with own modules
contract ReactiveShell {
    ISubscriptionService immutable service;

    constructor(address adapter_, address payable service_) payable {}

    modifier onlyVM() {
        requireVM();
        _;
    }
    modifier debtFree() {
        requireSolvency(address(this));
        _;
    }
    function react(IReactive.LogRecord calldata log) external onlyVM() debtFree() {

    }

    receive() external payable { coverDebt(address(this)); }

}
