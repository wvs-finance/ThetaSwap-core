# RC Review — MR-β.1 Sub-task 3 Registry Spec Doc

**Reviewer:** Reality Checker (RC trio member; CR + SD peers run in parallel).
**Subject:** `contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md` at commit `339a50480`, 335 lines.
**Date:** 2026-04-26.
**Lens:** Evidence-obsessed; live DuckDB probes + WebFetch + grep + git diff; no text-only analysis.
**Sub-plan anchor:** `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` §C sub-task 3 + §I sub-task 3 rescope.

---

## 1 — Verdict

**NEEDS-WORK.**

One sub-finding under RC concern 4 (paired-source narrative byte-alignment with sub-task 2 audit) and one minor finding under RC concern 7 (cross-reference resolution) require fix-up before the post-converge byte-exact-immutability lock fires per §1.3. Neither rises to BLOCK. All seven other RC concerns VERIFY clean. The empirical-evidence trail is overwhelmingly faithful to the live state and to upstream artifacts; the registry is **substantively correct** but carries one regression of a sub-task 2 RC-spot-check correction that, if not fixed before lock-in, would freeze a numerically wrong claim into the post-converge immutable source-of-truth.

The fix-up is mechanical: a single token in §6.1 (line 205) and one path-creation citation in §10.1 (line 297 → cross-ref §9 line 285) need to land. After fix-up, RC will PASS-w-non-blocking-advisories.

---

## 2 — Findings on the 8 RC concerns

### Concern 1 — Independent address byte-equality across sources

**VERIFIED (PASS).**

`grep -E -ino "0x[0-9a-fA-F]{40}"` extracted every 40-hex-char address in the registry. Cross-checked against:

- **Mento Labs deployment docs** (live WebFetch on `https://docs.mento.org/mento-v3/build/deployments/addresses.md` 2026-04-26):
  - StableTokenCOP: `0x8a567e2ae79ca692bd748ab832081c45de4041ea` — registry §3.1 has `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` — **case-folded byte-equal** ✓
  - StableTokenUSD: `0x765de816845861e75a25fca122bb6898b8b1282a` — registry §3.2 has `0x765DE816845861e75A25fCA122bb6898B8B1282a` — **case-folded byte-equal** ✓
  - StableTokenEUR: `0xd8763cba276a3738e6de85b4b3bf5fded6d6ca73` — registry §3.3 has `0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73` — **case-folded byte-equal** ✓
  - StableTokenBRL: `0xe8537a3d056da446677b9e9d6c5db704eaab4787` — registry §3.4 has `0xe8537a3d056DA446677B9E9d6c5dB704EaAb4787` — **case-folded byte-equal** ✓
  - StableTokenKES: `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` — registry §3.5 has `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` — **byte-equal** ✓
  - StableTokenXOF: `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08` — registry §3.6 has `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08` — **byte-equal** ✓
- **Project memory β-corrigendum block** (`project_mento_canonical_naming_2026.md` lines 12-13):
  - Mento-native COPm: `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` (mixed-case) — registry §3.1 byte-equal ✓
  - COPM-Minteo: `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` (lowercase) — registry §8.1 has `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606` (mixed-case checksummed form) — **case-folded byte-equal** ✓ (consistent with the dual-encoding the user flagged in the brief)
- **Project memory original-content section** (lines 33-38 lowercase forms):
  - All five non-COP tickers byte-equal under case-folding to registry §§3.2-3.6 ✓
  - COPM line 37 shows `0xc92e8fc2…` annotated `⚠️ SUPERSEDED by β-corrigendum above` — registry §8.1 byte-equal under case-folding ✓

The shared-implementation address `0x434563B0604BE100F04B7Ae485BcafE3c9D8850E` cited in §3.1's RC-3 cross-strengthening note is a **new claim not in project memory** — RC sub-task 3 review does not have a project-memory citation to verify against. RC PASS-with-non-blocking-advisory: this address is the implementation-sharing address per RC re-review independent finding (RC-3); a future-RC follow-up could WebFetch a Celoscan proxy verification on each of the six proxies pointing at this implementation. Not blocking under sub-task 3 because the claim is well-scoped (single line, attributed to RC re-review, byte-equal across all 6 proxies sharing it would be the pre-lock check).

