// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {Test, console2} from "forge-std/Test.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";

import {FeeConcentrationIndexV2} from "@fee-concentration-index-v2/FeeConcentrationIndexV2.sol";
import {UniswapV3Facet} from "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol";
import {UniswapV3Callback} from "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol";
import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {IUnlockCallback} from "v4-core/src/interfaces/callback/IUnlockCallback.sol";
import {UNISWAP_V3_REACTIVE} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";

import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {V3CallbackRouter} from "@reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol";

import {Accounts, initAccounts} from "@utils/Accounts.sol";

/// @title UniswapV3 Reactive FCI V2 — Phased integration test
/// @notice Split into deploy/mint/burn/verify phases for real-time sleep between them.
///
/// Usage (via shell orchestrator):
///   ./scripts/run-v3-integration.sh
///
/// Or manually:
///   forge script <this>:UniswapV3FCI_IntegrationScript --sig "deploy()" --broadcast --slow --rpc-url sepolia -vv
///   ./scripts/deploy-reactive.sh $LASNA_RPC $PK $CALLBACK $V3_POOL broadcast/reactive-addr.txt
///   sleep 10
///   forge script <this>:UniswapV3FCI_IntegrationScript --sig "mint()" --broadcast --slow --rpc-url sepolia -vv
///   sleep 90
///   forge script <this>:UniswapV3FCI_IntegrationScript --sig "burn()" --broadcast --slow --rpc-url sepolia -vv
///   sleep 90
///   forge script <this>:UniswapV3FCI_IntegrationScript --sig "verify()" --rpc-url sepolia -vv
contract UniswapV3FCI_IntegrationScript is Script, Test {
    using PoolIdLibrary for PoolKey;

    address constant CALLBACK_PROXY = 0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA;
    address constant DEFAULT_V3_POOL = 0xF66da9dd005192ee584a253b024070c9A1A1F4FA;
    address constant DEFAULT_V3_ROUTER = 0x1284E9d71a87276d05abD860bD9990dce9Dd721E;
    string constant STATE_FILE = "broadcast/v3-integration-state.json";

    // ═══════════════════════════════════════════════════════════════
    //  Phase 1: Deploy FCI V2 + Facet + Callback on Sepolia
    // ═══════════════════════════════════════════════════════════════

    function deploy() public {
        Accounts memory accts = initAccounts(vm);
        address v3Pool = _readV3Pool();

        vm.startBroadcast(accts.deployer.privateKey);

        FeeConcentrationIndexV2 fci = new FeeConcentrationIndexV2();
        UniswapV3Facet facet = new UniswapV3Facet();
        // rvmId = reactiveDeployer (index 4) — the EOA that deploys the reactive on Lasna.
        // The callback proxy replaces address(0) with the reactive's deployer address.
        UniswapV3Callback callback = new UniswapV3Callback{value: 0.1 ether}(
            address(fci), CALLBACK_PROXY, accts.reactiveDeployer.addr
        );

        fci.initialize(accts.deployer.addr);
        fci.registerProtocolFacet(UNISWAP_V3_REACTIVE, IFCIProtocolFacet(address(facet)));
        fci.setFacetFci(UNISWAP_V3_REACTIVE, IFeeConcentrationIndex(address(fci)));
        fci.setFacetProtocolStateView(UNISWAP_V3_REACTIVE, IProtocolStateView(v3Pool));
        facet.initialize(
            accts.deployer.addr,
            IProtocolStateView(v3Pool),
            IFeeConcentrationIndex(address(fci)),
            IUnlockCallback(address(callback))
        );

        PoolKey memory poolKey = facet.listen(abi.encode(IUniswapV3Pool(v3Pool)));
        fci.initializeEpochPool(poolKey, UNISWAP_V3_REACTIVE, 86400);

        vm.stopBroadcast();

        // Write state for subsequent phases
        string memory json = string.concat(
            '{"fci":"', vm.toString(address(fci)),
            '","facet":"', vm.toString(address(facet)),
            '","callback":"', vm.toString(address(callback)),
            '","v3Pool":"', vm.toString(v3Pool),
            '","deployer":"', vm.toString(accts.deployer.addr),
            '"}'
        );
        vm.writeFile(STATE_FILE, json);
        console2.log("FCI:      %s", address(fci));
        console2.log("Callback: %s", address(callback));
    }

    // ═══════════════════════════════════════════════════════════════
    //  Phase 2: Mint 2 LPs + Swap (after reactive is deployed)
    // ═══════════════════════════════════════════════════════════════

    function mint() public {
        Accounts memory accts = initAccounts(vm);
        string memory stateJson = vm.readFile(STATE_FILE);
        address v3Pool = vm.parseJsonAddress(stateJson, ".v3Pool");
        V3CallbackRouter router = V3CallbackRouter(DEFAULT_V3_ROUTER);
        IUniswapV3Pool pool = IUniswapV3Pool(v3Pool);

        vm.startBroadcast(accts.deployer.privateKey);
        router.mint(pool, accts.deployer.addr, -60, 60, 1e18);
        router.mint(pool, accts.lpPassive.addr, -60, 60, 2e18);
        router.swap(pool, accts.deployer.addr, true, -1e16, 4295128740);
        vm.stopBroadcast();

        console2.log("Mints (1e18 + 2e18) + swap done");
    }

    // ═══════════════════════════════════════════════════════════════
    //  Phase 3: Burn both LPs (after callbacks from mint/swap arrive)
    // ═══════════════════════════════════════════════════════════════

    function burn() public {
        Accounts memory accts = initAccounts(vm);
        string memory stateJson = vm.readFile(STATE_FILE);
        address v3Pool = vm.parseJsonAddress(stateJson, ".v3Pool");

        vm.broadcast(accts.deployer.privateKey);
        IUniswapV3Pool(v3Pool).burn(-60, 60, 1e18);

        vm.broadcast(accts.lpPassive.privateKey);
        IUniswapV3Pool(v3Pool).burn(-60, 60, 2e18);

        console2.log("Burns (1e18 + 2e18) done");
    }

    // ═══════════════════════════════════════════════════════════════
    //  Phase 4: Verify all FCI metrics (after burn callbacks arrive)
    // ═══════════════════════════════════════════════════════════════

    function verify() public {
        string memory stateJson = vm.readFile(STATE_FILE);
        address fciAddr = vm.parseJsonAddress(stateJson, ".fci");
        address facetAddr = vm.parseJsonAddress(stateJson, ".facet");
        address v3Pool = vm.parseJsonAddress(stateJson, ".v3Pool");
        FeeConcentrationIndexV2 fci = FeeConcentrationIndexV2(fciAddr);
        PoolKey memory poolKey = _buildPoolKey(v3Pool, fciAddr);

        // Query ALL view functions
        (uint128 indexA, uint256 thetaSum, uint256 removedPosCount) = fci.getIndex(poolKey, UNISWAP_V3_REACTIVE);
        uint128 deltaPlus = fci.getDeltaPlus(poolKey, UNISWAP_V3_REACTIVE);
        uint128 atNull = fci.getAtNull(poolKey, UNISWAP_V3_REACTIVE);
        uint256 thetaSumDirect = fci.getThetaSum(poolKey, UNISWAP_V3_REACTIVE);
        uint128 epochDeltaPlus = fci.getDeltaPlusEpoch(poolKey, UNISWAP_V3_REACTIVE);
        address registeredFacet = address(fci.getRegisteredProtocolFacet(UNISWAP_V3_REACTIVE));

        console2.log("removedPosCount: %d", removedPosCount);
        console2.log("deltaPlus:       %s", vm.toString(uint256(deltaPlus)));
        console2.log("epochDeltaPlus:  %s", vm.toString(uint256(epochDeltaPlus)));
        console2.log("indexA:          %s", vm.toString(uint256(indexA)));
        console2.log("atNull:          %s", vm.toString(uint256(atNull)));

        // Assertions
        assertEq(removedPosCount, 2, "removedPosCount must be 2");
        assertGt(uint256(deltaPlus), 0, "deltaPlus must be > 0");
        assertEq(uint256(epochDeltaPlus), uint256(deltaPlus), "epoch must equal cumulative");
        assertEq(thetaSumDirect, thetaSum, "getThetaSum != getIndex().thetaSum");
        assertEq(registeredFacet, facetAddr, "facet mismatch");
        if (indexA > atNull) {
            assertEq(uint256(deltaPlus), uint256(indexA - atNull), "deltaPlus != indexA - atNull");
        }

        console2.log("=== ALL ASSERTIONS PASSED ===");
    }

    // ── Helpers ──

    function _readV3Pool() internal view returns (address) {
        try vm.envAddress("V3_POOL") returns (address pool) { return pool; }
        catch { return DEFAULT_V3_POOL; }
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
