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
import {Scenario} from "@foundry-script/types/Scenario.sol";
import {
    JitGameConfig,
    JitGameResult,
    JitAccounts,
    MultiRoundJitGameConfig,
    MultiRoundJitGameResult,
    VaultConfig,
    WelfareResult,
    runMultiRoundJitGameWithSchedule,
    UNIT_LIQUIDITY
} from "@foundry-script/simulation/JitGame.sol";
import "@foundry-script/utils/Constants.sol";

import {FciTokenVaultHarness} from "../helpers/FciTokenVaultHarness.sol";
import {LONG, SHORT} from "@fci-token-vault/modules/CollateralCustodianMod.sol";
import {SwapParams} from "v4-core/src/types/PoolOperation.sol";
import {PoolSwapTest} from "v4-core/src/test/PoolSwapTest.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";

contract JitGameWelfareComparisonTest is PosmTestSetup, FCITestHelper {
    using PoolIdLibrary for PoolKey;

    Context ctx;
    Scenario scenario; // zero-initialized storage; mintPosition/burnPosition use it internally
    FeeConcentrationIndexHarness fciHarness;
    PoolId poolId;

    uint256 constant CAPITAL = 1e18;
    uint256 constant HEDGE_AMOUNT = 0.1e18;
    uint256 constant TRADE_SIZE = 1e15;
    uint256 constant EPOCH_LENGTH = 1 days;

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

        // Initialize epoch metric on FCI hook
        fciHarness.initializeEpochPool(key, EPOCH_LENGTH);

        ctx.vm = vm;
        ctx.v4Pool = key;
        ctx.v4PositionManager = address(lpm);
        ctx.v4SwapRouter = address(swapRouter);
        ctx.chainId = block.chainid;

        Vm.Wallet memory w = vm.createWallet("depositor");
        depositorAddr = w.addr;
        depositorPk = w.privateKey;
        seedBalance(depositorAddr);
    }

    // ── Helpers ──

    function _deployVault() internal returns (FciTokenVaultHarness) {
        FciTokenVaultHarness v = new FciTokenVaultHarness();
        uint160 strike = SqrtPriceLibrary.fractionToSqrtPriceX96(56e18, 100e18);
        address collateral = Currency.unwrap(currency1);
        v.harness_initVault(strike, 14 days, block.timestamp + 7 days, key, false, collateral);

        vm.startPrank(depositorAddr);
        IERC20(collateral).approve(address(v), HEDGE_AMOUNT);
        v.harness_deposit(depositorAddr, HEDGE_AMOUNT);
        vm.stopPrank();

        return v;
    }

    function _makeAccounts(uint256 n) internal returns (JitAccounts memory acc) {
        acc.passiveLps = new Vm.Wallet[](n);
        for (uint256 i; i < n; ++i) {
            acc.passiveLps[i] = vm.createWallet(string.concat("passiveLp", vm.toString(i)));
            seedBalance(acc.passiveLps[i].addr);
            approvePosmFor(acc.passiveLps[i].addr);
        }
        acc.jitLp = vm.createWallet("jitLp");
        seedBalance(acc.jitLp.addr);
        approvePosmFor(acc.jitLp.addr);

        acc.swapper = vm.createWallet("swapper");
        seedBalance(acc.swapper.addr);
        vm.startPrank(acc.swapper.addr);
        IERC20(Currency.unwrap(currency0)).approve(address(swapRouter), type(uint256).max);
        IERC20(Currency.unwrap(currency1)).approve(address(swapRouter), type(uint256).max);
        vm.stopPrank();

        acc.hedgedIndex = 0;
    }

    function _runGame(
        uint256 rounds,
        uint256 jitCapital,
        bool[] memory jitSchedule
    ) internal returns (WelfareResult memory) {
        FciTokenVaultHarness vault = _deployVault();
        JitAccounts memory acc = _makeAccounts(2);

        MultiRoundJitGameConfig memory cfg = MultiRoundJitGameConfig({
            rounds: rounds,
            roundConfig: JitGameConfig({
                n: 2,
                jitCapital: jitCapital,
                jitEntryProbability: 0, // overridden by schedule
                tradeSize: TRADE_SIZE,
                zeroForOne: true,
                protocol: Protocol.UniswapV4
            })
        });

        VaultConfig memory vaultCfg = VaultConfig({
            vault: address(vault),
            depositAmount: HEDGE_AMOUNT,
            reactive: false
        });

        MultiRoundJitGameResult memory gameResult = runMultiRoundJitGameWithSchedule(
            ctx, scenario, cfg, acc, address(fciHarness), vaultCfg, jitSchedule
        );

        return gameResult.welfare;
    }

    /// @dev Push the pool price back toward 1:1 by swapping in the opposite direction.
    /// Each _runGame sub-game does zeroForOne=true swaps that push the price down.
    /// This helper executes a matching reverse swap to approximately restore the price.
    function _rebalancePool() internal {
        _rebalancePool(3);
    }

    function _rebalancePool(uint256 rounds) internal {
        uint256 rebalanceAmount = rounds * TRADE_SIZE;
        PoolSwapTest router = PoolSwapTest(address(swapRouter));
        router.swap(
            key,
            SwapParams({
                zeroForOne: false,
                amountSpecified: int256(rebalanceAmount),
                sqrtPriceLimitX96: TickMath.MAX_SQRT_PRICE - 1
            }),
            PoolSwapTest.TestSettings({takeClaims: false, settleUsingBurn: false}),
            ""
        );
    }

    // ── Baseline Scenarios ──

    function test_B1_equilibrium_no_jit() public {
        console.log("=== B1: EQUILIBRIUM (no JIT) ===");
        bool[] memory schedule = new bool[](3);
        // all false by default

        WelfareResult memory w = _runGame(3, 0, schedule);

        assertEq(w.longPayout, 0, "B1: LONG should be 0 -- no JIT harm");
        assertEq(w.longPayout + w.shortPayout, HEDGE_AMOUNT, "B1: conservation");
    }

    function test_B2_full_jit_crowdout() public {
        console.log("=== B2: FULL JIT CROWD-OUT ===");
        bool[] memory schedule = new bool[](3);
        schedule[0] = true;
        schedule[1] = true;
        schedule[2] = true;

        WelfareResult memory w = _runGame(3, 9e18, schedule);

        assertGt(w.longPayout, 0, "B2: LONG should be positive -- JIT harm");
        assertGt(w.hedgedWelfare, w.unhedgedWelfare, "B2: hedged should outperform unhedged");
        assertEq(w.longPayout + w.shortPayout, HEDGE_AMOUNT, "B2: conservation");
    }

    function test_B3_mixed_jit() public {
        console.log("=== B3: MIXED JIT ===");
        bool[] memory schedule = new bool[](3);
        schedule[0] = true;
        // schedule[1] = false (default)
        schedule[2] = true;

        WelfareResult memory w = _runGame(3, 9e18, schedule);

        assertGt(w.longPayout, 0, "B3: LONG should be positive -- JIT in 2 of 3 rounds");
        assertGt(w.hedgedWelfare, w.unhedgedWelfare, "B3: hedged should outperform unhedged");
        assertEq(w.longPayout + w.shortPayout, HEDGE_AMOUNT, "B3: conservation");
    }

    // ── Welfare-Targeted Scenarios ──

    function test_W1_sustained_jit_5_rounds() public {
        console.log("=== W1: SUSTAINED JIT (5 rounds) ===");
        bool[] memory schedule = new bool[](5);
        for (uint256 i; i < 5; ++i) schedule[i] = true;

        WelfareResult memory w = _runGame(5, 9e18, schedule);

        assertGt(w.longPayout, 0, "W1: LONG should be positive -- persistent JIT");
        assertGt(w.hedgedWelfare, w.unhedgedWelfare, "W1: hedged outperforms unhedged");
        assertEq(w.longPayout + w.shortPayout, HEDGE_AMOUNT, "W1: conservation");
    }

    function test_W3_early_jit_harm() public {
        console.log("=== W3: EARLY JIT HARM ===");
        bool[] memory schedule = new bool[](5);
        schedule[0] = true;
        schedule[1] = true;
        // rounds 2-4 clean

        WelfareResult memory w = _runGame(5, 9e18, schedule);

        assertGt(w.longPayout, 0, "W3: LONG should be positive -- early JIT harm");
        assertGt(w.hedgedWelfare, w.unhedgedWelfare, "W3: hedged outperforms unhedged");
        assertEq(w.longPayout + w.shortPayout, HEDGE_AMOUNT, "W3: conservation");
    }

    function test_W4_late_jit_harm() public {
        console.log("=== W4: LATE JIT HARM ===");
        bool[] memory schedule = new bool[](5);
        // rounds 0-2 clean
        schedule[3] = true;
        schedule[4] = true;

        WelfareResult memory w = _runGame(5, 9e18, schedule);

        assertGt(w.longPayout, 0, "W4: LONG should be positive -- late JIT harm");
        assertGt(w.hedgedWelfare, w.unhedgedWelfare, "W4: hedged outperforms unhedged");
        assertEq(w.longPayout + w.shortPayout, HEDGE_AMOUNT, "W4: conservation");
    }

    // ── Intensity Sweep ──

    function test_W2_jit_intensity_sweep() public {
        console.log("=== W2: JIT INTENSITY SWEEP ===");
        bool[] memory schedule = new bool[](3);
        schedule[0] = true;
        schedule[1] = true;
        schedule[2] = true;

        // Use capitals in the non-saturating range (below ~11x where payout caps at 100%).
        // 9x → ~68%, so 9.5x and 10x should produce monotonically higher payouts.
        console.log("--- 9x capital ---");
        WelfareResult memory wLo = _runGame(3, 9e18, schedule);
        console.log("");

        // Rebalance pool price for next sub-game
        _rebalancePool();

        console.log("--- 9.5x capital ---");
        WelfareResult memory wMid = _runGame(3, 95e17, schedule);
        console.log("");

        // Rebalance pool price for next sub-game
        _rebalancePool();

        console.log("--- 10x capital ---");
        WelfareResult memory wHi = _runGame(3, 10e18, schedule);

        // All should be hedge-profitable
        assertGt(wLo.longPayout, 0, "W2-lo: LONG > 0");
        assertGt(wMid.longPayout, 0, "W2-mid: LONG > 0");
        assertGt(wHi.longPayout, 0, "W2-hi: LONG > 0");

        // Monotonic: 10x > 9.5x > 9x
        assertGt(wHi.hedgeValue, wMid.hedgeValue, "W2: 10x hedge value > 9.5x");
        assertGt(wMid.hedgeValue, wLo.hedgeValue, "W2: 9.5x hedge value > 9x");

        // Conservation
        assertEq(wLo.longPayout + wLo.shortPayout, HEDGE_AMOUNT, "W2-lo: conservation");
        assertEq(wMid.longPayout + wMid.shortPayout, HEDGE_AMOUNT, "W2-mid: conservation");
        assertEq(wHi.longPayout + wHi.shortPayout, HEDGE_AMOUNT, "W2-hi: conservation");
    }

    // ── Cross-Scenario Assertions ──

    function test_W4_beats_W3_less_decay() public {
        console.log("=== CROSS: W4 vs W3 (late JIT > early JIT) ===");

        // W3: early JIT [Y,Y,N,N,N]
        bool[] memory scheduleW3 = new bool[](5);
        scheduleW3[0] = true;
        scheduleW3[1] = true;

        console.log("--- W3: Early JIT ---");
        WelfareResult memory w3 = _runGame(5, 9e18, scheduleW3);
        console.log("");

        // W4: late JIT [N,N,N,Y,Y]
        bool[] memory scheduleW4 = new bool[](5);
        scheduleW4[3] = true;
        scheduleW4[4] = true;

        // Rebalance pool price before second sub-game (5 rounds of zeroForOne swaps)
        _rebalancePool(5);

        console.log("--- W4: Late JIT ---");
        WelfareResult memory w4 = _runGame(5, 9e18, scheduleW4);

        // Late JIT = less decay before settlement = higher payout
        assertGt(w4.hedgeValue, w3.hedgeValue, "W4 hedge value > W3: less decay");
        assertGt(w4.longPayout, w3.longPayout, "W4 LONG payout > W3");
    }
}
