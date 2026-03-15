// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";

/// @title IFCIProtocolAdmin
/// @dev Called directly on the facet contract (NOT via delegatecall from FCI).
/// Separated from IFCIProtocolFacet to prevent mixing call contexts.
interface IFCIProtocolAdmin {
    function listen(bytes calldata poolRpt) payable external returns (PoolKey memory poolKey);
}
