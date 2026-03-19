// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
// reference: @fee-concentration-index-v2/libraries/PoolKeyExtLib.sol

/// @dev Decodes a V4 PoolKey from bytes and sets hooks to the FCI hook address.
function fromUniswapV4PoolKeyToPoolKey(bytes memory encodedPoolKey, IHooks fciHook) pure returns (PoolKey memory key) {
    key = abi.decode(encodedPoolKey, (PoolKey));
    key.hooks = fciHook;
}
