# Backtest Simulation Design: ThetaSwap Fee Concentration Hedge

**Date**: 2026-03-04 | **Branch**: `002-theta-swap-cfmm`
**Audience**: LP demo — intuitive, visual storytelling
**Approach**: Python package (`simulation/`) + Jupyter notebook (`notebooks/demo.ipynb`)

## Purpose

Demonstrate to prospective PLPs how ThetaSwap's fee concentration derivative hedges against JIT competition risk. Show hedged vs unhedged P&L, ecosystem welfare, and CFMM mechanics through a narrative arc of three scenarios.

## Project Structure

```
simulation/
├── __init__.py
├── config.py           # Scenario parameters, deployment constants (YAML or dataclass)
├── cfmm.py             # CFMM state machine: reserves, trading function, price
├── index.py            # A_T evolution: synthetic scenario generators
├── funding.py          # Funding rate, premium, dynamic fee logic
├── agents.py           # PLP and Underwriter agent models
├── metrics.py          # P&L, welfare, TVL computations
├── plotting.py         # All matplotlib figure builders
└── scenarios.py        # Pre-built scenario configs (calm, gradual, shock)

notebooks/
└── demo.ipynb          # Narrative notebook: imports simulation/, runs scenarios, shows plots

pyproject.toml          # Dependencies: numpy, scipy, matplotlib, jupyter
```

Each module is a pure-function library operating on numpy arrays or frozen dataclasses. No global state.

## Core Math (from `specs/model/`)

### CFMM State (`cfmm.py`)

From the LaTeX spec:

| Formula | Source | Code |
|---------|--------|------|
| `V_LP(p) = ln(1 + p)` | payoff.tex eq 5 | `payoff(p)` |
| `ψ(x, y) = y + ln(x) + 1 - x = 0` | trading-function.tex eq 13 | `invariant(x, y)` |
| `x(p) = 1/(1+p)` | reserves.tex eq 6 | `risky_reserve(p)` |
| `y(p) = ln(1+p) - p/(1+p)` | reserves.tex eq 8 | `numeraire_reserve(p)` |
| `p = (1-x)/x` | trading-function.tex eq 17 | `spot_price(x)` |
| `x_0 = L_0*(1-A_0)` | initialization.tex eq init-x | `init_reserves(A_0, L_0)` |
| `y_0 = L_0*(-ln(1-A_0) - A_0)` | initialization.tex eq init-y | `init_reserves(A_0, L_0)` |

State: `@dataclass(frozen=True) CFMMState: x, y, L, p`

### Fee Concentration Index (`index.py`)

Synthetic generators produce `A_T[t]` arrays for `t = 0..T`:

- **Calm**: `A_T = 0.1 + noise(σ=0.02)`, bounded to `[0, 1)`
- **Gradual**: `A_T = 0.05 + 0.6 * sigmoid((t - t_mid) / τ)` — S-curve ramp from ~0.05 to ~0.65
- **Shock**: `A_T = 0.1` constant, then jumps to `0.8` at `t_shock`, exponential decay back

Price mapping: `p(t) = A_T(t) / (1 - A_T(t))` — the odds ratio from the spec.

### Funding Rate (`funding.py`)

From `funding-rate.tex`:

| Formula | Code |
|---------|------|
| `p_index = A_T / (1 - A_T)` | `index_price(A_T)` |
| `p_mark = (1 - x) / x` | `mark_price(x)` |
| `basis = p_mark - p_index` | inline |
| `r = α * \|basis\| / (p_index + 1)` | `funding_rate(basis, p_index, alpha)` |
| `φ(t) = φ_base + sign(basis) * min(r, φ_max - φ_base)` | `dynamic_fee(...)` |
| `F = r * basis` | `funding_payment(...)` |

## Agent Models (`agents.py`)

### PLP (Passive LP)

```python
@dataclass
class PLPState:
    liquidity: float         # L deposited in underlying pool
    fee_income: float        # cumulative fees earned from swaps
    premium_paid: float      # cumulative premium paid to insurance CFMM
    protection_value: float  # current hedge value: V_LP(p_index) * L_insurance
    net_pnl: float           # fee_income - premium_paid + protection_value
```

Each block:
1. PLP earns base fees: `Δfee = L * φ_base * volume_per_block`
2. PLP pays premium: fraction `π` of fee income routed to insurance
3. Protection value: `V_LP(p_index) * L_insurance = ln(1 + A_T/(1-A_T)) * L_ins`

### Unhedged PLP

Same but `premium_paid = 0`, `protection_value = 0`. Fee income reduced by JIT competition: `fee_income_unhedged = fee_income * (1 - A_T)` — JIT captures the concentrated portion.

