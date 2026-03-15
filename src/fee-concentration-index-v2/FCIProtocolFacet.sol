// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {
    FCIFacetAdminStorage,
    fciFacetAdminStorage,
    addPool,
    getProtocolCallback,
    PROTOCOL_FLAG
} from "@fee-concentration-index-v2/modules/FCIFacetAdminStorageMod.sol";
import {fromPoolRptToPoolKey} from "@fee-concentration-index-v2/libraries/PoolKeyExtLib.sol";

contract FCIProtocolFacet {

    event PoolAdded(address indexed facet, address indexed callback, PoolId indexed poolId, bytes2 protocolFlag);

    /// @notice Register a pool for FCI tracking.
    /// @dev fromPoolRptToPoolKey is to be written per protocol semantics —
    /// each protocol defines how to decode poolRpt into a PoolKey.
    function listen(bytes calldata poolRpt) payable external returns (PoolKey memory poolKey) {
        IHooks fciHook = IHooks(address(fciFacetAdminStorage(PROTOCOL_FLAG).fci));
        poolKey = fromPoolRptToPoolKey(poolRpt, fciHook);
        PoolId poolId = PoolIdLibrary.toId(poolKey);
        addPool(PROTOCOL_FLAG, poolId);
        emit PoolAdded(address(this), address(getProtocolCallback(PROTOCOL_FLAG)), poolId, PROTOCOL_FLAG);
    }
}
