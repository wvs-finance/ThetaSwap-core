"""TDD tests for Rev-5.3 Task 11.N.2c — Carbon-basket calibration.

Plan:    contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md
         §Task 11.N.2c lines 1024-1089 (incl. CORRECTIONS block + §0.3
         MDES formulation pin block + Anti-fishing guard)
Memo:    contracts/.scratch/2026-04-25-carbon-basket-gate-decision-memo.md
Corrigendum: contracts/.scratch/2026-04-25-carbon-basket-gate-memo-corrigendum.md
Design doc: contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md
            (§1, §2, §3 — immutable)

STRICT TDD: tests must fail on ImportError until ``carbon_calibration``
exposes the documented API; subsequent tests must fail on missing
behaviour until each step lands.

Test groups (Step 0 → Step 5 — mirrors plan body):

  Step 0 (constants + pinned source):
    * MDES_FORMULATION_HASH matches live SHA256 of required_power source
    * N_MIN == 80, POWER_MIN == 0.80, MDES_SD == 0.40, PC1_LOADING_FLOOR == 0.40
    * required_power(80, 13, 0.40) ≈ 0.888 (within 1e-3)
    * required_power(80, 13, 0.40) >= POWER_MIN

  Step 1 (compute_basket_calibration PASS branch):
    * synthetic 6-currency panel with basket-aggregate >= N_MIN non-zero
      weeks returns CalibrationResult with:
        - primary_choice == "basket_aggregate"
        - decision_branch == "PASS"
        - basket_n_nonzero_obs equals the count
        - per_currency_pc1_loadings has all six currencies
        - basket_pc1_variance_explained in [0, 1]

  Step 1.b (independent-reproduction witness):
    * second compute path (numpy explicit standardization +
      covariance-matrix eigendecomposition) reproduces PC1
      variance-explained share to within 1e-6 of sklearn output

  Step 5 (HALT-on-pathological):
    * synthetic panel with basket-aggregate < N_MIN non-zero weeks
      raises CalibrationStructurallyPathological with the structured
      payload (basket_n_nonzero_obs, n_min, rationale)
"""
from __future__ import annotations

import hashlib
import inspect
import math
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

# Module under test — import at top so any ImportError surfaces eagerly.
from scripts import carbon_calibration as cc
from scripts.carbon_calibration import (
    CalibrationResult,
    CalibrationStructurallyPathological,
    compute_basket_calibration,
    required_power,
)


# ─────────────────────────────────────────────────────────────────────
# Step 0 — pre-committed thresholds + pinned ``required_power`` source
# ─────────────────────────────────────────────────────────────────────


class TestStep0Constants:
    """Module-level Final constants match the design-doc + corrections values byte-exact."""

    def test_n_min_is_80(self) -> None:
        assert cc.N_MIN == 80, "N_MIN must equal 80 per design doc §3"

    def test_power_min_is_080(self) -> None:
        assert cc.POWER_MIN == 0.80, "POWER_MIN must equal 0.80 per design doc §3"

    def test_mdes_sd_is_040(self) -> None:
        # CORRECTIONS block: relaxed from Rev-4's 0.20 SD per RC-CF-1
        # scipy verification under canonical Cohen f² formulation.
        assert cc.MDES_SD == 0.40, (
            "MDES_SD must equal 0.40 per Task 11.N.2c CORRECTIONS block "
            "(relaxed from Rev-4's 0.20 SD per RC-CF-1 BLOCKER scipy "
            "verification; 0.20 yielded power 0.320, 0.40 yields 0.888)."
        )

    def test_pc1_loading_floor_is_040(self) -> None:
        assert cc.PC1_LOADING_FLOOR == 0.40, (
            "PC1_LOADING_FLOOR must equal 0.40 (PCA non-trivial-loading "
            "convention; informational/diagnostic only post RC-CF-2)."
        )


