# Dune MCP Extraction Pipeline — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract Uniswap V3 ETH/USDC 30bps event data via Dune MCP, compute A_T in SQL, and estimate structural logit in JAX to test whether fee concentration risk drives LP exit.

**Architecture:** DuneSQL handles JIT classification, FIFO lifecycle matching, daily A_T computation, and panel assembly via 4 saved queries (Q1-Q4). Python receives small JSON results (~90 rows) and runs JAX logit MLE. Progressive gates fail-fast before committing credits.

**Tech Stack:** Dune MCP (HTTP transport, pre-decoded tables), JAX 0.9.1 CPU, Python 3.14 (uhi8 venv). All Python code uses frozen dataclasses, free pure functions, full typing per @functional-python.

**Venv:** `source /home/jmsbpp/apps/ThetaSwap/ThetaSwap-research/uhi8/bin/activate`

**Working directory:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/`

**Design doc:** `docs/plans/2026-03-05-dune-extraction-design.md`

**Upstream spec:** `specs/econometrics/lp-insurance-demand.tex`

**Key constants:**
- Pool: ETH/USDC 30bps `0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8`
- Window: 90 days via `evt_block_date >= CURRENT_DATE - INTERVAL '90' DAY`
- Dune tables: `uniswap_v3_ethereum.uniswapv3pool_evt_mint`, `_evt_burn`, `_evt_swap`
- Credit budget: ~80 credits out of 2,500/month

---

## Task 0: Package Setup and Domain Types

**Files:**
- Create: `econometrics/__init__.py`
- Create: `econometrics/types.py`

**Step 1: Create package**

```python
# econometrics/__init__.py
"""LP insurance demand econometric pipeline — Dune MCP + JAX."""
```

**Step 2: Create domain types**

```python
# econometrics/types.py
"""Domain types — frozen dataclasses, type aliases, constants per @functional-python."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, TypeAlias


# ── Constants ──────────────────────────────────────────────────────────
POOL_ADDRESS: Final = "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
POOL_NAME: Final = "ETH/USDC 30bps"
FEE_TIER: Final = 3000
WINDOW_DAYS: Final = 90
MIN_JIT_EVENTS: Final = 50
FEE_REVENUE_PROXY: Final = 100.0  # avg daily fee revenue in USD per LP (placeholder)


# ── Type Aliases ───────────────────────────────────────────────────────
DuneRow: TypeAlias = dict[str, object]


# ── Value Types ────────────────────────────────────────────────────────
@dataclass(frozen=True)
class DailyPanelRow:
    """One day of the estimation panel from Dune Q2+Q3."""
    day: str
    a_t: float
    passive_exit_count: int
    total_positions: int
    jit_count: int
    swap_count: int
    jit_count_lag1: int


@dataclass(frozen=True)
class EstimationResult:
    """Structural logit estimation output."""
    beta_concentration: float   # β₃ — parameter of interest
    se_concentration: float
    p_value_concentration: float
    beta_swap: float
    beta_jit_lag: float
    n_obs: int
    pseudo_r2: float
    wtp_mean: float             # β₃ × E[A_T] × FeeRevenue
    log_likelihood: float
    aic: float
```

**Step 3: Commit**

```bash
git add econometrics/__init__.py econometrics/types.py
git commit -m "feat(econometrics): domain types and constants for Dune pipeline"
```

---

## Task 1: JAX Logit Estimator — TDD

**Files:**
- Create: `econometrics/estimate.py`
- Create: `tests/__init__.py`
- Create: `tests/econometrics/__init__.py`
- Create: `tests/econometrics/test_estimate.py`

**Step 1: Write the failing tests**

```python
# tests/__init__.py
# (empty)

# tests/econometrics/__init__.py
# (empty)
```

```python
# tests/econometrics/test_estimate.py
"""Tests for JAX structural logit estimation."""
from __future__ import annotations

import jax.numpy as jnp
import jax.random as jr
from econometrics.estimate import structural_logit, nll
from econometrics.types import EstimationResult


def test_nll_perfect_separation_low_loss() -> None:
    """When model perfectly predicts, NLL should be near zero."""
    params = jnp.array([0.0, 10.0, 0.0, 0.0])  # strong positive β for x1
    X = jnp.array([[1.0, 1.0, 0.0, 0.0],
                    [1.0, -1.0, 0.0, 0.0]])
    y = jnp.array([1.0, 0.0])
    loss = float(nll(params, X, y))
    assert loss < 0.1


def test_nll_random_params_positive() -> None:
    """NLL should always be positive."""
    params = jnp.array([0.5, -0.3, 0.1, 0.2])
    X = jnp.ones((5, 4))
    y = jnp.array([1.0, 0.0, 1.0, 0.0, 1.0])
    loss = float(nll(params, X, y))
    assert loss > 0


def test_positive_a_t_coefficient_on_synthetic_data() -> None:
    """On synthetic data where high A_T → exit, β₃ should be positive."""
    key = jr.PRNGKey(42)
    n = 500
    k1, k2, k3, k4 = jr.split(key, 4)

    a_t = jr.uniform(k1, (n,))
    swap_count = jr.poisson(k2, 50.0, (n,)).astype(jnp.float32)
    jit_lag = jr.poisson(k3, 3.0, (n,)).astype(jnp.float32)

    # Exit probability increases with A_T
    latent = 2.0 * a_t - 1.0 + jr.logistic(k4, (n,))
    exit_var = (latent > 0).astype(jnp.float32)

    result = structural_logit(
        exit=exit_var,
        a_t=a_t,
        jit_lag=jit_lag,
        swap_count=swap_count,
    )
    assert isinstance(result, EstimationResult)
    assert result.beta_concentration > 0
    assert result.p_value_concentration < 0.05


def test_estimation_result_has_wtp() -> None:
    """Result should include non-negative dollar WTP estimate."""
    key = jr.PRNGKey(123)
    n = 300
    k1, k2, k3, k4 = jr.split(key, 4)

    a_t = jr.uniform(k1, (n,))
    exit_var = (a_t + jr.logistic(k2, (n,)) * 0.5 > 0.5).astype(jnp.float32)

    result = structural_logit(
        exit=exit_var,
        a_t=a_t,
        jit_lag=jr.poisson(k3, 2.0, (n,)).astype(jnp.float32),
        swap_count=jr.poisson(k4, 40.0, (n,)).astype(jnp.float32),
    )
    assert result.wtp_mean >= 0


def test_all_zeros_exit_returns_result() -> None:
    """Edge case: no exits. Should still return a result (β₃ ≈ 0)."""
    n = 100
    result = structural_logit(
        exit=jnp.zeros(n),
        a_t=jnp.ones(n) * 0.5,
        jit_lag=jnp.ones(n),
        swap_count=jnp.ones(n) * 10,
    )
    assert isinstance(result, EstimationResult)
    assert result.n_obs == n
```

**Step 2: Run tests to verify failure**

```bash
source /home/jmsbpp/apps/ThetaSwap/ThetaSwap-research/uhi8/bin/activate
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev
python -m pytest tests/econometrics/test_estimate.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'econometrics.estimate'`

**Step 3: Implement JAX logit estimator**

```python
# econometrics/estimate.py
"""Structural logit estimation via JAX autodiff.

