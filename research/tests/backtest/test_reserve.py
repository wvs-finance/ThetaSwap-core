"""Tests for reserve simulation."""
from __future__ import annotations

from backtest.reserve import simulate_reserve
from backtest.types import DailyPoolState


# ── Helpers ───────────────────────────────────────────────────────────

def _make_state(day: str, delta_plus: float, n_positions: int = 10,
                pool_daily_fee: float = 100.0) -> DailyPoolState:
    return DailyPoolState(
        day=day, a_t_real=0.0, a_t_null=0.0,
        delta_plus=delta_plus, il=0.0,
        n_positions=n_positions, pool_daily_fee=pool_daily_fee,
    )


# ── Tests ─────────────────────────────────────────────────────────────

def test_no_trigger_no_payout():
    """delta_plus=0.05 < delta_star=0.09 => no trigger, no payout."""
    states = [_make_state("2024-01-01", delta_plus=0.05)]
    # Pre-computed premium: 2 exits * 0.10 * (100/10) = 2.0
    premium_by_day = {"2024-01-01": 2.0}

    result = simulate_reserve(states, premium_by_day, delta_star=0.09)
    assert len(result) == 1
    assert result[0].trigger_fired is False
    assert result[0].payout_out == 0.0
    assert result[0].balance > 0.0


def test_trigger_fires_correctly():
    """delta_plus=0.20 > delta_star=0.09 => trigger fires with correct D."""
    states = [_make_state("2024-01-01", delta_plus=0.20, n_positions=10)]
    # Premium = 2 exits * 0.10 * (100/10) = 2.0
    premium_by_day = {"2024-01-01": 2.0}

    result = simulate_reserve(states, premium_by_day, delta_star=0.09)
    r = result[0]
    assert r.trigger_fired is True

    expected_premium = 2.0
    assert abs(r.premium_in - expected_premium) < 1e-9

    # D = (delta_plus - delta_star) / (1 - delta_star) * balance_after_premium
    balance_after_premium = expected_premium
    expected_d = (0.20 - 0.09) / (1 - 0.09) * balance_after_premium
    expected_payout = min(expected_d, balance_after_premium)
    assert abs(r.payout_out - expected_payout) < 1e-9
    assert r.balance == balance_after_premium - expected_payout
    # C2 fix: donate_amount should equal raw D (before min cap)
    assert abs(r.donate_amount - expected_d) < 1e-9


def test_solvency_invariant():
    """INS-01: reserve balance >= 0 at all times."""
    states = [
        _make_state("2024-01-01", delta_plus=0.50, n_positions=5),
        _make_state("2024-01-02", delta_plus=0.80, n_positions=5),
        _make_state("2024-01-03", delta_plus=0.95, n_positions=5),
    ]
    # 1 exit per day * 0.05 * (100/5) = 1.0 per day
    premium_by_day = {
        "2024-01-01": 1.0,
        "2024-01-02": 1.0,
        "2024-01-03": 1.0,
    }

    result = simulate_reserve(states, premium_by_day, delta_star=0.09)
    for r in result:
        assert r.balance >= 0.0, f"Solvency violated on {r.day}: {r.balance}"


def test_no_exits_no_premium():
    """Zero exits => zero premium, but trigger can still fire."""
    states = [_make_state("2024-01-01", delta_plus=0.20)]
    premium_by_day = {}

    result = simulate_reserve(states, premium_by_day)
    assert result[0].premium_in == 0.0
    assert result[0].payout_out == 0.0


def test_multi_day_accumulation():
    """Premiums accumulate across days."""
    states = [
        _make_state("2024-01-01", delta_plus=0.0, n_positions=10),
        _make_state("2024-01-02", delta_plus=0.0, n_positions=10),
    ]
    # Day 1: 5 exits * 0.10 * (100/10) = 5.0
    # Day 2: 3 exits * 0.10 * (100/10) = 3.0
    premium_by_day = {"2024-01-01": 5.0, "2024-01-02": 3.0}

    result = simulate_reserve(states, premium_by_day)
    # balance = 5.0 + 3.0 = 8.0
    assert abs(result[1].balance - 8.0) < 1e-9
