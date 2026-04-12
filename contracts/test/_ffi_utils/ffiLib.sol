// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {Vm} from "forge-std/Vm.sol";


struct AccumulatorRow {
    uint256 blockNumber;
    uint256 blockTimestamp;
    uint256 globalGrowth;
}

string constant RAN_POOL_HEX = "0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657";
string constant RAN_DB_PATH = "data/ran_accumulator.duckdb";

function lenArgs() pure returns (string[] memory args) {
    args = new string[](7);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "len";
    args[3] = "--pool";
    args[4] = RAN_POOL_HEX;
    args[5] = "--db";
    args[6] = RAN_DB_PATH;
}

function decodeLen(bytes memory raw) pure returns (uint256 count) {
    (count) = abi.decode(raw, (uint256));
}

function rowArgs(Vm vm, uint256 idx) returns (string[] memory args) {
    args = new string[](9);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "row";
    args[3] = "--pool";
    args[4] = RAN_POOL_HEX;
    args[5] = "--idx";
    args[6] = vm.toString(idx);
    args[7] = "--db";
    args[8] = RAN_DB_PATH;
}

function rowByTsArgs(Vm vm, uint256 ts) returns (string[] memory args) {
    args = new string[](10);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "row-by-ts";
    args[3] = "--pool";
    args[4] = RAN_POOL_HEX;
    args[5] = "--ts";
    args[6] = vm.toString(ts);
    args[7] = "--db";
    args[8] = RAN_DB_PATH;
    args[9] = "--nearest";
}

function minArgs() pure returns (string[] memory args) {
    args = new string[](7);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "min";
    args[3] = "--pool";
    args[4] = RAN_POOL_HEX;
    args[5] = "--db";
    args[6] = RAN_DB_PATH;
}

function maxArgs() pure returns (string[] memory args) {
    args = new string[](7);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "max";
    args[3] = "--pool";
    args[4] = RAN_POOL_HEX;
    args[5] = "--db";
    args[6] = RAN_DB_PATH;
}

function decodeRow(bytes memory raw) pure returns (AccumulatorRow memory row) {
    (uint256 blockNumber, uint256 blockTimestamp, bytes32 growthBytes) =
        abi.decode(raw, (uint256, uint256, bytes32));
    row = AccumulatorRow({
        blockNumber: blockNumber, blockTimestamp: blockTimestamp, globalGrowth: uint256(growthBytes)
    });
}

function rangeArgs(Vm vm, uint256 from_, uint256 to_) returns (string[] memory args) {
    args = new string[](11);
    args[0] = "-m";
    args[1] = "scripts.ran_ffi";
    args[2] = "range";
    args[3] = "--pool";
    args[4] = RAN_POOL_HEX;
    args[5] = "--from";
    args[6] = vm.toString(from_);
    args[7] = "--to";
    args[8] = vm.toString(to_);
    args[9] = "--db";
    args[10] = RAN_DB_PATH;
}

function decodeRange(bytes memory raw) pure returns (AccumulatorRow[] memory rows) {
    (
        uint256 count,
        uint256[] memory blockNumbers,
        uint256[] memory blockTimestamps,
        bytes32[] memory growths
    ) = abi.decode(raw, (uint256, uint256[], uint256[], bytes32[]));

    require(
        count == blockNumbers.length && count == blockTimestamps.length && count == growths.length,
        "decodeRange: count mismatch"
    );

    rows = new AccumulatorRow[](count);
    for (uint256 i; i < count; ++i) {
        rows[i] = AccumulatorRow({
            blockNumber: blockNumbers[i],
            blockTimestamp: blockTimestamps[i],
            globalGrowth: uint256(growths[i])
        });
    }
}
