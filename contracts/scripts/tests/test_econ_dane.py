"""Tests for DANE data loaders."""
from __future__ import annotations

import io
from datetime import date

import duckdb

from scripts.econ_schema import init_db
from scripts.econ_dane import (
    parse_dane_ipc_csv,
    parse_dane_ipp_csv,
    parse_dane_release_calendar_csv,
    DaneIpcRow,
    DaneIppRow,
    DaneReleaseCalendarRow,
)

SAMPLE_IPC_CSV: str = """date,ipc_index,ipc_pct_change
2024-01-01,158.23,0.92
2024-02-01,158.89,0.42
2024-03-01,159.45,0.35
"""


def test_parse_dane_ipc_csv() -> None:
    """parse_dane_ipc_csv reads CSV into DaneIpcRow list."""
    rows = parse_dane_ipc_csv(io.StringIO(SAMPLE_IPC_CSV))
    assert len(rows) == 3
    assert rows[0] == DaneIpcRow(date=date(2024, 1, 1), ipc_index=158.23, ipc_pct_change=0.92)


def test_dane_ipc_insert_into_db() -> None:
    """Parsed IPC rows insert into dane_ipc_monthly."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    rows = parse_dane_ipc_csv(io.StringIO(SAMPLE_IPC_CSV))
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO dane_ipc_monthly (date, ipc_index, ipc_pct_change) VALUES (?, ?, ?)",
            [r.date, r.ipc_index, r.ipc_pct_change],
        )
    count = conn.execute("SELECT COUNT(*) FROM dane_ipc_monthly").fetchone()
    assert count is not None and count[0] == 3


SAMPLE_IPP_CSV: str = """date,ipp_index,ipp_pct_change
2024-01-01,210.50,0.55
2024-02-01,211.20,0.33
2024-03-01,211.80,0.28
"""


def test_parse_dane_ipp_csv() -> None:
    """parse_dane_ipp_csv reads CSV into DaneIppRow list."""
    rows = parse_dane_ipp_csv(io.StringIO(SAMPLE_IPP_CSV))
    assert len(rows) == 3
    assert rows[0] == DaneIppRow(date=date(2024, 1, 1), ipp_index=210.50, ipp_pct_change=0.55)


def test_dane_ipp_insert_into_db() -> None:
    """Parsed IPP rows insert into dane_ipp_monthly."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    rows = parse_dane_ipp_csv(io.StringIO(SAMPLE_IPP_CSV))
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO dane_ipp_monthly (date, ipp_index, ipp_pct_change) VALUES (?, ?, ?)",
            [r.date, r.ipp_index, r.ipp_pct_change],
        )
    count = conn.execute("SELECT COUNT(*) FROM dane_ipp_monthly").fetchone()
    assert count is not None and count[0] == 3


SAMPLE_RELEASE_CALENDAR_CSV: str = """year,month,release_date,series,imputed
2024,1,2024-02-07,ipc,false
2024,1,2024-02-07,ipp,false
2024,2,2024-03-06,ipc,false
2024,2,2024-03-06,ipp,false
"""


def test_parse_dane_release_calendar_csv() -> None:
    """parse_dane_release_calendar_csv reads calendar entries."""
    rows = parse_dane_release_calendar_csv(io.StringIO(SAMPLE_RELEASE_CALENDAR_CSV))
    assert len(rows) == 4
    assert rows[0] == DaneReleaseCalendarRow(
        year=2024, month=1, release_date=date(2024, 2, 7), series="ipc", imputed=False,
    )


def test_release_calendar_insert_into_db() -> None:
    """Parsed release calendar rows insert into dane_release_calendar."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    rows = parse_dane_release_calendar_csv(io.StringIO(SAMPLE_RELEASE_CALENDAR_CSV))
    for r in rows:
        conn.execute(
            "INSERT INTO dane_release_calendar (year, month, release_date, series, imputed) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT (year, month, series) DO UPDATE SET "
            "release_date = EXCLUDED.release_date, imputed = EXCLUDED.imputed",
            [r.year, r.month, r.release_date, r.series, r.imputed],
        )
    count = conn.execute("SELECT COUNT(*) FROM dane_release_calendar").fetchone()
    assert count is not None and count[0] == 4
