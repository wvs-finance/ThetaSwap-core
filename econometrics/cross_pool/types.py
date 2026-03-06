"""Cross-pool analysis domain types."""
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
class CollectEvent:
    """One Collect (fee withdrawal) event from Dune."""
    owner: str
    tick_lower: int
    tick_upper: int
    amount0: int
    amount1: int
    block_number: int


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
