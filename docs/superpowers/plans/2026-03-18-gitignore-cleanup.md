# Gitignore Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove noise from the tracked repo so judges and developers cloning see a clean, professional project.

**Architecture:** Edit `.gitignore` (remove stale rules, add new patterns), then `git rm --cached` 7 files that are currently tracked but shouldn't be. Single commit.

**Tech Stack:** git

**Spec:** `docs/superpowers/specs/2026-03-18-gitignore-cleanup-design.md`

---

### Task 1: Update `.gitignore`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Remove stale `docs/` ignore rule**

Remove line 11 (`docs/`) and its comment on line 10 (`# Docs`). This rule blocks new files under `docs/` from being tracked, which is wrong since `docs/` has 102 tracked files.

Before:
```gitignore
# Docs
docs/
```

After: (lines deleted)

- [ ] **Step 2: Remove `!research/**/*.log` exception**

Remove line 116 (`!research/**/*.log`). This lets LaTeX `.log` files through. Without this exception, the existing global `*.log` pattern (line 111) catches them.

Before:
```gitignore
!research/**/*.log
```

After: (line deleted)

- [ ] **Step 3: Add new gitignore entries at the end of the file**

Append these entries after the existing `out-sol/` line at the end of `.gitignore`:

```gitignore

# Personal scratch
notes/

# LaTeX .vrb artifacts
*.vrb

# Stray venvs
list/
```

- [ ] **Step 4: Verify the gitignore changes**

Run: `git diff .gitignore`

Expected: 3 lines removed (`# Docs`, `docs/`, `!research/**/*.log`), 7 lines added (new patterns).

---

### Task 2: Untrack noisy files (`git rm --cached`)

**Files:**
- Untrack: `notes/SCRATCH.md`, `notes/SCRATCH.md~`, `docs/usage.md~`, `specs/notes/DRAFT.md~`, `specs/notes/DraftEntryIndex.md~`, `research/model/main.log`, `research/slides/presentation.log`

- [ ] **Step 1: Remove files from git tracking (keep on disk)**

```bash
git rm --cached \
  notes/SCRATCH.md \
  "notes/SCRATCH.md~" \
  "docs/usage.md~" \
  "specs/notes/DRAFT.md~" \
  "specs/notes/DraftEntryIndex.md~" \
  research/model/main.log \
  research/slides/presentation.log
```

- [ ] **Step 2: Verify files are untracked but still on disk**

```bash
git status
```

Expected: 7 files show as "deleted" in staged changes (removed from index). The `.gitignore` changes show as modified.

```bash
ls notes/SCRATCH.md research/model/main.log
```

Expected: Files still exist on disk.

---

### Task 3: Commit

- [ ] **Step 1: Review staged changes**

```bash
git diff --cached --stat
```

Expected: `.gitignore` modified, 7 files deleted from index.

- [ ] **Step 2: Commit**

```bash
git commit -m "chore: clean gitignore for judge/cloner readiness

- Remove stale docs/ ignore rule that blocked new docs from tracking
- Remove !research/**/*.log exception (LaTeX logs now ignored)
- Add ignore patterns: notes/, *.vrb, list/
- Untrack 7 noisy files (backup files, LaTeX build artifacts)
- Files remain on disk, only removed from git tracking"
```

- [ ] **Step 3: Verify clean state**

```bash
git log --oneline -1
git status
```

Expected: Clean working tree (the untracked files are now covered by gitignore patterns).
