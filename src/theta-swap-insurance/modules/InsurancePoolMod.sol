// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {LiquidityMath} from "@uniswap/v4-core/src/libraries/LiquidityMath.sol";
import {FixedPoint128} from "@uniswap/v4-core/src/libraries/FixedPoint128.sol";
import {LogPrice, ZERO_LOG_PRICE, LN_1_0001_Q128, Q128, fromTick, toTick, gt, lt, isZero} from "../types/LogPriceMod.sol";
import {getLogPriceTarget, computeSettleStep} from "../libraries/SettleMath.sol";
import {tradingFunction, marginalRate, getPayoffDelta, getCollateralDelta} from "../libraries/LogPriceMath.sol";

// ── Errors ──────────────────────────────────────────────────────────────

error InsurancePool__TicksMisordered(int24 tickLower, int24 tickUpper);
error InsurancePool__TickLowerOutOfBounds(int24 tickLower);
error InsurancePool__TickUpperOutOfBounds(int24 tickUpper);
error InsurancePool__TickLiquidityOverflow(int24 tick);
error InsurancePool__AlreadyInitialized();
error InsurancePool__NotInitialized();
error InsurancePool__PriceLimitExceeded(int256 logPriceCurrent, int256 logPriceLimit);
error InsurancePool__PriceLimitOutOfBounds(int256 logPriceLimit);
error InsurancePool__NoLiquidity();

// ── Constants ───────────────────────────────────────────────────────────

int24 constant MIN_TICK = -887272;
int24 constant MAX_TICK = 887272;

// ── Structs ─────────────────────────────────────────────────────────────

/// @dev Per-tick state for the insurance CFMM.
///      Single fee dimension: premiums flow one way (PLP → underwriter).
struct TickInfo {
    uint128 liquidityGross;
    int128 liquidityNet;
    /// @dev Premium growth per unit of liquidity on the _other_ side of this tick.
    ///      Analogous to V4's feeGrowthOutside, but for insurance premium accrual.
    uint256 premiumGrowthOutsideX128;
}

/// @dev Insurance pool state. Mirrors V4 Pool.State for the log-shaped CFMM.
///      Single price dimension (LogPrice s) and single fee dimension (premium growth).
struct InsurancePoolState {
    /// @dev Current log-price s = ln(1 + A_T/B_T) in Q128.
    LogPrice logPrice;
    /// @dev Current tick derived from logPrice.
    int24 tick;
    /// @dev Active underwriter liquidity in the current tick range.
    uint128 liquidity;
    /// @dev Global premium growth per unit of liquidity, in Q128.
    ///      Accumulated from PLP fee streams flowing to underwriters.
    uint256 premiumGrowthGlobalX128;
    /// @dev Per-tick state.
    mapping(int24 tick => TickInfo) ticks;
    /// @dev Tick bitmap for initialized tick lookup.
    mapping(int16 wordPos => uint256) tickBitmap;
}

/// @dev Parameters for settling the insurance CFMM against an oracle index movement.
///      Analogous to V4's SwapParams, but driven by oracle rather than user input.
struct SettleParams {
    /// @dev The new LogPrice from the oracle (post-swap index).
    LogPrice targetLogPrice;
    /// @dev Tick spacing for bitmap traversal.
    int24 tickSpacing;
    /// @dev LogPrice limit (circuit breaker). Settlement stops if reached.
    LogPrice logPriceLimit;
}

/// @dev Result of settling the insurance pool.
struct SettleResult {
    /// @dev The final log-price after settlement.
    LogPrice logPrice;
    /// @dev The final tick after settlement.
    int24 tick;
    /// @dev The active liquidity after settlement.
    uint128 liquidity;
    /// @dev Total premium accrued to underwriters during this settlement.
    uint256 premiumAccrued;
}

/// @dev Intermediate state for each tick-step during settlement.
struct SettleStep {
    /// @dev LogPrice at the beginning of this step.
    LogPrice logPriceStart;
    /// @dev Next initialized tick in the settlement direction.
    int24 tickNext;
    /// @dev Whether tickNext is initialized.
    bool initialized;
    /// @dev LogPrice at tickNext boundary.
    LogPrice logPriceNext;
    /// @dev Protection payoff delta for this step (per unit of liquidity).
    ///      Computed from the trading function y(s) = s - 1 + e^{-s}.
    uint256 payoffDelta;
    /// @dev Premium accrued in this step.
    uint256 premiumDelta;
    /// @dev Running premium growth accumulator.
    uint256 premiumGrowthGlobalX128;
}

