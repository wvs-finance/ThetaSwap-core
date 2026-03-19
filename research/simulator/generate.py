#!/usr/bin/env python3
"""
Generate all FCI scenario fixtures for Solidity differential testing.

Usage:
    uhi8/bin/python -m simulator.generate [--output-dir DIR]

Outputs JSON fixtures to research/data/fixtures/simulator/ (default).
Each fixture contains the action sequence + expected metrics for one scenario.
"""
from __future__ import annotations

import sys
from pathlib import Path

from .engine import run_scenario
from .fixtures import write_all_fixtures, FIXTURE_DIR
from .scenarios import ALL_UNIT_SCENARIOS


def main() -> None:
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else FIXTURE_DIR

    results = []
    for scenario_fn in ALL_UNIT_SCENARIOS:
        scenario = scenario_fn()
        result = run_scenario(scenario)
        results.append(result)

        dp_q128 = result.metrics.delta_plus / (1 << 128)
        print(f"  {scenario.name:45s} deltaPlus={dp_q128:.6f}  removedN={result.metrics.removed_pos_count}")

    paths = write_all_fixtures(results, output_dir)

    print(f"\n{len(paths)} fixtures written to {output_dir}/")
    for p in paths:
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
