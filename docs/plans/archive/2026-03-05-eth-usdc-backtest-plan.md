# ETH/USDC Backtest Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Compare actual PLP P&L against counterfactual hedged P&L using ThetaSwap's insurance mechanism on ETH/USDC 30bps historical data.

**Architecture:** Pool-level reserve simulation (determines when donate() fires and how much) + position-level P&L attribution (shows per-position hedge value). Sweep gamma in {0.01, 0.05, 0.10, 0.20, gamma*} where gamma* is derived from the $110 econometric WTP. All data from existing `econometrics/data.py` — no new Dune queries.

**Tech Stack:** Python 3.14, uhi8 venv, pytest, frozen dataclasses, pure functions (@functional-python). matplotlib for plots. Jupyter notebook for results.

**Design doc:** `docs/plans/2026-03-05-eth-usdc-backtest-design.md`

**Test runner:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/uhi8/bin/python -m pytest`

---

### Task 1: Types

**Files:**
- Create: `backtest/__init__.py`
- Create: `backtest/types.py`
- Create: `tests/backtest/__init__.py`
- Create: `tests/backtest/test_types.py`

**Step 1: Write the failing test**

Create `tests/backtest/__init__.py` (empty) and `tests/backtest/test_types.py`:

```python
"""Tests for backtest domain types."""
from __future__ import annotations


def test_daily_pool_state_frozen() -> None:
    from backtest.types import DailyPoolState
    s = DailyPoolState(
        day="2025-12-05",
        a_t_real=0.027,
        a_t_null=0.008,
        delta_plus=0.019,
        il=0.012,
        n_positions=13,
        pool_daily_fee=50_000.0,
    )
    assert s.delta_plus == 0.019
    assert s.day == "2025-12-05"
    try:
        s.day = "X"  # type: ignore
        assert False, "should be frozen"
    except AttributeError:
        pass


def test_reserve_state_frozen() -> None:
    from backtest.types import ReserveState
    s = ReserveState(
        day="2025-12-05",
        balance=1000.0,
        premium_in=100.0,
        payout_out=0.0,
        trigger_fired=False,
        delta_plus=0.05,
        donate_amount=0.0,
    )
    assert s.balance == 1000.0
    assert not s.trigger_fired


def test_position_pnl_frozen() -> None:
    from backtest.types import PositionPnL
    p = PositionPnL(
        position_idx=0,
        burn_date="2025-12-10",
        blocklife=5000,
        alive_days=5,
        fees_earned=250.0,
        il_cost=30.0,
        premium_paid=25.0,
        payouts_received=40.0,
        pnl_unhedged=220.0,
        pnl_hedged=235.0,
        hedge_value=15.0,
    )
    assert p.hedge_value == 15.0


def test_backtest_result_frozen() -> None:
    from backtest.types import BacktestResult
    r = BacktestResult(
        gamma=0.10,
        total_premiums=5000.0,
        total_payouts=3000.0,
        trigger_days=3,
        mean_hedge_value=15.0,
        median_hedge_value=12.0,
        pct_better_off=0.65,
        reserve_peak=8000.0,
        reserve_utilization=0.375,
        position_pnls=[],
        reserve_states=[],
    )
    assert r.gamma == 0.10
    assert r.pct_better_off == 0.65
```

**Step 2: Run test to verify it fails**

Run: `uhi8/bin/python -m pytest tests/backtest/test_types.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backtest'`

**Step 3: Write minimal implementation**

Create `backtest/__init__.py` (empty) and `backtest/types.py`:

```python
"""Domain types for historical backtest — frozen dataclasses, pure @functional-python."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DailyPoolState:
    """Pool-level state for one day."""
    day: str
    a_t_real: float
    a_t_null: float
    delta_plus: float  # max(0, a_t_real - a_t_null)
    il: float
    n_positions: int  # alive positions on this day
    pool_daily_fee: float  # total pool fee revenue this day (USDC)


@dataclass(frozen=True)
class ReserveState:
    """Insurance reserve state after processing one day."""
    day: str
    balance: float  # R(t) after premium collection and payout
    premium_in: float  # premium collected this day
    payout_out: float  # payout distributed this day
    trigger_fired: bool  # Delta_plus > Delta_star
    delta_plus: float
    donate_amount: float  # D before min(D, R) cap


@dataclass(frozen=True)
class PositionPnL:
    """P&L for one position under a specific gamma."""
    position_idx: int
    burn_date: str
    blocklife: int
    alive_days: int
    fees_earned: float  # total fees at 1/N share
    il_cost: float  # total IL
    premium_paid: float  # gamma * fees_earned
    payouts_received: float  # sum of pro-rata donate()
    pnl_unhedged: float  # fees - IL
    pnl_hedged: float  # (1-gamma)*fees - IL + payouts
    hedge_value: float  # pnl_hedged - pnl_unhedged


@dataclass(frozen=True)
class BacktestResult:
    """Aggregate result for one gamma value."""
    gamma: float
    total_premiums: float
    total_payouts: float
    trigger_days: int
    mean_hedge_value: float
    median_hedge_value: float
    pct_better_off: float  # fraction of positions with hedge_value > 0
    reserve_peak: float
    reserve_utilization: float  # total_payouts / reserve_peak
    position_pnls: list[PositionPnL]
    reserve_states: list[ReserveState]
```

**Step 4: Run test to verify it passes**

Run: `uhi8/bin/python -m pytest tests/backtest/test_types.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add -f backtest/__init__.py backtest/types.py tests/backtest/__init__.py tests/backtest/test_types.py
git commit -m "feat(backtest): add domain types for historical PLP backtest"
```

---

### Task 2: Daily Pool State Builder

**Files:**
- Create: `backtest/daily.py`
- Create: `tests/backtest/test_daily.py`

**Step 1: Write the failing test**

