// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {FacetDeployer} from "../fixtures/FacetDeployer.sol";
import {DeltaPlusStub} from "../fixtures/DeltaPlusStub.sol";
import {CollateralCustodianFacet} from "@fci-token-vault/facets/CollateralCustodianFacet.sol";
import {V4_ADAPTER_SLOT} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {ZeroAmount, DepositCapExceeded} from "@fci-token-vault/storage/CustodianStorage.sol";
import {VaultAlreadySettled} from "@fci-token-vault/storage/OraclePayoffStorage.sol";
import {ReentrancyGuardReentrant} from "@fci-token-vault/modules/dependencies/ReentrancyLib.sol";
import {SafeTransferLib} from "solady/utils/SafeTransferLib.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";

uint256 constant LONG = 0;
uint256 constant SHORT = 1;

/// @dev Malicious ERC20 that re-enters vault.deposit() during transferFrom.
contract ReentrantDepositToken {
    CollateralCustodianFacet public target;
    bool public attacking;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function setTarget(address t) external {
        target = CollateralCustodianFacet(t);
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        allowance[from][msg.sender] -= amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;

        // Re-enter deposit on first call
        if (!attacking) {
            attacking = true;
            target.deposit(1);
        }
        return true;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }
}

/// @dev Malicious ERC20 that re-enters vault.redeemPair() during transfer (outbound).
contract ReentrantRedeemToken {
    CollateralCustodianFacet public target;
    bool public attacking;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function setTarget(address t) external {
        target = CollateralCustodianFacet(t);
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        allowance[from][msg.sender] -= amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        return true;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;

        // Re-enter redeemPair on first outbound transfer
        if (!attacking) {
            attacking = true;
            target.redeemPair(1);
        }
        return true;
    }
}

