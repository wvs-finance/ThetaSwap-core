// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {KontrolCheats} from "kontrol-cheatcodes/KontrolCheats.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {IUniswapV3Factory} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol";
import {fromV3Pool, toV3Pool, toPoolId} from "reactive-hooks/libraries/PoolKeyExtMod.sol";

// Minimal mock returning configurable V3 pool properties.
contract MockV3Pool {
    address public token0;
    address public token1;
    uint24 public fee;
    int24 public tickSpacing;

    constructor(address _t0, address _t1, uint24 _fee, int24 _ts) {
        token0 = _t0;
        token1 = _t1;
        fee = _fee;
        tickSpacing = _ts;
    }
}

// Minimal mock returning a pool address for (token0, token1, fee).
contract MockV3Factory {
    mapping(address => mapping(address => mapping(uint24 => address))) public getPool;

    function setPool(address t0, address t1, uint24 fee, address pool) external {
        getPool[t0][t1][fee] = pool;
    }
}

contract PoolKeyExtProof is Test, KontrolCheats {
    // RX-004: hooks field always set to adapter address
    function prove_poolKey_hooksField(
        address t0,
        address t1,
        uint24 fee,
        int24 ts,
        address adapter
    ) public {
        vm.assume(t0 != address(0));
        vm.assume(t1 != address(0));
        vm.assume(t0 < t1);
        vm.assume(adapter != address(0));

        MockV3Pool mock = new MockV3Pool(t0, t1, fee, ts);
        PoolKey memory key = fromV3Pool(IUniswapV3Pool(address(mock)), adapter);

        assert(address(key.hooks) == adapter);
    }

    // RX-002: same inputs produce same PoolKey (deterministic)
    function prove_poolKey_deterministic(
        address t0,
        address t1,
        uint24 fee,
        int24 ts,
        address adapter
    ) public {
        vm.assume(t0 != address(0));
        vm.assume(t1 != address(0));
        vm.assume(t0 < t1);
        vm.assume(adapter != address(0));

        MockV3Pool mock = new MockV3Pool(t0, t1, fee, ts);
        IUniswapV3Pool pool = IUniswapV3Pool(address(mock));

        PoolKey memory k1 = fromV3Pool(pool, adapter);
        PoolKey memory k2 = fromV3Pool(pool, adapter);

        assert(PoolId.unwrap(PoolIdLibrary.toId(k1)) == PoolId.unwrap(PoolIdLibrary.toId(k2)));
    }

    // RX-003: distinct pools produce distinct PoolIds
    function prove_poolKey_distinct(
        address t0a, address t1a, uint24 feeA, int24 tsA,
        address t0b, address t1b, uint24 feeB, int24 tsB,
        address adapter
    ) public {
        vm.assume(t0a < t1a && t0b < t1b);
        vm.assume(t0a != address(0) && t1a != address(0));
        vm.assume(t0b != address(0) && t1b != address(0));
        vm.assume(adapter != address(0));
        // At least one field differs
        vm.assume(t0a != t0b || t1a != t1b || feeA != feeB || tsA != tsB);

        MockV3Pool mockA = new MockV3Pool(t0a, t1a, feeA, tsA);
        MockV3Pool mockB = new MockV3Pool(t0b, t1b, feeB, tsB);

        PoolId idA = toPoolId(IUniswapV3Pool(address(mockA)), adapter);
        PoolId idB = toPoolId(IUniswapV3Pool(address(mockB)), adapter);

        assert(PoolId.unwrap(idA) != PoolId.unwrap(idB));
    }

    // RX-001: fromV3Pool → toV3Pool round-trips to original address
    function prove_poolKey_roundTrip(
        address t0,
        address t1,
        uint24 fee,
        int24 ts,
        address adapter
    ) public {
        vm.assume(t0 != address(0));
        vm.assume(t1 != address(0));
        vm.assume(t0 < t1);
        vm.assume(adapter != address(0));

        MockV3Pool mock = new MockV3Pool(t0, t1, fee, ts);
        address poolAddr = address(mock);

        // Register pool in factory mock
        MockV3Factory factory = new MockV3Factory();
        factory.setPool(t0, t1, fee, poolAddr);

        PoolKey memory key = fromV3Pool(IUniswapV3Pool(poolAddr), adapter);
        IUniswapV3Pool recovered = toV3Pool(key, IUniswapV3Factory(address(factory)));

        assert(address(recovered) == poolAddr);
    }
}
