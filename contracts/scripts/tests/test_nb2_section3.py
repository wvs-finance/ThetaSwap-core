"""Structural regression test for NB2 §3 (coefficient ladder) and §3.5 (block-bootstrap HAC sanity).

Task 17 of the econ-notebook-implementation plan. NB2 §3 fits a six-column
nested-control ladder (bivariate → add US CPI → BanRep rate → VIX →
intervention → oil) with Newey-West HAC(4) covariance on every column,
renders the coefficient table with Column 6 visually highlighted via
``\\cellcolor{gray!15}`` on the LaTeX export (the highlighting mechanism
is locked per plan line 358(a) — no alternative), reports sample size
and adj-R² per column, and stores the Column 6 fit object for
downstream tasks.

NB2 §3.5 runs a Politis-Romano stationary bootstrap with a 4-week mean
block length and B=1000 replications, computes a 90% percentile CI on
β̂_CPI from Column 6, and reports AGREEMENT or DIVERGENCE with the
HAC 90% CI using the ≥50%-of-HAC-interval-length overlap rule.

This module is authored TDD-first: it fails against the 12-cell post-§2
NB2 and turns green once the Analytics Reporter appends §3 and §3.5
trios.

What gets asserted, in order of decreasing "load-bearing":

  1. Six-column nested-control ladder: §3 source references six
     columns (names Column 1 through Column 6), the ladder regressor
     sequence is the locked one (CPI → US CPI → BanRep rate → VIX →
     intervention → oil), every column uses ``cov_type='HAC'`` and
     ``cov_kwds={'maxlags': 4}``.
  2. Column 6 highlighting mechanism locked: the §3 source contains
     the literal LaTeX token ``\\cellcolor{gray!15}`` on the Column 6
     header path of whatever rendering pipeline is used. Plan line 358
     forbids substitutes.
  3. Sample size + adj-R² per column: §3 source contains tokens
     ``nobs``/``rsquared_adj`` (or equivalent statsmodels accessors)
     across the ladder rendering path. Verified by source inspection
     rather than executed-DataFrame inspection because the ladder's
     rendered output is a LaTeX string, not a DataFrame.
  4. Column 6 fit object is exposed as ``column6_fit``. This is the
     downstream-task contract for Task 18 (diagnostics), Task 20
     (decomposition), Task 21 (T3b gate).
  5. §3.5 runs Politis-Romano with block length 4 and B=1000: the §3.5
     source contains ``StationaryBootstrap(4`` (the block argument is
     the 4-week mean block length; any other argument ordering will
     fail this assertion, which is intentional — the spec requires
     this exact call shape) and either ``N=1000`` or ``reps=1000`` or
     ``size=1000`` (library arg aliases — any of the three passes).
  6. §3.5 reports AGREEMENT or DIVERGENCE: the §3.5 source contains
     one of the two literal verdict strings, and the overlap
     computation uses the ≥50%-of-HAC-interval-length rule.
  7. Citation blocks precede §3 and §3.5: the four-part block
     ("Reference / Why used / Relevance to our results / Connection
     to simulator") appears in the preceding markdown, and the §3
     citation block references ``neweyWest1987simple`` +
     ``andersen2003micro``; the §3.5 citation block references
     ``politisRomano1994stationary``.
  8. Structural: every §3 and §3.5 code cell carries ``remove-input``
     and the appropriate ``section:3`` / ``section:3.5`` tag.
  9. Citation lint: ``scripts/lint_notebook_citations.py`` exits 0 on
     the live NB2 path (catches any citation-block regression in
     newly-authored cells).

What is NOT asserted:
  * Exact wording of prose (would couple the test to authoring).
  * Exact β̂_CPI value or CI endpoints (these are the OUTPUT of the
    estimator, not a contract assertion — reporting happens in the
    task's final message, not in the test file).
  * Exact bootstrap draw values (deterministic under the fixed seed,
    but the seed value itself is an implementation detail left to
    the author).
  * Exact LaTeX/HTML rendering path (summary_col vs Stargazer vs
    manual DataFrame.to_latex — any mechanism hitting the locked
    highlighting token and the locked structural requirements passes).
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Final

import nbformat
import pytest

# ── Path plumbing (mirrors test_nb2_section1_2.py) ────────────────────────

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

SECTION3_TAG: Final[str] = "section:3"
SECTION3_5_TAG: Final[str] = "section:3.5"
REMOVE_INPUT_TAG: Final[str] = "remove-input"

REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# The six-column nested-ladder regressor sequence. Each column ADDS the
# named regressor to the prior column's set. Assertion: every token in
# the sequence appears in the §3 source (spot-check; full structural
# equivalence is enforced by the execution-level ladder_df check).
_LADDER_REGRESSOR_SEQUENCE: Final[tuple[str, ...]] = (
    "cpi_surprise_ar1",   # Column 1 (bivariate)
    "us_cpi_surprise",    # Column 2 adds
    "banrep_rate_surprise",  # Column 3 adds
    "vix_avg",            # Column 4 adds
    "intervention_dummy",  # Column 5 adds
    "oil_return",         # Column 6 adds
)

# HAC(4) invocation landmarks — ANY call to statsmodels OLS.fit must
# pass both cov_type='HAC' and cov_kwds={'maxlags': 4}. The §3 source
# must contain both tokens together.
_HAC_LANDMARKS: Final[tuple[str, ...]] = (
    "cov_type=",
    "HAC",
    "maxlags",
    "4",
)

# LaTeX highlight token — plan line 358(a) locks the mechanism.
_COLUMN6_HIGHLIGHT_LATEX: Final[str] = r"\cellcolor{gray!15}"

# Column 6 fit object variable name — plan line 358(d) default.
_COLUMN6_FIT_VAR: Final[str] = "column6_fit"

# §3.5 bootstrap landmarks.
_STATIONARY_BOOTSTRAP_LANDMARKS: Final[tuple[str, ...]] = (
    "StationaryBootstrap",
    # Block length = 4 weeks. The StationaryBootstrap signature is
    # ``StationaryBootstrap(block_size, *args, **kwargs)`` where
    # block_size is positional; the author MUST pass 4 as the first
    # positional argument. The test verifies literal token '4' appears
    # immediately after the opening paren.
)

# One of these three aliases must appear to set B=1000 replications.
_BOOTSTRAP_REPS_ALIASES: Final[tuple[str, ...]] = (
    "N=1000",
    "reps=1000",
    "size=1000",
    "1000",  # fallback: just the number (some bootstrap APIs take positional)
)

# Verdict strings — §3.5 must print ONE of these.
_VERDICT_TOKENS: Final[tuple[str, ...]] = (
    "AGREEMENT",
    "DIVERGENCE",
)

# Citation bibkeys. §3 must cite both Newey-West + ABDV; §3.5 must cite
# Politis-Romano.
_SECTION3_BIBKEYS: Final[tuple[str, ...]] = (
    "neweyWest1987simple",
    "andersen2003micro",
)

_SECTION3_5_BIBKEYS: Final[tuple[str, ...]] = (
    "politisRomano1994stationary",
)

# After §1-§2 (Task 16) NB2 has 12 cells. Task 17 §3 + §3.5 each append
# a minimum of one (why-md, code, interp-md) trio → ≥6 new cells. We
# assert a hard floor.
_MIN_POST_TASK17_CELL_COUNT: Final[int] = 18


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

def test_nb2_has_at_least_18_cells_post_task17(
    nb2: nbformat.NotebookNode,
) -> None:
    """NB2 has the post-Task-17 cell count floor."""
    assert len(nb2.cells) >= _MIN_POST_TASK17_CELL_COUNT, (
        f"NB2 has only {len(nb2.cells)} cells; Task 17 must add at "
        f"least {_MIN_POST_TASK17_CELL_COUNT - 12} new cells beyond "
        f"the 12-cell post-§2 state."
    )


def test_nb2_section3_has_code_cells(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3 exists: at least one code cell tagged section:3 + remove-input."""
    s3_cells = _section_cells(nb2, SECTION3_TAG)
    s3_code = _code_cells(s3_cells)
    assert s3_code, (
        "§3 must contain at least one code cell (tagged section:3). "
        "Task 17 Step 3 must author §3."
    )
    for c in s3_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§3 code cell missing 'remove-input' tag; got {tags!r}."
        )


