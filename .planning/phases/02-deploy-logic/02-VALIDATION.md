---
phase: 2
slug: deploy-logic
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | cargo test (Rust built-in) |
| **Config file** | `d2p/Cargo.toml` |
| **Quick run command** | `cd d2p && cargo check` |
| **Full suite command** | `cd d2p && cargo test` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd d2p && cargo check`
- **After every plan wave:** Run `cd d2p && cargo test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | DEP-04 | unit | `cd d2p && cargo test path_check` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | DEP-01,DEP-06 | unit | `cd d2p && cargo test primary` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | DEP-02,DEP-03 | unit | `cd d2p && cargo test fallback` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | DEP-05 | unit | `cd d2p && cargo test receipt` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 1 | OUT-01,OUT-04 | unit | `cd d2p && cargo test runner` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Existing `d2p/` crate from Phase 1 compiles

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| forge→cast fallback fires on real RPC | DEP-02 | Requires live Foundry + RPC | Deploy to Lasna with intentionally broken forge path |
| Receipt verification on-chain | DEP-05 | Requires live deployment | Verify cast receipt returns 0x1 after real deploy |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
