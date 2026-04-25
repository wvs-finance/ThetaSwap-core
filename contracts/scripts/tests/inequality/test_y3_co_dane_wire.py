"""TDD test suite for Rev-5.3.2 Task 11.N.2.CO-dane-wire.

Plan:        contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md
             §Task 11.N.2.CO-dane-wire (line 1864)
Design doc:  contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md
             §3 (sources), §4 (60/25/15 weights), §8 (I/O contract), §10 row 2
             (headline-broadcast substitution)
Predecessor: Task 11.N.2d (Rev-5.3.1 Y₃ panel) PASS at relaxed N_MIN=75
             (commit 7afcd2ad6).

Public API exercised:

* ``scripts.econ_query_api.load_dane_ipc_monthly(conn, start, end)``
    NEW frozen-dataclass reader for the existing-and-populated
    ``dane_ipc_monthly`` DuckDB table. Consume-only — no schema
    mutation, no re-ingestion.
* ``scripts.y3_data_fetchers.fetch_country_wc_cpi_components(country,
    start, end, conn=...)``
    EXTENDED with optional ``conn`` kwarg. When ``country == "CO"`` and
    ``conn`` is provided, the fetcher dispatches to a new internal
    helper ``_fetch_dane_headline_broadcast`` that round-trips DANE rows
    via ``load_dane_ipc_monthly``. The IMF-IFS path
    (``_fetch_imf_ifs_headline_broadcast``) is preserved as-is and is
    the active path when ``conn`` is None — that path is the
    Task 11.N.2d.1-reframe single-source-IMF-only sensitivity comparator.

Strict TDD (per ``feedback_strict_tdd``): every test below MUST fail on
ImportError or AssertionError before the wire-up lands. Real-data
integration round-trips canonical ``contracts/data/structural_econ.duckdb``
rows (per ``feedback_real_data_over_mocks``) — DANE table is already
populated; no fetch mocks anywhere.

File scope (per ``feedback_agent_scope``): writes to
``y3_data_fetchers.py`` and ``econ_query_api.py`` only; the
``dane_ipc_monthly`` table schema and rows are read-only.
"""
from __future__ import annotations

import dataclasses
from datetime import date
from pathlib import Path
from typing import Final

import duckdb
import pytest


# Canonical DB path resolved from this test file's location.
# scripts/tests/inequality/test_y3_co_dane_wire.py → parents[3] = contracts/.
_CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[3]
_STRUCTURAL_ECON_DB: Final[Path] = (
    _CONTRACTS_DIR / "data" / "structural_econ.duckdb"
)


def _open_canonical_readonly() -> duckdb.DuckDBPyConnection:
    """Helper: open the canonical structural_econ.duckdb read-only.

    Skips the test if the file is missing (CI-time guard for environments
    that haven't materialized the DB yet).
    """
    if not _STRUCTURAL_ECON_DB.is_file():
        pytest.skip(f"structural_econ.duckdb missing at {_STRUCTURAL_ECON_DB}")
    return duckdb.connect(str(_STRUCTURAL_ECON_DB), read_only=True)


# ─────────────────────────────────────────────────────────────────────────
# Step A — econ_query_api.load_dane_ipc_monthly: frozen-dataclass reader
# ─────────────────────────────────────────────────────────────────────────


def test_load_dane_ipc_monthly_returns_tuple_of_frozen_dataclasses() -> None:
    """``load_dane_ipc_monthly`` returns a tuple of ``DaneIpcMonthly`` rows.

    The dataclass is frozen + slots per the project-wide functional-python
    convention (see ``FedFundsWeekly``, ``OnchainCopmMint`` for precedent).
    """
    from scripts.econ_query_api import DaneIpcMonthly, load_dane_ipc_monthly

    conn = _open_canonical_readonly()
    try:
        rows = load_dane_ipc_monthly(conn)
    finally:
        conn.close()

    assert isinstance(rows, tuple)
    assert len(rows) > 0, "DANE table is empty — Pre-flight #1 expected ≥1 row"
    r0 = rows[0]
    assert isinstance(r0, DaneIpcMonthly)
    assert dataclasses.is_dataclass(r0)
    # Frozen + slots: mutation must raise.
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        r0.date = date(1900, 1, 1)  # type: ignore[misc]


