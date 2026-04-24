"""Pipeline orchestrator for structural econometrics data.

Coordinates download -> insert -> panel build -> validate.
"""
from __future__ import annotations

import csv as _csv
import hashlib
from dataclasses import dataclass
from datetime import date, datetime
from io import StringIO
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
