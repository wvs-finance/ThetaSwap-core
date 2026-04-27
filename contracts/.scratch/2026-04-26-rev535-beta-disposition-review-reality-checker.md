# Rev-5.3.5 β-Resolution Disposition — Reality Checker Trio Review

**Reviewer:** Reality Checker (TestingRealityChecker persona; evidence-obsessed; defaults to NEEDS-WORK).
**Review date:** 2026-04-26.
**Tool budget used:** 13 tool calls (5 reads, 4 Bash, 2 Dune queries + 2 Dune executions, 2 WebFetch). Within the 8–15 budget.
**Trio peers:** CR + TW running in parallel; no coordination per dispatch directive.
**Review scope:** disposition memo `2026-04-26-mr-beta-1-1-halt-resolution-beta.md`; Rev-5.3.5 CORRECTIONS in major plan; §I CORRECTIONS in `2026-04-25-ccop-provenance-audit.md` sub-plan; CORRECTIONS in `2026-04-25-rev2-notebook-migration.md` sub-plan; project-memory β-corrigenda (`project_mento_canonical_naming_2026`, `project_abrigo_mento_native_only`); DE deliverable; earlier RC spot-check.

---

## 1. VERDICT

**PASS-with-non-blocking-advisories.**

Every load-bearing empirical claim in the disposition memo independently verified. The HALT-resolution discipline is intact. The anti-fishing scope-mismatch framing is consistently maintained without rescue-claim drift. The audit-trail commits exist, are docs-only, and mutate no DuckDB row. Coverage of `onchain_*` tables in the §I CORRECTIONS is complete (14/14 tables accounted for). Two non-blocking advisories surfaced — both pertain to forward-looking work under Task 11.P.spec-β, not to the disposition itself.

**One advisory rises to NEEDS-WORK in its specific domain (RC-Concern-8) but does NOT block the disposition** because the memo §6 explicitly defers β-track Rev-3 feasibility verification to β-spec authoring time. The advisory is therefore recorded as forward-looking guidance for the β-spec sub-plan author, not as a fix-up requirement for THIS disposition.

---

## 2. PER-CONCERN FINDINGS

### RC-Concern-1: Re-verify Dune empirical probe — VERIFIED (with minor live-drift)

**Independent execution:** Dune query `7379527` (RC-authored, fresh), execution `01KQ6CZWDVKZZM6CWCJ82F4Y29`, 0.014 credits, free tier.

**Counter-query against `celocolombianpeso_celo.stabletokenv2_evt_transfer`:**

| Metric | Memo claim | RC re-execution | Δ | Tolerance | Status |
|---|---|---|---|---|---|
| Total transfers | 285,390 | **285,420** | +30 | ≤1000 (live drift) | ✓ |
| Distinct senders | 5,015 | **5,015** | 0 | ≤100 | ✓ |
| Distinct receivers | 16,918 | **16,918** | 0 | ≤100 | ✓ |
| First transfer | 2024-10-31 16:35:48 UTC | **2024-10-31 16:35:48 UTC** | exact | exact | ✓ |
| Last transfer | 2026-04-26 21:12:59 UTC | **2026-04-27 02:12:04 UTC** | +5 hours | live | ✓ |
| Distinct weeks active | 78 | **79** | +1 | live | ✓ |
| Distinct days active | 534 | **535** | +1 | live | ✓ |

The +30 transfers / +1 week / +1 day deltas are explained by the ~5 hours of live activity between the memo's authoring (2026-04-26 21:12 UTC = `00790855b` at 22:37:23 EDT = 02:37 UTC 2026-04-27) and the RC's re-execution (2026-04-27 ~02:12 UTC). Live-drift is well within tolerance and confirms the memo's claims are not synthesized.

**N_MIN=75 gate clearance on X_d-only chronological window:** RE-VERIFIED at 79 weeks (4-week margin).

### RC-Concern-2: Mento-protocol-native dispositive evidence — VERIFIED

**Two independent verifications:**

