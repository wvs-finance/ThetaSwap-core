# FCI Token Vault — Design Specification

Date: 2026-03-10
Branch: `004-fci-token-vault`
Status: Approved

## Problem

The FCI oracle (branches 001/003) computes per-pool fee concentration deviation (Δ⁺) for V4 hooks and V3 reactive adapters. To enable hedging markets for passive LPs, the oracle output needs to be tokenized into a composable ERC-20 that can trade on any CFMM independently.

## Architecture

Three independent layers (only Layer 2 is in scope):

```
Layer 1: FCI Oracle (exists — branches 001/003)
  │ vault calls getDeltaPlus() → raw Δ⁺ (Q128)
  │ vault converts: p_index = Δ⁺ / (Q128 − Δ⁺)   (Q128-scaled)
  ▼
Layer 2: FCI Token Vault (this branch — 004)
  │ LONG and SHORT are standard ERC-20s
  ▼
Layer 3: Any CFMM (future — branches 005/006)
```

The vault reads the oracle via `IFeeConcentrationIndex.getDeltaPlus()` — the existing interface on both the V4 hook and V3 reactive adapter. The vault performs the `p_index = Δ⁺/(1−Δ⁺)` conversion internally. All vault state (HWM, strikes) is denominated in p_index (Q128).

**Diamond proxy note:** The V4 FCI hook runs as a facet inside the MasterHook diamond. The vault must call `getDeltaPlus()` on the **MasterHook proxy address**, not the facet address. The oracle address stored in the vault is the proxy.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Oracle coupling | Standalone synthetic token (not position-bound) | Maximum composability — trades on any CFMM, usable as collateral |
| Peg mechanism | Collateral-vault mint/burn | Redeemable for USDC at payoff value — hard floor, arbitrage-enforced peg |
| Mint structure | Paired mint (LONG + SHORT) | Both sides get native instruments, no borrow market needed |
| Payoff function | Power-squared: ((HWM/p*)² − 1)⁺ | Matches research spec's optimal α=2 payoff, convexity baked into token |
| Strike selection | Depositor-chosen from standardized grid | Balances expressiveness with liquidity concentration |
| Strike grid | 3-4 per pool, anchored at econometric Δ* ≈ 0.09 | Calibrated from hazard model turning point |
| Token lifecycle | Perpetual, no expiry | No rollover friction for passive LPs |
| Lookback mechanism | High-water mark with exponential decay | O(1) storage/update, no cliffs, captures spikes with graceful fade |

## Token Design

### Paired Mint

Depositor locks D USDC, specifying strike index. Receives:

- **LONG-FCI(pool, p\*)** — ERC-20, gains value when concentration rises above p*
- **SHORT-FCI(pool, p\*)** — ERC-20, retains value when concentration stays below p*

Each (pool, strike) pair produces a distinct token pair.

### Payoff Computation

All values are **per token** (1 token = 1 USDC of original collateral):

```
quadratic_payoff = ((HWM / p*)² − 1)⁺

LONG value per token  = min(quadratic_payoff, 1) USDC
SHORT value per token = 1 − LONG value per token  USDC
```

- HWM ≤ p*: LONG = 0, SHORT = 1 USDC
- HWM = p* × √2: LONG = 1 USDC, SHORT = 0 (max payout)
- Between: smooth quadratic curve

Tokens are fungible across depositors at the same strike. No per-deposit state.

**Precision note:** `(HWM/p*)²` in Q128 produces a 256-bit intermediate (Q128 × Q128). Use `FixedPointMathLib.mulDiv` to avoid overflow.

### High-Water Mark

```
elapsed = block.timestamp − lastUpdate
decayedMax = storedMax × e^(−λ × elapsed)
newHWM = max(currentPindex, decayedMax)
```

Single storage slot: `(hwm, lastUpdate)`. O(1) reads and writes. No keepers.

Starting parameter: half-life = 14 days (λ = ln(2) / 14 days). Calibrated from hazard model lag structure.

**Implementation:** Decay uses Solady's `expWad()` with conversion at the boundary: compute `exp(-λ × elapsed)` in WAD scale, then scale the result to Q128 for multiplication with `storedMax`.

### Strike Grid

Example for ETH/USDC 30bps:

| Strike | Δ* equivalent | Meaning |
|--------|--------------|---------|
| p* = 0.05 | Δ ≈ 0.048 | Early warning |
| p* = 0.10 | Δ ≈ 0.091 | Econometric turning point |
| p* = 0.25 | Δ ≈ 0.200 | Tail protection |

Grid is immutable per vault deployment.

## Vault Contract

### State

