"""End-to-end nbconvert execution test for NB3 (`03_tests_and_sensitivity.ipynb`).

Hardening test added after Task 25 cell 10 shipped with a `NameError: name
'panel' is not defined` that was invisible to every per-section structural
test in the suite. Those tests parse the notebook's JSON (cell source text,
tags, citation anchors) but never actually run the cells end-to-end — so a
NameError inside a code cell turns into a silent test-pass green while
`jupyter nbconvert --execute` is red. Same class as Task 22 E1 (schema regex
failure that also only surfaced at `--execute` time).

This test closes that gap by driving the real `jupyter nbconvert --execute`
pipeline on NB3 in a subprocess, asserting:

  1. exit code 0 (the notebook runs to completion),
  2. stderr carries no `NameError` substring (the specific bug class that
     silently passes structural tests but fails at execute time).

What is NOT asserted here:
  * Specific output values in executed cells — those live in the per-section
    tests (test_nb3_section1_2.py, test_nb3_section3_4.py, etc.). This test
    is deliberately narrow: it only protects against "the notebook cannot
    run at all" regressions.
  * PDF rendering — covered separately by the `just notebooks` recipe and
    its test in test_just_notebooks_recipe.py.

Runtime note: this test is EXPENSIVE (2-5 minutes per invocation — the full
NB3 pipeline including §1 pre-flight, §5 Bai-Perron ruptures fit, §8
specification curve with 13-row refits, and §10 gate aggregation). It uses
`env.NBCONVERT_TIMEOUT = 1800` as the ExecutePreprocessor timeout, matching
the timeout the `just notebooks` recipe uses in production. No pytest
marker — the codebase convention (checked across every existing test_nb*.py)
is to keep all tests in the default suite without slow/integration tags.

No mocks — uses the real on-disk notebook, the real DuckDB at
`data/structural_econ.duckdb`, the real NB2 handoff artifacts under
`notebooks/fx_vol_cpi_surprise/Colombia/estimates/`, and the venv's real
`jupyter` CLI. If any of those prerequisite artifacts are missing, the
test errors loudly via its prerequisite assertions before invoking
nbconvert — making "missing handoff" failures distinguishable from
"notebook bugs" failures.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest

# ── Path plumbing (mirrors test_nb1_section1.py / test_nb2_section1_2.py) ──

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parents[1]
_CONTRACTS_DIR: Final[Path] = _SCRIPTS_DIR.parent

_ENV_PATH: Final[Path] = (
    _CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "env.py"
)

_NB3_PATH: Final[Path] = (
    _CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "03_tests_and_sensitivity.ipynb"
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


def test_nb3_nbconvert_executes_cleanly(tmp_path: Path) -> None:
    """`jupyter nbconvert --to notebook --execute` runs NB3 cleanly.

    Hard assertions:
      * subprocess returncode == 0
      * stderr does not contain the substring "NameError" (the Task 25
        cell-10 / Task 27 §8 bug class — unbound names that evade
        source-parsing structural tests)
      * executed notebook exists at the output path (sanity check that
        nbconvert reached the write phase)
    """
    # Prerequisite: NB3 is present.
    assert _NB3_PATH.is_file(), (
        f"NB3 notebook missing at {_NB3_PATH}. Cannot run nbconvert."
    )

    # Prerequisite: the NB2 handoff artifacts NB3 §1 reads are present.
    # Without these, NB3 would fail for a reason orthogonal to cell-10 /
    # §8 bugs — make that failure mode obvious before invoking nbconvert.
    env_module = _load_env_module()
    assert env_module.POINT_JSON_PATH.is_file(), (
        f"NB2 handoff JSON missing at {env_module.POINT_JSON_PATH}. "
        f"Run NB2 to regenerate before running this integration test."
    )
    assert env_module.FULL_PKL_PATH.is_file(), (
        f"NB2 handoff PKL missing at {env_module.FULL_PKL_PATH}. "
        f"Run NB2 to regenerate before running this integration test."
    )
    assert env_module.DUCKDB_PATH.is_file(), (
        f"DuckDB missing at {env_module.DUCKDB_PATH}. "
        f"Cannot run NB3 without the source panel."
    )

    output_nb = tmp_path / "nb3_executed.ipynb"

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
        str(_NB3_PATH),
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
        f"jupyter nbconvert --execute failed on NB3 with returncode "
        f"{result.returncode}.\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{result.stderr}\n"
    )

    # Sharper assertion: the specific bug class we're hardening against.
    # NameError is what cell 10 produced for `panel` and what §8 produced
    # for `weekly` / `econ_query_api` / `conn`.
    assert "NameError" not in result.stderr, (
        f"NB3 nbconvert stderr contains 'NameError' — unbound-name bug "
        f"regressed (see Task 25 cell 10 / Task 27 §8 history).\n"
        f"--- stderr ---\n{result.stderr}\n"
    )

    # Sanity: output file landed on disk.
    assert output_nb.is_file(), (
        f"nbconvert reported returncode 0 but output file {output_nb} "
        f"is missing."
    )
