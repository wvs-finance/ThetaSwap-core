"""Structural regression tests for NB2 §4 (OLS diagnostics) and §5 (Student-t likelihood alternative).

Task 18 of the econ-notebook-implementation plan. NB2 §4 runs four OLS
diagnostic tests on the Column 6 residuals (``column6_fit.resid``) —
Jarque-Bera 1987 for residual normality, Breusch-Pagan 1979 for
heteroskedasticity, Durbin-Watson 1951 for first-order serial
correlation, and Ljung-Box 1978 Q-statistics at lags 1 through 8 for
higher-order serial correlation — and renders a single summary table
carrying the test statistic and p-value per test, **without** any
``if`` branching on the diagnostic p-values (no auto-commentary
pass/fail verdict per test; the interpretation belongs to the
follow-up markdown cell, not the code cell).

NB2 §5 fits a Student-t likelihood alternative using
``statsmodels.miscmodels.tmodel.TLinearModel`` (locked API per plan
Rev 2) on the **same** (y, X) design matrix Column 6 uses, reporting
the estimated ν̂ degrees of freedom and a side-by-side coefficient
table comparing Gaussian OLS vs Student-t fit for the six RHS
regressors. The refit runs **regardless** of §4 outcomes — it is a
principled robustness companion, not a pass/fail-gated substitute.

This module is authored TDD-first: it fails against the 18-cell
post-Task-17 NB2 and turns green once the Analytics Reporter appends
§4 and §5 trios.

What gets asserted:

  1. §4 runs all four diagnostic tests: Jarque-Bera + Breusch-Pagan +
     Durbin-Watson + Ljung-Box Q(1..8). Source-level token search.
  2. §4 renders a summary table (DataFrame) with columns including
     test name, statistic, and p-value (or equivalent).
  3. §4 contains NO ``if`` branching on p-values — no auto-commentary
     of the form ``if p < 0.05: print('fail')``. Diagnostic reading
     lives in the interpretation markdown cell, not the code cell.
  4. §5 imports and uses ``TLinearModel``.
  5. §5 reports the estimated ν̂ (degrees of freedom).
  6. §5 renders a side-by-side coefficient table (Gaussian vs
     Student-t) covering the six RHS regressors.
  7. §5 Student-t refit is unconditional (no ``if`` gate on §4
     outcomes).
  8. §4 citation block references Jarque-Bera 1987 + Breusch-Pagan
     1979 + Durbin-Watson 1951 + Ljung-Box 1978.
  9. §5 citation block references Campbell-Lo-MacKinlay 1997.
 10. Structural tags: every §4/§5 code cell carries ``remove-input``
     and the appropriate ``section:4`` / ``section:5`` tag.
 11. Citation lint: ``scripts/lint_notebook_citations.py`` exits 0.

What is NOT asserted:
  * Exact wording of prose interpretations (would couple to authoring).
  * Exact diagnostic p-values or ν̂ (these are OUTPUTS, reported in
    the task's final message, not the test file).
  * Exact rendering mechanism (pandas DataFrame vs summary_col vs
    manual print — any structure hitting the column tokens passes).
"""
from __future__ import annotations

import importlib.util
import re
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

SECTION4_TAG: Final[str] = "section:4"
SECTION5_TAG: Final[str] = "section:5"
REMOVE_INPUT_TAG: Final[str] = "remove-input"

REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# §4 diagnostic landmarks — statsmodels function names / test names.
# Jarque-Bera: either ``jarque_bera`` (statsmodels.stats.stattools) or
# ``jb_test`` helper pattern passes.
# Breusch-Pagan: ``het_breuschpagan`` (statsmodels.stats.diagnostic).
# Durbin-Watson: ``durbin_watson`` (statsmodels.stats.stattools).
# Ljung-Box: ``acorr_ljungbox`` (statsmodels.stats.diagnostic) with
#   ``lags=8`` or an equivalent iteration-over-range(1, 9) shape.
_JARQUE_BERA_ALIASES: Final[tuple[str, ...]] = (
    "jarque_bera",
    "jb_test",
)
_BREUSCH_PAGAN_ALIASES: Final[tuple[str, ...]] = (
    "het_breuschpagan",
    "breusch_pagan",
)
_DURBIN_WATSON_ALIASES: Final[tuple[str, ...]] = (
    "durbin_watson",
)
_LJUNG_BOX_ALIASES: Final[tuple[str, ...]] = (
    "acorr_ljungbox",
    "ljung_box",
)

