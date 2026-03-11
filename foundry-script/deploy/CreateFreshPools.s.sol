// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {IUniswapV3Factory} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {Accounts, initAccounts} from "@foundry-script/types/Accounts.sol";
import {
    resolveTokens,
    ethSepoliaPoolManager,
    ethSepoliaFCIHook,
    SEPOLIA
} from "@foundry-script/utils/Deployments.sol";
import "@foundry-script/utils/Constants.sol";

// V3 factory on Sepolia
address constant V3_FACTORY = 0x0227628f3F023bb0B980b67D528571c95c6DaC1c;

contract CreateFreshPoolsScript is Script {
    using PoolIdLibrary for PoolKey;

    function run() public {
        Accounts memory accounts = initAccounts(vm);
        (address tokenA, address tokenB) = resolveTokens(SEPOLIA);
        (address t0, address t1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);

        uint160 sqrtPriceX96 = 79228162514264337593543950336; // 1:1

        vm.startBroadcast(accounts.deployer.privateKey);

        // Fresh V3 pool (fee=3000)
        address v3Pool = IUniswapV3Factory(V3_FACTORY).createPool(t0, t1, 3000);
        IUniswapV3Pool(v3Pool).initialize(sqrtPriceX96);

        // Fresh V4 pool (fee=3000, same FCI hook)
        address fciHook = ethSepoliaFCIHook();
        PoolKey memory v4Key = PoolKey({
            currency0: Currency.wrap(t0),
            currency1: Currency.wrap(t1),
            fee: 3000,
            tickSpacing: int24(TICK_SPACING),
            hooks: IHooks(fciHook)
        });
        IPoolManager(ethSepoliaPoolManager()).initialize(v4Key, sqrtPriceX96);

        vm.stopBroadcast();

        console2.log("FRESH_V3_POOL=%s", v3Pool);
        console2.log("FRESH_V4_POOL_ID:");
        console2.logBytes32(PoolId.unwrap(v4Key.toId()));
    }
}
