# MR-β.1 Sub-task 3 Registry — Senior Developer (Implementation-Consumability) Review

**Date:** 2026-04-26.
**Reviewer:** Senior Developer (trio-member; replaces Tech Writer for sub-task 3).
**Trio peers (parallel, no coordination):** Code Reviewer + Reality Checker.
**Artifact under review:** `contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md` (commit `339a50480`, 335 lines).
**Sub-plan anchor:** `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` — §C sub-task 3.
**Lens:** Implementation consumability for downstream β-track Rev-3 ingestion plumbing under Task 11.P.spec-β + Task 11.P.exec-β. NOT empirical re-verification (RC's lens) or editorial / process-discipline (CR's lens).
**Inputs consumed:** registry doc (335 lines, full read); sub-task 1 inventory `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` lines 260-431 (§β-rescope appendix); sub-task 2 audit `contracts/.scratch/2026-04-25-duckdb-address-audit.md` lines 1-120.

---

## §1 — Verdict

**PASS-with-non-blocking-advisories.**

The registry is implementation-ready as a consumable artifact for β-track Rev-3 ingestion plumbing. Every concern in the dispatch brief (1-8) lands at CONFIRMED or CONFIRMED-with-minor-advisory; none rise to NEEDS-WORK or BLOCK level. The non-blocking advisories below are quality-of-life improvements for future implementers, not implementation-blockers — the β-spec author can scope around them or land them as a future-rev appendix without re-opening the registry's byte-exact-immutability invariant.

The advisories cluster in two areas: (a) §6.3 future-rev rename recommendation could be hoisted to a more discoverable location (currently embedded narratively in a §6 disambiguation entry, not in §10 audit-trail or §1 immutability invariant where future readers are most likely to navigate), and (b) §10.4 loader-helper interface paragraph is correct but slightly understates the consumption-time HALT-VERIFY check responsibility.

---

## §2 — Concern-by-concern findings

### §2.1 — Concern 1: Address-registry consumability for ingestion plumbing

**Finding: CONFIRMED.**

§3.1 records COPm at `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` in mixed-case (EIP-55 checksummed form). The form is unambiguous and ingestion-script-consumable verbatim.

Provenance citations are sufficient for a future implementer to reproduce ingestion plumbing without re-discovering the address:
- Primary on-chain: Dune query 7378788 (β-feasibility activity probe) **+** Dune project name `celocolombianpeso` **+** decoded-table name `celocolombianpeso_celo.stabletokenv2_evt_transfer`. A future ingester can filter the decoded `evt_transfer` table directly OR filter `erc20_celo.evt_transfer` on the contract address — both paths are determinable from the registry.
- Secondary docs: Mento V3 deployments URL with the post-RC-3 working anchor (legacy URL 404-flagged).
- Tertiary: Celo Token List entry verbatim with `name`, `symbol`, `decimals`, `chainId` for ABI-decoder sanity-check.

Mento Reserve relationship + basket-membership status are documented at the analytical-design grain: line 64 explicitly states "**0 events ingested into any DuckDB `onchain_*` table from this address**" — this is the load-bearing flag that tells β-spec the ingestion plumbing is greenfield (no inheritance from existing tables). The Reserve relationship line names the four Mento-protocol governance events (`evt_exchangeupdated`, `evt_validatorsupdated`, `evt_brokerupdated`, `evt_initialized`) — sufficient for a β-spec author choosing between mint/burn-flow ingestion vs. Transfer-event ingestion vs. governance-event ingestion.

The implementation-sharing note (line 68: shared implementation `0x434563B0604BE100F04B7Ae485BcafE3c9D8850E` across all six Mento StableTokens) is a useful disclosure for any future implementer using ABI-from-implementation decoding rather than per-proxy ABI lookup.

**Minor advisory (non-blocking).** The disposition-memo claim that COPm has "78 weeks of activity" while §β-rescope.3 in sub-task 1 (line 398) flags **"chronological joint [Y₃] window is approximately 73 weeks — 2 weeks short of N_MIN=75"** is *not* re-surfaced in this registry. A β-spec author reading the registry alone could miss the joint-N constraint. The registry is correctly editorial / declarative (joint-N feasibility belongs in β-spec), but a single-line forward pointer like "Joint-coverage feasibility with Y₃ panel is β-spec scope; cf. sub-task 1 §β-rescope.3 RC-8 note" would close the navigation gap. **Not BLOCKING** — sub-task 1 inventory is cited from §10.1 already, so a navigationally-careful reader will reach the joint-N note via the existing chain.

