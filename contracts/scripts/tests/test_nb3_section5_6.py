"""Structural regression tests for NB3 §5 (T6 Bai-Perron endogenous break
estimation) and §6 (T7 intervention-dummy adequacy) — Task 26 of the
econ-notebook implementation plan.

§5 asserts data-driven structural-break detection on the primary
Column-6 residual series via ``ruptures`` (first preference) or
``statsmodels.stats.diagnostic.breaks_cusumolsresid`` (fallback), with
a max-breaks prior of 3 (Bai-Perron 1998/2003 upper bound). Estimated
break dates are mapped from residual row indices back to
``panel.weekly['week_start']`` and are compared to NB2's exogenously
pre-committed subsample boundaries 2015-01-05 and 2021-01-04. Breaks
falling within ±4 ISO weeks of either boundary are flagged "ALIGNED";
anything outside is flagged "UNALIGNED" and the section emits the
alignment verdict as a data-supported-or-not check on NB2 §8's
subsample choice.

§6 asserts T7 intervention-dummy adequacy: re-fit Column 6 WITHOUT the
``intervention_dummy`` regressor under the same HAC(4) standard errors;
compare β̂_CPI with vs. without. Stability threshold
|β̂_with − β̂_without| ≤ 1·SE(β̂_with) → PASS (intervention dummy is
not load-bearing for β̂_CPI); exceedance → FAIL (the dummy is
materially affecting the primary coefficient and therefore must stay).

Tests are TDD-first: written to fail against the 15-cell Task-25
baseline and pass after Task 26's 2 trios (= 6 cells) extend NB3 to
21 cells.

What gets asserted, in order of decreasing "load-bearing":

  1. Cell count: 21 after Task 26 (6 new cells beyond Task 25's 15).
  2. §5 exists: at least one ``section:5`` code cell, every code cell
     has ``remove-input``.
  3. §5 source uses ``ruptures.Pelt`` or ``ruptures.Binseg`` or
     ``statsmodels.stats.diagnostic.breaks_cusumolsresid``.
  4. §5 source references BOTH NB2 subsample boundaries
     ``2015-01-05`` and ``2021-01-04`` so the comparison is traceable
     in code.
  5. §5 source binds a ``_break_dates`` list (or equivalent) so the
     test can execute and read out the estimated dates.
  6. §5 source emits an alignment verdict — source contains the
     ``ALIGNED`` or ``UNALIGNED`` tokens so §10's gate writer can
     pick up a structured flag.
  7. §5 citation block references THREE bib keys: ``@chow1960tests``
     (the Chow precedent for exogenous-break F-tests),
     ``@baiPerron1998estimating`` (the multi-break extension), and
     ``@baiPerron2003computation`` (the computational refinement).
  8. §6 exists: at least one ``section:6`` code cell, every code cell
     has ``remove-input``.
  9. §6 source refits Column 6 WITHOUT ``intervention_dummy`` (source
     mentions dropping / excluding / removing the column).
 10. §6 source extracts ``cpi_surprise_ar1`` coefficient from both
     fits and computes the absolute difference against one
     standard error.
 11. §6 emits a PASS/FAIL verdict token in the code source.
 12. §6 citation block references BOTH ``@fuentes2014bis462`` (the
     canonical Banrep FX-intervention evaluation paper) and
     ``@rinconTorres2021interdependence`` (the Colombia
     FX-Treasury transmission paper).
 13. Citation lint clean: ``lint_notebook_citations.py`` exits 0.

What is NOT asserted:
  * Exact estimated break dates (would couple to the residual-snapshot
    numerics and the ruptures penalty/cost choice).
  * Exact β̂_with / β̂_without values.
  * Exact prose wording of the interpretation cells.

No mocks — reads the real NB3 on disk and the real PKL / panel. §5/§6
execute: we want the detected breaks and the refit coefficients to
actually run against the serialised residuals and exog matrix.
"""
from __future__ import annotations

import importlib.util
import math
import pickle
import subprocess
import sys
from pathlib import Path
from typing import Final

import nbformat
import pytest

