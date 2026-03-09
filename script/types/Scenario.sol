// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Multi-chain, multi-protocol deterministic scenario dispatch for FCI scripts.
// Free functions operate on Scenario storage — routing mint/burn/swap
// to V3 (IUniswapV3Pool) or V4 (PositionManager) based on Protocol.
//
// BROADCAST MODE: all pool calls use vm.broadcast(pk) to sign real
// transactions on the live chain. The reactive adapter hears these events.
// Block advancement is external — multi-block recipes are split into phases.

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
import {V3CallbackRouter} from
    "../../src/reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol";
import {Protocol, isUniswapV3, isUniswapV4} from "./Protocol.sol";
import "../utils/Constants.sol";
import {Vm} from "forge-std/Vm.sol";

struct Scenario {
    Vm vm;
    mapping(uint256 chainId => PoolKey pool) pools;
    mapping(uint256 chainId => mapping(Protocol => address)) positionManager;
    mapping(uint256 chainId => address) swapRouter;
    mapping(uint256 chainId => uint256[]) tokenIds;
    mapping(uint256 chainId => address) v3Router;
}

// ── Known delta-plus thresholds (Q128, derived from unit tests) ──

uint128 constant DELTA_EQUILIBRIUM = 0;
uint128 constant DELTA_MILD        = uint128(uint256(INDEX_ONE) * 383 / 10000);   // 0.0383
uint128 constant DELTA_CAPPONI     = uint128(uint256(INDEX_ONE) * 900 / 10000);   // 0.09
uint128 constant DELTA_CROWDOUT    = uint128(uint256(INDEX_ONE) * 3981 / 10000);  // 0.3981

// ── Recipe ──

struct Recipe {
    uint256 capitalA;
    uint256 capitalB;
    uint256 numSwapsBeforeBurn;
    uint256 numSwapsAfterBurnB;
    bool    reverseSwap;
    bool    multiBlock;           // true = needs block gap (phased execution)
}

// US3-C: equal capital, 1 swap, both exit same block -> delta-plus = 0
function recipeEquilibrium() pure returns (Recipe memory) {
    return Recipe({
        capitalA: 1e18,
        capitalB: 1e18,
        numSwapsBeforeBurn: 1,
        numSwapsAfterBurnB: 0,
        reverseSwap: false,
        multiBlock: false
    });
}

// US3-D: 1:2 capital, 1 swap, same block -> delta-plus ~ 0.038
function recipeMild() pure returns (Recipe memory) {
    return Recipe({
        capitalA: 1e18,
        capitalB: 2e18,
        numSwapsBeforeBurn: 1,
        numSwapsAfterBurnB: 0,
        reverseSwap: false,
        multiBlock: false
    });
}

// US3-F: 1:9 capital, round-trip swap, B exits early, A exits late
// -> delta-plus ~ 0.398
// Requires 3 phases across multiple blocks.
function recipeCrowdout() pure returns (Recipe memory) {
    return Recipe({
        capitalA: 1e18,
        capitalB: 9e18,
        numSwapsBeforeBurn: 1,
        numSwapsAfterBurnB: 1,
        reverseSwap: true,
        multiBlock: true
    });
}

function selectRecipe(uint128 targetDeltaPlus) pure returns (Recipe memory) {
    if (targetDeltaPlus == 0) return recipeEquilibrium();
    uint128 midMildCrowdout = uint128((uint256(DELTA_MILD) + uint256(DELTA_CROWDOUT)) / 2);
    if (targetDeltaPlus <= midMildCrowdout) return recipeMild();
    return recipeCrowdout();
}

// ── Registration ──