# Ljung-Box Q(1..8) requires lags=8 in some form.
_LJUNG_BOX_LAGS_PATTERNS: Final[tuple[str, ...]] = (
    "lags=8",
    "lags=list(range(1, 9))",
    "lags=range(1, 9)",
    "lags=[1, 2, 3, 4, 5, 6, 7, 8]",
)

# Column 6 residuals access — the diagnostic tests must consume
# ``column6_fit.resid`` (or an alias bound to it) so the diagnostic
# output refers to the Column 6 OLS fit and not some other model.
_COLUMN6_RESID_LANDMARKS: Final[tuple[str, ...]] = (
    "column6_fit.resid",
    "column6_fit",
)

# §5 TLinearModel landmark — locked API per plan Rev 2.
_TLINEARMODEL_IMPORT_LANDMARKS: Final[tuple[str, ...]] = (
    "TLinearModel",
    "statsmodels.miscmodels.tmodel",
)

# §5 degrees-of-freedom symbol — source must reference ν̂ or ``nu`` or
# ``df`` assignment pattern to report the estimated t-distribution
# degrees of freedom. Accept any of the three naming conventions.
_NU_HAT_ALIASES: Final[tuple[str, ...]] = (
    "nu_hat",
    "nu =",
    "df =",
    "ν̂",
    "nu_est",
)

# Citation bibkeys.
_SECTION4_BIBKEYS: Final[tuple[str, ...]] = (
    "jarqueBera1987normality",
    "breuschPagan1979heteroscedasticity",
    "durbinWatson1951serial",
    "ljungBox1978measure",
)

_SECTION5_BIBKEYS: Final[tuple[str, ...]] = (
    "campbell1997econometrics",
)

# After Task 17 NB2 has 18 cells. Task 18 §4 + §5 each append a minimum
# of one (why-md, code, interp-md) trio → ≥6 new cells. Floor of 24.
_MIN_POST_TASK18_CELL_COUNT: Final[int] = 24

# §4 auto-branching guard — the §4 code cell must NOT contain an ``if``
# statement that branches on a p-value variable (auto-commentary
# pass/fail per diagnostic is explicitly forbidden by Task 18 spec).
# Pattern: ``if p`` followed by comparison operator against numeric
# threshold. Match at line-start (possibly indented).
_IF_PVALUE_BRANCH_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\s*if\s+p.*[<>=]",
    re.MULTILINE,
)

# §5 unconditional-refit guard — the §5 code cell must NOT contain an
# ``if`` gate referring to §4 diagnostic outcomes (e.g. ``if jb_p <
# 0.05``). This catches the temptation to gate the Student-t refit on
# normality rejection, which Task 18 explicitly forbids.
_IF_SECTION4_GATE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\s*if\s+(jb|bp|breusch|jarque|dw|durbin|lb|ljung).*[<>=]",
    re.MULTILINE | re.IGNORECASE,
)


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


# ── NB2 size / tag floor tests ────────────────────────────────────────────

def test_nb2_has_at_least_24_cells_post_task18(
    nb2: nbformat.NotebookNode,
) -> None:
    """NB2 has the post-Task-18 cell count floor."""
    assert len(nb2.cells) >= _MIN_POST_TASK18_CELL_COUNT, (
        f"NB2 has only {len(nb2.cells)} cells; Task 18 must add at "
        f"least {_MIN_POST_TASK18_CELL_COUNT - 18} new cells beyond "
        f"the 18-cell post-Task-17 state."
    )


def test_nb2_section4_has_code_cells(
    nb2: nbformat.NotebookNode,
) -> None:
    """§4 exists: at least one code cell tagged section:4 + remove-input."""
    s4_cells = _section_cells(nb2, SECTION4_TAG)
    s4_code = _code_cells(s4_cells)
    assert s4_code, (
        "§4 must contain at least one code cell (tagged section:4). "
        "Task 18 Step 3 must author §4."
    )
    for c in s4_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§4 code cell missing 'remove-input' tag; got {tags!r}."
        )


