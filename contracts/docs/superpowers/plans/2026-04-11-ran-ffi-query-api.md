# RAN FFI Query API + Schema Upgrade — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **REQUIRED SKILL:** Invoke `functional-python` before writing any Python code.
>
> **Agent:** Data Engineer implements ALL tasks. Code Reviewer + Reality Checker review.

---

> ## NON-NEGOTIABLE RULES — ALL AGENTS MUST READ
>
> ### Rule 1: STRICT TDD — One Behavior at a Time
> Write test → verify FAILS → implement MINIMAL → verify PASSES → next behavior.
>
> ### Rule 2: NO MERGE WITHOUT APPROVAL
> Code stays uncommitted until user approves.
>
> ### Rule 3: ALL commands from `contracts/`
> `cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts && .venv/bin/python3 -m pytest ...`
>
> ### Rule 4: SCRIPTS-ONLY SCOPE
> ONLY touch `contracts/scripts/`, `contracts/data/`, `contracts/.gitignore`. NEVER `.sol`, `foundry.toml`.
>
> ### Rule 5: REAL DATA OVER MOCKS
> Use real `globalGrowth` values from fixtures. Mock ONLY HTTP transport and error codes.

---

**Goal:** Add `block_timestamp` to the pipeline schema, update batch fetching to include `eth_getBlockByNumber`, and create an FFI query script (`ran_ffi.py`) for Solidity fork test consumption.

**Architecture:** Two pieces — (1) schema upgrade + pipeline modification for timestamp fetching/backfill, (2) new FFI script with `len` and `row` subcommands outputting `0x`-prefixed ABI-encoded hex.

**Tech Stack:** Python 3.13, DuckDB, httpx, eth_abi, pytest

**Spec:** `contracts/docs/superpowers/specs/2026-04-11-ran-ffi-query-api-design.md`

---

## Execution Phases

| Phase | Task | Agent | Dependency |
|-------|------|-------|------------|
| 1 — Schema + Fixtures | Task 1 | Data Engineer | None |
| 2 — Pipeline Upgrade | Task 2 | Data Engineer | Task 1 |
| 3 — FFI Script | Task 3 | Data Engineer | Task 1 |
| 4 — Backfill Run | Task 4 | Data Engineer | Task 2 |

Tasks 2 and 3 can run in parallel after Task 1 (different files).

---

## Task 1: Schema Upgrade + Fixture Updates

**Agent:** Data Engineer
**Files:**
- Modify: `contracts/scripts/ran_utils.py` (`CREATE_TABLE_DDL`)
- Modify: `contracts/scripts/tests/conftest.py` (DDL, mock transport, fixtures)
- Modify: `contracts/scripts/tests/test_ran_growth_pipeline.py` (update existing tests for new schema)

### Steps — DDL upgrade

- [ ] **Step 1: Update `CREATE_TABLE_DDL` in `ran_utils.py`**

Add `block_timestamp UBIGINT` column between `global_growth` and `sampled_at`. Run existing tests — they should FAIL because conftest DDL doesn't match.

- [ ] **Step 2: Update conftest DDL + fixtures**

Update conftest's local `CREATE_TABLE_DDL` to match. Add `MOCK_BLOCK_TIMESTAMPS` constant: deterministic values starting at `1_700_000_000`, incrementing by `600` per stride-50 block, one per key in `MOCK_BLOCKS_AND_GROWTH`. Update `populated_db_path` INSERT to include `block_timestamp`. Update `duckdb_conn` and `duckdb_file_conn` to use new DDL.

- [ ] **Step 3: Add `eth_getBlockByNumber` to mock transport**

Extend `MockRpcTransport._handle_single_rpc` to handle `eth_getBlockByNumber` method. Return `{"result": {"timestamp": hex(ts), "number": hex(block)}}` using `MOCK_BLOCK_TIMESTAMPS`. Add a `block_timestamps` parameter to the factory fixture (default: `MOCK_BLOCK_TIMESTAMPS`). For blocks not in the map, return `{"result": null}`.

- [ ] **Step 4: Update existing pipeline tests for 6-column schema**

All `insert_sample` calls in `test_ran_growth_pipeline.py` need the `block_timestamp` parameter. Update each call site. Run full suite — all 74 existing tests should PASS with the new schema.

