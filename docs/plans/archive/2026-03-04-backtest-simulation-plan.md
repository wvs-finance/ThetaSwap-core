# Backtest Simulation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python simulation package + Jupyter demo notebook that backtests ThetaSwap's fee concentration hedge across three scenarios (calm, gradual JIT growth, shock) and produces 5 publication-quality plots showing hedged vs unhedged PLP P&L, CFMM mechanics, and ecosystem welfare.

**Architecture:** Python package `simulation/` with 8 modules (config, cfmm, index, funding, agents, metrics, scenarios, plotting) consumed by `notebooks/demo.ipynb`. All math from `specs/model/` LaTeX spec. Pure functions on numpy arrays and frozen dataclasses. No global state.

**Tech Stack:** Python 3.11+, numpy, scipy, matplotlib, jupyter. Managed via `pyproject.toml` with `pip install -e .` for local dev.

**Design doc:** `docs/plans/2026-03-04-backtest-simulation-design.md`

---

### Task 1: Project Scaffold + pyproject.toml

**Files:**
- Create: `pyproject.toml`
- Create: `simulation/__init__.py`
- Create: `simulation/config.py`
- Create: `tests/simulation/__init__.py`
- Create: `tests/simulation/test_config.py`
- Create: `notebooks/.gitkeep`

**Step 1: Write the failing test**

Create `tests/simulation/test_config.py`:

```python
"""Tests for simulation config."""
from simulation.config import SimConfig


def test_default_config_creates():
    cfg = SimConfig()
    assert cfg.T == 3000
    assert cfg.L_0 == 100.0
    assert cfg.A_0 == 0.0


def test_config_is_frozen():
    cfg = SimConfig()
    try:
        cfg.T = 999
        assert False, "Should be frozen"
    except AttributeError:
        pass


def test_config_custom_values():
    cfg = SimConfig(T=500, alpha=0.2)
    assert cfg.T == 500
    assert cfg.alpha == 0.2
    assert cfg.fee_base == 0.003  # default preserved
```

**Step 2: Create pyproject.toml**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "thetaswap-simulation"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "numpy>=1.24",
    "scipy>=1.11",
    "matplotlib>=3.7",
    "jupyter>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 3: Create simulation/__init__.py**

```python
"""ThetaSwap fee concentration hedge backtest simulation."""
```

**Step 4: Create simulation/config.py**

```python
"""Simulation configuration — frozen dataclass with all parameters."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SimConfig:
    """All simulation parameters. Immutable after creation."""

    # Time
    T: int = 3000                          # total blocks

    # CFMM initialization
    L_0: float = 100.0                     # initial liquidity
    A_0: float = 0.0                       # initial fee concentration (genesis)

    # Funding rate
    alpha: float = 0.1                     # funding rate sensitivity

    # Fee structure
    fee_base: float = 0.003                # 30 bps base fee
    fee_max: float = 0.01                  # 100 bps max fee

    # Insurance
    premium_fraction: float = 0.1          # 10% of PLP fees -> insurance premium
    L_insurance: float = 50.0              # liquidity in insurance CFMM
    underwriter_collateral: float = 100.0  # underwriter capital

    # Synthetic market
    volume_per_block: float = 10.0         # swap volume per block
```

**Step 5: Create test init and notebooks dir**

```bash
mkdir -p tests/simulation notebooks
touch tests/simulation/__init__.py notebooks/.gitkeep
```

**Step 6: Install and run tests**

Run: `pip install -e ".[dev]" && pytest tests/simulation/test_config.py -v`
Expected: 3 PASS

**Step 7: Commit**

```bash
git add pyproject.toml simulation/ tests/simulation/ notebooks/
git commit -m "feat(sim): scaffold simulation package + config"
```

---

### Task 2: CFMM Module — Core Math

**Files:**
- Create: `simulation/cfmm.py`
- Create: `tests/simulation/test_cfmm.py`

**References:**
- `specs/model/payoff.tex` — eq 5: `V_LP(p) = ln(1+p)`
- `specs/model/reserves.tex` — eq 6: `x(p) = 1/(1+p)`, eq 8: `y(p) = ln(1+p) - p/(1+p)`
- `specs/model/trading-function.tex` — eq 13: `ψ(x,y) = y + ln(x) + 1 - x = 0`, eq 17: `p = (1-x)/x`
- `specs/model/initialization.tex` — `x_0 = L_0*(1-A_0)`, `y_0 = L_0*(-ln(1-A_0) - A_0)`

**Step 1: Write the failing tests**

Create `tests/simulation/test_cfmm.py`:

