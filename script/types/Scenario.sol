// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Multi-chain, multi-protocol deterministic scenario dispatch for FCI scripts.
// Free functions operate on Scenario storage — routing mint/burn/swap
// to V3 (IUniswapV3Pool) or V4 (PositionManager) based on Protocol.
// Tick ranges and swap params come from Constants.sol.
// Capital amounts and block lifetimes are recipe-driven (deltaPlusFactory).

import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {SwapParams} from "v4-core/src/types/PoolOperation.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";
import {PoolSwapTest} from "v4-core/src/test/PoolSwapTest.sol";
import {Actions} from "@uniswap/v4-periphery/src/libraries/Actions.sol";
import {Planner, Plan} from "@uniswap/v4-periphery/test/shared/Planner.sol";
import {INDEX_ONE} from "../../src/fee-concentration-index/types/FeeConcentrationStateMod.sol";
import {fromV3Pool} from "../../src/reactive-integration/libraries/PoolKeyExtMod.sol";
import {Protocol, isUniswapV3, isUniswapV4} from "./Protocol.sol";
import "../utils/Constants.sol";
import {Vm} from "forge-std/Vm.sol";

struct Scenario {
    Vm vm;
    mapping(uint256 chainId => PoolKey pool) pools;
    mapping(uint256 chainId => mapping(Protocol => address)) positionManager;
    mapping(uint256 chainId => address) swapRouter;
    mapping(uint256 chainId => uint256[]) tokenIds;
}

// ── Known Δ⁺ thresholds (Q128, derived from unit tests) ──
//
// US3-B: sole provider                     → Δ⁺ = 0
// US3-C: 2 LPs, 1:1 capital, same time    → Δ⁺ = 0
// US3-D: 2 LPs, 1:2 capital, same time    → Δ⁺ ≈ 0.038
// US3-F: 2 LPs, 1:9 capital, time 100:1   → Δ⁺ ≈ 0.398
// Capponi threshold Δ*                      ≈ 0.09

uint128 constant DELTA_EQUILIBRIUM = 0;
uint128 constant DELTA_MILD        = uint128(uint256(INDEX_ONE) * 383 / 10000);   // 0.0383
uint128 constant DELTA_CAPPONI     = uint128(uint256(INDEX_ONE) * 900 / 10000);   // 0.09
uint128 constant DELTA_CROWDOUT    = uint128(uint256(INDEX_ONE) * 3981 / 10000);  // 0.3981

// ── Recipe: the varying parameters for each known scenario ──

struct Recipe {
    uint256 capitalA;
    uint256 capitalB;
    uint256 blockAdvanceBeforeB;   // blocks between A mint and B mint
    uint256 numSwapsBeforeBurn;    // swaps while both active
    uint256 numSwapsAfterBurnB;    // swaps after B exits (only A active)
    uint256 blockLifetimeB;        // blocks B stays after its swaps
    uint256 blockLifetimeAAfterB;  // blocks A stays after B exits
    bool    reverseSwap;           // include a reverse swap (round-trip)
}

// US3-C: equal capital, same block, 1 swap, both exit → Δ⁺ = 0
function recipeEquilibrium() pure returns (Recipe memory) {
    return Recipe({
        capitalA: 1e18,
        capitalB: 1e18,
        blockAdvanceBeforeB: 0,
        numSwapsBeforeBurn: 1,
        numSwapsAfterBurnB: 0,
        blockLifetimeB: 0,
        blockLifetimeAAfterB: 0,
        reverseSwap: false
    });
}

// US3-D: 1:2 capital, same block, 1 swap → Δ⁺ ≈ 0.038
function recipeMild() pure returns (Recipe memory) {
    return Recipe({
        capitalA: 1e18,
        capitalB: 2e18,
        blockAdvanceBeforeB: 0,
        numSwapsBeforeBurn: 1,
        numSwapsAfterBurnB: 0,
        blockLifetimeB: 0,
        blockLifetimeAAfterB: 0,
        reverseSwap: false
    });
}

// US3-F: 1:9 capital, B enters at block 50, round-trip swap,
// B exits at block 51 (lifetime=1), A exits at block 101 (lifetime=100) → Δ⁺ ≈ 0.398
function recipeCrowdout() pure returns (Recipe memory) {
    return Recipe({
        capitalA: 1e18,
        capitalB: 9e18,
        blockAdvanceBeforeB: 49,
        numSwapsBeforeBurn: 1,
        numSwapsAfterBurnB: 1,
        blockLifetimeB: 1,
        blockLifetimeAAfterB: 49,
        reverseSwap: true
    });
}

// ── Registration ──

