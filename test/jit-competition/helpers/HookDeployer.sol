// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "forge-std/Test.sol";
import {Hooks} from "@uniswap/v4-core/src/libraries/Hooks.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {JitHook} from "../../src/JitHook.sol";

/// @title HookDeployer -- Deploy JitHook at V4-compatible address
/// @notice V4 requires hook permission flags encoded in address LSBs.
///         BaseHook validates address in constructor, so we use deployCodeTo
///         (same pattern as OpenZeppelin uniswap-hooks tests).
library HookDeployer {
    /// @notice Compute the required address flags for JitHook
    function jitHookFlags() internal pure returns (uint160) {
        return Hooks.BEFORE_SWAP_FLAG
            | Hooks.AFTER_SWAP_FLAG
            | Hooks.BEFORE_ADD_LIQUIDITY_FLAG
            | Hooks.AFTER_ADD_LIQUIDITY_FLAG;
    }

    /// @notice Address with JitHook permission flags set
    function jitHookAddress() internal pure returns (address payable) {
        return payable(address(jitHookFlags()));
    }

    /// @notice Deploy JitHook at the V4-compatible address using deployCodeTo
    /// @dev BaseHook constructor validates address flags, so we use deployCodeTo
    ///      which deploys at a target address (constructor runs with correct address(this))
    function deployJitHook(
        Vm vm,
        IPoolManager poolManager,
        uint128 jitLiquidity,
        int24 tickLower,
        int24 tickUpper
    ) internal returns (JitHook hook) {
        address hookAddr = jitHookAddress();
        vm.deployCodeTo(
            "JitHook.sol:JitHook",
            abi.encode(address(poolManager), jitLiquidity, tickLower, tickUpper),
            hookAddr
        );
        hook = JitHook(hookAddr);
    }
}
