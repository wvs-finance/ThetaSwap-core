# X_d Strategic Re-evaluation — Rev-5.3.7 Option A Disposition

**Date:** 2026-04-27
**Author:** foreground orchestrator
**Trigger:** User-surfaced HALT-VERIFY query 2026-04-27 mid-NB-α sub-task 12 dispatch:
1. Layer 1 (Rev-5.3.5) — `0xc92e8fc2…` Minteo vs Mento-native COPm `0x8A567e2a…` (resolved 2026-04-26)
2. Layer 2 (Rev-5.3.6) — BancorArbitrage V1-only partition rule; broken post-2025-07-01 (V2 successor not in whitelist)
3. **Layer 3 (Rev-5.3.7) — Carbon DeFi has NO protocol-level integration with Mento; X_d signal is third-party DEX activity, not Mento Reserve user demand**
**User disposition:** **Option A — close NB-α at sub-task 12; pivot β-track Rev-3 spec to Mento-Broker-native X_d.**

---

## 1. Empirical re-grounding

Mento V3 deployment manifest (https://docs.mento.org/mento-v3/build/deployments/addresses) was independently fetched. The complete contract list on Celo mainnet contains:

**V2 (legacy, still active):**
- Broker `0x777A8255cA72412f0d706dc03C9D1987306B4CaD` (THE Mento user-demand entry point)
- BiPoolManager `0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901`
- Reserve `0x9380fA34Fd9e4Fd14c06305fd7B6199089eD4eb9`
- StableTokens (12 currencies including StableTokenCOP `0x8a567e2a…`)
- Breakers, oracles, governance, MENTO/veMENTO

**V3 (new architecture):**
- Router `0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6`
- FPMMFactory `0xa849b475FE5a4B5C9C3280152c7a1945b907613b`
- ReserveV2 `0x4255Cf38e51516766180b33122029A88Cb853806`
- FPMM pools (USDT/USDm, USDC/USDm, axlUSDC/USDm, GBPm/USDm)

**Critical absence**: NO `CarbonAdapter`, NO `BancorBroker`, NO `DEXIntegration` contract. Mento is a closed system (Reserve + Broker + Pools).

## 2. Empirical confirmation that X_d measures the wrong signal

Dune query `7382711` (free-tier; 0.124 credits) compared the canonical Mento user-demand signal to the Carbon `tokenstraded` signal we were measuring as X_d:

| Signal | Lifetime events | Distinct traders | Events in Rev-2 panel window (2024-09-27 → 2026-03-13) | First seen |
|---|---|---|---|---|
| **Mento Broker V2 Swap (Mento-native)** | **6,161,979** | **383,303** | **4,226,345** | 2023-04-07 |
| Carbon `tokenstraded` (current X_d source) | 2,231,212 | 147 | 1,785,588 | 2024-07-25 |

**Mento Broker has 2,604× more distinct traders than Carbon for the same window.** The Mento-native demand signal exists, is large, is decoded on Dune (`mento_celo.broker_evt_swap`), and has been measured against `mento_celo.broker_*` decoded tables since 2023.

## 3. The actual actor architecture

There is no Carbon ↔ Mento integration at the protocol level. **The Carbon-Mento token-pair activity is third-party-DEX hosting, not protocol integration.**

Empirical breakdown of the X_d signal under the V1-only partition rule:

| Pre/Post 2025-07-01 | Partition | Event count | Distinct traders | Interpretation |
|---|---|---|---|---|
| Pre-July (V1 alive) | arb | 929,614 | 1 (V1 only) | **Bancor's own arb router (~72% of pre-July boundary volume)** |
| Pre-July | user | 368,389 | 68 | Other arb bots + small retail |
| Post-July (V1 dead) | 'user' (broken) | 669,872 | 80 | **524,104 (78%) is V2 BancorArbitrageV2 successor `0x20216f30…` misclassified as user** |
| Post-July | arb | 0 | 0 | Empty (V1 dead, V2 not in whitelist) |

**Bancor protocol** (the parent of Carbon DeFi) deployed CarbonController on Celo 2024-07-25 and ran BancorArbitrage V1 + V2 routers extracting value from cross-DEX price misalignment between Carbon's Mento-token pools and the Mento Broker (and other Mento-token markets). Mento was never a counterparty; Mento Reserve never minted/burned in response to a Carbon trade.

**Concretely**: Rev-2's β̂ = −2.7987e−8 measures the relationship between Bancor's own arbitrage volume and the inequality-differential Y_3. There is no theoretical reason to expect any structural relationship; the gate FAIL is exactly what one would expect from regressing Y_3 on a third-party-DEX-arb-volume signal.

## 4. What stays byte-exact-immutable under Option A

- Rev-2 published estimates: β̂ = −2.7987050503705652e−08; HAC(4) SE = 1.4234226026833985e−08; t-stat = −1.9661799981920483; two-sided p = 0.04927782209941108; one-sided 90% lower bound = −4.6206859818053154e−08; n = 76; T3b FAIL.
- All 12 NB-α commits (sub-tasks 1-12; HEAD `2b46ef0f6`).
- N_MIN = 75; POWER_MIN = 0.80; MDES_SD = 0.40.
- MDES_FORMULATION_HASH = `4940360dcd2987…cefa` (runtime-verified at NB2 §1).
- Rev-4 decision_hash = `6a5f9d1b05c1…443c`.
- Rev-2 14-row resolution-matrix scope.
- All `onchain_*` DuckDB tables (consume-only invariant).
- All sub-task RC spot-checks + the trio review file at HEAD.

## 5. What changes under Option A

### NB-α termination

NB-α terminates at the closer trio (appended after sub-task 12's HAC(12) cells). Sub-tasks 13-31 (NB2 §5/§6/§7 + NB3 + README) are NOT authored. The notebooks become audit-trail-only artifacts: a complete record of byte-exact reproduction of Rev-5.3.2 published numbers under the (now-known-wrong-signal) X_d, plus a closer trio documenting the compound 3-layer scope-mismatch.

NB-α deliverable count: 12 sub-tasks + closer trio per notebook = "13 sub-tasks plus closer" rather than 31.

### Project memory amendments

- `project_carbon_user_arb_partition_rule` — Rev-5.3.6 β-corrigendum: V1-only rule; broken post-2025-07-01; V2 successor `0x20216f30…` not in whitelist.
- `project_carbon_defi_attribution_celo` — Rev-5.3.6 β-corrigendum: add BancorArbitrageV2 to roster with V1→V2 transition timestamp.
- NEW memory `project_no_mento_carbon_protocol_integration` — Rev-5.3.7 finding: Mento V3 deployment manifest has zero references to Carbon; Carbon is third-party DEX hosting Mento basket tokens as standard ERC-20s; not authorized integration.

### Major plan + sub-plan + registry spec corrigenda

- Major plan: append Rev-5.3.7 CORRECTIONS block at file end documenting Option A pivot.
- MR-β.1 sub-plan: append §J CORRECTIONS noting the registry spec doc receives a §8.2 appendix entry for BancorArbitrageV2 (V1→V2 successor; out-of-Mento-native-scope).
- NB-α sub-plan: append CORRECTIONS noting termination at sub-task 12 + closer; sub-tasks 13-31 superseded.
- Registry spec doc: append §8.2 entry for BancorArbitrageV2 (audit-trail preservation; out-of-Mento-native-scope).

### β-track Rev-3 spec (Task 11.P.spec-β; deferred — to be authored)

Pivots X_d to Mento Broker V2 + V3:
- **Primary**: `mento_celo.broker_evt_swap` events on Broker `0x777A8255…` aggregated weekly (Friday anchor); partitioned by direction (mint vs redeem; in vs out) and basket currency.
- **Secondary**: Mento V3 FPMM pool swap events on the 4 deployed pools (USDT/USDm, USDC/USDm, axlUSDC/USDm, GBPm/USDm).
- **Diagnostic**: StableToken `Transfer` events with `from = 0x0` (mint) / `to = 0x0` (burn) for issuance/redemption flow per currency.
- **Partition discipline**: identify and exclude any successor arb routers analogous to BancorArbitrage V1+V2 by triangulating `searchTablesByContractAddress` for any contract decoded as `*ArbitrageExecuted` event-emitter.
- **N feasibility**: 4,226,345 events in Rev-2 panel window; 383,303 distinct traders; weekly aggregation will yield at least 76 weeks coverage on the same window AND likely much earlier history (Broker first event 2023-04-07, ~80 weeks pre-window available for windowed sensitivity).

### PR #74 close-out (NOT merge)

PR #74 at upstream `wvs-finance/ThetaSwap-core` (head: `phase0-vb-mvp`; title: "feat(remittance): Phase-A.0 remittance-surprise → TRM-RV pipeline (WIP, do not merge)") **will be CLOSED, NOT merged.** The X_d signal is scope-mismatched 3 layers deep; merging would introduce wrong-signal analytical infrastructure to upstream. Comment posted on PR with closer-commit reference + 3-layer scope-mismatch summary + pointer to forthcoming β-track Rev-3 spec.

This honors the user's explicit gate "push and merge PR #74. Only WHEN THAT TASK BUNDLE COMPLETES" by recognizing that the bundle did NOT successfully complete (it close-out as scope-mismatched, not analytically successful). Closing the PR is the honest disposition; merging would propagate Rev-5.3.5/6/7 contamination upstream.

## 6. Why Option A is the right pivot

| Option | Cost | Benefit | Anti-fishing risk |
|---|---|---|---|
| **A — Pivot to Mento-Broker-native X_d (selected)** | 30 min closer + Rev-5.3.7 corrigendum bundle; skips 19 NB-α sub-tasks | Pivots to actual Mento-native signal with 383K-trader retail base | LOW — preserves byte-exact-immutable Rev-2 audit trail; pivots β-track Rev-3 to correct signal |
| B — Pivot product thesis itself (re-ground inequality-hedge) | Brainstorming reset; multi-week delay | Most analytically honest if Mento Broker users aren't working-class | MEDIUM — risks reopening pre-Phase-A.0 scope decisions |
| C — Two-product split (Carbon basis-spread + Mento Broker macro-hedge) | Doubles scope | Captures both signals as separate products | HIGH — pursuing 2 products simultaneously is a Phase-A.0 anti-pattern |
| D — Continue NB-α byte-exact migration despite wrong-signal finding | 19 more dispatch cycles of effort | Complete audit trail | HIGH — burns effort migrating wrong-signal numbers; dilutes future analytical work |

Option A has the lowest cost AND lowest anti-fishing risk while pivoting to the empirically-correct signal. β-track Rev-3 spec authoring (Task 11.P.spec-β) becomes the next major deliverable.

## 7. Anti-fishing-invariant integrity preserved

No invariant is relaxed:
- N_MIN = 75 unchanged.
- POWER_MIN = 0.80 unchanged.
- MDES_SD = 0.40 unchanged.
- MDES_FORMULATION_HASH unchanged + runtime-verified.
- decision_hash unchanged.
- Rev-2 14-row resolution-matrix unchanged byte-exact.
- 0 DuckDB row mutations under this disposition.
- All prior NB-α commits preserved byte-exact (no commit reverted).
- Rev-2 published estimates byte-exact-immutable (audit-trail role only).

## 8. Empirical evidence trail

### Rev-5.3.7-relevant Dune queries

| Query ID | Description | Credits | Findings |
|---|---|---|---|
| `7382711` | Mento Broker V2 vs Carbon `tokenstraded` activity comparison | 0.124 | Broker 6.16M / 383K traders; Carbon 2.23M / 147 traders |

### Mento V3 deployment manifest (2026-04-27 fetched)

Working URL: https://docs.mento.org/mento-v3/build/deployments/addresses.md

Independent verification: zero `CarbonAdapter` / `BancorBroker` / `DEXIntegration` references; Mento is a closed Reserve+Broker+Pools system.

### Decoded-table verification

| Address | Dune project | Contract | Status |
|---|---|---|---|
| `0x777A8255…` | `mento` | Broker | 20 decoded tables; `broker_evt_swap` is the canonical Mento user-demand event |
| `0x22d9db95E6…` | `mento` | BiPoolManager | 29 decoded tables; V2 pool registry |
| `0x4861840C2E…` | (not decoded) | Router V3 | 0 decoded tables (V3 too new) |

## 9. References

- Disposition memo (this file): `contracts/.scratch/2026-04-27-x-d-strategic-re-evaluation-disposition.md`
- Rev-5.3.5 disposition (Layer 1): `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md`
- Rev-5.3.6 disposition (Layer 2): `contracts/.scratch/2026-04-27-x-d-partition-rule-staleness-disposition-beta.md`
- Major plan: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (Rev-5.3.7 CORRECTIONS to be appended at file end)
- NB-α sub-plan: `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md` (CORRECTIONS to be appended noting termination)
- MR-β.1 sub-plan: `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` (§J CORRECTIONS for V2 registry appendix)
- Registry spec: `contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md` (§8.2 BancorArbitrageV2 appendix entry)
- X_d formula source: `contracts/scripts/econ_pipeline.py` lines 2711-2799 + `contracts/data/carbon_celo/README.md`
- NB-α scaffolding: `contracts/notebooks/abrigo_y3_x_d/01_data_eda.ipynb` + `02_estimation.ipynb` + `estimates/{gate_verdict,panel_fingerprint,outlier_diagnostics,primary_estimate,bootstrap_recon,row11_student_t,row12_hac12}.json` + `figures/{x_d_distribution,x_d_diurnal_utc,xd_y3_scatter}.png`
- Mento V3 deployment manifest: https://docs.mento.org/mento-v3/build/deployments/addresses.md
- PR #74 (TO BE CLOSED, NOT merged): https://github.com/wvs-finance/ThetaSwap-core/pull/74
- β-track Rev-3 spec sub-plan (TO BE AUTHORED): `contracts/docs/superpowers/sub-plans/2026-04-25-beta-spec.md`
