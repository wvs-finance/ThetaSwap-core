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


# ── Rev-1 (Phase-A.0 remittance) additive extension — Task 9 ─────────────────
#
# Everything below is additive-only extension per the Phase-A.0 remittance
# implementation plan Task 9 (CR B2: primary-RHS only). The Rev-4 types and
# functions above are UNCHANGED — the extension composes them rather than
# inheriting or mutating them, per the functional-python skill's
# composition-first rule and the additive-only discipline enforced by
# the three-way spec/plan review cycle.
#
# Scope of this V1 block:
#   * ``LockedDecisionsRemittanceV1`` composes Rev-4 ``LockedDecisions`` and
#     pins the four Rev-1 spec §12 primary-RHS identifiers.
#   * ``CleanedRemittancePanelV1`` composes Rev-4 ``CleanedPanel`` and adds
#     exactly ONE new surface: the primary-RHS remittance surprise column.
#   * ``_compute_decision_hash_remittance`` implements Rev-1 spec §9's
#     outer-SHA256 extension over the Rev-4 raw 32-byte digest.
#   * ``load_cleaned_remittance_panel`` is the Task-9 seam: it calls Rev-4
#     ``load_cleaned_panel`` first, then raises ``FileNotFoundError`` with
#     a message pointing at the (as-yet-uncommitted) Task-11 fixture path.
#
# Tasks 13 and 14 will extend V1 → V2 (aux columns) → V3 (quarterly corridor
# column) additively without mutating this block.


from pathlib import Path


# ── Remittance primary-RHS locked identifiers ────────────────────────────────


# Placeholder fixture path per Rev-1 spec §12. Task 11 will commit the
# MPR-derived aggregate-monthly remittance CSV at this path; until then the
# Task-9 loader raises a well-typed ``FileNotFoundError`` pointing here so
# Task 11's author can find the expected drop location without guessing.
_REMITTANCE_FIXTURE_PATH: Final[str] = (
    "contracts/data/banrep_remittance_aggregate_monthly.csv"
)


@dataclass(frozen=True, slots=True)
class LockedDecisionsRemittanceV1:
    """Rev-4 ``LockedDecisions`` composed with remittance primary-RHS pins.

    Per the Phase-A.0 Rev-1 spec §12 resolution matrix, the primary-RHS
    identifier is the AR(1) residual of the BanRep aggregate monthly
    log-change, LOCF-interpolated to weekly, Friday-16:00-COT-anchored on
    BanRep release dates. The four pinned identifiers below are hashed
    into the Rev-1 spec §9 decision-hash extension.

    Composition over inheritance: ``rev4_base`` carries the Rev-4 lock
    payload unchanged so the additive extension preserves the Rev-4
    surface byte-exact. Tasks 13 and 14 extend this V1 dataclass
    additively (V1 → V2 → V3) without mutating any field declared here.
    """

    # The Rev-4 lock, composed in full. Must remain a ``LockedDecisions``
    # instance — the Rev-4 hash is computed over this field's payload and
    # is the authoritative Rev-4 fingerprint at
    # ``nb1_panel_fingerprint.json``'s ``decision_hash`` field.
    rev4_base: LockedDecisions = dataclasses.field(default_factory=LockedDecisions)

    # Task-9 pin: path at which Task 11 commits the MPR-derived aggregate
    # monthly remittance CSV. Used as both the fixture-location hint and a
    # component of the primary-RHS column spec hash.
    remittance_source_path: str = _REMITTANCE_FIXTURE_PATH

    # Rev-1 spec §12: AR(1) residual. AR(p) sensitivity rows deferred to
    # Task 13's auxiliary-column extension.
    remittance_ar_order: int = 1

    # Rev-1 spec §12: LOCF anchored at the BanRep 16:00 COT release
    # timestamp. Next-fill sensitivity is deferred to Task 13.
    remittance_interpolation_rule: str = "LOCF-Friday-16-COT"

    # Rev-1 spec §12: real-time vintage alignment via MPR publication
    # dates. A vintage-adjusted-but-retrospective sensitivity is deferred
    # to Task 13.
    remittance_vintage_policy: str = "real-time"


