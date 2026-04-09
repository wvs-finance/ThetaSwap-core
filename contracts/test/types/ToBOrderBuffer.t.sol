// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {BaseTest} from "test/_helpers/BaseTest.sol";
import {ToBOrderBuffer, ToBOrderBufferLib} from "src/types/ToBOrderBuffer.sol";
import {TopOfBlockOrder} from "test/_reference/OrderTypes.sol";
import {TopOfBlockOrder as SignedTopOfBlockOrder} from "test/_reference/SignedTypes.sol";

/// @author philogy <https://github.com/philogy>
contract ToBOrderBufferTest is BaseTest {
    struct Marker {
        uint256 value;
    }

    function test_bufferBytes() public pure {
        ToBOrderBuffer memory buffer;
        Marker memory end = Marker(1);

        uint256 gap;
        assembly ("memory-safe") {
            gap := sub(end, buffer)
        }

        assertEq(gap, ToBOrderBufferLib.BUFFER_BYTES);
    }

    function test_fuzzing_bufferTypeHashEqualReference(SignedTopOfBlockOrder calldata order)
        public
    {
        TopOfBlockOrder memory refOrder;
        refOrder.quantityIn = order.quantity_in;
        refOrder.quantityOut = order.quantity_out;
        refOrder.maxGasAsset0 = order.max_gas_asset0;
        refOrder.useInternal = order.use_internal;
        refOrder.assetIn = order.asset_in;
        refOrder.assetOut = order.asset_out;
        refOrder.recipient = order.recipient;
        refOrder.validForBlock = order.valid_for_block;

        vm.roll(order.valid_for_block);

        ToBOrderBuffer memory buffer;
        buffer.init();
        buffer.quantityIn = order.quantity_in;
        buffer.quantityOut = order.quantity_out;
        buffer.maxGasAsset0 = order.max_gas_asset0;
        buffer.useInternal = order.use_internal;
        buffer.assetIn = order.asset_in;
        buffer.assetOut = order.asset_out;
        buffer.recipient = order.recipient;

        assertEq(buffer.hash(), refOrder.hash());
    }

    function test_fuzzing_bufferPythonEquivalence(SignedTopOfBlockOrder calldata order) public {
        vm.roll(order.valid_for_block);

        ToBOrderBuffer memory buffer;
        buffer.init();
        buffer.quantityIn = order.quantity_in;
        buffer.quantityOut = order.quantity_out;
        buffer.maxGasAsset0 = order.max_gas_asset0;
        buffer.useInternal = order.use_internal;
        buffer.assetIn = order.asset_in;
        buffer.assetOut = order.asset_out;
        buffer.recipient = order.recipient;

        bytes32 pythonHash = ffiPythonEIP712Hash(buffer);

        assertEq(pythonHash, buffer.hash(), "python != buffer");
    }

    function ffiPythonEIP712Hash(ToBOrderBuffer memory buffer) internal returns (bytes32) {
        string[] memory args = new string[](10);
        args[0] = "test/_reference/eip712.py";
        args[1] = "test/_reference/SignedTypes.sol:TopOfBlockOrder";
        uint256 i = 2;
        args[i++] = vm.toString(buffer.quantityIn);
        args[i++] = vm.toString(buffer.quantityOut);
        args[i++] = vm.toString(buffer.maxGasAsset0);
        args[i++] = vm.toString(buffer.useInternal);
        args[i++] = vm.toString(buffer.assetIn);
        args[i++] = vm.toString(buffer.assetOut);
        args[i++] = vm.toString(buffer.recipient);
        args[i++] = vm.toString(buffer.validForBlock);
        return bytes32(ffiPython(args));
    }

    function _markMem() internal pure {
        bytes32 marker = (keccak256("marker"));
        assembly ("memory-safe") {
            let free := mload(0x40)
            mstore(0x40, add(free, 0x20))
            mstore(free, marker)
        }
    }
}