```python
"""Tests for daily pool state builder."""
from __future__ import annotations


def test_build_daily_states_length() -> None:
    from backtest.daily import build_daily_states
    at_map = {"2025-12-05": 0.027, "2025-12-06": 0.002}
    null_map = {"2025-12-05": 0.008, "2025-12-06": 0.001}
    il_map = {"2025-12-05": 0.012, "2025-12-06": 0.009}
    positions = [("2025-12-06", 1000, 0.1)]  # 1 position burns on 12-06

    states = build_daily_states(at_map, null_map, il_map, positions, pool_daily_fee=50_000.0)
    assert len(states) == 2


def test_build_daily_states_delta_plus_clamped() -> None:
    from backtest.daily import build_daily_states
    # null > real => delta_plus = 0
    at_map = {"2025-12-05": 0.001}
    null_map = {"2025-12-05": 0.010}
    il_map = {"2025-12-05": 0.012}
    positions = [("2025-12-06", 7200, 0.1)]  # alive on 12-05

    states = build_daily_states(at_map, null_map, il_map, positions, pool_daily_fee=50_000.0)
    assert states[0].delta_plus == 0.0


def test_build_daily_states_n_positions_counts_alive() -> None:
    from backtest.daily import build_daily_states
    at_map = {"2025-12-05": 0.027, "2025-12-06": 0.002}
    null_map = {"2025-12-05": 0.008, "2025-12-06": 0.001}
    il_map = {"2025-12-05": 0.012, "2025-12-06": 0.009}
    # pos0: burns 12-05, blocklife=7200 => mint ~12-04, alive on 12-05 only
    # pos1: burns 12-06, blocklife=14400 => mint ~12-04, alive on 12-05 and 12-06
    positions = [("2025-12-05", 7200, 0.1), ("2025-12-06", 14400, 0.1)]

    states = build_daily_states(at_map, null_map, il_map, positions, pool_daily_fee=50_000.0)
    assert states[0].n_positions == 2  # both alive on 12-05
    assert states[1].n_positions == 1  # only pos1 alive on 12-06
```

**Step 2: Run test to verify it fails**

Run: `uhi8/bin/python -m pytest tests/backtest/test_daily.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `backtest/daily.py`:

```python
"""Build daily pool state from existing econometrics data."""
from __future__ import annotations

from datetime import date, timedelta

from backtest.types import DailyPoolState

BLOCKS_PER_DAY: float = 7200.0


def _approximate_mint_date(burn_date: str, blocklife: int) -> str:
    burn = date.fromisoformat(burn_date)
    days = int(blocklife / BLOCKS_PER_DAY)
    mint = burn - timedelta(days=days)
    return mint.isoformat()


def _position_alive_on(day: str, burn_date: str, blocklife: int) -> bool:
    d = date.fromisoformat(day)
    burn_d = date.fromisoformat(burn_date)
    mint_d = date.fromisoformat(_approximate_mint_date(burn_date, blocklife))
    return mint_d <= d <= burn_d


def build_daily_states(
    daily_at_map: dict[str, float],
    daily_at_null_map: dict[str, float],
    il_map: dict[str, float],
    raw_positions: list[tuple[str, int, float]],
    pool_daily_fee: float = 50_000.0,
) -> list[DailyPoolState]:
    """Build sorted list of DailyPoolState from existing data maps."""
    sorted_days = sorted(daily_at_map.keys())
    states: list[DailyPoolState] = []
    for day in sorted_days:
        a_t_real = daily_at_map[day]
        a_t_null = daily_at_null_map.get(day, 0.0)
        delta_plus = max(0.0, a_t_real - a_t_null)
        il = il_map.get(day, 0.0)
        n_alive = sum(
            1 for burn_date, blocklife, _ in raw_positions
            if blocklife > 1 and _position_alive_on(day, burn_date, blocklife)
        )
        states.append(DailyPoolState(
            day=day,
            a_t_real=a_t_real,
            a_t_null=a_t_null,
            delta_plus=delta_plus,
            il=il,
            n_positions=max(1, n_alive),
            pool_daily_fee=pool_daily_fee,
        ))
    return states
```

**Step 4: Run test to verify it passes**

Run: `uhi8/bin/python -m pytest tests/backtest/test_daily.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add -f backtest/daily.py tests/backtest/test_daily.py
git commit -m "feat(backtest): daily pool state builder from existing data"
```

---

### Task 3: Reserve Simulation

**Files:**
- Create: `backtest/reserve.py`
- Create: `tests/backtest/test_reserve.py`

**Step 1: Write the failing test**

```python
"""Tests for reserve simulation (INS-01 through INS-05)."""
from __future__ import annotations

from backtest.types import DailyPoolState, ReserveState


def _make_states() -> list[DailyPoolState]:
    """3 days: day 1 below trigger, day 2 above trigger, day 3 below."""
    return [
        DailyPoolState(day="2025-12-05", a_t_real=0.05, a_t_null=0.04,
                        delta_plus=0.01, il=0.01, n_positions=10, pool_daily_fee=50_000.0),
        DailyPoolState(day="2025-12-06", a_t_real=0.15, a_t_null=0.04,
                        delta_plus=0.11, il=0.01, n_positions=10, pool_daily_fee=50_000.0),
        DailyPoolState(day="2025-12-07", a_t_real=0.05, a_t_null=0.04,
                        delta_plus=0.01, il=0.01, n_positions=8, pool_daily_fee=50_000.0),
    ]


def test_reserve_no_trigger_no_payout() -> None:
    from backtest.reserve import simulate_reserve
    states = [_make_states()[0]]  # only below-trigger day
    # 2 positions exit on day 1, each earning 50000/10 = 5000, premium = 0.10 * 5000 = 500
    exits_per_day = {"2025-12-05": 2}
    result = simulate_reserve(states, exits_per_day, gamma=0.10, delta_star=0.09)
    assert len(result) == 1
    assert result[0].balance == 2 * 0.10 * 5000.0  # 1000
    assert result[0].payout_out == 0.0
    assert not result[0].trigger_fired


