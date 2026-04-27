# RC Re-Review — MR-β.1 Sub-Task 3 Registry Fix-Up Bundle

**Reviewer:** Reality Checker (single-pass post-trio-fix-up convergence review)
**Commit reviewed:** `2a0dcf8fe` (fix-up bundle on top of trio-review commit `339a50480`)
**Doc reviewed:** `contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md`
**Date:** 2026-04-26
**Convention:** per `feedback_pathological_halt_anti_fishing_checkpoint` post-3-way-review fix-up convergence pass

---

## 1. Verdict

**PASS.**

All three fix-ups landed correctly with surgical precision. Diff is byte-bounded to exactly the agreed scope. No anti-fishing-invariant relaxation, no DuckDB row mutation, no address byte-changes, no proxy_kind enumeration changes, no scope-tag drift. RC's two prior NEEDS-WORK findings are fully resolved; CR's §7→§8 cross-reference drift is fully resolved; SD's two non-blocking advisories deferred per stated bundle scope.

**MR-β.1 sub-task 3 is hereby UNBLOCKED for sub-tasks 4 + 5 dispatch.**

---

## 2. Per-Fix-Up Findings

### Fix-Up 1 — CR §7→§8 cross-reference numbering drift

**Status:** LANDED CORRECTLY.

**Verification:** `grep -n "§7" /…/2026-04-25-mento-native-address-registry.md` returned exactly ONE line:

```
227:## §7 — Slug-vs-canonical-ticker mapping (annotation-only)
```

This is the section heading itself (the legitimate §7), unchanged. Zero stray §7 cross-references remain anywhere else in the document. The 16 mechanical §7→§8 substitutions in the diff hit:

- §0.1 line 21 (audit-trail appendix cite)
- §0.2 line 30 (byte-exact-immutability scope cite)
- §4 line 144 (DuckDB cross-reference linkage cite — narrative)
- §4 table rows 3, 4, 6, 7, 8, 9, 10, 11, 12 (9 of 14 table rows; "see §7" → "see §8")
- §4 table row 13 (`onchain_xd_weekly` mixed-scope row; "see §5 + §7" → "see §5 + §8")
- §5 row 5 cross-reference (`carbon_per_currency_copm_volume_usd` proxy_kind row; "cross-reference §7" → "cross-reference §8")
- §6.1 line 204 (paired-source `copm_*` half cross-reference; "cross-reference §7" → "cross-reference §8")
- §7 row 1 final column (`copm` slug audit-time live ingestion attribution; "per §7-appendix-entry-1" → "per §8-appendix-entry-1")

Total = 16 substitutions, matching CR's enumeration. The §8 section heading (out-of-scope appendix) was already correctly labeled §8 in the trio commit and is unchanged. No §7 ghost survives.

### Fix-Up 2 — RC §6.1 numerical regression on `ccop_unique_senders`

**Status:** LANDED CORRECTLY.

**Verification:** Read of registry §6.1 lines 200-205. Line 205 now reads:

> `ccop_*` half (`ccop_usdt_inflow_usd`, `ccop_usdt_outflow_usd`, `ccop_unique_senders`; **uniformly 92.5% non-null at 541/585 across all three columns**)

The prior trio-commit phrasing — "92.5% non-null at 541/585 USDT-pairing columns + **585/585 sender-count column**" — is GONE. The "585/585" claim for `ccop_unique_senders` no longer appears anywhere in §6.1.

Furthermore, line 205 carries an explicit audit-trail bracketed note at end-of-paragraph:

> [Corrected per RC sub-task 3 trio review 2026-04-26: prior version of this paragraph mis-stated `ccop_unique_senders` as 100% non-null; live re-probe confirms 541/585 = 92.5% uniform across all three `ccop_*` columns, byte-aligning with sub-task 2 audit §6.1 post-correction at commit `09bacc105`. Strengthens rather than weakens the paired-source conclusion; scope tag DEFERRED-via-scope-mismatch unaffected.]

Both required attribution elements present:
- Reviewer attribution: "RC sub-task 3 trio review 2026-04-26" — PRESENT.
- Byte-alignment cite to sub-task 2 audit commit: "byte-aligning with sub-task 2 audit §6.1 post-correction at commit `09bacc105`" — PRESENT.

