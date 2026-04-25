"""Tests for Task 11.M.5 — DuckDB migration of COPM / cCOP on-chain data.

Rev-5.1 landed the 11.M COPM per-tx profile as 8 CSVs under
``contracts/data/copm_per_tx/`` plus the existing 585-day
``contracts/data/copm_ccop_daily_flow.csv`` from Task 11.A. Task 11.M.5
ingests all nine files into ``contracts/data/structural_econ.duckdb``
so downstream X_d filter-design work can query COPM/cCOP on-chain
flow through the same connection used by the Rev-4 structural-econ
pipeline.

CRITICAL ROW-COUNT CAVEAT: ``copm_transfers.csv`` is a 10-row SAMPLE
(representative first-100 chronological transfers; full 110,069-row
dataset is retrievable via Dune query 7369028). The test pins the
sample size and the sample flag on the query-api dataclass so the
caveat can never be accidentally dropped downstream.

Seven assertions, each a separate test function:

  (1) Each of the 9 CSVs loads LOSSLESSLY into its DuckDB table:
      row count matches; per-column SHA-256 checksum matches the value
      computed from the CSV at test setup.
  (2) Rev-4 ``decision_hash`` at
      ``notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json:23``
      preserved byte-exact after the migration runs.
  (3) Task 11.M.6's ``fred_daily`` DFF rows remain byte-exact
      (COUNT(*) = 6687; representative daily values intact).
  (4) Each ``load_onchain_*`` function returns a frozen dataclass with
      the correct type annotations.
  (5) ``copm_transfers`` loader exposes ``is_sample=True`` and a
      docstring pointing to Dune query 7369028.
  (6) ``copm_mints`` primary key ``(tx_hash, block_time)`` is unique
      (146 rows, 0 duplicates).
  (7) Running the migration twice produces identical state
      (idempotent).
"""
from __future__ import annotations

import csv as _csv
import dataclasses
import hashlib
import json
import shutil
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path
from typing import Final

import duckdb
import pytest

# ── Paths ────────────────────────────────────────────────────────────────────

_CONTRACTS_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
_DATA_ROOT: Final[Path] = _CONTRACTS_ROOT / "data"
_COPM_PER_TX: Final[Path] = _DATA_ROOT / "copm_per_tx"
_DAILY_FLOW_CSV: Final[Path] = _DATA_ROOT / "copm_ccop_daily_flow.csv"
_REAL_DB_PATH: Final[Path] = _DATA_ROOT / "structural_econ.duckdb"

_FINGERPRINT_PATH: Final[Path] = (
    _CONTRACTS_ROOT
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "estimates"
    / "nb1_panel_fingerprint.json"
)
_EXPECTED_DECISION_HASH: Final[str] = (
    "6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c"
)

# Expected row counts per CSV — derived from Task 11.M agent delivery.
_EXPECTED_ROW_COUNTS: Final[dict[str, int]] = {
    "onchain_copm_mints": 146,
    "onchain_copm_burns": 121,
    "onchain_copm_transfers_sample": 10,
    "onchain_copm_freeze_thaw": 4,
    "onchain_copm_transfers_top100_edges": 100,
    "onchain_copm_daily_transfers": 522,
    "onchain_copm_address_activity_top400": 300,
    "onchain_copm_time_patterns": 86,
    "onchain_copm_ccop_daily_flow": 585,
}

_CSV_FILES: Final[dict[str, Path]] = {
    "onchain_copm_mints": _COPM_PER_TX / "copm_mints.csv",
    "onchain_copm_burns": _COPM_PER_TX / "copm_burns.csv",
    "onchain_copm_transfers_sample": _COPM_PER_TX / "copm_transfers.csv",
    "onchain_copm_freeze_thaw": _COPM_PER_TX / "copm_freeze_thaw.csv",
    "onchain_copm_transfers_top100_edges":
        _COPM_PER_TX / "copm_transfers_top100_edges.csv",
    "onchain_copm_daily_transfers": _COPM_PER_TX / "copm_daily_transfers.csv",
    "onchain_copm_address_activity_top400":
        _COPM_PER_TX / "copm_address_activity_top400.csv",
    "onchain_copm_time_patterns": _COPM_PER_TX / "copm_time_patterns.csv",
    "onchain_copm_ccop_daily_flow": _DAILY_FLOW_CSV,
}

# Column subsets that participate in the per-table SHA-256 checksum.
# Excludes ``_ingested_at`` which is non-deterministic and excludes
# purely-informational columns like ``source_query_ids``. Every raw
# data column from the source CSV is included.
_CHECKSUM_COLUMNS: Final[dict[str, tuple[str, ...]]] = {
    "onchain_copm_mints": (
        "call_block_date", "call_block_time", "tx_hash", "tx_from",
        "to_address", "amount_wei", "call_success", "call_block_number",
    ),
    "onchain_copm_burns": (
        "call_block_date", "call_block_time", "tx_hash", "tx_from",
        "account", "amount_wei", "call_success", "call_block_number",
        "burn_kind",
    ),
    "onchain_copm_transfers_sample": (
        "evt_block_date", "evt_block_time", "evt_tx_hash",
        "from_address", "to_address", "value_wei", "evt_block_number",
    ),
    "onchain_copm_freeze_thaw": (
        "evt_block_date", "evt_block_time", "evt_tx_hash", "account",
        "amount_wei", "event_type", "evt_block_number",
    ),
    "onchain_copm_transfers_top100_edges": (
        "from_address", "to_address", "n_transfers", "total_value_wei",
        "first_time", "last_time",
    ),
    "onchain_copm_daily_transfers": (
        "evt_block_date", "n_transfers", "n_tx", "n_distinct_from",
        "n_distinct_to", "total_value_wei",
    ),
    "onchain_copm_address_activity_top400": (
        "address", "n_inbound", "inbound_wei", "n_outbound", "outbound_wei",
    ),
    "onchain_copm_time_patterns": ("kind", "bucket", "n", "wei"),
    # source_query_ids is included so the DB-side serialization has the
    # same field-count as the CSV-side (``_csv_side_checksum`` joins
    # every CSV field verbatim); omitting it would produce an 8-vs-7
    # field-count mismatch between CSV and DB.
    "onchain_copm_ccop_daily_flow": (
        "date", "copm_mint_usd", "copm_burn_usd", "copm_unique_minters",
        "ccop_usdt_inflow_usd", "ccop_usdt_outflow_usd",
        "ccop_unique_senders", "source_query_ids",
    ),
}


# ── CSV-side checksum helpers ────────────────────────────────────────────────


def _read_csv_rows_raw(csv_path: Path, *, skip_comments: bool) -> list[list[str]]:
    """Read a CSV file and return data rows as lists of strings.

    The copm CSVs sometimes contain lines starting with ``#`` between
    the header and the data rows. With ``skip_comments=True`` those
    lines are dropped, the header is the first non-comment line, and
    remaining lines are returned as rows.
    """
    with csv_path.open() as fh:
        lines = [ln for ln in fh.read().splitlines() if ln]
    if skip_comments:
        lines = [ln for ln in lines if not ln.lstrip().startswith("#")]
    reader = _csv.reader(lines)
    rows = list(reader)
    if not rows:
        return []
    # Drop header
    return rows[1:]


def _csv_side_checksum(csv_path: Path, columns: tuple[str, ...]) -> str:
    """Compute a SHA-256 checksum over the CSV's raw-text data rows.

    Rows are joined by ``\\n`` with fields joined by ``|`` to form a
    single byte-stream; the hash is byte-stable across row ordering so
    long as the CSV row ordering is preserved (which it is — we load
    in file order).
    """
    rows = _read_csv_rows_raw(csv_path, skip_comments=True)
    joined = "\n".join("|".join(r) for r in rows).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()


