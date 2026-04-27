"""TDD red-first tests for Task 11.O Rev-2 Phase 5b Analytics Reporter.

Per ``feedback_strict_tdd``: every implementation symbol below MUST first be
asserted in this test file with a verified red phase before any implementation
code is admitted.

Per ``feedback_real_data_over_mocks``: tests consume the real Phase-5a panel
parquets, not synthetic fixtures. Synthetic data is admitted ONLY for
gate-classifier sanity (a known synthetic case where the gate verdict is
mathematically determinate).

Verification mechanism (matches ``feedback_implementation_review_agents``):
the green phase is reproducible via::

    cd contracts && source .venv/bin/activate
    PYTHONPATH=. python -m pytest scripts/tests/inequality/test_phase5b_analytics.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pytest

# Spec & data paths (frozen at Phase-5a commit `2eed63994`).
_SPEC_PATH = Path(__file__).resolve().parents[3] / ".scratch" / "2026-04-25-task110-rev2-spec-A-autonomous.md"
_PANEL_DIR = Path(__file__).resolve().parents[3] / ".scratch" / "2026-04-25-task110-rev2-data"
_OUTPUT_DIR = Path(__file__).resolve().parents[3] / ".scratch" / "2026-04-25-task110-rev2-analysis"


def _read_panel_parquet(path: Path) -> pd.DataFrame:
    """Phase-5a parquets are DuckDB-native ZSTD-compressed; read via duckdb."""
    con = duckdb.connect()
    df = con.sql(f"SELECT * FROM '{path.as_posix()}'").df()
    con.close()
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Section 0: import contract (ModuleNotFoundError on red, import on green)
# ─────────────────────────────────────────────────────────────────────────────


def test_phase5_analytics_module_importable() -> None:
    """The analytics module must import without error."""
    import scripts.phase5_analytics  # noqa: F401


def test_public_api_symbols_exposed() -> None:
    """Every load-bearing symbol in scripts.phase5_analytics is exposed."""
    import scripts.phase5_analytics as mod

    for name in (
        "RegressionResult",
        "GateVerdict",
        "fit_ols_hac",
        "fit_bootstrap",
        "fit_student_t",
        "compute_gate_verdict",
        "T3B_CRITICAL_VALUE",
        "PRE_REGISTERED_SIGN",
        "ALPHA_ONE_SIDED",
    ):
        assert hasattr(mod, name), f"missing public symbol: {name}"


# ─────────────────────────────────────────────────────────────────────────────
# Section 1: panel-consumption contract
# ─────────────────────────────────────────────────────────────────────────────


def test_primary_panel_parquet_loads_with_76_rows() -> None:
    """Sanity: Phase-5a primary panel artifact is consumable."""
    df = _read_panel_parquet(_PANEL_DIR / "panel_row_01_primary.parquet")
    assert len(df) == 76
    for col in (
        "week_start",
        "y3_value",
        "x_d",
        "vix_avg",
        "oil_return",
        "us_cpi_surprise",
        "banrep_rate_surprise",
        "fed_funds_weekly",
        "intervention_dummy",
    ):
        assert col in df.columns


# ─────────────────────────────────────────────────────────────────────────────
# Section 2: estimation contract — fit_ols_hac
# ─────────────────────────────────────────────────────────────────────────────


def test_fit_ols_hac_returns_regression_result_on_primary() -> None:
    """fit_ols_hac on Row-1 primary returns a populated RegressionResult."""
    from scripts.phase5_analytics import (
        RegressionResult,
        SIX_CONTROL_COLUMNS,
        fit_ols_hac,
    )

    df = _read_panel_parquet(_PANEL_DIR / "panel_row_01_primary.parquet")
    result = fit_ols_hac(df, x_col="x_d", y_col="y3_value", control_cols=SIX_CONTROL_COLUMNS, hac_lag=4)

    assert isinstance(result, RegressionResult)
    assert result.n == 76
    assert np.isfinite(result.beta_hat)
    assert np.isfinite(result.se)
    assert result.se > 0.0
    assert np.isfinite(result.t_stat)
    assert 0.0 < result.p_value_one_sided < 1.0
    assert result.lower_90_one_sided == pytest.approx(result.beta_hat - 1.28 * result.se, rel=1e-9)


def test_hac_se_differs_from_naive_ols_se() -> None:
    """Sanity: HAC and homoskedastic-OLS SEs are not identical (autocorrelation).

    They CAN coincide to many decimals, but on a real 76-week panel with
    serial correlation the two SEs differ by more than 1e-9.
    """
    import statsmodels.api as sm

    from scripts.phase5_analytics import SIX_CONTROL_COLUMNS, fit_ols_hac

    df = _read_panel_parquet(_PANEL_DIR / "panel_row_01_primary.parquet")
    result_hac = fit_ols_hac(df, x_col="x_d", y_col="y3_value", control_cols=SIX_CONTROL_COLUMNS, hac_lag=4)

    X = sm.add_constant(df[["x_d", *SIX_CONTROL_COLUMNS]].astype(float))
    naive = sm.OLS(df["y3_value"].astype(float), X).fit()
    naive_se_x_d = naive.bse["x_d"]

    assert abs(result_hac.se - naive_se_x_d) > 1e-9, "HAC SE collapsed to naive OLS SE"


# ─────────────────────────────────────────────────────────────────────────────
# Section 3: gate verdict logic — compute_gate_verdict
# ─────────────────────────────────────────────────────────────────────────────


def test_gate_verdict_pass_on_synthetic_strict_positive() -> None:
    """Known-PASS synthetic: β=0.5, SE=0.1 ⇒ lower-90 = 0.5 − 1.28·0.1 = 0.372 > 0."""
    from scripts.phase5_analytics import GateVerdict, compute_gate_verdict

    verdict = compute_gate_verdict(beta_hat=0.5, se=0.1, n=76)
    assert verdict.gate == "PASS"
    assert isinstance(verdict, GateVerdict)
    assert verdict.lower_90_one_sided == pytest.approx(0.5 - 1.28 * 0.1, rel=1e-9)


def test_gate_verdict_fail_on_synthetic_negative_beta() -> None:
    """β = −0.005 < 0 ⇒ FAIL regardless of SE (sign-locked one-sided)."""
    from scripts.phase5_analytics import compute_gate_verdict

    verdict = compute_gate_verdict(beta_hat=-0.005, se=0.001, n=76)
    assert verdict.gate == "FAIL"


def test_gate_verdict_fail_on_synthetic_ci_contains_zero() -> None:
    """β=0.05 SE=0.05: lower-90 = 0.05 − 1.28·0.05 = −0.014 ≤ 0 ⇒ FAIL."""
    from scripts.phase5_analytics import compute_gate_verdict

    verdict = compute_gate_verdict(beta_hat=0.05, se=0.05, n=76)
    assert verdict.gate == "FAIL"
    assert verdict.lower_90_one_sided < 0


# ─────────────────────────────────────────────────────────────────────────────
# Section 4: pre-registered FAIL rows must FAIL the gate (sample-driven)
# ─────────────────────────────────────────────────────────────────────────────


def test_row_3_locf_excluded_n_below_75_and_pre_registered_fail() -> None:
    """Row 3 (LOCF-tail-excluded) is pre-registered as FAIL on N_MIN=75."""
    df = _read_panel_parquet(_PANEL_DIR / "panel_row_03_locf_tail_excluded.parquet")
    assert len(df) == 65
    assert len(df) < 75


def test_row_4_imf_only_n_below_75_and_pre_registered_fail() -> None:
    """Row 4 (IMF-only) pre-registered FAIL on dual axis (N=56 + power=0.7301)."""
    df = _read_panel_parquet(_PANEL_DIR / "panel_row_04_imf_only_sensitivity.parquet")
    assert len(df) == 56
    assert len(df) < 75


# ─────────────────────────────────────────────────────────────────────────────
# Section 5: deferred row contract
# ─────────────────────────────────────────────────────────────────────────────


def test_deferred_rows_9_and_10_have_zero_observations() -> None:
    """Rows 9 + 10 are explicit deferred placeholders (Phase-5a contract)."""
    for filename in ("panel_row_09_y3_bond_diagnostic.parquet", "panel_row_10_population_weighted.parquet"):
        df = _read_panel_parquet(_PANEL_DIR / filename)
        assert len(df) == 0, f"{filename} expected to be deferred-empty"


# ─────────────────────────────────────────────────────────────────────────────
# Section 6: bootstrap reconciliation contract
# ─────────────────────────────────────────────────────────────────────────────


def test_fit_bootstrap_returns_regression_result_on_primary() -> None:
    """Politis-Romano stationary block bootstrap returns a RegressionResult."""
    from scripts.phase5_analytics import (
        RegressionResult,
        SIX_CONTROL_COLUMNS,
        fit_bootstrap,
    )

    df = _read_panel_parquet(_PANEL_DIR / "panel_row_01_primary.parquet")
    rng = np.random.default_rng(42)
    result = fit_bootstrap(
        df,
        x_col="x_d",
        y_col="y3_value",
        control_cols=SIX_CONTROL_COLUMNS,
        mean_block_length=4,
        n_resamples=200,  # small for test speed; analysis script uses 10000
        rng=rng,
    )

    assert isinstance(result, RegressionResult)
    assert result.n == 76
    assert np.isfinite(result.se)
    assert result.se > 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Section 7: Student-t innovation refit contract
# ─────────────────────────────────────────────────────────────────────────────


def test_fit_student_t_returns_regression_result() -> None:
    """Student-t MLE refit on Row 1 returns a populated RegressionResult."""
    from scripts.phase5_analytics import (
        RegressionResult,
        SIX_CONTROL_COLUMNS,
        fit_student_t,
    )

    df = _read_panel_parquet(_PANEL_DIR / "panel_row_01_primary.parquet")
    result = fit_student_t(
        df,
        x_col="x_d",
        y_col="y3_value",
        control_cols=SIX_CONTROL_COLUMNS,
    )

    assert isinstance(result, RegressionResult)
    assert result.n == 76
    assert np.isfinite(result.beta_hat)
    assert np.isfinite(result.se)
    assert result.se > 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Section 8: gate_verdict.json output schema contract
# ─────────────────────────────────────────────────────────────────────────────


_REQUIRED_GATE_VERDICT_KEYS = {
    "gate_verdict",
    "row_1_beta_hat",
    "row_1_se",
    "row_1_lower_90",
    "row_1_n",
    "pre_committed_fails_actual",
    "anti_fishing_invariants_intact",
}


def test_gate_verdict_json_schema_when_present() -> None:
    """If estimates have been written, the JSON file must match schema."""
    output_path = _OUTPUT_DIR / "gate_verdict.json"
    if not output_path.exists():
        pytest.skip("gate_verdict.json not yet produced (run analysis first)")

    with output_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    missing = _REQUIRED_GATE_VERDICT_KEYS - set(payload.keys())
    assert not missing, f"missing JSON keys: {missing}"
    assert payload["gate_verdict"] in {"PASS", "FAIL", "HALT"}
    assert payload["row_1_n"] == 76
    assert isinstance(payload["row_1_beta_hat"], (int, float))
    assert isinstance(payload["row_1_se"], (int, float))
    assert isinstance(payload["row_1_lower_90"], (int, float))
    assert payload["row_1_lower_90"] == pytest.approx(
        payload["row_1_beta_hat"] - 1.28 * payload["row_1_se"], rel=1e-6
    )
    pcf = payload["pre_committed_fails_actual"]
    assert "row_3" in pcf and pcf["row_3"] in {"FAIL", "UNEXPECTED-PASS"}
    assert "row_4" in pcf and pcf["row_4"] in {"FAIL", "UNEXPECTED-PASS"}
    assert isinstance(payload["anti_fishing_invariants_intact"], bool)


# ─────────────────────────────────────────────────────────────────────────────
# Section 9: pre-registered constants (anti-fishing audit)
# ─────────────────────────────────────────────────────────────────────────────


def test_t3b_critical_value_is_one_point_two_eight() -> None:
    """Spec §7 T3b lock: 1.28 (one-sided 90% Normal critical value)."""
    from scripts.phase5_analytics import T3B_CRITICAL_VALUE

    assert T3B_CRITICAL_VALUE == pytest.approx(1.28, rel=1e-9)


def test_pre_registered_sign_is_positive() -> None:
    """Spec §7 T3b lock: β > 0 (rising X_d → rising inequality differential)."""
    from scripts.phase5_analytics import PRE_REGISTERED_SIGN

    assert PRE_REGISTERED_SIGN == 1


def test_alpha_one_sided_is_zero_point_one_zero() -> None:
    """Spec §5 lock: α = 0.10 one-sided (Rev-4 prior-art)."""
    from scripts.phase5_analytics import ALPHA_ONE_SIDED

    assert ALPHA_ONE_SIDED == pytest.approx(0.10, rel=1e-9)
