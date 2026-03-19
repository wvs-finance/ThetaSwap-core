# Fee Concentration Duration Model Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the duration model from `specs/econometrics/lp-insurance-demand.tex` — prove fee concentration risk shortens LP position lifetimes and quantify insurance demand.

**Architecture:** Five Python modules (@functional-python: frozen dataclasses, free pure functions, full typing) with one display-only Jupyter notebook. All data hardcoded from prior Dune extractions (600 positions, 41 days of daily A_T). No runtime Dune calls. JAX 0.9.1 for linear algebra.

**Tech Stack:** Python 3.14, JAX 0.9.1, pytest 9.0.2, Jupyter (uhi8 kernel), matplotlib

**Important:**
- `.gitignore` has `*.py` rule — always use `git add -f` for Python files
- Activate venv: `source uhi8/bin/activate`
- Run all commands from `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev`
- BLOCKS_PER_DAY = 7200 (~12s per block)

---

### Task 0: Data Extraction Module

**Files:**
- Create: `econometrics/data.py`
- Test: `tests/econometrics/test_data.py`

**Context:** Currently `run_duration.py` has 600 hardcoded position tuples and an IL map. We extract these into a dedicated data module so all other modules import from one place. Also extract the daily A_T map (unique burn_date -> A_T pairs from Q4v2).

**Step 1: Write the failing test**

Create `tests/__init__.py` and `tests/econometrics/__init__.py` (empty), then:

```python
# tests/econometrics/test_data.py
"""Tests for econometrics.data — hardcoded Dune extraction data."""
from __future__ import annotations

from econometrics.data import DAILY_AT_MAP, IL_MAP, RAW_POSITIONS


def test_raw_positions_count() -> None:
    assert len(RAW_POSITIONS) == 600


def test_daily_at_map_is_complete() -> None:
    """41 unique days in the Q4v2 data."""
    assert len(DAILY_AT_MAP) == 41


def test_daily_at_map_values_in_range() -> None:
    """A_T should be between 0 and 1."""
    for day, at in DAILY_AT_MAP.items():
        assert 0.0 < at < 1.0, f"A_T out of range on {day}: {at}"


def test_il_map_covers_daily_at_dates() -> None:
    """IL map should cover most daily A_T dates."""
    overlap = set(IL_MAP.keys()) & set(DAILY_AT_MAP.keys())
    assert len(overlap) >= 35  # at least 35 of 41 days covered


def test_raw_positions_blocklife_positive() -> None:
    for _, bl, _ in RAW_POSITIONS:
        assert bl > 1, f"blocklife must be > 1 (JIT filtered)"
```

**Step 2: Run test to verify it fails**

Run: `source uhi8/bin/activate && python -m pytest tests/econometrics/test_data.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'econometrics.data'`

**Step 3: Write minimal implementation**

```python
# econometrics/data.py
"""Hardcoded data from Dune MCP extractions (Q4v2 + Q5).

Single source of truth. All other modules import from here.
No runtime Dune calls — data collected during prior sessions.
"""
from __future__ import annotations

from typing import Final

# ── Q5 IL proxy: day -> il_proxy ──
IL_MAP: Final[dict[str, float]] = {
    # [copy the entire IL_MAP dict from run_duration.py]
}

# ── Daily pool-level A_T: day -> a_t ──
# Extracted from Q4v2 unique (burn_date, daily_a_t) pairs.
DAILY_AT_MAP: Final[dict[str, float]] = {
    # [extract unique (date, at) pairs from RAW_POSITIONS]
}

# ── Q4v2 position data: (burn_date, blocklife, exit_day_a_t) ──
RAW_POSITIONS: Final[list[tuple[str, int, float]]] = [
    # [copy the entire RAW_POSITIONS list from run_duration.py]
]
```

Copy `IL_MAP` from `run_duration.py:12-27`. Copy `RAW_POSITIONS` from `run_duration.py:31-250`. Build `DAILY_AT_MAP` by extracting unique `{d: at for d, _, at in RAW_POSITIONS}`.

**Step 4: Run test to verify it passes**

Run: `source uhi8/bin/activate && python -m pytest tests/econometrics/test_data.py -v`
Expected: 5 passed

**Step 5: Commit**

```bash
git add -f econometrics/data.py tests/__init__.py tests/econometrics/__init__.py tests/econometrics/test_data.py
git commit -m "feat(data): extract hardcoded Dune data into dedicated module"
```

---

### Task 1: Updated Types

**Files:**
- Modify: `econometrics/types.py`
- Test: `tests/econometrics/test_types.py`

**Context:** Add new frozen dataclasses for the lagged-max model: `LaggedPositionRow`, `RobustDurationResult`, `SensitivityRow`, `QuartileRow`. Keep existing types unchanged.

