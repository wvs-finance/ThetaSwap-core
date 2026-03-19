// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @dev Test double for unlockCallbackReactive. Stores received data for assertions.
contract MockCallbackReceiver {
    event CallbackReceived(bytes data);

    bytes public lastData;
    address public lastRvmSender;
    uint256 public callbackCount;

    function unlockCallbackReactive(address rvmSender, bytes calldata data) external {
        lastRvmSender = rvmSender;
        lastData = data;
        callbackCount++;
        emit CallbackReceived(data);
    }
}
