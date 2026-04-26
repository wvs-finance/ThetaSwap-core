# Mento-Native On-Chain Address Inventory

**Sub-plan anchor:** `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` (HEAD `bf69a18f8`) — Task 11.P.MR-β.1 sub-task 1.

**Authoring date:** 2026-04-26.

**Author:** Data Engineer (sub-agent dispatch under Rev-5.3.4 RESCOPE).

**Scope:** enumerate the canonical on-chain contract address for each Mento-native stablecoin currently in the Abrigo basket (COPM, USDm, EURm, BRLm, KESm, XOFm). Per Rev-5.3.4 RESCOPE + RC R-3 immutability hygiene, the supply field is **deliberately omitted** — auditors needing current supply must query live DuckDB / Celoscan / Dune at consumption time. This memo is the address-provenance / token-identity record, not a circulating-supply dashboard.

**Consumed inputs (authoritative):**

- `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_mento_canonical_naming_2026.md` — canonical post-2026-rebrand tickers + addresses; correct as authored; no corrigendum needed under this sub-plan.
- `~/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_abrigo_mento_native_only.md` — Abrigo scope is Mento-native ONLY; corrigendum-internal already lands.
- `contracts/.scratch/2026-04-25-carbon-basket-gate-decision-memo.md` §1 (Task 11.N.2b.1 verification table) — Celoscan + Celo token-list verification of the basket addresses with HALT-VERIFY resolutions on USDT and WETH already closed.
- `contracts/.scratch/2026-04-25-mento-userbase-research.md` Finding 3 (TR research, with corrigendum target in sub-task 4) — context only; TR's external-source attribution was inverted.
- Live DuckDB at `contracts/data/structural_econ.duckdb` — `onchain_copm_transfers` (110,253 events, 2024-09-17 → 2026-04-25), the 10 `onchain_xd_weekly` `proxy_kind` values, table inventory.
- Celo Token List (canonical chainId 42220 registry): `https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json` — full token registry retrieved 2026-04-26.
- Mento Protocol docs (V3 deployments): `https://docs.mento.org/mento-v3/build/deployments.md` — deployments-page query API.

---

## CRITICAL HALT-VERIFY GATE: Colombian-peso address ambiguity

**Disposition:** raised here for user resolution per `feedback_pathological_halt_anti_fishing_checkpoint`. NOT silently overridden in either direction. The sub-plan's §B-3 source-of-truth invariant requires this to surface BEFORE the registry doc (sub-task 3) is locked.

**Two distinct Colombian-peso tokens exist on Celo mainnet, both presented with overlapping nomenclature:**

| Aspect | Token A (current `onchain_copm_transfers` source) | Token B (Mento docs canonical) |
|---|---|---|
| Address | `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606` | `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` |
| Celo Token List name | "COP Minteo" | "Mento Colombian Peso" |
| Celo Token List symbol | `COPM` (uppercase final M) | `COPm` (lowercase final m) |
| Mento Protocol V3 docs (deployments) | NOT listed as `COPM` per docs query | Listed as `StableTokenCOP`, "canonical Mento Colombian Peso address in the deployments list" — verbatim quote from docs query |
| Decimals | 18 | 18 |
| First on-chain mint observed | 2024-09-17 (block 27,786,128), `0x0…0` → `0x0155b191…7c04`, 1,000,000 units | not yet verified on-chain in this sub-task |
| Live DuckDB coverage | 110,253 transfer events covering 2024-09-17 → 2026-04-25; 147 mint events totalling ~4.94 billion units | 0 rows in `onchain_copm_transfers`; 0 rows in `onchain_carbon_tokenstraded` (empty as of probe) |

