// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {console2} from "forge-std/console2.sol";
import {Accounts, initAccounts} from "@foundry-script/types/Accounts.sol";
import {SEPOLIA, sepoliaV3Pool, resolveTokens} from "@foundry-script/utils/Deployments.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";

import {FeeConcentrationIndexV2} from "@fee-concentration-index-v2/FeeConcentrationIndexV2.sol";
import {UniswapV3Facet} from "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol";
import {UniswapV3Callback} from "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol";
import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {UNISWAP_V3_REACTIVE} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";
import {IUnlockCallback} from "v4-core/src/interfaces/callback/IUnlockCallback.sol";

/// @title FCI V2 Full Integration — Uniswap V3 Reactive (Sepolia Live)
/// @notice Deploy:
///   forge script test/.../FeeConcentrationIndexV2Full.integration.t.sol:FeeConcentrationIndexV2FullIntegrationTest \
///     --sig "run()" --broadcast --rpc-url $SEPOLIA_RPC
/// Listen (after reactive on Lasna):
///   LASNA_REACTIVE_ADDRESS=0x... \
///   forge script test/.../FeeConcentrationIndexV2Full.integration.t.sol:FeeConcentrationIndexV2FullIntegrationTest \
///     --sig "test_listen()" --broadcast --rpc-url $SEPOLIA_RPC
contract FeeConcentrationIndexV2FullIntegrationTest is Test {
    using PoolIdLibrary for PoolKey;

    // ── Sepolia constants ──
    address constant CALLBACK_PROXY = 0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA;

    // ── State ──
    Accounts accounts;
    IUniswapV3Pool v3Pool;

    FeeConcentrationIndexV2 fci;
    UniswapV3Facet facet;
    UniswapV3Callback callback;

    PoolKey poolKey;
    PoolId poolId;

    function setUp() public {
        accounts = initAccounts(vm);
        v3Pool = sepoliaV3Pool();

        console2.log("Deployer: %s", accounts.deployer.addr);
        console2.log("V3 Pool: %s", address(v3Pool));

        // ── 1. Fund LP accounts (10k each — safe amount) ──
        (address tA, address tB) = resolveTokens(block.chainid);
        uint256 fundAmount = 10_000e18;
        vm.startBroadcast(accounts.deployer.privateKey);
        IERC20(tA).transfer(accounts.lpPassive.addr, fundAmount);
        IERC20(tB).transfer(accounts.lpPassive.addr, fundAmount);
        vm.stopBroadcast();
        console2.log("Funded lpPassive with %d of each token", fundAmount);

        // ── 2. Deploy FCI V2 ──
        vm.startBroadcast(accounts.deployer.privateKey);
        fci = new FeeConcentrationIndexV2();
        fci.initialize(accounts.deployer.addr);
        vm.stopBroadcast();
        console2.log("FCI_V2=%s", address(fci));

        // ── 3. Deploy UniswapV3Callback (needs FCI address) ──
        vm.startBroadcast(accounts.deployer.privateKey);
        callback = new UniswapV3Callback(
            address(fci),
            CALLBACK_PROXY,
            accounts.deployer.addr  // rvmId = deployer EOA
        );
        vm.stopBroadcast();
        console2.log("V3_CALLBACK=%s", address(callback));

        // ── 4. Deploy + initialize UniswapV3Facet (needs callback address) ──
        vm.startBroadcast(accounts.deployer.privateKey);
        facet = new UniswapV3Facet();
        facet.initialize(
            accounts.deployer.addr,
            IProtocolStateView(address(v3Pool)),
            IFeeConcentrationIndex(address(fci)),
            IUnlockCallback(address(callback))
        );
        vm.stopBroadcast();
        console2.log("V3_FACET=%s", address(facet));

        // ── 4. Fund callback with SepETH for pay() ──
        vm.startBroadcast(accounts.deployer.privateKey);
        (bool ok,) = address(callback).call{value: 0.05 ether}("");
        require(ok, "Failed to fund callback");
        vm.stopBroadcast();
        console2.log("Callback funded with 0.05 SepETH");

        // ── 5. Wire: register facet + admin storage on FCI V2 ──
        vm.startBroadcast(accounts.deployer.privateKey);
        fci.registerProtocolFacet(UNISWAP_V3_REACTIVE, IFCIProtocolFacet(address(facet)));
        fci.setFacetFci(UNISWAP_V3_REACTIVE, IFeeConcentrationIndex(address(fci)));
        fci.setFacetProtocolStateView(UNISWAP_V3_REACTIVE, IProtocolStateView(address(v3Pool)));
        vm.stopBroadcast();
        console2.log("Facet registered + admin storage set on FCI V2");

        console2.log("");
        console2.log("=== Sepolia deployment complete ===");
        console2.log("Next: deploy UniswapV3Reactive on Lasna:");
        console2.log("  forge create --broadcast \\");
        console2.log("    src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol:UniswapV3Reactive \\");
        console2.log("    --constructor-args %d %s \\", SEPOLIA, address(facet));
        console2.log("    --rpc-url https://lasna-rpc.rnk.dev --private-key $DEPLOYER_PRIVATE_KEY --value 0.1ether");
        console2.log("");
        console2.log("Then set LASNA_REACTIVE_ADDRESS=0x... and run test_listen()");
    }

    /// @notice Entry point for forge script --broadcast
    function run() public {
        setUp();
    }



    /* modifier fetchOrDeployReactive(bool newDeployement){ */
    /* 	if (newDeployment){ vm.ffi(make deploy-reactive  --uni-v3);} */
    /* 	_; */
    /* } */
    /* /// @notice Call after UniswapV3Reactive is deployed on Lasna. */
    /// PRE-CONDITIONS:
    /// - UniswapV3Reactive deployed on Lasna
    /// - Set env: LASNA_REACTIVE_ADDRESS=0x...

    
    /* function test_integration_listenMustTriggerReactiveSubscriptionsAndFunding  (bool newDeployement) public fetchOrDeployReactive(newDeployment){ */
    /*     // ── PRE-CONDITIONS ── */
    /*     address reactiveAddr = vm.envAddress("LASNA_REACTIVE_ADDRESS"); */
    /*     require(reactiveAddr != address(0), "LASNA_REACTIVE_ADDRESS not set"); */
    /*     console2.log("UniswapV3Reactive on Lasna: %s", reactiveAddr); */

    /*     // ── LISTEN ── */
    /*     vm.startBroadcast(accounts.deployer.privateKey); */
    /*     poolKey = facet.listen(abi.encode(v3Pool)); */
    /*     poolId = poolKey.toId(); */
    /*     vm.stopBroadcast(); */

    /* 	bool res =  vm.ffi(make verify --listen --reactive) */
    /* 	    if (res) {emit log_ ... ("Reactive subscribed correctly")}; */

    /* } */

    // TODO: test_addLiquidity — LP mints position on V3 pool
    // TODO: test_queryIndex — query fci.getIndex(poolKey, UNISWAP_V3_REACTIVE) after callback processes

    /// standard tests


}


