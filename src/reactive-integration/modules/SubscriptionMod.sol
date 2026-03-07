// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {ISubscriptionService} from "reactive-lib/interfaces/ISubscriptionService.sol";
import {V3_SWAP_SIG, V3_MINT_SIG, V3_BURN_SIG, V3_COLLECT_SIG} from "../types/V3EventDecoderMod.sol";

uint256 constant REACTIVE_IGNORE = 0xa65f96fc951c35ead38878e0f0b7a3c744a6f5ccc1476b313353ce31712313ad;

// Subscribe to all 4 V3 event types for a given pool on a given chain.
function subscribeV3Pool(
    ISubscriptionService service,
    uint256 chainId_,
    address pool
) {
    service.subscribe(chainId_, pool, V3_SWAP_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    service.subscribe(chainId_, pool, V3_MINT_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    service.subscribe(chainId_, pool, V3_BURN_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    service.subscribe(chainId_, pool, V3_COLLECT_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
}

// Unsubscribe from all 4 V3 event types for a given pool.
function unsubscribeV3Pool(
    ISubscriptionService service,
    uint256 chainId_,
    address pool
) {
    service.unsubscribe(chainId_, pool, V3_SWAP_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    service.unsubscribe(chainId_, pool, V3_MINT_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    service.unsubscribe(chainId_, pool, V3_BURN_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    service.unsubscribe(chainId_, pool, V3_COLLECT_SIG, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
}
