// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IERC165} from "forge-std/interfaces/IERC165.sol";

interface IHookFacet {
    error HookFacet__NotValidHook();
}

interface IFeeConcentrationIndex is IERC165, IHookFacet {
    function getIndex(PoolKey calldata key, bool reactive)
        external
        view
        returns (uint128 indexA, uint256 thetaSum, uint256 posCount);
}