**Step 1: Write the failing test**

```python
# tests/econometrics/test_types.py
"""Tests for econometrics.types — frozen dataclasses."""
from __future__ import annotations

from econometrics.types import (
    LaggedPositionRow,
    QuartileRow,
    RobustDurationResult,
    SensitivityRow,
)


def test_lagged_position_row_frozen() -> None:
    row = LaggedPositionRow(
        burn_date="2026-01-01",
        mint_date="2025-12-25",
        blocklife=50400,
        max_a_t=0.22,
        mean_a_t=0.15,
        median_a_t=0.14,
        il_proxy=0.01,
    )
    assert row.max_a_t == 0.22
    assert row.mint_date == "2025-12-25"
    # Frozen — should raise
    try:
        row.max_a_t = 0.5  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass


def test_robust_duration_result_has_robust_fields() -> None:
    r = RobustDurationResult(
        beta_a_t=-2.0, se_a_t=1.0, p_value_a_t=0.05,
        robust_se_a_t=1.2, robust_p_value_a_t=0.09,
        beta_il=1.0, se_il=0.5, p_value_il=0.05,
        robust_se_il=0.6, robust_p_value_il=0.09,
        beta_intercept=8.0,
        n_obs=500, r_squared=0.05,
        mean_blocklife=30000.0, mean_blocklife_hours=100.0,
    )
    assert r.robust_se_a_t == 1.2
    assert r.robust_p_value_a_t == 0.09


def test_sensitivity_row() -> None:
    s = SensitivityRow(lag=5, measure="max", beta_a_t=-1.5, robust_se_a_t=0.8, robust_p_value_a_t=0.06, n_obs=400)
    assert s.lag == 5
    assert s.measure == "max"


def test_quartile_row() -> None:
    q = QuartileRow(quartile=1, mean_blocklife_hours=200.0, mean_a_t=0.08, n_obs=150)
    assert q.quartile == 1
```

**Step 2: Run test to verify it fails**

Run: `source uhi8/bin/activate && python -m pytest tests/econometrics/test_types.py -v`
Expected: FAIL with `ImportError: cannot import name 'LaggedPositionRow'`

**Step 3: Write minimal implementation**

Add to `econometrics/types.py` (after existing types):

```python
@dataclass(frozen=True)
class LaggedPositionRow:
    """Position with lagged A_T treatment variables."""
    burn_date: str
    mint_date: str
    blocklife: int
    max_a_t: float
    mean_a_t: float
    median_a_t: float
    il_proxy: float


@dataclass(frozen=True)
class RobustDurationResult:
    """Duration model with both OLS and HC1 robust standard errors."""
    beta_a_t: float
    se_a_t: float
    p_value_a_t: float
    robust_se_a_t: float
    robust_p_value_a_t: float
    beta_il: float
    se_il: float
    p_value_il: float
    robust_se_il: float
    robust_p_value_il: float
    beta_intercept: float
    n_obs: int
    r_squared: float
    mean_blocklife: float
    mean_blocklife_hours: float


@dataclass(frozen=True)
class SensitivityRow:
    """One row of the lag/measure sensitivity sweep."""
    lag: int
    measure: str  # "max", "mean", "median"
    beta_a_t: float
    robust_se_a_t: float
    robust_p_value_a_t: float
    n_obs: int


@dataclass(frozen=True)
class QuartileRow:
    """Dose-response: mean blocklife per A_T quartile."""
    quartile: int  # 1-4
    mean_blocklife_hours: float
    mean_a_t: float
    n_obs: int
```

**Step 4: Run test to verify it passes**

Run: `source uhi8/bin/activate && python -m pytest tests/econometrics/test_types.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add -f econometrics/types.py tests/econometrics/test_types.py
git commit -m "feat(types): add LaggedPositionRow, RobustDurationResult, SensitivityRow, QuartileRow"
```

---

### Task 2: Lagged Treatment Computation

**Files:**
- Modify: `econometrics/ingest.py`
- Test: `tests/econometrics/test_ingest.py`

**Context:** Given a position's burn_date and blocklife, approximate the mint_date. Then compute max/mean/median A_T over [mint_date, burn_date - lag] from the daily A_T map. Positions whose mint_date falls before the earliest A_T data are excluded.

**Step 1: Write the failing test**

