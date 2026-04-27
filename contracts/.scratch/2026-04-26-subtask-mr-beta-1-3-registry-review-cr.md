# MR-β.1 Sub-task 3 Registry Spec — Code Reviewer Review

**Date:** 2026-04-26
**Reviewer:** Code Reviewer (CR), trio member alongside RC + Senior-Developer
**Target file:** `contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md` (commit `339a50480`, 335 lines)
**CR scope:** byte-equality, DuckDB cross-reference coverage, proxy_kind enumeration completeness, RC R-2 disambiguation, scope partition discipline, anti-fishing-invariant adherence, non-canonical-source warning specificity, cross-reference resolution.

---

## §1 — Verdict

**NEEDS-WORK (single-issue fix-up; non-substantive on the science / scope correction; substantive on cross-reference correctness).**

The registry doc nails the heavy work — byte-equality of all 7 addresses is **CONFIRMED**, the 14-table DuckDB tag-totals identity is **CONFIRMED**, the 10-`proxy_kind` enumeration is **CONFIRMED**, the RC R-2 paired-source disambiguation is **CONFIRMED** with the right narrative discipline, the §3-vs-§8 scope partition has zero leakage, the anti-fishing invariants are honest and unrelaxed, the §9 non-canonical-source warning enumerates the two-layer inversion precedent + the four-authority triangulation procedure with actionable specificity, and every audit-trail-footer cross-referenced path resolves on disk.

**The single substantive issue is a section-numbering off-by-one in the cross-references.** Inside the doc, the out-of-scope appendix is **§8** (with its sole entry §8.1), but the body text references it as **§7** in 13 places (line 21, line 30, line 144, lines 150-160 each "see §7", line 185 "cross-reference §7", line 204, and line 238 "per §7-appendix-entry-1"). §7 in this doc is actually the slug-vs-canonical-ticker mapping table — a different section entirely. A reader following any of these references lands on the wrong section, and the §1.3 immutability invariant explicitly locks "the §7 out-of-scope appendix entry" against a section that is no longer the appendix.

This is a substantive correctness issue — not a stylistic nit — because (a) the doc is positioned as the post-converge byte-exact-immutable source-of-truth (§1.3) and a broken cross-reference inside an immutability invariant is exactly the kind of artifact that gets misread by downstream consumers, and (b) the registry's own §1.3 promises that the appendix will not be edited in place but identifies the wrong section number, so the immutability promise itself is mis-targeted. Recommend a single mechanical fix-up pass replacing every §7 → §8 (or §8.1 where appropriate) when the §7 reference is meant to point at the out-of-scope appendix; leave the §7 reference unchanged where it correctly points at the slug-mapping table (lines 227, 242 in the §7 section header itself, plus the `§7 (out-of-scope appendix)` typed-out parenthetical that should become `§8 (out-of-scope appendix)`).

The fix-up is approximately 13-14 line touches, all self-contained inside this one file, with zero impact on byte-equality of any address, on the 14-table count, on the 10-`proxy_kind` enumeration, or on the §6 paired-source narrative. It is also strictly non-anti-fishing: it does not relax any threshold, change any address, or affect the Rev-2 byte-exact-immutable estimates.

After fix-up I would PASS.

---

## §2 — Per-concern findings (8 CR concerns)

### Concern 1 — Internal consistency / byte-equality: **CONFIRMED**

Direct case-folded comparison of the 6 in-scope §3.1-§3.6 addresses + the 1 §8.1 out-of-scope address against the project memory β-corrigendum block (`/home/jmsbpp/.claude/projects/.../memory/project_mento_canonical_naming_2026.md` lines 12-13 + lines 33-38, β-corrigendum block — NOT the SUPERSEDED original-content section):

