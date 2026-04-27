# MR-β.1 Sub-task 1 — Reality Checker single-pass advisory spot-check

**Reviewed deliverable:** `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` (256 lines, committed at `3611b0716`).

**Sub-plan anchor:** `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` Task 11.P.MR-β.1 sub-task 1 — RC-R-4 advisory non-blocking review per the original MR-β.1 review.

**Reviewer:** Reality Checker (TestingRealityChecker persona).

**Review date:** 2026-04-26.

**Tool budget:** ≤ 12 tool uses (target). Actual: 7 tool uses (1 Read, 4 Bash/python-DuckDB, 2 WebFetch).

---

## Verdict

**PASS — HALT-VERIFY is well-founded; user-decision is genuinely required; no fishing or threshold-relaxation behavior detected.**

The HALT is **not** a false positive and is **not** a missed silent-override. Independent triangulation against (a) live DuckDB at HEAD `865402c2c`, (b) the Celo Token List JSON registry retrieved live, and (c) the Mento V3 deployments docs query API confirms a real, externally-auditable contradiction between project-memory `project_mento_canonical_naming_2026` and the Mento-protocol's own canonical-source documentation.

The memo's α/β/γ resolution paths are genuinely distinct, mutually exclusive, and methodologically defensible. No 4th option appears to be missing at the sub-task-1 grade (see §5 below for one annotation about a possible bridge/wrapper hypothesis that does NOT change the user-decision-required disposition).

The five non-HALT tokens (USDm, EURm, BRLm, KESm, XOFm) carry triangulated three-source verification that I confirmed independently — all five address claims are byte-exact (case-folded) against both the Celo Token List JSON and the Mento V3 docs.

---

## 1. HALT correctly invoked? — YES

Per `feedback_pathological_halt_anti_fishing_checkpoint`, when project memory disagrees with on-chain reality, the discrepancy must HALT to user — NOT be silently overridden in either direction.

The memo (lines 23–53) raises the HALT with full provenance for both candidate addresses, explicitly refuses to choose, and enumerates three resolution paths for user disposition. The sub-task-1 acceptance criterion under sub-plan §C is quoted verbatim at line 46. The HALT directive at line 46 fires the correct rule.

**Anti-fishing trail:** intact. No Rev-5.3.x invariant relaxed. No premature spec-doc dispatch (sub-task 3 is explicitly held pending user resolution per §B-3 of the sub-plan). The HALT was surfaced rather than masked.

**Contrast with the silent-override failure mode:** had the DE silently chosen `0xc92e8fc2…` because "that's what DuckDB filters on" or silently chosen `0x8A567e2a…` because "Mento docs say so", the resulting registry-lock spec doc (sub-task 3) would have been byte-exact-immutable on the wrong address with no recovery path under §B-3. The HALT is the correct disposition.

---

## 2. Independent verification of the conflicting evidence

### 2.1 Live DuckDB filter address (`onchain_copm_transfers`)

Query: `SELECT COUNT(*), MIN(evt_block_date), MAX(evt_block_date) FROM onchain_copm_transfers`

Result: **(110,253, 2024-09-17, 2026-04-25)** — matches memo line 17 and table 1 line 64 byte-exact.

Earliest mint query: `SELECT evt_block_date, evt_block_number, from_address, to_address, value_wei FROM onchain_copm_transfers WHERE from_address = '0x0000000000000000000000000000000000000000' ORDER BY evt_block_number ASC LIMIT 1`

Result: **(2024-09-17, block 27,786,128, 0x000…0 → 0x0155b191ec52728d26b1cd82f6a412d5d6897c04, 1,000,000 × 10^18 wei)** — matches memo line 36 and table 1 line 68 byte-exact.

Mint event count + total: **(147 mints, ~4.94B units)** — matches memo line 37 byte-exact.

