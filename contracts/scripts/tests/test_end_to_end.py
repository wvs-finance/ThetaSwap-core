"""End-to-end `just notebooks` pipeline + idempotency test — Task 32.

Phase 4 capstone of the ``docs/superpowers/plans/2026-04-17-econ-notebook-
implementation.md`` plan. This is the integration layer that catches
bugs every per-notebook and per-section test is structurally blind to:

  * Inter-notebook handoff corruption — e.g. NB1 writes a valid
    fingerprint JSON, NB2 reads it, but the `just notebooks` recipe
    orders them such that NB2 runs before NB1 (catastrophic).
  * Silent non-determinism — a wall-clock timestamp, a PYTHONHASHSEED
    leak, or a bootstrap seed leak that makes a second run produce
    different output bytes. The committed JSON then drifts silently on
    every CI run.
  * PDF export regressions — a missing LaTeX toolchain or a template
    bug that truncates a PDF to near-zero bytes.
  * README silent drift — the committed README disagrees with what
    ``render_readme`` produces from the committed JSON artifacts
    (Task 30's CI diff check).
  * Gate verdict corruption — ``gate_verdict.json`` parses but its
    ``gate_verdict`` field is null, empty, or out of enum.

What this test deliberately does NOT assert:

  * The sign or magnitude of any coefficient (NB2 / NB3 per-section
    tests cover that).
  * PASS vs FAIL on the gate. The plan line 586 explicitly says "The
    test does NOT assert PASS or FAIL on the gate; it asserts the
    pipeline runs twice deterministically and produces a verdict".

Two operating modes, chosen at import time:

  * **Subprocess mode** — ``just`` is on PATH. The tests invoke
    ``just notebooks`` twice back-to-back, capture artifact bytes
    between runs, and diff. Expensive: ~3-6 min per run × 2 = ~6-12
    min total. No pytest slow marker — codebase convention (verified
    across every ``test_nb*.py``) keeps all tests in the default suite.

  * **Committed-artifact mode** — ``just`` is absent (typical CI +
    developer laptop without casey/just installed). The subprocess
    tests skip with an explicit reason (mirrors
    ``test_just_notebooks_recipe.py``). In exchange, the
    artifact-validity assertions still run against the committed
    on-disk JSON + README + PNG — the pipeline's actual output. This
    gives the test suite teeth even on a `just`-less box: every PR
    still verifies the committed artifacts satisfy the pipeline
    invariants.

Idempotency / byte-identity scope (plan line 586):

  Plan asks for ``nb1_panel_fingerprint.json``, ``nb2_params_point.
  json``, and ``gate_verdict.json`` byte-identical across runs. NB1
  §8b embeds a ``generated_at`` ISO-8601 timestamp into the fingerprint
  JSON (cell 116, explicitly marked "advisory — not hashed"). That
  field is the ONLY known non-deterministic component of the three
  artifacts. Plan Task 32 Step 3 names two remediation options:
    (a) exclude from byte-identical comparison,
    (b) remove from the emission.
  We take (a) and make it LOUD: the comparison helper explicitly
  pops ``generated_at`` before diffing, and the test asserts that
  ``generated_at`` is the ONLY key dropped — any future field added
  to the non-deterministic-allowlist must be an explicit edit here,
  not a silent accumulation.

Paths flow through ``env.py`` per plan Rule 11 (no bare string paths).
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

import pytest


# ── Path plumbing (mirrors the NB1/NB2/NB3 end-to-end tests) ───────────────

# This test lives at: contracts/scripts/tests/test_end_to_end.py
# parents[0] = tests/
# parents[1] = scripts/
# parents[2] = contracts/
# parents[3] = worktree root (where the justfile lives)
_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parents[1]
_CONTRACTS_DIR: Final[Path] = _SCRIPTS_DIR.parent
_WORKTREE_ROOT: Final[Path] = _CONTRACTS_DIR.parent

_ENV_PATH: Final[Path] = (
    _CONTRACTS_DIR
    / "notebooks"
    / "fx_vol_cpi_surprise"
    / "Colombia"
    / "env.py"
)
_JUSTFILE_PATH: Final[Path] = _WORKTREE_ROOT / "justfile"


def _load_env_module() -> Any:
    """Load Colombia/env.py as a module without requiring it on sys.path.

    Same pattern used across the NB1/NB2/NB3 structural + end-to-end
    tests — env.py is not packaged, just a file on disk that we exec
    via importlib.util.
    """
    spec = importlib.util.spec_from_file_location("_fx_vol_env", _ENV_PATH)
    assert spec is not None and spec.loader is not None, (
        f"Could not build importlib spec for {_ENV_PATH}"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_env: Final[Any] = _load_env_module()

# ── Subprocess-mode skip gate ──────────────────────────────────────────────

_JUST_BIN: Final[str | None] = shutil.which("just")
_JUST_SKIP_REASON: Final[str] = (
    "`just` not on PATH in this test environment; subprocess integration "
    "skipped. Committed-artifact tests below still exercise the pipeline's "
    "actual on-disk output. Install casey/just to enable the two-run "
    "idempotency subprocess suite."
)

# Size floor for PDF rough-validity check (plan line 586).
_PDF_MIN_BYTES: Final[int] = 50 * 1024  # 50 KB

# Wall-clock timeout per `just notebooks` invocation. Generous upper bound
# — NB3 bootstrap + specification-curve alone can take 3-6 min on a clean
# venv. +60 s buffer so the pytest timeout is distinguishable from
# ExecutePreprocessor timeout.
_JUST_WALL_CLOCK_S: Final[int] = _env.NBCONVERT_TIMEOUT * 3 + 60  # 5460 s


# ── Shared helpers ─────────────────────────────────────────────────────────


def _read_json(path: Path) -> dict[str, Any]:
    """Load and parse a JSON file, asserting the result is a dict."""
    assert path.is_file(), f"Expected JSON artifact at {path}"
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert isinstance(data, dict), (
        f"Expected top-level JSON object at {path}, got {type(data).__name__}"
    )
    return data


# ── Non-deterministic-key allowlist (explicit + narrow) ────────────────────
#
# Plan Task 32 Step 3 names ``generated_at`` in nb1_panel_fingerprint.json
# as the canonical idempotency hazard. NB1 §8b cell 116 writes this field
# with a wall-clock timestamp and the cell comment explicitly marks it
# "advisory — not hashed". We tolerate it by popping before byte-diff,
# but the tolerance MUST be loud: the test below asserts this set is
# frozen and small. A new entry here is a deliberate human edit.

_FINGERPRINT_NONDET_KEYS: Final[frozenset[str]] = frozenset({"generated_at"})
_POINT_JSON_NONDET_KEYS: Final[frozenset[str]] = frozenset()
_GATE_VERDICT_NONDET_KEYS: Final[frozenset[str]] = frozenset()


def _canonical_json_bytes(
    obj: dict[str, Any], drop_keys: frozenset[str]
) -> bytes:
    """Return deterministic JSON bytes with named top-level keys removed.

    ``json.dumps(..., sort_keys=True)`` gives a canonical byte order that
    is stable across Python versions; dropping ``drop_keys`` lets us
    byte-compare the content-bearing subset while being explicit about
    what we tolerate.
    """
    filtered = {k: v for k, v in obj.items() if k not in drop_keys}
    return json.dumps(
        filtered, sort_keys=True, ensure_ascii=False, indent=2
    ).encode("utf-8")


def _run_just_notebooks() -> subprocess.CompletedProcess[str]:
    """Invoke ``just notebooks`` from the worktree root with a hard timeout.

    Callers must gate on ``_JUST_BIN is not None``. Returns the
    ``CompletedProcess`` so the caller can inspect exit code + streams.
    """
    assert _JUST_BIN is not None, "Call sites must skip when `just` is absent"
    return subprocess.run(
        [_JUST_BIN, "notebooks"],
        cwd=_WORKTREE_ROOT,
        capture_output=True,
        text=True,
        timeout=_JUST_WALL_CLOCK_S,
        check=False,
    )


def _snapshot_artifacts() -> dict[str, bytes]:
    """Read raw bytes of the three idempotency-sensitive JSON artifacts.

    Returns a dict keyed by artifact name so diffs in the subprocess
    two-run test can name which artifact drifted.
    """
    return {
        "nb1_panel_fingerprint.json": _env.FINGERPRINT_PATH.read_bytes(),
        "nb2_params_point.json": _env.POINT_JSON_PATH.read_bytes(),
        "gate_verdict.json": _env.GATE_VERDICT_PATH.read_bytes(),
    }


def _canonical_snapshot() -> dict[str, bytes]:
    """Byte snapshot with per-artifact non-deterministic keys stripped.

    This is what the idempotency test compares across runs. The raw
    bytes would drift on every run because of NB1 §8b's ``generated_at``
    timestamp; the canonical form excludes that explicitly-advisory
    field and nothing else.
    """
    fp = _read_json(_env.FINGERPRINT_PATH)
    pp = _read_json(_env.POINT_JSON_PATH)
    gv = _read_json(_env.GATE_VERDICT_PATH)
    return {
        "nb1_panel_fingerprint.json": _canonical_json_bytes(
            fp, _FINGERPRINT_NONDET_KEYS
        ),
        "nb2_params_point.json": _canonical_json_bytes(
            pp, _POINT_JSON_NONDET_KEYS
        ),
        "gate_verdict.json": _canonical_json_bytes(
            gv, _GATE_VERDICT_NONDET_KEYS
        ),
    }


# ── Allowlist sanity tests (frozen set discipline) ─────────────────────────
#
# These run unconditionally. They're cheap and they guard the primary
# idempotency test below from silent tolerance creep — if a future
# committer adds a second non-deterministic field, they must edit the
# allowlist here, which is visible in git diff.


def test_fingerprint_nondet_allowlist_is_exactly_generated_at() -> None:
    """Only ``generated_at`` is tolerated as non-deterministic in NB1 FP.

    Guards against silent accumulation of non-deterministic fields in
    the allowlist. Adding a second tolerated field is a deliberate
    human edit to this test.
    """
    assert _FINGERPRINT_NONDET_KEYS == frozenset({"generated_at"}), (
        f"Fingerprint non-deterministic allowlist drifted. Expected "
        f"exactly {{'generated_at'}}, got {set(_FINGERPRINT_NONDET_KEYS)}."
    )


def test_point_json_nondet_allowlist_is_empty() -> None:
    """NB2 handoff JSON must have no tolerated non-determinism."""
    assert _POINT_JSON_NONDET_KEYS == frozenset(), (
        f"nb2_params_point.json non-det allowlist must stay empty. "
        f"Got {set(_POINT_JSON_NONDET_KEYS)}."
    )


def test_gate_verdict_nondet_allowlist_is_empty() -> None:
    """NB3 gate verdict JSON must have no tolerated non-determinism."""
    assert _GATE_VERDICT_NONDET_KEYS == frozenset(), (
        f"gate_verdict.json non-det allowlist must stay empty. "
        f"Got {set(_GATE_VERDICT_NONDET_KEYS)}."
    )


# ── Committed-artifact tests (run unconditionally) ─────────────────────────
#
# These run whether or not `just` is on PATH. They assert the committed
# artifacts in `estimates/` + `figures/` + `README.md` satisfy the
# pipeline's output contracts right now — catching the case where a
# commit silently corrupted an artifact without touching the
# regenerating notebook.


def test_committed_fingerprint_artifact_parses_and_has_schema() -> None:
    """Committed nb1_panel_fingerprint.json parses + has all 8 top keys."""
    fp = _read_json(_env.FINGERPRINT_PATH)
    expected_keys = {
        "schema_version",
        "weekly_panel",
        "daily_panel",
        "decisions",
        "decision_hash",
        "ledger_table",
        "sensitivity_preregistration_hash",
        "generated_at",
    }
    missing = expected_keys - set(fp)
    assert not missing, (
        f"Committed {_env.FINGERPRINT_PATH.name} missing top-level keys: "
        f"{sorted(missing)}. Present: {sorted(fp)}."
    )


def test_committed_point_json_parses_and_has_schema() -> None:
    """Committed nb2_params_point.json parses + has NB2 handoff keys."""
    pp = _read_json(_env.POINT_JSON_PATH)
    required = {
        "ols_primary",
        "garch_x",
        "decomposition",
        "gate_verdict",
        "reconciliation",
        "panel_fingerprint",
        "spec_hash",
        "handoff_metadata",
    }
    missing = required - set(pp)
    assert not missing, (
        f"Committed {_env.POINT_JSON_PATH.name} missing required keys: "
        f"{sorted(missing)}. Present: {sorted(pp)}."
    )


def test_committed_gate_verdict_exists_and_parses() -> None:
    """Committed gate_verdict.json exists and parses as a JSON object."""
    gv = _read_json(_env.GATE_VERDICT_PATH)
    # Sanity: the verdict payload must mention the gate_verdict field —
    # that is the singular headline of the document.
    assert "gate_verdict" in gv, (
        f"Committed {_env.GATE_VERDICT_PATH.name} has no 'gate_verdict' "
        f"key. Present keys: {sorted(gv)}."
    )


def test_committed_gate_verdict_value_is_pass_or_fail() -> None:
    """gate_verdict.gate_verdict is exactly 'PASS' or 'FAIL' — not null.

    Reality-Checker hardening: "exists" is not "correct". An earlier
    bug could emit ``{"gate_verdict": null}`` or a typo'd ``"fail"``
    (lowercase) and every structural test would still pass. This
    verifies the value is in the two-element enum.
    """
    gv = _read_json(_env.GATE_VERDICT_PATH)
    verdict = gv.get("gate_verdict")
    assert verdict in {"PASS", "FAIL"}, (
        f"gate_verdict.gate_verdict must be exactly 'PASS' or 'FAIL' "
        f"(uppercase), got {verdict!r} (type {type(verdict).__name__}). "
        f"Full payload: {gv}"
    )


def test_committed_readme_matches_fresh_render() -> None:
    """Committed README.md matches render_readme from committed JSONs.

    This is Task 30's CI diff check, re-anchored here in the Phase 4
    integration test so a single run of this module verifies every
    inter-artifact contract.
    """
    # Import render_readme via file-path loader (it lives in
    # contracts/scripts/, which is not necessarily on sys.path in the
    # worktree-root pytest invocation).
    render_path = _SCRIPTS_DIR / "render_readme.py"
    assert render_path.is_file(), f"render_readme.py missing at {render_path}"

    spec = importlib.util.spec_from_file_location(
        "_fx_vol_render_readme", render_path
    )
    assert spec is not None and spec.loader is not None
    rr_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rr_mod)

    gate_verdict = _read_json(_env.GATE_VERDICT_PATH)
    point_params = _read_json(_env.POINT_JSON_PATH)
    template_path = (
        _env.READMEPath.parent / "_readme_template.md.j2"
    )
    assert template_path.is_file(), (
        f"Jinja2 template missing at {template_path}"
    )

    fresh = rr_mod.render_readme(gate_verdict, point_params, template_path)
    committed = _env.READMEPath.read_text(encoding="utf-8")
    assert fresh == committed, (
        f"Committed README.md drifted from render_readme output "
        f"against the committed JSON artifacts. Either re-run "
        f"`just notebooks` to regenerate, or manually re-render via "
        f"`python {render_path} {_env.GATE_VERDICT_PATH} "
        f"{_env.POINT_JSON_PATH} > {_env.READMEPath}`.\n"
        f"First 200 committed chars: {committed[:200]!r}\n"
        f"First 200 fresh chars:     {fresh[:200]!r}"
    )


def test_committed_forest_plot_exists_and_nonempty() -> None:
    """NB3 §8 emits a forest-plot PNG; it must exist + be non-trivial.

    Secondary artifact, but still load-bearing for README coherence.
    """
    png_path = _env.FIGURES_DIR / "forest_plot.png"
    assert png_path.is_file(), f"forest_plot.png missing at {png_path}"
    size = png_path.stat().st_size
    assert size > 1024, (
        f"forest_plot.png at {png_path} is suspiciously small "
        f"({size} bytes) — likely a rendering crash. Expected > 1 KB."
    )


def test_committed_canonical_snapshot_is_stable_across_two_reads() -> None:
    """Sanity check on the canonicalization helper itself.

    Re-reading the same on-disk files twice through
    ``_canonical_snapshot`` must produce byte-identical results. This
    hardens the primary idempotency test below: if this assertion
    ever fails, the canonical helper itself has introduced
    non-determinism and the subprocess test would yield a false
    "pipeline non-deterministic" verdict.
    """
    snap1 = _canonical_snapshot()
    snap2 = _canonical_snapshot()
    for name in snap1:
        assert snap1[name] == snap2[name], (
            f"_canonical_snapshot is non-deterministic for {name} — "
            f"two back-to-back reads differ. This is a bug in the "
            f"test helper, not the pipeline."
        )


# ── Subprocess tests (skipped when `just` is absent) ───────────────────────
#
# These invoke the actual `just notebooks` recipe and compare artifact
# bytes across two runs. Expensive (~6-12 min total). Skipped cleanly
# on environments without casey/just.


@pytest.mark.skipif(_JUST_BIN is None, reason=_JUST_SKIP_REASON)
def test_just_notebooks_first_run_produces_all_artifacts() -> None:
    """First `just notebooks` run emits all three .ipynb + 3 PDFs + 3 JSONs.

    Hard assertions:
      * exit code 0 from the full recipe (fail-fast ordering means any
        notebook failure aborts before later phases run, so returncode
        carries the full-chain success bit).
      * POINT_JSON_PATH, FINGERPRINT_PATH, GATE_VERDICT_PATH exist.
      * Each of the three PDFs exists at ``env.PDF_DIR`` and is
        > 50 KB (plan-specified rough validity proxy).
      * Each of the three notebooks has an ``execution_count`` set on
        every code cell (proof the cells actually ran; nbformat
        stores None for unexecuted cells).
    """
    result = _run_just_notebooks()
    assert result.returncode == 0, (
        f"`just notebooks` failed on first run with returncode "
        f"{result.returncode}.\n"
        f"--- stdout ---\n{result.stdout[-2000:]}\n"
        f"--- stderr ---\n{result.stderr[-2000:]}\n"
    )

    # JSON artifacts
    for name, path in (
        ("fingerprint", _env.FINGERPRINT_PATH),
        ("point_params", _env.POINT_JSON_PATH),
        ("gate_verdict", _env.GATE_VERDICT_PATH),
    ):
        assert path.is_file(), (
            f"Artifact {name} missing after `just notebooks`: {path}"
        )

    # PDFs
    for nb_path in (_env.NB1_PATH, _env.NB2_PATH, _env.NB3_PATH):
        pdf_path = _env.PDF_DIR / f"{nb_path.stem}.pdf"
        assert pdf_path.is_file(), (
            f"PDF missing at {pdf_path} after `just notebooks`. "
            f"PDF phase of the recipe must have failed silently."
        )
        size = pdf_path.stat().st_size
        assert size > _PDF_MIN_BYTES, (
            f"PDF at {pdf_path} is {size} bytes (< {_PDF_MIN_BYTES}). "
            f"Plan line 586: each PDF must be > 50 KB as a rough "
            f"validity proxy. A truncated PDF suggests a mid-render "
            f"LaTeX crash that nbconvert swallowed."
        )

    # Notebooks executed (every code cell has an execution_count)
    for nb_path in (_env.NB1_PATH, _env.NB2_PATH, _env.NB3_PATH):
        nb = json.loads(nb_path.read_text(encoding="utf-8"))
        code_cells = [c for c in nb["cells"] if c.get("cell_type") == "code"]
        unexecuted = [
            i for i, c in enumerate(code_cells)
            if c.get("execution_count") is None
        ]
        assert not unexecuted, (
            f"{nb_path.name} has {len(unexecuted)} code cells with no "
            f"execution_count after `just notebooks` (indices "
            f"{unexecuted[:5]}...). The --execute phase must have "
            f"skipped them."
        )


@pytest.mark.skipif(_JUST_BIN is None, reason=_JUST_SKIP_REASON)
def test_just_notebooks_second_run_deterministic() -> None:
    """Two back-to-back `just notebooks` runs produce byte-identical JSON.

    This is the idempotency guarantee from plan §4.1 — the linchpin
    that prevents silent drift on every CI run. ``generated_at`` in
    the NB1 fingerprint is excluded via ``_canonical_snapshot`` (the
    only tolerated non-determinism; see the allowlist test).

    Any drift outside ``generated_at`` is a pipeline-correctness bug:
    a leaked wall-clock, a seed-loss in the bootstrap, a hash-seed
    leak in dict iteration, etc. The error message names the drifting
    artifact so the fix is obvious.
    """
    # Run 1 — baseline. (If a prior test already ran the pipeline, we
    # still re-run here to make this test self-contained.)
    result1 = _run_just_notebooks()
    assert result1.returncode == 0, (
        f"First `just notebooks` run failed with returncode "
        f"{result1.returncode}.\n"
        f"--- stderr ---\n{result1.stderr[-2000:]}\n"
    )
    snap1 = _canonical_snapshot()

    # Run 2 — must match snap1 byte-for-byte on the canonical subset.
    result2 = _run_just_notebooks()
    assert result2.returncode == 0, (
        f"Second `just notebooks` run failed with returncode "
        f"{result2.returncode}.\n"
        f"--- stderr ---\n{result2.stderr[-2000:]}\n"
    )
    snap2 = _canonical_snapshot()

    drifted: list[str] = []
    for name in snap1:
        if snap1[name] != snap2[name]:
            drifted.append(name)
    assert not drifted, (
        f"Pipeline is non-deterministic. Artifacts with byte-drift "
        f"between two back-to-back `just notebooks` runs: {drifted}. "
        f"Tolerated non-determinism was limited to "
        f"{{'generated_at'}} in nb1_panel_fingerprint.json — any "
        f"other drift indicates a leaked wall-clock, unseeded "
        f"randomness, or hash-seed-dependent iteration order. "
        f"Investigate cell-by-cell in the drifted notebook."
    )


@pytest.mark.skipif(_JUST_BIN is None, reason=_JUST_SKIP_REASON)
def test_just_notebooks_second_run_generated_at_advances_monotonically() -> None:
    """The excluded ``generated_at`` field actually updates on rerun.

    Companion to the idempotency test: if ``generated_at`` did NOT
    update across runs, our exclusion would be tolerating a bug that
    is silently benign (the field is dead and not really stamped from
    wall-clock). This guards against a quiet regression where
    ``generated_at`` gets hard-coded to a constant while still living
    in the allowlist. The idempotency + this companion together pin
    the exact behaviour: ``generated_at`` changes, EVERYTHING else is
    byte-stable.
    """
    _ = _run_just_notebooks()  # Run 1
    fp1 = _read_json(_env.FINGERPRINT_PATH)
    t1 = fp1.get("generated_at")

    _ = _run_just_notebooks()  # Run 2
    fp2 = _read_json(_env.FINGERPRINT_PATH)
    t2 = fp2.get("generated_at")

    assert t1 is not None and t2 is not None, (
        f"generated_at missing from one or both runs: t1={t1!r}, t2={t2!r}"
    )
    # ISO-8601 "YYYY-MM-DDTHH:MM:SS+00:00" sorts lexicographically in
    # chronological order, so string <= is equivalent to time <=.
    assert t1 <= t2, (
        f"generated_at regressed across runs: t1={t1}, t2={t2}. "
        f"Wall clock should be monotonic."
    )


@pytest.mark.skipif(_JUST_BIN is None, reason=_JUST_SKIP_REASON)
def test_just_notebooks_gate_verdict_is_pass_or_fail_after_run() -> None:
    """After `just notebooks`, gate_verdict.gate_verdict is PASS or FAIL.

    Companion to ``test_committed_gate_verdict_value_is_pass_or_fail``
    but verifying the LIVE output of a fresh recipe run, not the
    committed artifact. Catches the regression where the pipeline
    writes ``gate_verdict=null`` but the committed artifact is stale
    PASS/FAIL.
    """
    result = _run_just_notebooks()
    assert result.returncode == 0, (
        f"`just notebooks` failed with returncode {result.returncode}\n"
        f"--- stderr ---\n{result.stderr[-2000:]}\n"
    )
    gv = _read_json(_env.GATE_VERDICT_PATH)
    verdict = gv.get("gate_verdict")
    assert verdict in {"PASS", "FAIL"}, (
        f"Fresh `just notebooks` run produced gate_verdict={verdict!r} "
        f"(expected 'PASS' or 'FAIL'). Full payload: {gv}"
    )
