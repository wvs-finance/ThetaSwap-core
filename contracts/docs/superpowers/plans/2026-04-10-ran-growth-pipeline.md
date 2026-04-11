# RAN Growth Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **REQUIRED SKILL:** Invoke `functional-python` before writing any Python code. Note: test infrastructure (mocks, fixtures, conftest) is exempt from the "no classes" rule — `httpx.BaseTransport` subclasses in conftest are acceptable.
>
> **Agent orchestration:** Agents Orchestrator dispatches to Data Engineer and Senior Backend Developer. See agent assignments per task.

---

> ## NON-NEGOTIABLE RULES — ALL AGENTS MUST READ BEFORE ANY WORK
>
> ### Rule 1: STRICT TDD — One Behavior at a Time
> Do NOT write implementation code for ANY feature unless:
> 1. The test for that SPECIFIC SINGLE behavior has been written FIRST
> 2. The test has been run and VERIFIED TO FAIL
> 3. Only THEN write the MINIMAL implementation to make that ONE test pass
> 4. Run the test again — VERIFY IT PASSES
> 5. Only THEN move to the next behavior's test
>
> No batch implementations. No writing code for B-P2 if B-P1's test hasn't passed yet.
> No writing tests for B-P2 before B-P1's implementation passes.
>
> ### Rule 2: NO MERGE WITHOUT APPROVAL
> No code from any implementing agent is merged to the working branch until the user explicitly approves it.
> - Agents implement in isolated git worktrees (their own branches)
> - Code Reviewer compares competing implementations
> - Results presented to user
> - User selects the winner
> - ONLY THEN is the winning branch merged
>
> **NEVER auto-merge. NEVER merge without user saying "merge".**
>
> ### Rule 3: ALL pytest/python commands MUST run from `contracts/`
> Every test and verification command uses the pattern: `cd contracts && .venv/bin/python3 -m pytest ...`
> Running from any other directory WILL break imports.
>
> ### Rule 4: SCRIPTS-ONLY SCOPE — Never Touch Contracts
> This pipeline is **non-intrusive to smart contract development**. Agents may ONLY create/modify:
> - `contracts/scripts/*.py` and `contracts/scripts/tests/*.py`
> - `contracts/scripts/__init__.py` and `contracts/scripts/tests/__init__.py`
> - `contracts/data/` (DuckDB, .gitkeep)
> - `contracts/.gitignore` (Python/DuckDB patterns only)
>
> **NEVER touch:**
> - `contracts/src/` (any Solidity source)
> - `contracts/test/**/*.sol` (any Solidity test)
> - `contracts/foundry.toml` or `contracts/remappings.txt`
> - Any `.sol` file anywhere
>
> **PR enforcement:** Before every commit, run `git diff --name-only` and verify ALL files are in the allowed list. Before opening a PR, verify the same. **REJECT any agent output that modifies disallowed files.**

---

**Goal:** Build a Python data pipeline that bulk-fetches Angstrom's `globalGrowth` accumulator samples into a local DuckDB store via Alchemy archive RPC, with a query interface for Forge FFI consumption.

**Architecture:** Four modules — shared utilities (`ran_utils`), bulk fetcher (`ran_growth_pipeline`), query interface (`ran_growth_query`), and a refactored existing script (`freeze_ran_snapshots`). DuckDB local file for storage. httpx for batch JSON-RPC. TDD throughout.

**Tech Stack:** Python 3.13, DuckDB, httpx, pytest, eth_abi, eth_hash (existing in venv)

**Spec:** `contracts/docs/superpowers/specs/2026-04-10-ran-growth-pipeline-design.md`

---

## Competitive Worktree Execution Strategy

For high-value tasks, **2 agents implement the same task independently** in isolated git worktrees. A Code Reviewer then compares implementations and the user selects the winner.

| Task | Execution Mode | Rationale |
|------|---------------|-----------|
| Task 1 (Setup) | Single agent | Mechanical, no design decisions |
| Task 2 (Utils) | **2 competing agents** | Core shared module, design decisions matter |
| Task 3 (Pipeline core) | **2 competing agents** | Critical batch/rate logic |
| Task 4 (Pipeline integration) | **2 competing agents** | DuckDB + retry — multiple valid approaches |
| Task 5 (Query) | **2 competing agents** | Independent module, good for parallel |
| Task 6 (Refactor) | Single agent | Straightforward extraction |
| Task 7 (Verify) | Single agent | Verification only |

### Flow per competitive task:

```
Plan Task N ───┬── Agent A (isolation: "worktree") ── implements Task N
               └── Agent B (isolation: "worktree") ── implements Task N
                            │
                            ▼
               Code Reviewer compares A vs B
                            │
                            ▼
               User selects winner → merge to working branch
               Losing worktree cleaned up
```

