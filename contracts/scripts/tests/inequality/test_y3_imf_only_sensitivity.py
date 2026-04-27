"""TDD test suite for Rev-5.3.2 Task 11.N.2d.1-reframe — IMF-IFS-only sensitivity.

Plan:        contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md
             §Task 11.N.2d.1-reframe (line 1957)
Predecessor: commit c5cc9b66b + d730c39ac (Task 11.N.2d-rev primary panel; gate
             cleared at 76 weeks under
             ``y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable``)

Public API exercised:

* ``scripts.econ_pipeline.ingest_y3_weekly(conn, ..., source_mode=...)`` —
  EXTENDED with a new ``source_mode: Literal["primary", "imf_only_sensitivity"]``
  keyword-only parameter (default ``"primary"`` — backward-compat).

  - ``source_mode == "primary"`` (default): existing behavior — forwards
    ``conn=conn`` to ``fetch_country_wc_cpi_components`` so the CO→DANE
    and BR→BCB Rev-5.3.2 source upgrades activate.
  - ``source_mode == "imf_only_sensitivity"``: forwards ``conn=None`` so
    CO and BR fall back to the IMF-IFS-via-DBnomics path, restoring the
    pre-Rev-5.3.2 dispatch for those countries. EU continues to route to
    Eurostat HICP (its branch is unconditional in the fetcher; no IMF-IFS
    series exists for EU at month-CPI cadence on free-tier APIs). KE is
    skipped per design §10 row 1.

* ``scripts.econ_query_api._KNOWN_Y3_METHODOLOGY_TAGS`` — EXTENDED to
  include the new sensitivity tag literal so downstream readers do not
  trip the validation guard.

Strict TDD (per ``feedback_strict_tdd``): every assertion below MUST fail
on ImportError / NameError / AssertionError before the implementation
lands. Each test is paired with a clear pre-patch ``red`` outcome.

Real data over mocks (per ``feedback_real_data_over_mocks``): the
sensitivity-tag round-trip uses the canonical
``contracts/data/structural_econ.duckdb`` after the ingest lands. The
parameter-dispatch test uses an in-memory DB and a monkeypatched
fetcher (no HTTP) — the unit under test is the call-site dispatch, not
the fetcher itself. Mocks are limited to short-circuiting the fetcher
to capture call-site kwargs; no behavioral mocks of fetched data.

File scope (per ``feedback_agent_scope``):
  * ``scripts/econ_pipeline.py`` — extend ``ingest_y3_weekly`` signature.
  * ``scripts/econ_query_api.py`` — extend ``_KNOWN_Y3_METHODOLOGY_TAGS``.
  * This test file (NEW under ``scripts/tests/inequality/``).
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
# scripts/tests/inequality/test_y3_imf_only_sensitivity.py → parents[3] = contracts/.
_CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[3]
_STRUCTURAL_ECON_DB: Final[Path] = (
    _CONTRACTS_DIR / "data" / "structural_econ.duckdb"
)

# The literal sensitivity tag landed by Task 11.N.2d.1-reframe. The base
# (sans the runtime ``_3country_ke_unavailable`` suffix) is what the
# caller passes to ``ingest_y3_weekly`` via ``source_methodology``; the
# stored tag carries the suffix because KE is skipped (design §10 row 1).
_SENSITIVITY_TAG_BASE: Final[str] = "y3_v2_imf_only_sensitivity"
_SENSITIVITY_TAG_STORED: Final[str] = (
    "y3_v2_imf_only_sensitivity_3country_ke_unavailable"
)


# ─────────────────────────────────────────────────────────────────────────
# Section 1 — ingest_y3_weekly grows a source_mode keyword-only parameter
# ─────────────────────────────────────────────────────────────────────────


def test_ingest_y3_weekly_signature_has_source_mode_kwarg() -> None:
    """``ingest_y3_weekly`` exposes a keyword-only ``source_mode`` parameter
    with default ``"primary"``.

    Pre-patch (red): the signature has no ``source_mode`` parameter.
    """
    from scripts.econ_pipeline import ingest_y3_weekly

    sig = inspect.signature(ingest_y3_weekly)
    assert "source_mode" in sig.parameters, (
        "ingest_y3_weekly must expose a 'source_mode' keyword-only parameter "
        "for Task 11.N.2d.1-reframe IMF-IFS-only sensitivity dispatch."
    )
    param = sig.parameters["source_mode"]
    assert param.kind is inspect.Parameter.KEYWORD_ONLY, (
        "source_mode must be keyword-only (declared after '*' in the signature)."
    )
    assert param.default == "primary", (
        "source_mode default must be 'primary' to preserve backward-compat "
        "with all existing call sites."
    )


def test_ingest_y3_weekly_rejects_unknown_source_mode() -> None:
    """Passing an unknown ``source_mode`` raises ``ValueError``."""
    from scripts.econ_pipeline import ingest_y3_weekly
    from scripts.econ_schema import migrate_onchain_y3_weekly

    test_conn = duckdb.connect(":memory:")
    try:
        migrate_onchain_y3_weekly(test_conn)
        with pytest.raises(ValueError) as excinfo:
            ingest_y3_weekly(
                test_conn,
                start=date(2024, 1, 1),
                end=date(2024, 2, 1),
                source_methodology="bogus",
                source_mode="not_a_real_mode",  # type: ignore[arg-type]
            )
        msg = str(excinfo.value)
        assert "source_mode" in msg
        assert "primary" in msg
        assert "imf_only_sensitivity" in msg
    finally:
        test_conn.close()


# ─────────────────────────────────────────────────────────────────────────
# Section 2 — primary mode forwards conn (regression guard for 11.N.2d-rev)
# ─────────────────────────────────────────────────────────────────────────


def test_primary_mode_forwards_conn_to_wc_cpi_fetcher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``source_mode='primary'`` forwards ``conn=conn`` to the fetcher.

    This is a regression guard — the existing Task 11.N.2d-rev
    behavior must not change. The 11.N.2d.1-reframe extension adds a
    new branch; the default branch must still activate the DANE / BCB
    upgrades on real ingests.
    """
    from scripts import econ_pipeline, y3_data_fetchers

    captured: list[dict[str, object]] = []

    def _capture(
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
        from scripts.y3_data_fetchers import Y3FetchError

        raise Y3FetchError("test sentinel — short-circuit after capture")

    def _equity_stub(country: str, start: date, end: date) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "date": [date(2024, 1, 5), date(2024, 1, 12)],
                "equity_close": [100.0, 101.0],
            }
        )

    test_conn = duckdb.connect(":memory:")
    try:
        from scripts.econ_schema import migrate_onchain_y3_weekly

        migrate_onchain_y3_weekly(test_conn)

        monkeypatch.setattr(
            y3_data_fetchers, "fetch_country_wc_cpi_components", _capture
        )
        monkeypatch.setattr(
            y3_data_fetchers, "fetch_country_equity", _equity_stub
        )

        from scripts.y3_data_fetchers import Y3FetchError

        with pytest.raises(Y3FetchError):
            econ_pipeline.ingest_y3_weekly(
                test_conn,
                start=date(2024, 1, 1),
                end=date(2024, 2, 1),
                source_methodology="primary_mode_regression_test",
                source_mode="primary",
            )
    finally:
        test_conn.close()

    assert len(captured) >= 1
    for cap in captured:
        assert not cap["conn_is_none"], (
            f"source_mode='primary' must forward the live conn to the "
            f"fetcher; country {cap['country']!r} received conn=None."
        )
        assert cap["conn_id"] == id(test_conn)


