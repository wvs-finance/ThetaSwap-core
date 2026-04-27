"""TDD test suite for Rev-5.3.2 Task 11.N.2d-rev fix-up — admitted-set + validation guard.

Plan:        contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md
             §Task 11.N.2d-rev (line 1916), acceptance criterion at line 1929
Reviews:     contracts/.scratch/2026-04-25-y3-rev532-review-senior-developer.md (§4 BLOCKING)
             contracts/.scratch/2026-04-25-y3-rev532-review-code-reviewer.md (CR-A1)
Predecessor: commit c5cc9b66b (Task 11.N.2d-rev primary execution; gate cleared at 76 weeks)

Reviewer-finding root cause:
    Plan line 1929 requires the new methodology-tag literal to be added to a
    ``load_onchain_y3_weekly()`` admitted-set with an additive schema-migration
    test. The primary execution (commit c5cc9b66b) skipped this on file-scope
    grounds. SD §4 flagged this as BLOCKING because downstream callers who typo
    the byte-exact methodology literal will get a SILENT-EMPTY tuple (no error)
    rather than a load-bearing ValueError. CR-A1 echoed the same concern.

Public API under test:

* ``scripts.econ_query_api._KNOWN_Y3_METHODOLOGY_TAGS`` — module-level
  ``Final[frozenset[str]]`` constant enumerating the admitted set.
* ``scripts.econ_query_api.load_onchain_y3_weekly(conn, source_methodology=...)``
  — must raise ``ValueError`` with a descriptive message listing the admitted
  set when ``source_methodology`` is not in ``_KNOWN_Y3_METHODOLOGY_TAGS``.

Strict TDD (per ``feedback_strict_tdd``): every assertion below MUST fail
before the admitted-set + validation guard land in ``econ_query_api.py``.

Real data over mocks (per ``feedback_real_data_over_mocks``): the admitted-tag
round-trip uses the canonical ``contracts/data/structural_econ.duckdb`` via the
session-scoped ``conn`` fixture in ``scripts/tests/conftest.py``. Synthetic
in-memory DuckDBs are used only to exercise the validation-guard branches
where no DB access is required.
"""
from __future__ import annotations

import duckdb
import pytest


# ─────────────────────────────────────────────────────────────────────────
# Section 1 — admitted-set constant exists and contains the expected tags
# ─────────────────────────────────────────────────────────────────────────


def test_known_y3_methodology_tags_constant_exists() -> None:
    """``_KNOWN_Y3_METHODOLOGY_TAGS`` is a module-level ``frozenset[str]``."""
    from scripts.econ_query_api import _KNOWN_Y3_METHODOLOGY_TAGS

    assert isinstance(_KNOWN_Y3_METHODOLOGY_TAGS, frozenset), (
        "Admitted set must be an immutable frozenset to prevent runtime mutation."
    )
    assert all(isinstance(tag, str) for tag in _KNOWN_Y3_METHODOLOGY_TAGS), (
        "Every admitted methodology tag must be a string literal."
    )


def test_known_y3_methodology_tags_contains_rev531_literal() -> None:
    """Admitted set contains the Rev-5.3.1 stored literal (canonical DB tag)."""
    from scripts.econ_query_api import _KNOWN_Y3_METHODOLOGY_TAGS

    assert "y3_v1_3country_ke_unavailable" in _KNOWN_Y3_METHODOLOGY_TAGS


def test_known_y3_methodology_tags_contains_rev532_literal() -> None:
    """Admitted set contains the Rev-5.3.2 primary-panel stored literal.

    This is the load-bearing literal flagged by SD §4 + CR-A1 — downstream
    Task 11.N.2d.1-reframe and Task 11.O Rev-2 must consume this literal
    byte-exact. The validation guard prevents silent-empty results when a
    consumer typoes the literal.
    """
    from scripts.econ_query_api import _KNOWN_Y3_METHODOLOGY_TAGS

    assert (
        "y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"
        in _KNOWN_Y3_METHODOLOGY_TAGS
    )


