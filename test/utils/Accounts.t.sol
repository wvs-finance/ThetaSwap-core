// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {TokenPair, mockPair} from "@utils/TokenPair.sol";
import {Mode} from "@utils/Mode.sol";
import {Accounts, makeTestAccounts, initAccounts, seed, approveAll, ApprovalTarget} from "@utils/Accounts.sol";

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

contract SeedTest is Test {
    function test_seed_testMode_fundsAllNonDeployer() public {
        Accounts memory accts = makeTestAccounts(vm);
        TokenPair memory pair = mockPair(1_000_000e18, address(this));
        uint256 amount = 100_000e18;

        seed(vm, accts, pair, amount, Mode.Test);

        assertEq(MockERC20(pair.token0).balanceOf(accts.lpPassive.addr), amount);
        assertEq(MockERC20(pair.token0).balanceOf(accts.lpSophisticated.addr), amount);
        assertEq(MockERC20(pair.token0).balanceOf(accts.swapper.addr), amount);
        assertEq(MockERC20(pair.token1).balanceOf(accts.lpPassive.addr), amount);
        assertEq(MockERC20(pair.token1).balanceOf(accts.lpSophisticated.addr), amount);
        assertEq(MockERC20(pair.token1).balanceOf(accts.swapper.addr), amount);
    }

    function test_seed_testMode_doesNotFundDeployer() public {
        Accounts memory accts = makeTestAccounts(vm);
        TokenPair memory pair = mockPair(1_000_000e18, address(this));

        seed(vm, accts, pair, 100_000e18, Mode.Test);

        assertEq(MockERC20(pair.token0).balanceOf(accts.deployer.addr), 0);
        assertEq(MockERC20(pair.token1).balanceOf(accts.deployer.addr), 0);
    }
}

contract ApproveAllTest is Test {
    function test_approveAll_testMode_approvesCorrectRoles() public {
        Accounts memory accts = makeTestAccounts(vm);
        TokenPair memory pair = mockPair(1_000_000e18, address(this));
        seed(vm, accts, pair, 100_000e18, Mode.Test);

        address router = makeAddr("router");

        ApprovalTarget[] memory targets = new ApprovalTarget[](1);
        targets[0] = ApprovalTarget(router, true, false, true); // lpPassive + swapper, not lpSophisticated

        approveAll(vm, accts, pair, targets, Mode.Test);

        // lpPassive approved
        assertEq(IERC20(pair.token0).allowance(accts.lpPassive.addr, router), type(uint256).max);
        assertEq(IERC20(pair.token1).allowance(accts.lpPassive.addr, router), type(uint256).max);

        // swapper approved
        assertEq(IERC20(pair.token0).allowance(accts.swapper.addr, router), type(uint256).max);
        assertEq(IERC20(pair.token1).allowance(accts.swapper.addr, router), type(uint256).max);

        // lpSophisticated NOT approved
        assertEq(IERC20(pair.token0).allowance(accts.lpSophisticated.addr, router), 0);
        assertEq(IERC20(pair.token1).allowance(accts.lpSophisticated.addr, router), 0);
    }

    function test_approveAll_testMode_multipleTargets() public {
        Accounts memory accts = makeTestAccounts(vm);
        TokenPair memory pair = mockPair(1_000_000e18, address(this));

        address posm = makeAddr("posm");
        address swapRouter = makeAddr("swapRouter");

        ApprovalTarget[] memory targets = new ApprovalTarget[](2);
        targets[0] = ApprovalTarget(posm, true, true, false);       // LPs only
        targets[1] = ApprovalTarget(swapRouter, false, false, true); // swapper only

        approveAll(vm, accts, pair, targets, Mode.Test);

        // LPs approved on posm
        assertEq(IERC20(pair.token0).allowance(accts.lpPassive.addr, posm), type(uint256).max);
        assertEq(IERC20(pair.token0).allowance(accts.lpSophisticated.addr, posm), type(uint256).max);

        // Swapper approved on swapRouter
        assertEq(IERC20(pair.token0).allowance(accts.swapper.addr, swapRouter), type(uint256).max);

        // Swapper NOT approved on posm
        assertEq(IERC20(pair.token0).allowance(accts.swapper.addr, posm), 0);

        // LPs NOT approved on swapRouter
        assertEq(IERC20(pair.token0).allowance(accts.lpPassive.addr, swapRouter), 0);
    }
}
