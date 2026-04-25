"""TDD test suite for Rev-5.3.2 Task 11.N.2d-rev — conn-forwarding patch.

Plan:        contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md
             §Task 11.N.2d-rev (line 1916)
Predecessors:
  * Task 11.N.2.CO-dane-wire (commit f7b03caac) — added
    ``_fetch_dane_headline_broadcast`` + ``conn`` kwarg dispatch in
    ``fetch_country_wc_cpi_components``.
  * Task 11.N.2.BR-bcb-fetcher (commit 4ecbf2813) — added
    ``_fetch_bcb_headline_broadcast`` + ``conn`` kwarg dispatch.

Public API exercised:

* ``scripts.econ_pipeline.ingest_y3_weekly`` — the load-bearing ingest
  entry point. Per the SD A2 advisory carried over from CO + BR
  reviews, the call site at ``econ_pipeline.py:2905`` must forward the
  ``conn`` argument it already holds to
  ``fetch_country_wc_cpi_components``. Without this forwarding, both
  the DANE (CO) and BCB (BR) source upgrades silently no-op and the
  ingest falls back to the IMF-IFS path.

Strict TDD (per ``feedback_strict_tdd``): the failing-first test below
monkeypatches ``fetch_country_wc_cpi_components`` to record its
keyword arguments. Pre-patch (red) the recorded ``conn`` kwarg is
``None`` (call site does NOT forward); post-patch (green) the recorded
``conn`` kwarg equals the connection threaded through the ingest
function.

File scope (per ``feedback_agent_scope``): writes to
``econ_pipeline.py`` (one-line patch at line 2905) only. No other
production-code mutation. The ``y3_data_fetchers.py`` API contract is
the predecessor's; this test exercises the pre-existing kwarg-aware
dispatch.
"""
from __future__ import annotations

import inspect
from datetime import date
from pathlib import Path
from typing import Final

import duckdb
import pandas as pd
import pytest

# Canonical DB path resolved from this test file's location.
# scripts/tests/inequality/test_y3_rev532_conn_forward.py → parents[3] = contracts/.
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
# Step 1 — conn-forwarding patch verification (the failing-first test)
# ─────────────────────────────────────────────────────────────────────────


def test_ingest_y3_weekly_forwards_conn_to_wc_cpi_fetcher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``ingest_y3_weekly`` MUST forward ``conn`` to
    ``fetch_country_wc_cpi_components``.

    Pre-patch: the call site at ``econ_pipeline.py:2905`` invokes
    ``fetch_country_wc_cpi_components(country, start, end)`` without
    forwarding ``conn``. The kwarg-aware dispatch in the fetcher then
    routes to IMF-IFS regardless of whether ``conn`` was provided
    upstream — silently negating the DANE / BCB source upgrades.

    Post-patch: ``conn`` is forwarded as a keyword argument
    (``conn=conn``); the per-country ``conn is not None`` branches in
    ``fetch_country_wc_cpi_components`` activate (CO → DANE, BR → BCB).

    The test mocks ``fetch_country_wc_cpi_components`` to a sentinel
    that records the keyword arguments. We don't run the full ingest —
    we just verify the call-site forwards the connection.
    """
    from scripts import econ_pipeline

    captured: list[dict[str, object]] = []

    def _capture_fetcher(
        country: str,
        start: date,
        end: date,
        *,
        conn: duckdb.DuckDBPyConnection | None = None,
    ) -> pd.DataFrame:
        captured.append(
            {
                "country": country,
                "conn_is_none": conn is None,
                "conn_id": id(conn) if conn is not None else None,
            }
        )
        # Raise to short-circuit the loop body (we only need to confirm
        # the kwarg dispatch — running the full ingest is not the unit
        # under test here).
        from scripts.y3_data_fetchers import Y3FetchError

        raise Y3FetchError("test sentinel — short-circuit after capture")

    # Also short-circuit the equity fetcher so the test doesn't issue
    # external HTTP requests; the WC-CPI fetcher is what we're locking
    # in here.
    def _capture_equity(country: str, start: date, end: date) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "date": [date(2024, 1, 5), date(2024, 1, 12)],
                "equity_close": [100.0, 101.0],
            }
        )

    # Use an in-memory DB so the test never mutates the canonical one.
    test_conn = duckdb.connect(":memory:")
    try:
        # Stand up the schema in the test DB so persist doesn't error
        # if the loop ever lands a country (it won't because the
        # WC-CPI fetcher raises) — defensive scaffolding only.
        from scripts.econ_schema import migrate_onchain_y3_weekly

        migrate_onchain_y3_weekly(test_conn)

        # Monkeypatch the fetcher reference inside the y3_data_fetchers
        # module — ingest_y3_weekly imports the names locally inside the
        # function body, so we patch at the source module.
        from scripts import y3_data_fetchers

        monkeypatch.setattr(
            y3_data_fetchers,
            "fetch_country_wc_cpi_components",
            _capture_fetcher,
        )
        monkeypatch.setattr(
            y3_data_fetchers, "fetch_country_equity", _capture_equity
        )

        # Run the ingest. It should raise (no countries land) — we
        # catch the expected error and inspect the capture log.
        from scripts.y3_data_fetchers import Y3FetchError

        with pytest.raises(Y3FetchError):
            econ_pipeline.ingest_y3_weekly(
                test_conn,
                start=date(2024, 1, 1),
                end=date(2024, 2, 1),
                source_methodology="conn_forward_test",
            )
    finally:
        test_conn.close()

    # Assertions: each country call MUST have received conn != None
    # post-patch. Pre-patch, conn_is_none is True for every country.
    assert len(captured) >= 1, (
        "Fetcher was never invoked — test scaffolding failure"
    )
    for cap in captured:
        assert not cap["conn_is_none"], (
            f"ingest_y3_weekly did NOT forward conn to "
            f"fetch_country_wc_cpi_components for country "
            f"{cap['country']!r} — the call site at "
            f"econ_pipeline.py:2905 is missing the conn=conn kwarg. "
            f"This is the load-bearing patch for Rev-5.3.2 "
            f"Task 11.N.2d-rev: without it, the DANE (CO) and BCB "
            f"(BR) source upgrades silently no-op."
        )
        assert cap["conn_id"] == id(test_conn), (
            "Forwarded conn is not the same object passed into "
            "ingest_y3_weekly"
        )


def test_ingest_y3_weekly_call_site_uses_kwarg_form() -> None:
    """Static-source guard: the call site at ``econ_pipeline.py:2905``
    uses the ``conn=conn`` kwarg form (not positional).

    Per the predecessor's contract, the ``conn`` parameter on
    ``fetch_country_wc_cpi_components`` is keyword-only (declared
    after ``*``). The call site MUST pass it as a keyword argument.
    This test reads the source of ``ingest_y3_weekly`` and asserts the
    canonical kwarg form is present.
    """
    from scripts import econ_pipeline

    src = inspect.getsource(econ_pipeline.ingest_y3_weekly)
    assert "fetch_country_wc_cpi_components(" in src, (
        "ingest_y3_weekly does not call fetch_country_wc_cpi_components — "
        "test scaffolding mismatch"
    )
    assert "conn=conn" in src, (
        "ingest_y3_weekly must forward conn via 'conn=conn' kwarg form. "
        "Per the kwarg-only signature in y3_data_fetchers, positional "
        "is not accepted."
    )
