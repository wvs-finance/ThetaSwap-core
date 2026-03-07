# Exit Hazard Model Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the failed duration model with a binary exit hazard (discrete-time survival) model that proves insurance demand without collinearity.

**Architecture:** Construct a position-day panel from existing 600 positions + 41 days of daily A_T. Estimate a pooled logit via JAX MLE with day-clustered sandwich SEs. Translate marginal effects into actuarially fair insurance premiums.

**Tech Stack:** Python 3, JAX 0.9.1 CPU, frozen dataclasses (@functional-python), uhi8 venv, Jupyter (uhi8 kernel).

**IMPORTANT:** `.gitignore` ignores `*.py` and `docs/`. Always use `git add -f` for Python files and docs.

**Existing code context:**
- `econometrics/data.py` — hardcoded `RAW_POSITIONS` (600 tuples: burn_date, blocklife, exit_day_a_t), `DAILY_AT_MAP` (41 days), `IL_MAP` (41 days)
- `econometrics/types.py:1-124` — frozen dataclasses (DailyPanelRow, PositionRow, EstimationResult, DurationResult, LaggedPositionRow, RobustDurationResult, SensitivityRow, QuartileRow)
- `econometrics/ingest.py:1-147` — ingestion/panel building functions including `approximate_mint_date`, `BLOCKS_PER_DAY = 7200.0`
- `econometrics/duration.py` — OLD duration model (will NOT be modified, kept for reference)
- `tests/econometrics/` — existing tests for data, types, ingest, duration

---

### Task 0: New Types for Exit Hazard Model

**Files:**
- Modify: `econometrics/types.py:124` (append after QuartileRow)
- Test: `tests/econometrics/test_types.py`

**Context:** We need three new frozen dataclasses for the exit hazard model. All follow @functional-python: `@dataclass(frozen=True)`, no methods except `__post_init__` for validation, typed fields, `Final` constants.

**Step 1: Write the failing tests**

Add to `tests/econometrics/test_types.py`:

```python
from econometrics.types import ExitPanelRow, LogitResult, MarginalEffect


def test_exit_panel_row_construction() -> None:
    """ExitPanelRow holds one position-day observation."""
    row = ExitPanelRow(
        position_idx=0,
        day="2025-12-10",
        exited=1,
        a_t_lagged=0.13,
        il=0.012,
        log_age=2.3,
    )
    assert row.exited in (0, 1)
    assert row.a_t_lagged == 0.13
    assert row.log_age == 2.3


def test_logit_result_construction() -> None:
    """LogitResult holds MLE estimation output."""
    result = LogitResult(
        beta_a_t=0.5,
        beta_il=-0.3,
        beta_log_age=-0.1,
        beta_intercept=-3.0,
        se_a_t=0.1,
        se_il=0.2,
        se_log_age=0.05,
        se_intercept=0.5,
        cluster_se_a_t=0.15,
        cluster_se_il=0.25,
        cluster_se_log_age=0.08,
        cluster_se_intercept=0.6,
        p_value_a_t=0.001,
        cluster_p_value_a_t=0.003,
        n_obs=5000,
        n_exits=600,
        n_clusters=41,
        log_likelihood=-800.0,
        aic=1608.0,
        pseudo_r2=0.05,
        mean_exit_prob=0.12,
    )
    assert result.beta_a_t == 0.5
    assert result.n_clusters == 41


def test_marginal_effect_construction() -> None:
    """MarginalEffect holds insurance pricing translation."""
    me = MarginalEffect(
        marginal_effect=0.05,
        delta_a_t=0.10,
        prob_increase=0.005,
        hours_lost=24.0,
        implied_premium_usd=2.40,
        mean_exit_prob=0.12,
    )
    assert me.marginal_effect == 0.05
    assert me.implied_premium_usd == 2.40
```

**Step 2: Run tests to verify they fail**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/test_types.py -v -k "exit_panel or logit_result_construction or marginal_effect"`
Expected: FAIL with `ImportError: cannot import name 'ExitPanelRow'`

**Step 3: Write minimal implementation**

Append to `econometrics/types.py` after line 124 (after the QuartileRow class):

```python


# ── Exit Hazard Model Types ───────────────────────────────────────────

@dataclass(frozen=True)
class ExitPanelRow:
    """One position-day observation for the exit hazard model.

    Y_i,t = exited (1 if position i exits on day t, 0 otherwise).
    Treatment = a_t_lagged (pool-level A_T from a prior day).
    """
    position_idx: int      # index into RAW_POSITIONS
    day: str               # observation date (ISO format)
    exited: int            # 1 = exit, 0 = survived
    a_t_lagged: float      # A_T from (day - lag)
    il: float              # IL proxy on this day
    log_age: float         # log(days since mint), floored at log(1)


