"""Simulation configuration — frozen dataclass with all parameters."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SimConfig:
    """All simulation parameters. Immutable after creation."""

    # Time
    T: int = 3000                          # total blocks

    # CFMM initialization
    L_0: float = 100.0                     # initial liquidity
    A_0: float = 0.0                       # initial fee concentration (genesis)

    # Funding rate
    alpha: float = 0.1                     # funding rate sensitivity

    # Fee structure
    fee_base: float = 0.003                # 30 bps base fee
    fee_max: float = 0.01                  # 100 bps max fee

    # Insurance
    premium_fraction: float = 0.1          # 10% of PLP fees -> insurance premium
    L_insurance: float = 50.0              # liquidity in insurance CFMM
    underwriter_collateral: float = 100.0  # underwriter capital

    # Synthetic market
    volume_per_block: float = 10.0         # swap volume per block