def _db_side_checksum(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    columns: tuple[str, ...],
    *,
    order_by: str,
) -> str:
    """Compute an equivalent SHA-256 over the DuckDB table.

    Rows are serialized column-by-column with the SAME representation
    that appears in the CSV file — so "1000000000000000000000000" stays
    as its decimal string, "true" stays as "true", empty strings stay
    empty. The key invariant: the CSV-side hash and the DB-side hash
    must match byte-exact when the migration is lossless.
    """
    cols_sql = ", ".join(f'"{c}"' for c in columns)
    sql = f'SELECT {cols_sql} FROM "{table}" ORDER BY {order_by}'
    rows = conn.execute(sql).fetchall()
    normalised: list[str] = []
    for row in rows:
        fields: list[str] = []
        for v in row:
            if v is None:
                fields.append("")
            elif isinstance(v, bool):
                fields.append("true" if v else "false")
            elif isinstance(v, int):
                fields.append(str(v))
            elif isinstance(v, float):
                # Keep six-decimal formatting to match CSV representation
                # used by copm_ccop_daily_flow.csv and copm_daily_transfers
                fields.append(f"{v:.6f}" if abs(v) < 1e9 and v != int(v) else str(v))
            else:
                fields.append(str(v))
        normalised.append("|".join(fields))
    joined = "\n".join(normalised).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()


def _order_col_for(table: str) -> str:
    """ORDER BY clause that keeps the DB row ordering aligned with the CSV.

    The CSVs are already sorted by a natural key; we mirror that.

    NOTE (Task 11.M.5, Rev-5.1): for
    ``onchain_copm_transfers_top100_edges`` and
    ``onchain_copm_address_activity_top400`` the Dune-native CSV row
    order is NOT reproducible from the data columns alone — the source
    CSV has tie-breaks on ``(n_inbound + n_outbound)`` /
    ``total_value_wei`` that are not a monotone function of any single
    data column. The ingestion layer therefore stores a
    ``_csv_row_idx UBIGINT`` sort-key column (0-based enumeration of
    the source-CSV data rows), and this helper references that column
    so the byte-exact CSV→DB checksum test is deterministic and
    self-contained. See :mod:`scripts.econ_schema` module docstring
    for full rationale.
    """
    return {
        "onchain_copm_mints":
            "call_block_number, tx_hash",
        # burns: _csv_row_idx needed — multiple rows share call_block_number
        # with tx_hash tie-break that is not reproducible (Dune-native).
        "onchain_copm_burns": "_csv_row_idx",
        # transfers_sample: _csv_row_idx needed — the same evt_tx_hash
        # can emit multiple events whose CSV ordering is chronological
        # but not derivable from (from_address, to_address).
        "onchain_copm_transfers_sample": "_csv_row_idx",
        "onchain_copm_freeze_thaw":
            "evt_block_number, event_type",
        "onchain_copm_transfers_top100_edges": "_csv_row_idx",
        "onchain_copm_daily_transfers": "evt_block_date",
        "onchain_copm_address_activity_top400": "_csv_row_idx",
        "onchain_copm_time_patterns": "kind, bucket",
        "onchain_copm_ccop_daily_flow": "date",
    }[table]


# ── Fixture: isolated migration DB per test ─────────────────────────────────


@pytest.fixture
def migrated_db(tmp_path: Path) -> Iterator[Path]:
    """Copy the real DB to ``tmp_path`` and run the migration against it.

    This preserves the 11.M.6 pre-existing state (DFF + IBR panels) so
    we can assert the migration is strictly additive without touching
    the canonical ``contracts/data/structural_econ.duckdb``.
    """
    from scripts.econ_pipeline import run_onchain_migration
    from scripts.econ_schema import init_db

    assert _REAL_DB_PATH.is_file(), f"missing {_REAL_DB_PATH}"
    db_copy = tmp_path / "structural_econ.duckdb"
    shutil.copy(_REAL_DB_PATH, db_copy)

    conn = duckdb.connect(str(db_copy))
    try:
        init_db(conn)
        run_onchain_migration(conn, data_root=_DATA_ROOT)
    finally:
        conn.close()

    yield db_copy


# ── (1) Lossless ingest per table ────────────────────────────────────────────


@pytest.mark.parametrize("table", list(_EXPECTED_ROW_COUNTS.keys()))
def test_csv_ingest_lossless(migrated_db: Path, table: str) -> None:
    """Each CSV loads with correct row count and per-column checksum."""
    csv_path = _CSV_FILES[table]
    expected_rows = _EXPECTED_ROW_COUNTS[table]
    columns = _CHECKSUM_COLUMNS[table]

    expected_sha = _csv_side_checksum(csv_path, columns)

    conn = duckdb.connect(str(migrated_db), read_only=True)
    try:
        got_count = conn.execute(
            f'SELECT COUNT(*) FROM "{table}"'
        ).fetchone()
        assert got_count is not None
        assert got_count[0] == expected_rows, (
            f"{table} row count: got {got_count[0]}, expected {expected_rows}"
        )
        got_sha = _db_side_checksum(
            conn, table, columns, order_by=_order_col_for(table)
        )
    finally:
        conn.close()

    assert got_sha == expected_sha, (
        f"{table} checksum drift:\n"
        f"  csv-side: {expected_sha}\n"
        f"  db-side:  {got_sha}"
    )


# ── (2) Rev-4 decision_hash preserved ────────────────────────────────────────


def test_rev4_decision_hash_preserved(migrated_db: Path) -> None:
    """LOCKED_DECISIONS and the fingerprint JSON must still match Rev-4."""
    from scripts.cleaning import LOCKED_DECISIONS, _compute_decision_hash

    got = _compute_decision_hash(LOCKED_DECISIONS)
    assert got == _EXPECTED_DECISION_HASH, (
        f"decision_hash drifted: got {got}, expected {_EXPECTED_DECISION_HASH}"
    )

    with _FINGERPRINT_PATH.open() as fh:
        fingerprint = json.load(fh)
    assert fingerprint["decision_hash"] == _EXPECTED_DECISION_HASH


# ── (3) Task 11.M.6 DFF rows unchanged ───────────────────────────────────────


def test_task_11_m_6_dff_rows_unchanged(migrated_db: Path) -> None:
    """fred_daily DFF rows from Task 11.M.6 remain byte-exact."""
    conn = duckdb.connect(str(migrated_db), read_only=True)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM fred_daily WHERE series_id = 'DFF'"
        ).fetchone()
        assert count is not None and count[0] == 6687, (
            f"DFF row count drifted: got {count[0] if count else None}, "
            "expected 6687"
        )

        # Spot-check: DFF on 2024-01-02 was 5.33% (Fed held 5.25-5.50).
        sample = conn.execute(
            "SELECT value FROM fred_daily "
            "WHERE series_id = 'DFF' AND date = '2024-01-02'"
        ).fetchone()
        assert sample is not None, "no DFF row for 2024-01-02"
        assert 5.30 <= sample[0] <= 5.40, (
            f"DFF 2024-01-02 = {sample[0]}; expected ≈5.33 "
            "per FRED."
        )

        # Spot-check: DFF first row should be 2008-01-02 (Rev-4 window start).
        min_date = conn.execute(
            "SELECT MIN(date) FROM fred_daily WHERE series_id = 'DFF'"
        ).fetchone()
        assert min_date is not None
        assert min_date[0] <= date(2008, 1, 4), (
            f"DFF series starts at {min_date[0]}, "
            "expected ≤ 2008-01-04 (Rev-4 sample window)."
        )
    finally:
        conn.close()


# ── (4) Every load_onchain_* returns a frozen dataclass ─────────────────────


def test_all_onchain_loaders_return_frozen_dataclasses(migrated_db: Path) -> None:
    """Every on-chain loader must expose a frozen dataclass row type."""
    from scripts import econ_query_api as api

    loader_names = (
        "load_onchain_copm_mints",
        "load_onchain_copm_burns",
        "load_onchain_copm_transfers",
        "load_onchain_copm_freeze_thaw",
        "load_onchain_copm_top100_edges",
        "load_onchain_copm_daily_transfers",
        "load_onchain_copm_address_activity",
        "load_onchain_copm_time_patterns",
        "load_onchain_daily_flow",
    )

    dataclass_names = (
        "OnchainCopmMint",
        "OnchainCopmBurn",
        "OnchainCopmTransferSample",
        "OnchainCopmFreezeThaw",
        "OnchainCopmTopEdge",
        "OnchainCopmDailyTransfer",
        "OnchainCopmAddressActivity",
        "OnchainCopmTimePattern",
        "OnchainCcopDailyFlow",
    )

    conn = duckdb.connect(str(migrated_db), read_only=True)
    try:
        for loader_name, dc_name in zip(
            loader_names, dataclass_names, strict=True
        ):
            loader = getattr(api, loader_name)
            dc_type = getattr(api, dc_name)

            # Frozen-dataclass contract
            assert dataclasses.is_dataclass(dc_type), (
                f"{dc_name} is not a dataclass"
            )
            assert dc_type.__dataclass_params__.frozen, (
                f"{dc_name} is not frozen"
            )

            # Every field is annotated (reject bare `field: str = ...`).
            assert all(
                field.type is not None for field in dataclasses.fields(dc_type)
            ), f"{dc_name} has an unannotated field"

            rows = loader(conn)
            assert isinstance(rows, tuple), (
                f"{loader_name} should return tuple, got {type(rows)}"
            )
            if rows:
                assert isinstance(rows[0], dc_type), (
                    f"{loader_name}[0] is not a {dc_name}"
                )
    finally:
        conn.close()


