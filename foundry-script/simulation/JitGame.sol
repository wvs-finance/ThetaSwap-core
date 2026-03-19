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
import {V3CallbackRouter} from "@utils/V3CallbackRouter.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {console} from "forge-std/console.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import "@foundry-script/utils/Constants.sol";

/// @dev Minimal interface to read delta-plus from FCI hook (harness or production).
interface IFCIDeltaPlusReader {
    function getDeltaPlus(PoolId poolId) external view returns (uint128);
}

/// @dev Minimal interface for vault operations in the game loop.
/// Uses harness function names -- the game library is test infrastructure.
interface IVaultPokeSettle {
    function harness_pokeEpoch() external;
    function harness_settle() external;
    /// @return sqrtPriceStrike, sqrtPriceHWM, expiry, totalDeposits, settled, longPayoutPerToken
    function harness_getVaultStorage() external view returns (
        uint160, uint160, uint256, uint256, bool, uint256
    );
}

struct VaultConfig {
    address vault;          // zero address = no vault
    uint256 depositAmount;  // lump-sum hedge deposit
    bool reactive;          // reactive flag for getDeltaPlusEpoch reads
}

struct WelfareResult {
    uint256 longPayout;       // vault settlement payout to LONG
    uint256 shortPayout;      // vault settlement payout to SHORT
    int256  hedgeValue;       // int256(longPayout) - int256(depositAmount)
    uint256 lpFeeRevenue;     // sum of hedgedLpPayout across all rounds
    uint256 hedgedWelfare;    // lpFeeRevenue + longPayout
    uint256 unhedgedWelfare;  // lpFeeRevenue (no vault interaction)
}

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

// Block offsets for Capponi timing model:
// Passive LPs enter at block B, JIT enters at B+49, passive LPs exit at B+99.
// This creates lifetime_passive ≈ 100 blocks (θ=1/100) vs lifetime_JIT = 1 block (θ=1).
uint256 constant PASSIVE_ENTRY_OFFSET = 0;
uint256 constant JIT_ENTRY_OFFSET = 49;
uint256 constant PASSIVE_EXIT_OFFSET = 50;

