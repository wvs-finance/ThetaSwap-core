# Cross-Epoch Welfare Comparison: Cumulative vs Epoch Δ⁺

## Purpose

Validate whether epoch-reset Δ⁺ produces fairer hedging outcomes than cumulative Δ⁺ by running scenarios that **cross epoch boundaries**. Within a single epoch, cumulative and epoch metrics are identical — divergence only appears when the epoch resets and cumulative keeps growing.

This is the **go/no-go gate** before investing in reactive dispatch (Task 9) and fork simulation. If epoch doesn't produce measurably better welfare outcomes in cross-epoch scenarios, further integration work is not justified.

## Architecture

### Dual-Vault Comparison

Both vaults watch the **same FCI hook and pool**, so they see identical market conditions:

```
                    ┌─────────────┐
                    │  FCI Hook   │
                    │ (addStateTerm + addEpochTerm)
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │                         │
     ┌────────▼────────┐      ┌────────▼────────┐
     │ Cumulative Vault │      │   Epoch Vault   │
     │  harness_poke()  │      │harness_pokeEpoch│
     │ getDeltaPlus()   │      │getDeltaPlusEpoch│
     └─────────────────┘      └─────────────────┘
```

- Same `PoolKey`, same `FeeConcentrationIndexHarness`
- Same strike price, half-life, expiry, collateral
- Same deposit amount from same depositor
- Same hedged/unhedged PLPs, same JIT LP, same swapper
- Only difference: which `getDeltaPlus*` the vault reads at poke time

### Epoch Length & Poke Ordering

`EPOCH_LENGTH = 1 day`, `ROUND_INTERVAL = 1 day`.

**Critical: poke BEFORE warp.** The `epochDeltaPlus` view returns 0 when `block.timestamp >= epochId + epochLength`. If we warp first, the epoch is expired by the time the vault reads it. So each round must:
1. LP entry → JIT → swap → burns → **poke both vaults** (reads Δ⁺ within current epoch)
2. Then `vm.warp(block.timestamp + ROUND_INTERVAL)` (advances clock to next epoch)

This ensures the epoch vault reads the current epoch's Δ⁺ before the boundary, while the next round's `addEpochTerm` writes to a fresh epoch (triggered by the expiry check on write).

### Welfare Metrics

Follows the PnL model from `research/backtest/pnl.py`:

```
pnl_unhedged = fees - il_cost
pnl_hedged   = (1 - γ) * fees - il_cost + payouts
hedge_value  = pnl_hedged - pnl_unhedged = payouts - γ * fees
```

Where `γ` is the premium rate (fraction of fees paid to the insurance pool). The hedged PLP **pays** `γ * fees` as premium and **receives** LONG token payouts when the trigger fires. `hedge_value > 0` means hedging was profitable; `hedge_value < 0` means the PLP overpaid for protection.

In the Solidity test, the simplified equivalent is:
- `fees` = LP token balance delta (same for hedged and unhedged since same pool, same capital)
- `payouts` = `longPayout` from vault settlement
- `premium` = `HEDGE_AMOUNT` (the deposit into the vault — the hedged PLP locks this capital)
- `pnl_unhedged` = `lpFeeRevenue` (keeps all fees + keeps HEDGE_AMOUNT as capital)
- `pnl_hedged` = `lpFeeRevenue + longPayout - HEDGE_AMOUNT` (pays premium, gets payout)
- `hedge_value` = `longPayout - HEDGE_AMOUNT` (positive = hedge was worth it)

For each scenario, report both vault variants:

| Metric | Source |
|--------|--------|
| `cumLongPayout` / `epochLongPayout` | Respective vault settlement |
| `cumHedgeValue` | `cumLongPayout - HEDGE_AMOUNT` |
| `epochHedgeValue` | `epochLongPayout - HEDGE_AMOUNT` |
| `lpFeeRevenue` | LP token balance delta (same for both, since same pool) |
| Per-round `cumDp` / `epochDp` | Logged via `console.log` for qualitative analysis |

