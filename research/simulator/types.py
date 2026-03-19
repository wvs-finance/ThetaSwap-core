"""
Domain types for the FCI scenario simulator.

All types are frozen dataclasses. State transitions return new instances.
Convention: @functional-python skill.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Sequence


# ── Agent types ──


class AgentRole(Enum):
    """LP classification per Capponi model."""
    PASSIVE = auto()   # Long-lived, enters early, exits late
    JIT = auto()       # Short-lived, enters just before swap, exits right after


@dataclass(frozen=True)
class Agent:
    """An LP agent in the simulation."""
    id: str
    role: AgentRole
    liquidity: int          # Position size (raw, not Q128)
    tick_lower: int
    tick_upper: int


# ── Actions ──


class ActionType(Enum):
    MINT = auto()
    SWAP = auto()
    BURN = auto()
    ROLL = auto()    # Advance block number (vm.roll equivalent)


@dataclass(frozen=True)
class Action:
    """A single action in the scenario timeline."""
    action_type: ActionType
    block: int                          # Block number when this action occurs
    agent_id: str | None = None         # None for SWAP and ROLL
    liquidity: int = 0                  # For MINT/BURN
    zero_for_one: bool = True           # For SWAP
    amount: int = 0                     # For SWAP (amountSpecified)


# ── Pool state ──


@dataclass(frozen=True)
class Position:
    """A position in the simulated pool."""
    owner: str
    tick_lower: int
    tick_upper: int
    liquidity: int
    entry_block: int
    fee_growth_inside_last: int = 0     # Q128


@dataclass(frozen=True)
class PoolState:
    """Simulated V3/V4 pool state (tick-level)."""
    tick: int = 0
    liquidity: int = 0                          # Active liquidity at current tick
    fee_growth_global_0: int = 0                # Q128
    block_number: int = 1
    positions: tuple[Position, ...] = ()        # Immutable tuple of positions


# ── FCI state (mirrors FeeConcentrationState in Solidity) ──


@dataclass(frozen=True)
class FCIState:
    """Fee Concentration Index accumulator state."""
    accumulated_sum: int = 0            # Q128: Σ(θ_k · x_k²)
    theta_sum: int = 0                  # Q128: Σ(1/ℓ_k)
    pos_count: int = 0                  # Active position count
    removed_pos_count: int = 0          # Positions that contributed terms


# ── Range registry entry ──


@dataclass(frozen=True)
class RangeEntry:
    """Per-range tracking in the tick range registry."""
    tick_lower: int
    tick_upper: int
    total_liquidity: int = 0
    swap_count: int = 0
    block_registered: int = 0
    position_keys: tuple[str, ...] = ()


# ── Metrics output ──


@dataclass(frozen=True)
class EpochMetrics:
    """Epoch-scoped FCI metrics — maps to getDeltaPlusEpoch()."""
    epoch_id: int
    accumulated_sum: int    # Q128
    index_a: int            # Q128
    theta_sum: int          # Q128
    removed_pos_count: int
    at_null: int            # Q128
    delta_plus: int         # Q128


@dataclass(frozen=True)
class RangeSnapshotExpected:
    """Expected per-range state — maps to getRegistryRangeSnapshot()."""
    tick_lower: int
    tick_upper: int
    total_liquidity: int
    swap_count: int
    position_count: int
    position_keys: tuple[str, ...]


@dataclass(frozen=True)
class PositionExpected:
    """Expected per-position state — maps to facet registry reads."""
    pos_key: str                   # agent_id (maps to posKey in Solidity)
    fee_growth_baseline: int       # getRegistryPositionBaseline()
    add_block: int                 # getRegistryPositionAddBlock()
    swap_lifetime: int             # getRegistryPositionSwapLifetime()


@dataclass(frozen=True)
class FCIMetrics:
    """
    Expected FCI metric values — maps 1:1 to FCI V2 interface.

    Top-level (FeeConcentrationIndexV2):
      getIndex()        → (index_a, theta_sum, removed_pos_count)
      getDeltaPlus()    → delta_plus
      getAtNull()       → at_null
      getThetaSum()     → theta_sum
      getDeltaPlusEpoch → epochs[i].delta_plus

    Per-range (IFCIProtocolFacet):
      getRegistryAllSnapshots() → ranges
      getRegistryActiveRanges() → active range keys

    Per-position (IFCIProtocolFacet):
      getRegistryPositionBaseline()    → fee growth at registration
      getRegistryPositionAddBlock()    → block number at registration
      getRegistryPositionSwapLifetime() → swaps during lifetime
    """
    # ── Top-level (cumulative) ──
    accumulated_sum: int    # Q128 — internal
    index_a: int            # Q128
    theta_sum: int          # Q128
    removed_pos_count: int
    at_null: int            # Q128
    delta_plus: int         # Q128

    # ── Epoch ──
    epochs: tuple[EpochMetrics, ...] = ()

    # ── Per-range snapshots (state at query time) ──
    ranges: tuple[RangeSnapshotExpected, ...] = ()

    # ── Per-position (active positions at query time) ──
    positions: tuple[PositionExpected, ...] = ()


# ── Scenario definition ──


@dataclass(frozen=True)
class Scenario:
    """
    A complete deterministic scenario for differential testing.

    The name encodes the test requirements (e.g., '2LP_hetero_capital_1swap').
    Actions are an ordered sequence of MINT/SWAP/BURN/ROLL events.
    Expected metrics are computed by the Python simulator.
    """
    name: str
    description: str
    agents: tuple[Agent, ...]
    actions: tuple[Action, ...]
    expected: FCIMetrics | None = None   # Filled after simulation


# ── Simulation result ──


@dataclass(frozen=True)
class SimulationResult:
    """Full simulation output."""
    scenario: Scenario
    final_pool: PoolState
    final_fci: FCIState
    metrics: FCIMetrics
    # Per-position removal data for debugging
    removal_log: tuple[RemovalEntry, ...] = ()


@dataclass(frozen=True)
class RemovalEntry:
    """Log entry for a position removal (burn)."""
    agent_id: str
    liquidity: int
    block_lifetime: int
    x_k: int                # Q128: posLiq / totalRangeLiq
    x_k_squared: int        # Q128
    theta_k: int             # Q128: 1 / blockLifetime
    term: int                # Q128: θ_k · x_k²
