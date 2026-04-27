"""TDD tests for Rev-5.3 Task 11.N.2b.2 — Carbon-basket weekly X_d filter.

Plan:    contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md
         §Task 11.N.2b.2 lines 974-1022
Memo:    contracts/.scratch/2026-04-25-carbon-basket-gate-decision-memo.md
Corrigendum: contracts/.scratch/2026-04-25-carbon-basket-gate-memo-corrigendum.md
Design doc: contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md (immutable)

Public API under test (per design doc §2)::

    @dataclass(frozen=True, slots=True)
    class WeeklyCarbonXdPanel:
        weeks: tuple[date, ...]
        primary_series: tuple[float, ...]
        primary_proxy_kind: str
        arb_only: tuple[float, ...]
        per_currency: dict[str, tuple[float, ...]]
        basket_aggregate: tuple[float, ...]
        is_partial_week: tuple[bool, ...]

    def compute_carbon_xd(
        events: pd.DataFrame,
        calibration_result: Optional["CalibrationResult"] = None,
        mento_basket: frozenset[str] = MENTO_BASKET,
        global_basket: frozenset[str] = GLOBAL_BASKET,
        friday_anchor_tz: str = "America/Bogota",
    ) -> WeeklyCarbonXdPanel: ...

    def is_arb_routed(trader: str | bytes) -> bool: ...

Six assertion groups (mirrors plan Step 1):

  (a) BASKET-MEMBERSHIP FILTER — Mento↔Mento and global↔global swaps
      excluded (no contribution to user_total or arb_total).
  (b) GOLDEN-FIXTURE USER-ONLY VOLUME — pre-committed synthetic fixture
      with manually-computed expected value reproduces byte-exact.
  (c) ARB-PARTITION — events with trader = ARB_FAST_LANE_ADDR routed to
      arb_only vector, NOT to user primary.
  (d) PER-CURRENCY VECTORS — all six populated; sum equals basket
      aggregate user-only volume.
  (e) INDEPENDENT-REPRODUCTION WITNESS — second compute path (manual
      pandas groupby) reproduces basket_aggregate to 6-decimal precision.
  (f) PROXY-KIND ROUTING — calibration_result=None ⇒ default
      "carbon_basket_user_volume_usd"; calibration_result with
      primary_choice="basket_aggregate" still emits the locked default
      (RC-CF-1/RC-CF-2 collapse — basket_aggregate is the only admitted
      Literal).

Pre-commitment hygiene: the golden synthetic fixture (§"Golden fixture")
is pinned BELOW BEFORE the implementation was authored. Each per-event
row has manually-computed magnitude and bucket assignment recorded as
inline comments; the expected per-week aggregates were computed by hand
from those rows.

Strict TDD: tests MUST fail on ImportError until
``contracts/scripts/carbon_xd_filter.py`` exists with the committed API.
"""
from __future__ import annotations

import dataclasses
from datetime import date
from decimal import Decimal
from typing import Final

import pytest

# pandas is in the venv from Rev-4.
import pandas as pd


# ─────────────────────────────────────────────────────────────────────
# Pre-committed addresses (mirror gate memo §1 + corrigendum §3)
# ─────────────────────────────────────────────────────────────────────

# Mento basket (lowercase, 0x-prefixed)
COPM: Final[str] = "0xc92e8fc2947e32f2b574cca9f2f12097a71d5606"
USDM: Final[str] = "0x765de816845861e75a25fca122bb6898b8b1282a"
EURM: Final[str] = "0xd8763cba276a3738e6de85b4b3bf5fded6d6ca73"
BRLM: Final[str] = "0xe8537a3d056da446677b9e9d6c5db704eaab4787"
KESM: Final[str] = "0x456a3d042c0dbd3db53d5489e98dfb038553b0d0"
XOFM: Final[str] = "0x73f93dcc49cb8a239e2032663e9475dd5ef29a08"

# Global basket (lowercase, 0x-prefixed)
CELO: Final[str] = "0x471ece3750da237f93b8e339c536989b8978a438"
USDT: Final[str] = "0x48065fbbe25f71c9282ddf5e1cd6d6a887483d5e"
USDC: Final[str] = "0xceba9300f2b948710d2653dd7b07f33a8b32118c"
WETH: Final[str] = "0xd221812de1bd094f35587ee8e174b07b6167d9af"

