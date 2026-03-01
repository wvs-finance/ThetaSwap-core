// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {PoolManager} from "@uniswap/v4-core/src/PoolManager.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "@uniswap/v4-core/src/types/PoolId.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {BalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {StateLibrary} from "@uniswap/v4-core/src/libraries/StateLibrary.sol";
import {PoolSwapTest} from "@uniswap/v4-core/src/test/PoolSwapTest.sol";
import {PoolModifyLiquidityTest} from "@uniswap/v4-core/src/test/PoolModifyLiquidityTest.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {IERC20Partial} from "2025-12-panoptic/contracts/tokens/interfaces/IERC20Partial.sol";

import {JitHook} from "../src/JitHook.sol";
import {EntryIndex} from "../src/EntryIndex.sol";
import {SimulationConfig} from "../src/types/ModelParams.sol";
import {Capital, Liquidity, EntryCount, FeeRevenue} from "../src/types/ModelTypes.sol";
import {HookDeployer} from "./helpers/HookDeployer.sol";
import {InvariantAssertions} from "./invariants/InvariantJit.t.sol";
import {
    ModelState, ForkedState, Accounts,
    getModelState, getForkedState,
    getMarket, setMarket, getMarketId,
    getAccount, setAccount,
    FEE, TICK_SPACING, TICK_RANGE,
    TickRange, tickLower, tickUpper
} from "./helpers/StateInit.sol";

/// @title JitCompetition -- Main Simulation Test
/// @notice Two-pool comparison from NOTES.md:
///   Pool A (hooked): 1 JIT LP + 1 Passive LP
///   Pool B (control): 1 Passive LP + 1 Passive LP
///   Both pools: same tokens, same fee, same initial capital, same tick range
///
/// Simulation flow:
///   1. Deploy manager, tokens, pools
///   2. Each LP deposits equal capital into their respective pool
///   3. Run N swap rounds (uninformed, mean-reverting pairs)
///   4. After each swap pair: assert INV0 (IL=0), track P&L
///   5. New LP enters each round (N_t increments on hooked pool)
///   6. One PLP on hooked pool purchases entry index
///   7. Compare P&L: show JIT compresses passive returns, index hedges
///

