// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {Accounts, initAccounts} from "@foundry-script/types/Accounts.sol";
import {resolveTokens, sepoliaV3CallbackRouter, SEPOLIA} from "@foundry-script/utils/Deployments.sol";

contract ApproveV3RouterScript is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        (address tokenA, address tokenB) = resolveTokens(SEPOLIA);
        address router = sepoliaV3CallbackRouter();

        uint256[3] memory pks = [
            accounts.lpPassive.privateKey,
            accounts.lpSophisticated.privateKey,
            accounts.swapper.privateKey
        ];

        for (uint256 i; i < 3; ++i) {
            vm.startBroadcast(pks[i]);
            IERC20(tokenA).approve(router, type(uint256).max);
            IERC20(tokenB).approve(router, type(uint256).max);
            vm.stopBroadcast();
        }

        console2.log("All 3 accounts approved tokens to V3CallbackRouter");
    }
}
