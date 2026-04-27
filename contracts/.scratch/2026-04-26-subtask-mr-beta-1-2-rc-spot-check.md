# Reality Checker Spot-Check: MR-β.1 Sub-task 2 (Single-Pass Advisory)

**Date:** 2026-04-26
**Reviewer:** Reality Checker (single-pass advisory; convergent CR+RC+SD trio carries heavy review at sub-task 3)
**Subject commit:** `b8e220da1`
**Subject artifact:** `contracts/.scratch/2026-04-25-duckdb-address-audit.md` (315 lines)
**Sub-plan anchor:** `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` §C-2 + §H R-4 + §I sub-task 2 rescope
**Spot-check scope:** 7 narrow concerns enumerated by orchestrator; lightweight; tool budget 5–9 calls actually used (4 calls).

---

## §1 — Verdict

**PASS-with-non-blocking-advisories.**

Six of seven concerns VERIFIED clean against live DuckDB at audit-time path `contracts/data/structural_econ.duckdb` (read-only, no row mutations). One concern (Concern 3) carries a **minor empirical discrepancy** in the audit memo's null-pattern claim for `ccop_unique_senders`: memo §6.1 line 182 + §6.1 prose paragraph state `ccop_unique_senders` is "100% non-null (585/585)"; live probe returns **541/585 = 92.5% non-null** for that column (matching the other two `ccop_usdt_*` columns, NOT `copm_*` columns). This is a one-line factual nit inside an otherwise correctly-reasoned paired-source narrative; the **scope conclusion (DEFERRED-via-scope-mismatch under β; paired-source structure; both halves non-Mento-native) is unaffected**. Recommended for fix-up at sub-task 3 trio convergence (one-line edit).

PASS unblocks MR-β.1 sub-task 3 dispatch (canonical address-registry spec doc with convergent CR+RC+SD trio).

---

## §2 — Per-concern findings

### Concern 1 — Pre-flight enumeration query result match: **VERIFIED**

Independent live-DuckDB probe via `contracts/data/structural_econ.duckdb` (path confirmed via `env.py` `DUCKDB_PATH` constant at line 49):

```
SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'onchain_%' ORDER BY table_name
```

returned exactly 14 rows in this order:

1. `onchain_carbon_arbitrages`
2. `onchain_carbon_tokenstraded`
3. `onchain_copm_address_activity_top400`
4. `onchain_copm_burns`
5. `onchain_copm_ccop_daily_flow`
6. `onchain_copm_daily_transfers`
7. `onchain_copm_freeze_thaw`
8. `onchain_copm_mints`
9. `onchain_copm_time_patterns`
10. `onchain_copm_transfers`
11. `onchain_copm_transfers_sample`
12. `onchain_copm_transfers_top100_edges`
13. `onchain_xd_weekly`
14. `onchain_y3_weekly`

**Byte-for-byte match** with audit memo §1 lines 22–35. No table silently omitted, no extra table introduced.

### Concern 2 — Coverage completeness (count(pre-flight) == count(tagged)): **VERIFIED**

Pre-flight enumeration count: **14**.
Audit memo §3 + §9 tagging tally: 3 (DIRECT in-scope) + 1 (DIRECT mixed-scope) + 5 (DIRECT DEFERRED-via-scope-mismatch) + 5 (DERIVATIVE DEFERRED-via-scope-mismatch) + 0 (pure DEFERRED) = **14**. Match. No table double-counted; no table silently dropped. Coverage HALT-clear.

### Concern 3 — `onchain_copm_ccop_daily_flow` paired-source empirical claim: **VERIFIED with one-line empirical nit**

`PRAGMA table_info('onchain_copm_ccop_daily_flow')` confirms **8 substantive columns + 1 audit timestamp** (`_ingested_at` TIMESTAMP). Schema matches audit memo §6.1 lines 174–183:

- `date` DATE (not-null)
- `copm_mint_usd` VARCHAR (not-null)
- `copm_burn_usd` VARCHAR (not-null)
- `copm_unique_minters` UINTEGER (not-null)
- `ccop_usdt_inflow_usd` VARCHAR (nullable)
- `ccop_usdt_outflow_usd` VARCHAR (nullable)
- `ccop_unique_senders` UINTEGER (nullable)
- `source_query_ids` VARCHAR (nullable)

Null-pattern probe across 585 rows returned:

