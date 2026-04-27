# Mento-Native On-Chain Address Registry

**Date:** 2026-04-26.
**Authoring revision:** Rev-5.3.5 β-rescoped framing.
**Status:** Authored under MR-β.1 sub-task 3 dispatch; awaiting convergent CR + RC + Senior-Developer 3-way review per `feedback_implementation_review_agents`.
**Sub-plan anchor:** `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` — §C sub-task 3 + §I sub-task 3 rescope.
**Major-plan anchor:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` — Rev-5.3.5 CORRECTIONS block (file end), Rev-5.3.4 CORRIGENDUM block, and Rev-5.3.3 CORRECTIONS block.

---

## §1 — Purpose, scope, and immutability invariant

### §1.1 — Purpose

This document is the canonical reference for every on-chain contract address the Abrigo project consumes from the Mento-native stablecoin family on Celo (chainId 42220). It is the post-converge byte-exact-immutable source-of-truth for token-identity / address-provenance: every downstream β-track and α-track artifact that names a Mento-native token MUST cross-check against this registry before propagating an address into specs, plans, code, or project memory.

### §1.2 — Mento-native-only scope

Per `project_abrigo_mento_native_only` (Rev-5.3.5 β-corrigendum extension), the Abrigo project's stablecoin scope is **Mento-protocol-native ONLY**. The following tokens are explicitly **OUT of scope** for the per-token registry body in §3:

- **COPM-Minteo** at `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606` (Minteo-fintech "COP Minteo" per Celo Token List). Preserved in the audit-trail appendix at §8 ONLY; not enumerated as an in-scope Mento-native token. The Rev-2 X_d ingestion pointed at this address; Rev-2 closes scope-mismatch under the Rev-5.3.5 β-disposition.
- All non-Mento third-party stablecoins on Celo (e.g., bridged USDT / USDC, fintech-issued stablecoins).
- All non-Mento Celo tokens not part of the Mento basket (with the narrow exception of basket-counter-side liquidity surfaced through `onchain_carbon_*` — those are Carbon DeFi MM platform addresses, not Mento-native tokens, and are documented in the §4 DuckDB cross-reference table at the platform level, not as registry entries).
- A separately-named "cCOP" token if it exists on Celo: as of Rev-5.3.5 β-disposition empirical verification (sub-task 1 §β-rescope.1 entry 1, Dune queries 7378788/7379527/7379530), the canonical Mento-native Colombian-peso token is **COPm at `0x8A567e2aE79CA692Bd748aB832081C45de4041eA`** (lowercase final-m); a separately-named "cCOP" token at a distinct Celo address is **not** the Mento-native COPM under this registry.

### §1.3 — Immutability invariant (post-converge)

This registry is byte-exact-immutable post-converge. The convergent CR + RC + Senior-Developer 3-way review per `feedback_implementation_review_agents` is the single quality gate. Once the review trio converges:

- **No in-place edits to existing per-token entries.** Every field in §3.1 through §3.6 (and the §8 out-of-scope appendix entry) is locked at the byte level. Future typo / formatting corrections that *would* land as in-place edits land instead as a new appendix section under a clearly-labeled CORRIGENDUM heading.
- **Future address additions land as new appendix sections.** When a new Mento-native token is deployed (e.g., a future Mento-stablecoin currency expansion), the new token's registry entry lands as a new appendix section keyed by date + Rev-anchor (e.g., "§N — COP-x added under Rev-5.3.X CORRIGENDUM"); never as an edit to §3.
- **Total supply field is deliberately omitted** from every per-token section. Per RC R-3 disposition (sub-plan §H R-3 resolution), supply moves over time and would conflict with the byte-exact-immutability invariant. Auditors and downstream consumers needing live circulating supply MUST query DuckDB / Celoscan / Dune at consumption time. The registry is a token-identity / address-provenance artifact, **not a circulating-supply dashboard**.

The §B-1 / §B-2 anti-fishing invariants from the sub-plan are preserved through this registry: no DuckDB row mutations, no schema migrations, no table renames. All observations in §4 (DuckDB cross-reference) and §5 (`proxy_kind` enumeration) are annotation-only.

---

## §2 — Authoritative provenance triangulation procedure

Per Rev-5.3.5 β-disposition (sub-plan §I CORRECTIONS), every Mento-native address in §3 was triangulated against the following four authorities. Future research that touches Mento-native token identity MUST follow the same procedure; failure to triangulate is an anti-fishing-banned shortcut per `feedback_pathological_halt_anti_fishing_checkpoint`:

1. **Mento Labs official deployment docs** at `https://docs.mento.org/mento-v3/build/deployments/addresses.md` — authoritative on Mento V2/V3 contract addresses (e.g., `StableTokenCOP`, `StableTokenUSD`, etc.). The legacy URL `https://docs.mento.org/mento/protocol/deployments` 404s and is superseded.
2. **Dune decoded-table catalog** via `mcp__dune__searchTablesByContractAddress` — authoritative on which contract is decoded as a Mento `StableTokenV2`. Mento-protocol-specific events (`evt_exchangeupdated`, `evt_validatorsupdated`, `evt_brokerupdated`, `evt_initialized`) presence on a contract is dispositive of Mento-protocol-native status.
3. **Celo Token List** at `https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json` — useful disambiguation evidence (community-attested registry); NOT authoritative when (1) and (2) disagree.
4. **Project memory cross-check** against `project_mento_canonical_naming_2026` (β-corrigendum block at file top) and `project_abrigo_mento_native_only` (β-corrigendum extension).

The empirical-evidence trail for the Rev-5.3.5 β-disposition lives in: the disposition memo at `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md`, sub-task 1's §β-rescope inventory at `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` lines 260-431, and the 3-way disposition review trio at `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-{code-reviewer,reality-checker,technical-writer}.md`.

---

## §3 — Per-token registry (Mento-native, in-scope)

**Count: 6 tokens.** Each subsection below carries: canonical post-rebrand ticker (with lowercase-m disambiguation for COPm), pre-rebrand legacy ticker (where applicable), contract address on Celo (chainId 42220, mixed-case as recorded; case-folded comparison is the byte-equality test), first-observed-on-chain date, Mento Reserve relationship, basket-membership status, primary on-chain provenance citation, secondary docs provenance, and Celo Token List provenance. Total supply is **deliberately omitted** per §1.3.

