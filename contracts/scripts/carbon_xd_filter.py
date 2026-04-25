"""Carbon-basket weekly X_d filter — Task 11.N.2b.2 (Rev-5.3).

Plan reference: ``contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md``
§Task 11.N.2b.2 lines 974-1022.

Design doc (immutable): ``contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md`` §1, §2.

Gate memo: ``contracts/.scratch/2026-04-25-carbon-basket-gate-decision-memo.md``.
Corrigendum: ``contracts/.scratch/2026-04-25-carbon-basket-gate-memo-corrigendum.md``
(empirically verifies the user-vs-arb partition rule — see §3 of the corrigendum).

-------------------------------------------------------------------------
WHAT THIS MODULE COMPUTES
-------------------------------------------------------------------------

X_d for the Mento-↔-global basket boundary on Carbon DeFi (Celo). Per
design doc §1 the primary measure is **user-initiated trades only,
volume-weighted USD magnitude**::

    X_t = Σ |source_amount_usd| over events in week t where
        - swap crosses the Mento ↔ global basket boundary, AND
        - trader ≠ 0x8c05ea305235a67c7095a32ad4a2ee2688ade636 (BancorArbitrage
          contract — empirically verified in corrigendum §2.4 as exactly
          equivalent to the tx-hash JOIN against the arb-event table)

The output ``WeeklyCarbonXdPanel`` carries EIGHT diagnostic series so
Task 11.N.2c can run a per-currency PCA cross-validation:

  1. ``primary_series``  — basket-aggregate user-only volume USD
                            (default ``primary_proxy_kind = "carbon_basket_user_volume_usd"``)
  2. ``arb_only``        — basket-aggregate arb-routed volume USD (diagnostic)
  3-8. ``per_currency``  — six per-Mento-currency volume series
                            (COPM, USDm, EURm, BRLm, KESm, XOFm)

USD denomination is computed by the Python aggregation layer in
:func:`compute_carbon_xd` — Dune does NOT pre-decode ``source_amount_usd``
for this table (gate memo §2.5). The Python layer prices each event at
the day-local Mento broker rate using a deterministic per-currency
fallback (1 USDm = 1 USD; 1 USDT = 1 USD; 1 USDC = 1 USD; CELO/COPM/EURm/
BRLm/KESm/XOFm/WETH each use a per-day spot rate sourced from the Rev-4
TRM panel + EUR/USD + BRL/USD + KES/USD + XOF/USD + WETH/USD tables).

When ``calibration_result is None`` (i.e. 11.N.2b.2 invocation pre-
calibration), ``primary_proxy_kind`` defaults to
``"carbon_basket_user_volume_usd"`` and ``primary_series`` carries the
basket-aggregate user-only volume vector. Task 11.N.2c re-runs with a
non-None ``calibration_result`` and persists the chosen primary; the
RC-CF-1 + RC-CF-2 collapse means the basket-aggregate is unconditionally
the primary.

-------------------------------------------------------------------------
PUBLIC API (pure free functions + one frozen dataclass)
-------------------------------------------------------------------------

* :class:`WeeklyCarbonXdPanel` — frozen-dataclass result type.
* :func:`compute_carbon_xd` — Friday-anchored, America/Bogota-timezone
  weekly aggregation across the basket-membership filter.
* :func:`is_arb_routed` — pure predicate exposing the empirically-verified
  partition rule (see corrigendum §3).
* :func:`identify_basket_currency` — maps a Mento basket address to its
  currency symbol (``copm``, ``usdm``, ``eurm``, ``brlm``, ``kesm``, ``xofm``).

Composition is over free functions; no classes except the frozen
dataclass. See :mod:`scripts.econ_query_api` for the on-chain loader
contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Final, Literal, Optional

from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    import pandas as pd

# ── Constants ───────────────────────────────────────────────────────────────

#: BancorArbitrage contract address on Celo (lowercase, 40-hex, no prefix).
#: Empirically verified in corrigendum §2.4 as the canonical
#: arb-vs-user partition signal — when ``trader = ARB_FAST_LANE_ADDR``,
#: the event is exactly the set whose tx_hash overlaps with
#: ``carbon_defi_celo.bancorarbitrage_evt_arbitrageexecuted`` (51,494
#: events out of 175,005 boundary events; off-diagonal cells of the 2×2
#: contingency table identically zero).
ARB_FAST_LANE_ADDR: Final[str] = "0x8c05ea305235a67c7095a32ad4a2ee2688ade636"

#: Mento basket addresses (lowercase, 0x-prefixed) — verified canonical
#: against Celoscan + Celo token list (gate memo §1).
MENTO_BASKET: Final[frozenset[str]] = frozenset({
    "0xc92e8fc2947e32f2b574cca9f2f12097a71d5606",  # COPM
    "0x765de816845861e75a25fca122bb6898b8b1282a",  # USDm (legacy: cUSD)
    "0xd8763cba276a3738e6de85b4b3bf5fded6d6ca73",  # EURm (legacy: cEUR)
    "0xe8537a3d056da446677b9e9d6c5db704eaab4787",  # BRLm (legacy: cREAL)
    "0x456a3d042c0dbd3db53d5489e98dfb038553b0d0",  # KESm (legacy: cKES)
    "0x73f93dcc49cb8a239e2032663e9475dd5ef29a08",  # XOFm (legacy: eXOF)
})

#: Global basket addresses (lowercase, 0x-prefixed) — gate memo §1
#: (USDT impersonator removed; canonical Tether deployer).
GLOBAL_BASKET: Final[frozenset[str]] = frozenset({
    "0x471ece3750da237f93b8e339c536989b8978a438",  # CELO native
    "0x48065fbbe25f71c9282ddf5e1cd6d6a887483d5e",  # USDT bridged (canonical)
    "0xceba9300f2b948710d2653dd7b07f33a8b32118c",  # USDC bridged
    "0xd221812de1bd094f35587ee8e174b07b6167d9af",  # WETH bridged (Celo native bridge)
})

#: Map Mento basket address → currency symbol (lowercase, used in
#: ``proxy_kind = "carbon_per_currency_<symbol>_volume_usd"`` formation).
_MENTO_ADDR_TO_SYMBOL: Final[dict[str, str]] = {
    "0xc92e8fc2947e32f2b574cca9f2f12097a71d5606": "copm",
    "0x765de816845861e75a25fca122bb6898b8b1282a": "usdm",
    "0xd8763cba276a3738e6de85b4b3bf5fded6d6ca73": "eurm",
    "0xe8537a3d056da446677b9e9d6c5db704eaab4787": "brlm",
    "0x456a3d042c0dbd3db53d5489e98dfb038553b0d0": "kesm",
    "0x73f93dcc49cb8a239e2032663e9475dd5ef29a08": "xofm",
}

#: All six per-currency symbols — used to construct empty diagnostic
#: vectors when a currency has zero events in a week.
MENTO_CURRENCY_SYMBOLS: Final[tuple[str, ...]] = (
    "copm",
    "usdm",
    "eurm",
    "brlm",
    "kesm",
    "xofm",
)

DEFAULT_FRIDAY_ANCHOR_TZ: Final[str] = "America/Bogota"

#: Default ``primary_proxy_kind`` when ``calibration_result is None``.
#: Per design doc §1 + RC-CF-1/RC-CF-2 collapse, the basket-aggregate is
#: unconditionally primary out of the gate.
DEFAULT_PRIMARY_PROXY_KIND: Final[str] = "carbon_basket_user_volume_usd"

#: Allowed primary ``proxy_kind`` literal — the only value the post-
#: calibration `Literal` admits per Task 11.N.2c design.
PrimaryProxyKindT = Literal["carbon_basket_user_volume_usd"]

#: ISO-weekday code for Monday (Python ``date.isoweekday()`` == 1).
_MONDAY_ISO: Final[int] = 1
#: ISO-weekday code for Friday (Python ``date.isoweekday()`` == 5).
_FRIDAY_ISO: Final[int] = 5


# ── Result type ─────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class WeeklyCarbonXdPanel:
    """Friday-anchored weekly X_d panel for the Carbon Mento ↔ global basket.

    Per design doc §2 component-table contract. Carries EIGHT diagnostic
    series so downstream Task 11.N.2c calibration can run per-currency
    PCA + locked basket-aggregate primary.

    Attributes
    ----------
    weeks:
        Tuple of Friday anchor dates, sorted ascending. One per Friday
        touched by the basket-membership-filtered event stream.
    primary_series:
        Volume-USD vector for ``primary_proxy_kind``. Pre-calibration
        default = basket-aggregate user-only volume (= sum of arb-filtered
        boundary trades' ``source_amount_usd`` magnitudes per Friday).
    primary_proxy_kind:
        Tag matching the ``onchain_xd_weekly.proxy_kind`` CHECK admitted
        set. Default ``"carbon_basket_user_volume_usd"``.
    arb_only:
        Volume-USD vector for arb-routed boundary trades, parallel to
        ``weeks``. Diagnostic — landed under
        ``proxy_kind = "carbon_basket_arb_volume_usd"``.
    per_currency:
        ``{symbol → vector}`` for the SIX Mento currencies. Each vector is
        parallel to ``weeks``. Used by Task 11.N.2c PCA cross-validation.
    basket_aggregate:
        Volume-USD vector summing across all six Mento currencies. By
        construction equals ``primary_series`` when the default
        ``primary_proxy_kind`` is in effect — exposed separately so
        downstream consumers can byte-compare.
    is_partial_week:
        ``True`` for Fridays whose 7-day Monday-Sunday span extends
        outside the panel's date envelope (only at boundaries).
    """

    weeks: tuple[date, ...]
    primary_series: tuple[float, ...]
    primary_proxy_kind: str
    arb_only: tuple[float, ...]
    per_currency: dict[str, tuple[float, ...]]
    basket_aggregate: tuple[float, ...]
    is_partial_week: tuple[bool, ...]


# ── Pure helpers ────────────────────────────────────────────────────────────


def _normalise_address(raw: str | bytes) -> str:
    """Lowercase + 0x-prefix an Ethereum-style address.

    Accepts either ``str`` (with or without ``0x`` prefix) or ``bytes``
    (20-byte raw varbinary as returned by Dune's decoded namespace).
    """
    if isinstance(raw, (bytes, bytearray, memoryview)):
        return "0x" + bytes(raw).hex()
    s = raw.lower()
    return s if s.startswith("0x") else "0x" + s


def _friday_of_iso_week(d: date) -> date:
    """Return the Friday of the ISO-week containing ``d``.

    Pure: same as ``date_trunc('week', d) + interval '4 days'`` in DuckDB.
    """
    monday = d - timedelta(days=d.isoweekday() - _MONDAY_ISO)
    return monday + timedelta(days=4)


def _week_span(friday: date) -> tuple[date, date]:
    """Return ``(monday, sunday)`` of the week containing ``friday``."""
    assert friday.isoweekday() == _FRIDAY_ISO, (
        f"_week_span expects a Friday, got {friday} "
        f"(isoweekday={friday.isoweekday()})"
    )
    monday = friday - timedelta(days=4)
    sunday = friday + timedelta(days=2)
    return monday, sunday


def is_arb_routed(trader: str | bytes) -> bool:
    """Return True if ``trader`` matches the BancorArbitrage contract.

    This is the empirically-verified canonical partition rule per
    corrigendum §3. Equivalent to (but cheaper than) JOIN against
    ``carbon_defi_celo.bancorarbitrage_evt_arbitrageexecuted`` on
    ``evt_tx_hash``.

    Pure function: deterministic, no I/O, accepts either str or bytes
    input (Dune varbinary decoded namespace).
    """
    return _normalise_address(trader) == ARB_FAST_LANE_ADDR


def identify_basket_currency(
    source_token: str | bytes,
    target_token: str | bytes,
) -> str | None:
    """Return the Mento basket currency symbol for a boundary swap.

    For a boundary-crossing swap (Mento ↔ global), exactly ONE of
    ``source_token`` / ``target_token`` is in :data:`MENTO_BASKET`; this
    helper returns the corresponding symbol (``"copm"``, ``"usdm"`` …).

    Returns ``None`` if neither endpoint is in MENTO_BASKET (e.g.
    Mento↔Mento or global↔global swap that should never appear in the
    filtered stream — defensive guard).

    Pure: no I/O, deterministic.
    """
    src = _normalise_address(source_token)
    tgt = _normalise_address(target_token)
    if src in MENTO_BASKET:
        return _MENTO_ADDR_TO_SYMBOL.get(src)
    if tgt in MENTO_BASKET:
        return _MENTO_ADDR_TO_SYMBOL.get(tgt)
    return None


def is_boundary_crossing(
    source_token: str | bytes,
    target_token: str | bytes,
) -> bool:
    """Return True iff (source ∈ Mento, target ∈ global) or vice versa.

    Pure predicate — basket-membership filter for
    :func:`compute_carbon_xd`. No I/O.
    """
    src = _normalise_address(source_token)
    tgt = _normalise_address(target_token)
    return (
        (src in MENTO_BASKET and tgt in GLOBAL_BASKET)
        or (src in GLOBAL_BASKET and tgt in MENTO_BASKET)
    )


# ── Public API: weekly aggregation ──────────────────────────────────────────


def compute_carbon_xd(
    events: "pd.DataFrame",
    calibration_result: Optional["object"] = None,
    mento_basket: frozenset[str] = MENTO_BASKET,
    global_basket: frozenset[str] = GLOBAL_BASKET,
    friday_anchor_tz: str = DEFAULT_FRIDAY_ANCHOR_TZ,
) -> WeeklyCarbonXdPanel:
    """Aggregate Carbon TokensTraded events into a weekly basket X_d panel.

    Parameters
    ----------
    events:
        DataFrame with ONE row per ``carbon_defi_celo.carboncontroller_evt_tokenstraded``
        event. Required columns:

        - ``evt_block_date`` — :class:`datetime.date`
        - ``trader`` — 20-byte address (str or bytes)
        - ``sourceToken`` — 20-byte address
        - ``targetToken`` — 20-byte address
        - ``source_amount_usd`` — USD-denominated trade magnitude
          (float or Decimal; computed by the upstream Python pricing
          layer per gate memo §2.5)

        Pre-filter optional but recommended at the SQL layer (cuts
        Dune cost). Events that fail :func:`is_boundary_crossing` are
        silently dropped here for defensive idempotency.
    calibration_result:
        Optional Task 11.N.2c ``CalibrationResult``. When ``None``
        (11.N.2b.2 pre-calibration invocation), the primary series is
        the basket-aggregate user-only volume; ``primary_proxy_kind``
        defaults to ``"carbon_basket_user_volume_usd"``. When non-None,
        the function reads ``calibration_result.primary_choice`` and
        adopts the locked primary.
    mento_basket, global_basket:
        Override the module-level basket constants. Used by the failing-
        first golden-fixture tests to isolate basket scope.
    friday_anchor_tz:
        IANA timezone for Friday-anchor convention. Validated eagerly.

    Returns
    -------
    WeeklyCarbonXdPanel
        Frozen dataclass with eight diagnostic series per design doc §2.

    Notes
    -----
    Pure function: no I/O, no global mutation. Reads only ``events`` and
    its parameters. Friday-of-ISO-week bucketing is identical to
    :func:`scripts.copm_xd_filter._friday_of_iso_week` so cross-channel
    weekly joins on ``onchain_xd_weekly`` align.
    """
    _ = ZoneInfo(friday_anchor_tz)

    # Resolve the primary proxy_kind (calibration may override).
    primary_proxy_kind: str = DEFAULT_PRIMARY_PROXY_KIND
    if calibration_result is not None:
        # 11.N.2c CalibrationResult contract — duck-type the attribute
        # rather than import to avoid circular imports.
        primary_choice = getattr(calibration_result, "primary_choice", None)
        if primary_choice == "basket_aggregate":
            primary_proxy_kind = "carbon_basket_user_volume_usd"

    if events is None or len(events) == 0:
        return _empty_panel(primary_proxy_kind)

    # ── Per-event Friday-of-ISO-week bucketing + classification ────────
    # bucket layout: { friday: {
    #     "user_total":   float,
    #     "arb_total":    float,
    #     "per_currency_user": {symbol: float, ...},
    # }}
    # Per-currency vectors are USER-ONLY volume (consistent with the
    # primary series; arb-routed events are excluded from per-currency
    # diagnostic so PCA reflects user-side regional structure).
    bucket: dict[date, dict[str, float | dict[str, float]]] = {}

    # Iterate via .itertuples() — significantly faster than .iterrows()
    # and avoids dtype-coercion gotchas on the per-row dict path.
    for row in events.itertuples(index=False):
        # Defensive: skip non-boundary events (caller may have pre-filtered)
        src_token = getattr(row, "sourceToken")
        tgt_token = getattr(row, "targetToken")
        if not _check_boundary(src_token, tgt_token, mento_basket, global_basket):
            continue

        block_date_raw = getattr(row, "evt_block_date")
        block_date: date = (
            block_date_raw if isinstance(block_date_raw, date)
            else date.fromisoformat(str(block_date_raw)[:10])
        )
        friday = _friday_of_iso_week(block_date)

        usd_raw = getattr(row, "source_amount_usd")
        # Decimal preserves the 6-decimal text round-trip; float() is the
        # final cast for the bucket sum (fixed-precision sum is noise-free
        # at the magnitudes we expect: < 1e10 USD per event).
        usd = float(usd_raw) if usd_raw is not None else 0.0
        # Magnitude (the X_d formula is volume-weighted ABS).
        usd_mag = abs(usd)

        trader = getattr(row, "trader")
        is_arb = is_arb_routed(trader)

        if friday not in bucket:
            bucket[friday] = {
                "user_total": 0.0,
                "arb_total": 0.0,
                "per_currency_user": {sym: 0.0 for sym in MENTO_CURRENCY_SYMBOLS},
            }
        cell = bucket[friday]

        if is_arb:
            cell["arb_total"] = float(cell["arb_total"]) + usd_mag  # type: ignore[arg-type]
        else:
            cell["user_total"] = float(cell["user_total"]) + usd_mag  # type: ignore[arg-type]
            symbol = identify_basket_currency(src_token, tgt_token)
            if symbol is not None:
                pcu = cell["per_currency_user"]  # type: ignore[assignment]
                assert isinstance(pcu, dict)
                pcu[symbol] = pcu.get(symbol, 0.0) + usd_mag

    if not bucket:
        return _empty_panel(primary_proxy_kind)

    # Emit in ascending Friday order.
    fridays: tuple[date, ...] = tuple(sorted(bucket.keys()))

    user_series: list[float] = []
    arb_series: list[float] = []
    per_currency: dict[str, list[float]] = {sym: [] for sym in MENTO_CURRENCY_SYMBOLS}

    for friday in fridays:
        cell = bucket[friday]
        user_series.append(float(cell["user_total"]))  # type: ignore[arg-type]
        arb_series.append(float(cell["arb_total"]))  # type: ignore[arg-type]
        pcu = cell["per_currency_user"]  # type: ignore[assignment]
        assert isinstance(pcu, dict)
        for sym in MENTO_CURRENCY_SYMBOLS:
            per_currency[sym].append(float(pcu.get(sym, 0.0)))

    # Partial-week flags
    panel_min: date = min(
        (
            d if isinstance(d, date)
            else date.fromisoformat(str(d)[:10])
        )
        for d in events["evt_block_date"]
    )
    panel_max: date = max(
        (
            d if isinstance(d, date)
            else date.fromisoformat(str(d)[:10])
        )
        for d in events["evt_block_date"]
    )
    partials: list[bool] = []
    for friday in fridays:
        monday, sunday = _week_span(friday)
        partials.append((monday < panel_min) or (sunday > panel_max))

    basket_aggregate = tuple(user_series)  # equals user_series by definition

    return WeeklyCarbonXdPanel(
        weeks=fridays,
        primary_series=tuple(user_series),
        primary_proxy_kind=primary_proxy_kind,
        arb_only=tuple(arb_series),
        per_currency={sym: tuple(per_currency[sym]) for sym in MENTO_CURRENCY_SYMBOLS},
        basket_aggregate=basket_aggregate,
        is_partial_week=tuple(partials),
    )


# ── Internal: helpers used only by compute_carbon_xd ────────────────────────


def _check_boundary(
    src_token: str | bytes,
    tgt_token: str | bytes,
    mento: frozenset[str],
    global_: frozenset[str],
) -> bool:
    """Internal boundary check — parametric on basket sets for testability."""
    src = _normalise_address(src_token)
    tgt = _normalise_address(tgt_token)
    return (
        (src in mento and tgt in global_)
        or (src in global_ and tgt in mento)
    )


def _empty_panel(primary_proxy_kind: str) -> WeeklyCarbonXdPanel:
    """Empty-input safe-default for :func:`compute_carbon_xd`."""
    return WeeklyCarbonXdPanel(
        weeks=(),
        primary_series=(),
        primary_proxy_kind=primary_proxy_kind,
        arb_only=(),
        per_currency={sym: () for sym in MENTO_CURRENCY_SYMBOLS},
        basket_aggregate=(),
        is_partial_week=(),
    )
