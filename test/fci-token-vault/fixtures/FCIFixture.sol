// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {PosmTestSetup} from "@uniswap/v4-periphery/test/shared/PosmTestSetup.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {PositionDescriptor} from "@uniswap/v4-periphery/src/PositionDescriptor.sol";

import {FeeConcentrationIndexHarness} from "../../fee-concentration-index/harness/FeeConcentrationIndexHarness.sol";
import {FCITestHelper} from "../../fee-concentration-index/helpers/FCITestHelper.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {FacetDeployer} from "./FacetDeployer.sol";
import {V4_ADAPTER_SLOT} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";

/// @dev Shared fixture for Layer 2 and Layer 3 vault integration tests.
/// Encapsulates FCI V1 hook + V4 pool + FacetDeployer vault setup.
/// Test contracts inherit this and call _deployFixture() in setUp().
abstract contract FCIFixture is PosmTestSetup, FCITestHelper {
    using PoolIdLibrary for PoolKey;

    FacetDeployer public vault;
    FeeConcentrationIndexHarness public fciHarness;
    PoolId public poolId;

    // ═══════════════════════════════════════════════════════════
    // Config
    // ═══════════════════════════════════════════════════════════

    uint256 constant EPOCH_LENGTH = 1 days;
    uint256 constant VAULT_DURATION = 30 days;
    uint256 constant JIT_CAPITAL = 9e18;
    uint256 constant TRADE_SIZE = 1e15;

    // Block offsets matching Capponi timing model
    uint256 constant JIT_ENTRY_OFFSET = 49;
    uint256 constant PASSIVE_EXIT_OFFSET = 50;

    // LP tick range
    int24 constant LP_TICK_LOWER = -60;
    int24 constant LP_TICK_UPPER = 60;

    // ═══════════════════════════════════════════════════════════
    // Core deployment
    // ═══════════════════════════════════════════════════════════

    /// @dev Deploy all infrastructure: V4 pool manager, FCI hook, pool, and vault.
    /// Call this in setUp() of inheriting test contracts.
    function _deployFixture() internal {
        // 1. Deploy V4 infrastructure (PoolManager, routers, tokens, POSM)
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();
        deployAndApprovePosm(manager);

        // 2. Wire FCITestHelper
        fciLP = makeAddr("defaultLP");
        fciSwapper = address(this);
        fciSwapRouter = swapRouter;

        // 3. Deploy FCI V1 hook via HookMiner
        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
                | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
                | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
                | Hooks.BEFORE_SWAP_FLAG
                | Hooks.AFTER_SWAP_FLAG
        );
        bytes memory constructorArgs = abi.encode(address(lpm));
        (address hookAddress, bytes32 salt) = HookMiner.find(
            address(this),
            flags,
            type(FeeConcentrationIndexHarness).creationCode,
            constructorArgs
        );
        fciHarness = new FeeConcentrationIndexHarness{salt: salt}(lpm);
        require(address(fciHarness) == hookAddress, "hook address mismatch");

        // 4. Init pool
        (key, poolId) = initPool(
            currency0, currency1,
            IHooks(address(fciHarness)),
            3000,
            SQRT_PRICE_1_1
        );

        // 5. Initialize epoch on FCI hook (required for getDeltaPlusEpoch)
        fciHarness.initializeEpochPool(key, EPOCH_LENGTH);

        // 6. Deploy vault (FacetDeployer) and wire to FCI
        vault = new FacetDeployer();
        uint160 strike = SqrtPriceLibrary.fractionToSqrtPriceX96(80, 100);
        vault.init(
            Currency.unwrap(currency1), // collateral = token1
            0,                          // no deposit cap
            strike,
            block.timestamp + VAULT_DURATION,
            V4_ADAPTER_SLOT,
            address(fciHarness),        // real FCI as entry point
            key,                        // real pool key
            false                       // not reactive (V4 native)
        );
    }

    // ═══════════════════════════════════════════════════════════
    // Account setup helpers
    // ═══════════════════════════════════════════════════════════

    /// @dev Fund an LP account and approve POSM for token spending.
    function _setupLP(address account) internal {
        seedBalance(account);
        approvePosmFor(account);
    }

    /// @dev Fund a swapper account and approve the swap router.
    function _setupSwapper(address account) internal {
        seedBalance(account);
        vm.startPrank(account);
        IERC20(Currency.unwrap(currency0)).approve(address(swapRouter), type(uint256).max);
        IERC20(Currency.unwrap(currency1)).approve(address(swapRouter), type(uint256).max);
        vm.stopPrank();
    }

    // ═══════════════════════════════════════════════════════════
    // Vault interaction helpers
    // ═══════════════════════════════════════════════════════════

    /// @dev Deposit collateral (token1) into the vault on behalf of depositor.
    function _depositToVault(address depositor, uint256 amount) internal {
        vm.startPrank(depositor);
        IERC20(Currency.unwrap(currency1)).approve(address(vault), amount);
        vault.deposit(amount);
        vm.stopPrank();
    }

    /// @dev Poke the vault — reads epoch delta-plus from FCI and updates HWM.
    function _pokeVault() internal {
        vault.poke();
    }

    /// @dev Settle the vault after expiry. Warps past expiry then calls settle().
    function _settleVault() internal {
        (,, uint256 expiry,,) = vault.getVaultStorage();
        vm.warp(expiry + 1);
        vault.settle();
    }

    /// @dev Advance block.timestamp to the next epoch boundary.
    function _rollToNextEpoch() internal {
        vm.warp(block.timestamp + EPOCH_LENGTH);
    }

    // ═══════════════════════════════════════════════════════════
    // JIT round helper
    // ═══════════════════════════════════════════════════════════

    /// @dev Execute one complete JIT round using FCITestHelper primitives.
    ///
    /// Timing (Capponi model):
    ///   Block B:   passive LP mints
    ///   Block B+49: JIT LP mints
    ///   Block B+49: swap executes
    ///   Block B+50: JIT LP burns
    ///   Block B+100: passive LP burns (triggers FCI observation)
    ///   poke() → warp to next epoch
    ///
    /// @param lpAddr      Passive LP address
    /// @param lpCapital   Passive LP liquidity amount
    /// @param jitAddr     JIT LP address (ignored if jitCapital == 0)
    /// @param jitCapital  JIT LP liquidity amount (0 = no JIT this round)
    /// @param swapZeroForOne Swap direction
    /// @param swapAmount  Swap amount (exactInput)
    function _runJitRound(
        address lpAddr,
        uint256 lpCapital,
        address jitAddr,
        uint256 jitCapital,
        bool swapZeroForOne,
        int256 swapAmount
    ) internal {
        // Passive LP entry
        uint256 passiveTokenId = _mintPositionAs(
            lpAddr, key, LP_TICK_LOWER, LP_TICK_UPPER, lpCapital
        );

        // Roll to JIT entry block
        vm.roll(block.number + JIT_ENTRY_OFFSET);

        // JIT entry (if applicable)
        uint256 jitTokenId;
        if (jitCapital > 0) {
            jitTokenId = _mintPositionAs(
                jitAddr, key, LP_TICK_LOWER, LP_TICK_UPPER, jitCapital
            );
        }

        // Swap
        _swap(key, swapZeroForOne, swapAmount);

        // JIT exit (next block)
        vm.roll(block.number + 1);
        if (jitCapital > 0) {
            _burnPositionAs(
                jitAddr, key, jitTokenId,
                LP_TICK_LOWER, LP_TICK_UPPER, jitCapital
            );
        }

        // Roll to passive exit
        vm.roll(block.number + PASSIVE_EXIT_OFFSET);

        // Passive LP exit — triggers FCI fee concentration observation
        _burnPositionAs(
            lpAddr, key, passiveTokenId,
            LP_TICK_LOWER, LP_TICK_UPPER, lpCapital
        );

        // Poke vault BEFORE warp (epoch metric reads current epoch's delta-plus)
        _pokeVault();

        // Advance time to next epoch
        _rollToNextEpoch();
    }
}
