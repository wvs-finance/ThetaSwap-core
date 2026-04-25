"""TDD test suite for Rev-5.3.1 Task 11.N.2d — Y₃ inequality-differential dataset.

Plan:        contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md
             §Task 11.N.2d (line 1092)
Design doc:  contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md
Predecessor: Task 11.N.2c PASS at relaxed N_MIN=75 (commit 7afcd2ad6, Rev-5.3.1)

Public API under test:

* `y3_compute.WC_CPI_FOOD_WEIGHT`, `WC_CPI_ENERGY_HOUSING_WEIGHT`,
  `WC_CPI_TRANSPORT_FUEL_WEIGHT`, `COUNTRY_AGGREGATION_WEIGHT`,
  `PRIMARY_PANEL_START`, `PRIMARY_PANEL_END`, `SENSITIVITY_PANEL_START`,
  `LOCF_TIMEZONE` — eight `Final` constants (Step 0).
* `y3_compute.compute_wc_cpi_weighted(components: pd.DataFrame) -> pd.Series`
  (Step 4).
* `y3_compute.interpolate_monthly_to_weekly_locf(monthly: pd.Series,
  friday_anchor_tz: str) -> pd.Series` (Step 4).
* `y3_compute.compute_per_country_differential(equity_returns: pd.Series,
  wc_cpi_logchange: pd.Series) -> pd.Series` (Step 5).
* `y3_compute.compute_y3_aggregate(per_country_diffs: dict[str, pd.Series])
  -> Y3Panel` (Step 6).
* `y3_data_fetchers.fetch_country_equity()`, `fetch_country_sovereign_yield()`,
  `fetch_country_wc_cpi_components()` — pure free functions (Steps 1-3).
* `econ_query_api.load_onchain_y3_weekly()` — frozen-dataclass loader
  (Step 7).

Strict TDD: tests MUST fail on ImportError until the modules / functions
exist.
"""
from __future__ import annotations

from datetime import date

import pytest


# ─────────────────────────────────────────────────────────────────────────
# Step 0 — Pre-committed constants (failing-first import test)
# ─────────────────────────────────────────────────────────────────────────


def test_step0_wc_cpi_food_weight_byte_exact() -> None:
    """Design doc §9 row 1: WC-CPI food weight = 0.60 (LAC bottom-quintile)."""
    from scripts.y3_compute import WC_CPI_FOOD_WEIGHT
    assert WC_CPI_FOOD_WEIGHT == 0.60


def test_step0_wc_cpi_energy_housing_weight_byte_exact() -> None:
    """Design doc §9 row 2: WC-CPI energy+housing-utilities weight = 0.25."""
    from scripts.y3_compute import WC_CPI_ENERGY_HOUSING_WEIGHT
    assert WC_CPI_ENERGY_HOUSING_WEIGHT == 0.25


def test_step0_wc_cpi_transport_fuel_weight_byte_exact() -> None:
    """Design doc §9 row 3: WC-CPI transport-fuel weight = 0.15."""
    from scripts.y3_compute import WC_CPI_TRANSPORT_FUEL_WEIGHT
    assert WC_CPI_TRANSPORT_FUEL_WEIGHT == 0.15


def test_step0_wc_cpi_weights_sum_to_unity() -> None:
    """Design doc §4: 60/25/15 weights must sum to 1.0 (budget-share invariant)."""
    from scripts.y3_compute import (
        WC_CPI_ENERGY_HOUSING_WEIGHT,
        WC_CPI_FOOD_WEIGHT,
        WC_CPI_TRANSPORT_FUEL_WEIGHT,
    )
    s = (
        WC_CPI_FOOD_WEIGHT
        + WC_CPI_ENERGY_HOUSING_WEIGHT
        + WC_CPI_TRANSPORT_FUEL_WEIGHT
    )
    assert s == 1.0, f"weights must sum to 1.0; got {s}"


def test_step0_country_aggregation_weight_byte_exact() -> None:
    """Design doc §9 row 4: equal-weight 1/4 per anchor country (CO/BR/KE/EU)."""
    from scripts.y3_compute import COUNTRY_AGGREGATION_WEIGHT
    assert COUNTRY_AGGREGATION_WEIGHT == 0.25


