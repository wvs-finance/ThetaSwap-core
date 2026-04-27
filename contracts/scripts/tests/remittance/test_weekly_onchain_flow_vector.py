"""TDD tests for the Task-11.B weekly on-chain flow vector aggregator.

Phase-A.0 Rev-3.3 Task 11.B of the remittance-surprise implementation plan.

These tests are written BEFORE implementation per ``feedback_strict_tdd`` and
MUST fail on ImportError until
``contracts/scripts/weekly_onchain_flow_vector.py`` exists.

Public API under test::

    aggregate_daily_to_weekly_vector(
        daily_df: pd.DataFrame,
        friday_anchor_tz: str = "America/Bogota",
    ) -> pd.DataFrame

Input is the Task-11.A 8-column schema (see
``contracts/scripts/dune_onchain_flow_fetcher.py::EXPECTED_COLUMNS``).
Output is a DataFrame with one row per Friday-anchored week, indexed by the
week-end Friday (right-label, right-closed convention so each week spans
Sat..Fri and is labelled on the Friday), carrying six channels per week:

  1. ``flow_sum_w``                   — Σ daily ``net_flow`` in the week.
  2. ``flow_var_w``                   — population variance (ddof=0) of daily
                                         ``net_flow``; NaN if <2 observations.
  3. ``flow_concentration_w``         — INTRA-WEEK HHI over daily ``|net_flow|``,
                                         i.e. ``Σ|x_d|²  /  (Σ|x_d|)²``. Range
                                         [1/7, 1]. NOT per-address HHI (the
                                         Task-11.A fixture does not carry per-
                                         address data and Rev-3.3 plan line 316
                                         explicitly clarifies this is intra-week).
  4. ``flow_directional_asymmetry_w`` — (positive-directional-days) minus
                                         (negative-directional-days). Integer
                                         in [-7, +7]. Zero-flow days count as
                                         neither positive nor negative.
  5. ``unique_daily_active_senders_w`` — Σ (``copm_unique_minters`` +
                                         ``ccop_unique_senders``) across the
                                         week's 7 days (upper-bound union —
                                         the two token cohorts are disjoint
                                         contracts so a single person can be
                                         counted in both).
  6. ``flow_max_single_day_w``        — max daily ``|net_flow|`` within the
                                         week.

Daily per-row derivations used by the aggregator:

  * ``net_flow = copm_mint_usd + copm_burn_usd +
                 ccop_usdt_inflow_usd + ccop_usdt_outflow_usd``  (NaN → 0;
                 all four USD channels are non-negative per the Task-11.A
                 validator, so this is total flow volume per day.)
  * ``directional_flow = (copm_mint_usd - copm_burn_usd)
                       + (ccop_usdt_inflow_usd - ccop_usdt_outflow_usd)`` (NaN→0).

Pre-cCOP-launch days (date < 2024-10-31) carry NaN in the cCOP columns by
Task-11.A contract; the aggregator treats those NaNs as zero so COPM-only
values still flow through correctly.

Edge cases:
  * Weeks with <7 days: emit NaN on all six channels (no partial-week
    imputation — explicit NaN-propagation, not zero-filling).
  * Empty daily_df input: empty weekly output, not an error.

Independent-reproduction-witness discipline (Rev-3.1 CR-B2 / plan line 324):
  Test 7 pins the 6 channels on the golden fixture's Week ending 2024-11-08
  (the equal-flow week). The pinned constants are computed by an INLINE
  reproduction of the aggregation logic — NOT via
  ``aggregate_daily_to_weekly_vector`` itself. This guards against
  silent-test-pass when the implementation and the test both share the same
  bug. These constants were committed BEFORE Step 3 implementation.

Purity contract (functional-python skill):
  The aggregator is a single free function operating on a DataFrame and a
  tz string. Zero side effects. Zero I/O. No inheritance. No classes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import pytest

# TDD red-phase import — MUST fail on ImportError until Task 11.B is
# implemented. Do not silence this with a try/except.
from scripts.weekly_onchain_flow_vector import (  # noqa: E402
    aggregate_daily_to_weekly_vector,
    WEEKLY_VECTOR_COLUMNS,
)
from scripts.dune_onchain_flow_fetcher import EXPECTED_COLUMNS


# ── Constants ────────────────────────────────────────────────────────────────

GOLDEN_CSV_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "fixtures" / "golden_daily_flow.csv"
)

#: The six weekly channels emitted by the aggregator.
EXPECTED_WEEKLY_COLUMNS: Final[tuple[str, ...]] = (
    "flow_sum_w",
    "flow_var_w",
    "flow_concentration_w",
    "flow_directional_asymmetry_w",
    "unique_daily_active_senders_w",
    "flow_max_single_day_w",
)

#: Floating-point tolerance for the pinned-witness block (Test 7).
#: Rev-3.1 CR-B2 mandates 6-decimal.
WITNESS_ATOL: Final[float] = 1e-6

#: Pinned independent-reproduction-witness values for the equal-flow
#: week ending 2024-11-08. Computed by the inline reproduction block
#: below, committed BEFORE Step 3 implementation. DO NOT regenerate
#: these constants from the implementation — that would defeat the
#: silent-test-pass guard.
PINNED_WEEK = pd.Timestamp("2024-11-08")
PINNED_FLOW_SUM_W: Final[float] = 700.000000
PINNED_FLOW_VAR_W: Final[float] = 0.000000
PINNED_FLOW_CONCENTRATION_W: Final[float] = 0.142857  # 1/7 to 6 decimals
PINNED_FLOW_DIRECTIONAL_ASYMMETRY_W: Final[int] = 7
PINNED_UNIQUE_DAILY_ACTIVE_SENDERS_W: Final[int] = 49
PINNED_FLOW_MAX_SINGLE_DAY_W: Final[float] = 100.000000


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def golden_daily_df() -> pd.DataFrame:
    """Load the hand-authored 35-row golden fixture.

    Uses ``comment='#'`` so the header commentary block in the CSV is
    stripped cleanly, mirroring the Task-11.A loader's read-convention.
    """
    if not GOLDEN_CSV_PATH.is_file():
        pytest.fail(
            f"Golden Task-11.B fixture CSV missing at {GOLDEN_CSV_PATH}. "
            "This fixture is hand-authored and committed under "
            "contracts/scripts/tests/remittance/fixtures/."
        )
    df = pd.read_csv(
        GOLDEN_CSV_PATH,
        comment="#",
        parse_dates=["date"],
        dtype={
            "copm_mint_usd": "float64",
            "copm_burn_usd": "float64",
            "copm_unique_minters": "int64",
            "ccop_usdt_inflow_usd": "float64",
            "ccop_usdt_outflow_usd": "float64",
            "ccop_unique_senders": "float64",
            "source_query_ids": "object",
        },
    )
    # Sanity: verify the fixture shape before tests depend on it.
    assert tuple(df.columns) == EXPECTED_COLUMNS, (
        f"Golden fixture schema drift: {tuple(df.columns)!r} vs "
        f"expected {EXPECTED_COLUMNS!r}"
    )
    assert len(df) == 35, f"Golden fixture must be exactly 35 rows; got {len(df)}"
    return df


# ── Test 1: module import + public symbol surface ───────────────────────────


def test_aggregator_is_importable() -> None:
    """``aggregate_daily_to_weekly_vector`` exists and is callable."""
    assert callable(aggregate_daily_to_weekly_vector)
    assert isinstance(WEEKLY_VECTOR_COLUMNS, tuple)
    assert WEEKLY_VECTOR_COLUMNS == EXPECTED_WEEKLY_COLUMNS


# ── Test 2: output schema — 6 required columns at expected dtypes ───────────


def test_output_schema_six_required_columns(golden_daily_df: pd.DataFrame) -> None:
    """Output carries exactly the six documented weekly channels."""
    out = aggregate_daily_to_weekly_vector(golden_daily_df)

    assert isinstance(out, pd.DataFrame)
    assert tuple(out.columns) == EXPECTED_WEEKLY_COLUMNS

    # Dtype expectations:
    #   * flow_sum_w, flow_var_w, flow_concentration_w, flow_max_single_day_w: float64
    #   * flow_directional_asymmetry_w: integer-valued — allowed int64 OR float64
    #                                    (pandas resample().apply may float-ify;
    #                                    we only require the VALUES are integral).
    #   * unique_daily_active_senders_w: integer-valued — same tolerance.
    for col in ("flow_sum_w", "flow_var_w", "flow_concentration_w",
                "flow_max_single_day_w"):
        assert pd.api.types.is_float_dtype(out[col]), \
            f"{col} must be float-dtype; got {out[col].dtype!r}"

    # Non-NaN integer-valued check for the count channels
    for col in ("flow_directional_asymmetry_w", "unique_daily_active_senders_w"):
        vals = out[col].dropna().to_numpy()
        assert np.allclose(vals, np.round(vals)), \
            f"{col} must carry integer-valued rows; got {vals!r}"


# ── Test 3: index is weekly-monotone Friday-anchored ────────────────────────


def test_output_index_is_friday_anchored(golden_daily_df: pd.DataFrame) -> None:
    """Each output row is indexed on a Friday date, strictly monotone increasing."""
    out = aggregate_daily_to_weekly_vector(golden_daily_df)

    # Index must be a DatetimeIndex
    assert isinstance(out.index, pd.DatetimeIndex), \
        f"Output index must be DatetimeIndex; got {type(out.index)!r}"

    # Each row label must be a Friday
    for ts in out.index:
        assert ts.day_name() == "Friday", \
            f"Row {ts!r} is not a Friday (day={ts.day_name()!r})"

    # Strictly monotone increasing
    diffs = out.index.to_series().diff().dropna()
    assert (diffs == pd.Timedelta(days=7)).all(), \
        f"Friday-week cadence violated: diffs={diffs.tolist()!r}"

    # Golden fixture covers exactly 5 Friday-weeks
    assert list(out.index.date) == [
        pd.Timestamp("2024-10-25").date(),
        pd.Timestamp("2024-11-01").date(),
        pd.Timestamp("2024-11-08").date(),
        pd.Timestamp("2024-11-15").date(),
        pd.Timestamp("2024-11-22").date(),
    ]


# ── Test 4: empty input → empty output ──────────────────────────────────────


def test_empty_input_produces_empty_output() -> None:
    """An empty (0-row) input DataFrame yields an empty (0-row) output."""
    empty = pd.DataFrame(
        {
            "date": pd.Series([], dtype="datetime64[ns]"),
            "copm_mint_usd": pd.Series([], dtype="float64"),
            "copm_burn_usd": pd.Series([], dtype="float64"),
            "copm_unique_minters": pd.Series([], dtype="int64"),
            "ccop_usdt_inflow_usd": pd.Series([], dtype="float64"),
            "ccop_usdt_outflow_usd": pd.Series([], dtype="float64"),
            "ccop_unique_senders": pd.Series([], dtype="float64"),
            "source_query_ids": pd.Series([], dtype="object"),
        }
    )
    out = aggregate_daily_to_weekly_vector(empty)
    assert isinstance(out, pd.DataFrame)
    assert len(out) == 0
    assert tuple(out.columns) == EXPECTED_WEEKLY_COLUMNS


# ── Test 5: single-week fixture: all six channels correctly computed ────────


def test_single_week_all_channels_correct(golden_daily_df: pd.DataFrame) -> None:
    """A single-Friday-week input emits one output row with correct values.

    Uses the equal-flow week (ending 2024-11-08) in isolation.
    """
    mask = (golden_daily_df["date"] >= "2024-11-02") & \
           (golden_daily_df["date"] <= "2024-11-08")
    single = golden_daily_df.loc[mask].reset_index(drop=True)
    assert len(single) == 7

    out = aggregate_daily_to_weekly_vector(single)
    assert len(out) == 1
    assert out.index[0] == pd.Timestamp("2024-11-08")

    row = out.iloc[0]
    assert row["flow_sum_w"] == pytest.approx(700.0, abs=WITNESS_ATOL)
    assert row["flow_var_w"] == pytest.approx(0.0, abs=WITNESS_ATOL)
    assert row["flow_concentration_w"] == pytest.approx(1.0 / 7.0, abs=WITNESS_ATOL)
    assert int(row["flow_directional_asymmetry_w"]) == 7
    assert int(row["unique_daily_active_senders_w"]) == 49
    assert row["flow_max_single_day_w"] == pytest.approx(100.0, abs=WITNESS_ATOL)


# ── Test 6: multi-week fixture — each week computed independently ───────────


def test_multi_week_each_week_independent(golden_daily_df: pd.DataFrame) -> None:
    """Aggregating 5 weeks yields 5 rows whose per-week values are independent.

    In particular, the equal-flow week and the single-spike week (adjacent
    in the fixture) produce their correct values simultaneously with no
    cross-contamination.
    """
    out = aggregate_daily_to_weekly_vector(golden_daily_df)

    # Equal-flow week
    eq = out.loc[pd.Timestamp("2024-11-08")]
    assert eq["flow_concentration_w"] == pytest.approx(1.0 / 7.0, abs=WITNESS_ATOL)
    assert eq["flow_var_w"] == pytest.approx(0.0, abs=WITNESS_ATOL)

    # Single-spike week
    sp = out.loc[pd.Timestamp("2024-11-15")]
    assert sp["flow_concentration_w"] == pytest.approx(1.0, abs=WITNESS_ATOL)
    assert sp["flow_max_single_day_w"] == pytest.approx(700.0, abs=WITNESS_ATOL)

    # The two adjacent weeks must not equal each other.
    assert eq["flow_concentration_w"] != pytest.approx(sp["flow_concentration_w"],
                                                        abs=1e-3)


# ── Test 7: independent-reproduction-witness block (Rev-3.1 CR-B2) ──────────


def test_independent_reproduction_witness_equal_flow_week(
    golden_daily_df: pd.DataFrame,
) -> None:
    """Pin golden-fixture values at 6-decimal tolerance — MANDATORY.

    Rev-3.1 CR-B2 (plan line 324) requires that the six pinned channel
    values be computed BY AN INDEPENDENT PATH — not by
    ``aggregate_daily_to_weekly_vector`` — and then compared against both
    (a) the pinned constants committed BEFORE implementation and
    (b) the implementation's output.

    This guards against silent-test-pass: a test that only checks
    ``agg_output == pinned_constant`` would pass even if BOTH the
    implementation and the pinned constant shared the same bug. By
    reproducing the arithmetic here with raw pandas, the test catches
    a bug in exactly one of the three places (implementation, pinned
    constants, or reproduction logic) rather than zero of them.

    Week under test: equal-flow week ending 2024-11-08 (Sat 2024-11-02 →
    Fri 2024-11-08). Chosen because it has the cleanest analytically-
    verifiable expected values (flow_var_w = 0, flow_concentration_w =
    1/7, flow_sum_w = 700 exactly).
    """
    # ── Independent reproduction path (raw pandas, NOT via the aggregator) ──
    df = golden_daily_df.copy()
    mask = (df["date"] >= "2024-11-02") & (df["date"] <= "2024-11-08")
    wk_df = df.loc[mask].copy()
    assert len(wk_df) == 7, "Week under test must carry 7 daily rows"

    # Daily net_flow — NaN-safe sum over four USD channels.
    daily_net = (
        wk_df["copm_mint_usd"].fillna(0.0)
        + wk_df["copm_burn_usd"].fillna(0.0)
        + wk_df["ccop_usdt_inflow_usd"].fillna(0.0)
        + wk_df["ccop_usdt_outflow_usd"].fillna(0.0)
    ).to_numpy(dtype="float64")

    # Daily directional flow
    daily_dir = (
        (wk_df["copm_mint_usd"].fillna(0.0) - wk_df["copm_burn_usd"].fillna(0.0))
        + (wk_df["ccop_usdt_inflow_usd"].fillna(0.0)
           - wk_df["ccop_usdt_outflow_usd"].fillna(0.0))
    ).to_numpy(dtype="float64")

    # Daily sender count (cCOP NaN → 0)
    daily_senders = (
        wk_df["copm_unique_minters"].astype("float64")
        + wk_df["ccop_unique_senders"].fillna(0.0)
    ).to_numpy(dtype="float64")

    # Six independent one-liners (plan Step-1 instruction):
    witness_flow_sum = float(daily_net.sum())
    witness_flow_var = float(np.var(daily_net, ddof=0))
    abs_daily = np.abs(daily_net)
    witness_flow_concentration = float(
        (abs_daily ** 2).sum() / (abs_daily.sum() ** 2)
    )
    witness_asymmetry = int((daily_dir > 0).sum() - (daily_dir < 0).sum())
    witness_senders = int(daily_senders.sum())
    witness_max_single_day = float(abs_daily.max())

    # ── (a) Reproduction values match the pinned constants ──
    assert witness_flow_sum == pytest.approx(
        PINNED_FLOW_SUM_W, abs=WITNESS_ATOL
    )
    assert witness_flow_var == pytest.approx(
        PINNED_FLOW_VAR_W, abs=WITNESS_ATOL
    )
    assert witness_flow_concentration == pytest.approx(
        PINNED_FLOW_CONCENTRATION_W, abs=WITNESS_ATOL
    )
    assert witness_asymmetry == PINNED_FLOW_DIRECTIONAL_ASYMMETRY_W
    assert witness_senders == PINNED_UNIQUE_DAILY_ACTIVE_SENDERS_W
    assert witness_max_single_day == pytest.approx(
        PINNED_FLOW_MAX_SINGLE_DAY_W, abs=WITNESS_ATOL
    )

    # ── (b) Implementation output matches the reproduction path ──
    out = aggregate_daily_to_weekly_vector(golden_daily_df)
    row = out.loc[PINNED_WEEK]
    assert row["flow_sum_w"] == pytest.approx(witness_flow_sum, abs=WITNESS_ATOL)
    assert row["flow_var_w"] == pytest.approx(witness_flow_var, abs=WITNESS_ATOL)
    assert row["flow_concentration_w"] == pytest.approx(
        witness_flow_concentration, abs=WITNESS_ATOL
    )
    assert int(row["flow_directional_asymmetry_w"]) == witness_asymmetry
    assert int(row["unique_daily_active_senders_w"]) == witness_senders
    assert row["flow_max_single_day_w"] == pytest.approx(
        witness_max_single_day, abs=WITNESS_ATOL
    )


# ── Test 8: flow_concentration_w = 1/7 on 7 equal daily values ──────────────


def test_flow_concentration_one_seventh_when_all_equal(
    golden_daily_df: pd.DataFrame,
) -> None:
    """All 7 days with identical |net_flow| → concentration = 1/7 exactly."""
    out = aggregate_daily_to_weekly_vector(golden_daily_df)
    row = out.loc[pd.Timestamp("2024-11-08")]
    assert row["flow_concentration_w"] == pytest.approx(
        1.0 / 7.0, abs=WITNESS_ATOL
    )


# ── Test 9: flow_concentration_w = 1.0 on single-spike week ─────────────────


def test_flow_concentration_one_on_single_spike_week(
    golden_daily_df: pd.DataFrame,
) -> None:
    """Six zero-flow days + one spike day → concentration = 1.0 exactly."""
    out = aggregate_daily_to_weekly_vector(golden_daily_df)
    row = out.loc[pd.Timestamp("2024-11-15")]
    assert row["flow_concentration_w"] == pytest.approx(1.0, abs=WITNESS_ATOL)


# ── Test 10: directional asymmetry — constructed per-day signs ──────────────


def test_directional_asymmetry_matches_constructed_signs(
    golden_daily_df: pd.DataFrame,
) -> None:
    """Constructed per-day signs give the expected integer count difference.

    Week 2024-11-22 (mixed-sign) has per-day directional signs by design:
      Sat 11-16: dir = +150  (pos)
      Sun 11-17: dir = -150  (neg)
      Mon 11-18: dir =   0   (zero — counted as neither)
      Tue 11-19: dir = +100  (pos)
      Wed 11-20: dir = + 10  (pos)
      Thu 11-21: dir = - 90  (neg)
      Fri 11-22: dir = + 20  (pos)
    Positive days = 4, negative = 2 → asymmetry = 4 - 2 = 2.
    """
    out = aggregate_daily_to_weekly_vector(golden_daily_df)
    row = out.loc[pd.Timestamp("2024-11-22")]
    assert int(row["flow_directional_asymmetry_w"]) == 2


# ── Test 11: pre-2024-10-31 week — cCOP NaN ignored, COPM-only works ────────


def test_pre_ccop_week_copm_only_aggregation(
    golden_daily_df: pd.DataFrame,
) -> None:
    """Pre-cCOP-launch week: cCOP NaN columns ignored; COPM-only valid output.

    Week ending 2024-10-25 spans Sat 2024-10-19 → Fri 2024-10-25; every row
    has ccop_* columns NaN. The aggregator must (a) produce non-NaN values
    on the five non-cCOP-dependent channels, and (b) compute
    ``unique_daily_active_senders_w`` from copm_unique_minters ALONE
    (ccop_unique_senders is NaN → treated as zero).

    Expected:
      Σ copm_unique_minters across 7 days = 3+2+0+5+1+4+2 = 17
    """
    out = aggregate_daily_to_weekly_vector(golden_daily_df)
    row = out.loc[pd.Timestamp("2024-10-25")]

    # All six channels must be non-NaN — the NaN cCOP data must not
    # poison the COPM-only aggregation.
    for col in EXPECTED_WEEKLY_COLUMNS:
        assert not pd.isna(row[col]), \
            f"Pre-cCOP week has NaN in {col}; cCOP-NaN should be treated as 0"

    # COPM-only sender count
    assert int(row["unique_daily_active_senders_w"]) == 17

    # COPM-only flow sum: Σ(mint + burn) over 7 days
    # = (100+20)+(30+50)+(0+0)+(200+10)+(15+45)+(75+25)+(10+90)
    # = 120 + 80 + 0 + 210 + 60 + 100 + 100 = 670
    assert row["flow_sum_w"] == pytest.approx(670.0, abs=WITNESS_ATOL)

    # Directional asymmetry by design = 3 positive - 3 negative = 0
    assert int(row["flow_directional_asymmetry_w"]) == 0


# ── Test 12: determinism — two identical calls yield byte-identical output ──


def test_determinism_two_calls_byte_identical(
    golden_daily_df: pd.DataFrame,
) -> None:
    """Two independent calls on the same input yield equal DataFrames."""
    a = aggregate_daily_to_weekly_vector(golden_daily_df)
    b = aggregate_daily_to_weekly_vector(golden_daily_df)
    pd.testing.assert_frame_equal(a, b, check_exact=True)


# ── Test 13: order-invariance — shuffled daily rows produce same output ─────


def test_order_invariance_on_shuffled_daily_rows(
    golden_daily_df: pd.DataFrame,
) -> None:
    """Shuffling daily-row order then aggregating yields the same weekly result.

    The aggregator must not depend on input ordering beyond its own internal
    sort. We permute rows with a fixed seed to keep the test deterministic.
    """
    rng = np.random.default_rng(42)
    perm = rng.permutation(len(golden_daily_df))
    shuffled = golden_daily_df.iloc[perm].reset_index(drop=True)

    # Sanity: the shuffle actually moved at least one row
    assert not shuffled["date"].equals(golden_daily_df["date"])

    out_sorted = aggregate_daily_to_weekly_vector(golden_daily_df)
    out_shuffled = aggregate_daily_to_weekly_vector(shuffled)

    # The output index is expected to be sorted ascending by the aggregator.
    pd.testing.assert_frame_equal(
        out_sorted.sort_index(), out_shuffled.sort_index(), check_exact=True
    )


# ── Test 14: partial (<7-day) weeks emit NaN on all six channels ────────────


def test_partial_week_emits_nan_on_all_channels(
    golden_daily_df: pd.DataFrame,
) -> None:
    """Weeks with fewer than 7 daily observations emit NaN, not zero-fill.

    Take only the first 4 rows (Sat 10-19 → Tue 10-22) — a 4-day partial
    week. The aggregator must emit one row indexed on Fri 2024-10-25 with
    every channel NaN (explicit NaN-propagation per spec edge-case rules).

    flow_directional_asymmetry_w and unique_daily_active_senders_w are
    integer-valued by type; when the aggregator emits "no valid value"
    for a partial week they must also be NaN (pandas float-carrying
    convention; integer NaN via pd.NA is also acceptable).
    """
    partial = golden_daily_df.iloc[:4].reset_index(drop=True)
    assert len(partial) == 4

    out = aggregate_daily_to_weekly_vector(partial)

    # The single output row must be labelled Fri 2024-10-25
    assert len(out) == 1
    assert out.index[0] == pd.Timestamp("2024-10-25")

    row = out.iloc[0]
    for col in EXPECTED_WEEKLY_COLUMNS:
        assert pd.isna(row[col]), \
            f"Partial-week {col} must be NaN; got {row[col]!r}"
