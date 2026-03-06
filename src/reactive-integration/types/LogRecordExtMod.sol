// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";

// Protocol-agnostic LogRecord utilities.
// Typed accessors over raw LogRecord fields.
// No V3/V4-specific logic — reusable across any event source.

function isSelfSync(IReactive.LogRecord calldata log, address self) pure returns (bool) {
    return log._contract == self;
}

function topic0(IReactive.LogRecord calldata log) pure returns (uint256) {
    return log.topic_0;
}

function emitter(IReactive.LogRecord calldata log) pure returns (address) {
    return log._contract;
}

function logChainId(IReactive.LogRecord calldata log) pure returns (uint256) {
    return log.chain_id;
}

function blockNumber(IReactive.LogRecord calldata log) pure returns (uint256) {
    return log.block_number;
}

function decodeTopic1AsAddress(IReactive.LogRecord calldata log) pure returns (address) {
    return address(uint160(log.topic_1));
}

function decodeTopic2AsInt24(IReactive.LogRecord calldata log) pure returns (int24) {
    return int24(int256(log.topic_2));
}

function decodeTopic3AsInt24(IReactive.LogRecord calldata log) pure returns (int24) {
    return int24(int256(log.topic_3));
}
