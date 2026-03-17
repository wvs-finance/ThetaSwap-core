// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {Deployers} from "v4-core/test/utils/Deployers.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";

import {TokenPair, mockPair} from "@utils/TokenPair.sol";
import {Mode} from "@utils/Mode.sol";
import {Accounts, ApprovalTarget, makeTestAccounts, seed, approveAll} from "@utils/Accounts.sol";
import {createPoolV4} from "@utils/Pool.sol";

contract HarnessIntegrationTest is Test, Deployers {
    function test_fullPipeline() public {
        // 1. Deploy V4 infra
        deployFreshManagerAndRouters();

        // 2. Create accounts + tokens
        Accounts memory accts = makeTestAccounts(vm);
        TokenPair memory pair = mockPair(1_000_000e18, address(this));

        // 3. Fund accounts
        seed(vm, accts, pair, 100_000e18, Mode.Test);

        // 4. Approve routers
        ApprovalTarget[] memory targets = new ApprovalTarget[](2);
        targets[0] = ApprovalTarget(address(modifyLiquidityRouter), true, true, false);
        targets[1] = ApprovalTarget(address(swapRouter), false, false, true);
        approveAll(vm, accts, pair, targets, Mode.Test);

        // 5. Create pool
        (PoolKey memory key,) = createPoolV4(
            pair, address(0), 3000, 60, SQRT_PRICE_1_1, address(manager)
        );

        // 6. Verify state
        assertEq(MockERC20(pair.token0).balanceOf(accts.lpPassive.addr), 100_000e18);
        assertEq(
            IERC20(pair.token0).allowance(accts.lpPassive.addr, address(modifyLiquidityRouter)),
            type(uint256).max
        );
        assertEq(
            IERC20(pair.token0).allowance(accts.swapper.addr, address(swapRouter)),
            type(uint256).max
        );
        assertEq(key.fee, 3000);
    }
}
