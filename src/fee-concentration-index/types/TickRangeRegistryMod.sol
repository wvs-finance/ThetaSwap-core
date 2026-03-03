// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {EnumerableSetLib} from "solady/utils/EnumerableSetLib.sol";
import {TickRange} from "./TickRangeMod.sol";
import {SwapCount} from "./SwapCountMod.sol";

// Groups positions by (tickLower, tickUpper) tick range.
// Per-range swap counter enables O(1) lifetime computation at removal.
// Uses solady EnumerableSetLib.Bytes32Set for O(1) add/remove/contains.

struct TickRangeRegistry {
    // TickRange => set of position keys in that range
    mapping(bytes32 => EnumerableSetLib.Bytes32Set) positionsByRange;
    // positionKey => its TickRange (reverse lookup for deregister)
    mapping(bytes32 => TickRange) rangeKeyOf;
    // TickRange => cumulative swap count for this range
    mapping(bytes32 => SwapCount) rangeSwapCount;
    // positionKey => snapshot of rangeSwapCount at add time
    mapping(bytes32 => SwapCount) baselineSwapCount;
}

using TickRangeRegistryLib for TickRangeRegistry global;

library TickRangeRegistryLib {
    using EnumerableSetLib for EnumerableSetLib.Bytes32Set;

    function register(
        TickRangeRegistry storage self,
        TickRange rk,
        bytes32 positionKey
    ) internal {
        self.positionsByRange[TickRange.unwrap(rk)].add(positionKey);
        self.rangeKeyOf[positionKey] = rk;
        self.baselineSwapCount[positionKey] = self.rangeSwapCount[TickRange.unwrap(rk)];
    }

    function deregister(
        TickRangeRegistry storage self,
        bytes32 positionKey
    ) internal returns (TickRange rk, SwapCount lifetime) {
        rk = self.rangeKeyOf[positionKey];
        bytes32 rkRaw = TickRange.unwrap(rk);

        // lifetime = current range count - baseline at add
        SwapCount current = self.rangeSwapCount[rkRaw];
        SwapCount baseline = self.baselineSwapCount[positionKey];
        lifetime = SwapCount.wrap(current.unwrap() - baseline.unwrap());

        self.positionsByRange[rkRaw].remove(positionKey);
        self.rangeKeyOf[positionKey] = TickRange.wrap(bytes32(0));
        self.baselineSwapCount[positionKey] = SwapCount.wrap(0);
    }

    function incrementRangeSwapCount(
        TickRangeRegistry storage self,
        TickRange rk
    ) internal {
        bytes32 rkRaw = TickRange.unwrap(rk);
        self.rangeSwapCount[rkRaw] = self.rangeSwapCount[rkRaw].increment();
    }

    function positionsInRange(
        TickRangeRegistry storage self,
        TickRange rk
    ) internal view returns (bytes32[] memory) {
        return self.positionsByRange[TickRange.unwrap(rk)].values();
    }

    function rangeLength(
        TickRangeRegistry storage self,
        TickRange rk
    ) internal view returns (uint256) {
        return self.positionsByRange[TickRange.unwrap(rk)].length();
    }

    function contains(
        TickRangeRegistry storage self,
        TickRange rk,
        bytes32 positionKey
    ) internal view returns (bool) {
        return self.positionsByRange[TickRange.unwrap(rk)].contains(positionKey);
    }

    function getLifetime(
        TickRangeRegistry storage self,
        bytes32 positionKey
    ) internal view returns (SwapCount) {
        TickRange rk = self.rangeKeyOf[positionKey];
        SwapCount current = self.rangeSwapCount[TickRange.unwrap(rk)];
        SwapCount baseline = self.baselineSwapCount[positionKey];
        return SwapCount.wrap(current.unwrap() - baseline.unwrap());
    }
}
