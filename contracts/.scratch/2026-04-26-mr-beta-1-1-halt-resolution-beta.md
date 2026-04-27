# MR-β.1 Sub-task 1 HALT-VERIFY — Disposition Memo (β resolution)

**Date:** 2026-04-26
**Author:** foreground orchestrator
**Trigger:** DE deliverable `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` at commit `3611b0716` fired HALT-VERIFY GATE on COPM canonical address.
**RC corroboration:** `contracts/.scratch/2026-04-25-subtask-mr-beta-1-1-rc-spot-check.md` at commit `3286dfe66` returned **PASS** with non-binding β-advisory.
**User disposition:** **β** — adopt `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` as canonical Mento-native `StableTokenCOP`; classify `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` as **Minteo-fintech (out of Mento-native scope)**.

---

## 1. HALT trigger summary

The DE's MR-β.1 sub-task 1 inventory surfaced two competing canonical Colombian-peso addresses on Celo:

| Field | `0xc92e8fc2…` | `0x8A567e2a…` |
|---|---|---|
| Live DuckDB events ingested | 110,253 (`onchain_copm_transfers`) | 0 |
| Celo Token List (chainId 42220) | "COP Minteo" / **COPM** | "Mento Colombian Peso" / **COPm** |
| Mento V3 deployments docs | not listed as `StableTokenCOP` | **canonical `StableTokenCOP`** (verbatim) |
| `project_mento_canonical_naming_2026` (pre-disposition) | claimed Mento-native COPM | not mentioned |

Memory said one thing; two independent canonical sources (Celo Token List + Mento V3 docs) said another. The DE correctly surfaced the gate rather than silently overriding.

## 2. RC PASS + β-advisory (commit `3286dfe66`)

The RC spot-check independently fetched both Celo Token List and Mento V3 docs and **confirmed** the contradiction is real and load-bearing. Empirical balance leaned β: `0x8A567e2a…` is the address Mento V3 documentation explicitly identifies as `StableTokenCOP`; `0xc92e8fc2…` is independently labeled "COP Minteo" by the Celo Token List.

RC also surfaced four non-blocking advisories for downstream sub-tasks 2 + 3 (ingester filter audit, time-gating analysis if β is adopted, Celoscan-403 bypass strategy for the registry-lock doc, cCOP-attribution re-examination depending on resolution path).

## 3. Empirical β-feasibility probe (Dune)

Before locking in β, the orchestrator ran two corroborating Dune queries:

### 3.1 Decoded-table catalog (`searchTablesByContractAddress`)

`0x8A567e2a…` is decoded under Dune project name **`celocolombianpeso`** with contract name **`StableTokenV2`**, exposing 24 decoded tables including:

- `celocolombianpeso_celo.stabletokenv2_evt_transfer` (Transfer events)
- `celocolombianpeso_celo.stabletokenv2_call_mint` (Mint calls)
- `celocolombianpeso_celo.stabletokenv2_call_burn` (Burn calls)
- `celocolombianpeso_celo.stabletokenv2_evt_exchangeupdated` (Mento exchange-update events)
- `celocolombianpeso_celo.stabletokenv2_evt_validatorsupdated` (Mento validator-update events)

The presence of `evt_exchangeupdated` and `evt_validatorsupdated` events (Mento-protocol-specific governance events) is by itself dispositive: this contract is Mento-protocol-native, not a third-party fintech token.

### 3.2 Activity probe (Dune query 7378788, free tier, 0.012 credits)

Run against `celocolombianpeso_celo.stabletokenv2_evt_transfer`:

| Metric | Value |
|---|---|
| Total transfers | **285,390** |
| Distinct senders | 5,015 |
| Distinct receivers | 16,918 |
| First transfer | **2024-10-31 16:35:48 UTC** |
| Last transfer | **2026-04-26 21:12:59 UTC** (live as of disposition time) |
| Distinct weeks with activity | **78** |
| Distinct days with activity | 534 |

**β-track Rev-3 data feasibility cleared.** 78 weeks ≥ N_MIN=75 (anti-fishing invariant). Volume is **2.6× larger** than the `0xc92e8fc2…` series we ingested for Rev-2 (285K vs. 110K transfers). The Mento Reserve / governance events are on this address, not the one we ingested.

