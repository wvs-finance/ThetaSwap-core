// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {BaseScript} from "./BaseScript.sol";
import {Angstrom} from "src/Angstrom.sol";
import {AngstromAdapter} from "src/periphery/AngstromAdapter.sol";
import {ControllerV1, IAngstromAuth} from "src/periphery/ControllerV1.sol";
import {TimelockController} from "@openzeppelin/contracts/governance/TimelockController.sol";
import {console} from "forge-std/console.sol";

/// @author Will <https://github.com/will-smith11>
contract AngstromAdapterScript is BaseScript {
    function run() public {
        vm.startBroadcast();
        address uniswap = uniswapOnCurrentChain();

        AngstromAdapter adapter = new AngstromAdapter(IPoolManager(uniswap));
        console.log("[INFO] deployed apdater to %s", address(adapter));
    }

    function isChain(string memory name) internal returns (bool) {
        return getChain(name).chainId == block.chainid;
    }

    function uniswapOnCurrentChain() internal returns (address) {
        if (isChain("sepolia")) {
            return 0xE03A1074c86CFeDd5C142C4F04F1a1536e203543;
        }
        if (isChain("mainnet")) {
            return 0x000000000004444c5dc75cB358380D2e3dE08A90;
        }
        revert(string.concat("Unsupported chain: ", getChain(block.chainid).name));
    }
}
