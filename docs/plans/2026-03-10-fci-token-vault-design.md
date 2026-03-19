# FCI Token Vault — Design Specification

Date: 2026-03-10 (revised 2026-03-11)
Branch: `004-fci-token-vault`
Status: Approved

## Problem

The FCI oracle (branches 001/003) computes per-pool fee concentration deviation (Δ⁺) for V4 hooks and V3 reactive adapters. To enable hedging markets for passive LPs, the oracle output needs to be tokenized into a composable ERC-20 that can trade on any CFMM independently.

Before building the full vault, the payoff and HWM sub-components must be validated against realistic JIT scenarios to confirm that the hedge improves passive LP welfare under adversarial fee extraction.

## Architecture

Four independent layers (Layers 2a and 2b are in scope):

```
Layer 1: FCI Oracle (exists — branches 001/003)
  │ getDeltaPlus() → raw Δ⁺ (Q128, last Q128 boundary)
  │ deltaPlusToSqrtPriceX96() → sqrtPriceX96 via SqrtPriceLibrary
  ▼
Layer 2a: Sub-component Libraries (this branch — 004, Chunk 1)
  │ PayoffMod, HighWaterMarkMod — pure math in sqrtPriceX96 space
  ▼
Layer 2b: Scenario Validation (this branch — 004, Chunk 2)
  │ Multi-round JIT game → FCI hook → HWM + payoff → hedged vs unhedged
  ▼
Layer 2c: FCI Token Vault (this branch — 004, Chunk 3)
  │ LONG and SHORT are standard ERC-20s, composing 2a libraries
  ▼
Layer 3: Any CFMM (future — branches 005/006)
```

The vault reads the oracle via `IFeeConcentrationIndex.getDeltaPlus(PoolKey, bool reactive)` — the existing interface on both the V4 hook and V3 reactive adapter. The conversion `p = Δ⁺/(Q128 - Δ⁺)` is performed via `SqrtPriceLibrary.fractionToSqrtPriceX96(deltaPlus, Q128 - deltaPlus)` from the `foundational-hooks` library (transitive dependency via `typed-uniswap-v4`). All vault state (HWM, strikes) is denominated in sqrtPriceX96 or ticks.

**Dependency prerequisite:** The `foundational-hooks` library lives at `lib/typed-uniswap-v4/lib/foundational-hooks/`. A remapping must be added to `foundry.toml` before Chunk 1 implementation:
```
"foundational-hooks/=lib/typed-uniswap-v4/lib/foundational-hooks/"
```

**Oracle interface note:** The canonical oracle interface is `IFeeConcentrationIndex.getDeltaPlus(PoolKey calldata key, bool reactive) returns (uint128)`. The `IFCIDeltaPlusReader(PoolId)` interface in `JitGame.sol` is a test harness convenience for direct harness reads; the scenario validation layer (Chunk 2) uses this harness interface in tests. The vault (Chunk 3) must use the canonical `IFeeConcentrationIndex` interface for production compatibility.

**Diamond proxy note:** The V4 FCI hook runs as a facet inside the MasterHook diamond. The vault must call `getDeltaPlus()` on the **MasterHook proxy address**, not the facet address. The oracle address stored in the vault is the proxy.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Oracle coupling | Standalone synthetic token (not position-bound) | Maximum composability — trades on any CFMM, usable as collateral |
| Peg mechanism | Collateral-vault mint/burn | Redeemable for USDC at payoff value — hard floor, arbitrage-enforced peg |
| Mint structure | Paired mint (LONG + SHORT) | Both sides get native instruments, no borrow market needed |
| Payoff function | Power-squared: ((sqrtPriceHWM/sqrtPriceStrike)⁴ − 1)⁺ | Matches α=2 on price (⁴ on sqrtPrice). Backtest-confirmed optimal. |
| Strike selection | Depositor-chosen from standardized grid | Balances expressiveness with liquidity concentration |
| Strike grid | Tick-based, anchored at econometric Δ* ≈ 0.09 | Ticks via TickMath — reuses V4 infrastructure, aligns with Layer 3 CFMM |
| Price representation | sqrtPriceX96 (V4-native) | Single conversion boundary at oracle read. SqrtPriceLibrary for arithmetic. |
| Token lifecycle | Perpetual, no expiry | No rollover friction for passive LPs |
| Lookback mechanism | High-water mark with exponential decay | O(1) storage/update, no cliffs, captures spikes with graceful fade |
| Scenario validation | Multi-round JIT game before vault | Validates payoff formula against real FCI hook before committing to vault contract |

