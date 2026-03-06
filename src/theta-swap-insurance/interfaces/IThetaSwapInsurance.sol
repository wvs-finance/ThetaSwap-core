// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";

interface IThetaSwapInsurance {
    //--------------------------------------------------------------------------
    // Events
    //--------------------------------------------------------------------------

    event InsurancePoolInitialized(
        PoolId indexed poolId,
        uint24 feeBase,
        uint24 feeMax,
        uint128 alpha
    );

    event PLPRegistered(
        PoolId indexed poolId,
        bytes32 indexed insurancePositionId,
        bytes32 v4PositionId,
        uint128 premiumFraction
    );

    event PLPDeregistered(
        PoolId indexed poolId,
        bytes32 indexed insurancePositionId,
        uint256 marginReturned,
        uint256 protectionValue
    );

    event PLPAutoClose(
        PoolId indexed poolId,
        bytes32 indexed insurancePositionId,
        uint256 remainingMargin
    );

    event UnderwriterAdded(
        PoolId indexed poolId,
        bytes32 indexed positionId,
        int24 tickLower,
        int24 tickUpper,
        uint128 liquidity
    );

    event UnderwriterRemoved(
        PoolId indexed poolId,
        bytes32 indexed positionId,
        uint256 collateralReturned,
        uint256 netPremiums
    );

    event PremiumAccrued(
        PoolId indexed poolId,
        uint256 totalPremium,
        int256 fundingRate
    );

    //--------------------------------------------------------------------------
    // Errors
    //--------------------------------------------------------------------------

    error InsurancePool__AlreadyInitialized();
    error InsurancePool__NotInitialized();
    error InsurancePool__InvalidTickRange();
    error InsurancePool__ZeroLiquidity();
    error InsurancePool__InsufficientCollateral();
    error InsurancePool__OracleFailure();
    error InsurancePool__PositionNotFound();
    error InsurancePool__PositionNotActive();
    error InsurancePool__NoUnderwriterLiquidity();
    error InsurancePool__InvalidPremiumFraction();

    //--------------------------------------------------------------------------
    // Pool Initialization
    //--------------------------------------------------------------------------

    function initialize(
        PoolKey calldata poolKey,
        uint24 feeBase,
        uint24 feeMax,
        uint128 alpha,
        int24 tickSpacing,
        uint128 premiumFraction,
        uint160 initialSqrtPrice
    ) external;

    //--------------------------------------------------------------------------
    // PLP Protection (Insurance Buyers)
    //--------------------------------------------------------------------------

    function registerForInsurance(
        PoolKey calldata poolKey,
        bytes32 v4PositionId,
        uint128 premiumFraction
    ) external returns (bytes32 insurancePositionId);

    function deregisterInsurance(
        PoolKey calldata poolKey,
        bytes32 insurancePositionId
    ) external returns (uint256 marginReturned, uint256 protectionValueReturned);

    //--------------------------------------------------------------------------
    // Underwriter Positions (Insurance Sellers)
    //--------------------------------------------------------------------------

    function addUnderwriterLiquidity(
        PoolKey calldata poolKey,
        int24 tickLower,
        int24 tickUpper,
        uint128 liquidity
    ) external returns (bytes32 positionId, uint256 collateralRequired);

    function removeUnderwriterLiquidity(
        PoolKey calldata poolKey,
        bytes32 positionId,
        uint128 liquidity
    ) external returns (uint256 collateralReturned, uint256 netPremiumsEarned);

    //--------------------------------------------------------------------------
    // View Functions
    //--------------------------------------------------------------------------

    function getInsuranceState(PoolKey calldata poolKey)
        external
        view
        returns (
            int24 currentTick,
            uint128 activeLiquidity,
            uint256 virtualReserveX,
            uint256 virtualReserveY
        );

    function getMarkPrice(PoolKey calldata poolKey)
        external
        view
        returns (uint256 pMark);

    function getIndexPrice(PoolKey calldata poolKey)
        external
        view
        returns (uint256 pIndex);

    function getPremiumRate(PoolKey calldata poolKey)
        external
        view
        returns (int256 fundingRate, uint256 effectiveFee);

    function getProtectionValue(
        PoolKey calldata poolKey,
        bytes32 insurancePositionId
    )
        external
        view
        returns (
            uint256 margin,
            uint256 protectionValue,
            uint256 premiumPaid,
            bool isActive
        );

    function getUnderwriterPosition(
        PoolKey calldata poolKey,
        bytes32 positionId
    )
        external
        view
        returns (
            int24 tickLower,
            int24 tickUpper,
            uint128 liquidity,
            uint256 premiumsEarned,
            uint256 protectionPayouts
        );
}
