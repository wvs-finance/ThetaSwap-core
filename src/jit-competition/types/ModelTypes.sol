// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @title Model Types — Type-Driven Development for JIT Competition Simulation
/// @notice User-defined value types enforce domain correctness at compile time.
/// @dev Following Angstrom X128MathLib pattern: custom types prevent unit confusion.

/// @notice LP liquidity amount (Uniswap V4 uint128 liquidity)
type Liquidity is uint128;

/// @notice Capital denominated in numeraire token
type Capital is uint256;

/// @notice Accumulated fee revenue in numeraire
type FeeRevenue is uint256;
// import {BalanceDelta}
/// This is a BalanceDelta that requires both amounts to be greater than 0



/// @notice Count of LP entries (N_t in Capponi model)
type EntryCount is uint256;

/// @notice Entry index instrument value (pays 1 unit per LP entry)
type IndexValue is uint256;

/// @notice Swap volume in numeraire
type SwapVolume is uint256;

using LiquidityLib for Liquidity global;
using CapitalLib for Capital global;
using FeeRevenueLib for FeeRevenue global;
using EntryCountLib for EntryCount global;
using IndexValueLib for IndexValue global;

library LiquidityLib {
    function unwrap(Liquidity l) internal pure returns (uint128) {
        return Liquidity.unwrap(l);
    }

    function add(Liquidity a, Liquidity b) internal pure returns (Liquidity) {
        return Liquidity.wrap(Liquidity.unwrap(a) + Liquidity.unwrap(b));
    }

    function gt(Liquidity a, Liquidity b) internal pure returns (bool) {
        return Liquidity.unwrap(a) > Liquidity.unwrap(b);
    }

    function isZero(Liquidity l) internal pure returns (bool) {
        return Liquidity.unwrap(l) == 0;
    }
}

library CapitalLib {
    function unwrap(Capital c) internal pure returns (uint256) {
        return Capital.unwrap(c);
    }

    function add(Capital a, Capital b) internal pure returns (Capital) {
        return Capital.wrap(Capital.unwrap(a) + Capital.unwrap(b));
    }

    function sub(Capital a, Capital b) internal pure returns (Capital) {
        return Capital.wrap(Capital.unwrap(a) - Capital.unwrap(b));
    }

    function eq(Capital a, Capital b) internal pure returns (bool) {
        return Capital.unwrap(a) == Capital.unwrap(b);
    }
}

library FeeRevenueLib {
    function unwrap(FeeRevenue f) internal pure returns (uint256) {
        return FeeRevenue.unwrap(f);
    }

    function add(FeeRevenue a, FeeRevenue b) internal pure returns (FeeRevenue) {
        return FeeRevenue.wrap(FeeRevenue.unwrap(a) + FeeRevenue.unwrap(b));
    }
}

library EntryCountLib {
    function unwrap(EntryCount n) internal pure returns (uint256) {
        return EntryCount.unwrap(n);
    }

    function increment(EntryCount n) internal pure returns (EntryCount) {
        return EntryCount.wrap(EntryCount.unwrap(n) + 1);
    }

    function isZero(EntryCount n) internal pure returns (bool) {
        return EntryCount.unwrap(n) == 0;
    }
}

library IndexValueLib {
    function unwrap(IndexValue v) internal pure returns (uint256) {
        return IndexValue.unwrap(v);
    }

    /// @notice Index value = N_t * 1 unit of account per entry
    function fromEntryCount(EntryCount n) internal pure returns (IndexValue) {
        return IndexValue.wrap(EntryCount.unwrap(n));
    }
}
