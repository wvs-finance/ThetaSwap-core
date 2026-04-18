"""Structural regression test for NB1 §1 (Setup + DAS).

Task 7 closure of the econ-notebook-implementation plan. NB1's §1 was
authored across three trios (1a/1b/1c manifest, 2a/2b/2c date coverage,
3 DAS block) committed in sequence between Trio 1 and Trio 3. This module
is a STRUCTURAL REGRESSION TEST authored AFTER the artifact it covers —
not a TDD-first test — because §1 is data-authored notebook content
(citation prose + gated code cells rendered to HTML), not algorithmic
code whose behaviour can be specified before implementation.

What gets asserted, in order of decreasing "load-bearing":

  1. Cell count: exactly 10 cells as of Trio 3 commit.
  2. Cell type layout: cells (0,1,2,5,6,8,9) are markdown; cells (3,4,7)
     are code.
  3. Tag coverage: cells 2-9 carry ``section:1``; cells 0 and 1 (title +
     gate verdict) do not.
  4. Input-hiding tags: every code cell carries ``remove-input`` so the
     PDF build via nbconvert hides the bootstrap + query mechanics from
     the rendered output.
  5. Citation block presence: cells 2 and 6 (the markdown cells that
     precede each gated code cell) each contain all four required
     4-part-block headers, per Rule 6 of the spec.
  6. DAS structure: cell 9 is the Data Availability Statement block with
     its canonical H2 heading and at least 9 bullet lines — one per raw
     source enumerated in the manifest.
  7. Lint end-to-end: ``scripts/lint_notebook_citations.py`` exits 0 on
     the NB1 path (covers the citation-block rule AND the
     chasing-offline rule simultaneously).

What is deliberately NOT asserted:

  * The exact rendered HTML of the pandas tables.
  * The exact SQL in the query-API invocations inside the code cells.
  * The exact wording of the bootstrap or trio interpretation prose.

These would couple the test to the authored prose and would produce
false negatives every time an author refines a sentence. Structure and
required tokens are enough to catch accidental §1 regressions.

No mocks — reads the actual .ipynb file on disk via ``nbformat.read``.
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import nbformat
import pytest

# ── Path plumbing (mirrors test_notebook_skeletons.py) ────────────────────

# This test file lives at:
#   contracts/scripts/tests/test_nb1_section1.py
# env.py lives at:
#   contracts/notebooks/fx_vol_cpi_surprise/Colombia/env.py
# contracts/ is parents[2] from here.
_ENV_PATH: Final[Path] = (
    Path(__file__).resolve().parents[2]
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "env.py"
)

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parents[1]
LINT_SCRIPT: Final[Path] = _SCRIPTS_DIR / "lint_notebook_citations.py"


def _load_env():
    """Load env.py as a module by file path (it is not on sys.path)."""
    spec = importlib.util.spec_from_file_location("fx_vol_env", _ENV_PATH)
    assert spec is not None and spec.loader is not None, (
        f"Cannot build spec for {_ENV_PATH}"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_env = _load_env()
NB1_PATH: Final[Path] = _env.NB1_PATH


# ── Expected §1 cell layout (as of Trio 3 commit b5954f056) ───────────────

@dataclass(frozen=True)
class CellExpectation:
    """Expected shape of a single §1 cell.

    Attributes:
        index: Zero-based cell index in the notebook.
        cell_type: Expected ``cell_type`` ("markdown" or "code").
        section1_tag: Whether ``section:1`` must appear in ``metadata.tags``.
        remove_input_tag: Whether ``remove-input`` must appear in
            ``metadata.tags`` (code cells only).
        label: Human-readable description for assertion messages.
    """

    index: int
    cell_type: str
    section1_tag: bool
    remove_input_tag: bool
    label: str


# Cell-by-cell truth table. Keep in sync with the plan's Task 7 closure
# paragraph. If the notebook grows a new cell, this table updates first and
# the rest of the tests follow.
EXPECTED_CELLS: Final[tuple[CellExpectation, ...]] = (
    CellExpectation(0, "markdown", False, False, "Notebook title"),
    CellExpectation(1, "markdown", False, False, "Gate Verdict placeholder"),
    CellExpectation(2, "markdown", True, False, "Trio 1a manifest citation block"),
    CellExpectation(3, "code", True, True, "Trio 2 bootstrap (sys.path setup)"),
    CellExpectation(4, "code", True, True, "Trio 1b manifest-table code"),
    CellExpectation(5, "markdown", True, False, "Trio 1c manifest interpretation"),
    CellExpectation(6, "markdown", True, False, "Trio 2a date-coverage citation block"),
    CellExpectation(7, "code", True, True, "Trio 2b date-coverage code"),
    CellExpectation(8, "markdown", True, False, "Trio 2c date-coverage interpretation"),
    CellExpectation(9, "markdown", True, False, "Data Availability Statement block"),
)

EXPECTED_CELL_COUNT: Final[int] = len(EXPECTED_CELLS)

# Citation-block cells: the two markdown cells that precede a gated code
# cell inside §1. Cell 2 precedes the Trio 1b manifest code; cell 6
# precedes the Trio 2b date-coverage code.
CITATION_CELL_INDICES: Final[tuple[int, ...]] = (2, 6)

# The four headers that MUST appear in every 4-part block, in the exact
# literal form defined by Spec §5.1 (Rule 6). Trailing period is part of
# the contract — prose that uses "**Reference**" without a period would
# slip past the lint today, but we tighten the structural test here so
# §1's author cannot accidentally drift that punctuation.
REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# DAS expectations: cell 9 contains the literal DAS H2 heading and at
# least this many bullet lines (one per raw source named in the manifest:
# Banrep TRM, Banrep IBR, Banrep FX intervention, FRED daily (VIX + WTI +
# Brent), FRED monthly CPI, DANE IPC, DANE IPP, DANE CPI release calendar,
# BLS CPI release calendar → 9 distinct bullet rows).
DAS_H2_HEADING: Final[str] = "## Data Availability Statement"
MIN_DAS_BULLETS: Final[int] = 9

# Bullet-line regex: markdown bullets begin with "- " or "* " at the
# start of a line (after optional leading whitespace). We anchor to line
# start with the MULTILINE flag so sub-list items are excluded.
_BULLET_RE: Final[re.Pattern[str]] = re.compile(r"^[\-\*]\s+", re.MULTILINE)


# ── Fixture: load NB1 once per module ─────────────────────────────────────

@pytest.fixture(scope="module")
def nb1() -> nbformat.NotebookNode:
    """Load NB1 once and share across tests in this module."""
    assert NB1_PATH.is_file(), f"Missing NB1 notebook: {NB1_PATH}"
    return nbformat.read(NB1_PATH, as_version=4)


# ── Helpers (free pure functions) ─────────────────────────────────────────

def _tags(cell: nbformat.NotebookNode) -> tuple[str, ...]:
    """Return cell tags as a tuple (empty tuple if unset)."""
    return tuple(cell.metadata.get("tags", []))


def _count_bullet_lines(markdown_source: str) -> int:
    """Count lines beginning with a markdown bullet marker ('-' or '*')."""
    return len(_BULLET_RE.findall(markdown_source))


# ── Test cases ────────────────────────────────────────────────────────────

def test_nb1_cell_count(nb1: nbformat.NotebookNode) -> None:
    """NB1 has exactly the expected number of cells after Trio 3."""
    assert len(nb1.cells) == EXPECTED_CELL_COUNT, (
        f"Expected {EXPECTED_CELL_COUNT} cells after §1 Trio 3; "
        f"got {len(nb1.cells)}."
    )


@pytest.mark.parametrize(
    "expectation",
    EXPECTED_CELLS,
    ids=lambda e: f"cell{e.index}-{e.label}",
)
def test_nb1_cell_types(
    nb1: nbformat.NotebookNode, expectation: CellExpectation
) -> None:
    """Each cell has the expected ``cell_type``."""
    actual = nb1.cells[expectation.index].cell_type
    assert actual == expectation.cell_type, (
        f"Cell {expectation.index} ({expectation.label}): expected "
        f"cell_type={expectation.cell_type!r}, got {actual!r}."
    )


@pytest.mark.parametrize(
    "expectation",
    EXPECTED_CELLS,
    ids=lambda e: f"cell{e.index}-{e.label}",
)
def test_nb1_section1_tags(
    nb1: nbformat.NotebookNode, expectation: CellExpectation
) -> None:
    """Cells 2-9 carry ``section:1``; title + gate-verdict cells do not."""
    tags = _tags(nb1.cells[expectation.index])
    if expectation.section1_tag:
        assert "section:1" in tags, (
            f"Cell {expectation.index} ({expectation.label}): "
            f"expected 'section:1' in tags, got {tags!r}."
        )
    else:
        assert "section:1" not in tags, (
            f"Cell {expectation.index} ({expectation.label}): "
            f"'section:1' must NOT be present on title/gate cells; "
            f"got tags={tags!r}."
        )


@pytest.mark.parametrize(
    "expectation",
    EXPECTED_CELLS,
    ids=lambda e: f"cell{e.index}-{e.label}",
)
def test_nb1_remove_input_tags(
    nb1: nbformat.NotebookNode, expectation: CellExpectation
) -> None:
    """Every code cell carries ``remove-input``; no markdown cell does."""
    tags = _tags(nb1.cells[expectation.index])
    if expectation.remove_input_tag:
        assert "remove-input" in tags, (
            f"Cell {expectation.index} ({expectation.label}): "
            f"code cells must carry 'remove-input' so the PDF hides "
            f"bootstrap/query mechanics; got tags={tags!r}."
        )
    else:
        assert "remove-input" not in tags, (
            f"Cell {expectation.index} ({expectation.label}): "
            f"markdown cells must NOT carry 'remove-input'; "
            f"got tags={tags!r}."
        )


@pytest.mark.parametrize("cell_index", CITATION_CELL_INDICES)
def test_nb1_citation_blocks_present(
    nb1: nbformat.NotebookNode, cell_index: int
) -> None:
    """Cells 2 and 6 each contain all four required citation headers.

    These cells are the 4-part blocks that precede gated code cells
    (Trio 1b manifest and Trio 2b date coverage). They are the structural
    guarantee behind Spec §5.1 Rule 6.
    """
    cell = nb1.cells[cell_index]
    assert cell.cell_type == "markdown", (
        f"Cell {cell_index} is expected to be a markdown citation block; "
        f"got cell_type={cell.cell_type!r}."
    )
    source = cell.source
    missing = [h for h in REQUIRED_HEADERS if h not in source]
    assert not missing, (
        f"Cell {cell_index} is missing required citation header(s): "
        f"{missing!r}. A 4-part citation block must contain all four "
        f"headers verbatim (with trailing period)."
    )


def test_nb1_das_structure(nb1: nbformat.NotebookNode) -> None:
    """Cell 9 is the DAS block: literal H2 heading + at least 9 bullets."""
    das_cell = nb1.cells[9]
    assert das_cell.cell_type == "markdown", (
        f"Cell 9 must be the DAS markdown block; got cell_type="
        f"{das_cell.cell_type!r}."
    )
    source = das_cell.source
    assert DAS_H2_HEADING in source, (
        f"Cell 9 must contain the literal H2 heading {DAS_H2_HEADING!r}; "
        f"got source (first 200 chars): {source[:200]!r}"
    )
    bullet_count = _count_bullet_lines(source)
    assert bullet_count >= MIN_DAS_BULLETS, (
        f"Cell 9 (DAS) must enumerate at least {MIN_DAS_BULLETS} raw "
        f"sources as bullet lines; found only {bullet_count}."
    )


def test_nb1_citation_lint_passes() -> None:
    """``lint_notebook_citations.py`` exits 0 on the live NB1 path.

    End-to-end coverage: the lint enforces BOTH the citation-block rule
    and the chasing-offline rule. If either tightens in the future, NB1
    must continue to pass or this regression test fails loudly.
    """
    assert LINT_SCRIPT.is_file(), f"Lint script missing: {LINT_SCRIPT}"
    assert NB1_PATH.is_file(), f"NB1 missing: {NB1_PATH}"
    result = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), str(NB1_PATH)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, (
        f"Expected lint exit 0 on NB1; got {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
