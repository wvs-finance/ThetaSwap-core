// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {console2} from "forge-std/console2.sol";
import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {UniswapV3Reactive} from "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol";
import {POOL_ADDED_SIG} from "@fee-concentration-index-v2/libraries/PoolAddedSig.sol";
import {UNISWAP_V3_REACTIVE} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";
import {encodeV3PoolAddedData} from "@fee-concentration-index-v2/protocols/uniswap-v3/libraries/UniswapV3PoolAddedLib.sol";

/// @notice Debug test — simulates react() with a mock PoolAdded log
contract UniswapV3ReactiveDebugTest is Test {

    UniswapV3Reactive reactive;

    address constant FACET = 0x1f9A0011e1653597FC3A2f835bD2179071976d0A;
    address constant CALLBACK = 0x821Da61070C91073eDAe5bFB1D6B2CE17448e22A;
    address constant V3_POOL = 0xF66da9dd005192ee584a253b024070c9A1A1F4FA;
    uint256 constant SEPOLIA_CHAIN_ID = 11155111;
    bytes32 constant MOCK_POOL_ID = bytes32(uint256(0x1234));

    function setUp() public {
        // Mock SystemContract at 0x...fffFfF so constructor doesn't revert
        // On RN: SystemContract has code → isReactiveVm returns true → constructor subscribes
        // We etch dummy code so extcodesize > 0, then mock subscribe calls
        address systemContract = 0x0000000000000000000000000000000000fffFfF;
        vm.etch(systemContract, hex"00");

        // Mock all calls to SystemContract to succeed (subscribe, debt, etc)
        vm.mockCall(systemContract, bytes(""), abi.encode(true));

        reactive = new UniswapV3Reactive{value: 0.1 ether}(CALLBACK);
    }

    function test_decode_poolAdded_data() public {
        // Exact data from the live event
        bytes memory logData = hex"52ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000aa36a7000000000000000000000000f66da9dd005192ee584a253b024070c9a1a1f4fa000000000000000000000000f66da9dd005192ee584a253b024070c9a1a1f4fa";

        (bytes2 protocolFlag, bytes memory poolData) = abi.decode(logData, (bytes2, bytes));
        console2.log("protocolFlag match: %s", protocolFlag == UNISWAP_V3_REACTIVE);

        (uint256 chainId, address pool, address stateView) = abi.decode(poolData, (uint256, address, address));
        console2.log("chainId: %d", chainId);
        console2.log("pool: %s", pool);
    }

    function test_react_poolAdded() public {
        // Build a mock PoolAdded log matching what the facet emits
        // event PoolAdded(address indexed facet, address indexed callback, PoolId indexed poolId, bytes2 protocolFlag, bytes data)
        // topic_0 = POOL_ADDED_SIG
        // topic_1 = facet address
        // topic_2 = callback address
        // topic_3 = poolId
        // data = abi.encode(bytes2 protocolFlag, bytes poolData)

        bytes memory poolData = encodeV3PoolAddedData(SEPOLIA_CHAIN_ID, V3_POOL, V3_POOL);
        bytes memory logData = abi.encode(UNISWAP_V3_REACTIVE, poolData);

        IReactive.LogRecord memory log = IReactive.LogRecord({
            chain_id: SEPOLIA_CHAIN_ID,
            _contract: FACET,
            topic_0: POOL_ADDED_SIG,
            topic_1: uint256(uint160(FACET)),
            topic_2: uint256(uint160(CALLBACK)),
            topic_3: uint256(MOCK_POOL_ID),
            data: logData,
            block_number: 0,
            op_code: 0,
            block_hash: 0,
            tx_hash: 0,
            log_index: 0
        });

        console2.log("Calling react() with PoolAdded log...");

        // This should process handlePoolAdded → register EDT → subscribe
        // But requireVM() will revert since we're not in ReactVM
        // Skip the requireVM check
        vm.mockCall(
            address(0x0000000000000000000000000000000000fffFfF),
            abi.encodeWithSignature(""),
            ""
        );

        // Try calling react directly — expect it to revert with requireVM
        // since we can't properly simulate ReactVM
        try reactive.react(log) {
            console2.log("react() succeeded");
        } catch (bytes memory reason) {
            console2.log("react() reverted");
            console2.logBytes(reason);
        }
    }

    function test_handlePoolAdded_directly() public {
        // Test handlePoolAdded logic directly by importing the free function
        // and calling it with the mock log data

        bytes memory poolData = encodeV3PoolAddedData(SEPOLIA_CHAIN_ID, V3_POOL, V3_POOL);
        bytes memory logData = abi.encode(UNISWAP_V3_REACTIVE, poolData);

        console2.log("logData length: %d", logData.length);
        console2.log("poolData length: %d", poolData.length);

        // Try to decode the way handlePoolAdded does
        (bytes2 protocolFlag, bytes memory decoded) = abi.decode(logData, (bytes2, bytes));
        console2.log("protocolFlag: %s", vm.toString(protocolFlag));
        console2.log("decoded poolData length: %d", decoded.length);

        (uint256 chainId, address pool, address stateView) = abi.decode(decoded, (uint256, address, address));
        console2.log("chainId: %d", chainId);
        console2.log("pool: %s", pool);
        console2.log("stateView: %s", stateView);
    }
}
