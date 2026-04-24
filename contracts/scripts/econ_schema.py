"""Schema DDL and initialization for the structural econometrics DuckDB.

All CREATE TABLE statements follow the spec:
contracts/notes/structural-econometrics/specs/2026-04-16-data-schema-acquisition.md (Rev 4)
"""
from __future__ import annotations

from typing import Final

import duckdb

# ── Expected tables ──────────────────────────────────────────────────────────

EXPECTED_TABLES: Final[frozenset[str]] = frozenset({
    "banrep_trm_daily",
    "banrep_ibr_daily",
    "banrep_intervention_daily",
    "banrep_meeting_calendar",
    "fred_daily",
    "fred_monthly",
    "dane_ipc_monthly",
    "dane_ipp_monthly",
    "dane_release_calendar",
    "bls_release_calendar",
    "download_manifest",
    # ── Task 11.M.5: on-chain COPM / cCOP tables ────────────────────────
    "onchain_copm_mints",
    "onchain_copm_burns",
    "onchain_copm_transfers_sample",
    "onchain_copm_freeze_thaw",
    "onchain_copm_transfers_top100_edges",
    "onchain_copm_daily_transfers",
    "onchain_copm_address_activity_top400",
    "onchain_copm_time_patterns",
    "onchain_copm_ccop_daily_flow",
    # ── Task 11.N: weekly X_d surrogate (net primary issuance USD) ──────
    "onchain_xd_weekly",
})

# ── DDL statements ───────────────────────────────────────────────────────────

_DDL_BANREP_TRM_DAILY: Final[str] = """
CREATE TABLE IF NOT EXISTS banrep_trm_daily (
    date DATE PRIMARY KEY,
    trm DOUBLE NOT NULL,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_BANREP_IBR_DAILY: Final[str] = """
