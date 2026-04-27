# X_d Partition-Rule Staleness — Disposition Memo (β resolution)

**Date:** 2026-04-27
**Author:** foreground orchestrator
**Trigger:** User-surfaced HALT-VERIFY query 2026-04-27 mid-NB-α sub-task 12 dispatch flagging three address-provenance concerns on Carbon DeFi attribution.
**RC + CR + TW corroboration target:** post-disposition 3-way review per `feedback_pathological_halt_anti_fishing_checkpoint`.
**User disposition:** **β** — document partition-rule staleness as a third corrigendum on top of Rev-5.3.5; close Rev-2 as **partition-rule-stale + Minteo-fintech scope-mismatched**; proceed to NB-α byte-exact migration; β-track Rev-3 spec must address BOTH provenance issues at re-ingestion time.

---

## 1. HALT trigger summary

User-surfaced 3 concerns 2026-04-27:

1. `0x6619871118D144c1c28eC3b23036FC1f0829ed3a` — claimed to be COPM, not CarbonController.
2. `0x8c05ea305235a67c7095a32ad4a2ee2688ade636` — claimed no transactions ~300 days ago.
3. `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` — claimed no transactions ~300 days ago.

Empirical resolution via independent Dune queries 7382618 + 7382632 + 7382639 + 7382645 + 7382647 + `searchTablesByContractAddress` lookups:

| Address | User claim | Empirical truth | Disposition |
|---|---|---|---|
| `0x6619871118…` | "COPM" | **CarbonController** (52 decoded tables; emits `tokenstraded`) per Dune `carbon_defi_celo.carboncontroller_evt_*` + `carbon_defi_multichain.carboncontroller_evt_*` | User wrong; project memory correct |
| `0x8c05ea30…` | "no tX 300d ago" | **DEAD since 2025-07-01 12:45:27 UTC**. 1,375,686 lifetime events; only 52 in Q3 2025 (300d-ago window); contract decoded as **BancorArbitrage V1** | **User EMPIRICALLY RIGHT** — load-bearing finding |
| `0x8A567e2a…` | "no tX 300d ago" | **LIVE today**. 285,458 lifetime events; **37,814 in Q3 2025**; first 2024-10-31, last 2026-04-27 09:37 UTC; decoded as `celocolombianpeso.stabletokenv2` Mento V2 StableTokenCOP | User wrong; Rev-5.3.5 β-corrigendum correct |

## 2. Critical empirical discovery — X_d partition rule is V1-only

The X_d formula per `contracts/data/carbon_celo/README.md` line 27 + `contracts/scripts/econ_pipeline.py` lines 2711-2799:

```sql
partition = CASE WHEN trader = 0x8c05ea305235a67c7095a32ad4a2ee2688ade636 THEN 'arb' ELSE 'user' END
```

This rule was authored under Task 11.N.2b.2 (Rev-5.3) when BancorArbitrage V1 was the only known arb router on Celo Carbon. **The rule is V1-only.**

### The V2 successor

Independent Dune `searchTablesByContractAddress` lookup confirms `0x20216f3056bf98e245562940e6c9c65ad9b31271` decodes as **`BancorArbitrageV2`** (38 decoded tables on `carbon_defi_multichain.bancorarbitragev2_*`). The V2 successor went live **2025-07-02 01:17:32 UTC** — exactly 12 hours and 31 minutes after V1's last event at 2025-07-01 12:45:27 UTC.

### Empirical contamination quantified

Carbon DeFi `tokenstraded` event partition counts on Celo, 2024-09-01 → 2026-04-04 window:

| Regime | Partition under V1-only rule | Event count | Distinct traders |
|---|---|---|---|
| Pre-2025-07-01 (V1 alive) | arb | 929,614 | 1 (V1 only) |
| Pre-2025-07-01 (V1 alive) | user | 368,389 | 68 |
| **Post-2025-07-01 (V1 dead)** | **'user' (broken classification)** | **669,872** | **80** |
| Post-2025-07-01 (V1 dead) | arb | 0 | 0 |

