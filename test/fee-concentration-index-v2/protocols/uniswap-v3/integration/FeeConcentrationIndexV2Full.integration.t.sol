// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {console2} from "forge-std/console2.sol";
import {Accounts, initAccounts} from "@foundry-script/types/Accounts.sol";
import {SEPOLIA, sepoliaV3Pool, resolveTokens} from "@foundry-script/utils/Deployments.sol";
import {FundAccountsScript} from "@foundry-script/deploy/FundAccounts.s.sol";
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

/// @title FCI V2 Full Integration — Uniswap V3 Reactive (Sepolia Live)
/// @notice Deploy:
///   forge script test/.../FeeConcentrationIndexV2Full.integration.t.sol:FeeConcentrationIndexV2FullIntegrationTest \
///     --sig "run()" --broadcast --rpc-url $SEPOLIA_RPC
/// Listen (after reactive on Lasna):
///   forge script test/.../FeeConcentrationIndexV2Full.integration.t.sol:FeeConcentrationIndexV2FullIntegrationTest \
///     --sig "test_listen()" --broadcast --rpc-url $SEPOLIA_RPC
contract FeeConcentrationIndexV2FullIntegrationTest is Test {
    using PoolIdLibrary for PoolKey;

    // ── Sepolia callback proxy ──
    address constant CALLBACK_PROXY = 0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA;
    address constant DEPLOYER_EOA = 0xe69228626E4800578D06a93BaaA595f6634A47C3;

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

        // ── 1. Fund accounts ──
        FundAccountsScript fundScript = new FundAccountsScript();
        fundScript.run();

        // ── 2. Deploy FCI V2 ──
        vm.startBroadcast(accounts.deployer.privateKey);
        fci = new FeeConcentrationIndexV2();
        fci.initialize(accounts.deployer.addr);
        vm.stopBroadcast();
        console2.log("FCI_V2=%s", address(fci));

        // ── 3. Deploy + initialize UniswapV3Facet ──
        vm.startBroadcast(accounts.deployer.privateKey);
        facet = new UniswapV3Facet();
        facet.initialize(
            accounts.deployer.addr,
            IProtocolStateView(address(v3Pool)),
            IFeeConcentrationIndex(address(fci))
        );
        vm.stopBroadcast();
        console2.log("V3_FACET=%s", address(facet));

        // ── 4. Deploy UniswapV3Callback (with auth) ──
        vm.startBroadcast(accounts.deployer.privateKey);
        callback = new UniswapV3Callback(
            address(fci),
            CALLBACK_PROXY,
            DEPLOYER_EOA
        );
        vm.stopBroadcast();
        console2.log("V3_CALLBACK=%s", address(callback));

        // ── 5. Wire: register facet + admin storage on FCI V2 ──
        vm.startBroadcast(accounts.deployer.privateKey);
        fci.registerProtocolFacet(UNISWAP_V3_REACTIVE, IFCIProtocolFacet(address(facet)));
        fci.setFacetFci(UNISWAP_V3_REACTIVE, IFeeConcentrationIndex(address(fci)));
        fci.setFacetProtocolStateView(UNISWAP_V3_REACTIVE, IProtocolStateView(address(v3Pool)));
        vm.stopBroadcast();

        console2.log("");
        console2.log("=== Sepolia deployment complete ===");
        console2.log("Next: deploy UniswapV3Reactive on Lasna:");
        console2.log("  forge create --broadcast UniswapV3Reactive");
        console2.log("  --constructor-args %d %s", SEPOLIA, address(facet));
        console2.log("  --rpc-url https://lasna-rpc.rnk.dev --private-key $KEY --value 0.1ether");
    }

    /// @notice Call after UniswapV3Reactive is deployed on Lasna.
    /// PRE-CONDITIONS:
    /// - UniswapV3Reactive deployed on Lasna
    /// - Set env: LASNA_REACTIVE_ADDRESS=0x...
    /// - Fund callback contract with SepETH for pay()
    function test_listen() public {
        // ── PRE-CONDITIONS ──
        address reactiveAddr = vm.envAddress("LASNA_REACTIVE_ADDRESS");
        require(reactiveAddr != address(0), "LASNA_REACTIVE_ADDRESS not set");
        console2.log("UniswapV3Reactive on Lasna: %s", reactiveAddr);

        // ── LISTEN ──
        vm.startBroadcast(accounts.deployer.privateKey);
        poolKey = facet.listen(abi.encode(v3Pool));
        poolId = poolKey.toId();
        vm.stopBroadcast();

        console2.log("PoolAdded emitted on Sepolia.");
        console2.log("POOL_ID=%s", vm.toString(PoolId.unwrap(poolId)));
        console2.log("ReactVM should auto-subscribe to V3 pool events.");
        console2.log("");
        console2.log("Next: add liquidity to V3 pool, then check FCI state.");
    }

    /// @notice Entry point for forge script --broadcast
    function run() public {
        setUp();
    }

    // TODO: test_addLiquidity — LP mints position on V3 pool
    // TODO: test_queryIndex — query fci.getIndex(poolKey, UNISWAP_V3_REACTIVE) after callback processes
}