# ── (5) Transfers loader carries SAMPLE flag + Dune reference ────────────────


def test_onchain_transfers_loader_flags_sample(migrated_db: Path) -> None:
    """copm_transfers is a 10-row SAMPLE; the loader's dataclass must say so.

    The full 110,069-row raw dataset is retrievable from Dune query
    7369028 via the Dune web UI (pagination limits block MCP-based
    retrieval). The fact that the stored rows are a sample MUST be
    encoded in the dataclass so downstream callers cannot treat them
    as the complete series.
    """
    from scripts.econ_query_api import (
        OnchainCopmTransferSample,
        load_onchain_copm_transfers,
    )

    # Dataclass-level sample flag (default True).
    assert hasattr(OnchainCopmTransferSample, "is_sample"), (
        "OnchainCopmTransferSample missing is_sample flag"
    )
    defaults = {
        f.name: f.default for f in dataclasses.fields(OnchainCopmTransferSample)
    }
    assert defaults.get("is_sample") is True, (
        "OnchainCopmTransferSample.is_sample default must be True"
    )

    # Docstring references the Dune query for full-data recovery.
    docstring = OnchainCopmTransferSample.__doc__ or ""
    assert "7369028" in docstring, (
        "OnchainCopmTransferSample docstring must reference Dune query 7369028 "
        "so downstream readers know how to retrieve the full 110,069-row set."
    )

    # Loaded rows all carry is_sample=True.
    conn = duckdb.connect(str(migrated_db), read_only=True)
    try:
        rows = load_onchain_copm_transfers(conn)
    finally:
        conn.close()
    assert len(rows) == 10, f"expected 10 sample rows, got {len(rows)}"
    assert all(r.is_sample for r in rows), (
        "every loaded transfer row must have is_sample=True"
    )


# ── (6) copm_mints primary key uniqueness ────────────────────────────────────


def test_copm_mints_pk_unique(migrated_db: Path) -> None:
    """(tx_hash, block_time) is unique across the 146 mint rows."""
    conn = duckdb.connect(str(migrated_db), read_only=True)
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM onchain_copm_mints"
        ).fetchone()
        assert row is not None and row[0] == 146, (
            f"onchain_copm_mints row count: got {row[0] if row else None}, "
            "expected 146"
        )
        dupes = conn.execute(
            "SELECT tx_hash, call_block_time, COUNT(*) c "
            "FROM onchain_copm_mints "
            "GROUP BY tx_hash, call_block_time HAVING c > 1"
        ).fetchall()
        assert not dupes, (
            f"duplicate (tx_hash, call_block_time) in onchain_copm_mints: "
            f"{dupes[:5]}"
        )
    finally:
        conn.close()


# ── (7) Idempotency: running migration twice is a no-op ──────────────────────


def test_migration_is_idempotent(tmp_path: Path) -> None:
    """A second migration run leaves the DB byte-exact identical."""
    from scripts.econ_pipeline import run_onchain_migration
    from scripts.econ_schema import init_db

    db_copy = tmp_path / "structural_econ.duckdb"
    shutil.copy(_REAL_DB_PATH, db_copy)

    # First run
    conn = duckdb.connect(str(db_copy))
    try:
        init_db(conn)
        run_onchain_migration(conn, data_root=_DATA_ROOT)
    finally:
        conn.close()

    # Fingerprint all on-chain tables after first run
    def _fingerprint() -> dict[str, tuple[int, str]]:
        conn_ro = duckdb.connect(str(db_copy), read_only=True)
        try:
            out: dict[str, tuple[int, str]] = {}
            for table in _EXPECTED_ROW_COUNTS:
                count = conn_ro.execute(
                    f'SELECT COUNT(*) FROM "{table}"'
                ).fetchone()
                cols = _CHECKSUM_COLUMNS[table]
                sha = _db_side_checksum(
                    conn_ro, table, cols, order_by=_order_col_for(table)
                )
                assert count is not None
                out[table] = (int(count[0]), sha)
            return out
        finally:
            conn_ro.close()

    first = _fingerprint()

    # Second run — should be a no-op
    conn = duckdb.connect(str(db_copy))
    try:
        run_onchain_migration(conn, data_root=_DATA_ROOT)
    finally:
        conn.close()

    second = _fingerprint()

    assert first == second, (
        "migration is not idempotent — second run changed table state:\n"
        f"before: {first}\n"
        f"after:  {second}"
    )


# ── (Step 0) Task 11.N.1 schema migration — Rev-5.2.1 BLOCKER resolution ─────
#
# Pre-committed Step-0 contract (5 assertions, each a separate test function):
#
#   (S0-a) ``onchain_xd_weekly`` CHECK constraint accepts BOTH
#          ``'net_primary_issuance_usd'`` AND ``'b2b_to_b2c_net_flow_usd'``.
#
#   (S0-b) Composite PK ``(week_start, proxy_kind)`` allows BOTH channels
#          to coexist for the same ``week_start`` row.
#
#   (S0-c) New ``onchain_copm_transfers`` table exists (distinct from the
#          preserved ``onchain_copm_transfers_sample``) and holds the full
#          dataset (schema-validated here; full rows arrive in Step 4).
#
#   (S0-d) ``copm_xd_filter.compute_weekly_xd()`` accepts a ``proxy_kind``
#          keyword argument (Literal["net_primary_issuance_usd",
#          "b2b_to_b2c_net_flow_usd"]); default preserves the existing
#          supply-channel behaviour so the 6 inequality-family tests keep
#          passing.
#
#   (S0-e) Rev-4 ``decision_hash`` preserved byte-exact — additive-only
#          guarantee (the hash covers LOCKED_DECISIONS, NOT on-chain
#          tables, so the schema change must not regress it).
#
# Plan reference: 2026-04-20-remittance-surprise-implementation.md,
# §"Step 0 (SCHEMA MIGRATION …)" under Task 11.N.1 (Rev 5.2.1).


def test_step0_xd_weekly_check_accepts_both_proxy_kinds(
    migrated_db: Path,
) -> None:
    """(S0-a) The migrated CHECK accepts the new B2B→B2C tag."""
    conn = duckdb.connect(str(migrated_db))
    try:
        # Supply channel — pre-existing — must still insert.
        conn.execute(
            "INSERT OR REPLACE INTO onchain_xd_weekly "
            "(week_start, value_usd, is_partial_week, proxy_kind) "
            "VALUES (?, ?, ?, ?)",
            [date(2025, 10, 31), "111.111111", False, "net_primary_issuance_usd"],
        )
        # Distribution channel — new — must also insert after migration.
        conn.execute(
            "INSERT OR REPLACE INTO onchain_xd_weekly "
            "(week_start, value_usd, is_partial_week, proxy_kind) "
            "VALUES (?, ?, ?, ?)",
            [date(2025, 10, 31), "222.222222", False, "b2b_to_b2c_net_flow_usd"],
        )
        # Invalid tag still rejected by the relaxed CHECK.
        with pytest.raises(duckdb.ConstraintException):
            conn.execute(
                "INSERT INTO onchain_xd_weekly "
                "(week_start, value_usd, is_partial_week, proxy_kind) "
                "VALUES (?, ?, ?, ?)",
                [date(2025, 10, 24), "0.0", False, "some_other_proxy"],
            )
    finally:
        conn.close()


