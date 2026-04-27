"""Pure AR(1) surprise constructor for the Rev-1 remittance pipeline.

This module implements Task 10 of the Phase-A.0 remittance-surprise
implementation plan. It builds the primary RHS (AR(1) residual of
``ΔlogRem_m``) for the remittance-surprise → TRM-RV regression, following
the Rev-1 spec authoritative at
``contracts/docs/superpowers/specs/2026-04-20-remittance-surprise-trm-rv-spec-rev1.md``.

Purity contract (functional-python skill):
  * Zero I/O, zero side effects, zero network. No DB access. No logging.
  * Frozen dataclasses (``slots=True``) for all value types; free functions
    for all transformations.
  * Input validation at each public function's first line only; no internal
    re-validation loops.
  * Composition over inheritance; no class methods beyond ``__post_init__``
    validation.

Rev-1 spec references (verbatim):
  * §4.6 LOCF protocol — anchored on BanRep release dates; for Friday-close
    date ``d_w`` in week w, surprise = residual of the monthly release with
    ``max(release_date)`` subject to ``release_date ≤ d_w``. Ties → earlier
    ``reference_period``.
  * §4.7 AR order — primary = AR(1); SARIMA(1,0,0)(1,0,0)_12 deferred.
  * §4.8 Vintage discipline — primary = real-time (first-printed value per
    ``reference_period``); sensitivity = current-vintage (latest release
    per ``reference_period``).
  * §12 row 7 — pre-sample-end = 2008-01-01; rolling refit protocol
    deferred to NB2 §3 (this module uses a single fixed fit on the full
    vintage-filtered series).

The AR(1) model:
    Δlog(Rem)_t = μ + φ · Δlog(Rem)_{t-1} + ε_t
fit by OLS via ``np.linalg.lstsq`` (transparent; avoids a hidden
statsmodels dependency on the primary code path).

Downstream consumption: Task 11 commits the real BanRep-derived fixture;
Task 12 plumbs ``SurpriseSeries.source_fingerprint`` into the Rev-1 spec §9
decision-hash extension; Task 9's ``load_cleaned_remittance_panel`` seam
calls ``construct_ar1_surprise`` once the fixture lands.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from datetime import date
from typing import Final, Literal

import numpy as np
import pandas as pd


# ── Constants ────────────────────────────────────────────────────────────────


#: Allowed ``vintage_policy`` tokens per Rev-1 spec §4.8.
_ALLOWED_VINTAGE_POLICIES: Final[frozenset[str]] = frozenset(
    {"real-time", "current-vintage"}
)

#: Minimum pre-sample depth (months) required for an AR(1) fit. Twelve months
#: is the standard documented floor in the Rev-4 CPI analog
#: (``econ_panels._ar1_expanding_surprises`` warmup default) and protects
#: against silent overfitting on a short history.
_MIN_PRE_SAMPLE_MONTHS: Final[int] = 12

#: Required columns on the input ``series`` DataFrame.
_REQUIRED_COLUMNS: Final[frozenset[str]] = frozenset(
    {"reference_period", "release_date", "value"}
)


# ── Value types (frozen, slotted) ────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class AR1Params:
    """AR(1) coefficient bundle for the fitted ``Δlog(Rem)`` series.

    ``phi`` is the lag-1 coefficient; ``mu`` is the intercept; ``sigma2`` is
    the unbiased residual variance (OLS ``RSS/(n-2)``). All three enter the
    Rev-1 spec §9 decision-hash via the column-spec JSON — any numeric drift
    flips the extended hash downstream.
    """

    phi: float
    mu: float
    sigma2: float


@dataclass(frozen=True, slots=True)
class SurpriseSeries:
    """Output payload of :func:`construct_ar1_surprise`.

    Fields:
      * ``monthly_residuals`` — :class:`pandas.Series` indexed by
        ``reference_period`` (``datetime.date``); values are AR(1) residuals
        in log-diff units. The first two entries are NaN (one for the diff,
        one for the lag).
      * ``weekly_interpolated`` — :class:`pandas.Series` indexed by Friday
        ``pd.Timestamp``; LOCF-aligned per Rev-1 spec §4.6. NaN before the
        first release_date in the horizon.
      * ``ar_params`` — :class:`AR1Params` with φ, μ, σ².
      * ``vintage_policy`` — one of ``{"real-time", "current-vintage"}``;
        echoed from the input for audit.
      * ``source_fingerprint`` — 64-char lowercase SHA-256 hex of sorted
        ``(reference_period, release_date, value)`` tuples.

    Frozen + slotted per functional-python; mutation raises
    ``FrozenInstanceError``. No instance ``__dict__``.
    """

    monthly_residuals: pd.Series
    weekly_interpolated: pd.Series
    ar_params: AR1Params
    vintage_policy: str
    source_fingerprint: str


# ── Private helpers ──────────────────────────────────────────────────────────


def _validate_input(
    series: pd.DataFrame,
    pre_sample_end_date: date,
    vintage_policy: str,
) -> None:
    """Boundary-only input validation.

    Raises :class:`ValueError` with an informative message on any bad input.
    Invoked as the first statement of :func:`construct_ar1_surprise`; no
    further validation occurs inside the implementation.
    """
    # Column presence.
    missing = _REQUIRED_COLUMNS - set(series.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(
            f"series is missing required columns: {missing_list}. "
            f"Expected columns: {sorted(_REQUIRED_COLUMNS)}; "
            f"got: {sorted(series.columns)}."
        )

    # Vintage policy token.
    if vintage_policy not in _ALLOWED_VINTAGE_POLICIES:
        raise ValueError(
            f"vintage_policy must be one of {sorted(_ALLOWED_VINTAGE_POLICIES)}; "
            f"got {vintage_policy!r}."
        )

    # Monotone reference_period (non-strict so duplicate ref-periods from
    # multi-vintage rows are permitted; they are resolved by the vintage
    # filter below).
    ref_periods = series["reference_period"]
    if not ref_periods.is_monotonic_increasing:
        raise ValueError(
            "series.reference_period must be monotone non-decreasing. "
            "Pre-sort the input by (reference_period, release_date) before "
            "calling construct_ar1_surprise."
        )

    # Pre-sample end sanity: must be strictly before the last release_date
    # (otherwise the function has no out-of-sample period at all).
    max_release = series["release_date"].max()
    if pre_sample_end_date >= max_release:
        raise ValueError(
            f"pre_sample_end_date ({pre_sample_end_date}) must be strictly "
            f"before the last release_date ({max_release}); otherwise the "
            f"series has no post-pre-sample observations."
        )

    # Insufficient pre-sample depth: need ≥ _MIN_PRE_SAMPLE_MONTHS monthly
    # reference-periods at or before the pre-sample end.
    pre_sample_periods = series.loc[
        series["reference_period"] <= pre_sample_end_date, "reference_period"
    ].unique()
    if len(pre_sample_periods) < _MIN_PRE_SAMPLE_MONTHS:
        raise ValueError(
            f"insufficient pre-sample observations: need at least "
            f"{_MIN_PRE_SAMPLE_MONTHS} monthly reference_periods on or before "
            f"pre_sample_end_date ({pre_sample_end_date}); got "
            f"{len(pre_sample_periods)}."
        )


def _filter_by_vintage(
    series: pd.DataFrame,
    vintage_policy: Literal["real-time", "current-vintage"],
) -> pd.DataFrame:
    """Collapse multi-vintage rows to one row per ``reference_period``.

    * ``real-time`` → earliest ``release_date`` per ``reference_period``
      (first-printed value, per Rev-1 spec §4.8).
    * ``current-vintage`` → latest ``release_date`` per ``reference_period``
      (revised value at the present time).
    """
    sorted_series = series.sort_values(["reference_period", "release_date"])
    group = sorted_series.groupby("reference_period", as_index=False)
    if vintage_policy == "real-time":
        return group.first().reset_index(drop=True)
    # current-vintage
    return group.last().reset_index(drop=True)


def _fit_ar1_on_log_diffs(values: np.ndarray) -> AR1Params:
    """Fit AR(1) on log-differences of a positive value series via OLS.

    Given ``values`` (strictly positive, length ≥ 3), computes
    ``dlog = np.diff(np.log(values))`` and fits
    ``dlog_t = mu + phi · dlog_{t-1} + eps_t`` by ordinary least squares.

    Returns :class:`AR1Params` with the fitted ``phi``, ``mu`` and the
    unbiased residual variance ``sigma2 = RSS/(n-2)``.
    """
    log_vals = np.log(values.astype(float))
    dlog = np.diff(log_vals)
    y = dlog[1:]
    y_lag = dlog[:-1]
    design = np.column_stack([np.ones_like(y_lag), y_lag])
    coeffs, *_ = np.linalg.lstsq(design, y, rcond=None)
    mu = float(coeffs[0])
    phi = float(coeffs[1])
    residuals = y - (mu + phi * y_lag)
    n = len(residuals)
    # Unbiased residual variance with 2 estimated parameters (mu, phi).
    sigma2 = float(np.sum(residuals**2) / (n - 2)) if n > 2 else float("nan")
    return AR1Params(phi=phi, mu=mu, sigma2=sigma2)


def _compute_monthly_residuals(filtered: pd.DataFrame, params: AR1Params) -> pd.Series:
    """Return the AR(1) residual series indexed by ``reference_period``.

    The first two entries are NaN (one for the log-diff, one for the AR(1)
    lag); subsequent entries are the residuals of the fit in
    ``dlog_t - (mu + phi * dlog_{t-1})`` form.
    """
    log_vals = np.log(filtered["value"].values.astype(float))
    dlog = np.diff(log_vals)
    y = dlog[1:]
    y_lag = dlog[:-1]
    residuals = y - (params.mu + params.phi * y_lag)

    # Align to reference_period: resid[j] corresponds to dlog[j+1], which
    # corresponds to ref_period[j+2]. First two ref-periods are NaN.
    ref_periods = filtered["reference_period"].tolist()
    n = len(ref_periods)
    values_aligned = [np.nan, np.nan] + list(residuals)
    # Ensure length matches; slice in case of any off-by-one edge cases
    # (impossible given the construction above, but defend for safety).
    values_aligned = values_aligned[:n]
    return pd.Series(values_aligned, index=ref_periods, name="surprise")


def _locf_weekly_align(
    monthly_surprise: pd.DataFrame,
    weekly_index: pd.DatetimeIndex,
) -> pd.Series:
    """Step-interpolate monthly surprise to a weekly Friday index via LOCF.

    Per Rev-1 spec §4.6: for each Friday ``d_w`` in ``weekly_index``, pick
    the ``surprise`` of the row with the largest ``release_date`` subject to
    ``release_date ≤ d_w``; on tie (multiple rows sharing the same max
    release_date), pick the row with the earliest ``reference_period`` per
    spec §12 row 6. Fridays that precede the first release_date in the
    series receive NaN.

    Parameters
    ----------
    monthly_surprise
        DataFrame with columns ``reference_period``, ``release_date``,
        ``surprise``. Values missing from ``surprise`` (NaN) are still
        eligible for LOCF selection — a NaN surprise carried forward
        legitimately reflects "no AR(1) residual available yet".
    weekly_index
        Friday-close :class:`pd.DatetimeIndex` defining the target
        interpolation surface.

    Returns
    -------
    pandas.Series
        Indexed by ``weekly_index``; values are the LOCF-selected
        ``surprise`` per week. Name is ``remittance_surprise_weekly``.
    """
    if monthly_surprise.empty:
        return pd.Series(
            [np.nan] * len(weekly_index),
            index=weekly_index,
            name="remittance_surprise_weekly",
            dtype=float,
        )

    # Pre-sort once: release_date asc (primary), reference_period asc
    # (secondary — for deterministic tie-breaking).
    sorted_src = monthly_surprise.sort_values(
        ["release_date", "reference_period"]
    ).reset_index(drop=True)
    release_dates = sorted_src["release_date"].tolist()
    ref_periods = sorted_src["reference_period"].tolist()
    surprises = sorted_src["surprise"].tolist()

    out_values: list[float] = []
    for friday in weekly_index:
        friday_date = friday.date() if isinstance(friday, pd.Timestamp) else friday
        # Find max release_date ≤ friday_date.
        chosen_idx: int | None = None
        chosen_release: date | None = None
        chosen_ref: date | None = None
        for i, rd in enumerate(release_dates):
            if rd > friday_date:
                continue
            if chosen_release is None or rd > chosen_release:
                chosen_idx, chosen_release, chosen_ref = i, rd, ref_periods[i]
            elif rd == chosen_release and ref_periods[i] < chosen_ref:  # type: ignore[operator]
                # Tie on release_date → earlier reference_period wins
                # (Rev-1 spec §12 row 6).
                chosen_idx, chosen_ref = i, ref_periods[i]
        if chosen_idx is None:
            out_values.append(np.nan)
        else:
            out_values.append(float(surprises[chosen_idx]) if surprises[chosen_idx] is not None and not _is_nan(surprises[chosen_idx]) else np.nan)

    return pd.Series(
        out_values, index=weekly_index, name="remittance_surprise_weekly", dtype=float
    )


def _is_nan(x: object) -> bool:
    """Return ``True`` if ``x`` is a float-NaN, else ``False``."""
    try:
        return bool(np.isnan(x))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False


def _compute_source_fingerprint(series: pd.DataFrame) -> str:
    """Return the SHA-256 hex fingerprint of the sorted source tuples.

    Canonicalization:
      1. Coerce ``reference_period`` and ``release_date`` to ISO-8601
         strings, ``value`` to :class:`float`.
      2. Build the list of triples ``(ref_iso, rel_iso, value)``.
      3. Sort ascending on the triple (lexicographic Python default).
      4. Serialize with ``json.dumps(..., sort_keys=True)`` and encode UTF-8.
      5. Apply SHA-256 and return the lowercase hex digest.

    Order-invariance follows from the explicit sort. Determinism follows
    from canonical JSON encoding (fixed key order, ASCII digits, no
    platform-dependent float formatting for finite values).
    """
    tuples = [
        (
            _to_iso(row["reference_period"]),
            _to_iso(row["release_date"]),
            float(row["value"]),
        )
        for _, row in series.iterrows()
    ]
    tuples_sorted = sorted(tuples)
    payload = json.dumps(tuples_sorted, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _to_iso(d: object) -> str:
    """Coerce a date-like value to an ISO-8601 ``YYYY-MM-DD`` string."""
    if isinstance(d, date):
        return d.isoformat()
    if isinstance(d, pd.Timestamp):
        return d.date().isoformat()
    if isinstance(d, str):
        # Assume already ISO-8601; round-trip through date to normalize.
        return date.fromisoformat(d).isoformat()
    # Pandas-converted numpy datetime64 → Timestamp → date.
    return pd.Timestamp(d).date().isoformat()


def _build_weekly_friday_index(filtered: pd.DataFrame) -> pd.DatetimeIndex:
    """Construct the Friday-close index spanning the filtered-series horizon.

    Horizon = ``[first_release_date, last_reference_period]``. Both
    endpoints are included; the Fridays are produced via
    ``pd.date_range(..., freq="W-FRI")``.
    """
    first_release = filtered["release_date"].min()
    last_ref = filtered["reference_period"].max()
    return pd.date_range(start=first_release, end=last_ref, freq="W-FRI")


# ── Public entry point ───────────────────────────────────────────────────────


def construct_ar1_surprise(
    series: pd.DataFrame,
    pre_sample_end_date: date,
    vintage_policy: Literal["real-time", "current-vintage"],
) -> SurpriseSeries:
    """Build the AR(1) remittance surprise series under Rev-1 spec §4.6–§4.8.

    Parameters
    ----------
    series
        DataFrame with columns ``reference_period`` (month-end date),
        ``release_date`` (BanRep publication date), ``value`` (USD
        aggregate monthly remittance, units irrelevant because the AR(1)
        fit is on log-differences). Multiple rows per ``reference_period``
        encode vintages: earliest ``release_date`` = first-printed, latest
        = most-recent revision.
    pre_sample_end_date
        Anchor for pre-sample-depth validation (Rev-1 spec §12 row 7
        default: ``2008-01-01``). Must have ≥ 12 monthly ``reference_period``
        values on or before this date, else ``ValueError``.
    vintage_policy
        ``"real-time"`` uses first-printed values (primary per spec §4.8);
        ``"current-vintage"`` uses latest revisions (sensitivity).

    Returns
    -------
    SurpriseSeries
        The full payload: monthly residuals, LOCF-interpolated weekly
        residuals on a Friday-close index, fitted AR(1) parameters, echoed
        vintage policy token, and source fingerprint.

    Raises
    ------
    ValueError
        On any of: missing required columns; non-monotone
        ``reference_period``; invalid ``vintage_policy`` token;
        ``pre_sample_end_date`` not strictly before the last release_date;
        fewer than 12 pre-sample monthly observations.
    """
    # Step 0 — boundary validation.
    _validate_input(series, pre_sample_end_date, vintage_policy)

    # Step 1 — vintage filter (collapse multi-vintage rows).
    filtered = _filter_by_vintage(series, vintage_policy)

    # Step 2 — fit AR(1) on Δlog(Rem).
    params = _fit_ar1_on_log_diffs(filtered["value"].values)

    # Step 3 — align residuals to ``reference_period`` month-ends.
    monthly_residuals = _compute_monthly_residuals(filtered, params)

    # Step 4 — LOCF-interpolate to a Friday-close weekly index.
    weekly_index = _build_weekly_friday_index(filtered)
    # Build the DataFrame expected by _locf_weekly_align: one row per
    # reference_period, carrying its release_date and the computed surprise.
    monthly_surprise_df = pd.DataFrame(
        {
            "reference_period": filtered["reference_period"].values,
            "release_date": filtered["release_date"].values,
            "surprise": monthly_residuals.values,
        }
    )
    weekly_interpolated = _locf_weekly_align(monthly_surprise_df, weekly_index)

    # Step 5 — source fingerprint (over the ORIGINAL input, not the filtered
    # view, so vintage-policy changes are visible at the hash level).
    fingerprint = _compute_source_fingerprint(series)

    return SurpriseSeries(
        monthly_residuals=monthly_residuals,
        weekly_interpolated=weekly_interpolated,
        ar_params=params,
        vintage_policy=vintage_policy,
        source_fingerprint=fingerprint,
    )
