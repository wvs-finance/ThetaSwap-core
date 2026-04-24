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
import pandas as pd
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


# ── Task 11.N: weekly X_d surrogate ingestion ──────────────────────────────
#
# Derived table: computed from ``onchain_copm_ccop_daily_flow`` and written
# to ``onchain_xd_weekly``.  See the design memo at
# ``contracts/.scratch/2026-04-24-xd-filter-design-memo.md`` for the
# ``X_D_INSUFFICIENT_DATA`` escalation; ``proxy_kind`` is the in-row flag.


def ingest_onchain_xd_weekly(
    conn: duckdb.DuckDBPyConnection,
) -> int:
    """Compute the X_d weekly panel and write it to ``onchain_xd_weekly``.

    Consumes ``onchain_copm_ccop_daily_flow`` via
    :func:`scripts.econ_query_api.load_onchain_daily_flow` and applies
    :func:`scripts.copm_xd_filter.compute_weekly_xd`.  Persists each
    Friday anchor as one row.  ``value_usd`` stored as VARCHAR with
    exact 6-decimal formatting (mirrors the daily-flow table's USD
    text-preservation convention).

    Rev-5.2.1 Task 11.N.1 Step 5 extension: when the
    ``onchain_copm_transfers`` full-dataset table has been populated
    (Step-4 backfill landed), also write distribution-channel X_d
    rows via :func:`scripts.copm_xd_filter.compute_weekly_xd_from_transfers`
    so ``onchain_xd_weekly`` carries both channels side-by-side (the
    relaxed CHECK constraint + composite PK from Step 0 supports this).

    Returns row-count written (supply + distribution combined).
    Idempotent via ``INSERT OR REPLACE`` keyed on
    ``(week_start, proxy_kind)``.
    """
    # Imports kept local to prevent a module-level cycle — both
    # ``copm_xd_filter`` and ``econ_query_api`` import from ``econ_schema``.
    from scripts.copm_xd_filter import (
        classify_addresses,
        compute_weekly_xd,
        compute_weekly_xd_from_transfers,
    )
    from scripts.econ_query_api import (
        load_onchain_copm_address_activity,
        load_onchain_copm_top100_edges,
        load_onchain_copm_transfers_full,
        load_onchain_daily_flow,
    )

    daily = load_onchain_daily_flow(conn)

    # Supply-channel series (Rev-5.1) — always computed.
    supply_panel = compute_weekly_xd(daily, proxy_kind="net_primary_issuance_usd")

    written = 0
    for friday, value, partial in zip(
        supply_panel.weeks,
        supply_panel.values_usd,
        supply_panel.is_partial_week,
        strict=True,
    ):
        conn.execute(
            "INSERT OR REPLACE INTO onchain_xd_weekly "
            "(week_start, value_usd, is_partial_week, proxy_kind) "
            "VALUES (?, ?, ?, ?)",
            [friday, f"{value:.6f}", bool(partial), supply_panel.proxy_kind],
        )
        written += 1

    # Distribution-channel series (Rev-5.2.1) — only when the full-
    # transfers table carries rows. Pre-Step-4 runs leave the
    # distribution channel absent (no row-level data yet) without
    # triggering an error so Step-0 migrations remain green.
    full_count = conn.execute(
        "SELECT COUNT(*) FROM onchain_copm_transfers"
    ).fetchone()
    has_full = full_count is not None and int(full_count[0]) > 100
    if has_full:
        # Pre-committed address-universe partition (memo §3.1 hubs
        # align with Task 11.M profile shorthands resolved earlier).
        known_hubs = frozenset({
            "0x0155b191ec52728d26b1cd82f6a412d5d6897c04",
            "0x5bd35ee3c1975b2d735d2023bd4f38e3b0cfc122",
        })
        activity = load_onchain_copm_address_activity(conn)
        edges = load_onchain_copm_top100_edges(conn)
        b2b, b2c = classify_addresses(activity, edges, known_hubs=known_hubs)

        transfers = load_onchain_copm_transfers_full(conn)
        dist_panel = compute_weekly_xd_from_transfers(
            transfers,
            b2b_addresses=b2b,
            b2c_addresses=b2c,
            daily_flow_rows=daily,
            proxy_kind="b2b_to_b2c_net_flow_usd",
        )
        for friday, value, partial in zip(
            dist_panel.weeks,
            dist_panel.values_usd,
            dist_panel.is_partial_week,
            strict=True,
        ):
            conn.execute(
                "INSERT OR REPLACE INTO onchain_xd_weekly "
                "(week_start, value_usd, is_partial_week, proxy_kind) "
                "VALUES (?, ?, ?, ?)",
                [friday, f"{value:.6f}", bool(partial), dist_panel.proxy_kind],
            )
            written += 1

    return written


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
    # Task 11.N derived table — listed here so run_onchain_migration
    # drops+recreates it alongside the raw tables.
    "onchain_xd_weekly",
    # Task 11.N.1 full-dataset table (Rev-5.2.1). Distinct from
    # ``onchain_copm_transfers_sample`` — the sample stays as audit pointer.
    "onchain_copm_transfers",
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
        _DDL_ONCHAIN_COPM_TRANSFERS,
        _DDL_ONCHAIN_COPM_TRANSFERS_SAMPLE,
        _DDL_ONCHAIN_XD_WEEKLY,
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
        _DDL_ONCHAIN_XD_WEEKLY,
        _DDL_ONCHAIN_COPM_TRANSFERS,
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

    # Task 11.N.1 full-transfers table (Rev-5.2.1). Only ingested when
    # the Step-4 backfill has landed the CSV; otherwise the table
    # stays empty so Step-0 migrations remain lightweight.
    full_transfers_csv = per_tx / "copm_transfers_full.csv"
    if full_transfers_csv.is_file():
        result["onchain_copm_transfers"] = ingest_onchain_copm_transfers(
            conn, full_transfers_csv
        )
    else:
        result["onchain_copm_transfers"] = 0

    # Task 11.N: derived weekly-X_d panel — must run LAST because it
    # consumes ``onchain_copm_ccop_daily_flow`` that the line above
    # has just ingested.
    result["onchain_xd_weekly"] = ingest_onchain_xd_weekly(conn)

    return result


