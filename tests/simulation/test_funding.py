"""Tests for funding rate mechanics — from funding-rate.tex."""
import math

from simulation.funding import (
    mark_price,
    funding_rate,
    dynamic_fee,
    funding_payment,
)


def test_mark_price_at_half():
    """x = 0.5 -> p = 1.0"""
    assert mark_price(0.5) == 1.0


def test_mark_price_at_one():
    """x = 1.0 -> p = 0.0"""
    assert mark_price(1.0) == 0.0


def test_funding_rate_zero_basis():
    """No basis -> no funding rate."""
    r = funding_rate(basis=0.0, p_index=1.0, alpha=0.1)
    assert r == 0.0


def test_funding_rate_positive_basis():
    """r = α * |basis| / (p_index + 1)."""
    r = funding_rate(basis=0.5, p_index=1.0, alpha=0.1)
    expected = 0.1 * 0.5 / 2.0  # 0.025
    assert math.isclose(r, expected, rel_tol=1e-12)


def test_dynamic_fee_mark_above_index():
    """Mark > index: fee increases."""
    fee = dynamic_fee(
        basis=0.5, p_index=1.0, alpha=0.1,
        fee_base=0.003, fee_max=0.01,
    )
    assert fee > 0.003


def test_dynamic_fee_mark_below_index():
    """Mark < index: fee decreases."""
    fee = dynamic_fee(
        basis=-0.5, p_index=1.0, alpha=0.1,
        fee_base=0.003, fee_max=0.01,
    )
    assert fee < 0.003


def test_dynamic_fee_capped():
    """Fee never exceeds fee_max."""
    fee = dynamic_fee(
        basis=100.0, p_index=0.01, alpha=10.0,
        fee_base=0.003, fee_max=0.01,
    )
    assert fee <= 0.01


def test_dynamic_fee_floor():
    """Fee never goes negative."""
    fee = dynamic_fee(
        basis=-100.0, p_index=0.01, alpha=10.0,
        fee_base=0.003, fee_max=0.01,
    )
    assert fee >= 0.0


def test_funding_payment_sign():
    """Positive basis -> positive payment (longs pay shorts)."""
    f = funding_payment(basis=0.5, p_index=1.0, alpha=0.1)
    assert f > 0.0
