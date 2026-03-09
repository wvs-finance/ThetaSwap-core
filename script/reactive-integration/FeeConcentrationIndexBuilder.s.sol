// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {StdAssertions} from "forge-std/StdAssertions.sol";
import {console2} from "forge-std/console2.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IFeeConcentrationIndex} from "../../src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {ReactiveHookAdapter} from
    "../../src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol";
import {
    Scenario,
    Recipe,
    deltaPlusFactory,
    registerV3Pool,
    registerV4Pool,
    poolKey,
    recipeCrowdout,
    crowdoutPhase1,
    crowdoutPhase2,
    crowdoutPhase3,
    DELTA_EQUILIBRIUM,
    DELTA_MILD,
    DELTA_CROWDOUT
} from "../types/Scenario.sol";
import {Accounts, initAccounts} from "../types/Accounts.sol";
import {Protocol} from "../types/Protocol.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {
    Deployments,
    resolveDeployments,
    resolveTokens,
    ethSepoliaFCIHook,
    sepoliaFreshV3Pool,
    sepoliaV3CallbackRouter,
    sepoliaReactiveAdapter,
    SEPOLIA
} from "../utils/Deployments.sol";
import "../utils/Constants.sol";


// Broadcasts real transactions to fabricate a target delta-plus on-chain.
//
// Two paths:
//   V4 — local FCI hook computes delta-plus in afterSwap/afterRemoveLiquidity
//   V3 — Reactive Network adapter hears V3 events and mirrors FCI state
//
// Fresh pools (fee=3000) give clean FCI state for each differential test run.
//
// Usage:
//   # V4 single-block:
//   forge script FeeConcentrationIndexBuilderScript --sig "buildEquilibriumV4()" --broadcast --rpc-url $SEPOLIA_RPC_URL
//   forge script FeeConcentrationIndexBuilderScript --sig "buildMildV4()" --broadcast --rpc-url $SEPOLIA_RPC_URL
//
//   # V3 single-block:
//   forge script FeeConcentrationIndexBuilderScript --sig "buildEquilibriumV3()" --broadcast --rpc-url $SEPOLIA_RPC_URL
//   forge script FeeConcentrationIndexBuilderScript --sig "buildMildV3()" --broadcast --rpc-url $SEPOLIA_RPC_URL
//
//   # V4 multi-block (crowdout):
//   forge script FeeConcentrationIndexBuilderScript --sig "buildCrowdoutPhase1V4()" --broadcast --rpc-url $SEPOLIA_RPC_URL
//   # ... wait N blocks ...
//   forge script FeeConcentrationIndexBuilderScript --sig "buildCrowdoutPhase2V4()" --broadcast --rpc-url $SEPOLIA_RPC_URL
//   # ... wait N blocks ...
//   TOKEN_A=<id> forge script FeeConcentrationIndexBuilderScript --sig "buildCrowdoutPhase3V4()" --broadcast --rpc-url $SEPOLIA_RPC_URL
//
//   # V3 multi-block (crowdout):
//   forge script FeeConcentrationIndexBuilderScript --sig "buildCrowdoutPhase1V3()" --broadcast --rpc-url $SEPOLIA_RPC_URL
//   # ... wait N blocks ...
//   forge script FeeConcentrationIndexBuilderScript --sig "buildCrowdoutPhase2V3()" --broadcast --rpc-url $SEPOLIA_RPC_URL
//   # ... wait N blocks ...
//   TOKEN_A=<id> forge script FeeConcentrationIndexBuilderScript --sig "buildCrowdoutPhase3V3()" --broadcast --rpc-url $SEPOLIA_RPC_URL

