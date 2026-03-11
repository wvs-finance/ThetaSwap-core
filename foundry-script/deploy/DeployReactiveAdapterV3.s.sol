// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {ReactiveHookAdapter} from
    "@reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol";
import {Accounts, initAccounts} from "@foundry-script/types/Accounts.sol";
import {SEPOLIA} from "@foundry-script/utils/Deployments.sol";

contract DeployReactiveAdapterV3Script is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        address callbackProxy = vm.envAddress("SEPOLIA_CALLBACK_PROXY");

        vm.startBroadcast(accounts.deployer.privateKey);
        ReactiveHookAdapter adapter = new ReactiveHookAdapter(callbackProxy);
        vm.stopBroadcast();

        console2.log("ADAPTER_ADDRESS=%s", address(adapter));
        console2.log("Now deploy ThetaSwapReactive on Reactive Lasna:");
        console2.log("  Pass adapter=%s to ThetaSwapReactive constructor", address(adapter));
        console2.log("  Then call registerPool(chainId, v3Pool) on the Reactive contract");
    }
}
