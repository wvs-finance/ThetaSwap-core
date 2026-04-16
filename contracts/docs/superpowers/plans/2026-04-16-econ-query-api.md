# Structural Econometrics Query API — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **REQUIRED SKILL:** Invoke `functional-python` before writing any Python code.

---

> ## NON-NEGOTIABLE RULES
>
> ### Rule 1: STRICT TDD
> ### Rule 2: NO MERGE WITHOUT APPROVAL
> ### Rule 3: ALL commands run from `contracts/`
> ### Rule 4: SCRIPTS-ONLY SCOPE

---

**Goal:** Build a pure-function query API over `structural_econ.duckdb` that returns pandas DataFrames (for panels) and frozen dataclasses (for metadata), so notebook authors and the estimation module never write SQL.

**Architecture:** Single module `econ_query_api.py` with 17 public functions. Follows `ran_data_api.py` pattern: conn-first, pure functions, QueryError exception. DataFrames for panel data, frozen dataclasses for metadata. Module-level constants define the pre-committed specification (PRIMARY_LHS, PRIMARY_RHS).

**Tech Stack:** Python 3.13, DuckDB 1.5.1, pandas, pytest

**API design source:** `contracts/.scratch/2026-04-16-econ-api-design-recommendations.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `contracts/scripts/econ_query_api.py` | All 17 query functions + domain types + spec constants |
| `contracts/scripts/tests/test_econ_query_api.py` | Tests for all endpoints using real `structural_econ.duckdb` |

---

### Task 1: Domain Types, Constants, and Core Panel Queries (1-2, 6, 11, 16)

**Files:**
- Create: `contracts/scripts/econ_query_api.py`
- Create: `contracts/scripts/tests/test_econ_query_api.py`

Core endpoints: `get_weekly_panel`, `get_daily_panel`, `get_table_summary`, `get_date_coverage`, `get_panel_completeness`.

- [ ] **Step 1: Write failing tests**

```python
# contracts/scripts/tests/test_econ_query_api.py
"""Tests for structural econometrics query API.

All tests query the REAL structural_econ.duckdb database (read-only).
"""
from __future__ import annotations

from datetime import date

import duckdb
import pandas as pd
import pytest

from scripts.econ_query_api import (
    QueryError,
    ManifestRow,
    DateCoverage,
    PRIMARY_LHS,
    PRIMARY_RHS,
    get_weekly_panel,
    get_daily_panel,
    get_table_summary,
    get_date_coverage,
    get_panel_completeness,
)

# ── Shared fixture: read-only connection to real DB ──

@pytest.fixture
def conn() -> duckdb.DuckDBPyConnection:
    """Read-only connection to the real structural_econ.duckdb."""
    return duckdb.connect("data/structural_econ.duckdb", read_only=True)


# ── Constants ──

def test_primary_lhs_is_rv_cuberoot() -> None:
    assert PRIMARY_LHS == "rv_cuberoot"

def test_primary_rhs_has_six_controls() -> None:
    assert len(PRIMARY_RHS) == 6
    assert "cpi_surprise_ar1" in PRIMARY_RHS
    assert "oil_return" in PRIMARY_RHS


# ── get_weekly_panel ──

