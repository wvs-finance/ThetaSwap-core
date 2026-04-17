"""Tests for panel_fingerprint utility.

Pure-function fingerprint over pandas DataFrames. No I/O is exercised —
serialization is the caller's concern. Tests construct real DataFrames
(not mocks) to assert deterministic, order-invariant hashing.
"""
from __future__ import annotations

import pandas as pd
import pytest

from scripts.panel_fingerprint import _EXPECTED_KEYS, fingerprint


# ── Fixture helpers ──────────────────────────────────────────────────────────


def _sample_df() -> pd.DataFrame:
    """Small deterministic panel with a date col, a numeric col, a string col."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]
            ),
            "rv": [0.12, 0.15, 0.11, 0.18],
            "regime": ["low", "low", "low", "high"],
        }
    )


# ── Tests ────────────────────────────────────────────────────────────────────


def test_fingerprint_is_deterministic() -> None:
    """Calling fingerprint twice on the same DataFrame returns equal dicts."""
    df = _sample_df()
    fp1 = fingerprint(df, "date")
    fp2 = fingerprint(df, "date")
    assert fp1 == fp2


def test_fingerprint_schema_keys() -> None:
    """Returned dict contains exactly the 6 spec-mandated keys."""
    df = _sample_df()
    fp = fingerprint(df, "date")
    # Single source of truth: the module-level Final constant.
    assert set(fp.keys()) == set(_EXPECTED_KEYS)
    assert fp["row_count"] == 4
    assert fp["column_count"] == 3
    assert isinstance(fp["column_dtypes"], dict)
    assert isinstance(fp["sha256"], str)
    assert len(fp["sha256"]) == 64  # sha256 hex digest length


def test_fingerprint_is_order_invariant() -> None:
    """Shuffling rows before fingerprinting yields the same hash."""
    df = _sample_df()
    shuffled = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    fp_original = fingerprint(df, "date")
    fp_shuffled = fingerprint(shuffled, "date")
    assert fp_original == fp_shuffled


def test_fingerprint_detects_numeric_drift() -> None:
    """Mutating a single numeric cell changes the sha256."""
    df = _sample_df()
    mutated = df.copy()
    mutated.loc[0, "rv"] = 0.99  # was 0.12
    fp_base = fingerprint(df, "date")
    fp_drift = fingerprint(mutated, "date")
    assert fp_base["sha256"] != fp_drift["sha256"]


def test_fingerprint_detects_string_drift() -> None:
    """Mutating a single string cell changes the sha256."""
    df = _sample_df()
    mutated = df.copy()
    mutated.loc[3, "regime"] = "crisis"  # was "high"
    fp_base = fingerprint(df, "date")
    fp_drift = fingerprint(mutated, "date")
    assert fp_base["sha256"] != fp_drift["sha256"]


def test_fingerprint_missing_date_column_raises() -> None:
    """Missing date_column raises ValueError naming the column and listing columns."""
    df = _sample_df()
    with pytest.raises(ValueError) as exc_info:
        fingerprint(df, "nonexistent_col")
    msg = str(exc_info.value)
    assert "nonexistent_col" in msg
    # Error message must list the actual columns to aid debugging
    for col in df.columns:
        assert col in msg


def test_fingerprint_empty_dataframe_raises() -> None:
    """Empty DataFrame with the date column present raises ValueError."""
    empty = pd.DataFrame({"date": pd.to_datetime([]), "rv": [], "regime": []})
    with pytest.raises(ValueError) as exc_info:
        fingerprint(empty, "date")
    assert "empty" in str(exc_info.value).lower()


def test_fingerprint_all_null_date_column_raises() -> None:
    """DataFrame whose date_column is entirely NaT/None raises ValueError."""
    df = pd.DataFrame(
        {
            "date": pd.to_datetime([pd.NaT, pd.NaT, pd.NaT]),
            "rv": [0.1, 0.2, 0.3],
            "regime": ["low", "low", "high"],
        }
    )
    with pytest.raises(ValueError) as exc_info:
        fingerprint(df, "date")
    assert "null" in str(exc_info.value).lower()


def test_fingerprint_single_row() -> None:
    """1-row DataFrame fingerprints successfully (date_min == date_max)."""
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01"]),
            "rv": [0.12],
            "regime": ["low"],
        }
    )
    fp = fingerprint(df, "date")
    assert fp["row_count"] == 1
    assert fp["date_min"] == fp["date_max"]
    assert len(fp["sha256"]) == 64


def test_fingerprint_invariant_to_column_order() -> None:
    """Two DataFrames with identical data but different column order produce equal sha256."""
    df = _sample_df()
    reordered = df[["regime", "date", "rv"]]  # different column order, same data
    fp_original = fingerprint(df, "date")
    fp_reordered = fingerprint(reordered, "date")
    assert fp_original["sha256"] == fp_reordered["sha256"]