# ─────────────────────────────────────────────────────────────────────────
# Section 2 — validation guard rejects unknown methodology tags
# ─────────────────────────────────────────────────────────────────────────


def test_load_onchain_y3_weekly_rejects_unknown_methodology_tag() -> None:
    """Passing an unknown methodology tag raises ``ValueError`` with admitted-set context."""
    from scripts.econ_query_api import load_onchain_y3_weekly
    from scripts.econ_schema import init_db, migrate_onchain_y3_weekly

    conn = duckdb.connect(":memory:")
    init_db(conn)
    migrate_onchain_y3_weekly(conn)

    bogus = "y3_v99_typoed_methodology_tag"

    with pytest.raises(ValueError) as excinfo:
        load_onchain_y3_weekly(conn, source_methodology=bogus)

    msg = str(excinfo.value)
    # Error must name the rejected tag so the caller can self-diagnose.
    assert bogus in msg
    # Error must enumerate the admitted set so the caller can self-correct
    # without grepping the source.
    assert "y3_v1_3country_ke_unavailable" in msg
    assert "y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable" in msg


def test_load_onchain_y3_weekly_rejects_typo_with_close_match() -> None:
    """A near-miss typo on the v2 literal raises ``ValueError``, not silent-empty.

    This is the load-bearing footgun SD §4 flagged: a downstream caller in
    Task 11.N.2d.1-reframe or Task 11.O passes a near-correct literal (e.g.,
    drops the trailing ``_3country_ke_unavailable`` suffix) and silently gets
    zero rows. The validation guard converts that footgun into a hard error.
    """
    from scripts.econ_query_api import load_onchain_y3_weekly
    from scripts.econ_schema import init_db, migrate_onchain_y3_weekly

    conn = duckdb.connect(":memory:")
    init_db(conn)
    migrate_onchain_y3_weekly(conn)

    # The base portion that ``ingest_y3_weekly`` consumes — but NOT what
    # gets stored in DuckDB after the runtime suffix-append.
    near_miss = "y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip"

    with pytest.raises(ValueError):
        load_onchain_y3_weekly(conn, source_methodology=near_miss)


# ─────────────────────────────────────────────────────────────────────────
# Section 3 — admitted tags pass validation and round-trip canonical DB rows
# ─────────────────────────────────────────────────────────────────────────


def test_load_onchain_y3_weekly_accepts_rev532_literal_against_canonical_db(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Passing the Rev-5.3.2 admitted literal returns the expected non-empty panel.

    Uses the session-scoped read-only ``conn`` fixture pointing at the
    canonical ``contracts/data/structural_econ.duckdb`` (per
    ``feedback_real_data_over_mocks``).
    """
    from scripts.econ_query_api import load_onchain_y3_weekly

    rows = load_onchain_y3_weekly(
        conn,
        source_methodology=(
            "y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"
        ),
    )
    # Per the verification memo §3.2, the Rev-5.3.2 panel has 116 rows;
    # we don't pin to 116 exactly so the test is robust to future additive
    # ingests, but the panel MUST be non-empty.
    assert len(rows) > 0, (
        "Admitted Rev-5.3.2 literal must round-trip non-empty rows from "
        "the canonical structural_econ.duckdb."
    )
    # All returned rows must carry the queried methodology tag.
    assert all(
        r.source_methodology
        == "y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"
        for r in rows
    )


def test_load_onchain_y3_weekly_accepts_rev531_literal_against_canonical_db(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Passing the Rev-5.3.1 admitted literal returns the preserved 59-row panel."""
    from scripts.econ_query_api import load_onchain_y3_weekly

    rows = load_onchain_y3_weekly(
        conn,
        source_methodology="y3_v1_3country_ke_unavailable",
    )
    assert len(rows) > 0, (
        "Admitted Rev-5.3.1 literal must round-trip non-empty rows "
        "(byte-exact-preserved 59 rows per memo §3.2)."
    )
    assert all(
        r.source_methodology == "y3_v1_3country_ke_unavailable" for r in rows
    )