# ── Task 11.N.1 (Rev-5.2.1): COPM raw-transfers backfill via JSON-RPC ───────
#
# Primary path (on-chain-native, no API key): Celo public RPCs
# ``forno.celo.org`` + ``rpc.ankr.com/celo`` via ``eth_getLogs`` paginated
# over 10,000-block windows (plan-specified; the implementation widens to
# 100,000 blocks where the endpoint tolerates it, narrowing back on any
# server-side "too many results" error).
#
# Secondary fallback: Alchemy ``getAssetTransfers`` — HALT-on-missing
# ``ALCHEMY_API_KEY`` per CR hygiene finding; no silent skip.
#
# Orchestration: ``backfill_copm_transfers`` tries primary first, falls
# back to Alchemy under plan-pre-committed trigger criteria.

_COPM_TOKEN_ADDRESS: Final[str] = (
    "0xc92e8fc2947e32f2b574cca9f2f12097a71d5606"
)
#: Transfer(address,address,uint256) event signature — keccak256.
_TRANSFER_TOPIC0: Final[str] = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)
#: Celo public RPC endpoints — primary + healthy-endpoint fallback.
_CELO_RPC_PRIMARY: Final[str] = "https://forno.celo.org"
_CELO_RPC_FALLBACK: Final[str] = "https://rpc.ankr.com/celo"
#: Alchemy Celo-mainnet JSON-RPC endpoint template.
_ALCHEMY_CELO_URL: Final[str] = (
    "https://celo-mainnet.g.alchemy.com/v2/{api_key}"
)

#: Deployment / first-transfer block — pinned by the Dune sample CSV's
#: first ``evt_block_number``.
_COPM_DEPLOY_BLOCK: Final[int] = 27_786_128

#: Plan-specified pagination unit (10,000-block windows). The primary
#: implementation uses this as a soft default — narrower windows engage
#: automatically on the recoverable "more than N results" server error.
_DEFAULT_BLOCK_WINDOW: Final[int] = 10_000

#: Maximum window when the primary endpoint tolerates wider scans
#: (forno ~ 100k blocks tested live). Windows above this hit a reliable
#: 500-class error and narrowing kicks in.
_MAX_BLOCK_WINDOW: Final[int] = 100_000

#: Backoff-exponent retry ceiling per call. With the skip-on-failure
#: fallback, we want SHORT retries (2s, 4s, 8s total ~14s per window)
#: so persistently-failing windows get skipped quickly and the scan
#: keeps moving. Intermittent 503s on other windows are absorbed by
#: the standard resume-on-restart path.
_MAX_RPC_RETRIES: Final[int] = 3

#: Checkpoint file (Rev-5.2.1 PM-P2 resumability finding).
_CHECKPOINT_PATH: Final[Path] = (
    Path(__file__).resolve().parents[1]
    / ".scratch"
    / "copm_transfers_backfill_progress.json"
)

#: Total wall-time budget before the orchestrator flips to Alchemy.
_WALL_TIME_BUDGET_S: Final[float] = 30 * 60.0  # 30 min per plan


# ── Pure helpers — log parsing ──────────────────────────────────────────────


