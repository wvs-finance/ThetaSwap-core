"""Tests for env.py, shared conn fixture, and nb2_serialize stub.

Task 1b of the econ-notebook-implementation plan. Asserts that:

  * env.py exposes module-level path constants resolved via pathlib to the
    notebooks/, estimates/, figures/, pdf/ tree and the DuckDB file.
  * env.REQUIRED_PACKAGES maps distribution keys to major.minor pin strings
    matching the CURRENT venv install (guards against silent drift).
  * env.pin_seed(seed) deterministically primes random, numpy, and
    PYTHONHASHSEED.
  * conftest.py provides a session-scoped `conn` fixture yielding a
    read-only DuckDB connection to the real populated structural_econ.duckdb.
  * nb2_serialize.py is import-safe and raises NotImplementedError with a
    "Task 22" marker when its placeholder is called.

No mocks — the `conn` fixture opens the real 4.3MB DuckDB file.
"""
from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import random
from pathlib import Path
from typing import Final

import duckdb
import numpy as np
import pytest

# ── Path to import env.py (not on sys.path by default) ─────────────────────

# This test file lives at: contracts/scripts/tests/test_env.py
# env.py lives at: contracts/notebooks/fx_vol_cpi_surprise/Colombia/env.py
# contracts/ is parents[2] from here.
CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[2]
ENV_PATH: Final[Path] = (
    CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "env.py"
)
EXPECTED_DUCKDB: Final[Path] = CONTRACTS_DIR / "data" / "structural_econ.duckdb"
EXPECTED_ESTIMATES: Final[Path] = (
    CONTRACTS_DIR / "notebooks" / "fx_vol_cpi_surprise" / "Colombia" / "estimates"
)
EXPECTED_FIGURES: Final[Path] = (
    CONTRACTS_DIR / "notebooks" / "fx_vol_cpi_surprise" / "Colombia" / "figures"
)
EXPECTED_PDF: Final[Path] = (
    CONTRACTS_DIR / "notebooks" / "fx_vol_cpi_surprise" / "Colombia" / "pdf"
)
EXPECTED_README: Final[Path] = (
    CONTRACTS_DIR / "notebooks" / "fx_vol_cpi_surprise" / "Colombia" / "README.md"
)
EXPECTED_NB1: Final[Path] = (
    CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "01_data_eda.ipynb"
)
EXPECTED_NB2: Final[Path] = (
    CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "02_estimation.ipynb"
)
EXPECTED_NB3: Final[Path] = (
    CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "03_tests_and_sensitivity.ipynb"
)