### §3.1 — COPm (Mento Colombian Peso)

| Field | Value |
|---|---|
| Canonical post-rebrand ticker | **COPm** (lowercase final-m) |
| Pre-rebrand legacy ticker | unchanged (deployed natively as Mento V2 `StableTokenCOP`; no pre-rebrand legacy variant) |
| Contract address (Celo, chainId 42220) | `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` |
| First-observed-on-chain | 2024-10-31 16:35:48 UTC; activity through 2026-04-26 21:12:59 UTC at registry-authoring time; 285,390 transfer events; 5,015 distinct senders; 16,918 distinct receivers; 78 weeks of activity |
| Mento Reserve relationship | Reserve-collateralized; canonical Mento V2 `StableTokenCOP`; Mento-protocol governance events `evt_exchangeupdated`, `evt_validatorsupdated`, `evt_brokerupdated`, `evt_initialized` decoded under Dune project `celocolombianpeso` (dispositive of Mento-protocol-native status per §2 procedure) |
| Basket-membership status | Active under Rev-5.3.5; β-track Rev-3 ingestion plumbing pointed at this address is authored under Task 11.P.spec-β + Task 11.P.exec-β (NOT under MR-β.1; sub-plan §G-3 reaffirms editorial-only scope). At registry-authoring time, **0 events ingested into any DuckDB `onchain_*` table from this address** — see §4 for DuckDB linkage |
| Primary on-chain provenance | Dune query 7378788 (β-feasibility activity probe; disposition memo §3.2). Dune project `celocolombianpeso` (24 decoded tables, including `celocolombianpeso_celo.stabletokenv2_evt_transfer`) decoded as `StableTokenV2` |
| Secondary docs provenance | Mento V3 deployments docs at `https://docs.mento.org/mento-v3/build/deployments/addresses.md` — `StableTokenCOP` canonical address |
| Celo Token List provenance | Celo Token List 2026-04-26: `name = "Mento Colombian Peso"`, `symbol = "COPm"`, `decimals = 18`, `chainId = 42220` |
| Implementation-sharing note | Per RC re-review independent finding (RC-3 cross-strengthening): all six Mento StableTokens share implementation `0x434563B0604BE100F04B7Ae485BcafE3c9D8850E`; the per-token addresses in §3.1-§3.6 are all proxies pointing at this shared implementation |

### §3.2 — USDm (Mento Dollar)

| Field | Value |
|---|---|
| Canonical post-rebrand ticker | **USDm** |
| Pre-rebrand legacy ticker | cUSD |
| Contract address (Celo, chainId 42220) | `0x765DE816845861e75A25fCA122bb6898B8B1282a` |
| First-observed-on-chain | 2020-04-22 20:21:03 UTC (block `2961`); ~835.6M transfers cumulative as of 2026-04-26 |
| Mento Reserve relationship | Reserve-collateralized; one of the two original Mento V1 basket stables (USDm + EURm), genesis stables of the Mento protocol |
| Basket-membership status | Active; consumed under `onchain_xd_weekly` proxy_kind `carbon_per_currency_usdm_volume_usd` (82 weeks pre-aggregated; see §5 entry 9). β-track Rev-3 will continue to consume USDm at the same address (no β-disposition impact) |
| Primary on-chain provenance | Dune query 7379578 (DE re-dispatch; `mento_celo.stabletoken_evt_transfer`; first-transfer + cumulative-volume probe; `free` tier, 0.906 credits) |
| Secondary docs provenance | Mento V3 deployments docs at `https://docs.mento.org/mento-v3/build/deployments/addresses.md`; Task 11.N.2b.1 gate-decision memo §1 (prior Celoscan verification, status OK) |
| Celo Token List provenance | Celo Token List 2026-04-26: `name = "Mento Dollar"`, `symbol = "USDm"`, `decimals = 18`, `chainId = 42220` |

### §3.3 — EURm (Mento Euro)

| Field | Value |
|---|---|
| Canonical post-rebrand ticker | **EURm** |
| Pre-rebrand legacy ticker | cEUR |
| Contract address (Celo, chainId 42220) | `0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73` |
| First-observed-on-chain | 2021-03-25 15:38:05 UTC (block `5,822,108`); ~19.3M transfers cumulative as of 2026-04-26 (first transfer ~11 months after USDm genesis) |
| Mento Reserve relationship | Reserve-collateralized; second of the two original Mento V1 basket stables (deployed alongside USDm at protocol genesis) |
| Basket-membership status | Active; consumed under `onchain_xd_weekly` proxy_kind `carbon_per_currency_eurm_volume_usd` (82 weeks pre-aggregated; see §5 entry 7) |
| Primary on-chain provenance | Dune query 7379585 (DE re-dispatch; UNION-ALL probe over per-token decoded tables; `mento_celo.stabletokeneur_evt_transfer`; `free` tier, 0.075 credits) |
| Secondary docs provenance | Mento V3 deployments docs; Task 11.N.2b.1 gate-decision memo §1 |
| Celo Token List provenance | Celo Token List 2026-04-26: `name = "Mento Euro"`, `symbol = "EURm"`, `decimals = 18`, `chainId = 42220` |

### §3.4 — BRLm (Mento Brazilian Real)

| Field | Value |
|---|---|
| Canonical post-rebrand ticker | **BRLm** |
| Pre-rebrand legacy ticker | cREAL |
| Contract address (Celo, chainId 42220) | `0xe8537a3d056DA446677B9E9d6c5dB704EaAb4787` |
| First-observed-on-chain | 2021-12-15 21:45:22 UTC (block `10,405,343`); ~6.4M transfers cumulative as of 2026-04-26 (deployed ~8 months after EURm) |
| Mento Reserve relationship | Reserve-collateralized; first second-generation Mento basket stable (post-USDm/EURm genesis stables) |
| Basket-membership status | Active; consumed under `onchain_xd_weekly` proxy_kind `carbon_per_currency_brlm_volume_usd` (82 weeks pre-aggregated; see §5 entry 6) |
| Primary on-chain provenance | Dune query 7379585 (DE re-dispatch; UNION-ALL probe; `mento_celo.stabletokenbrl_evt_transfer`) |
| Secondary docs provenance | Mento V3 deployments docs; Task 11.N.2b.1 gate-decision memo §1 (Celoscan label "Mento Brazilian Real, EIP-1967 proxy") |
| Celo Token List provenance | Celo Token List 2026-04-26: `name = "Mento Brazilian Real"`, `symbol = "BRLm"`, `decimals = 18`, `chainId = 42220` |

