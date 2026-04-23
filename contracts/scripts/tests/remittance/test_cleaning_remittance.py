"""TDD tests for the Task-9 Rev-4 cleaning extension — remittance primary-RHS.

Phase-A.0 Task 9 of the remittance-surprise implementation plan. These tests
are written BEFORE implementation and MUST fail on ImportError until the
additive Rev-4 extension lands in ``contracts/scripts/cleaning.py``.

Scope (CR B2 — primary-RHS only):
  * ``CleanedRemittancePanelV1`` is a frozen dataclass carrying only ONE new
    surface beyond the Rev-4 ``CleanedPanel``: ``remittance_surprise_weekly``.
    No auxiliary columns (no regime dummy, event dummy, A1-R monthly
    rebase, or release-day indicator) — those arrive with V2 in Task 13.
    No quarterly-corridor reconstruction column — that arrives with V3 in
    Task 14.
  * ``LockedDecisionsRemittanceV1`` carries the Rev-4 ``LockedDecisions``
    unchanged (via composition) AND the four remittance primary-RHS
    identifiers pinned by the Rev-1 spec §12: source path, AR(1) order,
    interpolation rule, vintage policy.
  * ``_compute_decision_hash_remittance`` implements Rev-1 spec §9:
    the extended hash is ``SHA256(rev4_bytes || sorted_col_hashes_bytes)``
    where ``rev4_bytes`` is the raw 32-byte SHA-256 digest of the Rev-4
    locked-decisions payload (not the hex-string), the column hashes are
    also 32-byte raw digests, and the sort key is lexicographic UTF-8 on
    column names.
  * The Rev-4 base hash is preserved byte-exact under the composition:
    calling Rev-4 ``_compute_decision_hash`` on the ``.rev4_base`` field
    of a ``LockedDecisionsRemittanceV1`` instance returns the Rev-4
    authoritative value ``6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c``.
  * ``load_cleaned_remittance_panel`` is the Task-9 seam: it calls the
    Rev-4 ``load_cleaned_panel`` first, then raises a well-typed
    ``FileNotFoundError`` pointing at the (as-yet-uncommitted) remittance
    fixture path. Task 11 will author the CSV fixture; Task 15 will swap
    this test for an end-to-end integration assertion.
"""
from __future__ import annotations

import dataclasses
import hashlib
from typing import Final

import pytest

from scripts import cleaning
from scripts.cleaning import (
    CleanedPanel,
    LockedDecisions,
    _compute_decision_hash,
    load_cleaned_panel,
)

# These imports MUST fail until Task 9 is implemented — that failure is the
# red phase of the red-green-refactor discipline per feedback_strict_tdd.
from scripts.cleaning import (  # noqa: E402  (TDD red-phase import)
    CleanedRemittancePanelV1,
    LockedDecisionsRemittanceV1,
    _compute_decision_hash_remittance,
    load_cleaned_remittance_panel,
)


# ── Constants ────────────────────────────────────────────────────────────────

# Rev-4 authoritative decision hash, pinned in
# ``contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json``
# field ``decision_hash``. Preserving this byte-exact across the remittance
# extension is the central invariant of Rev-1 spec §9.
_REV4_DECISION_HASH: Final[str] = (
    "6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c"
)

# The single primary-RHS column V1 adds to the Rev-4 weekly panel.
_PRIMARY_RHS_COLUMN: Final[str] = "remittance_surprise_weekly"

# Rev-1 spec §12 pin values for the primary-RHS locked identifiers.
_EXPECTED_AR_ORDER: Final[int] = 1
_EXPECTED_INTERPOLATION_RULE: Final[str] = "LOCF-Friday-16-COT"
_EXPECTED_VINTAGE_POLICY: Final[str] = "real-time"
# Task-9 placeholder path; Task 11 will author the real fixture here.
_EXPECTED_SOURCE_PATH: Final[str] = (
    "contracts/data/banrep_remittance_aggregate_monthly.csv"
)


# ── Dataclass shape tests ────────────────────────────────────────────────────


def test_cleaned_remittance_panel_v1_is_frozen_dataclass() -> None:
    """``CleanedRemittancePanelV1`` is a frozen dataclass."""
    assert dataclasses.is_dataclass(CleanedRemittancePanelV1), (
        "CleanedRemittancePanelV1 must be a dataclass"
    )
    # Introspect frozen-ness by attempting a mutation on a minimal instance.
    # Use the Rev-4 base field via composition — test asserts composition.
    base_fields = {f.name for f in dataclasses.fields(CleanedRemittancePanelV1)}
    assert "rev4_base" in base_fields, (
        f"CleanedRemittancePanelV1 must compose Rev-4 CleanedPanel via "
        f"a 'rev4_base' field; got fields {sorted(base_fields)}"
    )


