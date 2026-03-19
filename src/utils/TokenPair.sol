// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";

struct TokenPair {
    address token0;
    address token1;
}

/// @notice Deploy 2 fresh MockERC20s, mint `supply` to `mintTo`, return sorted.
///         Does not require Vm — MockERC20.mint() is unrestricted.
function mockPair(uint256 supply, address mintTo) returns (TokenPair memory) {
    MockERC20 a = new MockERC20("Token A", "TKA", 18);
    MockERC20 b = new MockERC20("Token B", "TKB", 18);
    a.mint(mintTo, supply);
    b.mint(mintTo, supply);
    if (address(a) < address(b)) {
        return TokenPair(address(a), address(b));
    }
    return TokenPair(address(b), address(a));
}

/// @notice Wrap two existing addresses into a sorted TokenPair.
function existingPair(address a, address b) pure returns (TokenPair memory) {
    require(a != b, "TokenPair: identical addresses");
    if (a < b) return TokenPair(a, b);
    return TokenPair(b, a);
}