def test_nb2_section5_has_code_cells(
    nb2: nbformat.NotebookNode,
) -> None:
    """§5 exists: at least one code cell tagged section:5 + remove-input."""
    s5_cells = _section_cells(nb2, SECTION5_TAG)
    s5_code = _code_cells(s5_cells)
    assert s5_code, (
        "§5 must contain at least one code cell (tagged section:5). "
        "Task 18 Step 3 must author §5."
    )
    for c in s5_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§5 code cell missing 'remove-input' tag; got {tags!r}."
        )


# ── §4 diagnostic tests ───────────────────────────────────────────────────

def test_nb2_section4_has_jarque_bera(
    nb2: nbformat.NotebookNode,
) -> None:
    """§4 runs the Jarque-Bera normality test."""
    s4_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION4_TAG))
    )
    assert any(a in s4_code_src for a in _JARQUE_BERA_ALIASES), (
        f"§4 source must invoke the Jarque-Bera test (any of "
        f"{_JARQUE_BERA_ALIASES!r}). Plan Task 18 mandates residual "
        f"normality diagnostic."
    )


def test_nb2_section4_has_breusch_pagan(
    nb2: nbformat.NotebookNode,
) -> None:
    """§4 runs the Breusch-Pagan heteroskedasticity test."""
    s4_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION4_TAG))
    )
    assert any(a in s4_code_src for a in _BREUSCH_PAGAN_ALIASES), (
        f"§4 source must invoke the Breusch-Pagan test (any of "
        f"{_BREUSCH_PAGAN_ALIASES!r}). Plan Task 18 mandates "
        f"heteroskedasticity diagnostic."
    )


def test_nb2_section4_has_durbin_watson(
    nb2: nbformat.NotebookNode,
) -> None:
    """§4 runs the Durbin-Watson first-order serial correlation test."""
    s4_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION4_TAG))
    )
    assert any(a in s4_code_src for a in _DURBIN_WATSON_ALIASES), (
        f"§4 source must invoke the Durbin-Watson test (any of "
        f"{_DURBIN_WATSON_ALIASES!r}). Plan Task 18 mandates "
        f"first-order serial correlation diagnostic."
    )


def test_nb2_section4_has_ljung_box_Q1_to_Q8(
    nb2: nbformat.NotebookNode,
) -> None:
    """§4 runs the Ljung-Box Q test at lags 1 through 8."""
    s4_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION4_TAG))
    )
    assert any(a in s4_code_src for a in _LJUNG_BOX_ALIASES), (
        f"§4 source must invoke the Ljung-Box test (any of "
        f"{_LJUNG_BOX_ALIASES!r}). Plan Task 18 mandates Q(1..8) "
        f"serial correlation diagnostic."
    )
    assert any(p in s4_code_src for p in _LJUNG_BOX_LAGS_PATTERNS), (
        f"§4 source must pass lags=8 (or equivalent range(1,9)) to "
        f"acorr_ljungbox (any of {_LJUNG_BOX_LAGS_PATTERNS!r}). Plan "
        f"Task 18 mandates Q-statistics at lags 1 through 8."
    )


def test_nb2_section4_uses_column6_fit_residuals(
    nb2: nbformat.NotebookNode,
) -> None:
    """§4 diagnostics consume Column 6 residuals.

    The diagnostic source must reference ``column6_fit.resid`` (or
    bind an alias to it) so the tests interrogate the pre-registered
    primary fit from §3 and not some other model.
    """
    s4_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION4_TAG))
    )
    assert any(lm in s4_code_src for lm in _COLUMN6_RESID_LANDMARKS), (
        f"§4 diagnostics must consume ``column6_fit.resid`` (or a "
        f"binding derived from ``column6_fit``). Plan Task 18 mandates "
        f"the Column 6 residuals as the diagnostic subject."
    )


