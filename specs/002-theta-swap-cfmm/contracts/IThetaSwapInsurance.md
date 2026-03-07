# Interface Contract: IThetaSwapInsurance

**Feature**: 002-theta-swap-cfmm | **Date**: 2026-03-04

## External Functions (facet interface)

### Pool Initialization

```
initialize(PoolKey poolKey, uint24 feeBase, uint24 feeMax, uint128 alpha, int24 tickSpacing, uint128 premiumFraction, uint160 initialSqrtPrice)
  → Initializes insurance pool state for a V4 pool
  → Reverts if already initialized
  → Computes and caches piecewise-linear coefficients for all ticks in [MIN_TICK, MAX_TICK]
```

### PLP Protection (Insurance Buyers)

```
registerForInsurance(PoolKey poolKey, bytes32 v4PositionId, uint128 premiumFraction)
  → Links PLP's V4 position to insurance, starts fee stream as premium
  → Returns: insurancePositionId (bytes32)
  → Reverts if: v4 position doesn't exist, pool not initialized, no underwriter liquidity

deregisterInsurance(PoolKey poolKey, bytes32 insurancePositionId)
  → Closes protection position, returns remaining margin + protection value
  → Returns: (uint256 marginReturned, uint256 protectionValueReturned)
```

### Underwriter Positions (Insurance Sellers)

```
addUnderwriterLiquidity(PoolKey poolKey, int24 tickLower, int24 tickUpper, uint128 liquidity)
  → Deposits collateral into tick range, starts earning premiums
  → Returns: (bytes32 positionId, uint256 collateralRequired)
  → Transfers collateral from msg.sender

removeUnderwriterLiquidity(PoolKey poolKey, bytes32 positionId, uint128 liquidity)
  → Withdraws collateral + net premiums - protection payouts
  → Returns: (uint256 collateralReturned, uint256 netPremiumsEarned)
  → Transfers collateral to msg.sender
```

### View Functions

```
getInsuranceState(PoolKey poolKey)
  → Returns: (int24 currentTick, uint128 activeLiquidity, uint256 virtualReserveX, uint256 virtualReserveY)

getMarkPrice(PoolKey poolKey)
  → Returns: uint256 pMark (Q128)

getIndexPrice(PoolKey poolKey)
  → Returns: uint256 pIndex (Q128)
  → Calls IFeeConcentrationIndex.getIndex() internally

getPremiumRate(PoolKey poolKey)
  → Returns: (int256 fundingRate, uint256 effectiveFee) (Q128)

getProtectionValue(PoolKey poolKey, bytes32 insurancePositionId)
  → Returns: (uint256 margin, uint256 protectionValue, uint256 premiumPaid, bool isActive)

getUnderwriterPosition(PoolKey poolKey, bytes32 positionId)
  → Returns: (int24 tickLower, int24 tickUpper, uint128 liquidity, uint256 premiumsEarned, uint256 protectionPayouts)
```

### Hook Callbacks (internal, called by MasterHook via composite facets)

```
_insuranceAfterAddLiquidity(sender, key, params, delta, feeDelta, hookData)
  → If sender is registered PLP: snapshot fee baseline, activate insurance
  → Returns: (bytes4 selector, BalanceDelta)

_insuranceAfterRemoveLiquidity(sender, key, params, delta, feeDelta, hookData)
  → If sender is registered PLP: compute final premium, auto-close position
  → Returns: (bytes4 selector, BalanceDelta)

_insuranceAfterSwap(sender, key, params, delta, hookData)
  → Accrue streaming premiums to underwriters
  → Update virtual reserves and tick state
  → Compute funding rate from mark-index divergence
  → Returns: (bytes4 selector, int128)
```

## Events

```
InsurancePoolInitialized(PoolId indexed poolId, uint24 feeBase, uint24 feeMax, uint128 alpha)
PLPRegistered(PoolId indexed poolId, bytes32 indexed insurancePositionId, bytes32 v4PositionId, uint128 premiumFraction)
PLPDeregistered(PoolId indexed poolId, bytes32 indexed insurancePositionId, uint256 marginReturned, uint256 protectionValue)
PLPAutoClose(PoolId indexed poolId, bytes32 indexed insurancePositionId, uint256 remainingMargin)
UnderwriterAdded(PoolId indexed poolId, bytes32 indexed positionId, int24 tickLower, int24 tickUpper, uint128 liquidity)
UnderwriterRemoved(PoolId indexed poolId, bytes32 indexed positionId, uint256 collateralReturned, uint256 netPremiums)
PremiumAccrued(PoolId indexed poolId, uint256 totalPremium, int256 fundingRate)
```

## Errors

```
InsurancePool__AlreadyInitialized()
InsurancePool__NotInitialized()
InsurancePool__InvalidTickRange()
InsurancePool__ZeroLiquidity()
InsurancePool__InsufficientCollateral()
InsurancePool__OracleFailure()
InsurancePool__PositionNotFound()
InsurancePool__PositionNotActive()
InsurancePool__NoUnderwriterLiquidity()
InsurancePool__InvalidPremiumFraction()
```
