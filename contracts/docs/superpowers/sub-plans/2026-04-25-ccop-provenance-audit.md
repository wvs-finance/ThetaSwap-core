# Sub-plan — Task 11.P.MR-β.1: Mento-native on-chain address registry + cCOP-vs-COPM provenance audit

**Status:** AUTHORED, awaiting 3-way review (CR + RC + TW spec-review trio per `feedback_three_way_review`).

**Authoring revision:** Rev-5.3.4 rescoped scope.

**Major-plan anchor:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` — Task 11.P.MR-β.1 super-task body (Rev-5.3.3 CORRECTIONS block, line ~2233 per CR live-grep) as RESCOPED by the Rev-5.3.4 CORRIGENDUM block (line ~2370+, formal RESCOPE statement at line ~2383). Line numbers are CR-verified at review time and may drift on subsequent major-plan revisions; the canonical anchor is the named CORRIGENDUM block, not the line number.

**Editorial scope:** code-agnostic; no Python or SQL bodies; backticked addresses, paths, table names, and source-citation hashes are permitted. No data is moved; no DuckDB rows are mutated; no project-memory file is overwritten by the act of authoring this sub-plan (memory updates happen WITHIN sub-task execution under the dispatched subagent's review, not at sub-plan authoring time).

---

## A. Trigger

Rev-5.3.3 introduced Task 11.P.MR-β.1 as a "cCOP-vs-COPM provenance audit + memory corrigendum" deliverable in response to Trend Researcher (`a7cd002b89b23e0ac`) Finding 3, which had attributed the Mento-native Colombia token identity to *cCOP* and the address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` to *cCOP* (not COPM).

