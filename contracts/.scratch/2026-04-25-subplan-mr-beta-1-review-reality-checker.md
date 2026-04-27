# Reality-Checker Adversarial Review — Sub-plan MR-β.1 (cCOP-vs-COPM provenance audit)

**Subject.** `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` (TW agent `adf6407b053051a5c`, uncommitted at review time).

**Reviewer.** TestingRealityChecker (RC, adversarial / fantasy-immune posture).

**Default verdict.** NEEDS-WORK unless overwhelming evidence supports promotion.

**Live-state probe budget.** ≤ 15 tool uses. Used: 7 (Read sub-plan, ls scratch, ls specs, ls memory, grep major-plan, DuckDB probe, Bash venv probe). Within budget.

---

## 1 — Verification matrix

| # | Claim under review | Live evidence | Verdict |
|---|---|---|---|
| 1 | `onchain_xd_weekly` proxy_kind ticker convention | Live `SELECT DISTINCT proxy_kind` returns lowercase canonical: `b2b_to_b2c_net_flow_usd`, `carbon_basket_arb_volume_usd`, `carbon_basket_user_volume_usd`, `carbon_per_currency_brlm_volume_usd`, `carbon_per_currency_copm_volume_usd`, `carbon_per_currency_eurm_volume_usd`, `carbon_per_currency_kesm_volume_usd`, `carbon_per_currency_usdm_volume_usd`, `carbon_per_currency_xofm_volume_usd`, `net_primary_issuance_usd`. The user-prompt convention `(copm|usdm|eurm|brlm|kesm|xofm)` matches reality; the design-doc capitalized convention does NOT. Sub-plan §C sub-task 2 lines 82-90 enumerate the LIVE lowercase slugs verbatim. | PASS |
| 2 | Sub-task 2 enumerates correct DuckDB onchain table inventory | Live `SHOW TABLES … LIKE 'onchain_%'` returns 14 tables: `onchain_carbon_arbitrages`, `onchain_carbon_tokenstraded`, `onchain_copm_address_activity_top400`, `onchain_copm_burns`, `onchain_copm_ccop_daily_flow`, `onchain_copm_daily_transfers`, `onchain_copm_freeze_thaw`, `onchain_copm_mints`, `onchain_copm_time_patterns`, `onchain_copm_transfers`, `onchain_copm_transfers_sample`, `onchain_copm_transfers_top100_edges`, `onchain_xd_weekly`, `onchain_y3_weekly`. Sub-task 2 audits ONLY `onchain_copm_transfers` + 10 `proxy_kind` rows of `onchain_xd_weekly` — i.e. it covers 2 of 14 onchain tables (≈14%). | **NEEDS-WORK** (see §2 finding R-1) |
| 3 | `onchain_copm_transfers` schema acknowledges absence of `contract_address` column | Live `DESCRIBE` returns 9 columns: `(evt_block_date, evt_block_time, evt_tx_hash, from_address, to_address, value_wei, evt_block_number, log_index, _ingested_at)`. No `contract_address` column. Sub-plan sub-task 2 line 79 instructs: "Document the address as a schema-level annotation in the loader-helper docstring or schema-doc comment, NOT as a column rename or table rename." Workable doc-level path. | PASS |
| 4 | TR research file at `contracts/.scratch/2026-04-25-mento-userbase-research.md` exists | `ls -la` shows 31,812 bytes, mtime 2026-04-26 15:16. | PASS |
| 5 | Five sub-task deliverable paths do not collide with existing files | Live `ls contracts/.scratch/` and `ls contracts/docs/superpowers/specs/` confirm: NO existing files at `2026-04-25-mento-native-address-inventory.md`, `2026-04-25-duckdb-address-audit.md`, `2026-04-25-mento-native-address-registry.md`, `2026-04-25-future-research-token-identity-safeguard.md`. (The TR research file at `2026-04-25-mento-userbase-research.md` is the corrigendum target, not a fresh deliverable, so co-location is by design.) | PASS |
| 6 | Project memory file paths resolve to real files | Live `ls ~/.claude/projects/.../memory/` confirms all six anchors cited in §F: `feedback_implementation_review_agents.md`, `feedback_no_code_in_specs_or_plans.md`, `feedback_pathological_halt_anti_fishing_checkpoint.md`, `feedback_specialized_agents_per_task.md`, `feedback_three_way_review.md`, `project_abrigo_mento_native_only.md`, `project_carbon_defi_attribution_celo.md`, `project_carbon_user_arb_partition_rule.md`, `project_mento_canonical_naming_2026.md`, `project_usdt_celo_canonical_address.md`. All 10 referenced anchors present. | PASS |
| 7 | Anti-fishing trail intact — no Rev-5.3.x invariant relaxed | §B pre-commitment 1: `decision_hash = 6a5f9d1b05c18defd8b30c4b3cef6af896d6e45a2a26c1c60aa342da0a5a443c` matches live `nb1_panel_fingerprint.json:23` per major-plan grep. `MDES_FORMULATION_HASH = 4940360dcd298738a1f7321c1573bc3aad01b8a4c5acbc546d0855276389cefa` matches `project_mdes_formulation_pin` source-pin. §B-1 explicitly states "No DuckDB row mutated; Rev-5.3.2 published estimates byte-exact." §B-4 forbids silent memory rewrites. §B-7 preserves TR Finding 3 audit-trail. §G out-of-scope reaffirmation lists every shared artifact (carbon-basket X_d design doc, Y₃ design doc, Rev-5.3.2 published estimates, β spec, β execution, α-track) as DO-NOT-MODIFY. | PASS |
| 8 | Rev-5.3.4 CORRIGENDUM anchor exists in major plan | Live grep on major plan shows Rev-5.3.4 CORRIGENDUM block at line 2370+; rescope text at line 2383: "the audit's deliverable changes from 'correct the project memory naming error' (no longer needed) to 'formally lock the on-chain address registry'". Sub-plan §A line 21 quotes this verbatim. | PASS |