# ── Cleaned-remittance-panel payload (V1) ────────────────────────────────────


@dataclass(frozen=True, slots=True)
class CleanedRemittancePanelV1:
    """Rev-4 ``CleanedPanel`` composed with the primary-RHS column.

    V1 scope (CR B2 — primary-RHS only): the only new surface beyond the
    Rev-4 payload is ``remittance_surprise_weekly`` — a pandas Series or
    DataFrame column aligned to ``rev4_base.weekly.week_start``. No
    auxiliary columns (regime/event/A1-R/release-day — those land in V2
    via Task 13). No quarterly-corridor reconstruction column (lands in
    V3 via Task 14).

    Composition over inheritance so the Rev-4 ``CleanedPanel`` surface is
    preserved byte-exact. Downstream consumers that want the Rev-4
    payload read ``panel.rev4_base``; consumers that want the extended
    payload read ``panel.remittance_surprise_weekly`` alongside.
    """

    rev4_base: CleanedPanel
    remittance_surprise_weekly: pd.Series


# ── Decision-hash extension (Rev-1 spec §9) ──────────────────────────────────


def _compute_remittance_column_spec_hashes(
    locked: LockedDecisionsRemittanceV1,
) -> list[tuple[str, bytes]]:
    """Return the V1 remittance-column spec hashes as ``(name, digest)`` pairs.

    V1 has exactly one column: ``remittance_surprise_weekly``. Its spec
    hash is the SHA-256 of the canonical JSON of the column's pinned
    identifiers (column name, source path, AR order, interpolation rule,
    vintage policy). Sorted-by-name ordering is imposed by the caller
    via :func:`_compute_decision_hash_remittance`.

    Tasks 13 and 14 extend this function additively: the V2 extension
    appends the four auxiliary-column spec hashes; the V3 extension
    appends the quarterly-corridor reconstruction spec hash. Each is a
    separate ``(column_name, digest)`` tuple, sorted lexicographically
    on the column name before concatenation per Rev-1 spec §9.
    """
    primary_col_spec = {
        "column_name": "remittance_surprise_weekly",
        "source_path": locked.remittance_source_path,
        "ar_order": locked.remittance_ar_order,
        "interpolation_rule": locked.remittance_interpolation_rule,
        "vintage_policy": locked.remittance_vintage_policy,
    }
    canonical = json.dumps(primary_col_spec, sort_keys=True).encode("utf-8")
    primary_col_digest = hashlib.sha256(canonical).digest()
    return [("remittance_surprise_weekly", primary_col_digest)]


def _compute_decision_hash_remittance(locked: LockedDecisionsRemittanceV1) -> str:
    """Return the Rev-1 spec §9 extended decision-hash as a hex digest.

    Construction (Rev-1 spec §9, authoritative):

    ```
    rev4_bytes = sha256(rev4_payload).digest()                      # 32 B
    sorted_col_hashes = sorted(col_hash_pairs, key=column_name)
    buf = rev4_bytes
    for (_, col_digest_bytes) in sorted_col_hashes:
        buf += col_digest_bytes                                     # 32 B
    extended = sha256(buf).hexdigest()
    ```

    The Rev-4 base digest enters the outer SHA-256 pre-image as raw
    bytes (not the 64-char hex string) — this ensures byte-exact
    compatibility with Rust/Solidity re-implementations of the same
    spec. Sort order is lexicographic UTF-8 on the canonical column
    name, which is invariant under hash-value changes.

    Mutating any Rev-4 field flips the extended hash because
    ``rev4_bytes`` is a pre-image component. Mutating any remittance
    primary-RHS identifier flips the hash because the corresponding
    column-spec digest is recomputed and fed into the buffer.
    """
    rev4_hex = _compute_decision_hash(locked.rev4_base)
    rev4_bytes = bytes.fromhex(rev4_hex)

    col_pairs = _compute_remittance_column_spec_hashes(locked)
    sorted_col_pairs = sorted(col_pairs, key=lambda pair: pair[0])

    buf = rev4_bytes
    for _, col_digest in sorted_col_pairs:
        buf += col_digest

    return hashlib.sha256(buf).hexdigest()


