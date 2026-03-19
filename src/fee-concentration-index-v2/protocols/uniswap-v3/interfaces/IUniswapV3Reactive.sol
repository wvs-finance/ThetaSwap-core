// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";

interface IUniswapV3Reactive {
    // ── Admin ──
    function setCallback(address newCallback) external;
    function migrateFunds(address payable to) external;
    function transferOwnership(address newOwner) external;

    // ── Pool management (RN only) ──
    function registerPool(uint256 chainId_, address pool) external;
    function unregisterPool(uint256 chainId_, address pool) external;

    // ── Reactive ──
    function react(IReactive.LogRecord calldata log) external;

    // ── Funding ──
    function fund() external payable;

    // ── Views ──
    function callback() external view returns (address);
}