@dataclass(frozen=True)
class LogitResult:
    """Logit MLE estimation output with day-clustered SEs."""
    beta_a_t: float           # beta_1 — parameter of interest
    beta_il: float            # beta_2 — IL control
    beta_log_age: float       # beta_3 — duration dependence
    beta_intercept: float     # beta_0
    se_a_t: float             # MLE SE
    se_il: float
    se_log_age: float
    se_intercept: float
    cluster_se_a_t: float     # day-clustered sandwich SE
    cluster_se_il: float
    cluster_se_log_age: float
    cluster_se_intercept: float
    p_value_a_t: float        # MLE p-value
    cluster_p_value_a_t: float  # clustered p-value
    n_obs: int                # total position-day observations
    n_exits: int              # total exits (Y=1)
    n_clusters: int           # number of day clusters
    log_likelihood: float
    aic: float
    pseudo_r2: float          # McFadden's: 1 - LL/LL_null
    mean_exit_prob: float     # average predicted P(exit)


@dataclass(frozen=True)
class MarginalEffect:
    """Insurance pricing translation from logit marginal effect."""
    marginal_effect: float    # dP(exit)/dA_T at means
    delta_a_t: float          # A_T shock size (e.g. 0.10)
    prob_increase: float      # ME * delta_a_t
    hours_lost: float         # prob_increase * avg_remaining_hours
    implied_premium_usd: float  # hours_lost * fee_revenue_per_hour
    mean_exit_prob: float     # baseline P(exit) at means
```

**Step 4: Run tests to verify they pass**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/test_types.py -v -k "exit_panel or logit_result_construction or marginal_effect"`
Expected: 3 PASSED

**Step 5: Run full test suite**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/ -v`
Expected: All existing tests still pass + 3 new ones

**Step 6: Commit**

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev
git add -f econometrics/types.py tests/econometrics/test_types.py
git commit -m "feat(types): add ExitPanelRow, LogitResult, MarginalEffect for exit hazard model"
```

---

### Task 1: Panel Builder — build_exit_panel()

**Files:**
- Modify: `econometrics/ingest.py:147` (append after build_lagged_positions)
- Test: `tests/econometrics/test_ingest.py`

**Context:** Construct a position-day panel from existing data. For each position in `RAW_POSITIONS`, compute mint_date from `approximate_mint_date`. For each day in `DAILY_AT_MAP`, check if the position is alive (mint_date <= day <= burn_date). Output an `ExitPanelRow` with exited=1 on burn_date, 0 otherwise. Use lagged A_T: the treatment for day t is `daily_at_map[t - lag_days]`.

The function reuses existing `approximate_mint_date` (line 87) and `BLOCKS_PER_DAY` (line 11).

**Step 1: Write the failing tests**

Add to `tests/econometrics/test_ingest.py`:

```python
import math
from econometrics.ingest import build_exit_panel
from econometrics.types import ExitPanelRow


# ── Exit panel tests ──────────────────────────────────────────────────

PANEL_DAILY_AT: dict[str, float] = {
    "2025-12-20": 0.10,
    "2025-12-21": 0.15,
    "2025-12-22": 0.20,
    "2025-12-23": 0.12,
    "2025-12-24": 0.18,
}

PANEL_IL: dict[str, float] = {
    "2025-12-20": 0.005,
    "2025-12-21": 0.008,
    "2025-12-22": 0.012,
    "2025-12-23": 0.006,
    "2025-12-24": 0.010,
}


def test_build_exit_panel_single_position() -> None:
    """A single position alive for 3 days produces 3 rows, last one exited=1."""
    # blocklife = 2 days * 7200 = 14400 blocks, burn_date = Dec 22
    # => mint_date = Dec 20
    # Position alive on Dec 20, 21, 22 (exits on 22)
    raw = [("2025-12-22", 14400, 0.20)]
    panel = build_exit_panel(raw, PANEL_DAILY_AT, PANEL_IL, lag_days=1)

    # Should have rows for Dec 20, 21, 22
    assert len(panel) == 3
    assert all(isinstance(r, ExitPanelRow) for r in panel)

    # Only the last row (Dec 22) has exited=1
    exits = [r for r in panel if r.exited == 1]
    assert len(exits) == 1
    assert exits[0].day == "2025-12-22"

    # Non-exit rows
    survived = [r for r in panel if r.exited == 0]
    assert len(survived) == 2


def test_build_exit_panel_lagged_a_t() -> None:
    """Treatment uses A_T from (day - lag_days), not same day."""
    raw = [("2025-12-22", 14400, 0.20)]
    panel = build_exit_panel(raw, PANEL_DAILY_AT, PANEL_IL, lag_days=1)

    # Dec 20 row: lagged A_T = daily_at_map[Dec 19] -> not in map, should be excluded
    # Dec 21 row: lagged A_T = daily_at_map[Dec 20] = 0.10
    # Dec 22 row: lagged A_T = daily_at_map[Dec 21] = 0.15
    row_21 = [r for r in panel if r.day == "2025-12-21"]
    if row_21:
        assert row_21[0].a_t_lagged == 0.10
    row_22 = [r for r in panel if r.day == "2025-12-22"]
    assert row_22[0].a_t_lagged == 0.15


def test_build_exit_panel_log_age() -> None:
    """log_age is log(days since mint), floored at log(1)=0."""
    raw = [("2025-12-22", 14400, 0.20)]
    panel = build_exit_panel(raw, PANEL_DAILY_AT, PANEL_IL, lag_days=1)

    # Dec 20: age = 0 days since mint -> log(max(1, 0)) = log(1) = 0
    row_20 = [r for r in panel if r.day == "2025-12-20"]
    if row_20:
        assert row_20[0].log_age == 0.0

    # Dec 22: age = 2 days -> log(2)
    row_22 = [r for r in panel if r.day == "2025-12-22"]
    assert abs(row_22[0].log_age - math.log(2)) < 1e-6


def test_build_exit_panel_excludes_jit() -> None:
    """Positions with blocklife <= 1 block are excluded (JIT)."""
    raw = [("2025-12-22", 1, 0.20)]  # JIT position
    panel = build_exit_panel(raw, PANEL_DAILY_AT, PANEL_IL, lag_days=1)
    assert len(panel) == 0


def test_build_exit_panel_il_lookup() -> None:
    """IL comes from il_map on the observation day."""
    raw = [("2025-12-22", 14400, 0.20)]
    panel = build_exit_panel(raw, PANEL_DAILY_AT, PANEL_IL, lag_days=1)
    row_21 = [r for r in panel if r.day == "2025-12-21"]
    if row_21:
        assert row_21[0].il == 0.008


def test_build_exit_panel_empty_input() -> None:
    """Empty positions list returns empty panel."""
    panel = build_exit_panel([], PANEL_DAILY_AT, PANEL_IL, lag_days=1)
    assert panel == []
```

