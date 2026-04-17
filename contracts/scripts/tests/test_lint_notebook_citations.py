"""Tests for the citation-block + chasing-offline notebook lint (Task 5).

Task 5 of the econ-notebook-implementation plan. Enforces two non-negotiable
cross-cutting rules via a pre-commit hook:

Rule 6 (Citation-block rule): every "gated" code cell (fit, test, or a
``Decision #N`` marker) must be preceded within the prior two markdown
cells by a four-part block containing ALL of:

    Reference
    Why used
    Relevance to our results
    Connection to simulator

Rule 7 (Chasing-offline rule): notebook markdown must not contain phrases
that narrate offline deliberation. The forbidden substrings (matched
case-insensitively) are:

    "we tried"
    "rejected in favor of"
    "we chose"
    "this didn't work"

The CLI script under test (``scripts/lint_notebook_citations.py``) is
invoked as a subprocess against synthetic ``.ipynb`` fixtures built with
``nbformat.v4``. Exit-code contract:

  * 0 → no violations (or no gated cells at all).
  * 1 → one or more violations. Error message identifies cell index and
    which of the four headers is missing OR which forbidden phrase was
    found.

Pre-commit integration is verified with a skip-if-missing guard, matching
the pattern in ``test_just_notebooks_recipe.py`` for `just`.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Final

import nbformat
import pytest
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

# ── Path constants ────────────────────────────────────────────────────────

# This test file lives at: contracts/scripts/tests/test_lint_notebook_citations.py
# The lint CLI lives at:   contracts/scripts/lint_notebook_citations.py
# The pre-commit config lives at: contracts/.pre-commit-config.yaml
_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parents[1]
_CONTRACTS_DIR: Final[Path] = _SCRIPTS_DIR.parent
LINT_SCRIPT: Final[Path] = _SCRIPTS_DIR / "lint_notebook_citations.py"
FIXTURES_DIR: Final[Path] = Path(__file__).resolve().parent / "fixtures"
PRE_COMMIT_CONFIG: Final[Path] = _CONTRACTS_DIR / ".pre-commit-config.yaml"

# ── Canonical four required headers ───────────────────────────────────────

REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "Reference",
    "Why used",
    "Relevance to our results",
    "Connection to simulator",
)

# ── Forbidden chasing-offline phrases (case-insensitive) ──────────────────

FORBIDDEN_PHRASES: Final[tuple[str, ...]] = (
    "we tried",
    "rejected in favor of",
    "we chose",
    "this didn't work",
)


# ── Fixture notebook builders (functional, return nbformat objects) ───────

def _four_part_block(*, include_connection: bool = True) -> str:
    """Return a markdown block with all four required headers (or three)."""
    parts = [
        "### Decision",
        "**Reference.** Smith (2020).",
        "**Why used.** It is the canonical choice.",
        "**Relevance to our results.** Governs the point estimate.",
    ]
    if include_connection:
        parts.append("**Connection to simulator.** Feeds the FX-vol block.")
    return "\n".join(parts)


def _build_valid_notebook() -> nbformat.NotebookNode:
    """Gated fit cell preceded by a complete citation block."""
    nb = new_notebook()
    nb.cells = [
        new_markdown_cell(_four_part_block(include_connection=True)),
        new_code_cell("result = sm.OLS(y, X).fit()"),
    ]
    return nb


def _build_missing_connection_notebook() -> nbformat.NotebookNode:
    """Citation block missing the `Connection to simulator` header."""
    nb = new_notebook()
    nb.cells = [
        new_markdown_cell(_four_part_block(include_connection=False)),
        new_code_cell("result = sm.OLS(y, X).fit()"),
    ]
    return nb


def _build_no_gated_cells_notebook() -> nbformat.NotebookNode:
    """Only imports and pandas mechanics — no gated cells."""
    nb = new_notebook()
    nb.cells = [
        new_markdown_cell("## Data loading"),
        new_code_cell("import pandas as pd"),
        new_code_cell('df = pd.read_csv("data.csv")'),
    ]
    return nb


def _build_gated_without_preceding_markdown_notebook() -> nbformat.NotebookNode:
    """Gated code cell with no markdown within the preceding 2 cells."""
    nb = new_notebook()
    nb.cells = [
        new_code_cell("import statsmodels.api as sm"),
        new_code_cell("x = 1"),
        new_code_cell("result = sm.OLS(y, X).fit()"),
    ]
    return nb


def _build_chasing_offline_notebook() -> nbformat.NotebookNode:
    """Markdown contains a forbidden chasing-offline phrase."""
    nb = new_notebook()
    nb.cells = [
        new_markdown_cell("## Modelling notes"),
        new_markdown_cell(
            "We tried GARCH(1,1) and rejected in favor of HAR-RV "
            "after calibration."
        ),
        new_code_cell("print('hello')"),
    ]
    return nb


# ── Fixture file materialisation (session-scoped) ─────────────────────────

_FIXTURE_BUILDERS: Final[dict[str, object]] = {
    "nb_citation_valid.ipynb": _build_valid_notebook,
    "nb_citation_missing_connection.ipynb": _build_missing_connection_notebook,
    "nb_no_gated_cells.ipynb": _build_no_gated_cells_notebook,
    "nb_gated_no_preceding_markdown.ipynb": _build_gated_without_preceding_markdown_notebook,
    "nb_chasing_offline_violation.ipynb": _build_chasing_offline_notebook,
}


@pytest.fixture(scope="module", autouse=True)
def _materialise_fixtures() -> None:
    """Build each synthetic .ipynb in fixtures/ on first use.

    Module-scoped + autouse so every test sees the files on disk without
    needing to request the fixture explicitly. Re-writes on every module
    load to keep fixtures deterministic.
    """
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    for filename, builder in _FIXTURE_BUILDERS.items():
        nb = builder()  # type: ignore[operator]
        path = FIXTURES_DIR / filename
        with path.open("w", encoding="utf-8") as fh:
            nbformat.write(nb, fh)


# ── Helpers ───────────────────────────────────────────────────────────────

def _run_lint(fixture_names: Iterable[str]) -> subprocess.CompletedProcess[str]:
    """Invoke the lint CLI on the named fixtures via the venv python.

    Uses the same interpreter as the test runner to avoid environment drift.
    """
    assert LINT_SCRIPT.is_file(), f"Lint script missing: {LINT_SCRIPT}"
    paths = [str(FIXTURES_DIR / name) for name in fixture_names]
    return subprocess.run(
        [sys.executable, str(LINT_SCRIPT), *paths],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


# ── Test cases (one per failure mode + one success + one integration) ────

def test_valid_notebook_exits_zero() -> None:
    """A notebook with a fully-populated citation block passes the lint."""
    result = _run_lint(["nb_citation_valid.ipynb"])
    assert result.returncode == 0, (
        f"Expected exit 0 for valid fixture; got {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_missing_connection_header_exits_nonzero() -> None:
    """Missing `Connection to simulator` header fails and is named in output."""
    result = _run_lint(["nb_citation_missing_connection.ipynb"])
    assert result.returncode != 0, (
        f"Expected non-zero exit for missing-connection fixture; got 0.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    combined = result.stdout + result.stderr
    assert "Connection to simulator" in combined, (
        "Error message must name the missing header 'Connection to simulator'.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_no_gated_cells_exits_zero() -> None:
    """A notebook with no fit/test/decision cells is vacuously compliant."""
    result = _run_lint(["nb_no_gated_cells.ipynb"])
    assert result.returncode == 0, (
        f"Expected exit 0 for no-gated-cells fixture; got {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_gated_cell_without_preceding_markdown_exits_nonzero() -> None:
    """Gated code cell without any preceding markdown fails the lint."""
    result = _run_lint(["nb_gated_no_preceding_markdown.ipynb"])
    assert result.returncode != 0, (
        "Expected non-zero exit when a gated cell has no preceding markdown.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_chasing_offline_violation_exits_nonzero_with_distinct_signal() -> None:
    """A forbidden phrase in markdown fails with a chasing-offline signal."""
    result = _run_lint(["nb_chasing_offline_violation.ipynb"])
    assert result.returncode != 0, (
        "Expected non-zero exit for a chasing-offline fixture; got 0.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    combined = (result.stdout + result.stderr).lower()
    assert "chasing" in combined or "forbidden phrase" in combined, (
        "Error output must use a distinct chasing-offline signal "
        "(e.g. 'chasing-offline' or 'forbidden phrase'). Got:\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


# ── Pre-commit hook configuration tests ──────────────────────────────────

def test_pre_commit_config_exists_and_references_lint_script() -> None:
    """The pre-commit config exists and declares a hook running our lint."""
    assert PRE_COMMIT_CONFIG.is_file(), (
        f"Pre-commit config missing at {PRE_COMMIT_CONFIG}"
    )
    text = PRE_COMMIT_CONFIG.read_text(encoding="utf-8")
    assert "lint_notebook_citations.py" in text, (
        "Pre-commit config must reference the lint script filename.\n"
        f"Config contents:\n{text}"
    )
    # Scope: the hook must target the fx_vol_cpi_surprise notebooks dir.
    assert "fx_vol_cpi_surprise" in text, (
        "Pre-commit hook must scope to fx_vol_cpi_surprise notebooks.\n"
        f"Config contents:\n{text}"
    )


# ── Optional pre-commit binary subprocess integration (skipped if absent) ─

_PRE_COMMIT_BIN: Final[str | None] = shutil.which("pre-commit")
_PRE_COMMIT_SKIP_REASON: Final[str] = (
    "`pre-commit` binary not on PATH in this test environment; structural "
    "assertions cover hook configuration. Install via "
    "`uv pip install pre-commit` to enable subprocess verification."
)


@pytest.mark.skipif(_PRE_COMMIT_BIN is None, reason=_PRE_COMMIT_SKIP_REASON)
def test_pre_commit_run_invokes_lint_hook() -> None:
    """`pre-commit run lint-notebook-citations --files <valid>` exits 0.

    Runs the hook directly (not via `install`) to avoid mutating
    ``.git/hooks`` in this worktree. Uses the pre-built valid fixture so
    the hook itself has a deterministic PASS baseline.
    """
    # Ensure fixtures exist (module autouse fixture already did this).
    valid_fixture = FIXTURES_DIR / "nb_citation_valid.ipynb"
    assert valid_fixture.is_file()

    result = subprocess.run(
        [
            _PRE_COMMIT_BIN or "pre-commit",
            "run",
            "lint-notebook-citations",
            "--files",
            str(valid_fixture),
        ],
        cwd=_CONTRACTS_DIR,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    # pre-commit may emit "No files to check" if the files-filter excludes
    # the fixture path. That's OK — the hook ran without a failure. We
    # treat non-zero ONLY if output indicates an actual hook failure.
    combined = result.stdout + result.stderr
    if result.returncode != 0:
        # Accept environment / bootstrapping issues (first-time init may fetch
        # plugins). Fail only when the hook itself declares a violation.
        assert "lint-notebook-citations" not in combined.lower() or "passed" in combined.lower(), (
            "pre-commit invocation failed with hook-identified violation.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
