# Baseline Test: Phase 02-implement -- Exact Next Steps After All Tests Pass

## Scenario

You have just finished implementing a Solidity library. All tests pass (`forge test` green), and `bulloak check` passes.

## Exact Next Steps, In Order

According to the skill file at `~/.claude/commands/evm-tdd/phases/02-implement.md`, the next steps after reaching full green are dictated by the **Exit Gate Checklist** and the **final line** of the phase.

### 1. Confirm every item on the Exit Gate Checklist (lines 109-117)

You must verify all six items:

> - [ ] All BTT leaf tests pass (concrete tests)
> - [ ] All fuzz tests pass (no counterexamples)
> - [ ] All `invariant_` properties hold
> - [ ] `forge test` fully green (no regressions across entire project)
> - [ ] `bulloak check <tree-file>` confirms spec-code sync
> - [ ] Any fuzz counterexamples found during implementation are pinned as regression tests

In this scenario these are already satisfied (all tests pass, bulloak check passes).

### 2. Proceed to the next phase as directed by line 118

The skill's final instruction is:

> "Phase 2 complete. If kontrol is available, read `phases/03-verify.md`. Otherwise, skip to Phase 4 or feature complete."

This means:

1. **Check whether kontrol (the K-framework formal verification tool) is available in the project.**
2. **If kontrol IS available**: proceed to **Phase 3: VERIFY (Prove)** -- read `phases/03-verify.md` and begin formal verification / symbolic execution of the implementation.
3. **If kontrol is NOT available**: skip Phase 3 entirely and proceed to **Phase 4: VALIDATE SPECS (Meta-test)**, or declare the feature complete.

## What the Skill Does NOT Say

- The skill does **not** mention launching sub-agents or parallel agents at any point in Phase 2.
- The skill does **not** mention committing code, creating PRs, or any git operations.
- The skill does **not** mention refactoring -- that is a separate Phase 5.
- The transition is a simple conditional branch: kontrol available -> Phase 3, otherwise -> Phase 4 or done.