The key comparison: when JIT stops, `cumHedgeValue` stays positive (overpaying — PLP didn't need the hedge), while `epochHedgeValue` should drop negative (correctly: hedge cost exceeds payout since no JIT is occurring).

## Scenarios

### Scenario 4: JIT-Then-Clean (the critical case)

**Setup**: EPOCH_LENGTH = 1 day, 3 rounds, each round crosses epoch boundary.

| Round | JIT enters? | Expected cumulative Δ⁺ | Expected epoch Δ⁺ |
|-------|------------|----------------------|-------------------|
| 1 | Yes (9x capital) | High | High |
| 2 | No | Higher (monotonic) | Near-zero (reset) |
| 3 | No | Even higher | Near-zero (reset) |

**Expected welfare outcome**:
- `cumulativeLongPayout > epochLongPayout` — cumulative overpays because it remembers Round 1 JIT forever
- `epochLongPayout ≈ 0` or small — epoch correctly reflects that Rounds 2-3 had no JIT
- This demonstrates **epoch is fairer**: unhedged PLP isn't suffering in Rounds 2-3, so paying LONG is a false trigger

**Assertions**:
- `cumulativeLongPayout > 0` — cumulative triggers (correct for cumulative semantics)
- `epochLongPayout < cumulativeLongPayout` — epoch produces strictly less payout when JIT stops
- Conservation holds for both vaults

### Scenario 5: Alternating JIT/Clean (responsiveness test)

**Setup**: EPOCH_LENGTH = 1 day, 4 rounds.

| Round | JIT enters? | Expected cumulative Δ⁺ | Expected epoch Δ⁺ |
|-------|------------|----------------------|-------------------|
| 1 | Yes | High | High |
| 2 | No | Higher | Near-zero |
| 3 | Yes | Even higher | High again |
| 4 | No | Even higher still | Near-zero again |

**Expected welfare outcome**:
- Cumulative vault Δ⁺ only grows — it cannot distinguish JIT rounds from clean rounds
- Epoch vault Δ⁺ oscillates — responsive to current-epoch conditions
- `cumulativeLongPayout > epochLongPayout` — cumulative over-signals

**Assertions**:
- Both `cumulativeLongPayout > 0` and `epochLongPayout > 0` — both detect JIT occurred
- `epochLongPayout < cumulativeLongPayout` — epoch doesn't over-count clean rounds
- Conservation holds for both vaults

### Scenario 6: Recovery After Initial JIT

**Setup**: EPOCH_LENGTH = 1 day, 5 rounds.

| Round | JIT enters? |
|-------|------------|
| 1 | Yes (9x capital) |
| 2 | No |
| 3 | No |
| 4 | No |
| 5 | No |

**Expected welfare outcome**:
- Cumulative Δ⁺ stays permanently elevated across all 5 rounds
- Epoch Δ⁺ is high in Round 1, then zero in Rounds 2-5
- `epochLongPayout` should be **significantly** less than `cumulativeLongPayout`
- With 14-day half-life and 5-day span, cumulative HWM barely decays — so cumulative vault dramatically overpays

**Assertions**:
- `cumulativeLongPayout > 0` — cumulative never forgets
- `epochLongPayout < cumulativeLongPayout` — epoch recovers
- `epochLongPayout < cumulativeLongPayout / 2` — epoch payout is significantly less (not just marginally)
- Conservation holds for both vaults

**Note on decay**: With 14-day half-life, Round 1's HWM retains ~82% after 4 days of decay (`2^(-4/14) ≈ 0.82`). The epoch vault only receives nonzero Δ⁺ in Round 1, so its HWM decays without refresh. At settlement (~day 6-7), decayed HWM may still exceed strike, making `epochLongPayout > 0` possible. The key assertion is the relative comparison, not exact zero.

## Test Structure

Single test contract: `test/fci-token-vault/integration/CrossEpochWelfareComparison.integration.t.sol`

```
contract CrossEpochWelfareComparisonTest is PosmTestSetup, FCITestHelper {
    FciTokenVaultHarness cumulativeVault;
    FciTokenVaultHarness epochVault;

    // EPOCH_LENGTH = 1 day (each round = new epoch)
    // ROUND_INTERVAL = 1 day (matches epoch length)
    // Strike, half-life, expiry, collateral — same for both vaults

    setUp():
        - Deploy FCI hook + pool
        - initializeEpochPool(key, EPOCH_LENGTH)
        - Deploy cumulativeVault with harness_initVault(strike, 14 days, block.timestamp + 7 days, key, false, collateral)
        - Deploy epochVault with harness_initVault(strike, 14 days, block.timestamp + 7 days, key, false, collateral)
        - Depositor funds both vaults with HEDGE_AMOUNT each

    _runCrossEpochRound(bool jitEnters, uint256 jitCapital):
        - Same LP mechanics as existing _runRound (mint, roll, JIT, swap, burn)
        - Log cumDp and epochDp BEFORE poke
        - Poke BOTH vaults BEFORE warp: cumulativeVault.harness_poke() + epochVault.harness_pokeEpoch()
        - THEN vm.warp(block.timestamp + ROUND_INTERVAL) to cross epoch boundary

    test_scenario4_jit_then_clean()
    test_scenario5_alternating_jit_clean()
    test_scenario6_recovery_after_initial_jit()
}
```

## Expiry & Decay Consideration

With `ROUND_INTERVAL = 1 day` and up to 5 rounds (Scenario 6), expiry must accommodate all rounds plus settlement gap. Set `expiry = block.timestamp + 7 days` to fit 5 rounds + 2-day settlement gap.

**Expected decay factors at settlement** (14-day half-life, poke-before-warp ordering):
- Scenario 4 (3 rounds): last poke at ~day 2, settlement at ~day 7. Decay gap ~5 days → retention `2^(-5/14) ≈ 0.78`
- Scenario 5 (4 rounds): last poke at ~day 3, settlement at ~day 7. Decay gap ~4 days → retention `2^(-4/14) ≈ 0.82`
- Scenario 6 (5 rounds): last poke at ~day 4, settlement at ~day 7. Decay gap ~3 days → retention `2^(-3/14) ≈ 0.86`

## Edge Cases Not Covered (future work)

- **Cross-epoch-boundary position lifetime**: a position entering in epoch N and exiting in epoch N+1. In the current test design, all positions enter and exit within a single round (within one epoch). `addEpochTerm` handles this correctly (writes to the new epoch on expiry), but no test currently exercises it.

## Success Criteria

The epoch metric is validated if:
1. All 3 cross-epoch scenarios show `epochLongPayout < cumulativeLongPayout` when JIT stops
2. Epoch Δ⁺ demonstrably resets across epoch boundaries (visible in per-round logs)
3. Epoch vault does not overpay when unhedged PLP is not being harmed (no false trigger in clean rounds)

If these hold → proceed to fork simulation and reactive dispatch.
If these fail → epoch metric needs redesign or abandonment.
