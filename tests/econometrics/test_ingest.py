"""Tests for Dune MCP JSON → JAX array ingestion."""
from __future__ import annotations

import math

import jax.numpy as jnp
from econometrics.ingest import (
    approximate_mint_date,
    build_exit_panel,
    build_exit_panel_deviation,
    build_lagged_positions,
    compute_lagged_treatment,
    compute_null_at_map,
    ingest_daily_panel,
    merge_jit_instrument,
)
from econometrics.types import DailyPanelRow, ExitPanelRow


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


# ── Lagged treatment tests ────────────────────────────────────────────

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
    raw = [("2025-12-22", 14400, 0.20)]
    panel = build_exit_panel(raw, PANEL_DAILY_AT, PANEL_IL, lag_days=1)
    assert len(panel) >= 2  # at least the days with lagged A_T available
    assert all(isinstance(r, ExitPanelRow) for r in panel)
    exits = [r for r in panel if r.exited == 1]
    assert len(exits) == 1
    assert exits[0].day == "2025-12-22"
    survived = [r for r in panel if r.exited == 0]
    assert len(survived) >= 1


def test_build_exit_panel_lagged_a_t() -> None:
    """Treatment uses A_T from (day - lag_days), not same day."""
    raw = [("2025-12-22", 14400, 0.20)]
    panel = build_exit_panel(raw, PANEL_DAILY_AT, PANEL_IL, lag_days=1)
    row_21 = [r for r in panel if r.day == "2025-12-21"]
    if row_21:
        assert row_21[0].a_t_lagged == 0.10  # daily_at_map["2025-12-20"]
    row_22 = [r for r in panel if r.day == "2025-12-22"]
    assert row_22[0].a_t_lagged == 0.15  # daily_at_map["2025-12-21"]


def test_build_exit_panel_log_age() -> None:
    """log_age is log(days since mint), floored at log(1)=0."""
    raw = [("2025-12-22", 14400, 0.20)]
    panel = build_exit_panel(raw, PANEL_DAILY_AT, PANEL_IL, lag_days=1)
    row_20 = [r for r in panel if r.day == "2025-12-20"]
    if row_20:
        assert row_20[0].log_age == 0.0  # age=0 -> log(max(1,0)) = 0
    row_22 = [r for r in panel if r.day == "2025-12-22"]
    assert abs(row_22[0].log_age - math.log(2)) < 1e-6  # age=2


def test_build_exit_panel_excludes_jit() -> None:
    """Positions with blocklife <= 1 block are excluded (JIT)."""
    raw = [("2025-12-22", 1, 0.20)]
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


# ── Lifetime-mean exit panel tests ───────────────────────────────────


def test_build_exit_panel_lifetime_mean_uses_average() -> None:
    """Lifetime mean uses average A_T over position's life, not point lag."""
    from econometrics.ingest import build_exit_panel_lifetime_mean
    daily_at = {
        "2025-12-05": 0.01,
        "2025-12-06": 0.02,
        "2025-12-07": 0.03,
        "2025-12-08": 0.04,
        "2025-12-09": 0.05,
    }
    il = {"2025-12-05": 0.0, "2025-12-06": 0.0, "2025-12-07": 0.0, "2025-12-08": 0.0, "2025-12-09": 0.0}
    # Position: burns on 2025-12-09, blocklife=28800 (~4 days), so mint ~2025-12-05
    positions = [("2025-12-09", 28800, 0.0)]
    panel = build_exit_panel_lifetime_mean(positions, daily_at, il, lag_days=1)
    # On day 2025-12-09 with lag=1, lifetime mean = mean(A_T from 2025-12-05 to 2025-12-08) = (0.01+0.02+0.03+0.04)/4 = 0.025
    exit_row = [r for r in panel if r.exited == 1]
    assert len(exit_row) == 1
    assert abs(exit_row[0].a_t_lagged - 0.025) < 1e-6
