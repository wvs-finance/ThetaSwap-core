"""Structural + behavioural regression tests for NB3 §9 (material-mover
spotlight + two-pronged rule + anti-fishing halt on upstream T3b FAIL)
— Task 28 of the econ-notebook implementation plan.

The plan's verbatim deliverable (lines 517-527):

    Two-pronged material-mover rule: a sensitivity is material iff β̂
    falls outside the primary's 90% CI AND the T3b sign/significance
    classification changes. Synthetic fits exercise both prongs. Also
    asserts: if upstream T3b FAILed, NB3 halts before §9 with an
    explicit "gate failed, halting" message and zero spotlight tables
    produced. Citation references Leamer 1983/1985 + Ankel-Peters-
    Brodeur 2024.

This test file covers BOTH branches:

  (A) Real-state branch (T3b = FAIL, our live state per NB2):
      §9 emits the halt message, binds ``SPOTLIGHT_STATUS =
      "halted_on_gate_fail"``, and produces zero material-mover
      tables. The forest-plot rows computed in §8 (Task 27) are the
      complete sensitivity record; §9 does NOT cherry-pick post-hoc
      spotlights.

  (B) Counterfactual / synthetic branch (T3b = PASS):
      A private helper ``_compute_material_movers`` (authored in the
      §9 code cell) applies the two-pronged rule to a list of
      sensitivity fits: a row is MATERIAL iff β̂ falls outside the
      primary's 90% CI AND the T3b sign/significance classification
      flips. Synthetic inputs exercise each prong in isolation + both
      prongs jointly.

The Leamer 1983/1985 reference is carried in PROSE ONLY — the
references.bib has no ``leamer*`` bib key as of Task 28, per the plan's
"flexible on Leamer citation bib-key availability" note. The two
bib-keyed references required are ``@ankelPeters2024protocol``
(anti-fishing I4R protocol §2) and ``@simonsohn2020specification``
(specification-curve discipline).

Tests are TDD-first: written to fail against the 27-cell Task-27
baseline (SHA 29b209dd8) and pass after Task 28's 1 trio (= 3 cells)
extends NB3 to 30 cells.

What gets asserted, in order of decreasing "load-bearing":

  1. Cell count: 30 after Task 28 (3 new cells beyond Task 27's 27).
  2. §9 exists: at least one ``section:9`` code cell, every code cell
     has ``remove-input``.
  3. §9 real-state branch halts: with the live NB2 PKL (T3b = FAIL),
     executing §9 binds ``SPOTLIGHT_STATUS = "halted_on_gate_fail"``
     and emits the literal halt message substring
     ``GATE FAILED — HALTING §9`` (unicode stop sign optional in the
     test; we check for the ASCII-identifying substring).
  4. §9 real-state branch produces zero material-mover tables:
     ``material_movers`` binds to an empty list (or the §9 namespace
     does not define a non-empty spotlight container).
  5. §9 exposes a pure helper ``_compute_material_movers`` taking
     ``(sensitivities, primary_fit, t3b_verdict)`` and returning a
     ``(material_rows, halt_flag)`` tuple.
  6. Synthetic PASS branch: helper returns the halt flag FALSE and a
     non-empty ``material_rows`` list when given a sensitivity with β̂
     outside the primary's 90% CI AND a classification flip.
  7. Synthetic PASS branch — prong 1 alone: β̂ outside CI but no
     classification change → NOT material.
  8. Synthetic PASS branch — prong 2 alone: classification change but
     β̂ inside CI → NOT material.
  9. §9 citation block references ``@simonsohn2020specification``.
 10. §9 citation block references ``@ankelPeters2024protocol``.
 11. §9 citation block carries a Leamer reference — either a bib key
     matching ``leamer*`` (if future task adds it) OR the literal
     token "Leamer" in prose.
 12. Citation lint clean: ``lint_notebook_citations.py`` exits 0.

What is NOT asserted:
  * Exact halt-message punctuation (unicode stop sign, em-dash
    variants) — only the ASCII substring "GATE FAILED" + "HALTING"
    + "§9" (or "section 9") is required.
  * Which specific forest-plot rows would have been spotlighted in the
    counterfactual (would couple to the PKL snapshot numerics).
  * Exact helper signature (positional vs. keyword) — we call it with
    keyword arguments to be signature-robust.

No mocks — reads the real NB3 on disk and the real PKL / panel. §9 code
executes end-to-end on top of §1-§8's bootstrap so the T3b re-derivation
is exercised against the live ``column6_fit`` and the halt branch
triggers naturally.
"""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
from pathlib import Path
from typing import Final

