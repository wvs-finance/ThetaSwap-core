# Scratch / Specs / Notes Cleanup Plan

Date: 2026-04-17
Branch: `phase0-vb-mvp` (worktree: ranFromAngstrom)
Scope: `contracts/.scratch/` + `contracts/docs/superpowers/{specs,plans}/` + `contracts/notes/`

## Goals

1. Remove stale files that bloat agent context and can mis-route decisions.
2. Preserve audit-trail artifacts (accepted-revision reviews) in a gitignored archive.
3. Leave only the **canonical current working set** in live paths.

---

## Dispositions

Three dispositions:

- **KEEP** — in a live path; currently referenced by active work.
- **ARCHIVE** — move to `contracts/.archive/2026-Q2/` (gitignored); preserved off-context for audit / historical reference.
- **DELETE** — permanent removal (git-tracked files get `git rm`; untracked files get `rm`).

---

## Staleness Criteria (identified)

### DELETE criteria

1. **Superseded review artifact.** A later revision of the same spec was accepted; the earlier-revision triad no longer reflects the canonical reasoning. Example: `fx-vol-spec-review-*` (v1) when `v4` was accepted.
2. **Abandoned workstream with no traceable downstream.** Work was superseded by a pivot (e.g., Solidity growth-pipeline → Python structural-econ pipeline). No current artifact references it.
3. **Backup / editor cruft.** Files ending in `~` or `.log` that are not the canonical artifact.
4. **One-off investigations whose conclusions were rolled into a spec.** The spec is the preserved conclusion; the investigation is redundant.

### ARCHIVE criteria

1. **Accepted-revision review artifact.** The three reviewer outputs that blessed the final revision — keep for audit trail, out of live context.
2. **Historical spec/plan that shaped current direction but is no longer active.** Preserves the "why we pivoted" narrative without weighing down agent reads.
3. **Approved external-positioning artifacts** (Abrigo reviews, logo retrospectives) where the implementation is already merged.

### KEEP criteria

1. **Active spec or plan** referenced by an open PR or currently-executing workstream.
2. **Canonical current-revision** of a multi-revision document (only the final rev, never the intermediate ones).
3. **Source-of-truth notes** still being edited or consumed.

---

## File-by-file disposition

Tables below group by workstream lineage. Paths are relative to repo root.

### W1 — Growth-pipeline / Vault-stack (Apr 9–13) — pre-pivot Solidity work

Pivoted to Python-only Phase 5 (per memory `project_ran_python_session.md`). No downstream consumer.

