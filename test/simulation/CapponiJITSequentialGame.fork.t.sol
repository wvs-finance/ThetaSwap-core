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
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";

// Force-compile artifacts so vm.getCode can find them (used by Deploy.sol in PosmTestSetup)
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {PositionDescriptor} from "@uniswap/v4-periphery/src/PositionDescriptor.sol";

import {FeeConcentrationIndexHarness} from "../fee-concentration-index/harness/FeeConcentrationIndexHarness.sol";
import {FCITestHelper} from "../fee-concentration-index/helpers/FCITestHelper.sol";

import {Context} from "@foundry-script/types/Context.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";
import {Scenario} from "@foundry-script/types/Scenario.sol";
import {
    JitGameConfig,
    JitGameResult,
    JitAccounts,
    initJitAccounts,
    runJitGame,
    MultiRoundJitGameConfig,
    MultiRoundJitGameResult,
    runMultiRoundJitGame,
    UNIT_LIQUIDITY
} from "@foundry-script/simulation/JitGame.sol";
import "@foundry-script/utils/Constants.sol";

contract CapponiJITSequentialGameForkTest is PosmTestSetup, FCITestHelper {
    using PoolIdLibrary for PoolKey;

    Context ctx;
    Scenario scenario;
    FeeConcentrationIndexHarness harness;
    PoolId poolId;

    function setUp() public {
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();
        deployAndApprovePosm(manager);

        // Wire up FCITestHelper actor references
        fciLP = makeAddr("defaultLP");
        fciSwapper = address(this);
        fciSwapRouter = swapRouter;

        // Deploy FCI hook via HookMiner (correct flag bits for CREATE2 address)
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

        // Init pool with FCI hook
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

    /// @dev Fund an address with tokens via seedBalance + approve for PositionManager via permit2.
    function _setupLP(address account) internal {
        seedBalance(account);
        approvePosmFor(account);
    }

    /// @dev Fund and approve an address for swapping (direct approval on swapRouter).
    function _setupSwapper(address account) internal {
        seedBalance(account);
        vm.startPrank(account);
        IERC20(Currency.unwrap(currency0)).approve(address(swapRouter), type(uint256).max);
        IERC20(Currency.unwrap(currency1)).approve(address(swapRouter), type(uint256).max);
        vm.stopPrank();
    }

    function test_jitGame_equilibrium_no_jit_entry() public {
        uint256 n = 3;
        JitAccounts memory acc = initJitAccounts(vm, n);

        // Fund and approve all passive LPs for PositionManager (permit2 flow)
        for (uint256 i; i < n; ++i) {
            _setupLP(acc.passiveLps[i].addr);
        }
        // Fund and approve swapper for SwapRouter
        _setupSwapper(acc.swapper.addr);

        JitGameConfig memory cfg = JitGameConfig({
            n: n,
            jitCapital: 5e18,
            jitEntryProbability: 0, // JIT never enters
            tradeSize: 1e15,
            zeroForOne: true,
            protocol: Protocol.UniswapV4
        });

        JitGameResult memory result = runJitGame(ctx, scenario, cfg, acc, address(harness));

        assertFalse(result.jitEntered, "JIT should not enter at 0% probability");
        assertEq(result.jitLpPayout, 0, "JIT payout should be 0 when not entered");
        // With equal passive LPs and no JIT, delta-plus should be ~0
        // (all positions have equal lifetime and capital)
        console.log("Equilibrium delta-plus (Q128):", uint256(result.deltaPlus));
    }

    function test_jitGame_concentration_with_guaranteed_jit() public {
        uint256 n = 2;
        JitAccounts memory acc = initJitAccounts(vm, n);

        // Fund and approve passive LPs
        for (uint256 i; i < n; ++i) {
            _setupLP(acc.passiveLps[i].addr);
        }
        // Fund and approve JIT LP
        _setupLP(acc.jitLp.addr);
        // Fund and approve swapper
        _setupSwapper(acc.swapper.addr);

        JitGameConfig memory cfg = JitGameConfig({
            n: n,
            jitCapital: 9e18,
            jitEntryProbability: 10000, // JIT always enters
            tradeSize: 1e15,
            zeroForOne: true,
            protocol: Protocol.UniswapV4
        });

        JitGameResult memory result = runJitGame(ctx, scenario, cfg, acc, address(harness));

        assertTrue(result.jitEntered, "JIT should enter at 100% probability");
        assertTrue(result.jitLpPayout > 0, "JIT should earn fees");
        // With JIT entering and exiting in same block, θ_JIT = 1/1 = 1 (max penalty).
        // This should produce non-zero delta-plus from the FCI hook.
        assertGt(result.deltaPlus, 0, "delta-plus must be > 0 with JIT crowd-out");
        console.log("JIT delta-plus (Q128):", uint256(result.deltaPlus));
        console.log("JIT payout:", result.jitLpPayout);
        console.log("Hedged LP payout:", result.hedgedLpPayout);
        console.log("Unhedged LP payout:", result.unhedgedLpPayout);
    }

    function test_multiRound_fci_accumulation() public {
        uint256 n = 2;
        JitAccounts memory acc = initJitAccounts(vm, n);

        for (uint256 i; i < n; ++i) {
            _setupLP(acc.passiveLps[i].addr);
        }
        _setupLP(acc.jitLp.addr);
        _setupSwapper(acc.swapper.addr);

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

        MultiRoundJitGameResult memory result = runMultiRoundJitGame(
            ctx, scenario, cfg, acc, address(harness)
        );

        // INV-010: multi-round accumulation — last round δ⁺ > first round
        assertGt(
            result.deltaPlusPerRound[cfg.rounds - 1],
            result.deltaPlusPerRound[0],
            "delta-plus must accumulate across rounds"
        );

        console.log("Round 1 delta-plus:", uint256(result.deltaPlusPerRound[0]));
        console.log("Round 3 delta-plus:", uint256(result.deltaPlusPerRound[2]));
        console.log("Total JIT payout:", result.totalJitLpPayout);
    }
}
