"""Task 2.1: Pre-registered primary OLS for Pair D simple-β.

Spec sha256 (sentinel-protocol):
    decision_hash = 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659
Spec frontmatter: contracts/docs/superpowers/specs/2026-04-27-simple-beta-pair-d-design.md (v1.3.1)

§5.3 PRIMARY specification (verbatim from spec):

    Y_t (logit) = α + β_6 * log(COP_USD_{t-6})
                    + β_9 * log(COP_USD_{t-9})
                    + β_12 * log(COP_USD_{t-12})
                    + ε_t

  Composite test statistic:
    β_composite = β_6 + β_9 + β_12
    Var(β_composite) = c'Σc, c = (0, 1, 1, 1)'
  One-sided test (§2):
    H0: β_composite ≤ 0
    H1: β_composite > 0
  Significance: α = 0.05 one-sided (§3.1)

HAC: Newey-West with bandwidth ⌊4 * (N/100)^(2/9)⌋. N=134 → bandwidth = 4.

ANTI-FISHING NOTE — orchestrator-vs-spec contradiction.
The Phase-2 task brief from the orchestrator instructs adding a `marco2018_dummy_t`
to the primary regression (defined as 1 for t ≥ 2021-01-01). This contradicts
spec §5.3 verbatim, which has NO methodology-break dummy in the primary; per spec
§6 the dummy is the R1 robustness alternative, NOT the primary, and the primary
disposition is to apply DANE empalme on raw Y before the §5.1 logit. Note that
because Y is a ratio of expansion factors (FEX_C or FEX_C18 per era; both numerator
and denominator use the same FEX), the share is invariant to a single multiplicative
empalme factor within each month — so empalme application is operationally a no-op
at the share level, and Phase 1 correctly did not apply it.

Per spec §9.1 (threshold immutability) + §9.2 (Y-construction immutability) +
§9.7 (sha256 governance) + the user's strict TDD/anti-fishing memories:
this script executes the SPEC-VERBATIM primary (no dummy). The orchestrator's
dummied variant is documented as an off-spec sensitivity in the findings memo.

Reproducibility:
    seed = 42
    statsmodels OLS with cov_type='HAC', cov_kwds={'maxlags': 4}
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox, het_breuschpagan
from statsmodels.stats.outliers_influence import OLSInfluence
from statsmodels.stats.stattools import durbin_watson, jarque_bera
from statsmodels.tsa.stattools import adfuller

WORKTREE = Path("/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom")
PANEL = WORKTREE / "contracts/.scratch/simple-beta-pair-d/data/panel_combined.parquet"
EXPECTED_PANEL_SHA = "6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf"

RESULTS = WORKTREE / "contracts/.scratch/simple-beta-pair-d/results"
OUT_JSON = RESULTS / "primary_ols.json"
OUT_RESID = RESULTS / "primary_ols_residuals.parquet"

SPEC_SHA = "964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659"

ALPHA_PRIMARY = 0.05  # spec §3.1
SEED = 42


@dataclass(frozen=True)
class CompositeBeta:
    point: float
    se_hac: float
    t_stat: float
    p_one_sided: float
    p_two_sided: float
    ci95_lower_one_sided: float  # one-sided 95% CI lower bound
    ci95_two_sided: tuple[float, float]


def _newey_west_bandwidth(n: int) -> int:
    return int(np.floor(4.0 * (n / 100.0) ** (2.0 / 9.0)))


def _file_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _composite(model: sm.regression.linear_model.RegressionResults, c: np.ndarray) -> CompositeBeta:
    """Composite β + HAC SE via the linear-restriction variance Var(c'β) = c'Σc.

    c is the contrast vector aligned to the model's exogenous design matrix order.
    The HAC covariance is what statsmodels exposes as `model.cov_params()` when
    fit with cov_type='HAC'.
    """
    beta_hat = np.asarray(model.params)
    sigma_hac = np.asarray(model.cov_params())
    point = float(c @ beta_hat)
    var_comp = float(c @ sigma_hac @ c)
    if var_comp < 0:
        raise ValueError(f"Composite-β variance c'Σc = {var_comp} < 0 — numerical pathology")
    se = float(np.sqrt(var_comp))
    t = point / se if se > 0 else float("nan")
    # one-sided H1: β > 0 → p = 1 - Φ(t) under asymptotic-normal approximation
    p_one = float(1.0 - stats.norm.cdf(t))
    p_two = float(2.0 * (1.0 - stats.norm.cdf(abs(t))))
    # one-sided 95% CI lower bound: point - z_{0.95} * se = point - 1.6449 * se
    z95 = float(stats.norm.ppf(0.95))
    ci_one_lower = point - z95 * se
    z975 = float(stats.norm.ppf(0.975))
    ci_two = (point - z975 * se, point + z975 * se)
    return CompositeBeta(
        point=point,
        se_hac=se,
        t_stat=t,
        p_one_sided=p_one,
        p_two_sided=p_two,
        ci95_lower_one_sided=ci_one_lower,
        ci95_two_sided=ci_two,
    )


def _diagnostics(resid: np.ndarray, exog: np.ndarray) -> dict[str, Any]:
    """Residual diagnostics: Breusch-Pagan, Durbin-Watson, Jarque-Bera, ADF, Ljung-Box."""
    # Breusch-Pagan: heteroskedasticity test (regress resid² on exog)
    bp_lm, bp_p, bp_f, bp_fp = het_breuschpagan(resid, exog)
    # Durbin-Watson on residuals
    dw = float(durbin_watson(resid))
    # Jarque-Bera: skew + kurtosis-based normality test
    jb_stat, jb_p, skew, kurt = jarque_bera(resid)
    # Excess kurtosis (J-B reports raw kurtosis ≈ 3 for normal; convert)
    excess_kurt = float(kurt) - 3.0
    # ADF on residuals: H0 = unit root → reject means residuals stationary
    adf_stat, adf_p, adf_lag, adf_n, adf_crit, _adf_icbest = adfuller(resid, autolag="AIC")
    # Ljung-Box at lags 4 and 12 (HAC bandwidth + monthly cycle)
    lb = acorr_ljungbox(resid, lags=[4, 12], return_df=True)
    return {
        "breusch_pagan_lm": float(bp_lm),
        "breusch_pagan_p": float(bp_p),
        "durbin_watson": dw,
        "jarque_bera_stat": float(jb_stat),
        "jarque_bera_p": float(jb_p),
        "skew": float(skew),
        "kurtosis_raw": float(kurt),
        "excess_kurtosis": excess_kurt,
        "adf_stat": float(adf_stat),
        "adf_p": float(adf_p),
        "adf_lag_used": int(adf_lag),
        "adf_n_used": int(adf_n),
        "adf_critical_values": {k: float(v) for k, v in adf_crit.items()},
        "ljung_box_lag4_stat": float(lb.loc[4, "lb_stat"]),
        "ljung_box_lag4_p": float(lb.loc[4, "lb_pvalue"]),
        "ljung_box_lag12_stat": float(lb.loc[12, "lb_stat"]),
        "ljung_box_lag12_p": float(lb.loc[12, "lb_pvalue"]),
    }


def main() -> None:
    np.random.seed(SEED)

    print("=== Task 2.1: pre-registered primary OLS (spec §5.3 verbatim) ===")
    print(f"Spec sha256: {SPEC_SHA}")

    panel_sha = _file_sha256(PANEL)
    print(f"Panel sha256: {panel_sha}")
    if panel_sha != EXPECTED_PANEL_SHA:
        raise RuntimeError(
            f"Panel sha256 mismatch. expected={EXPECTED_PANEL_SHA} got={panel_sha}"
        )
    print("Panel sha256 GATE PASS")

    df = pd.read_parquet(PANEL).sort_values("timestamp_utc").reset_index(drop=True)
    n = len(df)
    if n != 134:
        raise RuntimeError(f"Expected N=134, got {n}")
    print(f"N = {n}, window {df['timestamp_utc'].min()} → {df['timestamp_utc'].max()}")

    # marco2018_dummy: documented for the off-spec sensitivity ONLY (orchestrator brief).
    # Not used in the spec-verbatim primary.
    dummy = (df["timestamp_utc"] >= pd.Timestamp("2021-01-01", tz="UTC")).astype(int)
    n_dummy_ones = int(dummy.sum())
    print(f"marco2018_dummy: {n_dummy_ones} ones (informational; NOT in spec-verbatim primary)")

    # --- Spec-verbatim primary OLS (NO methodology dummy) -----------------
    y = df["Y_broad_logit"].astype(float).to_numpy()
    X_lags = df[["log_cop_usd_lag6", "log_cop_usd_lag9", "log_cop_usd_lag12"]].astype(float).to_numpy()
    X_design = sm.add_constant(X_lags, prepend=True)  # [const, lag6, lag9, lag12] order
    column_names_primary = ["const", "log_cop_usd_lag6", "log_cop_usd_lag9", "log_cop_usd_lag12"]

    bw = _newey_west_bandwidth(n)
    print(f"Newey-West bandwidth (floor(4*(N/100)^(2/9))) for N={n}: {bw}")

    model = sm.OLS(y, X_design)
    fit = model.fit(cov_type="HAC", cov_kwds={"maxlags": bw})
    print("\n--- Spec-verbatim primary OLS (HAC SE) ---")
    print(fit.summary(xname=column_names_primary))

    # Composite β: c selects the three lag betas (positions 1,2,3 in [const, lag6, lag9, lag12])
    c_primary = np.array([0.0, 1.0, 1.0, 1.0])
    comp = _composite(fit, c_primary)
    print(f"\nComposite β = β_6 + β_9 + β_12")
    print(f"  point          = {comp.point:.6e}")
    print(f"  HAC SE         = {comp.se_hac:.6e}")
    print(f"  t-stat         = {comp.t_stat:.4f}")
    print(f"  p one-sided    = {comp.p_one_sided:.6f}")
    print(f"  p two-sided    = {comp.p_two_sided:.6f}")
    print(f"  one-sided 95% CI lower = {comp.ci95_lower_one_sided:.6e}")
    print(f"  two-sided 95% CI       = [{comp.ci95_two_sided[0]:.6e}, {comp.ci95_two_sided[1]:.6e}]")

    # Verdict per spec §3.1 PASS-trigger: β_composite > 0 AND p_one_sided ≤ 0.05
    if comp.point > 0 and comp.p_one_sided <= ALPHA_PRIMARY:
        primary_verdict = "PASS"
    else:
        primary_verdict = "FAIL"
    print(f"\nPRIMARY VERDICT (§3.1 / §3.2 trigger primitive): {primary_verdict}")

    # F-test: joint significance of the three lag betas
    R_joint = np.array([
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])
    f_test = fit.f_test(R_joint)
    print(f"\nJoint F-test (β_6 = β_9 = β_12 = 0): F = {float(f_test.fvalue):.4f}, p = {float(f_test.pvalue):.6f}")

    # Diagnostics
    resid = np.asarray(fit.resid)
    diag = _diagnostics(resid, X_design)
    print("\n--- Residual diagnostics (spec-verbatim primary) ---")
    print(f"  Breusch-Pagan LM = {diag['breusch_pagan_lm']:.4f} (p = {diag['breusch_pagan_p']:.4f})")
    print(f"  Durbin-Watson    = {diag['durbin_watson']:.4f}")
    print(f"  Jarque-Bera      = {diag['jarque_bera_stat']:.4f} (p = {diag['jarque_bera_p']:.4f})")
    print(f"  skew             = {diag['skew']:.4f}")
    print(f"  excess kurtosis  = {diag['excess_kurtosis']:.4f}")
    print(f"  ADF on residuals = {diag['adf_stat']:.4f} (p = {diag['adf_p']:.4f})")
    print(f"  Ljung-Box L=4    = {diag['ljung_box_lag4_stat']:.4f} (p = {diag['ljung_box_lag4_p']:.4f})")
    print(f"  Ljung-Box L=12   = {diag['ljung_box_lag12_stat']:.4f} (p = {diag['ljung_box_lag12_p']:.4f})")

    # Individual lag-sign pattern
    individual = {}
    for i, col in enumerate(["log_cop_usd_lag6", "log_cop_usd_lag9", "log_cop_usd_lag12"], start=1):
        b = float(fit.params[i])
        se = float(fit.bse[i])
        t_individual = b / se if se > 0 else float("nan")
        p_two_individual = float(2.0 * (1.0 - stats.norm.cdf(abs(t_individual))))
        sign = "+" if b > 0 else ("-" if b < 0 else "0")
        individual[col] = {
            "point": b,
            "se_hac": se,
            "t": t_individual,
            "p_two_sided": p_two_individual,
            "sign": sign,
        }
    sign_pattern = "/".join(individual[c]["sign"] for c in
                            ["log_cop_usd_lag6", "log_cop_usd_lag9", "log_cop_usd_lag12"])
    print(f"\nIndividual lag-sign pattern (β_6/β_9/β_12): {sign_pattern}")

    # --- Off-spec sensitivity (orchestrator-brief variant WITH dummy) -----
    # Documented for transparency; NOT the primary verdict.
    X_with_dummy = np.column_stack([X_design, dummy.to_numpy()])
    column_names_dummy = column_names_primary + ["marco2018_dummy"]
    fit_dummy = sm.OLS(y, X_with_dummy).fit(cov_type="HAC", cov_kwds={"maxlags": bw})
    c_dummy = np.array([0.0, 1.0, 1.0, 1.0, 0.0])
    comp_dummy = _composite(fit_dummy, c_dummy)
    if comp_dummy.point > 0 and comp_dummy.p_one_sided <= ALPHA_PRIMARY:
        dummy_verdict = "PASS"
    else:
        dummy_verdict = "FAIL"
    print(f"\n--- Off-spec sensitivity: orchestrator-brief variant WITH marco2018_dummy ---")
    print(fit_dummy.summary(xname=column_names_dummy))
    print(f"Composite β = {comp_dummy.point:.6e}, HAC SE = {comp_dummy.se_hac:.6e}, "
          f"t = {comp_dummy.t_stat:.4f}, p_one = {comp_dummy.p_one_sided:.6f}")
    print(f"Off-spec verdict: {dummy_verdict}")

    # --- Persist residuals -------------------------------------------------
    resid_df = pd.DataFrame({
        "timestamp_utc": df["timestamp_utc"],
        "y_logit": y,
        "fitted": np.asarray(fit.fittedvalues),
        "residual": resid,
        "leverage": np.asarray(OLSInfluence(fit).hat_matrix_diag),
    })
    resid_df.to_parquet(OUT_RESID, index=False, compression="snappy")
    resid_sha = _file_sha256(OUT_RESID)
    print(f"\nWrote residuals: {OUT_RESID} (sha256 {resid_sha})")

    # --- Persist JSON ------------------------------------------------------
    out: dict[str, Any] = {
        "task": "Pair D Phase 2 Task 2.1 — pre-registered primary OLS",
        "spec_sha256": SPEC_SHA,
        "panel_sha256": panel_sha,
        "panel_path_abs": str(PANEL),
        "n": n,
        "window_start": str(df["timestamp_utc"].min()),
        "window_end": str(df["timestamp_utc"].max()),
        "marco2018_dummy_count_ones": n_dummy_ones,  # informational only
        "newey_west_bandwidth": bw,
        "alpha_primary_one_sided": ALPHA_PRIMARY,
        "primary_spec_verbatim_per_spec_§5_3": True,
        "orchestrator_brief_contradiction": {
            "flag": True,
            "explanation": (
                "Orchestrator Phase-2 brief specified a primary OLS that includes a "
                "marco2018_dummy (1 if t ≥ 2021-01-01 else 0). This contradicts spec §5.3 "
                "verbatim, which has NO dummy in the primary; per §6 the dummy is the R1 "
                "robustness alternative ONLY, and per §9.1 / §9.2 / §9.7 the spec governs. "
                "The spec-verbatim primary (no dummy) is the AUTHORITATIVE result; the "
                "dummied variant is reported as an off-spec sensitivity for transparency."
            ),
        },
        "primary_spec_verbatim": {
            "regressors_in_design_matrix_order": column_names_primary,
            "n": n,
            "rsquared": float(fit.rsquared),
            "rsquared_adj": float(fit.rsquared_adj),
            "f_pvalue_overall": float(fit.f_pvalue),
            "joint_lags_F": float(f_test.fvalue),
            "joint_lags_p": float(f_test.pvalue),
            "coefficients": {
                "const": {
                    "point": float(fit.params[0]),
                    "se_hac": float(fit.bse[0]),
                    "t": float(fit.params[0] / fit.bse[0]),
                    "p_two_sided": float(fit.pvalues[0]),
                },
                **individual,
            },
            "composite_beta": {
                "definition": "β_composite = β_6 + β_9 + β_12",
                "contrast_vector_c": c_primary.tolist(),
                "point": comp.point,
                "se_hac": comp.se_hac,
                "t_stat": comp.t_stat,
                "p_one_sided": comp.p_one_sided,
                "p_two_sided": comp.p_two_sided,
                "ci95_lower_one_sided": comp.ci95_lower_one_sided,
                "ci95_two_sided_lower": comp.ci95_two_sided[0],
                "ci95_two_sided_upper": comp.ci95_two_sided[1],
                "verdict_alpha_05_one_sided": primary_verdict,
            },
            "individual_lag_sign_pattern_b6_b9_b12": sign_pattern,
            "diagnostics": diag,
            "hac_cov_matrix": np.asarray(fit.cov_params()).tolist(),
        },
        "off_spec_sensitivity_orchestrator_brief": {
            "regressors_in_design_matrix_order": column_names_dummy,
            "n": n,
            "rsquared": float(fit_dummy.rsquared),
            "coefficients": {
                column_names_dummy[i]: {
                    "point": float(fit_dummy.params[i]),
                    "se_hac": float(fit_dummy.bse[i]),
                }
                for i in range(len(column_names_dummy))
            },
            "composite_beta": {
                "point": comp_dummy.point,
                "se_hac": comp_dummy.se_hac,
                "t_stat": comp_dummy.t_stat,
                "p_one_sided": comp_dummy.p_one_sided,
                "ci95_lower_one_sided": comp_dummy.ci95_lower_one_sided,
                "verdict_alpha_05_one_sided": dummy_verdict,
            },
        },
        "reproducibility": {
            "seed_numpy": SEED,
            "python_version": sys.version,
            "platform": platform.platform(),
            "package_versions": {
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "statsmodels": sm.__version__,
                "scipy": stats.norm.__module__.split(".")[0]
                + " (scipy "
                + __import__("scipy").__version__
                + ")",
            },
        },
        "outputs": {
            "primary_ols_json_abs": str(OUT_JSON),
            "primary_ols_residuals_parquet_abs": str(OUT_RESID),
            "primary_ols_residuals_sha256": resid_sha,
        },
    }

    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=2, default=str, sort_keys=False)
    json_sha = _file_sha256(OUT_JSON)
    print(f"Wrote JSON: {OUT_JSON} (sha256 {json_sha})")

    print("\n=== SUMMARY (orchestrator-facing) ===")
    print(f"primary_verdict_spec_verbatim    = {primary_verdict}")
    print(f"off_spec_dummy_verdict           = {dummy_verdict}")
    print(f"composite_beta_spec_verbatim     = {comp.point:.6e}")
    print(f"composite_se_hac                 = {comp.se_hac:.6e}")
    print(f"composite_t                      = {comp.t_stat:.4f}")
    print(f"composite_p_one_sided            = {comp.p_one_sided:.6f}")
    print(f"individual_sign_pattern          = {sign_pattern}")
    print(f"primary_ols_json_sha256          = {json_sha}")
    print(f"primary_ols_residuals_sha256     = {resid_sha}")


if __name__ == "__main__":
    main()