**Sequential dependency**: Each task's winning implementation must be merged (with user approval) before the next task's agents are dispatched. Agents for Task 3 see Task 2's merged winner as their starting state.

**Git commits**: Each competing agent commits to its own worktree branch. Commits from parallel tracks never collide.

**Pre-commit scope check (EVERY commit):** Before every `git commit`, run `git diff --cached --name-only` and verify every staged file is in the allowed list (Rule 4). If ANY `.sol`, `foundry.toml`, `remappings.txt`, or file outside `scripts/`/`data/`/`.gitignore` is staged, **STOP and unstage it**.

---

## Execution Phases

| Phase | Tasks | Agent | Dependency |
|-------|-------|-------|------------|
| 0 — Setup | Task 0 (stash) + Task 1 | Data Engineer (single) | None |
| 1 — Shared Utils | Task 2 | Data Engineer × 2 (competing) | Task 1 merged |
| 2a — Pipeline core | Task 3 | Data Engineer × 2 (competing) | Task 2 merged |
| 2b — Query (parallel with 2a) | Task 5 | Senior Backend Developer × 2 (competing) | Tasks 1 + 2 merged |
| 2c — Refactor (parallel with 2a) | Task 6 | Senior Backend Developer (single) | Tasks 1 + 2 merged |
| 3 — Pipeline integration | Task 4 | Data Engineer × 2 (competing) | Task 3 merged |
| 4 — Finalize | Task 7 | Either (single) | Tasks 3-6 all merged |

Task 3 and Tasks 5+6 can run in parallel once Task 2's winner is merged.
Task 4 is SERIAL after Task 3 (same files). They are NOT parallel.

---

## Task 0: Clean Working Tree

**Agent:** Data Engineer (single)

- [ ] **Step 1: Commit existing dirty state**

`contracts/scripts/freeze_ran_snapshots.py` has unstaged changes (development notes/comments). Commit them before any agent work begins — do NOT stash (stashes get forgotten):
```
git add contracts/scripts/freeze_ran_snapshots.py
git commit -m "chore: save freeze_ran_snapshots dev notes before pipeline refactor"
```
This ensures all agents start from a clean, committed state.

---

## Task 1: Project Setup and Test Infrastructure

**Agent:** Data Engineer (single — no competition)
**Files:**
- Create: `contracts/scripts/__init__.py`
- Create: `contracts/scripts/tests/__init__.py`
- Create: `contracts/scripts/tests/conftest.py`
- Create: `contracts/data/.gitkeep`
- Modify: `contracts/.gitignore`

### Steps

- [ ] **Step 1: Install dependencies**

Run from the worktree root (use `$(git rev-parse --show-toplevel)` to find it):
```
uv pip install --python "$(git rev-parse --show-toplevel)/contracts/.venv/bin/python" duckdb httpx pytest
```
Verify: `contracts/.venv/bin/python3 -c "import duckdb, httpx, pytest; print('OK')"` prints `OK`.

- [ ] **Step 2: Create package marker files**

Create empty `__init__.py` in `contracts/scripts/` and `contracts/scripts/tests/`. These enable `scripts.ran_utils` style imports. Without them, ALL subsequent tests will fail with `ModuleNotFoundError`.

- [ ] **Step 3: Create data directory and .gitignore entries**

Create `contracts/data/.gitkeep`. Add to `contracts/.gitignore`:
```
data/*.duckdb
data/*.parquet
data/*.duckdb.wal
__pycache__/
.pytest_cache/
```

- [ ] **Step 4: Implement conftest.py shared fixtures**

This file is a **prerequisite** for ALL subsequent test tasks. It must provide these pytest fixtures:

1. **`duckdb_conn`** — an in-memory DuckDB connection with the `accumulator_samples` table pre-created matching the spec's Data Model schema (5 columns, composite PK on `pool_id, block_number`). For unit tests that don't need persistence.

2. **`duckdb_file_conn`** — a file-backed DuckDB connection using pytest's `tmp_path` fixture. Same schema as `duckdb_conn`. For tests that need to close and reopen the DB (B-P5 crash recovery). Returns both the connection AND the file path so tests can reopen it.

3. **`mock_growth_data`** — a dict mapping block numbers to known `globalGrowth` hex values. At least 5 blocks with distinct non-zero values and 1 block with `"0x" + "0" * 64` (zero value). Use blocks starting from 22,972,937 with stride 50: `{22972937: "0x...", 22972987: "0x...", 22973037: "0x...", ...}`.

