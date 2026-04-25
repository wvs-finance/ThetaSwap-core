# Y₃ × X_d Coverage HALT — Task 11.O Disposition Memo

**Author**: assistant (continuation patch after 11.N.2d agent credit-cutoff)
**Date**: 2026-04-25 10:15 EDT
**Trigger**: Anti-fishing checkpoint — primary X_d × Y₃ joint coverage = **56 weeks** < pre-committed N_MIN = **75**.
**Plan revision in scope**: Rev-5.3.1 (commit `7afcd2ad6` — N_MIN 80→75 path α).
**Last clean commit**: `765b5e203` — `feat(abrigo): Rev-5.3.1 Task 11.N.2d — Y₃ 4-country inequality-differential dataset`.
**Status**: HALT. NO further task dispatch (11.N.2d.1 / 11.O / etc.) until user picks a disposition.

---

## 1. Discovery

After ingesting Y₃ at PRIMARY_PANEL_START=2024-09-01 → END=2026-04-24:

| Source | Per-country window | Rows |
|---|---|---|
| CO equity (Yahoo ICOLCAP.CL) | 2024-09-02 → 2026-04-24 | 403 |
| BR equity (Yahoo ^BVSP) | 2024-09-02 → 2026-04-24 | 409 |
| EU equity (Yahoo ^STOXX) | 2024-09-02 → 2026-04-24 | 410 |
| CO CPI (IMF IFS via DBnomics) | 2024-09-01 → **2025-07-01** | 11 |
| BR CPI (IMF IFS via DBnomics) | 2024-09-01 → **2025-07-01** | 11 |
| EU CPI (Eurostat HICP via DBnomics) | 2024-09-01 → **2025-12-01** | 16 |

CPI lag dominates: equity is current; IMF IFS for CO/BR is **9-month stale**, Eurostat HICP is 4-month stale.

`compute_y3_aggregate` takes the per-country-differential intersection — bounded by the latest week where every landed country has both equity Δlog and WC-CPI Δlog. Result: **59-week 3-country panel** ending 2025-10-24 (Kenya gracefully dropped per design §10 row 1; methodology tagged `y3_v1_3country_ke_unavailable`).

Joint with X_d:

| X_d proxy_kind | nonzero overlap with Y₃ |
|---|---|
| `b2b_to_b2c_net_flow_usd` | 44 |
| **`carbon_basket_user_volume_usd`** (primary) | **56** |
| `carbon_basket_arb_volume_usd` | 43 |
| `carbon_per_currency_copm_volume_usd` | 47 |
| `carbon_per_currency_brlm_volume_usd` | 23 |
| `carbon_per_currency_eurm_volume_usd` | 21 |
| `carbon_per_currency_kesm_volume_usd` | 16 |
| `carbon_per_currency_usdm_volume_usd` | 0 |
| `carbon_per_currency_xofm_volume_usd` | 0 |
| `net_primary_issuance_usd` | 44 |

Primary regression spec (per Rev-5.3.1) is at the 56-week intersection — **19 weeks short of pre-committed N_MIN=75**.

---

## 2. Why this is a HALT, not a "just-run-it" event

Per `feedback_pathological_halt_anti_fishing_checkpoint` and `feedback_strict_tdd`:

- N_MIN=75 was pre-committed at Rev-5.3.1 with a documented power calculation (`MDES_FORMULATION_HASH=4940360d…6389cefa`, scipy power 0.8638).
- Running 11.O at N=56 without an explicit pre-commitment update is **silent threshold tuning** — the exact failure mode the discipline forbids.
- The CORRECTIONS-block protocol requires:
  (a) HALT,
  (b) disposition memo (this document),
  (c) user-enumerated pivot,
  (d) post-hoc 3-way review of whichever path is picked.

This memo satisfies (a)+(b). Awaiting user input on (c).

---

## 3. Disposition options

Each option below lists: action, statistical implication, anti-fishing risk, downstream cascade.

### Option β — Further N_MIN relaxation (75 → ≤56)

**Action**: Re-pin `MDES_SD` and re-run `required_power(56, 13, MDES_SD)` to recover ≥0.80; if no MDES choice meets the floor, document and accept lower power.
**Implication**: Statistical detectability shrinks. With f² scaling, an N=56 multi-X (k=13) regression at α=0.05 needs roughly MDES f² ≥ 0.31 (Cohen large) to retain 0.80 power — that's much higher than Rev-5.3.1's f² ≈ 0.16.
**Anti-fishing risk**: HIGH. Two relaxations on one plan revision (80→75→56) approaches "tune until it passes." Reviewer pushback near-certain.
**Cascade**: 11.O can proceed under disclosed weakness; results published with explicit power statement.

### Option γ — Primary panel ⇄ Sensitivity panel swap (RECOMMENDED)

