"""Tests that frozen JSON loaders produce byte-identical data to hardcoded values."""
import hashlib
import json
from pathlib import Path

FROZEN_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "frozen"
BASELINE = json.loads((FROZEN_DIR / "baseline-hashes.json").read_text())

def _sha(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

def test_il_proxy_hash_matches_baseline():
    frozen = json.loads((FROZEN_DIR / "il_proxy.json").read_text())
    assert _sha(frozen["data"]) == BASELINE["il_proxy"]
    assert frozen["metadata"]["source"] == "derived"
    assert frozen["metadata"]["row_count"] == 41

def test_il_proxy_loader_matches_baseline():
    from econometrics.data import IL_MAP
    assert _sha({k: v for k, v in IL_MAP.items()}) == BASELINE["il_proxy"]

def test_daily_at_hash_matches_baseline():
    frozen = json.loads((FROZEN_DIR / "daily_at.json").read_text())
    assert _sha(frozen["data"]) == BASELINE["daily_at"]
    assert frozen["metadata"]["source"] == "dune"
    assert frozen["metadata"]["query_id"] == 6783604

def test_daily_at_loader_matches_baseline():
    from econometrics.data import DAILY_AT_MAP, DAILY_AT_NULL_MAP
    combined = {"real": {k: v for k, v in DAILY_AT_MAP.items()},
                "null": {k: v for k, v in DAILY_AT_NULL_MAP.items()}}
    assert _sha(combined) == BASELINE["daily_at"]

def test_positions_hash_matches_baseline():
    frozen = json.loads((FROZEN_DIR / "positions.json").read_text())
    assert _sha(frozen["data"]) == BASELINE["positions"]
    assert frozen["metadata"]["source"] == "frozen_original"
    assert frozen["metadata"]["row_count"] == 600

def test_positions_loader_matches_baseline():
    from econometrics.data import RAW_POSITIONS
    assert _sha([[d, bl, at] for d, bl, at in RAW_POSITIONS]) == BASELINE["positions"]
    assert len(RAW_POSITIONS) == 600
    assert isinstance(RAW_POSITIONS[0], tuple)
    assert isinstance(RAW_POSITIONS[0][0], str)
    assert isinstance(RAW_POSITIONS[0][1], int)
    assert isinstance(RAW_POSITIONS[0][2], float)

def test_selected_pools_hash_matches_baseline():
    frozen = json.loads((FROZEN_DIR / "selected_pools.json").read_text())
    assert _sha(frozen["data"]) == BASELINE["selected_pools"]
    assert frozen["metadata"]["source"] == "subgraph"
    assert frozen["metadata"]["row_count"] == 10

def test_selected_pools_loader_matches_baseline():
    from econometrics.cross_pool.data import SELECTED_POOLS
    serialized = [
        {"address": p.address, "token0_symbol": p.token0_symbol,
         "token1_symbol": p.token1_symbol, "fee_tier": p.fee_tier,
         "tvl_usd": p.tvl_usd, "volume_usd_24h": p.volume_usd_24h,
         "pair_category": p.pair_category}
        for p in SELECTED_POOLS
    ]
    assert _sha(serialized) == BASELINE["selected_pools"]

def test_pool_concentrations_hash_matches_baseline():
    frozen = json.loads((FROZEN_DIR / "cross_pool_concentrations.json").read_text())
    assert _sha(frozen["data"]) == BASELINE["pool_concentrations"]
    assert frozen["metadata"]["source"] == "dune"
    assert frozen["metadata"]["query_id"] == 6784588

def test_pool_concentrations_loader_matches_baseline():
    from econometrics.cross_pool.data import POOL_CONCENTRATIONS
    serialized = [
        {"pool_address": pc.pool.address, "a_t": pc.a_t, "a_t_null": pc.a_t_null,
         "delta_plus": pc.delta_plus, "n_positions": pc.n_positions,
         "n_removals": pc.n_removals, "window_days": pc.window_days}
        for pc in POOL_CONCENTRATIONS
    ]
    assert _sha(serialized) == BASELINE["pool_concentrations"]

def test_per_position_fees_hash_matches_baseline():
    frozen = json.loads((FROZEN_DIR / "per_position_fees.json").read_text())
    assert _sha(frozen["data"]) == BASELINE["per_position_fees"]
    assert frozen["metadata"]["source"] == "dune"
    assert frozen["metadata"]["query_id"] == 6815916

def test_per_position_fees_loader_matches_baseline():
    from econometrics.per_position_data import PER_POSITION_DATA
    serialized = [[d, bl, xs, tid] for d, bl, xs, tid in PER_POSITION_DATA]
    assert _sha(serialized) == BASELINE["per_position_fees"]
    assert len(PER_POSITION_DATA) == 50
    assert isinstance(PER_POSITION_DATA[0], tuple)
