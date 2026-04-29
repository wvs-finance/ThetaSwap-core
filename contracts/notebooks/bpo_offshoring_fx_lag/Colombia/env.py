"""Path constants, version pins, and seed helper for the Pair D simple-β notebooks.

Colombia BPO/non-industrialization-trap empirical-validation exec layer. All
inter-task artifact paths flow through the constants defined here — no bare
string paths in notebooks. Mirrors the canonical pattern at
contracts/notebooks/fx_vol_cpi_surprise/Colombia/env.py.

The numerical results these notebooks reproduce were originally produced by
the script-form execution at scripts/task_2_1_primary_ols.py and
scripts/task_2_2_robustness.py (committed at bce431544). The notebook
re-authoring under Option β (chosen 2026-04-28 PM late evening) honors the
trio-checkpoint discipline per memory feedback_notebook_trio_checkpoint that
the script form did not. The notebooks reproduce the byte-deterministic JSON
outputs already on disk; sha256 round-trip is asserted.

Spec governing these notebooks: 2026-04-27-simple-beta-pair-d-design.md v1.3.1
sha256 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659.

REQUIRED_PACKAGES key convention: keys are the IMPORT name (Python identifier
form, underscores).

pin_seed caveat: Setting os.environ['PYTHONHASHSEED'] from inside a running
interpreter does NOT retroactively alter this process's hash randomization.
It DOES propagate to any child process spawned after the call, which is what
the notebook subprocess workflow needs.
"""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Final

import numpy as np

# ── Repo-rooted path resolution ────────────────────────────────────────────

# This file lives at:
#   <worktree_root>/contracts/notebooks/bpo_offshoring_fx_lag/Colombia/env.py
# parents[0] = Colombia/                (country scope subfolder; mirrors
#                                         fx_vol_cpi_surprise/Colombia/ pattern)
# parents[1] = bpo_offshoring_fx_lag/   (hypothesis name: outcome=BPO offshoring labor
#                                         absorption, driver=FX (COP/USD), qualifier=lag
#                                         (6/9/12 months) — testing whether peso
#                                         devaluation predicts youth BPO absorption)
# parents[2] = notebooks/
# parents[3] = contracts/
# parents[4] = worktree root
_CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[3]
_NB_DIR: Final[Path] = Path(__file__).resolve().parent

# Cross-tree reference: the Phase-1 panel + script-form Phase-2 JSON
# artifacts live under contracts/.scratch/simple-beta-pair-d/ (per the
# original Pair D script-form execution committed at bce431544). The
# notebook layer references those artifacts read-only and asserts sha256
# round-trip; the notebooks' own outputs go to _NB_DIR/estimates/ per the
# canonical pattern.
_PAIR_D_DIR: Final[Path] = _CONTRACTS_DIR / ".scratch" / "simple-beta-pair-d"

# ── Phase-1 panel + Phase-2 results (committed under simple-beta-pair-d/) ──

PANEL_PARQUET: Final[Path] = _PAIR_D_DIR / "data" / "panel_combined.parquet"
PANEL_SHA256: Final[str] = (
    "6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf"
)

PRIMARY_OLS_JSON: Final[Path] = _PAIR_D_DIR / "results" / "primary_ols.json"
PRIMARY_OLS_SHA256: Final[str] = (
    "d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf"
)

ROBUSTNESS_PACK_JSON: Final[Path] = _PAIR_D_DIR / "results" / "robustness_pack.json"
ROBUSTNESS_PACK_SHA256: Final[str] = (
    "67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904"
)

VERDICT_MD: Final[Path] = _PAIR_D_DIR / "results" / "VERDICT.md"
MEMO_MD: Final[Path] = _PAIR_D_DIR / "results" / "MEMO.md"

# ── Notebook artifact directories ──────────────────────────────────────────

ESTIMATES_DIR: Final[Path] = _NB_DIR / "estimates"
FIGURES_DIR: Final[Path] = _NB_DIR / "figures"
PDF_DIR: Final[Path] = _NB_DIR / "pdf"

