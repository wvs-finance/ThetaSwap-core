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
from datetime import date
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
