//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {FullMath} from "@uniswap/v4-core/src/libraries/FullMath.sol";
import {SafeCast} from "@uniswap/v4-core/src/libraries/SafeCast.sol";

import "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {PositionInfoLibrary, PositionInfo} from "@uniswap/v4-periphery/src/libraries/PositionInfoLibrary.sol";
import {Position} from "@uniswap/v4-core/src/libraries/Position.sol";
import {
    Currency,
    CurrencySettler
} from "@uniswap/v4-core/test/utils/CurrencySettler.sol";

import {
    PoolId,
    PoolIdLibrary,
    PoolKey
} from "@uniswap/v4-core/src/types/PoolId.sol";
import {StateLibrary} from "@uniswap/v4-core/src/libraries/StateLibrary.sol";
//==================================================================
import {BaseHook} from "@uniswap/v4-periphery/src/utils/BaseHook.sol";
import {Hooks} from "@uniswap/v4-core/src/libraries/Hooks.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";
//====================================================================

//==============================================================
import "../types/Shared.sol";
import {IPLPResolver} from "../interfaces/IPLPResolver.sol";
import {IJITResolver} from "../interfaces/IJITResolver.sol";
import {IParityTaxRouter} from "../interfaces/IParityTaxRouter.sol";
import {IFiscalPolicy} from "../interfaces/IFiscalPolicy.sol";
import {ILPOracle} from "../interfaces/ILPOracle.sol";
import {IParityTaxHook} from "../interfaces/IParityTaxHook.sol";
//==============================================================


import {Exttload} from "@uniswap/v4-core/src/Exttload.sol";
import {LiquidityMetrics} from "../LiquidityMetrics.sol";
import {IParityTaxExtt} from "../interfaces/IParityTaxExtt.sol";

/**
 * @title ParityTaxHookBase
 * @author ParityTax Team
 * @notice Abstract base contract providing core functionality for ParityTax hook system
 * @dev This contract implements transient storage management, position tracking, and access control
 * for the ParityTax hook system. It provides the foundation for managing JIT and PLP liquidity
 * commitments, fee collection, and tax distribution mechanisms.
 */