def test_reserve_trigger_fires_and_pays() -> None:
    from backtest.reserve import simulate_reserve
    states = _make_states()
    # 5 positions exit on day 1 (builds reserve), trigger on day 2
    exits_per_day = {"2025-12-05": 5, "2025-12-06": 0, "2025-12-07": 0}
    result = simulate_reserve(states, exits_per_day, gamma=0.10, delta_star=0.09)
    # Day 1: premium = 5 * 0.10 * (50000/10) = 2500, no trigger
    assert result[0].balance == 2500.0
    # Day 2: delta_plus = 0.11 > 0.09, D = (0.11-0.09)/(1-0.09) * 2500
    expected_d = (0.11 - 0.09) / (1.0 - 0.09) * 2500.0
    assert result[1].trigger_fired
    assert abs(result[1].donate_amount - expected_d) < 0.01
    assert result[1].balance == 2500.0 - min(expected_d, 2500.0)


def test_reserve_solvency_ins01() -> None:
    """INS-01: R(t) >= 0 at all times."""
    from backtest.reserve import simulate_reserve
    states = _make_states()
    exits_per_day = {"2025-12-05": 1, "2025-12-06": 0, "2025-12-07": 0}
    result = simulate_reserve(states, exits_per_day, gamma=0.10, delta_star=0.09)
    for r in result:
        assert r.balance >= 0.0, f"INS-01 violated on {r.day}: R={r.balance}"
```

**Step 2: Run test to verify it fails**

Run: `uhi8/bin/python -m pytest tests/backtest/test_reserve.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `backtest/reserve.py`:

```python
"""Reserve simulation following main.pdf §6 (INS-01 through INS-05)."""
from __future__ import annotations

from backtest.types import DailyPoolState, ReserveState


def simulate_reserve(
    daily_states: list[DailyPoolState],
    exits_per_day: dict[str, int],
    gamma: float,
    delta_star: float = 0.09,
) -> list[ReserveState]:
    """Simulate per-pool insurance reserve R(t) day by day.

    Args:
        daily_states: sorted daily pool states.
        exits_per_day: day -> count of positions exiting that day.
        gamma: premium factor in (0, 1).
        delta_star: trigger threshold (econometric turning point).

    Returns:
        One ReserveState per day.
    """
    balance = 0.0
    results: list[ReserveState] = []

    for state in daily_states:
        # 1. Premium collection from exiting positions (§6.1)
        n_exits = exits_per_day.get(state.day, 0)
        fee_per_position = state.pool_daily_fee / state.n_positions
        premium_in = n_exits * gamma * fee_per_position
        balance += premium_in

        # 2. Trigger check and donate (INS-03, §6.2 eq 16)
        trigger = state.delta_plus > delta_star
        donate_amount = 0.0
        payout_out = 0.0
        if trigger and balance > 0.0:
            fraction = (state.delta_plus - delta_star) / (1.0 - delta_star)
            donate_amount = fraction * balance
            payout_out = min(donate_amount, balance)  # INS-01 solvency
            balance -= payout_out

        results.append(ReserveState(
            day=state.day,
            balance=balance,
            premium_in=premium_in,
            payout_out=payout_out,
            trigger_fired=trigger,
            delta_plus=state.delta_plus,
            donate_amount=donate_amount,
        ))

    return results
```

**Step 4: Run test to verify it passes**

Run: `uhi8/bin/python -m pytest tests/backtest/test_reserve.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add -f backtest/reserve.py tests/backtest/test_reserve.py
git commit -m "feat(backtest): reserve simulation with INS-01 solvency"
```

---

### Task 4: Position-Level P&L

**Files:**
- Create: `backtest/pnl.py`
- Create: `tests/backtest/test_pnl.py`

**Step 1: Write the failing test**

```python
"""Tests for position-level P&L computation."""
from __future__ import annotations

from backtest.types import DailyPoolState, ReserveState, PositionPnL


def _make_daily_states() -> list[DailyPoolState]:
    return [
        DailyPoolState(day="2025-12-05", a_t_real=0.05, a_t_null=0.04,
                        delta_plus=0.01, il=0.01, n_positions=10, pool_daily_fee=50_000.0),
        DailyPoolState(day="2025-12-06", a_t_real=0.15, a_t_null=0.04,
                        delta_plus=0.11, il=0.02, n_positions=10, pool_daily_fee=50_000.0),
    ]


def _make_reserve_states() -> list[ReserveState]:
    return [
        ReserveState(day="2025-12-05", balance=1000.0, premium_in=1000.0,
                     payout_out=0.0, trigger_fired=False, delta_plus=0.01, donate_amount=0.0),
        ReserveState(day="2025-12-06", balance=978.0, premium_in=0.0,
                     payout_out=22.0, trigger_fired=True, delta_plus=0.11, donate_amount=22.0),
    ]


def test_compute_position_pnl_unhedged() -> None:
    from backtest.pnl import compute_position_pnl
    daily = {s.day: s for s in _make_daily_states()}
    reserves = {s.day: s for s in _make_reserve_states()}
    # position alive both days, burns on 12-06
    pnl = compute_position_pnl(
        position_idx=0, burn_date="2025-12-06", blocklife=14400,
        daily_states=daily, reserve_states=reserves, gamma=0.10,
    )
    # fees = (50000/10) + (50000/10) = 10000
    # il = 0.01 + 0.02 = 0.03
    assert abs(pnl.fees_earned - 10_000.0) < 0.01
    assert abs(pnl.pnl_unhedged - (10_000.0 - 0.03)) < 0.01


def test_compute_position_pnl_hedged_gets_payout() -> None:
    from backtest.pnl import compute_position_pnl
    daily = {s.day: s for s in _make_daily_states()}
    reserves = {s.day: s for s in _make_reserve_states()}
    pnl = compute_position_pnl(
        position_idx=0, burn_date="2025-12-06", blocklife=14400,
        daily_states=daily, reserve_states=reserves, gamma=0.10,
    )
    # premium = 0.10 * 10000 = 1000
    # payout = 22.0 / 10 (pro-rata) = 2.2
    # hedged = (1-0.10)*10000 - 0.03 + 2.2 = 9002.17
    assert pnl.premium_paid == 1000.0
    assert abs(pnl.payouts_received - 2.2) < 0.01
    assert pnl.hedge_value == pnl.pnl_hedged - pnl.pnl_unhedged


def test_compute_position_pnl_not_alive_on_trigger_day() -> None:
    from backtest.pnl import compute_position_pnl
    daily = {s.day: s for s in _make_daily_states()}
    reserves = {s.day: s for s in _make_reserve_states()}
    # position burns on 12-05, not alive on 12-06 trigger day
    pnl = compute_position_pnl(
        position_idx=1, burn_date="2025-12-05", blocklife=7200,
        daily_states=daily, reserve_states=reserves, gamma=0.10,
    )
    assert pnl.payouts_received == 0.0  # not alive on trigger day
```

