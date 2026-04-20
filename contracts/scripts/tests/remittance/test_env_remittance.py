"""Tests for env_remittance.py (Phase-A.0 Task 7).

Asserts the remittance env module exposes:

  * DUCKDB_PATH, NBCONVERT_TIMEOUT, REQUIRED_PACKAGES, pin_seed inherited
    (by value / by identity) from the Rev-4 CPI env.py — shared DB contract
    plus shared version pins and determinism helper.
  * ESTIMATES_DIR, FIGURES_DIR, PDF_DIR pointing at the Task-6-scaffolded
    tree under contracts/notebooks/fx_vol_remittance_surprise/Colombia/.
  * FINGERPRINT_PATH, POINT_JSON_PATH, FULL_PKL_PATH,
    GATE_VERDICT_REMITTANCE_PATH, README_REMITTANCE_PATH — remittance-specific
    inter-task artifact paths anchored inside the remittance tree (NOT
    re-exported from Rev-4).

Also asserts the sibling remittance conftest.py:
  * provides a `conn` fixture yielding a DuckDB connection to DUCKDB_PATH.

Neither env.py nor env_remittance.py lives on sys.path; both are loaded via
importlib.util.spec_from_file_location (mirroring test_env.py Rev-4 pattern).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Final

import duckdb
import pytest


# ── Absolute paths to the two env modules ──────────────────────────────────

# This test lives at:
#   contracts/scripts/tests/remittance/test_env_remittance.py
# env_remittance.py lives at:
#   contracts/notebooks/fx_vol_remittance_surprise/Colombia/env_remittance.py
# Rev-4 env.py lives at:
#   contracts/notebooks/fx_vol_cpi_surprise/Colombia/env.py
# contracts/ is parents[3] from here.
_CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[3]
_REMITTANCE_COLOMBIA_DIR: Final[Path] = (
    _CONTRACTS_DIR / "notebooks" / "fx_vol_remittance_surprise" / "Colombia"
)
_REV4_COLOMBIA_DIR: Final[Path] = (
    _CONTRACTS_DIR / "notebooks" / "fx_vol_cpi_surprise" / "Colombia"
)
_ENV_REMITTANCE_PATH: Final[Path] = _REMITTANCE_COLOMBIA_DIR / "env_remittance.py"
_REV4_ENV_PATH: Final[Path] = _REV4_COLOMBIA_DIR / "env.py"


def _load(name: str, path: Path):
    """Load a .py file as a module by absolute path (no sys.path)."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, (
        f"Cannot build spec for {path}"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_rev4_env():
    return _load("fx_vol_env_rev4", _REV4_ENV_PATH)


def _load_env_remittance():
    return _load("fx_vol_env_remittance", _ENV_REMITTANCE_PATH)


def _load_rev4_env_via_shim():
    """Load Rev-4 env.py the way env_remittance loads it — via ``import env``.

    env_remittance.py inserts the Rev-4 Colombia dir on sys.path and then
    does a top-level ``import env``. To assert ``pin_seed is pin_seed``
    (identity, not equality), the test must resolve Rev-4 through the
    SAME module registration. Loading via ``spec_from_file_location`` with
    a different module name creates a second, unrelated module object whose
    function objects are not identical to the shim-loaded ones.

    Precondition: env_remittance has already been imported at least once
    so the sys.path mutation has occurred.
    """
    import sys
    # env_remittance's top-level assign makes sys.path insertion idempotent.
    _load_env_remittance()
    # Clear any stale "env" binding before re-importing — we want the module
    # object that env_remittance captured.
    if "env" in sys.modules:
        return sys.modules["env"]
    import env  # type: ignore[import-not-found]
    return env


# ── Module existence ───────────────────────────────────────────────────────

def test_env_remittance_module_exists() -> None:
    """env_remittance.py must be present at the expected sibling path."""
    assert _ENV_REMITTANCE_PATH.is_file(), (
        f"Missing env_remittance.py: {_ENV_REMITTANCE_PATH}"
    )


def test_env_remittance_imports_without_raising() -> None:
    """env_remittance.py must import cleanly (shim resolves Rev-4 env)."""
    env_rem = _load_env_remittance()
    assert env_rem is not None


# ── Inherited constants (shared-DB + shared-pins contract) ─────────────────

def test_duckdb_path_is_shared_with_rev4() -> None:
    """DUCKDB_PATH must equal Rev-4 env.DUCKDB_PATH (shared DB, NOT a copy)."""
    env_rem = _load_env_remittance()
    env_rev4 = _load_rev4_env()
    assert Path(env_rem.DUCKDB_PATH).resolve() == Path(env_rev4.DUCKDB_PATH).resolve()
    # Defensive: the path must point at the real populated DB.
    assert Path(env_rem.DUCKDB_PATH).is_file(), (
        f"DuckDB file missing at {env_rem.DUCKDB_PATH}"
    )


def test_nbconvert_timeout_inherited_from_rev4() -> None:
    """NBCONVERT_TIMEOUT must equal Rev-4's value (shared pin)."""
    env_rem = _load_env_remittance()
    env_rev4 = _load_rev4_env()
    assert env_rem.NBCONVERT_TIMEOUT == env_rev4.NBCONVERT_TIMEOUT


def test_required_packages_inherited_from_rev4() -> None:
    """REQUIRED_PACKAGES dict must equal Rev-4's dict (shared version pins)."""
    env_rem = _load_env_remittance()
    env_rev4 = _load_rev4_env()
    assert env_rem.REQUIRED_PACKAGES == env_rev4.REQUIRED_PACKAGES


