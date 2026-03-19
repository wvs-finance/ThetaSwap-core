# Data Provenance: Canonical JSON + Loader Pattern — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace hardcoded Python data dicts with self-documenting canonical JSON files, preserving all econometric results identically.

**Architecture:** 7 frozen JSON files under `research/data/frozen/` with metadata + SHA-256 hashes. 3 Python data files become thin loaders. One verification script for reviewers. Each dataset migrated individually behind a 5-level regression gate.

**Tech Stack:** Python 3.11 (uhi8 venv), JSON, hashlib, pytest, Jupyter, Forge

**Spec:** `docs/superpowers/specs/2026-03-17-data-provenance-canonical-json-design.md`

**User workflow rule:** All Python code (.py) must be presented piece-by-piece for user approval before writing. JSON files and docs can be handled autonomously.

---

## File Map

### New files
| File | Responsibility |
|------|---------------|
| `research/data/frozen/il_proxy.json` | IL_MAP frozen data + metadata |
| `research/data/frozen/daily_at.json` | DAILY_AT_MAP + DAILY_AT_NULL_MAP frozen data + metadata |
| `research/data/frozen/positions.json` | RAW_POSITIONS frozen data + metadata |
| `research/data/frozen/selected_pools.json` | SELECTED_POOLS frozen data + metadata |
| `research/data/frozen/cross_pool_concentrations.json` | POOL_CONCENTRATIONS frozen data + metadata |
| `research/data/frozen/per_position_fees.json` | PER_POSITION_DATA frozen data + metadata |
| `research/data/frozen/fci_v4_events.json` | FCI V4 raw events frozen data + metadata |
| `research/data/frozen/README.md` | Documents format, IL_MAP derivation, provenance chain |
| `research/data/scripts/verify_provenance.py` | One-command provenance verification for reviewers |
| `research/tests/data/test_frozen_loaders.py` | Tests that loaders produce byte-identical data to current hardcoded values |

### Modified files
| File | Change |
|------|--------|
| `research/econometrics/data.py` | Hardcoded dicts → JSON loaders |
| `research/econometrics/cross_pool/data.py` | Hardcoded dicts → JSON loaders |
| `research/econometrics/per_position_data.py` | Hardcoded tuple → JSON loader |
| `research/data/scripts/fci_oracle.py:360` | Read path `data/raw/` → `data/frozen/` |
| `research/data/queries/README.md` | Add frozen JSON references, query ID table |

---

## Task 0: Baseline Snapshot & Shared Utilities

**Files:**
- Create: `research/data/frozen/` (directory)
- Create: `research/tests/data/test_frozen_loaders.py`
- Create: `tmp/baseline-hashes.json` (committed — tests depend on it; cleaned up in Task 10)

This task captures the ground truth before any changes. All subsequent tasks compare against this.

- [ ] **Step 0.1: Create frozen directory**

```bash
mkdir -p /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/research/data/frozen
```

- [ ] **Step 0.2: Generate baseline hashes for all 7 datasets**

Write a script `tmp/generate_baseline.py` that:
1. Imports all hardcoded data from the 3 Python files
2. Serializes each to canonical JSON (sorted keys, no whitespace)
3. Computes SHA-256 of each
4. Writes `tmp/baseline-hashes.json` with dataset name → hash

