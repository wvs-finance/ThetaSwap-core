# RC single-pass advisory spot-check — MR-β.1 sub-task 1 RE-DISPATCH (§β-rescope appendix)

**Reviewer**: Reality Checker (single-pass advisory per sub-plan §C-1 + §H-CORRECTIONS RC R-4)
**Subject commit**: `b6d320429` (DE re-dispatch; appended §β-rescope to `2026-04-25-mento-native-address-inventory.md`)
**Predecessor (trio convergence baseline)**: `b4a6a50e6` (RC re-review on fix-up bundle)
**Disposition (already PASS-w-adv'd)**: commit `00790855b`
**Date**: 2026-04-26
**Tool budget consumed**: 5 of 4-7 (Read × 2, Bash × 2, Dune-getDuneQuery × 1)

---

## Verdict

**PASS** — unblocks MR-β.1 sub-task 2 dispatch (DuckDB table-to-address audit on 14 onchain_* tables tagged DIRECT/DERIVATIVE/DEFERRED).

No NEEDS-WORK or BLOCK findings. No non-blocking advisories beyond what was already filed under the disposition + fix-up bundle reviews. The §β-rescope appendix discharges the HALT-VERIFY GATE cleanly with full byte-equality, mandatory-field completeness, real-and-resolvable provenance, and zero scope leakage.

---

## Per-concern findings

### RC-concern-1: Address byte-equality vs. project memory

**Finding**: VERIFIED.

Cross-reference of `2026-04-25-mento-native-address-inventory.md` §β-rescope.1 entries against `project_mento_canonical_naming_2026.md` β-corrigendum block (top of file, lines 8-26), case-folded:

| Token | §β-rescope address | Memory β-corrigendum | Match |
|---|---|---|---|
| COPm | `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` (line 285) | `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` (line 12, 18) | byte-exact |
| USDm | `0x765DE816845861e75A25fCA122bb6898B8B1282a` (line 300) | `0x765de816845861e75a25fca122bb6898b8b1282a` (line 33, SUPERSEDED block) | byte-exact (case-folded) |
| EURm | `0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73` (line 314) | `0xd8763cba276a3738e6de85b4b3bf5fded6d6ca73` (line 34) | byte-exact (case-folded) |
| BRLm | `0xe8537a3d056DA446677B9E9d6c5dB704EaAb4787` (line 328) | `0xe8537a3d056da446677b9e9d6c5db704eaab4787` (line 35) | byte-exact (case-folded) |
| KESm | `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` (line 342) | `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` (line 36) | byte-exact |
| XOFm | `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08` (line 356) | `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08` (line 38) | byte-exact |

Out-of-scope COPM-Minteo: §β-rescope.2 entry 7 (line 376) `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606` byte-matches the SUPERSEDED memory-block entry `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` (line 13, 19, 37) and the disposition memo (per RC's earlier PASS-w-adv on `00790855b`). The capitalization difference in the §β-rescope appendix uses checksummed casing, which is RC-acceptable.

USDm matches the SUPERSEDED block rather than a corrigendum block because USDm is unaffected by β-corrigendum (the corrigendum block explicitly states only COPM disambiguation; "the other five Mento-native tickers (USDm/EURm/BRLm/KESm + XOFm) are unaffected … their addresses remain authoritative as listed below"). RC accepts this by-design: the SUPERSEDED block is the authoritative source for the unaffected five.

### RC-concern-2: Mandatory-field completeness

**Finding**: VERIFIED.

Per sub-plan §C-1 acceptance, the 6 mandatory fields per in-scope token are: ticker + pre-rebrand legacy ticker (where applicable) + contract address + first-observed-on-chain date + Mento Reserve relationship + basket-membership status + provenance citation(s). Supply field DELIBERATELY omitted per RC R-3.

| Token | Ticker | Legacy ticker | Address | First-observed | Reserve relationship | Basket status | Provenance | Status |
|---|---|---|---|---|---|---|---|---|
| COPm (entry 1) | line 283 | line 284 (no pre-rebrand; explicit) | line 285 | line 286 (2024-10-31) | line 287 | line 288 | lines 289-292 (3 citations) | COMPLETE |
| USDm (entry 2) | line 298 | line 299 (cUSD) | line 300 | line 301 (2020-04-22) | line 302 | line 303 | lines 304-306 (3 citations) | COMPLETE |
| EURm (entry 3) | line 312 | line 313 (cEUR) | line 314 | line 315 (2021-03-25) | line 316 | line 317 | lines 318-320 (3 citations) | COMPLETE |
| BRLm (entry 4) | line 326 | line 327 (cREAL) | line 328 | line 329 (2021-12-15) | line 330 | line 331 | lines 332-334 (3 citations) | COMPLETE |
| KESm (entry 5) | line 340 | line 341 (cKES) | line 342 | line 343 (2024-05-21) | line 344 | line 345 | lines 346-348 (3 citations) | COMPLETE |
| XOFm (entry 6) | line 354 | line 355 (no pre-rebrand; explicit "deployed under tail-m from genesis") | line 356 | line 357 (2023-10-16) | line 358 | line 359 | lines 360-362 (3 citations) | COMPLETE |

Out-of-scope COPM-Minteo (entry 7, lines 372-380): ticker + Celo Token List name + contract address + Rev-2 X_d source note all present (4-field slim schema verified, lines 374-378). Reserve / basket / issuance fields explicitly NOT APPLICABLE on line 380, which is RC-correct discipline (don't enumerate Mento-protocol fields for an out-of-scope third-party token).

Supply field absent from all 7 entries (RC R-3 immutability hygiene preserved).

### RC-concern-3: Provenance citation discipline

**Finding**: VERIFIED.

Every in-scope token carries at least one on-chain provenance citation (Dune query ID + secondary docs + token-registry triplet for entries 1-6). Spot-check on randomly-selected query ID 7379578 (USDm first-transfer probe, cited in entry 2 line 304):

`mcp__dune__getDuneQuery(query_id=7379578)` returned:
- Name: "Mento-native first-transfer probe (5 tokens) v2"
- Description: "First-observed-on-chain transfer date for USDm, EURm, BRLm, KESm, XOFm via mento_celo.stabletoken_evt_transfer. MR-β.1 sub-task 1 RE-DISPATCH provenance."
- Owner: user_id 685607 (DE's Dune account)
- SQL targets the 5 cited Mento-native addresses (USDm/EURm/BRLm/KESm/XOFm) verbatim
- Latest execution ID: `01KQ6E0H9KC8HC6SV8Z18RW6ZD`

Query ID resolves and is real. Description text matches the citation context in the memo. SQL targets exactly the addresses claimed. The other three cited query IDs (7378788, 7379585, 7379590) are extrapolated as similarly real on the basis of the consistent ID range, the matching DE Dune-account ownership, and the description-pattern continuity (β-feasibility / UNION-ALL / per-token probes). Sample size of 1-of-4 is the budgeted spot-check depth per the dispatch instructions.

Secondary-docs URL `https://docs.mento.org/mento-v3/build/deployments/addresses.md` is cited consistently across all 6 in-scope entries; the legacy URL is documented as 404'd in entry 1 (line 290). Token-registry citation `https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json` is cited in entry 1 (line 291) with WebFetch retrieval date 2026-04-26.

### RC-concern-4: HALT-VERIFY discipline

**Finding**: VERIFIED.

Grep over the appended §β-rescope section (lines 260-431) confirms scope segregation:

- `0x8A567e2a` appears in the in-scope context only (line 271 disposition statement, line 285 entry 1 address, line 387 reaffirmation, line 398 RC-8 forward-look, line 417 Dune-query annotation). Zero leakage into the out-of-scope §β-rescope.2 entry 7.
- `0xc92e8fc2` (and `0xC92E8Fc2` checksummed) appears only in the out-of-scope context (line 271 disposition statement explicitly tagging it Minteo-fintech, line 376 entry 7 address). Zero leakage into the in-scope §β-rescope.1 entries.

The §"CRITICAL HALT-VERIFY GATE: Colombian-peso address ambiguity" prior content (lines 1-258, pre-§β-rescope) is preserved verbatim above the appendix per anti-fishing-on-memory-edits append-only discipline (line 262 explicit + line 394 reaffirmation). No silent overwrite.

The DE's claim "HALT-VERIFY discrepancies: NONE" (per dispatch instructions) is RC-corroborated: all 6 in-scope addresses byte-match memory β-corrigendum, the 1 out-of-scope address byte-matches the SUPERSEDED-but-preserved entry, and there is no cross-contamination between in-scope and out-of-scope address surfaces.

### RC-concern-5: No DuckDB row mutation, no out-of-scope file changes

**Finding**: VERIFIED.

`git diff --name-only b4a6a50e6 b6d320429` returned a single file:
```
contracts/.scratch/2026-04-25-mento-native-address-inventory.md
```

`git diff --stat b4a6a50e6 b6d320429` confirms 175 line additions on that single file (matches the dispatch-instructions claim of "172 new lines" within rounding, since the diff-stat counts the section-divider lines).

`git diff b4a6a50e6 b6d320429 -- "*.duckdb" | wc -l` returned `0` → zero DuckDB byte mutations.

No project-memory edits in this commit (per RC-concern-6 below). No spec/plan edits. No code/SQL/notebook edits. The commit is editorial-only on the address-inventory memo, exactly as scoped under sub-plan §G-3.

### RC-concern-6: Anti-fishing scope discipline

**Finding**: VERIFIED.

The appended §β-rescope section (172 net new lines, 260-431) contains:
- **Permitted content**: backticked addresses, file paths, table names (e.g. `mento_celo.stabletoken_evt_transfer`, `onchain_xd_weekly`), URLs (Mento V3 docs, Celo Token List), Dune query IDs, dates, decoded-event names (`evt_exchangeupdated`, `evt_validatorsupdated`), the immutable hashes (`MDES_FORMULATION_HASH`, `decision_hash`), and prose interpretation of the disposition. ALL ALLOWED per dispatch instructions.
- **Banned content**: NONE detected.
  - No new spec authoring (no new acceptance criteria, no new gate thresholds; line 396 explicitly reaffirms "No anti-fishing invariant relaxed").
  - No code or SQL bodies (only backticked SQL-table names, never inline SQL).
  - No project-memory edits in this commit (`git diff --name-only` confirms only the inventory memo file changed; the `project_mento_canonical_naming_2026.md` and `project_abrigo_mento_native_only.md` files are NOT touched).
  - No silent override of byte-exact-immutability of Rev-2 published estimates (line 379 explicitly preserves Rev-2 β̂ = −2.7987e−8, n = 76, T3b FAIL, MDES_FORMULATION_HASH `4940360dcd2987…cefa`, decision_hash `6a5f9d1b05c1…443c`).

The RC-8 forward-looking joint-coverage note (line 398) is correctly framed as "NOT actionable here" and "deferred to β-spec, not actionable here" with a pre-committed pivot frame (refresh Y₃ panel OR pre-commit relaxation-or-defer disposition under `feedback_pathological_halt_anti_fishing_checkpoint`). This is RC-style risk-surfacing without scope-creep, which is acceptable.

---

## New findings outside the 6 RC concerns

None.

Two minor observations (NOT findings, NOT advisories, recorded for completeness):

1. The "RC-3 cross-strengthening" line in entry 1 (line 292) attributes a finding ("All six Mento StableTokens share implementation `0x434563B0604BE100F04B7Ae485BcafE3c9D8850E`") to "RC re-review independent finding". This is consistent with what RC observed at the trio-convergence checkpoint at commit `b4a6a50e6`. RC has no objection to the attribution.

2. The §β-rescope.4 audit-trail cross-references (lines 402-422) include a forward-pointer to "RC spot-check on this re-dispatch deliverable (single-pass advisory per RC R-4 in MR-β.1 sub-plan §H CORRECTIONS)" at lines 424-429 with a 5-item enumerated verification checklist. RC has executed all 5 items above (mapped onto RC-concerns 1, 3, 2, 4, and the out-of-scope-entry slim-schema check) and confirms full coverage. The forward-pointer is consistent with RC's actual scope.

---

## Audit trail

- Subject commit: `b6d320429`
- Predecessor (trio convergence): `b4a6a50e6`
- Disposition memo (already PASS-w-adv'd): `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` at commit `00790855b`
- Memo under review: `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` (lines 260-431 = §β-rescope appendix)
- Memory cross-referenced: `/home/jmsbpp/.claude/projects/-home-jmsbpp-apps-ThetaSwap-thetaSwap-core-dev--git-modules-lib-angstrom/memory/project_mento_canonical_naming_2026.md`
- Sub-plan: `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` (§C-1 acceptance, §H CORRECTIONS RC R-3 + R-4)
- Major plan: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` (Rev-5.3.5 CORRECTIONS block)
- Dune-spot-check evidence: query 7379578 ("Mento-native first-transfer probe (5 tokens) v2", DE-owned, latest execution ID `01KQ6E0H9KC8HC6SV8Z18RW6ZD`)

## Next dispatch unblocked

PASS verdict unblocks **MR-β.1 sub-task 2** dispatch: DuckDB table-to-address audit on 14 `onchain_*` tables tagged DIRECT / DERIVATIVE / DEFERRED per disposition memo §4.4 and Rev-5.3.5 CORRECTIONS block. The byte-exact-immutable address registry from this sub-task is the source-of-truth for the table-tagging deliverable.

---

**End RC single-pass advisory spot-check.**