| Token | Registry (lower-cased) | Memory β-corrigendum (lower-cased) | Match |
|---|---|---|---|
| §3.1 COPm | `0x8a567e2ae79ca692bd748ab832081c45de4041ea` | `0x8a567e2ae79ca692bd748ab832081c45de4041ea` | ✓ |
| §3.2 USDm | `0x765de816845861e75a25fca122bb6898b8b1282a` | `0x765de816845861e75a25fca122bb6898b8b1282a` | ✓ |
| §3.3 EURm | `0xd8763cba276a3738e6de85b4b3bf5fded6d6ca73` | `0xd8763cba276a3738e6de85b4b3bf5fded6d6ca73` | ✓ |
| §3.4 BRLm | `0xe8537a3d056da446677b9e9d6c5db704eaab4787` | `0xe8537a3d056da446677b9e9d6c5db704eaab4787` | ✓ |
| §3.5 KESm | `0x456a3d042c0dbd3db53d5489e98dfb038553b0d0` | `0x456a3d042c0dbd3db53d5489e98dfb038553b0d0` | ✓ |
| §3.6 XOFm | `0x73f93dcc49cb8a239e2032663e9475dd5ef29a08` | `0x73f93dcc49cb8a239e2032663e9475dd5ef29a08` | ✓ |
| §8.1 COPM-Minteo | `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` | `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` | ✓ |

