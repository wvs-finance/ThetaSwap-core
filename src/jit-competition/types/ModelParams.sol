// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Capital} from "./ModelTypes.sol";

/// @title Model Parameters — Capponi JIT Competition Model Configuration
/// @notice Encodes the structural assumptions from NOTES.md as immutable parameters.
/// @dev All parameters set at construction; none can change mid-simulation.



// Added the cosntant types as something of StateInit

struct SimulationConfig {
    /// @notice Initial capital per LP (same for all LPs, both pools)
    Capital initialCapital;
    /// @notice Number of swap rounds to simulate
    uint256 numSwaps;
    /// @notice Swap amount per round (uninformed, mean-reverting)
    uint256 swapAmount;
    /// @notice Initial sqrtPriceX96 for both pools
    uint160 sqrtPriceX96;
}