The user corrected the attribution 2026-04-25 mid-Rev-5.3.3: *"is COPM not cCOP."* Pre-existing project memory `project_mento_canonical_naming_2026` ("COPM and XOFm unchanged; address-level identity preserved") was correct all along; the address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` resolves to **Mento-native COPM**, not to a separate cCOP token. The Rev-5.3.4 CORRIGENDUM (in the major plan, immediately following the Rev-5.3.3 CORRECTIONS block) ratified this correction and **rescoped** Task 11.P.MR-β.1.

**Original framing (Rev-5.3.3, now superseded).** "Correct the project memory naming error and update DuckDB schema docs to reflect that `onchain_copm_transfers` tracks Mento-native cCOP."

**Rescoped framing (Rev-5.3.4, authoritative).** "Formally lock the on-chain address registry for the Mento-native basket — COPM at `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` plus the post-rebrand USDm/EURm/BRLm/KESm addresses + the unchanged XOFm address — with a single canonical reference document, and append a corrigendum to the Trend Researcher report so the project's audit trail makes the inverted attribution explicit and points future research at the on-chain registry as the authoritative cross-check."

The two project-memory files load-bearing on this sub-plan are:

- `project_mento_canonical_naming_2026` — authoritative on COPM identity; **no corrigendum needed.** This memo establishes the post-2026-rebrand canonical names: USDm (was cUSD), EURm (was cEUR), BRLm (was cREAL), KESm (was cKES), with COPM and XOFm unchanged; address-level identity is preserved across the rebrand.
- `project_abrigo_mento_native_only` — Abrigo scope is Mento-native stablecoins ONLY; non-Mento third-party tokens are out of scope; this memo already carries an internal corrigendum acknowledging the TR-mis-attribution-then-user-correction sequence and is the authoritative scope record going forward.

This sub-plan therefore does NOT modify either of those memory files; it consumes them as authoritative inputs. The TR research file (`contracts/.scratch/2026-04-25-mento-userbase-research.md`) is annotated with a corrigendum block as one sub-task; the TR's body content (Findings 1, 2, 4) remains a useful research artifact and is preserved.

---

## B. Pre-commitment

The following invariants are pre-committed BEFORE any sub-task is dispatched. They cannot be relaxed by sub-task execution; any sub-task that would force a relaxation must HALT to the user with an explicit pivot note per `feedback_pathological_halt_anti_fishing_checkpoint`.

1. **Consume-only DuckDB invariants.** No DuckDB row is mutated, deleted, or re-keyed. The Rev-5.3.2 published estimates remain byte-exact. The `decision_hash` (sha256 `6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c`) and `MDES_FORMULATION_HASH` (sha256 `4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa`) are immutable.
2. **No table renames; no schema migrations.** The table `onchain_copm_transfers` retains its name as the canonical Mento-native COPM transfers table. The `onchain_xd_weekly` table retains its `proxy_kind` enumeration (10 active proxy_kinds confirmed in Rev-5.3.2 design doc §3 row table). Any naming clarifications land as schema-doc comments, loader-helper docstring annotations, or addendum notes in spec docs — never as renames or migrations under this sub-plan.
3. **Address registry is the future authoritative source.** The canonical reference document produced by this sub-plan (sub-task 3 below) is the on-chain-address source-of-truth for every downstream β-track and α-track artifact. Future research that cites third-party Celo-forum / similar external sources MUST cross-check token identity against the address registry produced here; failure to cross-check is an anti-fishing-banned shortcut.
4. **Anti-fishing on memory edits.** Project-memory edits in sub-tasks are append-only or section-replace-with-corrigendum. No memory file is silently rewritten without an explicit corrigendum trail. The two load-bearing memory files (`project_mento_canonical_naming_2026`, `project_abrigo_mento_native_only`) require NO further edits under this sub-plan; if a sub-task discovers a need to edit one of them, that discovery HALTS to the user.
5. **Editorial-only deliverable.** This sub-plan ships documentation: an audit memo (sub-task 1), a DuckDB-table-to-address audit (sub-task 2), the canonical address-registry spec doc (sub-task 3), a corrigendum block in the TR research file (sub-task 4), and a future-research safeguard note (sub-task 5). No analytical work, no spec revision, no econometric estimation, no notebook authoring is in scope.
6. **Rev-5.3.4 RESCOPE supersedes Rev-5.3.3 framing.** Wherever a Rev-5.3.3 phrase implies a project-memory naming error needs correction, treat that phrase as superseded — the memory was correct; the agent's brief Rev-5.3.3 attribution flip was wrong; the user has already corrected it; the registry-lock is the rescoped deliverable. Any sub-task output that reverts to the Rev-5.3.3 framing fails acceptance.
7. **TR research file is preserved with corrigendum, not deleted.** The Trend Researcher's report (`contracts/.scratch/2026-04-25-mento-userbase-research.md`) remains in the audit trail. The corrigendum is appended at the file's end (or as an explicit prefix block) and is the authoritative override. Findings 1, 2, and 4 remain useful evidence; Finding 3's token attribution is the override target.

---

## C. Sub-tasks

Five sub-tasks decompose the rescoped deliverable. Each sub-task carries its own deliverable, acceptance criteria, dispatched subagent, reviewer assignment, and dependency note.

### Sub-task 1 — On-chain address inventory

**Deliverable.** A structured audit memo enumerating the canonical on-chain contract address for each Mento-native stablecoin currently in scope, with provenance citation and verification fields per token. The memo lands at `contracts/.scratch/2026-04-25-mento-native-address-inventory.md` (research-style intermediate artifact; the final canonical reference doc is sub-task 3's spec doc, which consumes this memo as input).

For each Mento-native stablecoin in scope, the memo records:

- **Ticker** — the canonical post-2026-rebrand ticker (COPM, USDm, EURm, BRLm, KESm, XOFm).
- **Pre-rebrand legacy ticker** — where applicable (cUSD, cEUR, cREAL, cKES); for COPM and XOFm, "unchanged" is recorded.
- **Contract address on Celo** — the bytes-32-checksummed address.
- **Deployment date / first-observed-on-chain date** — sourced from on-chain query (Celoscan, Dune, or first-Transfer-event scan); if precise deployment date is not recoverable from the canonical sources within the sub-task budget, "first-observed-on-chain in <year>-<quarter>" is acceptable provenance.
- **Mento Reserve relationship** — confirmed via Mento Labs documentation (Mento protocol contract registry and/or Mento Labs governance disclosures). Each token's relationship to the Mento Reserve (issuance, redemption, basket-membership) is documented at the citation level, not the analytical level.
- **Basket-membership status** — confirmation that the token is part of the Mento basket the Abrigo project consumes; out-of-basket tokens are NOT enumerated even if they exist on Mento.
- **Provenance citation** — the source(s) used to confirm each of the above fields. Multiple sources per field where available; primary preference is on-chain (Celoscan / direct RPC / Dune queries against canonical Mento contracts) and secondary preference is Mento Labs official documentation.

The supply field is **deliberately omitted from the registry**. Total supply moves over time and would conflict with the §B-3 / sub-task 3 byte-exact-immutability invariant of the canonical registry. Auditors and downstream consumers needing current supply MUST query live DuckDB / Celoscan / Dune at consumption time; the registry is a token-identity / address-provenance artifact, not a circulating-supply dashboard. Rationale recorded under RC review finding R-3 (post-author CORRECTIONS, 2026-04-26).

**Acceptance.** Memo enumerates all six Mento-native tokens (COPM, USDm, EURm, BRLm, KESm, XOFm). Every address matches the addresses recorded in `project_mento_canonical_naming_2026`. Every provenance field has at least one citation; on-chain provenance is preferred to web/forum-source provenance wherever both are available. Where the audit discovers a discrepancy between project-memory addresses and on-chain reality, the discrepancy HALTS to the user immediately per `feedback_pathological_halt_anti_fishing_checkpoint` rather than being silently overridden in the memo.

**Subagent.** Data Engineer (DuckDB / on-chain inspection competence; per `feedback_specialized_agents_per_task` and `feedback_implementation_review_agents` for implementation-adjacent corrigendum work).

**Reviewers.** Reality-Checker spot-check (single-pass, advisory) per RC R-4, to verify each enumerated address text-matches `project_mento_canonical_naming_2026` and provenance citations resolve; no full trio review at this sub-task level (sub-task 1 is an intermediate research artifact consumed by sub-task 3, which carries the convergent CR + RC + SD trio review).

**Dependency.** None internal to this sub-plan; dependent only on access to Celo on-chain query infrastructure and Mento Labs documentation (already established under prior tasks).

### Sub-task 2 — DuckDB table-to-address audit

**Deliverable.** An audit memo verifying which Mento-native token each existing DuckDB `onchain_*` table tracks, landed at `contracts/.scratch/2026-04-25-duckdb-address-audit.md`. The memo enumerates **every** live `onchain_*` table and confirms (or flags) the on-chain source per RC review finding R-1 (the §B-3 invariant claim of registry as source-of-truth for "every downstream β-track and α-track artifact" requires complete coverage, not partial).

**Annotation target file (per RC R-5).** The canonical address registry document at `contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md` (sub-task 3 deliverable) is the **authoritative annotation target** for `contract_address` provenance. Per-table table-comment annotations, loader-docstring edits, and `econ_schema.py` schema comments are explicitly **out of scope** for this sub-plan; the registry doc carries all per-table address linkage in its DuckDB cross-reference table (sub-task 3 §). This avoids the multi-file annotation drift risk RC flagged.

**Pre-flight enumeration query (REQUIRED).** Before authoring the audit memo, the dispatched Data Engineer MUST run the following enumeration query against live DuckDB to surface the authoritative table list and ground the audit in live state, not stale recollection:

```
SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'onchain_%' ORDER BY 1
```

(Equivalent DuckDB form: `SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'onchain_%' ORDER BY table_name`.) The query result becomes the audit's authoritative inventory; any divergence between the query result and the artifacts enumerated below HALTS to the user per `feedback_pathological_halt_anti_fishing_checkpoint`.

**Coverage classification scheme (REQUIRED).** Every `onchain_*` table the pre-flight enumeration returns MUST be tagged with exactly ONE of three coverage labels:

- **DIRECT** — the table consumes raw on-chain Transfer / event data scoped by `contract_address`; requires its own address-attribution audit linking the table to a Mento-native address from sub-task 1's inventory. The audit memo records the address(es), the relationship to the canonical registry, and any slug-vs-canonical asymmetry.
- **DERIVATIVE** — the table is computed from another `onchain_*` table (the parent) and inherits its address attribution. The audit memo names the parent table and the inheritance chain (e.g., `onchain_copm_transfers_top100_edges` is DERIVATIVE of `onchain_copm_transfers`; the COPM address attribution flows through). No separate address audit required; the inheritance documentation is the audit.
- **DEFERRED** — the table is already deferred under prior Rev-5.3.x scope (e.g., authored ahead of need; not yet consumed by any β-track or α-track artifact). The audit memo records the deferral and the upstream Rev-5.3.x scope decision that pinned the deferral; no audit body is required but the explicit DEFERRED tag is.

**Artifacts in scope (live DuckDB, 14 tables).** The 14 live `onchain_*` tables (per the Reality Checker's pre-flight live-DuckDB probe at review time, which the Sub-task 2 dispatched subagent re-confirms via the pre-flight enumeration query above):

- **`onchain_copm_transfers`** — DIRECT. Confirm this table tracks COPM at `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` (Mento-native, per the rescoped deliverable). The address linkage is documented in the registry doc (sub-task 3); no column rename or table rename is performed.
- **`onchain_copm_ccop_daily_flow`** — DIRECT, with **explicit narrative treatment per RC R-2** (the table name literally embeds the cCOP-vs-COPM ambiguity that the rescoped Rev-5.3.4 deliverable exists to lock down). The audit memo MUST: (a) verify which addresses the table actually filters on (single-address COPM vs. paired COPM-and-some-cCOP-historical-data vs. another configuration); (b) document in the registry doc whether the table tracks COPM, cCOP-historical-data, or both; (c) recommend (do **NOT** execute) a future-revision rename if the table-name confusion is judged a real footgun; per §B-2 no rename happens under this sub-plan, but a recommendation is recorded for a future rev's consideration.
- **`onchain_copm_daily_transfers`** — likely DERIVATIVE of `onchain_copm_transfers` (daily aggregation). Verify and document the inheritance chain.
- **`onchain_copm_burns`**, **`onchain_copm_mints`** — DIRECT or DERIVATIVE; verify per pre-flight schema inspection. If sourced from raw Transfer events filtered by `from = 0x0…` / `to = 0x0…`, classify DIRECT and link to the COPM address; if computed from `onchain_copm_transfers`, classify DERIVATIVE.
- **`onchain_copm_freeze_thaw`** — DIRECT or DERIVATIVE; verify and document.
- **`onchain_copm_time_patterns`** — DERIVATIVE (diurnal pattern aggregation); inheritance chain documented.
- **`onchain_copm_address_activity_top400`**, **`onchain_copm_transfers_top100_edges`**, **`onchain_copm_transfers_sample`** — DERIVATIVE of `onchain_copm_transfers` (top-N / sample reductions); inheritance chain documented.
- **`onchain_carbon_arbitrages`**, **`onchain_carbon_tokenstraded`** — DIRECT. Carbon DeFi raw event tables; address attribution lives at this level (`trader = 0x8c05ea30…` for the BancorArbitrage partition per `project_carbon_user_arb_partition_rule`). Confirm the on-chain contract addresses (CarbonController `0x66198711…`, BancorArbitrage `0x8c05ea30…` per `project_carbon_defi_attribution_celo`) and link them to the registry doc.
- **`onchain_xd_weekly`** — DIRECT (proxy aggregation table; the 10 `proxy_kind` enumeration below carries the per-proxy address-source verification).
- **`onchain_y3_weekly`** — DIRECT or DEFERRED depending on whether the Y₃ inequality-differential panel is currently consumed by any active β-track / α-track artifact at audit time. The §B-3 invariant covers this table; verify and tag.

**`onchain_xd_weekly` proxy_kinds (10 active values, Rev-5.3.2 design doc §3 row table; lowercase canonical slugs match live state).** For each `proxy_kind`, the audit confirms (a) the on-chain address(es) feeding the proxy series, (b) whether the address is Mento-native per sub-task 1's inventory, (c) any naming asymmetry between the `proxy_kind` slug and the address-level identity:

- `carbon_basket_user_volume_usd` (primary X_d; Carbon DeFi user-side basket volume in USD)
- `carbon_basket_arb_volume_usd` (Carbon DeFi arbitrageur-side basket volume; partition rule per `project_carbon_user_arb_partition_rule` — `trader = 0x8c05ea30…`)
- `b2b_to_b2c_net_flow_usd` (supply-channel diagnostic; pre-existing; verify Mento-native scope)
- `net_primary_issuance_usd` (supply-channel diagnostic; pre-existing; verify Mento-native scope)
- `carbon_per_currency_copm_volume_usd`
- `carbon_per_currency_brlm_volume_usd`
- `carbon_per_currency_eurm_volume_usd`
- `carbon_per_currency_kesm_volume_usd`
- `carbon_per_currency_usdm_volume_usd`
- `carbon_per_currency_xofm_volume_usd`

The slug strings shown here use lowercase canonical tickers (`copm`, `brlm`, `eurm`, `kesm`, `usdm`, `xofm`) which match the live DuckDB `proxy_kind` keys per the Reality Checker's live `SELECT DISTINCT proxy_kind` probe. Where any legacy-ticker slug surfaces during audit (e.g., a `carbon_per_currency_cREAL_volume_usd` historical artifact), the audit documents the slug-vs-canonical-ticker mapping in the registry doc without renaming, per `project_mento_canonical_naming_2026`.

**Acceptance.** Memo:

1. Records the pre-flight enumeration query result (the live-DuckDB authoritative table list) at the top.
2. Tags **every** `onchain_*` table the query returns with exactly ONE of {DIRECT, DERIVATIVE, DEFERRED}; no table is silently omitted.
3. For DIRECT tables, records the on-chain address(es) and links to sub-task 1's inventory; any non-Mento address HALTS to the user per the consume-only invariant.
4. For DERIVATIVE tables, records the parent table and inheritance chain.
5. For DEFERRED tables, records the prior Rev-5.3.x scope decision that pinned the deferral.
6. Enumerates all 10 `proxy_kind` values from `onchain_xd_weekly` with explicit address-level provenance per `proxy_kind`.
7. Treats `onchain_copm_ccop_daily_flow` per RC R-2 explicit narrative treatment (verify filter addresses; document COPM vs. cCOP-historical-data scope; record future-revision rename recommendation, no execution).
8. Documents any table-name vs. on-chain-source mismatch as a slug-asymmetry note, not a rename request.

Coverage completeness is verifiable: count(tagged tables) MUST equal count(rows from pre-flight enumeration query). Any divergence HALTS.

**Subagent.** Data Engineer (same competence set as sub-task 1).

**Reviewers.** Reality-Checker spot-check (single-pass, advisory) per RC R-4, to verify the pre-flight enumeration query was actually run and the coverage-completeness count matches; no full trio review at this sub-task level (the trio review on the consumed registry doc at sub-task 3 carries the convergent quality signal).

**Dependency.** Sub-task 1 complete (the address inventory is the cross-check for table-source confirmation).

### Sub-task 3 — Canonical address-registry spec doc

**Deliverable.** The single canonical reference document for every on-chain address the Abrigo project consumes, landed at `contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md`. This is the rescoped Rev-5.3.4 PRIMARY DELIVERABLE.

The doc consumes sub-task 1's inventory + sub-task 2's table-to-address audit and produces a single canonical reference with the following structure:

- **Header** — title, authoring date, Rev-5.3.4 anchor, immutability scope (the registry is the source-of-truth post-converge; future address additions land as appendix sections, never as in-place edits to the existing entries).
- **Scope** — explicit Mento-native-only scope per `project_abrigo_mento_native_only`; explicit out-of-scope list (cCOP if it exists separately, Minteo-fintech tokens if they exist, all non-Mento third-party stablecoins, all non-Mento Celo tokens except as Mento-basket counter-side liquidity).
- **Per-token section** — one section per Mento-native token (COPM, USDm, EURm, BRLm, KESm, XOFm). Each section enumerates: ticker (post-rebrand canonical), legacy ticker (where applicable), contract address on Celo (bytes-32-checksummed), deployment / first-observed date, Mento Reserve relationship, basket-membership status, primary provenance citations, secondary provenance citations. Total supply is **explicitly out of scope** for the registry per RC R-3 immutability hygiene; consumers needing current supply query live DuckDB / Celoscan / Dune at consumption time.
- **DuckDB cross-reference table** — for **every** `onchain_*` table tagged DIRECT or DERIVATIVE under sub-task 2 (and, by entry, every `proxy_kind` in `onchain_xd_weekly`), document which Mento-native token (or basket aggregation) the artifact tracks, with explicit address linkage to the per-token sections above. DEFERRED tables are listed in an explicit "Deferred — not currently audited" sub-section with the prior Rev-5.3.x scope decision recorded, so a future reader sees the deferral instead of inferring an omission.
- **`onchain_copm_ccop_daily_flow` explicit disambiguation entry (per RC R-2)** — the registry doc carries an explicit per-table entry for `onchain_copm_ccop_daily_flow`, recording: (a) which on-chain addresses the table actually filters on (verified under sub-task 2); (b) whether the table tracks COPM, cCOP-historical-data, or both; (c) a doc-level disambiguation note that the `_ccop_` slug fragment is a pre-rebrand legacy artifact preserved for migration-stability reasons per `project_mento_canonical_naming_2026` (or, if sub-task 2 finds the slug actually misrepresents content, an explicit recommendation for a future-revision rename — no rename executed under this sub-plan per §B-2). This is the single most pointed naming-confusion artifact in the project; it MUST appear by name in the registry doc, not be aggregated into a generic note.
- **Slug-vs-canonical-ticker mapping** — explicit table mapping legacy `proxy_kind` slug fragments (`copm`, `brlm`, `eurm`, `kesm`, `usdm`, `xofm`) to canonical addresses, since the slugs may have been authored before the 2026 rebrand and were intentionally not mass-renamed for migration-stability reasons.
- **Non-canonical-source warning** — explicit note that third-party Celo-forum posts, social-media discussions, and similar external sources have demonstrated inverted-attribution failure modes (citing the TR Finding 3 episode); future research that cites such sources MUST cross-check against this registry.
- **Audit-trail footer** — pointer to sub-task 1's inventory memo, sub-task 2's table-audit memo, the TR research file with corrigendum, and the Rev-5.3.3 + Rev-5.3.4 plan blocks.

**Acceptance.** Doc passes 3-way review (CR + RC + Senior Developer per `feedback_implementation_review_agents`, since this is implementation-adjacent corrigendum work, not spec-authoring of analytical content). Every per-token section's address matches `project_mento_canonical_naming_2026`. Every DuckDB cross-reference matches sub-task 2's audit. The non-canonical-source warning is explicit and actionable. The doc is byte-exact-immutable post-converge; future address additions land as new appendix sections.

**Subagent.** Data Engineer authors the registry doc body; Technical Writer is OPTIONALLY consulted for clarity/structure pass before the spec-review trio (per `feedback_three_way_review` precedent of TW-pre-review-pass for high-visibility reference docs).

**Reviewers.** CR + RC + Senior Developer per `feedback_implementation_review_agents`.

**Dependency.** Sub-tasks 1 and 2 complete.

### Sub-task 4 — TR research report corrigendum

**Deliverable.** A corrigendum block appended to `contracts/.scratch/2026-04-25-mento-userbase-research.md` (appended at the file's end as a clearly-labeled section, OR placed as an explicit prefix block at the file's top — the choice is left to the dispatched subagent and reviewers, with preference for the prefix-block placement because future readers encounter the corrigendum before reading Finding 3's body).

The corrigendum block records:

- **Date and authorship** — corrigendum dated 2026-04-25, authored under Task 11.P.MR-β.1 sub-task 4 dispatch.
- **Scope of correction** — Finding 3's token attribution was inverted: the address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` is **Mento-native COPM**, not "Mento-native cCOP." The user corrected this attribution mid-Rev-5.3.3 plan revision: *"is COPM not cCOP."* Pre-existing project memory `project_mento_canonical_naming_2026` was correct all along.
- **Authoritative override** — the canonical address-registry spec doc produced under sub-task 3 (`contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md`) is the authoritative reference for token-address identity going forward. Finding 3's body is preserved in the audit trail but is OVERRIDDEN by the registry.
- **Other findings unaffected** — Findings 1 (MiniPay = swap rail, USDt-dominated, ≈0 macro-hedge signal at aggregate), 2 (Carbon DeFi MM ≈ 52% of cCOP-labeled-but-actually-COPM Transfer events with NA-hours diurnal signature), and 4 (audit-trail disclosure of three prompt-injection attempts) remain useful research evidence and are NOT overridden by this corrigendum.
- **Future-research safeguard** — third-party Celo-forum / similar external sources can disagree on token identity; future research that cites such sources MUST cross-check against the address registry.