def _load_env():
    """Load env.py as a module by file path (it is not on sys.path)."""
    spec = importlib.util.spec_from_file_location("fx_vol_env", ENV_PATH)
    assert spec is not None and spec.loader is not None, (
        f"Cannot build spec for {ENV_PATH}"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── Path constant tests ────────────────────────────────────────────────────

def test_env_module_imports() -> None:
    """env.py exists and imports without raising."""
    assert ENV_PATH.is_file(), f"Missing env.py: {ENV_PATH}"
    env = _load_env()
    assert env is not None


def test_duckdb_path_is_absolute_and_points_at_real_file() -> None:
    """DUCKDB_PATH resolves to the real structural_econ.duckdb."""
    env = _load_env()
    assert Path(env.DUCKDB_PATH).is_absolute()
    assert Path(env.DUCKDB_PATH).name == "structural_econ.duckdb"
    assert Path(env.DUCKDB_PATH).resolve() == EXPECTED_DUCKDB.resolve()
    assert Path(env.DUCKDB_PATH).is_file(), (
        f"DuckDB file missing at {env.DUCKDB_PATH}"
    )


def test_estimates_dir_matches_scaffold() -> None:
    """ESTIMATES_DIR points at the Task-1a-created estimates/ folder."""
    env = _load_env()
    assert Path(env.ESTIMATES_DIR).resolve() == EXPECTED_ESTIMATES.resolve()
    assert Path(env.ESTIMATES_DIR).is_dir()


def test_figures_dir_matches_scaffold() -> None:
    """FIGURES_DIR points at the Task-1a-created figures/ folder."""
    env = _load_env()
    assert Path(env.FIGURES_DIR).resolve() == EXPECTED_FIGURES.resolve()
    assert Path(env.FIGURES_DIR).is_dir()


def test_pdf_dir_matches_scaffold() -> None:
    """PDF_DIR points at the Task-1a-created pdf/ folder."""
    env = _load_env()
    assert Path(env.PDF_DIR).resolve() == EXPECTED_PDF.resolve()
    assert Path(env.PDF_DIR).is_dir()


def test_artifact_file_paths_under_estimates_dir() -> None:
    """FINGERPRINT/POINT/FULL/GATE paths live inside ESTIMATES_DIR."""
    env = _load_env()
    assert (
        Path(env.FINGERPRINT_PATH).name == "nb1_panel_fingerprint.json"
    )
    assert Path(env.FINGERPRINT_PATH).parent.resolve() == EXPECTED_ESTIMATES.resolve()

    assert Path(env.POINT_JSON_PATH).name == "nb2_params_point.json"
    assert Path(env.POINT_JSON_PATH).parent.resolve() == EXPECTED_ESTIMATES.resolve()

    assert Path(env.FULL_PKL_PATH).name == "nb2_params_full.pkl"
    assert Path(env.FULL_PKL_PATH).parent.resolve() == EXPECTED_ESTIMATES.resolve()

    assert Path(env.GATE_VERDICT_PATH).name == "gate_verdict.json"
    assert Path(env.GATE_VERDICT_PATH).parent.resolve() == EXPECTED_ESTIMATES.resolve()


def test_readme_path() -> None:
    """READMEPath points at Colombia/README.md.

    Note: no .is_file() check — Task 1c creates the README via auto-render.
    At Task 1b time the file does not yet exist, so asserting existence here
    would be a false negative. Do not "fix" this by adding .is_file().
    """
    env = _load_env()
    assert Path(env.READMEPath).resolve() == EXPECTED_README.resolve()


def test_nb1_path_points_at_skeleton() -> None:
    """NB1_PATH resolves to 01_data_eda.ipynb and the skeleton exists on disk."""
    env = _load_env()
    assert Path(env.NB1_PATH).resolve() == EXPECTED_NB1.resolve()
    assert Path(env.NB1_PATH).suffix == ".ipynb"
    assert Path(env.NB1_PATH).is_file(), (
        f"NB1 skeleton missing at {env.NB1_PATH} (created by Task 1c)."
    )


def test_nb2_path_points_at_skeleton() -> None:
    """NB2_PATH resolves to 02_estimation.ipynb and the skeleton exists on disk."""
    env = _load_env()
    assert Path(env.NB2_PATH).resolve() == EXPECTED_NB2.resolve()
    assert Path(env.NB2_PATH).suffix == ".ipynb"
    assert Path(env.NB2_PATH).is_file(), (
        f"NB2 skeleton missing at {env.NB2_PATH} (created by Task 1c)."
    )


def test_nb3_path_points_at_skeleton() -> None:
    """NB3_PATH resolves to 03_tests_and_sensitivity.ipynb and the skeleton exists on disk."""
    env = _load_env()
    assert Path(env.NB3_PATH).resolve() == EXPECTED_NB3.resolve()
    assert Path(env.NB3_PATH).suffix == ".ipynb"
    assert Path(env.NB3_PATH).is_file(), (
        f"NB3 skeleton missing at {env.NB3_PATH} (created by Task 1c)."
    )


def test_nbconvert_timeout_is_1800() -> None:
    """NBCONVERT_TIMEOUT = 1800 seconds (30 min) for long notebooks."""
    env = _load_env()
    assert env.NBCONVERT_TIMEOUT == 1800


# ── REQUIRED_PACKAGES tests ────────────────────────────────────────────────

EXPECTED_PACKAGE_KEYS: Final[frozenset[str]] = frozenset({
    "statsmodels",
    "arch",
    "numpy",
    "pandas",
    "duckdb",
    "scipy",
    "jinja2",
    "bibtexparser",
    "specification_curve",
    "ruptures",
    "nbformat",
    "jupyter",
    "matplotlib",
})

# Map underscore keys to the pip-distribution name where it differs.
# Only specification_curve differs (dist name uses a dash).
_KEY_TO_DIST: Final[dict[str, str]] = {
    "specification_curve": "specification-curve",
}


def _major_minor(version: str) -> str:
    parts = version.split(".")
    return f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else version


def test_required_packages_has_expected_keys() -> None:
    """REQUIRED_PACKAGES contains at minimum the 13 expected keys."""
    env = _load_env()
    missing = EXPECTED_PACKAGE_KEYS - set(env.REQUIRED_PACKAGES)
    assert not missing, f"Missing keys in REQUIRED_PACKAGES: {sorted(missing)}"


def test_required_packages_match_installed_major_minor() -> None:
    """Each pin matches the currently installed major.minor exactly."""
    env = _load_env()
    drift: list[str] = []
    for key in EXPECTED_PACKAGE_KEYS:
        dist = _KEY_TO_DIST.get(key, key)
        actual = _major_minor(importlib.metadata.version(dist))
        declared = env.REQUIRED_PACKAGES[key]
        if actual != declared:
            drift.append(f"{key}: declared {declared!r}, installed {actual!r}")
    assert not drift, (
        "Version drift detected — update env.py REQUIRED_PACKAGES to match "
        "the current venv (or downgrade the venv to match the pin):\n  "
        + "\n  ".join(drift)
    )


# ── pin_seed tests (seed 42 draws are hard-coded) ──────────────────────────

# Intentional cross-version pin; regenerate these values if Python or numpy
# RNG implementation changes. They guard against an unexpected RNG swap but
# are stricter than the actual contract (which is only same-process
# reproducibility — see test_pin_seed_is_reproducible_across_calls below).
#
# Recomputed once via:
#   import random, numpy as np
#   random.seed(42); random.random()        -> 0.6394267984578837
#   np.random.seed(42); np.random.rand()    -> 0.3745401188473625
SEED_42_RANDOM_RANDOM: Final[float] = 0.6394267984578837
SEED_42_NUMPY_RAND: Final[float] = 0.3745401188473625


def test_pin_seed_makes_random_deterministic() -> None:
    """After pin_seed(42), random.random() returns the known first draw.

    Intentional cross-version pin; regenerate SEED_42_RANDOM_RANDOM if the
    Python RNG implementation changes.
    """
    env = _load_env()
    env.pin_seed(42)
    assert random.random() == SEED_42_RANDOM_RANDOM


def test_pin_seed_makes_numpy_random_deterministic() -> None:
    """After pin_seed(42), np.random.rand() returns the known first draw.

    Intentional cross-version pin; regenerate SEED_42_NUMPY_RAND if the numpy
    RNG implementation changes.
    """
    env = _load_env()
    env.pin_seed(42)
    assert np.random.rand() == SEED_42_NUMPY_RAND


def test_pin_seed_is_reproducible_across_calls() -> None:
    """Re-seeding with the same seed reproduces the exact same draws.

    This is the actual contract: pin_seed must be deterministic within a
    process. Unlike the hard-coded-value tests above, this survives Python
    or numpy RNG implementation changes because it compares draws to draws,
    not to a pinned literal.
    """
    env = _load_env()

    env.pin_seed(42)
    r1 = random.random()
    n1 = np.random.rand()

    env.pin_seed(42)
    r2 = random.random()
    n2 = np.random.rand()

    assert r1 == r2
    assert n1 == n2


def test_pin_seed_sets_pythonhashseed_env_var() -> None:
    """pin_seed writes PYTHONHASHSEED to os.environ for child processes."""
    env = _load_env()
    env.pin_seed(42)
    assert os.environ.get("PYTHONHASHSEED") == "42"


# ── conftest conn fixture test (real DuckDB, no mocks) ─────────────────────

def test_conn_fixture_queries_real_weekly_panel(conn: duckdb.DuckDBPyConnection) -> None:
    """The shared `conn` fixture opens the real DB and weekly_panel is populated."""
    (count,) = conn.execute("SELECT COUNT(*) FROM weekly_panel").fetchone()
    assert count > 0, "weekly_panel is empty — DB not populated?"


# ── nb2_serialize full-implementation smoke tests ─────────────────────────

def test_nb2_serialize_importable() -> None:
    """The full-implementation module imports without raising."""
    from scripts import nb2_serialize  # noqa: F401


def test_nb2_serialize_docstring_names_task_22() -> None:
    """The module docstring still names Task 22 as the originating plan row."""
    from scripts import nb2_serialize
    assert nb2_serialize.__doc__ is not None
    assert "Task 22" in nb2_serialize.__doc__


def test_nb2_serialize_public_api() -> None:
    """Post-Task-22 the module exports ``reconcile``, ``write_all``, and
    ``HandoffMetadata`` as the Layer-1-→-Layer-2 handoff surface."""
    from scripts import nb2_serialize
    for symbol in ("reconcile", "write_all", "HandoffMetadata",
                    "default_handoff_metadata", "build_payload"):
        assert hasattr(nb2_serialize, symbol), (
            f"nb2_serialize must export {symbol!r} post-Task-22."
        )