**The conflict.** Project memory `project_mento_canonical_naming_2026` records `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` under the entry "**COPM** (Minteo, unchanged)." That same memo also says "Address-level identity is unchanged — only the human-readable ticker rebranded — so on-chain partition rules and Celoscan token lists key off the address." But the Celo Token List literally labels this address as **"COP Minteo"** (the fintech-issuer brand), and Mento V3 docs explicitly identify a **different** address (`0x8A567e2aE79…`) as the Mento-protocol-native StableTokenCOP. The two tokens may be:

- (i) **The same token under different governance lenses** (i.e., `0xc92e8fc2…` is both Mento-protocol-issued AND distributed under the Minteo brand); OR
- (ii) **Two separate tokens** — `0xc92e8fc2…` is the Minteo-fintech fiat-backed COPM (reserved by Colombian banks, BDO-audited per TR Finding 3); `0x8A567e2a…` is the Mento-protocol-native COPm (Mento Reserve overcollateralized basket model).

**Why this matters for the registry-lock deliverable.** The Rev-5.3.4 RESCOPE deliverable (sub-task 3 spec doc) is the byte-exact-immutable source-of-truth for downstream β-track and α-track artifacts under §B-3 of the sub-plan. Locking the wrong address into the registry would corrupt every downstream consumer. The user-correction event of 2026-04-25 ("is COPM not cCOP") tightened scope to "Mento-native only" — but did NOT confirm which of the two on-chain addresses qualifies as Mento-native. The Mento V3 docs themselves explicitly point at `0x8A567e2a…`, not `0xc92e8fc2…`, contradicting the project-memory entry the user appeared to ratify.

**HALT directive.** This memo records both candidate addresses with their full provenance and DOES NOT silently choose one over the other. The sub-task-1 acceptance criterion under §C of the sub-plan reads verbatim: *"Where the audit discovers a discrepancy between project-memory addresses and on-chain reality, the discrepancy HALTS to the user immediately per `feedback_pathological_halt_anti_fishing_checkpoint` rather than being silently overridden in the memo."* That clause fires here. The user is asked to disambiguate one of the following resolutions before sub-task 3 (the registry-lock spec doc) is dispatched:

1. **Resolution α — `0xc92e8fc2…` is canonical-Mento for Abrigo** (current project memory + Rev-5.3.4 user correction stand). Justification needed: explain why Mento V3 docs label `0x8A567e2a…` as `StableTokenCOP` and the Celo Token List labels `0xc92e8fc2…` as "COP Minteo" if the latter is Mento-protocol native. One reading: `0xc92e8fc2…` IS Mento-issued and the Celo Token List "COP Minteo" name is a marketing alias under a Minteo-fintech distribution wrapper. This must be confirmed against Mento Reserve disclosures or governance records, not asserted.
2. **Resolution β — `0x8A567e2a…` is canonical-Mento; `0xc92e8fc2…` is the partner/fintech (Minteo) deployment**, OUT of scope per `project_abrigo_mento_native_only`. This implies `onchain_copm_transfers` (110,253 events filtered on `0xc92e8fc2…`) tracks an out-of-scope token; the Rev-5.3.2 published estimates and the 10 `onchain_xd_weekly` `proxy_kind` values (which use the legacy slug `copm`) are computed against the wrong address. This is a major scope/integrity event and triggers a downstream re-ingest decision under `feedback_pathological_halt_anti_fishing_checkpoint`. Per §B-1 of the sub-plan, Rev-5.3.2 published estimates remain byte-exact through this sub-plan; the impact is felt only in NEW β-track / α-track work that consumes the registry.
3. **Resolution γ — both addresses are in scope as separate-but-related Mento-ecosystem instruments.** Project memory must be amended to record both with disambiguating tickers (e.g., `COPM-Minteo` for `0xc92e8fc2…` and `COPm-Mento` for `0x8A567e2a…`). The registry doc must enumerate both. The basket scope must be explicitly defined per-instrument.

The author of THIS memo does not select among α / β / γ; that is a user decision with downstream rev consequences.

---

## Per-token sections (Mento-native basket)