## 4. Cascading implications under β

### 4.1 Rev-2 published estimates

Rev-2 published estimates (β̂ = −2.7987e−8, n = 76, T3b FAIL, MDES_FORMULATION_HASH `4940360dcd2987…cefa`, decision_hash `6a5f9d1b05c1…443c`) are **byte-exact immutable** per Rev-5.3.x anti-fishing invariants. They remain in the audit trail unchanged.

What changes is the **interpretation**. Rev-2 was measuring `0xc92e8fc2…` events — which under β is Minteo-fintech (out of Mento-native scope per `project_abrigo_mento_native_only`). Rev-2 therefore closes as **scope-mismatch**, NOT as "Mento-hedge-thesis-tested-and-failed." The Rev-2 disposition memo (`contracts/.scratch/2026-04-25-task110-rev2-gate-fail-disposition.md`) gate-FAIL framing is superseded by this scope-mismatch framing.

This re-explains the three Rev-2 anomalies cleanly:

- **Sign-flip (β̂ < 0)** — consistent with Minteo-fintech being a payments / B2B-API rail rather than Mento-basket hedge volume.
- **ρ(X_d, fed_funds) = −0.614 confounder** — consistent with Minteo's user base being FX-payments-driven (sensitive to US monetary cycle via remittance corridors), not macro-hedge-driven.
- **T1 REJECTS predictive-not-structural** — consistent with Minteo activity being a payments-cycle predictor, not a structural hedge-demand signal.

### 4.2 β-track Rev-3 ingestion plumbing

β-track Rev-3 needs new ingestion plumbing pointed at `0x8A567e2a…`. The existing scripts (`econ_pipeline.py`, `econ_schema.py`, `query_api.py`) reference the old address; they are **NOT mutated** under MR-β.1 (per §B-2 invariant: no schema migrations under this sub-plan). The β-spec sub-plan (Task 11.P.spec-β) and β-execution sub-plan (Task 11.P.exec-β) are the appropriate venues for new ingestion plumbing — those sub-plans have not yet been authored on disk and will be authored post-MR-β.1 convergence.

### 4.3 α-track NB-α notebook migration

The NB-α 31 dispatch units (Rev-2 notebook migration) carry forward unchanged for the **byte-exact migration of Rev-2 numbers**. What changes is the **interpretation cells**: every `why-markdown / code-cell / interpretation-markdown` trio under NB-α must now frame Rev-2 results as a **scope-mismatch close-out**, not as "Mento-hedge-thesis-tested-and-failed."

Concretely: the NB-α sub-plan's per-trio acceptance criteria for interpretation cells need a CORRECTIONS amendment under the same Rev-5.3.5 disposition. Authoring scope: minimal — interpretation framing only; numbers, panels, and gate verdicts stay byte-exact.

### 4.4 Existing DuckDB tables on `0xc92e8fc2…`

Every `onchain_*` table sourced from `0xc92e8fc2…` events (`onchain_copm_transfers`, `onchain_copm_daily_transfers`, `onchain_copm_burns`, `onchain_copm_mints`, `onchain_copm_freeze_thaw`, `onchain_copm_time_patterns`, `onchain_copm_address_activity_top400`, `onchain_copm_transfers_top100_edges`, `onchain_copm_transfers_sample`, `onchain_copm_ccop_daily_flow`, plus the `carbon_per_currency_copm_volume_usd` proxy) is now classified as **Minteo-scope, deferred from Mento-native β-track**. They are NOT dropped, renamed, or migrated under MR-β.1. Sub-task 2's coverage classification scheme (DIRECT / DERIVATIVE / DEFERRED) absorbs the change: these tables move from DIRECT-Mento-native (the Rev-5.3.4 framing) to **DEFERRED-via-scope-mismatch** (the Rev-5.3.5 framing).

### 4.5 Project memory amendments

Two memory files require corrigenda:

- `project_mento_canonical_naming_2026` — COPM address corrigendum: `0x8A567e2a…` (Mento V2 `StableTokenCOP`) is the canonical Mento-native COPm address; `0xc92e8fc2…` is Minteo-fintech (third-party, out of Mento-native scope).
- `project_abrigo_mento_native_only` — already carries the cCOP-vs-COPM corrigendum; needs **additional corrigendum** flipping the in-scope COPM address from `0xc92e8fc2…` to `0x8A567e2a…` and explicitly listing `0xc92e8fc2…` as out-of-scope Minteo-fintech.