CREATE TABLE IF NOT EXISTS banrep_ibr_daily (
    date DATE PRIMARY KEY,
    ibr_overnight_er DOUBLE NOT NULL,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_BANREP_INTERVENTION_DAILY: Final[str] = """
CREATE TABLE IF NOT EXISTS banrep_intervention_daily (
    date DATE PRIMARY KEY,
    discretionary DOUBLE,
    direct_purchase DOUBLE,
    put_volatility DOUBLE,
    call_volatility DOUBLE,
    put_reserve_accum DOUBLE,
    call_reserve_decum DOUBLE,
    ndf DOUBLE,
    fx_swaps DOUBLE,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_BANREP_MEETING_CALENDAR: Final[str] = """
CREATE TABLE IF NOT EXISTS banrep_meeting_calendar (
    year SMALLINT NOT NULL,
    meeting_date DATE NOT NULL,
    meeting_type VARCHAR NOT NULL,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (year, meeting_date)
)
"""

_DDL_FRED_DAILY: Final[str] = """
CREATE TABLE IF NOT EXISTS fred_daily (
    series_id VARCHAR NOT NULL CHECK (series_id IN ('VIXCLS', 'DCOILWTICO', 'DCOILBRENTEU', 'DFF')),
    date DATE NOT NULL,
    value DOUBLE,
    PRIMARY KEY (series_id, date)
)
"""

_DDL_FRED_MONTHLY: Final[str] = """
CREATE TABLE IF NOT EXISTS fred_monthly (
    series_id VARCHAR NOT NULL CHECK (series_id IN ('CPIAUCSL')),
    date DATE NOT NULL,
    value DOUBLE,
    PRIMARY KEY (series_id, date)
)
"""

_DDL_DANE_IPC_MONTHLY: Final[str] = """
CREATE TABLE IF NOT EXISTS dane_ipc_monthly (
    date DATE PRIMARY KEY,
    ipc_index DOUBLE,
    ipc_pct_change DOUBLE,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_DANE_IPP_MONTHLY: Final[str] = """
CREATE TABLE IF NOT EXISTS dane_ipp_monthly (
    date DATE PRIMARY KEY,
    ipp_index DOUBLE,
    ipp_pct_change DOUBLE,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_DANE_RELEASE_CALENDAR: Final[str] = """
CREATE TABLE IF NOT EXISTS dane_release_calendar (
    year SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    release_date DATE NOT NULL,
    series VARCHAR NOT NULL CHECK (series IN ('ipc', 'ipp')),
    imputed BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (year, month, series),
    UNIQUE (release_date, series)
)
"""

_DDL_BLS_RELEASE_CALENDAR: Final[str] = """
CREATE TABLE IF NOT EXISTS bls_release_calendar (
    year SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    release_date DATE NOT NULL,
    PRIMARY KEY (year, month),
    UNIQUE (release_date)
)
"""

_DDL_DOWNLOAD_MANIFEST: Final[str] = """
CREATE TABLE IF NOT EXISTS download_manifest (
    source VARCHAR NOT NULL,
    downloaded_at TIMESTAMP NOT NULL,
    row_count INTEGER,
    date_min DATE,
    date_max DATE,
    sha256 VARCHAR,
    url_or_path VARCHAR,
    status VARCHAR NOT NULL,
    notes VARCHAR,
    PRIMARY KEY (source, downloaded_at)
)
"""

_ALL_DDL: Final[tuple[str, ...]] = (
    _DDL_BANREP_TRM_DAILY,
    _DDL_BANREP_IBR_DAILY,
    _DDL_BANREP_INTERVENTION_DAILY,
    _DDL_BANREP_MEETING_CALENDAR,
    _DDL_FRED_DAILY,
    _DDL_FRED_MONTHLY,
    _DDL_DANE_IPC_MONTHLY,
    _DDL_DANE_IPP_MONTHLY,
    _DDL_DANE_RELEASE_CALENDAR,
    _DDL_BLS_RELEASE_CALENDAR,
    _DDL_DOWNLOAD_MANIFEST,
)


# ── Task 11.M.5 on-chain COPM / cCOP DDL ────────────────────────────────────
#
# Nine tables mirroring the 8 Dune profile CSVs delivered in 11.M plus the
# existing 585-day ``copm_ccop_daily_flow.csv`` from Task 11.A. Types follow
# DuckDB conventions, with one invariant that overrides type-convenience:
#
#   **Byte-exact CSV round-trip** (test_csv_ingest_lossless). The test
#   checksum hashes the DuckDB table's column values joined with ``|`` and
#   compares against the same hash computed over the raw CSV cells. So any
#   column whose DuckDB native string form differs from the CSV raw text
#   (e.g. ``TIMESTAMP`` drops the ``.000 UTC`` suffix, ``DOUBLE`` trims
#   trailing-zero decimals, ``SMALLINT`` sorts numerically but CSV is
#   lexical) is stored as ``VARCHAR`` verbatim. Loader functions in
#   :mod:`scripts.econ_query_api` CAST those VARCHARs to ``datetime`` /
#   ``float`` / ``int`` on the way out so downstream callers see typed
#   values. Semantic ``DATE`` / ``HUGEINT`` / ``BOOLEAN`` columns round-
#   trip byte-exact (``str(datetime.date) == '2024-09-17'`` matches CSV
#   exactly; HUGEINT decimals match; ``True`` / ``False`` become ``'true'``
#   / ``'false'`` via the test normaliser).
#
# Other type rules unchanged:
#   * Ethereum-style addresses → ``VARCHAR(42)`` (0x-prefixed 40-hex). Some
#     rows carry a NULL address (e.g. ``burn`` with no explicit account);
#     those columns stay nullable.
#   * Transaction hashes → ``VARCHAR(66)`` (0x + 64-hex).
#   * Wei amounts → ``HUGEINT`` (signed 128-bit, covers up to ~1.7e38; the
#     largest observed row is ~3.4e27 so headroom is generous). Columns that
#     can be NULL (``amount_wei`` on freeze/thaw events) stay nullable.
#
# ``address_activity_top400`` and ``transfers_top100_edges`` additionally
# carry a ``_csv_row_idx UBIGINT`` sort-key column (0-based, unique) so the
# DB ORDER BY can reproduce the source-CSV row order exactly. Dune's native
# result ordering for those two tables is not derivable from the data
# columns alone (tie-breaks are not a monotone function of any single
# column) — the stored row index is the only deterministic handle. The
# test's ``_order_col_for`` references this sort-key column with a
# documented rationale.
#
# A ``_ingested_at TIMESTAMP DEFAULT current_timestamp`` column is attached to
# every table so the CSV-side vs. DB-side lossless-ingest checksum can skip
# it (see ``_CHECKSUM_COLUMNS`` in the test file). All tables use ``CREATE
# TABLE IF NOT EXISTS`` so re-running ``init_db`` is a no-op.

_DDL_ONCHAIN_COPM_MINTS: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_copm_mints (
    call_block_date DATE NOT NULL,
    call_block_time VARCHAR NOT NULL,  -- raw CSV text; see module docstring
    tx_hash VARCHAR(66) NOT NULL,
    tx_from VARCHAR(42) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    amount_wei HUGEINT NOT NULL,
    call_success BOOLEAN NOT NULL,
    call_block_number UBIGINT NOT NULL,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (tx_hash, call_block_time)
)
"""

_DDL_ONCHAIN_COPM_BURNS: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_copm_burns (
    call_block_date DATE NOT NULL,
    call_block_time VARCHAR NOT NULL,  -- raw CSV text; see module docstring
    tx_hash VARCHAR(66) NOT NULL,
    tx_from VARCHAR(42) NOT NULL,
    account VARCHAR(42),
    amount_wei HUGEINT NOT NULL,
    call_success BOOLEAN NOT NULL,
    call_block_number UBIGINT NOT NULL,
    burn_kind VARCHAR NOT NULL CHECK (burn_kind IN ('burn', 'burnFrozen')),
    _csv_row_idx UBIGINT NOT NULL,  -- stable CSV row order; see module docstring
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (tx_hash, burn_kind),
    UNIQUE (_csv_row_idx)
)
"""

# ``copm_transfers`` stores the 10-row SAMPLE. The full 110,069-row raw set
# lives in Dune query 7369028 (Dune MCP pagination prevents MCP retrieval).
_DDL_ONCHAIN_COPM_TRANSFERS_SAMPLE: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_copm_transfers_sample (
    evt_block_date DATE NOT NULL,
    evt_block_time VARCHAR NOT NULL,  -- raw CSV text; see module docstring
    evt_tx_hash VARCHAR(66) NOT NULL,
    from_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    value_wei HUGEINT NOT NULL,
    evt_block_number UBIGINT NOT NULL,
    _csv_row_idx UBIGINT NOT NULL,  -- stable CSV row order; see module docstring
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (evt_tx_hash, from_address, to_address, value_wei),
    UNIQUE (_csv_row_idx)
)
"""

_DDL_ONCHAIN_COPM_FREEZE_THAW: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_copm_freeze_thaw (
    evt_block_date DATE NOT NULL,
    evt_block_time VARCHAR NOT NULL,  -- raw CSV text; see module docstring
    evt_tx_hash VARCHAR(66) NOT NULL,
    account VARCHAR(42) NOT NULL,
    amount_wei HUGEINT,
    event_type VARCHAR NOT NULL
      CHECK (event_type IN ('frozen', 'thawed', 'burnedfrozen')),
    evt_block_number UBIGINT NOT NULL,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (evt_tx_hash, event_type)
)
"""

# ``_csv_row_idx`` preserves the source-CSV row order — the Dune export's
# native ordering cannot be reproduced from the data columns alone (tie-
# breaks are not a monotone function of any single column). See module
# docstring.
_DDL_ONCHAIN_COPM_TOP100_EDGES: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_copm_transfers_top100_edges (
    from_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    n_transfers UBIGINT NOT NULL,
    total_value_wei HUGEINT NOT NULL,
    first_time VARCHAR NOT NULL,  -- raw CSV text; see module docstring
    last_time VARCHAR NOT NULL,   -- raw CSV text; see module docstring
    _csv_row_idx UBIGINT NOT NULL,  -- stable CSV row order; see module docstring
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (from_address, to_address),
    UNIQUE (_csv_row_idx)
)
"""

_DDL_ONCHAIN_COPM_DAILY_TRANSFERS: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_copm_daily_transfers (
    evt_block_date DATE NOT NULL PRIMARY KEY,
    n_transfers UBIGINT NOT NULL,
    n_tx UBIGINT NOT NULL,
    n_distinct_from UBIGINT NOT NULL,
    n_distinct_to UBIGINT NOT NULL,
    total_value_wei HUGEINT NOT NULL,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_DDL_ONCHAIN_COPM_ADDRESS_ACTIVITY: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_copm_address_activity_top400 (
    address VARCHAR(42) NOT NULL PRIMARY KEY,
    n_inbound UBIGINT NOT NULL,
    inbound_wei HUGEINT NOT NULL,
    n_outbound UBIGINT NOT NULL,
    outbound_wei HUGEINT NOT NULL,
    _csv_row_idx UBIGINT NOT NULL,  -- stable CSV row order; see module docstring
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    UNIQUE (_csv_row_idx)
)
"""

# ``bucket`` is stored as VARCHAR to preserve the source-CSV lexical
# ordering (``1, 10, 11, 12, ..., 2, 20, ...``). Storing as SMALLINT would
# sort numerically and break the byte-exact CSV-vs-DB checksum.
_DDL_ONCHAIN_COPM_TIME_PATTERNS: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_copm_time_patterns (
    kind VARCHAR NOT NULL
      CHECK (kind IN (
        'mints_dom', 'mints_dow',
        'transfers_dom', 'transfers_dow', 'transfers_month'
      )),
    bucket VARCHAR NOT NULL,
    n UBIGINT NOT NULL,
    wei HUGEINT NOT NULL,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (kind, bucket)
)
"""

# Task 11.A Rev-3.1 daily panel — COPM + cCOP flows in USD. ``ccop_*`` columns
# are NULL by contract before 2024-10-31 (pre-cCOP-launch window).
# USD columns stored as VARCHAR to preserve the exact 6-decimal CSV text
# (``0.000000`` vs DuckDB-DOUBLE's ``0.0``); see module docstring.
_DDL_ONCHAIN_COPM_CCOP_DAILY_FLOW: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_copm_ccop_daily_flow (
    date DATE NOT NULL PRIMARY KEY,
    copm_mint_usd VARCHAR NOT NULL,
    copm_burn_usd VARCHAR NOT NULL,
    copm_unique_minters UINTEGER NOT NULL,
    ccop_usdt_inflow_usd VARCHAR,
    ccop_usdt_outflow_usd VARCHAR,
    ccop_unique_senders UINTEGER,
    source_query_ids VARCHAR,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

# Task 11.N — weekly X_d surrogate panel (net primary issuance USD).
# ``value_usd`` preserved as VARCHAR to keep 6-decimal text exact (same
# rationale as ``onchain_copm_ccop_daily_flow``).  ``proxy_kind`` carries
# the ``X_D_INSUFFICIENT_DATA`` escalation tag committed in the
# design memo `contracts/.scratch/2026-04-24-xd-filter-design-memo.md`
# so every consumer sees the surrogate flag inline.
_DDL_ONCHAIN_XD_WEEKLY: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_xd_weekly (
    week_start DATE NOT NULL PRIMARY KEY,  -- Friday anchor
    value_usd VARCHAR NOT NULL,
    is_partial_week BOOLEAN NOT NULL,
    proxy_kind VARCHAR NOT NULL
      CHECK (proxy_kind = 'net_primary_issuance_usd'),
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
)
"""

_ONCHAIN_DDL: Final[tuple[str, ...]] = (
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
)


# ── Public API ───────────────────────────────────────────────────────────────


def init_db(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all raw tables if they don't exist. Idempotent."""
    for ddl in _ALL_DDL:
        conn.execute(ddl)
    for ddl in _ONCHAIN_DDL:
        conn.execute(ddl)
