"""Carbon-basket calibration — Task 11.N.2c (Rev-5.3).

Plan reference: ``contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md``
§Task 11.N.2c lines 1024-1089 (incl. CORRECTIONS block + §0.3 MDES
formulation pin block + Anti-fishing guard).

Design doc (immutable): ``contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md``
§1, §2, §3.

Gate memo: ``contracts/.scratch/2026-04-25-carbon-basket-gate-decision-memo.md``.
Corrigendum: ``contracts/.scratch/2026-04-25-carbon-basket-gate-memo-corrigendum.md``.

-------------------------------------------------------------------------
WHAT THIS MODULE COMPUTES
-------------------------------------------------------------------------

Per Rev-5.3 v2 fix-pass (CR-CF-1 + RC-CF-1 + RC-CF-2): the basket-
aggregate ``carbon_basket_user_volume_usd`` series is the COMMITTED
PRIMARY X_d out of the gate. Methodology (I) primary-selection has been
retired (the per-country COPM share is empirically dead-branch at 44
weeks vs ``N_MIN = 75`` post-Rev-5.3.1, originally 80). This module therefore performs a PCA cross-
validation diagnostic ONLY — it does NOT branch primary selection.

Two terminal states only (per RC-CF-1 + RC-CF-2 collapse):

  PASS               — basket-aggregate has ≥ ``N_MIN`` weekly non-zero
                       observations. Returns
                       :class:`CalibrationResult` with locked
                       ``primary_choice = "basket_aggregate"`` and a full
                       diagnostic payload (per-currency PC1 loadings +
                       basket-aggregate variance-explained share).
  pathological-HALT  — basket-aggregate has fewer than ``N_MIN`` weekly
                       non-zero observations. Raises
                       :class:`CalibrationStructurallyPathological` with
                       a structured payload. The orchestrator catches and
                       writes a disposition memo at
                       ``contracts/.scratch/2026-04-24-carbon-xd-pathological-disposition.md``;
                       does NOT silently set arb-only as primary.

-------------------------------------------------------------------------
PRE-COMMITTED THRESHOLDS (per design doc §3 + Task 11.N.2c CORRECTIONS)
-------------------------------------------------------------------------

  N_MIN: Final[int] = 75
      Originally 80 (anchored to existing CPI Rev-4 panel filtered range;
      prior Banrep IBR / DFF weekly extraction yielded 78–84 obs in
      similar tasks per Task 11.M.6 commit ``fff2ca7a3``). Relaxed to 75
      per Rev-5.3.1 CORRECTIONS (user-approved 2026-04-25 path α) after
      11.N.2c found basket-aggregate=77 nonzero weeks. Power floor
      preserved: required_power(75,13,0.40)=0.864 ≥ POWER_MIN=0.80.

  POWER_MIN: Final[float] = 0.80
      Rev-4 standard target; achievable power 0.888 at MDES_SD = 0.40
      under the canonical Cohen f² formulation pinned in
      :func:`required_power`. ``≥ POWER_MIN`` is the operative gate, not
      equality to a target.

  MDES_SD: Final[float] = 0.40
      Phase-A.0 anchor; documented relaxation from Rev-4's 0.20 SD per
      RC-CF-1 BLOCKER scipy verification (n=80, k=13, df₁=6, α=0.10;
      MDES=0.20 SD yielded actual power 0.320 — far below 0.80; relaxed
      to 0.40 SD where the pinned Cohen f² formulation gives power 0.888
      — exceeds POWER_MIN). Smaller-panel exercise (n ≈ 84 weekly obs vs
      Rev-4's 947 obs) requires a larger detectable effect size.

  PC1_LOADING_FLOOR: Final[float] = 0.40
      PCA non-trivial-loading convention; informational/diagnostic only
      (per RC-CF-2 collapse, no longer a path-selection input).

  MDES_FORMULATION_HASH: Final[str]
      Tamper-evident anchor for the pinned :func:`required_power` source
      text per §0.3 MDES formulation pin block. SHA256 of the function
      source as committed at Step 0; modification of the function
      (whitespace, docstring, df₁ value, α value, body lines) invalidates
      the hash and HALTs the Step-0 test.

-------------------------------------------------------------------------
ANTI-FISHING GUARD
-------------------------------------------------------------------------

``MDES_SD``, ``MDES_FORMULATION_HASH``, and the source text of
:func:`required_power` are pre-committed in source. Modification after
Step 0 commits requires (a) full design-doc revision; (b) CORRECTIONS
block in the next plan revision; (c) full 3-way review cycle. Free-tuning
``MDES_SD`` upward to chase a target power figure is anti-fishing-banned
per X_d design doc §1.

-------------------------------------------------------------------------
PUBLIC API (pure free functions + one frozen dataclass + one exception)
-------------------------------------------------------------------------

* :class:`CalibrationResult` — frozen-dataclass result type.
* :class:`CalibrationStructurallyPathological` — exception raised on
  pathological-HALT branch (basket-aggregate < ``N_MIN``).
* :func:`required_power` — Cohen f² canonical statistical-power
  computation per §0.3 MDES formulation pin block. Tamper-evident via
  ``MDES_FORMULATION_HASH``.
* :func:`compute_basket_calibration` — PCA cross-validation diagnostic;
  returns :class:`CalibrationResult` on PASS or raises
  :class:`CalibrationStructurallyPathological` on HALT.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, Literal

if TYPE_CHECKING:
    import pandas as pd

# ── Pre-committed thresholds (per design doc §3 + Task 11.N.2c CORRECTIONS) ──

N_MIN: Final[int] = 75
"""Weekly non-zero observation floor for basket-aggregate primary X_d.

