"""Structural regression tests for NB2 §8 subsample regimes + §9 T3b gate.

Task 21 of the econ-notebook-implementation plan. NB2 §8 refits the
Column-6 primary on three calendar regimes derived from the query
API's ``SUBSAMPLE_SPLITS`` constants (2015-01-05 and 2021-01-04),
reports per-regime (β̂, Σ̂, n, date range), runs a Wald χ² pooling
test AND a small-sample F pooling test against the null of a common
β̂_CPI across regimes, and carries a Bai-Perron 1998 caveat markdown
noting HAC over-rejection in small samples.

§9 declares the formal **T3b gate** for the pre-committed OLS primary:
two independent verdicts — (a) β̂_CPI − 1.28·SE(β̂_CPI) > 0 and (b)
adj-R² ≥ 0.15 — emitted as literal ``"PASS"`` / ``"FAIL"`` strings
bound to three notebook-module variables:

  * ``T3B_GATE_VERDICT``       — (a) alone
  * ``ADJ_R2_GATE_VERDICT``    — (b) alone
  * ``PRIMARY_GATE_VERDICT``   — AND of (a) and (b)

Per Rev 4 §1 the T3b gate is OLS-primary-only; GARCH-X cannot override
the OLS verdict. The interp-md must carry this admonition literally so
the scientific contract is readable from source (no rescue via
co-primaries allowed).

This module is authored TDD-first: it fails against the 30-cell
post-Task-20 NB2 and turns green once the Analytics Reporter appends
§8 and §9's trios (6 cells → 36 total).

What gets asserted:

  1. NB2 cell count ≥ 36 post-Task-21 (30 pre-Task-21 + 2 trios).
  2. §8 exists (tagged ``section:8``) and contains code + markdown cells.
  3. §8 splits the weekly panel at BOTH 2015-01-05 AND 2021-01-04 —
     three regimes.
  4. §8 reports per-regime β̂ (cpi_surprise_ar1 coefficient), HAC(4) Σ̂,
     n, and sample date range (min / max week_start).
  5. §8 reports a Wald χ² pooling test of H₀ "β̂_CPI is identical
     across regimes" with an emitted statistic + p-value.
  6. §8 reports a small-sample F pooling test of the same null with
     an emitted statistic + p-value.
  7. §8 interp-md carries the Bai-Perron HAC-over-rejection caveat.
  8. §8 citation block references ``baiPerron1998estimating``.
  9. §9 exists (tagged ``section:9``) and declares both T3b and
     adj-R² gate verdicts as literal PASS/FAIL emissions.
 10. §9 interp-md carries the Rev 4 §1 admonition that the gate is
     OLS-primary-only and GARCH-X cannot override.
 11. §9 citation block references ``balduzzi2001economic``.
 12. Structural: all §8 and §9 code cells carry ``remove-input``;
     §8 code cells carry ``section:8`` and §9 code cells carry
     ``section:9``.
 13. Citation lint: ``scripts/lint_notebook_citations.py`` exits 0 on
     NB2 post-Task-21.

What is NOT asserted:
  * Exact values of per-regime β̂_CPI, SE, or the pooling-test
    statistics (these are runtime outputs reported back in the Task 21
    final message, not test contracts).
  * The verdict direction itself — test only requires that the verdict
    is DECLARED as a literal PASS/FAIL string in the cell source so
    both branches are pre-registered.
  * Any NB3 downstream wiring — Task 22 scope.
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

SECTION8_TAG: Final[str] = "section:8"
SECTION9_TAG: Final[str] = "section:9"
REMOVE_INPUT_TAG: Final[str] = "remove-input"

REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# §8 subsample splits — canonical query-API constants.
_SPLIT_TOKENS: Final[tuple[str, ...]] = (
    "2015-01-05",
    "2021-01-04",
)

# Acceptable forms for invoking the query API's subsample helper OR
# inlining the split dates via pandas Timestamp comparisons.
_SUBSAMPLE_ENTRYPOINTS: Final[tuple[str, ...]] = (
    "SUBSAMPLE_SPLITS",
    "get_weekly_panel_subsample",
    "week_start",
)

# Per-regime report must surface β̂, SE/Σ̂, n, and a date range. We
# accept any pattern that references the cpi_surprise_ar1 coefficient
# per regime and any pattern that reports date min/max + n.
_PER_REGIME_REQUIRED_TOKENS: Final[tuple[str, ...]] = (
    "cpi_surprise_ar1",
    "nobs",
)

_DATE_RANGE_TOKENS: Final[tuple[str, ...]] = (
    ".min()",
    ".max()",
)

# HAC(4) tokens — identical spec to §3 Column 6 (each regime refit).
_HAC4_TOKENS: Final[tuple[str, ...]] = (
    "HAC",
    "maxlags",
)

# Wald / F pooling test tokens.
_WALD_TOKENS: Final[tuple[str, ...]] = (
    "wald",
    "Wald",
    "chi2",
    "chi-squared",
    "χ²",
)

_F_POOLING_TOKENS: Final[tuple[str, ...]] = (
    "F-test",
    "f_test",
    "F_test",
    "F statistic",
    "F-statistic",
    "small-sample F",
    "small_sample_F",
)

_P_VALUE_TOKENS: Final[tuple[str, ...]] = (
    "pvalue",
    "p-value",
    "p_value",
    "pvalues",
)

# Bai-Perron 1998 caveat.
_BAI_PERRON_CAVEAT_TOKENS: Final[tuple[str, ...]] = (
    "Bai-Perron",
    "Bai and Perron",
    "Bai–Perron",
    "baiPerron",
)

_HAC_OVER_REJECTION_TOKENS: Final[tuple[str, ...]] = (
    "over-reject",
    "over reject",
    "overreject",
    "small-sample",
    "small sample",
)

# §9 formal T3b gate tokens — the source must emit literal PASS/FAIL
# strings for each gate component.
_T3B_GATE_VERDICT_VAR: Final[str] = "T3B_GATE_VERDICT"
_ADJ_R2_GATE_VERDICT_VAR: Final[str] = "ADJ_R2_GATE_VERDICT"
_PRIMARY_GATE_VERDICT_VAR: Final[str] = "PRIMARY_GATE_VERDICT"

_LITERAL_PASS: Final[str] = '"PASS"'
_LITERAL_FAIL: Final[str] = '"FAIL"'

# §9 T3b statistic expression — β̂ − 1.28·SE > 0.
_T3B_STATISTIC_TOKENS: Final[tuple[str, ...]] = (
    "1.28",
    "cpi_surprise_ar1",
)

# §9 adj-R² threshold — 0.15.
_ADJ_R2_THRESHOLD_TOKENS: Final[tuple[str, ...]] = (
    "0.15",
    "rsquared_adj",
)

# Rev 4 §1 admonition — OLS primary only; GARCH-X cannot override.
_REV4_ADMONITION_TOKENS: Final[tuple[str, ...]] = (
    "OLS-primary-only",
    "OLS primary only",
    "GARCH-X cannot override",
    "cannot override",
)

_REV4_ADMONITION_CITATION_TOKENS: Final[tuple[str, ...]] = (
    "Rev 4",
    "§1",
)

# Citation bibkeys — §8 cites Bai-Perron 1998; §9 cites Balduzzi 2001.
_SECTION8_BIBKEYS: Final[tuple[str, ...]] = (
    "baiPerron1998estimating",
)
_SECTION9_BIBKEYS: Final[tuple[str, ...]] = (
    "balduzzi2001economic",
)

# After Task 20 NB2 has 30 cells. Task 21 appends 2 trios → ≥6 new
# cells → floor of 36.
_MIN_POST_TASK21_CELL_COUNT: Final[int] = 36


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


# ── NB2 size + section presence tests ─────────────────────────────────────

def test_nb2_has_at_least_36_cells_post_task21(
    nb2: nbformat.NotebookNode,
) -> None:
    """NB2 has the post-Task-21 cell count floor."""
    assert len(nb2.cells) >= _MIN_POST_TASK21_CELL_COUNT, (
        f"NB2 has only {len(nb2.cells)} cells; Task 21 must add at "
        f"least {_MIN_POST_TASK21_CELL_COUNT - 30} new cells beyond "
        f"the 30-cell post-Task-20 state."
    )


def test_nb2_section8_has_code_cells(
    nb2: nbformat.NotebookNode,
) -> None:
    """§8 exists: at least one code cell tagged section:8 + remove-input."""
    s8_cells = _section_cells(nb2, SECTION8_TAG)
    s8_code = _code_cells(s8_cells)
    assert s8_code, (
        "§8 must contain at least one code cell (tagged section:8). "
        "Task 21 must author §8."
    )
    for c in s8_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§8 code cell missing 'remove-input' tag; got {tags!r}."
        )


def test_nb2_section9_has_code_cells(
    nb2: nbformat.NotebookNode,
) -> None:
    """§9 exists: at least one code cell tagged section:9 + remove-input."""
    s9_cells = _section_cells(nb2, SECTION9_TAG)
    s9_code = _code_cells(s9_cells)
    assert s9_code, (
        "§9 must contain at least one code cell (tagged section:9). "
        "Task 21 must author §9."
    )
    for c in s9_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§9 code cell missing 'remove-input' tag; got {tags!r}."
        )


# ── §8 subsample-regime specification tests ───────────────────────────────

def test_nb2_section8_has_three_regimes(
    nb2: nbformat.NotebookNode,
) -> None:
    """§8 source splits the weekly panel at BOTH 2015-01-05 AND 2021-01-04.

    Plan Task 21: "three regimes from the query API's subsample-split
    constants (pre 2015-01-05, 2015-01-05 through 2021-01-04, post
    2021-01-04)". Both split literals must appear in §8 source.
    """
    s8_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION8_TAG))
    )
    for split in _SPLIT_TOKENS:
        assert split in s8_code_src, (
            f"§8 source must reference the split date {split!r}. Plan "
            f"Task 21 mandates three calendar regimes derived from the "
            f"query API's SUBSAMPLE_SPLITS constants."
        )
    # Source must reach the subsample split via the canonical API or an
    # equivalent week_start comparison — not via magic constants.
    has_entrypoint = any(t in s8_code_src for t in _SUBSAMPLE_ENTRYPOINTS)
    assert has_entrypoint, (
        f"§8 source must use the canonical subsample entrypoint "
        f"(any of {_SUBSAMPLE_ENTRYPOINTS!r}) — either the query-API "
        f"constant/helper or an explicit ``week_start`` comparison."
    )


def test_nb2_section8_per_regime_reports_beta_sigma_n_daterange(
    nb2: nbformat.NotebookNode,
) -> None:
    """§8 reports per-regime β̂, Σ̂, n, and sample date range."""
    s8_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION8_TAG))
    )
    for token in _PER_REGIME_REQUIRED_TOKENS:
        assert token in s8_code_src, (
            f"§8 source must report {token!r} per regime. Plan Task 21 "
            f"mandates per-regime (β̂, Σ̂, n, date range) tabulation."
        )
    for token in _DATE_RANGE_TOKENS:
        assert token in s8_code_src, (
            f"§8 source must report the regime date range (token "
            f"{token!r} missing — expected ``week_start.min()`` / "
            f"``.max()`` pattern)."
        )
    # HAC(4) must be used per regime — the inference machinery is
    # identical to §3 Column 6 so the per-regime SEs are comparable.
    for token in _HAC4_TOKENS:
        assert token in s8_code_src, (
            f"§8 source must use HAC(4) covariance per regime (token "
            f"{token!r} missing). Plan Task 21 mandates identical "
            f"inference spec as §3 Column 6 for every regime refit."
        )


def test_nb2_section8_reports_wald_chi2_pooling(
    nb2: nbformat.NotebookNode,
) -> None:
    """§8 reports a Wald χ² pooling test + p-value."""
    s8_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION8_TAG))
    )
    has_wald = any(t in s8_code_src for t in _WALD_TOKENS)
    assert has_wald, (
        f"§8 source must run a Wald χ² pooling test (any of "
        f"{_WALD_TOKENS!r}). Plan Task 21 mandates both a Wald χ² and "
        f"a small-sample F test of H₀: β̂_CPI identical across regimes."
    )
    has_pvalue = any(t in s8_code_src for t in _P_VALUE_TOKENS)
    assert has_pvalue, (
        f"§8 source must emit the Wald test p-value (any of "
        f"{_P_VALUE_TOKENS!r})."
    )


def test_nb2_section8_reports_small_sample_F_pooling(
    nb2: nbformat.NotebookNode,
) -> None:
    """§8 reports a small-sample F pooling test + p-value."""
    s8_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION8_TAG))
    )
    has_f = any(t in s8_code_src for t in _F_POOLING_TOKENS)
    assert has_f, (
        f"§8 source must run a small-sample F pooling test (any of "
        f"{_F_POOLING_TOKENS!r}). Plan Task 21 mandates both a Wald χ² "
        f"and a small-sample F test, both p-values reported."
    )


def test_nb2_section8_has_bai_perron_caveat(
    nb2: nbformat.NotebookNode,
) -> None:
    """§8 markdown carries the Bai-Perron HAC over-rejection caveat."""
    s8_md_src = "\n\n".join(
        _cell_source(c) for c in _markdown_cells(_section_cells(nb2, SECTION8_TAG))
    )
    has_bai_perron = any(t in s8_md_src for t in _BAI_PERRON_CAVEAT_TOKENS)
    assert has_bai_perron, (
        f"§8 markdown must carry a Bai-Perron caveat (any of "
        f"{_BAI_PERRON_CAVEAT_TOKENS!r}). Plan Task 21 mandates an "
        f"explicit note that HAC standard errors over-reject structural "
        f"break tests in small samples."
    )
    has_over_rejection = any(
        t in s8_md_src for t in _HAC_OVER_REJECTION_TOKENS
    )
    assert has_over_rejection, (
        f"§8 markdown must note the HAC over-rejection mechanism (any "
        f"of {_HAC_OVER_REJECTION_TOKENS!r}). Plan Task 21 mandates the "
        f"small-sample Bai-Perron 1998 artifact be explicitly flagged."
    )


def test_nb2_section8_citation_has_bai_perron_1998(
    nb2: nbformat.NotebookNode,
) -> None:
    """§8 citation block cites Bai-Perron 1998 (``baiPerron1998estimating``)."""
    s8_md_src = "\n\n".join(
        _cell_source(c) for c in _markdown_cells(_section_cells(nb2, SECTION8_TAG))
    )
    for bibkey in _SECTION8_BIBKEYS:
        assert bibkey in s8_md_src, (
            f"§8 citation block must reference bibkey {bibkey!r}. Plan "
            f"Task 21 mandates Bai-Perron 1998 (structural-break + HAC "
            f"over-rejection provenance)."
        )


def test_nb2_section8_has_four_part_citation_block(
    nb2: nbformat.NotebookNode,
) -> None:
    """§8 carries at least one 4-part citation block markdown cell."""
    s8_md = _markdown_cells(_section_cells(nb2, SECTION8_TAG))
    citation_cells = [
        c
        for c in s8_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§8 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )


# ── §9 formal T3b gate tests ──────────────────────────────────────────────

def test_nb2_section9_formal_t3b_gate_declared(
    nb2: nbformat.NotebookNode,
) -> None:
    """§9 declares T3B_GATE_VERDICT as a literal PASS/FAIL emission."""
    s9_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION9_TAG))
    )
    assert _T3B_GATE_VERDICT_VAR in s9_code_src, (
        f"§9 source must bind the module variable "
        f"{_T3B_GATE_VERDICT_VAR!r}. Task 22 consumes this handle to "
        f"serialize the verdict into nb2_params_point.json."
    )
    # Both literal PASS and literal FAIL strings must appear so both
    # branches are pre-registered in source.
    assert _LITERAL_PASS in s9_code_src, (
        f"§9 source must pre-register the literal {_LITERAL_PASS!r} "
        f"branch (anti-fishing: both verdicts are authored before the "
        f"computation runs)."
    )
    assert _LITERAL_FAIL in s9_code_src, (
        f"§9 source must pre-register the literal {_LITERAL_FAIL!r} "
        f"branch."
    )
    # The β̂ − 1.28·SE statistic must be computed explicitly.
    for token in _T3B_STATISTIC_TOKENS:
        assert token in s9_code_src, (
            f"§9 source must compute the T3b statistic β̂ − 1.28·SE "
            f"(token {token!r} missing)."
        )


def test_nb2_section9_formal_adj_r2_gate_declared(
    nb2: nbformat.NotebookNode,
) -> None:
    """§9 declares ADJ_R2_GATE_VERDICT as a literal PASS/FAIL emission."""
    s9_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION9_TAG))
    )
    assert _ADJ_R2_GATE_VERDICT_VAR in s9_code_src, (
        f"§9 source must bind the module variable "
        f"{_ADJ_R2_GATE_VERDICT_VAR!r}."
    )
    for token in _ADJ_R2_THRESHOLD_TOKENS:
        assert token in s9_code_src, (
            f"§9 source must check adj-R² ≥ 0.15 (token {token!r} "
            f"missing)."
        )


def test_nb2_section9_emits_primary_gate_verdict(
    nb2: nbformat.NotebookNode,
) -> None:
    """§9 emits the composite PRIMARY_GATE_VERDICT (AND of the two)."""
    s9_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION9_TAG))
    )
    assert _PRIMARY_GATE_VERDICT_VAR in s9_code_src, (
        f"§9 source must bind the composite module variable "
        f"{_PRIMARY_GATE_VERDICT_VAR!r} — the AND of T3b and adj-R² "
        f"verdicts. This is the scientific answer to the research "
        f"question."
    )


def test_nb2_section9_has_ols_primary_only_admonition(
    nb2: nbformat.NotebookNode,
) -> None:
    """§9 interp-md carries the Rev 4 §1 OLS-primary-only admonition.

    Plan Task 21 mandates literal text: "Gate is OLS-primary-only per
    Rev 4 §1; GARCH-X cannot override." or equivalent admonition.
    """
    s9_md_src = "\n\n".join(
        _cell_source(c) for c in _markdown_cells(_section_cells(nb2, SECTION9_TAG))
    )
    has_admonition = any(t in s9_md_src for t in _REV4_ADMONITION_TOKENS)
    assert has_admonition, (
        f"§9 interp-md must carry the OLS-primary-only admonition (any "
        f"of {_REV4_ADMONITION_TOKENS!r}). Plan Task 21 mandates the "
        f"literal Rev 4 §1 anti-fishing admonition: the gate is "
        f"OLS-primary-only and GARCH-X cannot override."
    )
    # Citation anchor — must reference Rev 4 §1 explicitly.
    for token in _REV4_ADMONITION_CITATION_TOKENS:
        assert token in s9_md_src, (
            f"§9 interp-md must cite the Rev 4 admonition anchor "
            f"{token!r}."
        )


def test_nb2_section9_citation_has_balduzzi2001_and_rev4_t3b(
    nb2: nbformat.NotebookNode,
) -> None:
    """§9 citation block cites ``balduzzi2001economic`` + Rev 4 §5 T3b."""
    s9_md_src = "\n\n".join(
        _cell_source(c) for c in _markdown_cells(_section_cells(nb2, SECTION9_TAG))
    )
    for bibkey in _SECTION9_BIBKEYS:
        assert bibkey in s9_md_src, (
            f"§9 citation block must reference bibkey {bibkey!r}. Plan "
            f"Task 21 mandates Balduzzi-Elton-Green 2001 (T3b "
            f"economic-news + bond-price provenance)."
        )
    # Rev 4 §5 T3b anchor — spec lock reference.
    assert "T3b" in s9_md_src, (
        "§9 citation block must anchor on the Rev 4 §5 T3b gate "
        "specification (token 'T3b' missing)."
    )


def test_nb2_section9_has_four_part_citation_block(
    nb2: nbformat.NotebookNode,
) -> None:
    """§9 carries at least one 4-part citation block markdown cell."""
    s9_md = _markdown_cells(_section_cells(nb2, SECTION9_TAG))
    citation_cells = [
        c
        for c in s9_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§9 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )


# ── Citation lint passthrough ─────────────────────────────────────────────

def test_nb2_citation_lint_passes_after_task21() -> None:
    """``lint_notebook_citations.py`` exits 0 on NB2 after §8-§9 authoring."""
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
        f"Expected lint exit 0 on NB2 post-Task-21; got "
        f"{result.returncode}.\nstdout:\n{result.stdout}\nstderr:\n"
        f"{result.stderr}"
    )