The note also adds an interpretive nuance — "Strengthens rather than weakens the paired-source conclusion; scope tag DEFERRED-via-scope-mismatch unaffected" — which is the correct disposition: a uniform 92.5% non-null rate across all three `ccop_*` columns is in fact a stronger asymmetric-null-pattern signature for shared-source than the prior mixed-claim was. The §6.2 scope tag (DEFERRED-via-scope-mismatch) is correctly preserved unchanged. No anti-fishing-invariant migration risk.

Additionally, the inserted sentence "The uniform 92.5% non-null rate across all three `ccop_*` columns is the asymmetric-null-pattern signature confirming they share the same source sub-query" makes the paired-source-evidence chain more explicit, which is a non-substantive clarity improvement. Not a regression.

### Fix-Up 3 — RC §9 + §10.1 forward-pointer styling

**Status:** LANDED CORRECTLY.

**Verification:** Read of §9 line 285 + §10.1 line 297.

§9 line 285:
> A future-research safeguard memo at `contracts/.scratch/2026-04-25-future-research-token-identity-safeguard.md` (sub-task 5 deliverable; **to be authored under sub-task 5 dispatch** post-MR-β.1 sub-tasks 3 + 4 convergence) will carry the process-discipline detail

§10.1 line 297:
> Sub-task 5 deliverable (downstream): Future-research safeguard memo at `contracts/.scratch/2026-04-25-future-research-token-identity-safeguard.md` (memo to be authored under sub-task 5 dispatch post-MR-β.1 sub-tasks 3 + 4 convergence; will cross-reference this registry by path).

Both citations now match the established sub-task 4 forward-pointer pattern at line 296:
> Sub-task 4 deliverable (downstream): TR research file corrigendum at `…/2026-04-25-mento-userbase-research.md` (corrigendum to be authored under sub-task 4 dispatch; cross-references this registry by path).

The "to be authored under sub-task X dispatch" forward-pointer phrasing is now uniform across sub-tasks 4 + 5. The earlier-form citation (without forward-pointer styling) is GONE. Future-tense disposition is consistent ("will carry"; "will cross-reference"). No reader can mistake the sub-task 5 deliverable for an already-authored artifact.

---

## 3. Regression Checks

### Check 4 — Anti-fishing-invariant integrity

**Status:** VERIFIED.

`git diff 339a50480 2a0dcf8fe -- contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md` shows exactly:

- 16 §7→§8 cross-reference substitutions (Fix-Up 1)
- 1 §6.1 numerical fix on line 205 with embedded audit-trail bracket note (Fix-Up 2)
- 2 forward-pointer styling fixes on lines 285 + 297 (Fix-Up 3)

Total = 19 line-touch points across 3 fix-up categories, all in the agreed scope. Verified absent:

- No address byte-changes. Every Celo address — `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606` (COPM-Minteo), `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` (Mento-native COPm), `0xe8537a3d056DA446677B9E9d6c5dB704EaAb4787` (BRLm), `0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73` (EURm), `0x456a3D042C0DbD3db53D5489e98dFb038553B0d0` (KESm), `0x73F93dcc49cB8A239e2032663e9475dd5ef29A08` (XOFm), `0x66198711…` (CarbonController), `0x8c05ea30…` (BancorArbitrage) — appears identical pre/post.
- No proxy_kind enumeration changes. The 10-`proxy_kind` table (§5) preserves all rows: `carbon_basket_user_volume_usd`, `carbon_basket_arb_volume_usd`, `b2b_to_b2c_net_flow_usd`, `net_primary_issuance_usd`, `carbon_per_currency_copm_volume_usd`, `carbon_per_currency_brlm_volume_usd`, `carbon_per_currency_eurm_volume_usd`, `carbon_per_currency_kesm_volume_usd`, plus the 2 remaining unaltered. Only the §7→§8 cross-reference at row 5 differs.
- No DuckDB cross-reference table-count changes. §4 table preserves all 14 rows; only the "see §7"→"see §8" cross-references on 9 of 14 rows differ.
- No anti-fishing-invariant relaxation. Per project memory: `N_MIN = 75`, `POWER_MIN = 0.80`, `MDES_SD = 0.40`, `MDES_FORMULATION_HASH = 4940360d…cefa`, Rev-4 `decision_hash`, Rev-2 14-row resolution matrix — none of these constants or hashes appear in the registry doc body, and the diff touches none of them indirectly. The byte-exact-immutability invariant articulated at §0.2 is itself preserved (the §0.2 line 30 substitution is `§7`→`§8` mechanical, not a relaxation of the invariant text).
- No §6.2 scope tag drift. The DEFERRED-via-scope-mismatch tag for `onchain_copm_ccop_daily_flow` is unchanged. The added clarifier in §6.1 line 205 explicitly preserves the disposition ("scope tag DEFERRED-via-scope-mismatch unaffected").
- No §11 / appendix structural changes (the "OUT of scope" appendix is at §8; §11 doesn't exist in this registry; only mechanical pointer redirection from §7 to §8).

The diff is a textbook surgical fix-up bundle — exactly the 3 mechanical edits + the 1 attribution-bracketed audit-note, nothing more.

### Check 5 — No DuckDB row mutation in commit

**Status:** VERIFIED.

`git diff --name-only 339a50480 2a0dcf8fe` returns exactly:

```
contracts/.scratch/2026-04-26-subtask-mr-beta-1-3-registry-review-cr.md
contracts/.scratch/2026-04-26-subtask-mr-beta-1-3-registry-review-rc.md
contracts/.scratch/2026-04-26-subtask-mr-beta-1-3-registry-review-sd.md
contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md
```

The 4 changed files are: registry spec + 3 trio review files (CR + RC + SD). Verified absent:

- No `.duckdb` file changes (no `contracts/data/structural_econ.duckdb` in name-only output).
- No Python source changes (no `contracts/src/…py` paths).
- No spec doc changes other than the target registry.
- No sub-plan file changes (`contracts/docs/superpowers/sub-plans/…` absent).
- No project-memory changes (`/home/jmsbpp/.claude/projects/…/memory/…` absent).
- No scratch artifact changes other than the 3 review files (the `2026-04-25-duckdb-address-audit.md` referenced in the audit-trail bracket note is NOT modified — its commit `09bacc105` predates this fix-up bundle).

Per `project_concurrent_agent_filesystem_interleaving`: no interleaving risk surfaces — the changeset is single-author (the fix-up dispatch agent), single-commit, and the 4 paths have no overlap with concurrent active worktree work. The DuckDB read-only constraint from sub-plan §H is preserved unbroken. The `09bacc105` cross-reference is a textual pointer, not a re-execution dependency.

---

## 4. New Findings

**None.**

The fix-up bundle is precisely scoped. The two SD non-blocking advisories (§6.3 hoist, §5 namespace explicitness) are correctly deferred per the bundle's stated scope; their deferral does not create new convergence risk for sub-tasks 4 + 5 because they are organizational / clarity issues with no semantic-correctness implication. RC has no additional findings to surface.

The audit-trail bracket note in §6.1 line 205 is itself a model of good post-3-way-review CORRECTIONS-block discipline per `feedback_pathological_halt_anti_fishing_checkpoint`: it carries (a) reviewer attribution, (b) date, (c) byte-aligned cross-reference to the upstream sub-task 2 audit fix commit, and (d) interpretive disposition note clarifying that the correction strengthens (not weakens) the paired-source conclusion. Future post-trio fix-ups should follow this exact template.

---

## 5. Disposition

**MR-β.1 sub-task 3 (registry spec) — CONVERGED.**

Three reviewers (CR, RC, SD) have now signed off:
- CR: NEEDS-WORK (§7→§8 drift) → resolved in `2a0dcf8fe` Fix-Up 1.
- RC (this re-review): NEEDS-WORK (§6.1 numerical + §9/§10.1 forward-pointer) → resolved in `2a0dcf8fe` Fix-Ups 2 + 3 → **PASS as of 2026-04-26**.
- SD: PASS-with-non-blocking-advisories → 2 advisories deferred per agreed bundle scope.

**Sub-tasks 4 + 5 are unblocked:**
- Sub-task 4: TR research file two-layer corrigendum (`contracts/.scratch/2026-04-25-mento-userbase-research.md`).
- Sub-task 5: Future-research safeguard memo (`contracts/.scratch/2026-04-25-future-research-token-identity-safeguard.md`).

Both downstream artifacts now have a stable, byte-exact-immutable registry to cross-reference per the §0.2 invariant.

---

**RC re-review file:** `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/.scratch/2026-04-26-subtask-mr-beta-1-3-registry-fixup-rc-rereview.md`
