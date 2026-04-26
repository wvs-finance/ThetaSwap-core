# NB1 Task 15 Review — Reality Checker (Adversarial)

**Verdict: CONDITIONAL PASS** — NB1 is substantively sound on data, construction, and handoff contract. But it ships to Task 15 review with three defects that are BLOCKERS against the anti-fishing claim as stated, and a fourth that is HIGH-severity against citation fidelity. None of them invalidates the underlying descriptive work; all of them are fixable before NB2 authoring begins and most are already flagged as "Task 15 cleanup" in the notebook itself.

---

## Top reviewer-killing findings

1. **BLOCKER — `sensitivity_preregistration_hash` is absent from `nb1_panel_fingerprint.json`.** The NB3 pre-registration document (`contracts/.scratch/2026-04-18-nb3-sensitivity-preregistration.md` §7 "Fingerprint Payload") explicitly requires Task 13 to hash the 8-line (A9, A12, S1-S6) payload into the handoff JSON under key `sensitivity_preregistration_hash`. The live fingerprint has keys `{daily_panel, decision_hash, decisions, generated_at, ledger_table, weekly_panel}` — no `sensitivity_preregistration_hash`. The anti-fishing seal this key is supposed to be is physically not on the artifact. Evidence: `notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json` (full file read). Expected sens hash (per the 8-line payload in pre-reg §7): `03ad01a23e710978ef4a6cae883b27902133730589a2542102c71dcd5d4604c7`. Severity: **BLOCKER** — the pre-registration's own tamper-evidence clause is not enforced. NB2 cannot legitimately claim Simonsohn 2020 compliance without it.

2. **BLOCKER — 9 of 12 `commit_sha` ledger rows are literal placeholder strings, not commit SHAs.** `nb1_panel_fingerprint.json.ledger_table` rows 4-12 carry values `cpi_surp_ar1`, `us_cpi_w12m`, `banrep_evt_sum`, `vix_weekly_avg`, `oil_lastpos_w`, `interv_dummy_any`, `collin_none_1p04`, `stat_levels`, `merge_listwise`. These are NOT short-SHA hashes — they're slug labels. Only rows 1 (`0d4fc1bec`), 2 (`ff1ac5bdd`), 3 (`9eb38ab46`) are real short-SHAs, and row 1's `0d4fc1bec` does not appear in `git log --all --oneline | grep 0d4fc1bec` (I didn't see a match, though I didn't verify exhaustively). The ledger is supposed to be the cross-audit record connecting Decisions to commits; 75% of it is disconnected from the git history. Evidence: `nb1_panel_fingerprint.json` rows 4-12 and corresponding source code at `01_data_eda.ipynb` cell 116 (`_LEDGER_ROWS[4:]`). Severity: **BLOCKER** — the "machine-verifiable handoff contract" claimed in cell 115's Reference block is not machine-verifiable on 9/12 rows.

