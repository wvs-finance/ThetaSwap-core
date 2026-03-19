// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {FeeConcentrationIndexV2} from "@fee-concentration-index-v2/FeeConcentrationIndexV2.sol";
import {NativeUniswapV4Facet} from "@fee-concentration-index-v2/protocols/uniswap-v4/NativeUniswapV4Facet.sol";
import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {IUnlockCallback} from "v4-core/src/interfaces/callback/IUnlockCallback.sol";
import {NATIVE_V4} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";
import {Accounts, initAccounts} from "@utils/Accounts.sol";
import {
    ethSepoliaPoolManager,
    SEPOLIA
} from "@foundry-script/utils/Deployments.sol";

/// @title Deploy FCI V2 Hook for Uniswap V4
/// @dev Two entry points:
///   - deployLocal(poolManager): for test setUp() — no broadcast, returns addresses
///   - run(): for live deployment — uses broadcast + mnemonic
contract DeployFCIV2HookV4Script is Script {

    uint160 constant HOOK_FLAGS = uint160(
        Hooks.AFTER_ADD_LIQUIDITY_FLAG
            | Hooks.BEFORE_SWAP_FLAG
            | Hooks.AFTER_SWAP_FLAG
            | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
            | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
    );

    /// @notice Deploy contracts only (test setUp). No broadcast, no wiring.
    /// @dev Returns uninitialized contracts. Caller must wire:
    ///      fci.initialize(owner), registerProtocolFacet, setFacetFci, etc.
    ///      This avoids msg.sender ownership issues (deployer vs test).
    /// @return fci The deployed FCI V2 at a valid hook address.
    /// @return facet The deployed NativeUniswapV4Facet.
    function deployLocal()
        public
        returns (FeeConcentrationIndexV2 fci, NativeUniswapV4Facet facet)
    {
        (address hookAddress, bytes32 salt) = HookMiner.find(
            address(this),
            HOOK_FLAGS,
            type(FeeConcentrationIndexV2).creationCode,
            ""
        );

        fci = new FeeConcentrationIndexV2{salt: salt}();
        require(address(fci) == hookAddress, "hook address mismatch");

        facet = new NativeUniswapV4Facet();
    }

    /// @notice Live deployment via broadcast.
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        address poolManager = ethSepoliaPoolManager();

        address CREATE2_DEPLOYER = 0x4e59b44847b379578588920cA78FbF26c0B4956C;

        (address hookAddress, bytes32 salt) = HookMiner.find(
            CREATE2_DEPLOYER,
            HOOK_FLAGS,
            type(FeeConcentrationIndexV2).creationCode,
            ""
        );

        vm.startBroadcast(accounts.deployer.privateKey);

        FeeConcentrationIndexV2 fci = new FeeConcentrationIndexV2{salt: salt}();
        require(address(fci) == hookAddress, "hook address mismatch");

        NativeUniswapV4Facet facet = new NativeUniswapV4Facet();

        fci.initialize(accounts.deployer.addr);
        fci.registerProtocolFacet(NATIVE_V4, IFCIProtocolFacet(address(facet)));
        fci.setFacetFci(NATIVE_V4, IFeeConcentrationIndex(address(fci)));
        fci.setFacetProtocolStateView(NATIVE_V4, IProtocolStateView(poolManager));

        facet.initialize(
            accounts.deployer.addr,
            IProtocolStateView(poolManager),
            IFeeConcentrationIndex(address(fci)),
            IUnlockCallback(address(0))
        );

        vm.stopBroadcast();

        console2.log("FCI_V2_HOOK=%s", address(fci));
        console2.log("V4_FACET=%s", address(facet));
    }
}