Of the 80 distinct post-2025-07-01 traders classified as 'user', the top contributor is `0x20216f30…` (BancorArbitrageV2) with **524,104 events** — i.e., **78.2% of post-2025-07-01 'user'-partition events are actually V2 arbitrage misclassified as user.**

### Rev-2 panel window straddles the V1→V2 transition

The Rev-2 panel window 2024-09-27 → 2026-03-13 (76 weeks) straddles 2025-07-01:

- **Weeks 1-~40 (2024-09-27 → 2025-07-01)**: partition rule WORKS. V1 was live; arb events caught.
- **Weeks ~41-76 (2025-07-01 → 2026-03-13)**: partition rule **silently fails**. V2's 524,104 events are misclassified as 'user'.

This is a **second-layer scope failure** independent of the Rev-5.3.5 COPM-Minteo provenance issue. The X_d primary series `carbon_basket_user_volume_usd` now has TWO simultaneous provenance failures:

1. **Per-currency proxy `carbon_per_currency_copm_volume_usd`** filtered to `0xc92e8fc2…` (Minteo, not Mento-native). Documented under Rev-5.3.5 β-disposition.
2. **Basket-aggregate `carbon_basket_user_volume_usd`** (THE PRIMARY): partition rule V1-only, broken post-2025-07-01. Documented under THIS Rev-5.3.6 disposition.

## 3. Disposition (Option β — mirror Rev-5.3.5 pattern)

Three disposition options were surfaced to the user (α: re-ingest from scratch; β: document and close as compound scope-mismatch; γ: fork sub-plan for partition-rule audit). User picked **β**.

### What β preserves (anti-fishing-immutable)

- Rev-2 published estimates (β̂ = −2.7987e−8, HAC(4) SE = 1.4234e−8, n = 76, T3b FAIL, byte-exact at full precision).
- N_MIN = 75, POWER_MIN = 0.80, MDES_SD = 0.40.
- MDES_FORMULATION_HASH = `4940360dcd2987…cefa` (runtime-verified at NB2 §1).
- Rev-4 decision_hash = `6a5f9d1b05c1…443c`.
- Rev-2 14-row resolution-matrix scope.
- DuckDB rows under `onchain_xd_weekly` (Carbon basket panel CSV-derived; consume-only).
- All 12 NB-α sub-task commits to date (sub-tasks 1-11; NB1 fully closed at `41969cd59`; NB2 §0 + §1 + §2 + §3 closed at `88d3631b9`).

### What β reframes (interpretation only)

- Rev-2 closes as **compound scope-mismatch close-out**: (a) per-currency Minteo-vs-Mento-native at the X_d source level (Rev-5.3.5); (b) basket-aggregate V1-only-partition staleness post-2025-07-01 (Rev-5.3.6).
- The Rev-2 X_d signal is interpreted as: pre-2025-07-01 portion = correct user-partition Mento-basket flow on Carbon; post-2025-07-01 portion = USER + V2-ARB-CONTAMINATED ≈ basket-aggregate trading volume regardless of partition.
- The gate FAIL is now explicable by both Rev-5.3.5 (Minteo-fintech-fintech-payments-rail signature) AND Rev-5.3.6 (V2-arb contamination amplifying the post-July-2025 X_d magnitude beyond user demand).
- The post-fix disposition framing is **partition-rule-stale + scope-mismatched X_d** (a compound term suitable for citing in NB-α interpretation cells).

### What β cascades to β-track Rev-3 spec (Task 11.P.spec-β; deferred)

β-track Rev-3 must:

1. Re-ingest X_d from `0x8A567e2a…` (Mento-native COPm) at the per-currency level.
2. Use a **multi-version partition rule**: `trader IN (0x8c05ea30…, 0x20216f30…, ...)` covering ALL known BancorArbitrage versions plus any documented successor arb routers discovered at β-spec authoring time.
3. Pre-commit a triangulation procedure for future arb-router successor detection: monitor `bancorarbitrageVN_evt_arbitrageexecuted` table-name proliferation on Dune at `searchTablesByContractAddress` for any contract decoded as a known-arb-class type.
4. Document the V1→V2 transition empirically (12h31m gap) as a precedent for "contract-versioning silent staleness" — analogous to the COPM-Minteo two-layer-inversion precedent under MR-β.1 sub-task 5 future-research safeguard.

## 4. NB-α dispatch chain — continue under compound scope-mismatch frame

NB-α is at sub-task 12 in flight (NB2 §4 HAC(12) bandwidth sensitivity Row 12) at HEAD `88d3631b9`. Sub-tasks 1-11 closed cleanly under Rev-5.3.5 substring discipline (banned: 0; canonical: 22/24/22/34 corpus-wide).

Under Rev-5.3.6 β-disposition:

- **Substring discipline UNCHANGED** in its core form (banned + canonical sets stay identical).
- **Interpretation cells should ALSO cite this disposition memo** (`contracts/.scratch/2026-04-27-x-d-partition-rule-staleness-disposition-beta.md`) wherever they discuss X_d post-2025-07-01 contamination. Optional — the Rev-5.3.5 framing is still authoritative for the Minteo-fintech layer; Rev-5.3.6 adds a partition-rule-stale layer.
- **No re-estimation of any Rev-2 row.** Numbers stay byte-exact.
- **Sub-task 12 (NB2 §4 HAC(12)) in flight when HALT fired**: when AR returns, commit per Rev-5.3.5 substring discipline (no Rev-5.3.6-specific changes needed for HAC(12) which is SE-method robustness on the same X_d).
- **NB-α can continue.** Sub-tasks 13-31 dispatch under the same Rev-5.3.5 + Rev-5.3.6 compound-scope-mismatch frame.

## 5. Project memory amendments

Two memory files require corrigenda under Rev-5.3.6:

- `project_carbon_user_arb_partition_rule` — partition rule was V1-only; post-2025-07-01 it silently fails (V2 successor not in whitelist); documented post-2025-07-01 contamination = 78.2% of 'user'-partition events on the basket aggregate.
- `project_carbon_defi_attribution_celo` — add BancorArbitrageV2 `0x20216f30…` to the contract-attribution roster as the V1 successor; document the V1→V2 transition timestamp (V1 last event 2025-07-01 12:45:27 UTC; V2 first event 2025-07-02 01:17:32 UTC; gap 12h31m).

Both amendments are append-only β-corrigenda per `feedback_pathological_halt_anti_fishing_checkpoint` anti-fishing-on-memory-edits.

## 6. Registry spec doc (sub-task 3 deliverable) — append BancorArbitrageV2 to out-of-scope appendix

The canonical address-registry spec doc at `contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md` (commit `2a0dcf8fe` + RC re-review PASS `1d30f6fc4`) carries a §1.3 byte-exact-immutability invariant: future address additions land as new appendix sections, never as in-place edits to existing entries.

Per that invariant, a NEW appendix entry for `0x20216f30…` (BancorArbitrageV2) is added as **§8.2** — out-of-scope third-party tokens, audit-trail preservation. The existing §8.1 entry (COPM-Minteo) is unmodified; §8.2 is appended.

## 7. Anti-fishing-invariant integrity preserved

No invariant is relaxed:

- N_MIN = 75 unchanged.
- POWER_MIN = 0.80 unchanged.
- MDES_SD = 0.40 unchanged.
- MDES_FORMULATION_HASH unchanged.
- decision_hash unchanged.
- Rev-2 14-row resolution-matrix scope unchanged.
- 0 DuckDB row mutations under this disposition.
- All 12 prior NB-α commits preserved byte-exact (no commit reverted).

## 8. Empirical evidence trail

### Dune queries (free-tier)

