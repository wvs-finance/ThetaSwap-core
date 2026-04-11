"""Tests for ran_utils — shared utilities for the RAN growth pipeline.

Strict TDD: each behavior tested in isolation.
"""
from __future__ import annotations

from typing import Final

import pytest


# ── B-U1: Storage slot derivation ──

USDC_WETH_POOL_ID: Final[str] = (
    "0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657"
)
USDC_WETH_GOLDEN_SLOT: Final[int] = (
    64786232186666095359405191405389153200399579038162050191060476505946183470809
)


def test_derive_pool_rewards_slot_usdc_weth() -> None:
    """Slot derivation for USDC/WETH must match the golden literal."""
    from scripts.ran_utils import derive_pool_rewards_slot

    result = derive_pool_rewards_slot(
        pool_id=USDC_WETH_POOL_ID,
        mapping_slot=7,
        reward_growth_size=16_777_216,
    )
    assert result == USDC_WETH_GOLDEN_SLOT


# ── B-U2: Hex encoding round-trip ──


def test_encode_uint256_zero() -> None:
    """encode_uint256(0) must produce 66-char hex with 64 zero digits."""
    from scripts.ran_utils import encode_uint256

    assert encode_uint256(0) == "0x" + "0" * 64


def test_encode_uint256_max() -> None:
    """encode_uint256(2**256 - 1) must produce all-f hex."""
    from scripts.ran_utils import encode_uint256

    assert encode_uint256(2**256 - 1) == "0x" + "f" * 64


def test_decode_encode_round_trip() -> None:
    """decode(encode(v)) must equal v for arbitrary values."""
    from scripts.ran_utils import decode_uint256, encode_uint256

    for v in (0, 1, 42, 2**128, 2**256 - 1):
        assert decode_uint256(encode_uint256(v)) == v


# ── B-U3: Pool configuration ──

WETH_USDT_POOL_ID: Final[str] = (
    "0x90078845bceb849b171873cfbc92db8540e9c803ff57d9d21b1215ec158e79b3"
)
WETH_USDT_GOLDEN_SLOT: Final[int] = (
    17382517064296572403152036871109474196302295655646069203304358844708054916277
)


def test_pool_config_is_frozen() -> None:
    """PoolConfig must be immutable (frozen dataclass)."""
    from scripts.ran_utils import PoolConfig

    cfg = PoolConfig(
        pool_id="0xdead",
        pool_rewards_slot=1,
        reward_growth_size=1,
        name="test",
    )
    with pytest.raises(AttributeError):
        cfg.name = "mutated"  # type: ignore[misc]


def test_pool_registry_usdc_weth() -> None:
    """USDC_WETH pool must exist in registry with correct slot."""
    from scripts.ran_utils import POOL_REGISTRY

    cfg = POOL_REGISTRY["usdc-weth"]
    assert cfg.pool_id == USDC_WETH_POOL_ID
    assert cfg.pool_rewards_slot == USDC_WETH_GOLDEN_SLOT
    assert cfg.reward_growth_size == 16_777_216


def test_pool_registry_weth_usdt() -> None:
    """WETH_USDT pool must exist in registry with correct slot."""
    from scripts.ran_utils import POOL_REGISTRY

    cfg = POOL_REGISTRY["weth-usdt"]
    assert cfg.pool_id == WETH_USDT_POOL_ID
    assert cfg.pool_rewards_slot == WETH_USDT_GOLDEN_SLOT
    assert cfg.reward_growth_size == 16_777_216


def test_pool_registry_unknown_raises() -> None:
    """Accessing an unknown pool name must raise KeyError."""
    from scripts.ran_utils import POOL_REGISTRY

    with pytest.raises(KeyError):
        _ = POOL_REGISTRY["nonexistent-pool"]


# ── B-U4: decode_uint256 overflow guard ──


def test_decode_uint256_overflow_rejects_257_bit_value() -> None:
    """decode_uint256 must reject values >= 2**256 (257-bit hex)."""
    from scripts.ran_utils import decode_uint256

    with pytest.raises((ValueError, OverflowError)):
        decode_uint256("0x" + "f" * 65)