```python
# tests/econometrics/test_ingest.py
"""Tests for econometrics.ingest — lagged treatment computation."""
from __future__ import annotations

from econometrics.ingest import (
    approximate_mint_date,
    build_lagged_positions,
    compute_lagged_treatment,
)


SAMPLE_DAILY_AT: dict[str, float] = {
    "2025-12-20": 0.10,
    "2025-12-21": 0.15,
    "2025-12-22": 0.20,
    "2025-12-23": 0.12,
    "2025-12-24": 0.18,
    "2025-12-25": 0.25,
    "2025-12-26": 0.11,
    "2025-12-27": 0.14,
}

SAMPLE_IL: dict[str, float] = {
    "2025-12-27": 0.01,
}

BLOCKS_PER_DAY = 7200


def test_approximate_mint_date() -> None:
    # 7 days * 7200 blocks/day = 50400 blocks
    result = approximate_mint_date("2025-12-27", 50400)
    assert result == "2025-12-20"


def test_approximate_mint_date_short_position() -> None:
    # 1 day = 7200 blocks
    result = approximate_mint_date("2025-12-27", 7200)
    assert result == "2025-12-26"


def test_compute_lagged_treatment_lag_0() -> None:
    # mint=Dec 20, burn=Dec 27, lag=0 -> range [Dec 20, Dec 27]
    max_at, mean_at, median_at = compute_lagged_treatment(
        SAMPLE_DAILY_AT, "2025-12-20", "2025-12-27", lag_days=0,
    )
    assert max_at == 0.25  # Dec 25
    assert abs(mean_at - sum(SAMPLE_DAILY_AT.values()) / 8) < 1e-6


def test_compute_lagged_treatment_lag_2() -> None:
    # mint=Dec 20, burn=Dec 27, lag=2 -> range [Dec 20, Dec 25]
    max_at, mean_at, median_at = compute_lagged_treatment(
        SAMPLE_DAILY_AT, "2025-12-20", "2025-12-27", lag_days=2,
    )
    assert max_at == 0.25  # Dec 25 is still included (burn-2 = Dec 25)
    # range is Dec 20-25 = 6 values: 0.10, 0.15, 0.20, 0.12, 0.18, 0.25
    assert abs(mean_at - (0.10 + 0.15 + 0.20 + 0.12 + 0.18 + 0.25) / 6) < 1e-6


def test_compute_lagged_treatment_lag_5() -> None:
    # mint=Dec 20, burn=Dec 27, lag=5 -> range [Dec 20, Dec 22]
    max_at, mean_at, median_at = compute_lagged_treatment(
        SAMPLE_DAILY_AT, "2025-12-20", "2025-12-27", lag_days=5,
    )
    assert max_at == 0.20  # Dec 22
    # range is Dec 20-22 = 3 values: 0.10, 0.15, 0.20
    assert abs(median_at - 0.15) < 1e-6


def test_compute_lagged_treatment_empty_range_returns_none() -> None:
    # lag exceeds position lifetime -> no data
    result = compute_lagged_treatment(
        SAMPLE_DAILY_AT, "2025-12-26", "2025-12-27", lag_days=5,
    )
    assert result is None


def test_build_lagged_positions() -> None:
    raw = [
        ("2025-12-27", 50400, 0.14),  # mint ~Dec 20, good coverage
    ]
    positions = build_lagged_positions(raw, SAMPLE_DAILY_AT, SAMPLE_IL, lag_days=2)
    assert len(positions) == 1
    assert positions[0].mint_date == "2025-12-20"
    assert positions[0].il_proxy == 0.01


def test_build_lagged_positions_excludes_short_coverage() -> None:
    raw = [
        ("2025-12-21", 7200, 0.15),  # mint ~Dec 20, only 1 day before burn-2 = nothing
    ]
    positions = build_lagged_positions(raw, SAMPLE_DAILY_AT, SAMPLE_IL, lag_days=2)
    # mint=Dec 20, burn-2=Dec 19 -> range [Dec 20, Dec 19] -> empty -> excluded
    assert len(positions) == 0
```

**Step 2: Run test to verify it fails**

Run: `source uhi8/bin/activate && python -m pytest tests/econometrics/test_ingest.py -v`
Expected: FAIL with `ImportError: cannot import name 'approximate_mint_date'`

**Step 3: Write minimal implementation**

Add to `econometrics/ingest.py`:

```python
from datetime import date, timedelta
from statistics import median as _median

BLOCKS_PER_DAY: float = 7200.0


def approximate_mint_date(burn_date: str, blocklife: int) -> str:
    """Approximate mint date from burn date and blocklife."""
    burn = date.fromisoformat(burn_date)
    days = int(blocklife / BLOCKS_PER_DAY)
    mint = burn - timedelta(days=days)
    return mint.isoformat()


def compute_lagged_treatment(
    daily_at_map: dict[str, float],
    mint_date: str,
    burn_date: str,
    lag_days: int,
) -> tuple[float, float, float] | None:
    """Compute max/mean/median A_T over [mint_date, burn_date - lag].

    Returns None if the date range yields no data points.
    """
    mint = date.fromisoformat(mint_date)
    cutoff = date.fromisoformat(burn_date) - timedelta(days=lag_days)
    if cutoff < mint:
        return None
    values: list[float] = []
    d = mint
    while d <= cutoff:
        key = d.isoformat()
        if key in daily_at_map:
            values.append(daily_at_map[key])
        d += timedelta(days=1)
    if not values:
        return None
    return max(values), sum(values) / len(values), _median(values)


def build_lagged_positions(
    raw_positions: list[tuple[str, int, float]],
    daily_at_map: dict[str, float],
    il_map: dict[str, float],
    lag_days: int,
) -> list[LaggedPositionRow]:
    """Build LaggedPositionRow list from raw data + daily A_T series."""
    from econometrics.types import LaggedPositionRow

    result: list[LaggedPositionRow] = []
    for burn_date, blocklife, _exit_at in raw_positions:
        if blocklife <= 1:
            continue
        mint_date = approximate_mint_date(burn_date, blocklife)
        treatment = compute_lagged_treatment(daily_at_map, mint_date, burn_date, lag_days)
        if treatment is None:
            continue
        max_at, mean_at, median_at = treatment
        result.append(LaggedPositionRow(
            burn_date=burn_date,
            mint_date=mint_date,
            blocklife=blocklife,
            max_a_t=max_at,
            mean_a_t=mean_at,
            median_a_t=median_at,
            il_proxy=il_map.get(burn_date, 0.0),
        ))
    return result
```

**Step 4: Run test to verify it passes**

Run: `source uhi8/bin/activate && python -m pytest tests/econometrics/test_ingest.py -v`
Expected: 7 passed

**Step 5: Commit**

```bash
git add -f econometrics/ingest.py tests/econometrics/test_ingest.py
git commit -m "feat(ingest): add lagged treatment computation (mint approx, max/mean/median A_T)"
```

---

### Task 3: Duration Model with HC1 Robust SEs

**Files:**
- Modify: `econometrics/duration.py`
- Test: `tests/econometrics/test_duration.py`

**Context:** Update the existing OLS duration model to also compute HC1 heteroskedasticity-robust standard errors. Add sensitivity sweep, quartile analysis, nested models, and economic magnitude functions.

**Step 1: Write the failing test**

```python
# tests/econometrics/test_duration.py
"""Tests for econometrics.duration — OLS + HC1 robust SEs."""
from __future__ import annotations

from econometrics.duration import (
    duration_model_robust,
    economic_magnitude,
    nested_models,
    quartile_analysis,
    sensitivity_sweep,
)
from econometrics.types import LaggedPositionRow


def _make_positions(n: int = 100) -> list[LaggedPositionRow]:
    """Synthetic data: higher max_a_t -> shorter blocklife."""
    import random
    random.seed(42)
    positions = []
    for i in range(n):
        a_t = 0.05 + (i / n) * 0.20  # 0.05 to 0.25
        # log(bl) = 10 - 5*a_t + noise
        noise = random.gauss(0, 0.5)
        log_bl = 10.0 - 5.0 * a_t + noise
        bl = max(2, int(2.718 ** log_bl))
        positions.append(LaggedPositionRow(
            burn_date=f"2026-01-{(i % 28) + 1:02d}",
            mint_date=f"2025-12-{(i % 28) + 1:02d}",
            blocklife=bl,
            max_a_t=a_t,
            mean_a_t=a_t * 0.8,
            median_a_t=a_t * 0.85,
            il_proxy=random.gauss(0.01, 0.005),
        ))
    return positions


def test_duration_model_robust_returns_result() -> None:
    positions = _make_positions()
    result = duration_model_robust(positions, measure="max")
    assert result.n_obs == 100
    assert result.beta_a_t < 0  # negative effect by construction
    assert result.robust_se_a_t > 0
    assert result.robust_p_value_a_t >= 0


def test_robust_se_differs_from_ols_se() -> None:
    positions = _make_positions()
    result = duration_model_robust(positions, measure="max")
    # Robust and OLS SEs should differ (heteroskedasticity present)
    assert result.se_a_t != result.robust_se_a_t


def test_economic_magnitude() -> None:
    positions = _make_positions()
    result = duration_model_robust(positions, measure="max")
    mag = economic_magnitude(result, delta_a_t=0.10)
    assert "factor" in mag
    assert "hours_shortened" in mag
    assert mag["factor"] < 1.0  # shortens (beta < 0)


def test_quartile_analysis() -> None:
    positions = _make_positions()
    quartiles = quartile_analysis(positions, measure="max")
    assert len(quartiles) == 4
    assert quartiles[0].quartile == 1
    assert quartiles[3].quartile == 4
    # Q1 (low A_T) should have longer blocklife than Q4 (high A_T)
    assert quartiles[0].mean_blocklife_hours > quartiles[3].mean_blocklife_hours


def test_nested_models() -> None:
    positions = _make_positions()
    models = nested_models(positions, measure="max")
    assert "full" in models
    assert "a_t_only" in models
    assert "il_only" in models
    assert models["full"].n_obs == models["a_t_only"].n_obs


def test_sensitivity_sweep() -> None:
    from econometrics.data import DAILY_AT_MAP, IL_MAP, RAW_POSITIONS
    rows = sensitivity_sweep(
        RAW_POSITIONS, DAILY_AT_MAP, IL_MAP,
        lags=[0, 3, 5], measures=["max", "mean"],
    )
    # 3 lags * 2 measures = 6 rows (some may have 0 obs if excluded)
    assert len(rows) <= 6
    assert all(r.lag in [0, 3, 5] for r in rows)
    assert all(r.measure in ["max", "mean"] for r in rows)
```