# ── Path plumbing (mirrors test_nb3_section3_4.py) ────────────────────────

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

SECTION5_TAG: Final[str] = "section:5"
SECTION6_TAG: Final[str] = "section:6"
REMOVE_INPUT_TAG: Final[str] = "remove-input"

REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# §5 landmarks: ruptures primary / statsmodels fallback + NB2 boundaries.
_RUPTURES_PELT_LANDMARK: Final[str] = "ruptures.Pelt"
_RUPTURES_BINSEG_LANDMARK: Final[str] = "ruptures.Binseg"
_STATSMODELS_CUSUMOLS_LANDMARK: Final[str] = "breaks_cusumolsresid"
_NB2_BOUNDARY_1: Final[str] = "2015-01-05"
_NB2_BOUNDARY_2: Final[str] = "2021-01-04"
_BREAK_DATES_VAR: Final[str] = "_break_dates"
_ALIGNMENT_VERDICT_VAR: Final[str] = "_alignment_verdict"

# §5 citation bib keys.
_CHOW1960_KEY: Final[str] = "chow1960tests"
_BAIPERRON1998_KEY: Final[str] = "baiPerron1998estimating"
_BAIPERRON2003_KEY: Final[str] = "baiPerron2003computation"

# §5 alignment tokens (either in source or markdown).
_ALIGNMENT_TOKENS: Final[tuple[str, ...]] = ("ALIGNED", "UNALIGNED")

# §6 landmarks.
_INTERVENTION_COLUMN_LANDMARK: Final[str] = "intervention_dummy"
_CPI_COEFFICIENT_LANDMARK: Final[str] = "cpi_surprise_ar1"
_BETA_WITH_VAR: Final[str] = "_beta_with"
_BETA_WITHOUT_VAR: Final[str] = "_beta_without"
_T7_VERDICT_VAR: Final[str] = "_t7_verdict"
_T7_THRESHOLD_TOKENS: Final[tuple[str, ...]] = ("PASS", "FAIL")

# §6 citation bib keys.
_FUENTES2014_KEY: Final[str] = "fuentes2014bis462"
_RINCON2021_KEY: Final[str] = "rinconTorres2021interdependence"

# Task 26 target: 15 cells (Task 25 baseline) + 6 cells (2 trios) = 21.
_POST_TASK26_CELL_COUNT: Final[int] = 21


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


# ── Shared bootstrap for §5/§6 source execution ───────────────────────────
#
# Both sections depend on §1 having loaded the weekly panel + PKL dict.
# We mimic §1's exported names rather than re-exec cell 4 (spec-hash
# checks, etc.).
def _make_bootstrap() -> str:
    return (
        "import sys\n"
        f"sys.path.insert(0, {str(_CONTRACTS_DIR)!r})\n"
        f"sys.path.insert(0, {str(_ENV_PATH.parent)!r})\n"
        "import duckdb\n"
        "import pickle\n"
        "import env\n"
        "from scripts import cleaning\n"
        "from scripts import panel_fingerprint\n"
        "conn = duckdb.connect(str(env.DUCKDB_PATH), read_only=True)\n"
        "try:\n"
        "    _panel = cleaning.load_cleaned_panel(conn)\n"
        "    panel = _panel\n"
        "    weekly = _panel.weekly\n"
        "finally:\n"
        "    conn.close()\n"
        "with open(env.FULL_PKL_PATH, 'rb') as _fh:\n"
        "    _pkl = pickle.load(_fh)\n"
        "pkl_degraded = False\n"
        "column6_fit = _pkl['column6_fit']\n"
    )


# ── Cell-count gate ───────────────────────────────────────────────────────

def test_nb3_has_task26_cell_count(nb3: nbformat.NotebookNode) -> None:
    """NB3 grows from 15 cells (Task 25) to 21 cells (Task 26 = + 2 trios)."""
    assert len(nb3.cells) >= _POST_TASK26_CELL_COUNT, (
        f"NB3 has {len(nb3.cells)} cells; Task 26 must author 6 new cells "
        f"(2 trios: §5 + §6) for a total of {_POST_TASK26_CELL_COUNT}."
    )


