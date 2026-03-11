// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// Multi-chain, multi-protocol deterministic scenario dispatch for FCI scripts.
// Free functions operate on Context + Scenario storage — routing mint/burn/swap
// to V3 (IUniswapV3Pool) or V4 (PositionManager) based on Protocol.
//
// Context holds environment state (pools, accounts, routers).
// Scenario tracks recipe execution (tokenIds, deltaPlus).
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
import {INDEX_ONE} from "typed-uniswap-v4/fee-concentration-index/types/FeeConcentrationStateMod.sol";
import {V3CallbackRouter} from
    "@reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol";
import {Protocol, isUniswapV3, isUniswapV4} from "@foundry-script/types/Protocol.sol";
import {Context} from "@foundry-script/types/Context.sol";
import "@foundry-script/utils/Constants.sol";

struct Scenario {
    uint256[] tokenIds;
    uint128 deltaPlus;
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
    Context storage ctx,
    Scenario storage s,
    Protocol protocol,
    uint256 pk,
    uint256 liquidity
) returns (uint256 tokenId) {
    address caller = ctx.vm.addr(pk);
    if (isUniswapV3(protocol)) {
        V3CallbackRouter router = V3CallbackRouter(ctx.v3Router);
        ctx.vm.broadcast(pk);
        router.mint(ctx.v3Pool, caller, TICK_LOWER, TICK_UPPER, uint128(liquidity));
    } else {
        IPositionManager lpm = IPositionManager(ctx.v4PositionManager);
        tokenId = lpm.nextTokenId();
        bytes memory calls = encodeMint(ctx.v4Pool, liquidity, caller);
        ctx.vm.broadcast(pk);
        lpm.modifyLiquidities(calls, DEADLINE);
        s.tokenIds.push(tokenId);
    }
}

// ── Burn (broadcast) ──

function burnPosition(
    Context storage ctx,
    Protocol protocol,
    uint256 pk,
    uint256 tokenId,
    uint256 liquidity
) {
    address caller = ctx.vm.addr(pk);
    if (isUniswapV3(protocol)) {
        // Zero-burn to trigger fee accounting
        ctx.vm.broadcast(pk);
        ctx.v3Pool.burn(TICK_LOWER, TICK_UPPER, 0);
        ctx.vm.broadcast(pk);
        ctx.v3Pool.collect(caller, TICK_LOWER, TICK_UPPER, type(uint128).max, type(uint128).max);

        // Full burn
        ctx.vm.broadcast(pk);
        ctx.v3Pool.burn(TICK_LOWER, TICK_UPPER, uint128(liquidity));
        ctx.vm.broadcast(pk);
        ctx.v3Pool.collect(caller, TICK_LOWER, TICK_UPPER, type(uint128).max, type(uint128).max);
    } else {
        IPositionManager lpm = IPositionManager(ctx.v4PositionManager);

        ctx.vm.broadcast(pk);
        lpm.modifyLiquidities(encodeDecrease(ctx.v4Pool, tokenId, liquidity), DEADLINE);

        ctx.vm.broadcast(pk);
        lpm.modifyLiquidities(encodeBurn(ctx.v4Pool, tokenId), DEADLINE);
    }
}

// ── Swap (broadcast) ──

function executeSwap(
    Context storage ctx,
    Protocol protocol,
    uint256 pk,
    bool zeroForOne
) {
    address caller = ctx.vm.addr(pk);
    if (isUniswapV3(protocol)) {
        V3CallbackRouter router = V3CallbackRouter(ctx.v3Router);
        uint160 sqrtPriceLimit = zeroForOne
            ? TickMath.MIN_SQRT_PRICE + 1
            : TickMath.MAX_SQRT_PRICE - 1;
        ctx.vm.broadcast(pk);
        router.swap(ctx.v3Pool, caller, zeroForOne, AMOUNT_SPECIFIED, sqrtPriceLimit);
    } else {
        PoolSwapTest router = PoolSwapTest(ctx.v4SwapRouter);
        ctx.vm.broadcast(pk);
        router.swap(
            ctx.v4Pool,
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
    Context storage ctx,
    Scenario storage s,
    Protocol protocol,
    uint128 targetDeltaPlus
) returns (Recipe memory recipe) {
    recipe = selectRecipe(targetDeltaPlus);
    require(!recipe.multiBlock, "Scenario: use phased functions for multi-block recipes");

    uint256 tokenA = mintPosition(ctx, s, protocol, ctx.accounts.lpPassive.privateKey, recipe.capitalA);
    uint256 tokenB = mintPosition(ctx, s, protocol, ctx.accounts.lpSophisticated.privateKey, recipe.capitalB);

    for (uint256 i; i < recipe.numSwapsBeforeBurn; ++i) {
        executeSwap(ctx, protocol, ctx.accounts.swapper.privateKey, ZERO_FOR_ONE);
    }

    burnPosition(ctx, protocol, ctx.accounts.lpSophisticated.privateKey, tokenB, recipe.capitalB);
    burnPosition(ctx, protocol, ctx.accounts.lpPassive.privateKey, tokenA, recipe.capitalA);

    s.deltaPlus = targetDeltaPlus;
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
    Context storage ctx,
    Scenario storage s,
    Protocol protocol,
    uint256 capitalA
) returns (uint256 tokenA) {
    tokenA = mintPosition(ctx, s, protocol, ctx.accounts.lpPassive.privateKey, capitalA);
}

function crowdoutPhase2(
    Context storage ctx,
    Scenario storage s,
    Protocol protocol,
    uint256 capitalB
) returns (uint256 tokenB) {
    tokenB = mintPosition(ctx, s, protocol, ctx.accounts.lpSophisticated.privateKey, capitalB);

    // Forward swap
    executeSwap(ctx, protocol, ctx.accounts.swapper.privateKey, ZERO_FOR_ONE);

    // Reverse swap (round-trip)
    executeSwap(ctx, protocol, ctx.accounts.swapper.privateKey, !ZERO_FOR_ONE);

    // LP_sophisticated exits
    burnPosition(ctx, protocol, ctx.accounts.lpSophisticated.privateKey, tokenB, capitalB);
}

function crowdoutPhase3(
    Context storage ctx,
    Scenario storage s,
    Protocol protocol,
    uint256 tokenA,
    uint256 capitalA
) {
    // Final swap (only passive active)
    executeSwap(ctx, protocol, ctx.accounts.swapper.privateKey, ZERO_FOR_ONE);

    // LP_passive exits
    burnPosition(ctx, protocol, ctx.accounts.lpPassive.privateKey, tokenA, capitalA);

    s.deltaPlus = DELTA_CROWDOUT;
}
