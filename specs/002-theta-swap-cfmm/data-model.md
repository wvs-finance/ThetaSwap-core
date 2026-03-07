# Data Model: ThetaSwap Fee Concentration Insurance CFMM

**Feature**: 002-theta-swap-cfmm | **Date**: 2026-03-04

## Entities

### InsurancePool

Singleton per V4 PoolKey within the MasterHook diamond.

| Field | Type | Description |
|-------|------|-------------|
| poolKey | PoolKey | V4 pool this insurance covers |
| feeBase | uint24 | Baseline swap fee (bps) |
| feeMax | uint24 | Maximum total fee cap (bps) |
| alpha | uint128 | Funding sensitivity parameter (Q128) |
| tickSpacing | int24 | Tick array spacing |
| premiumFractionDefault | uint128 | Default fraction of fees routed as premium (Q128) |
| currentTick | int24 | Current active tick |
| activeLiquidity | uint128 | Total underwriter liquidity in current tick |
| virtualReserveX | uint256 | Current virtual risky reserve (Q128) |
| virtualReserveY | uint256 | Current virtual numeraire reserve (Q128) |

**State transitions**: Uninitialized → Initialized (via initialize). Once initialized, only tick/reserve/liquidity state changes via swaps and LP operations.

### PLPProtectionPosition

One per registered PLP.

| Field | Type | Description |
|-------|------|-------------|
| owner | address | PLP address |
| v4PositionId | bytes32 | Linked V4 liquidity position |
| premiumFraction | uint128 | Fraction of fees committed as premium (Q128) |
| margin | uint256 | Accumulated fees minus streamed premiums (WAD) |
| feeGrowthBaseline | uint256 | feeGrowthInside0 at registration time |
| protectionValue | uint256 | Accrued protection from concentration changes (WAD) |
| registrationBlock | uint256 | Block number at registration |
| isActive | bool | False when auto-closed or deregistered |

**State transitions**: Registered → Active (streaming) → Auto-closed (margin ≤ MIN_MARGIN or fee stream = 0) or Deregistered (manual).

**Lifecycle**:
```
Register → fees accrue → premium streams out from margin →
  if margin ≤ MIN_MARGIN: auto-close, return remaining margin
  if fee stream = 0 (V4 position removed): auto-close
  if manual deregister: close, return margin + protection value
```

### UnderwriterPosition

One per underwriter per tick range.

| Field | Type | Description |
|-------|------|-------------|
| owner | address | Underwriter address |
| tickLower | int24 | Lower tick bound |
| tickUpper | int24 | Upper tick bound |
| liquidity | uint128 | Liquidity amount |
| collateralDeposited | uint256 | Initial collateral (WAD) |
| premiumGrowthInsideBaseline | uint256 | feeGrowthPerLiquidity at deposit (Q128) |
| protectionPayoutsBaseline | uint256 | protectionPayoutsPerLiquidity at deposit (Q128) |

**State transitions**: Created (addLiquidity) → Active (earning premiums, paying protection) → Removed (removeLiquidity).

### InsuranceTick

Per-tick state in the tick array.

| Field | Type | Description |
|-------|------|-------------|
| liquidityNet | int128 | Net liquidity delta at this tick |
| liquidityGross | uint128 | Total liquidity referencing this tick |
| premiumGrowthOutside | uint256 | Premium growth outside this tick (Q128) |
| protectionPayoutsOutside | uint256 | Protection payouts outside this tick (Q128) |
| slopeQ128 | int256 | Piecewise-linear slope: dy/dp at tick midpoint (Q128) |
| interceptQ128 | int256 | Piecewise-linear intercept: y at tick start (Q128) |

### OracleSnapshot

Refreshed on every hook callback.

| Field | Type | Description |
|-------|------|-------------|
| indexA | uint128 | A_T from FeeConcentrationIndex (Q128) |
| indexB | uint128 | B_T = 1 - A_T (Q128) |
| pIndex | uint256 | p_index = B_T / (1 - B_T) (Q128) |
| pMark | uint256 | p_mark = (1 - x) / x (Q128) |
| fundingRate | int256 | Current fee_funding component (signed, Q128) |

## Relationships

```
InsurancePool 1──* InsuranceTick (tick array)
InsurancePool 1──* PLPProtectionPosition (registered PLPs)
InsurancePool 1──* UnderwriterPosition (underwriters)
InsurancePool 1──1 OracleSnapshot (latest oracle state)
PLPProtectionPosition *──1 V4 Position (via v4PositionId)
UnderwriterPosition *──2 InsuranceTick (via tickLower, tickUpper)
```

## Validation Rules

- `tickLower < tickUpper` and both divisible by `tickSpacing`
- `tickLower >= MIN_TICK` and `tickUpper <= MAX_TICK`
- `premiumFraction ∈ (0, Q128_ONE]` (cannot be zero or exceed 100%)
- `liquidity > 0` for all positions
- `margin > MIN_MARGIN` for active PLP positions
- `collateralDeposited > 0` for underwriter positions
- `feeBase < feeMax`
- `alpha > 0`

## Storage Layout (Diamond Pattern)

Each entity group uses a distinct keccak256 storage slot to avoid collision:

```
INSURANCE_POOL_SLOT     = keccak256("theta-swap.insurance.pool")
PLP_POSITIONS_SLOT      = keccak256("theta-swap.insurance.plp-positions")
UNDERWRITER_SLOT        = keccak256("theta-swap.insurance.underwriter-positions")
TICK_SLOT               = keccak256("theta-swap.insurance.ticks")
ORACLE_SLOT             = keccak256("theta-swap.insurance.oracle")
TICK_BITMAP_SLOT        = keccak256("theta-swap.insurance.tick-bitmap")
```

These are disjoint from FeeConcentrationIndex's `FCI_STORAGE_SLOT`.
