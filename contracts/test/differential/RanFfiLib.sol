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
