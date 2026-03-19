// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Vm} from "forge-std/Vm.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {Accounts} from "./Accounts.sol";

struct Context {
    Vm vm;
    PoolKey v4Pool;
    IUniswapV3Pool v3Pool;
    Accounts accounts;
    address v4PositionManager;
    address v4SwapRouter;
    address v3Router;
    address adapter;
    uint256 chainId;
}
