"""Structural regression test for NB1 §4 (RHS EDA — regressors).

Task 11 (and its predecessors §4a/§4b) of the econ-notebook-implementation
plan author §4 as a growing sequence of (why-md, code, interp-md) trios —
§4a (cpi_surprise_ar1) complete, §4b (us_cpi_surprise) in progress, §4c
(risk-channel regressors) and §4d-f (Task 11 follow-ups) not yet started.
This module is a STRUCTURAL REGRESSION TEST authored AFTER §4 began —
not a TDD-first test — because §4 content is data-authored notebook prose
(citation prose + gated code cells rendered to HTML + SQL panels), not
algorithmic code whose behaviour can be specified before implementation.
TDD discipline remains in force for cleaning.py, estimation code, and
query-API extensions; this file covers only the notebook's structural
layout contract.

Scope note (grows with the notebook): §4 is actively being extended.
Rather than fix a cell-count total or hard-code per-cell indices, every
assertion in this module is parametrized over the cells discovered to
carry the ``section:4`` tag. Adding a new §4 trio MUST leave existing
assertions green; if it does not, the new trio violated a structural
rule and the failure is genuine.

What gets asserted, in order of decreasing "load-bearing":

  1. Presence: at least three cells carry ``section:4`` (enough for one
     trio). This keeps the test from silently passing on an empty §4.
  2. Cell types: every ``section:4`` cell is ``markdown`` or ``code`` —
     no raw cells (raw cells bypass nbconvert's PDF-hiding tags).
  3. Input-hiding: every ``section:4`` code cell also carries
     ``remove-input`` so the PDF build hides bootstrap + query mechanics.
  4. Citation-block placement: every GATED ``section:4`` code cell (OLS,
     GLS, arch_model, scipy stat tests, or a literal ``Decision #N``
     marker in its source) is preceded within the ``section:4`` window
     by a markdown cell containing all four required 4-part-block
     headers verbatim (with trailing periods). Spec §5.1 Rule 6.
  5. Decision-marker hygiene: every literal ``Decision #N``-style token
     (hash-prefixed) in §4 code-cell source matches the canonical
     ``Decision #<digits>`` form — no lowercase ``decision``, no
     trailing letter suffix like ``Decision #4a``. Variable names such
     as ``decision4_card_df`` carry no hash and are unaffected.
  6. No chasing-offline prose: mirrors
     ``lint_notebook_citations.py``'s Rule 7 — markdown cells tagged
     ``section:4`` must not contain "we tried", "rejected in favor of",
     "we chose", or "this didn't work" (case-insensitive, apostrophes
     normalised).
  7. Lint end-to-end: ``scripts/lint_notebook_citations.py`` exits 0 on
     the live NB1 path (sanity — the lint enforces BOTH the citation
     and chasing-offline rules across the whole file).

What is deliberately NOT asserted:

  * Specific cell indices (§4 is growing — indices drift every commit).
  * Specific cell contents (authored prose rewords between commits).
  * Specific Decision numbers exist (some have not fired yet).
  * Specific regressor column names (behaviour, not structure).

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

# ── Path plumbing (mirrors test_nb1_section1.py) ──────────────────────────

# This test file lives at:
#   contracts/scripts/tests/test_nb1_section4.py
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


# ── Contract constants ────────────────────────────────────────────────────

SECTION_TAG: Final[str] = "section:4"
REMOVE_INPUT_TAG: Final[str] = "remove-input"
MIN_SECTION4_CELLS: Final[int] = 3  # one full trio (why-md, code, interp-md)

# The four headers that MUST appear in every 4-part block, in the exact
# literal form defined by Spec §5.1 Rule 6. Trailing period is part of
# the contract — prose that uses "**Reference**" without a period would
# slip past the lint's substring match today, but we tighten the
# structural test here so §4's author cannot accidentally drift that
# punctuation.
REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# Regex patterns that mark a code cell as "gated" — mirrors the gate
# logic in scripts/lint_notebook_citations.py. A gated cell fires the
# citation-block requirement on its most-recent §4 markdown predecessor.
_GATED_SOURCE_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\bOLS\s*\("),
    re.compile(r"\bGLS\s*\("),
    re.compile(r"\barch_model\s*\("),
    re.compile(r"scipy\.stats\.levene"),
    re.compile(r"scipy\.stats\.jarque_bera"),
    re.compile(r"scipy\.stats\.shapiro"),
    re.compile(r"\bTLinearModel\b"),
    re.compile(r"arch\.bootstrap"),
)

# "Decision #N" gate: matches the literal hash-prefixed token in either
# cell source or cell tag. The ``#`` is required — bare identifiers like
# ``decision4_card_df`` are variable names, not gate markers.
_DECISION_GATE_RE: Final[re.Pattern[str]] = re.compile(
    r"\b[Dd]ecision\s*#\s*\d+"
)

# Canonical Decision-token form: capital D, single space, hash, digits,
# and no trailing letter suffix. Lookahead ``(?![A-Za-z0-9])`` rejects
# ``Decision #4a`` and ``Decision #40`` would be fine only if it is
# genuinely the 40th decision. The lint is structural — it does not
# verify N is monotone.
_DECISION_CANONICAL_RE: Final[re.Pattern[str]] = re.compile(
    r"Decision #\d+(?![A-Za-z0-9])"
)

# Any hash-prefixed Decision-like token (for enumeration). Matches both
# canonical and non-canonical forms so the assertion can report what the
# author typed vs. what the contract requires.
_DECISION_ANY_HASH_RE: Final[re.Pattern[str]] = re.compile(
    r"[Dd]ecision\s*#\s*\d+[A-Za-z0-9]*"
)

# Forbidden markdown phrases (chasing-offline rule). Mirrors
# lint_notebook_citations.FORBIDDEN_PHRASES exactly. Apostrophes are
# folded to ASCII before matching so Jupyter's U+2019 auto-conversion
# does not let a violation slip through.
FORBIDDEN_PHRASES: Final[tuple[str, ...]] = (
    "we tried",
    "rejected in favor of",
    "we chose",
    "this didn't work",
)


# ── Data types ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Section4Cell:
    """Reference to a single §4 cell by index + type + source.

    Attributes:
        index: Zero-based cell index in the parent notebook.
        cell_type: nbformat cell_type string ("markdown", "code", "raw").
        source: Flattened cell source (list-of-strings joined).
        tags: Tuple of cell-level tag strings.
    """

    index: int
    cell_type: str
    source: str
    tags: tuple[str, ...]


# ── Helpers (free pure functions) ─────────────────────────────────────────

def _cell_source(cell: nbformat.NotebookNode) -> str:
    """Flatten the cell source (nbformat allows list or str)."""
    src = cell.get("source", "")
    if isinstance(src, list):
        return "".join(src)
    return str(src)


def _cell_tags(cell: nbformat.NotebookNode) -> tuple[str, ...]:
    """Return cell tags as a tuple (empty tuple if unset)."""
    tags = cell.get("metadata", {}).get("tags", [])
    if not isinstance(tags, (list, tuple)):
        return ()
    return tuple(str(t) for t in tags)


def _section4_cells(nb: nbformat.NotebookNode) -> tuple[Section4Cell, ...]:
    """Return every notebook cell carrying the ``section:4`` tag, in order."""
    out: list[Section4Cell] = []
    for idx, cell in enumerate(nb.cells):
        tags = _cell_tags(cell)
        if SECTION_TAG in tags:
            out.append(
                Section4Cell(
                    index=idx,
                    cell_type=cell.cell_type,
                    source=_cell_source(cell),
                    tags=tags,
                )
            )
    return tuple(out)


def _is_gated_code_source(source: str) -> bool:
    """Return True iff a code cell's source fires the citation-block gate."""
    if any(p.search(source) for p in _GATED_SOURCE_PATTERNS):
        return True
    if _DECISION_GATE_RE.search(source):
        return True
    return False


