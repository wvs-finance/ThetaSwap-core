# Submodule & Build Optimization for Judge/Cloner Readiness

**Date:** 2026-03-19
**Branch:** 008-uniswap-v3-reactive-integration
**Goal:** Reduce recursive submodule count from ~95 to <25 and speed up test compilation 3-10x, while guaranteeing build + test integrity at every step.

## Context

Research analyzed Uniswap V4 core (3 submodules, zero nesting), v4-periphery (2 submodules, `compilation_restrictions`), OpenZeppelin, and Seaport. Our repo has 10 top-level submodules that expand to 95+ recursive checkouts across 8 nesting levels. forge-std is duplicated 15+ times, v4-core 8+ times. Reports at `tmp/our-submodule-analysis.md` and `tmp/submodule-optimization-research.md`.

## Non-Negotiable Verification Protocol

Every single change gets a 3-gate verification before proceeding:

### Gate 1 — Local build + test
```bash
forge build
forge test --match-path "test/fci-token-vault/**" -vv
forge test --match-path "test/fee-concentration-index-v2/**" -vv
```

### Gate 2 — Worktree fresh-clone simulation
```bash
git worktree add /tmp/theta-verify-<step> HEAD
cd /tmp/theta-verify-<step>
git submodule update --init --recursive
forge build
forge test --match-path "test/fci-token-vault/**" -vv
forge test --match-path "test/fee-concentration-index-v2/**" -vv
git worktree remove /tmp/theta-verify-<step>
```

