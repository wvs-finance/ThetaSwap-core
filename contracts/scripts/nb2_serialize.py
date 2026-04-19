"""NB2 Layer 1 → Layer 2 handoff serializer.

Task 22 of the ``docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md``
plan. This module:

  1. Implements the LOCKED reconciliation rule per plan rev 2 (``reconcile``)
     joining the OLS primary β̂_CPI against the GARCH-X δ̂. AGREE iff all
     three conditions hold:

         (i)   sign(β̂_CPI) == sign(δ̂)
         (ii)  90% HAC CI on β̂_CPI overlaps 90% QMLE CI on δ̂ (non-empty)
         (iii) significance at 10% concordant
               (both reject null OR both fail to reject)

     For condition (i) a point estimate exactly at zero (δ̂ = 0 is a
     legitimate Han-Kristensen 2014 boundary outcome for the positivity
     constraint) is treated as sign-concordant with any β̂_CPI whose 90%
     CI contains zero. Both CIs overlapping at {0} also trivially satisfy
     (ii) by non-empty intersection.

  2. Implements ``write_all`` — atomic two-phase emission of
     ``nb2_params_point.json`` (schema-validated) and ``nb2_params_full.pkl``
     (pickled fit-object bag). The two-phase pattern stages to ``.tmp``,
     fsyncs, and renames. If the PKL phase raises after the JSON rename,
     the JSON final path is unlinked so the two files are either both
     present or both absent on disk. Pre-write schema validation guarantees
     no malformed JSON hits disk.

  3. Exposes ``build_payload`` — a convenience constructor that assembles
     the §4.4-compliant payload dict from the typed fit-object bag produced
     in NB2 §§3–9. ``build_payload`` does NOT fit anything; it only packs
     already-fitted objects into the schema-compliant shape.

The module is pure-function + free-function in line with the
``@functional-python`` skill: no classes, no mutable globals, explicit
typing. The private ``_write_pkl_atomic`` helper is exposed at module
scope so the test suite can monkey-patch it to simulate the cross-phase
failure mode described in the plan.

Implementation reference: plan lines 421-438 + design spec §4.4 +
§7.5 bootstrap-draw distribution + §5.3 pickle version-guard.
"""
from __future__ import annotations

import json
import os
import pickle
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Final, Mapping

import jsonschema


# ── Reconciliation rule ──────────────────────────────────────────────────

_TEN_PERCENT_ALPHA: Final[float] = 0.10


def _sign(x: float) -> int:
    """Integer sign with 0 mapped to 0 (boundary convention)."""
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def _ci_contains_zero(ci: tuple[float, float]) -> bool:
    """True iff the closed 90% CI contains the origin."""
    lo, hi = ci
    return lo <= 0.0 <= hi


def _ci_overlap_nonempty(
    ci_a: tuple[float, float], ci_b: tuple[float, float]
) -> bool:
    """True iff two closed intervals [lo_a, hi_a] and [lo_b, hi_b] share a point."""
    lo_a, hi_a = ci_a
    lo_b, hi_b = ci_b
    return max(lo_a, lo_b) <= min(hi_a, hi_b)


