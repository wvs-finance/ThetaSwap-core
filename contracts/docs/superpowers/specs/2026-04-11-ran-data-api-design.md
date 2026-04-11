# RAN Data Query API + Notebook EDA — Design Spec

Date: 2026-04-11
Branch: ran-growth-pipeline
Status: Reviewed (3-way: Code Reviewer, Reality Checker, Technical Writer) — fixes applied

## Problem

The FFI script (`ran_ffi.py`) currently supports only `len` and `row` (by index). The Solidity differential fuzz test needs additional query patterns: lookup by timestamp, min/max boundaries, and range access. The notebook needs a clean Python API for EDA — not raw SQL. Both consumers need the same underlying query logic.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | New shared module `ran_data_api.py` | Single source of query logic for FFI + notebook |
| FFI max array size | 1,000 rows (96 KB ABI) | Safe for Forge memory; fuzz tests rarely need more |
| Timestamp lookup | Exact + nearest-lower (flag-based) | `exact=True` for strict tests, `exact=False` for fuzzy access |
| Notebook scope | Minimal EDA + test vector discovery | Finds edge cases for fuzz tests; visualizations by Analytics Reporter later |
| API style | Pure functions, frozen dataclasses | functional-python; DuckDB read-only, zero side effects |
| Scripts-only scope | No .sol files touched | Non-intrusive to contracts |

## Module Architecture

```
scripts/
├── ran_data_api.py          # NEW: shared query API (pure functions)
├── ran_ffi.py               # MODIFY: thin ABI wrapper over ran_data_api
├── ran_growth_query.py      # UNCHANGED
├── ran_utils.py             # UNCHANGED
└── tests/
    ├── test_ran_data_api.py # NEW: API tests
    └── test_ran_ffi.py      # MODIFY: tests for new subcommands

notebooks/
└── growthGlobal.ipynb       # MODIFY: use ran_data_api, add EDA for fuzz vectors
```

**Data flow:**
```
DuckDB (read-only) → ran_data_api.py → ran_ffi.py (ABI wrapper → Solidity FFI)
                                      → notebook (Python direct import → EDA)
```

## Data Types

**Frozen dataclass for query results:**
```
Row:
    block_number: int
    block_timestamp: int
    global_growth: str    # 0x-prefixed 66-char hex string representing a 32-byte value.
                          # Stored as VARCHAR in DuckDB. Encoded as bytes32 for ABI output
                          # via bytes.fromhex(global_growth[2:]).
```

**Exception class:**
```
QueryError(Exception):
    # Defined in ran_data_api.py at module level.
    # Subclasses Exception directly.
    # Carries only a message string (no structured fields).
    # FFI wrapper catches QueryError and exits with status 1 + stderr message.
    # Notebook lets QueryError propagate as a Python exception.
```

All API functions return `Row`, `list[Row]`, or `int`. No raw tuples, no dicts.

## API Surface (`ran_data_api.py`)

All functions are pure: take a DuckDB connection + parameters, return frozen dataclasses. No CLI, no ABI encoding, no I/O beyond DuckDB reads. No network calls.

**`pool_id` parameter:** Always the raw `0x`-prefixed hex pool ID string (as stored in DuckDB). Friendly name resolution (e.g., `"usdc-weth"` → `"0xe500..."`) happens at the caller layer (FFI script or notebook), NOT in this module.

### Core functions

**`dataset_len(conn, pool_id) → int`**
Count of ALL rows for the pool, including rows with NULL `block_timestamp`. This is intentional: `dataset_len` defines the index space (0..N-1), and index semantics must be stable regardless of backfill state.

**Note on NULL timestamps:** Some indices in `0..N-1` may have NULL `block_timestamp`. Calling `get_row` at those indices raises `QueryError`. Callers must handle this gracefully — the message says "run pipeline to backfill timestamps." After backfill, all indices are safe.

**`get_row(conn, pool_id, idx) → Row`**
Single row by index (0-based, ordered by `block_number ASC`).
- `idx < 0` → `QueryError` (validated at API layer, not just FFI)
- `idx >= dataset_len` → `QueryError`
- NULL `block_timestamp` in result → `QueryError` ("run pipeline to backfill timestamps")

**`get_by_timestamp(conn, pool_id, ts, exact=True) → Row`**
Lookup by `block_timestamp`.
- `exact=True`: exact match on `block_timestamp = ts`. Not found → `QueryError`.
- `exact=False`: nearest-lower match (`block_timestamp <= ts`). Below minimum → `QueryError`.
- NULL `block_timestamp` in result → `QueryError`
- **Tie-breaking:** If multiple rows share the same `block_timestamp`, return the one with the highest `block_number` (`ORDER BY block_timestamp DESC, block_number DESC LIMIT 1`).
- **Performance note:** No secondary index on `block_timestamp`. At current scale (~37K rows) a filtered scan is acceptable (<5ms in DuckDB). If dataset grows to 500K+, consider adding an index.

