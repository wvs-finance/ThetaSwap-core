// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

interface IFciTokenVault {
    function deposit(uint256 amount) external;
    function settle() external;
    function redeem(uint256 amount) external;
    function poke() external;
}
