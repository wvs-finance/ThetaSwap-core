// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {FeeConcentrationIndex} from "@fee-concentration-index/FeeConcentrationIndex.sol";
import {FeeConcentrationIndexV2} from "@fee-concentration-index-v2/FeeConcentrationIndexV2.sol";
import {NativeUniswapV4Facet} from "@fee-concentration-index-v2/protocols/uniswap-v4/NativeUniswapV4Facet.sol";
import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {NATIVE_V4} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";
import {IUnlockCallback} from "v4-core/src/interfaces/callback/IUnlockCallback.sol";

// Pre-calculated: AFTER_ADD_LIQUIDITY | BEFORE_REMOVE_LIQUIDITY | AFTER_REMOVE_LIQUIDITY | BEFORE_SWAP | AFTER_SWAP
// = (1<<10) | (1<<9) | (1<<8) | (1<<7) | (1<<6) = 0x7C0
uint160 constant FCI_HOOK_FLAGS = 0x7C0;

contract DeployFci is Script {
    IPoolManager public immutable poolManager;

    constructor(address poolManager_) {
        poolManager = IPoolManager(poolManager_);
    }

    function run() public returns (address v1Address, address v2Address, address facetAddress) {
        bytes memory v1Args = abi.encode(address(poolManager));

        // ── Deploy V1 ──
        (address v1Addr, bytes32 v1Salt) = HookMiner.find(
            msg.sender, FCI_HOOK_FLAGS,
            type(FeeConcentrationIndex).creationCode, v1Args
        );
        vm.broadcast();
        FeeConcentrationIndex v1 = new FeeConcentrationIndex{salt: v1Salt}(address(poolManager));
        require(address(v1) == v1Addr, "DeployFci: V1 hook address mismatch");

        // ── Deploy V2 (no constructor args) ──
        (address v2Addr, bytes32 v2Salt) = HookMiner.find(
            msg.sender, FCI_HOOK_FLAGS,
            type(FeeConcentrationIndexV2).creationCode, ""
        );
        vm.broadcast();
        FeeConcentrationIndexV2 v2 = new FeeConcentrationIndexV2{salt: v2Salt}();
        require(address(v2) == v2Addr, "DeployFci: V2 hook address mismatch");

        // ── Deploy NativeUniswapV4Facet ──
        vm.broadcast();
        NativeUniswapV4Facet facet = new NativeUniswapV4Facet();

        // ── Wire V2 system ──
        v2.initialize(msg.sender);
        facet.initialize(
            msg.sender,
            IProtocolStateView(address(poolManager)),
            IFeeConcentrationIndex(address(v2)),
            IUnlockCallback(address(0))  // V4 native has no callback
        );
        v2.registerProtocolFacet(NATIVE_V4, IFCIProtocolFacet(address(facet)));

        v1Address = address(v1);
        v2Address = address(v2);
        facetAddress = address(facet);
    }
}