**`get_range(conn, pool_id, from_idx, to_idx) → list[Row]`**
Slice of rows from `from_idx` (inclusive) to `to_idx` (exclusive).
- Ordered by `block_number ASC`
- `to_idx - from_idx > 1000` → `QueryError` (FFI safety limit)
- `from_idx > to_idx` → `QueryError`
- `from_idx == to_idx` → returns empty list (not an error)
- Out of bounds (`from_idx < 0` or `to_idx > dataset_len`) → `QueryError`
- For notebook use: `get_all` has no limit

**`get_min(conn, pool_id) → Row`**
Row with the smallest `block_number` for the pool. Unknown pool → `QueryError`.

**`get_max(conn, pool_id) → Row`**
Row with the largest `block_number` for the pool. Unknown pool → `QueryError`.

**`get_all(conn, pool_id) → list[Row]`**
All rows for the pool, ordered by `block_number ASC`. **Not exposed via FFI** — notebook-only. No size limit. At 37K rows (~15MB Python objects) this is fine. If dataset grows past 500K rows, consider a streaming/pagination alternative.

### Error handling

All errors raise `QueryError` (defined in `ran_data_api.py`, subclasses `Exception`, message-only). The FFI wrapper catches `QueryError` and exits with status 1 + stderr message. The notebook lets them propagate as Python exceptions.

**DB connection boundary:** The API functions take an open `conn` parameter. They do NOT open or close the database. "DuckDB file not found" errors are handled at the **FFI layer** (in `_open_db`), not in the API. The API error table below reflects this.

## FFI Subcommands (`ran_ffi.py`)

Refactored to be a thin wrapper: parse args → open DB (`_open_db` stays in FFI) → call `ran_data_api` → ABI-encode → `print("0x" + hex)`. Connection lifecycle (`_open_db`, `conn.close()`) remains in the FFI script.

**Solidity integration note:** The `row` subcommand returns `(blockNumber, blockTimestamp, globalGrowth)` as a combined tuple from a single FFI call. This is a deliberate deviation from the TODO_DATA_ANALYSIS.md example which shows three separate calls (`getBlockNumber`, `getBlockTimestamp`, `getGlobalGrowth`). The combined approach is more gas-efficient and simpler. The Solidity test contract decodes the tuple: `abi.decode(result, (uint256, uint256, bytes32))`.

### Existing (refactored internals, same CLI interface)

| Subcommand | Output | API function |
|-----------|--------|-------------|
| `len --pool <id> --db <path>` | `abi.encode(uint256)` | `dataset_len` |
| `row --pool <id> --idx <n> --db <path>` | `abi.encode(uint256, uint256, bytes32)` | `get_row` |

### New subcommands

| Subcommand | Output | API function |
|-----------|--------|-------------|
| `row-by-ts --pool <id> --ts <n> --db <path> [--nearest]` | `abi.encode(uint256, uint256, bytes32)` | `get_by_timestamp(exact=not nearest)` |
| `range --pool <id> --from <n> --to <n> --db <path>` | `abi.encode(uint256, uint256[], uint256[], bytes32[])` | `get_range` (max 1000) |
| `min --pool <id> --db <path>` | `abi.encode(uint256, uint256, bytes32)` | `get_min` |
| `max --pool <id> --db <path>` | `abi.encode(uint256, uint256, bytes32)` | `get_max` |

**All output:** `0x`-prefixed hex. `globalGrowth` as `bytes32` (hex string → `bytes.fromhex(growth[2:])`).

**`range` output format:** `abi.encode(uint256, uint256[], uint256[], bytes32[])` = (count, blockNumbers[], blockTimestamps[], globalGrowths[]). Count is redundant with array lengths but matches the `len` convention for Solidity convenience. Solidity decode: `abi.decode(result, (uint256, uint256[], uint256[], bytes32[]))`.

**`--pool`** accepts raw bytes32 hex (with or without `0x` prefix). Normalized to `0x`-prefixed lowercase.

## Notebook EDA (`notebooks/growthGlobal.ipynb`)

**Kernel:** `ran-venv` (Python 3.13, already registered).

**Imports:** `from scripts.ran_data_api import ...` via `sys.path` manipulation (same pattern as existing notebook).

**No raw SQL.** All queries through `ran_data_api`. Existing cells that use raw SQL must be migrated to API calls. The existing stale note "block_timestamp: PENDING" must be removed (schema upgrade already done).

### EDA Sections

**1. Load and summary stats** — `dataset_len`, `get_min`, `get_max`, `get_all` → pandas DataFrame

**2. Correctness checks:**
- `globalGrowth` monotonically non-decreasing — print summary count of violations + list first 10 violating indices
- `block_timestamp` increases with `block_number` — print summary count of inversions + list first 10
- Zero-value regions identified (where `global_growth == "0x" + "0"*64`) — print block ranges

**3. Edge case discovery (fuzz test vectors):**
- Largest single-stride growth delta (index of max spike)
- First non-zero growth block (first settlement)
- Last block before a long flat region (defined as: 10+ consecutive strides with zero growth delta)
- Timestamp gaps > expected stride (600s for stride-50)
- Min/max `globalGrowth` as Q128 float