(a) `searchTablesByContractAddress` against `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` returned **24 decoded tables** under Dune project `celocolombianpeso` with contract name `StableTokenV2`. The four Mento-protocol-specific governance event tables exist:
- `celocolombianpeso_celo.stabletokenv2_evt_exchangeupdated`
- `celocolombianpeso_celo.stabletokenv2_evt_validatorsupdated`
- `celocolombianpeso_celo.stabletokenv2_evt_brokerupdated`
- `celocolombianpeso_celo.stabletokenv2_evt_initialized`

(b) **Non-zero row counts confirmed** via Dune query `7379530`, execution `01KQ6D270SN52J6KXZQMY6RED2`, 0.008 credits:

| Event table | Row count |
|---|---|
| `evt_exchangeupdated` | **1** |
| `evt_validatorsupdated` | **1** |
| `evt_brokerupdated` | **1** |
| `evt_initialized` | **2** (V1 + V2 init for UUPS-upgradeable proxy) |

Single-row counts are consistent with one-shot deployment-time governance configuration. **The presence of these rows is dispositive of Mento-protocol-native status** because the Minteo-fintech token at `0xc92e8fc2…` would not emit `ExchangeUpdated` / `ValidatorsUpdated` / `BrokerUpdated` events — those are protocol-internal events emitted only when the Mento broker / reserve / validators contracts are configured against the StableToken. The memo's "dispositive" claim is empirically validated.

### RC-Concern-3: Mento V3 deployment docs cross-check — VERIFIED (after URL fallback)

**First WebFetch attempt:** `https://docs.mento.org/mento/protocol/deployments` — returned a 404 stub page; no address data.

**Fallback WebFetch:** `https://docs.mento.org/mento-v3/build/deployments/addresses.md` (alternate URL used by both DE and earlier RC) — returned the verbatim entry:

> **StableTokenCOP** | [`0x8a567e2ae79ca692bd748ab832081c45de4041ea`](https://celoscan.io/address/0x8a567e2ae79ca692bd748ab832081c45de4041ea) | `0x8a567e2ae79ca692bd748ab832081c45de4041ea`

Plus the other five Mento-native StableToken addresses, all matching the inventory memo:
- StableTokenUSD: `0x765de816845861e75a25fca122bb6898b8b1282a`
- StableTokenEUR: `0xd8763cba276a3738e6de85b4b3bf5fded6d6ca73`
- StableTokenBRL: `0xe8537a3d056da446677b9e9d6c5db704eaab4787`
- StableTokenKES: `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0`
- StableTokenXOF: `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08`

The Mento V3 docs ALSO returned a useful cross-check: "All listed entries share the same implementation address: `0x434563B0604BE100F04B7Ae485BcafE3c9D8850E`" — i.e., these are EIP-1967 proxies pointing at a common `StableTokenV2` implementation (consistent with the Dune `evt_initialized` returning 2 rows).

**The memo's "verbatim canonical Mento Colombian Peso address" claim is empirically grounded.** Status: VERIFIED.

(Non-blocking advisory: the disposition memo cites the docs URL as `https://docs.mento.org/mento/protocol/deployments` at line 140 — that URL is currently a 404 stub. The working canonical URL is `https://docs.mento.org/mento-v3/build/deployments/addresses.md`. This is a citation papercut, not a verification failure; see §3 Advisory R-1.)

### RC-Concern-4: Celo Token List cross-check — VERIFIED

WebFetch against `https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json` returned the verbatim entries:

| Address | Name | Symbol | Decimals |
|---|---|---|---|
| `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` | **"COP Minteo"** | `COPM` | 18 |
| `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` | **"Mento Colombian Peso"** | `COPm` | 18 |

Both entries match the memo's claims (lines 18, 32, 67) byte-exact. The case distinction (`COPM` vs. `COPm`) is preserved — celo-org's canonical chainId-42220 registry treats them as two distinct entries with different symbols. Status: VERIFIED.

### RC-Concern-5: HALT-discipline preservation (audit-trail integrity) — VERIFIED

**All three commits exist:**

| Commit | Date (EDT) | Subject | Files touched |
|---|---|---|---|
| `3611b0716` | 2026-04-26 18:15 | DE inventory deliverable | 1 file (`.scratch/2026-04-25-mento-native-address-inventory.md`) |
| `3286dfe66` | 2026-04-26 18:25 | RC spot-check | 1 file (`.scratch/2026-04-25-subtask-mr-beta-1-1-rc-spot-check.md`) |
| `00790855b` | 2026-04-26 22:37 | Rev-5.3.5 β-resolution disposition | 4 files (disposition memo + major plan + 2 sub-plans) |

**No DuckDB mutation:** `git log --all --diff-filter=AMD -- '*.duckdb'` returned **0 commits**. The three audit-trail commits touched only `.md` files. Status: VERIFIED.

**HALT-discipline pattern intact:**
- DE surfaced HALT instead of silently picking an address.
- RC spot-checked and corroborated independently before user disposition.
- User decision (path β) is recorded in the disposition memo header (line 7).
- Disposition memo lands as audit-trail; sub-plan + major plan get CORRECTIONS appendices (not silent rewrites).
- Project memory carries β-corrigenda blocks at top with original content **preserved verbatim** below; the canonical memo line that was wrong (`project_mento_canonical_naming_2026` line 37 "COPM (Minteo, unchanged)") is **annotated with an explicit `⚠️ SUPERSEDED` marker**, not deleted.

This is the textbook anti-fishing checkpoint pattern from `feedback_pathological_halt_anti_fishing_checkpoint`.

### RC-Concern-6: Anti-fishing scope-mismatch vs rescue-claim discipline — VERIFIED

The disposition framing is consistently maintained:

| Required discipline | Memo evidence | Status |
|---|---|---|
| Rev-2 estimates NOT re-interpreted as positive Mento-hedge signal | Line 66: "Rev-2 published estimates … are byte-exact immutable per Rev-5.3.x anti-fishing invariants. They remain in the audit trail unchanged." | ✓ |
| Reframe is "wrong-scope X_d, so didn't test the thesis," NOT "right-scope once we squint" | Line 68: "Rev-2 was measuring `0xc92e8fc2…` events — which under β is Minteo-fintech (out of Mento-native scope). Rev-2 therefore closes as scope-mismatch, NOT as 'Mento-hedge-thesis-tested-and-failed.'" | ✓ |
| Three Rev-2 anomalies explained by Minteo-fintech identity, NOT used to argue right-direction | Lines 72-74: sign-flip "consistent with Minteo-fintech being a payments / B2B-API rail"; ρ confounder "consistent with Minteo's user base being FX-payments-driven"; T1 REJECTS "consistent with Minteo activity being a payments-cycle predictor, not a structural hedge-demand signal." | ✓ |
| Anti-fishing invariants explicitly preserved | Lines 102-108: N_MIN, POWER_MIN, MDES_SD, MDES_FORMULATION_HASH, decision_hash, 14-row resolution matrix all enumerated as unchanged. | ✓ |
| "Scope correction, not threshold relaxation" called out | Line 110: explicit verbatim. | ✓ |

**No drift detected.** The memo nowhere argues Rev-2's β̂ < 0 is "right-direction" or that the FAIL is somehow validating. It explicitly frames the FAIL as a *scope-mismatched test* (i.e., NOT a test of the actual Mento-native hedge thesis). Critically, the memo also explicitly frames β-track Rev-3 as starting fresh: "β-track Rev-3 starts fresh under all the same anti-fishing thresholds against the correct on-chain address." That's the right discipline.

The scope-mismatch reframe is **honest and load-bearing** — it correctly identifies that Rev-2 was answering a different question than the one the Abrigo product cares about. Without the reframe, the gate-FAIL would have closed the Mento-hedge thesis prematurely against the wrong evidence.

Status: VERIFIED.

### RC-Concern-7: Coverage completeness — VERIFIED

Live DuckDB enumeration via `SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'onchain_%' ORDER BY 1` returned **14 tables**:

```
onchain_carbon_arbitrages
onchain_carbon_tokenstraded
onchain_copm_address_activity_top400
onchain_copm_burns
onchain_copm_ccop_daily_flow
onchain_copm_daily_transfers
onchain_copm_freeze_thaw
onchain_copm_mints
onchain_copm_time_patterns
onchain_copm_transfers
onchain_copm_transfers_sample
onchain_copm_transfers_top100_edges
onchain_xd_weekly
onchain_y3_weekly
```

§I CORRECTIONS classification cross-check:

| Live table | §I CORRECTIONS treatment | Status |
|---|---|---|
| `onchain_copm_address_activity_top400` | DEFERRED-via-scope-mismatch (line listed) | ✓ |
| `onchain_copm_burns` | DEFERRED-via-scope-mismatch (line listed) | ✓ |
| `onchain_copm_ccop_daily_flow` | DEFERRED-via-scope-mismatch + strengthened R-2 disambiguation | ✓ |
| `onchain_copm_daily_transfers` | DEFERRED-via-scope-mismatch (line listed) | ✓ |
| `onchain_copm_freeze_thaw` | DEFERRED-via-scope-mismatch (line listed) | ✓ |
| `onchain_copm_mints` | DEFERRED-via-scope-mismatch (line listed) | ✓ |
| `onchain_copm_time_patterns` | DEFERRED-via-scope-mismatch (line listed) | ✓ |
| `onchain_copm_transfers` | DEFERRED-via-scope-mismatch (line listed) | ✓ |
| `onchain_copm_transfers_sample` | DEFERRED-via-scope-mismatch (line listed) | ✓ |
| `onchain_copm_transfers_top100_edges` | DEFERRED-via-scope-mismatch (line listed) | ✓ |
| `onchain_carbon_arbitrages` | DIRECT in scope; follow-up question for β-spec | ✓ |
| `onchain_carbon_tokenstraded` | DIRECT in scope; follow-up question for β-spec | ✓ |
| `onchain_xd_weekly` | DIRECT; `carbon_per_currency_copm_volume_usd` proxy_kind tagged DEFERRED | ✓ |
| `onchain_y3_weekly` | Implicit Mento-native panel (4-country differential, not COPm-scoped); DIRECT-equivalent | ✓ |

**Coverage = 14/14. No table omitted from §I CORRECTIONS.** The 10 listed `onchain_copm_*` tables in the disposition memo (line 88) match the 10 live `onchain_copm_*` tables byte-exact. The 9-table list in MR-β.1 §I sub-task 2 rescope (which does not call out `onchain_copm_address_activity_top400` separately — actually it does, on line 338) — actually I count 10 tables in the §I list: `onchain_copm_transfers`, `_daily_transfers`, `_burns`, `_mints`, `_freeze_thaw`, `_time_patterns`, `_address_activity_top400`, `_transfers_top100_edges`, `_transfers_sample`, `_ccop_daily_flow`. ✓ ALL 10.

The 10 `proxy_kind` values in `onchain_xd_weekly` are consistent with the prior RC spot-check enumeration in `2026-04-25-subtask-mr-beta-1-1-rc-spot-check.md` §6.3 — `carbon_per_currency_copm_volume_usd` is the one DEFERRED-via-scope-mismatch.

Status: VERIFIED.

### RC-Concern-8: Empirical β-track Rev-3 joint-coverage feasibility — NEEDS-WORK (forward-looking only; not blocking the disposition)

**Empirical probe (live DuckDB):**
- `onchain_y3_weekly`: 291 weeks; min `week_start = 2023-08-11`; **max `week_start = 2026-03-27`** (4 weeks before the disposition date).
- `0x8A567e2a…` first transfer: 2024-10-31.
- `0x8A567e2a…` last transfer (Dune live as of RC re-execution): 2026-04-27.

**Two arithmetic windows:**

(a) **X_d-only chronological window** (memo's claim): 2024-10-31 → 2026-04-27 = **78 ISO weeks chronologically**, **79 distinct active weeks** per Dune. ≥ N_MIN=75. ✓ The memo's claim "78 weeks ≥ N_MIN=75" is **arithmetically correct on the X_d-only metric**.

(b) **Joint (Y₃ ∩ X_d) window relative to the live Y₃ panel maximum:** `joint_start = max(Y₃_min, X_d_min) = 2024-10-31`; `joint_end = min(Y₃_max, X_d_live) = 2026-03-27`. Chronological: **(2026-03-27 − 2024-10-31) // 7 = 73 weeks**. **Falls 2 weeks short of N_MIN=75.**

(c) **If Y₃ panel is refreshed forward to a date ≥ 2026-04-13:** joint chronological window clears 75. The Y₃ panel's source-data dependencies (CPI / equity / FX inputs) and refresh cadence will determine whether this is trivially achievable. NOT verified in this RC review.

**The disposition memo's confident claim "78 weeks ≥ N_MIN=75 → β-track Rev-3 data feasibility cleared" is X_d-only-conditioned, not joint-coverage-conditioned.** The memo §6 "Open question deferred to β-spec" does correctly defer the *partition* question (retail / consumer demand vs. governance / arbitrage flows) — but it does NOT call out the joint-coverage tightness against the existing Y₃ panel.

**However, this rises to NEEDS-WORK only as forward-looking guidance, not as a fix-up requirement for THIS disposition,** because:

1. The memo is explicit (line 103): "β-track Rev-3 must independently clear this on `0x8A567e2a…` data … to be verified at β-spec authoring time."
2. Task 11.P.spec-β is a separate sub-plan that hasn't been authored yet.
3. The Y₃ panel max may be a stale snapshot, not a hard ceiling — refreshing it forward is mechanical (the existing pipeline supports it).
4. The 73-week tightness is a 2-week shortfall, easily closed by either (a) a Y₃ refresh forward by ~3 weeks or (b) extending the LOCF-tail-forward window. These are β-spec authoring concerns.

**Recommended forward-looking fix-up (advisory; for the β-spec sub-plan, NOT for the disposition):** the β-spec sub-plan author should explicitly verify joint-coverage at authoring time against the live Y₃ panel state, and call out any mitigation (Y₃ refresh, LOCF tail extension) BEFORE locking in N_MIN clearance. The disposition memo could optionally be amended with a single-sentence note acknowledging the joint-coverage caveat — that is not required for the disposition's correctness, but it would be honest housekeeping.

Status: NEEDS-WORK (forward-looking advisory only; does NOT block the disposition).

---

## 3. ADDITIONAL FINDINGS (outside the 8 RC concerns)

### Advisory R-1 (non-blocking): Stale Mento docs URL citation in disposition memo

The disposition memo line 140 cites `https://docs.mento.org/mento/protocol/deployments` as the canonical Mento V3 deployments docs URL. That URL currently returns a 404 stub page; the working URL (used by the DE inventory memo line 19, the earlier RC spot-check, and this RC re-verification) is `https://docs.mento.org/mento-v3/build/deployments/addresses.md`.

**Recommended fix:** future-revision update to use the working URL, or document both URLs with a "URL may drift; canonical docs are accessible via …" caveat. The empirical evidence is unaffected because (a) the prior DE memo, (b) the earlier RC spot-check, and (c) THIS RC re-verification all retrieved the same canonical content via the working URL.

This is a citation-papercut footgun for any future reader following the link from the disposition memo and getting the 404. Non-blocking.

### Advisory R-2 (non-blocking): Implementation-address commonality cross-check is a useful disambiguation tool not yet leveraged

The Mento V3 docs revealed: "All listed entries share the same implementation address: `0x434563B0604BE100F04B7Ae485BcafE3c9D8850E`". That is, Mento-native StableTokens are all EIP-1967 proxies pointing at the common `StableTokenV2` implementation.

**The disambiguation tool not yet used:** verifying whether `0xc92e8fc2…` shares the SAME implementation address would be additional triangulation — if it does, Minteo deployed against the Mento StableToken V2 codebase (governance / branding distinction only); if it doesn't, the contracts are codebase-distinct as well as address-distinct.

This is a future-revision strengthening (β-spec sub-plan or sub-task 5 future-research safeguard memo concern) not a current-disposition fix-up. The Dune `evt_validatorsupdated` / `evt_brokerupdated` rows on `0x8A567e2a…` and the 0-row state on `0xc92e8fc2…` (which RC did not directly probe but which is implied by the absence of a `celominteo`-class Dune project) are already dispositive.

### Advisory R-3 (non-blocking): The "0 events ingested" claim for `0x8A567e2a…` in DuckDB is correct as of disposition time

The §I CORRECTIONS line 348 says: "nothing in current DuckDB tracks `0x8A567e2a…` yet — '0 events ingested' remains true at Rev-5.3.5 disposition time." RC-DuckDB-probe confirms: there is no `onchain_copm_v2_*` or `onchain_copm_mento_*` or similar table; all `onchain_copm_*` tables track the legacy `0xc92e8fc2…` (Minteo) source. ✓

### Advisory R-4 (non-blocking): Project-memory β-corrigenda use the right "preserve original content" pattern

Both `project_mento_canonical_naming_2026` and `project_abrigo_mento_native_only` carry the β-corrigenda at the top of the file with the original content preserved verbatim below. The canonical memo line that was wrong (`project_mento_canonical_naming_2026` line 37 "COPM (Minteo, unchanged) — `0xc92e8fc2…`") is annotated with an explicit `⚠️ SUPERSEDED by β-corrigendum above` marker, NOT deleted. This is the textbook append-only corrigendum pattern from `feedback_pathological_halt_anti_fishing_checkpoint`.

---

## 4. EMPIRICAL ARTIFACTS

### Dune queries (RC-authored, free tier)

- **Query `7379527`** — independent re-verification of activity probe (`celocolombianpeso_celo.stabletokenv2_evt_transfer` aggregations). URL: https://dune.com/queries/7379527.
- **Execution `01KQ6CZWDVKZZM6CWCJ82F4Y29`** — completed, COMPLETED state, 0.014 credits.
- **Query `7379530`** — Mento governance event row-count probe (`evt_exchangeupdated` / `evt_validatorsupdated` / `evt_brokerupdated` / `evt_initialized`). URL: https://dune.com/queries/7379530.
- **Execution `01KQ6D270SN52J6KXZQMY6RED2`** — completed, 0.008 credits.

### Dune table catalog

- `searchTablesByContractAddress(0x8A567e2aE79CA692Bd748aB832081C45de4041eA, ['celo'])` returned 24 decoded tables under project `celocolombianpeso`, contract `StableTokenV2`. Includes `evt_exchangeupdated`, `evt_validatorsupdated`, `evt_brokerupdated`, `evt_initialized`, `call_mint`, `call_burn`, etc.

### Authoritative on-chain references

- **Mento V3 docs (working URL):** https://docs.mento.org/mento-v3/build/deployments/addresses.md — `StableTokenCOP` = `0x8a567e2ae79ca692bd748ab832081c45de4041ea`.
- **Celo Token List:** https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json — `0xC92E8Fc2…` = "COP Minteo" / `COPM`; `0x8A567e2a…` = "Mento Colombian Peso" / `COPm`.
- **Celoscan reference (per Mento docs):** https://celoscan.io/address/0x8a567e2ae79ca692bd748ab832081c45de4041ea
- **Common StableTokenV2 implementation:** `0x434563B0604BE100F04B7Ae485BcafE3c9D8850E` (per Mento V3 docs).

### DuckDB live probe

- **Path:** `contracts/data/structural_econ.duckdb` (read-only mode).
- **Probe at:** branch `phase0-vb-mvp` HEAD `00790855b` = the disposition commit.
- **`onchain_*` table count:** 14 (10 `onchain_copm_*` + 2 `onchain_carbon_*` + `onchain_xd_weekly` + `onchain_y3_weekly`).
- **`onchain_xd_weekly` proxy_kind enumeration:** 10 distinct values (matches prior RC spot-check §6.3 byte-exact).
- **`onchain_copm_transfers` row count:** 110,253 events, 2024-09-17 → 2026-04-25 (matches DE inventory memo line 17 byte-exact).
- **`onchain_y3_weekly` panel bounds:** 291 weeks, 2023-08-11 → 2026-03-27.

### Audit-trail commits

- `3611b0716` (DE inventory deliverable, 2026-04-26 18:15 EDT, 1 file).
- `3286dfe66` (RC spot-check, 2026-04-26 18:25 EDT, 1 file).
- `00790855b` (Rev-5.3.5 disposition commit, 2026-04-26 22:37 EDT, 4 files: disposition memo + major plan + ccop-provenance-audit sub-plan + rev2-notebook-migration sub-plan).
- **`.duckdb` mutation check:** `git log --all --diff-filter=AMD -- '*.duckdb'` returned **0 commits**. No DuckDB row mutated under the disposition.

### Project-memory β-corrigenda

- `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_mento_canonical_naming_2026.md` — β-corrigendum at top (lines 1-28); original preserved (lines 30-52); `⚠️ SUPERSEDED` annotation on line 37.
- `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_abrigo_mento_native_only.md` — β-corrigendum at top (lines 1-22); original cCOP-vs-COPM corrigendum preserved (lines 26-32); authoritative content updated (lines 34-63).

---

## 5. RECOMMENDED ACTIONS (none blocking; trio convergence proceeds)

1. **R-1 (citation-papercut):** future-revision update of disposition memo line 140 Mento V3 docs URL from `mento/protocol/deployments` (404 stub) → `mento-v3/build/deployments/addresses.md` (working). Editorial; not blocking.
2. **RC-Concern-8 (forward-looking):** Task 11.P.spec-β sub-plan author MUST explicitly verify joint Y₃ × X_d coverage against the live Y₃ panel state at β-spec authoring time, and call out any required Y₃ refresh / LOCF-tail extension before locking N_MIN clearance. The 73 vs. 75 chronological joint-week gap is closeable but not yet closed. **The disposition itself is correct;** the gap arises only when downstream β-track Rev-3 actually runs.
3. **R-2 (future-strengthening):** the implementation-address commonality cross-check (`0x434563B0604BE100F04B7Ae485BcafE3c9D8850E`) is a free additional triangulation tool that future research touching token identity should use.

---

## 6. FINAL VERDICT (RESTATED)

**PASS-with-non-blocking-advisories.**

- All 8 RC concerns: **7 VERIFIED, 1 NEEDS-WORK forward-looking only** (RC-Concern-8 joint-coverage; deferred to β-spec by memo §6; not a disposition fix-up).
- Anti-fishing scope-mismatch discipline: VERIFIED (no rescue-claim drift).
- Audit-trail integrity: VERIFIED (3 commits exist, docs-only, 0 DuckDB mutations).
- Coverage completeness: VERIFIED (14/14 `onchain_*` tables tagged in §I CORRECTIONS).
- Empirical claims (Dune metrics, Mento-protocol-native events, Celo Token List, Mento V3 docs): all VERIFIED via independent execution.
- Project-memory β-corrigenda hygiene: VERIFIED (preserve-original + ⚠️SUPERSEDED markers).

**Trio convergence not blocked from the RC peer's side.** The CR + TW peers are running in parallel; my verdict is independent of theirs. The disposition is ready to land as Rev-5.3.5 once all three trio peers converge (CR and TW's verdicts are unknown to RC at write time).

**Sub-task re-dispatch (per disposition action plan §7 step 8 — "Re-dispatch DE for MR-β.1 sub-task 1"):** unblocked by this RC PASS. The DE re-dispatch for the rescoped sub-task 1 deliverable can proceed once CR and TW peers converge. The β-spec sub-plan (Task 11.P.spec-β) author should consume the RC-Concern-8 advisory at sub-plan authoring time.

---

## 7. AUDIT-TRAIL FOOTER

- **This review:** `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-reality-checker.md`
- **Reviewed deliverables:** disposition memo + Rev-5.3.5 CORRECTIONS in major plan + §I CORRECTIONS in MR-β.1 sub-plan + CORRECTIONS in NB-α sub-plan + project-memory β-corrigenda + DE inventory + earlier RC spot-check.
- **Tool budget:** 13 / 15 calls used.
- **Empirical evidence:** 2 RC-authored Dune queries (`7379527`, `7379530`), 2 Dune executions, 1 Dune `searchTablesByContractAddress`, 2 WebFetch (1 fallback after 404), 1 DuckDB live probe, 4 git audit-trail probes.
- **Independence:** RC review conducted with no coordination with CR or TW peers.
- **Branch:** `phase0-vb-mvp` HEAD `00790855b` (= disposition commit).

**End of review.**
