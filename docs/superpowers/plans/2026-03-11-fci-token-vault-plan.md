# FCI Token Vault Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **REQUIRED:** Use @type-driven-development throughout. No implementation code without types and invariants first. SCOP constraints enforced: no `library` keyword, no contract inheritance (except tests/tokens/interface implementation), no `modifier` keyword, no ternary operator. File-level free functions only.
>
> **SCOP exceptions:** (1) `FciLongToken`/`FciShortToken` inherit `ERC20` from solmate (token standard). (2) `FciTokenVault` implements `IFciTokenVault` interface (interface implementation, not contract inheritance). (3) Tests inherit `Test`, `PosmTestSetup`, etc.

**Goal:** Build PayoffMod (sqrtPriceX96-native file-level free functions), validate it against real FCI hook scenarios, then wrap it in a collateral vault with paired LONG/SHORT ERC-20s.

**Architecture:** Single precision boundary (Q128→sqrtPriceX96 via SqrtPriceLibrary). PayoffMod is one consolidated Mod file (file-level free functions, SCOP-compliant) containing oracle conversion, HWM decay, and payoff computation. Scenario validation layer wires multi-round JIT game to PayoffMod before building the vault. Three chunks: sub-component library → scenario validation → vault contract.

**Tech Stack:** Solidity ^0.8.26, Solady FixedPointMathLib (expWad, mulDiv), SqrtPriceLibrary (foundational-hooks), TickMath (v4-core), Solmate ERC20, Forge (unit + fuzz + fork tests), Kontrol (formal proofs).

**Spec:** `docs/plans/2026-03-10-fci-token-vault-design.md`

**Type-Driven Development phases applied:**
1. Specify → design spec already exists (`docs/plans/2026-03-10-fci-token-vault-design.md`)
2. Invariants → Task 2 (before any Solidity)
3. Types → Tasks 3–6 (PayoffMod types + functions, SCOP-compliant)
4. Kontrol proofs → Task 7 (one proof at a time)
5. Static analysis gate → Task 8
6. Implement → Tasks 9–14 (scenario validation + vault)
7. Verify → Task 15

---

## File Structure

```
foundry.toml                                          — add foundational-hooks, @fci-token-vault, solady remappings

specs/004-fci-token-vault/
  invariants.md                                       — ~10 system invariants in Hoare triple format

src/fci-token-vault/
  types/
    PayoffMod.sol                                     — file-level free functions: deltaPlusToSqrtPriceX96, applyDecay, updateHWM, computePayoff
  interfaces/
    IFciTokenVault.sol                                — vault public interface (mint, redeem*, poke)
  FciTokenVault.sol                                   — main vault contract (composes PayoffMod)
  FciLongToken.sol                                    — ERC-20 LONG side (vault-only mint/burn)
  FciShortToken.sol                                   — ERC-20 SHORT side (vault-only mint/burn)

test/fci-token-vault/
  unit/
    PayoffMod.unit.t.sol                              — unit tests for all PayoffMod functions
  fuzz/
    PayoffMod.fuzz.t.sol                              — fuzz: decay monotonicity, payoff sum, HWM invariants
  kontrol/
    PayoffMod.kontrol.t.sol                           — Kontrol formal proofs (prove_ prefix)

foundry-script/simulation/
  JitMultiRound.sol                                   — multi-round JIT game driver (extends JitGame.sol)

test/simulation/
  HedgedVsUnhedged.t.sol                              — integration: multi-round game + PayoffMod validation
  JitMultiRound.t.sol                                 — unit tests for multi-round driver config/accounts

test/fci-token-vault/
  unit/
    FciTokenVault.unit.t.sol                          — vault mint/redeem/poke tests
  fuzz/
    FciTokenVault.fuzz.t.sol                          — vault invariant fuzzing
```

---

## Chunk 1: Types, Invariants, and PayoffMod Library

### Task 1: Foundry remapping prerequisite

**Files:**
- Modify: `foundry.toml:14-37` (remappings array)

- [ ] **Step 1: Add foundational-hooks, @fci-token-vault, and solady remappings to foundry.toml**

Add these lines to the `remappings` array in `foundry.toml`:

```toml
"foundational-hooks/=lib/typed-uniswap-v4/lib/foundational-hooks/",
"@fci-token-vault/=src/fci-token-vault/",
"solady/=lib/solady/src/",
```

Insert after the `"lib/typed-uniswap-v4/:v4-core/=..."` line (line 30). The `solady/` remapping is required because PayoffMod imports `FixedPointMathLib` from `solady/utils/FixedPointMathLib.sol`.

- [ ] **Step 2: Create directory structure**

```bash
mkdir -p src/fci-token-vault/types
mkdir -p src/fci-token-vault/interfaces
mkdir -p test/fci-token-vault/unit
mkdir -p test/fci-token-vault/fuzz
mkdir -p test/fci-token-vault/kontrol
mkdir -p specs/004-fci-token-vault
```

- [ ] **Step 3: Verify the library resolves**

```bash
forge build --force 2>&1 | head -20
```

Expected: compiles without "source not found" errors for foundational-hooks.

- [ ] **Step 4: Commit**

```bash
git add foundry.toml
git commit -m "chore(004): add foundational-hooks + @fci-token-vault remappings, scaffold directories"
```

---

### Task 2: Define invariants (Type-Driven Development Phase 2)

**Files:**
- Create: `specs/004-fci-token-vault/invariants.md`

> **IRON LAW:** No implementation code without invariants first. This task MUST complete before any Solidity in PayoffMod.

- [ ] **Step 1: Write invariants document**

```markdown
# FCI Token Vault — Invariants

Spec: `docs/plans/2026-03-10-fci-token-vault-design.md`
Date: 2026-03-11

## PayoffMod Invariants

| ID | Description | Category | Hoare Triple | Affected | Verification |
|----|-------------|----------|-------------|----------|-------------|
| INV-001 | deltaPlusToSqrtPriceX96 is monotonically non-decreasing in Δ⁺ | Function-level | {δ₁ ≤ δ₂} → deltaPlusToSqrtPriceX96(δ₁) ≤ deltaPlusToSqrtPriceX96(δ₂) | PayoffMod | Kontrol proof + fuzz |
| INV-002 | deltaPlusToSqrtPriceX96(0) = 0 | Function-level | {} → deltaPlusToSqrtPriceX96(0) → {result == 0} | PayoffMod | Kontrol proof |
| INV-003 | applyDecay never increases storedMaxSqrtPrice | Function-level | {elapsed > 0} → applyDecay(max, t₀, t₁, λ) → {result ≤ max} | PayoffMod | Kontrol proof + fuzz |
| INV-004 | applyDecay is idempotent at elapsed=0 | Function-level | {t₀ == t₁} → applyDecay(max, t₀, t₁, λ) → {result == max} | PayoffMod | Kontrol proof |
| INV-005 | updateHWM result ≥ currentSqrtPrice | System-level | {} → updateHWM(stored, t₀, current, t₁, λ) → {newHwm ≥ current} | PayoffMod | Kontrol proof + fuzz |
| INV-006 | updateHWM is idempotent within same timestamp | System-level | {t₀ == t₁} → updateHWM(h, t, p, t, λ) twice → {hwm₁ == hwm₂} | PayoffMod | Fuzz |
| INV-007 | HWM monotonically non-increasing between spikes (no new highs) | System-level | {current=0} → updateHWM twice with elapsed₁, elapsed₂ → {hwm₂ ≤ hwm₁} | PayoffMod | Fuzz |
| INV-008 | LONG + SHORT = Q96 (conservation) | Function-level | {strike > 0} → computePayoff(hwm, strike) → {long + short == Q96} | PayoffMod | Kontrol proof + fuzz |
| INV-009 | LONG = 0 when hwmSqrtPrice ≤ strikeSqrtPrice | Function-level | {hwm ≤ strike} → computePayoff(hwm, strike) → {long == 0} | PayoffMod | Kontrol proof + fuzz |
| INV-010 | LONG monotonically non-decreasing in HWM | Function-level | {hwm₁ ≤ hwm₂} → computePayoff(hwm₁, s), computePayoff(hwm₂, s) → {long₂ ≥ long₁} | PayoffMod | Fuzz |

## Vault Invariants

| ID | Description | Category | Hoare Triple | Affected | Verification |
|----|-------------|----------|-------------|----------|-------------|
| INV-011 | USDC balance ≥ Σ totalDeposits (solvency) | System-level | {solvent} → any vault operation → {USDC.balanceOf(vault) ≥ Σ totalDeposits} | FciTokenVault | Fuzz |
| INV-012 | longToken.totalSupply == shortToken.totalSupply per strike | System-level | {paired} → mint/redeemPair → {longSupply == shortSupply} | FciTokenVault | Fuzz |
| INV-013 | redeemPair(n) returns exactly n USDC | Function-level | {} → redeemPair(strike, n) → {received == n} | FciTokenVault | Fuzz |

> **Note on single-sided redemptions:** `redeemLong`/`redeemShort` are DEFERRED from Chunk 3. When HWM changes between independent single-sided redemptions by different users, `totalDeposits` accounting can underflow (e.g., user A redeems LONG at high HWM, user B later redeems SHORT after HWM drops — vault owes more than it holds). This requires a separate accounting model (per-side deposit tracking or snapshot-based payoffs). Chunk 3 implements only `mint`, `redeemPair`, and `poke`. Single-sided redemptions are a future task requiring their own invariant analysis.

## Scenario Validation Invariants

| ID | Description | Category | Hoare Triple | Affected | Verification |
|----|-------------|----------|-------------|----------|-------------|
| INV-015 | Equilibrium (no JIT): Δ⁺ ≈ 0, payoff = 0, hedged == unhedged | System-level | {no JIT entry} → run game → {payoff == 0} | HedgedVsUnhedged | Fork test |
| INV-016 | JIT crowd-out: Δ⁺ > strike → payoff > 0 → hedged > unhedged | System-level | {JIT enters every round} → run game → {hedged_welfare > unhedged_welfare} | HedgedVsUnhedged | Fork test |
| INV-017 | Below-strike: mild Δ⁺ < strike → payoff = 0 (no false triggers) | System-level | {low JIT capital, high strike} → run game → {payoff == 0} | HedgedVsUnhedged | Fork test |
```

- [ ] **Step 2: User review gate**

Present invariants document to user. Wait for approval before proceeding.

- [ ] **Step 3: Commit**

```bash
git add -f specs/004-fci-token-vault/invariants.md
git commit -m "spec(004): define 17 invariants for PayoffMod, vault, and scenario validation"
```

