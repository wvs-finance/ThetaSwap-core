"""TDD test suite for Task 11.O Rev-2 Phase 5a — Data Engineer panel-prep functions.

Plan:        contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md
             §Task 11.O Rev-2 (14-row resolution matrix)
Spec:        contracts/.scratch/2026-04-25-task110-rev2-spec-A-autonomous.md
             (committed at d9e7ed4c8; 655 lines)
Output:      contracts/.scratch/2026-04-25-task110-rev2-data/
Predecessor: commit c5cc9b66b (Task 11.N.2d-rev primary panel; 76 weeks joint)

Strict TDD (per ``feedback_strict_tdd``): every assertion below MUST fail BEFORE
the panel-prep helpers land in ``scripts/phase5_data_prep.py``. Pre-implementation,
the imports raise ``ModuleNotFoundError``; post-implementation, the panel
constructions yield byte-exact pre-committed joint-nonzero counts (76/65/56/…).

Real data over mocks (per ``feedback_real_data_over_mocks``): every test consumes
the real ``contracts/data/structural_econ.duckdb`` via the session-scoped
``conn`` fixture in ``scripts/tests/conftest.py``; no synthetic panel fixtures.

Pre-committed joint-nonzero counts (verified live at spec-author time against
the canonical DuckDB; documented in spec §5 anti-fishing audit table):

    Row 1 (primary user-vol × y3_v2 × full 6-ctrl)            : 76 weeks
    Row 3 (LOCF-tail-excluded; week_start <= 2025-12-31)      : 65 weeks
    Row 4 (IMF-IFS-only sensitivity y3 panel)                 : 56 weeks
    Row 7 (arb-only diagnostic)                               : 45 weeks
    Row 8 (per-currency COPM diagnostic)                      : 47 weeks

These five counts are the gate of the data-prep stage. If any panel mis-joins
(e.g., weekly_panel's Monday anchor not reconciled to Friday via the
``+ INTERVAL 4 DAY`` translation), the count drifts and the assertion fires.

Friday-anchor invariant (per spec §1.2): every panel row MUST land on a
Friday week_start in the America/Bogota convention. ``weekly_panel`` is
Monday-anchored and is reconciled at construction time; callers consuming
the prepared panels see only Friday-anchored rows.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Final

import duckdb
import pytest


# ── Pinned spec literals (source: 2026-04-25-task110-rev2-spec-A-autonomous.md) ──

REV_5_3_2_V2_PRIMARY_LITERAL: Final[str] = (
    "y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable"
)
REV_5_3_2_V2_IMF_LITERAL: Final[str] = (
    "y3_v2_imf_only_sensitivity_3country_ke_unavailable"
)

PRIMARY_XD_KIND: Final[str] = "carbon_basket_user_volume_usd"
ARB_XD_KIND: Final[str] = "carbon_basket_arb_volume_usd"
COPM_XD_KIND: Final[str] = "carbon_per_currency_copm_volume_usd"

LOCF_TAIL_EXCLUDED_CUTOFF: Final[date] = date(2025, 12, 31)

# Pre-committed joint-nonzero counts (spec §5 + §6).
EXPECTED_N_ROW_1_PRIMARY: Final[int] = 76
EXPECTED_N_ROW_3_LOCF_EXCLUDED: Final[int] = 65
EXPECTED_N_ROW_4_IMF_ONLY: Final[int] = 56
EXPECTED_N_ROW_7_ARB_ONLY: Final[int] = 45
EXPECTED_N_ROW_8_PER_CCY_COPM: Final[int] = 47

# Pre-committed primary-panel date window (spec §5).
PRIMARY_DT_MIN: Final[date] = date(2024, 9, 27)
PRIMARY_DT_MAX: Final[date] = date(2026, 3, 13)

# Six pre-committed control columns — byte-exact match to spec §4.1 equation.
SIX_CONTROLS: Final[tuple[str, ...]] = (
    "vix_avg",
    "oil_return",
    "us_cpi_surprise",
    "banrep_rate_surprise",
    "fed_funds_weekly",
    "intervention_dummy",
)

# Three parsimonious controls (Row 6).
THREE_CONTROLS: Final[tuple[str, ...]] = (
    "vix_avg",
    "oil_return",
    "intervention_dummy",
)


# ─────────────────────────────────────────────────────────────────────────
# Section 1 — DuckDB schema / column-name alignment with spec
# ─────────────────────────────────────────────────────────────────────────


def test_onchain_xd_weekly_schema_exposes_value_usd_and_proxy_kind(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Live DuckDB schema for ``onchain_xd_weekly`` carries spec-cited columns.

    The data_dictionary section of the artifact set claims that X_d is
    materialized in the ``value_usd`` VARCHAR column under a row keyed by
    ``proxy_kind``; if either column is renamed upstream, every panel
    extraction quietly drifts. Catch the drift here before the panels build.
    """
    cols = {
        r[0] for r in conn.execute("DESCRIBE onchain_xd_weekly").fetchall()
    }
    assert {"week_start", "value_usd", "proxy_kind", "is_partial_week"} <= cols, (
        f"onchain_xd_weekly columns {cols!r} have drifted from spec."
    )


