// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

/// @dev Left shift in bits to convert the full hash `keccak256(abi.encode(asset0, asset1))` to a store key.
uint256 constant HASH_TO_STORE_KEY_SHIFT = 40;

type StoreKey is bytes27;

using StoreKeyLib for StoreKey global;
using {StoreKey_eq as ==, StoreKey_neq as !=} for StoreKey global;

function StoreKey_eq(StoreKey a, StoreKey b) pure returns (bool) {
    return StoreKey.unwrap(a) == StoreKey.unwrap(b);
}

function StoreKey_neq(StoreKey a, StoreKey b) pure returns (bool) {
    return StoreKey.unwrap(a) != StoreKey.unwrap(b);
}

/// @author philogy <https://github.com/philogy>
library StoreKeyLib {
    /// @dev Computes the `StoreKey` from the inputs. WARN: Does not check that the assets are
    /// sorted and in unique order.
    function keyFromAssetsUnchecked(address asset0, address asset1)
        internal
        pure
        returns (StoreKey key)
    {
        assembly ("memory-safe") {
            mstore(0x00, asset0)
            mstore(0x20, asset1)
            key := shl(HASH_TO_STORE_KEY_SHIFT, keccak256(0x00, 0x40))
        }
    }
}