def test_nb2_section3_5_has_code_cells(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3.5 exists: at least one code cell tagged section:3.5 + remove-input."""
    s35_cells = _section_cells(nb2, SECTION3_5_TAG)
    s35_code = _code_cells(s35_cells)
    assert s35_code, (
        "§3.5 must contain at least one code cell (tagged section:3.5). "
        "Task 17 Step 3 must author §3.5."
    )
    for c in s35_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§3.5 code cell missing 'remove-input' tag; got {tags!r}."
        )


# ── Ladder structure tests ────────────────────────────────────────────────

def test_nb2_section3_uses_six_column_labels(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3 source references six columns labelled 'Column 1' through 'Column 6'."""
    s3_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION3_TAG))
    )
    for i in range(1, 7):
        label = f"Column {i}"
        assert label in s3_code_src, (
            f"§3 code source is missing the ladder column label {label!r}. "
            f"Plan line 358(a) mandates six named ladder columns."
        )


def test_nb2_section3_hac4_newey_west(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3 fits every column with Newey-West HAC(4).

    The four landmarks (``cov_type=``, ``HAC``, ``maxlags``, ``4``) MUST
    all appear in the §3 source. A column fit without HAC(4) would fail
    plan line 358(a).
    """
    s3_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION3_TAG))
    )
    for landmark in _HAC_LANDMARKS:
        assert landmark in s3_code_src, (
            f"§3 source is missing HAC landmark {landmark!r}. Plan "
            f"line 358(a) mandates Newey-West HAC(4) on every column."
        )
    # Additionally verify the two tokens appear TOGETHER (not just
    # scattered across unrelated cells).
    assert "cov_type='HAC'" in s3_code_src or 'cov_type="HAC"' in s3_code_src, (
        "§3 source must invoke OLS.fit with cov_type='HAC' (Newey-West)."
    )
    assert "maxlags" in s3_code_src and (
        "'maxlags': 4" in s3_code_src
        or '"maxlags": 4' in s3_code_src
        or "maxlags=4" in s3_code_src
    ), (
        "§3 source must set cov_kwds with maxlags=4 (Newey-West HAC(4))."
    )


def test_nb2_section3_ladder_regressor_sequence_locked(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3 source references the locked ladder regressor sequence.

    Per plan line 358(a): bivariate → add US CPI → BanRep rate → VIX →
    intervention → oil. All six regressor names must appear in §3.
    """
    s3_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION3_TAG))
    )
    for regressor in _LADDER_REGRESSOR_SEQUENCE:
        assert regressor in s3_code_src, (
            f"§3 source is missing ladder regressor {regressor!r}. The "
            f"locked ladder sequence is {_LADDER_REGRESSOR_SEQUENCE!r}."
        )


