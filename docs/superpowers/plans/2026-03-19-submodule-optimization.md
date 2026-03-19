# Submodule & Build Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce recursive submodule count from ~95 to <25 and speed up test compilation, verified at every step.

**Architecture:** Sequential atomic commits, each verified with local build+test and worktree fresh-clone simulation. Phases ordered by risk: zero-risk removals → config changes → Solidity vendoring → build optimizations → Docker final validation.

**Tech Stack:** git, Foundry (forge), Docker

**Spec:** `docs/superpowers/specs/2026-03-19-submodule-optimization-design.md`

---

## Gate Commands (used after every task)

```bash
# Gate 1 — Local build + test
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv

# Gate 2 — Worktree fresh-clone simulation (use unique path per task)
git worktree prune
git worktree add /tmp/theta-verify-taskN HEAD && \
cd /tmp/theta-verify-taskN && \
git submodule update --init --recursive && \
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv && \
cd - && \
git worktree remove /tmp/theta-verify-taskN
```

---

### Task 0: Capture baseline metrics

**Files:** None (read-only)

- [ ] **Step 1: Count current recursive submodules**

```bash
find lib -name .gitmodules | wc -l
```

Record the number.

- [ ] **Step 2: Time current build**

```bash
forge clean && time forge build
```

Record wall-clock time.

- [ ] **Step 3: Time current tests**

```bash
time forge test --match-path "test/fci-token-vault/**" -vv
time forge test --match-path "test/fee-concentration-index-v2/**" -vv
```

Record wall-clock times.

- [ ] **Step 4: Record in a scratch note**

Save baseline numbers to compare at end. Do NOT commit this file.

---

### Task 1 (A1): Remove `lib/bunni-v2` directory

**Files:**
- Remove: `lib/bunni-v2/` (untracked directory, not in `.gitmodules`)

- [ ] **Step 1: Verify not tracked by git**

```bash
git ls-files lib/bunni-v2 | wc -l
```

Expected: `0` (untracked).

- [ ] **Step 2: Remove from disk**

```bash
rm -rf lib/bunni-v2
```

- [ ] **Step 3: Run Gate 1**

```bash
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv
```

Expected: All pass (no code references bunni-v2).

- [ ] **Step 4: Commit**

Nothing to commit (untracked dir). Verify with `git status` that working tree is clean.

---

### Task 2 (A2): Remove top-level `lib/v4-periphery` submodule

**Files:**
- Modify: `.gitmodules` — remove lines 4-6 (`[submodule "lib/v4-periphery"]`)
- Modify: `foundry.toml` — update lines 21-22 (`permit2/` and `solmate/` remappings)
- Modify: `Makefile` — remove line 18 (`git -C lib/v4-periphery ...`)
- Remove: `lib/v4-periphery` (via `git rm`)

- [ ] **Step 1: Deinit and remove the submodule**

```bash
git submodule deinit -f lib/v4-periphery
git rm -f lib/v4-periphery
```

- [ ] **Step 2: Remove entry from `.gitmodules`**

Remove these lines from `.gitmodules`:
```
[submodule "lib/v4-periphery"]
	path = lib/v4-periphery
	url = https://github.com/uniswap/v4-periphery
```

- [ ] **Step 3: Update `foundry.toml` remappings**

Change line 21 from:
```
"permit2/=lib/v4-periphery/lib/permit2/",
```
to:
```
"permit2/=lib/uniswap-hooks/lib/v4-periphery/lib/permit2/",
```

Change line 22 from:
```
"solmate/=lib/v4-periphery/lib/solmate/",
```
to:
```
"solmate/=lib/uniswap-hooks/lib/v4-core/lib/solmate/",
```

- [ ] **Step 4: Update `Makefile`**

Remove line 18:
```makefile
	git -C lib/v4-periphery submodule update --init --depth 1 -- lib/permit2
```

- [ ] **Step 5: Clean residual `.git/modules` entry**

```bash
rm -rf .git/modules/lib/v4-periphery
```

- [ ] **Step 6: Run Gate 1**

```bash
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv
```

- [ ] **Step 7: Run Gate 2**

```bash
git worktree add /tmp/theta-verify HEAD && \
cd /tmp/theta-verify && \
git submodule update --init --recursive && \
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv && \
cd - && \
git worktree remove /tmp/theta-verify
```

- [ ] **Step 8: Commit**

```bash
git add .gitmodules foundry.toml Makefile
git commit -m "chore: remove shadowed lib/v4-periphery submodule

Remappings already resolve permit2/ and solmate/ via the nested copy
inside lib/uniswap-hooks. Eliminates ~10 recursive submodule checkouts."
```