# BancorArbitrage contract (corrigendum §3 — empirically verified
# canonical arb-vs-user partition signal).
ARB: Final[str] = "0x8c05ea305235a67c7095a32ad4a2ee2688ade636"

# A user EOA distinct from ARB.
USER_EOA: Final[str] = "0x0000000000000000000000000000000000000001"

# A non-basket address (used to construct excluded swaps for filter test).
NON_BASKET: Final[str] = "0x4f604735c1cf31399c6e711d5962b2b3e0225ad3"


# ─────────────────────────────────────────────────────────────────────
# Golden fixture — pre-committed by-hand calculation
# ─────────────────────────────────────────────────────────────────────
#
# Two ISO-weeks. Friday anchors:
#   Week 1: 2025-10-31 (Monday 2025-10-27 → Sunday 2025-11-02)
#   Week 2: 2025-11-07 (Monday 2025-11-03 → Sunday 2025-11-09)
#
# Events (manually constructed):
#
# Week 1:
#   E1: COPM→USDT, trader=USER_EOA,  source_amount_usd=100.000000   → user, copm-bucket
#   E2: USDT→COPM, trader=USER_EOA,  source_amount_usd= 50.000000   → user, copm-bucket
#   E3: USDM→CELO, trader=USER_EOA,  source_amount_usd= 25.000000   → user, usdm-bucket
#   E4: COPM→USDT, trader=ARB,       source_amount_usd=400.000000   → arb (NOT in user)
#   E5: COPM→COPM, trader=USER_EOA,  source_amount_usd=999.999999   → EXCLUDED (Mento↔Mento)
#   E6: USDT→USDC, trader=USER_EOA,  source_amount_usd=999.999999   → EXCLUDED (global↔global)
#   E7: NON_BASKET→USDM, trader=USER_EOA, source_amount_usd=42.0   → EXCLUDED (non-basket source)
#   E8: EURM→WETH, trader=USER_EOA,  source_amount_usd= 75.500000   → user, eurm-bucket
#
# Week 2:
#   E9:  BRLM→CELO, trader=USER_EOA, source_amount_usd= 10.000000  → user, brlm-bucket
#   E10: KESM→USDT, trader=USER_EOA, source_amount_usd=  5.000000  → user, kesm-bucket
#   E11: XOFM→USDC, trader=USER_EOA, source_amount_usd=  3.000000  → user, xofm-bucket
#   E12: USDT→XOFM, trader=ARB,      source_amount_usd= 99.000000  → arb (NOT in user)
#
# Expected aggregates (hand-computed):
#   Week 1: user_total = 100 + 50 + 25 + 75.5 = 250.500000
#           arb_total  = 400.000000
#           per_currency.copm = 100 + 50 = 150.000000
#           per_currency.usdm = 25.000000
#           per_currency.eurm = 75.500000
#           per_currency.brlm = per_currency.kesm = per_currency.xofm = 0.0
#   Week 2: user_total = 10 + 5 + 3 = 18.000000
#           arb_total  = 99.000000
#           per_currency.brlm = 10.000000
#           per_currency.kesm =  5.000000
#           per_currency.xofm =  3.000000
#           per_currency.copm = per_currency.usdm = per_currency.eurm = 0.0
#
# Excluded events MUST NOT contribute to ANY bucket (E5 = Mento↔Mento,
# E6 = global↔global, E7 = non-basket-source) — assertion (a).

WEEK1_FRIDAY: Final[date] = date(2025, 10, 31)
WEEK2_FRIDAY: Final[date] = date(2025, 11, 7)

GOLDEN_USER_W1: Final[Decimal] = Decimal("250.500000")
GOLDEN_USER_W2: Final[Decimal] = Decimal("18.000000")
GOLDEN_ARB_W1: Final[Decimal] = Decimal("400.000000")
GOLDEN_ARB_W2: Final[Decimal] = Decimal("99.000000")

