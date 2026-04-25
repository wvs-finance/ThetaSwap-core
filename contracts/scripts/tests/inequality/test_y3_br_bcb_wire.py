"""TDD test suite for Rev-5.3.2 Task 11.N.2.BR-bcb-fetcher.

Plan:        contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md
             §Task 11.N.2.BR-bcb-fetcher (Rev-5.3.2 CORRECTIONS block)
Design doc:  contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md
             §3 (sources), §4 (60/25/15 weights), §8 (I/O contract), §10 row 2
             (headline-broadcast substitution)
Sibling:     Task 11.N.2.CO-dane-wire (commit f7b03caac) — the established
             CO-DANE-via-DuckDB pattern is mirrored here for BR-BCB-via-DuckDB
             with the additional cumulative-index materialization (BCB SGS/433
             returns variation %, not levels).

Public API exercised:

* ``scripts.econ_schema.migrate_bcb_ipca_monthly(conn)``
    NEW additive schema migration. Idempotent. Adds the ``bcb_ipca_monthly``
    raw table (date / ipca_pct_change / ipca_index_cumulative / _ingested_at).
* ``scripts.econ_schema.EXPECTED_TABLES``
    EXTENDED with ``"bcb_ipca_monthly"``.
* ``scripts.econ_pipeline.ingest_bcb_ipca_monthly(conn, start, end)``
    NEW ingest function: HTTP GET against the BCB SGS direct API series 433,
    parses dd/mm/yyyy + decimal-string variation %, materializes the
    cumulative index (I_0 = 100 at the earliest observation in the API
    response window), and idempotent-UPSERTs into ``bcb_ipca_monthly``.
* ``scripts.econ_query_api.load_bcb_ipca_monthly(conn, start, end)``
    NEW frozen-dataclass reader. Mirrors ``load_dane_ipc_monthly``.
* ``scripts.econ_query_api.BcbIpcaMonthly``
    NEW frozen+slots dataclass: ``date``, ``ipca_pct_change``,
    ``ipca_index_cumulative``.
* ``scripts.y3_data_fetchers.fetch_country_wc_cpi_components(country, start,
    end, conn=...)``
    EXTENDED dispatch: ``country == "BR"`` AND ``conn`` provided → routes to
    a new internal ``_fetch_bcb_headline_broadcast`` that consumes
    ``bcb_ipca_monthly`` via the canonical reader. ``country == "BR"`` AND
    ``conn`` is None → preserved IMF-IFS path (sensitivity comparator).

Strict TDD (per ``feedback_strict_tdd``): every test below MUST fail on
ImportError or AssertionError BEFORE the implementation lands.
Real-data integration round-trips the BCB SGS direct API endpoint per
``feedback_real_data_over_mocks`` — no fetch mocks for happy-path coverage.

File scope (per ``feedback_agent_scope``):

* contracts/scripts/econ_schema.py        — new migrate fn + EXPECTED_TABLES
* contracts/scripts/econ_pipeline.py      — new ingest_bcb_ipca_monthly
* contracts/scripts/econ_query_api.py     — new BcbIpcaMonthly + load_*
* contracts/scripts/y3_data_fetchers.py   — BR-conn dispatch + helper
"""
from __future__ import annotations

import dataclasses
import math
from datetime import date
from pathlib import Path
from typing import Final

import duckdb
import pytest


# Canonical DB path resolved from this test file's location.
_CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[3]
_STRUCTURAL_ECON_DB: Final[Path] = (
    _CONTRACTS_DIR / "data" / "structural_econ.duckdb"
)


def _open_canonical_readwrite() -> duckdb.DuckDBPyConnection:
    """Helper: open the canonical structural_econ.duckdb read-write.

    Skips the test if the file is missing. Caller is responsible for
    closing. Used by ingest tests that mutate the canonical table. The
    ingest is idempotent (INSERT OR REPLACE), so re-runs are safe and
    leave the canonical row set byte-exact.
    """
    if not _STRUCTURAL_ECON_DB.is_file():
        pytest.skip(f"structural_econ.duckdb missing at {_STRUCTURAL_ECON_DB}")
    return duckdb.connect(str(_STRUCTURAL_ECON_DB), read_only=False)


