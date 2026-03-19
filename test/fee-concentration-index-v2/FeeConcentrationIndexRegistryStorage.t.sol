// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    FeeConcentrationIndexRegistryStorage,
    FCI_REGISTRY_SLOT,
    fciRegistryStorage
} from "@fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol";

contract FeeConcentrationIndexRegistryStorageTest is Test {
    function test_slot_disjoint_from_existing() public pure {
        assertTrue(FCI_REGISTRY_SLOT != keccak256("thetaSwap.fci"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("thetaSwap.fci.reactive"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("ReactiveHookAdapter.fci.storage"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("ReactiveHookAdapter.v3.storage"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("thetaSwap.fci.epoch"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("thetaSwap.protocolAdapter.uniswapV4"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("thetaSwap.protocolAdapter.uniswapV3"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("thetaswap.oracle-payoff"));
        assertTrue(FCI_REGISTRY_SLOT != keccak256("thetaswap.collateral-custodian"));
    }

    function test_write_and_read_facet() public {
        FeeConcentrationIndexRegistryStorage storage $ = fciRegistryStorage();
        address facet = address(0xBEEF);
        $.protocolFacets[bytes2(uint16(0x03))] = facet;
        assertEq($.protocolFacets[bytes2(uint16(0x03))], facet);
    }

    function test_different_flags_isolated() public {
        FeeConcentrationIndexRegistryStorage storage $ = fciRegistryStorage();
        $.protocolFacets[bytes2(uint16(0x01))] = address(0xAAAA);
        $.protocolFacets[bytes2(uint16(0x03))] = address(0xBBBB);
        assertEq($.protocolFacets[bytes2(uint16(0x01))], address(0xAAAA));
        assertEq($.protocolFacets[bytes2(uint16(0x03))], address(0xBBBB));
    }
}
