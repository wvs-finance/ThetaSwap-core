"""Tests for econ_query_api — pure-function query API for structural_econ.duckdb.

All tests use the REAL database (data/structural_econ.duckdb) in read-only mode.
No mocks — real econometric data built by the pipeline.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Final

import duckdb
import pandas as pd
import pytest

# ── Constants ────────────────────────────────────────────────────────────────

DB_PATH: Final[str] = str(
    Path(__file__).resolve().parents[2] / "data" / "structural_econ.duckdb"
)


# ── Fixture ──────────────────────────────────────────────────────────────────


@pytest.fixture
def conn() -> duckdb.DuckDBPyConnection:
    """Read-only connection to the real structural econometrics database."""
    c = duckdb.connect(DB_PATH, read_only=True)
    yield c
    c.close()


# ── Batch 1: spec constants ─────────────────────────────────────────────────


def test_primary_lhs_is_rv_cuberoot() -> None:
    from scripts.econ_query_api import PRIMARY_LHS

    assert PRIMARY_LHS == "rv_cuberoot"


def test_primary_rhs_has_six_controls() -> None:
    from scripts.econ_query_api import PRIMARY_RHS

    assert len(PRIMARY_RHS) == 6
    assert "cpi_surprise_ar1" in PRIMARY_RHS
    assert "us_cpi_surprise" in PRIMARY_RHS
    assert "banrep_rate_surprise" in PRIMARY_RHS
    assert "vix_avg" in PRIMARY_RHS
    assert "intervention_dummy" in PRIMARY_RHS
    assert "oil_return" in PRIMARY_RHS


def test_subsample_splits_are_dates() -> None:
    from scripts.econ_query_api import SUBSAMPLE_SPLITS

    assert len(SUBSAMPLE_SPLITS) == 2
    assert SUBSAMPLE_SPLITS[0] == date(2015, 1, 5)
    assert SUBSAMPLE_SPLITS[1] == date(2021, 1, 4)


# ── Batch 2: QueryError + domain types ──────────────────────────────────────


def test_query_error_is_exception() -> None:
    from scripts.econ_query_api import QueryError

    assert issubclass(QueryError, Exception)
    err = QueryError("missing table")
    assert str(err) == "missing table"


def test_manifest_row_is_frozen_dataclass() -> None:
    from dataclasses import fields, is_dataclass

    from scripts.econ_query_api import ManifestRow

    assert is_dataclass(ManifestRow)
    # frozen check: setting attr should raise
    row = ManifestRow(
        source="test",
        downloaded_at=None,
        row_count=0,
        date_min=None,
        date_max=None,
        sha256="abc",
        url_or_path="http://x",
        status="ok",
        notes="",
    )
    with pytest.raises(AttributeError):
        row.source = "changed"  # type: ignore[misc]
    names = {f.name for f in fields(ManifestRow)}
    assert names == {
        "source",
        "downloaded_at",
        "row_count",
        "date_min",
        "date_max",
        "sha256",
        "url_or_path",
        "status",
        "notes",
    }


def test_date_coverage_is_frozen_dataclass() -> None:
    from dataclasses import fields, is_dataclass

    from scripts.econ_query_api import DateCoverage

    assert is_dataclass(DateCoverage)
    cov = DateCoverage(
        table="t", row_count=10, date_min=date(2020, 1, 1),
        date_max=date(2024, 1, 1), null_count=0,
    )
    with pytest.raises(AttributeError):
        cov.table = "changed"  # type: ignore[misc]
    names = {f.name for f in fields(DateCoverage)}
    assert names == {"table", "row_count", "date_min", "date_max", "null_count"}


# ── Batch 3: get_weekly_panel ────────────────────────────────────────────────


def test_get_weekly_panel_returns_dataframe(conn: duckdb.DuckDBPyConnection) -> None:
    from scripts.econ_query_api import PRIMARY_LHS, PRIMARY_RHS, get_weekly_panel

    df = get_weekly_panel(conn)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 1000
    # Must contain the spec columns
    assert PRIMARY_LHS in df.columns
    for rhs in PRIMARY_RHS:
        assert rhs in df.columns


def test_get_weekly_panel_date_filter(conn: duckdb.DuckDBPyConnection) -> None:
    from scripts.econ_query_api import get_weekly_panel

    df = get_weekly_panel(conn, start=date(2020, 1, 1), end=date(2020, 12, 31))
    # ~52 weeks in 2020, but boundary effects may reduce slightly
    assert 40 <= len(df) <= 55


def test_get_weekly_panel_no_nulls_in_surprises(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    from scripts.econ_query_api import get_weekly_panel

    df = get_weekly_panel(conn)
    for col in ("cpi_surprise_ar1", "us_cpi_surprise"):
        assert df[col].isna().sum() == 0, f"{col} has NULLs"


# ── Batch 4: get_daily_panel ─────────────────────────────────────────────────


def test_get_daily_panel_returns_dataframe(conn: duckdb.DuckDBPyConnection) -> None:
    from scripts.econ_query_api import get_daily_panel

    df = get_daily_panel(conn)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 5000


def test_get_daily_panel_date_filter(conn: duckdb.DuckDBPyConnection) -> None:
    from scripts.econ_query_api import get_daily_panel

    df = get_daily_panel(conn, start=date(2023, 1, 1), end=date(2023, 12, 31))
    # ~250 trading days in 2023
    assert 200 <= len(df) <= 270


# ── Batch 5: get_table_summary ───────────────────────────────────────────────


def test_get_table_summary(conn: duckdb.DuckDBPyConnection) -> None:
    from scripts.econ_query_api import get_table_summary

    summary = get_table_summary(conn)
    assert isinstance(summary, dict)
    assert summary["banrep_trm_daily"] > 8000
    assert summary["weekly_panel"] > 1000
    assert "daily_panel" in summary
    assert "download_manifest" in summary


# ── Batch 6: get_date_coverage ───────────────────────────────────────────────


def test_get_date_coverage(conn: duckdb.DuckDBPyConnection) -> None:
    from scripts.econ_query_api import DateCoverage, get_date_coverage

    cov = get_date_coverage(conn)
    assert isinstance(cov, dict)
    assert "banrep_trm_daily" in cov
    trm = cov["banrep_trm_daily"]
    assert isinstance(trm, DateCoverage)
    # TRM data starts in the early 1990s
    assert trm.date_min.year <= 1992


# ── Batch 7: get_panel_completeness ─────────────────────────────────────────


def test_get_panel_completeness(conn: duckdb.DuckDBPyConnection) -> None:
    from scripts.econ_query_api import get_panel_completeness

    df = get_panel_completeness(conn)
    assert isinstance(df, pd.DataFrame)
    # cpi_surprise_ar1 is zero on ~76% of non-release weeks
    row = df[df["column"] == "cpi_surprise_ar1"]
    assert len(row) > 0
    zero_count = row.iloc[0]["zero_count"]
    assert 800 <= zero_count <= 1200


# ── Batch 8: get_manifest ───────────────────────────────────────────────────


def test_get_manifest(conn: duckdb.DuckDBPyConnection) -> None:
    from scripts.econ_query_api import ManifestRow, get_manifest

    rows = get_manifest(conn)
    assert len(rows) >= 14
    assert all(isinstance(r, ManifestRow) for r in rows)
    # banrep:eme should be unavailable
    eme = [r for r in rows if r.source == "banrep:eme"]
    assert len(eme) == 1
    assert eme[0].status == "unavailable"


# ── Batch 9: release-week filters ──────────────────────────────────────────


def test_get_weekly_panel_release_only(conn: duckdb.DuckDBPyConnection) -> None:
    from scripts.econ_query_api import get_weekly_panel_release_only

    df = get_weekly_panel_release_only(conn)
    assert isinstance(df, pd.DataFrame)
    assert 250 < len(df) < 400
    # Every row must have at least one release flag True
    for _, row in df.iterrows():
        assert row["is_cpi_release_week"] or row["is_ppi_release_week"]


def test_get_weekly_panel_by_release_type(conn: duckdb.DuckDBPyConnection) -> None:
    from scripts.econ_query_api import get_weekly_panel_by_release_type

    cpi_only, ppi_only, both = get_weekly_panel_by_release_type(conn)
    assert isinstance(cpi_only, pd.DataFrame)
    assert isinstance(ppi_only, pd.DataFrame)
    assert isinstance(both, pd.DataFrame)
    # Most releases are joint
    assert len(both) > 200
    # cpi_only rows: is_cpi=True AND is_ppi=False
    for _, row in cpi_only.iterrows():
        assert row["is_cpi_release_week"] is True or row["is_cpi_release_week"] == 1
        assert row["is_ppi_release_week"] is False or row["is_ppi_release_week"] == 0


def test_get_daily_panel_release_days(conn: duckdb.DuckDBPyConnection) -> None:
    from scripts.econ_query_api import get_daily_panel_release_days

    df = get_daily_panel_release_days(conn)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 200
    # Every row must have at least one release-day flag True
    for _, row in df.iterrows():
        assert row["is_cpi_release_day"] or row["is_ppi_release_day"]


def test_get_weekly_panel_release_split(conn: duckdb.DuckDBPyConnection) -> None:
    from scripts.econ_query_api import get_weekly_panel_release_split

    release, non_release = get_weekly_panel_release_split(conn)
    assert isinstance(release, pd.DataFrame)
    assert isinstance(non_release, pd.DataFrame)
    # Together they cover the full panel
    assert len(release) + len(non_release) > 1000
    # Release rows all have at least one flag True
    for _, row in release.iterrows():
        assert row["is_cpi_release_week"] or row["is_ppi_release_week"]
    # Non-release rows have both flags False
    for _, row in non_release.iterrows():
        assert not row["is_cpi_release_week"]
        assert not row["is_ppi_release_week"]
