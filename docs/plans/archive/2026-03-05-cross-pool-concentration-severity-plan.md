# Cross-Pool Fee Concentration Severity — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Compute A_T across ~10 Uniswap V3 pools stratified by pair type to determine if fee concentration correlates with pool size (TVL), resolving the insurance architecture decision.

**Architecture:** Two-tier data pipeline: V3 subgraph (free) for pool discovery + TVL, Dune MCP (~100 credits) for position-level Collect events per pool. Compute A_T per pool, scatter against TVL.

**Tech Stack:** Python 3.12, JAX 0.9.1, httpx, Dune MCP, matplotlib, uhi8 venv

---

### Task 0: Subgraph Client — Pool Discovery

**Files:**
- Create: `econometrics/cross_pool/subgraph.py`
- Create: `econometrics/cross_pool/__init__.py`
- Test: `tests/econometrics/cross_pool/test_subgraph.py`

**Step 1: Write the types**

```python
# econometrics/cross_pool/types.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Final, Literal, TypeAlias

PairCategory: TypeAlias = Literal["stable_stable", "stable_token", "token_token"]

STABLECOINS: Final[frozenset[str]] = frozenset({
    "USDC", "USDT", "DAI", "FRAX", "LUSD", "TUSD", "BUSD", "GUSD", "USDP",
})

@dataclass(frozen=True)
class PoolInfo:
    """Pool metadata from V3 subgraph."""
    address: str
    token0_symbol: str
    token1_symbol: str
    fee_tier: int
    tvl_usd: float
    volume_usd_24h: float
    pair_category: PairCategory

@dataclass(frozen=True)
class PoolConcentration:
    """A_T result for one pool."""
    pool: PoolInfo
    a_t: float
    a_t_null: float
    delta_plus: float
    n_positions: int
    n_removals: int
    window_days: int
```

**Step 2: Write the subgraph client**

```python
# econometrics/cross_pool/subgraph.py
from __future__ import annotations
import os
import httpx
from typing import Sequence
from econometrics.cross_pool.types import PoolInfo, PairCategory, STABLECOINS

SUBGRAPH_URL: str = (
    "https://gateway.thegraph.com/api/{key}/subgraphs/id/"
    "5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
)

QUERY: str = """
{
  pools(first: 50, orderBy: totalValueLockedUSD, orderDirection: desc) {
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
    s0 = sym0.upper() in STABLECOINS
    s1 = sym1.upper() in STABLECOINS
    if s0 and s1:
        return "stable_stable"
    if s0 or s1:
        return "stable_token"
    return "token_token"

def fetch_top_pools() -> list[PoolInfo]:
    key = os.environ["GRAPH_API_KEY"]
    url = SUBGRAPH_URL.format(key=key)
    resp = httpx.post(url, json={"query": QUERY}, timeout=30.0)
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
            pair_category=classify_pair(p["token0"]["symbol"], p["token1"]["symbol"]),
        )
        for p in data
    ]

def select_pools(pools: Sequence[PoolInfo]) -> list[PoolInfo]:
    """Select ~10 pools: 2 stable/stable, 4 stable/token, 4 token/token."""
    by_cat: dict[PairCategory, list[PoolInfo]] = {
        "stable_stable": [], "stable_token": [], "token_token": [],
    }
    for p in pools:
        by_cat[p.pair_category].append(p)
    targets = {"stable_stable": 2, "stable_token": 4, "token_token": 4}
    selected: list[PoolInfo] = []
    for cat, n in targets.items():
        selected.extend(by_cat[cat][:n])
    return selected
```

**Step 3: Write test for classify_pair**

```python
# tests/econometrics/cross_pool/test_subgraph.py
from econometrics.cross_pool.subgraph import classify_pair

def test_stable_stable():
    assert classify_pair("USDC", "USDT") == "stable_stable"

def test_stable_token():
    assert classify_pair("WETH", "USDC") == "stable_token"

def test_token_token():
    assert classify_pair("WETH", "WBTC") == "token_token"
```

