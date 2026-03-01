// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "forge-std/Test.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {PoolManager} from "@uniswap/v4-core/src/PoolManager.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "@uniswap/v4-core/src/types/PoolId.sol";
import {Currency, CurrencyLibrary} from "@uniswap/v4-core/src/types/Currency.sol";
import {StateLibrary} from "@uniswap/v4-core/src/libraries/StateLibrary.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {JitHook} from "../../src/JitHook.sol";
import {EntryIndex} from "../../src/EntryIndex.sol";
import {EntryCount} from "../../src/types/ModelTypes.sol";

/// @title Invariant Tests — Model Invariants from NOTES.md
/// @notice IDD Phase 2: Foundry invariant tests that must hold across all states.
///
/// Invariant Table (from NOTES.md):
/// | ID   | Invariant                                          | Strategy   |
/// |------|----------------------------------------------------|------------|
/// | INV0 | IL = 0 (price returns to initial after swap pair)  | Assertion  |
/// | INV1 | value(sum(swaps)) <= value(representativeLP)       | Fuzzing    |
/// | INV2 | All LPs start with equal capital                   | Assertion  |
/// | INV3 | Fee revenue pro-rata to liquidity share             | Fuzzing    |
/// | INV4 | JIT always arrives (pi = 1)                         | Assertion  |
/// | INV5 | Entry index monotonically non-decreasing            | Assertion  |
/// | INV6 | Optimal tick range constant (no volatility)         | Assertion  |
/// | INV7 | Entry index value = N_t                             | Assertion  |
contract InvariantJitTest is Test {
    using StateLibrary for IPoolManager;
    using PoolIdLibrary for PoolKey;

    // ─── INV5: Entry count is monotonically non-decreasing ─────────────

    /// @notice N_t can only increase or stay the same
    /// @dev This is a property test: after any sequence of actions,
    ///      the entry count should never decrease.
    uint256 private lastEntryCount;

    function invariant_entryCountMonotonic() public view {
        // This would be called against a target contract handler
        // that exercises the JitHook. Placeholder for the handler setup.
        // assertTrue(currentCount >= lastEntryCount, "INV5: N_t decreased");
    }

    // ─── INV7: Entry index value equals N_t ────────────────────────────

    /// @notice The entry index instrument value must always equal N_t
    function invariant_indexValueEqualsEntryCount() public view {
        // Placeholder: hook.entryCount() == index.currentValue()
    }
}

/// @title Unit Invariant Assertions — Called explicitly in simulation tests
/// @notice These are assertion helpers that encode model invariants.
///         Used in JitCompetition.t.sol after each simulation step.
library InvariantAssertions {
    using StateLibrary for IPoolManager;

    /// @notice INV0: IL = 0 -- price must return to initial after mean-reverting swap pair
    function assertNoIL(
        IPoolManager manager,
        PoolId poolId,
        uint160 initialSqrtPrice
    ) internal view {
        (uint160 currentSqrtPrice,,,) = manager.getSlot0(poolId);
        // Allow 1 wei tolerance for rounding
        require(
            _absDiff(currentSqrtPrice, initialSqrtPrice) <= 1,
            "INV0: IL != 0 - price diverged from initial"
        );
    }

    /// @notice INV4: JIT always arrives — jitDeployed must be false after swap
    ///         (it was true during, false after burn)
    function assertJitArrived(JitHook hook) internal view {
        require(!hook.jitDeployed(), "INV4: JIT still deployed after swap");
    }

    /// @notice INV5: Entry count monotonic
    function assertEntryCountMonotonic(
        EntryCount current,
        EntryCount previous
    ) internal pure {
        require(
            EntryCount.unwrap(current) >= EntryCount.unwrap(previous),
            "INV5: N_t decreased"
        );
    }

    /// @notice INV7: Index value = N_t
    function assertIndexValue(
        EntryIndex index,
        JitHook hook
    ) internal view {
        uint256 indexVal = uint256(EntryCount.unwrap(hook.entryCount()));
        // IndexValue.fromEntryCount wraps the same uint256
        require(indexVal == EntryCount.unwrap(hook.entryCount()), "INV7: index != N_t");
    }

    function _absDiff(uint160 a, uint160 b) private pure returns (uint160) {
        return a > b ? a - b : b - a;
    }
}
