"""Mechanism sweep — epoch, decay, and sliding-window accumulation models.

Each mechanism provides a step function and delta_plus computation.
All are pure functions operating on frozen dataclasses.

Per @functional-python.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, replace as dc_replace
from datetime import datetime, timedelta

from backtest.oracle_comparison import PositionExit
from backtest.payoff import run_exit_payoff_backtest
from backtest.types import DailyPoolState


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
    x_k_sq = exit_.fee_share_x_k ** 2

    if days_since_epoch >= state.epoch_length_days:
        return EpochState(
            accumulated_sum=x_k_sq / exit_.block_lifetime,
            theta_sum=1.0 / exit_.block_lifetime,
            removed_pos_count=1,
            epoch_start=exit_.burn_date,
            epoch_length_days=state.epoch_length_days,
        )
    else:
        return EpochState(
            accumulated_sum=state.accumulated_sum + x_k_sq / exit_.block_lifetime,
            theta_sum=state.theta_sum + 1.0 / exit_.block_lifetime,
            removed_pos_count=state.removed_pos_count + 1,
            epoch_start=state.epoch_start,
            epoch_length_days=state.epoch_length_days,
        )


def epoch_delta_plus(state: EpochState) -> float:
    """Compute delta-plus from epoch state."""
    if state.removed_pos_count == 0:
        return 0.0
    n_sq = state.removed_pos_count ** 2
    return max(0.0, math.sqrt(state.accumulated_sum) - math.sqrt(state.theta_sum / n_sq))


# ── Exponential-decay mechanism ────────────────────────────────────

@dataclass(frozen=True)
class DecayState:
    """Accumulator state with exponential decay.

    effective_count decays alongside accumulated_sum and theta_sum,
    preventing the N squared denominator from growing unboundedly while
    the numerators decay.
    """
    accumulated_sum: float
    theta_sum: float
    effective_count: float  # decays with same factor as accumulators
    last_update: str
    half_life_days: float


def step_decay(state: DecayState, exit_: PositionExit) -> DecayState:
    """Decay existing state, then accumulate new exit."""
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
    """Compute delta-plus from decay state using effective N."""
    if state.effective_count < 1e-10:
        return 0.0
    n_sq = state.effective_count ** 2
    return max(0.0, math.sqrt(state.accumulated_sum) - math.sqrt(state.theta_sum / n_sq))


# ── Sliding-window mechanism ──────────────────────────────────────

@dataclass(frozen=True)
class WindowState:
    """Ring buffer of recent (fee_share_x_k, block_lifetime) entries."""
    entries: tuple[tuple[float, int], ...]
    window_size: int


def step_window(state: WindowState, exit_: PositionExit) -> WindowState:
    """Add exit to window, evicting oldest if at capacity."""
    new_entry = (exit_.fee_share_x_k, exit_.block_lifetime)
    entries = state.entries + (new_entry,)
    if len(entries) > state.window_size:
        entries = entries[1:]
    return WindowState(entries=entries, window_size=state.window_size)


def window_delta_plus(state: WindowState) -> float:
    """Compute delta-plus from window entries only."""
    if not state.entries:
        return 0.0
    n = len(state.entries)
    acc_sum = sum(x_k ** 2 / lifetime for x_k, lifetime in state.entries)
    theta_sum = sum(1.0 / lifetime for _, lifetime in state.entries)
    n_sq = n ** 2
    return max(0.0, math.sqrt(acc_sum) - math.sqrt(theta_sum / n_sq))


# ── Sweep runner ──────────────────────────────────────────────────

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
    """Build Δ⁺ series for a given mechanism."""
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


def _align_series(series: MechanismSeries, target_days: list[str]) -> list[float]:
    """Align mechanism series to target days, filling 0.0 for missing days."""
    day_to_val = dict(zip(series.days, series.delta_plus_values))
    return [day_to_val.get(d, 0.0) for d in target_days]


def _max_divergence(candidate: list[float], baseline: list[float]) -> float:
    """Max absolute difference between two aligned series."""
    if not candidate or not baseline:
        return 0.0
    return max(abs(c - b) for c, b in zip(candidate, baseline))


def run_mechanism_sweep(
    exits: list[PositionExit],
    daily_snapshot_baseline: list[float],
    baseline_days: list[str],
    epoch_lengths: list[int] | None = None,
    half_lives: list[float] | None = None,
    window_sizes: list[int] | None = None,
) -> list[SweepResult]:
    """Sweep all mechanism × parameter combos, scoring against daily-snapshot baseline."""
    if epoch_lengths is None:
        epoch_lengths = [1, 3, 7, 14]
    if half_lives is None:
        half_lives = [1.0, 3.0, 7.0, 14.0]
    if window_sizes is None:
        window_sizes = [10, 25, 50]

    results: list[SweepResult] = []

    for el in epoch_lengths:
        series = build_mechanism_series(exits, "epoch", epoch_length_days=el)
        aligned = _align_series(series, baseline_days)
        corr = compute_correlation(aligned, list(daily_snapshot_baseline))
        max_div = _max_divergence(aligned, list(daily_snapshot_baseline))
        results.append(SweepResult(
            mechanism_name="epoch", params={"epoch_length_days": el},
            correlation=corr, max_divergence=max_div, series=series,
        ))

    for hl in half_lives:
        series = build_mechanism_series(exits, "decay", half_life_days=hl)
        aligned = _align_series(series, baseline_days)
        corr = compute_correlation(aligned, list(daily_snapshot_baseline))
        max_div = _max_divergence(aligned, list(daily_snapshot_baseline))
        results.append(SweepResult(
            mechanism_name="decay", params={"half_life_days": hl},
            correlation=corr, max_divergence=max_div, series=series,
        ))

    for ws in window_sizes:
        series = build_mechanism_series(exits, "window", window_size=ws)
        aligned = _align_series(series, baseline_days)
        corr = compute_correlation(aligned, list(daily_snapshot_baseline))
        max_div = _max_divergence(aligned, list(daily_snapshot_baseline))
        results.append(SweepResult(
            mechanism_name="window", params={"window_size": ws},
            correlation=corr, max_divergence=max_div, series=series,
        ))

    results.sort(key=lambda r: r.correlation, reverse=True)
    return results


# ── Payoff pipeline integration ──────────────────────────────────

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

    For each mechanism, builds modified daily_states where delta_plus
    is replaced by the mechanism's delta-plus, then runs existing payoff pipeline.
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

    for sr in sweep_results:
        # Build modified daily states with mechanism's delta-plus
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