class TestStep0PinnedFormulation:
    """``required_power`` source text is tamper-evident via SHA256."""

    def test_mdes_formulation_hash_matches_live_source(self) -> None:
        live_sha = hashlib.sha256(
            inspect.getsource(required_power).encode("utf-8")
        ).hexdigest()
        assert cc.MDES_FORMULATION_HASH == live_sha, (
            "MDES_FORMULATION_HASH must equal the SHA256 of the pinned "
            "required_power source text. Modification of the function "
            "(whitespace, docstring, df₁ value, α value, body lines) "
            "invalidates the hash and HALTs this test."
        )

    def test_required_power_at_anchor_returns_0888(self) -> None:
        # Live-scipy reproduced 2026-04-25: 0.887746... rounds to 0.888.
        # Per §0.3 MDES formulation pin block. ± 1e-3 tolerance.
        actual = required_power(80, 13, 0.40)
        assert math.isclose(actual, 0.888, abs_tol=1e-3), (
            f"required_power(80, 13, 0.40) under canonical Cohen f² "
            f"must equal 0.888 ± 1e-3; got {actual}. Drift indicates "
            f"either a scipy version regression or tampering with the "
            f"pinned formulation."
        )

    def test_required_power_at_anchor_exceeds_power_min(self) -> None:
        # The operative gate is `>= POWER_MIN`, not equality to a target.
        actual = required_power(80, 13, 0.40)
        assert actual >= cc.POWER_MIN, (
            f"required_power(80, 13, 0.40) = {actual} must be >= "
            f"POWER_MIN = {cc.POWER_MIN}; the panel is under-powered "
            f"under MDES_SD=0.40 if this assertion fails. Anti-fishing "
            f"guard: do NOT free-tune MDES_SD upward to recover power "
            f"— per design doc §1, the correct response is HALT under "
            f"CalibrationStructurallyPathological."
        )

    def test_required_power_at_rev4_anchor_is_underpowered(self) -> None:
        # Sanity check that RC-CF-1's narrative is reproduced: at
        # MDES_SD=0.20 the same panel is under-powered. This is the
        # provenance for the 0.40 relaxation.
        actual = required_power(80, 13, 0.20)
        assert actual < cc.POWER_MIN, (
            f"At MDES_SD=0.20 the panel is expected to be under-powered "
            f"(< {cc.POWER_MIN}); got {actual}. If this assertion fails, "
            f"the CORRECTIONS block's 0.20 → 0.40 relaxation rationale "
            f"is no longer reproducible — escalate before modifying "
            f"MDES_SD downward."
        )


# ─────────────────────────────────────────────────────────────────────
# Step 1 — ``compute_basket_calibration`` PASS branch + diagnostics
# ─────────────────────────────────────────────────────────────────────