**Verdict on concern 1: VERIFIED — all 7 cited addresses are byte-equal across all four authority sources under case-folding.**

### Concern 2 — DuckDB 14-table cross-reference live re-verification

**VERIFIED (PASS).**

Live DuckDB probe via `contracts/.venv/bin/python` against `contracts/data/structural_econ.duckdb` (read-only):

```
SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'onchain_%' ORDER BY table_name
```

Returns **14 tables** (TABLE_COUNT: 14):
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

Registry §4 14-row table matches **byte-for-byte**. Per-tag breakdown per registry §4 totals block (lines 165-169):

- DIRECT in-scope: 3 ✓ (`onchain_carbon_arbitrages`, `onchain_carbon_tokenstraded`, `onchain_y3_weekly`) — matches sub-task 2 audit §3 totals.
- DIRECT mixed-scope: 1 ✓ (`onchain_xd_weekly`).
- DIRECT DEFERRED-via-scope-mismatch: 5 ✓ (`onchain_copm_burns`, `onchain_copm_ccop_daily_flow`, `onchain_copm_freeze_thaw`, `onchain_copm_mints`, `onchain_copm_transfers`).
- DERIVATIVE DEFERRED-via-scope-mismatch: 5 ✓ (`onchain_copm_address_activity_top400`, `onchain_copm_daily_transfers`, `onchain_copm_time_patterns`, `onchain_copm_transfers_sample`, `onchain_copm_transfers_top100_edges`).
- Prior-Rev DEFERRED: 0 ✓.
- **Sum: 3 + 1 + 5 + 5 + 0 = 14 = pre-flight enumeration count.** Coverage HALT-clear.

Spot-check on three table row counts (registry §4 column 4 vs live DuckDB):

- `onchain_copm_burns`: registry says 121 ✓ (live: 121).
- `onchain_copm_mints`: registry says 146 ✓ (live: 146).
- `onchain_copm_freeze_thaw`: registry says 4 ✓ (live: 4).
- `onchain_copm_transfers`: registry says 110,253 ✓ (live: 110253).
- `onchain_copm_daily_transfers`: registry says 522 ✓ (live: 522).
- `onchain_copm_time_patterns`: registry says 86 ✓ (live: 86).
- `onchain_copm_transfers_top100_edges`: registry says 100 ✓ (live: 100).
- `onchain_y3_weekly`: registry says 291 ✓ (live: 291).
- `onchain_xd_weekly`: registry says 819 ✓ (live: 819).

**`onchain_copm_address_activity_top400` row count: registry says nothing specific (only the sub-task 2 audit §4.3 says 300); live: 300.** Consistent with sub-task 2 audit. Not a registry deviation.

**Verdict on concern 2: VERIFIED — 14-table count matches; per-tag breakdown matches sub-task 2 audit §3; per-table row counts match live DuckDB.**

### Concern 3 — proxy_kind live re-verification

**VERIFIED (PASS).**

Live DuckDB probe:

```
SELECT DISTINCT proxy_kind FROM onchain_xd_weekly ORDER BY 1
```

Returns **10 values** (PROXY_KIND_COUNT: 10):
1. `b2b_to_b2c_net_flow_usd`
2. `carbon_basket_arb_volume_usd`
3. `carbon_basket_user_volume_usd`
4. `carbon_per_currency_brlm_volume_usd`
5. `carbon_per_currency_copm_volume_usd`
6. `carbon_per_currency_eurm_volume_usd`
7. `carbon_per_currency_kesm_volume_usd`
8. `carbon_per_currency_usdm_volume_usd`
9. `carbon_per_currency_xofm_volume_usd`
10. `net_primary_issuance_usd`

Registry §5 10-row table enumerates these 10 values **byte-for-byte**. The `_copm_` slug at row 5 is tagged DEFERRED-via-scope-mismatch under β with cross-reference to §7 / §8.1. The other 9 slugs are tagged in-scope.

Note: live-DuckDB ORDER BY produces alphabetical order; registry §5 numbering uses a different (Rev-5.3.2-design-doc) ordering, which is fine because every distinct value still maps. Set-equality holds.

