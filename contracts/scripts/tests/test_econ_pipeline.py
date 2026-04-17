"""Tests for pipeline orchestrator, manifest logging, and validation."""
from __future__ import annotations

from datetime import date

import duckdb
import pytest

from scripts.econ_schema import init_db
from scripts.econ_pipeline import log_manifest, validate_weekly_panel, validate_daily_panel, ValidationError
from scripts.econ_panels import build_weekly_panel, build_daily_panel
from scripts.tests.test_econ_panels import _seed_trm, _seed_fred


# ── Manifest tests ──


def test_log_manifest_inserts_row() -> None:
    """log_manifest appends a row to download_manifest."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    log_manifest(conn, source="banrep:trm", status="success", row_count=8250,
                 date_min=date(1991, 12, 2), date_max=date(2026, 4, 16),
                 url_or_path="https://www.datos.gov.co/resource/32sa-8pi3.json")
    count = conn.execute("SELECT COUNT(*) FROM download_manifest").fetchone()
    assert count is not None and count[0] == 1


def test_log_manifest_append_only() -> None:
    """Multiple log_manifest calls for same source append, not overwrite."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    log_manifest(conn, source="banrep:trm", status="verified")
    log_manifest(conn, source="banrep:trm", status="success", row_count=8250)
    count = conn.execute("SELECT COUNT(*) FROM download_manifest WHERE source = 'banrep:trm'").fetchone()
    assert count is not None and count[0] == 2


# ── Validation tests ──


def test_validate_weekly_panel_passes_on_good_data() -> None:
    """validate_weekly_panel passes on a well-formed panel."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_weekly_panel(conn, sample_start=date(2024, 1, 8))
    validate_weekly_panel(conn)


def test_validate_weekly_panel_catches_null_surprise() -> None:
    """validate_weekly_panel raises if a surprise column contains NULL."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_weekly_panel(conn, sample_start=date(2024, 1, 8))
    conn.execute("UPDATE weekly_panel SET cpi_surprise_ar1 = NULL WHERE week_start = '2024-01-08'")
    with pytest.raises(ValidationError, match="NULL"):
        validate_weekly_panel(conn)


def test_validate_weekly_panel_catches_bad_intervention() -> None:
    """validate_weekly_panel raises if intervention_dummy not in {0, 1}."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_weekly_panel(conn, sample_start=date(2024, 1, 8))
    conn.execute("UPDATE weekly_panel SET intervention_dummy = 2 WHERE week_start = '2024-01-08'")
    with pytest.raises(ValidationError, match="intervention"):
        validate_weekly_panel(conn)


def test_validate_daily_panel_passes_on_good_data() -> None:
    """validate_daily_panel passes on a well-formed panel."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    _seed_trm(conn)
    _seed_fred(conn)
    build_daily_panel(conn, sample_start=date(2024, 1, 8))
    validate_daily_panel(conn)


def test_validate_missing_table_raises() -> None:
    """validate_weekly_panel raises if the table doesn't exist."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    with pytest.raises(ValidationError, match="does not exist"):
        validate_weekly_panel(conn)