def _synthetic_panel(
    n_weeks: int,
    n_nonzero_per_currency: dict[str, int],
    seed: int = 0,
    *,
    force_basket_nonzero_weeks: int | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    """Build a synthetic per-currency panel + basket-aggregate.

    Each currency column is filled with ``n_nonzero_per_currency[ccy]``
    non-zero values (in deterministic positions seeded by ``seed``) and
    zeros elsewhere. The basket-aggregate is the row-wise sum.

    The basket-aggregate non-zero count = number of weeks where ANY
    currency has a non-zero entry — used to drive the N_MIN gate.

    If ``force_basket_nonzero_weeks`` is given, the function ensures that
    the union of non-zero positions across all currencies covers exactly
    that many weeks (used to reliably reproduce the PASS branch under
    arbitrary per-currency sparsity).
    """
    rng = np.random.default_rng(seed)
    columns = ["copm", "usdm", "eurm", "brlm", "kesm", "xofm"]
    weeks = [date(2024, 9, 6) + timedelta(days=7 * i) for i in range(n_weeks)]
    matrix = np.zeros((n_weeks, len(columns)), dtype=float)

    if force_basket_nonzero_weeks is not None:
        # Pick ``force_basket_nonzero_weeks`` "active" rows; route each
        # currency's non-zero values into a subset of these so the
        # basket-aggregate is non-zero in exactly that many weeks.
        active_rows = rng.choice(
            n_weeks, size=force_basket_nonzero_weeks, replace=False
        )
        for j, ccy in enumerate(columns):
            n_nonzero = n_nonzero_per_currency.get(ccy, 0)
            if n_nonzero > 0:
                # Sample ``n_nonzero`` rows from the active set (with
                # replacement guard via min).
                k = min(n_nonzero, force_basket_nonzero_weeks)
                positions = rng.choice(active_rows, size=k, replace=False)
                values = rng.uniform(low=100.0, high=10000.0, size=k)
                matrix[positions, j] = values
    else:
        for j, ccy in enumerate(columns):
            n_nonzero = n_nonzero_per_currency.get(ccy, 0)
            if n_nonzero > 0:
                positions = rng.choice(n_weeks, size=n_nonzero, replace=False)
                values = rng.uniform(low=100.0, high=10000.0, size=n_nonzero)
                matrix[positions, j] = values

    panel = pd.DataFrame(matrix, columns=columns, index=pd.Index(weeks, name="week_start"))
    basket_aggregate = panel.sum(axis=1)
    basket_aggregate.name = "basket_aggregate_user_volume_usd"
    return panel, basket_aggregate


class TestStep1Pass:
    """PASS branch — basket-aggregate >= N_MIN non-zero weekly obs."""

    # Reusable spec: 82 panel weeks, 82 active union weeks, broad per-ccy
    # populations. ``force_basket_nonzero_weeks=82`` ensures basket-
    # aggregate is non-zero in all 82 weeks regardless of seed-driven
    # per-currency overlap.
    _PASS_KW = {
        "n_weeks": 82,
        "n_nonzero_per_currency": {
            "copm": 60,
            "usdm": 50,
            "eurm": 55,
            "brlm": 40,
            "kesm": 30,
            "xofm": 20,
        },
        "force_basket_nonzero_weeks": 82,
    }

    def test_returns_calibration_result(self) -> None:
        panel, basket = _synthetic_panel(seed=1, **self._PASS_KW)
        result = compute_basket_calibration(panel, basket)
        assert isinstance(result, CalibrationResult)

    def test_primary_choice_locked_to_basket_aggregate(self) -> None:
        panel, basket = _synthetic_panel(seed=2, **self._PASS_KW)
        result = compute_basket_calibration(panel, basket)
        assert result.primary_choice == "basket_aggregate", (
            "primary_choice must be locked to 'basket_aggregate' per "
            "CR-CF-1 + RC-CF-1 + RC-CF-2 collapse."
        )

    def test_decision_branch_is_pass(self) -> None:
        panel, basket = _synthetic_panel(seed=3, **self._PASS_KW)
        result = compute_basket_calibration(panel, basket)
        assert result.decision_branch == "PASS"

    def test_basket_n_nonzero_obs_matches_actual_count(self) -> None:
        # All 82 weeks have COPM non-zero ⇒ basket-aggregate non-zero
        # in all 82 weeks.
        panel, basket = _synthetic_panel(
            n_weeks=82,
            n_nonzero_per_currency={"copm": 82, "usdm": 0, "eurm": 0, "brlm": 0, "kesm": 0, "xofm": 0},
            seed=4,
        )
        result = compute_basket_calibration(panel, basket)
        assert result.basket_n_nonzero_obs == 82

    def test_per_currency_loadings_dict_populated(self) -> None:
        panel, basket = _synthetic_panel(seed=5, **self._PASS_KW)
        result = compute_basket_calibration(panel, basket)
        for ccy in ("copm", "usdm", "eurm", "brlm", "kesm", "xofm"):
            assert ccy in result.per_currency_pc1_loadings, (
                f"per_currency_pc1_loadings missing key '{ccy}'"
            )
            assert isinstance(result.per_currency_pc1_loadings[ccy], float)

    def test_basket_pc1_variance_explained_in_unit_interval(self) -> None:
        panel, basket = _synthetic_panel(seed=6, **self._PASS_KW)
        result = compute_basket_calibration(panel, basket)
        assert 0.0 <= result.basket_pc1_variance_explained <= 1.0

    def test_copm_pc1_loading_in_unit_interval_signed(self) -> None:
        panel, basket = _synthetic_panel(seed=7, **self._PASS_KW)
        result = compute_basket_calibration(panel, basket)
        # Eigenvectors are unit-norm; per-component loading magnitude
        # ≤ 1 by Cauchy-Schwarz.
        assert -1.0 <= result.copm_pc1_loading <= 1.0


class TestStep1IndependentReproduction:
    """Independent reproduction witness — second compute path matches sklearn."""

    def test_pc1_variance_explained_reproduces_to_1e6(self) -> None:
        panel, basket = _synthetic_panel(
            n_weeks=82,
            n_nonzero_per_currency={
                "copm": 60,
                "usdm": 50,
                "eurm": 55,
                "brlm": 40,
                "kesm": 30,
                "xofm": 20,
            },
            seed=42,
            force_basket_nonzero_weeks=82,
        )
        result = compute_basket_calibration(panel, basket)

        # Independent path: explicit numpy standardization + covariance
        # matrix eigendecomposition. PCA on standardized data is
        # equivalent to eigendecomp of the correlation matrix.
        matrix = panel.astype(float).to_numpy()
        means = matrix.mean(axis=0)
        stds = matrix.std(axis=0, ddof=0)
        safe_stds = np.where(stds > 0.0, stds, 1.0)
        standardized = (matrix - means) / safe_stds
        # Use SVD for numerical stability (matches sklearn internals).
        # Centered already by standardization (mean=0); divide by sqrt(n)
        # convention matches PCA(svd_solver) variance.
        n = standardized.shape[0]
        cov = (standardized.T @ standardized) / n
        eigenvalues = np.linalg.eigvalsh(cov)
        eigenvalues_sorted = np.sort(eigenvalues)[::-1]
        total_var = eigenvalues_sorted.sum()
        expected_pc1_var_explained = float(eigenvalues_sorted[0] / total_var)

        assert math.isclose(
            result.basket_pc1_variance_explained,
            expected_pc1_var_explained,
            abs_tol=1e-6,
        ), (
            f"PC1 variance-explained mismatch: sklearn returned "
            f"{result.basket_pc1_variance_explained}, eigendecomp "
            f"returned {expected_pc1_var_explained} (diff "
            f"{abs(result.basket_pc1_variance_explained - expected_pc1_var_explained):.3e})."
        )


# ─────────────────────────────────────────────────────────────────────
# Step 5 — HALT-on-pathological branch
# ─────────────────────────────────────────────────────────────────────


class TestStep5PathologicalHalt:
    """HALT branch — basket-aggregate < N_MIN non-zero weekly obs."""

    def test_raises_calibration_structurally_pathological(self) -> None:
        # Construct a panel where basket-aggregate is non-zero in only
        # 50 of 82 weeks (below N_MIN=80).
        weeks_n = 82
        # Each currency only ever fires on one shared subset of 50
        # weeks; basket-aggregate non-zero count = 50.
        rng = np.random.default_rng(123)
        columns = ["copm", "usdm", "eurm", "brlm", "kesm", "xofm"]
        weeks = [date(2024, 9, 6) + timedelta(days=7 * i) for i in range(weeks_n)]
        nonzero_positions = rng.choice(weeks_n, size=50, replace=False)
        matrix = np.zeros((weeks_n, len(columns)), dtype=float)
        for j in range(len(columns)):
            matrix[nonzero_positions, j] = rng.uniform(100.0, 10000.0, size=50)
        panel = pd.DataFrame(matrix, columns=columns, index=pd.Index(weeks))
        basket = panel.sum(axis=1)

        with pytest.raises(CalibrationStructurallyPathological) as excinfo:
            compute_basket_calibration(panel, basket)

        # Structured payload: basket_n_nonzero_obs, n_min, rationale.
        assert excinfo.value.basket_n_nonzero_obs == 50
        assert excinfo.value.n_min == cc.N_MIN
        assert "50" in excinfo.value.rationale or "{50}" in excinfo.value.rationale

    def test_halt_preserves_non_zero_count_invariant(self) -> None:
        # Edge: exactly N_MIN - 1 non-zero weeks ⇒ pathological.
        weeks_n = 82
        rng = np.random.default_rng(124)
        columns = ["copm", "usdm", "eurm", "brlm", "kesm", "xofm"]
        weeks = [date(2024, 9, 6) + timedelta(days=7 * i) for i in range(weeks_n)]
        n_nonzero = cc.N_MIN - 1
        positions = rng.choice(weeks_n, size=n_nonzero, replace=False)
        matrix = np.zeros((weeks_n, len(columns)), dtype=float)
        for j in range(len(columns)):
            matrix[positions, j] = rng.uniform(100.0, 10000.0, size=n_nonzero)
        panel = pd.DataFrame(matrix, columns=columns, index=pd.Index(weeks))
        basket = panel.sum(axis=1)

        with pytest.raises(CalibrationStructurallyPathological) as excinfo:
            compute_basket_calibration(panel, basket)
        assert excinfo.value.basket_n_nonzero_obs == cc.N_MIN - 1

    def test_n_min_boundary_passes(self) -> None:
        # Exactly N_MIN non-zero weeks ⇒ PASS (gate is `>= N_MIN`).
        weeks_n = 82
        rng = np.random.default_rng(125)
        columns = ["copm", "usdm", "eurm", "brlm", "kesm", "xofm"]
        weeks = [date(2024, 9, 6) + timedelta(days=7 * i) for i in range(weeks_n)]
        positions = rng.choice(weeks_n, size=cc.N_MIN, replace=False)
        matrix = np.zeros((weeks_n, len(columns)), dtype=float)
        for j in range(len(columns)):
            matrix[positions, j] = rng.uniform(100.0, 10000.0, size=cc.N_MIN)
        panel = pd.DataFrame(matrix, columns=columns, index=pd.Index(weeks))
        basket = panel.sum(axis=1)

        result = compute_basket_calibration(panel, basket)
        assert result.basket_n_nonzero_obs == cc.N_MIN
        assert result.decision_branch == "PASS"
