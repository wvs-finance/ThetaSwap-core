// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Vm} from "forge-std/Vm.sol";

string constant DEFAULT_DERIVATION_PATH = "m/44'/60'/0'/0/";

struct Accounts {
    Vm.Wallet deployer;
    Vm.Wallet lpPassive;
    Vm.Wallet lpSophisticated;
    Vm.Wallet swapper;
}

// Derive 4 wallets from the MNEMONIC env var at HD indices 0-3.
// These are real accounts — fund them on the target chain before broadcasting.
function initAccounts(Vm vm) returns (Accounts memory) {
    string memory mnemonic = vm.envString("MNEMONIC");
    return Accounts({
        deployer: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 0), "deployer"),
        lpPassive: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 1), "lpPassive"),
        lpSophisticated: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 2), "lpSophisticated"),
        swapper: vm.createWallet(vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, 3), "swapper")
    });
}
