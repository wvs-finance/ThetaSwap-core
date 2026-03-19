# Research: ThetaSwap Fee Concentration Insurance CFMM

**Feature**: 002-theta-swap-cfmm | **Date**: 2026-03-04

## R-001: V4 Single Hook Constraint

**Decision**: Use MasterHook diamond pattern from hook-bazaar/monorepo
**Rationale**: V4 allows exactly one `IHooks` address per `PoolKey`. The MasterHook is a diamond proxy that dispatches hook callbacks via `delegatecall` to facets. Both FeeConcentrationIndex and ThetaSwapInsurance become facets of the same MasterHook.
**Alternatives considered**:
- Standalone contract (not a hook): loses hook-integrated fee routing
- Replace FeeConcentrationIndex: loses separation of concerns
- Sequential deployment (FCI as standalone oracle): FCI loses hook callbacks needed for accurate tracking

## R-002: Piecewise-Linear Approximation of ln(x)

**Decision**: Linear approximation of y(p) = ln(1+p) - p/(1+p) at tick midpoints
**Rationale**: Enables Uniswap V3-style CLAMM. Within each tick, swap math reduces to slope × Δp (O(1)). Error bounded by |y''(p_mid)| · (tickSpacing/2)² ≈ O(10⁻⁹) at 1 bps. gammaDEX-core validated piecewise approach for similar CFMM.
**Alternatives considered**:
- Exact Solady ln(): accurate but O(n) gas per transcendental call, doesn't decompose into tick-local constant-liquidity math
- Piecewise quadratic: better accuracy but more gas per swap, novel/untested
- Lookup table: lowest gas but also lowest precision

## R-003: Insurance Premium Model (Economic Design)

**Decision**: Streaming premium funded by PLP V4 fee accruals
**Rationale**: PLPs are naturally long B_T (hurt by concentration). They are natural SELLERS of B exposure, not buyers. Reframing as insurance where PLPs BUY protection (paying premium from fees) and underwriters SELL protection creates a viable two-sided market. JITs are not required as counterparties. The fee stream as premium creates a self-sizing hedge: insurance scales with fee exposure.
**Alternatives considered**:
- Swap-based derivative market: one-sided demand problem (PLPs sell, no one buys)
- Flip to A_T market: creates two-sided hedging but doesn't match the economic intuition
- Speculator-driven: relies on external speculative demand which may not bootstrap

## R-004: Composite Hook Callbacks

**Decision**: Composite facets that call FCI logic first, then Insurance logic
**Rationale**: Three callbacks are shared: afterAddLiquidity, afterSwap, afterRemoveLiquidity. FCI must execute first so B_T is updated before Insurance reads it. Diamond pattern allows a composite facet to call both in sequence within one delegatecall.
**Alternatives considered**:
- Single merged facet: loses separation of concerns, harder to test independently
- Chained delegatecalls: possible but adds gas overhead and complexity

## R-005: Fee Stream Access in delegatecall Context

**Decision**: Read V4 fee growth via StateLibrary within hook callbacks
**Rationale**: When executing via delegatecall from MasterHook, `msg.sender` is PoolManager (from V4's perspective), and `address(this)` is MasterHook. StateLibrary reads from PoolManager's extsload, which doesn't depend on caller identity. Fee growth data (feeGrowthInside0X128) is accessible.
**Alternatives considered**:
- External call to FCI: would break delegatecall context, adds gas
- Cache fee data in transient storage: FCI already does this (TSTORE), Insurance can read via TLOAD from same context
