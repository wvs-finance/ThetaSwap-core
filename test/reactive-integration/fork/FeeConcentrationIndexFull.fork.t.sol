// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {FeeConcentrationIndexBuilderScript} from
    "@foundry-script/reactive-integration/FeeConcentrationIndexBuilder.s.sol";
import {SEPOLIA} from "@foundry-script/utils/Deployments.sol";

// Maps chain ID → foundry.toml [rpc_endpoints] alias.
function rpcAlias(uint256 chainId) pure returns (string memory) {
    if (chainId == SEPOLIA) return "sepolia";
    revert("unknown chainId");
}

abstract contract FeeConcentrationIndexFullForkBase is Test {
    FeeConcentrationIndexBuilderScript fciScript;

    function _chainId() internal pure virtual returns (uint256);

    function setUp() public {
        vm.createSelectFork(vm.rpcUrl(rpcAlias(_chainId())));
        fciScript = new FeeConcentrationIndexBuilderScript();
        fciScript.setUp();
    }

    // ── V4 ──

    function test_buildEquilibriumV4() public {
        fciScript.buildEquilibriumV4();
        fciScript.assertDeltaPlusV4(0);
    }

    function test_buildMildV4() public {
        fciScript.buildMildV4();
    }

    // ── V3 ──

    function test_buildEquilibriumV3() public {
        fciScript.buildEquilibriumV3();
        fciScript.assertDeltaPlusV3(0);
    }

    function test_buildMildV3() public {
        fciScript.buildMildV3();
    }
}

contract SepoliaForkTest is FeeConcentrationIndexFullForkBase {
    function _chainId() internal pure override returns (uint256) { return SEPOLIA; }
}