def _open_canonical_readonly() -> duckdb.DuckDBPyConnection:
    """Helper: open the canonical structural_econ.duckdb read-only.

    Skips if missing. Used for reader tests that don't mutate.
    """
    if not _STRUCTURAL_ECON_DB.is_file():
        pytest.skip(f"structural_econ.duckdb missing at {_STRUCTURAL_ECON_DB}")
    return duckdb.connect(str(_STRUCTURAL_ECON_DB), read_only=True)


def _open_inmemory() -> duckdb.DuckDBPyConnection:
    """Open an in-memory DuckDB for schema-migration unit tests."""
    return duckdb.connect(":memory:")


# ─────────────────────────────────────────────────────────────────────────
# Step A — Schema migration: bcb_ipca_monthly table
# ─────────────────────────────────────────────────────────────────────────


def test_expected_tables_includes_bcb_ipca_monthly() -> None:
    """``EXPECTED_TABLES`` is extended with ``bcb_ipca_monthly``.

    Mirrors the schema-discipline pattern: every raw table has a
    membership entry in ``EXPECTED_TABLES`` so the orchestrator validation
    pass catches accidental renames or omissions.
    """
    from scripts.econ_schema import EXPECTED_TABLES

    assert "bcb_ipca_monthly" in EXPECTED_TABLES


def test_migrate_bcb_ipca_monthly_creates_table_idempotent() -> None:
    """``migrate_bcb_ipca_monthly`` creates the table and is idempotent.

    Step Atomicity Protocol (matches ``migrate_onchain_y3_weekly``
    precedent): the migration is exercised against in-memory DuckDB so
    canonical state is untouched by this test. Returns True on first
    call (created), False on second call (already exists).
    """
    from scripts.econ_schema import migrate_bcb_ipca_monthly

    conn = _open_inmemory()
    try:
        first = migrate_bcb_ipca_monthly(conn)
        second = migrate_bcb_ipca_monthly(conn)
    finally:
        conn.close()

    assert first is True, "first call should report table created"
    assert second is False, "second call must be idempotent (table already exists)"


def test_bcb_ipca_monthly_schema_columns() -> None:
    """The ``bcb_ipca_monthly`` table carries the documented columns.

    Column contract:
        date                       DATE PRIMARY KEY
        ipca_pct_change            DOUBLE  (raw monthly variation %; what
                                            the BCB SGS/433 endpoint emits
                                            verbatim — no cumulative-index
                                            transform)
        ipca_index_cumulative      DOUBLE  (materialized cumulative index,
                                            I_0 = 100 at the earliest
                                            observation in the API window)
        _ingested_at               TIMESTAMP (audit metadata)
    """
    from scripts.econ_schema import migrate_bcb_ipca_monthly

    conn = _open_inmemory()
    try:
        migrate_bcb_ipca_monthly(conn)
        cols = {
            r[0]: r[1]
            for r in conn.execute("DESCRIBE bcb_ipca_monthly").fetchall()
        }
    finally:
        conn.close()

    assert set(cols.keys()) >= {
        "date",
        "ipca_pct_change",
        "ipca_index_cumulative",
        "_ingested_at",
    }
    assert cols["date"] == "DATE"
    assert cols["ipca_pct_change"] == "DOUBLE"
    assert cols["ipca_index_cumulative"] == "DOUBLE"
    assert cols["_ingested_at"].startswith("TIMESTAMP")


# ─────────────────────────────────────────────────────────────────────────
# Step B — Ingest: real-data round-trip against BCB SGS direct API
# ─────────────────────────────────────────────────────────────────────────


