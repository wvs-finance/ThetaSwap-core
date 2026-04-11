// SPDX-License-Identifier: BUSL-1.1
pragma solidity >=0.8.26;

import {AngstromTest} from "anstrong-test/Angstrom.t.sol";
import {PanopticPoolTest} from "anstrong-test/PanopticPoolAngstromCompatibleTests.t.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {V4RouterSimple} from "panoptic-v2/test/testUtils/V4RouterSimple.sol";
import {
    SemiFungiblePositionManagerHarness,
    PanopticPoolHarness
} from "anstrong-test/PanopticPoolAngstromCompatibleTests.t.sol";
import {
    ISemiFungiblePositionManager
} from "panoptic-v2/src/interfaces/ISemiFungiblePositionManager.sol";
import {PanopticHelper} from "panoptic-v2/test/test_periphery/PanopticHelper.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {TokenId, TokenIdLibrary} from "panoptic-v2/src/types/TokenId.sol";
import {console2} from "forge-std/console2.sol";
import {FixedPointMathLib} from "solady/src/utils/FixedPointMathLib.sol";
import {Constants} from "panoptic-v2/src/libraries/Constants.sol";
import {IUniV4} from "core/src/interfaces/IUniV4.sol";
import {PoolManager as PoolManager_} from "v4-core/src/PoolManager.sol";
import {LiquidityAmounts} from "panoptic-v2/v3-periphery/libraries/LiquidityAmounts.sol";
import {SqrtPriceMath} from "panoptic-v2/v3-core/libraries/SqrtPriceMath.sol";
import {BalanceDelta, toBalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {Math} from "panoptic-v2/src/libraries/Math.sol";
import {PanopticMath} from "panoptic-v2/src/libraries/PanopticMath.sol";
import {LeftRightUnsigned, LeftRightSigned} from "panoptic-v2/src/types/LeftRight.sol";

uint256 constant ONE = 1e27;
uint16 constant DEFAULT_TICK_SPACING = 60;
uint248 constant DEFAULT_START_LIQUIDITY = 100_000e21;

// MAX_UNLOCK_FEE_E6 / 2
uint24 constant DEFAULT_UNLOCK_FEE = 200_000;
uint24 constant DEFAULT_PROTOCOL_UNLOCK_FEE = 0;

uint256 constant DEFAULT_OPTION_RATIO = 1; // optionRatio per leg (7-bit, max 127)
uint256 constant DEFAULT_POSITION_SIZE_SEED = 1e18; // seed for populatePositionData (bound to [1e15, 1e20])
uint32 constant DEFAULT_BLOCK_DELTA = 2;
uint88 constant DEFAULT_TICK_VOLATILITY = 14400; // width=2 at 2-block horizon, tickSpacing=60
uint256 constant NAKED = 0;

enum Underlying {
    A,
    B
}
enum OptionPosition {
    SHORT,
    LONG
}

enum OptionType {
    CALL,
    PUT
}

library VolToWidthLib {
    using FixedPointMathLib for uint256;

    function volToWidth(uint88 volatilityAverage, uint32 horizonBlocks, int24 tickSpacing)
        internal
        pure
        returns (int24 width)
    {
        uint256 tickStdDev = uint256(volatilityAverage).sqrt();
        uint256 sqrtHorizon = uint256(horizonBlocks).sqrt();
        uint256 deltaTick = tickStdDev * sqrtHorizon;

        uint256 spacing = uint256(uint24(tickSpacing));
        uint256 raw = (deltaTick + spacing - 1) / spacing;

        if (raw < 1) raw = 1;
        if (raw > 4095) raw = 4095;
        width = int24(uint24(raw));
    }

    function strikeFromVol(
        int24 currentTick,
        uint88 volatilityAverage,
        uint32 horizonBlocks,
        int24 tickSpacing,
        bool isCall
    ) internal pure returns (int24 strike) {
        uint256 tickStdDev = uint256(volatilityAverage).sqrt();
        uint256 sqrtHorizon = uint256(horizonBlocks).sqrt();
        int24 deltaTick = int24(int256(tickStdDev * sqrtHorizon));

        strike = !isCall
            ? currentTick + deltaTick  // short put: strike 1σ above
            : currentTick - deltaTick; // short call: strike 1σ below

        strike = (strike / tickSpacing) * tickSpacing;
    }

    function widthToVol(int24 width, int24 tickSpacing, uint32 horizonBlocks)
        internal
        pure
        returns (uint88 volatilityAverage)
    {
        uint256 deltaTick = uint256(uint24(width)) * uint256(uint24(tickSpacing));
        volatilityAverage = uint88((deltaTick * deltaTick) / uint256(horizonBlocks));
    }

    function amount0OnSwapForOption(
        int24 strike,
        int24 width,
        int24 tickSpacing,
        uint160 currentSqrtPriceX96,
        uint128 liquidity
    ) internal pure returns (int256, int24, int24) {
        (int24 tickLower, int24 tickUpper) = PanopticMath.getTicks(strike, width, tickSpacing);
        uint160 sqrtLower = TickMath.getSqrtPriceAtTick(tickLower);
        uint160 sqrtUpper = TickMath.getSqrtPriceAtTick(tickUpper);
        int256 amount0Required = SqrtPriceMath.getAmount0Delta(
            currentSqrtPriceX96 < sqrtLower ? sqrtLower : currentSqrtPriceX96,
            sqrtUpper,
            int128(liquidity)
        );
        return (amount0Required, tickLower, tickUpper);
    }
}

library OptionBuilderLibrary {
    using TokenIdLibrary for TokenId;

    function init(
        uint64 __poolId,
        Underlying _underlying,
        OptionPosition _optionPosition,
        OptionType _optionType
    ) internal pure returns (TokenId tokenId) {
        tokenId = TokenId.wrap(0).addPoolId(__poolId);
        tokenId = tokenId.addOptionRatio(DEFAULT_OPTION_RATIO, 0);
        tokenId = tokenId.addAsset(uint256(uint8(_underlying)), 0);
        tokenId = tokenId.addIsLong(uint256(uint8(_optionPosition)), 0);
        tokenId = tokenId.addTokenType(uint256(uint8(_optionType)), 0);
    }

    function finish(TokenId tokenId, int24 strike, int24 width) internal pure returns (TokenId) {
        tokenId = tokenId.addStrike(strike, 0);
        tokenId = tokenId.addWidth(width, 0);
        tokenId = tokenId.addRiskPartner(NAKED, 0);
        return tokenId;
    }
}

// NOTE: This assumes MEV ~ 0 AND block-number granularity

contract PanopticPlaygroundTest is AngstromTest, PanopticPoolTest {
    using PoolIdLibrary for PoolKey;
    using OptionBuilderLibrary for TokenId;
    using IUniV4 for PoolManager_;

    PoolKey testPoolKey;
    PoolId testPoolId;
    uint256 sellerBalanceStart;

    function swapToStrike(int24 strike, int24 width, int24 _tickSpacing)
        internal
        returns (BalanceDelta delta)
    {
        (int24 tickLower, int24 tickUpper) = PanopticMath.getTicks(strike, width, _tickSpacing);

        // 10 rounds of back-and-forth swaps oscillating around the strike
        // to generate fees through the option's tick range [tickLower, tickUpper]
        for (uint256 i = 0; i < 10; ++i) {
            vm.roll(block.number + 1);
            vm.prank(Alice);
            angstrom.execute("");

            // Push price above the option range upper bound
            actor.swap(_poolKey, false, -type(int256).max, TickMath.getSqrtPriceAtTick(tickUpper));

            vm.roll(block.number + 1);
            vm.prank(Alice);
            angstrom.execute("");

            // Pull price back below the option range lower bound
            actor.swap(_poolKey, true, -type(int256).max, TickMath.getSqrtPriceAtTick(tickLower));
        }

        // Final push to strike
        vm.roll(block.number + 1);
        vm.prank(Alice);
        angstrom.execute("");

        delta = actor.swap(_poolKey, false, -type(int256).max, TickMath.getSqrtPriceAtTick(strike));
    }

    function setUp() public override(AngstromTest, PanopticPoolTest) {
        AngstromTest.setUp();

        PanopticPoolTest.setUp();
        manager = uni;
        routerV4 = new V4RouterSimple(manager);
        sfpm = new SemiFungiblePositionManagerHarness(manager);
        ph = new PanopticHelper(ISemiFungiblePositionManager(address(sfpm)));
        poolReference = address(new PanopticPoolHarness(sfpm));

        Swapper = address(actor);
        Deployer = address(controller);

        {
            Alice = node.addr;
            Bob = node.addr;
            Charlie = node.addr;
            Seller = makeAddr("seller");
        }

        token0 = asset0;
        token1 = asset1;
    }

    function initPool() internal {
        console2.log("===> INIT POOL < ====");
        testPoolKey = _createPool(
            DEFAULT_TICK_SPACING,
            DEFAULT_UNLOCK_FEE,
            DEFAULT_START_LIQUIDITY,
            DEFAULT_PROTOCOL_UNLOCK_FEE
        );

        console2.log("Pair A/B", "");
        console2.log("Tick Spacing (D tick) :", DEFAULT_TICK_SPACING);
        console2.log("Init Liquidity (L_0):", DEFAULT_START_LIQUIDITY);
        testPoolId = testPoolKey.toId();

        _poolKey = testPoolKey;
        tickSpacing = int24(uint24(DEFAULT_TICK_SPACING));
        currentSqrtPriceX96 = PoolManager_(address(uni)).getSlot0(testPoolId).sqrtPriceX96();
        console2.log("Current Price (P_(A/B)): ", currentSqrtPriceX96);
        currentTick = PoolManager_(address(uni)).getSlot0(testPoolId).tick();
        console2.log("Current tick i [P_(A/B)]: ", currentTick);
        _poolId = uint40(uint256(PoolId.unwrap(testPoolId))) + uint64(uint256(vegoid) << 40);
        _poolId += uint64(uint24(tickSpacing)) << 48;

        _deployPanopticPool();

        _initAccounts();
    }

    function test__PanopticAngstrom__ShortPutNoMEVBlockNumberTimeFrequency() public {
        console2.log(
            "=====================PRE-CONDITIONS(WRITING THE OPTION )================================"
        );
        initPool();

        // Add liquidity spanning current tick through beyond the strike
        // so swaps have resistance when pushing price to tick 240
        actor.modifyLiquidity(
            _poolKey, int24(0), int24(360), int256(uint256(DEFAULT_START_LIQUIDITY)), bytes32(0)
        );

        console2.log(
            "============================TEST(WRITING THE OPTION)============================"
        );
        sellerBalanceStart = ct1.balanceOf(Seller);
        console2.log("Seller C :: Collateral balance (before mint): ", sellerBalanceStart);
        vm.startPrank(Seller);
        console2.log("Actor C", Seller);

        int24 strike = VolToWidthLib.strikeFromVol(
            currentTick,
            DEFAULT_TICK_VOLATILITY,
            DEFAULT_BLOCK_DELTA,
            int24(uint24(DEFAULT_TICK_SPACING)),
            false // short put → strike 1σ below
        );

        console2.log("believes fair value is P*_{A/B} = 3", strike);

        console2.log("Actor C's view on the expected velocity of the forecasted movement", "");

        int24 width = VolToWidthLib.volToWidth(
            DEFAULT_TICK_VOLATILITY, DEFAULT_BLOCK_DELTA, int24(uint24(DEFAULT_TICK_SPACING))
        );

        console2.log("is proportional to the length of his belief, sqrt(T)", width);

        console2.log("Actor C wants to benefit from max(P*_{A/B} - P_{A/B}, 0)", "");
        console2.log("His options are:", "");
        console2.log("(1) Long an OTM call with strike P*_{A/B} = 3", strike);
        console2.log("call = max(P*_{A/B} - P_{A/B}, 0) - premia", "");
        console2.log("(2) Short a put with strike", strike);
        console2.log("--> HE DECIDES ON (2) <----", "");

        console2.log("put  = max(P_{A/B} - P*_{A/B}, 0) - premia", "");
        console2.log("=> -put  = max(P*_{A/B} - P_{A/B}, 0) + premia = call + 2*premia", "");

        TokenId tokenId = OptionBuilderLibrary.finish(
            OptionBuilderLibrary.init(_poolId, Underlying.A, OptionPosition.SHORT, OptionType.PUT),
            strike,
            width
        );

        populatePositionData(width, strike, DEFAULT_POSITION_SIZE_SEED);

        TokenId[] memory posIdList = new TokenId[](1);
        posIdList[0] = tokenId;

        mintOptions(
            pp, posIdList, positionSize, 0, Constants.MIN_POOL_TICK, Constants.MAX_POOL_TICK, true
        );

        console2.log(
            "==========================POST-CONDITIONS (WRITING THE OPTION )=========================================="
        );

        console2.log(
            "Seller C :: Option Notional: ", sfpm.balanceOf(address(pp), TokenId.unwrap(tokenId))
        );
        console2.log(
            "Since the option is a put, it MUST be cash-secured. The CollateralTracker tracks token B because A is measured against B (token 0 = A, token 1 = B).",
            ""
        );
        (, uint256 marginDeposited,,) = ct1.getPoolData();

        uint256 amount1 = LiquidityAmounts.getAmount1ForLiquidity(sqrtLower, sqrtUpper, expectedLiq);

        console2.log("M_B  = L(nominal)*(sqrt(p_u) - sqrt(p_l))", amount1);
        console2.log("Seller C :: Cash Secured Margin Deposited: ", marginDeposited);
        console2.log("Seller C :: NUMBER OF OPTION LEGS", pp.numberOfLegs(Seller));
        (uint128 balance, uint64 poolUtilization0, uint64 poolUtilization1) =
            ph.optionPositionInfo(pp, Seller, tokenId);

        console2.log("Seller C :: Option Nominal Balance :", balance);
        console2.log(
            "Collateral tracking of B is now utilized by Seller C. Utilization = Seller C's marginDeposited / totalSupply of the collateral tracker (the deflator/normalizer)",
            Math.mulDivRoundingUp(amount1, 10000, ct1.totalSupply())
        );

        console2.log("Collateral Tracker Utilization: ", poolUtilization1);

        vm.stopPrank();

        console2.log(
            "=================PRE-CONDITIONS (REALIZING OPTION PAYOFF) ==========================",
            ""
        );

        {
            TokenId[] memory posIds = new TokenId[](1);
            posIds[0] = tokenId;
            (LeftRightUnsigned shortPremiaAccrued,,) =
                pp.getAccumulatedFeesAndPositionsData(Seller, true, posIds);
            console2.log(
                "Seller C :: Accrued streaming premia token0: ", shortPremiaAccrued.rightSlot()
            );
            console2.log(
                "Seller C :: Accrued streaming premia token1: ", shortPremiaAccrued.leftSlot()
            );
        }

        console2.log(
            "The only way to realize the payoff is by having the price move. This is achieved only through trading volume that drives prices. Given the volatility and expiration proxies the option writer used, we apply the same argument to derive the trading volume needed to drive the price to the option writer's desired ITM level and realize the intended payoff",
            ""
        );

        console2.log(
            "===================TEST (REALIZING OPTION PAYOFF)==================================",
            ""
        );
        console2.log(
            "Alice, who acts as a trader, will realize the payoff through her swap order, which effectively puts Seller in the money:",
            ""
        );
        vm.prank(Alice);
        angstrom.execute("");
        BalanceDelta swapDelta = swapToStrike(strike, width, int24(uint24(DEFAULT_TICK_SPACING)));
        console2.log("AmountIn Swap : ", uint256(int256(swapDelta.amount1())));
        console2.log("AmountOut Swap : ", uint256(int256(swapDelta.amount0())));

        console2.log(
            "==================POST - CONDITIONS (REALIZING OPTION PAYOFF)=======================",
            ""
        );

        currentSqrtPriceX96 = PoolManager_(address(uni)).getSlot0(testPoolId).sqrtPriceX96();
        console2.log("Current Price (P_(A/B)): ", currentSqrtPriceX96);
        currentTick = PoolManager_(address(uni)).getSlot0(testPoolId).tick();
        console2.log("Current tick i [P_(A/B)]: ", currentTick);

        console2.log(
            "==========================PREVIEW (PREMIA & PAYOFF)==========================================",
            ""
        );

        {
            TokenId[] memory posIds = new TokenId[](1);
            posIds[0] = tokenId;
            (LeftRightUnsigned shortPremiaAccrued,,) =
                pp.getAccumulatedFeesAndPositionsData(Seller, true, posIds);
            console2.log(
                "Seller C :: Accrued streaming premia token0: ", shortPremiaAccrued.rightSlot()
            );
            console2.log(
                "Seller C :: Accrued streaming premia token1: ", shortPremiaAccrued.leftSlot()
            );
        }

        {
            (uint128 balanceITM, uint64 poolUtil0ITM, uint64 poolUtil1ITM) =
                ph.optionPositionInfo(pp, Seller, tokenId);
            console2.log("Seller C :: Position balance (ITM): ", balanceITM);
            console2.log("Seller C :: Pool utilization token0: ", poolUtil0ITM);
            console2.log("Seller C :: Pool utilization token1: ", poolUtil1ITM);
        }

        {
            (, uint256 inAMM0,,) = ct0.getPoolData();
            (, uint256 inAMM1,,) = ct1.getPoolData();
            console2.log("Collateral locked in AMM (token0): ", inAMM0);
            console2.log("Collateral locked in AMM (token1): ", inAMM1);
        }

        uint256 sellerBalanceBefore = ct1.balanceOf(Seller);
        console2.log("Seller C :: Collateral balance (before burn): ", sellerBalanceBefore);

        console2.log(
            "==========================BURN (REMOVING POSITION)==========================================",
            ""
        );

        vm.startPrank(Seller);

        TokenId[] memory emptyList = new TokenId[](0);
        burnOptions(pp, tokenId, emptyList, Constants.MAX_POOL_TICK, Constants.MIN_POOL_TICK, true);

        vm.stopPrank();

        console2.log(
            "==========================POST-BURN ASSERTIONS==========================================",
            ""
        );

        assertEq(
            sfpm.balanceOf(address(pp), TokenId.unwrap(tokenId)), 0, "Position not fully burned"
        );
        console2.log("Seller C :: SFPM balance (post-burn): 0");

        assertEq(pp.numberOfLegs(Seller), 0, "Legs not cleared");
        console2.log("Seller C :: Number of legs (post-burn): 0");

        {
            (, uint256 inAMM0Post,,) = ct0.getPoolData();
            (, uint256 inAMM1Post,,) = ct1.getPoolData();
            console2.log("Collateral locked in AMM post-burn (token0): ", inAMM0Post);
            console2.log("Collateral locked in AMM post-burn (token1): ", inAMM1Post);
        }

        {
            uint256 _balAfter = ct1.balanceOf(Seller);
            uint256 _balBefore = sellerBalanceBefore;
            uint256 _balStart = sellerBalanceStart;
            console2.log("Seller C :: Collateral balance (after burn): ", _balAfter);
            console2.log(
                "Seller C :: P&L from burn only (token1): ", int256(_balAfter) - int256(_balBefore)
            );
            console2.log(
                "Seller C :: Total lifecycle P&L (token1): ", int256(_balAfter) - int256(_balStart)
            );
        }
    }
}