**Step 2: Run test to verify it fails**

Run: `source uhi8/bin/activate && python -m pytest tests/econometrics/test_duration.py -v`
Expected: FAIL with `ImportError: cannot import name 'duration_model_robust'`

**Step 3: Write minimal implementation**

Replace `econometrics/duration.py` contents:

```python
"""Duration model: does fee concentration risk shorten LP position lifetimes?

Model: log(blocklife) = beta_0 + beta_1 * A_T + beta_2 * IL + eps

beta_1 < 0 -> higher concentration drives earlier exit (insurance demand signal).
HC1 heteroskedasticity-robust standard errors for reliable inference.
"""
from __future__ import annotations

import jax
import jax.numpy as jnp
import jax.scipy.stats as jstats
from jax import Array

from econometrics.ingest import build_lagged_positions
from econometrics.types import (
    LaggedPositionRow,
    QuartileRow,
    RobustDurationResult,
    SensitivityRow,
)

BLOCKS_PER_HOUR: float = 300.0


def _get_a_t(pos: LaggedPositionRow, measure: str) -> float:
    if measure == "max":
        return pos.max_a_t
    elif measure == "mean":
        return pos.mean_a_t
    elif measure == "median":
        return pos.median_a_t
    raise ValueError(f"Unknown measure: {measure}")


def duration_model_robust(
    positions: list[LaggedPositionRow],
    measure: str = "max",
) -> RobustDurationResult:
    """OLS duration model with HC1 robust standard errors."""
    n = len(positions)
    log_bl = jnp.array([jnp.log(float(p.blocklife)) for p in positions])
    a_t = jnp.array([_get_a_t(p, measure) for p in positions])
    il = jnp.array([p.il_proxy for p in positions])
    ones = jnp.ones(n)

    X = jnp.column_stack([ones, a_t, il])
    k = 3

    # OLS: beta = (X'X)^{-1} X'y
    XtX = X.T @ X
    Xty = X.T @ log_bl
    params = jnp.linalg.solve(XtX, Xty)

    # Residuals and R^2
    y_hat = X @ params
    residuals = log_bl - y_hat
    ss_res = float(jnp.sum(residuals ** 2))
    ss_tot = float(jnp.sum((log_bl - jnp.mean(log_bl)) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # OLS SEs: sigma^2 (X'X)^{-1}
    sigma2 = ss_res / (n - k)
    XtX_inv = jnp.linalg.inv(XtX)
    ols_cov = sigma2 * XtX_inv
    ols_ses = jnp.sqrt(jnp.diag(ols_cov))

    # HC1 robust SEs: (X'X)^{-1} (sum e_i^2 x_i x_i') (X'X)^{-1} * n/(n-k)
    meat = jnp.zeros((k, k))
    for i in range(n):
        xi = X[i, :].reshape(-1, 1)
        meat = meat + (float(residuals[i]) ** 2) * (xi @ xi.T)
    robust_cov = XtX_inv @ meat @ XtX_inv * (n / (n - k))
    robust_ses = jnp.sqrt(jnp.diag(jnp.abs(robust_cov)))

    # p-values
    t_stats_ols = params / ols_ses
    p_ols = 2.0 * jstats.norm.sf(jnp.abs(t_stats_ols))
    t_stats_robust = params / robust_ses
    p_robust = 2.0 * jstats.norm.sf(jnp.abs(t_stats_robust))

    mean_bl = float(jnp.mean(jnp.array([float(p.blocklife) for p in positions])))

    return RobustDurationResult(
        beta_a_t=float(params[1]),
        se_a_t=float(ols_ses[1]),
        p_value_a_t=float(p_ols[1]),
        robust_se_a_t=float(robust_ses[1]),
        robust_p_value_a_t=float(p_robust[1]),
        beta_il=float(params[2]),
        se_il=float(ols_ses[2]),
        p_value_il=float(p_ols[2]),
        robust_se_il=float(robust_ses[2]),
        robust_p_value_il=float(p_robust[2]),
        beta_intercept=float(params[0]),
        n_obs=n,
        r_squared=r_squared,
        mean_blocklife=mean_bl,
        mean_blocklife_hours=mean_bl / BLOCKS_PER_HOUR,
    )


def economic_magnitude(
    result: RobustDurationResult,
    delta_a_t: float = 0.10,
) -> dict[str, float]:
    """Translate beta_1 into economic quantities."""
    import math
    factor = math.exp(result.beta_a_t * delta_a_t)
    hours_change = result.mean_blocklife_hours * (factor - 1.0)
    return {
        "delta_a_t": delta_a_t,
        "factor": factor,
        "hours_shortened": abs(hours_change),
        "pct_change": (factor - 1.0) * 100,
        "mean_blocklife_hours": result.mean_blocklife_hours,
    }


def quartile_analysis(
    positions: list[LaggedPositionRow],
    measure: str = "max",
) -> list[QuartileRow]:
    """Split positions into 4 quartiles by A_T, report mean blocklife."""
    sorted_pos = sorted(positions, key=lambda p: _get_a_t(p, measure))
    n = len(sorted_pos)
    q_size = n // 4
    quartiles: list[QuartileRow] = []
    for q in range(4):
        start = q * q_size
        end = (q + 1) * q_size if q < 3 else n
        chunk = sorted_pos[start:end]
        if not chunk:
            continue
        mean_bl_hours = sum(p.blocklife for p in chunk) / len(chunk) / BLOCKS_PER_HOUR
        mean_at = sum(_get_a_t(p, measure) for p in chunk) / len(chunk)
        quartiles.append(QuartileRow(
            quartile=q + 1,
            mean_blocklife_hours=mean_bl_hours,
            mean_a_t=mean_at,
            n_obs=len(chunk),
        ))
    return quartiles


def nested_models(
    positions: list[LaggedPositionRow],
    measure: str = "max",
) -> dict[str, RobustDurationResult]:
    """Run full, A_T-only, and IL-only models for comparison."""
    # Full model (as-is)
    full = duration_model_robust(positions, measure=measure)

    # A_T-only: set IL to zero
    a_t_only_pos = [
        LaggedPositionRow(
            burn_date=p.burn_date, mint_date=p.mint_date, blocklife=p.blocklife,
            max_a_t=p.max_a_t, mean_a_t=p.mean_a_t, median_a_t=p.median_a_t,
            il_proxy=0.0,
        )
        for p in positions
    ]
    a_t_only = duration_model_robust(a_t_only_pos, measure=measure)

    # IL-only: set A_T to zero
    il_only_pos = [
        LaggedPositionRow(
            burn_date=p.burn_date, mint_date=p.mint_date, blocklife=p.blocklife,
            max_a_t=0.0, mean_a_t=0.0, median_a_t=0.0,
            il_proxy=p.il_proxy,
        )
        for p in positions
    ]
    il_only = duration_model_robust(il_only_pos, measure=measure)

    return {"full": full, "a_t_only": a_t_only, "il_only": il_only}


def sensitivity_sweep(
    raw_positions: list[tuple[str, int, float]],
    daily_at_map: dict[str, float],
    il_map: dict[str, float],
    lags: list[int] | None = None,
    measures: list[str] | None = None,
) -> list[SensitivityRow]:
    """Sweep over lag windows and A_T measures."""
    if lags is None:
        lags = [0, 1, 2, 3, 4, 5, 6, 7, 10]
    if measures is None:
        measures = ["max", "mean", "median"]

    rows: list[SensitivityRow] = []
    for lag in lags:
        positions = build_lagged_positions(raw_positions, daily_at_map, il_map, lag)
        if len(positions) < 10:
            continue
        for measure in measures:
            result = duration_model_robust(positions, measure=measure)
            rows.append(SensitivityRow(
                lag=lag,
                measure=measure,
                beta_a_t=result.beta_a_t,
                robust_se_a_t=result.robust_se_a_t,
                robust_p_value_a_t=result.robust_p_value_a_t,
                n_obs=result.n_obs,
            ))
    return rows
```