```python
"""Tests for CFMM core math — verified against specs/model/ LaTeX spec."""
import math
import numpy as np
from simulation.cfmm import (
    payoff,
    invariant,
    risky_reserve,
    numeraire_reserve,
    spot_price,
    init_state,
    CFMMState,
)


# --- payoff.tex eq 5 ---
def test_payoff_at_zero():
    assert payoff(0.0) == 0.0


def test_payoff_at_one():
    assert math.isclose(payoff(1.0), math.log(2), rel_tol=1e-12)


def test_payoff_monotone():
    prices = np.linspace(0, 10, 100)
    vals = payoff(prices)
    assert np.all(np.diff(vals) > 0)


# --- trading-function.tex eq 13 ---
def test_invariant_on_curve():
    """Points on the reserve curve satisfy ψ = 0."""
    for p in [0.0, 0.5, 1.0, 2.0, 5.0]:
        x = risky_reserve(p)
        y = numeraire_reserve(p)
        assert math.isclose(invariant(x, y), 0.0, abs_tol=1e-12)


# --- reserves.tex eq 6 ---
def test_risky_reserve_at_zero():
    assert risky_reserve(0.0) == 1.0


def test_risky_reserve_decreasing():
    prices = np.linspace(0, 10, 100)
    x = risky_reserve(prices)
    assert np.all(np.diff(x) < 0)


# --- reserves.tex eq 8 ---
def test_numeraire_reserve_at_zero():
    assert numeraire_reserve(0.0) == 0.0


def test_numeraire_reserve_increasing():
    prices = np.linspace(0.01, 10, 100)
    y = numeraire_reserve(prices)
    assert np.all(np.diff(y) > 0)


# --- trading-function.tex eq 17 ---
def test_spot_price_roundtrip():
    """x(p) -> spot_price -> p, roundtrip."""
    for p in [0.1, 0.5, 1.0, 2.0, 5.0]:
        x = risky_reserve(p)
        p_recovered = spot_price(x)
        assert math.isclose(p_recovered, p, rel_tol=1e-12)


# --- initialization.tex ---
def test_init_state_genesis():
    """A_0 = 0: p=0, x=L, y=0."""
    s = init_state(A_0=0.0, L_0=100.0)
    assert s.p == 0.0
    assert s.x == 100.0
    assert math.isclose(s.y, 0.0, abs_tol=1e-12)
    assert s.L == 100.0


def test_init_state_half():
    """A_0 = 0.5, L_0 = 100: numerical verification from spec."""
    s = init_state(A_0=0.5, L_0=100.0)
    assert math.isclose(s.p, 1.0, rel_tol=1e-12)
    assert math.isclose(s.x, 50.0, rel_tol=1e-12)
    assert math.isclose(s.y, 19.31, rel_tol=1e-2)


def test_init_state_invariant():
    """Initial state satisfies ψ = 0."""
    s = init_state(A_0=0.3, L_0=100.0)
    psi = invariant(s.x / s.L, s.y / s.L)
    assert math.isclose(psi, 0.0, abs_tol=1e-10)


# --- Legendre-Fenchel: p*x + y = V_LP(p) ---
def test_legendre_fenchel():
    """Table from reserves.tex numerical verification."""
    for p, expected_v in [(0, 0), (0.5, 0.4055), (1.0, 0.6931), (2.0, 1.0986)]:
        x = risky_reserve(p)
        y = numeraire_reserve(p)
        lp_value = p * x + y
        assert math.isclose(lp_value, payoff(p), rel_tol=1e-3)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/simulation/test_cfmm.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'simulation.cfmm'`

**Step 3: Write minimal implementation**

Create `simulation/cfmm.py`:

```python
"""CFMM core math — implements specs/model/ LaTeX equations.

All functions accept and return floats or numpy arrays.
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CFMMState:
    """Snapshot of CFMM state at one point in time."""

    x: float  # risky reserve (feeConcentrationToken)
    y: float  # numeraire reserve
    L: float  # liquidity
    p: float  # spot price


def payoff(p: float | np.ndarray) -> float | np.ndarray:
    """V_LP(p) = ln(1 + p).  (payoff.tex eq 5)"""
    return np.log1p(p)


def invariant(x: float | np.ndarray, y: float | np.ndarray) -> float | np.ndarray:
    """ψ(x, y) = y + ln(x) + 1 - x.  (trading-function.tex eq 13)

    Returns 0 when (x, y) is on the curve.
    """
    return y + np.log(x) + 1.0 - x


def risky_reserve(p: float | np.ndarray) -> float | np.ndarray:
    """x(p) = 1 / (1 + p).  (reserves.tex eq 6)"""
    return 1.0 / (1.0 + p)


def numeraire_reserve(p: float | np.ndarray) -> float | np.ndarray:
    """y(p) = ln(1 + p) - p / (1 + p).  (reserves.tex eq 8)"""
    return np.log1p(p) - p / (1.0 + p)


def spot_price(x: float | np.ndarray) -> float | np.ndarray:
    """p = (1 - x) / x.  (trading-function.tex eq 17)"""
    return (1.0 - x) / x


def init_state(A_0: float, L_0: float) -> CFMMState:
    """Derive initial CFMM state from A_0 and L_0.  (initialization.tex)

    p_0 = A_0 / (1 - A_0)
    x_0 = L_0 * (1 - A_0)
    y_0 = L_0 * (-ln(1 - A_0) - A_0)
    """
    if A_0 == 0.0:
        return CFMMState(x=L_0, y=0.0, L=L_0, p=0.0)
    p_0 = A_0 / (1.0 - A_0)
    x_0 = L_0 * (1.0 - A_0)
    y_0 = L_0 * (-np.log(1.0 - A_0) - A_0)
    return CFMMState(x=x_0, y=y_0, L=L_0, p=p_0)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/simulation/test_cfmm.py -v`
Expected: 13 PASS

**Step 5: Commit**

```bash
git add simulation/cfmm.py tests/simulation/test_cfmm.py
git commit -m "feat(sim): CFMM core math — payoff, reserves, trading function, init"
```

---

### Task 3: Index Module — Synthetic A_T Generators

**Files:**
- Create: `simulation/index.py`
- Create: `tests/simulation/test_index.py`

**Step 1: Write the failing tests**

Create `tests/simulation/test_index.py`:

```python
"""Tests for synthetic A_T trajectory generators."""
import numpy as np
from simulation.index import (
    generate_calm,
    generate_gradual,
    generate_shock,
    generate_narrative_arc,
    index_price,
)


def test_index_price_zero():
    assert index_price(0.0) == 0.0


def test_index_price_half():
    assert index_price(0.5) == 1.0


def test_index_price_array():
    a = np.array([0.0, 0.25, 0.5, 0.75])
    p = index_price(a)
    expected = np.array([0.0, 1 / 3, 1.0, 3.0])
    np.testing.assert_allclose(p, expected, rtol=1e-12)


def test_calm_shape_and_bounds():
    a = generate_calm(T=1000, base=0.1, sigma=0.02, seed=42)
    assert a.shape == (1000,)
    assert np.all(a >= 0.0)
    assert np.all(a < 1.0)
    assert np.isclose(np.mean(a), 0.1, atol=0.05)


def test_gradual_ramps_up():
    a = generate_gradual(T=1000, a_start=0.05, a_end=0.65, tau=100.0)
    assert a.shape == (1000,)
    assert a[0] < 0.15
    assert a[-1] > 0.55
    assert np.all(a >= 0.0)
    assert np.all(a < 1.0)


def test_shock_spikes_and_decays():
    a = generate_shock(T=1000, base=0.1, spike=0.8, t_shock=100, decay=0.01)
    assert a.shape == (1000,)
    assert a[99] < 0.2  # before shock
    assert a[100] > 0.7  # at shock
    assert a[-1] < a[100]  # decayed
    assert np.all(a >= 0.0)
    assert np.all(a < 1.0)


def test_narrative_arc_concatenates():
    a = generate_narrative_arc(T_per_phase=500)
    assert a.shape == (1500,)
    assert np.all(a >= 0.0)
    assert np.all(a < 1.0)
    # Calm phase low, end of shock phase higher than calm
    assert np.mean(a[:100]) < np.mean(a[1100:1200])
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/simulation/test_index.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `simulation/index.py`:

```python
"""Synthetic fee concentration index (A_T) trajectory generators.

All generators return numpy arrays of shape (T,) with values in [0, 1).
"""
import numpy as np