### §3.5 — KESm (Mento Kenyan Shilling)

| Field | Value |
|---|---|
| Canonical post-rebrand ticker | **KESm** |
| Pre-rebrand legacy ticker | cKES |
| Contract address (Celo, chainId 42220) | `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` |
| First-observed-on-chain | 2024-05-21 14:10:00 UTC (block `25,725,915`); ~3.2M transfers cumulative as of 2026-04-26 |
| Mento Reserve relationship | Reserve-collateralized; Africa-tier Mento basket stable; StableTokenV2 implementation |
| Basket-membership status | Active; consumed under `onchain_xd_weekly` proxy_kind `carbon_per_currency_kesm_volume_usd` (82 weeks pre-aggregated; see §5 entry 8) |
| Primary on-chain provenance | Dune query 7379585 (DE re-dispatch; UNION-ALL probe; `ckes_mento_celo.stabletokenv2_evt_transfer`) |
| Secondary docs provenance | Mento V3 deployments docs |
| Celo Token List provenance | Celo Token List 2026-04-26: `name = "Mento Kenyan Shilling"`, `symbol = "KESm"`, `decimals = 18`, `chainId = 42220` |

### §3.6 — XOFm (Mento West African CFA franc)

| Field | Value |
|---|---|
| Canonical post-rebrand ticker | **XOFm** |
| Pre-rebrand legacy ticker | unchanged (deployed under tail-`m` from genesis; the external-marketplace alias `eXOF` was never used in `project_mento_canonical_naming_2026`) |
| Contract address (Celo, chainId 42220) | `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08` |
| First-observed-on-chain | 2023-10-16 15:12:02 UTC (block `21,960,106`); ~2.4M transfers cumulative as of 2026-04-26 |
| Mento Reserve relationship | Reserve-collateralized; Africa-tier Mento basket stable; `StableTokenXOFProxy` decoded structure pointing at the shared StableTokenV2 implementation |
| Basket-membership status | Active; consumed under `onchain_xd_weekly` proxy_kind `carbon_per_currency_xofm_volume_usd` (82 weeks pre-aggregated; see §5 entry 10) |
| Primary on-chain provenance | Dune query 7379590 (DE re-dispatch; `erc20_celo.evt_transfer` filter on the proxy address; `free` tier, 1.866 credits — the XOFm proxy does not expose its own per-token decoded `evt_transfer` table, so the generic `erc20_celo.evt_transfer` filter was the canonical source) |
| Secondary docs provenance | Mento V3 deployments docs |
| Celo Token List provenance | Celo Token List 2026-04-26: `name = "Mento West African CFA franc"`, `symbol = "XOFm"`, `decimals = 18`, `chainId = 42220` |

---

## §4 — DuckDB cross-reference (live `onchain_*` tables, audit-time inventory)

Per sub-task 2 audit at `contracts/.scratch/2026-04-25-duckdb-address-audit.md`, the live DuckDB at `contracts/data/structural_econ.duckdb` (audit-time path; consume-only) carries **14 `onchain_*` tables** as of registry-authoring time. Every table is tagged with exactly ONE of {DIRECT in-scope, DIRECT mixed-scope, DIRECT DEFERRED-via-scope-mismatch, DERIVATIVE DEFERRED-via-scope-mismatch} per the sub-task 2 audit's coverage scheme; **0 tables are DEFERRED purely under prior Rev-5.3.x scope**. Each row's address linkage cross-references back to §3 (in-scope) or §8 (out-of-scope appendix).

