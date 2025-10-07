//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title JITResolverBase
 * @author ParityTax Team
 * @notice Abstract base contract for Just-In-Time (JIT) liquidity resolvers
 * @dev This contract provides the foundation for JIT liquidity management in the ParityTax system,
 * handling short-term liquidity provision that is added just before a swap and removed immediately
 * after. JIT resolvers enable efficient liquidity utilization and optimal fee collection by
 * providing liquidity depth exactly when needed for swap operations.
 * @dev Inherits from IJITResolver for interface compliance and ResolverBase for standardized
 * liquidity operations. Critical component in the equitable fee distribution system's dynamic
 * liquidity management and fee optimization.
 */

import "../interfaces/IJITResolver.sol";
import {IParityTaxHook} from "../interfaces/IParityTaxHook.sol";
import "./ResolverBase.sol";

import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {TickBitmap} from "@uniswap/v4-core/src/libraries/TickBitmap.sol";
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {LiquidityAmounts} from "@uniswap/v4-core/test/utils/LiquidityAmounts.sol";
import {StateLibrary} from "@uniswap/v4-core/src/libraries/StateLibrary.sol";
import {SwapIntent,SwapIntentLibrary} from "../types/SwapIntent.sol";
import {PoolId,PoolIdLibrary} from "@uniswap/v4-core/src/types/PoolId.sol";
import {Constants} from "@uniswap/v4-core/test/utils/Constants.sol";

import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {IAllowanceTransfer} from "permit2/src/interfaces/IAllowanceTransfer.sol";
/**
 * @notice Abstract base contract for JIT resolvers
 * @dev Provides standardized JIT liquidity provision and management functionality
 */