def index_price(a_t: float | np.ndarray) -> float | np.ndarray:
    """p = A_T / (1 - A_T).  Odds-ratio mapping (payoff.tex)."""
    return a_t / (1.0 - a_t)


def generate_calm(
    T: int = 1000,
    base: float = 0.1,
    sigma: float = 0.02,
    seed: int = 42,
) -> np.ndarray:
    """Low, stable concentration with small noise."""
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, sigma, T)
    a = base + noise
    return np.clip(a, 0.001, 0.999)


def generate_gradual(
    T: int = 1000,
    a_start: float = 0.05,
    a_end: float = 0.65,
    tau: float = 100.0,
) -> np.ndarray:
    """S-curve ramp from a_start to a_end via sigmoid."""
    t = np.arange(T, dtype=float)
    t_mid = T / 2.0
    sigmoid = 1.0 / (1.0 + np.exp(-(t - t_mid) / tau))
    a = a_start + (a_end - a_start) * sigmoid
    return np.clip(a, 0.001, 0.999)


def generate_shock(
    T: int = 1000,
    base: float = 0.1,
    spike: float = 0.8,
    t_shock: int = 100,
    decay: float = 0.01,
) -> np.ndarray:
    """Constant base, then spike at t_shock with exponential decay back."""
    a = np.full(T, base, dtype=float)
    for t in range(t_shock, T):
        a[t] = base + (spike - base) * np.exp(-decay * (t - t_shock))
    return np.clip(a, 0.001, 0.999)


def generate_narrative_arc(
    T_per_phase: int = 1000,
    seed: int = 42,
) -> np.ndarray:
    """Calm -> Gradual -> Shock concatenated into one trajectory."""
    calm = generate_calm(T=T_per_phase, base=0.1, sigma=0.02, seed=seed)
    gradual = generate_gradual(
        T=T_per_phase, a_start=calm[-1], a_end=0.65, tau=T_per_phase / 10,
    )
    shock = generate_shock(
        T=T_per_phase, base=0.5, spike=0.8,
        t_shock=T_per_phase // 10, decay=0.005,
    )
    return np.concatenate([calm, gradual, shock])
```

**Step 4: Run tests**

Run: `pytest tests/simulation/test_index.py -v`
Expected: 7 PASS

**Step 5: Commit**

```bash
git add simulation/index.py tests/simulation/test_index.py
git commit -m "feat(sim): synthetic A_T generators — calm, gradual, shock, narrative arc"
```

---

### Task 4: Funding Module

**Files:**
- Create: `simulation/funding.py`
- Create: `tests/simulation/test_funding.py`

**References:** `specs/model/funding-rate.tex`

**Step 1: Write the failing tests**

Create `tests/simulation/test_funding.py`:

```python
"""Tests for funding rate mechanics — from funding-rate.tex."""
import math
import numpy as np
from simulation.funding import (
    mark_price,
    funding_rate,
    dynamic_fee,
    funding_payment,
)


def test_mark_price_at_half():
    """x = 0.5 -> p = 1.0"""
    assert mark_price(0.5) == 1.0


def test_mark_price_at_one():
    """x = 1.0 -> p = 0.0"""
    assert mark_price(1.0) == 0.0


def test_funding_rate_zero_basis():
    """No basis -> no funding rate."""
    r = funding_rate(basis=0.0, p_index=1.0, alpha=0.1)
    assert r == 0.0


def test_funding_rate_positive_basis():
    """r = α * |basis| / (p_index + 1)."""
    r = funding_rate(basis=0.5, p_index=1.0, alpha=0.1)
    expected = 0.1 * 0.5 / 2.0  # 0.025
    assert math.isclose(r, expected, rel_tol=1e-12)


def test_dynamic_fee_mark_above_index():
    """Mark > index: fee increases."""
    fee = dynamic_fee(
        basis=0.5, p_index=1.0, alpha=0.1,
        fee_base=0.003, fee_max=0.01,
    )
    assert fee > 0.003


def test_dynamic_fee_mark_below_index():
    """Mark < index: fee decreases."""
    fee = dynamic_fee(
        basis=-0.5, p_index=1.0, alpha=0.1,
        fee_base=0.003, fee_max=0.01,
    )
    assert fee < 0.003


def test_dynamic_fee_capped():
    """Fee never exceeds fee_max."""
    fee = dynamic_fee(
        basis=100.0, p_index=0.01, alpha=10.0,
        fee_base=0.003, fee_max=0.01,
    )
    assert fee <= 0.01


def test_dynamic_fee_floor():
    """Fee never goes negative."""
    fee = dynamic_fee(
        basis=-100.0, p_index=0.01, alpha=10.0,
        fee_base=0.003, fee_max=0.01,
    )
    assert fee >= 0.0


def test_funding_payment_sign():
    """Positive basis -> positive payment (longs pay shorts)."""
    f = funding_payment(basis=0.5, p_index=1.0, alpha=0.1)
    assert f > 0.0
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/simulation/test_funding.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `simulation/funding.py`:

```python
"""Funding rate, premium, and dynamic fee logic.

Implements specs/model/funding-rate.tex equations.
"""
import numpy as np


def mark_price(x: float | np.ndarray) -> float | np.ndarray:
    """p_mark = (1 - x) / x.  (funding-rate.tex eq mark-price)"""
    return (1.0 - x) / x


def funding_rate(
    basis: float | np.ndarray,
    p_index: float | np.ndarray,
    alpha: float,
) -> float | np.ndarray:
    """r = α * |basis| / (p_index + 1).  (funding-rate.tex eq funding-rate-evolution)"""
    return alpha * np.abs(basis) / (p_index + 1.0)


def dynamic_fee(
    basis: float | np.ndarray,
    p_index: float | np.ndarray,
    alpha: float,
    fee_base: float,
    fee_max: float,
) -> float | np.ndarray:
    """φ(t) = φ_base + sign(basis) * min(r, φ_max - φ_base).

    Clamped to [0, fee_max].  (funding-rate.tex eq dynamic-fee)
    """
    r = funding_rate(basis, p_index, alpha)
    fee_fund = np.sign(basis) * np.minimum(r, fee_max - fee_base)
    raw = fee_base + fee_fund
    return np.clip(raw, 0.0, fee_max)


def funding_payment(
    basis: float | np.ndarray,
    p_index: float | np.ndarray,
    alpha: float,
) -> float | np.ndarray:
    """F = r * basis.  (funding-rate.tex eq funding-payment)"""
    r = funding_rate(basis, p_index, alpha)
    return r * basis
```

**Step 4: Run tests**

Run: `pytest tests/simulation/test_funding.py -v`
Expected: 9 PASS

**Step 5: Commit**

```bash
git add simulation/funding.py tests/simulation/test_funding.py
git commit -m "feat(sim): funding rate, dynamic fee, and funding payment"
```

---

### Task 5: Agents Module — PLP + Underwriter

**Files:**
- Create: `simulation/agents.py`
- Create: `tests/simulation/test_agents.py`

**Step 1: Write the failing tests**

Create `tests/simulation/test_agents.py`:

```python
"""Tests for PLP and Underwriter agent state evolution."""
import math
import numpy as np
from simulation.agents import (
    PLPState,
    UnderwriterState,
    step_hedged_plp,
    step_unhedged_plp,
    step_underwriter,
)
from simulation.config import SimConfig


def test_plp_initial_state():
    s = PLPState()
    assert s.fee_income == 0.0
    assert s.premium_paid == 0.0
    assert s.protection_value == 0.0
    assert s.net_pnl == 0.0


def test_hedged_plp_earns_fees_and_pays_premium():
    cfg = SimConfig(volume_per_block=10.0, fee_base=0.003, premium_fraction=0.1)
    s = PLPState(liquidity=100.0)
    s_new = step_hedged_plp(s, A_T=0.1, cfg=cfg)
    # Fee earned: L * fee_base * volume = 100 * 0.003 * 10 = 3.0
    assert math.isclose(s_new.fee_income, 3.0, rel_tol=1e-6)
    # Premium: 10% of 3.0 = 0.3
    assert math.isclose(s_new.premium_paid, 0.3, rel_tol=1e-6)


def test_unhedged_plp_reduced_by_concentration():
    cfg = SimConfig(volume_per_block=10.0, fee_base=0.003)
    s = PLPState(liquidity=100.0)
    s_new = step_unhedged_plp(s, A_T=0.5, cfg=cfg)
    # Fee reduced by (1 - A_T) = 0.5: 3.0 * 0.5 = 1.5
    assert math.isclose(s_new.fee_income, 1.5, rel_tol=1e-6)
    assert s_new.premium_paid == 0.0


def test_underwriter_earns_premium():
    s = UnderwriterState(collateral=100.0)
    s_new = step_underwriter(s, premium_inflow=0.3, protection_liability=0.1)
    assert math.isclose(s_new.premium_earned, 0.3, rel_tol=1e-6)
    assert math.isclose(s_new.protection_liability, 0.1, rel_tol=1e-6)
    assert math.isclose(s_new.net_pnl, 0.2, rel_tol=1e-6)


def test_hedged_plp_protection_value_increases_with_concentration():
    cfg = SimConfig(L_insurance=50.0)
    s_low = step_hedged_plp(PLPState(liquidity=100.0), A_T=0.1, cfg=cfg)
    s_high = step_hedged_plp(PLPState(liquidity=100.0), A_T=0.5, cfg=cfg)
    assert s_high.protection_value > s_low.protection_value
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/simulation/test_agents.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `simulation/agents.py`:

```python
"""PLP and Underwriter agent state models.

Each step function takes the previous state + current block's parameters,
returns a new frozen state. Pure functions, no mutation.
"""
from dataclasses import dataclass, replace

import numpy as np

from simulation.cfmm import payoff
from simulation.config import SimConfig
from simulation.index import index_price


@dataclass(frozen=True)
class PLPState:
    """Passive LP state — tracks cumulative P&L components."""

    liquidity: float = 100.0
    fee_income: float = 0.0
    premium_paid: float = 0.0
    protection_value: float = 0.0
    net_pnl: float = 0.0


@dataclass(frozen=True)
class UnderwriterState:
    """Underwriter state — tracks premium vs liability."""

    collateral: float = 100.0
    premium_earned: float = 0.0
    protection_liability: float = 0.0
    net_pnl: float = 0.0


def step_hedged_plp(state: PLPState, A_T: float, cfg: SimConfig) -> PLPState:
    """Advance hedged PLP by one block."""
    # Fee earned this block (before JIT competition reduces it)
    gross_fee = state.liquidity * cfg.fee_base * cfg.volume_per_block
    # Premium paid: fraction of gross fees
    premium = cfg.premium_fraction * gross_fee
    # Protection value: V_LP(p_index) * L_insurance
    p = index_price(A_T)
    prot = float(payoff(p)) * cfg.L_insurance

    new_fee = state.fee_income + gross_fee
    new_prem = state.premium_paid + premium
    new_pnl = new_fee - new_prem + prot

    return replace(
        state,
        fee_income=new_fee,
        premium_paid=new_prem,
        protection_value=prot,
        net_pnl=new_pnl,
    )


def step_unhedged_plp(state: PLPState, A_T: float, cfg: SimConfig) -> PLPState:
    """Advance unhedged PLP by one block.

    Fee income reduced by (1 - A_T): JIT captures the concentrated portion.
    """
    gross_fee = state.liquidity * cfg.fee_base * cfg.volume_per_block
    effective_fee = gross_fee * (1.0 - A_T)

    new_fee = state.fee_income + effective_fee
    return replace(state, fee_income=new_fee, net_pnl=new_fee)