```python
"""Generate baseline SHA-256 hashes for all hardcoded datasets."""
import hashlib
import json
import sys
sys.path.insert(0, "research")

from econometrics.data import RAW_POSITIONS, DAILY_AT_MAP, DAILY_AT_NULL_MAP, IL_MAP
from econometrics.cross_pool.data import SELECTED_POOLS, POOL_CONCENTRATIONS
from econometrics.per_position_data import PER_POSITION_DATA

def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))

def sha(obj) -> str:
    return hashlib.sha256(canon(obj).encode()).hexdigest()

# Serialize each to its canonical form
datasets = {
    "il_proxy": {k: v for k, v in IL_MAP.items()},
    "daily_at": {"real": {k: v for k, v in DAILY_AT_MAP.items()},
                  "null": {k: v for k, v in DAILY_AT_NULL_MAP.items()}},
    "positions": [[d, bl, at] for d, bl, at in RAW_POSITIONS],
    "selected_pools": [
        {"address": p.address, "token0_symbol": p.token0_symbol,
         "token1_symbol": p.token1_symbol, "fee_tier": p.fee_tier,
         "tvl_usd": p.tvl_usd, "volume_usd_24h": p.volume_usd_24h,
         "pair_category": p.pair_category}
        for p in SELECTED_POOLS
    ],
    "pool_concentrations": [
        {"pool_address": pc.pool.address, "a_t": pc.a_t, "a_t_null": pc.a_t_null,
         "delta_plus": pc.delta_plus, "n_positions": pc.n_positions,
         "n_removals": pc.n_removals, "window_days": pc.window_days}
        for pc in POOL_CONCENTRATIONS
    ],
    "per_position_fees": [[d, bl, xs, tid] for d, bl, xs, tid in PER_POSITION_DATA],
}

hashes = {name: sha(data) for name, data in datasets.items()}
with open("tmp/baseline-hashes.json", "w") as f:
    json.dump(hashes, f, indent=2)

print("Baseline hashes:")
for name, h in hashes.items():
    print(f"  {name}: {h[:16]}...")
```

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python tmp/generate_baseline.py`

- [ ] **Step 0.3: Run full test suite — capture baseline pass count**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/research && ../uhi8/bin/python -m pytest tests/ -v 2>&1 | tail -5`
Expected: 139 passed

- [ ] **Step 0.4: Run duration model — capture baseline output**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/research && ../uhi8/bin/python -m econometrics.run_duration 2>&1 | head -20`
Expected: beta_a_t ≈ 5.34, R² ≈ 0.58

- [ ] **Step 0.5: Commit baseline tooling**

```bash
git add tmp/generate_baseline.py tmp/baseline-hashes.json research/data/frozen/
git commit -m "chore: add baseline hash generator and frozen directory for data provenance"
```

---

## Task 1: Migrate IL_MAP (derived, simplest)

**Files:**
- Create: `research/data/frozen/il_proxy.json`
- Modify: `research/econometrics/data.py:10-26`
- Test: `research/tests/data/test_frozen_loaders.py`

- [ ] **Step 1.1: Write the failing test**

Create `research/tests/data/__init__.py` (empty) and `research/tests/data/test_frozen_loaders.py`:

```python
"""Tests that frozen JSON loaders produce byte-identical data to hardcoded values."""
import hashlib
import json
from pathlib import Path

FROZEN_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "frozen"
BASELINE = json.loads(
    (Path(__file__).resolve().parent.parent.parent.parent / "tmp" / "baseline-hashes.json").read_text()
)

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
```

- [ ] **Step 1.2: Run test to verify it fails**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/research && ../uhi8/bin/python -m pytest tests/data/test_frozen_loaders.py::test_il_proxy_hash_matches_baseline -v`
Expected: FAIL (file not found)

- [ ] **Step 1.3: Create il_proxy.json**

Write a script `tmp/freeze_il_proxy.py` that reads from the current hardcoded `IL_MAP`, wraps in canonical JSON format with metadata, computes SHA-256, and writes to `research/data/frozen/il_proxy.json`:

```python
import hashlib, json, sys
sys.path.insert(0, "research")
from econometrics.data import IL_MAP

data = {k: v for k, v in IL_MAP.items()}
canon = json.dumps(data, sort_keys=True, separators=(",", ":"))
sha = hashlib.sha256(canon.encode()).hexdigest()

frozen = {
    "metadata": {
        "source": "derived",
        "derivation": "IL proxy: daily impermanent loss estimate for ETH/USDC 30bps pool. Derivation methodology documented in research/data/frozen/README.md. Original label: Q5 IL proxy.",
        "executed_at": "2026-03-05",
        "row_count": len(data),
        "sha256": sha
    },
    "data": data
}

with open("research/data/frozen/il_proxy.json", "w") as f:
    json.dump(frozen, f, indent=2)
print(f"Wrote il_proxy.json: {len(data)} days, sha256={sha[:16]}...")
```

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python tmp/freeze_il_proxy.py`

- [ ] **Step 1.4: Run hash test to verify frozen file matches**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/research && ../uhi8/bin/python -m pytest tests/data/test_frozen_loaders.py::test_il_proxy_hash_matches_baseline -v`
Expected: PASS

- [ ] **Step 1.5: Swap IL_MAP in data.py to loader**

In `research/econometrics/data.py`:

**First**, add the shared loader infrastructure after the existing imports (after `from typing import Final`). This goes ONCE at the top and is reused by Steps 2.5 and 3.5:

```python
import json as _json
from pathlib import Path as _Path

_FROZEN = _Path(__file__).resolve().parent.parent / "data" / "frozen"

def _load_frozen(name: str):
    return _json.loads((_FROZEN / name).read_text())
```

**Then**, replace the hardcoded `IL_MAP` dict (lines 10-26):
```python
# ── Q5 IL proxy: day -> il_proxy ──
IL_MAP: Final[dict[str, float]] = {
    "2025-12-05": 0.0117, ...
}
```
With:
```python
# ── Q5 IL proxy: loaded from canonical frozen JSON ──
IL_MAP: Final[dict[str, float]] = _load_frozen("il_proxy.json")["data"]
```

**Note:** Steps 2.5 and 3.5 only replace data blocks — they reuse the `_load_frozen` defined here.

- [ ] **Step 1.6: Run loader test**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/research && ../uhi8/bin/python -m pytest tests/data/test_frozen_loaders.py::test_il_proxy_loader_matches_baseline -v`
Expected: PASS

- [ ] **Step 1.7: REGRESSION GATE — Level 3 (full test suite)**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/research && ../uhi8/bin/python -m pytest tests/ -v 2>&1 | tail -5`
Expected: 139+ passed (new tests added), 0 failed

- [ ] **Step 1.8: REGRESSION GATE — Level 2 (duration model)**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/research && ../uhi8/bin/python -m econometrics.run_duration 2>&1 | head -20`
Expected: beta_a_t ≈ 5.34, R² ≈ 0.58 (identical to baseline)

- [ ] **Step 1.9: Commit**

```bash
git add research/data/frozen/il_proxy.json research/econometrics/data.py research/tests/data/
git commit -m "feat(provenance): migrate IL_MAP to canonical frozen JSON

Extract IL_MAP from hardcoded dict to data/frozen/il_proxy.json with
SHA-256 hash and metadata. Loader in data.py preserves identical API.
All 139+ tests pass, duration model output unchanged."
```

---

## Task 2: Migrate DAILY_AT_MAP + DAILY_AT_NULL_MAP

**Files:**
- Create: `research/data/frozen/daily_at.json`
- Modify: `research/econometrics/data.py:251-342` (the AT maps)
- Test: `research/tests/data/test_frozen_loaders.py` (add tests)

- [ ] **Step 2.1: Add failing tests to test_frozen_loaders.py**

```python
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
```

- [ ] **Step 2.2: Run test to verify it fails**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/research && ../uhi8/bin/python -m pytest tests/data/test_frozen_loaders.py::test_daily_at_hash_matches_baseline -v`
Expected: FAIL

- [ ] **Step 2.3: Create daily_at.json**

Write freeze script `tmp/freeze_daily_at.py`:

```python
import hashlib, json, sys
sys.path.insert(0, "research")
from econometrics.data import DAILY_AT_MAP, DAILY_AT_NULL_MAP

def canon(obj): return json.dumps(obj, sort_keys=True, separators=(",", ":"))
def sha(obj): return hashlib.sha256(canon(obj).encode()).hexdigest()

real = {k: v for k, v in DAILY_AT_MAP.items()}
null = {k: v for k, v in DAILY_AT_NULL_MAP.items()}
data = {"real": real, "null": null}

frozen = {
    "metadata": {
        "source": "dune",
        "query_id": 6783604,
        "parameters": {
            "pool_address": "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",
            "start_date": "2025-12-05",
            "end_date": "2026-01-14"
        },
        "executed_at": "2026-03-05",
        "row_count": len(real),
        "sha256": sha(data)
    },
    "data": data
}
with open("research/data/frozen/daily_at.json", "w") as f:
    json.dump(frozen, f, indent=2)
print(f"Wrote daily_at.json: {len(real)} days")
```

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python tmp/freeze_daily_at.py`

- [ ] **Step 2.4: Run hash test**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/research && ../uhi8/bin/python -m pytest tests/data/test_frozen_loaders.py::test_daily_at_hash_matches_baseline -v`
Expected: PASS

- [ ] **Step 2.5: Swap DAILY_AT_MAP + DAILY_AT_NULL_MAP in data.py to loaders**

Replace lines 251-342 (the two hardcoded dicts + comments) with:

```python
# ── Daily pool-level A_T: loaded from canonical frozen JSON ──
# Original: Dune query 6783604, per-position Collect fees joined with Burn+Mint
_daily_at_data = _load_frozen("daily_at.json")
DAILY_AT_MAP: Final[dict[str, float]] = _daily_at_data["data"]["real"]

# ── Null A_T: Ma & Crapis equal-share (x_k=1/N) from SAME position set ──
DAILY_AT_NULL_MAP: Final[dict[str, float]] = _daily_at_data["data"]["null"]
```

- [ ] **Step 2.6: Run loader test**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/research && ../uhi8/bin/python -m pytest tests/data/test_frozen_loaders.py::test_daily_at_loader_matches_baseline -v`
Expected: PASS

- [ ] **Step 2.7: REGRESSION GATE — Levels 2+3**

Run tests: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/research && ../uhi8/bin/python -m pytest tests/ -v 2>&1 | tail -5`
Run duration: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/research && ../uhi8/bin/python -m econometrics.run_duration 2>&1 | head -20`
Expected: all pass, identical output

- [ ] **Step 2.8: Commit**

```bash
git add research/data/frozen/daily_at.json research/econometrics/data.py research/tests/data/test_frozen_loaders.py
git commit -m "feat(provenance): migrate DAILY_AT_MAP and DAILY_AT_NULL_MAP to frozen JSON

Extract both A_T maps to data/frozen/daily_at.json (Dune 6783604).
Loader preserves identical API. All tests pass, duration output unchanged."
```

---

## Task 3: Migrate RAW_POSITIONS

**Files:**
- Create: `research/data/frozen/positions.json`
- Modify: `research/econometrics/data.py:28-249` (RAW_POSITIONS)
- Test: `research/tests/data/test_frozen_loaders.py` (add tests)

- [ ] **Step 3.1: Add failing tests**

```python
def test_positions_hash_matches_baseline():
    frozen = json.loads((FROZEN_DIR / "positions.json").read_text())
    assert _sha(frozen["data"]) == BASELINE["positions"]
    assert frozen["metadata"]["source"] == "frozen_original"
    assert frozen["metadata"]["row_count"] == 600

def test_positions_loader_matches_baseline():
    from econometrics.data import RAW_POSITIONS
    assert _sha([[d, bl, at] for d, bl, at in RAW_POSITIONS]) == BASELINE["positions"]
    assert len(RAW_POSITIONS) == 600
    # Verify tuple structure preserved
    assert isinstance(RAW_POSITIONS[0], tuple)
    assert isinstance(RAW_POSITIONS[0][0], str)
    assert isinstance(RAW_POSITIONS[0][1], int)
    assert isinstance(RAW_POSITIONS[0][2], float)
```

- [ ] **Step 3.2: Run test to verify it fails**

Expected: FAIL

- [ ] **Step 3.3: Create positions.json**

Write `tmp/freeze_positions.py`:

```python
import hashlib, json, sys
sys.path.insert(0, "research")
from econometrics.data import RAW_POSITIONS

data = [[d, bl, at] for d, bl, at in RAW_POSITIONS]
canon = json.dumps(data, sort_keys=True, separators=(",", ":"))
sha = hashlib.sha256(canon.encode()).hexdigest()

frozen = {
    "metadata": {
        "source": "frozen_original",
        "original_label": "Q4v2 position data (600 rows from pagination)",
        "reconstruction_query_id": 6847717,
        "reconstruction_note": "NFT-based reconstruction returns 618 rows with ~4x blocklife scale. Directional robustness confirmed: beta_a_t same sign and significance. See tmp/econometrics-comparison-report.md.",
        "pool": "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",
        "pool_name": "ETH/USDC 30bps",
        "date_range": ["2025-12-05", "2026-01-14"],
        "format": ["burn_date", "blocklife", "exit_day_a_t"],
        "executed_at": "2026-03-05",
        "row_count": len(data),
        "sha256": sha
    },
    "data": data
}
with open("research/data/frozen/positions.json", "w") as f:
    json.dump(frozen, f, indent=2)
print(f"Wrote positions.json: {len(data)} rows, sha256={sha[:16]}...")
```

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python tmp/freeze_positions.py`

- [ ] **Step 3.4: Run hash test**

Expected: PASS

- [ ] **Step 3.5: Swap RAW_POSITIONS in data.py to loader**

Replace lines 28-249 (the entire RAW_POSITIONS block) with:

```python
# ── Q4v2 position data: loaded from canonical frozen JSON ──
# Original query lost. Reconstruction: Dune 6847717 (directional match confirmed).
# Format: (burn_date, blocklife, exit_day_a_t)
_positions_data = _load_frozen("positions.json")
RAW_POSITIONS: Final[list[tuple[str, int, float]]] = [
    (str(r[0]), int(r[1]), float(r[2])) for r in _positions_data["data"]
]
```

- [ ] **Step 3.6: Run loader test**

Expected: PASS

- [ ] **Step 3.7: REGRESSION GATE — Levels 2+3**

Run tests + duration model. Expected: identical to baseline.

- [ ] **Step 3.8: Commit**

```bash
git add research/data/frozen/positions.json research/econometrics/data.py research/tests/data/test_frozen_loaders.py
git commit -m "feat(provenance): migrate RAW_POSITIONS to frozen JSON

Extract 600 position rows to data/frozen/positions.json. Source: frozen_original
(Q4v2 query lost; reconstruction Dune 6847717 confirms directional robustness).
All tests pass, duration model output unchanged."
```

---

## Task 4: Migrate SELECTED_POOLS

**Files:**
- Create: `research/data/frozen/selected_pools.json`
- Modify: `research/econometrics/cross_pool/data.py:13-27`
- Test: `research/tests/data/test_frozen_loaders.py`

- [ ] **Step 4.1: Add failing tests**

```python
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
```

- [ ] **Step 4.2: Run test to verify it fails**

- [ ] **Step 4.3: Create selected_pools.json**

Write `tmp/freeze_selected_pools.py` following the same pattern. Metadata: `source: "subgraph"`, `query_file: "data/queries/subgraph/pool-discovery.graphql"`, `selection: "top 100 by TVL, 2-4-4 stratification"`.

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python tmp/freeze_selected_pools.py`

- [ ] **Step 4.4: Run hash test — PASS**

- [ ] **Step 4.5: Swap SELECTED_POOLS in cross_pool/data.py to loader**

Replace lines 13-27 with a loader that reads from `selected_pools.json` and reconstructs `PoolInfo` objects:

```python
_FROZEN = _Path(__file__).resolve().parent.parent.parent / "data" / "frozen"
def _load_frozen(name: str):
    return _json.loads((_FROZEN / name).read_text())

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
```

- [ ] **Step 4.6: Run loader test + REGRESSION GATE — Levels 2+3**

- [ ] **Step 4.7: Commit**

```bash
git add research/data/frozen/selected_pools.json research/econometrics/cross_pool/data.py research/tests/data/test_frozen_loaders.py
git commit -m "feat(provenance): migrate SELECTED_POOLS to frozen JSON

Extract 10 selected pools to data/frozen/selected_pools.json (GraphQL subgraph).
All tests pass."
```

---

## Task 5: Migrate POOL_CONCENTRATIONS

**Files:**
- Create: `research/data/frozen/cross_pool_concentrations.json`
- Modify: `research/econometrics/cross_pool/data.py:31-45`
- Test: `research/tests/data/test_frozen_loaders.py`

- [ ] **Step 5.1: Add failing tests**

```python
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
```

- [ ] **Step 5.2: Run test to verify it fails**

- [ ] **Step 5.3: Create cross_pool_concentrations.json**

Write `tmp/freeze_cross_pool.py`. Metadata: `source: "dune"`, `query_id: 6784588`, `parameters: {"pools": [list of 10 addresses], "window_days": 90}`.

- [ ] **Step 5.4: Run hash test — PASS**

- [ ] **Step 5.5: Swap POOL_CONCENTRATIONS in cross_pool/data.py to loader**

Replace lines 31-45. The loader reads concentrations and matches pools by address (robust to ordering changes):

```python
_conc_data = _load_frozen("cross_pool_concentrations.json")
_pool_by_addr = {p.address: p for p in SELECTED_POOLS}
POOL_CONCENTRATIONS: Final[list[PoolConcentration]] = [
    PoolConcentration(
        pool=_pool_by_addr[c["pool_address"]],
        a_t=c["a_t"], a_t_null=c["a_t_null"], delta_plus=c["delta_plus"],
        n_positions=c["n_positions"], n_removals=c["n_removals"],
        window_days=c["window_days"]
    )
    for c in _conc_data["data"]
]
```

- [ ] **Step 5.6: Run loader test + REGRESSION GATE — Levels 2+3**

- [ ] **Step 5.7: Commit**

```bash
git add research/data/frozen/cross_pool_concentrations.json research/econometrics/cross_pool/data.py research/tests/data/test_frozen_loaders.py
git commit -m "feat(provenance): migrate POOL_CONCENTRATIONS to frozen JSON

