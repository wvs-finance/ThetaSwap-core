"""Schema DDL and initialization for the structural econometrics DuckDB.

All CREATE TABLE statements follow the spec:
contracts/notes/structural-econometrics/specs/2026-04-16-data-schema-acquisition.md (Rev 4)
"""
from __future__ import annotations

from typing import Final

import duckdb

# ── Expected tables ──────────────────────────────────────────────────────────

EXPECTED_TABLES: Final[frozenset[str]] = frozenset({
    "banrep_trm_daily",
    "banrep_ibr_daily",
    "banrep_intervention_daily",
    "banrep_meeting_calendar",
    "fred_daily",
    "fred_monthly",
    "dane_ipc_monthly",
    "dane_ipp_monthly",
    "dane_release_calendar",
    "bls_release_calendar",
    "download_manifest",
})

# ── DDL statements ───────────────────────────────────────────────────────────

_DDL_BANREP_TRM_DAILY: Final[str] = """
CREATE TABLE IF NOT EXISTS banrep_trm_daily (
    date DATE PRIMARY KEY,
    trm DOUBLE NOT NULL,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_BANREP_IBR_DAILY: Final[str] = """
CREATE TABLE IF NOT EXISTS banrep_ibr_daily (
    date DATE PRIMARY KEY,
    ibr_overnight_er DOUBLE NOT NULL,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_BANREP_INTERVENTION_DAILY: Final[str] = """
CREATE TABLE IF NOT EXISTS banrep_intervention_daily (
    date DATE PRIMARY KEY,
    discretionary DOUBLE,
    direct_purchase DOUBLE,
    put_volatility DOUBLE,
    call_volatility DOUBLE,
    put_reserve_accum DOUBLE,
    call_reserve_decum DOUBLE,
    ndf DOUBLE,
    fx_swaps DOUBLE,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_BANREP_MEETING_CALENDAR: Final[str] = """
CREATE TABLE IF NOT EXISTS banrep_meeting_calendar (
    year SMALLINT NOT NULL,
    meeting_date DATE NOT NULL,
    meeting_type VARCHAR NOT NULL,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (year, meeting_date)
)
"""

_DDL_FRED_DAILY: Final[str] = """
CREATE TABLE IF NOT EXISTS fred_daily (
    series_id VARCHAR NOT NULL CHECK (series_id IN ('VIXCLS', 'DCOILWTICO', 'DCOILBRENTEU', 'DFF')),
    date DATE NOT NULL,
    value DOUBLE,
    PRIMARY KEY (series_id, date)
)
"""

_DDL_FRED_MONTHLY: Final[str] = """
CREATE TABLE IF NOT EXISTS fred_monthly (
    series_id VARCHAR NOT NULL CHECK (series_id IN ('CPIAUCSL')),
    date DATE NOT NULL,
    value DOUBLE,
    PRIMARY KEY (series_id, date)
)
"""

_DDL_DANE_IPC_MONTHLY: Final[str] = """
CREATE TABLE IF NOT EXISTS dane_ipc_monthly (
    date DATE PRIMARY KEY,
    ipc_index DOUBLE,
    ipc_pct_change DOUBLE,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_DANE_IPP_MONTHLY: Final[str] = """
CREATE TABLE IF NOT EXISTS dane_ipp_monthly (
    date DATE PRIMARY KEY,
    ipp_index DOUBLE,
    ipp_pct_change DOUBLE,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_DANE_RELEASE_CALENDAR: Final[str] = """
CREATE TABLE IF NOT EXISTS dane_release_calendar (
    year SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    release_date DATE NOT NULL,
    series VARCHAR NOT NULL CHECK (series IN ('ipc', 'ipp')),
    imputed BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (year, month, series),
    UNIQUE (release_date, series)
)
"""

_DDL_BLS_RELEASE_CALENDAR: Final[str] = """
CREATE TABLE IF NOT EXISTS bls_release_calendar (
    year SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    release_date DATE NOT NULL,
    PRIMARY KEY (year, month),
    UNIQUE (release_date)
)
"""

_DDL_DOWNLOAD_MANIFEST: Final[str] = """
CREATE TABLE IF NOT EXISTS download_manifest (
    source VARCHAR NOT NULL,
    downloaded_at TIMESTAMP NOT NULL,
    row_count INTEGER,
    date_min DATE,
    date_max DATE,
    sha256 VARCHAR,
    url_or_path VARCHAR,
    status VARCHAR NOT NULL,
    notes VARCHAR,
    PRIMARY KEY (source, downloaded_at)
)
"""

_ALL_DDL: Final[tuple[str, ...]] = (
    _DDL_BANREP_TRM_DAILY,
    _DDL_BANREP_IBR_DAILY,
    _DDL_BANREP_INTERVENTION_DAILY,
    _DDL_BANREP_MEETING_CALENDAR,
    _DDL_FRED_DAILY,
    _DDL_FRED_MONTHLY,
    _DDL_DANE_IPC_MONTHLY,
    _DDL_DANE_IPP_MONTHLY,
    _DDL_DANE_RELEASE_CALENDAR,
    _DDL_BLS_RELEASE_CALENDAR,
    _DDL_DOWNLOAD_MANIFEST,
)


# ── Public API ───────────────────────────────────────────────────────────────


def init_db(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all raw tables if they don't exist. Idempotent."""
    for ddl in _ALL_DDL:
        conn.execute(ddl)