def test_ingest_bcb_ipca_monthly_real_data_round_trip() -> None:
    """``ingest_bcb_ipca_monthly`` writes ≥ 12 rows with cutoff ≥ 2026-02-01.

    Per ``feedback_real_data_over_mocks``: zero HTTP mocks. The BCB SGS
    direct API is the canonical source under Rev-5.3.2 BR; cutoff ≥
    2026-02-01 is the staleness gate (≤ 2-month staleness at authoring
    date 2026-04-25).

    The ingest is idempotent (INSERT OR REPLACE on PK ``date``); a
    second call on the same window leaves the table byte-exact. We
    therefore run against the canonical DB without rollback — re-runs
    are safe.
    """
    from scripts.econ_pipeline import ingest_bcb_ipca_monthly

    # Tight 2024-01-01 → 2026-04-24 window — gives us > 12 monthly rows
    # and lands the most recent observation for the staleness check.
    conn = _open_canonical_readwrite()
    try:
        result = ingest_bcb_ipca_monthly(
            conn,
            start=date(2024, 1, 1),
            end=date(2026, 4, 24),
        )
        # Verify rows landed.
        cnt = conn.execute(
            "SELECT COUNT(*) FROM bcb_ipca_monthly "
            "WHERE date >= '2024-01-01' AND date <= '2026-04-24'"
        ).fetchone()[0]
        max_date = conn.execute(
            "SELECT MAX(date) FROM bcb_ipca_monthly"
        ).fetchone()[0]
    finally:
        conn.close()

    assert isinstance(result, dict)
    assert result.get("rows_written", 0) >= 12, (
        f"expected ≥12 rows, got {result}"
    )
    assert cnt >= 12, f"DB row count {cnt} < 12"
    assert max_date >= date(2026, 2, 1), (
        f"BCB IPCA cutoff {max_date} < 2026-02-01 — staleness gate"
    )


def test_ingest_bcb_ipca_monthly_idempotent_replays_byte_exact() -> None:
    """Second call leaves table state byte-exact (no row count drift)."""
    from scripts.econ_pipeline import ingest_bcb_ipca_monthly

    conn = _open_canonical_readwrite()
    try:
        # First ingest (or re-ingest if prior test ran first)
        ingest_bcb_ipca_monthly(conn, start=date(2026, 1, 1), end=date(2026, 4, 24))
        n1 = conn.execute("SELECT COUNT(*) FROM bcb_ipca_monthly").fetchone()[0]
        # Second ingest of same window
        ingest_bcb_ipca_monthly(conn, start=date(2026, 1, 1), end=date(2026, 4, 24))
        n2 = conn.execute("SELECT COUNT(*) FROM bcb_ipca_monthly").fetchone()[0]
    finally:
        conn.close()

    assert n1 == n2, f"idempotency violation: {n1} → {n2} rows"


def test_cumulative_index_dlog_matches_pct_change_within_tolerance() -> None:
    """Δlog(cumulative_index) ≈ ln(1 + pct_change/100) within float tolerance.

    Anti-fishing guard (per task body): the cumulative index is a monotone
    transformation of the variation series — it preserves the Δlog signal
    that drives the per-country differential downstream. No extra
    transformations (smoothing, seasonal adjustment) are introduced.
    """
    from scripts.econ_pipeline import ingest_bcb_ipca_monthly

    conn = _open_canonical_readwrite()
    try:
        ingest_bcb_ipca_monthly(
            conn, start=date(2024, 1, 1), end=date(2026, 4, 24)
        )
        rows = conn.execute(
            "SELECT date, ipca_pct_change, ipca_index_cumulative "
            "FROM bcb_ipca_monthly "
            "WHERE date >= '2024-01-01' AND date <= '2026-04-24' "
            "ORDER BY date"
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) >= 2
    # Skip first row (it's the base, no Δ to compare).
    for prev, curr in zip(rows[:-1], rows[1:], strict=True):
        prev_idx = prev[2]
        curr_idx = curr[2]
        curr_pct = curr[1]
        # Δlog from cumulative index
        dlog_idx = math.log(curr_idx) - math.log(prev_idx)
        # Δlog from raw variation: ln(1 + pct/100)
        dlog_pct = math.log(1.0 + curr_pct / 100.0)
        assert abs(dlog_idx - dlog_pct) < 1e-9, (
            f"Δlog mismatch at {curr[0]}: index={dlog_idx}, pct={dlog_pct}"
        )


# ─────────────────────────────────────────────────────────────────────────
# Step C — Reader: load_bcb_ipca_monthly returns frozen dataclass tuple
# ─────────────────────────────────────────────────────────────────────────