import nbformat
import pytest

# ── Path plumbing (mirrors test_nb3_section7_8.py) ────────────────────────

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
    """Load env.py as a module by file path (it is not on sys.path)."""
    spec = importlib.util.spec_from_file_location("fx_vol_env", _ENV_PATH)
    assert spec is not None and spec.loader is not None, (
        f"Cannot build spec for {_ENV_PATH}"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_env = _load_env()
NB3_PATH: Final[Path] = _env.NB3_PATH
FULL_PKL_PATH: Final[Path] = _env.FULL_PKL_PATH


# ── Constants ─────────────────────────────────────────────────────────────

SECTION1_TAG: Final[str] = "section:1"
SECTION7_TAG: Final[str] = "section:7"
SECTION8_TAG: Final[str] = "section:8"
SECTION9_TAG: Final[str] = "section:9"
REMOVE_INPUT_TAG: Final[str] = "remove-input"

REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# §9 landmarks.
_SPOTLIGHT_STATUS_VAR: Final[str] = "SPOTLIGHT_STATUS"
_SPOTLIGHT_STATUS_HALT_VALUE: Final[str] = "halted_on_gate_fail"
_MATERIAL_MOVERS_VAR: Final[str] = "material_movers"
_COMPUTE_HELPER_NAME: Final[str] = "_compute_material_movers"

# Halt message tokens the code MUST emit (plan line 527, verbatim).
_HALT_SUBSTRINGS_REQUIRED: Final[tuple[str, ...]] = (
    "GATE FAILED",
    "HALTING",
)
_HALT_SECTION_TOKENS: Final[tuple[str, ...]] = ("§9", "section 9", "Section 9")

# Citation bib keys.
_SIMONSOHN2020_KEY: Final[str] = "simonsohn2020specification"
_ANKELPETERS2024_KEY: Final[str] = "ankelPeters2024protocol"
_LEAMER_PROSE_TOKEN: Final[str] = "Leamer"

# Task 28 target: 27 cells (Task 27 baseline) + 3 cells (1 trio) = 30.
_POST_TASK28_CELL_COUNT: Final[int] = 30


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def nb3() -> nbformat.NotebookNode:
    assert NB3_PATH.is_file(), f"Missing NB3 notebook: {NB3_PATH}"
    return nbformat.read(NB3_PATH, as_version=4)


# ── Pure helpers ──────────────────────────────────────────────────────────

def _cell_source(cell: nbformat.NotebookNode) -> str:
    src = cell.get("source", "")
    if isinstance(src, list):
        return "".join(src)
    return str(src)


def _cell_tags(cell: nbformat.NotebookNode) -> tuple[str, ...]:
    return tuple(cell.metadata.get("tags", []))


def _section_cells(
    nb: nbformat.NotebookNode, section_tag: str
) -> list[nbformat.NotebookNode]:
    return [c for c in nb.cells if section_tag in _cell_tags(c)]


def _code_cells(
    cells: list[nbformat.NotebookNode],
) -> list[nbformat.NotebookNode]:
    return [c for c in cells if c.get("cell_type") == "code"]


def _markdown_cells(
    cells: list[nbformat.NotebookNode],
) -> list[nbformat.NotebookNode]:
    return [c for c in cells if c.get("cell_type") == "markdown"]


def _section_source(
    nb: nbformat.NotebookNode, section_tag: str
) -> str:
    return "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb, section_tag))
    )