import {Ownable} from "@openzeppelin/contracts/Ownable.sol"
abstract contract JITResolverBase is IJITResolver, Ownable{
    using SqrtPriceMath for uint160;
    using LiquidityAmounts for uint160;
    using TickMath for uint160;
    using TickMath for int24;
    using TickBitmap for int24;
    using StateLibrary for IPoolManager;
    using PoolIdLibrary for PoolKey;

    // ================================ CONSTANTS ================================
    
    /// @notice Transient storage location for JIT metrics and data
    /// @dev keccak256(abi.encode(uint256(keccak256("openzeppelin.transient-storage.JIT_TRANSIENT")) - 1)) & ~bytes32(uint256(0xff))
    bytes32 constant JIT_Transient_MetricsLocation = 0xea3262c41a64b3c1fbce2786641b7f7461a1dc7c180ec16bb38fbe7e610def00;

    address liquidityManager;
    
    modifier onlyWithLiquidityManager(){
        if (liquidityManager == address(0x00)){
            revert("Liquidity Manager not set");
        }
        _;
    }
    // ================================ CONSTRUCTOR ================================
    
    /**
     * @notice Initializes the JITResolverBase with Uniswap V4 and ParityTax dependencies
     * @dev Sets up the JIT resolver with pool manager, position manager, and ParityTax hook.
     * Inherits access control and liquidity operations from ResolverBase.
     * @param _poolManager The Uniswap V4 pool manager contract
     * @param _lpm The Uniswap V4 position manager contract
     * @param _parityTaxHook The ParityTax hook contract for integration
     */

    
    constructor(
        IPoolManager _poolManager,
        IPositionManager _lpm,
        IParityTaxHook _parityTaxHook
    ) Ownable(msg.sender){
        
    }

    function initializeLiquidityOnPool(PoolKey calldata poolKey) external{
        address permit2 = abi.decode(
            address(lpm).functionStaticCall(
                abi.encodeWithSignature("permit2()");
            ),
            (address)
        );
        // Because POSM uses permit2, we must execute 2 permits/approvals.
        // 1. First, the caller must approve permit2 on the token.
        IERC20(Currency.unwrap(poolKey.currency0)).approve(address(permit2), type(uint256).max);
        // 2. Then, the caller must approve POSM as a spender of permit2. TODO: This could also be a signature.
        IAllowanceTransfer(permit2).approve(Currency.unwrap(poolKey.currency0), address(lpm), type(uint160).max, type(uint48).max);
        IERC20(Currency.unwrap(poolKey.currency1)).approve(address(permit2), type(uint256).max);
        // 2. Then, the caller must approve POSM as a spender of permit2. TODO: This could also be a signature.
        IAllowanceTransfer(permit2).approve(Currency.unwrap(poolKey.currency1), address(lpm), type(uint160).max, type(uint48).max);

        IERC20(Currency.unwrap(poolKey.currency0)).approve(parityTaxHook, type(uint256).max);
        IERC20(Currency.unwrap(poolKey.currency1)).approve(parityTaxHook, type(uint256).max);
    
    }


    function setLiquidityManager(address _liquidityManager) external onlyOwner{
        // NOTE: THis contract needs to be compliant with something that the EOA user 
        // can withdraw funds from 
        liquidityManager = _liquidityManager;
    }

    function getLiquidityManager() external returns(address){
        return liquidityManager;
    }
        


    function beforeAddLiquidity(
        PoolId poolId,
        SwapParams calldata swapParams,
        PositionInfo externalMarketPositionInfo,
        PositionInfo internalMarketPositionInfo,
        uint128 liquidityForSwap
    ) external onlyWithLiquidityManager returns (
        PositionConfig memory jitPositionConfig,
        uint128 jitLiquidity,
        address liquidityManager,
        bytes memory data
    )
    {   
        (jitPositionConfig, jitLiquidity) = _calculateLiquidityConfigOnSwap(
            poolId,
            swapParams,
            externalMarketPositionInfo,
            internalMarketPositionInfo
        );





    }

    function _calculateLiquidityConfigOnSwap(
        PoolId,
        SwapParams,
        PositionInfo,
        PositionInfo
    ) internal virtual returns(PositionConfig memory, uint128 jitLiquidity);

    function beforeAddLiquidity(
        PoolId poolId,
        SwapParams calldata swapParams,
        PositionInfo externalMarketPositionInfo,
        PositionInfo internalMarketPositionInfo,
        uint128 liquidityForSwap
    ) external returns (
        PositionConfig memory jitPositionConfig,
        uint128 jitLiquidity,
        address liquidityManager,
        bytes memory data
    )
    {
        
    }


    // ================================ EXTERNAL FUNCTIONS ================================

    /**
     * @inheritdoc IJITResolver
     * @dev Adds JIT liquidity for a swap operation - only called by the hook
     * @dev NOTE: The add liquidity method is only called by the hook
     */
    function addLiquidity(SwapContext memory swapContext) external onlyWithHookInitialized() onlyRole(DEFAULT_ADMIN_ROLE) returns(uint256,uint256){
        //NOTE: The Hook needs to be the msg.sender
        //TODO: Further security checks using introspection for this ERC165
        
        return _addLiquidity(swapContext);
    }

    /**
     * @inheritdoc IJITResolver
     * @dev Removes JIT liquidity after swap completion
     */
    function removeLiquidity(LiquidityPosition memory liquidityPosition) onlyWithHookInitialized() onlyRole(DEFAULT_ADMIN_ROLE) external{
        _removeLiquidity(liquidityPosition.tokenId);
    }

    // ================================ INTERNAL FUNCTIONS ================================

    /**
     * @notice Internal function to add JIT liquidity based on swap context
     * @dev Virtual function to be implemented by concrete JIT resolver implementations.
     * Handles the actual liquidity addition logic including position creation and optimization.
     * @param swapContext The swap context containing swap parameters and market data
     * @return uint256 The token ID of the created JIT position
     * @return uint256 The amount of liquidity added
     */
    function _addLiquidity(SwapContext memory swapContext) internal virtual returns(uint256,uint256);

    /**
     * @notice Internal function to remove JIT liquidity
     * @dev Virtual function to be implemented by concrete JIT resolver implementations.
     * Handles the actual liquidity removal logic including fee collection and position cleanup.
     * @param tokenId The token ID of the JIT position to remove
     */
    function _removeLiquidity(uint256 tokenId) internal virtual;



}







