# Data Provenance: Canonical JSON + Loader Pattern

**Date**: 2026-03-17
**Branch**: 008-uniswap-v3-reactive-integration
**Status**: Approved

## Problem

All empirical data backing the ThetaSwap econometric analysis is hardcoded in Python source files (`econometrics/data.py`, `econometrics/cross_pool/data.py`, `econometrics/per_position_data.py`). This data originates from Dune SQL queries and a GraphQL subgraph query, but there is no formal chain linking query → frozen result → model output. For academic peer review, a reviewer must be able to independently verify the data by re-running queries and confirming the econometric results are preserved.

## Approach

**Canonical JSON + Loader Pattern**: Extract all hardcoded data into self-documenting JSON files under `data/frozen/`. Each file includes metadata (query ID, parameters, execution date, SHA-256 hash of the data payload). The Python data files become thin loaders that read from JSON. A verification script re-runs the 6 query-backed datasets and diffs against frozen snapshots.

## Non-Negotiable Constraint: 5-Level Regression Gate

Every single dataset migration must pass all 5 levels before proceeding to the next. No exceptions.

### Level 1 — Raw Data Equality
Serialize the current hardcoded Python object to canonical JSON, compute SHA-256, verify the frozen JSON loader produces a byte-identical hash.

### Level 2 — Econometrics Result Equality
Before touching anything, snapshot all current model outputs:
- `estimation_result.json` (beta, p-value, pseudo_R², WTP)
- `estimation_result_lagged.json` (all 5 specs + predictive)
- `duration_result.json` (beta_a_t, beta_il, R², mean blocklife)
- Cross-pool analysis outputs (spearman rho, architecture decision)

After each loader swap, re-run the econometrics pipeline and diff against these snapshots. Any deviation is a hard fail.

### Level 3 — Test Suite Green
All 139 Python tests must pass before and after each swap. Not at the end — after each individual dataset migration.

### Level 4 — Notebook Output Equality
Run all 5 notebooks headless (`make notebooks`), capture cell outputs before and after. Key numeric outputs (coefficients, p-values, plot data) must match.

### Level 5 — Solidity Test Pass
`forge test` must pass. The FCI fixture consumed by the differential fork test must remain identical.

## Canonical JSON File Format

Each frozen dataset is a JSON file under `data/frozen/` with this structure:

```json
{
  "metadata": {
    "source": "dune | subgraph | derived",
    "query_id": 6783604,
    "parameters": {},
    "executed_at": "2026-03-05",
    "row_count": 41,
    "sha256": "<hex digest of canonicalized data array>"
  },
  "data": [ ... ]
}
```

The `sha256` is computed over the `data` array only (canonicalized: sorted keys, no whitespace), so metadata changes don't invalidate the hash.

For `il_proxy.json`, `source` is `"derived"` and metadata includes a `derivation` field documenting how the values were computed instead of a `query_id`.

## Frozen Datasets

| Frozen JSON | Replaces | Query Source | Type |
|---|---|---|---|
| `data/frozen/positions.json` | `data.py:RAW_POSITIONS` | Original Q4v2 lost; reconstruction Dune 6847717 | frozen_original |
| `data/frozen/daily_at.json` | `data.py:DAILY_AT_MAP + DAILY_AT_NULL_MAP` | Dune 6783604 | query-backed |
| `data/frozen/il_proxy.json` | `data.py:IL_MAP` | Derived (documented) | derived |
| `data/frozen/cross_pool_concentrations.json` | `cross_pool/data.py:POOL_CONCENTRATIONS` | Dune 6784588 (parameterized ×10 pools) | query-backed |
| `data/frozen/selected_pools.json` | `cross_pool/data.py:SELECTED_POOLS` | GraphQL subgraph (Uniswap V3) | query-backed |
| `data/frozen/per_position_fees.json` | `per_position_data.py:PER_POSITION_DATA` | Dune 6815916 | query-backed |
| `data/frozen/fci_v4_events.json` | `data/raw/fci_weth_usdc_v4_events.json` | Dune 6795594 | query-backed |

### Special Case: RAW_POSITIONS (positions.json)

The original Dune query ("Q4v2") that produced the 600-row `RAW_POSITIONS` dataset is lost. An NFT-based reconstruction (Dune 6847717) was attempted using `NonfungiblePositionManager` events, producing 618 rows from the same pool and date range. However, the reconstruction differs from the original:

- **Blocklife scale**: NFT query returns ~4x larger blocklifes (mean 159K vs 36K blocks)
- **Row count**: 618 vs 600 (NFT is a superset)
- **exit_day_a_t**: Differs but is unused downstream (all code discards it via `_exit_at`)

**Robustness verification** (see `tmp/econometrics-comparison-report.md`):
- Duration model `beta_a_t`: +5.34 (original) vs +6.29 (NFT) — same sign, both p≈0
- Hazard model `beta_a_t`: -5.44 vs -4.92 — same sign, neither significant with clustered SEs
- All coefficients maintain the same sign across both datasets

**Provenance strategy**: `positions.json` uses `source: "frozen_original"` with metadata field `reconstruction_query_id: 6847717`. The verification script performs hash-only verification (like `il_proxy.json`), not query re-execution. The comparison report is included as supporting evidence for reviewers.

## Loader Pattern

The 3 hardcoded Python files become thin loaders. The public API (variable names, types) stays identical — zero downstream changes.

Example for `econometrics/data.py`:

```python
"""Frozen Dune data — loaded from canonical JSON files."""
from pathlib import Path
import json
from typing import Final

_FROZEN = Path(__file__).resolve().parent.parent / "data" / "frozen"

def _load(name: str) -> dict:
    return json.loads((_FROZEN / name).read_text())["data"]

RAW_POSITIONS: Final[list[tuple[str, int, float]]] = [tuple(r) for r in _load("positions.json")]
DAILY_AT_MAP: Final[dict[str, float]] = _load("daily_at.json")["real"]
DAILY_AT_NULL_MAP: Final[dict[str, float]] = _load("daily_at.json")["null"]
IL_MAP: Final[dict[str, float]] = _load("il_proxy.json")
```

Same pattern for `cross_pool/data.py` and `per_position_data.py`.

## Verification Script

`data/scripts/verify_provenance.py` — a single script a reviewer can run:

1. For each frozen JSON file, reads metadata (query ID, parameters)
2. Re-executes the query via Dune API / GraphQL
3. Normalizes the fresh result (sort rows, consistent key ordering, consistent numeric precision)
4. Compares against the frozen `data` payload
5. Reports match/mismatch per dataset, row-level diff if mismatched

For `il_proxy.json` (derived) and `positions.json` (frozen_original), the script skips query re-execution and only verifies SHA-256 hash integrity.

**Query re-execution semantics**: All query-backed datasets use time-bounded parameters (fixed date ranges, block ranges, or pool addresses). These queries target historical on-chain events which are immutable, so re-execution should produce identical results regardless of when it's run. The `parameters` field in metadata captures these bounds. For `cross_pool_concentrations.json` (Dune 6784588), the query uses a rolling 90-day window — re-execution will produce different results. The verification script uses the frozen parameters to set the query window to the original execution date.

Output format:
```
Provenance Verification Report
==============================
positions.json         ✓ hash verified (frozen_original, reconstruction: Dune 6847717)
daily_at.json          ✓  41/41  days match (Dune 6783604)
il_proxy.json          ✓ hash verified (derived, no query)
cross_pool.json        ✓  10/10  pools match (Dune 6784588, parameterized)
per_position_fees.json ✓  50/50  rows match (Dune 6815916)
selected_pools.json    ✓  10/10  pools match (GraphQL subgraph)
fci_v4_events.json     ✓ 107/107 events match (Dune 6795594)
```

## File Layout

### New files
```
research/data/frozen/
  positions.json
  daily_at.json
  il_proxy.json
  cross_pool_concentrations.json
  selected_pools.json
  per_position_fees.json
  fci_v4_events.json
  README.md                        # Documents format, IL_MAP derivation

research/data/scripts/verify_provenance.py
```

### Modified files (loader swap)
- `econometrics/data.py` — hardcoded dicts → JSON loaders
- `econometrics/cross_pool/data.py` — same
- `econometrics/per_position_data.py` — same

### Deleted files
- `data/raw/fci_weth_usdc_v4_events.json` — content moves to `data/frozen/fci_v4_events.json`

### Unchanged
- All econometrics modules, backtest modules, notebooks, tests, Solidity tests, oracle scripts
- `data/fixtures/fci_weth_usdc_v4.json` (generated by oracle, stays as-is)
- `data/queries/` directory (queries preserved alongside frozen results)
- `data/scripts/fci_oracle.py` (updated to read from `data/frozen/fci_v4_events.json` instead of `data/raw/`)
- `foundry.toml` `fs_permissions` — no change needed. Solidity tests read from `data/fixtures/` (generated by oracle), not from `data/frozen/`. The oracle reads from `data/raw/` → `data/frozen/`, which is a Python-side path change only.

### Python Environment
All verification and regression gate commands must use the `uhi8/` venv:
- Tests: `cd research && ../uhi8/bin/python -m pytest tests/ -v`
- Duration model: `cd research && ../uhi8/bin/python -m econometrics.run_duration`
- Notebooks: verify `make notebooks` target uses `uhi8/bin/jupyter` (update Makefile if needed)

## Migration Order

One dataset at a time. Each must pass the 5-level regression gate before proceeding.

1. `IL_MAP` — derived, simplest (no query to wire up)
2. `DAILY_AT_MAP` + `DAILY_AT_NULL_MAP` — same source JSON
3. `RAW_POSITIONS`
4. `SELECTED_POOLS`
5. `POOL_CONCENTRATIONS`
6. `PER_POSITION_DATA`
7. `fci_v4_events` — raw events → frozen (also update `fci_oracle.py` read path)

## Queries README Update

Update `data/queries/README.md` to:
- Reference the frozen JSON files as the canonical snapshots
- Document query IDs: 4 Dune (6783604, 6784588, 6815916, 6795594) + 1 GraphQL subgraph + 1 reconstruction (6847717)
- Note `IL_MAP` derivation and `RAW_POSITIONS` frozen_original status
- Link to `verify_provenance.py` as the one-command reproducibility check
- Link to `tmp/econometrics-comparison-report.md` as robustness evidence for positions reconstruction

## Appendix: Known Query IDs

| Dataset | Dune Query ID | Status |
|---------|--------------|--------|
| `DAILY_AT_MAP` + `DAILY_AT_NULL_MAP` | 6783604 | Verified, active |
| `POOL_CONCENTRATIONS` | 6784588 | Verified, parameterized |
| `PER_POSITION_DATA` | 6815916 | Verified, active |
| FCI V4 events | 6795594 | Verified, active |
| `RAW_POSITIONS` (reconstruction) | 6847717 | NFT-based, directional match only |
| `RAW_POSITIONS` (original Q4v2) | Unknown | Lost |
| `IL_MAP` | N/A | Derived, no query |
| `SELECTED_POOLS` | N/A | GraphQL subgraph, `data/queries/subgraph/pool-discovery.graphql` |
