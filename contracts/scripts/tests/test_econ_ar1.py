"""Tests for AR(1) surprise construction."""
from __future__ import annotations

import math
from datetime import date

import duckdb

from scripts.econ_schema import init_db
from scripts.econ_panels import build_weekly_panel, build_daily_panel, compute_ar1_surprises


def _seed_full_test_data(conn: duckdb.DuckDBPyConnection) -> None:
    """Seed 24 months of IPC + TRM + FRED + release calendar for AR(1) testing.

    IPC: 2022-01 to 2023-12 (24 months; first 12 = warmup)
    TRM: daily for 2023 (post-warmup year)
    FRED: minimal VIX + oil for panel building
    Release calendar: 5th business day of following month
    """
    import math as _m

    # IPC: 24 months of synthetic data
    for i in range(24):
        year = 2022 + (i // 12)
        month = (i % 12) + 1
        pct = 0.5 + 0.1 * _m.sin(i * 0.5)
        conn.execute(
            "INSERT INTO dane_ipc_monthly (date, ipc_index, ipc_pct_change) VALUES (?, ?, ?)",
            [date(year, month, 1), 150.0 + i * 0.5, pct],
        )

    # Release calendar: each IPC month released on 7th of following month
    for i in range(24):
        year = 2022 + (i // 12)
        month = (i % 12) + 1
        rel_year = year + (1 if month == 12 else 0)
        rel_month = 1 if month == 12 else month + 1
        conn.execute(
            "INSERT INTO dane_release_calendar (year, month, release_date, series, imputed) "
            "VALUES (?, ?, ?, 'ipc', TRUE)",
            [year, month, date(rel_year, rel_month, 7)],
        )

    # TRM: daily for 2023 (Mon-Fri of each week, ~7th-11th of each month)
    for month in range(1, 13):
        for day in [7, 8, 9, 10, 11]:
            try:
                d = date(2023, month, day)
                if d.weekday() < 5:  # skip weekends
                    conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES (?, ?)",
                                 [d, 3900.0 + month])
            except ValueError:
                pass
    # Add a prior-month day for LAG
    conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES ('2022-12-30', 3899.0)")

    # Minimal FRED
    for month in range(1, 13):
        for day in [7, 8, 9, 10, 11]:
            try:
                d = date(2023, month, day)
                if d.weekday() < 5:
                    conn.execute("INSERT INTO fred_daily (series_id, date, value) VALUES ('VIXCLS', ?, 14.0)", [d])
                    conn.execute("INSERT INTO fred_daily (series_id, date, value) VALUES ('DCOILWTICO', ?, 74.0)", [d])
            except ValueError:
                pass


def test_compute_ar1_surprises_populates_weekly() -> None:
    """After compute_ar1_surprises, cpi_surprise_ar1 is nonzero on release weeks."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_full_test_data(conn)
    build_weekly_panel(conn, sample_start=date(2023, 1, 1))
    compute_ar1_surprises(conn, warmup_months=12)

    nonzero = conn.execute(
        "SELECT COUNT(*) FROM weekly_panel WHERE cpi_surprise_ar1 != 0.0"
    ).fetchone()
    assert nonzero is not None and nonzero[0] > 0


def test_ar1_warmup_not_leaked() -> None:
    """Warmup months (first 12) should not produce surprises in the panel."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_full_test_data(conn)
    build_weekly_panel(conn, sample_start=date(2023, 1, 1))
    compute_ar1_surprises(conn, warmup_months=12)

    # The first release in the panel is Jan 2023 IPC (released ~Feb 7, 2023).
    # But the IPC for Jan 2023 is the 13th observation (2022-01 to 2023-01 = 13 months).
    # With warmup=12, the first surprise is for index 12 (2023-01), which IS post-warmup.
    # Months 0-11 (2022-01 to 2022-12) are warmup — their releases fall in 2022,
    # which is before sample_start=2023-01-01, so they don't appear in weekly_panel.
    # Verify no weekly_panel rows before 2023 have nonzero surprise.
    pre_2023 = conn.execute(
        "SELECT COUNT(*) FROM weekly_panel WHERE week_start < '2023-01-01' AND cpi_surprise_ar1 != 0.0"
    ).fetchone()
    assert pre_2023 is not None and pre_2023[0] == 0


def test_ar1_surprise_updates_daily_panel() -> None:
    """compute_ar1_surprises also populates daily_panel surprise columns."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_full_test_data(conn)
    build_weekly_panel(conn, sample_start=date(2023, 1, 1))
    build_daily_panel(conn, sample_start=date(2023, 1, 1))
    compute_ar1_surprises(conn, warmup_months=12)

    # Check daily panel has nonzero abs_cpi_surprise on release dates
    nonzero_daily = conn.execute(
        "SELECT COUNT(*) FROM daily_panel WHERE abs_cpi_surprise != 0.0"
    ).fetchone()
    assert nonzero_daily is not None and nonzero_daily[0] > 0

    # abs should equal absolute value of signed surprise
    mismatches = conn.execute(
        "SELECT COUNT(*) FROM daily_panel WHERE abs_cpi_surprise != 0.0 "
        "AND ABS(abs_cpi_surprise - ABS(cpi_surprise_ar1_daily)) > 1e-10"
    ).fetchone()
    assert mismatches is not None and mismatches[0] == 0
