// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";

struct PoolKeyLiquidity {
    PoolKey pool;
    mapping(uint256 chainId => mapping(Protocol => address)) positionManager;
}