# ── Shared bootstrap for §9 execution ─────────────────────────────────────
#
# §9 needs the live PKL (T3b re-derivation reads column6_fit) + the
# §7/§8 namespace for the helper + forest_table it consumes when the
# halt branch is NOT active. We concatenate §1 bootstrap-equivalent +
# §7 + §8 + §9 so execution is end-to-end.
def _make_bootstrap() -> str:
    return (
        "import sys\n"
        f"sys.path.insert(0, {str(_CONTRACTS_DIR)!r})\n"
        f"sys.path.insert(0, {str(_ENV_PATH.parent)!r})\n"
        "import duckdb\n"
        "import pickle\n"
        "import env\n"
        "from scripts import cleaning\n"
        "from scripts import econ_query_api\n"
        "conn = duckdb.connect(str(env.DUCKDB_PATH), read_only=True)\n"
        "_panel = cleaning.load_cleaned_panel(conn)\n"
        "panel = _panel\n"
        "weekly = _panel.weekly\n"
        "with open(env.FULL_PKL_PATH, 'rb') as _fh:\n"
        "    _pkl = pickle.load(_fh)\n"
        "pkl_degraded = False\n"
        "column6_fit = _pkl['column6_fit']\n"
        "ladder_fits = _pkl['ladder_fits']\n"
        "decomposition_fit = _pkl['decomposition_fit']\n"
        "regime_fits = _pkl['regime_fits']\n"
        "garch_x = _pkl['garch_x']\n"
    )


def _exec_section9(nb: nbformat.NotebookNode) -> dict[str, object]:
    """Exec §1-adjacent bootstrap + §7 + §8 + §9 source; return namespace.

    The halt branch fires naturally when T3b FAILs on the live PKL, so
    the §9 code we execute here is the same code that runs in the
    notebook.
    """
    s7_code_src = _section_source(nb, SECTION7_TAG)
    s8_code_src = _section_source(nb, SECTION8_TAG)
    s9_code_src = _section_source(nb, SECTION9_TAG)
    assert s9_code_src, "§9 code must exist."
    ns: dict[str, object] = {}
    exec(
        compile(
            _make_bootstrap()
            + "\n"
            + s7_code_src
            + "\n"
            + s8_code_src
            + "\n"
            + s9_code_src,
            "<nb3-section9>",
            "exec",
        ),
        ns,
    )
    return ns


# ── Cell-count gate ───────────────────────────────────────────────────────

def test_nb3_has_task28_cell_count(nb3: nbformat.NotebookNode) -> None:
    """NB3 grows from 27 cells (Task 27) to 30 cells (Task 28 = +1 trio)."""
    assert len(nb3.cells) >= _POST_TASK28_CELL_COUNT, (
        f"NB3 has {len(nb3.cells)} cells; Task 28 must author 3 new cells "
        f"(1 trio: §9 material-mover halt) for a total of "
        f"{_POST_TASK28_CELL_COUNT}."
    )


# ── §9 structural tests ───────────────────────────────────────────────────

def test_nb3_section9_has_at_least_one_code_cell(
    nb3: nbformat.NotebookNode,
) -> None:
    """§9 exists: at least one code cell + every code cell has remove-input."""
    s9_code = _code_cells(_section_cells(nb3, SECTION9_TAG))
    assert s9_code, (
        "§9 must contain at least one code cell (tagged section:9); "
        "none found."
    )
    for c in s9_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§9 code cell missing 'remove-input' tag; got tags={tags!r}."
        )


# ── §9 real-state behaviour (T3b = FAIL) ──────────────────────────────────

def test_nb3_section9_halt_on_t3b_fail_real_state(
    nb3: nbformat.NotebookNode,
) -> None:
    """With the live PKL (T3b = FAIL), §9 halts and binds SPOTLIGHT_STATUS."""
    ns = _exec_section9(nb3)
    assert _SPOTLIGHT_STATUS_VAR in ns, (
        f"§9 must bind {_SPOTLIGHT_STATUS_VAR!r}. "
        f"Found names: {sorted(k for k in ns if not k.startswith('__'))!r}"
    )
    status = str(ns[_SPOTLIGHT_STATUS_VAR])
    assert status == _SPOTLIGHT_STATUS_HALT_VALUE, (
        f"{_SPOTLIGHT_STATUS_VAR!r} must equal "
        f"{_SPOTLIGHT_STATUS_HALT_VALUE!r} under the live T3b = FAIL "
        f"state; got {status!r}."
    )


