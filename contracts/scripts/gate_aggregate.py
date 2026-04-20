"""Gate aggregation + atomic emission of the FINAL scientific artifact.

Task 29 of the ``docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md``
plan. This module:

  1. Implements ``build_gate_verdict`` — a pure function taking a
     mapping of per-test verdicts + diagnostics + reconciliation status
     and returning a schema-compliant dict for the final
     ``estimates/gate_verdict.json`` artifact.

  2. Implements ``write_gate_verdict_atomic`` — stages a serialised
     verdict to ``<path>.tmp``, fsyncs the file and its containing
     directory, renames to the final path, then fsyncs the directory
     once more. On rename failure the ``.tmp`` file is cleaned up so
     the filesystem carries no half-written state.

The aggregation rule is fixed per the pre-committed Rev 4 spec:

  * Primary gate = T3b (NB2 §9, one-sided β̂ − 1.28·SE > 0).
  * If T3b fails the final verdict is FAIL regardless of any other
    test — the spec pre-commits T3b as binding.
  * If T3b passes the final verdict requires T1, T2, and T7 to also
    pass. T1 (consensus rationality on the surprise), T2 (Levene
    announcement-channel), and T7 (intervention-dummy adequacy)
    are the three auxiliary gates required alongside the primary.
  * T4 (Ljung-Box), T5 (Jarque-Bera), T6 (Bai-Perron alignment) are
    diagnostic-only. Their FAIL values are recorded in the JSON for
    auditability but they do NOT flip the final verdict. This mirrors
    the plan's design: T4/T5 are addressed by HAC(4) and Student-t
    robustness refits; T6 is descriptive, not gate.
  * T3a (two-sided β ≠ 0) is the two-sided complement to the
    primary one-sided T3b. It is recorded for auditability but does
    not gate.

The module is pure-function + free-function per the ``@functional-python``
skill. ``build_gate_verdict`` does not touch the filesystem; all I/O is
concentrated in ``write_gate_verdict_atomic`` so the aggregation logic
can be unit-tested via synthetic inputs without disk access.

Implementation reference: plan line 541 (Task 29 Step 1 checklist) +
the upstream atomic-emission pattern in ``scripts.nb2_serialize``
(Task 22) which we reuse for the ``.tmp`` → fsync → rename → fsync
directory discipline.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Final, Mapping


# ── Aggregation rule constants ───────────────────────────────────────────

# The primary gate: T3b alone binds the final verdict when it FAILs.
_PRIMARY_GATE_KEY: Final[str] = "t3b_verdict"

# Auxiliary gates required alongside T3b for a PASS final verdict. T1,
# T2, and T7 per plan design — the consensus-rationality + announcement-
# channel + intervention-dummy adequacy triad.
_AUX_GATE_KEYS: Final[tuple[str, ...]] = (
    "t1_verdict",
    "t2_verdict",
    "t7_verdict",
)

# Diagnostic-only verdicts — recorded in the JSON for auditability but
# do not flip the final verdict. T4/T5 are addressed by HAC(4) and
# Student-t refit; T6 is descriptive.
_DIAGNOSTIC_KEYS: Final[tuple[str, ...]] = (
    "t3a_verdict",
    "t4_verdict",
    "t5_verdict",
    "t6_verdict",
)

# Valid categorical token sets.
_PASS_TOKEN: Final[str] = "PASS"
_FAIL_TOKEN: Final[str] = "FAIL"


# ── Pure aggregation function ─────────────────────────────────────────────

def build_gate_verdict(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Assemble the final-artifact dict from per-test + reconciliation inputs.

    Pure function — performs no file I/O.

    Required keys in ``inputs`` (all values are token strings / ints /
    bools as described below):

      * ``t1_verdict``       : ``"PASS"`` | ``"FAIL"`` | ``"SKIPPED"``
      * ``t2_verdict``       : ``"PASS"`` | ``"FAIL"`` | ``"SKIPPED"``
      * ``t3a_verdict``      : REJECT / FAIL TO REJECT / SKIPPED — two-sided
                               β ≠ 0 verdict from NB3 §7. Diagnostic.
      * ``t3b_verdict``      : ``"PASS"`` | ``"FAIL"`` — re-referenced from
                               NB2 §9 one-sided β̂ − 1.28·SE > 0 gate.
                               The PRIMARY gate.
      * ``t4_verdict``       : ``"PASS"`` | ``"FAIL"`` | ``"SKIPPED"`` —
                               Ljung-Box Q(1..8). Diagnostic.
      * ``t5_verdict``       : ``"PASS"`` | ``"FAIL"`` | ``"SKIPPED"`` —
                               Jarque-Bera. Diagnostic.
      * ``t6_verdict``       : ``"PASS"`` | ``"FAIL"`` | ``"SKIPPED"`` —
                               Bai-Perron alignment. Diagnostic.
      * ``t7_verdict``       : ``"PASS"`` | ``"FAIL"`` | ``"SKIPPED"``
      * ``material_movers_count``  : int ≥ 0
      * ``reconciliation``         : ``"AGREE"`` | ``"DISAGREE"``
      * ``bootstrap_hac_agreement``: ``"AGREEMENT"`` | ``"DIVERGENCE"``
      * ``pkl_degraded``           : bool

    The returned dict echoes every input field plus a single synthesised
    ``gate_verdict`` ∈ {``"PASS"``, ``"FAIL"``} built from the binding
    gates (T3b primary + T1/T2/T7 auxiliary).

    Args:
        inputs: Mapping of per-test verdicts and diagnostics. Each
            expected key above MUST be present; a KeyError on access
            is raised (fail-fast) if not, because a silently missing
            verdict would be a bug in the notebook's assembly cell.

    Returns:
        Dict conforming to the gate_verdict.json schema. Key ordering
        is stable (Python 3.7+ insertion order) for reproducible
        downstream rendering.

    Raises:
        KeyError: A required input field is missing.
    """
    # Fail-fast field presence — explicitly dereferencing each expected
    # key surfaces a KeyError at assembly time rather than silently
    # dropping fields from the emitted JSON.
    t1 = str(inputs["t1_verdict"])
    t2 = str(inputs["t2_verdict"])
    t3a = str(inputs["t3a_verdict"])
    t3b = str(inputs["t3b_verdict"])
    t4 = str(inputs["t4_verdict"])
    t5 = str(inputs["t5_verdict"])
    t6 = str(inputs["t6_verdict"])
    t7 = str(inputs["t7_verdict"])
    movers = int(inputs["material_movers_count"])
    recon = str(inputs["reconciliation"])
    boot = str(inputs["bootstrap_hac_agreement"])
    degraded = bool(inputs["pkl_degraded"])

    # ── Aggregation rule ─────────────────────────────────────────────────
    # Primary gate: T3b must PASS.
    # Auxiliary gates: T1, T2, T7 must each PASS.
    # Diagnostic T-series (T3a, T4, T5, T6) do NOT gate.
    per_test_for_rule: dict[str, str] = {
        "t1_verdict": t1,
        "t2_verdict": t2,
        "t3b_verdict": t3b,
        "t7_verdict": t7,
    }
    if per_test_for_rule[_PRIMARY_GATE_KEY] != _PASS_TOKEN:
        final_verdict = _FAIL_TOKEN
    else:
        all_aux_pass = all(
            per_test_for_rule[k] == _PASS_TOKEN for k in _AUX_GATE_KEYS
        )
        final_verdict = _PASS_TOKEN if all_aux_pass else _FAIL_TOKEN

    return {
        "t1_verdict": t1,
        "t2_verdict": t2,
        "t3a_verdict": t3a,
        "t3b_verdict": t3b,
        "t4_verdict": t4,
        "t5_verdict": t5,
        "t6_verdict": t6,
        "t7_verdict": t7,
        "material_movers_count": movers,
        "reconciliation": recon,
        "bootstrap_hac_agreement": boot,
        "pkl_degraded": degraded,
        "gate_verdict": final_verdict,
    }