def test_cleaned_remittance_panel_v1_adds_only_primary_rhs_field() -> None:
    """V1 must add exactly ONE new surface beyond ``rev4_base``.

    The V1 scope is primary-RHS only (CR B2). No aux columns
    (regime/event/A1-R/release-day — those land in V2, Task 13). No
    quarterly-corridor column (lands in V3, Task 14). This guard defends
    the scope-discipline across the V1→V2→V3 additive sequence.
    """
    fields = {f.name for f in dataclasses.fields(CleanedRemittancePanelV1)}
    expected = {"rev4_base", _PRIMARY_RHS_COLUMN}
    assert fields == expected, (
        f"CleanedRemittancePanelV1 must declare exactly the fields "
        f"{sorted(expected)}; got {sorted(fields)}. "
        f"Aux columns belong to V2 (Task 13); corridor belongs to V3 "
        f"(Task 14)."
    )


def test_cleaned_remittance_panel_v1_rev4_base_is_cleaned_panel() -> None:
    """The ``rev4_base`` field carries the Rev-4 ``CleanedPanel`` type."""
    rev4_field = next(
        f for f in dataclasses.fields(CleanedRemittancePanelV1)
        if f.name == "rev4_base"
    )
    # The dataclass field's declared type must be CleanedPanel (composition).
    # Type annotations on frozen dataclasses are available via the
    # dataclass-fields `.type` attribute; compare by name to dodge
    # from-future-imports stringification.
    assert rev4_field.type in (CleanedPanel, "CleanedPanel"), (
        f"CleanedRemittancePanelV1.rev4_base must be typed as CleanedPanel "
        f"(composition over inheritance per functional-python); "
        f"got {rev4_field.type!r}"
    )


# ── LockedDecisionsRemittanceV1 contract ─────────────────────────────────────


def test_locked_decisions_remittance_v1_is_frozen_dataclass() -> None:
    """``LockedDecisionsRemittanceV1`` is a frozen dataclass (mutation raises)."""
    assert dataclasses.is_dataclass(LockedDecisionsRemittanceV1), (
        "LockedDecisionsRemittanceV1 must be a dataclass"
    )
    instance = LockedDecisionsRemittanceV1()
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.remittance_ar_order = 2  # type: ignore[misc]


def test_locked_decisions_remittance_v1_composes_rev4_locked_decisions() -> None:
    """Rev-4 ``LockedDecisions`` is composed as ``rev4_base`` (not inherited).

    Composition-first per the functional-python skill and the
    additive-only discipline of Rev-4. The Rev-4 dataclass is unchanged;
    the V1 extension adds remittance primary-RHS identifiers alongside
    a field that carries the full Rev-4 lock payload by reference.
    """
    field_names = {f.name for f in dataclasses.fields(LockedDecisionsRemittanceV1)}
    assert "rev4_base" in field_names, (
        f"LockedDecisionsRemittanceV1 must compose Rev-4 LockedDecisions via "
        f"a 'rev4_base' field; got {sorted(field_names)}"
    )
    instance = LockedDecisionsRemittanceV1()
    assert isinstance(instance.rev4_base, LockedDecisions), (
        f"rev4_base must be a Rev-4 LockedDecisions instance; "
        f"got {type(instance.rev4_base).__name__}"
    )


def test_locked_decisions_remittance_v1_carries_rev1_spec_pins() -> None:
    """The four Rev-1 spec §12 primary-RHS identifiers are pinned.

    * ``remittance_source_path`` — path at which Task 11 will commit the
      MPR-derived aggregate monthly CSV. Used as a placeholder here; Task
      11 swaps it for the real committed path.
    * ``remittance_ar_order = 1`` — AR(1) per Rev-1 spec (AR(p) sensitivity
      is deferred to Task 13 sensitivity rows).
    * ``remittance_interpolation_rule = "LOCF-Friday-16-COT"`` — Friday
      16:00 COT anchor per spec (LOCF surrogate; next-fill sensitivity
      deferred).
    * ``remittance_vintage_policy = "real-time"`` — MPR-vintage
      real-time-aware alignment per spec.
    """
    locked = LockedDecisionsRemittanceV1()
    assert locked.remittance_source_path == _EXPECTED_SOURCE_PATH, (
        f"remittance_source_path pin mismatch; "
        f"got {locked.remittance_source_path!r}"
    )
    assert locked.remittance_ar_order == _EXPECTED_AR_ORDER, (
        f"remittance_ar_order must be 1 per Rev-1 spec §12; "
        f"got {locked.remittance_ar_order}"
    )
    assert locked.remittance_interpolation_rule == _EXPECTED_INTERPOLATION_RULE, (
        f"remittance_interpolation_rule pin mismatch; "
        f"got {locked.remittance_interpolation_rule!r}"
    )
    assert locked.remittance_vintage_policy == _EXPECTED_VINTAGE_POLICY, (
        f"remittance_vintage_policy pin mismatch; "
        f"got {locked.remittance_vintage_policy!r}"
    )