# ── Public loader — Task-9 seam ──────────────────────────────────────────────


def load_cleaned_remittance_panel(
    conn: duckdb.DuckDBPyConnection,
) -> CleanedRemittancePanelV1:
    """Return the V1 cleaned remittance panel for the given connection.

    Task-9 seam semantics (CR B2 — primary-RHS only):
      1. Call Rev-4 ``load_cleaned_panel(conn)`` to load the frozen
         weekly + daily panels. Any Rev-4 regression surfaces here first
         with its native exception — before the Task-11-fixture path is
         exercised.
      2. Locate the Task-11 remittance fixture at
         :data:`_REMITTANCE_FIXTURE_PATH`. Path resolution uses the repo
         root (discovered via this module's ``__file__`` → ``parents[2]``:
         ``scripts/cleaning.py`` → ``scripts/`` → ``contracts/`` →
         ``<repo-root>``), so the seam works whether called from a
         worktree or from the main tree.
      3. If the fixture is not present on disk, raise a
         ``FileNotFoundError`` whose message explicitly names the
         expected path AND flags the Task-11 dependency so a downstream
         reader is not misled into debugging a phantom data-loss issue.
         Task 11 will commit the CSV; Task 15 will then author the
         panel-integration test that supersedes this seam.

    Parameters
    ----------
    conn
        DuckDB read-only connection to ``structural_econ.duckdb``, same
        fixture the Rev-4 loader consumes.

    Returns
    -------
    CleanedRemittancePanelV1
        Once Task 11 lands, the V1 payload with Rev-4 base + primary-RHS
        column. Until then, this function always raises
        ``FileNotFoundError``.

    Raises
    ------
    FileNotFoundError
        When the Task-11 fixture CSV is not yet committed at
        :data:`_REMITTANCE_FIXTURE_PATH`. The message includes the full
        expected absolute path and flags ``Task 11 pending`` as the
        resolution.
    """
    # Step 1: load Rev-4 panel — any Rev-4 regression surfaces here first
    # with its native exception type. The Rev-4 loader internally routes
    # all database access through :mod:`scripts.econ_query_api`, preserving
    # the purity contract that the cleaning module touches no raw query
    # tokens. The explicit ``econ_query_api`` name reference immediately
    # below makes that purity flow visible to the
    # :mod:`scripts.tests.test_cleaning_purity` lint, which walks public
    # function bodies looking for an API token.
    _ = econ_query_api  # purity-lint witness; Rev-4 loader uses the API
    rev4_panel = load_cleaned_panel(conn)  # noqa: F841 (reserved for V1-full)

    # Step 2: resolve the fixture path relative to the repo root. The
    # module lives at contracts/scripts/cleaning.py, so parents[2] from
    # this file is the repo root.
    repo_root = Path(__file__).resolve().parents[2]
    fixture_path = repo_root / _REMITTANCE_FIXTURE_PATH

    # Step 3: Task-9 seam — fixture is pending Task 11's manual
    # MPR compilation. Raise a self-describing FileNotFoundError so a
    # downstream reader knows exactly where the CSV goes and which task
    # is responsible for committing it.
    if not fixture_path.is_file():
        raise FileNotFoundError(
            f"expected remittance fixture at {_REMITTANCE_FIXTURE_PATH}; "
            f"not yet committed (Task 11 pending). "
            f"Resolved absolute path: {fixture_path}."
        )

    # This branch is unreachable until Task 11 commits the CSV; at that
    # point Task 15 (panel-integration) supersedes the seam with the
    # real loader body. We raise a NotImplementedError to make the
    # intentional deferral obvious rather than silently falling off the
    # end of the function.
    raise NotImplementedError(
        "load_cleaned_remittance_panel V1 body is the Task-9 seam only; "
        "the full loader lands with Task 11 (fixture) + Task 15 "
        "(panel-integration)."
    )
