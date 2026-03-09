// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {V3SwapData, V3MintData, V3BurnData} from "../../types/ReactiveCallbackDataMod.sol";
import {requireAuthorized} from "./ReactiveAuthMod.sol";
import {reactiveFciStorage} from "./ReactiveHookAdapterStorageMod.sol";
import {v3AdapterStorage, V3AdapterStorage} from "./ReactiveHookAdapterStorageMod.sol";
import {v3FeeGrowthInside0, v3PositionFeeGrowthLast0} from "../../libraries/V3FeeGrowthReaderMod.sol";
import {
    FeeConcentrationIndexStorage,
    registerPosition, setFeeGrowthBaseline, deleteFeeGrowthBaseline,
    getFeeGrowthBaseline,
    incrementOverlappingRanges
} from "../../../fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {TickRange, fromTicks} from "../../../fee-concentration-index/types/TickRangeMod.sol";
import {FeeShareRatio, fromFeeGrowthDelta} from "../../../fee-concentration-index/types/FeeShareRatioMod.sol";
import {SwapCount} from "../../../fee-concentration-index/types/SwapCountMod.sol";
import {BlockCount} from "../../../fee-concentration-index/types/BlockCountMod.sol";
import {v3PositionKey} from "../../types/CollectedFeesMod.sol";
import {fromV3Pool} from "../../libraries/PoolKeyExtMod.sol";