# ── Inter-notebook handoff files ───────────────────────────────────────────

PANEL_FINGERPRINT_PATH: Final[Path] = ESTIMATES_DIR / "nb1_panel_fingerprint.json"
PRIMARY_RESULTS_PATH: Final[Path] = ESTIMATES_DIR / "PRIMARY_RESULTS.md"
ROBUSTNESS_RESULTS_PATH: Final[Path] = ESTIMATES_DIR / "ROBUSTNESS_RESULTS.md"
GATE_VERDICT_PATH: Final[Path] = ESTIMATES_DIR / "gate_verdict.json"

# ── Auto-rendered README ───────────────────────────────────────────────────

# Named READMEPath (camelCase) to match the established Rule 11 spelling
# from the FX-vol-CPI pipeline. All other path constants are
# SCREAMING_SNAKE_CASE; this one is the documented exception.
READMEPath: Final[Path] = _NB_DIR / "README.md"

# ── Notebook skeletons ─────────────────────────────────────────────────────

NB1_PATH: Final[Path] = _NB_DIR / "01_data_eda.ipynb"
NB2_PATH: Final[Path] = _NB_DIR / "02_estimation.ipynb"
NB3_PATH: Final[Path] = _NB_DIR / "03_tests_and_sensitivity.ipynb"

# ── Spec pin ───────────────────────────────────────────────────────────────

SPEC_PATH: Final[Path] = (
    _CONTRACTS_DIR / "docs" / "superpowers" / "specs"
    / "2026-04-27-simple-beta-pair-d-design.md"
)
SPEC_SHA256: Final[str] = (
    "964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659"
)

# ── nbconvert execution timeout ────────────────────────────────────────────

# 1800 s = 30 min. OLS is fast but bootstrap reconciliation in NB3 can run
# longer on a clean venv.
NBCONVERT_TIMEOUT: Final[int] = 1800

# ── Required packages (major.minor pins) ───────────────────────────────────

# Snapshot taken 2026-04-28 from contracts/.venv on Python 3.13.5.
# Keys use import names (underscores); tests map to dist names where needed.
REQUIRED_PACKAGES: Final[dict[str, str]] = {
    "statsmodels": "0.14",
    "numpy": "2.4",
    "pandas": "3.0",
    "scipy": "1.17",
    "pyarrow": "21.0",
    "jinja2": "3.1",
    "bibtexparser": "1.4",
    "nbformat": "5.10",
    "jupyter": "1.1",
    "matplotlib": "3.10",
}


# ── Determinism helper ─────────────────────────────────────────────────────

def pin_seed(seed: int) -> None:
    """Deterministically seed numpy, Python's random, and PYTHONHASHSEED.

    Sets all three seed sources from one integer so every notebook / test
    call chain produces bit-identical draws.

    Note: PYTHONHASHSEED is read only at interpreter startup. Setting it via
    os.environ here affects CHILD processes (nbconvert, subprocess, etc.),
    not the current one. Intended behavior — do not work around it.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


# ── Spec-pinned numerical constants (read-only mirrors) ────────────────────

SEED: Final[int] = 42
N_EXPECTED: Final[int] = 134
WINDOW_START: Final[str] = "2015-01-31"
WINDOW_END: Final[str] = "2026-02-28"
LAG_SET: Final[tuple[int, ...]] = (6, 9, 12)
NEWEY_WEST_BANDWIDTH_PRIMARY: Final[int] = 4  # ⌊4·(134/100)^(2/9)⌋ = 4
NEWEY_WEST_BANDWIDTH_R4: Final[int] = 12
ALPHA_ONE_SIDED: Final[float] = 0.05
ESCALATE_P_UPPER: Final[float] = 0.20  # spec §3.3 Clause A upper bound
SUBSTRATE_TOO_NOISY_FLIP_THRESHOLD: Final[int] = 3  # spec §3.5
