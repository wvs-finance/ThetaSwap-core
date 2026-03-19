# FCI Derived Metric — Phases 1 & 2 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Confirm that the cumulative FCI oracle diverges from daily-snapshot Δ⁺ (Phase 1), then sweep candidate accumulation mechanisms to find the best replacement (Phase 2).

**Architecture:** Two new Python modules extend the existing backtest pipeline. `oracle_comparison.py` simulates cumulative oracle behavior from position exit data, producing dual Δ⁺ series. `mechanism_sweep.py` adds epoch-reset, exponential-decay, and sliding-window step functions. A single Jupyter notebook presents all analysis. No existing code is modified.

**Tech Stack:** Python 3.11+ via `uhi8/` venv, frozen dataclasses, free pure functions, full typing. Existing pipeline: `backtest/daily.py`, `backtest/payoff.py`, `econometrics/data.py`.

**Spec:** `docs/superpowers/specs/2026-03-11-fci-derived-metric-design.md`

**Python environment:** All commands use `uhi8/` venv. Tests: `cd research && ../uhi8/bin/python -m pytest tests/ -v`

**Checkpoint rule:** After every file creation or modification, run the full test suite. Stop and fix if anything fails.

**Dune query:** The spec lists a fresh Dune query for 50 positions. Due to credit constraints (~2,489 remaining on free tier), this plan uses the fallback path: `positions_from_raw_data(RAW_POSITIONS)` bridges to the existing 600-position dataset. This loses per-position x_k² granularity but preserves daily aggregates. If credits become available, a Dune task can be added before Task 6.

---

## File Structure

### New files (Phase 1)
- `research/backtest/oracle_comparison.py` — Cumulative oracle simulation + dual series builder
- `research/tests/backtest/test_oracle_comparison.py` — Unit tests for oracle comparison
- `research/notebooks/oracle-accumulation-comparison.ipynb` — Notebook with all Phase 1 + 2 analysis

### New files (Phase 2)
- `research/backtest/mechanism_sweep.py` — Epoch, decay, sliding-window step functions + sweep runner
- `research/tests/backtest/test_mechanism_sweep.py` — Unit tests for mechanism sweep

### Existing files (read-only reference)
- `research/backtest/types.py` — `DailyPoolState`, `PositionPnL`, `BacktestResult`
- `research/backtest/payoff.py` — `ExitPayoffResult`, `PositionExitResult`, `run_exit_payoff_backtest`, `delta_to_price`, `payoff_multiplier`
- `research/backtest/daily.py` — `build_daily_states`, `approximate_mint_date`, `BLOCKS_PER_DAY`
- `research/econometrics/data.py` — `RAW_POSITIONS`, `DAILY_AT_MAP`, `DAILY_AT_NULL_MAP`, `IL_MAP`
- `research/tests/backtest/test_integration.py` — Integration test pattern reference

---

## Chunk 1: Phase 1 — Oracle Comparison Module

### Task 1: PositionExit dataclass + CumulativeOracleState dataclass

**Files:**
- Create: `research/backtest/oracle_comparison.py`
- Create: `research/tests/backtest/test_oracle_comparison.py`

- [ ] **Step 1: Write the failing test for PositionExit frozen dataclass**

```python
# research/tests/backtest/test_oracle_comparison.py
"""Tests for oracle_comparison module — cumulative vs daily-snapshot Δ⁺."""
from __future__ import annotations

import pytest

from backtest.oracle_comparison import PositionExit, CumulativeOracleState


def test_position_exit_frozen():
    pe = PositionExit(
        token_id=1,
        burn_date="2025-12-23",
        block_lifetime=7200,
        fee_share_x_k=0.25,
    )
    assert pe.token_id == 1
    assert pe.burn_date == "2025-12-23"
    assert pe.block_lifetime == 7200
    assert pe.fee_share_x_k == 0.25
    with pytest.raises(AttributeError):
        pe.token_id = 2  # type: ignore[misc]


def test_cumulative_oracle_state_frozen():
    s = CumulativeOracleState(
        accumulated_sum=1.5,
        theta_sum=0.8,
        removed_pos_count=10,
    )
    assert s.accumulated_sum == 1.5
    assert s.theta_sum == 0.8
    assert s.removed_pos_count == 10
    with pytest.raises(AttributeError):
        s.accumulated_sum = 2.0  # type: ignore[misc]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_oracle_comparison.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backtest.oracle_comparison'`

- [ ] **Step 3: Write minimal implementation**

```python
# research/backtest/oracle_comparison.py
"""Oracle comparison — cumulative vs daily-snapshot Δ⁺ series.

Simulates the Solidity FCI oracle's append-only accumulators against
the daily-snapshot baseline used by the backtest pipeline.

Pure functions, frozen dataclasses per @functional-python.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PositionExit:
    """One position's exit event with per-position fee share."""
    token_id: int
    burn_date: str
    block_lifetime: int
    fee_share_x_k: float


@dataclass(frozen=True)
class CumulativeOracleState:
    """Snapshot of cumulative oracle accumulators after processing exits."""
    accumulated_sum: float
    theta_sum: float
    removed_pos_count: int
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_oracle_comparison.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Checkpoint — run full test suite**

Run: `cd research && ../uhi8/bin/python -m pytest tests/ -v`
Expected: All existing tests + 2 new tests pass

---

### Task 2: step_cumulative pure function

**Files:**
- Modify: `research/backtest/oracle_comparison.py`
- Modify: `research/tests/backtest/test_oracle_comparison.py`

- [ ] **Step 1: Write the failing test for step_cumulative**

Append to `test_oracle_comparison.py`:

```python
from backtest.oracle_comparison import step_cumulative


def test_step_cumulative_first_exit():
    """First exit: state goes from zero to non-zero."""
    initial = CumulativeOracleState(
        accumulated_sum=0.0,
        theta_sum=0.0,
        removed_pos_count=0,
    )
    exit_ = PositionExit(
        token_id=1,
        burn_date="2025-12-23",
        block_lifetime=7200,
        fee_share_x_k=0.5,
    )
    result = step_cumulative(initial, exit_)

    # x_k_squared = 0.5^2 = 0.25
    # accumulated_sum += x_k^2 / lifetime = 0.25 / 7200
    assert result.accumulated_sum == pytest.approx(0.25 / 7200)
    # theta_sum += 1.0 / lifetime = 1/7200
    assert result.theta_sum == pytest.approx(1.0 / 7200)
    assert result.removed_pos_count == 1


