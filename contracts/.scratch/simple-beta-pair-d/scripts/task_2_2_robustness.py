"""Task 2.2: Pre-committed robustness pack R1-R4 for Pair D simple-β.

Spec sha256 (sentinel-protocol):
    decision_hash = 964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659
Spec frontmatter: contracts/docs/superpowers/specs/2026-04-27-simple-beta-pair-d-design.md (v1.3.1)

Per spec §7 (verbatim):
    R1 — 2021 regime dummy (alternative to §6 primary methodology-break disposition).
         "Same primary specification but replace empalme with a 2021 regime dummy."
    R2 — Y narrow (CIIU Rev. 4 sections J + M + N — BPO-narrow). Same primary
         specification but recompute Y_t (raw share) with the numerator restricted
         to the BPO-narrow sector set; logit transform unchanged.
    R3 — raw OLS (no logit transform). Dependent variable = raw share Y_t.
    R4 — HAC standard errors (Newey-West, lag truncation L=12). Same regression
         as primary; only the HAC variance differs. β̂_composite is unchanged;
         only SE + p_one_sided change.

R1 IMPLEMENTATION NOTE (resolves brief's "open question").
The brief asks whether the panel admits an "un-empalme'd Y" reconstruction.
DATA_PROVENANCE.md §"Empalme application" (line 268) is authoritative:
    "the in-scope GEIH Empalme catalogs (cid 762, 757, 763, 758, 759, 764) for
    2015-01 → 2020-12 already pre-incorporate the empalme factor in FEX_C ...
    No separate downstream empalme transformation is applied. R1 (2021 regime
    dummy) per spec §7 remains an alternative methodology-break treatment
    applied at the OLS stage (not at this Y-construction stage)."

Independent algebraic confirmation by Task 2.1 author (lines 30-33 of
task_2_1_primary_ols.py):
    "because Y is a ratio of expansion factors (FEX_C or FEX_C18 per era;
    both numerator and denominator use the same FEX), the share is invariant
    to a single multiplicative empalme factor within each month — so empalme
    application is operationally a no-op at the share level".

Mathematically: if FEX_C is multiplied by an empalme scalar f_t per month,
both numerator (Σ FEX·1{services}·f_t) and denominator (Σ FEX·f_t) acquire
the same f_t, which cancels in the ratio. Y_raw is invariant to a uniform
monthly empalme factor.

Operational consequence: R1 = "primary OLS specification + 2021 regime dummy
on the same Y_broad_logit". This is the only feasible interpretation given
DANE's structurally-baked empalme design and is the interpretation
explicitly endorsed by DATA_PROVENANCE.md.

R2 IMPLEMENTATION NOTE.
Spec §5.1 + §7 R2: the J+M+N narrow set is computed at ingest in
geih_young_workers_narrow_share.parquet. The panel parquet exposes
Y_narrow_logit (= log(Y_narrow_raw / (1 - Y_narrow_raw))) directly. R2 swaps
the dependent variable on the same primary regressors {const, lag6, lag9, lag12};
no other change.

R3 IMPLEMENTATION NOTE.
Y_broad_raw replaces Y_broad_logit as dependent variable; otherwise identical
to primary specification.

R4 IMPLEMENTATION NOTE.
Same fitted OLS as primary (β̂ identical); only the HAC covariance is recomputed
with maxlags=12 instead of the rule-of-thumb 4. Composite SE changes; β̂_composite
sign/point unchanged.

Per spec §7.1 (verbatim):
    AGREE     = all 4 R-rows produce β_composite with same sign as primary
    MIXED     = 1-2 R-rows sign-flipped
    DISAGREE  = 3-4 R-rows sign-flipped → triggers SUBSTRATE_TOO_NOISY (§3.5)

Anti-fishing discipline:
    - Each R-row varies exactly ONE design choice from primary.
    - No silent multi-dimensional re-specification.
    - Sign/point/p reported exactly as computed; no verdict pre-judgment.

Reproducibility:
    seed = 42
    statsmodels OLS with cov_type='HAC'
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

WORKTREE = Path("/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom")
PANEL = WORKTREE / "contracts/.scratch/simple-beta-pair-d/data/panel_combined.parquet"
EXPECTED_PANEL_SHA = "6d7d9e60dad1715ce86e8adb7b3d44ba236d0b063796293b40575994a9363edf"

PRIMARY_JSON = WORKTREE / "contracts/.scratch/simple-beta-pair-d/results/primary_ols.json"
EXPECTED_PRIMARY_SHA = "d4790e743cdec62f1368cab1833e1266cb2da763d7c0931dd732bdf3d17938cf"

RESULTS = WORKTREE / "contracts/.scratch/simple-beta-pair-d/results"
OUT_JSON = RESULTS / "robustness_pack.json"
OUT_FINDINGS = RESULTS / "task_2_2_findings.md"

SPEC_SHA = "964c62cca0be1b9070944b5398fe97886c6d07d37ba7121199de8ccc341ef659"
SEED = 42


def _newey_west_bandwidth(n: int) -> int:
    return int(np.floor(4.0 * (n / 100.0) ** (2.0 / 9.0)))


def _file_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@dataclass(frozen=True)
class CompositeBeta:
    point: float
    se_hac: float
    t_stat: float
    p_one_sided: float
    p_two_sided: float
    ci95_lower_one_sided: float


def _composite_from_fit(
    fit: sm.regression.linear_model.RegressionResults, c: np.ndarray
) -> CompositeBeta:
    """Composite β + HAC SE via linear-restriction variance Var(c'β̂) = c'Σ̂c."""
    beta_hat = np.asarray(fit.params)
    sigma_hac = np.asarray(fit.cov_params())
    point = float(c @ beta_hat)
    var_comp = float(c @ sigma_hac @ c)
    if var_comp < 0:
        raise ValueError(f"Composite variance {var_comp} < 0")
    se = float(np.sqrt(var_comp))
    t = point / se if se > 0 else float("nan")
    p_one = float(1.0 - stats.norm.cdf(t))
    p_two = float(2.0 * (1.0 - stats.norm.cdf(abs(t))))
    z95 = float(stats.norm.ppf(0.95))
    ci_one_lower = point - z95 * se
    return CompositeBeta(
        point=point,
        se_hac=se,
        t_stat=t,
        p_one_sided=p_one,
        p_two_sided=p_two,
        ci95_lower_one_sided=ci_one_lower,
    )


def _coef_table(
    fit: sm.regression.linear_model.RegressionResults, names: list[str]
) -> dict[str, dict[str, float | str]]:
    """Per-coefficient point + HAC SE + t + 2-sided p; sign for lag betas."""
    out: dict[str, dict[str, float | str]] = {}
    for i, name in enumerate(names):
        b = float(fit.params[i])
        se = float(fit.bse[i])
        t = b / se if se > 0 else float("nan")
        p_two = float(2.0 * (1.0 - stats.norm.cdf(abs(t))))
        sign = "+" if b > 0 else ("-" if b < 0 else "0")
        out[name] = {
            "point": b,
            "se_hac": se,
            "t": t,
            "p_two_sided": p_two,
            "sign": sign,
        }
    return out


def _sign(point: float) -> str:
    return "+" if point > 0 else ("-" if point < 0 else "0")


def _consistency_classify(
    primary_sign: str, r_signs: dict[str, str]
) -> tuple[str, dict[str, str]]:
    """Per spec §7.1: AGREE / MIXED / DISAGREE."""
    flips = {k: ("FLIP" if v != primary_sign else "AGREE") for k, v in r_signs.items()}
    n_flips = sum(1 for v in flips.values() if v == "FLIP")
    if n_flips == 0:
        verdict = "AGREE"
    elif n_flips <= 2:
        verdict = "MIXED"
    else:
        verdict = "DISAGREE"
    return verdict, flips


def main() -> None:
    np.random.seed(SEED)

    print("=== Task 2.2: pre-committed robustness pack R1-R4 (spec §7) ===")
    print(f"Spec sha256: {SPEC_SHA}")

    # GATE: panel sha256
    panel_sha = _file_sha256(PANEL)
    print(f"Panel sha256: {panel_sha}")
    if panel_sha != EXPECTED_PANEL_SHA:
        raise RuntimeError(
            f"Panel sha256 mismatch. expected={EXPECTED_PANEL_SHA} got={panel_sha}"
        )
    print("Panel sha256 GATE PASS")

    # GATE: primary_ols.json sha256 (from Task 2.1)
    primary_json_sha = _file_sha256(PRIMARY_JSON)
    print(f"Primary OLS json sha256: {primary_json_sha}")
    if primary_json_sha != EXPECTED_PRIMARY_SHA:
        raise RuntimeError(
            f"primary_ols.json sha256 mismatch. expected={EXPECTED_PRIMARY_SHA} "
            f"got={primary_json_sha}"
        )
    print("primary_ols.json sha256 GATE PASS")

    primary_obj = json.loads(PRIMARY_JSON.read_text())
    primary_comp = primary_obj["primary_spec_verbatim"]["composite_beta"]
    primary_point = float(primary_comp["point"])
    primary_se = float(primary_comp["se_hac"])
    primary_p_one = float(primary_comp["p_one_sided"])
    primary_sign = _sign(primary_point)
    print(
        f"Primary β_composite = {primary_point:.6e} "
        f"(HAC SE {primary_se:.6e}, p_one {primary_p_one:.6e}, sign {primary_sign})"
    )

    # ----- LOAD PANEL ----------
    df = pd.read_parquet(PANEL).sort_values("timestamp_utc").reset_index(drop=True)
    n = len(df)
    if n != 134:
        raise RuntimeError(f"Expected N=134, got {n}")
    bw_default = _newey_west_bandwidth(n)
    print(f"N = {n}, default Newey-West bandwidth = {bw_default}")

    # Common regressors (primary 3-lag design)
    X_lags = df[["log_cop_usd_lag6", "log_cop_usd_lag9", "log_cop_usd_lag12"]].astype(
        float
    ).to_numpy()
    X_design_primary = sm.add_constant(X_lags, prepend=True)  # [const, lag6, lag9, lag12]

    # 2021 regime dummy (1 if t >= 2021-01-01)
    dummy_2021 = (df["timestamp_utc"] >= pd.Timestamp("2021-01-01", tz="UTC")).astype(
        int
    ).to_numpy()
    n_dummy_ones = int(dummy_2021.sum())
    print(f"2021 regime dummy: {n_dummy_ones} ones (2021-01 → 2026-02)")

    # ============================================================
    # R1 — 2021 regime dummy (per spec §7)
    # ============================================================
    print("\n--- R1: primary spec + 2021 regime dummy (§7 line 202) ---")
    X_R1 = np.column_stack([X_design_primary, dummy_2021])
    names_R1 = [
        "const",
        "log_cop_usd_lag6",
        "log_cop_usd_lag9",
        "log_cop_usd_lag12",
        "marco2018_dummy",
    ]
    y_logit = df["Y_broad_logit"].astype(float).to_numpy()
    fit_R1 = sm.OLS(y_logit, X_R1).fit(cov_type="HAC", cov_kwds={"maxlags": bw_default})
    # contrast on (const, lag6, lag9, lag12, dummy) = (0, 1, 1, 1, 0)
    c_R1 = np.array([0.0, 1.0, 1.0, 1.0, 0.0])
    comp_R1 = _composite_from_fit(fit_R1, c_R1)
    coef_R1 = _coef_table(fit_R1, names_R1)
    print(
        f"R1 β_composite = {comp_R1.point:.6e} (HAC SE {comp_R1.se_hac:.6e}, "
        f"t {comp_R1.t_stat:.4f}, p_one {comp_R1.p_one_sided:.6e}, sign {_sign(comp_R1.point)})"
    )
    for k, v in coef_R1.items():
        print(f"   {k}: point={v['point']:+.4e}, SE={v['se_hac']:.4e}, p2={v['p_two_sided']:.4e}")

    # ============================================================
    # R2 — Y_narrow_logit (per spec §7)
    # ============================================================
    print("\n--- R2: primary spec on Y_narrow_logit (§7 line 203) ---")
    y_narrow_logit = df["Y_narrow_logit"].astype(float).to_numpy()
    names_R2 = ["const", "log_cop_usd_lag6", "log_cop_usd_lag9", "log_cop_usd_lag12"]
    fit_R2 = sm.OLS(y_narrow_logit, X_design_primary).fit(
        cov_type="HAC", cov_kwds={"maxlags": bw_default}
    )
    c_R2 = np.array([0.0, 1.0, 1.0, 1.0])
    comp_R2 = _composite_from_fit(fit_R2, c_R2)
    coef_R2 = _coef_table(fit_R2, names_R2)
    print(
        f"R2 β_composite = {comp_R2.point:.6e} (HAC SE {comp_R2.se_hac:.6e}, "
        f"t {comp_R2.t_stat:.4f}, p_one {comp_R2.p_one_sided:.6e}, sign {_sign(comp_R2.point)})"
    )
    for k, v in coef_R2.items():
        print(f"   {k}: point={v['point']:+.4e}, SE={v['se_hac']:.4e}, p2={v['p_two_sided']:.4e}")

    # ============================================================
    # R3 — raw OLS (Y_broad_raw, no logit transform)
    # ============================================================
    print("\n--- R3: primary spec on Y_broad_raw (§7 line 204; no logit) ---")
    y_raw = df["Y_broad_raw"].astype(float).to_numpy()
    names_R3 = ["const", "log_cop_usd_lag6", "log_cop_usd_lag9", "log_cop_usd_lag12"]
    fit_R3 = sm.OLS(y_raw, X_design_primary).fit(
        cov_type="HAC", cov_kwds={"maxlags": bw_default}
    )
    c_R3 = np.array([0.0, 1.0, 1.0, 1.0])
    comp_R3 = _composite_from_fit(fit_R3, c_R3)
    coef_R3 = _coef_table(fit_R3, names_R3)
    print(
        f"R3 β_composite = {comp_R3.point:.6e} (HAC SE {comp_R3.se_hac:.6e}, "
        f"t {comp_R3.t_stat:.4f}, p_one {comp_R3.p_one_sided:.6e}, sign {_sign(comp_R3.point)})"
    )
    for k, v in coef_R3.items():
        print(f"   {k}: point={v['point']:+.4e}, SE={v['se_hac']:.4e}, p2={v['p_two_sided']:.4e}")

    # ============================================================
    # R4 — HAC L=12 (same primary regression; only bandwidth changes)
    # ============================================================
    print("\n--- R4: primary spec, HAC L=12 (§7 line 205; bandwidth-only) ---")
    fit_R4 = sm.OLS(y_logit, X_design_primary).fit(
        cov_type="HAC", cov_kwds={"maxlags": 12}
    )
    names_R4 = ["const", "log_cop_usd_lag6", "log_cop_usd_lag9", "log_cop_usd_lag12"]
    c_R4 = np.array([0.0, 1.0, 1.0, 1.0])
    comp_R4 = _composite_from_fit(fit_R4, c_R4)
    coef_R4 = _coef_table(fit_R4, names_R4)
    # Sanity check: β̂_composite point should equal primary's; only SE differs
    if not np.isclose(comp_R4.point, primary_point, atol=1e-10):
        raise RuntimeError(
            f"R4 point {comp_R4.point} != primary {primary_point}; bandwidth-only "
            "change should leave point unchanged"
        )
    print(
        f"R4 β_composite = {comp_R4.point:.6e} (HAC SE {comp_R4.se_hac:.6e}, "
        f"t {comp_R4.t_stat:.4f}, p_one {comp_R4.p_one_sided:.6e}, sign {_sign(comp_R4.point)})"
    )
    print(f"   (point identical to primary {primary_point:.6e}; only SE/p change.)")
    for k, v in coef_R4.items():
        print(f"   {k}: point={v['point']:+.4e}, SE={v['se_hac']:.4e}, p2={v['p_two_sided']:.4e}")

    # ============================================================
    # Consistency classification (spec §7.1)
    # ============================================================
    r_signs = {
        "R1": _sign(comp_R1.point),
        "R2": _sign(comp_R2.point),
        "R3": _sign(comp_R3.point),
        "R4": _sign(comp_R4.point),
    }
    consistency, per_row_flips = _consistency_classify(primary_sign, r_signs)
    n_flips = sum(1 for v in per_row_flips.values() if v == "FLIP")
    print("\n=== R-consistency (§7.1) ===")
    print(f"Primary sign: {primary_sign}")
    for k, v in r_signs.items():
        print(f"   {k} sign: {v}  ({per_row_flips[k]})")
    print(f"Number of flips: {n_flips}")
    print(f"Verdict: {consistency}")
    substrate_too_noisy_fires = consistency == "DISAGREE"
    print(f"SUBSTRATE_TOO_NOISY would fire (§3.5): {substrate_too_noisy_fires}")

    # ============================================================
    # Persist JSON
    # ============================================================
    def _row_dict(
        name: str,
        description: str,
        comp: CompositeBeta,
        coef: dict[str, dict[str, float | str]],
        regressors: list[str],
    ) -> dict[str, Any]:
        return {
            "row": name,
            "description": description,
            "regressors_in_design_matrix_order": regressors,
            "n": n,
            "coefficients": coef,
            "composite_beta": {
                "definition": "β_composite = β_6 + β_9 + β_12",
                "point": comp.point,
                "se_hac": comp.se_hac,
                "t_stat": comp.t_stat,
                "p_one_sided": comp.p_one_sided,
                "p_two_sided": comp.p_two_sided,
                "ci95_lower_one_sided": comp.ci95_lower_one_sided,
                "sign": _sign(comp.point),
                "vs_primary": per_row_flips[name],
            },
        }

    out: dict[str, Any] = {
        "task": "Pair D Phase 2 Task 2.2 — pre-committed robustness pack R1-R4",
        "spec_sha256": SPEC_SHA,
        "spec_version": "1.3.1",
        "panel_sha256": panel_sha,
        "primary_ols_json_sha256": primary_json_sha,
        "n": n,
        "newey_west_bandwidth_default_R1_R2_R3": bw_default,
        "newey_west_bandwidth_R4": 12,
        "primary_reference": {
            "composite_point": primary_point,
            "composite_se_hac": primary_se,
            "composite_p_one_sided": primary_p_one,
            "composite_sign": primary_sign,
        },
        "r1_implementation_note": (
            "R1 = primary OLS specification + 2021 regime dummy. The DANE empalme is "
            "structurally pre-baked into FEX_C for the 2015-2020 era; per "
            "DATA_PROVENANCE.md line 268 'No separate downstream empalme transformation "
            "is applied' and per the algebraic identity Y = (Σ FEX·1{services}·f_t) / "
            "(Σ FEX·f_t) = (Σ FEX·1{services}) / (Σ FEX), Y_raw is invariant to a "
            "uniform multiplicative empalme factor. Therefore 'replace empalme with "
            "dummy' is operationally identical to 'add dummy to primary'. This is the "
            "interpretation explicitly endorsed by DATA_PROVENANCE.md."
        ),
        "r1_2021_regime_dummy_count_ones": n_dummy_ones,
        "rows": {
            "R1": _row_dict(
                "R1",
                "2021 regime dummy (alternative to §6 primary methodology-break "
                "disposition); same primary regressors + dummy_2021",
                comp_R1,
                coef_R1,
                names_R1,
            ),
            "R2": _row_dict(
                "R2",
                "Y narrow (CIIU Rev.4 J+M+N — BPO-narrow); Y_narrow_logit replaces "
                "Y_broad_logit; logit transform unchanged",
                comp_R2,
                coef_R2,
                names_R2,
            ),
            "R3": _row_dict(
                "R3",
                "Raw OLS (no logit transform); Y_broad_raw replaces Y_broad_logit",
                comp_R3,
                coef_R3,
                names_R3,
            ),
            "R4": _row_dict(
                "R4",
                "HAC standard errors with maxlags=12 (autocorrelation-diagnostic "
                "bandwidth); same point estimate as primary, only SE differs",
                comp_R4,
                coef_R4,
                names_R4,
            ),
        },
        "r_consistency": {
            "primary_sign": primary_sign,
            "per_row_signs": r_signs,
            "per_row_flips": per_row_flips,
            "n_flips": n_flips,
            "verdict_per_§7_1": consistency,
            "substrate_too_noisy_fires_per_§3_5": substrate_too_noisy_fires,
        },
        "anti_fishing_compliance": {
            "single_dimension_per_row": True,
            "no_silent_re_specification": True,
            "no_threshold_tuning": True,
            "comment": (
                "Each R-row varies exactly one design choice from the primary per "
                "spec §7 line 200. R1=dummy added; R2=narrow Y; R3=raw Y (drop "
                "logit); R4=HAC bandwidth. No row varies two or more dimensions "
                "simultaneously."
            ),
        },
        "reproducibility": {
            "seed_numpy": SEED,
            "python_version": sys.version,
            "platform": platform.platform(),
            "package_versions": {
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "statsmodels": sm.__version__,
                "scipy": __import__("scipy").__version__,
            },
        },
        "outputs": {
            "robustness_pack_json_abs": str(OUT_JSON),
            "task_2_2_findings_md_abs": str(OUT_FINDINGS),
        },
    }

    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=2, default=str, sort_keys=False)
    json_sha = _file_sha256(OUT_JSON)
    print(f"\nWrote JSON: {OUT_JSON} (sha256 {json_sha})")

    # ============================================================
    # Persist findings memo (under 700 words)
    # ============================================================
    findings_lines: list[str] = []
    findings_lines.append("# Task 2.2 — Robustness pack R1-R4 findings")
    findings_lines.append("")
    findings_lines.append(f"Spec sha256: `{SPEC_SHA}` (v1.3.1)")
    findings_lines.append(f"Panel sha256: `{panel_sha}`")
    findings_lines.append(f"Primary OLS json sha256: `{primary_json_sha}`")
    findings_lines.append(f"This file's parent JSON sha256: `{json_sha}`")
    findings_lines.append("")
    findings_lines.append(
        f"**Primary reference (Task 2.1):** β_composite = "
        f"{primary_point:+.4f} (HAC SE {primary_se:.4f}, "
        f"p_one = {primary_p_one:.2e}, sign = {primary_sign})."
    )
    findings_lines.append("")
    findings_lines.append("## R1 — 2021 regime dummy (§6 alternative disposition)")
    findings_lines.append("")
    findings_lines.append(
        "*Implementation:* primary regressors {const, lag6, lag9, lag12} + "
        f"`marco2018_dummy_t` (1 if t ≥ 2021-01-01; {n_dummy_ones} ones in N={n}). "
        "Per DATA_PROVENANCE.md line 268, the DANE empalme is structurally pre-baked "
        "into `FEX_C` for 2015-2020; algebraic identity confirms Y_raw is invariant "
        "to any uniform monthly empalme scalar (numerator + denominator cancel). "
        "R1 therefore = primary + dummy at the OLS stage."
    )
    findings_lines.append("")
    findings_lines.append(
        f"β_composite = **{comp_R1.point:+.4f}** "
        f"(HAC SE {comp_R1.se_hac:.4f}, t = {comp_R1.t_stat:+.3f}, "
        f"p_one = {comp_R1.p_one_sided:.2e}, sign = **{_sign(comp_R1.point)}** "
        f"vs primary `{primary_sign}` → **{per_row_flips['R1']}**)."
    )
    findings_lines.append("")
    findings_lines.append("## R2 — Y narrow (CIIU Rev. 4 J+M+N, BPO-narrow)")
    findings_lines.append("")
    findings_lines.append(
        "*Implementation:* primary regressors unchanged; dependent variable swapped "
        "from `Y_broad_logit` to `Y_narrow_logit`. Y_narrow has empirical range "
        "≈ [0.07, 0.12] (interior to (0,1); logit valid)."
    )
    findings_lines.append("")
    findings_lines.append(
        f"β_composite = **{comp_R2.point:+.4f}** "
        f"(HAC SE {comp_R2.se_hac:.4f}, t = {comp_R2.t_stat:+.3f}, "
        f"p_one = {comp_R2.p_one_sided:.2e}, sign = **{_sign(comp_R2.point)}** "
        f"vs primary `{primary_sign}` → **{per_row_flips['R2']}**)."
    )
    findings_lines.append("")
    findings_lines.append("## R3 — Raw OLS (no logit transform)")
    findings_lines.append("")
    findings_lines.append(
        "*Implementation:* primary regressors unchanged; dependent variable swapped "
        "from `Y_broad_logit` to `Y_broad_raw` (level share, range ≈ [0.60, 0.68])."
    )
    findings_lines.append("")
    findings_lines.append(
        f"β_composite = **{comp_R3.point:+.4f}** "
        f"(HAC SE {comp_R3.se_hac:.4f}, t = {comp_R3.t_stat:+.3f}, "
        f"p_one = {comp_R3.p_one_sided:.2e}, sign = **{_sign(comp_R3.point)}** "
        f"vs primary `{primary_sign}` → **{per_row_flips['R3']}**). "
        "Coefficient magnitudes are smaller in level-units than logit-units, as expected."
    )
    findings_lines.append("")
    findings_lines.append("## R4 — HAC bandwidth L=12")
    findings_lines.append("")
    findings_lines.append(
        f"*Implementation:* identical primary OLS; HAC `maxlags=12` instead of the "
        f"rule-of-thumb {bw_default}. β̂_composite is mechanically unchanged "
        f"({comp_R4.point:+.4f} = primary {primary_point:+.4f}); only HAC SE changes."
    )
    findings_lines.append("")
    findings_lines.append(
        f"β_composite = **{comp_R4.point:+.4f}** "
        f"(HAC SE {comp_R4.se_hac:.4f}, t = {comp_R4.t_stat:+.3f}, "
        f"p_one = {comp_R4.p_one_sided:.2e}, sign = **{_sign(comp_R4.point)}** "
        f"vs primary `{primary_sign}` → **{per_row_flips['R4']}**)."
    )
    findings_lines.append("")
    findings_lines.append("## R-consistency verdict (§7.1)")
    findings_lines.append("")
    findings_lines.append(f"Primary sign: `{primary_sign}`")
    findings_lines.append("")
    findings_lines.append("| R-row | Sign | Match vs primary |")
    findings_lines.append("|-------|------|------------------|")
    for k in ("R1", "R2", "R3", "R4"):
        match = "AGREE" if per_row_flips[k] == "AGREE" else "FLIP"
        findings_lines.append(f"| {k} | `{r_signs[k]}` | {match} |")
    findings_lines.append("")
    findings_lines.append(
        f"**Number of sign-flips:** {n_flips} of 4. "
        f"**Verdict per §7.1:** **{consistency}**."
    )
    findings_lines.append("")
    if substrate_too_noisy_fires:
        findings_lines.append(
            "**SUBSTRATE_TOO_NOISY (§3.5) fires:** ≥3 R-rows sign-flipped relative to "
            "the primary. Per §8.1 rule 2, this overrides the primary's PASS verdict."
        )
    else:
        findings_lines.append(
            f"**SUBSTRATE_TOO_NOISY (§3.5) does NOT fire** (only {n_flips}/4 flips; "
            "trigger requires ≥3). Primary verdict from §3.1 (PASS) is preserved into "
            "Task 2.3."
        )
    findings_lines.append("")
    findings_lines.append(
        "*Anti-fishing compliance:* each R-row varies exactly one design choice from "
        "the primary per spec §7 line 200. No multi-dimensional re-specification. "
        "Sign + p reported as computed; no verdict pre-judgment."
    )
    findings_lines.append("")

    OUT_FINDINGS.write_text("\n".join(findings_lines))
    findings_sha = _file_sha256(OUT_FINDINGS)
    print(f"Wrote findings: {OUT_FINDINGS} (sha256 {findings_sha})")

    # Word count check
    word_count = sum(len(line.split()) for line in findings_lines)
    print(f"Findings word count: {word_count} (limit 700)")
    if word_count > 700:
        print(f"WARNING: findings exceeds 700 words ({word_count})")

    print("\n=== SUMMARY (orchestrator-facing) ===")
    print(f"R1 β_composite = {comp_R1.point:+.6e}, p_one = {comp_R1.p_one_sided:.2e}, sign = {_sign(comp_R1.point)} ({per_row_flips['R1']})")
    print(f"R2 β_composite = {comp_R2.point:+.6e}, p_one = {comp_R2.p_one_sided:.2e}, sign = {_sign(comp_R2.point)} ({per_row_flips['R2']})")
    print(f"R3 β_composite = {comp_R3.point:+.6e}, p_one = {comp_R3.p_one_sided:.2e}, sign = {_sign(comp_R3.point)} ({per_row_flips['R3']})")
    print(f"R4 β_composite = {comp_R4.point:+.6e}, p_one = {comp_R4.p_one_sided:.2e}, sign = {_sign(comp_R4.point)} ({per_row_flips['R4']})")
    print(f"R-consistency verdict (§7.1): {consistency}")
    print(f"SUBSTRATE_TOO_NOISY fires: {substrate_too_noisy_fires}")
    print(f"robustness_pack.json sha256: {json_sha}")
    print(f"task_2_2_findings.md sha256: {findings_sha}")


if __name__ == "__main__":
    main()
