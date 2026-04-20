"""End-to-end nbconvert execution test for NB1 (`01_data_eda.ipynb`).

Third companion in the end-to-end hardening trio (alongside
``test_nb2_end_to_end_execution.py`` and ``test_nb3_end_to_end_execution.py``).
Added after NB1 shipped a cell-3 bootstrap that added ``_COLOMBIA_DIR`` and
``_SCRIPTS_DIR`` to ``sys.path`` but omitted ``_CONTRACTS_DIR`` — the parent
of ``scripts/``. Cell 116 (§8b ledger emission, authored in Task 14) does
``from scripts import cleaning``, which requires ``contracts/`` itself on
``sys.path`` so the ``scripts`` package is resolvable. Under
``jupyter nbconvert --execute`` the kernel starts with no ``contracts/`` on
``sys.path``, cell 116 raises ``ModuleNotFoundError: No module named
'scripts'``, and the entire notebook fails — while the per-section
structural tests (which parse cell source text, not execute it) stay green.
Same silent-test-pass bug class as Task 22 E1 (schema regex failure) and
Task 25 cell 10 (``NameError: name 'panel' is not defined``).

This test closes that gap by driving the real ``jupyter nbconvert --execute``
pipeline on NB1 in a subprocess, asserting:

  1. exit code 0 (the notebook runs to completion),
  2. stderr carries no ``ModuleNotFoundError`` substring (the specific bug
     class this test hardens against),
  3. stderr carries no ``NameError`` substring (the sibling bug class
     covered by the NB2/NB3 companions).

What is NOT asserted here:
  * Specific output values in executed cells — those live in the per-section
    tests (``test_nb1_section1.py``, ``test_nb1_section2.py``, etc.). This
    test is deliberately narrow: it only protects against "the notebook
    cannot run at all" regressions.
  * PDF rendering — covered separately by the ``just notebooks`` recipe
    and its test in ``test_just_notebooks_recipe.py``.

Runtime note: NB1 end-to-end is the cheapest of the trio (~5-15 s — §8b is
the expensive cell and it fingerprints a 947-row weekly panel plus a
~6000-row daily panel). Uses ``env.NBCONVERT_TIMEOUT = 1800`` as the
ExecutePreprocessor timeout, matching the ``just notebooks`` recipe
production timeout. No pytest marker — the codebase convention (checked
across every existing ``test_nb*.py``) is to keep all tests in the default
suite without slow/integration tags.

No mocks — uses the real on-disk notebook, the real DuckDB at
``data/structural_econ.duckdb``, the NB3 sensitivity pre-registration doc
referenced by §8b, and the venv's real ``jupyter`` CLI. If any of those
prerequisite artifacts are missing, the test errors loudly via its
prerequisite assertions before invoking nbconvert — making "missing input"
failures distinguishable from "notebook bug" failures.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest

# ── Path plumbing (mirrors test_nb2/nb3_end_to_end_execution.py) ───────────

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parents[1]
_CONTRACTS_DIR: Final[Path] = _SCRIPTS_DIR.parent

_ENV_PATH: Final[Path] = (
    _CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "env.py"
)

_NB1_PATH: Final[Path] = (
    _CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "01_data_eda.ipynb"
)

_PREREG_DOC_PATH: Final[Path] = (
    _CONTRACTS_DIR
    / ".scratch"
    / "2026-04-18-nb3-sensitivity-preregistration.md"
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


def test_nb1_nbconvert_executes_cleanly(tmp_path: Path) -> None:
    """``jupyter nbconvert --to notebook --execute`` runs NB1 cleanly.

    Hard assertions:
      * subprocess returncode == 0
      * stderr does not contain ``ModuleNotFoundError`` (the specific
        bug class this test hardens against — cell 116 ``from scripts
        import cleaning`` requires ``contracts/`` on ``sys.path``)
      * stderr does not contain ``NameError`` (the sibling bug class
        covered by NB2/NB3 companions)
      * executed notebook exists at the output path (sanity check that
        nbconvert reached the write phase)
    """
    # Prerequisite: NB1 is present.
    assert _NB1_PATH.is_file(), (
        f"NB1 notebook missing at {_NB1_PATH}. Cannot run nbconvert."
    )

    # Prerequisite: NB1 §1 reads the DuckDB; NB1 §8b reads the NB3
    # sensitivity pre-registration doc to compute its tamper-evidence
    # hash. Without either, NB1 would fail for a reason orthogonal to
    # the sys.path bug class — make those failure modes obvious before
    # invoking nbconvert.
    env_module = _load_env_module()
    assert env_module.DUCKDB_PATH.is_file(), (
        f"DuckDB missing at {env_module.DUCKDB_PATH}. "
        f"Cannot run NB1 without the source warehouse."
    )
    assert _PREREG_DOC_PATH.is_file(), (
        f"NB3 sensitivity pre-registration doc missing at "
        f"{_PREREG_DOC_PATH}. NB1 §8b hashes this file; cannot run "
        f"nbconvert without it."
    )

    output_nb = tmp_path / "nb1_executed.ipynb"

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
        str(_NB1_PATH),
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
        f"jupyter nbconvert --execute failed on NB1 with returncode "
        f"{result.returncode}.\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{result.stderr}\n"
    )

    # Sharper assertion #1: the ModuleNotFoundError bug class this
    # test was born to catch — cell 116 ``from scripts import
    # cleaning`` under an incomplete sys.path bootstrap.
    assert "ModuleNotFoundError" not in result.stderr, (
        f"NB1 nbconvert stderr contains 'ModuleNotFoundError' — "
        f"sys.path bootstrap regression. Cell 3 must add "
        f"_CONTRACTS_DIR (parent of scripts/) to sys.path so "
        f"`from scripts import X` resolves.\n"
        f"--- stderr ---\n{result.stderr}\n"
    )

    # Sharper assertion #2: parity with NB2/NB3 end-to-end tests —
    # catch unbound-name bugs that evade source-parsing structural
    # tests (Task 22 E1 / Task 25 cell 10 class).
    assert "NameError" not in result.stderr, (
        f"NB1 nbconvert stderr contains 'NameError' — unbound-name "
        f"bug regressed (see Task 25 cell 10 history).\n"
        f"--- stderr ---\n{result.stderr}\n"
    )

    # Sanity: output file landed on disk.
    assert output_nb.is_file(), (
        f"nbconvert reported returncode 0 but output file {output_nb} "
        f"is missing."
    )