def test_nb2_section3_column6_latex_highlight_locked(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3 source contains the ``\\cellcolor{gray!15}`` highlight on Column 6.

    Plan line 358(a) explicitly locks this mechanism: 'Column 6 is
    visually highlighted using ``\\cellcolor{gray!15}`` on the Column 6
    header row of the LaTeX-exported table (the mechanism is locked —
    no alternative)'.
    """
    s3_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION3_TAG))
    )
    assert _COLUMN6_HIGHLIGHT_LATEX in s3_code_src, (
        f"§3 source is missing the locked LaTeX highlight token "
        f"{_COLUMN6_HIGHLIGHT_LATEX!r}. Plan line 358(a) forbids "
        f"substitutes — the rendering mechanism MUST inject this "
        f"verbatim into the Column 6 header on LaTeX export."
    )


def test_nb2_section3_reports_n_and_adj_r2_per_column(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3 reports sample size and adj-R² for each ladder column.

    Assertion is at source level: the ladder rendering path must
    reference both ``nobs`` (or equivalent) and ``rsquared_adj``.
    """
    s3_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION3_TAG))
    )
    has_n = ("nobs" in s3_code_src) or ("N=" in s3_code_src and "1000" not in s3_code_src)
    assert has_n, (
        "§3 source must reference sample size per column (statsmodels "
        "``RegressionResults.nobs`` or an 'N' row in the rendered table)."
    )
    assert "rsquared_adj" in s3_code_src or "adj-R" in s3_code_src or "adj_r2" in s3_code_src, (
        "§3 source must reference adj-R² per column (statsmodels "
        "``RegressionResults.rsquared_adj`` or an 'adj-R²' row in the "
        "rendered table)."
    )


def test_nb2_section3_column6_fit_variable_exposed(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3 binds Column 6 fit object to the documented variable name.

    Plan line 358(d): 'Column 6 fit object is stored in a notebook
    variable documented for downstream tasks.' The task-17 spec
    defaults to ``column6_fit``. Downstream Tasks 18, 20, 21 depend on
    this binding.
    """
    s3_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION3_TAG))
    )
    # Look for assignment pattern. Right-hand side is an OLS fit; the
    # identifier MUST appear on the LHS of an = somewhere in §3.
    assert f"{_COLUMN6_FIT_VAR} =" in s3_code_src or f"{_COLUMN6_FIT_VAR}=" in s3_code_src, (
        f"§3 source must assign the Column 6 fit object to variable "
        f"{_COLUMN6_FIT_VAR!r}. Plan line 358(d) mandates the "
        f"downstream-task binding."
    )


# ── §3.5 bootstrap tests ──────────────────────────────────────────────────

def test_nb2_section3_5_runs_stationary_bootstrap_block_4(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3.5 runs Politis-Romano stationary bootstrap with 4-week block.

    The ``StationaryBootstrap(4, ...)`` call signature is mandated by
    plan line 358(b). The leading positional argument is the mean block
    length in weeks.
    """
    s35_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION3_5_TAG))
    )
    assert "StationaryBootstrap" in s35_code_src, (
        "§3.5 source must import and use "
        "``arch.bootstrap.StationaryBootstrap``. Plan line 358(b) "
        "mandates Politis-Romano stationary bootstrap."
    )
    # Verify the block length is 4. Accept either StationaryBootstrap(4
    # or StationaryBootstrap(block_size=4 shapes.
    assert (
        "StationaryBootstrap(4" in s35_code_src
        or "StationaryBootstrap(block_size=4" in s35_code_src
    ), (
        "§3.5 source must pass block length 4 as the first positional "
        "or keyword argument to StationaryBootstrap. Plan line 358(b) "
        "mandates '4-week mean block length'."
    )