Extract 10 pool concentration records to data/frozen/cross_pool_concentrations.json
(Dune 6784588, parameterized). All tests pass."
```

---

## Task 6: Migrate PER_POSITION_DATA

**Files:**
- Create: `research/data/frozen/per_position_fees.json`
- Modify: `research/econometrics/per_position_data.py`
- Test: `research/tests/data/test_frozen_loaders.py`

- [ ] **Step 6.1: Add failing tests**

```python
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
```

- [ ] **Step 6.2: Run test to verify it fails**

- [ ] **Step 6.3: Create per_position_fees.json**

Write `tmp/freeze_per_position.py`. Metadata: `source: "dune"`, `query_id: 6815916`, `execution_id: "01KKFB8WHX57FX0G5PG0QB0HWJ"`.

- [ ] **Step 6.4: Run hash test — PASS**

- [ ] **Step 6.5: Swap PER_POSITION_DATA to loader**

Replace the entire hardcoded tuple with:

```python
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
```

- [ ] **Step 6.6: Run loader test + REGRESSION GATE — Levels 2+3**

- [ ] **Step 6.7: Commit**

```bash
git add research/data/frozen/per_position_fees.json research/econometrics/per_position_data.py research/tests/data/test_frozen_loaders.py
git commit -m "feat(provenance): migrate PER_POSITION_DATA to frozen JSON

Extract 50 per-position fee records to data/frozen/per_position_fees.json
(Dune 6815916, lifetime fees methodology). All tests pass."
```

---

## Task 7: Migrate FCI V4 Events

**Files:**
- Create: `research/data/frozen/fci_v4_events.json`
- Modify: `research/data/scripts/fci_oracle.py:360`
- Delete: `research/data/raw/fci_weth_usdc_v4_events.json` (after verification)

- [ ] **Step 7.1: Create fci_v4_events.json**

Write `tmp/freeze_fci_v4.py` that reads `data/raw/fci_weth_usdc_v4_events.json`, wraps in canonical format. The `data` field preserves the original structure (with `"events"`, `"pool"`, `"forkBlock"` keys) so the oracle's `raw["events"]` access on line 370 continues to work without modification.

```python
import hashlib, json
from pathlib import Path

raw_path = Path("research/data/raw/fci_weth_usdc_v4_events.json")
with open(raw_path) as f:
    original = json.load(f)

# data preserves the full original structure
data = original
canon = json.dumps(data, sort_keys=True, separators=(",", ":"))
sha = hashlib.sha256(canon.encode()).hexdigest()

frozen = {
    "metadata": {
        "source": "dune",
        "query_id": 6795594,
        "parameters": {
            "pool_id": "0x4f88f7c99022eace4740c6898f59ce6a2e798a1e64ce54589720b7153eb224a7",
            "block_range": [23656000, 23668000]
        },
        "executed_at": "2026-03-05",
        "event_count": len(original.get("events", [])),
        "sha256": sha
    },
    "data": data
}
with open("research/data/frozen/fci_v4_events.json", "w") as f:
    json.dump(frozen, f, indent=2)
print(f"Wrote fci_v4_events.json, sha256={sha[:16]}...")
```

- [ ] **Step 7.2: Update fci_oracle.py read path**

In `research/data/scripts/fci_oracle.py:360`, change:
```python
input_path = project_root / "data" / "raw" / "fci_weth_usdc_v4_events.json"
```
To:
```python
input_path = project_root / "data" / "frozen" / "fci_v4_events.json"
```

And update the JSON loading to unwrap the canonical format (the `data` field contains the original structure with `events`, `pool`, etc.):
```python
with open(input_path, "r") as f:
    raw = json.load(f)
# Unwrap canonical frozen format — data preserves original structure
if "metadata" in raw and "data" in raw:
    raw = raw["data"]
```

The oracle then continues with `events = raw["events"]` on line 370 unchanged.

- [ ] **Step 7.3: Re-run oracle to verify fixture is unchanged**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python research/data/scripts/fci_oracle.py`
Then: `sha256sum research/data/fixtures/fci_weth_usdc_v4.json`
Compare against pre-migration hash.

