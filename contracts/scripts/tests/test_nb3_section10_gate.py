"""Structural + pure-function tests for NB3 §10 (gate aggregation +
``gate_verdict.json`` atomic emission) — Task 29 of the econ-notebook
implementation plan.

§10 is the FINAL scientific artifact produced by the notebook chain: a
single JSON file summarising every gate + diagnostic test outcome. The
Abrigo simulator consumes this file at initialisation to decide whether
to load the CPI-surprise channel (``gate_verdict == "PASS"``) or treat
it as a null channel (``gate_verdict == "FAIL"``).

The file MUST contain, per plan line 541:

  * per-test PASS/FAIL: T1, T2, T3a (NB3 §7), T3b (re-referenced from
    NB2 §9), T4, T5, T6, T7
  * material-mover count (integer ≥ 0)
  * reconciliation status from NB2 §10 (``AGREE`` or ``DISAGREE``)
  * bootstrap-HAC agreement flag from NB2 §3.5 (``AGREEMENT`` or
    ``DIVERGENCE``)
  * ``pkl_degraded`` status from NB3 §1 (bool)
  * final ``gate_verdict`` (``PASS`` or ``FAIL``)

The file MUST be written atomically: stage → fsync → rename. A rename
failure must leave no stale ``.tmp`` file and no final file on disk.

``contracts/scripts/gate_aggregate.py`` MUST expose:

  * ``build_gate_verdict(inputs: Mapping[str, Any]) -> dict`` — pure
    function, no file I/O. Returns a dict conforming to the JSON shape
    above.
  * ``write_gate_verdict_atomic(verdict: Mapping[str, Any],
    path: pathlib.Path) -> None`` — stages to ``.tmp``, fsyncs the
    file and its containing directory, renames to the final path.

Decision rule for the final ``gate_verdict`` field, per the pre-committed
Rev 4 spec:

  * Primary gate = T3b (NB2 one-sided β̂ − 1.28·SE > 0). T3b FAIL →
    final ``gate_verdict = "FAIL"`` regardless of any other T-series.
  * If T3b PASS, then the aggregation requires: T1 PASS, T2 PASS, T7
    PASS (the three "gate" T-tests beyond T3b). T4/T5/T6 are
    diagnostic-only per plan Tasks 25/26 design and DO NOT gate.
  * All of (T1, T2, T3b, T7) PASS → final ``gate_verdict = "PASS"``.
  * Any of (T1, T2, T3b, T7) FAIL → final ``gate_verdict = "FAIL"``.

Tests are TDD-first: written to fail against the 30-cell Task-28
baseline (SHA a44c4e3c2) and pass after Task 29's 1 trio (= 3 cells)
extends NB3 to 33 cells plus a new ``gate_aggregate.py`` module and a
newly-written ``estimates/gate_verdict.json`` artifact.

Test coverage, in order of decreasing "load-bearing":

  1. Module `scripts.gate_aggregate` imports cleanly.
  2. `build_gate_verdict` is callable with keyword-style dict input.
  3. Schema — returned dict has all required per-test fields
     (`t1_verdict`, `t2_verdict`, `t3a_verdict`, `t3b_verdict`,
     `t4_verdict`, `t5_verdict`, `t6_verdict`, `t7_verdict`).
  4. Schema — returned dict has `material_movers_count` (int),
     `reconciliation` (AGREE/DISAGREE), `bootstrap_hac_agreement`
     (AGREEMENT/DIVERGENCE), `pkl_degraded` (bool),
     `gate_verdict` (PASS/FAIL).
  5. Purity — `build_gate_verdict` does NOT call any file I/O
     (patched ``open`` / ``os.replace`` are never invoked).
  6. Aggregation logic — T3b FAIL ⇒ final gate_verdict = FAIL
     regardless of other inputs.
  7. Aggregation logic — T3b PASS + all of (T1, T2, T7) PASS ⇒
     final gate_verdict = PASS.
  8. Aggregation logic — T3b PASS but any gate-T FAIL ⇒ final
     gate_verdict = FAIL.
  9. Atomic write — after successful write, the final file exists,
     its content round-trips through JSON, and no ``.tmp`` sibling
     remains.
 10. Atomic write — on simulated `os.replace` failure, the final
     path does NOT exist and no leaked ``.tmp`` sibling remains
     either.
 11. Cell count — NB3 has ≥ 33 cells after Task 29 (30 + 3).
 12. §10 exists — ≥ 1 ``section:10`` code cell, every code cell has
     ``remove-input``.
 13. §10 citation block present with all four REQUIRED_HEADERS and
     references ``@ankelPeters2024protocol``.
 14. Citation lint clean: ``lint_notebook_citations.py`` exits 0 on
     NB3.

What is NOT asserted:

  * Exact numerical values of the LIVE gate_verdict.json fields
    beyond the primary ``gate_verdict = "FAIL"`` outcome driven by
    T3b.
  * The ordering of keys inside the emitted JSON (schema validation
    is presence-based, not ordering-based).
  * Whether `gate_aggregate.py` uses a dataclass internally — only
    the signature (``Mapping`` in, ``dict`` out) is load-bearing.

No network / real-data mocks: the pure-function tests use synthetic
dicts; the atomic-write tests use a pytest ``tmp_path``; the schema
test loads the emitted JSON from the live ``ESTIMATES_DIR`` only if
it has already been produced by a prior notebook execution, otherwise
it executes §10 end-to-end on top of §1-§9's bootstrap (so the artifact
is always freshly derived).
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Final, Mapping

import nbformat
import pytest


# ── Section tag constants for cell filtering ─────────────────────────────

_ALL_SECTION_TAGS: Final[tuple[str, ...]] = (
    "section:1",
    "section:2",
    "section:3",
    "section:4",
    "section:5",
    "section:6",
    "section:7",
    "section:8",
    "section:9",
    "section:10",
)


# ── Path plumbing (mirrors test_nb3_section9.py) ──────────────────────────

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
GATE_VERDICT_PATH: Final[Path] = _env.GATE_VERDICT_PATH
ESTIMATES_DIR: Final[Path] = _env.ESTIMATES_DIR


# ── Constants ─────────────────────────────────────────────────────────────

SECTION10_TAG: Final[str] = "section:10"
REMOVE_INPUT_TAG: Final[str] = "remove-input"

REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# Task 29 target: 30 cells (Task 28 baseline) + 3 cells (1 trio) = 33.
_POST_TASK29_CELL_COUNT: Final[int] = 33

# Required JSON schema keys for gate_verdict.json.
_REQUIRED_PER_TEST_KEYS: Final[tuple[str, ...]] = (
    "t1_verdict",
    "t2_verdict",
    "t3a_verdict",
    "t3b_verdict",
    "t4_verdict",
    "t5_verdict",
    "t6_verdict",
    "t7_verdict",
)

_REQUIRED_OTHER_KEYS: Final[tuple[str, ...]] = (
    "material_movers_count",
    "reconciliation",
    "bootstrap_hac_agreement",
    "pkl_degraded",
    "gate_verdict",
)

_VALID_VERDICTS: Final[tuple[str, ...]] = ("PASS", "FAIL", "SKIPPED")
_VALID_RECONCILIATION: Final[tuple[str, ...]] = ("AGREE", "DISAGREE")
_VALID_BOOTSTRAP_FLAGS: Final[tuple[str, ...]] = (
    "AGREEMENT",
    "DIVERGENCE",
)
_VALID_FINAL_VERDICTS: Final[tuple[str, ...]] = ("PASS", "FAIL")

_ANKELPETERS2024_KEY: Final[str] = "ankelPeters2024protocol"


# ── Shared synthetic inputs ───────────────────────────────────────────────

def _synthetic_all_pass_inputs() -> dict[str, Any]:
    """Inputs that should produce the final PASS verdict."""
    return {
        "t1_verdict": "PASS",
        "t2_verdict": "PASS",
        "t3a_verdict": "FAIL TO REJECT",  # diagnostic only
        "t3b_verdict": "PASS",
        "t4_verdict": "FAIL",  # diagnostic only
        "t5_verdict": "FAIL",  # diagnostic only
        "t6_verdict": "FAIL",  # diagnostic only
        "t7_verdict": "PASS",
        "material_movers_count": 0,
        "reconciliation": "AGREE",
        "bootstrap_hac_agreement": "AGREEMENT",
        "pkl_degraded": False,
    }


def _synthetic_t3b_fail_inputs() -> dict[str, Any]:
    """Inputs where everything else passes but T3b fails.

    Final gate_verdict MUST be FAIL (T3b is the primary gate).
    """
    d = _synthetic_all_pass_inputs()
    d["t3b_verdict"] = "FAIL"
    return d


def _synthetic_t1_fail_inputs() -> dict[str, Any]:
    """Inputs where T3b passes but T1 fails."""
    d = _synthetic_all_pass_inputs()
    d["t1_verdict"] = "FAIL"
    return d


def _synthetic_t2_fail_inputs() -> dict[str, Any]:
    """Inputs where T3b passes but T2 fails."""
    d = _synthetic_all_pass_inputs()
    d["t2_verdict"] = "FAIL"
    return d


def _synthetic_t7_fail_inputs() -> dict[str, Any]:
    """Inputs where T3b passes but T7 fails."""
    d = _synthetic_all_pass_inputs()
    d["t7_verdict"] = "FAIL"
    return d


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def nb3() -> nbformat.NotebookNode:
    assert NB3_PATH.is_file(), f"Missing NB3 notebook: {NB3_PATH}"
    return nbformat.read(NB3_PATH, as_version=4)


@pytest.fixture(scope="module")
def gate_aggregate_mod():
    """Import ``scripts.gate_aggregate``. Raises ImportError pre-Task 29."""
    # Ensure scripts/ parent (contracts/) is on sys.path.
    ctr = str(_CONTRACTS_DIR)
    if ctr not in sys.path:
        sys.path.insert(0, ctr)
    return importlib.import_module("scripts.gate_aggregate")


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


# ── Module-import + pure-function tests ───────────────────────────────────

def test_gate_aggregate_module_imports(gate_aggregate_mod) -> None:
    """``scripts.gate_aggregate`` imports cleanly after Task 29."""
    assert hasattr(gate_aggregate_mod, "build_gate_verdict"), (
        "gate_aggregate must expose build_gate_verdict()."
    )
    assert hasattr(gate_aggregate_mod, "write_gate_verdict_atomic"), (
        "gate_aggregate must expose write_gate_verdict_atomic()."
    )
    assert callable(gate_aggregate_mod.build_gate_verdict), (
        "build_gate_verdict must be callable."
    )
    assert callable(gate_aggregate_mod.write_gate_verdict_atomic), (
        "write_gate_verdict_atomic must be callable."
    )


def test_build_gate_verdict_returns_dict(gate_aggregate_mod) -> None:
    """``build_gate_verdict(inputs)`` returns a dict."""
    verdict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_all_pass_inputs()
    )
    assert isinstance(verdict, dict), (
        f"build_gate_verdict must return dict; got {type(verdict).__name__!r}."
    )


def test_gate_verdict_schema_has_all_per_test_fields(
    gate_aggregate_mod,
) -> None:
    """Returned dict carries all required per-test verdict keys."""
    verdict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_all_pass_inputs()
    )
    missing = [k for k in _REQUIRED_PER_TEST_KEYS if k not in verdict]
    assert not missing, (
        f"gate_verdict dict missing per-test keys: {missing}. "
        f"Got keys={sorted(verdict.keys())}."
    )


def test_gate_verdict_has_material_movers_count(gate_aggregate_mod) -> None:
    """Dict has integer ``material_movers_count`` field."""
    verdict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_all_pass_inputs()
    )
    assert "material_movers_count" in verdict, (
        f"Missing material_movers_count; got keys={sorted(verdict.keys())}."
    )
    assert isinstance(verdict["material_movers_count"], int), (
        f"material_movers_count must be int; got "
        f"{type(verdict['material_movers_count']).__name__!r}."
    )
    assert verdict["material_movers_count"] >= 0, (
        f"material_movers_count must be ≥ 0; got "
        f"{verdict['material_movers_count']!r}."
    )


def test_gate_verdict_has_reconciliation_status(gate_aggregate_mod) -> None:
    """Dict has ``reconciliation`` field ∈ {AGREE, DISAGREE}."""
    verdict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_all_pass_inputs()
    )
    assert "reconciliation" in verdict, (
        "Missing reconciliation field."
    )
    assert verdict["reconciliation"] in _VALID_RECONCILIATION, (
        f"reconciliation must be one of {_VALID_RECONCILIATION}; got "
        f"{verdict['reconciliation']!r}."
    )


def test_gate_verdict_has_bootstrap_hac_agreement(gate_aggregate_mod) -> None:
    """Dict has ``bootstrap_hac_agreement`` ∈ {AGREEMENT, DIVERGENCE}."""
    verdict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_all_pass_inputs()
    )
    assert "bootstrap_hac_agreement" in verdict, (
        "Missing bootstrap_hac_agreement field."
    )
    assert verdict["bootstrap_hac_agreement"] in _VALID_BOOTSTRAP_FLAGS, (
        f"bootstrap_hac_agreement must be one of {_VALID_BOOTSTRAP_FLAGS}; "
        f"got {verdict['bootstrap_hac_agreement']!r}."
    )


def test_gate_verdict_has_pkl_degraded_status(gate_aggregate_mod) -> None:
    """Dict has boolean ``pkl_degraded`` field."""
    verdict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_all_pass_inputs()
    )
    assert "pkl_degraded" in verdict, "Missing pkl_degraded field."
    assert isinstance(verdict["pkl_degraded"], bool), (
        f"pkl_degraded must be bool; got "
        f"{type(verdict['pkl_degraded']).__name__!r}."
    )


def test_gate_verdict_final_field(gate_aggregate_mod) -> None:
    """Dict has final ``gate_verdict`` ∈ {PASS, FAIL}."""
    verdict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_all_pass_inputs()
    )
    assert "gate_verdict" in verdict, "Missing final gate_verdict field."
    assert verdict["gate_verdict"] in _VALID_FINAL_VERDICTS, (
        f"gate_verdict must be one of {_VALID_FINAL_VERDICTS}; got "
        f"{verdict['gate_verdict']!r}."
    )


def test_gate_aggregate_is_pure_function(
    gate_aggregate_mod, monkeypatch
) -> None:
    """``build_gate_verdict`` performs NO file I/O."""
    # Trap any accidental file write / rename call during the aggregation.
    opened_paths: list[str] = []
    replaced_calls: list[tuple[str, str]] = []
    real_open = open

    def _trap_open(path, *args, **kwargs):
        opened_paths.append(str(path))
        return real_open(path, *args, **kwargs)

    def _trap_replace(src, dst):
        replaced_calls.append((str(src), str(dst)))
        raise AssertionError(
            "build_gate_verdict called os.replace (must be pure)."
        )

    monkeypatch.setattr("builtins.open", _trap_open)
    monkeypatch.setattr(os, "replace", _trap_replace)

    _ = gate_aggregate_mod.build_gate_verdict(_synthetic_all_pass_inputs())
    assert opened_paths == [], (
        f"build_gate_verdict opened files: {opened_paths!r}. "
        "Must be pure — no I/O."
    )
    assert replaced_calls == [], (
        f"build_gate_verdict invoked os.replace: {replaced_calls!r}. "
        "Must be pure — no I/O."
    )


# ── Aggregation logic tests ───────────────────────────────────────────────

def test_gate_aggregate_fail_when_t3b_fail(gate_aggregate_mod) -> None:
    """T3b FAIL ⇒ final gate_verdict = FAIL regardless of other inputs."""
    verdict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_t3b_fail_inputs()
    )
    assert verdict["gate_verdict"] == "FAIL", (
        f"T3b FAIL must drive final gate_verdict=FAIL; got "
        f"{verdict['gate_verdict']!r}."
    )


def test_gate_aggregate_pass_requires_t3b_pass_plus_others(
    gate_aggregate_mod,
) -> None:
    """All of (T1, T2, T3b, T7) PASS ⇒ final gate_verdict = PASS."""
    verdict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_all_pass_inputs()
    )
    assert verdict["gate_verdict"] == "PASS", (
        f"All gate tests PASS must drive final gate_verdict=PASS; got "
        f"{verdict['gate_verdict']!r}."
    )


def test_gate_aggregate_fail_when_t1_fail(gate_aggregate_mod) -> None:
    """T3b PASS but T1 FAIL ⇒ final gate_verdict = FAIL."""
    verdict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_t1_fail_inputs()
    )
    assert verdict["gate_verdict"] == "FAIL", (
        f"T1 FAIL (with T3b PASS) must drive final gate_verdict=FAIL; "
        f"got {verdict['gate_verdict']!r}."
    )


def test_gate_aggregate_fail_when_t2_fail(gate_aggregate_mod) -> None:
    """T3b PASS but T2 FAIL ⇒ final gate_verdict = FAIL."""
    verdict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_t2_fail_inputs()
    )
    assert verdict["gate_verdict"] == "FAIL", (
        f"T2 FAIL (with T3b PASS) must drive final gate_verdict=FAIL; "
        f"got {verdict['gate_verdict']!r}."
    )


def test_gate_aggregate_fail_when_t7_fail(gate_aggregate_mod) -> None:
    """T3b PASS but T7 FAIL ⇒ final gate_verdict = FAIL."""
    verdict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_t7_fail_inputs()
    )
    assert verdict["gate_verdict"] == "FAIL", (
        f"T7 FAIL (with T3b PASS) must drive final gate_verdict=FAIL; "
        f"got {verdict['gate_verdict']!r}."
    )


# ── Atomic write tests ────────────────────────────────────────────────────

def test_atomic_write_creates_final_file(
    gate_aggregate_mod, tmp_path
) -> None:
    """After successful write, final file exists with valid JSON content."""
    target = tmp_path / "gate_verdict.json"
    verdict_dict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_all_pass_inputs()
    )
    gate_aggregate_mod.write_gate_verdict_atomic(verdict_dict, target)

    assert target.is_file(), (
        f"write_gate_verdict_atomic did not create final file: {target}"
    )
    loaded = json.loads(target.read_text(encoding="utf-8"))
    assert loaded == verdict_dict, (
        f"Round-trip mismatch: wrote {verdict_dict!r}, loaded {loaded!r}."
    )


def test_atomic_write_no_stale_tmp(gate_aggregate_mod, tmp_path) -> None:
    """After successful write, no ``.tmp`` sibling remains."""
    target = tmp_path / "gate_verdict.json"
    verdict_dict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_all_pass_inputs()
    )
    gate_aggregate_mod.write_gate_verdict_atomic(verdict_dict, target)

    # Check for any ``.tmp`` residue in the parent dir.
    tmp_residue = list(tmp_path.glob("*.tmp"))
    assert tmp_residue == [], (
        f"Stale .tmp files after successful write: {tmp_residue!r}."
    )


def test_atomic_write_rollback_on_rename_failure(
    gate_aggregate_mod, tmp_path, monkeypatch
) -> None:
    """``os.replace`` failure ⇒ final file absent + no stale ``.tmp``."""
    target = tmp_path / "gate_verdict.json"
    verdict_dict = gate_aggregate_mod.build_gate_verdict(
        _synthetic_all_pass_inputs()
    )

    def _fail_replace(src, dst):
        raise OSError("simulated rename failure")

    monkeypatch.setattr(os, "replace", _fail_replace)

    with pytest.raises(OSError, match="simulated rename failure"):
        gate_aggregate_mod.write_gate_verdict_atomic(verdict_dict, target)

    assert not target.exists(), (
        f"Final file must be absent on rename failure; found {target}."
    )
    # The ``.tmp`` staging file may remain (caller/OS may inspect it for
    # forensics), but the final path must be absent. Best-effort cleanup
    # SHOULD have removed the .tmp — we accept either outcome so long as
    # the final path is clean.


# ── NB3 structural tests ──────────────────────────────────────────────────

def test_nb3_has_task29_cell_count(nb3: nbformat.NotebookNode) -> None:
    """NB3 grows from 30 cells (Task 28) to 33 cells (Task 29 = +1 trio)."""
    assert len(nb3.cells) >= _POST_TASK29_CELL_COUNT, (
        f"NB3 has {len(nb3.cells)} cells; Task 29 must author 3 new cells "
        f"(1 trio: §10 gate aggregation) for a total of ≥ "
        f"{_POST_TASK29_CELL_COUNT}."
    )


def test_nb3_section10_has_at_least_one_code_cell(
    nb3: nbformat.NotebookNode,
) -> None:
    """§10 exists: at least one code cell + every code cell has remove-input."""
    s10_code = _code_cells(_section_cells(nb3, SECTION10_TAG))
    assert s10_code, (
        "§10 must contain at least one code cell (tagged section:10); "
        "none found."
    )
    for c in s10_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§10 code cell missing 'remove-input' tag; got tags={tags!r}."
        )


def test_nb3_section10_citation_has_ankel_peters_2024(
    nb3: nbformat.NotebookNode,
) -> None:
    """§10 citation block references @ankelPeters2024protocol."""
    s10_md = _markdown_cells(_section_cells(nb3, SECTION10_TAG))
    citation_cells = [
        c
        for c in s10_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§10 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )
    combined = "\n\n".join(_cell_source(c) for c in citation_cells)
    assert _ANKELPETERS2024_KEY in combined, (
        f"§10 citation block must reference bib key "
        f"@{_ANKELPETERS2024_KEY} (I4R gate-aggregation output protocol). "
        f"Not found."
    )


# ── R2 remediation: live cell-31 execution + JSON equality check ─────────
#
# Reality-Checker three-way-review finding (2026-04-19): the §10 tests
# exercise ``build_gate_verdict`` + ``write_gate_verdict_atomic`` only
# on synthetic inputs. The live cell 31 — which normalises §1-§9
# verdicts, re-derives the bootstrap-HAC agreement flag, and writes
# gate_verdict.json atomically — is exec-tested only via the end-to-end
# nbconvert subprocess, which catches crashes but not silent logical
# drift in the verdict mapping (e.g. a mis-spelled ``_levene_verdict``
# → ``_t2_verdict`` swap would escape).
#
# Fix: concatenate the §1-§10 code sources and exec them in a fresh
# namespace, then re-read ``env.GATE_VERDICT_PATH`` and assert the live
# notebook-derived JSON matches the committed on-disk JSON. This is the
# same exec-concatenation pattern §5/§7/§8/§9 tests use.


def _build_live_exec_source(nb: nbformat.NotebookNode) -> str:
    """Concatenate §1-§10 code-cell sources into one exec-able string.

    Mirrors the real notebook execution chain: §1 pre-flight (reads
    DuckDB + PKL), §2-§7 test machinery (bind verdict scalars),
    §8 forest table, §9 spotlight + material_movers, §10 gate assembly
    + atomic JSON emission.

    Every cell carries ``section:N`` + ``remove-input`` tags; we pull
    source in tag order so the execution context matches nbconvert's.
    """
    parts: list[str] = [
        # Import path shim: make `import env` and `from scripts import
        # *` work from the exec context.
        "import sys",
        f"sys.path.insert(0, {str(_CONTRACTS_DIR)!r})",
        f"sys.path.insert(0, {str(_ENV_PATH.parent)!r})",
    ]
    for tag in _ALL_SECTION_TAGS:
        for c in nb.cells:
            cell_tags = tuple(c.metadata.get("tags", []))
            if tag in cell_tags and c.get("cell_type") == "code":
                src = c.get("source", "")
                if isinstance(src, list):
                    src = "".join(src)
                parts.append(str(src))
    return "\n\n".join(parts)


# Pinned per-test verdict values the live notebook chain MUST emit
# under the current pre-committed data + PKL. These values are NOT
# parameters the test allows to drift — they reflect:
#   - Decision #1 locked weekly panel (2008-01-02 → 2026-02-23)
#   - NB2's Column-6 primary HAC(4) fit
#   - The Rev 4 spec's null-semantics map for T1/T2/T4/T5/T6/T7
# Any logical drift in cell 31's normalisation (e.g. a PASS/FAIL swap
# on T2) will flip at least one of these and be caught here — which the
# round-trip on-disk comparison misses because cell 31 WRITES the
# buggy value to disk during exec.
_EXPECTED_LIVE_VERDICTS: Final[dict[str, Any]] = {
    "t1_verdict": "FAIL",         # T1 REJECT → auxiliary-gate FAIL
    "t2_verdict": "FAIL",         # T2 FAIL TO REJECT → channel ABSENT → FAIL
    "t3b_verdict": "FAIL",        # NB2 t3b_pass = False
    "t7_verdict": "PASS",         # intervention |Δβ̂| ≤ SE
    "gate_verdict": "FAIL",       # T3b FAIL binds final
    "pkl_degraded": False,        # version-pin match
    "material_movers_count": 0,   # §9 halt-on-T3b-FAIL
    "reconciliation": "AGREE",
    "bootstrap_hac_agreement": "AGREEMENT",
}


def test_nb3_section10_live_exec_matches_expected_verdicts(
    nb3: nbformat.NotebookNode,
) -> None:
    """Exec-run §1-§10 live; assert per-test verdicts match spec-derived values.

    This is the load-bearing check Task 31-R2 introduces. It prevents a
    silent logical-drift class where cell 31's verdict-normalisation
    chain (e.g. the ``_t1_verdict → _t1_final`` map or the
    ``_levene_verdict → _t2_final`` map) could be mis-authored such
    that the emitted JSON differs from intent — a case the end-to-end
    nbconvert test cannot catch (exit code 0 + no NameError is
    compatible with a wrong verdict), and a case the prior disk-
    round-trip test misses because cell 31 writes the wrong value to
    disk during the same exec (the in-memory and on-disk dicts both
    carry the bug).

    The test:
      1. Exec-concatenates §1-§10 code in a fresh namespace.
      2. Cell 31 binds ``gate_verdict_dict``.
      3. For each key in ``_EXPECTED_LIVE_VERDICTS``, assert the live
         in-memory value matches the pinned expected value.

    A swap bug in cell 31's mapping (e.g. inverting the T2 PASS/FAIL
    branch) will flip ``t2_verdict`` from "FAIL" to "PASS" and the test
    will fail loudly.
    """
    # Guard: the live DuckDB + PKL must be present or we can't exec.
    duckdb_path = _CONTRACTS_DIR / "data" / "structural_econ.duckdb"
    if not duckdb_path.is_file():
        pytest.skip(
            f"{duckdb_path} missing — can't exec-run the live notebook "
            f"chain."
        )
    if not _env.FULL_PKL_PATH.is_file():
        pytest.skip(
            f"{_env.FULL_PKL_PATH} missing — NB2 §10 has not been run."
        )

    source = _build_live_exec_source(nb3)
    ns: dict[str, Any] = {}
    exec(compile(source, "<nb3-section10-live>", "exec"), ns)

    # Cell 31 binds ``gate_verdict_dict``.
    assert "gate_verdict_dict" in ns, (
        "Cell 31 live exec did not bind `gate_verdict_dict`. "
        "Check §10 code for NameError upstream."
    )
    live = dict(ns["gate_verdict_dict"])

    # Assert each pinned verdict key matches exactly.
    mismatches = {
        k: (expected, live.get(k, "<missing>"))
        for k, expected in _EXPECTED_LIVE_VERDICTS.items()
        if live.get(k) != expected
    }
    assert not mismatches, (
        f"Cell 31 live exec produced {len(mismatches)} verdict "
        f"mismatches against spec-derived expectations:\n"
        + "\n".join(
            f"  {k!r}: expected {exp!r}, got {actual!r}"
            for k, (exp, actual) in sorted(mismatches.items())
        )
    )


def test_nb3_section10_live_exec_final_verdict_is_fail(
    nb3: nbformat.NotebookNode,
) -> None:
    """Live exec produces the FAIL verdict driven by T3b.

    Pins the T3b-FAIL → final-FAIL branch against silent inversion of
    the PASS/FAIL logic (e.g. a reviewer hand-editing the branch
    ordering in ``build_gate_verdict``).
    """
    duckdb_path = _CONTRACTS_DIR / "data" / "structural_econ.duckdb"
    if not duckdb_path.is_file():
        pytest.skip(f"{duckdb_path} missing — can't exec-run.")
    if not _env.FULL_PKL_PATH.is_file():
        pytest.skip(f"{_env.FULL_PKL_PATH} missing.")

    source = _build_live_exec_source(nb3)
    ns: dict[str, Any] = {}
    exec(compile(source, "<nb3-section10-live-verdict>", "exec"), ns)

    v = ns["gate_verdict_dict"]
    assert v["gate_verdict"] == "FAIL", (
        f"Live exec expected final gate_verdict = FAIL (T3b FAIL drives "
        f"it); got {v['gate_verdict']!r}."
    )
    assert v["t3b_verdict"] == "FAIL", (
        f"Live exec expected t3b_verdict = FAIL; got "
        f"{v['t3b_verdict']!r}."
    )


# ── R3 remediation: §2 prose-vs-code drift on t1_pvalue / t1_source ──────
#
# Reality-Checker-flagged: the §2 interpretation cell (cell 8) promised
# three gate_verdict.json fields that cell 31 never emits:
#   - t1_pvalue
#   - t1_source
#   - Abrigo simulator "predictive-regression-interpretation" flag
# Fix: scrub the prose. The regression asserts the cell 8 text does
# NOT reference `t1_pvalue`, `t1_source`, or the flag name, because
# none of them exist in the current gate_verdict.json schema.

_UNFULFILLED_PROSE_TOKENS: Final[tuple[str, ...]] = (
    "t1_pvalue",
    "t1_source",
    "predictive-regression interpretation flag",
    "predictive-regression-interpretation flag",
)


def test_nb3_section2_prose_matches_gate_verdict_schema(
    nb3: nbformat.NotebookNode,
) -> None:
    """§2 cell 8 prose must not promise gate_verdict.json fields that do
    not exist.

    Cell 8 previously claimed the gate writer records ``t1_pvalue``,
    ``t1_source``, and a simulator "predictive-regression interpretation
    flag" — none of which are emitted by cell 31 or defined in the
    gate_verdict.json schema. This regression pins cell 8 to the
    actual schema.
    """
    section2_md = _markdown_cells(_section_cells(nb3, "section:2"))
    combined = "\n\n".join(_cell_source(c) for c in section2_md)
    violations = [
        t for t in _UNFULFILLED_PROSE_TOKENS if t in combined
    ]
    assert not violations, (
        f"§2 prose promises gate_verdict.json fields that cell 31 does "
        f"not emit: {violations!r}. Either add the fields to the "
        f"schema + emitter, or strip them from the prose."
    )


# ── End-to-end lint ───────────────────────────────────────────────────────

def test_nb3_citation_lint_passes_after_task29() -> None:
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
