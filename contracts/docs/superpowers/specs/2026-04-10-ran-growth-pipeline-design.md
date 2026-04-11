# RAN Growth Pipeline — Design Spec

Date: 2026-04-10
Branch: ran-v1a
Status: Reviewed (3-way × 2 rounds: Code Reviewer, Reality Checker, Technical Writer)

## Problem

Angstrom's `globalGrowth` accumulator is the core metric the RAN vault needs for reward attribution. It lives in contract storage with no events emitted. The current `freeze_ran_snapshots.py` fetches individual blocks via `cast storage` — fine for 4 blocks, unusable for historical backfill across ~2M blocks.

We need a Python data pipeline that bulk-fetches `globalGrowth` samples into a local analytical store, respecting Alchemy free tier constraints.

## Research Findings

No public indexer exposes `globalGrowth`. The Graph, Dune, Goldsky, Envio, Ponder — none work because Angstrom emits zero events. `eth_getStorageAt` via archive RPC is the only viable method. Full research: `contracts/.scratch/angstrom-indexer-globalGrowth-research.md`.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Metrics scope | `globalGrowth` only | Other metrics added as incremental schema additions later |
| Pool scope | USDC_WETH first, N-pool-ready schema | `pool_id` column from day one; adding pools = new rows, not migrations |
| Sampling | Fixed stride (default 50 blocks) | ~10 min resolution. Configurable. Fits comfortably in Alchemy free tier |
| Storage backend | DuckDB (local file) | Embedded, columnar, SQL, native Parquet export. Zero infrastructure |
| Bulk RPC | Python `httpx` JSON-RPC batches | No `web3.py` (heavy), no `cast` subprocess (slow). Direct batch calls |
| Single-block RPC | Keep `cast` subprocess | Forge FFI compatibility for existing test infrastructure |
| Approach | Conservative stride (Approach A) | Simple, robust, fits free tier budget |
| Development | TDD, functional-python | Tests first. Frozen dataclasses, pure functions, full typing |

## Naming Conventions

| Layer | Convention | Example |
|-------|-----------|---------|
| Solidity / contract-side | camelCase | `globalGrowth`, `poolId` |
| Python variables, args, columns | snake_case | `global_growth`, `pool_id` |
| DuckDB columns | snake_case | `global_growth`, `block_number` |
| CLI flags | kebab-case | `--from-block`, `--pool` |
| JSON output for Forge FFI | camelCase | `"globalGrowth"`, `"blockNumber"` |
| Module-level constants | UPPER_SNAKE | `ANGSTROM_HOOK`, `USDC_WETH_CONFIG` |

## Alchemy Free Tier Budget

| Constraint | Value |
|------------|-------|
| Monthly CU limit | 30,000,000 |
| Rate limit (CUPS) | 500 CU/second (rolling window, not strict per-second) |
| `eth_getStorageAt` cost | ~20 CU per call (verify at docs.alchemy.com before implementation) |
| Batch requests | Supported. CU = sum of individual calls |
| Archive access | Included, no surcharge |

**Budget for one full backfill (USDC_WETH, stride=50, ~2M blocks from block 22,972,937 to ~April 2026 head):**

BLOCK_NUMBER_0 (22,972,937) is approximately July 2025. At 7,200 blocks/day, ~270 days to April 2026 = ~1,944,000 blocks ≈ 2M.

- ~40,000 RPC calls × 20 CU = 800,000 CU (2.7% of monthly budget)
- Batches of 15 calls = ~2,667 HTTP requests
- At ~1 batch per 1.2s (with safety margin): **~53 minutes wall clock**
- Actual time will vary with HTTP latency; budget 60-70 minutes conservatively

**Batch size: 15 calls** (not 20). At 15 × 20 CU = 300 CU/batch, this provides 200 CU headroom below the 500 CUPS limit. If actual CU cost is 26 (Alchemy has varied historically), 15 × 26 = 390, still under 500.

## Configuration

**Pipeline RPC (`ran_growth_pipeline.py`):** Reads `ALCHEMY_API_KEY` from the environment and constructs the RPC URL as `https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}`. This matches `foundry.toml`'s `[rpc_endpoints]` convention. If `ALCHEMY_API_KEY` is not set, the pipeline exits with a clear error message.

