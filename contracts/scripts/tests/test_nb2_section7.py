"""Structural regression tests for NB2 §7 CPI/PPI decomposition co-primary.

Task 20 of the econ-notebook-implementation plan. NB2 §7 refits the
Column-6 weekly OLS primary with a standardized ΔIPP (producer-price
index MoM change) added alongside ``cpi_surprise_ar1``. The refit
decomposes the price-level shock into two channels:

  * **CPI channel** — demand-side inflation proxy (``cpi_surprise_ar1``,
    AR(1)-residualized, already near-standardized by construction).
  * **Producer-cost channel** — supply-side inflation proxy
    (standardized ΔIPP: ``dane_ipp_pct`` recentered to mean 0 and
    rescaled to std 1 so its coefficient is directly comparable to
    β̂_CPI).

The specification per plan Task 20 (line 401) + design spec §4.1
(decomposition block) + Conrad-Schoelkopf-Tushteva 2025 (decomposition
convention):

    rv_cuberoot_t = α + β_CPI · cpi_surprise_ar1_t
                      + β_PPI · ipp_std_t
                      + γ_1 · us_cpi_surprise_t
                      + γ_2 · banrep_rate_surprise_t
                      + γ_3 · vix_avg_t
                      + γ_4 · oil_return_t
                      + γ_5 · intervention_dummy_t
                      + ε_t

using Newey-West HAC(4) (the identical covariance mechanism as §3 /
Column 6). Output must include:

  1. Point estimates β̂_CPI (on ``cpi_surprise_ar1``) and β̂_PPI (on
     ``ipp_std``).
  2. HAC(4) standard errors for both coefficients.
  3. The 2×2 joint HAC covariance block on {cpi_surprise_ar1, ipp_std}
     — extracted via ``results.cov_params().loc[[...], [...]]``.
  4. An interpretation that branches on **channel dominance**: if
     ``|β̂_CPI| > |β̂_PPI|`` the verdict is "inflation channel", else
     "producer-cost channel". The verdict is descriptive only — no
     auto-gate is fired.

This module is authored TDD-first: it fails against the 27-cell
post-Task-19 NB2 and turns green once the Analytics Reporter appends
§7's trio.

What gets asserted:

  1. §7 adds the standardized ΔIPP regressor — source contains
     ``ipp_std`` or an explicit ``.mean()`` / ``.std()`` transform on
     ``dane_ipp_pct``.
  2. §7 uses HAC(4) — same covariance spec as §3 (Newey-West 1987 /
     ABDV 2003 convention, ``maxlags=4``).
  3. §7 reports β̂_CPI — source references ``cpi_surprise_ar1``
     coefficient extraction.
  4. §7 reports β̂_PPI — source references ``ipp_std`` coefficient
     extraction.
  5. §7 reports the 2×2 joint HAC covariance block — source contains
     a ``cov_params()`` call subsetted on both ``cpi_surprise_ar1`` and
     ``ipp_std``.
  6. §7 interpretation markdown contains BOTH channel-dominance
     verdicts ("inflation-channel" / "inflation channel" AND
     "producer-cost channel") so the branch is pre-registered in
     source regardless of which one fires at runtime.
  7. §7 interpretation compares to Column 6's β̂_CPI — source
     references ``column6_fit`` OR numerically cites Column 6's
     β̂_CPI (-0.000685 / Task 17 findings digest).
  8. §7 citation block references ``conrad2025longterm`` (the
     decomposition convention paper).
  9. Structural: every §7 code cell carries ``remove-input`` and
     ``section:7``; at least one markdown cell in §7 carries the
     four-part citation block headers.
 10. NB2 cell count is ≥30 post-Task-20 (27 pre-Task-20 + ≥3 trio
     cells).
 11. Citation lint: ``scripts/lint_notebook_citations.py`` exits 0 on
     NB2 post-Task-20.

What is NOT asserted:
  * Exact wording of prose interpretations.
  * Exact value of β̂_PPI, β̂_CPI in the decomposition spec, or the
    2×2 covariance matrix entries (these are OUTPUTS reported in the
    Task 20 final message, not test contracts).
  * Whether the channel-dominance verdict actually resolves to CPI or
    PPI — both branches are pre-registered in source so a runtime
    flip does not require code edits.
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

SECTION7_TAG: Final[str] = "section:7"
REMOVE_INPUT_TAG: Final[str] = "remove-input"

REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# Standardized ΔIPP — either a pre-computed ``ipp_std`` binding in the
# §7 cell (expected pattern) or an explicit inline standardization on
# ``dane_ipp_pct`` (``(x - x.mean()) / x.std()``).
_IPP_STD_ALIASES: Final[tuple[str, ...]] = (
    "ipp_std",
    "dane_ipp_pct",
)

_IPP_STANDARDIZATION_TOKENS: Final[tuple[str, ...]] = (
    ".mean()",
    ".std()",
)

# HAC(4) tokens — identical spec to §3 Column 6.
_HAC4_TOKENS: Final[tuple[str, ...]] = (
    "HAC",
    "maxlags",
)

# Channel-dominance verdicts — both strings must appear in interp-md so
# the branch is pre-registered in source regardless of which one fires.
_CHANNEL_DOMINANCE_TOKENS: Final[tuple[str, ...]] = (
    "inflation channel",
    "inflation-channel",
)
_PRODUCER_COST_TOKENS: Final[tuple[str, ...]] = (
    "producer-cost channel",
    "producer-cost-channel",
    "producer cost channel",
)

# Column-6 comparison — source must reference either the fit handle or
# cite the Column 6 β̂_CPI numerically.
_COLUMN6_COMPARISON_TOKENS: Final[tuple[str, ...]] = (
    "column6_fit",
    "-0.000685",
    "−0.000685",  # en-dash variant
    "Column 6",
)

# 2×2 joint HAC covariance block — source must subset ``cov_params()``
# on both regressors. Accept common subset-indexer forms.
_COV_PARAMS_TOKENS: Final[tuple[str, ...]] = (
    "cov_params()",
    ".cov_params(",
)
_COV_BLOCK_SUBSET_TOKENS: Final[tuple[str, ...]] = (
    "cpi_surprise_ar1",
    "ipp_std",
)

# Decomposition bibkey.
_SECTION7_BIBKEYS: Final[tuple[str, ...]] = (
    "conrad2025longterm",
)

# After Task 19 NB2 has 27 cells. Task 20 §7 appends a minimum of one
# (why-md, code, interp-md) trio → ≥3 new cells. Floor of 30.
_MIN_POST_TASK20_CELL_COUNT: Final[int] = 30


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

def test_nb2_has_at_least_30_cells_post_task20(
    nb2: nbformat.NotebookNode,
) -> None:
    """NB2 has the post-Task-20 cell count floor."""
    assert len(nb2.cells) >= _MIN_POST_TASK20_CELL_COUNT, (
        f"NB2 has only {len(nb2.cells)} cells; Task 20 must add at "
        f"least {_MIN_POST_TASK20_CELL_COUNT - 27} new cells beyond "
        f"the 27-cell post-Task-19 state."
    )


def test_nb2_section7_has_code_cells(
    nb2: nbformat.NotebookNode,
) -> None:
    """§7 exists: at least one code cell tagged section:7 + remove-input."""
    s7_cells = _section_cells(nb2, SECTION7_TAG)
    s7_code = _code_cells(s7_cells)
    assert s7_code, (
        "§7 must contain at least one code cell (tagged section:7). "
        "Task 20 Step 3 must author §7."
    )
    for c in s7_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§7 code cell missing 'remove-input' tag; got {tags!r}."
        )


# ── §7 specification tests ────────────────────────────────────────────────

def test_nb2_section7_adds_ipp_regressor(
    nb2: nbformat.NotebookNode,
) -> None:
    """§7 source adds standardized ΔIPP as a co-regressor.

    Either a pre-computed ``ipp_std`` binding appears directly, or the
    §7 cell contains an inline standardization of ``dane_ipp_pct``
    (mean + std tokens co-present with the column reference).
    """
    s7_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION7_TAG))
    )
    has_ipp_ref = any(a in s7_code_src for a in _IPP_STD_ALIASES)
    assert has_ipp_ref, (
        f"§7 source must reference the ΔIPP column (any of "
        f"{_IPP_STD_ALIASES!r}). Plan Task 20 mandates standardized "
        f"ΔIPP as an additional regressor alongside cpi_surprise_ar1."
    )
    # If the direct ``ipp_std`` binding is not present, the source must
    # contain BOTH standardization tokens on the dane_ipp_pct series.
    if "ipp_std" not in s7_code_src:
        for token in _IPP_STANDARDIZATION_TOKENS:
            assert token in s7_code_src, (
                f"§7 source lacks a pre-computed ``ipp_std`` binding "
                f"AND lacks the inline standardization token {token!r}. "
                f"Standardization is load-bearing: β̂_PPI must be "
                f"directly comparable in magnitude to β̂_CPI."
            )


def test_nb2_section7_uses_hac4(
    nb2: nbformat.NotebookNode,
) -> None:
    """§7 refit uses HAC(4) — identical covariance spec as §3."""
    s7_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION7_TAG))
    )
    for token in _HAC4_TOKENS:
        assert token in s7_code_src, (
            f"§7 source must use HAC(4) covariance (token {token!r} "
            f"missing). Plan Task 20 mandates the identical covariance "
            f"mechanism as §3 Column 6 (Newey-West 1987 / ABDV 2003)."
        )
    # Confirm the maxlags=4 argument appears (not a different HAC lag).
    assert "maxlags" in s7_code_src and "4" in s7_code_src, (
        "§7 source must specify ``maxlags=4`` or ``'maxlags': 4`` — "
        "the same lag choice as §3."
    )


def test_nb2_section7_reports_beta_cpi_and_beta_ipp(
    nb2: nbformat.NotebookNode,
) -> None:
    """§7 reports both β̂_CPI and β̂_PPI coefficients from the refit."""
    s7_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION7_TAG))
    )
    # The refit must extract the cpi_surprise_ar1 coefficient (β̂_CPI).
    assert "cpi_surprise_ar1" in s7_code_src, (
        "§7 source must extract the cpi_surprise_ar1 coefficient "
        "(β̂_CPI). Plan Task 20 mandates both point estimates."
    )
    # And the ipp_std coefficient (β̂_PPI).
    assert "ipp_std" in s7_code_src, (
        "§7 source must extract the ipp_std coefficient (β̂_PPI). "
        "Plan Task 20 mandates both point estimates."
    )


def test_nb2_section7_reports_joint_covariance_block(
    nb2: nbformat.NotebookNode,
) -> None:
    """§7 reports the 2×2 joint HAC covariance block on {β̂_CPI, β̂_PPI}.

    The source must contain a ``cov_params()`` call whose subset
    references BOTH ``cpi_surprise_ar1`` and ``ipp_std`` — the 2×2
    block extraction pattern.
    """
    s7_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION7_TAG))
    )
    has_cov_params = any(t in s7_code_src for t in _COV_PARAMS_TOKENS)
    assert has_cov_params, (
        f"§7 source must call ``cov_params()`` (any of "
        f"{_COV_PARAMS_TOKENS!r}). Plan Task 20 mandates the joint "
        f"HAC covariance block."
    )
    # Both regressors must appear in the covariance-subset path.
    for token in _COV_BLOCK_SUBSET_TOKENS:
        assert token in s7_code_src, (
            f"§7 source must subset the covariance matrix on "
            f"{token!r}. Plan Task 20 mandates the 2×2 block on "
            f"{{cpi_surprise_ar1, ipp_std}}."
        )


def test_nb2_section7_interp_branches_on_channel_dominance(
    nb2: nbformat.NotebookNode,
) -> None:
    """§7 interpretation pre-registers BOTH dominance verdicts.

    Plan Task 20: "interpretation markdown branches on channel
    dominance (|β_CPI| > |β_PPI| → inflation-channel; else
    producer-cost-channel)". Both branch tokens must appear in the §7
    markdown so the verdict is pre-registered in source regardless of
    which one fires at runtime.
    """
    s7_md_src = "\n\n".join(
        _cell_source(c) for c in _markdown_cells(_section_cells(nb2, SECTION7_TAG))
    )
    has_cpi_branch = any(t in s7_md_src for t in _CHANNEL_DOMINANCE_TOKENS)
    assert has_cpi_branch, (
        f"§7 interp-md must pre-register the CPI-dominance branch "
        f"verdict (any of {_CHANNEL_DOMINANCE_TOKENS!r}). Plan Task "
        f"20 mandates explicit channel-dominance branching."
    )
    has_ppi_branch = any(t in s7_md_src for t in _PRODUCER_COST_TOKENS)
    assert has_ppi_branch, (
        f"§7 interp-md must pre-register the PPI-dominance branch "
        f"verdict (any of {_PRODUCER_COST_TOKENS!r}). Plan Task 20 "
        f"mandates explicit channel-dominance branching."
    )


def test_nb2_section7_compares_to_column6(
    nb2: nbformat.NotebookNode,
) -> None:
    """§7 compares the decomposition β̂_CPI to Column 6's β̂_CPI.

    Task 20 explicit ask: "Compare to Column 6's β̂_CPI = −0.000685:
    does the coefficient shift materially when IPP is added as a
    co-regressor?" Source (code OR interp-md) must reference either
    the fit handle (``column6_fit``) or cite Column 6 directly.
    """
    s7_all_src = "\n\n".join(
        _cell_source(c) for c in _section_cells(nb2, SECTION7_TAG)
    )
    has_col6_ref = any(t in s7_all_src for t in _COLUMN6_COMPARISON_TOKENS)
    assert has_col6_ref, (
        f"§7 must compare the decomposition β̂_CPI to Column 6's "
        f"β̂_CPI (any of {_COLUMN6_COMPARISON_TOKENS!r}). Plan Task "
        f"20 mandates the comparison to detect whether adding IPP "
        f"shifts the CPI coefficient materially."
    )


# ── Citation block tests ──────────────────────────────────────────────────

def test_nb2_section7_has_four_part_citation_block(
    nb2: nbformat.NotebookNode,
) -> None:
    """§7 carries at least one 4-part citation block markdown cell."""
    s7_md = _markdown_cells(_section_cells(nb2, SECTION7_TAG))
    citation_cells = [
        c
        for c in s7_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§7 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )


def test_nb2_section7_citation_block_references_conrad2025(
    nb2: nbformat.NotebookNode,
) -> None:
    """§7 citation block cites Conrad-Schoelkopf-Tushteva 2025."""
    s7_md_src = "\n\n".join(
        _cell_source(c) for c in _markdown_cells(_section_cells(nb2, SECTION7_TAG))
    )
    for bibkey in _SECTION7_BIBKEYS:
        assert bibkey in s7_md_src, (
            f"§7 citation block must reference bibkey {bibkey!r}. Plan "
            f"Task 20 mandates Conrad-Schoelkopf-Tushteva 2025 "
            f"(decomposition convention baseline)."
        )


# ── Citation lint passthrough ─────────────────────────────────────────────

def test_nb2_citation_lint_passes_after_task20() -> None:
    """``lint_notebook_citations.py`` exits 0 on NB2 after §7 authoring."""
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
        f"Expected lint exit 0 on NB2 post-Task-20; got "
        f"{result.returncode}.\nstdout:\n{result.stdout}\nstderr:\n"
        f"{result.stderr}"
    )
