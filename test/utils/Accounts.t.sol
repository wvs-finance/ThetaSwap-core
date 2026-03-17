// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {Accounts, makeTestAccounts, initAccounts} from "@utils/Accounts.sol";

contract AccountsTest is Test {
    function test_makeTestAccounts_creates4Wallets() public {
        Accounts memory accts = makeTestAccounts(vm);
        assertTrue(accts.deployer.addr != address(0), "deployer zero");
        assertTrue(accts.lpPassive.addr != address(0), "lpPassive zero");
        assertTrue(accts.lpSophisticated.addr != address(0), "lpSophisticated zero");
        assertTrue(accts.swapper.addr != address(0), "swapper zero");
    }

    function test_makeTestAccounts_allDistinct() public {
        Accounts memory accts = makeTestAccounts(vm);
        assertTrue(accts.deployer.addr != accts.lpPassive.addr);
        assertTrue(accts.deployer.addr != accts.lpSophisticated.addr);
        assertTrue(accts.deployer.addr != accts.swapper.addr);
        assertTrue(accts.lpPassive.addr != accts.lpSophisticated.addr);
        assertTrue(accts.lpPassive.addr != accts.swapper.addr);
        assertTrue(accts.lpSophisticated.addr != accts.swapper.addr);
    }

    function test_makeTestAccounts_hasPrivateKeys() public {
        Accounts memory accts = makeTestAccounts(vm);
        assertTrue(accts.deployer.privateKey != 0);
        assertTrue(accts.lpPassive.privateKey != 0);
        assertTrue(accts.lpSophisticated.privateKey != 0);
        assertTrue(accts.swapper.privateKey != 0);
    }

    function test_initAccounts_derivesFromMnemonic() public {
        vm.setEnv("MNEMONIC", "test test test test test test test test test test test junk");
        Accounts memory accts = initAccounts(vm);
        assertTrue(accts.deployer.addr != address(0), "deployer zero");
        assertTrue(accts.lpPassive.addr != address(0), "lpPassive zero");
        assertTrue(accts.lpSophisticated.addr != address(0), "lpSophisticated zero");
        assertTrue(accts.swapper.addr != address(0), "swapper zero");
        assertTrue(accts.deployer.addr != accts.lpPassive.addr);
        assertTrue(accts.deployer.addr != accts.lpSophisticated.addr);
        assertTrue(accts.deployer.addr != accts.swapper.addr);
    }
}