7-of-7 byte-match (case-folded), against the β-corrigendum block specifically (the SUPERSEDED original content's COPM-Minteo line at memory line 37 carries the explicit ⚠️ SUPERSEDED marker; the doc correctly relies on the β-corrigendum block at lines 12-13 + the original-content non-COP entries at lines 33-38). The mixed-case rendering across registry sections (e.g., `0x8A567e2a` vs. `0xC92E8Fc2`) is consistent with the §3 preamble's documentation of "mixed-case as recorded; case-folded comparison is the byte-equality test" (line 53). No address-level inversion.

### Concern 2 — DuckDB cross-reference table coverage: **CONFIRMED**

§4 lists exactly **14** `onchain_*` tables (rows numbered 1-14 in the table at lines 148-161). Per-tag breakdown:

| Tag | Count | Tables |
|---|---|---|
| DIRECT in-scope | 3 | `onchain_carbon_arbitrages`, `onchain_carbon_tokenstraded`, `onchain_y3_weekly` |
| DIRECT mixed-scope | 1 | `onchain_xd_weekly` |
| DIRECT DEFERRED-via-scope-mismatch | 5 | `onchain_copm_burns`, `onchain_copm_ccop_daily_flow`, `onchain_copm_freeze_thaw`, `onchain_copm_mints`, `onchain_copm_transfers` |
| DERIVATIVE DEFERRED-via-scope-mismatch | 5 | `onchain_copm_address_activity_top400`, `onchain_copm_daily_transfers`, `onchain_copm_time_patterns`, `onchain_copm_transfers_sample`, `onchain_copm_transfers_top100_edges` |
| DEFERRED (prior Rev-5.3.x scope) | 0 | (empty bucket) |

Sum 3 + 1 + 5 + 5 + 0 = **14**. Matches sub-task 2 audit §3 + §9 coverage-completeness verification (sub-task 2 audit lines 73-80 + 268-274). Tag totals printed at registry lines 165-169 are correct and verifiable. Coverage HALT-clear.

### Concern 3 — proxy_kind enumeration completeness: **CONFIRMED**

§5 enumerates **10** `proxy_kind` values (rows 1-10 at registry lines 181-190), matching the live-DuckDB authoritative `SELECT DISTINCT proxy_kind FROM onchain_xd_weekly` count and the sub-task 2 audit §5 enumeration (sub-task 2 audit lines 150-160). Of the 10:

- 9 in-scope (`carbon_basket_user_volume_usd`, `carbon_basket_arb_volume_usd`, `b2b_to_b2c_net_flow_usd`, `net_primary_issuance_usd`, `carbon_per_currency_brlm_volume_usd`, `carbon_per_currency_eurm_volume_usd`, `carbon_per_currency_kesm_volume_usd`, `carbon_per_currency_usdm_volume_usd`, `carbon_per_currency_xofm_volume_usd`).
- 1 DEFERRED-via-scope-mismatch (`carbon_per_currency_copm_volume_usd`, registry line 185, correctly tagged with the rationale that the slug points at Minteo-fintech `0xC92E8Fc2…`, NOT Mento-native COPm `0x8A567e2a…`).

Per-`proxy_kind` HALT-clear. The summary text at registry line 192 ("In-scope per-`proxy_kind` count: 9 of 10") is correct.

### Concern 4 — `onchain_copm_ccop_daily_flow` explicit RC R-2 disambiguation: **CONFIRMED**

§6 (lines 196-223) carries a five-subsection narrative treatment of the paired-source finding:

- **§6.1** records the paired-source finding with the right structure: `copm_*` half = Minteo-fintech `0xC92E8Fc2…` mint/burn call traces, `ccop_*` half = separately-named historical-cCOP token paired with USDT inflow/outflow via Dune query `7366593`. Non-null cardinality (100% / 92.5%) is stated correctly per the sub-task 2 audit's RC-corrected paragraph (sub-task 2 audit line 185, the post-RC-spot-check correction).
- **§6.1 / §6.2** explicitly states BOTH halves out of Mento-native scope. The `ccop_*` side is not Mento-native COPm `0x8A567e2a…` either (no audit-time Dune query targets that address from this table). The DEFERRED-via-scope-mismatch tag applies to the table as a whole.
- **§6.3** records the future-revision rename recommendation as **NOT executed** under this sub-plan, with the §B-2 invariant cited as the binding constraint. The recommended re-slug `onchain_copm_minteo_daily_flow` is recorded as a future-revision candidate only; the recommendation block is correctly framed in non-imperative language ("recommendation is stable as a future-revision candidate").

The RC R-2 narrative-treatment requirement (sub-plan §H R-2 disposition + sub-plan §I sub-task 2 rescope strengthening) is satisfied. The text discipline is annotation-only — no rename, no schema migration, no row mutation language. Good.

### Concern 5 — Out-of-scope appendix discipline: **CONFIRMED on partition; NEEDS-WORK on §-numbering cross-reference**

**Partition (CONFIRMED).** §8 contains exactly ONE entry (§8.1 COPM-Minteo at lines 252-265). The §3 in-scope per-token body (lines 51-139) was scanned against `0xc92e8fc2`, "COPM-Minteo", and "Minteo" with zero matches — the §3 in-scope body is CLEAN. The COPM-Minteo entity surfaces only in §1.2 (out-of-scope declaration), §4 (DuckDB cross-reference rows for the 10 `onchain_copm_*` tables tagged DEFERRED-via-scope-mismatch), §5 (the one `carbon_per_currency_copm_volume_usd` proxy_kind tagged DEFERRED-via-scope-mismatch), §6 (paired-source narrative), §7 (slug-mapping table flagging the `copm` slug as ambiguous), §8.1 (the appendix entry itself), §9 (Layer-1 / Layer-2 inversion narrative), and §10.3 (project-memory anchor list). All those surfaces are correct: COPM-Minteo is named where it should be (out-of-scope context, audit-trail context, anti-pattern citation), and is absent from where it should be (the in-scope §3 body).

**§-numbering cross-reference (NEEDS-WORK).** This is the single substantive issue. The doc says "§7" in 13 places where it means "§8" or "§8.1". Specifically:

| Line | Quoted phrase | Should be |
|---|---|---|
| 21 (§1.2) | "Preserved in the audit-trail appendix at §7 ONLY" | §8 |
| 30 (§1.3) | "Every field in §3.1 through §3.6 (and the §7 out-of-scope appendix entry) is locked at the byte level" | §8.1 |
| 144 (§4 preamble) | "Each row's address linkage cross-references back to §3 (in-scope) or §7 (out-of-scope appendix)" | §8 |
| 150 (§4 row 3) | "via inheritance — see §7" | §8 (or §8.1) |
| 151 (§4 row 4) | "OUT of Mento-native scope — see §7" | §8 |
| 153 (§4 row 6) | "via inheritance — see §7" | §8 |
| 154 (§4 row 7) | "OUT of Mento-native scope — see §7" | §8 |
| 155 (§4 row 8) | "OUT of Mento-native scope — see §7" | §8 |
| 156 (§4 row 9) | "via inheritance — see §7" | §8 |
| 157 (§4 row 10) | "OUT of Mento-native scope — see §7" | §8 |
| 158 (§4 row 11) | "via inheritance — see §7" | §8 |
| 159 (§4 row 12) | "via inheritance — see §7" | §8 |
| 160 (§4 row 13) | "see §5 + §7" | §5 + §8 |
| 185 (§5 row 5) | "cross-reference §7 (out-of-scope appendix)" | §8 |
| 204 (§6.1 first bullet) | "OUT of Mento-native scope** under β; cross-reference §7" | §8 |
| 238 (§7 row `copm`) | "(audit-time live ingestion; per §7-appendix-entry-1)" | §8.1 |

The §7 section in the doc (lines 227-242) is actually the **slug-vs-canonical-ticker mapping** table; the out-of-scope appendix is §8. So 13-14 cross-references inside the doc point at the wrong section. Critical because §1.3's byte-exact-immutability invariant promises future edits will not be made to "the §7 out-of-scope appendix entry" — but §7 is not the appendix, so the immutability promise mis-targets.

The fix is mechanical: search for "§7" in the file, leave the two §7 references that genuinely point at the slug-mapping table header (registry line 227 itself, plus the audit-trail-footer cross-reference if any), and replace every other §7 → §8 (or §8.1 for the §1.3 immutability-invariant cross-reference and the §7-appendix-entry-1 reference at line 238). After fix-up, the cross-reference graph is consistent.

### Concern 6 — Anti-fishing-invariant adherence: **CONFIRMED**

- **No supply field in any per-token §3 entry (RC R-3).** §3 preamble line 53 explicitly states "Total supply is **deliberately omitted** per §1.3"; line-by-line scan of §3.1-§3.6 (registry lines 55-138) finds no supply / circulating / total_supply / total_value field. Confirmed clean. §1.3 line 32 carries the rationale ("supply moves over time and would conflict with the byte-exact-immutability invariant"). RC R-3 satisfied.
- **No DuckDB schema migration / table rename language in the body.** The five mentions of "rename" or "migration" all sit in correctly-bounded annotation contexts: line 34 (§1.3 invariant: "no DuckDB row mutations, no schema migrations, no table renames"); line 215 (§6.3 header: "Future-revision rename recommendation (NOT executed under this sub-plan)"); line 217 (recommendation block, "recorded for future revision consideration only; no rename is executed under MR-β.1"); line 223 (recommendation closure, "sub-plan §B-2's 'no rename, no schema migration' invariant binds this sub-task"); line 229 (§7 slug-mapping note: "they were intentionally not mass-renamed for migration-stability reasons"); line 242 (§7 closing line: "No rename executed under this sub-plan per §B-2"). Every mention is annotation-only and correctly flags the §B-2 invariant as the binding constraint. No silent migration / rename smuggling.
- **§1.3 byte-exact-immutability invariant is honest** in the sense that the per-token §3 body has no internal mutability hooks (no "subject to revision" / "TBD" / "preliminary" markers). The single dishonesty risk would be the §-numbering cross-reference issue from Concern 5 — the §1.3 invariant promises to lock "the §7 out-of-scope appendix entry" but that section number is wrong; an immutability promise that points at the wrong section is technically vacuous on the actual appendix. Bundle the §-numbering fix-up under Concern 5 and the §1.3 invariant becomes correctly-targeted.

### Concern 7 — Non-canonical-source warning specificity: **CONFIRMED**

§9 (registry lines 271-285) carries the two-layer inversion precedent + the four-authority triangulation procedure with actionable specificity:

- **Layer 1 inversion (Rev-5.3.3 cCOP-vs-COPM).** Registry line 275 names the source memo (`contracts/.scratch/2026-04-25-mento-userbase-research.md`), the specific Finding (Finding 3), the user correction quote ("is COPM not cCOP"), and the project-memory partial-correctness note (`project_mento_canonical_naming_2026` was correct on the **ticker** layer; the agent's brief Rev-5.3.3 attribution flip was wrong). Specific, actionable, citable.
- **Layer 2 inversion (Rev-5.3.4 address-level).** Registry line 276 explicitly names the wrong address (`0xC92E8Fc2…` claimed Mento-native COPM) and the corrected address (`0x8A567e2aE79CA692Bd748aB832081C45de4041eA` canonical Mento V2 `StableTokenCOP`, lowercase ticker COPm), and identifies the corrective evidence base (Dune `searchTablesByContractAddress` + activity probe + Mento V3 deployments docs + Celo Token List, all triangulated under MR-β.1 sub-task 1). Specific, actionable.
- **Mandatory triangulation procedure (4 authorities).** Registry lines 280-283 enumerate the four authorities exactly as §2 specifies. The "Mento Labs official deployment docs" URL is given (with the legacy URL flagged as 404'd and superseded). The Dune disambiguation criterion is given (Mento-protocol-specific events `evt_exchangeupdated` / `evt_validatorsupdated` / `evt_brokerupdated` / `evt_initialized` presence is dispositive). The Celo Token List URL is given. The project-memory anchors are named. Each authority has a concrete operational consume-pattern rather than a vague "consult external sources."
- **Anti-fishing-banned shortcut framing.** Line 285 states "Failure to triangulate before propagating a token-identity claim into specs / plans / code / project memory is an anti-fishing-banned shortcut per `feedback_pathological_halt_anti_fishing_checkpoint`." Specific, citable, with a forward-pointer to the future-research safeguard memo (sub-task 5 deliverable) for process-discipline detail. Specific.

The §9 warning is not vague; it is exactly the actionable warning a future researcher needs to avoid both layer-1 and layer-2 failure modes. Good.

### Concern 8 — Cross-references resolve: **CONFIRMED**

`ls -la` against every cross-reference in §10.1, §10.2, §10.3, §10.4 found every cited path on disk:

| §10 cross-reference | Resolves on disk? |
|---|---|
| sub-plan source-of-truth `2026-04-25-ccop-provenance-audit.md` | ✓ (55,055 bytes) |
| major plan `2026-04-20-remittance-surprise-implementation.md` | ✓ (439,908 bytes) |
| sub-task 1 inventory `2026-04-25-mento-native-address-inventory.md` | ✓ (43,411 bytes) |
| sub-task 2 audit `2026-04-25-duckdb-address-audit.md` | ✓ (36,846 bytes) |
| HALT-resolution memo `2026-04-26-mr-beta-1-1-halt-resolution-beta.md` | ✓ (13,804 bytes) |
| 3-way disposition trio `2026-04-26-rev535-beta-disposition-review-{cr,rc,tw}.md` | ✓ (all three present) |
| sub-task 1 RC spot-check `2026-04-25-subtask-mr-beta-1-1-rc-spot-check.md` | ✓ (19,619 bytes) |
| TR research file `2026-04-25-mento-userbase-research.md` | ✓ (31,812 bytes) |
| live DuckDB `contracts/data/structural_econ.duckdb` | ✓ (41 MB) |
| project-memory anchors named in §10.3 | (project-memory paths are global; the named-anchor approach is correct, no path breakage) |

Sub-task 4 + 5 deliverables are forward-pointers to currently-unauthored files — that's fine (clearly marked as "(downstream)" in §10.1). USDT scam-impersonator companion-precedent cite is present at registry line 314 (`project_usdt_celo_canonical_address`). All committed-commit references cited (e.g., `00790855b`, `b4a6a50e6`, `b6d320429`, `b8e220da1`, `eb72f7133`, `09bacc105`, `3286dfe66`, `3611b0716`) are presented as identifiers and don't claim post-commit-resolution anchors that the doc's reader needs to chase.

No broken cross-references on disk. The only stale cross-references in the doc are the §7-vs-§8 section-numbering issue inside the doc body (Concern 5).

---

## §3 — Findings outside the 8 CR concerns

**(F-1) Stylistic continuity with sibling specs.** The doc adopts a narrative, table-heavy structure consistent with `contracts/docs/superpowers/specs/2026-04-24-y3-inequality-differential-design.md` and `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md` (per `feedback_no_code_in_specs_or_plans`'s 100%-code-agnostic invariant). The single permitted SQL fragment is the schema-introspection query in the sub-task 2 audit (not in the registry); the registry itself contains zero SQL, zero Python, zero Solidity. Code-agnostic invariant satisfied.

**(F-2) §3 implementation-sharing note (per RC re-review RC-3 cross-strengthening).** Registry line 68 ("all six Mento StableTokens share implementation `0x434563B0604BE100F04B7Ae485BcafE3c9D8850E`; the per-token addresses in §3.1-§3.6 are all proxies pointing at this shared implementation") — present only in the §3.1 COPm subsection. The implementation address is a single shared one across all six tokens, so this note arguably belongs in the §3 preamble (line 53) or in a parallel position in §3.2-§3.6. This is non-blocking; the information is captured once, the byte-equality test for the per-token entries is satisfied; readers reading §3.2-§3.6 first might miss the shared-implementation context. Advisory only — leave as-is is fine; if you want consistency, mirror the implementation note across the six entries or hoist it to §3 preamble.

**(F-3) "§7 (out-of-scope appendix)" parenthetical at line 144 + line 185.** When the §-numbering fix-up from Concern 5 lands, these two phrases need to become "§8 (out-of-scope appendix)" — note the parenthetical itself is correct phrasing for what §8 actually is, only the section number is wrong. Bundling reminder so the fix-up doesn't drop the parenthetical.

**(F-4) Compactness of §10 audit-trail-footer.** §10 is 4 sub-sections (§10.1-§10.5) with ~30 cross-references. Every one resolves. The compactness is honest — each cited artifact is genuinely load-bearing for the registry. No padding, no redundant cites. Good discipline given `feedback_pathological_halt_anti_fishing_checkpoint`'s discipline of explicit audit trails.

**(F-5) The §3 preamble at line 53 explicitly documents the byte-equality test methodology** ("mixed-case as recorded; case-folded comparison is the byte-equality test"). This is the right invariant — Ethereum addresses are case-insensitive at the consensus layer, EIP-55 mixed-case is a checksum format, and case-folded comparison is the correct byte-equality semantic. Good.

---

## §4 — Specific quotable language flagged for change

### CR-NEEDS-WORK — single bundled fix-up

**Replace `§7` → `§8` (or `§8.1` for the §1.3 immutability-invariant cross-reference and the §7-appendix-entry-1 reference) in the following 13 lines, leaving the genuine §7 slug-mapping section header (line 227) and the §7 closing-line at 242 unchanged:**

| File:line | Current text | Recommended replacement |
|---|---|---|
| `2026-04-25-mento-native-address-registry.md:21` | `Preserved in the audit-trail appendix at §7 ONLY` | `Preserved in the audit-trail appendix at §8 ONLY` |
| `:30` | `(and the §7 out-of-scope appendix entry)` | `(and the §8.1 out-of-scope appendix entry)` |
| `:144` | `cross-references back to §3 (in-scope) or §7 (out-of-scope appendix)` | `cross-references back to §3 (in-scope) or §8 (out-of-scope appendix)` |
| `:150` | `via inheritance — see §7` | `via inheritance — see §8` |
| `:151` | `OUT of Mento-native scope — see §7` | `OUT of Mento-native scope — see §8` |
| `:153` | `via inheritance — see §7` | `via inheritance — see §8` |
| `:154` | `OUT of Mento-native scope — see §7` | `OUT of Mento-native scope — see §8` |
| `:155` | `OUT of Mento-native scope — see §7` | `OUT of Mento-native scope — see §8` |
| `:156` | `via inheritance — see §7` | `via inheritance — see §8` |
| `:157` | `OUT of Mento-native scope — see §7` | `OUT of Mento-native scope — see §8` |
| `:158` | `via inheritance — see §7` | `via inheritance — see §8` |
| `:159` | `via inheritance — see §7` | `via inheritance — see §8` |
| `:160` | `see §5 + §7` | `see §5 + §8` |
| `:185` | `cross-reference §7 (out-of-scope appendix)` | `cross-reference §8 (out-of-scope appendix)` |
| `:204` | `OUT of Mento-native scope** under β; cross-reference §7.` | `OUT of Mento-native scope** under β; cross-reference §8.` |
| `:238` | `(audit-time live ingestion; per §7-appendix-entry-1)` | `(audit-time live ingestion; per §8.1)` |

**Why:** the §7 section in the doc is the slug-vs-canonical-ticker mapping table; the out-of-scope appendix is §8 (sole entry §8.1). All 16 cross-references above are mis-pointed and a reader following them lands on the wrong section. The §1.3 byte-exact-immutability invariant explicitly locks the §7 out-of-scope appendix entry, but §7 is not the appendix, so the immutability promise is technically vacuous on the actual appendix without the fix.

**Discipline:** the fix-up is annotation-only; it does not change any address, any tag total, any RC R-2 narrative, or the anti-fishing invariant integrity panel. It is non-anti-fishing-relaxing.

---

## §5 — Closure

**Verdict: NEEDS-WORK on the §7-vs-§8 cross-reference issue (Concern 5). After that single mechanical fix-up pass, would PASS.**

The seven other CR concerns are CONFIRMED. The byte-equality work is excellent (7-of-7 case-folded matches against the β-corrigendum block); the 14-table count + 10-`proxy_kind` count are both verifiable against sub-task 2's live-DuckDB pre-flight; the RC R-2 disambiguation narrative is exactly the right shape; the §3-vs-§8 partition has zero leakage (the §3 in-scope body never names Minteo-COPM); the anti-fishing invariants are honest and unrelaxed; the §9 non-canonical-source warning is actionable with two-layer-precedent-citation + four-authority-procedure specificity; and every audit-trail cross-reference resolves on disk.

The §7-vs-§8 fix is a single grep-and-edit pass against this one file with a deterministic outcome and zero risk of side effects on the heavy work.

**End of CR review.**
