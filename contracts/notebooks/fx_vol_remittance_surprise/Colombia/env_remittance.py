"""Path constants and inherited pins for the FX-vol-remittance notebooks.

Sibling to Rev-4 ``env.py`` (Colombia CPI exercise). Hosts remittance-specific
artifact paths under ``fx_vol_remittance_surprise/Colombia/`` while inheriting
the shared-DuckDB contract, nbconvert timeout, package pins, and the
deterministic ``pin_seed`` helper from Rev-4. No Rev-4 source file is modified.

Import strategy (Rev-2 disambiguation per CR F2)
-------------------------------------------------
The Rev-4 env.py lives at

    contracts/notebooks/fx_vol_cpi_surprise/Colombia/env.py

Neither ``contracts/`` nor ``notebooks/`` declares ``__init__.py``, and the
project's ``pyproject.toml`` does not register those trees as packages — so
``from contracts.notebooks.fx_vol_cpi_surprise.Colombia.env import ...`` only
works when the current working directory happens to be the worktree root,
which is a fragile assumption for notebook kernels and pytest subprocess
invocations from arbitrary directories.

Consistent with Rev-4's own pattern (``test_env.py`` loads env.py via
``importlib.util.spec_from_file_location``), this module uses a **sys.path
shim**: it inserts the absolute Rev-4 Colombia directory onto ``sys.path``
and then does a top-level ``import env`` to access the Rev-4 symbols. The
original sys.path is not mutated destructively — the insert is idempotent
and the imported-name ``env`` is local to this module's namespace, not
re-exported.

The four inherited symbols (``pin_seed``, ``NBCONVERT_TIMEOUT``,
``REQUIRED_PACKAGES``, ``DUCKDB_PATH``) are rebound at module level so
downstream code can do ``from env_remittance import DUCKDB_PATH`` without
having to know about the shim.

The remittance-specific directory and artifact-path constants are declared
fresh below — they are NOT re-exported from Rev-4 (by design: the remittance
track writes to its own ``estimates/``, ``figures/``, ``pdf/`` tree).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

# ── sys.path shim: make Rev-4 env.py importable as the top-level name ``env``
#
# This file lives at:
#   contracts/notebooks/fx_vol_remittance_surprise/Colombia/env_remittance.py
# Rev-4 env.py lives at:
#   contracts/notebooks/fx_vol_cpi_surprise/Colombia/env.py
#
# parents[0] = Colombia/  (remittance)
# parents[1] = fx_vol_remittance_surprise/
# parents[2] = notebooks/
# parents[3] = contracts/
_NOTEBOOKS_DIR: Final[Path] = Path(__file__).resolve().parents[2]
_REV4_COLOMBIA_DIR: Final[Path] = (
    _NOTEBOOKS_DIR / "fx_vol_cpi_surprise" / "Colombia"
)

# Guard against silent resolution: the Rev-4 directory must exist. Raise a
# typed error (not bare assert) so the import-time failure is informative
# and symmetric with the conftest fail-loud pattern.
if not _REV4_COLOMBIA_DIR.is_dir():
    raise FileNotFoundError(
        f"Rev-4 Colombia directory missing at {_REV4_COLOMBIA_DIR}; "
        "env_remittance cannot inherit shared pins."
    )

# sys.path.append (NOT insert-at-0) — stdlib and site-packages win over Rev-4
# Colombia, so an unrelated top-level `env` module elsewhere on the path is
# not shadowed by this shim. See Task-7 code-review Issue #1.
_rev4_colombia_str = str(_REV4_COLOMBIA_DIR)
if _rev4_colombia_str not in sys.path:
    sys.path.append(_rev4_colombia_str)

import env as _rev4_env  # noqa: E402  (sys.path extended just above)

# Hardening: verify the imported ``env`` module really is the Rev-4 file,
# not a same-named module that pytest-xdist or a stray editable-install may
# have registered earlier in ``sys.modules``. See Task-7 code-review Issue #2.
_expected_rev4_env_path = (_REV4_COLOMBIA_DIR / "env.py").resolve()
_actual_rev4_env_path = Path(getattr(_rev4_env, "__file__", "")).resolve()
if _actual_rev4_env_path != _expected_rev4_env_path:
    raise RuntimeError(
        f"env_remittance bound to wrong `env` module: expected "
        f"{_expected_rev4_env_path}, got {_actual_rev4_env_path}. "
        "Check sys.modules['env'] state and test-ordering."
    )

# ── Inherited symbols (re-bound so callers need not know about the shim) ───

pin_seed = _rev4_env.pin_seed
NBCONVERT_TIMEOUT: Final[int] = _rev4_env.NBCONVERT_TIMEOUT
REQUIRED_PACKAGES: Final[dict[str, str]] = _rev4_env.REQUIRED_PACKAGES
# Shared DuckDB contract: the remittance pipeline writes to and reads from
# the SAME structural_econ.duckdb as the Rev-4 CPI exercise. No separate DB.
DUCKDB_PATH: Final[Path] = _rev4_env.DUCKDB_PATH

# ── Remittance-local paths (independent of Rev-4 tree) ─────────────────────

_REMITTANCE_COLOMBIA_DIR: Final[Path] = Path(__file__).resolve().parent

ESTIMATES_DIR: Final[Path] = _REMITTANCE_COLOMBIA_DIR / "estimates"
FIGURES_DIR: Final[Path] = _REMITTANCE_COLOMBIA_DIR / "figures"
PDF_DIR: Final[Path] = _REMITTANCE_COLOMBIA_DIR / "pdf"

# ── Inter-task handoff files (remittance-specific) ─────────────────────────

FINGERPRINT_PATH: Final[Path] = ESTIMATES_DIR / "nb1_panel_fingerprint.json"
POINT_JSON_PATH: Final[Path] = ESTIMATES_DIR / "nb2_params_point.json"
FULL_PKL_PATH: Final[Path] = ESTIMATES_DIR / "nb2_params_full.pkl"
GATE_VERDICT_REMITTANCE_PATH: Final[Path] = (
    ESTIMATES_DIR / "gate_verdict_remittance.json"
)

# ── Auto-rendered remittance README ────────────────────────────────────────

README_REMITTANCE_PATH: Final[Path] = _REMITTANCE_COLOMBIA_DIR / "README.md"
