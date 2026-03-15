// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";

struct FeeConcentrationIndexRegistryStorage {
    mapping(bytes1 => address) protocolFacets;
}

bytes32 constant FCI_REGISTRY_SLOT = keccak256("thetaSwap.fci.registry");

function fciRegistryStorage() pure returns (FeeConcentrationIndexRegistryStorage storage $) {
    bytes32 slot = FCI_REGISTRY_SLOT;
    assembly ("memory-safe") { $.slot := slot }
}

function setProtocolFacet(bytes1 flag, IFCIProtocolFacet protocolFacet) {
    fciRegistryStorage().protocolFacets[flag] = address(protocolFacet);
}

function getProtocolFacet(bytes1 flag) view returns (IFCIProtocolFacet) {
    return IFCIProtocolFacet(fciRegistryStorage().protocolFacets[flag]);
}
