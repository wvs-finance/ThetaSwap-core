"""Structural regression tests for the ``banrep_meeting_calendar`` table.

The table is the authoritative record of Junta Directiva monetary-policy
meeting dates used by the event-study ``banrep_rate_surprise`` operator
(research doc 2026-04-18 §8.1). It is composed from two sources:

  * ``policy_rate_decision`` rows — derived from TPM-change effective dates
    in the Banrep SDMX ``DF_CBR_DAILY_HIST`` dataflow. These are the literal
    rate-change meetings and are authoritative over 2008-present.
  * ``policy_rate_hold_inferred`` rows — generated from the institutional
    Junta cadence (monthly 2008-2012, 8/year 2013+), de-duplicated by ISO
    week against rate-change meetings.

These tests validate structural invariants of the table itself (schema,
row count, weekday-only, primary-key uniqueness, coverage window, known
category set). Construction-time invariants of the ``banrep_rate_surprise``
derivation live in ``test_banrep_rate_surprise_construction.py``.

No mocks — the tests read the populated ``structural_econ.duckdb`` via the
session-scoped ``conn`` fixture defined in ``conftest.py``.
"""
from __future__ import annotations

from datetime import date
from typing import Final

import duckdb

# ── Known-good category set ───────────────────────────────────────────────

EXPECTED_MEETING_TYPES: Final[frozenset[str]] = frozenset({
    "policy_rate_decision",
    "policy_rate_hold_inferred",
})


# ── Tests ─────────────────────────────────────────────────────────────────

def test_table_exists(conn: duckdb.DuckDBPyConnection) -> None:
    """banrep_meeting_calendar is registered in the DuckDB catalog."""
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    assert "banrep_meeting_calendar" in tables, (
        f"banrep_meeting_calendar missing — tables present: {sorted(tables)}"
    )


def test_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Required columns + types match the DDL in econ_schema.py.

    Required: year SMALLINT, meeting_date DATE, meeting_type VARCHAR.
    Additional columns (e.g. ``_ingested_at``) are permitted — the test
    checks only the required subset so ingestion-metadata evolution does
    not break the contract.
    """
    cols = {
        r[1]: r[2]
        for r in conn.execute(
            "PRAGMA table_info('banrep_meeting_calendar')"
        ).fetchall()
    }
    assert "year" in cols and cols["year"] == "SMALLINT", cols
    assert "meeting_date" in cols and cols["meeting_date"] == "DATE", cols
    assert "meeting_type" in cols and cols["meeting_type"] == "VARCHAR", cols


def test_row_count_reasonable(conn: duckdb.DuckDBPyConnection) -> None:
    """At least 130 meeting rows total across the 2008-present window.

    Floor derivation: 89 rate-change meetings observed in the TPM series
    + at least ~45 hold-inferred rows surviving week-level dedup against
    rate-change meetings. The actual row count at test-authoring time is
    234; the 130-row floor gives ~40% headroom for future dedup changes
    without making the test a snapshot.
    """
    row = conn.execute(
        "SELECT COUNT(*) FROM banrep_meeting_calendar"
    ).fetchone()
    assert row is not None
    count = row[0]
    assert count >= 130, (
        f"banrep_meeting_calendar has only {count} rows — expected >= 130. "
        f"Did the TPM or cadence-model generator misfire?"
    )


def test_no_weekend_meetings(conn: duckdb.DuckDBPyConnection) -> None:
    """Every meeting_date falls on a weekday (Mon-Fri).

    Both sources enforce this:
      * Rate-change rows: TPM effective-date is always a trading day (IBR
        reconciliation runs on settlement days only).
      * Hold-inferred rows: ``_next_trading_day(last_friday_of_month)``
        skips Sat/Sun explicitly (econ_banrep.py).

    A weekend meeting_date would signal a bug in either derivation path.
    """
    rows = conn.execute(
        "SELECT meeting_date, strftime(meeting_date, '%A') AS weekday "
        "FROM banrep_meeting_calendar "
        "WHERE strftime(meeting_date, '%A') IN ('Saturday', 'Sunday')"
    ).fetchall()
    assert rows == [], f"Weekend meeting_dates present: {rows[:5]}"


def test_primary_key_uniqueness(conn: duckdb.DuckDBPyConnection) -> None:
    """(year, meeting_date) is unique — no duplicate meeting rows.

    The DDL declares PRIMARY KEY (year, meeting_date). This test guards
    against future refactors that bypass the constraint (e.g. a bulk
    INSERT that drops the PK via CREATE TABLE AS).
    """
    row = conn.execute(
        "SELECT COUNT(*) FROM ("
        "  SELECT year, meeting_date, COUNT(*) AS c "
        "  FROM banrep_meeting_calendar "
        "  GROUP BY year, meeting_date "
        "  HAVING COUNT(*) > 1"
        ")"
    ).fetchone()
    assert row is not None and row[0] == 0, (
        f"Found {row[0]} (year, meeting_date) duplicates in banrep_meeting_calendar"
    )


def test_date_coverage_full_window(conn: duckdb.DuckDBPyConnection) -> None:
    """Coverage spans at least 2008-H1 through 2025 inclusive.

    The Decision #1 estimation window runs 2008-01-02 → 2026-03-01, so the
    calendar must cover at least 2008-06-01 on the lower side and 2025-12-01
    on the upper side. Tighter bounds would pin the test to the present
    snapshot (2008-01-25 → 2026-04-01) and break whenever either Banrep
    adds a meeting or the cadence model extends.
    """
    row = conn.execute(
        "SELECT MIN(meeting_date), MAX(meeting_date) "
        "FROM banrep_meeting_calendar"
    ).fetchone()
    assert row is not None
    min_d, max_d = row
    assert min_d <= date(2008, 6, 1), (
        f"min(meeting_date)={min_d} — expected <= 2008-06-01"
    )
    assert max_d >= date(2025, 12, 1), (
        f"max(meeting_date)={max_d} — expected >= 2025-12-01"
    )


def test_meeting_types_are_known(conn: duckdb.DuckDBPyConnection) -> None:
    """Every meeting_type value is in the expected category set.

    The ``banrep_rate_surprise`` aggregation in econ_panels.py treats every
    row in banrep_meeting_calendar identically (event-study SUM over
    ΔIBR on the meeting_date). If an unknown meeting_type silently appears
    — for example an ``'emergency_inter_meeting'`` row scraped from a new
    source — this test flags it so downstream semantics can be re-checked
    before the row flows into the panel.
    """
    rows = conn.execute(
        "SELECT DISTINCT meeting_type FROM banrep_meeting_calendar "
        "ORDER BY meeting_type"
    ).fetchall()
    observed = {r[0] for r in rows}
    unexpected = observed - EXPECTED_MEETING_TYPES
    assert not unexpected, (
        f"Unexpected meeting_type categories: {sorted(unexpected)}. "
        f"Expected subset: {sorted(EXPECTED_MEETING_TYPES)}"
    )
