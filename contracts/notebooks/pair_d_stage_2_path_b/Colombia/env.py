"""Path constants, version pins, and seed helper for the Pair D Stage-2 Path B notebooks.

Pair D Stage-2 Path B: on-chain data extraction + structural-exposure
characterization for the Colombian-young-worker BPO/non-industrialization
hedge instrument (CPO M-sketch). Internal ladder v0 (audit) → v1 (CF^a_l) →
v2 (CF^a_s) → v3 (CPO retrospective backtest). Per spec v1.3 CORRECTIONS-γ
the deliverable is structural-exposure characterization NOT WTP / behavioral
demand inference (WTP is a Stage-3 question requiring deployed-pilot
evidence). All notebook prose preserves this framing.

Mirrors the canonical pattern at
contracts/notebooks/bpo_offshoring_fx_lag/Colombia/env.py (Pair D Stage-1).

Spec governing these notebooks:
  contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md
  v1.3 sha256 4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea

Plan governing this layer:
  contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md

Stage-1 sha-pin chain (READ-ONLY through Path B):
  pair_d_spec_v1_3_1: 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659
  panel:              6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf
  primary_ols:        d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf
  robustness_pack:    67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904
  verdict:            1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf

REQUIRED_PACKAGES key convention: keys are the IMPORT name (Python identifier
form, underscores). Per `feedback_real_data_over_mocks` real on-chain data
only — no synthesized data, mocks reserved for HTTP errors that cannot be
reproduced.
"""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Final

import numpy as np

# ── Repo-rooted path resolution ────────────────────────────────────────────

# This file lives at:
#   <worktree_root>/contracts/notebooks/pair_d_stage_2_path_b/Colombia/env.py
# parents[0] = Colombia/                      (country scope subfolder)
# parents[1] = pair_d_stage_2_path_b/         (Stage-2 Path B notebook root)
# parents[2] = notebooks/
# parents[3] = contracts/
# parents[4] = worktree root
_CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[3]
_NB_DIR: Final[Path] = Path(__file__).resolve().parent

# ── Path B working directory (data + DATA_PROVENANCE.md) ───────────────────

# Per spec §4.0: parquet artifacts live at contracts/.scratch/pair-d-stage-2-B/v0/
# Per spec §3.A: per-artifact DATA_PROVENANCE.md mirror discipline
# Note: the plan's working directory is `path-b-stage-2/` (canonical per
# Phase 0 dispatch); the spec §4.0 reference `pair-d-stage-2-B/` is a longer
# variant used only in the spec's own §4.0 prose. The canonical scratch path
# pinned in this env.py is `path-b-stage-2/` (Phase 0 commit-time decision;
# matches the dispatch brief's working directory).
_PATH_B_SCRATCH: Final[Path] = _CONTRACTS_DIR / ".scratch" / "path-b-stage-2"

V0_DIR: Final[Path] = _PATH_B_SCRATCH / "v0"
V1_DIR: Final[Path] = _PATH_B_SCRATCH / "v1"
V2_DIR: Final[Path] = _PATH_B_SCRATCH / "v2"
V3_DIR: Final[Path] = _PATH_B_SCRATCH / "v3"

# ── Phase 0 scaffolding artifacts (created by Task 0.1-0.4) ────────────────

PHASE_0_DIR: Final[Path] = _PATH_B_SCRATCH / "phase-0"
NETWORK_CONFIG_TOML: Final[Path] = PHASE_0_DIR / "network_config.toml"
BURST_RATE_LOG_CSV: Final[Path] = PHASE_0_DIR / "burst_rate_log.csv"
DATA_PROVENANCE_TEMPLATE: Final[Path] = PHASE_0_DIR / "DATA_PROVENANCE.md.template"

# ── Stage-1 sha-pin chain (READ-ONLY through Path B) ───────────────────────

_STAGE_1_DIR: Final[Path] = _CONTRACTS_DIR / ".scratch" / "simple-beta-pair-d"

STAGE_1_PANEL_PARQUET: Final[Path] = _STAGE_1_DIR / "data" / "panel_combined.parquet"
STAGE_1_PANEL_SHA256: Final[str] = (
    "6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf"
)

STAGE_1_PRIMARY_OLS_JSON: Final[Path] = _STAGE_1_DIR / "results" / "primary_ols.json"
STAGE_1_PRIMARY_OLS_SHA256: Final[str] = (
    "d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf"
)