function registerV3Pool(
    Scenario storage s,
    uint256 chainId,
    IUniswapV3Pool pool,
    address adapter
) {
    s.pools[chainId] = fromV3Pool(pool, adapter);
    s.positionManager[chainId][Protocol.UniswapV3] = address(pool);
}

function registerV4Pool(
    Scenario storage s,
    uint256 chainId,
    PoolKey memory pool,
    address posMgr,
    address swapRtr
) {
    s.pools[chainId] = pool;
    s.positionManager[chainId][Protocol.UniswapV4] = posMgr;
    s.swapRouter[chainId] = swapRtr;
}

// ── Resolution ──

function poolKey(Scenario storage s, uint256 chainId) view returns (PoolKey memory) {
    return s.pools[chainId];
}

function v3Pool(Scenario storage s, uint256 chainId) view returns (IUniswapV3Pool) {
    return IUniswapV3Pool(s.positionManager[chainId][Protocol.UniswapV3]);
}

function v4Lpm(Scenario storage s, uint256 chainId) view returns (IPositionManager) {
    return IPositionManager(s.positionManager[chainId][Protocol.UniswapV4]);
}

function v4SwapRouter(Scenario storage s, uint256 chainId) view returns (PoolSwapTest) {
    return PoolSwapTest(s.swapRouter[chainId]);
}

// ── V4 encoding (pure, mirrors LiquidityOperations) ──

uint128 constant MAX_SLIPPAGE = type(uint128).max;
uint128 constant MIN_SLIPPAGE = 0;

function encodeMint(
    PoolKey memory k,
    uint256 liquidity,
    address recipient
) pure returns (bytes memory) {
    Plan memory planner = Planner.init();
    planner.add(
        Actions.MINT_POSITION,
        abi.encode(k, TICK_LOWER, TICK_UPPER, liquidity, MAX_SLIPPAGE, MAX_SLIPPAGE, recipient, "")
    );
    return planner.finalizeModifyLiquidityWithClose(k);
}

function encodeDecrease(
    PoolKey memory k,
    uint256 tokenId,
    uint256 liquidity
) pure returns (bytes memory) {
    Plan memory planner = Planner.init();
    planner.add(
        Actions.DECREASE_LIQUIDITY,
        abi.encode(tokenId, liquidity, MIN_SLIPPAGE, MIN_SLIPPAGE, "")
    );
    return planner.finalizeModifyLiquidityWithClose(k);
}

function encodeBurn(
    PoolKey memory k,
    uint256 tokenId
) pure returns (bytes memory) {
    Plan memory planner = Planner.init();
    planner.add(
        Actions.BURN_POSITION,
        abi.encode(tokenId, MIN_SLIPPAGE, MIN_SLIPPAGE, "")
    );
    return planner.finalizeModifyLiquidityWithClose(k);
}

// ── Mint (parameterized liquidity) ──

function mintPosition(
    Scenario storage s,
    uint256 chainId,
    Protocol protocol,
    address caller,
    uint256 liquidity
) returns (uint256 tokenId) {
    if (isUniswapV3(protocol)) {
        IUniswapV3Pool pool = v3Pool(s, chainId);
        s.vm.prank(caller);
        pool.mint(caller, TICK_LOWER, TICK_UPPER, uint128(liquidity), "");
    } else {
        IPositionManager lpm = v4Lpm(s, chainId);
        PoolKey memory k = s.pools[chainId];
        tokenId = lpm.nextTokenId();
        bytes memory calls = encodeMint(k, liquidity, caller);
        s.vm.prank(caller);
        lpm.modifyLiquidities(calls, DEADLINE);
        s.tokenIds[chainId].push(tokenId);
    }
}

// ── Burn (parameterized liquidity) ──

function burnPosition(
    Scenario storage s,
    uint256 chainId,
    Protocol protocol,
    address caller,
    uint256 tokenId,
    uint256 liquidity
) {
    if (isUniswapV3(protocol)) {
        IUniswapV3Pool pool = v3Pool(s, chainId);

        // Zero-burn to trigger fee accounting
        s.vm.prank(caller);
        pool.burn(TICK_LOWER, TICK_UPPER, 0);
        s.vm.prank(caller);
        pool.collect(caller, TICK_LOWER, TICK_UPPER, type(uint128).max, type(uint128).max);

        // Full burn
        s.vm.prank(caller);
        pool.burn(TICK_LOWER, TICK_UPPER, uint128(liquidity));
        s.vm.prank(caller);
        pool.collect(caller, TICK_LOWER, TICK_UPPER, type(uint128).max, type(uint128).max);
    } else {
        IPositionManager lpm = v4Lpm(s, chainId);
        PoolKey memory k = s.pools[chainId];

        // Decrease liquidity
        bytes memory decCalls = encodeDecrease(k, tokenId, liquidity);
        s.vm.prank(caller);
        lpm.modifyLiquidities(decCalls, DEADLINE);

        // Burn the NFT
        bytes memory burnCalls = encodeBurn(k, tokenId);
        s.vm.prank(caller);
        lpm.modifyLiquidities(burnCalls, DEADLINE);
    }
}

