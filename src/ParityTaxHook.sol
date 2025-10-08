//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title ParityTaxHook
 * @author ParityTax Team
 * @notice Main hook contract implementing Uniswap V4's hook system for equitable fee distribution
 * @dev This contract manages liquidity commitments, fee collection, and tax distribution between JIT and PLP providers
 * @dev The _afterRemoveLiquidity function is heavily inspired by LiquidityPenaltyHook.sol from OpenZeppelin Uniswap Hooks
 */
import {Plan, Planner} from "@uniswap/v4-periphery/test/shared/Planner.sol"
import {PositionConfig} from "@uniswap/v4-periphery/test/shared/PositionConfig.sol";

//=================================================================
import {SqrtPriceMath} from "@uniswap/v4-core/src/libraries/SqrtPriceMath.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {TickBitmap} from "@uniswap/v4-core/src/libraries/TickBitmap.sol";
import {LiquidityAmounts} from "@uniswap/v4-periphery/src/libraries/LiquidityAmounts.sol";
import {StateLibrary} from "@uniswap/v4-core/src/libraries/StateLibrary.sol";
import {TransientStateLibrary} from "@uniswap/v4-core/src/libraries/TransientStateLibrary.sol";
//=========================================================================

import {ModifyLiquidityParams} from "@uniswap/v4-core/src/types/PoolOperation.sol";
import {BeforeSwapDelta, BeforeSwapDeltaLibrary} from "@uniswap/v4-core/src/types/BeforeSwapDelta.sol";
import {PositionConfig} from "@uniswap/v4-periphery/test/shared/PositionConfig.sol";
//==================================================================

import {Address} from "@openzeppelin/contracts/utils/Address.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";


//======================================================================
import {Constants} from "@uniswap/v4-core/test/utils/Constants.sol";
import {IV4Quoter} from "@uniswap/v4-periphery/src/interfaces/IV4Quoter.sol";
import {V4Quoter} from "@uniswap/v4-periphery/src/lens/V4Quoter.sol";
import {QuoterRevert} from "@uniswap/v4-periphery/src/libraries/QuoterRevert.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";
import {IAllowanceTransfer} from "@uniswap/v4-periphery/lib/permit2/src/interfaces/IAllowanceTransfer.sol";
//============================================================================
import "./interfaces/IParityTaxHook.sol";
import "./types/Shared.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import "./base/ParityTaxHookBase.sol";
import {IParityTaxExtt} from "./interfaces/IParityTaxExtt.sol";
//===================================================================


// ======================== Currency Related Imports==================================
import{
    Currency,
    CurrencySettler
} from "@uniswap/v4-core/test/utils/CurrencySettler.sol";
// import {DeltaResolver} from "@uniswap/v4-periphery/src/base/DeltaResolver.sol";
import {CurrencyDelta} from "@uniswap/v4-core/src/libraries/CurrencyDelta.sol";

// =============== External Dependencies ============================
import {
    FeeRevenueInfo,
    FeeRevenueInfoLibrary
} from "./types/FeeRevenueInfo.sol";
import {
    SwapIntent,
    SwapIntentLibrary
} from "./types/SwapIntent.sol";
//TODO: Do we need a manager also for the PLP ?? ...

import {ILiquidityMetrics} from "./interfaces/ILiquidityMetrics.sol";

//logging-Debugging

import {console2} from "forge-std/Test.sol";


import {IJITResolver} from "./interfaces/IJITResolvers.sol";
import {IPLPResolver} from "./interfaces/IPLPResolver.sol";
import {IFiscalPolicy} from "./interfaces/IFiscalPolicy.sol";

import {LiquidityMath} from "@uniswap/v4-core/src/libraries/LiquidityMath.sol";

import {Exttload} from "@uniswap/v4-core/src/Exttload.sol";

import "@uniswap/v4-core/types/BalanceDelta.sol";