GOLDEN_PER_CURRENCY_W1: Final[dict[str, Decimal]] = {
    "copm": Decimal("150.000000"),
    "usdm": Decimal("25.000000"),
    "eurm": Decimal("75.500000"),
    "brlm": Decimal("0.000000"),
    "kesm": Decimal("0.000000"),
    "xofm": Decimal("0.000000"),
}
GOLDEN_PER_CURRENCY_W2: Final[dict[str, Decimal]] = {
    "copm": Decimal("0.000000"),
    "usdm": Decimal("0.000000"),
    "eurm": Decimal("0.000000"),
    "brlm": Decimal("10.000000"),
    "kesm": Decimal("5.000000"),
    "xofm": Decimal("3.000000"),
}


# ── Synthetic events DataFrame builder ──────────────────────────────


def _golden_events() -> pd.DataFrame:
    """Construct the pre-committed golden fixture as a pd.DataFrame.

    Mirrors the schema of ``onchain_carbon_tokenstraded`` after Python
    USD-denomination layer has populated ``source_amount_usd``.
    """
    rows = [
        # Week 1
        {  # E1
            "evt_tx_hash": "0xa1",
            "evt_index": 0,
            "evt_block_date": date(2025, 10, 27),  # Monday W1
            "trader": USER_EOA, "sourceToken": COPM, "targetToken": USDT,
            "source_amount_usd": 100.0,
        },
        {  # E2
            "evt_tx_hash": "0xa2",
            "evt_index": 0,
            "evt_block_date": date(2025, 10, 28),  # Tuesday W1
            "trader": USER_EOA, "sourceToken": USDT, "targetToken": COPM,
            "source_amount_usd": 50.0,
        },
        {  # E3
            "evt_tx_hash": "0xa3",
            "evt_index": 0,
            "evt_block_date": date(2025, 10, 30),  # Thursday W1
            "trader": USER_EOA, "sourceToken": USDM, "targetToken": CELO,
            "source_amount_usd": 25.0,
        },
        {  # E4 — arb-routed
            "evt_tx_hash": "0xa4",
            "evt_index": 0,
            "evt_block_date": date(2025, 10, 31),  # Friday W1
            "trader": ARB, "sourceToken": COPM, "targetToken": USDT,
            "source_amount_usd": 400.0,
        },
        {  # E5 — EXCLUDED (Mento↔Mento)
            "evt_tx_hash": "0xa5",
            "evt_index": 0,
            "evt_block_date": date(2025, 10, 31),
            "trader": USER_EOA, "sourceToken": COPM, "targetToken": COPM,
            "source_amount_usd": 999.999999,
        },
        {  # E6 — EXCLUDED (global↔global)
            "evt_tx_hash": "0xa6",
            "evt_index": 0,
            "evt_block_date": date(2025, 11, 1),  # Saturday W1
            "trader": USER_EOA, "sourceToken": USDT, "targetToken": USDC,
            "source_amount_usd": 999.999999,
        },
        {  # E7 — EXCLUDED (non-basket source)
            "evt_tx_hash": "0xa7",
            "evt_index": 0,
            "evt_block_date": date(2025, 11, 2),  # Sunday W1
            "trader": USER_EOA, "sourceToken": NON_BASKET, "targetToken": USDM,
            "source_amount_usd": 42.0,
        },
        {  # E8
            "evt_tx_hash": "0xa8",
            "evt_index": 0,
            "evt_block_date": date(2025, 11, 2),  # Sunday W1
            "trader": USER_EOA, "sourceToken": EURM, "targetToken": WETH,
            "source_amount_usd": 75.5,
        },
        # Week 2
        {  # E9
            "evt_tx_hash": "0xb1",
            "evt_index": 0,
            "evt_block_date": date(2025, 11, 4),  # Tuesday W2
            "trader": USER_EOA, "sourceToken": BRLM, "targetToken": CELO,
            "source_amount_usd": 10.0,
        },
        {  # E10
            "evt_tx_hash": "0xb2",
            "evt_index": 0,
            "evt_block_date": date(2025, 11, 5),  # Wednesday W2
            "trader": USER_EOA, "sourceToken": KESM, "targetToken": USDT,
            "source_amount_usd": 5.0,
        },
        {  # E11
            "evt_tx_hash": "0xb3",
            "evt_index": 0,
            "evt_block_date": date(2025, 11, 6),  # Thursday W2
            "trader": USER_EOA, "sourceToken": XOFM, "targetToken": USDC,
            "source_amount_usd": 3.0,
        },
        {  # E12 — arb-routed
            "evt_tx_hash": "0xb4",
            "evt_index": 0,
            "evt_block_date": date(2025, 11, 7),  # Friday W2
            "trader": ARB, "sourceToken": USDT, "targetToken": XOFM,
            "source_amount_usd": 99.0,
        },
    ]
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────
# (a) BASKET-MEMBERSHIP FILTER — Mento↔Mento, global↔global excluded
# ─────────────────────────────────────────────────────────────────────


