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

import {Context} from "@foundry-script/types/Context.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";
import {Scenario, mintPosition, burnPosition} from "@foundry-script/types/Scenario.sol";
import {executeSwapWithAmount} from "@foundry-script/simulation/JitGame.sol";
import "@foundry-script/utils/Constants.sol";

import {FciTokenVaultHarness} from "../helpers/FciTokenVaultHarness.sol";
import {LONG, SHORT} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {lookbackPayoffX96} from "@fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";

contract HedgedVsUnhedgedTest is PosmTestSetup, FCITestHelper {
    using PoolIdLibrary for PoolKey;

    Context ctx;
    Scenario scenario;
    FeeConcentrationIndexHarness fciHarness;
    FciTokenVaultHarness vault;
    PoolId poolId;

    // Test parameters
    uint256 constant CAPITAL = 1e18;
    uint256 constant HEDGE_AMOUNT = 0.1e18;
    uint256 constant TRADE_SIZE = 1e15;
    uint256 constant ROUNDS = 3;
    uint256 constant JIT_CAPITAL = 9e18;
    uint256 constant ROUND_INTERVAL = 1 days;

    address hedgedPlpAddr;
    uint256 hedgedPlpPk;
    address unhedgedPlpAddr;
    uint256 unhedgedPlpPk;
    address jitLpAddr;
    uint256 jitLpPk;
    address swapperAddr;
    uint256 swapperPk;

    function setUp() public {
        // Deploy V4 infrastructure
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();
        deployAndApprovePosm(manager);

        fciLP = makeAddr("defaultLP");
        fciSwapper = address(this);
        fciSwapRouter = swapRouter;

        // Deploy FCI hook via HookMiner
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
        fciHarness = new FeeConcentrationIndexHarness{salt: salt}(lpm);
        require(address(fciHarness) == hookAddress, "hook address mismatch");

        // Init pool
        (key, poolId) = initPool(
            currency0, currency1,
            IHooks(address(fciHarness)),
            3000,
            SQRT_PRICE_1_1
        );

        // Wire Context
        ctx.vm = vm;
        ctx.v4Pool = key;
        ctx.v4PositionManager = address(lpm);
        ctx.v4SwapRouter = address(swapRouter);
        ctx.chainId = block.chainid;

        // Initialize epoch metric on FCI hook (required for getDeltaPlusEpoch)
        fciHarness.initializeEpochPool(key, ROUND_INTERVAL);

        // Deploy vault harness
        vault = new FciTokenVaultHarness();
        // Strike at Δ* = 0.80 — calibrated so JIT crowd-out (9:1 capital ratio)
        // produces partial payoff in the non-saturating region of the power-4 lookback.
        // Higher strike → HWM/strike ratio closer to 1 → (ratio)^4 stays below 2.
        uint160 strikePrice = SqrtPriceLibrary.fractionToSqrtPriceX96(80, 100);
        // Expiry 5 days: 3 rounds × 1 day = 3 days of pokes.
        // Epoch-only: no decay. HWM is pure high-water mark.
        vault.harness_initVault(
            strikePrice,
            block.timestamp + 5 days,
            key,
            false,
            Currency.unwrap(currency1)
        );

        // Create wallets
        Vm.Wallet memory w;
        w = vm.createWallet("hedgedPlp");
        hedgedPlpAddr = w.addr; hedgedPlpPk = w.privateKey;
        w = vm.createWallet("unhedgedPlp");
        unhedgedPlpAddr = w.addr; unhedgedPlpPk = w.privateKey;
        w = vm.createWallet("jitLp");
        jitLpAddr = w.addr; jitLpPk = w.privateKey;
        w = vm.createWallet("swapper");
        swapperAddr = w.addr; swapperPk = w.privateKey;

        // Fund and approve all actors
        _setupLP(hedgedPlpAddr);
        _setupLP(unhedgedPlpAddr);
        _setupLP(jitLpAddr);
        _setupSwapper(swapperAddr);
    }

    // ═══════════════════════════════════════════════════════════
    // Helpers
    // ═══════════════════════════════════════════════════════════

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

    // Block offsets matching Capponi timing model (from JitGame.sol)
    uint256 constant JIT_ENTRY_OFFSET = 49;
    uint256 constant PASSIVE_EXIT_OFFSET = 50;

    /// @dev Execute one complete round following JitGame timing:
    /// Passive LPs enter → roll 49 → JIT enters → swap → JIT exits → roll 50 →
    /// passive LPs exit (triggers FCI observation) → poke() → warp time
    function _runRound(
        bool jitEnters,
        uint256 jitCapital,
        uint256 hedgedLiq,
        uint256 unhedgedLiq
    ) internal returns (uint256 hedgedTokenId, uint256 unhedgedTokenId) {
        // Passive LP entry (block B)
        hedgedTokenId = mintPosition(
            ctx, scenario, Protocol.UniswapV4, hedgedPlpPk, hedgedLiq
        );
        unhedgedTokenId = mintPosition(
            ctx, scenario, Protocol.UniswapV4, unhedgedPlpPk, unhedgedLiq
        );

        // Roll to JIT entry block
        vm.roll(block.number + JIT_ENTRY_OFFSET);

        // JIT entry (if applicable)
        uint256 jitTokenId;
        if (jitEnters) {
            jitTokenId = mintPosition(
                ctx, scenario, Protocol.UniswapV4, jitLpPk, jitCapital
            );
        }

        // Swap
        executeSwapWithAmount(
            ctx, Protocol.UniswapV4, swapperPk, ZERO_FOR_ONE, int256(TRADE_SIZE)
        );

        // JIT exit (next block)
        vm.roll(block.number + 1);
        if (jitEnters) {
            burnPosition(ctx, Protocol.UniswapV4, jitLpPk, jitTokenId, jitCapital);
        }

        // Roll to passive exit — FCI needs afterRemoveLiquidity to observe
        vm.roll(block.number + PASSIVE_EXIT_OFFSET);

        // Passive LP exit — triggers FCI fee concentration observation
        burnPosition(ctx, Protocol.UniswapV4, hedgedPlpPk, hedgedTokenId, hedgedLiq);
        burnPosition(ctx, Protocol.UniswapV4, unhedgedPlpPk, unhedgedTokenId, unhedgedLiq);

        // Poke vault BEFORE warp (epoch metric reads current epoch's delta-plus)
        vault.harness_pokeEpoch();
        // Advance time to next epoch
        vm.warp(block.timestamp + ROUND_INTERVAL);
    }

    /// @dev Settle vault and redeem. plpAddr is both depositor and redeemer.
    function _settleAndRedeem(FciTokenVaultHarness v, address plpAddr, uint256 depositAmount)
        internal
        returns (uint256 longPayout, uint256 shortPayout)
    {
        (,, uint256 expiry,,,) = v.harness_getVaultStorage();
        vm.warp(expiry + 1);
        v.harness_settle();
        (,,,,, uint256 longPayoutPerToken) = v.harness_getVaultStorage();
        longPayout = (depositAmount * longPayoutPerToken) / SqrtPriceLibrary.Q96;
        shortPayout = depositAmount - longPayout;
        vm.prank(plpAddr);
        v.harness_redeem(plpAddr, depositAmount);
    }

    /// @dev Measure cumulative welfare: token balances after all rounds vs before any LP activity
    function _snapshotBal(address who) internal view returns (uint256 a, uint256 b) {
        a = IERC20(Currency.unwrap(currency0)).balanceOf(who);
        b = IERC20(Currency.unwrap(currency1)).balanceOf(who);
    }

    // ═══════════════════════════════════════════════════════════
    // Scenario 1: Equilibrium — no JIT
    // ═══════════════════════════════════════════════════════════

    function test_equilibrium_no_jit() public {
        // Hedged PLP deposits from OWN capital — self-funded insurance
        _depositToVault(hedgedPlpAddr, HEDGE_AMOUNT);
        uint256 hedgedLiq = CAPITAL - HEDGE_AMOUNT;

        // Snapshot balances BEFORE LP rounds
        (uint256 hA0, uint256 hB0) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA0, uint256 uB0) = _snapshotBal(unhedgedPlpAddr);

        // Hedged PLP has less LP capital (paid for insurance)
        for (uint256 i; i < ROUNDS; ++i) {
            _runRound(false, 0, hedgedLiq, CAPITAL);
        }

        (uint256 hA1, uint256 hB1) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA1, uint256 uB1) = _snapshotBal(unhedgedPlpAddr);

        uint256 hedgedPayout = (hA1 + hB1) - (hA0 + hB0);
        uint256 unhedgedPayout = (uA1 + uB1) - (uA0 + uB0);

        (uint256 longPayout, uint256 shortPayout) = _settleAndRedeem(vault, hedgedPlpAddr, HEDGE_AMOUNT);

        uint256 hedgedWelfare = hedgedPayout + longPayout;
        uint256 unhedgedWelfare = unhedgedPayout;

        // Property 2: No false trigger — no JIT → LONG = 0, hedged gets deposit back but earned less fees
        assertEq(longPayout, 0, "LONG should be 0 in equilibrium");

        // Property 3: Vault solvency
        assertEq(longPayout + shortPayout, HEDGE_AMOUNT, "conservation: long + short = deposit");

        console.log("=== EQUILIBRIUM (no JIT) ===");
        console.log("Hedged LP payout:", hedgedPayout);
        console.log("Unhedged LP payout:", unhedgedPayout);
        console.log("LONG payout:", longPayout);
        console.log("Hedged welfare:", hedgedWelfare);
        console.log("Unhedged welfare:", unhedgedWelfare);
    }

    // ═══════════════════════════════════════════════════════════
    // Scenario 2: JIT crowd-out — hedge compensates
    // ═══════════════════════════════════════════════════════════

    function test_jit_crowdout_hedge_compensates() public {
        // Hedged PLP deposits from OWN capital — self-funded insurance
        _depositToVault(hedgedPlpAddr, HEDGE_AMOUNT);
        uint256 hedgedLiq = CAPITAL - HEDGE_AMOUNT;

        (uint256 hA0, uint256 hB0) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA0, uint256 uB0) = _snapshotBal(unhedgedPlpAddr);

        // Hedged PLP has less LP capital (paid for insurance)
        for (uint256 i; i < ROUNDS; ++i) {
            _runRound(true, JIT_CAPITAL, hedgedLiq, CAPITAL);

            // Property 4: HWM captures current price after each poke
            (,uint160 sqrtPriceHWM,,,,) = vault.harness_getVaultStorage();
            assertGt(uint256(sqrtPriceHWM), 0, "HWM should be > 0 after JIT round");
        }

        // Record pre-settlement HWM
        (,uint160 hwmBeforeSettle,,,,) = vault.harness_getVaultStorage();

        (uint256 hA1, uint256 hB1) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA1, uint256 uB1) = _snapshotBal(unhedgedPlpAddr);
        uint256 hedgedPayout = (hA1 + hB1) - (hA0 + hB0);
        uint256 unhedgedPayout = (uA1 + uB1) - (uA0 + uB0);

        (uint256 longPayout, uint256 shortPayout) = _settleAndRedeem(vault, hedgedPlpAddr, HEDGE_AMOUNT);

        // Hedged PLP: less LP fees (less capital) + insurance payout
        // Unhedged PLP: full LP fees (full capital)
        uint256 hedgedWelfare = hedgedPayout + longPayout;
        uint256 unhedgedWelfare = unhedgedPayout;

        // Property 1: Payoff compensation — insurance compensates for JIT crowd-out
        assertGt(hedgedWelfare, unhedgedWelfare, "hedged should earn more under JIT crowd-out");
        assertGt(longPayout, 0, "LONG should be positive under JIT crowd-out");

        // Property 3: Vault solvency
        assertEq(longPayout + shortPayout, HEDGE_AMOUNT, "conservation: long + short = deposit");

        console.log("=== JIT CROWD-OUT ===");
        console.log("Hedged LP payout:", hedgedPayout);
        console.log("Unhedged LP payout:", unhedgedPayout);
        console.log("LONG payout:", longPayout);
        console.log("Hedged welfare:", hedgedWelfare);
        console.log("Unhedged welfare:", unhedgedWelfare);
        console.log("Net hedge benefit:", hedgedWelfare - unhedgedWelfare);
        console.log("HWM before settle:", uint256(hwmBeforeSettle));
    }

    // ═══════════════════════════════════════════════════════════
    // Scenario 3: Below-strike JIT — no false trigger
    // ═══════════════════════════════════════════════════════════

    function test_below_strike_no_false_trigger() public {
        // Deploy a SEPARATE vault with very high strike (Δ* ≈ 0.99)
        FciTokenVaultHarness highStrikeVault = new FciTokenVaultHarness();
        uint160 highStrike = SqrtPriceLibrary.fractionToSqrtPriceX96(99, 1);
        highStrikeVault.harness_initVault(
            highStrike, block.timestamp + 5 days,
            key, false, Currency.unwrap(currency1)
        );
        // Hedged PLP funds the high-strike vault from OWN capital
        vm.startPrank(hedgedPlpAddr);
        IERC20(Currency.unwrap(currency1)).approve(address(highStrikeVault), HEDGE_AMOUNT);
        highStrikeVault.harness_deposit(hedgedPlpAddr, HEDGE_AMOUNT);
        vm.stopPrank();

        uint256 hedgedLiq = CAPITAL - HEDGE_AMOUNT;
        uint256 smallJitCapital = CAPITAL / 10;

        (uint256 hA0, uint256 hB0) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA0, uint256 uB0) = _snapshotBal(unhedgedPlpAddr);

        for (uint256 i; i < ROUNDS; ++i) {
            // Manual round using highStrikeVault for poke
            uint256 hTid = mintPosition(ctx, scenario, Protocol.UniswapV4, hedgedPlpPk, hedgedLiq);
            uint256 uTid = mintPosition(ctx, scenario, Protocol.UniswapV4, unhedgedPlpPk, CAPITAL);
            vm.roll(block.number + JIT_ENTRY_OFFSET);
            uint256 jTid = mintPosition(ctx, scenario, Protocol.UniswapV4, jitLpPk, smallJitCapital);
            executeSwapWithAmount(ctx, Protocol.UniswapV4, swapperPk, ZERO_FOR_ONE, int256(TRADE_SIZE));
            vm.roll(block.number + 1);
            burnPosition(ctx, Protocol.UniswapV4, jitLpPk, jTid, smallJitCapital);
            vm.roll(block.number + PASSIVE_EXIT_OFFSET);
            burnPosition(ctx, Protocol.UniswapV4, hedgedPlpPk, hTid, hedgedLiq);
            burnPosition(ctx, Protocol.UniswapV4, unhedgedPlpPk, uTid, CAPITAL);
            highStrikeVault.harness_pokeEpoch();
            vm.warp(block.timestamp + ROUND_INTERVAL);
        }

        (uint256 hA1, uint256 hB1) = _snapshotBal(hedgedPlpAddr);
        (uint256 uA1, uint256 uB1) = _snapshotBal(unhedgedPlpAddr);
        uint256 hedgedPayout = (hA1 + hB1) - (hA0 + hB0);
        uint256 unhedgedPayout = (uA1 + uB1) - (uA0 + uB0);

        (uint256 longPayout, uint256 shortPayout) = _settleAndRedeem(highStrikeVault, hedgedPlpAddr, HEDGE_AMOUNT);

        uint256 hedgedWelfare = hedgedPayout + longPayout;
        uint256 unhedgedWelfare = unhedgedPayout;

        // Property 2: No false trigger — below strike, hedge COSTS (less LP capital, no payout)
        assertEq(longPayout, 0, "LONG should be 0 when below strike");
        assertLt(hedgedWelfare, unhedgedWelfare, "hedged should earn less when below strike");

        // Property 3: Vault solvency
        assertEq(longPayout + shortPayout, HEDGE_AMOUNT, "conservation: long + short = deposit");

        console.log("=== BELOW-STRIKE JIT ===");
        console.log("Hedged LP payout:", hedgedPayout);
        console.log("Unhedged LP payout:", unhedgedPayout);
        console.log("LONG payout:", longPayout);
        console.log("Hedged welfare:", hedgedWelfare);
        console.log("Unhedged welfare:", unhedgedWelfare);
    }
}
