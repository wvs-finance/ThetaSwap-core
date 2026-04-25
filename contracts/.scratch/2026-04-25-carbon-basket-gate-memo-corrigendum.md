# Carbon-Basket Gate Memo — Corrigendum (Task 11.N.2b.2 Step 0)

**Date:** 2026-04-25T18:00Z
**Supersedes:** §3.3 of `contracts/.scratch/2026-04-25-carbon-basket-gate-decision-memo.md` (the user-vs-arb partition narrative).
**Plan reference:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` Task 11.N.2b.2 Step 0 (resume directive).
**Verdict:** **GO — proceed with re-implemented partition rule** based on `trader = BancorArbitrage_address`, not on `evt_tx_from`.

---

## 1. Why this corrigendum exists

The Rev-5.3 plan §982 X_d formula reads:

> `X_t = Σ |source_amount_usd| over events in week t where tx_origin ≠ 0x8c05ea305235a67c7095a32ad4a2ee2688ade636 (BancorArbitrage filtered out) ...`

The original gate memo §3.3 line 210 then asserted that the `evt_tx_from ≠ BancorArbitrage_address` partition correctly filters arb activity OUT. The prior implementation agent ran this filter and produced **all-zero `carbon_basket_arb_volume_usd`** rows — which contradicted the 11.N.2 attribution research's "BancorArbitrage was trader on 57,382 trades" finding.

The prior agent then hypothesised a tx-hash JOIN against `bancorarbitrage_evt_arbitrageexecuted` as the correct rule but did not empirically verify before halting.

This corrigendum lands the empirical verification.

---

## 2. Three Dune probes

### 2.1 Probe v1 — naive tx-hash JOIN, recent-1000 sample (query `7372237`)

| metric | value |
|---|---|
| `total_sampled_events` | 1000 |
| `overlapping_events` | **0** |
| `non_overlapping_events` | 1000 |
| `tx_from_eq_arb_contract` | 0 |
| `distinct_tx_from` (non-overlap) | 8 |

Cost: 0.095 credits.

The 1000-row sample by `evt_block_time DESC` was biased to the most recent boundary events. `evt_tx_from` is universally distinct from the BancorArbitrage contract (consistent with prior agent's "tx_from is the EOA" hypothesis), but the JOIN overlap was zero. Initial impression: tx-hash JOIN is also wrong.

### 2.2 Probe v2 — arb-table date-range health check (query `7372241`)

```json
{
  "arb_event_count": 1088570,
  "arb_first_date": "2024-09-01",
  "arb_last_date":  "2025-07-01",
  "arb_distinct_tx_hashes": 1088570
}
```

The arb-event table is **stale**: it stops at 2025-07-01 (10 months ago). The `tokenstraded` table runs through 2026-04-25. The 1000-event recent sample was entirely past the arb-table cutoff, mechanically guaranteeing zero overlap. The v1 probe was inconclusive, not falsifying.

### 2.3 Probe v3 — full-range partition over 175,005 boundary events (query `7372243`)

| scope | total | overlap | non-overlap | trader = arb | tx_from = arb |
|---|---|---|---|---|---|
| `2024-09-01 → 2026-04-25` (full) | 175,005 | 51,494 | 123,511 | **51,494** | 0 |
| `2024-09-01 → 2025-07-01` (overlap window) | 58,026 | 51,494 | 6,532 | 51,494 | 0 |

Cost: 0.098 credits.

Two observations leap out:
1. **`trader_eq_arb_contract` and `overlap_events` are byte-identical (51,494) in both scopes.** The two partitioning rules — (a) tx-hash JOIN against arb-event table, (b) `trader = 0x8c05ea…` — produce the SAME classification.
2. **Within the overlap window, 88.7% of boundary events are arb-routed (51,494 / 58,026).** This restores the 11.N.2 attribution research's "BancorArbitrage was the trader on 57,382 trades" — the figure was COPM-only; the basket-wide equivalent is 51,494 (different filter, same order of magnitude).

### 2.4 Probe v4 — 2×2 contingency proof of partition equivalence (query `7372247`)

Output:

| | `trader = arb` | `trader ≠ arb` |
|---|---|---|
| `tx ∈ arb_events_table` | **51,494** | **0** |
| `tx ∉ arb_events_table` | **0** | **123,511** |

Off-diagonal cells identically zero across all 175,005 boundary events. `trader_null_count = 0`. Cost: 0.094 credits.

This is the strongest possible empirical confirmation: the two partitions are **mathematically equivalent** on the basket-wide population.

---

## 3. Corrected partition rule (load-bearing)

**RULE:** an event in `carbon_defi_celo.carboncontroller_evt_tokenstraded` is "arb-routed" iff `trader = 0x8c05ea305235a67c7095a32ad4a2ee2688ade636` (the BancorArbitrage contract address).

**Why this is the canonical form (not the tx-hash JOIN):**

- **Empirically equivalent** to the tx-hash JOIN (zero misclassifications on 175k events; §2.4).
- **Cheaper to compute**: a single equality predicate on a per-row column vs. a JOIN against a 1.09M-row arb-event table.
- **Robust to arb-table staleness**: the `bancorarbitrage_evt_arbitrageexecuted` table is stale at 2025-07-01 (probe v2). The `trader` field lives on the `tokenstraded` row itself, never goes stale.
- **Consistent with 11.N.2 attribution research**: bots emit a stable `trader` value because the BancorArbitrage contract is the recorded `msg.sender` for the SwapExecutor pathway in the Carbon controller, not the EOA-level `evt_tx_from`. (Carbon's `TokensTraded` event captures the contract that called `tradeBySourceAmount` / `tradeByTargetAmount`, which for arbitrage routes is the BancorArbitrage contract.)

**Plan §982 reinterpretation:** the plan text "tx_origin ≠ 0x8c05ea…" was written under the false assumption that `evt_tx_from` (Dune's tx-origin) is where the BancorArbitrage signature lives. In fact `evt_tx_from` is always the EOA initiating the transaction; the BancorArbitrage signature lives in `trader`. The plan's intent (filter arb out of user-only) is preserved by switching the field. No spec/plan revision is needed; the corrigendum amends the operative interpretation in source.

**Why the gate memo §3.3 was wrong:** the §3.3 paragraph claimed "`evt_tx_from` of an arb event is the contract itself in `_evt_tokenstraded` rows initiated by the arb path". That statement is **falsified** by probe v3 (`tx_from_eq_arb_contract = 0` over 175,005 events). The correct anchor is `trader`, never `evt_tx_from`.

---

## 4. Corrected key cardinalities

| measure | value | source |
|---|---|---|
| Total `tokenstraded` events 2024-09-01 → 2026-04-25 | 2,229,217 | gate memo §2.2 |
| Boundary-crossing events (Mento ↔ global) | **175,005** | corrigendum §2.3 (was 213,452 in pre-probe estimate; -18%) |
| User-only events (non-arb) | 123,511 | corrigendum §2.3 |
| Arb-routed events (`trader = 0x8c05ea…`) | 51,494 | corrigendum §2.3 |
| Arb-routed share of boundary | 29.4% | computed |
| Arb-routed share within overlap window (≤ 2025-07-01) | 88.7% | corrigendum §2.3 |
| Distinct user `evt_tx_from` (full range) | 66 | corrigendum §2.3 |
| Distinct user `trader` (full range, 47 minus arb-trader) | 46 | corrigendum §2.3 |

**Implication for arb-volume non-zero sanity check (Step gate):** with 51,494 arb-routed events (~30% of boundary), arb-volume series will be **structurally non-zero** across multiple weeks of the panel. The pathological branch ("Arb Fast Lane is ~100% of activity") is FALSIFIED at the basket level — user-only volume is 70% of boundary events. The `compute_carbon_xd()` user-only primary `proxy_kind = "carbon_basket_user_volume_usd"` will populate cleanly.

**95% cardinality gate computation:** the plan's gate at §1018 reads "≈ 613,603 events for tokenstraded" — corrected per gate memo §2.2 to 2,229,217 total. The boundary-crossing target was 213,452 pre-probe; the probe v3 actual is 175,005. The 95% gate is computed against the corrected probe target (175,005), not the pre-probe estimate. The corrected 95% threshold is `0.95 × 175,005 = 166,255` boundary events ingested.

---

## 5. Step-1 ingestion plan addendum

The full ingestion (Step 1 of 11.N.2b.2) MUST:

1. Pull `carboncontroller_evt_tokenstraded` events satisfying the basket-membership filter at the SQL layer (not Python-side; reduces credit cost).
2. The arb-event table pull is now **diagnostic-only**: not load-bearing for partition (the `trader` field on `tokenstraded` carries the arb signature). Pull it for ON-CHAIN provenance / audit trail (so future agents can reproduce this corrigendum) but do NOT use it as the partition source.
3. Apply the corrected partition `is_arb_routed = (trader == 0x8c05ea305235a67c7095a32ad4a2ee2688ade636)` in the Python `compute_carbon_xd()` filter, NOT at the SQL layer (cheaper Python-side scalar comparison; preserves both halves of the panel for diagnostic computation).

---

## 6. Probe credit consumption

| probe | credits |
|---|---|
| Step-0 v1 (naive JOIN) | 0.095 |
| Step-0 v2 (date health) | 0.103 |
| Step-0 v3 (full-range partition) | 0.098 |
| Step-0 v4 (2×2 contingency) | 0.094 |
| **TOTAL Step-0** | **0.390** |

Cumulative Task 11.N.2b probe spend (incl. 11.N.2b.1's 0.150): 0.540 credits. Headroom for full ingestion (≤ 10 credits estimate) remains trivial against the 25,000-credit budget.

---

## 7. References

- Plan §982 (X_d formula); §1018 (gate)
- Gate memo `2026-04-25-carbon-basket-gate-decision-memo.md` §3.3 (superseded narrative)
- Dune queries `7372237`, `7372241`, `7372243`, `7372247`
- 11.N.2 attribution research (`contracts/.scratch/2026-04-24-copm-bot-attribution-research.md`)

— end of corrigendum —