Both amendments are append-only corrigenda per `feedback_pathological_halt_anti_fishing_checkpoint`'s anti-fishing-on-memory-edits discipline. The originals are preserved with corrigendum overlay; nothing is silently rewritten.

## 5. Anti-fishing-invariant integrity

No Rev-5.3.x anti-fishing invariant is relaxed by this disposition:

- N_MIN = 75 unchanged. β-track Rev-3 must independently clear this on `0x8A567e2a…` data (78 weeks already on-chain → likely cleared, but to be verified at β-spec authoring time).
- POWER_MIN = 0.80 unchanged.
- MDES_SD = 0.40 unchanged.
- MDES_FORMULATION_HASH = `4940360dcd2987…cefa` unchanged.
- decision_hash = `6a5f9d1b05c1…443c` unchanged (it pertains to Rev-2's published estimates, which remain byte-exact).
- Pre-committed 14-row resolution matrix for Rev-2 unchanged.

The disposition is a **scope correction**, not a threshold relaxation. Rev-2's gate FAIL is replaced by Rev-2's scope-mismatch close-out; β-track Rev-3 starts fresh under all the same anti-fishing thresholds against the correct on-chain address.

## 6. Open question deferred to β-spec

**Whether `0x8A567e2a…` activity represents retail / consumer demand for Mento-native COPm versus Mento basket internal flows / arbitrage / governance.** This question is the structural-econometric identification challenge that β-spec must address. The 285K-transfer / 5K-sender / 16K-receiver headcount is necessary but not sufficient; a DIRECT vs ARB-vs-USER partition (analogous to `project_carbon_user_arb_partition_rule`) will be required at β-spec authoring time. Out of scope for this disposition; in scope for Task 11.P.spec-β.

## 7. Disposition action plan

1. **Write β-resolution evidence memo** (this file). ✓
2. **Amend project memory** — `project_mento_canonical_naming_2026` and `project_abrigo_mento_native_only` corrigenda.
3. **Author Rev-5.3.5 CORRECTIONS block** in major plan documenting β disposition + cascade.
4. **Author CORRECTIONS block in MR-β.1 sub-plan** reflecting sub-task 1 / 2 / 3 rescopes under β:
   - Sub-task 1 deliverable now records BOTH addresses (0x8A567e2a as in-scope Mento-native, 0xc92e8fc2 as out-of-scope Minteo with audit-trail preservation).
   - Sub-task 2 every `onchain_*` table on `0xc92e8fc2…` tagged DEFERRED-via-scope-mismatch.
   - Sub-task 3 registry scopes only `0x8A567e2a…` as canonical Mento-native COPm; documents `0xc92e8fc2…` in an explicit "out-of-scope third-party tokens" appendix section.
5. **Author NB-α sub-plan CORRECTIONS block** for interpretation-framing rescope (numbers byte-exact; framing → scope-mismatch).
6. **Commit disposition** as atomic commit.
7. **Dispatch CR + RC + TW 3-way review** on the disposition per `feedback_pathological_halt_anti_fishing_checkpoint`.
8. **Re-dispatch DE for MR-β.1 sub-task 1** under the rescoped framing (post-3-way-review convergence).

## 8. References

- DE deliverable: `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` (commit `3611b0716`)
- RC spot-check: `contracts/.scratch/2026-04-25-subtask-mr-beta-1-1-rc-spot-check.md` (commit `3286dfe66`)
- Rev-2 disposition memo: `contracts/.scratch/2026-04-25-task110-rev2-gate-fail-disposition.md`
- MR-β.1 sub-plan: `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md`
- NB-α sub-plan: `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md`
- Major plan: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`
- Dune query 7378788 (β-feasibility probe, ~0.012 credits free-tier)
- Dune project: `celocolombianpeso` (decoded `StableTokenV2` contract, 24 tables)
- Mento V3 docs: https://docs.mento.org/mento/protocol/deployments
- Celo Token List (chainId 42220): https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json
