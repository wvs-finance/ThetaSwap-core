// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test, console} from "forge-std/Test.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {PosmTestSetup} from "@uniswap/v4-periphery/test/shared/PosmTestSetup.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {PositionDescriptor} from "@uniswap/v4-periphery/src/PositionDescriptor.sol";

import {FeeConcentrationIndexHarness} from "../../fee-concentration-index/harness/FeeConcentrationIndexHarness.sol";
import {FCITestHelper} from "../../fee-concentration-index/helpers/FCITestHelper.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";

import {Context} from "@foundry-script/types/Context.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";
import {Scenario} from "@foundry-script/types/Scenario.sol";
import {
    JitGameConfig,
    JitAccounts,
    initJitAccounts,
    MultiRoundJitGameConfig,
    MultiRoundJitGameResult,
    runMultiRoundJitGame,
    UNIT_LIQUIDITY
} from "@foundry-script/simulation/JitGame.sol";
import "@foundry-script/utils/Constants.sol";

import {
    deltaPlusToSqrtPriceX96,
    applyDecay,
    updateHWM,
    lookbackPayoffX96
} from "@fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol";

contract PayoffPipelineIntegrationTest is PosmTestSetup, FCITestHelper {
    using PoolIdLibrary for PoolKey;

    Context ctx;
    Scenario scenario;
    FeeConcentrationIndexHarness harness;
    PoolId poolId;

    function setUp() public {
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();
        deployAndApprovePosm(manager);

        fciLP = makeAddr("defaultLP");
        fciSwapper = address(this);
        fciSwapRouter = swapRouter;

        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
                | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
                | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
                | Hooks.BEFORE_SWAP_FLAG
                | Hooks.AFTER_SWAP_FLAG
        );

        bytes memory constructorArgs = abi.encode(address(lpm));
        (address hookAddress, bytes32 salt) = HookMiner.find(
            address(this),
            flags,
            type(FeeConcentrationIndexHarness).creationCode,
            constructorArgs
        );

        harness = new FeeConcentrationIndexHarness{salt: salt}(lpm);
        require(address(harness) == hookAddress, "hook address mismatch");

        (key, poolId) = initPool(
            currency0,
            currency1,
            IHooks(address(harness)),
            3000,
            SQRT_PRICE_1_1
        );

        ctx.vm = vm;
        ctx.v4Pool = key;
        ctx.v4PositionManager = address(lpm);
        ctx.v4SwapRouter = address(swapRouter);
        ctx.chainId = block.chainid;
    }

    function _setupLP(address account) internal {
        seedBalance(account);
        approvePosmFor(account);
    }

    function _setupSwapper(address account) internal {
        seedBalance(account);
        vm.startPrank(account);
        IERC20(Currency.unwrap(currency0)).approve(address(swapRouter), type(uint256).max);
        IERC20(Currency.unwrap(currency1)).approve(address(swapRouter), type(uint256).max);
        vm.stopPrank();
    }

    function test_payoffPipeline_endToEnd() public {
        uint256 n = 2;
        JitAccounts memory acc = initJitAccounts(vm, n);

        for (uint256 i; i < n; ++i) _setupLP(acc.passiveLps[i].addr);
        _setupLP(acc.jitLp.addr);
        _setupSwapper(acc.swapper.addr);

        // Run 3-round game with guaranteed JIT
        MultiRoundJitGameConfig memory cfg = MultiRoundJitGameConfig({
            rounds: 3,
            roundConfig: JitGameConfig({
                n: n,
                jitCapital: 9e18,
                jitEntryProbability: 10000,
                tradeSize: 1e15,
                zeroForOne: true,
                protocol: Protocol.UniswapV4
            })
        });

        MultiRoundJitGameResult memory gameResult = runMultiRoundJitGame(
            ctx, scenario, cfg, acc, address(harness)
        );

        // Pipeline: delta-plus → sqrtPrice → HWM → decay → payoff
        uint128 finalDeltaPlus = gameResult.deltaPlusPerRound[cfg.rounds - 1];
        assertGt(finalDeltaPlus, 0, "delta-plus must be non-zero with JIT");

        uint160 sqrtPrice = deltaPlusToSqrtPriceX96(finalDeltaPlus);
        assertGt(sqrtPrice, 0, "sqrtPrice must be non-zero");

        uint160 hwm = updateHWM(0, sqrtPrice);
        assertEq(hwm, sqrtPrice, "HWM should equal first price");

        // Decay 7 days with 14-day half-life
        uint160 decayed = applyDecay(hwm, 7 days, 14 days);
        assertLt(decayed, hwm, "decay must reduce HWM");
        assertGt(decayed, 0, "decayed HWM must be positive");

        // Payoff with strike at SQRT_PRICE_1_1 (1.0)
        uint160 strike = uint160(SqrtPriceLibrary.Q96);
        uint256 payoff = lookbackPayoffX96(decayed, strike);

        console.log("Final delta-plus (Q128):", uint256(finalDeltaPlus));
        console.log("SqrtPrice from delta-plus:", uint256(sqrtPrice));
        console.log("HWM after 7d decay:", uint256(decayed));
        console.log("Payoff (Q96):", payoff);
    }
}
