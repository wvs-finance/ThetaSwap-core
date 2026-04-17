"""Tests for structural econometrics schema DDL."""
from __future__ import annotations

import duckdb
import pytest

from scripts.econ_schema import init_db, EXPECTED_TABLES


def test_init_db_creates_all_tables() -> None:
    """init_db creates exactly the 10 expected raw + calendar tables."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    assert tables == EXPECTED_TABLES


def test_init_db_is_idempotent() -> None:
    """Calling init_db twice does not error or duplicate tables."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    init_db(conn)  # second call
    tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    assert tables == EXPECTED_TABLES


def test_banrep_trm_daily_schema() -> None:
    """banrep_trm_daily has correct columns and types."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    cols = conn.execute("DESCRIBE banrep_trm_daily").fetchall()
    col_map = {c[0]: c[1] for c in cols}
    assert col_map["date"] == "DATE"
    assert col_map["trm"] == "DOUBLE"
    assert "_ingested_at" in col_map


def test_banrep_trm_daily_pk_enforced() -> None:
    """Duplicate date in banrep_trm_daily raises constraint error."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES ('2024-01-01', 3900.0)")
    with pytest.raises(duckdb.ConstraintException):
        conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES ('2024-01-01', 3901.0)")


def test_insert_or_replace_overwrites() -> None:
    """INSERT OR REPLACE on banrep_trm_daily updates the value."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    conn.execute("INSERT INTO banrep_trm_daily (date, trm) VALUES ('2024-01-01', 3900.0)")
    conn.execute("INSERT OR REPLACE INTO banrep_trm_daily (date, trm) VALUES ('2024-01-01', 3950.0)")
    result = conn.execute("SELECT trm FROM banrep_trm_daily WHERE date = '2024-01-01'").fetchone()
    assert result is not None
    assert result[0] == 3950.0


def test_download_manifest_append_only() -> None:
    """download_manifest allows multiple rows for same source."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    conn.execute(
        "INSERT INTO download_manifest (source, downloaded_at, status) "
        "VALUES ('banrep:trm', '2026-04-16 10:00:00', 'verified')"
    )
    conn.execute(
        "INSERT INTO download_manifest (source, downloaded_at, status) "
        "VALUES ('banrep:trm', '2026-04-16 10:00:01', 'success')"
    )
    count = conn.execute("SELECT COUNT(*) FROM download_manifest WHERE source = 'banrep:trm'").fetchone()
    assert count is not None and count[0] == 2


def test_fred_daily_check_constraint() -> None:
    """fred_daily rejects unknown series_id."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    with pytest.raises(duckdb.ConstraintException):
        conn.execute("INSERT INTO fred_daily (series_id, date, value) VALUES ('FAKE', '2024-01-01', 100.0)")


def test_banrep_intervention_daily_schema() -> None:
    """banrep_intervention_daily has all 8 intervention type columns."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    cols = conn.execute("DESCRIBE banrep_intervention_daily").fetchall()
    col_names = {c[0] for c in cols}
    expected = {"date", "discretionary", "direct_purchase", "put_volatility",
                "call_volatility", "put_reserve_accum", "call_reserve_decum",
                "ndf", "fx_swaps", "_ingested_at"}
    assert expected.issubset(col_names)


def test_banrep_ibr_daily_schema() -> None:
    """banrep_ibr_daily has date, ibr_overnight_er, _ingested_at."""
    conn = duckdb.connect(":memory:")
    init_db(conn)
    cols = conn.execute("DESCRIBE banrep_ibr_daily").fetchall()
    col_map = {c[0]: c[1] for c in cols}
    assert col_map["date"] == "DATE"
    assert col_map["ibr_overnight_er"] == "DOUBLE"
    assert "_ingested_at" in col_map
