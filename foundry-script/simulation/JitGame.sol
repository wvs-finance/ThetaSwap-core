// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Vm} from "forge-std/Vm.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {Protocol, isUniswapV3, isUniswapV4} from "@foundry-script/types/Protocol.sol";
import {DEFAULT_DERIVATION_PATH} from "@foundry-script/types/Accounts.sol";
import {Context} from "@foundry-script/types/Context.sol";
import {Scenario, mintPosition, burnPosition} from "@foundry-script/types/Scenario.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {SwapParams} from "v4-core/src/types/PoolOperation.sol";
import {PoolSwapTest} from "v4-core/src/test/PoolSwapTest.sol";
import {V3CallbackRouter} from "@reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import "@foundry-script/utils/Constants.sol";

struct JitGameConfig {
    uint256 n;
    uint256 jitCapital;
    uint256 jitEntryProbability;
    uint256 tradeSize;
    bool zeroForOne;
    Protocol protocol;
}

struct JitGameResult {
    uint128 deltaPlus;
    uint256 hedgedLpPayout;
    uint256 unhedgedLpPayout;
    uint256 jitLpPayout;
    bool jitEntered;
}

struct JitAccounts {
    Vm.Wallet[] passiveLps;
    Vm.Wallet jitLp;
    Vm.Wallet swapper;
    uint256 hedgedIndex;
}

function initJitAccounts(Vm vm, uint256 n) returns (JitAccounts memory acc) {
    require(n >= 2, "JitGame: N must be >= 2");
    string memory mnemonic = vm.envString("MNEMONIC");

    acc.passiveLps = new Vm.Wallet[](n);
    for (uint256 i; i < n; ++i) {
        acc.passiveLps[i] = vm.createWallet(
            vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, uint32(i)),
            string.concat("passiveLp", vm.toString(i))
        );
    }
    acc.jitLp = vm.createWallet(
        vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, uint32(n)),
        "jitLp"
    );
    acc.swapper = vm.createWallet(
        vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, uint32(n + 1)),
        "swapper"
    );
    acc.hedgedIndex = 0;
}

function validateJitConfig(JitGameConfig memory cfg) pure {
    require(cfg.n >= 2, "JitGame: N must be >= 2");
    require(cfg.jitEntryProbability <= 10000, "JitGame: probability must be <= 10000 bps");
    require(cfg.tradeSize > 0, "JitGame: tradeSize must be > 0");
}

function executeSwapWithAmount(
    Context storage ctx,
    Protocol protocol,
    uint256 pk,
    bool zeroForOne,
    int256 amountSpecified
) {
    address caller = ctx.vm.addr(pk);
    if (isUniswapV3(protocol)) {
        V3CallbackRouter router = V3CallbackRouter(ctx.v3Router);
        uint160 sqrtPriceLimit = zeroForOne
            ? TickMath.MIN_SQRT_PRICE + 1
            : TickMath.MAX_SQRT_PRICE - 1;
        ctx.vm.broadcast(pk);
        router.swap(ctx.v3Pool, caller, zeroForOne, amountSpecified, sqrtPriceLimit);
    } else {
        PoolSwapTest router = PoolSwapTest(ctx.v4SwapRouter);
        ctx.vm.broadcast(pk);
        router.swap(
            ctx.v4Pool,
            SwapParams({
                zeroForOne: zeroForOne,
                amountSpecified: amountSpecified,
                sqrtPriceLimitX96: zeroForOne
                    ? TickMath.MIN_SQRT_PRICE + 1
                    : TickMath.MAX_SQRT_PRICE - 1
            }),
            PoolSwapTest.TestSettings({takeClaims: false, settleUsingBurn: false}),
            ""
        );
    }
}

uint256 constant UNIT_LIQUIDITY = 1e18;