def test_nb3_section9_halt_message_in_source(
    nb3: nbformat.NotebookNode,
) -> None:
    """§9 source carries the literal 'GATE FAILED' + 'HALTING' + §9 token."""
    src = _section_source(nb3, SECTION9_TAG)
    for tok in _HALT_SUBSTRINGS_REQUIRED:
        assert tok in src, (
            f"§9 source must carry the halt-message substring {tok!r} "
            f"(plan line 527 verbatim). Not found."
        )
    assert any(t in src for t in _HALT_SECTION_TOKENS), (
        f"§9 halt message must identify the section — one of "
        f"{_HALT_SECTION_TOKENS!r} must appear in §9 source. "
        f"None found."
    )


def test_nb3_section9_zero_spotlight_tables_on_halt(
    nb3: nbformat.NotebookNode,
) -> None:
    """Under T3b = FAIL, §9 produces zero material-mover rows."""
    ns = _exec_section9(nb3)
    # Either material_movers is bound to an empty list, OR the §9 code
    # never computes it (halt short-circuits before the loop). Both
    # outcomes satisfy the anti-fishing invariant.
    movers = ns.get(_MATERIAL_MOVERS_VAR, [])
    try:
        n_movers = len(movers)  # type: ignore[arg-type]
    except TypeError:
        pytest.fail(
            f"{_MATERIAL_MOVERS_VAR!r} bound to non-sequence "
            f"{type(movers).__name__!r}; expected empty list under halt."
        )
    assert n_movers == 0, (
        f"Under the live T3b = FAIL state, §9 must produce ZERO "
        f"material-mover spotlight rows. Got n={n_movers}. Anti-fishing "
        f"violation: sensitivities in §8 forest plot + appendix are the "
        f"complete record."
    )


# ── §9 two-pronged rule behaviour (synthetic) ─────────────────────────────

def _synthetic_material_mover_fixture() -> dict[str, object]:
    """Build synthetic inputs exercising the two-pronged rule.

    primary_fit has β̂ = +0.010, SE = 0.005 → 90% CI = [+0.00178, +0.01823].
    T3b-PASS signature on primary: β̂ − 1.28·SE = +0.0036 > 0 → POSITIVE
    & SIGNIFICANT (the "classification" the rule compares against).

    Sensitivities:
      * s_both   : β̂ = +0.030, SE = 0.005 (outside primary CI AND
                   flips classification by magnitude — still positive &
                   significant but far away). To actually flip
                   classification we pair it with an opposite-sign β̂.
      * s_flip_only : β̂ inside primary CI but classification flipped
                      (negative & significant): β̂ = +0.010, SE = 0.001
                      does NOT flip — instead use β̂ = -0.020, SE =
                      0.002: outside CI + flipped (sign negative).
      * s_ci_only : β̂ outside CI but classification unchanged
                    (still positive & significant): β̂ = +0.025,
                    SE = 0.001.
      * s_inside_same : β̂ = +0.012, SE = 0.010 inside CI + same class
                        (positive & significant / or marginal). NOT
                        material.

    The helper is called with t3b_verdict = "PASS" (synthetic PASS
    branch) so the halt short-circuit does NOT fire.
    """
    primary = {
        "beta": 0.010,
        "se": 0.005,
        "ci_lo_90": 0.010 - 1.645 * 0.005,
        "ci_hi_90": 0.010 + 1.645 * 0.005,
        "classification": "positive_significant",
    }
    sensitivities = [
        # Both prongs → MATERIAL.
        {
            "label": "s_both",
            "beta": -0.030,  # outside CI (below) AND sign flipped
            "se": 0.005,
            "classification": "negative_significant",
        },
        # Only CI-outside, classification unchanged → NOT material.
        {
            "label": "s_ci_only",
            "beta": 0.025,  # outside CI (above) but still positive-sig
            "se": 0.001,
            "classification": "positive_significant",
        },
        # Only classification flipped, β̂ inside CI → NOT material.
        {
            "label": "s_flip_only",
            "beta": 0.009,  # well inside CI
            "se": 0.002,
            "classification": "negative_significant",
        },
        # Inside CI + same class → NOT material.
        {
            "label": "s_inside_same",
            "beta": 0.012,
            "se": 0.010,
            "classification": "positive_significant",
        },
    ]
    return {"primary": primary, "sensitivities": sensitivities}


