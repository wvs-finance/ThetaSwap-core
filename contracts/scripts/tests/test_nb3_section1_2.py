"""Structural regression test for NB3 §1 (Setup + pre-flight verification)
and §2 (T1 consensus-rationality F-test) — Task 24 of the econ-notebook
implementation plan.

NB3's §1 performs the same three pre-flight checks as NB2's §1 (spec-hash
match + panel-fingerprint equality + Gate Verdict anchor) AND adds a
fourth: version-mismatch degraded mode. The handoff JSON carries a
``handoff_metadata`` block pinning the Python / statsmodels / arch /
numpy / pandas versions that produced the pickle. On execute, §1 compares
those pins to the currently-installed versions; any major.minor mismatch
emits a WARNING and sets ``pkl_degraded = True``. Downstream cells that
consume pickled statsmodels fit objects (Ljung-Box on residuals, Bai-
Perron inputs, etc.) must gate on ``not pkl_degraded`` — that contract is
authored in later Phase-3 tasks (25-29), but §1 must wire the flag.

§2 runs the first specification test, T1 consensus-rationality: under
rational expectations, CPI surprises should be uncorrelated with
information dated t-1. §2 regresses ``s_t^CPI`` on {s_{t-1}^CPI,
RV_{t-1}, VIX_{t-1}} on the Decision #1 weekly window and reports the
joint F-statistic, the F-test p-value, and a REJECT / FAIL-TO-REJECT
verdict at α=0.05. Rejection means surprises are predictable from
lagged information — an identification concern for the primary
specification, pre-committed to the gate verdict.

This module is authored TDD-first: it fails against the 2-cell skeleton
and turns green once the Analytics Reporter appends §1 + §2 cells.

What gets asserted, in order of decreasing "load-bearing":

  1. Handoff artifact loads: §1 references both
     ``env.POINT_JSON_PATH`` and ``env.FULL_PKL_PATH`` so the reader
     can see where the pre-flight reads come from.
  2. Spec-hash match: §1 re-computes the sha256 of the econ-notebook
     design spec inline and asserts equality with the JSON's
     ``spec_hash`` field.
  3. Panel fingerprint match: §1 re-loads the weekly panel via
     ``cleaning.load_cleaned_panel`` and fingerprints it via
     ``panel_fingerprint.fingerprint(df, "week_start")``, then compares
     the resulting sha256 to the JSON's ``panel_fingerprint`` field.
  4. Version-mismatch degraded mode: §1 source must reference the
     token ``pkl_degraded`` and compare runtime package versions to
     the JSON's ``handoff_metadata`` pins (landmark tokens:
     ``handoff_metadata`` + ``pkl_degraded``). Keeps the contract
     observable in static analysis without having to execute the
     notebook under a version-drifted kernel.
  5. §1 citation block: at least one markdown cell among §1 carries
     all four required headers AND references
     ``@ankelPeters2024protocol`` so the handoff protocol citation is
     grounded.
  6. §2 T1 OLS regressors: §2 code binds the F-test result object to
     a known variable name (``_t1_f_result``) and fits OLS of
     ``cpi_surprise_ar1`` on the three lagged regressors (landmark
     tokens: ``cpi_surprise_ar1`` + ``.shift(1)`` + ``OLS(``).
  7. §2 verdict string: an output markdown cell tagged ``section:2``
     mentions "REJECT" or "FAIL TO REJECT" at α=0.05 so the reader
     sees the verdict without inspecting numeric output.
  8. §2 citation block: §2's gated code cell is preceded by a 4-part
     citation block that cites BOTH
     ``@mincerZarnowitz1969evaluation`` (forecast-rationality test
     canon) AND ``@balduzzi2001economic`` (macro-surprise exogeneity
     construction).
  9. Section tags: new §1 cells carry ``section:1`` and every §1
     code cell also carries ``remove-input``; same for §2 cells with
     ``section:2``. Mirrors NB1 / NB2 convention.
 10. Citation lint clean: the full lint script exits 0 on NB3.

What is NOT asserted:
  * Exact prose (would couple the test to authoring style).
  * Exact numeric values of the F-statistic or p-value (would couple
    the test to the panel snapshot — prototype shows F≈15.1, p≈1e-9,
    so REJECT is the confident prediction, but the test only asserts
    the verdict string appears).
  * The exact Python code layout beyond the landmark API calls named
    above — the author is free to place helper logic around the fit.

No mocks — reads the real NB3 ipynb on disk and the real NB2 JSON/PKL
artifacts committed under Colombia/estimates/. No subprocess execution
of §1 is attempted (§1 loads a 1.4 MB pickle file; a structural inspection
of source-level landmarks is sufficient to prove the contract is wired).
§2 DOES execute: we want to see the F-test runs against the real panel
and emits a verdict — that's the core of the acceptance criterion.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
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

SPEC_MD_PATH: Final[Path] = (
    _CONTRACTS_DIR
    / "docs"
    / "superpowers"
    / "specs"
    / "2026-04-17-econ-notebook-design.md"
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
NB3_PATH: Final[Path] = _env.NB3_PATH
POINT_JSON_PATH: Final[Path] = _env.POINT_JSON_PATH
FULL_PKL_PATH: Final[Path] = _env.FULL_PKL_PATH


# ── Constants ─────────────────────────────────────────────────────────────

# §1 / §2 cell-tag contract. §1 code cells carry both section:1 and
# remove-input (NB1 / NB2 convention). Same for §2.
SECTION1_TAG: Final[str] = "section:1"
SECTION2_TAG: Final[str] = "section:2"
REMOVE_INPUT_TAG: Final[str] = "remove-input"

# Required headers in any 4-part citation block.
REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# Landmark API tokens the test searches for in §1 code cells.
_POINT_JSON_LANDMARK: Final[str] = "POINT_JSON_PATH"
_FULL_PKL_LANDMARK: Final[str] = "FULL_PKL_PATH"

# The four §1 load-bearing concepts, each a single landmark token the
# source must reference. Each check looks for the token anywhere in any
# §1 code cell's source.
_SPEC_HASH_LANDMARKS: Final[tuple[str, ...]] = (
    "hashlib.sha256",
    "2026-04-17-econ-notebook-design.md",
)

_FINGERPRINT_LANDMARKS: Final[tuple[str, ...]] = (
    "cleaning.load_cleaned_panel",
    "panel_fingerprint",
    "week_start",
)

_DEGRADED_MODE_LANDMARKS: Final[tuple[str, ...]] = (
    "pkl_degraded",
    "handoff_metadata",
)

# §1 citation block must reference the Ankel-Peters 2024 handoff-
# verification protocol bib key (at minimum).
_HANDOFF_PROTOCOL_KEY: Final[str] = "ankelPeters2024protocol"

# §2 citation block must reference BOTH canonical keys.
_MINCER_ZARNOWITZ_KEY: Final[str] = "mincerZarnowitz1969evaluation"
_BALDUZZI_KEY: Final[str] = "balduzzi2001economic"

# §2 code cell must bind the F-test result object to this variable name.
# Contracted so the test can exec the source and extract fstat / pvalue
# for the verdict assertion.
_T1_F_RESULT_VAR: Final[str] = "_t1_f_result"

# §2 landmarks: regressor construction + OLS invocation + lagged
# surprise reference. We want the source to literally reference the
# three lagged regressors — the t-1 surprise, t-1 RV, t-1 VIX — so a
# static reader can confirm which regressors are being tested.
_T1_REGRESSOR_LANDMARKS: Final[tuple[str, ...]] = (
    "cpi_surprise_ar1",
    ".shift(1)",
    "rv_cuberoot",
    "vix_avg",
)

_T1_OLS_LANDMARK: Final[str] = "OLS("

# §2 verdict string: the notebook must emit either REJECT or FAIL TO
# REJECT somewhere in its §2 output (markdown). Matching is
# case-insensitive against the canonical phrases.
_T1_VERDICT_TOKENS: Final[tuple[str, ...]] = (
    "REJECT",
    "FAIL TO REJECT",
)

# NB3 starts at 2 cells (skeleton). After §1-2 authoring we expect at
# least a title + gate + 2 trios (= 6 authored) = 8 cells total.
_MIN_POST_AUTHOR_CELL_COUNT: Final[int] = 8


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def nb3() -> nbformat.NotebookNode:
    """Load NB3 once per module."""
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


def _load_point_json() -> dict:
    return json.loads(POINT_JSON_PATH.read_text(encoding="utf-8"))


# ── §1 structural tests ───────────────────────────────────────────────────

def test_nb3_exists_and_has_enough_cells(nb3: nbformat.NotebookNode) -> None:
    """NB3 has at least the §1-2 cell count after authoring."""
    assert len(nb3.cells) >= _MIN_POST_AUTHOR_CELL_COUNT, (
        f"NB3 has only {len(nb3.cells)} cells; §1-2 authoring must append "
        f"at least {_MIN_POST_AUTHOR_CELL_COUNT - 2} new cells beyond the "
        f"2-cell skeleton."
    )


def test_nb3_section1_has_at_least_one_code_cell(
    nb3: nbformat.NotebookNode,
) -> None:
    """§1 exists: at least one code cell carries section:1 + remove-input."""
    s1_cells = _section_cells(nb3, SECTION1_TAG)
    s1_code = _code_cells(s1_cells)
    assert s1_code, (
        "§1 must contain at least one code cell (tagged section:1); "
        "none found. Task 24 Step 3 must author §1."
    )
    for c in s1_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§1 code cell missing 'remove-input' tag; got tags={tags!r}."
        )


def test_nb3_section1_loads_point_json(
    nb3: nbformat.NotebookNode,
) -> None:
    """§1 references env.POINT_JSON_PATH so the JSON load is visible."""
    s1_code = _code_cells(_section_cells(nb3, SECTION1_TAG))
    hits = [c for c in s1_code if _POINT_JSON_LANDMARK in _cell_source(c)]
    assert hits, (
        f"§1 must reference the landmark {_POINT_JSON_LANDMARK!r} (the "
        f"env.py constant pointing at nb2_params_point.json). No §1 "
        f"code cell mentions it among {len(s1_code)} cells."
    )


def test_nb3_section1_loads_full_pkl(
    nb3: nbformat.NotebookNode,
) -> None:
    """§1 references env.FULL_PKL_PATH so the PKL load is visible."""
    s1_code = _code_cells(_section_cells(nb3, SECTION1_TAG))
    hits = [c for c in s1_code if _FULL_PKL_LANDMARK in _cell_source(c)]
    assert hits, (
        f"§1 must reference the landmark {_FULL_PKL_LANDMARK!r} (the "
        f"env.py constant pointing at nb2_params_full.pkl). No §1 code "
        f"cell mentions it among {len(s1_code)} cells."
    )


def test_nb3_section1_enforces_spec_hash_match(
    nb3: nbformat.NotebookNode,
) -> None:
    """§1 has a code cell that re-computes the spec sha256.

    Two landmark tokens must co-occur: ``hashlib.sha256`` (recomputation)
    and ``2026-04-17-econ-notebook-design.md`` (the filename). Additionally
    the current spec-file sha256 hex MUST appear as an embedded literal so
    a silent spec edit flips the assertion.
    """
    s1_code = _code_cells(_section_cells(nb3, SECTION1_TAG))
    current_spec_hash = _compute_spec_hash()

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

    for c in spec_hash_cells:
        src = _cell_source(c)
        if current_spec_hash in src:
            return  # success
    pytest.fail(
        f"§1 spec-hash cell(s) exist but none embeds the current spec "
        f"sha256 {current_spec_hash!r}. The embedded literal must be "
        f"updated every time the spec file changes."
    )


def test_nb3_section1_verifies_panel_fingerprint(
    nb3: nbformat.NotebookNode,
) -> None:
    """§1 re-loads the weekly panel and re-computes its fingerprint."""
    s1_code = _code_cells(_section_cells(nb3, SECTION1_TAG))
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
        f"code cells. Task 24 Step 3 must re-wire the fingerprint check."
    )


def test_nb3_section1_version_mismatch_degraded_mode(
    nb3: nbformat.NotebookNode,
) -> None:
    """§1 source references pkl_degraded and handoff_metadata.

    The degraded-mode logic compares runtime package versions (from
    ``importlib.metadata`` or package ``__version__`` attributes) to the
    versions pinned in the JSON's ``handoff_metadata`` block. On any
    major.minor drift, ``pkl_degraded`` is set to True and a WARNING is
    emitted; downstream NB3 cells that consume pickled statsmodels fits
    gate on ``not pkl_degraded``. The two tokens together prove the
    contract is wired at authoring time.
    """
    s1_code = _code_cells(_section_cells(nb3, SECTION1_TAG))
    combined = "\n\n".join(_cell_source(c) for c in s1_code)
    missing = [t for t in _DEGRADED_MODE_LANDMARKS if t not in combined]
    assert not missing, (
        f"§1 must reference landmarks {_DEGRADED_MODE_LANDMARKS!r} to "
        f"wire the version-mismatch degraded mode. Missing from all §1 "
        f"code cells: {missing!r}."
    )


def test_nb3_section1_citation_block(
    nb3: nbformat.NotebookNode,
) -> None:
    """§1 carries a 4-part citation block citing ankelPeters2024protocol."""
    s1_md = _markdown_cells(_section_cells(nb3, SECTION1_TAG))
    citation_cells = [
        c
        for c in s1_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§1 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )
    combined = "\n\n".join(_cell_source(c) for c in citation_cells)
    assert _HANDOFF_PROTOCOL_KEY in combined, (
        f"§1 citation block(s) must reference bib key "
        f"@{_HANDOFF_PROTOCOL_KEY} (Ankel-Peters et al. 2024 handoff-"
        f"verification protocol). Not found in §1 citation markdown."
    )


# ── §2 structural tests ───────────────────────────────────────────────────

def test_nb3_section2_exists(nb3: nbformat.NotebookNode) -> None:
    """§2 carries at least one code cell."""
    s2_cells = _section_cells(nb3, SECTION2_TAG)
    assert _code_cells(s2_cells), (
        "§2 must contain at least one code cell (tagged section:2); "
        "none found."
    )


def test_nb3_section2_code_cells_hide_input(
    nb3: nbformat.NotebookNode,
) -> None:
    """Every §2 code cell carries 'remove-input' (NB1 / NB2 convention)."""
    s2_code = _code_cells(_section_cells(nb3, SECTION2_TAG))
    for c in s2_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§2 code cell missing 'remove-input' tag; got tags={tags!r}."
        )


def test_nb3_section2_t1_regressor_landmarks(
    nb3: nbformat.NotebookNode,
) -> None:
    """§2 source references each of the three lagged regressors + OLS."""
    s2_code = _code_cells(_section_cells(nb3, SECTION2_TAG))
    combined = "\n\n".join(_cell_source(c) for c in s2_code)
    missing = [t for t in _T1_REGRESSOR_LANDMARKS if t not in combined]
    assert not missing, (
        f"§2 must reference landmarks {_T1_REGRESSOR_LANDMARKS!r} so a "
        f"static reader sees the three lagged regressors used in T1. "
        f"Missing from §2 code: {missing!r}."
    )
    assert _T1_OLS_LANDMARK in combined, (
        f"§2 must call {_T1_OLS_LANDMARK!r} — T1 is fitted via OLS. "
        f"Token not found in §2 code."
    )


def test_nb3_section2_t1_f_test_binds_result(
    nb3: nbformat.NotebookNode,
) -> None:
    """§2 binds the fit/F-test result to the contract variable name.

    Executes §2 source in a fresh namespace (with a minimal bootstrap
    reproducing enough of §1 to give §2 the panel) and asserts that
    ``_t1_f_result`` exists and exposes ``fvalue`` / ``f_pvalue`` — the
    canonical statsmodels OLS F-test attributes. This is the contract
    downstream Task 25-29 tests lean on.
    """
    s2_code = _code_cells(_section_cells(nb3, SECTION2_TAG))
    assert s2_code, "§2 must contain at least one code cell."

    s2_source = "\n\n".join(_cell_source(c) for c in s2_code)

    # Minimal bootstrap: give §2 the panel + env without re-running §1's
    # JSON/PKL load (avoids 1.4 MB pickle deserialisation overhead in the
    # test). Mirrors the NB2 §2 bootstrap pattern.
    bootstrap = (
        "import sys\n"
        f"sys.path.insert(0, {str(_CONTRACTS_DIR)!r})\n"
        f"sys.path.insert(0, {str(_ENV_PATH.parent)!r})\n"
        "import duckdb\n"
        "import env\n"
        "from scripts import cleaning\n"
        "from scripts import panel_fingerprint\n"
        "conn = duckdb.connect(str(env.DUCKDB_PATH), read_only=True)\n"
        "try:\n"
        "    _panel = cleaning.load_cleaned_panel(conn)\n"
        "    panel = _panel  # alias\n"
        "    weekly = _panel.weekly\n"
        "finally:\n"
        "    conn.close()\n"
        # Pre-set pkl_degraded so §2 can read it if it chooses to\n"
        "pkl_degraded = False\n"
    )

    ns: dict[str, object] = {}
    exec(compile(bootstrap + "\n" + s2_source, "<nb3-section2>", "exec"), ns)

    assert _T1_F_RESULT_VAR in ns, (
        f"§2 must bind the T1 F-test result to a variable named "
        f"{_T1_F_RESULT_VAR!r}. Found names: "
        f"{sorted(k for k in ns if not k.startswith('__'))!r}"
    )

    result = ns[_T1_F_RESULT_VAR]
    # Duck-type: must expose fvalue + f_pvalue (statsmodels OLS results).
    for attr in ("fvalue", "f_pvalue"):
        assert hasattr(result, attr), (
            f"{_T1_F_RESULT_VAR} missing attribute {attr!r}; expected a "
            f"statsmodels OLS RegressionResults-like object. "
            f"got type={type(result).__name__}."
        )

    # Sanity: F-stat must be finite + non-negative; p-value in [0, 1].
    import math

    fstat = float(result.fvalue)
    pval = float(result.f_pvalue)
    assert math.isfinite(fstat) and fstat >= 0.0, (
        f"T1 F-stat invalid: {fstat!r}"
    )
    assert 0.0 <= pval <= 1.0, f"T1 p-value out of [0,1]: {pval!r}"


def test_nb3_section2_reports_verdict(
    nb3: nbformat.NotebookNode,
) -> None:
    """§2 emits REJECT or FAIL TO REJECT in a §2 markdown cell.

    The verdict string lets the reader see the outcome without inspecting
    numeric output. We match against markdown source (not executed
    output) so the assertion is stable without running the notebook.
    """
    s2_md = _markdown_cells(_section_cells(nb3, SECTION2_TAG))
    combined = "\n\n".join(_cell_source(c).upper() for c in s2_md)
    hits = [t for t in _T1_VERDICT_TOKENS if t in combined]
    assert hits, (
        f"§2 must carry a markdown cell mentioning one of "
        f"{_T1_VERDICT_TOKENS!r} (the T1 verdict at α=0.05). None found "
        f"in §2 markdown."
    )


def test_nb3_section2_citation_has_mincerZarnowitz_and_balduzzi(
    nb3: nbformat.NotebookNode,
) -> None:
    """§2 carries a 4-part citation block citing BOTH canonical keys."""
    s2_md = _markdown_cells(_section_cells(nb3, SECTION2_TAG))
    citation_cells = [
        c
        for c in s2_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§2 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )
    combined = "\n\n".join(_cell_source(c) for c in citation_cells)
    for key in (_MINCER_ZARNOWITZ_KEY, _BALDUZZI_KEY):
        assert key in combined, (
            f"§2 citation block(s) must reference bib key @{key}. Not "
            f"found among §2 citation markdown cells."
        )


# ── Handoff-artifact consistency sanity ───────────────────────────────────

def test_point_json_has_spec_hash_and_handoff_metadata() -> None:
    """Pre-flight sanity: the JSON on disk has the fields §1 will read.

    Catches a broken handoff artifact before the §1 source landmark
    checks even run.
    """
    data = _load_point_json()
    assert "spec_hash" in data, "JSON missing 'spec_hash' key"
    assert "handoff_metadata" in data, "JSON missing 'handoff_metadata' key"
    assert "panel_fingerprint" in data, "JSON missing 'panel_fingerprint' key"
    meta = data["handoff_metadata"]
    for k in (
        "python_version",
        "statsmodels_version",
        "arch_version",
        "numpy_version",
        "pandas_version",
    ):
        assert k in meta, f"handoff_metadata missing required key {k!r}"


def test_full_pkl_exists_and_nonempty() -> None:
    """Pre-flight sanity: the PKL file is present + non-trivial."""
    assert FULL_PKL_PATH.is_file(), f"FULL_PKL missing: {FULL_PKL_PATH}"
    size = FULL_PKL_PATH.stat().st_size
    # NB2 §11 emits a ~1.4 MB pickle. Tolerate some variation but catch
    # empty / truncated cases.
    assert size > 100_000, (
        f"FULL_PKL too small ({size} bytes) — expected >100 kB. Possibly "
        f"truncated / empty."
    )


# ── End-to-end lint ───────────────────────────────────────────────────────

def test_nb3_citation_lint_passes_after_task24() -> None:
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