## Precision Chain

The system has a **single precision boundary** — all downstream math operates in sqrtPriceX96:

```
FCI hook → Δ⁺ (Q128)
  │
  ▼ deltaPlusToSqrtPriceX96():
  │   SqrtPriceLibrary.fractionToSqrtPriceX96(deltaPlus, Q128 - deltaPlus)
  │   (from foundational-hooks, already in dependency tree via typed-uniswap-v4)
  ▼
sqrtPriceX96 (uint160)
  │
  ├─→ TickMath.getTickAtSqrtPrice() → tick (int24) [for strike grid]
  ├─→ HighWaterMarkMod: stores uint160 maxSqrtPrice, decay in sqrtPrice space
  └─→ PayoffMod: ratio = sqrtPriceHWM / sqrtPriceStrike via SqrtPriceLibrary.divX96
```
note: The highWaterMarkMod is inside the PayoffMod and this PayoffMod also ha the deltaPlussSqrtPriceX96 utility

No WAD. No Q128 in payoff/HWM math. No custom conversion libraries.

**Small Δ⁺ precision note:** `fractionToSqrtPriceX96` uses integer `sqrt()`, which loses precision for very small Δ⁺ values (e.g., Δ⁺ < 100). This is acceptable: small Δ⁺ means no meaningful concentration deviation, so the payoff is 0 regardless. The precision cliff does not affect any scenario where the payoff would be non-zero.

## Token Design

### Paired Mint

Depositor locks D USDC, specifying strike index. Receives:

- **LONG-FCI(pool, p\*)** — ERC-20, gains value when concentration rises above p*
- **SHORT-FCI(pool, p\*)** — ERC-20, retains value when concentration stays below p*

Each (pool, strike) pair produces a distinct token pair.

### Payoff Computation

All values are **per token** (1 token = 1 USDC of original collateral). Internally computed in sqrtPriceX96 space:

```
ratio = SqrtPriceLibrary.divX96(sqrtPriceHWM, sqrtPriceStrike)
// ratio is Q96-scaled. Safe range: ratio ∈ [0, ~2^80] before overflow on squaring.
// Since Δ⁺ ∈ [0, Q128) and p = Δ⁺/(Q128-Δ⁺), sqrtPrice is bounded by TickMath limits,
// so ratio cannot exceed ~2^48 in practice (well within safe range).
ratioSquared = FixedPointMathLib.mulDiv(ratio, ratio, Q96)    // ratio² in Q96
ratioToFourth = FixedPointMathLib.mulDiv(ratioSquared, ratioSquared, Q96)  // ratio⁴ in Q96
quadratic_payoff = ratioToFourth - Q96    // ((p_hwm/p*)² - 1) in Q96 scale

LONG value per token  = min(quadratic_payoff, Q96) → scaled to USDC
SHORT value per token = Q96 − LONG value            → scaled to USDC
```

All squaring uses `FixedPointMathLib.mulDiv` to prevent overflow.

- HWM sqrtPrice ≤ strike sqrtPrice: LONG = 0, SHORT = 1 USDC
- HWM sqrtPrice = strike sqrtPrice × √(√2): LONG = 1 USDC, SHORT = 0 (max payout)
- Between: smooth quadratic curve

Tokens are fungible across depositors at the same strike. No per-deposit state.

### High-Water Mark

