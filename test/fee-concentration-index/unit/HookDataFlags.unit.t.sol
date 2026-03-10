// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    REACTIVE_FLAG, V3_FLAG, V4_FLAG,
    isReactive, isV3, isV4,
    encodeSwapHookData, decodeSwapHookData,
    encodeMintHookData, decodeMintHookData,
    encodeBurnHookData, decodeBurnHookData
} from "../../../src/fee-concentration-index/types/HookDataFlagsMod.sol";

contract HookDataFlagsTest is Test {
    function test_flagConstants_areSingleBits() public pure {
        assertEq(REACTIVE_FLAG, 0x01);
        assertEq(V3_FLAG, 0x02);
        assertEq(V4_FLAG, 0x00);
    }

    function test_flagChecks_composable() public pure {
        uint8 reactiveV3 = REACTIVE_FLAG | V3_FLAG; // 0x03
        assertTrue(isReactive(reactiveV3));
        assertTrue(isV3(reactiveV3));
        assertFalse(isV4(reactiveV3));
    }

    function test_swapHookData_roundtrip() public pure {
        uint8 flags = REACTIVE_FLAG | V3_FLAG;
        int24 tickBefore = -42;
        int24 tickAfter = 17;
        bytes memory encoded = encodeSwapHookData(flags, tickBefore, tickAfter);
        (uint8 f, int24 tb, int24 ta) = decodeSwapHookData(encoded);
        assertEq(f, flags);
        assertEq(tb, tickBefore);
        assertEq(ta, tickAfter);
    }

    function test_mintHookData_roundtrip() public pure {
        uint8 flags = REACTIVE_FLAG | V3_FLAG;
        address owner = address(0xBEEF);
        int24 tickLower = -60;
        int24 tickUpper = 60;
        uint128 liquidity = 10000;
        bytes memory encoded = encodeMintHookData(flags, owner, tickLower, tickUpper, liquidity);
        (uint8 f, address o, int24 tl, int24 tu, uint128 liq) = decodeMintHookData(encoded);
        assertEq(f, flags);
        assertEq(o, owner);
        assertEq(tl, tickLower);
        assertEq(tu, tickUpper);
        assertEq(liq, liquidity);
    }

    function test_burnHookData_roundtrip() public pure {
        uint8 flags = REACTIVE_FLAG | V3_FLAG;
        address owner = address(0xCAFE);
        int24 tickLower = -120;
        int24 tickUpper = 120;
        uint128 liquidity = 5000;
        bytes memory encoded = encodeBurnHookData(flags, owner, tickLower, tickUpper, liquidity);
        (uint8 f, address o, int24 tl, int24 tu, uint128 liq) = decodeBurnHookData(encoded);
        assertEq(f, flags);
        assertEq(o, owner);
        assertEq(tl, tickLower);
        assertEq(tu, tickUpper);
        assertEq(liq, liquidity);
    }

    function test_emptyHookData_isNotReactive() public pure {
        assertFalse(isReactive(0));
        assertFalse(isV3(0));
        assertTrue(isV4(0)); // flags=0 means V4 (default)
    }

    function testFuzz_swapHookData_roundtrip(uint8 flags, int24 tickBefore, int24 tickAfter) public pure {
        bytes memory encoded = encodeSwapHookData(flags, tickBefore, tickAfter);
        (uint8 f, int24 tb, int24 ta) = decodeSwapHookData(encoded);
        assertEq(f, flags);
        assertEq(tb, tickBefore);
        assertEq(ta, tickAfter);
    }

    function testFuzz_mintHookData_roundtrip(uint8 flags, address owner, int24 tickLower, int24 tickUpper, uint128 liquidity) public pure {
        bytes memory encoded = encodeMintHookData(flags, owner, tickLower, tickUpper, liquidity);
        (uint8 f, address o, int24 tl, int24 tu, uint128 liq) = decodeMintHookData(encoded);
        assertEq(f, flags);
        assertEq(o, owner);
        assertEq(tl, tickLower);
        assertEq(tu, tickUpper);
        assertEq(liq, liquidity);
    }
}
