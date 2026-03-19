"""Hardcoded data from Dune MCP extractions (Q4v2 + Q5).

Single source of truth. All other modules import from here.
No runtime Dune calls — data collected during prior sessions.
"""
from __future__ import annotations

import json as _json
from pathlib import Path as _Path
from typing import Final

_FROZEN = _Path(__file__).resolve().parent.parent / "data" / "frozen"

def _load_frozen(name: str):
    return _json.loads((_FROZEN / name).read_text())

# ── Q5 IL proxy: loaded from canonical frozen JSON ──
IL_MAP: Final[dict[str, float]] = _load_frozen("il_proxy.json")["data"]

# ── Q4v2 position data: loaded from canonical frozen JSON ──
# Original query lost. Reconstruction: Dune 6847717 (directional match confirmed).
# Format: (burn_date, blocklife, exit_day_a_t)
_positions_data = _load_frozen("positions.json")
RAW_POSITIONS: Final[list[tuple[str, int, float]]] = [
    (str(r[0]), int(r[1]), float(r[2])) for r in _positions_data["data"]
]

# ── Daily pool-level A_T: loaded from canonical frozen JSON ──
# Original: Dune query 6783604, per-position Collect fees joined with Burn+Mint
_daily_at_data = _load_frozen("daily_at.json")
DAILY_AT_MAP: Final[dict[str, float]] = _daily_at_data["data"]["real"]

# ── Null A_T: Ma & Crapis equal-share (x_k=1/N) from SAME position set ──
DAILY_AT_NULL_MAP: Final[dict[str, float]] = _daily_at_data["data"]["null"]
