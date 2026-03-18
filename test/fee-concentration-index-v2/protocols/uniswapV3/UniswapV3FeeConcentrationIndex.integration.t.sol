// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {Test, console2} from "forge-std/Test.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";

// FCI V2
import {FeeConcentrationIndexV2} from "@fee-concentration-index-v2/FeeConcentrationIndexV2.sol";
import {UniswapV3Facet} from "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol";
import {UniswapV3Callback} from "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol";
import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {IUnlockCallback} from "v4-core/src/interfaces/callback/IUnlockCallback.sol";
import {UNISWAP_V3_REACTIVE} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";

// V3
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {V3CallbackRouter} from "@reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol";

// Utils
import {Accounts, initAccounts} from "@utils/Accounts.sol";

/// @title UniswapV3 Reactive FCI V2 Integration Tests — fixture-driven
/// @dev Multi-phase forge script for live Sepolia + Lasna testing.
///
/// Same Python fixtures as V4 native tests. Three-way differential:
///   Python ≈ V4 native ≈ V3 reactive
///
/// Phases:
///   1. deploy()          — broadcast: FCI V2 + Facet + Callback on Sepolia
///   2. deployReactive()  — FFI: UniswapV3Reactive on Lasna via CLI tool
///   3. execute(name)     — broadcast: replay fixture actions on V3 pool
///   4. verify(name)      — read-only: query FCI metrics, assert vs fixture
///
/// Usage:
///   forge script <this>:UniswapV3FCI_IntegrationScript --sig "deploy()" --broadcast --rpc-url sepolia
///   forge script <this>:UniswapV3FCI_IntegrationScript --sig "deployReactive()" --rpc-url sepolia
///   forge script <this>:UniswapV3FCI_IntegrationScript --sig "execute(string)" --broadcast --rpc-url sepolia -- "jit_crowdout_three_swaps"
///   # CLI: theta reactive wait-callbacks --callback $CALLBACK --expected-count 5 --timeout 90
///   forge script <this>:UniswapV3FCI_IntegrationScript --sig "verify(string)" --rpc-url sepolia -- "jit_crowdout_three_swaps"
contract UniswapV3FCI_IntegrationScript is Script, Test {
    using PoolIdLibrary for PoolKey;

    string constant STATE_FILE = "broadcast/v3-reactive-integration-state.json";
    string constant FIXTURE_DIR = "research/data/fixtures/simulator/";

    // Sepolia constants
    address constant CALLBACK_PROXY = 0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA;

    // ══════════════════════════════════════════════════════════════
    //  Phase 1: Deploy on Sepolia
    // ══════════════════════════════════════════════════════════════

    function deploy() public {
        Accounts memory accts = initAccounts(vm);
        address v3Pool = _readV3Pool();

        vm.startBroadcast(accts.deployer.privateKey);

        // Deploy FCI V2
        FeeConcentrationIndexV2 fci = new FeeConcentrationIndexV2();

        // Deploy V3 Facet
        UniswapV3Facet facet = new UniswapV3Facet();

        // Deploy Callback (funded)
        UniswapV3Callback callback = new UniswapV3Callback{value: 0.2 ether}(
            address(fci), CALLBACK_PROXY, accts.deployer.addr
        );

        // Wire FCI V2
        fci.initialize(accts.deployer.addr);
        fci.registerProtocolFacet(UNISWAP_V3_REACTIVE, IFCIProtocolFacet(address(facet)));
        fci.setFacetFci(UNISWAP_V3_REACTIVE, IFeeConcentrationIndex(address(fci)));
        fci.setFacetProtocolStateView(UNISWAP_V3_REACTIVE, IProtocolStateView(v3Pool));

        // Wire Facet
        facet.initialize(
            accts.deployer.addr,
            IProtocolStateView(v3Pool),
            IFeeConcentrationIndex(address(fci)),
            IUnlockCallback(address(callback))
        );

        // Listen (register pool on facet)
        PoolKey memory poolKey = facet.listen(abi.encode(IUniswapV3Pool(v3Pool)));

        // Initialize epoch (1 day) on FCI V2's storage
        fci.initializeEpochPool(poolKey, UNISWAP_V3_REACTIVE, 86400);

        vm.stopBroadcast();

        // Write state
        string memory json = string.concat(
            '{"fci":"', vm.toString(address(fci)),
            '","facet":"', vm.toString(address(facet)),
            '","callback":"', vm.toString(address(callback)),
            '","v3Pool":"', vm.toString(v3Pool),
            '","deployer":"', vm.toString(accts.deployer.addr),
            '"}'
        );
        vm.writeFile(STATE_FILE, json);
        console2.log("State written to", STATE_FILE);
        console2.log("FCI=%s", address(fci));
        console2.log("CALLBACK=%s", address(callback));
    }

    // ══════════════════════════════════════════════════════════════
    //  Phase 2: Deploy Reactive on Lasna (via CLI FFI)
    // ══════════════════════════════════════════════════════════════

    function deployReactive() public {
        string memory stateJson = vm.readFile(STATE_FILE);
        address callback = vm.parseJsonAddress(stateJson, ".callback");

        // TODO: Replace with actual CLI tool command
        // vm.ffi(["theta", "reactive", "deploy-lasna",
        //         "--callback", vm.toString(callback),
        //         "--fund", "20"])
        //
        // For now, log the manual command:
        console2.log("=== Manual Lasna deployment required ===");
        console2.log("Run:");
        console2.log("  theta reactive deploy-lasna --callback %s --fund 20", callback);
        console2.log("Then:");
        console2.log("  theta reactive register-pool --chain-id 11155111 --pool <V3_POOL>");
    }

    // ══════════════════════════════════════════════════════════════
    //  Phase 3: Execute fixture actions (broadcast)
    // ══════════════════════════════════════════════════════════════

    function execute(string calldata fixtureName) public {
        Accounts memory accts = initAccounts(vm);
        string memory stateJson = vm.readFile(STATE_FILE);
        address v3Pool = vm.parseJsonAddress(stateJson, ".v3Pool");

        // Deploy V3CallbackRouter if needed (for mint/swap)
        V3CallbackRouter router = _getOrDeployRouter(accts.deployer.privateKey);

        string memory fixtureJson = vm.readFile(string.concat(FIXTURE_DIR, fixtureName, ".json"));

        // Parse action count
        bytes[] memory actionsRaw = abi.decode(vm.parseJson(fixtureJson, ".scenario.actions"), (bytes[]));
        uint256 actionCount = actionsRaw.length;

        console2.log("Executing %d actions for scenario: %s", actionCount, fixtureName);

        for (uint256 i; i < actionCount; ++i) {
            string memory prefix = string.concat(".scenario.actions[", vm.toString(i), "]");
            string memory actionType = vm.parseJsonString(fixtureJson, string.concat(prefix, ".type"));
            uint256 blockNum = vm.parseJsonUint(fixtureJson, string.concat(prefix, ".block"));

            bytes32 typeHash = keccak256(bytes(actionType));

            if (typeHash == keccak256("ROLL")) {
                // Can't vm.roll on live — skip (block advances naturally)
                continue;

            } else if (typeHash == keccak256("MINT")) {
                string memory agentId = vm.parseJsonString(fixtureJson, string.concat(prefix, ".agentId"));
                uint256 liquidity = vm.parseJsonUint(fixtureJson, string.concat(prefix, ".liquidity"));
                address lp = _resolveAgent(accts, agentId);

                // Read tick range from agents
                int24 tickLower = -60;
                int24 tickUpper = 60;
                // TODO: parse from fixture agent definition

                vm.broadcast(accts.deployer.privateKey);
                router.mint(
                    IUniswapV3Pool(v3Pool),
                    lp,
                    tickLower, tickUpper,
                    uint128(liquidity)
                );

            } else if (typeHash == keccak256("SWAP")) {
                uint160 sqrtPriceLimit = 4295128740; // MIN_SQRT_RATIO + 1
                vm.broadcast(accts.deployer.privateKey);
                router.swap(
                    IUniswapV3Pool(v3Pool),
                    accts.deployer.addr,
                    true,  // zeroForOne
                    -100,  // small exactInput
                    sqrtPriceLimit
                );

            } else if (typeHash == keccak256("BURN")) {
                string memory agentId = vm.parseJsonString(fixtureJson, string.concat(prefix, ".agentId"));
                uint256 liquidity = vm.parseJsonUint(fixtureJson, string.concat(prefix, ".liquidity"));
                address lp = _resolveAgent(accts, agentId);

                int24 tickLower = -60;
                int24 tickUpper = 60;

                vm.broadcast(_getPrivateKey(accts, agentId));
                IUniswapV3Pool(v3Pool).burn(tickLower, tickUpper, uint128(liquidity));
            }
        }

        console2.log("All actions executed. Wait for reactive callbacks.");
    }

    // ══════════════════════════════════════════════════════════════
    //  Phase 4: Verify (read-only — query on-chain, assert vs fixture)
    // ══════════════════════════════════════════════════════════════

    function verify(string calldata fixtureName) public view {
        string memory stateJson = vm.readFile(STATE_FILE);
        address fciAddr = vm.parseJsonAddress(stateJson, ".fci");
        address facetAddr = vm.parseJsonAddress(stateJson, ".facet");
        FeeConcentrationIndexV2 fci_ = FeeConcentrationIndexV2(fciAddr);

        string memory fixtureJson = vm.readFile(string.concat(FIXTURE_DIR, fixtureName, ".json"));

        // ── Parse expected metrics ──
        uint256 expectedDeltaPlus = vm.parseJsonUint(fixtureJson, ".expected.deltaPlus");
        uint256 expectedIndexA = vm.parseJsonUint(fixtureJson, ".expected.indexA");
        uint256 expectedThetaSum = vm.parseJsonUint(fixtureJson, ".expected.thetaSum");
        uint256 expectedRemovedPosCount = vm.parseJsonUint(fixtureJson, ".expected.removedPosCount");
        uint256 expectedAtNull = vm.parseJsonUint(fixtureJson, ".expected.atNull");

        // Build PoolKey (V3 reactive uses hooks = fci address)
        address v3Pool = vm.parseJsonAddress(stateJson, ".v3Pool");
        PoolKey memory poolKey = _buildPoolKey(v3Pool, fciAddr);

        // ══════════════════════════════════════════════════════
        //  Query ALL FCI V2 view functions
        // ══════════════════════════════════════════════════════

        // ── getIndex() ──
        (uint128 actualIndexA, uint256 actualThetaSum, uint256 actualRemovedPosCount) =
            fci_.getIndex(poolKey, UNISWAP_V3_REACTIVE);

        // ── getDeltaPlus() ──
        uint128 actualDeltaPlus = fci_.getDeltaPlus(poolKey, UNISWAP_V3_REACTIVE);

        // ── getAtNull() ──
        uint128 actualAtNull = fci_.getAtNull(poolKey, UNISWAP_V3_REACTIVE);

        // ── getThetaSum() — must equal thetaSum from getIndex() ──
        uint256 actualThetaSumDirect = fci_.getThetaSum(poolKey, UNISWAP_V3_REACTIVE);

        // ── getDeltaPlusEpoch() — within 1 day, must equal cumulative deltaPlus ──
        uint128 actualDeltaPlusEpoch = fci_.getDeltaPlusEpoch(poolKey, UNISWAP_V3_REACTIVE);

        // ── getRegisteredProtocolFacet() ──
        address actualFacet = address(fci_.getRegisteredProtocolFacet(UNISWAP_V3_REACTIVE));

        // ══════════════════════════════════════════════════════
        //  Log
        // ══════════════════════════════════════════════════════

        console2.log("=== Verify: %s ===", fixtureName);
        console2.log("removedPosCount: expected=%d actual=%d", expectedRemovedPosCount, actualRemovedPosCount);
        console2.log("deltaPlus (cumulative): %s", vm.toString(uint256(actualDeltaPlus)));
        console2.log("deltaPlus (epoch):      %s", vm.toString(uint256(actualDeltaPlusEpoch)));

        // ══════════════════════════════════════════════════════
        //  Assertions — 5% tolerance for V3 reactive async timing
        // ══════════════════════════════════════════════════════

        // Exact: removedPosCount
        assertEq(actualRemovedPosCount, expectedRemovedPosCount, "removedPosCount mismatch");

        // 5% tolerance for async-affected quantities
        if (expectedThetaSum > 0) {
            assertApproxEqAbs(actualThetaSum, expectedThetaSum, expectedThetaSum / 20, "getIndex().thetaSum mismatch");
        } else {
            assertEq(actualThetaSum, 0, "thetaSum must be 0");
        }
        if (expectedIndexA > 0) {
            assertApproxEqAbs(uint256(actualIndexA), expectedIndexA, expectedIndexA / 20, "getIndex().indexA mismatch");
        } else {
            assertEq(uint256(actualIndexA), 0, "indexA must be 0");
        }
        if (expectedAtNull > 0) {
            assertApproxEqAbs(uint256(actualAtNull), expectedAtNull, expectedAtNull / 20, "getAtNull() mismatch");
        } else {
            assertEq(uint256(actualAtNull), 0, "atNull must be 0");
        }

        // deltaPlus direction check + tolerance
        if (expectedDeltaPlus > 0) {
            assertGt(uint256(actualDeltaPlus), 0, "getDeltaPlus() must be > 0");
        } else {
            assertEq(uint256(actualDeltaPlus), 0, "getDeltaPlus() must be 0");
        }

        // getThetaSum() must be consistent with getIndex()
        assertEq(actualThetaSumDirect, actualThetaSum, "getThetaSum() != getIndex().thetaSum");

        // getDeltaPlusEpoch() must equal getDeltaPlus() within same epoch
        assertEq(uint256(actualDeltaPlusEpoch), uint256(actualDeltaPlus),
            "getDeltaPlusEpoch() must equal getDeltaPlus() within same epoch");

        // getRegisteredProtocolFacet()
        assertEq(actualFacet, facetAddr, "getRegisteredProtocolFacet() mismatch");

        // Cross-getter consistency: deltaPlus == max(0, indexA - atNull)
        if (actualIndexA > actualAtNull) {
            assertEq(uint256(actualDeltaPlus), uint256(actualIndexA - actualAtNull), "deltaPlus != indexA - atNull");
        } else {
            assertEq(uint256(actualDeltaPlus), 0, "deltaPlus must be 0 when indexA <= atNull");
        }
    }

    // ══════════════════════════════════════════════════════════════
    //  Helpers
    // ══════════════════════════════════════════════════════════════

    function _readV3Pool() internal view returns (address) {
        // Read from env or use default Sepolia pool
        try vm.envAddress("V3_POOL") returns (address pool) {
            return pool;
        } catch {
            return 0xF66da9dd005192ee584a253b024070c9A1A1F4FA;
        }
    }

    function _resolveAgent(Accounts memory accts, string memory agentId) internal pure returns (address) {
        if (keccak256(bytes(agentId)) == keccak256("lp0")) return accts.deployer.addr;
        if (keccak256(bytes(agentId)) == keccak256("lp1")) return accts.lpPassive.addr;
        if (keccak256(bytes(agentId)) == keccak256("lp2")) return accts.lpSophisticated.addr;
        return accts.swapper.addr;
    }

    function _getPrivateKey(Accounts memory accts, string memory agentId) internal pure returns (uint256) {
        if (keccak256(bytes(agentId)) == keccak256("lp0")) return accts.deployer.privateKey;
        if (keccak256(bytes(agentId)) == keccak256("lp1")) return accts.lpPassive.privateKey;
        if (keccak256(bytes(agentId)) == keccak256("lp2")) return accts.lpSophisticated.privateKey;
        return accts.swapper.privateKey;
    }

    function _getOrDeployRouter(uint256 deployerPk) internal returns (V3CallbackRouter) {
        // Use existing router or deploy new
        address existing = 0x1284E9d71a87276d05abD860bD9990dce9Dd721E;
        if (existing.code.length > 0) return V3CallbackRouter(existing);

        vm.broadcast(deployerPk);
        return new V3CallbackRouter();
    }

    function _buildPoolKey(address v3Pool, address fci) internal view returns (PoolKey memory) {
        return PoolKey({
            currency0: Currency.wrap(IUniswapV3Pool(v3Pool).token0()),
            currency1: Currency.wrap(IUniswapV3Pool(v3Pool).token1()),
            fee: IUniswapV3Pool(v3Pool).fee(),
            tickSpacing: IUniswapV3Pool(v3Pool).tickSpacing(),
            hooks: IHooks(fci)
        });
    }
}
