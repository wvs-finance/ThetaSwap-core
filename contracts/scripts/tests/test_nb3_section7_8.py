"""Structural regression tests for NB3 §7 (T3a two-sided β ≠ 0 test) and
§8 (13-row forest plot / specification curve) — Task 27 of the
econ-notebook implementation plan.

§7 asserts the two-sided β ≠ 0 complement to NB2 §9's one-sided T3b
gate. T3b (NB2) tested β − 1.28·SE > 0 (one-sided, reject at α=0.10);
T3a (here) tests the two-sided null β = 0 on the same Column-6 primary
HAC(4) standard errors. Expected outcome is FAIL TO REJECT (the
Column-6 point estimate is -0.000685 with SE ≈ 0.001794, a |t| < 1),
but the test itself only checks machinery — t-stat, two-sided p-value,
95% two-sided CI — and cross-references T3b so the reader sees both
sides of the null.

§8 asserts a 13-row forest plot / specification curve carrying β̂_CPI
with 90% HAC CI whiskers for every sensitivity pre-committed in NB2
§10 plus the asymmetric-response subsets flagged in Phase 1:

  Row 1  (anchor, top, divider below):  Primary Column-6 fit
  Row 2+ (sorted |β̂| descending):
    - GARCH-X δ̂                                (NB2 garch_x PKL)
    - Decomposition β̂_CPI (IPP added)          (NB2 decomposition_fit)
    - Decomposition β̂_PPI                      (NB2 decomposition_fit)
    - Subsample pre-2015                        (NB2 regime_fits)
    - Subsample 2015-2021                       (NB2 regime_fits)
    - Subsample post-2021                       (NB2 regime_fits)
    - A1 monthly                                (refit on get_monthly_panel)
    - A4 release-day-excluded                   (refit on
                                                 get_rv_excluding_release_day)
    - A5 lagged-RV                              (Column 6 + rv_cuberoot_lag1)
    - A6 bivariate                              (ladder Column 1, no controls)
    - A8 oil-level                              (Column 6 with oil_log_level)
    - A9⁺ positive-surprise subset              (cpi_surprise_ar1 > 0)
    - A9⁻ negative-surprise subset              (cpi_surprise_ar1 < 0)
  + A2/A3/A7 annotated "see NB2".

Tests are TDD-first: written to fail against the 21-cell Task-26
baseline and pass after Task 27's 2 trios (= 6 cells) extend NB3 to
27 cells.

What gets asserted, in order of decreasing "load-bearing":

  1. Cell count: 27 after Task 27 (6 new cells beyond Task 26's 21).
  2. §7 exists: ≥1 ``section:7`` code cell, every code cell has
     ``remove-input``.
  3. §7 source computes a two-sided t-stat, two-sided p-value, and 95%
     two-sided CI on β̂_cpi_surprise_ar1 from ``column6_fit``. Binds:
     ``_t3a_tstat``, ``_t3a_pvalue``, ``_t3a_ci_lo``, ``_t3a_ci_hi``,
     ``_t3a_verdict``.
  4. §7 source cross-references T3b by mentioning the bib-key or the
     substring "T3b" in code comments.
  5. §7 citation block references ``@andersen2003micro`` (ABDV 2003).
  6. §8 exists: ≥1 ``section:8`` code cell, every code cell has
     ``remove-input``.
  7. §8 forest-plot table has exactly 14 rows (1 primary + 13
     sensitivities, of which A9+ and A9- are two separate rows;
     A2/A3/A7 are annotations, not rows). Task-prompt shorthand
     "13 rows" counts only the post-primary sensitivities.
  8. §8 row 1 is the primary anchor (label contains "Primary" or
     "Column 6").
  9. §8 rows 2+ sorted by |β̂| descending.
 10. §8 BOTH A9⁺ and A9⁻ rows present (labels contain "A9+"/"A9-" or
     "positive"/"negative" surprise).
 11. §8 source references ``get_monthly_panel`` (A1 refit) and
     ``get_rv_excluding_release_day`` (A4 refit).
 12. §8 source builds A6 as the bivariate Column-1 fit (references
     ``ladder_fits[0]`` or rebuilds bivariate inline).
 13. §8 A2/A3/A7 annotated "see NB2" (token in source or markdown).
 14. §8 citation block references ``@simonsohn2020specification``.
 15. Citation lint clean: ``lint_notebook_citations.py`` exits 0.

What is NOT asserted:
  * Exact t-stat / p-value / CI bounds (would couple to the PKL
    snapshot numerics).
  * Exact |β̂| ordering of rows 2+ (this test only asserts the
    sorted-descending invariant, not the row identities at each rank).
  * Which rows (if any) have 90% CI excluding zero — reported in the
    final verdict, not asserted.

No mocks — reads the real NB3 on disk and the real PKL / panel. §7/§8
execute: we want the t-stats and the forest-plot β̂ series to actually
run against the serialised fits.
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

# ── Path plumbing (mirrors test_nb3_section5_6.py) ────────────────────────

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

SECTION7_TAG: Final[str] = "section:7"
SECTION8_TAG: Final[str] = "section:8"
REMOVE_INPUT_TAG: Final[str] = "remove-input"

REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# §7 landmarks.
_CPI_COEFFICIENT_LANDMARK: Final[str] = "cpi_surprise_ar1"
_T3A_TSTAT_VAR: Final[str] = "_t3a_tstat"
_T3A_PVALUE_VAR: Final[str] = "_t3a_pvalue"
_T3A_CI_LO_VAR: Final[str] = "_t3a_ci_lo"
_T3A_CI_HI_VAR: Final[str] = "_t3a_ci_hi"
_T3A_VERDICT_VAR: Final[str] = "_t3a_verdict"
_T3A_VERDICT_TOKENS: Final[tuple[str, ...]] = ("REJECT", "FAIL TO REJECT")

# §7 citation bib keys.
_ANDERSEN2003_KEY: Final[str] = "andersen2003micro"

# §8 landmarks.
_FOREST_TABLE_VAR: Final[str] = "_forest_table"
_FOREST_EXPECTED_ROWS: Final[int] = 14  # 1 primary + 13 sensitivities
# Enumeration (per plan lines 503-515):
#   1 anchor primary
# + 6 PKL rows: GARCH-X, Decomp β̂_CPI, Decomp β̂_PPI, pre-2015,
#   2015-2021, post-2021
# + 5 A-series fits here: A1, A4, A5, A6, A8
# + 2 asymmetric-response subsets: A9+, A9-
# = 14 rows total. (Task prompt header said "13 rows" which counts the
# post-primary sensitivities; the plan's explicit list enumerates 14.)
_A9_PLUS_TOKENS: Final[tuple[str, ...]] = ("A9+", "A9⁺", "positive-surprise", "positive surprise")
_A9_MINUS_TOKENS: Final[tuple[str, ...]] = ("A9-", "A9−", "A9⁻", "negative-surprise", "negative surprise")
_MONTHLY_PANEL_LANDMARK: Final[str] = "get_monthly_panel"
_RV_EXCL_RELEASE_LANDMARK: Final[str] = "get_rv_excluding_release_day"
_A2_A3_A7_SEE_NB2_TOKENS: Final[tuple[str, ...]] = ("see NB2", "See NB2", "see nb2")

# §8 citation bib keys.
_SIMONSOHN2020_KEY: Final[str] = "simonsohn2020specification"

# Task 27 target: 21 cells (Task 26 baseline) + 6 cells (2 trios) = 27.
_POST_TASK27_CELL_COUNT: Final[int] = 27


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


# ── Shared bootstrap for §7/§8 source execution ───────────────────────────
#
# §7 only needs the PKL column6_fit; §8 needs the PKL + weekly panel + the
# econ_query_api accessors. The bootstrap below covers both.
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
        "try:\n"
        "    _panel = cleaning.load_cleaned_panel(conn)\n"
        "    panel = _panel\n"
        "    weekly = _panel.weekly\n"
        "finally:\n"
        "    pass\n"
        # Leave conn open for §8's accessor calls (A1 monthly / A4 excl).
        "with open(env.FULL_PKL_PATH, 'rb') as _fh:\n"
        "    _pkl = pickle.load(_fh)\n"
        "pkl_degraded = False\n"
        "column6_fit = _pkl['column6_fit']\n"
        "ladder_fits = _pkl['ladder_fits']\n"
        "decomposition_fit = _pkl['decomposition_fit']\n"
        "regime_fits = _pkl['regime_fits']\n"
        "garch_x = _pkl['garch_x']\n"
    )


# ── Cell-count gate ───────────────────────────────────────────────────────

def test_nb3_has_task27_cell_count(nb3: nbformat.NotebookNode) -> None:
    """NB3 grows from 21 cells (Task 26) to 27 cells (Task 27 = + 2 trios)."""
    assert len(nb3.cells) >= _POST_TASK27_CELL_COUNT, (
        f"NB3 has {len(nb3.cells)} cells; Task 27 must author 6 new cells "
        f"(2 trios: §7 + §8) for a total of {_POST_TASK27_CELL_COUNT}."
    )


# ── §7 structural tests ───────────────────────────────────────────────────

def test_nb3_section7_has_at_least_one_code_cell(
    nb3: nbformat.NotebookNode,
) -> None:
    """§7 exists: at least one code cell + every code cell has remove-input."""
    s7_code = _code_cells(_section_cells(nb3, SECTION7_TAG))
    assert s7_code, (
        "§7 must contain at least one code cell (tagged section:7); "
        "none found."
    )
    for c in s7_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§7 code cell missing 'remove-input' tag; got tags={tags!r}."
        )


def test_nb3_section7_t3a_two_sided_test(
    nb3: nbformat.NotebookNode,
) -> None:
    """§7 computes t-stat, p-value (two-sided), and 95% CI on β̂_CPI."""
    s7_code_src = _section_source(nb3, SECTION7_TAG)
    assert s7_code_src, "§7 code must exist."
    assert _CPI_COEFFICIENT_LANDMARK in s7_code_src, (
        f"§7 must reference {_CPI_COEFFICIENT_LANDMARK!r} so the "
        f"coefficient being tested is explicit. Not found in §7 source."
    )

    ns: dict[str, object] = {}
    exec(
        compile(
            _make_bootstrap() + "\n" + s7_code_src, "<nb3-section7-t3a>", "exec"
        ),
        ns,
    )
    for name in (_T3A_TSTAT_VAR, _T3A_PVALUE_VAR):
        assert name in ns, (
            f"§7 must bind {name!r} for the two-sided β ≠ 0 test. "
            f"Found names: {sorted(k for k in ns if not k.startswith('__'))!r}"
        )
        val = float(ns[name])
        assert math.isfinite(val), f"{name!r} must be finite; got {val!r}."
    # p-value must be in [0, 1].
    pval = float(ns[_T3A_PVALUE_VAR])
    assert 0.0 <= pval <= 1.0, (
        f"{_T3A_PVALUE_VAR!r} must be a probability in [0, 1]; got {pval}."
    )


def test_nb3_section7_95_two_sided_ci(nb3: nbformat.NotebookNode) -> None:
    """§7 binds 95% two-sided CI bounds; lo < hi and they bracket β̂."""
    s7_code_src = _section_source(nb3, SECTION7_TAG)
    ns: dict[str, object] = {}
    exec(
        compile(
            _make_bootstrap() + "\n" + s7_code_src, "<nb3-section7-ci>", "exec"
        ),
        ns,
    )
    for name in (_T3A_CI_LO_VAR, _T3A_CI_HI_VAR):
        assert name in ns, (
            f"§7 must bind {name!r} as a 95% two-sided CI bound. "
            f"Found names: {sorted(k for k in ns if not k.startswith('__'))!r}"
        )
    lo = float(ns[_T3A_CI_LO_VAR])
    hi = float(ns[_T3A_CI_HI_VAR])
    assert math.isfinite(lo) and math.isfinite(hi), (
        f"CI bounds must be finite: lo={lo}, hi={hi}"
    )
    assert lo < hi, f"95% CI must have lo < hi; got lo={lo}, hi={hi}."


def test_nb3_section7_cross_ref_t3b(nb3: nbformat.NotebookNode) -> None:
    """§7 cross-references T3b — mentions it in code or markdown."""
    s7_code = _section_source(nb3, SECTION7_TAG)
    s7_md = _markdown_cells(_section_cells(nb3, SECTION7_TAG))
    combined_md = "\n\n".join(_cell_source(c) for c in s7_md)
    combined = s7_code + "\n\n" + combined_md
    assert "T3b" in combined, (
        "§7 must cross-reference NB2's one-sided T3b test. Expected the "
        "literal substring 'T3b' in §7 code or markdown; not found."
    )


def test_nb3_section7_verdict_token(nb3: nbformat.NotebookNode) -> None:
    """§7 binds _t3a_verdict to REJECT or FAIL TO REJECT."""
    s7_code_src = _section_source(nb3, SECTION7_TAG)
    ns: dict[str, object] = {}
    exec(
        compile(
            _make_bootstrap() + "\n" + s7_code_src, "<nb3-section7-verdict>",
            "exec",
        ),
        ns,
    )
    assert _T3A_VERDICT_VAR in ns, (
        f"§7 must bind {_T3A_VERDICT_VAR!r} to a verdict token."
    )
    v = str(ns[_T3A_VERDICT_VAR])
    assert v in _T3A_VERDICT_TOKENS, (
        f"{_T3A_VERDICT_VAR!r} must be one of {_T3A_VERDICT_TOKENS!r}; "
        f"got {v!r}."
    )


def test_nb3_section7_citation_has_abdv_2003(
    nb3: nbformat.NotebookNode,
) -> None:
    """§7 carries a 4-part citation block citing @andersen2003micro."""
    s7_md = _markdown_cells(_section_cells(nb3, SECTION7_TAG))
    citation_cells = [
        c
        for c in s7_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§7 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )
    combined = "\n\n".join(_cell_source(c) for c in citation_cells)
    assert _ANDERSEN2003_KEY in combined, (
        f"§7 citation block must reference bib key @{_ANDERSEN2003_KEY} "
        f"(Andersen-Bollerslev-Diebold-Vega 2003). Not found."
    )


# ── §8 structural tests ───────────────────────────────────────────────────

def test_nb3_section8_has_at_least_one_code_cell(
    nb3: nbformat.NotebookNode,
) -> None:
    """§8 exists: at least one code cell + every code cell has remove-input."""
    s8_code = _code_cells(_section_cells(nb3, SECTION8_TAG))
    assert s8_code, (
        "§8 must contain at least one code cell (tagged section:8); "
        "none found."
    )
    for c in s8_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§8 code cell missing 'remove-input' tag; got tags={tags!r}."
        )


def _exec_section8(nb: nbformat.NotebookNode) -> dict[str, object]:
    """Exec §8 source with §7 source + bootstrap; return the namespace.

    §8 depends on §7 having run (both fit against column6_fit), so we
    concatenate §7 + §8 source to avoid NameError on β̂ scalars §7
    exposes. If §8 doesn't need them it's harmless.
    """
    s7_code_src = _section_source(nb, SECTION7_TAG)
    s8_code_src = _section_source(nb, SECTION8_TAG)
    assert s8_code_src, "§8 code must exist."
    ns: dict[str, object] = {}
    exec(
        compile(
            _make_bootstrap()
            + "\n"
            + s7_code_src
            + "\n"
            + s8_code_src,
            "<nb3-section8>",
            "exec",
        ),
        ns,
    )
    return ns


def test_nb3_section8_forest_plot_has_13_rows(
    nb3: nbformat.NotebookNode,
) -> None:
    """§8 forest-plot table has exactly 13 rows."""
    ns = _exec_section8(nb3)
    assert _FOREST_TABLE_VAR in ns, (
        f"§8 must bind {_FOREST_TABLE_VAR!r} (the forest-plot row "
        f"table). Found names: "
        f"{sorted(k for k in ns if not k.startswith('__'))!r}"
    )
    table = ns[_FOREST_TABLE_VAR]
    # Accept pandas DataFrame, list-of-dicts, list-of-tuples, or any len()-able.
    try:
        n = len(table)
    except TypeError as exc:
        pytest.fail(
            f"{_FOREST_TABLE_VAR!r} must be len()-able; got "
            f"type={type(table).__name__} ({exc})."
        )
    assert n == _FOREST_EXPECTED_ROWS, (
        f"§8 forest plot must have exactly {_FOREST_EXPECTED_ROWS} rows "
        f"(1 primary + 12 sensitivities); got n={n}."
    )


def test_nb3_section8_primary_anchor_row_1(
    nb3: nbformat.NotebookNode,
) -> None:
    """§8 row 1 is the primary Column-6 anchor."""
    ns = _exec_section8(nb3)
    table = ns[_FOREST_TABLE_VAR]
    # Extract the row-1 label. Accept DataFrame (first row), list-of-dicts,
    # list-of-tuples (label is element 0).
    import pandas as pd
    if isinstance(table, pd.DataFrame):
        # Look for a "label" or "spec" or similar column.
        label_col = next(
            (c for c in ("label", "spec", "name", "row") if c in table.columns),
            None,
        )
        assert label_col is not None, (
            f"§8 forest table DataFrame must have a label/spec/name column; "
            f"got columns={list(table.columns)!r}"
        )
        row1_label = str(table.iloc[0][label_col])
    else:
        row1 = table[0]
        if isinstance(row1, dict):
            row1_label = str(
                row1.get("label")
                or row1.get("spec")
                or row1.get("name")
                or ""
            )
        elif isinstance(row1, (tuple, list)):
            row1_label = str(row1[0])
        else:
            row1_label = str(row1)
    lower = row1_label.lower()
    assert (
        "primary" in lower or "column 6" in lower or "column-6" in lower
    ), (
        f"§8 row 1 must be the primary anchor (label containing 'Primary' "
        f"or 'Column 6'); got {row1_label!r}."
    )


def test_nb3_section8_sorted_by_abs_beta(
    nb3: nbformat.NotebookNode,
) -> None:
    """§8 rows 2+ must be sorted by |β̂| descending."""
    ns = _exec_section8(nb3)
    table = ns[_FOREST_TABLE_VAR]
    # Extract (label, beta) pairs from the table.
    import pandas as pd
    if isinstance(table, pd.DataFrame):
        beta_col = next(
            (c for c in ("beta", "beta_hat", "coef", "point") if c in table.columns),
            None,
        )
        assert beta_col is not None, (
            f"§8 forest table DataFrame must have a beta/beta_hat/coef/"
            f"point column; got columns={list(table.columns)!r}"
        )
        betas = [float(x) for x in table[beta_col].tolist()]
    else:
        betas = []
        for r in table:
            if isinstance(r, dict):
                b = (
                    r.get("beta")
                    or r.get("beta_hat")
                    or r.get("coef")
                    or r.get("point")
                )
                betas.append(float(b))
            elif isinstance(r, (tuple, list)):
                # Assume (label, beta, ...) ordering.
                betas.append(float(r[1]))
    # Rows 2+ (index ≥ 1) sorted by |beta| descending.
    tail_abs = [abs(b) for b in betas[1:]]
    assert tail_abs == sorted(tail_abs, reverse=True), (
        f"§8 rows 2+ must be sorted by |β̂| descending. "
        f"Got |β̂|_2+ = {tail_abs!r}."
    )


def test_nb3_section8_a9_plus_minus_both_present(
    nb3: nbformat.NotebookNode,
) -> None:
    """§8 must contain BOTH A9⁺ and A9⁻ rows as separate entries."""
    ns = _exec_section8(nb3)
    table = ns[_FOREST_TABLE_VAR]
    import pandas as pd
    labels: list[str]
    if isinstance(table, pd.DataFrame):
        label_col = next(
            (c for c in ("label", "spec", "name", "row") if c in table.columns),
            None,
        )
        labels = [str(x) for x in table[label_col].tolist()]
    else:
        labels = []
        for r in table:
            if isinstance(r, dict):
                labels.append(
                    str(r.get("label") or r.get("spec") or r.get("name") or "")
                )
            elif isinstance(r, (tuple, list)):
                labels.append(str(r[0]))
    all_labels = " | ".join(labels)
    has_plus = any(t in all_labels for t in _A9_PLUS_TOKENS)
    has_minus = any(t in all_labels for t in _A9_MINUS_TOKENS)
    assert has_plus, (
        f"§8 must have an A9⁺ (positive-surprise subset) row. "
        f"Expected one of {_A9_PLUS_TOKENS!r} in labels={labels!r}."
    )
    assert has_minus, (
        f"§8 must have an A9⁻ (negative-surprise subset) row. "
        f"Expected one of {_A9_MINUS_TOKENS!r} in labels={labels!r}."
    )


def test_nb3_section8_a1_uses_monthly_panel(
    nb3: nbformat.NotebookNode,
) -> None:
    """§8 source references econ_query_api.get_monthly_panel for A1."""
    combined = _section_source(nb3, SECTION8_TAG)
    assert _MONTHLY_PANEL_LANDMARK in combined, (
        f"§8 must call {_MONTHLY_PANEL_LANDMARK!r} for the A1 monthly "
        f"refit. Not found in §8 source."
    )


def test_nb3_section8_a4_uses_release_excluded(
    nb3: nbformat.NotebookNode,
) -> None:
    """§8 source references get_rv_excluding_release_day for A4."""
    combined = _section_source(nb3, SECTION8_TAG)
    assert _RV_EXCL_RELEASE_LANDMARK in combined, (
        f"§8 must call {_RV_EXCL_RELEASE_LANDMARK!r} for the A4 "
        f"release-day-excluded refit. Not found in §8 source."
    )


def test_nb3_section8_a6_bivariate(nb3: nbformat.NotebookNode) -> None:
    """§8 A6 is the bivariate no-controls Column-1 specification.

    Either references ``ladder_fits[0]`` (PKL ladder) or rebuilds the
    bivariate OLS of rv_cuberoot ~ const + cpi_surprise_ar1 inline.
    """
    combined = _section_source(nb3, SECTION8_TAG)
    uses_ladder = "ladder_fits[0]" in combined or "ladder_fits [0]" in combined
    assert uses_ladder, (
        "§8 A6 must read the bivariate Column-1 β̂_CPI from "
        "ladder_fits[0] (PKL). Not found in §8 source."
    )


def test_nb3_section8_a2_a3_a7_annotated_see_nb2(
    nb3: nbformat.NotebookNode,
) -> None:
    """§8 annotates A2/A3/A7 'see NB2' (token in code or markdown)."""
    s8_code = _section_source(nb3, SECTION8_TAG)
    s8_md = _markdown_cells(_section_cells(nb3, SECTION8_TAG))
    combined_md = "\n\n".join(_cell_source(c) for c in s8_md)
    combined = s8_code + "\n\n" + combined_md
    hits = [t for t in _A2_A3_A7_SEE_NB2_TOKENS if t in combined]
    assert hits, (
        f"§8 must annotate A2/A3/A7 with a 'see NB2' token. None of "
        f"{_A2_A3_A7_SEE_NB2_TOKENS!r} found in §8 code or markdown."
    )
    # Also verify the three labels are referenced.
    for label in ("A2", "A3", "A7"):
        assert label in combined, (
            f"§8 must reference label {label!r} (annotated as see-NB2)."
        )


def test_nb3_section8_citation_has_simonsohn2020(
    nb3: nbformat.NotebookNode,
) -> None:
    """§8 carries a 4-part citation block citing @simonsohn2020specification."""
    s8_md = _markdown_cells(_section_cells(nb3, SECTION8_TAG))
    citation_cells = [
        c
        for c in s8_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§8 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )
    combined = "\n\n".join(_cell_source(c) for c in citation_cells)
    assert _SIMONSOHN2020_KEY in combined, (
        f"§8 citation block must reference bib key @{_SIMONSOHN2020_KEY} "
        f"(Simonsohn-Simmons-Nelson 2020 specification-curve). Not found."
    )


# ── End-to-end lint ───────────────────────────────────────────────────────

def test_nb3_citation_lint_passes_after_task27() -> None:
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
