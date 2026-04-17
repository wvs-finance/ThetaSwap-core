"""Tests for the fx_vol_cpi_surprise notebook folder scaffold and scoped gitignore.

Task 1a of the econ-notebook-implementation plan. Asserts that:
  * The folder tree contracts/notebooks/fx_vol_cpi_surprise/Colombia/{estimates,figures,pdf}
    exists (four leaf folders plus the fx_vol_cpi_surprise root = five folders).
  * contracts/.gitignore contains the three scoped ignore rules for pickle
    estimates, per-run pdf outputs, and nbconvert aux artifacts.

The test does not use mocks: it reads the real filesystem at the worktree root.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

# ── Path constants ──

# This test file lives at: contracts/scripts/tests/test_scaffold.py
# The contracts/ directory is two parents up from the test file's parent.
CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[2]
NOTEBOOKS_DIR: Final[Path] = CONTRACTS_DIR / "notebooks"
FX_VOL_DIR: Final[Path] = NOTEBOOKS_DIR / "fx_vol_cpi_surprise"
COLOMBIA_DIR: Final[Path] = FX_VOL_DIR / "Colombia"
GITIGNORE_PATH: Final[Path] = CONTRACTS_DIR / ".gitignore"

EXPECTED_FOLDERS: Final[tuple[Path, ...]] = (
    FX_VOL_DIR,
    COLOMBIA_DIR,
    COLOMBIA_DIR / "estimates",
    COLOMBIA_DIR / "figures",
    COLOMBIA_DIR / "pdf",
)

EXPECTED_GITIGNORE_PATTERNS: Final[tuple[str, ...]] = (
    "contracts/notebooks/fx_vol_cpi_surprise/**/estimates/*.pkl",
    "contracts/notebooks/fx_vol_cpi_surprise/**/pdf/",
    "contracts/notebooks/fx_vol_cpi_surprise/**/_nbconvert_template/**/*.aux",
)


# ── Folder existence tests ──

def test_fx_vol_cpi_surprise_root_exists() -> None:
    """The fx_vol_cpi_surprise/ top-level folder under notebooks/ exists."""
    assert FX_VOL_DIR.is_dir(), f"Missing folder: {FX_VOL_DIR}"


def test_colombia_folder_exists() -> None:
    """The Colombia/ country-scoped folder exists."""
    assert COLOMBIA_DIR.is_dir(), f"Missing folder: {COLOMBIA_DIR}"


def test_estimates_folder_exists() -> None:
    """The Colombia/estimates/ leaf folder exists."""
    assert (COLOMBIA_DIR / "estimates").is_dir(), (
        f"Missing folder: {COLOMBIA_DIR / 'estimates'}"
    )


def test_figures_folder_exists() -> None:
    """The Colombia/figures/ leaf folder exists."""
    assert (COLOMBIA_DIR / "figures").is_dir(), (
        f"Missing folder: {COLOMBIA_DIR / 'figures'}"
    )


def test_pdf_folder_exists() -> None:
    """The Colombia/pdf/ leaf folder exists."""
    assert (COLOMBIA_DIR / "pdf").is_dir(), (
        f"Missing folder: {COLOMBIA_DIR / 'pdf'}"
    )


def test_all_five_folders_exist() -> None:
    """Sanity check: all five expected folders exist as a set."""
    missing = [str(p) for p in EXPECTED_FOLDERS if not p.is_dir()]
    assert not missing, f"Missing folders: {missing}"


# ── .gitkeep tests (leaf folders only: estimates, figures, pdf) ──

def test_estimates_has_gitkeep() -> None:
    """estimates/.gitkeep exists so git tracks the otherwise-empty folder."""
    gitkeep = COLOMBIA_DIR / "estimates" / ".gitkeep"
    assert gitkeep.is_file(), f"Missing .gitkeep: {gitkeep}"


def test_figures_has_gitkeep() -> None:
    """figures/.gitkeep exists so git tracks the otherwise-empty folder."""
    gitkeep = COLOMBIA_DIR / "figures" / ".gitkeep"
    assert gitkeep.is_file(), f"Missing .gitkeep: {gitkeep}"


def test_pdf_has_gitkeep() -> None:
    """pdf/.gitkeep exists so git tracks the otherwise-empty folder."""
    gitkeep = COLOMBIA_DIR / "pdf" / ".gitkeep"
    assert gitkeep.is_file(), f"Missing .gitkeep: {gitkeep}"


# ── .gitignore pattern tests ──

def test_gitignore_exists() -> None:
    """contracts/.gitignore exists (prerequisite for pattern checks)."""
    assert GITIGNORE_PATH.is_file(), f"Missing file: {GITIGNORE_PATH}"


def test_gitignore_contains_estimates_pkl_rule() -> None:
    """Scoped ignore for pickle estimates under any country subfolder."""
    content = GITIGNORE_PATH.read_text()
    pattern = "contracts/notebooks/fx_vol_cpi_surprise/**/estimates/*.pkl"
    assert pattern in content, f"Missing gitignore pattern: {pattern}"


def test_gitignore_contains_pdf_rule() -> None:
    """Scoped ignore for per-run pdf outputs under any country subfolder."""
    content = GITIGNORE_PATH.read_text()
    pattern = "contracts/notebooks/fx_vol_cpi_surprise/**/pdf/"
    assert pattern in content, f"Missing gitignore pattern: {pattern}"


def test_gitignore_contains_nbconvert_aux_rule() -> None:
    """Scoped ignore for nbconvert LaTeX aux artifacts."""
    content = GITIGNORE_PATH.read_text()
    pattern = "contracts/notebooks/fx_vol_cpi_surprise/**/_nbconvert_template/**/*.aux"
    assert pattern in content, f"Missing gitignore pattern: {pattern}"


def test_gitignore_has_no_global_pkl_rule() -> None:
    """Guard: we must not accidentally add a global *.pkl rule.

    Only the scoped rule under fx_vol_cpi_surprise/**/estimates/*.pkl is allowed.
    """
    content = GITIGNORE_PATH.read_text()
    for raw_line in content.splitlines():
        line = raw_line.strip()
        # Skip comments and blanks.
        if not line or line.startswith("#"):
            continue
        # A truly global *.pkl rule would be exactly "*.pkl" or "**/*.pkl" or "/*.pkl".
        assert line not in {"*.pkl", "**/*.pkl", "/*.pkl"}, (
            f"Unexpected global pkl rule in .gitignore: {line!r}"
        )


def test_gitignore_has_all_three_scoped_rules() -> None:
    """Aggregate check: all three scoped patterns present."""
    content = GITIGNORE_PATH.read_text()
    missing = [p for p in EXPECTED_GITIGNORE_PATTERNS if p not in content]
    assert not missing, f"Missing gitignore patterns: {missing}"
