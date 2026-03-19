# Project Scaffold — Design Document

**Date:** 2026-03-02
**Status:** Approved

## Decision: Clean Rewrite

Delete all existing src/, test/, script/ code. DRAFT.md is the sole source of truth. Existing code uses `library` keyword and other SCOP violations.

## TDD Context

- Base TLA+ model: ToyCLAMM2DirArb
- CFMM submodule: activated (19 mandatory invariants, 8 mandatory UDVTs)
- 3 features, each through full 7-phase TDD cycle independently

## Type Classification

Model-independent (src/types/):
- ReserveX, ReserveY, Liquidity, SqrtPriceX96, TickIndex
- FeeAccumX, FeeAccumY, FeeRevenue, Capital

Model-dependent (src/liquidity-supply-model-simplest/types/):
- FeeRate (φ = 4·max(gasCost)), EntryCount (N_t), IndexValue
- SwapVolume, FixedMarketPrice, SimulationConfig

Key insight: FeeRate is model-dependent (dynamic fee set by hook). FeeRevenue is model-independent (market reports it, unaware of fee computation).

## Directory Layout

```
src/
  types/
    ReserveX.sol + ReserveXMod.sol
    ReserveY.sol + ReserveYMod.sol
    Liquidity.sol + LiquidityMod.sol
    SqrtPriceX96.sol + SqrtPriceX96Mod.sol
    TickIndex.sol + TickIndexMod.sol
    FeeAccumX.sol + FeeAccumXMod.sol
    FeeAccumY.sol + FeeAccumYMod.sol
    FeeRevenue.sol + FeeRevenueMod.sol
    Capital.sol + CapitalMod.sol

  liquidity-supply-model-simplest/
    types/
      FeeRate.sol + FeeRateMod.sol
      EntryCount.sol + EntryCountMod.sol
      IndexValue.sol + IndexValueMod.sol
      SwapVolume.sol + SwapVolumeMod.sol
      FixedMarketPrice.sol + FixedMarketPriceMod.sol
      SimulationConfig.sol
    core-cfmm/
    jit-plp/
    entry-index/

specs/
  core-cfmm/
    spec.md, plan.md, tasks.md, model.tla, invariants.md
  jit-plp/
    spec.md, plan.md, tasks.md, invariants.md
  entry-index/
    spec.md, plan.md, tasks.md, invariants.md

test/
  liquidity-supply-model-simplest/
    base/
      StateInit.t.sol
      HookDeployer.t.sol
    helpers/
      ForkUtils.sol
    CoreCfmm.kontrol.t.sol
    CoreCfmm.fuzz.t.sol
    JitPlp.kontrol.t.sol
    JitPlp.fuzz.t.sol
    EntryIndex.kontrol.t.sol
    EntryIndex.fuzz.t.sol

script/
  liquidity-supply-model-simplest/
```

## Feature Dependency Chain

```
Feature 1: core-cfmm (no dependencies)
    ↓
Feature 2: jit-plp (depends on core-cfmm)
    ↓
Feature 3: entry-index (depends on jit-plp)
```

### Feature 1 — core-cfmm

- Two-pool setup (hooked + control), same underlying + numeraire (R1.1, R1.2)
- Swap mechanics with FixedMarketPrice enforcement
- MeanRevertingVolume rule: isInverse(swapDeltaPrevious, swapDeltaNow)
- Dynamic fee hook: φ = 4·max(LiquidityMintingAndBurningGasCost)
- Construction proof: MeanRevertingVolume ⟹ FixedMarketPrice
- Implication: CFMMIsOnlyMarket ⟹ impermanentLoss = 0
- PerfectVolumeElasticityWrtLiquidityDepth rule
- TLA+ base: ToyCLAMM2DirArb
- CFMM submodule: 19 mandatory invariants + feature-specific

### Feature 2 — jit-plp

- LiquidityProvider type with PLP and JIT variants
- JIT: mint before swap, burn after, capture 2 fee units, leave 1 surplus
- PLP: liquidity based on elasticity(volume, liquidityDepth)
- JIT arrival probability π = 1
- UnawareSufficiency: value(Σ swaps) ≤ value(representativeLPPosition)
- After each swap pair: new PLP enters, equal share
- EntryCount (N_t) tracking
- End condition: swaps per pool = number of LPs + 2

### Feature 3 — entry-index

- Hedging instrument: pays 1 unit of account per LP entry
- ONE PLP on hooked pool uses surplus to purchase instrument
- Other LPs re-invest surplus as liquidity
- Prove: PLP hedges competition risk
- Prove: competition risk is the ONLY risk in this model

## StateInit.t.sol

LiquiditySupplyModelSimplestTest extends PosmTestSetUp (test inheritance exception).
TRADER = address(this) — uninformed traders have no identity.
Diamond storage for ModelState and ForkedState.
setUp(): deploy PoolManager, PositionManager, mock ERC20s, hook, initialize 2 pools, fund 4 LPs equally, approve routers.

## ForkUtils.sol

ChainAddresses struct with per-field accessor functions.
No comments. poolManager("ethereum"), positionManager("ethereum"), etc.
Each accessor calls getChainAddresses internally.

## Remappings

Keep:
- forge-std/=lib/forge-std/src/
- @uniswap/v4-core/=lib/uniswap-hooks/lib/v4-core/
- @uniswap/v4-periphery/=lib/uniswap-hooks/lib/v4-periphery/
- @uniswap/v4-hooks/=lib/uniswap-hooks/src/base/
- @openzeppelin/contracts/=lib/uniswap-hooks/lib/openzeppelin-contracts/contracts/
- permit2/=lib/uniswap-hooks/lib/v4-periphery/lib/permit2/
- solmate/=lib/uniswap-hooks/lib/v4-core/lib/solmate/

Keep with branch update:
- @uniswap/v3-core/=lib/v3-core/ (branch 0.8)
- @uniswap/v3-periphery/=lib/v3-periphery/ (branch 0.8)

Rename:
- @panoptic-v2/=lib/2025-12-panoptic/

Add:
- @angstrom/=lib/angstrom/contracts/src/
- @bunni-v2/=lib/bunni-v2/src/
- kontrol-cheatcodes/=lib/kontrol-cheatcodes/src/
- solady/=lib/solady/src/

## What Gets Deleted

- src/jit-competition/ (JitHook.sol, EntryIndex.sol, ModelTypes.sol, ModelParams.sol)
- src/fee-variance/ (FeeVariance.sol)
- test/jit-competition/ (all files)
- script/fee-variance/ (ComputeFeeVariance.s.sol)

## References

- DRAFT.md — source of truth
- type-driven-development skill — 7-phase TDD process
- cfmm-specification submodule — 19 mandatory invariants, TLA+ requirement
- ToyCLAMM2DirArb — selected TLA+ base model