function runJitGame(
    Context storage ctx,
    Scenario storage s,
    JitGameConfig memory cfg,
    JitAccounts memory acc,
    address fciHook
) returns (JitGameResult memory result) {
    validateJitConfig(cfg);

    // ── Step 2: Passive LP entry (block B) ──
    // Passive LPs enter early, establishing long-lived positions.
    uint256[] memory passiveTokenIds = new uint256[](cfg.n);
    for (uint256 i; i < cfg.n; ++i) {
        passiveTokenIds[i] = mintPosition(
            ctx, s, cfg.protocol, acc.passiveLps[i].privateKey, UNIT_LIQUIDITY
        );
    }

    // ── Step 3: Advance to JIT entry block (block B + JIT_ENTRY_OFFSET) ──
    // This creates the block-time gap between passive LP entry and JIT entry.
    // FCI computes θ_k = 1/blockLifetime_k, so the gap is critical:
    //   - passive LP: lifetime ≈ 100 blocks → θ ≈ 1/100 (low penalty)
    //   - JIT LP: lifetime = 1 block → θ = 1 (max penalty)
    ctx.vm.roll(block.number + JIT_ENTRY_OFFSET);

    // ── Step 4: JIT decision ──
    uint256 jitTokenId;
    uint256 roll = ctx.vm.randomUint(0, 9999);
    if (roll < cfg.jitEntryProbability) {
        result.jitEntered = true;
        jitTokenId = mintPosition(
            ctx, s, cfg.protocol, acc.jitLp.privateKey, cfg.jitCapital
        );
    }

    // ── Step 5: Trade arrives (same block as JIT entry) ──
    executeSwapWithAmount(
        ctx, cfg.protocol, acc.swapper.privateKey, cfg.zeroForOne, int256(cfg.tradeSize)
    );

    // ── Step 6: JIT exit (next block — minimum 1-block lifetime) ──
    ctx.vm.roll(block.number + 1);

    if (result.jitEntered) {
        address jitAddr = acc.jitLp.addr;
        (address tokenA, address tokenB) = resolveTokensFromCtx(ctx);
        uint256 jitBalABefore = IERC20(tokenA).balanceOf(jitAddr);
        uint256 jitBalBBefore = IERC20(tokenB).balanceOf(jitAddr);

        burnPosition(ctx, cfg.protocol, acc.jitLp.privateKey, jitTokenId, cfg.jitCapital);
	// note: Same observation on multiplying by price
        result.jitLpPayout = (IERC20(tokenA).balanceOf(jitAddr) - jitBalABefore)
            + (IERC20(tokenB).balanceOf(jitAddr) - jitBalBBefore);
    }

    // ── Step 7: Advance to passive LP exit (block B + JIT_ENTRY_OFFSET + PASSIVE_EXIT_OFFSET) ──
    ctx.vm.roll(block.number + PASSIVE_EXIT_OFFSET);

    // ── Step 8: Passive LP exit + fee tracking ──
    uint256[] memory payouts = new uint256[](cfg.n);
    for (uint256 i; i < cfg.n; ++i) {
        address lpAddr = acc.passiveLps[i].addr;
        (address tokenA, address tokenB) = resolveTokensFromCtx(ctx);
        uint256 balABefore = IERC20(tokenA).balanceOf(lpAddr);
        uint256 balBBefore = IERC20(tokenB).balanceOf(lpAddr);

        burnPosition(ctx, cfg.protocol, acc.passiveLps[i].privateKey, passiveTokenIds[i], UNIT_LIQUIDITY);
	// note: This is not multiplying the payoff by the price, since the CFMM or V4 pool
	// is the only market, It MUST use the CFMM price to multiply one of the amounts
	// by its price 
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

    // ── Step 9: Read delta-plus from FCI hook ──
    // The FCI hook captures θ_k = 1/lifetime_k for each removed position,
    // computing A_T = √(Σ θ_k · x_k²) and Δ⁺ = max(0, A_T - atNull).
    // This correctly penalizes short-lived JIT positions via the θ parameter.
    result.deltaPlus = IFCIDeltaPlusReader(fciHook).getDeltaPlus(
        PoolIdLibrary.toId(ctx.v4Pool)
    );
}

struct MultiRoundJitGameConfig {
    uint256 rounds;
    JitGameConfig roundConfig;
}

struct MultiRoundJitGameResult {
    uint128[] deltaPlusPerRound;
    uint256 finalHedgedLpPayout;
    uint256 finalUnhedgedLpPayout;
    uint256 totalJitLpPayout;
    WelfareResult welfare;
}

function runMultiRoundJitGame(
    Context storage ctx,
    Scenario storage s,
    MultiRoundJitGameConfig memory cfg,
    JitAccounts memory acc,
    address fciHook
) returns (MultiRoundJitGameResult memory result) {
    require(cfg.rounds > 0, "MultiRound: rounds must be > 0");
    validateJitConfig(cfg.roundConfig);

    result.deltaPlusPerRound = new uint128[](cfg.rounds);

    for (uint256 r; r < cfg.rounds; ++r) {
        JitGameResult memory roundResult = runJitGame(ctx, s, cfg.roundConfig, acc, fciHook);

        result.deltaPlusPerRound[r] = roundResult.deltaPlus;
        result.totalJitLpPayout += roundResult.jitLpPayout;

        // Keep last round's passive LP payouts as final
        if (r == cfg.rounds - 1) {
            result.finalHedgedLpPayout = roundResult.hedgedLpPayout;
            result.finalUnhedgedLpPayout = roundResult.unhedgedLpPayout;
        }
    }
}

/// @dev Multi-round game with deterministic JIT schedule and optional vault.
/// jitSchedule[r] = true forces JIT entry in round r, false forces no JIT.
/// When vault is configured (non-zero address), pokes epoch vault after burns
/// and before warp (poke-before-warp ordering), then settles after all rounds.
function runMultiRoundJitGameWithSchedule(
    Context storage ctx,
    Scenario storage s,
    MultiRoundJitGameConfig memory cfg,
    JitAccounts memory acc,
    address fciHook,
    VaultConfig memory vaultCfg,
    bool[] memory jitSchedule
) returns (MultiRoundJitGameResult memory result) {
    require(cfg.rounds > 0, "MultiRound: rounds must be > 0");
    require(jitSchedule.length == cfg.rounds, "MultiRound: schedule length mismatch");
    validateJitConfig(cfg.roundConfig);

    result.deltaPlusPerRound = new uint128[](cfg.rounds);
    uint256 totalHedgedLpFees;

    for (uint256 r; r < cfg.rounds; ++r) {
        // Override probability for deterministic scheduling
        cfg.roundConfig.jitEntryProbability = jitSchedule[r] ? 10000 : 0;

        JitGameResult memory roundResult = runJitGame(ctx, s, cfg.roundConfig, acc, fciHook);

        result.deltaPlusPerRound[r] = roundResult.deltaPlus;
        result.totalJitLpPayout += roundResult.jitLpPayout;
        totalHedgedLpFees += roundResult.hedgedLpPayout;

        if (r == cfg.rounds - 1) {
            result.finalHedgedLpPayout = roundResult.hedgedLpPayout;
            result.finalUnhedgedLpPayout = roundResult.unhedgedLpPayout;
        }

        // Vault poke: BEFORE warp (critical for epoch metric)
        if (vaultCfg.vault != address(0)) {
            uint128 epochDp = IFeeConcentrationIndex(fciHook)
                .getDeltaPlusEpoch(ctx.v4Pool, vaultCfg.reactive);
            console.log("  Round", r + 1);
            console.log("    JIT:", jitSchedule[r] ? "YES" : "NO ");
            console.log("    epochDp:", uint256(epochDp));
            console.log("    fees:", roundResult.hedgedLpPayout);

            IVaultPokeSettle(vaultCfg.vault).harness_pokeEpoch();
        }

        // Warp to next epoch
        ctx.vm.warp(block.timestamp + 1 days);
    }

    // Settlement
    if (vaultCfg.vault != address(0)) {
        (,, uint256 expiry,,,) = IVaultPokeSettle(vaultCfg.vault).harness_getVaultStorage();
        ctx.vm.warp(expiry + 1);
        IVaultPokeSettle(vaultCfg.vault).harness_settle();

        (,,,,, uint256 longPayoutPerToken) = IVaultPokeSettle(vaultCfg.vault).harness_getVaultStorage();
        result.welfare.longPayout = (vaultCfg.depositAmount * longPayoutPerToken) / (2 ** 96);
        result.welfare.shortPayout = vaultCfg.depositAmount - result.welfare.longPayout;
        result.welfare.hedgeValue = int256(result.welfare.longPayout) - int256(vaultCfg.depositAmount);
        result.welfare.lpFeeRevenue = totalHedgedLpFees;
        result.welfare.hedgedWelfare = totalHedgedLpFees + result.welfare.longPayout;
        result.welfare.unhedgedWelfare = totalHedgedLpFees;

        // Narrative summary
        console.log("  ---");
        console.log("  LONG payout:      ", result.welfare.longPayout);
        console.log("  Hedge deposit:    ", vaultCfg.depositAmount);
        console.log("  LP fee revenue:   ", result.welfare.lpFeeRevenue);
        console.log("  Hedged welfare:   ", result.welfare.hedgedWelfare);
        console.log("  Unhedged welfare: ", result.welfare.unhedgedWelfare);
        if (result.welfare.hedgedWelfare > result.welfare.unhedgedWelfare) {
            console.log("  VERDICT: HEDGE PROFITABLE");
        } else {
            console.log("  VERDICT: HEDGE UNPROFITABLE");
        }
    }
}

/// @dev Extract token addresses from Context. For V4, read from PoolKey.
/// Currency wraps address as bytes32 via Currency.wrap(). Unwrap reverses.
function resolveTokensFromCtx(Context storage ctx) view returns (address, address) {
    return (
        Currency.unwrap(ctx.v4Pool.currency0),
        Currency.unwrap(ctx.v4Pool.currency1)
    );
}
