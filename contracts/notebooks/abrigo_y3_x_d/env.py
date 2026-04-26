"""Path constants, version pins, and seed helper for the FX-vol notebooks.

Colombia-scoped structural econometrics exec layer. All inter-task artifact
paths flow through the constants defined here — no bare string paths in
notebooks or tests (Rule 11 of the implementation plan).

Package version pins (REQUIRED_PACKAGES) are recorded at authoring time from
the currently installed venv and are asserted against importlib.metadata on
every test run. Any drift triggers test_required_packages_match_installed_major_minor
and forces an explicit bump here before the mismatch can be committed.

REQUIRED_PACKAGES key convention:
  * Keys are the IMPORT name (Python identifier form, underscores).
  * The only distribution whose pip-install name differs from its import name
    is ``specification_curve`` — on PyPI it is registered as
    ``specification-curve`` (dash). Tests translate via a local map; callers
    reading REQUIRED_PACKAGES get the import-name key directly.

pin_seed caveat:
  Setting ``os.environ['PYTHONHASHSEED']`` from inside a running interpreter
  does NOT retroactively alter this process's hash randomization (which is
  baked in at interpreter startup). It DOES propagate to any child process
  spawned after the call, which is what the notebook subprocess workflow
  needs. Do not rely on PYTHONHASHSEED to stabilize dict iteration in the
  current process — use explicit sorting if determinism matters there.
"""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Final

import numpy as np

# ── Repo-rooted path resolution ────────────────────────────────────────────

# This file lives at:
#   <worktree_root>/contracts/notebooks/abrigo_y3_x_d/env.py
# parents[0] = abrigo_y3_x_d/
# parents[1] = notebooks/
# parents[2] = contracts/
# parents[3] = worktree root
_CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[2]
_ABRIGO_DIR: Final[Path] = Path(__file__).resolve().parent

# ── DuckDB source of truth ─────────────────────────────────────────────────

DUCKDB_PATH: Final[Path] = _CONTRACTS_DIR / "data" / "structural_econ.duckdb"

# ── Artifact directories (Task 1a scaffold) ────────────────────────────────

ESTIMATES_DIR: Final[Path] = _ABRIGO_DIR / "estimates"
FIGURES_DIR: Final[Path] = _ABRIGO_DIR / "figures"
PDF_DIR: Final[Path] = _ABRIGO_DIR / "pdf"

# ── Inter-task handoff files ───────────────────────────────────────────────

FINGERPRINT_PATH: Final[Path] = ESTIMATES_DIR / "nb1_panel_fingerprint.json"
POINT_JSON_PATH: Final[Path] = ESTIMATES_DIR / "nb2_params_point.json"
FULL_PKL_PATH: Final[Path] = ESTIMATES_DIR / "nb2_params_full.pkl"
GATE_VERDICT_PATH: Final[Path] = ESTIMATES_DIR / "gate_verdict.json"

# ── Auto-rendered README ───────────────────────────────────────────────────

# Named READMEPath (camelCase) to match the plan's Rule 11 literal spelling.
# All other path constants are SCREAMING_SNAKE_CASE; this one is the exception.
READMEPath: Final[Path] = _ABRIGO_DIR / "README.md"

# ── Notebook skeletons (Task 1c) ───────────────────────────────────────────

NB1_PATH: Final[Path] = _ABRIGO_DIR / "01_data_eda.ipynb"
NB2_PATH: Final[Path] = _ABRIGO_DIR / "02_estimation.ipynb"
NB3_PATH: Final[Path] = _ABRIGO_DIR / "03_tests_and_sensitivity.ipynb"

# ── nbconvert execution timeout ────────────────────────────────────────────

# 1800 s = 30 min. Required because NB3 bootstrap + specification-curve fits
# can exceed the nbconvert default (600 s) on a clean venv.
NBCONVERT_TIMEOUT: Final[int] = 1800

# ── Required packages (major.minor pins) ───────────────────────────────────

# Snapshot taken 2026-04-17 from contracts/.venv on Python 3.13.5.
# Keys use import names (underscores); tests map to dist names where needed.
REQUIRED_PACKAGES: Final[dict[str, str]] = {
    "statsmodels": "0.14",
    "arch": "8.0",
    "numpy": "2.4",
    "pandas": "3.0",
    "duckdb": "1.5",
    "scipy": "1.17",
    "jinja2": "3.1",
    "bibtexparser": "1.4",
    "specification_curve": "0.3",
    "ruptures": "1.1",
    "nbformat": "5.10",
    "jupyter": "1.1",
    "matplotlib": "3.10",
}


# ── Determinism helper ─────────────────────────────────────────────────────

def pin_seed(seed: int) -> None:
    """Deterministically seed numpy, Python's random, and PYTHONHASHSEED.

    Sets all three seed sources from one integer so every notebook / test
    call chain produces bit-identical draws.

    Note: ``PYTHONHASHSEED`` is read only at interpreter startup. Setting it
    via ``os.environ`` here affects CHILD processes (nbconvert, subprocess,
    etc.), not the current one. Intended behavior — do not work around it.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