**Step 4: Run test to verify it passes**

Run: `source uhi8/bin/activate && python -m pytest tests/econometrics/test_duration.py -v`
Expected: 6 passed

**Step 5: Commit**

```bash
git add -f econometrics/duration.py tests/econometrics/test_duration.py
git commit -m "feat(duration): HC1 robust SEs, sensitivity sweep, quartile analysis, nested models"
```

---

### Task 4: Display Notebook

**Files:**
- Create: `notebooks/duration_results.ipynb`

**Context:** Jupyter notebook using uhi8 kernel. Display-only — all computation happens in imported module functions. Shows main result, economic magnitude, dose-response quartiles, lag sensitivity, nested model comparison, and implied insurance value.

**Step 1: Create notebooks directory**

```bash
mkdir -p notebooks
```

**Step 2: Create the notebook**

Create `notebooks/duration_results.ipynb` with these cells:

**Cell 1 (markdown):**
```markdown
# Fee Concentration Duration Model — Results

**Spec:** `specs/econometrics/lp-insurance-demand.tex`

**Model:** log(blocklife) = β₀ + β₁·max_A_T + β₂·IL + ε (OLS + HC1 robust SEs)

**Hypothesis:** β₁ < 0 → higher fee concentration shortens position life → insurance demand
```

**Cell 2 (code):**
```python
from econometrics.data import DAILY_AT_MAP, IL_MAP, RAW_POSITIONS
from econometrics.ingest import build_lagged_positions
from econometrics.duration import (
    duration_model_robust,
    economic_magnitude,
    nested_models,
    quartile_analysis,
    sensitivity_sweep,
)

LAG = 5
positions = build_lagged_positions(RAW_POSITIONS, DAILY_AT_MAP, IL_MAP, lag_days=LAG)
print(f"Positions after lag={LAG} filter: {len(positions)}")
print(f"Date range: {positions[0].burn_date} to {positions[-1].burn_date}")
```