abstract contract ParityTaxHookBase is IParityTaxHook,Exttload,BaseHook, LiquidityMetrics{


    using SafeCast for *;
    using Position for address;
    using PositionInfoLibrary for PoolKey;
    using CurrencySettler for Currency;
    using PositionInfoLibrary for PositionInfo;
    using StateLibrary for IPoolManager;

    /// @notice PLP resolver contract for permanent liquidity provider operations
    IPLPResolver plpResolver;
    
    /// @notice JIT resolver contract for just-in-time liquidity operations
    IJITResolver jitResolver;
    
    /// @notice Position manager for liquidity position management
    IPositionManager lpm;
    
    /// @notice Fiscal policy contract for tax calculations and remittances
    IFiscalPolicy fiscalPolicy;
    
    /// @notice LP oracle for liquidity price information
    ILPOracle lpOracle;

    /// @notice ParityTaxExtt contract for transient storage operations
    IParityTaxExtt parityTaxExtt;


    /// @notice Mapping to track PLP block number commitments for liquidity withdrawal validation
    /// @dev TODO: This are to be migrated to enumerable mappings for iteration
    mapping(PoolId poolId => mapping(address owner => mapping(uint256 tokenId => uint48 blockNumberCommitment))) internal _plpBlockNumberCommitmnet;
    
    /// @notice Reserved for future use - mapping for withheld fees
    // mapping(PoolId poolId => mapping(address owner => mapping(uint256 tokenId => BalanceDelta delta))) internal _withheldFees;


    /**
     * @notice Modifier to ensure only the position manager can call certain functions
     * @param _router The address attempting to call the function
     */
    modifier onlyPositionManager(address _router){
        if (_router != address(lpm)) revert InvalidLiquidityRouterCaller();
        _;
    }

    /**
     * @notice Modifier to ensure only the position manager can call JIT-related functions
     * @param _router The address attempting to call the function
     * @dev Allows position manager or non-JIT operations
     */
    modifier onlyPositionManagerForJIT(address _router){
        if ( _router != address(lpm) && _tload_jit_tokenId() > uint256(0x00) ) revert InvalidLiquidityRouterCaller();
        _;
    }


    

    /**
     * @notice Initializes the ParityTaxHookBase with required dependencies
     * @dev Sets up the pool manager, position manager, LP oracle, and ParityTaxExtt for hook operations
     * @param _poolManager The Uniswap V4 pool manager contract
     * @param _lpm The position manager for liquidity operations
     * @param _lpOracle Oracle for liquidity price information
     * @param _parityTaxExtt The ParityTaxExtt contract for transient storage operations
     */
    constructor(
        IPoolManager _poolManager,
        IPositionManager _lpm,
        ILPOracle _lpOracle,
        IParityTaxExtt _parityTaxExtt
    ) BaseHook(_poolManager) LiquidityMetrics(_poolManager){
        lpm = _lpm;
        lpOracle = _lpOracle;
        parityTaxExtt = _parityTaxExtt;
    }

    /**
     * @inheritdoc IParityTaxHook
     * @dev TODO: Access control to be implemented
     */
    function setLiquidityResolvers(
        IPLPResolver _plpResolver,
        IJITResolver _jitResolver
    ) external {
        plpResolver = _plpResolver;
        jitResolver = _jitResolver;
    }

    /**
     * @inheritdoc IParityTaxHook
     * @dev TODO: Access control to be implemented
     */
    function setFiscalPolicy(
        IFiscalPolicy _fiscalPolicy
    ) external {
        fiscalPolicy = _fiscalPolicy;
    }


    /**
     * @inheritdoc BaseHook
     * @dev Defines which hooks are enabled for this contract
     */
    function getHookPermissions() public pure virtual override returns (Hooks.Permissions memory){
        return Hooks.Permissions({
            beforeInitialize: true,      // @dev NOTE: ILPOracle -> sync the internal price with the external one
            afterInitialize: false,  
            beforeAddLiquidity: true,    // @dev NOTE: Handles the commitment of PLP's and JIT's 
            afterAddLiquidity: true,     // @dev NOTE: Processes fee collection and remittance
            beforeRemoveLiquidity: true, // @dev NOTE: Validates commitment compliance
            afterRemoveLiquidity: true,  // @dev NOTE: Handles tax calculations and fee processing
            beforeSwap: true,            // @dev NOTE: Manages JIT liquidity addition and price tracking
            afterSwap: true,             // @dev NOTE: Processes JIT liquidity removal and fee collection
            beforeDonate: false,
            afterDonate: true,       // @dev NOTE: It allows for custom tax income distribution mechanisms among PLPs
            beforeSwapReturnDelta:false,  
            afterSwapReturnDelta: false,
            afterAddLiquidityReturnDelta: true, // @dev NOTE: Enables fee delta modifications
            afterRemoveLiquidityReturnDelta: true // @dev NOTE: Enables fee delta modifications
        });
    }

    /**
     * @notice Retrieves comprehensive liquidity position data
     * @dev Constructs a complete LiquidityPosition struct with all relevant information
     * @param poolKey The pool configuration data
     * @param lpType The type of liquidity provider (JIT or PLP)
     * @param owner The address of the position owner
     * @param tokenId The NFT token ID representing the position
     * @return liquidityPositionData Complete liquidity position information
     */
    function getLiquidityPosition(
        PoolKey memory poolKey,
        LP_TYPE lpType,
        address owner,
        uint256 tokenId
    ) public view returns (LiquidityPosition memory liquidityPositionData){
        PoolId poolId = poolKey.toId();

        uint256 liquidity = lpm.getPositionLiquidity(tokenId);
        
        PositionInfo positionInfo = lpm.positionInfo(tokenId);
        
        bytes32 lpTypePositionKey = address(lpm).calculatePositionKey(
            positionInfo.tickLower(),
            positionInfo.tickUpper(),
            bytes32(tokenId)
        );

        (,uint256 feeRevenueOn0, uint256 feeRevenueOn1) = poolManager.getPositionInfo(
            poolId,
            lpTypePositionKey
        );

        liquidityPositionData = LiquidityPosition({
                lpType: lpType,
                blockCommitment: lpType == LP_TYPE.PLP ? getPositionBlockNumberCommitment(poolId,owner,tokenId): JIT_COMMITMENT,
                owner: owner,
                tokenId: tokenId,
                positionKey: lpTypePositionKey,
                positionInfo: positionInfo,
                liquidity: liquidity,
                feeRevenueOnCurrency0: feeRevenueOn0,
                feeRevenueOnCurrency1: feeRevenueOn1
        });
    }

    // @dev TODO: This functions are to be protected to only be called by the parityTaxRouter or the taxController 
    
    /**
     * @inheritdoc IParityTaxHook
     */
    function tstore_plp_liquidity(int256 liquidityChange) external{
        parityTaxExtt.tstore_plp_liquidity(liquidityChange);
    }

    /**
     * @inheritdoc IParityTaxHook
     */
    function tstore_plp_feesAccrued(uint256 feesAccruedOn0, uint256 feesAccruedOn1) external{
        parityTaxExtt.tstore_plp_feesAccrued(feesAccruedOn0, feesAccruedOn1);
    }



    /**
     * @notice Internal function to store PLP liquidity change in transient storage
     * @dev Delegates to ParityTaxExtt contract for transient storage operations
     * @param liquidityChange The change in liquidity amount
     */
    function _tstore_plp_liquidity(int256 liquidityChange) internal virtual{
        parityTaxExtt.tstore_plp_liquidity(liquidityChange);
    }

    /**
     * @notice Internal function to store PLP fees accrued in transient storage
     * @dev Delegates to ParityTaxExtt contract for transient storage operations
     * @param feesAccruedOn0 The fees accrued on currency0
     * @param feesAccruedOn1 The fees accrued on currency1
     */
    function _tstore_plp_feesAccrued(uint256 feesAccruedOn0, uint256 feesAccruedOn1) internal virtual{
        parityTaxExtt.tstore_plp_feesAccrued(feesAccruedOn0, feesAccruedOn1);
    }

    /**
     * @notice Internal function to store PLP token ID in transient storage
     * @dev Delegates to ParityTaxExtt contract for transient storage operations
     * @param tokenId The PLP position token ID
     */
    function _tstore_plp_tokenId(uint256 tokenId) internal{
        parityTaxExtt.tstore_plp_tokenId(tokenId);
    }



    /**
     * @notice Internal function to store pre-swap sqrt price in transient storage
     * @dev Delegates to ParityTaxExtt contract for transient storage operations
     * @param beforeSwapSqrtPriceX96 The sqrt price before the swap
     */
    function _tstore_swap_beforeSwapSqrtPriceX96(uint160 beforeSwapSqrtPriceX96 ) internal{
        parityTaxExtt.tstore_swap_beforeSwapSqrtPriceX96(beforeSwapSqrtPriceX96);
    }

    /**
     * @notice Internal function to store pre-swap external sqrt price in transient storage
     * @dev Delegates to ParityTaxExtt contract for transient storage operations
     * @param beforeSwapExternalSqrtPriceX96 The external sqrt price before the swap
     */
    function _tstore_swap_beforeSwapExternalSqrtPriceX96(uint160 beforeSwapExternalSqrtPriceX96 ) internal{
        parityTaxExtt.tstore_swap_beforeSwapExternalSqrtPriceX96(beforeSwapExternalSqrtPriceX96);
    }




    /**
     * @notice Internal function to store JIT token ID in transient storage
     * @dev Delegates to ParityTaxExtt contract for transient storage operations
     * @param tokenId The JIT position token ID
     */
    function _tstore_jit_tokenId(uint256 tokenId) internal{
        parityTaxExtt.tstore_jit_tokenId(tokenId);
    }

    /**
     * @notice Internal function to store JIT fee revenue in transient storage
     * @dev Delegates to ParityTaxExtt contract for transient storage operations
     * @param feeRevenueOn0 The fee revenue on currency0
     * @param feeRevenueOn1 The fee revenue on currency1
     */
    function _tstore_jit_feeRevenue(
        uint256 feeRevenueOn0,
        uint256 feeRevenueOn1
    ) internal {
        parityTaxExtt.tstore_jit_feeRevenue(feeRevenueOn0, feeRevenueOn1);
    }

    /**
     * @notice Internal function to store JIT position info in transient storage
     * @dev Delegates to ParityTaxExtt contract for transient storage operations
     * @param positionInfo The JIT position information
     */
    function _tstore_jit_positionInfo(
        PositionInfo positionInfo
    ) internal{
        parityTaxExtt.tstore_jit_positionInfo(positionInfo);
    }

    /**
     * @notice Internal function to store JIT liquidity in transient storage
     * @dev Delegates to ParityTaxExtt contract for transient storage operations
     * @param liquidity The JIT liquidity amount
     */
    function _tstore_jit_liquidity(
        uint256 liquidity
    ) internal{
        parityTaxExtt.tstore_jit_liquidity(liquidity);
    }

    /**
     * @notice Internal function to store JIT position key in transient storage
     * @dev Delegates to ParityTaxExtt contract for transient storage operations
     * @param positionKey The JIT position key
     */
    function _tstore_jit_positionKey(
        bytes32 positionKey
    ) internal{
        parityTaxExtt.tstore_jit_positionKey(positionKey);
    }

    /**
     * @notice Internal function to store JIT owner in transient storage
     * @dev Delegates to ParityTaxExtt contract for transient storage operations
     * @param owner The JIT position owner address
     */
    function _tstore_jit_owner(
        address owner
    ) internal{
        parityTaxExtt.tstore_jit_owner(owner);
    }

    
    /**
     * @notice Internal function to store complete JIT liquidity position in transient storage
     * @dev Delegates to ParityTaxExtt contract for transient storage operations
     * @param jitLiquidityPosition The complete JIT liquidity position data
     */
    function _tstore_jit_liquidityPosition(LiquidityPosition memory jitLiquidityPosition) internal{
        parityTaxExtt.tstore_jit_liquidityPosition(jitLiquidityPosition);
    }

    /**
     * @notice Internal function to load PLP token ID from transient storage
     * @dev Uses IExttload to read from ParityTaxExtt contract
     * @return tokenId The PLP position token ID
     */
    function _tload_plp_tokenId() internal view returns(uint256 tokenId){
        bytes32 slot;
        assembly {
            slot := add(PLP_LIQUIDITY_POSITION_LOCATION, 0x03)
        }
        bytes32 value = parityTaxExtt.exttload(slot);
        tokenId = uint256(value);
    }

    /**
     * @notice Internal function to load pre-swap sqrt price from transient storage
     * @dev Uses IExttload to read from ParityTaxExtt contract
     * @return The sqrt price before the swap
     */
    function _tload_swap_beforeSwapSqrtPriceX96() internal view returns(uint160){
        bytes32 value = parityTaxExtt.exttload(PRICE_IMPACT_LOCATION);
        return uint160(uint256(value));
    }

    /**
     * @notice Internal function to load pre-swap external sqrt price from transient storage
     * @dev Uses IExttload to read from ParityTaxExtt contract
     * @return The external sqrt price before the swap
     */
    function _tload_swap_beforeSwapExternalSqrtPriceX96() internal view returns(uint160){
        bytes32 slot;
        assembly {
            slot := add(PRICE_IMPACT_LOCATION, 0x01)
        }
        bytes32 value = parityTaxExtt.exttload(slot);
        return uint160(uint256(value));
    }

    /**
     * @notice Internal function to load JIT token ID from transient storage
     * @dev Uses IExttload to read from ParityTaxExtt contract
     * @dev NOTE: This function is to be called during JIT Resolver removeLiquidity Flow
     * @return jitTokenId The JIT position token ID
     */
    function _tload_jit_tokenId() internal view returns(uint256 jitTokenId){
        bytes32 value = parityTaxExtt.exttload(JIT_LIQUIDITY_POSITION_LOCATION);
        jitTokenId = uint256(value);
    }

    /**
     * @notice Internal function to load JIT position info from transient storage
     * @dev Uses IExttload to read from ParityTaxExtt contract
     * @return jitPositionInfo The JIT position information
     */
    function _tload_jit_positionInfo() internal view returns(PositionInfo jitPositionInfo){
        bytes32 slot;
        assembly {
            slot := add(JIT_LIQUIDITY_POSITION_LOCATION, 0x02)
        }
        bytes32 value = parityTaxExtt.exttload(slot);
        jitPositionInfo = PositionInfo.wrap(uint256(value));
    }

    /**
     * @notice Internal function to load JIT position key from transient storage
     * @dev Uses IExttload to read from ParityTaxExtt contract
     * @return jitPositionKey The JIT position key
     */
    function _tload_jit_positionKey() internal view returns(bytes32 jitPositionKey){
        bytes32 slot;
        assembly {
            slot := add(JIT_LIQUIDITY_POSITION_LOCATION, 0x01)
        }
        jitPositionKey = parityTaxExtt.exttload(slot);
    }

    /**
     * @notice Internal function to load JIT liquidity from transient storage
     * @dev Uses IExttload to read from ParityTaxExtt contract
     * @return jitLiquidity The JIT liquidity amount
     */
    function _tload_jit_liquidity() internal view returns(uint256 jitLiquidity){
        bytes32 slot;
        assembly {
            slot := add(JIT_LIQUIDITY_POSITION_LOCATION, 0x03)
        }
        bytes32 value = parityTaxExtt.exttload(slot);
        jitLiquidity = uint256(value);
    }

    /**
     * @notice Internal function to load JIT fee revenue from transient storage
     * @dev Uses IExttload to read from ParityTaxExtt contract
     * @return The fee revenue on currency0 and currency1
     */
    function _tload_jit_feeRevenue() internal view returns(uint256,uint256){
        bytes32 slot0;
        bytes32 slot1;
        assembly {
            slot0 := add(JIT_LIQUIDITY_POSITION_LOCATION, 0x04)
            slot1 := add(JIT_LIQUIDITY_POSITION_LOCATION, 0x05)
        }
        bytes32 value0 = parityTaxExtt.exttload(slot0);
        bytes32 value1 = parityTaxExtt.exttload(slot1);
        
        return (uint256(value0), uint256(value1));
    }

    /**
     * @notice Internal function to load JIT owner from transient storage
     * @dev Uses IExttload to read from ParityTaxExtt contract
     * @return owner The JIT position owner address
     */
    function _tload_jit_owner() internal view returns(address owner){
        bytes32 slot;
        assembly {
            slot := add(JIT_LIQUIDITY_POSITION_LOCATION, 0x06)
        }
        bytes32 value = parityTaxExtt.exttload(slot);
        owner = address(uint160(uint256(value)));
    }



    /**
     * @notice Internal function to load complete JIT liquidity position from transient storage
     * @dev Constructs a complete LiquidityPosition struct from stored JIT data using IExttload
     * @return jitLiquidityPosition The complete JIT liquidity position data
     */
    function _tload_jit_liquidityPosition() internal view returns(LiquidityPosition memory jitLiquidityPosition){
        (uint256 feesOn0,uint256 feesOn1) = _tload_jit_feeRevenue();

        jitLiquidityPosition = LiquidityPosition({
            lpType: LP_TYPE.JIT,
            blockCommitment: JIT_COMMITMENT,
            owner: _tload_jit_owner(),
            tokenId: _tload_jit_tokenId(),
            positionKey: _tload_jit_positionKey(),
            positionInfo: _tload_jit_positionInfo(),
            liquidity: _tload_jit_liquidity(),
            feeRevenueOnCurrency0: feesOn0,
            feeRevenueOnCurrency1: feesOn1       
        });
    }

    /**
     * @notice Internal function to get pool ID and position key for liquidity operations
     * @dev Calculates the position key using the liquidity router and parameters
     * @param liquidityRouter The address of the liquidity router
     * @param poolKey The pool configuration data
     * @param liquidityParams The liquidity modification parameters
     * @return poolId The pool identifier
     * @return lpPositionKey The calculated position key
     */
    function _getPoolIdAndPositionKey(
        address liquidityRouter,
        PoolKey memory poolKey,
        ModifyLiquidityParams memory liquidityParams
    ) internal view returns(PoolId poolId, bytes32 lpPositionKey){
        poolId = poolKey.toId();
        
        lpPositionKey = liquidityRouter.calculatePositionKey(
            liquidityParams.tickLower,
            liquidityParams.tickUpper,
            liquidityParams.salt
        );
    }

    /**
     * @notice Locks liquidity by setting a block number commitment
     * @dev Prevents withdrawal until the commitment period expires
     * @param poolId The pool identifier
     * @param tokenId The position token ID
     * @param owner The position owner address
     * @param blockNumberCommitment The block number when liquidity can be withdrawn
     */
    function _lockLiquidity(
        PoolId poolId,
        uint256 tokenId,
        address owner,
        uint48 blockNumberCommitment
    ) internal virtual {
        _plpBlockNumberCommitmnet[poolId][owner][tokenId] =blockNumberCommitment; 
    }





    /**
     * @notice Clears the block number commitment for a position
     * @dev Allows immediate withdrawal by removing the commitment constraint
     * @param poolId The pool identifier
     * @param owner The position owner address
     * @param tokenId The position token ID
     */
    function _clearPositionBlockNumberCommitment(
        PoolId poolId,
        address owner,
        uint256 tokenId
    ) internal virtual {
        _plpBlockNumberCommitmnet[poolId][owner][tokenId] = NO_COMMITMENT;
    }



    function getPositionBlockNumberCommitment(
        PoolId poolId,
        address owner,
        uint256 tokenId
    ) public virtual view returns(uint48){
        return _plpBlockNumberCommitmnet[poolId][owner][tokenId];
    }







    /**
     * @notice Placeholder function for current price retrieval
     * @dev TODO: This is a placeholder, to be implemented
     * @return The current price (currently returns 1 as placeholder)
     */
    function getCurrentPrice() public pure returns(uint256){
        return 1;
    }

    /**
     * @inheritdoc IParityTaxHook
     */
    function positionManager() external view returns(IPositionManager){
        return lpm;
    }

    /**
     * @inheritdoc IParityTaxHook
     */
    function FiscalPolicy() external view returns(IFiscalPolicy){
        return fiscalPolicy;
    }

}