| File | Disposition | Reason |
|---|---|---|
| `contracts/.scratch/spec-review-completeness.md` | DELETE | Review of superseded spec rev |
| `contracts/.scratch/spec-review-completeness-rev2.md` | DELETE | " |
| `contracts/.scratch/spec-review-completeness-rev3.md` | DELETE | " |
| `contracts/.scratch/spec-review-completeness-rev6.md` | DELETE | " |
| `contracts/.scratch/spec-review-completeness-rev7.md` | DELETE | " |
| `contracts/.scratch/spec-review-economic-coherence.md` | DELETE | " |
| `contracts/.scratch/spec-review-economic-coherence-rev2.md` | DELETE | " |
| `contracts/.scratch/spec-review-economic-coherence-rev3.md` | DELETE | " |
| `contracts/.scratch/spec-review-economic-rev6.md` | DELETE | " |
| `contracts/.scratch/spec-review-economic-rev7.md` | DELETE | " |
| `contracts/.scratch/angstrom-accumulator-consumer-btt-spec.md` | DELETE | Abandoned Solidity BTT spec |
| `contracts/.scratch/angstrom-pool-observer-btt-spec.md` | DELETE | " |
| `contracts/.scratch/ema-growth-transformation-lib-btt-spec.md` | DELETE | " |
| `contracts/.scratch/ema-growth-transformation-storage-mod-btt-spec.md` | DELETE | " |
| `contracts/.scratch/growth-observation-v2-btt-spec.md` | DELETE | " |
| `contracts/.scratch/growth-observation-storage-mod-btt-spec.md` | DELETE | " |
| `contracts/.scratch/growth-observer-lib-btt-spec.md` | DELETE | " |
| `contracts/.scratch/growth-to-tick-lib-btt-spec.md` | DELETE | " |
| `contracts/.scratch/v-b-vault-btt-spec.md` | DELETE | " |
| `contracts/.scratch/security-audit-*.md` (9 files) | DELETE | Audits of abandoned contracts |
| `contracts/.scratch/security-edge-cases-*.md` (3 files) | DELETE | " |
| `contracts/.scratch/security-round2.md` | DELETE | " |
| `contracts/.scratch/security-final-review.md` | DELETE | " |
| `contracts/.scratch/code-review-*.md` (7 files) | DELETE | Reviews of abandoned Solidity code |
| `contracts/.scratch/code-review-v2-final.md` | DELETE | " |
| `contracts/.scratch/test-review-growth-observer.md` | DELETE | Test review of abandoned code |
| `contracts/.scratch/ema-test-review.md` | DELETE | " |
| `contracts/.scratch/diff-tests-review-round2.md` | DELETE | " |
| `contracts/.scratch/integration-review-and-flaws.md` | DELETE | " |
| `contracts/.scratch/senior-dev-test-review.md` | DELETE | " |
| `contracts/.scratch/senior-round2.md` | DELETE | " |
| `contracts/.scratch/reality-check-tests.md` | DELETE | " |
| `contracts/.scratch/reality-round2.md` | DELETE | " |
| `contracts/.scratch/baseline-test-02-implement.md` | DELETE | " |
| `contracts/.scratch/green-test-02-implement.md` | DELETE | " |
| `contracts/.scratch/erc4626-diamond-facet-research.md` | DELETE | Research for abandoned diamond vault |
| `contracts/.scratch/compose-vs-solady-vault-tradeoff.md` | DELETE | " |
| `contracts/.scratch/vault-pattern-comparison-euler-balancer.md` | DELETE | " |
| `contracts/.scratch/vault-yield-function-research.md` | DELETE | " |
| `contracts/.scratch/balancer-concrete-imports.md` | DELETE | " |
| `contracts/.scratch/balancer-rate-provider-deep-dive.md` | DELETE | " |
| `contracts/.scratch/time-weighted-oracle-patterns-research.md` | DELETE | " |
| `contracts/.scratch/token-supply-mutation-research.md` | DELETE | " |
| `contracts/.scratch/mean-reversion-validation.md` | DELETE | " |
| `contracts/.scratch/aquilina-risk-taxonomy.md` | DELETE | Superseded by Tier 1 feasibility spec |
| `contracts/.scratch/ran-residual-risk-scenarios.md` | DELETE | " |
| `contracts/.scratch/angstrom-risk-mitigation-map.md` | DELETE | " |
| `contracts/.scratch/gap-analysis-oracle-vs-spec.md` | DELETE | Abandoned oracle workstream |
| `contracts/docs/superpowers/specs/2026-04-09-angstrom-panoptic-vault-architecture-design.md` | ARCHIVE | Historical pre-pivot architecture; keep for "why we pivoted" |
| `contracts/docs/superpowers/specs/2026-04-10-ran-growth-pipeline-design.md` | ARCHIVE | " |
| `contracts/docs/superpowers/specs/2026-04-13-rev10-vault-stack.md` | ARCHIVE | " |
| `contracts/docs/superpowers/specs/2026-04-13-phase0-mvp.md` | **KEEP** | Current branch is `phase0-vb-mvp`; overarching context |
| `contracts/docs/superpowers/plans/2026-04-10-ran-growth-pipeline.md` | ARCHIVE | Historical plan |

### W2 — RAN FFI lib (Apr 11) — superseded by Phase 5 Python pipeline

| File | Disposition | Reason |
|---|---|---|
| `contracts/.scratch/2026-04-11-ran-ffi-lib-plan.md` | DELETE | Workstream replaced by Python data pipeline |
| `contracts/.scratch/ran-ffi-lib-design.md` | DELETE | " |
| `contracts/.scratch/ran-ffi-lib-review-reality-checker.md` | DELETE | " |
| `contracts/.scratch/ran-ffi-lib-review-reality-checker-r2.md` | DELETE | " |
| `contracts/.scratch/ran-ffi-lib-review-solidity-dev.md` | DELETE | " |
| `contracts/.scratch/ran-ffi-lib-review-solidity-dev-r2.md` | DELETE | " |
| `contracts/docs/superpowers/specs/2026-04-11-ran-ffi-query-api-design.md` | ARCHIVE | Historical; superseded by Python |
| `contracts/docs/superpowers/plans/2026-04-11-ran-ffi-query-api.md` | ARCHIVE | " |
| `contracts/docs/superpowers/specs/2026-04-11-ran-data-api-design.md` | ARCHIVE | " |
| `contracts/docs/superpowers/plans/2026-04-11-ran-data-api.md` | ARCHIVE | " |