STAGE_1_ROBUSTNESS_PACK_JSON: Final[Path] = _STAGE_1_DIR / "results" / "robustness_pack.json"
STAGE_1_ROBUSTNESS_PACK_SHA256: Final[str] = (
    "67dd18cfeb2584fa6ed9334b1d0314a1a16830faf7c3f3443f07889b9b078904"
)

STAGE_1_VERDICT_MD: Final[Path] = _STAGE_1_DIR / "results" / "VERDICT.md"
STAGE_1_VERDICT_MD_SHA256: Final[str] = (
    "1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf"
)

STAGE_1_SPEC_PATH: Final[Path] = (
    _CONTRACTS_DIR / "docs" / "superpowers" / "specs"
    / "2026-04-27-simple-beta-pair-d-design.md"
)
STAGE_1_SPEC_SHA256_SELF_REFERENTIAL: Final[str] = (
    "964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659"
)

# ── Path B spec + plan pin ─────────────────────────────────────────────────

PATH_B_SPEC_PATH: Final[Path] = (
    _CONTRACTS_DIR / "docs" / "superpowers" / "specs"
    / "2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md"
)
PATH_B_SPEC_SHA256: Final[str] = (
    "4e8905a93b1307d5f9a5b8fe76bcd5de92b6b6493627bcf28d8e8bdf0fdd6bea"
)

PATH_B_PLAN_PATH: Final[Path] = (
    _CONTRACTS_DIR / "docs" / "superpowers" / "plans"
    / "2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md"
)

# ── Notebook artifact directories ──────────────────────────────────────────

ESTIMATES_DIR: Final[Path] = _NB_DIR / "estimates"
FIGURES_DIR: Final[Path] = _NB_DIR / "figures"
PDF_DIR: Final[Path] = _NB_DIR / "pdf"

# ── Notebook skeletons ─────────────────────────────────────────────────────

NB1_PATH: Final[Path] = _NB_DIR / "01_v0_audit.ipynb"
NB2_PATH: Final[Path] = _NB_DIR / "02_v1_cf_al.ipynb"
NB3_PATH: Final[Path] = _NB_DIR / "03_v2_cf_as.ipynb"
NB4_PATH: Final[Path] = _NB_DIR / "04_v3_cpo_backtest.ipynb"
NB5_PATH: Final[Path] = _NB_DIR / "05_convergence_memo.ipynb"

# ── Auto-rendered README (Stage-1 Pair D pattern) ──────────────────────────

# Named READMEPath (camelCase) to match the established Rule 11 spelling
# from the FX-vol-CPI pipeline. All other path constants are
# SCREAMING_SNAKE_CASE; this one is the documented exception.
READMEPath: Final[Path] = _NB_DIR / "README.md"

# ── Network config + burst-rate harness handles ────────────────────────────

# All Phase 1+ network calls MUST honor spec §5.A burst-rate discipline:
#   - SQD Network: ≥250 ms inter-call sleep, concurrency cap = 1 per IP
#   - Alchemy free: ≤25-receipt batches, ≥1 sec inter-batch sleep, concurrency cap = 1
#   - Dune: pre-flight cost-estimate inspection per query
# Exceedance triggers typed exceptions per spec §6:
#   - Stage2PathBSqdNetworkThrottled
#   - Stage2PathBAlchemyFreeTierRateLimitExceeded
#   - Stage2PathBAlchemyFreeTierMonthlyCUExceeded
# Auto-pivot to paid services is anti-fishing-banned (CORRECTIONS-δ).

ALCHEMY_RATE_LIMIT_REQ_PER_SEC: Final[int] = 25
ALCHEMY_RATE_LIMIT_CU_PER_SEC: Final[int] = 500
ALCHEMY_RATE_LIMIT_CU_PER_MONTH: Final[int] = 30_000_000
ALCHEMY_BATCH_SIZE_RECEIPTS_MAX: Final[int] = 25
ALCHEMY_INTER_BATCH_SLEEP_SECONDS_MIN: Final[float] = 1.0

SQD_INTER_CALL_SLEEP_SECONDS_MIN: Final[float] = 0.250
SQD_RATE_LIMIT_REQ_PER_SEC_SUSTAINED: Final[int] = 5
SQD_CHUNK_SIZE_BLOCKS_DEFAULT: Final[int] = 500_000

# ── Spec section pins (anchor references for citation blocks) ──────────────

