"""Pipeline orchestrator for structural econometrics data.

Coordinates download -> insert -> panel build -> validate.
"""
from __future__ import annotations

import csv as _csv
import hashlib
from dataclasses import dataclass
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from typing import Final

import duckdb
import requests


# ── FRED DFF (Federal Funds Effective Rate) ingestion ────────────────────────
#
# Task 11.M.6 (RC plan-review BLOCKER): Y_asset_leg ≡
#   (Banrep_rate - Fed_funds)/52 + ΔTRM/TRM
# requires DFF alongside the Banrep IBR level. The public FRED CSV
# endpoint does NOT require an API key, so ingestion is key-free — the
# existing ``econ_fred.fetch_fred_series`` JSON path is API-key-bound
# and reserved for series that need the richer metadata.

_FRED_DFF_CSV_URL: Final[str] = (
    "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF&cosd={start}"
)


@dataclass(frozen=True, slots=True)
class DffObservation:
    """One FRED DFF (Federal Funds Effective Rate) observation."""

    date: date
    value: float | None


def parse_fred_dff_csv(csv_text: str) -> list[DffObservation]:
    """Parse FRED's public CSV response for the DFF series.

    Pure — takes raw CSV text, returns parsed rows. Missing values are
    encoded as ``.`` in FRED's CSV output and mapped to ``None`` here.
    """
    reader = _csv.reader(StringIO(csv_text))
    header = next(reader, None)
    if header is None:
        return []
    rows: list[DffObservation] = []
    for row in reader:
        if len(row) < 2:
            continue
        raw_date, raw_value = row[0].strip(), row[1].strip()
        try:
            parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            continue
        value = None if raw_value in (".", "") else float(raw_value)
        rows.append(DffObservation(date=parsed_date, value=value))
    return rows


def fetch_fred_dff(start: str = "2008-01-01") -> list[DffObservation]:
    """Fetch the DFF (Federal Funds Effective Rate) daily series from FRED.

    Uses the public fredgraph.csv endpoint — no API key required.
    """
    url = _FRED_DFF_CSV_URL.format(start=start)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return parse_fred_dff_csv(resp.text)


def upsert_fred_dff(
    conn: duckdb.DuckDBPyConnection,
    observations: list[DffObservation],
) -> int:
    """Idempotent upsert of DFF observations into ``fred_daily``.

    Returns the number of rows written (matches ``len(observations)`` —
    ``INSERT OR REPLACE`` guarantees a one-to-one row count).
    """
    n = 0
    for obs in observations:
        conn.execute(
            "INSERT OR REPLACE INTO fred_daily (series_id, date, value) "
            "VALUES ('DFF', ?, ?)",
            [obs.date, obs.value],
        )
        n += 1
    return n


def migrate_fred_daily_allow_dff(conn: duckdb.DuckDBPyConnection) -> bool:
    """Rebuild ``fred_daily`` with the extended CHECK constraint (+DFF).

    DuckDB cannot drop a column-level CHECK in place, so an in-place
    migration requires a shadow-table rebuild:

      1. Create ``fred_daily_new`` with the new CHECK.
      2. Copy every row from the current ``fred_daily``.
      3. Drop the old table, rename the shadow.

    Returns ``True`` if a migration was performed, ``False`` if the
    table already permits DFF (call is a no-op). Byte-exact preserving
    — no column, value, or row count changes for pre-existing series.
    """
    existing = conn.execute(
        "SELECT constraint_text FROM duckdb_constraints() "
        "WHERE table_name = 'fred_daily' AND constraint_type = 'CHECK'"
    ).fetchall()
    for row in existing:
        clause = (row[0] or "")
        if "'DFF'" in clause:
            return False  # already migrated

    conn.execute("""
    CREATE TABLE fred_daily_new (
        series_id VARCHAR NOT NULL
          CHECK (series_id IN ('VIXCLS', 'DCOILWTICO', 'DCOILBRENTEU', 'DFF')),
        date DATE NOT NULL,
        value DOUBLE,
        PRIMARY KEY (series_id, date)
    )
    """)
    conn.execute(
        "INSERT INTO fred_daily_new (series_id, date, value) "
        "SELECT series_id, date, value FROM fred_daily"
    )
    conn.execute("DROP TABLE fred_daily")
    conn.execute("ALTER TABLE fred_daily_new RENAME TO fred_daily")
    return True


