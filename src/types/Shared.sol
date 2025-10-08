//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Shared Types and Constants
 * @author ParityTax Team
 * @notice Common types, constants, and data structures used throughout the ParityTax system
 * @dev This file contains all shared types, constants, and data structures that are used across
 * multiple contracts in the ParityTax ecosystem. It includes transient storage locations, liquidity
 * provider types, swap contexts, callback data structures, and various utility constants for the
 * equitable fee distribution and taxation system.
 */

import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {SwapParams, ModifyLiquidityParams} from "@uniswap/v4-core/src/types/PoolOperation.sol";
import {PositionInfo, PositionInfoLibrary} from "@uniswap/v4-periphery/src/libraries/PositionInfoLibrary.sol";
import "@uniswap/v4-core/src/types/BalanceDelta.sol";
import "./SwapIntent.sol";

// ================================ TRANSIENT STORAGE LOCATIONS ================================

/// @dev Transient storage location for JIT liquidity position data
/// @dev keccak256(abi.encode(uint256(keccak256("openzeppelin.transient-storage.JIT_TRANSIENT")) - 1)) & ~bytes32(uint256(0xff))
bytes32 constant  JIT_LIQUIDITY_POSITION_LOCATION = 0xea3262c41a64b3c1fbce2786641b7f7461a1dc7c180ec16bb38fbe7e610def00;

/// @dev Transient storage location for PLP liquidity position data
/// @dev keccak256(abi.encode(uint256(keccak256("openzeppelin.transient-storage.PLP_TRANSIENT")) - 1)) & ~bytes32(uint256(0xff))
bytes32 constant  PLP_LIQUIDITY_POSITION_LOCATION = 0x369fcc6be4409721b124e1944af5cd9c5a8ac6c841854a0f264aead4f039bb00;

/// @dev Transient storage location for price impact data during swaps
/// @dev keccak256(abi.encode(uint256(keccak256("openzeppelin.transient-storage.PRICE_IMPACT")) - 1)) & ~bytes32(uint256(0xff))
bytes32 constant  PRICE_IMPACT_LOCATION = 0x9a6e024ebb4e856a20885b7e11ce369a95696ac0f9ef8bcb2bc66a08583efa00;

/// @dev Transient storage location for liquidity on swap data
/// @dev keccak256(abi.encode(uint256(keccak256("openzeppelin.transient-storage.LIQUIDITY_ON_SWAP")) - 1)) & ~bytes32(uint256(0xff))
bytes32 constant LIQUIDITY_ON_SWAP_LOCATION = 0x5a6e024ebb4e856a20885b7e11ce369a95696ac0f9ef8bcb2bc66a08583efa00;
/// @dev Transient storage location for tax rate data
/// @dev keccak256(abi.encode(uint256(keccak256("openzeppelin.transient-storage.TAX_RATE")) - 1)) & ~bytes32(uint256(0xff))
bytes32 constant TAX_RATE_SLOT = 0x27ab0422f76b78bf083331c8c5fff9ffc12f6849edb4cd1117fbfe5487d3ed00;

// ================================ COMMITMENT CONSTANTS ================================

/// @dev Block commitment value for JIT (Just-In-Time) liquidity providers
uint48 constant JIT_COMMITMENT = uint48(0x01);

/// @dev No commitment value for immediate liquidity operations
uint48 constant NO_COMMITMENT = uint48(0x00);

/// @dev Minimum block number commitment required for PLP (Permanent Liquidity Provider) positions
uint48 constant  MIN_PLP_BLOCK_NUMBER_COMMITMENT = uint48(0x02);

// ================================ DATA LENGTH CONSTANTS ================================

/// @dev Expected length of swap callback data in bytes
uint256 constant SWAP_CALLBACK_DATA_LENGTH = uint256(0x340);

/// @dev Expected length of liquidity commitment data in bytes
uint256 constant LIQUIDITY_COMMITMENT_LENGTH = uint256(0x1e0);

/// @dev Expected length of commitment data in bytes
uint256 constant COMMITMENT_LENGTH = uint256(0x40);

// ================================ ENUMS ================================

/**
 * @notice Enum representing different types of liquidity providers in the ParityTax system
 * @dev Used to distinguish between JIT (Just-In-Time) and PLP (Permanent Liquidity Provider) types
 * for different fee distribution and taxation policies
 */
enum LP_TYPE{
    /// @notice Just-In-Time liquidity provider - provides liquidity for very short durations
    JIT,
    /// @notice Permanent Liquidity Provider - commits liquidity for longer durations with block commitments
    PLP
}


// ================================ SWAP-RELATED STRUCTS ================================

/**
 * @notice Struct containing swap output amounts
 * @dev Used to track the actual amounts involved in a swap operation
 */
struct SwapOutput{
    /// @notice The amount of input currency used in the swap
    uint256 amountIn;
    /// @notice The amount of output currency received from the swap
    uint256 amountOut;
}

/**
 * @notice Struct containing comprehensive swap context information
 * @dev Used throughout the ParityTax system to track swap state and calculate optimal taxation
 */
struct SwapContext {
    /// @notice The pool configuration for the swap
    PoolKey poolKey;
    /// @notice The swap parameters including amount and direction
    SwapParams swapParams;
    /// @notice The actual input amount used in the swap
    uint256 amountIn;
    /// @notice The actual output amount received from the swap
    uint256 amountOut;
    /// @notice The sqrt price before the swap occurred
    uint160 beforeSwapSqrtPriceX96;
    /// @notice The PLP liquidity available during the swap
    uint128 plpLiquidity;                   
    /// @notice The expected sqrt price after the swap
    uint160 expectedAfterSwapSqrtPriceX96;  
    /// @notice The expected tick after the swap
    int24 expectedAfterSwapTick;
}

