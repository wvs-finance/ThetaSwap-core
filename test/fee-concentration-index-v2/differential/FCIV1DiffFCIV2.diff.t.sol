// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PosmTestSetup} from "@uniswap/v4-periphery/test/shared/PosmTestSetup.sol";
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {PositionDescriptor} from "@uniswap/v4-periphery/src/PositionDescriptor.sol";

import {FeeConcentrationIndex} from "@fee-concentration-index/FeeConcentrationIndex.sol";
import {FeeConcentrationIndexV2} from "@fee-concentration-index-v2/FeeConcentrationIndexV2.sol";
import {DeployFci, FCI_HOOK_FLAGS} from "@foundry-script/deploy/DeployFci.s.sol";
import {FCITestHelper} from "../../fee-concentration-index/helpers/FCITestHelper.sol";

/// @title FCI V1 vs V2 Differential Test
/// @notice Deploys both V1 and V2 hooks via DeployFci script.
/// Runs the same scenarios on both pools and asserts identical FCI state.
/// V4 path only — hookData is always empty.
contract FCIV1DiffFCIV2Test is PosmTestSetup, FCITestHelper {
    using PoolIdLibrary for PoolKey;

    FeeConcentrationIndex v1;
    FeeConcentrationIndexV2 v2;

    PoolKey keyV1;
    PoolKey keyV2;
    PoolId poolIdV1;
    PoolId poolIdV2;

    function setUp() public {
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();
        deployAndApprovePosm(manager);

        fciLP = makeAddr("diffLP");
        fciSwapper = address(this);
        fciSwapRouter = swapRouter;

        // ── Deploy V1 + V2 via DeployFci script ──
        DeployFci deployer = new DeployFci(address(manager));
        (address v1Addr, address v2Addr) = deployer.run();
        v1 = FeeConcentrationIndex(v1Addr);
        v2 = FeeConcentrationIndexV2(v2Addr);

        // ── Initialize two pools — identical config, different hooks ──
        (keyV1, poolIdV1) = initPool(
            currency0, currency1, IHooks(address(v1)), 3000, SQRT_PRICE_1_1
        );
        (keyV2, poolIdV2) = initPool(
            currency0, currency1, IHooks(address(v2)), 3000, SQRT_PRICE_1_1
        );
    }

    // ── State comparison helper ──

    function _assertFCIStateEqual() internal view {
        // ── getIndex ──
        (uint128 indexAV1, uint256 thetaSumV1, uint256 removedV1) = v1.getIndex(keyV1, false);
        (uint128 indexAV2, uint256 thetaSumV2, uint256 removedV2) = v2.getIndex(keyV2, false);
        assertEq(indexAV1, indexAV2, "indexA mismatch");
        assertEq(thetaSumV1, thetaSumV2, "thetaSum mismatch");
        assertEq(removedV1, removedV2, "removedPosCount mismatch");

        // ── getDeltaPlus ──
        uint128 dpV1 = v1.getDeltaPlus(keyV1, false);
        uint128 dpV2 = v2.getDeltaPlus(keyV2, false);
        assertEq(dpV1, dpV2, "deltaPlus mismatch");

        // ── getDeltaPlusEpoch ──
        uint128 dpEpochV1 = v1.getDeltaPlusEpoch(keyV1, false);
        uint128 dpEpochV2 = v2.getDeltaPlusEpoch(keyV2, false);
        assertEq(dpEpochV1, dpEpochV2, "deltaPlusEpoch mismatch");

        // ── getAtNull ──
        uint128 atNullV1 = v1.getAtNull(keyV1, false);
        uint128 atNullV2 = v2.getAtNull(keyV2, false);
        assertEq(atNullV1, atNullV2, "atNull mismatch");

        // ── getThetaSum ──
        uint256 tsV1 = v1.getThetaSum(keyV1, false);
        uint256 tsV2 = v2.getThetaSum(keyV2, false);
        assertEq(tsV1, tsV2, "getThetaSum mismatch");
    }

    // TODO: add test scenarios — mint on both, swap on both, burn on both, assert _assertFCIStateEqual()
}