```
elapsed = block.timestamp − lastUpdate

// Decay is on PRICE (not sqrtPrice). Half-life of 14 days means price halves every 14 days.
// In sqrtPrice space this means: sqrtP_decayed = sqrtP × sqrt(e^(-λ×elapsed))
//                                              = sqrtP × e^(-λ×elapsed/2)
//
// Implementation:
//   1. Compute decayFactor = expWad(-ln2 × elapsed / halfLife) → WAD-scaled [0, 1e18]
//   2. Scale to Q96: decayFactorQ96 = decayFactor × Q96 / WAD
//   3. sqrtDecay = sqrt(decayFactorQ96 × Q96) → Q96-scaled sqrt of decay factor
//   4. decayedMax = storedMaxSqrtPrice × sqrtDecay / Q96

decayFactorWad = expWad(-ln2 × elapsed / halfLife)   // WAD: e^(-λt) on price
sqrtDecayQ96 = sqrt(decayFactorWad × Q96² / WAD)     // Q96: sqrt(e^(-λt))
decayedMax = storedMaxSqrtPrice × sqrtDecayQ96 / Q96  // uint160
newHWM = max(currentSqrtPrice, decayedMax)
```

Single storage slot: `(maxSqrtPrice uint160, lastUpdate uint64)`. O(1) reads and writes. No keepers.

Starting parameter: half-life = 14 days on **price** (λ = ln(2) / 14 days). This means sqrtPrice decays with effective half-life of 28 days. Calibrated from hazard model lag structure.

**Initialization:** `hwmSqrtPrice` starts at 0. The first `poke()` sets it to `currentSqrtPrice`.

### Strike Grid

Strikes are **tick indices** validated by `TickMath`. Example for ETH/USDC 30bps:

| Strike tick | p ≈ | Δ⁺ ≈ | Meaning |
|---|---|---|---|
| tick for p=0.05 | 0.050 | 0.048 | Early warning |
| tick for p=0.10 | 0.100 | 0.091 | Econometric turning point (Δ*) |
| tick for p=0.33 | 0.333 | 0.200 | Tail protection |

Grid is immutable per vault deployment. Validated via `TickMath.getSqrtPriceAtTick()` bounds.

**Computing strike ticks:** `strikeTick = TickMath.getTickAtSqrtPrice(SqrtPriceLibrary.fractionToSqrtPriceX96(p_num, p_den))` where `p = Δ⁺/(1-Δ⁺)` expressed as numerator/denominator. Ticks must be rounded to the pool's tick spacing.

## Scenario Validation Layer

Before building the full vault, the sub-component libraries (PayoffMod, HighWaterMarkMod) are validated against realistic JIT scenarios using the Capponi JIT sequential game.

### Multi-Round JIT Game Driver

Extends the existing single-round `runJitGame` to K rounds with persistent passive LPs:

```
Round setup (once):
  Block B₀: N passive LPs mint positions (long-lived)

Per round k = 1..K:
  Block B₀ + k×ROUND_SPACING: JIT decision (probabilistic entry)
  Same block: swap arrives
  Next block: JIT exits → FCI hook records θ_JIT = 1/1 (max penalty)
  Read Δ⁺ snapshot from FCI hook

Final:
  Block B₀ + K×ROUND_SPACING + EXIT_OFFSET: passive LPs exit
  FCI hook records θ_passive = 1/lifetime (low penalty, long-lived)
```

**Config**: `JitMultiRoundConfig` adds `rounds` (K) and `roundSpacing` (blocks between JIT events).

**Result**: `JitMultiRoundResult` with `deltaSnapshots[K]` (Δ⁺ after each round) + final passive LP payouts.

### Hedged-vs-Unhedged Integration Test

Wires the game driver with sub-component libraries — no vault contract, no tokens, no premium:

