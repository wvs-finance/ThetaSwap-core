"""Pure functions: Dune MCP JSON rows → typed domain objects."""
from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from statistics import median as _median
import math
from typing import Sequence

from econometrics.types import DailyPanelRow, DuneRow, ExitPanelRow, LaggedPositionRow, PositionRow

BLOCKS_PER_DAY: float = 7200.0


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


def ingest_positions(
    q4_rows: Sequence[DuneRow],
    il_map: dict[str, float],
) -> list[PositionRow]:
    """Convert Q4v2 position rows + Q5 IL proxy into PositionRow list.

    Args:
        q4_rows: Dune Q4v2 rows with burn_date, blocklife, daily_a_t.
        il_map: day -> il_proxy from Q5.
    """
    return [
        PositionRow(
            burn_date=str(r["burn_date"]),
            blocklife=int(r["blocklife"]),
            daily_a_t=float(r["daily_a_t"]),
            il_proxy=il_map.get(str(r["burn_date"]), 0.0),
        )
        for r in q4_rows
        if int(r["blocklife"]) > 1  # extra safety filter
    ]


def build_il_map(q5_rows: Sequence[DuneRow]) -> dict[str, float]:
    """Build day -> il_proxy lookup from Q5 results."""
    return {str(r["day"]): float(r["il_proxy"]) for r in q5_rows}


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

    Treatment variable (a_t_lagged) uses A_T from (day - lag_days).
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

        obs_start = max(mint_d, window_start)
        obs_end = min(burn_d, window_end)

        d = obs_start
        while d <= obs_end:
            day_str = d.isoformat()
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


def build_exit_panel_deviation(
    raw_positions: list[tuple[str, int, float]],
    daily_at_map: dict[str, float],
    null_at_map: dict[str, float],
    il_map: dict[str, float],
    lag_days: int = 1,
) -> list[ExitPanelRow]:
    """Like build_exit_panel but treatment = real A_T - null A_T (deviation from Ma-Crapis null).

    The deviation measures excess fee concentration above the symmetric
    equilibrium baseline predicted by Ma & Crapis (2024).
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

        obs_start = max(mint_d, window_start)
        obs_end = min(burn_d, window_end)

        d = obs_start
        while d <= obs_end:
            day_str = d.isoformat()
            lag_d = d - timedelta(days=lag_days)
            lag_key = lag_d.isoformat()
            if lag_key not in daily_at_map:
                d += timedelta(days=1)
                continue

            real_at = daily_at_map[lag_key]
            null_at = null_at_map.get(lag_key, 0.0)
            a_t_lagged = real_at - null_at  # deviation from null

            age_days = (d - mint_d).days
            rows.append(ExitPanelRow(
                position_idx=idx,
                day=day_str,
                exited=1 if d == burn_d else 0,
                a_t_lagged=a_t_lagged,
                il=il_map.get(day_str, 0.0),
                log_age=math.log(max(1, age_days)),
            ))
            d += timedelta(days=1)

    return rows


def build_exit_panel_lifetime_mean(
    raw_positions: list[tuple[str, int, float]],
    daily_at_map: dict[str, float],
    il_map: dict[str, float],
    lag_days: int = 1,
) -> list[ExitPanelRow]:
    """Build position-day panel using lifetime-mean A_T as treatment.

    Identical to ``build_exit_panel`` except the treatment variable
    ``a_t_lagged`` is the **mean A_T over [mint_date, day − lag_days]**
    rather than the single-day point lag.  A passive LP's decision is
    shaped by accumulated exposure, not one snapshot.

    Rows where no A_T data exists in that range are skipped (same as
    the point-lag variant).
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

        obs_start = max(mint_d, window_start)
        obs_end = min(burn_d, window_end)

        d = obs_start
        while d <= obs_end:
            day_str = d.isoformat()
            lag_d = d - timedelta(days=lag_days)

            # Collect A_T values over [max(mint_d, window_start), lag_d]
            range_start = max(mint_d, window_start)
            if lag_d < range_start:
                d += timedelta(days=1)
                continue

            values: list[float] = []
            cursor = range_start
            while cursor <= lag_d:
                key = cursor.isoformat()
                if key in daily_at_map:
                    values.append(daily_at_map[key])
                cursor += timedelta(days=1)

            if not values:
                d += timedelta(days=1)
                continue

            lifetime_mean = sum(values) / len(values)
            age_days = (d - mint_d).days
            rows.append(ExitPanelRow(
                position_idx=idx,
                day=day_str,
                exited=1 if d == burn_d else 0,
                a_t_lagged=lifetime_mean,
                il=il_map.get(day_str, 0.0),
                log_age=math.log(max(1, age_days)),
            ))
            d += timedelta(days=1)

    return rows
