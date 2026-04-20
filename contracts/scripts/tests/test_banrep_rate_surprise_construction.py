"""Construction-time regression tests for ``banrep_rate_surprise``.

The ``banrep_rate_surprise`` column on ``weekly_panel`` and ``daily_panel``
is the empirical implementation of the event-study operator specified in
research doc 2026-04-18 §8.1:

    s_w = SUM_{τ ∈ meetings ∩ week w} (IBR_ON_τ - IBR_ON_{τ-1})

The construction lives in ``scripts/econ_panels.py`` and joins
``banrep_meeting_calendar`` against per-day IBR changes from
``banrep_ibr_daily``. This module validates the empirical output against
six non-trivial invariants that the old zero-variance placeholder (0.0
for every row) would have violated.

All tests are scoped to the Decision #1 estimation window:
    ``week_start BETWEEN '2008-01-02' AND '2026-03-01'``

No mocks — the tests read the populated ``structural_econ.duckdb`` via
the session-scoped ``conn`` fixture from ``conftest.py``.
"""
from __future__ import annotations

from datetime import date
from typing import Final

import duckdb

# ── Decision #1 window (research doc §2.1, spec §3.1) ────────────────────

DECISION1_START: Final[date] = date(2008, 1, 2)
DECISION1_END: Final[date] = date(2026, 3, 1)

_WINDOW_PREDICATE: Final[str] = (
    f"week_start BETWEEN '{DECISION1_START.isoformat()}' "
    f"AND '{DECISION1_END.isoformat()}'"
)


# ── 1. Variance ───────────────────────────────────────────────────────────

def test_nonzero_variance(conn: duckdb.DuckDBPyConnection) -> None:
    """STDDEV(banrep_rate_surprise) > 0.05 in the Decision #1 window.

    This is the hard regression against the legacy "CAST(0.0 AS DOUBLE) AS
    banrep_rate_surprise" placeholder that was in place before the
    event-study construction landed. The 0.05 floor is deliberately loose
    relative to the observed 0.160 — any future reformulation that keeps
    meaningful variation will clear it; any silent regression to a constant
    zero will fail it immediately.
    """
    row = conn.execute(
        f"SELECT STDDEV(banrep_rate_surprise) "
        f"FROM weekly_panel WHERE {_WINDOW_PREDICATE}"
    ).fetchone()
    assert row is not None
    std = row[0]
    assert std is not None and std > 0.05, (
        f"STDDEV(banrep_rate_surprise) = {std} — expected > 0.05. "
        f"Did the event-study construction regress to a constant?"
    )


# ── 2. Non-zero count ─────────────────────────────────────────────────────

def test_nonzero_count_in_expected_range(conn: duckdb.DuckDBPyConnection) -> None:
    """Non-zero week count falls in [60, 200].

    At test-authoring time the panel has 88 non-zero weeks (one per
    rate-change meeting, which always moves IBR by at least a few bp on
    the effective date). The 60-200 band allows Banrep to add or remove
    ~30 meetings before the test becomes brittle, while still catching
    gross failures (e.g. 0 non-zero = placeholder regression, 900+
    non-zero = spurious non-zero on hold / non-meeting weeks).
    """
    row = conn.execute(
        f"SELECT SUM(CASE WHEN banrep_rate_surprise != 0 THEN 1 ELSE 0 END) "
        f"FROM weekly_panel WHERE {_WINDOW_PREDICATE}"
    ).fetchone()
    assert row is not None
    count = row[0]
    assert count is not None and 60 <= count <= 200, (
        f"Non-zero banrep_rate_surprise weeks = {count} — expected in [60, 200]"
    )


# ── 3. Non-meeting-week structural zeros ──────────────────────────────────