```
1. Deploy FCI hook via HookMiner
2. Init pool with FCI hook
3. Pick strike tick (e.g., tick for Δ* ≈ 0.09)
4. Run multi-round JIT game (K rounds, persistent PLPs)
5. After each round:
   a. Read Δ⁺ from FCI hook
   b. Convert to sqrtPriceX96 via deltaPlusToSqrtPriceX96()
   c. Update HWM via HighWaterMarkMod
6. After all rounds:
   a. Compute payoff via PayoffMod(hwm, strike)
   b. hedged_welfare   = raw_fee_payout + payoff (scaled to fee units)
   c. unhedged_welfare  = raw_fee_payout
   d. Assert: hedged > unhedged when Δ⁺ crossed the strike
```

This proves the payoff formula compensates hedged LPs without building the vault.

## Vault Contract

### State

```
// Immutable (set at construction)
PoolKey     poolKey;            // the pool this vault tracks
IERC20      collateral;         // USDC
IFeeConcentrationIndex oracle;  // MasterHook proxy or ReactiveHookAdapter
bool        reactive;           // false for V4, true for V3 adapter
int24[]     strikeTicks;        // standardized strike grid (tick indices)

// Per-strike state
struct StrikeState {
    ERC20      longToken;       // deployed at vault init
    ERC20      shortToken;      // deployed at vault init
    uint160    hwmSqrtPrice;    // high-water mark in sqrtPriceX96
    uint64     lastUpdate;      // timestamp of last HWM update
    uint256    totalDeposits;   // aggregate USDC locked at this strike
}
mapping(uint8 => StrikeState) strikes;
```

### Oracle Interface

Uses the existing `IFeeConcentrationIndex` interface (no new interface). The vault stores the oracle address (MasterHook proxy for V4, or ReactiveHookAdapter for V3).

```solidity
import {IFeeConcentrationIndex} from "src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
```

The vault reads raw `Δ⁺` via `getDeltaPlus(key, reactive)` and converts to sqrtPriceX96 via `SqrtPriceLibrary.fractionToSqrtPriceX96(deltaPlus, Q128 - deltaPlus)`. All downstream math operates in sqrtPriceX96.

### Scope: One Vault Per Pool

Each vault deployment is scoped to a **single pool** (single `PoolKey`). The vault stores the pool key at construction. Multi-pool support is achieved by deploying multiple vault instances.

### Token Fungibility

LONG and SHORT tokens are **fungible within a strike**. All minters at the same (pool, strike) share the same token. Payoffs are computed per-token against the aggregate collateral pool.

1 LONG + 1 SHORT always redeems for 1 USDC (the original mint ratio). No per-deposit tracking needed.

### Functions

- `mint(uint8 strikeIndex, uint256 usdcAmount)` — lock USDC, mint equal LONG + SHORT to caller (1 token per 1 USDC)
- `redeemPair(uint8 strikeIndex, uint256 tokenAmount)` — burn equal LONG + SHORT, return `tokenAmount` USDC
- `redeemLong(uint8 strikeIndex, uint256 tokenAmount)` — burn LONG, return `tokenAmount × longValuePerToken` USDC
- `redeemShort(uint8 strikeIndex, uint256 tokenAmount)` — burn SHORT, return `tokenAmount × shortValuePerToken` USDC
- `poke(uint8 strikeIndex)` — permissionless HWM update (reads oracle, applies decay)

### Events

```solidity
event Mint(address indexed depositor, uint8 strikeIndex, uint256 amount);
event RedeemPair(address indexed redeemer, uint8 strikeIndex, uint256 amount);
event RedeemLong(address indexed redeemer, uint8 strikeIndex, uint256 amount, uint256 payout);
event RedeemShort(address indexed redeemer, uint8 strikeIndex, uint256 amount, uint256 payout);
event HWMUpdated(uint8 strikeIndex, uint160 newHwmSqrtPrice, uint160 currentSqrtPrice);
```

### Oracle Manipulation Resistance

The FCI oracle's `Δ⁺` is updated only on full position exits (`afterRemoveLiquidity` with full burn). It cannot be manipulated by flash loans (which add/remove liquidity within one tx) because:
- `addTerm()` only fires on full position removal
- Block lifetime (`blockLifetime`) is floored to 1, so same-block add+remove contributes minimal weight
- The `accumulatedSum` is cumulative — a single term cannot dominate unless it represents genuinely concentrated fee capture over multiple blocks

