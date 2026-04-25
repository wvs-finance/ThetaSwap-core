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
    # ── Task 11.N.1: full COPM transfers (Rev-5.2.1) ────────────────────
    "onchain_copm_transfers",
    # ── Task 11.N.2d (Rev-5.3.1): Y₃ inequality-differential weekly panel ─
    "onchain_y3_weekly",
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
#
# Rev-5.2.1 Task 11.N.1 Step 0 (BLOCKER CR-B1 / RC-B1) — the CHECK
# constraint was pinned singleton ``proxy_kind = 'net_primary_issuance_usd'``
# and the PK was single-column ``week_start``. That schema could not
# host the distribution-channel X_d (``b2b_to_b2c_net_flow_usd``)
# alongside the surrogate. The migration helper
# ``scripts.econ_pipeline.migrate_onchain_xd_weekly_allow_both_channels``
# rebuilds legacy tables into this shape; this DDL is the target state
# for fresh DBs.
_DDL_ONCHAIN_XD_WEEKLY: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_xd_weekly (
    week_start DATE NOT NULL,  -- Friday anchor
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

# Rev-5.2.1 Task 11.N.1 (BLOCKER CR-B2) — full COPM transfers. This is
# a NEW table distinct from ``onchain_copm_transfers_sample``, which
# continues to live on unchanged as a historical-sample audit pointer.
# The full dataset is ingested via :func:`econ_pipeline.ingest_onchain_copm_transfers`
# after the RPC backfill populates ``contracts/data/copm_per_tx/copm_transfers.csv``.
# Same column set as the sample table; no ``_csv_row_idx`` needed
# because the RPC-ordered backfill is monotone on
# ``(evt_block_number, logIndex)`` — we instead include ``log_index`` as
# the event-level tie-break so the PK covers the natural on-chain
# identity of a Transfer event.
_DDL_ONCHAIN_COPM_TRANSFERS: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_copm_transfers (
    evt_block_date DATE NOT NULL,
    evt_block_time VARCHAR NOT NULL,  -- raw RPC-derived ISO text
    evt_tx_hash VARCHAR(66) NOT NULL,
    from_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    value_wei HUGEINT NOT NULL,
    evt_block_number UBIGINT NOT NULL,
    log_index UBIGINT NOT NULL,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (evt_tx_hash, log_index)
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
    _DDL_ONCHAIN_COPM_TRANSFERS,
)


# ── Task 11.N.2b.1: Carbon-basket schema migration ──────────────────────────
#
# The Rev-5.2.1 ``onchain_xd_weekly`` CHECK constraint admits exactly two
# ``proxy_kind`` values: ``'net_primary_issuance_usd'`` (supply channel,
# Task 11.N) and ``'b2b_to_b2c_net_flow_usd'`` (distribution channel,
# Task 11.N.1b). Task 11.N.2b.1 (Rev 5.3) extends the admitted set with
# eight new Carbon-basket values per plan §937:
#
#   - 'carbon_basket_user_volume_usd'             (basket-aggregate primary)
#   - 'carbon_basket_arb_volume_usd'              (Arb Fast Lane diagnostic)
#   - 'carbon_per_currency_copm_volume_usd'       (per-currency PCA cross-val)
#   - 'carbon_per_currency_usdm_volume_usd'
#   - 'carbon_per_currency_eurm_volume_usd'
#   - 'carbon_per_currency_brlm_volume_usd'
#   - 'carbon_per_currency_kesm_volume_usd'
#   - 'carbon_per_currency_xofm_volume_usd'
#
# The migration also creates two new per-event tables for Carbon DeFi
# Celo events:
#
#   - ``onchain_carbon_tokenstraded`` — from Dune
#     ``carbon_defi_celo.carboncontroller_evt_tokenstraded``
#   - ``onchain_carbon_arbitrages``    — from Dune
#     ``carbon_defi_celo.bancorarbitrage_evt_arbitrageexecuted``
#
# DDL DEVIATION (gate-decision memo §3.2): the plan-§927 pre-commitment
# treated the BancorArbitrage event as scalar (single ``sourceToken``,
# ``sourceAmount``, ``tokenPath``). Dune-MCP LIMIT-100 probe (query
# ``7371828``) shows the event is multi-hop with array-typed source/path
# fields:
#
#   sourceTokens     array(varbinary)
#   sourceAmounts    array(uint256)
#   tokenPath        array(varbinary)
#   protocolAmounts  array(uint256)
#   rewardAmounts    array(uint256)
#   platformIds      array(integer)
#
# These six array fields are stored as JSON-encoded VARCHAR following the
# 11.M.5 commit ``af98bb659`` text-preserving precedent for text-shaped
# event data. uint256 array fields cannot be stored as ``HUGEINT[]``
# without overflow risk on whale trades — VARCHAR JSON is the safe
# canonical-text round-trip representation.
#
# uint256 scalar fields in ``onchain_carbon_tokenstraded`` (sourceAmount,
# targetAmount, tradingFeeAmount) use HUGEINT per the same 11.M.5
# precedent. HUGEINT max (2^127 − 1 ≈ 1.7e38) > any observed Carbon trade
# magnitude in the LIMIT-100 probe (max sourceAmount = 9.43e18, well
# within range). Production ingest in 11.N.2b.2 must guard against
# uint256-max overflow on whale trades (memo §3.1).
#
# Address fields (``sourceToken``, ``targetToken``, ``trader``,
# ``evt_tx_from``, ``contract_address``, ``caller``) use VARBINARY (no
# length attribute on DuckDB; Dune decoded namespace returns 20-byte
# addresses verbatim).
#
# Step Atomicity Protocol (CR-P5 / PM-P1): this migration is committed
# to source code in Task 11.N.2b.1 but is NOT executed against the
# canonical ``contracts/data/structural_econ.duckdb`` until Task
# 11.N.2b.2 Step 5 (atomic-commit-after-population). The Task 11.N.2b.1
# tests run against an in-memory DuckDB only.

_DDL_ONCHAIN_XD_WEEKLY_CARBON: Final[str] = """
CREATE TABLE onchain_xd_weekly_new (
    week_start DATE NOT NULL,
    value_usd VARCHAR NOT NULL,
    is_partial_week BOOLEAN NOT NULL,
    proxy_kind VARCHAR NOT NULL
      CHECK (proxy_kind IN (
        'net_primary_issuance_usd',
        'b2b_to_b2c_net_flow_usd',
        'carbon_basket_user_volume_usd',
        'carbon_basket_arb_volume_usd',
        'carbon_per_currency_copm_volume_usd',
        'carbon_per_currency_usdm_volume_usd',
        'carbon_per_currency_eurm_volume_usd',
        'carbon_per_currency_brlm_volume_usd',
        'carbon_per_currency_kesm_volume_usd',
        'carbon_per_currency_xofm_volume_usd'
      )),
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (week_start, proxy_kind)
)
"""

# DuckDB does not track a CHECK clause's literal text in a way that
# survives table rebuilds without quoting drift, so the migration
# detects the post-state by checking for the presence of one of the new
# Carbon-basket values in the existing CHECK clause text.
_CARBON_PROXY_KIND_SENTINEL: Final[str] = "carbon_basket_user_volume_usd"

_DDL_ONCHAIN_CARBON_TOKENSTRADED: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_carbon_tokenstraded (
    contract_address VARBINARY NOT NULL,
    evt_tx_hash VARCHAR(66) NOT NULL,
    evt_index BIGINT NOT NULL,
    evt_block_number BIGINT NOT NULL,
    evt_block_time TIMESTAMP NOT NULL,
    evt_block_date DATE NOT NULL,
    evt_tx_from VARBINARY,
    trader VARBINARY NOT NULL,
    sourceToken VARBINARY NOT NULL,
    targetToken VARBINARY NOT NULL,
    sourceAmount HUGEINT NOT NULL,
    targetAmount HUGEINT NOT NULL,
    tradingFeeAmount HUGEINT NOT NULL,
    byTargetAmount BOOLEAN NOT NULL,
    -- Populated by Python aggregation layer in Task 11.N.2b.2 Step 3.
    -- VARCHAR text-preserving per 11.M.5 commit `af98bb659`.
    source_amount_usd VARCHAR,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (evt_tx_hash, evt_index)
)
"""

_DDL_ONCHAIN_CARBON_ARBITRAGES: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_carbon_arbitrages (
    contract_address VARBINARY NOT NULL,
    evt_tx_hash VARCHAR(66) NOT NULL,
    evt_index BIGINT NOT NULL,
    evt_block_number BIGINT NOT NULL,
    evt_block_time TIMESTAMP NOT NULL,
    evt_block_date DATE NOT NULL,
    evt_tx_from VARBINARY,
    caller VARBINARY NOT NULL,
    -- Array-typed fields stored as JSON-encoded VARCHAR per
    -- gate-decision memo §3.2 DDL DEVIATION (plan-§927 scalar
    -- pre-commit superseded by probe-confirmed array semantics).
    platformIds VARCHAR NOT NULL,
    protocolAmounts VARCHAR NOT NULL,
    rewardAmounts VARCHAR NOT NULL,
    sourceAmounts VARCHAR NOT NULL,
    sourceTokens VARCHAR NOT NULL,
    tokenPath VARCHAR NOT NULL,
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (evt_tx_hash, evt_index)
)
"""


def migrate_onchain_xd_weekly_for_carbon(
    conn: duckdb.DuckDBPyConnection,
) -> bool:
    """Relax ``onchain_xd_weekly.proxy_kind`` CHECK + create Carbon tables.

    DuckDB cannot drop a column-level CHECK constraint in place — the
    migration uses the same shadow-table rebuild pattern as
    :func:`scripts.econ_pipeline.migrate_fred_daily_allow_dff` (commit
    ``a724252c6``). Steps:

      1. Detect post-state via ``duckdb_constraints()`` lookup; if the
         CHECK already includes ``'carbon_basket_user_volume_usd'``,
         return ``False`` (no-op idempotency).
      2. Create ``onchain_xd_weekly_new`` with the relaxed 10-value CHECK.
      3. Copy every row from the existing ``onchain_xd_weekly``.
      4. Drop the old table; rename the shadow.
      5. Create ``onchain_carbon_tokenstraded`` + ``onchain_carbon_arbitrages``
         (idempotent ``CREATE TABLE IF NOT EXISTS``).

    Returns ``True`` if a migration was performed, ``False`` if the
    table already permits the Carbon-basket proxy_kind values.

    Byte-exact preserving for pre-existing rows: every ``onchain_xd_weekly``
    row carrying ``'net_primary_issuance_usd'`` or ``'b2b_to_b2c_net_flow_usd'``
    survives the migration unchanged in week_start, value_usd,
    is_partial_week, proxy_kind, and _ingested_at columns.

    Step Atomicity Protocol (CR-P5 / PM-P1): callers MUST run this
    function against an in-memory or temporary DuckDB during Task
    11.N.2b.1; the canonical ``contracts/data/structural_econ.duckdb``
    is untouched until Task 11.N.2b.2 Step 5 atomic commit.
    """
    existing = conn.execute(
        "SELECT constraint_text FROM duckdb_constraints() "
        "WHERE table_name = 'onchain_xd_weekly' "
        "  AND constraint_type = 'CHECK'"
    ).fetchall()
    already_carbon = any(
        _CARBON_PROXY_KIND_SENTINEL in (row[0] or "") for row in existing
    )

    if not already_carbon:
        # Shadow-table rebuild for the relaxed CHECK.
        conn.execute(_DDL_ONCHAIN_XD_WEEKLY_CARBON)
        conn.execute(
            "INSERT INTO onchain_xd_weekly_new "
            "(week_start, value_usd, is_partial_week, proxy_kind, _ingested_at) "
            "SELECT week_start, value_usd, is_partial_week, proxy_kind, _ingested_at "
            "FROM onchain_xd_weekly"
        )
        conn.execute("DROP TABLE onchain_xd_weekly")
        conn.execute("ALTER TABLE onchain_xd_weekly_new RENAME TO onchain_xd_weekly")

    # Idempotent: ``CREATE TABLE IF NOT EXISTS`` is safe to run on
    # fresh + already-migrated DBs alike.
    conn.execute(_DDL_ONCHAIN_CARBON_TOKENSTRADED)
    conn.execute(_DDL_ONCHAIN_CARBON_ARBITRAGES)

    return not already_carbon


# ── Task 11.N.2d (Rev-5.3.1): Y₃ inequality-differential weekly panel ──────
#
# Additive migration. The new ``onchain_y3_weekly`` table persists the
# regional-pan-EM equal-weighted Y₃ aggregate computed by
# :mod:`scripts.y3_compute`. Composite primary key (week_start,
# source_methodology) so the same week can carry both the primary panel
# row (``source_methodology = 'y3_v1'``) and the sensitivity-panel row
# (``source_methodology = 'y3_v1_sensitivity'``, populated by Task
# 11.N.2d.1) without overlap-mutation.
#
# Per-country diff columns (copm_diff / brl_diff / kes_diff / eur_diff)
# are nullable so the 3-country fallback path (Kenya WC-CPI ETL fail
# per design doc §10 row 1) can persist a NULL kes_diff column under
# ``source_methodology = 'y3_v1_3country_kenya_unavailable'``.
#
# This DDL is purely additive — no existing tables touched; Rev-4
# ``decision_hash`` byte-exact preserved.

_DDL_ONCHAIN_Y3_WEEKLY: Final[str] = """
CREATE TABLE IF NOT EXISTS onchain_y3_weekly (
    week_start DATE NOT NULL,
    y3_value DOUBLE NOT NULL,
    copm_diff DOUBLE,
    brl_diff DOUBLE,
    kes_diff DOUBLE,
    eur_diff DOUBLE,
    source_methodology VARCHAR NOT NULL DEFAULT 'y3_v1',
    _ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (week_start, source_methodology)
)
"""


def migrate_onchain_y3_weekly(conn: duckdb.DuckDBPyConnection) -> bool:
    """Create the ``onchain_y3_weekly`` table. Idempotent.

    Returns ``True`` if the table was created on this call, ``False``
    if it already existed. Strictly additive — does not touch any
    other table.

    Step Atomicity Protocol (CR-P5 / PM-P1, propagated from Task
    11.N.2b.1 / 11.N.2b.2 / 11.N.2c): callers MUST run this function
    first against an in-memory or temporary DuckDB during Task 11.N.2d
    Step 7 schema-migration tests; the canonical
    ``contracts/data/structural_econ.duckdb`` is mutated only after the
    in-memory smoke probe succeeds (then via
    :func:`scripts.econ_pipeline.ingest_y3_weekly`).
    """
    existing = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    already = "onchain_y3_weekly" in existing
    conn.execute(_DDL_ONCHAIN_Y3_WEEKLY)
    return not already


# ── Public API ───────────────────────────────────────────────────────────────


def init_db(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all raw tables if they don't exist. Idempotent."""
    for ddl in _ALL_DDL:
        conn.execute(ddl)
    for ddl in _ONCHAIN_DDL:
        conn.execute(ddl)
    # Task 11.N.2d (Rev-5.3.1): additive Y₃ table.
    conn.execute(_DDL_ONCHAIN_Y3_WEEKLY)