# ── Atomic write ──────────────────────────────────────────────────────────

def _fsync_dir(dir_path: Path) -> None:
    """fsync the given directory so a rename inside it is durable."""
    dir_fd = os.open(str(dir_path), os.O_DIRECTORY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def write_gate_verdict_atomic(
    verdict: Mapping[str, Any], path: Path
) -> None:
    """Stage → fsync → rename a verdict dict to ``path``.

    The pattern:
      1. Ensure parent directory exists.
      2. Serialise to ``<path>.tmp`` in the same directory (so the
         rename can be atomic on POSIX filesystems — the ``.tmp`` and
         the final path MUST share an inode namespace).
      3. fsync the file bytes.
      4. ``os.replace`` the ``.tmp`` to the final path (atomic on
         POSIX).
      5. fsync the parent directory so the rename itself is durable
         across a power cut.

    On ``os.replace`` failure the ``.tmp`` file is removed (best
    effort) and the OSError propagates. The caller sees no file at
    the final path.

    Args:
        verdict: Mapping to serialise. Must be JSON-encodable (dicts,
            lists, strings, ints, bools, None). The builder
            ``build_gate_verdict`` returns such a dict.
        path: Final destination for the JSON artifact.

    Raises:
        OSError: ``os.replace`` failed (e.g. cross-device link,
            permission denied). The ``.tmp`` is cleaned up best-
            effort before the error propagates.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")

    # Stage.
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(dict(verdict), fh, indent=2, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())

    # Rename (atomic on POSIX).
    try:
        os.replace(str(tmp_path), str(path))
    except Exception:
        # Best-effort cleanup of the staging file so no stale ``.tmp``
        # survives.
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:  # pragma: no cover — best effort
            pass
        raise

    # fsync the containing directory so the rename itself is durable.
    _fsync_dir(path.parent)
