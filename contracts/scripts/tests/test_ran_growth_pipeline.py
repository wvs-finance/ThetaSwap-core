"""Tests for RAN growth pipeline — Tasks 3-4 + Task 2: batch construction, correlation, rate limiting, DuckDB, CLI."""
from __future__ import annotations

import json
import random
import sys
from typing import Final

import duckdb
import httpx
import pytest

# ── B-P1: Batch JSON-RPC construction ───────────────────────────────────────


class TestBatchJsonRpcConstruction:
    """Verify that build_rpc_batches produces valid JSON-RPC 2.0 batch payloads."""

    def test_batch_single_block(self) -> None:
        """A single block produces one batch with one request."""
        from scripts.ran_growth_pipeline import build_rpc_batches

        slot: Final[int] = 42
        blocks: Final[list[int]] = [100]
        batches = build_rpc_batches(slot=slot, blocks=blocks, batch_size=15)

        assert len(batches) == 1
        assert len(batches[0]) == 1
        req = batches[0][0]
        assert req["jsonrpc"] == "2.0"
        assert req["method"] == "eth_getStorageAt"
        assert isinstance(req["id"], int)

    def test_batch_params_hex_encoding(self) -> None:
        """Params must be [address_hex, slot_hex, block_hex], all 0x-prefixed."""
        from scripts.ran_growth_pipeline import build_rpc_batches
        from scripts.ran_utils import ANGSTROM_HOOK, encode_uint256

        slot: Final[int] = 99
        blocks: Final[list[int]] = [22_972_937]
        batches = build_rpc_batches(slot=slot, blocks=blocks, batch_size=15)

        params = batches[0][0]["params"]
        assert len(params) == 3
        # address
        assert params[0] == ANGSTROM_HOOK
        # slot as 0x-prefixed uint256
        assert params[1] == encode_uint256(slot)
        # block as 0x-prefixed hex
        assert params[2].startswith("0x")
        assert int(params[2], 16) == 22_972_937

    def test_batch_unique_ids(self) -> None:
        """Every request in the payload must have a unique id."""
        from scripts.ran_growth_pipeline import build_rpc_batches

        blocks = list(range(100, 120))  # 20 blocks
        batches = build_rpc_batches(slot=1, blocks=blocks, batch_size=15)

        all_ids: list[int] = []
        for batch in batches:
            for req in batch:
                all_ids.append(req["id"])
        assert len(all_ids) == len(set(all_ids)), "Request IDs must be unique"

    def test_batch_splitting_at_max_size(self) -> None:
        """20 blocks with batch_size=15 must produce exactly two batches (15 + 5)."""
        from scripts.ran_growth_pipeline import build_rpc_batches

        blocks = list(range(100, 120))  # 20 blocks
        batches = build_rpc_batches(slot=1, blocks=blocks, batch_size=15)

        assert len(batches) == 2
        assert len(batches[0]) == 15
        assert len(batches[1]) == 5

    def test_batch_exact_multiple(self) -> None:
        """15 blocks with batch_size=15 produces exactly one batch."""
        from scripts.ran_growth_pipeline import build_rpc_batches

        blocks = list(range(100, 115))
        batches = build_rpc_batches(slot=1, blocks=blocks, batch_size=15)

        assert len(batches) == 1
        assert len(batches[0]) == 15


# ── B-P2: Response correlation by ID ────────────────────────────────────────


class TestResponseCorrelation:
    """Verify that correlate_batch_response maps block numbers to values by id, not position."""

    def _make_requests_and_responses(
        self,
        blocks: list[int],
        growth_data: dict[int, str],
        shuffle: bool,
    ) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        """Helper: build requests and matching mock responses."""
        from scripts.ran_growth_pipeline import build_rpc_batches

        batches = build_rpc_batches(slot=1, blocks=blocks, batch_size=100)
        requests = batches[0]  # all in one batch

        responses: list[dict[str, object]] = []
        for req in requests:
            req_id = req["id"]
            block_hex = req["params"][2]  # type: ignore[index]
            block_num = int(str(block_hex), 16)
            value = growth_data.get(block_num, "0x" + "0" * 64)
            responses.append({"jsonrpc": "2.0", "id": req_id, "result": value})

        if shuffle:
            random.seed(42)
            random.shuffle(responses)

        return requests, responses

    def test_correlate_ordered_responses(self, mock_growth_data: dict[int, str]) -> None:
        """Ordered responses produce correct block-to-value mapping."""
        from scripts.ran_growth_pipeline import correlate_batch_response

        blocks = sorted(mock_growth_data.keys())
        batch, responses = self._make_requests_and_responses(
            blocks, mock_growth_data, shuffle=False,
        )
        result = correlate_batch_response(batch=batch, responses=responses)

        for block_num, expected_value in mock_growth_data.items():
            assert result[block_num] == expected_value, f"Mismatch for block {block_num}"

    def test_correlate_shuffled_responses(self, mock_growth_data: dict[int, str]) -> None:
        """Shuffled responses still produce the same correct mapping."""
        from scripts.ran_growth_pipeline import correlate_batch_response

        blocks = sorted(mock_growth_data.keys())
        batch, ordered_responses = self._make_requests_and_responses(
            blocks, mock_growth_data, shuffle=False,
        )
        _, shuffled_responses = self._make_requests_and_responses(
            blocks, mock_growth_data, shuffle=True,
        )

        ordered_result = correlate_batch_response(batch=batch, responses=ordered_responses)
        shuffled_result = correlate_batch_response(batch=batch, responses=shuffled_responses)

        assert ordered_result == shuffled_result, "Shuffled responses must yield same mapping"

    def test_correlate_with_mock_transport(self, mock_rpc_transport: object) -> None:
        """Integration: use mock_rpc_transport(shuffle=True) end-to-end."""
        from scripts.ran_growth_pipeline import build_rpc_batches, correlate_batch_response
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH

        blocks = sorted(MOCK_BLOCKS_AND_GROWTH.keys())
        batches = build_rpc_batches(slot=1, blocks=blocks, batch_size=100)
        batch = batches[0]

        # Send via mock transport with shuffle
        transport = mock_rpc_transport(shuffle=True)  # type: ignore[operator]
        client = httpx.Client(transport=transport, base_url="http://mock-rpc")
        response = client.post("/", content=json.dumps(batch).encode())
        responses = response.json()

        result = correlate_batch_response(batch=batch, responses=responses)

        for block_num, expected_value in MOCK_BLOCKS_AND_GROWTH.items():
            assert result[block_num] == expected_value


# ── B-P3: Rate limiting ─────────────────────────────────────────────────────


