"""Pure-function query API for the structural econometrics DuckDB.

Zero network dependencies — reads only from an open DuckDB connection.
All functions are pure free functions operating on a caller-supplied connection.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final

import duckdb
import pandas as pd

# ── Spec constants ───────────────────────────────────────────────────────────

PRIMARY_LHS: Final[str] = "rv_cuberoot"

PRIMARY_RHS: Final[tuple[str, ...]] = (
    "cpi_surprise_ar1",
    "us_cpi_surprise",
    "banrep_rate_surprise",
    "vix_avg",
    "intervention_dummy",
    "oil_return",
)

SUBSAMPLE_SPLITS: Final[tuple[date, date]] = (date(2015, 1, 5), date(2021, 1, 4))

# Tables that have a date column for coverage analysis
_DATE_TABLES: Final[dict[str, str]] = {
    "banrep_trm_daily": "date",
    "banrep_ibr_daily": "date",
    "banrep_intervention_daily": "date",
    "fred_daily": "date",
    "fred_monthly": "date",
    "dane_ipc_monthly": "date",
    "dane_ipp_monthly": "date",
    "dane_release_calendar": "release_date",
    "bls_release_calendar": "release_date",
    "weekly_panel": "week_start",
    "daily_panel": "date",
}

# ── Domain types ─────────────────────────────────────────────────────────────


class QueryError(Exception):
    """Raised when a query cannot be satisfied (missing table, bad filter)."""


@dataclass(frozen=True, slots=True)
class ManifestRow:
    """One row from the download_manifest table."""

    source: str
    downloaded_at: object  # TIMESTAMP — may be None
    row_count: int | None
    date_min: date | None
    date_max: date | None
    sha256: str | None
    url_or_path: str | None
    status: str
    notes: str | None


@dataclass(frozen=True, slots=True)
class DateCoverage:
    """Date range and NULL summary for a single table."""

    table: str
    row_count: int
    date_min: date
    date_max: date
    null_count: int


# ── Internal helpers ─────────────────────────────────────────────────────────


def _check_table(conn: duckdb.DuckDBPyConnection, table: str) -> None:
    """Raise QueryError if *table* does not exist in the database."""
    tables = {
        row[0]
        for row in conn.execute("SHOW TABLES").fetchall()
    }
    if table not in tables:
        raise QueryError(f"Table '{table}' not found in database")


def _date_filter(
    start: date | None,
    end: date | None,
    col: str = "week_start",
) -> tuple[str, list[object]]:
    """Build a WHERE clause fragment with parameter list for date filtering.

    Returns ("", []) when both bounds are None.
    """
    clauses: list[str] = []
    params: list[object] = []
    if start is not None:
        clauses.append(f"{col} >= ?")
        params.append(start)
    if end is not None:
        clauses.append(f"{col} <= ?")
        params.append(end)
    if not clauses:
        return "", []
    return " WHERE " + " AND ".join(clauses), params


# ── Public API ───────────────────────────────────────────────────────────────


def get_weekly_panel(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return the weekly_panel table as a DataFrame, optionally date-filtered."""
    _check_table(conn, "weekly_panel")
    where, params = _date_filter(start, end, col="week_start")
    sql = f"SELECT * FROM weekly_panel{where} ORDER BY week_start"
    return conn.execute(sql, params).fetchdf()


def get_daily_panel(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return the daily_panel table as a DataFrame, optionally date-filtered."""
    _check_table(conn, "daily_panel")
    where, params = _date_filter(start, end, col="date")
    sql = f"SELECT * FROM daily_panel{where} ORDER BY date"
    return conn.execute(sql, params).fetchdf()


def get_table_summary(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Return {table_name: row_count} for every table in the database."""
    tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]
    result: dict[str, int] = {}
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM \"{t}\"").fetchone()
        result[t] = int(count[0]) if count else 0
    return result


def get_manifest(conn: duckdb.DuckDBPyConnection) -> list[ManifestRow]:
    """Return all rows from download_manifest as ManifestRow instances."""
    _check_table(conn, "download_manifest")
    rows = conn.execute(
        "SELECT source, downloaded_at, row_count, date_min, date_max, "
        "sha256, url_or_path, status, notes "
        "FROM download_manifest ORDER BY source"
    ).fetchall()
    return [
        ManifestRow(
            source=r[0],
            downloaded_at=r[1],
            row_count=r[2],
            date_min=r[3],
            date_max=r[4],
            sha256=r[5],
            url_or_path=r[6],
            status=r[7],
            notes=r[8],
        )
        for r in rows
    ]