def test_onchain_y3_weekly_schema_exposes_y3_and_per_country_diffs(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Live DuckDB schema for ``onchain_y3_weekly`` carries the four diff columns."""
    cols = {
        r[0] for r in conn.execute("DESCRIBE onchain_y3_weekly").fetchall()
    }
    assert (
        {
            "week_start",
            "y3_value",
            "copm_diff",
            "brl_diff",
            "kes_diff",
            "eur_diff",
            "source_methodology",
        }
        <= cols
    ), f"onchain_y3_weekly columns {cols!r} have drifted from spec."


def test_weekly_panel_schema_exposes_six_macro_controls(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """``weekly_panel`` carries 5 of 6 spec-cited continuous controls.

    ``fed_funds_weekly`` lives separately in ``weekly_rate_panel`` (post Task
    11.M.6 schema split); the other 5 controls live in ``weekly_panel``.
    """
    cols = {r[0] for r in conn.execute("DESCRIBE weekly_panel").fetchall()}
    expected_in_weekly_panel: set[str] = {
        "week_start",
        "vix_avg",
        "oil_return",
        "us_cpi_surprise",
        "banrep_rate_surprise",
        "intervention_dummy",
    }
    assert expected_in_weekly_panel <= cols, (
        f"weekly_panel columns {cols!r} have drifted from spec; "
        f"missing: {expected_in_weekly_panel - cols!r}."
    )


def test_weekly_rate_panel_schema_exposes_fed_funds_weekly(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """``weekly_rate_panel`` carries the Fed-funds control on the Friday anchor."""
    cols = {
        r[0] for r in conn.execute("DESCRIBE weekly_rate_panel").fetchall()
    }
    assert {"week_start", "fed_funds_weekly"} <= cols, (
        f"weekly_rate_panel columns {cols!r} have drifted; "
        "fed_funds_weekly is the spec-cited Fed-funds control."
    )


# ─────────────────────────────────────────────────────────────────────────
# Section 2 — Anchor-translation invariant (Monday→Friday for weekly_panel)
# ─────────────────────────────────────────────────────────────────────────


def test_weekly_panel_is_monday_anchored(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Every ``weekly_panel.week_start`` is a Monday (isodow=1)."""
    rows = conn.execute(
        "SELECT DISTINCT EXTRACT('isodow' FROM week_start)::INTEGER "
        "FROM weekly_panel WHERE week_start IS NOT NULL"
    ).fetchall()
    assert rows == [(1,)], (
        f"weekly_panel.week_start drifted from Monday-anchor: {rows!r}"
    )


def test_other_weekly_tables_are_friday_anchored(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """The 3 Friday-anchored tables stay Friday (isodow=5)."""
    for tbl in ("onchain_xd_weekly", "onchain_y3_weekly", "weekly_rate_panel"):
        rows = conn.execute(
            f"SELECT DISTINCT EXTRACT('isodow' FROM week_start)::INTEGER "
            f"FROM {tbl} WHERE week_start IS NOT NULL"
        ).fetchall()
        assert rows == [(5,)], (
            f"{tbl}.week_start drifted from Friday-anchor: {rows!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# Section 3 — Panel-builder invariants (joint nonzero counts)
# ─────────────────────────────────────────────────────────────────────────


def test_build_panel_row_1_primary_returns_76_rows(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Row 1 (primary): user-vol × y3_v2-primary × full 6-ctrl = 76 weeks (spec §5)."""
    from scripts.phase5_data_prep import build_panel

    df = build_panel(
        conn,
        x_d_kind=PRIMARY_XD_KIND,
        y3_methodology=REV_5_3_2_V2_PRIMARY_LITERAL,
        controls=SIX_CONTROLS,
    )
    assert len(df) == EXPECTED_N_ROW_1_PRIMARY, (
        f"Row 1 panel length {len(df)} drifted from spec pre-commitment "
        f"{EXPECTED_N_ROW_1_PRIMARY}; investigate join logic."
    )


def test_build_panel_row_1_date_window_matches_spec(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Row 1 panel spans [2024-09-27, 2026-03-13] (spec §5)."""
    from scripts.phase5_data_prep import build_panel

    df = build_panel(
        conn,
        x_d_kind=PRIMARY_XD_KIND,
        y3_methodology=REV_5_3_2_V2_PRIMARY_LITERAL,
        controls=SIX_CONTROLS,
    )
    assert df["week_start"].min() == PRIMARY_DT_MIN
    assert df["week_start"].max() == PRIMARY_DT_MAX


def test_build_panel_row_3_locf_tail_excluded_returns_65_rows(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Row 3 (LOCF-tail-excluded; cutoff 2025-12-31): joint = 65 weeks (spec §6 + RC probe-5)."""
    from scripts.phase5_data_prep import build_panel

    df = build_panel(
        conn,
        x_d_kind=PRIMARY_XD_KIND,
        y3_methodology=REV_5_3_2_V2_PRIMARY_LITERAL,
        controls=SIX_CONTROLS,
        locf_tail_cutoff=LOCF_TAIL_EXCLUDED_CUTOFF,
    )
    assert len(df) == EXPECTED_N_ROW_3_LOCF_EXCLUDED, (
        f"Row 3 panel length {len(df)} drifted from spec pre-commitment "
        f"{EXPECTED_N_ROW_3_LOCF_EXCLUDED}."
    )


def test_build_panel_row_4_imf_only_returns_56_rows(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Row 4 (IMF-IFS-only sensitivity): joint = 56 weeks (spec §5 / §6)."""
    from scripts.phase5_data_prep import build_panel

    df = build_panel(
        conn,
        x_d_kind=PRIMARY_XD_KIND,
        y3_methodology=REV_5_3_2_V2_IMF_LITERAL,
        controls=SIX_CONTROLS,
    )
    assert len(df) == EXPECTED_N_ROW_4_IMF_ONLY, (
        f"Row 4 panel length {len(df)} drifted from spec pre-commitment "
        f"{EXPECTED_N_ROW_4_IMF_ONLY}."
    )


def test_build_panel_row_7_arb_only_returns_45_rows(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Row 7 (arb-only diagnostic): joint = 45 weeks (spec §6)."""
    from scripts.phase5_data_prep import build_panel

    df = build_panel(
        conn,
        x_d_kind=ARB_XD_KIND,
        y3_methodology=REV_5_3_2_V2_PRIMARY_LITERAL,
        controls=SIX_CONTROLS,
    )
    assert len(df) == EXPECTED_N_ROW_7_ARB_ONLY


def test_build_panel_row_8_per_ccy_copm_returns_47_rows(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Row 8 (per-currency COPM diagnostic): joint = 47 weeks (spec §6)."""
    from scripts.phase5_data_prep import build_panel

    df = build_panel(
        conn,
        x_d_kind=COPM_XD_KIND,
        y3_methodology=REV_5_3_2_V2_PRIMARY_LITERAL,
        controls=SIX_CONTROLS,
    )
    assert len(df) == EXPECTED_N_ROW_8_PER_CCY_COPM


# ─────────────────────────────────────────────────────────────────────────
# Section 4 — Output-column contract for the prepared panel DataFrame
# ─────────────────────────────────────────────────────────────────────────


def test_build_panel_columns_include_y3_xd_and_six_controls(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Returned DataFrame carries all spec-cited columns explicitly named."""
    from scripts.phase5_data_prep import build_panel

    df = build_panel(
        conn,
        x_d_kind=PRIMARY_XD_KIND,
        y3_methodology=REV_5_3_2_V2_PRIMARY_LITERAL,
        controls=SIX_CONTROLS,
    )
    cols = set(df.columns)
    assert {
        "week_start",
        "y3_value",
        "x_d",
        *SIX_CONTROLS,
    } <= cols, f"Returned panel columns {cols!r} missing required fields."


def test_build_panel_returns_friday_anchored_rows_only(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Every row in the returned DataFrame has a Friday week_start (isodow=5)."""
    from scripts.phase5_data_prep import build_panel

    df = build_panel(
        conn,
        x_d_kind=PRIMARY_XD_KIND,
        y3_methodology=REV_5_3_2_V2_PRIMARY_LITERAL,
        controls=SIX_CONTROLS,
    )
    isodow = df["week_start"].apply(lambda d: d.isoweekday()).unique().tolist()
    assert isodow == [5], (
        f"Panel rows are not Friday-anchored; isodow distribution: {isodow!r}"
    )


def test_build_panel_x_d_strictly_positive(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Per spec §3 (joint-nonzero filter), every panel row has x_d > 0."""
    from scripts.phase5_data_prep import build_panel

    df = build_panel(
        conn,
        x_d_kind=PRIMARY_XD_KIND,
        y3_methodology=REV_5_3_2_V2_PRIMARY_LITERAL,
        controls=SIX_CONTROLS,
    )
    assert (df["x_d"] > 0).all(), (
        "Panel contains x_d <= 0 rows; the joint-nonzero filter is broken."
    )


def test_build_panel_no_null_in_six_controls(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """Every panel row has all 6 controls non-null (no silent imputation)."""
    from scripts.phase5_data_prep import build_panel

    df = build_panel(
        conn,
        x_d_kind=PRIMARY_XD_KIND,
        y3_methodology=REV_5_3_2_V2_PRIMARY_LITERAL,
        controls=SIX_CONTROLS,
    )
    for col in SIX_CONTROLS:
        assert df[col].notnull().all(), (
            f"Panel column {col!r} carries NULL — joint-nonzero filter is broken."
        )


# ─────────────────────────────────────────────────────────────────────────
# Section 5 — Validation helper: per-row joint-count audit
# ─────────────────────────────────────────────────────────────────────────


def test_audit_panel_returns_audit_report_dataclass(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """``audit_panel`` returns a frozen-dataclass with n_obs / dt_min / dt_max."""
    from scripts.phase5_data_prep import audit_panel, build_panel

    df = build_panel(
        conn,
        x_d_kind=PRIMARY_XD_KIND,
        y3_methodology=REV_5_3_2_V2_PRIMARY_LITERAL,
        controls=SIX_CONTROLS,
    )
    report = audit_panel(df)

    assert report.n_obs == EXPECTED_N_ROW_1_PRIMARY
    assert report.dt_min == PRIMARY_DT_MIN
    assert report.dt_max == PRIMARY_DT_MAX
    assert report.n_x_d_nonzero == EXPECTED_N_ROW_1_PRIMARY


# ─────────────────────────────────────────────────────────────────────────
# Section 6 — Y₃ admitted-set guard re-test (defense-in-depth)
# ─────────────────────────────────────────────────────────────────────────


def test_build_panel_rejects_unknown_y3_methodology(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    """An unknown ``y3_methodology`` raises ValueError via the upstream guard."""
    from scripts.phase5_data_prep import build_panel

    with pytest.raises(ValueError, match="Unknown Y₃ source_methodology"):
        build_panel(
            conn,
            x_d_kind=PRIMARY_XD_KIND,
            y3_methodology="y3_v999_typoed",
            controls=SIX_CONTROLS,
        )