def reconcile(
    *,
    beta_cpi: float,
    beta_cpi_hac_ci90: tuple[float, float],
    delta: float,
    delta_qmle_ci90: tuple[float, float],
) -> str:
    """Return the reconciliation verdict for the OLS primary vs GARCH-X.

    Arguments are keyword-only so the call site cannot accidentally swap
    the β̂ and δ̂ arguments — their numerical magnitudes are incommensurable
    (one is a mean-equation slope on cuberoot-RV, the other is a
    variance-equation coefficient on |CPI surprise|), but their signs and
    significance classifications are the comparable quantities.

    Args:
        beta_cpi: Point estimate β̂_CPI from the OLS primary.
        beta_cpi_hac_ci90: 90% HAC CI on β̂_CPI (lo, hi).
        delta: Point estimate δ̂ from the GARCH-X co-primary.
        delta_qmle_ci90: 90% QMLE CI on δ̂ (lo, hi).

    Returns:
        ``"AGREE"`` iff all three conditions hold, else ``"DISAGREE"``.

    Rules (locked per plan rev 2):
        (i)   Sign concordance: sign(β̂_CPI) == sign(δ̂). Special-case:
              δ̂ = 0 at boundary counts as concordant with any β̂_CPI
              whose 90% CI contains zero (joint-null case).
        (ii)  CI overlap: the two 90% CIs share at least one point.
        (iii) Significance-at-10% concordance: both CIs exclude zero
              OR both contain zero.
    """
    beta_ci_contains_zero = _ci_contains_zero(beta_cpi_hac_ci90)
    delta_ci_contains_zero = _ci_contains_zero(delta_qmle_ci90)

    # Condition (iii): significance concordance at 10%.
    sig_concordant = beta_ci_contains_zero == delta_ci_contains_zero
    if not sig_concordant:
        return "DISAGREE"

    # Condition (ii): CI overlap (non-empty intersection).
    if not _ci_overlap_nonempty(beta_cpi_hac_ci90, delta_qmle_ci90):
        return "DISAGREE"

    # Condition (i): sign concordance. Boundary-zero on δ̂ concordant
    # with any β̂_CPI whose CI contains zero — the joint-null case.
    s_beta = _sign(beta_cpi)
    s_delta = _sign(delta)

    if s_beta == s_delta:
        return "AGREE"

    # Boundary case: δ̂ = 0 and both CIs contain zero → joint null,
    # treat as sign-concordant.
    if s_delta == 0 and beta_ci_contains_zero and delta_ci_contains_zero:
        return "AGREE"

    # Symmetric boundary: β̂_CPI = 0 with both CIs containing zero.
    if s_beta == 0 and beta_ci_contains_zero and delta_ci_contains_zero:
        return "AGREE"

    return "DISAGREE"


# ── Payload builder ──────────────────────────────────────────────────────

def _named_cov(matrix: Any, param_names: list[str]) -> dict[str, Any]:
    """Build the {param_names, matrix} covariance record.

    Accepts a numpy array, pandas DataFrame, or a list of lists. Coerces
    to a plain list of lists of floats for JSON-friendliness.
    """
    try:
        import numpy as np
        import pandas as pd
    except ImportError as exc:  # pragma: no cover — required at runtime
        raise RuntimeError("numpy and pandas are required") from exc

    if isinstance(matrix, pd.DataFrame):
        arr = matrix.values
    elif isinstance(matrix, np.ndarray):
        arr = matrix
    else:
        arr = np.asarray(matrix, dtype=float)
    return {
        "param_names": list(param_names),
        "matrix": [[float(v) for v in row] for row in arr],
    }


@dataclass(frozen=True)
class HandoffMetadata:
    """Pinned version strings + Layer 2 bootstrap-draw convention."""

    python_version: str
    statsmodels_version: str
    arch_version: str
    numpy_version: str
    pandas_version: str
    bootstrap_distribution: str
    recommended_seed: int
    schema_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "python_version": self.python_version,
            "statsmodels_version": self.statsmodels_version,
            "arch_version": self.arch_version,
            "numpy_version": self.numpy_version,
            "pandas_version": self.pandas_version,
            "bootstrap_distribution": self.bootstrap_distribution,
            "recommended_seed": int(self.recommended_seed),
            "schema_version": self.schema_version,
        }


def default_handoff_metadata() -> HandoffMetadata:
    """Build the canonical HandoffMetadata from the current interpreter.

    Reads Python, statsmodels, arch, numpy, pandas versions at runtime so
    the emitted JSON records exactly what was in force during NB2
    execution. The bootstrap-distribution string is pre-registered text
    per plan line 437 — OLS blocks use multivariate-normal draws from the
    HAC-robust covariance; the GARCH-X block uses parametric bootstrap
    from the fitted standardized residuals (Barone-Adesi 2008 /
    Bollerslev-Wooldridge 1992), because Gaussian draws from N(θ̂, Σ̂)
    would violate the α_1+β_1 < 1 stationarity constraint with non-trivial
    probability at realistic Colombian persistence (~0.996).

    The recommended seed 20260418 is the Rev 4 spec-lock date.
    """
    import platform
    from importlib.metadata import PackageNotFoundError, version

    def _safe_version(pkg: str) -> str:
        try:
            return version(pkg)
        except PackageNotFoundError:
            return "unknown"

    bootstrap_text = (
        "OLS blocks (primary, Student-t, ladder, decomposition, subsample "
        "regimes): multivariate normal draws from the HAC-robust covariance "
        "matrix stored in each block's `cov` field. "
        "GARCH-X block: parametric bootstrap from the fitted standardized "
        "residuals {ẑ_t} (Barone-Adesi 2008 filtered-historical-simulation "
        "/ Bollerslev-Wooldridge 1992 QMLE convention) — Gaussian draws "
        "from N(θ̂, Σ̂) would violate α_1+β_1<1 stationarity and the "
        "ω/α/β/δ ≥ 0 positivity constraints with non-trivial probability "
        "at the Colombian persistence of ~0.996. Layer 2 resamples ẑ_t in "
        "blocks of 1 day (plain bootstrap) to rebuild the conditional "
        "variance path; parameter vectors are the bootstrap distribution "
        "itself."
    )

    return HandoffMetadata(
        python_version=platform.python_version(),
        statsmodels_version=_safe_version("statsmodels"),
        arch_version=_safe_version("arch"),
        numpy_version=_safe_version("numpy"),
        pandas_version=_safe_version("pandas"),
        bootstrap_distribution=bootstrap_text,
        recommended_seed=20260418,
    )