### 1. COPM / Colombian peso (HALT-VERIFY pending — see above)

| Field | Value | Verification |
|---|---|---|
| Canonical post-rebrand ticker | COPM (per `project_mento_canonical_naming_2026`) | Project memory; user correction 2026-04-25 |
| Pre-rebrand legacy ticker | "unchanged" per project memory; in legacy plan artefacts also referred to as cCOP, but Rev-5.3.4 corrigendum nullifies the cCOP attribution | Project memory + sub-plan §A |
| Primary candidate address | `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606` (case-checksummed via Celo Token List) | Live DuckDB `onchain_copm_transfers`: 110,253 events; first observed 2024-09-17 block `27,786,128`; ~4.94B units minted across 147 mint events |
| Alternate canonical-Mento candidate (per Mento docs) | `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` | Mento V3 deployments docs query: "documented StableTokenCOP on Celo Mainnet … canonical Mento Colombian Peso address in the deployments list" |
| Celo Token List entry (chainId 42220) — primary candidate | "COP Minteo" / `COPM` / 18 decimals | `https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json` retrieved 2026-04-26 |
| Celo Token List entry (chainId 42220) — alternate candidate | "Mento Colombian Peso" / `COPm` / 18 decimals | Same source |
| First-observed-on-chain (primary candidate) | 2024-09-17, block `27,786,128`, mint of 1,000,000 units to `0x0155b191ec52728d26b1cd82f6a412d5d6897c04` | Live DuckDB `onchain_copm_transfers` ORDER BY evt_block_number ASC LIMIT 1 — verifiable via `SELECT evt_block_date, evt_block_number, from_address, to_address, value_wei FROM onchain_copm_transfers WHERE from_address = '0x0000000000000000000000000000000000000000' ORDER BY evt_block_number ASC LIMIT 1` |
| Mento Reserve relationship | UNRESOLVED pending HALT-VERIFY α/β/γ user decision; mint manager `0x0155b191…7c04` is the recipient of the earliest mints (likely a Reserve-side proxy or distributor; not yet identity-confirmed in this sub-task) | Live DuckDB |
| Basket-membership status | Currently consumed under proxy_kind `carbon_per_currency_copm_volume_usd` in `onchain_xd_weekly` (82 weeks); legacy slug pre-2026-rebrand intentionally not mass-renamed per `project_mento_canonical_naming_2026` | Live DuckDB `SELECT DISTINCT proxy_kind FROM onchain_xd_weekly` |
| Total supply | OUT OF SCOPE per Rev-5.3.4 RESCOPE + RC R-3 (registry-immutability hygiene); query live for current supply | n/a |

**Verification block (primary candidate `0xc92e8fc2…`).**
- Address text-match against `project_mento_canonical_naming_2026`: **PASS** (memo line 13 verbatim).
- Live DuckDB row count (read-only): **PASS** — 110,253 events covering 587 days; consistent with a live, in-use token contract.
- Celoscan WebFetch direct verification: **DEFERRED** — Celoscan returned HTTP 403 for unauthenticated WebFetch in this sub-task (rate-limit-class block); cross-confirmation falls back to (a) Celo Token List JSON registry; (b) live DuckDB observability of mint/burn/transfer activity; (c) Task 11.N.2b.1 gate-decision memo §1 which records prior-task Celoscan verification (status OK).
- HALT-VERIFY ambiguity vs. `0x8A567e2a…`: **PRESENT — surfaced above; not resolved in this memo.**

---

### 2. USDm / US Dollar (Mento Dollar)

