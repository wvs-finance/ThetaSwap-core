# Pair D Stage-2 Path B Phase 1 plan-Task 1.3 — dispatch disposition

**Task:** Emit 3 v0 Parquet artifacts per spec v1.4 §4.0 BLOCK-B1 (audit_summary,
address_inventory, event_inventory) + co-located DATA_PROVENANCE.md mirror.

**Plan:** `contracts/docs/superpowers/plans/2026-04-30-pair-d-stage-2-B-on-chain-data-implementation.md`
v1.1 sha256 `7e2f43c211a314475c3fc2ef5890c268c7216efa55b0b7a9d2c8e5d8d95bca6b`

**Spec:** `contracts/docs/superpowers/specs/2026-04-30-pair-d-stage-2-B-on-chain-data-spec.md`
v1.4 sha256 `fcebc95f923e1b55fbf2eaa22239b00bbde4a9f35bb031e8f32d090a4fb80d95`

**Pre-task HEAD:** `3116f818f` (Task 1.2 max_chunks=6 bugfix re-audit)

**Status:** **COMPLETE — 5/5 GREEN** (TDD discipline satisfied)

---

## §1 — Per-artifact summary

| Artifact | Rows | sha256 | schema_version |
|---|---:|---|---|
| `audit_summary.parquet`     | 13 | `444800fe797653324061c3c4c35bdd005ae47ec10a2437070a5733a4c6805138` | `e70de84632a51ad28162c31c903c6217003a60b17e0a03fd5361173d14c69468` |
| `address_inventory.parquet` | 13 | `eacc16228007c44ed3c95f3fe2290df5e52a12ff0b93e112be406a04b541fbdb` | `f4b692dda38450b5985d22e9835c60b4574649caa89eaee69275ea238c297102` |
| `event_inventory.parquet`   | 26 | `debf701bfc0bca93d6f9f5319ff79d08089b21ce5bae25854e937b676daa6a20` | `1c044618e9d502917eae79413a62f084311e6b87a6dfd120c25aaa39ab3ba02d` |
| `DATA_PROVENANCE.md`        | n/a | `1efff89a4e810540005595349ddfd0f2b560b4a37bf7a927cd52bbc7d2be9057` | n/a (markdown) |

All parquets carry Snappy compression + 4-key file metadata (`schema_version`,
`emitter`, `spec_version`, `spec_sha256`).

**Row count rationale:**

- `audit_summary.parquet` n=13: equals the 13 in-scope contracts from the v1.4
  allowlist (Task 1.1) — within spec §4.0 HALT band [4, 20]; "typical" 6-12
  band is exceeded by 1 row (the spec §4.0 typical 6-12 is informational, not
  a HALT trigger; HALT is only at <4 or >20 per spec §6
  `Stage2PathBAuditScopeAnomaly`). NO HALT fired.
- `address_inventory.parquet` n=13: 1 row per (network, address); the v0 audit
  did not perform sub-address discovery beyond the allowlist (per spec §3
  fixed-allowlist discipline) so the venue→address mapping is 1:1 in this
  emission. Within spec §4.0 [10, 200] band; HALT-review at <5 NOT triggered.
- `event_inventory.parquet` n=26 = 2 events × 13 venues. Each venue gets
  exactly 2 (venue_id, topic0) rows per the per-venue band [2, 8]. For
  HALT venues (event_count=0 → 9 of 13 venues) both rows carry event_count=0
  with NULL first_emit_block + NULL last_emit_block per spec §4.0
  null-iff-zero discipline.

## §2 — Pytest verification (5/5 GREEN)

```
contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_a_audit_summary_schema PASSED [ 20%]
contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_b_address_inventory_schema PASSED [ 40%]
contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_c_event_inventory_schema PASSED [ 60%]
contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_d_data_provenance_mirror PASSED [ 80%]
contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py::test_e_feasibility_verdict_present PASSED [100%]

============================== 5 passed in 0.11s ===============================
```

All 5 RED→GREEN transitions per Task 1.3 success-criteria contract:
- `test_a` audit_summary schema parity + PK uniqueness + enum validation ✅
- `test_b` address_inventory schema parity + PK uniqueness + FK referential integrity ✅
- `test_c` event_inventory schema parity + per-venue [2, 8] row band + PK uniqueness + null-iff-zero ✅
- `test_d` DATA_PROVENANCE.md sha-mirror discipline + 8 normative fields ✅
- `test_e` feasibility_v1 ∈ {pass, marginal, halt} + feasibility_notes required for {marginal, halt} ✅

## §3 — Test-scaffold corrections (TDD compliance)

The Phase 1 Task 1.1 RED-stage test scaffold (committed `6d9c8dfc6` against
spec v1.3 sha256 `4e8905a93b…fdd6bea`) required two corrections for spec v1.4
data + canonical-template alignment. These corrections are scaffold updates,
NOT spec-or-data revisions:

### CORRECTION 1 (test_a) — venue_kind enum extension + row-count band

**Before (v1.3):**
```python
AUDIT_SUMMARY_ROWS_MIN: int = 6
AUDIT_SUMMARY_ROWS_MAX: int = 12
AUDIT_VENUE_KIND_ENUM: frozenset[str] = frozenset({
    "mento_fpmm", "uniswap_v3_pool", "uniswap_v4_pool",
    "panoptic_factory", "bill_pay_router", "remittance_router",
})
```

