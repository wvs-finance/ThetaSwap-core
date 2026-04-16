"""DANE data loaders: IPC, IPP, release calendar from CSV files.

DANE's API is unreliable. These functions parse manually downloaded CSV files.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from typing import IO


@dataclass(frozen=True, slots=True)
class DaneIpcRow:
    """One monthly IPC observation."""
    date: date
    ipc_index: float
    ipc_pct_change: float


@dataclass(frozen=True, slots=True)
class DaneIppRow:
    """One monthly IPP observation."""
    date: date
    ipp_index: float
    ipp_pct_change: float


@dataclass(frozen=True, slots=True)
class DaneReleaseCalendarRow:
    """One DANE release calendar entry."""
    year: int
    month: int
    release_date: date
    series: str
    imputed: bool


def parse_dane_ipc_csv(file: IO[str]) -> list[DaneIpcRow]:
    """Parse DANE IPC CSV: date, ipc_index, ipc_pct_change."""
    reader = csv.DictReader(file)
    rows: list[DaneIpcRow] = []
    for record in reader:
        rows.append(DaneIpcRow(
            date=datetime.strptime(record["date"], "%Y-%m-%d").date(),
            ipc_index=float(record["ipc_index"]),
            ipc_pct_change=float(record["ipc_pct_change"]),
        ))
    return rows


def parse_dane_ipp_csv(file: IO[str]) -> list[DaneIppRow]:
    """Parse DANE IPP CSV: date, ipp_index, ipp_pct_change."""
    reader = csv.DictReader(file)
    rows: list[DaneIppRow] = []
    for record in reader:
        rows.append(DaneIppRow(
            date=datetime.strptime(record["date"], "%Y-%m-%d").date(),
            ipp_index=float(record["ipp_index"]),
            ipp_pct_change=float(record["ipp_pct_change"]),
        ))
    return rows


def parse_dane_release_calendar_csv(file: IO[str]) -> list[DaneReleaseCalendarRow]:
    """Parse DANE release calendar CSV: year, month, release_date, series, imputed."""
    reader = csv.DictReader(file)
    rows: list[DaneReleaseCalendarRow] = []
    for record in reader:
        rows.append(DaneReleaseCalendarRow(
            year=int(record["year"]),
            month=int(record["month"]),
            release_date=datetime.strptime(record["release_date"], "%Y-%m-%d").date(),
            series=record["series"],
            imputed=record["imputed"].lower() in ("true", "1", "yes"),
        ))
    return rows