**Acceptance.** Corrigendum block lands in the TR research file at the agreed placement (prefix or appended). The block is clearly labeled as a corrigendum (not silently rewritten into the Finding 3 body). The TR's original Finding 3 text is NOT deleted or overwritten — the audit-trail-evidence value of the original-attribution-then-correction sequence is preserved. The corrigendum cross-references the registry spec doc by path.

**Subagent.** Data Engineer.

**Reviewers.** None at sub-task level (this is editorial-only, fully scope-bounded; the registry spec doc carries the trio review and the corrigendum is consistent with that doc).

**Dependency.** Sub-task 3 complete (the registry doc path must exist before the corrigendum can cross-reference it).

### Sub-task 5 — Future-research safeguard memo

**Deliverable.** A short safeguard note documenting the rule that third-party Celo-forum / similar external sources can disagree on token identity, and that future research that cites such sources MUST cross-check against the canonical address registry from sub-task 3. Lands at `contracts/.scratch/2026-04-25-future-research-token-identity-safeguard.md`.

The memo records:

- **Episode summary** — the Rev-5.3.3 / Rev-5.3.4 cCOP-vs-COPM attribution flip + correction sequence.
- **Lesson** — third-party sources are not authoritative for on-chain identity; on-chain inspection + project-memory cross-checks against `project_mento_canonical_naming_2026` are the authoritative path.
- **Process rule** — future Trend Researcher / Reality Checker / any subagent dispatch that encounters token-identity attribution from third-party sources MUST cross-check against the address registry spec doc before propagating the attribution into specs, plans, code, or memory. Failure to cross-check is an anti-fishing-banned shortcut and surfaces as a process violation.
- **Reference** — the canonical address-registry spec doc path; the TR research file (with corrigendum); the load-bearing memory anchors.

