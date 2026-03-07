#!/usr/bin/env python3
"""
Off-chain HHI oracle for Foundry FFI fuzz tests.

Input:  hex-encoded ABI (uint256[] liquidities, uint256[] blockLifetimes)
Output: hex-encoded ABI (uint256 expectedHHI, uint256 expectedIndexA)

Q128 arithmetic uses Python native ints (arbitrary precision).
"""
import sys
from eth_abi import encode, decode

Q128 = 1 << 128
INDEX_ONE = (1 << 128) - 1  # type(uint128).max


def floor_one(n: int) -> int:
    return 1 if n == 0 else n


def isqrt(n: int) -> int:
    """Integer square root (Newton's method)."""
    if n < 0:
        raise ValueError("isqrt of negative")
    if n == 0:
        return 0
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def compute_hhi(liquidities: list[int], block_lifetimes: list[int]) -> tuple[int, int]:
    """
    Compute expected HHI and indexA in Q128.

    x_k = liq_k * Q128 / total_liq  (Q128 fixed-point)
    x_k_squared = x_k * x_k / Q128  (Q128 result)
    term = x_k_squared / max(1, blockLifetime_k)
    HHI = sum(terms)
    indexA = floor(sqrt(HHI << 128)) capped at INDEX_ONE
    """
    total_liq = sum(liquidities)
    if total_liq == 0:
        return (0, 0)

    hhi = 0
    for liq, bl in zip(liquidities, block_lifetimes):
        # x_k in Q128: liq * Q128 / total_liq (integer division like Solidity)
        x_k = liq * Q128 // total_liq
        # Cap at INDEX_ONE (FEE_SHARE_ONE = 2^128-1) like FeeShareRatioMod
        if x_k > INDEX_ONE:
            x_k = INDEX_ONE
        # x_k^2 in Q128: mulDiv(x_k, x_k, Q128)
        x_k_sq = x_k * x_k // Q128
        # term = x_k^2 / max(1, blockLifetime)
        term = x_k_sq // floor_one(bl)
        hhi += term

    # indexA = sqrt(hhi << 128) capped at INDEX_ONE
    if hhi >= Q128:
        index_a = INDEX_ONE
    else:
        a = isqrt(hhi << 128)
        index_a = min(a, INDEX_ONE)

    return (hhi, index_a)


def main():
    hex_str = sys.argv[1]
    if hex_str.startswith("0x") or hex_str.startswith("0X"):
        hex_str = hex_str[2:]
    raw = bytes.fromhex(hex_str)
    (liquidities, block_lifetimes) = decode(
        ["uint256[]", "uint256[]"], raw
    )
    hhi, index_a = compute_hhi(list(liquidities), list(block_lifetimes))
    result = encode(["uint256", "uint256"], [hhi, index_a])
    sys.stdout.write("0x" + result.hex())


if __name__ == "__main__":
    main()
