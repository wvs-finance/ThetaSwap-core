// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";
import {CalldataReader, CalldataReaderLib} from "angstrom/src/types/CalldataReader.sol";
import {NATIVE_V4} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";

struct FeeConcentrationIndexRegistryStorage {
    mapping(bytes2 => address) protocolFacets;
}

bytes32 constant FCI_REGISTRY_SLOT = keccak256("thetaSwap.fci.registry");

function fciRegistryStorage() pure returns (FeeConcentrationIndexRegistryStorage storage $) {
    bytes32 slot = FCI_REGISTRY_SLOT;
    assembly ("memory-safe") { $.slot := slot }
}

function setProtocolFacet(bytes2 flag, IFCIProtocolFacet protocolFacet) {
    fciRegistryStorage().protocolFacets[flag] = address(protocolFacet);
}

function getProtocolFacet(bytes2 flag) view returns (IFCIProtocolFacet) {
    return IFCIProtocolFacet(fciRegistryStorage().protocolFacets[flag]);
}

/// @dev Reads the protocol flag from hookData. The flag occupies the first 2 bytes
/// at a deterministic position. Empty hookData returns NATIVE_V4 (0xFFFF).
function getProtocolFlagFromHookData(bytes calldata hookData) pure returns (bytes2 flag) {
    if (hookData.length == 0) return NATIVE_V4;
    CalldataReader reader = CalldataReaderLib.from(hookData);
    uint16 raw;
    (reader, raw) = reader.readU16();
    flag = bytes2(raw);
}