def build_payload(
    *,
    column6_fit: Any,
    tfit: Any,
    ladder_fits: list[Any],
    garch_x: Mapping[str, Any],
    decomposition_fit: Any,
    regime_fits: Mapping[str, Any],
    regime_sigma_hats: Mapping[str, Any],
    pooling_wald_chi2: Mapping[str, Any],
    pooling_f_test: Mapping[str, Any],
    reconciliation: str,
    t3b_pass: bool,
    gate_verdict: str,
    spec_hash: str,
    panel_fingerprint: str,
    intervention_coverage: int,
    handoff_metadata: HandoffMetadata,
    weekly_index_dates: Any,
    daily_index_dates: Any,
) -> dict[str, Any]:
    """Assemble the §4.4-compliant payload dict from NB2 fit objects.

    Pure packer — does not perform any estimation, only schema-aligned
    field marshalling. Callers supply all fitted objects from the NB2
    §§3-9 cells and the scalar verdicts from §9 + §10.

    The weekly and daily index-date sequences feed the per-block
    date_min / date_max fields. They are expected to be pandas
    DatetimeIndex-like objects (anything with ``.min()`` / ``.max()``).
    """
    column6_regressors = [
        "cpi_surprise_ar1",
        "us_cpi_surprise",
        "banrep_rate_surprise",
        "vix_avg",
        "intervention_dummy",
        "oil_return",
    ]
    full_param_names = ["const"] + column6_regressors

    def _date_bounds(dates: Any) -> tuple[str, str]:
        return (
            str(dates.min()).split(" ")[0],
            str(dates.max()).split(" ")[0],
        )

    weekly_min, weekly_max = _date_bounds(weekly_index_dates)
    daily_min, daily_max = _date_bounds(daily_index_dates)

    # ── ols_primary ──────────────────────────────────────────────────────
    ols_primary = {
        "beta": {k: float(v) for k, v in column6_fit.params.items()},
        "se": {k: float(v) for k, v in column6_fit.bse.items()},
        "cov": _named_cov(
            column6_fit.cov_params().loc[full_param_names, full_param_names],
            full_param_names,
        ),
        "hac_lag": 4,
        "n": int(column6_fit.nobs),
        "r_squared": float(column6_fit.rsquared),
        "adj_r_squared": float(column6_fit.rsquared_adj),
        "date_min": weekly_min,
        "date_max": weekly_max,
    }

    # ── ols_student_t ────────────────────────────────────────────────────
    # TLinearModel: params layout is [β_const, β_1, ..., β_6, df, scale];
    # k_beta = 7 (six regressors + constant). We slice the leading β-block.
    k_beta = len(full_param_names)
    t_beta_values = [float(tfit.params[i]) for i in range(k_beta)]
    t_se_values = [float(tfit.bse[i]) for i in range(k_beta)]
    t_cov_matrix = [
        [float(tfit.cov_params()[i, j]) for j in range(k_beta)]
        for i in range(k_beta)
    ]
    ols_student_t = {
        "beta": dict(zip(full_param_names, t_beta_values)),
        "se": dict(zip(full_param_names, t_se_values)),
        "cov": {"param_names": list(full_param_names), "matrix": t_cov_matrix},
        "nu_hat": float(tfit.params[-2]),
        "scale_hat": float(abs(tfit.params[-1])),
        "n": int(tfit.nobs) if hasattr(tfit, "nobs") else len(t_beta_values),
        "date_min": weekly_min,
        "date_max": weekly_max,
    }

    # ── ols_ladder ───────────────────────────────────────────────────────
    ladder_columns = []
    for idx, fit in enumerate(ladder_fits, start=1):
        ladder_columns.append(
            {
                "column": idx,
                "beta": {k: float(v) for k, v in fit.params.items()},
                "se": {k: float(v) for k, v in fit.bse.items()},
                "n": int(fit.nobs),
                "adj_r_squared": float(fit.rsquared_adj),
                "date_min": weekly_min,
                "date_max": weekly_max,
            }
        )

    # ── garch_x ──────────────────────────────────────────────────────────
    # garch_x is a mapping with fitted scalars, the QMLE covariance, and
    # the per-obs series. We consume keys the NB2 §6 cell exposes.
    garch_param_names = ["mu", "omega", "alpha_1", "beta_1", "delta"]
    garch_x_block = {
        "theta": {k: float(garch_x[k]) for k in garch_param_names},
        "cov": _named_cov(
            garch_x["qmle_cov_matrix"], garch_param_names
        ),
        "log_likelihood": float(garch_x["log_likelihood"]),
        "persistence": float(garch_x["persistence"]),
        "iterations": int(garch_x["iterations"]),
        "hessian_pd_status": bool(garch_x["hessian_pd_status"]),
        "std_resid": [float(z) for z in garch_x["std_resid"]],
        "conditional_vol": [float(s) for s in garch_x["conditional_vol"]],
        "date_min": daily_min,
        "date_max": daily_max,
    }

    # ── decomposition ────────────────────────────────────────────────────
    decomposition_params = ["cpi_surprise_ar1", "ipp_std"]
    decomposition = {
        "beta": {
            "cpi_surprise_ar1": float(
                decomposition_fit.params["cpi_surprise_ar1"]
            ),
            "ipp_std": float(decomposition_fit.params["ipp_std"]),
        },
        "se": {
            "cpi_surprise_ar1": float(
                decomposition_fit.bse["cpi_surprise_ar1"]
            ),
            "ipp_std": float(decomposition_fit.bse["ipp_std"]),
        },
        "cov": _named_cov(
            decomposition_fit.cov_params().loc[
                decomposition_params, decomposition_params
            ],
            decomposition_params,
        ),
        "n": int(decomposition_fit.nobs),
        "date_min": weekly_min,
        "date_max": weekly_max,
    }

    # ── subsamples ───────────────────────────────────────────────────────
    regime_labels = ("pre_2015", "mid_2015_2021", "post_2021")
    subsamples_block: dict[str, Any] = {}
    for label in regime_labels:
        fit = regime_fits[label]
        sigma = regime_sigma_hats[label]
        # Per-regime Σ̂ is a DataFrame on the 6 base regressors.
        sigma_names = list(sigma.columns)
        subsamples_block[label] = {
            "beta": {
                k: float(fit.params[k]) for k in sigma_names if k in fit.params
            },
            "se": {
                k: float(fit.bse[k]) for k in sigma_names if k in fit.bse
            },
            "cov": _named_cov(sigma.values, sigma_names),
            "n": int(fit.nobs),
            "adj_r_squared": float(fit.rsquared_adj),
            "date_min": str(fit.model.data.row_labels.min()).split(" ")[0]
            if hasattr(fit.model.data, "row_labels")
            else weekly_min,
            "date_max": str(fit.model.data.row_labels.max()).split(" ")[0]
            if hasattr(fit.model.data, "row_labels")
            else weekly_max,
        }
    subsamples_block["pooling_wald_chi2"] = {
        "statistic": float(pooling_wald_chi2["statistic"]),
        "pvalue": float(pooling_wald_chi2["pvalue"]),
        "df": int(pooling_wald_chi2["df"]),
    }
    subsamples_block["pooling_f_test"] = {
        "statistic": float(pooling_f_test["statistic"]),
        "pvalue": float(pooling_f_test["pvalue"]),
        "df_num": int(pooling_f_test["df_num"]),
        "df_den": int(pooling_f_test["df_den"]),
    }

    return {
        "ols_primary": ols_primary,
        "ols_student_t": ols_student_t,
        "ols_ladder": {"columns": ladder_columns},
        "garch_x": garch_x_block,
        "decomposition": decomposition,
        "subsamples": subsamples_block,
        "reconciliation": reconciliation,
        "t3b_pass": bool(t3b_pass),
        "gate_verdict": gate_verdict,
        "spec_hash": spec_hash,
        "panel_fingerprint": panel_fingerprint,
        "intervention_coverage": int(intervention_coverage),
        "handoff_metadata": handoff_metadata.to_dict(),
    }