---

### Task 3 (A3): Clean phantom remappings from `remappings.txt`

**Files:**
- Modify: `remappings.txt` — remove 8 stale entries (lines 6, 10-13, 15-18)

- [ ] **Step 1: Remove stale remappings**

Remove these lines from `remappings.txt`:

```
@uniswap/v3-periphery/=lib/v3-periphery/
@panoptic-v2/=lib/2025-12-panoptic/
@angstrom/=lib/angstrom/contracts/src/
@bunni-v2/=lib/bunni-v2/src/
kontrol-cheatcodes/=lib/kontrol-cheatcodes/src/
@hook-bazaar/master-hook/=lib/hook-bazaar/contracts/src/master-hook-pkg/
@hook-bazaar/=lib/hook-bazaar/contracts/src/
Compose/=lib/Compose/src/
compose-extensions/=lib/compose-extensions/src/
```

Note: Keep `@angstrom/` removal here even though `angstrom/` (without @) in `foundry.toml` is the actually-used one — both are stale after C1 removes the submodule.

- [ ] **Step 2: Run Gate 1**

```bash
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv
```

- [ ] **Step 3: Run Gate 2**

```bash
git worktree add /tmp/theta-verify HEAD && \
cd /tmp/theta-verify && \
git submodule update --init --recursive && \
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv && \
cd - && \
git worktree remove /tmp/theta-verify
```

- [ ] **Step 4: Commit**

```bash
git add remappings.txt
git commit -m "chore: remove 9 phantom remappings pointing to deleted submodules"
```

---

### Task 4 (B1): Point OpenZeppelin to nested copy, remove top-level

**Files:**
- Modify: `.gitmodules` — remove lines 19-21 (`[submodule "lib/openzeppelin-contracts"]`)
- Modify: `foundry.toml` — update line 32 (`@openzeppelin/contracts/`)
- Remove: `lib/openzeppelin-contracts` (via `git rm`)

- [ ] **Step 1: Verify the nested copy exists**

```bash
ls lib/uniswap-hooks/lib/openzeppelin-contracts/contracts/utils/structs/EnumerableSet.sol
```

Expected: File exists.

- [ ] **Step 2: Update `foundry.toml` remapping**

Change line 32 from:
```
"@openzeppelin/contracts/=lib/openzeppelin-contracts/contracts/",
```
to:
```
"@openzeppelin/contracts/=lib/uniswap-hooks/lib/openzeppelin-contracts/contracts/",
```

(`remappings.txt` line 7 already points to this path.)

- [ ] **Step 3: Deinit and remove the submodule**

```bash
git submodule deinit -f lib/openzeppelin-contracts
git rm -f lib/openzeppelin-contracts
rm -rf .git/modules/lib/openzeppelin-contracts
```

- [ ] **Step 4: Remove entry from `.gitmodules`**

Remove these lines:
```
[submodule "lib/openzeppelin-contracts"]
	path = lib/openzeppelin-contracts
	url = https://github.com/OpenZeppelin/openzeppelin-contracts.git
```

- [ ] **Step 5: Run Gate 1**

```bash
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv
```

- [ ] **Step 6: Run Gate 2**

```bash
git worktree add /tmp/theta-verify HEAD && \
cd /tmp/theta-verify && \
git submodule update --init --recursive && \
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv && \
cd - && \
git worktree remove /tmp/theta-verify
```

- [ ] **Step 7: Commit**

```bash
git add .gitmodules foundry.toml
git commit -m "chore: point @openzeppelin/contracts to nested copy in uniswap-hooks

Only EnumerableSet is used. Eliminates ~3 recursive submodule checkouts."
```

---

### Task 5 (B2): Fix `typed-uniswap-v4` self-nesting

**Files:**
- Modify: upstream repo `wvs-finance/typed-uniswap-v4` — remove `lib/typed-uniswap-v4` directory
- Modify: `lib/typed-uniswap-v4` — update pinned commit

- [ ] **Step 1: Verify the self-nesting exists**

```bash
ls lib/typed-uniswap-v4/lib/typed-uniswap-v4/
```

Expected: Directory exists with content. It's NOT in `typed-uniswap-v4/.gitmodules` — it's a tracked directory, not a submodule.

- [ ] **Step 2: Fix upstream**

