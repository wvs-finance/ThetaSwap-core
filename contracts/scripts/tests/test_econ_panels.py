"""Tests for panel builders (weekly_panel, daily_panel)."""
from __future__ import annotations

import math
from datetime import date

import duckdb

from scripts.econ_schema import init_db
from scripts.econ_panels import build_weekly_panel, build_daily_panel


def _seed_trm(conn: duckdb.DuckDBPyConnection) -> None:
    """Insert TRM observations spanning 2 weeks + prior Friday for LAG."""
    trm_data = [
        # Prior Friday (for Monday return)
        ("2024-01-05", 3900.0),
        # Week 1: Mon-Fri
        ("2024-01-08", 3910.0),
        ("2024-01-09", 3905.0),
        ("2024-01-10", 3920.0),
        ("2024-01-11", 3915.0),
        ("2024-01-12", 3925.0),
        # Week 2: Mon-Fri
        ("2024-01-15", 3930.0),
        ("2024-01-16", 3940.0),
        ("2024-01-17", 3935.0),
        ("2024-01-18", 3950.0),
        ("2024-01-19", 3945.0),
    ]
    for d, v in trm_data:
        conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES (?, ?)", [d, v])


def _seed_fred(conn: duckdb.DuckDBPyConnection) -> None:
    """Insert VIX and WTI for the same 2-week period."""
    vix_data = [
        ("2024-01-08", 13.5), ("2024-01-09", 14.0), ("2024-01-10", 13.8),
        ("2024-01-11", 14.2), ("2024-01-12", 13.9),
        ("2024-01-15", 14.5), ("2024-01-16", 14.1), ("2024-01-17", 14.3),
        ("2024-01-18", 14.8), ("2024-01-19", 14.6),
    ]
    for d, v in vix_data:
        conn.execute("INSERT INTO fred_daily (series_id, date, value) VALUES ('VIXCLS', ?, ?)", [d, v])

    oil_data = [
        ("2024-01-05", 72.0),  # prior week for LAG
        ("2024-01-08", 72.5), ("2024-01-09", 73.0), ("2024-01-10", 72.8),
        ("2024-01-11", 73.5), ("2024-01-12", 74.0),
        ("2024-01-15", 74.5), ("2024-01-16", 75.0), ("2024-01-17", 74.8),
        ("2024-01-18", 75.5), ("2024-01-19", 76.0),
    ]
    for d, v in oil_data:
        conn.execute("INSERT INTO fred_daily (series_id, date, value) VALUES ('DCOILWTICO', ?, ?)", [d, v])


def test_weekly_panel_rv_computation() -> None:
    """weekly_panel computes RV as sum of squared log-returns."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_weekly_panel(conn, sample_start=date(2024, 1, 8))
    row = conn.execute(
        "SELECT rv, rv_cuberoot, rv_log, n_trading_days FROM weekly_panel WHERE week_start = '2024-01-08'"
    ).fetchone()
    assert row is not None
    rv, rv_cr, rv_log, n_days = row
    assert n_days == 5  # Mon return uses prior Friday
    assert rv > 0
    assert abs(rv_cr - rv ** (1.0 / 3.0)) < 1e-10
    assert abs(rv_log - math.log(rv)) < 1e-10


def test_weekly_panel_oil_return() -> None:
    """oil_return is log(last_wti_this_week / last_wti_prior_week)."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_weekly_panel(conn, sample_start=date(2024, 1, 8))
    row = conn.execute(
        "SELECT oil_return, oil_log_level FROM weekly_panel WHERE week_start = '2024-01-08'"
    ).fetchone()
    assert row is not None
    oil_ret, oil_level = row
    expected_ret = math.log(74.0 / 72.0)  # Fri 12 / Fri 05
    assert abs(oil_ret - expected_ret) < 1e-10
    assert abs(oil_level - math.log(74.0)) < 1e-10


def test_weekly_panel_vix_avg_and_friday() -> None:
    """vix_avg is weekly mean, vix_friday_close is last trading day."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_weekly_panel(conn, sample_start=date(2024, 1, 8))
    row = conn.execute(
        "SELECT vix_avg, vix_friday_close FROM weekly_panel WHERE week_start = '2024-01-08'"
    ).fetchone()
    assert row is not None
    vix_avg, vix_fri = row
    expected_avg = (13.5 + 14.0 + 13.8 + 14.2 + 13.9) / 5.0
    assert abs(vix_avg - expected_avg) < 1e-10
    assert vix_fri == 13.9  # Friday 2024-01-12


def test_weekly_panel_non_release_week_zeros() -> None:
    """Non-release weeks have 0.0 for surprise columns, not NULL."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_weekly_panel(conn, sample_start=date(2024, 1, 8))
    row = conn.execute(
        "SELECT cpi_surprise_ar1, dane_ipc_pct, dane_ipp_pct, us_cpi_surprise, "
        "is_cpi_release_week, is_ppi_release_week "
        "FROM weekly_panel WHERE week_start = '2024-01-08'"
    ).fetchone()
    assert row is not None
    cpi_s, ipc_pct, ipp_pct, us_s, is_cpi, is_ppi = row
    assert cpi_s == 0.0
    assert ipc_pct == 0.0
    assert ipp_pct == 0.0
    assert us_s == 0.0
    assert is_cpi is False
    assert is_ppi is False