// Destination-chain adapter: receives callbacks from Reactive Network callback proxy,
// translates V3 event data into FCI state updates on the reactive storage slot.
// Thin contract shell — all logic in Mod files. SCOP compliant (no is/library/modifier).
contract ReactiveHookAdapter {
    address public rvmId;
    address immutable owner;
    mapping(address => bool) public authorizedCallers;

    event AuthorizedCallerUpdated(address indexed caller, bool authorized);
    event RvmIdUpdated(address indexed oldRvmId, address indexed newRvmId);

    error OnlyOwner();
    error InvalidRvmId();

    constructor(address callbackProxy) {
        owner = msg.sender;
        rvmId = msg.sender;
        authorizedCallers[callbackProxy] = true;
    }

    function setRvmId(address rvmId_) external {
        if (msg.sender != owner) revert OnlyOwner();
        address old = rvmId;
        rvmId = rvmId_;
        emit RvmIdUpdated(old, rvmId_);
    }

    function setAuthorized(address caller, bool authorized) external {
        if (msg.sender != owner) revert OnlyOwner();
        authorizedCallers[caller] = authorized;
        emit AuthorizedCallerUpdated(caller, authorized);
    }

    // Reactive Network injects the RVM ID as the first argument of every callback.
    // All on* functions verify msg.sender (callback proxy) and rvmSender (deployer EOA).

    function onV3Swap(address rvmSender, V3SwapData calldata data) external {
        requireAuthorized(msg.sender, authorizedCallers);
        if (rvmSender != rvmId) revert InvalidRvmId();
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolKey memory key = fromV3Pool(data.pool, address(this));
        PoolId poolId = PoolIdLibrary.toId(key);
        int24 tickMin = data.tickBefore < data.tick ? data.tickBefore : data.tick;
        int24 tickMax = data.tickBefore > data.tick ? data.tickBefore : data.tick;
        if (tickMin == tickMax) return;
        incrementOverlappingRanges($, poolId, tickMin, tickMax);
    }

    function onV3Mint(address rvmSender, V3MintData calldata data) external {
        requireAuthorized(msg.sender, authorizedCallers);
        if (rvmSender != rvmId) revert InvalidRvmId();
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolKey memory key = fromV3Pool(data.pool, address(this));
        PoolId poolId = PoolIdLibrary.toId(key);
        bytes32 posKey = v3PositionKey(data.owner, data.tickLower, data.tickUpper);
        TickRange rk = fromTicks(data.tickLower, data.tickUpper);
        registerPosition($, poolId, rk, posKey, data.tickLower, data.tickUpper, data.liquidity);

        // Snapshot feeGrowthInside0 from V3 pool at mint time.
        // This is the baseline for computing the fee delta on burn.
        uint256 feeGrowthNow0 = v3FeeGrowthInside0(data.pool, data.tickLower, data.tickUpper);
        V3AdapterStorage storage v3$ = v3AdapterStorage();
        v3$.feeGrowthSnapshot0[poolId][posKey] = feeGrowthNow0;

        // Also set FCI baseline to current feeGrowthInside (used by fromFeeGrowthDelta)
        setFeeGrowthBaseline($, poolId, posKey, feeGrowthNow0);
        $.fciState[poolId].incrementPos();
    }

    function onV3Burn(address rvmSender, V3BurnData calldata data) external {
        requireAuthorized(msg.sender, authorizedCallers);
        if (rvmSender != rvmId) revert InvalidRvmId();
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolKey memory key = fromV3Pool(data.pool, address(this));
        PoolId poolId = PoolIdLibrary.toId(key);
        bytes32 posKey = v3PositionKey(data.owner, data.tickLower, data.tickUpper);

        (, SwapCount swapLifetime, BlockCount blockLifetime, uint128 totalRangeLiq) =
            $.registries[poolId].deregister(posKey, data.liquidity);

        if (!swapLifetime.isZero()) {
            // Read position's feeGrowthInsideLast0 from V3 pool.
            // V3's burn() updates this to current feeGrowthInside BEFORE
            // de-initializing ticks, so it's valid even after the last LP exits.
            uint256 rangeFeeGrowthNow0 = v3PositionFeeGrowthLast0(
                data.pool, data.owner, data.tickLower, data.tickUpper
            );
            // Position's snapshot at mint time (stored by onV3Mint).
            V3AdapterStorage storage v3$ = v3AdapterStorage();
            uint256 positionFeeLast0 = v3$.feeGrowthSnapshot0[poolId][posKey];
            // FCI baseline (set to same value as snapshot on mint).
            uint256 baseline0 = getFeeGrowthBaseline($, poolId, posKey);

            FeeShareRatio xk = fromFeeGrowthDelta(
                rangeFeeGrowthNow0,
                positionFeeLast0,
                baseline0,
                data.liquidity,
                totalRangeLiq
            );
            uint256 xSquaredQ128 = xk.square();
            $.fciState[poolId].addTerm(blockLifetime, xSquaredQ128);
        }

        // Clean up storage
        delete v3AdapterStorage().feeGrowthSnapshot0[poolId][posKey];
        $.fciState[poolId].decrementPos();
        deleteFeeGrowthBaseline($, poolId, posKey);
    }

    // ── IFeeConcentrationIndex ──

    function getIndex(PoolKey calldata key, bool /* reactive */)
        external
        view
        returns (uint128 indexA, uint256 thetaSum, uint256 removedPosCount)
    {
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolId poolId = PoolIdLibrary.toId(key);
        indexA = $.fciState[poolId].toIndexA();
        thetaSum = $.fciState[poolId].thetaSum;
        removedPosCount = $.fciState[poolId].removedPosCount;
    }

    function getDeltaPlus(PoolKey calldata key, bool /* reactive */)
        external
        view
        returns (uint128 deltaPlus_)
    {
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolId poolId = PoolIdLibrary.toId(key);
        deltaPlus_ = $.fciState[poolId].deltaPlus();
    }

    function getAtNull(PoolKey calldata key, bool /* reactive */)
        external
        view
        returns (uint128 atNull_)
    {
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolId poolId = PoolIdLibrary.toId(key);
        atNull_ = $.fciState[poolId].atNull();
    }

    function getThetaSum(PoolKey calldata key, bool /* reactive */)
        external
        view
        returns (uint256 thetaSum_)
    {
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();
        PoolId poolId = PoolIdLibrary.toId(key);
        thetaSum_ = $.fciState[poolId].thetaSum;
    }

    // ── IPayer (callback proxy gas payment — no `is` per SCOP) ──

    error InsufficientFunds();
    error TransferFailed();

    // Called by the callback proxy to collect gas costs for executing callbacks.
    function pay(uint256 amount) external {
        requireAuthorized(msg.sender, authorizedCallers);
        if (address(this).balance < amount) revert InsufficientFunds();
        if (amount > 0) {
            (bool success,) = payable(msg.sender).call{value: amount}("");
            if (!success) revert TransferFailed();
        }
    }

    // Accept ETH/SepETH funding for callback gas payments.
    receive() external payable {}

    // ── IERC165 ──

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == 0x01ffc9a7; // IERC165
    }
}
