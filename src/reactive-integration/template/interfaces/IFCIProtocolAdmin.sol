// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";

/// @title IFCIProtocolAdmin
/// @dev Called directly on the facet contract (NOT via delegatecall from FCI).
/// Separated from IFCIProtocolFacet to prevent mixing call contexts.
interface IFCIProtocolAdmin {
    function initialize(address _owner, IProtocolStateView _protocolStateView, IFeeConcentrationIndex _fci) external;
    function listen(bytes calldata poolRpt) payable external returns (PoolKey memory poolKey);
    function setProtocolStateView(IProtocolStateView stateView) external;
}