| Field | Value | Verification |
|---|---|---|
| Canonical post-rebrand ticker | USDm | `project_mento_canonical_naming_2026` |
| Pre-rebrand legacy ticker | cUSD | Project memory + Mento V3 deployments docs |
| Contract address (Celo, chainId 42220) | `0x765DE816845861e75A25fCA122bb6898B8B1282a` | Celo Token List ("Mento Dollar" / `USDm` / 18 decimals); Mento V3 deployments docs query confirms `0x765de816845861e75a25fca122bb6898b8b1282a` as USDm; Task 11.N.2b.1 gate-decision memo §1 records prior Celoscan verification |
| First-observed-on-chain date | NOT directly probed in this sub-task; Celo Dollar (cUSD) is one of the earliest Mento deployments (2020 era; Celo Deployer) per industry-known history; precise deployment date deferred to live Celoscan query at consumption time | Mento V3 docs reference; Task 11.N.2b.1 memo §1 ("plan-provisional matches; Celo token list confirms") |
| Mento Reserve relationship | Reserve-collateralized stable; one of the original Mento basket stables | Mento V3 deployments docs ("USDm collateral $806,039 outstanding" per reserve.mento.org dashboard) |
| Basket-membership status | Active in `onchain_xd_weekly` proxy_kind `carbon_per_currency_usdm_volume_usd` (82 weeks of pre-aggregated cells) | Live DuckDB |
| Total supply | OUT OF SCOPE per Rev-5.3.4 RESCOPE | n/a |

**Verification block.**
- Address text-match against `project_mento_canonical_naming_2026` line 9: **PASS** (case-folding equivalent — memo lowercase, Token List checksum-cased).
- Mento V3 deployments docs query: **PASS** — exact address `0x765de816845861e75a25fca122bb6898b8b1282a` returned for USDm.
- Celo Token List entry: **PASS** ("Mento Dollar" / `USDm` / 18 decimals at chainId 42220).
- Task 11.N.2b.1 gate-decision memo §1: **PASS** (status OK, prior-task Celoscan verification).
- Celoscan direct WebFetch: **DEFERRED** (HTTP 403 for unauthenticated fetch in this sub-task; redundant with the three PASS verifications above).

---

### 3. EURm / Euro (Mento Euro)

| Field | Value | Verification |
|---|---|---|
| Canonical post-rebrand ticker | EURm | `project_mento_canonical_naming_2026` |
| Pre-rebrand legacy ticker | cEUR | Project memory + Mento docs |
| Contract address (Celo) | `0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73` | Celo Token List ("Mento Euro" / `EURm` / 18 decimals); Mento V3 deployments docs query confirms `0xd8763cba276a3738e6de85b4b3bf5fded6d6ca73`; Task 11.N.2b.1 memo §1 records prior Celoscan verification |
| First-observed-on-chain date | One of the original Mento basket stables (cEUR launched alongside cUSD); precise date deferred to live Celoscan at consumption time | Mento V3 docs |
| Mento Reserve relationship | Reserve-collateralized; original Mento basket stable | Mento V3 deployments docs |
| Basket-membership status | Active in `onchain_xd_weekly` proxy_kind `carbon_per_currency_eurm_volume_usd` (82 weeks) | Live DuckDB |
| Total supply | OUT OF SCOPE per Rev-5.3.4 RESCOPE | n/a |

**Verification block.**
- Address text-match against `project_mento_canonical_naming_2026` line 10: **PASS**.
- Mento V3 deployments docs query: **PASS**.
- Celo Token List entry: **PASS**.
- Task 11.N.2b.1 gate-decision memo §1: **PASS**.
- Celoscan direct WebFetch: **DEFERRED** (same rationale as USDm).

---

### 4. BRLm / Brazilian Real (Mento Brazilian Real)

