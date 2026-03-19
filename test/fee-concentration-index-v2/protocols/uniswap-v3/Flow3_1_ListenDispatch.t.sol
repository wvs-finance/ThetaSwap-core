// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {ISubscriptionService} from "reactive-lib/interfaces/ISubscriptionService.sol";

// EDT + dispatch
import {handlePoolAdded, dispatchEvent} from
    "@fee-concentration-index-v2/modules/ReactiveDispatchMod.sol";
import {
    _originRegistryStorage, getOriginExists, OriginRegistryStorage
} from "reactive-hooks/modules/OriginRegistryStorageMod.sol";
import {
    _eventDispatchStorage, getBindingCountByOrigin, EventDispatchStorage
} from "reactive-hooks/modules/EventDispatchStorageMod.sol";

// Libs
import {encodeV3PoolAddedData} from
    "@fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PoolAddedLib.sol";
import {V3_SWAP_SIG, V3_MINT_SIG, V3_BURN_SIG} from
    "@fee-concentration-index-v2/protocols/uniswap-v3/libraries/EventSignatures.sol";
import {POOL_ADDED_SIG} from "@fee-concentration-index-v2/libraries/PoolAddedSig.sol";
import {UNISWAP_V3_REACTIVE} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";
import {OriginEndpoint, originId} from "reactive-hooks/types/OriginEndpoint.sol";

// Test mock
import {MockCallbackReceiver} from "./mocks/MockCallbackReceiver.sol";

