"""Pure-function query API for the structural econometrics DuckDB.

Zero network dependencies — reads only from an open DuckDB connection.
All functions are pure free functions operating on a caller-supplied connection.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Final, Literal

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


# ── Task 11.M.6 types: Fed funds + BanRep IBR weekly series ─────────────────


@dataclass(frozen=True, slots=True)
class FedFundsWeekly:
    """One weekly-close observation of the FRED DFF series.

    ``week_start`` is the Friday the close was observed on; ``value`` is
    the DFF percent-per-annum figure. Friday anchoring mirrors the
    ``vix_friday_close`` convention already used in the Rev-4 weekly
    panel and is the operationally stable closure point for the US
    Federal Reserve's daily effective-rate publication.
    """

    week_start: date
    value: float


@dataclass(frozen=True, slots=True)
class BanrepIbrWeekly:
    """One weekly-close observation of the BanRep IBR overnight rate.

    ``week_start`` is the Friday the rate was observed on; ``value`` is
    the IBR overnight effective rate (``ibr_overnight_er``) as
    published by BanRep. Friday anchoring matches ``FedFundsWeekly``
    so (IBR − DFF) is computable on a single date-aligned frame.
    """

    week_start: date
    value: float


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


# ── Task 3: subsamples, surprise series, calendar alignment ──────────────


def get_weekly_panel_subsample(
    conn: duckdb.DuckDBPyConnection,
    split_date: date,
    start: date | None = None,
    end: date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split the weekly panel into (pre_split, post_split) at *split_date*.

    pre  = week_start <  split_date
    post = week_start >= split_date
    """
    _check_table(conn, "weekly_panel")
    where, params = _date_filter(start, end, col="week_start")
    sql = f"SELECT * FROM weekly_panel{where} ORDER BY week_start"
    df = conn.execute(sql, params).fetchdf()
    mask = df["week_start"] < pd.Timestamp(split_date)
    pre = df[mask].reset_index(drop=True)
    post = df[~mask].reset_index(drop=True)
    return pre, post


