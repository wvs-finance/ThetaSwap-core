# Reality Checker review — Task 11.O Step-0 default flip @ `202874565`

**Date:** 2026-04-25
**Reviewer:** TestingRealityChecker (foreground orchestrator dispatch)
**Subject commit:** `202874565` (Rev-5.3.2 Task 11.O Step 0 — `load_onchain_y3_weekly` default flip)
**DE memo under review:** `contracts/.scratch/2026-04-25-step0-default-flip-result.md`
**Verdict:** **PASS**
**Tool budget consumed:** 7 of 10

---

## §1. Live verification trace (all probes against canonical `contracts/data/structural_econ.duckdb`)

HEAD pinned at `202874565` (`git rev-parse HEAD` confirmed). Probe transcript:

### Probe 1 — Default-arg live behavior

```
PROBE-1: default-arg returned 116 rows; tags = {'y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable'}
PROBE-1: first week_start = 2024-01-12, last week_start = 2026-03-27
```

**MATCHES DE's smoke test** (memo §2: "116 rows … 2024-01-12 → 2026-03-27"). Single tag, v2 primary literal. **PASS.**

### Probe 2 — Pre-flip behavior reproduction (via diff inspection, no checkout)

`git diff 202874565~1 202874565 -- scripts/econ_query_api.py` shows the only behavioral diff in the function signature is the default literal change `"y3_v1"` → `"y3_v2_co_dane_…"`. Probe 7 below independently shows zero rows are stored under the bare `"y3_v1"` literal in the canonical DB. Therefore pre-flip `load_onchain_y3_weekly(conn)` would have returned `()` — the silent-empty footgun DE claims. **PASS** via diff + Probe 7 chain.

### Probe 3 — Step-7 synthetic round-trip (migrated)

```
scripts/tests/inequality/test_y3.py::test_step7_load_onchain_y3_weekly_returns_frozen_dataclass PASSED
```

**MATCHES DE's claim** (memo §4.1). Migration to explicit `source_methodology="y3_v1"` is green. **PASS.**

### Probe 4 — New failing-first test integrity

```
scripts/tests/inequality/test_y3_default_methodology.py::test_load_onchain_y3_weekly_default_returns_v2_primary_literal_rows PASSED
scripts/tests/inequality/test_y3_default_methodology.py::test_load_onchain_y3_weekly_default_matches_explicit_v2_primary_call PASSED
```

**MATCHES DE's claim** (memo §4.2: "2/2 GREEN post-flip"). **PASS.**

### Probe 5 — Inequality suite as a whole

```
100 passed, 1 skipped in 11.33s
```

**MATCHES DE's claim** (memo §5.4: "100 passed / 1 skipped"). **PASS.**

### Probe 6 — Validation-guard interaction

```
PROBE-6: default literal = 'y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable'
PROBE-6: default in admitted-set = True
PROBE-6: admitted-set size = 4; tags = ['y3_v1', 'y3_v1_3country_ke_unavailable',
         'y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable',
         'y3_v2_imf_only_sensitivity_3country_ke_unavailable']
```

Default literal is admitted; validation guard does not reject the new default; admitted-set membership UNCHANGED at 4 elements (matches DE memo §5.3 invariant). **PASS.**

### Probe 7 — Composite PK + per-tag row counts

```
'y3_v1_3country_ke_unavailable':                                           59
'y3_v2_co_dane_br_bcb_eu_eurostat_ke_skip_3country_ke_unavailable':       116
'y3_v2_imf_only_sensitivity_3country_ke_unavailable':                     116
```

Three distinct stored methodologies coexist in `onchain_y3_weekly` under composite PK. The bare `'y3_v1'` literal returns zero rows (it is absent from the GROUP BY result entirely) — confirming DE's silent-empty-footgun framing exactly. The Rev-5.3.1 Y₃ panel (59 rows under `y3_v1_3country_ke_unavailable`) is preserved unchanged; the IMF-only sensitivity panel (116 rows) is preserved unchanged. **PASS.**

