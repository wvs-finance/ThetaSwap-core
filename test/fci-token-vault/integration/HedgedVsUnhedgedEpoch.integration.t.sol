// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test, console} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {PosmTestSetup} from "@uniswap/v4-periphery/test/shared/PosmTestSetup.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {PositionDescriptor} from "@uniswap/v4-periphery/src/PositionDescriptor.sol";

import {FeeConcentrationIndexHarness} from "../../fee-concentration-index/harness/FeeConcentrationIndexHarness.sol";
import {FCITestHelper} from "../../fee-concentration-index/helpers/FCITestHelper.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";

import {Context} from "@foundry-script/types/Context.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";
import {Scenario, mintPosition, burnPosition} from "@foundry-script/types/Scenario.sol";
import {executeSwapWithAmount} from "@foundry-script/simulation/JitGame.sol";
import "@foundry-script/utils/Constants.sol";

import {FciTokenVaultHarness} from "../helpers/FciTokenVaultHarness.sol";
import {LONG, SHORT} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {lookbackPayoffX96, applyDecay} from "@fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol";

contract HedgedVsUnhedgedEpochTest is PosmTestSetup, FCITestHelper {
    using PoolIdLibrary for PoolKey;

    Context ctx;
    Scenario scenario;
    FeeConcentrationIndexHarness fciHarness;
    FciTokenVaultHarness vault;
    PoolId poolId;

    uint256 constant CAPITAL = 1e18;
    uint256 constant HEDGE_AMOUNT = 0.1e18;
    uint256 constant TRADE_SIZE = 1e15;
    uint256 constant ROUNDS = 3;
    uint256 constant JIT_CAPITAL = 9e18;
    uint256 constant ROUND_INTERVAL = 1 days;
    uint256 constant EPOCH_LENGTH = 7 days; // All 3 rounds fit in one epoch

    address hedgedPlpAddr;
    uint256 hedgedPlpPk;
    address unhedgedPlpAddr;
    uint256 unhedgedPlpPk;
    address jitLpAddr;
    uint256 jitLpPk;
    address swapperAddr;
    uint256 swapperPk;
    address depositorAddr;
    uint256 depositorPk;

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
            address(this), flags,
            type(FeeConcentrationIndexHarness).creationCode, constructorArgs
        );
        fciHarness = new FeeConcentrationIndexHarness{salt: salt}(lpm);
        require(address(fciHarness) == hookAddress, "hook address mismatch");

        (key, poolId) = initPool(
            currency0, currency1,
            IHooks(address(fciHarness)),
            3000, SQRT_PRICE_1_1
        );

        // Initialize epoch metric for this pool
        fciHarness.initializeEpochPool(key, EPOCH_LENGTH);

        ctx.vm = vm;
        ctx.v4Pool = key;
        ctx.v4PositionManager = address(lpm);
        ctx.v4SwapRouter = address(swapRouter);
        ctx.chainId = block.chainid;

        vault = new FciTokenVaultHarness();
        uint160 strikePrice = SqrtPriceLibrary.fractionToSqrtPriceX96(30, 70);
        vault.harness_initVault(
            strikePrice, 14 days, block.timestamp + 5 days,
            key, false, Currency.unwrap(currency1)
        );

        Vm.Wallet memory w;
        w = vm.createWallet("hedgedPlp");
        hedgedPlpAddr = w.addr; hedgedPlpPk = w.privateKey;
        w = vm.createWallet("unhedgedPlp");
        unhedgedPlpAddr = w.addr; unhedgedPlpPk = w.privateKey;
        w = vm.createWallet("jitLp");
        jitLpAddr = w.addr; jitLpPk = w.privateKey;
        w = vm.createWallet("swapper");
        swapperAddr = w.addr; swapperPk = w.privateKey;
        w = vm.createWallet("depositor");
        depositorAddr = w.addr; depositorPk = w.privateKey;

        _setupLP(hedgedPlpAddr);
        _setupLP(unhedgedPlpAddr);
        _setupLP(jitLpAddr);
        _setupSwapper(swapperAddr);
        seedBalance(depositorAddr);
    }

    // ── Helpers (same as cumulative test) ──

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

    function _depositToVault(address plpAddr, uint256 amount) internal {
        vm.startPrank(plpAddr);
        IERC20(Currency.unwrap(currency1)).approve(address(vault), amount);
        vault.harness_deposit(plpAddr, amount);
        vm.stopPrank();
    }

    uint256 constant JIT_ENTRY_OFFSET = 49;
    uint256 constant PASSIVE_EXIT_OFFSET = 50;

    function _runRound(
        bool jitEnters, uint256 jitCapital, uint256 hedgedLiq, uint256 unhedgedLiq
    ) internal returns (uint256 hedgedTokenId, uint256 unhedgedTokenId) {
        hedgedTokenId = mintPosition(ctx, scenario, Protocol.UniswapV4, hedgedPlpPk, hedgedLiq);
        unhedgedTokenId = mintPosition(ctx, scenario, Protocol.UniswapV4, unhedgedPlpPk, unhedgedLiq);

        vm.roll(block.number + JIT_ENTRY_OFFSET);

        uint256 jitTokenId;
        if (jitEnters) {
            jitTokenId = mintPosition(ctx, scenario, Protocol.UniswapV4, jitLpPk, jitCapital);
        }

        executeSwapWithAmount(ctx, Protocol.UniswapV4, swapperPk, ZERO_FOR_ONE, int256(TRADE_SIZE));

        vm.roll(block.number + 1);
        if (jitEnters) {
            burnPosition(ctx, Protocol.UniswapV4, jitLpPk, jitTokenId, jitCapital);
        }

        vm.roll(block.number + PASSIVE_EXIT_OFFSET);
        burnPosition(ctx, Protocol.UniswapV4, hedgedPlpPk, hedgedTokenId, hedgedLiq);
        burnPosition(ctx, Protocol.UniswapV4, unhedgedPlpPk, unhedgedTokenId, unhedgedLiq);

        // Log both metrics for comparison
        uint128 cumDp = IFeeConcentrationIndex(address(fciHarness)).getDeltaPlus(key, false);
        uint128 epochDp = IFeeConcentrationIndex(address(fciHarness)).getDeltaPlusEpoch(key, false);
        console.log("  Cumulative delta+:", uint256(cumDp));
        console.log("  Epoch delta+:     ", uint256(epochDp));

        vm.warp(block.timestamp + ROUND_INTERVAL);
        vault.harness_pokeEpoch(); // Uses epoch Δ⁺
    }

    function _settleVault(FciTokenVaultHarness v, uint256 depositAmount)
        internal
        returns (uint256 longPayout, uint256 shortPayout)
    {
        (,,, uint256 expiry,,,,) = v.harness_getVaultStorage();
        vm.warp(expiry + 1);
        v.harness_settle();
        (,,,,,,, uint256 longPayoutPerToken) = v.harness_getVaultStorage();
        longPayout = (depositAmount * longPayoutPerToken) / SqrtPriceLibrary.Q96;
        shortPayout = depositAmount - longPayout;
        vm.prank(depositorAddr);
        v.harness_redeem(depositorAddr, depositAmount);
    }

    function _snapshotBal(address who) internal view returns (uint256 a, uint256 b) {
        a = IERC20(Currency.unwrap(currency0)).balanceOf(who);
        b = IERC20(Currency.unwrap(currency1)).balanceOf(who);
    }

    // ── Scenario 1: Equilibrium ──

    function test_epoch_equilibrium_no_jit() public {
        _depositToVault(depositorAddr, HEDGE_AMOUNT);
        (uint256 hA0, uint256 hB0) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA0, uint256 uB0) = _snapshotBal(unhedgedPlpAddr);

        console.log("=== EPOCH: EQUILIBRIUM (no JIT) ===");
        for (uint256 i; i < ROUNDS; ++i) {
            console.log("Round", i + 1);
            _runRound(false, 0, CAPITAL, CAPITAL);
        }

        (uint256 hA1, uint256 hB1) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA1, uint256 uB1) = _snapshotBal(unhedgedPlpAddr);
        uint256 hedgedPayout = (hA1 + hB1) - (hA0 + hB0);
        uint256 unhedgedPayout = (uA1 + uB1) - (uA0 + uB0);

        (uint256 longPayout, uint256 shortPayout) = _settleVault(vault, HEDGE_AMOUNT);

        assertEq(longPayout, 0, "LONG should be 0 in equilibrium");
        assertEq(longPayout + shortPayout, HEDGE_AMOUNT, "conservation");

        console.log("LONG payout:", longPayout);
    }

    // ── Scenario 2: JIT crowd-out ──

    function test_epoch_jit_crowdout_hedge_compensates() public {
        _depositToVault(depositorAddr, HEDGE_AMOUNT);
        (uint256 hA0, uint256 hB0) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA0, uint256 uB0) = _snapshotBal(unhedgedPlpAddr);

        console.log("=== EPOCH: JIT CROWD-OUT ===");
        for (uint256 i; i < ROUNDS; ++i) {
            console.log("Round", i + 1);
            _runRound(true, JIT_CAPITAL, CAPITAL, CAPITAL);
        }

        (uint256 hA1, uint256 hB1) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA1, uint256 uB1) = _snapshotBal(unhedgedPlpAddr);
        uint256 hedgedPayout = (hA1 + hB1) - (hA0 + hB0);
        uint256 unhedgedPayout = (uA1 + uB1) - (uA0 + uB0);

        (uint256 longPayout, uint256 shortPayout) = _settleVault(vault, HEDGE_AMOUNT);

        uint256 hedgedWelfare = hedgedPayout + longPayout;
        uint256 unhedgedWelfare = unhedgedPayout;

        // Property 1: Hedge compensates
        assertGt(hedgedWelfare, unhedgedWelfare, "hedged should earn more under JIT");
        assertGt(longPayout, 0, "LONG should be positive under JIT");

        // Property: Conservation
        assertEq(longPayout + shortPayout, HEDGE_AMOUNT, "conservation");

        console.log("LONG payout:", longPayout);
        console.log("Hedged welfare:", hedgedWelfare);
        console.log("Unhedged welfare:", unhedgedWelfare);
        console.log("Net hedge benefit:", hedgedWelfare - unhedgedWelfare);
    }

    // ── Scenario 3: Below-strike ──

    function test_epoch_below_strike_no_false_trigger() public {
        FciTokenVaultHarness highStrikeVault = new FciTokenVaultHarness();
        uint160 highStrike = SqrtPriceLibrary.fractionToSqrtPriceX96(99, 1);
        highStrikeVault.harness_initVault(
            highStrike, 14 days, block.timestamp + 5 days,
            key, false, Currency.unwrap(currency1)
        );
        vm.startPrank(depositorAddr);
        IERC20(Currency.unwrap(currency1)).approve(address(highStrikeVault), HEDGE_AMOUNT);
        highStrikeVault.harness_deposit(depositorAddr, HEDGE_AMOUNT);
        vm.stopPrank();

        uint256 smallJitCapital = CAPITAL / 10;
        (uint256 hA0, uint256 hB0) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA0, uint256 uB0) = _snapshotBal(unhedgedPlpAddr);

        console.log("=== EPOCH: BELOW-STRIKE JIT ===");
        for (uint256 i; i < ROUNDS; ++i) {
            console.log("Round", i + 1);
            uint256 hTid = mintPosition(ctx, scenario, Protocol.UniswapV4, hedgedPlpPk, CAPITAL);
            uint256 uTid = mintPosition(ctx, scenario, Protocol.UniswapV4, unhedgedPlpPk, CAPITAL);
            vm.roll(block.number + JIT_ENTRY_OFFSET);
            uint256 jTid = mintPosition(ctx, scenario, Protocol.UniswapV4, jitLpPk, smallJitCapital);
            executeSwapWithAmount(ctx, Protocol.UniswapV4, swapperPk, ZERO_FOR_ONE, int256(TRADE_SIZE));
            vm.roll(block.number + 1);
            burnPosition(ctx, Protocol.UniswapV4, jitLpPk, jTid, smallJitCapital);
            vm.roll(block.number + PASSIVE_EXIT_OFFSET);
            burnPosition(ctx, Protocol.UniswapV4, hedgedPlpPk, hTid, CAPITAL);
            burnPosition(ctx, Protocol.UniswapV4, unhedgedPlpPk, uTid, CAPITAL);

            uint128 epochDp = IFeeConcentrationIndex(address(fciHarness)).getDeltaPlusEpoch(key, false);
            console.log("  Epoch delta+:", uint256(epochDp));

            vm.warp(block.timestamp + ROUND_INTERVAL);
            highStrikeVault.harness_pokeEpoch();
        }

        (uint256 hA1, uint256 hB1) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA1, uint256 uB1) = _snapshotBal(unhedgedPlpAddr);
        uint256 hedgedPayout = (hA1 + hB1) - (hA0 + hB0);
        uint256 unhedgedPayout = (uA1 + uB1) - (uA0 + uB0);

        (uint256 longPayout, uint256 shortPayout) = _settleVault(highStrikeVault, HEDGE_AMOUNT);

        assertEq(longPayout, 0, "LONG should be 0 when below strike");
        assertEq(longPayout + shortPayout, HEDGE_AMOUNT, "conservation");

        console.log("LONG payout:", longPayout);
    }
}