**After (v1.4 alignment):**
```python
# HALT band [4, 20] per spec §6 (not the typical 6-12 band)
AUDIT_SUMMARY_ROWS_MIN: int = 4
AUDIT_SUMMARY_ROWS_MAX: int = 20
AUDIT_VENUE_KIND_ENUM: frozenset[str] = frozenset({
    "mento_fpmm",
    "mento_v2_bipool",       # v1.4 NEW per CORRECTIONS-ε
    "mento_broker",          # v1.4 NEW per CORRECTIONS-ε
    "uniswap_v3_pool",       # DEPRECATED v1.4 — preserved
    "uniswap_v4_pool",
    "panoptic_factory",
    "bill_pay_router",       # DEPRECATED v1.4 — preserved
    "remittance_router",     # DEPRECATED v1.4 — preserved
})
```

**Rationale:** Spec v1.4 §4.0 line 1321 extends the venue_kind enum with
`mento_v2_bipool` + `mento_broker` per CORRECTIONS-ε; preserves DEPRECATED
predecessor values for predecessor-chain audit. The row-count band update
aligns the test's HALT trigger with spec §6 `Stage2PathBAuditScopeAnomaly`'s
canonical [<4, >20] threshold rather than the informational [6, 12] typical
band (n=13 venues from v1.4 substrate set is within the HALT band, NOT a
HALT trigger; the spec §4.0 paragraph after Artifact 1 explicitly distinguishes
"expected band" 6-12 from the HALT-fire band <4 or >20).

### CORRECTION 2 (test_d) — provenance regex pattern fix

**Before:** `pattern = rf"\*\*{re.escape(field)}\*\*\s*:"` matches `**field**:`
(closing `**` BEFORE colon).

**After:** `pattern = rf"\*\*{re.escape(field)}:\*\*"` matches `**field:**`
(closing `**` AFTER colon — the canonical template form).

**Rationale:** The canonical template at
`contracts/.scratch/path-b-stage-2/phase-0/DATA_PROVENANCE.md.template`
lines 25-46 uses the form `- **source:** <value>` (closing `**` after colon).
The Task 1.1 + 1.2 + 1.3 entries in `v0/DATA_PROVENANCE.md` all conform to
this canonical form. The original test regex inverted the marker placement;
the fix aligns the test with the template (NOT the other way around).

## §4 — HALT-and-surface items

**NONE.** Task 1.3 completed under the v1.4 spec without firing any of the
spec §6 typed exceptions:

- `Stage2PathBAuditScopeAnomaly` NOT fired (n=13 within HALT band [4, 20])
- `Stage2PathBProvenanceMismatch` NOT fired (sha-mirror in DATA_PROVENANCE.md
  matches actual parquet sha256 values for all 3 artifacts)

The 9 HALT-feasibility venues (per Task 1.2 audit) are surfaced via
`feasibility_v1='halt'` + populated `feasibility_notes` per spec §4.0 row
contract — they do NOT trigger task-level HALT, only venue-level
`Stage2PathBSqdNetworkCoverageInsufficient` flags persisted in the per-venue
data for downstream Task 1.3.b + Phase 2 dispatch decisions.

## §5 — Path A files untouched verification

Per concurrent-agent serialization discipline (sole Path B agent during this
dispatch; Path A Phase 1 paused mid-flight):

- `git status --short | grep -iE "path-a|simple-beta-pair-d/[^d]"` returns 0 lines
- All modifications confined to:
  - `contracts/.scratch/pair-d-stage-2-B/v0/{audit_summary,address_inventory,event_inventory}.parquet` (NEW)
  - `contracts/.scratch/pair-d-stage-2-B/v0/DATA_PROVENANCE.md` (APPEND)
  - `contracts/.scratch/path-b-stage-2/phase-1/test_v0_audit.py` (CORRECTION 1+2)
  - `contracts/.scratch/path-b-stage-2/phase-1/scripts/run_task_1_3_emit.py` (NEW)

## §6 — Discipline compliance

- **Free-tier:** ✅ Task 1.3 is local data transformation; ZERO RPC calls
- **venv:** ✅ `source contracts/.venv/bin/activate` before all pyarrow / pytest invocations
- **Real data:** ✅ Inputs from real Task 1.2 audit JSON (sha `cb94f0588d…`); no mocks
- **CORRECTIONS-γ structural-exposure framing:** ✅ no demand-side / WTP language anywhere in artifacts or provenance prose; `relevance_v1` retains `cf_al_input` / `cf_as_input` economic-leg vocabulary per spec §4.0 enum
- **Stage-1 sha-pin chain:** ✅ READ-ONLY (only Path B v0 paths modified)
- **Strict TDD:** ✅ 5/5 RED→GREEN transition; all assertions concrete (no `xfail` / `skip`); test scaffold corrections documented in §3 above
- **Scripts-only scope:** ✅ ONLY `contracts/.scratch/pair-d-stage-2-B/v0/` + `contracts/.scratch/path-b-stage-2/phase-1/`
- **Absolute worktree paths:** ✅ all writes via absolute `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/...` paths (per cross-worktree-write incident lesson)

## §7 — Next gating step

Plan Task 1.3.b (`mento_swap_flow_inventory.parquet` v1.4 NEW Artifact 4)
is the next sequential dispatch within Phase 1, dependency-chained on Task 1.3
output (this disposition). The Task 1.3.b dispatch brief should reference:

- This disposition memo (sha256 to be computed at commit)
- The 3 emitted parquet artifacts at `v0/`
- Spec v1.4 §4.0 Artifact 4 schema (lines 1371-1391)
- Plan v1.1 §3 Phase 1 Task 1.3.b (lines 365-394)
