// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {BaseForkTest} from "anstrong-test/_helpers/BaseForkTest.t.sol";
import {GrowthObservation, newGrowthObservation} from "core/src/types/GrowthObservation.sol";
import {
    AccumulatorRow,
    lenArgs,
    rowArgs,
    decodeLen,
    decodeRow
} from "anstrong-test/_ffi_utils/ffiLib.sol";

contract GrowthObservationDifferentialTest is BaseForkTest {
    uint256 constant FIRST_OBSERVATION_TIME_DELTA = 0;

    function setUp() public override {
        super.setUp();
        if (!forked) return;
    }

    function test__fuzzDifferential__PackRoundTripBitPackingSuccess(uint256 idxSeed) public onlyForked {
        uint256 n = decodeLen(ffiPython(lenArgs()));
        uint256 idx = bound(idxSeed, 0, n - 1);
        AccumulatorRow memory row = decodeRow(ffiPython(rowArgs(vm, idx)));

        GrowthObservation obs = newGrowthObservation(
            row.blockNumber,
            FIRST_OBSERVATION_TIME_DELTA,
            row.globalGrowth
        );

        assertEq(uint256(obs.blockNumber()), row.blockNumber, "blockNumber");
        assertEq(uint256(obs.relativeTimeDelta()), FIRST_OBSERVATION_TIME_DELTA, "relativeTimeDelta");
        assertEq(uint256(obs.cumulativeGrowth()), row.globalGrowth, "cumulativeGrowth");
    }

    function test__fuzzDifferential__GrowthDeltaMatchesRawSubtraction(uint256 idxSeed) public onlyForked {
        uint256 n = decodeLen(ffiPython(lenArgs()));
        uint256 idx = bound(idxSeed, 1, n - 1);
        AccumulatorRow memory prevRow = decodeRow(ffiPython(rowArgs(vm, idx - 1)));
        AccumulatorRow memory currRow = decodeRow(ffiPython(rowArgs(vm, idx)));

        vm.rollFork(prevRow.blockNumber);
        uint256 prevTimestamp = block.timestamp;
        GrowthObservation prev = newGrowthObservation(
            block.number,
            FIRST_OBSERVATION_TIME_DELTA,
            prevRow.globalGrowth
        );

        vm.rollFork(currRow.blockNumber);
        GrowthObservation curr = newGrowthObservation(
            block.number,
            block.timestamp - prevTimestamp,
            currRow.globalGrowth
        );

        uint256 expectedDelta = currRow.globalGrowth - prevRow.globalGrowth;
        assertEq(uint256(prev.growthDelta(curr)), expectedDelta, "growthDelta mismatch");
    }

    function test__fuzzDifferential__ElapsedBlocksMatchesRawSubtraction(uint256 idxSeed) public onlyForked {
        uint256 n = decodeLen(ffiPython(lenArgs()));
        uint256 idx = bound(idxSeed, 1, n - 1);
        AccumulatorRow memory prevRow = decodeRow(ffiPython(rowArgs(vm, idx - 1)));
        AccumulatorRow memory currRow = decodeRow(ffiPython(rowArgs(vm, idx)));

        vm.rollFork(prevRow.blockNumber);
        uint256 prevTimestamp = block.timestamp;
        GrowthObservation prev = newGrowthObservation(
            block.number,
            FIRST_OBSERVATION_TIME_DELTA,
            prevRow.globalGrowth
        );

        vm.rollFork(currRow.blockNumber);
        GrowthObservation curr = newGrowthObservation(
            block.number,
            block.timestamp - prevTimestamp,
            currRow.globalGrowth
        );

        uint256 expectedElapsed = currRow.blockNumber - prevRow.blockNumber;
        assertEq(uint256(prev.elapsedBlocks(curr)), expectedElapsed, "elapsedBlocks mismatch");
    }

    function test__fuzzDifferential__ConsecutiveRowsMonotonic(uint256 idxSeed) public onlyForked {
        uint256 n = decodeLen(ffiPython(lenArgs()));
        uint256 idx = bound(idxSeed, 1, n - 1);
        AccumulatorRow memory prevRow = decodeRow(ffiPython(rowArgs(vm, idx - 1)));
        AccumulatorRow memory currRow = decodeRow(ffiPython(rowArgs(vm, idx)));

        vm.rollFork(prevRow.blockNumber);
        uint256 prevTimestamp = block.timestamp;
        GrowthObservation prev = newGrowthObservation(
            block.number,
            FIRST_OBSERVATION_TIME_DELTA,
            prevRow.globalGrowth
        );

        vm.rollFork(currRow.blockNumber);
        GrowthObservation curr = newGrowthObservation(
            block.number,
            block.timestamp - prevTimestamp,
            currRow.globalGrowth
        );

        assertTrue(curr.gte(prev), "curr should be gte prev");
        assertFalse(prev.gte(curr), "prev should not be gte curr");
        assertTrue(prev.lt(curr), "prev should be lt curr");
        assertFalse(curr.lt(prev), "curr should not be lt prev");
    }

    function test__fuzzDifferential__RealObservationsAreNonZero(uint256 idxSeed) public onlyForked {
        uint256 n = decodeLen(ffiPython(lenArgs()));
        uint256 idx = bound(idxSeed, 0, n - 1);
        AccumulatorRow memory row = decodeRow(ffiPython(rowArgs(vm, idx)));

        vm.rollFork(row.blockNumber);
        GrowthObservation obs = newGrowthObservation(
            block.number,
            FIRST_OBSERVATION_TIME_DELTA,
            row.globalGrowth
        );

        assertFalse(obs.isZero(), "real observation should not be zero");
    }

    function test__fuzzDifferential__BlockNumberGteBoundary(uint256 idxSeed) public onlyForked {
        uint256 n = decodeLen(ffiPython(lenArgs()));
        uint256 idx = bound(idxSeed, 1, n - 2);

        AccumulatorRow memory belowRow = decodeRow(ffiPython(rowArgs(vm, idx - 1)));
        AccumulatorRow memory targetRow = decodeRow(ffiPython(rowArgs(vm, idx)));
        AccumulatorRow memory aboveRow = decodeRow(ffiPython(rowArgs(vm, idx + 1)));

        uint32 target = uint32(targetRow.blockNumber);

        vm.rollFork(belowRow.blockNumber);
        GrowthObservation below = newGrowthObservation(block.number, FIRST_OBSERVATION_TIME_DELTA, belowRow.globalGrowth);

        vm.rollFork(targetRow.blockNumber);
        GrowthObservation atTarget = newGrowthObservation(block.number, FIRST_OBSERVATION_TIME_DELTA, targetRow.globalGrowth);

        vm.rollFork(aboveRow.blockNumber);
        GrowthObservation above = newGrowthObservation(block.number, FIRST_OBSERVATION_TIME_DELTA, aboveRow.globalGrowth);

        assertTrue(below.blockNumberLt(target), "below should be lt target");
        assertFalse(below.blockNumberGte(target), "below should not be gte target");

        assertTrue(atTarget.blockNumberGte(target), "at target should be gte target");
        assertFalse(atTarget.blockNumberLt(target), "at target should not be lt target");

        assertTrue(above.blockNumberGte(target), "above should be gte target");
        assertFalse(above.blockNumberLt(target), "above should not be lt target");
    }
}
