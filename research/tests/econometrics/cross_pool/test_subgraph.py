"""Tests for subgraph client functions."""
from __future__ import annotations

from econometrics.cross_pool.subgraph import classify_pair, select_pools
from econometrics.cross_pool.types import PoolInfo


def test_classify_stable_stable() -> None:
    assert classify_pair("USDC", "USDT") == "stable_stable"


def test_classify_stable_token() -> None:
    assert classify_pair("WETH", "USDC") == "stable_token"


def test_classify_token_token() -> None:
    assert classify_pair("WETH", "WBTC") == "token_token"


def test_classify_case_insensitive() -> None:
    assert classify_pair("usdc", "weth") == "stable_token"


def test_select_pools_respects_targets() -> None:
    pools = [
        PoolInfo("0x1", "USDC", "USDT", 100, 500.0, 100.0, "stable_stable"),
        PoolInfo("0x2", "USDC", "DAI", 500, 400.0, 80.0, "stable_stable"),
        PoolInfo("0x3", "USDC", "FRAX", 500, 300.0, 60.0, "stable_stable"),
        PoolInfo("0x4", "WETH", "USDC", 500, 1000.0, 500.0, "stable_token"),
        PoolInfo("0x5", "WETH", "USDC", 3000, 900.0, 400.0, "stable_token"),
        PoolInfo("0x6", "WBTC", "USDC", 3000, 800.0, 300.0, "stable_token"),
        PoolInfo("0x7", "LINK", "USDC", 3000, 700.0, 200.0, "stable_token"),
        PoolInfo("0x8", "UNI", "USDC", 3000, 600.0, 100.0, "stable_token"),
        PoolInfo("0x9", "WETH", "WBTC", 3000, 500.0, 200.0, "token_token"),
        PoolInfo("0xa", "LINK", "WETH", 3000, 400.0, 150.0, "token_token"),
        PoolInfo("0xb", "UNI", "WETH", 3000, 300.0, 100.0, "token_token"),
        PoolInfo("0xc", "AAVE", "WETH", 3000, 200.0, 50.0, "token_token"),
        PoolInfo("0xd", "MKR", "WETH", 3000, 100.0, 25.0, "token_token"),
    ]
    selected = select_pools(pools)
    cats = [p.pair_category for p in selected]
    assert cats.count("stable_stable") == 2
    assert cats.count("stable_token") == 4
    assert cats.count("token_token") == 4
    assert len(selected) == 10