def step_underwriter(
    state: UnderwriterState,
    premium_inflow: float,
    protection_liability: float,
) -> UnderwriterState:
    """Advance underwriter by one block."""
    new_prem = state.premium_earned + premium_inflow
    new_pnl = new_prem - protection_liability

    return replace(
        state,
        premium_earned=new_prem,
        protection_liability=protection_liability,
        net_pnl=new_pnl,
    )
```

**Step 4: Run tests**

Run: `pytest tests/simulation/test_agents.py -v`
Expected: 5 PASS

**Step 5: Commit**

```bash
git add simulation/agents.py tests/simulation/test_agents.py
git commit -m "feat(sim): PLP and Underwriter agent models with step functions"
```

---

### Task 6: Scenarios + Metrics + Full Simulation Loop

**Files:**
- Create: `simulation/scenarios.py`
- Create: `simulation/metrics.py`
- Create: `tests/simulation/test_scenarios.py`

**Step 1: Write the failing tests**

Create `tests/simulation/test_scenarios.py`:

```python
"""Tests for simulation loop and metrics."""
import numpy as np
from simulation.scenarios import run_simulation, SimResult
from simulation.metrics import hedge_effectiveness, ecosystem_welfare
from simulation.config import SimConfig


def test_run_simulation_shape():
    cfg = SimConfig(T=100, volume_per_block=10.0)
    result = run_simulation(cfg, seed=42)
    assert isinstance(result, SimResult)
    assert result.A_T.shape == (100,)
    assert result.hedged_pnl.shape == (100,)
    assert result.unhedged_pnl.shape == (100,)
    assert result.underwriter_pnl.shape == (100,)


def test_hedged_beats_unhedged_under_shock():
    """Under concentration shock, hedged PLP should outperform."""
    cfg = SimConfig(T=500, volume_per_block=10.0)
    result = run_simulation(cfg, seed=42, scenario="shock")
    # At end: hedged should be better than unhedged
    assert result.hedged_pnl[-1] > result.unhedged_pnl[-1]


def test_invariant_holds():
    """CFMM invariant ψ ≈ 0 at every step."""
    cfg = SimConfig(T=100)
    result = run_simulation(cfg, seed=42)
    assert np.all(np.abs(result.invariant_check) < 1e-8)


def test_a_t_bounded():
    """A_T in [0, 1) at every step (CFMM-31)."""
    cfg = SimConfig(T=100)
    result = run_simulation(cfg, seed=42)
    assert np.all(result.A_T >= 0.0)
    assert np.all(result.A_T < 1.0)


def test_hedge_effectiveness_positive_under_shock():
    cfg = SimConfig(T=500)
    result = run_simulation(cfg, seed=42, scenario="shock")
    eff = hedge_effectiveness(result.hedged_pnl[-1], result.unhedged_pnl[-1])
    assert eff > 0.0


def test_ecosystem_welfare_positive():
    cfg = SimConfig(T=500)
    result = run_simulation(cfg, seed=42, scenario="gradual")
    welfare = ecosystem_welfare(result.hedged_pnl[-1], result.underwriter_pnl[-1])
    assert welfare > 0.0
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/simulation/test_scenarios.py -v`
Expected: FAIL

**Step 3: Write metrics.py**

Create `simulation/metrics.py`:

```python
"""Welfare and performance metrics."""


def hedge_effectiveness(hedged_pnl: float, unhedged_pnl: float) -> float:
    """(hedged - unhedged) / |unhedged|. Positive means hedge helps."""
    if unhedged_pnl == 0.0:
        return 0.0
    return (hedged_pnl - unhedged_pnl) / abs(unhedged_pnl)


def ecosystem_welfare(plp_pnl: float, underwriter_pnl: float) -> float:
    """Total ecosystem welfare. Positive means positive-sum."""
    return plp_pnl + underwriter_pnl
```

**Step 4: Write scenarios.py — the simulation loop**

Create `simulation/scenarios.py`:

```python
"""Simulation loop — runs the full backtest and returns time series."""
from dataclasses import dataclass

import numpy as np

from simulation.agents import (
    PLPState,
    UnderwriterState,
    step_hedged_plp,
    step_unhedged_plp,
    step_underwriter,
)
from simulation.cfmm import (
    init_state,
    invariant,
    payoff,
    risky_reserve,
    numeraire_reserve,
)
from simulation.config import SimConfig
from simulation.funding import dynamic_fee, funding_payment, mark_price
from simulation.index import (
    generate_calm,
    generate_gradual,
    generate_narrative_arc,
    generate_shock,
    index_price,
)


@dataclass
class SimResult:
    """All time series from a simulation run."""

    A_T: np.ndarray            # (T,) fee concentration index
    p_index: np.ndarray        # (T,) index price
    p_mark: np.ndarray         # (T,) mark price
    x: np.ndarray              # (T,) risky reserve
    y: np.ndarray              # (T,) numeraire reserve
    hedged_pnl: np.ndarray     # (T,) cumulative hedged PLP P&L
    unhedged_pnl: np.ndarray   # (T,) cumulative unhedged PLP P&L
    underwriter_pnl: np.ndarray  # (T,) cumulative underwriter P&L
    funding_rates: np.ndarray  # (T,) funding rate
    fees: np.ndarray           # (T,) dynamic fee
    cum_premium_paid: np.ndarray   # (T,) cumulative premium paid by PLP
    cum_premium_earned: np.ndarray # (T,) cumulative premium earned by underwriter
    invariant_check: np.ndarray    # (T,) ψ(x/L, y/L) — should be ~0


