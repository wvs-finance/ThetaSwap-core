// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {BaseForkTest} from "anstrong-test/_helpers/BaseForkTest.t.sol";
import {AngstromAccumulatorConsumer} from "core/src/_adapters/AngstromAccumulatorConsumer.sol";
import {IAngstromAuth} from "core/src/interfaces/IAngstromAuth.sol";
import {console2} from "forge-std/console2.sol";
import "anstrong-test/_fork_references/Ethereum.sol" as EthereumForkData;
import {
    AccumulatorRow,
    lenArgs,
    rowArgs,
    minArgs,
    maxArgs,
    rangeArgs,
    decodeLen,
    decodeRow,
    decodeRange
} from "anstrong-test/_ffi_utils/ffiLib.sol";

contract AngstromAccumulatorConsumerForkDifferentialTest is BaseForkTest {
    AngstromAccumulatorConsumer consumer;

    uint256 constant FIRST_NONZERO_IDX = 0;
    uint256 constant MAX_SPIKE_IDX = 27677;

    function setUp() public override {
        super.setUp();
        if (!forked) return;

        consumer = new AngstromAccumulatorConsumer(
            IAngstromAuth(EthereumForkData.AngstromAddresses.ANGSTROM),
            POOL_MANAGER
        );
        vm.makePersistent(address(consumer));
    }

    function test__OffChainDifferentialTest__First() public onlyForked {
        AccumulatorRow memory row = decodeRow(ffiPython(rowArgs(vm, 0)));
        vm.rollFork(row.blockNumber);
        uint256 onchain = consumer.globalGrowth(USDC_WETH);
        assertEq(onchain, row.globalGrowth, "first row mismatch");
    }

    function test__OffChainDifferentialTest__Last() public onlyForked {
        uint256 n = decodeLen(ffiPython(lenArgs()));
        AccumulatorRow memory row = decodeRow(ffiPython(rowArgs(vm, n - 1)));
        vm.rollFork(row.blockNumber);
        uint256 onchain = consumer.globalGrowth(USDC_WETH);
        assertEq(onchain, row.globalGrowth, "last row mismatch");
    }

    function test__OffChainDifferentialTest__FirstNonZero() public onlyForked {
        AccumulatorRow memory row = decodeRow(ffiPython(rowArgs(vm, FIRST_NONZERO_IDX)));
        assertTrue(row.globalGrowth > 0, "expected non-zero growth");
        vm.rollFork(row.blockNumber);
        uint256 onchain = consumer.globalGrowth(USDC_WETH);
        assertEq(onchain, row.globalGrowth, "first nonzero mismatch");
    }

    function test__OffChainDifferentialTest__MaxSpike() public onlyForked {
        AccumulatorRow memory row = decodeRow(ffiPython(rowArgs(vm, MAX_SPIKE_IDX)));
        vm.rollFork(row.blockNumber);
        uint256 onchain = consumer.globalGrowth(USDC_WETH);
        assertEq(onchain, row.globalGrowth, "max spike mismatch");
    }

    function test__OffChainDifferentialTest__Midpoint() public onlyForked {
        uint256 n = decodeLen(ffiPython(lenArgs()));
        uint256 mid = n / 2;
        AccumulatorRow memory row = decodeRow(ffiPython(rowArgs(vm, mid)));
        vm.rollFork(row.blockNumber);
        uint256 onchain = consumer.globalGrowth(USDC_WETH);
        assertEq(onchain, row.globalGrowth, "midpoint mismatch");
    }

    function test__OffChainFuzzDifferentialTest__GlobalGrowthMatches(uint256 idxSeed) public onlyForked {
        uint256 n = decodeLen(ffiPython(lenArgs()));
        require(n > 0, "empty dataset");
        uint256 idx = bound(idxSeed, 0, n - 1);

        AccumulatorRow memory row = decodeRow(ffiPython(rowArgs(vm, idx)));
        vm.rollFork(row.blockNumber);
        uint256 onchain = consumer.globalGrowth(USDC_WETH);
        assertEq(onchain, row.globalGrowth, "globalGrowth mismatch");
    }
}