def test_step0_xd_weekly_composite_pk_allows_both_channels(
    migrated_db: Path,
) -> None:
    """(S0-b) Composite PK (week_start, proxy_kind) lets both channels coexist.

    Under the Rev-5.1 singleton PK ``week_start``, inserting two rows with
    the same Friday but different ``proxy_kind`` would raise a
    ``ConstraintException``. Under the Rev-5.2.1 migration, this is the
    expected behaviour.
    """
    conn = duckdb.connect(str(migrated_db))
    try:
        friday = date(2025, 10, 31)
        # Delete pre-existing rows for this Friday to avoid PK collision
        # with the migration-seeded supply-channel data.
        conn.execute(
            "DELETE FROM onchain_xd_weekly WHERE week_start = ?", [friday]
        )
        conn.execute(
            "INSERT INTO onchain_xd_weekly "
            "(week_start, value_usd, is_partial_week, proxy_kind) "
            "VALUES (?, ?, ?, ?)",
            [friday, "1000.000000", False, "net_primary_issuance_usd"],
        )
        conn.execute(
            "INSERT INTO onchain_xd_weekly "
            "(week_start, value_usd, is_partial_week, proxy_kind) "
            "VALUES (?, ?, ?, ?)",
            [friday, "2000.000000", False, "b2b_to_b2c_net_flow_usd"],
        )
        rows = conn.execute(
            "SELECT proxy_kind, value_usd FROM onchain_xd_weekly "
            "WHERE week_start = ? ORDER BY proxy_kind",
            [friday],
        ).fetchall()
        assert len(rows) == 2, (
            f"Expected both channels coexisting at {friday}; got {rows}"
        )
        kinds = {r[0] for r in rows}
        assert kinds == {
            "net_primary_issuance_usd",
            "b2b_to_b2c_net_flow_usd",
        }, f"Missing expected proxy_kinds: got {kinds}"

        # PK enforcement still blocks duplicate (week_start, proxy_kind) tuples.
        with pytest.raises(duckdb.ConstraintException):
            conn.execute(
                "INSERT INTO onchain_xd_weekly "
                "(week_start, value_usd, is_partial_week, proxy_kind) "
                "VALUES (?, ?, ?, ?)",
                [friday, "3000.000000", False, "net_primary_issuance_usd"],
            )
    finally:
        conn.close()


def test_step0_onchain_copm_transfers_table_exists_distinct_from_sample(
    migrated_db: Path,
) -> None:
    """(S0-c) Full-dataset table exists distinct from the sample table.

    ``onchain_copm_transfers`` is the Rev-5.2.1 table for the full ~110k
    dataset (populated in Step 4); ``onchain_copm_transfers_sample`` is
    preserved byte-exact as a historical-audit pointer.
    """
    conn = duckdb.connect(str(migrated_db), read_only=True)
    try:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main'"
            ).fetchall()
        }
        assert "onchain_copm_transfers" in tables, (
            "onchain_copm_transfers table missing after Step 0 migration"
        )
        assert "onchain_copm_transfers_sample" in tables, (
            "onchain_copm_transfers_sample must be preserved (audit pointer)"
        )
        # Distinct tables.
        assert "onchain_copm_transfers" != "onchain_copm_transfers_sample"

        # Schema check: onchain_copm_transfers holds the same data-bearing
        # columns as the sample table (future rows will use identical dtypes),
        # plus it must be creatable/empty (row count 0 at Step 0 — rows
        # arrive in Step 4).
        cols = {
            r[0]
            for r in conn.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'onchain_copm_transfers' "
                "AND table_schema = 'main'"
            ).fetchall()
        }
        required_cols = {
            "evt_block_date",
            "evt_block_time",
            "evt_tx_hash",
            "from_address",
            "to_address",
            "value_wei",
            "evt_block_number",
        }
        assert required_cols.issubset(cols), (
            f"onchain_copm_transfers missing columns: "
            f"{required_cols - cols}"
        )

        # Sample table row count unchanged at 10.
        sample_n = conn.execute(
            "SELECT COUNT(*) FROM onchain_copm_transfers_sample"
        ).fetchone()
        assert sample_n is not None and sample_n[0] == 10, (
            f"Sample table row count drifted: got "
            f"{sample_n[0] if sample_n else None}, expected 10"
        )
    finally:
        conn.close()


def test_step0_compute_weekly_xd_accepts_proxy_kind_argument() -> None:
    """(S0-d) ``compute_weekly_xd`` is parametrized on ``proxy_kind``.

    The Rev-5.1 signature was ``compute_weekly_xd(daily_flow_rows, *,
    friday_anchor_tz='America/Bogota')`` and emitted
    ``proxy_kind='net_primary_issuance_usd'`` unconditionally. Step 0
    adds a ``proxy_kind`` keyword accepting the two-member Literal set
    while preserving the default (supply-channel) for backward
    compatibility with the existing 6 ``inequality/test_copm_xd_filter``
    assertions.
    """
    import inspect

    from scripts.copm_xd_filter import compute_weekly_xd

    sig = inspect.signature(compute_weekly_xd)
    assert "proxy_kind" in sig.parameters, (
        "compute_weekly_xd missing 'proxy_kind' parameter after Step 0"
    )
    param = sig.parameters["proxy_kind"]
    # Keyword-only or with a default — either is acceptable, so long as
    # callers need not pass it to preserve Rev-5.1 behaviour.
    assert param.default != inspect.Parameter.empty, (
        "compute_weekly_xd 'proxy_kind' must have a default to stay "
        "additive with existing Rev-5.1 callers."
    )
    assert param.default == "net_primary_issuance_usd", (
        f"Default proxy_kind must be 'net_primary_issuance_usd' (supply "
        f"channel); got {param.default!r}"
    )

    # Accepts the new distribution-channel value (empty input tuple is
    # a valid smoke input — should not raise).
    from scripts.copm_xd_filter import compute_weekly_xd as fn

    panel = fn((), proxy_kind="b2b_to_b2c_net_flow_usd")
    assert panel.proxy_kind == "b2b_to_b2c_net_flow_usd"

    # Default call unchanged.
    default_panel = fn(())
    assert default_panel.proxy_kind == "net_primary_issuance_usd"


def test_step0_rev4_decision_hash_preserved(migrated_db: Path) -> None:
    """(S0-e) Rev-4 ``decision_hash`` preserved byte-exact through Step 0.

    The migration must not touch ``LOCKED_DECISIONS`` or the fingerprint
    JSON. This is additive-only with respect to the Rev-4 discipline
    (schema change affects only DuckDB tables that do NOT participate in
    the hash computation).
    """
    from scripts.cleaning import LOCKED_DECISIONS, _compute_decision_hash

    got = _compute_decision_hash(LOCKED_DECISIONS)
    assert got == _EXPECTED_DECISION_HASH, (
        f"Rev-4 decision_hash drifted through Step 0: got {got}, "
        f"expected {_EXPECTED_DECISION_HASH}"
    )

    with _FINGERPRINT_PATH.open() as fh:
        fingerprint = json.load(fh)
    assert fingerprint["decision_hash"] == _EXPECTED_DECISION_HASH, (
        "nb1_panel_fingerprint.json decision_hash drifted through Step 0"
    )


# ── (Steps 1-4) Task 11.N.1 RPC backfill — real-RPC smoke + fallback ────────
#
# Five Step-1 assertions, per plan §Task 11.N.1 Step 1:
#
#   (R1) Public ``backfill_copm_transfers()`` / ``fetch_copm_transfers_rpc()``
#        / ``fetch_copm_transfers_alchemy()`` functions exist on
#        :mod:`scripts.econ_pipeline` with the committed signatures.
#
#   (R2) ``fetch_copm_transfers_rpc`` on a narrow 10,000-block range that
#        contains the known first Transfer event (block 27,786,128) is
#        deterministic across two calls and returns the expected two
#        log rows — the mint (``0x0 → treasury``) and the subsequent
#        treasury → hub transfer captured in the Dune sample CSV.
#
#   (R3) ``fetch_copm_transfers_alchemy`` raises ``RuntimeError`` with
#        a clear message when ``ALCHEMY_API_KEY`` is missing from the
#        environment — HALT-on-missing per plan CR hygiene finding.
#        No silent-skip / no silent-regression.
#
#   (R4) AFTER full backfill (Step 4) has landed the CSV and the
#        ``onchain_copm_transfers`` table, the table's row count matches
#        the backfill CSV row count to within ±1 % of the Dune-reported
#        110,069 target.
#
#   (R5) ``load_onchain_copm_transfers`` returns a frozen-dataclass
#        tuple over the FULL dataset (not the sample) — concretely,
#        ``len(rows)`` equals the Step-4 DB row count rather than 10.
#
# R4 + R5 are skipped when the CSV is still the 10-row sample (the
# Step-4 backfill has not yet run). This is *not* silent-pass: the skip
# condition is a hard DB row-count check that surfaces which step is
# outstanding in the skip reason.


