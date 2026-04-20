"""Pure-function fingerprint over pandas DataFrames.

Emits a 6-key summary dict used to assert cross-notebook panel integrity:
NB1 §8 serializes the result as nb1_panel_fingerprint.json; NB2 §1 and
NB3 §1 re-compute and compare to detect upstream drift.

This module performs zero I/O — the caller owns serialization.
"""
from __future__ import annotations

import hashlib
from typing import Final

import pandas as pd

# ── Spec constants ───────────────────────────────────────────────────────────

_EXPECTED_KEYS: Final[frozenset[str]] = frozenset(
    {
        "row_count",
        "column_count",
        "column_dtypes",
        "date_min",
        "date_max",
        "sha256",
    }
)

# ── Public API ───────────────────────────────────────────────────────────────


def fingerprint(df: pd.DataFrame, date_column: str) -> dict[str, object]:
    """Return a deterministic 6-key fingerprint of a pandas DataFrame.

    The sha256 is invariant to both row order (sorted by date_column
    internally) and column order (columns reordered alphabetically before
    serialization). Data drift in any cell still flips the hash.

    Parameters
    ----------
    df : pd.DataFrame
        Panel to fingerprint. Must contain ``date_column`` and at least one row.
    date_column : str
        Name of the column used for min/max extraction and stable sort.

    Returns
    -------
    dict[str, object]
        Dict with exactly 6 keys: row_count, column_count, column_dtypes,
        date_min, date_max, sha256.

    Raises
    ------
    ValueError
        If ``date_column`` is not a column of ``df`` (message names the
        missing column and lists the actual columns), if ``df`` is empty,
        or if ``date_column`` contains only null values.
    """
    if date_column not in df.columns:
        raise ValueError(
            f"date_column '{date_column}' not found in DataFrame. "
            f"Available columns: {list(df.columns)}"
        )

    if len(df) == 0:
        raise ValueError("Cannot fingerprint an empty DataFrame")
    if df[date_column].isna().all():
        raise ValueError(
            f"Date column {date_column!r} contains only null values"
        )

    # reset_index is belt-and-braces; the real hash stability comes from
    # index=False in the to_csv call below. If that flips, reset_index won't save us.
    sorted_df = df.sort_values(by=date_column).reset_index(drop=True)

    column_dtypes = {col: str(sorted_df[col].dtype) for col in sorted(sorted_df.columns)}

    # Reorder columns alphabetically so an upstream producer reordering
    # columns (e.g. via merge/reindex) does not flip the hash.
    csv_bytes = (
        sorted_df[sorted(sorted_df.columns)].to_csv(index=False).encode("utf-8")
    )
    sha256_hex = hashlib.sha256(csv_bytes).hexdigest()

    date_series = sorted_df[date_column]

    result: dict[str, object] = {
        "row_count": int(len(sorted_df)),
        "column_count": int(len(sorted_df.columns)),
        "column_dtypes": column_dtypes,
        "date_min": pd.Timestamp(date_series.min()).isoformat(),
        "date_max": pd.Timestamp(date_series.max()).isoformat(),
        "sha256": sha256_hex,
    }

    # Module-internal self-check: catch schema drift during development.
    assert set(result) == _EXPECTED_KEYS, f"schema drift: got {set(result)}"

    return result
