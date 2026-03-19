// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test, console} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";

import {FacetDeployer} from "../fixtures/FacetDeployer.sol";
import {DeltaPlusStub} from "../fixtures/DeltaPlusStub.sol";
import {FCIFixture} from "../fixtures/FCIFixture.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {V4_ADAPTER_SLOT} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";
import {LONG, SHORT} from "@fci-token-vault/modules/CollateralCustodianMod.sol";

// ═══════════════════════════════════════════════════════════════════════
// Layer 3 — Stub-based edge-case payoff tests (no FCI needed)
// ═══════════════════════════════════════════════════════════════════════

contract EdgeCasePayoffsStubTest is Test {
    FacetDeployer vault;
    DeltaPlusStub stub;
    MockERC20 collateral;
    address alice = makeAddr("alice");
    uint256 constant Q96 = SqrtPriceLibrary.Q96;
    uint256 constant LONG_ID = 0;
    uint256 constant SHORT_ID = 1;
    uint256 constant DEPOSIT = 100e18;

    function setUp() public {
        collateral = new MockERC20("USDC", "USDC", 18);
        stub = new DeltaPlusStub();
        vault = new FacetDeployer();
        PoolKey memory dummyKey;
        vault.init(
            address(collateral),
            0,
            uint160(Q96),
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

    /// @dev HWM never poked → stays 0 → LONG payout = 0, SHORT gets everything.
    function test_zero_hwm_settlement() public {
        vm.prank(alice);
        vault.deposit(DEPOSIT);

        // Never poke → HWM stays 0
        vm.warp(block.timestamp + 30 days + 1);
        vault.settle();

        (, , , , uint256 longPayoutPerToken) = vault.getVaultStorage();
        assertEq(longPayoutPerToken, 0, "longPayoutPerToken should be 0 when HWM is 0");

        // Redeem LONG → alice gets 0 USDC
        vm.prank(alice);
        vault.redeemLong(DEPOSIT);

        // Redeem SHORT → alice gets full DEPOSIT USDC
        vm.prank(alice);
        vault.redeemShort(DEPOSIT);

        assertEq(
            collateral.balanceOf(alice),
            1000e18,
            "alice should have original balance restored (1000e18)"
        );
    }

    /// @dev HWM == strike → payoff = 0 (no intrinsic value).
    function test_hwm_at_strike() public {
        vm.prank(alice);
        vault.deposit(DEPOSIT);

        // Force HWM == strike (Q96)
        vault.setHWM(uint160(Q96));

        vm.warp(block.timestamp + 30 days + 1);
        vault.settle();

        (, , , , uint256 longPayoutPerToken) = vault.getVaultStorage();
        assertEq(longPayoutPerToken, 0, "longPayoutPerToken should be 0 when HWM == strike");
    }

    /// @dev Maximum delta-plus → longPayoutPerToken capped at Q96.
    function test_maximum_delta_plus() public {
        vm.prank(alice);
        vault.deposit(DEPOSIT);

        stub.setDeltaPlus(type(uint128).max - 1);
        vault.poke();

        vm.warp(block.timestamp + 30 days + 1);
        vault.settle();

        (, , , , uint256 longPayoutPerToken) = vault.getVaultStorage();
        assertEq(longPayoutPerToken, Q96, "longPayoutPerToken should be capped at Q96");
    }

    /// @dev Poke with zero delta-plus → HWM unchanged (stays 0).
    function test_poke_with_zero_delta_plus() public {
        stub.setDeltaPlus(0);
        vault.poke();

        (, uint160 sqrtPriceHWM, , , ) = vault.getVaultStorage();
        assertEq(uint256(sqrtPriceHWM), 0, "HWM should remain 0 when deltaPlus is 0");
    }
}

// ═══════════════════════════════════════════════════════════════════════
// Layer 3 — FCI-based single-sided solvency test
// ═══════════════════════════════════════════════════════════════════════

contract EdgeCasePayoffsFCITest is FCIFixture {
    address aliceAddr;
    address bobAddr;
    address lpAddr;
    address jitAddr;
    address swapperAddr;

    uint256 constant DEPOSIT_AMOUNT = 0.1e18;
    uint256 constant LP_CAPITAL = 1e18;
    uint256 constant ROUNDS = 3;

    function setUp() public {
        _deployFixture();

        // Create wallets
        Vm.Wallet memory w;
        w = vm.createWallet("alice");
        aliceAddr = w.addr;
        w = vm.createWallet("bob");
        bobAddr = w.addr;
        w = vm.createWallet("lp");
        lpAddr = w.addr;
        w = vm.createWallet("jit");
        jitAddr = w.addr;
        w = vm.createWallet("swapper");
        swapperAddr = w.addr;

        // Setup actors
        _setupLP(lpAddr);
        _setupLP(jitAddr);
        _setupSwapper(swapperAddr);
        seedBalance(aliceAddr);
        seedBalance(bobAddr);
    }

    /// @dev Both alice and bob deposit. After settlement, each redeems only one
    /// side first (alice LONG, bob SHORT), then cross-redeems. Vault stays
    /// solvent throughout and totalDeposited reaches 0 at the end.
    function test_single_sided_solvency() public {
        // ─── 1. Alice and Bob deposit ────────────────────────────
        _depositToVault(aliceAddr, DEPOSIT_AMOUNT);
        _depositToVault(bobAddr, DEPOSIT_AMOUNT);

        // ─── 2. Run 3 JIT rounds ────────────────────────────────
        for (uint256 i; i < ROUNDS; ++i) {
            _deadline = block.timestamp + 1;
            _runJitRound(
                lpAddr, LP_CAPITAL,
                jitAddr, JIT_CAPITAL,
                true,
                int256(TRADE_SIZE)
            );
        }

        // ─── 3. Settle ──────────────────────────────────────────
        _settleVault();

        address collateralAddr = Currency.unwrap(currency1);

        // ─── 4. Alice redeems only LONG ──────────────────────────
        uint256 aliceBalBefore = IERC20(collateralAddr).balanceOf(aliceAddr);
        vm.prank(aliceAddr);
        vault.redeemLong(DEPOSIT_AMOUNT);
        uint256 longPayout = IERC20(collateralAddr).balanceOf(aliceAddr) - aliceBalBefore;

        // ─── 5. Bob redeems only SHORT ───────────────────────────
        uint256 bobBalBefore = IERC20(collateralAddr).balanceOf(bobAddr);
        vm.prank(bobAddr);
        vault.redeemShort(DEPOSIT_AMOUNT);
        uint256 shortPayout = IERC20(collateralAddr).balanceOf(bobAddr) - bobBalBefore;

        // ─── 6. Vault still solvent (still has deposits) ─────────
        assertGt(vault.totalDeposited(), 0, "vault should still have deposits after single-sided redemptions");

        // ─── 7. Cross-redeem: alice SHORT, bob LONG ─────────────
        vm.prank(aliceAddr);
        vault.redeemShort(DEPOSIT_AMOUNT);

        vm.prank(bobAddr);
        vault.redeemLong(DEPOSIT_AMOUNT);

        // ─── 8. totalDeposited == 0 ─────────────────────────────
        assertEq(vault.totalDeposited(), 0, "totalDeposited should be 0 after full cross-redemption");

        console.log("=== SINGLE-SIDED SOLVENCY ===");
        console.log("LONG payout:", longPayout);
        console.log("SHORT payout:", shortPayout);
    }
}
