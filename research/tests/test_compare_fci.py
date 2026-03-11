"""Tests for compare_fci — unit tests with mocked data."""
from __future__ import annotations

import json
from pathlib import Path

from compare_fci import parse_index_response, check_convergence, load_off_chain, encode_pool_key


def test_parse_index_response_zeros():
    """All-zero response decodes to (0, 0, 0)."""
    raw = "0x" + "00" * 96
    idx, theta, pos = parse_index_response(raw)
    assert idx == 0
    assert theta == 0
    assert pos == 0


def test_parse_index_response_distinct_values():
    """Verify word boundaries with distinct non-zero values in each slot."""
    # indexA=1, thetaSum=2, posCount=3 — each in last byte of 32-byte word
    word1 = "00" * 31 + "01"  # indexA = 1
    word2 = "00" * 31 + "02"  # thetaSum = 2
    word3 = "00" * 31 + "03"  # posCount = 3
    raw = "0x" + word1 + word2 + word3
    idx, theta, pos = parse_index_response(raw)
    assert idx == 1
    assert theta == 2
    assert pos == 3


def test_parse_index_response_large_values():
    """Verify large uint128/uint256 values decode correctly."""
    # indexA = 2^128 - 1 (max uint128)
    word1 = "00" * 16 + "ff" * 16
    # thetaSum = 2^256 - 1 (max uint256)
    word2 = "ff" * 32
    # posCount = 42
    word3 = "00" * 31 + "2a"
    raw = "0x" + word1 + word2 + word3
    idx, theta, pos = parse_index_response(raw)
    assert idx == (1 << 128) - 1
    assert theta == (1 << 256) - 1
    assert pos == 42


def test_check_convergence_pass():
    result = check_convergence(
        on_chain_index=1000,
        off_chain_index=1005,
        epsilon=0.01,
    )
    assert result.passed is True
    assert result.drift < 0.01


def test_check_convergence_fail():
    result = check_convergence(
        on_chain_index=1000,
        off_chain_index=1200,
        epsilon=0.01,
    )
    assert result.passed is False
    assert result.drift > 0.01


def test_check_convergence_both_zero():
    """Both zero should pass (drift=0)."""
    result = check_convergence(on_chain_index=0, off_chain_index=0, epsilon=0.01)
    assert result.passed is True
    assert result.drift == 0.0


def test_encode_pool_key_length():
    """PoolKey encodes to 5 x 32-byte words = 320 hex chars."""
    encoded = encode_pool_key(
        "0x" + "00" * 20,
        "0x" + "00" * 20,
        500,
        10,
        "0x" + "00" * 20,
    )
    assert len(encoded) == 320  # 5 * 64 hex chars


def test_encode_pool_key_negative_tick_spacing():
    """Negative tick spacing encodes as two's complement."""
    encoded = encode_pool_key(
        "0x" + "00" * 20,
        "0x" + "00" * 20,
        500,
        -1,
        "0x" + "00" * 20,
    )
    # int24(-1) in 256-bit = 0xff...ff
    tick_word = encoded[3 * 64 : 4 * 64]
    assert tick_word == "f" * 64


def test_load_off_chain_list(tmp_path: Path):
    """load_off_chain returns list as-is when JSON root is a list."""
    fixture = [{"indexA": 42, "posCount": 1}]
    p = tmp_path / "test_fixture.json"
    p.write_text(json.dumps(fixture))
    result = load_off_chain(str(p))
    assert len(result) == 1
    assert result[0]["indexA"] == 42


def test_load_off_chain_dict(tmp_path: Path):
    """load_off_chain wraps a dict in a list."""
    fixture = {"indexA": 42, "posCount": 1}
    p = tmp_path / "test_fixture.json"
    p.write_text(json.dumps(fixture))
    result = load_off_chain(str(p))
    assert len(result) == 1
    assert result[0]["indexA"] == 42