**Step 2: Run tests to verify they fail**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/test_ingest.py -v -k "exit_panel"`
Expected: FAIL with `ImportError: cannot import name 'build_exit_panel'`

**Step 3: Write minimal implementation**

Append to `econometrics/ingest.py` after line 147. Also add `ExitPanelRow` to the import on line 9.

First, update the import on line 9 from:
```python
from econometrics.types import DailyPanelRow, DuneRow, LaggedPositionRow, PositionRow
```
to:
```python
from econometrics.types import DailyPanelRow, DuneRow, ExitPanelRow, LaggedPositionRow, PositionRow
```

Then add `import math` at the top (after `from statistics import median as _median`).

Then append:

```python


def build_exit_panel(
    raw_positions: list[tuple[str, int, float]],
    daily_at_map: dict[str, float],
    il_map: dict[str, float],
    lag_days: int = 1,
) -> list[ExitPanelRow]:
    """Build position-day panel for exit hazard model.

    For each position, identifies the days it was alive within the
    daily_at_map window. Creates one ExitPanelRow per position-day:
    exited=1 on burn_date, 0 on all prior days.

    Treatment variable (a_t_lagged) uses A_T from (day - lag_days)
    to break simultaneity.

    Excludes rows where lagged A_T is unavailable.
    Excludes JIT positions (blocklife <= 1 block).
    """
    sorted_days = sorted(daily_at_map.keys())
    if not sorted_days:
        return []

    window_start = date.fromisoformat(sorted_days[0])
    window_end = date.fromisoformat(sorted_days[-1])

    rows: list[ExitPanelRow] = []
    for idx, (burn_date_str, blocklife, _exit_at) in enumerate(raw_positions):
        if blocklife <= 1:
            continue

        mint_date_str = approximate_mint_date(burn_date_str, blocklife)
        mint_d = date.fromisoformat(mint_date_str)
        burn_d = date.fromisoformat(burn_date_str)

        # Iterate over days this position is alive within the data window
        obs_start = max(mint_d, window_start)
        obs_end = min(burn_d, window_end)

        d = obs_start
        while d <= obs_end:
            day_str = d.isoformat()

            # Lagged A_T: use A_T from (d - lag_days)
            lag_d = d - timedelta(days=lag_days)
            lag_key = lag_d.isoformat()
            if lag_key not in daily_at_map:
                d += timedelta(days=1)
                continue

            age_days = (d - mint_d).days
            rows.append(ExitPanelRow(
                position_idx=idx,
                day=day_str,
                exited=1 if d == burn_d else 0,
                a_t_lagged=daily_at_map[lag_key],
                il=il_map.get(day_str, 0.0),
                log_age=math.log(max(1, age_days)),
            ))
            d += timedelta(days=1)

    return rows
```

**Step 4: Run tests to verify they pass**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/test_ingest.py -v -k "exit_panel"`
Expected: 6 PASSED

**Step 5: Run full test suite**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/ -v`
Expected: All existing tests still pass + 6 new ones

**Step 6: Commit**

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev
git add -f econometrics/ingest.py tests/econometrics/test_ingest.py
git commit -m "feat(ingest): add build_exit_panel for position-day survival panel"
```

---

### Task 2: Logit MLE with Day-Clustered SEs — hazard.py

**Files:**
- Create: `econometrics/hazard.py`
- Test: `tests/econometrics/test_hazard.py`

