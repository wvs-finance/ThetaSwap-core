"""Weekly on-chain flow vector aggregator.

Phase-A.0 Rev-3.3 Task 11.B of the remittance-surprise implementation plan.
Pure transformation from the Task-11.A daily 8-column fixture (COPM + cCOP
on-chain flows) to a 6-channel weekly vector, Friday-anchored per Rev-4
panel discipline.

Public API:
  * :data:`WEEKLY_VECTOR_COLUMNS` — the six output column names, in order.
  * :func:`aggregate_daily_to_weekly_vector` — the single transformation.

Six weekly channels (per spec):
  1. ``flow_sum_w``                   — Σ daily ``net_flow`` within the week.
  2. ``flow_var_w``                   — population variance (ddof=0) of the 7
                                         daily ``net_flow`` values.
  3. ``flow_concentration_w``         — INTRA-WEEK Herfindahl over daily
                                         ``|net_flow|``:
                                         ``Σ|x_d|²  /  (Σ|x_d|)²``. Range
                                         ``[1/7, 1]``. **NOT** per-address HHI —
                                         see Rev-3.3 plan line 316 clarification.
  4. ``flow_directional_asymmetry_w`` — integer in ``[-7, +7]``: count of days
                                         with ``directional_flow > 0`` minus
                                         count with ``directional_flow < 0``.
                                         Zero-flow days count as neither.
  5. ``unique_daily_active_senders_w`` — Σ (``copm_unique_minters`` +
                                         ``ccop_unique_senders``) across the 7
                                         daily rows (union upper bound; the two
                                         token cohorts are separate contracts,
                                         so a single entity can appear in both).
  6. ``flow_max_single_day_w``        — max daily ``|net_flow|`` within the week.

Daily per-row derivations (used internally; not part of the public contract):
  * ``net_flow_d        = Σ (copm_mint_usd, copm_burn_usd,
                             ccop_usdt_inflow_usd, ccop_usdt_outflow_usd)``
    (NaN-safe; all four channels are non-negative per Task-11.A validator).
  * ``directional_flow_d = (copm_mint_usd - copm_burn_usd)
                          + (ccop_usdt_inflow_usd - ccop_usdt_outflow_usd)``
    (NaN-safe).
  * Pre-cCOP-launch days (date < 2024-10-31) carry NaN in cCOP columns; the
    aggregator treats NaNs as zero so COPM-only aggregation still flows.

Edge cases:
  * Weeks with <7 daily observations → all six channels emit NaN
    (explicit NaN-propagation; NOT zero-filling).
  * Empty daily_df input → empty output DataFrame (not an error).

Week anchoring (Rev-4 discipline):
  Each calendar week aligns on Friday-close in the Colombian operating
  timezone. Because the Task-11.A ``date`` column is already a calendar
  date (daily UTC block-date), the aggregator resamples with
  ``freq='W-FRI', label='right', closed='right'`` — each week spans
  Sat..Fri and is labelled on the Friday. The ``friday_anchor_tz``
  parameter's behavior depends on the input ``date`` column:
    * If the ``date`` column is timezone-naive (the Task-11.A case), the
      dates are treated as calendar dates AT the anchor timezone and
      resampled without any shift — this matches the Rev-4 convention,
      where ``pd.date_range(..., freq='W-FRI')`` operates on a naive
      calendar index (see ``surprise_constructor._build_weekly_friday_index``).
      Applying a UTC-to-Bogota conversion on naive calendar dates would
      silently shift the calendar day, corrupting semantics.
    * If the ``date`` column is timezone-aware, values are converted to
      ``friday_anchor_tz`` before resampling and the index is stripped to
      naive afterwards so downstream joins (Rev-4 naive Friday index)
      remain aligned.
  Default ``America/Bogota`` matches the Rev-4 FX-vol weekly panel.

Purity contract (functional-python skill):
  Zero side effects. No I/O. No classes. Free functions only. Full
  typing. Input validation at each public function's first line.
"""
from __future__ import annotations

