"""Tests for FRED data fetchers."""
from __future__ import annotations

from datetime import date
from typing import Final

import duckdb

from scripts.econ_schema import init_db
from scripts.econ_fred import (
    parse_fred_observations,
    parse_bls_release_dates,
    FredObservation,
    BlsReleaseDate,
)

SAMPLE_FRED_RESPONSE: Final[dict] = {
    "observations": [
        {"date": "2024-01-02", "value": "12.45"},
        {"date": "2024-01-03", "value": "."},
        {"date": "2024-01-04", "value": "13.20"},
    ]
}


def test_parse_fred_observations() -> None:
    """parse_fred_observations converts '.' to None."""
    rows = parse_fred_observations(SAMPLE_FRED_RESPONSE, "VIXCLS")
    assert len(rows) == 3
    assert rows[0] == FredObservation(series_id="VIXCLS", date=date(2024, 1, 2), value=12.45)
    assert rows[1].value is None  # "." → None
    assert rows[2].value == 13.20


def test_fred_observations_insert_into_db() -> None:
    """Parsed FRED observations can be inserted into fred_daily."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    rows = parse_fred_observations(SAMPLE_FRED_RESPONSE, "VIXCLS")
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO fred_daily (series_id, date, value) VALUES (?, ?, ?)",
            [r.series_id, r.date, r.value],
        )
    count = conn.execute("SELECT COUNT(*) FROM fred_daily").fetchone()
    assert count is not None and count[0] == 3
    null_row = conn.execute("SELECT value FROM fred_daily WHERE date = '2024-01-03'").fetchone()
    assert null_row is not None and null_row[0] is None


def test_fred_monthly_insert() -> None:
    """CPIAUCSL monthly observations insert into fred_monthly."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    sample = {"observations": [
        {"date": "2024-01-01", "value": "308.417"},
        {"date": "2024-02-01", "value": "310.326"},
    ]}
    rows = parse_fred_observations(sample, "CPIAUCSL")
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO fred_monthly (series_id, date, value) VALUES (?, ?, ?)",
            [r.series_id, r.date, r.value],
        )
    count = conn.execute("SELECT COUNT(*) FROM fred_monthly").fetchone()
    assert count is not None and count[0] == 2


SAMPLE_BLS_DATES_RESPONSE: Final[dict] = {
    "release_dates": [
        {"release_id": "10", "date": "2024-01-11"},
        {"release_id": "10", "date": "2024-02-13"},
        {"release_id": "10", "date": "2024-03-12"},
    ]
}


def test_parse_bls_release_dates() -> None:
    """parse_bls_release_dates extracts year, month-1, release_date."""
    rows = parse_bls_release_dates(SAMPLE_BLS_DATES_RESPONSE)
    assert len(rows) == 3
    # Jan 2024 release covers Dec 2023 CPI
    assert rows[0] == BlsReleaseDate(year=2023, month=12, release_date=date(2024, 1, 11))
    assert rows[1] == BlsReleaseDate(year=2024, month=1, release_date=date(2024, 2, 13))


def test_bls_dates_insert_into_db() -> None:
    """Parsed BLS release dates insert into bls_release_calendar."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    rows = parse_bls_release_dates(SAMPLE_BLS_DATES_RESPONSE)
    for r in rows:
        conn.execute(
            "INSERT INTO bls_release_calendar (year, month, release_date) VALUES (?, ?, ?) "
            "ON CONFLICT (year, month) DO UPDATE SET release_date = EXCLUDED.release_date",
            [r.year, r.month, r.release_date],
        )
    count = conn.execute("SELECT COUNT(*) FROM bls_release_calendar").fetchone()
    assert count is not None and count[0] == 3