**Single-block RPC (`ran_utils.read_storage_at`):** This function is used ONLY by `freeze_ran_snapshots.py` (not by the pipeline, which uses httpx directly). It retains the `cast` subprocess approach and accepts the RPC URL as a parameter — the caller provides it. `freeze_ran_snapshots.py` continues to construct the URL from `ALCHEMY_API_KEY` in its own `main()`. This keeps the shared utility pure (no env var reads) and lets callers decide their RPC source.

## Data Model

### Table: `accumulator_samples`

| Column | Type | Description |
|--------|------|-------------|
| `block_number` | `UBIGINT` | Ethereum block number |
| `pool_id` | `VARCHAR` | 0x-prefixed 66-char hex pool ID |
| `global_growth` | `VARCHAR` | 0x-prefixed 64-char hex (uint256, full fidelity) |
| `sampled_at` | `TIMESTAMP` | When the fetch was performed |
| `stride` | `USMALLINT` | Sampling stride used |

**Primary key:** `(pool_id, block_number)`

**Idempotent writes:** Re-runs with overlapping block ranges must be safe. Use conflict-ignoring insert semantics on the primary key so that existing rows are not overwritten. This enables crash recovery without checkpoint logic — just re-run the same command.

**Commit granularity:** The pipeline must commit to DuckDB after every batch (default). If the process crashes at batch 1,000 of 2,667, previously committed batches are preserved and the re-run skips them via the idempotent insert.

Design notes:
- `global_growth` as hex string: preserves uint256 fidelity, matches Forge `vm.parseJson` expectations
- `stride` column: coarse and dense samples coexist. Query by stride or ignore it
- Future metrics (outsideBelow, outsideAbove, currentTick, blockTimestamp) are additive columns — no schema rewrite needed
- DuckDB supports single-writer, multiple-reader. Two simultaneous pipeline runs will conflict — this is acceptable for a single-user tool

### Storage Location

```
contracts/data/
└── ran_accumulator.duckdb    # must be added to .gitignore
```

Parquet export for sharing/backup: `COPY accumulator_samples TO 'data/ran_accumulator.parquet'`

A `.gitignore` entry for `data/*.duckdb` and `data/*.parquet` must be added during implementation.

## Module Architecture

```
contracts/scripts/
├── ran_utils.py              # Shared utilities (extracted from freeze_ran_snapshots.py)
├── ran_growth_pipeline.py    # Bulk fetcher: httpx JSON-RPC → DuckDB
├── ran_growth_query.py       # Query interface: DuckDB → stdout (Forge FFI consumer)
└── freeze_ran_snapshots.py   # Existing script, refactored to import from ran_utils
```

### Agent Boundary Mapping

| Module | Owner Agent | Rationale |
|--------|-------------|-----------|
| `ran_utils.py` | Data Engineer | Shared ETL primitives, storage slot math, pool config |
| `ran_growth_pipeline.py` | Data Engineer | ETL pipeline, RPC batching, DuckDB writes |
| `ran_growth_query.py` | Senior Backend Developer | Query API, JSON output, FFI integration |
| `freeze_ran_snapshots.py` refactor | Senior Backend Developer | Integration with existing test infra |
| Pipeline tests | Data Engineer | `test_ran_utils.py`, `test_ran_growth_pipeline.py` |
| Query tests | Senior Backend Developer | `test_ran_growth_query.py` |
| Test fixtures (conftest) | Data Engineer (first), then shared | Must be implemented before either agent writes tests |

Analytics Reporter has no module in this spec — out of scope for this pipeline step. Will be relevant when analysis/reporting features are added on top of the stored data.

### Data Flow

```
[CLI args + ALCHEMY_API_KEY] → ran_growth_pipeline.py → [httpx batches] → Alchemy RPC
                                                       → [duckdb write]  → ran_accumulator.duckdb

[CLI args]                   → ran_growth_query.py     → [duckdb read]   → ran_accumulator.duckdb
                                                       → [JSON stdout]   → Forge FFI / analysis
```

Data Engineer owns everything left of DuckDB in the first flow.
Senior Backend Developer owns the second flow.
Both share `ran_utils.py` (Data Engineer implements, Backend Developer consumes).

## Expected Behaviors (Test-Driven)