contract CollateralCustodianFacetTest is Test {
    FacetDeployer vault;
    MockERC20 collateral;
    DeltaPlusStub stub;
    address alice = makeAddr("alice");

    event PairedMint(address indexed depositor, uint256 amount);
    event PairedBurn(address indexed redeemer, uint256 amount);

    function setUp() public {
        vault = new FacetDeployer();
        collateral = new MockERC20("Collateral", "COL", 18);
        stub = new DeltaPlusStub();

        PoolKey memory dummyKey; // zero-initialized
        vault.init(
            address(collateral),
            0, // no cap
            uint160(SqrtPriceLibrary.Q96), // strike = 1.0
            block.timestamp + 30 days,
            V4_ADAPTER_SLOT,
            address(stub),
            dummyKey,
            false
        );

        collateral.mint(alice, 1000e18);
        vm.prank(alice);
        collateral.approve(address(vault), type(uint256).max);
    }

    // ── Test 1: deposit mints pair and transfers USDC ──────────────────

    function test_deposit_mints_pair_and_transfers_usdc() public {
        uint256 amount = 100e18;

        vm.expectEmit(true, false, false, true, address(vault));
        emit PairedMint(alice, amount);

        vm.prank(alice);
        vault.deposit(amount);

        assertEq(vault.erc6909BalanceOf(alice, LONG), amount, "LONG balance");
        assertEq(vault.erc6909BalanceOf(alice, SHORT), amount, "SHORT balance");
        assertEq(collateral.balanceOf(address(vault)), amount, "vault USDC balance");
        assertEq(collateral.balanceOf(alice), 1000e18 - amount, "alice USDC balance");
        assertEq(vault.totalDeposited(), amount, "totalDeposited");
    }

    // ── Test 2: redeemPair burns and transfers USDC ────────────────────

    function test_redeemPair_burns_and_transfers_usdc() public {
        uint256 amount = 100e18;

        vm.prank(alice);
        vault.deposit(amount);

        vm.expectEmit(true, false, false, true, address(vault));
        emit PairedBurn(alice, amount);

        vm.prank(alice);
        vault.redeemPair(amount);

        assertEq(vault.erc6909BalanceOf(alice, LONG), 0, "LONG balance after redeem");
        assertEq(vault.erc6909BalanceOf(alice, SHORT), 0, "SHORT balance after redeem");
        assertEq(collateral.balanceOf(alice), 1000e18, "alice USDC restored");
        assertEq(vault.totalDeposited(), 0, "totalDeposited zero");
    }

    // ── Test 3: previewDeposit returns equal amounts ───────────────────

    function test_previewDeposit_returns_equal_amounts() public view {
        (uint256 longAmt, uint256 shortAmt) = vault.previewDeposit(100e18);
        assertEq(longAmt, 100e18, "long preview");
        assertEq(shortAmt, 100e18, "short preview");
    }

    // ── Test 4: balanceOf reads ERC-6909 ───────────────────────────────

    function test_balanceOf_reads_erc6909() public {
        uint256 amount = 50e18;

        vm.prank(alice);
        vault.deposit(amount);

        assertEq(vault.balanceOf(alice, LONG), amount, "balanceOf LONG");
        assertEq(vault.balanceOf(alice, SHORT), amount, "balanceOf SHORT");
    }

    // ── Test 5: deposit zero reverts ───────────────────────────────────

    function test_deposit_zero_reverts() public {
        vm.prank(alice);
        vm.expectRevert(ZeroAmount.selector);
        vault.deposit(0);
    }

    // ── Test 6: redeemPair zero reverts ────────────────────────────────

    function test_redeemPair_zero_reverts() public {
        vm.prank(alice);
        vm.expectRevert(ZeroAmount.selector);
        vault.redeemPair(0);
    }

    // ── Test 7: deposit exceeds cap reverts ────────────────────────────

    function test_deposit_exceeds_cap_reverts() public {
        // Deploy a separate vault with a 50e18 cap
        FacetDeployer cappedVault = new FacetDeployer();
        PoolKey memory dummyKey;
        cappedVault.init(
            address(collateral),
            uint128(50e18), // cap = 50e18
            uint160(SqrtPriceLibrary.Q96),
            block.timestamp + 30 days,
            V4_ADAPTER_SLOT,
            address(stub),
            dummyKey,
            false
        );

        vm.prank(alice);
        collateral.approve(address(cappedVault), type(uint256).max);

        vm.prank(alice);
        vm.expectRevert(DepositCapExceeded.selector);
        cappedVault.deposit(100e18);
    }

    // ── Test 8: deposit reentrancy reverts ─────────────────────────────

    function test_deposit_reentrancy_reverts() public {
        ReentrantDepositToken malicious = new ReentrantDepositToken();
        malicious.mint(alice, 1000e18);
        malicious.setTarget(address(vault));

        // Deploy vault with malicious token as collateral
        FacetDeployer reentrantVault = new FacetDeployer();
        PoolKey memory dummyKey;
        reentrantVault.init(
            address(malicious),
            0,
            uint160(SqrtPriceLibrary.Q96),
            block.timestamp + 30 days,
            V4_ADAPTER_SLOT,
            address(stub),
            dummyKey,
            false
        );
        malicious.setTarget(address(reentrantVault));

        vm.prank(alice);
        malicious.approve(address(reentrantVault), type(uint256).max);

        // The re-entrant deposit() reverts with ReentrancyGuardReentrant, but
        // Solady's SafeTransferLib catches inner reverts and surfaces TransferFromFailed.
        // This proves the guard fires: without it the re-entrant deposit would succeed.
        vm.prank(alice);
        vm.expectRevert(SafeTransferLib.TransferFromFailed.selector);
        reentrantVault.deposit(10e18);
    }

    // ── Test 9: redeemPair reentrancy reverts ──────────────────────────

    function test_redeemPair_reentrancy_reverts() public {
        ReentrantRedeemToken malicious = new ReentrantRedeemToken();
        malicious.mint(alice, 1000e18);

        // Deploy vault with malicious token as collateral
        FacetDeployer reentrantVault = new FacetDeployer();
        PoolKey memory dummyKey;
        reentrantVault.init(
            address(malicious),
            0,
            uint160(SqrtPriceLibrary.Q96),
            block.timestamp + 30 days,
            V4_ADAPTER_SLOT,
            address(stub),
            dummyKey,
            false
        );
        malicious.setTarget(address(reentrantVault));

        vm.prank(alice);
        malicious.approve(address(reentrantVault), type(uint256).max);

        // First deposit normally
        vm.prank(alice);
        reentrantVault.deposit(100e18);

        // Now redeemPair — the malicious token will re-enter on the outbound transfer.
        // Solady's SafeTransferLib catches the inner ReentrancyGuardReentrant and
        // surfaces TransferFailed. This proves the guard fires.
        vm.prank(alice);
        vm.expectRevert(SafeTransferLib.TransferFailed.selector);
        reentrantVault.redeemPair(50e18);
    }

    // ── Test 10: redeemPair after settle succeeds ──────────────────────

    function test_redeemPair_after_settle_succeeds() public {
        uint256 amount = 100e18;

        vm.prank(alice);
        vault.deposit(amount);

        // Set deltaPlus so poke() updates HWM
        stub.setDeltaPlus(1e18);
        vault.poke();

        // Force HWM above strike so settlement produces a nonzero longPayout
        vault.setHWM(uint160(SqrtPriceLibrary.Q96) * 2);

        // Warp past expiry and settle
        vm.warp(block.timestamp + 31 days);
        vault.settle();

        // redeemPair should still succeed post-settlement
        vm.prank(alice);
        vault.redeemPair(amount);

        assertEq(vault.erc6909BalanceOf(alice, LONG), 0, "LONG after settle+redeem");
        assertEq(vault.erc6909BalanceOf(alice, SHORT), 0, "SHORT after settle+redeem");
        assertEq(collateral.balanceOf(alice), 1000e18, "alice USDC restored after settle");
        assertEq(vault.totalDeposited(), 0, "totalDeposited zero after settle");
    }
}