def test_basket_membership_filter_excludes_mento_to_mento_and_global_to_global() -> None:
    """Excluded events (E5, E6, E7) must NOT contribute to any bucket."""
    from scripts.carbon_xd_filter import compute_carbon_xd

    events = _golden_events()
    panel = compute_carbon_xd(events)

    # Sanity: only two weeks present (W1, W2).
    assert panel.weeks == (WEEK1_FRIDAY, WEEK2_FRIDAY), (
        f"Expected weeks (W1, W2), got {panel.weeks}"
    )

    # If E5 (Mento↔Mento, 999.999999) had leaked into user_total, W1
    # user_total would be ≥ 999. The pinned golden is 250.500000 — proves
    # E5 + E6 + E7 are filtered out.
    w1_user_actual = Decimal(str(panel.primary_series[0])).quantize(Decimal("0.000001"))
    assert w1_user_actual == GOLDEN_USER_W1, (
        f"W1 user_total mismatch: got {w1_user_actual}, expected {GOLDEN_USER_W1}. "
        "Excluded events (Mento↔Mento, global↔global, non-basket source) leaked in."
    )


# ─────────────────────────────────────────────────────────────────────
# (b) GOLDEN-FIXTURE USER-ONLY VOLUME (W1 + W2)
# ─────────────────────────────────────────────────────────────────────


def test_golden_user_only_volume_week1() -> None:
    """compute_carbon_xd must reproduce the pre-committed W1 user volume."""
    from scripts.carbon_xd_filter import compute_carbon_xd

    panel = compute_carbon_xd(_golden_events())
    actual = Decimal(str(panel.primary_series[0])).quantize(Decimal("0.000001"))
    assert actual == GOLDEN_USER_W1, (
        f"W1 user volume mismatch: expected {GOLDEN_USER_W1}, got {actual}"
    )


def test_golden_user_only_volume_week2() -> None:
    """compute_carbon_xd must reproduce the pre-committed W2 user volume."""
    from scripts.carbon_xd_filter import compute_carbon_xd

    panel = compute_carbon_xd(_golden_events())
    actual = Decimal(str(panel.primary_series[1])).quantize(Decimal("0.000001"))
    assert actual == GOLDEN_USER_W2, (
        f"W2 user volume mismatch: expected {GOLDEN_USER_W2}, got {actual}"
    )


# ─────────────────────────────────────────────────────────────────────
# (c) ARB-PARTITION — events with trader=ARB go to arb_only, NOT primary
# ─────────────────────────────────────────────────────────────────────


def test_arb_partition_routes_arb_to_arb_only_not_primary() -> None:
    """Events with trader = ARB_FAST_LANE_ADDR populate arb_only series."""
    from scripts.carbon_xd_filter import compute_carbon_xd

    panel = compute_carbon_xd(_golden_events())
    arb_w1 = Decimal(str(panel.arb_only[0])).quantize(Decimal("0.000001"))
    arb_w2 = Decimal(str(panel.arb_only[1])).quantize(Decimal("0.000001"))
    assert arb_w1 == GOLDEN_ARB_W1, f"W1 arb_only mismatch: {arb_w1} vs {GOLDEN_ARB_W1}"
    assert arb_w2 == GOLDEN_ARB_W2, f"W2 arb_only mismatch: {arb_w2} vs {GOLDEN_ARB_W2}"

    # Cross-check: the W1 arb 400 and W2 arb 99 MUST NOT appear in primary_series.
    w1_user = Decimal(str(panel.primary_series[0])).quantize(Decimal("0.000001"))
    w2_user = Decimal(str(panel.primary_series[1])).quantize(Decimal("0.000001"))
    assert w1_user < Decimal("400"), (
        f"W1 user_total {w1_user} ≥ 400 — arb event leaked into primary"
    )
    assert w2_user < Decimal("99"), (
        f"W2 user_total {w2_user} ≥ 99 — arb event leaked into primary"
    )