Estimates: P(Exit=1) = σ(β₀ + β₁·A_T + β₂·SwapCount + β₃·JIT_lag)
where β₁ is the concentration risk premium (parameter of interest).

Uses JAX for exact gradients and Hessian-based standard errors.
"""
from __future__ import annotations

import jax
import jax.numpy as jnp
import jax.scipy.optimize
import jax.scipy.stats as jstats
from jax import Array

from econometrics.types import EstimationResult, FEE_REVENUE_PROXY


def nll(params: Array, X: Array, y: Array) -> Array:
    """Negative log-likelihood for binary logit.

    Args:
        params: Coefficient vector [β₀, β₁, β₂, β₃].
        X: Design matrix (n, 4) with intercept column.
        y: Binary outcome vector (n,).
    """
    logits = X @ params
    # Numerically stable: log(σ(z)) = z - log(1+exp(z)) = -softplus(-z)
    log_p = -jax.nn.softplus(-logits)
    log_1_minus_p = -jax.nn.softplus(logits)
    return -jnp.mean(y * log_p + (1.0 - y) * log_1_minus_p)


def structural_logit(
    exit: Array,
    a_t: Array,
    jit_lag: Array,
    swap_count: Array,
) -> EstimationResult:
    """Estimate structural logit of LP exit decision.

    Args:
        exit: Binary outcome (1 = LP exits), shape (n,).
        a_t: Fee concentration index at exit event, shape (n,).
        jit_lag: Lagged JIT count (instrument as control), shape (n,).
        swap_count: Daily swap count (fee revenue proxy), shape (n,).

    Returns:
        EstimationResult with β₃ (concentration), SEs, p-values, WTP.
    """
    n = exit.shape[0]
    ones = jnp.ones(n)
    X = jnp.column_stack([ones, a_t, swap_count, jit_lag])

    # Optimize via L-BFGS
    init_params = jnp.zeros(4)
    result = jax.scipy.optimize.minimize(
        nll, init_params, args=(X, exit), method="BFGS"
    )
    params = result.x

    # Standard errors via inverse Hessian
    hess = jax.hessian(nll)(params, X, exit)
    # Multiply by n because nll uses mean (Hessian of mean = Hessian of sum / n)
    cov = jnp.linalg.inv(hess * n) / n
    ses = jnp.sqrt(jnp.diag(jnp.abs(cov)))

    # z-scores and two-sided p-values
    z_scores = params / ses
    p_values = 2.0 * jstats.norm.sf(jnp.abs(z_scores))

    # Null model (intercept only) for pseudo-R²
    null_params = jnp.zeros(4).at[0].set(params[0])
    nll_fitted = float(nll(params, X, exit))
    nll_null = float(nll(null_params, X, exit))
    pseudo_r2 = 1.0 - nll_fitted / nll_null if nll_null > 0 else 0.0

    # Log-likelihood (sum, not mean)
    ll = -nll_fitted * n

    # AIC = 2k - 2ln(L)
    k = 4
    aic = 2 * k - 2 * ll

    # WTP = β₁ × E[A_T] × FeeRevenue
    beta_1 = float(params[1])
    mean_a_t = float(jnp.mean(a_t))
    wtp = beta_1 * mean_a_t * FEE_REVENUE_PROXY

    return EstimationResult(
        beta_concentration=beta_1,
        se_concentration=float(ses[1]),
        p_value_concentration=float(p_values[1]),
        beta_swap=float(params[2]),
        beta_jit_lag=float(params[3]),
        n_obs=n,
        pseudo_r2=pseudo_r2,
        wtp_mean=max(wtp, 0.0),
        log_likelihood=ll,
        aic=aic,
    )
```

**Step 4: Run tests**

```bash
python -m pytest tests/econometrics/test_estimate.py -v
```

Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add econometrics/estimate.py tests/__init__.py tests/econometrics/__init__.py tests/econometrics/test_estimate.py
git commit -m "feat(econometrics): JAX structural logit estimator with autodiff SEs"
```

---

## Task 2: Ingest Module — Dune JSON to JAX Arrays

**Files:**
- Create: `econometrics/ingest.py`
- Create: `tests/econometrics/test_ingest.py`

**Step 1: Write the failing tests**

```python
# tests/econometrics/test_ingest.py
"""Tests for Dune MCP JSON → JAX array ingestion."""
from __future__ import annotations

import jax.numpy as jnp
from econometrics.ingest import ingest_daily_panel, merge_jit_instrument
from econometrics.types import DailyPanelRow


def test_ingest_daily_panel_basic() -> None:
    """Convert Dune Q2 rows to DailyPanelRow list."""
    rows = [
        {"day": "2026-01-01", "a_t": 0.35, "passive_exit_count": 10,
         "total_positions": 25, "jit_count": 5, "swap_count": 100},
        {"day": "2026-01-02", "a_t": 0.42, "passive_exit_count": 8,
         "total_positions": 20, "jit_count": 3, "swap_count": 80},
    ]
    result = ingest_daily_panel(rows)
    assert len(result) == 2
    assert isinstance(result[0], DailyPanelRow)
    assert result[0].a_t == 0.35
    assert result[1].swap_count == 80
    # jit_count_lag1 defaults to 0 before merge
    assert result[0].jit_count_lag1 == 0


def test_merge_jit_instrument() -> None:
    """Merge Q3 lagged JIT counts into panel rows."""
    panel = [
        DailyPanelRow("2026-01-01", 0.3, 10, 25, 5, 100, 0),
        DailyPanelRow("2026-01-02", 0.4, 8, 20, 3, 80, 0),
    ]
    q3_rows = [
        {"day": "2026-01-01", "jit_count": 5, "jit_count_lag1": 0},
        {"day": "2026-01-02", "jit_count": 3, "jit_count_lag1": 5},
    ]
    merged = merge_jit_instrument(panel, q3_rows)
    assert merged[0].jit_count_lag1 == 0
    assert merged[1].jit_count_lag1 == 5


def test_ingest_empty_rows() -> None:
    """Empty input returns empty list."""
    assert ingest_daily_panel([]) == []


def test_merge_preserves_other_fields() -> None:
    """Merge only touches jit_count_lag1, leaves rest intact."""
    panel = [DailyPanelRow("2026-01-01", 0.55, 12, 30, 7, 150, 0)]
    q3_rows = [{"day": "2026-01-01", "jit_count": 7, "jit_count_lag1": 4}]
    merged = merge_jit_instrument(panel, q3_rows)
    assert merged[0].a_t == 0.55
    assert merged[0].passive_exit_count == 12
    assert merged[0].jit_count_lag1 == 4
```

**Step 2: Run tests to verify failure**

```bash
python -m pytest tests/econometrics/test_ingest.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'econometrics.ingest'`

**Step 3: Implement ingestion**

```python
# econometrics/ingest.py
"""Pure functions: Dune MCP JSON rows → typed domain objects."""
from __future__ import annotations

from dataclasses import replace
from typing import Sequence

from econometrics.types import DailyPanelRow, DuneRow


def ingest_daily_panel(rows: Sequence[DuneRow]) -> list[DailyPanelRow]:
    """Convert Dune Q2 result rows to DailyPanelRow list.

    Args:
        rows: List of dicts from Dune getExecutionResults.

    Returns:
        Typed panel rows with jit_count_lag1 defaulted to 0
        (populated later by merge_jit_instrument).
    """
    return [
        DailyPanelRow(
            day=str(r["day"]),
            a_t=float(r["a_t"]),
            passive_exit_count=int(r["passive_exit_count"]),
            total_positions=int(r["total_positions"]),
            jit_count=int(r["jit_count"]),
            swap_count=int(r["swap_count"]),
            jit_count_lag1=0,
        )
        for r in rows
    ]


def merge_jit_instrument(
    panel: Sequence[DailyPanelRow],
    q3_rows: Sequence[DuneRow],
) -> list[DailyPanelRow]:
    """Merge Q3 lagged JIT instrument into panel rows.

    Args:
        panel: Panel rows from ingest_daily_panel.
        q3_rows: Dune Q3 result with day, jit_count, jit_count_lag1.

    Returns:
        New panel rows with jit_count_lag1 populated.
    """
    lag_map: dict[str, int] = {
        str(r["day"]): int(r["jit_count_lag1"]) for r in q3_rows
    }
    return [
        replace(row, jit_count_lag1=lag_map.get(row.day, 0))
        for row in panel
    ]
```

**Step 4: Run tests**

```bash
python -m pytest tests/econometrics/test_ingest.py -v
```

Expected: PASS (all 4 tests)

**Step 5: Commit**

```bash
git add econometrics/ingest.py tests/econometrics/test_ingest.py
git commit -m "feat(econometrics): Dune JSON ingestion and JIT instrument merge"
```

---

## Task 3: Gate 1 — Run Q1 via Dune MCP

**Files:** None (interactive MCP execution)

**Step 1: Create and execute Q1 via Dune MCP**

Use `mcp__dune__createDuneQuery` with the Q1 SQL from the design doc (90-day window JIT gate check).

**Step 2: Execute query**

Use `mcp__dune__executeQueryById` with the returned query_id.

**Step 3: Get results**

Use `mcp__dune__getExecutionResults` with the execution_id.

**Step 4: Evaluate gate**

- If `jit_tx_count >= 50`: PASS → proceed to Task 4
- If `jit_tx_count < 50`: FAIL → switch pool address to ETH/USDC 5bps (`0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640`) and re-run Q1

**Step 5: Record result**

Print gate result and credit cost to console. No commit needed.

---

## Task 4: Gate 2 — Run Q2 + Q3 via Dune MCP

**Files:** None (interactive MCP execution)

**Step 1: Create and execute Q2 (daily panel) via Dune MCP**

Use `mcp__dune__createDuneQuery` with the Q2 SQL from the design doc.

**Step 2: Create and execute Q3 (JIT instrument) via Dune MCP**

Use `mcp__dune__createDuneQuery` with the Q3 SQL from the design doc. Can run in parallel with Q2.

**Step 3: Get results for both queries**

Use `mcp__dune__getExecutionResults` for each execution_id.

**Step 4: Evaluate gate — visual pattern check**

Inspect the Q2 results:
- Do days with higher `a_t` have higher `passive_exit_count`?
- Is there variation in `a_t` across days?
- Are there enough non-zero `passive_exit_count` days for regression?

If no visible pattern: publishable null result. Document and stop.
If pattern visible: proceed to Task 5.

**Step 5: Record results and credit usage**

Check `mcp__dune__getUsage` to track cumulative credit spend.

---

## Task 5: Gate 3 — Run Structural Logit Estimation

**Files:** None (interactive Python execution)

This task wires the Dune MCP results from Task 4 into the Python estimator.

**Step 1: Ingest Q2 + Q3 results**

```python
# Run interactively or as a script
from econometrics.ingest import ingest_daily_panel, merge_jit_instrument

# q2_rows and q3_rows are the JSON row lists from Dune MCP getExecutionResults
panel = ingest_daily_panel(q2_rows)
panel = merge_jit_instrument(panel, q3_rows)
```

**Step 2: Prepare JAX arrays and estimate**

```python
import jax.numpy as jnp
from econometrics.estimate import structural_logit

a_t = jnp.array([r.a_t for r in panel])
exit_var = jnp.array([float(r.passive_exit_count) for r in panel])
# Normalize exit to [0, 1] — fraction of positions that exited
exit_rate = exit_var / jnp.array([float(r.total_positions) for r in panel])
# Binarize: above-median exit rate = 1
exit_binary = (exit_rate > jnp.median(exit_rate)).astype(jnp.float32)

swap_count = jnp.array([float(r.swap_count) for r in panel])
jit_lag = jnp.array([float(r.jit_count_lag1) for r in panel])

result = structural_logit(exit_binary, a_t, jit_lag, swap_count)
print(f"β₃ (concentration) = {result.beta_concentration:.4f}")
print(f"SE = {result.se_concentration:.4f}")
print(f"p-value = {result.p_value_concentration:.4f}")
print(f"WTP = ${result.wtp_mean:.2f}")
print(f"Pseudo-R² = {result.pseudo_r2:.4f}")
print(f"N = {result.n_obs}")
```

**Step 3: Evaluate gate**

- If `beta_concentration > 0` AND `p_value_concentration < 0.05`: PASS → model validated
- If `beta_concentration <= 0` OR `p_value_concentration >= 0.05`: FAIL → expand window to 180 days or revise specification

**Step 4: Save result**

```python
# Save estimation result to JSON for reproducibility
import json
from dataclasses import asdict
from pathlib import Path

Path("data/econometrics").mkdir(parents=True, exist_ok=True)
with open("data/econometrics/estimation_result.json", "w") as f:
    json.dump(asdict(result), f, indent=2)
```

**Step 5: Commit**

```bash
git add data/econometrics/estimation_result.json
git commit -m "results(econometrics): Gate 3 structural logit estimation"
```

---

## Summary

| Task | Component | Tests | Depends On | Credits |
|------|-----------|-------|------------|---------|
| 0 | Types, constants, package setup | — | — | 0 |
| 1 | JAX logit estimator | test_estimate.py (5 tests) | Task 0 | 0 |
| 2 | Dune JSON ingestion | test_ingest.py (4 tests) | Task 0 | 0 |
| 3 | Gate 1: Q1 JIT existence | — | — | ~0.15 |
| 4 | Gate 2: Q2+Q3 daily panel | — | Gate 1 pass | ~2-4 |
| 5 | Gate 3: Structural logit | — | Tasks 1, 2, Gate 2 pass | 0 |

**Tasks 0-2 are pure Python (0 credits).** Tasks 3-4 spend credits. Task 5 is Python-only.

**Total estimated credits: ~3-5** for the happy path, out of 2,500 available.

**After implementation:** If Gate 3 passes, extend with Q4 (position-level robustness) and alternative specifications (expanded window, different pools).
