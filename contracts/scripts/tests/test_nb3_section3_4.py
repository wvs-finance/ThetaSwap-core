"""Structural regression tests for NB3 §3 (T2 Levene announcement-channel)
and §4 (T4 Ljung-Box + T5 Jarque-Bera on primary residuals) — Task 25 of
the econ-notebook implementation plan.

§3 asserts Levene's test in the Brown-Forsythe variant (median-centered)
comparing weekly ``rv_cuberoot`` on CPI-release weeks (218 of 947 per
Phase 1 audit) versus non-release weeks (729). Rejection at α=0.10 is
product-viability-relevant: an announcement-channel-active verdict says
that release days themselves carry a vol footprint distinguishable from
ordinary weeks, independent of surprise sign or magnitude. Under the
primary T3b gate-verdict FAIL scenario, a §3 REJECT would still supply
clean empirical grounding for the pre-event hedge thesis.

§4 asserts residual diagnostics on ``column6_fit.resid`` unpickled from
``env.FULL_PKL_PATH`` in §1: Ljung-Box Q(1..8) — 8 autocorrelation
statistics — plus Jarque-Bera for normality. These are the final
diagnostics on the PKL-serialised residuals; they should line up with
NB2 §4's in-memory reads. Ljung-Box rejections motivate the HAC(4)
standard errors already applied in NB2; Jarque-Bera rejection motivates
the Student-t robustness refit from NB2 §5.

Tests are TDD-first: written to fail against the 9-cell Task-24 baseline
and pass after Task 25's 2 trios (= 6 cells) extend NB3 to 15 cells.

What gets asserted, in order of decreasing "load-bearing":

  1. Cell count: 15 after Task 25 (6 new cells beyond Task 24's 9).
  2. §3 exists: at least one ``section:3`` code cell, every code cell
     has ``remove-input``.
  3. §3 Levene source uses ``scipy.stats.levene`` with
     ``center='median'`` (Brown-Forsythe variant, explicitly).
  4. §3 source splits on the ``is_cpi_release_week`` column (landmark
     for the 218/729 split).
  5. §3 source binds the result to ``_levene_result`` so the test can
     execute it and read the W-statistic and p-value (same contract
     pattern as NB3 §2's ``_t1_f_result``).
  6. §3 citation block references BOTH ``@levene1960robust`` and
     ``@conover1981comparative``.
  7. §3 verdict markdown mentions REJECT or FAIL TO REJECT at α=0.10 +
     the "announcement channel" phrase (active/absent).
  8. §4 exists: at least one ``section:4`` code cell, every code cell
     has ``remove-input``.
  9. §4 source references ``acorr_ljungbox`` with ``lags=8`` (Q(1..8))
     and pulls residuals from ``column6_fit`` / the PKL dict.
 10. §4 source references ``jarque_bera`` on the same residuals.
 11. §4 binds the Ljung-Box output to ``_ljungbox_df`` and Jarque-Bera
     result to ``_jb_result``; the test execs §4 source (with §1-§3
     bootstrap) and asserts:
       * ``_ljungbox_df`` is a DataFrame-like with 8 rows (lags 1..8)
         carrying ``lb_pvalue`` column (canonical statsmodels name).
       * ``_jb_result`` exposes a pair (stat, pvalue) or a tuple
         compatible with ``statsmodels.stats.stattools.jarque_bera``.
 12. §4 citation block references BOTH ``@ljungBox1978measure`` and
     ``@jarqueBera1987normality``.
 13. Citation lint clean: ``lint_notebook_citations.py`` exits 0.

What is NOT asserted:
  * Exact Levene W-stat or p-value (would couple to the panel
    snapshot).
  * Exact Ljung-Box / Jarque-Bera values.
  * Exact prose wording of the interpretation cells.

No mocks — reads the real NB3 on disk and the real PKL / panel. §4
executes: we want the 8-lag Ljung-Box table and JB output to actually
run against the serialised residuals (the whole point of §4 is to
confirm PKL residuals behave identically to NB2's in-memory ones).
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

# ── Path plumbing (mirrors test_nb3_section1_2.py) ────────────────────────

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

SECTION3_TAG: Final[str] = "section:3"
SECTION4_TAG: Final[str] = "section:4"
REMOVE_INPUT_TAG: Final[str] = "remove-input"

REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# §3 landmarks: median-centered Levene call + release-week split.
_LEVENE_CALL_LANDMARK: Final[str] = "scipy.stats.levene"
_LEVENE_CENTER_LANDMARK: Final[str] = "center='median'"
_RELEASE_WEEK_LANDMARK: Final[str] = "is_cpi_release_week"
_LEVENE_RESULT_VAR: Final[str] = "_levene_result"

# §3 citation bib keys.
_LEVENE1960_KEY: Final[str] = "levene1960robust"
_CONOVER1981_KEY: Final[str] = "conover1981comparative"

# §3 verdict tokens (α=0.10 per plan line 480).
_VERDICT_TOKENS: Final[tuple[str, ...]] = ("REJECT", "FAIL TO REJECT")
_ANNOUNCEMENT_TOKENS: Final[tuple[str, ...]] = (
    "announcement channel",
    "ANNOUNCEMENT CHANNEL",
)

# §4 landmarks: Ljung-Box Q(1..8) + Jarque-Bera on residuals.
_ACORR_LJUNGBOX_LANDMARK: Final[str] = "acorr_ljungbox"
_JARQUE_BERA_LANDMARK: Final[str] = "jarque_bera"
_LJUNGBOX_LAGS_LANDMARK: Final[str] = "lags=8"
_COLUMN6_RESID_LANDMARK: Final[str] = "column6_fit"
_LJUNGBOX_RESULT_VAR: Final[str] = "_ljungbox_df"
_JB_RESULT_VAR: Final[str] = "_jb_result"

# §4 citation bib keys.
_LJUNGBOX1978_KEY: Final[str] = "ljungBox1978measure"
_JARQUEBERA1987_KEY: Final[str] = "jarqueBera1987normality"

# Task 25 target: 9 cells (Task 24 baseline) + 6 cells (2 trios) = 15.
_POST_TASK25_CELL_COUNT: Final[int] = 15


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


# ── Shared bootstrap for §3/§4 source execution ───────────────────────────
#
# §3 and §4 both depend on §1 having loaded the weekly panel and the PKL
# into the `_pkl` dict. We don't re-execute §1 in tests (1.4 MB pickle
# deserialisation). Instead we mimic §1's exported names (panel, _pkl,
# pkl_degraded) and then exec the section source on top.
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
        # Common aliases the author may use.
        "column6_fit = _pkl['column6_fit']\n"
    )


# ── §3 structural tests ───────────────────────────────────────────────────

def test_nb3_has_task25_cell_count(nb3: nbformat.NotebookNode) -> None:
    """NB3 grows from 9 cells (Task 24) to 15 cells (Task 25 = + 2 trios)."""
    assert len(nb3.cells) >= _POST_TASK25_CELL_COUNT, (
        f"NB3 has {len(nb3.cells)} cells; Task 25 must author 6 new cells "
        f"(2 trios: §3 + §4) for a total of {_POST_TASK25_CELL_COUNT}."
    )


def test_nb3_section3_has_at_least_one_code_cell(
    nb3: nbformat.NotebookNode,
) -> None:
    """§3 exists: at least one code cell + every code cell has remove-input."""
    s3_code = _code_cells(_section_cells(nb3, SECTION3_TAG))
    assert s3_code, (
        "§3 must contain at least one code cell (tagged section:3); "
        "none found."
    )
    for c in s3_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§3 code cell missing 'remove-input' tag; got tags={tags!r}."
        )


def test_nb3_section3_levene_brown_forsythe(
    nb3: nbformat.NotebookNode,
) -> None:
    """§3 uses scipy.stats.levene with center='median' — Brown-Forsythe."""
    combined = _section_source(nb3, SECTION3_TAG)
    assert _LEVENE_CALL_LANDMARK in combined, (
        f"§3 must call {_LEVENE_CALL_LANDMARK!r}. Not found in §3 code."
    )
    assert _LEVENE_CENTER_LANDMARK in combined, (
        f"§3 must pass {_LEVENE_CENTER_LANDMARK!r} to scipy.stats.levene "
        f"(Brown-Forsythe variant, median-centered — plan line 480). "
        f"Not found in §3 code."
    )


def test_nb3_section3_splits_on_release_week(
    nb3: nbformat.NotebookNode,
) -> None:
    """§3 references the is_cpi_release_week column for the 218/729 split."""
    combined = _section_source(nb3, SECTION3_TAG)
    assert _RELEASE_WEEK_LANDMARK in combined, (
        f"§3 must reference {_RELEASE_WEEK_LANDMARK!r} to partition weekly "
        f"RV into release (218) vs non-release (729) groups. Not found."
    )


def test_nb3_section3_reports_W_stat_and_pvalue(
    nb3: nbformat.NotebookNode,
) -> None:
    """§3 binds the Levene result and exposes statistic + pvalue.

    Executes §3 source with a bootstrap reproducing §1's panel + PKL
    loads, then checks the bound result has the canonical scipy
    ``statistic`` and ``pvalue`` attributes (a namedtuple-like object).
    """
    s3_code_src = _section_source(nb3, SECTION3_TAG)
    assert s3_code_src, "§3 code must exist."

    ns: dict[str, object] = {}
    exec(
        compile(_make_bootstrap() + "\n" + s3_code_src, "<nb3-section3>", "exec"),
        ns,
    )
    assert _LEVENE_RESULT_VAR in ns, (
        f"§3 must bind the Levene result to {_LEVENE_RESULT_VAR!r} so "
        f"downstream cells (and this test) can read the W-stat and "
        f"p-value. Found names: "
        f"{sorted(k for k in ns if not k.startswith('__'))!r}"
    )
    result = ns[_LEVENE_RESULT_VAR]
    for attr in ("statistic", "pvalue"):
        assert hasattr(result, attr), (
            f"{_LEVENE_RESULT_VAR} missing attribute {attr!r}; expected a "
            f"scipy.stats.levene result (namedtuple with statistic/pvalue). "
            f"got type={type(result).__name__}."
        )
    stat = float(result.statistic)
    pval = float(result.pvalue)
    assert math.isfinite(stat) and stat >= 0.0, (
        f"Levene statistic invalid: {stat!r}"
    )
    assert 0.0 <= pval <= 1.0, f"Levene p-value out of [0,1]: {pval!r}"


def test_nb3_section3_verdict_at_alpha_0p10(
    nb3: nbformat.NotebookNode,
) -> None:
    """§3 verdict markdown mentions REJECT or FAIL TO REJECT at α=0.10."""
    s3_md = _markdown_cells(_section_cells(nb3, SECTION3_TAG))
    combined = "\n\n".join(_cell_source(c).upper() for c in s3_md)
    hits = [t for t in _VERDICT_TOKENS if t in combined]
    assert hits, (
        f"§3 must carry a markdown cell mentioning one of "
        f"{_VERDICT_TOKENS!r} (Levene verdict at α=0.10 per plan). "
        f"None found in §3 markdown."
    )
    # Also require the 0.10 threshold to be mentioned explicitly so a
    # reader who only sees the verdict string can still tell the threshold.
    assert "0.10" in combined or "0.1" in combined or "10%" in combined, (
        "§3 markdown must mention the α=0.10 threshold (not 0.05). Plan "
        "line 480 locks 10% for the announcement-channel reading."
    )


def test_nb3_section3_announcement_channel_claim(
    nb3: nbformat.NotebookNode,
) -> None:
    """§3 interpretation references the 'announcement channel' phrase."""
    s3_md = _markdown_cells(_section_cells(nb3, SECTION3_TAG))
    combined_lower = "\n\n".join(
        _cell_source(c).lower() for c in s3_md
    )
    assert "announcement channel" in combined_lower, (
        "§3 must carry a markdown cell mentioning 'announcement channel' — "
        "this is the product-viability reading of the Levene test (active "
        "when REJECT, absent when FAIL TO REJECT). None found in §3 "
        "markdown."
    )


def test_nb3_section3_citation_has_levene1960_and_conover1981(
    nb3: nbformat.NotebookNode,
) -> None:
    """§3 carries a 4-part citation block citing BOTH canonical keys."""
    s3_md = _markdown_cells(_section_cells(nb3, SECTION3_TAG))
    citation_cells = [
        c
        for c in s3_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§3 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )
    combined = "\n\n".join(_cell_source(c) for c in citation_cells)
    for key in (_LEVENE1960_KEY, _CONOVER1981_KEY):
        assert key in combined, (
            f"§3 citation block(s) must reference bib key @{key}. Not "
            f"found among §3 citation markdown cells."
        )


# ── §4 structural tests ───────────────────────────────────────────────────

def test_nb3_section4_has_at_least_one_code_cell(
    nb3: nbformat.NotebookNode,
) -> None:
    """§4 exists: at least one code cell + every code cell has remove-input."""
    s4_code = _code_cells(_section_cells(nb3, SECTION4_TAG))
    assert s4_code, (
        "§4 must contain at least one code cell (tagged section:4); "
        "none found."
    )
    for c in s4_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§4 code cell missing 'remove-input' tag; got tags={tags!r}."
        )


def test_nb3_section4_ljung_box_Q1_to_Q8(
    nb3: nbformat.NotebookNode,
) -> None:
    """§4 source calls acorr_ljungbox with lags=8 and reads column6 resid."""
    combined = _section_source(nb3, SECTION4_TAG)
    assert _ACORR_LJUNGBOX_LANDMARK in combined, (
        f"§4 must call {_ACORR_LJUNGBOX_LANDMARK!r} "
        f"(statsmodels.stats.diagnostic). Not found in §4 code."
    )
    assert _LJUNGBOX_LAGS_LANDMARK in combined, (
        f"§4 must pass {_LJUNGBOX_LAGS_LANDMARK!r} to acorr_ljungbox — "
        f"plan locks Q(1..8). Not found in §4 code."
    )
    assert _COLUMN6_RESID_LANDMARK in combined, (
        f"§4 must reference {_COLUMN6_RESID_LANDMARK!r} (the PKL-dict "
        f"primary fit) so the reader sees which residuals are being "
        f"diagnosed. Not found in §4 code."
    )


def test_nb3_section4_jarque_bera_on_residuals(
    nb3: nbformat.NotebookNode,
) -> None:
    """§4 source calls jarque_bera (statsmodels) on the residuals."""
    combined = _section_source(nb3, SECTION4_TAG)
    assert _JARQUE_BERA_LANDMARK in combined, (
        f"§4 must call {_JARQUE_BERA_LANDMARK!r} "
        f"(statsmodels.stats.stattools). Not found in §4 code."
    )


def test_nb3_section4_binds_result_vars(
    nb3: nbformat.NotebookNode,
) -> None:
    """§4 binds _ljungbox_df (8 rows) + _jb_result; both runnable on PKL."""
    s4_code_src = _section_source(nb3, SECTION4_TAG)
    assert s4_code_src, "§4 code must exist."

    ns: dict[str, object] = {}
    exec(
        compile(_make_bootstrap() + "\n" + s4_code_src, "<nb3-section4>", "exec"),
        ns,
    )
    assert _LJUNGBOX_RESULT_VAR in ns, (
        f"§4 must bind the Ljung-Box result to {_LJUNGBOX_RESULT_VAR!r}. "
        f"Found names: "
        f"{sorted(k for k in ns if not k.startswith('__'))!r}"
    )
    assert _JB_RESULT_VAR in ns, (
        f"§4 must bind the Jarque-Bera result to {_JB_RESULT_VAR!r}. "
        f"Found names: "
        f"{sorted(k for k in ns if not k.startswith('__'))!r}"
    )

    lb_df = ns[_LJUNGBOX_RESULT_VAR]
    # Duck-type: must have 8 rows (lags 1..8) and a canonical
    # ``lb_pvalue`` column (statsmodels returns this name by default).
    assert hasattr(lb_df, "shape"), (
        f"{_LJUNGBOX_RESULT_VAR} must be DataFrame-like; got "
        f"type={type(lb_df).__name__}."
    )
    assert lb_df.shape[0] == 8, (
        f"{_LJUNGBOX_RESULT_VAR} must have 8 rows (Q(1..8)); got "
        f"shape={lb_df.shape!r}."
    )
    assert "lb_pvalue" in getattr(lb_df, "columns", ()), (
        f"{_LJUNGBOX_RESULT_VAR} must carry an 'lb_pvalue' column "
        f"(statsmodels default). columns={list(lb_df.columns)!r}"
    )

    jb = ns[_JB_RESULT_VAR]
    # statsmodels.stats.stattools.jarque_bera returns a 4-tuple
    # (JB, JBpv, skew, kurtosis). Accept that or any object with
    # statistic/pvalue.
    if isinstance(jb, tuple):
        assert len(jb) >= 2, (
            f"{_JB_RESULT_VAR} tuple must have >=2 entries (stat, pvalue); "
            f"got len={len(jb)}."
        )
        jb_stat = float(jb[0])
        jb_pval = float(jb[1])
    else:
        assert hasattr(jb, "statistic") and hasattr(jb, "pvalue"), (
            f"{_JB_RESULT_VAR} neither a tuple nor a namedtuple with "
            f"statistic/pvalue; got type={type(jb).__name__}."
        )
        jb_stat = float(jb.statistic)
        jb_pval = float(jb.pvalue)
    assert math.isfinite(jb_stat) and jb_stat >= 0.0, (
        f"Jarque-Bera statistic invalid: {jb_stat!r}"
    )
    assert 0.0 <= jb_pval <= 1.0, f"Jarque-Bera p-value out of [0,1]: {jb_pval!r}"


def test_nb3_section4_citations_ljungBox_jarqueBera(
    nb3: nbformat.NotebookNode,
) -> None:
    """§4 carries a 4-part citation block citing BOTH canonical keys."""
    s4_md = _markdown_cells(_section_cells(nb3, SECTION4_TAG))
    citation_cells = [
        c
        for c in s4_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§4 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )
    combined = "\n\n".join(_cell_source(c) for c in citation_cells)
    for key in (_LJUNGBOX1978_KEY, _JARQUEBERA1987_KEY):
        assert key in combined, (
            f"§4 citation block(s) must reference bib key @{key}. Not "
            f"found among §4 citation markdown cells."
        )


# ── Handoff-artifact sanity ───────────────────────────────────────────────

def test_full_pkl_has_column6_fit_with_resid() -> None:
    """Pre-flight sanity: PKL carries a column6_fit with .resid (947)."""
    assert FULL_PKL_PATH.is_file(), f"FULL_PKL missing: {FULL_PKL_PATH}"
    with open(FULL_PKL_PATH, "rb") as fh:
        pkl = pickle.load(fh)
    assert isinstance(pkl, dict), (
        f"FULL_PKL root must be a dict; got {type(pkl).__name__}."
    )
    assert "column6_fit" in pkl, (
        f"FULL_PKL missing 'column6_fit' key. Got keys: "
        f"{sorted(pkl.keys())!r}"
    )
    fit = pkl["column6_fit"]
    assert hasattr(fit, "resid"), (
        f"column6_fit must expose .resid; got type={type(fit).__name__}."
    )
    resid = fit.resid
    assert len(resid) == 947, (
        f"column6_fit.resid must have 947 entries (weekly panel); got "
        f"len={len(resid)}."
    )


# ── End-to-end lint ───────────────────────────────────────────────────────

def test_nb3_citation_lint_passes_after_task25() -> None:
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