# ── Manifest logging ─────────────────────────────────────────────────────────


def log_manifest(
    conn: duckdb.DuckDBPyConnection,
    *,
    source: str,
    status: str,
    row_count: int | None = None,
    date_min: date | None = None,
    date_max: date | None = None,
    sha256: str | None = None,
    url_or_path: str | None = None,
    notes: str | None = None,
) -> None:
    """Append a row to download_manifest. INSERT-only (never replaces)."""
    conn.execute(
        "INSERT INTO download_manifest "
        "(source, downloaded_at, row_count, date_min, date_max, sha256, url_or_path, status, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [source, datetime.now(), row_count, date_min, date_max, sha256, url_or_path, status, notes],
    )


def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hex digest of raw response bytes."""
    return hashlib.sha256(data).hexdigest()


# ── Validation ───────────────────────────────────────────────────────────────


class ValidationError(Exception):
    """Raised when a derived panel fails validation checks."""


def validate_weekly_panel(conn: duckdb.DuckDBPyConnection) -> None:
    """Validate weekly_panel constraints from spec section 5 step 6."""
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    if "weekly_panel" not in tables:
        raise ValidationError("weekly_panel table does not exist")

    count = conn.execute("SELECT COUNT(*) FROM weekly_panel").fetchone()
    if count is None or count[0] == 0:
        raise ValidationError("weekly_panel is empty")

    # No duplicate week_starts
    dupes = conn.execute(
        "SELECT week_start, COUNT(*) AS c FROM weekly_panel GROUP BY week_start HAVING c > 1"
    ).fetchall()
    if dupes:
        raise ValidationError(f"Duplicate week_starts: {dupes}")

    # RV > 0 (allow rv_log NULL for zero-RV weeks from degenerate data)
    bad_rv = conn.execute("SELECT COUNT(*) FROM weekly_panel WHERE rv < 0").fetchone()
    if bad_rv and bad_rv[0] > 0:
        raise ValidationError(f"{bad_rv[0]} rows with rv < 0")

    # n_trading_days in [1, 5]
    bad_n = conn.execute(
        "SELECT COUNT(*) FROM weekly_panel WHERE n_trading_days < 1 OR n_trading_days > 5"
    ).fetchone()
    if bad_n and bad_n[0] > 0:
        raise ValidationError(f"{bad_n[0]} rows with n_trading_days outside [1, 5]")

    # No NULLs in surprise/release columns (should be 0.0)
    null_check = conn.execute(
        "SELECT COUNT(*) FROM weekly_panel WHERE "
        "cpi_surprise_ar1 IS NULL OR us_cpi_surprise IS NULL OR "
        "dane_ipc_pct IS NULL OR dane_ipp_pct IS NULL"
    ).fetchone()
    if null_check and null_check[0] > 0:
        raise ValidationError(f"{null_check[0]} rows with NULL in surprise columns (should be 0.0)")

    # intervention_dummy in {0, 1}
    bad_iv = conn.execute(
        "SELECT COUNT(*) FROM weekly_panel WHERE intervention_dummy NOT IN (0, 1)"
    ).fetchone()
    if bad_iv and bad_iv[0] > 0:
        raise ValidationError(f"{bad_iv[0]} rows with intervention_dummy not in {{0, 1}}")


def validate_daily_panel(conn: duckdb.DuckDBPyConnection) -> None:
    """Validate daily_panel constraints from spec section 5 step 6."""
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    if "daily_panel" not in tables:
        raise ValidationError("daily_panel table does not exist")

    count = conn.execute("SELECT COUNT(*) FROM daily_panel").fetchone()
    if count is None or count[0] == 0:
        raise ValidationError("daily_panel is empty")

    # No duplicate dates
    dupes = conn.execute(
        "SELECT date, COUNT(*) AS c FROM daily_panel GROUP BY date HAVING c > 1"
    ).fetchall()
    if dupes:
        raise ValidationError(f"Duplicate dates in daily_panel: {dupes[:5]}")

    # intervention_dummy in {0, 1}
    bad_iv = conn.execute(
        "SELECT COUNT(*) FROM daily_panel WHERE intervention_dummy NOT IN (0, 1)"
    ).fetchone()
    if bad_iv and bad_iv[0] > 0:
        raise ValidationError(f"{bad_iv[0]} rows with intervention_dummy not in {{0, 1}}")


# ── Task 11.M.5: on-chain COPM / cCOP ingestion ─────────────────────────────
#
# Reads the 8 Dune profile CSVs under ``contracts/data/copm_per_tx/`` plus the
# Task 11.A 585-day ``contracts/data/copm_ccop_daily_flow.csv`` into the
# structural-econ DuckDB. Every ingest is idempotent via ``INSERT OR REPLACE``
# (matches the ``upsert_fred_dff`` precedent) so a second run leaves byte-
# exact state. Ingestion is strictly additive — no pre-existing table is
# touched, and on-chain rows never join any existing Rev-4 table.
#
# Per ``feedback_strict_tdd.md`` + ``feedback_scripts_only_scope.md``, this
# module touches only ``contracts/scripts/`` + ``contracts/data/`` (the
# DuckDB binary at ``contracts/data/structural_econ.duckdb``).

_DEFAULT_DATA_ROOT: Final[Path] = (
    Path(__file__).resolve().parents[1] / "data"
)


def _read_csv_rows(
    csv_path: Path, *, skip_comments: bool = True
) -> list[dict[str, str]]:
    """Read a CSV file into a list of field-dicts.

    ``skip_comments=True`` drops any line whose first non-whitespace
    character is ``#`` — the copm CSVs place such lines between the
    header and the data rows (notably ``copm_transfers.csv`` and
    ``copm_ccop_daily_flow.csv``). The first non-comment line is then
    treated as the header.
    """
    with csv_path.open() as fh:
        lines = [ln for ln in fh.read().splitlines() if ln]
    if skip_comments:
        lines = [ln for ln in lines if not ln.lstrip().startswith("#")]
    reader = _csv.DictReader(lines)
    return list(reader)


def _parse_hugeint(raw: str) -> int | None:
    """Parse a wei-amount string into an int (or None if empty)."""
    raw = (raw or "").strip()
    if raw == "":
        return None
    return int(raw)


def _parse_bool(raw: str) -> bool:
    """Parse a boolean-like string (``true``/``false``)."""
    raw = (raw or "").strip().lower()
    if raw in ("true", "t", "1"):
        return True
    if raw in ("false", "f", "0"):
        return False
    raise ValueError(f"cannot parse {raw!r} as bool")


def _preserve_timestamp_text(raw: str) -> str:
    """Return the CSV timestamp text verbatim (no parsing, no reformatting).

    The CSV ship Dune's ``YYYY-MM-DD HH:MM:SS.sss UTC`` timestamp format.
    Parsing+reformatting through ``datetime`` drops the trailing
    ``.000 UTC`` suffix, breaking byte-exact CSV→DB round-trip. Timestamp
    columns are stored as ``VARCHAR`` and the text is passed through
    untouched; downstream loaders (:mod:`scripts.econ_query_api`) CAST
    the stored text back into ``datetime`` when typed values are needed.
    """
    return raw.strip() if raw is not None else ""


def _parse_date(raw: str) -> date:
    """Parse a YYYY-MM-DD date string."""
    return datetime.strptime(raw.strip(), "%Y-%m-%d").date()


def _parse_address(raw: str) -> str | None:
    """Return the address lowercased, or None if empty.

    Dune returns all addresses lowercased, so ``lower()`` is a no-op in
    practice — we apply it defensively to make the CSV-side vs. DB-side
    checksum invariant to any future case drift in upstream exports.
    """
    raw = (raw or "").strip()
    if raw == "":
        return None
    return raw.lower()


# ── Per-CSV ingestion functions ─────────────────────────────────────────────


def ingest_onchain_copm_mints(
    conn: duckdb.DuckDBPyConnection, csv_path: Path
) -> int:
    """Ingest ``copm_mints.csv`` (146 rows). Returns row-count written."""
    rows = _read_csv_rows(csv_path)
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO onchain_copm_mints "
            "(call_block_date, call_block_time, tx_hash, tx_from, to_address, "
            " amount_wei, call_success, call_block_number) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                _parse_date(r["call_block_date"]),
                _preserve_timestamp_text(r["call_block_time"]),
                r["call_tx_hash"].strip().lower(),
                _parse_address(r["call_tx_from"]),
                _parse_address(r["to_address"]),
                _parse_hugeint(r["amount_wei"]),
                _parse_bool(r["call_success"]),
                int(r["call_block_number"]),
            ],
        )
    return len(rows)


def ingest_onchain_copm_burns(
    conn: duckdb.DuckDBPyConnection, csv_path: Path
) -> int:
    """Ingest ``copm_burns.csv`` (121 rows, union of burn + burnFrozen).

    A ``_csv_row_idx`` column preserves CSV-native row order — the CSV
    has multiple rows sharing the same ``call_block_number`` where
    ``ORDER BY tx_hash`` does not reproduce the Dune-native ordering.
    """
    rows = _read_csv_rows(csv_path)
    for idx, r in enumerate(rows):
        # Plain INSERT (not REPLACE): run_onchain_migration wipes the
        # table before calling this function, and the two UNIQUE
        # constraints (PK + _csv_row_idx) preclude a multi-target
        # upsert clause in DuckDB.
        conn.execute(
            "INSERT INTO onchain_copm_burns "
            "(call_block_date, call_block_time, tx_hash, tx_from, account, "
            " amount_wei, call_success, call_block_number, burn_kind, "
            " _csv_row_idx) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                _parse_date(r["call_block_date"]),
                _preserve_timestamp_text(r["call_block_time"]),
                r["call_tx_hash"].strip().lower(),
                _parse_address(r["call_tx_from"]),
                _parse_address(r["account"]),
                _parse_hugeint(r["amount_wei"]),
                _parse_bool(r["call_success"]),
                int(r["call_block_number"]),
                r["burn_kind"].strip(),
                idx,
            ],
        )
    return len(rows)


def ingest_onchain_copm_transfers_sample(
    conn: duckdb.DuckDBPyConnection, csv_path: Path
) -> int:
    """Ingest the 10-row SAMPLE of ``copm_transfers.csv``.

    The full 110,069-row raw dataset is retrievable from Dune query
    7369028 via the Dune web UI (Dune MCP pagination blocks full-data
    retrieval in a single agent session).

    A ``_csv_row_idx`` column preserves CSV-native row order — multiple
    transfer events often share the same ``evt_tx_hash`` (e.g. a mint
    that emits both a ``0x0 -> account`` event and an
    ``account -> operator`` event), and the chronological ``from/to``
    ordering in the CSV is not reproducible from ``ORDER BY
    from_address`` alone.
    """
    rows = _read_csv_rows(csv_path)
    for idx, r in enumerate(rows):
        # Plain INSERT (not REPLACE): run_onchain_migration wipes the
        # table before calling this function, and the two UNIQUE
        # constraints (PK + _csv_row_idx) preclude a multi-target
        # upsert clause in DuckDB.
        conn.execute(
            "INSERT INTO onchain_copm_transfers_sample "
            "(evt_block_date, evt_block_time, evt_tx_hash, from_address, "
            " to_address, value_wei, evt_block_number, _csv_row_idx) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                _parse_date(r["evt_block_date"]),
                _preserve_timestamp_text(r["evt_block_time"]),
                r["evt_tx_hash"].strip().lower(),
                _parse_address(r["from_address"]),
                _parse_address(r["to_address"]),
                _parse_hugeint(r["value_wei"]),
                int(r["evt_block_number"]),
                idx,
            ],
        )
    return len(rows)


def ingest_onchain_copm_freeze_thaw(
    conn: duckdb.DuckDBPyConnection, csv_path: Path
) -> int:
    """Ingest ``copm_freeze_thaw.csv`` (4 rows)."""
    rows = _read_csv_rows(csv_path)
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO onchain_copm_freeze_thaw "
            "(evt_block_date, evt_block_time, evt_tx_hash, account, "
            " amount_wei, event_type, evt_block_number) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                _parse_date(r["evt_block_date"]),
                _preserve_timestamp_text(r["evt_block_time"]),
                r["evt_tx_hash"].strip().lower(),
                _parse_address(r["account"]),
                _parse_hugeint(r["amount_wei"]),
                r["event_type"].strip(),
                int(r["evt_block_number"]),
            ],
        )
    return len(rows)


def ingest_onchain_copm_top100_edges(
    conn: duckdb.DuckDBPyConnection, csv_path: Path
) -> int:
    """Ingest ``copm_transfers_top100_edges.csv`` (100 rows).

    A ``_csv_row_idx`` column (0-based enumeration of CSV data rows)
    preserves the Dune-native row order so the test's byte-exact
    checksum can reproduce it deterministically. See
    :mod:`scripts.econ_schema` for why this is required.
    """
    rows = _read_csv_rows(csv_path)
    for idx, r in enumerate(rows):
        # Plain INSERT (not REPLACE): run_onchain_migration wipes the
        # table before calling this function, and the two UNIQUE
        # constraints (PK + _csv_row_idx) preclude a multi-target
        # upsert clause in DuckDB.
        conn.execute(
            "INSERT INTO onchain_copm_transfers_top100_edges "
            "(from_address, to_address, n_transfers, total_value_wei, "
            " first_time, last_time, _csv_row_idx) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                _parse_address(r["from_address"]),
                _parse_address(r["to_address"]),
                int(r["n_transfers"]),
                _parse_hugeint(r["total_value_wei"]),
                _preserve_timestamp_text(r["first_time"]),
                _preserve_timestamp_text(r["last_time"]),
                idx,
            ],
        )
    return len(rows)


def ingest_onchain_copm_daily_transfers(
    conn: duckdb.DuckDBPyConnection, csv_path: Path
) -> int:
    """Ingest ``copm_daily_transfers.csv`` (522 daily aggregates)."""
    rows = _read_csv_rows(csv_path)
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO onchain_copm_daily_transfers "
            "(evt_block_date, n_transfers, n_tx, n_distinct_from, "
            " n_distinct_to, total_value_wei) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                _parse_date(r["evt_block_date"]),
                int(r["n_transfers"]),
                int(r["n_tx"]),
                int(r["n_distinct_from"]),
                int(r["n_distinct_to"]),
                _parse_hugeint(r["total_value_wei"]),
            ],
        )
    return len(rows)


def ingest_onchain_copm_address_activity(
    conn: duckdb.DuckDBPyConnection, csv_path: Path
) -> int:
    """Ingest ``copm_address_activity_top400.csv`` (300 rows).

    Note: the file is named ``top400`` but the actual row count is 300 —
    the source Dune query truncates at the top-N with activity ≥ threshold.

    A ``_csv_row_idx`` column (0-based enumeration of CSV data rows)
    preserves the Dune-native row order so the test's byte-exact
    checksum can reproduce it deterministically — the Dune CSV has
    tie-breaks on ``(n_inbound + n_outbound)`` that are not a monotone
    function of any single column. See :mod:`scripts.econ_schema`.
    """
    rows = _read_csv_rows(csv_path)
    for idx, r in enumerate(rows):
        # Plain INSERT (not REPLACE): run_onchain_migration wipes the
        # table before calling this function, and the two UNIQUE
        # constraints (PK + _csv_row_idx) preclude a multi-target
        # upsert clause in DuckDB.
        conn.execute(
            "INSERT INTO onchain_copm_address_activity_top400 "
            "(address, n_inbound, inbound_wei, n_outbound, outbound_wei, "
            " _csv_row_idx) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                _parse_address(r["address"]),
                int(r["n_inbound"]),
                _parse_hugeint(r["inbound_wei"]),
                int(r["n_outbound"]),
                _parse_hugeint(r["outbound_wei"]),
                idx,
            ],
        )
    return len(rows)


def ingest_onchain_copm_time_patterns(
    conn: duckdb.DuckDBPyConnection, csv_path: Path
) -> int:
    """Ingest ``copm_time_patterns.csv`` (86 rows: dom + dow + month).

    ``bucket`` is stored as its CSV text (VARCHAR) so lexical ordering
    (``1, 10, 11, ..., 2, 20, ...``) matches the source CSV. See
    :mod:`scripts.econ_schema` for rationale.
    """
    rows = _read_csv_rows(csv_path)
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO onchain_copm_time_patterns "
            "(kind, bucket, n, wei) VALUES (?, ?, ?, ?)",
            [
                r["kind"].strip(),
                r["bucket"].strip(),
                int(r["n"]),
                _parse_hugeint(r["wei"]),
            ],
        )
    return len(rows)


def ingest_onchain_ccop_daily_flow(
    conn: duckdb.DuckDBPyConnection, csv_path: Path
) -> int:
    """Ingest ``copm_ccop_daily_flow.csv`` (Task 11.A, 585 daily rows).

    USD columns are stored as VARCHAR to preserve the exact 6-decimal
    CSV text (``237.797991``, ``0.000000``). DuckDB ``DOUBLE`` trims
    trailing-zero decimals (``0.000000`` → ``0.0``) which would break
    the byte-exact CSV-vs-DB checksum. See :mod:`scripts.econ_schema`.
    """
    rows = _read_csv_rows(csv_path)
    for r in rows:
        raw_inflow = (r.get("ccop_usdt_inflow_usd") or "").strip()
        raw_outflow = (r.get("ccop_usdt_outflow_usd") or "").strip()
        raw_senders = (r.get("ccop_unique_senders") or "").strip()
        conn.execute(
            "INSERT OR REPLACE INTO onchain_copm_ccop_daily_flow "
            "(date, copm_mint_usd, copm_burn_usd, copm_unique_minters, "
            " ccop_usdt_inflow_usd, ccop_usdt_outflow_usd, "
            " ccop_unique_senders, source_query_ids) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                _parse_date(r["date"]),
                r["copm_mint_usd"].strip(),
                r["copm_burn_usd"].strip(),
                int(r["copm_unique_minters"]),
                raw_inflow if raw_inflow != "" else None,
                raw_outflow if raw_outflow != "" else None,
                int(raw_senders) if raw_senders != "" else None,
                (r.get("source_query_ids") or "").strip() or None,
            ],
        )
    return len(rows)


# ── Orchestrator ────────────────────────────────────────────────────────────


_ONCHAIN_TABLES: Final[tuple[str, ...]] = (
    "onchain_copm_mints",
    "onchain_copm_burns",
    "onchain_copm_transfers_sample",
    "onchain_copm_freeze_thaw",
    "onchain_copm_transfers_top100_edges",
    "onchain_copm_daily_transfers",
    "onchain_copm_address_activity_top400",
    "onchain_copm_time_patterns",
    "onchain_copm_ccop_daily_flow",
)


def run_onchain_migration(
    conn: duckdb.DuckDBPyConnection,
    *,
    data_root: Path | None = None,
) -> dict[str, int]:
    """Ingest all 9 on-chain CSVs into the structural-econ DuckDB.

    Returns ``{table_name: rows_written}`` so callers can log per-table
    row counts. Idempotent — rerunning produces identical state because
    every ingest uses ``INSERT OR REPLACE`` keyed on each table's
    primary key.

    Rev-5.1 Task 11.M.5: this function **owns** the on-chain table DDL
    end-to-end. It drops any pre-existing on-chain tables and re-creates
    them from :mod:`scripts.econ_schema`'s DDL before ingesting. This
    guarantees the migration is reproducible even when the checked-in
    DuckDB file (``contracts/data/structural_econ.duckdb``) carries an
    older on-chain schema (e.g. from the Rev-5.0 TIMESTAMP/DOUBLE
    variant). Non-on-chain tables (``fred_daily``, ``banrep_*``,
    ``dane_*``) are NEVER touched — strictly additive to the Rev-4
    panel.
    """
    # Import locally to avoid a module-level cycle with econ_schema.
    from scripts.econ_schema import (
        _DDL_ONCHAIN_COPM_ADDRESS_ACTIVITY,
        _DDL_ONCHAIN_COPM_BURNS,
        _DDL_ONCHAIN_COPM_CCOP_DAILY_FLOW,
        _DDL_ONCHAIN_COPM_DAILY_TRANSFERS,
        _DDL_ONCHAIN_COPM_FREEZE_THAW,
        _DDL_ONCHAIN_COPM_MINTS,
        _DDL_ONCHAIN_COPM_TIME_PATTERNS,
        _DDL_ONCHAIN_COPM_TOP100_EDGES,
        _DDL_ONCHAIN_COPM_TRANSFERS_SAMPLE,
    )

    # Drop (in reverse dependency order — all tables are independent) then
    # recreate from the canonical Rev-5.1 DDL.
    for table in _ONCHAIN_TABLES:
        conn.execute(f'DROP TABLE IF EXISTS "{table}"')
    for ddl in (
        _DDL_ONCHAIN_COPM_MINTS,
        _DDL_ONCHAIN_COPM_BURNS,
        _DDL_ONCHAIN_COPM_TRANSFERS_SAMPLE,
        _DDL_ONCHAIN_COPM_FREEZE_THAW,
        _DDL_ONCHAIN_COPM_TOP100_EDGES,
        _DDL_ONCHAIN_COPM_DAILY_TRANSFERS,
        _DDL_ONCHAIN_COPM_ADDRESS_ACTIVITY,
        _DDL_ONCHAIN_COPM_TIME_PATTERNS,
        _DDL_ONCHAIN_COPM_CCOP_DAILY_FLOW,
    ):
        conn.execute(ddl)

    root = data_root if data_root is not None else _DEFAULT_DATA_ROOT
    per_tx = root / "copm_per_tx"

    result: dict[str, int] = {}
    result["onchain_copm_mints"] = ingest_onchain_copm_mints(
        conn, per_tx / "copm_mints.csv"
    )
    result["onchain_copm_burns"] = ingest_onchain_copm_burns(
        conn, per_tx / "copm_burns.csv"
    )
    result["onchain_copm_transfers_sample"] = (
        ingest_onchain_copm_transfers_sample(
            conn, per_tx / "copm_transfers.csv"
        )
    )
    result["onchain_copm_freeze_thaw"] = ingest_onchain_copm_freeze_thaw(
        conn, per_tx / "copm_freeze_thaw.csv"
    )
    result["onchain_copm_transfers_top100_edges"] = (
        ingest_onchain_copm_top100_edges(
            conn, per_tx / "copm_transfers_top100_edges.csv"
        )
    )
    result["onchain_copm_daily_transfers"] = (
        ingest_onchain_copm_daily_transfers(
            conn, per_tx / "copm_daily_transfers.csv"
        )
    )
    result["onchain_copm_address_activity_top400"] = (
        ingest_onchain_copm_address_activity(
            conn, per_tx / "copm_address_activity_top400.csv"
        )
    )
    result["onchain_copm_time_patterns"] = ingest_onchain_copm_time_patterns(
        conn, per_tx / "copm_time_patterns.csv"
    )
    result["onchain_copm_ccop_daily_flow"] = ingest_onchain_ccop_daily_flow(
        conn, root / "copm_ccop_daily_flow.csv"
    )

    return result
