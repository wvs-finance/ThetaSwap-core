# Task 11.C Bridge-Validation Result (Phase-A.0 Rev-3.4)

**Verdict (pre-registered gate):** `FAIL-BRIDGE`

**Execution timestamp (UTC):** 2026-04-24T04:23:56+00:00

## Observed bridge statistics

| Statistic | Value |
|---|---|
| Pearson ρ (N=6 primary) | `+0.755417` (two-sided p = `0.0824`) |
| Pearson ρ (N=5 robustness, excl. 2024-Q3) | `+0.706886` (two-sided p = `0.1819`) |
| Sign-concordance count | `2/5` (threshold ≥ 3) |
| Sign-concordant? | `False` |
| ρ > 0.5? | `True` |
| 0.3 < ρ ≤ 0.5? | `False` |
| ρ ≤ 0.3? | `False` |

## Overlap window

Observed N = 6 quarterly observations (task description prescribed N = 7, off
by one; see preamble header of `0B_bridge_validation.ipynb`). K = 5 Q-over-Q
transitions. Quarterly sample: 2024-Q3, 2024-Q4, 2025-Q1, 2025-Q2, 2025-Q3,
2025-Q4.

## Pre-registered gate (committed BEFORE any ρ computation)

| Verdict | Condition |
|---|---|
| PASS-BRIDGE | ρ > 0.5 AND sign-concordant (≥ 3 of 5 transitions agree) |
| INCONCLUSIVE-BRIDGE | 0.3 < ρ ≤ 0.5 AND sign-concordant |
| FAIL-BRIDGE | ρ ≤ 0.3 OR sign-discordant (< 3 of 5 transitions agree) |

## Narrative implication (Rev-3.1 recovery protocol)

Primary regression still runs (the on-chain X is a well-defined observable). Narrative shifts from 'remittance' to 'crypto-rail income-conversion' per Rev-3.1 recovery protocol item 1. A Rev-1.1.1 spec patch (to be authored at FAIL-BRIDGE observation) re-scopes §4.1 only; §§4.2+ mechanism unchanged. Task 11.D decision gate: the spec patch is classified as wording/cadence-only (X-interpretation relabel), not an economic-mechanism change.

## Rev-3.4 NaN-ambiguity protocol applied

Quarterly aggregation distinguished `partial_week` (dropped) from
`all_zero_full_week` (retained as valid zero) per plan line 329. Across the
84 weekly rows emitted by Task-11.B: 1 partial_week, 2 all_zero_full_week,
81 valid. The single partial_week (2024-09-20 boundary Friday) was dropped;
the two all_zero_full_week rows contributed 0 USD to their respective
quarterly sums.

## Source artifact paths

- Task-11.A daily CSV: `contracts/data/copm_ccop_daily_flow.csv`
- Task-11.B aggregator: `contracts/scripts/weekly_onchain_flow_vector.py`
- Task-11 BanRep quarterly CSV: `contracts/data/banrep_remittance_aggregate_monthly.csv`
- This notebook: `contracts/notebooks/fx_vol_remittance_surprise/Colombia/0B_bridge_validation.ipynb`

## Quarterly bridge table (USD)

```
             on_chain_quarterly_sum_usd  banrep_quarterly_inflow_usd  on_chain_valid_weeks_count
quarter_end                                                                                     
2024-09-30                         0.00             3,052,700,000.00                           1
2024-12-31                   898,766.34             3,167,990,000.00                          13
2025-03-31                 7,069,193.29             3,130,620,000.00                          13
2025-06-30                 3,697,897.06             3,277,470,000.00                          13
2025-09-30                16,681,562.69             3,354,000,000.00                          13
2025-12-31                28,691,059.42             3,336,180,000.00                          13
```

## Δ Q-over-Q transitions

| Transition | Δ on-chain (USD) | Δ BanRep (USD) | Concordant? |
|---|---:|---:|---:|
| 2024-09-30 → 2024-12-31 | +898,766.34 | +115,290,000.00 | True |
| 2024-12-31 → 2025-03-31 | +6,170,426.96 | -37,370,000.00 | False |
| 2025-03-31 → 2025-06-30 | -3,371,296.24 | +146,850,000.00 | False |
| 2025-06-30 → 2025-09-30 | +12,983,665.63 | +76,530,000.00 | True |
| 2025-09-30 → 2025-12-31 | +12,009,496.73 | -17,820,000.00 | False |

## Anti-fishing framing (Rev-1 §10)

This exercise is a distinct pre-commitment on the remittance external-inflow
channel via the on-chain COPM+cCOP rail. It is NOT a rescue of the CPI-FAIL
verdict (2026-04-19). Provenance anchor:
`/home/jmsbpp/apps/liq-soldk-dev/notes/REMITTANCE_VOLATILITY_SWAP/REMITTANCE_VOLATILITY_SWAP.md`
has mtime 2026-04-02 (17 days before CPI-FAIL).

The pre-registered gate thresholds were NOT adjusted after observing the ρ
value of +0.7554. The sign-concordance AND-clause is load-bearing in the
PASS-BRIDGE rule and was honored: although ρ > 0.5, the 2/5 concordance
count triggered the FAIL-BRIDGE OR-clause.