def test_step0_primary_panel_start_byte_exact() -> None:
    """Design doc §9 row 5: primary panel start = 2024-09-01."""
    from scripts.y3_compute import PRIMARY_PANEL_START
    assert PRIMARY_PANEL_START == date(2024, 9, 1)


def test_step0_primary_panel_end_byte_exact() -> None:
    """Design doc §9 row 6 + plan line 1123: primary panel end = 2026-04-24."""
    from scripts.y3_compute import PRIMARY_PANEL_END
    assert PRIMARY_PANEL_END == date(2026, 4, 24)


def test_step0_sensitivity_panel_start_byte_exact() -> None:
    """Design doc §9 row 7: sensitivity panel start = 2023-08-01 (1y pre-X_d)."""
    from scripts.y3_compute import SENSITIVITY_PANEL_START
    assert SENSITIVITY_PANEL_START == date(2023, 8, 1)


def test_step0_locf_timezone_byte_exact() -> None:
    """Design doc §9 row 8 + Task 11.M.6 inheritance: LOCF tz = America/Bogota."""
    from scripts.y3_compute import LOCF_TIMEZONE
    assert LOCF_TIMEZONE == "America/Bogota"


# ─────────────────────────────────────────────────────────────────────────
# Step 4 — WC-CPI weighting + LOCF interpolation
# ─────────────────────────────────────────────────────────────────────────


def test_step4_wc_cpi_weighted_60_25_15_combination() -> None:
    """compute_wc_cpi_weighted applies design-doc 60/25/15 weights byte-exact.

    Independent reproduction witness: manual pandas-arithmetic recompute.
    """
    import pandas as pd

    from scripts.y3_compute import compute_wc_cpi_weighted

    # Synthetic 3-month panel; values pinned manually.
    components = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-02-01", "2025-03-01"]),
            "food_cpi": [100.0, 101.0, 102.0],
            "energy_cpi": [200.0, 202.0, 204.0],
            "housing_cpi": [300.0, 303.0, 306.0],
            "transport_cpi": [400.0, 404.0, 408.0],
        }
    )
    out = compute_wc_cpi_weighted(components)

    # Manual second-pass: WC = 0.60*food + 0.25*((energy+housing)/2) + 0.15*transport.
    # Energy+housing combined under "energy+housing-utilities" weight = 0.25;
    # in the design doc the two are jointly weighted, so we average them
    # within the 0.25 bucket. Implementation MUST match this convention.
    eh = (components["energy_cpi"] + components["housing_cpi"]) / 2.0
    expected = (
        0.60 * components["food_cpi"]
        + 0.25 * eh
        + 0.15 * components["transport_cpi"]
    )
    assert len(out) == 3
    for got, want in zip(out.tolist(), expected.tolist(), strict=True):
        assert abs(got - want) < 1e-9


def test_step4_locf_friday_anchor_advance() -> None:
    """LOCF interpolation: weekly Friday holds the latest published monthly value.

    A monthly observation at 2025-01-15 holds for every Friday until the
    next monthly observation lands. Design doc §7.
    """
    import pandas as pd

    from scripts.y3_compute import LOCF_TIMEZONE, interpolate_monthly_to_weekly_locf

    monthly = pd.Series(
        [100.0, 101.0, 102.0],
        index=pd.to_datetime(["2025-01-15", "2025-02-15", "2025-03-15"]),
    )
    out = interpolate_monthly_to_weekly_locf(
        monthly,
        friday_anchor_tz=LOCF_TIMEZONE,
    )
    # Output indexed by Fridays; check a few specific anchors.
    out_dict = {pd.Timestamp(idx).date(): v for idx, v in out.items()}
    # 2025-01-17 is a Friday after 2025-01-15 → 100.0
    # 2025-02-21 is a Friday after 2025-02-15 → 101.0
    # 2025-03-21 is a Friday after 2025-03-15 → 102.0
    assert out_dict.get(date(2025, 1, 17)) == 100.0
    assert out_dict.get(date(2025, 2, 21)) == 101.0
    assert out_dict.get(date(2025, 3, 21)) == 102.0


# ─────────────────────────────────────────────────────────────────────────
# Step 5 — per-country differential
# ─────────────────────────────────────────────────────────────────────────