def _preceding_section4_markdown(
    cells: tuple[Section4Cell, ...], gated_pos: int
) -> Section4Cell | None:
    """Return the most-recent ``section:4`` markdown cell before ``gated_pos``.

    ``gated_pos`` is an index into ``cells`` (i.e. into the filtered §4
    sequence), NOT into the parent notebook. Walking within §4 is correct
    here because the citation block and its gated cell live in the same
    section by construction.
    """
    for i in range(gated_pos - 1, -1, -1):
        if cells[i].cell_type == "markdown":
            return cells[i]
    return None


def _normalize_apostrophes(text: str) -> str:
    """Fold U+2019 to ASCII apostrophe before forbidden-phrase matching."""
    return text.replace("\u2019", "'")


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def nb1() -> nbformat.NotebookNode:
    """Load NB1 once and share across tests in this module."""
    assert NB1_PATH.is_file(), f"Missing NB1 notebook: {NB1_PATH}"
    return nbformat.read(NB1_PATH, as_version=4)


@pytest.fixture(scope="module")
def section4(nb1: nbformat.NotebookNode) -> tuple[Section4Cell, ...]:
    """All cells tagged ``section:4``, in notebook order."""
    return _section4_cells(nb1)


# ── Test cases ────────────────────────────────────────────────────────────