- [ ] **Step 5: Verify and commit**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/ -v`
Expected: ALL tests PASS.

```
git add contracts/scripts/ran_utils.py contracts/scripts/tests/conftest.py contracts/scripts/tests/test_ran_growth_pipeline.py
git commit -m "feat(ran-pipeline): schema upgrade — add block_timestamp column"
```

---

## Task 2: Pipeline Upgrade — Combined Batches, Correlation, Smart Resume

**Agent:** Data Engineer
**Files:**
- Modify: `contracts/scripts/ran_growth_pipeline.py`
- Modify: `contracts/scripts/tests/test_ran_growth_pipeline.py`
**Prerequisite:** Task 1 merged.

### Steps — one behavior at a time, strict TDD:

### UPSERT migration (DO NOTHING → DO UPDATE SET)

- [ ] **Step 1: Write failing test for conditional UPSERT**

Test that inserting a row with NULL `block_timestamp`, then re-inserting with a timestamp, fills ONLY the timestamp. `global_growth` must be preserved. A third insert with a different timestamp must NOT overwrite the now-non-NULL timestamp.

- [ ] **Step 2: Verify FAILS** (current UPSERT uses DO NOTHING)
- [ ] **Step 3: Update `_UPSERT_SQL` to `ON CONFLICT DO UPDATE SET block_timestamp WHERE IS NULL`**

Also update `insert_sample` to accept `block_timestamp` parameter.

- [ ] **Step 4: Verify PASSES**

### Combined batch construction

- [ ] **Step 5: Write failing test for combined batch**

Given 3 blocks, the batch builder should produce a JSON-RPC array of 6 calls: 3 `eth_getStorageAt` (IDs 1-3) + 3 `eth_getBlockByNumber` (IDs 4-6). Verify method names, params format (`[hex_block, false]` for block calls), and batch-local IDs.

- [ ] **Step 6: Verify FAILS**
- [ ] **Step 7: Implement combined batch builder**

Either modify `build_rpc_batches` or add a new `build_combined_rpc_batches` function. Each batch contains N storage + N block calls with IDs 1..N and N+1..2N respectively.

- [ ] **Step 8: Verify PASSES**

### Mixed response correlation

- [ ] **Step 9: Write failing test for mixed correlation**

Given a combined batch response (storage + block responses, possibly shuffled), the correlator must return a mapping of `block_number → (global_growth_hex, block_timestamp_int)`. Test with ordered and shuffled responses. Use mock transport with `shuffle=True`.

- [ ] **Step 10: Verify FAILS**
- [ ] **Step 11: Implement mixed correlator**

Determine call type from ID range (≤N = storage, >N = block). For storage: extract `result` as hex. For block: extract `result["timestamp"]` as int. Join by block number.

- [ ] **Step 12: Verify PASSES**

### Null block result handling

- [ ] **Step 13: Write failing test for null block result**

Mock transport returns `{"result": null}` for one block's `eth_getBlockByNumber` response. Pipeline should skip that block (not crash), log warning to stderr. Other blocks in the batch succeed.

- [ ] **Step 14: Verify FAILS**
- [ ] **Step 15: Implement null-result skip**
- [ ] **Step 16: Verify PASSES**

### Rate limiter update

- [ ] **Step 17: Write failing test for 540 CU batch delay**

With combined batches (15 storage + 15 block = 540 CU), the computed delay must be >= 1.08s. Test that the rate limiter accepts total batch CU.

- [ ] **Step 18: Verify FAILS**
- [ ] **Step 19: Update rate limiter**

Add a way to pass total batch CU directly (e.g., `compute_inter_batch_delay(batch_cu_total=540, cups_limit=500)` or restructure). The existing per-call API can remain for backward compat if needed.

- [ ] **Step 20: Verify PASSES**

### Smart resume NULL-timestamp detection

- [ ] **Step 21: Write failing test for NULL-timestamp resume**

Pre-populate DuckDB with rows that have `global_growth` but NULL `block_timestamp`. Run `filter_missing_blocks` — these blocks must be returned as "missing" even though the row exists. Use `duckdb_file_conn`.

- [ ] **Step 22: Verify FAILS**
- [ ] **Step 23: Update `filter_missing_blocks` SQL**

Add `AND block_timestamp IS NOT NULL` to the existing-block query.

- [ ] **Step 24: Verify PASSES**

### CLI main() integration

- [ ] **Step 25: Write integration test for combined pipeline**

End-to-end test: mock transport returns both storage values and block timestamps. Pipeline writes both to DuckDB. Verify rows have non-NULL `block_timestamp` and correct `global_growth`.

- [ ] **Step 26: Verify FAILS**
- [ ] **Step 27: Update `main()` to use combined batches**

Compose: `build_combined_rpc_batches` → `send_rpc_batch` → mixed correlator → `insert_sample` with timestamp → commit per batch. Update rate limiter call to use 540 CU total.

- [ ] **Step 28: Verify PASSES**

### Full suite verification

- [ ] **Step 29: Run ALL tests**

`cd contracts && .venv/bin/python3 -m pytest scripts/tests/ -v`
ALL must PASS.

- [ ] **Step 30: Commit**

```
git add contracts/scripts/ran_growth_pipeline.py contracts/scripts/tests/test_ran_growth_pipeline.py
git commit -m "feat(ran-pipeline): combined batch fetch with block timestamps, smart resume"
```

---

## Task 3: FFI Query Script — `ran_ffi.py`

**Agent:** Data Engineer
**Files:**
- Create: `contracts/scripts/ran_ffi.py`
- Create: `contracts/scripts/tests/test_ran_ffi.py`
**Prerequisite:** Task 1 merged. Can run in parallel with Task 2.

### Steps — one behavior at a time, strict TDD:

### `len` subcommand

- [ ] **Step 1: Write failing test for `len`**

Call `ran_ffi.py len --pool <USDC_WETH_pool_id> --db <populated_db_path>`. Verify output starts with `0x`. Decode via `eth_abi.decode(['uint256'], bytes.fromhex(output[2:]))` and verify count matches expected row count in fixture DB.

- [ ] **Step 2: Verify FAILS**
- [ ] **Step 3: Implement `len` subcommand**

argparse with subparsers (`len`, `row`). `--pool` accepts raw hex (normalize to `0x`-prefix lowercase). `--db` required. Query DuckDB: `SELECT count(*) FROM accumulator_samples WHERE pool_id = ?`. Output `0x` + `eth_abi.encode(['uint256'], [count]).hex()` to stdout.

- [ ] **Step 4: Verify PASSES**

### `row` subcommand — exact values

- [ ] **Step 5: Write failing test for `row` at index 0**

Call `ran_ffi.py row --pool <pool_id> --idx 0 --db <populated_db_path>`. Decode output as `(uint256, uint256, bytes32)`. Verify `blockNumber` matches earliest block in fixture, `blockTimestamp` matches fixture timestamp, `globalGrowth` bytes32 matches original hex from DuckDB.

- [ ] **Step 6: Verify FAILS**
- [ ] **Step 7: Implement `row` subcommand**

Query: `SELECT block_number, block_timestamp, global_growth FROM accumulator_samples WHERE pool_id = ? ORDER BY block_number LIMIT 1 OFFSET ?`. Convert `global_growth` hex to bytes: `bytes.fromhex(growth[2:])`. ABI encode: `eth_abi.encode(['uint256', 'uint256', 'bytes32'], [block_num, timestamp, growth_bytes])`. Output `0x` + hex.

- [ ] **Step 8: Verify PASSES**

### `row` at last index

- [ ] **Step 9: Write failing test for `row` at index N-1**

Verify returns the latest block with correct values.

- [ ] **Step 10: Verify FAILS → PASSES** (should pass with existing implementation)

### `0x` prefix verification

- [ ] **Step 11: Write test verifying both `len` and `row` output starts with `0x`**
- [ ] **Step 12: Verify PASSES**

### Error: invalid index

- [ ] **Step 13: Write failing test for out-of-bounds index**

`--idx` >= row count → exit 1, stderr shows valid range.

- [ ] **Step 14: Verify FAILS**
- [ ] **Step 15: Implement bounds check**
- [ ] **Step 16: Verify PASSES**

### Error: unknown pool

- [ ] **Step 17: Write failing test for unknown pool**

`--pool 0xdead...` (not in DB) → exit 1, stderr: "pool not found".

- [ ] **Step 18: Verify FAILS**
- [ ] **Step 19: Implement pool check**
- [ ] **Step 20: Verify PASSES**

### Error: NULL timestamp

- [ ] **Step 21: Write failing test for NULL block_timestamp**

Pre-populate DB with a row where `block_timestamp IS NULL`. Query that row via `--idx` → exit 1, stderr: "run pipeline to backfill timestamps".

- [ ] **Step 22: Verify FAILS**
- [ ] **Step 23: Implement post-fetch NULL check**
- [ ] **Step 24: Verify PASSES**

### Error: nonexistent DB

- [ ] **Step 25: Write failing test for missing DB file**

`--db /nonexistent/path.duckdb` → exit 1, clean error (no traceback).

- [ ] **Step 26: Verify FAILS**
- [ ] **Step 27: Implement DB open error handling**
- [ ] **Step 28: Verify PASSES**

### Zero network dependency

- [ ] **Step 29: Write test verifying no network imports**

AST-based check: module does not import `httpx`, `requests`, `urllib`, `socket`.

- [ ] **Step 30: Verify PASSES** (should pass if implemented correctly)

### Pool ID normalization

- [ ] **Step 31: Write test for `--pool` without `0x` prefix**

Pass bare hex (no `0x`). Verify same result as with `0x` prefix.

- [ ] **Step 32: Verify FAILS → implement normalization → PASSES**

### Full suite + commit

- [ ] **Step 33: Run ALL tests**

`cd contracts && .venv/bin/python3 -m pytest scripts/tests/ -v`
ALL must PASS.

- [ ] **Step 34: Commit**

```
git add contracts/scripts/ran_ffi.py contracts/scripts/tests/test_ran_ffi.py
git commit -m "feat(ran-pipeline): FFI query script with len + row subcommands"
```

---

## Task 4: Timestamp Backfill Run

**Agent:** Data Engineer (or user manual run)
**Prerequisite:** Tasks 1 + 2 merged. Requires `ALCHEMY_API_KEY`.

- [ ] **Step 1: ALTER TABLE on existing DuckDB**

```
cd contracts && .venv/bin/python3 -c "
import duckdb
conn = duckdb.connect('data/ran_accumulator.duckdb')
conn.execute('ALTER TABLE accumulator_samples ADD COLUMN IF NOT EXISTS block_timestamp UBIGINT')
print(conn.execute('SELECT count(*) FROM accumulator_samples WHERE block_timestamp IS NULL').fetchone())
conn.close()
"
```
Expected: `(37606,)` — all rows have NULL timestamp.

- [ ] **Step 2: Run pipeline to backfill timestamps**

```
.venv/bin/python3 -m scripts.ran_growth_pipeline --pool usdc-weth --from-block 22972937 --to-block latest --stride 50 --db data/ran_accumulator.duckdb
```

Smart resume detects 37,606 blocks with NULL timestamps as "missing" → re-fetches with combined batches → fills timestamps via UPSERT. ~45 min, 602K CU.

- [ ] **Step 3: Verify backfill**

```
.venv/bin/python3 -c "
import duckdb
conn = duckdb.connect('data/ran_accumulator.duckdb', read_only=True)
null_count = conn.execute('SELECT count(*) FROM accumulator_samples WHERE block_timestamp IS NULL').fetchone()
total = conn.execute('SELECT count(*) FROM accumulator_samples').fetchone()
sample = conn.execute('SELECT block_number, block_timestamp, global_growth FROM accumulator_samples WHERE block_timestamp IS NOT NULL ORDER BY block_number LIMIT 3').fetchall()
print(f'NULL timestamps: {null_count[0]} / {total[0]} total')
for s in sample: print(f'  Block {s[0]}: ts={s[1]}, growth={s[2][:30]}...')
"
```
Expected: 0 NULL timestamps, all rows have real block timestamps.

- [ ] **Step 4: Test FFI script against real data**

```
.venv/bin/python3 -m scripts.ran_ffi len --pool 0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657 --db data/ran_accumulator.duckdb
.venv/bin/python3 -m scripts.ran_ffi row --pool 0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657 --idx 0 --db data/ran_accumulator.duckdb
```

Verify both produce `0x`-prefixed hex output that decodes correctly.

---

## Coverage Checklist (Spec → Task Mapping)

| Spec Requirement | Task |
|-----------------|------|
| Schema: add `block_timestamp UBIGINT` | Task 1 |
| DDL in both `ran_utils.py` and `conftest.py` | Task 1 |
| UPSERT: DO NOTHING → DO UPDATE SET | Task 2, Steps 1-4 |
| Combined batch construction (storage + block) | Task 2, Steps 5-8 |
| Mixed response correlation (ID scheme) | Task 2, Steps 9-12 |
| Null block result handling | Task 2, Steps 13-16 |
| Rate limiter: 540 CU total | Task 2, Steps 17-20 |
| Smart resume: NULL-timestamp detection | Task 2, Steps 21-24 |
| CLI integration with combined batches | Task 2, Steps 25-28 |
| FFI `len` subcommand | Task 3, Steps 1-4 |
| FFI `row` subcommand | Task 3, Steps 5-10 |
| `0x` prefix verification | Task 3, Steps 11-12 |
| Error: invalid index | Task 3, Steps 13-16 |
| Error: unknown pool | Task 3, Steps 17-20 |
| Error: NULL timestamp | Task 3, Steps 21-24 |
| Error: nonexistent DB | Task 3, Steps 25-28 |
| Zero network dependency | Task 3, Steps 29-30 |
| Pool ID normalization (bare hex) | Task 3, Steps 31-32 |
| Mock transport: `eth_getBlockByNumber` handler | Task 1, Step 3 |
| Fixture timestamps: deterministic | Task 1, Step 2 |
| Timestamp backfill run | Task 4 |
| FFI against real data | Task 4, Step 4 |
