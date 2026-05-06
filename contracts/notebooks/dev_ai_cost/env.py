"""Path constants, version pins, and helpers for the dev-AI Stage-1 simple-β notebooks.

Dev-AI Stage-1 simple-β iteration. Y_p = Colombian young-worker (14-28)
employment share in CIIU Rev.4 Section J (Información y Comunicaciones);
X = log(COP/USD) lagged 6/9/12 months (composite). Sample window 2015-01 →
2026-03 (Pair D Option-α' inheritance), monthly cadence, N = 134 post-lag-12.

This file lives at:
  <worktree_root>/contracts/notebooks/dev_ai_cost/env.py
parents[0] = dev_ai_cost/
parents[1] = notebooks/
parents[2] = contracts/
parents[3] = worktree root

Migrated from contracts/.scratch/dev-ai-stage-1/ on 2026-05-06 per
user directive: "the miss-specifications serve for learning AND give
insights AND the data is preserved for testing new things". Mirrors
fx_vol_cpi_surprise/Colombia/ canonical pattern.

All inter-task artifact paths flow through the constants defined here — no
bare string paths in notebooks. Mirrors the abrigo_y3_x_d/env.py parents-fix
pattern (commit 865402c2c) and the fx_vol_cpi_surprise/Colombia/env.py
3-NB pattern (Pair D Option-β precedent).
"""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Final

# ── Repo-rooted path resolution (parents-fix per 865402c2c precedent) ──────

_NOTEBOOKS_DIR: Final[Path] = Path(__file__).resolve().parent
_NOTEBOOKS_PARENT_DIR: Final[Path] = Path(__file__).resolve().parents[1]
_CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[2]
_WORKTREE_ROOT: Final[Path] = Path(__file__).resolve().parents[3]

# ── Data inputs (Phase 1 outputs from Task 1.1 + Task 1.2 + Task 1.3) ──────

DATA_DIR: Final[Path] = _NOTEBOOKS_DIR / "data"
PANEL_COMBINED_PATH: Final[Path] = DATA_DIR / "panel_combined.parquet"
GEIH_SECTION_J_PATH: Final[Path] = DATA_DIR / "geih_young_workers_section_j_share.parquet"
GEIH_SECTION_M_PATH: Final[Path] = DATA_DIR / "geih_young_workers_section_m_share.parquet"
COP_USD_PANEL_PATH: Final[Path] = DATA_DIR / "cop_usd_panel.parquet"
DATA_PROVENANCE_PATH: Final[Path] = DATA_DIR / "DATA_PROVENANCE.md"

# ── Notebook artifact directories (created by NB on first write) ───────────

ESTIMATES_DIR: Final[Path] = _NOTEBOOKS_DIR / "estimates"
FIGURES_DIR: Final[Path] = _NOTEBOOKS_DIR / "figures"
PDF_DIR: Final[Path] = _NOTEBOOKS_DIR / "pdf"
DISPOSITIONS_DIR: Final[Path] = _NOTEBOOKS_DIR / "dispositions"

# OUTPUT_DIR alias to ESTIMATES_DIR (post-migration backward-compat for NB02 + NB03 cells
# that referenced OUTPUT_DIR pre-migration; kept for re-execution stability)
OUTPUT_DIR: Final[Path] = ESTIMATES_DIR

# ── Inter-notebook handoff files (now in estimates/ per fx_vol convention) ──

PANEL_FINGERPRINT_PATH: Final[Path] = ESTIMATES_DIR / "nb1_panel_fingerprint.json"
PRIMARY_RESULTS_PATH: Final[Path] = ESTIMATES_DIR / "PRIMARY_RESULTS.md"
GATE_VERDICT_PATH: Final[Path] = ESTIMATES_DIR / "gate_verdict.json"
ROBUSTNESS_RESULTS_PATH: Final[Path] = ESTIMATES_DIR / "ROBUSTNESS_RESULTS.md"
ESCALATION_RESULTS_PATH: Final[Path] = ESTIMATES_DIR / "ESCALATION_RESULTS.md"
EA_FRAMEWORK_APPLICATION_PATH: Final[Path] = ESTIMATES_DIR / "EA_FRAMEWORK_APPLICATION.md"
MEMO_PATH: Final[Path] = ESTIMATES_DIR / "MEMO.md"

# ── Notebook paths ─────────────────────────────────────────────────────────

NB1_PATH: Final[Path] = _NOTEBOOKS_DIR / "01_data_eda.ipynb"
NB2_PATH: Final[Path] = _NOTEBOOKS_DIR / "02_estimation.ipynb"
NB3_PATH: Final[Path] = _NOTEBOOKS_DIR / "03_tests_and_sensitivity.ipynb"
REFERENCES_BIB_PATH: Final[Path] = _NOTEBOOKS_DIR / "references.bib"

# ── Spec / plan / Phase 1 commit pins ──────────────────────────────────────