# ── §5 structural tests ───────────────────────────────────────────────────

def test_nb3_section5_has_at_least_one_code_cell(
    nb3: nbformat.NotebookNode,
) -> None:
    """§5 exists: at least one code cell + every code cell has remove-input."""
    s5_code = _code_cells(_section_cells(nb3, SECTION5_TAG))
    assert s5_code, (
        "§5 must contain at least one code cell (tagged section:5); "
        "none found."
    )
    for c in s5_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§5 code cell missing 'remove-input' tag; got tags={tags!r}."
        )


def test_nb3_section5_bai_perron_estimation(
    nb3: nbformat.NotebookNode,
) -> None:
    """§5 source calls ruptures.Pelt, ruptures.Binseg, or the
    statsmodels fallback ``breaks_cusumolsresid``.

    Any one of the three satisfies the plan's "primary ruptures +
    fallback statsmodels" spec (plan line 497).
    """
    combined = _section_source(nb3, SECTION5_TAG)
    hits = [
        landmark
        for landmark in (
            _RUPTURES_PELT_LANDMARK,
            _RUPTURES_BINSEG_LANDMARK,
            _STATSMODELS_CUSUMOLS_LANDMARK,
        )
        if landmark in combined
    ]
    assert hits, (
        f"§5 must call one of {{{_RUPTURES_PELT_LANDMARK!r}, "
        f"{_RUPTURES_BINSEG_LANDMARK!r}, "
        f"{_STATSMODELS_CUSUMOLS_LANDMARK!r}}}. None found in §5 code."
    )


def test_nb3_section5_reports_estimated_break_dates(
    nb3: nbformat.NotebookNode,
) -> None:
    """§5 binds ``_break_dates`` so the reader (and this test) can pull
    the estimated dates out of the namespace.

    The list may be empty (no breaks detected is a valid outcome) or
    contain pandas Timestamps / datetime-like objects mapped from the
    residual-row indices back to ``panel.weekly['week_start']``.
    """
    s5_code_src = _section_source(nb3, SECTION5_TAG)
    assert s5_code_src, "§5 code must exist."

    ns: dict[str, object] = {}
    exec(
        compile(
            _make_bootstrap() + "\n" + s5_code_src, "<nb3-section5>", "exec"
        ),
        ns,
    )
    assert _BREAK_DATES_VAR in ns, (
        f"§5 must bind the estimated break dates to {_BREAK_DATES_VAR!r} "
        f"so downstream readers can iterate them. Found names: "
        f"{sorted(k for k in ns if not k.startswith('__'))!r}"
    )
    break_dates = ns[_BREAK_DATES_VAR]
    # Accept any iterable (list / pandas DatetimeIndex / tuple).
    try:
        break_dates_list = list(break_dates)
    except TypeError as exc:
        pytest.fail(
            f"{_BREAK_DATES_VAR!r} must be iterable; got "
            f"type={type(break_dates).__name__} ({exc})."
        )
    # Every entry, if any, must be convertible to a pandas Timestamp
    # (duck-type check — don't hard-wire the exact Python type).
    import pandas as pd
    for d in break_dates_list:
        try:
            pd.Timestamp(d)
        except (TypeError, ValueError) as exc:
            pytest.fail(
                f"Break-date entry {d!r} is not Timestamp-compatible: {exc}"
            )


def test_nb3_section5_compares_to_nb2_boundaries(
    nb3: nbformat.NotebookNode,
) -> None:
    """§5 source references BOTH NB2 subsample boundaries explicitly."""
    combined = _section_source(nb3, SECTION5_TAG)
    for boundary in (_NB2_BOUNDARY_1, _NB2_BOUNDARY_2):
        assert boundary in combined, (
            f"§5 must reference NB2 subsample boundary {boundary!r} "
            f"so the comparison to endogenous break dates is traceable "
            f"in code. Not found in §5 source."
        )


