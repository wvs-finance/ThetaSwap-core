"""Path constants, version pins, and seed helper for the Pair D Stage-2 Path A notebooks.

Path A = fork-and-simulate verification track for the Pair D Convex Payoff
Option (CPO) M-sketch. The internal ladder is v0 (sympy mathematics, no
contracts) → v1 (Mento V3 + Uniswap V3 forked Celo) → v2 (Panoptic IronCondor
strip forked Ethereum, 3 condors / 12 legs) → v3 (stochastic-σ MC with GBM
baseline, ≥1000 paths). Each rung is hosted in one of the four notebook
skeletons named by NB_*_PATH below.

This env module mirrors the canonical pattern at
contracts/notebooks/bpo_offshoring_fx_lag/Colombia/env.py (Stage-1 PASS notebooks)
and contracts/notebooks/abrigo_y3_x_d/env.py (parents-fix convention).

Spec governing these notebooks: 2026-04-30-pair-d-stage-2-A-fork-simulate-spec.md v1.2.1
sha256 1a4cc6a41b864deec5702866dd3e8badc8a5eac5e259f61f41b93d233b3f9d78.

Plan governing these notebooks: 2026-04-30-pair-d-stage-2-A-fork-simulate-implementation.md
sha256 05f5216faa62b7a3cccb384215d5da007636d87d2b6d9597a21cb42b4860436d.

Stage-1 anchor (READ-ONLY input, NOT a re-test target):
- VERDICT.md sha256: 1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf

REQUIRED_PACKAGES key convention: keys are the IMPORT name (Python identifier
form, underscores).

pin_seed caveat: Setting os.environ['PYTHONHASHSEED'] from inside a running
interpreter does NOT retroactively alter this process's hash randomization.
It DOES propagate to any child process spawned after the call, which is what
the notebook subprocess workflow needs. Per spec §10.3, v3 stochastic MC must
use numpy.random.default_rng(seed=...) — NOT legacy numpy.random.seed() —
because legacy global state leaks across modules. pin_seed is an
orchestration convenience for non-MC determinism only; v3 NBs MUST instantiate
default_rng directly.
"""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Final

import numpy as np

# ── Repo-rooted path resolution ────────────────────────────────────────────

# This file lives at:
#   <worktree_root>/contracts/notebooks/pair_d_stage_2_path_a/Colombia/env.py
# parents[0] = Colombia/                     (country scope subfolder)
# parents[1] = pair_d_stage_2_path_a/        (Stage-2 Path A track)
# parents[2] = notebooks/
# parents[3] = contracts/
# parents[4] = worktree root
_CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[3]
_NB_DIR: Final[Path] = Path(__file__).resolve().parent

# Cross-tree reference: Path A scratch root (Phase-0 onwards). Phase-0
# Foundry pin + smoke test artifacts are fixed inputs to v1 / v2 / v3
# manifests downstream.
_PATH_A_SCRATCH_DIR: Final[Path] = (
    _CONTRACTS_DIR / ".scratch" / "path-a-stage-2"
)

# Cross-tree reference: Stage-1 PASS pinned chain (READ-ONLY anchor;
# Path A v0/v1/v2/v3 do NOT re-test Stage-1 numerics).
_STAGE1_DIR: Final[Path] = _CONTRACTS_DIR / ".scratch" / "simple-beta-pair-d"

# ── Phase 0 inputs (fixed once committed) ──────────────────────────────────

FOUNDRY_PIN_PATH: Final[Path] = _PATH_A_SCRATCH_DIR / "phase-0" / "foundry_pin.md"
ENV_SMOKE_TEST_PATH: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "phase-0" / "environment_smoke_test.md"
)
DATA_PROVENANCE_PATH: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "phase-0" / "DATA_PROVENANCE.md"
)

# ── Stage-1 PASS anchor (read-only) ────────────────────────────────────────

STAGE1_VERDICT_MD: Final[Path] = _STAGE1_DIR / "results" / "VERDICT.md"
STAGE1_VERDICT_SHA256: Final[str] = (
    "1efd0e34d7c1af821c8528a7bc895a63e1dc5e1c289f3b6a1b2d392ba59806cf"
)
STAGE1_PRIMARY_OLS_JSON: Final[Path] = _STAGE1_DIR / "results" / "primary_ols.json"
STAGE1_PRIMARY_OLS_SHA256: Final[str] = (
    "d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf"
)

# ── Imported CPO framework note (read-only) ────────────────────────────────

CPO_FRAMEWORK_PATH: Final[Path] = (
    _CONTRACTS_DIR / "notes" / "2026-04-29-macro-markets-draft-import.md"
)

# ── Per-version output directories (Phase 1-4 will populate) ───────────────