def test_load_bcb_ipca_monthly_returns_tuple_of_frozen_dataclasses() -> None:
    """``load_bcb_ipca_monthly`` returns ``tuple[BcbIpcaMonthly, ...]``.

    Mirrors ``load_dane_ipc_monthly`` from the CO sibling task.
    """
    from scripts.econ_query_api import BcbIpcaMonthly, load_bcb_ipca_monthly
    from scripts.econ_pipeline import ingest_bcb_ipca_monthly

    # Ensure table is populated.
    rw = _open_canonical_readwrite()
    try:
        ingest_bcb_ipca_monthly(rw, start=date(2024, 1, 1), end=date(2026, 4, 24))
    finally:
        rw.close()

    conn = _open_canonical_readonly()
    try:
        rows = load_bcb_ipca_monthly(conn)
    finally:
        conn.close()

    assert isinstance(rows, tuple)
    assert len(rows) > 0
    r0 = rows[0]
    assert isinstance(r0, BcbIpcaMonthly)
    assert dataclasses.is_dataclass(r0)
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        r0.date = date(1900, 1, 1)  # type: ignore[misc]


def test_load_bcb_ipca_monthly_schema_fields() -> None:
    """``BcbIpcaMonthly`` exposes ``date``, ``ipca_pct_change``,
    ``ipca_index_cumulative``."""
    from scripts.econ_query_api import BcbIpcaMonthly, load_bcb_ipca_monthly
    from scripts.econ_pipeline import ingest_bcb_ipca_monthly

    rw = _open_canonical_readwrite()
    try:
        ingest_bcb_ipca_monthly(rw, start=date(2026, 1, 1), end=date(2026, 4, 24))
    finally:
        rw.close()

    conn = _open_canonical_readonly()
    try:
        rows = load_bcb_ipca_monthly(conn, start=date(2026, 1, 1))
    finally:
        conn.close()

    fields = {f.name for f in dataclasses.fields(BcbIpcaMonthly)}
    assert "date" in fields
    assert "ipca_pct_change" in fields
    assert "ipca_index_cumulative" in fields
    assert len(rows) >= 1
    s = rows[0]
    assert isinstance(s.date, date)
    assert isinstance(s.ipca_pct_change, float)
    assert isinstance(s.ipca_index_cumulative, float)


def test_load_bcb_ipca_monthly_date_filter_inclusive() -> None:
    """``[start, end]`` inclusive bounds match project ``_date_filter`` semantics."""
    from scripts.econ_query_api import load_bcb_ipca_monthly
    from scripts.econ_pipeline import ingest_bcb_ipca_monthly

    rw = _open_canonical_readwrite()
    try:
        ingest_bcb_ipca_monthly(rw, start=date(2024, 1, 1), end=date(2026, 4, 24))
    finally:
        rw.close()

    conn = _open_canonical_readonly()
    try:
        # 2026-01-01 → 2026-03-31 should pull exactly 2026-01, 02, 03
        rows = load_bcb_ipca_monthly(
            conn, start=date(2026, 1, 1), end=date(2026, 3, 31)
        )
    finally:
        conn.close()

    dates = [r.date for r in rows]
    assert date(2026, 1, 1) in dates
    assert date(2026, 2, 1) in dates
    assert date(2026, 3, 1) in dates
    # Ascending order.
    assert dates == sorted(dates)


# ─────────────────────────────────────────────────────────────────────────
# Step D — Fetcher dispatch: BR + conn → BCB; BR + no conn → IMF IFS
# ─────────────────────────────────────────────────────────────────────────


def test_fetch_country_wc_cpi_components_br_via_bcb_returns_4_components() -> None:
    """BR + ``conn`` provided → BCB-broadcast 4-component DataFrame.

    Per design doc §10 row 2, BCB IPCA is headline-only at this monthly
    cadence; the cumulative index is broadcast across all four
    component slots. The consumer contract is preserved byte-exact:
    columns ``date``, ``food_cpi``, ``energy_cpi``, ``housing_cpi``,
    ``transport_cpi``.
    """
    from scripts.y3_data_fetchers import fetch_country_wc_cpi_components
    from scripts.econ_pipeline import ingest_bcb_ipca_monthly

    rw = _open_canonical_readwrite()
    try:
        ingest_bcb_ipca_monthly(rw, start=date(2024, 1, 1), end=date(2026, 4, 24))
    finally:
        rw.close()

    conn = _open_canonical_readonly()
    try:
        df = fetch_country_wc_cpi_components(
            "BR",
            date(2024, 1, 1),
            date(2026, 4, 24),
            conn=conn,
        )
    finally:
        conn.close()

    expected_cols = {"date", "food_cpi", "energy_cpi", "housing_cpi", "transport_cpi"}
    assert expected_cols.issubset(set(df.columns))
    assert len(df) > 0
    # Headline-broadcast invariant.
    sample = df.iloc[-1]
    assert sample["food_cpi"] == sample["energy_cpi"]
    assert sample["energy_cpi"] == sample["housing_cpi"]
    assert sample["housing_cpi"] == sample["transport_cpi"]


