//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {
    PoolId,
    PoolIdLibrary,
    PoolKey
} from "@uniswap/v4-core/src/types/PoolId.sol";
import {BalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import "../types/SwapIntent.sol";
import "./ISwapMetrics.sol";
import "./ILiquidityMetrics.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";
import {IFiscalPolicy} from "./IFiscalPolicy.sol";
import {IExttload} from "@uniswap/v4-core/src/interfaces/IExttload.sol";
import {IPLPResolver} from "./IPLPResolver.sol";
import {IJITResolver} from "./IJITResolver.sol";
import {IParityTaxExtt} from "./IParityTaxExtt.sol";

/**
 * @title IParityTaxHook
 * @author ParityTax Team
 * @notice Interface for the ParityTax hook system implementing equitable fee distribution
 * @dev This interface defines the core functionality for managing JIT and PLP liquidity commitments,
 * fee collection, and tax distribution between different liquidity provider types
 */
interface IParityTaxHook is IExttload{


    /**
     * @notice Emitted when price impact is calculated during a swap
     * @param poolId The unique identifier of the pool
     * @param blockNumber The block number when the swap occurred
     * @param swapIntent The direction and type of swap (buy/sell)
     * @param swapDelta The balance changes resulting from the swap
     * @param beforeSwapSqrtPriceX96 The sqrt price before the swap
     * @param beforeSwapExternalSqrtPriceX96 The external sqrt price before the swap
     * @param afterSwapSqrtPriceX96 The sqrt price after the swap
     * @param afterSwapExternalSqrtPriceX96 The external sqrt price after the swap
     */
    event PriceImpact(
        bytes32 indexed poolId,
        uint48 indexed blockNumber,
        SwapIntent indexed swapIntent,
        BalanceDelta swapDelta,
        uint160 beforeSwapSqrtPriceX96,
        uint160 beforeSwapExternalSqrtPriceX96,
        uint160 afterSwapSqrtPriceX96,
        uint160 afterSwapExternalSqrtPriceX96
    );

    /**
     * @notice Emitted when liquidity distribution is tracked during a swap
     * @param poolId The unique identifier of the pool
     * @param blockNumber The block number when the swap occurred
     * @param totalLiquidity Total liquidity available in the pool
     * @param jitLiquidity JIT (Just-In-Time) liquidity amount
     * @param plpLiquidity PLP (Permanent Liquidity Provider) liquidity amount
     */
    event LiquidityOnSwap(
        uint256 indexed positionInfo // The position info contains ticks and bytes25 poolId
        bytes32 indexed poolId, // This is the bytes32 pool id   
        uint128 jitLiquidity, //  JIT Liquidity entered on the swap
        uint128 plpLiquidity // PLP Liquiity entered on the swap
    );
    
    /**
     * @notice Emitted when liquidity is committed with a specific block number commitment
     * @param poolId The unique identifier of the pool
     * @param blockNumber The block number when the commitment was made
     * @param commitment The block number commitment for the liquidity
     * @param owner The address of the liquidity provider
     * @param tokenId The NFT token ID representing the position
     * @param liquidityParams Encoded liquidity parameters
     */
    event LiquidityCommitted(
        bytes32 indexed poolId,
        uint48 indexed blockNumber,
        uint48 indexed commitment,
        address indexed owner,
        uint256 tokenId,
        bytes liquidityParams
    ) anonymous;

    /**
     * @notice Emitted when fee revenue is remitted to the fiscal policy
     * @param poolId The unique identifier of the pool
     * @param currentBlock The current block number
     * @param blockCommitment The block number commitment for the remittance
     * @param feeRevenueDelta The fee revenue being remitted
     */
    event Remittance (
        bytes32 indexed poolId,
        uint48 indexed currentBlock,
        uint48 indexed blockCommitment,
        BalanceDelta feeRevenueDelta
    );

    
    
    /// @notice Thrown when the calculated amount out exceeds the specified swap amount out
    error AmountOutGreaterThanSwapAmountOut();
    
    /// @notice Thrown when there is insufficient liquidity in the pool for the operation
    /// @param poolId The pool identifier where liquidity is insufficient
    error NotEnoughLiquidity(PoolId poolId);
    
    /// @notice Thrown when attempting to withdraw liquidity that is still committed
    error NotWithdrawableLiquidity__LiquidityIsCommitted();
    
    /// @notice Thrown when there is no liquidity available to receive tax revenue
    error NoLiquidityToReceiveTaxRevenue();
    
    /// @notice Thrown when there is a mismatch between expected and actual currencies
    error CurrencyMissmatch();
    
    /// @notice Thrown when there is no liquidity available to receive tax credits
    error NoLiquidityToReceiveTaxCredit();
    
    /// @notice Thrown when an invalid caller attempts to access liquidity router functions
    error InvalidLiquidityRouterCaller();
    
    /// @notice Thrown when PLP block commitment is below the minimum required threshold
    error InvalidPLPBlockCommitment();

    // @dev TODO: I need to expose the queries available to the router

    // @dev NOTE: The router can (with access control) store on Hook's transient storage

    /**
     * @notice Stores PLP liquidity change in transient storage
     * @dev Allows the router to update PLP liquidity information
     * @param liquidityChange The change in liquidity amount (positive for addition, negative for removal)
     */
    function tstore_plp_liquidity(int256 liquidityChange) external;

    /**
     * @notice Stores PLP fees accrued in transient storage
     * @dev Allows the router to update PLP fee information
     * @param feesAccruedOn0 The fees accrued on currency0
     * @param feesAccruedOn1 The fees accrued on currency1
     */
    function tstore_plp_feesAccrued(uint256 feesAccruedOn0, uint256 feesAccruedOn1) external;

    /**
     * @notice Returns the position manager contract
     * @return The IPositionManager interface instance
     */
    function positionManager() external returns(IPositionManager);
 
    /**
     * @notice Returns the fiscal policy contract
     * @return The IFiscalPolicy interface instance
     */
    function FiscalPolicy() external returns(IFiscalPolicy);

    /**
     * @notice Sets the liquidity resolvers for PLP and JIT operations
     * @dev Updates the resolver contracts used for different liquidity provider types
     * @param _plpResolver The PLP resolver contract
     * @param _jitResolver The JIT resolver contract
     */
    function setLiquidityResolvers(
        IPLPResolver _plpResolver,
        IJITResolver _jitResolver
    ) external;

    /**
     * @notice Sets the fiscal policy contract
     * @dev Updates the fiscal policy used for tax calculations and remittances
     * @param _fiscalPolicy The fiscal policy contract
     */
    function setFiscalPolicy(
        IFiscalPolicy _fiscalPolicy
    ) external;

    /**
     * @notice Gets the block number commitment for a specific position
     * @dev Returns when the liquidity can be withdrawn based on commitment
     * @param poolId The pool identifier
     * @param owner The position owner address
     * @param tokenId The position token ID
     * @return The block number when the position can be withdrawn
     */
    function getPositionBlockNumberCommitment(
        PoolId poolId,
        address owner,
        uint256 tokenId
    ) external view returns(uint48);

    /**
     * @notice Returns the ParityTaxExtt instance for transient storage operations
     * @dev This allows external contracts to access the transient storage through ParityTaxExtt
     * @return The ParityTaxExtt contract instance
     */
    function getParityTaxExtt() external view returns (IParityTaxExtt);




}