def test_step5_per_country_differential_sign_convention() -> None:
    """Design doc §1: Δ_country = R_equity + Δlog(WC_CPI).

    Rises with inequality via either rich-side gains or WC cost-of-living
    squeeze. Manual second-pass.
    """
    import pandas as pd

    from scripts.y3_compute import compute_per_country_differential

    fridays = pd.to_datetime(["2025-09-05", "2025-09-12", "2025-09-19"])
    equity = pd.Series([0.01, -0.02, 0.005], index=fridays)
    wc_cpi_logchange = pd.Series([0.002, 0.001, 0.003], index=fridays)
    out = compute_per_country_differential(equity, wc_cpi_logchange)
    expected = (equity + wc_cpi_logchange).tolist()
    assert len(out) == 3
    for got, want in zip(out.tolist(), expected, strict=True):
        assert abs(got - want) < 1e-12


# ─────────────────────────────────────────────────────────────────────────
# Step 6 — Y₃ aggregate
# ─────────────────────────────────────────────────────────────────────────


def test_step6_y3_aggregate_equal_weight() -> None:
    """Design doc §5: Y₃_t = (1/4) × Σ Δ_country_t.

    Independent reproduction: dict-mean recompute.
    """
    import pandas as pd

    from scripts.y3_compute import Y3Panel, compute_y3_aggregate

    fridays = pd.to_datetime(["2025-09-05", "2025-09-12"])
    diffs = {
        "CO": pd.Series([0.01, 0.02], index=fridays),
        "BR": pd.Series([0.005, 0.015], index=fridays),
        "KE": pd.Series([0.002, 0.003], index=fridays),
        "EU": pd.Series([0.001, 0.002], index=fridays),
    }
    panel = compute_y3_aggregate(diffs)
    assert isinstance(panel, Y3Panel)

    # Manual second-pass.
    expected_w0 = (0.01 + 0.005 + 0.002 + 0.001) / 4
    expected_w1 = (0.02 + 0.015 + 0.003 + 0.002) / 4
    assert abs(panel.y3_value[0] - expected_w0) < 1e-12
    assert abs(panel.y3_value[1] - expected_w1) < 1e-12
    assert panel.weeks[0] == date(2025, 9, 5)
    assert panel.weeks[1] == date(2025, 9, 12)
    assert panel.per_country_diffs["CO"][0] == 0.01
    assert panel.per_country_diffs["BR"][1] == 0.015


def test_step6_y3_aggregate_three_country_fallback() -> None:
    """Recovery protocol §10 row 1: Kenya WC-CPI fail → 3-country aggregate."""
    import pandas as pd

    from scripts.y3_compute import compute_y3_aggregate

    fridays = pd.to_datetime(["2025-09-05"])
    diffs = {
        "CO": pd.Series([0.01], index=fridays),
        "BR": pd.Series([0.005], index=fridays),
        "EU": pd.Series([0.001], index=fridays),
    }
    panel = compute_y3_aggregate(diffs)
    expected = (0.01 + 0.005 + 0.001) / 3
    assert abs(panel.y3_value[0] - expected) < 1e-12
    assert "KE" not in panel.per_country_diffs


# ─────────────────────────────────────────────────────────────────────────
# Step 7 — DuckDB schema migration + loader
# ─────────────────────────────────────────────────────────────────────────


def test_step7_onchain_y3_weekly_table_exists_inmemory() -> None:
    """Schema migration creates ``onchain_y3_weekly`` with required columns."""
    import duckdb

    from scripts.econ_schema import init_db

    conn = duckdb.connect(":memory:")
    init_db(conn)

    # Either init_db creates it directly, or we apply the additive migration.
    from scripts.econ_schema import migrate_onchain_y3_weekly  # noqa: F401

    migrate_onchain_y3_weekly(conn)

    cols = {
        row[0]: row[1]
        for row in conn.execute("DESCRIBE onchain_y3_weekly").fetchall()
    }
    # Required columns per design doc §8.
    assert "week_start" in cols
    assert "y3_value" in cols
    assert "copm_diff" in cols
    assert "brl_diff" in cols
    assert "kes_diff" in cols
    assert "eur_diff" in cols
    assert "source_methodology" in cols