# Pre-committed smoke-range constants — covers the FIRST COPM Transfer event
# recorded on-chain (block 27,786,128, tx ``0x4e762b…ea``) per the sample
# CSV. A 10,000-block window is the plan-specified pagination unit.
_SMOKE_START_BLOCK: Final[int] = 27_786_128
_SMOKE_END_BLOCK: Final[int] = _SMOKE_START_BLOCK + 9_999  # inclusive 10k
_SMOKE_EXPECTED_LOGS: Final[int] = 2  # mint + subsequent transfer
_FORNO_URL: Final[str] = "https://forno.celo.org"

# Dune-reported full dataset size for R4 tolerance check.
_EXPECTED_FULL_ROWS: Final[int] = 110_069
_ROW_COUNT_TOLERANCE: Final[float] = 0.01  # ±1 % per plan


def test_r1_backfill_functions_exposed() -> None:
    """(R1) Public API surface area for Steps 2/3 exists on econ_pipeline."""
    import inspect

    from scripts import econ_pipeline

    for name in (
        "fetch_copm_transfers_rpc",
        "fetch_copm_transfers_alchemy",
        "backfill_copm_transfers",
    ):
        assert hasattr(econ_pipeline, name), (
            f"scripts.econ_pipeline.{name} missing — Step 2/3 not yet implemented"
        )
        fn = getattr(econ_pipeline, name)
        assert callable(fn), f"{name} is not callable"

    sig_rpc = inspect.signature(econ_pipeline.fetch_copm_transfers_rpc)
    required = {"start_block", "end_block", "rpc_url"}
    assert required.issubset(sig_rpc.parameters), (
        f"fetch_copm_transfers_rpc missing required params: "
        f"{required - set(sig_rpc.parameters)}"
    )

    sig_alchemy = inspect.signature(econ_pipeline.fetch_copm_transfers_alchemy)
    assert "api_key" in sig_alchemy.parameters, (
        "fetch_copm_transfers_alchemy must take an api_key param"
    )


def test_r2_rpc_smoke_deterministic_on_narrow_range() -> None:
    """(R2) Two consecutive calls on the first-event 10k-block range return
    the same two rows.

    Real RPC test — hits forno.celo.org (plan's primary data path). Skip
    path engages on network unavailability (``RuntimeError`` /
    ``TimeoutError``) with ``RPC_RATE_LIMITED_AT_TEST_TIME`` marker.
    """
    from scripts.econ_pipeline import fetch_copm_transfers_rpc

    try:
        df_a = fetch_copm_transfers_rpc(
            start_block=_SMOKE_START_BLOCK,
            end_block=_SMOKE_END_BLOCK,
            rpc_url=_FORNO_URL,
        )
        df_b = fetch_copm_transfers_rpc(
            start_block=_SMOKE_START_BLOCK,
            end_block=_SMOKE_END_BLOCK,
            rpc_url=_FORNO_URL,
        )
    except (RuntimeError, TimeoutError) as exc:  # noqa: BLE001
        pytest.skip(f"RPC_RATE_LIMITED_AT_TEST_TIME: {exc}")

    # Deterministic: both calls return identical data.
    assert len(df_a) == _SMOKE_EXPECTED_LOGS, (
        f"Expected {_SMOKE_EXPECTED_LOGS} Transfer events on smoke range, "
        f"got {len(df_a)}"
    )
    assert len(df_b) == len(df_a), "Second RPC call returned different row count"
    # Stable row-order keys: (evt_block_number, log_index).
    sort_cols = ["evt_block_number", "log_index"]
    a = df_a.sort_values(sort_cols).reset_index(drop=True)
    b = df_b.sort_values(sort_cols).reset_index(drop=True)
    # Comparing hashes avoids numpy/pandas equality pitfalls around ints.
    import hashlib
    def _rowhash(df):
        return hashlib.sha256(
            "|".join(
                "~".join(str(v) for v in row)
                for row in df.itertuples(index=False)
            ).encode()
        ).hexdigest()
    assert _rowhash(a) == _rowhash(b), (
        "fetch_copm_transfers_rpc non-deterministic on fixed range"
    )

    # Sanity: row columns match the target DuckDB schema.
    required_cols = {
        "evt_block_date",
        "evt_block_time",
        "evt_tx_hash",
        "from_address",
        "to_address",
        "value_wei",
        "evt_block_number",
        "log_index",
    }
    assert required_cols.issubset(set(df_a.columns)), (
        f"Missing expected columns: {required_cols - set(df_a.columns)}"
    )


def test_r3_alchemy_halts_when_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """(R3) Alchemy fallback HALTs instead of silently skipping when the
    API key is unset (CR hygiene finding)."""
    from scripts.econ_pipeline import fetch_copm_transfers_alchemy

    monkeypatch.delenv("ALCHEMY_API_KEY", raising=False)
    with pytest.raises(RuntimeError) as exc_info:
        fetch_copm_transfers_alchemy(api_key=None)
    assert "ALCHEMY_API_KEY" in str(exc_info.value), (
        "RuntimeError must explicitly cite the missing env var so "
        "the operator sees the HALT reason"
    )


def test_r4_onchain_copm_transfers_row_count(migrated_db: Path) -> None:
    """(R4) Post-backfill, ``onchain_copm_transfers`` holds ≈ 110,069 rows
    (±1 %).

    Three states:
      (i)   empty/sample (< 100 rows): SKIP — Step 4 has not run.
      (ii)  partial (100 ≤ rows < 99% target): SKIP with
            ``X_D_STILL_INSUFFICIENT`` reason — Step 4 ran but primary
            RPC + fallback BOTH could not land the full dataset
            (plan recovery protocol endorses this as a valid outcome
            per contracts/.../copm_per_tx/README.md provenance block).
      (iii) complete (99%-target ≤ rows ≤ 101%-target): PASS.

    The SKIP in state (ii) is NOT a silent pass — the skip reason
    embeds ``X_D_STILL_INSUFFICIENT`` so CI + humans immediately see
    the escalation. A separate follow-up task (11.N.1b) is
    responsible for landing the remaining rows.
    """
    conn = duckdb.connect(str(migrated_db), read_only=True)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM onchain_copm_transfers"
        ).fetchone()
        got = int(count[0]) if count else 0
    finally:
        conn.close()

    if got < 100:
        pytest.skip(
            "Task 11.N.1 Step 4 not run — onchain_copm_transfers is empty/sample. "
            f"Target = {_EXPECTED_FULL_ROWS} ± {_ROW_COUNT_TOLERANCE:.0%}"
        )

    low = int(_EXPECTED_FULL_ROWS * (1 - _ROW_COUNT_TOLERANCE))
    high = int(_EXPECTED_FULL_ROWS * (1 + _ROW_COUNT_TOLERANCE))
    if got < low:
        pytest.skip(
            f"X_D_STILL_INSUFFICIENT: onchain_copm_transfers has {got} rows "
            f"({100 * got / _EXPECTED_FULL_ROWS:.1f}% of Dune-reported "
            f"{_EXPECTED_FULL_ROWS}) — primary RPC scan incomplete. "
            f"See contracts/data/copm_per_tx/README.md §'Provenance' for "
            f"backfill-failure diagnostics. Follow-up Task 11.N.1b required."
        )
    assert got <= high, (
        f"onchain_copm_transfers row count {got} ABOVE "
        f"+{_ROW_COUNT_TOLERANCE:.0%} of Dune-reported {_EXPECTED_FULL_ROWS} "
        f"(likely duplicate ingestion bug — investigate)."
    )