def test_nb1_section4_has_at_least_one_trio(
    section4: tuple[Section4Cell, ...],
) -> None:
    """§4 must contain at least three ``section:4`` cells (one full trio).

    Prevents a silent-pass on an accidentally-empty §4 (e.g. if the
    section tag is typoed or if §4 is deleted during a rebase). Three is
    the minimum meaningful size: why-markdown, code, interp-markdown.
    """
    assert len(section4) >= MIN_SECTION4_CELLS, (
        f"Expected at least {MIN_SECTION4_CELLS} cells tagged "
        f"{SECTION_TAG!r} (one full trio); got {len(section4)}. "
        f"§4 may be empty, un-tagged, or truncated."
    )


def test_nb1_section4_cell_types_are_md_or_code(
    section4: tuple[Section4Cell, ...],
) -> None:
    """Every ``section:4`` cell is markdown or code — no raw cells.

    Raw cells bypass nbconvert's tag-based hiding and render as literal
    text in the PDF, which would leak unformatted content into the gate
    deliverable. Parametrized in-body (not via pytest.mark.parametrize)
    because the cell list is resolved only at test-collection time and
    must tolerate §4 growth without parametrize-id collisions.
    """
    offenders: list[tuple[int, str]] = []
    for cell in section4:
        if cell.cell_type not in ("markdown", "code"):
            offenders.append((cell.index, cell.cell_type))
    assert not offenders, (
        f"§4 cells must be markdown or code; found non-conforming cells: "
        f"{offenders!r}"
    )


def test_nb1_section4_code_cells_have_remove_input(
    section4: tuple[Section4Cell, ...],
) -> None:
    """Every ``section:4`` code cell also carries ``remove-input``.

    The PDF build hides code inputs so the gate deliverable reads as
    prose + rendered tables/figures, not as bootstrap machinery. A §4
    code cell missing ``remove-input`` would leak DuckDB connection
    setup into the output.
    """
    offenders: list[int] = []
    for cell in section4:
        if cell.cell_type != "code":
            continue
        if REMOVE_INPUT_TAG not in cell.tags:
            offenders.append(cell.index)
    assert not offenders, (
        f"§4 code cells missing {REMOVE_INPUT_TAG!r} tag "
        f"(input will leak into PDF): cells {offenders!r}"
    )


