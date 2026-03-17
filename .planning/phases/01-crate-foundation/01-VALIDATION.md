---
phase: 1
slug: crate-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | cargo test (Rust built-in) |
| **Config file** | `d2p/Cargo.toml` — Wave 0 creates |
| **Quick run command** | `cd d2p && cargo check` |
| **Full suite command** | `cd d2p && cargo test` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd d2p && cargo check`
- **After every plan wave:** Run `cd d2p && cargo test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | SET-01 | build | `cd d2p && cargo check` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | SET-02 | build | `cd d2p && cargo check` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | SET-03 | unit | `cd d2p && cargo test` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `d2p/Cargo.toml` — crate manifest with all 4 dependencies
- [ ] `d2p/src/main.rs` — minimal main entry point
- [ ] Rust toolchain available on PATH

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Module structure inspection | SET-03 | Verify distinct files exist for errors, params, output | `ls d2p/src/errors.rs d2p/src/deploy/mod.rs` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