ESTIMATES_DIR: Final[Path] = _NB_DIR / "estimates"
FIGURES_DIR: Final[Path] = _NB_DIR / "figures"
PDF_DIR: Final[Path] = _NB_DIR / "pdf"

# ── v0 outputs (Phase 1) ───────────────────────────────────────────────────

V0_DELTA_PKL_PATH: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "results" / "path_a_v0_delta_expressions.pkl"
)
V0_DERIVATION_PKL_PATH: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "results" / "path_a_v0_derivation.pkl"
)
V0_DERIVATION_TEX_PATH: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "results" / "path_a_v0_derivation.tex"
)
V0_EXIT_REPORT_PATH: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "results" / "path_a_v0_exit_report.md"
)

# ── v1 outputs (Phase 2) ───────────────────────────────────────────────────

V1_FORK_MANIFEST_PATH: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "results" / "path_a_v1_fork_manifest.md"
)
V1_HARNESS_CSV_PATH: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "results" / "path_a_v1_harness.csv"
)
V1_RECONCILIATION_PATH: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "results" / "path_a_v1_reconciliation.md"
)

# ── v2 outputs (Phase 3) ───────────────────────────────────────────────────

V2_FORK_MANIFEST_PATH: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "results" / "path_a_v2_fork_manifest.md"
)
V2_STRIP_CONFIG_JSON_PATH: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "results" / "path_a_v2_strip_config.json"
)
V2_PREMIUM_TIMESERIES_CSV_PATH: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "results" / "path_a_v2_premium_timeseries.csv"
)
V2_FIT_PATH: Final[Path] = _PATH_A_SCRATCH_DIR / "results" / "path_a_v2_fit.md"

# ── v3 outputs (Phase 4) ───────────────────────────────────────────────────

V3_REPRODUCIBILITY_MANIFEST_PATH: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "results" / "path_a_v3_reproducibility_manifest.md"
)
V3_MC_DISTRIBUTIONS_DIR: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "results" / "path_a_v3_mc_distributions"
)
V3_ENVELOPE_COVERAGE_PATH: Final[Path] = (
    _PATH_A_SCRATCH_DIR / "results" / "path_a_v3_envelope_coverage.md"
)

# ── Notebook skeletons (Task 0.2) ──────────────────────────────────────────

NB_V0_SYMPY_PATH: Final[Path] = _NB_DIR / "01_v0_sympy.ipynb"
NB_V1_MENTO_FORK_PATH: Final[Path] = _NB_DIR / "02_v1_mento_fork.ipynb"
NB_V2_PANOPTIC_STRIP_PATH: Final[Path] = _NB_DIR / "03_v2_panoptic_strip.ipynb"
NB_V3_GBM_MC_PATH: Final[Path] = _NB_DIR / "04_v3_gbm_mc.ipynb"

# ── Spec + plan pin ────────────────────────────────────────────────────────

SPEC_PATH: Final[Path] = (
    _CONTRACTS_DIR / "docs" / "superpowers" / "specs"
    / "2026-04-30-pair-d-stage-2-A-fork-simulate-spec.md"
)
SPEC_SHA256: Final[str] = (
    "1a4cc6a41b864deec5702866dd3e8badc8a5eac5e259f61f41b93d233b3f9d78"
)
SPEC_VERSION: Final[str] = "v1.2.1"

PLAN_PATH: Final[Path] = (
    _CONTRACTS_DIR / "docs" / "superpowers" / "plans"
    / "2026-04-30-pair-d-stage-2-A-fork-simulate-implementation.md"
)
PLAN_SHA256: Final[str] = (
    "05f5216faa62b7a3cccb384215d5da007636d87d2b6d9597a21cb42b4860436d"
)

# ── Foundry / Anvil pin (Task 0.1 source-of-truth) ─────────────────────────

# Pinned at Phase 0 Task 0.1; re-cited by every fork-using version manifest
# downstream per spec §10.2 (commit hash is the determinism anchor).
FOUNDRY_COMMIT_SHA: Final[str] = "b0a9dd9ceda36f63e2326ce530c10e6916f4b8a2"
FOUNDRY_VERSION_TAG: Final[str] = "1.5.1-stable"

# ── Free-tier RPC ladder (per spec §10.1 + Task 0.1 reachability matrix) ───

# Celo: PRIMARY = Alchemy free (currently NOT enabled on local app — see
# Phase-0 Task 0.1 environment_smoke_test.md §6 Surface-1); FALLBACK = Forno
# (verified reachable, requires custom User-Agent for Python urllib clients).
RPC_CELO_FALLBACK: Final[str] = "https://forno.celo.org"
RPC_CELO_PRIMARY_TEMPLATE: Final[str] = (
    "https://celo-mainnet.g.alchemy.com/v2/{api_key}"
)

