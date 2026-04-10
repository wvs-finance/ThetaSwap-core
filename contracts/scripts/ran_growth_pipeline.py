"""RAN growth pipeline — batch JSON-RPC, response correlation, rate limiting."""
from __future__ import annotations

from typing import Final

from scripts.ran_utils import ANGSTROM_HOOK, encode_uint256


# ── B-P1: Batch JSON-RPC construction ───────────────────────────────────────


def build_rpc_batches(
    *,
    slot: int,
    blocks: list[int],
    batch_size: int = 15,
) -> list[list[dict[str, object]]]:
    """Build JSON-RPC 2.0 batch payloads for eth_getStorageAt.

    Each request gets a globally unique ``id`` (sequential from 1).
    Batches are capped at ``batch_size`` requests each.

    Returns a list of batches, where each batch is a list of JSON-RPC request dicts.
    """
    address: Final[str] = ANGSTROM_HOOK
    slot_hex: Final[str] = encode_uint256(slot)

    all_requests: list[dict[str, object]] = []
    for idx, block in enumerate(blocks, start=1):
        block_hex: str = hex(block)
        all_requests.append(
            {
                "jsonrpc": "2.0",
                "id": idx,
                "method": "eth_getStorageAt",
                "params": [address, slot_hex, block_hex],
            }
        )

    batches: list[list[dict[str, object]]] = []
    for i in range(0, len(all_requests), batch_size):
        batches.append(all_requests[i : i + batch_size])

    return batches


# ── B-P2: Response correlation by ID ────────────────────────────────────────


def correlate_batch_response(
    *,
    batch: list[dict[str, object]],
    responses: list[dict[str, object]],
) -> dict[int, str]:
    """Correlate JSON-RPC batch responses to block numbers using the ``id`` field.

    Takes a single batch of requests and its corresponding responses.
    Responses may arrive in any order.  This function builds an id-to-block lookup
    from the original requests, then maps each response's ``id`` to its block number
    and extracts the ``result`` value.

    Returns a dict mapping block_number (int) -> hex result (str).
    """
    # Build id -> block_number lookup from original requests
    id_to_block: dict[object, int] = {}
    for req in batch:
        req_id: object = req["id"]
        params: list[str] = req["params"]  # type: ignore[assignment]
        block_hex: str = str(params[2])
        block_num: int = int(block_hex, 16)
        id_to_block[req_id] = block_num

    # Correlate by id, never by position
    result: dict[int, str] = {}
    for resp in responses:
        resp_id: object = resp["id"]
        block_num = id_to_block[resp_id]
        result[block_num] = str(resp["result"])

    return result


# ── B-P3: Rate limiting ─────────────────────────────────────────────────────

SAFETY_FLOOR_SECONDS: Final[float] = 1.0


def compute_inter_batch_delay(
    *,
    batch_calls: int,
    cu_per_call: int,
    cups_limit: int,
) -> float:
    """Compute the minimum inter-batch delay in seconds.

    ``batch_calls`` is the number of RPC calls in a single batch.
    ``cu_per_call`` is the compute-unit cost of each call.
    ``cups_limit`` is the provider's compute-units-per-second cap.

    The raw delay is ``(batch_calls * cu_per_call) / cups_limit``.
    A mandatory safety floor of 1.0 second is enforced regardless of
    raw computation.

    Pure function — no sleeping, no side effects.
    """
    raw_delay: float = (batch_calls * cu_per_call) / cups_limit
    return max(raw_delay, SAFETY_FLOOR_SECONDS)