def test_nb2_section4_renders_summary_table(
    nb2: nbformat.NotebookNode,
) -> None:
    """§4 emits a summary table (DataFrame) with statistic + p-value columns.

    Accept any DataFrame-shaped rendering that carries both "statistic"
    and "p_value" (or "p-value" or "pvalue") as column markers. The
    table groups the four diagnostics into one cohesive output.
    """
    s4_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION4_TAG))
    )
    has_dataframe = (
        "DataFrame" in s4_code_src
        or "pd.DataFrame" in s4_code_src
    )
    assert has_dataframe, (
        "§4 source must construct a pandas DataFrame as the summary "
        "table (one row per diagnostic, columns statistic + p-value)."
    )
    has_statistic_col = (
        "statistic" in s4_code_src
        or '"stat"' in s4_code_src
        or "'stat'" in s4_code_src
    )
    assert has_statistic_col, (
        "§4 summary table must carry a 'statistic' column."
    )
    has_pvalue_col = (
        "p_value" in s4_code_src
        or "p-value" in s4_code_src
        or "pvalue" in s4_code_src
        or '"p"' in s4_code_src
        or "'p'" in s4_code_src
    )
    assert has_pvalue_col, (
        "§4 summary table must carry a 'p_value' column "
        "(or equivalent 'pvalue'/'p-value' naming)."
    )


def test_nb2_section4_no_auto_branching_on_pvalues(
    nb2: nbformat.NotebookNode,
) -> None:
    """§4 code must NOT auto-branch on diagnostic p-values.

    Plan Task 18: "rendered in a summary table, no auto-branching."
    Interpretation of pass/fail belongs to the markdown cell, not
    the code cell. Reject any ``if p... <`` / ``if p... >`` /
    ``if p... ==`` pattern at line start.
    """
    s4_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION4_TAG))
    )
    matches = _IF_PVALUE_BRANCH_PATTERN.findall(s4_code_src)
    assert not matches, (
        f"§4 code cell must not branch on p-values (found "
        f"{matches!r}). Plan Task 18: 'rendered in a summary table, "
        f"no auto-branching'."
    )


# ── §5 Student-t tests ────────────────────────────────────────────────────

def test_nb2_section5_uses_tlinear_model(
    nb2: nbformat.NotebookNode,
) -> None:
    """§5 imports and uses ``TLinearModel``.

    Plan Rev 2 locks the API: ``statsmodels.miscmodels.tmodel
    .TLinearModel``. Both tokens must appear in the §5 source.
    """
    s5_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION5_TAG))
    )
    for landmark in _TLINEARMODEL_IMPORT_LANDMARKS:
        assert landmark in s5_code_src, (
            f"§5 source must reference {landmark!r}. Plan Rev 2 locks "
            f"the Student-t likelihood API."
        )


def test_nb2_section5_reports_nu_hat(
    nb2: nbformat.NotebookNode,
) -> None:
    """§5 reports the estimated ν̂ (degrees of freedom)."""
    s5_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION5_TAG))
    )
    assert any(a in s5_code_src for a in _NU_HAT_ALIASES), (
        f"§5 source must assign and report the estimated ν̂ (any of "
        f"{_NU_HAT_ALIASES!r}). Plan Task 18 mandates reporting the "
        f"Student-t degrees of freedom."
    )


def test_nb2_section5_side_by_side_coefficient_table(
    nb2: nbformat.NotebookNode,
) -> None:
    """§5 renders a side-by-side Gaussian-vs-Student-t coefficient table.

    The table must carry all six RHS regressor names (same ladder as
    Column 6) and reference both fits. Accept DataFrame construction
    with both regressor references.
    """
    s5_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION5_TAG))
    )
    has_dataframe = (
        "DataFrame" in s5_code_src
        or "pd.DataFrame" in s5_code_src
    )
    assert has_dataframe, (
        "§5 source must construct a pandas DataFrame as the "
        "side-by-side coefficient table."
    )
    # All six Column-6 regressors must appear.
    for regressor in (
        "cpi_surprise_ar1",
        "us_cpi_surprise",
        "banrep_rate_surprise",
        "vix_avg",
        "intervention_dummy",
        "oil_return",
    ):
        assert regressor in s5_code_src, (
            f"§5 coefficient table must include regressor "
            f"{regressor!r}. Plan Task 18 mandates side-by-side "
            f"comparison for the six Column-6 regressors."
        )
    # Both fit objects referenced — column6_fit (Gaussian) + the
    # Student-t fit. Accept any common naming for the t-fit.
    has_gaussian_ref = "column6_fit" in s5_code_src
    assert has_gaussian_ref, (
        "§5 table must reference the Gaussian OLS fit "
        "``column6_fit`` for side-by-side comparison."
    )


