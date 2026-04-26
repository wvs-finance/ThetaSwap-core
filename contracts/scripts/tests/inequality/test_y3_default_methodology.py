"""TDD test suite for Rev-5.3.2 Task 11.O Step 0 — load_onchain_y3_weekly default flip.

Plan:        contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md
             §Task 11.O Step 0 (line 1228)
Reviews:     contracts/.scratch/2026-04-25-y3-rev532-review-senior-developer.md
             (SD-RR-A1: residual silent-empty-tuple footgun on the legacy default)
             contracts/.scratch/2026-04-25-y3-rev532-review-code-reviewer.md (CR-A1)
Predecessor: commit 2a0377057 (Rev-5.3.2 admitted-set + validation guard fix-up)

Reviewer-finding root cause:
    The Rev-5.3.2 fix-up (commit 2a0377057) closed the SILENT-EMPTY footgun
    against TYPOED methodology literals (`y3_v99_typoed` now raises ValueError
    via the admitted-set guard). It did NOT close the SILENT-EMPTY footgun
    against the LEGACY DEFAULT: a production caller that simply omits the
    ``source_methodology`` argument calls
    ``load_onchain_y3_weekly(conn)`` and gets ZERO rows back from the canonical
    DuckDB, because no rows in the production DB carry the bare ``"y3_v1"``
    literal — that literal is reserved for the synthetic-data round-trip in
    ``test_y3.py::test_step7_load_onchain_y3_weekly_returns_frozen_dataclass``.
    SD-RR-A1 flagged this as the residual gap; Step 0 (Rev-5.3.2 plan line
    1228) closes it by flipping the default to the v2 primary literal so
    default callers receive the operative production panel.

Public API under test:

* ``scripts.econ_query_api.load_onchain_y3_weekly(conn)`` — invoked WITHOUT
  ``source_methodology`` argument MUST return rows tagged with the Rev-5.3.2
  v2 primary literal
  ``"y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"``,
  not the synthetic-test-only ``"y3_v1"`` literal.

Strict TDD (per ``feedback_strict_tdd``): the assertion below MUST fail BEFORE
the default-flip lands in ``econ_query_api.py``. Pre-flip, the call returns
an empty tuple (silent footgun). Post-flip, the call returns the canonical
116-row Rev-5.3.2 primary panel.

Real data over mocks (per ``feedback_real_data_over_mocks``): the round-trip
uses the canonical ``contracts/data/structural_econ.duckdb`` via the
session-scoped ``conn`` fixture in ``scripts/tests/conftest.py``.
"""
from __future__ import annotations

from typing import Final

import duckdb


# Pinned Rev-5.3.2 v2 primary literal — the operative production tag (116 rows
# in canonical DB). Pinned here so a future rename of the v2 literal forces
# this test to be updated in lockstep with the default in ``econ_query_api.py``.
REV_5_3_2_V2_PRIMARY_LITERAL: Final[str] = (
    "y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"
)


# ─────────────────────────────────────────────────────────────────────────
# Section 1 — default-arg flip on the public loader (failing-first)
# ─────────────────────────────────────────────────────────────────────────


def test_load_onchain_y3_weekly_default_returns_v2_primary_literal_rows(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """``load_onchain_y3_weekly(conn)`` (no tag arg) returns Rev-5.3.2 v2 primary rows.

    This is the load-bearing footgun-fix assertion for SD-RR-A1: a caller that
    omits ``source_methodology`` MUST receive the operative production panel,
    not an empty tuple. Post-flip: rows are non-empty and every row carries
    the v2 primary literal.
    """
    from scripts.econ_query_api import load_onchain_y3_weekly

    rows = load_onchain_y3_weekly(conn)

    assert len(rows) > 0, (
        "Default-arg call MUST return non-empty rows from canonical DuckDB. "
        "Pre-flip behavior (default = 'y3_v1') yields zero rows because the "
        "bare 'y3_v1' literal is synthetic-test-only."
    )
    assert all(
        r.source_methodology == REV_5_3_2_V2_PRIMARY_LITERAL for r in rows
    ), (
        "Every row from the default-arg call must carry the Rev-5.3.2 v2 "
        f"primary literal {REV_5_3_2_V2_PRIMARY_LITERAL!r}; the default has "
        "drifted off the production panel."
    )


def test_load_onchain_y3_weekly_default_matches_explicit_v2_primary_call(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Default-arg result equals explicit v2-literal result row-for-row.

    Locks the default behavior to the v2 primary panel: any drift between the
    default-arg path and the explicit-arg path against the same canonical DB
    indicates a regression in the default value.
    """
    from scripts.econ_query_api import load_onchain_y3_weekly

    default_rows = load_onchain_y3_weekly(conn)
    explicit_rows = load_onchain_y3_weekly(
        conn, source_methodology=REV_5_3_2_V2_PRIMARY_LITERAL
    )

    assert len(default_rows) == len(explicit_rows), (
        "Default-arg row count must match explicit Rev-5.3.2 v2 literal "
        f"row count: default={len(default_rows)}, "
        f"explicit={len(explicit_rows)}."
    )
    # week_start ASC ordering is part of the loader contract; pairwise equality
    # below depends on it. Frozen dataclass equality compares all 7 fields.
    assert default_rows == explicit_rows, (
        "Default-arg rows must be byte-equal (frozen-dataclass field-wise) "
        "to explicit-Rev-5.3.2-v2-literal rows."
    )