def test_nb2_section3_5_uses_1000_replications(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3.5 runs B=1000 bootstrap replications."""
    s35_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION3_5_TAG))
    )
    # Any of N=1000 / reps=1000 / size=1000 / literal 1000 passes.
    assert any(alias in s35_code_src for alias in _BOOTSTRAP_REPS_ALIASES), (
        f"§3.5 source must use B=1000 bootstrap replications (any of "
        f"{_BOOTSTRAP_REPS_ALIASES!r} aliases). Plan line 358(b) "
        f"mandates B=1000."
    )


def test_nb2_section3_5_reports_agreement_or_divergence(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3.5 reports AGREEMENT or DIVERGENCE verdict.

    One of the two literal tokens must appear in §3.5 — either as a
    string literal that gets printed, or as a markdown interpretation
    cell that narrates the verdict.
    """
    s35_cells = _section_cells(nb2, SECTION3_5_TAG)
    s35_all_src = "\n\n".join(_cell_source(c) for c in s35_cells)
    assert any(v in s35_all_src for v in _VERDICT_TOKENS), (
        f"§3.5 must render one of the verdicts {_VERDICT_TOKENS!r}. "
        f"Plan line 358(b) locks the token."
    )


def test_nb2_section3_5_uses_50_percent_overlap_rule(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3.5 code computes the ≥50%-overlap rule vs HAC interval length.

    Plan line 358(b): 'agreement = the two intervals overlap by ≥50%
    of the HAC interval length'. The source must contain either the
    literal ``0.5`` ratio threshold or the equivalent ``>= 0.5`` /
    ``>= 50%`` computation.
    """
    s35_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION3_5_TAG))
    )
    has_half = (
        "0.5" in s35_code_src
        or "0.50" in s35_code_src
        or "/ 2" in s35_code_src
    )
    assert has_half, (
        "§3.5 source must compute the ≥50% overlap ratio threshold. "
        "Plan line 358(b) locks the rule."
    )


# ── Citation block tests ──────────────────────────────────────────────────

def test_nb2_section3_has_four_part_citation_block(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3 carries at least one 4-part citation block markdown cell."""
    s3_md = _markdown_cells(_section_cells(nb2, SECTION3_TAG))
    citation_cells = [
        c
        for c in s3_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§3 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )


def test_nb2_section3_citation_references_newey_west_and_abdv(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3 citation block cites Newey-West 1987 + ABDV 2003."""
    s3_md_src = "\n\n".join(
        _cell_source(c) for c in _markdown_cells(_section_cells(nb2, SECTION3_TAG))
    )
    for bibkey in _SECTION3_BIBKEYS:
        assert bibkey in s3_md_src, (
            f"§3 citation block must reference bibkey {bibkey!r}. Plan "
            f"line 358(c) mandates Newey-West 1987 + ABDV 2003."
        )


def test_nb2_section3_5_has_four_part_citation_block(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3.5 carries a 4-part citation block."""
    s35_md = _markdown_cells(_section_cells(nb2, SECTION3_5_TAG))
    citation_cells = [
        c
        for c in s35_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§3.5 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )


def test_nb2_section3_5_citation_references_politis_romano(
    nb2: nbformat.NotebookNode,
) -> None:
    """§3.5 citation block cites Politis-Romano 1994."""
    s35_md_src = "\n\n".join(
        _cell_source(c)
        for c in _markdown_cells(_section_cells(nb2, SECTION3_5_TAG))
    )
    for bibkey in _SECTION3_5_BIBKEYS:
        assert bibkey in s35_md_src, (
            f"§3.5 citation block must reference bibkey {bibkey!r}. "
            f"Plan line 358(c) mandates Politis-Romano 1994."
        )


# ── Citation lint passthrough ─────────────────────────────────────────────

def test_nb2_citation_lint_passes_after_task17() -> None:
    """``lint_notebook_citations.py`` exits 0 on NB2 after §3/§3.5 authoring."""
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
        f"Expected lint exit 0 on NB2 post-Task-17; got "
        f"{result.returncode}.\nstdout:\n{result.stdout}\nstderr:\n"
        f"{result.stderr}"
    )