**Step 4: Run tests**

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev
source .venv/bin/activate  # or uhi8 venv
python -m pytest tests/econometrics/cross_pool/test_subgraph.py -v
```

**Step 5: Commit**

```bash
git add -f econometrics/cross_pool/__init__.py econometrics/cross_pool/types.py econometrics/cross_pool/subgraph.py tests/econometrics/cross_pool/__init__.py tests/econometrics/cross_pool/test_subgraph.py
git commit -m "feat(cross-pool): subgraph client for pool discovery + TVL ranking"
```

---

### Task 1: Run Subgraph Query — Select 10 Pools

**Files:**
- Uses: `econometrics/cross_pool/subgraph.py`

**Step 1: Run the subgraph query interactively**

Load .env, call `fetch_top_pools()`, then `select_pools()`. Print the 10 selected pools with addresses, pair, fee tier, TVL, category.

**Step 2: Hardcode the selected pool list**

Save the 10 pool addresses + metadata as a constant in `econometrics/cross_pool/data.py` so Dune queries can reference them without re-querying the subgraph.

```python
# econometrics/cross_pool/data.py
from econometrics.cross_pool.types import PoolInfo

SELECTED_POOLS: list[PoolInfo] = [
    # Filled after subgraph query
]
```

**Step 3: Commit**

```bash
git add -f econometrics/cross_pool/data.py
git commit -m "feat(cross-pool): selected 10 pools from V3 subgraph TVL ranking"
```

---

### Task 2: Dune Collect Query — Per Pool

**Files:**
- Create: `econometrics/cross_pool/dune_collect.py`

**Step 1: Write the Dune query template**

The query fetches Collect events (position fee withdrawals) for a specific pool over 90 days. This is the same pattern as the existing ETH/USDC analysis but parameterized by pool address.

```sql
SELECT
    c.evt_tx_hash,
    c.owner,
    c.tickLower,
    c.tickUpper,
    c.amount0,
    c.amount1,
    c.evt_block_number,
    c.evt_block_time
FROM uniswap_v3_ethereum.Pair_evt_Collect c
WHERE c.contract_address = {{pool_address}}
  AND c.evt_block_time >= NOW() - INTERVAL '90' DAY
ORDER BY c.evt_block_number
```

**Step 2: Execute via Dune MCP for each pool**

Use `mcp__dune__createDuneQuery` + `mcp__dune__executeQueryById` for each of the 10 pools. Store results in `econometrics/cross_pool/data.py` as hardcoded dicts (same pattern as existing `data.py`).

**Step 3: Commit after each pool's data is collected**

---

### Task 3: Compute A_T Per Pool

**Files:**
- Create: `econometrics/cross_pool/concentration.py`
- Test: `tests/econometrics/cross_pool/test_concentration.py`

**Step 1: Write A_T computation**

```python
# econometrics/cross_pool/concentration.py
from __future__ import annotations
import math
from typing import Sequence
from econometrics.cross_pool.types import PoolConcentration, PoolInfo

@dataclass(frozen=True)
class CollectEvent:
    owner: str
    tick_lower: int
    tick_upper: int
    amount0: int
    amount1: int
    block_number: int