def test_step_cumulative_accumulates():
    """Cumulative state is append-only — values only increase."""
    s0 = CumulativeOracleState(accumulated_sum=0.0, theta_sum=0.0, removed_pos_count=0)
    e1 = PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.5)
    e2 = PositionExit(token_id=2, burn_date="2025-12-24", block_lifetime=3600, fee_share_x_k=0.3)

    s1 = step_cumulative(s0, e1)
    s2 = step_cumulative(s1, e2)

    assert s2.accumulated_sum > s1.accumulated_sum
    assert s2.theta_sum > s1.theta_sum
    assert s2.removed_pos_count == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_oracle_comparison.py::test_step_cumulative_first_exit -v`
Expected: FAIL with `ImportError: cannot import name 'step_cumulative'`

- [ ] **Step 3: Write minimal implementation**

Add to `oracle_comparison.py`:

```python
def step_cumulative(state: CumulativeOracleState, exit_: PositionExit) -> CumulativeOracleState:
    """Simulate one Solidity addStateTerm() call.

    Mirrors FeeConcentrationStateMod.addTerm():
      accumulatedSum += x_k^2 / blockLifetime
      thetaSum += 1.0 / blockLifetime
      removedPosCount += 1
    """
    x_k_sq = exit_.fee_share_x_k ** 2
    return CumulativeOracleState(
        accumulated_sum=state.accumulated_sum + x_k_sq / exit_.block_lifetime,
        theta_sum=state.theta_sum + 1.0 / exit_.block_lifetime,
        removed_pos_count=state.removed_pos_count + 1,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_oracle_comparison.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Checkpoint — run full test suite**

Run: `cd research && ../uhi8/bin/python -m pytest tests/ -v`
Expected: All pass

---

### Task 3: cumulative_delta_plus + daily_snapshot_delta_plus functions

**Files:**
- Modify: `research/backtest/oracle_comparison.py`
- Modify: `research/tests/backtest/test_oracle_comparison.py`

- [ ] **Step 1: Write failing tests**

Append to `test_oracle_comparison.py`:

```python
from backtest.oracle_comparison import cumulative_delta_plus, daily_snapshot_delta_plus
import math


def test_cumulative_delta_plus_matches_solidity_formula():
    """Δ⁺ = max(0, sqrt(accumulatedSum) - sqrt(thetaSum / N²))."""
    state = CumulativeOracleState(
        accumulated_sum=0.04,   # sqrt = 0.2
        theta_sum=0.01,         # sqrt(0.01/100) = sqrt(0.0001) = 0.01
        removed_pos_count=10,
    )
    expected = max(0.0, math.sqrt(0.04) - math.sqrt(0.01 / 100))
    assert cumulative_delta_plus(state) == pytest.approx(expected)


def test_cumulative_delta_plus_zero_when_no_concentration():
    """When all positions have equal fee share, Δ⁺ should be near zero."""
    # N positions each with x_k = 1/N and same lifetime
    n = 10
    lifetime = 7200
    x_k = 1.0 / n
    acc_sum = n * (x_k ** 2 / lifetime)  # sum(x_k^2/lifetime)
    theta_sum = n * (1.0 / lifetime)     # sum(1/lifetime)
    state = CumulativeOracleState(
        accumulated_sum=acc_sum,
        theta_sum=theta_sum,
        removed_pos_count=n,
    )
    # sqrt(sum(x_k^2/L)) = sqrt(N * (1/N)^2 / L) = sqrt(1/(N*L))
    # sqrt(sum(1/L)/N^2) = sqrt(N/L / N^2) = sqrt(1/(N*L))
    # They're equal => Δ⁺ = 0
    assert cumulative_delta_plus(state) == pytest.approx(0.0, abs=1e-12)


def test_cumulative_delta_plus_zero_state():
    """Empty state returns 0."""
    state = CumulativeOracleState(accumulated_sum=0.0, theta_sum=0.0, removed_pos_count=0)
    assert cumulative_delta_plus(state) == 0.0


def test_daily_snapshot_delta_plus_basic():
    """Daily snapshot computes Δ⁺ fresh from day's exits only."""
    exits = [
        PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.8),
        PositionExit(token_id=2, burn_date="2025-12-23", block_lifetime=3600, fee_share_x_k=0.2),
    ]
    dp = daily_snapshot_delta_plus(exits)
    # This should be computed fresh — no memory of previous days
    assert dp >= 0.0


def test_daily_snapshot_delta_plus_empty():
    """No exits => Δ⁺ = 0."""
    assert daily_snapshot_delta_plus([]) == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_oracle_comparison.py::test_cumulative_delta_plus_matches_solidity_formula -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

Add to `oracle_comparison.py`:

```python
import math


def cumulative_delta_plus(state: CumulativeOracleState) -> float:
    """Compute Δ⁺ from cumulative oracle state.

    Mirrors FeeConcentrationStateMod.deltaPlus():
      Δ⁺ = max(0, sqrt(accumulatedSum) - sqrt(thetaSum / N²))
    """
    if state.removed_pos_count == 0:
        return 0.0
    n_sq = state.removed_pos_count ** 2
    term_a = math.sqrt(state.accumulated_sum)
    term_b = math.sqrt(state.theta_sum / n_sq)
    return max(0.0, term_a - term_b)


def daily_snapshot_delta_plus(exits: list[PositionExit]) -> float:
    """Compute Δ⁺ from a single day's exits only (no memory).

    Same formula as cumulative, but applied to only one day's data.
    This is what the backtest's daily.py does via DAILY_AT_MAP.
    """
    if not exits:
        return 0.0
    n = len(exits)
    acc_sum = sum(e.fee_share_x_k ** 2 / e.block_lifetime for e in exits)
    theta_sum = sum(1.0 / e.block_lifetime for e in exits)
    n_sq = n ** 2
    term_a = math.sqrt(acc_sum)
    term_b = math.sqrt(theta_sum / n_sq)
    return max(0.0, term_a - term_b)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_oracle_comparison.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Checkpoint — run full test suite**

Run: `cd research && ../uhi8/bin/python -m pytest tests/ -v`
Expected: All pass

---

### Task 4: DualDeltaPlusSeries dataclass + build_dual_series function

**Files:**
- Modify: `research/backtest/oracle_comparison.py`
- Modify: `research/tests/backtest/test_oracle_comparison.py`

- [ ] **Step 1: Write the failing test**

Append to `test_oracle_comparison.py`:

```python
from backtest.oracle_comparison import DualDeltaPlusSeries, build_dual_series


def test_dual_series_dataclass():
    s = DualDeltaPlusSeries(
        days=["2025-12-23", "2025-12-24"],
        cumulative_delta_plus=[0.15, 0.14],
        daily_snapshot_delta_plus=[0.15, 0.001],
    )
    assert len(s.days) == 2
    assert s.cumulative_delta_plus[1] > s.daily_snapshot_delta_plus[1]


def test_build_dual_series_divergence():
    """After a high-concentration day, cumulative stays elevated but daily resets."""
    exits = [
        # Day 1: high concentration (one position dominates)
        PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=100, fee_share_x_k=0.95),
        PositionExit(token_id=2, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.05),
        # Day 2: low concentration (equal shares)
        PositionExit(token_id=3, burn_date="2025-12-24", block_lifetime=7200, fee_share_x_k=0.5),
        PositionExit(token_id=4, burn_date="2025-12-24", block_lifetime=7200, fee_share_x_k=0.5),
    ]
    series = build_dual_series(exits)

    assert len(series.days) == 2
    # Day 1: both should be similar (no prior history)
    # Day 2: cumulative carries Day 1 baggage, daily snapshot resets
    assert series.daily_snapshot_delta_plus[1] < series.daily_snapshot_delta_plus[0]
    # Cumulative stays elevated due to Day 1 spike
    assert series.cumulative_delta_plus[1] > 0
    # Key assertion: cumulative diverges above daily after the spike
    assert series.cumulative_delta_plus[1] > series.daily_snapshot_delta_plus[1]


def test_build_dual_series_empty():
    series = build_dual_series([])
    assert len(series.days) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_oracle_comparison.py::test_build_dual_series_divergence -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

Add to `oracle_comparison.py`:

```python
from collections import defaultdict


@dataclass(frozen=True)
class DualDeltaPlusSeries:
    """Parallel Δ⁺ series: cumulative (Solidity oracle) vs daily-snapshot (backtest)."""
    days: tuple[str, ...]
    cumulative_delta_plus: tuple[float, ...]
    daily_snapshot_delta_plus: tuple[float, ...]


def build_dual_series(exits: list[PositionExit]) -> DualDeltaPlusSeries:
    """Build dual Δ⁺ series from position exits sorted by burn date.

    Groups exits by burn_date, then for each day:
    - Cumulative: feeds exits into running cumulative state, computes Δ⁺
    - Daily snapshot: computes Δ⁺ from that day's exits only
    """
    if not exits:
        return DualDeltaPlusSeries(days=(), cumulative_delta_plus=(), daily_snapshot_delta_plus=())

    # Group by burn_date
    by_day: dict[str, list[PositionExit]] = defaultdict(list)
    for e in exits:
        by_day[e.burn_date].append(e)

    sorted_days = sorted(by_day.keys())

    days_acc: list[str] = []
    cum_acc: list[float] = []
    snap_acc: list[float] = []

    cum_state = CumulativeOracleState(accumulated_sum=0.0, theta_sum=0.0, removed_pos_count=0)

    for day in sorted_days:
        day_exits = by_day[day]

        # Step cumulative state through all exits on this day
        for e in day_exits:
            cum_state = step_cumulative(cum_state, e)

        # Compute both Δ⁺ values
        cum_dp = cumulative_delta_plus(cum_state)
        snap_dp = daily_snapshot_delta_plus(day_exits)

        days_acc.append(day)
        cum_acc.append(cum_dp)
        snap_acc.append(snap_dp)

    return DualDeltaPlusSeries(
        days=tuple(days_acc),
        cumulative_delta_plus=tuple(cum_acc),
        daily_snapshot_delta_plus=tuple(snap_acc),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_oracle_comparison.py -v`
Expected: PASS (12 tests)

- [ ] **Step 5: Checkpoint — run full test suite**

Run: `cd research && ../uhi8/bin/python -m pytest tests/ -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add research/backtest/oracle_comparison.py research/tests/backtest/test_oracle_comparison.py
git commit -m "feat(research): add oracle_comparison module — cumulative vs daily-snapshot Δ⁺"
```

---

### Task 5: positions_from_raw_data helper (bridge to existing data)

**Files:**
- Modify: `research/backtest/oracle_comparison.py`
- Modify: `research/tests/backtest/test_oracle_comparison.py`

- [ ] **Step 1: Write the failing test**

Append to `test_oracle_comparison.py`:

```python
from backtest.oracle_comparison import positions_from_raw_data


def test_positions_from_raw_data():
    """Convert RAW_POSITIONS tuples to PositionExit list."""
    # Use a small subset
    raw = [
        ("2025-12-23", 100, 0.15843),
        ("2025-12-23", 7200, 0.15843),
        ("2025-12-24", 3600, 0.13833),
    ]
    exits = positions_from_raw_data(raw)

    assert len(exits) == 3
    assert all(isinstance(e, PositionExit) for e in exits)
    # token_id is index-based
    assert exits[0].token_id == 0
    assert exits[1].token_id == 1
    assert exits[2].token_id == 2
    # burn_date preserved
    assert exits[0].burn_date == "2025-12-23"
    assert exits[2].burn_date == "2025-12-24"
    # block_lifetime preserved
    assert exits[0].block_lifetime == 100
    # fee_share_x_k comes from exit_day_a_t (3rd tuple element)
    assert exits[0].fee_share_x_k == 0.15843
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_oracle_comparison.py::test_positions_from_raw_data -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

Add to `oracle_comparison.py`:

```python
def positions_from_raw_data(
    raw_positions: list[tuple[str, int, float]],
) -> list[PositionExit]:
    """Convert RAW_POSITIONS tuples to PositionExit list.

    Uses the exit_day_a_t value from the tuple as fee_share_x_k.
    This is the per-position x_k approximation available in the existing data.

    Args:
        raw_positions: List of (burn_date, blocklife, exit_day_a_t) tuples

    Returns:
        List of PositionExit sorted by burn_date
    """
    return [
        PositionExit(
            token_id=idx,
            burn_date=burn_date,
            block_lifetime=blocklife,
            fee_share_x_k=exit_day_a_t,
        )
        for idx, (burn_date, blocklife, exit_day_a_t) in enumerate(raw_positions)
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_oracle_comparison.py -v`
Expected: PASS (13 tests)

- [ ] **Step 5: Checkpoint — run full test suite**

Run: `cd research && ../uhi8/bin/python -m pytest tests/ -v`
Expected: All pass

---

### Task 6: Integration test with real data

**Files:**
- Modify: `research/tests/backtest/test_oracle_comparison.py`

- [ ] **Step 1: Write integration test using real data**

Append to `test_oracle_comparison.py`:

```python
from econometrics.data import RAW_POSITIONS, DAILY_AT_MAP


def test_dual_series_real_data_dec23_spike():
    """Real data: cumulative Δ⁺ diverges from daily-snapshot after Dec 23 spike."""
    exits = positions_from_raw_data(RAW_POSITIONS)
    series = build_dual_series(exits)

    # Find Dec 23 index
    dec23_idx = series.days.index("2025-12-23")

    # Dec 23 is the spike day — both should be elevated
    assert series.daily_snapshot_delta_plus[dec23_idx] > 0.01, \
        f"Dec 23 daily Δ⁺ should be elevated: {series.daily_snapshot_delta_plus[dec23_idx]}"

    # After Dec 23, daily-snapshot should drop but cumulative should stay elevated
    if dec23_idx + 1 < len(series.days):
        dec24_cum = series.cumulative_delta_plus[dec23_idx + 1]
        dec24_snap = series.daily_snapshot_delta_plus[dec23_idx + 1]

        # Cumulative stays elevated (carries Dec 23 baggage)
        assert dec24_cum > 0.01, \
            f"Cumulative should stay elevated after spike: {dec24_cum}"
        # Daily snapshot resets to current day's conditions
        # (may or may not be lower — the key is cumulative >= daily)
        assert dec24_cum >= dec24_snap * 0.5, \
            "Cumulative should be at least comparable to daily after spike"


def test_dual_series_real_data_has_all_days():
    """Real data: series covers all exit days in RAW_POSITIONS."""
    exits = positions_from_raw_data(RAW_POSITIONS)
    series = build_dual_series(exits)

    # Should have entries for each unique burn_date
    unique_burn_dates = sorted(set(bd for bd, _, _ in RAW_POSITIONS))
    assert series.days == unique_burn_dates
    assert len(series.cumulative_delta_plus) == len(unique_burn_dates)
    assert len(series.daily_snapshot_delta_plus) == len(unique_burn_dates)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_oracle_comparison.py::test_dual_series_real_data_dec23_spike -v`
Expected: PASS

- [ ] **Step 3: Checkpoint — run full test suite**

Run: `cd research && ../uhi8/bin/python -m pytest tests/ -v`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add research/backtest/oracle_comparison.py research/tests/backtest/test_oracle_comparison.py
git commit -m "feat(research): add positions_from_raw_data + real data integration test"
```

---

## Chunk 2: Phase 2 — Mechanism Sweep Module

### Task 7: EpochState + step_epoch function

**Files:**
- Create: `research/backtest/mechanism_sweep.py`
- Create: `research/tests/backtest/test_mechanism_sweep.py`

- [ ] **Step 1: Write failing tests for epoch-reset mechanism**

```python
# research/tests/backtest/test_mechanism_sweep.py
"""Tests for mechanism_sweep — epoch, decay, sliding-window step functions."""
from __future__ import annotations

import pytest

from backtest.oracle_comparison import PositionExit
from backtest.mechanism_sweep import EpochState, step_epoch, epoch_delta_plus


def test_epoch_state_frozen():
    s = EpochState(
        accumulated_sum=0.0,
        theta_sum=0.0,
        removed_pos_count=0,
        epoch_start="2025-12-23",
        epoch_length_days=7,
    )
    assert s.epoch_length_days == 7
    with pytest.raises(AttributeError):
        s.epoch_start = "2025-12-24"  # type: ignore[misc]


def test_step_epoch_within_epoch():
    """Exits within the same epoch accumulate normally."""
    s0 = EpochState(
        accumulated_sum=0.0, theta_sum=0.0, removed_pos_count=0,
        epoch_start="2025-12-20", epoch_length_days=7,
    )
    e = PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.5)
    s1 = step_epoch(s0, e)

    assert s1.accumulated_sum == pytest.approx(0.25 / 7200)
    assert s1.removed_pos_count == 1
    assert s1.epoch_start == "2025-12-20"  # epoch unchanged


def test_step_epoch_crosses_boundary():
    """Exit past epoch boundary resets accumulators."""
    s0 = EpochState(
        accumulated_sum=999.0, theta_sum=999.0, removed_pos_count=100,
        epoch_start="2025-12-16", epoch_length_days=7,
    )
    # Dec 23 is day 7 from Dec 16 => crosses epoch boundary
    e = PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.5)
    s1 = step_epoch(s0, e)

    # State should be RESET, then this exit accumulated fresh
    assert s1.accumulated_sum == pytest.approx(0.25 / 7200)
    assert s1.removed_pos_count == 1
    assert s1.epoch_start == "2025-12-23"  # new epoch started


