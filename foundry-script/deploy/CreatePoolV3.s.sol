// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {IUniswapV3Factory} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {Accounts, initAccounts} from "@foundry-script/types/Accounts.sol";
import {resolveTokens, SEPOLIA} from "@foundry-script/utils/Deployments.sol";

// Sepolia V3 factory (canonical Uniswap deployment)
address constant V3_FACTORY = 0x0227628f3F023bb0B980b67D528571c95c6DaC1c;

contract CreatePoolV3Script is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        (address tokenA, address tokenB) = resolveTokens(SEPOLIA);

        (address t0, address t1) = tokenA < tokenB
            ? (tokenA, tokenB)
            : (tokenB, tokenA);

        vm.startBroadcast(accounts.deployer.privateKey);
        address pool = IUniswapV3Factory(V3_FACTORY).createPool(t0, t1, 500);
        uint160 sqrtPriceX96 = 79228162514264337593543950336;
        IUniswapV3Pool(pool).initialize(sqrtPriceX96);
        vm.stopBroadcast();

        console2.log("V3_POOL=%s", pool);
    }
}
