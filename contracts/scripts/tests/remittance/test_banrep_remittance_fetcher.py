"""TDD tests for the Task-11 BanRep remittance fetcher / loader module.

Phase-A.0 Task 11 of the remittance-surprise implementation plan. These tests
are written BEFORE implementation per ``feedback_strict_tdd`` and MUST fail on
ImportError / FileNotFoundError until both
``contracts/scripts/banrep_remittance_fetcher.py`` and
``contracts/data/banrep_remittance_aggregate_monthly.csv`` exist.

Scope (pure loader; no network I/O at test time):
  * ``load_banrep_remittance_monthly(csv_path=None) -> pd.DataFrame`` — pure
    read of the committed real-BanRep-derived CSV. Default ``csv_path`` points
    at ``contracts/data/banrep_remittance_aggregate_monthly.csv``. Raises
    ``FileNotFoundError`` if the CSV is missing; ``ValueError`` on schema
    violation.
  * ``validate_remittance_csv(df) -> None`` — pure validator; raises
    ``ValueError`` with a diagnostic message on invalid data.
  * Module-level constants documenting expected schema.

Rev-2 real-world constraint (honestly acknowledged in this test file):
  BanRep's ONLY authoritative remittance series published via its economic
  statistics portal (suameca.banrep.gov.co) is the **quarterly** series
  ``Ingresos de Remesas de trabajadores`` (idMenu=4150, idPlan=REMESAS_TRIMESTRAL,
  descripcionPeriodicidad=Trimestral). No monthly aggregate inflow series is
  published publicly. Accordingly, ``reference_period`` rows in the committed
  CSV carry QUARTER-END dates (YYYY-03-31, YYYY-06-30, YYYY-09-30, YYYY-12-31).
  The sanity threshold (>= 12 observations) is therefore "at least 12 periods
  = 3+ years of quarterly data," which the real BanRep series comfortably
  exceeds (104 quarters, Q1-2000 through Q4-2025).

  The CSV filename retains ``aggregate_monthly`` (as specified by the Task-11
  protocol and the Rev-1 spec §4.8 data-contract anchor) for backward
  compatibility with the ``cleaning.py`` V1 seam (Task 9). Tasks 12-15 are
  responsible for periodicity-aware downstream handling (or documented
  placeholder paths, per Task 14 Step-0 pre-flight).

CSV schema (real BanRep values, committed):
  reference_period   YYYY-MM-DD quarter-end date (Period, ISO 8601)
  value_usd          USD millions, float (2 decimals, from BanRep API)
  mpr_vintage_date   YYYY-MM-DD ``fechaUltimoCargue`` snapshot date
  source_url         str beginning with ``https://www.banrep.gov.co/`` or
                     the sibling ``https://suameca.banrep.gov.co/``

Test design:
  * Tests read the CSV path off the loader's module constants — NOT a
    hard-coded copy — to stay resilient if the loader resolves a different
    path for future relocations.
  * No test opens the network. The loader MUST be a pure CSV read.
  * Determinism test round-trips the loaded DataFrame through a fresh call
    and compares byte-identical equality on the canonical columns.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import pytest

# TDD red-phase imports — MUST fail on ImportError until Task 11 is
# implemented. Do not silence this with a try/except.
from scripts.banrep_remittance_fetcher import (  # noqa: E402
    EXPECTED_COLUMNS,
    EXPECTED_DTYPES,
    DEFAULT_CSV_PATH,
    load_banrep_remittance_monthly,
    validate_remittance_csv,
)


# ── Constants for the test suite ─────────────────────────────────────────────

#: Minimum number of reference_period observations the fixture must carry.
#: Derived from the MDES-style AR(1) pre-sample floor in
#: ``surprise_constructor._MIN_PRE_SAMPLE_MONTHS`` (12). Because BanRep
#: publishes quarterly (not monthly — see module docstring), this threshold
#: translates to 12 quarterly observations = 3 years; the real series carries
#: 104 quarters and passes trivially.
_MIN_OBSERVATIONS: Final[int] = 12

#: All URLs compiled for the fixture must live under the real BanRep domain.
#: The suameca subdomain is the official statistics portal; the main
#: banrep.gov.co domain hosts MPR PDFs and methodological documents.
_ALLOWED_URL_PREFIXES: Final[tuple[str, ...]] = (
    "https://www.banrep.gov.co/",
    "https://suameca.banrep.gov.co/",
    "https://repositorio.banrep.gov.co/",
)


# ── Schema-level contract tests ──────────────────────────────────────────────


def test_expected_columns_is_exact_four_tuple() -> None:
    """``EXPECTED_COLUMNS`` must declare the four Task-11 contract columns.

    The loader's public contract is pinned at the module level so downstream
    consumers (Task 15 panel integration + Rev-4 decision-hash extension in
    Task 12) can import it without re-deriving the schema.
    """
    assert EXPECTED_COLUMNS == (
        "reference_period",
        "value_usd",
        "mpr_vintage_date",
        "source_url",
    ), (
        f"EXPECTED_COLUMNS drift detected: got {EXPECTED_COLUMNS!r}. "
        "The Task-11 contract requires exactly these four columns in this "
        "order."
    )


def test_expected_dtypes_declares_all_four_columns() -> None:
    """``EXPECTED_DTYPES`` must map every column to a pandas dtype."""
    assert set(EXPECTED_DTYPES.keys()) == set(EXPECTED_COLUMNS), (
        f"EXPECTED_DTYPES keys {set(EXPECTED_DTYPES.keys())!r} do not match "
        f"EXPECTED_COLUMNS {set(EXPECTED_COLUMNS)!r}."
    )


def test_default_csv_path_points_at_data_directory() -> None:
    """``DEFAULT_CSV_PATH`` must resolve to contracts/data/..."""
    p = Path(DEFAULT_CSV_PATH).resolve()
    # parents[2] from contracts/data/banrep_remittance_aggregate_monthly.csv
    # is contracts/, whose sibling "data" directory should contain us.
    assert p.parent.name == "data", (
        f"DEFAULT_CSV_PATH parent is {p.parent.name!r}, expected 'data'."
    )
    assert p.name == "banrep_remittance_aggregate_monthly.csv", (
        f"DEFAULT_CSV_PATH filename drift: {p.name!r}."
    )


# ── Loader behavior tests ────────────────────────────────────────────────────


def test_load_returns_dataframe_with_expected_columns() -> None:
    """The loader returns a DataFrame whose columns exactly match the schema.

    Asserts order-sensitive equality so the test catches any accidental
    column re-ordering during a future refactor.
    """
    df = load_banrep_remittance_monthly()
    assert isinstance(df, pd.DataFrame)
    assert tuple(df.columns) == EXPECTED_COLUMNS


def test_load_returns_expected_dtypes() -> None:
    """Each column must have the declared dtype after load.

    Date columns are parsed as ``datetime64[ns]`` (pandas default for
    ``parse_dates=`` behavior); ``value_usd`` must be float64; ``source_url``
    must be pandas string dtype or object (we accept either for forward
    compatibility with pandas ``StringDtype`` migration).
    """
    df = load_banrep_remittance_monthly()
    # reference_period + mpr_vintage_date must be datetime-like
    assert pd.api.types.is_datetime64_any_dtype(df["reference_period"]), (
        f"reference_period dtype={df['reference_period'].dtype!r}"
    )
    assert pd.api.types.is_datetime64_any_dtype(df["mpr_vintage_date"]), (
        f"mpr_vintage_date dtype={df['mpr_vintage_date'].dtype!r}"
    )
    # value_usd must be floating
    assert pd.api.types.is_float_dtype(df["value_usd"]), (
        f"value_usd dtype={df['value_usd'].dtype!r}"
    )
    # source_url must be string-like (object or pandas StringDtype)
    assert (
        pd.api.types.is_object_dtype(df["source_url"])
        or pd.api.types.is_string_dtype(df["source_url"])
    ), f"source_url dtype={df['source_url'].dtype!r}"


def test_reference_period_values_are_period_end_dates() -> None:
    """Every ``reference_period`` must fall on a month-end day.

    BanRep's quarterly series emits values with reference_period fixed on
    the quarter-end calendar day (2000-03-31, 2000-06-30, 2000-09-30,
    2000-12-31, ...). This test accepts any period-end date so the fixture
    can evolve (e.g., if a future BanRep publication adds monthly granularity,
    the test need not be relaxed).
    """
    df = load_banrep_remittance_monthly()
    ts = pd.to_datetime(df["reference_period"])
    # Month-end: the day after must be the 1st of the following month.
    next_day = ts + pd.Timedelta(days=1)
    assert (next_day.dt.day == 1).all(), (
        "Some reference_period rows are not month-end dates. "
        f"Offenders: {df.loc[next_day.dt.day != 1, 'reference_period'].tolist()!r}"
    )


def test_reference_period_is_sorted_and_strictly_increasing() -> None:
    """After load, rows must be in strictly increasing reference_period order.

    Strict monotonicity (not merely non-decreasing) rules out duplicate
    reference periods, which would corrupt the AR(1) fit downstream in
    ``construct_ar1_surprise``. Re-loading the CSV should not require a sort.
    """
    df = load_banrep_remittance_monthly()
    ts = pd.to_datetime(df["reference_period"])
    diffs = ts.diff().dropna()
    assert (diffs > pd.Timedelta(0)).all(), (
        "reference_period is not strictly increasing. "
        f"Non-positive diffs at indices: {diffs[diffs <= pd.Timedelta(0)].index.tolist()!r}"
    )


def test_fixture_has_at_least_twelve_observations() -> None:
    """Row count >= 12. See module docstring: quarterly cadence means this
    equals "at least 3 years of quarterly data"; the real BanRep 4150 series
    carries 104 quarters (2000-Q1 through 2025-Q4) and passes trivially.
    """
    df = load_banrep_remittance_monthly()
    assert len(df) >= _MIN_OBSERVATIONS, (
        f"Fixture has only {len(df)} rows; AR(1) pre-sample floor is "
        f"{_MIN_OBSERVATIONS}."
    )


def test_value_usd_is_all_positive_finite() -> None:
    """No zero, negative, NaN, or inf values — remittance inflows are
    positive magnitudes by economic definition.
    """
    df = load_banrep_remittance_monthly()
    vals = df["value_usd"].to_numpy()
    assert np.isfinite(vals).all(), "Non-finite value_usd present."
    assert (vals > 0).all(), (
        f"Non-positive value_usd present. Min={vals.min()!r}."
    )


def test_mpr_vintage_date_ge_reference_period() -> None:
    """A BanRep release cannot occur before the month it documents.

    This rules out accidentally swapping the two date columns in the CSV
    — a high-consequence bug for the Rev-1 spec §4.8 vintage-discipline
    contract consumed by ``surprise_constructor.construct_ar1_surprise``.
    """
    df = load_banrep_remittance_monthly()
    ref = pd.to_datetime(df["reference_period"])
    vint = pd.to_datetime(df["mpr_vintage_date"])
    violations = df.loc[vint < ref]
    assert violations.empty, (
        "mpr_vintage_date precedes reference_period for "
        f"{len(violations)} row(s): "
        f"{violations[['reference_period', 'mpr_vintage_date']].to_dict('records')!r}"
    )


def test_source_url_starts_with_banrep_domain() -> None:
    """Every source_url must be rooted under a real BanRep domain.

    Catches accidental fabrication or silent migration to a third-party
    mirror. Accepts www.banrep.gov.co (main site), suameca.banrep.gov.co
    (statistics portal), and repositorio.banrep.gov.co (institutional PDF
    repository).
    """
    df = load_banrep_remittance_monthly()
    urls = df["source_url"].astype(str)
    bad = urls[~urls.str.startswith(_ALLOWED_URL_PREFIXES)]
    assert bad.empty, (
        f"Non-BanRep source_url(s) found: {bad.unique().tolist()!r}"
    )


def test_load_is_deterministic_across_two_calls() -> None:
    """Two consecutive loads of the CSV must yield identical DataFrames.

    The loader is a pure read; no hidden state should leak between calls
    (e.g., a caching layer that mutates on second invocation, or parsing
    that depends on locale). ``pd.testing.assert_frame_equal`` with default
    ``check_exact=True`` on numeric columns gives byte-identical semantics.
    """
    df1 = load_banrep_remittance_monthly()
    df2 = load_banrep_remittance_monthly()
    pd.testing.assert_frame_equal(df1, df2, check_exact=True)


# ── Error-path tests ─────────────────────────────────────────────────────────


def test_load_raises_file_not_found_on_missing_path(tmp_path: Path) -> None:
    """Missing CSV path must raise ``FileNotFoundError`` with a diagnostic.

    The error message should name the missing path (for operator debugging)
    and mention the protocol that the CSV is a manually-compiled fixture
    (not a network call).
    """
    missing = tmp_path / "no_such_file.csv"
    with pytest.raises(FileNotFoundError) as excinfo:
        load_banrep_remittance_monthly(missing)
    assert str(missing) in str(excinfo.value), (
        f"Exception message {excinfo.value!r} does not mention path."
    )


def test_load_raises_value_error_on_missing_column(tmp_path: Path) -> None:
    """A CSV missing one of the four required columns must raise ``ValueError``.

    This catches partial-schema corruption (e.g., a commit that accidentally
    drops the ``source_url`` column, which would break provenance tracking).
    """
    bad_csv = tmp_path / "bad.csv"
    # Deliberately omit source_url
    bad_csv.write_text(
        "reference_period,value_usd,mpr_vintage_date\n"
        "2023-01-31,814.3,2023-04-28\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError) as excinfo:
        load_banrep_remittance_monthly(bad_csv)
    msg = str(excinfo.value).lower()
    assert "source_url" in msg or "column" in msg, (
        f"ValueError message does not diagnose the missing column: "
        f"{excinfo.value!r}"
    )


def test_load_raises_value_error_on_non_monotone_reference_period(
    tmp_path: Path,
) -> None:
    """A CSV with duplicated or out-of-order reference_period must fail fast."""
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text(
        "reference_period,value_usd,mpr_vintage_date,source_url\n"
        "2023-06-30,900.0,2023-08-15,https://www.banrep.gov.co/x\n"
        "2023-03-31,800.0,2023-05-15,https://www.banrep.gov.co/x\n",  # reversed
        encoding="utf-8",
    )
    with pytest.raises(ValueError) as excinfo:
        load_banrep_remittance_monthly(bad_csv)
    assert "monoton" in str(excinfo.value).lower() or "order" in str(
        excinfo.value
    ).lower(), (
        f"ValueError message does not diagnose the ordering issue: "
        f"{excinfo.value!r}"
    )


def test_validate_accepts_a_loaded_frame() -> None:
    """``validate_remittance_csv`` must accept the canonical loaded frame."""
    df = load_banrep_remittance_monthly()
    # Should not raise.
    validate_remittance_csv(df)


def test_validate_rejects_negative_value_usd() -> None:
    """The validator must catch negative remittance inflows."""
    df = load_banrep_remittance_monthly().copy()
    df.loc[df.index[0], "value_usd"] = -1.0
    with pytest.raises(ValueError) as excinfo:
        validate_remittance_csv(df)
    assert "value_usd" in str(excinfo.value) or "positive" in str(
        excinfo.value
    ).lower(), f"Validator message does not diagnose negative value: {excinfo.value!r}"
