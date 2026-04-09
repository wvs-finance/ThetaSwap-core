# Exact Next Steps After All Tests Pass (Phase 2, 02-implement.md)

Starting state: Implementation complete, `forge test` green, `bulloak check` passes.

## Step-by-step, in order:

### 1. Verify Spec-Code Sync (Step 5)

Run `bulloak check <path-to-tree-file>` to confirm the BTT tree and the test file are in sync. If mismatches are reported (missing test functions, extra test functions, modifier mismatches), fix them before proceeding.

### 2. Full Green Verification (Step 6)

Run `forge test` across the entire project -- not just the tests for this function. No regressions allowed.

### 3. Dual-Agent Review Gate (Step 7)

Launch **two background review agents in parallel**, scoped to ONLY the files implemented or modified in this phase. The skill is explicit: "Do not proceed to the exit gate until both return clean."

**Agent 1 -- Code Reviewer** (`subagent_type: "Code Reviewer"`):
- Verifies implementation matches BTT spec (pass/fail per tree branch)
- Checks edge cases: off-by-one in searches, missing branches, signature mismatches
- Flags NatSpec gaps on safety-critical functions

**Agent 2 -- Blockchain Security Auditor** (`subagent_type: "Blockchain Security Auditor"`):
- Audits for oracle manipulation, truncation safety, access control
- Checks unchecked arithmetic for silent wraparound on ALL code paths (not just happy path -- "guard/skip paths that cast before SafeCast are a known vector")
- Verifies monotonicity invariants under adversarial inputs

Both agent prompts MUST include: `"Review ONLY these files: [list]. Do NOT review, comment on, or modify any other files."`

Reports are written to:
- `.scratch/code-review-<name>.md`
- `.scratch/security-audit-<name>.md`

**If either agent finds issues:** Fix the implementation, re-run `forge test`, re-launch BOTH agents. Iterate until both pass clean.

Quoting the skill directly on why this is mandatory:

> **Why this is not optional:** Tests verify specified behavior. They do NOT verify:
> - Silent truncation bypassing SafeCast on non-push code paths
> - Bit-packing cross-field contamination
> - Monotonicity guard bypass via unchecked downcasts
> - Oracle manipulation timing vectors
>
> All of these were found by review agents in practice and would have shipped undetected by tests alone.

### 4. Exit Gate Checklist

All of the following must be true:

- [ ] All BTT leaf tests pass (concrete tests)
- [ ] All fuzz tests pass (no counterexamples)
- [ ] All `invariant_` properties hold
- [ ] `forge test` fully green (no regressions across entire project)
- [ ] `bulloak check <tree-file>` confirms spec-code sync
- [ ] Any fuzz counterexamples found during implementation are pinned as regression tests
- [ ] Code Reviewer agent passes clean (no blockers)
- [ ] Security Auditor agent passes clean (no Critical or High findings)

### 5. Transition

Quoting the final line of the skill:

> Phase 2 complete. If kontrol is available, read `phases/03-verify.md`. Otherwise, skip to Phase 4 or feature complete.

So the next phase depends on tooling: if kontrol (formal verification) is available, proceed to Phase 3 (VERIFY / Prove). If not, skip to Phase 4 (VALIDATE SPECS / Meta-test) or declare the feature complete.