# Ethereum: PRIMARY = Alchemy free (verified reachable); FALLBACK =
# eth.llamarpc.com (verified reachable). Public Ankr no longer free without
# API key as of 2026-05-02 — spec §5 enumeration partially stale.
RPC_ETH_FALLBACK: Final[str] = "https://eth.llamarpc.com"
RPC_ETH_PRIMARY_TEMPLATE: Final[str] = (
    "https://eth-mainnet.g.alchemy.com/v2/{api_key}"
)

# Default User-Agent for direct Python urllib probes (Forno returns 403 to
# default urllib UA — see Phase-0 Task 0.1 §6 Surface-2).
HTTP_USER_AGENT: Final[str] = "path-a-stage-2/0.1"

# ── Mento V3 + V2 contract addresses (per spec §3 v1 inputs / FLAG-F2) ─────

MENTO_V3_ROUTER_CELO: Final[str] = "0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6"
MENTO_V2_COPM_CELO: Final[str] = "0x8A567e2aE79CA692Bd748aB832081C45de4041eA"
# OUT-of-scope per project_mento_canonical_naming_2026 β-corrigendum 2026-04-26:
# 0xc92e8fc2... is Minteo-fintech, NOT Mento-native. Path A v1 does NOT touch it.

# ── nbconvert execution timeout ────────────────────────────────────────────

# 1800 s = 30 min. v0 sympy derivations + v3 GBM MC at N≥1000 paths can run
# longer than nbconvert default (600 s) on a clean venv.
NBCONVERT_TIMEOUT: Final[int] = 1800

# ── Required packages (major.minor pins) ───────────────────────────────────

# Snapshot taken 2026-05-02 from contracts/.venv on Python 3.13.5.
# Path A v0/v3 add sympy + QuantLib to the Stage-1 dependency baseline.
# Keys use import names (underscores); tests map to dist names where needed.
REQUIRED_PACKAGES: Final[dict[str, str]] = {
    # Core numerics (v0 + v1 + v2 + v3)
    "numpy": "2.4",
    "scipy": "1.17",
    "pandas": "3.0",
    # Symbolic mathematics (v0 — derive Δ + Carr-Madan strip + Π closed form)
    "sympy": "1.14",
    # Stochastic-process + option-pricing (v3 GBM MC + v0/v2 strip benchmarks)
    "QuantLib": "1.42",  # import name is QuantLib (PyPI dist: QuantLib-Python)
    # Notebook tooling (all 4 NBs)
    "nbformat": "5.10",
    "nbconvert": "7.17",
    "jupyter_client": "8.8",
    "jupyter_core": "5.9",
    "ipykernel": "7.2",
    "matplotlib": "3.10",
    "IPython": "9.12",
    # Bibliography + templating (citations + auto-rendered exports)
    "jinja2": "3.1",
    "bibtexparser": "1.4",
}


# ── Determinism helper ─────────────────────────────────────────────────────

def pin_seed(seed: int) -> None:
    """Deterministically seed numpy, Python's random, and PYTHONHASHSEED.

    Use ONLY for non-MC determinism (e.g., dict iteration order in v0
    notebooks, sample-shuffle determinism in v1/v2 reconciliation tables).

    For v3 stochastic-σ MC, do NOT use this function — instead instantiate
    numpy.random.default_rng(seed=...) directly per spec §10.3, because
    legacy numpy.random global state leaks across modules and breaks the
    BLOCK-D1 byte-identical-artifact requirement.

    Note: PYTHONHASHSEED is read only at interpreter startup. Setting it via
    os.environ here affects CHILD processes (nbconvert, subprocess, etc.),
    not the current one. Intended behavior — do not work around it.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


# ── Spec-pinned numerical constants (read-only mirrors) ────────────────────

# v0 exit criteria reference these via §11.a / §11.b
N_LEGS: Final[int] = 12              # 3 IronCondor positions × 4 legs each (§10.5)
N_CONDORS: Final[int] = 3            # left-tail / ATM / right-tail (§10.5)
LEGS_PER_POSITION: Final[int] = 4    # well under Panoptic 5-leg-per-position cap

# §11.a self-consistency tolerance (machine-epsilon × N_legs)
SELF_CONSISTENCY_TOL: Final[float] = 1.2e-9   # ≤ 1e-10 × 12 per spec §11.a

# §11.b truncation/discretization bound (analytic-vs-strip)
TRUNCATION_BOUND_REL: Final[float] = 5.0e-2   # 5% per spec §11.b

# §2 v3 envelope coverage threshold
ENVELOPE_COVERAGE_MIN: Final[float] = 0.95    # ≥95% per spec §2 v3

# §10.3 v3 RNG seed pin (v3 dispatch may override; this is the default GBM seed)
V3_GBM_SEED_DEFAULT: Final[int] = 42
V3_PATH_COUNT_MIN: Final[int] = 1000          # N ≥ 1000 per spec §2 v3