Originally 80 (anchored to existing CPI Rev-4 panel filtered range
78–84 obs in similar tasks per Task 11.M.6 commit ``fff2ca7a3``).
**Relaxed to 75 per Rev-5.3.1 CORRECTIONS block** (user-approved
2026-04-25, path α from the pathological-HALT disposition memo) after
Task 11.N.2c initial calibration found basket-aggregate = 77 nonzero
weeks — 3 short of the original 80 floor. The relaxation preserves
POWER_MIN: ``required_power(75, 13, 0.40) = 0.8638`` (scipy-verified)
≥ POWER_MIN=0.80; ``required_power(77, 13, 0.40) = 0.8739``;
``required_power(80, 13, 0.40) = 0.8877`` (original anchor). MDES_SD
remains 0.40 unchanged. Below this floor, the pathological-HALT
branch fires per design doc §4 row 4.
"""

POWER_MIN: Final[float] = 0.80
"""Rev-4 standard target statistical-power floor.

Achievable power at MDES_SD = 0.40 under the pinned Cohen f²
formulation is 0.888 — exceeds POWER_MIN. ``>= POWER_MIN`` is the
operative gate (not equality to a target).
"""

MDES_SD: Final[float] = 0.40
"""Phase-A.0 minimum detectable effect size (in SD units).