# Per `feedback_notebook_citation_block` every test/decision/spec choice in an
# estimation/sensitivity notebook is preceded by a 4-part markdown block:
#   (1) reference / (2) why used / (3) relevance to results / (4) connection to simulator
# These constants are the canonical anchors notebooks cite.
SPEC_SECTION_FLAG_B1_R_AL_ESTIMATOR: Final[str] = "spec §3 FLAG-B1"
SPEC_SECTION_FLAG_B2_TRANSFER_LEG: Final[str] = "spec §3 FLAG-B2"
SPEC_SECTION_FLAG_B3_DAILY_BIN: Final[str] = "spec §3 FLAG-B3"
SPEC_SECTION_FLAG_B4_PRICE_LADDER: Final[str] = "spec §3 FLAG-B4"
SPEC_SECTION_FLAG_B5_RECONCILE_CADENCE: Final[str] = "spec §3 FLAG-B5"
SPEC_SECTION_FLAG_B6_REALIZED_VS_IMPLIED: Final[str] = "spec §3 FLAG-B6"
SPEC_SECTION_FLAG_B7_ALLOWLIST: Final[str] = "spec §3 FLAG-B7"
SPEC_SECTION_FLAG_B8_NON_ECON_PARTITION: Final[str] = "spec §3 FLAG-B8"
SPEC_SECTION_FLAG_B9_HANDOFF_SCHEMA: Final[str] = "spec §3 FLAG-B9"
SPEC_SECTION_3A_PROVENANCE: Final[str] = "spec §3.A"
SPEC_SECTION_4_0_V0_SCHEMA: Final[str] = "spec §4.0"
SPEC_SECTION_5_TOOLING_STACK: Final[str] = "spec §5"
SPEC_SECTION_5A_BURST_RATE: Final[str] = "spec §5.A"
SPEC_SECTION_6_HALT_DISCIPLINE: Final[str] = "spec §6"

# ── nbconvert execution timeout ────────────────────────────────────────────

# 3600 s = 60 min. Allows for chunked SQD pulls under sequential discipline
# (e.g., ~25 chunks × ~30 sec/chunk including ≥250 ms inter-call sleep).
NBCONVERT_TIMEOUT: Final[int] = 3600

# ── Required packages (major.minor pins; live snapshot 2026-05-02) ─────────

# Per Task 0.2 contracts/.scratch/path-b-stage-2/phase-0/duckdb_polars_pin.md
REQUIRED_PACKAGES: Final[dict[str, str]] = {
    "duckdb": "1.5",
    "polars": "1.40",
    "pyarrow": "24.0",
    "requests": "2.32",
    "tomli": "2.4",
    "statsmodels": "0.14",
    "numpy": "2.4",
    "pandas": "3.0",
    "sympy": "1.14",
    "matplotlib": "3.10",
    "jinja2": "3.1",
    "nbconvert": "7.17",
    "nbformat": "5.10",
    "jupyter": "1.1",
}


# ── Determinism helper ─────────────────────────────────────────────────────

def pin_seed(seed: int) -> None:
    """Deterministically seed numpy, Python's random, and PYTHONHASHSEED.

    Sets all three seed sources from one integer so every notebook / test
    call chain produces bit-identical draws.

    Note: PYTHONHASHSEED is read only at interpreter startup. Setting it via
    os.environ here affects CHILD processes (nbconvert, subprocess, etc.),
    not the running parent. Notebooks that need deterministic dict iteration
    must dispatch via subprocess after pin_seed() rather than rely on the
    parent process.
    """
    np.random.seed(seed)
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


# ── Sentinels for orchestrator HALT triggers ───────────────────────────────

# Anti-fishing — these typed exceptions per spec §6 are the only legitimate
# ways for Path B execution to deviate from the pre-pinned path. Any informal
# pivot that does not raise one of these is a methodology error.
HALT_EXCEPTIONS: Final[tuple[str, ...]] = (
    "Stage2PathBMentoUSDmCOPmPoolDoesNotExist",
    "Stage2PathBAuditScopeAnomaly",
    "Stage2PathBSqdNetworkCoverageInsufficient",
    "Stage2PathBSqdNetworkThrottled",
    "Stage2PathBAlchemyFreeTierRateLimitExceeded",
    "Stage2PathBAlchemyFreeTierMonthlyCUExceeded",
    "Stage2PathBPublicRPCConsistencyDegraded",
    "Stage2PathBProvenanceMismatch",
    "Stage2PathBALCashFlowContaminated",
    "Stage2PathBASOnChainSignalAbsent",
)
