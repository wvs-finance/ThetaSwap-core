"""Pure loader + validator for the Task-11.A on-chain flow fixture.

Phase-1.5 Task 11.A of the Rev-3.1 remittance-surprise implementation plan.
This module implements a **pure CSV read** — no network access, no mutable
global state — of the real-on-chain-derived fixture at
``contracts/data/copm_ccop_daily_flow.csv``.

Provenance (authoritative; see ``contracts/data/dune_onchain_sources.md``):

  The CSV is populated from Celo-chain transfers emitted by the two
  Colombian peso stablecoin token contracts on Celo. Daily aggregation is
  produced by Dune query #7366593 against the spell
  ``stablecoins_multichain.transfers``, filtering to ``blockchain='celo'``
  and ``currency='COP'`` and the two token addresses below. Acquisition ran
  2026-04-24 via the Dune MCP (execution ID ``01KPYR8NBKG4XV0V2VH55XJQ5F``,
  4.16 execution credits). Calendar index is forward-filled to daily from
  2024-09-17 onward; missing-transfer days are zero-filled in USD/count
  columns. Pre-cCOP-launch rows (dates < 2024-10-31) carry NaN in cCOP
  columns by contract.

Contract disambiguation (Rev-3.1 RC-B2):
  * ``COPM_TOKEN_ADDRESS``    = ``0xc92e8fc2947e32f2b574cca9f2f12097a71d5606``
    COPM by Minteo. ERC-20 token on Celo. First on-chain transfer
    2024-09-17 19:54 UTC (verified via Dune query #6940691).
  * ``CCOP_TOKEN_ADDRESS``    = ``0x8a567e2ae79ca692bd748ab832081c45de4041ea``
    Mento cCOP / COPm. Single ERC-20 contract; the symbol was renamed
    cCOP → COPm at 2026-01-25 (corpus line-163 canonical per Rev-3.1
    F-3.1-2 footnote). First on-chain transfer 2024-10-31 16:35 UTC.
  * ``MENTO_BROKER_ADDRESS``  = ``0x777a8255ca72412f0d706dc03c9d1987306b4cad``
    Mento protocol broker (swap venue, NOT the token). Emits swap-level
    events, not transfer-level events. NOT queried for this task;
    constant retained here so the disambiguation is self-documenting
    for downstream readers.

Mint/burn convention:
  * A **mint** transfer has ``from = 0x0000000000000000000000000000000000000000``.
  * A **burn** transfer has ``to   = 0x0000000000000000000000000000000000000000``.

Semantics of the four USD columns:
  * ``copm_mint_usd``           — sum of ``amount_usd`` for COPM transfers
                                    with ``from = 0x0`` (mint inflows to the
                                    COPM supply).
  * ``copm_burn_usd``           — sum of ``amount_usd`` for COPM transfers
                                    with ``to   = 0x0`` (burn outflows from
                                    the COPM supply).
  * ``ccop_usdt_inflow_usd``    — sum of ``amount_usd`` for cCOP/COPm
                                    transfers with non-zero ``to`` (inflow-
                                    to-user side; mints excluded).
  * ``ccop_usdt_outflow_usd``   — sum of ``amount_usd`` for cCOP/COPm
                                    transfers with non-zero ``from`` (outflow-
                                    from-user side; mints excluded).

The "usdt" phrase in the cCOP column names is inherited from the Rev-3.1
plan schema nomenclature; the data source is the Celo stablecoins multichain
transfer feed, not a direct cCOP↔USDT swap ledger. Downstream consumers
that need swap-venue data (Task 11.B rich-aggregation) should read from
Mento broker events (Dune query #6939814) rather than this transfer-level
fixture.

Purity contract (functional-python skill):
  * Zero side effects; no I/O beyond the single CSV read at the user-
    supplied path.
  * Input validation at each public function's first line only.
  * Free functions; no classes beyond module-level constants.
  * Exceptions name the path, column, or row that triggered them.

Pre-committed downstream constraint (RC-F3):
  Downstream Task 11.B aggregates this daily fixture to weekly observations.
  The pre-committed analytical sample size is **N = 95 weekly observations**
  anchored at the Feb-2026 Rev-4-panel-end floor. If the daily fixture
  yields more weekly-equivalent rows, the excess is retained in the daily
  CSV; downstream sensitivity tests truncate to N=95. Task 11.A does NOT
  enforce N=95 directly — it is a downstream concern recorded here for
  provenance completeness.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final, Mapping

import numpy as np
import pandas as pd


# ── Module-level contract ────────────────────────────────────────────────────

#: The eight schema columns, in their canonical order. Import this tuple
#: rather than re-deriving the schema in downstream consumers.
EXPECTED_COLUMNS: Final[tuple[str, ...]] = (
    "date",
    "copm_mint_usd",
    "copm_burn_usd",
    "copm_unique_minters",
    "ccop_usdt_inflow_usd",
    "ccop_usdt_outflow_usd",
    "ccop_unique_senders",
    "source_query_ids",
)

#: Declared pandas dtypes for each column.
#:
#: ``ccop_unique_senders`` is ``float64`` rather than integer because
#: pre-cCOP-launch rows (dates < 2024-10-31) must carry NaN by contract
#: and pandas integer dtypes cannot represent NaN without the nullable
#: ``Int64`` extension — we prefer plain float64 here for downstream
#: compatibility simplicity.
EXPECTED_DTYPES: Final[Mapping[str, str]] = {
    "date": "datetime64[ns]",
    "copm_mint_usd": "float64",
    "copm_burn_usd": "float64",
    "copm_unique_minters": "int64",
    "ccop_usdt_inflow_usd": "float64",
    "ccop_usdt_outflow_usd": "float64",
    "ccop_unique_senders": "float64",
    "source_query_ids": "object",
}

#: Default CSV path. Resolves to ``contracts/data/copm_ccop_daily_flow.csv``.
DEFAULT_CSV_PATH: Final[Path] = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "copm_ccop_daily_flow.csv"
)

# ── On-chain ground-truth constants (Rev-3.1 RC-B2, RC-F2, F-3.1-2) ─────────

#: COPM (Minteo) ERC-20 token contract on Celo. Lowercase hex.
COPM_TOKEN_ADDRESS: Final[str] = "0xc92e8fc2947e32f2b574cca9f2f12097a71d5606"

#: Mento cCOP / COPm ERC-20 token contract on Celo. Lowercase hex. The
#: symbol was renamed cCOP → COPm at 2026-01-25 at THIS SAME contract
#: address; the contract is NOT redeployed on rename.
CCOP_TOKEN_ADDRESS: Final[str] = "0x8a567e2ae79ca692bd748ab832081c45de4041ea"

#: Mento protocol broker (swap venue). NOT a token. NOT queried by this
#: task. Retained here for self-documenting disambiguation.
MENTO_BROKER_ADDRESS: Final[str] = "0x777a8255ca72412f0d706dc03c9d1987306b4cad"

#: Zero address; marker for mint (``from``) and burn (``to``) events.
ZERO_ADDRESS: Final[str] = "0x0000000000000000000000000000000000000000"

#: COPM on-chain first transfer (verified via Dune query #6940691
#: ``first_seen=2024-09-17 19:54:27 UTC``).
COPM_LAUNCH_DATE: Final[pd.Timestamp] = pd.Timestamp("2024-09-17")

#: cCOP on-chain first transfer (verified via Dune query #6940691
#: ``first_seen=2024-10-31 16:35:48 UTC``).
CCOP_LAUNCH_DATE: Final[pd.Timestamp] = pd.Timestamp("2024-10-31")

#: cCOP → COPm symbol migration date (canonical per corpus
#: ``CCOP_BEHAVIORAL_FINGERPRINTS.md`` line-163; Rev-3.1 F-3.1-2 resolves
#: the corpus' internal date inconsistency — line-27 "Jan 2025" is a typo —
#: in favor of the line-163 "2026-01-25" value).
CCOP_COPM_MIGRATION_DATE: Final[pd.Timestamp] = pd.Timestamp("2026-01-25")


# ── Public functions ─────────────────────────────────────────────────────────


def load_copm_ccop_daily_flow(
    csv_path: Path | str | None = None,
) -> pd.DataFrame:
    """Load the daily COPM + cCOP/COPm on-chain flow fixture.

    Parameters
    ----------
    csv_path:
        Optional override for the CSV path. Defaults to :data:`DEFAULT_CSV_PATH`.

    Returns
    -------
    pd.DataFrame
        A new DataFrame with columns exactly equal to :data:`EXPECTED_COLUMNS`,
        parsed dtypes per :data:`EXPECTED_DTYPES`, rows sorted by ``date``
        ascending at daily cadence.

    Raises
    ------
    FileNotFoundError
        If the CSV path does not exist. Message names the absolute path
        and identifies this as a Task-11.A real-on-chain-derived fixture.
    ValueError
        On schema violations: missing columns, non-monotone date index,
        non-daily cadence, negative USD values, or pre-cCOP-launch rows
        carrying non-NaN cCOP values.
    """
    path = Path(csv_path) if csv_path is not None else DEFAULT_CSV_PATH
    path = path.expanduser().resolve() if path.is_absolute() else path.resolve()

    if not path.is_file():
        raise FileNotFoundError(
            f"Task-11.A on-chain flow fixture CSV not found at {path}. "
            "This is a real-data fixture derived from Dune query #7366593 "
            "(execution ID 01KPYR8NBKG4XV0V2VH55XJQ5F, 4.16 credits); "
            "see contracts/data/dune_onchain_sources.md for full "
            "provenance and re-fetch protocol."
        )

    # Header comment lines start with '#'. pandas' comment= option skips them.
    df = pd.read_csv(
        path,
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

    validate_daily_flow_csv(df)

    return df


def validate_daily_flow_csv(df: pd.DataFrame) -> None:
    """Validate a loaded DataFrame against the Task-11.A schema.

    Checks, in order:
      1. Exactly the eight expected columns are present in canonical order.
      2. ``date`` column is datetime-like and strictly monotone increasing
         at daily cadence.
      3. Four USD columns are floating-point, and non-negative where non-NaN.
      4. ``copm_unique_minters`` is integer-valued and non-negative.
      5. Pre-cCOP-launch rows (date < 2024-10-31) carry NaN in cCOP columns.
      6. ``source_query_ids`` has no empty entries.

    Parameters
    ----------
    df:
        DataFrame to validate.

    Raises
    ------
    ValueError
        With a diagnostic naming the first violated invariant.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError(
            f"validate_daily_flow_csv expected a DataFrame; got {type(df)!r}."
        )

    # (1) Column presence — order-sensitive ────────────────────────────────
    actual = tuple(df.columns)
    if actual != EXPECTED_COLUMNS:
        raise ValueError(
            f"Schema column drift: got {actual!r}, "
            f"expected {EXPECTED_COLUMNS!r}."
        )

    # (2) Date column: datetime-like + strictly monotone daily ─────────────
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        raise ValueError(
            f"date column must be datetime-like; "
            f"got dtype={df['date'].dtype!r}."
        )

    dates = df["date"]
    if len(dates) >= 2:
        diffs = dates.diff().dropna()
        if not (diffs > pd.Timedelta(0)).all():
            bad = diffs[diffs <= pd.Timedelta(0)].index.tolist()
            raise ValueError(
                "date column is not strictly monotone increasing; "
                f"monotonicity broken at row position(s) {bad!r}."
            )
        if not (diffs == pd.Timedelta(days=1)).all():
            uniq = sorted(set(diffs.unique().tolist()))
            raise ValueError(
                "date column is not daily-cadence; "
                f"observed gaps (set): {uniq!r}."
            )

    # (3) USD columns: float + non-negative where present ──────────────────
    for col in (
        "copm_mint_usd",
        "copm_burn_usd",
        "ccop_usdt_inflow_usd",
        "ccop_usdt_outflow_usd",
    ):
        if not pd.api.types.is_float_dtype(df[col]):
            raise ValueError(
                f"{col} must be float dtype; got {df[col].dtype!r}."
            )
        vals = df[col].to_numpy()
        # NaN is allowed (pre-launch window). Verify the non-NaN entries.
        present = ~np.isnan(vals)
        if not np.all(vals[present] >= 0.0):
            neg_positions = np.where(present & (vals < 0.0))[0]
            raise ValueError(
                f"{col} contains negative value(s) at row position(s) "
                f"{neg_positions.tolist()!r} "
                f"(first offender: {float(vals[neg_positions[0]])!r})."
            )

    # (4) Integer count column: non-negative ───────────────────────────────
    minters = df["copm_unique_minters"].to_numpy()
    if not (minters >= 0).all():
        neg_positions = np.where(minters < 0)[0]
        raise ValueError(
            f"copm_unique_minters contains negative value(s) at "
            f"row position(s) {neg_positions.tolist()!r}."
        )

    # (5) Pre-cCOP-launch rows must carry NaN in cCOP columns ──────────────
    pre_launch = df["date"] < CCOP_LAUNCH_DATE
    if pre_launch.any():
        for col in (
            "ccop_usdt_inflow_usd",
            "ccop_usdt_outflow_usd",
            "ccop_unique_senders",
        ):
            pre_vals = df.loc[pre_launch, col]
            if not pre_vals.isna().all():
                bad_rows = df.loc[pre_launch & df[col].notna(),
                                  ["date", col]].to_dict(orient="records")
                raise ValueError(
                    f"{col} carries non-NaN value(s) at rows dated before "
                    f"the cCOP launch ({CCOP_LAUNCH_DATE.date()}): "
                    f"{bad_rows!r}"
                )

    # (6) Provenance non-emptiness ─────────────────────────────────────────
    urls = df["source_query_ids"].astype(str)
    if (urls.str.len() == 0).any():
        empty_positions = df.index[urls.str.len() == 0].tolist()
        raise ValueError(
            f"source_query_ids has empty/whitespace-only row(s) at "
            f"position(s) {empty_positions!r}."
        )
