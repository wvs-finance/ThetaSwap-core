"""Synthetic CLEAN fixture for ``test_cleaning_purity.py``.

This module demonstrates the required shape of the real ``cleaning.py``:
every public function routes its database read through ``econ_query_api``
and performs only pure pandas post-processing on the returned DataFrame.

Zero raw-query patterns (``.execute(``, ``.sql(``, ``.read_sql(``,
``duckdb.connect(``) — the lint in ``test_cleaning_purity.py`` must
classify this module as pure.
"""
from __future__ import annotations

from datetime import date

import duckdb
import pandas as pd

from scripts.econ_query_api import get_weekly_panel


def load_cleaned(
    conn: duckdb.DuckDBPyConnection,
    start: date,
    end: date,
) -> pd.DataFrame:
    """Load the weekly panel via econ_query_api and drop non-positive rv rows."""
    df = get_weekly_panel(conn, start=start, end=end)
    return df[df["rv"] > 0].reset_index(drop=True)
