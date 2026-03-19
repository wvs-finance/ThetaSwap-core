"""Per-position data from Dune queries for ETH/USDC 0.3% pool, Dec 20-26 2025.

Three datasets, progressively refined:
1. PER_POSITION_DATA_TOTAL_VALUE (Dune 6815894) — total Collect proxy
2. PER_POSITION_DATA_EXIT_FEES (Dune 6815901) — exit-only fees (54% zero)
3. PER_POSITION_DATA (Dune 6815916) ← RECOMMENDED, lifetime fees

Now loaded from data/frozen/per_position_fees.json.
"""
from __future__ import annotations
import json as _json
from pathlib import Path as _Path

_FROZEN = _Path(__file__).resolve().parent.parent / "data" / "frozen"
_ppd = _json.loads((_FROZEN / "per_position_fees.json").read_text())

PER_POSITION_DATA: tuple[tuple[str, int, float, int], ...] = tuple(
    (str(r[0]), int(r[1]), float(r[2]), int(r[3])) for r in _ppd["data"]
)