**Step 2: Run test to verify it fails**

Run: `uhi8/bin/python -m pytest tests/backtest/test_pnl.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `backtest/pnl.py`:

```python
"""Position-level P&L: unhedged vs hedged(gamma)."""
from __future__ import annotations

from datetime import date, timedelta

from backtest.types import DailyPoolState, PositionPnL, ReserveState

BLOCKS_PER_DAY: float = 7200.0


def _approximate_mint_date(burn_date: str, blocklife: int) -> str:
    burn = date.fromisoformat(burn_date)
    days = int(blocklife / BLOCKS_PER_DAY)
    return (burn - timedelta(days=days)).isoformat()


def compute_position_pnl(
    position_idx: int,
    burn_date: str,
    blocklife: int,
    daily_states: dict[str, DailyPoolState],
    reserve_states: dict[str, ReserveState],
    gamma: float,
) -> PositionPnL:
    """Compute unhedged and hedged P&L for one position."""
    mint_date = _approximate_mint_date(burn_date, blocklife)
    mint_d = date.fromisoformat(mint_date)
    burn_d = date.fromisoformat(burn_date)

    fees_earned = 0.0
    il_cost = 0.0
    payouts_received = 0.0
    alive_days = 0

    sorted_days = sorted(daily_states.keys())
    for day_str in sorted_days:
        d = date.fromisoformat(day_str)
        if d < mint_d or d > burn_d:
            continue

        state = daily_states[day_str]
        alive_days += 1

        # Fee income: passive share = 1/N
        fee_per_position = state.pool_daily_fee / state.n_positions
        fees_earned += fee_per_position

        # IL cost
        il_cost += state.il

        # Pro-rata payout on trigger days
        rs = reserve_states.get(day_str)
        if rs is not None and rs.trigger_fired and rs.payout_out > 0.0:
            payouts_received += rs.payout_out / state.n_positions

    premium_paid = gamma * fees_earned
    pnl_unhedged = fees_earned - il_cost
    pnl_hedged = (1.0 - gamma) * fees_earned - il_cost + payouts_received
    hedge_value = pnl_hedged - pnl_unhedged

    return PositionPnL(
        position_idx=position_idx,
        burn_date=burn_date,
        blocklife=blocklife,
        alive_days=alive_days,
        fees_earned=fees_earned,
        il_cost=il_cost,
        premium_paid=premium_paid,
        payouts_received=payouts_received,
        pnl_unhedged=pnl_unhedged,
        pnl_hedged=pnl_hedged,
        hedge_value=hedge_value,
    )
```

**Step 4: Run test to verify it passes**

Run: `uhi8/bin/python -m pytest tests/backtest/test_pnl.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add -f backtest/pnl.py tests/backtest/test_pnl.py
git commit -m "feat(backtest): position-level P&L with hedge value"
```

---

### Task 5: Gamma Calibration

**Files:**
- Create: `backtest/calibrate.py`
- Create: `tests/backtest/test_calibrate.py`

**Step 1: Write the failing test**

```python
"""Tests for econometric gamma* calibration."""
from __future__ import annotations


def test_derive_gamma_star_basic() -> None:
    from backtest.calibrate import derive_gamma_star
    # WTP = $110, avg fees = $1100 => gamma* = 0.10
    gamma_star = derive_gamma_star(wtp=110.0, avg_fees=1100.0)
    assert abs(gamma_star - 0.10) < 1e-6


def test_derive_gamma_star_bounded() -> None:
    from backtest.calibrate import derive_gamma_star
    # WTP > avg_fees => gamma* capped at 1.0
    gamma_star = derive_gamma_star(wtp=5000.0, avg_fees=100.0)
    assert gamma_star <= 1.0


def test_derive_gamma_star_zero_fees() -> None:
    from backtest.calibrate import derive_gamma_star
    gamma_star = derive_gamma_star(wtp=110.0, avg_fees=0.0)
    assert gamma_star == 1.0  # edge case: no fees => max gamma


def test_compute_avg_fees_from_positions() -> None:
    from backtest.calibrate import compute_avg_fees
    from backtest.types import PositionPnL
    pnls = [
        PositionPnL(0, "d", 100, 5, 1000.0, 10.0, 100.0, 0.0, 990.0, 890.0, -100.0),
        PositionPnL(1, "d", 100, 5, 2000.0, 10.0, 200.0, 0.0, 1990.0, 1790.0, -200.0),
    ]
    avg = compute_avg_fees(pnls)
    assert abs(avg - 1500.0) < 0.01
```

**Step 2: Run test to verify it fails**

Run: `uhi8/bin/python -m pytest tests/backtest/test_calibrate.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `backtest/calibrate.py`:

```python
"""Econometric gamma* calibration from WTP."""
from __future__ import annotations

from backtest.types import PositionPnL


def derive_gamma_star(wtp: float, avg_fees: float) -> float:
    """Derive gamma* such that expected premium = WTP.

    gamma* = WTP / avg_fees_earned_per_position.
    Capped at 1.0.
    """
    if avg_fees <= 0.0:
        return 1.0
    return min(wtp / avg_fees, 1.0)


def compute_avg_fees(position_pnls: list[PositionPnL]) -> float:
    """Average fees earned across positions."""
    if not position_pnls:
        return 0.0
    return sum(p.fees_earned for p in position_pnls) / len(position_pnls)
```

**Step 4: Run test to verify it passes**

