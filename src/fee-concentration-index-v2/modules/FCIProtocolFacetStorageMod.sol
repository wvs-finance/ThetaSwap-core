// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FeeConcentrationIndexStorage} from "@fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {FeeConcentrationEpochStorage} from "@fee-concentration-index/modules/FeeConcentrationEpochStorageMod.sol";

// ── Per-protocol FCI storage slot derivation ──

function protocolFciStorage(bytes1 flag) pure returns (FeeConcentrationIndexStorage storage $) {
    bytes32 position = keccak256(abi.encode("thetaSwap.fci", flag));
    assembly ("memory-safe") { $.slot := position }
}

function protocolEpochFciStorage(bytes1 flag) pure returns (FeeConcentrationEpochStorage storage $) {
    bytes32 position = keccak256(abi.encode("thetaSwap.fci.epoch", flag));
    assembly ("memory-safe") { $.slot := position }
}

// ── Transient storage helpers (per-protocol isolated) ──

function transientBase(bytes1 flag) pure returns (bytes32) {
    return keccak256(abi.encode("thetaSwap.fci.transient", flag));
}

function tstoreTick(bytes1 flag, int24 tick) {
    bytes32 slot = transientBase(flag);
    assembly { tstore(slot, tick) }
}

function tloadTick(bytes1 flag) returns (int24 tick) {
    bytes32 slot = transientBase(flag);
    assembly { tick := tload(slot) }
}

function tstoreRemovalData(bytes1 flag, uint256 feeLast, uint128 posLiquidity, uint256 rangeFeeGrowth) {
    bytes32 base = transientBase(flag);
    bytes32 feeSlot = bytes32(uint256(base) + 1);
    bytes32 liqSlot = bytes32(uint256(base) + 2);
    bytes32 rangeFeeSlot = bytes32(uint256(base) + 3);
    assembly {
        tstore(feeSlot, feeLast)
        tstore(liqSlot, posLiquidity)
        tstore(rangeFeeSlot, rangeFeeGrowth)
    }
}

function tloadRemovalData(bytes1 flag) returns (uint256 feeLast, uint128 posLiquidity, uint256 rangeFeeGrowth) {
    bytes32 base = transientBase(flag);
    bytes32 feeSlot = bytes32(uint256(base) + 1);
    bytes32 liqSlot = bytes32(uint256(base) + 2);
    bytes32 rangeFeeSlot = bytes32(uint256(base) + 3);
    assembly {
        feeLast := tload(feeSlot)
        posLiquidity := tload(liqSlot)
        rangeFeeGrowth := tload(rangeFeeSlot)
    }
}