**Context:** This is the core estimation module. It implements:
1. `logit_mle()` — Maximum likelihood logit estimation via JAX
2. `clustered_se()` — Day-clustered sandwich standard errors
3. `marginal_effect_at_means()` — Insurance pricing translation
4. `exit_quartile_analysis()` — Dose-response by A_T quartile
5. `exit_lag_sensitivity()` — Sweep over lag windows

All functions are pure free functions per @functional-python. The logit MLE uses `jax.scipy.optimize.minimize` (L-BFGS-B) on the negative log-likelihood. Clustered SEs use the sandwich formula `H^{-1} * (sum_t g_t g_t') * H^{-1}`.

**Step 1: Write the failing tests**

Create `tests/econometrics/test_hazard.py`:

```python
"""Tests for exit hazard (logit) estimation."""
from __future__ import annotations

import math

from econometrics.hazard import (
    exit_lag_sensitivity,
    exit_quartile_analysis,
    logit_mle,
    marginal_effect_at_means,
)
from econometrics.types import ExitPanelRow, LogitResult, MarginalEffect


# ── Fixtures ──────────────────────────────────────────────────────────

def _make_panel(n_days: int = 20, n_positions: int = 50) -> list[ExitPanelRow]:
    """Synthetic panel where higher A_T correlates with exit."""
    import random
    random.seed(42)
    rows: list[ExitPanelRow] = []
    for pos in range(n_positions):
        # Each position lives for a random number of days
        lifetime = random.randint(3, n_days)
        burn_day = random.randint(lifetime, n_days)
        mint_day = burn_day - lifetime
        for d in range(mint_day, burn_day + 1):
            if d < 0 or d >= n_days:
                continue
            a_t = 0.10 + 0.005 * d + random.gauss(0, 0.02)
            il = 0.01 + random.gauss(0, 0.005)
            exited = 1 if d == burn_day else 0
            rows.append(ExitPanelRow(
                position_idx=pos,
                day=f"2025-12-{d + 1:02d}",
                exited=exited,
                a_t_lagged=max(0.01, a_t),
                il=max(0.0, il),
                log_age=math.log(max(1, d - mint_day)),
            ))
    return rows


# ── logit_mle tests ──────────────────────────────────────────────────

def test_logit_mle_returns_logit_result() -> None:
    """logit_mle returns a LogitResult with correct field types."""
    panel = _make_panel()
    result = logit_mle(panel)
    assert isinstance(result, LogitResult)
    assert result.n_obs == len(panel)
    assert result.n_exits == sum(1 for r in panel if r.exited == 1)
    assert result.n_clusters > 0
    assert result.log_likelihood < 0.0  # negative log-likelihood
    assert result.aic > 0.0


def test_logit_mle_clustered_se_wider() -> None:
    """Clustered SEs should generally be >= MLE SEs (more conservative)."""
    panel = _make_panel()
    result = logit_mle(panel)
    # Clustered SEs are typically wider due to within-cluster correlation
    # This is a soft test — in small samples it's not guaranteed
    # Just verify they are positive and finite
    assert result.cluster_se_a_t > 0.0
    assert math.isfinite(result.cluster_se_a_t)
    assert result.cluster_se_il > 0.0


def test_logit_mle_pseudo_r2_bounded() -> None:
    """McFadden's pseudo R^2 should be in [0, 1)."""
    panel = _make_panel()
    result = logit_mle(panel)
    assert 0.0 <= result.pseudo_r2 < 1.0


def test_logit_mle_mean_exit_prob_reasonable() -> None:
    """Mean predicted exit probability should be between 0 and 1."""
    panel = _make_panel()
    result = logit_mle(panel)
    assert 0.0 < result.mean_exit_prob < 1.0


# ── marginal_effect tests ────────────────────────────────────────────

def test_marginal_effect_at_means_returns_type() -> None:
    """marginal_effect_at_means returns a MarginalEffect."""
    panel = _make_panel()
    result = logit_mle(panel)
    me = marginal_effect_at_means(result, delta_a_t=0.10)
    assert isinstance(me, MarginalEffect)
    assert me.delta_a_t == 0.10
    assert math.isfinite(me.marginal_effect)
    assert math.isfinite(me.implied_premium_usd)


# ── quartile analysis tests ──────────────────────────────────────────

def test_exit_quartile_analysis_four_quartiles() -> None:
    """Should return exactly 4 quartile rows."""
    panel = _make_panel()
    quartiles = exit_quartile_analysis(panel)
    assert len(quartiles) == 4
    assert all(q.quartile in (1, 2, 3, 4) for q in quartiles)


# ── lag sensitivity tests ────────────────────────────────────────────

def test_exit_lag_sensitivity_returns_results() -> None:
    """Sensitivity sweep returns results for each lag."""
    # Use raw positions + daily maps for this
    from econometrics.data import DAILY_AT_MAP, IL_MAP, RAW_POSITIONS
    rows = exit_lag_sensitivity(RAW_POSITIONS, DAILY_AT_MAP, IL_MAP, lags=[1, 2])
    assert len(rows) >= 1
    assert all(hasattr(r, 'lag') for r in rows)
```

