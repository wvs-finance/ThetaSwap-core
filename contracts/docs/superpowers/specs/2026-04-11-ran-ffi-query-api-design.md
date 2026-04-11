# RAN FFI Query API + Schema Upgrade — Design Spec

Date: 2026-04-11
Branch: ran-growth-pipeline
Status: Reviewed (3-way: Code Reviewer, Reality Checker, Technical Writer)

## Problem

The RAN vault needs differential fuzz tests that compare off-chain `globalGrowth` data (from DuckDB) against on-chain values (via `vm.rollFork`). Solidity fork tests call Python scripts via `ffiPython()` (BaseTest.sol L118). The current `ran_growth_query.py` outputs JSON — not ABI-encoded bytes that Solidity can decode. Additionally, the schema lacks `block_timestamp` which the fuzz test needs for `vm.rollFork` context.

## Naming Conventions

| Layer | Convention | Example |
|-------|-----------|---------|
| DuckDB columns | snake_case | `block_timestamp`, `pool_id` |
| Python variables | snake_case | `block_timestamp`, `pool_id` |
| ABI encoding | positional (not named) | `abi.encode(uint256, uint256, bytes32)` |
| CLI flags | kebab-case | `--pool`, `--db` |
| Solidity camelCase | only in Solidity consumer (out of scope) | `blockTimestamp` |

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Timestamp source | `eth_getBlockByNumber(hex_block, false)` per block | Real timestamps, no full tx data |
| Pipeline change | Modify existing pipeline (Option B) | Avoid maintaining two code paths |
| Batch strategy | Combined JSON-RPC batch (30 calls) | Single HTTP request, 540 CU/batch, 1.08s delay |
| UPSERT strategy | `ON CONFLICT DO UPDATE SET block_timestamp WHERE NULL` | Backfills timestamps without overwriting existing globalGrowth |
| FFI output format | `0x`-prefixed hex string to stdout | Matches existing `eip712.py` pattern and Forge `vm.ffi()` convention |
| FFI call pattern | Two subcommands: `len` + `row` | Avoids OOG from loading full dataset |
| FFI `--pool` argument | Raw bytes32 pool ID (hex string) | Solidity passes `vm.toString(poolId)` directly — no registry name lookup |
| Scripts-only scope | No .sol files touched | Non-intrusive to contracts |

## Alchemy Budget Impact

| Item | CU Cost | % of 30M Monthly |
|------|---------|-------------------|
| Already spent (globalGrowth backfill) | 752K | 2.5% |
| Timestamp backfill (37,606 blocks × 16 CU) | 602K | 2.0% |
| **Total after both backfills** | **1.35M** | **4.5%** |
| Ongoing daily (144 blocks × 36 CU) | 5.2K/day | 0.52%/month |
| **Monthly worst case** | **1.5M** | **5.0%** |
| Headroom remaining | 28.5M | 95% |

**CUPS rate check:** 15 × 20 CU (storage) + 15 × 16 CU (block) = 540 CU/batch. At 500 CUPS limit: minimum delay = 540/500 = 1.08s. The raw delay (1.08s) exceeds the safety floor (1.0s), so the floor has no effect.

**Rate limiter behavior:** The delay must be computed from the **total batch CU** (540), not from a per-call average. The existing rate limiter takes per-call parameters — the implementation plan must define how to bridge this (e.g., pass the pre-computed total directly, or restructure the API). This is a function-level decision for the plan, not this spec.

## Schema Change

### Before
```
accumulator_samples (
    block_number    UBIGINT,
    pool_id         VARCHAR,
    global_growth   VARCHAR,
    sampled_at      TIMESTAMP,
    stride          USMALLINT,
    PRIMARY KEY (pool_id, block_number)
)
```

### After (new databases via CREATE TABLE)
```
accumulator_samples (
    block_number    UBIGINT,
    pool_id         VARCHAR,
    global_growth   VARCHAR,
    block_timestamp UBIGINT,       -- NEW: Ethereum block timestamp (unix seconds)
    sampled_at      TIMESTAMP,
    stride          USMALLINT,
    PRIMARY KEY (pool_id, block_number)
)
```

