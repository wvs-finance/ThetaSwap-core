// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {EnumerableSetLib} from "solady/utils/EnumerableSetLib.sol";
import {TickRange} from "./TickRangeMod.sol";
import {SwapCount} from "./SwapCountMod.sol";
import {BlockCount} from "./BlockCountMod.sol";

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
    // All range keys with >= 1 position (for afterSwap iteration)
    EnumerableSetLib.Bytes32Set activeRanges;
    // Recover tick bounds from one-way TickRange hash (for intersects check)
    mapping(bytes32 => int24) rangeLowerTick;
    mapping(bytes32 => int24) rangeUpperTick;
    // TickRange => sum of liquidity across all positions in range (for x_k weighting)
    mapping(bytes32 => uint128) totalRangeLiquidity;
    // positionKey => block.number at registration (for block-based lifetime)
    mapping(bytes32 => uint256) positionAddBlock;
}

using TickRangeRegistryLib for TickRangeRegistry global;

library TickRangeRegistryLib {
    using EnumerableSetLib for EnumerableSetLib.Bytes32Set;

    function register(
        TickRangeRegistry storage self,
        TickRange rk,
        bytes32 positionKey,
        int24 tickLower,
        int24 tickUpper,
        uint128 posLiquidity
    ) internal {
        bytes32 rkRaw = TickRange.unwrap(rk);
        self.positionsByRange[rkRaw].add(positionKey);
        self.rangeKeyOf[positionKey] = rk;
        self.baselineSwapCount[positionKey] = self.rangeSwapCount[rkRaw];
        self.totalRangeLiquidity[rkRaw] += posLiquidity;
        self.positionAddBlock[positionKey] = block.number;

        // First position in this range: track for afterSwap iteration
        if (self.positionsByRange[rkRaw].length() == 1) {
            self.activeRanges.add(rkRaw);
            self.rangeLowerTick[rkRaw] = tickLower;
            self.rangeUpperTick[rkRaw] = tickUpper;
        }
    }

    function deregister(
        TickRangeRegistry storage self,
        bytes32 positionKey,
        uint128 /* posLiquidity */
    ) internal returns (TickRange rk, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalLiquidityBefore) {
        rk = self.rangeKeyOf[positionKey];
        bytes32 rkRaw = TickRange.unwrap(rk);

        // Swap lifetime (for zero-check)
        SwapCount current = self.rangeSwapCount[rkRaw];
        SwapCount baseline = self.baselineSwapCount[positionKey];
        swapLifetime = SwapCount.wrap(current.unwrap() - baseline.unwrap());

        // Block lifetime (for HHI divisor)
        blockLifetime = BlockCount.wrap(block.number - self.positionAddBlock[positionKey]);

        // Read total liquidity (used for x_k computation denominator).
        // NOT decremented per-position: all positions that overlapped the same swaps
        // should see the same denominator to get correct fee shares.
        // Cleaned up only when the range is fully empty.
        totalLiquidityBefore = self.totalRangeLiquidity[rkRaw];

        self.positionsByRange[rkRaw].remove(positionKey);
        self.rangeKeyOf[positionKey] = TickRange.wrap(bytes32(0));
        self.baselineSwapCount[positionKey] = SwapCount.wrap(0);
        delete self.positionAddBlock[positionKey];

        // Last position removed: clean up range tracking (INV-005)
        if (self.positionsByRange[rkRaw].length() == 0) {
            self.activeRanges.remove(rkRaw);
            delete self.rangeLowerTick[rkRaw];
            delete self.rangeUpperTick[rkRaw];
            self.rangeSwapCount[rkRaw] = SwapCount.wrap(0);
            self.totalRangeLiquidity[rkRaw] = 0;
        }
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

    function activeRangeCount(
        TickRangeRegistry storage self
    ) internal view returns (uint256) {
        return self.activeRanges.length();
    }

    function activeRangeAt(
        TickRangeRegistry storage self,
        uint256 index
    ) internal view returns (bytes32) {
        return self.activeRanges.at(index);
    }
}