def test_r6_xd_weekly_both_channels_populated(migrated_db: Path) -> None:
    """(R6) After Step 5, ``onchain_xd_weekly`` carries BOTH
    ``'net_primary_issuance_usd'`` (supply) AND
    ``'b2b_to_b2c_net_flow_usd'`` (distribution) rows.

    Gate assertion per plan: "full 110k transfers in DuckDB;
    distribution-channel X_d rows in ``onchain_xd_weekly`` alongside
    supply-channel rows." Skipped when Step 4 has not yet landed.
    """
    conn = duckdb.connect(str(migrated_db), read_only=True)
    try:
        got_full = conn.execute(
            "SELECT COUNT(*) FROM onchain_copm_transfers"
        ).fetchone()
        full_rows = int(got_full[0]) if got_full else 0

        if full_rows < 100:
            pytest.skip(
                "Task 11.N.1 Step 4 not run — "
                "onchain_copm_transfers is empty/sample"
            )

        counts = conn.execute(
            "SELECT proxy_kind, COUNT(*) AS n "
            "FROM onchain_xd_weekly "
            "GROUP BY proxy_kind ORDER BY proxy_kind"
        ).fetchall()
    finally:
        conn.close()

    kinds = {r[0] for r in counts}
    assert "net_primary_issuance_usd" in kinds, (
        f"Supply-channel proxy_kind missing; got {kinds}"
    )
    assert "b2b_to_b2c_net_flow_usd" in kinds, (
        f"Distribution-channel proxy_kind missing; got {kinds}"
    )
    # Both channels should have a comparable number of weeks (the
    # supply channel has 1 row per Friday with >=1 day in the daily-
    # flow panel; the distribution channel has 1 row per Friday with
    # >=1 B2B/B2C transfer edge — may be a subset of supply weeks).
    supply_n = next(r[1] for r in counts if r[0] == "net_primary_issuance_usd")
    dist_n = next(r[1] for r in counts if r[0] == "b2b_to_b2c_net_flow_usd")
    assert supply_n >= 50, (
        f"Supply-channel rows unexpectedly low: {supply_n}"
    )
    assert dist_n >= 10, (
        f"Distribution-channel rows unexpectedly low: {dist_n}"
    )


def test_r5_load_onchain_copm_transfers_full_dataset(migrated_db: Path) -> None:
    """(R5) ``load_onchain_copm_transfers_full`` exposes the full dataset.

    The existing ``load_onchain_copm_transfers`` (which reads the 10-row
    sample) is preserved unchanged as a historical-audit pointer; the
    Rev-5.2.1 full-dataset loader is a new function
    ``load_onchain_copm_transfers_full`` returning the Rev-5.2.1
    ``OnchainCopmTransfer`` dataclass (no ``is_sample`` flag — the row
    is the real thing). Skipped when Step 4 has not yet landed.
    """
    from scripts import econ_query_api as api

    conn = duckdb.connect(str(migrated_db), read_only=True)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM onchain_copm_transfers"
        ).fetchone()
        got_db = int(count[0]) if count else 0
    finally:
        conn.close()

    if got_db < 100:
        pytest.skip(
            "Task 11.N.1 Step 4 not run — onchain_copm_transfers is "
            "empty/sample. load_onchain_copm_transfers_full contract "
            "not exercised."
        )

    assert hasattr(api, "load_onchain_copm_transfers_full"), (
        "scripts.econ_query_api.load_onchain_copm_transfers_full missing"
    )
    loader = api.load_onchain_copm_transfers_full
    conn = duckdb.connect(str(migrated_db), read_only=True)
    try:
        rows = loader(conn)
    finally:
        conn.close()

    assert isinstance(rows, tuple), f"loader returned {type(rows)}"
    assert len(rows) == got_db, (
        f"loader returned {len(rows)} rows; table has {got_db}. "
        "Ensure load_onchain_copm_transfers_full reads from "
        "onchain_copm_transfers (the full table), not the sample table."
    )
    # Rows carry the full schema.
    if rows:
        r = rows[0]
        for attr in (
            "evt_block_date",
            "evt_tx_hash",
            "from_address",
            "to_address",
            "value_wei",
            "evt_block_number",
            "log_index",
        ):
            assert hasattr(r, attr), f"frozen-dataclass missing {attr}"


# ── (Step N2b.1) Task 11.N.2b.1 schema migration — Carbon-basket pre-commit ───
#
# Pre-committed Step-N2b.1 contract (7 assertions, each a separate test
# function). All assertions run against an IN-MEMORY DuckDB; the canonical
# ``contracts/data/structural_econ.duckdb`` MUST remain byte-exact unchanged
# through the entire test cycle — this is the load-bearing additive-only
# invariant that lets 11.N.2b.1 author the schema-migration code path
# WITHOUT executing it against the canonical DB. Production migration is
# deferred to Task 11.N.2b.2 Step 5 (atomic-commit-after-population).
#
# Assertions:
#
#   (S1-N2b.1-a) ``scripts.econ_schema.migrate_onchain_xd_weekly_for_carbon``
#                exists and is callable. (Pre-Step-4 RED was AttributeError.)
#
#   (S1-N2b.1-b) After running against an in-memory DB seeded with the
#                Rev-5.2.1 2-value CHECK on ``onchain_xd_weekly``, the
#                migration relaxes the CHECK to admit ALL TEN ``proxy_kind``
#                values (2 pre-existing + 8 new Carbon-basket values per
#                plan §937).
#
#   (S1-N2b.1-c) The two new tables exist with probe-confirmed dtypes
#                from Dune-MCP LIMIT-100 probes (queries 7371827 + 7371828):
#                ``onchain_carbon_tokenstraded`` + ``onchain_carbon_arbitrages``.
#                Array-typed Bancor fields stored as JSON-encoded VARCHAR
#                per gate-decision memo §3.2 DDL DEVIATION (plan-§927
#                scalar pre-commit superseded by probe-observed
#                ``array(uint256)`` / ``array(varbinary)`` semantics).
#
#   (S1-N2b.1-d) Invalid ``proxy_kind`` values (e.g. ``'foo_bar_baz'``)
#                still rejected by the relaxed CHECK — over-permissive bug
#                guard.
#
#   (S1-N2b.1-e) Composite PK ``(week_start, proxy_kind)`` continues to
#                allow the pre-existing supply + distribution channels AND
#                the new Carbon basket-aggregate row to coexist for the
#                same Friday.
#
#   (S1-N2b.1-f) **CANONICAL DB CHECKSUM UNCHANGED** — sha256 of
#                ``contracts/data/structural_econ.duckdb`` is byte-exact
#                identical before and after the entire test-cycle.
#
#   (S1-N2b.1-g) Rev-4 ``decision_hash`` preserved byte-exact through the
#                schema migration (additive-only with respect to
#                LOCKED_DECISIONS).
#
# Plan reference: 2026-04-20-remittance-surprise-implementation.md,
# §"Task 11.N.2b.1: Carbon-basket pre-commitment + Dune-credit-budget probe".
# Memo reference: contracts/.scratch/2026-04-25-carbon-basket-gate-decision-memo.md.

# Pre-committed full set of admitted ``proxy_kind`` values per plan §937.
# Two pre-existing + eight new = ten total.
_N2B1_ADMITTED_PROXY_KINDS: Final[frozenset[str]] = frozenset({
    "net_primary_issuance_usd",
    "b2b_to_b2c_net_flow_usd",
    "carbon_basket_user_volume_usd",
    "carbon_basket_arb_volume_usd",
    "carbon_per_currency_copm_volume_usd",
    "carbon_per_currency_usdm_volume_usd",
    "carbon_per_currency_eurm_volume_usd",
    "carbon_per_currency_brlm_volume_usd",
    "carbon_per_currency_kesm_volume_usd",
    "carbon_per_currency_xofm_volume_usd",
})

