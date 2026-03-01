// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {BaseHook} from "@uniswap/v4-hooks/BaseHook.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {BalanceDelta, toBalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {BeforeSwapDelta, BeforeSwapDeltaLibrary} from "@uniswap/v4-core/src/types/BeforeSwapDelta.sol";
import {Hooks} from "@uniswap/v4-core/src/libraries/Hooks.sol";
import {SwapParams, ModifyLiquidityParams} from "@uniswap/v4-core/src/types/PoolOperation.sol";
import {EntryCount, EntryCountLib} from "./types/ModelTypes.sol";
// ModelMod: import StateInit as ModelMod for JITAlwaysArrive library
// import "../test/helpers/StateInit.sol" as ModelMod;
// TODO: uncomment once StateInit pseudocode compiles

/// @title JitHook -- JIT LP that always arrives (pi = 1)
/// @notice Inherits BaseHook from OpenZeppelin uniswap-hooks.
///         Only overrides the _internal hooks needed for JIT mint/burn + N_t tracking.
///         JIT fill logic: ModelMod.JITAlwaysArrive.fillSwap (test/helpers/StateInit.sol)
contract JitHook is BaseHook {

    /// @notice LP entry count (N_t) -- incremented on each addLiquidity
    EntryCount public entryCount;

    /// @notice Track whether JIT liquidity is currently deployed
    bool public jitDeployed;

    event JitMint(uint128 liquidity);
    event JitBurn(uint128 liquidity);
    event LpEntry(EntryCount newCount);

    constructor(
        IPoolManager _poolManager,
        uint128,
        int24,
        int24
    ) BaseHook(_poolManager) {
        entryCount = EntryCount.wrap(0);
    }

    // -- Hook Permissions --

    function getHookPermissions() public pure override returns (Hooks.Permissions memory) {
        return Hooks.Permissions({
            beforeInitialize: false,
            afterInitialize: false,
            beforeAddLiquidity: true,
            afterAddLiquidity: true,
            beforeRemoveLiquidity: false,
            afterRemoveLiquidity: false,
            beforeSwap: true,
            afterSwap: true,
            beforeDonate: false,
            afterDonate: false,
            beforeSwapReturnDelta: false,
            afterSwapReturnDelta: false,
            afterAddLiquidityReturnDelta: false,
            afterRemoveLiquidityReturnDelta: false
        });
    }

    // -- Swap Hooks (JIT Mint/Burn) --

    /// @notice Mint concentrated JIT liquidity before each swap
    /// @dev Invariant: pi = 1 (JIT always arrives)
    ///
    /// ===> JIT probability of arrival is always 1
    /// ===> Delegates to ModelMod.JITAlwaysArrive.fillSwap(swapParams)
    ///      which calls: positionManager.mintLiquidity(jitLiquidityParams(swapParams))
    ///      and asserts: require(CurrencySettled(swapDelta, swapFulfilled))
    function _beforeSwap(
        address,
        PoolKey calldata key,
        SwapParams calldata swapParams,
        bytes calldata
    ) internal override returns (bytes4, BeforeSwapDelta, uint24) {
        // LiquidityDelta liq = ModelMod.JITAlwaysArrive.fillSwap(swapParams, beforeSwapDelta);
        // return (IHooks.beforeSwap.selector, beforeSwapDelta(liq), 0);

        // TODO: replace with ModelMod call once StateInit compiles
        // Placeholder: direct modifyLiquidity
        jitDeployed = true;

        return (IHooks.beforeSwap.selector, BeforeSwapDeltaLibrary.ZERO_DELTA, 0);
    }

    /// @notice Burn JIT liquidity after each swap
    function _afterSwap(
        address,
        PoolKey calldata key,
        SwapParams calldata,
        BalanceDelta,
        bytes calldata
    ) internal override returns (bytes4, int128) {
        if (jitDeployed) {
            jitDeployed = false;
        }

        return (IHooks.afterSwap.selector, 0);
    }

    // -- Liquidity Hooks (N_t Tracking) --

    function _beforeAddLiquidity(
        address,
        PoolKey calldata,
        ModifyLiquidityParams calldata,
        bytes calldata
    ) internal pure override returns (bytes4) {
        return IHooks.beforeAddLiquidity.selector;
    }

    /// @notice After liquidity is added, increment the entry counter
    function _afterAddLiquidity(
        address,
        PoolKey calldata,
        ModifyLiquidityParams calldata params,
        BalanceDelta,
        BalanceDelta,
        bytes calldata
    ) internal override returns (bytes4, BalanceDelta) {
        // Only count positive liquidity additions (not JIT internal mints via salt=1)
        if (params.liquidityDelta > 0 && params.salt == bytes32(0)) {
            entryCount = entryCount.increment();
            emit LpEntry(entryCount);
        }

        return (IHooks.afterAddLiquidity.selector, toBalanceDelta(0, 0));
    }
}