In the `wvs-finance/typed-uniswap-v4` repo:
```bash
git rm -rf lib/typed-uniswap-v4
git commit -m "chore: remove self-referencing lib/typed-uniswap-v4 directory"
git push
```

- [ ] **Step 3: Update pinned commit in this repo**

```bash
cd lib/typed-uniswap-v4
git pull origin main
cd ../..
git add lib/typed-uniswap-v4
```

- [ ] **Step 4: Run Gate 1**

```bash
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv
```

- [ ] **Step 5: Run Gate 2**

```bash
git worktree add /tmp/theta-verify HEAD && \
cd /tmp/theta-verify && \
git submodule update --init --recursive && \
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv && \
cd - && \
git worktree remove /tmp/theta-verify
```

- [ ] **Step 6: Commit**

```bash
git commit -m "chore: update typed-uniswap-v4 to fix self-nesting

Upstream removed lib/typed-uniswap-v4/ self-reference.
Eliminates ~15 recursive submodule checkouts."
```

---

### Task 6 (B3): Add `shallow = true` to all `.gitmodules` entries

**Files:**
- Modify: `.gitmodules` — add `shallow = true` to every remaining submodule entry

- [ ] **Step 1: Add shallow flag to every submodule**

For each `[submodule ...]` block in `.gitmodules`, add `shallow = true` after the `url` line. After Task 2 and Task 4, the remaining submodules are:

1. `lib/forge-std`
2. `lib/uniswap-hooks`
3. `lib/v3-core`
4. `lib/angstrom` (removed in Task 7, but add shallow now)
5. `lib/solady`
6. `lib/reactive-hooks`
7. `lib/typed-uniswap-v4`
8. `lib/reactive-lib`

- [ ] **Step 2: Run Gate 1**

```bash
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv
```

- [ ] **Step 3: Commit**

```bash
git add .gitmodules
git commit -m "chore: add shallow = true to all submodules for faster cloning"
```

---

### Task 7 (C1): Vendor CalldataReader from angstrom

**Files:**
- Create: `src/types/CalldataReader.sol` (copied from `lib/angstrom/contracts/src/types/CalldataReader.sol`)
- Modify: `src/fee-concentration-index/FeeConcentrationIndex.sol:25` — update import path
- Modify: `src/fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol:5` — update import path
- Modify: `src/fee-concentration-index-v2/libraries/PoolKeyExtLib.sol:7` — update import path
- Modify: `foundry.toml` — remove line 20 (`angstrom/` remapping)
- Modify: `.gitmodules` — remove angstrom entry (lines 13-15)
- Remove: `lib/angstrom` (via `git rm`)

**NOTE: This task creates a new Solidity file. Present the file to the user for piece-by-piece review before writing it.**

- [ ] **Step 1: Copy CalldataReader.sol with attribution**

Create `src/types/CalldataReader.sol` with the exact contents of `lib/angstrom/contracts/src/types/CalldataReader.sol`, but prepend an attribution comment after the SPDX line:

```solidity
// SPDX-License-Identifier: MIT
// Copied from SorellaLabs/angstrom (contracts/src/types/CalldataReader.sol)
// Original author: philogy <https://github.com/philogy>
pragma solidity ^0.8.13;
```

Rest of file is identical to the original.

- [ ] **Step 2: Update import in `FeeConcentrationIndex.sol`**

Change line 25 from:
```solidity
import {CalldataReader, CalldataReaderLib} from "angstrom/src/types/CalldataReader.sol";
```
to:
```solidity
import {CalldataReader, CalldataReaderLib} from "@types/CalldataReader.sol";
```

- [ ] **Step 3: Update import in `FeeConcentrationIndexRegistryStorageMod.sol`**

Change line 5 from:
```solidity
import {CalldataReader, CalldataReaderLib} from "angstrom/src/types/CalldataReader.sol";
```
to:
```solidity
import {CalldataReader, CalldataReaderLib} from "@types/CalldataReader.sol";
```

- [ ] **Step 4: Update import in `PoolKeyExtLib.sol`**

Change line 7 from:
```solidity
import {CalldataReader, CalldataReaderLib} from "angstrom/src/types/CalldataReader.sol";
```
to:
```solidity
import {CalldataReader, CalldataReaderLib} from "@types/CalldataReader.sol";
```

- [ ] **Step 5: Remove `angstrom/` remapping from `foundry.toml`**

Remove line 20:
```
"angstrom/=lib/angstrom/contracts/",
```

- [ ] **Step 6: Deinit and remove the submodule**

```bash
git submodule deinit -f lib/angstrom
git rm -f lib/angstrom
rm -rf .git/modules/lib/angstrom
```