---

## 2 — Adversarial findings

### R-1 — DuckDB inventory under-coverage (NEEDS-WORK trigger)

Sub-task 2 audits 2 of 14 live `onchain_*` tables (`onchain_copm_transfers` + `onchain_xd_weekly`'s 10 `proxy_kind` rows). It OMITS the following 12 tables — several of which are directly load-bearing on the rescoped cCOP-vs-COPM provenance question:

- `onchain_copm_ccop_daily_flow` — name literally pairs `copm` and `ccop`. If the rescoped Rev-5.3.4 deliverable is "formally lock the on-chain address registry … with a single canonical reference document," a table whose own name embeds the inverted-attribution ambiguity is a primary audit target. Currently invisible to sub-task 2.
- `onchain_copm_daily_transfers`, `onchain_copm_burns`, `onchain_copm_mints`, `onchain_copm_freeze_thaw`, `onchain_copm_time_patterns`, `onchain_copm_address_activity_top400`, `onchain_copm_transfers_top100_edges`, `onchain_copm_transfers_sample` — all carry the `copm_*` naming convention. Each is a candidate for "is this address-attributed correctly?" audit. Currently invisible to sub-task 2.
- `onchain_carbon_arbitrages`, `onchain_carbon_tokenstraded` — Carbon DeFi raw event tables; address-attribution questions (`trader = 0x8c05ea30…` per `project_carbon_user_arb_partition_rule`) live here, not in the aggregated `onchain_xd_weekly` proxies. The registry's value is precisely cross-checking source-data tables, not just the aggregates.
- `onchain_y3_weekly` — Y₃ inequality-differential panel; the §B-3 invariant says the registry is the source-of-truth for "every downstream β-track and α-track artifact," yet the Y₃ panel is excluded from the audit.

This is not a code-agnosticism gap; it's a scope-completeness gap. The sub-plan claims the registry is "the on-chain-address source-of-truth for every downstream β-track and α-track artifact" (§B-3), but the audit feeding that registry only inspects 14% of the live onchain tables. **The acceptance criteria as authored will pass on incomplete evidence.**

**Recommended fix.** Sub-task 2 deliverable expanded to enumerate all 14 live `onchain_*` tables (or explicit allow-list rationale for any excluded). For each excluded table, the audit memo cites the rationale (e.g., "table is a derivative of `onchain_copm_transfers` and inherits its address attribution; no separate audit needed"). The audit memo's acceptance line should be amended to: "Memo enumerates all 14 live `onchain_*` tables; each is either (a) explicitly cross-referenced to a Mento-native address, or (b) explicitly flagged as a derivative whose address attribution is inherited from a parent table also enumerated, or (c) HALTed to the user as a discrepancy."

### R-2 — `onchain_copm_ccop_daily_flow` deserves explicit narrative treatment

The table name `onchain_copm_ccop_daily_flow` literally embeds the cCOP-vs-COPM ambiguity that the rescoped sub-plan exists to lock down. A reader of the future address registry encountering this table will face the exact attribution confusion that the registry is meant to prevent.

The corrigendum corpus (sub-task 4 + sub-task 5) covers the TR research file's Finding 3 narrative and a future-research process rule, but does NOT carry an explicit "what to do about this table name" disposition. Per §B-2 ("no table renames"), the table cannot be renamed; per §B-4, naming clarifications must be documented at the schema-doc / loader-docstring level.

**Recommended fix.** Either (a) sub-task 2 audit memo explicitly resolves what `onchain_copm_ccop_daily_flow` tracks (COPM transfers paired with what?) and the address registry sub-task 3 carries a per-table disposition note, or (b) the sub-plan adds an explicit acceptance line that the registry doc enumerates this table by name with a doc-level disambiguation note ("the `_ccop_` slug is a pre-rebrand legacy artifact; the underlying source is Mento-native COPM at `0xc92e8fc2…`; the table content is correct; the slug is preserved for migration-stability reasons per `project_mento_canonical_naming_2026`"). Without this, the registry leaves the most pointed naming-confusion artifact in the project unaddressed.

### R-3 — Total-supply field at "audit time" creates a fragility risk

Sub-task 1 line 62 requires "Total supply (current) — current circulating supply at the audit time, with the audit timestamp and the data source." This field varies across audit runs by construction. The registry doc (sub-task 3 line 109) consumes it. §B-3 + §B-acceptance-doc-immutability assert the registry is "byte-exact-immutable post-converge."

If the registry is byte-exact-immutable but contains a timestamped "current supply" field, the field stales by definition the moment the audit lands. Future readers will see a stale supply with no flag. This is a small but real anti-fishing-adjacent risk: the registry documents an "audited" value that no longer reflects on-chain reality.

**Recommended fix.** Either (a) drop the "current supply" requirement from the registry's per-token sections (keep it only in sub-task 1's audit memo, which is dated and not claimed to be immutable), or (b) explicitly carve out the supply field as the ONE non-immutable cell in each section, with a documented refresh policy ("supply field is appendix-refreshable on a quarterly cadence; address + provenance + Mento Reserve relationship are byte-exact-immutable"). Either fix preserves the §B-3 invariant honestly.

