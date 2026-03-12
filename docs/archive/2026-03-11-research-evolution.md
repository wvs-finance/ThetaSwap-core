# Research Evolution: Reserve-Based → Payoff-Based Insurance Model

Date: 2026-03-11

## Context

The ThetaSwap insurance mechanism evolved from a reserve-based pool model to a direct payoff model. Two research modules (`sweep.py`, `reserve.py`) implemented the earlier reserve approach and are now superseded. This document captures the key learnings before archiving.

## Superseded Files

### `backtest/reserve.py` — Reserve Simulation

**What it did**: Day-by-day simulation of a shared insurance reserve pool. Premiums flow in from exiting positions, payouts flow out when `delta_plus > delta_star`.

**Key design**: Payout formula `D = (Δ⁺ - Δ*) / (1 - Δ*) × balance` — a linear ramp from the strike threshold, capped at available balance. This made payouts proportional to both severity and pool balance.

**Why superseded**: The reserve model couples all LPs through a shared balance. One LP's payout depends on others' premium timing, creating cross-position externalities. The payoff-based model (lookback put with exponential decay) gives each position an independent payout determined solely by its own epoch's concentration metric.

**Retained learning**: The `delta_star` strike threshold concept carried forward as the strike price in the lookback payoff. The trigger condition `Δ⁺ > strike` is structurally identical.

### `backtest/sweep.py` — Gamma Sweep Orchestrator

**What it did**: Ran backtests across a grid of `gamma` (premium rate) values. For each gamma, computed lifetime premiums per position, simulated the reserve, computed per-position PnL, and aggregated into `BacktestResult`.

**Key design**: Premium = `gamma × lifetime_fees`, collected at burn date. This meant premium was proportional to actual fee revenue, not capital deployed. The sweep found the gamma that maximized `pct_better_off` (fraction of positions where hedging was profitable).

**Why superseded**: With the payoff model, there's no reserve to sweep over. Premium is now a fixed deposit into the vault (collateral for SHORT tokens), and the payoff is determined by the FCI oracle, not a reserve balance. The sweep concept lives on in `mechanism_sweep.py` which sweeps epoch length and decay parameters instead.

**Retained learning**: The `hedge_value = payouts - gamma × fees` metric carried forward directly into the welfare comparison tests. The `pct_better_off` metric informed the design of the hedged-vs-unhedged welfare assertions.

## Evolution Summary

| Aspect | Reserve Model | Payoff Model |
|--------|--------------|-------------|
| Premium | `γ × lifetime_fees` (proportional) | Fixed deposit (collateral) |
| Payout trigger | `Δ⁺ > Δ*` with linear ramp | `Δ⁺ > strike` with lookback put payoff |
| Pool coupling | Shared reserve (cross-position externality) | Independent per-vault (no externality) |
| Key parameter | `gamma` (premium rate) | Epoch length, decay half-life |
| Sweep target | `pct_better_off` across gammas | Welfare comparison across mechanism params |
| Oracle | Cumulative Δ⁺ only | Epoch-reset Δ⁺ (fairer, validated) |

## Archived Files

Originals moved to `research/_archive/`:
- `research/_archive/sweep.py` (was `backtest/sweep.py`)
- `research/_archive/reserve.py` (was `backtest/reserve.py`)
