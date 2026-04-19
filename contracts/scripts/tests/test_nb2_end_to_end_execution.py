"""End-to-end nbconvert execution test for NB2 (`02_estimation.ipynb`).

Companion hardening test to ``test_nb3_end_to_end_execution.py``. Added
after the same class of silent-test-pass bug hit us twice: Task 22 E1
(schema regex failure only surfaced at ``jupyter nbconvert --execute``)
and Task 25 NB3 cell 10 (``NameError: name 'panel' is not defined`` also
only surfaced at ``--execute``). The per-section structural tests in
``test_nb2_section*.py`` all parse the notebook JSON (cell source text,
tags, citation anchors) — none of them actually run the cells end-to-end.
So a NameError inside an NB2 code cell turns into a silent test-pass
green while the PDF-publish pipeline would be red.

This test closes that gap for NB2 by driving the real
``jupyter nbconvert --execute`` pipeline in a subprocess, asserting:

  1. exit code 0 (the notebook runs to completion),
  2. stderr carries no ``NameError`` substring (the specific bug class
     that silently passes structural tests but fails at execute time).

What is NOT asserted:
  * Specific output values in executed cells — those live in the per-
    section tests (test_nb2_section1_2.py, test_nb2_section3.py, etc.).
    This test is deliberately narrow: it only protects against "the
    notebook cannot run at all" regressions.
  * PDF rendering — covered separately by the ``just notebooks`` recipe
    and its test in test_just_notebooks_recipe.py.

Runtime note: this test runs NB2 end-to-end (~5 s on a clean cache —
statsmodels fits are fast at 947 weekly observations; the bottleneck is
the GARCH-X QMLE iteration). Uses ``env.NBCONVERT_TIMEOUT = 1800`` as
the ExecutePreprocessor timeout, matching the timeout the ``just
notebooks`` recipe uses in production. No pytest marker — the codebase
convention (checked across every existing test_nb*.py) is to keep all
tests in the default suite without slow/integration tags.

No mocks — uses the real on-disk notebook, the real DuckDB at
``data/structural_econ.duckdb``, the real NB1 handoff artifact
(``estimates/nb1_panel_fingerprint.json``), and the venv's real
``jupyter`` CLI.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest

# ── Path plumbing (mirrors test_nb3_end_to_end_execution.py) ──────────────

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parents[1]
_CONTRACTS_DIR: Final[Path] = _SCRIPTS_DIR.parent

_ENV_PATH: Final[Path] = (
    _CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "env.py"
)

_NB2_PATH: Final[Path] = (
    _CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "02_estimation.ipynb"
)


def _load_env_module():
    """Load Colombia/env.py as a module without triggering package imports.

    Same pattern used across the NB1/NB2/NB3 structural tests — env.py is
    not packaged, just a file on disk that we exec via importlib.util.
    """
    spec = importlib.util.spec_from_file_location("_fx_vol_env", _ENV_PATH)
    assert spec is not None and spec.loader is not None, (
        f"Could not build importlib spec for {_ENV_PATH}"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Test ───────────────────────────────────────────────────────────────────


def test_nb2_nbconvert_executes_cleanly(tmp_path: Path) -> None:
    """``jupyter nbconvert --to notebook --execute`` runs NB2 cleanly.

    Hard assertions:
      * subprocess returncode == 0
      * stderr does not contain the substring "NameError" (the Task 25
        cell-10 bug class — unbound names that evade source-parsing
        structural tests)
      * executed notebook exists at the output path (sanity check that
        nbconvert reached the write phase)
    """
    # Prerequisite: NB2 is present.
    assert _NB2_PATH.is_file(), (
        f"NB2 notebook missing at {_NB2_PATH}. Cannot run nbconvert."
    )

    # Prerequisite: NB2's §1 reads the NB1 fingerprint handoff + the
    # DuckDB. Without these, NB2 would fail for a reason orthogonal to
    # NameError-class bugs — make that failure mode obvious before
    # invoking nbconvert.
    env_module = _load_env_module()
    assert env_module.FINGERPRINT_PATH.is_file(), (
        f"NB1 fingerprint handoff missing at {env_module.FINGERPRINT_PATH}. "
        f"Run NB1 to regenerate before running this integration test."
    )
    assert env_module.DUCKDB_PATH.is_file(), (
        f"DuckDB missing at {env_module.DUCKDB_PATH}. "
        f"Cannot run NB2 without the source panel."
    )

    output_nb = tmp_path / "nb2_executed.ipynb"

    # Mirror `just notebooks` invocation in production — same jupyter
    # executable, same ExecutePreprocessor timeout, same --to notebook
    # intermediate phase (PDF phase is a separate concern).
    cmd = [
        sys.executable,
        "-m",
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        f"--ExecutePreprocessor.timeout={env_module.NBCONVERT_TIMEOUT}",
        "--output",
        str(output_nb),
        str(_NB2_PATH),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=env_module.NBCONVERT_TIMEOUT + 60,  # hard wall clock
        check=False,
    )

    # Primary assertion: exit code 0.
    assert result.returncode == 0, (
        f"jupyter nbconvert --execute failed on NB2 with returncode "
        f"{result.returncode}.\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{result.stderr}\n"
    )

    # Sharper assertion: the specific bug class we're hardening against.
    assert "NameError" not in result.stderr, (
        f"NB2 nbconvert stderr contains 'NameError' — unbound-name bug "
        f"regressed.\n"
        f"--- stderr ---\n{result.stderr}\n"
    )

    # Sanity: output file landed on disk.
    assert output_nb.is_file(), (
        f"nbconvert reported returncode 0 but output file {output_nb} "
        f"is missing."
    )