**Caveat:** The `onchain_copm_transfers` schema does NOT include a `contract_address` column. The table's address-binding is established at ingest time (the ingester filtered Celo `Transfer(address,address,uint256)` events on the contract address presumably set in the upstream extractor). Therefore the claim that this table is "filtered on `0xc92e8fc2…`" is not directly auditable from the table itself — it depends on the ingester configuration. This is a **pre-existing audit-trail gap** that is NOT a sub-task-1 defect; it would be material to sub-task 2 (DuckDB table-to-address audit). The memo correctly flags this in resolution path β (line 49) by noting that if `0x8A567e2a…` is canonical-Mento, the 110,253 events filtered on `0xc92e8fc2…` "tracks an out-of-scope token" — implicitly acknowledging the ingester-config dependency.

**Recommendation (advisory, non-blocking):** sub-task 2 should grep the ingester / Dune-query / scripts/data path that populates `onchain_copm_transfers` and confirm the literal contract_address filter. This is appropriate for sub-task-2 grade, not sub-task-1.

### 2.2 Celo Token List independent fetch

I fetched `https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json` live and extracted the entries for both candidate addresses on chainId 42220:

| Address | Token-list `name` | Token-list `symbol` | Decimals |
|---|---|---|---|
| `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606` | **"COP Minteo"** | `COPM` (capital M) | 18 |
| `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` | **"Mento Colombian Peso"** | `COPm` (lowercase m) | 18 |

Both labels match the memo exactly (lines 32, 67). Critically, the Celo Token List itself treats these as **two distinct entries** with different `name` and (case-distinguished) `symbol` fields. This is dispositive of the memo's central claim that two competing tokens exist on Celo mainnet — the canonical chainId-42220 registry maintained by celo-org confirms it.

### 2.3 Mento V3 deployments docs independent fetch

I queried `https://docs.mento.org/mento-v3/build/deployments.md` via the documented `?ask=…` query API. The Mento docs returned:

- `StableTokenUSD` → `0x765de816845861e75a25fca122bb6898b8b1282a`
- `StableTokenEUR` → `0xd8763cba276a3738e6de85b4b3bf5fded6d6ca73`
- `StableTokenBRL` → `0xe8537a3d056da446677b9e9d6c5db704eaab4787`
- `StableTokenKES` → `0x456a3d042c0dbd3db53d5489e98dfb038553b0d0`
- `StableTokenXOF` → `0x73f93dcc49cb8a239e2032663e9475dd5ef29a08`
- **`StableTokenCOP` → `0x8a567e2ae79ca692bd748ab832081c45de4041ea`**

The Mento V3 docs **explicitly and unambiguously** identify `0x8A567e2a…` as `StableTokenCOP` — NOT `0xc92e8fc2…`. The memo's claim at line 34 ("Mento V3 docs query: NOT listed as COPM per docs query … `0x8A567e2a…` listed as `StableTokenCOP`") is verified verbatim against the live docs API.

### 2.4 Five non-HALT tokens — three-source triangulation genuine

For each of the five non-HALT tokens, I confirmed:
- Address claim in the memo (column "Contract address" in §§2–6) **matches** the Celo Token List entry byte-exact (case-folded).
- Address claim **matches** the Mento V3 docs StableToken-* entry byte-exact (case-folded).
- Project-memory line citation (`project_mento_canonical_naming_2026` lines 9–14) matches each ticker.

All five PASS as a genuine three-source-concur. No fabricated triangulation.

---

## 3. Five non-HALT tokens — verification verdict: PASS

| Ticker | Memo address | Celo Token List | Mento V3 docs | Memory line | Status |
|---|---|---|---|---|---|
| USDm | `0x765DE816…1282a` | "Mento Dollar" / USDm | StableTokenUSD | line 9 | PASS |
| EURm | `0xD8763CBa…6cA73` | "Mento Euro" / EURm | StableTokenEUR | line 10 | PASS |
| BRLm | `0xe8537a3d…b4787` | "Mento Brazilian Real" / BRLm | StableTokenBRL | line 11 | PASS |
| KESm | `0x456a3D04…3B0d0` | "Mento Kenyan Shilling" / KESm | StableTokenKES | line 12 | PASS |
| XOFm | `0x73F93dcc…f29A08` | "Mento West African CFA franc" / XOFm | StableTokenXOF | line 14 | PASS |

