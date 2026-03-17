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
        swapper: vm.createWallet("swapper")
    });
}

/// @notice Create script accounts from MNEMONIC env var (HD indices 0-3).
function initAccounts(Vm vm) returns (Accounts memory) {
    string memory mnemonic = vm.envString("MNEMONIC");
    return Accounts({
        deployer: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 0), "deployer"),
        lpPassive: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 1), "lpPassive"),
        lpSophisticated: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 2), "lpSophisticated"),
        swapper: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 3), "swapper")
    });
}