function runJitGame(
    Context storage ctx,
    Scenario storage s,
    JitGameConfig memory cfg,
    JitAccounts memory acc
) returns (JitGameResult memory result) {
    validateJitConfig(cfg);

    // ── Step 2: Passive LP entry ──
    uint256[] memory passiveTokenIds = new uint256[](cfg.n);
    for (uint256 i; i < cfg.n; ++i) {
        passiveTokenIds[i] = mintPosition(
            ctx, s, cfg.protocol, acc.passiveLps[i].privateKey, UNIT_LIQUIDITY
        );
    }

    // ── Step 3: JIT decision ──
    uint256 jitTokenId;
    uint256 roll = ctx.vm.randomUint(0, 9999);
    if (roll < cfg.jitEntryProbability) {
        result.jitEntered = true;
        jitTokenId = mintPosition(
            ctx, s, cfg.protocol, acc.jitLp.privateKey, cfg.jitCapital
        );
    }

    // ── Step 4: Trade arrives ──
    executeSwapWithAmount(
        ctx, cfg.protocol, acc.swapper.privateKey, cfg.zeroForOne, int256(cfg.tradeSize)
    );

    // ── Step 5: JIT exit ──
    if (result.jitEntered) {
        address jitAddr = acc.jitLp.addr;
        (address tokenA, address tokenB) = resolveTokensFromCtx(ctx);
        uint256 jitBalABefore = IERC20(tokenA).balanceOf(jitAddr);
        uint256 jitBalBBefore = IERC20(tokenB).balanceOf(jitAddr);

        burnPosition(ctx, cfg.protocol, acc.jitLp.privateKey, jitTokenId, cfg.jitCapital);

        result.jitLpPayout = (IERC20(tokenA).balanceOf(jitAddr) - jitBalABefore)
            + (IERC20(tokenB).balanceOf(jitAddr) - jitBalBBefore);
    }

    // ── Step 6: Passive LP exit + fee tracking ──
    // Note: Payouts sum both token0 and token1 balance deltas as raw uint256.
    // This is valid for HHI/delta-plus since all LPs share the same tick range
    // and fee tier — relative shares are preserved regardless of token weighting.
    uint256[] memory payouts = new uint256[](cfg.n);
    for (uint256 i; i < cfg.n; ++i) {
        address lpAddr = acc.passiveLps[i].addr;
        (address tokenA, address tokenB) = resolveTokensFromCtx(ctx);
        uint256 balABefore = IERC20(tokenA).balanceOf(lpAddr);
        uint256 balBBefore = IERC20(tokenB).balanceOf(lpAddr);

        burnPosition(ctx, cfg.protocol, acc.passiveLps[i].privateKey, passiveTokenIds[i], UNIT_LIQUIDITY);

        payouts[i] = (IERC20(tokenA).balanceOf(lpAddr) - balABefore)
            + (IERC20(tokenB).balanceOf(lpAddr) - balBBefore);
    }

    result.hedgedLpPayout = payouts[acc.hedgedIndex];

    // Worst non-hedged LP
    uint256 minPayout = type(uint256).max;
    for (uint256 i; i < cfg.n; ++i) {
        if (i != acc.hedgedIndex && payouts[i] < minPayout) {
            minPayout = payouts[i];
        }
    }
    result.unhedgedLpPayout = minPayout;

    // ── Step 7: Measure delta-plus (inline HHI) ──
    result.deltaPlus = computeDeltaPlus(payouts, cfg.n);
}

/// @dev HHI-based delta-plus: sum((s_i)^2) - 1/N, where s_i = payout_i / totalPayout
/// Returns Q128 fixed-point to match existing FCI convention.
function computeDeltaPlus(uint256[] memory payouts, uint256 n) pure returns (uint128) {
    uint256 total;
    for (uint256 i; i < n; ++i) {
        total += payouts[i];
    }
    if (total == 0) return 0; // No fees accrued — equilibrium by default

    // HHI = sum(share_i^2), share_i = payout_i / total
    // We compute in 1e18 precision then convert to Q128
    uint256 hhi;
    for (uint256 i; i < n; ++i) {
        uint256 share = (payouts[i] * 1e18) / total;
        hhi += (share * share) / 1e18;
    }
    // delta-plus = HHI - 1/N (in 1e18)
    uint256 baseline = 1e18 / n;
    if (hhi <= baseline) return 0;
    uint256 deltaPlusE18 = hhi - baseline;

    // Convert to Q128: deltaPlusE18 * 2^128 / 1e18
    return uint128((deltaPlusE18 << 128) / 1e18);
}

/// @dev Extract token addresses from Context. For V4, read from PoolKey.
/// Currency wraps address as bytes32 via Currency.wrap(). Unwrap reverses.
function resolveTokensFromCtx(Context storage ctx) view returns (address, address) {
    return (
        Currency.unwrap(ctx.v4Pool.currency0),
        Currency.unwrap(ctx.v4Pool.currency1)
    );
}