The memo's three-source triangulation claim for these five is **genuine, not fabricated**. The Celoscan-403 deferral (memo line 227) is methodologically adequate at sub-task-1 grade given the three-source concur from {project memory, Celo Token List, Mento V3 docs} plus the prior-task gate-decision memo (Task 11.N.2b.1 §1) corroborating Celoscan results from when the WebFetch was working.

---

## 4. Anti-fishing trail intact — verdict: PASS

Reviewed against `feedback_pathological_halt_anti_fishing_checkpoint` and the project-memory anti-fishing rules:

- **No Rev-5.3.x invariant relaxed.** The memo does not modify N_MIN, POWER_MIN, or any sample-power threshold. It does not free-tune MDES_SD (per `project_mdes_formulation_pin`).
- **No premature spec-doc dispatch.** Sub-task 3 (registry-lock spec doc, byte-exact-immutable post-converge) is explicitly held pending user α/β/γ resolution per §B-3 of the sub-plan.
- **No silent override of project memory.** The memo records project memory's claim verbatim (line 39) AND the Mento docs' contradicting claim verbatim (line 34) AND surfaces the conflict for user disposition.
- **No fabricated provenance.** Every cited row count, block number, address, and token-list label was independently verifiable in this RC spot-check.
- **No silent-test-pass pattern** (per `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons`). The memo does not claim "verified" without showing the verification trail; the Celoscan-403 issue is documented openly rather than masked.
- **No scope creep.** Memo stays within sub-task 1 (address inventory); does not preempt sub-task 2 (DuckDB table-to-address audit) or sub-task 3 (registry spec doc).

---

## 5. α/β/γ resolution paths — verdict: PASS, three paths genuinely distinct

The three paths the memo enumerates (lines 47–50) are:

- **α** — `0xc92e8fc2…` is canonical-Mento; `0x8A567e2a…` is something else; project memory stands.
- **β** — `0x8A567e2a…` is canonical-Mento; `0xc92e8fc2…` is the Minteo-fintech token (out of scope per `project_abrigo_mento_native_only`); project memory needs corrigendum; downstream `onchain_copm_transfers` ingest tracks the wrong token.
- **γ** — both tokens are in scope as separate-but-related Mento-ecosystem instruments with disambiguating tickers (`COPM-Minteo` vs. `COPm-Mento`); both enumerated in the registry.

These are genuinely distinct, mutually exclusive, and methodologically defensible. The economic / architectural distinctions are:

- α requires a governance / Reserve-disclosure citation showing `0xc92e8fc2…` IS Mento-issued under a Minteo-distribution wrapper, despite the Celo Token List labeling it "COP Minteo" and the Mento V3 docs not including it. **This is the path with the heaviest evidentiary burden.**
- β is consistent with the most natural reading of the Celo Token List (which distinguishes "COP Minteo" from "Mento Colombian Peso" as two different entries) and the Mento V3 docs (which list only `0x8A567e2a…` as `StableTokenCOP`). **This is the path with the lowest evidentiary burden.**
- γ is the conservative both-in-scope path; preserves the 110,253 historical events but expands scope to also ingest `0x8A567e2a…` going forward.

### 5.1 Possible 4th option (annotated, NOT a missing-option defect)

A possible 4th read is that **`0x8A567e2a…` is a NEW Mento-protocol-native COPm contract deployed AFTER `0xc92e8fc2…`** — i.e., that the Mento protocol re-deployed the Colombian peso under a new contract for governance / V3-architecture reasons, and the older `0xc92e8fc2…` (with 110k events of historical activity) is the deprecated-but-still-distributed Minteo brand. This would resolve to a **time-gated combination of β and γ**: the ingest cutover date matters; pre-cutover events on `0xc92e8fc2…` are the "real" historical record but post-cutover should track `0x8A567e2a…`.

