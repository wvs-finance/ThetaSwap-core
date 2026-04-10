"""Tests for RAN growth pipeline — Task 3: batch construction, correlation, rate limiting."""
from __future__ import annotations

import json
import random
from typing import Final

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
