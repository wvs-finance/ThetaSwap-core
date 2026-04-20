"""Pure wrapper around ``econ_query_api`` encoding the 12 locked NB1 Decisions.

This module is the frozen-decision view of the structural econometrics
database that downstream notebooks (NB2 estimation, NB3 sensitivity) and
the Layer 2 simulator consume. Every design choice recorded in NB1 §8's
ledger (Decisions #1 through #12) is embedded here as a module constant,
and the two returned DataFrames are guaranteed to reflect those
Decisions at load time.

Purity contract (enforced by ``tests/test_cleaning_purity.py``):
  * No raw database query tokens anywhere in the source.
  * Every public function flows through at least one ``econ_query_api``
    call before any pandas post-processing.
  * No side effects, no global mutation, no logging, no network I/O.

Determinism contract:
  * For a fixed connection, every public function returns a byte-identical
    DataFrame across runs.
  * The :class:`LockedDecisions` dataclass is frozen, the locked-decision
    instance is a module-level constant, and the derived decision hash is
    a pure function of the dataclass field values.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from datetime import date
from typing import Final

import duckdb
import pandas as pd

from scripts import econ_query_api


# ── Locked Decisions (NB1 §8 ledger) ─────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class LockedDecisions:
    """The 12 locked Decisions from NB1 §8, one field per ledger row.

    Decision #1 is expressed as a closed interval ``[start, end]`` and
    therefore occupies two fields (``sample_window_start`` and
    ``sample_window_end``); Decisions #2 through #12 each map to a
    single field. Total declared fields: 13.

    Every field value is a short descriptive token matching the
    spec-published lock text so the resulting decision hash is
    spec-addressable and stable across reproduction runs.
    """

    # Decision #1 — sample window lock (spec §6 NB1.2; NB1 §3 Trio 3).
    # Primary-estimation sample is 2008-01-02 through 2026-03-01 (closed
    # interval), spanning ~18.2 years and 947 weekly observations.
    sample_window_start: str = "2008-01-02"
    sample_window_end: str = "2026-03-01"

    # Decision #2 — RV estimator / transform lock (spec §6 NB1.3).
    # Primary LHS transform is ``rv_cuberoot`` — the weekly realized
    # variance raised to the 1/3 power (Andersen et al. 2001 convention).
    lhs_transform: str = "rv_cuberoot"

    # Decision #3 — frequency lock (spec §6 NB1.3, Trio 6).
    # Primary estimation is at weekly frequency on ``weekly_panel``; the
    # daily panel is retained as NB3's daily-sensitivity companion.
    frequency: str = "weekly"

    # Decision #4 — CPI surprise specification lock (spec §6 NB1.4).
    # Primary identifying regressor is ``cpi_surprise_ar1`` constructed
    # via ABDV 2003 AR(1) expanding-window on DANE IPC monthly percent
    # changes (Colombia).
    cpi_surprise_spec: str = "cpi_surprise_ar1"

    # Decision #5 — US CPI warmup convention lock (spec §6 NB1.4).
    # US CPI surprise built via AR(1) expanding-window on FRED CPIAUCSL
    # with a 12-month warmup, aligned to week_start via the BLS calendar.
    us_cpi_warmup: str = "us_cpi_surprise_ar1_warmup_12m"

    # Decision #6 — BanRep rate surprise methodology lock (spec §6 NB1.4;
    # research doc 2026-04-18 §8.1). Event-study daily ΔIBR at Junta
    # Directiva policy-decision dates, sign-preserving sum to week_start.
    banrep_rate_surprise_spec: str = "event_study_delta_ibr_meeting_sum"

    # Decision #7 — VIX aggregation convention lock (spec §6 NB1.4).
    # Primary global-risk control is ``vix_avg``, the weekly arithmetic
    # mean of daily VIXCLS (FRED) over Monday-Friday within each ISO week.
    vix_aggregation: str = "vix_avg_weekly_mean"

    # Decision #8 — oil return aggregation convention lock (spec §6 NB1.4).
    # Primary commodity-channel control is ``oil_return``, the weekly
    # log-return of the last positive daily FRED DCOILWTICO close per
    # ISO week.
    oil_aggregation: str = "oil_return_weekly_lastpositive_logret"

    # Decision #9 — intervention regressor form + data-freshness lock
    # (spec §6 NB1.4). Primary Column-6 intervention control is
    # ``intervention_dummy`` — binary any-activity indicator.
    intervention_form: str = "intervention_dummy_any_activity_binary"

    # Decision #10 — collinearity resolution policy lock (spec §6 NB1.5).
    # No adjustment required; all 6 RHS regressors enter at locked forms
    # without orthogonalization (max VIF = 1.04, max |ρ| = 0.14).
    collinearity_policy: str = "none_max_vif_1p04"

    # Decision #11 — stationarity treatment policy lock (spec §6 NB1.6).
    # Primary specification uses levels (no differencing); ADF rejects
    # unit root for all 7 series.
    stationarity_policy: str = "levels_no_differencing"

    # Decision #12 — merge-alignment policy lock (spec §6 NB1.7).
    # Primary merge policy is listwise complete-case drop.
    merge_policy: str = "listwise_complete_case"


# The authoritative, module-level instance — the single source of truth
# that :func:`load_cleaned_panel` and :func:`compute_decision_hash`
# operate on. Frozen dataclass + frozenset of values → safe to share.
LOCKED_DECISIONS: Final[LockedDecisions] = LockedDecisions()


# ── Cleaned-panel payload ────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class CleanedPanel:
    """The frozen-Decision view of the structural econometrics database.

    ``weekly`` carries the primary-estimation weekly panel per Decisions
    #1-#12 (947 rows, zero nulls). ``daily`` carries the companion daily
    sensitivity dataset per Decision #3. ``n_weeks`` is redundant with
    ``len(weekly)`` but exposed separately so downstream consumers can
    assert the 947-row lock without reaching into the DataFrame.
    ``decision_hash`` is the sha256 fingerprint of the LockedDecisions
    field values and must be recorded alongside any derived artifact so
    hash-mismatches surface silently-shifted Decisions during review.
    """

    weekly: pd.DataFrame
    daily: pd.DataFrame
    n_weeks: int
    decision_hash: str


# ── Decision-hash helper ─────────────────────────────────────────────────────


def _compute_decision_hash(locked: LockedDecisions) -> str:
    """Return a sha256 hex digest over the locked-decision field values.

    The hash is computed from the dataclass's ``asdict`` serialization
    with sorted keys, producing a stable 64-character lowercase hex
    string. Mutating any field (via :func:`dataclasses.replace`) flips
    the hash deterministically, so downstream artifacts recording this
    fingerprint reveal any silent Decision drift on verification.
    """
    payload = dataclasses.asdict(locked)
    canonical = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# ── Internal helpers ─────────────────────────────────────────────────────────


def _parse_iso_date(value: str) -> date:
    """Parse an ISO-8601 ``YYYY-MM-DD`` string into a :class:`datetime.date`.

    Pure, stdlib-only, side-effect-free — used to translate the
    :class:`LockedDecisions` window bounds into the ``date`` objects
    that the :mod:`scripts.econ_query_api` helpers expect.
    """
    return date.fromisoformat(value)


def _apply_listwise_complete_case(df: pd.DataFrame) -> pd.DataFrame:
    """Apply Decision #12 listwise complete-case drop.

    Drops any row carrying a NULL in any column, then resets the index
    so downstream consumers see a contiguous ``0..n-1`` integer index.
    Pure — returns a fresh DataFrame, leaves the input untouched.
    """
    return df.dropna(axis=0, how="any").reset_index(drop=True)


# ── Public loader ────────────────────────────────────────────────────────────


def load_cleaned_panel(conn: duckdb.DuckDBPyConnection) -> CleanedPanel:
    """Return the frozen-Decision :class:`CleanedPanel` for the given connection.

    All database access is routed through :mod:`scripts.econ_query_api`;
    this function contains zero raw query patterns (enforced statically
    by :mod:`scripts.tests.test_cleaning_purity`). Every Decision #1-#12
    is embedded via the :data:`LOCKED_DECISIONS` module constant, so
    altering any lock requires editing the dataclass (and thereby
    flipping :attr:`CleanedPanel.decision_hash`).

    Steps:
      1. Parse the Decision #1 sample window bounds.
      2. Pull the weekly panel via
         :func:`econ_query_api.get_weekly_panel` restricted to the window.
      3. Pull the daily panel via
         :func:`econ_query_api.get_daily_panel` restricted to the window.
      4. Apply Decision #12 listwise complete-case drop to the weekly
         panel (primary-estimation surface). The daily panel is
         returned without dropping rows because Decision #12 is scoped
         by the ledger to NB2 Column-6 primary OLS on the weekly panel;
         the daily companion is NB3's A1-sensitivity dataset and
         preserves its native event-density sparsity.
      5. Compute the decision hash and assemble the frozen result.
    """
    start = _parse_iso_date(LOCKED_DECISIONS.sample_window_start)
    end = _parse_iso_date(LOCKED_DECISIONS.sample_window_end)

    weekly_raw = econ_query_api.get_weekly_panel(conn, start=start, end=end)
    daily_raw = econ_query_api.get_daily_panel(conn, start=start, end=end)

    weekly = _apply_listwise_complete_case(weekly_raw)
    # Daily panel is the sensitivity companion; Decision #12 does not
    # apply. Reset index so consumers see a contiguous integer index.
    daily = daily_raw.reset_index(drop=True)

    return CleanedPanel(
        weekly=weekly,
        daily=daily,
        n_weeks=len(weekly),
        decision_hash=_compute_decision_hash(LOCKED_DECISIONS),
    )
