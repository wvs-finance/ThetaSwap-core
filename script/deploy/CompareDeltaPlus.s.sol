// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {StdAssertions} from "forge-std/StdAssertions.sol";
import {console2} from "forge-std/console2.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {IFeeConcentrationIndex} from "../../src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {ReactiveHookAdapter} from
    "../../src/reactive-integration/adapters/uniswapV3/ReactiveHookAdapter.sol";
import {fromV3Pool} from "../../src/reactive-integration/libraries/PoolKeyExtMod.sol";
import {
    resolveTokens,
    ethSepoliaFCIHook,
    sepoliaFreshV3Pool,
    sepoliaReactiveAdapter,
    SEPOLIA
} from "../utils/Deployments.sol";
import "../utils/Constants.sol";

// Same-chain differential comparison: reads deltaPlus from both the V4 FCI
// hook and the V3 ReactiveHookAdapter on Eth Sepolia (fresh pools, fee=3000).
//
// Usage:
//   forge script CompareDeltaPlusScript --sig "run()" --rpc-url $SEPOLIA_RPC_URL
//
// No broadcast needed — purely read-only.

contract CompareDeltaPlusScript is Script, StdAssertions {
    function run() public view {
        require(block.chainid == SEPOLIA, "CompareDeltaPlus: only Eth Sepolia");

        (address tokenA, address tokenB) = resolveTokens(SEPOLIA);
        (address c0, address c1) = tokenA < tokenB
            ? (tokenA, tokenB)
            : (tokenB, tokenA);

        // ── V4 side: FCI hook on fresh pool (fee=3000) ──
        address fciHook = ethSepoliaFCIHook();
        PoolKey memory v4Key = PoolKey({
            currency0: Currency.wrap(c0),
            currency1: Currency.wrap(c1),
            fee: 3000,
            tickSpacing: int24(TICK_SPACING),
            hooks: IHooks(fciHook)
        });

        IFeeConcentrationIndex v4Fci = IFeeConcentrationIndex(fciHook);
        uint128 v4Delta = v4Fci.getDeltaPlus(v4Key, false);
        console2.log("[V4] deltaPlus = %d", uint256(v4Delta));

        // ── V3 side: ReactiveHookAdapter on fresh pool (fee=3000) ──
        ReactiveHookAdapter adapter = ReactiveHookAdapter(payable(sepoliaReactiveAdapter()));
        IUniswapV3Pool freshV3 = sepoliaFreshV3Pool();
        PoolKey memory v3Key = fromV3Pool(freshV3, address(adapter));

        uint128 v3Delta = adapter.getDeltaPlus(v3Key, true);
        console2.log("[V3] deltaPlus (reactive) = %d", uint256(v3Delta));

        // ── Compare ──
        assertEq(
            uint256(v4Delta),
            uint256(v3Delta),
            "deltaPlus mismatch: V4 local vs V3 reactive"
        );
        console2.log("=== PASS: deltaPlus V4 == V3 ===");
    }
}