| # | Table | Tag | Address(es) or parent | Mento-native token tracked |
|---|---|---|---|---|
| 1 | `onchain_carbon_arbitrages` | DIRECT in-scope | CarbonController `0x66198711…`; BancorArbitrage `0x8c05ea30…` per `project_carbon_defi_attribution_celo`; 0 rows ingested at audit time | Carbon DeFi MM platform (basket-counter-side); not a Mento-native token; cross-reference to §3 is platform-level (basket = Mento-native USDm/EURm/BRLm/KESm/XOFm + future COPm) |
| 2 | `onchain_carbon_tokenstraded` | DIRECT in-scope | CarbonController `0x66198711…`; row-level `trader = 0x8c05ea30…` partition rule per `project_carbon_user_arb_partition_rule`; 0 rows ingested at audit time | Carbon DeFi MM trades (basket-counter-side); cross-reference to §3 via the per-currency proxy_kinds in `onchain_xd_weekly` (§5) — `sourceToken`/`targetToken` filters resolve to per-token addresses |
| 3 | `onchain_copm_address_activity_top400` | DERIVATIVE DEFERRED-via-scope-mismatch | Parent: `onchain_copm_transfers` (top-400 sender/receiver activity reduction); inheritance chain | OUT of Mento-native scope; tracks COPM-Minteo `0xC92E8Fc2…` via inheritance — see §8 |
| 4 | `onchain_copm_burns` | DIRECT DEFERRED-via-scope-mismatch | COPM-Minteo `0xC92E8Fc2…` burn call traces; 121 rows | OUT of Mento-native scope — see §8 |
| 5 | `onchain_copm_ccop_daily_flow` | DIRECT DEFERRED-via-scope-mismatch (paired-source) | **Paired source** — see §6 explicit disambiguation entry: `copm_*` columns sourced from COPM-Minteo `0xC92E8Fc2…` (mint/burn call traces); `ccop_*` columns sourced from a separately-named historical-cCOP token via Dune query `7366593` (USDT-paired); 585 rows | BOTH halves OUT of Mento-native scope; full table tagged DEFERRED-via-scope-mismatch — see §6 |
| 6 | `onchain_copm_daily_transfers` | DERIVATIVE DEFERRED-via-scope-mismatch | Parent: `onchain_copm_transfers` (daily aggregation: `n_transfers`, `n_tx`, `n_distinct_from`, `n_distinct_to`, `total_value_wei`); 522 rows | OUT of Mento-native scope; tracks COPM-Minteo `0xC92E8Fc2…` via inheritance — see §8 |
| 7 | `onchain_copm_freeze_thaw` | DIRECT DEFERRED-via-scope-mismatch | COPM-Minteo `0xC92E8Fc2…` freeze/thaw event logs; 4 rows | OUT of Mento-native scope — see §8 |
| 8 | `onchain_copm_mints` | DIRECT DEFERRED-via-scope-mismatch | COPM-Minteo `0xC92E8Fc2…` mint call traces; 146 rows | OUT of Mento-native scope — see §8 |
| 9 | `onchain_copm_time_patterns` | DERIVATIVE DEFERRED-via-scope-mismatch | Parent: `onchain_copm_transfers` (diurnal-pattern aggregation by `kind` × `bucket`); 86 rows | OUT of Mento-native scope; tracks COPM-Minteo `0xC92E8Fc2…` via inheritance — see §8 |
| 10 | `onchain_copm_transfers` | DIRECT DEFERRED-via-scope-mismatch | COPM-Minteo `0xC92E8Fc2…` Transfer events; 110,253 rows; coverage 2024-09-17 → 2026-04-25 | OUT of Mento-native scope — see §8 |
| 11 | `onchain_copm_transfers_sample` | DERIVATIVE DEFERRED-via-scope-mismatch | Parent: `onchain_copm_transfers` (10-row sample reduction) | OUT of Mento-native scope; tracks COPM-Minteo `0xC92E8Fc2…` via inheritance — see §8 |
| 12 | `onchain_copm_transfers_top100_edges` | DERIVATIVE DEFERRED-via-scope-mismatch | Parent: `onchain_copm_transfers` (top-100 from→to edge aggregation; `n_transfers`, `total_value_wei`, `first_time`, `last_time`); 100 rows | OUT of Mento-native scope; tracks COPM-Minteo `0xC92E8Fc2…` via inheritance — see §8 |
| 13 | `onchain_xd_weekly` | DIRECT mixed-scope | 10-`proxy_kind` aggregation table; 819 rows total; per-`proxy_kind` provenance enumerated in §5 | Mixed: 9 of 10 `proxy_kind` values track Mento-native addresses (in-scope); 1 of 10 (`carbon_per_currency_copm_volume_usd`) tracks COPM-Minteo `0xC92E8Fc2…` and is DEFERRED-via-scope-mismatch — see §5 + §8 |
| 14 | `onchain_y3_weekly` | DIRECT in-scope | Y₃ inequality-differential 4-country panel (CO/BR/KE/EU); methodology-scoped via `source_methodology` (3 enumerated values); NOT address-scoped on Celo; 291 rows | Macro-data-derived inequality differential; the `copm_diff` column tracks the Colombian-peso macro-data component (DANE/IMF), NOT on-chain `0xC92E8Fc2…` events — see slug-asymmetry note in §6.5 of the sub-task 2 audit |

**Tag totals (matches sub-task 2 §3 audit, verifiable):**

- DIRECT in-scope: **3** (`onchain_carbon_arbitrages`, `onchain_carbon_tokenstraded`, `onchain_y3_weekly`)
- DIRECT mixed-scope: **1** (`onchain_xd_weekly`)
- DIRECT DEFERRED-via-scope-mismatch: **5** (`onchain_copm_burns`, `onchain_copm_ccop_daily_flow`, `onchain_copm_freeze_thaw`, `onchain_copm_mints`, `onchain_copm_transfers`)
- DERIVATIVE DEFERRED-via-scope-mismatch: **5** (`onchain_copm_address_activity_top400`, `onchain_copm_daily_transfers`, `onchain_copm_time_patterns`, `onchain_copm_transfers_sample`, `onchain_copm_transfers_top100_edges`)
- DEFERRED (prior Rev-5.3.x scope, not β): 0

**Sum: 3 + 1 + 5 + 5 + 0 = 14.** Matches the live-DuckDB pre-flight enumeration count of 14. Coverage HALT-clear; consistent with sub-task 2 audit §9 coverage-completeness verification.

---

## §5 — `onchain_xd_weekly` proxy_kind enumeration (10 active values)

Per sub-task 2 audit §5, the `onchain_xd_weekly` table aggregates 10 distinct `proxy_kind` values. Per-`proxy_kind` provenance + scope status under β:

| # | proxy_kind | Row count | On-chain source / address | Scope under β |
|---|---|---|---|---|
| 1 | `carbon_basket_user_volume_usd` | 82 | Carbon DeFi user-side basket volume; `onchain_carbon_tokenstraded` filtered to `trader != 0x8c05ea30…` per `project_carbon_user_arb_partition_rule`; basket = Mento-native stablecoin family (USDm/EURm/BRLm/KESm/XOFm + future COPm at `0x8A567e2a…`) | **In-scope** (primary X_d under Rev-5.3.2; basket-internal flows on Mento-native side) |
| 2 | `carbon_basket_arb_volume_usd` | 82 | Carbon DeFi arbitrageur-side basket volume; same `onchain_carbon_tokenstraded` source filtered to `trader = 0x8c05ea30…` (BancorArbitrage) per `project_carbon_user_arb_partition_rule` | **In-scope** (arb-side diagnostic; same basket scope as user-side) |
| 3 | `b2b_to_b2c_net_flow_usd` | 79 | Supply-channel diagnostic (B2B-issued stables flowing to B2C wallets via Mento Reserve broker / minter-partition heuristic); pre-existing under Rev-5.3.2 scope; address-source = Mento Reserve / Mento-native StableTokenV2 contracts per §3 | **In-scope** (Mento-native supply-channel diagnostic) |
| 4 | `net_primary_issuance_usd` | 84 | Supply-channel diagnostic (net new issuance against Mento Reserve over the week); pre-existing under Rev-5.3.2 scope; address-source = Mento Reserve / Mento-native StableTokenV2 contracts per §3 | **In-scope** (Mento-native primary-issuance diagnostic) |
| 5 | `carbon_per_currency_copm_volume_usd` | 82 | Carbon DeFi per-currency volume filtered to COPM-Minteo `0xC92E8Fc2…` (Rev-2 X_d source) | **DEFERRED-via-scope-mismatch** under β — the slug `_copm_` (lowercase) was authored pre-rebrand pointing at Minteo-fintech, NOT at Mento-native COPm `0x8A567e2a…` per §3.1; sub-plan §I sub-task 2 rescope; cross-reference §8 (out-of-scope appendix) |
| 6 | `carbon_per_currency_brlm_volume_usd` | 82 | Carbon DeFi per-currency volume filtered to BRLm `0xe8537a3d056DA446677B9E9d6c5dB704EaAb4787` (per §3.4) | **In-scope** (BRLm Mento-native, basket-active) |
| 7 | `carbon_per_currency_eurm_volume_usd` | 82 | Carbon DeFi per-currency volume filtered to EURm `0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73` (per §3.3) | **In-scope** (EURm Mento-native, basket-active) |
| 8 | `carbon_per_currency_kesm_volume_usd` | 82 | Carbon DeFi per-currency volume filtered to KESm `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` (per §3.5) | **In-scope** (KESm Mento-native, basket-active) |
| 9 | `carbon_per_currency_usdm_volume_usd` | 82 | Carbon DeFi per-currency volume filtered to USDm `0x765DE816845861e75A25fCA122bb6898B8B1282a` (per §3.2) | **In-scope** (USDm Mento-native, basket-active) |
| 10 | `carbon_per_currency_xofm_volume_usd` | 82 | Carbon DeFi per-currency volume filtered to XOFm `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08` (per §3.6) | **In-scope** (XOFm Mento-native, basket-active) |

