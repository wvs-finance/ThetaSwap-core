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

---

## §β-rescope (Rev-5.3.5, 2026-04-26)

**Anchors.** The HALT-VERIFY GATE raised in §"CRITICAL HALT-VERIFY GATE: Colombian-peso address ambiguity" above was resolved by the user under disposition β. This section appends the rescoped Mento-native address inventory; the prior content of this memo is preserved unchanged in the audit trail per `feedback_pathological_halt_anti_fishing_checkpoint` anti-fishing-on-memory-edits append-only-or-section-replace-with-corrigendum discipline.

**Disposition source documents (cite in this order for re-verification):**
- Major plan Rev-5.3.5 CORRECTIONS block: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (file end)
- HALT-resolution disposition memo: `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` (disposition commit `00790855b`)
- 3-way review trio (post-disposition): `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-{code-reviewer,reality-checker,technical-writer}.md`
- RC re-review on fix-up bundle: trio convergence at commit `b4a6a50e6`
- Prior-dispatch DE deliverable (this file's pre-§β-rescope content): commit `3611b0716`

**Per-key disposition.** `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` is canonical Mento-native COPm (Mento V2 `StableTokenCOP`); `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` is the Minteo-fintech "COP Minteo" token, **out of Mento-native scope** per `project_abrigo_mento_native_only`. Resolution α and γ from the prior HALT-VERIFY block are SUPERSEDED.

---

### §β-rescope.1 — In-scope Mento-native address inventory (post-disposition)

**Count = 6 tokens. Total supply field deliberately omitted from every entry per RC R-3 immutability hygiene (sub-plan §B-3 + sub-task 1 acceptance).** Auditors needing live circulating supply must query DuckDB / Celoscan / Dune at consumption time; this memo is the byte-exact-immutable address-identity registry, not a supply dashboard.

#### 1. COPm — Mento Colombian Peso (NEW canonical Mento-native, post-β disposition)

| Field | Value |
|---|---|
| Canonical post-rebrand ticker | COPm (lowercase final m) |
| Pre-rebrand legacy ticker | unchanged (no pre-rebrand legacy variant; deployed natively as Mento V2 `StableTokenCOP`) |
| Contract address (Celo, chainId 42220) | `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` |
| First-observed-on-chain | 2024-10-31 16:35:48 UTC (Dune query 7378788, β-feasibility probe; activity through 2026-04-26 21:12:59 UTC at disposition time; 285,390 transfers; 5,015 distinct senders; 16,918 distinct receivers; 78 weeks of activity) |
| Mento Reserve relationship | Reserve-collateralized; canonical Mento V2 `StableTokenCOP` (Mento-protocol governance events `evt_exchangeupdated`, `evt_validatorsupdated`, `evt_brokerupdated`, `evt_initialized` decoded under Dune project `celocolombianpeso`) |
| Basket-membership status | NEW in-scope under Rev-5.3.5; β-track Rev-3 ingestion plumbing pointed at this address is authored under Task 11.P.spec-β + Task 11.P.exec-β (NOT under MR-β.1; sub-plan §G-3 reaffirms editorial-only scope) |
| Provenance citations (primary on-chain) | Dune query 7378788 (β-feasibility probe, 0.012 credits free-tier) — recorded in disposition memo §3.2; RC re-review queries 7379527 (joint-coverage feasibility) + 7379530 (governance-event verification); Dune project `celocolombianpeso` decoded as `StableTokenV2` |
| Provenance citations (secondary docs) | Mento V3 deployments docs (working URL post-RC-3 verification): `https://docs.mento.org/mento-v3/build/deployments/addresses.md` — `StableTokenCOP` canonical address. The legacy URL `https://docs.mento.org/mento/protocol/deployments` 404s and is superseded |
| Provenance citations (token registry) | Celo Token List (chainId 42220) WebFetch retrieved 2026-04-26: `name = "Mento Colombian Peso"`, `symbol = "COPm"`, `decimals = 18`; URL `https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json` |
| RC-3 cross-strengthening | All six Mento StableTokens share implementation `0x434563B0604BE100F04B7Ae485BcafE3c9D8850E` (RC re-review independent finding) |

#### 2. USDm — Mento Dollar

| Field | Value |
|---|---|
| Canonical post-rebrand ticker | USDm |
| Pre-rebrand legacy ticker | cUSD |
| Contract address (Celo, chainId 42220) | `0x765DE816845861e75A25fCA122bb6898B8B1282a` |
| First-observed-on-chain | 2020-04-22 20:21:03 UTC (block `2961`); ~835.6M transfers cumulative as of 2026-04-26 (DE re-dispatch Dune query 7379578 against `mento_celo.stabletoken_evt_transfer`) |
| Mento Reserve relationship | Reserve-collateralized; one of the two original Mento V1 basket stables (cUSD + cEUR) |
| Basket-membership status | Active; consumed under `onchain_xd_weekly` proxy_kind `carbon_per_currency_usdm_volume_usd` (82 weeks pre-aggregated). β-track Rev-3 will continue to consume USDm at the same address (no β-disposition impact) |
| Provenance citations (primary on-chain) | DE re-dispatch Dune query 7379578 (`free` tier, 0.906 credits) — first-transfer + cumulative-volume probe |
| Provenance citations (secondary docs) | Mento V3 deployments docs at `https://docs.mento.org/mento-v3/build/deployments/addresses.md`; Task 11.N.2b.1 gate-decision memo §1 (prior Celoscan verification, status OK) |
| Provenance citations (token registry) | Celo Token List 2026-04-26: `name = "Mento Dollar"`, `symbol = "USDm"`, `decimals = 18` |

#### 3. EURm — Mento Euro

| Field | Value |
|---|---|
| Canonical post-rebrand ticker | EURm |
| Pre-rebrand legacy ticker | cEUR |
| Contract address (Celo, chainId 42220) | `0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73` |
| First-observed-on-chain | 2021-03-25 15:38:05 UTC (block `5,822,108`); ~19.3M transfers cumulative as of 2026-04-26 (DE re-dispatch Dune query 7379585 against `mento_celo.stabletokeneur_evt_transfer`) |
| Mento Reserve relationship | Reserve-collateralized; second of the two original Mento V1 basket stables (deployed alongside cUSD; first transfer ~11 months after cUSD genesis) |
| Basket-membership status | Active; consumed under `onchain_xd_weekly` proxy_kind `carbon_per_currency_eurm_volume_usd` (82 weeks pre-aggregated) |
| Provenance citations (primary on-chain) | DE re-dispatch Dune query 7379585 (`free` tier, 0.075 credits) — UNION-ALL probe over per-token decoded tables |
| Provenance citations (secondary docs) | Mento V3 deployments docs; Task 11.N.2b.1 gate-decision memo §1 |
| Provenance citations (token registry) | Celo Token List 2026-04-26: `name = "Mento Euro"`, `symbol = "EURm"`, `decimals = 18` |

#### 4. BRLm — Mento Brazilian Real

| Field | Value |
|---|---|
| Canonical post-rebrand ticker | BRLm |
| Pre-rebrand legacy ticker | cREAL |
| Contract address (Celo, chainId 42220) | `0xe8537a3d056DA446677B9E9d6c5dB704EaAb4787` |
| First-observed-on-chain | 2021-12-15 21:45:22 UTC (block `10,405,343`); ~6.4M transfers cumulative as of 2026-04-26 (DE re-dispatch Dune query 7379585 against `mento_celo.stabletokenbrl_evt_transfer`) |
| Mento Reserve relationship | Reserve-collateralized; first second-generation Mento basket stable (post-cUSD/cEUR; deployed ~8 months after cEUR) |
| Basket-membership status | Active; consumed under `onchain_xd_weekly` proxy_kind `carbon_per_currency_brlm_volume_usd` (82 weeks pre-aggregated) |
| Provenance citations (primary on-chain) | DE re-dispatch Dune query 7379585 — UNION-ALL probe |
| Provenance citations (secondary docs) | Mento V3 deployments docs; Task 11.N.2b.1 gate-decision memo §1 (Celoscan label "Mento Brazilian Real, EIP-1967 proxy") |
| Provenance citations (token registry) | Celo Token List 2026-04-26: `name = "Mento Brazilian Real"`, `symbol = "BRLm"`, `decimals = 18` |

#### 5. KESm — Mento Kenyan Shilling

| Field | Value |
|---|---|
| Canonical post-rebrand ticker | KESm |
| Pre-rebrand legacy ticker | cKES |
| Contract address (Celo, chainId 42220) | `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` |
| First-observed-on-chain | 2024-05-21 14:10:00 UTC (block `25,725,915`); ~3.2M transfers cumulative as of 2026-04-26 (DE re-dispatch Dune query 7379585 against `ckes_mento_celo.stabletokenv2_evt_transfer`) |
| Mento Reserve relationship | Reserve-collateralized; Africa-tier Mento basket stable (StableTokenV2 implementation) |
| Basket-membership status | Active; consumed under `onchain_xd_weekly` proxy_kind `carbon_per_currency_kesm_volume_usd` (82 weeks pre-aggregated) |
| Provenance citations (primary on-chain) | DE re-dispatch Dune query 7379585 — UNION-ALL probe |
| Provenance citations (secondary docs) | Mento V3 deployments docs |
| Provenance citations (token registry) | Celo Token List 2026-04-26: `name = "Mento Kenyan Shilling"`, `symbol = "KESm"`, `decimals = 18` |

#### 6. XOFm — Mento West African CFA franc

| Field | Value |
|---|---|
| Canonical post-rebrand ticker | XOFm |
| Pre-rebrand legacy ticker | unchanged (deployed under tail-`m` from genesis; `eXOF` was an external-marketplace alias never used in `project_mento_canonical_naming_2026`) |
| Contract address (Celo, chainId 42220) | `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08` |
| First-observed-on-chain | 2023-10-16 15:12:02 UTC (block `21,960,106`); ~2.4M transfers cumulative as of 2026-04-26 (DE re-dispatch Dune query 7379590 against `erc20_celo.evt_transfer` filtered to the proxy address; XOFm uses a `StableTokenXOFProxy` decoded structure that does not expose its own `evt_transfer` table) |
| Mento Reserve relationship | Reserve-collateralized; Africa-tier Mento basket stable (proxy → StableTokenV2 implementation) |
| Basket-membership status | Active; consumed under `onchain_xd_weekly` proxy_kind `carbon_per_currency_xofm_volume_usd` (82 weeks pre-aggregated) |
| Provenance citations (primary on-chain) | DE re-dispatch Dune query 7379590 (`free` tier, 1.866 credits) — `erc20_celo.evt_transfer` filter on proxy address |
| Provenance citations (secondary docs) | Mento V3 deployments docs |
| Provenance citations (token registry) | Celo Token List 2026-04-26: `name = "Mento West African CFA franc"`, `symbol = "XOFm"`, `decimals = 18` |

---

### §β-rescope.2 — Out-of-scope third-party token (audit-trail preservation)

**Count = 1 token.** Recorded for the registry's exclusion list under sub-task 3 + audit-trail preservation; `onchain_copm_transfers` (110,253 events) and the `carbon_per_currency_copm_volume_usd` proxy_kind in `onchain_xd_weekly` remain in DuckDB unchanged (sub-task 2 will tag these tables `DEFERRED-via-scope-mismatch` per disposition memo §4.4).

#### 7. COPM-Minteo — out-of-scope (Minteo-fintech, third-party)

| Field | Value |
|---|---|
| Ticker (Celo Token List) | COPM (uppercase final M) — distinct from Mento-native COPm |
| Celo Token List name | "COP Minteo" |
| Contract address (Celo, chainId 42220) | `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606` |
| Scope tag | OUT OF Mento-native scope per `project_abrigo_mento_native_only` (β-corrigendum at file top) and Rev-5.3.5 CORRECTIONS block in major plan |
| Brief provenance | Celo Token List entry "COP Minteo" / `COPM` / 18 decimals at chainId 42220; Rev-2 X_d data source — 110,253 transfers ingested into `onchain_copm_transfers` (covering 2024-09-17 → 2026-04-25) and 147 mint events totalling ~4.94B units; the Rev-2 `carbon_per_currency_copm_volume_usd` proxy_kind in `onchain_xd_weekly` was computed against this address |
| Audit-trail status | Rev-2 published estimates (β̂ = −2.7987e−8, n = 76, T3b FAIL, MDES_FORMULATION_HASH `4940360dcd2987…cefa`, decision_hash `6a5f9d1b05c1…443c`) remain byte-exact immutable per Rev-5.3.x anti-fishing invariants. Re-interpretation under β: Rev-2 closes as **scope-mismatch** (measured the wrong address), NOT as "Mento-hedge-thesis-tested-and-failed" |
| Reserve / basket / issuance fields | NOT APPLICABLE — Mento-protocol fields are not enumerated for an out-of-scope third-party token |

---

### §β-rescope.3 — HALT-VERIFY discipline reaffirmation

**This dispatch HALT-clears under β.** Every Mento-native address recorded in §β-rescope.1 byte-matches `project_mento_canonical_naming_2026` β-corrigendum block at the file top:
- COPm `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` — matches β-corrigendum (NEW Mento-native canonical address)
- USDm `0x765DE816845861e75A25fCA122bb6898B8B1282a` — matches pre-existing memory entry (case-folded)
- EURm `0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73` — matches pre-existing memory entry (case-folded)
- BRLm `0xe8537a3d056DA446677B9E9d6c5dB704EaAb4787` — matches pre-existing memory entry (case-folded)
- KESm `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` — matches pre-existing memory entry
- XOFm `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08` — matches pre-existing memory entry

**The prior HALT-VERIFY GATE remains in the audit trail unchanged** (the §"CRITICAL HALT-VERIFY GATE: Colombian-peso address ambiguity" block above is preserved verbatim per anti-fishing-on-memory-edits append-only discipline). The disposition resolution sits in this §β-rescope appendix; the prior gate-firing content stays as the empirical evidence that triggered the gate.

**No anti-fishing invariant relaxed.** N_MIN = 75, POWER_MIN = 0.80, MDES_SD = 0.40, MDES_FORMULATION_HASH = `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa`, decision_hash = `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c`, Rev-2 14-row resolution matrix all unchanged. The disposition is a **scope correction**, not a threshold relaxation.

**RC-8 forward-looking joint-coverage note (deferred to β-spec, not actionable here).** The 78-week activity window for COPm `0x8A567e2a…` (2024-10-31 → 2026-04-26 live) is X_d-only-conditioned. Joint with the live Y₃ panel (panel max date 2026-03-27 per `project_y3_inequality_differential_design`), the chronological joint window is approximately **73 weeks — 2 weeks short of N_MIN=75**. This does NOT block this MR-β.1 sub-task 1 deliverable (Rev-2 closes scope-mismatch on byte-exact-immutable estimates; the disposition is independent of β-track Rev-3's joint-N feasibility). It is recorded here as a forward-looking constraint that β-spec MUST address at authoring time, with two natural resolutions: (a) refresh the Y₃ panel forward by ≥3 weeks before β-spec data freeze, OR (b) document the joint-N shortfall and pre-commit to a relaxation-or-defer disposition under the established `feedback_pathological_halt_anti_fishing_checkpoint` discipline (no silent threshold tuning). Cross-reference: disposition memo §4.2.

---

### §β-rescope.4 — Audit-trail cross-references

- This memo: `contracts/.scratch/2026-04-25-mento-native-address-inventory.md`
- Disposition memo: `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` (commit `00790855b`)
- Prior-dispatch DE deliverable (HALT-VERIFY-firing memo, content preserved above): commit `3611b0716`
- RC sub-task 1 spot-check (single-pass advisory): `contracts/.scratch/2026-04-25-subtask-mr-beta-1-1-rc-spot-check.md` (commit `3286dfe66`) — empirical β-advisory
- 3-way review trio on disposition (CR + RC + TW): `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-{code-reviewer,reality-checker,technical-writer}.md`
- RC re-review on fix-up bundle (trio convergence): commit `b4a6a50e6`
- Major plan Rev-5.3.5 CORRECTIONS block: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (file-end CORRECTIONS section)
- MR-β.1 sub-plan §I CORRECTIONS Rev-5.3.5: `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md`
- NB-α sub-plan CORRECTIONS Rev-5.3.5: `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md`
- Project memory β-corrigenda: `project_mento_canonical_naming_2026` (β-corrigendum block at file top), `project_abrigo_mento_native_only` (β-corrigendum extension)
- Live DuckDB at re-dispatch authoring time: `contracts/data/structural_econ.duckdb` at git HEAD `865402c2c`+ (no row mutations under MR-β.1 per sub-plan §G-3)

**Dune queries cited (re-dispatch + disposition):**
- 7378788 — β-feasibility activity probe on `0x8A567e2a…` (disposition memo §3.2; 285K transfers, 78 weeks, 5K senders, 16K receivers)
- 7379527 — RC re-review joint-coverage feasibility (RC re-review)
- 7379530 — RC re-review governance-event verification (RC re-review)
- 7379578 — DE re-dispatch USDm first-transfer probe via `mento_celo.stabletoken_evt_transfer` (this memo §β-rescope.1 entry 2)
- 7379585 — DE re-dispatch UNION-ALL probe for EURm/BRLm/KESm via per-token decoded tables (this memo §β-rescope.1 entries 3-5)
- 7379590 — DE re-dispatch XOFm first-transfer probe via `erc20_celo.evt_transfer` filter (this memo §β-rescope.1 entry 6)

**RC spot-check on this re-dispatch deliverable (single-pass advisory per RC R-4 in MR-β.1 sub-plan §H CORRECTIONS).** The RC's verification scope on this §β-rescope appendix:
1. All seven enumerated addresses (6 in-scope + 1 out-of-scope) byte-match `project_mento_canonical_naming_2026` β-corrigendum block (case-folded comparison).
2. The 6 in-scope tokens carry primary on-chain provenance (Dune query IDs cited) + secondary docs provenance (Mento V3 docs working URL) + token-registry provenance (Celo Token List entry verbatim).
3. The supply field is absent from every entry per RC R-3 immutability hygiene.
4. The §"CRITICAL HALT-VERIFY GATE" prior content is preserved verbatim above (no silent overwrite).
5. The COPM-Minteo out-of-scope entry records audit-trail preservation language without enumerating Mento-protocol fields (Reserve / basket / issuance NOT APPLICABLE).

**End of §β-rescope appendix.**