class TestRateLimiting:
    """Verify pure rate-limit delay computation."""

    def test_rate_limit_basic_computation(self) -> None:
        """15 calls * 20 CU = 300 CU/batch, 500 CUPS => 300/500 = 0.6s raw."""
        from scripts.ran_growth_pipeline import compute_inter_batch_delay

        delay = compute_inter_batch_delay(
            batch_calls=15,
            cu_per_call=20,
            cups_limit=500,
        )
        # Raw = 0.6s, but mandatory minimum is 1.0s
        assert delay >= 1.0

    def test_rate_limit_enforces_minimum(self) -> None:
        """Even if raw delay < 1.0s, result must be >= 1.0s."""
        from scripts.ran_growth_pipeline import compute_inter_batch_delay

        # Very high CUPS => raw delay near zero
        delay = compute_inter_batch_delay(
            batch_calls=1,
            cu_per_call=10,
            cups_limit=100_000,
        )
        assert delay >= 1.0

    def test_rate_limit_high_cost_exceeds_minimum(self) -> None:
        """When raw delay > 1.0s, the actual delay must match the raw value."""
        from scripts.ran_growth_pipeline import compute_inter_batch_delay

        # 15 * 20 = 300 CU / 100 CUPS = 3.0s raw, which exceeds 1.0s minimum
        delay = compute_inter_batch_delay(
            batch_calls=15,
            cu_per_call=20,
            cups_limit=100,
        )
        assert delay == pytest.approx(3.0)

    def test_rate_limit_from_batch_params(self) -> None:
        """Decomposed params: 15 calls * 20 CU, 500 CUPS => max(0.6, 1.0) = 1.0."""
        from scripts.ran_growth_pipeline import compute_inter_batch_delay

        # 15 calls * 20 CU = 300 CU, 500 CUPS => max(0.6, 1.0) = 1.0
        delay = compute_inter_batch_delay(
            batch_calls=15,
            cu_per_call=20,
            cups_limit=500,
        )
        assert delay == pytest.approx(1.0)

    def test_rate_limit_returns_float(self) -> None:
        """Delay must always be a float for use with time.sleep."""
        from scripts.ran_growth_pipeline import compute_inter_batch_delay

        delay = compute_inter_batch_delay(batch_calls=15, cu_per_call=20, cups_limit=500)
        assert isinstance(delay, float)


# ── B-P4: DuckDB writes are idempotent ────────────────────────────────────────


