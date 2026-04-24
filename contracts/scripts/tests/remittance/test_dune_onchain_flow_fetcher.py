"""TDD tests for the Task-11.A Dune on-chain daily flow fetcher / loader module.

Phase-1.5 Task 11.A of the Rev-3.1 remittance-surprise implementation plan.
These tests are written BEFORE implementation per `feedback_strict_tdd` and
MUST fail on ImportError / FileNotFoundError until both
``contracts/scripts/dune_onchain_flow_fetcher.py`` and
``contracts/data/copm_ccop_daily_flow.csv`` exist.

Rev-3.1 tightened assertions (CR-F1) — with calendar-infeasibility adjustment:
  * Row count ≥ 580 (COPM launch 2024-09-17 → acquisition 2026-04-24 ≈
    585 calendar days). Rev-3.1 prescribed `>= 720` but that threshold
    assumed 24 months of post-launch calendar time which had not elapsed
    as of acquisition — see module-level ``_MIN_ROW_COUNT`` docstring
    for the full calibration note and `contracts/data/dune_onchain_sources.md`
    for the deviation record.
  * At least 500 rows with non-zero ``copm_mint_usd OR ccop_usdt_inflow_usd``
    (bare row-count is satisfiable by zero-padding; the non-zero constraint
    ensures the data is economically load-bearing). This threshold is
    preserved verbatim from Rev-3.1.
  * ``copm_mint_usd`` has non-NaN values spanning COPM-launch → latest with
    no internal NaN gap exceeding 3 consecutive days. COPM on-chain first
    transfer is 2024-09-17 (verified via Dune query #6940691).
  * ``ccop_usdt_inflow_usd`` has non-NaN values spanning cCOP-launch → latest
    with no internal NaN gap exceeding 3 consecutive days. cCOP first
    transfer is 2024-10-31 (verified via Dune query #6940691).

Contract disambiguation (Rev-3.1 RC-B2):
  * cCOP/COPm TOKEN contract: ``0x8a567e2ae79ca692bd748ab832081c45de4041ea``
    — the ERC-20 token (symbol changed cCOP→COPm on 2026-01-25 at SAME address).
  * COPM (Minteo) TOKEN contract: ``0xc92e8fc2947e32f2b574cca9f2f12097a71d5606``
  * Mento BROKER contract (NOT queried for this task):
    ``0x777a8255ca72412f0d706dc03c9d1987306b4cad`` — swap venue, not token.

CSV schema (real on-chain Dune-derived values, committed):
  date                     YYYY-MM-DD UTC block_date (daily)
  copm_mint_usd            USD sum of COPM transfers with from=0x0 (mints)
  copm_burn_usd            USD sum of COPM transfers with to=0x0 (burns)
  copm_unique_minters      Distinct ``to`` addresses on COPM mint events
  ccop_usdt_inflow_usd     USD sum of cCOP/COPm transfers with non-zero ``to``
                           (inflow-to-user side; mints excluded)
  ccop_usdt_outflow_usd    USD sum of cCOP/COPm transfers with non-zero ``from``
                           (outflow-from-user side; burns excluded)
  ccop_unique_senders      Distinct non-zero ``from`` senders on cCOP/COPm
  source_query_ids         Pipe-separated Dune query ID list, e.g.
                           ``6941901|6940691`` (or paste-in URL list on
                           fallback path per PM-F1 Recovery Protocol 1a).

Test design:
  * Tests read the CSV path off the loader's module constants — NOT a
    hard-coded copy.
  * No test opens the network. The loader MUST be a pure CSV read.
  * Determinism test round-trips the loaded DataFrame through a fresh call
    and compares equality on the canonical columns.
  * Per the 3-integration-test silent-test-pass guard: the non-zero row
    count assertion guards against a zero-padded fixture that would pass
    a bare row-count test.

Pre-committed downstream constraint (documented here for completeness,
not enforced at Task 11.A level; see `dune_onchain_sources.md`):
  N = 95 weekly observations anchored at the Feb-2026 Rev-4-panel-end floor
  is the canonical downstream sample size. Task 11.A retains any additional
  rows in the fixture; downstream tasks truncate to N=95.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import pytest

# TDD red-phase imports — MUST fail on ImportError until Task 11.A is
# implemented. Do not silence this with a try/except.
from scripts.dune_onchain_flow_fetcher import (  # noqa: E402
    EXPECTED_COLUMNS,
    EXPECTED_DTYPES,
    DEFAULT_CSV_PATH,
    COPM_LAUNCH_DATE,
    CCOP_LAUNCH_DATE,
    CCOP_COPM_MIGRATION_DATE,
    load_copm_ccop_daily_flow,
    validate_daily_flow_csv,
)


# ── Constants for the test suite ─────────────────────────────────────────────

#: Minimum row count per Rev-3.1 CR-F1.
#:
#: Rev-3.1 plan prescribed `>= 720` (24 months × 30 days). At acquisition
#: time (2026-04-23), COPM launched only 2024-09-17 (19 months prior per
#: Dune query #6940691 verified first_seen), so `>= 720` was calendar-
#: infeasible: 2024-09-17 → 2026-04-24 = 585 calendar days. Satisfying
#: `>= 720` would require zero-padding to a synthetic pre-launch window,
#: which CR-F1 explicitly forbids (the non-zero check below is the anti-
#: zero-pad guard).
#:
#: Adjusted threshold: `>= 580` (the COPM-launch-anchored calendar floor,
#: allowing small sampling-time variance). The 500-non-zero assertion
#: (`_MIN_NONZERO_ROWS`) is preserved as written; it is the economic-
#: load-bearing check and passes comfortably at 533 non-zero rows.
#:
#: Deviation from Rev-3.1 documented at
#: `contracts/data/dune_onchain_sources.md` § "Deviations from Rev-3.1 Plan".
_MIN_ROW_COUNT: Final[int] = 580

#: Minimum count of rows with non-zero economic signal per Rev-3.1 CR-F1.
#: Guards against the silent-test-pass pattern where a fixture passes
#: ``_MIN_ROW_COUNT`` via zero-padding.
_MIN_NONZERO_ROWS: Final[int] = 500

#: Maximum allowed NaN-gap in consecutive days within a non-NaN window.
#: Per Rev-3.1 CR-F1: "no internal NaN gaps exceeding 3 consecutive days".
_MAX_NAN_GAP_DAYS: Final[int] = 3


# ── Schema-level contract tests ──────────────────────────────────────────────


def test_expected_columns_is_exact_eight_tuple() -> None:
    """``EXPECTED_COLUMNS`` must declare the 8 Task-11.A contract columns.

    Order-sensitive. Downstream consumers (Task 11.B weekly aggregation
    module) import this constant rather than re-deriving the schema.
    """
    assert EXPECTED_COLUMNS == (
        "date",
        "copm_mint_usd",
        "copm_burn_usd",
        "copm_unique_minters",
        "ccop_usdt_inflow_usd",
        "ccop_usdt_outflow_usd",
        "ccop_unique_senders",
        "source_query_ids",
    ), (
        f"EXPECTED_COLUMNS drift detected: got {EXPECTED_COLUMNS!r}. "
        "The Task-11.A contract requires exactly these 8 columns in this "
        "order."
    )


def test_expected_dtypes_declares_all_columns() -> None:
    """``EXPECTED_DTYPES`` must map every column to a pandas dtype."""
    assert set(EXPECTED_DTYPES.keys()) == set(EXPECTED_COLUMNS), (
        f"EXPECTED_DTYPES keys {set(EXPECTED_DTYPES.keys())!r} do not match "
        f"EXPECTED_COLUMNS {set(EXPECTED_COLUMNS)!r}."
    )


def test_default_csv_path_points_at_data_directory() -> None:
    """``DEFAULT_CSV_PATH`` must resolve to contracts/data/copm_ccop_daily_flow.csv."""
    p = Path(DEFAULT_CSV_PATH).resolve()
    assert p.parent.name == "data", (
        f"DEFAULT_CSV_PATH parent is {p.parent.name!r}, expected 'data'."
    )
    assert p.name == "copm_ccop_daily_flow.csv", (
        f"DEFAULT_CSV_PATH filename drift: {p.name!r}."
    )


def test_launch_date_constants_match_on_chain_ground_truth() -> None:
    """Launch-date constants must match Dune query #6940691 verified values.

    Per Rev-3.1 schema verification (logged in contracts/data/dune_onchain_sources.md):
      * COPM (Minteo) first_seen: 2024-09-17 19:54:27 UTC
      * cCOP first_seen: 2024-10-31 16:35:48 UTC
      * cCOP→COPm symbol migration: 2026-01-25 (per corpus line-163)

    These constants are load-bearing for the per-series NaN-gap test below;
    drift here invalidates the "no NaN gap >3 consecutive days within the
    valid window" check.
    """
    assert COPM_LAUNCH_DATE == pd.Timestamp("2024-09-17"), (
        f"COPM_LAUNCH_DATE drift: got {COPM_LAUNCH_DATE!r}"
    )
    assert CCOP_LAUNCH_DATE == pd.Timestamp("2024-10-31"), (
        f"CCOP_LAUNCH_DATE drift: got {CCOP_LAUNCH_DATE!r}"
    )
    assert CCOP_COPM_MIGRATION_DATE == pd.Timestamp("2026-01-25"), (
        f"CCOP_COPM_MIGRATION_DATE drift: got {CCOP_COPM_MIGRATION_DATE!r}"
    )


# ── Loader behavior tests ────────────────────────────────────────────────────


def test_load_returns_dataframe_with_expected_columns() -> None:
    """The loader returns a DataFrame whose columns exactly match the schema."""
    df = load_copm_ccop_daily_flow()
    assert isinstance(df, pd.DataFrame)
    assert tuple(df.columns) == EXPECTED_COLUMNS


def test_load_returns_expected_dtypes() -> None:
    """Each column must have the declared dtype after load."""
    df = load_copm_ccop_daily_flow()
    assert pd.api.types.is_datetime64_any_dtype(df["date"]), (
        f"date dtype={df['date'].dtype!r}"
    )
    for col in (
        "copm_mint_usd",
        "copm_burn_usd",
        "ccop_usdt_inflow_usd",
        "ccop_usdt_outflow_usd",
    ):
        assert pd.api.types.is_float_dtype(df[col]), (
            f"{col} dtype={df[col].dtype!r} (expected float)"
        )
    for col in ("copm_unique_minters", "ccop_unique_senders"):
        assert pd.api.types.is_integer_dtype(df[col]) or pd.api.types.is_float_dtype(df[col]), (
            f"{col} dtype={df[col].dtype!r} (expected int/float)"
        )
    assert (
        pd.api.types.is_object_dtype(df["source_query_ids"])
        or pd.api.types.is_string_dtype(df["source_query_ids"])
    ), f"source_query_ids dtype={df['source_query_ids'].dtype!r}"


def test_date_column_is_daily_monotone_increasing() -> None:
    """The ``date`` column must be strictly monotone increasing at daily cadence."""
    df = load_copm_ccop_daily_flow()
    dates = pd.to_datetime(df["date"])
    diffs = dates.diff().dropna()
    assert (diffs > pd.Timedelta(0)).all(), (
        "date column is not strictly monotone increasing."
    )
    # Daily cadence: all diffs should be exactly 1 day.
    assert (diffs == pd.Timedelta(days=1)).all(), (
        f"date column has non-daily gaps: "
        f"unique diffs = {diffs.unique().tolist()!r}"
    )


def test_row_count_at_least_calendar_floor() -> None:
    """Per CR-F1 (calendar-adjusted): row count ≥ 580.

    Rev-3.1 originally prescribed `>= 720`. Because COPM launched
    2024-09-17 (verified via Dune query #6940691) and acquisition
    ran at 2026-04-24, only 585 calendar days have elapsed —
    honoring `>= 720` would require zero-padding to a synthetic
    pre-launch window, which CR-F1 explicitly forbids. Threshold
    adjusted to the COPM-launch-anchored calendar floor per
    ``_MIN_ROW_COUNT`` docstring.

    Bare row-count is necessary but NOT sufficient — see
    ``test_at_least_500_rows_have_nonzero_signal`` below.
    """
    df = load_copm_ccop_daily_flow()
    assert len(df) >= _MIN_ROW_COUNT, (
        f"Row count {len(df)} below minimum {_MIN_ROW_COUNT}. "
        f"Date range: {df['date'].min()} → {df['date'].max()}."
    )


def test_at_least_500_rows_have_nonzero_signal() -> None:
    """Per CR-F1 economic-load-bearing assertion.

    At least 500 rows must have non-zero ``copm_mint_usd OR
    ccop_usdt_inflow_usd``. Guards against the silent-test-pass pattern
    where a fixture is zero-padded to inflate row-count.
    """
    df = load_copm_ccop_daily_flow()
    nonzero_mask = (df["copm_mint_usd"].fillna(0.0) > 0.0) | (
        df["ccop_usdt_inflow_usd"].fillna(0.0) > 0.0
    )
    nonzero_count = int(nonzero_mask.sum())
    assert nonzero_count >= _MIN_NONZERO_ROWS, (
        f"Only {nonzero_count} rows have non-zero economic signal "
        f"(threshold {_MIN_NONZERO_ROWS}). This is the CR-F1 "
        "silent-test-pass guard against zero-padded fixtures."
    )


def test_copm_mint_usd_spans_launch_to_latest_without_nan_gaps() -> None:
    """``copm_mint_usd`` must be non-NaN within COPM_LAUNCH_DATE → latest.

    Per CR-F1: no internal NaN gap exceeding 3 consecutive days. This
    guards against silent data dropout between Dune query executions or
    mis-joined daily sub-queries.
    """
    df = load_copm_ccop_daily_flow()
    dates = pd.to_datetime(df["date"])
    latest = dates.max()

    in_window = (dates >= COPM_LAUNCH_DATE) & (dates <= latest)
    window_values = df.loc[in_window, "copm_mint_usd"]

    assert window_values.notna().any(), (
        "copm_mint_usd is fully NaN within COPM window "
        f"[{COPM_LAUNCH_DATE} .. {latest}]."
    )

    nan_mask = window_values.isna().to_numpy()
    max_gap = _longest_run(nan_mask)
    assert max_gap <= _MAX_NAN_GAP_DAYS, (
        f"copm_mint_usd has a {max_gap}-day consecutive NaN gap in "
        f"[{COPM_LAUNCH_DATE} .. {latest}] (max allowed: {_MAX_NAN_GAP_DAYS})."
    )


def test_ccop_usdt_inflow_usd_spans_launch_to_latest_without_nan_gaps() -> None:
    """``ccop_usdt_inflow_usd`` must be non-NaN within cCOP launch → latest.

    Per CR-F1: no internal NaN gap exceeding 3 consecutive days.
    """
    df = load_copm_ccop_daily_flow()
    dates = pd.to_datetime(df["date"])
    latest = dates.max()

    in_window = (dates >= CCOP_LAUNCH_DATE) & (dates <= latest)
    window_values = df.loc[in_window, "ccop_usdt_inflow_usd"]

    assert window_values.notna().any(), (
        "ccop_usdt_inflow_usd is fully NaN within cCOP window "
        f"[{CCOP_LAUNCH_DATE} .. {latest}]."
    )

    nan_mask = window_values.isna().to_numpy()
    max_gap = _longest_run(nan_mask)
    assert max_gap <= _MAX_NAN_GAP_DAYS, (
        f"ccop_usdt_inflow_usd has a {max_gap}-day consecutive NaN gap in "
        f"[{CCOP_LAUNCH_DATE} .. {latest}] (max allowed: {_MAX_NAN_GAP_DAYS})."
    )


def test_pre_ccop_launch_ccop_columns_are_nan() -> None:
    """cCOP-column values before CCOP_LAUNCH_DATE must be NaN.

    cCOP launched 2024-10-31; any value for rows dated earlier than that
    is either fabricated or mis-joined. This asserts the pre-launch NaN
    discipline called out in the Step-1 test plan.
    """
    df = load_copm_ccop_daily_flow()
    dates = pd.to_datetime(df["date"])
    pre_launch = dates < CCOP_LAUNCH_DATE
    if pre_launch.any():
        pre_rows = df.loc[pre_launch]
        for col in (
            "ccop_usdt_inflow_usd",
            "ccop_usdt_outflow_usd",
        ):
            assert pre_rows[col].isna().all(), (
                f"{col} has non-NaN value(s) before cCOP launch "
                f"({CCOP_LAUNCH_DATE.date()}): "
                f"{pre_rows.loc[~pre_rows[col].isna(), ['date', col]].to_dict(orient='records')!r}"
            )


def test_usd_values_are_non_negative_where_present() -> None:
    """Where not NaN, all ``*_usd`` columns must be >= 0 (no negative volumes)."""
    df = load_copm_ccop_daily_flow()
    for col in (
        "copm_mint_usd",
        "copm_burn_usd",
        "ccop_usdt_inflow_usd",
        "ccop_usdt_outflow_usd",
    ):
        vals = df[col].dropna().to_numpy()
        assert (vals >= 0.0).all(), (
            f"{col} has negative values: "
            f"{vals[vals < 0.0].tolist()!r}"
        )


def test_source_query_ids_are_non_empty_strings() -> None:
    """Every row's ``source_query_ids`` must be a non-empty string.

    Provenance non-emptiness is a hard requirement — no row may lack
    attribution. Accepts pipe-separated Dune query IDs OR pipe-separated
    paste-in URLs (per PM-F1 Recovery Protocol 1a).
    """
    df = load_copm_ccop_daily_flow()
    urls = df["source_query_ids"].astype(str)
    assert (urls.str.len() > 0).all(), (
        "source_query_ids has empty/whitespace-only rows at positions "
        f"{df.index[urls.str.len() == 0].tolist()!r}"
    )


def test_loader_is_deterministic() -> None:
    """Calling the loader twice must produce byte-identical frames."""
    df1 = load_copm_ccop_daily_flow()
    df2 = load_copm_ccop_daily_flow()
    pd.testing.assert_frame_equal(df1, df2)


def test_loader_raises_filenotfound_on_missing_csv(tmp_path: Path) -> None:
    """``load_copm_ccop_daily_flow(missing_path)`` must raise FileNotFoundError."""
    missing = tmp_path / "nonexistent_flow.csv"
    assert not missing.exists()
    with pytest.raises(FileNotFoundError) as excinfo:
        load_copm_ccop_daily_flow(missing)
    # The error message must name the path so operators can diagnose quickly.
    assert str(missing) in str(excinfo.value), (
        f"FileNotFoundError message must name the missing path; got {excinfo.value!r}"
    )


def test_validator_rejects_dataframe_with_missing_columns() -> None:
    """``validate_daily_flow_csv`` must raise ValueError on a bad schema."""
    bad = pd.DataFrame({"date": [pd.Timestamp("2024-10-31")]})
    with pytest.raises(ValueError):
        validate_daily_flow_csv(bad)


# ── Test helpers ─────────────────────────────────────────────────────────────


def _longest_run(mask: "np.ndarray") -> int:
    """Return the length of the longest run of ``True`` values in a bool array.

    Inline re-implementation (not imported from the module under test)
    per the silent-test-pass guard doctrine: test helpers must not
    share code with the implementation.
    """
    if mask.size == 0:
        return 0
    max_run = 0
    current = 0
    for flag in mask:
        if flag:
            current += 1
            if current > max_run:
                max_run = current
        else:
            current = 0
    return max_run
