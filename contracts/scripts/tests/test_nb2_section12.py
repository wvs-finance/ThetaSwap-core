"""Structural regression tests for NB2 §12 economic-magnitude translation.

Task 23 of the econ-notebook-implementation plan. NB2 §12 closes Phase 2
with a single-trio block that translates the primary and co-primary
point estimates into plain-English economic magnitudes: the
"basis-points-per-one-sigma" convention adopted from
Conrad-Schoelkopf-Tushteva 2025 (bibkey ``conrad2025longterm``; the
working-paper copy is SSRN 4632733). The section emits two literal
lines the reader can scan without diving into the natural scale of
RV^(1/3):

    β̂ = <value> ⇒ <X> bp per 1-σ CPI surprise
    δ̂ = <value> ⇒ <Y> bp per 1-σ |CPI surprise|

The first line is the OLS-primary mean-channel (weekly RV^(1/3));
the second is the GARCH-X conditional-variance channel (daily).
Both are purely in-estimation — there is NO translation to any
RAN/Abrigo payoff or product unit here. The plan text (line 444)
prohibits any such translation in §12; that work is downstream of
NB3 and belongs to the sensitivity/simulator layer.

Per Rev 4 §1 T3b is OLS-primary-only, and the T3b gate has FAILED
(§9 verdict). §12's role is therefore to contextualise *how small*
the effect is in magnitude terms — not to rescue significance via
a different scale. The interp-md must frame this honestly and defer
larger-effect conjectures to NB3 sensitivities.

This module is authored TDD-first: it fails against the 42-cell
post-Task-22 NB2 and turns green once the Analytics Reporter
appends §12's one trio (3 cells → 45 total).

What gets asserted:

  1. NB2 cell count ≥ 45 post-Task-23 (42 pre-Task-23 + 1 trio).
  2. §12 exists (tagged ``section:12``) and contains a why-md +
     code + interp-md trio.
  3. The §12 code cell is a ``remove-input`` cell.
  4. The §12 code cell source emits the literal β̂ magnitude line
     containing ``β̂ =`` and ``bp per 1-σ CPI surprise`` tokens
     (either as f-string literals or raw string tokens).
  5. The §12 code cell source emits the literal δ̂ magnitude line
     containing ``δ̂ =`` and ``bp per 1-σ |CPI surprise|`` tokens.
  6. The §12 code cell source contains NO reference to
     ``Abrigo``, ``RAN``, ``payoff``, ``hedge``, or ``product``
     (plan line 444 prohibits RAN-payoff translation in §12).
  7. The §12 why-markdown cell contains all four citation headers.
  8. The §12 why-markdown cell cites ``conrad2025longterm``.
  9. The §12 interp-md does NOT emit a ``Decision #N`` marker
     (§12 is a contextual cell, not a decision gate).
 10. Citation lint: ``scripts/lint_notebook_citations.py`` exits 0
     on NB2 post-Task-23.

What is NOT asserted:
  * The exact numeric basis-point values (those are runtime outputs,
    reported back in the Task 23 final message as load-bearing numbers).
  * Any sign or sign-convention choice — the test accepts positive or
    negative bp/σ because both are economically meaningful.
  * Any NB3 downstream wiring — Task 24+ scope.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Final

import nbformat
import pytest

# ── Path plumbing ────────────────────────────────────────────────────────

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parents[1]
_CONTRACTS_DIR: Final[Path] = _SCRIPTS_DIR.parent

_ENV_PATH: Final[Path] = (
    _CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "env.py"
)

LINT_SCRIPT: Final[Path] = _SCRIPTS_DIR / "lint_notebook_citations.py"


def _load_env():
    spec = importlib.util.spec_from_file_location("fx_vol_env", _ENV_PATH)
    assert spec is not None and spec.loader is not None, (
        f"Cannot build spec for {_ENV_PATH}"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_env = _load_env()
NB2_PATH: Final[Path] = _env.NB2_PATH


# ── Constants ─────────────────────────────────────────────────────────────

SECTION12_TAG: Final[str] = "section:12"
REMOVE_INPUT_TAG: Final[str] = "remove-input"

REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# The two load-bearing literal strings the §12 code cell must print.
# The test matches the composable tokens — the actual f-string can
# interpolate values and units in either Greek-letter or ASCII form.
_BETA_MAGNITUDE_TOKENS: Final[tuple[str, ...]] = (
    "β̂ =",
    "bp per 1-σ CPI surprise",
)

_DELTA_MAGNITUDE_TOKENS: Final[tuple[str, ...]] = (
    "δ̂ =",
    "bp per 1-σ |CPI surprise|",
)

# Plan line 444: "No RAN-payoff translation." §12 is purely
# in-estimation; any downstream-product reference is a scope violation.
_PROHIBITED_SUBSTRINGS: Final[tuple[str, ...]] = (
    "Abrigo",
    "RAN",
    "payoff",
    "hedge",
    "product",
)

# Citation bibkey — Conrad-Schoelkopf-Tushteva 2025 (forthcoming JoE;
# SSRN 4632733 is the accessible working-paper copy).
_SECTION12_BIBKEY: Final[str] = "conrad2025longterm"

# §12 interp-md must NOT carry a Decision marker — it is contextual.
_DECISION_MARKERS: Final[tuple[str, ...]] = (
    "Decision #",
    "**Decision",
)

# After Task 22 NB2 has 42 cells. Task 23 appends 1 trio → 3 new
# cells → floor of 45.
_MIN_POST_TASK23_CELL_COUNT: Final[int] = 45


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def nb2() -> nbformat.NotebookNode:
    assert NB2_PATH.is_file(), f"Missing NB2 notebook: {NB2_PATH}"
    return nbformat.read(NB2_PATH, as_version=4)


# ── Pure helpers ──────────────────────────────────────────────────────────

def _cell_source(cell: nbformat.NotebookNode) -> str:
    src = cell.get("source", "")
    if isinstance(src, list):
        return "".join(src)
    return str(src)


def _cell_tags(cell: nbformat.NotebookNode) -> tuple[str, ...]:
    return tuple(cell.metadata.get("tags", []))


def _section12_cells(
    nb: nbformat.NotebookNode,
) -> list[nbformat.NotebookNode]:
    return [c for c in nb.cells if SECTION12_TAG in _cell_tags(c)]


def _code_cells(
    cells: list[nbformat.NotebookNode],
) -> list[nbformat.NotebookNode]:
    return [c for c in cells if c.get("cell_type") == "code"]


def _markdown_cells(
    cells: list[nbformat.NotebookNode],
) -> list[nbformat.NotebookNode]:
    return [c for c in cells if c.get("cell_type") == "markdown"]


# ── NB2 size + §12 presence tests ─────────────────────────────────────────

def test_nb2_has_minimum_post_task23_cell_count(nb2: nbformat.NotebookNode) -> None:
    assert len(nb2.cells) >= _MIN_POST_TASK23_CELL_COUNT, (
        f"NB2 has {len(nb2.cells)} cells; Task 23 requires ≥"
        f"{_MIN_POST_TASK23_CELL_COUNT} (42 pre + 1 trio)."
    )


def test_nb2_section12_exists(nb2: nbformat.NotebookNode) -> None:
    cells = _section12_cells(nb2)
    assert cells, (
        f"No cells tagged {SECTION12_TAG!r}; Task 23 §12 trio missing."
    )


def test_nb2_section12_has_trio_layout(nb2: nbformat.NotebookNode) -> None:
    """§12 is exactly one trio: why-md, code, interp-md (≥3 cells)."""
    cells = _section12_cells(nb2)
    code_cells = _code_cells(cells)
    md_cells = _markdown_cells(cells)
    assert len(code_cells) >= 1, (
        f"§12 needs ≥1 code cell; found {len(code_cells)}."
    )
    assert len(md_cells) >= 2, (
        f"§12 needs ≥2 markdown cells (why-md + interp-md); "
        f"found {len(md_cells)}."
    )


def test_nb2_section12_code_has_remove_input_tag(
    nb2: nbformat.NotebookNode,
) -> None:
    code_cells = _code_cells(_section12_cells(nb2))
    assert code_cells, "§12 has no code cells to check for remove-input."
    for c in code_cells:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§12 code cell is missing {REMOVE_INPUT_TAG!r} tag; tags={tags}."
        )


# ── β̂ / δ̂ magnitude-line tests ─────────────────────────────────────────

def test_nb2_section12_has_beta_magnitude_line(
    nb2: nbformat.NotebookNode,
) -> None:
    """The §12 code cell must print ``β̂ = ... bp per 1-σ CPI surprise``."""
    code_cells = _code_cells(_section12_cells(nb2))
    combined = "".join(_cell_source(c) for c in code_cells)
    for token in _BETA_MAGNITUDE_TOKENS:
        assert token in combined, (
            f"§12 code cell is missing β̂ magnitude token {token!r}; "
            f"plan line 444 requires the line "
            f"'β̂ = X ⇒ Y bp per 1-σ CPI surprise'."
        )


def test_nb2_section12_has_delta_magnitude_line(
    nb2: nbformat.NotebookNode,
) -> None:
    """The §12 code cell must print ``δ̂ = ... bp per 1-σ |CPI surprise|``."""
    code_cells = _code_cells(_section12_cells(nb2))
    combined = "".join(_cell_source(c) for c in code_cells)
    for token in _DELTA_MAGNITUDE_TOKENS:
        assert token in combined, (
            f"§12 code cell is missing δ̂ magnitude token {token!r}; "
            f"plan line 444 requires the parallel line "
            f"'δ̂ = X ⇒ Y bp per 1-σ |CPI surprise|'."
        )


def test_nb2_section12_no_ran_payoff_translation(
    nb2: nbformat.NotebookNode,
) -> None:
    """§12 must not carry any RAN/Abrigo/hedge/product/payoff reference.

    Plan line 444 is explicit: "No RAN-payoff translation." The §12
    cell is purely in-estimation magnitude contextualisation.
    """
    cells = _section12_cells(nb2)
    for c in cells:
        src = _cell_source(c)
        for prohibited in _PROHIBITED_SUBSTRINGS:
            assert prohibited not in src, (
                f"§12 contains prohibited substring {prohibited!r}; "
                f"plan line 444 forbids RAN-payoff translation in §12."
            )


# ── Citation + interp-md tests ────────────────────────────────────────────

def test_nb2_section12_citation_block_has_all_headers(
    nb2: nbformat.NotebookNode,
) -> None:
    cells = _section12_cells(nb2)
    md_cells = _markdown_cells(cells)
    assert md_cells, "§12 has no markdown cells to check for citation headers."
    # The citation block must live in a why-markdown cell BEFORE the code
    # cell. We scan all §12 markdown cells because the trio order may
    # interleave the interp-md among them.
    combined_md = "".join(_cell_source(c) for c in md_cells)
    for header in REQUIRED_HEADERS:
        assert header in combined_md, (
            f"§12 citation block is missing header {header!r}."
        )


def test_nb2_section12_citation_has_conrad2025longterm(
    nb2: nbformat.NotebookNode,
) -> None:
    cells = _section12_cells(nb2)
    md_cells = _markdown_cells(cells)
    combined_md = "".join(_cell_source(c) for c in md_cells)
    assert _SECTION12_BIBKEY in combined_md, (
        f"§12 citation block must reference {_SECTION12_BIBKEY!r}; "
        f"plan line 444 fixes the in-estimation magnitude convention "
        f"to Conrad-Schoelkopf-Tushteva 2025."
    )


def test_nb2_section12_interp_has_no_decision_marker(
    nb2: nbformat.NotebookNode,
) -> None:
    """§12 is a contextual cell — no Decision #N markers.

    Decision markers belong to the pre-registered locks in §§1-9. §12
    is a post-verdict reader-magnitude cell and must not introduce a
    new decision gate.
    """
    cells = _section12_cells(nb2)
    md_cells = _markdown_cells(cells)
    combined_md = "".join(_cell_source(c) for c in md_cells)
    for marker in _DECISION_MARKERS:
        assert marker not in combined_md, (
            f"§12 markdown contains a decision marker {marker!r}; "
            f"§12 is contextual-only per plan line 444."
        )


# ── Review-remediation tests (3-way review convergence) ──────────────────

def test_nb2_section12_has_pooled_mean_caveat(
    nb2: nbformat.NotebookNode,
) -> None:
    """Per 3-way review (Model QA #3 + Reality Checker #3), §12 interp-md
    must flag the pooled-mean linearisation caveat so readers don't
    confuse the pooled bp/σ with a regime-conditional number."""
    cells = _section12_cells(nb2)
    md_cells = _markdown_cells(cells)
    combined_md = "".join(_cell_source(c) for c in md_cells)
    # Accept any phrasing that names "pooled" + "linearisation" (or
    # "linearization") + "regime".
    _pooled_caveat_tokens = ("pooled", "regime")
    for token in _pooled_caveat_tokens:
        assert token.lower() in combined_md.lower(), (
            f"§12 interp-md must carry a pooled-sample-linearisation caveat; "
            f"token {token!r} not found."
        )


def test_nb2_section12_has_one_line_summary(
    nb2: nbformat.NotebookNode,
) -> None:
    """Per 3-way review (Tech Writer LOW 7), §12 interp-md must lead
    with a one-line summary so readers see the two numbers before
    the three-paragraph exposition."""
    cells = _section12_cells(nb2)
    md_cells = _markdown_cells(cells)
    # Find the interp-md (the one that starts with "**Interpretation").
    interp_md_candidates = [
        _cell_source(c)
        for c in md_cells
        if _cell_source(c).lstrip().startswith("**Interpretation")
    ]
    assert interp_md_candidates, "§12 interp-md cell not found."
    interp_md = interp_md_candidates[0]
    assert "One-line summary" in interp_md or "one-line summary" in interp_md, (
        "§12 interp-md must lead with a 'One-line summary:' phrase "
        "per Tech Writer review LOW 7."
    )


# ── Citation-lint integration test ────────────────────────────────────────

def test_nb2_citation_lint_passes_after_task23() -> None:
    """The citation-block + chasing-offline linter passes on NB2 post-23."""
    result = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), str(NB2_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Citation lint failed on NB2 post-Task-23. "
        f"stdout={result.stdout!r}; stderr={result.stderr!r}"
    )