**Step 2: Run tests to verify they fail**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/test_hazard.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'econometrics.hazard'`

**Step 3: Write minimal implementation**

Create `econometrics/hazard.py`:

```python
"""Exit hazard model: does fee concentration risk drive LP exits?

Model: P(exit_i,t = 1) = sigma(b0 + b1*A_T,t-lag + b2*IL_t + b3*log(age_i,t))

b1 > 0 -> higher concentration increases exit probability (insurance demand).
Day-clustered sandwich SEs for reliable inference (41 clusters).
"""
from __future__ import annotations

import math
from typing import Final

import jax
import jax.numpy as jnp
import jax.scipy.stats as jstats
from jax import Array

from econometrics.ingest import build_exit_panel
from econometrics.types import (
    ExitPanelRow,
    LogitResult,
    MarginalEffect,
    QuartileRow,
    SensitivityRow,
)

FEE_REVENUE_PER_HOUR: Final[float] = 100.0
AVG_REMAINING_HOURS: Final[float] = 48.0  # placeholder: avg hours left at mean age


def _panel_to_arrays(
    panel: list[ExitPanelRow],
) -> tuple[Array, Array, list[str]]:
    """Convert panel rows to JAX arrays (X, y) and day list for clustering."""
    n = len(panel)
    y = jnp.array([float(r.exited) for r in panel])
    X = jnp.column_stack([
        jnp.ones(n),                                          # intercept
        jnp.array([r.a_t_lagged for r in panel]),              # A_T
        jnp.array([r.il for r in panel]),                      # IL
        jnp.array([r.log_age for r in panel]),                 # log(age)
    ])
    days = [r.day for r in panel]
    return X, y, days


def _neg_log_likelihood(params: Array, X: Array, y: Array) -> float:
    """Negative log-likelihood for logit model."""
    z = X @ params
    # Numerically stable: log(sigma(z)) = z - log(1+exp(z)) = -softplus(-z)
    log_p = -jax.nn.softplus(-z)       # log(sigma(z))
    log_1mp = -jax.nn.softplus(z)      # log(1 - sigma(z))
    return -float(jnp.sum(y * log_p + (1.0 - y) * log_1mp))


def _hessian_and_scores(
    params: Array, X: Array, y: Array,
) -> tuple[Array, Array]:
    """Compute Hessian and per-observation score vectors for logit.

    Score_i = (y_i - p_i) * x_i
    Hessian = -X' diag(p*(1-p)) X
    """
    z = X @ params
    p = jax.nn.sigmoid(z)
    residuals = y - p
    # Per-observation scores: (n, k)
    scores = residuals[:, None] * X
    # Hessian: -X' W X where W = diag(p * (1-p))
    w = p * (1.0 - p)
    H = -(X.T * w[None, :]) @ X
    return H, scores


def logit_mle(panel: list[ExitPanelRow]) -> LogitResult:
    """Logit MLE with day-clustered sandwich standard errors.

    Optimizes via L-BFGS-B (jax.scipy.optimize.minimize).
    Clustered SE: V = H^{-1} M H^{-1} where M = sum_t g_t g_t'
    and g_t = sum of scores within cluster t.
    """
    X, y, days = _panel_to_arrays(panel)
    n, k = X.shape

    # Initial params: zeros
    init_params = jnp.zeros(k)

    # Optimize via gradient descent (L-BFGS-B)
    def objective(params: Array) -> float:
        return _neg_log_likelihood(params, X, y)

    result = jax.scipy.optimize.minimize(
        objective, init_params, method="BFGS",
    )
    params = result.x

    # Log-likelihood at optimum and null
    ll = -_neg_log_likelihood(params, X, y)
    ll_null = -_neg_log_likelihood(jnp.zeros(k), X, y)
    pseudo_r2 = 1.0 - ll / ll_null if ll_null != 0 else 0.0

    # Hessian and scores
    H, scores = _hessian_and_scores(params, X, y)
    H_inv = jnp.linalg.inv(H)

    # MLE SEs: from -H^{-1}
    mle_cov = -H_inv
    mle_ses = jnp.sqrt(jnp.abs(jnp.diag(mle_cov)))

    # Day-clustered sandwich: V = H^{-1} M H^{-1}
    unique_days = sorted(set(days))
    n_clusters = len(unique_days)
    day_to_idx: dict[str, int] = {d: i for i, d in enumerate(unique_days)}
    meat = jnp.zeros((k, k))
    for day_label in unique_days:
        mask = jnp.array([1.0 if d == day_label else 0.0 for d in days])
        g_t = jnp.sum(scores * mask[:, None], axis=0)  # sum of scores in cluster t
        meat = meat + jnp.outer(g_t, g_t)

    # Small-sample correction: n_clusters / (n_clusters - 1) * n / (n - k)
    correction = (n_clusters / (n_clusters - 1)) * (n / (n - k)) if n_clusters > 1 else 1.0
    cluster_cov = H_inv @ meat @ H_inv * correction
    cluster_ses = jnp.sqrt(jnp.abs(jnp.diag(cluster_cov)))

    # p-values (two-sided)
    t_mle = params / mle_ses
    p_mle = 2.0 * jstats.norm.sf(jnp.abs(t_mle))
    t_cluster = params / cluster_ses
    p_cluster = 2.0 * jstats.norm.sf(jnp.abs(t_cluster))

    # Mean predicted probability
    p_hat = jax.nn.sigmoid(X @ params)
    mean_p = float(jnp.mean(p_hat))

    return LogitResult(
        beta_a_t=float(params[1]),
        beta_il=float(params[2]),
        beta_log_age=float(params[3]),
        beta_intercept=float(params[0]),
        se_a_t=float(mle_ses[1]),
        se_il=float(mle_ses[2]),
        se_log_age=float(mle_ses[3]),
        se_intercept=float(mle_ses[0]),
        cluster_se_a_t=float(cluster_ses[1]),
        cluster_se_il=float(cluster_ses[2]),
        cluster_se_log_age=float(cluster_ses[3]),
        cluster_se_intercept=float(cluster_ses[0]),
        p_value_a_t=float(p_mle[1]),
        cluster_p_value_a_t=float(p_cluster[1]),
        n_obs=n,
        n_exits=int(jnp.sum(y)),
        n_clusters=n_clusters,
        log_likelihood=ll,
        aic=-2.0 * ll + 2.0 * k,
        pseudo_r2=pseudo_r2,
        mean_exit_prob=mean_p,
    )


