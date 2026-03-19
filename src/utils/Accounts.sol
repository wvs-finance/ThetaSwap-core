// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Vm} from "forge-std/Vm.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {TokenPair} from "./TokenPair.sol";
import {Mode} from "./Mode.sol";

struct Accounts {
    Vm.Wallet deployer;
    Vm.Wallet lpPassive;
    Vm.Wallet lpSophisticated;
    Vm.Wallet swapper;
    Vm.Wallet reactiveDeployer;  // HD index 4 — dedicated EOA for Lasna reactive deploys (clean ReactVM)
}

struct ApprovalTarget {
    address spender;
    bool lpPassive;
    bool lpSophisticated;
    bool swapper;
}

string constant DEFAULT_DERIVATION_PATH = "m/44'/60'/0'/0/";

/// @notice Create test accounts using vm.createWallet with labels.
function makeTestAccounts(Vm vm) returns (Accounts memory) {
    return Accounts({
        deployer: vm.createWallet("deployer"),
        lpPassive: vm.createWallet("lpPassive"),
        lpSophisticated: vm.createWallet("lpSophisticated"),
        swapper: vm.createWallet("swapper"),
        reactiveDeployer: vm.createWallet("reactiveDeployer")
    });
}

/// @notice Create script accounts from MNEMONIC env var (HD indices 0-3).
function initAccounts(Vm vm) returns (Accounts memory) {
    string memory mnemonic = vm.envString("MNEMONIC");
    return Accounts({
        deployer: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 0), "deployer"),
        lpPassive: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 1), "lpPassive"),
        lpSophisticated: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 2), "lpSophisticated"),
        swapper: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 3), "swapper"),
        reactiveDeployer: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 4), "reactiveDeployer")
    });
}

/// @notice Fund all non-deployer accounts with `amount` of both tokens.
///         Mode.Test  → MockERC20(token).mint(account, amount).
///         Mode.Script → vm.startBroadcast(deployer.pk) + IERC20.transfer().
///         Calling seed in Mode.Test on a TokenPair from existingPair will revert.
function seed(
    Vm vm,
    Accounts memory accts,
    TokenPair memory pair,
    uint256 amount,
    Mode mode
) {
    address[3] memory recipients = [accts.lpPassive.addr, accts.lpSophisticated.addr, accts.swapper.addr];

    if (mode == Mode.Test) {
        for (uint256 i; i < 3; ++i) {
            MockERC20(pair.token0).mint(recipients[i], amount);
            MockERC20(pair.token1).mint(recipients[i], amount);
        }
    } else {
        vm.startBroadcast(accts.deployer.privateKey);
        for (uint256 i; i < 3; ++i) {
            IERC20(pair.token0).transfer(recipients[i], amount);
            IERC20(pair.token1).transfer(recipients[i], amount);
        }
        vm.stopBroadcast();
    }
}

/// @notice Each account approves pair tokens on its assigned spenders.
///         Mode.Test  → vm.startPrank/stopPrank per role.
///         Mode.Script → vm.startBroadcast/stopBroadcast per role. Never nested.
function approveAll(
    Vm vm,
    Accounts memory accts,
    TokenPair memory pair,
    ApprovalTarget[] memory targets,
    Mode mode
) {
    for (uint256 i; i < targets.length; ++i) {
        ApprovalTarget memory t = targets[i];

        if (t.lpPassive) _approveFor(vm, accts.lpPassive, pair, t.spender, mode);
        if (t.lpSophisticated) _approveFor(vm, accts.lpSophisticated, pair, t.spender, mode);
        if (t.swapper) _approveFor(vm, accts.swapper, pair, t.spender, mode);
    }
}

/// @dev Internal helper — not part of the public API.
function _approveFor(
    Vm vm,
    Vm.Wallet memory wallet,
    TokenPair memory pair,
    address spender,
    Mode mode
) {
    if (mode == Mode.Test) {
        vm.startPrank(wallet.addr);
    } else {
        vm.startBroadcast(wallet.privateKey);
    }

    IERC20(pair.token0).approve(spender, type(uint256).max);
    IERC20(pair.token1).approve(spender, type(uint256).max);

    if (mode == Mode.Test) {
        vm.stopPrank();
    } else {
        vm.stopBroadcast();
    }
}
