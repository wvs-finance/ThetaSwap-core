"""TDD tests for ``scripts/cleaning.py`` — the frozen-decision panel loader.

Task 14 §8a of the econ-notebook-implementation plan. The cleaning module
wraps ``econ_query_api`` and applies the 12 locked Decisions from NB1 §8
to produce the canonical weekly and daily panels NB2/NB3 consume.

These tests are written BEFORE the implementation and MUST fail on
ImportError until ``scripts/cleaning.py`` exists (STRICT TDD red-before-
green discipline). Once the implementation lands, all 10 tests here plus
``test_cleaning_purity.test_real_cleaning_module_is_pure`` must pass.

Scope covered:
  * Dataclass shape — ``CleanedPanel`` returned frozen with the 4
    fields (weekly, daily, n_weeks, decision_hash).
  * Row-count locks — weekly = 947 per Decision #1, daily > 4000 per
    Decision #3 sparsity audit.
  * Column-set locks — exact Decision #4-9 regressor spelling plus the
    LHS transform ``rv_cuberoot`` (Decision #2) and the join key
    ``week_start`` / ``date``.
  * Null policy — zero nulls across every column in the cleaned weekly
    panel (matches §7 Trio 1 listwise-complete-case audit).
  * Decision hash — deterministic across calls, and sensitive to the
    locked-decision values (mutating one flips the hash).
  * LockedDecisions contract — 12 fields exactly matching the 12 locks.
"""
from __future__ import annotations

import dataclasses
from typing import Final

import pytest

from scripts import cleaning
from scripts.cleaning import (
    CleanedPanel,
    LockedDecisions,
    load_cleaned_panel,
)
from scripts.cleaning import _compute_decision_hash as compute_decision_hash

# ── Expected column sets ─────────────────────────────────────────────────────

# Per spec §6 NB1 and Decisions #2, #4-9: the weekly panel exposed to NB2's
# Column-6 primary OLS must carry the RV^{1/3} LHS and the 6 RHS regressors
# at their locked forms. The ``week_start`` key anchors the join.
EXPECTED_WEEKLY_COLUMNS: Final[frozenset[str]] = frozenset({
    "week_start",
    "rv_cuberoot",           # Decision #2 — RV estimator lock
    "cpi_surprise_ar1",      # Decision #4 — CPI surprise spec lock
    "us_cpi_surprise",       # Decision #5 — US CPI warmup lock
    "banrep_rate_surprise",  # Decision #6 — BanRep methodology lock
    "vix_avg",               # Decision #7 — VIX aggregation lock
    "oil_return",            # Decision #8 — oil return lock
    "intervention_dummy",    # Decision #9 — intervention form lock
})

# Per Decision #3 (frequency lock) the daily companion dataset is the
# NB3 daily sensitivity surface. It carries the same Decision #4-9
# variables at daily frequency, keyed on ``date``.
EXPECTED_DAILY_COLUMNS: Final[frozenset[str]] = frozenset({
    "date",
    "cop_usd_return",             # LHS building block at daily frequency
    "cpi_surprise_ar1_daily",     # Decision #4 at daily frequency
    "banrep_rate_surprise",       # Decision #6 at daily frequency
    "vix",                        # Decision #7 at daily frequency
    "oil_return",                 # Decision #8 at daily frequency
    "intervention_dummy",         # Decision #9 at daily frequency
})


# ── Dataclass shape tests ────────────────────────────────────────────────────


def test_load_cleaned_panel_returns_cleaned_panel_dataclass(
    conn: object,
) -> None:
    """``load_cleaned_panel`` returns a frozen ``CleanedPanel`` instance."""
    result = load_cleaned_panel(conn)  # type: ignore[arg-type]
    assert isinstance(result, CleanedPanel), (
        f"expected CleanedPanel; got {type(result).__name__}"
    )
    assert dataclasses.is_dataclass(result), (
        "CleanedPanel must be a dataclass"
    )
    # Frozen check: attempting to mutate a field raises FrozenInstanceError.
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.n_weeks = 0  # type: ignore[misc]


# ── Row-count locks ──────────────────────────────────────────────────────────


def test_weekly_has_947_rows(conn: object) -> None:
    """Decision #1 sample window (2008-01-02 to 2026-03-01) → exactly 947 weeks."""
    result = load_cleaned_panel(conn)  # type: ignore[arg-type]
    assert len(result.weekly) == 947, (
        f"weekly panel row count must be 947 per Decision #1 window; "
        f"got {len(result.weekly)}"
    )
    assert result.n_weeks == 947, (
        f"CleanedPanel.n_weeks must equal 947; got {result.n_weeks}"
    )


def test_daily_has_expected_rows(conn: object) -> None:
    """Daily panel per Decision #3 is sparse but > 4000 trading-day rows."""
    result = load_cleaned_panel(conn)  # type: ignore[arg-type]
    assert len(result.daily) > 4000, (
        f"daily panel must exceed 4000 trading days over the Decision #1 "
        f"window (Decision #3 daily-sensitivity dataset); "
        f"got {len(result.daily)}"
    )


# ── Column-set locks ─────────────────────────────────────────────────────────


def test_weekly_columns_match_decision_set(conn: object) -> None:
    """Weekly panel must contain all Decision-locked columns (superset ok)."""
    result = load_cleaned_panel(conn)  # type: ignore[arg-type]
    actual = frozenset(result.weekly.columns)
    missing = EXPECTED_WEEKLY_COLUMNS - actual
    assert not missing, (
        f"weekly panel missing Decision-locked column(s): {sorted(missing)}; "
        f"present columns: {sorted(actual)}"
    )