def test_nb3_section5_flags_unaligned_breaks(
    nb3: nbformat.NotebookNode,
) -> None:
    """§5 emits an ALIGNED / UNALIGNED token so the gate writer can
    pick up a structured alignment flag.

    The token may appear in code (e.g. ``_alignment_verdict = 'ALIGNED'``)
    or in markdown interpretation. Plan line 497: "flags unaligned breaks."
    """
    combined_src = _section_source(nb3, SECTION5_TAG)
    s5_md = _markdown_cells(_section_cells(nb3, SECTION5_TAG))
    combined_md = "\n\n".join(_cell_source(c) for c in s5_md)
    combined = combined_src + "\n\n" + combined_md
    hits = [t for t in _ALIGNMENT_TOKENS if t in combined]
    assert hits, (
        f"§5 must carry an alignment token from {_ALIGNMENT_TOKENS!r} "
        f"(either in code or markdown) so the alignment verdict is "
        f"surfaced to the reader. None found."
    )


def test_nb3_section5_citations_chow_bai_perron(
    nb3: nbformat.NotebookNode,
) -> None:
    """§5 carries a 4-part citation block citing all three canonical keys."""
    s5_md = _markdown_cells(_section_cells(nb3, SECTION5_TAG))
    citation_cells = [
        c
        for c in s5_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§5 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )
    combined = "\n\n".join(_cell_source(c) for c in citation_cells)
    for key in (_CHOW1960_KEY, _BAIPERRON1998_KEY, _BAIPERRON2003_KEY):
        assert key in combined, (
            f"§5 citation block(s) must reference bib key @{key}. Not "
            f"found among §5 citation markdown cells."
        )


# ── §6 structural tests ───────────────────────────────────────────────────

def test_nb3_section6_has_at_least_one_code_cell(
    nb3: nbformat.NotebookNode,
) -> None:
    """§6 exists: at least one code cell + every code cell has remove-input."""
    s6_code = _code_cells(_section_cells(nb3, SECTION6_TAG))
    assert s6_code, (
        "§6 must contain at least one code cell (tagged section:6); "
        "none found."
    )
    for c in s6_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§6 code cell missing 'remove-input' tag; got tags={tags!r}."
        )


def test_nb3_section6_t7_refit_without_intervention(
    nb3: nbformat.NotebookNode,
) -> None:
    """§6 source refits Column 6 without ``intervention_dummy``.

    Source must reference both the dropped column name and a refit /
    removal operation (one of the canonical Python patterns: drop,
    delete, exclude, np.delete, remove, without).
    """
    combined = _section_source(nb3, SECTION6_TAG)
    assert _INTERVENTION_COLUMN_LANDMARK in combined, (
        f"§6 must reference {_INTERVENTION_COLUMN_LANDMARK!r} "
        f"(the column being dropped). Not found in §6 source."
    )
    refit_tokens = ("drop", "np.delete", "delete", "remove", "without", "exclud")
    assert any(t in combined for t in refit_tokens), (
        f"§6 must reference a drop/remove/exclude operation so the "
        f"reader can see the intervention_dummy column is omitted. "
        f"None of {refit_tokens!r} found."
    )


def test_nb3_section6_compares_beta_cpi_with_without(
    nb3: nbformat.NotebookNode,
) -> None:
    """§6 extracts β̂_cpi_surprise_ar1 from both fits and binds the
    with/without pair so the test (and the reader) can compare them."""
    s6_code_src = _section_source(nb3, SECTION6_TAG)
    assert s6_code_src, "§6 code must exist."

    combined = s6_code_src
    assert _CPI_COEFFICIENT_LANDMARK in combined, (
        f"§6 must reference {_CPI_COEFFICIENT_LANDMARK!r} so the "
        f"coefficient being compared is explicit. Not found."
    )

    ns: dict[str, object] = {}
    exec(
        compile(
            _make_bootstrap() + "\n" + s6_code_src, "<nb3-section6>", "exec"
        ),
        ns,
    )
    for name in (_BETA_WITH_VAR, _BETA_WITHOUT_VAR):
        assert name in ns, (
            f"§6 must bind {name!r} to the cpi_surprise_ar1 coefficient. "
            f"Found names: "
            f"{sorted(k for k in ns if not k.startswith('__'))!r}"
        )
        val = ns[name]
        fv = float(val)
        assert math.isfinite(fv), (
            f"{name!r} must be a finite float; got {val!r}."
        )


