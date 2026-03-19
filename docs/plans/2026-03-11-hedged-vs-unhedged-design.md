# Hedged-vs-Unhedged Scenario Validation — Design Specification

Date: 2026-03-11
Branch: `004-fci-token-vault`
Status: Draft

## Problem

The FCI Token Vault sub-components (payoff library, HWM decay, ERC-6909 tokens) are unit-tested in isolation but never validated against realistic JIT scenarios with actual collateral flow. Before extending the vault (delta-hedging, LONG/SHORT markets), we need to prove that a single upfront hedge deposit compensates a passive LP under adversarial JIT extraction — using real FCI hook readings, real swaps, and real vault interactions.

## Architecture

Three deliverables:

1. **`poke()` function** — new free function in `FciTokenVaultMod` + external on `FciTokenVaultFacet`. Reads Δ⁺ from FCI oracle via `PoolKey.hooks`, converts to sqrtPrice, applies decay, updates HWM.
2. **Storage expansion** — `FciVaultStorage` gets `PoolKey` and `bool reactive` fields appended to the END of the struct (preserving existing field positions).
3. **Integration test contract** — fork test deploying real FCI hook + pool + vault. Runs three scenarios with two PLPs (hedged vs unhedged). Asserts six acceptance properties.

No mocks except `deal()` for initial token balances. Everything else is real contracts end-to-end.

## Storage Changes

`FciVaultStorage` appends two fields at the END of the struct:

```
address collateralToken;    // (existing, last current field)
PoolKey poolKey;             // the pool this vault tracks (poolKey.hooks = oracle address)
bool reactive;               // false for V4, true for V3 adapter
```

The oracle address is derived from `poolKey.hooks` — no separate oracle field needed. The vault calls `IFeeConcentrationIndex(address(poolKey.hooks)).getDeltaPlus(poolKey, reactive)`.

## `poke()` Function

Module-level free function in `FciTokenVaultMod.sol`:

```
poke():
  1. vs = getFciVaultStorage()
  2. require(!vs.settled)
  3. deltaPlus = IFeeConcentrationIndex(address(vs.poolKey.hooks))
       .getDeltaPlus(vs.poolKey, vs.reactive)
  4. currentSqrtPrice = deltaPlusToSqrtPriceX96(deltaPlus)
  5. dt = block.timestamp - vs.lastHwmTimestamp
  6. decayed = applyDecay(vs.sqrtPriceHWM, dt, vs.halfLifeSeconds)
  7. vs.sqrtPriceHWM = updateHWM(decayed, currentSqrtPrice)
  8. vs.lastHwmTimestamp = block.timestamp
```

Facet: `function poke() external { _poke(); }`

Harness: `function harness_poke() external { poke(); }`

`poke()` propagates oracle reverts (strict) — if the hook address is invalid or pool not initialized, the call reverts. No try/catch.

## Delta-Plus Read Path

The test does NOT use `JitGameResult.deltaPlus` for vault assertions. The game's internal delta-plus reading goes through the harness interface (`IFCIDeltaPlusReader(PoolId)`), which is a test convenience. The vault's `poke()` reads through the production interface (`getDeltaPlus(PoolKey, bool)`). These are independent read paths — the vault state after `poke()` is what matters for welfare assertions.

`JitGameResult.deltaPlus` values may be logged for debugging but are not used in acceptance property assertions.

## Collateral Model

The collateral token is one of the pool tokens (currency1 / "USDC" side). The hedged PLP redirects part of their LP capital to the vault — they have less liquidity in the pool than the unhedged PLP.

```
Hedged PLP:   LP position (C - hedgeAmount) + vault LONG exposure
Unhedged PLP: LP position (C)
```

No separate premium parameter. The cost of hedging is organic: reduced fee income from a smaller LP position.

## Welfare Metric

```
hedged_welfare   = fees_from_smaller_position + longPayout
unhedged_welfare = fees_from_full_position
```

Where:
- `fees_from_*_position` = net fee revenue only, computed as `tokenBalanceAfterBurn - tokenBalanceBeforeMint` for both tokens, converted to collateral denomination (currency1) using the pool's current sqrtPrice. Both token0 and token1 deltas are accounted for.
- `longPayout` = vault LONG redemption value after settlement (from `longPayoutPerToken * deposit / Q96`)

## Test Contract

File: `test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol`

### LP Management

The test manages LP positions manually — it does NOT reuse `runMultiRoundJitGame`'s LP entry/exit, since that function mints all passive LPs with identical `UNIT_LIQUIDITY`. The test needs asymmetric LP sizes (hedged PLP has less liquidity).

The test reuses only the swap + JIT entry/exit mechanics from the game infrastructure. LP mint/burn is orchestrated directly by the test.

