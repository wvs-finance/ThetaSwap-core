// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {SlotDerivation} from "openzeppelin-contracts/utils/SlotDerivation.sol";
import {IAngstromAuth} from "core/src/interfaces/IAngstromAuth.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {IUniV4} from "core/src/interfaces/IUniV4.sol";
import {PoolConfigStore, PoolConfigStoreLib} from "core/src/libraries/PoolConfigStore.sol";
import {StoreKey, StoreKeyLib} from "core/src/types/StoreKey.sol";
import {ConfigEntry, ConfigEntryLib} from "core/src/types/ConfigEntry.sol";

/// @title AngstromAccumulatorConsumer
/// @notice Read-only Angstrom client. Surfaces accumulator values, block metadata,
///         and pool configuration via extsload. Does NOT write any state.
contract AngstromAccumulatorConsumer {
    // ── Angstrom storage layout constants ──
    uint256 private constant POOL_REWARDS_SLOT = 7;
    uint256 private constant REWARD_GROWTH_SIZE = 16777216;
    uint256 private constant LAST_BLOCK_CONFIG_STORE_SLOT = 3;
    uint256 private constant LAST_BLOCK_BIT_OFFSET = 0;
    uint256 private constant STORE_BIT_OFFSET = 64;

    // ── Immutables ──
    IPoolManager immutable UNI_V4;
    IAngstromAuth immutable ANGSTROM;

    using SlotDerivation for bytes32;
    using IUniV4 for IPoolManager;
    using PoolConfigStoreLib for PoolConfigStore;
    using ConfigEntryLib for ConfigEntry;
    using StoreKeyLib for address;

    constructor(IAngstromAuth _angstrom, IPoolManager _poolManager) {
        ANGSTROM = _angstrom;
        UNI_V4 = _poolManager;
    }

    // ── Accumulator reads ──

    /// @notice Returns the cumulative global reward growth for a pool.
    function globalGrowth(PoolId poolId) external view returns (uint256 _globalGrowth) {
        bytes32 base = bytes32(POOL_REWARDS_SLOT).deriveMapping(PoolId.unwrap(poolId));
        _globalGrowth = ANGSTROM.extsload(uint256(base.offset(REWARD_GROWTH_SIZE)));
    }

    /// @notice Returns the cumulative reward growth inside a tick range.
    function growthInside(
        PoolId poolId,
        int24 tickLower,
        int24 tickUpper
    ) external view returns (uint256) {
        bytes32 base = bytes32(POOL_REWARDS_SLOT).deriveMapping(PoolId.unwrap(poolId));
        int24 currentTick = UNI_V4.getSlot0(poolId).tick();

        uint256 outsideBelow = ANGSTROM.extsload(uint256(base.offset(uint256(uint24(tickLower)))));
        uint256 outsideAbove = ANGSTROM.extsload(uint256(base.offset(uint256(uint24(tickUpper)))));

        unchecked {
            if (currentTick < tickLower) {
                return outsideBelow - outsideAbove;
            } else if (currentTick >= tickUpper) {
                return outsideAbove - outsideBelow;
            } else {
                uint256 global = ANGSTROM.extsload(uint256(base.offset(REWARD_GROWTH_SIZE)));
                return global - outsideBelow - outsideAbove;
            }
        }
    }

    // ── Metadata reads ──

    /// @notice Returns the block number of the most recent Angstrom bundle execution.
    function lastBlockUpdated() external view returns (uint64) {
        return uint64(ANGSTROM.extsload(LAST_BLOCK_CONFIG_STORE_SLOT) >> LAST_BLOCK_BIT_OFFSET);
    }

    /// @notice Returns the SSTORE2 address of Angstrom's current PoolConfigStore.
    function configStore() public view returns (PoolConfigStore) {
        uint256 value = ANGSTROM.extsload(LAST_BLOCK_CONFIG_STORE_SLOT);
        return PoolConfigStore.wrap(address(uint160(value >> STORE_BIT_OFFSET)));
    }

    // ── Pool configuration reads ──

    /// @notice Returns whether at least one Angstrom pool exists for the given token pair.
    /// @param token0 The lower-address token. Must be less than token1.
    /// @param token1 The higher-address token.
    function poolExists(address token0, address token1) external view returns (bool) {
        if (token0 >= token1) return false;

        StoreKey key = StoreKeyLib.keyFromAssetsUnchecked(token0, token1);
        PoolConfigStore store = configStore();
        if (PoolConfigStore.unwrap(store) == address(0)) return false;

        uint256 total = store.totalEntries();
        for (uint256 i; i < total; ++i) {
            ConfigEntry entry = store.getWithDefaultEmpty(key, i);
            if (!entry.isEmpty()) return true;
        }
        return false;
    }

    /// @notice Returns the tick spacing and bundle fee for a specific pool config entry.
    /// @dev Reverts with NoEntry if the index has no matching entry for the token pair.
    /// @param token0 The lower-address token (caller must sort).
    /// @param token1 The higher-address token.
    /// @param index The config entry index to read.
    function getPoolConfig(
        address token0,
        address token1,
        uint256 index
    ) external view returns (int24 tickSpacing, uint24 bundleFee) {
        StoreKey key = StoreKeyLib.keyFromAssetsUnchecked(token0, token1);
        return configStore().get(key, index);
    }
}