def test_non_meeting_weeks_are_exactly_zero(conn: duckdb.DuckDBPyConnection) -> None:
    """Weeks with NO policy_rate_decision meeting have surprise = 0.0 exactly.

    Research doc §9.2 specifies a *structural zero* on non-meeting weeks —
    not a tiny noise value. This test defends against two classes of bug:

      * Numerical drift in the event-study SUM (e.g. floating-point residues
        from an accidental LAG over non-meeting days).
      * NULL leakage from the LEFT JOIN collapsing to ``NULL`` instead of
        ``COALESCE(..., 0.0)``.

    The predicate excludes weeks containing a ``policy_rate_decision``
    entry — weeks containing only a ``policy_rate_hold_inferred`` entry
    are also expected to be exactly zero by construction (§4.2: hold days
    produce sub-basis-point OMO noise in the IBR, which nets to zero after
    the within-week SUM). This is validated implicitly by the stronger
    "non-meeting" clause below.
    """
    row = conn.execute(
        f"""
        WITH decision_weeks AS (
            SELECT DISTINCT date_trunc('week', meeting_date)::DATE AS week_start
            FROM banrep_meeting_calendar
            WHERE meeting_type = 'policy_rate_decision'
        )
        SELECT
          SUM(CASE WHEN w.banrep_rate_surprise = 0.0 THEN 1 ELSE 0 END) AS zero_rows,
          SUM(CASE WHEN w.banrep_rate_surprise != 0.0 THEN 1 ELSE 0 END) AS nonzero_rows,
          MIN(w.banrep_rate_surprise) AS min_val,
          MAX(w.banrep_rate_surprise) AS max_val
        FROM weekly_panel w
        LEFT JOIN decision_weeks dw ON dw.week_start = w.week_start
        WHERE {_WINDOW_PREDICATE.replace('week_start', 'w.week_start')}
          AND dw.week_start IS NULL
        """
    ).fetchone()
    assert row is not None
    zeros, nonzeros, min_val, max_val = row
    assert nonzeros == 0, (
        f"Non-decision-meeting weeks with non-zero surprise: {nonzeros} "
        f"(min={min_val}, max={max_val}). Expected all exact zero."
    )


# ── 4. Decision-meeting weeks have non-zero surprise OR hold justification ─