### setUp

Same as existing fork tests: deploy PoolManager, currencies, FCI hook via HookMiner, init pool. Additionally deploy vault (via harness) with:
- `collateralToken = currency1`
- `sqrtPriceStrike` = sqrtPrice corresponding to Δ* ≈ 0.09
- `poolKey` = the initialized pool's key
- `reactive = false` (V4 native)
- `halfLifeSeconds = 14 days`
- `expiry = block.timestamp + 365 days` (far future, manually settle via vm.warp)

Two PLPs with equal starting capital `C`:
- Hedged PLP (index 0): deposits `hedgeAmount` into vault, LPs with `C - hedgeAmount`
- Unhedged PLP (index 1): LPs with full `C`

### Scenario Matrix

| Test | JIT probability | JIT capital | Rounds | Expected |
|------|----------------|-------------|--------|----------|
| `test_equilibrium_no_jit` | 0% | — | 3 | Δ⁺ ≈ 0, LONG = 0, hedged < unhedged |
| `test_jit_crowdout_hedge_compensates` | 100% | large | 3 | Δ⁺ >> strike, LONG > 0, hedged > unhedged |
| `test_below_strike_no_false_trigger` | 100% | small | 3 | Δ⁺ > 0 but < strike, LONG = 0, hedged < unhedged |

### Test Flow (each scenario)

1. Mint starting capital `C` to both PLPs (via `deal()`)
2. Hedged PLP: approve + deposit `hedgeAmount` into vault, LP with `C - hedgeAmount`
3. Unhedged PLP: LP with full `C`
4. Run K rounds: each round executes swap + JIT entry/exit → call `poke()` after each round
5. Both PLPs exit positions (burn liquidity, collect fees)
6. Compute fee revenue: `fees = tokenBalanceAfterBurn - tokenBalanceBeforeMint` for each PLP
7. `vm.warp` past expiry → `settle()` → hedged PLP calls `redeem()`
8. Compute welfare: `hedged = fees + longPayout`, `unhedged = fees`
9. Assert properties + log metrics

## Acceptance Properties

All six must pass before any delta-hedging extensions.

| # | Property | Tested in | Assertion |
|---|----------|-----------|-----------|
| 1 | Payoff compensation | `test_jit_crowdout_hedge_compensates` | `hedged_welfare > unhedged_welfare` |
| 2 | No false trigger | `test_equilibrium_no_jit` + `test_below_strike_no_false_trigger` | `longPayout == 0`, `hedged_welfare < unhedged_welfare` |
| 3 | Vault solvency | All three scenarios | After all redeems, `collateralToken.balanceOf(vault) >= totalDeposits` (vault never underpays) |
| 4 | HWM captures current price | `test_jit_crowdout_hedge_compensates` | After each `poke()`, `sqrtPriceHWM >= currentSqrtPrice` for that round |
| 5 | Decay effect | `test_jit_crowdout_hedge_compensates` with time gaps | `decayedHWM < rawHWM` when rounds are spaced apart |
| 6 | Break-even premium | `test_jit_crowdout_hedge_compensates` | Log `hedged_welfare - unhedged_welfare` (observational, no assertion) |

## Scope Boundaries

NOT building:
- Delta-hedging (round-by-round deposits) — next iteration after these six properties pass
- LONG/SHORT market or pricing model — PLP holds both tokens, welfare uses longPayout directly
- Oracle interface changes — vault stores full `PoolKey`, reads via existing `getDeltaPlus(PoolKey, reactive)`
- New actors beyond the two PLPs + JIT + swapper
- Keeper bot — test calls `poke()` explicitly after each round
- Expiry logic changes — `vm.warp` past expiry, call `settle()`
- Changes to `JitGame.sol` — only reuse swap + JIT mechanics, LP management is manual

## Dependencies

- `FciTokenVaultMod.sol` — add `poke()`, expand `FciVaultStorage` with `poolKey` + `reactive` (appended at end)
- `FciTokenVaultFacet.sol` — add external `poke()`
- `FciTokenVaultHarness.sol` — add `harness_poke()`, update `harness_initVault` to accept `PoolKey`, `reactive`, and `collateralToken`; add `harness_getPoolKey()` and `harness_getReactive()` accessors; update `harness_getVaultStorage` to include all storage fields
- `IFciTokenVault.sol` — add `poke()` to interface
- `IFeeConcentrationIndex.sol` — no changes (use existing `getDeltaPlus(PoolKey, bool)`)
- `JitGame.sol` — no changes (test orchestrates LP management manually, reuses only swap/JIT mechanics)
- `SqrtPriceLookbackPayoffX96Lib.sol` — no changes (reuse existing functions)