| Field | Value | Verification |
|---|---|---|
| Canonical post-rebrand ticker | BRLm | `project_mento_canonical_naming_2026` |
| Pre-rebrand legacy ticker | cREAL | Project memory + Mento docs |
| Contract address (Celo) | `0xe8537a3d056DA446677B9E9d6c5dB704EaAb4787` | Celo Token List ("Mento Brazilian Real" / `BRLm` / 18 decimals); Mento V3 deployments docs query confirms `0xe8537a3d056da446677b9e9d6c5db704eaab4787`; Task 11.N.2b.1 memo §1 (Celoscan: "Mento Brazilian Real, EIP-1967 proxy") |
| First-observed-on-chain date | Launched 2022 era; precise date deferred to live Celoscan at consumption time | Mento V3 docs; industry-known launch year |
| Mento Reserve relationship | Reserve-collateralized; second-generation Mento basket stable (post-cUSD/cEUR) | Mento V3 deployments docs |
| Basket-membership status | Active in `onchain_xd_weekly` proxy_kind `carbon_per_currency_brlm_volume_usd` (82 weeks) | Live DuckDB |
| Total supply | OUT OF SCOPE per Rev-5.3.4 RESCOPE | n/a |

**Verification block.**
- Address text-match against `project_mento_canonical_naming_2026` line 11: **PASS**.
- Mento V3 deployments docs query: **PASS**.
- Celo Token List entry: **PASS** (note: omitted from older Celo token-list snapshots per Task 11.N.2b.1 memo §1; the canonical 2026-04-26 retrieval includes it).
- Task 11.N.2b.1 gate-decision memo §1: **PASS** (Celoscan token-page label confirmed at prior task).
- Celoscan direct WebFetch: **DEFERRED**.

---

### 5. KESm / Kenyan Shilling (Mento Kenyan Shilling)