Documented relaxation from Rev-4's 0.20 SD per RC-CF-1 BLOCKER scipy
verification: at n=80, k=13, df₁=6, α=0.10 the pinned Cohen f²
formulation gives power 0.320 at MDES=0.20 (far below 0.80) and power
0.888 at MDES=0.40 (exceeds POWER_MIN). Smaller-panel exercise (n ≈ 84
weekly obs vs Rev-4's 947 obs) requires a larger detectable effect size.
"""

PC1_LOADING_FLOOR: Final[float] = 0.40
"""PCA non-trivial-loading convention.

Informational/diagnostic only (per RC-CF-2 collapse, no longer a
path-selection input).
"""

# ── Statistical-power function (pinned source — tamper-evident) ─────────────


def required_power(
    n_obs: int,
    k_regressors: int,
    mdes_sd: float,
    alpha: float = 0.10,
    df1: int = 6,
) -> float:
    """Cohen f² canonical statistical-power computation.

    Per Cohen 1988 (*Statistical Power Analysis for the Behavioral
    Sciences*, 2nd ed., chapter 9). Computes the achievable power for a
    one-sided F-test against the primary block of macro regressors.

    f² = mdes_sd² / (1 − mdes_sd²)
    λ  = n_obs × f²
    crit = scipy.stats.f.ppf(1 − alpha, df1, n_obs − k_regressors)
    power = 1 − scipy.stats.ncf.cdf(crit, df1, n_obs − k_regressors, λ)
    """
    from scipy.stats import f, ncf  # type: ignore[import-untyped]

    f2 = mdes_sd * mdes_sd / (1.0 - mdes_sd * mdes_sd)
    lam = n_obs * f2
    df2 = n_obs - k_regressors
    crit = f.ppf(1.0 - alpha, df1, df2)
    return float(1.0 - ncf.cdf(crit, df1, df2, lam))


# ── Tamper-evident SHA256 of the pinned ``required_power`` source ───────────
#
# Computed as ``hashlib.sha256(inspect.getsource(required_power).encode("utf-8")).hexdigest()``
# at Step 0 commit time. The Step-0 failing test recomputes this and asserts
# byte-exact match. Any whitespace / docstring / signature drift in
# :func:`required_power` invalidates the hash and HALTs the test.

MDES_FORMULATION_HASH: Final[str] = (
    "4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa"
)


# ── Result types ────────────────────────────────────────────────────────────


class CalibrationStructurallyPathological(RuntimeError):
    """Raised when basket-aggregate has < ``N_MIN`` weekly non-zero obs.

    Per design doc §4 row 4, this is the structurally-pathological
    branch: do NOT silently set arb-only as primary (would conflate
    stress-detection with capital-flow magnitude). Orchestrator catches
    and writes a disposition memo; user decides next-step pivot.
    """

    def __init__(
        self,
        *,
        basket_n_nonzero_obs: int,
        n_min: int,
        rationale: str,
    ) -> None:
        self.basket_n_nonzero_obs = basket_n_nonzero_obs
        self.n_min = n_min
        self.rationale = rationale
        super().__init__(
            f"Carbon-basket aggregate has {basket_n_nonzero_obs} weekly non-zero "
            f"observations; required minimum is {n_min}. {rationale}"
        )


@dataclass(frozen=True, slots=True)
class CalibrationResult:
    """PCA cross-validation diagnostic result (PASS branch only).

    Per design doc §2 contract (REVISED for Rev-5.3 v2 fix-pass two-state
    collapse). The ``primary_choice`` Literal admits ONE value
    (``"basket_aggregate"``) — pathological branch raises
    :class:`CalibrationStructurallyPathological` instead of returning.

    Fields
    ------
    primary_choice
        Locked to ``"basket_aggregate"`` per CR-CF-1 + RC-CF-1 + RC-CF-2.
    copm_n_nonzero_obs
        Diagnostic: count of weekly non-zero observations for the COPM
        per-currency series (informational; NOT a path-selection input
        post-collapse).
    copm_pc1_loading
        Diagnostic: COPM's loading on PC1 (signed, in [-1, 1]).
    basket_pc1_variance_explained
        Diagnostic: PC1's variance-explained share over the standardized
        per-currency matrix (in [0, 1]).
    decision_branch
        ``"PASS"`` (the only Literal admitted on a returned result;
        ``"pathological_HALT"`` is reserved for the exception payload
        but not present on a returned dataclass instance).
    rationale
        Free-form English explanation (e.g., "basket-aggregate has 77
        weekly non-zero obs ≥ N_MIN=75 (relaxed Rev-5.3.1 from 80); primary X_d locked to
        carbon_basket_user_volume_usd").
    per_currency_pc1_loadings
        Full 6-element diagnostic dict mapping mento symbol → PC1
        loading for downstream consumption.
    basket_n_nonzero_obs
        Count of weekly non-zero observations for the basket-aggregate
        series.
    """

    primary_choice: Literal["basket_aggregate"]
    copm_n_nonzero_obs: int
    copm_pc1_loading: float
    basket_pc1_variance_explained: float
    decision_branch: Literal["PASS"]
    rationale: str
    basket_n_nonzero_obs: int
    per_currency_pc1_loadings: dict[str, float] = field(default_factory=dict)


# ── Calibration entry point ─────────────────────────────────────────────────


def compute_basket_calibration(
    per_currency_panel: "pd.DataFrame",
    basket_aggregate: "pd.Series",
    *,
    n_min: int = N_MIN,
    pc1_loading_floor: float = PC1_LOADING_FLOOR,
) -> CalibrationResult:
    """Run PCA cross-validation diagnostic on the per-currency panel.

    Per design doc §2 contract (post-RC-CF-2 collapse). The function
    does NOT branch primary selection — the basket-aggregate is the
    committed primary per CR-CF-1 + RC-CF-1 + RC-CF-2.

    Parameters
    ----------
    per_currency_panel
        Six-column ``pandas.DataFrame`` indexed by Friday-anchored
        ``week_start`` (date), with one column per Mento stablecoin
        (``copm``, ``usdm``, ``eurm``, ``brlm``, ``kesm``, ``xofm``).
        Values are weekly USD volumes for the user-only partition.
    basket_aggregate
        ``pandas.Series`` indexed identically to ``per_currency_panel``;
        carries the basket-aggregate user-only volume (this is the
        committed primary X_d).
    n_min
        Minimum weekly non-zero observation count for the
        basket-aggregate to PASS the gate. Defaults to module-level
        :data:`N_MIN`.
    pc1_loading_floor
        Diagnostic floor for "non-trivial" PC1 loading (informational
        only post-RC-CF-2 collapse). Defaults to module-level
        :data:`PC1_LOADING_FLOOR`.

    Returns
    -------
    CalibrationResult
        With ``decision_branch = "PASS"`` and full diagnostic payload.

    Raises
    ------
    CalibrationStructurallyPathological
        If basket-aggregate has fewer than ``n_min`` weekly non-zero
        observations (design doc §4 row 4 pathological branch).
    """
    import numpy as np
    from sklearn.decomposition import PCA  # type: ignore[import-untyped]

    # ── Step (a): basket-aggregate N_MIN gate ────────────────────────────
    basket_nonzero = int((basket_aggregate.astype(float) > 0.0).sum())
    if basket_nonzero < n_min:
        raise CalibrationStructurallyPathological(
            basket_n_nonzero_obs=basket_nonzero,
            n_min=n_min,
            rationale=(
                f"Basket-aggregate carbon_basket_user_volume_usd has "
                f"{basket_nonzero} weekly non-zero observations across the "
                f"available panel; required minimum is {n_min}. The "
                f"Carbon-basket X_d thesis is empirically failing at the "
                f"basket-wide level — escalate to user. Do NOT silently "
                f"set arb-only as primary (would conflate stress-detection "
                f"with capital-flow magnitude). See design doc §4 row 4."
            ),
        )

    # ── Step (b): standardize per-currency matrix ────────────────────────
    matrix = per_currency_panel.astype(float).to_numpy()
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0, ddof=0)
    # Guard against zero-variance columns (e.g., XOFm with zero user
    # activity); replace zero std with 1 to avoid division by zero — the
    # standardized column will be all zeros and contribute nothing to the
    # principal component.
    safe_stds = np.where(stds > 0.0, stds, 1.0)
    standardized = (matrix - means) / safe_stds

    # ── Step (c): PCA via sklearn (full component decomposition) ─────────
    n_currencies = standardized.shape[1]
    pca = PCA(n_components=n_currencies)
    pca.fit(standardized)
    pc1_loadings = pca.components_[0]
    pc1_variance_explained = float(pca.explained_variance_ratio_[0])

    # ── Step (d): per-currency loadings dict ─────────────────────────────
    columns = list(per_currency_panel.columns)
    per_currency_pc1: dict[str, float] = {
        str(col): float(load) for col, load in zip(columns, pc1_loadings)
    }

    # COPM is the Colombia-pilot anchor; pull its loading explicitly.
    copm_key: str | None = None
    for candidate in ("copm", "COPM"):
        if candidate in per_currency_pc1:
            copm_key = candidate
            break
    copm_loading = per_currency_pc1[copm_key] if copm_key is not None else 0.0
    copm_series = (
        per_currency_panel[copm_key].astype(float)
        if copm_key is not None
        else None
    )
    copm_nonzero = int((copm_series > 0.0).sum()) if copm_series is not None else 0

    # ── Step (e): rationale string ───────────────────────────────────────
    nontrivial_loading = abs(copm_loading) >= pc1_loading_floor
    rationale = (
        f"Basket-aggregate carbon_basket_user_volume_usd has "
        f"{basket_nonzero} weekly non-zero observations >= N_MIN={n_min}; "
        f"primary X_d locked to carbon_basket_user_volume_usd per "
        f"CR-CF-1 + RC-CF-1 + RC-CF-2. PC1 explains "
        f"{pc1_variance_explained:.4f} of the standardized per-currency "
        f"variance; COPM loading on PC1 = {copm_loading:.4f} "
        f"({'non-trivial' if nontrivial_loading else 'idiosyncratic'} "
        f"per |loading| >= {pc1_loading_floor} convention)."
    )

    return CalibrationResult(
        primary_choice="basket_aggregate",
        copm_n_nonzero_obs=copm_nonzero,
        copm_pc1_loading=float(copm_loading),
        basket_pc1_variance_explained=pc1_variance_explained,
        decision_branch="PASS",
        rationale=rationale,
        basket_n_nonzero_obs=basket_nonzero,
        per_currency_pc1_loadings=per_currency_pc1,
    )
