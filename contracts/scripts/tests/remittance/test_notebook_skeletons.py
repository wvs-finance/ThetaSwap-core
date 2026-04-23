"""Task 8 tests: .ipynb skeletons + anti-fishing disclaimer headers + README template.

Asserts the Phase-A.0 Colombia tree carries three empty-but-structurally-valid
notebook skeletons, a Jinja2 README template mirroring Rev-4's 7-section
structure, and a placeholder README.md flagged for Task-24 auto-render
overwrite.

Every notebook skeleton MUST embed the anti-fishing disclaimer from the
Rev-1 spec §10 ("Why this is not a rescue of CPI-FAIL") in its header
markdown cells. The disclaimer requires:
  - the phrase "NOT a rescue" (or close variant, e.g. "not a rescue")
  - the phrase "CPI-FAIL"
  - the mtime provenance anchor "2026-04-02"

No code cells are permitted at Task 8 — code authoring is deferred to the
Task 16+ X-trio protocol, which adds cells trio-by-trio with human review
after every (why-markdown, code-cell, interpretation-markdown) triple.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import nbformat


# Repository / worktree root: this file lives at
#   <root>/contracts/scripts/tests/remittance/test_notebook_skeletons.py
# so parents[4] == <root>.
_ROOT: Final[Path] = Path(__file__).resolve().parents[4]

_COLOMBIA_DIR: Final[Path] = (
    _ROOT / "contracts" / "notebooks" / "fx_vol_remittance_surprise" / "Colombia"
)

_NOTEBOOKS: Final[tuple[str, ...]] = (
    "01_data_eda.ipynb",
    "02_estimation.ipynb",
    "03_tests_and_sensitivity.ipynb",
)

_TEMPLATE: Final[Path] = _COLOMBIA_DIR / "_readme_template.md.j2"
_README: Final[Path] = _COLOMBIA_DIR / "README.md"

# Header-identifier substring required in each notebook's first markdown cell.
_HEADER_IDENTIFIER: Final[str] = "Phase-A.0"
_HEADER_TOPIC_HINT: Final[str] = "Remittance"  # must also appear
_HEADER_TARGET_HINT: Final[str] = "TRM"  # must also appear

# Anti-fishing disclaimer required substrings (case-insensitive on "not a rescue").
_DISCLAIMER_RESCUE_MARKERS: Final[tuple[str, ...]] = ("not a rescue",)
_DISCLAIMER_CPI_MARKER: Final[str] = "CPI-FAIL"
_DISCLAIMER_MTIME_MARKER: Final[str] = "2026-04-02"

# Gate-verdict placeholder required substrings.
_GATE_VERDICT_HEADING: Final[str] = "Gate Verdict"
_GATE_VERDICT_STATUS: Final[str] = "populated after NB2 and NB3"


def _read_notebook(path: Path) -> nbformat.NotebookNode:
    """Read a notebook file via nbformat.read at v4. Raises on invalid format."""
    assert path.is_file(), f"notebook not found: {path}"
    with path.open("r", encoding="utf-8") as fh:
        nb = nbformat.read(fh, as_version=4)
    # nbformat.read validates the structure; the return type is NotebookNode.
    return nb


def _markdown_sources(nb: nbformat.NotebookNode) -> list[str]:
    return [c.get("source", "") for c in nb.cells if c.get("cell_type") == "markdown"]


def _code_cells(nb: nbformat.NotebookNode) -> list[nbformat.NotebookNode]:
    return [c for c in nb.cells if c.get("cell_type") == "code"]


# ---------------------------------------------------------------------------
# Per-notebook assertions (parametrized by file name)
# ---------------------------------------------------------------------------


def test_notebook_files_exist() -> None:
    """All three skeleton notebooks must exist on disk."""
    for name in _NOTEBOOKS:
        path = _COLOMBIA_DIR / name
        assert path.is_file(), f"missing notebook: {path}"


def test_notebooks_are_valid_nbformat_v4() -> None:
    """Each notebook must be readable by nbformat.read at v4 without errors."""
    for name in _NOTEBOOKS:
        path = _COLOMBIA_DIR / name
        nb = _read_notebook(path)
        # nbformat_major must be 4 (current format). Some readers also carry
        # nbformat_minor; we don't pin that.
        assert nb.nbformat == 4, (
            f"{name}: expected nbformat major=4, got {nb.nbformat}"
        )


def test_notebooks_have_phase_a0_header() -> None:
    """First markdown cell of each notebook carries the Phase-A.0 identifier."""
    for name in _NOTEBOOKS:
        nb = _read_notebook(_COLOMBIA_DIR / name)
        md_sources = _markdown_sources(nb)
        assert md_sources, f"{name}: no markdown cells found"
        head = md_sources[0]
        assert _HEADER_IDENTIFIER in head, (
            f"{name}: first markdown cell missing '{_HEADER_IDENTIFIER}' — got:\n{head[:200]}"
        )
        assert _HEADER_TOPIC_HINT.lower() in head.lower(), (
            f"{name}: first markdown cell missing topic hint '{_HEADER_TOPIC_HINT}'"
        )
        assert _HEADER_TARGET_HINT in head, (
            f"{name}: first markdown cell missing target hint '{_HEADER_TARGET_HINT}'"
        )


def test_notebooks_carry_anti_fishing_disclaimer() -> None:
    """A markdown cell must carry BOTH 'NOT a rescue'+'CPI-FAIL' AND the 2026-04-02 anchor.

    We allow the disclaimer to span a single cell OR to split the rescue/CPI
    pairing and the mtime anchor across two cells — the test succeeds if
    at least one markdown cell contains all three markers OR if the union
    of all markdown cells contains all three markers.
    """
    for name in _NOTEBOOKS:
        nb = _read_notebook(_COLOMBIA_DIR / name)
        md_sources = _markdown_sources(nb)
        combined = "\n\n".join(md_sources).lower()

        # "not a rescue" is case-insensitive.
        assert any(m.lower() in combined for m in _DISCLAIMER_RESCUE_MARKERS), (
            f"{name}: missing 'NOT a rescue' disclaimer substring"
        )
        assert _DISCLAIMER_CPI_MARKER.lower() in combined, (
            f"{name}: missing 'CPI-FAIL' disclaimer substring"
        )
        assert _DISCLAIMER_MTIME_MARKER in combined, (
            f"{name}: missing '2026-04-02' mtime provenance substring"
        )


def test_notebooks_carry_gate_verdict_placeholder() -> None:
    """A markdown cell must flag the Gate Verdict as populated after NB2+NB3."""
    for name in _NOTEBOOKS:
        nb = _read_notebook(_COLOMBIA_DIR / name)
        md_sources = _markdown_sources(nb)
        combined = "\n\n".join(md_sources)
        assert _GATE_VERDICT_HEADING in combined, (
            f"{name}: missing 'Gate Verdict' section/heading"
        )
        assert _GATE_VERDICT_STATUS in combined, (
            f"{name}: missing 'populated after NB2 and NB3' status sentence"
        )


def test_notebooks_have_zero_code_cells() -> None:
    """Task 8 skeletons are markdown-only; code cells arrive via Task 16+ X-trio."""
    for name in _NOTEBOOKS:
        nb = _read_notebook(_COLOMBIA_DIR / name)
        code = _code_cells(nb)
        assert len(code) == 0, (
            f"{name}: expected 0 code cells, found {len(code)} — "
            "code authoring is deferred to Task 16+ X-trio protocol"
        )


# ---------------------------------------------------------------------------
# Jinja2 README template + placeholder README.md
# ---------------------------------------------------------------------------


def test_readme_template_exists_with_seven_h2_sections() -> None:
    """The Jinja2 template must exist and carry ≥ 7 H2 headings (Rev-4 parity)."""
    assert _TEMPLATE.is_file(), f"missing Jinja2 template: {_TEMPLATE}"
    text = _TEMPLATE.read_text(encoding="utf-8")
    # Count lines starting with exactly '## ' (H2, not H3+).
    h2_lines = [
        line for line in text.splitlines()
        if line.startswith("## ") and not line.startswith("### ")
    ]
    assert len(h2_lines) >= 7, (
        f"expected ≥ 7 H2 headings in template, got {len(h2_lines)}: {h2_lines}"
    )


def test_readme_template_uses_remittance_wording() -> None:
    """Template must swap CPI wording for remittance wording (Task 8 scope rule)."""
    text = _TEMPLATE.read_text(encoding="utf-8")
    # Must mention remittance (case-insensitive).
    assert "remittance" in text.lower(), (
        "template appears to still reference CPI exclusively; "
        "wording-swap from Rev-4 not performed"
    )


def test_readme_placeholder_is_short_and_flags_task_24() -> None:
    """README.md must be a < 300-byte placeholder pointing to Task 24 auto-render."""
    assert _README.is_file(), f"missing placeholder README: {_README}"
    size = _README.stat().st_size
    assert size < 300, (
        f"README.md too large ({size} bytes) — Task 8 placeholder must be "
        "< 300 bytes; the rich auto-render is produced by Task 24"
    )
    text = _README.read_text(encoding="utf-8")
    # Must reference Task 24 explicitly so reviewers know this is a stub.
    assert "Task 24" in text, (
        "placeholder README.md must reference 'Task 24' as the auto-render owner"
    )