**Action**: Promote `SENSITIVITY_PANEL_START=2023-08-01` to be the primary window (2023-08-01 → 2025-10-24, the actual upper-bound from CPI lag). Y₃ panel grows from 59 → ~115 weeks. X_d × Y₃ intersection grows correspondingly (the X_d series start at 2024-08-30 so the intersection becomes ~60-65 weeks for `carbon_basket_user_volume_usd` — still tight for k=13).
**Implication**: Sample roughly +9 weeks for the primary X_d (~65 vs. 56). Below 75 still — but path γ + light β micro-relaxation (e.g., 75 → 65) is far less anti-fishing-adjacent than path β alone.
**Anti-fishing risk**: MODERATE. Window swap is documented, deterministic, doesn't game thresholds — but it does change the pre-committed primary panel, which needs disclosure.
**Cascade**: Re-ingest Y₃ at extended window (idempotent UPSERT — non-destructive); 11.N.2d.1 becomes redundant or reframes as "primary-window extension" rather than "sensitivity panel"; 11.O proceeds.

### Option δ — Switch CO/BR CPI source

**Action**: Replace IMF IFS via DBnomics with native stat-agency feeds (DANE for Colombia, IBGE for Brazil). Both publish monthly CPI with ~1-month lag — would push CO/BR CPI cutoff from 2025-07-01 to ~2026-03-01, gaining ~30 weeks.
**Implication**: Y₃ panel could extend to ~2026-02-2026-03 (4-week CPI→weekly LOCF tail). X_d × Y₃ intersection grows substantially.
**Anti-fishing risk**: LOW. Source upgrade is methodologically clean — same definition, fresher publication.
**Cascade**: ~6 hours of data-engineer fetcher work + design-doc Rev-2 disclosing source change. Not "low-risk continuation". Schedule cost likely 1-2 days.

### Option ε — Run 11.O at N=56, fully disclosed

**Action**: Proceed with primary regression at 56 weeks; spec explicitly disclaims "below pre-committed N_MIN; result interpreted as preliminary/pilot."
**Implication**: Power < pre-committed floor. Effect-sizes possible but error bars wide. Falsification harder.
**Anti-fishing risk**: LOW (because fully disclosed) but **scientific cost is HIGH**: a 56-week pilot can't produce a publishable verdict on the inequality-differential thesis.
**Cascade**: 11.O runs; verdict almost certainly framed as "directional / inconclusive" rather than gate-FAIL or gate-PASS.

### Option ζ — Combine γ + δ

**Action**: Both window-swap (γ) and CO/BR source upgrade (δ).
**Implication**: Y₃ ~110-115 weeks (Aug-2023 → Mar-2026). X_d × Y₃ intersection ~80+ weeks → exceeds N_MIN=75.
**Anti-fishing risk**: LOW.
**Cascade**: Same ~1-2 days as δ alone, but yields a pre-committed-spec-clean result.

---

## 4. Recommendation

**Option ζ (γ + δ)** is the only path that lands the original Rev-5.3.1 N_MIN=75 commitment without further relaxation. It costs ~1-2 days of fetcher work and a design-doc Rev-2.

**If schedule is a hard constraint**, Option γ alone is the cleanest cheap path — accept a single, documented N_MIN micro-relaxation (75 → 65 or so) under explicit disclosure.

Avoid Option β (compounding relaxations) and Option ε (publishable verdict not feasible at N=56).

---

## 5. Action gate

**Awaiting user pick: β / γ / δ / ε / ζ.**

No agent dispatch (11.N.2d.1, 11.O, etc.) until disposition is locked.

---

## Appendix — verification queries

```sql
-- Y₃ panel
SELECT MIN(week_start), MAX(week_start), COUNT(*) FROM onchain_y3_weekly;
-- → ('2024-09-13', '2025-10-24', 59)

-- per-country coverage
SELECT
  COUNT(*) FILTER (WHERE copm_diff IS NOT NULL) AS co_n,
  COUNT(*) FILTER (WHERE brl_diff IS NOT NULL) AS br_n,
  COUNT(*) FILTER (WHERE kes_diff IS NOT NULL) AS ke_n,
  COUNT(*) FILTER (WHERE eur_diff IS NOT NULL) AS eu_n
FROM onchain_y3_weekly;
-- → (59, 59, 0, 59)

-- X_d × Y₃ joint nonzero
SELECT x.proxy_kind,
       COUNT(*) FILTER (WHERE x.value_usd != 0 AND x.value_usd IS NOT NULL) AS n
FROM onchain_xd_weekly x
INNER JOIN onchain_y3_weekly y ON x.week_start = y.week_start
GROUP BY x.proxy_kind ORDER BY n DESC;
```

```python
# CPI lag confirmation
from datetime import date
from scripts.y3_data_fetchers import fetch_country_wc_cpi_components
for c in ('CO', 'BR', 'EU'):
    df = fetch_country_wc_cpi_components(c, date(2024,9,1), date(2026,4,24))
    print(c, df['date'].max())
# CO 2025-07-01
# BR 2025-07-01
# EU 2025-12-01
```