# ── Atomic two-phase emit ─────────────────────────────────────────────────

def _fsync_then_rename(tmp_path: Path, final_path: Path) -> None:
    """fsync the tmp file's bytes + its directory, then rename to final.

    The directory fsync guarantees the rename is durable across a power
    cut — without it, the inode could survive but the dirent might not.
    """
    # fsync the file itself.
    with open(tmp_path, "rb") as fh:
        os.fsync(fh.fileno())
    # Atomic rename.
    os.replace(str(tmp_path), str(final_path))
    # fsync the containing directory so the rename is durable.
    dir_fd = os.open(str(final_path.parent), os.O_DIRECTORY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def _write_json_atomic(
    payload: Mapping[str, Any], json_path: Path
) -> None:
    """Stage JSON to ``.tmp`` in the same dir, fsync, rename."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = json_path.with_suffix(json_path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    _fsync_then_rename(tmp_path, json_path)


def _write_pkl_atomic(
    fit_objects: Any, pkl_path: Path
) -> None:
    """Stage PKL to ``.tmp`` in the same dir, fsync, rename."""
    pkl_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = pkl_path.with_suffix(pkl_path.suffix + ".tmp")
    with open(tmp_path, "wb") as fh:
        pickle.dump(fit_objects, fh, protocol=pickle.HIGHEST_PROTOCOL)
        fh.flush()
        os.fsync(fh.fileno())
    _fsync_then_rename(tmp_path, pkl_path)


def _load_schema(schema_path: Path) -> dict[str, Any]:
    with open(schema_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _cleanup_tempfiles(paths: list[Path]) -> None:
    """Best-effort removal of half-written temp files — never raises."""
    for p in paths:
        try:
            p.unlink(missing_ok=True)
        except Exception:  # pragma: no cover — best effort
            pass


def write_all(
    *,
    payload: Mapping[str, Any],
    fit_objects: Any,
    json_path: Path,
    pkl_path: Path,
    schema_path: Path,
) -> None:
    """Atomically emit ``nb2_params_point.json`` + ``nb2_params_full.pkl``.

    The routine enforces four rules:

      1. Pre-write schema validation: ``payload`` is checked against
         ``schema_path`` before any file is created. Invalid payload raises
         ``jsonschema.ValidationError`` and no disk state changes.
      2. JSON atomic write: stage to ``<json_path>.tmp``, fsync the file
         and its containing directory, then ``os.replace`` to the final
         path.
      3. PKL atomic write: same pattern, to ``<pkl_path>``.
      4. Cross-phase rollback: if the PKL phase raises AFTER the JSON
         final path has been created, the JSON file is unlinked so the
         caller sees no half-committed handoff.

    Side-effect ordering:
        validate → stage+rename JSON → stage+rename PKL
        on PKL exception → unlink(JSON) → re-raise

    Args:
        payload: Dict conforming to ``nb2_params_point.schema.json``.
        fit_objects: Arbitrary Python object graph to pickle. Convention:
            ``{"ols_primary": fit, "ladder": [...], "tfit": ..., ...}``.
        json_path: Final destination for the JSON contract.
        pkl_path: Final destination for the pickle companion.
        schema_path: Path to the authoritative JSON Schema.

    Raises:
        jsonschema.ValidationError: Payload does not match schema.
        Exception: Any disk-IO or pickle error. If it occurs after the
            JSON file is in place, the JSON file is rolled back before
            the exception propagates.
    """
    schema = _load_schema(Path(schema_path))
    # Pre-write validation: raises jsonschema.ValidationError on mismatch.
    jsonschema.Draft202012Validator(schema).validate(dict(payload))

    json_path = Path(json_path)
    pkl_path = Path(pkl_path)

    # Phase 1: JSON.
    _write_json_atomic(payload, json_path)

    # Phase 2: PKL. On ANY exception, roll back the JSON write.
    try:
        _write_pkl_atomic(fit_objects, pkl_path)
    except Exception:
        # Roll back Phase 1: unlink JSON + any leftover tmp files.
        _cleanup_tempfiles(
            [
                json_path,
                json_path.with_suffix(json_path.suffix + ".tmp"),
                pkl_path.with_suffix(pkl_path.suffix + ".tmp"),
            ]
        )
        raise


__all__ = [
    "HandoffMetadata",
    "build_payload",
    "default_handoff_metadata",
    "reconcile",
    "write_all",
    "_write_pkl_atomic",
]