def test_weekly_panel_release_week_flags() -> None:
    """Release weeks have correct flags and dane_ipc_pct populated."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    # Add IPC data for Dec 2023 and release calendar entry
    conn.execute("INSERT INTO dane_ipc_monthly (date, ipc_index, ipc_pct_change) VALUES ('2023-12-01', 150.0, 0.5)")
    # Release date falls in week of 2024-01-08 (Mon)
    conn.execute(
        "INSERT INTO dane_release_calendar (year, month, release_date, series, imputed) "
        "VALUES (2023, 12, '2024-01-09', 'ipc', TRUE)"
    )
    build_weekly_panel(conn, sample_start=date(2024, 1, 8))
    row = conn.execute(
        "SELECT dane_ipc_pct, is_cpi_release_week FROM weekly_panel WHERE week_start = '2024-01-08'"
    ).fetchone()
    assert row is not None
    assert row[0] == 0.5  # ipc_pct_change from the release
    assert row[1] is True


def test_weekly_panel_short_week() -> None:
    """Weeks with fewer than 5 trading days produce correct n_trading_days."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    # Only 3 TRM days in the week (+ prior day for LAG)
    conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES ('2024-01-19', 3945.0)")  # prior Fri
    conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES ('2024-01-22', 3950.0)")  # Mon
    conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES ('2024-01-23', 3955.0)")  # Tue
    conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES ('2024-01-24', 3960.0)")  # Wed
    # No Thu/Fri (holiday)
    # Minimal FRED data
    for d in ["2024-01-22", "2024-01-23", "2024-01-24"]:
        conn.execute("INSERT INTO fred_daily (series_id, date, value) VALUES ('VIXCLS', ?, 14.0)", [d])
        conn.execute("INSERT INTO fred_daily (series_id, date, value) VALUES ('DCOILWTICO', ?, 74.0)", [d])
    build_weekly_panel(conn, sample_start=date(2024, 1, 22))
    row = conn.execute(
        "SELECT n_trading_days, rv FROM weekly_panel WHERE week_start = '2024-01-22'"
    ).fetchone()
    assert row is not None
    assert row[0] == 3  # only 3 returns (Mon, Tue, Wed using prior Fri for Mon LAG)
    assert row[1] > 0


def test_daily_panel_basic() -> None:
    """daily_panel has one row per TRM trading day with correct columns."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_daily_panel(conn, sample_start=date(2024, 1, 8))
    count = conn.execute("SELECT COUNT(*) FROM daily_panel").fetchone()
    assert count is not None and count[0] == 10  # Mon-Fri × 2 weeks

    # First day should have a return (uses prior Friday via lookback)
    first = conn.execute(
        "SELECT date, cop_usd_return, week_start FROM daily_panel ORDER BY date LIMIT 1"
    ).fetchone()
    assert first is not None
    assert first[0] == date(2024, 1, 8)
    assert first[1] is not None  # return computed from prior Friday
    expected_ret = math.log(3910.0 / 3900.0)
    assert abs(first[1] - expected_ret) < 1e-10
    assert first[2] == date(2024, 1, 8)  # week_start = Monday


def test_daily_panel_intervention_dummy() -> None:
    """daily_panel sets intervention_dummy=1 on intervention dates."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    # Add an intervention on 2024-01-10
    conn.execute(
        "INSERT INTO banrep_intervention_daily (date, direct_purchase) VALUES ('2024-01-10', 50.0)"
    )
    build_daily_panel(conn, sample_start=date(2024, 1, 8))
    row = conn.execute(
        "SELECT intervention_dummy FROM daily_panel WHERE date = '2024-01-10'"
    ).fetchone()
    assert row is not None and row[0] == 1

    non_intv = conn.execute(
        "SELECT intervention_dummy FROM daily_panel WHERE date = '2024-01-08'"
    ).fetchone()
    assert non_intv is not None and non_intv[0] == 0