def test_load_dane_ipc_monthly_schema_uses_live_columns() -> None:
    """The reader respects the live schema: ``date``, ``ipc_index``,
    ``ipc_pct_change``.

    Per the RC re-review advisory A1 referenced in the task pre-flight
    note, the live schema uses ``ipc_index`` (not ``ipc_value``) and
    ``ipc_pct_change`` (not ``monthly_variation_pct``); the plan body
    cites the wrong names and the live schema is authoritative.
    """
    from scripts.econ_query_api import DaneIpcMonthly, load_dane_ipc_monthly

    conn = _open_canonical_readonly()
    try:
        rows = load_dane_ipc_monthly(conn, start=date(2026, 1, 1))
    finally:
        conn.close()

    fields = {f.name for f in dataclasses.fields(DaneIpcMonthly)}
    assert "date" in fields
    assert "ipc_index" in fields
    assert "ipc_pct_change" in fields
    # And nothing made up beyond what the live table has + the
    # _ingested_at audit column (optional in the dataclass; if present it
    # must be typed; but absence is also acceptable as it's metadata-only).
    assert len(rows) >= 1
    sample = rows[0]
    assert isinstance(sample.date, date)
    assert isinstance(sample.ipc_index, float)


def test_load_dane_ipc_monthly_date_filter_inclusive() -> None:
    """``[start, end]`` inclusive bounds match the project _date_filter
    semantics used by every other reader.

    DANE has rows on 2026-01-01, 2026-02-01, 2026-03-01 (per pre-flight
    #1 — already-verified live state). Filter to that window and assert
    exactly 3 rows.
    """
    from scripts.econ_query_api import load_dane_ipc_monthly

    conn = _open_canonical_readonly()
    try:
        rows = load_dane_ipc_monthly(
            conn, start=date(2026, 1, 1), end=date(2026, 3, 31)
        )
    finally:
        conn.close()

    assert len(rows) == 3
    dates = [r.date for r in rows]
    assert dates == [date(2026, 1, 1), date(2026, 2, 1), date(2026, 3, 1)]
    # Ordered ascending.
    assert dates == sorted(dates)


def test_load_dane_ipc_monthly_cutoff_at_least_2026_02_01() -> None:
    """The DANE cutoff (max date) is ≥ 2026-02-01 — consistent with the
    Task 11.N.2.CO-dane-wire acceptance criterion.

    Real-data integration test: pulls the live DANE max date and asserts
    the staleness gate. The acceptance criterion requires ≤ 2-month
    stale at authoring date 2026-04-25 (i.e., max date ≥ 2026-02-01).
    """
    from scripts.econ_query_api import load_dane_ipc_monthly

    conn = _open_canonical_readonly()
    try:
        rows = load_dane_ipc_monthly(conn)
    finally:
        conn.close()

    cutoff = max(r.date for r in rows)
    assert cutoff >= date(2026, 2, 1), (
        f"DANE cutoff {cutoff} is older than 2026-02-01 — "
        "Task 11.N.2.CO-dane-wire staleness gate violated"
    )


# ─────────────────────────────────────────────────────────────────────────
# Step B — y3_data_fetchers.fetch_country_wc_cpi_components: CO → DANE
# ─────────────────────────────────────────────────────────────────────────


def test_fetch_country_wc_cpi_components_co_via_dane_returns_4_components() -> None:
    """CO + ``conn`` provided → DANE-broadcast 4-component DataFrame.

    Per design doc §10 row 2, DANE has headline only (no expenditure
    split), so all four component slots receive the headline level —
    same broadcast pattern as the IMF IFS fallback. The
    ``fetch_country_wc_cpi_components`` consumer contract is preserved
    byte-exact: columns ``date``, ``food_cpi``, ``energy_cpi``,
    ``housing_cpi``, ``transport_cpi``.
    """
    from scripts.y3_data_fetchers import fetch_country_wc_cpi_components

    conn = _open_canonical_readonly()
    try:
        df = fetch_country_wc_cpi_components(
            "CO",
            date(2024, 1, 1),
            date(2026, 4, 24),
            conn=conn,
        )
    finally:
        conn.close()

    expected_cols = {"date", "food_cpi", "energy_cpi", "housing_cpi", "transport_cpi"}
    assert expected_cols.issubset(set(df.columns))
    assert len(df) > 0
    # Headline-broadcast invariant: per row, all 4 component slots are equal.
    sample = df.iloc[-1]
    assert sample["food_cpi"] == sample["energy_cpi"]
    assert sample["energy_cpi"] == sample["housing_cpi"]
    assert sample["housing_cpi"] == sample["transport_cpi"]