4. **`mock_rpc_transport`** — a **factory fixture** (returns a callable, not an instance) that creates `httpx.BaseTransport` implementations. The factory accepts these parameters:
   - `shuffle: bool = False` — when True, returns JSON-RPC batch responses in randomized order (for B-P2)
   - `fail_count: int = 0` — when > 0, returns error HTTP status for the first N HTTP requests before succeeding (for B-P6). Applies per HTTP request (= per batch), NOT per individual RPC call within a batch.
   - `fail_status: int = 429` — the HTTP status code to return during failures (default 429, use 500 to test 5xx)
   - `timeout_count: int = 0` — when > 0, raises `httpx.TimeoutException` for the first N HTTP requests before succeeding (for B-P6 timeout testing)
   - `head_block: int = <max block in mock_growth_data> + 1000` — the block number returned for `eth_getBlockNumber` requests (for B-P7 `--to-block latest` testing)
   
   **Transport behavior:**
   - Handles both JSON arrays (batches) and single JSON objects. A single object is treated as a batch of one.
   - For `eth_getStorageAt` requests: extracts block number from the **third element** of the `params` array (hex string), decodes it to int, looks up the value in `mock_growth_data`. If the block is NOT in `mock_growth_data`, returns `"0x" + "0" * 64` (zero value).
   - For `eth_getBlockNumber` requests: returns the `head_block` value as a hex string.
   - Each response `id` matches the corresponding request `id`.
   
   Usage: `transport = mock_rpc_transport(shuffle=True, head_block=23_000_000)` then `httpx.Client(transport=transport)`

5. **`usdc_weth_config`** — a fixture returning the USDC_WETH pool configuration with pool ID `0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657`, pool rewards slot `7`, reward growth size `16777216`, name `"usdc-weth"`.

6. **`populated_db_path`** — a file-backed DuckDB created via `tmp_path`, pre-populated with rows from `mock_growth_data` combined with `usdc_weth_config.pool_id`, then **closed**. Returns the file path as a string. For Task 5 query tests that need to open a DB independently via `--db` CLI argument. Uses **raw DuckDB SQL inserts** (`INSERT INTO accumulator_samples VALUES (...)`) — do NOT import from `ran_growth_pipeline`. This fixture must be self-contained because it is consumed by Task 5 before Task 4 exists. Insert with `stride=50` and `sampled_at='2026-04-10 00:00:00'` (fixed timestamp for deterministic tests).

- [ ] **Step 5: Verify test infrastructure works**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/ -v --collect-only`
Expected: pytest discovers `conftest.py` with no import errors. No tests collected yet (no test files).

Also smoke-test fixtures by running a quick inline test:
`cd contracts && .venv/bin/python3 -c "from scripts.tests.conftest import *; print('conftest OK')"`
This catches import errors in the fixture definitions before any agent depends on them.

- [ ] **Step 6: Commit**

```
git add contracts/scripts/__init__.py contracts/scripts/tests/__init__.py \
       contracts/scripts/tests/conftest.py contracts/data/.gitkeep contracts/.gitignore
git commit -m "feat(ran-pipeline): project setup, test fixtures, DuckDB schema"
```

---

## Architectural Clarifications (ALL agents must read)

**Constants home:** `ran_utils.py` must define these module-level constants:
- `ANGSTROM_HOOK: str` — the Angstrom hook contract address (`0x0000000aa232009084bd71a5797d089aa4edfad4`)
- `POOL_MANAGER: str` — the V4 PoolManager address (`0x000000000004444c5dc75cB358380D2e3dE08A90`)
- `BLOCK_NUMBER_0: int` — the starting block (`22_972_937`)
- Pool configs and registry (defined in B-U3)

Both agents need these constants — Data Engineer for pipeline validation (B-P7), Senior Backend Developer for query error messages (B-Q2).

**`blockNumber` semantics in JSON output:**
- `"blockNumber"` in query output is always the **requested** block number (the one the user asked for), not the stored one.
- For exact matches (B-Q1), requested == stored, so this distinction doesn't matter.
- For nearest-lower matches (B-Q2), `"blockNumber"` = requested, `"sampledBlock"` = the actual stored block.

**Module invocation:** Both `ran_growth_pipeline.py` and `ran_growth_query.py` must use `if __name__ == "__main__"` with `argparse` so they can be invoked as `cd contracts && .venv/bin/python3 -m scripts.ran_growth_pipeline --help`. After refactoring, `freeze_ran_snapshots.py` must also be invoked this way (`cd contracts && .venv/bin/python3 -m scripts.freeze_ran_snapshots`) — standalone invocation (`python3 freeze_ran_snapshots.py`) will NOT work due to package imports. This is a known breaking change documented in the spec.

**`freeze_snapshot()` is non-functional after refactor:** The tick function stubs raise `NotImplementedError`, so `freeze_snapshot()` and `main()` will crash if called. Only importability is validated. Full functionality is deferred to a future tick-scope spec.

**DuckDB table DDL:** All fixtures and pipeline code must use this table creation:
`CREATE TABLE IF NOT EXISTS accumulator_samples (block_number UBIGINT, pool_id VARCHAR, global_growth VARCHAR, sampled_at TIMESTAMP, stride USMALLINT, PRIMARY KEY (pool_id, block_number))`

This DDL string should be defined as a constant in `ran_utils.py` (e.g., `CREATE_TABLE_DDL`) and imported by both conftest and the pipeline. This prevents schema drift between test fixtures and production code.

**`duckdb_file_conn` return type:** Returns `tuple[duckdb.DuckDBPyConnection, str]` — (connection, file_path).

**`populated_db_path` composition:** This fixture uses `mock_growth_data` values combined with `usdc_weth_config.pool_id` to construct rows. The pool ID comes from the config, not from the growth data dict.

---

## Task 2: Shared Utilities — `ran_utils.py`

**Agent:** Data Engineer × 2 (competing worktrees)
**Behaviors:** B-U1, B-U2, B-U3 — **one at a time, strict TDD**
**Files:**
- Create: `contracts/scripts/tests/test_ran_utils.py`
- Create: `contracts/scripts/ran_utils.py`
**Prerequisite:** Task 1 merged.

### Steps — B-U1 cycle (slot derivation)

- [ ] **Step 1: Write failing test for B-U1**

Compute the expected `globalGrowth` slot by hand using `eth_abi.encode` + `eth_hash.auto.keccak` on the USDC_WETH pool ID + slot 7, then add 16777216. Hard-code the resulting integer as a golden literal. Assert the implementation's slot derivation function returns this exact value.

- [ ] **Step 2: Run test — verify it FAILS**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_ran_utils.py -v -k "slot"`
Expected: FAIL (ImportError or function not defined).

