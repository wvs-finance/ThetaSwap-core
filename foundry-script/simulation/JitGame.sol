// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Vm} from "forge-std/Vm.sol";
import {Protocol, isUniswapV3, isUniswapV4} from "@foundry-script/types/Protocol.sol";
import {DEFAULT_DERIVATION_PATH} from "@foundry-script/types/Accounts.sol";
import {Context} from "@foundry-script/types/Context.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {SwapParams} from "v4-core/src/types/PoolOperation.sol";
import {PoolSwapTest} from "v4-core/src/test/PoolSwapTest.sol";
import {V3CallbackRouter} from "@reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol";
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