def get_date_coverage(
    conn: duckdb.DuckDBPyConnection,
) -> dict[str, DateCoverage]:
    """Return date range and NULL count for tables that have a date column."""
    existing = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    result: dict[str, DateCoverage] = {}
    for table, date_col in _DATE_TABLES.items():
        if table not in existing:
            continue
        row = conn.execute(
            f"SELECT COUNT(*), MIN(\"{date_col}\"), MAX(\"{date_col}\"), "
            f"SUM(CASE WHEN \"{date_col}\" IS NULL THEN 1 ELSE 0 END) "
            f"FROM \"{table}\""
        ).fetchone()
        if row and row[0] > 0:
            result[table] = DateCoverage(
                table=table,
                row_count=int(row[0]),
                date_min=row[1],
                date_max=row[2],
                null_count=int(row[3]),
            )
    return result


def get_panel_completeness(
    conn: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Per-column NULL and zero counts for both weekly_panel and daily_panel.

    Returns a DataFrame with columns: panel, column, null_count, zero_count.
    """
    records: list[dict[str, object]] = []
    # Types where = 0 comparison is valid
    _numeric_types = frozenset({
        "DOUBLE", "FLOAT", "REAL",
        "TINYINT", "SMALLINT", "INTEGER", "BIGINT",
        "UTINYINT", "USMALLINT", "UINTEGER", "UBIGINT",
        "HUGEINT", "DECIMAL",
    })
    for panel in ("weekly_panel", "daily_panel"):
        _check_table(conn, panel)
        col_info = conn.execute(f"DESCRIBE \"{panel}\"").fetchall()
        for col_row in col_info:
            col_name = col_row[0]
            col_type = col_row[1].upper().split("(")[0]  # strip precision
            is_numeric = col_type in _numeric_types
            zero_expr = (
                f"SUM(CASE WHEN \"{col_name}\" = 0 THEN 1 ELSE 0 END)"
                if is_numeric
                else "0"
            )
            row = conn.execute(
                f"SELECT "
                f"SUM(CASE WHEN \"{col_name}\" IS NULL THEN 1 ELSE 0 END), "
                f"{zero_expr} "
                f"FROM \"{panel}\""
            ).fetchone()
            records.append({
                "panel": panel,
                "column": col_name,
                "null_count": int(row[0]) if row and row[0] is not None else 0,
                "zero_count": int(row[1]) if row and row[1] is not None else 0,
            })
    return pd.DataFrame(records)


# ── Task 2: release-week / release-day filters ─────────────────────────────


def get_weekly_panel_release_only(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Weekly panel rows where CPI or PPI was released that week."""
    _check_table(conn, "weekly_panel")
    where, params = _date_filter(start, end, col="week_start")
    release_clause = "(is_cpi_release_week OR is_ppi_release_week)"
    if where:
        where += f" AND {release_clause}"
    else:
        where = f" WHERE {release_clause}"
    sql = f"SELECT * FROM weekly_panel{where} ORDER BY week_start"
    return conn.execute(sql, params).fetchdf()


def get_weekly_panel_by_release_type(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split release weeks into (cpi_only, ppi_only, both).

    cpi_only = is_cpi_release_week AND NOT is_ppi_release_week
    ppi_only = NOT is_cpi_release_week AND is_ppi_release_week
    both     = is_cpi_release_week AND is_ppi_release_week
    """
    _check_table(conn, "weekly_panel")
    where, params = _date_filter(start, end, col="week_start")
    base = f"SELECT * FROM weekly_panel{where} ORDER BY week_start"
    df = conn.execute(base, params).fetchdf()
    cpi_flag = df["is_cpi_release_week"].astype(bool)
    ppi_flag = df["is_ppi_release_week"].astype(bool)
    cpi_only = df[cpi_flag & ~ppi_flag].reset_index(drop=True)
    ppi_only = df[~cpi_flag & ppi_flag].reset_index(drop=True)
    both = df[cpi_flag & ppi_flag].reset_index(drop=True)
    return cpi_only, ppi_only, both


def get_daily_panel_release_days(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Daily panel rows where CPI or PPI was released that day."""
    _check_table(conn, "daily_panel")
    where, params = _date_filter(start, end, col="date")
    release_clause = "(is_cpi_release_day OR is_ppi_release_day)"
    if where:
        where += f" AND {release_clause}"
    else:
        where = f" WHERE {release_clause}"
    sql = f"SELECT * FROM daily_panel{where} ORDER BY date"
    return conn.execute(sql, params).fetchdf()


def get_weekly_panel_release_split(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split weekly panel into (release_weeks, non_release_weeks) for Levene test."""
    _check_table(conn, "weekly_panel")
    where, params = _date_filter(start, end, col="week_start")
    base = f"SELECT * FROM weekly_panel{where} ORDER BY week_start"
    df = conn.execute(base, params).fetchdf()
    is_release = (
        df["is_cpi_release_week"].astype(bool)
        | df["is_ppi_release_week"].astype(bool)
    )
    release_weeks = df[is_release].reset_index(drop=True)
    non_release_weeks = df[~is_release].reset_index(drop=True)
    return release_weeks, non_release_weeks
