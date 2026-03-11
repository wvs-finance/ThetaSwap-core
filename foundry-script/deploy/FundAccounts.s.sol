// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {IAllowanceTransfer} from "permit2/src/interfaces/IAllowanceTransfer.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {Accounts, initAccounts} from "@foundry-script/types/Accounts.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";
import {
    resolveTokens,
    resolveDeployments,
    resolveV3,
    Deployments,
    SEPOLIA,
    UNICHAIN_SEPOLIA
} from "@foundry-script/utils/Deployments.sol";

address constant PERMIT2 = 0x000000000022D473030F116dDEE9F6B43aC78BA3;

contract FundAccountsScript is Script {
    function run() public {
        Accounts memory accounts = initAccounts(vm);
        uint256 chainId = block.chainid;
        (address tokenA, address tokenB) = resolveTokens(chainId);
        uint256 amount = 100_000e18;

        address[3] memory recipients =
            [accounts.lpPassive.addr, accounts.lpSophisticated.addr, accounts.swapper.addr];
        uint256[3] memory pks = [
            accounts.lpPassive.privateKey,
            accounts.lpSophisticated.privateKey,
            accounts.swapper.privateKey
        ];

        // ── Transfer tokens from deployer ──
        vm.startBroadcast(accounts.deployer.privateKey);
        for (uint256 i; i < 3; ++i) {
            MockERC20(tokenA).transfer(recipients[i], amount);
            MockERC20(tokenB).transfer(recipients[i], amount);
        }
        vm.stopBroadcast();

        // ── Approvals (each wallet approves for itself) ──
        // V3: token -> pool directly
        if (chainId == SEPOLIA) {
            (IUniswapV3Pool pool,,) = resolveV3(chainId);
            for (uint256 i; i < 3; ++i) {
                vm.startBroadcast(pks[i]);
                IERC20(tokenA).approve(address(pool), type(uint256).max);
                IERC20(tokenB).approve(address(pool), type(uint256).max);
                vm.stopBroadcast();
            }
        }

        // V4: token -> Permit2 -> PositionManager (on any chain with V4)
        if (chainId == UNICHAIN_SEPOLIA || chainId == SEPOLIA) {
            Deployments memory d = resolveDeployments(chainId, Protocol.UniswapV4);
            for (uint256 i; i < 3; ++i) {
                vm.startBroadcast(pks[i]);
                IERC20(tokenA).approve(PERMIT2, type(uint256).max);
                IERC20(tokenB).approve(PERMIT2, type(uint256).max);
                IAllowanceTransfer(PERMIT2).approve(
                    tokenA, d.positionManager, type(uint160).max, type(uint48).max
                );
                IAllowanceTransfer(PERMIT2).approve(
                    tokenB, d.positionManager, type(uint160).max, type(uint48).max
                );
                vm.stopBroadcast();
            }
        }

        for (uint256 i; i < 3; ++i) {
            console2.log("Funded %s with %d of each token", recipients[i], amount);
        }
    }
}