from typing import Final

import numpy as np
import pandas as pd


# ── Module-level contract ────────────────────────────────────────────────────


#: The six weekly output columns, in canonical order. Import this tuple
#: rather than re-deriving the schema in downstream consumers.
WEEKLY_VECTOR_COLUMNS: Final[tuple[str, ...]] = (
    "flow_sum_w",
    "flow_var_w",
    "flow_concentration_w",
    "flow_directional_asymmetry_w",
    "unique_daily_active_senders_w",
    "flow_max_single_day_w",
)

#: Required input columns (subset of Task-11.A's 8-column schema that the
#: aggregator actually reads). ``source_query_ids`` is not consumed.
_REQUIRED_INPUT_COLUMNS: Final[tuple[str, ...]] = (
    "date",
    "copm_mint_usd",
    "copm_burn_usd",
    "copm_unique_minters",
    "ccop_usdt_inflow_usd",
    "ccop_usdt_outflow_usd",
    "ccop_unique_senders",
)

#: Exact number of daily observations required for a "complete" week.
#: Weeks with fewer observations emit NaN on every channel per spec.
_DAYS_PER_WEEK: Final[int] = 7


# ── Public function ──────────────────────────────────────────────────────────


def aggregate_daily_to_weekly_vector(
    daily_df: pd.DataFrame,
    friday_anchor_tz: str = "America/Bogota",
) -> pd.DataFrame:
    """Aggregate a Task-11.A daily DataFrame to Friday-anchored weekly rows.

    Parameters
    ----------
    daily_df:
        DataFrame matching the Task-11.A 8-column schema (see
        :mod:`scripts.dune_onchain_flow_fetcher`). At minimum the seven
        columns in :data:`_REQUIRED_INPUT_COLUMNS` must be present; the
        eighth column (``source_query_ids``) is ignored by this aggregator.
    friday_anchor_tz:
        IANA timezone string identifying the Friday-close anchor. Default
        ``"America/Bogota"`` matches Rev-4 panel discipline. When the
        input ``date`` column is timezone-naive (the Task-11.A case),
        naive dates are treated as calendar dates in this timezone and
        no shift is applied before resampling (the Rev-4 convention uses
        naive Friday dates). When the input ``date`` column is timezone-
        aware, values are converted to ``friday_anchor_tz`` before
        resampling, preserving wall-clock semantics at the anchor.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns exactly equal to
        :data:`WEEKLY_VECTOR_COLUMNS` and index a naive DatetimeIndex of
        week-ending Fridays, strictly monotone increasing. Empty input
        yields an empty (zero-row) DataFrame with the correct columns.

    Raises
    ------
    ValueError
        If required input columns are missing, or ``date`` column is not
        datetime-like, or ``friday_anchor_tz`` is empty.
    """
    # ── Input validation ──
    if not isinstance(daily_df, pd.DataFrame):
        raise ValueError(
            "aggregate_daily_to_weekly_vector expected a DataFrame; "
            f"got {type(daily_df)!r}."
        )
    if not isinstance(friday_anchor_tz, str) or not friday_anchor_tz:
        raise ValueError(
            "friday_anchor_tz must be a non-empty IANA timezone string; "
            f"got {friday_anchor_tz!r}."
        )
    missing = tuple(c for c in _REQUIRED_INPUT_COLUMNS if c not in daily_df.columns)
    if missing:
        raise ValueError(
            f"daily_df is missing required columns: {missing!r}. "
            f"Expected at least {_REQUIRED_INPUT_COLUMNS!r}."
        )

    # ── Empty input → empty output (explicit early return) ──
    if len(daily_df) == 0:
        return _empty_weekly_frame()

    # ── Validate date column dtype ──
    if not pd.api.types.is_datetime64_any_dtype(daily_df["date"]):
        raise ValueError(
            "daily_df['date'] must be datetime-like; "
            f"got dtype={daily_df['date'].dtype!r}."
        )

    # ── Derive daily columns (pure, NaN-safe) ──
    daily = _derive_daily_columns(daily_df)

    # ── Resample to Friday-anchored weeks ──
    weekly, weekly_count = _resample_weekly(daily, friday_anchor_tz=friday_anchor_tz)

    # ── Propagate NaN on partial (<7-day) weeks ──
    weekly = _nan_out_partial_weeks(weekly, weekly_count)

    # ── Enforce canonical column order (defensive) ──
    return weekly[list(WEEKLY_VECTOR_COLUMNS)]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _empty_weekly_frame() -> pd.DataFrame:
    """Return the empty weekly DataFrame with the canonical column schema."""
    return pd.DataFrame(
        {
            "flow_sum_w": pd.Series([], dtype="float64"),
            "flow_var_w": pd.Series([], dtype="float64"),
            "flow_concentration_w": pd.Series([], dtype="float64"),
            "flow_directional_asymmetry_w": pd.Series([], dtype="float64"),
            "unique_daily_active_senders_w": pd.Series([], dtype="float64"),
            "flow_max_single_day_w": pd.Series([], dtype="float64"),
        },
        index=pd.DatetimeIndex([], name="date"),
    )


