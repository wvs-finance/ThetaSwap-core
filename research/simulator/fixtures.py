"""
Fixture output — converts SimulationResult to JSON for Solidity consumption.

Output format is protocol-agnostic: the same fixture drives both
V4 native (Anvil fork) and V3 reactive (live broadcast) tests.

Solidity reads fixtures via vm.readFile() + vm.parseJson*().
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .types import (
    SimulationResult, Scenario, Action, ActionType,
    FCIMetrics, EpochMetrics, RangeSnapshotExpected, PositionExpected,
    RemovalEntry, Agent, AgentRole,
)

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "simulator"


def _action_to_dict(action: Action) -> dict[str, Any]:
    """Serialize an action for Solidity consumption."""
    d: dict[str, Any] = {
        "type": action.action_type.name,
        "block": action.block,
    }
    if action.agent_id is not None:
        d["agentId"] = action.agent_id
    if action.action_type == ActionType.MINT or action.action_type == ActionType.BURN:
        d["liquidity"] = str(action.liquidity)
    if action.action_type == ActionType.SWAP:
        d["amount"] = str(action.amount)
        d["zeroForOne"] = action.zero_for_one
    return d


def _agent_to_dict(agent: Agent) -> dict[str, Any]:
    return {
        "id": agent.id,
        "role": agent.role.name,
        "liquidity": str(agent.liquidity),
        "tickLower": agent.tick_lower,
        "tickUpper": agent.tick_upper,
    }


def _q128_to_readable(val: int) -> str:
    """Convert Q128 fixed-point to human-readable decimal string."""
    Q128 = 1 << 128
    return f"{val / Q128:.6f}"


def _metrics_to_dict(m: FCIMetrics) -> dict[str, Any]:
    """Serialize metrics as hex strings (Q128 values) for Solidity parsing."""
    d: dict[str, Any] = {
        "accumulatedSum": hex(m.accumulated_sum),
        "indexA": hex(m.index_a),
        "thetaSum": hex(m.theta_sum),
        "removedPosCount": m.removed_pos_count,
        "atNull": hex(m.at_null),
        "deltaPlus": hex(m.delta_plus),
        "readable": {
            "deltaPlus": _q128_to_readable(m.delta_plus),
            "indexA": _q128_to_readable(m.index_a),
            "atNull": _q128_to_readable(m.at_null),
            "thetaSum": _q128_to_readable(m.theta_sum),
        },
    }
    if m.epochs:
        d["epochs"] = [
            {
                "epochId": e.epoch_id,
                "accumulatedSum": hex(e.accumulated_sum),
                "indexA": hex(e.index_a),
                "thetaSum": hex(e.theta_sum),
                "removedPosCount": e.removed_pos_count,
                "atNull": hex(e.at_null),
                "deltaPlus": hex(e.delta_plus),
            }
            for e in m.epochs
        ]
    if m.ranges:
        d["ranges"] = [
            {
                "tickLower": r.tick_lower,
                "tickUpper": r.tick_upper,
                "totalLiquidity": str(r.total_liquidity),
                "swapCount": r.swap_count,
                "positionCount": r.position_count,
                "positionKeys": list(r.position_keys),
            }
            for r in m.ranges
        ]
    if m.positions:
        d["positions"] = [
            {
                "posKey": p.pos_key,
                "feeGrowthBaseline": hex(p.fee_growth_baseline),
                "addBlock": p.add_block,
                "swapLifetime": p.swap_lifetime,
            }
            for p in m.positions
        ]
    return d


def _removal_to_dict(r: RemovalEntry) -> dict[str, Any]:
    return {
        "agentId": r.agent_id,
        "liquidity": str(r.liquidity),
        "blockLifetime": r.block_lifetime,
        "xK": hex(r.x_k),
        "xKSquared": hex(r.x_k_squared),
        "thetaK": hex(r.theta_k),
        "term": hex(r.term),
    }


def result_to_fixture(result: SimulationResult) -> dict[str, Any]:
    """
    Convert a SimulationResult to a JSON-serializable fixture dict.

    Structure:
    {
        "scenario": { name, description, agents[], actions[] },
        "expected": { accumulatedSum, indexA, ..., ranges[], positions[] },
        "removals": [ { agentId, xK, term, ... } ]
    }
    """
    scenario = result.scenario
    return {
        "scenario": {
            "name": scenario.name,
            "description": scenario.description,
            "agents": [_agent_to_dict(a) for a in scenario.agents],
            "actions": [_action_to_dict(a) for a in scenario.actions],
        },
        "expected": _metrics_to_dict(result.metrics),
        "removals": [_removal_to_dict(r) for r in result.removal_log],
    }


def write_fixture(result: SimulationResult, output_dir: Path | None = None) -> Path:
    """Write fixture JSON to disk. Returns path."""
    out_dir = output_dir or FIXTURE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{result.scenario.name}.json"
    data = result_to_fixture(result)
    path.write_text(json.dumps(data, indent=2) + "\n")
    return path


def write_all_fixtures(
    results: list[SimulationResult],
    output_dir: Path | None = None,
) -> list[Path]:
    """Write all scenario fixtures to disk."""
    return [write_fixture(r, output_dir) for r in results]
