// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;


import {PoolKey} from "v4-core/src/types/PoolKey.sol";

interface IFeeConcentrationIndex{
      function getIndex(PoolKey calldata key) external view returns (uint128 indexA, uint128 indexB);
}