def compute_pool_at(
    pool: PoolInfo,
    events: Sequence[CollectEvent],
    window_days: int = 90,
) -> PoolConcentration:
    """Compute aggregate A_T for a pool from its Collect events.

    Groups by (owner, tickLower, tickUpper) to identify positions.
    For each position: fee_share = position_fees / total_fees.
    theta_k = 1 / blocklife (blocks between first and last event).
    A_T = sqrt(sum(theta_k * fee_share^2)).
    """
    # Group by position key
    positions: dict[tuple, list[CollectEvent]] = {}
    for e in events:
        key = (e.owner, e.tick_lower, e.tick_upper)
        positions.setdefault(key, []).append(e)

    total_fees = sum(e.amount0 + e.amount1 for e in events)
    if total_fees == 0:
        return PoolConcentration(pool=pool, a_t=0.0, a_t_null=0.0,
                                  delta_plus=0.0, n_positions=0,
                                  n_removals=len(events), window_days=window_days)

    n = len(positions)
    theta_sum = 0.0
    weighted_sq_sum = 0.0

    for _key, pos_events in positions.items():
        pos_fees = sum(e.amount0 + e.amount1 for e in pos_events)
        fee_share = pos_fees / total_fees
        blocks = [e.block_number for e in pos_events]
        blocklife = max(1, max(blocks) - min(blocks))
        theta_k = 1.0 / blocklife
        theta_sum += theta_k
        weighted_sq_sum += theta_k * fee_share ** 2

    a_t = math.sqrt(weighted_sq_sum)
    a_t_null = math.sqrt(theta_sum / (n * n)) if n > 0 else 0.0
    delta_plus = max(0.0, a_t - a_t_null)

    return PoolConcentration(
        pool=pool, a_t=a_t, a_t_null=a_t_null, delta_plus=delta_plus,
        n_positions=n, n_removals=len(events), window_days=window_days,
    )
```

**Step 2: Write test**

```python
def test_equal_shares_gives_null():
    """If all positions have equal fee shares, A_T == A_T_null."""
    # ... construct synthetic events with equal shares
    result = compute_pool_at(mock_pool, events)
    assert abs(result.a_t - result.a_t_null) < 1e-6
    assert result.delta_plus < 1e-6
```

**Step 3: Run tests, commit**

---

### Task 4: Analysis + Plots

**Files:**
- Create: `econometrics/cross_pool/analysis.py`

**Step 1: Write analysis functions**

```python
# econometrics/cross_pool/analysis.py
from __future__ import annotations
import math
from typing import Sequence
from econometrics.cross_pool.types import PoolConcentration

def spearman_rank(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Spearman rank correlation (no scipy dependency)."""
    n = len(xs)
    rx = _ranks(xs)
    ry = _ranks(ys)
    d2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return 1 - 6 * d2 / (n * (n * n - 1))

def scatter_at_vs_tvl(results: Sequence[PoolConcentration]) -> None:
    """Scatter: A_T vs log(TVL), colored by pair category."""
    import matplotlib.pyplot as plt
    # ... implementation

def scatter_at_vs_volume(results: Sequence[PoolConcentration]) -> None:
    """Scatter: A_T vs log(volume), colored by pair category."""
    # ...

def summary_table(results: Sequence[PoolConcentration]) -> str:
    """Markdown table of all pools with A_T, TVL, category."""
    # ...

def architecture_decision(rho: float) -> str:
    """Return architecture recommendation based on rank correlation."""
    if rho < -0.3:
        return "HOOK_INSURANCE"  # small pools have high concentration
    elif rho > 0.3:
        return "CFMM_POOL"  # large pools have high concentration
    else:
        return "HYBRID"  # no clear pattern
```

**Step 2: Commit**

---

### Task 5: Notebook Assembly

**Files:**
- Create: `notebooks/cross-pool-concentration-severity.ipynb`

**Cells:**

1. **Header**: Title, purpose, literature grounding
2. **Pool selection**: Load subgraph results, show table of 10 pools
3. **A_T computation**: Load Collect data, compute per pool, show results table
4. **Scatter: A_T vs TVL**: With pair category colors, Spearman rho annotation
5. **Scatter: A_T vs volume**: Same
6. **Architecture decision**: Based on correlation sign and magnitude
7. **Conclusion**: State the architecture choice with evidence

**Step 1: Create the notebook with all cells**

**Step 2: Run it end-to-end**

**Step 3: Commit**

```bash
git add notebooks/cross-pool-concentration-severity.ipynb
git commit -m "feat(cross-pool): concentration severity analysis notebook — architecture decision"
```