Run: `uhi8/bin/python -m pytest tests/backtest/test_calibrate.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add -f backtest/calibrate.py tests/backtest/test_calibrate.py
git commit -m "feat(backtest): gamma* calibration from econometric WTP"
```

---

### Task 6: Gamma Sweep Orchestrator

**Files:**
- Create: `backtest/sweep.py`
- Create: `tests/backtest/test_sweep.py`

**Step 1: Write the failing test**

```python
"""Tests for gamma sweep orchestrator."""
from __future__ import annotations

from backtest.types import DailyPoolState


def _make_daily_states() -> list[DailyPoolState]:
    return [
        DailyPoolState("2025-12-05", 0.05, 0.04, 0.01, 0.01, 10, 50_000.0),
        DailyPoolState("2025-12-06", 0.15, 0.04, 0.11, 0.02, 10, 50_000.0),
        DailyPoolState("2025-12-07", 0.05, 0.04, 0.01, 0.01, 8, 50_000.0),
    ]


def test_run_single_backtest_returns_result() -> None:
    from backtest.sweep import run_single_backtest
    positions = [
        ("2025-12-06", 14400, 0.1),  # alive 12-04..12-06
        ("2025-12-07", 14400, 0.1),  # alive 12-05..12-07
    ]
    result = run_single_backtest(
        daily_states=_make_daily_states(),
        raw_positions=positions,
        gamma=0.10,
        delta_star=0.09,
    )
    assert result.gamma == 0.10
    assert result.trigger_days >= 0
    assert len(result.position_pnls) == 2
    assert len(result.reserve_states) == 3


def test_run_gamma_sweep_multiple() -> None:
    from backtest.sweep import run_gamma_sweep
    positions = [("2025-12-06", 14400, 0.1)]
    states = _make_daily_states()
    results = run_gamma_sweep(
        daily_states=states,
        raw_positions=positions,
        gammas=[0.01, 0.10, 0.20],
        delta_star=0.09,
    )
    assert len(results) == 3
    assert results[0].gamma == 0.01
    assert results[2].gamma == 0.20


def test_higher_gamma_more_premium_paid() -> None:
    from backtest.sweep import run_gamma_sweep
    positions = [("2025-12-06", 14400, 0.1), ("2025-12-07", 14400, 0.1)]
    states = _make_daily_states()
    results = run_gamma_sweep(states, positions, gammas=[0.01, 0.20], delta_star=0.09)
    assert results[1].total_premiums > results[0].total_premiums
```

**Step 2: Run test to verify it fails**

Run: `uhi8/bin/python -m pytest tests/backtest/test_sweep.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `backtest/sweep.py`:

```python
"""Gamma sweep orchestrator: runs full backtest at each gamma."""
from __future__ import annotations

from collections import Counter
from statistics import median

from backtest.daily import build_daily_states
from backtest.pnl import compute_position_pnl
from backtest.reserve import simulate_reserve
from backtest.types import BacktestResult, DailyPoolState


def run_single_backtest(
    daily_states: list[DailyPoolState],
    raw_positions: list[tuple[str, int, float]],
    gamma: float,
    delta_star: float = 0.09,
) -> BacktestResult:
    """Run one backtest at a specific gamma."""
    # Count exits per day
    exits_per_day: dict[str, int] = Counter()
    for burn_date, blocklife, _ in raw_positions:
        if blocklife > 1:
            exits_per_day[burn_date] += 1

    # Simulate reserve
    reserve_states = simulate_reserve(daily_states, dict(exits_per_day), gamma, delta_star)
    reserve_map = {rs.day: rs for rs in reserve_states}
    daily_map = {ds.day: ds for ds in daily_states}

    # Compute per-position P&L
    position_pnls = [
        compute_position_pnl(idx, burn_date, blocklife, daily_map, reserve_map, gamma)
        for idx, (burn_date, blocklife, _) in enumerate(raw_positions)
        if blocklife > 1
    ]

    # Aggregate
    hedge_values = [p.hedge_value for p in position_pnls]
    total_premiums = sum(p.premium_paid for p in position_pnls)
    total_payouts = sum(rs.payout_out for rs in reserve_states)
    trigger_days = sum(1 for rs in reserve_states if rs.trigger_fired)
    reserve_peak = max((rs.balance for rs in reserve_states), default=0.0)

    return BacktestResult(
        gamma=gamma,
        total_premiums=total_premiums,
        total_payouts=total_payouts,
        trigger_days=trigger_days,
        mean_hedge_value=sum(hedge_values) / len(hedge_values) if hedge_values else 0.0,
        median_hedge_value=median(hedge_values) if hedge_values else 0.0,
        pct_better_off=sum(1 for h in hedge_values if h > 0) / len(hedge_values) if hedge_values else 0.0,
        reserve_peak=reserve_peak,
        reserve_utilization=total_payouts / reserve_peak if reserve_peak > 0 else 0.0,
        position_pnls=position_pnls,
        reserve_states=reserve_states,
    )


def run_gamma_sweep(
    daily_states: list[DailyPoolState],
    raw_positions: list[tuple[str, int, float]],
    gammas: list[float],
    delta_star: float = 0.09,
) -> list[BacktestResult]:
    """Run backtest at each gamma value."""
    return [
        run_single_backtest(daily_states, raw_positions, g, delta_star)
        for g in gammas
    ]
