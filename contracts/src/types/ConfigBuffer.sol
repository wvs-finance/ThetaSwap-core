// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {ConfigEntry, ENTRY_SIZE} from "./ConfigEntry.sol";
import {StoreKey} from "./StoreKey.sol";

struct ConfigBuffer {
    ConfigEntry[] entries;
    uint256 capacity;
}

using ConfigBufferLib for ConfigBuffer global;

/// @author philogy <https://github.com/philogy>
library ConfigBufferLib {
    error InsufficientCapacity();
    error EntryKeyMismatch();

    function get(ConfigBuffer memory self, StoreKey key, uint256 index)
        internal
        pure
        returns (ConfigEntry entry)
    {
        entry = self.entries[index];
        if (entry.key() != key) revert EntryKeyMismatch();
        return entry;
    }

    /// @dev Allocate memory for `capacity` entries and resets le
    function reset_and_alloc_capacity(ConfigBuffer memory self, uint256 capacity) internal pure {
        self.capacity = capacity;
        assembly ("memory-safe") {
            // Alloc entry space.
            let entries := mload(0x40)
            mstore(0x40, add(entries, add(mul(capacity, ENTRY_SIZE), 0x20)))
            // Set  default length to 0.
            mstore(entries, 0)
            // Set ptr `self.entries`.
            mstore(self, entries)
        }
    }

    function remove_entry(ConfigBuffer memory self, StoreKey key, uint256 index) internal pure {
        if (self.entries[index].key() != key) revert EntryKeyMismatch();

        uint256 newLength = self.entries.length - 1;
        if (index < newLength) {
            self.entries[index] = self.entries[newLength];
        }
        // Set new length to `length - 1`.
        unsafe_resize(self, newLength);
    }

    /// @dev Add a new entry to the store. WARNING: Responsibility of caller to ensure that `entry`
    /// does *not* contain a duplicate key otherwise key uniqueness invariant will be broken.
    function unsafe_add(ConfigBuffer memory self, ConfigEntry entry) internal pure {
        uint256 prev_length = self.entries.length;
        if (prev_length == self.capacity) revert InsufficientCapacity();

        unsafe_resize(self, prev_length + 1);
        self.entries[prev_length] = entry;
    }

    /// @dev Sets the length of the buffer to an arbitrary length `new_length`. WARNING:
    /// Responsibility of the caller to ensure that the length is either being *decreased* from a
    /// valid length or increased at most to the capacity and only to contain valid entries.
    function unsafe_resize(ConfigBuffer memory self, uint256 new_length) internal pure {
        ConfigEntry[] memory entries = self.entries;
        assembly ("memory-safe") {
            mstore(entries, new_length)
        }
    }
}