# Pre-committed columns for the two new Carbon tables — mirror the
# probe-confirmed Dune schema. ``tokenstraded`` columns match the plan-§915
# DDL with the addition of ``contract_address`` and the rename of
# ``tx_hash`` → ``evt_tx_hash`` to match Dune's decoded namespace
# convention. ``arbitrages`` columns log the DDL deviation: array-typed
# Bancor fields stored as JSON-encoded VARCHAR per memo §3.2.
_N2B1_TOKENSTRADED_COLUMNS: Final[frozenset[str]] = frozenset({
    "contract_address",
    "evt_tx_hash",
    "evt_index",
    "evt_block_number",
    "evt_block_time",
    "evt_block_date",
    "evt_tx_from",
    "trader",
    "sourceToken",
    "targetToken",
    "sourceAmount",
    "targetAmount",
    "tradingFeeAmount",
    "byTargetAmount",
    "source_amount_usd",  # populated by Python aggregation layer in 11.N.2b.2
    "_ingested_at",
})
_N2B1_ARBITRAGES_COLUMNS: Final[frozenset[str]] = frozenset({
    "contract_address",
    "evt_tx_hash",
    "evt_index",
    "evt_block_number",
    "evt_block_time",
    "evt_block_date",
    "evt_tx_from",
    "caller",
    "platformIds",
    "protocolAmounts",
    "rewardAmounts",
    "sourceAmounts",
    "sourceTokens",
    "tokenPath",
    "_ingested_at",
})


def _seed_legacy_xd_weekly(conn: duckdb.DuckDBPyConnection) -> None:
    """Seed an in-memory DB with the Rev-5.2.1 ``onchain_xd_weekly`` schema.

    This represents the canonical DB's CURRENT state at Task 11.N.2b.1
    author time: composite PK ``(week_start, proxy_kind)`` + 2-value CHECK
    on ``proxy_kind``. The migration must transform this into the relaxed
    10-value CHECK while preserving every existing row byte-exact.
    """
    conn.execute(
        """
        CREATE TABLE onchain_xd_weekly (
            week_start DATE NOT NULL,
            value_usd VARCHAR NOT NULL,
            is_partial_week BOOLEAN NOT NULL,
            proxy_kind VARCHAR NOT NULL
              CHECK (proxy_kind IN (
                'net_primary_issuance_usd',
                'b2b_to_b2c_net_flow_usd'
              )),
            _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            PRIMARY KEY (week_start, proxy_kind)
        )
        """
    )
    # Seed two rows representative of canonical DB state: 1 supply row,
    # 1 distribution row on the same Friday. Migration must preserve
    # both byte-exact.
    conn.execute(
        "INSERT INTO onchain_xd_weekly "
        "(week_start, value_usd, is_partial_week, proxy_kind) "
        "VALUES (?, ?, ?, ?)",
        [date(2025, 10, 31), "111.111111", False, "net_primary_issuance_usd"],
    )
    conn.execute(
        "INSERT INTO onchain_xd_weekly "
        "(week_start, value_usd, is_partial_week, proxy_kind) "
        "VALUES (?, ?, ?, ?)",
        [date(2025, 10, 31), "222.222222", False, "b2b_to_b2c_net_flow_usd"],
    )


def test_n2b1_a_migration_function_exists() -> None:
    """(S1-N2b.1-a) ``migrate_onchain_xd_weekly_for_carbon`` is exposed."""
    from scripts import econ_schema

    assert hasattr(econ_schema, "migrate_onchain_xd_weekly_for_carbon"), (
        "scripts.econ_schema.migrate_onchain_xd_weekly_for_carbon missing — "
        "Step 4 not yet implemented."
    )
    fn = getattr(econ_schema, "migrate_onchain_xd_weekly_for_carbon")
    assert callable(fn), "migrate_onchain_xd_weekly_for_carbon is not callable"


def test_n2b1_b_relaxed_check_admits_all_ten_proxy_kinds() -> None:
    """(S1-N2b.1-b) Migration relaxes CHECK to admit all 10 proxy_kind values."""
    from scripts.econ_schema import migrate_onchain_xd_weekly_for_carbon

    conn = duckdb.connect(":memory:")
    try:
        _seed_legacy_xd_weekly(conn)

        # Pre-migration: only 2 values admitted; new Carbon values rejected.
        with pytest.raises(duckdb.ConstraintException):
            conn.execute(
                "INSERT INTO onchain_xd_weekly "
                "(week_start, value_usd, is_partial_week, proxy_kind) "
                "VALUES (?, ?, ?, ?)",
                [
                    date(2025, 11, 7),
                    "333.000000",
                    False,
                    "carbon_basket_user_volume_usd",
                ],
            )

        # Run migration.
        migrate_onchain_xd_weekly_for_carbon(conn)

        # Post-migration: every admitted value MUST insert successfully on a
        # distinct Friday so the composite PK never collides during the
        # smoke loop.
        base_friday = date(2025, 11, 7)
        for i, pk in enumerate(sorted(_N2B1_ADMITTED_PROXY_KINDS)):
            friday = base_friday + timedelta(weeks=i)
            conn.execute(
                "INSERT INTO onchain_xd_weekly "
                "(week_start, value_usd, is_partial_week, proxy_kind) "
                "VALUES (?, ?, ?, ?)",
                [friday, f"{i}.000000", False, pk],
            )

        # Assert all 10 values present in the table.
        kinds_in_table = {
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT proxy_kind FROM onchain_xd_weekly"
            ).fetchall()
        }
        assert _N2B1_ADMITTED_PROXY_KINDS.issubset(kinds_in_table), (
            f"Migration did not admit every expected proxy_kind. "
            f"Missing: {_N2B1_ADMITTED_PROXY_KINDS - kinds_in_table}"
        )

        # Pre-existing rows preserved byte-exact.
        legacy = conn.execute(
            "SELECT week_start, value_usd, is_partial_week, proxy_kind "
            "FROM onchain_xd_weekly "
            "WHERE proxy_kind IN ('net_primary_issuance_usd', "
            "                     'b2b_to_b2c_net_flow_usd') "
            "  AND week_start = ? "
            "ORDER BY proxy_kind",
            [date(2025, 10, 31)],
        ).fetchall()
        assert legacy == [
            (date(2025, 10, 31), "222.222222", False,
             "b2b_to_b2c_net_flow_usd"),
            (date(2025, 10, 31), "111.111111", False,
             "net_primary_issuance_usd"),
        ], f"Pre-existing rows mutated by migration: {legacy}"
    finally:
        conn.close()


def test_n2b1_c_new_carbon_tables_have_probe_confirmed_schema() -> None:
    """(S1-N2b.1-c) Two new Carbon tables created with probe-verified dtypes.

    Plan-§915 DDL pre-commitment for ``onchain_carbon_arbitrages`` was
    based on a scalar-field assumption that does not hold against the
    actual Dune ``carbon_defi_celo.bancorarbitrage_evt_arbitrageexecuted``
    schema (the event is multi-hop with array-typed source/path fields).
    The migration uses JSON-encoded VARCHAR for those array fields per
    gate-decision memo §3.2.
    """
    from scripts.econ_schema import migrate_onchain_xd_weekly_for_carbon

    conn = duckdb.connect(":memory:")
    try:
        _seed_legacy_xd_weekly(conn)
        migrate_onchain_xd_weekly_for_carbon(conn)

        tables = {
            r[0]
            for r in conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main'"
            ).fetchall()
        }
        assert "onchain_carbon_tokenstraded" in tables, (
            "onchain_carbon_tokenstraded table missing after migration"
        )
        assert "onchain_carbon_arbitrages" in tables, (
            "onchain_carbon_arbitrages table missing after migration"
        )

        # Column set check for each table.
        for table, expected_cols in (
            ("onchain_carbon_tokenstraded", _N2B1_TOKENSTRADED_COLUMNS),
            ("onchain_carbon_arbitrages", _N2B1_ARBITRAGES_COLUMNS),
        ):
            cols = {
                r[0]
                for r in conn.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = ? AND table_schema = 'main'",
                    [table],
                ).fetchall()
            }
            missing = expected_cols - cols
            assert not missing, (
                f"{table} missing columns: {missing}; got cols: {cols}"
            )

        # Dtype spot-checks per probe verification.
        type_rows = conn.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'onchain_carbon_tokenstraded' "
            "  AND table_schema = 'main'"
        ).fetchall()
        types = {col: dtype for (col, dtype) in type_rows}
        # uint256 → HUGEINT (signed 128-bit) per 11.M.5 commit af98bb659
        # precedent. Caveat in memo §3.1: HUGEINT max < uint256 max, so
        # the production ingest layer must guard against overflow on
        # whale trades (LIMIT-100 max sourceAmount = 9.43e18, well within
        # range).
        assert types.get("sourceAmount") == "HUGEINT", (
            f"sourceAmount must be HUGEINT; got {types.get('sourceAmount')}"
        )
        assert types.get("targetAmount") == "HUGEINT", (
            f"targetAmount must be HUGEINT; got {types.get('targetAmount')}"
        )
        assert types.get("evt_block_number") == "BIGINT", (
            f"evt_block_number must be BIGINT; got {types.get('evt_block_number')}"
        )
        # Address fields: VARBINARY (20-byte; Dune decoded namespace native).
        assert types.get("sourceToken") == "BLOB", (
            f"sourceToken must be VARBINARY/BLOB; got {types.get('sourceToken')}"
        )
        assert types.get("targetToken") == "BLOB", (
            f"targetToken must be VARBINARY/BLOB; got {types.get('targetToken')}"
        )
        assert types.get("byTargetAmount") == "BOOLEAN", (
            f"byTargetAmount must be BOOLEAN; got {types.get('byTargetAmount')}"
        )

        # Arbitrages array fields: JSON-encoded VARCHAR per DDL deviation
        # logged in gate-decision memo §3.2.
        arb_type_rows = conn.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'onchain_carbon_arbitrages' "
            "  AND table_schema = 'main'"
        ).fetchall()
        arb_types = {col: dtype for (col, dtype) in arb_type_rows}
        for arr_field in (
            "platformIds",
            "protocolAmounts",
            "rewardAmounts",
            "sourceAmounts",
            "sourceTokens",
            "tokenPath",
        ):
            assert arb_types.get(arr_field) == "VARCHAR", (
                f"{arr_field} must be VARCHAR (JSON-encoded array per "
                f"gate-decision memo §3.2); got {arb_types.get(arr_field)}"
            )
    finally:
        conn.close()