def get_surprise_series(
    conn: duckdb.DuckDBPyConnection,
    series: Literal["cpi", "us_cpi", "ppi"] = "cpi",
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return release-aligned surprise series for CPI, US CPI, or PPI.

    Columns: release_date, week_start, raw_pct_change, ar1_surprise, abs_surprise.
    """
    if series == "cpi":
        _check_table(conn, "dane_release_calendar")
        _check_table(conn, "dane_ipc_monthly")
        _check_table(conn, "weekly_panel")
        base = (
            "SELECT rc.release_date, wp.week_start, "
            "ipc.ipc_pct_change AS raw_pct_change, "
            "wp.cpi_surprise_ar1 AS ar1_surprise, "
            "ABS(wp.cpi_surprise_ar1) AS abs_surprise "
            "FROM dane_release_calendar rc "
            "JOIN dane_ipc_monthly ipc "
            "  ON ipc.date = make_date(rc.year, rc.month, 1) "
            "JOIN weekly_panel wp "
            "  ON wp.week_start = date_trunc('week', rc.release_date)::DATE "
            "WHERE rc.series = 'ipc'"
        )
        date_col = "wp.week_start"
    elif series == "us_cpi":
        _check_table(conn, "bls_release_calendar")
        _check_table(conn, "fred_monthly")
        _check_table(conn, "weekly_panel")
        base = (
            "SELECT rc.release_date, wp.week_start, "
            "fm.value AS raw_pct_change, "
            "wp.us_cpi_surprise AS ar1_surprise, "
            "ABS(wp.us_cpi_surprise) AS abs_surprise "
            "FROM bls_release_calendar rc "
            "JOIN fred_monthly fm "
            "  ON fm.date = make_date(rc.year, rc.month, 1) "
            "  AND fm.series_id = 'CPIAUCSL' "
            "JOIN weekly_panel wp "
            "  ON wp.week_start = date_trunc('week', rc.release_date)::DATE "
            "WHERE rc.release_date >= '2003-01-01'"
        )
        date_col = "wp.week_start"
    elif series == "ppi":
        _check_table(conn, "dane_release_calendar")
        _check_table(conn, "dane_ipp_monthly")
        _check_table(conn, "weekly_panel")
        base = (
            "SELECT rc.release_date, wp.week_start, "
            "ipp.ipp_pct_change AS raw_pct_change, "
            "wp.dane_ipp_pct AS ar1_surprise, "
            "ABS(wp.dane_ipp_pct) AS abs_surprise "
            "FROM dane_release_calendar rc "
            "JOIN dane_ipp_monthly ipp "
            "  ON ipp.date = make_date(rc.year, rc.month, 1) "
            "JOIN weekly_panel wp "
            "  ON wp.week_start = date_trunc('week', rc.release_date)::DATE "
            "WHERE rc.series = 'ipp'"
        )
        date_col = "wp.week_start"
    else:
        raise QueryError(f"Unknown surprise series: {series!r}")

    # Apply optional date filter on week_start
    params: list[object] = []
    if start is not None:
        base += f" AND {date_col} >= ?"
        params.append(start)
    if end is not None:
        base += f" AND {date_col} <= ?"
        params.append(end)

    base += " ORDER BY rc.release_date"
    return conn.execute(base, params).fetchdf()


def get_release_calendar_aligned(
    conn: duckdb.DuckDBPyConnection,
    series: Literal["ipc", "ipp", "bls"] = "ipc",
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return release calendar joined with actual monthly values.

    Columns: year, month, release_date, week_start, actual_value, pct_change, imputed.
    """
    if series == "ipc":
        _check_table(conn, "dane_release_calendar")
        _check_table(conn, "dane_ipc_monthly")
        base = (
            "SELECT rc.year, rc.month, rc.release_date, "
            "date_trunc('week', rc.release_date)::DATE AS week_start, "
            "ipc.ipc_index AS actual_value, "
            "ipc.ipc_pct_change AS pct_change, "
            "rc.imputed "
            "FROM dane_release_calendar rc "
            "JOIN dane_ipc_monthly ipc "
            "  ON ipc.date = make_date(rc.year, rc.month, 1) "
            "WHERE rc.series = 'ipc'"
        )
        date_col = "rc.release_date"
    elif series == "ipp":
        _check_table(conn, "dane_release_calendar")
        _check_table(conn, "dane_ipp_monthly")
        base = (
            "SELECT rc.year, rc.month, rc.release_date, "
            "date_trunc('week', rc.release_date)::DATE AS week_start, "
            "ipp.ipp_index AS actual_value, "
            "ipp.ipp_pct_change AS pct_change, "
            "rc.imputed "
            "FROM dane_release_calendar rc "
            "JOIN dane_ipp_monthly ipp "
            "  ON ipp.date = make_date(rc.year, rc.month, 1) "
            "WHERE rc.series = 'ipp'"
        )
        date_col = "rc.release_date"
    elif series == "bls":
        _check_table(conn, "bls_release_calendar")
        _check_table(conn, "fred_monthly")
        base = (
            "SELECT rc.year, rc.month, rc.release_date, "
            "date_trunc('week', rc.release_date)::DATE AS week_start, "
            "fm.value AS actual_value, "
            "NULL::DOUBLE AS pct_change, "
            "FALSE AS imputed "
            "FROM bls_release_calendar rc "
            "JOIN fred_monthly fm "
            "  ON fm.date = make_date(rc.year, rc.month, 1) "
            "  AND fm.series_id = 'CPIAUCSL'"
        )
        date_col = "rc.release_date"
    else:
        raise QueryError(f"Unknown calendar series: {series!r}")

    # Apply optional date filter on release_date
    params: list[object] = []
    if start is not None:
        base += f" AND {date_col} >= ?"
        params.append(start)
    if end is not None:
        base += f" AND {date_col} <= ?"
        params.append(end)

    base += " ORDER BY rc.release_date"
    return conn.execute(base, params).fetchdf()


# ── Task 4: RV exclusion, monthly panel, standardized PPI, intervention ────

import numpy as _np


def get_rv_excluding_release_day(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Weekly realised variance excluding CPI/PPI release days."""
    _check_table(conn, "daily_panel")
    where, params = _date_filter(start, end, col="week_start")
    release_clause = (
        "NOT is_cpi_release_day AND NOT is_ppi_release_day "
        "AND cop_usd_return IS NOT NULL"
    )
    if where:
        where += f" AND {release_clause}"
    else:
        where = f" WHERE {release_clause}"
    sql = (
        "SELECT week_start, "
        "SUM(cop_usd_return * cop_usd_return) AS rv_excl_release, "
        "POWER(SUM(cop_usd_return * cop_usd_return), 1.0/3.0) AS rv_excl_release_cuberoot, "
        "COUNT(*) AS n_trading_days_excl "
        f"FROM daily_panel{where} "
        "GROUP BY week_start "
        "ORDER BY week_start"
    )
    return conn.execute(sql, params).fetchdf()


def get_monthly_panel(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Monthly aggregation: RV, VIX, oil, intervention, CPI, PPI."""
    _check_table(conn, "daily_panel")
    _check_table(conn, "fred_daily")
    _check_table(conn, "banrep_intervention_daily")
    _check_table(conn, "dane_ipc_monthly")
    _check_table(conn, "dane_ipp_monthly")

    where, params = _date_filter(start, end, col="mr.month_start")
    sql = (
        "WITH monthly_rv AS ( "
        "  SELECT date_trunc('month', date)::DATE AS month_start, "
        "         SUM(cop_usd_return * cop_usd_return) AS rv_monthly, "
        "         CASE WHEN SUM(cop_usd_return * cop_usd_return) > 0 "
        "              THEN POWER(SUM(cop_usd_return * cop_usd_return), 1.0/3.0) "
        "              ELSE 0.0 END AS rv_monthly_cuberoot, "
        "         CASE WHEN SUM(cop_usd_return * cop_usd_return) > 0 "
        "              THEN LN(SUM(cop_usd_return * cop_usd_return)) "
        "              ELSE NULL END AS rv_monthly_log, "
        "         COUNT(*) AS n_trading_days "
        "  FROM daily_panel "
        "  WHERE cop_usd_return IS NOT NULL "
        "  GROUP BY date_trunc('month', date)::DATE "
        "), "
        "monthly_vix AS ( "
        "  SELECT date_trunc('month', date)::DATE AS month_start, "
        "         AVG(value) AS vix_avg "
        "  FROM fred_daily "
        "  WHERE series_id = 'VIXCLS' AND value IS NOT NULL "
        "  GROUP BY date_trunc('month', date)::DATE "
        "), "
        "monthly_oil AS ( "
        "  SELECT date_trunc('month', date)::DATE AS month_start, "
        "         CASE WHEN ARG_MIN(value, date) > 0 AND ARG_MAX(value, date) > 0 "
        "              THEN LN(ARG_MAX(value, date) / ARG_MIN(value, date)) "
        "              ELSE NULL END AS oil_return "
        "  FROM fred_daily "
        "  WHERE series_id = 'DCOILWTICO' AND value > 0 "
        "  GROUP BY date_trunc('month', date)::DATE "
        "), "
        "monthly_intervention AS ( "
        "  SELECT date_trunc('month', date)::DATE AS month_start, "
        "         CASE WHEN SUM(ABS(discretionary)) > 0 THEN 1 ELSE 0 END AS intervention_dummy, "
        "         SUM(discretionary) AS intervention_amount "
        "  FROM banrep_intervention_daily "
        "  GROUP BY date_trunc('month', date)::DATE "
        ") "
        "SELECT mr.month_start, mr.rv_monthly, mr.rv_monthly_cuberoot, "
        "  mr.rv_monthly_log, mr.n_trading_days, "
        "  ipc.ipc_pct_change AS dane_ipc_pct, "
        "  ipp.ipp_pct_change AS dane_ipp_pct, "
        "  mv.vix_avg, mo.oil_return, "
        "  COALESCE(mi.intervention_dummy, 0) AS intervention_dummy, "
        "  COALESCE(mi.intervention_amount, 0.0) AS intervention_amount "
        "FROM monthly_rv mr "
        "LEFT JOIN dane_ipc_monthly ipc ON ipc.date = mr.month_start "
        "LEFT JOIN dane_ipp_monthly ipp ON ipp.date = mr.month_start "
        "LEFT JOIN monthly_vix mv ON mv.month_start = mr.month_start "
        "LEFT JOIN monthly_oil mo ON mo.month_start = mr.month_start "
        f"LEFT JOIN monthly_intervention mi ON mi.month_start = mr.month_start"
        f"{where} "
        "ORDER BY mr.month_start"
    )
    return conn.execute(sql, params).fetchdf()


def get_standardized_ppi_change(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """IPP releases with expanding-window standardized surprise."""
    _check_table(conn, "dane_release_calendar")
    _check_table(conn, "dane_ipp_monthly")

    base = (
        "SELECT rc.release_date, "
        "date_trunc('week', rc.release_date)::DATE AS week_start, "
        "ipp.ipp_pct_change AS raw_ipp_pct "
        "FROM dane_release_calendar rc "
        "JOIN dane_ipp_monthly ipp "
        "  ON ipp.date = make_date(rc.year, rc.month, 1) "
        "WHERE rc.series = 'ipp'"
    )
    params: list[object] = []
    if start is not None:
        base += " AND rc.release_date >= ?"
        params.append(start)
    if end is not None:
        base += " AND rc.release_date <= ?"
        params.append(end)
    base += " ORDER BY rc.release_date"
    df = conn.execute(base, params).fetchdf()

    # Expanding-window standardization in Python
    raw = df["raw_ipp_pct"].values.astype(float)
    standardized = _np.full(len(raw), _np.nan)
    for i in range(2, len(raw)):  # need at least 2 obs for std
        window = raw[:i]
        mu = _np.nanmean(window)
        sigma = _np.nanstd(window, ddof=1)
        if sigma > 0:
            standardized[i] = (raw[i] - mu) / sigma
    df["standardized_ipp_change"] = standardized
    return df


def get_intervention_details(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Detailed BanRep intervention records with week_start."""
    _check_table(conn, "banrep_intervention_daily")
    where, params = _date_filter(start, end, col="date")
    sql = (
        "SELECT date, date_trunc('week', date)::DATE AS week_start, "
        "discretionary, direct_purchase, put_volatility, call_volatility, "
        "put_reserve_accum, call_reserve_decum, ndf, fx_swaps "
        f"FROM banrep_intervention_daily{where} "
        "ORDER BY date"
    )
    return conn.execute(sql, params).fetchdf()


# ── Task 11.M.6: Fed funds + BanRep IBR weekly loaders ──────────────────────


def load_fed_funds_weekly(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> tuple[FedFundsWeekly, ...]:
    """Return Friday-anchored weekly FRED DFF closes as frozen dataclasses.

    Pulls the Friday (isodow=5) close of the DFF daily series from
    ``fred_daily``. Returns a tuple of :class:`FedFundsWeekly` — an
    immutable, ordered collection keyed on ``week_start``. NULL
    observations in the raw series are filtered; callers needing a
    null-aware view should query the raw table directly.
    """
    _check_table(conn, "fred_daily")
    where, params = _date_filter(start, end, col="date")
    release_clause = (
        "series_id = 'DFF' AND value IS NOT NULL "
        "AND EXTRACT('isodow' FROM date) = 5"
    )
    if where:
        where += f" AND {release_clause}"
    else:
        where = f" WHERE {release_clause}"
    sql = f"SELECT date, value FROM fred_daily{where} ORDER BY date"
    rows = conn.execute(sql, params).fetchall()
    return tuple(
        FedFundsWeekly(week_start=r[0], value=float(r[1])) for r in rows
    )


def load_banrep_ibr_weekly(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> tuple[BanrepIbrWeekly, ...]:
    """Return Friday-anchored weekly BanRep IBR overnight ER closes.

    Pulls the Friday (isodow=5) close of the IBR overnight effective
    rate from ``banrep_ibr_daily``. Friday anchoring mirrors
    :func:`load_fed_funds_weekly` so the two series can be differenced
    row-wise to form the (IBR − DFF) carry-leg component of
    ``Y_asset_leg``.
    """
    _check_table(conn, "banrep_ibr_daily")
    where, params = _date_filter(start, end, col="date")
    release_clause = "EXTRACT('isodow' FROM date) = 5"
    if where:
        where += f" AND {release_clause}"
    else:
        where = f" WHERE {release_clause}"
    sql = (
        f"SELECT date, ibr_overnight_er FROM banrep_ibr_daily{where} "
        "ORDER BY date"
    )
    rows = conn.execute(sql, params).fetchall()
    return tuple(
        BanrepIbrWeekly(week_start=r[0], value=float(r[1])) for r in rows
    )


# ── Task 11.M.5: on-chain COPM / cCOP loaders ───────────────────────────────
#
# Nine pure loader functions — one per table ingested by
# :func:`scripts.econ_pipeline.run_onchain_migration`. Each returns a
# tuple of frozen dataclasses keyed by the table's natural order. Zero
# network calls; zero side effects. Follow the ``load_fed_funds_weekly``
# convention from Task 11.M.6.


@dataclass(frozen=True, slots=True)
class OnchainCopmMint:
    """One COPM ``mint`` call (146 total across 2024-09-17 → 2026-04-14).

    Keys: ``(tx_hash, call_block_time)`` is unique. ``amount_wei`` stored
    as Python int (DuckDB HUGEINT → int loss-free).
    """

    call_block_date: date
    call_block_time: datetime
    tx_hash: str
    tx_from: str
    to_address: str
    amount_wei: int
    call_success: bool
    call_block_number: int


@dataclass(frozen=True, slots=True)
class OnchainCopmBurn:
    """One COPM ``burn`` or ``burnFrozen`` call (121 total).

    ``account`` is nullable — ``burn`` variants that do not take an
    explicit account argument leave the column NULL.
    """

    call_block_date: date
    call_block_time: datetime
    tx_hash: str
    tx_from: str
    account: str | None
    amount_wei: int
    call_success: bool
    call_block_number: int
    burn_kind: str


@dataclass(frozen=True, slots=True)
class OnchainCopmTransferSample:
    """One row from the 10-row SAMPLE of COPM transfers.

    The full 110,069-row raw dataset is retrievable via Dune query
    7369028 (Dune web UI). The Dune MCP server paginates at 100 rows
    per call, so a complete MCP-based retrieval would require ~1,101
    paginated calls in a single agent session and is impractical.

    Downstream X_d filter-design code MUST treat these rows as a
    representative first-100-chronological sample rather than a
    complete series — the ``is_sample`` flag (default True) makes that
    contract explicit and unforgeable at the dataclass layer.
    """

    evt_block_date: date
    evt_block_time: datetime
    evt_tx_hash: str
    from_address: str
    to_address: str
    value_wei: int
    evt_block_number: int
    is_sample: bool = True


@dataclass(frozen=True, slots=True)
class OnchainCopmFreezeThaw:
    """One ``frozen``, ``thawed`` or ``burnedfrozen`` event (4 total)."""

    evt_block_date: date
    evt_block_time: datetime
    evt_tx_hash: str
    account: str
    amount_wei: int | None
    event_type: str
    evt_block_number: int


@dataclass(frozen=True, slots=True)
class OnchainCopmTopEdge:
    """One from→to volume-aggregate edge (top 100 by total_value_wei)."""

    from_address: str
    to_address: str
    n_transfers: int
    total_value_wei: int
    first_time: datetime
    last_time: datetime


@dataclass(frozen=True, slots=True)
class OnchainCopmDailyTransfer:
    """One daily-aggregate row (522 dates covered)."""

    evt_block_date: date
    n_transfers: int
    n_tx: int
    n_distinct_from: int
    n_distinct_to: int
    total_value_wei: int


@dataclass(frozen=True, slots=True)
class OnchainCopmAddressActivity:
    """One address with (inbound, outbound) activity counts + wei volume.

    Source CSV is named ``top400`` but the actual row count is 300 — the
    Dune query truncates at the activity threshold rather than a fixed
    rank. 300 covers the full observed active-address universe.
    """

    address: str
    n_inbound: int
    inbound_wei: int
    n_outbound: int
    outbound_wei: int


@dataclass(frozen=True, slots=True)
class OnchainCopmTimePattern:
    """One day-of-month / day-of-week / month bucket (86 rows)."""

    kind: str
    bucket: int
    n: int
    wei: int


@dataclass(frozen=True, slots=True)
class OnchainCcopDailyFlow:
    """One Task 11.A daily flow row (COPM + cCOP USD, 585 dates).

    ``ccop_*`` columns are NULL for pre-cCOP-launch dates
    (< 2024-10-31).
    """

    date: date
    copm_mint_usd: float
    copm_burn_usd: float
    copm_unique_minters: int
    ccop_usdt_inflow_usd: float | None
    ccop_usdt_outflow_usd: float | None
    ccop_unique_senders: int | None
    source_query_ids: str | None


# ── Loader functions ────────────────────────────────────────────────────────


def _parse_dune_timestamp(raw: str) -> datetime:
    """Parse a Dune ``YYYY-MM-DD HH:MM:SS.sss UTC`` text back to ``datetime``.

    Timestamp columns are stored as VARCHAR verbatim (see
    :mod:`scripts.econ_schema`) to preserve byte-exact CSV round-trip.
    Loaders that expose a ``datetime`` field re-parse the text here.
    """
    s = raw.strip()
    if s.endswith(" UTC"):
        s = s[:-4]
    # Support both "YYYY-MM-DD HH:MM:SS" and "YYYY-MM-DD HH:MM:SS.sss".
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"cannot parse Dune timestamp: {raw!r}")


def load_onchain_copm_mints(
    conn: duckdb.DuckDBPyConnection,
) -> tuple[OnchainCopmMint, ...]:
    """Return all 146 COPM mint calls as frozen dataclasses."""
    _check_table(conn, "onchain_copm_mints")
    rows = conn.execute(
        "SELECT call_block_date, call_block_time, tx_hash, tx_from, "
        "to_address, amount_wei, call_success, call_block_number "
        "FROM onchain_copm_mints "
        "ORDER BY call_block_number, tx_hash"
    ).fetchall()
    return tuple(
        OnchainCopmMint(
            call_block_date=r[0],
            call_block_time=_parse_dune_timestamp(r[1]),
            tx_hash=r[2],
            tx_from=r[3],
            to_address=r[4],
            amount_wei=int(r[5]),
            call_success=bool(r[6]),
            call_block_number=int(r[7]),
        )
        for r in rows
    )


def load_onchain_copm_burns(
    conn: duckdb.DuckDBPyConnection,
) -> tuple[OnchainCopmBurn, ...]:
    """Return all 121 COPM burn / burnFrozen calls as frozen dataclasses."""
    _check_table(conn, "onchain_copm_burns")
    rows = conn.execute(
        "SELECT call_block_date, call_block_time, tx_hash, tx_from, account, "
        "amount_wei, call_success, call_block_number, burn_kind "
        "FROM onchain_copm_burns "
        "ORDER BY call_block_number, tx_hash, burn_kind"
    ).fetchall()
    return tuple(
        OnchainCopmBurn(
            call_block_date=r[0],
            call_block_time=_parse_dune_timestamp(r[1]),
            tx_hash=r[2],
            tx_from=r[3],
            account=r[4],
            amount_wei=int(r[5]),
            call_success=bool(r[6]),
            call_block_number=int(r[7]),
            burn_kind=r[8],
        )
        for r in rows
    )


def load_onchain_copm_transfers(
    conn: duckdb.DuckDBPyConnection,
) -> tuple[OnchainCopmTransferSample, ...]:
    """Return the 10-row COPM transfer SAMPLE as frozen dataclasses.

    Every returned row carries ``is_sample=True``. The complete
    110,069-row raw dataset lives in Dune query 7369028; see
    :class:`OnchainCopmTransferSample` for the re-execution note.
    """
    _check_table(conn, "onchain_copm_transfers_sample")
    rows = conn.execute(
        "SELECT evt_block_date, evt_block_time, evt_tx_hash, from_address, "
        "to_address, value_wei, evt_block_number "
        "FROM onchain_copm_transfers_sample "
        "ORDER BY evt_block_number, evt_tx_hash, from_address, to_address"
    ).fetchall()
    return tuple(
        OnchainCopmTransferSample(
            evt_block_date=r[0],
            evt_block_time=_parse_dune_timestamp(r[1]),
            evt_tx_hash=r[2],
            from_address=r[3],
            to_address=r[4],
            value_wei=int(r[5]),
            evt_block_number=int(r[6]),
        )
        for r in rows
    )


def load_onchain_copm_freeze_thaw(
    conn: duckdb.DuckDBPyConnection,
) -> tuple[OnchainCopmFreezeThaw, ...]:
    """Return all 4 freeze/thaw/burnedfrozen events as frozen dataclasses."""
    _check_table(conn, "onchain_copm_freeze_thaw")
    rows = conn.execute(
        "SELECT evt_block_date, evt_block_time, evt_tx_hash, account, "
        "amount_wei, event_type, evt_block_number "
        "FROM onchain_copm_freeze_thaw "
        "ORDER BY evt_block_number, event_type"
    ).fetchall()
    return tuple(
        OnchainCopmFreezeThaw(
            evt_block_date=r[0],
            evt_block_time=_parse_dune_timestamp(r[1]),
            evt_tx_hash=r[2],
            account=r[3],
            amount_wei=(None if r[4] is None else int(r[4])),
            event_type=r[5],
            evt_block_number=int(r[6]),
        )
        for r in rows
    )


def load_onchain_copm_top100_edges(
    conn: duckdb.DuckDBPyConnection,
) -> tuple[OnchainCopmTopEdge, ...]:
    """Return the top 100 from→to volume edges as frozen dataclasses.

    Ordered by the stored ``_csv_row_idx`` (CSV-native row order) — the
    Dune CSV is sorted by ``n_transfers DESC`` which is NOT reproducible
    from ``ORDER BY total_value_wei DESC`` on the data columns alone.
    """
    _check_table(conn, "onchain_copm_transfers_top100_edges")
    rows = conn.execute(
        "SELECT from_address, to_address, n_transfers, total_value_wei, "
        "first_time, last_time "
        "FROM onchain_copm_transfers_top100_edges "
        "ORDER BY _csv_row_idx"
    ).fetchall()
    return tuple(
        OnchainCopmTopEdge(
            from_address=r[0],
            to_address=r[1],
            n_transfers=int(r[2]),
            total_value_wei=int(r[3]),
            first_time=_parse_dune_timestamp(r[4]),
            last_time=_parse_dune_timestamp(r[5]),
        )
        for r in rows
    )


def load_onchain_copm_daily_transfers(
    conn: duckdb.DuckDBPyConnection,
) -> tuple[OnchainCopmDailyTransfer, ...]:
    """Return 522 daily transfer aggregates as frozen dataclasses."""
    _check_table(conn, "onchain_copm_daily_transfers")
    rows = conn.execute(
        "SELECT evt_block_date, n_transfers, n_tx, n_distinct_from, "
        "n_distinct_to, total_value_wei "
        "FROM onchain_copm_daily_transfers "
        "ORDER BY evt_block_date"
    ).fetchall()
    return tuple(
        OnchainCopmDailyTransfer(
            evt_block_date=r[0],
            n_transfers=int(r[1]),
            n_tx=int(r[2]),
            n_distinct_from=int(r[3]),
            n_distinct_to=int(r[4]),
            total_value_wei=int(r[5]),
        )
        for r in rows
    )


def load_onchain_copm_address_activity(
    conn: duckdb.DuckDBPyConnection,
) -> tuple[OnchainCopmAddressActivity, ...]:
    """Return the 300 top-activity addresses as frozen dataclasses.

    Ordered by the stored ``_csv_row_idx`` (CSV-native row order) — the
    Dune CSV's tie-break on ``(n_inbound + n_outbound)`` is not a
    monotone function of any single column, so the source order is the
    only deterministic ordering available.
    """
    _check_table(conn, "onchain_copm_address_activity_top400")
    rows = conn.execute(
        "SELECT address, n_inbound, inbound_wei, n_outbound, outbound_wei "
        "FROM onchain_copm_address_activity_top400 "
        "ORDER BY _csv_row_idx"
    ).fetchall()
    return tuple(
        OnchainCopmAddressActivity(
            address=r[0],
            n_inbound=int(r[1]),
            inbound_wei=int(r[2]),
            n_outbound=int(r[3]),
            outbound_wei=int(r[4]),
        )
        for r in rows
    )


def load_onchain_copm_time_patterns(
    conn: duckdb.DuckDBPyConnection,
) -> tuple[OnchainCopmTimePattern, ...]:
    """Return 86 day-of-month / day-of-week / month buckets.

    ``bucket`` is stored as VARCHAR (lexical CSV order preserved) and
    cast back to int for the frozen-dataclass consumer contract.
    """
    _check_table(conn, "onchain_copm_time_patterns")
    rows = conn.execute(
        "SELECT kind, bucket, n, wei "
        "FROM onchain_copm_time_patterns "
        "ORDER BY kind, bucket"
    ).fetchall()
    return tuple(
        OnchainCopmTimePattern(
            kind=r[0],
            bucket=int(r[1]),
            n=int(r[2]),
            wei=int(r[3]),
        )
        for r in rows
    )


def load_onchain_daily_flow(
    conn: duckdb.DuckDBPyConnection,
) -> tuple[OnchainCcopDailyFlow, ...]:
    """Return the 585 Task 11.A daily COPM + cCOP USD flow rows.

    USD columns are stored as VARCHAR (6-decimal CSV text preserved)
    and cast back to ``float`` here for the frozen-dataclass consumer
    contract.
    """
    _check_table(conn, "onchain_copm_ccop_daily_flow")
    rows = conn.execute(
        "SELECT date, copm_mint_usd, copm_burn_usd, copm_unique_minters, "
        "ccop_usdt_inflow_usd, ccop_usdt_outflow_usd, ccop_unique_senders, "
        "source_query_ids "
        "FROM onchain_copm_ccop_daily_flow "
        "ORDER BY date"
    ).fetchall()
    return tuple(
        OnchainCcopDailyFlow(
            date=r[0],
            copm_mint_usd=float(r[1]),
            copm_burn_usd=float(r[2]),
            copm_unique_minters=int(r[3]),
            ccop_usdt_inflow_usd=(None if r[4] is None else float(r[4])),
            ccop_usdt_outflow_usd=(None if r[5] is None else float(r[5])),
            ccop_unique_senders=(None if r[6] is None else int(r[6])),
            source_query_ids=r[7],
        )
        for r in rows
    )
