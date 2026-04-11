// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {BaseForkTest} from "anstrong-test/_helpers/BaseForkTest.t.sol";
import {AngstromAccumulatorConsumer} from "core/src/_adapters/AngstromAccumulatorConsumer.sol";
import {IAngstromAuth} from "core/src/interfaces/IAngstromAuth.sol";
import {console2} from "forge-std/console2.sol";
import "anstrong-test/_fork_references/Ethereum.sol" as EthereumForkData;
import {
    AccumulatorRow,
    RAN_POOL_HEX,
    RAN_DB_PATH,
    decodeLen,
    decodeRow,
    decodeRange
} from "./RanFfiLib.sol";

contract DifferentialGrowthForkTest is BaseForkTest {
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

    function _ffiLen() internal returns (uint256) {
        string[] memory args = new string[](7);
        args[0] = "-m";
        args[1] = "scripts.ran_ffi";
        args[2] = "len";
        args[3] = "--pool";
        args[4] = RAN_POOL_HEX;
        args[5] = "--db";
        args[6] = RAN_DB_PATH;
        return decodeLen(ffiPython(args));
    }

    function _ffiRow(uint256 idx) internal returns (AccumulatorRow memory) {
        string[] memory args = new string[](9);
        args[0] = "-m";
        args[1] = "scripts.ran_ffi";
        args[2] = "row";
        args[3] = "--pool";
        args[4] = RAN_POOL_HEX;
        args[5] = "--idx";
        args[6] = vm.toString(idx);
        args[7] = "--db";
        args[8] = RAN_DB_PATH;
        return decodeRow(ffiPython(args));
    }

    function _ffiRowByTs(uint256 ts) internal returns (AccumulatorRow memory) {
        string[] memory args = new string[](10);
        args[0] = "-m";
        args[1] = "scripts.ran_ffi";
        args[2] = "row-by-ts";
        args[3] = "--pool";
        args[4] = RAN_POOL_HEX;
        args[5] = "--ts";
        args[6] = vm.toString(ts);
        args[7] = "--db";
        args[8] = RAN_DB_PATH;
        args[9] = "--nearest";
        return decodeRow(ffiPython(args));
    }

    function _ffiMin() internal returns (AccumulatorRow memory) {
        string[] memory args = new string[](7);
        args[0] = "-m";
        args[1] = "scripts.ran_ffi";
        args[2] = "min";
        args[3] = "--pool";
        args[4] = RAN_POOL_HEX;
        args[5] = "--db";
        args[6] = RAN_DB_PATH;
        return decodeRow(ffiPython(args));
    }

    function _ffiMax() internal returns (AccumulatorRow memory) {
        string[] memory args = new string[](7);
        args[0] = "-m";
        args[1] = "scripts.ran_ffi";
        args[2] = "max";
        args[3] = "--pool";
        args[4] = RAN_POOL_HEX;
        args[5] = "--db";
        args[6] = RAN_DB_PATH;
        return decodeRow(ffiPython(args));
    }

    function _ffiRange(uint256 from_, uint256 to_) internal returns (AccumulatorRow[] memory) {
        string[] memory args = new string[](11);
        args[0] = "-m";
        args[1] = "scripts.ran_ffi";
        args[2] = "range";
        args[3] = "--pool";
        args[4] = RAN_POOL_HEX;
        args[5] = "--from";
        args[6] = vm.toString(from_);
        args[7] = "--to";
        args[8] = vm.toString(to_);
        args[9] = "--db";
        args[10] = RAN_DB_PATH;
        return decodeRange(ffiPython(args));
    }

    function test__OffChainDifferentialTest__First() public onlyForked {
        AccumulatorRow memory row = _ffiRow(0);
        vm.rollFork(row.blockNumber);
        uint256 onchain = consumer.globalGrowth(USDC_WETH);
        assertEq(onchain, row.globalGrowth, "first row mismatch");
    }

    function test__OffChainDifferentialTest__Last() public onlyForked {
        uint256 n = _ffiLen();
        AccumulatorRow memory row = _ffiRow(n - 1);
        vm.rollFork(row.blockNumber);
        uint256 onchain = consumer.globalGrowth(USDC_WETH);
        assertEq(onchain, row.globalGrowth, "last row mismatch");
    }

    function test__OffChainDifferentialTest__FirstNonZero() public onlyForked {
        AccumulatorRow memory row = _ffiRow(FIRST_NONZERO_IDX);
        assertTrue(row.globalGrowth > 0, "expected non-zero growth");
        vm.rollFork(row.blockNumber);
        uint256 onchain = consumer.globalGrowth(USDC_WETH);
        assertEq(onchain, row.globalGrowth, "first nonzero mismatch");
    }

    function test__OffChainDifferentialTest__MaxSpike() public onlyForked {
        AccumulatorRow memory row = _ffiRow(MAX_SPIKE_IDX);
        vm.rollFork(row.blockNumber);
        uint256 onchain = consumer.globalGrowth(USDC_WETH);
        assertEq(onchain, row.globalGrowth, "max spike mismatch");
    }

    function test__OffChainDifferentialTest__Midpoint() public onlyForked {
        uint256 n = _ffiLen();
        uint256 mid = n / 2;
        AccumulatorRow memory row = _ffiRow(mid);
        vm.rollFork(row.blockNumber);
        uint256 onchain = consumer.globalGrowth(USDC_WETH);
        assertEq(onchain, row.globalGrowth, "midpoint mismatch");
    }

    function test__OffChainFuzzDifferentialTest__GlobalGrowthMatches(uint256 idxSeed) public onlyForked {
        uint256 n = _ffiLen();
        require(n > 0, "empty dataset");
        uint256 idx = bound(idxSeed, 0, n - 1);

        AccumulatorRow memory row = _ffiRow(idx);
        vm.rollFork(row.blockNumber);
        uint256 onchain = consumer.globalGrowth(USDC_WETH);
        assertEq(onchain, row.globalGrowth, "globalGrowth mismatch");
    }
}
