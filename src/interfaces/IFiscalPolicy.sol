// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title IFiscalPolicy
 * @author ParityTax Team
 * @notice Interface for fiscal policy implementation in the ParityTax system
 * @dev Defines the core fiscal policy functions for tax calculation, fee remittance,
 * and liquidity commitment handling. This interface is the bridge between the reactive
 * network events from IParityTaxHook and the actual fiscal policy implementation.
 * @dev TODO: This needs to inherit IERC4626
 */

import {IERC4626} from "@openzeppelin/contracts/interfaces/IERC4626.sol";
import {BalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {FeeRevenueInfo} from "../types/FeeRevenueInfo.sol";
import {PoolKey, PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";

import {ILPOracle} from "./ILPOracle.sol";
import {IParityTaxRouter} from "./IParityTaxRouter.sol";
import {ISubscriber} from "@uniswap/v4-periphery/src/interfaces/ISubscriber.sol";

interface IFiscalPolicy is ISubscriber{ 
    


    
    
    error InvalidDataLength();

    function createTaxStrategy(bytes32 poolId) external returns(ITaxHook);
    /**
     * @notice Processes fee revenue remittance and applies taxation
     * @dev Handles fee revenue from both JIT and PLP liquidity providers,
     * applying appropriate taxation based on commitment type
     * @param poolId The pool identifier for the fee revenue
     * @param feeRevenueInfo Packed fee revenue information including amounts and commitment
     * @return BalanceDelta The net balance delta after tax application
     */
    function remit(PoolId poolId, FeeRevenueInfo feeRevenueInfo) external returns(BalanceDelta);
    
    /**
     * @notice Calculates the optimal tax rate for a given pool and context
     * @dev Uses reactive network data and pool metrics to determine the most
     * appropriate tax rate for equitable fee distribution
     * @dev It is intended to be the upgradable target for governance on how to use different
     * techniques for coming down to optimal taxing
     * @dev This function is callable only by the system contract on reactive network.
     * They are triggered by the reactive network flow
     * @param poolId The pool identifier for tax calculation
     * @param data Additional context data for tax calculation
     * @return uint24 The calculated optimal tax rate in pips (1/10000)
     */
    function calculateOptimalTax(PoolId poolId, bytes memory data) external returns(uint24);

    /**
     * @notice Accrues credit for liquidity providers based on their contributions
     * @dev Calculates and tracks credit accumulation for PLP providers based on
     * their commitment duration and fee revenue generation
     * @dev The calculation is to come up with a system of reward distribution with
     * rewards increasing on time commitment
     * @param poolId The pool identifier for credit calculation
     * @param data Additional context data for credit calculation
     * @return uint256 The amount of credit accrued for token0
     * @return uint256 The amount of credit accrued for token1
     */
    function accrueCredit(PoolId poolId, bytes memory data) external returns(uint256, uint256);

    /**
     * @notice Handles liquidity commitment events from the reactive network
     * @dev Processes liquidity commitment data and returns appropriate response
     * for the commitment process
     * @dev This function is callable only by the system contract on reactive network.
     * They are triggered by the reactive network flow
     * @param poolId The pool identifier for the commitment
     * @param data The commitment data from the reactive network
     * @return bytes The response data for the commitment process
     */
    function onLiquidityCommitmment(PoolId poolId, bytes memory data) external returns(bytes memory);

    function onLiquidityOnSwap(PoolId poolId, bytes memory data) external returns(bytes memory);

    function onPriceImpact(PoolId poolId, bytes memory data) external returns(bytes memory);

    /**
     * @notice Returns the liquidity provider oracle instance
     * @dev Provides access to the LP oracle for price and liquidity data
     * @return ILPOracle The liquidity provider oracle contract
     */
    function lpOracle() external returns(ILPOracle);    
}