**Verdict on concern 3: VERIFIED — count = 10; byte-set matches; `_copm_` tagged DEFERRED-via-scope-mismatch as required.**

### Concern 4 — `onchain_copm_ccop_daily_flow` paired-source verification

**NEEDS-WORK** (one numerical regression vs sub-task 2 audit corrected paragraph).

Live DuckDB null-pattern probe:

```
SELECT COUNT(*) total,
       COUNT(copm_mint_usd) copm_mint_nn,
       COUNT(copm_burn_usd) copm_burn_nn,
       COUNT(copm_unique_minters) copm_minters_nn,
       COUNT(ccop_usdt_inflow_usd) ccop_inflow_nn,
       COUNT(ccop_usdt_outflow_usd) ccop_outflow_nn,
       COUNT(ccop_unique_senders) ccop_senders_nn
FROM onchain_copm_ccop_daily_flow
```

Returns: `(585, 585, 585, 585, 541, 541, 541)`.

That is: **all three `ccop_*` columns are 541/585 = 92.5% non-null**, including `ccop_unique_senders`.

Sub-task 2 audit §6.1 (post-RC-correction at commit `09bacc105`, line 185) says (verbatim): *"all three `ccop_*` columns (`ccop_usdt_inflow_usd`, `ccop_usdt_outflow_usd`, `ccop_unique_senders`) 92.5% non-null (541/585)"* — and is annotated with the explicit 1-line correction notice (*"prior version of this paragraph mis-stated `ccop_unique_senders` as 100% non-null; live re-probe confirms 541/585 = 92.5%, which strengthens rather than weakens the paired-source conclusion"*).

Registry §6.1 (line 205) says (verbatim): *"`ccop_*` half (`ccop_usdt_inflow_usd`, `ccop_usdt_outflow_usd`, `ccop_unique_senders`; 92.5% non-null at 541/585 USDT-pairing columns + **585/585 sender-count column**)"*. **This is the regressed claim.** It contradicts the live DuckDB probe AND it contradicts the sub-task 2 audit's RC-corrected paragraph.

Empirical evidence:
- Live DuckDB (above): `ccop_unique_senders` non-null = 541, NOT 585.
- Sub-task 2 audit (line 185 post-correction): 541/585 for all three `ccop_*` columns.
- Registry §6.1 (line 205): claims 541/585 for two of three `ccop_*` columns + 585/585 for `ccop_unique_senders` — **wrong on the third column**.

This is exactly the failure mode the byte-alignment requirement in RC concern 4 was authored to catch. The registry §6.1 text was authored as a slight semantic re-organization of the sub-task 2 audit §6.1 paragraph but inadvertently dropped the RC-correction's third-column update. The structural conclusion (paired-source, DEFERRED-via-scope-mismatch tag) is unaffected; only the numerical claim on the `ccop_unique_senders` non-null rate is wrong.

**Mechanical fix-up before convergence-lock fires (a single substring edit):**

In §6.1, replace the parenthetical *"(`ccop_usdt_inflow_usd`, `ccop_usdt_outflow_usd`, `ccop_unique_senders`; 92.5% non-null at 541/585 USDT-pairing columns + 585/585 sender-count column)"* with *"(`ccop_usdt_inflow_usd`, `ccop_usdt_outflow_usd`, `ccop_unique_senders`; all three 92.5% non-null at 541/585; the uniform 92.5% rate across all three `ccop_*` columns confirms shared upstream sub-query)"* — pulling the language exactly from the post-correction sub-task 2 audit §6.1 line 185.

After this 1-line correction, the registry §6.1 narrative will byte-align with the sub-task 2 audit corrected paragraph and with live DuckDB, and the post-converge byte-exact-immutability lock per §1.3 will not freeze a numerical error.

Side note (non-blocking): the registry's same paragraph mentions Dune query IDs `7378788/7379527/7379530` for the Mento-native COPm path. Live DuckDB does not directly verify those (they live on Dune, not DuckDB), but they are byte-consistent with the disposition memo + sub-task 1 inventory + project-memory β-corrigendum block, so RC concern 4 does not extend further.

