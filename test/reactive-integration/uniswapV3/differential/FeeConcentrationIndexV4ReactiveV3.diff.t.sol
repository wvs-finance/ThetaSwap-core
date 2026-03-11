// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {Test, console2} from "forge-std/Test.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {Accounts, initAccounts} from "@foundry-script/types/Accounts.sol";

import {FeeConcentrationIndexBuilderScript} from
    "@foundry-script/reactive-integration/FeeConcentrationIndexBuilder.s.sol";
import {FeeConcentrationIndex} from
    "@fee-concentration-index/FeeConcentrationIndex.sol";
import {ReactiveHookAdapter} from
    "@reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol";
import {CallbackProxy} from
    "reactive-hooks/types/CallbackProxy.sol";
import {getCallbackProxy} from
    "reactive-hooks/libraries/CallbackProxyRegistryLib.sol";
import {ethSepoliaPoolManager} from "@foundry-script/utils/Deployments.sol";

/// @title FCI Differential Test — V4 Native vs V3 Reactive
/// @notice Three-phase differential test:
///   Phase 1 (deploy):   Deploys FCI hook + adapter on Sepolia, writes state JSON.
///   Phase 2 (run_*):    Reads state, runs V4+V3 scenarios, updates state JSON.
///   Phase 3 (verify):   Reads state, queries on-chain deltaPlus, asserts convergence.
///
/// Between phases, the shell orchestrator deploys ThetaSwapReactive on Lasna,
/// registers the V3 pool, funds the adapter, and waits for the relay.
///
/// Usage: ./script/reactive-integration/run-differential.sh mild
contract FeeConcentrationIndexV4ReactiveV3DiffTest is Script, Test {
    FeeConcentrationIndexBuilderScript internal builder;
    FeeConcentrationIndex internal fci;
    ReactiveHookAdapter internal adapter;
    Accounts internal accounts;

    string constant STATE_FILE = "broadcast/diff-test-state.json";

    // ═══════════════════════════════════════════════════════════════
    //  Phase 1: Deploy — deploy FCI hook + adapter, write state JSON
    // ═══════════════════════════════════════════════════════════════

    function deploy() public {
        accounts = initAccounts(vm);

        // 1. Deploy FCI hook (CREATE2 with mined salt for valid hook address)
        fci = _deployFCIHook(accounts.deployer.privateKey, ethSepoliaPoolManager());

        // 2. Deploy adapter (uses CallbackProxyRegistryLib for proxy address)
        vm.broadcast(accounts.deployer.privateKey);
        adapter = _deployAdapter();

        console2.log("FCI hook:", address(fci));
        console2.log("Adapter:", address(adapter));

        // Write deploy state (no pool keys yet — those come from run_*)
        string memory json = string.concat(
            '{"fci":"', vm.toString(address(fci)),
            '","adapter":"', vm.toString(address(adapter)),
            '"}'
        );
        vm.writeFile(STATE_FILE, json);
        console2.log("Deploy state written to", STATE_FILE);
    }

    // ═══════════════════════════════════════════════════════════════
    //  Phase 2: Run — read deploy state, run scenarios, update JSON
    // ═══════════════════════════════════════════════════════════════

    /// @notice Create V4+V3 pools and run V4 mild scenario.
    ///         V3 pool is created but operations are deferred to execute_mild_v3().
    function run_mild() public {
        _loadDeployState();

        builder.buildMildV4();
        builder.initPoolsV3();

        uint128 deltaPlusV4 = fci.getDeltaPlus(builder.v4PoolKey(), false);
        console2.log("V4 deltaPlus =", uint256(deltaPlusV4));
        console2.log("V3 pool =", builder.v3PoolAddr());

        _writeFullState(builder.v4PoolKey(), builder.v3PoolKey(), builder.v3PoolAddr());
    }

    /// @notice Execute V3 mild scenario operations on already-created pools.
    ///         Call AFTER registerPool on reactive so events are captured.
    function execute_mild_v3() public {
        _loadDeployState();

        // Load existing V3 pool from state (don't create new one)
        string memory json = vm.readFile(STATE_FILE);
        address v3Pool = vm.parseJsonAddress(json, ".v3_pool");
        builder.loadPoolsV3(v3Pool);
        builder.executeMildV3();

        console2.log("V3 mild scenario executed on pool:", v3Pool);
    }

    function run_crowdout() public {
        _loadDeployState();

        builder.buildCrowdoutPhase1V4();
        builder.buildCrowdoutPhase2V4();
        builder.buildCrowdoutPhase3V4();

        builder.buildCrowdoutPhase1V3();
        builder.buildCrowdoutPhase2V3();
        builder.buildCrowdoutPhase3V3();

        uint128 deltaPlusV4 = fci.getDeltaPlus(builder.v4PoolKey(), false);
        console2.log("V4 deltaPlus =", uint256(deltaPlusV4));
        console2.log("V3 pool =", builder.v3PoolAddr());

        _writeFullState(builder.v4PoolKey(), builder.v3PoolKey(), builder.v3PoolAddr());
    }

    /// @dev Load FCI + adapter from state JSON and wire up builder
    function _loadDeployState() internal {
        accounts = initAccounts(vm);

        string memory json = vm.readFile(STATE_FILE);
        address fciAddr = vm.parseJsonAddress(json, ".fci");
        address adapterAddr = vm.parseJsonAddress(json, ".adapter");

        fci = FeeConcentrationIndex(fciAddr);
        adapter = ReactiveHookAdapter(payable(adapterAddr));

        builder = new FeeConcentrationIndexBuilderScript();
        builder.setUp();
        builder.setDeployments(fciAddr, adapterAddr);

        console2.log("Loaded FCI:", fciAddr);
        console2.log("Loaded Adapter:", adapterAddr);
    }

    // ═══════════════════════════════════════════════════════════════
    //  Phase 2: Verify — read state JSON, query on-chain, assert
    // ═══════════════════════════════════════════════════════════════

    function verify() public {
        (
            address fciAddr,
            address adapterAddr,
            PoolKey memory v4Key,
            PoolKey memory v3Key
        ) = _readState();

        uint128 deltaPlusV4 = FeeConcentrationIndex(fciAddr).getDeltaPlus(v4Key, false);
        uint128 deltaPlusV3 = ReactiveHookAdapter(payable(adapterAddr)).getDeltaPlus(v3Key, true);

        console2.log("V4 deltaPlus =", uint256(deltaPlusV4));
        console2.log("V3 deltaPlus =", uint256(deltaPlusV3));

        assertApproxEqRel(
            uint256(deltaPlusV3), uint256(deltaPlusV4), 0.05e18,
            "deltaPlus: V3 diverged from V4"
        );
    }

    // ═══════════════════════════════════════════════════════════════
    //  State persistence (JSON)
    // ═══════════════════════════════════════════════════════════════

    function _writeFullState(PoolKey memory v4Key, PoolKey memory v3Key, address v3Pool) internal {
        string memory json = string.concat(
            '{"fci":"', vm.toString(address(fci)),
            '","adapter":"', vm.toString(address(adapter)),
            '","v3_pool":"', vm.toString(v3Pool),
            '","v4_currency0":"', vm.toString(Currency.unwrap(v4Key.currency0)),
            '","v4_currency1":"', vm.toString(Currency.unwrap(v4Key.currency1)),
            '","v4_fee":', vm.toString(v4Key.fee),
            ',"v4_tickSpacing":', vm.toString(int256(int24(v4Key.tickSpacing))),
            ',"v4_hooks":"', vm.toString(address(v4Key.hooks)),
            '","v3_currency0":"', vm.toString(Currency.unwrap(v3Key.currency0)),
            '","v3_currency1":"', vm.toString(Currency.unwrap(v3Key.currency1)),
            '","v3_fee":', vm.toString(v3Key.fee),
            ',"v3_tickSpacing":', vm.toString(int256(int24(v3Key.tickSpacing))),
            ',"v3_hooks":"', vm.toString(address(v3Key.hooks)),
            '"}'
        );
        vm.writeFile(STATE_FILE, json);
        console2.log("State written to", STATE_FILE);
    }

    function _readState() internal view returns (
        address fciAddr,
        address adapterAddr,
        PoolKey memory v4Key,
        PoolKey memory v3Key
    ) {
        string memory json = vm.readFile(STATE_FILE);

        fciAddr = vm.parseJsonAddress(json, ".fci");
        adapterAddr = vm.parseJsonAddress(json, ".adapter");

        v4Key = PoolKey({
            currency0: Currency.wrap(vm.parseJsonAddress(json, ".v4_currency0")),
            currency1: Currency.wrap(vm.parseJsonAddress(json, ".v4_currency1")),
            fee: uint24(vm.parseJsonUint(json, ".v4_fee")),
            tickSpacing: int24(int256(vm.parseJsonInt(json, ".v4_tickSpacing"))),
            hooks: IHooks(vm.parseJsonAddress(json, ".v4_hooks"))
        });

        v3Key = PoolKey({
            currency0: Currency.wrap(vm.parseJsonAddress(json, ".v3_currency0")),
            currency1: Currency.wrap(vm.parseJsonAddress(json, ".v3_currency1")),
            fee: uint24(vm.parseJsonUint(json, ".v3_fee")),
            tickSpacing: int24(int256(vm.parseJsonInt(json, ".v3_tickSpacing"))),
            hooks: IHooks(vm.parseJsonAddress(json, ".v3_hooks"))
        });
    }

    // ═══════════════════════════════════════════════════════════════
    //  Deployment helpers (Sepolia)
    // ═══════════════════════════════════════════════════════════════

    // Forge routes `new X{salt}()` through this factory under vm.broadcast
    address constant CREATE2_DEPLOYER = 0x4e59b44847b379578588920cA78FbF26c0B4956C;

    function _deployFCIHook(uint256 deployerPK, address poolManager) internal returns (FeeConcentrationIndex) {
        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
                | Hooks.BEFORE_SWAP_FLAG
                | Hooks.AFTER_SWAP_FLAG
                | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
                | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
        );

        bytes memory creationCode = type(FeeConcentrationIndex).creationCode;
        bytes memory constructorArgs = abi.encode(poolManager);

        (address hookAddress, bytes32 salt) =
            _findHookSalt(CREATE2_DEPLOYER, flags, creationCode, constructorArgs);

        vm.broadcast(deployerPK);
        FeeConcentrationIndex hook = new FeeConcentrationIndex{salt: salt}(poolManager);
        require(address(hook) == hookAddress, "hook address mismatch");
        return hook;
    }

    // ── Inlined HookMiner (avoids address(this) issues in forge script) ──

    uint160 constant FLAG_MASK = Hooks.ALL_HOOK_MASK;
    uint256 constant MAX_LOOP = 160_444;

    function _findHookSalt(
        address deployer_,
        uint160 flags,
        bytes memory creationCode,
        bytes memory constructorArgs
    ) internal view returns (address hookAddress, bytes32 salt) {
        flags = flags & FLAG_MASK;
        bytes32 initCodeHash = keccak256(abi.encodePacked(creationCode, constructorArgs));

        for (uint256 s; s < MAX_LOOP; s++) {
            hookAddress = address(
                uint160(
                    uint256(
                        keccak256(
                            abi.encodePacked(bytes1(0xFF), deployer_, bytes32(s), initCodeHash)
                        )
                    )
                )
            );
            if (uint160(hookAddress) & FLAG_MASK == flags && hookAddress.code.length == 0) {
                return (hookAddress, bytes32(s));
            }
        }
        revert("HookMiner: could not find salt");
    }

    function _deployAdapter() internal returns (ReactiveHookAdapter) {
        CallbackProxy proxy = getCallbackProxy(block.chainid);
        return new ReactiveHookAdapter{value: 0}(CallbackProxy.unwrap(proxy));
    }

}
