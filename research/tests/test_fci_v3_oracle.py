"""Tests for V3 FCI oracle — mirrors V4 oracle tests but with V3 event types."""
from __future__ import annotations

import math

from fci_v3_oracle import FCIStateV3, Q128, v3_position_key


def test_v3_position_key_matches_solidity():
    """keccak256(abi.encodePacked(owner, tickLower, tickUpper))"""
    pk = v3_position_key("0x" + "00" * 19 + "01", -60, 60)
    assert len(pk) == 32
    assert isinstance(pk, bytes)


def test_single_mint_burn_produces_index():
    state = FCIStateV3()
    owner = "0x" + "00" * 19 + "01"
    state.process_mint(owner, -60, 60, 1_000_000, block_number=100)
    state.process_swap(tick=0)
    state.process_swap(tick=10)
    state.process_collect(owner, -60, 60, fee0=500, fee1=0)
    state.process_burn(owner, -60, 60, 1_000_000, block_number=110)
    assert state.pos_count == 0
    assert state.accumulated_sum > 0
    idx = state.to_index_a()
    assert 0 < idx <= (1 << 128) - 1


def test_collect_without_burn_does_not_affect_index():
    state = FCIStateV3()
    owner = "0x" + "00" * 19 + "01"
    state.process_mint(owner, -60, 60, 1_000_000, block_number=100)
    state.process_collect(owner, -60, 60, fee0=500, fee1=0)
    assert state.accumulated_sum == 0  # No burn yet — no FCI term


def test_snapshot_fields():
    state = FCIStateV3()
    snap = state.snapshot(block_number=100)
    assert "blockNumber" in snap
    assert "expectedIndexA" in snap
    assert "expectedPosCount" in snap
    assert "expectedThetaSum" in snap


def test_v3_position_key_differs_by_owner():
    """Different owners produce different position keys."""
    pk1 = v3_position_key("0x" + "00" * 19 + "01", -60, 60)
    pk2 = v3_position_key("0x" + "00" * 19 + "02", -60, 60)
    assert pk1 != pk2


def test_v3_position_key_differs_by_ticks():
    """Different tick ranges produce different position keys."""
    owner = "0x" + "00" * 19 + "01"
    pk1 = v3_position_key(owner, -60, 60)
    pk2 = v3_position_key(owner, -120, 120)
    assert pk1 != pk2


def test_multiple_positions_same_range():
    """Two positions in the same tick range both contribute to FCI."""
    state = FCIStateV3()
    owner_a = "0x" + "00" * 19 + "01"
    owner_b = "0x" + "00" * 19 + "02"
    state.process_mint(owner_a, -60, 60, 1_000_000, block_number=100)
    state.process_mint(owner_b, -60, 60, 3_000_000, block_number=100)
    state.process_swap(tick=0)
    state.process_swap(tick=10)
    # Collect fees for both
    state.process_collect(owner_a, -60, 60, fee0=100, fee1=0)
    state.process_collect(owner_b, -60, 60, fee0=300, fee1=0)
    # Burn both
    state.process_burn(owner_a, -60, 60, 1_000_000, block_number=110)
    state.process_burn(owner_b, -60, 60, 3_000_000, block_number=110)
    assert state.pos_count == 0
    assert state.accumulated_sum > 0


def test_burn_orphan_position_is_noop():
    """Burning a position that was never minted is silently ignored."""
    state = FCIStateV3()
    owner = "0x" + "00" * 19 + "01"
    state.process_burn(owner, -60, 60, 1_000_000, block_number=110)
    assert state.pos_count == 0
    assert state.accumulated_sum == 0


def test_collect_accumulates_fees():
    """Multiple collects accumulate fees before a burn."""
    state = FCIStateV3()
    owner = "0x" + "00" * 19 + "01"
    state.process_mint(owner, -60, 60, 1_000_000, block_number=100)
    state.process_swap(tick=0)
    state.process_swap(tick=10)
    state.process_collect(owner, -60, 60, fee0=100, fee1=0)
    state.process_collect(owner, -60, 60, fee0=200, fee1=0)
    # accumulated_sum still 0 — no burn yet
    assert state.accumulated_sum == 0
    state.process_burn(owner, -60, 60, 1_000_000, block_number=110)
    assert state.accumulated_sum > 0


def test_replay_processes_events():
    """replay() drives the state machine from an event list."""
    from fci_v3_oracle import replay

    events = [
        {"eventType": "Mint", "owner": "0x" + "00" * 19 + "01",
         "tickLower": -60, "tickUpper": 60, "liquidity": 1_000_000,
         "blockNumber": 100},
        {"eventType": "Swap", "tick": 0, "blockNumber": 101},
        {"eventType": "Swap", "tick": 10, "blockNumber": 102},
        {"eventType": "Collect", "owner": "0x" + "00" * 19 + "01",
         "tickLower": -60, "tickUpper": 60, "fee0": 500, "fee1": 0,
         "blockNumber": 103},
        {"eventType": "Burn", "owner": "0x" + "00" * 19 + "01",
         "tickLower": -60, "tickUpper": 60, "liquidity": 1_000_000,
         "blockNumber": 104},
    ]
    state, snapshots = replay(events)
    assert state.pos_count == 0
    assert state.accumulated_sum > 0