**Note on migrated databases:** `ALTER TABLE ADD COLUMN` appends `block_timestamp` to the END (after `stride`), not at position 4 as shown above. This is fine — all queries use named columns, never positional. New databases from `CREATE_TABLE_DDL` will have the column at position 4.

**DDL exists in TWO locations:** `ran_utils.py` (`CREATE_TABLE_DDL`) AND `conftest.py` (local copy). BOTH must be updated to add `block_timestamp`. The conftest copy exists for test isolation — it does not import from `ran_utils`.

### UPSERT SQL (updated)
```sql
INSERT INTO accumulator_samples (block_number, pool_id, global_growth, block_timestamp, sampled_at, stride)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT (pool_id, block_number)
DO UPDATE SET block_timestamp = excluded.block_timestamp
WHERE accumulator_samples.block_timestamp IS NULL
```

This means:
- New rows: inserted with all fields including `block_timestamp`
- Existing rows with NULL `block_timestamp`: timestamp gets filled, `globalGrowth` untouched
- Existing rows with non-NULL `block_timestamp`: completely untouched

**Migration note:** This replaces the current `ON CONFLICT DO NOTHING` with `DO UPDATE SET ... WHERE IS NULL`. This is a deliberate behavioral change. Existing idempotency tests still pass because: (1) `global_growth` is never in the UPDATE SET clause, so it cannot be overwritten; (2) the WHERE clause prevents updating non-NULL timestamps; (3) re-inserting the same row with the same timestamp is a no-op since `block_timestamp` is already non-NULL.

## Pipeline Changes (`ran_growth_pipeline.py`)

### Batch construction
Each batch combines two RPC call types in one JSON-RPC array for a given set of block numbers:
- N × `eth_getStorageAt` — params: `[address, slot_hex, block_hex]`
- N × `eth_getBlockByNumber` — params: `[block_hex, false]` (false = no full tx objects)
- Total: 2N calls per HTTP request (default N=15, so 30 calls)

**ID scheme for mixed batches:** IDs are **batch-local** (reset to 1 for each batch, not globally sequential). Within a single batch: storage calls get IDs `1..N`, block calls get IDs `N+1..2N`. For block `i` (0-indexed) in the batch: storage ID = `i+1`, block ID = `N+i+1`. The correlator determines call type from the ID range: IDs ≤ N are storage responses, IDs > N are block responses.

**`eth_getBlockByNumber` request format:**
```json
{"jsonrpc": "2.0", "id": 16, "method": "eth_getBlockByNumber", "params": ["0x15ecb09", false]}
```

**`eth_getBlockByNumber` response format:**
```json
{"jsonrpc": "2.0", "id": 16, "result": {"timestamp": "0x66a3b1c0", "number": "0x15ecb09", ...}}
```

The `timestamp` field is a hex-encoded unix timestamp in seconds. Parse via `int(result["timestamp"], 16)`.

**Null result handling:** If `eth_getBlockByNumber` returns `{"result": null}` (e.g., future block), the pipeline must skip that block and log a warning to stderr. Do not crash — other blocks in the batch may be valid.

### Response correlation
The correlator must handle mixed response types in a single batch:
- IDs `1..N` → `eth_getStorageAt` responses: extract `result` as hex string (globalGrowth)
- IDs `N+1..2N` → `eth_getBlockByNumber` responses: extract `result.timestamp` as hex string

Both are correlated back to their block number. The output for each block is a pair: `(global_growth_hex, block_timestamp_int)`.

### Rate limiter update
The rate limiter must receive the total CU per batch (540), not a per-call average. The implementation should either:
- Pass `batch_cu_total=540` to a new overload, or
- Compute `15 * 20 + 15 * 16 = 540` and pass it as the total

The `SAFETY_FLOOR_SECONDS` (1.0s) is below the computed 1.08s, so the floor does not clamp. No change to the floor constant needed.