**Verdict on concern 4: NEEDS-WORK — single numerical regression (585/585 → 541/585 for `ccop_unique_senders`) requires fix-up before convergence-lock; mechanical 1-line edit; structural conclusion unaffected.**

### Concern 5 — Out-of-scope appendix scope partition

**VERIFIED (PASS).**

`grep` on §3 in-scope per-token body (lines 51-138, slicing from "## §3" to "## §4"):

```
awk '/^### §3/,/^## §4/' contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md | grep -in "0xc92e8fc2\|COPM-Minteo"
```

Returns: **ZERO matches.** The §3 in-scope body does NOT mention `0xc92e8fc2` (case-insensitive) or "COPM-Minteo" anywhere across §§3.1 through §3.6.

§7 (slug-vs-canonical-ticker mapping) appropriately mentions `0xC92E8Fc2…` and "COPM-Minteo" because that section's purpose is the slug-asymmetry annotation (legitimate cross-ref).

§8 (out-of-scope appendix) contains exactly **one entry** (§8.1 — COPM-Minteo). The closing line *"No further out-of-scope entries are enumerated"* (line 267) explicitly establishes the §8.1 = singleton invariant. Future additions land as new sections per the §8 closing protocol.

**Verdict on concern 5: VERIFIED — §3 zero contamination from out-of-scope; §8 has exactly one entry.**

### Concern 6 — Mento V3 docs citation

**VERIFIED (PASS).**

Live WebFetch on `https://docs.mento.org/mento-v3/build/deployments/addresses.md` (2026-04-26): URL resolves; returns the StableToken Addresses table from Celo Mainnet under "Shared (Mento v2 & v3)" section. **`StableTokenCOP` entry is present and resolves to `0x8a567e2ae79ca692bd748ab832081c45de4041ea`** (lowercase). The other 5 in-scope addresses (`StableTokenUSD`, `StableTokenEUR`, `StableTokenBRL`, `StableTokenKES`, `StableTokenXOF`) all resolve and byte-match registry §§3.2-3.6 under case-folding.

