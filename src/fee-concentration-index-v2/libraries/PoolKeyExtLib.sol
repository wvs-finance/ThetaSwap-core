// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {CalldataReader, CalldataReaderLib} from "angstrom/src/types/CalldataReader.sol";

/// @dev Reads a protocol pool representation and builds a V4-shaped PoolKey.
/// Currently only reads a single address from poolRpt.
/// Extend per protocol to decode fee, tickSpacing, tokens, etc.
function fromPoolRptToPoolKey(bytes calldata poolRpt, IHooks fciHook) pure returns (PoolKey memory key) {
    CalldataReader reader = CalldataReaderLib.from(poolRpt);
    address pool;
    (reader, pool) = reader.readAddr();
    // TODO: protocol-specific decoding — extract tokens, fee, tickSpacing from pool address
    // For now, only the pool address is read. Protocols override this function.
    key.hooks = fciHook;
}