def test_step7_load_onchain_y3_weekly_returns_frozen_dataclass() -> None:
    """``load_onchain_y3_weekly`` returns a tuple of ``OnchainY3Weekly`` rows."""
    import dataclasses

    import duckdb

    from scripts.econ_query_api import OnchainY3Weekly, load_onchain_y3_weekly
    from scripts.econ_schema import init_db, migrate_onchain_y3_weekly

    conn = duckdb.connect(":memory:")
    init_db(conn)
    migrate_onchain_y3_weekly(conn)

    # Insert one synthetic row and round-trip it.
    conn.execute(
        "INSERT INTO onchain_y3_weekly "
        "(week_start, y3_value, copm_diff, brl_diff, kes_diff, eur_diff, "
        " source_methodology) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            date(2025, 9, 5),
            0.00425,
            0.01,
            0.005,
            0.002,
            0.001,
            "y3_v1",
        ],
    )

    rows = load_onchain_y3_weekly(conn)
    assert isinstance(rows, tuple)
    assert len(rows) == 1
    r = rows[0]
    assert isinstance(r, OnchainY3Weekly)
    assert dataclasses.is_dataclass(r)
    assert r.week_start == date(2025, 9, 5)
    assert abs(r.y3_value - 0.00425) < 1e-12
    assert r.source_methodology == "y3_v1"


def test_step7_idempotent_upsert_by_week_and_methodology() -> None:
    """Re-ingesting same (week_start, source_methodology) does not duplicate."""
    import duckdb

    from scripts.econ_schema import init_db, migrate_onchain_y3_weekly

    conn = duckdb.connect(":memory:")
    init_db(conn)
    migrate_onchain_y3_weekly(conn)

    # Insert twice — second insert MUST replace, not duplicate.
    for value in (0.001, 0.002):
        conn.execute(
            "INSERT OR REPLACE INTO onchain_y3_weekly "
            "(week_start, y3_value, copm_diff, brl_diff, kes_diff, eur_diff, "
            " source_methodology) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [date(2025, 9, 5), value, 0.0, 0.0, 0.0, 0.0, "y3_v1"],
        )

    n = conn.execute(
        "SELECT COUNT(*) FROM onchain_y3_weekly"
    ).fetchone()[0]
    assert n == 1


def test_step7_decision_hash_preserved() -> None:
    """Rev-4 ``decision_hash`` byte-exact through additive migration.

    Reads the canonical fingerprint JSON and asserts the constant matches.
    Independent: pin the value here; if anyone mutates the fingerprint
    file this test fires alongside the panel-fingerprint test suite.
    """
    import json
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[4]
    fp_path = (
        repo_root
        / "contracts"
        / "notebooks"
        / "fx_vol_cpi_surprise"
        / "Colombia"
        / "estimates"
        / "nb1_panel_fingerprint.json"
    )
    fp = json.loads(fp_path.read_text())
    expected = (
        "6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c"
    )
    assert fp["decision_hash"] == expected


# ─────────────────────────────────────────────────────────────────────────
# Optional smoke probes for fetchers (Steps 1-3) — gated on real data
# (skipped when the canonical structural_econ.duckdb is not populated
# with the fetched panel rows yet; populated by Step 7 ingestion).
# ─────────────────────────────────────────────────────────────────────────


def test_y3_panel_meets_n_min_or_skips() -> None:
    """Primary panel must have ≥ N_MIN=75 weekly observations.

    Skipped if the canonical DB has not yet been populated with Y₃ rows;
    this test asserts the gate criterion (per task body Recovery
    Protocols row 4: N_MIN=75 from Rev-5.3.1 relaxation).
    """
    import duckdb
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[4]
    db_path = repo_root / "contracts" / "data" / "structural_econ.duckdb"
    if not db_path.exists():
        pytest.skip("canonical DuckDB not present")

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
        if "onchain_y3_weekly" not in tables:
            pytest.skip("onchain_y3_weekly not yet populated")
        n = conn.execute(
            "SELECT COUNT(*) FROM onchain_y3_weekly "
            "WHERE source_methodology = 'y3_v1'"
        ).fetchone()[0]
        if n == 0:
            pytest.skip("no y3_v1 rows yet")
        assert n >= 75, (
            f"Y₃ primary panel has {n} weeks; "
            "Rev-5.3.1 gate requires ≥ 75 (Y3_PANEL_INSUFFICIENT)."
        )
    finally:
        conn.close()
