"""V3 subgraph client: pool discovery + TVL ranking."""
from __future__ import annotations

import os
from typing import Final, Sequence

import httpx
from dotenv import load_dotenv

from econometrics.cross_pool.types import STABLECOINS, PairCategory, PoolInfo

SUBGRAPH_URL: Final[str] = (
    "https://gateway.thegraph.com/api/{key}/subgraphs/id/"
    "5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
)

MIN_VOLUME_USD: Final[float] = 1_000_000.0

POOL_QUERY: Final[str] = """
{
  pools(first: 100, orderBy: totalValueLockedUSD, orderDirection: desc,
        where: { volumeUSD_gt: "1000000" }) {
    id
    token0 { symbol }
    token1 { symbol }
    feeTier
    totalValueLockedUSD
    volumeUSD
  }
}
"""


def classify_pair(sym0: str, sym1: str) -> PairCategory:
    """Classify a token pair into stable/stable, stable/token, or token/token."""
    s0 = sym0.upper() in STABLECOINS
    s1 = sym1.upper() in STABLECOINS
    if s0 and s1:
        return "stable_stable"
    if s0 or s1:
        return "stable_token"
    return "token_token"


def fetch_top_pools() -> list[PoolInfo]:
    """Fetch top 50 V3 pools by TVL from the subgraph."""
    load_dotenv()
    key = os.environ["GRAPH_API_KEY"]
    url = SUBGRAPH_URL.format(key=key)
    resp = httpx.post(url, json={"query": POOL_QUERY}, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()["data"]["pools"]
    return [
        PoolInfo(
            address=p["id"],
            token0_symbol=p["token0"]["symbol"],
            token1_symbol=p["token1"]["symbol"],
            fee_tier=int(p["feeTier"]),
            tvl_usd=float(p["totalValueLockedUSD"]),
            volume_usd_24h=float(p["volumeUSD"]),
            pair_category=classify_pair(
                p["token0"]["symbol"], p["token1"]["symbol"]
            ),
        )
        for p in data
    ]


def select_pools(pools: Sequence[PoolInfo]) -> list[PoolInfo]:
    """Select ~10 pools: 2 stable/stable, 4 stable/token, 4 token/token.

    Takes top N by TVL within each category.
    """
    targets: Final[dict[PairCategory, int]] = {
        "stable_stable": 2,
        "stable_token": 4,
        "token_token": 4,
    }
    by_cat: dict[PairCategory, list[PoolInfo]] = {
        cat: [p for p in pools if p.pair_category == cat]
        for cat in targets
    }
    return [
        p
        for cat, n in targets.items()
        for p in by_cat[cat][:n]
    ]
