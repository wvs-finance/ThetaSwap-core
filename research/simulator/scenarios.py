"""
Deterministic scenario definitions for FCI differential testing.

Each scenario maps 1:1 to a Solidity integration test function.
Names follow the test naming convention.
"""
from __future__ import annotations

from .types import Agent, AgentRole, Action, ActionType, Scenario

# ── Constants ──

TL, TU = -60, 60           # Standard tick range
SWAP_FEE = 500_000         # Fee amount per swap (raw tokens, not Q128)


# ── Helper builders ──

def _passive(id: str, liq: int) -> Agent:
    return Agent(id=id, role=AgentRole.PASSIVE, liquidity=liq, tick_lower=TL, tick_upper=TU)

def _jit(id: str, liq: int) -> Agent:
    return Agent(id=id, role=AgentRole.JIT, liquidity=liq, tick_lower=TL, tick_upper=TU)

def _mint(agent_id: str, liq: int, block: int) -> Action:
    return Action(ActionType.MINT, block=block, agent_id=agent_id, liquidity=liq)

def _burn(agent_id: str, liq: int, block: int) -> Action:
    return Action(ActionType.BURN, block=block, agent_id=agent_id, liquidity=liq)

def _swap(block: int, amount: int = SWAP_FEE) -> Action:
    return Action(ActionType.SWAP, block=block, amount=amount)

def _roll(block: int) -> Action:
    return Action(ActionType.ROLL, block=block)


# ═══════════════════════════════════════════════════════════════
#  UNIT SCENARIOS — deterministic, small N
# ═══════════════════════════════════════════════════════════════


def sole_provider_no_swaps() -> Scenario:
    """1 LP, no swaps, burn → all metrics zero."""
    lp = _passive("lp0", 1_000_000_000_000_000_000)  # 1e18
    return Scenario(
        name="sole_provider_no_swaps",
        description="1 LP mints and burns with no swaps. All FCI quantities must be zero.",
        agents=(lp,),
        actions=(
            _mint("lp0", lp.liquidity, block=1),
            _roll(10),
            _burn("lp0", lp.liquidity, block=10),
        ),
    )


def sole_provider_no_swaps_repeated() -> Scenario:
    """1 LP, mint/burn 3 cycles, no swaps → all stay zero."""
    lp = _passive("lp0", 1_000_000_000_000_000_000)
    actions: list[Action] = []
    for cycle in range(3):
        b = cycle * 10 + 1
        actions.append(_mint("lp0", lp.liquidity, block=b))
        actions.append(_roll(b + 5))
        actions.append(_burn("lp0", lp.liquidity, block=b + 5))
    return Scenario(
        name="sole_provider_no_swaps_repeated",
        description="1 LP cycles 3 times with no swaps. All quantities stay zero.",
        agents=(lp,),
        actions=tuple(actions),
    )


def sole_provider_one_swap() -> Scenario:
    """1 LP, 1 swap, burn → deltaPlus=0 (sole provider, x_k=1)."""
    lp = _passive("lp0", 1_000_000_000_000_000_000)
    return Scenario(
        name="sole_provider_one_swap",
        description="Sole provider with 1 swap. x_k=1, deltaPlus must be 0.",
        agents=(lp,),
        actions=(
            _mint("lp0", lp.liquidity, block=1),
            _swap(block=5),
            _roll(10),
            _burn("lp0", lp.liquidity, block=10),
        ),
    )


def two_homogeneous_lps_one_swap() -> Scenario:
    """2 LPs, equal capital, 1 swap, both burn → deltaPlus=0."""
    lp0 = _passive("lp0", 1_000_000_000_000_000_000)
    lp1 = _passive("lp1", 1_000_000_000_000_000_000)
    return Scenario(
        name="two_homogeneous_lps_one_swap",
        description="2 equal LPs, 1 swap, both burn same block. deltaPlus=0 (competitive null).",
        agents=(lp0, lp1),
        actions=(
            _mint("lp0", lp0.liquidity, block=1),
            _mint("lp1", lp1.liquidity, block=1),
            _swap(block=5),
            _roll(10),
            _burn("lp0", lp0.liquidity, block=10),
            _burn("lp1", lp1.liquidity, block=10),
        ),
    )