**In-scope per-`proxy_kind` count: 9 of 10.** The single DEFERRED-via-scope-mismatch is `carbon_per_currency_copm_volume_usd`. The Rev-5.3.2 published estimates against `carbon_basket_user_volume_usd` (primary X_d) remain byte-exact-immutable per anti-fishing invariants (`decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c`); the per-currency COPM proxy was a diagnostic, not the primary X_d, so the scope-mismatch does NOT propagate to the primary estimates.

---

## §6 — `onchain_copm_ccop_daily_flow` explicit disambiguation entry (per RC R-2)

Per RC R-2 in sub-plan §H CORRECTIONS, this table receives a dedicated registry entry because its name literally embeds the cCOP-vs-COPM ambiguity that the rescoped Rev-5.3.5 β-deliverable exists to lock down. The explicit narrative treatment follows.

### §6.1 — Filter-address determination (paired source)

The table is a **paired-source artifact** tracking TWO distinct on-chain identities joined on `date`:

1. **`copm_*` half (`copm_mint_usd`, `copm_burn_usd`, `copm_unique_minters`; 100% non-null at 585/585 rows).** Sourced from **COPM-Minteo at `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606`** (mint/burn call traces). **OUT of Mento-native scope** under β; cross-reference §8.
2. **`ccop_*` half (`ccop_usdt_inflow_usd`, `ccop_usdt_outflow_usd`, `ccop_unique_senders`; uniformly 92.5% non-null at 541/585 across all three columns).** Sourced from a separately-named historical-cCOP token paired with USDT inflow/outflow; the upstream Dune query ID `7366593` is the schema-recorded provenance (`source_query_ids` column carries the single distinct value `7366593`). The uniform 92.5% non-null rate across all three `ccop_*` columns is the asymmetric-null-pattern signature confirming they share the same source sub-query. The `ccop` side's address-level identity is NOT directly determinable from DuckDB schema introspection alone; per the sub-task 2 audit's read-only / no-row-mutation hard constraint, the `ccop` side is **separately-named historical-cCOP source, NOT Mento-native COPm at `0x8A567e2a…`** (the Mento-native COPm Dune attribution path was authored under sub-task 1 re-dispatch via separate query IDs 7378788/7379527/7379530, not 7366593). [Corrected per RC sub-task 3 trio review 2026-04-26: prior version of this paragraph mis-stated `ccop_unique_senders` as 100% non-null; live re-probe confirms 541/585 = 92.5% uniform across all three `ccop_*` columns, byte-aligning with sub-task 2 audit §6.1 post-correction at commit `09bacc105`. Strengthens rather than weakens the paired-source conclusion; scope tag DEFERRED-via-scope-mismatch unaffected.]

### §6.2 — Full-table scope tag under β

**Tag: DEFERRED-via-scope-mismatch.** Reasoning:

- The `copm_*` half is unambiguously OUT of Mento-native scope (Minteo-fintech `0xC92E8Fc2…`).
- The `ccop_*` half is unspecified-address-source under audit-time read-only verification AND is also NOT Mento-native COPm at `0x8A567e2a…` (no Dune query ID at audit time targets that address from this table; ingestion plumbing into `0x8A567e2a…` is β-spec future work).
- Both halves of the paired source are NON-Mento-native under β disposition. The DEFERRED-via-scope-mismatch tag applies to the table as a whole.

### §6.3 — Future-revision rename recommendation (NOT executed under this sub-plan)

Per sub-plan §B-2 + §I sub-task 2 rescope strengthening, the recommendation below is **recorded for future revision consideration only**; no rename is executed under MR-β.1:

- **Drop the `_ccop_` slug fragment** — the fragment is a pre-rebrand legacy artifact meaningless under post-rebrand canonical naming per `project_mento_canonical_naming_2026` and ambiguous under Rev-5.3.5 β-disposition.
- **Re-slug as `onchain_copm_minteo_daily_flow`** — pinning the `_minteo_` qualifier makes the Minteo-fintech scope explicit at the table-name level and prevents future readers from conflating with Mento-native COPm.
- **If the `ccop_*` side later requires preservation in a separate table**, author a new artifact (e.g., `onchain_celo_ccop_historical_usdt_flow`) with a name that pins the historical / pre-rebrand semantic and the USDT-pairing nature, rather than overloading a single table with two source identities.

The recommendation is stable as a future-revision candidate; sub-plan §B-2's "no rename, no schema migration" invariant binds this sub-task.

---

## §7 — Slug-vs-canonical-ticker mapping (annotation-only)

Per sub-plan §C sub-task 3 acceptance line 132, the legacy `proxy_kind` slug fragments are mapped to canonical post-rebrand addresses. The slugs were authored before the 2026 rebrand AND pre-Rev-5.3.5 β-disposition; **they were intentionally not mass-renamed for migration-stability reasons** per `project_mento_canonical_naming_2026`. The `copm` slug is **flagged as ambiguous** because the slug name reflects pre-rebrand legacy attribution (Minteo-fintech `0xC92E8Fc2…`) while the post-rebrand corrected naming would suggest Mento-native COPm `0x8A567e2a…`.