def test_nb3_section6_stability_threshold_one_se(
    nb3: nbformat.NotebookNode,
) -> None:
    """§6 source must reference an SE threshold (1·SE, one standard
    error, 1 SE, etc.) for the stability check."""
    combined = _section_source(nb3, SECTION6_TAG)
    # Accept a broad set of canonical phrasings for "one SE".
    se_tokens = (
        "1 * se",
        "1*se",
        "1 SE",
        "one standard error",
        "one-standard-error",
        "1-SE",
        "one SE",
        "± 1 SE",
        "±1 SE",
        "SE_with",
        "se_with",
        "bse",
    )
    hits = [t for t in se_tokens if t in combined]
    assert hits, (
        f"§6 must reference the 1-SE stability threshold. None of "
        f"{se_tokens!r} found in §6 source."
    )


def test_nb3_section6_pass_fail_verdict(
    nb3: nbformat.NotebookNode,
) -> None:
    """§6 emits a PASS or FAIL verdict token for intervention-dummy
    adequacy. Must appear in the code source so the gate writer can
    pick up a structured flag."""
    combined = _section_source(nb3, SECTION6_TAG)
    hits = [t for t in _T7_THRESHOLD_TOKENS if t in combined]
    assert hits, (
        f"§6 must emit one of {_T7_THRESHOLD_TOKENS!r} as the T7 "
        f"adequacy verdict. None found in §6 source."
    )
    # Also bind the verdict variable.
    s6_code_src = _section_source(nb3, SECTION6_TAG)
    ns: dict[str, object] = {}
    exec(
        compile(
            _make_bootstrap() + "\n" + s6_code_src, "<nb3-section6-verdict>",
            "exec",
        ),
        ns,
    )
    assert _T7_VERDICT_VAR in ns, (
        f"§6 must bind {_T7_VERDICT_VAR!r} to 'PASS' or 'FAIL' for the "
        f"T7 adequacy verdict. Found names: "
        f"{sorted(k for k in ns if not k.startswith('__'))!r}"
    )
    v = ns[_T7_VERDICT_VAR]
    assert v in ("PASS", "FAIL"), (
        f"{_T7_VERDICT_VAR!r} must be 'PASS' or 'FAIL'; got {v!r}."
    )


def test_nb3_section6_citations_fuentes_rincon(
    nb3: nbformat.NotebookNode,
) -> None:
    """§6 carries a 4-part citation block citing BOTH canonical keys."""
    s6_md = _markdown_cells(_section_cells(nb3, SECTION6_TAG))
    citation_cells = [
        c
        for c in s6_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§6 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )
    combined = "\n\n".join(_cell_source(c) for c in citation_cells)
    for key in (_FUENTES2014_KEY, _RINCON2021_KEY):
        assert key in combined, (
            f"§6 citation block(s) must reference bib key @{key}. Not "
            f"found among §6 citation markdown cells."
        )


# ── Handoff-artifact sanity ───────────────────────────────────────────────

def test_full_pkl_has_column6_fit_with_intervention_dummy() -> None:
    """Pre-flight: PKL column6_fit has intervention_dummy in its exog."""
    assert FULL_PKL_PATH.is_file(), f"FULL_PKL missing: {FULL_PKL_PATH}"
    with open(FULL_PKL_PATH, "rb") as fh:
        pkl = pickle.load(fh)
    fit = pkl["column6_fit"]
    exog_names = list(fit.model.exog_names)
    assert "intervention_dummy" in exog_names, (
        f"column6_fit.model.exog_names must include 'intervention_dummy' "
        f"for T7 refit to be meaningful; got {exog_names!r}."
    )
    assert "cpi_surprise_ar1" in exog_names, (
        f"column6_fit.model.exog_names must include 'cpi_surprise_ar1' "
        f"(the primary coefficient); got {exog_names!r}."
    )


# ── End-to-end lint ───────────────────────────────────────────────────────

def test_nb3_citation_lint_passes_after_task26() -> None:
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