- [ ] **Step 3: Implement ONLY slot derivation to make B-U1 pass**

Minimal implementation: frozen dataclass for pool config, slot derivation function. Nothing else.

- [ ] **Step 4: Run test — verify it PASSES**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_ran_utils.py -v -k "slot"`
Expected: PASS.

### Steps — B-U2 cycle (hex encoding)

- [ ] **Step 5: Write failing test for B-U2**

Tests: encoding `0` → `"0x" + "0" * 64`, encoding `2^256 - 1` → `"0x" + "f" * 64`, encoding mid-range → 66 chars, round-trip decode.

- [ ] **Step 6: Run test — verify it FAILS**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_ran_utils.py -v -k "hex"`
Expected: FAIL.

- [ ] **Step 7: Implement ONLY hex encoding/decoding to make B-U2 pass**

- [ ] **Step 8: Run test — verify it PASSES**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_ran_utils.py -v -k "hex"`
Expected: PASS.

### Steps — B-U3 cycle (pool config)

- [ ] **Step 9: Write failing test for B-U3**

Tests: USDC_WETH config has correct pool ID (`0xe500...a657`), WETH_USDT has `0x9007...79b3`, both have slot 7 + size 16777216, registry lookups work, unknown name raises error.

- [ ] **Step 10: Run test — verify it FAILS**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_ran_utils.py -v -k "config or registry"`
Expected: FAIL.

- [ ] **Step 11: Implement pool configs and registry to make B-U3 pass**

Also add `read_storage_at` to `ran_utils.py` — it accepts RPC URL as parameter (no env var reads), uses `cast` subprocess. NOT used by the pipeline. Its TDD cycle is in Task 6 (B-F1) where the Senior Backend Developer tests the signature change and call-site refactoring together.

- [ ] **Step 12: Run ALL utils tests**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_ran_utils.py -v`
Expected: ALL PASS (B-U1 + B-U2 + B-U3).

- [ ] **Step 13: Commit**

```
git add contracts/scripts/ran_utils.py contracts/scripts/tests/test_ran_utils.py
git commit -m "feat(ran-pipeline): shared utilities with slot derivation, hex encoding, pool config"
```

---

## Task 3: Bulk Pipeline Core — Batch Construction, Response Handling, Rate Limiting

**Agent:** Data Engineer × 2 (competing worktrees)
**Behaviors:** B-P1, B-P2, B-P3 — **one at a time, strict TDD**
**Files:**
- Create: `contracts/scripts/tests/test_ran_growth_pipeline.py`
- Create: `contracts/scripts/ran_growth_pipeline.py`
**Prerequisite:** Task 2 merged.

### Steps — B-P1 cycle (batch construction)

- [ ] **Step 1: Write failing test for B-P1**

Tests: given a slot + 3 blocks → valid JSON-RPC 2.0 batch with 3 elements, unique `id` fields, correct method/params. Given 20 blocks + batch size 15 → two batches (15 + 5).

- [ ] **Step 2: Run test — verify FAILS**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_ran_growth_pipeline.py -v -k "batch"`
Expected: FAIL.

