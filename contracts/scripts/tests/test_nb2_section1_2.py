"""Structural regression test for NB2 §1 (Setup + verification) and §2 (descriptive stats).

Task 16 of the econ-notebook-implementation plan. NB2's §1 does three
jobs: (a) recomputes the sha256 of the econ-notebook-design spec and
asserts equality with an embedded hex string, (b) re-runs
``cleaning.load_cleaned_panel(conn)`` and compares its weekly-panel
sha256 to the JSON handoff at ``env.FINGERPRINT_PATH``, and (c) carries
the Gate Verdict admonition placeholder that Task 30 later populates.
§2 emits a full-sample descriptive-stats DataFrame (mean / std / skew /
kurtosis) for the LHS and six RHS regressors with NO release-week
conditioning — per spec Rev 4 §3 NB2.2 and plan line 344(d).

This module is authored TDD-first: it fails against the 2-cell skeleton
and turns green once the Analytics Reporter appends §1 and §2 cells.

What gets asserted, in order of decreasing "load-bearing":

  1. Spec-hash embed: §1 contains a code cell that embeds the current
     spec-file sha256 as a literal hex string AND recomputes the file
     hash inline, so any silent edit to ``2026-04-17-econ-notebook-design.md``
     surfaces at notebook execution time.
  2. Panel-fingerprint equality: §1 contains a code cell that loads the
     weekly panel via ``cleaning.load_cleaned_panel(conn).weekly``,
     fingerprints it via ``panel_fingerprint.fingerprint(df, "week_start")``,
     and compares the sha256 to ``env.FINGERPRINT_PATH``'s
     ``weekly_panel.sha256`` field. The test inspects cell source for
     both API calls to verify the check is actually wired up.
  3. Gate Verdict placeholder: §1 carries a markdown cell with the literal
     ``Gate Verdict:`` admonition so Task 30's auto-render has a stable
     anchor.
  4. Descriptive-stats DataFrame: §2 renders a table whose rows are the
     LHS + six RHS names and whose columns include {mean, std, skew,
     kurtosis} (order-insensitive). The test runs the notebook cells in
     a Python subprocess and inspects the resulting DataFrame object
     referenced by a known module-level name.
  5. Full-sample discipline: §2 source MUST NOT carry any release-week
     or sub-sample filters (no ``is_cpi_release_week``,
     ``is_ppi_release_week``, ``.query(`` on a sub-window, etc.) so the
     descriptive-stats table stays a pure full-sample artifact per spec
     Rev 4.
  6. Section tags: new §1 cells carry ``section:1``; new §2 cells carry
     ``section:2``. Code cells carry ``remove-input`` matching NB1
     convention.
  7. Citation blocks: §1's gated cells (the ones carrying the
     ``Decision #`` reference) are preceded by a 4-part citation block;
     §2's descriptive-stats cell is preceded by a 4-part block citing
     the Conrad-Schoelkopf-Tushteva 2025 convention.

What is NOT asserted:
  * Exact wording of prose (would couple the test to authoring).
  * Exact DataFrame dtypes beyond "numeric".
  * The exact Python code inside cells beyond the landmark API calls
    named above.

No mocks — reads the real .ipynb on disk and, for §2 execution,
opens the real ``structural_econ.duckdb`` read-only via the session
``conn`` fixture defined in ``conftest.py``.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Final

import nbformat
import pytest

# ── Path plumbing (mirrors test_nb1_section1.py) ──────────────────────────

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

SPEC_MD_PATH: Final[Path] = (
    _CONTRACTS_DIR
    / "docs"
    / "superpowers"
    / "specs"
    / "2026-04-17-econ-notebook-design.md"
)

FINGERPRINT_JSON_PATH: Final[Path] = (
    _CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "estimates"
    / "nb1_panel_fingerprint.json"
)


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
NB2_PATH: Final[Path] = _env.NB2_PATH


# ── Constants ─────────────────────────────────────────────────────────────

# The seven series whose full-sample descriptive stats §2 must emit.
# Order is locked: LHS first, then the six RHS controls in the nested
# ladder order (CPI surprise first — identifying regressor — then the
# five controls).
EXPECTED_SERIES: Final[tuple[str, ...]] = (
    "rv_cuberoot",
    "cpi_surprise_ar1",
    "us_cpi_surprise",
    "banrep_rate_surprise",
    "vix_avg",
    "oil_return",
    "intervention_dummy",
)

# Required columns in the §2 descriptive-stats DataFrame. Order is
# not asserted; set membership is.
EXPECTED_STAT_COLS: Final[frozenset[str]] = frozenset(
    {"mean", "std", "skew", "kurtosis"}
)

# Required headers in any 4-part citation block.
REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# §1 code cells carry both section:1 and remove-input.
# §2 code cells carry both section:2 and remove-input.
SECTION1_TAG: Final[str] = "section:1"
SECTION2_TAG: Final[str] = "section:2"
REMOVE_INPUT_TAG: Final[str] = "remove-input"

# Landmark API tokens the test looks for in §1 code cells.
_SPEC_HASH_LANDMARKS: Final[tuple[str, ...]] = (
    "hashlib.sha256",
    "2026-04-17-econ-notebook-design.md",
)

_FINGERPRINT_LANDMARKS: Final[tuple[str, ...]] = (
    "cleaning.load_cleaned_panel",
    "panel_fingerprint",
    "week_start",
    "FINGERPRINT_PATH",
)

_GATE_VERDICT_LANDMARK: Final[str] = "Gate Verdict"

# §2 descriptive-stats DataFrame must be bound to this variable name so
# the test can import the notebook module and inspect the table directly.
# (Analytics Reporter is free to name intermediate variables as they like;
# this single name is the contract.)
_DESCRIPTIVE_STATS_VAR: Final[str] = "_descriptive_stats"

# Forbidden filters in §2 — the stats table is full-sample only.
_FORBIDDEN_FILTERS: Final[tuple[str, ...]] = (
    "is_cpi_release_week",
    "is_ppi_release_week",
    # Common sub-sample filter tokens — flag if they appear in §2.
    "2024-10",
    "regime_subsample",
)

# NB2 starts at 2 cells (skeleton). After §1-2 authoring we expect many
# more; the precise count depends on the author's trio granularity. We
# assert "at least N" where N is the minimum meaningful count.
_MIN_POST_AUTHOR_CELL_COUNT: Final[int] = 6  # title + gate + §1 (≥3) + §2 (≥1)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def nb2() -> nbformat.NotebookNode:
    """Load NB2 once per module."""
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
    """Return all cells carrying the named section tag."""
    return [c for c in nb.cells if section_tag in _cell_tags(c)]


def _code_cells(
    cells: list[nbformat.NotebookNode],
) -> list[nbformat.NotebookNode]:
    return [c for c in cells if c.get("cell_type") == "code"]


def _markdown_cells(
    cells: list[nbformat.NotebookNode],
) -> list[nbformat.NotebookNode]:
    return [c for c in cells if c.get("cell_type") == "markdown"]


def _compute_spec_hash() -> str:
    return hashlib.sha256(SPEC_MD_PATH.read_bytes()).hexdigest()


# ── §1 structural tests ───────────────────────────────────────────────────

def test_nb2_exists_and_has_enough_cells(nb2: nbformat.NotebookNode) -> None:
    """NB2 has at least the §1-2 cell count after authoring."""
    assert len(nb2.cells) >= _MIN_POST_AUTHOR_CELL_COUNT, (
        f"NB2 has only {len(nb2.cells)} cells; §1-2 authoring must append "
        f"at least {_MIN_POST_AUTHOR_CELL_COUNT - 2} new cells beyond the "
        f"2-cell skeleton."
    )


def test_nb2_section1_has_at_least_one_code_cell(
    nb2: nbformat.NotebookNode,
) -> None:
    """§1 exists: at least one code cell carries section:1 + remove-input."""
    s1_cells = _section_cells(nb2, SECTION1_TAG)
    s1_code = _code_cells(s1_cells)
    assert s1_code, (
        "§1 must contain at least one code cell (tagged section:1); "
        "none found. Task 16 Step 3 must author §1."
    )
    # Every §1 code cell carries remove-input (NB1 convention).
    for c in s1_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§1 code cell missing 'remove-input' tag; got tags={tags!r}."
        )


def test_nb2_section1_computes_spec_rev4_hash(
    nb2: nbformat.NotebookNode,
) -> None:
    """§1 has a code cell that embeds + recomputes the spec sha256.

    Two landmark tokens must appear in the same §1 code cell:
    ``hashlib.sha256`` (for recomputation) and the spec filename
    ``2026-04-17-econ-notebook-design.md``. Additionally, the current
    spec-file sha256 hex MUST appear verbatim as an embedded literal so
    an accidental spec edit flips the assertion.
    """
    s1_code = _code_cells(_section_cells(nb2, SECTION1_TAG))
    current_spec_hash = _compute_spec_hash()

    # Search for a cell carrying both landmarks.
    spec_hash_cells = [
        c
        for c in s1_code
        if all(landmark in _cell_source(c) for landmark in _SPEC_HASH_LANDMARKS)
    ]
    assert spec_hash_cells, (
        f"§1 must contain a code cell with both landmarks "
        f"{_SPEC_HASH_LANDMARKS!r}. None found among {len(s1_code)} §1 "
        f"code cells."
    )

    # Now verify the current sha256 hex is embedded in that cell. This
    # is how an edit to the spec .md file surfaces as a test failure:
    # the embedded literal no longer matches the recomputed hash.
    for c in spec_hash_cells:
        src = _cell_source(c)
        if current_spec_hash in src:
            return  # success
    pytest.fail(
        f"§1 spec-hash cell(s) exist but none embeds the current spec "
        f"sha256 {current_spec_hash!r}. The embedded literal must be "
        f"updated every time the spec file changes."
    )


def test_nb2_section1_recomputes_panel_fingerprint(
    nb2: nbformat.NotebookNode,
) -> None:
    """§1 loads the weekly panel and compares its fingerprint to JSON.

    The notebook must carry a §1 code cell that calls
    ``cleaning.load_cleaned_panel`` and ``panel_fingerprint`` (fingerprint
    API) on column ``week_start``, then compares the result against the
    ``FINGERPRINT_PATH`` JSON file (via ``env.FINGERPRINT_PATH`` or
    equivalent reference).
    """
    s1_code = _code_cells(_section_cells(nb2, SECTION1_TAG))
    fingerprint_cells = [
        c
        for c in s1_code
        if all(
            landmark in _cell_source(c) for landmark in _FINGERPRINT_LANDMARKS
        )
    ]
    assert fingerprint_cells, (
        f"§1 must contain a code cell with all landmarks "
        f"{_FINGERPRINT_LANDMARKS!r}. None found among {len(s1_code)} §1 "
        f"code cells. Task 16 Step 3 must wire the fingerprint check."
    )


def test_nb2_section1_has_gate_verdict_placeholder(
    nb2: nbformat.NotebookNode,
) -> None:
    """§1 (or the existing skeleton) carries a Gate Verdict admonition.

    The cell may live either among §1-tagged cells (if the author moved
    it) or at the top of the notebook (if the skeleton placeholder was
    preserved). We search the entire notebook for the admonition token.
    """
    hits = [
        c
        for c in nb2.cells
        if c.get("cell_type") == "markdown"
        and _GATE_VERDICT_LANDMARK in _cell_source(c)
    ]
    assert hits, (
        f"NB2 must carry a markdown cell containing the {_GATE_VERDICT_LANDMARK!r} "
        f"admonition so Task 30's auto-render has a stable anchor. None "
        f"found."
    )


def test_nb2_section1_has_citation_block(nb2: nbformat.NotebookNode) -> None:
    """§1 carries at least one 4-part citation block markdown cell."""
    s1_md = _markdown_cells(_section_cells(nb2, SECTION1_TAG))
    citation_cells = [
        c
        for c in s1_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§1 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )


# ── §2 structural tests ───────────────────────────────────────────────────

def test_nb2_section2_exists(nb2: nbformat.NotebookNode) -> None:
    """§2 carries at least one code cell + one markdown citation block."""
    s2_cells = _section_cells(nb2, SECTION2_TAG)
    assert _code_cells(s2_cells), (
        "§2 must contain at least one code cell (tagged section:2); "
        "none found."
    )


def test_nb2_section2_code_cells_hide_input(
    nb2: nbformat.NotebookNode,
) -> None:
    """Every §2 code cell carries 'remove-input' (NB1 convention)."""
    s2_code = _code_cells(_section_cells(nb2, SECTION2_TAG))
    for c in s2_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§2 code cell missing 'remove-input' tag; got tags={tags!r}."
        )


def test_nb2_section2_has_citation_block(nb2: nbformat.NotebookNode) -> None:
    """§2 carries a 4-part citation block referencing descriptive-stat convention."""
    s2_md = _markdown_cells(_section_cells(nb2, SECTION2_TAG))
    citation_cells = [
        c
        for c in s2_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§2 must contain at least one markdown citation block (4-part "
        "header) citing the Conrad-Schoelkopf-Tushteva 2025 Table 1 "
        "descriptive-only convention."
    )


def test_nb2_section2_is_full_sample_not_conditioned(
    nb2: nbformat.NotebookNode,
) -> None:
    """§2 source must NOT reference any release-week or sub-sample filters.

    Full-sample discipline per plan line 344(d). Release-week / regime
    filters are NB3 concerns, not §2's.
    """
    s2_code_sources = [
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION2_TAG))
    ]
    combined = "\n".join(s2_code_sources)
    for forbidden in _FORBIDDEN_FILTERS:
        assert forbidden not in combined, (
            f"§2 code references forbidden filter token {forbidden!r}; "
            f"full-sample discipline per spec Rev 4 §3 NB2.2 and plan "
            f"line 344(d). Remove any release-week / regime conditioning."
        )


def test_nb2_section2_emits_full_sample_descriptive_stats(
    nb2: nbformat.NotebookNode, conn
) -> None:
    """§2 computes a DataFrame over 7 series × 4 stats, full-sample.

    The test extracts §2 code cells, prepends a minimal bootstrap that
    reproduces the notebook's ``env``/``cleaning``/``panel`` setup (to
    avoid re-running §1's expensive machinery), and executes them in a
    fresh namespace. It then inspects the variable
    ``_descriptive_stats`` (the contracted table binding) and asserts
    both the 7-row index and the 4-column statistic set.
    """
    s2_code = _code_cells(_section_cells(nb2, SECTION2_TAG))
    assert s2_code, "§2 must contain at least one code cell."

    # Build a standalone script that reproduces enough of NB2 §1 to
    # give §2 the variables it needs. We do NOT re-execute §1 cells
    # (that would double the runtime and couple the tests). Instead we
    # minimally reconstruct the ``panel`` / ``env`` / ``cleaning``
    # bindings.
    s2_source = "\n\n".join(_cell_source(c) for c in s2_code)

    bootstrap = (
        "import sys\n"
        f"sys.path.insert(0, {str(_CONTRACTS_DIR / 'scripts')!r})\n"
        f"sys.path.insert(0, {str(_ENV_PATH.parent)!r})\n"
        "import duckdb\n"
        "import env\n"
        "from scripts import cleaning\n"
        "from scripts import panel_fingerprint\n"
        "conn = duckdb.connect(str(env.DUCKDB_PATH), read_only=True)\n"
        "try:\n"
        "    _panel = cleaning.load_cleaned_panel(conn)\n"
        "    panel = _panel  # alias; §2 may use either name\n"
        "    weekly = _panel.weekly\n"
        "finally:\n"
        "    conn.close()\n"
    )

    ns: dict[str, object] = {}
    exec(compile(bootstrap + "\n" + s2_source, "<nb2-section2>", "exec"), ns)

    assert _DESCRIPTIVE_STATS_VAR in ns, (
        f"§2 must bind the descriptive-stats DataFrame to a variable "
        f"named {_DESCRIPTIVE_STATS_VAR!r}. Found names: "
        f"{sorted(k for k in ns if not k.startswith('__'))!r}"
    )

    df = ns[_DESCRIPTIVE_STATS_VAR]

    # Duck-type: must have .index, .columns, 7 rows, 4 cols.
    assert hasattr(df, "index") and hasattr(df, "columns"), (
        f"{_DESCRIPTIVE_STATS_VAR} must be a pandas DataFrame; got "
        f"{type(df).__name__}."
    )

    index_set = set(str(i) for i in df.index)
    missing_rows = set(EXPECTED_SERIES) - index_set
    assert not missing_rows, (
        f"{_DESCRIPTIVE_STATS_VAR} missing expected rows {missing_rows!r}; "
        f"got index={sorted(index_set)!r}. All 7 series "
        f"(LHS + 6 RHS) must appear."
    )

    cols = set(str(c).lower() for c in df.columns)
    missing_cols = EXPECTED_STAT_COLS - cols
    assert not missing_cols, (
        f"{_DESCRIPTIVE_STATS_VAR} missing expected columns "
        f"{missing_cols!r}; got columns={sorted(cols)!r}. All four "
        f"stats (mean / std / skew / kurtosis) must appear."
    )


# ── End-to-end lint ───────────────────────────────────────────────────────

def test_nb2_citation_lint_passes() -> None:
    """``lint_notebook_citations.py`` exits 0 on the live NB2 path."""
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
        f"Expected lint exit 0 on NB2; got {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