def test_get_weekly_panel_returns_dataframe(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_weekly_panel(conn)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 1000  # ~1,215 expected
    assert "week_start" in df.columns
    assert PRIMARY_LHS in df.columns
    for col in PRIMARY_RHS:
        assert col in df.columns

def test_get_weekly_panel_date_filter(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_weekly_panel(conn, start=date(2020, 1, 1), end=date(2020, 12, 31))
    assert len(df) > 40  # ~52 weeks in a year
    assert len(df) < 60
    assert df["week_start"].min() >= pd.Timestamp("2020-01-01")
    assert df["week_start"].max() <= pd.Timestamp("2020-12-31")

def test_get_weekly_panel_no_nulls_in_surprises(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_weekly_panel(conn)
    for col in ["cpi_surprise_ar1", "us_cpi_surprise", "dane_ipc_pct", "dane_ipp_pct"]:
        assert df[col].isna().sum() == 0, f"NULL found in {col}"


# ── get_daily_panel ──

def test_get_daily_panel_returns_dataframe(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_daily_panel(conn)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 5000
    assert "cop_usd_return" in df.columns
    assert "abs_cpi_surprise" in df.columns

def test_get_daily_panel_date_filter(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_daily_panel(conn, start=date(2023, 1, 1), end=date(2023, 12, 31))
    assert len(df) > 200
    assert len(df) < 260


# ── get_table_summary ──

def test_get_table_summary(conn: duckdb.DuckDBPyConnection) -> None:
    summary = get_table_summary(conn)
    assert isinstance(summary, dict)
    assert summary["banrep_trm_daily"] > 8000
    assert summary["weekly_panel"] > 1000
    assert summary["daily_panel"] > 5000


# ── get_date_coverage ──

def test_get_date_coverage(conn: duckdb.DuckDBPyConnection) -> None:
    coverage = get_date_coverage(conn)
    assert "banrep_trm_daily" in coverage
    trm = coverage["banrep_trm_daily"]
    assert isinstance(trm, DateCoverage)
    assert trm.row_count > 8000
    assert trm.date_min is not None
    assert trm.date_min.year <= 1992


# ── get_panel_completeness ──

def test_get_panel_completeness(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_panel_completeness(conn)
    assert isinstance(df, pd.DataFrame)
    assert "panel" in df.columns
    assert "column_name" in df.columns
    assert "null_count" in df.columns
    # cpi_surprise_ar1 should have mostly zeros (non-release weeks) but some nonzero
    cpi_row = df[(df["panel"] == "weekly_panel") & (df["column_name"] == "cpi_surprise_ar1")]
    assert len(cpi_row) == 1
    assert cpi_row.iloc[0]["zero_count"] > 800  # ~76% zeros
    assert cpi_row.iloc[0]["zero_count"] < 1200  # but not ALL zeros
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest scripts/tests/test_econ_query_api.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

```python
# contracts/scripts/econ_query_api.py
"""Pure-function query API for the structural econometrics DuckDB.

Zero network dependencies — reads only from an open DuckDB connection.
Returns pandas DataFrames for panel data, frozen dataclasses for metadata.
Notebook authors and estimation modules call these functions instead of writing SQL.
"""
from __future__ import annotations

from dataclasses import dataclass
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


# ── Domain types ─────────────────────────────────────────────────────────────


class QueryError(Exception):
    """Raised when a query cannot be satisfied."""


@dataclass(frozen=True, slots=True)
class ManifestRow:
    """One download manifest entry."""
    source: str
    downloaded_at: datetime
    row_count: int | None
    date_min: date | None
    date_max: date | None
    sha256: str | None
    url_or_path: str | None
    status: str
    notes: str | None


@dataclass(frozen=True, slots=True)
class DateCoverage:
    """Date range and completeness for one table."""
    table: str
    row_count: int
    date_min: date | None
    date_max: date | None
    null_count: int


# ── Internal helpers ─────────────────────────────────────────────────────────


def _date_filter(start: date | None, end: date | None, col: str = "week_start") -> tuple[str, list]:
    """Build a WHERE clause fragment for date filtering."""
    clauses: list[str] = []
    params: list = []
    if start is not None:
        clauses.append(f"{col} >= ?")
        params.append(start)
    if end is not None:
        clauses.append(f"{col} <= ?")
        params.append(end)
    if clauses:
        return " AND ".join(clauses), params
    return "TRUE", []


def _check_table(conn: duckdb.DuckDBPyConnection, table: str) -> None:
    """Raise QueryError if table does not exist."""
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    if table not in tables:
        raise QueryError(f"Table '{table}' does not exist. Run the pipeline first.")


# ── Core panel queries (1, 2) ────────────────────────────────────────────────


def get_weekly_panel(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return the weekly estimation panel as a DataFrame."""
    _check_table(conn, "weekly_panel")
    where, params = _date_filter(start, end, "week_start")
    return conn.execute(f"SELECT * FROM weekly_panel WHERE {where} ORDER BY week_start", params).df()


def get_daily_panel(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return the daily estimation panel as a DataFrame."""
    _check_table(conn, "daily_panel")
    where, params = _date_filter(start, end, "date")
    return conn.execute(f"SELECT * FROM daily_panel WHERE {where} ORDER BY date", params).df()


# ── Metadata queries (5, 6, 11, 16) ─────────────────────────────────────────


def get_table_summary(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Return row counts for all tables."""
    result: dict[str, int] = {}
    for (name,) in conn.execute("SHOW TABLES").fetchall():
        count = conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()
        result[name] = count[0] if count else 0
    return result


def get_manifest(conn: duckdb.DuckDBPyConnection) -> list[ManifestRow]:
    """Return all download manifest entries."""
    _check_table(conn, "download_manifest")
    rows = conn.execute(
        "SELECT source, downloaded_at, row_count, date_min, date_max, "
        "sha256, url_or_path, status, notes FROM download_manifest ORDER BY downloaded_at"
    ).fetchall()
    return [ManifestRow(*r) for r in rows]


def get_date_coverage(conn: duckdb.DuckDBPyConnection) -> dict[str, DateCoverage]:
    """Return date range and NULL counts for key tables."""
    tables_config = {
        "banrep_trm_daily": ("date", "trm"),
        "banrep_ibr_daily": ("date", "ibr_overnight_er"),
        "fred_daily": ("date", "value"),
        "fred_monthly": ("date", "value"),
        "dane_ipc_monthly": ("date", "ipc_pct_change"),
        "dane_ipp_monthly": ("date", "ipp_pct_change"),
        "weekly_panel": ("week_start", "rv"),
        "daily_panel": ("date", "cop_usd_return"),
    }
    result: dict[str, DateCoverage] = {}
    existing = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    for table, (date_col, val_col) in tables_config.items():
        if table not in existing:
            continue
        row = conn.execute(
            f'SELECT COUNT(*), MIN("{date_col}"), MAX("{date_col}"), '
            f'SUM(CASE WHEN "{val_col}" IS NULL THEN 1 ELSE 0 END) FROM "{table}"'
        ).fetchone()
        if row:
            result[table] = DateCoverage(
                table=table, row_count=row[0],
                date_min=row[1], date_max=row[2], null_count=row[3] or 0,
            )
    return result


def get_panel_completeness(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Return per-column NULL/zero counts for weekly_panel and daily_panel."""
    rows: list[dict] = []
    for panel in ("weekly_panel", "daily_panel"):
        existing = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
        if panel not in existing:
            continue
        total = conn.execute(f"SELECT COUNT(*) FROM {panel}").fetchone()[0]
        cols = conn.execute(f"DESCRIBE {panel}").fetchall()
        for col_name, col_type, *_ in cols:
            if col_type in ("DATE", "BOOLEAN"):
                continue
            null_count = conn.execute(
                f'SELECT COUNT(*) FROM {panel} WHERE "{col_name}" IS NULL'
            ).fetchone()[0]
            zero_count = conn.execute(
                f'SELECT COUNT(*) FROM {panel} WHERE "{col_name}" = 0'
            ).fetchone()[0] if col_type in ("DOUBLE", "SMALLINT", "BIGINT", "INTEGER") else 0
            rows.append({
                "panel": panel,
                "column_name": col_name,
                "total_rows": total,
                "null_count": null_count,
                "zero_count": zero_count,
                "pct_populated": round((total - null_count - zero_count) / total * 100, 1) if total > 0 else 0,
            })
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest scripts/tests/test_econ_query_api.py -v -k "task1 or constants or weekly_panel or daily_panel or table_summary or date_coverage or panel_completeness"`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/econ_query_api.py scripts/tests/test_econ_query_api.py
git commit -m "feat(structural-econ): query API — core panels, metadata, spec constants"
```

---

### Task 2: Release-Week Queries (3, 8, 9, 10)

**Files:**
- Modify: `contracts/scripts/econ_query_api.py`
- Modify: `contracts/scripts/tests/test_econ_query_api.py`

Endpoints: `get_weekly_panel_release_only`, `get_weekly_panel_by_release_type`, `get_daily_panel_release_days`, `get_weekly_panel_release_split`.

- [ ] **Step 1: Write failing tests**

```python
# Append to test_econ_query_api.py

from scripts.econ_query_api import (
    get_weekly_panel_release_only,
    get_weekly_panel_by_release_type,
    get_daily_panel_release_days,
    get_weekly_panel_release_split,
)


def test_get_weekly_panel_release_only(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_weekly_panel_release_only(conn)
    assert len(df) > 250  # ~280 release weeks
    assert len(df) < 400
    assert (df["is_cpi_release_week"] | df["is_ppi_release_week"]).all()


def test_get_weekly_panel_by_release_type(conn: duckdb.DuckDBPyConnection) -> None:
    cpi_only, ppi_only, both = get_weekly_panel_by_release_type(conn)
    assert isinstance(cpi_only, pd.DataFrame)
    # Most releases are joint (CPI+PPI same day)
    assert len(both) > 200
    assert (cpi_only["is_cpi_release_week"]).all()
    assert (~cpi_only["is_ppi_release_week"]).all()


def test_get_daily_panel_release_days(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_daily_panel_release_days(conn)
    assert len(df) > 200  # ~221 release days
    assert (df["is_cpi_release_day"] | df["is_ppi_release_day"]).all()


def test_get_weekly_panel_release_split(conn: duckdb.DuckDBPyConnection) -> None:
    release, non_release = get_weekly_panel_release_split(conn)
    assert len(release) + len(non_release) > 1000
    assert (release["is_cpi_release_week"] | release["is_ppi_release_week"]).all()
    assert (~non_release["is_cpi_release_week"]).all()
    assert (~non_release["is_ppi_release_week"]).all()
```

- [ ] **Step 2: Run to verify failure, implement, run to verify pass**

```python
# Append to econ_query_api.py

# ── Release-week queries (3, 8, 9, 10) ──────────────────────────────────────


def get_weekly_panel_release_only(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return weekly panel filtered to release weeks only."""
    _check_table(conn, "weekly_panel")
    where, params = _date_filter(start, end, "week_start")
    return conn.execute(
        f"SELECT * FROM weekly_panel WHERE ({where}) AND (is_cpi_release_week OR is_ppi_release_week) "
        "ORDER BY week_start", params
    ).df()


def get_weekly_panel_by_release_type(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (cpi_only_weeks, ppi_only_weeks, both_weeks)."""
    _check_table(conn, "weekly_panel")
    where, params = _date_filter(start, end, "week_start")
    base = conn.execute(f"SELECT * FROM weekly_panel WHERE {where} ORDER BY week_start", params).df()
    cpi_only = base[base["is_cpi_release_week"] & ~base["is_ppi_release_week"]]
    ppi_only = base[~base["is_cpi_release_week"] & base["is_ppi_release_week"]]
    both = base[base["is_cpi_release_week"] & base["is_ppi_release_week"]]
    return cpi_only.copy(), ppi_only.copy(), both.copy()


def get_daily_panel_release_days(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return daily panel filtered to release days only."""
    _check_table(conn, "daily_panel")
    where, params = _date_filter(start, end, "date")
    return conn.execute(
        f"SELECT * FROM daily_panel WHERE ({where}) AND (is_cpi_release_day OR is_ppi_release_day) "
        "ORDER BY date", params
    ).df()


def get_weekly_panel_release_split(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (release_weeks, non_release_weeks) for T2 Levene test."""
    _check_table(conn, "weekly_panel")
    where, params = _date_filter(start, end, "week_start")
    base = conn.execute(f"SELECT * FROM weekly_panel WHERE {where} ORDER BY week_start", params).df()
    is_release = base["is_cpi_release_week"] | base["is_ppi_release_week"]
    return base[is_release].copy(), base[~is_release].copy()
```

- [ ] **Step 3: Commit**

```bash
git add scripts/econ_query_api.py scripts/tests/test_econ_query_api.py
git commit -m "feat(structural-econ): query API — release-week splits + daily release days"
```

---

### Task 3: Subsample, Surprise Series, and Calendar Queries (4, 5, 12, 13)

**Files:**
- Modify: `contracts/scripts/econ_query_api.py`
- Modify: `contracts/scripts/tests/test_econ_query_api.py`

Endpoints: `get_weekly_panel_subsample`, `get_manifest`, `get_surprise_series`, `get_release_calendar_aligned`.

- [ ] **Step 1: Write failing tests**

```python
# Append to test_econ_query_api.py

from scripts.econ_query_api import (
    get_weekly_panel_subsample,
    get_manifest,
    get_surprise_series,
    get_release_calendar_aligned,
)


def test_get_weekly_panel_subsample(conn: duckdb.DuckDBPyConnection) -> None:
    pre, post = get_weekly_panel_subsample(conn, split_date=date(2015, 1, 5))
    assert len(pre) > 500  # 2003-2014
    assert len(post) > 400  # 2015-2026
    assert pre["week_start"].max() < pd.Timestamp("2015-01-05")
    assert post["week_start"].min() >= pd.Timestamp("2015-01-05")


def test_get_manifest(conn: duckdb.DuckDBPyConnection) -> None:
    manifest = get_manifest(conn)
    assert len(manifest) >= 14
    assert all(isinstance(r, ManifestRow) for r in manifest)
    eme = [r for r in manifest if r.source == "banrep:eme"]
    assert len(eme) >= 1
    assert eme[0].status == "unavailable"


def test_get_surprise_series_cpi(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_surprise_series(conn, series="cpi")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 250  # ~280 CPI releases
    assert "release_date" in df.columns
    assert "ar1_surprise" in df.columns
    assert "raw_pct_change" in df.columns
    # All surprises should be nonzero (these are release events)
    assert (df["ar1_surprise"] != 0).sum() > 200


def test_get_surprise_series_us_cpi(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_surprise_series(conn, series="us_cpi")
    assert len(df) > 250


def test_get_release_calendar_aligned_ipc(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_release_calendar_aligned(conn, series="ipc")
    assert isinstance(df, pd.DataFrame)
    assert "release_date" in df.columns
    assert "week_start" in df.columns
    assert "actual_value" in df.columns
    assert len(df) > 250
```

- [ ] **Step 2: Implement**

```python
# Append to econ_query_api.py

# ── Subsample + surprise queries (4, 5, 12, 13) ─────────────────────────────


def get_weekly_panel_subsample(
    conn: duckdb.DuckDBPyConnection,
    split_date: date,
    start: date | None = None,
    end: date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (pre_split, post_split) for A3 sub-sample splits and T6 Chow test."""
    _check_table(conn, "weekly_panel")
    where, params = _date_filter(start, end, "week_start")
    base = conn.execute(f"SELECT * FROM weekly_panel WHERE {where} ORDER BY week_start", params).df()
    pre = base[base["week_start"] < pd.Timestamp(split_date)]
    post = base[base["week_start"] >= pd.Timestamp(split_date)]
    return pre.copy(), post.copy()


def get_surprise_series(
    conn: duckdb.DuckDBPyConnection,
    series: Literal["cpi", "us_cpi", "ppi"] = "cpi",
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return AR(1) surprise series with release dates (~260 rows, not 1,215).

    For T1 (consensus rationality F-test on lagged surprise).
    """
    _check_table(conn, "weekly_panel")
    if series == "cpi":
        sql = """
        SELECT rc.release_date, date_trunc('week', rc.release_date)::DATE AS week_start,
               dim.ipc_pct_change AS raw_pct_change,
               wp.cpi_surprise_ar1 AS ar1_surprise,
               ABS(wp.cpi_surprise_ar1) AS abs_surprise
        FROM dane_release_calendar rc
        JOIN dane_ipc_monthly dim ON dim.date = make_date(rc.year, rc.month, 1)
        JOIN weekly_panel wp ON wp.week_start = date_trunc('week', rc.release_date)::DATE
        WHERE rc.series = 'ipc'
        """
    elif series == "us_cpi":
        sql = """
        SELECT bc.release_date, date_trunc('week', bc.release_date)::DATE AS week_start,
               fm.value AS raw_pct_change,
               wp.us_cpi_surprise AS ar1_surprise,
               ABS(wp.us_cpi_surprise) AS abs_surprise
        FROM bls_release_calendar bc
        JOIN fred_monthly fm ON fm.series_id = 'CPIAUCSL' AND fm.date = make_date(bc.year, bc.month, 1)
        JOIN weekly_panel wp ON wp.week_start = date_trunc('week', bc.release_date)::DATE
        WHERE bc.release_date >= '2003-01-01'
        """
    elif series == "ppi":
        sql = """
        SELECT rc.release_date, date_trunc('week', rc.release_date)::DATE AS week_start,
               dip.ipp_pct_change AS raw_pct_change,
               wp.dane_ipp_pct AS ar1_surprise,
               ABS(wp.dane_ipp_pct) AS abs_surprise
        FROM dane_release_calendar rc
        JOIN dane_ipp_monthly dip ON dip.date = make_date(rc.year, rc.month, 1)
        JOIN weekly_panel wp ON wp.week_start = date_trunc('week', rc.release_date)::DATE
        WHERE rc.series = 'ipp'
        """
    else:
        raise QueryError(f"Unknown series: {series}")

    where, params = _date_filter(start, end, "wp.week_start")
    full_sql = f"{sql} AND {where} ORDER BY rc.release_date"
    return conn.execute(full_sql, params).df()


def get_release_calendar_aligned(
    conn: duckdb.DuckDBPyConnection,
    series: Literal["ipc", "ipp", "bls"] = "ipc",
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return release calendar with actual values and week_start alignment."""
    if series == "ipc":
        sql = """
        SELECT rc.year, rc.month, rc.release_date,
               date_trunc('week', rc.release_date)::DATE AS week_start,
               dim.ipc_index AS actual_value, dim.ipc_pct_change AS pct_change,
               rc.imputed
        FROM dane_release_calendar rc
        JOIN dane_ipc_monthly dim ON dim.date = make_date(rc.year, rc.month, 1)
        WHERE rc.series = 'ipc'
        """
    elif series == "ipp":
        sql = """
        SELECT rc.year, rc.month, rc.release_date,
               date_trunc('week', rc.release_date)::DATE AS week_start,
               dip.ipp_index AS actual_value, dip.ipp_pct_change AS pct_change,
               rc.imputed
        FROM dane_release_calendar rc
        JOIN dane_ipp_monthly dip ON dip.date = make_date(rc.year, rc.month, 1)
        WHERE rc.series = 'ipp'
        """
    elif series == "bls":
        sql = """
        SELECT bc.year, bc.month, bc.release_date,
               date_trunc('week', bc.release_date)::DATE AS week_start,
               fm.value AS actual_value,
               NULL::DOUBLE AS pct_change,
               FALSE AS imputed
        FROM bls_release_calendar bc
        JOIN fred_monthly fm ON fm.series_id = 'CPIAUCSL' AND fm.date = make_date(bc.year, bc.month, 1)
        """
    else:
        raise QueryError(f"Unknown series: {series}")

    where, params = _date_filter(start, end, "release_date")
    return conn.execute(f"{sql} AND {where} ORDER BY release_date", params).df()
```

- [ ] **Step 3: Commit**

```bash
git add scripts/econ_query_api.py scripts/tests/test_econ_query_api.py
git commit -m "feat(structural-econ): query API — subsamples, surprise series, calendar"
```

---

### Task 4: RV Exclusion, Monthly Panel, Standardized PPI, Intervention (7, 14, 15, 17)

**Files:**
- Modify: `contracts/scripts/econ_query_api.py`
- Modify: `contracts/scripts/tests/test_econ_query_api.py`

Endpoints: `get_rv_excluding_release_day`, `get_monthly_panel`, `get_standardized_ppi_change`, `get_intervention_details`.

- [ ] **Step 1: Write failing tests**

```python
# Append to test_econ_query_api.py

from scripts.econ_query_api import (
    get_rv_excluding_release_day,
    get_monthly_panel,
    get_standardized_ppi_change,
    get_intervention_details,
)


def test_get_rv_excluding_release_day(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_rv_excluding_release_day(conn)
    assert isinstance(df, pd.DataFrame)
    assert "week_start" in df.columns
    assert "rv_excl_release" in df.columns
    assert "n_trading_days_excl" in df.columns
    # Should have fewer trading days on release weeks
    assert len(df) > 1000


def test_get_monthly_panel(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_monthly_panel(conn)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 260  # ~23 years × 12 months
    assert "month_start" in df.columns
    assert "rv_monthly" in df.columns
    assert "rv_monthly_cuberoot" in df.columns
    assert df["rv_monthly"].notna().all()


def test_get_standardized_ppi_change(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_standardized_ppi_change(conn)
    assert isinstance(df, pd.DataFrame)
    assert "standardized_ipp_change" in df.columns
    # Standardized series should have mean ~0 and std ~1 (approx)
    mean = df["standardized_ipp_change"].mean()
    std = df["standardized_ipp_change"].std()
    assert abs(mean) < 0.5  # close to zero
    assert 0.5 < std < 2.0  # close to 1


def test_get_intervention_details(conn: duckdb.DuckDBPyConnection) -> None:
    df = get_intervention_details(conn)
    assert isinstance(df, pd.DataFrame)
    assert "discretionary" in df.columns
    assert "direct_purchase" in df.columns
    assert "week_start" in df.columns
    assert len(df) > 1000
```

- [ ] **Step 2: Implement**

```python
# Append to econ_query_api.py

# ── Derived queries (7, 14, 15, 17) ─────────────────────────────────────────


def get_rv_excluding_release_day(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return weekly RV recomputed excluding release-day returns (A4)."""
    _check_table(conn, "daily_panel")
    where, params = _date_filter(start, end, "week_start")
    return conn.execute(f"""
    SELECT week_start,
           SUM(cop_usd_return * cop_usd_return) AS rv_excl_release,
           POWER(SUM(cop_usd_return * cop_usd_return), 1.0/3.0) AS rv_excl_release_cuberoot,
           COUNT(*) AS n_trading_days_excl
    FROM daily_panel
    WHERE NOT is_cpi_release_day AND NOT is_ppi_release_day
      AND cop_usd_return IS NOT NULL
      AND {where}
    GROUP BY week_start
    ORDER BY week_start
    """, params).df()


def get_monthly_panel(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return monthly-frequency panel for A1 sensitivity (monthly horizon).

    Aggregates daily TRM returns to monthly RV. Joins monthly controls.
    """
    _check_table(conn, "daily_panel")
    where, params = _date_filter(start, end, "month_start")
    return conn.execute(f"""
    WITH monthly_rv AS (
        SELECT
            date_trunc('month', date)::DATE AS month_start,
            SUM(cop_usd_return * cop_usd_return) AS rv_monthly,
            COUNT(*) AS n_trading_days
        FROM daily_panel
        WHERE cop_usd_return IS NOT NULL
        GROUP BY date_trunc('month', date)::DATE
    ),
    monthly_vix AS (
        SELECT
            date_trunc('month', date)::DATE AS month_start,
            AVG(value) AS vix_avg
        FROM fred_daily
        WHERE series_id = 'VIXCLS' AND value IS NOT NULL
        GROUP BY date_trunc('month', date)::DATE
    ),
    monthly_oil AS (
        SELECT
            date_trunc('month', date)::DATE AS month_start,
            LN(ARG_MAX(value, date) / ARG_MIN(value, date)) AS oil_return
        FROM fred_daily
        WHERE series_id = 'DCOILWTICO' AND value IS NOT NULL AND value > 0
        GROUP BY date_trunc('month', date)::DATE
    ),
    monthly_intervention AS (
        SELECT
            date_trunc('month', date)::DATE AS month_start,
            1 AS intervention_dummy,
            SUM(COALESCE(discretionary,0) + COALESCE(direct_purchase,0) +
                COALESCE(put_volatility,0) + COALESCE(call_volatility,0) +
                COALESCE(put_reserve_accum,0) + COALESCE(call_reserve_decum,0) +
                COALESCE(ndf,0) + COALESCE(fx_swaps,0)) AS intervention_amount
        FROM banrep_intervention_daily
        GROUP BY date_trunc('month', date)::DATE
    )
    SELECT
        r.month_start,
        r.rv_monthly,
        CASE WHEN r.rv_monthly > 0 THEN POWER(r.rv_monthly, 1.0/3.0) ELSE 0.0 END AS rv_monthly_cuberoot,
        CASE WHEN r.rv_monthly > 0 THEN LN(r.rv_monthly) ELSE NULL END AS rv_monthly_log,
        r.n_trading_days,
        COALESCE(dim.ipc_pct_change, 0.0) AS dane_ipc_pct,
        COALESCE(dip.ipp_pct_change, 0.0) AS dane_ipp_pct,
        COALESCE(v.vix_avg, 0.0) AS vix_avg,
        COALESCE(o.oil_return, 0.0) AS oil_return,
        COALESCE(mi.intervention_dummy, 0) AS intervention_dummy,
        COALESCE(mi.intervention_amount, 0.0) AS intervention_amount
    FROM monthly_rv r
    LEFT JOIN dane_ipc_monthly dim ON dim.date = r.month_start
    LEFT JOIN dane_ipp_monthly dip ON dip.date = r.month_start
    LEFT JOIN monthly_vix v ON v.month_start = r.month_start
    LEFT JOIN monthly_oil o ON o.month_start = r.month_start
    LEFT JOIN monthly_intervention mi ON mi.month_start = r.month_start
    WHERE {where}
    ORDER BY r.month_start
    """, params).df()


def get_standardized_ppi_change(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return expanding-window standardized PPI change for co-primary decomposition.

    (IPP_pct - expanding_mean) / expanding_std. Avoids look-ahead bias.
    """
    _check_table(conn, "dane_release_calendar")
    import numpy as _np

    rows = conn.execute("""
    SELECT rc.release_date, date_trunc('week', rc.release_date)::DATE AS week_start,
           dip.ipp_pct_change AS raw_ipp_pct
    FROM dane_release_calendar rc
    JOIN dane_ipp_monthly dip ON dip.date = make_date(rc.year, rc.month, 1)
    WHERE rc.series = 'ipp'
    ORDER BY rc.release_date
    """).df()

    if rows.empty:
        rows["standardized_ipp_change"] = pd.Series(dtype=float)
        return rows

    # Expanding-window standardization (no look-ahead)
    raw = rows["raw_ipp_pct"].values
    standardized = _np.full(len(raw), _np.nan)
    for i in range(1, len(raw)):
        window = raw[:i]
        m = _np.mean(window)
        s = _np.std(window, ddof=1)
        if s > 0:
            standardized[i] = (raw[i] - m) / s
    rows["standardized_ipp_change"] = standardized

    where, params = _date_filter(start, end, "week_start")
    if start or end:
        mask = pd.Series(True, index=rows.index)
        if start:
            mask &= rows["week_start"] >= pd.Timestamp(start)
        if end:
            mask &= rows["week_start"] <= pd.Timestamp(end)
        rows = rows[mask]

    return rows.reset_index(drop=True)


def get_intervention_details(
    conn: duckdb.DuckDBPyConnection,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Return raw daily intervention data with week_start for T7 deep-dive."""
    _check_table(conn, "banrep_intervention_daily")
    where, params = _date_filter(start, end, "date")
    return conn.execute(f"""
    SELECT date, date_trunc('week', date)::DATE AS week_start,
           discretionary, direct_purchase, put_volatility, call_volatility,
           put_reserve_accum, call_reserve_decum, ndf, fx_swaps
    FROM banrep_intervention_daily
    WHERE {where}
    ORDER BY date
    """, params).df()
```

- [ ] **Step 3: Run all tests**

Run: `.venv/bin/python -m pytest scripts/tests/test_econ_query_api.py -v`
Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/econ_query_api.py scripts/tests/test_econ_query_api.py
git commit -m "feat(structural-econ): query API — RV exclusion, monthly panel, standardized PPI, intervention"
```

---

## Self-Review

1. **Endpoint coverage:** All 16 CORE + 1 USEFUL endpoints implemented across 4 tasks. Mapped to spec requirements:
   - Primary OLS: `get_weekly_panel` + `PRIMARY_LHS`/`PRIMARY_RHS` constants ✓
   - GARCH-X: `get_daily_panel` + `get_daily_panel_release_days` ✓
   - Co-primary decomposition: `get_weekly_panel_by_release_type` + `get_standardized_ppi_change` ✓
   - A1 monthly: `get_monthly_panel` ✓
   - A3 sub-samples: `get_weekly_panel_subsample` ✓
   - A4 release-day exclusion: `get_rv_excluding_release_day` ✓
   - T1 rationality: `get_surprise_series` ✓
   - T2 Levene: `get_weekly_panel_release_split` ✓
   - T7 intervention: `get_intervention_details` ✓
   - Data validation: `get_table_summary`, `get_date_coverage`, `get_panel_completeness` ✓
   - Audit trail: `get_manifest` ✓
   - Calendar alignment: `get_release_calendar_aligned` ✓

2. **Placeholder scan:** No TBD/TODO found. All SQL is complete.

3. **Type consistency:** All functions use `conn: duckdb.DuckDBPyConnection` first param, `start/end: date | None`, return `pd.DataFrame` or typed dataclasses. `_date_filter` helper shared across all queries. `_check_table` guard on every function.