/**
 * @notice Struct containing price impact information for swap analysis
 * @dev Used to track price changes and calculate impact for taxation purposes
 */
struct SwapPriceImpactInfo{
    /// @notice The balance delta resulting from the swap
    BalanceDelta swapDelta;
    /// @notice The sqrt price before the swap
    uint160 beforeSwapSqrtPriceX96;
    /// @notice The external sqrt price before the swap (from oracle)
    uint160 beforeSwapExternalSqrtPriceX96;
    /// @notice The sqrt price after the swap
    uint160 afterSwapSqrtPriceX96;
    /// @notice The external sqrt price after the swap (from oracle)
    uint160 afterSwapExternalSqrtPriceX96;
}


// ================================ LIQUIDITY-RELATED STRUCTS ================================

/**
 * @notice Struct containing complete liquidity position information
 * @dev Used to track both JIT and PLP liquidity positions with their commitments and fee revenue
 */
struct LiquidityPosition{
    /// @notice The type of liquidity provider (JIT or PLP)
    LP_TYPE lpType;
    /// @notice The block number commitment for the position
    uint256 blockCommitment;
    /// @notice The address of the position owner
    address owner;
    /// @notice The NFT token ID representing the position
    uint256 tokenId;
    /// @notice The position key for the liquidity position
    bytes32 positionKey;
    /// @notice The position information including pool details
    PositionInfo positionInfo;
    /// @notice The amount of liquidity in the position
    uint256 liquidity;
    /// @notice The fee revenue accrued on currency0
    uint256 feeRevenueOnCurrency0;
    /// @notice The fee revenue accrued on currency1
    uint256 feeRevenueOnCurrency1;
}

// ================================ CALLBACK DATA STRUCTS ================================

/**
 * @notice Struct containing swap callback data
 * @dev Used to pass data to swap callbacks in the ParityTax hook system
 */
struct SwapCallbackData {
    /// @notice The address initiating the swap
    address sender;
    /// @notice The pool configuration for the swap
    PoolKey key;
    /// @notice The swap parameters
    SwapParams params;
    /// @notice Additional hook-specific data
    bytes hookData;
}

/**
 * @notice Struct containing modify liquidity callback data
 * @dev Used to pass data to liquidity modification callbacks in the ParityTax hook system
 */
struct ModifyLiquidityCallBackData{
    /// @notice The address initiating the liquidity modification
    address sender;
    /// @notice The pool configuration for the liquidity operation
    PoolKey key;
    /// @notice The liquidity modification parameters
    ModifyLiquidityParams params;
    /// @notice Additional hook-specific data
    bytes hookData;
}

/**
 * @notice Struct containing commitment information
 * @dev Used to track block number commitments for liquidity providers
 */
struct Commitment{
    /// @notice The address making the commitment
    address committer;
    /// @notice The block number until which the commitment is valid
    uint48 blockNumberCommitment;
}

enum DEX{
    UNISWAP_V4,
    ALGEBRA_INTEGRAL,
    BALANCER_V3
}

struct OnboardingData{
    address token0;
    address token1;
    Commitment lpCommitment;
    DEX dex;
    bool isCLAMM;
    uint256 currentPrice; 
    uint256 currentFee;
    uint256 tickSpacing;
}


// ================================ REACTIVE NETWORK CALLBACK STRUCTS ================================

/**
 * @notice Struct containing price impact callback data for reactive network
 * @dev Used by FiscalLogDispatcher to forward PriceImpact events to the fiscal policy
 */
struct PriceImpactCallback{
    /// @notice The block number when the price impact occurred
    uint48 blockNumber;
    /// @notice The swap intent (direction and type of swap)
    SwapIntent swapIntent;
    /// @notice The balance delta from the swap
    BalanceDelta swapDelta;
    /// @notice The sqrt price before the swap
    uint160 beforeSwapSqrtPriceX96;
    /// @notice The external sqrt price before the swap (from oracle)
    uint160 beforeSwapExternalSqrtPriceX96;
    /// @notice The sqrt price after the swap
    uint160 afterSwapSqrtPriceX96;
    /// @notice The external sqrt price after the swap (from oracle)
    uint160 afterSwapExternalSqrtPriceX96;
}

/**
 * @notice Struct containing liquidity distribution callback data for reactive network
 * @dev Used by FiscalLogDispatcher to forward LiquidityOnSwap events to the fiscal policy
 */
struct LiquidityOnSwapCallback{
    /// @notice The block number when the liquidity distribution occurred
    uint48 blockNumber;
    /// @notice The total liquidity available in the pool
    uint128 totalLiquidity;
    /// @notice The JIT liquidity amount
    uint128 jitLiquidity;
    /// @notice The PLP liquidity amount
    uint128 plpLiquidity;
}

/**
 * @notice Struct containing liquidity commitment callback data for reactive network
 * @dev Used by FiscalLogDispatcher to forward LiquidityCommitted events to the fiscal policy
 */
struct LiquidityCommittedCallback{
    /// @notice The block number when the commitment was made
    uint48 blockNumber;
    /// @notice The block number commitment for the liquidity
    uint48 commitment;
    /// @notice The address of the liquidity provider
    address owner;
    /// @notice The NFT token ID representing the position
    uint256 tokenId;
    /// @notice Encoded liquidity parameters
    bytes liquidityParams;
}

/**
 * @notice Struct containing remittance callback data for reactive network
 * @dev Used by FiscalLogDispatcher to forward Remittance events to the fiscal policy
 */
struct RemittanceCallback {
    /// @notice The block number when the remittance occurred
    uint48 blockNumber;
    /// @notice The block number commitment for the remittance
    uint48 blockCommitment;
    /// @notice The fee revenue delta being remitted
    BalanceDelta feeRevenueDelta;
}