- [ ] **Step 3: Implement ONLY batch construction**

- [ ] **Step 4: Run test — verify PASSES**

### Steps — B-P2 cycle (response correlation)

- [ ] **Step 5: Write failing test for B-P2**

Tests: ordered response → correct mapping. SHUFFLED response (use `mock_rpc_transport(shuffle=True)`) → same correct mapping. Correlation by `id`, not position.

- [ ] **Step 6: Run test — verify FAILS**

- [ ] **Step 7: Implement ONLY response correlation**

- [ ] **Step 8: Run test — verify PASSES**

### Steps — B-P3 cycle (rate limiting)

- [ ] **Step 9: Write failing test for B-P3**

Test: 15 calls × 20 CU at 500 CUPS → delay >= 1.0s. Pure computation, no sleeping.

- [ ] **Step 10: Run test — verify FAILS**

- [ ] **Step 11: Implement ONLY rate limit computation**

- [ ] **Step 12: Run ALL Task 3 tests**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_ran_growth_pipeline.py -v`
Expected: ALL PASS.

- [ ] **Step 13: Commit**

```
git add contracts/scripts/ran_growth_pipeline.py contracts/scripts/tests/test_ran_growth_pipeline.py
git commit -m "feat(ran-pipeline): batch construction, response correlation, rate limiting"
```

---

## Task 4: Bulk Pipeline Integration — DuckDB Writes, Retry, Validation, CLI

**Agent:** Data Engineer × 2 (competing worktrees)
**Behaviors:** B-P4, B-P5, B-P6, B-P7, B-P8, B-P9, plus error conditions — **one at a time, strict TDD**
**Files:**
- Modify: `contracts/scripts/tests/test_ran_growth_pipeline.py`
- Modify: `contracts/scripts/ran_growth_pipeline.py`
**Prerequisite:** Task 3 merged.

### Steps — B-P4 cycle (idempotent writes)

- [ ] **Step 1: Write failing test for B-P4**

Insert same `(pool_id, block_number)` twice → no error, original row preserved. Use `duckdb_conn` fixture.

- [ ] **Step 2: Run — verify FAILS**
- [ ] **Step 3: Implement idempotent insert**
- [ ] **Step 4: Run — verify PASSES**

### Steps — B-P5 cycle (commit granularity)

- [ ] **Step 5: Write failing test for B-P5**

Use `duckdb_file_conn` fixture (NOT in-memory). Insert 5 batches, commit each. Close connection. Reopen DB file. Verify 5 batches present. This requires file-backed DuckDB.

- [ ] **Step 6: Run — verify FAILS**
- [ ] **Step 7: Implement per-batch commit**
- [ ] **Step 8: Run — verify PASSES**

### Steps — B-P6 cycle (retry)

- [ ] **Step 9: Write failing tests for B-P6 (4 separate test cases)**

Retry semantics: initial attempt + 3 retries = 4 total attempts max.

Test case A: `mock_rpc_transport(fail_count=2, fail_status=429)` → 429, 429, then 200 → **success**.
Test case B: `mock_rpc_transport(fail_count=4, fail_status=429)` → 4 consecutive 429s → retries exhausted → **error** with message containing HTTP status 429 and the failed block range.
Test case C: `mock_rpc_transport(fail_count=2, fail_status=500)` → 500, 500, then 200 → **success** (5xx triggers same retry as 429).
Test case D: `mock_rpc_transport(timeout_count=2)` → timeout, timeout, then 200 → **success** (timeout triggers retry).

- [ ] **Step 10: Run — verify FAILS**
- [ ] **Step 11: Implement retry with exponential backoff**
- [ ] **Step 12: Run — verify PASSES**

### Steps — B-P7 cycle (block range validation)

- [ ] **Step 13: Write failing test for B-P7**

`--from-block 0` → exit 1, mentions 22,972,937. `--from-block >= --to-block` → exit 1. Valid range passes. `--to-block latest` → resolves to chain head (mock `eth_getBlockNumber` to return a known value, assert the pipeline uses it as upper bound).

- [ ] **Step 14: Run — verify FAILS**
- [ ] **Step 15: Implement validation**
- [ ] **Step 16: Run — verify PASSES**

### Steps — Error condition: ALCHEMY_API_KEY not set

- [ ] **Step 17: Write failing test for missing API key**

With `ALCHEMY_API_KEY` unset in environment, pipeline exits with status 1 and message "ALCHEMY_API_KEY not set".

- [ ] **Step 18: Run — verify FAILS**
- [ ] **Step 19: Implement env var check in CLI entrypoint**
- [ ] **Step 20: Run — verify PASSES**

### Steps — B-P8 cycle (zero-value storage)

- [ ] **Step 21: Write failing test for B-P8**

`0x0` response stored as `"0x" + "0" * 64` — no error, no skip.

- [ ] **Step 22: Run — verify FAILS**
- [ ] **Step 23: Implement (likely already works from B-P4 logic, but verify)**
- [ ] **Step 24: Run — verify PASSES**

### Steps — B-P9 (progress reporting) + CLI assembly

- [ ] **Step 25: Write test for B-P9**

Test that pipeline output on stderr contains ALL of these substrings: `"fetched"`, `"total"`, `"CU"`, and `"%"`. These correspond to the spec's four required fields: blocks fetched, total blocks, estimated CU, percentage of budget. This is a UX format test — verify the keywords appear, not exact numbers. Use pytest's `capsys` or `capfd` to capture stderr.

- [ ] **Step 26: Run — verify FAILS**
- [ ] **Step 27: Implement CLI entrypoint composing all pure functions with I/O.**

CLI accepts: `--pool` (required), `--from-block` (required), `--to-block` (required, accepts "latest"), `--stride` (default 50), `--db` (default `data/ran_accumulator.duckdb`). Reads `ALCHEMY_API_KEY` from env. B-P9 progress to stderr. The `stride` value must be stored in the `stride` column of each inserted row.
- [ ] **Step 28: Run ALL pipeline tests (Tasks 3 + 4)**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_ran_growth_pipeline.py -v`
Expected: ALL PASS.