### W3 — RAN fork test (Apr 7) — one-off validation

| File | Disposition | Reason |
|---|---|---|
| `contracts/docs/superpowers/specs/2026-04-07-ran-fork-test-design.md` | ARCHIVE | Validation complete |
| `contracts/docs/superpowers/plans/2026-04-07-ran-fork-test.md` | ARCHIVE | " |

### W4 — Angstrom indexer / Dune research (Apr 10)

| File | Disposition | Reason |
|---|---|---|
| `contracts/.scratch/angstrom-indexer-globalGrowth-research.md` | DELETE | Conclusion rolled into structural-econ specs |
| `contracts/.scratch/competing-agents-research.md` | DELETE | One-off investigation; stale |
| `contracts/.scratch/dune-angstrom-tables-research.md` | DELETE | " |

### W5 — Tier 1 literature review (Apr 14)

Triad rev1 is superseded by rev2 which was accepted.

| File | Disposition | Reason |
|---|---|---|
| `contracts/.scratch/2026-04-14-tier1-review-code-reviewer.md` | DELETE | Superseded by rev2 |
| `contracts/.scratch/2026-04-14-tier1-review-reality-checker.md` | DELETE | " |
| `contracts/.scratch/2026-04-14-tier1-review-technical-writer.md` | DELETE | " |
| `contracts/.scratch/2026-04-14-tier1-rev2-review-code-reviewer.md` | ARCHIVE | Accepted-revision review, audit trail |
| `contracts/.scratch/2026-04-14-tier1-rev2-review-reality-checker.md` | ARCHIVE | " |
| `contracts/.scratch/2026-04-14-tier1-rev2-review-technical-writer.md` | ARCHIVE | " |
| `contracts/docs/superpowers/specs/2026-04-14-inflation-mirror-tier1-feasibility-design.md` | **KEEP** | Referenced by structural-econ + Abrigo evidence base |
| `contracts/docs/superpowers/plans/2026-04-14-inflation-mirror-tier1-literature.md` | **KEEP** | " |

### W6 — Abrigo branding agent (Apr 15–16)

Spec + plan accepted; triad reviews are audit trail.

| File | Disposition | Reason |
|---|---|---|
| `contracts/.scratch/2026-04-15-abrigo-spec-review-code-reviewer.md` | ARCHIVE | Accepted-revision review |
| `contracts/.scratch/2026-04-15-abrigo-spec-review-reality-checker.md` | ARCHIVE | " |
| `contracts/.scratch/2026-04-15-abrigo-spec-review-technical-writer.md` | ARCHIVE | " |
| `contracts/.scratch/2026-04-15-abrigo-plan-review-code-reviewer.md` | ARCHIVE | " |
| `contracts/.scratch/2026-04-15-abrigo-plan-review-reality-checker.md` | ARCHIVE | " |
| `contracts/.scratch/2026-04-15-abrigo-plan-review-technical-writer.md` | ARCHIVE | " |
| `contracts/.scratch/2026-04-15-abrigo-hook-schema.md` | ARCHIVE | Design rationale for shipped hook |
| `contracts/.scratch/2026-04-15-abrigo-evidence-preflight.md` | ARCHIVE | One-off preflight, completed |
| `contracts/.scratch/2026-04-15-abrigo-reviewer-charter-check.md` | ARCHIVE | One-off audit, completed |
| `contracts/.scratch/2026-04-15-abrigo-un-archive-rollback.md` | ARCHIVE | " |
| `contracts/.scratch/2026-04-15-abrigo-logo-engineer-charter-check.md` | ARCHIVE | " |
| `contracts/.scratch/2026-04-15-abrigo-logo-retrospective.md` | ARCHIVE | Retrospective, completed |
| `contracts/.scratch/2026-04-15-abrigo-resume-note.md` | DELETE | Ephemeral handoff note, stale |
| `contracts/.scratch/abrigo-hook-decisions.log` | DELETE | Runtime log, not source of truth |
| `contracts/.scratch/dsquared-pi-logo-prompt.md` | ARCHIVE | Design artifact referenced by logo-prompt-library |
| `contracts/.scratch/dsquared-pi-logo-prompt.md~` | DELETE | Editor backup |
| `contracts/docs/superpowers/specs/2026-04-15-abrigo-branding-agent-design.md` | **KEEP** | Active external-positioning system |
| `contracts/docs/superpowers/plans/2026-04-15-abrigo-branding-agent.md` | **KEEP** | " |
| `contracts/docs/superpowers/specs/2026-04-15-abrigo-logo-prompt-library-design.md` | **KEEP** | " |
| `contracts/docs/superpowers/plans/2026-04-15-abrigo-logo-prompt-library.md` | **KEEP** | " |

