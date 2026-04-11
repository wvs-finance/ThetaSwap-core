# RAN Data Query API — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **REQUIRED SKILL:** Invoke `functional-python` before writing any Python code.
>
> **Agent:** Data Engineer implements ALL tasks. Code Reviewer + Reality Checker review.

---

> ## NON-NEGOTIABLE RULES
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
> ONLY touch `contracts/scripts/`, `contracts/notebooks/`. NEVER `.sol`, `foundry.toml`.
>
> ### Rule 5: REAL DATA OVER MOCKS
> Use real `globalGrowth` values from DuckDB fixtures. Mock ONLY what cannot be reproduced.

---

**Goal:** Build a shared Python query API module (`ran_data_api.py`) consumed by both the FFI script (Solidity fork tests) and the notebook (EDA), plus 4 new FFI subcommands.

**Architecture:** Pure function module with frozen `Row` dataclass and `QueryError` exception. FFI script becomes a thin ABI wrapper. Notebook imports API directly.

**Tech Stack:** Python 3.13, DuckDB, eth_abi, pytest

**Spec:** `contracts/docs/superpowers/specs/2026-04-11-ran-data-api-design.md`

---

## Execution Phases

| Phase | Task | Dependency |
|-------|------|------------|
| 1 — Fixtures | Task 1: Add `large_populated_db_path` to conftest | None |
| 2 — Core API | Task 2: `ran_data_api.py` (all 7 functions) | Task 1 |
| 3 — FFI Refactor | Task 3: Refactor `ran_ffi.py` + new subcommands | Task 2 |
| 4 — Notebook | Task 4: Rewrite `growthGlobal.ipynb` using API | Task 2 |

Tasks 3 and 4 can run in parallel after Task 2.

---

## Task 1: Conftest — Add Large Fixture

**Files:**
- Modify: `contracts/scripts/tests/conftest.py`

### Steps

- [ ] **Step 1: Add `large_populated_db_path` fixture**

New pytest fixture: file-backed DuckDB with 1,050 rows of synthetic data at stride 50 starting from block 22,972,937. Uses `MOCK_BLOCK_TIMESTAMPS` pattern (deterministic timestamps). Pool ID = USDC_WETH. Growth values can be synthetic (incrementing hex). This fixture exists ONLY for testing the 1,000-row range limit independently from bounds checking.