### R-4 — Sub-task 1 has no sub-task-level reviewer; flows directly into sub-task 3 trio

Sub-task 1 line 69: "Reviewers. None at sub-task level (sub-task 1 is an intermediate research artifact consumed by sub-task 3, which carries the trio review)." Same for sub-task 2 line 97.

Per `feedback_specialized_agents_per_task` ("every plan task dispatches a specialized subagent; foreground orchestrates and verifies, never authors") and `feedback_implementation_review_agents`, the project's standing pattern is per-task review. Sub-tasks 1 + 2 produce the load-bearing audit evidence that sub-task 3 consumes; the sub-task-3 trio inherits the responsibility of catching errors in the upstream evidence. This is workable BUT concentrates review burden at sub-task 3.

This is not a verdict-changing issue (the sub-plan states the structural choice explicitly, doesn't hide it, and the §B-4 + §B-acceptance-of-sub-task-1-line-65 HALT-on-discrepancy invariant gives sub-task 1's dispatched subagent a backstop). Flagged as ADVISORY only.

### R-5 — "Workable" doesn't mean "complete" for the contract_address absence

The schema-doc-level path proposed by sub-task 2 line 79 (annotate the loader docstring rather than rename the column) is workable per RC's check 3 above. However, sub-plan §C sub-task 2 doesn't specify which file the annotation lands in (`contracts/scripts/econ_schema.py` loader? a separate schema-doc memo? the registry spec doc itself?). Reviewers consuming this sub-plan will plausibly converge on different files.

