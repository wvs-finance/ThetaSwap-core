"""Citation-block + chasing-offline lint for FX-vol notebooks (Task 5).

Enforces two cross-cutting non-negotiable rules from the econ-notebook
implementation plan (``docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md``):

Rule 6 — Citation-block rule
    Every "gated" code cell (statistical fit, test, or a ``Decision #N``
    marker) MUST be preceded within the prior two markdown cells by a
    block containing ALL four headers:

        Reference
        Why used
        Relevance to our results
        Connection to simulator

Rule 7 — Chasing-offline rule
    Notebook markdown MUST NOT narrate offline deliberation. Forbidden
    substrings (matched case-insensitively anywhere in any markdown cell):

        "we tried"
        "rejected in favor of"
        "we chose"
        "this didn't work"

Usage
-----
    python scripts/lint_notebook_citations.py NB1.ipynb [NB2.ipynb ...]

Exit codes
----------
    0 : all notebooks pass (or contain no gated cells).
    1 : one or more violations found. One line per violation is printed
        to stderr in the form::

            <path>:<cell_index>: <kind>: <detail>

        where ``<kind>`` is either ``missing-citation-header``,
        ``missing-citation-block``, or ``chasing-offline``.
    2 : command misuse (no notebook paths supplied). Unix convention —
        a silent exit 0 on empty argv could mask a misconfigured CI
        invocation that forgets to pass files.

Design
------
Functional Python: module-level constants + pure helpers. No classes, no
mutable globals. State flows via argument passing and return values.
``nbformat`` is the only external dependency — already pinned in
``contracts/requirements.txt``.
"""
from __future__ import annotations

import re
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import nbformat

# ── Configuration constants ───────────────────────────────────────────────

REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "Reference",
    "Why used",
    "Relevance to our results",
    "Connection to simulator",
)

FORBIDDEN_PHRASES: Final[tuple[str, ...]] = (
    "we tried",
    "rejected in favor of",
    "we chose",
    "this didn't work",
)

# Regex patterns that identify a "gated" code cell. A cell is gated if its
# source contains any of these regex matches.
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

# A cell-level "Decision #N" marker counts as a gating trigger too. We
# accept it in either the cell source (any language/cell type) OR as a
# cell-level tag in ``cell.metadata.tags``. The regex is case-insensitive
# on the "Decision" word per plan guidance. A leading ``\b`` word-boundary
# prevents matches inside longer words ("indecision #3", "Undecision #1")
# from triggering the gate.
_DECISION_MARKER_RE: Final[re.Pattern[str]] = re.compile(
    r"\b[Dd]ecision\s*#\s*\d+"
)

# How many preceding cells (of any type) the lint walks back through when
# searching for a citation block. The plan specifies "within 2 markdown
# cells", which we interpret generously: walk back up to ``_LOOKBACK``
# cells total and count any markdown cell we find — but consider only the
# two most-recent markdown cells for header coverage.
_LOOKBACK: Final[int] = 4
_MAX_MARKDOWN_CELLS_TO_CONSIDER: Final[int] = 2


# ── Data types ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Violation:
    """Immutable record of a single lint violation."""

    path: Path
    cell_index: int
    kind: str  # "missing-citation-header" | "missing-citation-block" | "chasing-offline"
    detail: str

    def format(self) -> str:
        return f"{self.path}:{self.cell_index}: {self.kind}: {self.detail}"


# ── Pure helpers ──────────────────────────────────────────────────────────

def _cell_source(cell: nbformat.NotebookNode) -> str:
    """Return the cell source as a string (nbformat allows list or str)."""
    src = cell.get("source", "")
    if isinstance(src, list):
        return "".join(src)
    return str(src)


def _cell_tags(cell: nbformat.NotebookNode) -> tuple[str, ...]:
    """Return the tuple of cell-level tags (may be empty)."""
    tags = cell.get("metadata", {}).get("tags", [])
    if not isinstance(tags, (list, tuple)):
        return ()
    return tuple(str(t) for t in tags)


def _is_gated_code_cell(cell: nbformat.NotebookNode) -> bool:
    """Return True iff the code cell triggers the citation-block requirement."""
    if cell.get("cell_type") != "code":
        return False
    source = _cell_source(cell)
    if any(pattern.search(source) for pattern in _GATED_SOURCE_PATTERNS):
        return True
    if _DECISION_MARKER_RE.search(source):
        return True
    if any(_DECISION_MARKER_RE.search(tag) for tag in _cell_tags(cell)):
        return True
    return False


def _missing_headers(markdown_text: str) -> tuple[str, ...]:
    """Return the subset of REQUIRED_HEADERS NOT present in ``markdown_text``.

    Case-sensitive substring match — headers are canonical and authors
    must spell them exactly.
    """
    return tuple(h for h in REQUIRED_HEADERS if h not in markdown_text)


