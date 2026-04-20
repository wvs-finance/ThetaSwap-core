"""Synthetic VIOLATOR fixture for ``test_cleaning_purity.py``.

This module intentionally violates the cleaning-module purity rule: it
imports from ``econ_query_api`` (the legitimate side) but ALSO calls
``conn.execute(...)`` directly on a DuckDB connection (the raw-query
violation). The lint in ``test_cleaning_purity.py`` must flag it.

Do not import this module from production code.
"""
from __future__ import annotations

import duckdb

from scripts.econ_query_api import get_weekly_panel  # noqa: F401  (intentional)


def load_broken(conn: duckdb.DuckDBPyConnection) -> object:
    """Load data via a raw SQL execute — the forbidden pattern we test for."""
    # VIOLATION: direct raw SQL execution bypasses the econ_query_api contract.
    return conn.execute("SELECT * FROM weekly_panel").fetchdf()