```

**Step 4: Run test to verify it passes**

Run: `uhi8/bin/python -m pytest tests/backtest/test_sweep.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add -f backtest/sweep.py tests/backtest/test_sweep.py
git commit -m "feat(backtest): gamma sweep orchestrator"
```

---

### Task 7: Plotting Functions

**Files:**
- Create: `backtest/plotting.py`
- Create: `tests/backtest/test_plotting.py`

**Step 1: Write the failing test**

```python
"""Tests for backtest plotting (smoke tests — verify figures are created)."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # non-interactive backend

from backtest.types import DailyPoolState, ReserveState, BacktestResult, PositionPnL


def _make_result() -> BacktestResult:
    rs = [
        ReserveState("2025-12-05", 1000.0, 1000.0, 0.0, False, 0.01, 0.0),
        ReserveState("2025-12-06", 978.0, 0.0, 22.0, True, 0.11, 22.0),
    ]
    pnls = [
        PositionPnL(0, "2025-12-06", 14400, 2, 10000.0, 0.03, 1000.0, 2.2,
                     9999.97, 9002.17, -997.8),
    ]
    return BacktestResult(
        gamma=0.10, total_premiums=1000.0, total_payouts=22.0, trigger_days=1,
        mean_hedge_value=-997.8, median_hedge_value=-997.8, pct_better_off=0.0,
        reserve_peak=1000.0, reserve_utilization=0.022,
        position_pnls=pnls, reserve_states=rs,
    )


def test_money_plot_returns_figure() -> None:
    from backtest.plotting import money_plot
    fig = money_plot([_make_result()])
    assert fig is not None
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_reserve_plot_returns_figure() -> None:
    from backtest.plotting import reserve_plot
    fig = reserve_plot(_make_result())
    assert fig is not None
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_hedge_distribution_plot_returns_figure() -> None:
    from backtest.plotting import hedge_distribution_plot
    fig = hedge_distribution_plot(_make_result())
    assert fig is not None
    import matplotlib.pyplot as plt
    plt.close(fig)
```

**Step 2: Run test to verify it fails**

Run: `uhi8/bin/python -m pytest tests/backtest/test_plotting.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `backtest/plotting.py`:

```python
"""Plotting functions for backtest results."""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from backtest.types import BacktestResult


def money_plot(results: list[BacktestResult]) -> Figure:
    """Cumulative P&L: unhedged vs hedged at each gamma.

    X: day index, Y: mean cumulative P&L across positions.
    """
    fig, (ax_pnl, ax_delta) = plt.subplots(2, 1, figsize=(10, 7),
                                             height_ratios=[3, 1], sharex=True)

    # Use first result for unhedged baseline and delta_plus series
    base = results[0]
    days = [rs.day for rs in base.reserve_states]
    deltas = [rs.delta_plus for rs in base.reserve_states]

    # Shade trigger days
    for i, rs in enumerate(base.reserve_states):
        if rs.trigger_fired:
            ax_pnl.axvspan(i - 0.5, i + 0.5, alpha=0.15, color="red")
            ax_delta.axvspan(i - 0.5, i + 0.5, alpha=0.15, color="red")

    # Unhedged: cumulative mean unhedged P&L
    unhedged_cum = []
    running = 0.0
    for i, day in enumerate(days):
        day_pnls = [p.pnl_unhedged for p in base.position_pnls
                     if p.burn_date >= day]
        running += sum(day_pnls) / max(len(day_pnls), 1) if day_pnls else 0
        unhedged_cum.append(running)
    ax_pnl.plot(range(len(days)), unhedged_cum, "r-", linewidth=2, label="Unhedged")

    # Hedged per gamma
    colors = ["#2ecc71", "#27ae60", "#1abc9c", "#16a085", "#0e6655"]
    for idx, r in enumerate(results):
        hedged_cum = []
        running = 0.0
        for i, day in enumerate(days):
            day_pnls = [p.pnl_hedged for p in r.position_pnls
                         if p.burn_date >= day]
            running += sum(day_pnls) / max(len(day_pnls), 1) if day_pnls else 0
            hedged_cum.append(running)
        color = colors[idx % len(colors)]
        ax_pnl.plot(range(len(days)), hedged_cum, color=color, linewidth=1.5,
                     label=f"Hedged (γ={r.gamma:.0%})")

    ax_pnl.set_ylabel("Cumulative P&L ($)")
    ax_pnl.set_title("PLP P&L: Unhedged vs Hedged")
    ax_pnl.legend(fontsize=8)
    ax_pnl.grid(True, alpha=0.3)

    # Delta+ subplot
    ax_delta.plot(range(len(days)), deltas, "k-", linewidth=1)
    ax_delta.axhline(y=0.09, color="red", linestyle="--", alpha=0.7, label="Δ* = 0.09")
    ax_delta.set_ylabel("Δ⁺")
    ax_delta.set_xlabel("Day")
    ax_delta.legend(fontsize=8)
    ax_delta.grid(True, alpha=0.3)

    tick_positions = list(range(0, len(days), max(1, len(days) // 10)))
    ax_delta.set_xticks(tick_positions)
    ax_delta.set_xticklabels([days[i][-5:] for i in tick_positions], rotation=45, fontsize=7)

    plt.tight_layout()
    return fig


def reserve_plot(result: BacktestResult) -> Figure:
    """Reserve R(t) trajectory with premium in / payout out."""
    fig, ax = plt.subplots(figsize=(10, 4))
    days = range(len(result.reserve_states))
    balances = [rs.balance for rs in result.reserve_states]
    ax.fill_between(days, balances, alpha=0.3, color="blue")
    ax.plot(days, balances, "b-", linewidth=1.5, label="Reserve R(t)")

    for i, rs in enumerate(result.reserve_states):
        if rs.trigger_fired:
            ax.axvline(x=i, color="red", alpha=0.3, linestyle="--")

    ax.set_ylabel("Reserve ($)")
    ax.set_title(f"Insurance Reserve (γ={result.gamma:.0%})")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig


def hedge_distribution_plot(result: BacktestResult) -> Figure:
    """Histogram of hedge_value_i across positions."""
    fig, ax = plt.subplots(figsize=(8, 4))
    values = [p.hedge_value for p in result.position_pnls]
    ax.hist(values, bins=30, edgecolor="black", alpha=0.7,
            color=["#2ecc71" if v > 0 else "#e74c3c" for v in values] if len(values) < 50
            else "#3498db")
    ax.axvline(x=0, color="black", linestyle="--", linewidth=1)
    ax.set_xlabel("Hedge Value ($)")
    ax.set_ylabel("Positions")
    ax.set_title(f"Hedge Value Distribution (γ={result.gamma:.0%}, "
                 f"{result.pct_better_off:.0%} better off)")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig
```

**Step 4: Run test to verify it passes**

Run: `uhi8/bin/python -m pytest tests/backtest/test_plotting.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add -f backtest/plotting.py tests/backtest/test_plotting.py
git commit -m "feat(backtest): plotting — money plot, reserve, hedge distribution"
```

---

### Task 8: Integration Test with Real Data

**Files:**
- Create: `tests/backtest/test_integration.py`

**Step 1: Write the test**

```python
"""Integration test: full backtest on real ETH/USDC 30bps data."""
from __future__ import annotations


def test_full_backtest_real_data() -> None:
    from econometrics.data import DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS
    from backtest.daily import build_daily_states
    from backtest.sweep import run_single_backtest

    daily_states = build_daily_states(
        DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS,
        pool_daily_fee=50_000.0,
    )
    assert len(daily_states) == 41

    result = run_single_backtest(daily_states, RAW_POSITIONS, gamma=0.10, delta_star=0.09)

    # Basic sanity
    assert result.gamma == 0.10
    assert len(result.position_pnls) > 500  # 600 positions minus JIT
    assert len(result.reserve_states) == 41
    assert result.total_premiums > 0.0

    # INS-01: reserve never negative
    for rs in result.reserve_states:
        assert rs.balance >= 0.0, f"INS-01 violated on {rs.day}"

    # Trigger days: delta_plus > 0.09 should exist (we know from data)
    trigger_days = [rs for rs in result.reserve_states if rs.trigger_fired]
    assert len(trigger_days) >= 1, "Expected at least 1 trigger day"


def test_gamma_sweep_real_data() -> None:
    from econometrics.data import DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS
    from backtest.daily import build_daily_states
    from backtest.sweep import run_gamma_sweep

    daily_states = build_daily_states(
        DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS,
        pool_daily_fee=50_000.0,
    )
    results = run_gamma_sweep(daily_states, RAW_POSITIONS, gammas=[0.01, 0.10], delta_star=0.09)
    assert len(results) == 2
    # Higher gamma => more premiums
    assert results[1].total_premiums > results[0].total_premiums


def test_gamma_star_calibration_real_data() -> None:
    from econometrics.data import DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS
    from backtest.daily import build_daily_states
    from backtest.sweep import run_single_backtest
    from backtest.calibrate import derive_gamma_star, compute_avg_fees

    daily_states = build_daily_states(
        DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS,
        pool_daily_fee=50_000.0,
    )
    # First pass at gamma=0.01 to get avg fees
    base = run_single_backtest(daily_states, RAW_POSITIONS, gamma=0.01, delta_star=0.09)
    avg_fees = compute_avg_fees(base.position_pnls)
    assert avg_fees > 0.0

    gamma_star = derive_gamma_star(wtp=110.0, avg_fees=avg_fees)
    assert 0.0 < gamma_star < 1.0

    # Run at gamma_star
    result = run_single_backtest(daily_states, RAW_POSITIONS, gamma=gamma_star, delta_star=0.09)
    assert result.gamma == gamma_star
```

**Step 2: Run test**

Run: `uhi8/bin/python -m pytest tests/backtest/test_integration.py -v`
Expected: 3 passed

**Step 3: Commit**

```bash
git add -f tests/backtest/test_integration.py
git commit -m "test(backtest): integration tests on real ETH/USDC data"
```

---

### Task 9: Jupyter Notebook

**Files:**
- Create: `notebooks/eth-usdc-backtest.ipynb`

**Step 1: Create the notebook**

The notebook has 7 sections matching the design doc. Create it with these cells:

**Cell 1 (markdown):**
```markdown
# Historical Backtest: ETH/USDC 30bps Fee Concentration Insurance

**Question:** Would PLPs have been better off with ThetaSwap insurance?

**Method:** Replay 600 real positions (41 days, 2025-12-05 to 2026-01-14) through the hybrid insurance mechanism (main.pdf §6). Compare actual P&L vs counterfactual hedged P&L at each gamma.

**Insurance mechanism:**
- Premium: PLP pays γ% of fees into reserve R at exit
- Trigger: Δ⁺ > Δ* = 0.09 (econometric turning point)
- Payout: D = (Δ⁺ − Δ*)/(1 − Δ*) · R via donate(), pro-rata to insured positions
```

**Cell 2 (code) — Setup:**
```python
from econometrics.data import DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS
from backtest.daily import build_daily_states
from backtest.sweep import run_single_backtest, run_gamma_sweep
from backtest.calibrate import derive_gamma_star, compute_avg_fees
from backtest.plotting import money_plot, reserve_plot, hedge_distribution_plot

POOL_DAILY_FEE = 50_000.0  # conservative estimate for ETH/USDC 30bps
DELTA_STAR = 0.09

daily_states = build_daily_states(
    DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP, RAW_POSITIONS,
    pool_daily_fee=POOL_DAILY_FEE,
)
print(f"Days: {len(daily_states)}")
print(f"Positions: {sum(1 for _, bl, _ in RAW_POSITIONS if bl > 1)}")
```

**Cell 3 (markdown):**
```markdown
## 1. Trigger Days

Days where Δ⁺ = max(0, A_T − A_T^{1/N}) exceeds the econometric turning point Δ* = 0.09.
```

**Cell 4 (code) — Trigger days:**
```python
import matplotlib.pyplot as plt

days = [s.day[-5:] for s in daily_states]
deltas = [s.delta_plus for s in daily_states]
triggers = [s.delta_plus > DELTA_STAR for s in daily_states]

print(f"Trigger days: {sum(triggers)} / {len(daily_states)}")
print(f"Days with Δ⁺ > 0: {sum(1 for d in deltas if d > 0)} / {len(daily_states)}")
print()
for s in daily_states:
    if s.delta_plus > DELTA_STAR:
        print(f"  {s.day}: Δ⁺ = {s.delta_plus:.4f}, A_T = {s.a_t_real:.4f}, null = {s.a_t_null:.4f}")

fig, ax = plt.subplots(figsize=(12, 3))
colors = ["#e74c3c" if t else "#3498db" for t in triggers]
ax.bar(range(len(days)), deltas, color=colors, edgecolor="black", linewidth=0.3)
ax.axhline(y=DELTA_STAR, color="red", linestyle="--", label=f"Δ* = {DELTA_STAR}")
ax.set_ylabel("Δ⁺")
ax.set_title("Daily Concentration Deviation")
ax.set_xticks(range(0, len(days), 5))
ax.set_xticklabels([days[i] for i in range(0, len(days), 5)], rotation=45)
ax.legend()
plt.tight_layout()
plt.show()
```

**Cell 5 (markdown):**
```markdown
## 2. Gamma Calibration

Derive γ* from the econometric WTP ($110 at Δ = 0.15).
```

**Cell 6 (code) — Calibration:**
```python
# First pass at minimal gamma to get fee distribution
base = run_single_backtest(daily_states, RAW_POSITIONS, gamma=0.001, delta_star=DELTA_STAR)
avg_fees = compute_avg_fees(base.position_pnls)
gamma_star = derive_gamma_star(wtp=110.0, avg_fees=avg_fees)

print(f"Average fees per position: ${avg_fees:,.2f}")
print(f"Econometric WTP: $110")
print(f"Calibrated γ* = {gamma_star:.4f} ({gamma_star:.2%})")
```

**Cell 7 (markdown):**
```markdown
## 3. Gamma Sweep Results
```

**Cell 8 (code) — Sweep:**
```python
gammas = sorted(set([0.01, 0.05, 0.10, 0.20, gamma_star]))
results = run_gamma_sweep(daily_states, RAW_POSITIONS, gammas=gammas, delta_star=DELTA_STAR)

print(f"{'γ':>8} {'Premiums':>12} {'Payouts':>10} {'Triggers':>9} {'Mean HV':>10} "
      f"{'% Better':>9} {'R Peak':>10} {'R Util':>8}")
print("-" * 80)
for r in results:
    star = " ←γ*" if abs(r.gamma - gamma_star) < 0.0001 else ""
    print(f"{r.gamma:>8.2%} {r.total_premiums:>12,.0f} {r.total_payouts:>10,.0f} "
          f"{r.trigger_days:>9} {r.mean_hedge_value:>10,.2f} "
          f"{r.pct_better_off:>8.1%} {r.reserve_peak:>10,.0f} "
          f"{r.reserve_utilization:>8.1%}{star}")
```

**Cell 9 (markdown):**
```markdown
## 4. The Money Plot

Cumulative P&L: unhedged (red) vs hedged at each γ (green). Background shading = trigger days.
```

**Cell 10 (code) — Money plot:**
```python
fig = money_plot(results)
plt.show()
```

**Cell 11 (markdown):**
```markdown
## 5. Reserve Dynamics at γ*
```

**Cell 12 (code) — Reserve:**
```python
gamma_star_result = [r for r in results if abs(r.gamma - gamma_star) < 0.0001][0]
fig = reserve_plot(gamma_star_result)
plt.show()
```

**Cell 13 (markdown):**
```markdown
## 6. Position-Level Hedge Value Distribution
```

**Cell 14 (code) — Distribution:**
```python
fig = hedge_distribution_plot(gamma_star_result)
plt.show()

# Breakdown: positions exiting on trigger days vs non-trigger days
trigger_days_set = {rs.day for rs in gamma_star_result.reserve_states if rs.trigger_fired}
on_trigger = [p for p in gamma_star_result.position_pnls if p.burn_date in trigger_days_set]
off_trigger = [p for p in gamma_star_result.position_pnls if p.burn_date not in trigger_days_set]

print(f"\nPositions exiting on trigger days: {len(on_trigger)}")
if on_trigger:
    print(f"  Mean hedge value: ${sum(p.hedge_value for p in on_trigger)/len(on_trigger):,.2f}")
print(f"\nPositions exiting on non-trigger days: {len(off_trigger)}")
if off_trigger:
    print(f"  Mean hedge value: ${sum(p.hedge_value for p in off_trigger)/len(off_trigger):,.2f}")
```

**Cell 15 (markdown):**
```markdown
## 7. Summary

Key findings from the historical backtest on ETH/USDC 30bps (41 days, 600 positions).
```

**Cell 16 (code) — Summary:**
```python
print("=== BACKTEST SUMMARY ===\n")
print(f"Pool: ETH/USDC 30bps")
print(f"Window: 2025-12-05 to 2026-01-14 ({len(daily_states)} days)")
print(f"Positions: {len(gamma_star_result.position_pnls)}")
print(f"Trigger days (Δ⁺ > {DELTA_STAR}): {gamma_star_result.trigger_days}")
print(f"Calibrated γ*: {gamma_star:.2%}")
print(f"\nAt γ*:")
print(f"  Total premiums collected: ${gamma_star_result.total_premiums:,.2f}")
print(f"  Total payouts distributed: ${gamma_star_result.total_payouts:,.2f}")
print(f"  Mean hedge value: ${gamma_star_result.mean_hedge_value:,.2f}")
print(f"  Positions better off: {gamma_star_result.pct_better_off:.1%}")
print(f"  Reserve peak: ${gamma_star_result.reserve_peak:,.2f}")
print(f"  Reserve utilization: {gamma_star_result.reserve_utilization:.1%}")
```

**Step 2: Run the notebook to verify**

Run: `uhi8/bin/jupyter execute notebooks/eth-usdc-backtest.ipynb --ExecutePreprocessor.timeout=120`
Expected: executes without errors

**Step 3: Commit**

```bash
git add -f notebooks/eth-usdc-backtest.ipynb
git commit -m "feat(backtest): ETH/USDC backtest notebook with gamma sweep"
```

---

### Task 10: Run All Tests

**Step 1: Run full test suite**

Run: `uhi8/bin/python -m pytest tests/backtest/ -v`
Expected: all tests pass (types: 4, daily: 3, reserve: 3, pnl: 3, calibrate: 4, sweep: 3, plotting: 3, integration: 3 = **26 tests**)

**Step 2: Run existing econometrics tests to verify no regression**

Run: `uhi8/bin/python -m pytest tests/econometrics/ -v`
Expected: all existing tests still pass

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore(backtest): all 26 tests passing, no regressions"
```
