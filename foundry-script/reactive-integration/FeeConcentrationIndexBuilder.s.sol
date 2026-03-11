// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {StdAssertions} from "forge-std/StdAssertions.sol";
import {console2} from "forge-std/console2.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {ReactiveHookAdapter} from
    "@reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol";
import {
    Scenario,
    Recipe,
    deltaPlusFactory,
    recipeCrowdout,
    crowdoutPhase1,
    crowdoutPhase2,
    crowdoutPhase3,
    DELTA_EQUILIBRIUM,
    DELTA_MILD,
    DELTA_CROWDOUT
} from "@foundry-script/types/Scenario.sol";
import {Context} from "@foundry-script/types/Context.sol";
import {Accounts, initAccounts} from "@foundry-script/types/Accounts.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {
    Deployments,
    resolveDeployments,
    resolveTokens,
    ethSepoliaFCIHook,
    ethSepoliaPoolManager,
    sepoliaV3Factory,
    sepoliaV3CallbackRouter,
    sepoliaReactiveAdapter,
    SEPOLIA
} from "@foundry-script/utils/Deployments.sol";
import {fromV3Pool} from "reactive-hooks/libraries/PoolKeyExtMod.sol";
import {IAllowanceTransfer} from "permit2/src/interfaces/IAllowanceTransfer.sol";
import "@foundry-script/utils/Constants.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {IUniswapV3Factory} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol";
import {MockERC20} from "solady/../test/utils/mocks/MockERC20.sol";


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



struct PoolFactoryStorage{
    PoolKey v4Pool;
    IUniswapV3Pool v3Pool;
    uint256 counter;
}
bytes32 constant POOL_FACTORY_STORAGE_SLOT = keccak256("thetaSwap.poolFactoryStorage");

function getPools() pure returns(PoolFactoryStorage storage $){
    bytes32 pos = POOL_FACTORY_STORAGE_SLOT;
    assembly("memory-safe"){
       $.slot := pos
    }
}
function increment() returns(uint256){
    PoolFactoryStorage storage $ = getPools();
    $.counter++;
    return $.counter;
}

function v4Pool() view returns(PoolKey memory){
    PoolFactoryStorage storage $ = getPools();
    return $.v4Pool;
}

function v3Pool() view returns(IUniswapV3Pool){
    PoolFactoryStorage storage $ = getPools();
    return $.v3Pool;
}
function createPools(IUniswapV3Factory v3Factory, IPoolManager v4Manager, address fci) {
    PoolFactoryStorage storage $ = getPools();

    // Seed counter with block.number on first call to avoid CREATE2 collisions across runs
    if ($.counter == 0) $.counter = block.number * 100;

    // Deploy fresh mock tokens (CREATE2 with counter salt for unique addresses)
    MockERC20 tokenA = new MockERC20{salt: bytes32(increment())}("TestA", "TKA", 18);
    MockERC20 tokenB = new MockERC20{salt: bytes32(increment())}("TestB", "TKB", 18);

    // Sort for Uniswap ordering (currency0 < currency1)
    (address t0, address t1) = address(tokenA) < address(tokenB)
        ? (address(tokenA), address(tokenB))
        : (address(tokenB), address(tokenA));

    // Create V3 pool
    $.v3Pool = IUniswapV3Pool(v3Factory.createPool(t0, t1, Constants.FEE_MEDIUM));
    $.v3Pool.initialize(Constants.SQRT_PRICE_1_1);

    // Initialize V4 pool
    $.v4Pool = PoolKey({
        currency0: Currency.wrap(t0),
        currency1: Currency.wrap(t1),
        fee: Constants.FEE_MEDIUM,
        tickSpacing: int24(TICK_SPACING),
        hooks: IHooks(fci)
    });
    v4Manager.initialize($.v4Pool, Constants.SQRT_PRICE_1_1);
} 

// note: setUp seeds actors with tokens and approves routers for both V3 and V4 pools.
// Called after createPools. Uses vm.broadcast per actor to sign real txs.
// function seedActors(Vm vm, Accounts memory accounts, PoolKey memory v4Key, IUniswapV3Pool v3PoolAddr, Deployments memory d) {
//     // TODO: mint tokens to each actor, approve V3 router + V4 PositionManager + SwapRouter
// }

contract PoolFactory {
    IUniswapV3Factory immutable V3_FACTORY;
    IPoolManager immutable V4_FACTORY;
    address immutable FCI;

    constructor(IUniswapV3Factory v3Factory, IPoolManager v4Factory, address fci) {
        (V3_FACTORY, V4_FACTORY, FCI) = (v3Factory, v4Factory, fci);
        run();
    }

    function run() public {
        createPools(V3_FACTORY, V4_FACTORY, FCI);
    }
}