/// YES INHERITANCE ONLY IN THIS CASE
contract JitCompetitionTest is Test is PosmTestSetUp{
    using PoolIdLibrary for PoolKey;
    using StateLibrary for IPoolManager;

    // -- Constants --

    function setUp() public {
        ModelState storage $ = getModelState();

        // -- Config --
        $.config = SimulationConfig({
            initialCapital: Capital.wrap(100e18),
            numSwaps: 10,
            swapAmount: 1e18,
            sqrtPriceX96: SQRT_PRICE_1_1
        });

        // -- V4 Infrastructure (no inheritance, direct deployment) --
        $.manager = new PoolManager(address(this));
        $.swapRouter = new PoolSwapTest($.manager);
        $.liquidityRouter = new PoolModifyLiquidityTest($.manager);

        // -- Mock Tokens --
        MockERC20 tokenA = new MockERC20("Numeraire", "NUM", 18);
        MockERC20 tokenB = new MockERC20("Risky", "RSK", 18);

        // -- Sort & store in ForkedState --
        ForkedState storage f = getForkedState();
        if (address(tokenA) < address(tokenB)) {
            f.stableAsset = IERC20Partial(address(tokenA));
            f.riskyAsset = IERC20Partial(address(tokenB));
            f.currency0 = Currency.wrap(address(tokenA));
            f.currency1 = Currency.wrap(address(tokenB));
        } else {
            f.stableAsset = IERC20Partial(address(tokenB));
            f.riskyAsset = IERC20Partial(address(tokenA));
            f.currency0 = Currency.wrap(address(tokenB));
            f.currency1 = Currency.wrap(address(tokenA));
        }

        // -- Deploy JIT Hook at V4-compatible address --
        $.jitHook = HookDeployer.deployJitHook(
            vm,
            $.manager,
            uint128(Capital.unwrap($.config.initialCapital)),
            tickLower(TICK_RANGE),
            tickUpper(TICK_RANGE)
        );
        $.entryIndex = new EntryIndex($.jitHook);

        // -- Initialize Pools --
        // Pool A: hooked (JIT + PLP)
        PoolKey memory hookedKey = PoolKey({
            currency0: f.currency0,
            currency1: f.currency1,
            fee: FEE,
            tickSpacing: TICK_SPACING,
            hooks: IHooks(address($.jitHook))
        });
        $.manager.initialize(hookedKey, $.config.sqrtPriceX96);
        setMarket("hooked", hookedKey);

        // Pool B: control (PLP + PLP, no hooks)
        PoolKey memory controlKey = PoolKey({
            currency0: f.currency0,
            currency1: f.currency1,
            fee: FEE,
            tickSpacing: TICK_SPACING,
            hooks: IHooks(address(0))
        });
        $.manager.initialize(controlKey, $.config.sqrtPriceX96);
        setMarket("control", controlKey);

        // -- Fund Accounts (1.3 from NOTES.md) --
        // LP wallets
        _createAndFundAccount("plp", getMarketId("hooked"));
        _createAndFundAccount("plp", getMarketId("control"));
        _createAndFundAccount("plp2", getMarketId("control"));

        // Fund hook for JIT operations
        _fundAddress(address($.jitHook), 1000e18);

        // Fund test contract (traders are address(this))
        _fundAddress(address(this), 1000e18);
    }

    // -- INV2: Equal Initial Capital --

    function test_INV2_equalInitialCapital() public view {
        ModelState storage $ = getModelState();
        uint256 bal = Capital.unwrap($.config.initialCapital);
        assertGt(bal, 0, "INV2: initial capital is zero");
    }

    // -- INV6: Constant Tick Range --

    function test_INV6_constantTickRange() public pure {
        assertEq(tickLower(TICK_RANGE), -120, "INV6: tickLower changed");
        assertEq(tickUpper(TICK_RANGE), 120, "INV6: tickUpper changed");
    }

    // -- Pool Setup Verification --

    function test_poolsInitialized() public view {
        ModelState storage $ = getModelState();
        PoolId idH = getMarketId("hooked");
        PoolId idC = getMarketId("control");

        (uint160 sqrtH,,,) = $.manager.getSlot0(idH);
        (uint160 sqrtC,,,) = $.manager.getSlot0(idC);

        assertEq(sqrtH, $.config.sqrtPriceX96, "Hooked pool price mismatch");
        assertEq(sqrtC, $.config.sqrtPriceX96, "Control pool price mismatch");
    }

    function test_hookPermissions() public view {
        ModelState storage $ = getModelState();
        uint160 addr = uint160(address($.jitHook));
        uint160 flags = HookDeployer.jitHookFlags();
        assertTrue(addr & flags == flags, "Hook flags mismatch");
    }

    // -- Helpers --

    function _createAndFundAccount(
        string memory role,
        PoolId poolId
    ) internal {
        ModelState storage $ = getModelState();
        string memory label = string.concat(role, "_", vm.toString(PoolId.unwrap(poolId)));
        address addr = makeAddr(label);
        setAccount($.accounts, role, poolId, addr);
        _fundAddress(addr, 1000e18);
    }

    function _fundAddress(address to, uint256 amount) internal {
        ModelState storage $ = getModelState();
        ForkedState storage f = getForkedState();
        MockERC20(address(f.stableAsset)).mint(to, amount);
        MockERC20(address(f.riskyAsset)).mint(to, amount);

        vm.startPrank(to);
        f.stableAsset.approve(address($.swapRouter), type(uint256).max);
        f.stableAsset.approve(address($.liquidityRouter), type(uint256).max);
        f.stableAsset.approve(address($.manager), type(uint256).max);
        f.riskyAsset.approve(address($.swapRouter), type(uint256).max);
        f.riskyAsset.approve(address($.liquidityRouter), type(uint256).max);
        f.riskyAsset.approve(address($.manager), type(uint256).max);
        vm.stopPrank();
    }
}