- [ ] **Step 29: Commit**

```
git add contracts/scripts/ran_growth_pipeline.py contracts/scripts/tests/test_ran_growth_pipeline.py
git commit -m "feat(ran-pipeline): DuckDB writes, retry, validation, CLI entrypoint"
```

---

## Task 5: Query Interface — `ran_growth_query.py`

**Agent:** Senior Backend Developer × 2 (competing worktrees)
**Behaviors:** B-Q1, B-Q2, B-Q3, B-Q4, B-Q5 — **one at a time, strict TDD**
**Files:**
- Create: `contracts/scripts/tests/test_ran_growth_query.py`
- Create: `contracts/scripts/ran_growth_query.py`
**Prerequisite:** Tasks 1 + 2 merged. Can run in parallel with Tasks 3-4.

**Import dependency:** This module imports pool config and registry from `scripts.ran_utils` (Task 2). It does NOT define its own pool configs.

**CLI interface:** The query module accepts `--pool`, `--block`, and `--db` arguments. `--db` specifies the DuckDB file path (default: `data/ran_accumulator.duckdb` relative to `contracts/`).

**Test data setup:** Use the `populated_db_path` fixture from conftest — it provides a file-backed DuckDB pre-populated with `mock_growth_data` rows for USDC_WETH, already closed. Pass the path to the query module via `--db`.

### Steps — B-Q1 cycle (exact block match)

- [ ] **Step 1: Write failing test for B-Q1**

Given DuckDB with known rows, query exact block → JSON stdout with exactly 4 keys: `blockNumber`, `globalGrowth`, `poolId`, `exact` (true). `sampled_at`/`stride` NOT in output.

- [ ] **Step 2: Run — verify FAILS**
- [ ] **Step 3: Implement exact-match query**
- [ ] **Step 4: Run — verify PASSES**

### Steps — B-Q2 cycle (nearest-lower match)

- [ ] **Step 5: Write failing test for B-Q2**

Block between samples → nearest lower with 6 keys: `blockNumber`, `globalGrowth`, `poolId`, `exact` (false), `sampledBlock`, `blockDelta`. Block BELOW lowest sample → exit 1 with "Requested block N is before earliest sample at block M".

- [ ] **Step 6: Run — verify FAILS**
- [ ] **Step 7: Implement nearest-lower query**
- [ ] **Step 8: Run — verify PASSES**

### Steps — B-Q3 cycle (missing pool)

- [ ] **Step 9: Write failing test for B-Q3**

`--pool nonexistent` → exit 1, lists valid names.

- [ ] **Step 10: Run — verify FAILS**
- [ ] **Step 11: Implement pool validation**
- [ ] **Step 12: Run — verify PASSES**

### Steps — B-Q4 cycle (empty DB)

- [ ] **Step 13: Write failing test for B-Q4**

Query pool with no rows → exit 1, "no data fetched" message.

- [ ] **Step 14: Run — verify FAILS**
- [ ] **Step 15: Implement empty-DB check**
- [ ] **Step 16: Run — verify PASSES**

### Steps — B-Q5 cycle (zero network dependency)

- [ ] **Step 17: Write failing test for B-Q5**

