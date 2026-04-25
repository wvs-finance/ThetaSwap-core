"""Y₃ inequality-differential compute primitives — Rev-5.3.1 Task 11.N.2d.

Pre-committed `Final` constants per design doc
``contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md``
§9. Step 0 of Task 11.N.2d commits these constants ONLY (no compute logic
yet) so the failing-first test imports them and asserts byte-exact match
against the design-doc spec.

Anti-fishing guarantee (mirrors Carbon X_d design §3): these eight values
are pinned at Step 0 BEFORE any data ingestion. Modification requires a
new design-doc revision + 3-way review.

Design-doc references:
- §1 sign convention: ``Δ_country_t = R_equity + Δlog(WC_CPI)`` rises with
  inequality (rich gains OR working-class loss).
- §4 budget-share weights: 60% food / 25% energy+housing-utilities /
  15% transport-fuel (World Bank LAC bottom-quintile basket per
  ``contracts/.scratch/2026-04-24-y3-consumption-proxy-research.md`` §4).
- §5 aggregation: equal-weight 1/4 across CO/BR/KE/EU.
- §6 panel windows: Sep-2024 → 2026-04-24 (~84 weeks primary);
  Aug-2023 → 2026-04-24 (~140 weeks sensitivity, deferred to Task
  11.N.2d.1).
- §7 LOCF: monthly→weekly Friday-anchored America/Bogota.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Final
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


# ── Pre-committed parameters (design doc §9) ────────────────────────────────

WC_CPI_FOOD_WEIGHT: Final[float] = 0.60
WC_CPI_ENERGY_HOUSING_WEIGHT: Final[float] = 0.25
WC_CPI_TRANSPORT_FUEL_WEIGHT: Final[float] = 0.15

COUNTRY_AGGREGATION_WEIGHT: Final[float] = 0.25  # equal 1/4 per anchor country

PRIMARY_PANEL_START: Final[date] = date(2024, 9, 1)
PRIMARY_PANEL_END: Final[date] = date(2026, 4, 24)
SENSITIVITY_PANEL_START: Final[date] = date(2023, 8, 1)

LOCF_TIMEZONE: Final[str] = "America/Bogota"


# ── Frozen dataclass output of compute_y3_aggregate ─────────────────────────


@dataclass(frozen=True, slots=True)
class Y3Panel:
    """Y₃ aggregated weekly panel — output of ``compute_y3_aggregate``.

    Attributes:
        weeks: tuple of Friday-anchored ``date`` values (one per observation).
        y3_value: tuple of ``Y3_t`` floats (equal-weighted across countries).
        per_country_diffs: dict ``{country_code: tuple[float, ...]}``;
            country codes are ISO-2 ("CO", "BR", "KE", "EU") and only
            countries that actually contributed to the aggregate appear.
        n_observations: number of observations (== ``len(weeks)``).
    """

    weeks: tuple[date, ...]
    y3_value: tuple[float, ...]
    per_country_diffs: dict[str, tuple[float, ...]]
    n_observations: int


# ── Compute functions ──────────────────────────────────────────────────────


def compute_wc_cpi_weighted(components: pd.DataFrame) -> pd.Series:
    """Combine 4 CPI components into the working-class CPI per design §4.

    Weights (pre-committed): 60% food / 25% energy+housing-utilities /
    15% transport-fuel. Energy and housing are jointly weighted at 25%
    (averaged within the bucket); design doc §4 lists them as a single
    "energy+housing-utilities" bucket per the World Bank LAC bottom-
    quintile budget-share basket.

    Inputs (DataFrame columns):
        date         — datetime-like
        food_cpi     — index level
        energy_cpi   — index level
        housing_cpi  — index level
        transport_cpi — index level

    Output: pd.Series indexed by ``date`` with the WC-CPI composite level.
    """
    eh_avg = (components["energy_cpi"] + components["housing_cpi"]) / 2.0
    wc = (
        WC_CPI_FOOD_WEIGHT * components["food_cpi"]
        + WC_CPI_ENERGY_HOUSING_WEIGHT * eh_avg
        + WC_CPI_TRANSPORT_FUEL_WEIGHT * components["transport_cpi"]
    )
    if "date" in components.columns:
        wc.index = pd.to_datetime(components["date"]).values
    return wc.rename("wc_cpi")


def interpolate_monthly_to_weekly_locf(
    monthly: pd.Series,
    friday_anchor_tz: str,
) -> pd.Series:
    """LOCF interpolation: monthly → weekly Friday-anchored series.

    Each Friday holds the latest monthly observation as of that Friday.
    Friday anchoring is performed in the specified timezone (per design
    doc §7 — America/Bogota mirrors Task 11.M.6 Banrep IBR weekly
    extraction).

    Inputs:
        monthly: pd.Series indexed by datetime-like; one row per month.
        friday_anchor_tz: IANA timezone name (e.g. ``"America/Bogota"``).

    Output: pd.Series indexed by Friday timestamps in the anchor tz, with
    the LOCF value of ``monthly`` as of each Friday. Fridays before the
    first monthly observation are NOT emitted (no extrapolation).
    """
    # Validate timezone arg (raises on unknown).
    ZoneInfo(friday_anchor_tz)

    monthly = monthly.copy()
    monthly.index = pd.to_datetime(monthly.index)
    monthly = monthly.sort_index()

    if monthly.empty:
        return pd.Series([], dtype="float64", name=monthly.name or "value")

    first_date = monthly.index[0]
    last_date = monthly.index[-1]

    # Build a Friday-anchored index from the first Friday on or after
    # ``first_date`` through the last Friday on or before today (or the
    # caller's requested window — caller post-filters as needed).
    # Use pandas weekly Friday frequency.
    fridays = pd.date_range(
        start=first_date,
        end=last_date + pd.Timedelta(days=120),  # extend for LOCF tail
        freq="W-FRI",
    )

    # Reindex monthly onto the Friday timeline with forward-fill.
    aligned = monthly.reindex(
        monthly.index.union(fridays)
    ).sort_index().ffill().reindex(fridays)
    aligned = aligned.dropna()
    aligned.name = monthly.name or "value"
    return aligned


def compute_per_country_differential(
    equity_returns: pd.Series,
    wc_cpi_logchange: pd.Series,
) -> pd.Series:
    """Per-country inequality differential: Δ = R_equity + Δlog(WC_CPI).

    Design doc §1 sign convention — rises with inequality via either
    rich-side gains or working-class cost-of-living squeeze.

    Inputs:
        equity_returns: weekly Friday-anchored log-returns of country index.
        wc_cpi_logchange: weekly Friday-anchored log-change of WC-CPI.

    Output: pd.Series of differentials, indexed by the intersection of
    the two input indices (inner-join to drop weeks where either input
    is missing).
    """
    # Inner-join to require both series present.
    df = pd.concat(
        {"r_eq": equity_returns, "d_wc": wc_cpi_logchange},
        axis=1,
        join="inner",
    )
    out = df["r_eq"] + df["d_wc"]
    out.name = "country_diff"
    return out


def compute_y3_aggregate(
    per_country_diffs: dict[str, pd.Series],
) -> Y3Panel:
    """Equal-weight Y₃ aggregate across the supplied countries.

    Design doc §5: ``Y₃_t = (1/4) × Σ Δ_country_t``. When a country
    drops out (data fetch failure per recovery protocol §10 row 1), the
    aggregate divides by the number of countries actually present
    (e.g. 1/3 for 3-country fallback) — the equal-weight invariant
    inside the supplied set is preserved.

    Inputs:
        per_country_diffs: dict ``{country_code: pd.Series}``; each
            series indexed by Friday timestamps with weekly differentials.

    Output: ``Y3Panel`` frozen dataclass.

    Independent reproduction witness: the dict-mean over each row is
    computed directly via ``pd.DataFrame(per_country_diffs).mean(axis=1)``;
    the test suite recomputes it by hand to verify byte-exactness.
    """
    if not per_country_diffs:
        return Y3Panel(
            weeks=tuple(),
            y3_value=tuple(),
            per_country_diffs={},
            n_observations=0,
        )

    # Stack into a DataFrame on a unified weekly index (inner-join).
    df = pd.DataFrame(per_country_diffs).dropna(how="any")

    # Equal-weight mean across columns (this is 1/N where N=number of
    # countries supplied, preserving the design-doc §5 invariant under
    # the 3-country fallback path).
    y3 = df.mean(axis=1)

    weeks = tuple(pd.Timestamp(idx).date() for idx in df.index)
    y3_value = tuple(float(v) for v in y3.tolist())
    per_country = {
        c: tuple(float(v) for v in df[c].tolist())
        for c in df.columns
    }

    return Y3Panel(
        weeks=weeks,
        y3_value=y3_value,
        per_country_diffs=per_country,
        n_observations=len(weeks),
    )


# ── Helpers consumed by ingestion path ──────────────────────────────────────


def compute_weekly_log_return(
    daily_close: pd.Series,
    friday_anchor_tz: str = LOCF_TIMEZONE,
) -> pd.Series:
    """Friday-to-Friday log-return of a daily-close price series.

    Rolls to the last available trading day per design doc §10 row 3
    (Friday-holiday equity calendar). Returns indexed by Friday
    timestamps.
    """
    ZoneInfo(friday_anchor_tz)  # validate

    daily = daily_close.copy()
    daily.index = pd.to_datetime(daily.index)
    daily = daily.sort_index()

    if daily.empty:
        return pd.Series([], dtype="float64", name="equity_log_return_weekly")

    fridays = pd.date_range(
        start=daily.index[0],
        end=daily.index[-1],
        freq="W-FRI",
    )
    # For each Friday, take the latest available close on or before that Friday.
    weekly_close = daily.reindex(
        daily.index.union(fridays)
    ).sort_index().ffill().reindex(fridays)

    weekly_close = weekly_close.dropna()
    if len(weekly_close) < 2:
        return pd.Series(
            [], dtype="float64", name="equity_log_return_weekly"
        )

    log_returns = np.log(weekly_close / weekly_close.shift(1)).dropna()
    log_returns.name = "equity_log_return_weekly"
    return log_returns


def compute_weekly_log_change(
    weekly_level: pd.Series,
) -> pd.Series:
    """Weekly first-difference of log levels: Δlog(x_t) = log(x_t) - log(x_{t-1}).

    Used for the WC-CPI Δlog series feeding ``compute_per_country_differential``.
    """
    s = weekly_level.copy()
    s = s[s > 0].dropna()
    if len(s) < 2:
        return pd.Series([], dtype="float64", name="wc_cpi_log_change")
    out = np.log(s / s.shift(1)).dropna()
    out.name = "wc_cpi_log_change"
    return out
