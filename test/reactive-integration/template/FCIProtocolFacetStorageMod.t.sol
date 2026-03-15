// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {BlockCount} from "typed-uniswap-v4/fee-concentration-index/types/BlockCountMod.sol";
import {FeeConcentrationIndexStorage, FCI_STORAGE_SLOT} from "@fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {
    protocolFciStorage,
    protocolEpochFciStorage,
    tstoreTick,
    tloadTick,
    tstoreRemovalData,
    tloadRemovalData
} from "@fee-concentration-index-v2/modules/FCIProtocolFacetStorageMod.sol";

contract FCIProtocolFacetStorageModTest is Test {
    function test_different_flags_different_slots() public {
        FeeConcentrationIndexStorage storage a = protocolFciStorage(bytes1(0x03));
        FeeConcentrationIndexStorage storage b = protocolFciStorage(bytes1(0x01));
        PoolId poolId = PoolId.wrap(bytes32(uint256(1)));
        a.fciState[poolId].addTerm(BlockCount.wrap(1), 1e18);
        assertEq(b.fciState[poolId].thetaSum, 0);
    }

    function test_protocol_slot_disjoint_from_v4() public pure {
        bytes32 v4Slot = FCI_STORAGE_SLOT;
        bytes32 v3Slot = keccak256(abi.encode("thetaSwap.fci", bytes1(0x03)));
        assertTrue(v4Slot != v3Slot);
    }

    function test_tstoreTick_tloadTick_roundtrip() public {
        tstoreTick(bytes1(0x03), -12345);
        assertEq(tloadTick(bytes1(0x03)), -12345);
    }

    function test_tstoreRemovalData_tloadRemovalData_roundtrip() public {
        tstoreRemovalData(bytes1(0x03), 999, 42, 777);
        (uint256 f, uint128 l, uint256 r) = tloadRemovalData(bytes1(0x03));
        assertEq(f, 999);
        assertEq(l, 42);
        assertEq(r, 777);
    }

    function test_transient_slots_isolated_by_flag() public {
        tstoreTick(bytes1(0x01), 100);
        tstoreTick(bytes1(0x03), -200);
        assertEq(tloadTick(bytes1(0x01)), 100);
        assertEq(tloadTick(bytes1(0x03)), -200);
    }
}
