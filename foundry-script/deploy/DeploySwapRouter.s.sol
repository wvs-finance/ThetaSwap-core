// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolSwapTest} from "v4-core/src/test/PoolSwapTest.sol";
import {Accounts, initAccounts} from "@foundry-script/types/Accounts.sol";
import {
    ethSepoliaPoolManager,
    unichainSepoliaPoolManager,
    SEPOLIA,
    UNICHAIN_SEPOLIA
} from "@foundry-script/utils/Deployments.sol";

contract DeploySwapRouterScript is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        uint256 chainId = block.chainid;

        address poolManager;
        if (chainId == SEPOLIA) {
            poolManager = ethSepoliaPoolManager();
        } else if (chainId == UNICHAIN_SEPOLIA) {
            poolManager = unichainSepoliaPoolManager();
        } else {
            revert("unsupported chain");
        }

        vm.startBroadcast(accounts.deployer.privateKey);
        PoolSwapTest router = new PoolSwapTest(IPoolManager(poolManager));
        vm.stopBroadcast();

        console2.log("SWAP_ROUTER=%s", address(router));
    }
}
