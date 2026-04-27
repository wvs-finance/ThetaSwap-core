"""Pure loader for the Task-11 real BanRep remittance fixture.

This module implements Task 11 of the Phase-A.0 remittance-surprise
implementation plan. It is a **pure CSV read** — no network access, no
mutable global state — of the committed real-BanRep-derived fixture at
``contracts/data/banrep_remittance_aggregate_monthly.csv``.

Rev-2 real-world constraint (authoritative; see
``contracts/data/banrep_mpr_sources.md`` for full provenance):

  BanRep publishes a single structured worker-remittance time series
  (suameca series id 4150, ``idPlan=REMESAS_TRIMESTRAL``) at **quarterly**
  cadence. No public monthly aggregate-inflow API exists. MPR (Informe de
  Política Monetaria) Excel annexes publish macroeconomic forecast variables
  and a quarterly "C. Ingresos secundarios (transferencias corrientes)" row
  that is *total* current transfers, not a clean remittance series.

  Accordingly the committed CSV carries **quarterly** ``reference_period``
  rows (104 rows, Q1-2000 → Q4-2025 as of the 2026-03-06 snapshot). The
  filename retains ``aggregate_monthly`` for backward compatibility with
  the Task-9 ``cleaning.py`` V1 seam and the Rev-1 spec §4.8 data-contract
  anchor; periodicity-aware downstream handling is Task 13's responsibility.

Purity contract (functional-python skill):
  * Zero side effects; no I/O beyond the single CSV read at the user-supplied
    path.
  * Input validation at each public function's first line only.
  * Free functions; no classes beyond module-level constants.
  * Exceptions are informative — they name the path, column, or row that
    triggered them.

Refresh protocol: see ``contracts/data/banrep_mpr_sources.md`` §
"Future-Maintenance Protocol". There is no programmatic re-pull here —
BanRep's series-id-4150 feed is a snapshot-refresh mechanism, not a
live API with first-print vintages.

Downstream consumption:
  * Task 9's ``cleaning.py`` V1 seam — reads this loader's output to build
    ``CleanedRemittancePanelV1``.
  * Task 10's ``construct_ar1_surprise`` — consumes the
    ``(reference_period, release_date, value)`` shape. Note: this loader
    emits ``mpr_vintage_date`` (not ``release_date``) and ``value_usd``
    (not ``value``); Task 9's seam is responsible for the column-rename
    adapter.
  * Task 12's decision-hash extension — hashes the CSV bytes for
    fingerprinting.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final, Mapping

import numpy as np
import pandas as pd


# ── Module-level contract ────────────────────────────────────────────────────

#: The four schema columns, in their canonical order. Import this tuple
#: instead of re-deriving the schema in downstream consumers.
EXPECTED_COLUMNS: Final[tuple[str, ...]] = (
    "reference_period",
    "value_usd",
    "mpr_vintage_date",
    "source_url",
)

#: Declared pandas dtypes for each column. ``object`` for ``source_url`` is
#: intentional — it accommodates pandas' default CSV-read behavior for
#: string columns across versions <=2.2 without forcing a ``StringDtype``
#: migration that could regress on older CI environments.
EXPECTED_DTYPES: Final[Mapping[str, str]] = {
    "reference_period": "datetime64[ns]",
    "value_usd": "float64",
    "mpr_vintage_date": "datetime64[ns]",
    "source_url": "object",
}

#: Default CSV path. Resolved from this module's location: the file lives
#: at ``contracts/scripts/banrep_remittance_fetcher.py``; the CSV is at
#: ``contracts/data/banrep_remittance_aggregate_monthly.csv``.
#: ``parents[1]`` = ``contracts/``; ``/ "data" / "..."`` = the fixture.
DEFAULT_CSV_PATH: Final[Path] = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "banrep_remittance_aggregate_monthly.csv"
)


# ── Public functions ─────────────────────────────────────────────────────────


def load_banrep_remittance_monthly(
    csv_path: Path | str | None = None,
) -> pd.DataFrame:
    """Load the committed BanRep real-data fixture into a typed DataFrame.

    Parameters
    ----------
    csv_path:
        Optional override for the CSV path. Defaults to
        :data:`DEFAULT_CSV_PATH`. Accepts ``Path``, ``str``, or ``None``.

    Returns
    -------
    pd.DataFrame
        A new DataFrame with columns exactly equal to :data:`EXPECTED_COLUMNS`,
        parsed dtypes per :data:`EXPECTED_DTYPES`, rows sorted by
        ``reference_period`` ascending.

    Raises
    ------
    FileNotFoundError
        If the CSV path does not exist. The message names the absolute path
        and notes that the fixture is manually compiled (not network-fetched).
    ValueError
        On schema violations: missing columns, non-monotone ``reference_period``,
        non-positive ``value_usd``, ``mpr_vintage_date`` preceding
        ``reference_period``, or non-BanRep ``source_url``.
    """
    path = Path(csv_path) if csv_path is not None else DEFAULT_CSV_PATH
    path = path.expanduser().resolve() if path.is_absolute() else path.resolve()

    if not path.is_file():
        raise FileNotFoundError(
            f"BanRep remittance fixture CSV not found at {path}. "
            "This is a manually-compiled Task-11 fixture (no public monthly "
            "API exists for BanRep remittance); see "
            "contracts/data/banrep_mpr_sources.md for provenance and "
            "re-compilation protocol."
        )

    # The CSV header comment lines start with '#'. Pandas' comment= option
    # treats '#' as a comment character globally, which is what we want:
    # header comment lines are skipped; the first non-comment line is the
    # column header.
    df = pd.read_csv(
        path,
        comment="#",
        parse_dates=["reference_period", "mpr_vintage_date"],
        dtype={"value_usd": "float64", "source_url": "object"},
    )

    # Run full-schema validation before returning. This catches corruption
    # that may have been introduced by a manual edit between releases.
    validate_remittance_csv(df)

    return df


def validate_remittance_csv(df: pd.DataFrame) -> None:
    """Validate a loaded DataFrame against the Task-11 schema.

    Checks, in order:
      1. Exactly the four expected columns are present.
      2. ``reference_period`` and ``mpr_vintage_date`` are datetime-like.
      3. ``value_usd`` is a finite-valued float column with all positive values.
      4. ``reference_period`` is strictly increasing (no ties, no inversions).
      5. ``mpr_vintage_date >= reference_period`` row-wise.
      6. ``source_url`` values are strings rooted under a BanRep domain.

    Parameters
    ----------
    df:
        DataFrame to validate. May have any row order at entry; however
        strict-monotone ``reference_period`` is a precondition of
        (4).

    Raises
    ------
    ValueError
        With a diagnostic message naming the first violated invariant.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError(
            f"validate_remittance_csv expected a DataFrame; got {type(df)!r}."
        )

    # (1) Column presence ───────────────────────────────────────────────────
    expected_set = set(EXPECTED_COLUMNS)
    actual_set = set(df.columns)
    missing = expected_set - actual_set
    extra = actual_set - expected_set
    if missing or extra:
        raise ValueError(
            f"Schema column mismatch: missing={sorted(missing)!r}, "
            f"extra={sorted(extra)!r}. Expected exactly {EXPECTED_COLUMNS!r}."
        )

    # (2) Date dtypes ───────────────────────────────────────────────────────
    if not pd.api.types.is_datetime64_any_dtype(df["reference_period"]):
        raise ValueError(
            f"reference_period must be datetime-like; "
            f"got dtype={df['reference_period'].dtype!r}."
        )
    if not pd.api.types.is_datetime64_any_dtype(df["mpr_vintage_date"]):
        raise ValueError(
            f"mpr_vintage_date must be datetime-like; "
            f"got dtype={df['mpr_vintage_date'].dtype!r}."
        )

    # (3) value_usd positivity + finiteness ─────────────────────────────────
    if not pd.api.types.is_float_dtype(df["value_usd"]):
        raise ValueError(
            f"value_usd must be float dtype; got {df['value_usd'].dtype!r}."
        )
    vals = df["value_usd"].to_numpy()
    if not np.isfinite(vals).all():
        bad_idx = np.where(~np.isfinite(vals))[0]
        raise ValueError(
            f"value_usd contains non-finite entries at row(s) "
            f"{bad_idx.tolist()!r}."
        )
    if not (vals > 0).all():
        bad_idx = np.where(vals <= 0)[0]
        raise ValueError(
            f"value_usd must be strictly positive; "
            f"non-positive row(s) {bad_idx.tolist()!r} with value(s) "
            f"{vals[bad_idx].tolist()!r}."
        )

    # (4) Strict-monotone reference_period ──────────────────────────────────
    ts = df["reference_period"]
    diffs = ts.diff().dropna()
    if not (diffs > pd.Timedelta(0)).all():
        bad_positions = diffs[diffs <= pd.Timedelta(0)].index.tolist()
        raise ValueError(
            "reference_period must be strictly increasing (sorted, no ties); "
            f"monotonicity broken at row position(s) {bad_positions!r}."
        )

    # (5) mpr_vintage_date cannot precede reference_period ─────────────────
    ref = df["reference_period"]
    vint = df["mpr_vintage_date"]
    bad_vintage = df.loc[vint < ref]
    if not bad_vintage.empty:
        raise ValueError(
            "mpr_vintage_date precedes reference_period for "
            f"{len(bad_vintage)} row(s) at position(s) "
            f"{bad_vintage.index.tolist()!r}."
        )

    # (6) source_url rooted under a BanRep domain ──────────────────────────
    allowed_prefixes = (
        "https://www.banrep.gov.co/",
        "https://suameca.banrep.gov.co/",
        "https://repositorio.banrep.gov.co/",
    )
    urls = df["source_url"].astype(str)
    bad_url_mask = ~urls.str.startswith(allowed_prefixes)
    if bad_url_mask.any():
        bad_urls = urls[bad_url_mask].unique().tolist()
        raise ValueError(
            f"source_url rows must start with a BanRep domain; "
            f"non-conformant URL(s): {bad_urls!r}."
        )
