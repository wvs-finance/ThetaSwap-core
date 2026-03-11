// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {Accounts, initAccounts} from "@foundry-script/types/Accounts.sol";
import {
    unichainSepoliaPoolManager,
    unichainSepoliaFCIHook,
    ethSepoliaPoolManager,
    ethSepoliaFCIHook,
    resolveTokens,
    SEPOLIA,
    UNICHAIN_SEPOLIA
} from "@foundry-script/utils/Deployments.sol";
import "@foundry-script/utils/Constants.sol";

contract CreatePoolV4Script is Script {
    using PoolIdLibrary for PoolKey;

    function run() public {
        Accounts memory accounts = initAccounts(vm);
        uint256 chainId = block.chainid;

        address poolManager;
        address fciHook;
        if (chainId == UNICHAIN_SEPOLIA) {
            poolManager = unichainSepoliaPoolManager();
            fciHook = unichainSepoliaFCIHook();
        } else if (chainId == SEPOLIA) {
            poolManager = ethSepoliaPoolManager();
            fciHook = ethSepoliaFCIHook();
        } else {
            revert("unsupported chain");
        }
        (address tokenA, address tokenB) = resolveTokens(chainId);

        // Sort for currency0 < currency1
        (address c0, address c1) = tokenA < tokenB
            ? (tokenA, tokenB)
            : (tokenB, tokenA);

        PoolKey memory key = PoolKey({
            currency0: Currency.wrap(c0),
            currency1: Currency.wrap(c1),
            fee: 500,
            tickSpacing: int24(TICK_SPACING),
            hooks: IHooks(fciHook)
        });

        // 1:1 initial price: sqrt(1) * 2^96
        uint160 sqrtPriceX96 = 79228162514264337593543950336;

        vm.startBroadcast(accounts.deployer.privateKey);
        int24 tick = IPoolManager(poolManager).initialize(key, sqrtPriceX96);
        vm.stopBroadcast();

        console2.log("Pool initialized at tick=%d", tick);
        console2.log("PoolId:");
        console2.logBytes32(PoolId.unwrap(key.toId()));
    }
}