contract FeeConcentrationIndexBuilderScript is Script, StdAssertions {
    // V4 scenario (fresh pool, fee=3000, FCI hook)
    Scenario internal scenarioV4;
    // V3 scenario (fresh pool, fee=3000, reactive adapter)
    Scenario internal scenarioV3;

    Accounts internal accounts;
    uint256 internal _chainId;

    // V4 hook — local FCI computation
    IFeeConcentrationIndex internal fciIndex;
    // V3 reactive adapter — mirrors FCI via Reactive Network events
    ReactiveHookAdapter internal reactiveAdapter;

    function setUp() public {
        accounts = initAccounts(vm);
        _chainId = block.chainid;
        require(_chainId == SEPOLIA, "Builder: only Eth Sepolia supported");

        scenarioV4.vm = vm;
        scenarioV3.vm = vm;

        (address tokenA, address tokenB) = resolveTokens(SEPOLIA);
        (address c0, address c1) = tokenA < tokenB
            ? (tokenA, tokenB)
            : (tokenB, tokenA);

        // ── V4 registration (fresh pool, fee=3000) ──
        Deployments memory d = resolveDeployments(SEPOLIA, Protocol.UniswapV4);
        address fciHook = ethSepoliaFCIHook();

        PoolKey memory v4Key = PoolKey({
            currency0: Currency.wrap(c0),
            currency1: Currency.wrap(c1),
            fee: 3000,
            tickSpacing: int24(TICK_SPACING),
            hooks: IHooks(fciHook)
        });
        registerV4Pool(scenarioV4, _chainId, v4Key, d.positionManager, d.swapRouter);
        fciIndex = d.fciIndex;

        // ── V3 registration (fresh pool, fee=3000) ──
        IUniswapV3Pool freshV3 = sepoliaFreshV3Pool();
        address adapter = sepoliaReactiveAdapter();
        address v3Router = sepoliaV3CallbackRouter();

        registerV3Pool(scenarioV3, _chainId, freshV3, adapter, v3Router);
        reactiveAdapter = ReactiveHookAdapter(payable(adapter));
    }

    // ═══════════════════════════════════════════════════════════════
    //  V4 — single-block recipes
    // ═══════════════════════════════════════════════════════════════

    function buildEquilibriumV4() public {
        deltaPlusFactory(
            scenarioV4, _chainId, Protocol.UniswapV4,
            accounts.lpPassive.privateKey,
            accounts.lpSophisticated.privateKey,
            accounts.swapper.privateKey,
            DELTA_EQUILIBRIUM
        );
        _logDeltaPlusV4("equilibrium");
    }

    function buildMildV4() public {
        deltaPlusFactory(
            scenarioV4, _chainId, Protocol.UniswapV4,
            accounts.lpPassive.privateKey,
            accounts.lpSophisticated.privateKey,
            accounts.swapper.privateKey,
            DELTA_MILD
        );
        _logDeltaPlusV4("mild");
    }

    // ═══════════════════════════════════════════════════════════════
    //  V4 — multi-block recipe: crowdout (US3-F)
    // ═══════════════════════════════════════════════════════════════

    function buildCrowdoutPhase1V4() public {
        Recipe memory r = recipeCrowdout();
        uint256 tokenA = crowdoutPhase1(
            scenarioV4, _chainId, Protocol.UniswapV4,
            accounts.lpPassive.privateKey, r.capitalA
        );
        console2.log("[V4] Phase 1 complete. TOKEN_A=%d", tokenA);
    }

    function buildCrowdoutPhase2V4() public {
        Recipe memory r = recipeCrowdout();
        uint256 tokenB = crowdoutPhase2(
            scenarioV4, _chainId, Protocol.UniswapV4,
            accounts.lpSophisticated.privateKey,
            accounts.swapper.privateKey,
            r.capitalB
        );
        console2.log("[V4] Phase 2 complete. TOKEN_B=%d (already burned)", tokenB);
    }

    function buildCrowdoutPhase3V4() public {
        Recipe memory r = recipeCrowdout();
        uint256 tokenA = vm.envUint("TOKEN_A");
        crowdoutPhase3(
            scenarioV4, _chainId, Protocol.UniswapV4,
            accounts.lpPassive.privateKey,
            accounts.swapper.privateKey,
            tokenA, r.capitalA
        );
        _logDeltaPlusV4("crowdout");
    }

    // ═══════════════════════════════════════════════════════════════
    //  V3 — single-block recipes
    // ═══════════════════════════════════════════════════════════════

    function buildEquilibriumV3() public {
        deltaPlusFactory(
            scenarioV3, _chainId, Protocol.UniswapV3,
            accounts.lpPassive.privateKey,
            accounts.lpSophisticated.privateKey,
            accounts.swapper.privateKey,
            DELTA_EQUILIBRIUM
        );
        _logDeltaPlusV3("equilibrium");
    }

    function buildMildV3() public {
        deltaPlusFactory(
            scenarioV3, _chainId, Protocol.UniswapV3,
            accounts.lpPassive.privateKey,
            accounts.lpSophisticated.privateKey,
            accounts.swapper.privateKey,
            DELTA_MILD
        );
        _logDeltaPlusV3("mild");
    }

    // ═══════════════════════════════════════════════════════════════
    //  V3 — multi-block recipe: crowdout (US3-F)
    // ═══════════════════════════════════════════════════════════════

    function buildCrowdoutPhase1V3() public {
        Recipe memory r = recipeCrowdout();
        uint256 tokenA = crowdoutPhase1(
            scenarioV3, _chainId, Protocol.UniswapV3,
            accounts.lpPassive.privateKey, r.capitalA
        );
        console2.log("[V3] Phase 1 complete. TOKEN_A=%d", tokenA);
    }

    function buildCrowdoutPhase2V3() public {
        Recipe memory r = recipeCrowdout();
        uint256 tokenB = crowdoutPhase2(
            scenarioV3, _chainId, Protocol.UniswapV3,
            accounts.lpSophisticated.privateKey,
            accounts.swapper.privateKey,
            r.capitalB
        );
        console2.log("[V3] Phase 2 complete. TOKEN_B=%d (already burned)", tokenB);
    }

    function buildCrowdoutPhase3V3() public {
        Recipe memory r = recipeCrowdout();
        uint256 tokenA = vm.envUint("TOKEN_A");
        crowdoutPhase3(
            scenarioV3, _chainId, Protocol.UniswapV3,
            accounts.lpPassive.privateKey,
            accounts.swapper.privateKey,
            tokenA, r.capitalA
        );
        _logDeltaPlusV3("crowdout");
    }

    // ═══════════════════════════════════════════════════════════════
    //  Assertions
    // ═══════════════════════════════════════════════════════════════

    function assertDeltaPlusV4(uint128 target) public view {
        PoolKey memory k = poolKey(scenarioV4, _chainId);
        uint128 actual = fciIndex.getDeltaPlus(k, false);
        assertApproxEqRel(
            uint256(actual), uint256(target), 0.05e18,
            "V4 deltaPlus diverged from target"
        );
    }

    function assertDeltaPlusV3(uint128 target) public view {
        PoolKey memory k = poolKey(scenarioV3, _chainId);
        uint128 actual = reactiveAdapter.getDeltaPlus(k, true);
        assertApproxEqRel(
            uint256(actual), uint256(target), 0.05e18,
            "V3 deltaPlus diverged from target"
        );
    }

    // ═══════════════════════════════════════════════════════════════
    //  Logging helpers
    // ═══════════════════════════════════════════════════════════════

    function _logDeltaPlusV4(string memory label) internal view {
        PoolKey memory k = poolKey(scenarioV4, _chainId);
        uint128 dp = fciIndex.getDeltaPlus(k, false);
        console2.log("[V4:%s] deltaPlus = %d", label, uint256(dp));
    }

    function _logDeltaPlusV3(string memory label) internal view {
        PoolKey memory k = poolKey(scenarioV3, _chainId);
        uint128 dp = reactiveAdapter.getDeltaPlus(k, true);
        console2.log("[V3:%s] deltaPlus = %d", label, uint256(dp));
    }
}
