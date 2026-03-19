"""Selected pools and collected data for cross-pool concentration analysis.

Pool selection: V3 subgraph top pools by TVL (volume > $1M), 2-4-4 stratification.
A_T computed via Dune query 6784588 (90-day window, 2026-03-05).
Total Dune cost: ~3 credits.
"""
from __future__ import annotations

import json as _json
from pathlib import Path as _Path
from typing import Final

from econometrics.cross_pool.types import PoolConcentration, PoolInfo

_FROZEN = _Path(__file__).resolve().parent.parent.parent / "data" / "frozen"

def _load_frozen(name: str):
    return _json.loads((_FROZEN / name).read_text())

# ── Selected pools: loaded from canonical frozen JSON ──
_pools_data = _load_frozen("selected_pools.json")
SELECTED_POOLS: Final[list[PoolInfo]] = [
    PoolInfo(
        address=p["address"], token0_symbol=p["token0_symbol"],
        token1_symbol=p["token1_symbol"], fee_tier=p["fee_tier"],
        tvl_usd=p["tvl_usd"], volume_usd_24h=p["volume_usd_24h"],
        pair_category=p["pair_category"]
    )
    for p in _pools_data["data"]
]

# ── A_T results: loaded from canonical frozen JSON ──
_conc_data = _load_frozen("cross_pool_concentrations.json")
_pool_by_addr: dict[str, PoolInfo] = {p.address: p for p in SELECTED_POOLS}
POOL_CONCENTRATIONS: Final[list[PoolConcentration]] = [
    PoolConcentration(
        pool=_pool_by_addr[c["pool_address"]],
        a_t=c["a_t"], a_t_null=c["a_t_null"], delta_plus=c["delta_plus"],
        n_positions=c["n_positions"], n_removals=c["n_removals"],
        window_days=c["window_days"]
    )
    for c in _conc_data["data"]
]