### §2.2 — Concern 2: DuckDB cross-reference utility (§4 as decision table)

**Finding: CONFIRMED.**

§4 is the strongest section in the registry from an implementation-consumability standpoint. The 14-table decision table is unambiguous on every axis a future implementer will exercise:

- **Each table's tag is unambiguous.** All 14 rows carry exactly one of {DIRECT in-scope, DIRECT mixed-scope, DIRECT DEFERRED-via-scope-mismatch, DERIVATIVE DEFERRED-via-scope-mismatch}. No row carries an ambiguous compound tag or a free-text "see notes" placeholder.
- **DERIVATIVE inheritance chains are traceable.** All 5 DERIVATIVE rows (`onchain_copm_address_activity_top400`, `onchain_copm_daily_transfers`, `onchain_copm_time_patterns`, `onchain_copm_transfers_sample`, `onchain_copm_transfers_top100_edges`) explicitly name parent `onchain_copm_transfers` in the "Address(es) or parent" column with the inheritance-reduction nature spelled out (e.g., "top-400 sender/receiver activity reduction", "daily aggregation: `n_transfers`, `n_tx`, `n_distinct_from`, `n_distinct_to`, `total_value_wei`"). A future implementer dropping the parent for a Mento-native re-ingestion can determine which downstream tables also become invalid without re-querying DuckDB.
- **DEFERRED-via-scope-mismatch carries a clear "do NOT consume" decision flag.** The "OUT of Mento-native scope — see §7" suffix (lines 151, 153, 155, 156, 157, 158, 159) is functionally a decision flag: any future implementer reading the row terminates Mento-native consumption immediately and navigates to §7 (which the registry author labelled §8 in the actual document — see Concern 6 advisory below) for audit-trail context.

**Tag totals (§4 footer, lines 165-169) sum to 14 exactly**, matching the live-DuckDB pre-flight enumeration count from sub-task 2 §1. This is the verifiable HALT-VERIFY check a future implementer can re-run via `SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'onchain_%' ORDER BY table_name`.

The §4 mixed-scope tag on `onchain_xd_weekly` (1 row) plus the §4 → §5 forward pointer to per-`proxy_kind` partition resolves the "mixed scope = need to look elsewhere for partition" problem cleanly: the registry doesn't try to encode 9 in-scope / 1 DEFERRED at the table-level cell, it forwards to §5 where the per-`proxy_kind` decision lives.

### §2.3 — Concern 3: proxy_kind enumeration usability (§5)

**Finding: CONFIRMED.**

§5 maps each of the 10 `proxy_kind` values to exactly one scope tag in the rightmost column ("Scope under β"). The 9 in-scope entries are clearly distinguishable from the 1 DEFERRED-via-scope-mismatch by the bolded marker (**In-scope** vs. **DEFERRED-via-scope-mismatch**). A future implementer adding β-track Rev-3 proxy_kinds gets:

- The full existing namespace (10 values) for collision detection.
- Per-kind row count + provenance + scope status in one row.
- Forward pointer to §3 sub-section for per-token addresses (e.g., "BRLm `0xe8537a3d…` (per §3.4)") — enabling cross-reference verification.
- Forward pointer to §7 (out-of-scope appendix; actually §8 in document) for the single DEFERRED entry.

The §5 footer (line 192) makes the implementation-relevant invariant explicit: "the per-currency COPM proxy was a diagnostic, not the primary X_d, so the scope-mismatch does NOT propagate to the primary estimates." This is the load-bearing finding for β-spec scope: existing Rev-5.3.2 published estimates are sound (under their own scope), and β-track Rev-3 ingestion plumbing additions land alongside, not as replacements for, the in-scope 9 proxy_kinds.

