"""Tests for the three empty .ipynb skeletons and placeholder README.md.

Task 1c of the econ-notebook-implementation plan. Asserts that:

  * Each of 01_data_eda.ipynb, 02_estimation.ipynb, 03_tests_and_sensitivity.ipynb
    is valid ``nbformat.v4`` (validates via ``nbformat.validate``).
  * Each notebook contains EXACTLY two cells, BOTH markdown:
      - cell[0]: a title cell identifying the notebook (NB1 / NB2 / NB3 + topic).
      - cell[1]: a "Gate Verdict" admonition with the literal placeholder text
        "populated after NB2 and NB3".
  * Zero code cells in any skeleton.
  * The placeholder README.md exists, is short (< 500 bytes), and references
    "Task 30" (the Jinja2 auto-render task that overwrites this file).

No mocks — reads the actual .ipynb files on disk via ``nbformat.read``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

import nbformat
import pytest

# ── Path resolution (mirrors test_env.py convention) ──────────────────────

# This test file lives at: contracts/scripts/tests/test_notebook_skeletons.py
# Notebooks live at: contracts/notebooks/fx_vol_cpi_surprise/Colombia/*.ipynb
# contracts/ is parents[2] from here.
CONTRACTS_DIR: Final[Path] = Path(__file__).resolve().parents[2]
COLOMBIA_DIR: Final[Path] = (
    CONTRACTS_DIR / "notebooks" / "fx_vol_cpi_surprise" / "Colombia"
)

NB1_PATH: Final[Path] = COLOMBIA_DIR / "01_data_eda.ipynb"
NB2_PATH: Final[Path] = COLOMBIA_DIR / "02_estimation.ipynb"
NB3_PATH: Final[Path] = COLOMBIA_DIR / "03_tests_and_sensitivity.ipynb"
README_PATH: Final[Path] = COLOMBIA_DIR / "README.md"

# Identifying title-substring tokens per notebook. The title cell must contain
# the NB-N prefix; we intentionally do NOT pin the full title string so that
# authors can refine wording without breaking the test.
NB_TITLE_TOKENS: Final[dict[Path, str]] = {
    NB1_PATH: "NB1",
    NB2_PATH: "NB2",
    NB3_PATH: "NB3",
}

# The gate-verdict cell must contain BOTH of these literal substrings.
GATE_VERDICT_TOKENS: Final[tuple[str, ...]] = (
    "Gate Verdict",
    "populated after NB2 and NB3",
)

ALL_NB_PATHS: Final[tuple[Path, ...]] = (NB1_PATH, NB2_PATH, NB3_PATH)


# ── .ipynb structural tests ────────────────────────────────────────────────

@pytest.mark.parametrize("nb_path", ALL_NB_PATHS, ids=lambda p: p.name)
def test_notebook_file_exists(nb_path: Path) -> None:
    """Each skeleton .ipynb file exists on disk."""
    assert nb_path.is_file(), f"Missing notebook skeleton: {nb_path}"


@pytest.mark.parametrize("nb_path", ALL_NB_PATHS, ids=lambda p: p.name)
def test_notebook_is_valid_nbformat_v4(nb_path: Path) -> None:
    """Each skeleton is valid nbformat v4 per ``nbformat.validate``."""
    nb = nbformat.read(nb_path, as_version=4)
    # validate raises ValidationError on failure; call it to assert.
    nbformat.validate(nb)
    assert nb.nbformat == 4


@pytest.mark.parametrize("nb_path", ALL_NB_PATHS, ids=lambda p: p.name)
def test_notebook_has_exactly_two_cells(nb_path: Path) -> None:
    """Each skeleton has exactly 2 cells: title + gate-verdict box."""
    nb = nbformat.read(nb_path, as_version=4)
    assert len(nb.cells) == 2, (
        f"{nb_path.name}: expected 2 cells, got {len(nb.cells)}"
    )


@pytest.mark.parametrize("nb_path", ALL_NB_PATHS, ids=lambda p: p.name)
def test_notebook_has_zero_code_cells(nb_path: Path) -> None:
    """Skeletons contain no code cells — phase tasks add them later."""
    nb = nbformat.read(nb_path, as_version=4)
    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    assert code_cells == [], (
        f"{nb_path.name}: expected zero code cells, got {len(code_cells)}"
    )


@pytest.mark.parametrize("nb_path", ALL_NB_PATHS, ids=lambda p: p.name)
def test_notebook_all_cells_are_markdown(nb_path: Path) -> None:
    """All cells in each skeleton are markdown (no raw/code cells)."""
    nb = nbformat.read(nb_path, as_version=4)
    assert all(c.cell_type == "markdown" for c in nb.cells), (
        f"{nb_path.name}: non-markdown cells present: "
        f"{[c.cell_type for c in nb.cells]}"
    )


@pytest.mark.parametrize("nb_path", ALL_NB_PATHS, ids=lambda p: p.name)
def test_notebook_title_cell_identifies_notebook(nb_path: Path) -> None:
    """Cell 0 is a markdown title cell containing the NB-N identifier."""
    nb = nbformat.read(nb_path, as_version=4)
    title_cell = nb.cells[0]
    assert title_cell.cell_type == "markdown"
    token = NB_TITLE_TOKENS[nb_path]
    assert token in title_cell.source, (
        f"{nb_path.name} title cell missing identifier {token!r}; "
        f"got source: {title_cell.source!r}"
    )


@pytest.mark.parametrize("nb_path", ALL_NB_PATHS, ids=lambda p: p.name)
def test_notebook_gate_verdict_cell_has_placeholder(nb_path: Path) -> None:
    """Cell 1 is a markdown 'Gate Verdict' box with the placeholder text."""
    nb = nbformat.read(nb_path, as_version=4)
    gv_cell = nb.cells[1]
    assert gv_cell.cell_type == "markdown"
    for token in GATE_VERDICT_TOKENS:
        assert token in gv_cell.source, (
            f"{nb_path.name} gate-verdict cell missing {token!r}; "
            f"got source: {gv_cell.source!r}"
        )


# ── Placeholder README.md tests ────────────────────────────────────────────

def test_readme_placeholder_exists() -> None:
    """Placeholder README.md exists (will be overwritten by Task 30)."""
    assert README_PATH.is_file(), f"Missing placeholder README: {README_PATH}"


def test_readme_placeholder_references_task_30() -> None:
    """Placeholder body mentions Task 30 as the auto-render author."""
    content = README_PATH.read_text(encoding="utf-8")
    assert "Task 30" in content, (
        f"README placeholder should reference 'Task 30'; got: {content!r}"
    )


def test_readme_placeholder_is_short() -> None:
    """Placeholder README stays under 500 bytes — just a pointer, not content."""
    size = README_PATH.stat().st_size
    assert size < 500, (
        f"README placeholder grew to {size} bytes — should be a one-line "
        f"pointer under 500 bytes (Task 30 writes the real content)."
    )