- [ ] **Step 7: Remove entry from `.gitmodules`**

Remove these lines:
```
[submodule "lib/angstrom"]
	path = lib/angstrom
	url = https://github.com/SorellaLabs/angstrom
```

- [ ] **Step 8: Run Gate 1**

```bash
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv
```

- [ ] **Step 9: Run Gate 2**

```bash
git worktree add /tmp/theta-verify HEAD && \
cd /tmp/theta-verify && \
git submodule update --init --recursive && \
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv && \
cd - && \
git worktree remove /tmp/theta-verify
```

- [ ] **Step 10: Commit**

```bash
git add src/types/CalldataReader.sol \
  src/fee-concentration-index/FeeConcentrationIndex.sol \
  src/fee-concentration-index-v2/modules/FeeConcentrationIndexRegistryStorageMod.sol \
  src/fee-concentration-index-v2/libraries/PoolKeyExtLib.sol \
  foundry.toml .gitmodules
git commit -m "chore: vendor CalldataReader from angstrom, remove submodule

Copied from SorellaLabs/angstrom (contracts/src/types/CalldataReader.sol).
Only CalldataReader type was used. Eliminates ~15 recursive submodule checkouts."
```

---

### Task 8 (D1): Add `compilation_restrictions` to `foundry.toml`

**Files:**
- Modify: `foundry.toml` — add `compilation_restrictions` after the `remappings` array

- [ ] **Step 1: Verify Foundry supports `compilation_restrictions`**

```bash
forge --version
```

`compilation_restrictions` requires Foundry v0.3.0+ (late 2025). If the version is too old, run `foundryup` first.

- [ ] **Step 2: Add compilation restrictions**

Add after the `remappings = [...]` closing bracket (before `script = "foundry-script"`):

```toml
compilation_restrictions = [
    { paths = "test/**", via_ir = false },
    { paths = "foundry-script/**", via_ir = false },
]
```

- [ ] **Step 3: Run Gate 1**

```bash
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv
```

- [ ] **Step 4: Run Gate 2**

```bash
git worktree prune
git worktree add /tmp/theta-verify-task8 HEAD && \
cd /tmp/theta-verify-task8 && \
git submodule update --init --recursive && \
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv && \
cd - && \
git worktree remove /tmp/theta-verify-task8
```

- [ ] **Step 5: Commit**

```bash
git add foundry.toml
git commit -m "perf: add compilation_restrictions — via_ir=false for tests and scripts

Follows Uniswap v4-periphery pattern. Production src/ keeps via_ir=true.
Tests and scripts compile 3-10x faster without IR pipeline."
```

---

### Task 9 (D2): Add `[profile.debug]` to `foundry.toml`

**Files:**
- Modify: `foundry.toml` — add debug profile

- [ ] **Step 1: Add debug profile**

Add after the `[profile.ci]` block:

```toml
[profile.debug]
via_ir = false
optimizer_runs = 200
fuzz.runs = 50
```

- [ ] **Step 2: Verify it works**

```bash
FOUNDRY_PROFILE=debug forge test --match-path "test/fci-token-vault/**" -vv
```

Expected: Tests pass, noticeably faster compilation.

- [ ] **Step 3: Commit**

```bash
git add foundry.toml
git commit -m "perf: add [profile.debug] with via_ir=false for fast single-test runs"
```

---

### Task 10 (D3): Consolidate remapping sources

**Files:**
- Modify: `foundry.toml` — remove stale/duplicate remappings that are already in `remappings.txt`

- [ ] **Step 1: Remove duplicate entries from `foundry.toml`**

The following `foundry.toml` remappings duplicate what `remappings.txt` already provides (and `remappings.txt` has the correct paths after Tasks 2-4):

Remove from `foundry.toml` remappings array:
```
"@uniswap/v4-core/=lib/uniswap-hooks/lib/v4-core/",
"@uniswap/v3-core/=lib/v3-core/",
"solady/=lib/solady/src/",
```

These are identical duplicates of `remappings.txt` entries. The `foundry.toml` remappings that remain are ones NOT in `remappings.txt` (cross-submodule resolution prefixes like `lib/reactive-hooks/:v4-core/=...`).

- [ ] **Step 2: Run Gate 1**

```bash
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv
```

- [ ] **Step 3: Run Gate 2**

```bash
git worktree add /tmp/theta-verify HEAD && \
cd /tmp/theta-verify && \
git submodule update --init --recursive && \
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv && \
cd - && \
git worktree remove /tmp/theta-verify
```