- [ ] **Step 2: Verify existing tests still pass**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/ -q`
Expected: 101 passed.

- [ ] **Step 3: Commit**

```
git add contracts/scripts/tests/conftest.py
git commit -m "feat(ran-pipeline): add large_populated_db_path fixture (1050 rows)"
```

---

## Task 2: Core API — `ran_data_api.py`

**Files:**
- Create: `contracts/scripts/ran_data_api.py`
- Create: `contracts/scripts/tests/test_ran_data_api.py`

All behaviors implemented one at a time with strict TDD. Tests open their own `duckdb.connect(populated_db_path, read_only=True)` connection.

### Steps — `QueryError` + `Row`

- [ ] **Step 1: Write failing test for `QueryError` and `Row` imports**

Test that `QueryError` is importable from `scripts.ran_data_api`, subclasses `Exception`. Test that `Row` is a frozen dataclass with fields `block_number: int`, `block_timestamp: int`, `global_growth: str`.

- [ ] **Step 2: Verify FAILS**
- [ ] **Step 3: Create `ran_data_api.py` with `QueryError` and `Row`**
- [ ] **Step 4: Verify PASSES**

### Steps — `dataset_len`

- [ ] **Step 5: Write failing test for `dataset_len`**

Count of rows for USDC_WETH pool in `populated_db_path` must equal 6 (the fixture count).

- [ ] **Step 6: Verify FAILS**
- [ ] **Step 7: Implement `dataset_len`**
- [ ] **Step 8: Verify PASSES**

### Steps — `get_row`

- [ ] **Step 9: Write failing test for `get_row` index 0**

Must return `Row` with earliest block number from fixture, correct timestamp, correct growth hex.

- [ ] **Step 10: Verify FAILS**
- [ ] **Step 11: Implement `get_row`**
- [ ] **Step 12: Verify PASSES**

- [ ] **Step 13: Write failing test for `get_row` index N-1**

Must return latest block.

- [ ] **Step 14: Verify PASSES** (should work with existing impl)

- [ ] **Step 15: Write failing test for `get_row` out of bounds**

`idx >= 6` → `QueryError`.

- [ ] **Step 16: Verify FAILS → implement bounds check → PASSES**

- [ ] **Step 17: Write failing test for `get_row` negative index**

`idx = -1` → `QueryError`.

- [ ] **Step 18: Verify FAILS → implement negative check → PASSES**

### Steps — `get_by_timestamp`

- [ ] **Step 19: Write failing test for exact timestamp match**

Use a known timestamp from `MOCK_BLOCK_TIMESTAMPS`. Must return correct `Row`.

- [ ] **Step 20: Verify FAILS**
- [ ] **Step 21: Implement `get_by_timestamp` with `exact=True`**
- [ ] **Step 22: Verify PASSES**

- [ ] **Step 23: Write failing test for exact miss**

Timestamp not in DB → `QueryError`.

- [ ] **Step 24: Verify FAILS → implement → PASSES**

- [ ] **Step 25: Write failing test for nearest-lower**

Timestamp between two stored values, `exact=False` → returns the lower one.

- [ ] **Step 26: Verify FAILS**
- [ ] **Step 27: Implement nearest-lower with `ORDER BY block_timestamp DESC, block_number DESC LIMIT 1`**
- [ ] **Step 28: Verify PASSES**

- [ ] **Step 29: Write failing test for below minimum**

Timestamp below earliest → `QueryError` with `exact=False`.

- [ ] **Step 30: Verify FAILS → implement → PASSES**

### Steps — `get_range`

- [ ] **Step 31: Write failing test for valid range**

`get_range(conn, pool_id, 0, 3)` → list of 3 `Row` objects in order.

- [ ] **Step 32: Verify FAILS**
- [ ] **Step 33: Implement `get_range`**
- [ ] **Step 34: Verify PASSES**

- [ ] **Step 35: Write failing test for `from == to` → empty list**
- [ ] **Step 36: Verify FAILS → implement → PASSES**

- [ ] **Step 37: Write failing test for `from > to` → `QueryError`**
- [ ] **Step 38: Verify FAILS → implement → PASSES**

- [ ] **Step 39: Write failing test for range exceeds 1000**

Use `large_populated_db_path` fixture. `get_range(conn, pool_id, 0, 1001)` → `QueryError`.

- [ ] **Step 40: Verify FAILS → implement 1000 limit check → PASSES**

- [ ] **Step 41: Write failing test for out of bounds**

`get_range(conn, pool_id, 0, 100)` on 6-row fixture → `QueryError`.

- [ ] **Step 42: Verify FAILS → implement → PASSES**

### Steps — `get_min` / `get_max`

- [ ] **Step 43: Write failing test for `get_min`**

Must equal `get_row(conn, pool_id, 0)`.

- [ ] **Step 44: Verify FAILS → implement → PASSES**

- [ ] **Step 45: Write failing test for `get_max`**

Must equal `get_row(conn, pool_id, dataset_len - 1)`.

- [ ] **Step 46: Verify FAILS → implement → PASSES**

- [ ] **Step 47: Write failing test for `get_min`/`get_max` unknown pool → `QueryError`**
- [ ] **Step 48: Verify FAILS → implement → PASSES**

### Steps — `get_all`

- [ ] **Step 49: Write failing test for `get_all`**

Returns all 6 rows, ordered, correct count.

- [ ] **Step 50: Verify FAILS → implement → PASSES**

### Steps — NULL timestamp + zero network

- [ ] **Step 51: Write failing test for NULL `block_timestamp`**

Insert a row with NULL timestamp into a test DB. `get_row` at that index → `QueryError`.

- [ ] **Step 52: Verify FAILS → implement post-fetch NULL check → PASSES**

- [ ] **Step 53: Write test for zero network dependency**

AST check: module does not import httpx, requests, urllib, socket.

- [ ] **Step 54: Verify PASSES**

### Full suite + commit

- [ ] **Step 55: Run ALL tests**

`cd contracts && .venv/bin/python3 -m pytest scripts/tests/ -v`
ALL must PASS.

- [ ] **Step 56: Commit**

```
git add contracts/scripts/ran_data_api.py contracts/scripts/tests/test_ran_data_api.py
git commit -m "feat(ran-pipeline): shared query API — dataset_len, get_row, get_by_timestamp, get_range, get_min, get_max, get_all"
```

---

## Task 3: FFI Refactor + New Subcommands

**Files:**
- Modify: `contracts/scripts/ran_ffi.py`
- Modify: `contracts/scripts/tests/test_ran_ffi.py`
**Prerequisite:** Task 2.

### Steps — Refactor existing subcommands

- [ ] **Step 1: Refactor `len` and `row` to wrap `ran_data_api`**

Replace inline SQL in `_cmd_len` and `_cmd_row` with calls to `dataset_len` and `get_row`. Keep `_open_db` and `_normalize_pool_id` in FFI. Connection lifecycle stays in FFI.

- [ ] **Step 2: Verify ALL existing FFI tests still pass**

Run: `cd contracts && .venv/bin/python3 -m pytest scripts/tests/test_ran_ffi.py -v`

### Steps — New subcommands (one at a time, TDD)

### `row-by-ts`

- [ ] **Step 3: Write failing test for `row-by-ts` exact match**

Call FFI with exact timestamp from fixture. ABI-decode output. Verify matches expected row.

- [ ] **Step 4: Verify FAILS**
- [ ] **Step 5: Implement `row-by-ts` subcommand**

argparse subparser `row-by-ts` with `--pool`, `--ts`, `--db`, `[--nearest]`. Calls `get_by_timestamp(exact=not args.nearest)`. ABI-encode as `(uint256, uint256, bytes32)`.

- [ ] **Step 6: Verify PASSES**

- [ ] **Step 7: Write failing test for `row-by-ts --nearest`**
- [ ] **Step 8: Verify FAILS → already works if get_by_timestamp(exact=False) is correct → PASSES**

- [ ] **Step 9: Write failing test for `row-by-ts` miss → exit 1**
- [ ] **Step 10: Verify PASSES** (QueryError caught by wrapper)

### `range`

- [ ] **Step 11: Write failing test for `range --from 0 --to 3`**

ABI-decode as `(uint256, uint256[], uint256[], bytes32[])`. Verify count=3, arrays match fixture.

- [ ] **Step 12: Verify FAILS**
- [ ] **Step 13: Implement `range` subcommand**

argparse subparser with `--pool`, `--from`, `--to`, `--db`. Calls `get_range`. ABI-encode arrays. Max 1000 enforced by API.

- [ ] **Step 14: Verify PASSES**

- [ ] **Step 15: Write failing test for `range` exceeds 1000 → exit 1**

Use `large_populated_db_path`. `--from 0 --to 1001` → exit 1.

- [ ] **Step 16: Verify PASSES**

### `min` / `max`

- [ ] **Step 17: Write failing test for `min`**

ABI round-trip matches `get_min`.

- [ ] **Step 18: Verify FAILS → implement → PASSES**

- [ ] **Step 19: Write failing test for `max`**

ABI round-trip matches `get_max`.

- [ ] **Step 20: Verify FAILS → implement → PASSES**

### Full suite + commit

- [ ] **Step 21: Run ALL tests**

`cd contracts && .venv/bin/python3 -m pytest scripts/tests/ -v`

- [ ] **Step 22: Commit**

```
git add contracts/scripts/ran_ffi.py contracts/scripts/tests/test_ran_ffi.py
git commit -m "feat(ran-pipeline): FFI refactor + row-by-ts, range, min, max subcommands"
```

---

## Task 4: Notebook EDA Rewrite

**Files:**
- Modify: `contracts/notebooks/growthGlobal.ipynb`
**Prerequisite:** Task 2.

### Steps

- [ ] **Step 1: Rewrite notebook to use `ran_data_api`**

Replace all raw SQL cells with API calls. Remove stale "block_timestamp: PENDING" note. Structure:

1. **Setup cell:** `sys.path`, imports from `scripts.ran_data_api`, open DuckDB read-only
2. **Load + summary:** `dataset_len`, `get_min`, `get_max`, `get_all` → pandas DataFrame
3. **Correctness checks:**
   - Monotonicity: compute deltas, print count of violations + first 10 indices
   - Timestamp ordering: verify timestamps increase with block numbers, print inversions
   - Zero-value regions: identify blocks where `global_growth == "0x" + "0"*64`
4. **Edge case discovery:**
   - Largest growth delta (index of max spike)
   - First non-zero growth block
   - Long flat regions (10+ consecutive zero-delta strides) — print start/end indices
   - Timestamp gaps > 600s
   - Min/max growth as Q128 float
5. **Minimal visualizations:** cumulative growth, delta histogram, timestamp gap distribution
6. **Test vector summary:** print golden `(idx, blockNumber, blockTimestamp, globalGrowth)` tuples

- [ ] **Step 2: Verify notebook runs headless**

`cd contracts && .venv/bin/jupyter nbconvert --to notebook --execute notebooks/growthGlobal.ipynb --output /tmp/growthGlobal_executed.ipynb`
Expected: executes without errors.

- [ ] **Step 3: Commit**

```
git add contracts/notebooks/growthGlobal.ipynb
git commit -m "feat(ran-pipeline): notebook EDA using ran_data_api, test vector discovery"
```

---

## Coverage Checklist (Spec → Task)

| Spec Requirement | Task |
|-----------------|------|
| `QueryError` exception class | Task 2, Steps 1-4 |
| `Row` frozen dataclass | Task 2, Steps 1-4 |
| `dataset_len` | Task 2, Steps 5-8 |
| `get_row` (index, bounds, negative) | Task 2, Steps 9-18 |
| `get_by_timestamp` (exact, miss, nearest, below-min) | Task 2, Steps 19-30 |
| `get_range` (valid, empty, error, 1000 limit, OOB) | Task 2, Steps 31-42 |
| `get_min` / `get_max` | Task 2, Steps 43-48 |
| `get_all` | Task 2, Steps 49-50 |
| NULL timestamp error | Task 2, Steps 51-52 |
| Zero network dependency | Task 2, Steps 53-54 |
| FFI refactor (len, row wrap API) | Task 3, Steps 1-2 |
| FFI `row-by-ts` (exact, nearest, miss) | Task 3, Steps 3-10 |
| FFI `range` (valid, 1000 limit) | Task 3, Steps 11-16 |
| FFI `min` / `max` | Task 3, Steps 17-20 |
| `large_populated_db_path` fixture | Task 1 |
| Notebook EDA rewrite | Task 4 |
| Notebook correctness checks | Task 4, Step 1 (section 3) |
| Notebook edge case discovery | Task 4, Step 1 (section 4) |
| Notebook test vector summary | Task 4, Step 1 (section 6) |