def test_meeting_weeks_have_nonzero_surprise_or_hold_justification(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Every decision-meeting week has non-zero surprise.

    By construction, ``policy_rate_decision`` rows are derived from TPM
    *changes* in ``DF_CBR_DAILY_HIST``. Each such date therefore has a
    non-zero IBR step on the effective date (the IBR tracks TPM on
    settlement days — research doc §4.1, §4.3). The join in
    ``build_weekly_panel`` turns this into a non-zero
    ``banrep_rate_surprise`` for the ISO week containing the meeting_date.

    If this test ever fails for a week where TPM held flat (a "genuine
    hold" that was misclassified as decision), the assertion message
    instructs the reader to check the TPM series for that date.
    """
    rows = conn.execute(
        f"""
        WITH decision_weeks AS (
            SELECT DISTINCT
                date_trunc('week', meeting_date)::DATE AS week_start,
                MIN(meeting_date) AS sample_meeting_date
            FROM banrep_meeting_calendar
            WHERE meeting_type = 'policy_rate_decision'
            GROUP BY date_trunc('week', meeting_date)::DATE
        )
        SELECT dw.week_start, dw.sample_meeting_date, w.banrep_rate_surprise
        FROM decision_weeks dw
        JOIN weekly_panel w ON w.week_start = dw.week_start
        WHERE {_WINDOW_PREDICATE.replace('week_start', 'w.week_start')}
          AND w.banrep_rate_surprise = 0.0
        """
    ).fetchall()
    assert rows == [], (
        f"Decision meetings with zero weekly surprise: {rows}. "
        "Every policy_rate_decision row is derived from a TPM step, so "
        "the IBR change on the effective date should be non-zero. Check "
        "banrep_ibr_daily for the listed dates — missing IBR observations "
        "would be a data-ingestion gap, not a pipeline bug."
    )


# ── 5. Correlation with CPI surprise ──────────────────────────────────────

def test_correlation_with_cpi_surprise_within_bound(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """|corr(banrep_rate_surprise, cpi_surprise_ar1)| < 0.5.

    A severe collinearity between the Banrep monetary-policy surprise and
    the CPI surprise would destroy identification of the latter in the
    Section-5 OLS regression (spec Rev 4 §5.3). The Decision #1 sample
    yields ρ ≈ 0.074, well within the 0.5 ceiling — but if someone later
    re-defines the surprise as (say) "TPM change aligned to the CPI
    release day", correlation could explode. This test is a sanity check,
    not a hypothesis test.
    """
    row = conn.execute(
        f"SELECT CORR(banrep_rate_surprise, cpi_surprise_ar1) "
        f"FROM weekly_panel WHERE {_WINDOW_PREDICATE}"
    ).fetchone()
    assert row is not None
    corr = row[0]
    assert corr is not None, "CORR returned NULL — check for constant columns"
    assert abs(corr) < 0.5, (
        f"corr(banrep_rate_surprise, cpi_surprise_ar1) = {corr} — "
        "|rho| >= 0.5 would signal severe collinearity between the "
        "monetary-policy and CPI-surprise instruments."
    )


# ── 6. Daily/weekly aggregation consistency ───────────────────────────────

# Five spot-check weeks where (a) the meeting_date falls on a TRM trading day
# and (b) the within-week SUM of daily surprises equals the weekly surprise.
# Derived at test-authoring time by finding meetings whose effective-date is
# itself a trading day (no Colombian feriado intervening); for those weeks
# the daily-panel's "assign surprise to first TRM date >= meeting_date"
# convention (econ_panels.py build_daily_panel) collapses to "same day",
# making daily vs weekly aggregation directly comparable.

_CONSISTENCY_CHECK_WEEKS: Final[tuple[date, ...]] = (
    date(2009, 11, 23),  # Mon meeting, -0.460
    date(2012, 1, 30),   # Mon meeting, +0.255
    date(2016, 6, 20),   # Mon meeting, +0.227
    date(2020, 6, 29),   # Mon meeting, -0.265
    date(2022, 3, 28),   # Mon meeting, +0.988 (hike cycle)
    date(2023, 3, 27),   # Mon meeting, +0.216
)


def test_weekly_daily_consistency(conn: duckdb.DuckDBPyConnection) -> None:
    """For 5+ meeting weeks, sum(daily surprise) == weekly surprise.

    The daily panel applies a trading-day-impact convention (research doc
    §8.4): when a meeting_date falls on a ``feriado`` the surprise is
    pushed to the first subsequent TRM trading day, which may spill into
    the next ISO week. The spot-check weeks selected above all have
    meeting_dates that are TRM trading days, so the weekly SUM equals the
    daily SUM exactly.

    This test catches a different class of bug than #3 and #4: a mistaken
    join or re-aggregation in ``build_daily_panel`` that would change the
    per-meeting magnitude without affecting ``build_weekly_panel``.
    """
    assert len(_CONSISTENCY_CHECK_WEEKS) >= 5, (
        "Spot-check set must have at least 5 weeks per test spec."
    )

    rows = conn.execute(
        """
        WITH daily_sum AS (
            SELECT week_start, SUM(banrep_rate_surprise) AS daily_sum
            FROM daily_panel
            GROUP BY week_start
        )
        SELECT w.week_start,
               w.banrep_rate_surprise AS weekly_val,
               d.daily_sum AS daily_val
        FROM weekly_panel w
        JOIN daily_sum d ON d.week_start = w.week_start
        WHERE w.week_start = ANY(?)
        ORDER BY w.week_start
        """,
        [list(_CONSISTENCY_CHECK_WEEKS)],
    ).fetchall()

    assert len(rows) == len(_CONSISTENCY_CHECK_WEEKS), (
        f"Expected {len(_CONSISTENCY_CHECK_WEEKS)} spot-check weeks in both "
        f"panels; got {len(rows)}."
    )

    for week_start, weekly_val, daily_val in rows:
        assert weekly_val is not None and daily_val is not None, (
            f"Week {week_start}: weekly={weekly_val} daily={daily_val}"
        )
        assert abs(weekly_val - daily_val) < 1e-9, (
            f"Consistency failure for week {week_start}: "
            f"weekly={weekly_val} vs daily_sum={daily_val} "
            f"(diff={weekly_val - daily_val})"
        )