Module has NO imports of `httpx`, `requests`, `urllib`, or any network library.

- [ ] **Step 18: Run — verify FAILS**
- [ ] **Step 19: (Likely already passes if implemented correctly — verify)**
- [ ] **Step 20: Run ALL query tests**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_ran_growth_query.py -v`
Expected: ALL PASS.

- [ ] **Step 21: Commit**

```
git add contracts/scripts/ran_growth_query.py contracts/scripts/tests/test_ran_growth_query.py
git commit -m "feat(ran-pipeline): query interface with exact and nearest-lower block lookup"
```

---

## Task 6: Refactor `freeze_ran_snapshots.py`

**Agent:** Senior Backend Developer (single — no competition)
**Behaviors:** B-F1, B-F2, B-U4
**Files:**
- Create: `contracts/scripts/tests/test_freeze_ran_snapshots.py`
- Modify: `contracts/scripts/freeze_ran_snapshots.py`
**Prerequisite:** Tasks 1 + 2 merged.

### Steps — B-F1 cycle (import refactor) — TDD

- [ ] **Step 1: Write failing test for B-F1**

In `test_freeze_ran_snapshots.py`, test that:
- `freeze_ran_snapshots` module does NOT define `keccak_mapping_slot`, `to_hex256`, or `read_storage_at` as local functions (inspect module attributes or source)
- These three names ARE importable from `scripts.ran_utils`
- `freeze_ran_snapshots` imports them from `scripts.ran_utils`
- `read_storage_at` accepts RPC URL as a parameter (mock `subprocess.run`, call `read_storage_at(address, slot, block, rpc_url)`, assert `cast storage` is called with `--rpc-url` matching the passed URL)

- [ ] **Step 2: Run test — verify FAILS**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_freeze_ran_snapshots.py -v -k "import"`
Expected: FAIL (functions still defined inline).

- [ ] **Step 3: Remove inline definitions, add imports from `ran_utils`**

- Remove inline `keccak_mapping_slot`, `to_hex256`, `read_storage_at` from `freeze_ran_snapshots.py`
- Add `from scripts.ran_utils import keccak_mapping_slot, to_hex256, read_storage_at`
- Update `read_storage_at` calls: function now takes RPC URL as parameter. Construct URL from `ALCHEMY_API_KEY` in `main()` and pass it to callers.
- Also update the `cast block` timestamp call (around line 107 in current file) to use the same RPC URL variable instead of reading `ETH_RPC_URL` directly.
- **Breaking change:** The freeze script now reads `ALCHEMY_API_KEY` instead of `ETH_RPC_URL`. This matches `foundry.toml` and the pipeline. No backward compatibility fallback — clean break.

- [ ] **Step 4: Run test — verify PASSES**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_freeze_ran_snapshots.py -v -k "import"`
Expected: PASS.

### Steps — B-F2 / B-U4 cycle (tick function stubs + negative assertion) — TDD

**SCOPE NOTE:** Tick functions (`tick_to_uint24`, `read_current_tick`, `compute_growth_inside`) are OUT OF SCOPE for this pipeline. This pipeline is globalGrowth time series ONLY. These functions get `NotImplementedError` stubs so the file is importable. Full implementation is deferred to a future spec.

- [ ] **Step 5: Write failing test for B-U4 negative assertion**

Test that `tick_to_uint24`, `read_current_tick`, `compute_growth_inside` are NOT importable from `scripts.ran_utils` (they must stay in `freeze_ran_snapshots.py`, not leak into shared utils).

- [ ] **Step 6: Run test — verify FAILS**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_freeze_ran_snapshots.py -v -k "not_in_utils"`
Expected: FAIL.

- [ ] **Step 7: Write failing test for B-F2 stubs**

Test that `tick_to_uint24`, `read_current_tick`, `compute_growth_inside` exist as callable attributes in `freeze_ran_snapshots` module AND that calling them raises `NotImplementedError`.

- [ ] **Step 8: Run test — verify FAILS**

- [ ] **Step 9: Add `NotImplementedError` stubs for all three tick functions in `freeze_ran_snapshots.py`**

Each stub: accepts the same arguments as the call sites use (infer from lines 81-93 of current file), raises `NotImplementedError("Planned for future implementation — see globalGrowth pipeline spec")`.