**Cell 3 (markdown):**
```markdown
## 1. Main Result
```

**Cell 4 (code):**
```python
result = duration_model_robust(positions, measure="max")
print(f"{'':>20} {'Coeff':>10} {'OLS SE':>10} {'HC1 SE':>10} {'HC1 p':>10}")
print(f"{'β₁ (max A_T)':>20} {result.beta_a_t:>10.4f} {result.se_a_t:>10.4f} {result.robust_se_a_t:>10.4f} {result.robust_p_value_a_t:>10.6f}")
print(f"{'β₂ (IL)':>20} {result.beta_il:>10.4f} {result.se_il:>10.4f} {result.robust_se_il:>10.4f} {result.robust_p_value_il:>10.6f}")
print(f"{'β₀ (intercept)':>20} {result.beta_intercept:>10.4f}")
print(f"\nn={result.n_obs}  R²={result.r_squared:.4f}  Mean blocklife={result.mean_blocklife_hours:.1f} hours")
```

**Cell 5 (markdown):**
```markdown
## 2. Economic Magnitude
```

**Cell 6 (code):**
```python
mag = economic_magnitude(result, delta_a_t=0.10)
print(f"A 0.10 increase in max A_T:")
print(f"  Multiplicative factor: {mag['factor']:.4f}")
print(f"  Position life change:  {mag['pct_change']:+.1f}%")
print(f"  Hours shortened:       {mag['hours_shortened']:.1f} hours")
print(f"  (Mean position life:   {mag['mean_blocklife_hours']:.1f} hours)")
```

**Cell 7 (markdown):**
```markdown
## 3. Dose-Response (Quartile Analysis)
```

**Cell 8 (code):**
```python
import matplotlib.pyplot as plt

quartiles = quartile_analysis(positions, measure="max")
qs = [q.quartile for q in quartiles]
hours = [q.mean_blocklife_hours for q in quartiles]
ats = [q.mean_a_t for q in quartiles]

fig, ax1 = plt.subplots(figsize=(8, 5))
bars = ax1.bar(qs, hours, color=["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"], edgecolor="black")
ax1.set_xlabel("max A_T Quartile")
ax1.set_ylabel("Mean Position Life (hours)")
ax1.set_title("Dose-Response: Fee Concentration vs Position Duration")
ax1.set_xticks(qs)
ax1.set_xticklabels([f"Q{q}\n(A_T={a:.3f})" for q, a in zip(qs, ats)])

for bar, h, n in zip(bars, hours, [q.n_obs for q in quartiles]):
    ax1.text(bar.get_x() + bar.get_width()/2, h + 2, f"{h:.0f}h\n(n={n})",
             ha="center", va="bottom", fontsize=9)
plt.tight_layout()
plt.show()
```

**Cell 9 (markdown):**
```markdown
## 4. Lag Sensitivity
```

**Cell 10 (code):**
```python
rows = sensitivity_sweep(RAW_POSITIONS, DAILY_AT_MAP, IL_MAP)
print(f"{'Lag':>4} {'Measure':>8} {'β₁':>10} {'HC1 SE':>10} {'p-value':>10} {'n':>6} {'Sig':>4}")
print("-" * 60)
for r in rows:
    sig = "***" if r.robust_p_value_a_t < 0.01 else "**" if r.robust_p_value_a_t < 0.05 else "*" if r.robust_p_value_a_t < 0.10 else ""
    print(f"{r.lag:>4} {r.measure:>8} {r.beta_a_t:>10.4f} {r.robust_se_a_t:>10.4f} {r.robust_p_value_a_t:>10.4f} {r.n_obs:>6} {sig:>4}")
```