def test_fetch_country_wc_cpi_components_br_via_bcb_cutoff_ge_2026_02_01() -> None:
    """Smoke-test cutoff: BR via BCB returns max date ≥ 2026-02-01."""
    from scripts.y3_data_fetchers import fetch_country_wc_cpi_components
    from scripts.econ_pipeline import ingest_bcb_ipca_monthly

    rw = _open_canonical_readwrite()
    try:
        ingest_bcb_ipca_monthly(rw, start=date(2024, 1, 1), end=date(2026, 4, 24))
    finally:
        rw.close()

    conn = _open_canonical_readonly()
    try:
        df = fetch_country_wc_cpi_components(
            "BR",
            date(2024, 1, 1),
            date(2026, 4, 24),
            conn=conn,
        )
    finally:
        conn.close()

    max_d = df["date"].max()
    if hasattr(max_d, "date"):
        max_d = max_d.date()
    assert max_d >= date(2026, 2, 1), (
        f"BR BCB-broadcast cutoff {max_d} < 2026-02-01"
    )


def test_fetch_country_wc_cpi_components_br_bcb_values_match_table() -> None:
    """Round-trip integrity: fetcher ``food_cpi`` equals ``ipca_index_cumulative``."""
    from scripts.econ_query_api import load_bcb_ipca_monthly
    from scripts.y3_data_fetchers import fetch_country_wc_cpi_components
    from scripts.econ_pipeline import ingest_bcb_ipca_monthly

    rw = _open_canonical_readwrite()
    try:
        ingest_bcb_ipca_monthly(rw, start=date(2024, 1, 1), end=date(2026, 4, 24))
    finally:
        rw.close()

    conn = _open_canonical_readonly()
    try:
        bcb_rows = load_bcb_ipca_monthly(
            conn, start=date(2025, 10, 1), end=date(2026, 3, 31)
        )
        df = fetch_country_wc_cpi_components(
            "BR",
            date(2025, 10, 1),
            date(2026, 3, 31),
            conn=conn,
        )
    finally:
        conn.close()

    bcb_map = {r.date: r.ipca_index_cumulative for r in bcb_rows}
    df_dates = df["date"].tolist()
    fetcher_map: dict[date, float] = {}
    for d, v in zip(df_dates, df["food_cpi"].tolist(), strict=True):
        if hasattr(d, "date"):
            d = d.date()
        fetcher_map[d] = float(v)

    assert set(fetcher_map.keys()) == set(bcb_map.keys())
    for d, expected in bcb_map.items():
        got = fetcher_map[d]
        assert abs(got - expected) < 1e-12, (
            f"BCB round-trip mismatch at {d}: fetcher={got}, bcb={expected}"
        )


def test_fetch_country_wc_cpi_components_br_without_conn_uses_imf_path() -> None:
    """BR + no ``conn`` → IMF-IFS path (sensitivity-comparator preservation).

    No external HTTP call is made — we monkey-patch the IMF-IFS fetcher
    to a sentinel and assert the dispatch hits it. This locks in the
    contract: the new BCB path is ONLY active when ``conn`` is
    explicitly provided. Mirrors the CO sibling-test pattern.
    """
    import pandas as pd

    from scripts import y3_data_fetchers

    sentinel: dict[str, bool] = {"hit": False}

    def _fake_imf(country: str, start: date, end: date) -> pd.DataFrame:
        sentinel["hit"] = True
        return pd.DataFrame(
            {
                "date": [date(2025, 1, 1)],
                "food_cpi": [100.0],
                "energy_cpi": [100.0],
                "housing_cpi": [100.0],
                "transport_cpi": [100.0],
            }
        )

    original = y3_data_fetchers._fetch_imf_ifs_headline_broadcast
    try:
        y3_data_fetchers._fetch_imf_ifs_headline_broadcast = _fake_imf  # type: ignore[assignment]
        out = y3_data_fetchers.fetch_country_wc_cpi_components(
            "BR", date(2025, 1, 1), date(2025, 12, 31)
        )
    finally:
        y3_data_fetchers._fetch_imf_ifs_headline_broadcast = original  # type: ignore[assignment]

    assert sentinel["hit"], (
        "BR without conn must still route through IMF-IFS path "
        "(sensitivity-comparator preservation)"
    )
    assert len(out) == 1