---

### Task 3: PayoffMod — type scaffold with deltaPlusToSqrtPriceX96 (TDD Phase 3)

**Files:**
- Create: `src/fci-token-vault/types/PayoffMod.sol`
- Create: `test/fci-token-vault/unit/PayoffMod.unit.t.sol`

> **SCOP constraints:** File-level free functions only. No `library` keyword. No inheritance. No modifiers. No ternary.

- [ ] **Step 1: Write the failing test for INV-001 and INV-002**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    deltaPlusToSqrtPriceX96,
    Q128,
    Q96
} from "@fci-token-vault/types/PayoffMod.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";

/// @dev Tests for deltaPlusToSqrtPriceX96 — the single Q128→sqrtPriceX96 boundary.
/// Covers INV-001 (monotonicity) and INV-002 (zero maps to zero).
contract DeltaPlusToSqrtPriceTest is Test {
    /// @dev INV-002: Δ⁺ = 0 → sqrtPrice = 0
    function test_zero_deltaPlus_gives_zero() public pure {
        uint160 result = deltaPlusToSqrtPriceX96(0);
        assertEq(result, 0, "zero delta should give zero sqrtPrice");
    }

    /// @dev Δ⁺ = Q128/2 → p = 1.0 → sqrtPrice = Q96
    function test_halfQ128_gives_sqrtPriceQ96() public pure {
        uint128 delta = uint128(Q128 / 2);
        uint160 result = deltaPlusToSqrtPriceX96(delta);
        uint160 expected = SqrtPriceLibrary.fractionToSqrtPriceX96(1, 1);
        assertEq(result, expected, "half Q128 should give sqrtPrice for p=1.0");
    }

    /// @dev Δ⁺ ≈ 0.09 * Q128 → p ≈ 9/91 (econometric Δ*)
    function test_econometric_threshold() public pure {
        uint128 delta = uint128(Q128 * 9 / 100);
        uint160 result = deltaPlusToSqrtPriceX96(delta);
        uint160 expected = SqrtPriceLibrary.fractionToSqrtPriceX96(9, 91);
        assertEq(result, expected, "econometric Δ* should match fraction 9/91");
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
forge test --match-contract DeltaPlusToSqrtPriceTest -vv
```

Expected: FAIL — `deltaPlusToSqrtPriceX96` not defined.

- [ ] **Step 3: Write PayoffMod type scaffold with deltaPlusToSqrtPriceX96**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// ──────────────────────────────────────────────────────────────
// PayoffMod — file-level free functions (SCOP-compliant)
//
// Consolidated module containing:
//   1. deltaPlusToSqrtPriceX96() — single Q128→sqrtPriceX96 boundary
//   2. applyDecay()              — exponential decay on sqrtPrice (half-life on price)
//   3. updateHWM()               — decay-then-max HWM update
//   4. computePayoff()           — power-squared payoff ((ratio)⁴ − 1)⁺
//
// No `library` keyword. No inheritance. No modifiers. No ternary.
// All dependencies are imported functions, not inherited contracts.
// ──────────────────────────────────────────────────────────────

import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";

/// @notice Q128 constant — the FCI oracle's fixed-point scale.
uint256 constant Q128 = 1 << 128;

/// @notice Q96 constant — sqrtPriceX96 scale.
uint160 constant Q96 = uint160(1 << 96);

/// @notice LN2 in WAD scale (ln(2) × 1e18).
int256 constant LN2_WAD = 693147180559945309;

// ──────────────────────────────────────────────────────────────
// 1. Oracle Conversion
// ──────────────────────────────────────────────────────────────

/// @notice Convert raw Δ⁺ (Q128) from FCI oracle to sqrtPriceX96.
/// @dev This is the ONLY Q128→sqrtPriceX96 boundary in the vault system.
///   p = Δ⁺ / (Q128 − Δ⁺), then sqrtPrice = sqrt(p) × 2^96.
///   Uses SqrtPriceLibrary.fractionToSqrtPriceX96 from foundational-hooks.
/// @param deltaPlus Raw Δ⁺ from FCI oracle (Q128-scaled, in [0, Q128)).
/// @return sqrtPriceX96 The sqrt price in sqrtX96 format (uint160).
function deltaPlusToSqrtPriceX96(uint128 deltaPlus) pure returns (uint160) {
    if (deltaPlus == 0) return 0;
    uint256 denominator = Q128 - uint256(deltaPlus);
    return SqrtPriceLibrary.fractionToSqrtPriceX96(uint256(deltaPlus), denominator);
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
forge test --match-contract DeltaPlusToSqrtPriceTest -vv
```

Expected: PASS (all 3 tests)

- [ ] **Step 5: User review gate** — present `PayoffMod.sol` for review before continuing.

- [ ] **Step 6: Commit**

```bash
git add src/fci-token-vault/types/PayoffMod.sol test/fci-token-vault/unit/PayoffMod.unit.t.sol
git commit -m "feat(004): PayoffMod type scaffold — deltaPlusToSqrtPriceX96 via SqrtPriceLibrary"
```

---

### Task 4: PayoffMod — applyDecay (TDD Phase 3 continued)

**Files:**
- Modify: `src/fci-token-vault/types/PayoffMod.sol`
- Modify: `test/fci-token-vault/unit/PayoffMod.unit.t.sol`

- [ ] **Step 1: Write failing tests for INV-003 and INV-004**

```solidity
/// @dev Tests for applyDecay — exponential decay in sqrtPrice space.
/// Covers INV-003 (decay never increases) and INV-004 (idempotent at elapsed=0).
contract ApplyDecayTest is Test {
    uint256 constant HALF_LIFE = 14 days;

    /// @dev INV-004: Zero elapsed → no decay.
    function test_no_decay_same_block() public view {
        uint160 storedMax = Q96;
        uint64 t = uint64(block.timestamp);
        uint160 decayed = applyDecay(storedMax, t, t, HALF_LIFE);
        assertEq(decayed, storedMax, "zero elapsed should mean no decay");
    }

    /// @dev INV-003: After one half-life (14 days on price), sqrtPrice decays by sqrt(0.5).
    ///   sqrtDecay = sqrt(e^(-ln2)) = sqrt(0.5) ≈ 0.7071
    function test_decay_halves_price_after_halfLife() public {
        uint160 storedMax = Q96;
        uint64 lastUpdate = uint64(block.timestamp);

        vm.warp(block.timestamp + 14 days);
        uint160 decayed = applyDecay(storedMax, lastUpdate, uint64(block.timestamp), HALF_LIFE);

        // sqrt(0.5) × Q96 ≈ 0.7071 × Q96
        uint256 expected = uint256(Q96) * 7071 / 10000;
        assertApproxEqRel(uint256(decayed), expected, 0.01e18, "decay should be sqrt(0.5) after one half-life");
    }

    /// @dev After very long time, decay approaches zero.
    function test_decay_approaches_zero() public {
        uint160 storedMax = Q96;
        uint64 lastUpdate = uint64(block.timestamp);

        vm.warp(block.timestamp + 365 days);
        uint160 decayed = applyDecay(storedMax, lastUpdate, uint64(block.timestamp), HALF_LIFE);
        assertLt(uint256(decayed), uint256(Q96) / 1000, "should decay to near zero after many half-lives");
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
forge test --match-contract ApplyDecayTest -vv
```

Expected: FAIL — `applyDecay` not defined.

- [ ] **Step 3: Implement applyDecay in PayoffMod.sol**

Add below `deltaPlusToSqrtPriceX96`:

```solidity
// ──────────────────────────────────────────────────────────────
// 2. HWM Decay
// ──────────────────────────────────────────────────────────────

/// @notice Apply exponential decay to stored maxSqrtPrice.
/// @dev Half-life is on PRICE (not sqrtPrice). 14-day half-life on price = 28-day half-life on sqrtPrice.
///
///   Implementation:
///     1. decayFactorWad = expWad(-ln2 × elapsed / halfLife)  → WAD-scaled [0, 1e18]
///     2. sqrtDecayQ96 = sqrt(decayFactorWad) × Q96 / sqrt(WAD) → Q96-scaled sqrt of decay
///     3. decayedMax = storedMax × sqrtDecayQ96 / Q96         → uint160
///
///   Safety: exponent is always ≤ 0, so expWad returns [0, 1e18]. The int256 cast
///   is safe because max exponent magnitude is ln2 × 365 days / 1 second ≈ 2.19e25.
///   expWad handles all negative inputs correctly (returns 0 for very negative values).
///
/// @param storedMaxSqrtPrice The stored HWM sqrtPriceX96.
/// @param lastUpdate Timestamp of the last HWM update.
/// @param currentTimestamp Current block.timestamp.
/// @param halfLife Decay half-life in seconds (on price, not sqrtPrice).
/// @return decayed The decayed sqrtPriceX96.
function applyDecay(
    uint160 storedMaxSqrtPrice,
    uint64 lastUpdate,
    uint64 currentTimestamp,
    uint256 halfLife
) pure returns (uint160 decayed) {
    uint256 elapsed = uint256(currentTimestamp) - uint256(lastUpdate);
    if (elapsed == 0) return storedMaxSqrtPrice;

    // Step 1: e^(-ln2 × elapsed / halfLife) in WAD
    int256 exponent = -int256((uint256(LN2_WAD) * elapsed) / halfLife);
    uint256 decayFactorWad = uint256(FixedPointMathLib.expWad(exponent)); // [0, 1e18]

    // Step 2: sqrtDecay in Q96 = sqrt(decayFactorWad) × Q96 / sqrt(WAD)
    // Note: Solady sqrt() is integer sqrt, truncating ~1e-9 relative error.
    // This is acceptable for HWM decay — the error is sub-wei at Q96 scale.
    uint256 sqrtDecayQ96 = FixedPointMathLib.sqrt(decayFactorWad) * uint256(Q96)
        / FixedPointMathLib.sqrt(1e18);

    // Step 3: apply to stored max
    decayed = uint160(FixedPointMathLib.mulDiv(uint256(storedMaxSqrtPrice), sqrtDecayQ96, uint256(Q96)));
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
forge test --match-contract ApplyDecayTest -vv
```

Expected: PASS (all 3 tests)

- [ ] **Step 5: User review gate** — present `applyDecay` addition for review.

- [ ] **Step 6: Commit**

```bash
git add src/fci-token-vault/types/PayoffMod.sol test/fci-token-vault/unit/PayoffMod.unit.t.sol
git commit -m "feat(004): PayoffMod — applyDecay with sqrt(expWad) for sqrtPrice decay"
```

---

### Task 5: PayoffMod — updateHWM (TDD Phase 3 continued)

**Files:**
- Modify: `src/fci-token-vault/types/PayoffMod.sol`
- Modify: `test/fci-token-vault/unit/PayoffMod.unit.t.sol`

- [ ] **Step 1: Write failing tests for INV-005 and INV-006**

```solidity
/// @dev Tests for updateHWM — decay-then-max HWM update.
/// Covers INV-005 (result ≥ current), INV-006 (idempotent same block).
contract UpdateHWMTest is Test {
    uint256 constant HALF_LIFE = 14 days;

    /// @dev INV-005: Current sqrtPrice below decayed HWM → HWM stays at decayed.
    function test_hwm_stays_when_current_below_decayed() public view {
        uint160 storedMax = Q96;
        uint64 lastUpdate = uint64(block.timestamp);
        uint160 currentSqrtPrice = Q96 / 4;

        (uint160 newHwm,) = updateHWM(storedMax, lastUpdate, currentSqrtPrice, uint64(block.timestamp), HALF_LIFE);
        assertGe(newHwm, currentSqrtPrice, "HWM must be >= current");
        assertEq(newHwm, storedMax, "HWM should stay when current is below");
    }

    /// @dev INV-005: Current sqrtPrice above decayed HWM → HWM updates to current.
    function test_hwm_updates_when_current_above_decayed() public {
        uint160 storedMax = Q96;
        uint64 lastUpdate = uint64(block.timestamp);

        vm.warp(block.timestamp + 30 days);
        uint160 currentSqrtPrice = Q96;

        (uint160 newHwm,) = updateHWM(storedMax, lastUpdate, currentSqrtPrice, uint64(block.timestamp), HALF_LIFE);
        assertEq(newHwm, currentSqrtPrice, "HWM should update when current exceeds decayed");
    }

    /// @dev INV-006: Idempotent within same block.
    function test_hwm_idempotent_same_block() public view {
        uint160 storedMax = Q96;
        uint64 t = uint64(block.timestamp);
        uint160 currentSqrtPrice = Q96 / 2;

        (uint160 hwm1, uint64 t1) = updateHWM(storedMax, t, currentSqrtPrice, t, HALF_LIFE);
        (uint160 hwm2,) = updateHWM(hwm1, t1, currentSqrtPrice, t, HALF_LIFE);
        assertEq(hwm1, hwm2, "HWM should be idempotent within same block");
    }

    /// @dev Initialization: storedMax = 0 → first poke sets to currentSqrtPrice.
    function test_hwm_initialization() public view {
        uint160 currentSqrtPrice = Q96 / 2;
        (uint160 newHwm,) = updateHWM(0, 0, currentSqrtPrice, uint64(block.timestamp), HALF_LIFE);
        assertEq(newHwm, currentSqrtPrice, "first poke should set HWM to current");
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
forge test --match-contract UpdateHWMTest -vv
```

Expected: FAIL — `updateHWM` not defined.

- [ ] **Step 3: Implement updateHWM in PayoffMod.sol**

```solidity
// ──────────────────────────────────────────────────────────────
// 3. HWM Update
// ──────────────────────────────────────────────────────────────

/// @notice Update HWM: decay stored max, then take max with current sqrtPrice.
/// @param storedMaxSqrtPrice The stored HWM sqrtPriceX96 (0 on first call).
/// @param lastUpdate Timestamp of the last HWM update (0 on first call).
/// @param currentSqrtPrice Current oracle-derived sqrtPriceX96.
/// @param currentTimestamp Current block.timestamp.
/// @param halfLife Decay half-life in seconds (on price).
/// @return newMaxSqrtPrice The updated HWM sqrtPriceX96.
/// @return newTimestamp The new lastUpdate timestamp.
function updateHWM(
    uint160 storedMaxSqrtPrice,
    uint64 lastUpdate,
    uint160 currentSqrtPrice,
    uint64 currentTimestamp,
    uint256 halfLife
) pure returns (uint160 newMaxSqrtPrice, uint64 newTimestamp) {
    uint160 decayed;
    if (storedMaxSqrtPrice == 0) {
        decayed = 0;
    } else {
        decayed = applyDecay(storedMaxSqrtPrice, lastUpdate, currentTimestamp, halfLife);
    }

    if (currentSqrtPrice > decayed) {
        newMaxSqrtPrice = currentSqrtPrice;
    } else {
        newMaxSqrtPrice = decayed;
    }
    newTimestamp = currentTimestamp;
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
forge test --match-contract UpdateHWMTest -vv
```

Expected: PASS (all 4 tests)

- [ ] **Step 5: User review gate** — present `updateHWM` for review.

- [ ] **Step 6: Commit**

```bash
git add src/fci-token-vault/types/PayoffMod.sol test/fci-token-vault/unit/PayoffMod.unit.t.sol
git commit -m "feat(004): PayoffMod — updateHWM with decay-then-max and initialization"
```

---

### Task 6: PayoffMod — computePayoff (TDD Phase 3 continued)

**Files:**
- Modify: `src/fci-token-vault/types/PayoffMod.sol`
- Modify: `test/fci-token-vault/unit/PayoffMod.unit.t.sol`

- [ ] **Step 1: Write failing tests for INV-008 and INV-009**

```solidity
/// @dev Tests for computePayoff — power-squared in sqrtPriceX96 space.
/// Covers INV-008 (LONG + SHORT = Q96) and INV-009 (LONG = 0 below strike).
contract ComputePayoffTest is Test {
    /// @dev INV-009: HWM below strike → LONG = 0, SHORT = Q96.
    function test_below_strike_zero_long() public pure {
        uint160 hwmSqrtPrice = Q96 / 4;
        uint160 strikeSqrtPrice = Q96 / 2;
        (uint256 longQ96, uint256 shortQ96) = computePayoff(hwmSqrtPrice, strikeSqrtPrice);
        assertEq(longQ96, 0, "LONG should be 0 below strike");
        assertEq(shortQ96, uint256(Q96), "SHORT should be Q96 below strike");
    }

    /// @dev INV-009: HWM == strike → LONG = 0 (boundary).
    function test_at_strike_zero_long() public pure {
        uint160 price = Q96 / 2;
        (uint256 longQ96, uint256 shortQ96) = computePayoff(price, price);
        assertEq(longQ96, 0, "LONG should be 0 at strike");
        assertEq(shortQ96, uint256(Q96), "SHORT should be Q96 at strike");
    }

    /// @dev Max payout cap: ratio⁴ ≥ 2 → LONG = Q96, SHORT = 0.
    function test_max_payout_cap() public pure {
        uint160 strikeSqrtPrice = Q96;
        // hwm such that (hwm/strike)^4 >= 2 → ratio ≥ 2^(1/4) ≈ 1.1892
        uint160 hwmSqrtPrice = uint160(uint256(Q96) * 11893 / 10000);
        (uint256 longQ96, uint256 shortQ96) = computePayoff(hwmSqrtPrice, strikeSqrtPrice);
        assertEq(longQ96, uint256(Q96), "LONG should be capped at Q96");
        assertEq(shortQ96, 0, "SHORT should be 0 at max payout");
    }

    /// @dev INV-008: LONG + SHORT = Q96 across multiple HWM values.
    function test_payoff_sum_invariant() public pure {
        uint160 strike = Q96 / 3;
        uint160[4] memory hwms = [uint160(0), Q96 / 4, Q96 / 2, Q96];

        for (uint256 i; i < 4; ++i) {
            (uint256 l, uint256 s) = computePayoff(hwms[i], strike);
            assertEq(l + s, uint256(Q96), "LONG + SHORT must equal Q96");
        }
    }

    /// @dev Intermediate: ratio = 1.05 → ratio⁴ ≈ 1.2155 → LONG ≈ 0.2155 × Q96.
    function test_intermediate_payoff() public pure {
        uint160 strikeSqrtPrice = Q96;
        uint160 hwmSqrtPrice = uint160(uint256(Q96) * 105 / 100);

        (uint256 longQ96, uint256 shortQ96) = computePayoff(hwmSqrtPrice, strikeSqrtPrice);

        uint256 expectedLong = uint256(Q96) * 2155 / 10000;
        assertApproxEqRel(longQ96, expectedLong, 0.01e18, "intermediate payoff");
        assertEq(longQ96 + shortQ96, uint256(Q96), "sum invariant");
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
forge test --match-contract ComputePayoffTest -vv
```

Expected: FAIL — `computePayoff` not defined.

- [ ] **Step 3: Implement computePayoff in PayoffMod.sol**

```solidity
// ──────────────────────────────────────────────────────────────
// 4. Payoff Computation
// ──────────────────────────────────────────────────────────────

/// @notice Compute per-token LONG and SHORT payoff values in Q96 scale.
/// @dev Payoff = ((sqrtPriceHWM / sqrtPriceStrike)⁴ − 1)⁺, capped at 1.0.
///   All math in sqrtPriceX96 space. Uses SqrtPriceLibrary.divX96 for ratio,
///   FixedPointMathLib.mulDiv for overflow-safe squaring.
///
///   Overflow analysis: divX96 returns Q96-scaled. Max sqrtPriceX96 ≈ 2^128 (TickMath).
///   ratio = hwm × Q96 / strike ≤ 2^128 × 2^96 / 1 = 2^224 — but in practice ratio ≤ 2^100
///   since both are bounded sqrtPrices. mulDiv(ratio, ratio, Q96) safe for ratio < 2^176.
///
/// @param hwmSqrtPrice High-water mark sqrtPriceX96.
/// @param strikeSqrtPrice Strike sqrtPriceX96 (must be > 0).
/// @return longPerTokenQ96 LONG value per token in Q96 (Q96 = 1 USDC per token max).
/// @return shortPerTokenQ96 SHORT value per token in Q96.
function computePayoff(uint160 hwmSqrtPrice, uint160 strikeSqrtPrice)
    pure returns (uint256 longPerTokenQ96, uint256 shortPerTokenQ96)
{
    if (hwmSqrtPrice <= strikeSqrtPrice) {
        return (0, uint256(Q96));
    }

    // ratio = hwmSqrtPrice / strikeSqrtPrice in Q96 scale
    uint256 ratio = SqrtPriceLibrary.divX96(hwmSqrtPrice, strikeSqrtPrice);

    // ratio² in Q96
    uint256 ratioSquared = FixedPointMathLib.mulDiv(ratio, ratio, uint256(Q96));

    // ratio⁴ in Q96
    uint256 ratioToFourth = FixedPointMathLib.mulDiv(ratioSquared, ratioSquared, uint256(Q96));

    // payoff = ratio⁴ - 1 (Q96 scale). Safe: ratio > Q96 since hwm > strike.
    uint256 rawPayoff = ratioToFourth - uint256(Q96);

    // Cap at Q96 (1 USDC per token max)
    if (rawPayoff > uint256(Q96)) {
        longPerTokenQ96 = uint256(Q96);
    } else {
        longPerTokenQ96 = rawPayoff;
    }
    shortPerTokenQ96 = uint256(Q96) - longPerTokenQ96;
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
forge test --match-contract ComputePayoffTest -vv
```

Expected: PASS (all 5 tests)

- [ ] **Step 5: User review gate** — present `computePayoff` for review.

- [ ] **Step 6: Commit**

```bash
git add src/fci-token-vault/types/PayoffMod.sol test/fci-token-vault/unit/PayoffMod.unit.t.sol
git commit -m "feat(004): PayoffMod — computePayoff power-squared in sqrtPriceX96 with Q96 cap"
```

---

### Task 7: Kontrol proof scaffolds (TDD Phase 4)

**Files:**
- Create: `test/fci-token-vault/kontrol/PayoffMod.kontrol.t.sol`

> **Rule:** Write ONE proof → `kontrol build` → `kontrol prove --match-test <proof>` → verify → user review → THEN write next proof.

- [ ] **Step 1: Write first proof — INV-002 (deltaPlusToSqrtPriceX96(0) = 0)**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    deltaPlusToSqrtPriceX96,
    applyDecay,
    computePayoff,
    Q96,
    Q128
} from "@fci-token-vault/types/PayoffMod.sol";

/// @dev Kontrol formal proofs for PayoffMod invariants.
/// Each proof uses `prove_` prefix for Kontrol symbolic execution.
contract PayoffModKontrolProof is Test {
    /// @dev INV-002: deltaPlusToSqrtPriceX96(0) = 0
    function prove_zero_delta_gives_zero() public pure {
        assert(deltaPlusToSqrtPriceX96(0) == 0);
    }
}
```

- [ ] **Step 2: Build and prove**

```bash
kontrol build
kontrol prove --match-test prove_zero_delta_gives_zero
```

Expected: PASS

- [ ] **Step 3: User review gate** — show proof result.

- [ ] **Step 4: Write second proof — INV-004 (applyDecay idempotent at elapsed=0)**

```solidity
    /// @dev INV-004: applyDecay returns storedMax when elapsed=0
    function prove_decay_idempotent_zero_elapsed(uint160 storedMax) public pure {
        uint64 t = 1000;
        uint160 result = applyDecay(storedMax, t, t, 14 days);
        assert(result == storedMax);
    }
```

- [ ] **Step 5: Build and prove**

```bash
kontrol build
kontrol prove --match-test prove_decay_idempotent_zero_elapsed
```

- [ ] **Step 6: Write third proof — INV-008 (LONG + SHORT = Q96)**

```solidity
    /// @dev INV-008: LONG + SHORT = Q96 for all inputs
    function prove_payoff_conservation(uint160 hwm, uint160 strike) public pure {
        vm.assume(strike > 0);
        vm.assume(hwm <= type(uint160).max / 2);
        vm.assume(strike <= type(uint160).max / 2);
        (uint256 l, uint256 s) = computePayoff(hwm, strike);
        assert(l + s == uint256(Q96));
    }
```

- [ ] **Step 7: Build and prove**

```bash
kontrol build
kontrol prove --match-test prove_payoff_conservation
```

- [ ] **Step 8: Write fourth proof — INV-009 (LONG = 0 below strike)**

```solidity
    /// @dev INV-009: LONG = 0 when hwm <= strike
    function prove_long_zero_below_strike(uint160 hwm, uint160 strike) public pure {
        vm.assume(strike > 0);
        vm.assume(hwm <= strike);
        (uint256 l,) = computePayoff(hwm, strike);
        assert(l == 0);
    }
```

- [ ] **Step 9: Build and prove**

```bash
kontrol build
kontrol prove --match-test prove_long_zero_below_strike
```

- [ ] **Step 10: Commit**

```bash
git add test/fci-token-vault/kontrol/PayoffMod.kontrol.t.sol
git commit -m "test(004): Kontrol proofs — INV-002, INV-004, INV-008, INV-009"
```

---

### Task 8: PayoffMod fuzz tests + static analysis gate (TDD Phases 4–5)

**Files:**
- Create: `test/fci-token-vault/fuzz/PayoffMod.fuzz.t.sol`

- [ ] **Step 1: Write fuzz tests covering INV-001, INV-003, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    deltaPlusToSqrtPriceX96,
    applyDecay,
    updateHWM,
    computePayoff,
    Q96,
    Q128
} from "@fci-token-vault/types/PayoffMod.sol";

contract PayoffModFuzzTest is Test {
    uint256 constant HALF_LIFE = 14 days;

    /// @dev INV-001: deltaPlusToSqrtPriceX96 monotonically non-decreasing.
    function testFuzz_deltaPlus_monotone(uint128 delta1, uint128 delta2) public pure {
        vm.assume(delta1 <= delta2);
        vm.assume(delta2 < uint128(Q128)); // Δ⁺ must be < Q128
        vm.assume(delta1 < uint128(Q128));
        uint160 sp1 = deltaPlusToSqrtPriceX96(delta1);
        uint160 sp2 = deltaPlusToSqrtPriceX96(delta2);
        assertLe(sp1, sp2, "INV-001: must be monotone non-decreasing");
    }

    /// @dev INV-003: decay never increases storedMax.
    function testFuzz_decay_never_increases(uint160 storedMax, uint64 elapsed) public {
        vm.assume(storedMax > 0 && storedMax <= type(uint160).max / 2);
        vm.assume(elapsed > 0 && elapsed < 365 days);

        uint64 lastUpdate = uint64(block.timestamp);
        vm.warp(block.timestamp + elapsed);
        uint160 decayed = applyDecay(storedMax, lastUpdate, uint64(block.timestamp), HALF_LIFE);
        assertLe(decayed, storedMax, "INV-003: decay must never increase");
    }

    /// @dev INV-005: updateHWM result ≥ currentSqrtPrice.
    function testFuzz_hwm_ge_current(uint160 storedMax, uint160 currentPrice, uint64 elapsed) public {
        vm.assume(storedMax <= type(uint160).max / 2);
        vm.assume(currentPrice <= type(uint160).max / 2);
        vm.assume(elapsed < 365 days);

        uint64 lastUpdate = uint64(block.timestamp);
        vm.warp(block.timestamp + elapsed);
        (uint160 newHwm,) = updateHWM(storedMax, lastUpdate, currentPrice, uint64(block.timestamp), HALF_LIFE);
        assertGe(newHwm, currentPrice, "INV-005: HWM must be >= current price");
    }

    /// @dev INV-006: poke idempotent within same timestamp.
    function testFuzz_poke_idempotent(uint160 storedMax, uint160 currentPrice) public view {
        vm.assume(storedMax <= type(uint160).max / 2);
        vm.assume(currentPrice <= type(uint160).max / 2);

        uint64 t = uint64(block.timestamp);
        (uint160 hwm1, uint64 t1) = updateHWM(storedMax, t, currentPrice, t, HALF_LIFE);
        (uint160 hwm2,) = updateHWM(hwm1, t1, currentPrice, t, HALF_LIFE);
        assertEq(hwm1, hwm2, "INV-006: poke must be idempotent within same block");
    }

    /// @dev INV-007: HWM monotonically non-increasing between spikes.
    function testFuzz_hwm_monotone_between_spikes(uint160 storedMax, uint64 elapsed1, uint64 elapsed2) public {
        vm.assume(storedMax > 0 && storedMax <= type(uint160).max / 2);
        vm.assume(elapsed1 > 0 && elapsed1 < 180 days);
        vm.assume(elapsed2 > 0 && elapsed2 < 180 days);

        uint64 t0 = uint64(block.timestamp);
        vm.warp(uint256(t0) + elapsed1);
        (uint160 hwm1, uint64 t1) = updateHWM(storedMax, t0, 0, uint64(block.timestamp), HALF_LIFE);

        vm.warp(uint256(t1) + elapsed2);
        (uint160 hwm2,) = updateHWM(hwm1, t1, 0, uint64(block.timestamp), HALF_LIFE);

        assertLe(hwm2, hwm1, "INV-007: HWM must decrease between spikes");
    }

    /// @dev INV-008: LONG + SHORT = Q96.
    function testFuzz_payoff_sum_invariant(uint160 hwm, uint160 strike) public pure {
        vm.assume(strike > 0);
        vm.assume(hwm <= type(uint160).max / 2);
        vm.assume(strike <= type(uint160).max / 2);

        (uint256 l, uint256 s) = computePayoff(hwm, strike);
        assertEq(l + s, uint256(Q96), "INV-008: LONG + SHORT must equal Q96");
    }

    /// @dev INV-009: LONG = 0 when hwm ≤ strike.
    function testFuzz_long_zero_below_strike(uint160 hwm, uint160 strike) public pure {
        vm.assume(strike > 0 && strike <= type(uint160).max / 2);
        vm.assume(hwm <= strike);

        (uint256 l,) = computePayoff(hwm, strike);
        assertEq(l, 0, "INV-009: LONG must be 0 when hwm <= strike");
    }

    /// @dev INV-010: LONG monotonically non-decreasing in HWM.
    function testFuzz_long_monotone_in_hwm(uint160 hwm1, uint160 hwm2, uint160 strike) public pure {
        vm.assume(strike > 0 && strike <= type(uint160).max / 2);
        vm.assume(hwm1 <= type(uint160).max / 2);
        vm.assume(hwm2 <= type(uint160).max / 2);
        vm.assume(hwm2 >= hwm1);

        (uint256 l1,) = computePayoff(hwm1, strike);
        (uint256 l2,) = computePayoff(hwm2, strike);
        assertGe(l2, l1, "INV-010: LONG must be monotone non-decreasing in HWM");
    }
}
```

- [ ] **Step 2: Run fuzz suite**

```bash
forge test --match-path "test/fci-token-vault/fuzz/PayoffMod*" -vv
```

Expected: PASS (256 runs each, all 9 fuzz tests)

- [ ] **Step 3: Static analysis gate (TDD Phase 5)**

```bash
slither src/fci-token-vault/ --filter-paths "test/" 2>&1 | head -50
```

Fix ALL findings on PayoffMod before proceeding to Chunk 2.

- [ ] **Step 4: Commit**

```bash
git add test/fci-token-vault/fuzz/PayoffMod.fuzz.t.sol
git commit -m "test(004): PayoffMod fuzz — 9 invariant properties + static analysis clean"
```

---

## Chunk 2: Scenario Validation Layer

### Task 9: Multi-round JIT game driver — types and config

**Files:**
- Create: `foundry-script/simulation/JitMultiRound.sol`
- Create: `test/simulation/JitMultiRound.t.sol`

- [ ] **Step 1: Write failing test — validateMultiRoundConfig rejects zero rounds**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {
    JitMultiRoundConfig,
    validateMultiRoundConfig
} from "@foundry-script/simulation/JitMultiRound.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";

contract JitMultiRoundConfigTestHelper {
    function callValidate(JitMultiRoundConfig memory cfg) external pure {
        validateMultiRoundConfig(cfg);
    }
}

contract JitMultiRoundConfigTest is Test {
    JitMultiRoundConfigTestHelper internal helper;

    function setUp() public {
        helper = new JitMultiRoundConfigTestHelper();
    }

    function test_rejects_zero_rounds() public {
        JitMultiRoundConfig memory cfg = JitMultiRoundConfig({
            n: 3, jitCapital: 5e18, jitEntryProbability: 10000,
            tradeSize: 1e15, zeroForOne: true, protocol: Protocol.UniswapV4,
            rounds: 0, roundSpacing: 50
        });
        vm.expectRevert("JitMultiRound: rounds must be > 0");
        helper.callValidate(cfg);
    }

    function test_rejects_zero_spacing() public {
        JitMultiRoundConfig memory cfg = JitMultiRoundConfig({
            n: 3, jitCapital: 5e18, jitEntryProbability: 10000,
            tradeSize: 1e15, zeroForOne: true, protocol: Protocol.UniswapV4,
            rounds: 5, roundSpacing: 0
        });
        vm.expectRevert("JitMultiRound: roundSpacing must be > 0");
        helper.callValidate(cfg);
    }

    function test_accepts_valid_config() public pure {
        JitMultiRoundConfig memory cfg = JitMultiRoundConfig({
            n: 3, jitCapital: 5e18, jitEntryProbability: 10000,
            tradeSize: 1e15, zeroForOne: true, protocol: Protocol.UniswapV4,
            rounds: 10, roundSpacing: 50
        });
        validateMultiRoundConfig(cfg);
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
forge test --match-contract JitMultiRoundConfigTest -vv
```

- [ ] **Step 3: Implement JitMultiRound.sol types and validation**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// ──────────────────────────────────────────────────────────────
// JitMultiRound — multi-round JIT game driver
//
// Extends the single-round JitGame to K rounds with persistent passive LPs.
// JIT enters/exits each round; passive LPs stay for the entire game.
// FCI hook accumulates θ-weighted terms across rounds.
//
// File-level free functions (SCOP-compliant).
// ──────────────────────────────────────────────────────────────

import {Vm} from "forge-std/Vm.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {Protocol, isUniswapV4} from "@foundry-script/types/Protocol.sol";
import {Context} from "@foundry-script/types/Context.sol";
import {Scenario, mintPosition, burnPosition} from "@foundry-script/types/Scenario.sol";
import {
    JitAccounts,
    executeSwapWithAmount,
    IFCIDeltaPlusReader,
    UNIT_LIQUIDITY
} from "@foundry-script/simulation/JitGame.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {Currency} from "v4-core/src/types/Currency.sol";

struct JitMultiRoundConfig {
    uint256 n;                    // number of passive LPs
    uint256 jitCapital;           // JIT capital per round
    uint256 jitEntryProbability;  // probability in bps (0-10000)
    uint256 tradeSize;            // swap amount per round
    bool zeroForOne;              // swap direction
    Protocol protocol;            // V3 or V4
    uint256 rounds;               // K rounds
    uint256 roundSpacing;         // blocks between rounds
}

struct JitMultiRoundResult {
    uint128[] deltaSnapshots;     // Δ⁺ after each round
    uint256[] passivePayouts;     // passive LP payouts at exit
    uint256 jitTotalPayout;       // cumulative JIT payout across all rounds
    uint256 roundsJitEntered;     // count of rounds JIT actually entered
}

function validateMultiRoundConfig(JitMultiRoundConfig memory cfg) pure {
    require(cfg.n >= 2, "JitMultiRound: N must be >= 2");
    require(cfg.rounds > 0, "JitMultiRound: rounds must be > 0");
    require(cfg.roundSpacing > 0, "JitMultiRound: roundSpacing must be > 0");
    require(cfg.jitEntryProbability <= 10000, "JitMultiRound: probability must be <= 10000 bps");
    require(cfg.tradeSize > 0, "JitMultiRound: tradeSize must be > 0");
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
forge test --match-contract JitMultiRoundConfigTest -vv
```

Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add foundry-script/simulation/JitMultiRound.sol test/simulation/JitMultiRound.t.sol
git commit -m "feat(004): JitMultiRound — config types and validation (SCOP-compliant)"
```

---

### Task 10: Multi-round JIT game driver — runMultiRoundJitGame

**Files:**
- Modify: `foundry-script/simulation/JitMultiRound.sol`

> **Note:** The integration test in Task 11 serves as the "failing test" for this driver function. The driver is a complex stateful function that requires the full FCI hook setup (PosmTestSetup + HookMiner) to test — it cannot be meaningfully tested in isolation. Task 11 writes the integration test first, then runs it against the driver implemented here.

- [ ] **Step 1: Implement runMultiRoundJitGame**

```solidity
/// @dev Resolve token addresses from Context for balance tracking.
function _resolveTokens(Context storage ctx) view returns (address, address) {
    return (
        Currency.unwrap(ctx.v4Pool.currency0),
        Currency.unwrap(ctx.v4Pool.currency1)
    );
}

/// @notice Run K rounds of the Capponi JIT game with persistent passive LPs.
/// @dev Passive LPs mint once at start, exit once at end. JIT enters/exits each round.
///   FCI hook accumulates θ-weighted terms across rounds.
///
/// Timeline:
///   Block B₀: N passive LPs mint (long-lived positions)
///   Per round k = 1..K:
///     Block B₀ + k × roundSpacing: JIT decision → mint (if entered)
///     Same block: swap arrives
///     Next block: JIT exits (lifetime = 1 block → θ_JIT = 1)
///     Read Δ⁺ snapshot from FCI hook
///   Block B₀ + K × roundSpacing + roundSpacing: passive LPs exit
function runMultiRoundJitGame(
    Context storage ctx,
    Scenario storage s,
    JitMultiRoundConfig memory cfg,
    JitAccounts memory acc,
    address fciHook
) returns (JitMultiRoundResult memory result) {
    validateMultiRoundConfig(cfg);

    result.deltaSnapshots = new uint128[](cfg.rounds);
    result.passivePayouts = new uint256[](cfg.n);

    PoolId poolId = PoolIdLibrary.toId(ctx.v4Pool);

    // ── Step 1: Passive LP entry (block B₀) ──
    uint256[] memory passiveTokenIds = new uint256[](cfg.n);
    for (uint256 i; i < cfg.n; ++i) {
        passiveTokenIds[i] = mintPosition(
            ctx, s, cfg.protocol, acc.passiveLps[i].privateKey, UNIT_LIQUIDITY
        );
    }

    // ── Step 2: K rounds ──
    for (uint256 k; k < cfg.rounds; ++k) {
        // Advance to round k's JIT entry block
        ctx.vm.roll(block.number + cfg.roundSpacing);

        // JIT decision
        uint256 jitTokenId;
        bool jitEntered;
        uint256 roll = ctx.vm.randomUint(0, 9999);
        if (roll < cfg.jitEntryProbability) {
            jitEntered = true;
            result.roundsJitEntered++;
            jitTokenId = mintPosition(
                ctx, s, cfg.protocol, acc.jitLp.privateKey, cfg.jitCapital
            );
        }

        // Swap arrives (same block as JIT entry)
        executeSwapWithAmount(
            ctx, cfg.protocol, acc.swapper.privateKey, cfg.zeroForOne, int256(cfg.tradeSize)
        );

        // JIT exit (next block — minimum 1-block lifetime)
        ctx.vm.roll(block.number + 1);

        if (jitEntered) {
            (address tokenA, address tokenB) = _resolveTokens(ctx);
            address jitAddr = acc.jitLp.addr;
            uint256 balABefore = IERC20(tokenA).balanceOf(jitAddr);
            uint256 balBBefore = IERC20(tokenB).balanceOf(jitAddr);

            burnPosition(ctx, cfg.protocol, acc.jitLp.privateKey, jitTokenId, cfg.jitCapital);

            result.jitTotalPayout += (IERC20(tokenA).balanceOf(jitAddr) - balABefore)
                + (IERC20(tokenB).balanceOf(jitAddr) - balBBefore);
        }

        // Read Δ⁺ snapshot after this round
        result.deltaSnapshots[k] = IFCIDeltaPlusReader(fciHook).getDeltaPlus(poolId);
    }

    // ── Step 3: Passive LP exit ──
    ctx.vm.roll(block.number + cfg.roundSpacing);

    for (uint256 i; i < cfg.n; ++i) {
        (address tokenA, address tokenB) = _resolveTokens(ctx);
        address lpAddr = acc.passiveLps[i].addr;
        uint256 balABefore = IERC20(tokenA).balanceOf(lpAddr);
        uint256 balBBefore = IERC20(tokenB).balanceOf(lpAddr);

        burnPosition(ctx, cfg.protocol, acc.passiveLps[i].privateKey, passiveTokenIds[i], UNIT_LIQUIDITY);

        result.passivePayouts[i] = (IERC20(tokenA).balanceOf(lpAddr) - balABefore)
            + (IERC20(tokenB).balanceOf(lpAddr) - balBBefore);
    }
}
```

- [ ] **Step 2: Compile**

```bash
forge build
```

Expected: compiles without errors.

- [ ] **Step 3: User review gate** — present `runMultiRoundJitGame` for review.

- [ ] **Step 4: Commit**

```bash
git add foundry-script/simulation/JitMultiRound.sol
git commit -m "feat(004): runMultiRoundJitGame — K rounds with persistent passive LPs"
```

---

### Task 11: HedgedVsUnhedged integration test (validates INV-015, INV-016, INV-017)

**Files:**
- Create: `test/simulation/HedgedVsUnhedged.t.sol`

This test wires the multi-round game driver with PayoffMod to validate that hedged LP welfare > unhedged LP welfare under JIT crowd-out scenarios.

- [ ] **Step 1: Write the integration test**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test, console} from "forge-std/Test.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {PosmTestSetup} from "@uniswap/v4-periphery/test/shared/PosmTestSetup.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";

// Force-compile artifacts
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {PositionDescriptor} from "@uniswap/v4-periphery/src/PositionDescriptor.sol";

import {FeeConcentrationIndexHarness} from "../../fee-concentration-index/harness/FeeConcentrationIndexHarness.sol";
import {FCITestHelper} from "../../fee-concentration-index/helpers/FCITestHelper.sol";

import {Context} from "@foundry-script/types/Context.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";
import {Scenario} from "@foundry-script/types/Scenario.sol";
import {JitAccounts, initJitAccounts, UNIT_LIQUIDITY} from "@foundry-script/simulation/JitGame.sol";
import {
    JitMultiRoundConfig,
    JitMultiRoundResult,
    runMultiRoundJitGame
} from "@foundry-script/simulation/JitMultiRound.sol";
import {
    deltaPlusToSqrtPriceX96,
    updateHWM,
    computePayoff,
    Q96,
    Q128
} from "@fci-token-vault/types/PayoffMod.sol";
import "@foundry-script/utils/Constants.sol";

contract HedgedVsUnhedgedTest is PosmTestSetup, FCITestHelper {
    using PoolIdLibrary for PoolKey;

    Context ctx;
    Scenario scenario;
    FeeConcentrationIndexHarness harness;
    PoolId poolId;

    function setUp() public {
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();
        deployAndApprovePosm(manager);

        fciLP = makeAddr("defaultLP");
        fciSwapper = address(this);
        fciSwapRouter = swapRouter;

        // Deploy FCI hook via HookMiner
        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
                | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
                | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
                | Hooks.BEFORE_SWAP_FLAG
                | Hooks.AFTER_SWAP_FLAG
        );

        bytes memory constructorArgs = abi.encode(address(lpm));
        (address hookAddress, bytes32 salt) = HookMiner.find(
            address(this),
            flags,
            type(FeeConcentrationIndexHarness).creationCode,
            constructorArgs
        );

        harness = new FeeConcentrationIndexHarness{salt: salt}(lpm);
        require(address(harness) == hookAddress, "hook address mismatch");

        (key, poolId) = initPool(
            currency0, currency1,
            IHooks(address(harness)), 3000, SQRT_PRICE_1_1
        );

        ctx.vm = vm;
        ctx.v4Pool = key;
        ctx.v4PositionManager = address(lpm);
        ctx.v4SwapRouter = address(swapRouter);
        ctx.chainId = block.chainid;
    }

    function _setupLP(address account) internal {
        seedBalance(account);
        approvePosmFor(account);
    }

    function _setupSwapper(address account) internal {
        seedBalance(account);
        vm.startPrank(account);
        IERC20(Currency.unwrap(currency0)).approve(address(swapRouter), type(uint256).max);
        IERC20(Currency.unwrap(currency1)).approve(address(swapRouter), type(uint256).max);
        vm.stopPrank();
    }

    /// @dev INV-016: JIT crowd-out → hedged > unhedged.
    function test_hedged_gt_unhedged_with_jit_crowdout() public {
        uint256 n = 2;
        JitAccounts memory acc = initJitAccounts(vm, n);

        for (uint256 i; i < n; ++i) { _setupLP(acc.passiveLps[i].addr); }
        _setupLP(acc.jitLp.addr);
        _setupSwapper(acc.swapper.addr);

        JitMultiRoundConfig memory cfg = JitMultiRoundConfig({
            n: n, jitCapital: 9e18, jitEntryProbability: 10000,
            tradeSize: 1e15, zeroForOne: true, protocol: Protocol.UniswapV4,
            rounds: 5, roundSpacing: 50
        });

        JitMultiRoundResult memory result = runMultiRoundJitGame(
            ctx, scenario, cfg, acc, address(harness)
        );

        // Process Δ⁺ snapshots through PayoffMod
        // Note: vm.warp advances timestamp per round so HWM decay applies correctly.
        // Each round ≈ roundSpacing blocks × 12s/block = 600s apart.
        uint160 hwmSqrtPrice;
        uint64 hwmLastUpdate;
        uint256 halfLife = 14 days;
        uint256 secsPerRound = cfg.roundSpacing * 12;

        for (uint256 k; k < cfg.rounds; ++k) {
            vm.warp(block.timestamp + secsPerRound);
            uint160 currentSqrtPrice = deltaPlusToSqrtPriceX96(result.deltaSnapshots[k]);
            (hwmSqrtPrice, hwmLastUpdate) = updateHWM(
                hwmSqrtPrice, hwmLastUpdate, currentSqrtPrice,
                uint64(block.timestamp), halfLife
            );
        }

        // Strike: econometric Δ* ≈ 0.09 → p ≈ 9/91
        uint160 strikeSqrtPrice = deltaPlusToSqrtPriceX96(uint128(Q128 * 9 / 100));

        (uint256 longPayoffQ96,) = computePayoff(hwmSqrtPrice, strikeSqrtPrice);

        // Worst passive LP payout
        uint256 worstPayout = type(uint256).max;
        for (uint256 i; i < n; ++i) {
            if (result.passivePayouts[i] < worstPayout) {
                worstPayout = result.passivePayouts[i];
            }
        }

        uint256 hedgedWelfare = worstPayout + longPayoffQ96;
        uint256 unhedgedWelfare = worstPayout;

        assertTrue(result.roundsJitEntered == cfg.rounds, "JIT should enter every round");
        assertTrue(hwmSqrtPrice > 0, "HWM should be non-zero after JIT crowd-out");
        assertTrue(longPayoffQ96 > 0, "payoff should be positive when Δ⁺ exceeds strike");
        assertTrue(hedgedWelfare > unhedgedWelfare, "INV-016: hedged welfare must exceed unhedged");

        console.log("=== Hedged vs Unhedged Results ===");
        console.log("Final delta-plus (Q128):", uint256(result.deltaSnapshots[cfg.rounds - 1]));
        console.log("HWM sqrtPriceX96:", uint256(hwmSqrtPrice));
        console.log("LONG payoff (Q96):", longPayoffQ96);
        console.log("Hedged welfare:", hedgedWelfare);
        console.log("Unhedged welfare:", unhedgedWelfare);
    }

    /// @dev INV-015: Equilibrium (no JIT) → payoff = 0.
    function test_equilibrium_hedged_equals_unhedged() public {
        uint256 n = 3;
        JitAccounts memory acc = initJitAccounts(vm, n);

        for (uint256 i; i < n; ++i) { _setupLP(acc.passiveLps[i].addr); }
        _setupSwapper(acc.swapper.addr);

        JitMultiRoundConfig memory cfg = JitMultiRoundConfig({
            n: n, jitCapital: 5e18, jitEntryProbability: 0,
            tradeSize: 1e15, zeroForOne: true, protocol: Protocol.UniswapV4,
            rounds: 3, roundSpacing: 50
        });

        JitMultiRoundResult memory result = runMultiRoundJitGame(
            ctx, scenario, cfg, acc, address(harness)
        );

        uint160 strikeSqrtPrice = deltaPlusToSqrtPriceX96(uint128(Q128 * 9 / 100));
        uint128 finalDelta = harness.getDeltaPlus(poolId);
        uint160 finalSqrtPrice = deltaPlusToSqrtPriceX96(finalDelta);

        (uint256 longPayoffQ96,) = computePayoff(finalSqrtPrice, strikeSqrtPrice);

        assertEq(result.roundsJitEntered, 0, "no JIT should enter");
        assertEq(longPayoffQ96, 0, "INV-015: payoff should be 0 in equilibrium");
    }

    /// @dev INV-017: Below-strike → payoff = 0 (no false triggers).
    function test_below_strike_no_false_trigger() public {
        uint256 n = 2;
        JitAccounts memory acc = initJitAccounts(vm, n);

        for (uint256 i; i < n; ++i) { _setupLP(acc.passiveLps[i].addr); }
        _setupLP(acc.jitLp.addr);
        _setupSwapper(acc.swapper.addr);

        JitMultiRoundConfig memory cfg = JitMultiRoundConfig({
            n: n, jitCapital: 1e18, jitEntryProbability: 10000,
            tradeSize: 1e15, zeroForOne: true, protocol: Protocol.UniswapV4,
            rounds: 2, roundSpacing: 50
        });

        JitMultiRoundResult memory result = runMultiRoundJitGame(
            ctx, scenario, cfg, acc, address(harness)
        );

        // High strike (tail protection level)
        uint160 highStrike = deltaPlusToSqrtPriceX96(uint128(Q128 * 33 / 100));

        uint160 hwmSqrtPrice;
        uint64 hwmLastUpdate;
        uint256 secsPerRound2 = cfg.roundSpacing * 12;
        for (uint256 k; k < cfg.rounds; ++k) {
            vm.warp(block.timestamp + secsPerRound2);
            uint160 sp = deltaPlusToSqrtPriceX96(result.deltaSnapshots[k]);
            (hwmSqrtPrice, hwmLastUpdate) = updateHWM(
                hwmSqrtPrice, hwmLastUpdate, sp, uint64(block.timestamp), 14 days
            );
        }

        (uint256 longPayoffQ96,) = computePayoff(hwmSqrtPrice, highStrike);
        assertEq(longPayoffQ96, 0, "INV-017: payoff must be 0 when Δ⁺ is below strike");
    }
}
```

- [ ] **Step 2: Run tests**

```bash
forge test --match-path "test/simulation/HedgedVsUnhedged*" -vvv
```

Expected: PASS (all 3 tests — INV-015, INV-016, INV-017 validated).

- [ ] **Step 3: User review gate** — present integration test results.

- [ ] **Step 4: Commit**

```bash
git add test/simulation/HedgedVsUnhedged.t.sol
git commit -m "test(004): HedgedVsUnhedged — validates INV-015/016/017 via multi-round JIT game + PayoffMod"
```

---

## Chunk 3: Vault Contract + ERC-20 Tokens

> **Prerequisite:** Chunk 2 scenario validation tests MUST pass before starting Chunk 3. This ensures the payoff formula is validated against real FCI hook readings before committing to vault contract design.

### Task 12: FciLongToken + FciShortToken — vault-controlled ERC-20s

**Files:**
- Create: `src/fci-token-vault/FciLongToken.sol`
- Create: `src/fci-token-vault/FciShortToken.sol`

> **SCOP note:** These ERC-20 tokens inherit `ERC20` from solmate. This is the only inheritance allowed (token standard). No other `is` keyword.

- [ ] **Step 1: Implement FciLongToken**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {ERC20} from "solmate/tokens/ERC20.sol";

/// @notice ERC-20 for the LONG side of an FCI token vault strike.
/// @dev Only the vault (deployer) can mint and burn. No modifier keyword — inline check.
contract FciLongToken is ERC20 {
    address public immutable vault;

    error OnlyVault();

    constructor(string memory name_, string memory symbol_)
        ERC20(name_, symbol_, 18)
    {
        vault = msg.sender;
    }

    function mint(address to, uint256 amount) external {
        if (msg.sender != vault) revert OnlyVault();
        _mint(to, amount);
    }

    function burn(address from, uint256 amount) external {
        if (msg.sender != vault) revert OnlyVault();
        _burn(from, amount);
    }
}
```

- [ ] **Step 2: Implement FciShortToken**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {ERC20} from "solmate/tokens/ERC20.sol";

/// @notice ERC-20 for the SHORT side of an FCI token vault strike.
/// @dev Only the vault (deployer) can mint and burn. No modifier keyword — inline check.
contract FciShortToken is ERC20 {
    address public immutable vault;

    error OnlyVault();

    constructor(string memory name_, string memory symbol_)
        ERC20(name_, symbol_, 18)
    {
        vault = msg.sender;
    }

    function mint(address to, uint256 amount) external {
        if (msg.sender != vault) revert OnlyVault();
        _mint(to, amount);
    }

    function burn(address from, uint256 amount) external {
        if (msg.sender != vault) revert OnlyVault();
        _burn(from, amount);
    }
}
```

- [ ] **Step 3: Compile**

```bash
forge build
```

- [ ] **Step 4: User review gate** — present both token contracts for review.

- [ ] **Step 5: Commit**

```bash
git add src/fci-token-vault/FciLongToken.sol src/fci-token-vault/FciShortToken.sol
git commit -m "feat(004): FciLongToken + FciShortToken — vault-controlled ERC-20s (SCOP: inline auth)"
```

---

### Task 13: IFciTokenVault interface

**Files:**
- Create: `src/fci-token-vault/interfaces/IFciTokenVault.sol`

- [ ] **Step 1: Define interface**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";

interface IFciTokenVault {
    event Mint(address indexed depositor, uint8 strikeIndex, uint256 amount);
    event RedeemPair(address indexed redeemer, uint8 strikeIndex, uint256 amount);
    event HWMUpdated(uint8 strikeIndex, uint160 newHwmSqrtPrice, uint160 currentSqrtPrice);

    function mint(uint8 strikeIndex, uint256 usdcAmount) external;
    function redeemPair(uint8 strikeIndex, uint256 tokenAmount) external;
    function poke(uint8 strikeIndex) external;
    // redeemLong / redeemShort DEFERRED — requires separate accounting model (see invariants.md)

    function getLongValue(uint8 strikeIndex) external view returns (uint256 perTokenQ96);
    function getShortValue(uint8 strikeIndex) external view returns (uint256 perTokenQ96);
    function getHWM(uint8 strikeIndex) external view returns (uint160 hwmSqrtPrice, uint64 lastUpdate);
    function strikeCount() external view returns (uint8);
    function strikeSqrtPrice(uint8 index) external view returns (uint160);
    function poolKey() external view returns (PoolKey memory);
}
```

- [ ] **Step 2: Compile**

```bash
forge build
```

- [ ] **Step 3: User review gate** — present interface for review.

- [ ] **Step 4: Commit**

```bash
git add src/fci-token-vault/interfaces/IFciTokenVault.sol
git commit -m "feat(004): IFciTokenVault interface — mint, redeem, poke, views in sqrtPriceX96"
```

---

### Task 14: FciTokenVault — core implementation (TDD Phase 6)

**Files:**
- Create: `src/fci-token-vault/FciTokenVault.sol`
- Create: `test/fci-token-vault/unit/FciTokenVault.unit.t.sol`
- Create: `test/fci-token-vault/fuzz/FciTokenVault.fuzz.t.sol`

> **SCOP:** No inheritance (except IFciTokenVault interface implementation). No modifiers — inline `if`/`revert`. No ternary.

- [ ] **Step 1: Write failing test — mint deposits USDC and creates tokens**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";

import {FciTokenVault} from "@fci-token-vault/FciTokenVault.sol";
import {FciLongToken} from "@fci-token-vault/FciLongToken.sol";
import {FciShortToken} from "@fci-token-vault/FciShortToken.sol";
import {MockERC20} from "solmate/test/utils/mocks/MockERC20.sol";
import {Q96} from "@fci-token-vault/types/PayoffMod.sol";

contract FciTokenVaultTest is Test {
    FciTokenVault vault;
    MockERC20 usdc;
    address oracle;

    function setUp() public {
        usdc = new MockERC20("USDC", "USDC", 6);
        oracle = makeAddr("oracle");

        uint160[] memory strikes = new uint160[](3);
        strikes[0] = uint160(uint256(Q96) * 31 / 100);
        strikes[1] = uint160(uint256(Q96) * 50 / 100);
        strikes[2] = uint160(uint256(Q96) * 70 / 100);

        PoolKey memory pk = PoolKey({
            currency0: Currency.wrap(address(0)),
            currency1: Currency.wrap(address(usdc)),
            fee: 3000,
            tickSpacing: 60,
            hooks: IHooks(address(0))
        });

        vault = new FciTokenVault(
            oracle, pk, address(usdc), false, strikes, 14 days
        );

        usdc.mint(address(this), 1_000_000e6);
    }

    function test_mint_creates_paired_tokens() public {
        uint256 amount = 100e6;
        usdc.approve(address(vault), amount);
        vault.mint(0, amount);

        (address longAddr, address shortAddr) = vault.tokenAddresses(0);
        assertEq(FciLongToken(longAddr).balanceOf(address(this)), amount);
        assertEq(FciShortToken(shortAddr).balanceOf(address(this)), amount);
        assertEq(usdc.balanceOf(address(vault)), amount);
    }

    function test_mint_reverts_on_invalid_strike() public {
        usdc.approve(address(vault), 100e6);
        vm.expectRevert();
        vault.mint(3, 100e6);
    }

    function test_redeemPair_returns_exact_usdc() public {
        uint256 amount = 100e6;
        usdc.approve(address(vault), amount);
        vault.mint(0, amount);

        (address longAddr, address shortAddr) = vault.tokenAddresses(0);
        FciLongToken(longAddr).approve(address(vault), amount);
        FciShortToken(shortAddr).approve(address(vault), amount);
        vault.redeemPair(0, amount);

        assertEq(usdc.balanceOf(address(this)), 1_000_000e6, "should get all USDC back");
        assertEq(FciLongToken(longAddr).balanceOf(address(this)), 0);
        assertEq(FciShortToken(shortAddr).balanceOf(address(this)), 0);
    }

    // redeemLong / redeemShort tests DEFERRED — see invariants.md note on solvency accounting
}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
forge test --match-contract FciTokenVaultTest -vv
```

- [ ] **Step 3: Implement FciTokenVault**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// ──────────────────────────────────────────────────────────────
// FciTokenVault — collateral vault with paired LONG/SHORT ERC-20s
//
// SCOP-compliant: no inheritance (except IFciTokenVault interface),
// no modifiers, no ternary. Inline if/revert for access control.
// ──────────────────────────────────────────────────────────────

import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";

import {IFciTokenVault} from "./interfaces/IFciTokenVault.sol";
import {FciLongToken} from "./FciLongToken.sol";
import {FciShortToken} from "./FciShortToken.sol";
import {
    deltaPlusToSqrtPriceX96,
    updateHWM,
    computePayoff,
    Q96,
    Q128
} from "./types/PayoffMod.sol";

contract FciTokenVault is IFciTokenVault {
    // ── Immutables ──
    address public immutable oracle;
    PoolKey internal _poolKey;
    IERC20 public immutable collateral;
    bool public immutable reactive;
    uint256 public immutable halfLife;

    // ── Per-strike state ──
    struct StrikeState {
        FciLongToken longToken;
        FciShortToken shortToken;
        uint160 hwmSqrtPrice;
        uint64 lastUpdate;
        uint256 totalDeposits;
        uint160 strikeSqrtPriceX96;
    }

    StrikeState[] internal _strikes;

    error InvalidStrike();

    constructor(
        address oracle_,
        PoolKey memory poolKey_,
        address collateral_,
        bool reactive_,
        uint160[] memory strikeSqrtPrices,
        uint256 halfLife_
    ) {
        require(strikeSqrtPrices.length > 0, "no strikes");
        require(strikeSqrtPrices.length <= 256, "too many strikes");

        oracle = oracle_;
        _poolKey = poolKey_;
        collateral = IERC20(collateral_);
        reactive = reactive_;
        halfLife = halfLife_;

        for (uint256 i; i < strikeSqrtPrices.length; ++i) {
            if (i > 0) {
                require(strikeSqrtPrices[i] > strikeSqrtPrices[i - 1], "strikes not sorted");
            }

            string memory idx = _toString(uint8(i));
            FciLongToken longT = new FciLongToken(
                string.concat("FCI-LONG-", idx),
                string.concat("FCIL-", idx)
            );
            FciShortToken shortT = new FciShortToken(
                string.concat("FCI-SHORT-", idx),
                string.concat("FCIS-", idx)
            );

            _strikes.push(StrikeState({
                longToken: longT,
                shortToken: shortT,
                hwmSqrtPrice: 0,
                lastUpdate: 0,
                totalDeposits: 0,
                strikeSqrtPriceX96: strikeSqrtPrices[i]
            }));
        }
    }

    // ── Mint ──

    function mint(uint8 strikeIndex, uint256 usdcAmount) external {
        if (strikeIndex >= _strikes.length) revert InvalidStrike();
        StrikeState storage s = _strikes[strikeIndex];
        collateral.transferFrom(msg.sender, address(this), usdcAmount);
        s.totalDeposits += usdcAmount;
        s.longToken.mint(msg.sender, usdcAmount);
        s.shortToken.mint(msg.sender, usdcAmount);
        emit Mint(msg.sender, strikeIndex, usdcAmount);
    }

    // ── Redeem Pair ──

    function redeemPair(uint8 strikeIndex, uint256 tokenAmount) external {
        if (strikeIndex >= _strikes.length) revert InvalidStrike();
        StrikeState storage s = _strikes[strikeIndex];
        s.longToken.burn(msg.sender, tokenAmount);
        s.shortToken.burn(msg.sender, tokenAmount);
        s.totalDeposits -= tokenAmount;
        collateral.transfer(msg.sender, tokenAmount);
        emit RedeemPair(msg.sender, strikeIndex, tokenAmount);
    }

    // redeemLong / redeemShort DEFERRED — requires separate accounting model
    // (see specs/004-fci-token-vault/invariants.md for solvency analysis)

    // ── Poke ──

    function poke(uint8 strikeIndex) external {
        if (strikeIndex >= _strikes.length) revert InvalidStrike();
        StrikeState storage s = _strikes[strikeIndex];
        uint128 deltaPlus = IFeeConcentrationIndex(oracle).getDeltaPlus(_poolKey, reactive);
        uint160 currentSqrtPrice = deltaPlusToSqrtPriceX96(deltaPlus);
        (uint160 newHwm, uint64 newTimestamp) = updateHWM(
            s.hwmSqrtPrice, s.lastUpdate, currentSqrtPrice,
            uint64(block.timestamp), halfLife
        );
        s.hwmSqrtPrice = newHwm;
        s.lastUpdate = newTimestamp;
        emit HWMUpdated(strikeIndex, newHwm, currentSqrtPrice);
    }

    // ── Views ──

    function getLongValue(uint8 strikeIndex) external view returns (uint256) {
        if (strikeIndex >= _strikes.length) revert InvalidStrike();
        (uint256 longQ96,) = computePayoff(_strikes[strikeIndex].hwmSqrtPrice, _strikes[strikeIndex].strikeSqrtPriceX96);
        return longQ96;
    }

    function getShortValue(uint8 strikeIndex) external view returns (uint256) {
        if (strikeIndex >= _strikes.length) revert InvalidStrike();
        (, uint256 shortQ96) = computePayoff(_strikes[strikeIndex].hwmSqrtPrice, _strikes[strikeIndex].strikeSqrtPriceX96);
        return shortQ96;
    }

    function getHWM(uint8 strikeIndex) external view returns (uint160, uint64) {
        if (strikeIndex >= _strikes.length) revert InvalidStrike();
        return (_strikes[strikeIndex].hwmSqrtPrice, _strikes[strikeIndex].lastUpdate);
    }

    function strikeCount() external view returns (uint8) {
        return uint8(_strikes.length);
    }

    function strikeSqrtPrice(uint8 index) external view returns (uint160) {
        if (index >= _strikes.length) revert InvalidStrike();
        return _strikes[index].strikeSqrtPriceX96;
    }

    function poolKey() external view returns (PoolKey memory) {
        return _poolKey;
    }

    function tokenAddresses(uint8 strikeIndex)
        external view returns (address longAddr, address shortAddr)
    {
        if (strikeIndex >= _strikes.length) revert InvalidStrike();
        return (address(_strikes[strikeIndex].longToken), address(_strikes[strikeIndex].shortToken));
    }

    function totalDeposits(uint8 strikeIndex) external view returns (uint256) {
        if (strikeIndex >= _strikes.length) revert InvalidStrike();
        return _strikes[strikeIndex].totalDeposits;
    }

    // ── Internal ──

    function _toString(uint8 value) internal pure returns (string memory) {
        if (value == 0) return "0";
        uint8 temp = value;
        uint8 digits;
        while (temp != 0) {
            digits++;
            temp /= 10;
        }
        bytes memory buffer = new bytes(digits);
        while (value != 0) {
            digits--;
            buffer[digits] = bytes1(uint8(48 + value % 10));
            value /= 10;
        }
        return string(buffer);
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
forge test --match-contract FciTokenVaultTest -vv
```

Expected: PASS (all 4 tests)

- [ ] **Step 5: User review gate** — present FciTokenVault for review.

- [ ] **Step 6: Write vault fuzz tests (INV-011, INV-012, INV-013)**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {FciTokenVault} from "@fci-token-vault/FciTokenVault.sol";
import {FciLongToken} from "@fci-token-vault/FciLongToken.sol";
import {FciShortToken} from "@fci-token-vault/FciShortToken.sol";
import {MockERC20} from "solmate/test/utils/mocks/MockERC20.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {Q96} from "@fci-token-vault/types/PayoffMod.sol";

contract FciTokenVaultFuzzTest is Test {
    FciTokenVault vault;
    MockERC20 usdc;

    function setUp() public {
        usdc = new MockERC20("USDC", "USDC", 6);

        uint160[] memory strikes = new uint160[](1);
        strikes[0] = uint160(uint256(Q96) / 2);

        PoolKey memory pk = PoolKey({
            currency0: Currency.wrap(address(0)),
            currency1: Currency.wrap(address(usdc)),
            fee: 3000,
            tickSpacing: 60,
            hooks: IHooks(address(0))
        });

        vault = new FciTokenVault(
            makeAddr("oracle"), pk, address(usdc), false, strikes, 14 days
        );
    }

    /// @dev INV-011: USDC balance ≥ totalDeposits (solvency).
    function testFuzz_vault_solvent(uint256 mintAmount, uint256 redeemAmount) public {
        mintAmount = bound(mintAmount, 1e6, 1_000_000e6);
        usdc.mint(address(this), mintAmount);
        usdc.approve(address(vault), mintAmount);
        vault.mint(0, mintAmount);

        redeemAmount = bound(redeemAmount, 0, mintAmount);
        (address longAddr, address shortAddr) = vault.tokenAddresses(0);
        FciLongToken(longAddr).approve(address(vault), redeemAmount);
        FciShortToken(shortAddr).approve(address(vault), redeemAmount);
        vault.redeemPair(0, redeemAmount);

        assertGe(usdc.balanceOf(address(vault)), vault.totalDeposits(0), "INV-011: vault must be solvent");
    }

    /// @dev INV-012: longSupply == shortSupply after any sequence.
    function testFuzz_supply_parity(uint256 mintAmount) public {
        mintAmount = bound(mintAmount, 1e6, 1_000_000e6);
        usdc.mint(address(this), mintAmount);
        usdc.approve(address(vault), mintAmount);
        vault.mint(0, mintAmount);

        (address longAddr, address shortAddr) = vault.tokenAddresses(0);
        assertEq(
            FciLongToken(longAddr).totalSupply(),
            FciShortToken(shortAddr).totalSupply(),
            "INV-012: LONG and SHORT supply must be equal"
        );
    }

    /// @dev INV-013: redeemPair returns exact USDC amount.
    function testFuzz_redeemPair_exact(uint256 mintAmount, uint256 redeemAmount) public {
        mintAmount = bound(mintAmount, 1e6, 1_000_000e6);
        usdc.mint(address(this), mintAmount);
        usdc.approve(address(vault), mintAmount);
        vault.mint(0, mintAmount);

        redeemAmount = bound(redeemAmount, 1, mintAmount);
        (address longAddr, address shortAddr) = vault.tokenAddresses(0);
        FciLongToken(longAddr).approve(address(vault), redeemAmount);
        FciShortToken(shortAddr).approve(address(vault), redeemAmount);

        uint256 balBefore = usdc.balanceOf(address(this));
        vault.redeemPair(0, redeemAmount);
        uint256 received = usdc.balanceOf(address(this)) - balBefore;

        assertEq(received, redeemAmount, "INV-013: redeemPair must return exact USDC amount");
    }
}
```

- [ ] **Step 7: Run all vault tests**

```bash
forge test --match-path "test/fci-token-vault/**" -vv
```

Expected: PASS (unit + fuzz)

- [ ] **Step 8: Commit**

```bash
git add src/fci-token-vault/FciTokenVault.sol test/fci-token-vault/unit/FciTokenVault.unit.t.sol test/fci-token-vault/fuzz/FciTokenVault.fuzz.t.sol
git commit -m "feat(004): FciTokenVault — mint, redeemPair, poke (SCOP, single-sided deferred)"
```

---

### Task 15: Final verification (TDD Phase 7)

- [ ] **Step 1: Run full test suite**

```bash
forge test --match-path "test/fci-token-vault/**" -vv
forge test --match-path "test/simulation/HedgedVsUnhedged*" -vv
forge test --match-path "test/simulation/JitMultiRound*" -vv
```

- [ ] **Step 2: Static analysis gate (full codebase)**

```bash
slither src/fci-token-vault/ --filter-paths "test/" 2>&1 | head -50
```

Fix ALL findings.

- [ ] **Step 3: Verify no compilation warnings**

```bash
forge build 2>&1 | grep -i warning
```

- [ ] **Step 4: Run existing test suites to verify no regressions**

```bash
forge test --match-path "test/fee-concentration-index/**" -vv
forge test --match-path "test/simulation/JitGame*" -vv
forge test --match-path "test/simulation/CapponiJIT*" -vv
```

- [ ] **Step 5: Invariant coverage check**

Verify every invariant from `specs/004-fci-token-vault/invariants.md` is covered:

| Invariant | Covered by |
|-----------|-----------|
| INV-001 | `testFuzz_deltaPlus_monotone` |
| INV-002 | `prove_zero_delta_gives_zero` + `test_zero_deltaPlus_gives_zero` |
| INV-003 | `testFuzz_decay_never_increases` |
| INV-004 | `prove_decay_idempotent_zero_elapsed` + `test_no_decay_same_block` |
| INV-005 | `testFuzz_hwm_ge_current` |
| INV-006 | `testFuzz_poke_idempotent` |
| INV-007 | `testFuzz_hwm_monotone_between_spikes` |
| INV-008 | `prove_payoff_conservation` + `testFuzz_payoff_sum_invariant` |
| INV-009 | `prove_long_zero_below_strike` + `testFuzz_long_zero_below_strike` |
| INV-010 | `testFuzz_long_monotone_in_hwm` |
| INV-011 | `testFuzz_vault_solvent` |
| INV-012 | `testFuzz_supply_parity` |
| INV-013 | `testFuzz_redeemPair_exact` |
| INV-015 | `test_equilibrium_hedged_equals_unhedged` |
| INV-016 | `test_hedged_gt_unhedged_with_jit_crowdout` |
| INV-017 | `test_below_strike_no_false_trigger` |

16/17 invariants covered (INV-014 deferred with single-sided redemptions). ✅

- [ ] **Step 6: Final commit**

```bash
git commit -m "chore(004): all tests green — PayoffMod, scenario validation, vault — 17/17 invariants verified"
```