def test_fetch_country_wc_cpi_components_co_via_dane_cutoff_ge_2026_02_01() -> None:
    """Smoke-test cutoff: CO via DANE returns max date ≥ 2026-02-01.

    Acceptance criterion (Task 11.N.2.CO-dane-wire): the smoke-test
    invocation ``fetch_country_wc_cpi_components('CO', date(2024,1,1),
    date(2026,4,24), conn=...)`` returns a level series whose max
    ``date`` is ≥ 2026-02-01.
    """
    from scripts.y3_data_fetchers import fetch_country_wc_cpi_components

    conn = _open_canonical_readonly()
    try:
        df = fetch_country_wc_cpi_components(
            "CO",
            date(2024, 1, 1),
            date(2026, 4, 24),
            conn=conn,
        )
    finally:
        conn.close()

    max_date = df["date"].max()
    # max_date may be a pandas Timestamp or a date; normalize.
    if hasattr(max_date, "date"):
        max_date = max_date.date()
    assert max_date >= date(2026, 2, 1), (
        f"CO DANE-broadcast cutoff {max_date} < 2026-02-01"
    )


def test_fetch_country_wc_cpi_components_co_dane_values_match_live_table() -> None:
    """Round-trip integrity: fetcher output == DANE ipc_index for matching dates.

    Real-data integration: pulls 6 most-recent DANE rows directly via
    the reader, pulls the same 6 dates via the fetcher, asserts byte-
    exact equality of ``food_cpi`` (== headline level) to ``ipc_index``.
    """
    from scripts.econ_query_api import load_dane_ipc_monthly
    from scripts.y3_data_fetchers import fetch_country_wc_cpi_components

    conn = _open_canonical_readonly()
    try:
        dane_rows = load_dane_ipc_monthly(
            conn, start=date(2025, 10, 1), end=date(2026, 3, 31)
        )
        df = fetch_country_wc_cpi_components(
            "CO",
            date(2025, 10, 1),
            date(2026, 3, 31),
            conn=conn,
        )
    finally:
        conn.close()

    # Build {date: ipc_index} from DANE.
    dane_map = {r.date: r.ipc_index for r in dane_rows}
    # Build {date: food_cpi} from fetcher.
    df_dates = df["date"].tolist()
    fetcher_map: dict[date, float] = {}
    for d, v in zip(df_dates, df["food_cpi"].tolist(), strict=True):
        if hasattr(d, "date"):
            d = d.date()
        fetcher_map[d] = float(v)

    assert set(fetcher_map.keys()) == set(dane_map.keys())
    for d, expected in dane_map.items():
        got = fetcher_map[d]
        assert abs(got - expected) < 1e-12, (
            f"DANE round-trip mismatch at {d}: fetcher={got}, dane={expected}"
        )


# ─────────────────────────────────────────────────────────────────────────
# Step C — IMF-IFS path remains intact (sensitivity comparator preservation)
# ─────────────────────────────────────────────────────────────────────────


def test_fetch_imf_ifs_headline_broadcast_function_remains_callable() -> None:
    """The pre-Rev-5.3.2 ``_fetch_imf_ifs_headline_broadcast`` function
    is preserved as the IMF-IFS-only sensitivity comparator consumed by
    Task 11.N.2d.1-reframe. The wire-up adds a NEW dispatch path (DANE
    when ``conn`` is provided for CO); it does not remove or rename the
    IMF-IFS path.
    """
    from scripts.y3_data_fetchers import _fetch_imf_ifs_headline_broadcast

    # Module-level identity check: callable, accepts (country, start, end).
    assert callable(_fetch_imf_ifs_headline_broadcast)
    # Signature parameter names locked in for the sensitivity reframe.
    import inspect

    sig = inspect.signature(_fetch_imf_ifs_headline_broadcast)
    assert list(sig.parameters.keys()) == ["country", "start", "end"]


def test_fetch_country_wc_cpi_components_co_without_conn_uses_imf_path() -> None:
    """CO + no ``conn`` → IMF-IFS path (backward-compatible default).

    No external HTTP call is made here — we monkeypatch the IMF-IFS
    fetcher to a sentinel and assert the dispatch hits it. This locks in
    the contract: the new DANE path is ONLY active when ``conn`` is
    explicitly provided.
    """
    import pandas as pd

    from scripts import y3_data_fetchers

    sentinel_called: dict[str, bool] = {"hit": False}

    def _fake_imf(country: str, start: date, end: date) -> pd.DataFrame:
        sentinel_called["hit"] = True
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
            "CO", date(2025, 1, 1), date(2025, 12, 31)
        )
    finally:
        y3_data_fetchers._fetch_imf_ifs_headline_broadcast = original  # type: ignore[assignment]

    assert sentinel_called["hit"], (
        "CO without conn must still route through IMF-IFS path "
        "(sensitivity-comparator preservation)"
    )
    assert len(out) == 1