import {EnumerableMap} from "@openzeppelin/contracts/utils/struct/EnumerableMap.sol";

import {IPoolAdminEntryPoint} from "./interfaces/IPoolAdminEntryPoint.sol";
import {ILiquidityEntryPoint} from "./interfaces/ILiquidityEntryPoint.sol";

contract ParityTaxHook is IParityTaxHook, ParityTaxHookBase, Exttload{
    using SafeCast for *;
    using FeeRevenueInfoLibrary for *;
    using SwapIntentLibrary for *;
    using Position for address;
    using Address for address;
    using QuoterRevert for bytes;
    using StateLibrary for IPoolManager;
    using TransientStateLibrary for IPoolManager;
    using SqrtPriceMath for uint160;
    using LiquidityAmounts for uint160;
    using TickMath for uint160;
    using TickMath for int24;
    using TickBitmap for int24;
    using PoolIdLibrary for PoolKey;
    using PositionInfoLibrary for PoolKey;
    using PositionInfoLibrary for PositionInfo;
    using BalanceDeltaLibrary for BalanceDelta;
    using CurrencySettler for Currency;
    using CurrencyDelta for Currency;
    using LiquidityMath for uint128;
    using Planner for Plan;


    error swapSimulation(int24 tick, uint128 jitLiquidity);

    


    mapping(PoolId => IPoolAdminEntryPoint) poolAdmins;
    mapping(PoolId => IFiscalPolicy) fiscalPolicies;
    mapping(PoolId => ILPOracle) externalMarketOracles;
    
    // NOTE: This stores the tokens as the keys
    // but the tokens are accessible since this is a 
    // enumerable mapping
    mapping(PoolId => EnumerableMap.UintToUintMap) plpPositions;




    
    
    modifier onlyWithPoolAdmin(PoolKey memory poolKey){
        if (address(poolAdmins[poolKey.toId()]) == address(0x00)){
            revert("Pool Governance Not Set"); 
        }
        _;
    }

    modifier onlyAfterCommitmentExpired(PoolKey memory poolKey, uint256 tokenId){
        
        (,uint48 liquidityCommitment) = plpPositions[poolKey.toId()].tryGet(bytes32(tokenId));

        if (uint48(block.number) < liquidityCommitment) revert("Liquidity commitment has not ended");
        _;
    }


    /**
     * @notice Initializes the ParityTaxHook with required dependencies
     * @dev Sets up the pool manager, position manager, LP oracle, and ParityTaxExtt for hook operations
     * @param _poolManager The Uniswap V4 pool manager contract
     * @param _lpm The position manager for liquidity operations
     * @param _lpOracle Oracle for liquidity price information
     * @param _parityTaxExtt The ParityTaxExtt contract for transient storage operations
     * @dev WARNING: The ParityTaxRouter is not needed as any router that calls the swap/modifyLiquidity
     * with the right hookData and no claims is valid
     */
    constructor(
        IPoolManager _poolManager,
        IPositionManager _lpm
    ) ParityTaxHookBase(
        _poolManager,
        _lpm
    ) 
    {

    }

    function setPoolAdmin(PoolKey calldata poolKey, IPoolAdminEntryPoint poolAdmin) external{
        poolAdmins[poolKey.toId()] = poolAdmin;
    }

    /**
     * @inheritdoc IParityTaxHook
     * @dev TODO: Access control to be implemented
     */
    function setLiquidityAggreagtors(
        IPLPResolver _plpResolver,
        IJITResolver _jitResolver
    ) external {
        plpResolver = _plpResolver;
        jitResolver = _jitResolver;
    }



    /**
     * @notice Handles pre-initialization logic for new pools
     * @dev WARNING: Here the deployer sets governance that can update the fiscal policy tax calculation
     * and also manager oracle dependencies initialization
     */
    function _beforeInitialize(
        address sender, //NOTE: PoolInitialization router
        PoolKey calldata poolKey,
        uint160
    ) internal virtual override returns (bytes4) {
        PoolId poolId = poolKey.toId();
        
        ILPOracle externalMarketOracle = IGovernace(sender).assignExternalMarketOracle(poolKey);
        externalMarketOracles[poolId] = externalMarketOracle;
        uint256 externalMarketPrice = externalMarketOracles[poolId].getExternalMarketPrice(poolKey);
        // TODO: Logic of internal swap to align prices ...
        return IHooks.beforeInitialize.selector;
    }
    
    // NOTE: This signals the governance to create a fiscal policy
    function _afterInitialize(
        address sender,
        PoolKey calldata poolKey,
        uint160 sqrtPriceX96,
        int24 tick
    )
        internal
        override
        onlyWithGovernance(poolKey)
        returns (bytes4)
    {
        IFiscalPolicy marketFiscalPolicy = IGovernance(sender).assignFiscalPolicy(poolKey);
        fiscalPolicies[poolKey.toId()] = marketFiscalPolicy;


        return _afterInitialize(sender, key, sqrtPriceX96, tick);
    }



    /**
     * @notice Executes before swap logic including JIT liquidity addition and price tracking
     * @dev Handles JIT liquidity provision and stores pre-swap price data for accurate tracking
     * @dev All this data is passed to the JIT Resolver, which returns the JIT liquidity that is willing to fulfill
     * @dev This is to be improved to store beforeSwap prices on transient storage and emit the event on afterSwap for further accuracy
     * @dev WARNING: This is a placeholder implementation. Correct calculation needs to be done for PLP liquidity determination
     */
    function _beforeSwap(
        address swapRouter ,
        PoolKey calldata poolKey, 
        SwapParams calldata swapParams,
        bytes calldata hookData
    ) internal virtual onlyWithGovernance(poolKey) override returns (bytes4, BeforeSwapDelta, uint24)
    {   

        uint256 jitTokenId = _tload_jit_tokenId();

        // NOTE: This is becase the simulateSwap does not have stored the token id, otherwise this 
        // call will be infinite recursion
        if (jitTokenId == uint256(0x00)){

            PoolId poolId = poolKey.toId();        
            
            (int24 tickAfter,uint128 liquidityForSwap) = _getSwapSimulationData(poolKey, swapParams);
            // NOTE: This tracks the internal price of the pool before swap
            (,int24 tickBefore,,) = poolManager.getSlot0(poolId);
            
            // NOTE: This requests the external price of the pair before swap, the narrower the
            // range the deepest the market => Does not have to coincide with the internal range

            (int24 tickBeforeExternal,int24 tickAfterExternal) = externalMarketOracles[poolId].getExternalTickInfo(poolKey);

            uint128 tickRangeAvailableLiquidity = _getTickRangeLiquidity(poolKey, tickLower, tickUpper);
            PositionConfig memory default_jit_positionConfig = PositionConfig(poolKey,tickLower, tickUpper);

            PositionInfo externalMarketPosition = poolKey.initialize(tickBeforeExternal, tickAfterExternal);


            (
                PositionConfig memory jitPositionConfig,
                uint128 jitLiquidity,
                address liquidityManager,
                bytes memory data
            
            ) = jitResolver.beforeAddLiquidity(
                poolId,
                swapParams,
                externalMarketPosition,
                default_jit_positionConfig,
                liquidityForSwap,
                tickRangeAvailableLiquidity
            );
            // NOTE: The data passed can not match the Commitment length
            // other wise it will trigger the PLP logic
            // on beforeAddLiquidity
            _mintUnlocked(
                jitPositionConfig,
                jitLiquidity,
                liquidityManager,
                data
            );

                
            PositionInfo jitPosition = poolKey.initialize(tickBefore, tickAfter);
            // NOTE: Now with liquidity minted, we can simulate the swap 
            // again to get the actual plp liquidity that will be enttered
            // for this swap


            // NOTE: This should consider the JIT liqudity fullfiulling the portion requested to fulfill
            // thus, making the calculation over the unfulfilled portion of the swap

            // NOTE: IF THIS IS NOT THE CASE WE MIGHT CONSIDER UWSING BEFORE SWAP DELTA
            // TO GUARANTE THE JIT FULLFILLS THE REQUESTED

            (,uint128 plpLiquidity) = _getSwapSimulationData(poolKey, swapParams);



            _tstore_jit_tokenId(jitPositionTokenId);
            
            _tstore_swap_externalMarketPosition(externalMarketPosition);
        
            emit LiquidityOnSwap(
                PositionInfo.unwrap(jitPosition),
                PoolId.unwrap(poolId),
                jitLiquidity
                plpLiquidity
            );

        }
 
         


        return (IHooks.beforeSwap.selector, BeforeSwapDeltaLibrary.ZERO_DELTA, uint24(0x00));
    }
    


    /**
     * @notice Handles post-swap operations including JIT liquidity removal and fee collection
     * @dev Processes JIT liquidity removal, calculates fee revenue, and remits to fiscal policy
     * @dev WARNING: This is a placeholder implementation for external price calculation
     * @dev WARNING: This is to be improved to include the actual converted external price
     * @dev WARNING: The JIT fee revenue has been earned on the asset losing appreciation. This needs to be corrected so it converts to a numeraire
     */
    function _afterSwap(
        address swapRouter,
        PoolKey calldata poolKey,
        SwapParams calldata swapParams,
        BalanceDelta swapDelta,
        bytes calldata hookData
    ) internal virtual onlyWithGovernance(poolKey) override returns (bytes4, int128)
    {
        // =====================JIT============================//
        uint256 jitTokenId = _tload_jit_tokenId();

        if (jitTokenId > uint256(0x00)){

            PoolId poolId = poolKey.toId();
            // NOTE: beforeSwapTick == jitPosition.tickLower && afterSwapTick == jitPosition.tickUpper
            // Or backwards depending on the direction of the swap, the point is that the information is there
            (, int24 afterSwapTick,, ) = poolManager.getSlot0(poolId);
            PositionInfo externalMarketPositionInfo = _tload_swap_externalMarketPosition();
            PositionInfo jitPositionInfo = lpm.positionInfo(jitTokenId);

            PositionConfig jitPositionConfig = PositionConfig(
                poolKey,
                jitPositionInfo.tickLower(),
                jitPositionInfo.tickUpper()
            );

                        
            // NOTE: hookData can be passed to the JIT Resolver for any actions that do not involve
            // breaking the taxing protocol (like withdrwing fee revenue)

            _burnUnlocked(
                jitTokenId,
                jitPositionConfig,
                hookData
            );
        }
        //====================================================//


        return (IHooks.afterSwap.selector, int128(0x00));
    }

    /**
     * @notice Manages liquidity addition with commitment validation and JIT/PLP routing
     * @dev Handles both JIT and PLP liquidity commitments based on hook data and current state
     * @dev This applies for hooks where the user provides valid hookData. This needs to be considered
     */
    function _beforeAddLiquidity(
        address liquidityRouter,
        PoolKey calldata poolKey,
        ModifyLiquidityParams calldata liquidityParams,
        bytes calldata hookData
    ) internal virtual override onlyWithGovernance(poolKey) returns (bytes4)
    {
        
        // TODO: There needs to be a checkesr to route the call from JIT, PLP resolvers

        // NOTE: This is the flow for other routers not the resolvers
        
        //NOTE: This applies for hooks where the user puts valid hookData. This needs to be considered 
        PoolId poolId = poolKey.toId();
        uint256 jitTokenId = _tload_jit_tokenId();
        Commitment memory plpCommitment;
        if (hookData.length == COMMITMENT_LENGTH){
            
            Commitment memory lpCommitment = abi.decode(
                hookData,
                (Commitment)
            );
            // NOTE: This is a PLP commiting liquidity
            if (lpCommitment.blockNumberCommitment >= MIN_PLP_BLOCK_NUMBER_COMMITMENT && jitTokenId == uint256(0x00)){
                plpCommitment = lpCommitment;  
            
                plpCommitment.blockNumberCommitment += uint48(block.number);
        
            }
        }
        //==================================================================//
        
        return IHooks.beforeAddLiquidity.selector;
    }

    

    /**
     * @notice Handles post-liquidity addition fee collection and remittance
     * @dev Processes PLP fee revenue and remits to fiscal policy, stores JIT fee revenue in transient storage
     * @dev This needs to be the position manager associated with the liquidity operator
     */
    function _afterAddLiquidity(
        address liquidityRouter,
        PoolKey calldata poolKey,
        ModifyLiquidityParams calldata liquidityParams,
        BalanceDelta,
        BalanceDelta feeDelta,
        bytes calldata hookData
    ) internal virtual override onlyWithGovernance(poolKey) returns (bytes4, BalanceDelta) {
        
        uint256 jitTokenId = _tload_jit_tokenId();
        uint256 tokenId = uint256(liquidityParams.salt);
        //==========================PLP==============================//
        if (hookData.length == COMMITMENT_LENGTH && jitTokenId == uint256(0x00) ){
        
            uint256 plpPositionTokenId = lpm.nextTokenId() > uint256(0x01) ? lpm.nextTokenId() - uint256(0x01):lpm.nextTokenId();
            
            assert(tokenId == plpPositionTokenId);

            plpPositions[poolId].set(plpPositionTokenId, plpCommitment.blockNumberCommitment);
            


        }
        //==========================================================//

        return (IHooks.afterAddLiquidity.selector, BalanceDeltaLibrary.ZERO_DELTA);
    }



    /**
     * @notice Validates liquidity removal permissions and commitment compliance
     * @dev Handles PLP liquidity removal validation and commitment expiration checks
     */
    function _beforeRemoveLiquidity(
        address liquidityRouter,
        PoolKey calldata poolKey,
        ModifyLiquidityParams calldata liquidityParams,
        bytes calldata hookData
    )
    internal
    virtual
    override
    onlyWithGovernance(poolKey)
    onlyAfterCommitmentExpired(poolKey, uint256(liquidityParams.salt))
    returns (bytes4)
    {
        
        return IHooks.beforeRemoveLiquidity.selector;
    }




    /**
     * @notice Handles post-liquidity removal operations and fee processing
     * @dev Processes JIT fee revenue and handles tax calculations for liquidity removal
     * @dev This tokenId is just for internal reference because the positionManager burns the position before modifyingLiquidity
     * @dev This informs the tax controller what kind of LP this is
     * @dev If there is a tax liability to be applied but there are no active liquidity positions in range to receive the donation, then the liquidity removal is not possible and the offset must be awaited
     * @dev WARNING: This is where accrueCredit gets called and assigns the right rewards to PLPs based on their commitment
     */
    function _afterRemoveLiquidity(
        address liquidityRouter,
        PoolKey calldata poolKey,
        ModifyLiquidityParams calldata liquidityParams,
        BalanceDelta delta,
        BalanceDelta feeRevenueDelta,
        bytes calldata hookData
    ) internal virtual override onlyWithGovernance(poolKey) onlyPositionManager(liquidityRouter) returns (bytes4, BalanceDelta) {
        

        PoolId poolId = poolKey.toId();
        uint256 jitTokenId = _tload_jit_tokenId();
        // NOTE: This token does not trak enything now
        // but works as a signal to indicate this is a JIT liquidity removal
        if (jitTokenId > uint256(0x00)){
            (uint24 taxRateOnX0, uint24 taxRateOnX1) = fiscalPolicies[poolId].calculateOptimalTax(delta, feeRevenueDelta);

            // NOTE: Based on this taxRate we do deduction
            BalanceDelta taxedjitRevenueDelta = toBalanceDelta(
                feeRevenueDelta.amount0()*int128(1-taxRateOnX0),
                feeRevenueDelta.amount1()*int128(1-taxRateOnX1)
            );

            if (poolManager.getLiquidity(poolId) == uint128(0x00)) revert("Not PLP Liquidty to reward");

            BalanceDelta delta = poolManager.donate(
                poolKey,uint256(uint128(taxedjitRevenueDelta.amount0())),uint256(uint128(taxedjitRevenueDelta.amount1())), hookData
            );
        }

        //=========================================PLP==============================================
        bool ok = plpPositions[poolId].remove(uint256(liquidityParams.salt));

        return (this.afterRemoveLiquidity.selector, taxedjitRevenueDelta);

    }
    
 

    /**
     * @notice Handles post-donation operations for credit accrual and PLP rewards
     * @dev Processes donations and assigns rewards to PLPs based on their commitment
     * @dev WARNING: This is where accrueCredit gets called and assigns the right rewards to PLPs based on their commitment
     */
    function _afterDonate(
        address sender, 
        PoolKey calldata poolKey,
        uint256 totalDonatedAmount0,
        uint256 totalDonateAmount1, 
        bytes calldata hookData
    ) internal virtual onlyWithGovernance(poolKey) override returns (bytes4){
        PoolId poolId = poolKey.toId();
        
        // NOTE: THis assigns a portion of revenue to the PLP
        // this portion is then queried beforeRemoveing liquidity

        // NOTE: The sum of endowments need to equal the total donated
        // 
        fiscalPolicies[poolId].accrueCredit(
            poolKey,
            plpPositions,
            totalDonatedAmount0,
            totalDonatedAmount1,
            hookData
        );

        return IHooks.afterDonate.selector;
    }

    /**
     * @notice Returns the ParityTaxExtt instance for transient storage operations
     * @dev This allows external contracts to access the transient storage through ParityTaxExtt
     * @return The ParityTaxExtt contract instance
     */
    function getParityTaxExtt() external view returns (IParityTaxExtt) {
        return parityTaxExtt;
    }



    // TODO: THis can be modified so it retrieves the bytes with all the needed
    // data
    function _getSimulatedSwapData(
        PoolKey calldata poolKey,
        SwapParams calldata swapParams
    ) internal returns(int24 tickAfter, uint128 liquidityNeededForSwap){

        try this.simulateSwap(poolKey,swapParams){
            revert("simulate swap should revert");
        } catch (bytes memory){
            // Decode the selector (first 4 bytes)
            bytes4 selector = bytes4(reason);

            if (selector != OnJITLiquiditySwap.selector) {
                revert("returned selector should be OnJITLiquiditySwap");
            }

            // Decode the uint24 value (assuming it's at the end)
            assembly {
                // If we're looking at the last 32 bytes, we need to position our pointer
                // reason + 32 (to skip length) + reason.length - 32 (to get to the last 32 bytes)
                let lastWordPtr := add(add(reason, 32), sub(mload(reason), 32))

                // For uint152, we only need the last 19 bytes of the last word
                // This assumes the uint24 is right-aligned in the last word
                let lastWord := mload(lastWordPtr)

                // Mask to get only the last 19 bytes (152 bits)
                tickAfter := and(lastWord, 0xFFFFFF)
            }
        }
    }





    // NOTE: This a util function to get price impact data beforeSwap
    // for JIT
    function simulateSwap(
        PoolKey calldata poolKey,
        SwapParams calldata swapParams
    ) external returns (int24 afterSwapTick, uint128 liquidityNeededForSwap){
        if (msg.sender != address(this)){
            revert("simulateSwap can only be called by the hook");
        }
        bool isExactInput = swapParams.amountSpecified < 0;
        (uint160 sqrtPriceBefore,int24 tickBefore,,) = poolManager.getSlot0(poolKey.toId());
        

        BalanceDelta swapDelta = poolManager.swap(poolKey, swapParams, Constants.ZERO_BYTES);
        // NOTE: THe positive is the outputt amoutnt
       
         
        (uint160 sqrtPriceAfter,int24 tickAfter,,) = poolManager.getSlot0(poolKey.toId());
        
        if (swapDelta.amount0() > int128(0x00)){
             liquidityNeededForSwap = sqrtPriceBefore.getLiquidityForAmount0(
                sqrtPriceAfter,
                uint256(uint128(swapDelta.amount0()))
            );
        } else if (swapDelta.amount1() > int128(0x00)){
            liquidityNeededForSwap = sqrtPriceBefore.getLiquidityForAmount1(
                sqrtPriceAfter,
                uint256(uint128(swapDelta.amount1()))
            );
        }
        revert swapSimulation(tickAfter,liquidityNeededForSwap);
    }

    function _getTickRangeLiquidity(
        PoolKey calldata poolKey,
        int24 tickLower,
        int24 tickUpper
    ) internal returns (uint128 tickRangeLiquidity){
        
        PoolId poolId = poolKey.toId();
        (uint128 initialLiquidity,,,) = poolManager.getTickInfo(poolId,tickLower);
        uint24 tickDelta = uint256(uint24(tickUpper-tickLower));
        
        int24 tick = tickLower + int24(poolKey.tickSpacing);
        uint128 _tickRangeLiquidity = initialLiquidity;
        
        while(tick <=tickUpper){
            (,int128 tickLiquidityAdded,,) = poolManager.getTickInfo(poolId,tick);
            _tickRangeLiquidity = _tickRangeLiquidity.addDelta(tickLiquidityAdded);
        }

        tickRangeLiquidity = _tickRangeLiquidity;
    }  

    function _mintUnlocked(
        PositionConfig memory config,
        uint256 liquidity,
        address recipient,
        bytes memory hookData
    ) internal virtual {
        Plan memory planner = Planner.init();
        {
            planner.add(
                Actions.MINT_POSITION,
                abi.encode(
                    config.poolKey,
                    config.tickLower < config.tickUpper ?config.tickLower:config.tickUpper,
                    config.tickLower < config.tickUpper ?config.tickUpper:config.tickLower,
                    liquidity,
                    MAX_SLIPPAGE_INCREASE,
                    MAX_SLIPPAGE_INCREASE,
                    recipient,
                    hookData
                )
            );
            planner.add(
                Actions.CLOSE_CURRENCY,
                abi.encode(config.poolKey.currency0)
            );
            planner.add(
                Actions.CLOSE_CURRENCY, abi.encode(config.poolKey.currency1)
            );
        }
        
        lpm.modifyLiquiditiesWithoutUnlock(planner.actions, planner.params);
    }

    // NOTE: The JIT needs to make the approval for the

    // msg.sender of this function wichh is the hook, this needs to be
    // done on beforeSwap

    function _burnUnlocked(
        uint256 tokenId,
        PositionConfig memory config
        bytes memory data
    ) internal virtual {
        Plan memory planner = Planner.init();
        planner.add(
            Actions.BURN_POSITION,
            abi.encode(
                tokenId,
                MIN_SLIPPAGE_DECREASE,
                MIN_SLIPPAGE_DECREASE,
                data
            )
        );

        planner.add(
            Actions.CLOSE_CURRENCY,
            abi.encode(config.poolKey.currency0)
        );
        planner.add(
            Actions.CLOSE_CURRENCY, 
            abi.encode(config.poolKey.currency1)
        );

        lpm.modifyLiquiditiesWithoutUnlock(planner.actions, planner.params);
    }
      

}