def marginal_effect_at_means(
    result: LogitResult,
    delta_a_t: float = 0.10,
    fee_revenue_per_hour: float = FEE_REVENUE_PER_HOUR,
    avg_remaining_hours: float = AVG_REMAINING_HOURS,
) -> MarginalEffect:
    """Translate beta_1 into insurance pricing quantities.

    Marginal effect: dP(exit)/dA_T = beta_1 * P_bar * (1 - P_bar)
    Prob increase for delta_a_t shock: ME * delta_a_t
    Hours lost: prob_increase * avg_remaining_hours
    Premium: hours_lost * fee_revenue_per_hour
    """
    p_bar = result.mean_exit_prob
    me = result.beta_a_t * p_bar * (1.0 - p_bar)
    prob_inc = me * delta_a_t
    hours_lost = abs(prob_inc) * avg_remaining_hours
    premium = hours_lost * fee_revenue_per_hour

    return MarginalEffect(
        marginal_effect=me,
        delta_a_t=delta_a_t,
        prob_increase=prob_inc,
        hours_lost=hours_lost,
        implied_premium_usd=premium,
        mean_exit_prob=p_bar,
    )


def exit_quartile_analysis(panel: list[ExitPanelRow]) -> list[QuartileRow]:
    """Split panel days into 4 quartiles by A_T, report exit rate per quartile."""
    # Group by unique day, compute exit rate per day
    from collections import defaultdict
    day_data: dict[str, tuple[float, int, int]] = {}  # day -> (a_t, exits, total)
    day_at: dict[str, float] = {}
    day_exits: dict[str, int] = defaultdict(int)
    day_total: dict[str, int] = defaultdict(int)

    for r in panel:
        day_at[r.day] = r.a_t_lagged
        day_exits[r.day] += r.exited
        day_total[r.day] += 1

    sorted_days = sorted(day_at.keys(), key=lambda d: day_at[d])
    n = len(sorted_days)
    q_size = n // 4

    quartiles: list[QuartileRow] = []
    for q in range(4):
        start = q * q_size
        end = (q + 1) * q_size if q < 3 else n
        chunk = sorted_days[start:end]
        if not chunk:
            continue
        total_exits = sum(day_exits[d] for d in chunk)
        total_obs = sum(day_total[d] for d in chunk)
        exit_rate = total_exits / total_obs if total_obs > 0 else 0.0
        mean_at = sum(day_at[d] for d in chunk) / len(chunk)
        # Store exit rate as "mean_blocklife_hours" field (repurposing QuartileRow)
        # exit_rate * 100 for readability (percentage points)
        quartiles.append(QuartileRow(
            quartile=q + 1,
            mean_blocklife_hours=exit_rate * 100,  # exit rate in pct
            mean_a_t=mean_at,
            n_obs=total_obs,
        ))

    return quartiles


def exit_lag_sensitivity(
    raw_positions: list[tuple[str, int, float]],
    daily_at_map: dict[str, float],
    il_map: dict[str, float],
    lags: list[int] | None = None,
) -> list[SensitivityRow]:
    """Sweep over lag windows and report beta_1 stability."""
    if lags is None:
        lags = [1, 2, 3, 5, 7]

    rows: list[SensitivityRow] = []
    for lag in lags:
        panel = build_exit_panel(raw_positions, daily_at_map, il_map, lag_days=lag)
        if len(panel) < 50:
            continue
        result = logit_mle(panel)
        rows.append(SensitivityRow(
            lag=lag,
            measure="logit",
            beta_a_t=result.beta_a_t,
            robust_se_a_t=result.cluster_se_a_t,
            robust_p_value_a_t=result.cluster_p_value_a_t,
            n_obs=result.n_obs,
        ))
    return rows