3. **BLOCKER — `Anzoátegui-Zapata & Galvis 2019` citation has the wrong title and wrong subject in NB1 cell 73.** NB1 cell 73 (Decision #6 Reference) cites: "Anzoátegui-Zapata & Galvis (2019, *Cuadernos de Economía* 38(77), 'Efectos de los anuncios de política monetaria sobre el mercado accionario colombiano')". Web verification against the journal index shows that *Cuadernos de Economía* v38n77 (July 2019) published a paper titled "Efectos de la comunicación del banco central sobre los títulos públicos: evidencia empírica para Colombia" (DOI 10.15446/cuad.econ.v38n77.64706) — which is about **public debt securities, not the stock market**. The title NB1 uses ("mercado accionario colombiano") appears to match a different Anzoategui-Galvis paper in *Lecturas de Economía* (2017) by Galvis-de Moraes-Anzoátegui. NB1 has conflated two distinct papers under a single citation. Severity: **BLOCKER for citation fidelity** — a reviewer who looks the paper up will find it is not about rate-surprise event studies at all. The grounding this citation is supposed to provide for Decision #6 (event-study methodology) is weakened or entirely absent.

4. **HIGH — `Uribe-Gil & Galvis-Ciro 2022 BIS WP 1022` is unverified and likely does not exist at that venue.** NB1 cell 73 and cell 75 cite "Uribe-Gil & Galvis-Ciro 2022 BIS WP 1022" with title "Latin American monetary policy shocks and FX volatility". Web search against BIS Working Paper 1022 returned no matching author-title pair. The verifiable BIS-adjacent Uribe-authored Colombia piece is a BIS Papers chapter (José Darío Uribe, different author, different format). Until a DOI, BIS URL, or authoritative citation is produced, this is a citation of unclear provenance. Severity: **HIGH** — it is one of only two "Colombian literature canon" groundings Decision #6 invokes; if it turns out to be fabricated or misattributed, Decision #6's methodology justification leans entirely on ABDV 2003 Table 4 and Balduzzi 2001 (which ARE in the bib and real). The Decision would still stand on those, but the "Colombian canon precedent" claim would collapse.

5. **HIGH — Decision #6 was post-hoc rationalized: §4c Trio 1 was re-authored AFTER the data was populated.** Git log shows this sequence on 2026-04-18:
   - `813cd092e` 10:07 — §4c Trio 1 initial inspection (on then-zero-placeholder banrep_rate_surprise)
   - 10:21 — `2026-04-18-banrep-rate-surprise-methodology-research.md` scratch doc created
   - `b723648ed` 13:10 — meeting calendar scraper added
   - `3c148da8a` 13:10 — banrep_rate_surprise column populated
   - `1e076d9de` 13:25 — **§4c Trio 1 RE-AUTHORED** ("88 non-zero weeks" commit message) after seeing populated data
   - `11389a7b1` 13:46 — Decision #6 lock

   The re-author means the NB1 author SAW the populated event-study output (88 events, symmetric sign balance 42/46, corr(CPI)=+0.074) before writing the "why-used" justification that the methodology is "orthogonal to Colombian CPI" and produces "symmetric sign balance." Classical p-hacking under Simonsohn 2020: the data-informed justification was written after the data was observed, even though the methodology was pre-specified in the research note. The `anti_fishing_binding = True` claim in Decision #6's card is therefore misleading — the binding is to the methodology recommendation (genuinely pre-data) but the PROSE that justifies the lock was data-informed. Severity: **HIGH** for methodological integrity. Mitigation: the methodology research note timestamps show the CHOICE of event-study over AR(1) was pre-populated-data; only the in-NB1 justification prose was post-data. Decision #6's methodology is defensible; its pre-commitment narrative is not, as presently written.

---

## Attack vectors

### A. Anti-fishing integrity

**Finding A1 (Decision #6 post-hoc rationalization).** See top finding #5 above.

**Finding A2 (Decision #4 lock is pre-committed; honest-footnote audit trail holds).** The timing of 09:04 audit → 09:16 lock on 2026-04-18, combined with the spec Rev 4 pre-commitment of `cpi_surprise_ar1` as primary, means Decision #4's primary choice is genuinely anti-fishing bound. The audit ruled out three candidate bugs (alignment, imputation, warm-up) BEFORE accepting the asymmetry as a regime-anchoring design property. This is honest. The A9 sensitivity was data-motivated (the 94% asymmetry finding in Trio 1 is what made A9 more than a theoretical possibility), but A9 was already "anticipated in spec Rev 4 §8" per the pre-registration doc §3 A9 entry. Acceptable under Simonsohn 2020 provided the pre-registration is truly frozen before NB2 runs.

**Finding A3 (S7 is informally registered; formally absent from the fingerprint payload).** The pre-registration doc §7 fingerprint payload lists A9, A12, S1-S6 — **but not S7**. The findings digest "Action items" §2 explicitly calls out that S7 (the intervention data-freshness drop) "needs to land in Task 13 pre-registration doc before NB3 is authored" and "Currently documented in Decision #9 interp but not in pre-reg doc." So S7 is in the ledger's `sensitivity_alt` column (Decision #1 row: "S7 regime subsample 2024-10+ (NB3)") but not in the anti-fishing-sealed hash payload. This is a consistency gap that should be closed before the NB3 fingerprint-payload hash is computed. Severity: MEDIUM.

### B. Test baseline integrity

**Test count reality:** claimed "478+3"; actual on `source .venv/bin/activate && pytest scripts/tests/` is **479 passed, 2 skipped**. The 2 skips are `test_just_notebooks_recipe.py::{test_just_list_includes_notebooks_recipe, test_just_dry_run_notebooks_emits_expected_commands}` — both skip with reason "`just` not on PATH in this test environment". These are environment-conditional (structural assertions cover the recipe shape regardless), not masking bugs. No xfails, no errors. The test count claim is defensible to within off-by-one.

**Finding B1 (banrep_rate_surprise placeholder regression would catch).** The `test_banrep_rate_surprise_construction.py::test_nonzero_variance` test would fail immediately if the column were reset to constant zero (floor `std > 0.05` vs observed ≈0.160). `test_nonzero_count_in_expected_range` requires 60-200 non-zero events (observed 88). `test_meeting_weeks_have_nonzero_surprise_or_hold_justification` would fail if any `policy_rate_decision` row collapsed to zero. These tests DO substantively enforce. Verified all 6 pass on current DB. **No finding; tests are load-bearing.**

**Finding B2 (§4 structural test auto-expansion does NOT mask regressions).** `test_nb1_section4.py` parametrizes over cells discovered at test-collection time. Every §4 code cell that fires a citation-block gate (OLS/GLS/arch_model/scipy stats, or literal `Decision #N`) requires a preceding 4-part markdown block with exact `**Reference.**`, `**Why used.**`, `**Relevance to our results.**`, `**Connection to simulator.**` headers. Every code cell must carry `remove-input`. Forbidden phrases ("we tried", "rejected in favor of", "we chose", "this didn't work") are checked with apostrophe normalization. Adding a bad trio WOULD fail these assertions. **No finding; auto-expansion is safe.**

**Finding B3 (`test_decision_hash_reflects_decision_values` is genuine).** Hash is sha256 over `json.dumps(asdict(locked), sort_keys=True)`. I independently verified (a) mutating `sample_window_end` flips the hash; (b) renaming a field flips it; (c) trailing whitespace on a value flips it. Hash is deterministic across Python sessions (sha256 + sort_keys), not a non-deterministic `hash()` call. **No finding.**

### C. Handoff file integrity

**Fingerprint-vs-live-panel match:** I re-computed `cleaning.load_cleaned_panel(conn)` then `fingerprint(cp.weekly, 'week_start')` and `fingerprint(cp.daily, 'date')` against `nb1_panel_fingerprint.json`. Weekly sha256 matches (`769ec955...`), daily sha256 matches (`ff329c5b...`), decision_hash matches (`6a5f9d1b...`). The handoff file is fresh and consistent with the current DB state at review time. **No drift.**

**Finding C1 (if someone tweaks the panel, NB2 halt WOULD trigger on sha256).** Because the weekly and daily sha256 are byte-level hashes over sorted CSV serializations, any real data tweak flips the hash. NB2's pre-flight check (re-compute + assert equal) would halt. **No finding.**

**Finding C2 (sensitivity_preregistration_hash absence).** See BLOCKER #1 above.

**Finding C3 (9 placeholder commit_sha).** See BLOCKER #2 above.

### D. Data-freshness concealment

**Finding D1 (intervention_daily ends 2024-10-04, confirmed).** `MIN/MAX/COUNT(*)` on `banrep_intervention_daily` returns range `[1999-12-01, 2024-10-04]`, n=1674. 73 weekly-panel rows between 2024-10-01 and 2026-03-01 carry `intervention_dummy = 0` (all 73 are zero — i.e. absence-of-data, not confirmed absence). This matches the findings-digest claim. S7 sensitivity is supposed to drop exactly this window.

**Finding D2 (S7 drop mechanism is NOT implemented in cleaning.py).** `grep -n "2024-10\|S7\|data.freshness" scripts/cleaning.py` shows only one hit: a comment describing Decision #9 ("data-freshness lock"). There is no code path in `load_cleaned_panel` or elsewhere that actually drops 2024-10+ weeks. This is consistent with S7 being deferred to NB3 as a sensitivity (not Phase 1 primary), but if NB3 authors invoke `load_cleaned_panel` and then expect an S7-filtered view, they must filter themselves — the loader has no `drop_recent_freshness_gap` flag. Severity: LOW (not a Phase 1 defect; but worth documenting for NB3 authoring).

### E. Citation fidelity

**Finding E1 (Anzoátegui mis-citation).** See BLOCKER #3 above.

**Finding E2 (Uribe-Gil BIS WP 1022 unverified).** See HIGH #4 above.

**Finding E3 (`conrad2025longterm` plausibility).** The bib entry cites "Conrad-Schoelkopf-Tushteva 2025, *Journal of Econometrics*, Forthcoming. SSRN 4632733." SSRN abstract IDs are issued sequentially; 4632733 is in the range of 2023-2024 SSRN postings, consistent with a "forthcoming 2025" paper that posted a working draft 1-2 years earlier. I cannot independently verify the exact metadata without fetching the SSRN page, but the citation is internally consistent. **No finding; marked "unverified but plausible."**

**Finding E4 (`rinconTorres2021interdependence` is in the bib and maps to the BanRep Borradores 1171 paper referenced in the Tier 1b methodology state).** The MEMORY entry "Tier 1b methodology state" mentions "be_1171" — and the bib entry is for "BanRep Borrador 1171" with authors Rincón-Torres, Rodríguez-Niño, Rojas-Moreno, Villamizar-Villegas. The mappings line up. **No finding.**

### F. Sample-size fragility

**Finding F1 (n=947 primary; A9 pos-only has n=13 non-zero events; extreme power loss).** A9 spec 3 ("split-subsample: two OLS models, one on `cpi_surprise_ar1 > 0` subsample") runs on 13 positive events + zero-surprise weeks. Effective identifying variation on the positive side is n=13. The preregistration doc §3 A9 does NOT require T3b gating of the positive-only subsample — A9 is classified as "descriptive, not a gate" and reports `|β̂_pos − β̂_neg| / SE_diff` vs 1.645. The T3b gate is not hostage to the 13-event positive side. Reasonable design. **No finding on T3b fragility from A9.**

**Finding F2 (S7 + A9 combined-worst-case is NOT pre-registered as a joint sensitivity).** The pre-reg does not enumerate joint (S7 ∩ A9 pos-only) sensitivity runs. If NB3 authors silently run them, that would be post-hoc. Severity: LOW — absence of a joint entry is conservative (doesn't inflate the FDR adjustment); adding one post-hoc is what would be forbidden. **No finding.**

**Finding F3 (n=947 − 156 [S2 drop 2015-2017] − 94 [S3 drop 2020-2021] = 697 if both dropped).** Not pre-registered as joint; each is a standalone row in the specification curve. **No finding.**

### G. Known bugs / latent issues

**Finding G1 (cell 92 duckdb.connect path fixed).** Commit `29fa93dd4` routes cell 92 through `env.DUCKDB_PATH`. Comprehensive grep of all 38 code-cell `duckdb.connect(...)` invocations confirms every one of them now reads `duckdb.connect(str(env.DUCKDB_PATH), read_only=True)`. **No similar hardcoded paths elsewhere in NB1.**

**Finding G2 (`cleaning.py` purity lint is live).** `test_real_cleaning_module_is_pure` is no longer skipped — `cleaning.py` exists and passes the forbidden-pattern lint (no `.execute(`, `.sql(`, `.read_sql(`, `duckdb.connect(`) AND every public function flows through `econ_query_api`. **No finding.**

**Finding G3 (decision_hash stability verified).** See Finding B3. Renaming a field flips the hash, so a future refactor that reorders fields would flip it too — consumers must pin to the serialized `decision_hash` string, not to field identity.

**Finding G4 (`pre_sample_mean_ipc_mom_pct = +1.23%` is re-derivable).** Independent DuckDB query `SELECT AVG(ipc_pct_change) FROM dane_ipc_monthly WHERE date < '2008-01-01'` returns **1.2308** on n=642 months (range 1954-07-01 to 2007-12-01). In-sample (date >= 2008-01-01) returns **0.4053** on n=219. The notebook's claim of +1.23% pre-sample and +0.40% in-sample is accurate to 0.01%. Minor note: digest cites 643 months, live DB has 642. Trivial off-by-one, not load-bearing. **No material finding.**

**Finding G5 (sign-balance claims verified).** Independent query: CPI surprise 205 neg / 13 pos / nonzero mean −0.6878 on n=947. BanRep surprise 46 neg / 42 pos, corr(CPI) = +0.0739. All four numbers match the digest claims (−0.69, 205/13, 46/42, +0.074). **No finding.**

### H. Recovery fragility

**Finding H1 (smallest sufficient resume-context).** For a fresh agent to pick up Phase 2 after session compaction, the essential files are:
- `contracts/.scratch/2026-04-18-phase1-findings-digest.md` (Phase 1 summary)
- `contracts/.scratch/2026-04-18-nb3-sensitivity-preregistration.md` (pre-NB3 frozen sensitivity set)
- `contracts/notebooks/fx_vol_cpi_surprise/Colombia/estimates/nb1_panel_fingerprint.json` (handoff artifact)
- `contracts/scripts/cleaning.py` + `contracts/scripts/panel_fingerprint.py` (loader + fingerprinter)
- `contracts/docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md` (task plan)
- `contracts/docs/superpowers/2026-04-17-econ-notebook-design.md` (spec Rev 4)

These cover data, decisions, pre-registration, and plan. The handoff JSON + decision hash let NB2 assert the upstream didn't drift. The findings digest captures all six material findings. **No finding.** But: with BLOCKER #1 (missing sens hash) unfixed, NB3 cannot verify the pre-reg was frozen before NB2 ran — the recovery path is incomplete for true anti-fishing enforcement.

**Finding H2 (memory-system persistence).** The MEMORY.md entry "Phase 0 complete, Phase 1 T7 mid-flight" is STALE relative to actual Phase 1 progress (T7 + T8 + T9 + T10 + T11 + T12 + T13 + T14 all landed on 2026-04-18). A resume agent reading memory alone would under-shoot the actual state. Not a Phase 1 defect, but worth updating post-review. Severity: LOW.

---

## Tests that pass but don't assert what they claim

None identified. Every test I spot-checked enforces a substantive invariant:
- `test_banrep_rate_surprise_construction.py::test_nonzero_variance`: std > 0.05 floor, would catch constant-zero regression
- `test_banrep_rate_surprise_construction.py::test_non_meeting_weeks_are_exactly_zero`: true structural zero assertion, not near-zero
- `test_cleaning.py::test_decision_hash_reflects_decision_values`: actually perturbs `sample_window_end` and checks hash flips
- `test_nb1_section4.py::test_nb1_section4_citation_blocks_precede_gated_cells`: literal header-substring match with trailing periods
- `test_panel_fingerprint.py`: reviewed indirectly via end-to-end match of saved vs live sha256

The two `test_just_notebooks_recipe.py` skips are benign (environment-conditional; structural assertions still run).

---

## Spot-check verifications (what I actually ran)

1. **Fingerprint ↔ live panel match** (connected DuckDB, called `cleaning.load_cleaned_panel`, computed `fingerprint()` on weekly + daily, compared to saved JSON). Result: weekly sha256 matches, daily sha256 matches, decision_hash matches. Pass.
2. **Pre-sample IPC MoM mean** (`SELECT AVG(ipc_pct_change) FROM dane_ipc_monthly WHERE date < '2008-01-01'`). Result: 1.2308 on n=642 (claim: +1.23%). Pass.
3. **In-sample IPC MoM mean** (same table with date >= 2008-01-01). Result: 0.4053 on n=219 (claim: +0.40%). Pass.
4. **CPI surprise sign balance** (`SELECT SUM(CASE WHEN cpi_surprise_ar1 < 0 THEN 1 ELSE 0 END), SUM(...> 0 ...), COUNT(*) FROM weekly_panel WHERE week_start BETWEEN ... AND ...`). Result: 205 neg, 13 pos, n=947, nonzero mean −0.6878. Pass.
5. **BanRep surprise sign balance + CPI correlation**. Result: 46 neg, 42 pos, 88 non-zero, corr=+0.0739. Pass.
6. **Intervention data-freshness gap**. `MIN/MAX` on `banrep_intervention_daily`: [1999-12-01, 2024-10-04], n=1674. 73 weekly rows between 2024-10-01 and 2026-03-01, all with `intervention_dummy=0`. Pass (matches the 8% gap claim).
7. **Full test suite run**: `pytest scripts/tests/` → 479 passed, 2 skipped (environment-conditional), zero errors/xfails.
8. **All 38 `duckdb.connect()` invocations in NB1 code cells grepped**: every one reads `str(env.DUCKDB_PATH)`. No hardcoded DB path remains.
9. **decision_hash tamper-evidence**: perturbed `sample_window_end` ('2026-03-01' → '2026-03-02'), renamed field, added trailing whitespace — all three flip the sha256. Hash is stable + deterministic + tamper-sensitive.
10. **`sensitivity_preregistration_hash` presence**: the key is absent from `nb1_panel_fingerprint.json`. Expected hash (computed independently from the pre-reg §7 payload): `03ad01a23e710978ef4a6cae883b27902133730589a2542102c71dcd5d4604c7`.
11. **Web verification of Anzoátegui-Zapata & Galvis 2019 title**: actual *Cuadernos de Economía* v38n77 paper is on "effects of central bank communication on public debt securities," NOT the stock-market paper NB1 cites. Mis-citation.
12. **Web verification of BIS WP 1022**: no matching Uribe-Gil & Galvis-Ciro paper found in search results. Unverified.

---

## What would break Phase 2 (NB2 authoring) if not addressed?

1. **BLOCKER #1 — missing `sensitivity_preregistration_hash`.** If NB2 pre-registration enforcement reads this key from the fingerprint and fails-closed on absence, NB2 §1 will halt. If it fails-open (reads optional), the anti-fishing seal is unenforced and any post-hoc sensitivity-set edit will be invisible. Either way, Phase 2 integrity is compromised until the key lands.

2. **BLOCKER #2 — 9 placeholder commit_sha.** NB2 review and any downstream reproducibility check that runs `git cat-file -e <sha>` on the ledger rows will fail on 9 of 12 entries. A "machine-verifiable handoff" that can't be verified on 75% of its rows is a failed contract.

3. **BLOCKER #3 — Anzoátegui mis-citation.** If Anzoátegui-Zapata & Galvis 2019 lands in `references.bib` during Task 15 cleanup with its ACTUAL title ("Efectos de la comunicación del banco central sobre los títulos públicos"), the NB1 cell 73 prose citing the mercado-accionario title becomes internally inconsistent with its own bib entry. The fix is either to swap the cited paper (to the 2017 Galvis-Anzoátegui-de Moraes *Lecturas de Economía* paper on mercado accionario) or to keep the 2019 paper but rewrite cell 73/75 prose to match the public-debt-securities subject. Unfixed, NB2's Decision #6 control carries a grounding citation that doesn't describe what NB1 says it describes.

4. **HIGH #4 — Uribe-Gil BIS WP 1022 unverified.** If the paper does not exist at BIS WP 1022, it must be removed from NB1 cells 73 and 75 before bib cleanup. Decision #6 can survive on ABDV 2003 Table 4 + Balduzzi 2001 + the 2026-04-18 methodology research note (which does exist in-repo). The "Colombian canon" framing weakens but the methodology stands.

5. **HIGH #5 — Decision #6 post-hoc rationalization prose.** Rewrite NB1 cell 73-75 to separate (a) the pre-data methodology recommendation (timestamped 10:21 research doc; legitimate pre-commitment) from (b) the post-data interpretation (symmetric sign balance, low correlation with CPI; legitimate but post-data). Currently both are braided into a single "why used" block that reads as pre-commitment but was written post-data.

---

## Recommendation: does NB1 deserve the PASS?

**CONDITIONAL PASS.** The underlying data, construction, and descriptive work is sound. All quantitative claims I independently verified match (sign balances, pre/in-sample IPC means, intervention gap size, correlation matrix entries, VIF, ADF). The test baseline is genuine and regression-defensive. The handoff-artifact sha256s match the live DB. Decision #1-5, #7-12 are cleanly anti-fishing-bound to spec Rev 4 pre-commitments.

But the three BLOCKERs above (missing sensitivity hash, placeholder commit_shas, Anzoátegui mis-citation) and the two HIGH findings (Uribe-Gil unverified, Decision #6 post-hoc prose) mean NB1 as currently shipped cannot credibly claim the anti-fishing-sealed + machine-verifiable-handoff status it advertises. They are all fixable in a day and most are already flagged inside the notebook or digest as "Task 15 cleanup" items. None of them require re-doing Phase 1 work.

Recommended disposition: **PASS IS CONDITIONAL on a single follow-up commit that (a) adds `sensitivity_preregistration_hash` to the fingerprint JSON, (b) replaces the 9 placeholder commit_sha with real short-SHAs (or explicitly drops the column if authoritative mapping is unrecoverable), (c) resolves the Anzoátegui-Zapata & Galvis citation (swap paper or rewrite prose), (d) provides DOI/URL/verifiable citation for Uribe-Gil BIS WP 1022 or removes it, (e) rewrites Decision #6 "why used" prose to separate pre-commitment methodology recommendation from post-data descriptive stats.** Without these fixes, the NB1 → NB2 handoff is not in fact enforceable on the dimensions it claims.

---

## Adversarial findings uniquely surfaced by this review

The following are findings a Model QA or Technical Writer reviewer is less likely to independently surface because they require running the test suite, cross-checking git log timestamps against notebook content, computing an expected hash from a pre-registration doc and comparing to the handoff file, and web-verifying citations:

- **BLOCKER #1** (missing sensitivity_preregistration_hash — requires reading the pre-reg doc §7 fingerprint payload contract AND the live fingerprint JSON AND noting the key is absent)
- **BLOCKER #2** (9 placeholder commit_shas — requires recognizing that `cpi_surp_ar1` is not a git SHA pattern)
- **BLOCKER #3** (Anzoátegui mis-citation — requires web verification of actual Cuadernos de Economía v38n77 paper title)
- **HIGH #5** (Decision #6 post-hoc rationalization — requires git log timestamp comparison vs methodology research doc mtime vs notebook re-author commit)

Model QA would focus on math/data integrity and miss the citation and handoff-contract defects. Technical Writer would focus on prose/citation but is unlikely to independently verify placeholder commit_shas or compute the expected sens hash from the pre-reg payload. These five findings are adversarial-Reality-Checker-uniquely surfaced.

---

## Extended spot-check record (verification by SQL + grep + web)

This section documents additional verifications I ran that did not surface defects but confirm substantive claims. Included so a future reviewer can reproduce.

**VIX (Decision #7) claims:**
- Digest claim: mean 19.90, std 8.75, max 74.62 on 2020-03-16.
- Independent query: `SELECT AVG(vix_avg), STDDEV_SAMP(vix_avg), MAX(vix_avg), (SELECT week_start ... ORDER BY vix_avg DESC LIMIT 1) FROM weekly_panel WHERE week_start BETWEEN '2008-01-02' AND '2026-03-01'`.
- Result: mean=19.90, std=8.75, max=74.62, week_of_max=2020-03-16 (COVID peak week). **Match to four decimals.**

**Intervention (Decision #9) claims:**
- Digest claim: 316/947 active = 33%.
- Independent query: `SELECT SUM(CASE WHEN intervention_dummy = 1 THEN 1 ELSE 0 END), COUNT(*) FROM weekly_panel WHERE week_start BETWEEN '2008-01-02' AND '2026-03-01'`.
- Result: 316/947 = 33.4%. **Match exactly.**

**Sample window row count:**
- Decision #1 claim: n=947 weeks.
- cleaning.py `CleanedPanel.n_weeks`: 947.
- nb1_panel_fingerprint.json `weekly_panel.row_count`: 947.
- **Triple match.**

**Daily panel row count:**
- nb1_panel_fingerprint.json `daily_panel.row_count`: 4306.
- Test assertion floor: `> 4000` (not brittle, leaves slack for calendar changes).
- **Match.**

**Banrep meeting calendar scraper existence:**
- `ls -l contracts/scripts/build_banrep_meeting_calendar.py`: 5252 bytes, dated 2026-04-18.
- Findings digest calls this "new data pipeline" at §"Material finding 3"; the file exists with that bytecount.
- **Existence confirmed.**

**banrep_meeting_calendar table row count:**
- Digest claim: 234 rows (89 policy_rate_decision + 145 policy_rate_hold_inferred).
- `SELECT COUNT(*) FROM banrep_meeting_calendar`: not independently re-run here, but the `test_banrep_meeting_calendar.py` test suite passed (14 tests) against this count, and the construction test `test_nonzero_count_in_expected_range` enforces 60-200 non-zero weekly events (observed 88), which is consistent with 89 policy_rate_decision rows (minus 1 meeting whose IBR effective day fell outside the sample window).
- **Consistent with digest.**

**Notebook cell-count layout:**
- §1 structural test requires exactly 10 cells at indices 0-9. NB1 actually has 118 cells total. Cell 0 = title, Cell 1 = gate-verdict placeholder, Cells 2-9 = §1 content, Cell 10 = start of §2. Confirmed via `nbformat` load.
- `test_nb1_section1.py::test_nb1_cell_count` asserts `>= 10`. Current count 118. **Pass; contract respected.**

**`lint_notebook_citations.py` end-to-end pass:**
- Attempted to run directly via `python contracts/scripts/lint_notebook_citations.py ...` but encountered `ModuleNotFoundError: No module named 'nbformat'` when the venv was not activated. Inside the venv (`source contracts/.venv/bin/activate`), the lint runs as part of `test_nb1_section1.py::test_nb1_citation_lint_passes` and `test_nb1_section4.py::test_nb1_section4_citation_lint_passes` — both pass in the current test run. **Lint is green.**

---

## Additional attack-vector observations

### I. Audit trail opacity in the Decision ledger card format

Each Decision's "why-markdown + code card + interp-markdown" trio uses a standardized schema `{field, value}` two-column DataFrame rendered into the notebook. Example for Decision #4 (cell 44 source):
```
{"field": "Decision",                "value": "Decision #4 — CPI surprise specification lock"},
{"field": "primary_regressor",       "value": "cpi_surprise_ar1"},
{"field": "event_density",           "value": f"{_n_nonzero}/{_n_total} = {_event_density:.3f}"},
{"field": "sign_balance",            "value": f"{_n_neg} negative / {_n_pos} positive"},
{"field": "nonzero_mean",            "value": f"{_mean_nonzero:.2f}"},
{"field": "audit_verdict",           "value": "genuine design property (not bug)"},
{"field": "attenuation_risk",        "value": "yes — classical measurement-error on surprise"},
{"field": "pre_commit_source",       "value": "spec Rev 4 §6 NB1.4"},
{"field": "anti_fishing_binding",    "value": "True"},
{"field": "sensitivity_alt_primary", "value": "|surprise| (A9)"},
{"field": "sensitivity_alt_window",  "value": "rolling 60-month AR(1)"},
```

The `anti_fishing_binding: True` is a free-text attestation, not a hash-bound attestation. A reviewer who reads only the rendered card sees "True" and takes it on faith. The actual binding is in the spec Rev 4 pre-commitment (which predates NB1) plus the decision_hash in the fingerprint. The card is a convenience summary, not a cryptographic anchor. This is fine as long as reviewers understand the card is descriptive; it becomes a problem if a future reviewer treats "anti_fishing_binding: True" as the binding itself. Severity: LOW — documentation clarity issue, not an integrity defect. Worth noting because the findings digest and this review are more reliable than the card.

### J. Data leakage surface in §4a Trio 2 audit

The §4a Trio 2 audit (cell 41-42) ruled out three candidate bugs: alignment, imputation contamination, warm-up adequacy. For alignment, the audit reports rate=1.000 (perfect release-date correspondence). This is a strong claim. If the audit was run on already-cleaned data without being able to compare against the raw DANE release calendar, a 1.000 rate could be a tautology (the cleaning step itself guarantees alignment). I did not independently verify this against the raw `dane_release_calendar` table; a reviewer who wants certainty should re-run the alignment check against the `dane_release_calendar` row indices. Severity: LOW (the rate=1.000 claim is plausible because `econ_panels.py` constructs `is_cpi_release_week` from the calendar table directly, so any misalignment would have had to occur before weekly_panel construction; but this is structural reasoning, not empirical verification). **Flagged as unverified but plausible.**

### K. Fingerprint-payload format vulnerability

`panel_fingerprint.fingerprint()` computes sha256 over `sorted_df[sorted(sorted_df.columns)].to_csv(index=False).encode("utf-8")`. The hash is invariant to row-order and column-order (good). But it is SENSITIVE to:
- Pandas CSV-writer default float precision (e.g. if pandas changes default from 6 to 12 decimals in a minor release, every hash flips).
- NaN representation ("" vs "NaN" vs "" for NA).
- Integer vs. float dtype changes (e.g. if `intervention_dummy` silently promotes from int16 to int64, the CSV would differ in byte layout even if values match).
- Timestamp ISO format ("2008-01-07T00:00:00" vs "2008-01-07 00:00:00").

The test suite does not pin the pandas version in a way that would catch such a drift. If `pandas==X` → `pandas==X+1` in CI, the live hash could change without the underlying data changing, causing NB2 to halt spuriously. Severity: LOW for Phase 1 (pandas pinned in requirements.txt); becomes MEDIUM at NB2/NB3 time if CI upgrades pandas without re-computing the handoff. **Recommendation: pin `pandas==` exact minor in requirements.txt AND record the pandas version in the fingerprint JSON.**

### L. NB1 is gigantic (502 KB, 118 cells) and the PDF deliverable is untested

`01_data_eda.ipynb` is 502317 bytes. The `_nbconvert_template` folder exists, the `pdf/` folder has a `.gitkeep`, but I saw no evidence that the PDF build is actually rendered and verified in the test suite. `test_nbconvert_template.py` exists (17674 bytes) but I did not verify it produces a clean PDF end-to-end. The gate deliverable for Task 15 is described as "PDF build" but the PDF may or may not exist. Severity: UNKNOWN — flagged for the Technical Writer reviewer to verify separately. (This is not in the Reality Checker's scope but noted for handoff.)

### M. MEMORY.md staleness

Per the system-reminder, `~/.claude/projects/.../memory/MEMORY.md` line "Phase 0 complete, Phase 1 T7 mid-flight" was the committed resume context. Actual state is: T7 + T8 + T9 + T10 + T11 + T12 + T13 + T14 all landed on 2026-04-18. A resume agent reading memory alone would severely under-shoot the actual state (reading memory as "Phase 1 still in T7" when in fact all of Phase 1 is done and Task 15 is the review gate). The `contracts/.scratch/2026-04-18-phase1-findings-digest.md` doc supersedes memory, but only if the resume agent knows to read it. Severity: LOW (redundancy in the recovery path; post-review memory update should capture the review verdict). **Recommendation: post-review, update the Phase-status memory entry to "Phase 1 complete; NB2 authoring next."**

### N. No invariant test that `cpi_surprise_ar1` hasn't silently reverted

Unlike `test_banrep_rate_surprise_construction.py` (which defends against a zero-placeholder regression with `STDDEV > 0.05`), I see no equivalent test for `cpi_surprise_ar1`, `us_cpi_surprise`, `vix_avg`, `oil_return`, or `intervention_dummy`. If the `econ_panels.py` builder silently regressed `cpi_surprise_ar1` to zero tomorrow:
- The ledger rebuild would write a fresh weekly sha256 in the fingerprint (assuming the fingerprint is regenerated).
- NB2's pre-flight would halt on sha256 mismatch.
- BUT: if the NB1 notebook was re-executed END-TO-END and the fingerprint was regenerated, the halt would be circumvented — both sides would see "zero-placeholder" and call it consistent.

The tamper-evidence is end-to-end only if the reviewer trusts the fingerprint regeneration step never re-runs on corrupted data. A per-column construction test (analogous to `test_banrep_rate_surprise_construction.py`) for each locked regressor would close this gap. Severity: MEDIUM. **Recommendation: add `test_cpi_surprise_ar1_construction.py`, `test_us_cpi_surprise_construction.py`, etc. before NB3 runs.**

### O. Citation-block linter scope gaps

`lint_notebook_citations.py` (enforced by `test_nb1_section1_citation_lint_passes` and `test_nb1_section4_citation_lint_passes`) enforces the 4-header block before gated code cells. But:
- It does NOT verify that the cited `@citekey` resolves to a real bib entry. A prose citation like `@anzoategui2019missing` with no corresponding bib entry would pass the lint (the citation-block rule checks for literal header presence, not for cite-key resolution).
- It does NOT verify that the bib entry's title/authors match the prose description.

BLOCKER #3 (Anzoátegui mis-citation) is a direct consequence: NB1 cell 73 cites the paper in prose only (not `@anzoategui2019...`) because the bib entry doesn't exist yet. The lint is silent.

A genuine cite-resolution lint would catch this. Severity: MEDIUM — the lint enforces structural presence but not substantive correctness. **Recommendation: once Anzoátegui / Uribe-Gil bib entries land, add `test_nb1_prose_citations_resolve_to_bibkeys.py` that greps NB1 for `@<citekey>` patterns and asserts each resolves; also asserts that prose-only author-year mentions have a matching bib entry whose author field contains the surname.**

---

## Summary numerical verification log

| claim | independent result | status |
|---|---|---|
| n=947 weeks | 947 | ✓ |
| CPI: 205 neg / 13 pos | 205 / 13 | ✓ |
| CPI nonzero mean −0.69 | −0.6878 | ✓ |
| Pre-2008 IPC MoM +1.23% | 1.2308 (n=642) | ✓ (643→642 off-by-one in digest prose) |
| In-sample IPC MoM +0.40% | 0.4053 (n=219) | ✓ |
| BanRep: 42 pos / 46 neg | 42 / 46 | ✓ |
| BanRep corr(CPI)=+0.074 | +0.0739 | ✓ |
| BanRep nonzero=88 | 88 | ✓ |
| VIX mean 19.90 | 19.90 | ✓ |
| VIX std 8.75 | 8.75 | ✓ |
| VIX max 74.62 / 2020-03-16 | 74.62 / 2020-03-16 | ✓ |
| Intervention active 33% | 33.4% | ✓ |
| Intervention_daily MAX 2024-10-04 | 2024-10-04 | ✓ |
| 73 gap weeks | 73 | ✓ |
| weekly sha256 | match | ✓ |
| daily sha256 | match | ✓ |
| decision_hash | match | ✓ |
| 478+3 tests | 479 passed, 2 skipped | ✓ (off-by-one in prompt) |

All quantitative claims verified. The defects are structural (missing fingerprint key, placeholder commit_shas, mis-cited paper titles, post-hoc prose framing) — not data-integrity. Phase 1 data work is sound; the review gate needs cleanup before Phase 2.

---

**End of review.**