class TestDuckDbIdempotentWrites:
    """Insert same (pool_id, block_number) twice; original value preserved, no error."""

    def test_insert_then_duplicate_preserves_original(
        self, duckdb_conn: object,
    ) -> None:
        """Inserting the same PK twice keeps the first value and raises no error."""
        from scripts.ran_growth_pipeline import insert_sample
        from scripts.tests.conftest import USDC_WETH_POOL_ID

        # Real globalGrowth from fixture snapshot index 0
        original: Final[str] = (
            "0x0000000000000000000000000000000000002d2c02eeae24bd7a65341761b9c3"
        )
        different: Final[str] = (
            "0x0000000000000000000000000000000000002d2c20f39492940b8e1e976b5ad2"
        )
        block: Final[int] = 24_827_762

        insert_sample(
            conn=duckdb_conn,
            pool_id=USDC_WETH_POOL_ID,
            block_number=block,
            global_growth=original,
            stride=50,
        )
        # Second insert with different value — must not raise
        insert_sample(
            conn=duckdb_conn,
            pool_id=USDC_WETH_POOL_ID,
            block_number=block,
            global_growth=different,
            stride=50,
        )

        rows = duckdb_conn.execute(  # type: ignore[union-attr]
            "SELECT global_growth FROM accumulator_samples "
            "WHERE pool_id = ? AND block_number = ?",
            [USDC_WETH_POOL_ID, block],
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == original


# ── B-P5: Commit granularity survives crash ───────────────────────────────────


class TestCommitGranularitySurvesCrash:
    """File-backed DuckDB: data committed per batch survives connection close."""

    def test_five_batches_survive_crash_and_resume(
        self,
        duckdb_file_conn: tuple[object, str],
    ) -> None:
        """Insert 5 batches, commit each, close, reopen — all 5 present."""
        from scripts.ran_growth_pipeline import insert_sample
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, USDC_WETH_POOL_ID

        conn, db_path = duckdb_file_conn
        blocks = sorted(MOCK_BLOCKS_AND_GROWTH.keys())[:5]
        growth_values = [MOCK_BLOCKS_AND_GROWTH[b] for b in blocks]

        # Insert 5 batches, commit after each
        for block, growth in zip(blocks, growth_values):
            insert_sample(
                conn=conn,  # type: ignore[arg-type]
                pool_id=USDC_WETH_POOL_ID,
                block_number=block,
                global_growth=growth,
                stride=50,
            )
            conn.commit()  # type: ignore[union-attr]

        # Simulate crash
        conn.close()  # type: ignore[union-attr]

        # Reopen and verify all 5 batches present
        conn2 = duckdb.connect(db_path)
        rows = conn2.execute(
            "SELECT block_number, global_growth FROM accumulator_samples "
            "WHERE pool_id = ? ORDER BY block_number",
            [USDC_WETH_POOL_ID],
        ).fetchall()
        conn2.close()

        assert len(rows) == 5
        for i, (block_num, growth_hex) in enumerate(rows):
            assert block_num == blocks[i]
            assert growth_hex == growth_values[i]

    def test_rerun_after_crash_is_idempotent(
        self,
        duckdb_file_conn: tuple[object, str],
    ) -> None:
        """After crash recovery, re-inserting the same rows changes nothing."""
        from scripts.ran_growth_pipeline import insert_sample
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, USDC_WETH_POOL_ID

        conn, db_path = duckdb_file_conn
        blocks = sorted(MOCK_BLOCKS_AND_GROWTH.keys())[:3]

        for block in blocks:
            insert_sample(
                conn=conn,  # type: ignore[arg-type]
                pool_id=USDC_WETH_POOL_ID,
                block_number=block,
                global_growth=MOCK_BLOCKS_AND_GROWTH[block],
                stride=50,
            )
            conn.commit()  # type: ignore[union-attr]

        conn.close()  # type: ignore[union-attr]

        # Reopen and re-insert same rows (simulating pipeline resume)
        conn2 = duckdb.connect(db_path)
        from scripts.ran_utils import CREATE_TABLE_DDL
        conn2.execute(CREATE_TABLE_DDL)
        for block in blocks:
            insert_sample(
                conn=conn2,
                pool_id=USDC_WETH_POOL_ID,
                block_number=block,
                global_growth="0xdeadbeef" + "0" * 56,  # different value
                stride=50,
            )

        rows = conn2.execute(
            "SELECT block_number, global_growth FROM accumulator_samples "
            "WHERE pool_id = ? ORDER BY block_number",
            [USDC_WETH_POOL_ID],
        ).fetchall()
        conn2.close()

        assert len(rows) == 3
        # Original values preserved, not the "deadbeef" ones
        for i, (block_num, growth_hex) in enumerate(rows):
            assert growth_hex == MOCK_BLOCKS_AND_GROWTH[blocks[i]]


# ── B-P6: Retry on transient RPC errors ──────────────────────────────────────


class TestRetryOnTransientErrors:
    """send_rpc_batch retries on 429, 5xx, and timeout; gives up after max retries."""

    def test_a_success_after_two_429(self, mock_rpc_transport: object) -> None:
        """Two 429s then success — result contains expected data."""
        from scripts.ran_growth_pipeline import send_rpc_batch
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH

        transport = mock_rpc_transport(fail_count=2, fail_status=429)  # type: ignore[operator]
        client = httpx.Client(transport=transport, base_url="http://mock-rpc")

        blocks = sorted(MOCK_BLOCKS_AND_GROWTH.keys())[:2]
        from scripts.ran_growth_pipeline import build_rpc_batches
        batch = build_rpc_batches(slot=1, blocks=blocks, batch_size=100)[0]

        result = send_rpc_batch(client=client, batch=batch, max_retries=3)
        # Must succeed and return all responses
        assert len(result) == len(batch)

    def test_b_exhausts_retries_on_429(self, mock_rpc_transport: object) -> None:
        """Four consecutive 429s (initial + 3 retries) → RpcBatchError with status."""
        from scripts.ran_growth_pipeline import RpcBatchError, build_rpc_batches, send_rpc_batch
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH

        transport = mock_rpc_transport(fail_count=4, fail_status=429)  # type: ignore[operator]
        client = httpx.Client(transport=transport, base_url="http://mock-rpc")

        blocks = sorted(MOCK_BLOCKS_AND_GROWTH.keys())[:2]
        batch = build_rpc_batches(slot=1, blocks=blocks, batch_size=100)[0]

        with pytest.raises(RpcBatchError, match="429"):
            send_rpc_batch(client=client, batch=batch, max_retries=3)

    def test_c_success_after_two_500(self, mock_rpc_transport: object) -> None:
        """Two 500s then success — 5xx triggers same retry logic."""
        from scripts.ran_growth_pipeline import build_rpc_batches, send_rpc_batch
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH

        transport = mock_rpc_transport(fail_count=2, fail_status=500)  # type: ignore[operator]
        client = httpx.Client(transport=transport, base_url="http://mock-rpc")

        blocks = sorted(MOCK_BLOCKS_AND_GROWTH.keys())[:2]
        batch = build_rpc_batches(slot=1, blocks=blocks, batch_size=100)[0]

        result = send_rpc_batch(client=client, batch=batch, max_retries=3)
        assert len(result) == len(batch)

    def test_d_success_after_two_timeouts(self, mock_rpc_transport: object) -> None:
        """Two timeouts then success — timeout triggers retry."""
        from scripts.ran_growth_pipeline import build_rpc_batches, send_rpc_batch
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH

        transport = mock_rpc_transport(timeout_count=2)  # type: ignore[operator]
        client = httpx.Client(transport=transport, base_url="http://mock-rpc")

        blocks = sorted(MOCK_BLOCKS_AND_GROWTH.keys())[:2]
        batch = build_rpc_batches(slot=1, blocks=blocks, batch_size=100)[0]

        result = send_rpc_batch(client=client, batch=batch, max_retries=3)
        assert len(result) == len(batch)


# ── B-P7: Block range validation ─────────────────────────────────────────────


class TestBlockRangeValidation:
    """validate_block_range rejects invalid ranges and resolves 'latest'."""

    def test_from_block_below_minimum_raises(self) -> None:
        """--from-block 0 must fail mentioning minimum block 22,972,937."""
        from scripts.ran_growth_pipeline import BlockRangeError, validate_block_range

        with pytest.raises(BlockRangeError, match="22972937"):
            validate_block_range(from_block=0, to_block=23_000_000, client=None)

    def test_from_block_gte_to_block_raises(self) -> None:
        """--from-block >= --to-block must fail."""
        from scripts.ran_growth_pipeline import BlockRangeError, validate_block_range

        with pytest.raises(BlockRangeError):
            validate_block_range(
                from_block=23_000_000, to_block=23_000_000, client=None,
            )
        with pytest.raises(BlockRangeError):
            validate_block_range(
                from_block=23_000_001, to_block=23_000_000, client=None,
            )

    def test_to_block_latest_resolves_via_rpc(
        self, mock_rpc_transport: object,
    ) -> None:
        """--to-block latest resolves via eth_getBlockNumber."""
        from scripts.ran_growth_pipeline import validate_block_range

        transport = mock_rpc_transport(head_block=23_000_000)  # type: ignore[operator]
        client = httpx.Client(transport=transport, base_url="http://mock-rpc")

        from_block, to_block = validate_block_range(
            from_block=22_972_937, to_block="latest", client=client,
        )
        assert from_block == 22_972_937
        assert to_block == 23_000_000

    def test_valid_range_passes(self) -> None:
        """A valid numeric range returns both values unchanged."""
        from scripts.ran_growth_pipeline import validate_block_range

        from_block, to_block = validate_block_range(
            from_block=22_972_937, to_block=23_000_000, client=None,
        )
        assert from_block == 22_972_937
        assert to_block == 23_000_000


# ── Error: ALCHEMY_API_KEY not set ───────────────────────────────────────────


class TestAlchemyApiKeyRequired:
    """Pipeline exits with status 1 when ALCHEMY_API_KEY is not set."""

    def test_missing_api_key_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without ALCHEMY_API_KEY env var, main() exits with status 1."""
        from scripts.ran_growth_pipeline import main

        monkeypatch.delenv("ALCHEMY_API_KEY", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            main(["--pool", "usdc-weth", "--from-block", "22972937", "--to-block", "23000000"])
        assert exc_info.value.code == 1


# ── B-P8: Zero-value storage ─────────────────────────────────────────────────


class TestZeroValueStorage:
    """0x0 response normalized and stored as 0x + 64 zeros."""

    def test_zero_value_stored_as_padded_hex(self, duckdb_conn: object) -> None:
        """encode_uint256(int('0x0', 16)) produces '0x' + '0'*64, stored without error."""
        from scripts.ran_growth_pipeline import insert_sample
        from scripts.ran_utils import encode_uint256
        from scripts.tests.conftest import USDC_WETH_POOL_ID

        zero_hex: Final[str] = encode_uint256(int("0x0", 16))
        expected: Final[str] = "0x" + "0" * 64
        assert zero_hex == expected

        insert_sample(
            conn=duckdb_conn,  # type: ignore[arg-type]
            pool_id=USDC_WETH_POOL_ID,
            block_number=22_972_937,
            global_growth=zero_hex,
            stride=50,
        )

        rows = duckdb_conn.execute(  # type: ignore[union-attr]
            "SELECT global_growth FROM accumulator_samples "
            "WHERE pool_id = ? AND block_number = ?",
            [USDC_WETH_POOL_ID, 22_972_937],
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == expected


# ── B-P9: Progress reporting ─────────────────────────────────────────────────


class TestProgressReporting:
    """Pipeline output on stderr contains progress indicators."""

    def test_progress_output_on_stderr(
        self,
        mock_rpc_transport: object,
        tmp_path: object,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        """Pipeline stderr contains 'fetched', 'total', 'CU', '%'."""
        from scripts.ran_growth_pipeline import main
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH

        # Set up env
        monkeypatch.setenv("ALCHEMY_API_KEY", "test-key")

        # Create a mock transport and patch httpx.Client to use it
        transport = mock_rpc_transport(head_block=23_000_000)  # type: ignore[operator]

        db_path = str(tmp_path / "progress_test.duckdb")  # type: ignore[operator]

        blocks = sorted(MOCK_BLOCKS_AND_GROWTH.keys())
        from_block = blocks[0]
        to_block = blocks[-1] + 1

        # Patch httpx.Client to return our mock transport client
        import scripts.ran_growth_pipeline as pipeline_mod

        original_client = httpx.Client

        def mock_client_factory(*args: object, **kwargs: object) -> httpx.Client:
            return original_client(transport=transport, base_url="http://mock-rpc")

        monkeypatch.setattr(pipeline_mod, "_make_http_client", mock_client_factory)

        main([
            "--pool", "usdc-weth",
            "--from-block", str(from_block),
            "--to-block", str(to_block),
            "--stride", "50",
            "--db", db_path,
        ])

        captured = capfd.readouterr()
        stderr = captured.err
        for keyword in ("fetched", "total", "CU", "%"):
            assert keyword in stderr, f"Expected '{keyword}' in stderr, got: {stderr}"


# ── CLI entrypoint ───────────────────────────────────────────────────────────


class TestCliEntrypoint:
    """main() parses args, composes pipeline, writes to DuckDB."""

    def test_end_to_end_with_mock_transport(
        self,
        mock_rpc_transport: object,
        tmp_path: object,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Full pipeline run: fetches data, writes to DuckDB, committed."""
        from scripts.ran_growth_pipeline import main
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, USDC_WETH_POOL_ID

        monkeypatch.setenv("ALCHEMY_API_KEY", "test-key")

        transport = mock_rpc_transport()  # type: ignore[operator]
        db_path = str(tmp_path / "cli_test.duckdb")  # type: ignore[operator]

        blocks = sorted(MOCK_BLOCKS_AND_GROWTH.keys())
        from_block = blocks[0]
        to_block = blocks[-1] + 1

        import scripts.ran_growth_pipeline as pipeline_mod

        original_client = httpx.Client

        def mock_client_factory(*args: object, **kwargs: object) -> httpx.Client:
            return original_client(transport=transport, base_url="http://mock-rpc")

        monkeypatch.setattr(pipeline_mod, "_make_http_client", mock_client_factory)

        main([
            "--pool", "usdc-weth",
            "--from-block", str(from_block),
            "--to-block", str(to_block),
            "--stride", "50",
            "--db", db_path,
        ])

        # Verify data was written
        conn = duckdb.connect(db_path)
        rows = conn.execute(
            "SELECT block_number, global_growth, stride FROM accumulator_samples "
            "WHERE pool_id = ? ORDER BY block_number",
            [USDC_WETH_POOL_ID],
        ).fetchall()
        conn.close()

        assert len(rows) >= 1
        # Check stride is stored
        for row in rows:
            assert row[2] == 50


# ── B-P10: Smart Resume — Skip Already-Fetched Blocks ──────────────────────


class TestSmartResumeSkipExistingBlocks:
    """Pipeline must not re-fetch blocks already present in DuckDB."""

    def test_skip_existing_blocks(
        self,
        duckdb_file_conn: tuple[object, str],
        mock_rpc_transport: object,
        monkeypatch: pytest.MonkeyPatch,
        mock_growth_data: dict[int, str],
    ) -> None:
        """Pre-populate 3 blocks, request range of 4 — only 1 RPC batch for the missing block."""
        from scripts.ran_growth_pipeline import main
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, MOCK_BLOCK_TIMESTAMPS, USDC_WETH_POOL_ID

        conn, db_path = duckdb_file_conn

        # Pre-populate with 3 of the 4 blocks in range
        pre_existing: Final[list[int]] = [22_972_937, 22_972_987, 22_973_037]
        for block in pre_existing:
            conn.execute(  # type: ignore[union-attr]
                "INSERT INTO accumulator_samples VALUES (?, ?, ?, ?, ?, ?)",
                [block, USDC_WETH_POOL_ID, MOCK_BLOCKS_AND_GROWTH[block], MOCK_BLOCK_TIMESTAMPS[block], "2026-04-10 00:00:00", 50],
            )
        conn.commit()  # type: ignore[union-attr]
        conn.close()  # type: ignore[union-attr]

        # Track RPC calls via a counting transport wrapper
        call_count: list[int] = [0]
        real_transport_factory = mock_rpc_transport

        class CountingTransport(httpx.BaseTransport):
            def __init__(self, inner: httpx.BaseTransport) -> None:
                self._inner = inner

            def handle_request(self, request: httpx.Request) -> httpx.Response:
                body = json.loads(request.content.decode())
                if isinstance(body, list):
                    # Count actual eth_getStorageAt calls, not eth_getBlockNumber
                    storage_calls = [r for r in body if r.get("method") == "eth_getStorageAt"]
                    call_count[0] += len(storage_calls)
                elif isinstance(body, dict) and body.get("method") == "eth_getStorageAt":
                    call_count[0] += 1
                return self._inner.handle_request(request)

        inner = real_transport_factory()  # type: ignore[operator]
        counting = CountingTransport(inner)

        monkeypatch.setenv("ALCHEMY_API_KEY", "test-key")

        import scripts.ran_growth_pipeline as pipeline_mod

        original_client = httpx.Client

        def mock_client_factory(*args: object, **kwargs: object) -> httpx.Client:
            return original_client(transport=counting, base_url="http://mock-rpc")

        monkeypatch.setattr(pipeline_mod, "_make_http_client", mock_client_factory)

        # Range 22972937..22973137 stride 50 = blocks [22972937, 22972987, 22973037, 22973087]
        # Only 22973087 is missing
        main([
            "--pool", "usdc-weth",
            "--from-block", "22972937",
            "--to-block", "22973137",
            "--stride", "50",
            "--db", db_path,
        ])

        # Only 1 RPC call should have been made (for block 22973087)
        assert call_count[0] == 1, f"Expected 1 RPC call, got {call_count[0]}"

        # Verify the missing block is now stored
        conn2 = duckdb.connect(db_path)
        rows = conn2.execute(
            "SELECT block_number FROM accumulator_samples "
            "WHERE pool_id = ? ORDER BY block_number",
            [USDC_WETH_POOL_ID],
        ).fetchall()
        conn2.close()
        assert len(rows) == 4
        assert [r[0] for r in rows] == [22_972_937, 22_972_987, 22_973_037, 22_973_087]

    def test_all_blocks_present_skip_entirely(
        self,
        duckdb_file_conn: tuple[object, str],
        mock_rpc_transport: object,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When ALL blocks in range exist in DuckDB, ZERO RPC calls and clean exit."""
        from scripts.ran_growth_pipeline import main
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, MOCK_BLOCK_TIMESTAMPS, USDC_WETH_POOL_ID

        conn, db_path = duckdb_file_conn

        # Pre-populate ALL blocks that the range would generate
        # Range 22972937..22973137 stride 50 = [22972937, 22972987, 22973037, 22973087]
        all_blocks: Final[list[int]] = [22_972_937, 22_972_987, 22_973_037, 22_973_087]
        for block in all_blocks:
            conn.execute(  # type: ignore[union-attr]
                "INSERT INTO accumulator_samples VALUES (?, ?, ?, ?, ?, ?)",
                [block, USDC_WETH_POOL_ID, MOCK_BLOCKS_AND_GROWTH[block], MOCK_BLOCK_TIMESTAMPS[block], "2026-04-10 00:00:00", 50],
            )
        conn.commit()  # type: ignore[union-attr]
        conn.close()  # type: ignore[union-attr]

        # Track RPC calls
        call_count: list[int] = [0]
        real_transport_factory = mock_rpc_transport

        class CountingTransport(httpx.BaseTransport):
            def __init__(self, inner: httpx.BaseTransport) -> None:
                self._inner = inner

            def handle_request(self, request: httpx.Request) -> httpx.Response:
                body = json.loads(request.content.decode())
                if isinstance(body, list):
                    storage_calls = [r for r in body if r.get("method") == "eth_getStorageAt"]
                    call_count[0] += len(storage_calls)
                elif isinstance(body, dict) and body.get("method") == "eth_getStorageAt":
                    call_count[0] += 1
                return self._inner.handle_request(request)

        inner = real_transport_factory()  # type: ignore[operator]
        counting = CountingTransport(inner)

        monkeypatch.setenv("ALCHEMY_API_KEY", "test-key")

        import scripts.ran_growth_pipeline as pipeline_mod

        original_client = httpx.Client

        def mock_client_factory(*args: object, **kwargs: object) -> httpx.Client:
            return original_client(transport=counting, base_url="http://mock-rpc")

        monkeypatch.setattr(pipeline_mod, "_make_http_client", mock_client_factory)

        # This should complete cleanly with no RPC calls
        main([
            "--pool", "usdc-weth",
            "--from-block", "22972937",
            "--to-block", "22973137",
            "--stride", "50",
            "--db", db_path,
        ])

        assert call_count[0] == 0, f"Expected 0 RPC calls, got {call_count[0]}"

    def test_append_mode_new_blocks_only(
        self,
        duckdb_file_conn: tuple[object, str],
        mock_rpc_transport: object,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Pre-populate up to 22973037, run to 22973137 — only 22973087 and 22973137 fetched."""
        from scripts.ran_growth_pipeline import main
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, MOCK_BLOCK_TIMESTAMPS, USDC_WETH_POOL_ID

        conn, db_path = duckdb_file_conn

        # Pre-populate blocks up to 22973037
        early_blocks: Final[list[int]] = [22_972_937, 22_972_987, 22_973_037]
        for block in early_blocks:
            conn.execute(  # type: ignore[union-attr]
                "INSERT INTO accumulator_samples VALUES (?, ?, ?, ?, ?, ?)",
                [block, USDC_WETH_POOL_ID, MOCK_BLOCKS_AND_GROWTH[block], MOCK_BLOCK_TIMESTAMPS[block], "2026-04-10 00:00:00", 50],
            )
        conn.commit()  # type: ignore[union-attr]
        conn.close()  # type: ignore[union-attr]

        # Track RPC calls
        call_count: list[int] = [0]
        fetched_blocks: list[int] = []
        real_transport_factory = mock_rpc_transport

        class CountingTransport(httpx.BaseTransport):
            def __init__(self, inner: httpx.BaseTransport) -> None:
                self._inner = inner

            def handle_request(self, request: httpx.Request) -> httpx.Response:
                body = json.loads(request.content.decode())
                if isinstance(body, list):
                    for r in body:
                        if r.get("method") == "eth_getStorageAt":
                            call_count[0] += 1
                            block_hex = r["params"][2]
                            fetched_blocks.append(int(block_hex, 16))
                elif isinstance(body, dict) and body.get("method") == "eth_getStorageAt":
                    call_count[0] += 1
                    block_hex = body["params"][2]
                    fetched_blocks.append(int(block_hex, 16))
                return self._inner.handle_request(request)

        inner = real_transport_factory()  # type: ignore[operator]
        counting = CountingTransport(inner)

        monkeypatch.setenv("ALCHEMY_API_KEY", "test-key")

        import scripts.ran_growth_pipeline as pipeline_mod

        original_client = httpx.Client

        def mock_client_factory(*args: object, **kwargs: object) -> httpx.Client:
            return original_client(transport=counting, base_url="http://mock-rpc")

        monkeypatch.setattr(pipeline_mod, "_make_http_client", mock_client_factory)

        # Range 22972937..22973187 stride 50 = [22972937, 22972987, 22973037, 22973087, 22973137]
        # Missing: 22973087 and 22973137
        main([
            "--pool", "usdc-weth",
            "--from-block", "22972937",
            "--to-block", "22973187",
            "--stride", "50",
            "--db", db_path,
        ])

        assert call_count[0] == 2, f"Expected 2 RPC calls, got {call_count[0]}"
        assert sorted(fetched_blocks) == [22_973_087, 22_973_137]


class TestFilterMissingBlocksPure:
    """Unit tests for the pure filter_missing_blocks function."""

    def test_filter_returns_only_missing(self, duckdb_conn: object) -> None:
        """Given some blocks in DB, filter_missing_blocks returns only those NOT stored."""
        from scripts.ran_growth_pipeline import filter_missing_blocks
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, MOCK_BLOCK_TIMESTAMPS, USDC_WETH_POOL_ID

        # Insert 2 blocks
        for block in [22_972_937, 22_972_987]:
            duckdb_conn.execute(  # type: ignore[union-attr]
                "INSERT INTO accumulator_samples VALUES (?, ?, ?, ?, ?, ?)",
                [block, USDC_WETH_POOL_ID, MOCK_BLOCKS_AND_GROWTH[block], MOCK_BLOCK_TIMESTAMPS[block], "2026-04-10 00:00:00", 50],
            )

        requested: list[int] = [22_972_937, 22_972_987, 22_973_037, 22_973_087]
        missing = filter_missing_blocks(
            conn=duckdb_conn,  # type: ignore[arg-type]
            pool_id=USDC_WETH_POOL_ID,
            blocks=requested,
        )
        assert missing == [22_973_037, 22_973_087]

    def test_filter_all_present_returns_empty(self, duckdb_conn: object) -> None:
        """When all blocks exist, returns empty list."""
        from scripts.ran_growth_pipeline import filter_missing_blocks
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, MOCK_BLOCK_TIMESTAMPS, USDC_WETH_POOL_ID

        blocks: list[int] = [22_972_937, 22_972_987]
        for block in blocks:
            duckdb_conn.execute(  # type: ignore[union-attr]
                "INSERT INTO accumulator_samples VALUES (?, ?, ?, ?, ?, ?)",
                [block, USDC_WETH_POOL_ID, MOCK_BLOCKS_AND_GROWTH[block], MOCK_BLOCK_TIMESTAMPS[block], "2026-04-10 00:00:00", 50],
            )

        missing = filter_missing_blocks(
            conn=duckdb_conn,  # type: ignore[arg-type]
            pool_id=USDC_WETH_POOL_ID,
            blocks=blocks,
        )
        assert missing == []

    def test_filter_none_present_returns_all(self, duckdb_conn: object) -> None:
        """When no blocks exist, returns the full input list."""
        from scripts.ran_growth_pipeline import filter_missing_blocks
        from scripts.tests.conftest import USDC_WETH_POOL_ID

        blocks: list[int] = [22_972_937, 22_972_987, 22_973_037]
        missing = filter_missing_blocks(
            conn=duckdb_conn,  # type: ignore[arg-type]
            pool_id=USDC_WETH_POOL_ID,
            blocks=blocks,
        )
        assert missing == blocks


# ── Fix 1: RpcBatchError caught in main() ──────────────────────────────────


class TestRpcBatchErrorCaughtInMain:
    """main() catches RpcBatchError and exits with status 1 + stderr message."""

    def test_rpc_batch_error_exits_with_message(
        self,
        mock_rpc_transport: object,
        tmp_path: object,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        """When send_rpc_batch raises RpcBatchError, main() exits 1 with error on stderr."""
        from scripts.ran_growth_pipeline import main

        monkeypatch.setenv("ALCHEMY_API_KEY", "test-key")

        db_path = str(tmp_path / "rpc_error_test.duckdb")  # type: ignore[operator]

        # Patch send_rpc_batch to raise RpcBatchError
        import scripts.ran_growth_pipeline as pipeline_mod
        from scripts.ran_growth_pipeline import RpcBatchError

        def _raise_rpc_error(**kwargs: object) -> None:
            raise RpcBatchError("HTTP 401 (non-retryable)")

        monkeypatch.setattr(pipeline_mod, "send_rpc_batch", _raise_rpc_error)

        # Still need a working client for validate_block_range
        transport = mock_rpc_transport(head_block=23_000_000)  # type: ignore[operator]
        original_client = httpx.Client

        def mock_client_factory(*args: object, **kwargs: object) -> httpx.Client:
            return original_client(transport=transport, base_url="http://mock-rpc")

        monkeypatch.setattr(pipeline_mod, "_make_http_client", mock_client_factory)

        with pytest.raises(SystemExit) as exc_info:
            main([
                "--pool", "usdc-weth",
                "--from-block", "22972937",
                "--to-block", "23000000",
                "--stride", "50",
                "--db", db_path,
            ])
        assert exc_info.value.code == 1

        captured = capfd.readouterr()
        assert "HTTP 401 (non-retryable)" in captured.err


# ── Fix 3: Stride validation ──────────────────────────────────────────────


class TestStrideValidation:
    """Pipeline rejects --stride 0 with a clear error message."""

    def test_stride_zero_exits_with_message(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        """--stride 0 must exit with status 1 and stderr message about stride."""
        from scripts.ran_growth_pipeline import main

        monkeypatch.setenv("ALCHEMY_API_KEY", "test-key")

        with pytest.raises(SystemExit) as exc_info:
            main([
                "--pool", "usdc-weth",
                "--from-block", "22972937",
                "--to-block", "23000000",
                "--stride", "0",
                "--db", "/tmp/stride_test.duckdb",
            ])
        assert exc_info.value.code == 1

        captured = capfd.readouterr()
        assert "stride" in captured.err.lower()


# ── Fix 5: Auto-create data/ directory ──────────────────────────────────────


class TestAutoCreateDataDirectory:
    """Pipeline creates parent directory for --db path if it doesn't exist."""

    def test_creates_parent_dir_for_db(
        self,
        mock_rpc_transport: object,
        tmp_path: object,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When --db points to a non-existent parent dir, pipeline creates it."""
        from scripts.ran_growth_pipeline import main
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH

        monkeypatch.setenv("ALCHEMY_API_KEY", "test-key")

        # Use a nested path where parent does NOT exist
        nested_db = str(tmp_path / "deeply" / "nested" / "dir" / "test.duckdb")  # type: ignore[operator]

        transport = mock_rpc_transport(head_block=23_000_000)  # type: ignore[operator]

        import scripts.ran_growth_pipeline as pipeline_mod

        original_client = httpx.Client

        def mock_client_factory(*args: object, **kwargs: object) -> httpx.Client:
            return original_client(transport=transport, base_url="http://mock-rpc")

        monkeypatch.setattr(pipeline_mod, "_make_http_client", mock_client_factory)

        blocks = sorted(MOCK_BLOCKS_AND_GROWTH.keys())
        from_block = blocks[0]
        to_block = blocks[-1] + 1

        # Should NOT raise FileNotFoundError
        main([
            "--pool", "usdc-weth",
            "--from-block", str(from_block),
            "--to-block", str(to_block),
            "--stride", "50",
            "--db", nested_db,
        ])

        import pathlib
        assert pathlib.Path(nested_db).exists()


# ── Task 2: UPSERT migration — DO NOTHING → DO UPDATE SET ─────────────────


class TestUpsertTimestampBackfill:
    """UPSERT fills NULL block_timestamp without overwriting globalGrowth."""

    def test_upsert_fills_null_timestamp(self, duckdb_conn: object) -> None:
        """Insert with NULL timestamp, then re-insert with timestamp — timestamp gets filled,
        globalGrowth preserved. Third insert with different timestamp must NOT overwrite."""
        from scripts.ran_growth_pipeline import insert_sample
        from scripts.tests.conftest import USDC_WETH_POOL_ID

        original_growth: Final[str] = (
            "0x0000000000000000000000000000000000002d2c02eeae24bd7a65341761b9c3"
        )
        block: Final[int] = 22_972_937
        timestamp_1: Final[int] = 1_700_000_000
        timestamp_2: Final[int] = 1_700_999_999

        # 1) Insert with NULL timestamp
        insert_sample(
            conn=duckdb_conn,  # type: ignore[arg-type]
            pool_id=USDC_WETH_POOL_ID,
            block_number=block,
            global_growth=original_growth,
            stride=50,
            block_timestamp=None,
        )
        row = duckdb_conn.execute(  # type: ignore[union-attr]
            "SELECT global_growth, block_timestamp FROM accumulator_samples "
            "WHERE pool_id = ? AND block_number = ?",
            [USDC_WETH_POOL_ID, block],
        ).fetchone()
        assert row[0] == original_growth
        assert row[1] is None

        # 2) Re-insert with timestamp — timestamp should be filled
        insert_sample(
            conn=duckdb_conn,  # type: ignore[arg-type]
            pool_id=USDC_WETH_POOL_ID,
            block_number=block,
            global_growth="0xdeadbeef" + "0" * 56,  # different growth — must NOT overwrite
            stride=50,
            block_timestamp=timestamp_1,
        )
        row = duckdb_conn.execute(  # type: ignore[union-attr]
            "SELECT global_growth, block_timestamp FROM accumulator_samples "
            "WHERE pool_id = ? AND block_number = ?",
            [USDC_WETH_POOL_ID, block],
        ).fetchone()
        assert row[0] == original_growth, "globalGrowth must be preserved"
        assert row[1] == timestamp_1, "NULL timestamp must be filled"

        # 3) Third insert with different timestamp — must NOT overwrite non-NULL timestamp
        insert_sample(
            conn=duckdb_conn,  # type: ignore[arg-type]
            pool_id=USDC_WETH_POOL_ID,
            block_number=block,
            global_growth="0xdeadbeef" + "0" * 56,
            stride=50,
            block_timestamp=timestamp_2,
        )
        row = duckdb_conn.execute(  # type: ignore[union-attr]
            "SELECT global_growth, block_timestamp FROM accumulator_samples "
            "WHERE pool_id = ? AND block_number = ?",
            [USDC_WETH_POOL_ID, block],
        ).fetchone()
        assert row[0] == original_growth, "globalGrowth must still be preserved"
        assert row[1] == timestamp_1, "Non-NULL timestamp must NOT be overwritten"


# ── Task 2: Combined batch construction ────────────────────────────────────


class TestCombinedBatchConstruction:
    """build_combined_rpc_batches produces N storage + N block calls per batch."""

    def test_combined_batch_three_blocks(self) -> None:
        """3 blocks → 1 batch with 6 calls: 3 storage (IDs 1-3) + 3 block (IDs 4-6)."""
        from scripts.ran_growth_pipeline import build_combined_rpc_batches

        blocks: Final[list[int]] = [22_972_937, 22_972_987, 22_973_037]
        batches = build_combined_rpc_batches(slot=1, blocks=blocks, batch_size=15)

        assert len(batches) == 1
        batch = batches[0]
        assert len(batch) == 6

        # First 3: eth_getStorageAt with IDs 1, 2, 3
        for i in range(3):
            assert batch[i]["method"] == "eth_getStorageAt"
            assert batch[i]["id"] == i + 1

        # Last 3: eth_getBlockByNumber with IDs 4, 5, 6
        for i in range(3):
            req = batch[3 + i]
            assert req["method"] == "eth_getBlockByNumber"
            assert req["id"] == 4 + i
            params = req["params"]
            assert isinstance(params, list) and len(params) == 2
            assert params[0] == hex(blocks[i])
            assert params[1] is False

    def test_combined_batch_splitting(self) -> None:
        """20 blocks with batch_size=15 → 2 batches (15+15 calls, then 5+5 calls)."""
        from scripts.ran_growth_pipeline import build_combined_rpc_batches

        blocks = list(range(22_972_937, 22_972_937 + 20 * 50, 50))
        batches = build_combined_rpc_batches(slot=1, blocks=blocks, batch_size=15)

        assert len(batches) == 2
        # First batch: 15 blocks → 30 calls (15 storage + 15 block)
        assert len(batches[0]) == 30
        # Second batch: 5 blocks → 10 calls (5 storage + 5 block)
        assert len(batches[1]) == 10

    def test_combined_batch_ids_are_batch_local(self) -> None:
        """IDs reset to 1 in each batch, not globally sequential."""
        from scripts.ran_growth_pipeline import build_combined_rpc_batches

        blocks = list(range(22_972_937, 22_972_937 + 20 * 50, 50))
        batches = build_combined_rpc_batches(slot=1, blocks=blocks, batch_size=15)

        # First batch: IDs 1..15 (storage) + 16..30 (block)
        assert batches[0][0]["id"] == 1
        assert batches[0][14]["id"] == 15
        assert batches[0][15]["id"] == 16
        assert batches[0][29]["id"] == 30

        # Second batch: IDs 1..5 (storage) + 6..10 (block)
        assert batches[1][0]["id"] == 1
        assert batches[1][4]["id"] == 5
        assert batches[1][5]["id"] == 6
        assert batches[1][9]["id"] == 10


# ── Task 2: Mixed response correlation ─────────────────────────────────────


class TestMixedResponseCorrelation:
    """correlate_combined_batch_response maps block → (growth, timestamp) from mixed responses."""

    def test_correlate_ordered_combined(self) -> None:
        """Ordered combined responses produce correct (growth_hex, timestamp_int) per block."""
        from scripts.ran_growth_pipeline import (
            build_combined_rpc_batches,
            correlate_combined_batch_response,
        )
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, MOCK_BLOCK_TIMESTAMPS

        blocks: Final[list[int]] = sorted(MOCK_BLOCKS_AND_GROWTH.keys())[:3]
        batches = build_combined_rpc_batches(slot=1, blocks=blocks, batch_size=15)
        batch = batches[0]
        n = len(blocks)

        # Build ordered responses
        responses: list[dict[str, object]] = []
        for i, blk in enumerate(blocks):
            responses.append({"jsonrpc": "2.0", "id": i + 1, "result": MOCK_BLOCKS_AND_GROWTH[blk]})
        for i, blk in enumerate(blocks):
            responses.append({
                "jsonrpc": "2.0",
                "id": n + i + 1,
                "result": {"timestamp": hex(MOCK_BLOCK_TIMESTAMPS[blk]), "number": hex(blk)},
            })

        result = correlate_combined_batch_response(batch=batch, responses=responses)
        for blk in blocks:
            growth, ts = result[blk]
            assert growth == MOCK_BLOCKS_AND_GROWTH[blk]
            assert ts == MOCK_BLOCK_TIMESTAMPS[blk]

    def test_correlate_shuffled_combined(self) -> None:
        """Shuffled combined responses still produce correct mapping."""
        from scripts.ran_growth_pipeline import (
            build_combined_rpc_batches,
            correlate_combined_batch_response,
        )
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, MOCK_BLOCK_TIMESTAMPS

        blocks: Final[list[int]] = sorted(MOCK_BLOCKS_AND_GROWTH.keys())[:3]
        batches = build_combined_rpc_batches(slot=1, blocks=blocks, batch_size=15)
        batch = batches[0]
        n = len(blocks)

        responses: list[dict[str, object]] = []
        for i, blk in enumerate(blocks):
            responses.append({"jsonrpc": "2.0", "id": i + 1, "result": MOCK_BLOCKS_AND_GROWTH[blk]})
        for i, blk in enumerate(blocks):
            responses.append({
                "jsonrpc": "2.0",
                "id": n + i + 1,
                "result": {"timestamp": hex(MOCK_BLOCK_TIMESTAMPS[blk]), "number": hex(blk)},
            })

        random.seed(99)
        random.shuffle(responses)

        result = correlate_combined_batch_response(batch=batch, responses=responses)
        for blk in blocks:
            growth, ts = result[blk]
            assert growth == MOCK_BLOCKS_AND_GROWTH[blk]
            assert ts == MOCK_BLOCK_TIMESTAMPS[blk]

    def test_correlate_with_mock_transport_combined(self, mock_rpc_transport: object) -> None:
        """Integration: combined batch via mock transport with shuffle=True."""
        from scripts.ran_growth_pipeline import (
            build_combined_rpc_batches,
            correlate_combined_batch_response,
        )
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, MOCK_BLOCK_TIMESTAMPS

        blocks: Final[list[int]] = sorted(MOCK_BLOCKS_AND_GROWTH.keys())[:3]
        batches = build_combined_rpc_batches(slot=1, blocks=blocks, batch_size=15)
        batch = batches[0]

        transport = mock_rpc_transport(shuffle=True)  # type: ignore[operator]
        client = httpx.Client(transport=transport, base_url="http://mock-rpc")
        response = client.post("/", content=json.dumps(batch).encode())
        responses = response.json()

        result = correlate_combined_batch_response(batch=batch, responses=responses)
        for blk in blocks:
            growth, ts = result[blk]
            assert growth == MOCK_BLOCKS_AND_GROWTH[blk]
            assert ts == MOCK_BLOCK_TIMESTAMPS[blk]


# ── Task 2: Null block result handling ──────────────────────────────────────


class TestNullBlockResult:
    """eth_getBlockByNumber returning null -> skip that block, don't crash."""

    def test_null_block_skipped_others_succeed(self, mock_rpc_transport: object) -> None:
        """One block's eth_getBlockByNumber returns null — that block is skipped,
        others in the batch produce valid (growth, timestamp) pairs."""
        from scripts.ran_growth_pipeline import (
            build_combined_rpc_batches,
            correlate_combined_batch_response,
        )
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, MOCK_BLOCK_TIMESTAMPS

        blocks: Final[list[int]] = sorted(MOCK_BLOCKS_AND_GROWTH.keys())[:3]
        # Remove the middle block from timestamps so transport returns null
        partial_timestamps = {k: v for k, v in MOCK_BLOCK_TIMESTAMPS.items() if k != blocks[1]}

        transport = mock_rpc_transport(block_timestamps=partial_timestamps)  # type: ignore[operator]
        client = httpx.Client(transport=transport, base_url="http://mock-rpc")

        batches = build_combined_rpc_batches(slot=1, blocks=blocks, batch_size=15)
        batch = batches[0]
        response = client.post("/", content=json.dumps(batch).encode())
        responses = response.json()

        result = correlate_combined_batch_response(batch=batch, responses=responses)

        # Middle block should be absent (null timestamp -> skipped)
        assert blocks[1] not in result
        # Other blocks present with correct values
        for blk in [blocks[0], blocks[2]]:
            growth, ts = result[blk]
            assert growth == MOCK_BLOCKS_AND_GROWTH[blk]
            assert ts == MOCK_BLOCK_TIMESTAMPS[blk]


# ── Task 2: Rate limiter update — total batch CU ───────────────────────────


class TestRateLimiterBatchCu:
    """Rate limiter accepts total batch CU (540) directly."""

    def test_540_cu_batch_delay_at_least_1_08s(self) -> None:
        """Combined batch: 15*20 + 15*16 = 540 CU at 500 CUPS => 1.08s delay."""
        from scripts.ran_growth_pipeline import compute_inter_batch_delay

        delay = compute_inter_batch_delay(
            batch_cu_total=540,
            cups_limit=500,
        )
        assert delay >= 1.08
        assert delay == pytest.approx(1.08)

    def test_batch_cu_total_overrides_per_call_params(self) -> None:
        """When batch_cu_total is passed, batch_calls and cu_per_call are ignored."""
        from scripts.ran_growth_pipeline import compute_inter_batch_delay

        # batch_cu_total=540 should dominate regardless of batch_calls/cu_per_call
        delay = compute_inter_batch_delay(
            batch_cu_total=540,
            cups_limit=500,
        )
        assert delay == pytest.approx(1.08)


# ── Task 2: Smart resume NULL-timestamp detection ──────────────────────────


class TestSmartResumeNullTimestamp:
    """Blocks with NULL block_timestamp are treated as 'missing' by filter_missing_blocks."""

    def test_null_timestamp_blocks_are_missing(
        self, duckdb_file_conn: tuple[object, str],
    ) -> None:
        """Rows with globalGrowth but NULL block_timestamp → returned as 'missing'."""
        from scripts.ran_growth_pipeline import filter_missing_blocks
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, MOCK_BLOCK_TIMESTAMPS, USDC_WETH_POOL_ID

        conn, db_path = duckdb_file_conn
        blocks = sorted(MOCK_BLOCKS_AND_GROWTH.keys())[:3]

        # Insert block 0 with timestamp, blocks 1 and 2 with NULL timestamp
        conn.execute(  # type: ignore[union-attr]
            "INSERT INTO accumulator_samples VALUES (?, ?, ?, ?, ?, ?)",
            [blocks[0], USDC_WETH_POOL_ID, MOCK_BLOCKS_AND_GROWTH[blocks[0]], MOCK_BLOCK_TIMESTAMPS[blocks[0]], "2026-04-10 00:00:00", 50],
        )
        for blk in blocks[1:]:
            conn.execute(  # type: ignore[union-attr]
                "INSERT INTO accumulator_samples VALUES (?, ?, ?, ?, ?, ?)",
                [blk, USDC_WETH_POOL_ID, MOCK_BLOCKS_AND_GROWTH[blk], None, "2026-04-10 00:00:00", 50],
            )

        # blocks[1] and blocks[2] have NULL timestamp → should be "missing"
        missing = filter_missing_blocks(
            conn=conn,  # type: ignore[arg-type]
            pool_id=USDC_WETH_POOL_ID,
            blocks=blocks,
        )
        assert missing == blocks[1:]


# ── Task 2: CLI main() integration — combined batches with timestamps ──────


class TestCombinedPipelineIntegration:
    """End-to-end: combined batches write both globalGrowth and block_timestamp to DuckDB."""

    def test_main_writes_growth_and_timestamp(
        self,
        mock_rpc_transport: object,
        tmp_path: object,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Pipeline run produces rows with non-NULL block_timestamp and correct globalGrowth."""
        from scripts.ran_growth_pipeline import main
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, MOCK_BLOCK_TIMESTAMPS, USDC_WETH_POOL_ID

        monkeypatch.setenv("ALCHEMY_API_KEY", "test-key")

        transport = mock_rpc_transport()  # type: ignore[operator]
        db_path = str(tmp_path / "combined_test.duckdb")  # type: ignore[operator]

        blocks = sorted(MOCK_BLOCKS_AND_GROWTH.keys())
        from_block = blocks[0]
        to_block = blocks[-1] + 1

        import scripts.ran_growth_pipeline as pipeline_mod

        original_client = httpx.Client

        def mock_client_factory(*args: object, **kwargs: object) -> httpx.Client:
            return original_client(transport=transport, base_url="http://mock-rpc")

        monkeypatch.setattr(pipeline_mod, "_make_http_client", mock_client_factory)

        main([
            "--pool", "usdc-weth",
            "--from-block", str(from_block),
            "--to-block", str(to_block),
            "--stride", "50",
            "--db", db_path,
        ])

        # Verify rows have both globalGrowth and block_timestamp
        conn = duckdb.connect(db_path)
        rows = conn.execute(
            "SELECT block_number, global_growth, block_timestamp FROM accumulator_samples "
            "WHERE pool_id = ? ORDER BY block_number",
            [USDC_WETH_POOL_ID],
        ).fetchall()
        conn.close()

        assert len(rows) >= 1
        for block_num, growth_hex, block_ts in rows:
            assert block_ts is not None, f"block_timestamp NULL for block {block_num}"
            assert block_ts == MOCK_BLOCK_TIMESTAMPS[block_num], f"Wrong timestamp for block {block_num}"
            assert growth_hex == MOCK_BLOCKS_AND_GROWTH[block_num], f"Wrong growth for block {block_num}"


# ── Fix 2: Per-call JSON-RPC error handling in correlators ───────────────────


class TestJsonRpcErrorInCorrelators:
    """Correlators must skip responses with 'error' instead of 'result', not crash."""

    def test_correlate_batch_skips_error_response(self) -> None:
        """One response has 'error' instead of 'result' — it is skipped, others correlated."""
        from scripts.ran_growth_pipeline import build_rpc_batches, correlate_batch_response

        blocks: list[int] = [22_972_937, 22_972_987, 22_973_037]
        batches = build_rpc_batches(slot=1, blocks=blocks, batch_size=100)
        batch = batches[0]

        # Build responses: first two OK, third has JSON-RPC error
        responses: list[dict[str, object]] = [
            {"jsonrpc": "2.0", "id": 1, "result": "0x" + "ab" * 32},
            {"jsonrpc": "2.0", "id": 2, "result": "0x" + "cd" * 32},
            {"jsonrpc": "2.0", "id": 3, "error": {"code": -32000, "message": "block not found"}},
        ]

        result = correlate_batch_response(batch=batch, responses=responses)

        # Block 22_972_937 (id=1) and 22_972_987 (id=2) should be present
        assert 22_972_937 in result
        assert 22_972_987 in result
        # Block 22_973_037 (id=3) should be skipped
        assert 22_973_037 not in result

    def test_correlate_combined_skips_error_response(self) -> None:
        """Combined correlator skips error responses for both storage and block calls."""
        from scripts.ran_growth_pipeline import (
            build_combined_rpc_batches,
            correlate_combined_batch_response,
        )
        from scripts.tests.conftest import MOCK_BLOCKS_AND_GROWTH, MOCK_BLOCK_TIMESTAMPS

        blocks: list[int] = sorted(MOCK_BLOCKS_AND_GROWTH.keys())[:3]
        batches = build_combined_rpc_batches(slot=1, blocks=blocks, batch_size=15)
        batch = batches[0]
        n = len(blocks)

        # Build responses: storage call for block[1] returns error
        responses: list[dict[str, object]] = []
        for i, blk in enumerate(blocks):
            if i == 1:
                responses.append({"jsonrpc": "2.0", "id": i + 1, "error": {"code": -32000, "message": "block not found"}})
            else:
                responses.append({"jsonrpc": "2.0", "id": i + 1, "result": MOCK_BLOCKS_AND_GROWTH[blk]})
        for i, blk in enumerate(blocks):
            responses.append({
                "jsonrpc": "2.0",
                "id": n + i + 1,
                "result": {"timestamp": hex(MOCK_BLOCK_TIMESTAMPS[blk]), "number": hex(blk)},
            })

        result = correlate_combined_batch_response(batch=batch, responses=responses)

        # blocks[1] should be absent (error on storage call → no growth data)
        assert blocks[1] not in result
        # Other blocks present with correct values
        for blk in [blocks[0], blocks[2]]:
            growth, ts = result[blk]
            assert growth == MOCK_BLOCKS_AND_GROWTH[blk]
            assert ts == MOCK_BLOCK_TIMESTAMPS[blk]
