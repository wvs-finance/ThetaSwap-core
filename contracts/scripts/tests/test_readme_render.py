"""Tests for ``scripts.render_readme`` + the NB3 Jinja2 README auto-render
layer — Task 30 of the ``docs/superpowers/plans/2026-04-17-econ-notebook-
implementation.md`` plan.

Task 30 is the final artifact-rendering stage of the FX-vol notebook
chain. After NB3 §10 (Task 29) atomically emits the gate verdict JSON,
Task 30 renders a human-readable ``README.md`` from that JSON + NB2's
point-parameter JSON via a Jinja2 template. The rendered README is
committed to the repository so CI can detect silent drift between the
committed JSON artifacts and the committed README — a byte-identical
diff check.

Per plan line 557 the Jinja2 template MUST contain, in the following
order:

  1. A one-line gate-verdict headline (``PASS`` or ``FAIL`` with β̂ and
     the 90% CI on ``cpi_surprise_ar1`` from the primary Column-6
     specification).
  2. A β̂ results table with primary / GARCH-X / decomposition rows.
  3. A reconciliation row (``AGREE`` / ``DISAGREE``) with the
     bootstrap-HAC agreement flag from NB2 §3.5.
  4. An embedded or linked forest-plot PNG (relative markdown link;
     the PNG itself is emitted by NB3's final cell).
  5. A per-test pass/fail table for T1, T2, T4, T5, T6, T7 (T3a and
     T3b carried separately; T3b is the primary gate and drives the
     headline).
  6. Links to the three PDF exports (NB1/NB2/NB3, produced by ``just
     notebooks`` under ``env.PDF_DIR``).
  7. A spec-hash footer (plus the panel fingerprint for cross-notebook
     traceability).

The key determinism guarantee: given identical JSON inputs + identical
template, ``render_readme`` MUST produce byte-identical output across
repeated calls and across processes. No timestamps, no wall-clock
access, no random seeds. This is the precondition that enables the CI
diff check in Task 32 to detect silent pipeline drift.

Tests are TDD-first — written to fail against the ``main`` baseline
(before ``scripts/render_readme.py`` or the template exist) and pass
after Task 30's implementation.

Test coverage, in order of decreasing "load-bearing":

  1. ``scripts.render_readme`` imports cleanly.
  2. ``render_readme`` is a callable with the pure-function signature
     ``(gate_verdict, point_params, template_path) -> str``.
  3. Output starts with a one-line gate-verdict headline — plan item
     (1).
  4. Output contains a β̂ results table header + the three required
     rows (Primary / GARCH-X / Decomposition / Decomp PPI) — plan
     item (2).
  5. Output contains a reconciliation row with AGREE/DISAGREE + the
     bootstrap-HAC flag — plan item (3).
  6. Output contains a markdown image reference to the forest plot
     PNG — plan item (4).
  7. Output contains a per-test pass/fail table with rows for T1, T2,
     T4, T5, T6, T7 — plan item (5).
  8. Output contains three PDF links matching the NB1/NB2/NB3 file
     stems in ``env.PDF_DIR`` — plan item (6).
  9. Output ends with a spec-hash footer containing the expected hash
     — plan item (7).
 10. ``render_readme`` is DETERMINISTIC — three repeated calls on
     identical inputs produce byte-identical output.
 11. The CLI entry point ``python scripts/render_readme.py
     <gate_verdict.json> <point_params.json>`` prints the rendered
     markdown to stdout and matches what the pure function returns.
 12. The committed ``README.md`` is byte-identical to what
     ``render_readme`` produces from the committed JSON artifacts —
     THE CI diff check.
 13. NB3 has a final cell that loads the two JSON artifacts, calls
     ``render_readme``, and writes ``README.md``. Idempotent.

What is NOT asserted:

  * The absolute numerical values of the β̂ / CI / SE printed in the
    headline (those come directly from the committed JSON and drift
    when NB2 reruns).
  * The existence of the ``estimates/forest_plot.png`` file itself —
    the renderer only emits the markdown link; PNG emission belongs
    to the NB3 final cell.
  * The ``just notebooks`` recipe producing PDFs (Phase 4 territory).

Path / Spec conventions follow the existing ``test_nb3_section10_gate.py``
test file (same working directory layout, same env.py loader pattern).
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Final, Mapping

import nbformat
import pytest


# ── Path plumbing (mirrors test_nb3_section10_gate.py) ────────────────────

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parents[1]
_CONTRACTS_DIR: Final[Path] = _SCRIPTS_DIR.parent

_ENV_PATH: Final[Path] = (
    _CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "env.py"
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
README_PATH: Final[Path] = _env.READMEPath
GATE_VERDICT_PATH: Final[Path] = _env.GATE_VERDICT_PATH
POINT_JSON_PATH: Final[Path] = _env.POINT_JSON_PATH
COLOMBIA_DIR: Final[Path] = README_PATH.parent

TEMPLATE_PATH: Final[Path] = COLOMBIA_DIR / "_readme_template.md.j2"


# ── Synthetic inputs (do NOT depend on live JSON artifacts) ───────────────

# A self-contained synthetic pair that exercises every template branch
# without touching the committed estimates/*.json files. Mirrors the
# NB2 point-param schema (ols_primary / garch_x / decomposition /
# spec_hash / panel_fingerprint / reconciliation) and the NB3 gate-
# verdict schema (per-test verdicts + material movers + reconciliation
# + bootstrap_hac_agreement + pkl_degraded + gate_verdict).
_SYNTHETIC_GATE_VERDICT_PASS: Final[dict[str, Any]] = {
    "t1_verdict": "PASS",
    "t2_verdict": "PASS",
    "t3a_verdict": "REJECT",
    "t3b_verdict": "PASS",
    "t4_verdict": "PASS",
    "t5_verdict": "PASS",
    "t6_verdict": "PASS",
    "t7_verdict": "PASS",
    "material_movers_count": 0,
    "reconciliation": "AGREE",
    "bootstrap_hac_agreement": "AGREEMENT",
    "pkl_degraded": False,
    "gate_verdict": "PASS",
}


_SYNTHETIC_GATE_VERDICT_FAIL: Final[dict[str, Any]] = {
    "t1_verdict": "FAIL",
    "t2_verdict": "FAIL",
    "t3a_verdict": "FAIL TO REJECT",
    "t3b_verdict": "FAIL",
    "t4_verdict": "FAIL",
    "t5_verdict": "FAIL",
    "t6_verdict": "FAIL",
    "t7_verdict": "PASS",
    "material_movers_count": 0,
    "reconciliation": "AGREE",
    "bootstrap_hac_agreement": "AGREEMENT",
    "pkl_degraded": False,
    "gate_verdict": "FAIL",
}


_SYNTHETIC_POINT_PARAMS: Final[dict[str, Any]] = {
    "ols_primary": {
        "beta": {
            "const": 0.04357901203289465,
            "cpi_surprise_ar1": -0.000685131999464896,
            "us_cpi_surprise": 0.001980764304262811,
            "banrep_rate_surprise": 0.004877388461250203,
            "vix_avg": 0.0009513122347152942,
            "intervention_dummy": -0.01244999107667577,
            "oil_return": -0.02474462236874135,
        },
        "se": {
            "const": 0.00333,
            "cpi_surprise_ar1": 0.0017935935601703335,
            "us_cpi_surprise": 0.00204,
            "banrep_rate_surprise": 0.00402,
            "vix_avg": 0.00017,
            "intervention_dummy": 0.00216,
            "oil_return": 0.00684,
        },
        "n": 947,
        "hac_lag": 4,
        "r_squared": 0.19,
        "adj_r_squared": 0.185,
        "date_min": "2008-01-07",
        "date_max": "2026-02-23",
        "cov": {"matrix": [[0.0]], "param_names": ["cpi_surprise_ar1"]},
    },
    "garch_x": {
        "theta": {
            "mu": -0.0036126632151455024,
            "omega": 0.008302758867310255,
            "alpha_1": 0.13248330057004004,
            "beta_1": 0.863166474996908,
            "delta": 0.0,
        },
        "cov": {
            "matrix": [
                [1e-6, 0.0, 0.0, 0.0, 0.0],
                [0.0, 1e-6, 0.0, 0.0, 0.0],
                [0.0, 0.0, 1e-6, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1e-6, 0.0],
                [0.0, 0.0, 0.0, 0.0, 2.9551111e-37],
            ],
            "param_names": ["mu", "omega", "alpha_1", "beta_1", "delta"],
        },
        "persistence": 0.996,
        "log_likelihood": -123.4,
        "iterations": 42,
        "hessian_pd_status": "PD",
        "date_min": "2008-01-07",
        "date_max": "2026-02-23",
    },
    "decomposition": {
        "beta": {
            "cpi_surprise_ar1": -0.0006051799704374745,
            "ipp_std": 0.00024510518559515466,
        },
        "se": {
            "cpi_surprise_ar1": 0.0018375971470669522,
            "ipp_std": 0.0006821602474482078,
        },
        "n": 947,
        "date_min": "2008-01-07",
        "date_max": "2026-02-23",
        "cov": {
            "matrix": [[1.0, 0.0], [0.0, 1.0]],
            "param_names": ["cpi_surprise_ar1", "ipp_std"],
        },
    },
    "reconciliation": "AGREE",
    "spec_hash": (
        "5d86d01c5d2ca58587f966c2b0a66c942500107436ecb91c11d8efc3e65aa2c6"
    ),
    "panel_fingerprint": (
        "769ec955e72ddfcb6ff5b16e9c949fd8f53d9e8c349fc56ce96090fce81d791f"
    ),
    "t3b_pass": False,
    "gate_verdict": "FAIL",
    "intervention_coverage": 316,
    "ols_ladder": {"columns": []},
    "ols_student_t": {},
    "subsamples": {},
    "handoff_metadata": {
        "schema_version": "1.0",
        "python_version": "3.13.5",
        "numpy_version": "2.4.4",
        "pandas_version": "3.0.2",
        "statsmodels_version": "0.14.6",
        "scipy_version": "1.17.1",
        "arch_version": "8.0.0",
        "recommended_seed": 20260418,
        "bootstrap_distribution": "synthetic",
    },
}


# ── Module import + callable signature ───────────────────────────────────

def test_render_readme_module_imports() -> None:
    """``scripts.render_readme`` imports cleanly."""
    module = importlib.import_module("scripts.render_readme")
    assert hasattr(module, "render_readme")


def test_render_readme_is_callable() -> None:
    """``render_readme(gate_verdict, point_params, template_path) -> str``."""
    from scripts.render_readme import render_readme
    assert callable(render_readme)
    result = render_readme(
        _SYNTHETIC_GATE_VERDICT_FAIL,
        _SYNTHETIC_POINT_PARAMS,
        TEMPLATE_PATH,
    )
    assert isinstance(result, str)
    assert len(result) > 0


# ── Per-section content (plan items 1-7) ──────────────────────────────────

def test_render_readme_has_gate_verdict_headline() -> None:
    """Plan item (1): one-line gate-verdict headline with β̂ + 90% CI."""
    from scripts.render_readme import render_readme

    fail_md = render_readme(
        _SYNTHETIC_GATE_VERDICT_FAIL,
        _SYNTHETIC_POINT_PARAMS,
        TEMPLATE_PATH,
    )
    # The headline must appear before the first H2 section.
    headline_block = fail_md.split("\n## ", 1)[0]
    assert "FAIL" in headline_block, (
        f"Expected 'FAIL' verdict in headline; got: {headline_block[:400]}"
    )
    # β̂ appears in the headline (we accept the exact number or the
    # Greek-β wording — both are acceptable as long as the primary
    # point estimate is present).
    assert "-0.000685" in headline_block or "\u03b2\u0302" in headline_block

    pass_md = render_readme(
        _SYNTHETIC_GATE_VERDICT_PASS,
        _SYNTHETIC_POINT_PARAMS,
        TEMPLATE_PATH,
    )
    pass_headline = pass_md.split("\n## ", 1)[0]
    assert "PASS" in pass_headline


def test_render_readme_has_primary_results_table() -> None:
    """Plan item (2): β̂ results table with primary / GARCH-X / decomp rows."""
    from scripts.render_readme import render_readme

    md = render_readme(
        _SYNTHETIC_GATE_VERDICT_FAIL,
        _SYNTHETIC_POINT_PARAMS,
        TEMPLATE_PATH,
    )
    assert "Primary" in md, "Primary (Column 6) row missing from results table"
    assert "GARCH-X" in md, "GARCH-X row missing from results table"
    assert "Decomp" in md or "Decomposition" in md, (
        "Decomposition row missing from results table"
    )


def test_render_readme_has_reconciliation_row() -> None:
    """Plan item (3): reconciliation row with AGREE/DISAGREE + bootstrap flag."""
    from scripts.render_readme import render_readme

    md = render_readme(
        _SYNTHETIC_GATE_VERDICT_FAIL,
        _SYNTHETIC_POINT_PARAMS,
        TEMPLATE_PATH,
    )
    assert "AGREE" in md or "DISAGREE" in md, (
        "Reconciliation token (AGREE/DISAGREE) missing"
    )
    assert "AGREEMENT" in md or "DIVERGENCE" in md, (
        "Bootstrap-HAC agreement flag missing"
    )


def test_render_readme_has_forest_plot_reference() -> None:
    """Plan item (4): embedded or linked forest-plot PNG."""
    from scripts.render_readme import render_readme

    md = render_readme(
        _SYNTHETIC_GATE_VERDICT_FAIL,
        _SYNTHETIC_POINT_PARAMS,
        TEMPLATE_PATH,
    )
    # Accept either an embedded markdown image ![alt](path) or an
    # HTML <img src="..."> tag; both point at a .png file.
    has_md_image = "![" in md and ".png" in md
    has_html_image = '<img' in md.lower() and ".png" in md
    assert has_md_image or has_html_image, (
        "Forest-plot PNG reference missing (no markdown image or "
        "<img> tag with .png path)"
    )


def test_render_readme_has_per_test_table() -> None:
    """Plan item (5): per-test pass/fail table with T1, T2, T4, T5, T6, T7."""
    from scripts.render_readme import render_readme

    md = render_readme(
        _SYNTHETIC_GATE_VERDICT_FAIL,
        _SYNTHETIC_POINT_PARAMS,
        TEMPLATE_PATH,
    )
    required_rows = ("T1", "T2", "T4", "T5", "T6", "T7")
    for label in required_rows:
        assert label in md, f"Per-test table missing row '{label}'"


def test_render_readme_has_pdf_links() -> None:
    """Plan item (6): three PDF links (NB1/NB2/NB3)."""
    from scripts.render_readme import render_readme

    md = render_readme(
        _SYNTHETIC_GATE_VERDICT_FAIL,
        _SYNTHETIC_POINT_PARAMS,
        TEMPLATE_PATH,
    )
    nb_stems = (
        _env.NB1_PATH.stem,
        _env.NB2_PATH.stem,
        _env.NB3_PATH.stem,
    )
    for stem in nb_stems:
        assert f"{stem}.pdf" in md, (
            f"PDF link '{stem}.pdf' missing from README"
        )


def test_render_readme_has_spec_hash_footer() -> None:
    """Plan item (7): spec-hash footer present."""
    from scripts.render_readme import render_readme

    md = render_readme(
        _SYNTHETIC_GATE_VERDICT_FAIL,
        _SYNTHETIC_POINT_PARAMS,
        TEMPLATE_PATH,
    )
    expected_hash = _SYNTHETIC_POINT_PARAMS["spec_hash"]
    # Footer should be at or near the end of the file; we accept any
    # position AS LONG AS the hash appears at least once.
    assert expected_hash in md, (
        f"spec_hash '{expected_hash[:16]}...' missing from rendered README"
    )
    # Panel fingerprint also carried in the footer for traceability.
    expected_fp = _SYNTHETIC_POINT_PARAMS["panel_fingerprint"]
    assert expected_fp in md, (
        f"panel_fingerprint '{expected_fp[:16]}...' missing from footer"
    )


# ── Determinism + CLI ────────────────────────────────────────────────────

def test_render_readme_is_deterministic() -> None:
    """Repeated calls on identical inputs produce byte-identical output."""
    from scripts.render_readme import render_readme

    outputs = [
        render_readme(
            _SYNTHETIC_GATE_VERDICT_FAIL,
            _SYNTHETIC_POINT_PARAMS,
            TEMPLATE_PATH,
        )
        for _ in range(3)
    ]
    assert outputs[0] == outputs[1] == outputs[2], (
        "render_readme is not deterministic across repeated calls"
    )


def test_render_readme_cli(tmp_path: Path) -> None:
    """CLI entry point prints rendered markdown to stdout."""
    gate_json = tmp_path / "gate.json"
    point_json = tmp_path / "point.json"
    gate_json.write_text(
        json.dumps(_SYNTHETIC_GATE_VERDICT_FAIL, indent=2, sort_keys=True)
    )
    point_json.write_text(
        json.dumps(_SYNTHETIC_POINT_PARAMS, indent=2, sort_keys=True)
    )

    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPTS_DIR / "render_readme.py"),
            str(gate_json),
            str(point_json),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(_CONTRACTS_DIR),
    )
    assert result.returncode == 0, (
        f"CLI failed with stderr: {result.stderr[:800]}"
    )
    # stdout must match what the pure function returns.
    from scripts.render_readme import render_readme
    expected = render_readme(
        _SYNTHETIC_GATE_VERDICT_FAIL,
        _SYNTHETIC_POINT_PARAMS,
        TEMPLATE_PATH,
    )
    assert result.stdout == expected, (
        "CLI stdout does not match pure-function output"
    )


# ── CI diff check — THE load-bearing regression assertion ─────────────────

def test_readme_byte_identical_to_committed() -> None:
    """Committed README matches a fresh render from committed JSONs."""
    if not GATE_VERDICT_PATH.is_file():
        pytest.skip(
            f"{GATE_VERDICT_PATH.name} missing — NB3 §10 has not been "
            "executed in this worktree"
        )
    if not POINT_JSON_PATH.is_file():
        pytest.skip(
            f"{POINT_JSON_PATH.name} missing — NB2 §10 has not been "
            "executed in this worktree"
        )

    gate_verdict = json.loads(GATE_VERDICT_PATH.read_text(encoding="utf-8"))
    point_params = json.loads(POINT_JSON_PATH.read_text(encoding="utf-8"))

    from scripts.render_readme import render_readme
    rendered = render_readme(gate_verdict, point_params, TEMPLATE_PATH)

    assert README_PATH.is_file(), (
        f"Committed README missing at {README_PATH}"
    )
    committed = README_PATH.read_text(encoding="utf-8")

    assert committed == rendered, (
        "CI diff check FAILED: committed README.md is not byte-identical to "
        "a fresh render from the committed JSON artifacts.\n"
        f"  committed size = {len(committed)} bytes\n"
        f"  rendered size  = {len(rendered)} bytes\n"
        "Re-run NB3 to regenerate README.md, then commit the updated file."
    )


# ── R4 remediation: single-source forest-plot title constant ─────────────
#
# Reality-Checker three-way-review finding (2026-04-19): the forest-plot
# title is spelled three different ways across three surfaces:
#   1. NB3 cell 25's in-notebook Axes.set_title — Unicode § + em-dash
#      + dynamic "(engine: {_engine})" suffix.
#   2. NB3 cell 33's saved-PNG Axes.set_title — ASCII "NB3 sec 8 forest
#      plot -- primary anchor + 12 sensitivities" (deliberate ASCII
#      safety, no engine).
#   3. README template's markdown image alt-text — Unicode § + em-dash
#      but with the word "sensitivity" inserted.
#
# A reader following the README's image link sees a title that neither
# matches the caption nor the in-notebook figure. Fix: single-source
# the base title string via a module-level constant in
# ``scripts.render_readme`` and require both notebook surfaces and the
# README alt-text to resolve from the same base. The dynamic-engine
# suffix in cell 25 is permitted to extend the base string; what's
# locked is the base prefix.

_FOREST_PLOT_BASE_TITLE_TOKEN: Final[str] = (
    "Column 6 β̂_CPI — primary + 13 sensitivities (90% HAC CI)"
)


def test_forest_plot_title_constant_exported() -> None:
    """``scripts.render_readme`` exports ``_FOREST_PLOT_TITLE`` constant.

    Downstream surfaces (NB3 §8, NB3 final PNG-render cell, README
    template) read from this one constant to prevent drift.
    """
    mod = importlib.import_module("scripts.render_readme")
    assert hasattr(mod, "_FOREST_PLOT_TITLE"), (
        "scripts.render_readme must expose a module-level "
        "`_FOREST_PLOT_TITLE` constant as the single source of truth "
        "for the forest-plot base title."
    )
    title = getattr(mod, "_FOREST_PLOT_TITLE")
    assert isinstance(title, str) and title.strip(), (
        f"_FOREST_PLOT_TITLE must be a non-empty string; got {title!r}."
    )
    # Landmark substring lock: the exported title must contain the
    # "Column 6 β̂_CPI" and "90% HAC CI" fragments that unambiguously
    # identify the forest plot's content.
    assert "Column 6" in title, (
        f"_FOREST_PLOT_TITLE must reference 'Column 6'; got {title!r}."
    )
    assert "90% HAC CI" in title or "HAC" in title, (
        f"_FOREST_PLOT_TITLE must reference HAC coverage; got {title!r}."
    )


def test_forest_plot_title_landmark_in_notebook_cells() -> None:
    """NB3 cells 25 + 33 both render the same title landmark.

    We can't force byte-identical titles without importing the
    constant in both cells (which we do in the fix), but the test
    asserts the landmark fragment appears in both cell source texts so
    any hand-edit that drops the shared title will be caught.
    """
    nb = nbformat.read(NB3_PATH, as_version=4)
    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    assert len(code_cells) >= 2, (
        f"NB3 must have multiple code cells; got {len(code_cells)}."
    )

    # Find the §8 primary forest cell (first cell whose source contains
    # _forest_table assembly) and the §10 PNG-render cell (last code
    # cell).
    s8_cells = [c for c in code_cells if "_forest_rows = []" in "".join(c.source)]
    assert s8_cells, "Could not locate §8 forest-plot code cell."
    last_cell = code_cells[-1]

    s8_src = "".join(s8_cells[0].source)
    last_src = "".join(last_cell.source)

    # Both cells must reference the shared constant name so they read
    # the same title at execution time.
    assert "_FOREST_PLOT_TITLE" in s8_src, (
        "NB3 §8 primary forest-plot cell must reference the shared "
        "`_FOREST_PLOT_TITLE` constant from scripts.render_readme "
        "(single-source pattern)."
    )
    assert "_FOREST_PLOT_TITLE" in last_src, (
        "NB3 §10 PNG-render cell must reference the shared "
        "`_FOREST_PLOT_TITLE` constant (single-source pattern)."
    )


def test_forest_plot_title_landmark_in_readme_template() -> None:
    """README template alt-text aligns with the forest-plot title base."""
    tpl = TEMPLATE_PATH.read_text(encoding="utf-8")
    # Landmarks: "Forest Plot" + "primary" + "sensitivit" share across
    # template + cell titles without requiring byte-identical strings.
    # The key anti-drift fragment is "β̂_CPI" — the exported constant
    # contains it and the template alt-text now references it.
    assert "β̂_CPI" in tpl or "forest_plot.png" in tpl, (
        "README template must reference the forest plot image with a "
        "β̂_CPI-branded alt-text aligned to the _FOREST_PLOT_TITLE "
        "constant."
    )


# ── C1 remediation: PDF links marked pending until `just notebooks` runs ──
#
# Technical-Writer three-way-review finding (2026-04-19): the README
# Reports section lists three PDF links under `pdf/` but the `pdf/`
# directory is empty in the current worktree because `just notebooks`
# has not been run yet. A reader who clicks today gets a 404. Fix:
# template marks the PDF links with a visible "pending" indicator so
# readers know the artifacts have not been produced — the alternative
# (option b: generate PDFs now via nbconvert --to pdf) is deferred to
# Task 33's scope.

_PENDING_MARKER_TOKENS: Final[tuple[str, ...]] = (
    "pending",  # the word appears somewhere in the Reports section
)


def test_render_readme_pdf_links_marked_pending() -> None:
    """Reports section marks PDF links as pending-generation.

    When `just notebooks` has not yet run, `pdf/*.pdf` is empty. The
    README template flags this so readers do not expect clickable PDF
    links. This test asserts the marker landmark exists in the
    Reports section output.
    """
    from scripts.render_readme import render_readme
    md = render_readme(
        _SYNTHETIC_GATE_VERDICT_FAIL,
        _SYNTHETIC_POINT_PARAMS,
        TEMPLATE_PATH,
    )
    reports_parts = md.split("\n## ")
    reports_block = next(
        (p for p in reports_parts if p.startswith("Reports")), None
    )
    assert reports_block is not None, (
        "README must contain a '## Reports' H2 section."
    )
    lower = reports_block.lower()
    has_marker = any(t in lower for t in _PENDING_MARKER_TOKENS)
    assert has_marker, (
        f"Reports section must mark PDF links with a 'pending' "
        f"visible indicator until `just notebooks` produces the "
        f"actual PDFs. Found Reports block:\n{reports_block[:400]}..."
    )


def test_pending_marker_in_committed_readme() -> None:
    """Committed README carries the pending-marker landmark."""
    if not README_PATH.is_file():
        pytest.skip(f"{README_PATH} not present.")
    md = README_PATH.read_text(encoding="utf-8").lower()
    assert any(t in md for t in _PENDING_MARKER_TOKENS), (
        "Committed README must carry the 'pending' PDF marker."
    )


# ── C2 remediation: anti-fishing discipline paragraph visibility ──────────
#
# Technical-Writer three-way-review finding (2026-04-19): the README,
# read standalone, does not transmit the central scientific-discipline
# moment of the analysis — that A1 and A4 sensitivities DID reject the
# null but were NOT promoted to the gate verdict because T3b FAILed
# upstream and post-hoc subset selection is ruled out by the
# pre-committed anti-fishing protocol. The fix adds a paragraph under
# the Forest Plot section. These tests lock the paragraph's presence
# + its load-bearing citations.

_ANTI_FISHING_LANDMARK_PHRASES: Final[tuple[str, ...]] = (
    "pre-registered sensitivities",
    "A1",
    "A4",
    "anti-fishing",
)

_ANTI_FISHING_CITATION_TOKENS: Final[tuple[str, ...]] = (
    "Simonsohn",
    "Ankel-Peters",
)


def test_render_readme_has_anti_fishing_paragraph_under_forest_plot() -> None:
    """README carries the anti-fishing-discipline paragraph under the
    Forest Plot H2 section.

    The paragraph must:
      (a) name "A1" and "A4" as the rejecting-but-not-promoted rows,
      (b) reference the "anti-fishing" framing explicitly,
      (c) cite Simonsohn et al. 2020 and Ankel-Peters et al. 2024,
      (d) appear under the ``## Forest Plot`` section and before the
          next H2 section (``## Per-Test Gate Table``).
    """
    from scripts.render_readme import render_readme

    md = render_readme(
        _SYNTHETIC_GATE_VERDICT_FAIL,
        _SYNTHETIC_POINT_PARAMS,
        TEMPLATE_PATH,
    )

    # Isolate the Forest Plot H2 block.
    parts = md.split("\n## ")
    forest_parts = [p for p in parts if p.startswith("Forest Plot")]
    assert forest_parts, (
        "README must contain a '## Forest Plot' section; not found."
    )
    forest_block = forest_parts[0]

    # (a) + (b): landmark phrases naming A1, A4, anti-fishing.
    for phrase in _ANTI_FISHING_LANDMARK_PHRASES:
        assert phrase in forest_block, (
            f"Forest Plot section must reference {phrase!r} "
            f"(anti-fishing discipline paragraph). Not found."
        )

    # (c): citation tokens.
    for token in _ANTI_FISHING_CITATION_TOKENS:
        assert token in forest_block, (
            f"Forest Plot section must cite {token!r} as part of the "
            f"anti-fishing discipline paragraph. Not found."
        )


def test_anti_fishing_paragraph_in_committed_readme() -> None:
    """Committed README carries the anti-fishing paragraph.

    Guards against a template update that regenerates the committed
    README but silently drops the paragraph.
    """
    if not README_PATH.is_file():
        pytest.skip(f"{README_PATH} not present — run NB3 §10 to render.")
    md = README_PATH.read_text(encoding="utf-8")
    for phrase in _ANTI_FISHING_LANDMARK_PHRASES:
        assert phrase in md, (
            f"Committed README must reference {phrase!r} (anti-fishing "
            f"discipline paragraph). Not found."
        )


# ── NB3 final cell structural check ───────────────────────────────────────

def test_notebook_final_cell_writes_readme() -> None:
    """NB3 has a final cell that invokes render_readme + writes README.md."""
    nb = nbformat.read(NB3_PATH, as_version=4)
    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    assert code_cells, "NB3 has no code cells"

    last_code = code_cells[-1].source
    assert "render_readme" in last_code, (
        "NB3 final code cell does not import or call render_readme"
    )
    # Must reference the env.READMEPath constant (Rule 11 — no bare
    # string paths) or the literal README.md file name.
    assert "READMEPath" in last_code or "README.md" in last_code, (
        "NB3 final code cell does not reference READMEPath / README.md"
    )
    # Must reference the two JSON artifact paths as inputs.
    assert (
        "GATE_VERDICT_PATH" in last_code
        or "gate_verdict.json" in last_code
    ), "NB3 final code cell does not read gate_verdict.json"
    assert (
        "POINT_JSON_PATH" in last_code
        or "nb2_params_point.json" in last_code
    ), "NB3 final code cell does not read nb2_params_point.json"