// ── Swap (deterministic direction + amount from Constants.sol) ──

function executeSwap(
    Scenario storage s,
    uint256 chainId,
    Protocol protocol,
    address caller,
    bool zeroForOne
) {
    if (isUniswapV3(protocol)) {
        IUniswapV3Pool pool = v3Pool(s, chainId);
        uint160 sqrtPriceLimit = zeroForOne
            ? TickMath.MIN_SQRT_PRICE + 1
            : TickMath.MAX_SQRT_PRICE - 1;
        s.vm.prank(caller);
        pool.swap(caller, zeroForOne, AMOUNT_SPECIFIED, sqrtPriceLimit, "");
    } else {
        PoolSwapTest router = v4SwapRouter(s, chainId);
        PoolKey memory k = s.pools[chainId];
        s.vm.prank(caller);
        router.swap(
            k,
            SwapParams({
                zeroForOne: zeroForOne,
                amountSpecified: AMOUNT_SPECIFIED,
                sqrtPriceLimitX96: zeroForOne
                    ? TickMath.MIN_SQRT_PRICE + 1
                    : TickMath.MAX_SQRT_PRICE - 1
            }),
            PoolSwapTest.TestSettings({takeClaims: false, settleUsingBurn: false}),
            ""
        );
    }
}

// ── Recipe selector: closest known Δ⁺ ──

function selectRecipe(uint128 targetDeltaPlus) pure returns (Recipe memory) {
    if (targetDeltaPlus == 0) return recipeEquilibrium();

    // Midpoints between known Δ⁺ values for nearest-match selection
    // MILD=0.038, CROWDOUT=0.398 → midpoint ≈ 0.218
    uint128 midMildCrowdout = uint128((uint256(DELTA_MILD) + uint256(DELTA_CROWDOUT)) / 2);

    if (targetDeltaPlus <= midMildCrowdout) return recipeMild();
    return recipeCrowdout();
}

// ── deltaPlusFactory ──
// Takes a target Δ⁺ and executes the on-chain behavior that yields it.
// Selects the closest known recipe (reverse-engineered from unit tests)
// and replays the exact mint/swap/burn sequence.
//
// Returns the recipe used so the caller knows the expected Δ⁺.

function deltaPlusFactory(
    Scenario storage s,
    uint256 chainId,
    Protocol protocol,
    address lpPassive,
    address lpSophisticated,
    address swapper,
    uint128 targetDeltaPlus
) returns (Recipe memory recipe) {
    recipe = selectRecipe(targetDeltaPlus);

    // Block 1: LP_passive mints capitalA
    uint256 tokenA = mintPosition(s, chainId, protocol, lpPassive, recipe.capitalA);

    // Advance blocks before LP_sophisticated enters
    if (recipe.blockAdvanceBeforeB > 0) {
        s.vm.roll(block.number + recipe.blockAdvanceBeforeB);
    }

    // LP_sophisticated mints capitalB
    uint256 tokenB = mintPosition(s, chainId, protocol, lpSophisticated, recipe.capitalB);

    // Swaps while both LPs active
    for (uint256 i; i < recipe.numSwapsBeforeBurn; ++i) {
        executeSwap(s, chainId, protocol, swapper, ZERO_FOR_ONE);
    }

    // Reverse swap if round-trip recipe (US3-F pattern)
    if (recipe.reverseSwap) {
        if (recipe.blockLifetimeB > 0) {
            s.vm.roll(block.number + recipe.blockLifetimeB);
        }
        executeSwap(s, chainId, protocol, swapper, !ZERO_FOR_ONE);
    }

    // LP_sophisticated exits
    burnPosition(s, chainId, protocol, lpSophisticated, tokenB, recipe.capitalB);

    // Swaps after B exits (only passive active)
    if (recipe.numSwapsAfterBurnB > 0) {
        if (recipe.blockLifetimeAAfterB > 0) {
            s.vm.roll(block.number + recipe.blockLifetimeAAfterB);
        }
        for (uint256 i; i < recipe.numSwapsAfterBurnB; ++i) {
            executeSwap(s, chainId, protocol, swapper, ZERO_FOR_ONE);
        }
    }

    // LP_passive exits
    if (recipe.blockLifetimeAAfterB > 0 && recipe.numSwapsAfterBurnB == 0) {
        s.vm.roll(block.number + recipe.blockLifetimeAAfterB);
    }
    s.vm.roll(block.number + 1);
    burnPosition(s, chainId, protocol, lpPassive, tokenA, recipe.capitalA);
}
