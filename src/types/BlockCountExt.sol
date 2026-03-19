// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {BlockCount} from "typed-uniswap-v4/types/BlockCountMod.sol";

uint256 constant Q128 = 1 << 128;

/// @notice Theta weight for a position: θ_k = 1/ℓ_k in Q128.
/// @dev Matches the computation inside FeeConcentrationState.addTerm().
function thetaWeight(BlockCount n) pure returns (uint256) {
    return Q128 / n.floorOne();
}