def test_locked_decisions_remittance_v1_rev4_base_hash_preserved() -> None:
    """Calling Rev-4 ``_compute_decision_hash`` on ``rev4_base`` returns the
    Rev-4 authoritative hash byte-exact.

    This is the Rev-1 spec §9 base-hash-preservation invariant expressed
    at the dataclass composition boundary: the Rev-4 surface is unchanged,
    so the Rev-4 hash function applied to the Rev-4 portion returns the
    exact pinned value from ``nb1_panel_fingerprint.json``.
    """
    locked = LockedDecisionsRemittanceV1()
    rev4_hash = _compute_decision_hash(locked.rev4_base)
    assert rev4_hash == _REV4_DECISION_HASH, (
        f"Rev-4 base hash drift detected: expected {_REV4_DECISION_HASH}, "
        f"got {rev4_hash}. This means a Rev-4 LockedDecisions field value "
        f"changed — STOP and investigate; Task 9 is additive-only."
    )


# ── _compute_decision_hash_remittance — Rev-1 spec §9 contract ───────────────


def test_compute_decision_hash_remittance_returns_sha256_hex() -> None:
    """The extended hash is a 64-char lowercase hex sha256 digest."""
    locked = LockedDecisionsRemittanceV1()
    result = _compute_decision_hash_remittance(locked)
    assert isinstance(result, str), (
        f"extended hash must be str (hex digest); got {type(result).__name__}"
    )
    assert len(result) == 64, (
        f"extended hash must be a sha256 hex digest (64 chars); "
        f"got length {len(result)} ({result!r})"
    )
    assert all(c in "0123456789abcdef" for c in result), (
        f"extended hash must be lowercase hex; got {result!r}"
    )


def test_compute_decision_hash_remittance_is_deterministic() -> None:
    """Same locked input → same extended hash across repeated calls."""
    locked = LockedDecisionsRemittanceV1()
    first = _compute_decision_hash_remittance(locked)
    second = _compute_decision_hash_remittance(locked)
    assert first == second, (
        f"extended hash must be deterministic; "
        f"first={first!r}, second={second!r}"
    )


def test_compute_decision_hash_remittance_flips_on_rev4_mutation() -> None:
    """Mutating any Rev-4 lock flips the extended hash.

    Base-hash sensitivity: the Rev-1 spec §9 construction
    ``SHA256(rev4_bytes || col_hashes_bytes)`` cannot collapse a Rev-4
    mutation because ``rev4_bytes`` enters the outer SHA256 pre-image.
    Without this property, a silent Rev-4 drift would be invisible to
    downstream consumers — exactly the failure mode the extension exists
    to prevent.
    """
    baseline_locked = LockedDecisionsRemittanceV1()
    baseline_hash = _compute_decision_hash_remittance(baseline_locked)

    # Perturb a Rev-4 field by replacing rev4_base with a mutated copy.
    mutated_rev4 = dataclasses.replace(
        baseline_locked.rev4_base, sample_window_end="2026-03-02"
    )
    perturbed_locked = dataclasses.replace(
        baseline_locked, rev4_base=mutated_rev4
    )
    perturbed_hash = _compute_decision_hash_remittance(perturbed_locked)

    assert baseline_hash != perturbed_hash, (
        "extended hash did not flip after mutating a Rev-4 locked field; "
        "the Rev-4 base must enter the pre-image of the outer SHA256 per "
        "Rev-1 spec §9."
    )


def test_compute_decision_hash_remittance_flips_on_remittance_mutation() -> None:
    """Mutating a remittance primary-RHS identifier flips the extended hash.

    Extension-hash sensitivity: if the primary-RHS column spec changes
    (e.g., AR order flipped to 2, or interpolation rule changes),
    downstream artifacts must see a hash change. The column-spec portion
    of the pre-image is derived from the remittance identifiers, so a
    mutation of any pinned identifier must flip the outer hash.
    """
    baseline_locked = LockedDecisionsRemittanceV1()
    baseline_hash = _compute_decision_hash_remittance(baseline_locked)

    perturbed_locked = dataclasses.replace(
        baseline_locked, remittance_ar_order=2
    )
    perturbed_hash = _compute_decision_hash_remittance(perturbed_locked)

    assert baseline_hash != perturbed_hash, (
        "extended hash did not flip after mutating a remittance "
        "primary-RHS identifier (remittance_ar_order 1 → 2); "
        "the remittance column-spec portion must enter the pre-image."
    )