| Slug fragment | Surface location | Canonical address resolved at audit time | Asymmetry note |
|---|---|---|---|
| `usdm` | `carbon_per_currency_usdm_volume_usd` proxy_kind | USDm `0x765DE816845861e75A25fCA122bb6898B8B1282a` (per §3.2) | None — slug matches canonical post-rebrand ticker; in-scope |
| `eurm` | `carbon_per_currency_eurm_volume_usd` proxy_kind | EURm `0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73` (per §3.3) | None — slug matches canonical post-rebrand ticker; in-scope |
| `brlm` | `carbon_per_currency_brlm_volume_usd` proxy_kind | BRLm `0xe8537a3d056DA446677B9E9d6c5dB704EaAb4787` (per §3.4) | None — slug matches canonical post-rebrand ticker; in-scope |
| `kesm` | `carbon_per_currency_kesm_volume_usd` proxy_kind | KESm `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` (per §3.5) | None — slug matches canonical post-rebrand ticker; in-scope |
| `xofm` | `carbon_per_currency_xofm_volume_usd` proxy_kind | XOFm `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08` (per §3.6) | None — slug matches canonical post-rebrand ticker; in-scope |
| `copm` | `carbon_per_currency_copm_volume_usd` proxy_kind + 12 of 14 `onchain_copm_*` table names | **COPM-Minteo `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606`** (audit-time live ingestion; per §8-appendix-entry-1) | **AMBIGUOUS** — pre-rebrand legacy slug; under post-rebrand canonical naming would suggest Mento-native COPm `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` (per §3.1) but at audit time resolves to Minteo-fintech `0xC92E8Fc2…`; future-revision rename recommendation may rename to `copm_minteo` or similar |
| `ccop` | `onchain_copm_ccop_daily_flow` table name | Separately-named historical-cCOP token (address unspecified at audit-time read-only verification; sourced via Dune query `7366593`) | Pre-rebrand legacy slug with no canonical post-rebrand address attribution; future-revision rename recommended in §6.3 |
| `copm_diff` (column name) | `onchain_y3_weekly` schema | Macro-data-derived (DANE / IMF / Eurostat); NOT address-filtered to any Celo contract | Column name follows pre-rebrand legacy convention; column tracks Colombian-peso inequality-differential macro component, not on-chain Minteo-fintech events |

**No rename executed under this sub-plan per §B-2.** All slug-asymmetry notes above are annotation-only.

---

## §8 — Out-of-scope third-party tokens (audit-trail preservation)

This appendix preserves the historical record of out-of-Mento-native-scope tokens for audit-trail purposes. **Entries here are NOT registry entries** — they are explicitly excluded from the §3 in-scope per-token registry; they are documented to make the Rev-5.3.5 β-disposition's scope-mismatch decision visible to future readers (cross-reference Rev-5.3.5 CORRECTIONS in major plan, sub-plan §I CORRECTIONS, project-memory β-corrigenda).

**Count: 1 entry.**

### §8.1 — COPM-Minteo (Minteo-fintech, OUT of Mento-native scope)

| Field | Value |
|---|---|
| Ticker (Celo Token List) | **COPM** (uppercase final-M) — distinct from Mento-native COPm (lowercase final-m) per §3.1 |
| Celo Token List name | "COP Minteo" |
| Contract address (Celo, chainId 42220) | `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606` |
| Scope tag | **OUT of Mento-native scope** per `project_abrigo_mento_native_only` (β-corrigendum extension) and Rev-5.3.5 CORRECTIONS block in major plan |
| Origin / issuer | Minteo (third-party fintech on Celo); NOT Mento-protocol-native (no `evt_exchangeupdated` / `evt_validatorsupdated` / `evt_brokerupdated` events on this contract) |
| DuckDB ingestion footprint | 110,253 transfer events ingested into `onchain_copm_transfers` (covering 2024-09-17 → 2026-04-25); 121 burn events in `onchain_copm_burns`; 146 mint events in `onchain_copm_mints` (~4.94B units total mint volume); 4 freeze/thaw events in `onchain_copm_freeze_thaw`; 5 DERIVATIVE tables inheriting; the `copm_*` half of `onchain_copm_ccop_daily_flow`; the `carbon_per_currency_copm_volume_usd` proxy_kind in `onchain_xd_weekly` (82 weeks pre-aggregated). Cross-reference §4 + §5 + §6 |
| Rev-2 audit-trail status | Was the Rev-2 X_d data source. Rev-2 published estimates (β̂ = −2.7987e−8, n = 76, T3b FAIL, `MDES_FORMULATION_HASH = 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa`, `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c`) remain **byte-exact-immutable** per Rev-5.3.x anti-fishing invariants (sub-plan §B-1; major plan Rev-5.3.5 anti-fishing block). Re-interpretation under β: **Rev-2 closes scope-mismatch** (measured the wrong address — Minteo-fintech, not Mento-native), NOT as "Mento-hedge-thesis-tested-and-failed" |
| Mento-protocol fields (Reserve / basket / issuance) | **NOT APPLICABLE** — Mento-protocol fields are not enumerated for an out-of-scope third-party token; this entry exists for audit-trail preservation only |
| DuckDB cross-reference tag | All 10 `onchain_copm_*` tables (5 DIRECT + 5 DERIVATIVE) and 1 `proxy_kind` (`carbon_per_currency_copm_volume_usd`) tagged DEFERRED-via-scope-mismatch in §4 + §5 |
| Audit-trail cross-reference | Sub-task 1 §β-rescope.2 (out-of-scope inventory entry); sub-task 2 §3 + §4.3 (DEFERRED-via-scope-mismatch table tags); Rev-5.3.5 CORRECTIONS block in major plan; disposition memo at `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md`; project-memory β-corrigenda at `project_mento_canonical_naming_2026` and `project_abrigo_mento_native_only` |

**End of out-of-scope appendix.** No further out-of-scope entries are enumerated; if a future sub-plan discovers an additional out-of-Mento-native-scope token whose preservation is audit-warranted, that token's appendix entry lands under a new section (§8.2, §8.3, ...) — never as an in-place edit to §8.1 or as an entry in §3.

