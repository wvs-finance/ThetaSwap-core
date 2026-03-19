// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IUnlockCallback} from "v4-core/src/interfaces/callback/IUnlockCallback.sol";

/// @title IUnlockCallbackReactiveExt
/// @dev Extends IUnlockCallback with a reactive callback entry point.
/// Called by the Reactive Network callback proxy with the RVM sender ID.
interface IUnlockCallbackReactiveExt is IUnlockCallback {
    function unlockCallbackReactive(address rvmId, bytes calldata data) external;
}
