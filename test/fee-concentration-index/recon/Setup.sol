// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {BaseSetup} from "chimera/BaseSetup.sol";

import {Test} from "forge-std/Test.sol";
import {Deployers} from "v4-core/test/utils/Deployers.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";

import {FeeConcentrationIndexHarness} from "../harness/FeeConcentrationIndexHarness.sol";
import {MockPositionManager} from "../harness/MockPositionManager.sol";
import {FeeConcentrationIndexStorage, fciStorage} from "../../../src/fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {TickRange, fromTicks} from "../../../src/fee-concentration-index/types/TickRangeMod.sol";

// Chimera Setup: deploys V4 PoolManager, routers, tokens, and hook harness.
// Uses Deployers for V4 core + MockPositionManager (hook only needs poolManager()).
// Harness deployed via CREATE2 + HookMiner for correct address flag bits.

abstract contract Setup is BaseSetup, Test, Deployers {
    FeeConcentrationIndexHarness internal harness;
    PoolKey internal fciPoolKey;
    PoolId internal fciPoolId;

    // Ghost tracking for property checks
    uint256 internal positionsAdded;
    bytes32[] internal allPositionKeys;
    mapping(bytes32 => bool) internal ghostRegistered;
    mapping(bytes32 => int24) internal ghostTickLower;
    mapping(bytes32 => int24) internal ghostTickUpper;

    function setup() internal override {
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();

        MockPositionManager mockPosm = new MockPositionManager(manager);

        // Hook permissions: afterAddLiquidity, afterRemoveLiquidity, beforeSwap, afterSwap
        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
                | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
                | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
                | Hooks.BEFORE_SWAP_FLAG
                | Hooks.AFTER_SWAP_FLAG
        );

        // Mine CREATE2 salt for address with correct flag bits
        bytes memory constructorArgs = abi.encode(address(mockPosm));
        (address hookAddress, bytes32 salt) = HookMiner.find(
            address(this),
            flags,
            type(FeeConcentrationIndexHarness).creationCode,
            constructorArgs
        );

        harness = new FeeConcentrationIndexHarness{salt: salt}(IPositionManager(address(mockPosm)));
        require(address(harness) == hookAddress, "Setup: hook address mismatch");

        // Initialize pool with hook attached
        (fciPoolKey,) = initPool(
            currency0,
            currency1,
            IHooks(address(harness)),
            3000,
            SQRT_PRICE_1_1
        );
        fciPoolId = PoolIdLibrary.toId(fciPoolKey);
    }
}