---

## §2. Cross-validation against DE memo

| DE claim (memo location) | Live evidence | Status |
|--------------------------|---------------|--------|
| Default-arg returns 116 rows (§2 smoke test) | Probe 1: 116 rows | CONFIRMED |
| All rows carry v2 primary literal (§2) | Probe 1: single tag = v2 primary literal | CONFIRMED |
| Span 2024-01-12 → 2026-03-27 (§2) | Probe 1: identical span | CONFIRMED |
| Pre-flip: 0 rows under bare `"y3_v1"` (§2 table) | Probe 7: literal absent from GROUP BY | CONFIRMED |
| Rev-5.3.1 stored literal: 59 rows (§2 table) | Probe 7: 59 | CONFIRMED |
| v2 primary explicit-arg: 116 rows (§2 table) | Probe 1: 116 | CONFIRMED |
| Step-7 test green post-migration (§4.1) | Probe 3: PASSED | CONFIRMED |
| New file 2/2 green post-flip (§4.2) | Probe 4: 2/2 PASSED | CONFIRMED |
| Inequality suite: 100 passed / 1 skipped (§5.4) | Probe 5: 100 passed / 1 skipped | CONFIRMED |
| `_KNOWN_Y3_METHODOLOGY_TAGS` membership unchanged at 4 (§5.3) | Probe 6: 4 tags, listed | CONFIRMED |
| Validation guard accepts new default (§5.3) | Probe 6: default in admitted-set = True | CONFIRMED |

**Zero claim discrepancies.** DE memo is empirically watertight.

---

## §3. Adversarial probes for fantasy indicators

- **"Zero issues found" check.** No fantasy claim found — DE memo §6 acknowledges out-of-scope items, §7 explicitly lists three forwarded reviewer concerns (CR / RC / SD).
- **Specification compliance.** Plan line 1228 spec is "default-flip + Step-7 migration + new failing-first test"; commit delivers exactly that. No scope creep into `econ_pipeline.py`, `y3_compute.py`, `econ_schema.py`, or DuckDB writes (verified by `git show --stat` showing 4 files, all in scope).
- **Anti-fishing invariants.** Admitted-set membership unchanged (Probe 6); no MDES_FORMULATION_HASH touch (memo §5.3); no decision_hash touch; no panel-construction touch. Pure loader-default flip.
- **Real-data discipline.** New test consumes the canonical-DB `conn` fixture (memo §4.2 cites `scripts/tests/conftest.py:322`), not a mock — satisfies `feedback_real_data_over_mocks`.

---

## §4. Non-blocking advisory (forwarded to SD review)

**SD-A4 fold opportunity (already anticipated by DE memo §7).** The v2 primary literal is now duplicated in two locations: as the default-arg in `econ_query_api.py:1525` and as `REV_5_3_2_V2_PRIMARY_LITERAL: Final[str]` in `test_y3_default_methodology.py`. Forwarding to SD: at the 6-tag boundary (Task 11.O downstream growth), promote the v2 literal to a module-level `Final[str]` constant in `econ_query_api.py` so the test can `import` it instead of duplicating. This is **not** a blocker for Step 0 — the duplication is intentional defense against silent default drift (the test fails loudly if either side changes without coupled edit).

---

## §5. Verdict

**PASS.** All seven adversarial probes corroborate DE's load-bearing claims byte-for-byte against the live canonical DuckDB. The 116-row count is independently verified, the silent-empty-tuple footgun is empirically demonstrated (Probe 7), the validation guard accepts the new default, the admitted-set is preserved, and all migrated and new tests are green. Zero blast radius outside the inequality test module (memo §4.3 grep enumeration is structurally sound: only test callers exist).

Promotion to downstream Task 11.O Step-1 is supported.

---

End of review.