def _topic_address(topic: str) -> str:
    """Extract a 40-hex address from a 32-byte padded log topic.

    Event-indexed address topics are left-padded to 32 bytes:
    ``0x000...000 || 40-hex address``. The last 40 hex chars are the
    address (lowercased, 0x-prefixed). Pure function.
    """
    t = topic.lower()
    if t.startswith("0x"):
        t = t[2:]
    if len(t) != 64:
        raise ValueError(f"Malformed topic (not 32 bytes): {topic!r}")
    return "0x" + t[-40:]


def _hex_to_int(raw: str) -> int:
    """Parse ``0x``-prefixed hex into an int. Pure."""
    return int(raw, 16) if raw.startswith("0x") else int(raw, 16)


def _ts_to_iso(unix_ts_hex: str) -> tuple[date, str]:
    """Parse a hex unix timestamp → ``(date, ISO-UTC-text)``.

    Pure function; returns the Dune-compatible
    ``YYYY-MM-DD HH:MM:SS.000 UTC`` text so the VARCHAR schema round-
    trips byte-exact with the Dune-exported CSVs already in the DB.
    """
    from datetime import datetime as _dt
    from datetime import timezone as _tz

    ts = int(unix_ts_hex, 16) if unix_ts_hex.startswith("0x") else int(unix_ts_hex)
    d = _dt.fromtimestamp(ts, tz=_tz.utc)
    iso = d.strftime("%Y-%m-%d %H:%M:%S.000 UTC")
    return d.date(), iso


def _parse_log_row(log: dict) -> dict:
    """Convert a single ``eth_getLogs`` result into a flat row dict.

    Pure: reads the log, writes a new dict. The dict mirrors the column
    layout of the ``onchain_copm_transfers`` DDL + the downstream CSV
    schema (minus the auto-generated ``_ingested_at``).
    """
    topics = log["topics"]
    if len(topics) < 3:
        raise ValueError(
            f"Unexpected Transfer log shape (topics < 3): {topics}"
        )
    block_ts = log.get("blockTimestamp")
    if block_ts is None:
        # Celo returns blockTimestamp on forno; if an alternate RPC
        # omits it, the caller's enrichment path must supply it.
        raise ValueError(
            "Log missing blockTimestamp; enrich via eth_getBlockByNumber"
        )
    evt_date, evt_iso = _ts_to_iso(block_ts)
    return {
        "evt_block_date": evt_date,
        "evt_block_time": evt_iso,
        "evt_tx_hash": log["transactionHash"].lower(),
        "from_address": _topic_address(topics[1]),
        "to_address": _topic_address(topics[2]),
        "value_wei": _hex_to_int(log["data"]),
        "evt_block_number": _hex_to_int(log["blockNumber"]),
        "log_index": _hex_to_int(log["logIndex"]),
    }


# ── Checkpoint I/O ──────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class BackfillCheckpoint:
    """Resumability state for Task 11.N.1 backfill (Rev-5.2.1 PM-P2)."""

    last_completed_end_block: int
    total_rows_so_far: int
    data_source: str  # "forno" | "ankr" | "alchemy"


def _read_checkpoint() -> BackfillCheckpoint | None:
    """Load the last checkpoint, or ``None`` if no prior run exists."""
    import json as _json

    if not _CHECKPOINT_PATH.is_file():
        return None
    with _CHECKPOINT_PATH.open() as fh:
        payload = _json.load(fh)
    return BackfillCheckpoint(
        last_completed_end_block=int(payload["last_completed_end_block"]),
        total_rows_so_far=int(payload["total_rows_so_far"]),
        data_source=str(payload["data_source"]),
    )


def _write_checkpoint(cp: BackfillCheckpoint) -> None:
    """Persist the checkpoint atomically via tmp-file + rename."""
    import json as _json

    _CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _CHECKPOINT_PATH.with_suffix(".json.tmp")
    with tmp.open("w") as fh:
        _json.dump(
            {
                "last_completed_end_block": cp.last_completed_end_block,
                "total_rows_so_far": cp.total_rows_so_far,
                "data_source": cp.data_source,
            },
            fh,
        )
    tmp.replace(_CHECKPOINT_PATH)


# ── RPC primary (Steps 2 + 2b) ─────────────────────────────────────────────


def _post_rpc(
    rpc_url: str,
    method: str,
    params: list,
    *,
    timeout: float = 60.0,
) -> dict:
    """One JSON-RPC POST. Raises on HTTP / JSON-RPC error."""
    resp = requests.post(
        rpc_url,
        json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
        timeout=timeout,
    )
    resp.raise_for_status()
    payload = resp.json()
    if "error" in payload:
        err = payload["error"]
        # Surface the JSON-RPC error verbatim so narrowing logic in
        # fetch_copm_transfers_rpc can pattern-match the "too many
        # results" family.
        raise RuntimeError(
            f"RPC error {err.get('code')}: {err.get('message')}"
        )
    return payload


