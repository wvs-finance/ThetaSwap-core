// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {HookMiner} from "lib/uniswap-hooks/lib/v4-periphery/src/utils/HookMiner.sol";
import {FeeConcentrationIndex} from "@fee-concentration-index/FeeConcentrationIndex.sol";
import {Accounts, initAccounts} from "@foundry-script/types/Accounts.sol";
import {
    unichainSepoliaPoolManager,
    ethSepoliaPoolManager,
    SEPOLIA,
    UNICHAIN_SEPOLIA
} from "@foundry-script/utils/Deployments.sol";

contract DeployFCIHookV4Script is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        uint256 chainId = block.chainid;
        address poolManager;
        if (chainId == UNICHAIN_SEPOLIA) {
            poolManager = unichainSepoliaPoolManager();
        } else if (chainId == SEPOLIA) {
            poolManager = ethSepoliaPoolManager();
        } else {
            revert("unsupported chain");
        }

        // FCI implements 5 hook callbacks
        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
                | Hooks.BEFORE_SWAP_FLAG
                | Hooks.AFTER_SWAP_FLAG
                | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
                | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
        );

        bytes memory creationCode = type(FeeConcentrationIndex).creationCode;
        bytes memory constructorArgs = abi.encode(poolManager);

        // Forge broadcast uses the deterministic CREATE2 factory for `new X{salt}()`
        address CREATE2_DEPLOYER = 0x4e59b44847b379578588920cA78FbF26c0B4956C;

        // Mine CREATE2 salt for valid hook address
        (address hookAddress, bytes32 salt) =
            HookMiner.find(CREATE2_DEPLOYER, flags, creationCode, constructorArgs);

        vm.startBroadcast(accounts.deployer.privateKey);
        FeeConcentrationIndex fci = new FeeConcentrationIndex{salt: salt}(poolManager);
        vm.stopBroadcast();

        require(address(fci) == hookAddress, "hook address mismatch");
        console2.log("FCI_HOOK=%s", address(fci));
    }
}