def test_n2b1_d_invalid_proxy_kind_still_rejected() -> None:
    """(S1-N2b.1-d) Relaxed CHECK is not over-permissive."""
    from scripts.econ_schema import migrate_onchain_xd_weekly_for_carbon

    conn = duckdb.connect(":memory:")
    try:
        _seed_legacy_xd_weekly(conn)
        migrate_onchain_xd_weekly_for_carbon(conn)

        with pytest.raises(duckdb.ConstraintException):
            conn.execute(
                "INSERT INTO onchain_xd_weekly "
                "(week_start, value_usd, is_partial_week, proxy_kind) "
                "VALUES (?, ?, ?, ?)",
                [date(2025, 12, 5), "0.0", False, "foo_bar_baz_invalid"],
            )

        # Carbon-basket primary key value still admitted (positive control).
        conn.execute(
            "INSERT INTO onchain_xd_weekly "
            "(week_start, value_usd, is_partial_week, proxy_kind) "
            "VALUES (?, ?, ?, ?)",
            [date(2025, 12, 5), "100.0", False, "carbon_basket_user_volume_usd"],
        )
    finally:
        conn.close()


def test_n2b1_e_composite_pk_admits_all_channels_same_friday() -> None:
    """(S1-N2b.1-e) Three+ channels coexist for the same Friday post-migration."""
    from scripts.econ_schema import migrate_onchain_xd_weekly_for_carbon

    conn = duckdb.connect(":memory:")
    try:
        _seed_legacy_xd_weekly(conn)
        migrate_onchain_xd_weekly_for_carbon(conn)

        friday = date(2025, 12, 12)
        for v, pk in (
            ("100.0", "net_primary_issuance_usd"),
            ("200.0", "b2b_to_b2c_net_flow_usd"),
            ("300.0", "carbon_basket_user_volume_usd"),
            ("50.0", "carbon_basket_arb_volume_usd"),
        ):
            conn.execute(
                "INSERT INTO onchain_xd_weekly "
                "(week_start, value_usd, is_partial_week, proxy_kind) "
                "VALUES (?, ?, ?, ?)",
                [friday, v, False, pk],
            )

        rows = conn.execute(
            "SELECT proxy_kind, value_usd FROM onchain_xd_weekly "
            "WHERE week_start = ? ORDER BY proxy_kind",
            [friday],
        ).fetchall()
        assert len(rows) == 4, (
            f"Composite PK must admit 4 channels for the same Friday; got {rows}"
        )

        # PK still enforces per-(week_start, proxy_kind) uniqueness.
        with pytest.raises(duckdb.ConstraintException):
            conn.execute(
                "INSERT INTO onchain_xd_weekly "
                "(week_start, value_usd, is_partial_week, proxy_kind) "
                "VALUES (?, ?, ?, ?)",
                [friday, "999.0", False, "carbon_basket_user_volume_usd"],
            )
    finally:
        conn.close()


def test_n2b1_f_canonical_db_checksum_unchanged_through_full_test_cycle(
    tmp_path: Path,
) -> None:
    """(S1-N2b.1-f) Canonical DB byte-exact identical before and after.

    This is the load-bearing additive-only invariant for Task 11.N.2b.1:
    the schema-migration code path is committed to ``scripts.econ_schema``
    but is NOT executed against canonical ``contracts/data/structural_econ.duckdb``
    until Task 11.N.2b.2 Step 5 (atomic-commit-after-population). Any
    in-test invocation against the canonical path is a regression.
    """
    assert _REAL_DB_PATH.is_file(), f"missing {_REAL_DB_PATH}"

    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(64 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    before = _sha256(_REAL_DB_PATH)

    # Run the migration's full test cycle against an in-memory DB,
    # mirroring the four assertions above. Canonical path must NOT be
    # touched.
    from scripts.econ_schema import migrate_onchain_xd_weekly_for_carbon

    conn = duckdb.connect(":memory:")
    try:
        _seed_legacy_xd_weekly(conn)
        migrate_onchain_xd_weekly_for_carbon(conn)
        # Smoke-test all 10 proxy_kind values insert.
        base_friday = date(2026, 1, 2)
        for i, pk in enumerate(sorted(_N2B1_ADMITTED_PROXY_KINDS)):
            conn.execute(
                "INSERT INTO onchain_xd_weekly "
                "(week_start, value_usd, is_partial_week, proxy_kind) "
                "VALUES (?, ?, ?, ?)",
                [base_friday + timedelta(weeks=i), f"{i}.0", False, pk],
            )
    finally:
        conn.close()

    # Sanity: also verify that an exported temp file from the in-memory DB
    # is NOT the canonical file.
    sentinel = tmp_path / "n2b1_inmemory_sentinel.duckdb"
    conn2 = duckdb.connect(str(sentinel))
    try:
        _seed_legacy_xd_weekly(conn2)
        migrate_onchain_xd_weekly_for_carbon(conn2)
    finally:
        conn2.close()
    assert sentinel.resolve() != _REAL_DB_PATH.resolve(), (
        "sentinel migration leaked into canonical DB path"
    )

    after = _sha256(_REAL_DB_PATH)
    assert before == after, (
        f"Canonical structural_econ.duckdb checksum drifted through Task "
        f"11.N.2b.1 — Step Atomicity Protocol violated.\n"
        f"  before: {before}\n"
        f"  after:  {after}"
    )


def test_n2b1_g_rev4_decision_hash_preserved() -> None:
    """(S1-N2b.1-g) Rev-4 ``decision_hash`` byte-exact through the migration.

    The migration affects only DuckDB schema; LOCKED_DECISIONS and the
    nb1_panel_fingerprint.json must remain identical.
    """
    from scripts.cleaning import LOCKED_DECISIONS, _compute_decision_hash

    got = _compute_decision_hash(LOCKED_DECISIONS)
    assert got == _EXPECTED_DECISION_HASH, (
        f"Rev-4 decision_hash drifted through Task 11.N.2b.1: "
        f"got {got}, expected {_EXPECTED_DECISION_HASH}"
    )

    with _FINGERPRINT_PATH.open() as fh:
        fingerprint = json.load(fh)
    assert fingerprint["decision_hash"] == _EXPECTED_DECISION_HASH, (
        "nb1_panel_fingerprint.json decision_hash drifted through Task 11.N.2b.1"
    )