These are the behaviors the implementation must satisfy. Tests are written first to assert these outcomes. The implementer decides the internal structure to make them pass.

### Shared Utilities (`ran_utils.py`)

**B-U1: Storage slot derivation correctness**
Given the USDC_WETH pool ID `0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657`, pool rewards slot `7`, and reward growth size `16777216`:
- The `globalGrowth` storage slot must equal `keccak256(abi.encode(poolId, 7)) + 16777216`
- Golden value: the base slot for this pool ID is `keccak256(abi.encode(0xe500...a657, 7))`. The implementer must compute this once using `eth_abi.encode` + `eth_hash.keccak`, hard-code it as a test literal, and assert the implementation matches. Do NOT write a test that re-implements the function and asserts it equals itself.
- Cross-verify: the computed slot must produce the same `globalGrowth` value as `AngstromAccumulatorConsumer.sol`'s `globalGrowth()` function for the same pool

**B-U2: Hex encoding round-trip**
For any uint256 value `v` in `[0, 2^256 - 1]`:
- Encoding to hex produces a string of exactly 66 characters (0x + 64 hex digits)
- Decoding that string back produces exactly `v`
- Zero is encoded as `"0x" + "0" * 64`, not `"0x0"`

**B-U3: Pool configuration completeness**
- A pool config for USDC_WETH must contain: pool ID (str), pool rewards slot (int), reward growth size (int), human name (str)
- USDC_WETH pool ID: `0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657`
- WETH_USDT pool ID: `0x90078845bceb849b171873cfbc92db8540e9c803ff57d9d21b1215ec158e79b3`
- Both must match the constants in `test/_fork_references/Ethereum.sol` (lines 18-19)
- A registry mapping CLI name strings (`"usdc-weth"`, `"weth-usdt"`) to configs must exist. Unknown names produce exit status 1 listing valid names

**B-U4: Functions remaining in `freeze_ran_snapshots.py`**
The following functions are tick-specific and NOT extracted to `ran_utils.py`: `tick_to_uint24`, `read_current_tick`, `compute_growth_inside`. These are called in the current `freeze_ran_snapshots.py` but are **not yet implemented** (they are forward references from a prior plan). They must be implemented in `freeze_ran_snapshots.py` as part of the B-F2 refactoring scope — they are NOT part of this pipeline's scope but must exist for the freeze script to work after refactoring.

### Bulk Fetcher (`ran_growth_pipeline.py`)

**B-P1: Batch JSON-RPC construction**
Given a storage slot and a list of block numbers, the pipeline must produce valid JSON-RPC 2.0 batch payloads:
- Each request in the batch must have a unique `id` field
- Method must be `eth_getStorageAt`
- Params must be `[address, slot_hex, block_hex]` where all values are 0x-prefixed hex
- Batch size must not exceed 15 requests

**B-P2: Response correlation by ID**
Batch responses from JSON-RPC are NOT guaranteed to arrive in request order. The pipeline must correlate each response to its request using the `id` field, never by array position. A test with shuffled response order must produce correct block-to-value mappings.

**B-P3: Rate limiting**
Given a CUPS limit and a batch CU cost, the pipeline must compute a minimum inter-batch delay. At 15 calls × 20 CU = 300 CU/batch with 500 CUPS limit: the minimum delay is 300/500 = 0.6 seconds. The actual delay must be >= 1.0 second (includes mandatory safety margin for rolling-window CUPS and HTTP latency). Tests must assert delay >= 1.0s.

**B-P4: DuckDB writes are idempotent**
Inserting the same `(pool_id, block_number)` twice must not error and must not overwrite the first value. A test inserting duplicate rows must succeed silently and preserve the original row.

**B-P5: Commit granularity survives crash**
The pipeline must commit to DuckDB after every batch (default). After inserting 5 batches, committing each, and simulating a crash before batch 6 (closing the connection without final commit), all 5 committed batches must be recoverable by reopening the DB. Combined with B-P4 idempotent inserts, this means re-running the same command after a crash safely resumes.

**B-P6: Retry on transient RPC errors**
On HTTP 429 (rate limit) or 5xx (server error), the pipeline must retry with exponential backoff. After max retries, it must abort with a clear error message including the last HTTP status and the block range that failed. A test with a mock returning 429 twice then 200 must succeed.