def test_nb2_section5_runs_regardless_of_section4(
    nb2: nbformat.NotebookNode,
) -> None:
    """§5 Student-t refit runs unconditionally.

    Plan Task 18: 'the refit runs regardless of §4 outcomes'. The §5
    code must NOT contain an ``if`` gate referring to §4 diagnostic
    variable names (jb, bp, dw, lb, jarque, breusch, durbin, ljung).
    """
    s5_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION5_TAG))
    )
    matches = _IF_SECTION4_GATE_PATTERN.findall(s5_code_src)
    assert not matches, (
        f"§5 code must not gate the Student-t refit on §4 diagnostic "
        f"outcomes (found conditional branches: {matches!r}). Plan "
        f"Task 18: 'the refit runs regardless of §4 outcomes'."
    )


# ── Citation block tests ──────────────────────────────────────────────────

def test_nb2_section4_has_four_part_citation_block(
    nb2: nbformat.NotebookNode,
) -> None:
    """§4 carries at least one 4-part citation block markdown cell."""
    s4_md = _markdown_cells(_section_cells(nb2, SECTION4_TAG))
    citation_cells = [
        c
        for c in s4_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§4 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )


def test_nb2_section4_citation_references_all_four_diagnostics(
    nb2: nbformat.NotebookNode,
) -> None:
    """§4 citation block cites Jarque-Bera + Breusch-Pagan + Durbin-Watson + Ljung-Box."""
    s4_md_src = "\n\n".join(
        _cell_source(c) for c in _markdown_cells(_section_cells(nb2, SECTION4_TAG))
    )
    for bibkey in _SECTION4_BIBKEYS:
        assert bibkey in s4_md_src, (
            f"§4 citation block must reference bibkey {bibkey!r}. Plan "
            f"Task 18 mandates citations for all four diagnostic tests."
        )


def test_nb2_section5_has_four_part_citation_block(
    nb2: nbformat.NotebookNode,
) -> None:
    """§5 carries a 4-part citation block."""
    s5_md = _markdown_cells(_section_cells(nb2, SECTION5_TAG))
    citation_cells = [
        c
        for c in s5_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§5 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )


def test_nb2_section5_citation_references_campbell_lo_mackinlay(
    nb2: nbformat.NotebookNode,
) -> None:
    """§5 citation block cites Campbell-Lo-MacKinlay 1997."""
    s5_md_src = "\n\n".join(
        _cell_source(c)
        for c in _markdown_cells(_section_cells(nb2, SECTION5_TAG))
    )
    for bibkey in _SECTION5_BIBKEYS:
        assert bibkey in s5_md_src, (
            f"§5 citation block must reference bibkey {bibkey!r}. "
            f"Plan Task 18 mandates Campbell-Lo-MacKinlay 1997 for "
            f"fat-tailed financial residuals."
        )


# ── Citation lint passthrough ─────────────────────────────────────────────

def test_nb2_citation_lint_passes_after_task18() -> None:
    """``lint_notebook_citations.py`` exits 0 on NB2 after §4/§5 authoring."""
    assert LINT_SCRIPT.is_file(), f"Lint script missing: {LINT_SCRIPT}"
    assert NB2_PATH.is_file(), f"NB2 missing: {NB2_PATH}"
    result = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), str(NB2_PATH)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, (
        f"Expected lint exit 0 on NB2 post-Task-18; got "
        f"{result.returncode}.\nstdout:\n{result.stdout}\nstderr:\n"
        f"{result.stderr}"
    )
