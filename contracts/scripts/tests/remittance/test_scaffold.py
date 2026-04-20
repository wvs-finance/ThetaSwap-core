"""Scaffold test for Phase-A.0 Task 6: folder scaffold + scoped gitignore.

Mirrors the Rev-4 CPI exercise layout; verifies the sibling
`fx_vol_remittance_surprise` tree exists with .gitkeep markers and that
`contracts/.gitignore` carries the three scoped ignore rules (structurally
identical to the Rev-4 block with `fx_vol_cpi_surprise` replaced by
`fx_vol_remittance_surprise`).
"""

from __future__ import annotations

import importlib
from pathlib import Path


# Repository / worktree root: this file lives at
#   <root>/contracts/scripts/tests/remittance/test_scaffold.py
# so parents[4] == <root>.
_ROOT: Path = Path(__file__).resolve().parents[4]

_COLOMBIA_DIR: Path = (
    _ROOT / "contracts" / "notebooks" / "fx_vol_remittance_surprise" / "Colombia"
)
_SUBFOLDERS: tuple[str, ...] = ("estimates", "figures", "pdf")

_GITIGNORE: Path = _ROOT / "contracts" / ".gitignore"

_REQUIRED_IGNORE_PATTERNS: tuple[str, ...] = (
    "contracts/notebooks/fx_vol_remittance_surprise/**/estimates/*.pkl",
    "contracts/notebooks/fx_vol_remittance_surprise/**/pdf/",
    "contracts/notebooks/fx_vol_remittance_surprise/**/_nbconvert_template/**/*.aux",
)


def test_colombia_subfolders_exist() -> None:
    """estimates/, figures/, pdf/ must exist under the Colombia/ tree."""
    for sub in _SUBFOLDERS:
        folder = _COLOMBIA_DIR / sub
        assert folder.is_dir(), f"missing folder: {folder}"


def test_gitkeep_files_present() -> None:
    """Each of the three subfolders must contain a committed .gitkeep file."""
    for sub in _SUBFOLDERS:
        keep = _COLOMBIA_DIR / sub / ".gitkeep"
        assert keep.is_file(), f"missing .gitkeep: {keep}"


def test_gitignore_contains_scoped_remittance_rules() -> None:
    """contracts/.gitignore must carry the three scoped remittance patterns.

    Patterns are structurally identical to the Rev-4 CPI block with
    `fx_vol_cpi_surprise` replaced by `fx_vol_remittance_surprise`.
    """
    assert _GITIGNORE.is_file(), f"gitignore not found: {_GITIGNORE}"
    lines = set(
        line.strip() for line in _GITIGNORE.read_text().splitlines() if line.strip()
    )
    for pattern in _REQUIRED_IGNORE_PATTERNS:
        assert pattern in lines, f"missing .gitignore rule: {pattern}"


def test_remittance_test_package_importable() -> None:
    """The scripts/tests/remittance/ package must be importable.

    Requires a committed ``__init__.py`` (not just implicit namespace
    discovery) so the package is explicitly declared.
    """
    init_file = Path(__file__).resolve().parent / "__init__.py"
    assert init_file.is_file(), f"missing __init__.py: {init_file}"
    module = importlib.import_module("scripts.tests.remittance")
    assert module is not None
    assert hasattr(module, "__file__")