### Underwriter

```python
@dataclass
class UnderwriterState:
    collateral: float            # capital deposited
    premium_earned: float        # cumulative premium received
    protection_liability: float  # current obligation
    net_pnl: float               # premium_earned - protection_liability
```

## Metrics (`metrics.py`)

- **Hedge effectiveness**: `(PLP_hedged_pnl - PLP_unhedged_pnl) / |PLP_unhedged_pnl|`
- **Ecosystem welfare**: `PLP_net_pnl + Underwriter_net_pnl` (should be positive)
- **TVL impact**: `L_total(t)` tracking
- **Break-even A_T**: concentration level where hedge cost = protection benefit

## Scenarios (`scenarios.py` + `config.py`)

### Narrative Arc: Calm → Gradual → Shock

Three consecutive phases over `T = 3000` blocks:

1. **Calm** (blocks 0–999): `A_T ≈ 0.1`, low noise. Hedge costs little, PLP and unhedged PLP earn similarly.
2. **Gradual** (blocks 1000–1999): `A_T` ramps from 0.1 to 0.65 via sigmoid. Hedge starts paying off, unhedged PLP fee income drops.
3. **Shock** (blocks 2000–2999): `A_T` spikes to 0.8 at block 2100, decays to 0.5. Insurance pays out dramatically.

### Default Parameters (`config.py`)

```python
@dataclass(frozen=True)
class SimConfig:
    T: int = 3000                 # total blocks
    L_0: float = 100.0            # initial liquidity
    A_0: float = 0.0              # initial fee concentration (genesis)
    alpha: float = 0.1            # funding rate sensitivity
    fee_base: float = 0.003       # 30 bps base fee
    fee_max: float = 0.01         # 100 bps max fee
    premium_fraction: float = 0.1 # 10% of PLP fees → insurance premium
    volume_per_block: float = 10.0  # synthetic swap volume per block
    L_insurance: float = 50.0     # liquidity in insurance CFMM
    underwriter_collateral: float = 100.0
```

## Plots (`plotting.py`)

### Plot 1: P&L Over Time (The Money Plot)
- **X**: Block number, **Y**: Cumulative P&L
- **Lines**: PLP hedged (green), PLP unhedged (red)
- **Background shading**: Calm (light blue), Gradual (yellow), Shock (pink)
- **Annotation**: Arrow at hedge-payoff inflection point
- **Subplot below**: A_T(t) trajectory as context

### Plot 2: A_T Trajectory + CFMM Price Response
- **Top panel**: `A_T(t)` raw fee concentration index
- **Bottom panel**: `p_index(t)` and `p_mark(t)` overlaid
- **Shaded area** between mark and index = basis

### Plot 3: Reserve Composition Over Time
- **Stacked area**: Risky reserve `x(t)` and numeraire reserve `y(t)`
- Shows shift from "all risky" at genesis to "more numeraire" as A_T rises
- **Annotation**: Total value `p*x + y` tracks `V_LP(p)`

### Plot 4: Funding Rate + Premium Cost
- **Top panel**: Funding rate `r(t)` and dynamic fee `φ(t)`
- **Bottom panel**: Cumulative premium paid (PLP) vs cumulative premium earned (underwriter)

### Plot 5 (Bonus): Ecosystem Welfare Summary
- **Bar chart**: Per-scenario bars for PLP hedged, PLP unhedged, Underwriter, Total welfare
- Visual proof the hedge is positive-sum

## Notebook Narrative (`demo.ipynb`)

1. **Introduction**: "What if you could hedge against JIT competition?"
2. **Setup**: Import simulation, configure parameters, explain the model
3. **Scenario 1 — Calm**: Low concentration, hedge costs pennies, both PLPs do well
4. **Scenario 2 — Gradual**: JIT bot ramps up, unhedged PLP bleeds, hedged PLP protected
5. **Scenario 3 — Shock**: Sudden MEV event, insurance pays out, unhedged PLP devastated
6. **Full Arc**: Combined plot across all three phases
7. **Welfare Analysis**: Hedged vs unhedged comparison, then ecosystem-level positive-sum argument
8. **Parameter Sensitivity**: Quick sweep of `alpha`, `premium_fraction` to show robustness

## Verification

- `invariant(x, y) ≈ 0` at every step (CFMM-15)
- `0 ≤ A_T < 1` at every step (CFMM-31)
- `p*x + y ≈ L * V_LP(p)` at every step (replication accuracy CFMM-20)
- Premium conservation: `PLP_premium_paid ≈ Underwriter_premium_earned` (INS-001)
- Mark-index convergence: basis shrinks over time (CFMM-26)