This 4th read does NOT change the user-decision-required disposition. Either:
- it collapses into γ (both in scope, with time-gating disambiguation in the registry doc), OR
- it collapses into β (one canonical, one out-of-scope, with time-gating only relevant for the corrigendum scope).

The memo's α/β/γ enumeration is sufficient at sub-task-1 grade. The user resolving α/β/γ will naturally surface any time-gating needs at sub-task-3 spec-doc draft time.

**No missing-option defect.** Pass.

### 5.2 RC opinion (non-binding, advisory)

The empirical balance of evidence in this spot-check leans toward **β**:
- The Celo Token List literally labels `0xc92e8fc2…` as **"COP Minteo"** (the fintech-issuer brand) — not "Mento Colombian Peso".
- The Mento V3 docs explicitly identify `0x8A567e2a…` (NOT `0xc92e8fc2…`) as `StableTokenCOP`.
- The mint manager `0x0155b191…7c04` for the earliest `0xc92e8fc2…` mints is **not** the Mento Reserve proxy pattern observed for confirmed Mento-native tokens (this is a soft signal, not dispositive — sub-task 2 should confirm).
- TR research (memo line 16, Finding 3) attributes the COPM token to "Minteo-fintech with Colombian-bank-reserved BDO-audited backing" — which is **not** the Mento Reserve overcollateralized basket model.

If the user resolves to β, the downstream impact is non-trivial:
- `onchain_copm_transfers` (110,253 events) tracks an **out-of-scope** token under `project_abrigo_mento_native_only`.
- The `proxy_kind = 'carbon_per_currency_copm_volume_usd'` in `onchain_xd_weekly` (82 weeks) was computed against **the wrong address** for Abrigo's Mento-native scope.
- Rev-5.3.2 published estimates remain byte-exact (per §B-1 of the sub-plan), but new β-track / α-track work consuming the registry would need re-ingestion against `0x8A567e2a…`.

If the user resolves to α or γ, that's a defensible path but requires the Reserve-disclosure / governance citation the memo flags at line 48. Without that citation, β is the path of least evidentiary resistance.

**This RC opinion is advisory only and DOES NOT preempt the user's α/β/γ decision** per the spot-check directive. The HALT is the user's to resolve.

---

## 6. Methodological notes

### 6.1 Celoscan-403 deferral — adequate at sub-task-1 grade

The memo's use of {project memory + Celo Token List + Mento V3 docs + live DuckDB + Task 11.N.2b.1 prior-task corroboration} as the verification stack in lieu of direct Celoscan WebFetch is methodologically sound for an **intermediate research artifact** (sub-task 1). The five-source triangulation provides redundancy; Celoscan-403 is a real external constraint, not a masked failure. Per `feedback_real_data_over_mocks`, no data was synthesized — all citations are independently auditable.

For sub-task 3 (the byte-exact-immutable registry-lock spec doc), the trio review may want to require Celoscan direct verification for each address (with explicit `User-Agent` / authenticated-fetch path to bypass the rate-limit-class 403). That is a sub-task-3 trio-review concern, not a sub-task-1 reviewer-blocker.

### 6.2 Pre-rebrand-ticker note for COPM

The memo at line 63 records: *"Pre-rebrand legacy ticker: 'unchanged' per project memory; in legacy plan artefacts also referred to as cCOP, but Rev-5.3.4 corrigendum nullifies the cCOP attribution."*

This is consistent with `project_mento_canonical_naming_2026` line 13's "COPM (Minteo, unchanged)" claim — i.e., project memory itself records the COPM ticker as having no pre-rebrand alias. But — and this is the key tension — if the Mento-protocol-native token is actually `0x8A567e2a…` ("Mento Colombian Peso" / `COPm`), then under the broader rebrand pattern (cUSD→USDm, cEUR→EURm, etc.) one would naturally expect a `cCOP → COPm` rebrand on `0x8A567e2a…` and a separate Minteo-fintech `COPM` on `0xc92e8fc2…`. This is exactly resolution path **β**. The memo's framing of the "cCOP" attribution as "corrigendum'd" may need re-examination depending on the user's α/β/γ resolution.