def test_is_arb_routed_helper_recognises_canonical_address() -> None:
    """is_arb_routed pure predicate must be symmetric across str/bytes inputs."""
    from scripts.carbon_xd_filter import is_arb_routed

    # canonical lowercase string
    assert is_arb_routed(ARB) is True
    # mixed case
    assert is_arb_routed("0x8C05Ea305235A67C7095A32AD4A2EE2688Ade636") is True
    # bytes (Dune varbinary native form)
    raw_bytes = bytes.fromhex(ARB[2:])
    assert is_arb_routed(raw_bytes) is True
    # non-arb EOA
    assert is_arb_routed(USER_EOA) is False


# ─────────────────────────────────────────────────────────────────────
# (d) PER-CURRENCY VECTORS — all six populated; sum == basket_aggregate
# ─────────────────────────────────────────────────────────────────────


def test_per_currency_vectors_match_golden_week1() -> None:
    """All six per-currency W1 entries match pre-committed golden values."""
    from scripts.carbon_xd_filter import MENTO_CURRENCY_SYMBOLS, compute_carbon_xd

    panel = compute_carbon_xd(_golden_events())
    for sym in MENTO_CURRENCY_SYMBOLS:
        actual = Decimal(str(panel.per_currency[sym][0])).quantize(Decimal("0.000001"))
        expected = GOLDEN_PER_CURRENCY_W1[sym]
        assert actual == expected, (
            f"W1 per_currency.{sym} mismatch: got {actual}, expected {expected}"
        )


def test_per_currency_vectors_match_golden_week2() -> None:
    """All six per-currency W2 entries match pre-committed golden values."""
    from scripts.carbon_xd_filter import MENTO_CURRENCY_SYMBOLS, compute_carbon_xd

    panel = compute_carbon_xd(_golden_events())
    for sym in MENTO_CURRENCY_SYMBOLS:
        actual = Decimal(str(panel.per_currency[sym][1])).quantize(Decimal("0.000001"))
        expected = GOLDEN_PER_CURRENCY_W2[sym]
        assert actual == expected, (
            f"W2 per_currency.{sym} mismatch: got {actual}, expected {expected}"
        )


def test_per_currency_sum_equals_basket_aggregate() -> None:
    """Σ per_currency = basket_aggregate (= primary_series for default proxy)."""
    from scripts.carbon_xd_filter import MENTO_CURRENCY_SYMBOLS, compute_carbon_xd

    panel = compute_carbon_xd(_golden_events())
    for week_idx in range(len(panel.weeks)):
        per_curr_sum = sum(
            Decimal(str(panel.per_currency[sym][week_idx]))
            for sym in MENTO_CURRENCY_SYMBOLS
        ).quantize(Decimal("0.000001"))
        basket_agg = Decimal(str(panel.basket_aggregate[week_idx])).quantize(
            Decimal("0.000001")
        )
        assert per_curr_sum == basket_agg, (
            f"Week {week_idx} ({panel.weeks[week_idx]}): "
            f"Σ per_currency = {per_curr_sum} ≠ basket_aggregate = {basket_agg}"
        )


# ─────────────────────────────────────────────────────────────────────
# (e) INDEPENDENT-REPRODUCTION WITNESS
# ─────────────────────────────────────────────────────────────────────