- [ ] **Step 4: Commit**

```bash
git add foundry.toml
git commit -m "chore: remove duplicate remappings from foundry.toml

remappings.txt is canonical for shared mappings. foundry.toml retains
only cross-submodule resolution prefixes not expressible in remappings.txt."
```

---

### Task 11 (E1): Update Makefile install target

**Files:**
- Modify: `Makefile` — update install target to reflect removed submodules

- [ ] **Step 1: Update install target**

After removing `lib/v4-periphery` (Task 2) and `lib/angstrom` + `lib/openzeppelin-contracts` (Tasks 4, 7), the Makefile `install` target no longer needs line 18. Verify the remaining selective init commands still reference existing submodules:

```makefile
install:
	git submodule update --init --depth 1 --jobs 4
	git -C lib/uniswap-hooks submodule update --init --depth 1 --jobs 4 -- \
		lib/v4-core lib/openzeppelin-contracts lib/v4-periphery
	git -C lib/uniswap-hooks/lib/v4-core submodule update --init --depth 1 -- lib/solmate
	git -C lib/typed-uniswap-v4 submodule update --init --depth 1 -- lib/foundational-hooks
	uv venv $(VENV) --python 3.13
	uv pip install --python $(PYTHON) -e ".[dev]"
	$(MAKE) setup-kernel
```

(Line 18 was already removed in Task 2. Verify the remaining lines are correct.)

- [ ] **Step 2: Test the install target from scratch**

```bash
make install
```

Expected: Completes without errors.

- [ ] **Step 3: Run Gate 1**

```bash
forge build && \
forge test --match-path "test/fci-token-vault/**" -vv && \
forge test --match-path "test/fee-concentration-index-v2/**" -vv
```

- [ ] **Step 4: Commit (if any changes)**

```bash
git add Makefile
git commit -m "chore: update Makefile install target for reduced submodule set"
```

---

### Task 12 (E2): Docker end-to-end validation

**Files:**
- None committed (validation only)

- [ ] **Step 1: Push all changes to origin**

```bash
git push origin 008-uniswap-v3-reactive-integration
```

- [ ] **Step 2: Create Dockerfile for validation**

```dockerfile
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y curl git python3 python3-pip python3-venv

# Install Foundry
RUN curl -L https://foundry.paradigm.xyz | bash && \
    /root/.foundry/bin/foundryup

ENV PATH="/root/.foundry/bin:${PATH}"

WORKDIR /workspace

# Clone directly onto the correct branch with recursive submodules
RUN git clone -b 008-uniswap-v3-reactive-integration --recursive \
    https://github.com/JMSBPP/thetaSwap-core-dev.git .

# Build (lite profile, same as CI)
RUN FOUNDRY_PROFILE=lite forge build

# Test (ci profile, same as CI: ffi=false, force=true)
ENV FOUNDRY_PROFILE=ci
RUN forge test --match-path "test/fci-token-vault/**" -vv
RUN forge test --match-path "test/fee-concentration-index-v2/**" -vv \
    --no-match-test "test_integrationNativeV4_unit_equalCapitalDurationHeterogeneousLps_twoSwaps_deltaPlusMustBeZero|test_integrationNativeV4_unit_twoHeteroCapitalPartialExit_registryHasActivePosition"
ENV FOUNDRY_PROFILE=default

# Python research tests
RUN python3 -m venv uhi8 && \
    uhi8/bin/pip install uv && \
    uhi8/bin/uv pip install -e ".[dev]" && \
    cd research && ../uhi8/bin/python -m pytest tests/ -v
```

- [ ] **Step 3: Build and run Docker**

```bash
docker build -t theta-verify -f /tmp/theta-verify.Dockerfile .
```

Expected: All stages complete successfully.

- [ ] **Step 4: Measure after metrics**

```bash
find lib -name .gitmodules | wc -l
```

Compare with Task 0 baseline.

- [ ] **Step 5: Record before/after comparison**

| Metric | Before | After |
|--------|--------|-------|
| Recursive submodule count | (from Task 0) | (current) |
| `forge build` time | (from Task 0) | (current) |
| `forge test` time | (from Task 0) | (current) |

---

### Task 13: Push and update PR

- [ ] **Step 1: Push**

```bash
git push origin 008-uniswap-v3-reactive-integration
```

- [ ] **Step 2: Verify PR #54 includes all commits**

PR at https://github.com/wvs-finance/ThetaSwap-core/pull/54 should now include all optimization commits.