| Field | Value | Verification |
|---|---|---|
| Canonical post-rebrand ticker | KESm | `project_mento_canonical_naming_2026` |
| Pre-rebrand legacy ticker | cKES | Project memory + Mento docs |
| Contract address (Celo) | `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` | Celo Token List ("Mento Kenyan Shilling" / `KESm` / 18 decimals); Mento V3 deployments docs query confirms `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0`; Task 11.N.2b.1 memo §1 records RC-empirical canonical-form match against truncated `0x456a3D04…3B0d0` prefix |
| First-observed-on-chain date | Launched as part of the Africa-focus expansion (post-MiniPay-Kenya); precise date deferred to live Celoscan at consumption time | Industry-known launch context (TR research §1.1 — Kenya is MiniPay #1 free app Q4 2024) |
| Mento Reserve relationship | Reserve-collateralized; Africa-tier Mento basket stable | Mento V3 deployments docs |
| Basket-membership status | Active in `onchain_xd_weekly` proxy_kind `carbon_per_currency_kesm_volume_usd` (82 weeks) | Live DuckDB |
| Total supply | OUT OF SCOPE per Rev-5.3.4 RESCOPE | n/a |

**Verification block.**
- Address text-match against `project_mento_canonical_naming_2026` line 12: **PASS**.
- Mento V3 deployments docs query: **PASS**.
- Celo Token List entry: **PASS**.
- Task 11.N.2b.1 gate-decision memo §1: **PASS**.
- Celoscan direct WebFetch: **DEFERRED**.

---

### 6. XOFm / West African CFA franc (Mento West African CFA franc)

| Field | Value | Verification |
|---|---|---|
| Canonical post-rebrand ticker | XOFm | `project_mento_canonical_naming_2026` |
| Pre-rebrand legacy ticker | eXOF (the trailing "m" tail is unchanged per project memory line 14) | Project memory + Mento docs |
| Contract address (Celo) | `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08` | Celo Token List ("Mento West African CFA franc" / `XOFm` / 18 decimals); Mento V3 deployments docs query confirms `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08`; Task 11.N.2b.1 memo §1 records RC-empirical canonical-form match against truncated `0x73f93dcc…f29a08` prefix |
| First-observed-on-chain date | Launched as part of Africa expansion; precise date deferred to live Celoscan at consumption time | Industry-known launch context |
| Mento Reserve relationship | Reserve-collateralized; Africa-tier Mento basket stable | Mento V3 deployments docs |
| Basket-membership status | Active in `onchain_xd_weekly` proxy_kind `carbon_per_currency_xofm_volume_usd` (82 weeks) | Live DuckDB |
| Total supply | OUT OF SCOPE per Rev-5.3.4 RESCOPE | n/a |

**Verification block.**
- Address text-match against `project_mento_canonical_naming_2026` line 14: **PASS**.
- Mento V3 deployments docs query: **PASS**.
- Celo Token List entry: **PASS**.
- Task 11.N.2b.1 gate-decision memo §1: **PASS**.
- Celoscan direct WebFetch: **DEFERRED**.

---

## Summary table (all six Mento-native tokens)

| Ticker | Address | Legacy ticker | Celo Token List name | Verification status |
|---|---|---|---|---|
| **COPM** (HALT) | `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606` | "unchanged" per project memory; legacy plans referred to it as cCOP (corrigendum'd) | "COP Minteo" | **HALT-VERIFY** vs. Mento docs canonical `0x8A567e2a…` |
| USDm | `0x765DE816845861e75A25fCA122bb6898B8B1282a` | cUSD | Mento Dollar | PASS (3 sources concur) |
| EURm | `0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73` | cEUR | Mento Euro | PASS (3 sources concur) |
| BRLm | `0xe8537a3d056DA446677B9E9d6c5dB704EaAb4787` | cREAL | Mento Brazilian Real | PASS (3 sources concur) |
| KESm | `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` | cKES | Mento Kenyan Shilling | PASS (3 sources concur) |
| XOFm | `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08` | eXOF | Mento West African CFA franc | PASS (3 sources concur) |

---

## Out-of-scope tokens (recorded for the registry's exclusion list under sub-task 3)

The Mento V3 deployments docs and Celo Token List enumerate **additional** Mento-native stablecoins beyond the Abrigo basket. Per `project_abrigo_mento_native_only`, the basket is **scope-frozen** at the six-token list above; the following are recorded here for the sub-task 3 spec doc's explicit out-of-scope-list section so future research does not silently expand scope:

- **PHPm** (Mento Philippine Peso) — `0x105d4A9306D2E55a71d2Eb95B81553AE1dC20d7B`
- **GHSm** (Mento Ghanaian Cedi) — `0xfaea5f3404bba20d3cc2f8c4b0a888f55a3c7313`
- **GBPm** (Mento British Pound) — `0xCCF663b1fF11028f0b19058d0f7B674004a40746`
- **ZARm** (Mento South African Rand) — `0x4c35853A3B4e647fD266f4de678dCc8fEC410BF6`
- **CADm** (Mento Canadian Dollar) — `0xff4Ab19391af240c311c54200a492233052B6325`
- **AUDm** (Mento Australian Dollar) — `0x7175504C455076F15c04A2F90a8e352281F492F9`
- **CHFm** (Mento Swiss Franc) — `0xb55a79F398E759E43C95b979163f30eC87Ee131D`
- **JPYm** (Mento Japanese Yen) — `0xc45eCF20f3CD864B32D9794d6f76814aE8892e20`
- **NGNm** (Mento Nigerian Naira) — `0xE2702Bd97ee33c88c8f6f92DA3B733608aa76F71`

These are Mento-protocol native (per the V3 deployments docs and Celo Token List) but are **not** in the Abrigo basket per the inequality-hedge thesis (`project_abrigo_inequality_hedge_thesis`) and the underserved-FX-country product framing (`project_ran_product_framing`). Adding any of them to the basket is a future-revision scope decision; the registry doc (sub-task 3) records them in the explicit out-of-scope list so the boundary is clear.

---

## Verification methodology summary (per `feedback_real_data_over_mocks` — real data only)

Each address in this memo was triangulated against at least three independent sources where available:

1. **Project memory** — `project_mento_canonical_naming_2026` (the canonical post-rebrand registry, user-ratified at memo authoring time).
2. **Celo Token List** — `https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json` retrieved 2026-04-26 (chainId 42220 registry).
3. **Mento V3 deployments docs** — `https://docs.mento.org/mento-v3/build/deployments.md?ask=…` query API.
4. **Live DuckDB** — `contracts/data/structural_econ.duckdb` at HEAD `865402c2c`; tables `onchain_copm_transfers`, `onchain_xd_weekly`, `onchain_carbon_tokenstraded`, `onchain_carbon_arbitrages`. Read-only mode.
5. **Prior task corroboration** — `contracts/.scratch/2026-04-25-carbon-basket-gate-decision-memo.md` §1 (Task 11.N.2b.1 ten-address verification table with Celoscan + Celo token-list cross-reference; HALT-VERIFY resolutions on USDT and WETH already closed under Task 11.N.2b.1).

**Celoscan direct WebFetch** returned HTTP 403 for unauthenticated fetches in this sub-task (rate-limit-class block). Per `feedback_pathological_halt_anti_fishing_checkpoint`, this is documented as a methodological constraint, not silently masked. The five-source triangulation above (project memory, Celo Token List, Mento V3 docs, live DuckDB, prior-task gate-decision memo) provides adequate provenance for the five non-COPM tokens; the COPM HALT-VERIFY is independent of the Celoscan-403 issue.

**No data was synthesized.** Every cited row count, block number, transfer address, and basket-membership statistic was retrieved from live DuckDB at HEAD `865402c2c` via read-only `SELECT` queries, executable verbatim against the canonical `contracts/data/structural_econ.duckdb` file. Every cited address is bytes-equivalent to the corresponding entry in either the Celo Token List JSON registry or the Mento V3 deployments docs (case-folded comparison; the memo preserves checksum casing where the registry source provided it).

---

## Reviewer instructions (Reality Checker spot-check, single-pass advisory)

Per sub-plan §C sub-task 1 reviewer assignment: Reality Checker single-pass advisory spot-check of this memo. The RC's verification scope is:

1. Each enumerated address text-matches `project_mento_canonical_naming_2026` (case-folded comparison).
2. Each provenance citation resolves (the Celo Token List URL, the Mento V3 docs URL, the live DuckDB queries, the gate-decision memo §1 reference).
3. The HALT-VERIFY block above is not silently overridden — the user-decision-required disposition stands until the user resolves α/β/γ.
4. The five non-HALT tokens (USDm, EURm, BRLm, KESm, XOFm) carry triangulated three-source verification (project memory + Celo Token List + Mento V3 docs).
5. The Celoscan-403 mitigation (deferred-to-prior-task-gate-memo + three-source triangulation) is judged adequate for sub-task-1 grade (intermediate research artifact); if RC judges it inadequate, an addendum can be appended noting the gap for the sub-task-3 trio review.

---

## Audit-trail footer

- This memo: `contracts/.scratch/2026-04-25-mento-native-address-inventory.md`
- Sub-plan: `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` @ HEAD `bf69a18f8`
- Major plan anchor: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` Task 11.P.MR-β.1 (Rev-5.3.4 CORRIGENDUM)
- Prior cross-reference: `contracts/.scratch/2026-04-25-carbon-basket-gate-decision-memo.md` §1
- Live DuckDB at memo authoring time: `contracts/data/structural_econ.duckdb` at git HEAD `865402c2c`
- Project memory anchors: `project_mento_canonical_naming_2026`, `project_abrigo_mento_native_only`, `project_carbon_defi_attribution_celo`, `project_carbon_user_arb_partition_rule`, `project_usdt_celo_canonical_address`
- Reviewer assignment per sub-plan §C-sub-task-1: Reality Checker single-pass spot-check (advisory)
- Downstream consumer: sub-task 2 (DuckDB table-to-address audit) and sub-task 3 (canonical address-registry spec doc, byte-exact-immutable post-converge under §B-3)

**End of inventory memo.**
