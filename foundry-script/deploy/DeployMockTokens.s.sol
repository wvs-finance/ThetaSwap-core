// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {Accounts, initAccounts} from "@foundry-script/types/Accounts.sol";

contract DeployMockTokensScript is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        uint256 supply = 1_000_000e18;

        vm.startBroadcast(accounts.deployer.privateKey);

        MockERC20 tokenA = new MockERC20("ThetaSwap Token A", "TSA", 18);
        MockERC20 tokenB = new MockERC20("ThetaSwap Token B", "TSB", 18);
        tokenA.mint(accounts.deployer.addr, supply);
        tokenB.mint(accounts.deployer.addr, supply);

        vm.stopBroadcast();

        console2.log("TOKEN_A=%s", address(tokenA));
        console2.log("TOKEN_B=%s", address(tokenB));

        if (address(tokenA) > address(tokenB)) {
            console2.log("currency0=TOKEN_B, currency1=TOKEN_A");
        } else {
            console2.log("currency0=TOKEN_A, currency1=TOKEN_B");
        }
    }
}