**B-P7: Block range validation**
- `--from-block` must be >= 22,972,937 (BLOCK_NUMBER_0). Lower values produce an error.
- `--from-block` must be < `--to-block`. Equal or reversed values produce an error.
- `--to-block latest` resolves to the current chain head via `eth_getBlockNumber`.

**B-P8: Zero-value awareness**
If `eth_getStorageAt` returns `0x0` for a block, the pipeline normalizes it through `to_hex256(int(response, 16))` and stores the result (`"0x" + "0" * 64`). "As-is" means the pipeline does NOT skip or error on zero values — it stores them like any other value. No assertion-on-zero — that was appropriate for the snapshot script's specific use case but not for bulk backfill.

**B-P9: Progress reporting**
The pipeline must print to stderr: blocks fetched so far, total blocks, estimated CU spent, and percentage of monthly budget consumed. This is a UX requirement, not a correctness requirement — tests may verify output format but not exact numbers.

### Query Interface (`ran_growth_query.py`)

**B-Q1: Exact block match**
Given a block number that exists in the DB, the query returns a JSON object to stdout with these camelCase keys only (matching Forge `vm.parseJson` conventions):
```json
{
  "blockNumber": 24827762,
  "globalGrowth": "0x0000...64-chars",
  "poolId": "0xe500...64-chars",
  "exact": true
}
```
Only these four keys. `sampled_at` and `stride` are internal DB columns and are NOT included in query output.

**B-Q2: Nearest-lower match**
Given a block number that does NOT exist in the DB, the query returns the nearest lower sampled block with these six keys:
```json
{
  "blockNumber": 24827762,
  "globalGrowth": "0x0000...64-chars",
  "poolId": "0xe500...64-chars",
  "exact": false,
  "sampledBlock": 24827750,
  "blockDelta": 12
}
```
`sampledBlock` is the block that was actually returned. `blockDelta` is `blockNumber - sampledBlock`. If the requested block is BELOW the lowest sample in the DB, the query exits with status 1 and a message: "Requested block N is before earliest sample at block M."

**B-Q3: Missing pool error**
Given a `--pool` value not in the registry, the query exits with status 1 and a message listing valid pool names.

**B-Q4: Empty DB**
Given an empty DuckDB (no rows for the requested pool), the query exits with status 1 and a message indicating no data has been fetched yet.

**B-Q5: Zero network dependency**
The query module makes ZERO network calls. It reads only from the local DuckDB file. No RPC URL, no API key, no HTTP client.

### Refactored `freeze_ran_snapshots.py`

**B-F1: Import, don't duplicate**
After refactoring, the three shared utilities (`keccak_mapping_slot`, `to_hex256`, `read_storage_at`) must be imported from `ran_utils`, not defined inline. Note: `read_storage_at` signature changes — it now accepts the RPC URL as a parameter instead of reading `ETH_RPC_URL` from environment (see Configuration section). The freeze script's `main()` constructs the URL from `ALCHEMY_API_KEY` and passes it in. The module must be importable after refactoring. Note: `freeze_snapshot()` and `main()` will NOT be functional until tick functions are implemented in a future spec — only the import path and shared utility extraction are validated in this pipeline scope.

**B-F2: Tick-specific functions are stubbed in `freeze_ran_snapshots.py`**
`tick_to_uint24`, `read_current_tick`, `compute_growth_inside` are called but not yet defined in the current file (forward references). They must be **stubbed with `NotImplementedError`** in `freeze_ran_snapshots.py` — they are NOT moved to `ran_utils.py`. Full implementation is deferred to a future spec (tick/growthInside scope). B-F1 testing focuses only on the three extracted functions, not on these stubs.

## Error Handling

| Error Condition | Expected Behavior |
|----------------|-------------------|
| `ALCHEMY_API_KEY` not set | Exit with status 1, message: "ALCHEMY_API_KEY not set" |
| Unknown `--pool` name | Exit with status 1, list valid pool names |
| `--from-block` < BLOCK_NUMBER_0 | Exit with status 1, message showing minimum block |
| HTTP 429 from Alchemy | Retry with exponential backoff (3 retries max) |
| HTTP 5xx from Alchemy | Retry with exponential backoff (3 retries max) |
| HTTP timeout | Retry with exponential backoff (3 retries max) |
| All retries exhausted | Exit with status 1, show failed block range and last HTTP status |
| DuckDB file locked by another writer | Exit with status 1, message about concurrent access |
| `globalGrowth` returns 0x0 | Store it (legitimate pre-settlement value) |
| Duplicate `(pool_id, block_number)` insert | Silently skip (idempotent) |
| Process crash mid-run | Previously committed batches are preserved; re-run continues safely |

