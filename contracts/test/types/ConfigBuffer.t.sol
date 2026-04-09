// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import "forge-std/Test.sol";
import {StoreKey, StoreKeyLib, HASH_TO_STORE_KEY_SHIFT} from "src/types/StoreKey.sol";
import {ConfigEntry, ConfigEntryLib, MAX_FEE} from "src/types/ConfigEntry.sol";
import {ConfigBuffer, ConfigBufferLib} from "src/types/ConfigBuffer.sol";
import {BaseTest} from "test/_helpers/BaseTest.sol";
import {PRNG} from "solady/src/utils/g/LibPRNG.sol";

contract ConfigBufferTest is BaseTest {
    using ConfigEntryLib for ConfigEntry;
    using StoreKeyLib for StoreKey;
    using ConfigBufferLib for ConfigBuffer;

    // Test addresses for creating StoreKeys
    address internal constant ASSET0 = address(0x1);
    address internal constant ASSET1 = address(0x2);
    address internal constant ASSET2 = address(0x3);
    address internal constant ASSET3 = address(0x4);

    function testUnsafeAllocUninit() public pure {
        ConfigBuffer memory buffer;
        uint256 capacity = 10;

        buffer.reset_and_alloc_capacity(capacity);

        assertEq(buffer.capacity, capacity, "Capacity not set correctly");
        assertEq(buffer.entries.length, 0, "Initial length should be 0");
    }

    function testPushEntry() public pure {
        ConfigBuffer memory buffer;
        uint256 capacity = 5;
        buffer.reset_and_alloc_capacity(capacity);

        StoreKey key = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET1);
        ConfigEntry entry = ConfigEntryLib.init(key, 10, 3000);

        buffer.unsafe_add(entry);

        assertEq(buffer.entries.length, 1, "Entry not added");
        assertEq(buffer.entries[0].key(), key, "Key not matching");
        assertEq(buffer.entries[0].tickSpacing(), 10, "Tick spacing not matching");
        assertEq(buffer.entries[0].bundleFee(), 3000, "Fee not matching");
    }

    function testPushDuplicationUnchecked() public pure {
        ConfigBuffer memory buffer;
        uint256 capacity = 5;
        buffer.reset_and_alloc_capacity(capacity);

        StoreKey key = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET1);
        ConfigEntry entry1 = ConfigEntryLib.init(key, 10, 3000);
        ConfigEntry entry2 = ConfigEntryLib.init(key, 20, 5000);

        buffer.unsafe_add(entry1);
        buffer.unsafe_add(entry2);

        assertEq(buffer.entries.length, 2, "Entries not added");
        assertEq(buffer.entries[0].key(), key, "First entry key not matching");
        assertEq(buffer.entries[1].key(), key, "Second entry key not matching");
    }

    /// forge-config: default.allow_internal_expect_revert = true
    function testPushInsufficientCapacity() public {
        ConfigBuffer memory buffer;
        uint256 capacity = 1;
        buffer.reset_and_alloc_capacity(capacity);

        StoreKey key1 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET1);
        StoreKey key2 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET2);
        ConfigEntry entry1 = ConfigEntryLib.init(key1, 10, 3000);
        ConfigEntry entry2 = ConfigEntryLib.init(key2, 20, 5000);

        buffer.unsafe_add(entry1);

        vm.expectRevert(ConfigBufferLib.InsufficientCapacity.selector);
        buffer.unsafe_add(entry2);
    }

    function testRemoveEntryFirst() public pure {
        ConfigBuffer memory buffer;
        uint256 capacity = 3;
        buffer.reset_and_alloc_capacity(capacity);

        StoreKey key1 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET1);
        StoreKey key2 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET2);
        StoreKey key3 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET3);
        ConfigEntry entry1 = ConfigEntryLib.init(key1, 10, 3000);
        ConfigEntry entry2 = ConfigEntryLib.init(key2, 20, 5000);
        ConfigEntry entry3 = ConfigEntryLib.init(key3, 30, 7000);

        buffer.unsafe_add(entry1);
        buffer.unsafe_add(entry2);
        buffer.unsafe_add(entry3);

        buffer.remove_entry(key1, 0);

        assertEq(buffer.entries.length, 2, "Entry not removed");
        assertEq(buffer.entries[0].key(), key3, "Last entry should be moved to first position");
        assertEq(buffer.entries[1].key(), key2, "Second entry should not be moved");
    }

    function testRemoveEntryMiddle() public pure {
        ConfigBuffer memory buffer;
        uint256 capacity = 3;
        buffer.reset_and_alloc_capacity(capacity);

        StoreKey key1 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET1);
        StoreKey key2 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET2);
        StoreKey key3 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET3);
        ConfigEntry entry1 = ConfigEntryLib.init(key1, 10, 3000);
        ConfigEntry entry2 = ConfigEntryLib.init(key2, 20, 5000);
        ConfigEntry entry3 = ConfigEntryLib.init(key3, 30, 7000);

        buffer.unsafe_add(entry1);
        buffer.unsafe_add(entry2);
        buffer.unsafe_add(entry3);

        buffer.remove_entry(key2, 1);

        assertEq(buffer.entries.length, 2, "Entry not removed");
        assertEq(buffer.entries[0].key(), key1, "First entry should not be moved");
        assertEq(buffer.entries[1].key(), key3, "Last entry should be moved to middle position");
    }

    function testRemoveEntryLast() public pure {
        ConfigBuffer memory buffer;
        uint256 capacity = 3;
        buffer.reset_and_alloc_capacity(capacity);

        StoreKey key1 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET1);
        StoreKey key2 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET2);
        StoreKey key3 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET3);
        ConfigEntry entry1 = ConfigEntryLib.init(key1, 10, 3000);
        ConfigEntry entry2 = ConfigEntryLib.init(key2, 20, 5000);
        ConfigEntry entry3 = ConfigEntryLib.init(key3, 30, 7000);

        buffer.unsafe_add(entry1);
        buffer.unsafe_add(entry2);
        buffer.unsafe_add(entry3);

        buffer.remove_entry(key3, 2);

        assertEq(buffer.entries.length, 2, "Entry not removed");
        assertEq(buffer.entries[0].key(), key1, "First entry should not be moved");
        assertEq(buffer.entries[1].key(), key2, "Second entry should not be moved");
    }

    /// forge-config: default.allow_internal_expect_revert = true
    function testRemoveEntryKeyMismatch() public {
        ConfigBuffer memory buffer;
        uint256 capacity = 3;
        buffer.reset_and_alloc_capacity(capacity);

        StoreKey key1 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET1);
        StoreKey key2 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET2);
        ConfigEntry entry1 = ConfigEntryLib.init(key1, 10, 3000);

        buffer.unsafe_add(entry1);

        vm.expectRevert(ConfigBufferLib.EntryKeyMismatch.selector);
        buffer.remove_entry(key2, 0);
    }

    function testUnsafeSetLength() public pure {
        ConfigBuffer memory buffer;
        uint256 capacity = 5;
        buffer.reset_and_alloc_capacity(capacity);

        StoreKey key = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET1);
        ConfigEntry entry = ConfigEntryLib.init(key, 10, 3000);

        buffer.unsafe_add(entry);
        assertEq(buffer.entries.length, 1, "Entry not added");

        buffer.unsafe_resize(0);
        assertEq(buffer.entries.length, 0, "Length not set to 0");
    }

    function test_fuzzing_UnsafeAllocUninit(uint256 capacity) public pure {
        // Limit capacity to avoid out-of-gas errors
        capacity = bound(capacity, 0, 1000);

        ConfigBuffer memory buffer;
        buffer.reset_and_alloc_capacity(capacity);

        assertEq(buffer.capacity, capacity, "Capacity not set correctly");
        assertEq(buffer.entries.length, 0, "Initial length should be 0");
    }

    function test_fuzzing_PushAndRemoveEntries(uint16 tickSpacing, uint24 fee) public pure {
        unchecked {
            ConfigBuffer memory buffer;
            uint256 capacity = 10;
            buffer.reset_and_alloc_capacity(capacity);

            StoreKey key1 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET1);
            StoreKey key2 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET2);
            StoreKey key3 = StoreKeyLib.keyFromAssetsUnchecked(ASSET0, ASSET3);

            ConfigEntry entry1 =
                ConfigEntryLib.init(key1, boundTickSpacing(tickSpacing), boundE6(fee, MAX_FEE));
            ConfigEntry entry2 = ConfigEntryLib.init(
                key2, boundTickSpacing(tickSpacing + 1), boundE6(fee + 1000, MAX_FEE)
            );
            ConfigEntry entry3 = ConfigEntryLib.init(
                key3, boundTickSpacing(tickSpacing + 2), boundE6(fee + 2000, MAX_FEE)
            );

            buffer.unsafe_add(entry1);
            buffer.unsafe_add(entry2);
            buffer.unsafe_add(entry3);

            assertEq(buffer.entries.length, 3, "Entries not added");

            buffer.remove_entry(key2, 1);

            assertEq(buffer.entries.length, 2, "Entry not removed");
            assertEq(buffer.entries[0].key(), key1, "First entry should remain unchanged");
            assertEq(buffer.entries[1].key(), key3, "Last entry should be moved to middle position");
        }
    }
}
