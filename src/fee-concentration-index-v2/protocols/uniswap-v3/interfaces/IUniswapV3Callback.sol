// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IHooks} from "v4-core/src/interfaces/IHooks.sol";

interface IUniswapV3Callback {
    // ── Admin ──
    function setFci(address newFci) external;
    function setRvmId(address rvmId_) external;
    function setAuthorized(address caller, bool authorized) external;
    function migrateFunds(address payable to) external;
    function transferOwnership(address newOwner) external;

    // ── Reactive callback ──
    function unlockCallback(bytes calldata data) external returns (bytes memory);
    function unlockCallbackReactive(address rvmSender, bytes calldata data) external;

    // ── Gas reimbursement ──
    function pay(uint256 amount) external;

    // ── Views ──
    function fci() external view returns (IHooks);
    function rvmId() external view returns (address);
    function authorizedCallers(address caller) external view returns (bool);
}
