"""Tests for panel_fingerprint utility.

Pure-function fingerprint over pandas DataFrames. No I/O is exercised —
serialization is the caller's concern. Tests construct real DataFrames
(not mocks) to assert deterministic, order-invariant hashing.
"""
from __future__ import annotations

import pandas as pd
import pytest

from scripts.panel_fingerprint import fingerprint


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
    expected_keys = {
        "row_count",
        "column_count",
        "column_dtypes",
        "date_min",
        "date_max",
        "sha256",
    }
    assert set(fp.keys()) == expected_keys
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