# Spec v1.0.2 — committed at c4e0032a0
SPEC_DECISION_HASH: Final[str] = (
    "7c72292516f58f3cf2d16464d4f84c3e7d7270ad2c5d3d8ed8fef6b3b2751f5a"
)
SPEC_FILE_SHA256: Final[str] = (
    "d90f6302f9473aa938521ed0b7a9b58dc1c849cd74476cd90424f59f3bd3f37e"
)
SPEC_RELPATH: Final[str] = (
    "contracts/docs/superpowers/specs/2026-05-04-dev-ai-stage-1-simple-beta-design.md"
)

# Plan v1.1.1 — committed at 354841f3f
PLAN_FILE_SHA256: Final[str] = (
    "772b52e1f4b4e9e0ed964c3068b1948c24d5cfe27afc109e8e589a1ea790c036"
)
PLAN_RELPATH: Final[str] = (
    "contracts/docs/superpowers/plans/2026-05-04-dev-ai-stage-1-simple-beta-implementation.md"
)

# Phase 1 Gate B1 close commit — Task 1.3 panel_combined.parquet emission
PHASE1_GATE_B1_COMMIT: Final[str] = "627f509b8"

# ── Pair D PASS verdict (precedent inheritance) ────────────────────────────

# Project memory: project_pair_d_phase2_pass
PAIR_D_SPEC_SHA256: Final[str] = (
    "964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659"
)
PAIR_D_BETA_COMPOSITE: Final[float] = 0.13670985
PAIR_D_HAC_SE: Final[float] = 0.02465
PAIR_D_T_STAT: Final[float] = 5.5456
PAIR_D_P_ONE: Final[float] = 1.46e-08

# ── Sample-window pins (per spec §4) ───────────────────────────────────────

SAMPLE_WINDOW_START: Final[str] = "2015-01"
SAMPLE_WINDOW_END: Final[str] = "2026-03"
N_EXPECTED_POST_LAG_12: Final[int] = 134
N_MIN_GATE: Final[int] = 75  # spec §3.6
YOUTH_BAND: Final[tuple[int, int]] = (14, 28)

# ── Required panel schema (verify_panel asserts these columns exist) ──────

REQUIRED_PANEL_COLUMNS: Final[tuple[str, ...]] = (
    "year_month",
    "Y_p_logit",
    "Y_p_raw",
    "Y_s2_logit",
    "Y_s2_raw",
    "log_cop_usd",
    "X_lag6",
    "X_lag9",
    "X_lag12",
    "cell_count_section_j",
    "cell_count_section_m",
)


# ── 4-part citation block helper (per feedback_notebook_citation_block) ────

def citation_block(
    reference: str,
    why_used: str,
    relevance_to_results: str,
    connection_to_simulator: str,
) -> str:
    """Emit a 4-part citation block as a markdown string.

    Per `feedback_notebook_citation_block`: every test/decision/spec choice in
    an estimation or sensitivity notebook is preceded by a 4-part markdown
    block (reference / why used / relevance to results / connection to
    simulator). This helper standardizes the format across NB01/NB02/NB03.

    Use the returned string as the source of a markdown cell.
    """
    return (
        f"**Reference.** {reference}\n\n"
        f"**Why used.** {why_used}\n\n"
        f"**Relevance to results.** {relevance_to_results}\n\n"
        f"**Connection to simulator.** {connection_to_simulator}\n"
    )


# ── Panel-load + verify helper ─────────────────────────────────────────────

def verify_panel():
    """Load `panel_combined.parquet` and assert N + nulls + columns.

    Asserts:
      * row count == N_EXPECTED_POST_LAG_12 (134)
      * total null count == 0
      * column set ⊇ REQUIRED_PANEL_COLUMNS

    Returns the loaded pandas DataFrame on success; raises AssertionError on
    any contract violation. Intended as a sanity-check at the top of NB01 §1.
    """
    import pandas as pd

    df = pd.read_parquet(PANEL_COMBINED_PATH)

    assert len(df) == N_EXPECTED_POST_LAG_12, (
        f"panel row count {len(df)} != expected "
        f"{N_EXPECTED_POST_LAG_12} (spec §3.6)"
    )

    null_total = int(df.isnull().sum().sum())
    assert null_total == 0, (
        f"panel has {null_total} null cells; spec §4 requires 0"
    )

    missing_cols = set(REQUIRED_PANEL_COLUMNS) - set(df.columns)
    assert not missing_cols, (
        f"panel missing required columns: {sorted(missing_cols)}"
    )

    return df


# ── Determinism helper ─────────────────────────────────────────────────────

def pin_seed(seed: int) -> None:
    """Deterministically seed numpy, Python's random, and PYTHONHASHSEED.

    Sets all three seed sources from one integer so every notebook / test
    call chain produces bit-identical draws.

    Note: PYTHONHASHSEED is read only at interpreter startup. Setting it via
    os.environ here affects CHILD processes (nbconvert, subprocess), not the
    current one.
    """
    import numpy as np

    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