## Dependencies

Install via `uv pip install duckdb httpx` (the venv has no `pip` binary — `uv` manages packages directly; do NOT run `pip install`).

| Package | Purpose |
|---------|---------|
| `duckdb` | Embedded analytical DB |
| `httpx` | Sync HTTP client for JSON-RPC batches |

Also needed for tests: `pytest` (install via `uv pip install pytest`).

No other new dependencies. `eth_abi`, `eth_hash` already in venv.

## Testing Strategy (TDD)

Tests written before implementation. The test structure must support parallel agent dispatch — the Data Engineer writes pipeline tests while the Senior Backend Developer writes query tests.

### Test Organization

```
contracts/scripts/tests/
├── conftest.py                 # PREREQUISITE: implemented first by Data Engineer
├── test_ran_utils.py           # Owner: Data Engineer
├── test_ran_growth_pipeline.py # Owner: Data Engineer
└── test_ran_growth_query.py    # Owner: Senior Backend Developer
```

**Run command:** `cd contracts && .venv/bin/python3 -m pytest scripts/tests/ -v`

**Import convention:** Tests import from `scripts.ran_utils`, `scripts.ran_growth_pipeline`, etc. The test runner is invoked from `contracts/` so `scripts/` is on the path. An `__init__.py` must exist in both `scripts/` and `scripts/tests/` — without them, Python package imports will fail. These files must be created as part of the conftest setup (Data Engineer prerequisite step).

### `conftest.py` — Shared Fixtures (implement FIRST)

This file is a prerequisite for both agents. It must provide:
- An in-memory DuckDB connection with the `accumulator_samples` table schema pre-created
- Mock RPC response data: a mapping of block numbers to known `globalGrowth` hex values (at least 5 blocks with distinct non-zero values, and 1 block with zero value)
- A mock `httpx` transport (implementing `httpx.BaseTransport`) that returns JSON-RPC batch responses. Must provide both ordered and shuffled response variants for testing B-P2
- Pool config fixtures for USDC_WETH

### Test Categories Mapped to Behaviors

| Test Category | Behavior IDs | Owner |
|--------------|-------------|-------|
| Slot derivation golden values | B-U1 | Data Engineer |
| Hex round-trip fidelity | B-U2 | Data Engineer |
| Pool config completeness | B-U3 | Data Engineer |
| Batch payload construction | B-P1 | Data Engineer |
| Response ID correlation (shuffled) | B-P2 | Data Engineer |
| Rate limit math | B-P3 | Data Engineer |
| Idempotent DuckDB inserts | B-P4 | Data Engineer |
| Commit granularity / crash survival | B-P5 | Data Engineer |
| Retry on 429/5xx | B-P6 | Data Engineer |
| Block range validation | B-P7 | Data Engineer |
| Zero-value storage | B-P8 | Data Engineer |
| Exact block query → JSON | B-Q1 | Senior Backend Developer |
| Nearest-lower query → JSON | B-Q2 | Senior Backend Developer |
| Missing pool error | B-Q3 | Senior Backend Developer |
| Empty DB error | B-Q4 | Senior Backend Developer |
| Zero network dependency | B-Q5 | Senior Backend Developer |
| Import-not-duplicate | B-F1 | Senior Backend Developer |

No live RPC calls in any test. All RPC interactions are mocked.

## Out of Scope

- `outsideBelow`, `outsideAbove`, `currentTick`, `blockTimestamp` columns (future incremental)
- WETH_USDT pool fetching (schema supports it, pipeline doesn't fetch it yet)
- Async/concurrent fetching (sync batches are sufficient)
- Cloud sync automation (manual Parquet export + file copy for now)
- Adaptive/two-pass densification
- Analytics Reporter module (no analysis features in this pipeline step)
