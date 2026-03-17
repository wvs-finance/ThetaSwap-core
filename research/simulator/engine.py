"""
Simulation engine — pure state-machine step functions.

Each step function takes (state, action) and returns new state.
No mutation, no side effects. Follows research/backtest/ pattern.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Sequence

from .types import (
    Action, ActionType, PoolState, Position, FCIState,
    RangeEntry, RemovalEntry, SimulationResult, Scenario,
)
from .metrics import (
    Q128, floor_one, compute_x_k, compute_x_k_squared,
    compute_term, compute_theta, fci_state_to_metrics,
)


# ── Pool state transitions ──


def _find_position(pool: PoolState, owner: str, tl: int, tu: int) -> Position | None:
    for p in pool.positions:
        if p.owner == owner and p.tick_lower == tl and p.tick_upper == tu:
            return p
    return None


def _replace_position(positions: tuple[Position, ...], old: Position, new: Position) -> tuple[Position, ...]:
    return tuple(new if p is old else p for p in positions)


def _remove_position(positions: tuple[Position, ...], target: Position) -> tuple[Position, ...]:
    return tuple(p for p in positions if p is not target)


def step_mint(pool: PoolState, owner: str, tl: int, tu: int, liq: int) -> PoolState:
    """Add liquidity to a position. Creates or increases."""
    existing = _find_position(pool, owner, tl, tu)
    if existing is not None:
        new_pos = replace(existing, liquidity=existing.liquidity + liq)
        new_positions = _replace_position(pool.positions, existing, new_pos)
    else:
        new_pos = Position(
            owner=owner, tick_lower=tl, tick_upper=tu,
            liquidity=liq, entry_block=pool.block_number,
            fee_growth_inside_last=pool.fee_growth_global_0,
        )
        new_positions = pool.positions + (new_pos,)

    # Update active liquidity if position range covers current tick
    new_liq = pool.liquidity
    if tl <= pool.tick < tu:
        new_liq += liq

    return replace(pool, positions=new_positions, liquidity=new_liq)


def step_burn(pool: PoolState, owner: str, tl: int, tu: int, liq: int) -> PoolState:
    """Remove liquidity from a position."""
    existing = _find_position(pool, owner, tl, tu)
    assert existing is not None, f"position not found: {owner} [{tl},{tu}]"
    assert existing.liquidity >= liq, f"insufficient liquidity: {existing.liquidity} < {liq}"

    new_liq = pool.liquidity
    if tl <= pool.tick < tu:
        new_liq -= liq

    if existing.liquidity == liq:
        # Full burn — remove position
        new_positions = _remove_position(pool.positions, existing)
    else:
        # Partial burn
        new_pos = replace(existing, liquidity=existing.liquidity - liq)
        new_positions = _replace_position(pool.positions, existing, new_pos)

    return replace(pool, positions=new_positions, liquidity=new_liq)


def step_swap(pool: PoolState, fee_amount: int) -> PoolState:
    """
    Simplified swap: adds fee_amount to feeGrowthGlobal (Q128 per unit of liquidity).

    Real V3/V4 swaps are tick-crossing, but for FCI metric testing we only
    care about fee distribution, not price movement. The tick stays fixed.
    """
    if pool.liquidity == 0:
        return pool
    # fee per unit of liquidity in Q128
    fee_per_liq = fee_amount * Q128 // pool.liquidity
    return replace(
        pool,
        fee_growth_global_0=pool.fee_growth_global_0 + fee_per_liq,
    )


def step_roll(pool: PoolState, new_block: int) -> PoolState:
    """Advance block number."""
    return replace(pool, block_number=new_block)


# ── Range registry tracking ──


def _range_key(tl: int, tu: int) -> str:
    return f"{tl}:{tu}"


def build_range_registry(
    pool: PoolState,
    swap_counts: dict[str, int],
) -> dict[str, RangeEntry]:
    """Build range registry from current pool positions and swap counts."""
    registry: dict[str, RangeEntry] = {}
    for pos in pool.positions:
        rk = _range_key(pos.tick_lower, pos.tick_upper)
        if rk not in registry:
            registry[rk] = RangeEntry(
                tick_lower=pos.tick_lower,
                tick_upper=pos.tick_upper,
                total_liquidity=pos.liquidity,
                swap_count=swap_counts.get(rk, 0),
                block_registered=pos.entry_block,
                position_keys=(pos.owner,),
            )
        else:
            entry = registry[rk]
            registry[rk] = RangeEntry(
                tick_lower=entry.tick_lower,
                tick_upper=entry.tick_upper,
                total_liquidity=entry.total_liquidity + pos.liquidity,
                swap_count=swap_counts.get(rk, 0),
                block_registered=min(entry.block_registered, pos.entry_block),
                position_keys=entry.position_keys + (pos.owner,),
            )
    return registry


# ── FCI accumulation on burn ──


def accumulate_burn(
    fci: FCIState,
    pos_liquidity: int,
    total_range_liquidity: int,
    block_lifetime: int,
    swap_lifetime: int,
) -> tuple[FCIState, RemovalEntry]:
    """
    Accumulate FCI term on full position removal.

    Uses V1 approach: x_k = posLiq / totalRangeLiq (exact for V3).
    Only accumulates if swap_lifetime > 0 (position saw at least 1 swap).
    """
    x_k = compute_x_k(pos_liquidity, total_range_liquidity)
    x_k_sq = compute_x_k_squared(x_k)
    bl = floor_one(block_lifetime)
    term = compute_term(x_k_sq, bl)
    theta_k = compute_theta(bl)

    removal = RemovalEntry(
        agent_id="",  # filled by caller
        liquidity=pos_liquidity,
        block_lifetime=bl,
        x_k=x_k,
        x_k_squared=x_k_sq,
        theta_k=theta_k,
        term=term,
    )

    if swap_lifetime == 0:
        # No swaps during lifetime → no FCI contribution
        new_fci = replace(fci, pos_count=fci.pos_count - 1)
        return new_fci, removal

    new_fci = FCIState(
        accumulated_sum=fci.accumulated_sum + term,
        theta_sum=fci.theta_sum + theta_k,
        pos_count=fci.pos_count - 1,
        removed_pos_count=fci.removed_pos_count + 1,
    )
    return new_fci, removal


# ── Full scenario runner ──


def run_scenario(scenario: Scenario) -> SimulationResult:
    """
    Execute a complete scenario and return metrics.

    Pure function: takes scenario definition, returns simulation result.
    """
    pool = PoolState()
    fci = FCIState()
    removals: list[RemovalEntry] = []

    # Track swap counts per range and position entry blocks
    swap_counts: dict[str, int] = {}
    pos_entry_blocks: dict[str, int] = {}       # agent_id → entry block
    pos_swap_at_entry: dict[str, int] = {}      # agent_id → swap count at entry

    agent_map = {a.id: a for a in scenario.agents}

    for action in scenario.actions:
        if action.action_type == ActionType.ROLL:
            pool = step_roll(pool, action.block)

        elif action.action_type == ActionType.MINT:
            agent = agent_map[action.agent_id]
            pool = step_mint(pool, agent.id, agent.tick_lower, agent.tick_upper, action.liquidity)
            fci = replace(fci, pos_count=fci.pos_count + 1)

            rk = _range_key(agent.tick_lower, agent.tick_upper)
            pos_entry_blocks[agent.id] = pool.block_number
            pos_swap_at_entry[agent.id] = swap_counts.get(rk, 0)

        elif action.action_type == ActionType.SWAP:
            pool = step_swap(pool, action.amount)
            # Increment swap count for all active ranges that cover current tick
            seen_ranges: set[str] = set()
            for pos in pool.positions:
                if pos.tick_lower <= pool.tick < pos.tick_upper:
                    rk = _range_key(pos.tick_lower, pos.tick_upper)
                    if rk not in seen_ranges:
                        swap_counts[rk] = swap_counts.get(rk, 0) + 1
                        seen_ranges.add(rk)

        elif action.action_type == ActionType.BURN:
            agent = agent_map[action.agent_id]
            pos = _find_position(pool, agent.id, agent.tick_lower, agent.tick_upper)
            assert pos is not None

            # Compute range totals BEFORE burn
            total_range_liq = sum(
                p.liquidity for p in pool.positions
                if p.tick_lower == agent.tick_lower and p.tick_upper == agent.tick_upper
            )

            block_lifetime = pool.block_number - pos_entry_blocks[agent.id]
            rk = _range_key(agent.tick_lower, agent.tick_upper)
            swap_lifetime = swap_counts.get(rk, 0) - pos_swap_at_entry.get(agent.id, 0)

            # Only accumulate on full burns (partial-remove guard)
            if action.liquidity == pos.liquidity:
                fci, removal = accumulate_burn(
                    fci, pos.liquidity, total_range_liq,
                    block_lifetime, swap_lifetime,
                )
                removal = RemovalEntry(
                    agent_id=agent.id,
                    liquidity=removal.liquidity,
                    block_lifetime=removal.block_lifetime,
                    x_k=removal.x_k,
                    x_k_squared=removal.x_k_squared,
                    theta_k=removal.theta_k,
                    term=removal.term,
                )
                removals.append(removal)
            else:
                fci = replace(fci, pos_count=fci.pos_count - 1)

            pool = step_burn(pool, agent.id, agent.tick_lower, agent.tick_upper, action.liquidity)

    metrics = fci_state_to_metrics(fci)

    return SimulationResult(
        scenario=replace(scenario, expected=metrics),
        final_pool=pool,
        final_fci=fci,
        metrics=metrics,
        removal_log=tuple(removals),
    )