### W7 — FX-vol spec (Apr 15–16)

Rev 4 accepted per memory `project_phase5_ready_state.md`. v1–v3 reviews superseded.

| File | Disposition | Reason |
|---|---|---|
| `contracts/.scratch/2026-04-15-fx-vol-spec-review-*` (3 files: adversarial-referee, model-qa, reality-checker) | DELETE | Superseded by v4 |
| `contracts/.scratch/2026-04-15-fx-vol-spec-v2-review-*` (3 files) | DELETE | " |
| `contracts/.scratch/2026-04-15-fx-vol-spec-v3-review-*` (3 files) | DELETE | " |
| `contracts/.scratch/2026-04-15-fx-vol-spec-v4-review-adversarial-referee.md` | ARCHIVE | Accepted-revision audit trail |
| `contracts/.scratch/2026-04-15-fx-vol-spec-v4-review-model-qa.md` | ARCHIVE | " |
| `contracts/.scratch/2026-04-15-fx-vol-spec-v4-review-reality-checker.md` | ARCHIVE | " |
| `contracts/notes/structural-econometrics/specs/2026-04-15-fx-vol-cpi-surprise.md` | **KEEP** | Canonical Rev 4 spec |

### W8 — Data schema & acquisition (Apr 16)

Rev 3 accepted (in PR #72). v1 reviews superseded.

| File | Disposition | Reason |
|---|---|---|
| `contracts/.scratch/2026-04-16-data-schema-review-data-engineer.md` | DELETE | Superseded by rev2/rev3 |
| `contracts/.scratch/2026-04-16-data-schema-review-model-qa.md` | DELETE | " |
| `contracts/.scratch/2026-04-16-data-schema-review-reality-checker.md` | DELETE | " |
| `contracts/.scratch/2026-04-16-data-schema-rev2-review-data-engineer.md` | ARCHIVE | Accepted-revision audit trail (rev2 → rev3 only editorial) |
| `contracts/.scratch/2026-04-16-data-schema-rev2-review-model-qa.md` | ARCHIVE | " |
| `contracts/.scratch/2026-04-16-data-schema-rev2-review-reality-checker.md` | ARCHIVE | " |
| `contracts/.scratch/2026-04-16-impl-plan-review-code-reviewer.md` | ARCHIVE | Plan-review triad (accepted) |
| `contracts/.scratch/2026-04-16-impl-plan-review-data-engineer.md` | ARCHIVE | " |
| `contracts/.scratch/2026-04-16-impl-plan-review-reality-checker.md` | ARCHIVE | " |
| `contracts/.scratch/2026-04-16-suameca-investigation.md` | DELETE | One-off; conclusion rolled into spec |
| `contracts/.scratch/2026-04-16-data-validation-report.md` | ARCHIVE | Verification artifact for accepted spec |
| `contracts/.scratch/2026-04-16-econ-api-design-recommendations.md` | ARCHIVE | Design rationale rolled into econ-query-api plan |
| `contracts/notes/structural-econometrics/specs/2026-04-16-data-schema-acquisition.md` | **KEEP** | Canonical Rev 3 (PR #72) |
| `contracts/docs/superpowers/plans/2026-04-16-structural-econ-data-pipeline.md` | **KEEP** | Active plan |
| `contracts/docs/superpowers/plans/2026-04-16-econ-query-api.md` | **KEEP** | Active plan |

### W9 — Notebook design (Apr 17) — CURRENT workstream

| File | Disposition | Reason |
|---|---|---|
| `contracts/.scratch/2026-04-17-notebook-structure-research.md` | **KEEP** | Active research for nb1–nb3 |
| `contracts/.scratch/2026-04-17-nb1-eda-conventions-research.md` | **KEEP** | " |
| `contracts/.scratch/2026-04-17-nb2-estimation-and-handoff-research.md` | **KEEP** | " |
| `contracts/.scratch/2026-04-17-nb3-tests-sensitivity-research.md` | **KEEP** | " |
| `contracts/.scratch/2026-04-17-notebook-design-review-data-engineer.md` | **KEEP** | Active review (spec not yet locked) |
| `contracts/.scratch/2026-04-17-notebook-design-review-model-qa.md` | **KEEP** | " |
| `contracts/.scratch/2026-04-17-notebook-design-review-reality-checker.md` | **KEEP** | " |
| `contracts/.scratch/2026-04-17-plan-review-code-reviewer.md` | **KEEP** | Active plan review |
| `contracts/.scratch/2026-04-17-plan-review-spm.md` | **KEEP** | " |
| `contracts/.scratch/2026-04-17-plan-review-reality-checker.md` | **KEEP** | " |
| `contracts/docs/superpowers/specs/2026-04-17-econ-notebook-design.md` | **KEEP** | Current spec |
| `contracts/docs/superpowers/plans/2026-04-17-econ-notebook-implementation.md` | **KEEP** | Current plan |

### W10 — Notes / Playgrounds

| File | Disposition | Reason |
|---|---|---|
| `contracts/notes/playgrounds/OPTION_STRATEGIES.md` | **KEEP** | Reference notes, small, cheap |
| `contracts/notes/structural-econometrics/identification/2026-04-14-inflation-mirror-two-channel-literature.md` | **KEEP** | Current literature review |
| `contracts/notes/structural-econometrics/identification/2026-04-14-inflation-mirror-two-channel-literature-human-review.md` | **KEEP** | Current human annotations |
| `contracts/notes/structural-econometrics/identification/2026-04-14-inflation-mirror-two-channel-literature-human-review.md~` | DELETE | Editor backup |

---

## Summary counts

| Disposition | Count | Est. token savings |
|---|---|---|
| DELETE | ~85 files | ~950 KB (removes ~240K tokens of potential context) |
| ARCHIVE | ~26 files | ~520 KB (still on disk, invisible to agents) |
| KEEP | ~30 files | canonical working set |

---

## Execution steps (DO NOT RUN — pending approval)

```bash
# 1. Create archive target (gitignored)
mkdir -p contracts/.archive/2026-Q2/{scratch,docs/specs,docs/plans}
echo ".archive/" >> contracts/.gitignore   # if not already ignored

# 2. ARCHIVE phase — git mv tracked files (preserves history), mv for untracked
#    [one command per ARCHIVE-row, grouped by workstream]

# 3. DELETE phase
#    git rm <tracked-files>
#    rm <untracked-files>

# 4. Commit
git add -A
git commit -m "chore: cleanup stale scratch/specs — archive accepted-revision triads, delete abandoned workstreams"

# 5. Verify agent read-surface
find contracts/.scratch -type f | wc -l   # expected: ~15
find contracts/docs/superpowers -type f | wc -l  # expected: ~10
```

---

## Open questions before execution

1. **Phase-0 MVP spec** (`contracts/docs/superpowers/specs/2026-04-13-phase0-mvp.md`): current branch name is `phase0-vb-mvp`, so this spec likely is the branch charter. I marked it **KEEP** — confirm?
2. **Abrigo hook decisions log** (`abrigo-hook-decisions.log`): the hook itself logs to `.branding/` (gitignored); this scratch log duplicates runtime output. Confirm DELETE?
3. **Archive location**: Is `contracts/.archive/2026-Q2/` the right path, or would you prefer `contracts/.scratch/.archive/`, or a branch-local archive outside the worktree?
4. **Git history**: For ARCHIVE files that are tracked in git (e.g., Abrigo spec/plan — but those I'm KEEPing anyway), everything in ARCHIVE set is currently untracked `.scratch/` content + tracked `docs/superpowers/` content. For tracked content, should I use `git mv` (preserve blame) or `git rm` + untracked copy (breaks blame)?
5. **Notebook workstream (W9)**: I kept everything because the spec/plan is actively under review. Confirm the triad/plan-review files should all stay live until the notebook impl lands?

Once these are answered I'll build the concrete command sequence.