| Column | Non-null count | % non-null |
|---|---|---|
| `copm_mint_usd` | 585 | 100% |
| `copm_burn_usd` | 585 | 100% |
| `copm_unique_minters` | 585 | 100% |
| `ccop_usdt_inflow_usd` | 541 | 92.5% |
| `ccop_usdt_outflow_usd` | 541 | 92.5% |
| `ccop_unique_senders` | **541** | **92.5%** |

**Empirical nit (non-blocking advisory).** Audit memo §6.1 last paragraph (line 185) states: *"`copm_*` columns 100% non-null (585/585); `ccop_usdt_inflow_usd` and `ccop_usdt_outflow_usd` 92.5% non-null (541/585); `ccop_unique_senders` 100% non-null."* The final clause (`ccop_unique_senders` 100% non-null) is **incorrect**: the column is **541/585 = 92.5% non-null**, matching the other two `ccop_usdt_*` columns. This actually **strengthens** the audit's paired-source conclusion — all three `ccop_*` columns share an asymmetric null pattern distinct from `copm_*` columns, consistent with a single ccop-side Dune sub-query joined on `date`. The scope tag (DEFERRED-via-scope-mismatch under β) and the paired-source structure conclusion are unaffected.

Memo §6.2 + §6.3 + §6.4 + §6.5 narratives are all consistent with the corrected null pattern. **One-line fix at sub-task 3 trio convergence: change "`ccop_unique_senders` 100% non-null" → "`ccop_unique_senders` 92.5% non-null (541/585)".**

