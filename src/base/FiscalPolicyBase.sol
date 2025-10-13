// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title FiscalPolicyBase
 * @author ParityTax Team
 * @notice Abstract base contract for fiscal policy implementation using reactive network architecture
 * @dev This contract serves as the bridge between IParityTaxHook events and IFiscalPolicy implementation,
 * enabling optimal taxation calculations through real-time event processing. It implements the reactive
 * network pattern for forwarding event data from ParityTax hooks to fiscal policy for dynamic tax rate
 * calculation and fee distribution.
 * @dev Inherits from UUPSUpgradeable for upgradeable fiscal policy implementations and AbstractCallback
 * for reactive network event processing. Critical component in the equitable fee distribution system.
 * @custom:security-contact security@paritytax.com
 */

import "../interfaces/IFiscalPolicy.sol";
import {FeeRevenueInfoLibrary} from "../types/FeeRevenueInfo.sol";
import {BalanceDelta, BalanceDeltaLibrary} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {EnumerableMap} from "@openzeppelin/contracts/utils/structs/EnumerableMap.sol";
import {PoolKey,PoolId,PoolIdLibrary} from "@uniswap/v4-core/src/types/PoolId.sol";

import {ILPOracle} from "../interfaces/ILPOracle.sol";
import {IParityTaxRouter} from "../interfaces/IParityTaxRouter.sol";
import {ISubscriber} from "@uniswap/v4-periphery/src/interfaces/ISubscriber.sol";
import {IParityTaxExtt} from "../interfaces/IParityTaxExtt.sol";

import "../types/Shared.sol"; 

import {Address} from "@openzeppelin/contracts/utils/Address.sol";
import {FullMath} from "@uniswap/v4-core/src/libraries/FullMath.sol";
import {SafeCast} from "@uniswap/v4-core/src/libraries/SafeCast.sol";

//===================================PROXY=======================================
import "@openzeppelin-upgradeable/contracts/proxy/utils/UUPSUpgradeable.sol";

//============================REACTIVE NETWORK =================================

import {AbstractCallback} from "@reactive-network/abstract-base/AbstractCallback.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";
import {IParityTaxHook} from "../interfaces/IParityTaxHook.sol";

import {console2} from "forge-std/Test.sol";

import {Planner, Plan} from "@uniswap/v4-periphery/test/shared/Planner.sol";
import {Actions} from "@uniswap/v4-periphery/src/libraries/Actions.sol";
import {
    PoolId,
    PoolIdLibrary,
    PoolKey
} from "@uniswap/v4-core/src/types/PoolId.sol";

import {AccessControlEnumerable} from "@openzeppelin/contracts/access/extensions/AccessControlEnumerable.sol";

