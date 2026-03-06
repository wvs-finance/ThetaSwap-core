// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";

import {V3SwapData, V3MintData, V3BurnData} from "../../types/ReactiveCallbackDataMod.sol";
import {requireAuthorized} from "./ReactiveAuthMod.sol";
import {reactiveFciStorage} from "./ReactiveHookAdapterStorageMod.sol";
import {
    FeeConcentrationIndexStorage,
    registerPosition, setFeeGrowthBaseline, deleteFeeGrowthBaseline,
    incrementOverlappingRanges
} from "../../../fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {TickRange, fromTicks} from "../../../fee-concentration-index/types/TickRangeMod.sol";
import {FeeShareRatio} from "../../../fee-concentration-index/types/FeeShareRatioMod.sol";
import {SwapCount} from "../../../fee-concentration-index/types/SwapCountMod.sol";
import {BlockCount} from "../../../fee-concentration-index/types/BlockCountMod.sol";
import {SyntheticFeeGrowth, fromBurnAmount, toFeeShareRatio} from "../../types/SyntheticFeeGrowthMod.sol";
import {v3PositionKey} from "../../types/CollectedFeesMod.sol";
import {fromV3Pool} from "../../libraries/PoolKeyExtMod.sol";

// Destination-chain adapter: receives callbacks from Reactive Network callback proxy,
// translates V3 event data into FCI state updates on the reactive storage slot.
// Thin contract shell — all logic in Mod files. SCOP compliant (no is/library/modifier).
contract ReactiveHookAdapter {
    address immutable rvmId;
    address immutable owner;
    mapping(address => bool) public authorizedCallers;

    event AuthorizedCallerUpdated(address indexed caller, bool authorized);

    error OnlyOwner();

    constructor(address callbackProxy) {
        owner = msg.sender;
        rvmId = msg.sender;
        authorizedCallers[callbackProxy] = true;
    }

    function setAuthorized(address caller, bool authorized) external {
        if (msg.sender != owner) revert OnlyOwner();
        authorizedCallers[caller] = authorized;
        emit AuthorizedCallerUpdated(caller, authorized);
    }

    function onV3Swap(V3SwapData calldata data) external {
        requireAuthorized(msg.sender, authorizedCallers);
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolKey memory key = fromV3Pool(data.pool, address(this));
        PoolId poolId = PoolIdLibrary.toId(key);
        incrementOverlappingRanges($, poolId, data.tick, data.tick);
    }

    function onV3Mint(V3MintData calldata data) external {
        requireAuthorized(msg.sender, authorizedCallers);
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolKey memory key = fromV3Pool(data.pool, address(this));
        PoolId poolId = PoolIdLibrary.toId(key);
        bytes32 posKey = v3PositionKey(data.owner, data.tickLower, data.tickUpper);
        TickRange rk = fromTicks(data.tickLower, data.tickUpper);
        registerPosition($, poolId, rk, posKey, data.tickLower, data.tickUpper, data.liquidity);
        setFeeGrowthBaseline($, poolId, posKey, 0);
        $.fciState[poolId].incrementPos();
    }

    function onV3Burn(V3BurnData calldata data, uint256 fee0, uint256 fee1) external {
        requireAuthorized(msg.sender, authorizedCallers);
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolKey memory key = fromV3Pool(data.pool, address(this));
        PoolId poolId = PoolIdLibrary.toId(key);
        bytes32 posKey = v3PositionKey(data.owner, data.tickLower, data.tickUpper);

        (, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) =
            $.registries[poolId].deregister(posKey, data.liquidity);

        if (!swapLifetime.isZero()) {
            SyntheticFeeGrowth posDelta = fromBurnAmount(fee0, data.liquidity);
            SyntheticFeeGrowth rangeDelta = fromBurnAmount(fee0, totalRangeLiq);
            FeeShareRatio xk = toFeeShareRatio(posDelta, rangeDelta);
            uint256 xSquaredQ128 = xk.square();
            $.fciState[poolId].addTerm(blockLifetime, xSquaredQ128);
        }

        $.fciState[poolId].decrementPos();
        deleteFeeGrowthBaseline($, poolId, posKey);
    }

    function getIndex(PoolKey calldata key) external view returns (uint128 indexA, uint256 thetaSum, uint256 posCount) {
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolId poolId = PoolIdLibrary.toId(key);
        indexA = $.fciState[poolId].toIndexA();
        thetaSum = $.fciState[poolId].thetaSum;
        posCount = $.fciState[poolId].posCount;
    }
}
