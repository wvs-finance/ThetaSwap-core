# Historical Backtest Design: ETH/USDC 30bps Fee Concentration Insurance

**Date**: 2026-03-05 | **Branch**: `002-theta-swap-cfmm`
**Pool**: ETH/USDC 30bps (0x8ad599c3...eb6e6d8)
**Window**: 2025-12-05 to 2026-01-14 (41 days, 600 positions)

## Purpose

Compare actual realized PLP P&L against counterfactual hedged P&L using the ThetaSwap hybrid insurance mechanism (main.pdf §6). Demonstrates that PLPs who exited during high fee concentration would have been better off with insurance. Sweep premium factor gamma to find the optimal rate and validate the econometric WTP calibration.

## Inputs (All Existing)

| Input | Source | Granularity |
|---|---|---|
| `DAILY_AT_MAP` | econometrics/data.py (Dune Q6) | pool-day, 41 days |
| `DAILY_AT_NULL_MAP` | econometrics/data.py (Dune Q6) | pool-day, 41 days |
| `IL_MAP` | econometrics/data.py (Dune Q5) | pool-day, 41 days |
| `RAW_POSITIONS` | econometrics/data.py (Dune Q4v2) | 600 positions |

No new Dune queries required.

### Derived Daily

- Delta_plus(t) = max(0, A_T_real(t) - A_T_null(t))
- Trigger(t) = 1 if Delta_plus(t) > Delta_star = 0.09

### Per-Position Approximation

- Mint date = burn_date - blocklife/7200 (existing `approximate_mint_date`)
- Alive days = [mint_date, burn_date] intersect [window_start, window_end]
- Fee share x_k = 1/N(t) for passive positions (conservative: actual passive shares <= 1/N due to JIT dilution, so unhedged P&L is an upper bound)
- Daily fee income per position = pool_daily_fee * (1/N(t))
- `pool_daily_fee`: documented assumption ($50K/day), with sensitivity check

## Reserve Simulation (Pool Level)

Simulates R(t) per day following main.pdf §6 (INS-01 through INS-05).

### State

- R(t): reserve balance (USDC)
- D(t): donate amount (0 if no trigger)
- N_insured(t): count of alive insured positions

### Daily Step

1. **Premium collection** (§6.1, eq 15): For each position exiting on day t:
   - premium_i = gamma * fee_income_i
   - R(t) += premium_i
   - Note: premium enters R only at afterRemoveLiquidity (position exit)

2. **Trigger check** (INS-03): Compute Delta_plus(t) = max(0, A_T(t) - A_T_null(t))
   - If Delta_plus(t) > Delta_star = 0.09:
     - D = (Delta_plus - Delta_star) / (1 - Delta_star) * R  (eq 16)
     - actual_payout = min(D, R)  (INS-01 solvency)
     - R(t) -= actual_payout
     - Distribute pro-rata to all alive insured positions (INS-05)

3. **Track**: R(t), cumulative premiums, cumulative payouts, trigger days

### Bootstrapping Dynamic

Reserve grows only when positions exit. Early trigger events have limited payout. The gamma sweep reveals how this scales.

## Position-Level P&L Attribution

For each of 600 positions, two tracks:

### Unhedged

```
PnL_unhedged_i = fees_earned_i - IL_i
```

- fees_earned_i = sum over alive_days of pool_daily_fee * (1/N(t))
- IL_i = sum over alive_days of IL(t)

### Hedged(gamma)

```
PnL_hedged_i(gamma) = (1 - gamma) * fees_earned_i - IL_i + payouts_received_i
```

- payouts_received_i = sum of pro-rata donate() on trigger days while alive
- Pro-rata: 1/N_insured(t) per trigger day (equal weight approximation)

### Per-Position Metrics

- hedge_value_i(gamma) = PnL_hedged_i - PnL_unhedged_i
- break_even_gamma_i: gamma where hedged = unhedged

### Aggregate Metrics

- Mean/median hedge value
- % of positions better off hedged
- Breakdown: positions exiting on high-Delta_plus days vs low

## Gamma Sweep + Econometric Calibration

### Sweep Values

gamma in {0.01, 0.05, 0.10, 0.20, gamma_star}

### Econometric gamma* Derivation

From marginal effect analysis: WTP ~ $110 per position at Delta = 0.15.

```
gamma_star = WTP / avg_fees_earned_per_position
```

This is the break-even premium rate — maximum gamma a rational PLP accepts.

### Output Per Gamma

| Metric | Purpose |
|---|---|
| Reserve R(t) trajectory | Bootstrapping: does R build fast enough? |
| Total premiums collected | Cost side |
| Total payouts distributed | Benefit side |
| % of positions better off hedged | Adoption threshold |
| Mean hedge value | Net benefit |
| Reserve utilization (payouts / peak R) | Solvency stress |
| Trigger day count | How often Delta_plus > 0.09 |

## Project Structure

```
backtest/
  __init__.py
  types.py          # PositionPnL, ReserveState, BacktestResult, GammaSweepResult
  reserve.py        # simulate_reserve(positions, daily_data, gamma, delta_star)
  pnl.py            # compute_position_pnl(position, daily_data, reserve_states, gamma)
  calibrate.py      # derive_gamma_star(wtp, avg_fees)
  sweep.py          # run_gamma_sweep(gammas, ...)
  plotting.py       # money_plot, reserve_plot, hedge_distribution_plot
```

All pure functions, frozen dataclasses, @functional-python patterns.

## Notebook: eth-usdc-backtest.ipynb

1. **Setup** — imports, load data from econometrics.data
2. **Trigger days** — which days Delta_plus > Delta_star, visualize Delta_plus(t)
3. **Reserve simulation** — R(t) trajectory at each gamma
4. **Money plot** — hedged vs unhedged cumulative P&L (the key chart)
   - X: day, Y: cumulative P&L
   - Lines: unhedged (red), hedged per gamma (green gradient)
   - Background shading on trigger days
   - Subplot: Delta_plus(t) with Delta_star threshold
5. **Position-level distribution** — histogram of hedge_value_i
6. **gamma* calibration** — econometric derivation, placement in sweep
7. **Summary table** — one row per gamma, all aggregate metrics

## Calibration Assumptions

| Parameter | Value | Justification |
|---|---|---|
| pool_daily_fee | $50,000/day | Conservative for ETH/USDC 30bps |
| Delta_star | 0.09 | Econometric turning point (lp-insurance-demand.tex §5) |
| WTP | $110 | Marginal effect at Delta = 0.15 (lp-insurance-demand.tex §6.2) |
| N(t) | derived from RAW_POSITIONS alive on day t | Existing data |

## Verification

- INS-01: R(t) >= 0 at all times
- INS-03: donate() fires iff Delta_plus > Delta_star
- INS-05: sum of payouts = actual_payout (pro-rata conservation)
- Premium conservation: total premiums in = total premiums collected from exiting positions
- Hedge value monotonicity: higher gamma -> more protection but higher cost (inverted-U in gamma)
