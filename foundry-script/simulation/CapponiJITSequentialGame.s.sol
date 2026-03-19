// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script, console} from "forge-std/Script.sol";
import {StdCheats} from "forge-std/StdCheats.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";

import {Context} from "@foundry-script/types/Context.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";
import {Scenario} from "@foundry-script/types/Scenario.sol";
import {
    JitGameConfig,
    JitGameResult,
    JitAccounts,
    initJitAccounts,
    runJitGame,
    UNIT_LIQUIDITY
} from "@foundry-script/simulation/JitGame.sol";
import {
    resolveDeployments,
    Deployments,
    UNICHAIN_SEPOLIA,
    resolveTokens
} from "@foundry-script/utils/Deployments.sol";
import "@foundry-script/utils/Constants.sol";

contract CapponiJITSequentialGameScript is Script, StdCheats {
    Context ctx;
    Scenario scenario;

    function run(
        uint256 n,
        uint256 jitCapital,
        uint256 jitEntryProbability,
        uint256 tradeSize
    ) public {
        // ── 1. Fork ──
        vm.createSelectFork("unichain_sepolia");
        uint256 chainId = block.chainid;

        // ── 2. Build Context ──
        Deployments memory d = resolveDeployments(chainId, Protocol.UniswapV4);
        (address tokenA, address tokenB) = resolveTokens(chainId);

        ctx.vm = vm;
        ctx.v4PositionManager = d.positionManager;
        ctx.v4SwapRouter = d.swapRouter;
        ctx.chainId = chainId;

        // Build PoolKey — standard 0.30% fee tier, tick spacing 60
        ctx.v4Pool = PoolKey({
            currency0: Currency.wrap(tokenA),
            currency1: Currency.wrap(tokenB),
            fee: 3000,
            tickSpacing: 60,
            hooks: IHooks(address(0))
        });

        // ── 3. Build Config ──
        JitGameConfig memory cfg = JitGameConfig({
            n: n,
            jitCapital: jitCapital,
            jitEntryProbability: jitEntryProbability,
            tradeSize: tradeSize,
            zeroForOne: true,
            protocol: Protocol.UniswapV4
        });

        // ── 4. Generate and fund accounts ──
        JitAccounts memory acc = initJitAccounts(vm, n);
        _fundAccounts(acc, tokenA, tokenB, jitCapital);
        _approveAll(acc, tokenA, tokenB, d.positionManager, d.swapRouter);

        // ── 5. Run game ──
        JitGameResult memory result = runJitGame(ctx, scenario, cfg, acc, address(ctx.v4Pool.hooks));

        // ── 6. Emit results ──
        console.log("=== Capponi JIT Sequential Game Results ===");
        console.log("N (passive LPs):", n);
        console.log("JIT capital:", jitCapital);
        console.log("JIT entry prob (bps):", jitEntryProbability);
        console.log("Trade size:", tradeSize);
        console.log("JIT entered:", result.jitEntered);
        console.log("Delta-plus (Q128):", uint256(result.deltaPlus));
        console.log("Hedged LP payout:", result.hedgedLpPayout);
        console.log("Unhedged LP payout (worst):", result.unhedgedLpPayout);
        console.log("JIT LP payout:", result.jitLpPayout);
    }

    function _fundAccounts(
        JitAccounts memory acc,
        address tokenA,
        address tokenB,
        uint256 jitCapital
    ) internal {
        for (uint256 i; i < acc.passiveLps.length; ++i) {
            address lp = acc.passiveLps[i].addr;
            vm.deal(lp, 1 ether);
            deal(tokenA, lp, UNIT_LIQUIDITY);
            deal(tokenB, lp, UNIT_LIQUIDITY);
        }
        vm.deal(acc.jitLp.addr, 1 ether);
        deal(tokenA, acc.jitLp.addr, jitCapital);
        deal(tokenB, acc.jitLp.addr, jitCapital);

        vm.deal(acc.swapper.addr, 1 ether);
        deal(tokenA, acc.swapper.addr, UNIT_LIQUIDITY * 10);
        deal(tokenB, acc.swapper.addr, UNIT_LIQUIDITY * 10);
    }

    function _approveAll(
        JitAccounts memory acc,
        address tokenA,
        address tokenB,
        address positionManager,
        address swapRouter_
    ) internal {
        for (uint256 i; i < acc.passiveLps.length; ++i) {
            _approveFor(acc.passiveLps[i].privateKey, tokenA, tokenB, positionManager);
        }
        _approveFor(acc.jitLp.privateKey, tokenA, tokenB, positionManager);
        _approveFor(acc.swapper.privateKey, tokenA, tokenB, swapRouter_);
    }

    function _approveFor(
        uint256 pk,
        address tokenA,
        address tokenB,
        address spender
    ) internal {
        vm.startBroadcast(pk);
        IERC20(tokenA).approve(spender, type(uint256).max);
        IERC20(tokenB).approve(spender, type(uint256).max);
        vm.stopBroadcast();
    }
}