The PRAGMA-confirmed schema also clarifies that nullable-flag at the column-definition level (PRAGMA's `not-null` column = False for `ccop_*` columns; True for `copm_*` columns + `_ingested_at`) is itself an additional confirmation of the paired-source identity claim (the schema author intended the `ccop_*` half to be optional / sometimes-missing on join).

### Concern 4 — 10 proxy_kind values match: **VERIFIED**

Independent probe `SELECT proxy_kind, COUNT(*) FROM onchain_xd_weekly GROUP BY proxy_kind ORDER BY proxy_kind` returned exactly 10 distinct values + row counts:

| # | proxy_kind | rows |
|---|---|---|
| 1 | `b2b_to_b2c_net_flow_usd` | 79 |
| 2 | `carbon_basket_arb_volume_usd` | 82 |
| 3 | `carbon_basket_user_volume_usd` | 82 |
| 4 | `carbon_per_currency_brlm_volume_usd` | 82 |
| 5 | `carbon_per_currency_copm_volume_usd` | 82 |
| 6 | `carbon_per_currency_eurm_volume_usd` | 82 |
| 7 | `carbon_per_currency_kesm_volume_usd` | 82 |
| 8 | `carbon_per_currency_usdm_volume_usd` | 82 |
| 9 | `carbon_per_currency_xofm_volume_usd` | 82 |
| 10 | `net_primary_issuance_usd` | 84 |

Total rows = **819**, matching audit memo §3 row 13 ("819 rows total"). The DEFERRED-via-scope-mismatch entry `carbon_per_currency_copm_volume_usd` is present. The other 9 in-scope entries match audit memo §5 table (lines 150–160) byte-for-byte on slug + row counts. No new value introduced; no value missing.

### Concern 5 — `onchain_xd_weekly` mixed-scope tagging consistency: **VERIFIED**

Audit memo §3 row 13 tags `onchain_xd_weekly` as **DIRECT (mixed)** with rationale: "Aggregation table over 10 `proxy_kind` values; 819 rows total; per-proxy address-source provenance enumerated in §5." §5 then partitions: 9-of-10 in-scope + 1-of-10 DEFERRED-via-scope-mismatch (`carbon_per_currency_copm_volume_usd`).

The internal-consistency check holds:

- Table-level DIRECT tag is justified because the table's row-population logic is `contract_address`-scoped via the proxy_kind aggregation (each proxy_kind row is filtered by a fixed Mento or Minteo address).
- The mixed-scope qualifier is justified because 9-of-10 proxy_kinds resolve to Mento-native or basket-counter-side platform addresses (in-scope under β), while 1-of-10 (`carbon_per_currency_copm_volume_usd`) resolves to Minteo-fintech `0xc92e8fc2…` (out-of-scope under β).
- §3 row count (819) matches the per-proxy_kind sum (79 + 82×8 + 84 = 79 + 656 + 84 = 819). ✓
- §5 in-scope per-proxy_kind count (9) + DEFERRED count (1) = 10 = pre-flight DISTINCT count. ✓

Narrative is internally consistent; no rationale gap.

### Concern 6 — No DuckDB row mutation in commit diff: **VERIFIED**

`git diff b8e220da1~1 b8e220da1 --stat` returned exactly:

```
.../.scratch/2026-04-25-duckdb-address-audit.md    | 315 +++++++++++++++++++++
1 file changed, 315 insertions(+)
```

Only the audit memo file was added. No `.duckdb` file changes. No `.parquet` or other data file changes. No spec / plan / sub-plan / project-memory edits. No code changes. Commit scope-discipline-clean.

### Concern 7 — Anti-fishing scope discipline: **VERIFIED**

The audit memo:

- Does NOT contain new spec authoring (no new acceptance criteria, no new gate thresholds, no MDES_SD changes, no new statistical tests). All §7 forward-pointers are explicitly recorded as "OUT of scope for sub-task 2 / IN scope for Task 11.P.spec-β" — correct deferral.
- Contains only the permitted SQL fragments: §1 enumeration query (the ONE permitted per sub-plan §C-2); plus the schema-introspection / null-pattern / proxy_kind probe SQLs that the RC R-2 narrative-treatment + acceptance-line-9 coverage-completeness verification implicitly require (§5 GROUP BY proxy_kind probe; §6.1 PRAGMA table_info + null-count probes). These are bounded read-only schema/aggregation probes; not a backdoor to row-level data mining. Mild interpretation but defensible per sub-plan §C-2 acceptance lines 130–132 + RC R-2.
- Does NOT modify any project-memory file. No `.claude/memory/MEMORY.md` edits.
- Does NOT silently override byte-exact-immutability invariants. §10 explicitly reaffirms N_MIN = 75, POWER_MIN = 0.80, MDES_SD = 0.40, MDES_FORMULATION_HASH = `4940360dcd2987…cefa`, decision_hash = `6a5f9d1b05c1…443c`, Rev-2 14-row resolution matrix unchanged.
- Does NOT execute any rename or schema migration. The §6.4 future-revision rename recommendation is explicitly recorded as "NOT executed under this sub-plan; sub-plan §B-2 prohibits renames." Correct deferral.
- Does NOT issue any HALT-VERIFY override. §10 closes with "No HALT-VERIFY GATE fires under this audit."

Anti-fishing scope discipline holds.

---

## §3 — New findings outside the 7 concerns

**None blocking.** Two minor observations recorded for sub-task 3 trio's awareness:

1. **One-line null-pattern nit (Concern 3 above).** Audit memo §6.1 line 185 misstates `ccop_unique_senders` as 100% non-null when it is 92.5% (541/585). One-line fix at sub-task 3 convergence; does NOT alter scope tagging or paired-source conclusion.

2. **`_ingested_at` audit timestamp is undocumented in §6.1 schema enumeration.** PRAGMA returns 9 columns total; audit memo §6.1 line 174 says "8 substantive columns + audit timestamp" and then enumerates the 8 substantive ones. The wording is technically correct ("+ audit timestamp" implies 9th column exists) but a reader could miss that `_ingested_at` is one of the 9 columns rather than a separate metadata field. Non-blocking advisory; pure documentation clarity question, not a scope question.

Neither observation triggers HALT-VERIFY. Neither alters the audit's substantive conclusions on tag-coverage, address-source provenance, or β-scope disposition.

---

## §4 — Disposition

**Verdict: PASS-with-non-blocking-advisories.**

**Action:** MR-β.1 sub-task 3 dispatch is unblocked. The convergent CR + RC + SD trio at sub-task 3 should fold the one-line null-pattern fix (Concern 3) into the canonical address-registry spec doc's authoring (or as an audit-memo correction commit upstream of sub-task 3, at the trio's discretion). The 14-table count + 10-proxy_kind enumeration + paired-source structural conclusion are all empirically verified — sub-task 3 can build on them without re-probing DuckDB.

**Tool budget actually consumed:** 4 calls (Read audit memo + Read env.py + 1 Bash for git diff + 2 Bash for DuckDB probes). Within 5–9 budget.

**No row mutations performed by this spot-check.** Read-only DuckDB connection used throughout (`duckdb.connect(..., read_only=True)`).