### Gate 3 — Docker end-to-end (final only, after all changes)
Mirrors `.github/workflows/test.yml` exactly:
- `ubuntu:latest` base, install Foundry via `foundryup`
- `git clone --recursive <repo>`
- `FOUNDRY_PROFILE=lite forge build`
- Tests under `FOUNDRY_PROFILE=ci` (matches CI's `ffi = false`, `force = true`):
  - `forge test --match-path "test/fci-token-vault/**" -vv`
  - `forge test --match-path "test/fee-concentration-index-v2/**" -vv --no-match-test "test_integrationNativeV4_unit_equalCapitalDurationHeterogeneousLps_twoSwaps_deltaPlusMustBeZero|test_integrationNativeV4_unit_twoHeteroCapitalPartialExit_registryHasActivePosition"`
- Python research tests: `pytest research/tests/ -v`

Note: CI uses `foundry-rs/foundry-toolchain@v1` which may install a different Foundry version than `foundryup`. The Docker test validates clone + build + test flow; exact Foundry version parity is ensured by CI itself.

### Rollback policy
If any gate fails at any step, revert that specific commit immediately. Do not proceed. Investigate root cause before retrying.

Changes are committed one at a time — each step is an atomic, revertible commit.

## Phase A — Zero-Risk Removals (no code changes)

### A1: Remove `lib/bunni-v2` directory
- Not in `.gitmodules`, zero imports anywhere
- First verify tracking status: `git ls-files lib/bunni-v2`. If tracked, use `git rm -rf lib/bunni-v2`. If untracked, `rm -rf lib/bunni-v2` (won't appear in fresh clones anyway, but clean up disk).
- Eliminates ~30 recursive submodule checkouts

### A2: Remove top-level `lib/v4-periphery` submodule
- Shadowed by the copy inside `lib/uniswap-hooks/lib/v4-periphery/`
- `remappings.txt` already points to the nested copy for most paths
- **Must also update `foundry.toml`**: lines declaring `permit2/=lib/v4-periphery/lib/permit2/` and `solmate/=lib/v4-periphery/lib/solmate/` become dangling after removal. Update these to point to `lib/uniswap-hooks/lib/v4-periphery/lib/permit2/` and `lib/uniswap-hooks/lib/v4-core/lib/solmate/` respectively (or remove them from `foundry.toml` since `remappings.txt` already has the correct paths).
- `git rm lib/v4-periphery`, update `.gitmodules`
- Eliminates ~10 recursive submodule checkouts

### A3: Clean 8 phantom remappings from `remappings.txt`
- These reference deleted submodules from earlier branches:
  - `@panoptic-v2/` → `lib/2025-12-panoptic/` (doesn't exist)
  - `@bunni-v2/` → `lib/bunni-v2/src/` (doesn't exist)
  - `kontrol-cheatcodes/` → `lib/kontrol-cheatcodes/src/` (doesn't exist)
  - `@hook-bazaar/master-hook/` → `lib/hook-bazaar/contracts/src/master-hook-pkg/` (doesn't exist)
  - `@hook-bazaar/` → `lib/hook-bazaar/contracts/src/` (doesn't exist)
  - `Compose/` → `lib/Compose/src/` (doesn't exist)
  - `compose-extensions/` → `lib/compose-extensions/src/` (doesn't exist)
  - `@uniswap/v3-periphery/` → `lib/v3-periphery/` (doesn't exist)
- `remappings.txt` only, no build impact

## Phase B — Submodule Consolidation (config changes)

### B1: Point `@openzeppelin/contracts/` to nested copy, remove top-level
- Only `EnumerableSet` is used (1 import in `src/`, 0 in `test/`)
- `remappings.txt` already points to the nested copy (`lib/uniswap-hooks/lib/openzeppelin-contracts/contracts/`)
- **Must also update `foundry.toml`**: the entry `@openzeppelin/contracts/=lib/openzeppelin-contracts/contracts/` points to the top-level copy. Either update it to match `remappings.txt` or remove it from `foundry.toml` (since `remappings.txt` already has the correct path).
- Remove `lib/openzeppelin-contracts` from `.gitmodules`, `git rm` it
- Eliminates ~3 recursive submodule checkouts

### B2: Fix `typed-uniswap-v4` self-nesting
- `lib/typed-uniswap-v4/lib/typed-uniswap-v4/` contains a copy of itself
- Fix in upstream repo (`wvs-finance/typed-uniswap-v4`): remove the self-referencing submodule entry from its `.gitmodules`
- Push upstream, then update pinned commit in this repo
- Eliminates ~15 recursive submodule checkouts

### B3: Add `shallow = true` to all `.gitmodules` entries
- Low risk, protects against naive `git clone --recursive` pulling full history
- Note: `shallow = true` is respected by `git submodule update --init` but may be ignored by some CI environments (e.g., `actions/checkout` with `submodules: recursive` depending on git version). Not harmful in those cases, just ineffective.
- `.gitmodules` only

## Phase C — Solidity-Touching Changes (user reviews code piece-by-piece)

### C1: Vendor `CalldataReader.sol` from angstrom
- The entire angstrom submodule (full Rust workspace + 7 nested Solidity submodules) exists for one type: `CalldataReader`
- Copy `CalldataReader.sol` into `src/types/CalldataReader.sol`, preserving original filename and structure
- Add attribution comment at top: copied from `SorellaLabs/angstrom`
- Update 3 import paths in `src/` to point to local copy
- Remove `lib/angstrom` from `.gitmodules`, `git rm` it
- Remove `angstrom/=lib/angstrom/contracts/` from `foundry.toml` (the actually-used remapping)
- Remove `@angstrom/=lib/angstrom/contracts/src/` from `remappings.txt`
- Eliminates ~15 recursive submodule checkouts

## Phase D — Build Optimizations (foundry.toml)

### D1: Add `compilation_restrictions`
Following the Uniswap v4-periphery pattern:
```toml
compilation_restrictions = [
  { paths = "test/**", via_ir = false },
  { paths = "foundry-script/**", via_ir = false }
]
```
Tests and scripts compile without IR pipeline (3-10x faster). Production `src/` contracts keep `via_ir = true`.

### D2: Add `[profile.debug]`
```toml
[profile.debug]
via_ir = false
optimizer_runs = 200
fuzz.runs = 50
```
For quick single-test debugging.

### D3: Consolidate remapping sources
Both `remappings.txt` and `foundry.toml` declare remappings with conflicts for `permit2/`, `solmate/`, `@openzeppelin/contracts/`. `remappings.txt` has the correct paths (pointing to nested copies); `foundry.toml` has stale paths (pointing to top-level submodules removed in A2/B1). Resolution: remove the conflicting entries from `foundry.toml`, keeping `remappings.txt` as canonical for those mappings.

**Ordering dependency:** D3 cleans up stale `foundry.toml` entries that A2 and B1 should have already addressed. If A2/B1 fully clean their `foundry.toml` entries, D3 becomes a verification pass. If not, D3 catches any remaining conflicts.

## Phase E — Final Validation

### E1: Docker end-to-end
Docker container mirrors CI exactly:
- `git clone --recursive` from origin
- `FOUNDRY_PROFILE=lite forge build`
- Full test suite
- Python research tests

### E2: Measure before/after
| Metric | Before | After | How to measure |
|--------|--------|-------|---------------|
| Recursive submodule count | ~95 | <25 | `find lib -name .gitmodules \| wc -l` |
| `git clone --recursive` time | baseline | <50% of baseline | timed in Docker |
| `forge build` time (lite) | baseline | same or faster | timed locally |
| `forge test` time | baseline | 30-50% faster | timed locally |

## Success Criteria

- All vault tests pass (`test/fci-token-vault/**`)
- All FCI V2 tests pass (`test/fee-concentration-index-v2/**`)
- `forge build` compiles with zero errors
- Worktree fresh-submodule-init succeeds at every step
- No import resolution errors
- Docker final validation matches CI behavior
- Recursive submodule count < 25
- Clone time reduced by at least 50%

## Out of Scope

- No import refactoring beyond what's needed for vendored files and remapping changes
- No Solidity code changes except the CalldataReader vendoring (C1)
- No CI workflow changes — Docker validates against current CI
- No soldeer/npm migration
- No uniswap-hooks consolidation (longer-term, separate spec)
- No changes to `lib/` submodule code (standing rule: never modify lib/)