// NOTE: This is the entry point for poolAdmins to define Tax Strategies on pools
abstract contract FiscalPolicyBase is IFiscalPolicy, AccessControlEnumerble{
    using PoolIdLibrary for PoolKey;
    using FeeRevenueInfoLibrary for FeeRevenueInfo;
    using PositionInfoLibrary for PositionInfo;
    using Address for address;
    using SafeCast for *;
    using BalanceDeltaLibrary for BalanceDelta;

    // NOTE: They tax strategies can be ieither uniform (ad-valorem) or have custom functionality

    address immutable poolFactory;
    mapping(bytes32 poolId => ITaxHook taxStrategy) taxStrategies;




    constructor(address _poolFactory){
        poolFactory = _poolFactory;
    }

    function createTaxStrategy(bytes32 poolId) external returns(ITaxHook){
        // NOTE: It needs to do deployment (deterministic)
    }

    function _createTaxStrategy(bytes32 poolId) internal virtual returns(ITaxHook);


    function createPool(bytes calldata data) external returns(bytes memory){

    }

    function _onCreatePool

    





    // The pool deployer MUST define the custom taxSTrategy on beforeInitialize 
    // The FiscalPolicy base MUST give all information to taxStrategy to manage th Tax data structure



    // A poolId only has 

    // ================================ STORAGE CONSTANTS ================================

    // ================================ STATE VARIABLES ================================
    
    /// @notice Liquidity provider oracle for price and liquidity data
    ILPOracle _lpOracle;
    
    /// @notice Uniswap V4 position manager for liquidity operations
    IPositionManager lpm;
    
    /// @notice ParityTax hook contract for event data and reactive network integration
    IParityTaxHook parityTaxHook;

    // ================================ CONSTRUCTOR ================================

    /**
     * @notice Initializes the FiscalPolicyBase with reactive network dependencies
     * @dev Sets up the reactive network callback system and core dependencies for
     * optimal taxation calculations. This constructor establishes the bridge between
     * IParityTaxHook events and IFiscalPolicy implementation.
     * @param _callbackSender The address authorized to send reactive network callbacks
     * @param __lpOracle The liquidity provider oracle for price and liquidity data
     * @param _lpm The Uniswap V4 position manager for liquidity operations
     * @param _parityTaxHook The ParityTax hook contract for event data integration
     */
    constructor(
        address _callbackSender,
        ILPOracle __lpOracle,
        IPositionManager _lpm,
        IParityTaxHook _parityTaxHook
    ) AbstractCallback(_callbackSender){
        _lpOracle = __lpOracle;
        lpm = _lpm;
        parityTaxHook = _parityTaxHook;
    }

    // ================================ EXTERNAL FUNCTIONS ================================

    /**
     * @inheritdoc IFiscalPolicy
     * @dev Processes fee revenue remittance and applies taxation based on commitment type
     */

     // TODO: This can be simplified to just call the _calculateTaxPayment function
    // after retriving the tax rate from transient storage calculated and stored
    // by the calculateOptimalTax function
    function remit(PoolId poolId,FeeRevenueInfo feeRevenueInfo) external returns(BalanceDelta){
        
        if (feeRevenueInfo.commitment() == JIT_COMMITMENT){
            _applyTax(poolId,feeRevenueInfo);

        }
        return BalanceDeltaLibrary.ZERO_DELTA;

    }


    // ================================ INTERNAL FUNCTIONS ================================

    /**
     * @notice Applies tax to JIT liquidity provider fee revenue
     * @dev Calculates tax payment and donates it to the pool, ensuring equitable fee distribution
     * @param poolId The pool identifier for tax application
     * @param feeRevenueInfo The fee revenue information for tax calculation
     */
    function _applyTax(PoolId poolId, FeeRevenueInfo feeRevenueInfo) internal virtual{
        BalanceDelta jitFeeRevenueDelta = feeRevenueInfo.toBalanceDelta();
        console2.log("Balance Delta:", BalanceDelta.unwrap(jitFeeRevenueDelta));
        BalanceDelta jitTaxPaymentDelta = _calculateTaxPayment(jitFeeRevenueDelta);
        console2.log("Tax Payment Delta:", BalanceDelta.unwrap(jitTaxPaymentDelta));
        console2.log("JIT Liquidity Liability:", BalanceDelta.unwrap(jitFeeRevenueDelta - jitTaxPaymentDelta));
        IParityTaxExtt parityTaxExtt = parityTaxHook.getParityTaxExtt();
        bytes32 slot;
        assembly {
            slot := add(JIT_LIQUIDITY_POSITION_LOCATION, 0x02)
        }
        PositionInfo jitPositionInfo = PositionInfo.wrap(
            uint256(parityTaxExtt.exttload(slot))
        );
        bytes25 poolKeyLookUpPoolId = jitPositionInfo.poolId();
        PoolKey memory poolKey = abi.decode(
            address(lpm).functionStaticCall(
                abi.encodeWithSignature(
                    "poolKeys(bytes25)",
                     poolKeyLookUpPoolId
                )
            ),
            (PoolKey)
        );

        assert(PoolId.unwrap(poolKey.toId())== PoolId.unwrap(poolId));

        lpm.poolManager().donate(
            poolKey,
            uint256(uint128(jitTaxPaymentDelta.amount0())),
            uint256(uint128(jitTaxPaymentDelta.amount1())),
            bytes("")
        );        
    }

    /**
     * @notice Calculates tax payment based on fee revenue and current tax rate
     * @dev Uses transient storage to retrieve tax rate and applies it to fee revenue
     * @param feeRevenueDelta The fee revenue delta to calculate tax on
     * @return taxPayment The calculated tax payment as BalanceDelta
     */
    function _calculateTaxPayment(BalanceDelta feeRevenueDelta) internal view returns(BalanceDelta taxPayment){
        uint24 taxRate;
        assembly("memory-safe"){
            taxRate := tload(TAX_RATE_SLOT)
        }

        if (taxRate == 0) {
           return BalanceDeltaLibrary.ZERO_DELTA;
        }

        // Ensure tax rate doesn't exceed Uniswap v4's maximum protocol fee (1000 pips = 0.1%)
        require(taxRate <= 1000, "Tax rate exceeds maximum protocol fee");

        unchecked {
            uint256 amount0TaxPayment = FullMath.mulDiv(
                SafeCast.toUint128(feeRevenueDelta.amount0()),
                1000000 - taxRate, // (1 - taxRate) as pips
                1000000 // 100% as pips (1,000,000)
            );
            
            uint256 amount1TaxPayment = FullMath.mulDiv(
                SafeCast.toUint128(feeRevenueDelta.amount1()),
                1000000 - taxRate, // (1 - taxRate) as pips
                1000000 // 100% as pips (1,000,000)
            );

            // Convert back to int128 and create BalanceDelta
            taxPayment = toBalanceDelta(
                int128(uint128(amount0TaxPayment)),
                int128(uint128(amount1TaxPayment))
            );
        }
    }

    /**
     * @inheritdoc IFiscalPolicy
     * @dev Calculates optimal tax rate and stores it in transient storage
     */
    function calculateOptimalTax(PoolId poolId,bytes memory data) external returns(uint24){
        uint24 taxRate = _calculateOptimalTax(poolId, data);
        assembly("memory-safe"){
            tstore(TAX_RATE_SLOT, taxRate)
        }
        emit TaxRate(PoolId.unwrap(poolId), taxRate);
        return taxRate;
    }

    /**
     * @inheritdoc IFiscalPolicy
     * @dev Accrues credit for liquidity providers based on their contributions
     */
    function accrueCredit(PoolId,bytes memory) external returns(uint256,uint256){

    }

    /**
     * @notice Internal function to calculate optimal tax rate
     * @dev Virtual function to be implemented by concrete fiscal policy implementations
     * @return uint24 The calculated optimal tax rate in pips
     */
    function _calculateOptimalTax(PoolId ,bytes memory) internal virtual returns(uint24){

    }

    /**
     * @notice Internal function to accrue credit for liquidity providers
     * @dev Virtual function to be implemented by concrete fiscal policy implementations
     * @return uint256 The amount of credit accrued for token0
     * @return uint256 The amount of credit accrued for token1
     */
    function _accrueCredit(PoolId,bytes memory) internal virtual returns(uint256,uint256){

    }

    /**
     * @inheritdoc IFiscalPolicy
     * @dev Handles liquidity commitment events from the reactive network
     */
    function onLiquidityCommitmment(PoolId ,bytes memory) external returns(bytes memory){

    }

    /**
     * @notice Internal function to handle liquidity commitment
     * @dev Virtual function to be implemented by concrete fiscal policy implementations
     * @return bytes The response data for the commitment process
     */
    function _onLiquidityCommitmment(PoolId ,bytes memory) internal virtual returns(bytes memory){

    }

    function onLiquidityOnSwap(PoolId poolId, bytes memory data) external returns(bytes memory){
        if (data.length > uint256(0x80)) revert InvalidDataLength();

        LiquidityOnSwapCallback memory liquidityOnSwapCallback = abi.decode(data, (LiquidityOnSwapCallback));
        return _onLiquidityOnSwap(poolId, liquidityOnSwapCallback);
    }

    function onPriceImpact(PoolId poolId, bytes memory data) external returns(bytes memory){
        // NOTE: 224 is the length of the PriceImpactCallback struct abi encoded
        if (data.length > uint256(0xe0)) revert InvalidDataLength();
        PriceImpactCallback memory priceImpactCallback = abi.decode(data, (PriceImpactCallback));
        return _onPriceImpact(poolId, priceImpactCallback);
    }

    function _onLiquidityOnSwap(PoolId poolId, LiquidityOnSwapCallback memory liquidityOnSwapCallback) internal virtual returns(bytes memory);

    function _onPriceImpact(PoolId poolId, PriceImpactCallback memory priceImpactCallback) internal virtual returns(bytes memory);



    /**
     * @notice Internal function to process fee revenue remittance
     * @dev Virtual function to be implemented by concrete fiscal policy implementations
     */
    function _remit(PoolId,FeeRevenueInfo) internal virtual{

    }

    // ================================ VIEW FUNCTIONS ================================

    /**
     * @inheritdoc IFiscalPolicy
     * @dev Returns the liquidity provider oracle instance
     */
    function lpOracle() external view returns(ILPOracle){
        return _lpOracle;
    }
 
 
 
    // ================================ ISUBSCRIBER FUNCTIONS ================================

    /**
     * @inheritdoc ISubscriber
     * @dev Handles liquidity position burn notifications
     */
    function notifyBurn(uint256 tokenId, address owner, PositionInfo info, uint256 liquidity, BalanceDelta feesAccrued) external{}
    
    /**
     * @inheritdoc ISubscriber
     * @dev Handles liquidity position modification notifications
     */
    function notifyModifyLiquidity(uint256 tokenId, int256 liquidityChange, BalanceDelta feesAccrued) external{}
    
    /**
     * @inheritdoc ISubscriber
     * @dev Handles liquidity position subscription notifications
     */
    function notifySubscribe(uint256 tokenId, bytes memory data) external{}
    
    /**
     * @inheritdoc ISubscriber
     * @dev Handles liquidity position unsubscription notifications
     */
    function notifyUnsubscribe(uint256 tokenId) external{} 

    // ================================ UUPS UPGRADEABLE FUNCTIONS ================================

    /**
     * @notice Authorizes contract upgrades
     * @dev Virtual function to be implemented by concrete fiscal policy implementations
     * @param newImplementation The address of the new implementation contract
     */
    function _authorizeUpgrade(address newImplementation) internal virtual override{}
}