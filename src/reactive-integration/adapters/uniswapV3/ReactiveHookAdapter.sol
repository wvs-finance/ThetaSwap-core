// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {V3SwapData, V3MintData, V3BurnData} from "reactive-hooks/types/ReactiveCallbackDataMod.sol";
import {requireAuthorized} from "./ReactiveAuthMod.sol";
import {reactiveFciStorage} from "./ReactiveHookAdapterStorageMod.sol";
import {
    FeeConcentrationIndexStorage,
    registerPosition,
    incrementOverlappingRanges
} from "../../../fee-concentration-index/modules/FeeConcentrationIndexStorageMod.sol";
import {TickRange, fromTicks} from "typed-uniswap-v4/types/TickRangeMod.sol";
import {FeeShareRatio, fromFeeGrowth} from "typed-uniswap-v4/types/FeeShareRatioMod.sol";
import {SwapCount} from "typed-uniswap-v4/types/SwapCountMod.sol";
import {BlockCount} from "typed-uniswap-v4/types/BlockCountMod.sol";
import {v3PositionKey} from "reactive-hooks/types/CollectedFeesMod.sol";
import {fromV3Pool} from "reactive-hooks/libraries/PoolKeyExtMod.sol";

// Destination-chain adapter: receives callbacks from Reactive Network callback proxy,
// translates V3 event data into FCI state updates on the reactive storage slot.
// Thin contract shell — all logic in Mod files. SCOP compliant (no is/library/modifier).
// CallbackShell, RvmId, CallbackProxy, CallbackStorage, CallbackProxyRegistryLib
// → now in modules/CallbackMod.sol, types/RvmId.sol, types/CallbackProxy.sol,
//   modules/CallbackStorageMod.sol, libraries/CallbackProxyRegistryLib.sol

contract ReactiveHookAdapter {
    address public rvmId;
    address immutable owner;
    mapping(address => bool) public authorizedCallers;

    event AuthorizedCallerUpdated(address indexed caller, bool authorized);
    event RvmIdUpdated(address indexed oldRvmId, address indexed newRvmId);

    error OnlyOwner();
    error InvalidRvmId();

    constructor(address callbackProxy) payable {
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
        incrementOverlappingRanges($, poolId, tickMin, tickMax);
    }
    function onV3MintTranstionToHook(address rvmSender, V3MintData calldata data) external{
	// note: This is checked for a type on reactive
        requireAuthorized(msg.sender, authorizedCallers);
        if (rvmSender != rvmId) revert InvalidRvmId();
	// ============================================
	PoolKey memory key = fromV3Pool(data.pool, address(this));
        PoolId poolId = PoolIdLibrary.toId(key);


	
    }

    function onV3Mint(address rvmSender, V3MintData calldata data) external {
	// note: This is checked for a type on reactive
        requireAuthorized(msg.sender, authorizedCallers);
        if (rvmSender != rvmId) revert InvalidRvmId();
	// ============================================
        FeeConcentrationIndexStorage storage $ = reactiveFciStorage();

        PoolKey memory key = fromV3Pool(data.pool, address(this));
        PoolId poolId = PoolIdLibrary.toId(key);
        bytes32 posKey = v3PositionKey(data.owner, data.tickLower, data.tickUpper);


	TickRange rk = fromTicks(data.tickLower, data.tickUpper);

	registerPosition($, poolId, rk, posKey, data.tickLower, data.tickUpper, data.liquidity);
        // No feeGrowthInside snapshot needed: reactive callbacks arrive asynchronously,
        // so V3 pool state at callback time ≠ state at event emission time. x_k is
        // computed purely from liquidity shares at burn time (exact for V3 since
        // feeGrowthInside is per-unit-of-liquidity).
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
            // x_k = posLiquidity / totalRangeLiquidity — exact for V3 since
            // feeGrowthInside is per-unit-of-liquidity (all positions in a tick
            // range earn fees proportionally). No V3 pool reads needed; avoids
            // callback timing issue where async delivery makes snapshots stale.
            FeeShareRatio xk = fromFeeGrowth(uint256(data.liquidity), uint256(totalRangeLiq));
            uint256 xSquaredQ128 = xk.square();
            $.fciState[poolId].addTerm(blockLifetime, xSquaredQ128);
        }

        $.fciState[poolId].decrementPos();
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