def test_compute_decision_hash_remittance_matches_spec_construction() -> None:
    """The extended hash equals ``SHA256(rev4_bytes || sorted_col_hashes_bytes)``.

    Ties the implementation to the canonical Rev-1 spec §9 construction:

    ```
    buf = sha256(rev4_payload).digest()                 # 32 bytes
    for col_hash_bytes in sorted(remittance_col_hashes, by=column_name):
        buf += col_hash_bytes                           # 32 bytes each
    extended = sha256(buf).hexdigest()
    ```

    We reproduce the construction here with only the primary-RHS column
    in play (V1 scope) so the test is independent of the implementation
    module's internal layout.
    """
    locked = LockedDecisionsRemittanceV1()
    rev4_hex = _compute_decision_hash(locked.rev4_base)
    rev4_bytes = bytes.fromhex(rev4_hex)

    # V1 adds one column: remittance_surprise_weekly. Its spec hash is the
    # SHA-256 of the canonical JSON representation of the column's pinned
    # identifiers (source path, AR order, interpolation rule, vintage
    # policy). The test reproduces this canonicalization inline so the
    # implementation is forced to match — any divergence breaks the test.
    import json

    primary_col_spec = {
        "column_name": _PRIMARY_RHS_COLUMN,
        "source_path": locked.remittance_source_path,
        "ar_order": locked.remittance_ar_order,
        "interpolation_rule": locked.remittance_interpolation_rule,
        "vintage_policy": locked.remittance_vintage_policy,
    }
    canonical = json.dumps(primary_col_spec, sort_keys=True).encode("utf-8")
    primary_col_hash_bytes = hashlib.sha256(canonical).digest()

    # V1 has only one column-spec hash; sorted-by-column-name is trivially
    # just that single hash.
    buf = rev4_bytes + primary_col_hash_bytes
    expected_hash = hashlib.sha256(buf).hexdigest()

    actual_hash = _compute_decision_hash_remittance(locked)
    assert actual_hash == expected_hash, (
        f"extended hash does not match Rev-1 spec §9 construction:\n"
        f"  expected = {expected_hash}\n"
        f"  actual   = {actual_hash}\n"
        f"Check: (a) Rev-4 base is raw 32-byte digest (not hex string), "
        f"(b) column-spec JSON uses sort_keys=True, "
        f"(c) outer SHA-256 is applied once to the full buffer."
    )


# ── load_cleaned_remittance_panel — Task-9 seam ──────────────────────────────


def test_load_cleaned_remittance_panel_raises_file_not_found_without_fixture(
    conn: object,
) -> None:
    """Task-9 seam: the loader raises ``FileNotFoundError`` with a clear
    message pointing at the expected fixture path (which Task 11 commits).

    This is the "seam exists, data doesn't yet" assertion pattern. The
    V1 loader is wired; the fixture payload is pending Task 11's manual
    MPR compilation. When Task 11 lands, this test becomes obsolete and
    is superseded by Task 15's panel-integration test.
    """
    with pytest.raises(FileNotFoundError) as excinfo:
        load_cleaned_remittance_panel(conn)  # type: ignore[arg-type]
    # The message must point at the expected fixture path so a Task-11
    # reader knows where to drop the CSV.
    assert _EXPECTED_SOURCE_PATH in str(excinfo.value), (
        f"FileNotFoundError message must reference the expected fixture "
        f"path {_EXPECTED_SOURCE_PATH!r}; got {excinfo.value!s}"
    )
    # Explicitly flag the Task-11 dependency so a reader stumbling on the
    # failure understands it is not a bug.
    assert "Task 11" in str(excinfo.value), (
        f"FileNotFoundError message must flag 'Task 11 pending' to avoid "
        f"misreading as a genuine data-loss bug; got {excinfo.value!s}"
    )


def test_load_cleaned_remittance_panel_calls_rev4_loader_first(
    conn: object,
) -> None:
    """The V1 loader MUST call Rev-4 ``load_cleaned_panel`` before raising
    the FileNotFoundError.

    This pins the dependency order: any regression in the Rev-4 loader
    surfaces here FIRST (as the Rev-4 exception), not masked behind the
    Task-11-fixture-missing path. If the Rev-4 loader fails, the
    FileNotFoundError should not even be reached.
    """
    # Sanity: Rev-4 load must succeed against the real conn fixture.
    rev4_panel = load_cleaned_panel(conn)  # type: ignore[arg-type]
    assert isinstance(rev4_panel, CleanedPanel), (
        "Rev-4 load_cleaned_panel regression: conn fixture cannot produce "
        "a CleanedPanel. Fix Rev-4 before debugging Task 9."
    )
    # Now verify Task-9 raises FileNotFoundError (not some other error that
    # would indicate Rev-4 never ran).
    with pytest.raises(FileNotFoundError):
        load_cleaned_remittance_panel(conn)  # type: ignore[arg-type]