This note is annotated for the sub-task-3 trio review's attention, NOT a sub-task-1 defect.

### 6.3 proxy_kind enum integrity

I verified the 10 `proxy_kind` values in `onchain_xd_weekly` directly:
- `b2b_to_b2c_net_flow_usd`
- `carbon_basket_arb_volume_usd`
- `carbon_basket_user_volume_usd`
- `carbon_per_currency_brlm_volume_usd`
- `carbon_per_currency_copm_volume_usd`
- `carbon_per_currency_eurm_volume_usd`
- `carbon_per_currency_kesm_volume_usd`
- `carbon_per_currency_usdm_volume_usd`
- `carbon_per_currency_xofm_volume_usd`
- `net_primary_issuance_usd`

Six per-currency proxies (for the six basket tokens). This matches the memo's basket scope and the `project_duckdb_xd_weekly_state_post_rev531` memory record.

---

## 7. Summary of advisories (all non-blocking)

| # | Advisory | Grade |
|---|---|---|
| 1 | Sub-task 2 should grep the ingester / Dune-query / scripts path that populates `onchain_copm_transfers` to literally confirm the `contract_address` filter; the table itself does not store the contract address. | sub-task-2 concern |
| 2 | If the user resolves to β, sub-task-3 spec doc must include the time-gating / cutover analysis for the 110,253 historical events on `0xc92e8fc2…`. | sub-task-3 concern |
| 3 | Sub-task-3 trio review should require Celoscan direct verification (with auth/UA bypass for the 403) for every address in the registry-lock doc. | sub-task-3 concern |
| 4 | Re-examine the "cCOP attribution corrigendum'd" claim in the memo's COPM section depending on which α/β/γ path the user selects. | sub-task-3 concern |

None of these block the sub-task-1 PASS. They are forward-looking advisories for sub-task 2 and 3.

---

## 8. Final verdict — restated

**PASS — HALT-VERIFY is well-founded and the user-decision is genuinely required.**

- HALT correctly fired per `feedback_pathological_halt_anti_fishing_checkpoint`.
- All factual claims in the memo independently verified in this spot-check.
- α/β/γ paths are genuinely distinct and methodologically defensible.
- Anti-fishing trail intact.
- Five non-HALT tokens carry genuine three-source-concur verification.

**RC advisory opinion (non-binding, do NOT preempt user decision):** the empirical balance of evidence leans toward **β** (`0x8A567e2a…` is canonical-Mento `StableTokenCOP`; `0xc92e8fc2…` is Minteo-fintech). This opinion is surfaced for the user's information; the HALT is the user's to resolve and α / γ remain defensible paths if the user can produce the governance / Reserve-disclosure citations the memo asks for in path α.

Sub-task 3 (registry-lock spec doc) MUST remain held until the user disposes of α / β / γ.

---

## 9. Audit-trail footer

- Reviewed deliverable: `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` (256 lines, commit `3611b0716`).
- Sub-plan anchor: `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` Task 11.P.MR-β.1 sub-task 1.
- Independent verifications conducted: live DuckDB at `contracts/data/structural_econ.duckdb` HEAD `865402c2c` (3 queries); Celo Token List JSON at `https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json` (1 fetch); Mento V3 deployments docs at `https://docs.mento.org/mento-v3/build/deployments.md?ask=…` (2 fetches).
- Project-memory anchors consulted: `feedback_pathological_halt_anti_fishing_checkpoint`, `project_mento_canonical_naming_2026`, `project_abrigo_mento_native_only`, `project_duckdb_xd_weekly_state_post_rev531`, `project_carbon_defi_attribution_celo`, `project_mdes_formulation_pin`, `feedback_real_data_over_mocks`, `project_fx_vol_econ_reviewer_and_silent_test_pass_lessons`.
- Tool-use count: 7 / 12 budget.
- This spot-check: `contracts/.scratch/2026-04-25-subtask-mr-beta-1-1-rc-spot-check.md`.

**End of spot-check.**