contract FeeConcentrationIndexBuilderScript is Script, StdAssertions {
    // V4 context + scenario (fresh pool, fee=3000, FCI hook)
    Context internal ctxV4;
    Scenario internal scenarioV4;
    // V3 context + scenario (fresh pool, fee=3000, reactive adapter)
    Context internal ctxV3;
    Scenario internal scenarioV3;

    // V4 hook — local FCI computation
    IFeeConcentrationIndex internal fciIndex;
    // V3 reactive adapter — mirrors FCI via Reactive Network events
    ReactiveHookAdapter internal reactiveAdapter;

    function setUp() public {
        Accounts memory accounts = initAccounts(vm);
        uint256 chainId = block.chainid;
        require(chainId == SEPOLIA, "Builder: only Eth Sepolia supported");

        Deployments memory d = resolveDeployments(SEPOLIA, Protocol.UniswapV4);
        fciIndex = d.fciIndex;

        // ── V4 context (infrastructure only — pools created per-build) ──
        ctxV4.vm = vm;
        ctxV4.accounts = accounts;
        ctxV4.chainId = chainId;
        ctxV4.v4PositionManager = d.positionManager;
        ctxV4.v4SwapRouter = d.swapRouter;

        // ── V3 context (infrastructure only — pools created per-build) ──
        ctxV3.vm = vm;
        ctxV3.accounts = accounts;
        ctxV3.chainId = chainId;
        ctxV3.adapter = sepoliaReactiveAdapter();
        ctxV3.v3Router = sepoliaV3CallbackRouter();
        reactiveAdapter = ReactiveHookAdapter(payable(ctxV3.adapter));
    }

    // ═══════════════════════════════════════════════════════════════
    //  Fresh pool deployment (called per-build)
    // ═══════════════════════════════════════════════════════════════

    function _toMemory(Scenario storage s) internal view returns (Scenario memory) {
        return Scenario({tokenIds: s.tokenIds, deltaPlus: s.deltaPlus});
    }

    function _initFreshPoolsV4() internal {
        vm.startBroadcast(ctxV4.accounts.deployer.privateKey);
        createPools(
            IUniswapV3Factory(sepoliaV3Factory()),
            IPoolManager(ethSepoliaPoolManager()),
            address(fciIndex)
        );
        vm.stopBroadcast();
        ctxV4.v4Pool = v4Pool();
        _seedActorsFromKey(ctxV4.v4Pool);
    }

    function _initFreshPoolsV3() internal {
        vm.startBroadcast(ctxV3.accounts.deployer.privateKey);
        createPools(
            IUniswapV3Factory(sepoliaV3Factory()),
            IPoolManager(ethSepoliaPoolManager()),
            address(fciIndex)
        );
        vm.stopBroadcast();
        ctxV3.v3Pool = v3Pool();
        ctxV3.v4Pool = fromV3Pool(ctxV3.v3Pool, ctxV3.adapter);
        _seedActorsFromKey(ctxV3.v4Pool);
    }

    function _seedActorsFromKey(PoolKey memory key) internal {
        address t0 = Currency.unwrap(key.currency0);
        address t1 = Currency.unwrap(key.currency1);
        uint256 supply = 100e18;
        uint256 deployerPK = ctxV4.accounts.deployer.privateKey;
        address permit2 = 0x000000000022D473030F116dDEE9F6B43aC78BA3;
        uint48 deadline = type(uint48).max - 1;

        // Mint tokens to all actors
        address[3] memory actors = [
            ctxV4.accounts.lpPassive.addr,
            ctxV4.accounts.lpSophisticated.addr,
            ctxV4.accounts.swapper.addr
        ];

        for (uint256 i; i < 3; ++i) {
            vm.broadcast(deployerPK);
            MockERC20(t0).mint(actors[i], supply);
            vm.broadcast(deployerPK);
            MockERC20(t1).mint(actors[i], supply);
        }

        // LPs: ERC20→Permit2→PositionManager (V4) + V3CallbackRouter (V3)
        uint256[2] memory lpPKs = [
            ctxV4.accounts.lpPassive.privateKey,
            ctxV4.accounts.lpSophisticated.privateKey
        ];
        for (uint256 i; i < 2; ++i) {
            vm.startBroadcast(lpPKs[i]);
            MockERC20(t0).approve(permit2, type(uint256).max);
            MockERC20(t1).approve(permit2, type(uint256).max);
            IAllowanceTransfer(permit2).approve(t0, ctxV4.v4PositionManager, type(uint160).max, deadline);
            IAllowanceTransfer(permit2).approve(t1, ctxV4.v4PositionManager, type(uint160).max, deadline);
            MockERC20(t0).approve(ctxV3.v3Router, type(uint256).max);
            MockERC20(t1).approve(ctxV3.v3Router, type(uint256).max);
            vm.stopBroadcast();
        }

        // Swapper: approve SwapRouter (V4) + V3CallbackRouter (V3)
        vm.startBroadcast(ctxV4.accounts.swapper.privateKey);
        MockERC20(t0).approve(ctxV4.v4SwapRouter, type(uint256).max);
        MockERC20(t1).approve(ctxV4.v4SwapRouter, type(uint256).max);
        MockERC20(t0).approve(ctxV3.v3Router, type(uint256).max);
        MockERC20(t1).approve(ctxV3.v3Router, type(uint256).max);
        vm.stopBroadcast();
    }

    // ═══════════════════════════════════════════════════════════════
    //  V4 — single-block recipes
    // ═══════════════════════════════════════════════════════════════

    function buildEquilibriumV4() public returns (Scenario memory) {
        _initFreshPoolsV4();
        deltaPlusFactory(ctxV4, scenarioV4, Protocol.UniswapV4, DELTA_EQUILIBRIUM);
        _logDeltaPlusV4("equilibrium");
        return _toMemory(scenarioV4);
    }

    function buildMildV4() public returns (Scenario memory) {
        _initFreshPoolsV4();
        deltaPlusFactory(ctxV4, scenarioV4, Protocol.UniswapV4, DELTA_MILD);
        _logDeltaPlusV4("mild");
        return _toMemory(scenarioV4);
    }

    // ═══════════════════════════════════════════════════════════════
    //  V4 — multi-block recipe: crowdout (US3-F)
    // ═══════════════════════════════════════════════════════════════

    function buildCrowdoutPhase1V4() public returns (Scenario memory) {
        _initFreshPoolsV4();
        Recipe memory r = recipeCrowdout();
        uint256 tokenA = crowdoutPhase1(ctxV4, scenarioV4, Protocol.UniswapV4, r.capitalA);
        console2.log("[V4] Phase 1 complete. TOKEN_A=%d", tokenA);
        return _toMemory(scenarioV4);
    }

    function buildCrowdoutPhase2V4() public returns (Scenario memory) {
        Recipe memory r = recipeCrowdout();
        uint256 tokenB = crowdoutPhase2(ctxV4, scenarioV4, Protocol.UniswapV4, r.capitalB);
        console2.log("[V4] Phase 2 complete. TOKEN_B=%d (already burned)", tokenB);
        return _toMemory(scenarioV4);
    }

    function buildCrowdoutPhase3V4() public returns (Scenario memory) {
        Recipe memory r = recipeCrowdout();
        uint256 tokenA = vm.envUint("TOKEN_A");
        crowdoutPhase3(ctxV4, scenarioV4, Protocol.UniswapV4, tokenA, r.capitalA);
        _logDeltaPlusV4("crowdout");
        return _toMemory(scenarioV4);
    }

    // ═══════════════════════════════════════════════════════════════
    //  V3 — single-block recipes
    // ═══════════════════════════════════════════════════════════════

    function buildEquilibriumV3() public returns (Scenario memory) {
        _initFreshPoolsV3();
        deltaPlusFactory(ctxV3, scenarioV3, Protocol.UniswapV3, DELTA_EQUILIBRIUM);
        _logDeltaPlusV3("equilibrium");
        return _toMemory(scenarioV3);
    }

    function buildMildV3() public returns (Scenario memory) {
        _initFreshPoolsV3();
        deltaPlusFactory(ctxV3, scenarioV3, Protocol.UniswapV3, DELTA_MILD);
        _logDeltaPlusV3("mild");
        return _toMemory(scenarioV3);
    }

    /// @notice Create V3 pools + seed actors without running scenario operations.
    ///         Call this first, then register the pool on reactive, then call executeMildV3().
    function initPoolsV3() public {
        _initFreshPoolsV3();
        console2.log("[V3] Pools initialized. V3 pool:", address(ctxV3.v3Pool));
    }

    /// @notice Load an existing V3 pool and seed actors (no new pool creation).
    ///         Use when resuming from a state file with a known V3 pool address.
    function loadPoolsV3(address v3PoolAddr) public {
        IUniswapV3Pool pool = IUniswapV3Pool(v3PoolAddr);
        ctxV3.v3Pool = pool;
        ctxV3.v4Pool = fromV3Pool(pool, ctxV3.adapter);
        _seedActorsFromKey(ctxV3.v4Pool);
        console2.log("[V3] Loaded existing pool:", v3PoolAddr);
    }

    /// @notice Run mild scenario on already-initialized V3 pools.
    ///         Requires initPoolsV3() or loadPoolsV3() to have been called first.
    function executeMildV3() public returns (Scenario memory) {
        require(address(ctxV3.v3Pool) != address(0), "V3 pools not initialized");
        deltaPlusFactory(ctxV3, scenarioV3, Protocol.UniswapV3, DELTA_MILD);
        _logDeltaPlusV3("mild");
        return _toMemory(scenarioV3);
    }

    // ═══════════════════════════════════════════════════════════════
    //  V3 — multi-block recipe: crowdout (US3-F)
    // ═══════════════════════════════════════════════════════════════

    function buildCrowdoutPhase1V3() public returns (Scenario memory) {
        _initFreshPoolsV3();
        Recipe memory r = recipeCrowdout();
        uint256 tokenA = crowdoutPhase1(ctxV3, scenarioV3, Protocol.UniswapV3, r.capitalA);
        console2.log("[V3] Phase 1 complete. TOKEN_A=%d", tokenA);
        return _toMemory(scenarioV3);
    }

    function buildCrowdoutPhase2V3() public returns (Scenario memory) {
        Recipe memory r = recipeCrowdout();
        uint256 tokenB = crowdoutPhase2(ctxV3, scenarioV3, Protocol.UniswapV3, r.capitalB);
        console2.log("[V3] Phase 2 complete. TOKEN_B=%d (already burned)", tokenB);
        return _toMemory(scenarioV3);
    }

    function buildCrowdoutPhase3V3() public returns (Scenario memory) {
        Recipe memory r = recipeCrowdout();
        uint256 tokenA = vm.envUint("TOKEN_A");
        crowdoutPhase3(ctxV3, scenarioV3, Protocol.UniswapV3, tokenA, r.capitalA);
        _logDeltaPlusV3("crowdout");
        return _toMemory(scenarioV3);
    }

    // ═══════════════════════════════════════════════════════════════
    //  Pool key accessors (for external test consumers)
    // ═══════════════════════════════════════════════════════════════

    function v4PoolKey() public view returns (PoolKey memory) { return ctxV4.v4Pool; }
    function v3PoolKey() public view returns (PoolKey memory) { return ctxV3.v4Pool; }
    function v3PoolAddr() public view returns (address) { return address(ctxV3.v3Pool); }

    /// @notice Override hook + adapter addresses (for differential test injection)
    function setDeployments(address fciHook, address adapterAddr) public {
        fciIndex = IFeeConcentrationIndex(fciHook);
        reactiveAdapter = ReactiveHookAdapter(payable(adapterAddr));
        ctxV3.adapter = adapterAddr;
    }

    // ═══════════════════════════════════════════════════════════════
    //  Assertions
    // ═══════════════════════════════════════════════════════════════

    function assertDeltaPlusV4(uint128 target) public view {
        uint128 actual = fciIndex.getDeltaPlus(ctxV4.v4Pool, false);
        assertApproxEqRel(
            uint256(actual), uint256(target), 0.05e18,
            "V4 deltaPlus diverged from target"
        );
    }

    function assertDeltaPlusV3(uint128 target) public view {
        uint128 actual = reactiveAdapter.getDeltaPlus(ctxV3.v4Pool, true);
        assertApproxEqRel(
            uint256(actual), uint256(target), 0.05e18,
            "V3 deltaPlus diverged from target"
        );
    }

    // ═══════════════════════════════════════════════════════════════
    //  Logging helpers
    // ═══════════════════════════════════════════════════════════════

    function _logDeltaPlusV4(string memory label) internal view {
        uint128 dp = fciIndex.getDeltaPlus(ctxV4.v4Pool, false);
        console2.log("[V4:%s] deltaPlus = %d", label, uint256(dp));
    }

    function _logDeltaPlusV3(string memory label) internal view {
        uint128 dp = reactiveAdapter.getDeltaPlus(ctxV3.v4Pool, true);
        console2.log("[V3:%s] deltaPlus = %d", label, uint256(dp));
    }
}