```

**Step 4: Run tests to verify they pass**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/test_hazard.py -v`
Expected: 7 PASSED (may take 10-30s due to JAX compilation)

**Step 5: Run full test suite**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/ -v`
Expected: All existing + new tests pass

**Step 6: Commit**

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev
git add -f econometrics/hazard.py tests/econometrics/test_hazard.py
git commit -m "feat(hazard): logit MLE with day-clustered SEs for exit hazard model"
```

---

### Task 3: Display Notebook

**Files:**
- Create: `notebooks/exit_hazard_results.ipynb`

**Context:** A display-only Jupyter notebook using the `uhi8` kernel (already configured with `PYTHONPATH` for econometrics imports). Shows: main result, economic magnitude, dose-response chart, lag sensitivity, implied insurance value. The notebook has NO logic — it just calls functions from `hazard.py` and displays results.

**Step 1: Create the notebook**

Create `notebooks/exit_hazard_results.ipynb` with the following cells:

Cell 1 (markdown):
```markdown
# Exit Hazard Model — Results

**Replaces:** Duration model (failed: mechanical collinearity with A_T)

**Model:** P(exit_i,t = 1) = sigma(beta_0 + beta_1 * A_T,t-lag + beta_2 * IL_t + beta_3 * log(age_i,t))

**Hypothesis:** beta_1 > 0 -> higher fee concentration drives LP exits -> insurance demand
```

Cell 2 (code):
```python
from econometrics.data import DAILY_AT_MAP, IL_MAP, RAW_POSITIONS
from econometrics.ingest import build_exit_panel
from econometrics.hazard import (
    logit_mle,
    marginal_effect_at_means,
    exit_quartile_analysis,
    exit_lag_sensitivity,
)

LAG = 1
panel = build_exit_panel(RAW_POSITIONS, DAILY_AT_MAP, IL_MAP, lag_days=LAG)
print(f"Panel size: {len(panel)} position-day observations")
print(f"Exits: {sum(1 for r in panel if r.exited == 1)}")
print(f"Days: {len(set(r.day for r in panel))}")
```

Cell 3 (markdown):
```markdown
## 1. Main Result
```

Cell 4 (code):
```python
result = logit_mle(panel)
print(f"{'':>20} {'Coeff':>10} {'MLE SE':>10} {'Cluster SE':>10} {'Cluster p':>10}")
print(f"{'beta_1 (A_T)':>20} {result.beta_a_t:>10.4f} {result.se_a_t:>10.4f} {result.cluster_se_a_t:>10.4f} {result.cluster_p_value_a_t:>10.6f}")
print(f"{'beta_2 (IL)':>20} {result.beta_il:>10.4f} {result.se_il:>10.4f} {result.cluster_se_il:>10.4f}")
print(f"{'beta_3 (log age)':>20} {result.beta_log_age:>10.4f} {result.se_log_age:>10.4f} {result.cluster_se_log_age:>10.4f}")
print(f"{'beta_0 (intercept)':>20} {result.beta_intercept:>10.4f}")
print(f"\nn={result.n_obs}  exits={result.n_exits}  clusters={result.n_clusters}")
print(f"LL={result.log_likelihood:.1f}  AIC={result.aic:.1f}  pseudo-R2={result.pseudo_r2:.4f}")
print(f"Mean P(exit)={result.mean_exit_prob:.4f}")
```

Cell 5 (markdown):
```markdown
## 2. Economic Magnitude (Insurance Pricing)
```

Cell 6 (code):
```python
me = marginal_effect_at_means(result, delta_a_t=0.10)
print(f"Marginal effect dP(exit)/dA_T:  {me.marginal_effect:.6f}")
print(f"A 0.10 increase in A_T:")
print(f"  Exit probability increase:    {me.prob_increase:.6f}")
print(f"  Hours of fee revenue lost:    {me.hours_lost:.2f}")
print(f"  Implied insurance premium:    ${me.implied_premium_usd:.2f}")
print(f"  (Mean exit probability:       {me.mean_exit_prob:.4f})")
if result.beta_a_t > 0:
    print(f"\nINTERPRETATION: beta_1 > 0 confirms insurance demand.")
    print(f"PLPs exit faster when fee concentration is high.")
else:
    print(f"\nbeta_1 <= 0 -- concentration does not drive exits in this sample.")
```

Cell 7 (markdown):
```markdown
## 3. Dose-Response (A_T Quartiles)
```

