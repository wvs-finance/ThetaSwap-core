// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {ISubscriptionService} from "reactive-lib/interfaces/ISubscriptionService.sol";
import {coverDebt, depositToSystem} from "reactive-hooks/modules/DebtMod.sol";
import {SYSTEM_CONTRACT} from "reactive-hooks/libraries/DebtLib.sol";
import {requireVM, reactVmStorage} from "reactive-hooks/modules/ReactVMMod.sol";
import {ReactVm} from "reactive-hooks/types/ReactVM.sol";
import {REACTIVE_IGNORE} from "reactive-hooks/libraries/SubscriptionLib.sol";
import {POOL_ADDED_SIG} from "@fee-concentration-index-v2/libraries/PoolAddedSig.sol";
import {UNISWAP_V3_REACTIVE} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";
import {V3_SWAP_SIG, V3_MINT_SIG, V3_BURN_SIG} from "./libraries/EventSignatures.sol";
import {decodeV3PoolAddedData} from "./libraries/UniswapV3PoolAddedLib.sol";
import {mutateV3Payload} from "./libraries/UniswapV3PayloadMutatorLib.sol";

uint64 constant CALLBACK_GAS_LIMIT = 1_000_000;

/// @title UniswapV3Reactive
/// @dev Reactive Network contract for V3 reactive integration.
/// Dual-instance: RN subscribes to PoolAdded from facet on origin chain,
/// ReactVM auto-subscribes to V3 pool events + forwards to callback.
/// Light pattern — no EDT, direct subscribe + emit Callback.
contract UniswapV3Reactive {
    ISubscriptionService immutable service;

    // Stored on PoolAdded — callback target on destination chain
    address callbackTarget;

    constructor(uint256 originChainId, address facetAddress) payable {
        service = ISubscriptionService(SYSTEM_CONTRACT);

        // Initialize ReactVM storage for requireVM() checks
        uint256 size;
        assembly { size := extcodesize(0x0000000000000000000000000000000000fffFfF) }
        reactVmStorage().reactVm = ReactVm.wrap(size == 0);

        // RN instance: subscribe to PoolAdded from facet on origin chain
        if (size > 0) {
            service.subscribe(originChainId, facetAddress, POOL_ADDED_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
            depositToSystem(address(this));
        }
    }

    function react(IReactive.LogRecord calldata log) external {
        requireVM();

        if (log.topic_0 == POOL_ADDED_SIG) {
            _handlePoolAdded(log);
            return;
        }

        // Forward V3 event to callback with enriched payload
        emit IReactive.Callback(
            log.chain_id, callbackTarget, CALLBACK_GAS_LIMIT,
            abi.encodeWithSignature(
                "unlockCallbackReactive(address,bytes)",
                address(0),
                mutateV3Payload(log)
            )
        );
    }

    function _handlePoolAdded(IReactive.LogRecord calldata log) internal {
        (bytes2 protocolFlag, bytes memory poolData) = abi.decode(log.data, (bytes2, bytes));
        if (protocolFlag != UNISWAP_V3_REACTIVE) return;

        // Store callback target from event topic_2
        callbackTarget = address(uint160(log.topic_2));

        // Decode pool address + chain from pool data
        (uint256 chainId, address pool,) = decodeV3PoolAddedData(poolData);

        // Subscribe to V3 pool events — direct calls, no EDT overhead
        service.subscribe(chainId, pool, V3_SWAP_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        service.subscribe(chainId, pool, V3_MINT_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        service.subscribe(chainId, pool, V3_BURN_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    }

    function fund() external payable {
        depositToSystem(address(this));
    }

    receive() external payable {
        coverDebt(address(this));
    }
}
