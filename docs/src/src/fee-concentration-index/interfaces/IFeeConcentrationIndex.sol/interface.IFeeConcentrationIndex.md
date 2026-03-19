# IFeeConcentrationIndex
[Git Source](https://github.com/JMSBPP/thetaSwap-core-dev/blob/ce79e8aa1265f6744b75598e8829707a42ddd160/src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol)

**Inherits:**
IERC165, [IHookFacet](/src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol/interface.IHookFacet.md)


## Functions
### getIndex

Returns the co-primary state triple for the pool's FCI.


```solidity
function getIndex(PoolKey calldata key, bool reactive)
    external
    view
    returns (uint128 indexA, uint256 thetaSum, uint256 removedPosCount);
```
**Parameters**

|Name|Type|Description|
|----|----|-----------|
|`key`|`PoolKey`|The pool key.|
|`reactive`|`bool`|If true, reads from reactive storage; false for local.|

**Returns**

|Name|Type|Description|
|----|----|-----------|
|`indexA`|`uint128`|A_T = sqrt(accumulatedSum), Q128-scaled, capped at INDEX_ONE.|
|`thetaSum`|`uint256`|Θ = Σ(1/ℓ_k), Q128-scaled, cumulative over removals.|
|`removedPosCount`|`uint256`|N = number of positions that contributed terms.|


### getDeltaPlus

Returns Δ⁺ = max(0, A_T - atNull) for the pool, Q128-scaled.

Derived on the fly from stored co-primary state.


```solidity
function getDeltaPlus(PoolKey calldata key, bool reactive) external view returns (uint128 deltaPlus_);
```

### getAtNull

Returns the competitive null atNull = sqrt(Θ/N²), Q128-scaled.


```solidity
function getAtNull(PoolKey calldata key, bool reactive) external view returns (uint128 atNull_);
```

### getThetaSum

Returns Θ = Σ(1/ℓ_k), Q128-scaled, cumulative over removals.


```solidity
function getThetaSum(PoolKey calldata key, bool reactive) external view returns (uint256 thetaSum_);
```

