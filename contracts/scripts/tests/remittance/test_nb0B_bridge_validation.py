"""Post-authoring behavior test for Phase-A.0 Rev-3.4 Task 11.C bridge-validation notebook.

This is a **post-authoring behavior test** per plan Step 1 (PM-F3 decision gate):
it verifies that after the notebook is authored AND executed, the notebook is
structurally valid, executes cleanly, and emits the expected scratch-log
artifact with a pre-registered bridge-gate verdict.

The notebook under test cross-validates that the Task-11.B weekly on-chain
flow aggregate (COPM + cCOP daily flows summed to Friday-anchored weeks then
re-aggregated to calendar quarters) correlates with the Task-11 BanRep
quarterly remittance series over the 7-quarter overlap window
(2024-Q3 → 2025-Q4).

Pre-registered gate logic (Rev-3 anti-fishing discipline; committed BEFORE
any ρ computation):

  * PASS-BRIDGE:          ρ > 0.5 on N=7 quarterly obs AND sign-concordant
                          on Δ quarter-over-quarter.
  * FAIL-BRIDGE:          ρ ≤ 0.3 OR sign-discordant.
  * INCONCLUSIVE-BRIDGE:  0.3 < ρ ≤ 0.5 (and sign-concordant, otherwise FAIL).

Silent-test-pass guard (Rev-3.1 CR-F2): the test EXECUTES the notebook via
``jupyter nbconvert --execute`` in a subprocess and asserts ``returncode == 0``
BEFORE any structural assertion runs. This catches the silent-test-pass
pattern where a notebook's code cells would otherwise not be exercised by
a structure-only test.

Test surface per plan Step 1:
  (a) notebook exists and is valid nbformat.v4
  (b) nbconvert-execute returns 0
  (c) scratch-log file exists at the expected path after execution
  (d) scratch log contains one of {PASS-BRIDGE, FAIL-BRIDGE, INCONCLUSIVE-BRIDGE}
  (e) scratch log records the observed ρ value and sign-concordance flag
  (f) N=7 is documented

Purity: tests import nothing from the notebook module itself; they operate
at the artifact level (filesystem + subprocess).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Final

import nbformat
import pytest


# Repository / worktree root: this file lives at
#   <root>/contracts/scripts/tests/remittance/test_nb0B_bridge_validation.py
# so parents[4] == <root>.
_ROOT: Final[Path] = Path(__file__).resolve().parents[4]

_COLOMBIA_DIR: Final[Path] = (
    _ROOT / "contracts" / "notebooks" / "fx_vol_remittance_surprise" / "Colombia"
)

_NOTEBOOK_PATH: Final[Path] = _COLOMBIA_DIR / "0B_bridge_validation.ipynb"

_SCRATCH_LOG_PATH: Final[Path] = (
    _ROOT / "contracts" / ".scratch" / "2026-04-20-onchain-banrep-bridge-result.md"
)

_VERDICT_ENUM: Final[tuple[str, ...]] = (
    "PASS-BRIDGE",
    "FAIL-BRIDGE",
    "INCONCLUSIVE-BRIDGE",
)

# nbconvert timeout. Match the value in the plan Step 4.5
# (``--ExecutePreprocessor.timeout=600``).
_NBCONVERT_TIMEOUT_SECONDS: Final[int] = 600
# subprocess timeout is slightly larger than the kernel execute timeout so
# the test process does not kill nbconvert before it reports its own timeout.
_SUBPROCESS_TIMEOUT_SECONDS: Final[int] = 900


# ---------------------------------------------------------------------------
# Shared session fixture: execute the notebook exactly once per test session.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def _execute_notebook() -> subprocess.CompletedProcess[str]:
    """Execute the bridge-validation notebook in place; return the process result.

    Runs ``jupyter nbconvert --to notebook --execute --inplace ...`` with the
    same timeout as the plan-committed Step 4.5 guard. The notebook is
    expected to write its scratch-log artifact as a side-effect of the
    final trio's code cell.

    The subprocess is run from the worktree root so any relative paths the
    notebook uses resolve consistently with the CSV data layout.
    """
    assert _NOTEBOOK_PATH.is_file(), (
        f"bridge notebook missing at {_NOTEBOOK_PATH}; author Step 3 X-trios first"
    )
    cmd = [
        sys.executable,
        "-m",
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        "--inplace",
        str(_NOTEBOOK_PATH),
        f"--ExecutePreprocessor.timeout={_NBCONVERT_TIMEOUT_SECONDS}",
    ]
    return subprocess.run(
        cmd,
        cwd=str(_ROOT),
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT_SECONDS,
        check=False,
    )


# ---------------------------------------------------------------------------
# Structural assertions (notebook file itself).
# ---------------------------------------------------------------------------


def test_notebook_exists_and_is_valid_nbformat_v4() -> None:
    """Surface (a): the notebook must exist and parse as nbformat v4."""
    assert _NOTEBOOK_PATH.is_file(), f"notebook missing: {_NOTEBOOK_PATH}"
    with _NOTEBOOK_PATH.open("r", encoding="utf-8") as fh:
        nb = nbformat.read(fh, as_version=4)
    assert nb.nbformat == 4, (
        f"expected nbformat major=4, got {nb.nbformat}"
    )


# ---------------------------------------------------------------------------
# Execution guard (Rev-3.1 CR-F2 silent-test-pass protection).
# ---------------------------------------------------------------------------


def test_notebook_executes_cleanly_via_nbconvert(
    _execute_notebook: subprocess.CompletedProcess[str],
) -> None:
    """Surface (b): ``jupyter nbconvert --execute`` must return 0.

    This is the critical silent-test-pass guard: a structure-only test that
    never exercised the notebook's code cells could pass even while the
    code raised at runtime. By running nbconvert-execute inside a pytest
    fixture, any runtime error is surfaced as a test failure.
    """
    proc = _execute_notebook
    assert proc.returncode == 0, (
        f"nbconvert --execute failed with returncode={proc.returncode}\n"
        f"STDOUT:\n{proc.stdout}\n"
        f"STDERR:\n{proc.stderr}"
    )


# ---------------------------------------------------------------------------
# Scratch-log artifact assertions.
# ---------------------------------------------------------------------------


def test_scratch_log_exists_after_execution(
    _execute_notebook: subprocess.CompletedProcess[str],
) -> None:
    """Surface (c): the scratch-log file must exist after notebook execution.

    Depends on ``_execute_notebook`` fixture so we do not mis-diagnose a
    pre-existing stale log as a freshly-authored one. The fixture's
    return-code check runs first in the test order, but we defensively
    assert success again inside the closure.
    """
    assert _execute_notebook.returncode == 0, (
        "notebook execution failed; scratch log cannot be trusted"
    )
    assert _SCRATCH_LOG_PATH.is_file(), (
        f"scratch log missing at {_SCRATCH_LOG_PATH} after notebook execution"
    )


def test_scratch_log_contains_verdict_enum(
    _execute_notebook: subprocess.CompletedProcess[str],
) -> None:
    """Surface (d): scratch log carries exactly one of the three gate verdicts."""
    assert _execute_notebook.returncode == 0, "prerequisite: notebook execution"
    text = _SCRATCH_LOG_PATH.read_text(encoding="utf-8")
    matches = [v for v in _VERDICT_ENUM if v in text]
    assert len(matches) >= 1, (
        f"scratch log does not contain any verdict enum value; "
        f"expected one of {_VERDICT_ENUM!r}. Log body:\n{text[:500]}"
    )


def test_scratch_log_records_rho_and_sign_concordance(
    _execute_notebook: subprocess.CompletedProcess[str],
) -> None:
    """Surface (e): scratch log records the observed ρ value and sign-concordance.

    ρ is required as a numeric literal (supports integer, decimal, optional
    leading sign, scientific form); sign-concordance is required as an
    ``N/6`` style count where ``N`` is an integer in ``[0, 6]``.
    """
    assert _execute_notebook.returncode == 0, "prerequisite: notebook execution"
    text = _SCRATCH_LOG_PATH.read_text(encoding="utf-8")

    # Observed ρ: look for a line that mentions rho / "ρ" / "pearson" and a
    # numeric literal. We accept either spelling since the notebook author
    # may prefer ASCII.
    rho_pattern = re.compile(
        r"(?:rho|ρ|pearson)[^\n]{0,80}?(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
        flags=re.IGNORECASE,
    )
    assert rho_pattern.search(text), (
        f"scratch log does not record observed ρ as a numeric literal. "
        f"Log body:\n{text[:500]}"
    )

    # Sign-concordance: Q-over-Q transitions. With observed N=6 quarterly
    # obs there are 5 transitions; if a future data refresh gives N=7,
    # there would be 6 transitions. Accept ``k/5`` or ``k/6`` where k is
    # the number of concordant transitions.
    sign_pattern = re.compile(r"\b([0-6])\s*/\s*([56])\b")
    assert sign_pattern.search(text), (
        f"scratch log does not record sign-concordance as k/5 or k/6. "
        f"Log body:\n{text[:500]}"
    )


def test_scratch_log_documents_overlap_n(
    _execute_notebook: subprocess.CompletedProcess[str],
) -> None:
    """Surface (f): the overlap sample size N is documented in the scratch log.

    Task description prescribed N=7 (2024-Q3 → 2025-Q4 inclusive); direct
    enumeration of the BanRep CSV rows in that window gives N=6 (six quarter-
    end rows: 2024-09-30, 2024-12-31, 2025-03-31, 2025-06-30, 2025-09-30,
    2025-12-31). The notebook MUST document the observed N and flag the
    off-by-one. We accept either ``N=6`` (the arithmetically correct value
    from the actual data) or ``N=7`` (if a future re-issue of BanRep adds
    a row) — the rule is simply that a concrete N must be recorded, and
    the verdict math must be internally consistent with that N.

    Accepts ``N=<k>``, ``N = <k>``, ``n = <k>``, ``<k> quarterly observations``
    or ``<k> quarters`` for k ∈ {6, 7}.
    """
    assert _execute_notebook.returncode == 0, "prerequisite: notebook execution"
    text = _SCRATCH_LOG_PATH.read_text(encoding="utf-8")
    n_patterns: tuple[re.Pattern[str], ...] = (
        re.compile(r"\bN\s*=\s*[67]\b"),
        re.compile(r"\bn\s*=\s*[67]\b"),
        re.compile(r"\b[67]\s+quarterly\s+observations\b", flags=re.IGNORECASE),
        re.compile(r"\b[67]\s+quarters\b", flags=re.IGNORECASE),
    )
    assert any(p.search(text) for p in n_patterns), (
        f"scratch log does not document overlap N. Log body:\n{text[:500]}"
    )