| Query ID | Description | Credits | Findings |
|---|---|---|---|
| `7382618` | 3-address activity probe (COPm + V1 + CarbonController, lifetime + 300d window + Q4 2024) | 0.034 | V1 dead 2025-07-01; COPm 37,814 events Q3 2025; CC 65,000 |
| `7382632` | partition contamination by regime (pre/post 2025-07-01) | 0.026 | 78% post-July contamination |
| `7382645` | top 10 post-2025-07-01 traders | 0.008 | `0x20216f30…` = 524,104 events (#1) |
| `7382647` | 3-regime debug transaction samples | 0.037 | tx hashes for Celoscan inspection |

### `searchTablesByContractAddress` lookups

- `0x6619871118D144c1c28eC3b23036FC1f0829ed3a` → 52 decoded tables, project `carbon_defi_celo`/`carbon_defi_multichain`, contract `CarbonController` ✅
- `0x8c05ea305235a67c7095a32ad4a2ee2688ade636` → 16 decoded tables, project `carbon_defi_celo`/`carbon_defi_multichain`, contract `BancorArbitrage` (V1) ✅
- `0x20216f3056bf98e245562940e6c9c65ad9b31271` → 38 decoded tables, project `carbon_defi_multichain`, contract `BancorArbitrageV2` ✅ (the SUCCESSOR)
- `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` → 24 decoded tables (per Rev-5.3.5 sub-task 1), project `celocolombianpeso`, contract `StableTokenV2` ✅

### Debug transactions (Celoscan inspectable)

- Pre-July-2025 V1 'arb' (correct): tx `0x0e39f99e6eb22b371d12f879e27565d3b68c20547bd24595bb9f6abb68a44ed8`, trader `0x8c05ea30…` (V1 LAST event), 2025-07-01 12:45:27 UTC.
- Pre-July-2025 'user' (correct): tx `0xa81c12a1ae02cc42d5eceba4e203ded97a4c4438887b4529b1d212aed1295091`, trader `0x5f7635086d…`, 2025-07-01 23:10:07 UTC.
- Post-July-2025 'user' (BROKEN): tx `0x85c0e993fab72ce058bac450bdabeda1559ae1a49b866125ca4e85cf09ba2f84`, trader `0x20216f30…` (BancorArbitrageV2), 2025-10-31 23:39:12 UTC.

## 9. References

- Disposition memo (this file): `contracts/.scratch/2026-04-27-x-d-partition-rule-staleness-disposition-beta.md`
- Rev-5.3.5 disposition (companion, prior layer): `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md`
- Major plan: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (Rev-5.3.6 CORRECTIONS to be appended at file end)
- MR-β.1 sub-plan: `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` (§J CORRECTIONS to be appended)
- NB-α sub-plan: `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md` (CORRECTIONS to be appended; substring discipline unchanged)
- Registry spec: `contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md` (§8.2 appendix entry to be appended)
- X_d formula source: `contracts/scripts/econ_pipeline.py` lines 2711-2799 + `contracts/data/carbon_celo/README.md`
- Carbon basket panel CSV: `contracts/data/carbon_celo/weekly_basket_panel.csv` (16,343 bytes; 253 rows; 82 Friday anchors)
- Project memory anchors load-bearing on this disposition:
  - `project_carbon_user_arb_partition_rule` (β-corrigendum target; partition rule = V1 only, post-2025-07-01 stale)
  - `project_carbon_defi_attribution_celo` (β-corrigendum target; add V2 to roster)
  - `project_abrigo_mento_native_only` (Rev-5.3.5 β-corrigendum already landed; this disposition compounds with it)
- Dune project namespaces:
  - `carbon_defi_celo.carboncontroller_evt_tokenstraded` (event source)
  - `carbon_defi_celo.bancorarbitrage_evt_arbitrageexecuted` (V1)
  - `carbon_defi_multichain.bancorarbitragev2_evt_arbitrageexecuted` (V2 successor)
- Mento V3 deployment docs (working URL post-RC-3 verification): https://docs.mento.org/mento-v3/build/deployments/addresses.md
- Celo Token List (chainId 42220): https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json
