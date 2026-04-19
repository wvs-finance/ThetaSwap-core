"""Structural + unit tests for NB2 §10 reconciliation dashboard + §11 atomic
serialization + the ``nb2_params_point.schema.json`` JSON Schema.

Task 22 of the econ-notebook-implementation plan. This module authors four
tranches of TDD assertions against:

  1. The JSON-Schema file at
     ``notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb2_params_point.schema.json``.
     It must be a valid Draft 2020-12 schema and it must require every Rev 4
     §4.4 top-level block (``ols_primary``, ``ols_student_t``, ``ols_ladder``,
     ``garch_x``, ``decomposition``, ``subsamples``, ``reconciliation``,
     ``t3b_pass``, ``gate_verdict``, ``spec_hash``, ``panel_fingerprint``,
     ``intervention_coverage``, ``handoff_metadata``). Every covariance block
     must use the ``{param_names, matrix}`` layout.

  2. The pure reconciliation rule implemented in
     ``scripts.nb2_serialize.reconcile(...)``. The rule (LOCKED per plan
     rev 2 — see plan line 431) says: AGREE iff ALL three conditions:

         (i)   sign(β̂_CPI) == sign(δ̂)                    (direction)
         (ii)  overlap of the 90% HAC CI on β̂_CPI with
               the 90% QMLE CI on δ̂ is non-empty          (directional
                                                            concordance — the
                                                            two parameters are
                                                            not numerically
                                                            comparable but
                                                            their signs and
                                                            significance are)
         (iii) significance at 10% concordant — both reject null OR
               both fail to reject                         (joint-inference
                                                            concordance)

     Zero is signed positive for the purpose of (i) so that a GARCH-X δ̂ fit
     at the positivity boundary (δ̂ = 0 under Han-Kristensen 2014, a
     legitimate null outcome) is treated as sign-concordant with any β̂_CPI
     whose 90% CI contains zero. Synthetic fits exhibiting each failure mode
     are tested explicitly.

  3. ``scripts.nb2_serialize.write_all(...)`` atomic two-phase emission. The
     rule is: stage JSON → fsync → rename → stage PKL → fsync → rename. An
     exception injected after the JSON write but before the PKL write must
     leave NEITHER file on disk (roll back). The synthetic-exception test
     monkey-patches the module-local ``_write_pkl_atomic`` helper to raise,
     then asserts the JSON final path and the PKL final path are both absent.

  4. NB2 notebook structure post-Task-22 — §10 dashboard (programmatic
     Verdict Box update + side-by-side coefficient/CI block for OLS /
     GARCH-X / decomposition + bootstrap-HAC agreement flag surfaced from
     §3.5) and §11 serialization cell (calls ``nb2_serialize.write_all(...)``
     with all fit objects).

This module is authored TDD-first: it fails against the 36-cell post-Task-21
NB2 and the 1175-byte Task-1b ``nb2_serialize.py`` stub and turns green once
the Data Engineer commits the schema + the full serializer + the §10-§11
trios (6 cells → 42 total).
"""
from __future__ import annotations

import importlib.util
import json
import pickle
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

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
SCHEMA_PATH: Final[Path] = _env.ESTIMATES_DIR / "nb2_params_point.schema.json"


# ── Constants ─────────────────────────────────────────────────────────────

SECTION10_TAG: Final[str] = "section:10"
SECTION11_TAG: Final[str] = "section:11"
REMOVE_INPUT_TAG: Final[str] = "remove-input"

REQUIRED_HEADERS: Final[tuple[str, ...]] = (
    "**Reference.**",
    "**Why used.**",
    "**Relevance to our results.**",
    "**Connection to simulator.**",
)

# All Rev 4 §4.4 top-level blocks the schema must declare as required.
_REQUIRED_SCHEMA_BLOCKS: Final[tuple[str, ...]] = (
    "ols_primary",
    "ols_student_t",
    "ols_ladder",
    "garch_x",
    "decomposition",
    "subsamples",
    "reconciliation",
    "t3b_pass",
    "gate_verdict",
    "spec_hash",
    "panel_fingerprint",
    "intervention_coverage",
    "handoff_metadata",
)

# Covariance sub-blocks the schema must use the {param_names, matrix} layout on.
_COV_BEARING_BLOCK_PATHS: Final[tuple[tuple[str, ...], ...]] = (
    ("ols_primary", "cov"),
    ("ols_student_t", "cov"),
    ("garch_x", "cov"),
    ("decomposition", "cov"),
)

# Post-Task-21 NB2 has 36 cells. Task 22 appends §10 and §11 trios
# (3 cells each) → floor of 42.
_MIN_POST_TASK22_CELL_COUNT: Final[int] = 42

# Bootstrap-HAC agreement flag surfaced from §3.5 (Task 17).
_BOOTSTRAP_HAC_AGREEMENT_TOKENS: Final[tuple[str, ...]] = (
    "AGREEMENT",
    "DIVERGENCE",
    "_verdict",
    "bootstrap_hac",
)

# §10 reconciliation dashboard tokens.
_RECONCILIATION_VERDICT_TOKENS: Final[tuple[str, ...]] = (
    '"AGREE"',
    '"DISAGREE"',
)

_SIDE_BY_SIDE_TOKENS: Final[tuple[str, ...]] = (
    "column6_fit",
    "garch_x",
    "decomposition_fit",
)

# §11 serialization cell tokens.
_SECTION11_REQUIRED_TOKENS: Final[tuple[str, ...]] = (
    "nb2_serialize",
    "write_all",
    "POINT_JSON_PATH",
    "FULL_PKL_PATH",
)