contract Flow3_1_ListenDispatch is Test {
    MockCallbackReceiver receiver;
    MockSubscriptionService mockService;

    address constant MOCK_POOL = address(0xBEEF);
    uint256 constant ORIGIN_CHAIN = 1;

    function setUp() public {
        receiver = new MockCallbackReceiver();
        mockService = new MockSubscriptionService();

        // Initialize ReactVM storage so requireVM() passes.
        // ReactVMStorage.reactVm is at slot keccak256("reactive.reactVM"), offset 0.
        // ReactVm is a bool UDVT — true means "is ReactVM instance".
        bytes32 reactVmSlot = keccak256("reactive.reactVM");
        vm.store(address(this), reactVmSlot, bytes32(uint256(1)));
    }

    // ── Phase 1: PoolAdded → EDT registration ──

    function test_handlePoolAdded_registers_3_origins_1_callback_3_bindings() public {
        IReactive.LogRecord memory log = _buildPoolAddedLog(
            ORIGIN_CHAIN, MOCK_POOL, address(receiver)
        );

        handlePoolAdded(log, ISubscriptionService(payable(address(mockService))));

        _assertOriginExists(ORIGIN_CHAIN, MOCK_POOL, V3_SWAP_SIG);
        _assertOriginExists(ORIGIN_CHAIN, MOCK_POOL, V3_MINT_SIG);
        _assertOriginExists(ORIGIN_CHAIN, MOCK_POOL, V3_BURN_SIG);

        _assertBindingCount(ORIGIN_CHAIN, MOCK_POOL, V3_SWAP_SIG, 1);
        _assertBindingCount(ORIGIN_CHAIN, MOCK_POOL, V3_MINT_SIG, 1);
        _assertBindingCount(ORIGIN_CHAIN, MOCK_POOL, V3_BURN_SIG, 1);
    }

    // ── Phase 2: V3 event → dispatch → Callback event emitted ──

    function test_dispatchEvent_swap_emits_callback() public {
        _registerPool();

        IReactive.LogRecord memory log = _buildV3SwapLog(ORIGIN_CHAIN, MOCK_POOL);

        vm.expectEmit(true, true, false, false);
        emit IReactive.Callback(ORIGIN_CHAIN, address(receiver), 0, "");

        dispatchEvent(log);
    }

    function test_dispatchEvent_mint_emits_callback() public {
        _registerPool();

        IReactive.LogRecord memory log = _buildV3MintLog(ORIGIN_CHAIN, MOCK_POOL);

        vm.expectEmit(true, true, false, false);
        emit IReactive.Callback(ORIGIN_CHAIN, address(receiver), 0, "");

        dispatchEvent(log);
    }

    function test_dispatchEvent_burn_emits_callback() public {
        _registerPool();

        IReactive.LogRecord memory log = _buildV3BurnLog(ORIGIN_CHAIN, MOCK_POOL);

        vm.expectEmit(true, true, false, false);
        emit IReactive.Callback(ORIGIN_CHAIN, address(receiver), 0, "");

        dispatchEvent(log);
    }

    // ── Helpers ──

    function _registerPool() internal {
        IReactive.LogRecord memory log = _buildPoolAddedLog(
            ORIGIN_CHAIN, MOCK_POOL, address(receiver)
        );
        handlePoolAdded(log, ISubscriptionService(payable(address(mockService))));
    }

    function _buildPoolAddedLog(
        uint256 chainId,
        address pool,
        address callbackTarget
    ) internal pure returns (IReactive.LogRecord memory) {
        bytes memory poolData = encodeV3PoolAddedData(chainId, pool, pool);
        bytes memory logData = abi.encode(UNISWAP_V3_REACTIVE, poolData);

        return IReactive.LogRecord({
            chain_id: chainId,
            _contract: address(0),
            topic_0: POOL_ADDED_SIG,
            topic_1: uint256(uint160(address(0))),
            topic_2: uint256(uint160(callbackTarget)),
            topic_3: 0,
            data: logData,
            block_number: 0,
            op_code: 0,
            block_hash: 0,
            tx_hash: 0,
            log_index: 0
        });
    }

    function _buildV3SwapLog(
        uint256 chainId,
        address pool
    ) internal pure returns (IReactive.LogRecord memory) {
        int24 tick = 100;
        bytes memory swapData = abi.encode(
            int256(1e18),
            int256(-1e18),
            uint160(1 << 96),
            uint128(1e18),
            tick
        );

        return IReactive.LogRecord({
            chain_id: chainId,
            _contract: pool,
            topic_0: V3_SWAP_SIG,
            topic_1: uint256(uint160(address(0x1))),
            topic_2: uint256(uint160(address(0x2))),
            topic_3: 0,
            data: swapData,
            block_number: 1,
            op_code: 0,
            block_hash: 0,
            tx_hash: 0,
            log_index: 0
        });
    }

    function _buildV3MintLog(
        uint256 chainId,
        address pool
    ) internal pure returns (IReactive.LogRecord memory) {
        bytes memory mintData = abi.encode(
            address(0x1),
            uint128(1e18),
            uint256(1e18),
            uint256(1e18)
        );

        return IReactive.LogRecord({
            chain_id: chainId,
            _contract: pool,
            topic_0: V3_MINT_SIG,
            topic_1: uint256(uint160(address(0x3))),
            topic_2: uint256(uint24(int24(-100))),
            topic_3: uint256(uint24(int24(100))),
            data: mintData,
            block_number: 2,
            op_code: 0,
            block_hash: 0,
            tx_hash: 0,
            log_index: 0
        });
    }

    function _buildV3BurnLog(
        uint256 chainId,
        address pool
    ) internal pure returns (IReactive.LogRecord memory) {
        bytes memory burnData = abi.encode(
            uint128(1e18),
            uint256(1e18),
            uint256(1e18)
        );

        return IReactive.LogRecord({
            chain_id: chainId,
            _contract: pool,
            topic_0: V3_BURN_SIG,
            topic_1: uint256(uint160(address(0x3))),
            topic_2: uint256(uint24(int24(-100))),
            topic_3: uint256(uint24(int24(100))),
            data: burnData,
            block_number: 3,
            op_code: 0,
            block_hash: 0,
            tx_hash: 0,
            log_index: 0
        });
    }

    function _assertOriginExists(uint256 chainId, address pool, uint256 sig) internal view {
        OriginEndpoint memory o = OriginEndpoint({
            chainId: uint32(chainId),
            emitter: pool,
            eventSig: bytes32(sig)
        });
        bytes32 oid = originId(o);
        assertTrue(getOriginExists(_originRegistryStorage(), oid), "origin not registered");
    }

    function _assertBindingCount(uint256 chainId, address pool, uint256 sig, uint256 expected) internal view {
        OriginEndpoint memory o = OriginEndpoint({
            chainId: uint32(chainId),
            emitter: pool,
            eventSig: bytes32(sig)
        });
        bytes32 oid = originId(o);
        assertEq(getBindingCountByOrigin(_eventDispatchStorage(), oid), expected, "wrong binding count");
    }
}

/// @dev Minimal mock that accepts any subscribe/unsubscribe call without reverting.
contract MockSubscriptionService {
    fallback() external payable {}
    receive() external payable {}
}