# ─────────────────────────────────────────────────────────────────────────
# Section 3 — imf_only_sensitivity mode forwards conn=None to the fetcher
# ─────────────────────────────────────────────────────────────────────────


def test_imf_only_sensitivity_passes_conn_none_to_wc_cpi_fetcher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``source_mode='imf_only_sensitivity'`` forwards ``conn=None``.

    This is the load-bearing dispatch for Task 11.N.2d.1-reframe: when
    the caller wants the pre-Rev-5.3.2 source mix (CO + BR routed
    through IMF-IFS rather than DANE / BCB), the call site at
    ``econ_pipeline.py`` must pass ``conn=None`` regardless of whether
    the upstream caller threaded a connection through.

    Pre-patch (red): no ``source_mode`` parameter exists; the test
    fails on TypeError.
    """
    from scripts import econ_pipeline, y3_data_fetchers

    captured: list[dict[str, object]] = []

    def _capture(
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
            }
        )
        from scripts.y3_data_fetchers import Y3FetchError

        raise Y3FetchError("test sentinel — short-circuit after capture")

    def _equity_stub(country: str, start: date, end: date) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "date": [date(2024, 1, 5), date(2024, 1, 12)],
                "equity_close": [100.0, 101.0],
            }
        )

    test_conn = duckdb.connect(":memory:")
    try:
        from scripts.econ_schema import migrate_onchain_y3_weekly

        migrate_onchain_y3_weekly(test_conn)

        monkeypatch.setattr(
            y3_data_fetchers, "fetch_country_wc_cpi_components", _capture
        )
        monkeypatch.setattr(
            y3_data_fetchers, "fetch_country_equity", _equity_stub
        )

        from scripts.y3_data_fetchers import Y3FetchError

        with pytest.raises(Y3FetchError):
            econ_pipeline.ingest_y3_weekly(
                test_conn,
                start=date(2024, 1, 1),
                end=date(2024, 2, 1),
                source_methodology=_SENSITIVITY_TAG_BASE,
                source_mode="imf_only_sensitivity",
            )
    finally:
        test_conn.close()

    assert len(captured) >= 1
    for cap in captured:
        assert cap["conn_is_none"], (
            f"source_mode='imf_only_sensitivity' must pass conn=None to the "
            f"fetcher so CO/BR fall back to IMF-IFS; country {cap['country']!r} "
            f"received conn != None."
        )


# ─────────────────────────────────────────────────────────────────────────
# Section 4 — admitted-set extension: sensitivity tag is admitted
# ─────────────────────────────────────────────────────────────────────────


def test_known_y3_methodology_tags_contains_sensitivity_literal() -> None:
    """The IMF-IFS-only sensitivity stored literal is in the admitted set.

    Pre-patch (red): ``_KNOWN_Y3_METHODOLOGY_TAGS`` does not contain
    ``y3_v2_imf_only_sensitivity_3country_ke_unavailable``.

    The stored literal carries the runtime suffix because KE is skipped
    (design §10 row 1) — same convention as the primary panel literal.
    """
    from scripts.econ_query_api import _KNOWN_Y3_METHODOLOGY_TAGS

    assert _SENSITIVITY_TAG_STORED in _KNOWN_Y3_METHODOLOGY_TAGS, (
        f"Admitted set must include {_SENSITIVITY_TAG_STORED!r} so downstream "
        f"readers can round-trip the Task 11.N.2d.1-reframe sensitivity panel "
        f"without tripping the load-bearing ValueError validation guard."
    )


def test_load_onchain_y3_weekly_accepts_sensitivity_literal_against_canonical_db() -> None:
    """``load_onchain_y3_weekly(conn, source_methodology=<sensitivity>)``
    returns the sensitivity panel non-empty.

    Pre-ingest (red): the canonical DB has zero rows under the
    sensitivity literal — the loader either raises ValueError (if the
    literal is unknown) or returns an empty tuple (if known but
    un-ingested).

    Post-ingest (green): the loader returns a non-empty panel matching
    the count documented in the verification memo.
    """
    if not _STRUCTURAL_ECON_DB.is_file():
        pytest.skip(f"structural_econ.duckdb missing at {_STRUCTURAL_ECON_DB}")

    from scripts.econ_query_api import load_onchain_y3_weekly

    conn = duckdb.connect(str(_STRUCTURAL_ECON_DB), read_only=True)
    try:
        rows = load_onchain_y3_weekly(
            conn,
            source_methodology=_SENSITIVITY_TAG_STORED,
        )
    finally:
        conn.close()

    assert len(rows) > 0, (
        f"Sensitivity panel must persist non-empty in the canonical "
        f"structural_econ.duckdb under {_SENSITIVITY_TAG_STORED!r}. "
        f"Per the Task 11.N.2d.1-reframe verification memo, expected "
        f"row count is in the 50-110 range (binding country IMF-IFS "
        f"cutoff bounds the panel above)."
    )
    assert all(
        r.source_methodology == _SENSITIVITY_TAG_STORED for r in rows
    ), (
        "All sensitivity rows must carry the sensitivity literal — "
        "composite-PK isolation must be byte-exact."
    )


def test_primary_panel_rows_unchanged_post_sensitivity_ingest() -> None:
    """The Task 11.N.2d-rev primary panel rows are byte-exact preserved.

    The sensitivity ingest is purely additive INSERT under a distinct
    ``source_methodology`` value; the composite PK ``(week_start,
    source_methodology)`` admits the new tag without mutating the
    primary 116-row panel.

    Per the Task 11.N.2d-rev verification memo §3.2, the primary panel
    has 116 rows under
    ``y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable``;
    this test asserts the count is preserved after the sensitivity
    ingest lands.
    """
    if not _STRUCTURAL_ECON_DB.is_file():
        pytest.skip(f"structural_econ.duckdb missing at {_STRUCTURAL_ECON_DB}")

    from scripts.econ_query_api import load_onchain_y3_weekly

    conn = duckdb.connect(str(_STRUCTURAL_ECON_DB), read_only=True)
    try:
        primary = load_onchain_y3_weekly(
            conn,
            source_methodology=(
                "y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"
            ),
        )
    finally:
        conn.close()

    assert len(primary) == 116, (
        f"Primary panel must remain at 116 rows post-sensitivity-ingest "
        f"(byte-exact preservation); observed {len(primary)}. The "
        f"sensitivity ingest is additive under a distinct methodology tag — "
        f"any mutation here is a composite-PK violation."
    )