def two_hetero_capital_one_swap() -> Scenario:
    """
    2 LPs, different capital (1:2), 1 swap, both burn → deltaPlus > 0.

    x_0 = 1/3, x_1 = 2/3. accSum = (1/9 + 4/9) = 5/9.
    atNull = sqrt(2/4) = 0.707. indexA = sqrt(5/9) = 0.745.
    deltaPlus ≈ 0.038. Matches V1 unit test US3-D.
    """
    lp0 = _passive("lp0", 1_000_000_000_000_000_000)   # 1e18
    lp1 = _passive("lp1", 2_000_000_000_000_000_000)   # 2e18
    return Scenario(
        name="two_hetero_capital_one_swap",
        description="2 LPs (1:2 capital), 1 swap. deltaPlus > 0 from capital asymmetry.",
        agents=(lp0, lp1),
        actions=(
            _mint("lp0", lp0.liquidity, block=1),
            _mint("lp1", lp1.liquidity, block=1),
            _swap(block=5),
            _roll(10),
            _burn("lp0", lp0.liquidity, block=10),
            _burn("lp1", lp1.liquidity, block=10),
        ),
    )


def equal_capital_hetero_duration() -> Scenario:
    """
    2 LPs, equal capital, different entry blocks, 2 swaps → deltaPlus=0.

    Equal capital means x_k = 0.5 for both regardless of timing.
    accSum = 2 × (0.25 × theta_k). With different lifetimes, accSum and
    thetaSum scale equally → indexA ≈ atNull → deltaPlus ≈ 0.
    """
    lp0 = _passive("lp0", 1_000_000_000_000_000_000)
    lp1 = _passive("lp1", 1_000_000_000_000_000_000)
    return Scenario(
        name="equal_capital_hetero_duration",
        description="2 equal-capital LPs, different durations, 2 swaps. deltaPlus≈0.",
        agents=(lp0, lp1),
        actions=(
            _mint("lp0", lp0.liquidity, block=1),
            _swap(block=2),
            _mint("lp1", lp1.liquidity, block=3),
            _swap(block=4),
            _roll(5),
            _burn("lp0", lp0.liquidity, block=5),   # lifetime=4
            _roll(9),
            _burn("lp1", lp1.liquidity, block=9),   # lifetime=6
        ),
    )


def jit_crowdout_three_swaps() -> Scenario:
    """
    JIT crowd-out: LP0 passive (small, long-lived), LP1 JIT (large, short-lived).

    Capponi timing model:
    - LP0 enters block 1, exits block 100 (lifetime=99, θ≈0.01)
    - LP1 enters block 49, exits block 51 (lifetime=2, θ=0.5)
    - 3 swaps: block 10 (only LP0), block 50 (both), block 80 (only LP0)

    LP1 has large capital → high x_k during its lifetime → deltaPlus captures JIT.
    """
    lp0 = _passive("lp0", 1_000_000_000_000_000_000)    # 1e18 passive
    lp1 = _jit("lp1", 9_000_000_000_000_000_000)         # 9e18 JIT (9x capital)
    return Scenario(
        name="jit_crowdout_three_swaps",
        description="JIT crowd-out: passive LP0 (1e18, 99 blocks) vs JIT LP1 (9e18, 2 blocks). deltaPlus captures concentration.",
        agents=(lp0, lp1),
        actions=(
            _mint("lp0", lp0.liquidity, block=1),
            _swap(block=10),                              # Only LP0 active
            _roll(49),
            _mint("lp1", lp1.liquidity, block=49),        # JIT enters
            _swap(block=50),                              # Both active (LP1 gets 9/10 of fees)
            _roll(51),
            _burn("lp1", lp1.liquidity, block=51),         # JIT exits (2 block lifetime)
            _swap(block=80),                              # Only LP0 active again
            _roll(100),
            _burn("lp0", lp0.liquidity, block=100),        # Passive exits (99 block lifetime)
        ),
    )


# ═══════════════════════════════════════════════════════════════
#  ALL SCENARIOS — for batch execution
# ═══════════════════════════════════════════════════════════════

ALL_UNIT_SCENARIOS = (
    sole_provider_no_swaps,
    sole_provider_no_swaps_repeated,
    sole_provider_one_swap,
    two_homogeneous_lps_one_swap,
    two_hetero_capital_one_swap,
    equal_capital_hetero_duration,
    jit_crowdout_three_swaps,
)