- [ ] **Step 10: Run ALL Task 6 tests + verify import**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_freeze_ran_snapshots.py -v`
Expected: ALL PASS.

Run: `cd contracts && .venv/bin/python3 -c "from scripts.freeze_ran_snapshots import main; print('OK')"`
Expected: `OK` (importable, but freeze_snapshot() will raise NotImplementedError if called).

- [ ] **Step 11: Commit**

```
git add contracts/scripts/freeze_ran_snapshots.py contracts/scripts/tests/test_freeze_ran_snapshots.py
git commit -m "refactor(ran-pipeline): extract shared utils to ran_utils, stub tick functions"
```

---

## Task 7: Full Integration Verification

**Agent:** Either (single — no competition)
**Files:** None created — verification only
**Prerequisite:** Tasks 1-6 all merged.

### Steps

- [ ] **Step 1: Run complete test suite**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/ -v`
Expected: ALL tests pass across all 4 test files.

- [ ] **Step 2: Verify module imports are clean**

Run: `cd contracts && .venv/bin/python3 -c "from scripts.ran_utils import *; from scripts.ran_growth_pipeline import *; from scripts.ran_growth_query import *; print('All imports OK')"`
Expected: No errors.

- [ ] **Step 3: Verify CLI help text works**

Run:
```
cd contracts && .venv/bin/python3 -m scripts.ran_growth_pipeline --help
cd contracts && .venv/bin/python3 -m scripts.ran_growth_query --help
```
Expected: Both show usage with documented arguments.

- [ ] **Step 4: Verify .gitignore**

Run: `git status contracts/data/` — should show nothing tracked except `.gitkeep`.
Run: `git status contracts/scripts/__pycache__/` — should show nothing (ignored).

- [ ] **Step 5: Final commit if any loose changes**

```
git status contracts/scripts/ contracts/data/ contracts/.gitignore
```
Review output. If there are loose changes, stage ONLY explicitly named files (never `git add -A`). Commit only if needed.

---

## Coverage Checklist (Spec → Task Mapping)

| Spec Behavior | Task | TDD Cycle |
|---------------|------|-----------|
| B-U1 Slot derivation | Task 2, Steps 1-4 | |
| B-U2 Hex round-trip | Task 2, Steps 5-8 | |
| B-U3 Pool config | Task 2, Steps 9-12 | |
| B-U4 Tick functions NOT in ran_utils | Task 6, Steps 5-6 (negative assertion) | |
| B-P1 Batch construction | Task 3, Steps 1-4 | |
| B-P2 Response correlation | Task 3, Steps 5-8 | |
| B-P3 Rate limiting | Task 3, Steps 9-12 | |
| B-P4 Idempotent writes | Task 4, Steps 1-4 | |
| B-P5 Commit granularity | Task 4, Steps 5-8 | |
| B-P6 Retry on errors | Task 4, Steps 9-12 | |
| B-P7 Block range validation | Task 4, Steps 13-16 | |
| B-P8 Zero-value storage | Task 4, Steps 21-24 | |
| B-P9 Progress reporting | Task 4, Steps 25-28 | |
| B-Q1 Exact block query | Task 5, Steps 1-4 | |
| B-Q2 Nearest-lower query | Task 5, Steps 5-8 | |
| B-Q3 Missing pool error | Task 5, Steps 9-12 | |
| B-Q4 Empty DB error | Task 5, Steps 13-16 | |
| B-Q5 Zero network dependency | Task 5, Steps 17-20 | |
| B-F1 Import refactor + read_storage_at signature | Task 6, Steps 1-4 | |
| B-F2 Tick function stubs | Task 6, Steps 7-9 | |

### Error Handling Coverage

| Error Condition | Task/Step |
|----------------|-----------|
| `ALCHEMY_API_KEY` not set | Task 4, Steps 17-20 |
| Unknown `--pool` name | Task 5 B-Q3 |
| `--from-block` < BLOCK_NUMBER_0 | Task 4 B-P7 |
| HTTP 429 | Task 4 B-P6 |
| HTTP 5xx | Task 4 B-P6 |
| HTTP timeout | Task 4 B-P6 (Step 9 includes timeout test) |
| All retries exhausted | Task 4 B-P6 |
| DuckDB locked | **Intentionally untested** — DuckDB locking is OS-level and unreliable to mock in CI. Implement the handler (try/except around connection open) but do not unit-test it. |
| `globalGrowth` returns 0x0 | Task 4 B-P8 |
| Duplicate insert | Task 4 B-P4 |
| Process crash | Task 4 B-P5 |

### Infrastructure Coverage

| Item | Task |
|------|------|
| Dependencies installed | Task 1, Step 1 |
| `__init__.py` files | Task 1, Step 2 |
| conftest.py fixtures (6: duckdb_conn, duckdb_file_conn, mock_growth_data, mock_rpc_transport, usdc_weth_config, populated_db_path) | Task 1, Step 4 |
| `.gitignore` entries | Task 1, Step 3 |
| `__pycache__/` in .gitignore | Task 1, Step 3 |
| `ETH_RPC_URL` → `ALCHEMY_API_KEY` (clean break, no fallback) | Task 6, Step 3 |
