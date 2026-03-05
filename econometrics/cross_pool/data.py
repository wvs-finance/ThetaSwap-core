"""Selected pools and collected data for cross-pool concentration analysis.

Pool selection: V3 subgraph top pools by TVL (volume > $1M), 2-4-4 stratification.
Query date: 2026-03-05.
"""
from __future__ import annotations

from typing import Final

from econometrics.cross_pool.types import PoolInfo

SELECTED_POOLS: Final[list[PoolInfo]] = [
    # ── stable/stable (2) ──
    PoolInfo("0x3416cf6c708da44db2624d63ea0aaef7113527c6", "USDC", "USDT", 100, 32_300_000.0, 105_630_000_000.0, "stable_stable"),
    PoolInfo("0x7858e59e0c01ea06df3af3d20ac7b0003275d4bf", "USDC", "USDT", 500, 8_700_000.0, 16_320_000_000.0, "stable_stable"),
    # ── stable/token (4) ──
    PoolInfo("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", "USDC", "WETH", 500, 372_400_000.0, 586_880_000_000.0, "stable_token"),
    PoolInfo("0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8", "USDC", "WETH", 3000, 269_400_000.0, 88_560_000_000.0, "stable_token"),
    PoolInfo("0x4e68ccd3e89f51c3074ca5072bbac773960dfa36", "WETH", "USDT", 3000, 214_200_000.0, 59_460_000_000.0, "stable_token"),
    PoolInfo("0x99ac8ca7087fa4a2a1fb6357269965a2014abc35", "WBTC", "USDC", 3000, 134_500_000.0, 29_290_000_000.0, "stable_token"),
    # ── token/token (4) ──
    PoolInfo("0xcbcdf9626bc03e24f779434178a73a0b4bad62ed", "WBTC", "WETH", 3000, 191_900_000.0, 34_000_000_000.0, "token_token"),
    PoolInfo("0x4585fe77225b41b697c938b018e2ac67ac5a20c0", "WBTC", "WETH", 500, 112_800_000.0, 94_320_000_000.0, "token_token"),
    PoolInfo("0xa6cc3c2531fdaa6ae1a3ca84c2855806728693e8", "LINK", "WETH", 3000, 52_100_000.0, 15_250_000_000.0, "token_token"),
    PoolInfo("0x1d42064fc4beb5f8aaf85f4617ae8b3b5b8bd801", "UNI", "WETH", 3000, 34_500_000.0, 9_860_000_000.0, "token_token"),
]
