"""Structural regression tests for NB2 §6 GARCH(1,1)-X co-primary.

Task 19 of the econ-notebook-implementation plan. NB2 §6 is the
co-primary specification alongside the weekly §3 linear OLS — it
operates at DAILY frequency on COP/USD log-returns, and it tests
whether the CPI-surprise shock enters the VARIANCE equation (not the
mean). The specification per plan Task 19 + spec Rev 4 §3:

    r_t = μ + ε_t,  ε_t = σ_t z_t,  z_t ~ i.i.d. (Normal or Student-t)
    σ_t² = ω + α₁ ε_{t-1}² + β₁ σ_{t-1}² + δ · |s_t^CPI|

where ``|s_t^CPI|`` is the absolute value of the daily CPI surprise
regressor (Han-Kristensen 2014 JBES convention — the absolute-value
transformation is load-bearing, NOT signed surprise). The fit uses
BFGS with a 500-iteration ceiling plus a Hessian positive-definiteness
check at the optimum. Output must include the five variance-equation
parameters (ω, α₁, β₁, δ, plus ν if Student-t), log-likelihood,
persistence α₁ + β₁, standardized-residual and conditional-volatility
series, iterations-used count, and Hessian-PD status. A Jarque-Bera
test on the standardized residuals is run and, if it rejects, the
Bollerslev-Wooldridge 1992 QMLE standard errors are explicitly
surfaced in the notebook cell output (not the scratch log).

This module is authored TDD-first: it fails against the 24-cell
post-Task-18 NB2 and turns green once the Analytics Reporter appends
§6's trio.

What gets asserted:

  1. §6 loads the DAILY panel (not weekly) — Decision #3 A1-sensitivity
     scope per plan Task 19.
  2. §6 uses the absolute-value CPI-surprise regressor (Han-Kristensen
     2014 convention) — source contains ``abs_cpi_surprise`` or
     ``np.abs(`` / ``.abs()`` applied to a CPI-surprise column.
  3. §6 fits GARCH(1,1) — source contains ``p=1`` and ``q=1`` tokens
     in conjunction with a GARCH specification.
  4. §6 uses the BFGS optimizer (via scipy.optimize.minimize with
     method='BFGS' or 'L-BFGS-B' — Quasi-Newton family).
  5. §6 enforces a 500-iter ceiling — source contains ``maxiter=500``
     or ``max_iter=500``.
  6. §6 reports all required output fields: ω (omega), α₁ (alpha),
     β₁ (beta), δ (delta), log-likelihood, persistence, iterations,
     Hessian-PD status, standardized-residual series, conditional
     volatility series.
  7. §6 performs a live Hessian positive-definiteness check — source
     contains ``eigvalsh`` or ``eig`` on an inverse-Hessian / Hessian
     object with a PD verdict assignment.
  8. §6 runs Jarque-Bera on standardized residuals.
  9. §6 surfaces the QMLE-SE fallback in the notebook cell if JB
     rejects — source contains a code path that emits robust /
     Bollerslev-Wooldridge 1992 standard errors.
 10. §6 citation block references Bollerslev 1986 + Han-Kristensen
     2014 JBES + Bollerslev-Wooldridge 1992 bibkeys.
 11. Structural tags: every §6 code cell carries ``remove-input`` and
     ``section:6``.
 12. Citation lint: ``scripts/lint_notebook_citations.py`` exits 0.

What is NOT asserted:
  * Exact wording of prose interpretations.
  * Exact values of δ̂, ω̂, α̂, β̂, or the JB p-value (OUTPUTS reported
    in Task 19 final message, not the test file).
  * Specific implementation library for the GARCH-X custom fit
    (scipy-level manual likelihood is expected because arch 8.0.0 does
    not support exogenous variance regressors natively; the test does
    NOT lock to arch_model's high-level API because the high-level API
    cannot express exogenous variance regressors).
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

SECTION6_TAG: Final[str] = "section:6"
REMOVE_INPUT_TAG: Final[str] = "remove-input"

REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# Daily-panel load landmarks — §6 must reach the daily panel via the
# cleaned-panel loader (primary path) or a direct reference to the
# ``.daily`` attribute on the CleanedPanel result object.
_DAILY_PANEL_ALIASES: Final[tuple[str, ...]] = (
    "cleaned.daily",
    "cp.daily",
    "panel.daily",
    ".daily",
)

# Absolute-value CPI-surprise regressor (Han-Kristensen 2014 convention)
# — the cleaning layer pre-computes an ``abs_cpi_surprise`` column on
# the daily panel (verified via schema introspection). Accept that
# column reference OR an in-cell ``np.abs(...)`` / ``.abs()`` call
# applied to a CPI-surprise column.
_ABS_CPI_ALIASES: Final[tuple[str, ...]] = (
    "abs_cpi_surprise",
    "np.abs(cpi",
    ".abs()",
    "|s_t",
)

# GARCH(1,1) specification tokens. arch.arch_model uses p=1, q=1.
# A custom scipy implementation may use ``p=1`` + ``q=1`` in parameter
# count, or explicit ``alpha`` + ``beta`` single-lag variables.
_GARCH_P1_Q1_TOKENS: Final[tuple[str, ...]] = (
    "p=1",
    "GARCH(1",  # GARCH(1,1) in comments / labels
    "alpha",    # single-lag ARCH coefficient
)
_GARCH_Q1_TOKEN: Final[str] = "q=1"
_GARCH_BETA_TOKEN: Final[str] = "beta"

# BFGS optimizer — scipy.optimize.minimize with method='BFGS' or
# 'L-BFGS-B' (Quasi-Newton family, per plan Task 19).
_BFGS_ALIASES: Final[tuple[str, ...]] = (
    "method='BFGS'",
    'method="BFGS"',
    "method='L-BFGS-B'",
    'method="L-BFGS-B"',
    "BFGS",
)

# 500-iter ceiling tokens.
_MAXITER_500_ALIASES: Final[tuple[str, ...]] = (
    "maxiter=500",
    "max_iter=500",
    "'maxiter': 500",
    '"maxiter": 500',
)

# Hessian PD check — source must compute eigenvalues of the inverse
# Hessian (or Hessian) at the optimum and decide positive definiteness.
_HESSIAN_PD_ALIASES: Final[tuple[str, ...]] = (
    "eigvalsh",
    "eigvals",
    "hessian_pd",
    "hess_inv",
)

# Jarque-Bera on standardized residuals.
_JARQUE_BERA_ALIASES: Final[tuple[str, ...]] = (
    "jarque_bera",
    "jb_test",
    "JarqueBera",
)

# QMLE / Bollerslev-Wooldridge robust-SE fallback — surfaced in the
# cell output when JB rejects. Accept any of:
#   * ``cov_type='robust'`` (arch convention)
#   * ``qmle`` token
#   * ``bollerslev_wooldridge`` / ``bollerslevWooldridge``
#   * explicit sandwich-formula ``A^{-1} B A^{-1}``
_QMLE_ALIASES: Final[tuple[str, ...]] = (
    "qmle",
    "QMLE",
    "cov_type='robust'",
    'cov_type="robust"',
    "bollerslev",
    "sandwich",
    "robust_se",
    "robust SE",
)

# Required output field tokens — every listed token must appear in the
# §6 source (as a variable name, dict key, or printout label).
_REQUIRED_OUTPUT_FIELDS: Final[tuple[str, ...]] = (
    "omega",            # ω
    "alpha",            # α₁
    "beta",             # β₁
    "delta",            # δ (coefficient on |s_t^CPI|)
    "log_likelihood",   # ℓ — also accepts "loglik", handled below
    "persistence",      # α₁ + β₁
    "iterations",       # iterations used
)

# Standardized-residual series — accept ``std_resid`` (arch library
# convention) or ``standardized_residuals``.
_STD_RESID_ALIASES: Final[tuple[str, ...]] = (
    "std_resid",
    "standardized_residual",
    "z_hat",
)

# Conditional-volatility series — accept ``conditional_vol``,
# ``cond_vol``, ``conditional_volatility``, or ``sigma``.
_COND_VOL_ALIASES: Final[tuple[str, ...]] = (
    "conditional_vol",
    "cond_vol",
    "conditional_volatility",
    "sigma_t",
    "sigma2",
)

# Citation bibkeys.
_SECTION6_BIBKEYS: Final[tuple[str, ...]] = (
    "bollerslev1986generalized",
    "hanKristensen2014garch",
    "bollerslevWooldridge1992qmle",
)

# After Task 18 NB2 has 24 cells. Task 19 §6 appends a minimum of one
# (why-md, code, interp-md) trio → ≥3 new cells. Floor of 27.
_MIN_POST_TASK19_CELL_COUNT: Final[int] = 27


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

def test_nb2_has_at_least_27_cells_post_task19(
    nb2: nbformat.NotebookNode,
) -> None:
    """NB2 has the post-Task-19 cell count floor."""
    assert len(nb2.cells) >= _MIN_POST_TASK19_CELL_COUNT, (
        f"NB2 has only {len(nb2.cells)} cells; Task 19 must add at "
        f"least {_MIN_POST_TASK19_CELL_COUNT - 24} new cells beyond "
        f"the 24-cell post-Task-18 state."
    )


def test_nb2_section6_has_code_cells(
    nb2: nbformat.NotebookNode,
) -> None:
    """§6 exists: at least one code cell tagged section:6 + remove-input."""
    s6_cells = _section_cells(nb2, SECTION6_TAG)
    s6_code = _code_cells(s6_cells)
    assert s6_code, (
        "§6 must contain at least one code cell (tagged section:6). "
        "Task 19 Step 3 must author §6."
    )
    for c in s6_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§6 code cell missing 'remove-input' tag; got {tags!r}."
        )


# ── §6 specification tests ────────────────────────────────────────────────

def test_nb2_section6_uses_daily_not_weekly(
    nb2: nbformat.NotebookNode,
) -> None:
    """§6 loads the daily panel — Decision #3 A1-sensitivity scope.

    Plan Task 19 mandates GARCH(1,1)-X on daily COP/USD returns.
    Source must reference the ``.daily`` attribute on the CleanedPanel
    result (or equivalent cp.daily / cleaned.daily access path).
    """
    s6_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION6_TAG))
    )
    assert any(a in s6_code_src for a in _DAILY_PANEL_ALIASES), (
        f"§6 source must load the daily panel (any of "
        f"{_DAILY_PANEL_ALIASES!r}). Plan Task 19 mandates daily "
        f"frequency for the GARCH(1,1)-X co-primary — this is the "
        f"Decision #3 A1-sensitivity scope complement to the weekly §3 "
        f"linear OLS."
    )


def test_nb2_section6_uses_abs_cpi_surprise(
    nb2: nbformat.NotebookNode,
) -> None:
    """§6 uses |s_t^CPI| — Han-Kristensen 2014 JBES convention.

    The absolute-value transformation of the CPI surprise is
    load-bearing, NOT signed surprise. Source must reference the
    pre-computed ``abs_cpi_surprise`` column on the daily panel OR
    an explicit ``np.abs(...)`` / ``.abs()`` call.
    """
    s6_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION6_TAG))
    )
    assert any(a in s6_code_src for a in _ABS_CPI_ALIASES), (
        f"§6 source must use the absolute-value CPI-surprise regressor "
        f"(any of {_ABS_CPI_ALIASES!r}). Han-Kristensen 2014 JBES "
        f"specifies |s_t|, not signed s_t, for the variance-equation "
        f"exogenous regressor."
    )


def test_nb2_section6_garch_p1_q1(
    nb2: nbformat.NotebookNode,
) -> None:
    """§6 specifies GARCH(1,1) — p=1 and q=1 (or equivalent)."""
    s6_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION6_TAG))
    )
    # Accept any GARCH(1,1) indicator — direct token, or explicit
    # alpha + beta single-lag variables.
    has_p_spec = any(t in s6_code_src for t in _GARCH_P1_Q1_TOKENS)
    assert has_p_spec, (
        f"§6 source must specify p=1 (or GARCH(1,1) or single-lag "
        f"alpha). Plan Task 19 mandates GARCH(1,1). Searched: "
        f"{_GARCH_P1_Q1_TOKENS!r}."
    )
    # q=1 or beta lag-1 coefficient.
    has_q_spec = (
        _GARCH_Q1_TOKEN in s6_code_src
        or _GARCH_BETA_TOKEN in s6_code_src
    )
    assert has_q_spec, (
        f"§6 source must specify q=1 (or single-lag beta). Plan Task "
        f"19 mandates GARCH(1,1)."
    )


def test_nb2_section6_bfgs_optimizer(
    nb2: nbformat.NotebookNode,
) -> None:
    """§6 uses BFGS optimizer."""
    s6_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION6_TAG))
    )
    assert any(a in s6_code_src for a in _BFGS_ALIASES), (
        f"§6 source must specify BFGS optimizer (any of "
        f"{_BFGS_ALIASES!r}). Plan Task 19 mandates BFGS with "
        f"500-iter ceiling."
    )


def test_nb2_section6_500_iter_ceiling(
    nb2: nbformat.NotebookNode,
) -> None:
    """§6 enforces a 500-iteration ceiling."""
    s6_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION6_TAG))
    )
    assert any(a in s6_code_src for a in _MAXITER_500_ALIASES), (
        f"§6 source must set maxiter=500 (any of "
        f"{_MAXITER_500_ALIASES!r}). Plan Task 19 mandates 500-iter "
        f"ceiling."
    )


def test_nb2_section6_has_hessian_pd_check(
    nb2: nbformat.NotebookNode,
) -> None:
    """§6 performs a live Hessian positive-definiteness check.

    Source must compute eigenvalues of the (inverse) Hessian at the
    optimum and derive a PD verdict. ``eigvalsh`` or ``eigvals`` on
    ``hess_inv`` (scipy.optimize result) is the canonical pattern.
    """
    s6_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION6_TAG))
    )
    assert any(a in s6_code_src for a in _HESSIAN_PD_ALIASES), (
        f"§6 source must perform a live Hessian PD check (any of "
        f"{_HESSIAN_PD_ALIASES!r}). Plan Task 19 Step 3.5 mandates "
        f"the PD check is not commented out."
    )


def test_nb2_section6_reports_all_required_parameters(
    nb2: nbformat.NotebookNode,
) -> None:
    """§6 reports ω, α₁, β₁, δ, log-lik, persistence, iterations."""
    s6_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION6_TAG))
    )
    for field in _REQUIRED_OUTPUT_FIELDS:
        if field == "log_likelihood":
            # Accept any of log_likelihood / loglik / log-lik / llf.
            has_loglik = (
                "log_likelihood" in s6_code_src
                or "loglik" in s6_code_src
                or "log-lik" in s6_code_src
                or "llf" in s6_code_src
                or "log-likelihood" in s6_code_src
            )
            assert has_loglik, (
                "§6 source must report the log-likelihood (log_likelihood / "
                "loglik / log-lik / llf). Plan Task 19 mandates log-lik "
                "in the output field set."
            )
        else:
            assert field in s6_code_src, (
                f"§6 source must report {field!r}. Plan Task 19 mandates "
                f"all of: ω (omega), α₁ (alpha), β₁ (beta), δ (delta), "
                f"log-likelihood, persistence, iterations."
            )


def test_nb2_section6_has_standardized_residuals(
    nb2: nbformat.NotebookNode,
) -> None:
    """§6 emits a standardized-residual series."""
    s6_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION6_TAG))
    )
    assert any(a in s6_code_src for a in _STD_RESID_ALIASES), (
        f"§6 source must emit a standardized-residual series (any of "
        f"{_STD_RESID_ALIASES!r}). Plan Task 19 mandates the series "
        f"in the output field set."
    )


def test_nb2_section6_has_conditional_volatility(
    nb2: nbformat.NotebookNode,
) -> None:
    """§6 emits a conditional-volatility series."""
    s6_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION6_TAG))
    )
    assert any(a in s6_code_src for a in _COND_VOL_ALIASES), (
        f"§6 source must emit a conditional-volatility series (any of "
        f"{_COND_VOL_ALIASES!r}). Plan Task 19 mandates the series "
        f"in the output field set."
    )


def test_nb2_section6_has_jb_on_std_residuals(
    nb2: nbformat.NotebookNode,
) -> None:
    """§6 runs Jarque-Bera on standardized residuals."""
    s6_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION6_TAG))
    )
    assert any(a in s6_code_src for a in _JARQUE_BERA_ALIASES), (
        f"§6 source must run Jarque-Bera on standardized residuals "
        f"(any of {_JARQUE_BERA_ALIASES!r}). Plan Task 19 mandates "
        f"the JB test with QMLE-SE fallback if it rejects."
    )


def test_nb2_section6_qmle_fallback_surfaced_if_jb_rejects(
    nb2: nbformat.NotebookNode,
) -> None:
    """§6 surfaces QMLE-SE fallback in the notebook cell.

    Plan Task 19: 'explicit QMLE-SE fallback surfaced in the notebook
    cell (not scratch) if JB rejects'. The §6 code must contain a
    reference to QMLE / robust / Bollerslev-Wooldridge 1992 SE
    computation. This test passes whether or not JB actually rejects
    at runtime — the code path must exist in source either way
    (pre-registered) so a post-hoc JB rejection does not require code
    edits.
    """
    s6_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION6_TAG))
    )
    assert any(a in s6_code_src for a in _QMLE_ALIASES), (
        f"§6 source must contain a QMLE / Bollerslev-Wooldridge 1992 "
        f"robust-SE code path (any of {_QMLE_ALIASES!r}). Plan Task 19 "
        f"mandates the QMLE-SE fallback is surfaced in the notebook "
        f"cell (not scratch) if JB rejects — the fallback must be "
        f"pre-registered in source so a runtime JB rejection does not "
        f"require code edits."
    )


# ── Citation block tests ──────────────────────────────────────────────────

def test_nb2_section6_has_four_part_citation_block(
    nb2: nbformat.NotebookNode,
) -> None:
    """§6 carries at least one 4-part citation block markdown cell."""
    s6_md = _markdown_cells(_section_cells(nb2, SECTION6_TAG))
    citation_cells = [
        c
        for c in s6_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§6 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )


def test_nb2_section6_citation_block(
    nb2: nbformat.NotebookNode,
) -> None:
    """§6 citation block cites Bollerslev 1986 + Han-Kristensen 2014 + BW 1992."""
    s6_md_src = "\n\n".join(
        _cell_source(c) for c in _markdown_cells(_section_cells(nb2, SECTION6_TAG))
    )
    for bibkey in _SECTION6_BIBKEYS:
        assert bibkey in s6_md_src, (
            f"§6 citation block must reference bibkey {bibkey!r}. Plan "
            f"Task 19 mandates Bollerslev 1986 (original GARCH), "
            f"Han-Kristensen 2014 JBES (GARCH-X QMLE + |s_t| "
            f"convention), and Bollerslev-Wooldridge 1992 (QMLE-SE "
            f"fallback)."
        )


# ── Citation lint passthrough ─────────────────────────────────────────────

def test_nb2_citation_lint_passes_after_task19() -> None:
    """``lint_notebook_citations.py`` exits 0 on NB2 after §6 authoring."""
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
        f"Expected lint exit 0 on NB2 post-Task-19; got "
        f"{result.returncode}.\nstdout:\n{result.stdout}\nstderr:\n"
        f"{result.stderr}"
    )
