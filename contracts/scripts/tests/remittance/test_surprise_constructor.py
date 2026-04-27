"""TDD tests for the Task-10 AR(1) surprise constructor module.

Phase-A.0 Task 10 of the remittance-surprise implementation plan. These tests
are written BEFORE implementation per ``feedback_strict_tdd`` and MUST fail on
ImportError until ``contracts/scripts/surprise_constructor.py`` is authored.

Scope (pure module; no I/O, no DB, no network):
  * ``SurpriseSeries`` — frozen dataclass (``slots=True``) carrying monthly
    residuals, weekly LOCF-interpolated residuals, AR(1) parameters, vintage
    policy token, and source-fingerprint hex.
  * ``construct_ar1_surprise(series, pre_sample_end_date, vintage_policy)``
    — the primary entry point; fits AR(1) on ``ΔlogRem_m`` under the chosen
    vintage discipline, returns the full ``SurpriseSeries`` payload.
  * ``_locf_weekly_align(monthly_surprise_df, weekly_index)`` — the private
    LOCF helper; pins Rev-1 spec §4.6 semantics (last release on or before
    the Friday-close, ties broken by earlier reference-period).
  * ``_compute_source_fingerprint(series)`` — deterministic SHA-256 over
    sorted ``(reference_period, release_date, value)`` tuples; used for
    decision-hash extension + reproducibility auditing.

Rev-1 spec authoritative reference:
  * §4.6 LOCF protocol (anchored on BanRep release dates; tie → earlier
    reference-period).
  * §4.7 AR order = AR(1) primary (SARIMA sensitivity deferred).
  * §4.8 Vintage discipline = real-time (first-printed) primary;
    current-vintage sensitivity.
  * §12 row 6 (LOCF side + tie rule), row 7 (AR(1) + pre-sample-end).

The golden fixture at ``fixtures/golden_banrep_monthly.csv`` is hand-authored
synthetic data documented as test-fixture in its own header comment. Real
BanRep-derived data arrives in Task 11 at ``contracts/data/``.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import pytest

# These imports MUST fail until Task 10 is implemented — that is the red
# phase of red-green-refactor per ``feedback_strict_tdd``.
from scripts.surprise_constructor import (  # noqa: E402  (TDD red-phase import)
    SurpriseSeries,
    construct_ar1_surprise,
    _compute_source_fingerprint,
    _locf_weekly_align,
)


# ── Fixture constants ────────────────────────────────────────────────────────

_FIXTURE_DIR: Final[Path] = Path(__file__).resolve().parent / "fixtures"
_GOLDEN_CSV: Final[Path] = _FIXTURE_DIR / "golden_banrep_monthly.csv"

# Values pinned from an independent reproduction of the AR(1) fit on the
# golden fixture under real-time vintage. The reproduction code lives in
# ``test_golden_fixture_matches_independent_fit`` below so a reviewer can
# regenerate these values from the committed CSV bytes alone (no round-trip
# through ``construct_ar1_surprise``).
_EXPECTED_PHI_REAL_TIME: Final[float] = 0.834729  # to 6 decimals
_EXPECTED_MU_REAL_TIME: Final[float] = 0.001089  # to 6 decimals
# Current-vintage (revised) fit yields different parameters — pinned to guard
# against silent vintage-policy regression.
_EXPECTED_PHI_CURRENT_VINTAGE: Final[float] = 0.816151  # to 6 decimals
_EXPECTED_MU_CURRENT_VINTAGE: Final[float] = 0.001240  # to 6 decimals

# Source fingerprint pinned over the ENTIRE fixture (both vintages); this is
# a deterministic hash of all 27 rows sorted by (reference_period,
# release_date, value). If the CSV bytes change, the fingerprint flips.
_EXPECTED_SOURCE_FINGERPRINT_HEX: Final[str] = (
    "429c61946d718c850775231fda221f35583671da672901f150dfa465014869e3"
)

# Number of Fridays in the fixture horizon [first_release_date=2006-03-17,
# last_reference_period=2008-01-31]. Used to pin the weekly-series length.
_EXPECTED_FRIDAY_COUNT: Final[int] = 98


# ── Helpers (test-local) ─────────────────────────────────────────────────────


def _load_golden_fixture() -> pd.DataFrame:
    """Load the hand-authored golden fixture as a typed DataFrame.

    Strips commented lines, coerces ``reference_period`` and ``release_date``
    to ``datetime.date``, and ``value`` to float. Tests never depend on this
    helper for pinned-value assertions — those reproduce the loading inline
    to keep the golden values auditable.
    """
    df = pd.read_csv(_GOLDEN_CSV, comment="#")
    df["reference_period"] = pd.to_datetime(df["reference_period"]).dt.date
    df["release_date"] = pd.to_datetime(df["release_date"]).dt.date
    df["value"] = df["value"].astype(float)
    return df


def _weekly_friday_index(start: date, end: date) -> pd.DatetimeIndex:
    """Return the Friday-close index for the closed interval ``[start, end]``."""
    return pd.date_range(start=start, end=end, freq="W-FRI")


# ── 1. SurpriseSeries dataclass shape ───────────────────────────────────────


def test_surprise_series_is_frozen_slots_dataclass() -> None:
    """``SurpriseSeries`` is a frozen dataclass with ``slots=True``."""
    assert dataclasses.is_dataclass(SurpriseSeries), (
        "SurpriseSeries must be a @dataclass"
    )
    # Frozen: mutation must raise FrozenInstanceError. We construct a minimal
    # instance by calling the real constructor on the golden fixture.
    series = _load_golden_fixture()
    result = construct_ar1_surprise(
        series=series,
        pre_sample_end_date=date(2007, 2, 1),
        vintage_policy="real-time",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.vintage_policy = "current-vintage"  # type: ignore[misc]
    # Slots: no __dict__ on instance.
    assert not hasattr(result, "__dict__"), (
        "SurpriseSeries must be declared with slots=True (no instance __dict__)"
    )


def test_surprise_series_has_expected_fields() -> None:
    """``SurpriseSeries`` declares the five Task-10 surface fields."""
    field_names = {f.name for f in dataclasses.fields(SurpriseSeries)}
    expected = {
        "monthly_residuals",
        "weekly_interpolated",
        "ar_params",
        "vintage_policy",
        "source_fingerprint",
    }
    assert field_names == expected, (
        f"SurpriseSeries must declare exactly {sorted(expected)}; "
        f"got {sorted(field_names)}"
    )


# ── 2. construct_ar1_surprise — input validation ─────────────────────────────


def test_construct_raises_on_missing_columns() -> None:
    """``construct_ar1_surprise`` raises ValueError when required columns are absent."""
    bad = pd.DataFrame({"reference_period": [date(2006, 1, 31)], "value": [1000.0]})
    # Missing `release_date`.
    with pytest.raises(ValueError, match="release_date"):
        construct_ar1_surprise(
            series=bad,
            pre_sample_end_date=date(2007, 2, 1),
            vintage_policy="real-time",
        )


def test_construct_raises_on_non_monotone_reference_period() -> None:
    """Non-monotone ``reference_period`` raises ValueError.

    The spec §4.6 LOCF protocol assumes a sorted series; a silently
    out-of-order input would produce a subtly wrong fit. Validate at the
    boundary (first line) per functional-python's input-validation rule.
    """
    rows = [
        {"reference_period": date(2006, 1, 31), "release_date": date(2006, 3, 17), "value": 1000.0},
        {"reference_period": date(2006, 3, 31), "release_date": date(2006, 5, 15), "value": 1063.3},
        {"reference_period": date(2006, 2, 28), "release_date": date(2006, 4, 14), "value": 1035.0},  # out of order
    ]
    bad = pd.DataFrame(rows)
    with pytest.raises(ValueError, match="monotone|sorted|reference_period"):
        construct_ar1_surprise(
            series=bad,
            pre_sample_end_date=date(2007, 2, 1),
            vintage_policy="real-time",
        )


def test_construct_raises_on_invalid_vintage_policy() -> None:
    """``vintage_policy`` outside the allowed set raises ValueError."""
    df = _load_golden_fixture()
    with pytest.raises(ValueError, match="vintage_policy"):
        construct_ar1_surprise(
            series=df,
            pre_sample_end_date=date(2007, 2, 1),
            vintage_policy="backwards",  # type: ignore[arg-type]
        )


def test_construct_raises_on_pre_sample_end_after_all_observations() -> None:
    """``pre_sample_end_date`` past the last release_date raises ValueError."""
    df = _load_golden_fixture()
    with pytest.raises(ValueError, match="pre_sample_end_date"):
        construct_ar1_surprise(
            series=df,
            pre_sample_end_date=date(2099, 1, 1),
            vintage_policy="real-time",
        )


def test_construct_raises_on_insufficient_pre_sample() -> None:
    """Fewer than 12 pre-sample monthly obs raises ValueError.

    The Rev-1 spec §12 row 7 pins `pre_sample_end_date = 2008-01-01`; the
    AR(1) fit needs enough pre-sample depth to avoid overfitting on a short
    history. Twelve months is the minimum documented pre-sample depth.
    """
    # Five monthly obs — well under the 12-month floor.
    short_rows = [
        {"reference_period": date(2006, 1, 31), "release_date": date(2006, 3, 17), "value": 1000.0},
        {"reference_period": date(2006, 2, 28), "release_date": date(2006, 4, 14), "value": 1035.0},
        {"reference_period": date(2006, 3, 31), "release_date": date(2006, 5, 15), "value": 1063.3},
        {"reference_period": date(2006, 4, 30), "release_date": date(2006, 6, 14), "value": 1080.0},
        {"reference_period": date(2006, 5, 31), "release_date": date(2006, 7, 15), "value": 1083.3},
    ]
    short = pd.DataFrame(short_rows)
    with pytest.raises(ValueError, match="12|pre.?sample"):
        construct_ar1_surprise(
            series=short,
            pre_sample_end_date=date(2006, 12, 1),
            vintage_policy="real-time",
        )


# ── 3. AR(1) fit — pinned coefficients on golden fixture ─────────────────────


def test_construct_golden_ar1_phi_real_time() -> None:
    """``ar_params.phi`` on the real-time golden fixture matches the pinned value.

    Pinned to 6 decimals against an independent ``np.linalg.lstsq`` fit of
    `dlog_t = mu + phi * dlog_{t-1} + eps_t` on the first-printed vintage
    (25 unique reference-periods → 24 log-diffs → 23 residuals).
    """
    df = _load_golden_fixture()
    result = construct_ar1_surprise(
        series=df,
        pre_sample_end_date=date(2007, 2, 1),
        vintage_policy="real-time",
    )
    assert result.ar_params.phi == pytest.approx(_EXPECTED_PHI_REAL_TIME, abs=1e-6), (
        f"real-time AR(1) phi drift: expected {_EXPECTED_PHI_REAL_TIME:.6f}, "
        f"got {result.ar_params.phi:.6f}"
    )


def test_construct_golden_ar1_mu_real_time() -> None:
    """``ar_params.mu`` on the real-time golden fixture matches the pinned value."""
    df = _load_golden_fixture()
    result = construct_ar1_surprise(
        series=df,
        pre_sample_end_date=date(2007, 2, 1),
        vintage_policy="real-time",
    )
    assert result.ar_params.mu == pytest.approx(_EXPECTED_MU_REAL_TIME, abs=1e-6), (
        f"real-time AR(1) mu drift: expected {_EXPECTED_MU_REAL_TIME:.6f}, "
        f"got {result.ar_params.mu:.6f}"
    )


def test_construct_golden_ar1_sigma2_positive() -> None:
    """``ar_params.sigma2`` (residual variance) is strictly positive."""
    df = _load_golden_fixture()
    result = construct_ar1_surprise(
        series=df,
        pre_sample_end_date=date(2007, 2, 1),
        vintage_policy="real-time",
    )
    assert result.ar_params.sigma2 > 0.0, (
        f"residual variance must be strictly positive; got {result.ar_params.sigma2}"
    )


# ── 4. Residual sanity: signs + mean-zero ────────────────────────────────────


def test_construct_residuals_have_mixed_signs_and_mean_zero() -> None:
    """Golden-fixture residuals include positive and negative surprises and
    sum to ≈0 (tolerance 1e-10).

    An OLS fit with intercept forces the residual mean to vanish by
    construction (normal-equations orthogonality with the 1-vector). This
    test guards against a silent regression where the intercept gets
    dropped from the design matrix.
    """
    df = _load_golden_fixture()
    result = construct_ar1_surprise(
        series=df,
        pre_sample_end_date=date(2007, 2, 1),
        vintage_policy="real-time",
    )
    residuals = result.monthly_residuals.dropna().values
    assert any(r > 0 for r in residuals), (
        "golden fixture should exhibit at least one positive surprise"
    )
    assert any(r < 0 for r in residuals), (
        "golden fixture should exhibit at least one negative surprise"
    )
    assert abs(float(np.mean(residuals))) < 1e-10, (
        f"residuals must sum to ~0 under OLS-with-intercept fit; "
        f"got mean = {np.mean(residuals):.2e}"
    )


# ── 5. Weekly interpolation length + endpoints ───────────────────────────────


def test_construct_weekly_interpolated_length_matches_friday_count() -> None:
    """``weekly_interpolated`` length equals the Friday count over the horizon.

    The horizon is ``[first_release_date, last_reference_period]`` on the
    real-time vintage. Per Rev-1 spec §4.6 the series is step-held via LOCF
    anchored on release dates; the index itself is the set of Fridays in
    that closed interval.
    """
    df = _load_golden_fixture()
    result = construct_ar1_surprise(
        series=df,
        pre_sample_end_date=date(2007, 2, 1),
        vintage_policy="real-time",
    )
    assert len(result.weekly_interpolated) == _EXPECTED_FRIDAY_COUNT, (
        f"weekly_interpolated length mismatch: expected {_EXPECTED_FRIDAY_COUNT} "
        f"Fridays, got {len(result.weekly_interpolated)}"
    )
    # Index is Fridays only (isoweekday=5).
    idx = pd.DatetimeIndex(result.weekly_interpolated.index)
    iso_days = set(idx.isocalendar().day.tolist())
    assert iso_days == {5}, (
        f"weekly_interpolated index must be Fridays only; got iso-days {sorted(iso_days)}"
    )


# ── 6. LOCF ties → earlier reference-period wins ─────────────────────────────


def test_locf_weekly_align_tie_breaks_to_earlier_reference_period() -> None:
    """When two releases land on the same Friday, the earlier ref-period wins.

    Rev-1 spec §12 row 6 pins this tie-breaker unambiguously. Without it, the
    LOCF output is ambiguous on the tie date, and downstream consumers would
    silently see either value depending on sort stability.
    """
    friday = date(2010, 6, 4)  # a Friday
    tied = pd.DataFrame(
        [
            {
                "reference_period": date(2010, 3, 31),  # EARLIER ref-period
                "release_date": friday,
                "surprise": -0.005,
            },
            {
                "reference_period": date(2010, 4, 30),  # LATER ref-period
                "release_date": friday,
                "surprise": +0.012,
            },
        ]
    )
    weekly_idx = pd.DatetimeIndex([friday])
    aligned = _locf_weekly_align(tied, weekly_idx)
    # Earlier reference-period value (−0.005) must win.
    assert aligned.loc[pd.Timestamp(friday)] == pytest.approx(-0.005), (
        f"LOCF tie-break must prefer earlier reference-period "
        f"(expected -0.005 from 2010-03-31); got {aligned.loc[pd.Timestamp(friday)]}"
    )


def test_locf_weekly_align_uses_most_recent_release_on_or_before_friday() -> None:
    """LOCF picks max(release_date) subject to release_date ≤ Friday.

    Also asserts releases AFTER the Friday cutoff do NOT leak into week w.
    """
    monthly = pd.DataFrame(
        [
            {"reference_period": date(2010, 1, 31), "release_date": date(2010, 3, 15), "surprise": 0.01},
            {"reference_period": date(2010, 2, 28), "release_date": date(2010, 4, 15), "surprise": 0.02},
            {"reference_period": date(2010, 3, 31), "release_date": date(2010, 5, 15), "surprise": 0.03},
        ]
    )
    # Week ending 2010-04-02 (Friday): only the 2010-03-15 release is on-or-before.
    # Week ending 2010-04-16 (Friday): the 2010-04-15 release is now on-or-before (0.02 wins).
    weekly_idx = pd.DatetimeIndex([date(2010, 4, 2), date(2010, 4, 16), date(2010, 5, 21)])
    aligned = _locf_weekly_align(monthly, weekly_idx)
    assert aligned.iloc[0] == pytest.approx(0.01), "week 2010-04-02 should use 2010-03-15 release"
    assert aligned.iloc[1] == pytest.approx(0.02), "week 2010-04-16 should use 2010-04-15 release"
    assert aligned.iloc[2] == pytest.approx(0.03), "week 2010-05-21 should use 2010-05-15 release"


# ── 7. Vintage policy — real-time vs current-vintage ─────────────────────────


def test_construct_real_time_uses_first_printed_value() -> None:
    """Under ``vintage_policy = "real-time"``, only first-printed values
    enter the AR(1) fit.

    The golden fixture has two reference-periods (2006-04-30, 2006-10-31)
    with both first-printed AND revised values. Under real-time, the
    earlier release_date per reference-period wins, so the fit reproduces
    the pinned phi/mu above (which were computed on first-printed values).
    """
    df = _load_golden_fixture()
    result = construct_ar1_surprise(
        series=df,
        pre_sample_end_date=date(2007, 2, 1),
        vintage_policy="real-time",
    )
    # Real-time fit must match the first-printed pinned value, NOT the
    # current-vintage pinned value.
    assert result.ar_params.phi == pytest.approx(_EXPECTED_PHI_REAL_TIME, abs=1e-6)
    # Disambiguate from current-vintage (a silent policy bug would otherwise
    # land on the current-vintage phi).
    assert result.ar_params.phi != pytest.approx(_EXPECTED_PHI_CURRENT_VINTAGE, abs=1e-4), (
        "real-time fit must NOT equal current-vintage fit; silent vintage regression"
    )


def test_construct_current_vintage_uses_latest_revised_value() -> None:
    """Under ``vintage_policy = "current-vintage"``, the latest-revision
    value per reference-period enters the AR(1) fit."""
    df = _load_golden_fixture()
    result = construct_ar1_surprise(
        series=df,
        pre_sample_end_date=date(2007, 2, 1),
        vintage_policy="current-vintage",
    )
    assert result.ar_params.phi == pytest.approx(_EXPECTED_PHI_CURRENT_VINTAGE, abs=1e-6), (
        f"current-vintage phi drift: expected {_EXPECTED_PHI_CURRENT_VINTAGE:.6f}, "
        f"got {result.ar_params.phi:.6f}"
    )
    assert result.ar_params.mu == pytest.approx(_EXPECTED_MU_CURRENT_VINTAGE, abs=1e-6)


# ── 8. Source fingerprint — determinism, order-invariance, pinned hex ────────


def test_source_fingerprint_is_deterministic() -> None:
    """Same input → same fingerprint on repeated calls."""
    df = _load_golden_fixture()
    fp1 = _compute_source_fingerprint(df)
    fp2 = _compute_source_fingerprint(df)
    assert fp1 == fp2, f"source fingerprint must be deterministic; got {fp1!r} vs {fp2!r}"


def test_source_fingerprint_is_order_invariant() -> None:
    """Same tuples in different row order → same fingerprint.

    The helper must sort internally so row-order perturbations (which are
    semantically irrelevant) do not change the fingerprint. Without this,
    a harmless DataFrame reordering would spuriously invalidate a pinned
    decision-hash downstream.
    """
    df = _load_golden_fixture()
    fp_normal = _compute_source_fingerprint(df)
    # Reverse rows.
    df_reversed = df.iloc[::-1].reset_index(drop=True)
    fp_reversed = _compute_source_fingerprint(df_reversed)
    assert fp_normal == fp_reversed, (
        f"source fingerprint must be order-invariant; normal={fp_normal}, "
        f"reversed={fp_reversed}"
    )


def test_source_fingerprint_matches_pinned_hex_on_golden() -> None:
    """Fingerprint on the golden fixture matches the pinned hex.

    Pinning the hex ties the fingerprint function to its reference
    implementation (UTF-8 canonical-JSON SHA-256 over sorted ISO-date +
    float-value tuples); any divergence in canonicalization flips this.
    """
    df = _load_golden_fixture()
    actual = _compute_source_fingerprint(df)
    assert actual == _EXPECTED_SOURCE_FINGERPRINT_HEX, (
        f"source fingerprint drift: expected {_EXPECTED_SOURCE_FINGERPRINT_HEX}, "
        f"got {actual}"
    )


def test_surprise_series_source_fingerprint_matches_helper() -> None:
    """``SurpriseSeries.source_fingerprint`` equals ``_compute_source_fingerprint``
    on the same input series.

    This is the "the top-level payload fingerprint is the helper fingerprint"
    invariant; protects against an accidental alternate-hash code path.
    """
    df = _load_golden_fixture()
    result = construct_ar1_surprise(
        series=df,
        pre_sample_end_date=date(2007, 2, 1),
        vintage_policy="real-time",
    )
    helper_fp = _compute_source_fingerprint(df)
    assert result.source_fingerprint == helper_fp, (
        f"SurpriseSeries.source_fingerprint must equal the helper's output; "
        f"series={result.source_fingerprint!r}, helper={helper_fp!r}"
    )


# ── 9. Independent-fit reproducibility witness ───────────────────────────────


def test_golden_fixture_matches_independent_fit() -> None:
    """Verify the pinned phi/mu can be reproduced from the committed CSV bytes.

    This test does NOT exercise ``construct_ar1_surprise``; it reproduces the
    fit using ``np.linalg.lstsq`` directly on the fixture so a reviewer can
    confirm the pinned values are correct without trusting the implementation.
    If the CSV bytes change, the pinned constants must be regenerated from
    this independent code path.
    """
    df = _load_golden_fixture()
    # Real-time: first-printed value per reference_period.
    rt = (
        df.sort_values(["reference_period", "release_date"])
        .groupby("reference_period", as_index=False)
        .first()
    )
    log_rem = np.log(rt["value"].values.astype(float))
    dlog = np.diff(log_rem)
    y = dlog[1:]
    y_lag = dlog[:-1]
    design = np.column_stack([np.ones_like(y_lag), y_lag])
    coeffs, *_ = np.linalg.lstsq(design, y, rcond=None)
    mu_indep, phi_indep = float(coeffs[0]), float(coeffs[1])
    assert phi_indep == pytest.approx(_EXPECTED_PHI_REAL_TIME, abs=1e-6)
    assert mu_indep == pytest.approx(_EXPECTED_MU_REAL_TIME, abs=1e-6)

    # Also verify the pinned fingerprint against an inline reference impl.
    tuples_sorted = sorted(
        [
            (r["reference_period"].isoformat(), r["release_date"].isoformat(), float(r["value"]))
            for _, r in df.iterrows()
        ]
    )
    payload = json.dumps(tuples_sorted, sort_keys=True).encode("utf-8")
    fp_indep = hashlib.sha256(payload).hexdigest()
    assert fp_indep == _EXPECTED_SOURCE_FINGERPRINT_HEX
