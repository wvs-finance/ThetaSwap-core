"""
Deterministic AMM fee concentration simulator.

Generates scenarios (LP actions sequences) and expected FCI metrics
for differential testing against Solidity FCI V2 contracts.

Architecture: frozen dataclasses + pure functions (no mutable state).
Convention: @functional-python skill.
"""