### Smart resume update
`filter_missing_blocks` must consider a block "existing" ONLY if both conditions are met:
- The row exists in DuckDB
- `block_timestamp IS NOT NULL`

Updated query behavior:
```sql
SELECT block_number FROM accumulator_samples
WHERE pool_id = ? AND block_number IN (SELECT UNNEST(?))
AND block_timestamp IS NOT NULL
```

Blocks with NULL `block_timestamp` are treated as "missing" and will be re-fetched (the UPSERT fills only the timestamp, preserving `globalGrowth`).

## FFI Query Script (`ran_ffi.py`)

### Subcommand: `len`

```
.venv/bin/python3 -m scripts.ran_ffi len --pool <poolId_hex> --db <path>
```

Output: `0x`-prefixed hex string of `abi.encode(uint256)` — the count of ALL rows for that pool, including rows with NULL `block_timestamp`. This is intentional: `len` defines the index space (0..N-1), and index semantics must be stable regardless of backfill state. The `row` subcommand handles NULLs via a post-fetch check, not by filtering.

**Contrast with `filter_missing_blocks`:** The pipeline's smart resume query uses `AND block_timestamp IS NOT NULL` to find blocks needing re-fetch. The FFI `len` query does NOT filter NULLs. These are different use cases — do not copy-paste one into the other.

`--pool` accepts a raw bytes32 hex pool ID (with or without `0x` prefix). This is what Solidity's `vm.toString(poolId)` produces. The script normalizes to `0x`-prefixed lowercase before querying DuckDB.

### Subcommand: `row`

```
.venv/bin/python3 -m scripts.ran_ffi row --pool <poolId_hex> --idx <n> --db <path>
```

Output: `0x`-prefixed hex string of `abi.encode(uint256, uint256, bytes32)`:
- `uint256 blockNumber`
- `uint256 blockTimestamp`
- `bytes32 globalGrowth`

**Critical encoding note:** `globalGrowth` is stored in DuckDB as a hex string (e.g., `"0x0000...1234"`). Before ABI encoding as `bytes32`, it MUST be converted to a `bytes` object: `bytes.fromhex(global_growth[2:])`. Passing the hex string directly to `eth_abi.encode` will raise `EncodingTypeError`.

Rows are ordered by `block_number ASC`. Index 0 = earliest block, index N-1 = latest.

### Behavior

- `len` queries: `SELECT count(*) FROM accumulator_samples WHERE pool_id = ?`
- `row` queries: `SELECT block_number, block_timestamp, global_growth FROM accumulator_samples WHERE pool_id = ? ORDER BY block_number LIMIT 1 OFFSET ?`
- Output is `0x`-prefixed hex — matches existing `eip712.py` FFI convention and Forge's `vm.ffi()` expectation. Without `0x` prefix, Forge treats output as raw UTF-8 bytes, producing garbage.
- Uses `eth_abi.encode` for ABI encoding (convert hex strings to `bytes` for `bytes32` type)
- Zero network calls — DuckDB read-only
- Invalid index (>= len) → exit 1 with error to stderr
- Missing/unknown pool ID → exit 1 with error to stderr
- NULL `block_timestamp` for the requested row → exit 1 with "run pipeline to backfill timestamps"
- The `row` query does NOT filter NULL timestamps in SQL. The NULL check is a post-fetch assertion so that index semantics remain stable regardless of backfill state.

## Error Handling