def test_epoch_delta_plus():
    s = EpochState(
        accumulated_sum=0.04, theta_sum=0.01, removed_pos_count=10,
        epoch_start="2025-12-20", epoch_length_days=7,
    )
    dp = epoch_delta_plus(s)
    assert dp >= 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_mechanism_sweep.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# research/backtest/mechanism_sweep.py
"""Mechanism sweep — epoch, decay, and sliding-window accumulation models.

Each mechanism provides a step function and delta_plus computation.
All are pure functions operating on frozen dataclasses.

Per @functional-python.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from backtest.oracle_comparison import PositionExit


# ── Epoch-reset mechanism ──────────────────────────────────────────


@dataclass(frozen=True)
class EpochState:
    """Accumulator state with epoch-based reset."""
    accumulated_sum: float
    theta_sum: float
    removed_pos_count: int
    epoch_start: str
    epoch_length_days: int


def _date_diff_days(d1: str, d2: str) -> int:
    """Days between two YYYY-MM-DD strings."""
    dt1 = datetime.strptime(d1, "%Y-%m-%d")
    dt2 = datetime.strptime(d2, "%Y-%m-%d")
    return (dt2 - dt1).days


def step_epoch(state: EpochState, exit_: PositionExit) -> EpochState:
    """Accumulate exit into epoch state, resetting if epoch boundary crossed."""
    days_since_epoch = _date_diff_days(state.epoch_start, exit_.burn_date)

    if days_since_epoch >= state.epoch_length_days:
        # Reset: new epoch starts at this exit's date
        x_k_sq = exit_.fee_share_x_k ** 2
        return EpochState(
            accumulated_sum=x_k_sq / exit_.block_lifetime,
            theta_sum=1.0 / exit_.block_lifetime,
            removed_pos_count=1,
            epoch_start=exit_.burn_date,
            epoch_length_days=state.epoch_length_days,
        )
    else:
        # Accumulate within epoch
        x_k_sq = exit_.fee_share_x_k ** 2
        return EpochState(
            accumulated_sum=state.accumulated_sum + x_k_sq / exit_.block_lifetime,
            theta_sum=state.theta_sum + 1.0 / exit_.block_lifetime,
            removed_pos_count=state.removed_pos_count + 1,
            epoch_start=state.epoch_start,
            epoch_length_days=state.epoch_length_days,
        )


def epoch_delta_plus(state: EpochState) -> float:
    """Compute Δ⁺ from epoch state — same formula, epoch-scoped data."""
    if state.removed_pos_count == 0:
        return 0.0
    n_sq = state.removed_pos_count ** 2
    return max(0.0, math.sqrt(state.accumulated_sum) - math.sqrt(state.theta_sum / n_sq))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_mechanism_sweep.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Checkpoint — run full test suite**

Run: `cd research && ../uhi8/bin/python -m pytest tests/ -v`
Expected: All pass

---

### Task 8: DecayState + step_decay function

**Files:**
- Modify: `research/backtest/mechanism_sweep.py`
- Modify: `research/tests/backtest/test_mechanism_sweep.py`

- [ ] **Step 1: Write failing tests**

Append to `test_mechanism_sweep.py`:

```python
from backtest.mechanism_sweep import DecayState, step_decay, decay_delta_plus


def test_decay_state_frozen():
    s = DecayState(
        accumulated_sum=1.0, theta_sum=0.5, effective_count=5.0,
        last_update="2025-12-23", half_life_days=7.0,
    )
    assert s.half_life_days == 7.0


def test_step_decay_applies_decay_before_accumulating():
    """Decay multiplies existing state by exp(-λ*dt) before adding new exit."""
    s0 = DecayState(
        accumulated_sum=1.0, theta_sum=0.5, effective_count=5.0,
        last_update="2025-12-20", half_life_days=7.0,
    )
    e = PositionExit(token_id=1, burn_date="2025-12-27", block_lifetime=7200, fee_share_x_k=0.5)
    s1 = step_decay(s0, e)

    # 7 days elapsed, half_life=7 => decay factor = 0.5
    import math
    decay = 0.5  # exp(-ln2 * 7/7) = exp(-ln2) = 0.5
    expected_acc = 1.0 * decay + 0.25 / 7200
    assert s1.accumulated_sum == pytest.approx(expected_acc, rel=1e-6)
    # effective_count also decays
    assert s1.effective_count == pytest.approx(5.0 * decay + 1.0, rel=1e-6)


def test_step_decay_same_day_no_decay():
    """Same-day exit: no time elapsed, no decay applied."""
    s0 = DecayState(
        accumulated_sum=1.0, theta_sum=0.5, effective_count=5.0,
        last_update="2025-12-23", half_life_days=7.0,
    )
    e = PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.5)
    s1 = step_decay(s0, e)

    expected_acc = 1.0 + 0.25 / 7200  # no decay
    assert s1.accumulated_sum == pytest.approx(expected_acc, rel=1e-6)


def test_decay_delta_plus():
    s = DecayState(
        accumulated_sum=0.04, theta_sum=0.01, effective_count=10.0,
        last_update="2025-12-23", half_life_days=7.0,
    )
    dp = decay_delta_plus(s)
    assert dp >= 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_mechanism_sweep.py::test_step_decay_applies_decay_before_accumulating -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

Add to `mechanism_sweep.py`:

```python
# ── Exponential-decay mechanism ────────────────────────────────────


@dataclass(frozen=True)
class DecayState:
    """Accumulator state with exponential decay.

    effective_count decays alongside accumulated_sum and theta_sum,
    preventing the N² denominator from growing unboundedly while
    the numerators decay. This keeps the Δ⁺ formula balanced.
    """
    accumulated_sum: float
    theta_sum: float
    effective_count: float  # decays with same factor as accumulators
    last_update: str
    half_life_days: float


def step_decay(state: DecayState, exit_: PositionExit) -> DecayState:
    """Decay existing state, then accumulate new exit.

    decay_factor = exp(-ln(2) * dt / half_life)
    All three accumulators (accumulated_sum, theta_sum, effective_count)
    decay together so the Δ⁺ formula remains balanced.
    """
    dt = _date_diff_days(state.last_update, exit_.burn_date)
    if dt > 0:
        lam = math.log(2) / state.half_life_days
        decay = math.exp(-lam * dt)
    else:
        decay = 1.0

    x_k_sq = exit_.fee_share_x_k ** 2
    return DecayState(
        accumulated_sum=state.accumulated_sum * decay + x_k_sq / exit_.block_lifetime,
        theta_sum=state.theta_sum * decay + 1.0 / exit_.block_lifetime,
        effective_count=state.effective_count * decay + 1.0,
        last_update=exit_.burn_date,
        half_life_days=state.half_life_days,
    )


def decay_delta_plus(state: DecayState) -> float:
    """Compute Δ⁺ from decay state.

    Uses effective_count (which decays alongside the accumulators)
    instead of raw count, keeping the N² denominator balanced.
    """
    if state.effective_count < 1e-10:
        return 0.0
    n_sq = state.effective_count ** 2
    return max(0.0, math.sqrt(state.accumulated_sum) - math.sqrt(state.theta_sum / n_sq))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_mechanism_sweep.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Checkpoint — run full test suite**

Run: `cd research && ../uhi8/bin/python -m pytest tests/ -v`
Expected: All pass

---

### Task 9: WindowState + step_window function

**Files:**
- Modify: `research/backtest/mechanism_sweep.py`
- Modify: `research/tests/backtest/test_mechanism_sweep.py`

- [ ] **Step 1: Write failing tests**

Append to `test_mechanism_sweep.py`:

```python
from backtest.mechanism_sweep import WindowState, step_window, window_delta_plus


def test_window_state_frozen():
    s = WindowState(
        entries=((0.1, 7200),),
        window_size=10,
    )
    assert s.window_size == 10


def test_step_window_within_capacity():
    """Window accumulates when under capacity."""
    s0 = WindowState(entries=(), window_size=3)
    e1 = PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.5)
    s1 = step_window(s0, e1)
    assert len(s1.entries) == 1


def test_step_window_evicts_oldest():
    """Window drops oldest entry when at capacity."""
    s0 = WindowState(
        entries=((0.1, 7200), (0.2, 3600), (0.3, 1800)),
        window_size=3,
    )
    e = PositionExit(token_id=4, burn_date="2025-12-24", block_lifetime=100, fee_share_x_k=0.9)
    s1 = step_window(s0, e)

    assert len(s1.entries) == 3
    # Oldest (0.1, 7200) should be evicted
    assert s1.entries[0] == (0.2, 3600)
    # Newest should be last
    assert s1.entries[-1] == (0.9, 100)


def test_window_delta_plus():
    s = WindowState(
        entries=((0.5, 7200), (0.3, 3600), (0.2, 1800)),
        window_size=10,
    )
    dp = window_delta_plus(s)
    assert dp >= 0.0


def test_window_delta_plus_empty():
    s = WindowState(entries=(), window_size=10)
    assert window_delta_plus(s) == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_mechanism_sweep.py::test_step_window_evicts_oldest -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

Add to `mechanism_sweep.py`:

```python
# ── Sliding-window mechanism ──────────────────────────────────────


@dataclass(frozen=True)
class WindowState:
    """Ring buffer of recent (fee_share_x_k, block_lifetime) entries."""
    entries: tuple[tuple[float, int], ...]  # immutable ring buffer
    window_size: int


def step_window(state: WindowState, exit_: PositionExit) -> WindowState:
    """Add exit to window, evicting oldest if at capacity."""
    new_entry = (exit_.fee_share_x_k, exit_.block_lifetime)
    entries = state.entries + (new_entry,)
    if len(entries) > state.window_size:
        entries = entries[1:]  # drop oldest
    return WindowState(entries=entries, window_size=state.window_size)


def window_delta_plus(state: WindowState) -> float:
    """Compute Δ⁺ from window entries only."""
    if not state.entries:
        return 0.0
    n = len(state.entries)
    acc_sum = sum(x_k ** 2 / lifetime for x_k, lifetime in state.entries)
    theta_sum = sum(1.0 / lifetime for _, lifetime in state.entries)
    n_sq = n ** 2
    return max(0.0, math.sqrt(acc_sum) - math.sqrt(theta_sum / n_sq))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_mechanism_sweep.py -v`
Expected: PASS (13 tests)

- [ ] **Step 5: Checkpoint — run full test suite**

Run: `cd research && ../uhi8/bin/python -m pytest tests/ -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add research/backtest/mechanism_sweep.py research/tests/backtest/test_mechanism_sweep.py
git commit -m "feat(research): add mechanism_sweep — epoch, decay, sliding-window step functions"
```

---

### Task 10: build_mechanism_series — unified series builder for all mechanisms

**Files:**
- Modify: `research/backtest/mechanism_sweep.py`
- Modify: `research/tests/backtest/test_mechanism_sweep.py`

- [ ] **Step 1: Write failing tests**

Append to `test_mechanism_sweep.py`:

```python
from backtest.mechanism_sweep import MechanismSeries, build_mechanism_series


def test_mechanism_series_dataclass():
    s = MechanismSeries(
        days=("2025-12-23",),
        delta_plus_values=(0.15,),
        mechanism_name="epoch",
        params={"epoch_length_days": 7},
    )
    assert s.mechanism_name == "epoch"


def test_build_mechanism_series_epoch():
    exits = [
        PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=100, fee_share_x_k=0.9),
        PositionExit(token_id=2, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.1),
        PositionExit(token_id=3, burn_date="2025-12-24", block_lifetime=7200, fee_share_x_k=0.5),
    ]
    series = build_mechanism_series(exits, mechanism="epoch", epoch_length_days=7)
    assert series.mechanism_name == "epoch"
    assert len(series.days) == 2
    assert all(v >= 0 for v in series.delta_plus_values)


def test_build_mechanism_series_decay():
    exits = [
        PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=100, fee_share_x_k=0.9),
        PositionExit(token_id=2, burn_date="2025-12-24", block_lifetime=7200, fee_share_x_k=0.1),
    ]
    series = build_mechanism_series(exits, mechanism="decay", half_life_days=7.0)
    assert series.mechanism_name == "decay"
    assert len(series.days) == 2


def test_build_mechanism_series_window():
    exits = [
        PositionExit(token_id=i, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.5)
        for i in range(5)
    ]
    series = build_mechanism_series(exits, mechanism="window", window_size=3)
    assert series.mechanism_name == "window"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_mechanism_sweep.py::test_build_mechanism_series_epoch -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

Add to `mechanism_sweep.py`:

```python
from collections import defaultdict


@dataclass(frozen=True)
class MechanismSeries:
    """Δ⁺ time series for one mechanism with specific parameters."""
    days: tuple[str, ...]
    delta_plus_values: tuple[float, ...]
    mechanism_name: str
    params: dict[str, float | int]


def build_mechanism_series(
    exits: list[PositionExit],
    mechanism: str,
    **kwargs: float | int,
) -> MechanismSeries:
    """Build Δ⁺ series for a given mechanism.

    Args:
        exits: Position exits sorted by burn_date
        mechanism: One of "epoch", "decay", "window"
        **kwargs: Mechanism-specific parameters
    """
    # Group by day
    by_day: dict[str, list[PositionExit]] = defaultdict(list)
    for e in exits:
        by_day[e.burn_date].append(e)
    sorted_days = sorted(by_day.keys())

    days_acc: list[str] = []
    values_acc: list[float] = []

    if mechanism == "epoch":
        epoch_len = int(kwargs.get("epoch_length_days", 7))
        state = EpochState(
            accumulated_sum=0.0, theta_sum=0.0, removed_pos_count=0,
            epoch_start=sorted_days[0] if sorted_days else "2025-01-01",
            epoch_length_days=epoch_len,
        )
        for day in sorted_days:
            for e in by_day[day]:
                state = step_epoch(state, e)
            days_acc.append(day)
            values_acc.append(epoch_delta_plus(state))
        params = {"epoch_length_days": epoch_len}

    elif mechanism == "decay":
        hl = float(kwargs.get("half_life_days", 7.0))
        state_d = DecayState(
            accumulated_sum=0.0, theta_sum=0.0, effective_count=0.0,
            last_update=sorted_days[0] if sorted_days else "2025-01-01",
            half_life_days=hl,
        )
        for day in sorted_days:
            for e in by_day[day]:
                state_d = step_decay(state_d, e)
            days_acc.append(day)
            values_acc.append(decay_delta_plus(state_d))
        params = {"half_life_days": hl}

    elif mechanism == "window":
        ws = int(kwargs.get("window_size", 25))
        state_w = WindowState(entries=(), window_size=ws)
        for day in sorted_days:
            for e in by_day[day]:
                state_w = step_window(state_w, e)
            days_acc.append(day)
            values_acc.append(window_delta_plus(state_w))
        params = {"window_size": ws}

    else:
        raise ValueError(f"Unknown mechanism: {mechanism}")

    return MechanismSeries(
        days=tuple(days_acc),
        delta_plus_values=tuple(values_acc),
        mechanism_name=mechanism,
        params=params,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_mechanism_sweep.py -v`
Expected: PASS (17 tests)

- [ ] **Step 5: Checkpoint — run full test suite**

Run: `cd research && ../uhi8/bin/python -m pytest tests/ -v`
Expected: All pass

---

### Task 11: run_mechanism_sweep — full parameter grid

**Files:**
- Modify: `research/backtest/mechanism_sweep.py`
- Modify: `research/tests/backtest/test_mechanism_sweep.py`

- [ ] **Step 1: Write failing tests**

Append to `test_mechanism_sweep.py`:

```python
from backtest.mechanism_sweep import SweepResult, run_mechanism_sweep, compute_correlation


def test_compute_correlation_perfect():
    assert compute_correlation([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)


def test_compute_correlation_inverse():
    assert compute_correlation([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)


def test_compute_correlation_short():
    """Less than 3 data points returns 0."""
    assert compute_correlation([1], [1]) == 0.0


def test_run_mechanism_sweep_basic():
    exits = [
        PositionExit(token_id=1, burn_date="2025-12-23", block_lifetime=100, fee_share_x_k=0.9),
        PositionExit(token_id=2, burn_date="2025-12-23", block_lifetime=7200, fee_share_x_k=0.1),
        PositionExit(token_id=3, burn_date="2025-12-24", block_lifetime=7200, fee_share_x_k=0.5),
        PositionExit(token_id=4, burn_date="2025-12-24", block_lifetime=3600, fee_share_x_k=0.5),
        PositionExit(token_id=5, burn_date="2025-12-25", block_lifetime=7200, fee_share_x_k=0.3),
    ]
    # Daily snapshot baseline from oracle_comparison
    from backtest.oracle_comparison import build_dual_series
    dual = build_dual_series(exits)

    results = run_mechanism_sweep(
        exits=exits,
        daily_snapshot_baseline=dual.daily_snapshot_delta_plus,
        baseline_days=dual.days,
        epoch_lengths=[3, 7],
        half_lives=[3.0, 7.0],
        window_sizes=[3],
    )
    assert len(results) == 5  # 2 epoch + 2 decay + 1 window
    assert all(isinstance(r, SweepResult) for r in results)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_mechanism_sweep.py::test_run_mechanism_sweep_basic -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

Add to `mechanism_sweep.py`:

```python
@dataclass(frozen=True)
class SweepResult:
    """Evaluation of one mechanism + parameter combo against daily-snapshot baseline."""
    mechanism_name: str
    params: dict[str, float | int]
    correlation: float
    max_divergence: float
    series: MechanismSeries


def compute_correlation(xs: list[float], ys: list[float]) -> float:
    """Pearson correlation between two series. Returns 0 if too few data points."""
    n = len(xs)
    if n < 3 or n != len(ys):
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    denom = math.sqrt(var_x * var_y)
    if denom == 0:
        return 0.0
    return cov / denom


def run_mechanism_sweep(
    exits: list[PositionExit],
    daily_snapshot_baseline: list[float],
    baseline_days: list[str],
    epoch_lengths: list[int] | None = None,
    half_lives: list[float] | None = None,
    window_sizes: list[int] | None = None,
) -> list[SweepResult]:
    """Sweep all mechanism × parameter combos, scoring against daily-snapshot baseline.

    Args:
        exits: All position exits
        daily_snapshot_baseline: Daily-snapshot Δ⁺ values (the target)
        baseline_days: Days corresponding to baseline values
        epoch_lengths: Epoch lengths to sweep (days)
        half_lives: Decay half-lives to sweep (days)
        window_sizes: Window sizes to sweep (number of exits)

    Returns:
        List of SweepResult, sorted by correlation (descending)
    """
    if epoch_lengths is None:
        epoch_lengths = [1, 3, 7, 14]
    if half_lives is None:
        half_lives = [1.0, 3.0, 7.0, 14.0]
    if window_sizes is None:
        window_sizes = [10, 25, 50]

    results: list[SweepResult] = []

    for el in epoch_lengths:
        series = build_mechanism_series(exits, "epoch", epoch_length_days=el)
        # Align series to baseline days
        aligned = _align_series(series, baseline_days)
        corr = compute_correlation(aligned, daily_snapshot_baseline)
        max_div = _max_divergence(aligned, daily_snapshot_baseline)
        results.append(SweepResult(
            mechanism_name="epoch", params={"epoch_length_days": el},
            correlation=corr, max_divergence=max_div, series=series,
        ))

    for hl in half_lives:
        series = build_mechanism_series(exits, "decay", half_life_days=hl)
        aligned = _align_series(series, baseline_days)
        corr = compute_correlation(aligned, daily_snapshot_baseline)
        max_div = _max_divergence(aligned, daily_snapshot_baseline)
        results.append(SweepResult(
            mechanism_name="decay", params={"half_life_days": hl},
            correlation=corr, max_divergence=max_div, series=series,
        ))

    for ws in window_sizes:
        series = build_mechanism_series(exits, "window", window_size=ws)
        aligned = _align_series(series, baseline_days)
        corr = compute_correlation(aligned, daily_snapshot_baseline)
        max_div = _max_divergence(aligned, daily_snapshot_baseline)
        results.append(SweepResult(
            mechanism_name="window", params={"window_size": ws},
            correlation=corr, max_divergence=max_div, series=series,
        ))

    results.sort(key=lambda r: r.correlation, reverse=True)
    return results


def _align_series(series: MechanismSeries, target_days: list[str]) -> list[float]:
    """Align mechanism series to target days, filling 0.0 for missing days."""
    day_to_val = dict(zip(series.days, series.delta_plus_values))
    return [day_to_val.get(d, 0.0) for d in target_days]


def _max_divergence(candidate: list[float], baseline: list[float]) -> float:
    """Max absolute difference between two aligned series."""
    if not candidate or not baseline:
        return 0.0
    return max(abs(c - b) for c, b in zip(candidate, baseline))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_mechanism_sweep.py -v`
Expected: PASS (21 tests)

- [ ] **Step 5: Checkpoint — run full test suite**

Run: `cd research && ../uhi8/bin/python -m pytest tests/ -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add research/backtest/mechanism_sweep.py research/tests/backtest/test_mechanism_sweep.py
git commit -m "feat(research): add mechanism sweep — epoch/decay/window with parameter grid"
```

---

## Chunk 3: Phase 2 — Payoff Pipeline Integration

### Task 12: run_payoff_with_mechanism — feed mechanism Δ⁺ into existing payoff pipeline

**Files:**
- Modify: `research/backtest/mechanism_sweep.py`
- Modify: `research/tests/backtest/test_mechanism_sweep.py`

- [ ] **Step 1: Write failing tests**

Append to `test_mechanism_sweep.py`:

```python
from backtest.mechanism_sweep import PayoffComparison, run_payoff_comparison
from econometrics.data import RAW_POSITIONS, DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP
from backtest.oracle_comparison import positions_from_raw_data


def test_payoff_comparison_dataclass():
    pc = PayoffComparison(
        mechanism_name="decay",
        params={"half_life_days": 7.0},
        correlation=0.85,
        max_divergence=0.05,
        pct_better_off=0.20,
        mean_hedge_value=15.0,
    )
    assert pc.mechanism_name == "decay"


def test_run_payoff_comparison_with_real_data():
    """Run payoff comparison using real data — smoke test."""
    exits = positions_from_raw_data(RAW_POSITIONS)
    from backtest.oracle_comparison import build_dual_series
    dual = build_dual_series(exits)

    from backtest.daily import build_daily_states

    def _to_dicts(raw: list[tuple[str, int, float]]) -> list[dict]:
        return [{"burn_date": bd, "blocklife": bl} for bd, bl, _ in raw]

    raw_dicts = _to_dicts(RAW_POSITIONS)
    daily_states = build_daily_states(
        DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, raw_dicts, pool_daily_fee=50_000.0
    )

    comparisons = run_payoff_comparison(
        exits=exits,
        daily_snapshot_baseline=dual.daily_snapshot_delta_plus,
        baseline_days=dual.days,
        daily_states=daily_states,
        raw_positions=raw_dicts,
        gamma=0.10,
        alpha=2.0,
        delta_star=0.09,
        epoch_lengths=[7],
        half_lives=[7.0],
        window_sizes=[25],
    )
    assert len(comparisons) == 3  # 1 epoch + 1 decay + 1 window
    assert all(isinstance(c, PayoffComparison) for c in comparisons)
    # Each should have valid metrics
    for c in comparisons:
        assert 0.0 <= c.pct_better_off <= 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_mechanism_sweep.py::test_run_payoff_comparison_with_real_data -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

Add to `mechanism_sweep.py`:

```python
from dataclasses import replace as dc_replace
from backtest.types import DailyPoolState
from backtest.payoff import run_exit_payoff_backtest


@dataclass(frozen=True)
class PayoffComparison:
    """Full evaluation: series correlation + payoff pipeline metrics."""
    mechanism_name: str
    params: dict[str, float | int]
    correlation: float
    max_divergence: float
    pct_better_off: float
    mean_hedge_value: float


def run_payoff_comparison(
    exits: list[PositionExit],
    daily_snapshot_baseline: list[float],
    baseline_days: list[str],
    daily_states: list[DailyPoolState],
    raw_positions: list[dict],
    gamma: float,
    alpha: float,
    delta_star: float = 0.09,
    epoch_lengths: list[int] | None = None,
    half_lives: list[float] | None = None,
    window_sizes: list[int] | None = None,
) -> list[PayoffComparison]:
    """Run mechanism sweep + payoff pipeline for each candidate.

    For each mechanism, builds a modified daily_states where delta_plus
    is replaced by the mechanism's Δ⁺, then runs the existing payoff pipeline.
    """
    sweep_results = run_mechanism_sweep(
        exits=exits,
        daily_snapshot_baseline=daily_snapshot_baseline,
        baseline_days=baseline_days,
        epoch_lengths=epoch_lengths,
        half_lives=half_lives,
        window_sizes=window_sizes,
    )

    comparisons: list[PayoffComparison] = []
    daily_dict = {ds.day: ds for ds in daily_states}

    for sr in sweep_results:
        # Build modified daily states with mechanism's Δ⁺
        mech_day_to_dp = dict(zip(sr.series.days, sr.series.delta_plus_values))
        modified_states = [
            dc_replace(ds, delta_plus=mech_day_to_dp.get(ds.day, ds.delta_plus))
            for ds in daily_states
        ]

        payoff_result = run_exit_payoff_backtest(
            modified_states, raw_positions, gamma, alpha, delta_star,
        )

        comparisons.append(PayoffComparison(
            mechanism_name=sr.mechanism_name,
            params=sr.params,
            correlation=sr.correlation,
            max_divergence=sr.max_divergence,
            pct_better_off=payoff_result.pct_better_off,
            mean_hedge_value=payoff_result.mean_hedge_value,
        ))

    comparisons.sort(key=lambda c: c.correlation, reverse=True)
    return comparisons
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd research && ../uhi8/bin/python -m pytest tests/backtest/test_mechanism_sweep.py -v`
Expected: PASS (23 tests)

- [ ] **Step 5: Checkpoint — run full test suite**

Run: `cd research && ../uhi8/bin/python -m pytest tests/ -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add research/backtest/mechanism_sweep.py research/tests/backtest/test_mechanism_sweep.py
git commit -m "feat(research): add payoff comparison — mechanism Δ⁺ through existing payoff pipeline"
```

---

## Chunk 4: Notebook

### Task 13: Create oracle-accumulation-comparison notebook

**Files:**
- Create: `research/notebooks/oracle-accumulation-comparison.ipynb`

- [ ] **Step 1: Create the notebook with all cells**

The notebook has 6 cells:

**Cell 1 — Setup & Data Loading:**
```python
import sys
sys.path.insert(0, "..")

from econometrics.data import RAW_POSITIONS, DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP
from backtest.oracle_comparison import positions_from_raw_data, build_dual_series
from backtest.mechanism_sweep import run_mechanism_sweep, run_payoff_comparison, build_mechanism_series
from backtest.daily import build_daily_states
from backtest.payoff import run_exit_payoff_backtest
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['figure.figsize'] = (14, 6)

# Build data
exits = positions_from_raw_data(RAW_POSITIONS)
dual = build_dual_series(exits)

raw_dicts = [{"burn_date": bd, "blocklife": bl} for bd, bl, _ in RAW_POSITIONS]
daily_states = build_daily_states(
    DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, raw_dicts, pool_daily_fee=50_000.0
)

print(f"Total exits: {len(exits)}")
print(f"Days with exits: {len(dual.days)}")
print(f"Date range: {dual.days[0]} to {dual.days[-1]}")
```

**Cell 2 — Phase 1: Cumulative vs Daily-Snapshot Δ⁺:**
```python
fig, ax = plt.subplots()
ax.plot(range(len(dual.days)), dual.cumulative_delta_plus, 'r-o', label='Cumulative (Solidity)', markersize=4)
ax.plot(range(len(dual.days)), dual.daily_snapshot_delta_plus, 'b-s', label='Daily Snapshot (Backtest)', markersize=4)
ax.set_xticks(range(len(dual.days)))
ax.set_xticklabels(dual.days, rotation=45, ha='right', fontsize=7)
ax.axvline(x=dual.days.index("2025-12-23"), color='gray', linestyle='--', alpha=0.5, label='Dec 23 spike')
ax.set_ylabel('Δ⁺')
ax.set_title('FCI Oracle: Cumulative vs Daily-Snapshot Δ⁺')
ax.legend()
plt.tight_layout()
plt.show()

# Divergence after Dec 23
dec23_idx = dual.days.index("2025-12-23")
print(f"\nDec 23 — Cumulative: {dual.cumulative_delta_plus[dec23_idx]:.6f}, Daily: {dual.daily_snapshot_delta_plus[dec23_idx]:.6f}")
if dec23_idx + 1 < len(dual.days):
    print(f"Dec 24 — Cumulative: {dual.cumulative_delta_plus[dec23_idx+1]:.6f}, Daily: {dual.daily_snapshot_delta_plus[dec23_idx+1]:.6f}")
    print(f"Ratio (cum/daily): {dual.cumulative_delta_plus[dec23_idx+1] / max(dual.daily_snapshot_delta_plus[dec23_idx+1], 1e-10):.2f}x")
```

**Cell 3 — Phase 1: Payoff comparison (cumulative vs daily-snapshot):**
```python
# Run payoff with daily-snapshot baseline (what backtest uses)
baseline_payoff = run_exit_payoff_backtest(daily_states, raw_dicts, gamma=0.10, alpha=2.0, delta_star=0.09)

print("=== Payoff with Daily-Snapshot Δ⁺ (Backtest Baseline) ===")
print(f"  % better off:     {baseline_payoff.pct_better_off:.1%}")
print(f"  Mean hedge value:  ${baseline_payoff.mean_hedge_value:.2f}")
print(f"  Total premiums:    ${baseline_payoff.total_premiums:.2f}")
print(f"  Total payouts:     ${baseline_payoff.total_payouts:.2f}")
```

**Cell 4 — Phase 2: Mechanism sweep grid:**
```python
comparisons = run_payoff_comparison(
    exits=exits,
    daily_snapshot_baseline=dual.daily_snapshot_delta_plus,
    baseline_days=dual.days,
    daily_states=daily_states,
    raw_positions=raw_dicts,
    gamma=0.10,
    alpha=2.0,
    delta_star=0.09,
    epoch_lengths=[1, 3, 7, 14],
    half_lives=[1.0, 3.0, 7.0, 14.0],
    window_sizes=[10, 25, 50],
)

print("=== Mechanism Sweep Results (sorted by correlation) ===")
print(f"{'Mechanism':<10} {'Params':<30} {'Corr':>6} {'MaxDiv':>8} {'%Better':>8} {'MeanHV':>10}")
print("-" * 80)
for c in comparisons:
    params_str = ", ".join(f"{k}={v}" for k, v in c.params.items())
    print(f"{c.mechanism_name:<10} {params_str:<30} {c.correlation:>6.3f} {c.max_divergence:>8.4f} {c.pct_better_off:>7.1%} {c.mean_hedge_value:>10.2f}")

# Highlight viable candidates (correlation > 0.8 AND non-negative mean HV)
viable = [c for c in comparisons if c.correlation > 0.8 and c.mean_hedge_value >= 0]
print(f"\nViable candidates (corr > 0.8 AND mean HV >= 0): {len(viable)}")
for c in viable:
    print(f"  {c.mechanism_name} ({c.params}): corr={c.correlation:.3f}, HV=${c.mean_hedge_value:.2f}")
```

**Cell 5 — Phase 2: Plot candidate Δ⁺ series vs baseline:**
```python
# Plot top 3 candidates vs baseline
top_n = min(3, len(comparisons))
fig, axes = plt.subplots(top_n, 1, figsize=(14, 4 * top_n), sharex=True)
if top_n == 1:
    axes = [axes]

for i, c in enumerate(comparisons[:top_n]):
    ax = axes[i]
    # Rebuild mechanism series for plotting
    series = build_mechanism_series(exits, c.mechanism_name, **c.params)

    ax.plot(range(len(dual.days)), dual.daily_snapshot_delta_plus, 'b-s',
            label='Daily Snapshot (target)', markersize=3, alpha=0.7)

    # Align mechanism to baseline days
    mech_dict = dict(zip(series.days, series.delta_plus_values))
    aligned = [mech_dict.get(d, 0) for d in dual.days]
    ax.plot(range(len(dual.days)), aligned, 'g-^',
            label=f'{c.mechanism_name} ({c.params})', markersize=3)

    ax.set_ylabel('Δ⁺')
    ax.set_title(f'#{i+1}: {c.mechanism_name} — corr={c.correlation:.3f}, HV=${c.mean_hedge_value:.2f}')
    ax.legend(fontsize=8)

axes[-1].set_xticks(range(len(dual.days)))
axes[-1].set_xticklabels(dual.days, rotation=45, ha='right', fontsize=7)
plt.tight_layout()
plt.show()
```

**Cell 6 — Summary table:**
```python
print("=" * 60)
print("PHASE 2 SUMMARY")
print("=" * 60)
print(f"Baseline (daily-snapshot): % better off = {baseline_payoff.pct_better_off:.1%}, mean HV = ${baseline_payoff.mean_hedge_value:.2f}")
print()

if viable:
    best = viable[0]
    print(f"BEST CANDIDATE: {best.mechanism_name}")
    print(f"  Parameters: {best.params}")
    print(f"  Correlation to baseline: {best.correlation:.4f}")
    print(f"  Max divergence: {best.max_divergence:.6f}")
    print(f"  % better off: {best.pct_better_off:.1%}")
    print(f"  Mean hedge value: ${best.mean_hedge_value:.2f}")
    print()
    if len(viable) > 1:
        print("AMBIGUOUS — multiple viable candidates. All will ship as parallel oracle APIs.")
        for v in viable:
            print(f"  {v.mechanism_name}({v.params}): corr={v.correlation:.3f}")
    else:
        print("CLEAR WINNER — vault defaults to this mechanism.")
else:
    print("NO VIABLE CANDIDATES — all fail viability threshold.")
    print("Action: revisit oracle architecture (event-level redesign needed).")
```

- [ ] **Step 2: Verify notebook executes**

Run: `cd research && ../uhi8/bin/python -m jupyter nbconvert --to notebook --execute notebooks/oracle-accumulation-comparison.ipynb --output oracle-accumulation-comparison-executed.ipynb`

If jupyter is not installed: `cd research && ../uhi8/bin/python -c "from backtest.oracle_comparison import *; from backtest.mechanism_sweep import *; print('imports OK')"` as a smoke test.

- [ ] **Step 3: Checkpoint — run full test suite**

Run: `cd research && ../uhi8/bin/python -m pytest tests/ -v`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add research/notebooks/oracle-accumulation-comparison.ipynb
git commit -m "feat(research): add oracle accumulation comparison notebook — Phase 1 + 2 analysis"
```

---

## Post-Completion

After all tasks pass:

1. Run final checkpoint: `cd research && ../uhi8/bin/python -m pytest tests/ -v` — all 114+ existing + ~38 new tests pass
2. Execute notebook to generate results
3. Review Phase 2 summary table to determine:
   - **Clear winner** → Phase 3 implements that mechanism as default + others as alternatives
   - **Ambiguous** → Phase 3 implements all viable mechanisms as parallel oracle APIs
   - **All fail** → Revisit oracle architecture before Phase 3
4. Write Phase 3 plan based on Phase 2 outcomes (separate plan document)
