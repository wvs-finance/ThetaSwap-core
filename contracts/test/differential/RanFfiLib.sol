// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

struct AccumulatorRow {
    uint256 blockNumber;
    uint256 blockTimestamp;
    uint256 globalGrowth;
}

string constant RAN_POOL_HEX = "0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657";
string constant RAN_DB_PATH = "data/ran_accumulator.duckdb";

function decodeLen(bytes memory raw) pure returns (uint256 count) {
    (count) = abi.decode(raw, (uint256));
}

function decodeRow(bytes memory raw) pure returns (AccumulatorRow memory row) {
    (uint256 blockNumber, uint256 blockTimestamp, bytes32 growthBytes) =
        abi.decode(raw, (uint256, uint256, bytes32));
    row = AccumulatorRow({
        blockNumber: blockNumber, blockTimestamp: blockTimestamp, globalGrowth: uint256(growthBytes)
    });
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
