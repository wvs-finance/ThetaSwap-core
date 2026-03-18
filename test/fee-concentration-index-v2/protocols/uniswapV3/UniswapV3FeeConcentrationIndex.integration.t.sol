// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {Test, console2} from "forge-std/Test.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";

// FCI V2
import {FeeConcentrationIndexV2} from "@fee-concentration-index-v2/FeeConcentrationIndexV2.sol";
import {UniswapV3Facet} from "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol";
import {UniswapV3Callback} from "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol";
import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index-v2/interfaces/IFeeConcentrationIndex.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {IUnlockCallback} from "v4-core/src/interfaces/callback/IUnlockCallback.sol";
import {UNISWAP_V3_REACTIVE} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";

// V3
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {IUniswapV3Factory} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol";
import {V3CallbackRouter} from "@reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol";

// Utils
import {Accounts, initAccounts} from "@utils/Accounts.sol";

/// @title UniswapV3 Reactive FCI V2 — Self-contained integration test
/// @notice Deploys everything fresh, plays Capponi-style JIT scenario, asserts deltaPlus > 0.
///
/// Usage (single command, ~5 min):
///   forge script <this>:UniswapV3FCI_IntegrationScript \
///     --sig "run()" --broadcast --slow --rpc-url sepolia -vv
///
/// Prerequisites:
///   - .env with MNEMONIC, ALCHEMY_API_KEY, REACTIVE_RPC_URL
///   - Deployer funded on Sepolia (~0.5 ETH) + Lasna (~5 lREACT)
///   - V3 pool + mock tokens already deployed (uses V3_POOL env or default)
///
/// The script:
///   1. Deploys FCI V2 + V3 Facet + Callback on Sepolia
///   2. Deploys UniswapV3Reactive on Lasna (via vm.ffi → cast)
///   3. Registers pool + funds reactive
///   4. Phase A: Mints 2 LPs (1:2 capital ratio) + 1 swap
///   5. Sleeps 90s for mint+swap callbacks
///   6. Phase B: Burns both LPs
///   7. Sleeps 90s for burn callbacks
///   8. Asserts: deltaPlus > 0, removedPosCount == 2, epoch deltaPlus > 0
contract UniswapV3FCI_IntegrationScript is Script, Test {
    using PoolIdLibrary for PoolKey;

    // Sepolia constants
    address constant CALLBACK_PROXY = 0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA;
    address constant DEFAULT_V3_POOL = 0xF66da9dd005192ee584a253b024070c9A1A1F4FA;
    address constant DEFAULT_V3_ROUTER = 0x1284E9d71a87276d05abD860bD9990dce9Dd721E;

    function run() public {
        Accounts memory accts = initAccounts(vm);
        string memory lasnaRpc = vm.envString("REACTIVE_RPC_URL");
        address v3Pool = _readV3Pool();

        console2.log("=== Phase 1: Deploy Sepolia (FCI V2 + Facet + Callback) ===");

        vm.startBroadcast(accts.deployer.privateKey);

        FeeConcentrationIndexV2 fci = new FeeConcentrationIndexV2();
        UniswapV3Facet facet = new UniswapV3Facet();
        UniswapV3Callback callback = new UniswapV3Callback{value: 0.1 ether}(
            address(fci), CALLBACK_PROXY, accts.deployer.addr
        );

        // Wire
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

        console2.log("FCI:      %s", address(fci));
        console2.log("Callback: %s", address(callback));

        // ── Phase 2: Deploy Reactive on Lasna (via FFI) ──
        console2.log("=== Phase 2: Deploy Reactive on Lasna ===");

        string memory callbackStr = vm.toString(address(callback));
        string memory pkHex = vm.toString(bytes32(accts.deployer.privateKey));
        string memory v3PoolStr = vm.toString(v3Pool);
        string memory reactiveFile = "broadcast/reactive-addr.txt";

        // Deploy reactive on Lasna + register pool + fund (all in one script)
        string[] memory deployCmd = new string[](6);
        deployCmd[0] = "scripts/deploy-reactive.sh";
        deployCmd[1] = lasnaRpc;
        deployCmd[2] = pkHex;
        deployCmd[3] = callbackStr;
        deployCmd[4] = v3PoolStr;
        deployCmd[5] = reactiveFile;
        vm.ffi(deployCmd);

        // Read reactive address from file
        string memory reactiveStr = vm.readFile(reactiveFile);
        console2.log("Reactive: %s", reactiveStr);

        // ── Phase 3: Mint LPs + Swap ──
        console2.log("=== Phase 3: Mint 2 LPs (1:2 ratio) + Swap ===");

        V3CallbackRouter router = V3CallbackRouter(DEFAULT_V3_ROUTER);
        IUniswapV3Pool pool = IUniswapV3Pool(v3Pool);
        int24 tickLower = -60;
        int24 tickUpper = 60;

        vm.startBroadcast(accts.deployer.privateKey);

        // LP0: deployer, 1e18
        router.mint(pool, accts.deployer.addr, tickLower, tickUpper, 1e18);

        // LP1: lpPassive, 2e18
        router.mint(pool, accts.lpPassive.addr, tickLower, tickUpper, 2e18);

        // Swap (generate fees)
        router.swap(pool, accts.deployer.addr, true, -1e16, 4295128740);

        vm.stopBroadcast();

        console2.log("Mints + swap done. Sleeping 90s for callbacks...");
        vm.sleep(90_000);

        // ── Phase 4: Burn both LPs ──
        console2.log("=== Phase 4: Burn both LPs ===");

        vm.broadcast(accts.deployer.privateKey);
        pool.burn(tickLower, tickUpper, 1e18);

        vm.broadcast(accts.lpPassive.privateKey);
        pool.burn(tickLower, tickUpper, 2e18);

        console2.log("Burns done. Sleeping 90s for callbacks...");
        vm.sleep(90_000);

        // ── Phase 5: Verify ──
        console2.log("=== Phase 5: Verify ===");

        (uint128 indexA, uint256 thetaSum, uint256 removedPosCount) =
            fci.getIndex(poolKey, UNISWAP_V3_REACTIVE);
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

        // ── Assertions: ALL FCI V2 view functions ──

        // removedPosCount == 2
        assertEq(removedPosCount, 2, "removedPosCount must be 2");

        // deltaPlus > 0 (capital asymmetry 1:2 → concentration)
        assertGt(uint256(deltaPlus), 0, "deltaPlus must be > 0");

        // epochDeltaPlus == deltaPlus (within same epoch)
        assertEq(uint256(epochDeltaPlus), uint256(deltaPlus), "epoch must equal cumulative");

        // getThetaSum consistency
        assertEq(thetaSumDirect, thetaSum, "getThetaSum != getIndex().thetaSum");

        // getRegisteredProtocolFacet
        assertEq(registeredFacet, address(facet), "facet mismatch");

        // Cross-getter: deltaPlus == max(0, indexA - atNull)
        if (indexA > atNull) {
            assertEq(uint256(deltaPlus), uint256(indexA - atNull), "deltaPlus != indexA - atNull");
        }

        console2.log("=== ALL ASSERTIONS PASSED ===");
    }

    // ── Helpers ──

    function _readV3Pool() internal view returns (address) {
        try vm.envAddress("V3_POOL") returns (address pool) {
            return pool;
        } catch {
            return DEFAULT_V3_POOL;
        }
    }

}

// ══════════════════════════════════════════════════════════════
//  COMMENTED-OUT STUBS — future fixture-driven tests
//  Uncomment when CLI tool is ready for phased execution.
// ══════════════════════════════════════════════════════════════

// function test_integrationUniswapV3_unit_soleProvider_noSwaps_allDerivedQuantitiesZero() {}
// function test_integrationUniswapV3_unit_soleProvider_oneSwap_deltaPlusMustBeZero() {}
// function test_integrationUniswapV3_unit_twoHomogeneousLps_oneSwap_deltaPlusMustBeZero() {}
// function test_integrationUniswapV3_unit_equalCapitalDurationHeterogeneousLps_twoSwaps_deltaPlusMustBeZero() {}
// function test_integrationUniswapV3_unit_twoDifferentHeterogenousLps_threeSwaps_deltaPlusCapturesCrowdOut() {}
// function test_integrationUniswapV3_fuzz_NlpsEqualCapitalEqualTime(uint8 n) {}
// function test_integrationUniswapV3_fuzz_NlpsDiffCapitalEqualTime(uint8 n) {}
// function test_integrationUniswapV3_fuzz_NlpsDiffCapitalDiffTime(uint8 n) {}
