// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";

/// @dev Per-protocol adapter storage. One instance per protocol at a distinct diamond slot.
/// See docs/superpowers/specs/2026-03-12-protocol-adapter-storage-design.md
struct ProtocolAdapterStorage {
    address protocolState;   // V4: IPoolManager, V3: IUniswapV3Factory — cast at call site
    IHooks  fciEntryPoint;   // typed IHooks for assignment compat with PoolKey.hooks; cast to IFeeConcentrationIndex at call sites
    PoolKey poolKey;          // V4-shaped PoolKey (V3 adapters construct via fromV3Pool). For V4 native, consumed only by vault oracle path
    bool    reactive;         // per-pool flag — true for V3, also true for V4 pools that missed initial hook registration
}

bytes32 constant V4_ADAPTER_SLOT = keccak256("thetaSwap.protocolAdapter.uniswapV4");
bytes32 constant V3_ADAPTER_SLOT = keccak256("thetaSwap.protocolAdapter.uniswapV3");

function protocolAdapterStorage(bytes32 slot) pure returns (ProtocolAdapterStorage storage $) {
    assembly { $.slot := slot }
}

function v4AdapterStorage() pure returns (ProtocolAdapterStorage storage $) {
    return protocolAdapterStorage(V4_ADAPTER_SLOT);
}

function v3AdapterStorage() pure returns (ProtocolAdapterStorage storage $) {
    return protocolAdapterStorage(V3_ADAPTER_SLOT);
}