def _generate_a_t(scenario: str, T: int, seed: int) -> np.ndarray:
    if scenario == "calm":
        return generate_calm(T=T, seed=seed)
    elif scenario == "gradual":
        return generate_gradual(T=T)
    elif scenario == "shock":
        return generate_shock(T=T)
    elif scenario == "narrative":
        return generate_narrative_arc(T_per_phase=T // 3, seed=seed)[:T]
    else:
        return generate_narrative_arc(T_per_phase=T // 3, seed=seed)[:T]


def run_simulation(
    cfg: SimConfig,
    seed: int = 42,
    scenario: str = "narrative",
) -> SimResult:
    """Run the full simulation loop.

    Returns all time series needed for plotting.
    """
    T = cfg.T
    A_T = _generate_a_t(scenario, T, seed)

    # Output arrays
    p_idx = np.zeros(T)
    p_mrk = np.zeros(T)
    xs = np.zeros(T)
    ys = np.zeros(T)
    hedged = np.zeros(T)
    unhedged = np.zeros(T)
    uw_pnl = np.zeros(T)
    fund_rates = np.zeros(T)
    fees = np.zeros(T)
    cum_prem_paid = np.zeros(T)
    cum_prem_earned = np.zeros(T)
    inv_check = np.zeros(T)

    # Initialize CFMM and agents
    cfmm = init_state(cfg.A_0, cfg.L_0)
    plp_h = PLPState(liquidity=cfg.L_0)
    plp_u = PLPState(liquidity=cfg.L_0)
    uw = UnderwriterState(collateral=cfg.underwriter_collateral)

    for t in range(T):
        a = A_T[t]

        # Update CFMM reserves to match current A_T via oracle
        p = float(index_price(a))
        x = cfg.L_0 * float(risky_reserve(p))
        y = cfg.L_0 * float(numeraire_reserve(p))

        # Mark price from reserves
        p_m = float(mark_price(x / cfg.L_0))

        # Funding
        basis = p_m - p
        r = float(np.abs(basis)) * cfg.alpha / (p + 1.0) if p + 1.0 > 0 else 0.0
        fee = float(dynamic_fee(basis, p, cfg.alpha, cfg.fee_base, cfg.fee_max))
        fp = float(funding_payment(basis, p, cfg.alpha))

        # Step agents
        plp_h = step_hedged_plp(plp_h, a, cfg)
        plp_u = step_unhedged_plp(plp_u, a, cfg)

        premium = cfg.premium_fraction * cfg.L_0 * cfg.fee_base * cfg.volume_per_block
        prot_liability = float(payoff(p)) * cfg.L_insurance
        uw = step_underwriter(uw, premium, prot_liability)

        # Record
        p_idx[t] = p
        p_mrk[t] = p_m
        xs[t] = x
        ys[t] = y
        hedged[t] = plp_h.net_pnl
        unhedged[t] = plp_u.net_pnl
        uw_pnl[t] = uw.net_pnl
        fund_rates[t] = r
        fees[t] = fee
        cum_prem_paid[t] = plp_h.premium_paid
        cum_prem_earned[t] = uw.premium_earned
        inv_check[t] = float(invariant(x / cfg.L_0, y / cfg.L_0))

    return SimResult(
        A_T=A_T,
        p_index=p_idx,
        p_mark=p_mrk,
        x=xs,
        y=ys,
        hedged_pnl=hedged,
        unhedged_pnl=unhedged,
        underwriter_pnl=uw_pnl,
        funding_rates=fund_rates,
        fees=fees,
        cum_premium_paid=cum_prem_paid,
        cum_premium_earned=cum_prem_earned,
        invariant_check=inv_check,
    )
```

**Step 5: Run tests**

Run: `pytest tests/simulation/test_scenarios.py -v`
Expected: 6 PASS

**Step 6: Run all tests**

Run: `pytest tests/simulation/ -v`
Expected: All PASS (config + cfmm + index + funding + agents + scenarios)

**Step 7: Commit**

```bash
git add simulation/scenarios.py simulation/metrics.py tests/simulation/test_scenarios.py
git commit -m "feat(sim): simulation loop, metrics, and scenario runner"
```

---

### Task 7: Plotting Module — 5 Figures

**Files:**
- Create: `simulation/plotting.py`
- Create: `tests/simulation/test_plotting.py`

**Step 1: Write a smoke test**

Create `tests/simulation/test_plotting.py`:

```python
"""Smoke tests for plotting — verify figures are created without errors."""
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for CI

from simulation.scenarios import run_simulation
from simulation.config import SimConfig
from simulation.plotting import (
    plot_pnl_comparison,
    plot_index_and_price,
    plot_reserves,
    plot_funding_and_premium,
    plot_welfare_summary,
)


def _result():
    return run_simulation(SimConfig(T=100), seed=42)


def test_plot_pnl_creates_figure():
    fig = plot_pnl_comparison(_result())
    assert fig is not None
    assert len(fig.axes) >= 2  # main plot + A_T subplot


def test_plot_index_creates_figure():
    fig = plot_index_and_price(_result())
    assert fig is not None


def test_plot_reserves_creates_figure():
    fig = plot_reserves(_result())
    assert fig is not None


def test_plot_funding_creates_figure():
    fig = plot_funding_and_premium(_result())
    assert fig is not None


def test_plot_welfare_creates_figure():
    fig = plot_welfare_summary(_result())
    assert fig is not None
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/simulation/test_plotting.py -v`
Expected: FAIL

**Step 3: Write plotting.py**

Create `simulation/plotting.py`:

```python
"""All matplotlib figure builders for the demo notebook.

Each function takes a SimResult and returns a matplotlib Figure.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from simulation.scenarios import SimResult
from simulation.metrics import hedge_effectiveness, ecosystem_welfare

# Style constants
HEDGED_COLOR = "#2ecc71"
UNHEDGED_COLOR = "#e74c3c"
INDEX_COLOR = "#3498db"
MARK_COLOR = "#e67e22"
RISKY_COLOR = "#9b59b6"
NUMERAIRE_COLOR = "#f1c40f"
UW_COLOR = "#1abc9c"

PHASE_COLORS = ["#d4e6f1", "#fdebd0", "#fadbd8"]  # calm, gradual, shock
PHASE_LABELS = ["Calm", "Gradual JIT Growth", "Shock"]


def _add_phase_shading(ax, T: int):
    """Add background shading for the 3-phase narrative arc."""
    third = T // 3
    for i, (color, label) in enumerate(zip(PHASE_COLORS, PHASE_LABELS)):
        ax.axvspan(i * third, (i + 1) * third, alpha=0.3, color=color, label=label)


def plot_pnl_comparison(result: SimResult) -> plt.Figure:
    """Plot 1: Hedged vs Unhedged PLP P&L with A_T subplot."""
    T = len(result.A_T)
    blocks = np.arange(T)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), height_ratios=[3, 1],
                                    sharex=True, gridspec_kw={"hspace": 0.08})

    # Phase shading
    _add_phase_shading(ax1, T)

    # P&L lines
    ax1.plot(blocks, result.hedged_pnl, color=HEDGED_COLOR, linewidth=2,
             label="PLP (Hedged)")
    ax1.plot(blocks, result.unhedged_pnl, color=UNHEDGED_COLOR, linewidth=2,
             label="PLP (Unhedged)", linestyle="--")

    ax1.set_ylabel("Cumulative P&L")
    ax1.set_title("PLP Profit & Loss: Hedged vs Unhedged", fontsize=14, fontweight="bold")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    # A_T subplot
    ax2.fill_between(blocks, result.A_T, alpha=0.4, color=INDEX_COLOR)
    ax2.plot(blocks, result.A_T, color=INDEX_COLOR, linewidth=1)
    ax2.set_ylabel("$A_T$")
    ax2.set_xlabel("Block Number")
    ax2.set_ylim(0, 1)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_index_and_price(result: SimResult) -> plt.Figure:
    """Plot 2: A_T trajectory + mark vs index price."""
    T = len(result.A_T)
    blocks = np.arange(T)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True,
                                    gridspec_kw={"hspace": 0.08})

    # A_T
    ax1.plot(blocks, result.A_T, color=INDEX_COLOR, linewidth=1.5)
    ax1.fill_between(blocks, result.A_T, alpha=0.2, color=INDEX_COLOR)
    ax1.set_ylabel("$A_T$ (Fee Concentration)")
    ax1.set_title("Fee Concentration Index & CFMM Price Response", fontsize=14, fontweight="bold")
    ax1.set_ylim(0, 1)
    ax1.grid(True, alpha=0.3)

    # Prices
    ax2.plot(blocks, result.p_index, color=INDEX_COLOR, linewidth=1.5,
             label="$p_{index} = A_T/(1-A_T)$")
    ax2.plot(blocks, result.p_mark, color=MARK_COLOR, linewidth=1.5,
             label="$p_{mark} = (1-x)/x$", linestyle="--")
    ax2.fill_between(blocks, result.p_index, result.p_mark, alpha=0.15,
                     color=MARK_COLOR, label="Basis")
    ax2.set_ylabel("Price $p$")
    ax2.set_xlabel("Block Number")
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_reserves(result: SimResult) -> plt.Figure:
    """Plot 3: Reserve composition (stacked area) over time."""
    T = len(result.A_T)
    blocks = np.arange(T)

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.stackplot(blocks, result.x, result.y,
                 labels=["Risky Reserve $x$", "Numeraire Reserve $y$"],
                 colors=[RISKY_COLOR, NUMERAIRE_COLOR], alpha=0.7)

    # Total value line
    total = result.p_index * result.x + result.y
    ax.plot(blocks, total, color="black", linewidth=1.5, linestyle=":",
            label="Total Value $px + y$")

    ax.set_title("CFMM Reserve Composition Over Time", fontsize=14, fontweight="bold")
    ax.set_xlabel("Block Number")
    ax.set_ylabel("Reserve Amount")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_funding_and_premium(result: SimResult) -> plt.Figure:
    """Plot 4: Funding rate + dynamic fee, cumulative premium flows."""
    T = len(result.A_T)
    blocks = np.arange(T)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True,
                                    gridspec_kw={"hspace": 0.12})

    # Funding rate and fee
    ax1.plot(blocks, result.funding_rates, color=MARK_COLOR, linewidth=1,
             label="Funding Rate $r$", alpha=0.8)
    ax1.plot(blocks, result.fees, color=INDEX_COLOR, linewidth=1.5,
             label="Dynamic Fee $\\varphi(t)$")
    ax1.set_ylabel("Rate")
    ax1.set_title("Funding Rate & Premium Cost", fontsize=14, fontweight="bold")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    # Cumulative premiums
    ax2.plot(blocks, result.cum_premium_paid, color=UNHEDGED_COLOR, linewidth=1.5,
             label="PLP Premium Paid")
    ax2.plot(blocks, result.cum_premium_earned, color=UW_COLOR, linewidth=1.5,
             label="Underwriter Premium Earned", linestyle="--")
    ax2.set_ylabel("Cumulative Premium")
    ax2.set_xlabel("Block Number")
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_welfare_summary(result: SimResult) -> plt.Figure:
    """Plot 5 (Bonus): Ecosystem welfare bar chart."""
    hedged_final = result.hedged_pnl[-1]
    unhedged_final = result.unhedged_pnl[-1]
    uw_final = result.underwriter_pnl[-1]
    total = hedged_final + uw_final

    labels = ["PLP\n(Hedged)", "PLP\n(Unhedged)", "Underwriter", "Total\nWelfare"]
    values = [hedged_final, unhedged_final, uw_final, total]
    colors = [HEDGED_COLOR, UNHEDGED_COLOR, UW_COLOR, "#34495e"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, values, color=colors, edgecolor="white", linewidth=1.5)

    # Value labels on bars
    for bar, val in zip(bars, values):
        y = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, y + abs(y) * 0.02,
                f"{val:.1f}", ha="center", va="bottom", fontweight="bold")

    ax.set_title("Ecosystem Welfare Summary", fontsize=14, fontweight="bold")
    ax.set_ylabel("Cumulative P&L")
    ax.axhline(y=0, color="gray", linewidth=0.5)
    ax.grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    return fig
```

**Step 4: Run tests**

Run: `pytest tests/simulation/test_plotting.py -v`
Expected: 5 PASS

**Step 5: Commit**

```bash
git add simulation/plotting.py tests/simulation/test_plotting.py
git commit -m "feat(sim): 5 publication-quality plot builders for LP demo"
```

---

### Task 8: Demo Notebook

**Files:**
- Create: `notebooks/demo.ipynb`

**Step 1: Create the notebook**

Create `notebooks/demo.ipynb` as a Jupyter notebook with these cells in order:

**Cell 1 (markdown):**
```markdown
# ThetaSwap: Fee Concentration Hedge Demo

**What if you could hedge against JIT competition?**

This notebook demonstrates how ThetaSwap's fee concentration derivative protects passive LPs against adverse competition from just-in-time (JIT) liquidity providers.

We simulate three market regimes:
1. **Calm** — Low concentration, competitive equilibrium
2. **Gradual JIT Growth** — A JIT bot ramps up over 1000 blocks
3. **Shock** — Sudden MEV event spikes concentration

For each, we compare a hedged PLP (using ThetaSwap) vs an unhedged PLP.
```

**Cell 2 (code):**
```python
import numpy as np
import matplotlib.pyplot as plt
from simulation.config import SimConfig
from simulation.scenarios import run_simulation
from simulation.metrics import hedge_effectiveness, ecosystem_welfare
from simulation.plotting import (
    plot_pnl_comparison,
    plot_index_and_price,
    plot_reserves,
    plot_funding_and_premium,
    plot_welfare_summary,
)

%matplotlib inline
plt.rcParams["figure.dpi"] = 120
```

**Cell 3 (markdown):**
```markdown
## Setup

We use the default simulation parameters: 3000 blocks across three phases, 30 bps base fee, 10% premium fraction. The fee concentration index $A_T$ evolves synthetically through calm → gradual → shock.
```

**Cell 4 (code):**
```python
cfg = SimConfig()
result = run_simulation(cfg, seed=42, scenario="narrative")

print(f"Simulation: {cfg.T} blocks, L₀={cfg.L_0}, α={cfg.alpha}")
print(f"Fee: {cfg.fee_base*10000:.0f} bps base, {cfg.fee_max*10000:.0f} bps max")
print(f"Premium fraction: {cfg.premium_fraction*100:.0f}%")
print(f"A_T range: [{result.A_T.min():.3f}, {result.A_T.max():.3f}]")
```

**Cell 5 (markdown):**
```markdown
## Plot 1: The Money Plot — Hedged vs Unhedged P&L

The green line shows the hedged PLP's cumulative P&L. The red dashed line shows the unhedged PLP. Background shading indicates the three market regimes.

Notice how the lines track closely during the calm phase (hedge costs little), diverge during gradual JIT growth, and dramatically separate during the shock.
```

**Cell 6 (code):**
```python
fig = plot_pnl_comparison(result)
plt.show()
```

**Cell 7 (markdown):**
```markdown
## Plot 2: Fee Concentration Index & Price Response

The top panel shows $A_T$ — the fee concentration index — evolving through the three phases. The bottom panel shows how the CFMM's index price $p_{index} = A_T/(1-A_T)$ and mark price $p_{mark}$ track each other.

The shaded area between them is the *basis* — the signal that drives funding rate payments.
```

**Cell 8 (code):**
```python
fig = plot_index_and_price(result)
plt.show()
```

**Cell 9 (markdown):**
```markdown
## Plot 3: Reserve Composition

The CFMM starts fully in the risky asset (at $A_0 = 0$). As fee concentration increases, reserves shift from risky to numeraire — this is the protection payoff mechanism in action.

The dotted line shows total LP value $px + y$ tracking $V_{LP}(p) = \ln(1+p)$.
```

**Cell 10 (code):**
```python
fig = plot_reserves(result)
plt.show()
```

**Cell 11 (markdown):**
```markdown
## Plot 4: Funding Rate & Premium Cost

The top panel shows the funding rate and dynamic fee. The bottom panel shows cumulative premium flows: what the PLP pays vs what the underwriter earns.

Key insight: the cost of the hedge is small during calm markets and only scales when protection is actually needed.
```

**Cell 12 (code):**
```python
fig = plot_funding_and_premium(result)
plt.show()
```

**Cell 13 (markdown):**
```markdown
## Plot 5: Ecosystem Welfare

This bar chart shows final P&L for each participant. The hedge is **not zero-sum**: total welfare (PLP hedged + Underwriter) is positive because the hedge enables PLPs to remain in the pool and earn more total fees.
```

**Cell 14 (code):**
```python
fig = plot_welfare_summary(result)
plt.show()
```

**Cell 15 (markdown):**
```markdown
## Summary Statistics
```

**Cell 16 (code):**
```python
eff = hedge_effectiveness(result.hedged_pnl[-1], result.unhedged_pnl[-1])
welf = ecosystem_welfare(result.hedged_pnl[-1], result.underwriter_pnl[-1])

print("=" * 50)
print("FINAL RESULTS")
print("=" * 50)
print(f"Hedged PLP P&L:    {result.hedged_pnl[-1]:>10.2f}")
print(f"Unhedged PLP P&L:  {result.unhedged_pnl[-1]:>10.2f}")
print(f"Underwriter P&L:   {result.underwriter_pnl[-1]:>10.2f}")
print(f"Hedge Effectiveness: {eff:>8.1%}")
print(f"Ecosystem Welfare:   {welf:>10.2f}")
print(f"Premium Paid:        {result.cum_premium_paid[-1]:>10.2f}")
print(f"Max A_T:             {result.A_T.max():>10.3f}")
```

**Step 2: Verify notebook runs**

Run: `cd notebooks && jupyter nbconvert --to notebook --execute demo.ipynb --output demo_executed.ipynb`
Expected: Executes without errors, produces output notebook with all plots

**Step 3: Commit**

```bash
git add notebooks/demo.ipynb
git commit -m "feat(sim): demo notebook — full LP hedge narrative with 5 plots"
```

---

### Task 9: Final Verification

**Step 1: Run full test suite**

Run: `pytest tests/simulation/ -v --tb=short`
Expected: All tests pass (config=3, cfmm=13, index=7, funding=9, agents=5, scenarios=6, plotting=5 = ~48 tests)

**Step 2: Cross-check invariants**

Run a quick Python check:
```bash
python3 -c "
from simulation.scenarios import run_simulation
from simulation.config import SimConfig
import numpy as np

r = run_simulation(SimConfig(T=3000), seed=42)
print(f'Invariant max deviation: {np.max(np.abs(r.invariant_check)):.2e}')
print(f'A_T bounds: [{r.A_T.min():.4f}, {r.A_T.max():.4f}]')
print(f'All A_T < 1: {np.all(r.A_T < 1.0)}')
print(f'Hedged > Unhedged at end: {r.hedged_pnl[-1] > r.unhedged_pnl[-1]}')
"
```
Expected: Invariant deviation < 1e-10, A_T bounded, hedged outperforms

**Step 3: Commit any final fixes**

```bash
git add -A
git commit -m "chore(sim): final verification — all invariants hold"
```