| Error Condition | Expected Behavior |
|----------------|-------------------|
| Unknown pool ID (not in DuckDB) | Exit 1, stderr: "pool not found" |
| Index out of bounds (>= row count) | Exit 1, stderr shows valid range 0..N-1 |
| DuckDB file not found | Exit 1, clean error (no traceback) |
| NULL block_timestamp in requested row | Exit 1, "run pipeline to backfill timestamps" |
| Invalid subcommand (not len/row) | Exit 1, show usage |
| eth_getBlockByNumber returns null result | Pipeline: skip block, log warning (don't crash) |
| Alchemy auth failure (HTTP 401) | Pipeline: RpcBatchError caught, exit 1 |

## Conftest / Fixture Updates

The mock transport (`MockRpcTransport`) must be extended:
- Add `eth_getBlockByNumber` handler that returns `{"result": {"timestamp": hex_timestamp, "number": hex_block}}`. Only `timestamp` and `number` are accessed by the pipeline — the mock may omit all other block fields (`hash`, `parentHash`, etc.)
- The factory fixture must accept a `block_timestamps: dict[int, int]` parameter mapping block_number → unix_timestamp
- Default timestamps: deterministic values starting from `1_700_000_000`, incrementing by `600` (50 blocks × 12s) per stride-50 block

The `populated_db_path` fixture must insert `block_timestamp` values matching the mock timestamp data.

## Files Changed

| File | Change |
|------|--------|
| `contracts/scripts/ran_utils.py` | `CREATE_TABLE_DDL` — add `block_timestamp UBIGINT` column |
| `contracts/scripts/ran_growth_pipeline.py` | Batch construction (add `eth_getBlockByNumber`), correlation (handle mixed responses), insert_sample (add `block_timestamp`), UPSERT SQL, smart resume (NULL timestamp detection), rate limiter (540 CU total) |
| `contracts/scripts/tests/conftest.py` | DDL update, mock transport `eth_getBlockByNumber` handler, fixture timestamps, `populated_db_path` with timestamps |
| `contracts/scripts/tests/test_ran_growth_pipeline.py` | ~15 tests: add `block_timestamp` to insert_sample calls, test combined batch correlation, test NULL-timestamp resume |
| Create: `contracts/scripts/ran_ffi.py` | FFI query script with `len` and `row` subcommands |
| Create: `contracts/scripts/tests/test_ran_ffi.py` | Tests for both subcommands, ABI encoding validation, `0x` prefix verification |

**Scripts-only scope enforced.** No `.sol`, `foundry.toml`, or contract files touched.

## Testing Strategy (TDD)

### Schema upgrade tests
- UPSERT fills NULL `block_timestamp` without overwriting `globalGrowth`
- UPSERT leaves non-NULL `block_timestamp` untouched
- Smart resume detects rows with NULL `block_timestamp` as "missing" (query uses `AND block_timestamp IS NOT NULL`)
- Smart resume treats rows with non-NULL `block_timestamp` as "existing" (not re-fetched)
- Combined batch (storage + block) correlates correctly — IDs 1..N are storage, N+1..2N are block
- `eth_getBlockByNumber` responses parsed for `result.timestamp` field
- Null block result (future block) is skipped without crashing

### FFI query tests
- `len` returns correct count as `0x`-prefixed ABI-encoded uint256
- `len` output round-trips: `eth_abi.decode(['uint256'], bytes.fromhex(output[2:]))` matches expected count
- `row` at index 0 returns earliest block with correct blockNumber, blockTimestamp, globalGrowth
- `row` at index N-1 returns latest block
- `row` output round-trips: `eth_abi.decode(['uint256', 'uint256', 'bytes32'], bytes.fromhex(output[2:]))` matches expected values
- `row` globalGrowth decoded as `bytes32` matches the original hex string from DuckDB
- Invalid index → exit 1
- Unknown pool → exit 1
- NULL timestamp → exit 1
- Non-existent DB file → exit 1
- Zero network dependency (no httpx/requests imports)
- Output starts with `0x` (prefix verification)

Tests use real `globalGrowth` values from the existing DuckDB data and fixture data. Mocks only for HTTP transport.

## Out of Scope

- Solidity test contract consuming the FFI API (separate spec, different branch scope)
- Additional metrics (outsideBelow, outsideAbove, currentTick)
- Multiple pool fetching (WETH_USDT)
- Query by timestamp (only query by index)
- Concurrent reads during pipeline writes (DuckDB single-writer lock prevents this)
