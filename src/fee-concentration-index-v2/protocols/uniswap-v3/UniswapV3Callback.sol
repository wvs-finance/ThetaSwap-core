// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {V3MintData} from "reactive-hooks/types/ReactiveCallbackDataMod.sol";
import {fromUniswapV3PoolToPoolKey} from "./libraries/UniswapV3PoolKeyLib.sol";
import {encodeAfterAddLiquidity, decodeV3MintFromLog} from "./libraries/V3HookDataLib.sol";
import {V3_MINT_SIG} from "./libraries/EventSignatures.sol";

/// @title UniswapV3Callback
/// @dev Receives reactive callbacks from the Reactive Network callback proxy.
/// Decodes V3 event data, builds V4-shaped calldata with hookData,
/// and calls FCI V2's hook functions.
/// Implements IUnlockCallbackReactiveExt without explicit inheritance (SCOP).
contract UniswapV3Callback {
    IHooks immutable fci;

    constructor(address fci_) {
        fci = IHooks(fci_);
    }

    function unlockCallback(bytes calldata) external returns (bytes memory) {}

    function unlockCallbackReactive(address rvmId, bytes calldata data) external {
        // TODO: auth (rvmId check, msg.sender = callback proxy)

        IReactive.LogRecord memory log = abi.decode(data, (IReactive.LogRecord));
        uint256 sig = log.topic_0;

        if (sig == V3_MINT_SIG) {
            _handleMint(decodeV3MintFromLog(log));
        }
        // TODO: V3_SWAP_SIG, V3_BURN_SIG in later flows
    }

    function _handleMint(V3MintData memory data) internal {
        PoolKey memory key = fromUniswapV3PoolToPoolKey(data.pool, fci);

        ModifyLiquidityParams memory params = ModifyLiquidityParams({
            tickLower: data.tickLower,
            tickUpper: data.tickUpper,
            liquidityDelta: int256(uint256(data.liquidity)),
            salt: bytes32(0)
        });

        bytes memory hookData = encodeAfterAddLiquidity(address(data.pool));

        fci.afterAddLiquidity(
            data.owner,
            key,
            params,
            BalanceDelta.wrap(0),
            BalanceDelta.wrap(0),
            hookData
        );
    }
}