- [ ] **Step 7.4: REGRESSION GATE — Level 5 (Solidity tests)**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && forge test --match-path "test/fee-concentration-index/**" -vv`
Expected: all pass

- [ ] **Step 7.5: Remove data/raw/fci_weth_usdc_v4_events.json**

```bash
git rm research/data/raw/fci_weth_usdc_v4_events.json
```

- [ ] **Step 7.6: Commit**

```bash
git add research/data/frozen/fci_v4_events.json research/data/scripts/fci_oracle.py
git commit -m "feat(provenance): migrate FCI V4 events to frozen JSON

Move raw events from data/raw/ to data/frozen/fci_v4_events.json (Dune 6795594).
Oracle updated to read from frozen path. Fixture output unchanged.
Forge tests pass."
```

---

## Task 8: Frozen README + Queries README Update

**Files:**
- Create: `research/data/frozen/README.md`
- Modify: `research/data/queries/README.md`

- [ ] **Step 8.1: Write data/frozen/README.md**

Document: canonical JSON format, all 7 datasets with their sources, IL_MAP derivation methodology, RAW_POSITIONS reconstruction note, how to run `verify_provenance.py`.

- [ ] **Step 8.2: Update data/queries/README.md**

Add: frozen JSON references, complete query ID table (from spec appendix), link to verify_provenance.py, link to comparison report.

- [ ] **Step 8.3: Commit**

```bash
git add research/data/frozen/README.md research/data/queries/README.md
git commit -m "docs(provenance): add frozen data README and update queries README

Documents canonical JSON format, all 7 datasets with query IDs,
IL_MAP derivation, RAW_POSITIONS reconstruction, and verification procedure."
```

---

## Task 9: Verification Script

**Files:**
- Create: `research/data/scripts/verify_provenance.py`

- [ ] **Step 9.1: Write verify_provenance.py**

The script:
1. Reads each `data/frozen/*.json`
2. For `source: "derived"` or `source: "frozen_original"`: verify SHA-256 hash only
3. For `source: "dune"`: print query ID and parameters for manual re-execution (Dune API integration is optional — the reviewer can paste the SQL from `data/queries/` into Dune UI)
4. For `source: "subgraph"`: print the GraphQL query path
5. Summary table with pass/fail per dataset

- [ ] **Step 9.2: Run verify_provenance.py**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python research/data/scripts/verify_provenance.py`
Expected: all 7 datasets verified

- [ ] **Step 9.3: Commit**

```bash
git add research/data/scripts/verify_provenance.py
git commit -m "feat(provenance): add verify_provenance.py for reviewer verification

Single-command script to verify all 7 frozen datasets: hash integrity
for derived/frozen_original, query references for Dune/subgraph-backed."
```

---

## Task 10: Final Regression Gate (All 5 Levels)

- [ ] **Step 10.1: Level 1 — Hash verification**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && uhi8/bin/python research/data/scripts/verify_provenance.py`

- [ ] **Step 10.2: Level 2 — Econometrics results**

Run duration model and compare to baseline snapshot in `tmp/econometrics-baseline-snapshot.md`.

- [ ] **Step 10.3: Level 3 — Full test suite**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/research && ../uhi8/bin/python -m pytest tests/ -v`
Expected: 139+ passed, 0 failed

- [ ] **Step 10.4: Level 4 — Notebooks**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && make notebooks` (or equivalent headless execution)
Verify key numeric outputs match baseline.

- [ ] **Step 10.5: Level 5 — Solidity tests**

Run: `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev && forge test --match-path "test/fee-concentration-index/**" -vv`
Expected: all pass

- [ ] **Step 10.6: Clean up tmp/ freeze scripts**

Remove `tmp/freeze_*.py`, `tmp/generate_baseline.py`, and `tmp/baseline-hashes.json` (one-time migration tools). Update `test_frozen_loaders.py` to compute expected hashes inline from the frozen JSON files instead of reading from `tmp/baseline-hashes.json`, so the tests remain self-contained after cleanup.

- [ ] **Step 10.7: Final commit**

```bash
git add -A
git commit -m "chore(provenance): complete data provenance migration — all 5 regression levels pass

7 datasets migrated to canonical frozen JSON:
- 4 Dune-backed (daily_at, cross_pool, per_position, fci_v4_events)
- 1 subgraph-backed (selected_pools)
- 1 derived (il_proxy)
- 1 frozen_original (positions, Q4v2 lost, reconstruction verified)

Verification: verify_provenance.py confirms all hashes.
Regression: 139+ tests pass, duration model identical, notebooks unchanged, forge tests pass."
```