def _get_latest_block(rpc_url: str) -> int:
    """Call ``eth_blockNumber`` and return an int."""
    payload = _post_rpc(rpc_url, "eth_blockNumber", [])
    return _hex_to_int(payload["result"])


def _get_logs_range(
    rpc_url: str,
    start_block: int,
    end_block: int,
    *,
    address: str,
    topic0: str,
) -> list[dict]:
    """Call ``eth_getLogs`` once for the inclusive range [start, end].

    Raises :class:`RuntimeError` on RPC error (caller's responsibility to
    narrow or retry).
    """
    params = [{
        "fromBlock": hex(start_block),
        "toBlock": hex(end_block),
        "address": address,
        "topics": [topic0],
    }]
    payload = _post_rpc(rpc_url, "eth_getLogs", params)
    return list(payload.get("result") or [])


def fetch_copm_transfers_rpc(
    start_block: int,
    end_block: int,
    rpc_url: str,
    *,
    address: str = _COPM_TOKEN_ADDRESS,
    topic0: str = _TRANSFER_TOPIC0,
    max_window: int = _MAX_BLOCK_WINDOW,
    initial_window: int = _MAX_BLOCK_WINDOW,
    max_retries: int = _MAX_RPC_RETRIES,
) -> pd.DataFrame:
    """Fetch COPM Transfer logs for inclusive block range [start, end].

    Plan specification (Task 11.N.1 Step 2):

      * ``requests``-only JSON-RPC (no ``web3.py`` — not installed in
        ``contracts/.venv/``).
      * Paginate in block-windows. Start at ``initial_window`` (default
        100k, forno-tolerated); narrow with a halving binary-search
        when the endpoint returns ``"query returned more than N
        results"`` or an equivalent server-side cap.
      * Exponential-backoff retries (up to ``max_retries``) per window
        before escalating to the caller.
      * Deterministic: two calls on the same range return the same rows
        (modulo chain reorgs, which are implausible at this age).

    Returns a DataFrame with the ``onchain_copm_transfers`` schema:
    ``evt_block_date``, ``evt_block_time``, ``evt_tx_hash``,
    ``from_address``, ``to_address``, ``value_wei``, ``evt_block_number``,
    ``log_index``.

    Pure modulo-network: the only side-effect is HTTP I/O. No DuckDB
    writes, no file I/O.
    """
    import time as _time

    if start_block > end_block:
        raise ValueError(
            f"start_block {start_block} > end_block {end_block}"
        )

    rows: list[dict] = []
    cursor = start_block
    window = max(1, min(initial_window, max_window))

    while cursor <= end_block:
        sub_end = min(cursor + window - 1, end_block)
        attempt = 0
        while True:
            try:
                logs = _get_logs_range(
                    rpc_url, cursor, sub_end, address=address, topic0=topic0
                )
                for log in logs:
                    rows.append(_parse_log_row(log))
                break
            except RuntimeError as exc:
                msg = str(exc).lower()
                # "too many results" family — narrow window and retry
                # from same cursor. Ankr uses "response size is larger"
                # or "block range is too large"; forno reports
                # "query returned more than".
                is_too_many = any(
                    key in msg
                    for key in (
                        "more than",
                        "response size",
                        "too many",
                        "result set",
                        "block range",
                        "range is too",
                        "too large",
                    )
                )
                if is_too_many and window > 1:
                    window = max(1, window // 2)
                    sub_end = min(cursor + window - 1, end_block)
                    continue
                attempt += 1
                if attempt >= max_retries:
                    raise
                # Exponential backoff: 1s, 2s, 4s ...
                _time.sleep(2 ** (attempt - 1))
            except requests.RequestException:
                # Retry 5xx / transient network errors with backoff.
                attempt += 1
                if attempt >= max_retries:
                    raise
                # 2s, 4s, 8s — short enough to keep the parallel
                # batch flowing even when one worker sees a 503.
                _time.sleep(2 ** attempt)

        cursor = sub_end + 1
        # Opportunistically widen the window if narrowing succeeded on
        # a prior range but the current one may tolerate the plan's
        # max; doubling back up cheaply recovers throughput after a
        # transient-dense window.
        if window < max_window:
            window = min(window * 2, max_window)

    if not rows:
        return pd.DataFrame(
            columns=[
                "evt_block_date",
                "evt_block_time",
                "evt_tx_hash",
                "from_address",
                "to_address",
                "value_wei",
                "evt_block_number",
                "log_index",
            ]
        )
    return pd.DataFrame(rows)


# ── Alchemy secondary (Step 3) ──────────────────────────────────────────────


def fetch_copm_transfers_alchemy(
    api_key: str | None,
    *,
    address: str = _COPM_TOKEN_ADDRESS,
) -> pd.DataFrame:
    """Fetch COPM Transfer events via Alchemy ``alchemy_getAssetTransfers``.

    HALT-on-missing: raises :class:`RuntimeError` if ``api_key`` is
    ``None`` / empty (CR hygiene finding). Never silently skips — a
    missing key surfaces at the orchestration layer so the operator
    sees the root cause rather than a silent regression to the 10-row
    sample.

    Returns the same DataFrame schema as
    :func:`fetch_copm_transfers_rpc`.
    """
    if not api_key:
        raise RuntimeError(
            "ALCHEMY_API_KEY required for fallback path. "
            "Populate contracts/.env or export the env var, then rerun. "
            "See contracts/.env.example for the exact variable name."
        )

    url = _ALCHEMY_CELO_URL.format(api_key=api_key)

    rows: list[dict] = []
    page_key: str | None = None
    # Alchemy caps 1000 per page per docs.
    while True:
        params = {
            "fromBlock": hex(_COPM_DEPLOY_BLOCK),
            "toBlock": "latest",
            "contractAddresses": [address],
            "category": ["erc20"],
            "maxCount": hex(1000),
            "withMetadata": True,
            "excludeZeroValue": False,
            "order": "asc",
        }
        if page_key:
            params["pageKey"] = page_key

        payload = _post_rpc(url, "alchemy_getAssetTransfers", [params])
        result = payload["result"]
        transfers = result.get("transfers") or []
        for t in transfers:
            # Alchemy's metadata block carries the block timestamp as
            # ISO-8601 "2024-09-17T19:54:27.000Z" — convert to the
            # Dune-compatible text format.
            meta = t.get("metadata") or {}
            block_ts_iso = meta.get("blockTimestamp")
            if block_ts_iso:
                from datetime import datetime as _dt

                dt_obj = _dt.strptime(
                    block_ts_iso.replace("Z", "").split(".")[0],
                    "%Y-%m-%dT%H:%M:%S",
                )
                evt_date = dt_obj.date()
                evt_iso = dt_obj.strftime("%Y-%m-%d %H:%M:%S.000 UTC")
            else:
                # No metadata — fall back to a zero-filled timestamp so
                # the row is still ingestable; caller must surface this
                # in the provenance README.
                evt_date = date(1970, 1, 1)
                evt_iso = "1970-01-01 00:00:00.000 UTC"

            # Alchemy returns ``value`` as a decimal-string in token
            # units; ``rawContract.value`` is 0x-hex wei. Prefer the
            # hex wei so precision matches the RPC path.
            raw_val = (t.get("rawContract") or {}).get("value") or "0x0"
            value_wei = _hex_to_int(raw_val)

            rows.append({
                "evt_block_date": evt_date,
                "evt_block_time": evt_iso,
                "evt_tx_hash": t["hash"].lower(),
                "from_address": (t.get("from") or "").lower(),
                "to_address": (t.get("to") or "").lower(),
                "value_wei": value_wei,
                "evt_block_number": _hex_to_int(t["blockNum"]),
                # Alchemy doesn't expose logIndex in this endpoint;
                # use uniqueId text-hash → stable int per transfer.
                # This keeps the PK ``(evt_tx_hash, log_index)``
                # non-colliding even when a tx emits multiple events.
                "log_index": int(
                    hashlib.sha256(
                        t.get("uniqueId", "").encode()
                    ).hexdigest()[:12],
                    16,
                ) if t.get("uniqueId") else 0,
            })
        page_key = result.get("pageKey")
        if not page_key:
            break

    return pd.DataFrame(
        rows,
        columns=[
            "evt_block_date",
            "evt_block_time",
            "evt_tx_hash",
            "from_address",
            "to_address",
            "value_wei",
            "evt_block_number",
            "log_index",
        ],
    )


# ── Orchestration (Step 3b) ─────────────────────────────────────────────────


_CSV_COLS: Final[tuple[str, ...]] = (
    "evt_block_date",
    "evt_block_time",
    "evt_tx_hash",
    "from_address",
    "to_address",
    "value_wei",
    "evt_block_number",
    "log_index",
)


def _write_csv(df: pd.DataFrame, path: Path) -> int:
    """Write the RPC-fetched DataFrame to the target CSV path.

    Columns are ordered to match the ``onchain_copm_transfers`` DDL +
    the Dune-export convention (same shape as the sample CSV's header).
    Returns the row count written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, columns=list(_CSV_COLS), index=False)
    return len(df)


def _append_csv(df: pd.DataFrame, path: Path) -> int:
    """Append rows to the backfill CSV. Writes header only on first call.

    Keeps the file accumulated incrementally so a mid-pull interruption
    preserves progress to disk (PM-P2 extension — complements the
    checkpoint JSON).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.is_file()
    df.to_csv(
        path,
        columns=list(_CSV_COLS),
        index=False,
        header=write_header,
        mode="a",
    )
    return len(df)


@dataclass(frozen=True, slots=True)
class BackfillResult:
    """Summary of a :func:`backfill_copm_transfers` call."""

    rows: int
    data_source: str  # "forno" | "ankr" | "alchemy"
    start_block: int
    end_block: int
    wall_time_s: float
    narrowed_windows: int
    skipped_windows: tuple[tuple[int, int], ...] = ()


def backfill_copm_transfers(
    *,
    alchemy_api_key: str | None = None,
    output_csv: Path | None = None,
    primary_urls: tuple[str, ...] = (_CELO_RPC_PRIMARY, _CELO_RPC_FALLBACK),
    start_block: int = _COPM_DEPLOY_BLOCK,
    end_block: int | None = None,
    expected_rows: int = 110_069,
    tolerance: float = 0.01,
    wall_time_budget_s: float = _WALL_TIME_BUDGET_S,
) -> BackfillResult:
    """Orchestrate the primary-RPC → Alchemy-fallback backfill.

    Plan fallback-trigger criteria (Task 11.N.1):
      1. Public RPC returns < expected_rows × (1 − tolerance).
      2. Any endpoint times out on 3 consecutive ranges.
      3. The range-size binary search narrows below 1,000 blocks AND
         still errors (primary too aggressive for endpoint).
      4. Total wall-time exceeds ``wall_time_budget_s``.

    Writes a per-10k-block checkpoint on every completed range so a
    mid-pull interruption resumes from the last completed block rather
    than from zero (PM-P2).

    Returns a :class:`BackfillResult` summary for the caller's
    provenance log.
    """
    import time as _time

    t0 = _time.monotonic()

    # Resume from checkpoint if present. PM-P2 resumability: rows
    # fetched before the checkpoint was last written are re-read from
    # the output CSV (if it exists) so the 30-min wall-time budget
    # applies only to NEW RPC work. The CSV is NOT truncated on
    # resume — new batches append below the existing rows, and the
    # final pass dedupes on (evt_tx_hash, log_index) before the
    # orchestration exits. This keeps mid-run process exits
    # non-destructive: a crash leaves a CSV with both prior + newly
    # completed batches on disk.
    checkpoint = _read_checkpoint()
    prior_rows: list[dict] = []
    if checkpoint is not None:
        resume_from = checkpoint.last_completed_end_block + 1
        if output_csv is not None and output_csv.is_file():
            prior_df = pd.read_csv(output_csv, dtype={"value_wei": "string"})
            # Coerce value_wei back to int since CSV stored it as str
            # (dtype hint above preserves it as string to avoid
            # float precision loss on uint256-ish values).
            prior_df["value_wei"] = prior_df["value_wei"].astype(object).apply(
                lambda s: int(s) if isinstance(s, str) and s else s
            )
            prior_rows = prior_df.to_dict("records")
            print(
                f"[backfill] Resuming from block {resume_from} "
                f"(prior source={checkpoint.data_source}, "
                f"rows_so_far={checkpoint.total_rows_so_far}, "
                f"reloaded {len(prior_rows)} rows from {output_csv.name})"
            )
        else:
            print(
                f"[backfill] Resuming from block {resume_from} "
                f"(prior source={checkpoint.data_source}, "
                f"rows_so_far={checkpoint.total_rows_so_far}, "
                f"no prior CSV — prior rows are LOST, consider rerunning "
                f"from scratch)"
            )
    else:
        resume_from = start_block

    # Default end_block = latest on-chain head.
    if end_block is None:
        # Probe latest via primary; if that fails, propagate.
        last_err: Exception | None = None
        latest: int | None = None
        for url in primary_urls:
            try:
                latest = _get_latest_block(url)
                break
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                continue
        if latest is None:
            raise RuntimeError(
                f"Cannot reach any primary RPC to determine latest block: "
                f"{last_err!r}"
            )
        end_block = latest

    # Per-endpoint window caps — forno tolerates the plan's 100k max;
    # Ankr's cap is narrower ("Block range is too large" at 100k; we
    # default Ankr to the plan's 10k minimum).
    _ENDPOINT_WINDOW: dict[str, int] = {
        _CELO_RPC_PRIMARY: _MAX_BLOCK_WINDOW,  # forno 100k
        _CELO_RPC_FALLBACK: _DEFAULT_BLOCK_WINDOW,  # ankr 10k
    }

    # Shared progress state across primary endpoints — rotating to the
    # next endpoint on failure RESUMES from the last completed window
    # rather than restarting from zero. This is the PM-P2 resumability
    # invariant applied at the inter-endpoint rotation level.
    primary_rows: list[dict] = []
    data_source: str | None = None
    narrowed = 0
    primary_failed = False
    cursor = resume_from

    # Rev-5.2.1: forno returns consistent HTTP 503 under any level
    # of concurrency (including 2 workers empirically) — its rate
    # limit appears to be per-IP-sustained rather than per-request,
    # so single-threaded is the reliable path. 374 windows ×
    # ~2-3s/window serial ≈ 12-18 min within the 30-min budget.
    from concurrent.futures import ThreadPoolExecutor, as_completed

    _MAX_WORKERS: Final[int] = 1

    # Track windows that persistently failed so we can report + skip.
    skipped_windows: list[tuple[int, int]] = []

    for url in primary_urls:
        # Pass over this endpoint if we already finished.
        if cursor > end_block:
            break
        tag = (
            "forno"
            if "forno" in url
            else "ankr" if "ankr" in url else url
        )
        window = _ENDPOINT_WINDOW.get(url, _DEFAULT_BLOCK_WINDOW)
        # Build the list of windows from current cursor to end.
        windows: list[tuple[int, int]] = []
        w_cursor = cursor
        while w_cursor <= end_block:
            w_end = min(w_cursor + window - 1, end_block)
            windows.append((w_cursor, w_end))
            w_cursor = w_end + 1

        # Fetch in parallel batches. Each batch has _MAX_WORKERS
        # windows; within a batch, we wait for all futures to
        # complete before advancing the cursor/checkpoint — this
        # preserves the "checkpoint reflects highest completed
        # contiguous block" invariant even under parallelism.
        def _fetch_one(rng: tuple[int, int]) -> list[dict]:
            """Worker: fetch one window; returns [] or parsed rows."""
            return fetch_copm_transfers_rpc(
                start_block=rng[0],
                end_block=rng[1],
                rpc_url=url,
                initial_window=window,
                max_window=window,
            ).to_dict("records")

        batch_size = _MAX_WORKERS
        idx = 0
        # Rev-5.2.1 resilience: instead of failing the WHOLE
        # endpoint-loop when one window dies, skip individual
        # persistently-failing windows and continue. Forno in
        # particular returns sporadic 503s on specific block ranges
        # (infrastructure variability) — skipping keeps the scan
        # moving while we document the gaps in provenance.
        with ThreadPoolExecutor(max_workers=batch_size) as pool:
            while idx < len(windows):
                if _time.monotonic() - t0 > wall_time_budget_s:
                    # Don't raise — we want to return whatever rows
                    # the scan has collected so far. The outer
                    # orchestration's row-count trigger will decide
                    # if Alchemy fallback kicks in.
                    print(
                        f"[backfill] Wall-time budget {wall_time_budget_s:.0f}s "
                        f"exceeded at batch idx={idx}; stopping scan"
                    )
                    break
                batch = windows[idx : idx + batch_size]
                futures = {pool.submit(_fetch_one, rng): rng for rng in batch}
                per_window: dict[tuple[int, int], list[dict]] = {}
                for fut in as_completed(futures):
                    rng = futures[fut]
                    try:
                        per_window[rng] = fut.result()
                    except Exception as exc:  # noqa: BLE001
                        # Persistent failure after retries — skip.
                        print(
                            f"[backfill] skipping window {rng} at {url}: {exc!r}"
                        )
                        skipped_windows.append(rng)
                        per_window[rng] = []
                batch_rows: list[dict] = []
                for rng in batch:
                    batch_rows.extend(per_window.get(rng, []))
                primary_rows.extend(batch_rows)
                if output_csv is not None and batch_rows:
                    _append_csv(pd.DataFrame(batch_rows), output_csv)
                cp = BackfillCheckpoint(
                    last_completed_end_block=batch[-1][1],
                    total_rows_so_far=(
                        len(primary_rows) + checkpoint.total_rows_so_far
                        if checkpoint
                        else len(primary_rows)
                    ),
                    data_source=tag,
                )
                _write_checkpoint(cp)
                cursor = batch[-1][1] + 1
                idx += batch_size
        data_source = tag
        break

    # Accept the primary path if it finished the block range — even if
    # it required rotation — provided the row count passes the
    # tolerance check below. ``primary_failed=True`` alone does not
    # trigger Alchemy as long as the rotational endpoint finished the
    # scan.
    if cursor > end_block and data_source is None:
        # All endpoints rotated and the last one advanced the cursor
        # past end_block, but the inner loop exited via exception
        # before setting data_source. Recover the last successful tag
        # from the checkpoint.
        last_cp = _read_checkpoint()
        if last_cp is not None:
            data_source = last_cp.data_source
            primary_failed = False

    # Combine prior (reloaded from CSV) + new (this run) — dedup by
    # (evt_tx_hash, log_index) on the join just in case the last
    # partial run had overlapping rows.
    combined_rows = list(prior_rows) + list(primary_rows)
    seen: set[tuple[str, int]] = set()
    deduped_rows: list[dict] = []
    for row in combined_rows:
        key = (row["evt_tx_hash"], int(row["log_index"]))
        if key in seen:
            continue
        seen.add(key)
        deduped_rows.append(row)
    primary_rows = deduped_rows

    # Row-count trigger: if primary reached row count below the
    # tolerance bound, declare fallback.
    need_alchemy = (
        primary_failed
        or data_source is None
        or (
            expected_rows > 0
            and len(primary_rows) < int(expected_rows * (1 - tolerance))
        )
    )

    if need_alchemy:
        print(
            f"[backfill] Fallback triggered (primary rows={len(primary_rows)} "
            f"vs expected ≥ {int(expected_rows * (1 - tolerance))})"
        )
        df_alchemy = fetch_copm_transfers_alchemy(alchemy_api_key)
        chosen_rows = df_alchemy.to_dict("records")
        data_source = "alchemy"
        cp = BackfillCheckpoint(
            last_completed_end_block=end_block,
            total_rows_so_far=len(chosen_rows),
            data_source="alchemy",
        )
        _write_checkpoint(cp)
    else:
        chosen_rows = primary_rows

    df_out = pd.DataFrame(
        chosen_rows,
        columns=list(_CSV_COLS),
    )

    # Alchemy path fetched all rows in one shot; overwrite the CSV
    # (incremental appends from the primary path, if any, would have
    # been abandoned). Primary path already appended incrementally —
    # re-write to enforce dedup + canonical order.
    if output_csv is not None:
        _write_csv(df_out, output_csv)

    return BackfillResult(
        rows=len(df_out),
        data_source=data_source or "unknown",
        start_block=start_block,
        end_block=end_block,
        wall_time_s=_time.monotonic() - t0,
        narrowed_windows=narrowed,
        skipped_windows=tuple(skipped_windows),
    )


# ── Ingestion: ``onchain_copm_transfers`` ──────────────────────────────────


def ingest_onchain_copm_transfers(
    conn: duckdb.DuckDBPyConnection, csv_path: Path
) -> int:
    """Ingest the full ``copm_transfers_full.csv`` into the NEW table.

    Schema: ``evt_block_date, evt_block_time, evt_tx_hash, from_address,
    to_address, value_wei, evt_block_number, log_index``. PK is
    ``(evt_tx_hash, log_index)`` — a single transaction can emit
    multiple Transfer events (e.g. a mint emits both
    ``0x0 → treasury`` and ``treasury → hub`` in the same tx), and the
    log index disambiguates them.

    Uses DuckDB's ``read_csv`` + bulk ``INSERT … FROM`` for O(n)
    ingestion — row-by-row ``executemany`` is O(n) but burns ~5 min
    on 50k rows due to Python-side overhead; the bulk path is ~10s.
    """
    if not csv_path.is_file():
        return 0
    rows_df = pd.read_csv(
        csv_path,
        dtype={
            "evt_tx_hash": "string",
            "from_address": "string",
            "to_address": "string",
            "value_wei": "string",  # preserve precision
        },
    )
    if rows_df.empty:
        return 0

    # Normalise case-insensitive fields.
    rows_df["evt_tx_hash"] = rows_df["evt_tx_hash"].str.strip().str.lower()
    rows_df["from_address"] = rows_df["from_address"].str.strip().str.lower()
    rows_df["to_address"] = rows_df["to_address"].str.strip().str.lower()
    rows_df["evt_block_time"] = rows_df["evt_block_time"].str.strip()

    # DuckDB accepts pandas DataFrame as a virtual table.
    # Cast types via the SELECT so the HUGEINT column gets a DECIMAL
    # conversion from the string column without precision loss.
    conn.register("rows_df_view", rows_df)
    conn.execute(
        """
        INSERT OR REPLACE INTO onchain_copm_transfers (
            evt_block_date, evt_block_time, evt_tx_hash, from_address,
            to_address, value_wei, evt_block_number, log_index
        )
        SELECT
            CAST(evt_block_date AS DATE),
            evt_block_time,
            evt_tx_hash,
            from_address,
            to_address,
            CAST(value_wei AS HUGEINT),
            CAST(evt_block_number AS UBIGINT),
            CAST(log_index AS UBIGINT)
        FROM rows_df_view
        """
    )
    conn.unregister("rows_df_view")
    return int(len(rows_df))