def test_fetch_imf_ifs_headline_broadcast_signature_preserved() -> None:
    """The IMF-IFS path is preserved byte-exact (signature locked).

    Acceptance criterion: ``_fetch_imf_ifs_headline_broadcast`` retains
    its (country, start, end) signature for both the BR and KE
    sensitivity-comparator paths.
    """
    import inspect

    from scripts.y3_data_fetchers import _fetch_imf_ifs_headline_broadcast

    assert callable(_fetch_imf_ifs_headline_broadcast)
    sig = inspect.signature(_fetch_imf_ifs_headline_broadcast)
    assert list(sig.parameters.keys()) == ["country", "start", "end"]


# ─────────────────────────────────────────────────────────────────────────
# Step E — Cross-country safety: CO with conn still routes to DANE; KE raises
# ─────────────────────────────────────────────────────────────────────────


def test_co_with_conn_still_routes_to_dane() -> None:
    """CO + conn must still route to DANE — BR change does NOT regress CO."""
    from scripts import y3_data_fetchers

    sentinel: dict[str, bool] = {"dane_hit": False}

    import pandas as pd

    def _fake_dane(conn, start: date, end: date) -> pd.DataFrame:
        sentinel["dane_hit"] = True
        return pd.DataFrame(
            {
                "date": [date(2025, 1, 1)],
                "food_cpi": [100.0],
                "energy_cpi": [100.0],
                "housing_cpi": [100.0],
                "transport_cpi": [100.0],
            }
        )

    original = y3_data_fetchers._fetch_dane_headline_broadcast
    try:
        y3_data_fetchers._fetch_dane_headline_broadcast = _fake_dane  # type: ignore[assignment]
        # Pass a sentinel non-None conn (the fake doesn't use it).
        out = y3_data_fetchers.fetch_country_wc_cpi_components(
            "CO", date(2025, 1, 1), date(2025, 12, 31), conn=object()
        )
    finally:
        y3_data_fetchers._fetch_dane_headline_broadcast = original  # type: ignore[assignment]

    assert sentinel["dane_hit"], "CO with conn must still route to DANE path"
    assert len(out) == 1


def test_ke_still_routes_to_imf_ifs_path() -> None:
    """KE + conn provided → still IMF-IFS path (KE-fallback unchanged)."""
    import pandas as pd

    from scripts import y3_data_fetchers

    sentinel: dict[str, bool] = {"imf_hit": False}

    def _fake_imf(country: str, start: date, end: date) -> pd.DataFrame:
        sentinel["imf_hit"] = True
        return pd.DataFrame(
            {
                "date": [date(2025, 1, 1)],
                "food_cpi": [100.0],
                "energy_cpi": [100.0],
                "housing_cpi": [100.0],
                "transport_cpi": [100.0],
            }
        )

    original = y3_data_fetchers._fetch_imf_ifs_headline_broadcast
    try:
        y3_data_fetchers._fetch_imf_ifs_headline_broadcast = _fake_imf  # type: ignore[assignment]
        # Even with conn provided, KE goes to IMF-IFS — no BCB BR-only path leak.
        out = y3_data_fetchers.fetch_country_wc_cpi_components(
            "KE", date(2025, 1, 1), date(2025, 12, 31), conn=object()
        )
    finally:
        y3_data_fetchers._fetch_imf_ifs_headline_broadcast = original  # type: ignore[assignment]

    assert sentinel["imf_hit"], "KE with conn must still route to IMF-IFS"
    assert len(out) == 1
