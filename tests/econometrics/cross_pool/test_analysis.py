"""Tests for cross-pool analysis functions."""
from __future__ import annotations

from econometrics.cross_pool.analysis import _ranks, spearman_rank


def test_ranks_no_ties() -> None:
    assert _ranks([3.0, 1.0, 2.0]) == [3.0, 1.0, 2.0]


def test_ranks_with_ties() -> None:
    assert _ranks([1.0, 2.0, 2.0, 4.0]) == [1.0, 2.5, 2.5, 4.0]


def test_spearman_perfect_positive() -> None:
    rho = spearman_rank([1.0, 2.0, 3.0, 4.0], [10.0, 20.0, 30.0, 40.0])
    assert abs(rho - 1.0) < 1e-10


def test_spearman_perfect_negative() -> None:
    rho = spearman_rank([1.0, 2.0, 3.0, 4.0], [40.0, 30.0, 20.0, 10.0])
    assert abs(rho - (-1.0)) < 1e-10


def test_spearman_too_few() -> None:
    assert spearman_rank([1.0, 2.0], [3.0, 4.0]) == 0.0
