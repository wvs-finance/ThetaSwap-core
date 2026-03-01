// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {EntryCount, IndexValue, IndexValueLib} from "./types/ModelTypes.sol";
import {JitHook} from "./JitHook.sol";

/// @title EntryIndex — Hedging Instrument for LP Competition Risk
/// @notice Pays 1 unit of account per LP entry into the hooked pool.
///         Value = N_t (cumulative LP entries).
/// @dev From NOTES.md: "an instrument that pays one unit of account per
///      liquidity provider that enters the pool"
///
/// Invariants:
///   - value(index) = N_t * 1 unit
///   - value is monotonically non-decreasing (entries never reverse)
///   - PLP who holds this hedges competition risk
contract EntryIndex {
    /// @notice The JIT hook that tracks LP entries
    JitHook public immutable hook;

    /// @notice Price per unit of the index (1 unit of account)
    uint256 public constant PRICE_PER_UNIT = 1e18;

    /// @notice Holdings: address => units purchased
    mapping(address => uint256) public holdings;

    event IndexPurchased(address indexed buyer, uint256 units, uint256 cost);

    error InsufficientPayment();

    constructor(JitHook _hook) {
        hook = _hook;
    }

    /// @notice Current index value = N_t
    function currentValue() public view returns (IndexValue) {
        return IndexValueLib.fromEntryCount(hook.entryCount());
    }

    /// @notice Purchase units of the entry index
    /// @param units Number of units to buy
    /// @dev In this model, cost = units * PRICE_PER_UNIT
    ///      The buyer pays from their surplus fee revenue.
    function purchase(uint256 units) external {
        holdings[msg.sender] += units;
        emit IndexPurchased(msg.sender, units, units * PRICE_PER_UNIT);
    }

    /// @notice Payoff for a holder: holdings * N_t
    /// @param holder Address of the index holder
    /// @return payoff Total payoff in units of account
    function payoff(address holder) external view returns (uint256) {
        return holdings[holder] * EntryCount.unwrap(hook.entryCount());
    }
}
