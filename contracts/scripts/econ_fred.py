"""FRED data fetchers: daily series, monthly series, BLS release dates.

Pure functions — no side effects except HTTP when explicitly called.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Final

import requests


@dataclass(frozen=True, slots=True)
class FredObservation:
    """One FRED observation."""
    series_id: str
    date: date
    value: float | None


@dataclass(frozen=True, slots=True)
class BlsReleaseDate:
    """One BLS CPI release date mapping."""
    year: int
    month: int
    release_date: date


_FRED_OBS_ENDPOINT: Final[str] = "https://api.stlouisfed.org/fred/series/observations"
_FRED_RELEASE_DATES_ENDPOINT: Final[str] = "https://api.stlouisfed.org/fred/release/dates"


def parse_fred_observations(data: dict, series_id: str) -> list[FredObservation]:
    """Parse FRED JSON response. Converts value='.' to None."""
    rows: list[FredObservation] = []
    for obs in data.get("observations", []):
        date_str = obs.get("date", "")
        value_str = obs.get("value", ".")
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        value = None if value_str.strip() == "." else float(value_str)
        rows.append(FredObservation(series_id=series_id, date=parsed_date, value=value))
    return rows


def fetch_fred_series(series_id: str, api_key: str, start: str = "2000-01-01") -> list[FredObservation]:
    """Fetch a FRED series via REST API."""
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
    }
    resp = requests.get(_FRED_OBS_ENDPOINT, params=params, timeout=60)
    resp.raise_for_status()
    return parse_fred_observations(resp.json(), series_id)


def parse_bls_release_dates(data: dict) -> list[BlsReleaseDate]:
    """Parse FRED release dates response.

    BLS CPI release in month M covers CPI for month M-1.
    E.g., release on 2024-01-11 -> CPI for December 2023 (year=2023, month=12).
    """
    rows: list[BlsReleaseDate] = []
    for entry in data.get("release_dates", []):
        release_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
        # The release covers the PRIOR month's CPI
        if release_date.month == 1:
            ref_year = release_date.year - 1
            ref_month = 12
        else:
            ref_year = release_date.year
            ref_month = release_date.month - 1
        rows.append(BlsReleaseDate(year=ref_year, month=ref_month, release_date=release_date))
    return rows


def fetch_bls_release_dates(api_key: str) -> list[BlsReleaseDate]:
    """Fetch BLS CPI release dates from FRED."""
    params = {
        "release_id": "10",
        "api_key": api_key,
        "file_type": "json",
    }
    resp = requests.get(_FRED_RELEASE_DATES_ENDPOINT, params=params, timeout=60)
    resp.raise_for_status()
    return parse_bls_release_dates(resp.json())