def _derive_daily_columns(daily_df: pd.DataFrame) -> pd.DataFrame:
    """Compute the per-day ``net_flow``, ``directional_flow``, and ``senders``
    columns used by the weekly aggregation.

    Returns a new DataFrame indexed by ``date`` with three numeric columns;
    the input is not modified. NaN values in the four USD channels and in
    ``ccop_unique_senders`` are treated as zero for arithmetic purposes,
    which lets pre-cCOP-launch days (cCOP NaN) aggregate via their COPM
    values alone.
    """
    # Work off an indexed copy so downstream resample() has a time axis.
    idx = pd.DatetimeIndex(daily_df["date"].to_numpy(), name="date")
    mint = daily_df["copm_mint_usd"].fillna(0.0).to_numpy(dtype="float64")
    burn = daily_df["copm_burn_usd"].fillna(0.0).to_numpy(dtype="float64")
    inflow = daily_df["ccop_usdt_inflow_usd"].fillna(0.0).to_numpy(dtype="float64")
    outflow = daily_df["ccop_usdt_outflow_usd"].fillna(0.0).to_numpy(dtype="float64")
    minters = daily_df["copm_unique_minters"].astype("float64").to_numpy()
    ccop_senders = daily_df["ccop_unique_senders"].fillna(0.0).to_numpy(dtype="float64")

    net_flow = mint + burn + inflow + outflow
    directional = (mint - burn) + (inflow - outflow)
    senders = minters + ccop_senders

    return pd.DataFrame(
        {
            "_net_flow": net_flow,
            "_directional": directional,
            "_senders": senders,
        },
        index=idx,
    ).sort_index()


