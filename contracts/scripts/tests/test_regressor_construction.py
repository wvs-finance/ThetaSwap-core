"""Construction-time regression tests for the 5 Decision #4-9 regressors.

The ``banrep_rate_surprise`` regressor is already defended by its own
dedicated suite (``test_banrep_rate_surprise_construction.py``) against
the zero-variance placeholder that was in place before the event-study
construction landed. This module extends that defensive posture to the
remaining five regressors that appear in the NB2 Column-6 primary OLS:

    * ``cpi_surprise_ar1``       — Decision #4 identifying regressor
    * ``us_cpi_surprise``        — Decision #5 global inflation control
    * ``vix_avg``                — Decision #7 global-risk control
    * ``oil_return``             — Decision #8 commodity-channel control
    * ``intervention_dummy``     — Decision #9 policy-regime control

Each regressor is guarded with three construction-time invariants:

    1. Non-zero variance — catches regression to a constant placeholder.
    2. Row count matches Decision #1 window — exactly 947 weekly rows
       on ``week_start BETWEEN '2008-01-02' AND '2026-03-01'``.
    3. Zero nulls — catches upstream pipeline breakage (vendor API
       outage, schema drift, silent join failure).

The variance thresholds are deliberately loose relative to the observed
values — any future reformulation that preserves meaningful variation
will clear them; any silent regression to a constant will fail the
first assertion. Observed standard deviations on the Decision #1 window
at test-authoring time:

    * cpi_surprise_ar1:    σ ≈ 0.347  → threshold > 0.05
    * us_cpi_surprise:     σ ≈ 0.128  → threshold > 0.02
    * vix_avg:             σ ≈ 8.746  → threshold > 1.0
    * oil_return:          σ ≈ 0.060  → threshold > 0.005
    * intervention_dummy:  σ ≈ 0.472  → threshold > 0.1

Reality Checker LOW-LATENT finding from Task 15 three-way review: the
non-banrep regressors had no dedicated construction-time guardrail;
this module closes that gap. All tests use the session-scoped read-only
``conn`` fixture from ``conftest.py`` — no mocks, no synthetic data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final

import duckdb


# ── Decision #1 window (research doc §2.1, spec §3.1) ────────────────────

DECISION1_START: Final[date] = date(2008, 1, 2)
DECISION1_END: Final[date] = date(2026, 3, 1)
EXPECTED_ROWS: Final[int] = 947

_WINDOW_PREDICATE: Final[str] = (
    f"week_start BETWEEN '{DECISION1_START.isoformat()}' "
    f"AND '{DECISION1_END.isoformat()}'"
)


# ── Regressor spec ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class _RegressorSpec:
    """Construction-time invariant spec for a single regressor column.

    * ``column``: the ``weekly_panel`` column name being guarded.
    * ``variance_floor``: minimum STDDEV below which the test fails. Set
      deliberately loose (~15% of the observed value) so the test catches
      regression to a constant placeholder without flickering on ordinary
      data-vintage refreshes.
    * ``decision_ref``: human-readable ``Decision #N`` label used in
      failure messages to point reviewers at the right spec section.
    """
    column: str
    variance_floor: float
    decision_ref: str


_REGRESSORS: Final[tuple[_RegressorSpec, ...]] = (
    _RegressorSpec(
        column="cpi_surprise_ar1",
        variance_floor=0.05,
        decision_ref="Decision #4 (CPI surprise AR(1) identifier)",
    ),
    _RegressorSpec(
        column="us_cpi_surprise",
        variance_floor=0.02,
        decision_ref="Decision #5 (US CPI surprise control)",
    ),
    _RegressorSpec(
        column="vix_avg",
        variance_floor=1.0,
        decision_ref="Decision #7 (VIX weekly-mean global-risk control)",
    ),
    _RegressorSpec(
        column="oil_return",
        variance_floor=0.005,
        decision_ref="Decision #8 (oil return weekly commodity control)",
    ),
    _RegressorSpec(
        column="intervention_dummy",
        variance_floor=0.1,
        decision_ref="Decision #9 (BanRep FX intervention binary dummy)",
    ),
)


# ── 1. Non-zero variance per regressor ───────────────────────────────────

def test_cpi_surprise_ar1_has_nonzero_variance(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_variance_above_floor(conn, _REGRESSORS[0])


def test_us_cpi_surprise_has_nonzero_variance(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_variance_above_floor(conn, _REGRESSORS[1])


def test_vix_avg_has_nonzero_variance(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_variance_above_floor(conn, _REGRESSORS[2])


def test_oil_return_has_nonzero_variance(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_variance_above_floor(conn, _REGRESSORS[3])


def test_intervention_dummy_has_nonzero_variance(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_variance_above_floor(conn, _REGRESSORS[4])


# ── 2. Row count matches Decision #1 window ───────────────────────────────

def test_cpi_surprise_ar1_row_count_matches_decision_1(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_row_count_matches_decision_1(conn, _REGRESSORS[0])


def test_us_cpi_surprise_row_count_matches_decision_1(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_row_count_matches_decision_1(conn, _REGRESSORS[1])


def test_vix_avg_row_count_matches_decision_1(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_row_count_matches_decision_1(conn, _REGRESSORS[2])


def test_oil_return_row_count_matches_decision_1(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_row_count_matches_decision_1(conn, _REGRESSORS[3])


def test_intervention_dummy_row_count_matches_decision_1(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_row_count_matches_decision_1(conn, _REGRESSORS[4])


# ── 3. Null count is zero on the Decision #1 window ──────────────────────

def test_cpi_surprise_ar1_null_count_zero(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_null_count_zero(conn, _REGRESSORS[0])


def test_us_cpi_surprise_null_count_zero(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_null_count_zero(conn, _REGRESSORS[1])


def test_vix_avg_null_count_zero(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_null_count_zero(conn, _REGRESSORS[2])


def test_oil_return_null_count_zero(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_null_count_zero(conn, _REGRESSORS[3])


def test_intervention_dummy_null_count_zero(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    _assert_null_count_zero(conn, _REGRESSORS[4])


# ── Shared helpers ────────────────────────────────────────────────────────

def _assert_variance_above_floor(
    conn: duckdb.DuckDBPyConnection, spec: _RegressorSpec,
) -> None:
    """Guard against regression to a constant placeholder.

    Matches the pattern in ``test_banrep_rate_surprise_construction.py``:
    the DDL could silently be reverted to ``CAST(0.0 AS DOUBLE) AS
    <column>``; this assertion defends the populated build.
    """
    row = conn.execute(
        f"SELECT STDDEV({spec.column}) "
        f"FROM weekly_panel WHERE {_WINDOW_PREDICATE}"
    ).fetchone()
    assert row is not None
    std = row[0]
    assert std is not None and std > spec.variance_floor, (
        f"STDDEV({spec.column}) = {std} — expected > {spec.variance_floor} "
        f"on the Decision #1 window. Did the {spec.decision_ref} "
        f"construction regress to a constant placeholder?"
    )


def _assert_row_count_matches_decision_1(
    conn: duckdb.DuckDBPyConnection, spec: _RegressorSpec,
) -> None:
    """Guard against window drift or panel-build truncation.

    The Decision #1 window is 947 ISO weeks (Monday-aligned) spanning
    2008-01-02 through 2026-03-01 inclusive. Any future panel refresh
    that silently drops the lower or upper bound (vendor history tail
    deprecation, BanRep methodology cutover, FRED calendar extension)
    will surface here before reaching NB2.
    """
    row = conn.execute(
        f"SELECT COUNT(*) FROM weekly_panel WHERE {_WINDOW_PREDICATE}"
    ).fetchone()
    assert row is not None
    count = row[0]
    assert count == EXPECTED_ROWS, (
        f"weekly_panel row count on Decision #1 window = {count}; "
        f"expected {EXPECTED_ROWS}. Spec binding this column: "
        f"{spec.decision_ref}."
    )


def _assert_null_count_zero(
    conn: duckdb.DuckDBPyConnection, spec: _RegressorSpec,
) -> None:
    """Guard against upstream pipeline breakage introducing NULLs.

    Each Decision #4-9 regressor lands at 947/947 non-null on the
    Decision #1 window by construction (econ_panels.py build steps
    compute deterministic values on every week). A non-zero null
    count indicates vendor API outage, schema drift, or silent join
    failure in the panel builder — any of which would silently bias
    NB2 Column-6 OLS under listwise-complete-case alignment
    (Decision #12).
    """
    row = conn.execute(
        f"SELECT COUNT(*) - COUNT({spec.column}) "
        f"FROM weekly_panel WHERE {_WINDOW_PREDICATE}"
    ).fetchone()
    assert row is not None
    null_count = row[0]
    assert null_count == 0, (
        f"weekly_panel.{spec.column} null count on Decision #1 window = "
        f"{null_count}; expected 0. Spec binding: {spec.decision_ref}. "
        f"Investigate upstream in scripts/econ_panels.py."
    )
