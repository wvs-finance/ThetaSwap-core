// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {AssetArray} from "src/types/Asset.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {TransientStateLibrary, Currency} from "v4-core/src/libraries/TransientStateLibrary.sol";
import {console} from "forge-std/console.sol";

library Debugging {
    using TransientStateLibrary for IPoolManager;

    function logUnresolvedUniswapDeltas(IPoolManager uni, AssetArray assets) internal view {
        if (uni.getNonzeroDeltaCount() == 0) {
            console.log("[TRACE] All Uniswap deltas resolved");
            return;
        }

        console.log("[ERROR] Unresolved deltas:");

        for (uint256 i = 0; i < assets.len(); i++) {
            address asset = assets.get(i).addr();
            int256 delta = uni.currencyDelta(address(this), Currency.wrap(asset));
            if (delta == 0) continue;
            if (delta > 0) {
                console.log("  %s: +%s", asset, uint256(delta));
            } else {
                unchecked {
                    console.log("  %s: -%s", asset, uint256(-delta));
                }
            }
        }
    }
}