```
// Immutable (set at construction)
PoolKey     poolKey;            // the pool this vault tracks
IERC20      collateral;         // USDC
IFeeConcentrationIndex oracle;  // MasterHook proxy or ReactiveHookAdapter
bool        reactive;           // false for V4, true for V3 adapter
uint128[]   strikes;            // standardized p* grid (Q128)

// Per-strike state
struct StrikeState {
    ERC20      longToken;       // deployed at vault init
    ERC20      shortToken;      // deployed at vault init
    uint128    hwm;             // high-water mark in p_index (Q128)
    uint64     lastUpdate;      // timestamp of last HWM update
    uint256    totalDeposits;   // aggregate USDC locked at this strike
}
mapping(uint8 => StrikeState) strikes;
```

### Oracle Interface

Uses the existing `IFeeConcentrationIndex` interface (no new interface). The vault stores the oracle address (MasterHook proxy for V4, or ReactiveHookAdapter for V3).

```solidity
import {IFeeConcentrationIndex} from "src/fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
```

The vault reads raw `Δ⁺` via `getDeltaPlus(key, reactive)` and converts to `p_index = Δ⁺ / (Q128 − Δ⁺)` internally using Solady's `FixedPointMathLib` for the division in Q128 scale. The exponential decay uses Solady's `expWad()` with WAD↔Q128 conversion at the boundary.

### Scope: One Vault Per Pool

Each vault deployment is scoped to a **single pool** (single `PoolKey`). The vault stores the pool key at construction. Multi-pool support is achieved by deploying multiple vault instances.

### Token Fungibility

LONG and SHORT tokens are **fungible within a strike**. All minters at the same (pool, strike) share the same token. Payoffs are computed per-token against the aggregate collateral pool:

```
LONG value per token = min(((HWM / p*)² − 1)⁺, 1) USDC
SHORT value per token = 1 − LONG value per token    USDC
```

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
event HWMUpdated(uint8 strikeIndex, uint128 newHwm, uint128 pIndex);
```

### Oracle Manipulation Resistance

The FCI oracle's `Δ⁺` is updated only on full position exits (`afterRemoveLiquidity` with full burn). It cannot be manipulated by flash loans (which add/remove liquidity within one tx) because:
- `addTerm()` only fires on full position removal
- Block lifetime (`blockLifetime`) is floored to 1, so same-block add+remove contributes minimal weight
- The `accumulatedSum` is cumulative — a single term cannot dominate unless it represents genuinely concentrated fee capture over multiple blocks

`poke()` is therefore safe to be permissionless — the oracle value it reads is manipulation-resistant by construction.

## Sub-components

Three independent modules, each specified via type-driven development:

| Sub-component | Responsibility | Dependencies |
|---------------|---------------|--------------|
| **HighWaterMark** | Decaying max tracking | None (pure math) |
| **PayoffEngine** | Quadratic payoff computation | None (pure math) |
| **TokenVault** | Paired mint/burn, USDC custody, ERC-20 | HighWaterMark, PayoffEngine, IFCIOracle |

HWM and PayoffEngine are pure libraries. TokenVault composes them.

## Invariants

### HWM

- `hwm ≥ decayed(previous_hwm)` — decay only decreases between spikes
- Monotonically non-increasing between oracle spikes
- `poke()` is idempotent within the same block
- Deterministic from `(storedMax, lastUpdate, currentPindex, λ)`

### Payoff

- `longValue + shortValue = deposit` — always
- `longValue ≥ 0` and `shortValue ≥ 0` — neither side negative
- `longValue = 0` when `hwm ≤ p*` — no payout below strike
- `longValue = deposit` when `(hwm/p*)² − 1 ≥ 1` — capped at deposit
- Monotonically non-decreasing in HWM (for LONG)

### Vault

- `USDC.balanceOf(vault) ≥ Σ totalDeposits[strike]` — fully collateralized always
- `longToken.totalSupply() == shortToken.totalSupply()` per strike — paired mint/burn
- `redeemPair(n)` always returns exactly `n` USDC — risk-free unwinding regardless of HWM
- `redeemLong(n) + redeemShort(n) = n USDC` — single-sided redemptions sum to pair value
- Minting `n` USDC increases both LONG and SHORT supply by `n` tokens
- `totalDeposits[strike] == longToken.totalSupply()` — 1:1 USDC backing per token

## Branch Rules

- Branch `004-fci-token-vault` owns only plans in `docs/plans/` related to FCI tokenization and vault
- `research/` must stay synced across all feature branches per CLAUDE.md
- Implementation follows type-driven development: types and invariants first, implementation after
- Each sub-component (HWM, PayoffEngine, TokenVault) specified individually before coding