**Acceptance.** Memo lands at the cited path; is short (**≤ 100 lines** of markdown body, falsifiable line-count criterion per TW A4 advisory; replaces the prior non-falsifiable "≤ 2 pages" target); is referenceable from future research dispatches; is consistent with the registry spec doc and the corrigendum.

**Subagent.** Technical Writer (this is editorial / process-discipline content; TW is the appropriate author per the agent role's process-documentation competence).

**Reviewers.** None at sub-task level (editorial-only, fully scope-bounded).

**Dependency.** Sub-tasks 3 and 4 complete.

---

## D. Acceptance criteria for the sub-plan as a whole

The sub-plan is complete when ALL of the following hold:

1. **Sub-task 1** — on-chain address inventory memo lands at `contracts/.scratch/2026-04-25-mento-native-address-inventory.md`; all six Mento-native tokens enumerated with provenance.
2. **Sub-task 2** — DuckDB table-to-address audit memo lands at `contracts/.scratch/2026-04-25-duckdb-address-audit.md`; `onchain_copm_transfers` + 10 `proxy_kind` values enumerated with address-level provenance.
3. **Sub-task 3** — canonical address-registry spec doc lands at `contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md`; passes 3-way review (CR + RC + SD); is the post-converge byte-exact-immutable source-of-truth.
4. **Sub-task 4** — corrigendum block lands in `contracts/.scratch/2026-04-25-mento-userbase-research.md` at the agreed placement; original Finding 3 text preserved; cross-references the registry doc.
5. **Sub-task 5** — future-research safeguard memo lands at `contracts/.scratch/2026-04-25-future-research-token-identity-safeguard.md`.
6. **Invariants preserved** — no DuckDB row mutated; no schema migration; no table rename; no project-memory file silently rewritten; Rev-5.3.2 published estimates byte-exact; `decision_hash` and `MDES_FORMULATION_HASH` unchanged.
7. **Rev-5.3.4 RESCOPE honored** — no sub-task output reverts to the Rev-5.3.3 framing of "correct the project-memory naming error"; the registry-lock framing is the authoritative deliverable.
8. **Downstream β-spec unblocking** — Task 11.P.spec-β can now author a Mento-native-only retail-only hypothesis citing the registry spec doc as the on-chain-identity authority. The β-spec dependency on Task 11.P.MR-β.1 is satisfied.

---

## E. Reviewers (post-author, sub-plan-level)

**Two distinct trios apply at different stages** (per CR Advisory A; lead with bottom line so first-time readers do not conflate them):

- **Sub-plan-level trio (TW-flavored)** — reviews the sub-plan structure, not the eventual registry doc.
- **Sub-task-3-level trio (SD-flavored)** — reviews the registry spec doc's technical correctness when sub-task 3's deliverable lands.

**Sub-plan-level trio.** Per `feedback_three_way_review`, this sub-plan is reviewed by:

- **Code Reviewer** — invariant adherence, scope discipline, plan-vs-implementation boundary clarity.
- **Reality Checker** — verifies the sub-tasks are grounded in the major-plan Rev-5.3.4 RESCOPE; verifies the load-bearing memory anchors exist and are correctly cited; verifies the TR research file path and content.
- **Technical Writer** — verifies code-agnostic discipline; verifies acceptance criteria are crisp and falsifiable; verifies the per-sub-task subagent / reviewer / dependency triples are complete.

The sub-plan-level trio convenes after this sub-plan lands; convergence is required before any sub-task is dispatched. If the trio diverges, a CORRECTIONS block is appended to this sub-plan (analogous to the major-plan Rev-5.3.x CORRECTIONS pattern) before sub-task dispatch.

**Sub-task-3-level trio.** Per `feedback_implementation_review_agents`, sub-task 3's spec-doc deliverable is reviewed by **CR + RC + Senior Developer** (NOT TW), because the registry doc is implementation-adjacent corrigendum work rather than spec-authoring of analytical content. The TW review at the sub-plan level (above) addresses the sub-plan structure; the SD review at sub-task 3 addresses the registry doc's technical correctness.

---

## F. Reference paths

- Major-plan anchor: `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` — Task 11.P.MR-β.1 super-task body (Rev-5.3.3 CORRECTIONS block) + Rev-5.3.4 CORRIGENDUM.
- TR research file (corrigendum target in sub-task 4): `contracts/.scratch/2026-04-25-mento-userbase-research.md`.
- Carbon-basket X_d design doc (cross-referenced from sub-task 2's `proxy_kind` enumeration): `contracts/docs/superpowers/specs/2026-04-24-carbon-basket-xd-design.md`.
- Project memory anchors load-bearing on this sub-plan:
  - `project_abrigo_mento_native_only` — Abrigo scope is Mento-native ONLY; COPM is the Mento-native Colombia token; corrigendum-internal already lands; no further edit needed.
  - `project_mento_canonical_naming_2026` — canonical post-rebrand tickers + addresses; correct as authored; no corrigendum needed.
  - `project_carbon_user_arb_partition_rule` — `trader = 0x8c05ea30…` partition for Carbon DeFi MM-vs-user attribution; load-bearing for sub-task 2 `proxy_kind` `carbon_basket_arb_volume_usd` provenance.
  - `project_carbon_defi_attribution_celo` — context where the 2026 rebrand surfaced.
  - `project_usdt_celo_canonical_address` — companion address-canonicality precedent (USDT scam-impersonator HALT-VERIFY); precedent for the address-registry-as-authoritative discipline.
  - `feedback_three_way_review` — sub-plan-level review trio.
  - `feedback_implementation_review_agents` — sub-task-3-level review trio (CR + RC + SD).
  - `feedback_specialized_agents_per_task` — per-sub-task subagent dispatch.
  - `feedback_no_code_in_specs_or_plans` — code-agnostic body discipline.
  - `feedback_pathological_halt_anti_fishing_checkpoint` — HALT-on-discrepancy invariant for sub-tasks 1 and 2.
- Rev-5.3.2 published baseline (immutable through this sub-plan): commit `799cbc280`.
- 4-reviewer gate close-out commits (precedent format): `6b1200dcb` + `f38f1aad3`.
- Sibling sub-plan forward-pointers (NOT dependencies of this sub-plan; co-Rev-5.3.3 super-tasks):
  - `contracts/docs/superpowers/sub-plans/2026-04-25-rev2-notebook-migration.md` (Task 11.O.NB-α; **definitely-on-disk**, verify pre-dispatch per CR Advisory C)
  - `contracts/docs/superpowers/sub-plans/2026-04-25-rev3-zeta-group.md` (Task 11.O.ζ-α; **definitely-on-disk**, verify pre-dispatch per CR Advisory C)
  - `contracts/docs/superpowers/sub-plans/2026-04-25-beta-spec.md` (Task 11.P.spec-β; BLOCKED on this sub-plan's completion; not-yet-on-disk is acceptable per sub-plan-discipline pattern)
  - `contracts/docs/superpowers/sub-plans/2026-04-25-beta-execution.md` (Task 11.P.exec-β; BLOCKED on Task 11.P.spec-β convergence; not-yet-on-disk is acceptable)
- **Pre-dispatch hygiene check (CR Advisory C).** Before dispatching this sub-plan's first sub-task, the orchestrator MUST verify the two definitely-exist sibling sub-plans (`…-rev2-notebook-migration.md` and `…-rev3-zeta-group.md`) are on disk. A stale sibling-citation discovered post-dispatch is an editorial papercut, not a scope failure, but the pre-dispatch check is cheap and avoids the surprise.

---

## G. Out-of-scope reaffirmation

This sub-plan does NOT:

- Modify `project_mento_canonical_naming_2026` (correct as authored).
- Modify `project_abrigo_mento_native_only` (already carries internal corrigendum).
- Modify the major plan, the carbon-basket X_d design doc, the Y₃ inequality-differential design doc, or any other Rev-5.3.x spec.
- Mutate any DuckDB row, column, or table.
- Author or modify any code, schema-migration script, or notebook.
- Author or modify any Solidity contract or test.
- Re-open the Rev-5.3.2 published estimates or the Rev-5.3.2 14-row resolution-matrix scope.
- Author the β spec, the β execution scaffolding, or any α-track artifact.
- Decide whether the β-spec hypothesis is H1 (FALSIFICATION-recognition) or H2 (partition-surgery); that decision is Task 11.P.spec-β's scope.

If a sub-task discovers a need to do any of the above, it HALTS to the user with an explicit pivot note per `feedback_pathological_halt_anti_fishing_checkpoint`.

### §G addendum under §I CORRECTIONS (Rev-5.3.5) — TW-7 reconciliation

The HALT-VERIFY β-resolution required append-only β-corrigenda to both `project_mento_canonical_naming_2026` and `project_abrigo_mento_native_only` (per §B-4 anti-fishing-on-memory-edits discipline). The §G first two bullets ("does NOT modify project_mento_canonical_naming_2026" / "does NOT modify project_abrigo_mento_native_only") are read under §I as **"does NOT silently modify; corrigenda are append-only and explicitly anchored to the Rev-5.3.5 CORRECTIONS block."** The Rev-5.3.2 published estimates remain byte-exact (no re-estimation; consume-only DuckDB invariants per §B-1); only their interpretation framing is rescoped under §I CORRECTIONS, which is consistent with the byte-exact-immutability invariant. The §G out-of-scope discipline is preserved structurally; §I is the authoritative venue where the disposition's append-only memory edits + interpretation reframing are formally documented. A reader scanning §G in isolation must read §I before concluding the corrigenda are out-of-scope — they are not; they are append-only-with-explicit-anchor and fall fully within the discipline §G enforces.

---

## H. CORRECTIONS block (post-author 3-way review, 2026-04-26)

The 3-way review trio convened post-author per §E. CR returned PASS-w-non-blocking-advisories (3 editorial advisories). TW peer returned PASS-w-non-blocking-advisories (6 minor advisories). Reality Checker returned **NEEDS-WORK** with three substantive but fixable findings (R-1, R-2, R-3) and two non-blocking advisories (R-4, R-5).

This CORRECTIONS block records the resolution trail. The corrections are editorial / coverage / contradiction-hygiene fix-ups; no Rev-5.3.x invariant is relaxed, no scope is expanded beyond the Rev-5.3.4 RESCOPE, and the rescoped registry-lock mandate is preserved.

### RC NEEDS-WORK findings — resolutions

- **R-1 (DOMINANT) — DuckDB sub-task 2 coverage gap.** RC's live `SHOW TABLES … LIKE 'onchain_%'` probe returned **14 onchain_* tables**; sub-task 2 as authored audited 2 (≈14% coverage), under-serving the §B-3 invariant that the registry is source-of-truth for "every downstream β-track and α-track artifact." **Resolution.** Sub-task 2 expanded to enumerate **every** live `onchain_*` table tagged with exactly ONE of {DIRECT, DERIVATIVE, DEFERRED}; a pre-flight DuckDB enumeration query is now REQUIRED before audit-memo authoring; coverage completeness is verifiable via count(tagged tables) = count(query rows); divergence HALTS. All 14 tables now appear by name (or are surfaced by the pre-flight query) with an explicit coverage tag.
- **R-2 — `onchain_copm_ccop_daily_flow` table-name disposition.** The table name literally embeds the cCOP-vs-COPM ambiguity the rescoped Rev-5.3.4 deliverable exists to lock down; the sub-plan as authored carried no explicit acceptance line for it. **Resolution.** Sub-task 2 now classifies this table as DIRECT with explicit narrative treatment: verify which addresses the table actually filters on; document COPM vs. cCOP-historical-data scope; record a future-revision rename recommendation (no rename executed under this sub-plan per §B-2). Sub-task 3's deliverable now carries an **explicit per-table disambiguation entry** for this table — it MUST appear by name in the registry doc, not be aggregated into a generic note.
- **R-3 — Supply-field internal contradiction.** Sub-task 1 required "current supply at audit time"; §B-3 + sub-task 3 acceptance asserted byte-exact-immutability post-converge — these contradict. **Resolution.** Approach (a) selected for cleanest immutability: the supply field is **dropped from the registry per-token sections**. Auditors and downstream consumers needing current supply query live DuckDB / Celoscan / Dune at consumption time. The registry is a token-identity / address-provenance artifact, not a circulating-supply dashboard. Sub-task 1 line and sub-task 3 per-token-section bullet both reflect the deletion with an explicit rationale callout to RC R-3.

### RC non-blocking advisories — disposition

- **R-4 — Sub-tasks 1 and 2 carry no sub-task-level review.** Resolved at lightweight: sub-task 1 and sub-task 2 each now carry a **Reality-Checker spot-check (single-pass, advisory)** sub-task-level reviewer. Sub-task 1's spot-check verifies address text-match against `project_mento_canonical_naming_2026` and provenance citations; sub-task 2's spot-check verifies the pre-flight enumeration query was actually run and the coverage-completeness count matches. The convergent CR + RC + SD trio still anchors at sub-task 3's registry doc; the spot-checks add a cheap upstream backstop.
- **R-5 — Sub-task 2 didn't pin which file receives the `contract_address` annotation.** Resolved: sub-task 2 now explicitly names the **canonical address registry document** (sub-task 3 deliverable) at `contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md` as the **authoritative annotation target**. Per-table table-comment annotations, loader-docstring edits, and `econ_schema.py` schema comments are explicitly OUT OF SCOPE for this sub-plan. Single-file annotation locus avoids the multi-file drift risk RC flagged.

### CR non-blocking advisories — disposition

- **CR Advisory A — Tighten §E dual-trio language.** Resolved: §E now leads with the bottom line ("Two distinct trios apply at different stages") and explicitly labels the two trios (sub-plan-level TW-flavored vs. sub-task-3-level SD-flavored).
- **CR Advisory B — Legacy-vs-canonical slug clarifier at sub-plan line 90.** Resolved: sub-task 2's `proxy_kind` enumeration block now carries an explicit clarifier that the lowercase canonical slugs match live DuckDB keys per RC's `SELECT DISTINCT proxy_kind` probe, with explicit reference to legacy-ticker handling per `project_mento_canonical_naming_2026`.
- **CR Advisory C — Pre-dispatch hygiene for sibling sub-plans.** Resolved: §F now flags the two definitely-exist sibling sub-plans for pre-dispatch on-disk verification; the not-yet-on-disk β-spec / β-execution forward-pointers are acceptable per the sub-plan-discipline pattern.

### TW peer advisories — disposition

- **TW A1 — Major-plan anchor citation tighter.** Resolved: §A header now cites Rev-5.3.3 CORRECTIONS at line ~2233 and Rev-5.3.4 CORRIGENDUM at line ~2370+ / ~2383, with an explicit caveat that line numbers are review-time-verified and may drift; canonical anchor is the named CORRIGENDUM block.
- **TW A4 — Sub-task 5 falsifiable length criterion.** Resolved: "≤ 2 pages" replaced with "≤ 100 lines of markdown body" (falsifiable via `wc -l`).
- **TW A2, A3, A5, A6 — DECLINED (with reason).**
  - **A2** (sub-task 3 TW optionality at line 117) — DECLINED: the optional-TW-pre-pass for the registry doc draft is appropriately delegated to orchestrator field-judgment; introducing a numeric threshold ("if doc exceeds N pages") would be over-engineering at sub-plan-authoring time.
  - **A3** (the "TW's 5 pre-flight findings" phrase ambiguity in the user's review prompt) — DECLINED: this advisory concerned the dispatch-envelope upstream of the sub-plan body, not the sub-plan itself; the sub-plan §B 7 invariants + §G 9 out-of-scope items already over-determine the anti-error scaffolding.
  - **A5** (Rev-5.3.2 14-row resolution-matrix anchor in §G.6) — DECLINED: Rev-5.3.2 is well-established context for the trio reviewers per the project's standing pattern; pinning a specific spec-doc path would create a premature anchor that the next Rev could break. The convention-resolution path (reviewer queries the major plan) is sufficient.
  - **A6** (byte-exact-immutability claim soften / qualify) — DECLINED: the immutability claim is load-bearing for the §B-3 invariant; softening it would weaken the registry's source-of-truth status. The R-3 resolution (drop the supply field) eliminates the only fragility that would have justified softening; with supply gone, the byte-exact-immutability claim is honest. Future typo corrections can land via the appendix-section pattern already documented at line 107.

### Resolution status

All three RC NEEDS-WORK findings (R-1, R-2, R-3) are resolved. Two RC advisories (R-4, R-5) are resolved at lightweight. Three CR advisories (A, B, C) are resolved. Two TW advisories (A1, A4) are resolved; four TW advisories (A2, A3, A5, A6) are DECLINED with documented reason. The sub-plan is ready for **RC-only single-pass re-review** per the post-fix-up plan; CR's PASS-w-adv and TW peer's PASS-w-adv stand.

---

## I. CORRECTIONS — Rev-5.3.5 β-resolution (2026-04-26, post-HALT-VERIFY)

**Trigger.** MR-β.1 sub-task 1's first dispatched DE deliverable (`contracts/.scratch/2026-04-25-mento-native-address-inventory.md` at commit `3611b0716`) fired a HALT-VERIFY GATE on the canonical Mento-native Colombian-peso address. RC spot-check at commit `3286dfe66` returned **PASS** with non-binding β-advisory; foreground orchestrator ran a Dune empirical probe (query `7378788`) confirming β-track Rev-3 data feasibility. **User picked path β.** Authoritative disposition memo: `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md`. Major-plan anchor: Rev-5.3.5 CORRECTIONS block (`contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md`).

**Outcome.** `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` is the canonical Mento V2 `StableTokenCOP` (Mento-native COPm). `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` is Minteo-fintech (Mento-native scope OUT). Project memory `project_mento_canonical_naming_2026` and `project_abrigo_mento_native_only` both carry β-corrigendum blocks at top.

### Sub-task rescopes under β

**Sub-task 1 (re-dispatch under rescoped framing).** The DE's existing inventory at commit `3611b0716` is preserved as a research artifact and consumed (NOT overwritten) by the rescoped re-dispatch. The rescoped deliverable enumerates **both** addresses with explicit scope tags:

- `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` — **IN scope**, canonical Mento-native COPm; provenance: Mento V3 deployments docs (`StableTokenCOP`), Dune project `celocolombianpeso` decoded as `StableTokenV2`, Celo Token List entry "Mento Colombian Peso" (chainId 42220), 285,390 transfer events 2024-10-31 → 2026-04-26 (live), `evt_exchangeupdated` + `evt_validatorsupdated` events present (Mento-protocol-specific governance; dispositive of Mento-protocol-native status).
- `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` — **OUT of Mento-native scope**, Minteo-fintech COPM-Minteo (audit-trail preservation only); provenance: Celo Token List entry "COP Minteo" (chainId 42220), 110,253 transfer events 2024-09-17 → 2026-04-25 ingested in `onchain_copm_transfers`. Was the Rev-2 X_d source; Rev-2 closes scope-mismatch.

The other five Mento-native tokens (USDm/EURm/BRLm/KESm/XOFm) are unchanged — their addresses remain authoritative as in `project_mento_canonical_naming_2026`. Sub-task 1's rescoped acceptance: enumeration of all six in-scope Mento-native tokens + the one out-of-scope Minteo entry; provenance citations preserved; HALT-VERIFY discrepancies surfaced (none expected post-disposition; if any, HALT to user).

**Sub-task 2 (rescope under DEFERRED-via-scope-mismatch tag).** The DIRECT/DERIVATIVE/DEFERRED coverage scheme is preserved. Every `onchain_*` table sourced from `0xc92e8fc2…` events — `onchain_copm_transfers`, `onchain_copm_daily_transfers`, `onchain_copm_burns`, `onchain_copm_mints`, `onchain_copm_freeze_thaw`, `onchain_copm_time_patterns`, `onchain_copm_address_activity_top400`, `onchain_copm_transfers_top100_edges`, `onchain_copm_transfers_sample`, `onchain_copm_ccop_daily_flow` — is now tagged **DEFERRED-via-scope-mismatch**. The `proxy_kind` value `carbon_per_currency_copm_volume_usd` in `onchain_xd_weekly` is also DEFERRED-via-scope-mismatch.

The `onchain_carbon_*` tables (`onchain_carbon_arbitrages`, `onchain_carbon_tokenstraded`) remain DIRECT in scope; their coverage of Mento-basket internal flows uses the `0xc92e8fc2…` address as one of the basket-counter-sides under the (now-corrected) prior assumption. The audit memo records this as a follow-up question: do the carbon basket queries need to swap `0xc92e8fc2…` → `0x8A567e2a…` for Mento-basket trading attribution? **Out of scope for sub-task 2 acceptance**; in scope for Task 11.P.spec-β identification design (β-spec must decide whether COPm trading on Carbon — if any — feeds the X_d signal).

The pre-flight enumeration query (`SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'onchain_%' ORDER BY 1`) is still REQUIRED. Coverage completeness verification (count of tagged = count of returned) is unchanged. No table is dropped, renamed, or migrated; the rescope is annotation-only.

**Sub-task 3 (registry doc rescope).** The canonical address-registry spec doc (`contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md`) scopes only Mento-native tokens in the per-token body sections: COPm at `0x8A567e2a…`, USDm, EURm, BRLm, KESm, XOFm. The body sections do NOT enumerate `0xc92e8fc2…`.

A new explicit appendix section **"Out-of-scope third-party tokens (audit-trail preservation)"** is added, containing one entry: COPM-Minteo at `0xc92e8fc2…`, with provenance citations + cross-reference to the DEFERRED-via-scope-mismatch tag in sub-task 2 + cross-reference to the Rev-5.3.5 CORRECTIONS block in the major plan. The appendix is preservation-only; it is NOT a registry of in-scope tokens.

The DuckDB cross-reference table within the registry doc enumerates DIRECT and DERIVATIVE tables tracking Mento-native addresses (i.e., `onchain_carbon_*` if scoped to `0x8A567e2a…`-side flows under future ingestion; nothing in current DuckDB tracks `0x8A567e2a…` yet — "0 events ingested" remains true at Rev-5.3.5 disposition time). The DEFERRED section enumerates all `0xc92e8fc2…`-derived tables with the scope-mismatch reason.

The `onchain_copm_ccop_daily_flow` explicit disambiguation entry per RC R-2 is **strengthened** under β: the table tracks Minteo-COPM daily flow (it's all out-of-scope under β); the `_ccop_` slug fragment is a pre-rebrand legacy artifact meaningless under the post-rebrand corrected naming; future-revision rename recommendation = drop the `_ccop_` fragment and re-slug as `onchain_copm_minteo_daily_flow` (NOT executed under this sub-plan; recorded for future rev).

**Sub-task 4 (TR corrigendum strengthened).** The TR research file (`contracts/.scratch/2026-04-25-mento-userbase-research.md`) corrigendum block is sharpened with both inversion layers documented:

1. **Layer 1 — Rev-5.3.3 cCOP-vs-COPM inversion** (TR's Finding 3 "cCOP = Mento-native, COPM = Minteo" attribution). Corrected by user 2026-04-25: "is COPM not cCOP."
2. **Layer 2 — Rev-5.3.4 address-level inversion** (after correcting Layer 1, the rescoped framing claimed `0xc92e8fc2…` is the Mento-native COPM address). Corrected by user + empirical Dune evidence 2026-04-26: `0x8A567e2a…` is the Mento-native COPm address; `0xc92e8fc2…` is Minteo-fintech.

The corrigendum block cross-references the Rev-5.3.5 CORRECTIONS block in the major plan and the disposition memo at `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` for empirical evidence. The TR's body content (Findings 1, 2, 4) is preserved unchanged; Finding 3 is fully overridden by the registry doc + corrigendum.

**Sub-task 5 (future-research safeguard memo strengthened).** The safeguard note now cites the **two-layer inversion precedent** as a worked example: third-party sources can disagree on token identity AT ANY GRAIN — both at the ticker / project-name level AND at the contract-address level. The mandatory triangulation procedure for any future research that touches Mento-native token identity:

1. Mento Labs official deployment docs (https://docs.mento.org/mento/protocol/deployments) for `StableTokenCOP` etc. — authoritative on contract addresses.
2. Dune decoded-table catalog (`searchTablesByContractAddress`) for project-name confirmation — authoritative on which contract is decoded as a Mento `StableTokenV2`.
3. Celo Token List (https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json) for community-attested token registry entries — useful disambiguation evidence but NOT authoritative when (1) and (2) disagree.
4. Cross-check against `project_mento_canonical_naming_2026` post-β-corrigendum.

Failure to triangulate before propagating a token-identity claim into specs / plans / code / memory is an anti-fishing-banned shortcut.

### Anti-fishing-invariant integrity preserved

- Consume-only DuckDB invariants preserved (no rows mutated, no schema migrations, no table renames).
- N_MIN = 75 unchanged; β-track Rev-3 must independently clear this on `0x8A567e2a…` data (78 weeks of activity already on-chain → likely cleared, to be verified at β-spec authoring time).
- POWER_MIN = 0.80 unchanged; MDES_SD = 0.40 unchanged.
- MDES_FORMULATION_HASH = `4940360dcd2987…cefa` unchanged.
- decision_hash = `6a5f9d1b05c1…443c` unchanged (Rev-2 published estimates byte-exact preserved).
- Address registry post-converge byte-exact-immutability invariant preserved (the registry doc, once it lands at sub-task 3 acceptance, is byte-exact-immutable; future address additions land as new appendix sections).

### Reviewer cycle for this CORRECTIONS block

Per `feedback_pathological_halt_anti_fishing_checkpoint` + `feedback_three_way_review`: post-hoc 3-way review (CR + RC + TW) on the disposition. The review scope is THIS CORRECTIONS block + the major-plan Rev-5.3.5 CORRECTIONS block + the disposition memo + the project-memory β-corrigenda. The review trio convenes immediately post-commit; convergence is required before MR-β.1 sub-task 1 re-dispatch under the rescoped framing.