`poke()` is therefore safe to be permissionless — the oracle value it reads is manipulation-resistant by construction.

## Sub-components

Two independent modules, each specified via type-driven development:

| Sub-component | Responsibility | Contains | Dependencies |
|---------------|---------------|----------|--------------|
| **PayoffMod** | Oracle conversion, HWM tracking, payoff computation | `deltaPlusToSqrtPriceX96()`, `applyDecay()`, `updateHWM()`, `computePayoff()` | Solady expWad, SqrtPriceLibrary (fractionToSqrtPriceX96, divX96) |
| **TokenVault** | Paired mint/burn, USDC custody, ERC-20 | mint, redeemPair, redeemLong, redeemShort, poke | PayoffMod, IFCIOracle |

PayoffMod is a single pure library containing all math: Q128→sqrtPriceX96 conversion, HWM decay, and payoff computation. TokenVault composes it.

## Development Chunks

### Chunk 1: PayoffMod Library
PayoffMod — single library containing `deltaPlusToSqrtPriceX96()`, `applyDecay()`, `updateHWM()`, `computePayoff()`. Pure math in sqrtPriceX96 space, testable in isolation. No game or vault dependency.

### Chunk 2: Scenario Validation Layer
Multi-round JIT game driver + HedgedVsUnhedged integration test. Validates that the sub-components from Chunk 1 correctly compensate hedged LPs under adversarial JIT scenarios generated by the Capponi game with real FCI hook readings.

### Chunk 3: Vault Contract + ERC-20 Tokens
FciLongToken, FciShortToken, IFciTokenVault, FciTokenVault. Wraps the validated Chunk 1 primitives with deposit/token/redemption logic. No surprises — payoff parameters already confirmed by Chunk 2.

## Invariants

### PayoffMod (HWM + Payoff)

- `hwmSqrtPrice ≥ decayed(previous_hwmSqrtPrice)` — decay only decreases between spikes
- Monotonically non-increasing between oracle spikes
- `poke()` is idempotent within the same block
- Deterministic from `(storedMaxSqrtPrice, lastUpdate, currentSqrtPrice, λ)`
- `longValue + shortValue = deposit` — always
- `longValue ≥ 0` and `shortValue ≥ 0` — neither side negative
- `longValue = 0` when `hwmSqrtPrice ≤ strikeSqrtPrice` — no payout below strike
- `longValue = deposit` when `(hwmSqrtPrice/strikeSqrtPrice)⁴ − 1 ≥ 1` — capped at deposit
- Monotonically non-decreasing in HWM (for LONG)

### Vault

- `USDC.balanceOf(vault) ≥ Σ totalDeposits[strike]` — fully collateralized always
- `longToken.totalSupply() == shortToken.totalSupply()` per strike — paired mint/burn
- `redeemPair(n)` always returns exactly `n` USDC — risk-free unwinding regardless of HWM
- `redeemLong(n) + redeemShort(n) = n USDC` — single-sided redemptions sum to pair value
- Minting `n` USDC increases both LONG and SHORT supply by `n` tokens
- `totalDeposits[strike] == longToken.totalSupply()` — 1:1 USDC backing per token

### Scenario Validation

- Equilibrium (no JIT, equal capital, equal lifetime): Δ⁺ = 0, payoff = 0, hedged == unhedged
- JIT crowd-out (high capital, short lifetime): Δ⁺ >> Δ*, payoff > 0, hedged > unhedged
- Below-strike Δ⁺: payoff = 0, hedged == unhedged (no false triggers)

## Branch Rules

- Branch `004-fci-token-vault` owns only plans in `docs/plans/` related to FCI tokenization and vault
- `research/` must stay synced across all feature branches per CLAUDE.md
- Implementation follows type-driven development: types and invariants first, implementation after
- PayoffMod specified via type-driven development before coding
- Scenario validation (Chunk 2) must pass before starting vault implementation (Chunk 3)
