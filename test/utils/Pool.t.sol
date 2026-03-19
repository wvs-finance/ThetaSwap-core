// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {Deployers} from "v4-core/test/utils/Deployers.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {TokenPair, mockPair} from "@utils/TokenPair.sol";
import {createPoolV4} from "@utils/Pool.sol";

contract PoolV4Test is Test, Deployers {
    function test_createPoolV4_initializesPool() public {
        deployFreshManagerAndRouters();
        TokenPair memory pair = mockPair(1_000_000e18, address(this));

        (PoolKey memory key, PoolId poolId) = createPoolV4(
            pair,
            address(0),   // no hook
            3000,
            60,           // tickSpacing
            SQRT_PRICE_1_1,
            address(manager)
        );

        assertTrue(PoolId.unwrap(poolId) != bytes32(0), "poolId is zero");
        assertEq(key.fee, 3000);
    }
}