def test_nb1_section4_citation_blocks_precede_gated_cells(
    section4: tuple[Section4Cell, ...],
) -> None:
    """Every gated §4 code cell is preceded by a full 4-part block.

    Implements Spec §5.1 Rule 6 for §4 specifically. A code cell fires
    the gate if it contains a statistical fit (OLS/GLS/arch_model),
    a scipy stat test (levene/jarque_bera/shapiro), or a literal
    ``Decision #N`` marker. The most-recent ``section:4`` markdown cell
    before the gated cell MUST contain all four required headers
    verbatim (with trailing periods).

    Walking back within §4 (rather than across the entire notebook) is
    intentional: the citation block is a section-local contract, and a
    §3 or §5 markdown cell cannot cover a §4 gate by construction.
    """
    failures: list[str] = []
    for pos, cell in enumerate(section4):
        if cell.cell_type != "code":
            continue
        if not _is_gated_code_source(cell.source):
            continue
        md = _preceding_section4_markdown(section4, pos)
        if md is None:
            failures.append(
                f"cell {cell.index}: gated code cell has no preceding "
                f"§4 markdown in the section window"
            )
            continue
        missing = tuple(h for h in REQUIRED_HEADERS if h not in md.source)
        if missing:
            failures.append(
                f"cell {cell.index}: preceding §4 markdown (cell "
                f"{md.index}) missing headers {list(missing)!r}"
            )
    assert not failures, (
        "Citation-block violations in §4:\n  " + "\n  ".join(failures)
    )


def test_nb1_section4_decision_markers_are_canonical(
    section4: tuple[Section4Cell, ...],
) -> None:
    """Every ``Decision #N`` token in §4 code cells matches canonical form.

    Canonical form is ``Decision #<digits>`` — capital D, single space,
    hash, one or more digits, no trailing letter. Detects author typos
    like ``Decision #4a`` (sub-lettering is not part of the spec's
    decision-numbering scheme) and ``decision #4`` (lowercase). Python
    identifiers like ``decision4_card_df`` have no ``#`` and are not
    matched by ``_DECISION_ANY_HASH_RE``.

    Skipped cleanly when §4 contains no code-cell Decision markers yet
    (§4c and beyond may introduce the first ones).
    """
    violations: list[str] = []
    for cell in section4:
        if cell.cell_type != "code":
            continue
        for token in _DECISION_ANY_HASH_RE.findall(cell.source):
            if not _DECISION_CANONICAL_RE.fullmatch(token):
                violations.append(
                    f"cell {cell.index}: non-canonical token {token!r} "
                    f"(expected 'Decision #<digits>')"
                )
    assert not violations, (
        "Non-canonical Decision markers in §4 code cells:\n  "
        + "\n  ".join(violations)
    )


def test_nb1_section4_no_forbidden_phrases(
    section4: tuple[Section4Cell, ...],
) -> None:
    """§4 markdown cells contain no chasing-offline prose.

    Mirrors Rule 7 of ``lint_notebook_citations.py`` scoped to §4.
    Apostrophes are folded to ASCII before the case-insensitive
    substring check so Jupyter's U+2019 auto-conversion cannot mask a
    ``this didn't work`` violation authored in a smart-quote editor.
    """
    violations: list[str] = []
    for cell in section4:
        if cell.cell_type != "markdown":
            continue
        normalised = _normalize_apostrophes(cell.source).lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() in normalised:
                violations.append(
                    f"cell {cell.index}: forbidden phrase {phrase!r}"
                )
    assert not violations, (
        "Chasing-offline violations in §4 markdown:\n  "
        + "\n  ".join(violations)
    )


def test_nb1_section4_citation_lint_passes() -> None:
    """``lint_notebook_citations.py`` exits 0 on the live NB1 path.

    Sanity check — the lint already runs across all sections on every
    pre-commit, but re-running it from this module guarantees §4's
    citation and chasing-offline rules are honoured even when the lint
    tightens in future (e.g. adds new gated-source patterns). A drift
    here fails loudly rather than silently.
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