**Cell 11 (markdown):**
```markdown
## 5. Nested Model Comparison (IL Orthogonality)
```

**Cell 12 (code):**
```python
models = nested_models(positions, measure="max")
print(f"{'Model':>12} {'β₁(A_T)':>10} {'HC1 p':>10} {'β₂(IL)':>10} {'HC1 p':>10} {'R²':>8}")
print("-" * 65)
for name, m in models.items():
    print(f"{name:>12} {m.beta_a_t:>10.4f} {m.robust_p_value_a_t:>10.4f} {m.beta_il:>10.4f} {m.robust_p_value_il:>10.4f} {m.r_squared:>8.4f}")
```

**Cell 13 (markdown):**
```markdown
## 6. Implied Insurance Value
```

**Cell 14 (code):**
```python
import math

FEE_REVENUE_PER_HOUR = 100.0  # placeholder: $100/hr avg fee revenue per LP

if result.beta_a_t < 0:
    mean_at = sum(p.max_a_t for p in positions) / len(positions)
    hours_lost = abs(mag["hours_shortened"])
    implied_value = hours_lost * FEE_REVENUE_PER_HOUR
    print(f"Mean max A_T exposure:    {mean_at:.4f}")
    print(f"Hours shortened per 0.10: {hours_lost:.1f}")
    print(f"Fee revenue per hour:     ${FEE_REVENUE_PER_HOUR:.0f} (placeholder)")
    print(f"Implied insurance value:  ${implied_value:.0f} per position per 0.10 A_T shock")
    print(f"\nINTERPRETATION: PLPs would pay up to ${implied_value:.0f} to avoid")
    print(f"a 0.10 increase in fee concentration. This validates insurance demand.")
else:
    print("β₁ ≥ 0 — concentration does not shorten positions in this sample.")
    print("Insurance demand signal not found with current specification.")
```

**Step 3: Set notebook kernel to uhi8**

Ensure the notebook metadata specifies `uhi8` kernel:
```json
{
  "kernelspec": {
    "display_name": "uhi8",
    "language": "python",
    "name": "uhi8"
  }
}
```

**Step 4: Run the notebook**

```bash
source uhi8/bin/activate && jupyter nbconvert --to notebook --execute notebooks/duration_results.ipynb --output duration_results_executed.ipynb
```

Verify all cells execute without errors.

**Step 5: Commit**

```bash
git add -f notebooks/duration_results.ipynb
git commit -m "feat(notebook): duration model results display notebook (uhi8 kernel)"
```

---

### Task 5: Clean Up run_duration.py

**Files:**
- Modify: `econometrics/run_duration.py`

**Context:** Now that data lives in `data.py` and the model in `duration.py`, simplify `run_duration.py` to import from these modules. Remove hardcoded data.

**Step 1: Rewrite run_duration.py**

```python
"""Run duration model — thin CLI wrapper."""
from __future__ import annotations

import json
from dataclasses import asdict

from econometrics.data import DAILY_AT_MAP, IL_MAP, RAW_POSITIONS
from econometrics.duration import duration_model_robust, economic_magnitude
from econometrics.ingest import build_lagged_positions


def main() -> None:
    positions = build_lagged_positions(RAW_POSITIONS, DAILY_AT_MAP, IL_MAP, lag_days=5)
    print(f"Positions (lag=5): {len(positions)}")

    result = duration_model_robust(positions, measure="max")
    print(f"\n=== Duration Model: log(blocklife) ~ max_A_T + IL (HC1) ===")
    print(f"n={result.n_obs}  R²={result.r_squared:.4f}")
    print(f"β₁(max_A_T) = {result.beta_a_t:.4f}  HC1 SE={result.robust_se_a_t:.4f}  p={result.robust_p_value_a_t:.6f}")
    print(f"β₂(IL)      = {result.beta_il:.4f}  HC1 SE={result.robust_se_il:.4f}  p={result.robust_p_value_il:.6f}")

    mag = economic_magnitude(result)
    print(f"\nA 0.10 increase in max A_T: {mag['pct_change']:+.1f}% position life ({mag['hours_shortened']:.1f} hours)")

    out = asdict(result)
    with open("data/econometrics/duration_result.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved to data/econometrics/duration_result.json")


if __name__ == "__main__":
    main()
```

**Step 2: Run it**

```bash
source uhi8/bin/activate && python -m econometrics.run_duration
```

**Step 3: Run all tests**

```bash
source uhi8/bin/activate && python -m pytest tests/ -v
```
Expected: All tests pass.

**Step 4: Commit**

```bash
git add -f econometrics/run_duration.py
git commit -m "refactor(run): simplify run_duration to use data.py and lagged treatment"
```
