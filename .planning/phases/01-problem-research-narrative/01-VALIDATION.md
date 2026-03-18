---
phase: 1
slug: problem-research-narrative
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual review + file existence checks |
| **Config file** | none — narrative/content phase |
| **Quick run command** | `ls research/figures/*.png && test -f .planning/phases/01-problem-research-narrative/narrative.md` |
| **Full suite command** | `ls research/figures/*.png && wc -l .planning/phases/01-problem-research-narrative/narrative.md` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run quick command to verify files exist
- **After every plan wave:** Verify all expected output files present with content
- **Before `/gsd:verify-work`:** All narrative sections and PNGs must exist
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | PROB-01 | file check | `grep -l "adverse competition" .planning/phases/01-problem-research-narrative/narrative.md` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | PROB-02 | file check | `grep -l "inverted-U" .planning/phases/01-problem-research-narrative/narrative.md` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | PROB-03 | file check | `grep -l "2.65" .planning/phases/01-problem-research-narrative/narrative.md` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | PROB-01 | file check | `test -f research/figures/dose-response.png` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 1 | PROB-02 | file check | `test -f research/figures/trigger-days.png` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 1 | PROB-02 | file check | `test -f research/figures/alpha-sweep.png` | ❌ W0 | ⬜ pending |
| 1-02-04 | 02 | 1 | PROB-03 | file check | `test -f research/figures/reserve-dynamics.png` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `research/figures/` directory — create output directory for PNG plots
- [ ] Narrative output file location established

*Existing infrastructure covers plot generation (notebooks + matplotlib).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Narrative is accessible to non-DeFi reader | PROB-01 | Readability is subjective | Read problem section; can you explain adverse competition in one sentence? |
| Three pillars structure (demand/price/backtest) | PROB-02 | Structural organization | Verify narrative has clear sections for each pillar |
| Statistics presented accessibly | PROB-03 | Presentation quality | Check stats have plain-English context, not just numbers |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 2s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
