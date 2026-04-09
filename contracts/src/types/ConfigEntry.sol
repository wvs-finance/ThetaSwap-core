// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {StoreKey} from "./StoreKey.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";

/// @dev Packed `storeKey:u216 ++ tickSpacing:u16 ++ feeInE6:u24`
type ConfigEntry is uint256;

uint256 constant ENTRY_SIZE = 32;
uint256 constant KEY_MASK = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000;
uint256 constant TICK_SPACING_MASK = 0xffff;
uint256 constant TICK_SPACING_OFFSET = 24;
uint256 constant FEE_MASK = 0xffffff;
uint256 constant FEE_OFFSET = 0;

/// @dev Max bundle fee.
uint24 constant MAX_FEE = 0.2e6;
/// @dev 100% fee in `bundleFee` units (pips).
uint24 constant ONE_E6 = 1.0e6;

using ConfigEntryLib for ConfigEntry global;

/// @author philogy <https://github.com/philogy>
library ConfigEntryLib {
    error InvalidTickSpacing();
    error FeeAboveMax();

    function isEmpty(ConfigEntry self) internal pure returns (bool) {
        return ConfigEntry.unwrap(self) == 0;
    }

    function init(StoreKey skey, uint16 spacing, uint24 fee) internal pure returns (ConfigEntry) {
        _checkTickSpacing(spacing);
        _checkBundleFee(fee);
        // forgefmt: disable-next-item
        return ConfigEntry.wrap(uint256(bytes32(StoreKey.unwrap(skey))))
            .setTickSpacing(spacing)
            .setBundleFee(fee);
    }

    function key(ConfigEntry self) internal pure returns (StoreKey) {
        return StoreKey.wrap(bytes27(bytes32(ConfigEntry.unwrap(self))));
    }

    uint256 internal constant MIN_TICK_SPACING = uint24(TickMath.MIN_TICK_SPACING);
    uint256 internal constant MAX_TICK_SPACING = uint24(TickMath.MAX_TICK_SPACING);

    function setTickSpacing(ConfigEntry self, uint16 spacing)
        internal
        pure
        returns (ConfigEntry updated)
    {
        _checkTickSpacing(spacing);
        uint256 backing = ConfigEntry.unwrap(self);
        uint256 xoredSpacing = spacing ^ uint24(self.tickSpacing());
        updated = ConfigEntry.wrap(backing ^ (xoredSpacing << TICK_SPACING_OFFSET));
        return updated;
    }

    function tickSpacing(ConfigEntry self) internal pure returns (uint16 spacing) {
        assembly ("memory-safe") {
            spacing := and(TICK_SPACING_MASK, shr(TICK_SPACING_OFFSET, self))
        }
    }

    function setBundleFee(ConfigEntry self, uint24 fee)
        internal
        pure
        returns (ConfigEntry updated)
    {
        _checkBundleFee(fee);
        uint256 backing = ConfigEntry.unwrap(self);
        uint256 xoredFee = fee ^ self.bundleFee();
        updated = ConfigEntry.wrap(backing ^ (xoredFee << FEE_OFFSET));
        return updated;
    }

    function bundleFee(ConfigEntry self) internal pure returns (uint24 fee) {
        assembly ("memory-safe") {
            fee := and(FEE_MASK, shr(FEE_OFFSET, self))
        }
    }

    function _checkTickSpacing(uint16 spacing) internal pure {
        if (spacing < MIN_TICK_SPACING || spacing > MAX_TICK_SPACING) {
            revert InvalidTickSpacing();
        }
    }

    function _checkBundleFee(uint24 fee) internal pure {
        if (fee > MAX_FEE) revert FeeAboveMax();
    }
}