**Future-rev guidance is implicit but not explicit.** The §1.3 immutability invariant (line 31) states "Future address additions land as new appendix sections..." but does not explicitly extend to `proxy_kind` enumeration additions in §5. A strict reader could argue §5 is mutable for future additions (since adding a new row doesn't violate the "no in-place edits to existing per-token entries" wording in §1.3). Practical risk: low; the `decision_hash`-anchored Rev-2 estimates are byte-exact-immutable independently.

**Advisory (non-blocking).** A 1-line clarification at the §5 head — e.g., "Future β-track Rev-3 proxy_kinds (e.g., `mento_native_copm_volume_usd`) MUST be appended below row 10, never inserted between existing rows; existing rows 1-10 are byte-exact-immutable per §1.3 spirit" — would close the namespace-management ambiguity. The β-spec author can land this as a future-rev appendix at the registry without re-opening the spec body.

### §2.4 — Concern 4: `onchain_copm_ccop_daily_flow` future-rev rename guidance (§6.3)

**Finding: CONFIRMED-with-non-blocking-advisory.**

§6.3 (lines 215-223) records the rename recommendation in three explicit sub-bullets:
1. "**Drop the `_ccop_` slug fragment**" (rationale: pre-rebrand legacy artifact + ambiguous under Rev-5.3.5).
2. "**Re-slug as `onchain_copm_minteo_daily_flow`**" (rationale: pinning `_minteo_` qualifier prevents conflation).
3. "**If the `ccop_*` side later requires preservation in a separate table**" — a third-path provision for a hypothetical future need.

The "NOT executed under this sub-plan; recorded for future revision consideration only" clause is preserved at line 217 ("the recommendation below is **recorded for future revision consideration only**; no rename is executed under MR-β.1") and reaffirmed at line 223 ("sub-plan §B-2's 'no rename, no schema migration' invariant binds this sub-task"). A reader cannot misread §6.3 as a green-light to execute the rename now.

The rationale (`_ccop_` slug = pre-rebrand artifact + table holds two distinct out-of-scope tokens) is reproducible from §6.1 + §6.2 alone without external lookup:
- §6.1 lines 203-205 lay out the paired-source structure (`copm_*` half = Minteo-fintech `0xC92E8Fc2…`; `ccop_*` half = separately-named historical-cCOP via Dune query 7366593).
- §6.2 lines 209-213 lay out the dual-out-of-scope conclusion.

**Non-blocking advisory.** The future-rev rename recommendation is correctly recorded but **discoverability is suboptimal**. A future implementer touching the registry to plan Mento-native ingestion plumbing might never read §6 (the section is labelled "explicit disambiguation entry" — sounds like prose narrative, not implementation guidance). The recommendation could be hoisted to a more discoverable location:
- **Option A (preferred):** Add a single line to §10 audit-trail footer under a new §10.6 sub-section "Future-revision pending recommendations" with a one-line cross-reference to §6.3 + a one-line cross-reference to the §5 namespace-management advisory (Concern 3 above).
- **Option B (lighter):** Add a single line to §1.3 immutability invariant (line 31 area) noting "Future-rev rename recommendations recorded under §6.3 (table `onchain_copm_ccop_daily_flow`) and any future additions are out-of-scope under MR-β.1."

This is a quality-of-life improvement for downstream β-track Rev-3 implementers; not implementation-blocking. The β-spec author can land it as a §10.6 appendix at registry-edit-time without re-opening the byte-exact-immutability invariant on §3 / §6 / §8 entries.

### §2.5 — Concern 5: Slug-vs-canonical-ticker mapping completeness (§7 in document, slug map)

**Finding: CONFIRMED.**

The slug map at §7 (lines 227-242 — note the document calls this section "§7", not "§5"; the dispatch brief's §5/§7/§8 numbering refers to logical sections, not in-document section numbers; for clarity I use document section numbers here) is complete on the dispatch brief's checklist:

- **All 5 in-scope ticker slugs mapped:** `usdm` (line 233), `eurm` (line 234), `brlm` (line 235), `kesm` (line 236), `xofm` (line 237). Each row carries the canonical address verbatim (e.g., `0x765DE816845861e75A25fCA122bb6898B8B1282a` for usdm), the surface location (`carbon_per_currency_X_volume_usd` proxy_kind), the §3.X cross-reference for full per-token entry, and the asymmetry note ("None — slug matches canonical post-rebrand ticker; in-scope").
- **Ambiguous `copm` slug flagged with explicit warning** (line 238). The warning is multi-part: the table name fragment surface area is named ("`carbon_per_currency_copm_volume_usd` proxy_kind + 12 of 14 `onchain_copm_*` table names"), the audit-time resolution is named (Minteo-fintech `0xC92E8Fc2…`), and the cross-reference to the canonical Mento-native COPm `0x8A567e2a…` is named (per §3.1) along with the future-revision rename recommendation cross-reference. The "**AMBIGUOUS**" bolded tag plus the "future-revision rename recommendation may rename to `copm_minteo` or similar" are both explicit.
- **Legacy `ccop` slug fragment documented** (line 239). The row records the surface location (`onchain_copm_ccop_daily_flow` table name), the unspecified-address-source resolution ("Separately-named historical-cCOP token (address unspecified at audit-time read-only verification; sourced via Dune query `7366593`)"), and the asymmetry note ("Pre-rebrand legacy slug with no canonical post-rebrand address attribution; future-revision rename recommended in §6.3").

The bonus row (`copm_diff` column name in `onchain_y3_weekly`, line 240) is a high-quality disclosure: it captures the Y₃ panel column-name asymmetry that a future implementer might trip over if they conflate "any column named `copm_*`" with "Minteo-fintech-sourced." The note explicitly states "Column tracks Colombian-peso inequality-differential macro component, not on-chain Minteo-fintech events." This is exactly the disambiguation a downstream β-spec author needs when reasoning about Y × X joint-coverage.

### §2.6 — Concern 6: Out-of-scope appendix usability (§8)

**Finding: CONFIRMED.**

§8 (lines 246-267) is structurally well-isolated from the in-scope §3 body:
- **Section title clearly marks out-of-scope status:** "§8 — Out-of-scope third-party tokens (audit-trail preservation)" (line 246). The "(audit-trail preservation)" parenthetical doubles the signal.
- **Headnote explicitly states "Entries here are NOT registry entries"** (line 248): "they are explicitly excluded from the §3 in-scope per-token registry; they are documented to make the Rev-5.3.5 β-disposition's scope-mismatch decision visible to future readers." This is the load-bearing language that prevents accidental in-scope consumption.
- **§8.1 (COPM-Minteo) carries explicit scope tag** (line 259): "**OUT of Mento-native scope** per `project_abrigo_mento_native_only` (β-corrigendum extension) and Rev-5.3.5 CORRECTIONS block in major plan."
- **Mento-protocol fields are explicitly NOT enumerated** for the out-of-scope entry (line 263): "**NOT APPLICABLE** — Mento-protocol fields are not enumerated for an out-of-scope third-party token; this entry exists for audit-trail preservation only." This is the structural difference between an in-scope §3 entry (Reserve / basket / issuance fields populated) and an out-of-scope §8 entry (those fields explicitly absent).
- **Cross-references to §4 DEFERRED-via-scope-mismatch entries are explicit** (line 264): "All 10 `onchain_copm_*` tables (5 DIRECT + 5 DERIVATIVE) and 1 `proxy_kind` (`carbon_per_currency_copm_volume_usd`) tagged DEFERRED-via-scope-mismatch in §4 + §5."
- **Future out-of-scope additions guidance** (line 267): "if a future sub-plan discovers an additional out-of-Mento-native-scope token whose preservation is audit-warranted, that token's appendix entry lands under a new section (§8.2, §8.3, ...) — never as an in-place edit to §8.1 or as an entry in §3." This closes the namespace-management ambiguity for the out-of-scope appendix (compare with the §5 in-scope-namespace ambiguity flagged in Concern 3 advisory above).

The "DO NOT INGEST FOR MENTO-NATIVE β-TRACK" decision flag the dispatch brief asked for is functionally present via the combination of (a) section title's "Out-of-scope" + "(audit-trail preservation)" markers, (b) headnote's "Entries here are NOT registry entries," (c) §8.1's "**OUT of Mento-native scope**" bolded tag, and (d) §4 row-level "OUT of Mento-native scope — see §7 [sic — should read §8]" markers. The decision flag is distributed across four reinforcing sites; functionally equivalent to a single bolded "DO NOT INGEST" header.

**Minor cross-reference inconsistency (non-blocking).** The §4 rows at lines 150, 152, 153, 154, 155, 156, 157, 158, 159, 160 say "see §7" or "see §7" suffixes when pointing at the out-of-scope appendix. The out-of-scope appendix is at §8 in the document, not §7 (§7 is the slug map). This is a numbering drift — likely a section was renumbered late in authoring and the §4 cross-references were not refreshed. **Not BLOCKING** because the section titles are self-evident on navigation (a future implementer landing at §7 sees "Slug-vs-canonical-ticker mapping" and continues to §8 "Out-of-scope third-party tokens"). The β-spec author or the next CORRIGENDUM can refresh "see §7" → "see §8" in §4 row-level cross-references at registry-edit-time.

### §2.7 — Concern 7: Audit-trail footer (§10) for downstream debugging

**Finding: CONFIRMED.**

§10 provides the full navigational chain a downstream debugger needs:

- **Disposition memo path cited:** §10.2 line 301 — "**HALT-VERIFY disposition memo (β path):** `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` (disposition commit `00790855b`)."
- **All 3 trio review files cited:** §10.2 line 302 — "**3-way disposition review trio:** `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-code-reviewer.md`, `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-reality-checker.md`, `contracts/.scratch/2026-04-26-rev535-beta-disposition-review-technical-writer.md`." All three trio members named.
- **RC re-review file cited:** §10.2 line 303 — "**Sub-plan trio convergence on fix-up bundle:** commit `b4a6a50e6`." (The RC re-review converged at this commit per sub-task 1 §β-rescope.4 line 409.)
- **Sub-task RC spot-checks cited:** §10.2 lines 304-305 — "**Sub-task 1 RC spot-check:** `contracts/.scratch/2026-04-25-subtask-mr-beta-1-1-rc-spot-check.md` (commit `3286dfe66`); RC PASS-w-β-advisory at commit `eb72f7133`. **Sub-task 2 RC spot-check:** RC PASS-w-1-line-correction-inline at commit `09bacc105`."
- **Live DuckDB connection details cited:** §10.4 lines 318-321 — path (`contracts/data/structural_econ.duckdb`), read-only invariant (no write SQL issued under MR-β.1), loader-helper interface (`load_onchain_xd_weekly(proxy_kind=...)`, `load_onchain_y3_weekly(...)`), and HEAD anchor (`865402c2c+` on `phase0-vb-mvp`).

A future implementer debugging "why does the registry say COPm is at `0x8A567e2a…` when the old `econ_pipeline.py` references `0xc92e8fc2…`?" can navigate:
1. §10.2 → disposition memo → HALT-VERIFY content + 3 trio reviews.
2. §10.3 → major plan Rev-5.3.5 CORRECTIONS block + project memory β-corrigenda.
3. §10.4 → live DuckDB path + loader-helper interface + HEAD commit.
4. §10.5 → anti-fishing invariants integrity confirmation (no relaxation, just scope correction).

**Minor advisory (non-blocking).** §10.4 line 320 ("Address byte-equality between this registry and the loader-helper-observed schema is the verifiable HALT-VERIFY check at consumption time") states the consumption-time HALT-VERIFY check correctly but slightly understates *whose* responsibility it is. A future implementer reading line 320 might believe the loader-helper itself enforces byte-equality at runtime (it does not, at audit time). The β-spec author should make explicit in β-spec that the byte-equality check is the ingestion-script's responsibility at consumption time, not the loader-helper's runtime invariant. **Not registry's concern to resolve** — the registry correctly delegates this to β-spec.

### §2.8 — Concern 8: Implementation-readiness gating (registry stays declarative)

**Finding: CONFIRMED.**

I scanned the registry for imperative implementation language ("the ingester MUST run this query", "the loader MUST mutate this column", "execute the rename", etc.). The registry stays correctly declarative throughout:

- §3 per-token entries: declarative (field/value tables; no instructions).
- §4 DuckDB cross-reference: declarative (tags + addresses + cross-references; no instructions).
- §5 proxy_kind enumeration: declarative (rows + scope tags + provenance; no instructions).
- §6.3 future-rev rename: explicitly **NOT** an instruction — line 217 ("recorded for future revision consideration only; no rename is executed under MR-β.1") and line 223 ("sub-plan §B-2's 'no rename, no schema migration' invariant binds this sub-task") double-bolt the non-imperative framing.
- §7 slug map: declarative (annotation-only per line 242: "**No rename executed under this sub-plan per §B-2.** All slug-asymmetry notes above are annotation-only").
- §8 out-of-scope: declarative (preservation-only per headnote line 248).
- §9 non-canonical-source warning: prescriptive language is present but is **process-discipline for future research**, not implementation steps for any code (line 285 "**Failure to triangulate before propagating a token-identity claim into specs / plans / code / project memory is an anti-fishing-banned shortcut**"). This is a research-process MUST, not an ingestion-script MUST. Acceptable per `feedback_no_code_in_specs_or_plans` — research-process discipline is meta-spec, not implementation code.
- §10 audit-trail footer: declarative (path citations + invariant integrity + commit anchors).

The §1.1 Purpose statement is the only place where the word "MUST" appears in a prescriptive sense (line 15: "every downstream β-track and α-track artifact that names a Mento-native token MUST cross-check against this registry before propagating an address into specs, plans, code, or project memory"). This is a cross-reference discipline directive, not an implementation step — it tells future spec / plan / code authors to consult the registry, which is the purpose of a registry. Acceptable.

The §2 procedure ("every Mento-native address in §3 was triangulated against the following four authorities. Future research that touches Mento-native token identity MUST follow the same procedure...") is research-process discipline — same acceptable framing as §9.

**No imperative implementation language found.** The registry is 100% declarative / editorial / cross-reference-discipline. β-spec author can consume the registry without inheriting any spec-level imperative steps.

---

## §3 — Additional findings outside the 8 dispatch concerns

### §3.1 — §4 cross-reference numbering drift (already flagged in Concern 6)

§4 row-level cross-references say "see §7" when pointing at the out-of-scope appendix; the appendix is actually at §8 in the document. Numbering drift, non-blocking, β-spec author or next CORRIGENDUM can fix.

### §3.2 — `MDES_FORMULATION_HASH` and `decision_hash` echoed in §10.5

§10.5 (line 328-329) echoes the SHA256-pinned `MDES_FORMULATION_HASH` and `decision_hash`. This is correct anti-fishing-invariant integrity preservation (no relaxation under β-disposition). For a future debugger checking "did the β-rescope silently change Rev-2's anti-fishing thresholds?", §10.5 is the load-bearing artifact. Confirmed unchanged from Rev-2 published values per `project_mdes_formulation_pin` and `project_rev531_n_min_relaxation_path_alpha`.

### §3.3 — No claims about β-spec data freeze date or β-spec timeline

The registry correctly avoids any implementation-timeline claims about Task 11.P.spec-β / Task 11.P.exec-β. It refers to those tasks as the consumers of this registry but does not pre-commit β-spec to any particular Y₃ panel refresh date or N_MIN-relaxation path. Joint-N feasibility is correctly delegated to β-spec via the §β-rescope.3 RC-8 forward-looking note in sub-task 1 (which the registry chains to via §10.1 line 294 cross-reference). This is the right scope-discipline for a registry.

### §3.4 — Implementation-sharing note (line 68) only on COPm entry

The RC re-review independent finding that "all six Mento StableTokens share implementation `0x434563B0604BE100F04B7Ae485BcafE3c9D8850E`" is recorded only on the §3.1 (COPm) entry, not echoed on §3.2-§3.6. A future implementer using ABI-from-implementation decoding for any of USDm / EURm / BRLm / KESm / XOFm can derive the shared-implementation fact only by reading §3.1 first. **Non-blocking** because the shared implementation is one of the four authoritative-triangulation procedure outputs in §2 (Dune `searchTablesByContractAddress`), and the registry isn't an implementation-decoder reference manual. β-spec ABI-decoder design can echo the shared implementation explicitly in the β-spec body if useful.

---

## §4 — Implementation-consumability advisory for β-track Rev-3

**β-track Rev-3 implementation difficulty: LOW-to-MODERATE; greenfield ingestion plumbing with no DuckDB inheritance constraints.**

The registry's §3.1 entry establishes that COPm `0x8A567e2a…` has **0 events ingested into any DuckDB `onchain_*` table** at registry-authoring time (line 64). β-spec authoring under Task 11.P.spec-β + Task 11.P.exec-β therefore lands as **net-new ingestion plumbing**, not a migration of an existing pipeline. The pre-existing `onchain_copm_*` tables (Minteo-fintech `0xC92E8Fc2…`) stay byte-exact-immutable per the §1.3 immutability invariant; a new table family (e.g., `onchain_copm_v2_transfers`, `onchain_copm_v2_daily_flow`) lands alongside. The principal scoping concern for β-spec is the **joint-N feasibility** under the live Y₃ panel (sub-task 1 §β-rescope.3 RC-8 note flags ~73-week joint window vs. N_MIN=75 — 2 weeks short, with two pre-registered resolutions: refresh Y₃ forward, OR document and pre-commit relaxation-or-defer disposition under `feedback_pathological_halt_anti_fishing_checkpoint` discipline). The registry does not constrain the β-spec author's choice between those two paths.

---

**End of Senior Developer review.**
