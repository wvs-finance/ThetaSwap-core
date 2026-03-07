"""Tests for econometrics.data — hardcoded Dune extraction data."""
from __future__ import annotations

from econometrics.data import DAILY_AT_MAP, IL_MAP, RAW_POSITIONS


def test_raw_positions_count() -> None:
    assert len(RAW_POSITIONS) == 600


def test_daily_at_map_is_complete() -> None:
    """41 unique days in the Q4v2 data."""
    assert len(DAILY_AT_MAP) == 41


def test_daily_at_map_values_in_range() -> None:
    """A_T should be between 0 and 1."""
    for day, at in DAILY_AT_MAP.items():
        assert 0.0 < at < 1.0, f"A_T out of range on {day}: {at}"


def test_il_map_covers_daily_at_dates() -> None:
    """IL map should cover most daily A_T dates."""
    overlap = set(IL_MAP.keys()) & set(DAILY_AT_MAP.keys())
    assert len(overlap) >= 35  # at least 35 of 41 days covered


def test_raw_positions_blocklife_positive() -> None:
    for _, bl, _ in RAW_POSITIONS:
        assert bl > 1, f"blocklife must be > 1 (JIT filtered)"