**Recommended fix.** Sub-task 2 deliverable explicitly names the annotation target file (preference: the registry spec doc § per-token section AND the loader-helper docstring in `contracts/scripts/query_api.py` if such a function exists for `onchain_copm_transfers`; if not, a one-line schema-comment in `contracts/scripts/econ_schema.py` adjacent to the table DDL). Without this, the audit fix is ambiguous and reviewers may converge on docstring-only / schema-comment-only / registry-only and produce inconsistent provenance trails.

---

## 3 — Anti-fishing posture (clean)

§B pre-commitment items 1, 2, 4, 5, 6 are tight and load-bearing. The Rev-5.3.4 RESCOPE is correctly internalized (§B-6: "Wherever a Rev-5.3.3 phrase implies a project-memory naming error needs correction, treat that phrase as superseded"). The TR Finding 3 audit-trail is preserved (§B-7). No invariant from any prior Rev-5.3.x revision is relaxed; the `decision_hash` and `MDES_FORMULATION_HASH` are quoted byte-exact and match live state. The HALT-on-discrepancy gate (sub-task 1 acceptance line 65, sub-task 2 acceptance line 93) honors `feedback_pathological_halt_anti_fishing_checkpoint`.

The only anti-fishing-adjacent risk is R-3 (immutable registry containing a stale supply field) — flagged but not load-bearing on the verdict.

---

## 4 — Verdict

**NEEDS-WORK.**

Three NEEDS-WORK-level findings (R-1, R-2, R-3) and two advisories (R-4, R-5). R-1 is the dominant trigger: the sub-plan's stated ambition (registry as source-of-truth for "every downstream β-track and α-track artifact," §B-3) is materially under-served by sub-task 2's 14% live-table coverage. R-2 leaves the project's most pointed naming-confusion artifact (`onchain_copm_ccop_daily_flow`) without explicit registry treatment. R-3 fingerprints an internal contradiction (immutable registry containing a by-construction-stale supply field).

These are fixable WITHOUT scope expansion: R-1 by amending sub-task 2's enumeration to all 14 tables (with derivative-inheritance flags where appropriate), R-2 by an explicit acceptance line in sub-task 3 covering the `_ccop_` table-name disposition, R-3 by either dropping the supply field from the registry sections or explicitly carving it out as appendix-refreshable. None of these fixes require Rev-5.3.x invariant relaxation.

The PASS items (verification rows 1, 3, 4, 5, 6, 7, 8 of §1) are strong: the live-state probes confirm the sub-plan's factual claims about ticker convention, schema absence-of-contract_address, file existence, path non-collision, memory anchor resolution, anti-fishing posture, and major-plan anchor. The NEEDS-WORK is on completeness and immutability hygiene, not on factual misrepresentation.

**Recommendation.** A CORRECTIONS-block fix-up to sub-plan §C sub-task 2 + §C sub-task 3 acceptance lines addressing R-1, R-2, R-3 (text-level, no scope change) clears NEEDS-WORK to PASS-w-adv. The CR + TW reviews can converge in parallel; if TW-reviewer flags additional editorial concerns, fold them into the same CORRECTIONS block before sub-task dispatch.

**No BLOCK warranted.** Anti-fishing trail intact, all factual claims verifiable against live state, no Rev-5.3.x invariant relaxed.

---

**Reality Checker.** Adversarial review complete. ≤ 15 tool uses honored (7 used). No code, sub-plan, or DuckDB modified.