The legacy URL `https://docs.mento.org/mento/protocol/deployments` referenced in §2 paragraph 1 as "404s and is superseded" — RC sub-task 3 does not test this 404 claim live (RC's earlier disposition review already verified it; no need to re-verify in sub-task 3).

**Verdict on concern 6: VERIFIED — Mento V3 docs URL resolves; StableTokenCOP entry byte-equal to registry §3.1.**

### Concern 7 — Cross-reference resolution

**NEEDS-WORK** (1 of 11 cited paths does not exist on disk).

`test -f` on each cited audit-trail path in §10.1 + §10.2 + §10.3 + §9 line 285:

| Path | Status |
|---|---|
| `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` | **OK** ✓ |
| `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` | **OK** ✓ |
| `contracts/.scratch/2026-04-25-duckdb-address-audit.md` | **OK** ✓ |
| `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` | **OK** ✓ |
| `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` | **OK** ✓ |
| `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-code-reviewer.md` | **OK** ✓ |
| `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-reality-checker.md` | **OK** ✓ |
| `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-technical-writer.md` | **OK** ✓ |
| `contracts/.scratch/2026-04-25-subtask-mr-beta-1-1-rc-spot-check.md` | **OK** ✓ |
| `contracts/.scratch/2026-04-25-mento-userbase-research.md` | **OK** ✓ |
| `contracts/.scratch/2026-04-25-future-research-token-identity-safeguard.md` | **MISSING** ✗ |

The MISSING path is cited in §9 line 285 (within the registry-internal warning: *"A future-research safeguard memo at `contracts/.scratch/2026-04-25-future-research-token-identity-safeguard.md` (sub-task 5 deliverable) carries the process-discipline detail; this §9 carries the registry-internal warning"*) AND again in §10.1 line 297 (within the audit-trail footer: *"Sub-task 5 deliverable (downstream): Future-research safeguard memo at `contracts/.scratch/2026-04-25-future-research-token-identity-safeguard.md` (cross-references this registry by path)"*).

The path is **explicitly self-labeled as "downstream" / "sub-task 5 deliverable not yet authored"** in both sites — the registry is honest about this being a forward-pointer to future MR-β.1 sub-task 5 work, not an existing artifact. This is consistent with the sub-plan structure (sub-tasks 1, 2, 3 land before sub-tasks 4, 5).

**Severity: NEEDS-WORK at the borderline of PASS-with-non-blocking-advisory.** The forward-pointer style is honest, but as stated the citation reads as a path that "carries the process-discipline detail" — which is false for any reader trying to follow the link before sub-task 5 is authored. Two equally-acceptable fix-ups:

(a) **Annotate inline** that the path is forward-pointing: e.g., *"...carries the process-discipline detail (forward-pointer; sub-task 5 dispatch pending)"* in §9 line 285. The §10.1 citation (line 297) already says *"downstream"* + *"sub-task 4 deliverable to be authored"* (for sub-task 4, line 296) but NOT for sub-task 5 (line 297) — symmetric fix-up: add *"(forward-pointer; sub-task 5 not yet authored at this registry's authoring time)"* to line 297 too.

(b) **Defer convergence-lock** of the registry until sub-task 5 lands, then re-verify path existence at the moment of lock-in.

Option (a) is mechanical and fits the §B-2 immutability invariants (the registry is internally honest about which deliverables are downstream); option (b) couples the registry's lock-in to two unrelated sub-tasks and is not preferable.

The sub-task 4 reference at line 296 already uses option (a) styling (*"corrigendum to be authored under sub-task 4 dispatch"*) — so the registry is internally inconsistent in how it handles sub-task 4 vs sub-task 5 forward-pointers. Tightening line 285 + line 297 to match sub-task 4 styling is the cleanest fix.

**Verdict on concern 7: NEEDS-WORK — 10 of 11 paths VERIFIED; 1 forward-pointer path MISSING but legitimately described as downstream; recommend annotating §9 line 285 + §10.1 line 297 to match sub-task 4 citation styling for internal consistency before convergence-lock.**

### Concern 8 — Anti-fishing-invariant integrity

**VERIFIED (PASS).**

- **`git diff --name-only 09bacc105 339a50480`** returns exactly **one file**: `contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md`. **No DuckDB row mutations** (the `.duckdb` file is not in the diff). **No project memory edits**. **No other specs / plans / sub-plans edited**. **No Solidity / Python / schema migration**. ✓
- **`git log --oneline 09bacc105..339a50480`** returns one commit: `339a50480 spec(abrigo): MR-β.1 sub-task 3 — canonical Mento-native address registry`. Single-commit, single-file landing — anti-fishing-clean. ✓
- **Anti-fishing invariant byte-equality** (registry §10.5 lines 325-329):
  - `N_MIN = 75` ✓ (project-memory anchor `project_rev531_n_min_relaxation_path_alpha` confirms 75).
  - `POWER_MIN = 0.80` ✓.
  - `MDES_SD = 0.40` ✓.
  - `MDES_FORMULATION_HASH = 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` — byte-equal to project-memory anchor `project_mdes_formulation_pin` ✓.
  - `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` — byte-equal to active project memory ✓ (same hash also appears in §5 line 192 and §8.1 line 262, all three byte-equal).
- **Rev-2 byte-exact-immutability** of published estimates (β̂ = −2.7987e−8, n = 76, T3b FAIL) — registry §8.1 line 262 + §10.5 line 330 invokes this invariant; no Rev-2 estimate is mutated by the registry; the registry is interpretively re-framing Rev-2 as "scope-mismatch" (Minteo address measured) which is consistent with the disposition-memo β-resolution.
- **Total supply field omission per RC R-3** ✓:
  - `grep -ino "total[- ]supply"` returns 4 matches (lines 32, 53), all in §1.3 + §3 lead-in **explanations of why total supply is omitted**, NOT enumerated entries. The 6 in-scope per-token tables (§§3.1-3.6) and the 1 out-of-scope per-token table (§8.1) carry **zero "Total supply" rows**. Verified by visual inspection of each table's row labels — no enumerated "Total supply" field appears anywhere. ✓
  - `grep -ino "circulating[- ]supply"` returns 1 match (line 32) in the same RC R-3 explanation context; not an enumerated field; ✓.

The §1.3 immutability invariant (post-converge byte-exact-immutable; future additions land as new appendix sections; no in-place edits) is well-formed and consistent with the §B-2 anti-fishing invariants. The §10.5 anti-fishing invariant integrity block is correctly populated.

**Verdict on concern 8: VERIFIED — no anti-fishing invariant relaxed; no DuckDB mutations; no out-of-scope file edits; RC R-3 total-supply omission honored.**

---

## 3 — Additional findings outside the 8 RC concerns

### A1 — Strengthening: shared-implementation cross-check (advisory, non-blocking)

§3.1 line 68 introduces the shared-implementation address `0x434563B0604BE100F04B7Ae485BcafE3c9D8850E` ("all six Mento StableTokens share implementation … the per-token addresses in §§3.1-3.6 are all proxies pointing at this shared implementation"). RC sub-task 3 review did not have a project-memory citation against this address; it is attributed to "RC re-review independent finding (RC-3 cross-strengthening)" and is plausibly correct given Mento V2 EIP-1967 proxy patterns. **Future-RC follow-up suggestion (NOT under sub-task 3):** WebFetch each of the six Celoscan proxy-implementation pages and verify they all point at this implementation. Not blocking under sub-task 3 because (a) the claim is well-scoped to a single line; (b) it does not flow downstream into §4 / §5 / §6 / §7 / §8 / §10; (c) the canonical authority for sub-task 3 is the Mento Labs deployment docs + project memory β-corrigendum + Dune decoded-table catalog, all of which validate the per-token addresses without requiring shared-implementation verification.

This advisory is recorded for sub-plan post-converge consideration; it is not a sub-task 3 NEEDS-WORK item.

### A2 — Cross-strengthening: §10.5 anti-fishing integrity block

§10.5 lines 325-331 enumerate every anti-fishing invariant that COULD have drifted under sub-task 3 dispatch and explicitly states they are unchanged. This is excellent defensive citation discipline — it preempts any future reader's question of whether the registry "snuck in" a threshold change. RC notes the pattern as a positive exemplar for future spec-level immutability invariants.

### A3 — Internal inconsistency in forward-pointer styling (NEEDS-WORK consolidation point)

§10.1 line 296 (sub-task 4 deliverable cite) uses the styling *"corrigendum to be authored under sub-task 4 dispatch; cross-references this registry by path"* — explicit forward-pointer language. §10.1 line 297 (sub-task 5 deliverable cite) does not have the same forward-pointer language and only says *"downstream"* + *"cross-references this registry by path"*. The §9 line 285 sub-task 5 path citation has no forward-pointer language at all — reads as if the path exists. This is the same failure mode as concern 7 NEEDS-WORK; consolidating the fix-up under concern 7's recommendation (option (a)) resolves both.

---

## 4 — Summary line

**RC verdict: NEEDS-WORK.** Two mechanical fix-ups before convergence-lock fires (one numerical claim in §6.1; one forward-pointer styling consistency in §9 line 285 + §10.1 line 297). All eight concerns produce a path to PASS-w-non-blocking-advisories after these fix-ups. The empirical-evidence trail is overwhelmingly faithful and the registry is substantively correct; the two fix-ups protect against freezing minor errors into the post-converge byte-exact-immutable source-of-truth.

**Tool budget consumed:** 8 tool calls (1 Read for registry; 1 Read for project memory; 1 Read for sub-task 2 audit; 4 Bash calls for git diff + grep + path tests + DuckDB live probes; 1 WebFetch for Mento docs; plus 1 ToolSearch for WebFetch loading and 2 follow-up Reads / Bashes on §3 body and §6.1 narrative). Within the 8-14 budget.

**Empirical evidence anchor for fix-up convergence:** `(585, 585, 585, 585, 541, 541, 541)` from the live DuckDB null-pattern probe on `onchain_copm_ccop_daily_flow` against the registry-authoring-time `contracts/data/structural_econ.duckdb` connection. Sub-task 2 audit §6.1 (post-correction at commit `09bacc105`) and live DuckDB AGREE; registry §6.1 at commit `339a50480` DISAGREES with both on the third `ccop_*` column non-null count.

**End of RC review.**