function registerV3Pool(
    Scenario storage s,
    uint256 chainId,
    IUniswapV3Pool pool,
    address adapter,
    address router
) {
    s.pools[chainId] = fromV3Pool(pool, adapter);
    s.positionManager[chainId][Protocol.UniswapV3] = address(pool);
    s.v3Router[chainId] = router;
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

// ── V4 encoding (pure) ──

uint128 constant MAX_SLIPPAGE = type(uint128).max;
uint128 constant MIN_SLIPPAGE = 0;

function encodeMint(PoolKey memory k, uint256 liquidity, address recipient)
    pure returns (bytes memory)
{
    Plan memory planner = Planner.init();
    planner.add(
        Actions.MINT_POSITION,
        abi.encode(k, TICK_LOWER, TICK_UPPER, liquidity, MAX_SLIPPAGE, MAX_SLIPPAGE, recipient, "")
    );
    return planner.finalizeModifyLiquidityWithClose(k);
}

function encodeDecrease(PoolKey memory k, uint256 tokenId, uint256 liquidity)
    pure returns (bytes memory)
{
    Plan memory planner = Planner.init();
    planner.add(
        Actions.DECREASE_LIQUIDITY,
        abi.encode(tokenId, liquidity, MIN_SLIPPAGE, MIN_SLIPPAGE, "")
    );
    return planner.finalizeModifyLiquidityWithClose(k);
}

function encodeBurn(PoolKey memory k, uint256 tokenId)
    pure returns (bytes memory)
{
    Plan memory planner = Planner.init();
    planner.add(Actions.BURN_POSITION, abi.encode(tokenId, MIN_SLIPPAGE, MIN_SLIPPAGE, ""));
    return planner.finalizeModifyLiquidityWithClose(k);
}

// ── Mint (broadcast: signs real tx from pk) ──

function mintPosition(
    Scenario storage s,
    uint256 chainId,
    Protocol protocol,
    uint256 pk,
    uint256 liquidity
) returns (uint256 tokenId) {
    address caller = s.vm.addr(pk);
    if (isUniswapV3(protocol)) {
        IUniswapV3Pool pool = v3Pool(s, chainId);
        V3CallbackRouter router = V3CallbackRouter(s.v3Router[chainId]);
        s.vm.broadcast(pk);
        router.mint(pool, caller, TICK_LOWER, TICK_UPPER, uint128(liquidity));
    } else {
        IPositionManager lpm = v4Lpm(s, chainId);
        PoolKey memory k = s.pools[chainId];
        tokenId = lpm.nextTokenId();
        bytes memory calls = encodeMint(k, liquidity, caller);
        s.vm.broadcast(pk);
        lpm.modifyLiquidities(calls, DEADLINE);
        s.tokenIds[chainId].push(tokenId);
    }
}

// ── Burn (broadcast) ──

function burnPosition(
    Scenario storage s,
    uint256 chainId,
    Protocol protocol,
    uint256 pk,
    uint256 tokenId,
    uint256 liquidity
) {
    address caller = s.vm.addr(pk);
    if (isUniswapV3(protocol)) {
        IUniswapV3Pool pool = v3Pool(s, chainId);

        // Zero-burn to trigger fee accounting
        s.vm.broadcast(pk);
        pool.burn(TICK_LOWER, TICK_UPPER, 0);
        s.vm.broadcast(pk);
        pool.collect(caller, TICK_LOWER, TICK_UPPER, type(uint128).max, type(uint128).max);

        // Full burn
        s.vm.broadcast(pk);
        pool.burn(TICK_LOWER, TICK_UPPER, uint128(liquidity));
        s.vm.broadcast(pk);
        pool.collect(caller, TICK_LOWER, TICK_UPPER, type(uint128).max, type(uint128).max);
    } else {
        IPositionManager lpm = v4Lpm(s, chainId);
        PoolKey memory k = s.pools[chainId];

        s.vm.broadcast(pk);
        lpm.modifyLiquidities(encodeDecrease(k, tokenId, liquidity), DEADLINE);

        s.vm.broadcast(pk);
        lpm.modifyLiquidities(encodeBurn(k, tokenId), DEADLINE);
    }
}

// ── Swap (broadcast) ──

function executeSwap(
    Scenario storage s,
    uint256 chainId,
    Protocol protocol,
    uint256 pk,
    bool zeroForOne
) {
    address caller = s.vm.addr(pk);
    if (isUniswapV3(protocol)) {
        IUniswapV3Pool pool = v3Pool(s, chainId);
        V3CallbackRouter router = V3CallbackRouter(s.v3Router[chainId]);
        uint160 sqrtPriceLimit = zeroForOne
            ? TickMath.MIN_SQRT_PRICE + 1
            : TickMath.MAX_SQRT_PRICE - 1;
        s.vm.broadcast(pk);
        router.swap(pool, caller, zeroForOne, AMOUNT_SPECIFIED, sqrtPriceLimit);
    } else {
        PoolSwapTest router = v4SwapRouter(s, chainId);
        PoolKey memory k = s.pools[chainId];
        s.vm.broadcast(pk);
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

// ═══════════════════════════════════════════════════════════════════
// deltaPlusFactory — single-block recipes
//
// Broadcasts real transactions: mint A, mint B, swap(s), burn B, burn A.
// All land in a single block → lifetime = 1 for both positions.
// Works for equilibrium (delta-plus=0) and mild (delta-plus~0.038).
//
// For multi-block recipes (crowdout), use the phased functions below.
// ═══════════════════════════════════════════════════════════════════

function deltaPlusFactory(
    Scenario storage s,
    uint256 chainId,
    Protocol protocol,
    uint256 lpPassivePK,
    uint256 lpSophisticatedPK,
    uint256 swapperPK,
    uint128 targetDeltaPlus
) returns (Recipe memory recipe) {
    recipe = selectRecipe(targetDeltaPlus);
    require(!recipe.multiBlock, "Scenario: use phased functions for multi-block recipes");

    uint256 tokenA = mintPosition(s, chainId, protocol, lpPassivePK, recipe.capitalA);
    uint256 tokenB = mintPosition(s, chainId, protocol, lpSophisticatedPK, recipe.capitalB);

    for (uint256 i; i < recipe.numSwapsBeforeBurn; ++i) {
        executeSwap(s, chainId, protocol, swapperPK, ZERO_FOR_ONE);
    }

    burnPosition(s, chainId, protocol, lpSophisticatedPK, tokenB, recipe.capitalB);
    burnPosition(s, chainId, protocol, lpPassivePK, tokenA, recipe.capitalA);
}

// ═══════════════════════════════════════════════════════════════════
// Phased execution for multi-block recipes (crowdout / US3-F)
//
// Phase 1: LP_passive mints. Wait N blocks.
// Phase 2: LP_sophisticated mints, swaps, reverse swap, LP_sophisticated burns.
//          Wait N blocks.
// Phase 3: Swap (only passive active), LP_passive burns.
//
// Each phase is a separate script invocation. The script stores
// tokenIds between phases via .env or on-chain state.
// ═══════════════════════════════════════════════════════════════════

function crowdoutPhase1(
    Scenario storage s,
    uint256 chainId,
    Protocol protocol,
    uint256 lpPassivePK,
    uint256 capitalA
) returns (uint256 tokenA) {
    tokenA = mintPosition(s, chainId, protocol, lpPassivePK, capitalA);
}

function crowdoutPhase2(
    Scenario storage s,
    uint256 chainId,
    Protocol protocol,
    uint256 lpSophisticatedPK,
    uint256 swapperPK,
    uint256 capitalB
) returns (uint256 tokenB) {
    tokenB = mintPosition(s, chainId, protocol, lpSophisticatedPK, capitalB);

    // Forward swap
    executeSwap(s, chainId, protocol, swapperPK, ZERO_FOR_ONE);

    // Reverse swap (round-trip)
    executeSwap(s, chainId, protocol, swapperPK, !ZERO_FOR_ONE);

    // LP_sophisticated exits
    burnPosition(s, chainId, protocol, lpSophisticatedPK, tokenB, capitalB);
}

function crowdoutPhase3(
    Scenario storage s,
    uint256 chainId,
    Protocol protocol,
    uint256 lpPassivePK,
    uint256 swapperPK,
    uint256 tokenA,
    uint256 capitalA
) {
    // Final swap (only passive active)
    executeSwap(s, chainId, protocol, swapperPK, ZERO_FOR_ONE);

    // LP_passive exits
    burnPosition(s, chainId, protocol, lpPassivePK, tokenA, capitalA);
}
