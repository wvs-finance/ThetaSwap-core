// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {BaseTargetFunctions} from "chimera/BaseTargetFunctions.sol";

import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {ModifyLiquidityParams} from "v4-core/src/types/PoolOperation.sol";
import {Position} from "v4-core/src/libraries/Position.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";

import {TickRange, fromTicks} from "../../../src/fee-concentration-index/types/TickRangeMod.sol";
import {Properties} from "./Properties.sol";

// Chimera TargetFunctions: fuzzer calls exposed_afterAddLiquidity directly on harness.
// Inputs are clamped to valid tick ranges. Ghost state updated for property checking.

abstract contract TargetFunctions is BaseTargetFunctions, Properties {
    function fuzz_afterAddLiquidity(
        address sender,
        int24 tickLower,
        int24 tickUpper,
        int256 liquidityDelta,
        bytes32 salt
    ) public {
        // Clamp ticks to valid range aligned to tick spacing
        int24 spacing = fciPoolKey.tickSpacing;
        tickLower = int24(between(int256(tickLower), TickMath.MIN_TICK, TickMath.MAX_TICK - spacing));
        tickUpper = int24(between(int256(tickUpper), int256(tickLower) + spacing, TickMath.MAX_TICK));
        tickLower = (tickLower / spacing) * spacing;
        tickUpper = (tickUpper / spacing) * spacing;
        if (tickUpper <= tickLower) tickUpper = tickLower + spacing;

        // Positive liquidity for add
        liquidityDelta = between(liquidityDelta, 1, type(int128).max);

        ModifyLiquidityParams memory params = ModifyLiquidityParams({
            tickLower: tickLower,
            tickUpper: tickUpper,
            liquidityDelta: liquidityDelta,
            salt: salt
        });

        try harness.exposed_afterAddLiquidity(
            sender,
            fciPoolKey,
            params,
            BalanceDelta.wrap(0),
            BalanceDelta.wrap(0),
            ""
        ) {
            // Update ghost state only on success
            bytes32 positionKey = Position.calculatePositionKey(sender, tickLower, tickUpper, salt);

            if (!ghostRegistered[positionKey]) {
                ghostRegistered[positionKey] = true;
                ghostTickLower[positionKey] = tickLower;
                ghostTickUpper[positionKey] = tickUpper;
                allPositionKeys.push(positionKey);
                positionsAdded++;
            }
        } catch {
            // Skip invalid inputs (e.g. uninitialized ticks causing overflow)
        }
    }
}