def _merge_recent_markdown_sources(
    cells: Sequence[nbformat.NotebookNode],
    gated_idx: int,
) -> tuple[str | None, int]:
    """Collect up to _MAX_MARKDOWN_CELLS_TO_CONSIDER markdown sources above.

    Walks back from ``gated_idx - 1`` through at most ``_LOOKBACK`` cells,
    collecting markdown cells until we have the max or run out of lookback.
    The two markdown cells are concatenated (most-recent first) so that a
    citation block split across two adjacent markdown cells is still
    recognised.

    Returns (joined_markdown_or_None, count_of_markdown_cells_found). If
    no markdown is found in the lookback window, returns (None, 0).
    """
    collected: list[str] = []
    start = gated_idx - 1
    stop = max(-1, gated_idx - 1 - _LOOKBACK)
    for i in range(start, stop, -1):
        cell = cells[i]
        if cell.get("cell_type") == "markdown":
            collected.append(_cell_source(cell))
            if len(collected) >= _MAX_MARKDOWN_CELLS_TO_CONSIDER:
                break
    if not collected:
        return None, 0
    return "\n\n".join(collected), len(collected)


def _check_citation_blocks(
    path: Path,
    cells: Sequence[nbformat.NotebookNode],
) -> tuple[Violation, ...]:
    """Return citation-block violations for every gated cell in order."""
    violations: list[Violation] = []
    for idx, cell in enumerate(cells):
        if not _is_gated_code_cell(cell):
            continue
        merged, count = _merge_recent_markdown_sources(cells, idx)
        if merged is None or count == 0:
            violations.append(
                Violation(
                    path=path,
                    cell_index=idx,
                    kind="missing-citation-block",
                    detail=(
                        "gated code cell has no preceding markdown within "
                        f"{_LOOKBACK} cells"
                    ),
                )
            )
            continue
        missing = _missing_headers(merged)
        if missing:
            violations.append(
                Violation(
                    path=path,
                    cell_index=idx,
                    kind="missing-citation-header",
                    detail=(
                        "preceding citation block is missing required "
                        f"header(s): {', '.join(missing)}"
                    ),
                )
            )
    return tuple(violations)


def _normalize_apostrophes(text: str) -> str:
    """Fold U+2019 (right single quotation mark) to ASCII apostrophe.

    Jupyter / VS Code frequently auto-convert ``'`` to the Unicode curly
    apostrophe U+2019 during markdown editing. Our FORBIDDEN_PHRASES list
    is expressed with ASCII apostrophes, so a source cell containing
    ``this didn\u2019t work`` would otherwise slip through the ``in``
    substring match. Normalising both sides to ASCII is the cheapest
    robust fix; we do not try to cover every exotic Unicode apostrophe
    because Jupyter's auto-conversion only produces U+2019.
    """
    return text.replace("\u2019", "'")


def _check_chasing_offline(
    path: Path,
    cells: Sequence[nbformat.NotebookNode],
) -> tuple[Violation, ...]:
    """Return chasing-offline violations across every markdown cell."""
    violations: list[Violation] = []
    for idx, cell in enumerate(cells):
        if cell.get("cell_type") != "markdown":
            continue
        # Normalise smart-quotes BEFORE lower-casing so that the phrase
        # list (ASCII-apostrophe, lower-case) can match source cells
        # authored in editors that auto-convert ``'`` to ``\u2019``.
        source_lower = _normalize_apostrophes(_cell_source(cell)).lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() in source_lower:
                violations.append(
                    Violation(
                        path=path,
                        cell_index=idx,
                        kind="chasing-offline",
                        detail=(
                            f"markdown contains forbidden phrase {phrase!r} "
                            "(chasing-offline deliberation not allowed)"
                        ),
                    )
                )
    return tuple(violations)


def _lint_notebook(path: Path) -> tuple[Violation, ...]:
    """Run both rules against a single notebook file."""
    nb = nbformat.read(str(path), as_version=4)
    cells: Sequence[nbformat.NotebookNode] = nb.get("cells", [])
    return _check_citation_blocks(path, cells) + _check_chasing_offline(
        path, cells
    )


def _lint_many(paths: Iterable[Path]) -> tuple[Violation, ...]:
    """Aggregate violations across a sequence of notebook paths."""
    results: list[Violation] = []
    for p in paths:
        results.extend(_lint_notebook(p))
    return tuple(results)


# ── CLI ───────────────────────────────────────────────────────────────────

def main(argv: Sequence[str]) -> int:
    if len(argv) < 2:
        print(
            "usage: lint_notebook_citations.py NB1.ipynb [NB2.ipynb ...]",
            file=sys.stderr,
        )
        # Unix convention: exit 2 = command misuse. A silent exit 0 on
        # empty argv could mask a misconfigured CI invocation that
        # forgets to pass filenames (pre-commit's ``pass_filenames: true``
        # guarantees files, but a direct call missing them is a bug).
        return 2

    paths = tuple(Path(a) for a in argv[1:])
    missing = tuple(p for p in paths if not p.is_file())
    if missing:
        for p in missing:
            print(f"{p}: error: file not found", file=sys.stderr)
        return 1

    violations = _lint_many(paths)
    if not violations:
        return 0
    for v in violations:
        print(v.format(), file=sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover - entrypoint
    sys.exit(main(sys.argv))