def test_daily_columns_match_decision_set(conn: object) -> None:
    """Daily panel must contain all Decision-locked daily-frequency columns."""
    result = load_cleaned_panel(conn)  # type: ignore[arg-type]
    actual = frozenset(result.daily.columns)
    missing = EXPECTED_DAILY_COLUMNS - actual
    assert not missing, (
        f"daily panel missing Decision-locked column(s): {sorted(missing)}; "
        f"present columns: {sorted(actual)}"
    )


# ── Null policy ──────────────────────────────────────────────────────────────


def test_no_nulls_in_weekly(conn: object) -> None:
    """Decision #12 listwise-complete-case merge → 0 nulls across every column."""
    result = load_cleaned_panel(conn)  # type: ignore[arg-type]
    null_counts = result.weekly.isna().sum()
    offenders = {col: int(n) for col, n in null_counts.items() if n > 0}
    assert not offenders, (
        f"weekly panel violates Decision #12 listwise-complete-case: "
        f"columns with nulls = {offenders}"
    )


# ── Decision hash tests ──────────────────────────────────────────────────────


def test_decision_hash_is_deterministic(conn: object) -> None:
    """Same connection → same decision hash across repeated calls."""
    first = load_cleaned_panel(conn)  # type: ignore[arg-type]
    second = load_cleaned_panel(conn)  # type: ignore[arg-type]
    assert first.decision_hash == second.decision_hash, (
        "decision_hash must be deterministic across calls; "
        f"first={first.decision_hash!r}, second={second.decision_hash!r}"
    )
    # Also sanity: hash looks like a sha256 hex digest (64 lowercase hex chars).
    assert len(first.decision_hash) == 64, (
        f"decision_hash must be a sha256 hex digest (64 chars); "
        f"got length {len(first.decision_hash)}"
    )
    assert all(c in "0123456789abcdef" for c in first.decision_hash), (
        f"decision_hash must be lowercase hex; got {first.decision_hash!r}"
    )


def test_decision_hash_reflects_decision_values() -> None:
    """Mutating a locked-decision value changes the hash.

    Uses ``dataclasses.replace`` on a ``LockedDecisions`` instance to
    build a perturbed copy, proving the hash is NOT a constant string but
    is genuinely derived from the Decision values.
    """
    baseline = cleaning.LOCKED_DECISIONS
    assert isinstance(baseline, LockedDecisions), (
        "LOCKED_DECISIONS must be a LockedDecisions instance"
    )
    baseline_hash = compute_decision_hash(baseline)

    # Perturb Decision #1 sample window end by one day. The hash must flip.
    perturbed = dataclasses.replace(baseline, sample_window_end="2026-03-02")
    perturbed_hash = compute_decision_hash(perturbed)

    assert baseline_hash != perturbed_hash, (
        "decision_hash did not change after mutating sample_window_end — "
        "hash must be a function of the LockedDecisions field values"
    )


# ── LockedDecisions contract ─────────────────────────────────────────────────


def test_locked_decisions_sample_window_matches_decision_1() -> None:
    """Decision #1 locks 2008-01-02 → 2026-03-01 (non-negotiable)."""
    locked = cleaning.LOCKED_DECISIONS
    assert locked.sample_window_start == "2008-01-02", (
        f"Decision #1 start must be '2008-01-02'; "
        f"got {locked.sample_window_start!r}"
    )
    assert locked.sample_window_end == "2026-03-01", (
        f"Decision #1 end must be '2026-03-01'; "
        f"got {locked.sample_window_end!r}"
    )


def test_locked_decisions_has_12_entries() -> None:
    """``LockedDecisions`` must declare exactly 12 fields — one per Decision.

    Decision #1 spans two fields (sample_window_start + sample_window_end)
    because the window is a closed interval; the other 11 Decisions map to
    one field each, for a total of 13 fields. The invariant this test
    defends is that the 12 ledger-locked Decisions each have a declared
    home and no extra fields have crept in.
    """
    fields = dataclasses.fields(LockedDecisions)
    field_names = {f.name for f in fields}

    # Every locked Decision (1-12) must be referenced by at least one
    # declared field. The names are matched by substring so minor stylistic
    # variation ("sample_window_start" satisfies Decision #1) is allowed,
    # while an entirely missing Decision is caught.
    expected_decision_tokens = {
        1: "sample_window",
        2: "lhs_transform",
        3: "frequency",
        4: "cpi_surprise",
        5: "us_cpi",
        6: "banrep_rate",
        7: "vix",
        8: "oil",
        9: "intervention",
        10: "collinearity",
        11: "stationarity",
        12: "merge",
    }
    missing = [
        decision_n
        for decision_n, token in expected_decision_tokens.items()
        if not any(token in name for name in field_names)
    ]
    assert not missing, (
        f"LockedDecisions is missing a field for Decision(s) "
        f"{missing}; declared fields: {sorted(field_names)}"
    )
    # Guard against bloat: no more than 13 fields total (12 Decisions with
    # Decision #1 splitting into start/end).
    assert len(fields) == 13, (
        f"LockedDecisions should declare exactly 13 fields "
        f"(12 Decisions with Decision #1 as start+end pair); "
        f"got {len(fields)} fields: {sorted(field_names)}"
    )