/// @dev Parameters for adding/removing underwriter liquidity.
struct ModifyLiquidityParams {
    int24 tickLower;
    int24 tickUpper;
    int128 liquidityDelta;
    int24 tickSpacing;
}

// ── Tick validation ─────────────────────────────────────────────────────

function checkTicks(int24 tickLower, int24 tickUpper) pure {
    if (tickLower >= tickUpper) revert InsurancePool__TicksMisordered(tickLower, tickUpper);
    if (tickLower < MIN_TICK) revert InsurancePool__TickLowerOutOfBounds(tickLower);
    if (tickUpper > MAX_TICK) revert InsurancePool__TickUpperOutOfBounds(tickUpper);
}

function checkInitialized(InsurancePoolState storage self) view {
    if (self.logPrice.isZero() && self.tick == 0 && self.liquidity == 0) {
        revert InsurancePool__NotInitialized();
    }
}

// ── Initialize ──────────────────────────────────────────────────────────

/// @dev Initialize the insurance pool with a starting log-price from the oracle.
function initialize(InsurancePoolState storage self, LogPrice startLogPrice) {
    if (!self.logPrice.isZero() || self.tick != 0) revert InsurancePool__AlreadyInitialized();
    int24 tick = startLogPrice.toTick();
    self.logPrice = startLogPrice;
    self.tick = tick;
}

// ── Settlement (the "swap" of the insurance CFMM) ──────────────────────

/// @dev Settle the insurance CFMM: walk the trading curve from the current
///      log-price to the oracle's target log-price, accruing protection payoff
///      to PLPs and premium revenue to underwriters at each tick step.
///
///      Trading function: y(s) = s - 1 + e^{-s}
///      Marginal rate:    dy/ds = 1 - e^{-s}
///
///      This is the core engine that realizes the PLP payoff.
function settle(InsurancePoolState storage self, SettleParams memory params)
    returns (SettleResult memory result)
{
    // TODO: implement tick-stepping loop
    // Scaffold only — no business logic until invariants and proofs exist.
}

// ── Modify underwriter liquidity ────────────────────────────────────────

/// @dev Add or remove underwriter liquidity in a tick range.
///      Mirrors V4's Pool.modifyLiquidity for the insurance CFMM.
function modifyLiquidity(InsurancePoolState storage self, ModifyLiquidityParams memory params)
    returns (uint256 premiumOwed)
{
    // TODO: implement
}

// ── Premium growth accounting ───────────────────────────────────────────

/// @dev Get the premium growth inside a tick range.
///      Analogous to V4's getFeeGrowthInside but for a single premium dimension.
function getPremiumGrowthInside(
    InsurancePoolState storage self,
    int24 tickLower,
    int24 tickUpper
) view returns (uint256 premiumGrowthInsideX128) {
    // TODO: implement
}

// ── Tick management ─────────────────────────────────────────────────────

/// @dev Update a tick's liquidity. Returns whether the tick flipped initialization state.
function updateTick(
    InsurancePoolState storage self,
    int24 tick,
    int128 liquidityDelta,
    bool upper
) returns (bool flipped, uint128 liquidityGrossAfter) {
    // TODO: implement
}

/// @dev Cross a tick boundary during settlement. Flips premiumGrowthOutside
///      and returns the liquidityNet to apply.
function crossTick(
    InsurancePoolState storage self,
    int24 tick,
    uint256 premiumGrowthGlobalX128
) returns (int128 liquidityNet) {
    // TODO: implement
}

/// @dev Clear tick data when it becomes uninitialized.
function clearTick(InsurancePoolState storage self, int24 tick) {
    delete self.ticks[tick];
}

// ── Trading function math ───────────────────────────────────────────────
// tradingFunction(s) and marginalRate(s) live in LogPriceMath.sol
// getPayoffDelta, getCollateralDelta live in LogPriceMath.sol
// computeSettleStep, getLogPriceTarget live in SettleMath.sol