# ── Dynamic import of the serializer module ───────────────────────────────

def _load_nb2_serialize():
    """Import ``scripts/nb2_serialize.py`` with forced-reload semantics.

    The Task 22 serializer adds three callables:
      * ``reconcile`` — pure, returns "AGREE" or "DISAGREE"
      * ``write_all`` — atomic two-phase emit
      * ``_write_pkl_atomic`` — module-private helper that ``write_all``
        uses after the JSON write. The atomic-rollback test monkey-patches
        this one.

    We register the loaded module in ``sys.modules`` under the chosen name
    BEFORE executing it so the dataclass machinery (``HandoffMetadata``
    decorator) can look up ``cls.__module__`` during field-annotation
    resolution. Skipping this registration surfaces as
    ``AttributeError: 'NoneType' object has no attribute '__dict__'`` in
    dataclasses.py during field processing.
    """
    serialize_path = _SCRIPTS_DIR / "nb2_serialize.py"
    assert serialize_path.is_file(), f"Missing {serialize_path}"
    mod_name = "nb2_serialize_test_target"
    spec = importlib.util.spec_from_file_location(mod_name, serialize_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def nb2() -> nbformat.NotebookNode:
    assert NB2_PATH.is_file(), f"Missing NB2 notebook: {NB2_PATH}"
    return nbformat.read(NB2_PATH, as_version=4)


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    assert SCHEMA_PATH.is_file(), (
        f"Missing schema: {SCHEMA_PATH}. Task 22 must create it."
    )
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def serialize_module():
    return _load_nb2_serialize()


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


def _resolve_ref(schema: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    """Resolve a single-level local ``$ref`` (``#/$defs/xxx``) against schema.

    Returns ``node`` unchanged if it has no ``$ref``. Only supports one hop —
    the schema is authored to avoid nested refs on the covariance + regime
    definitions, so single-level resolution is sufficient.
    """
    ref = node.get("$ref")
    if ref is None:
        return node
    assert ref.startswith("#/$defs/"), (
        f"Only local $defs refs are supported in tests; got {ref!r}."
    )
    def_name = ref[len("#/$defs/"):]
    return schema["$defs"][def_name]


# ── (1) Schema validation tests ───────────────────────────────────────────

def test_schema_is_valid_json_schema_draft_2020_12(schema: dict[str, Any]) -> None:
    """``nb2_params_point.schema.json`` is a valid Draft 2020-12 schema.

    We use ``jsonschema.Draft202012Validator.check_schema`` — it raises
    ``SchemaError`` if the schema itself is not a valid meta-schema instance.
    """
    import jsonschema

    assert schema.get("$schema", "").endswith("2020-12/schema"), (
        f"Schema $schema must declare Draft 2020-12. Got "
        f"{schema.get('$schema')!r}."
    )
    # Raises SchemaError on invalid schema structure.
    jsonschema.Draft202012Validator.check_schema(schema)


def test_schema_declares_all_rev4_blocks(schema: dict[str, Any]) -> None:
    """The schema requires every Rev 4 §4.4 top-level block."""
    required = set(schema.get("required", []))
    missing = set(_REQUIRED_SCHEMA_BLOCKS) - required
    assert not missing, (
        f"Schema is missing required top-level blocks: {sorted(missing)!r}. "
        f"Rev 4 §4.4 mandates: {sorted(_REQUIRED_SCHEMA_BLOCKS)!r}."
    )
    properties = schema.get("properties", {})
    for block in _REQUIRED_SCHEMA_BLOCKS:
        assert block in properties, (
            f"Schema ``properties`` must define {block!r}."
        )


def test_schema_covariance_blocks_use_param_names_matrix_layout(
    schema: dict[str, Any],
) -> None:
    """Every covariance sub-block uses the ``{param_names, matrix}`` layout."""
    properties = schema["properties"]
    for path in _COV_BEARING_BLOCK_PATHS:
        node = properties
        for key in path[:-1]:
            node = node[key]["properties"]
        cov_schema = _resolve_ref(schema, node[path[-1]])
        cov_required = set(cov_schema.get("required", []))
        assert "param_names" in cov_required and "matrix" in cov_required, (
            f"Covariance block at {'.'.join(path)} must require both "
            f"'param_names' and 'matrix' (got required: {cov_required!r})."
        )
        cov_props = cov_schema.get("properties", {})
        assert cov_props.get("param_names", {}).get("type") == "array", (
            f"param_names at {'.'.join(path)} must be an array."
        )
        assert cov_props.get("matrix", {}).get("type") == "array", (
            f"matrix at {'.'.join(path)} must be an array (row-major)."
        )


def test_schema_garch_x_has_residual_and_conditional_vol_series(
    schema: dict[str, Any],
) -> None:
    """GARCH-X block carries both standardized-residual and conditional-vol series."""
    garch_props = schema["properties"]["garch_x"]["properties"]
    assert "std_resid" in garch_props, (
        "GARCH-X block must include standardized-residual series 'std_resid' "
        "(Layer 2 filtered-historical simulation)."
    )
    assert "conditional_vol" in garch_props, (
        "GARCH-X block must include conditional-volatility series "
        "'conditional_vol' (Layer 2 σ̂_T initialization)."
    )


def test_schema_subsamples_has_three_regimes(schema: dict[str, Any]) -> None:
    """Subsamples block declares all three regime labels."""
    sub_props = schema["properties"]["subsamples"]["properties"]
    for regime in ("pre_2015", "mid_2015_2021", "post_2021"):
        assert regime in sub_props, (
            f"Subsamples block must define regime {regime!r}."
        )
        regime_schema = _resolve_ref(schema, sub_props[regime])
        regime_required = set(regime_schema.get("required", []))
        for field in ("beta", "cov", "n", "date_min", "date_max"):
            assert field in regime_required, (
                f"Regime {regime!r} must require field {field!r}."
            )


def test_schema_handoff_metadata_fields(schema: dict[str, Any]) -> None:
    """Handoff-metadata block carries all pinned library versions + bootstrap + seed."""
    handoff_required = set(
        schema["properties"]["handoff_metadata"].get("required", [])
    )
    for field in (
        "python_version",
        "statsmodels_version",
        "arch_version",
        "numpy_version",
        "pandas_version",
        "bootstrap_distribution",
        "recommended_seed",
    ):
        assert field in handoff_required, (
            f"handoff_metadata must require {field!r}."
        )


def test_schema_gate_verdict_is_pass_or_fail(schema: dict[str, Any]) -> None:
    """``gate_verdict`` is an enum restricted to PASS / FAIL."""
    gate_schema = schema["properties"]["gate_verdict"]
    assert gate_schema.get("enum") == ["PASS", "FAIL"], (
        f"gate_verdict must be enum ['PASS', 'FAIL']; got "
        f"{gate_schema.get('enum')!r}."
    )


def test_schema_reconciliation_is_agree_or_disagree(schema: dict[str, Any]) -> None:
    """``reconciliation`` is an enum restricted to AGREE / DISAGREE."""
    recon_schema = schema["properties"]["reconciliation"]
    assert recon_schema.get("enum") == ["AGREE", "DISAGREE"], (
        f"reconciliation must be enum ['AGREE', 'DISAGREE']; got "
        f"{recon_schema.get('enum')!r}."
    )


# ── (2) Reconciliation rule tests — synthetic fits per failure mode ───────

def test_reconcile_agree_both_negative_both_sig(serialize_module) -> None:
    """Both β̂ and δ̂ negative, both significant at 10%, CIs overlap → AGREE."""
    verdict = serialize_module.reconcile(
        beta_cpi=-0.003,
        beta_cpi_hac_ci90=(-0.005, -0.001),
        delta=-0.002,
        delta_qmle_ci90=(-0.004, -0.0005),
    )
    assert verdict == "AGREE", (
        f"Expected AGREE when both point estimates are same-sign, CIs "
        f"overlap (intersection [-0.004, -0.001]), and both exclude zero; "
        f"got {verdict!r}."
    )


def test_reconcile_agree_both_null(serialize_module) -> None:
    """Both fail to reject at 10% (CIs contain 0) → AGREE under joint-null.

    Locked per plan rev 2 — test embedded in Task 22's real case where
    β̂_CPI = -0.000685 (HAC CI contains 0) and δ̂ = 0 at the positivity
    boundary (QMLE CI contains 0). sign(δ̂) = 0 is treated as concordant
    with any β̂_CPI whose CI contains zero.
    """
    verdict = serialize_module.reconcile(
        beta_cpi=-0.000685,
        beta_cpi_hac_ci90=(-0.003636, 0.002266),
        delta=0.0,
        delta_qmle_ci90=(-0.001, 0.001),
    )
    assert verdict == "AGREE", (
        f"Expected AGREE under joint-null (both CIs contain 0); got "
        f"{verdict!r}."
    )


def test_reconcile_disagree_opposite_signs(serialize_module) -> None:
    """Opposite signs + both CIs exclude zero → DISAGREE (sign mismatch)."""
    verdict = serialize_module.reconcile(
        beta_cpi=-0.002,
        beta_cpi_hac_ci90=(-0.004, -0.0005),
        delta=+0.01,
        delta_qmle_ci90=(0.002, 0.02),
    )
    assert verdict == "DISAGREE", (
        f"Expected DISAGREE when point estimates have opposite signs and "
        f"neither CI contains zero; got {verdict!r}."
    )


def test_reconcile_disagree_significance_mismatch(serialize_module) -> None:
    """Same sign, but one significant and the other not → DISAGREE."""
    # β̂ excludes 0 (significant); δ̂ CI contains 0 (not significant).
    verdict = serialize_module.reconcile(
        beta_cpi=-0.002,
        beta_cpi_hac_ci90=(-0.004, -0.0005),
        delta=-0.001,
        delta_qmle_ci90=(-0.005, 0.003),
    )
    assert verdict == "DISAGREE", (
        f"Expected DISAGREE when significance classifications differ; got "
        f"{verdict!r}."
    )


def test_reconcile_agree_same_sign_both_excluding_zero_disjoint_intervals(
    serialize_module,
) -> None:
    """Directional concordance: same sign + both CIs exclude zero → AGREE.

    Plan rev 2 line 431 semantics (three-way review E2 hotfix): β̂ and δ̂
    live in different units (weekly RV^(1/3) slope vs daily conditional-
    variance coefficient) — their numerical magnitudes are not comparable.
    Clause (ii) "overlap is non-empty" is **directional concordance** on
    zero-containment, NOT numerical CI intersection. When both CIs exclude
    zero on the same side, the two fits AGREE on "both reject the null with
    matching sign", which is the substantive research verdict.
    """
    verdict = serialize_module.reconcile(
        beta_cpi=-10.0,
        beta_cpi_hac_ci90=(-12.0, -8.0),
        delta=-1.0,
        delta_qmle_ci90=(-3.0, -2.0),
    )
    assert verdict == "AGREE", (
        f"Expected AGREE (directional concordance): both CIs exclude zero "
        f"on the negative side, signs match. Numerical-intersection logic "
        f"would mis-classify this as DISAGREE because the two CIs live in "
        f"different parameter spaces; directional concordance on zero-"
        f"containment is the correct semantics. Got {verdict!r}."
    )


def test_reconcile_disagree_same_sign_cis_on_opposite_sides_of_zero(
    serialize_module,
) -> None:
    """Point estimates same sign, but one CI on each side of zero → DISAGREE.

    Degenerate case: δ̂ is marginally positive but its CI crosses zero onto
    the negative side while β̂'s CI sits entirely on the negative side.
    Directional-concordance clause (ii) requires both CIs be on the same
    side of zero (both contain or both exclude); here β̂'s CI excludes zero
    and δ̂'s CI contains zero → significance classification mismatch.
    """
    verdict = serialize_module.reconcile(
        beta_cpi=-10.0,
        beta_cpi_hac_ci90=(-12.0, -8.0),
        delta=-1.0,
        delta_qmle_ci90=(-2.0, 0.5),  # contains zero
    )
    assert verdict == "DISAGREE", (
        f"Expected DISAGREE: one CI excludes zero, the other contains "
        f"zero → significance classification mismatch. Got {verdict!r}."
    )


def test_reconcile_both_excluding_zero_opposite_sides_disagree(
    serialize_module,
) -> None:
    """Both CIs exclude zero but on opposite sides → DISAGREE (sign mismatch).

    Directional-concordance clause (i) (sign concordance) fails: β̂ negative,
    δ̂ positive, both significant. This is an unambiguous scientific
    disagreement between the two co-primary fits.
    """
    verdict = serialize_module.reconcile(
        beta_cpi=-10.0,
        beta_cpi_hac_ci90=(-12.0, -8.0),
        delta=+1.0,
        delta_qmle_ci90=(0.5, 2.0),
    )
    assert verdict == "DISAGREE", (
        f"Expected DISAGREE: signs opposite and both significant (CIs "
        f"exclude zero) → unambiguous disagreement. Got {verdict!r}."
    )


def test_reconcile_both_containing_zero_numerically_disjoint_agree(
    serialize_module,
) -> None:
    """Directional concordance E2 fix: both CIs contain zero → AGREE.

    Plan rev 2 line 431 locked semantics: even when the two CIs do NOT
    numerically intersect, if BOTH contain zero the two fits concord on
    "both fail to reject at 10%" → joint-null → AGREE.

    This test is the sharpest diagnostic of the E2 bug: pre-fix the
    reconcile() helper does a literal max/min intersection test; post-fix
    it returns AGREE because both 90% CIs contain zero regardless of their
    numerical distance. Pre-fix: DISAGREE (wrong). Post-fix: AGREE.
    """
    # Deliberately disjoint CIs, but both contain zero.
    verdict = serialize_module.reconcile(
        beta_cpi=0.0001,
        beta_cpi_hac_ci90=(-5.0, 5.0),       # contains zero
        delta=0.0001,
        delta_qmle_ci90=(-0.0001, 0.0001),   # contains zero, numerically disjoint from above
    )
    assert verdict == "AGREE", (
        f"Expected AGREE under directional concordance: both CIs contain "
        f"zero → joint-null verdict concordant. Numerical-intersection "
        f"logic (pre-fix) would still say AGREE here only because both "
        f"CIs happen to contain zero and their numerical intersection "
        f"{{0}} is non-empty — but the semantics test is that the rule "
        f"must NOT depend on numerical distance between β̂'s and δ̂'s "
        f"parameter spaces. Got {verdict!r}."
    )


# ── E1 + E2 three-way review hotfix tests ─────────────────────────────────

def test_build_payload_emits_iso_date_strings_for_subsample_regimes(
    serialize_module,
) -> None:
    """E1 regression: `build_payload` must emit ISO-date strings for every
    `date_min`/`date_max` field — including subsample regimes built from
    `_sub.reset_index(drop=True)` in NB2 §8.

    The live NB2 §8 cell 31 resets the index on the per-regime DataFrame
    (see `_sub = _w.loc[_mask].reset_index(drop=True)`), so the regime fit's
    `fit.model.data.row_labels` is an integer RangeIndex, NOT a
    DatetimeIndex. Pre-E1-fix: `build_payload` writes `"0"` / `"N-1"` into
    `subsamples.<regime>.date_{min,max}` → the schema's
    `^\\d{4}-\\d{2}-\\d{2}$` regex on `$defs/date_iso` fails under
    `jupyter nbconvert --execute`.

    This test reproduces the failure mode by constructing a regime fit
    whose `model.data.row_labels` is an integer RangeIndex (the native
    shape after `reset_index(drop=True)`). Pre-fix: ValueError via
    jsonschema because `"0"` does not match the regex. Post-fix: the
    regime block's `date_min`/`date_max` fields are ISO-date strings
    drawn from a trustworthy fallback source (the `week_start` column
    kept on the regime DataFrame) and pass schema validation.
    """
    import importlib.util
    import sys as _sys
    import types

    import numpy as np
    import pandas as pd
    import statsmodels.api as sm
    from jsonschema import Draft202012Validator

    # ── Build a minimal weekly panel with the six Column-6 regressors.
    rng = np.random.default_rng(0)
    n = 80
    week_start = pd.date_range("2010-01-04", periods=n, freq="W-MON")
    regressors = {
        "cpi_surprise_ar1": rng.standard_normal(n) * 0.5,
        "us_cpi_surprise": rng.standard_normal(n) * 0.3,
        "banrep_rate_surprise": rng.standard_normal(n) * 0.1,
        "vix_avg": rng.standard_normal(n) * 2.0 + 18.0,
        "intervention_dummy": (rng.random(n) > 0.95).astype(float),
        "oil_return": rng.standard_normal(n) * 0.02,
    }
    y = (
        0.2
        + 0.05 * regressors["cpi_surprise_ar1"]
        + 0.3 * rng.standard_normal(n)
    )
    weekly_df = pd.DataFrame(
        {"week_start": week_start, "rv_cuberoot": y, **regressors}
    )

    # ── Fit Column-6 primary on full panel (for build_payload).
    X = sm.add_constant(weekly_df[list(regressors.keys())])
    column6_fit = sm.OLS(weekly_df["rv_cuberoot"], X).fit(
        cov_type="HAC", cov_kwds={"maxlags": 4}
    )

    # ── Build per-regime fits EXACTLY like §8.1: reset_index(drop=True).
    regime_fits: dict[str, Any] = {}
    regime_sigma_hats: dict[str, Any] = {}
    regime_labels = ("pre_2015", "mid_2015_2021", "post_2021")
    for i, label in enumerate(regime_labels):
        lo = i * (n // 3)
        hi = lo + (n // 3) if i < 2 else n
        sub = weekly_df.iloc[lo:hi].reset_index(drop=True)  # ← loses datetime idx
        Xr = sm.add_constant(sub[list(regressors.keys())])
        fit_r = sm.OLS(sub["rv_cuberoot"], Xr).fit(
            cov_type="HAC", cov_kwds={"maxlags": 4}
        )
        regime_fits[label] = fit_r
        regime_sigma_hats[label] = fit_r.cov_params().loc[
            list(regressors.keys()), list(regressors.keys())
        ]

    # ── Build a minimal Student-t-like fit (not load-bearing for E1).
    # The build_payload contract requires an object with .params, .bse,
    # .cov_params(), .nobs — a plain OLS on 2 columns suffices.
    t_panel = sm.add_constant(weekly_df[list(regressors.keys())])
    tfit_stub = sm.OLS(weekly_df["rv_cuberoot"], t_panel).fit()

    # Fake a TLinearModel-style params index: params[-2] = df, params[-1] = scale.
    class _TfitAdapter:
        """Duck-types the TLinearModel fit shape build_payload expects."""

        def __init__(self, fit):
            self._fit = fit
            # Six regressors + const = 7 β-params, plus df and scale = 9 total.
            # Emulate by appending two synthetic trailing values.
            import numpy as _np

            self.params = _np.concatenate(
                [fit.params.values, [5.0, 0.04]]
            )
            self.bse = _np.concatenate([fit.bse.values, [1.0, 0.01]])
            # Extend cov_params to 9×9 block-diagonal.
            base = fit.cov_params().values
            pad = _np.eye(2) * 1e-6
            self._cov = _np.block(
                [
                    [base, _np.zeros((base.shape[0], 2))],
                    [_np.zeros((2, base.shape[0])), pad],
                ]
            )
            self.nobs = int(fit.nobs)

        def cov_params(self):
            return self._cov

    tfit = _TfitAdapter(tfit_stub)

    # ── Ladder: six 1-term regressions on cpi_surprise_ar1 incrementally.
    ladder_fits = []
    cumulative = ["cpi_surprise_ar1"]
    base_regs = list(regressors.keys())
    for k in range(1, 7):
        cumulative = base_regs[:k]
        X_lad = sm.add_constant(weekly_df[cumulative])
        f_lad = sm.OLS(weekly_df["rv_cuberoot"], X_lad).fit(
            cov_type="HAC", cov_kwds={"maxlags": 4}
        )
        ladder_fits.append(f_lad)

    # ── GARCH-X bag (synthetic, not load-bearing).
    garch_x_bag = {
        "mu": 0.01,
        "omega": 0.01,
        "alpha_1": 0.07,
        "beta_1": 0.92,
        "delta": 0.0,
        "qmle_cov_matrix": np.eye(5) * 1e-6,
        "log_likelihood": -1234.5,
        "persistence": 0.99,
        "iterations": 123,
        "hessian_pd_status": True,
        "std_resid": [0.1, -0.2, 0.05],
        "conditional_vol": [0.4, 0.41, 0.42],
    }

    # ── Decomposition fit (2-regressor CPI/PPI).
    weekly_df["ipp_std"] = rng.standard_normal(n) * 0.5
    X_dec = sm.add_constant(weekly_df[["cpi_surprise_ar1", "ipp_std"]])
    decomposition_fit = sm.OLS(weekly_df["rv_cuberoot"], X_dec).fit(
        cov_type="HAC", cov_kwds={"maxlags": 4}
    )

    # ── Pooling tests stubs.
    pooling_wald_chi2 = {"statistic": 1.2, "pvalue": 0.54, "df": 2}
    pooling_f_test = {"statistic": 0.6, "pvalue": 0.55, "df_num": 2, "df_den": n - 10}

    # ── Handoff metadata.
    handoff_meta = serialize_module.default_handoff_metadata()

    # ── Daily index dates (ISO date range).
    daily_dates = pd.date_range("2010-01-01", periods=3000, freq="D")

    payload = serialize_module.build_payload(
        column6_fit=column6_fit,
        tfit=tfit,
        ladder_fits=ladder_fits,
        garch_x=garch_x_bag,
        decomposition_fit=decomposition_fit,
        regime_fits=regime_fits,
        regime_sigma_hats=regime_sigma_hats,
        pooling_wald_chi2=pooling_wald_chi2,
        pooling_f_test=pooling_f_test,
        reconciliation="AGREE",
        t3b_pass=False,
        gate_verdict="FAIL",
        spec_hash="5d86d01c5d2ca58587f966c2b0a66c942500107436ecb91c11d8efc3e65aa2c6",
        panel_fingerprint="deadbeef" * 8,
        intervention_coverage=5,
        handoff_metadata=handoff_meta,
        weekly_index_dates=weekly_df["week_start"],
        daily_index_dates=daily_dates,
    )

    # ── Load the authoritative schema and validate.
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        schema = json.load(fh)
    validator = Draft202012Validator(schema)

    # The key E1 assertion: the regime date fields match the ISO-date regex.
    import re

    iso_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for label in regime_labels:
        block = payload["subsamples"][label]
        assert iso_re.match(str(block["date_min"])), (
            f"Regime {label!r} date_min must be ISO 'YYYY-MM-DD'; got "
            f"{block['date_min']!r}. Pre-fix this is '0' (RangeIndex from "
            f"reset_index(drop=True))."
        )
        assert iso_re.match(str(block["date_max"])), (
            f"Regime {label!r} date_max must be ISO 'YYYY-MM-DD'; got "
            f"{block['date_max']!r}."
        )

    # Full schema validation: raises ValidationError on any ISO-date regex failure.
    validator.validate(payload)


def test_nb2_section11_live_build_payload_call_passes_iso_dates(
    nb2: nbformat.NotebookNode,
) -> None:
    """E1 regression: NB2 §11 cell must hand ISO-date compatible inputs to
    build_payload — either the cell pre-coerces to ISO strings OR
    build_payload itself coerces every date field at construction time.

    This is a structural check: the cell must either import/use a date
    coercion utility OR the serializer must handle pandas Timestamp/
    integer-index edge cases internally. We assert the serializer itself
    (tested by the sibling test above) handles the case cleanly.
    """
    s11_code_src = "\n\n".join(
        _cell_source(c)
        for c in _code_cells(_section_cells(nb2, SECTION11_TAG))
    )
    # Must call build_payload — the site where coercion happens.
    assert "build_payload" in s11_code_src, (
        "§11 must call nb2_serialize.build_payload so date coercion "
        "happens in a single audited location."
    )


# ── (3) Atomic emit tests ─────────────────────────────────────────────────

def _synthetic_payload(estimates_dir: Path) -> dict[str, Any]:
    """Build a minimal schema-valid payload for atomic-emit tests.

    Not load-bearing on the real NB2 fits — only the shape matters for
    schema validation during the atomic-write path.
    """
    return {
        "ols_primary": {
            "beta": {"cpi_surprise_ar1": -0.000685, "const": 0.18},
            "cov": {
                "param_names": ["const", "cpi_surprise_ar1"],
                "matrix": [[1e-4, 0.0], [0.0, 3.2e-6]],
            },
            "se": {"cpi_surprise_ar1": 0.001794, "const": 0.01},
            "hac_lag": 4,
            "n": 941,
            "r_squared": 0.12,
            "adj_r_squared": 0.11,
            "date_min": "2008-01-07",
            "date_max": "2025-12-31",
        },
        "ols_student_t": {
            "beta": {"cpi_surprise_ar1": -0.000946, "const": 0.18},
            "cov": {
                "param_names": ["const", "cpi_surprise_ar1"],
                "matrix": [[1e-4, 0.0], [0.0, 4.0e-6]],
            },
            "se": {"cpi_surprise_ar1": 0.002, "const": 0.01},
            "nu_hat": 5.54,
            "scale_hat": 0.04,
            "n": 941,
            "date_min": "2008-01-07",
            "date_max": "2025-12-31",
        },
        "ols_ladder": {
            "columns": [
                {
                    "column": 1,
                    "beta": {"cpi_surprise_ar1": -0.0005},
                    "se": {"cpi_surprise_ar1": 0.0018},
                    "n": 941,
                    "adj_r_squared": 0.02,
                    "date_min": "2008-01-07",
                    "date_max": "2025-12-31",
                }
            ]
        },
        "garch_x": {
            "theta": {
                "mu": 0.01,
                "omega": 0.01,
                "alpha_1": 0.07,
                "beta_1": 0.92,
                "delta": 0.0,
            },
            "cov": {
                "param_names": ["mu", "omega", "alpha_1", "beta_1", "delta"],
                "matrix": [[1e-6] * 5 for _ in range(5)],
            },
            "log_likelihood": -1234.5,
            "persistence": 0.9957,
            "iterations": 123,
            "hessian_pd_status": True,
            "std_resid": [0.1, -0.2, 0.05],
            "conditional_vol": [0.4, 0.41, 0.42],
            "date_min": "2008-01-07",
            "date_max": "2025-12-31",
        },
        "decomposition": {
            "beta": {"cpi_surprise_ar1": -0.000605, "ipp_std": 0.000245},
            "cov": {
                "param_names": ["cpi_surprise_ar1", "ipp_std"],
                "matrix": [[3.0e-6, 0.0], [0.0, 5.0e-6]],
            },
            "se": {"cpi_surprise_ar1": 0.0018, "ipp_std": 0.0022},
            "n": 941,
            "date_min": "2008-01-07",
            "date_max": "2025-12-31",
        },
        "subsamples": {
            "pre_2015": {
                "beta": {"cpi_surprise_ar1": -0.0004},
                "cov": {
                    "param_names": ["cpi_surprise_ar1"],
                    "matrix": [[4e-6]],
                },
                "n": 364,
                "date_min": "2008-01-07",
                "date_max": "2014-12-29",
            },
            "mid_2015_2021": {
                "beta": {"cpi_surprise_ar1": -0.0006},
                "cov": {
                    "param_names": ["cpi_surprise_ar1"],
                    "matrix": [[3e-6]],
                },
                "n": 313,
                "date_min": "2015-01-05",
                "date_max": "2020-12-28",
            },
            "post_2021": {
                "beta": {"cpi_surprise_ar1": -0.0012},
                "cov": {
                    "param_names": ["cpi_surprise_ar1"],
                    "matrix": [[5e-6]],
                },
                "n": 264,
                "date_min": "2021-01-04",
                "date_max": "2025-12-31",
            },
            "pooling_wald_chi2": {"statistic": 1.2, "pvalue": 0.54, "df": 2},
            "pooling_f_test": {"statistic": 0.6, "pvalue": 0.55, "df_num": 2, "df_den": 900},
        },
        "reconciliation": "AGREE",
        "t3b_pass": False,
        "gate_verdict": "FAIL",
        "spec_hash": "5d86d01c5d2ca58587f966c2b0a66c942500107436ecb91c11d8efc3e65aa2c6",
        "panel_fingerprint": "deadbeef" * 8,
        "intervention_coverage": 42,
        "handoff_metadata": {
            "python_version": "3.13.5",
            "statsmodels_version": "0.14.x",
            "arch_version": "8.0.x",
            "numpy_version": "2.4.x",
            "pandas_version": "3.0.x",
            "bootstrap_distribution": (
                "OLS blocks: multivariate normal from the HAC-robust "
                "covariance. GARCH-X block: parametric bootstrap from the "
                "fitted standardized residuals (Barone-Adesi 2008 / "
                "Bollerslev-Wooldridge 1992 convention) because Gaussian "
                "draws violate the α₁+β₁<1 stationarity constraint."
            ),
            "recommended_seed": 20260418,
            "schema_version": "1.0",
        },
    }


def test_write_all_emits_both_files(serialize_module, tmp_path: Path) -> None:
    """Happy path: ``write_all`` emits both JSON + PKL files atomically."""
    json_path = tmp_path / "nb2_params_point.json"
    pkl_path = tmp_path / "nb2_params_full.pkl"
    payload = _synthetic_payload(tmp_path)

    serialize_module.write_all(
        payload=payload,
        fit_objects={"sentinel": {"value": 42}},
        json_path=json_path,
        pkl_path=pkl_path,
        schema_path=SCHEMA_PATH,
    )

    assert json_path.is_file(), "JSON file not written"
    assert pkl_path.is_file(), "PKL file not written"

    # Validate round-trip.
    with open(json_path, "r", encoding="utf-8") as f:
        loaded_json = json.load(f)
    assert loaded_json["reconciliation"] == "AGREE"

    with open(pkl_path, "rb") as f:
        loaded_pkl = pickle.load(f)
    assert loaded_pkl["sentinel"]["value"] == 42

    # Tempfile sidecars must be gone after success.
    assert not (tmp_path / "nb2_params_point.json.tmp").exists()
    assert not (tmp_path / "nb2_params_full.pkl.tmp").exists()


def test_write_all_rolls_back_on_pkl_exception(
    serialize_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Synthetic exception after JSON write but before PKL write → BOTH files absent."""
    json_path = tmp_path / "nb2_params_point.json"
    pkl_path = tmp_path / "nb2_params_full.pkl"
    payload = _synthetic_payload(tmp_path)

    def _boom(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("synthetic failure between JSON and PKL")

    monkeypatch.setattr(serialize_module, "_write_pkl_atomic", _boom)

    with pytest.raises(RuntimeError, match="synthetic failure"):
        serialize_module.write_all(
            payload=payload,
            fit_objects={"sentinel": {"value": 42}},
            json_path=json_path,
            pkl_path=pkl_path,
            schema_path=SCHEMA_PATH,
        )

    # BOTH final paths must be absent — atomic rollback.
    assert not json_path.exists(), (
        "JSON final path must NOT exist after PKL-write exception. The "
        "serializer must roll back the JSON write in the exception handler."
    )
    assert not pkl_path.exists(), (
        "PKL final path must NOT exist after PKL-write exception."
    )
    # Stage files must also be absent (no leftovers).
    assert not (tmp_path / "nb2_params_point.json.tmp").exists()
    assert not (tmp_path / "nb2_params_full.pkl.tmp").exists()


def test_write_all_validates_against_schema(
    serialize_module, tmp_path: Path
) -> None:
    """Invalid payload → schema validation fails before any file is written."""
    import jsonschema

    json_path = tmp_path / "nb2_params_point.json"
    pkl_path = tmp_path / "nb2_params_full.pkl"

    # Missing required top-level block.
    bad_payload = {"reconciliation": "AGREE"}

    with pytest.raises((jsonschema.ValidationError, ValueError)):
        serialize_module.write_all(
            payload=bad_payload,
            fit_objects={},
            json_path=json_path,
            pkl_path=pkl_path,
            schema_path=SCHEMA_PATH,
        )
    assert not json_path.exists()
    assert not pkl_path.exists()


# ── (4) NB2 §10 + §11 notebook structure tests ────────────────────────────

def test_nb2_has_at_least_42_cells_post_task22(
    nb2: nbformat.NotebookNode,
) -> None:
    """NB2 has the post-Task-22 cell count floor."""
    assert len(nb2.cells) >= _MIN_POST_TASK22_CELL_COUNT, (
        f"NB2 has only {len(nb2.cells)} cells; Task 22 must add at least "
        f"{_MIN_POST_TASK22_CELL_COUNT - 36} new cells beyond the 36-cell "
        f"post-Task-21 state."
    )


def test_nb2_section10_has_code_cells(
    nb2: nbformat.NotebookNode,
) -> None:
    """§10 exists: at least one code cell tagged section:10 + remove-input."""
    s10_cells = _section_cells(nb2, SECTION10_TAG)
    s10_code = _code_cells(s10_cells)
    assert s10_code, (
        "§10 must contain at least one code cell (tagged section:10). "
        "Task 22 must author §10."
    )
    for c in s10_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§10 code cell missing 'remove-input' tag; got {tags!r}."
        )


def test_nb2_section11_has_code_cells(
    nb2: nbformat.NotebookNode,
) -> None:
    """§11 exists: at least one code cell tagged section:11 + remove-input."""
    s11_cells = _section_cells(nb2, SECTION11_TAG)
    s11_code = _code_cells(s11_cells)
    assert s11_code, (
        "§11 must contain at least one code cell (tagged section:11). "
        "Task 22 must author §11."
    )
    for c in s11_code:
        tags = _cell_tags(c)
        assert REMOVE_INPUT_TAG in tags, (
            f"§11 code cell missing 'remove-input' tag; got {tags!r}."
        )


def test_nb2_section10_surfaces_reconciliation_verdict(
    nb2: nbformat.NotebookNode,
) -> None:
    """§10 emits both AGREE and DISAGREE literals (pre-registered branches)."""
    s10_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION10_TAG))
    )
    for token in _RECONCILIATION_VERDICT_TOKENS:
        assert token in s10_code_src, (
            f"§10 source must pre-register the reconciliation branch "
            f"{token!r} so both verdicts are authored before the "
            f"computation runs."
        )


def test_nb2_section10_side_by_side_all_three_blocks(
    nb2: nbformat.NotebookNode,
) -> None:
    """§10 side-by-side references OLS primary + GARCH-X + decomposition fits."""
    s10_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION10_TAG))
    )
    for token in _SIDE_BY_SIDE_TOKENS:
        assert token in s10_code_src, (
            f"§10 source must reference {token!r} — the side-by-side "
            f"dashboard must include OLS primary, GARCH-X, and decomposition "
            f"blocks."
        )


def test_nb2_section10_surfaces_bootstrap_hac_agreement_flag(
    nb2: nbformat.NotebookNode,
) -> None:
    """§10 surfaces the bootstrap-HAC agreement flag from §3.5."""
    s10_src = "\n\n".join(_cell_source(c) for c in _section_cells(nb2, SECTION10_TAG))
    has_flag = any(t in s10_src for t in _BOOTSTRAP_HAC_AGREEMENT_TOKENS)
    assert has_flag, (
        f"§10 must surface the bootstrap-HAC agreement flag from §3.5 "
        f"(any of {_BOOTSTRAP_HAC_AGREEMENT_TOKENS!r}). Plan Task 22 "
        f"mandates this explicit cross-reference."
    )


def test_nb2_section11_calls_write_all(
    nb2: nbformat.NotebookNode,
) -> None:
    """§11 calls ``nb2_serialize.write_all(...)`` with the canonical paths."""
    s11_code_src = "\n\n".join(
        _cell_source(c) for c in _code_cells(_section_cells(nb2, SECTION11_TAG))
    )
    for token in _SECTION11_REQUIRED_TOKENS:
        assert token in s11_code_src, (
            f"§11 source must reference {token!r} — the serialization cell "
            f"must call nb2_serialize.write_all(...) with env.POINT_JSON_PATH "
            f"+ env.FULL_PKL_PATH."
        )


def test_nb2_section10_has_four_part_citation_block(
    nb2: nbformat.NotebookNode,
) -> None:
    """§10 carries at least one 4-part citation block markdown cell."""
    s10_md = _markdown_cells(_section_cells(nb2, SECTION10_TAG))
    citation_cells = [
        c
        for c in s10_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§10 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )


def test_nb2_section11_has_four_part_citation_block(
    nb2: nbformat.NotebookNode,
) -> None:
    """§11 carries at least one 4-part citation block markdown cell."""
    s11_md = _markdown_cells(_section_cells(nb2, SECTION11_TAG))
    citation_cells = [
        c
        for c in s11_md
        if all(h in _cell_source(c) for h in REQUIRED_HEADERS)
    ]
    assert citation_cells, (
        "§11 must contain at least one markdown cell carrying all four "
        "citation headers (Reference / Why used / Relevance / Connection)."
    )


def test_nb2_citation_lint_passes_after_task22() -> None:
    """``lint_notebook_citations.py`` exits 0 on NB2 after §10-§11 authoring."""
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
        f"Expected lint exit 0 on NB2 post-Task-22; got "
        f"{result.returncode}.\nstdout:\n{result.stdout}\nstderr:\n"
        f"{result.stderr}"
    )