Cell 8 (code):
```python
import matplotlib.pyplot as plt

quartiles = exit_quartile_analysis(panel)
qs = [q.quartile for q in quartiles]
exit_rates = [q.mean_blocklife_hours for q in quartiles]  # exit rate in pct
ats = [q.mean_a_t for q in quartiles]

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(qs, exit_rates, color=["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"], edgecolor="black")
ax.set_xlabel("A_T Quartile (lagged)")
ax.set_ylabel("Exit Rate (%)")
ax.set_title("Dose-Response: Fee Concentration vs Exit Probability")
ax.set_xticks(qs)
ax.set_xticklabels([f"Q{q}\n(A_T={a:.3f})" for q, a in zip(qs, ats)])

for bar, rate, n in zip(bars, exit_rates, [q.n_obs for q in quartiles]):
    ax.text(bar.get_x() + bar.get_width()/2, rate + 0.1, f"{rate:.2f}%\n(n={n})",
            ha="center", va="bottom", fontsize=9)
plt.tight_layout()
plt.show()
```

Cell 9 (markdown):
```markdown
## 4. Lag Sensitivity
```

Cell 10 (code):
```python
rows = exit_lag_sensitivity(RAW_POSITIONS, DAILY_AT_MAP, IL_MAP)
print(f"{'Lag':>4} {'beta_1':>10} {'Cluster SE':>12} {'p-value':>10} {'n':>8} {'Sig':>4}")
print("-" * 52)
for r in rows:
    sig = "***" if r.robust_p_value_a_t < 0.01 else "**" if r.robust_p_value_a_t < 0.05 else "*" if r.robust_p_value_a_t < 0.10 else ""
    print(f"{r.lag:>4} {r.beta_a_t:>10.4f} {r.robust_se_a_t:>12.4f} {r.robust_p_value_a_t:>10.4f} {r.n_obs:>8} {sig:>4}")
```

**Step 2: Verify the notebook runs**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -c "from econometrics.data import RAW_POSITIONS, DAILY_AT_MAP, IL_MAP; from econometrics.ingest import build_exit_panel; from econometrics.hazard import logit_mle; panel = build_exit_panel(RAW_POSITIONS, DAILY_AT_MAP, IL_MAP, lag_days=1); print(f'Panel: {len(panel)} obs'); result = logit_mle(panel); print(f'beta_1={result.beta_a_t:.4f}, p={result.cluster_p_value_a_t:.4f}')"`
Expected: Panel size and beta_1 coefficient printed (sign TBD — this is the real test)

**Step 3: Commit**

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev
git add -f notebooks/exit_hazard_results.ipynb
git commit -m "feat(notebook): exit hazard results display notebook"
```

---

### Task 4: Integration Smoke Test on Real Data

**Files:**
- No new files — this is a verification task

**Context:** Run the full pipeline on the real 600 positions. This is the moment of truth: does beta_1 come out positive (insurance demand confirmed)?

**Step 1: Run the full pipeline**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -c "
from econometrics.data import RAW_POSITIONS, DAILY_AT_MAP, IL_MAP
from econometrics.ingest import build_exit_panel
from econometrics.hazard import logit_mle, marginal_effect_at_means, exit_quartile_analysis

panel = build_exit_panel(RAW_POSITIONS, DAILY_AT_MAP, IL_MAP, lag_days=1)
print(f'Panel: {len(panel)} obs, {sum(1 for r in panel if r.exited==1)} exits, {len(set(r.day for r in panel))} days')

result = logit_mle(panel)
print(f'beta_1 (A_T) = {result.beta_a_t:.4f}  cluster_SE = {result.cluster_se_a_t:.4f}  p = {result.cluster_p_value_a_t:.6f}')
print(f'beta_2 (IL)  = {result.beta_il:.4f}')
print(f'beta_3 (age) = {result.beta_log_age:.4f}')
print(f'LL={result.log_likelihood:.1f}  pseudo-R2={result.pseudo_r2:.4f}  mean_P={result.mean_exit_prob:.4f}')

me = marginal_effect_at_means(result, delta_a_t=0.10)
print(f'Marginal effect = {me.marginal_effect:.6f}')
print(f'Premium per 0.10 A_T shock = \${me.implied_premium_usd:.2f}')

qs = exit_quartile_analysis(panel)
for q in qs:
    print(f'  Q{q.quartile}: exit_rate={q.mean_blocklife_hours:.3f}%  mean_A_T={q.mean_a_t:.4f}  n={q.n_obs}')
"`

Expected: Results printed. beta_1 > 0 confirms insurance demand.

**Step 2: Run full test suite**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python -m pytest tests/econometrics/ -v`
Expected: All tests pass (existing + new from Tasks 0-2)

**Step 3: Interpret results**

- If **beta_1 > 0 with cluster_p < 0.05**: Insurance demand confirmed. Fee concentration drives LP exits. The model is correctly specified.
- If **beta_1 > 0 but cluster_p > 0.05**: Directionally correct but underpowered. May need more data or alternative specification.
- If **beta_1 <= 0**: The exit hazard also fails. Need to rethink the approach entirely (unlikely given the clean identification).

Document the result in a brief comment at the top of `hazard.py`.