def _exec_helper(nb: nbformat.NotebookNode) -> object:
    """Execute §9 source and return the _compute_material_movers helper."""
    ns = _exec_section9(nb)
    helper = ns.get(_COMPUTE_HELPER_NAME)
    assert helper is not None, (
        f"§9 must define helper {_COMPUTE_HELPER_NAME!r}. "
        f"Found names: {sorted(k for k in ns if not k.startswith('__'))!r}"
    )
    assert callable(helper), (
        f"{_COMPUTE_HELPER_NAME!r} must be callable; got "
        f"type={type(helper).__name__!r}."
    )
    return helper


def test_nb3_section9_helper_exists_and_is_callable(
    nb3: nbformat.NotebookNode,
) -> None:
    """§9 exposes a pure helper ``_compute_material_movers``."""
    _ = _exec_helper(nb3)  # raises if helper missing / non-callable


def test_nb3_section9_helper_halts_on_t3b_fail(
    nb3: nbformat.NotebookNode,
) -> None:
    """helper(t3b_verdict='FAIL', ...) returns empty + halt flag True."""
    helper = _exec_helper(nb3)
    fixt = _synthetic_material_mover_fixture()
    result = helper(  # type: ignore[misc]
        sensitivities=fixt["sensitivities"],
        primary_fit=fixt["primary"],
        t3b_verdict="FAIL",
    )
    # Helper returns (material_rows, halt_flag) tuple.
    assert isinstance(result, tuple) and len(result) == 2, (
        f"{_COMPUTE_HELPER_NAME!r} must return a 2-tuple "
        f"(material_rows, halt_flag); got type={type(result).__name__!r} "
        f"len={len(result) if hasattr(result, '__len__') else 'N/A'!r}."
    )
    material_rows, halt_flag = result
    assert bool(halt_flag) is True, (
        f"{_COMPUTE_HELPER_NAME!r}(t3b_verdict='FAIL', ...) must return "
        f"halt_flag = True; got {halt_flag!r}."
    )
    assert len(material_rows) == 0, (
        f"{_COMPUTE_HELPER_NAME!r}(t3b_verdict='FAIL', ...) must return "
        f"zero material rows; got n={len(material_rows)}."
    )


def test_nb3_section9_helper_applies_two_pronged_rule_both_prongs(
    nb3: nbformat.NotebookNode,
) -> None:
    """Under synthetic PASS + both prongs → one material row (s_both)."""
    helper = _exec_helper(nb3)
    fixt = _synthetic_material_mover_fixture()
    material_rows, halt_flag = helper(  # type: ignore[misc]
        sensitivities=fixt["sensitivities"],
        primary_fit=fixt["primary"],
        t3b_verdict="PASS",
    )
    assert bool(halt_flag) is False, (
        f"{_COMPUTE_HELPER_NAME!r}(t3b_verdict='PASS') must not halt; "
        f"got halt_flag={halt_flag!r}."
    )
    # Only s_both satisfies BOTH prongs.
    labels = [str(row.get("label") if isinstance(row, dict) else row[0])
              for row in material_rows]
    assert "s_both" in labels, (
        f"Two-pronged rule: s_both (β̂ outside CI AND classification "
        f"flipped) must be MATERIAL. Got labels={labels!r}."
    )


def test_nb3_section9_helper_rejects_ci_only_prong(
    nb3: nbformat.NotebookNode,
) -> None:
    """Prong 1 alone (β̂ outside CI, no flip) → NOT material."""
    helper = _exec_helper(nb3)
    fixt = _synthetic_material_mover_fixture()
    material_rows, _ = helper(  # type: ignore[misc]
        sensitivities=fixt["sensitivities"],
        primary_fit=fixt["primary"],
        t3b_verdict="PASS",
    )
    labels = [str(row.get("label") if isinstance(row, dict) else row[0])
              for row in material_rows]
    assert "s_ci_only" not in labels, (
        f"Two-pronged rule: s_ci_only (β̂ outside CI but SAME "
        f"classification) must NOT be material (CI alone insufficient). "
        f"Got labels={labels!r}."
    )


