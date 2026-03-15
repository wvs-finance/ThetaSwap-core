// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId} from "v4-core/src/types/PoolId.sol";
import {EnumerableSet} from "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {IUnlockCallback} from "v4-core/src/interfaces/callback/IUnlockCallback.sol";

struct FCIFacetAdminStorage {
    EnumerableSet.Bytes32Set poolIds;
    IFeeConcentrationIndex fci;
    IProtocolStateView protocolStateView;
    IUnlockCallback protocolCallback;
}

// Placeholder — protocols MUST define their own PROTOCOL_FLAG constant.
bytes2 constant PROTOCOL_FLAG = bytes2(keccak256("thetaSwap.protocolId"));

function fciFacetAdminStorage(bytes1 flag) pure returns (FCIFacetAdminStorage storage $) {
    bytes32 position = keccak256(abi.encode("thetaSwap.fci.facetAdmin", flag));
    assembly ("memory-safe") { $.slot := position }
}

function setProtocolCallback(bytes1 flag, IUnlockCallback protocolCallback) {
    fciFacetAdminStorage(flag).protocolCallback = protocolCallback;
}

function getProtocolCallback(bytes1 flag) view returns (IUnlockCallback) {
    return fciFacetAdminStorage(flag).protocolCallback;
}

function addPool(bytes1 flag, PoolId poolId) {
    EnumerableSet.add(fciFacetAdminStorage(flag).poolIds, PoolId.unwrap(poolId));
}
