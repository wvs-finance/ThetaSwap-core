// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// DEPRECATED: This module is superseded by ProtocolAdapterMod.
// Import path: @protocol-adapter/modules/ProtocolAdapterMod.sol
// This file re-exports for backward compatibility. Remove once all callers migrate.

import {
    registerPosition,
    incrementPosCount, decrementPosCount,
    incrementOverlappingRanges,
    deregisterPosition,
    addStateTerm,
    setFeeGrowthBaseline, getFeeGrowthBaseline, deleteFeeGrowthBaseline,
    initializeAdapter
} from "@protocol-adapter/modules/ProtocolAdapterMod.sol";
