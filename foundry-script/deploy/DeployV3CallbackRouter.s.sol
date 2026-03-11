// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {V3CallbackRouter} from
    "@reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol";
import {Accounts, initAccounts} from "@foundry-script/types/Accounts.sol";

contract DeployV3CallbackRouterScript is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        vm.startBroadcast(accounts.deployer.privateKey);
        V3CallbackRouter router = new V3CallbackRouter();
        vm.stopBroadcast();
        console2.log("V3_CALLBACK_ROUTER=%s", address(router));
    }
}