def test_pin_seed_is_same_callable_as_rev4() -> None:
    """pin_seed must be the SAME function object re-exported from Rev-4.

    Identity comparison (``is``) — not equality — ensures no local override
    or re-implementation has been introduced. The Rev-4 module is resolved
    via the same sys.path shim env_remittance uses (``import env``) so that
    both references resolve to a single module object in ``sys.modules``.
    """
    env_rem = _load_env_remittance()
    env_rev4 = _load_rev4_env_via_shim()
    assert callable(env_rem.pin_seed)
    assert env_rem.pin_seed is env_rev4.pin_seed


# ── Remittance-specific path constants ─────────────────────────────────────

def test_estimates_dir_points_at_remittance_tree() -> None:
    """ESTIMATES_DIR must resolve to the Task-6 remittance estimates/ folder."""
    env_rem = _load_env_remittance()
    expected = _REMITTANCE_COLOMBIA_DIR / "estimates"
    assert Path(env_rem.ESTIMATES_DIR).resolve() == expected.resolve()
    assert Path(env_rem.ESTIMATES_DIR).is_dir(), (
        f"estimates/ missing at {env_rem.ESTIMATES_DIR}"
    )


def test_figures_dir_points_at_remittance_tree() -> None:
    """FIGURES_DIR must resolve to the Task-6 remittance figures/ folder."""
    env_rem = _load_env_remittance()
    expected = _REMITTANCE_COLOMBIA_DIR / "figures"
    assert Path(env_rem.FIGURES_DIR).resolve() == expected.resolve()
    assert Path(env_rem.FIGURES_DIR).is_dir(), (
        f"figures/ missing at {env_rem.FIGURES_DIR}"
    )


def test_pdf_dir_points_at_remittance_tree() -> None:
    """PDF_DIR must resolve to the Task-6 remittance pdf/ folder."""
    env_rem = _load_env_remittance()
    expected = _REMITTANCE_COLOMBIA_DIR / "pdf"
    assert Path(env_rem.PDF_DIR).resolve() == expected.resolve()
    assert Path(env_rem.PDF_DIR).is_dir(), (
        f"pdf/ missing at {env_rem.PDF_DIR}"
    )


def test_fingerprint_path_under_remittance_estimates() -> None:
    """FINGERPRINT_PATH == <remittance estimates>/nb1_panel_fingerprint.json."""
    env_rem = _load_env_remittance()
    expected = _REMITTANCE_COLOMBIA_DIR / "estimates" / "nb1_panel_fingerprint.json"
    assert Path(env_rem.FINGERPRINT_PATH).resolve() == expected.resolve()


def test_point_json_path_under_remittance_estimates() -> None:
    """POINT_JSON_PATH == <remittance estimates>/nb2_params_point.json."""
    env_rem = _load_env_remittance()
    expected = _REMITTANCE_COLOMBIA_DIR / "estimates" / "nb2_params_point.json"
    assert Path(env_rem.POINT_JSON_PATH).resolve() == expected.resolve()


def test_full_pkl_path_under_remittance_estimates() -> None:
    """FULL_PKL_PATH == <remittance estimates>/nb2_full.pkl (per Task-7 spec)."""
    env_rem = _load_env_remittance()
    expected = _REMITTANCE_COLOMBIA_DIR / "estimates" / "nb2_full.pkl"
    assert Path(env_rem.FULL_PKL_PATH).resolve() == expected.resolve()


def test_gate_verdict_remittance_path_under_remittance_estimates() -> None:
    """GATE_VERDICT_REMITTANCE_PATH == <remittance estimates>/gate_verdict_remittance.json."""
    env_rem = _load_env_remittance()
    expected = (
        _REMITTANCE_COLOMBIA_DIR / "estimates" / "gate_verdict_remittance.json"
    )
    assert Path(env_rem.GATE_VERDICT_REMITTANCE_PATH).resolve() == expected.resolve()


def test_readme_remittance_path_in_remittance_colombia_root() -> None:
    """README_REMITTANCE_PATH == <remittance Colombia>/README.md."""
    env_rem = _load_env_remittance()
    expected = _REMITTANCE_COLOMBIA_DIR / "README.md"
    assert Path(env_rem.README_REMITTANCE_PATH).resolve() == expected.resolve()


def test_remittance_paths_anchored_inside_remittance_tree() -> None:
    """All remittance-specific paths must live under the remittance tree.

    Defensive cross-check: catches any accidental fall-through to Rev-4
    CPI directories.
    """
    env_rem = _load_env_remittance()
    remittance_root = _REMITTANCE_COLOMBIA_DIR.resolve()
    for name in (
        "ESTIMATES_DIR",
        "FIGURES_DIR",
        "PDF_DIR",
        "FINGERPRINT_PATH",
        "POINT_JSON_PATH",
        "FULL_PKL_PATH",
        "GATE_VERDICT_REMITTANCE_PATH",
        "README_REMITTANCE_PATH",
    ):
        p = Path(getattr(env_rem, name)).resolve()
        assert remittance_root in p.parents or p == remittance_root, (
            f"{name}={p} is not rooted under {remittance_root}"
        )


# ── conftest `conn` fixture contract ───────────────────────────────────────

def test_conn_fixture_available_and_opens_shared_duckdb(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """The remittance conftest must inherit/provide the `conn` fixture.

    The fixture must yield a live DuckDB connection to DUCKDB_PATH. We
    execute a trivial metadata query to prove liveness without assuming
    any specific schema.
    """
    assert conn is not None
    # A trivial liveness check that does not depend on schema.
    result = conn.execute("SELECT 1").fetchone()
    assert result == (1,)
