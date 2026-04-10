"""Shared utilities for the RAN growth pipeline."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Final

from eth_abi import encode as abi_encode  # type: ignore[import-untyped]
from eth_hash.auto import keccak  # type: ignore[import-untyped]


def derive_pool_rewards_slot(
    pool_id: str,
    mapping_slot: int,
    reward_growth_size: int,
) -> int:
    """Derive the storage slot for a pool's reward-growth array.

    Mirrors Solidity: ``keccak256(abi.encode(poolId, mappingSlot)) + rewardGrowthSize``.
    """
    pid_bytes: bytes = bytes.fromhex(pool_id.removeprefix("0x"))
    slot_hash: bytes = keccak(abi_encode(["bytes32", "uint256"], [pid_bytes, mapping_slot]))
    return int.from_bytes(slot_hash, "big") + reward_growth_size


def encode_uint256(value: int) -> str:
    """Encode an unsigned 256-bit integer as a 0x-prefixed, zero-padded hex string."""
    return "0x" + value.to_bytes(32, "big").hex()


def decode_uint256(hex_str: str) -> int:
    """Decode a 0x-prefixed hex string back to an unsigned 256-bit integer."""
    value: int = int(hex_str, 16)
    if value >= 2**256:
        raise OverflowError(f"Value exceeds uint256 range: {value}")
    return value


# ── Pool configuration ───────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class PoolConfig:
    """Immutable configuration for a monitored Angstrom pool."""

    pool_id: str
    pool_rewards_slot: int
    reward_growth_size: int
    name: str


def _build_pool_config(pool_id: str, name: str) -> PoolConfig:
    """Build a PoolConfig with standard mapping_slot=7, size=16_777_216."""
    mapping_slot: Final[int] = 7
    reward_growth_size: Final[int] = 16_777_216
    return PoolConfig(
        pool_id=pool_id,
        pool_rewards_slot=derive_pool_rewards_slot(pool_id, mapping_slot, reward_growth_size),
        reward_growth_size=reward_growth_size,
        name=name,
    )


POOL_REGISTRY: Final[dict[str, PoolConfig]] = {
    "usdc-weth": _build_pool_config(
        "0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657",
        "usdc-weth",
    ),
    "weth-usdt": _build_pool_config(
        "0x90078845bceb849b171873cfbc92db8540e9c803ff57d9d21b1215ec158e79b3",
        "weth-usdt",
    ),
}


# ── Constants ─────────────────────────────────────────────────────────────────

ANGSTROM_HOOK: Final[str] = "0x0000000aa232009084Bd71A5797d089AA4Edfad4"
POOL_MANAGER: Final[str] = "0x000000000004444c5dc75cB358380D2e3dE08A90"
BLOCK_NUMBER_0: Final[int] = 22_972_937

CREATE_TABLE_DDL: Final[str] = (
    "CREATE TABLE IF NOT EXISTS accumulator_samples ("
    "block_number UBIGINT, "
    "pool_id VARCHAR, "
    "global_growth VARCHAR, "
    "sampled_at TIMESTAMP, "
    "stride USMALLINT, "
    "PRIMARY KEY (pool_id, block_number))"
)


# ── RPC helper (tested in Task 6) ────────────────────────────────────────────


def read_storage_at(address: str, slot: int, block: int, rpc_url: str) -> int:
    """Read a single storage slot via ``cast storage`` subprocess."""
    hex_slot: str = encode_uint256(slot)
    result: subprocess.CompletedProcess[str] = subprocess.run(
        ["cast", "storage", address, hex_slot, "--block", str(block), "--rpc-url", rpc_url],
        capture_output=True,
        text=True,
        check=True,
    )
    return decode_uint256(result.stdout.strip())