---

## §9 — Non-canonical-source warning (mandatory for future research)

Third-party Celo-forum posts, social-media discussions, blog summaries, and similar external sources have demonstrated **TWO-LAYER inverted-attribution failure modes** in this project's history:

- **Layer 1 (Rev-5.3.3 cCOP-vs-COPM inversion).** The Trend Researcher's Finding 3 (research file `contracts/.scratch/2026-04-25-mento-userbase-research.md`) attributed the Mento-native Colombia token identity to "cCOP" and the address `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606` to "cCOP / Mento-native." The user corrected the attribution mid-Rev-5.3.3: *"is COPM not cCOP."* Pre-existing project memory `project_mento_canonical_naming_2026` ("COPM and XOFm unchanged; address-level identity preserved") was correct on the **ticker** layer; the agent's brief Rev-5.3.3 attribution flip was wrong.
- **Layer 2 (Rev-5.3.4 address-level inversion).** After correcting Layer 1, the Rev-5.3.4 rescoped framing claimed the Mento-native COPM **address** is `0xC92E8Fc2…`. Empirical disambiguation under Rev-5.3.5 (Dune `searchTablesByContractAddress` + activity probe + Mento V3 deployments docs + Celo Token List, all triangulated under MR-β.1 sub-task 1) corrected this: the Mento-native Colombian-peso address is **`0x8A567e2aE79CA692Bd748aB832081C45de4041eA` (canonical Mento V2 `StableTokenCOP`, lowercase ticker COPm)**; the address `0xC92E8Fc2…` is **Minteo-fintech "COP Minteo"**, OUT of Mento-native scope.

Both inversions originated from third-party / forum-style sources rather than from the four authoritative triangulation sources enumerated in §2. Future research that touches Mento-native token identity at any grain (ticker level, address level, project / issuer level) MUST follow the §2 mandatory triangulation procedure:

1. Mento Labs official deployment docs at `https://docs.mento.org/mento-v3/build/deployments/addresses.md` for canonical contract addresses (e.g., `StableTokenCOP`).
2. Dune decoded-table catalog (`mcp__dune__searchTablesByContractAddress`) for project-name confirmation — authoritative on which contract is decoded as a Mento `StableTokenV2`. Mento-protocol-specific events (`evt_exchangeupdated`, `evt_validatorsupdated`, `evt_brokerupdated`, `evt_initialized`) presence is dispositive of Mento-protocol-native status.
3. Celo Token List at `https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json` for community-attested registry entries — useful disambiguation evidence but NOT authoritative when (1) and (2) disagree.
4. Cross-check against this registry (§3 in-scope, §8 out-of-scope appendix) and against `project_mento_canonical_naming_2026` (β-corrigendum block at file top) + `project_abrigo_mento_native_only` (β-corrigendum extension).

**Failure to triangulate before propagating a token-identity claim into specs / plans / code / project memory is an anti-fishing-banned shortcut per `feedback_pathological_halt_anti_fishing_checkpoint`.** A future-research safeguard memo at `contracts/.scratch/2026-04-25-future-research-token-identity-safeguard.md` (sub-task 5 deliverable; **to be authored under sub-task 5 dispatch** post-MR-β.1 sub-tasks 3 + 4 convergence) will carry the process-discipline detail; this §9 carries the registry-internal warning.

---

## §10 — Audit-trail footer

### §10.1 — Sub-plan + sub-task lineage

- **MR-β.1 sub-plan source-of-truth:** `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` — §C sub-tasks 1-5, §H CORRECTIONS (post-3-way-review fix-up), §I CORRECTIONS Rev-5.3.5 (β-resolution).
- **Sub-task 1 inventory memo (consumed input):** `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` — §β-rescope.1 (in-scope 6-token inventory; lines 260-431) + §β-rescope.2 (out-of-scope COPM-Minteo) + §β-rescope.3 (HALT-VERIFY discipline reaffirmation) + §β-rescope.4 (audit-trail cross-references).
- **Sub-task 2 audit memo (consumed input):** `contracts/.scratch/2026-04-25-duckdb-address-audit.md` — 14-table coverage classification, 10-`proxy_kind` enumeration, paired-source finding for `onchain_copm_ccop_daily_flow`.
- **Sub-task 4 deliverable (downstream):** TR research file corrigendum at `contracts/.scratch/2026-04-25-mento-userbase-research.md` (corrigendum to be authored under sub-task 4 dispatch; cross-references this registry by path).
- **Sub-task 5 deliverable (downstream):** Future-research safeguard memo at `contracts/.scratch/2026-04-25-future-research-token-identity-safeguard.md` (memo to be authored under sub-task 5 dispatch post-MR-β.1 sub-tasks 3 + 4 convergence; will cross-reference this registry by path).

### §10.2 — Disposition + review trail

- **HALT-VERIFY disposition memo (β path):** `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` (disposition commit `00790855b`).
- **3-way disposition review trio:** `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-code-reviewer.md`, `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-reality-checker.md`, `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-technical-writer.md`.
- **Sub-plan trio convergence on fix-up bundle:** commit `b4a6a50e6`.
- **Sub-task 1 RC spot-check:** `contracts/.scratch/2026-04-25-subtask-mr-beta-1-1-rc-spot-check.md` (commit `3286dfe66`); RC PASS-w-β-advisory at commit `eb72f7133`.
- **Sub-task 2 RC spot-check:** RC PASS-w-1-line-correction-inline at commit `09bacc105`.
- **Sub-task 1 re-dispatch + commit:** commit `b6d320429`.
- **Sub-task 2 commit:** commit `b8e220da1`.
- **Prior-dispatch DE deliverable (HALT-VERIFY-firing memo, content preserved in sub-task 1 inventory above):** commit `3611b0716`.

### §10.3 — Major plan + project memory anchors