def test_nb3_section9_helper_rejects_flip_only_prong(
    nb3: nbformat.NotebookNode,
) -> None:
    """Prong 2 alone (classification flipped, β̂ inside CI) → NOT material."""
    helper = _exec_helper(nb3)
    fixt = _synthetic_material_mover_fixture()
    material_rows, _ = helper(  # type: ignore[misc]
        sensitivities=fixt["sensitivities"],
        primary_fit=fixt["primary"],
        t3b_verdict="PASS",
    )
    labels = [str(row.get("label") if isinstance(row, dict) else row[0])
              for row in material_rows]
    assert "s_flip_only" not in labels, (
        f"Two-pronged rule: s_flip_only (classification flipped but β̂ "
        f"INSIDE primary CI) must NOT be material (flip alone "
        f"insufficient). Got labels={labels!r}."
    )


def test_nb3_section9_helper_rejects_inside_same(
    nb3: nbformat.NotebookNode,
) -> None:
    """Neither prong triggered (β̂ inside CI + same classification) → NOT."""
    helper = _exec_helper(nb3)
    fixt = _synthetic_material_mover_fixture()
    material_rows, _ = helper(  # type: ignore[misc]
        sensitivities=fixt["sensitivities"],
        primary_fit=fixt["primary"],
        t3b_verdict="PASS",
    )
    labels = [str(row.get("label") if isinstance(row, dict) else row[0])
              for row in material_rows]
    assert "s_inside_same" not in labels, (
        f"Neither prong triggered: s_inside_same must NOT be material. "
        f"Got labels={labels!r}."
    )


# ── §9 citation tests ─────────────────────────────────────────────────────

def test_nb3_section9_citation_has_simonsohn2020(
    nb3: nbformat.NotebookNode,
) -> None:
    """§9 carries a 4-part citation block citing @simonsohn2020specification."""
    s9_md = _markdown_cells(_section_cells(nb3, SECTION9_TAG))
    citation_cells = [
        c
        for c in s9_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§9 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )
    combined = "\n\n".join(_cell_source(c) for c in citation_cells)
    assert _SIMONSOHN2020_KEY in combined, (
        f"§9 citation block must reference bib key @{_SIMONSOHN2020_KEY} "
        f"(Simonsohn-Simmons-Nelson 2020 specification curve / "
        f"anti-cherry-picking). Not found."
    )


def test_nb3_section9_citation_has_ankel_peters_2024(
    nb3: nbformat.NotebookNode,
) -> None:
    """§9 citation block references @ankelPeters2024protocol."""
    s9_md = _markdown_cells(_section_cells(nb3, SECTION9_TAG))
    citation_cells = [
        c
        for c in s9_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§9 must contain at least one markdown cell carrying all four "
        "citation headers."
    )
    combined = "\n\n".join(_cell_source(c) for c in citation_cells)
    assert _ANKELPETERS2024_KEY in combined, (
        f"§9 citation block must reference bib key "
        f"@{_ANKELPETERS2024_KEY} (Ankel-Peters I4R anti-fishing "
        f"protocol). Not found."
    )


def test_nb3_section9_citation_references_leamer(
    nb3: nbformat.NotebookNode,
) -> None:
    """§9 citation block carries a Leamer reference (bib key OR prose).

    The references.bib has no ``leamer*`` key as of Task 28 — plan
    annotation is "flexible on Leamer citation bib-key availability".
    Accept either form.
    """
    s9_md = _markdown_cells(_section_cells(nb3, SECTION9_TAG))
    citation_cells = [
        c
        for c in s9_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§9 must contain at least one markdown cell carrying all four "
        "citation headers."
    )
    combined = "\n\n".join(_cell_source(c) for c in citation_cells)
    has_bib_key = "@leamer" in combined.lower()
    has_prose = _LEAMER_PROSE_TOKEN in combined
    assert has_bib_key or has_prose, (
        f"§9 citation block must carry a Leamer reference — either a "
        f"bib key matching @leamer* or the prose token "
        f"{_LEAMER_PROSE_TOKEN!r}. Neither found."
    )


# ── End-to-end lint ───────────────────────────────────────────────────────

def test_nb3_citation_lint_passes_after_task28() -> None:
    """``lint_notebook_citations.py`` exits 0 on the live NB3 path."""
    assert LINT_SCRIPT.is_file(), f"Lint script missing: {LINT_SCRIPT}"
    assert NB3_PATH.is_file(), f"NB3 missing: {NB3_PATH}"
    result = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), str(NB3_PATH)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, (
        f"Expected lint exit 0 on NB3; got {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