def test_independent_witness_reproduces_basket_aggregate() -> None:
    """A second compute path (manual pandas groupby) reproduces basket_aggregate.

    Guards against silent-test-pass per the Phase-A.0 3-integration-test
    guard catalogued in memory project_fx_vol_econ_reviewer_and_silent_test_pass_lessons.
    The witness deliberately does NOT import from carbon_xd_filter.
    """
    from scripts.carbon_xd_filter import compute_carbon_xd

    events = _golden_events()
    panel = compute_carbon_xd(events)

    # Witness: independent computation.
    df = events.copy()
    # Boundary filter (Mento↔global)
    mento = {COPM, USDM, EURM, BRLM, KESM, XOFM}
    glb = {CELO, USDT, USDC, WETH}
    is_boundary = (
        (df["sourceToken"].isin(mento) & df["targetToken"].isin(glb))
        | (df["sourceToken"].isin(glb) & df["targetToken"].isin(mento))
    )
    df = df[is_boundary].copy()
    # User-only filter
    df = df[df["trader"] != ARB].copy()
    # Friday-of-ISO-week
    df["friday"] = df["evt_block_date"].apply(
        lambda d: d + pd.Timedelta(days=(4 - d.isoweekday() + 1) % 7)
        if d.isoweekday() <= 5
        else d - pd.Timedelta(days=d.isoweekday() - 5)
    )
    # Manual ISO-week Friday computation: Monday + 4 days
    df["friday"] = df["evt_block_date"].apply(
        lambda d: pd.Timestamp(d) - pd.Timedelta(days=d.isoweekday() - 1)
        + pd.Timedelta(days=4)
    )
    grouped = df.groupby("friday")["source_amount_usd"].sum().sort_index()

    for friday, expected_witness in zip(panel.weeks, panel.basket_aggregate):
        witness_value = grouped.loc[pd.Timestamp(friday)]
        actual_module = Decimal(str(expected_witness)).quantize(Decimal("0.000001"))
        actual_witness = Decimal(str(witness_value)).quantize(Decimal("0.000001"))
        assert actual_module == actual_witness, (
            f"Witness disagreement at {friday}: "
            f"module={actual_module} vs witness={actual_witness}"
        )


# ─────────────────────────────────────────────────────────────────────
# (f) PROXY-KIND ROUTING
# ─────────────────────────────────────────────────────────────────────


def test_proxy_kind_default_when_no_calibration_result() -> None:
    """calibration_result=None ⇒ primary_proxy_kind = default basket-aggregate tag."""
    from scripts.carbon_xd_filter import (
        DEFAULT_PRIMARY_PROXY_KIND,
        compute_carbon_xd,
    )

    panel = compute_carbon_xd(_golden_events(), calibration_result=None)
    assert panel.primary_proxy_kind == DEFAULT_PRIMARY_PROXY_KIND
    assert panel.primary_proxy_kind == "carbon_basket_user_volume_usd"


def test_proxy_kind_with_basket_aggregate_calibration() -> None:
    """calibration_result.primary_choice='basket_aggregate' yields locked default."""
    from scripts.carbon_xd_filter import compute_carbon_xd

    @dataclasses.dataclass(frozen=True)
    class FakeCalibrationResult:
        primary_choice: str

    cal = FakeCalibrationResult(primary_choice="basket_aggregate")
    panel = compute_carbon_xd(_golden_events(), calibration_result=cal)
    # Per RC-CF-1/RC-CF-2 collapse the only admitted Literal is
    # basket_aggregate ⇒ "carbon_basket_user_volume_usd".
    assert panel.primary_proxy_kind == "carbon_basket_user_volume_usd"


# ─────────────────────────────────────────────────────────────────────
# Frozen-dataclass + purity contract
# ─────────────────────────────────────────────────────────────────────


def test_weekly_carbon_xd_panel_is_frozen_dataclass() -> None:
    """WeeklyCarbonXdPanel is a frozen dataclass with the committed field set."""
    from scripts.carbon_xd_filter import WeeklyCarbonXdPanel

    assert dataclasses.is_dataclass(WeeklyCarbonXdPanel)
    field_names = {f.name for f in dataclasses.fields(WeeklyCarbonXdPanel)}
    expected = {
        "weeks",
        "primary_series",
        "primary_proxy_kind",
        "arb_only",
        "per_currency",
        "basket_aggregate",
        "is_partial_week",
    }
    assert field_names == expected, (
        f"Expected fields {expected}, got {field_names}"
    )


def test_compute_carbon_xd_purity_idempotent() -> None:
    """Calling compute_carbon_xd twice with the same input yields identical output."""
    from scripts.carbon_xd_filter import compute_carbon_xd

    events = _golden_events()
    p1 = compute_carbon_xd(events)
    p2 = compute_carbon_xd(events)
    assert p1.weeks == p2.weeks
    assert p1.primary_series == p2.primary_series
    assert p1.arb_only == p2.arb_only
    assert p1.basket_aggregate == p2.basket_aggregate
    assert p1.per_currency == p2.per_currency
    assert p1.primary_proxy_kind == p2.primary_proxy_kind