- **Major plan:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` — Rev-5.3.5 CORRECTIONS block (file end), Rev-5.3.4 CORRIGENDUM block, Rev-5.3.3 CORRECTIONS block.
- **Project memory β-corrigenda:** `project_mento_canonical_naming_2026` (β-corrigendum block at file top, original content preserved below); `project_abrigo_mento_native_only` (β-corrigendum extension).
- **Load-bearing project memory anchors:** `project_carbon_defi_attribution_celo` (CarbonController `0x66198711…` + BancorArbitrage `0x8c05ea30…` attribution); `project_carbon_user_arb_partition_rule` (`trader = 0x8c05ea30…` row-level partition for Carbon TokensTraded user-vs-arb USD split); `project_y3_inequality_differential_design` (4-country Y₃ panel methodology, orthogonal to X_d address rescope under β); `project_usdt_celo_canonical_address` (companion address-canonicality precedent — USDT scam-impersonator HALT-VERIFY); `feedback_three_way_review`; `feedback_implementation_review_agents`; `feedback_pathological_halt_anti_fishing_checkpoint`; `feedback_no_code_in_specs_or_plans`.

### §10.4 — Live DuckDB connection details

- **Path:** `contracts/data/structural_econ.duckdb` (audit-time path; consume-only connection).
- **Read-only invariant:** No `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `ALTER`, or `DROP` was issued under MR-β.1; per sub-plan §B-1 and §B-2.
- **Loader-helper interface:** Loader helpers (e.g., `load_onchain_xd_weekly(proxy_kind=...)`, `load_onchain_y3_weekly(...)`) consume this registry's per-token addresses indirectly via the DuckDB schema (the schema-recorded addresses must byte-match this registry at consumption time per the §1.3 immutability invariant). Address byte-equality between this registry and the loader-helper-observed schema is the verifiable HALT-VERIFY check at consumption time.
- **HEAD / commit anchor:** Live DuckDB at registry-authoring time corresponds to git HEAD `865402c2c+` on branch `phase0-vb-mvp` (no row mutations under MR-β.1 per sub-plan §G-3).

### §10.5 — Anti-fishing invariant integrity

- `N_MIN = 75` unchanged.
- `POWER_MIN = 0.80` unchanged.
- `MDES_SD = 0.40` unchanged.
- `MDES_FORMULATION_HASH = 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` unchanged.
- `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` unchanged.
- Rev-2 14-row resolution matrix and Rev-2 published estimates byte-exact preserved.
- Address registry post-converge byte-exact-immutability invariant established at §1.3; future address additions land as new appendix sections, never as in-place edits to existing entries.

The Rev-5.3.5 β-disposition is a **scope correction**, not a threshold relaxation. The registry authored here makes the scope correction explicit, durable, and cross-referenceable for every downstream β-track and α-track artifact.

**End of Mento-Native On-Chain Address Registry.**

---

## §8.2 — BancorArbitrageV2 (out-of-Mento-native-scope; partition-rule-staleness audit-trail; Rev-5.3.6 corrigendum)

**Address:** `0x20216f3056bf98e245562940e6c9c65ad9b31271`

**Identity:** **BancorArbitrageV2** — V1 successor arb router; Carbon DeFi adjacent; decoded by Dune as `carbon_defi_multichain.bancorarbitragev2_*` (38 decoded tables including `evt_arbitrageexecuted`, `call_fundandarb`, `call_flashloanandarb`, `evt_initialized`, etc.).

**Scope status under Rev-5.3.7:** OUT of Mento-native scope (Carbon DeFi has no protocol-level integration with Mento per Mento V3 deployment manifest; this entry is recorded for partition-rule-staleness audit-trail per Rev-5.3.6 disposition).

**Provenance trail:**
- Dune `searchTablesByContractAddress` confirmed 2026-04-27.
- First event 2025-07-02 01:17:32 UTC (12h31m after BancorArbitrage V1's last event at 2025-07-01 12:45:27 UTC).
- Lifetime events: 524,104 in the post-2025-07-01 window through 2026-04-03 (Dune query 7382645).
- Project namespace: `carbon_defi_multichain.bancorarbitragev2_*` (38 decoded tables; cross-chain deployment).

**Why this entry exists in the registry's out-of-scope appendix:**
- The Rev-5.3.4 partition rule for X_d (per `contracts/data/carbon_celo/README.md` line 27 + `contracts/scripts/econ_pipeline.py` line 53) used the V1 address `0x8c05ea305235a67c7095a32ad4a2ee2688ade636` ONLY. V1 died 2025-07-01.
- BancorArbitrageV2 took over 2025-07-02. Under the V1-only partition, V2 events get classified as 'user' partition (since `trader != 0x8c05ea30…`). Empirical contamination: 524,104 of 669,872 post-July 'user'-partition events are V2 (78.2%).
- This entry serves as: (a) audit-trail anchor for the V1→V2 transition; (b) future-research safeguard cited in `project_carbon_user_arb_partition_rule` β-corrigendum; (c) explicit out-of-scope tag for Mento-native β-track Rev-3.

**Cross-references:**
- §8.1 — COPM-Minteo at `0xc92e8fc2…` (out-of-scope; Rev-5.3.5 disposition).
- §4 — DuckDB cross-reference: NO existing `onchain_*` table tracks this address (V2 was discovered post-NB-α-dispatch; not previously ingested).
- Project memory `project_carbon_user_arb_partition_rule.md` (β-corrigendum 2026-04-27).
- Project memory `project_carbon_defi_attribution_celo.md` (β-corrigendum 2026-04-27).
- Project memory `project_no_mento_carbon_protocol_integration.md` (NEW 2026-04-27).
- Rev-5.3.6 disposition memo: `contracts/.scratch/2026-04-27-x-d-partition-rule-staleness-disposition-beta.md`.
- Rev-5.3.7 Option A disposition memo: `contracts/.scratch/2026-04-27-x-d-strategic-re-evaluation-disposition.md`.

**Future-research procedural note (per sub-task 5 safeguard memo):**
Any contract decoded by Dune as `*ArbitrageExecuted` event-emitter on Celo MUST be added to the partition whitelist BEFORE X_d ingestion. Triangulation procedure: `searchTablesByContractAddress` → check `contract_name` for `*Arbitrage*` patterns; cross-check `bancorarbitrage*_evt_arbitrageexecuted` table-name proliferation under `carbon_defi_multichain`. Rev-5.3.6's V1-only-rule failure is the canonical cautionary precedent.

**Registry immutability invariant honored:** This §8.2 entry is appended as a new appendix section (per §1.3 byte-exact-immutability invariant: "future address additions land as new appendix sections, never as in-place edits to existing entries"). The §8.1 COPM-Minteo entry is unmodified.