def _resample_weekly(
    daily: pd.DataFrame,
    friday_anchor_tz: str,
) -> tuple[pd.DataFrame, pd.Series]:
    """Resample the daily derived DataFrame to Friday-anchored weeks.

    The index of ``daily`` is a DatetimeIndex. If timezone-naive, it is
    interpreted as calendar dates in ``friday_anchor_tz`` (Rev-4
    discipline). If timezone-aware, it is converted to ``friday_anchor_tz``
    first so the Friday anchor respects the Colombian operating timezone.

    Output index is naive (tz-stripped) to match Rev-4 panel conventions
    and simplify downstream joins.

    Returns
    -------
    (weekly_df, weekly_count):
        ``weekly_df`` has the six WEEKLY_VECTOR_COLUMNS populated from
        full-week arithmetic (no partial-week NaN propagation yet).
        ``weekly_count`` is an int64 Series (indexed identically) giving
        the number of daily observations contributing to each weekly
        row — the caller uses this to mask partial weeks.
    """
    idx = daily.index
    if idx.tz is not None:
        # tz-aware input: convert to anchor tz, then strip before resample so
        # the Friday boundary computed on wall-clock matches the anchor tz.
        daily = daily.tz_convert(friday_anchor_tz)
        daily = daily.tz_localize(None)
    # tz-naive input: treat as calendar dates at the anchor tz (Rev-4
    # convention — naive Friday date).

    nf = daily["_net_flow"]
    dirf = daily["_directional"]
    senders = daily["_senders"]

    resample_kwargs = dict(rule="W-FRI", label="right", closed="right")

    # Per-channel weekly aggregations.
    flow_sum_w = nf.resample(**resample_kwargs).sum(min_count=1)
    flow_var_w = nf.resample(**resample_kwargs).var(ddof=0)
    flow_concentration_w = nf.resample(**resample_kwargs).apply(
        _weekly_concentration
    )
    flow_directional_asymmetry_w = dirf.resample(**resample_kwargs).apply(
        _weekly_directional_asymmetry
    )
    unique_daily_active_senders_w = senders.resample(**resample_kwargs).sum(
        min_count=1
    )
    flow_max_single_day_w = nf.abs().resample(**resample_kwargs).max()

    # Per-week observation count — used by the caller to NaN-out partial weeks.
    weekly_count = nf.resample(**resample_kwargs).size().astype("int64")

    out = pd.DataFrame(
        {
            "flow_sum_w": flow_sum_w.astype("float64"),
            "flow_var_w": flow_var_w.astype("float64"),
            "flow_concentration_w": flow_concentration_w.astype("float64"),
            "flow_directional_asymmetry_w":
                flow_directional_asymmetry_w.astype("float64"),
            "unique_daily_active_senders_w":
                unique_daily_active_senders_w.astype("float64"),
            "flow_max_single_day_w": flow_max_single_day_w.astype("float64"),
        }
    )
    out.index.name = "date"
    return out.sort_index(), weekly_count.sort_index()


def _weekly_concentration(x: pd.Series) -> float:
    """Intra-week Herfindahl on ``|daily_net_flow|``.

    ``H_w = Σ |x_d|² / (Σ |x_d|)²`` ∈ [1/7, 1].

    Returns NaN if the weekly denominator is zero or the series is empty.
    """
    if len(x) == 0:
        return float("nan")
    a = np.abs(x.to_numpy(dtype="float64"))
    denom = a.sum() ** 2
    if denom == 0.0:
        return float("nan")
    return float((a ** 2).sum() / denom)


def _weekly_directional_asymmetry(x: pd.Series) -> float:
    """Weekly directional asymmetry: (# positive days) - (# negative days).

    Returns a float for pandas-compatibility (NaN for empty weeks). The
    count result is integer-valued; tests may cast back to int.
    """
    if len(x) == 0:
        return float("nan")
    a = x.to_numpy(dtype="float64")
    pos = int((a > 0.0).sum())
    neg = int((a < 0.0).sum())
    return float(pos - neg)


def _nan_out_partial_weeks(
    weekly: pd.DataFrame, weekly_count: pd.Series
) -> pd.DataFrame:
    """Blank out every channel on weeks with fewer than 7 daily observations.

    Per spec, weeks at the fixture boundaries (fewer than 7 daily rows) must
    emit NaN on all six channels — explicit NaN-propagation, not zero-fill
    nor partial-week extrapolation.

    Parameters
    ----------
    weekly:
        The weekly DataFrame emitted by :func:`_resample_weekly`.
    weekly_count:
        Integer Series, indexed identically to ``weekly``, giving the number
        of daily observations contributing to each weekly row.

    Returns
    -------
    pd.DataFrame
        A new DataFrame with all six channels set to NaN on rows where
        ``weekly_count < _DAYS_PER_WEEK``. The index is preserved so the
        caller can still see which Fridays are boundary weeks.
    """
    partial_mask = (weekly_count < _DAYS_PER_WEEK).to_numpy()
    if not partial_mask.any():
        return weekly
    out = weekly.copy()
    out.loc[partial_mask, list(WEEKLY_VECTOR_COLUMNS)] = np.nan
    return out