**4. Minimal visualizations (matplotlib):**
- Cumulative growth over block number
- Growth delta distribution (histogram)
- Timestamp gap distribution

**5. Test vector summary:**
Prints specific `(idx, blockNumber, blockTimestamp, globalGrowth)` tuples worth testing on-chain. These are the golden test vectors for the differential fuzz test.

**Integration note:** Full visualization buildout is done by the **Analytics Reporter** agent in a future session. This notebook provides only the minimum needed for fuzz test design.

## Files Changed

| File | Change |
|------|--------|
| Create: `contracts/scripts/ran_data_api.py` | Shared query API module with `QueryError`, `Row`, 7 query functions |
| Create: `contracts/scripts/tests/test_ran_data_api.py` | API tests |
| Modify: `contracts/scripts/ran_ffi.py` | Refactor to wrap ran_data_api, add 4 new subcommands, keep `_open_db` |
| Modify: `contracts/scripts/tests/test_ran_ffi.py` | Tests for new subcommands |
| Modify: `contracts/scripts/tests/conftest.py` | Add `large_populated_db_path` fixture with 1001+ rows for range limit test |
| Modify: `contracts/notebooks/growthGlobal.ipynb` | Migrate raw SQL to ran_data_api, add EDA sections, fix stale notes |

**Scripts-only scope enforced.** No `.sol`, `foundry.toml`, or contract files touched.

## Testing Strategy (TDD)

### `test_ran_data_api.py` — API unit tests

Tests open their own `duckdb.connect(populated_db_path, read_only=True)` connection — no new fixture needed for standard tests.

- `dataset_len` returns correct count
- `get_row` index 0 → earliest block
- `get_row` index N-1 → latest block
- `get_row` out of bounds → `QueryError`
- `get_row` negative index → `QueryError`
- `get_by_timestamp` exact match → correct row
- `get_by_timestamp` exact miss → `QueryError`
- `get_by_timestamp` nearest-lower → closest ≤ timestamp
- `get_by_timestamp` below minimum → `QueryError`
- `get_by_timestamp` tie-breaking → highest block_number wins
- `get_range` valid slice → correct rows in order
- `get_range` exceeds 1000 → `QueryError` (uses `large_populated_db_path` fixture with 1001+ rows)
- `get_range` out of bounds → `QueryError`
- `get_range` from > to → `QueryError`
- `get_range` from == to → empty list
- `get_min` → earliest row matches `get_row(0)`
- `get_max` → latest row matches `get_row(N-1)`
- `get_min` / `get_max` unknown pool → `QueryError`
- `get_all` → all rows, ordered, correct count
- NULL `block_timestamp` in any result → `QueryError`
- Zero network dependency (no httpx/requests imports)

### `test_ran_ffi.py` — new subcommand tests

- `row-by-ts --ts <exact>` → ABI round-trip matches
- `row-by-ts --ts <exact> --nearest` → nearest-lower match
- `row-by-ts --ts <miss>` → exit 1
- `range --from 0 --to 5` → ABI-decoded arrays match
- `range --from 0 --to 1001` → exit 1 (exceeds 1000, uses `large_populated_db_path`)
- `min` → ABI round-trip matches `get_min`
- `max` → ABI round-trip matches `get_max`

### Conftest fixture addition

**`large_populated_db_path`** — file-backed DuckDB with 1,050 rows (synthetic data at stride 50, starting from block 22,972,937). Used ONLY for testing the 1,000-row range limit independently from the out-of-bounds check. Regular tests use the existing `populated_db_path` (6 rows).

Tests use real fixture data from `populated_db_path` where possible. The large fixture uses synthetic but structurally valid data.

## Error Handling

| Error Condition | API behavior | FFI behavior |
|----------------|-------------|-------------|
| Unknown pool ID | Raise `QueryError` | Exit 1, stderr |
| Index out of bounds | Raise `QueryError` | Exit 1, stderr |
| Negative index | Raise `QueryError` | Exit 1, stderr |
| Timestamp not found (exact) | Raise `QueryError` | Exit 1, stderr |
| Below minimum timestamp | Raise `QueryError` | Exit 1, stderr |
| Range exceeds 1000 | Raise `QueryError` | Exit 1, stderr |
| Range from > to | Raise `QueryError` | Exit 1, stderr |
| NULL block_timestamp | Raise `QueryError` | Exit 1, stderr |
| DuckDB file not found | N/A (API takes open conn) | Exit 1, stderr (FFI `_open_db`) |

## Out of Scope

- Full visualization buildout (Analytics Reporter, future session)
- Solidity test contract consuming the FFI API (separate spec, different branch scope)
- Multiple pool support (WETH_USDT) — schema supports it, API is pool-parameterized
- Write operations — this is a read-only query API
- HTTP/FastAPI service — not needed for FFI + notebook consumers
- Secondary index on `block_timestamp` (scan acceptable at current 37K rows)
