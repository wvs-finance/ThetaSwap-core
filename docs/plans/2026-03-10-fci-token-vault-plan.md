# FCI Token Vault Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a collateral vault that tokenizes the FCI oracle into paired LONG/SHORT ERC-20s with power-squared payoff and decaying high-water mark.

**Architecture:** Three independent sub-components (HWM library, Payoff library, TokenVault contract) composed into a per-pool vault. Each sub-component is specified via @type-driven-development before implementation. Branch `004-fci-token-vault` off `main`.

**Tech Stack:** Solidity ^0.8.26, Solady FixedPointMathLib (expWad, mulDiv), Solmate ERC20, Forge (unit + fuzz tests), Uniswap V4 PoolKey type.

**Spec:** `docs/plans/2026-03-10-fci-token-vault-design.md`

---

## File Structure

```
src/fci-token-vault/
  interfaces/
    IFciTokenVault.sol          — vault public interface (mint, redeem*, poke)
  types/
    HighWaterMarkMod.sol        — HWM struct + decay math (pure library)
    PayoffMod.sol               — quadratic payoff computation (pure library)
    StrikeGridMod.sol           — strike validation + p_index conversion
  FciTokenVault.sol             — main vault contract
  FciLongToken.sol              — ERC-20 for LONG side (minimal, vault-only mint/burn)
  FciShortToken.sol             — ERC-20 for SHORT side (minimal, vault-only mint/burn)

test/fci-token-vault/
  unit/
    HighWaterMark.unit.t.sol    — HWM decay math tests
    Payoff.unit.t.sol           — payoff computation tests
    FciTokenVault.unit.t.sol    — vault mint/redeem tests
  fuzz/
    HighWaterMark.fuzz.t.sol    — HWM invariant fuzzing
    Payoff.fuzz.t.sol           — payoff invariant fuzzing
    FciTokenVault.fuzz.t.sol    — vault invariant fuzzing
```

---

## Chunk 1: Sub-component Libraries (HWM + Payoff)

### Task 1: Branch setup

**Files:**
- No code files — branch creation only

- [ ] **Step 1: Create branch from main**

```bash
git checkout main
git pull origin main
git checkout -b 004-fci-token-vault
```

- [ ] **Step 2: Create directory structure**

```bash
mkdir -p src/fci-token-vault/interfaces
mkdir -p src/fci-token-vault/types
mkdir -p test/fci-token-vault/unit
mkdir -p test/fci-token-vault/fuzz
```

- [ ] **Step 3: Commit scaffold**

```bash
touch src/fci-token-vault/interfaces/.gitkeep src/fci-token-vault/types/.gitkeep test/fci-token-vault/unit/.gitkeep test/fci-token-vault/fuzz/.gitkeep
git add src/fci-token-vault/ test/fci-token-vault/
git commit -m "chore(004): scaffold fci-token-vault directories"
```

---

### Task 2: HighWaterMarkMod — type + invariants (type-driven-development)

Use @type-driven-development to define the HWM type, invariants, and spec before writing implementation.

**Files:**
- Create: `src/fci-token-vault/types/HighWaterMarkMod.sol`
- Test: `test/fci-token-vault/unit/HighWaterMark.unit.t.sol`

- [ ] **Step 1: Define the type and struct**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @notice High-water mark with exponential decay for tracking peak oracle readings.
/// @dev All price values in WAD (1e18) scale. The vault converts oracle Q128 → WAD
///   at the boundary via `deltaPlusToPrice()` before calling `updateHWM()`.
struct HWM {
    uint128 maxPrice;    // decayed high-water mark (WAD, 1e18 = p_index of 1.0)
    uint64  lastUpdate;  // timestamp of last update
}
```

- [ ] **Step 2: Write failing test — decay reduces maxPrice over time**

```solidity
function test_decay_reduces_over_time() public {
    HWM memory h = HWM({maxPrice: uint128(WAD), lastUpdate: uint64(block.timestamp)});
    vm.warp(block.timestamp + 14 days); // one half-life
    uint128 decayed = applyDecay(h, uint64(block.timestamp), HALF_LIFE_14D);
    // After one half-life, decayed ≈ WAD/2
    assertApproxEqRel(uint256(decayed), WAD / 2, 0.01e18);
}
```

- [ ] **Step 3: Run test — verify it fails**

```bash
forge test --match-test test_decay_reduces_over_time -vv
```

Expected: FAIL — `applyDecay` not defined.

- [ ] **Step 4: Implement applyDecay**

```solidity
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";

uint256 constant Q128 = 1 << 128;
uint256 constant HALF_LIFE_14D = 14 days;

/// @notice Apply exponential decay to stored maxPrice.
/// @param h The HWM state.
/// @param currentTimestamp Current block.timestamp (passed in to keep function pure).
/// @param halfLife Decay half-life in seconds.
/// @return decayed The decayed maxPrice (WAD).
/// @dev Safety: exponent is always ≤ 0 (negative), so expWad returns [0, 1e18].
///   The int256 cast of the negated product is safe because max exponent magnitude
///   is ln2 × 365 days / 1 second ≈ 2.19e25, well within int256 range.
///   expWad itself is safe for all negative inputs (returns 0 for very negative values).
function applyDecay(HWM memory h, uint64 currentTimestamp, uint256 halfLife)
    pure returns (uint128 decayed)
{
    uint256 elapsed = currentTimestamp - h.lastUpdate;
    if (elapsed == 0) return h.maxPrice;

    // Compute e^(-ln2 * elapsed / halfLife) in WAD scale
    // ln2 in WAD ≈ 0.693147180559945309e18
    int256 exponent = -int256((693147180559945309 * elapsed) / halfLife);
    // expWad returns WAD-scaled result in int256; safe to cast since exponent ≤ 0 → result ∈ [0, 1e18]
    uint256 decayFactor = uint256(FixedPointMathLib.expWad(exponent));

    // maxPrice is WAD, decayFactor is WAD → (maxPrice * decayFactor) / WAD
    decayed = uint128(FixedPointMathLib.mulDiv(uint256(h.maxPrice), decayFactor, 1e18));
}
```

- [ ] **Step 5: Run test — verify it passes**

```bash
forge test --match-test test_decay_reduces_over_time -vv
```

Expected: PASS

- [ ] **Step 6: Write failing test — update takes max of decayed and current**

```solidity
function test_update_takes_max() public {
    HWM memory h = HWM({maxPrice: uint128(WAD), lastUpdate: uint64(block.timestamp)});

    // Current price below decayed max → max stays
    uint128 lowPrice = uint128(WAD / 4);
    h = updateHWM(h, lowPrice, uint64(block.timestamp), HALF_LIFE_14D);
    assertGt(h.maxPrice, lowPrice);

    // Current price above decayed max → max updates
    vm.warp(block.timestamp + 30 days);
    uint128 highPrice = uint128(WAD * 2);
    h = updateHWM(h, highPrice, uint64(block.timestamp), HALF_LIFE_14D);
    assertEq(h.maxPrice, highPrice);
}
```

- [ ] **Step 7: Implement updateHWM**

```solidity
/// @notice Update HWM with current oracle reading.
/// @param h The HWM state.
/// @param currentPrice Current p_index (WAD). Caller converts Q128→WAD before calling.
/// @param currentTimestamp Current block.timestamp.
/// @param halfLife Decay half-life in seconds.
/// @return updated The new HWM state.
function updateHWM(HWM memory h, uint128 currentPrice, uint64 currentTimestamp, uint256 halfLife)
    pure returns (HWM memory updated)
{
    uint128 decayed = applyDecay(h, currentTimestamp, halfLife);
    updated.maxPrice = currentPrice > decayed ? currentPrice : decayed;
    updated.lastUpdate = currentTimestamp;
}
```

- [ ] **Step 8: Run tests — verify all pass**

```bash
forge test --match-path "test/fci-token-vault/unit/HighWaterMark*" -vv
```

- [ ] **Step 9: Write failing test — idempotent within same block**

```solidity
function test_idempotent_same_block() public {
    HWM memory h = HWM({maxPrice: uint128(WAD), lastUpdate: uint64(block.timestamp)});
    uint128 price = uint128(WAD / 2);
    HWM memory h1 = updateHWM(h, price, uint64(block.timestamp), HALF_LIFE_14D);
    HWM memory h2 = updateHWM(h1, price, uint64(block.timestamp), HALF_LIFE_14D);
    assertEq(h1.maxPrice, h2.maxPrice);
}
```

- [ ] **Step 10: Run — verify passes (should pass with existing implementation)**

```bash
forge test --match-test test_idempotent_same_block -vv
```

- [ ] **Step 11: Commit**

```bash
git add src/fci-token-vault/types/HighWaterMarkMod.sol test/fci-token-vault/unit/HighWaterMark.unit.t.sol
git commit -m "feat(004): HighWaterMarkMod — decaying max tracker with exponential decay"
```

---

### Task 3: HighWaterMark fuzz tests — invariant verification

**Files:**
- Test: `test/fci-token-vault/fuzz/HighWaterMark.fuzz.t.sol`

- [ ] **Step 1: Write fuzz test — decay never increases**

```solidity
function testFuzz_decay_never_increases(uint128 maxPrice, uint64 elapsed) public {
    vm.assume(maxPrice > 0 && maxPrice <= uint128(WAD * 1000)); // bound to reasonable WAD range
    vm.assume(elapsed > 0 && elapsed < 365 days);

    HWM memory h = HWM({maxPrice: maxPrice, lastUpdate: uint64(block.timestamp)});
    vm.warp(block.timestamp + elapsed);
    uint128 decayed = applyDecay(h, uint64(block.timestamp), HALF_LIFE_14D);
    assertLe(decayed, maxPrice);
}
```

- [ ] **Step 2: Write fuzz test — updateHWM maxPrice ≥ currentPrice**

```solidity
function testFuzz_update_ge_current(uint128 maxPrice, uint128 currentPrice, uint64 elapsed) public {
    vm.assume(maxPrice > 0 && maxPrice <= uint128(WAD * 1000));
    vm.assume(currentPrice <= uint128(WAD * 1000));
    vm.assume(elapsed < 365 days);

    HWM memory h = HWM({maxPrice: maxPrice, lastUpdate: uint64(block.timestamp)});
    vm.warp(block.timestamp + elapsed);
    HWM memory updated = updateHWM(h, currentPrice, uint64(block.timestamp), HALF_LIFE_14D);
    assertGe(updated.maxPrice, currentPrice);
}
```

- [ ] **Step 3: Write fuzz test — HWM monotonically non-increasing between spikes (no new highs)**

```solidity
function testFuzz_hwm_monotone_between_spikes(
    uint128 maxPrice, uint64 elapsed1, uint64 elapsed2
) public {
    vm.assume(maxPrice > 0 && maxPrice <= uint128(WAD * 1000));
    vm.assume(elapsed1 > 0 && elapsed1 < 180 days);
    vm.assume(elapsed2 > 0 && elapsed2 < 180 days);

    uint64 t0 = uint64(block.timestamp);
    HWM memory h = HWM({maxPrice: maxPrice, lastUpdate: t0});

    // Two sequential decays with no new highs (currentPrice = 0)
    uint64 t1 = t0 + elapsed1;
    vm.warp(t1);
    HWM memory h1 = updateHWM(h, 0, t1, HALF_LIFE_14D);

    uint64 t2 = t1 + elapsed2;
    vm.warp(t2);
    HWM memory h2 = updateHWM(h1, 0, t2, HALF_LIFE_14D);

    assertLe(h2.maxPrice, h1.maxPrice, "HWM increased between spikes");
}
```

- [ ] **Step 4: Write fuzz test — poke idempotent within same timestamp**

```solidity
function testFuzz_poke_idempotent(uint128 maxPrice, uint128 currentPrice) public {
    vm.assume(maxPrice > 0 && maxPrice <= uint128(WAD * 1000));
    vm.assume(currentPrice <= uint128(WAD * 1000));

    uint64 t = uint64(block.timestamp);
    HWM memory h = HWM({maxPrice: maxPrice, lastUpdate: t});
    HWM memory h1 = updateHWM(h, currentPrice, t, HALF_LIFE_14D);
    HWM memory h2 = updateHWM(h1, currentPrice, t, HALF_LIFE_14D);
    assertEq(h1.maxPrice, h2.maxPrice, "poke not idempotent");
}
```

- [ ] **Step 5: Run fuzz tests**

```bash
forge test --match-path "test/fci-token-vault/fuzz/HighWaterMark*" -vv
```

Expected: PASS (256 runs each)

- [ ] **Step 6: Commit**

```bash
git add test/fci-token-vault/fuzz/HighWaterMark.fuzz.t.sol
git commit -m "test(004): HWM fuzz — decay monotonicity, update lower bound, spike monotone, poke idempotent"
```

---

### Task 4: PayoffMod — type + invariants (type-driven-development)

Use @type-driven-development to define the payoff type and spec.

**Files:**
- Create: `src/fci-token-vault/types/PayoffMod.sol`
- Test: `test/fci-token-vault/unit/Payoff.unit.t.sol`

- [ ] **Step 1: Write failing test — below strike returns zero LONG**

```solidity
function test_below_strike_zero_long() public {
    uint128 hwm = uint128(WAD / 20);    // p_index = 0.05 (WAD)
    uint128 strike = uint128(WAD / 10);  // p* = 0.10 (WAD)
    (uint256 longVal, uint256 shortVal) = computePayoff(hwm, strike);
    assertEq(longVal, 0);
    assertEq(shortVal, WAD); // 1 USDC per token (WAD-scaled)
}
```

- [ ] **Step 2: Run test — verify fails**

```bash
forge test --match-test test_below_strike_zero_long -vv
```

- [ ] **Step 3: Implement computePayoff**

```solidity
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";

uint256 constant WAD = 1e18;

/// @notice Compute per-token LONG and SHORT payoff values.
/// @dev All inputs and outputs in WAD scale (1e18). The vault converts oracle Q128 → WAD
///   via `deltaPlusToPrice()` before storing HWM. Strikes are stored in WAD at construction.
/// @param hwm Current high-water mark (WAD).
/// @param strike Strike price p* (WAD).
/// @return longPerToken LONG value in WAD (1e18 = 1 USDC).
/// @return shortPerToken SHORT value in WAD (1e18 = 1 USDC).
function computePayoff(uint128 hwm, uint128 strike)
    pure returns (uint256 longPerToken, uint256 shortPerToken)
{
    if (hwm <= strike) {
        return (0, WAD);
    }

    // ratio = hwm / strike (WAD / WAD → WAD scale)
    uint256 ratio = FixedPointMathLib.mulDiv(uint256(hwm), WAD, uint256(strike));

    // quadratic = ratio² - 1 (in WAD)
    uint256 ratioSquared = FixedPointMathLib.mulDiv(ratio, ratio, WAD);
    uint256 quadratic = ratioSquared - WAD; // safe: ratio > WAD since hwm > strike

    // Cap at WAD (1 USDC per token max)
    longPerToken = quadratic > WAD ? WAD : quadratic;
    shortPerToken = WAD - longPerToken;
}
```

- [ ] **Step 4: Run test — verify passes**

```bash
forge test --match-test test_below_strike_zero_long -vv
```

- [ ] **Step 5: Write failing test — at sqrt(2) × strike, LONG = max**

```solidity
function test_at_sqrt2_strike_max_payout() public {
    uint128 strike = uint128(WAD / 10); // p* = 0.10 (WAD)
    // hwm = strike * sqrt(2) → ratio² = 2 → quadratic = 1 → LONG = WAD
    uint128 hwm = uint128(FixedPointMathLib.mulDiv(uint256(strike), 1414213562373095049, 1e18));
    (uint256 longVal, uint256 shortVal) = computePayoff(hwm, strike);
    assertApproxEqRel(longVal, WAD, 0.001e18);
    assertApproxEqRel(shortVal, 0, 0.001e18);
}
```

- [ ] **Step 6: Run test — verify passes**

```bash
forge test --match-test test_at_sqrt2_strike_max_payout -vv
```

- [ ] **Step 7: Write failing test — LONG + SHORT = WAD always**

```solidity
function test_payoff_sum_invariant() public {
    uint128 strike = uint128(WAD / 10);
    uint128[] memory hwms = new uint128[](5);
    hwms[0] = 0;
    hwms[1] = uint128(WAD / 20);
    hwms[2] = uint128(WAD / 10);
    hwms[3] = uint128(WAD / 5);
    hwms[4] = uint128(WAD);

    for (uint256 i = 0; i < hwms.length; i++) {
        (uint256 l, uint256 s) = computePayoff(hwms[i], strike);
        assertEq(l + s, WAD, "LONG + SHORT != WAD");
    }
}
```

- [ ] **Step 8: Run all payoff tests**

```bash
forge test --match-path "test/fci-token-vault/unit/Payoff*" -vv
```

- [ ] **Step 9: Commit**

```bash
git add src/fci-token-vault/types/PayoffMod.sol test/fci-token-vault/unit/Payoff.unit.t.sol
git commit -m "feat(004): PayoffMod — power-squared payoff with LONG+SHORT=WAD invariant"
```

---

### Task 5: Payoff fuzz tests — invariant verification

**Files:**
- Test: `test/fci-token-vault/fuzz/Payoff.fuzz.t.sol`

- [ ] **Step 1: Write fuzz test — LONG + SHORT = WAD**

```solidity
function testFuzz_payoff_sum_invariant(uint128 hwm, uint128 strike) public {
    vm.assume(strike > 0);
    (uint256 l, uint256 s) = computePayoff(hwm, strike);
    assertEq(l + s, WAD, "LONG + SHORT != WAD");
}
```

- [ ] **Step 2: Write fuzz test — LONG monotonically non-decreasing in HWM**

```solidity
function testFuzz_long_monotone_in_hwm(uint128 hwm1, uint128 hwm2, uint128 strike) public {
    vm.assume(strike > 0);
    vm.assume(hwm2 >= hwm1);
    (uint256 l1,) = computePayoff(hwm1, strike);
    (uint256 l2,) = computePayoff(hwm2, strike);
    assertGe(l2, l1, "LONG not monotone in HWM");
}
```

- [ ] **Step 3: Write fuzz test — LONG = 0 when hwm ≤ strike**

```solidity
function testFuzz_long_zero_below_strike(uint128 hwm, uint128 strike) public {
    vm.assume(strike > 0);
    vm.assume(hwm <= strike);
    (uint256 l,) = computePayoff(hwm, strike);
    assertEq(l, 0, "LONG should be 0 below strike");
}
```

- [ ] **Step 4: Run fuzz tests**

```bash
forge test --match-path "test/fci-token-vault/fuzz/Payoff*" -vv
```

Expected: PASS (256 runs each)

- [ ] **Step 5: Commit**

```bash
git add test/fci-token-vault/fuzz/Payoff.fuzz.t.sol
git commit -m "test(004): payoff fuzz — sum invariant, monotonicity, zero-below-strike"
```

---

### Task 6: StrikeGridMod — p_index conversion + strike validation

**Files:**
- Create: `src/fci-token-vault/types/StrikeGridMod.sol`
- Test: `test/fci-token-vault/unit/StrikeGrid.unit.t.sol`

- [ ] **Step 1: Write failing test — deltaPlusToPrice conversion**

```solidity
function test_deltaPlus_to_price() public {
    // Δ⁺ = Q128/2 → p = (Q128/2) / (Q128 - Q128/2) = 1.0 → WAD
    uint128 delta = uint128(Q128 / 2);
    uint256 price = deltaPlusToPrice(delta);
    assertApproxEqRel(price, WAD, 0.001e18);

    // Δ⁺ = 0 → p = 0
    assertEq(deltaPlusToPrice(0), 0);
}
```

- [ ] **Step 2: Implement deltaPlusToPrice**

```solidity
/// @notice Convert raw Δ⁺ (Q128) to p_index (WAD).
/// @dev This is the ONLY Q128→WAD boundary in the vault. All downstream consumers
///   (updateHWM, computePayoff) operate purely in WAD.
///   p = Δ⁺ / (Q128 − Δ⁺), returned in WAD scale.
function deltaPlusToPrice(uint128 deltaPlus) pure returns (uint256 priceWad) {
    if (deltaPlus == 0) return 0;
    uint256 denominator = Q128 - uint256(deltaPlus);
    priceWad = FixedPointMathLib.mulDiv(uint256(deltaPlus), WAD, denominator);
}
```

- [ ] **Step 3: Run test — verify passes**

```bash
forge test --match-test test_deltaPlus_to_price -vv
```

- [ ] **Step 4: Write failing test — validateStrikes rejects unsorted/empty arrays**

```solidity
function test_validateStrikes_rejects_empty() public {
    uint128[] memory empty = new uint128[](0);
    vm.expectRevert(EmptyStrikes.selector);
    validateStrikes(empty);
}

function test_validateStrikes_rejects_unsorted() public {
    uint128[] memory bad = new uint128[](2);
    bad[0] = uint128(WAD / 5);
    bad[1] = uint128(WAD / 10); // out of order
    vm.expectRevert(StrikesNotSorted.selector);
    validateStrikes(bad);
}

function test_validateStrikes_accepts_sorted() public pure {
    uint128[] memory good = new uint128[](3);
    good[0] = uint128(WAD / 20);   // 0.05
    good[1] = uint128(WAD / 10);   // 0.10
    good[2] = uint128(WAD / 4);    // 0.25
    validateStrikes(good); // should not revert
}
```

- [ ] **Step 5: Implement validateStrikes**

```solidity
error EmptyStrikes();
error StrikesNotSorted();

/// @notice Validate that strikes array is non-empty, sorted ascending, and all > 0.
function validateStrikes(uint128[] memory strikes) pure {
    if (strikes.length == 0) revert EmptyStrikes();
    if (strikes[0] == 0) revert StrikesNotSorted();
    for (uint256 i = 1; i < strikes.length; i++) {
        if (strikes[i] <= strikes[i - 1]) revert StrikesNotSorted();
    }
}
```

- [ ] **Step 6: Run all StrikeGrid tests**

```bash
forge test --match-path "test/fci-token-vault/unit/StrikeGrid*" -vv
```

- [ ] **Step 7: Commit**

```bash
git add src/fci-token-vault/types/StrikeGridMod.sol test/fci-token-vault/unit/StrikeGrid.unit.t.sol
git commit -m "feat(004): StrikeGridMod — deltaPlusToPrice Q128→WAD + validateStrikes"
```

---

## Chunk 2: Vault Contract + ERC-20 Tokens

### Task 7: FciLongToken + FciShortToken — vault-controlled ERC-20s

**Files:**
- Create: `src/fci-token-vault/FciLongToken.sol`
- Create: `src/fci-token-vault/FciShortToken.sol`

- [ ] **Step 1: Implement FciLongToken**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {ERC20} from "solmate/tokens/ERC20.sol";

/// @notice ERC-20 for the LONG side of an FCI token vault.
/// @dev Only the vault can mint and burn.
contract FciLongToken is ERC20 {
    address public immutable vault;

    error OnlyVault();

    modifier onlyVault() {
        if (msg.sender != vault) revert OnlyVault();
        _;
    }

    constructor(string memory name_, string memory symbol_)
        ERC20(name_, symbol_, 18)
    {
        vault = msg.sender;
    }

    function mint(address to, uint256 amount) external onlyVault {
        _mint(to, amount);
    }

    function burn(address from, uint256 amount) external onlyVault {
        _burn(from, amount);
    }
}
```

- [ ] **Step 2: Implement FciShortToken (identical pattern)**

Same as FciLongToken but with "SHORT" naming.

- [ ] **Step 3: Compile**

```bash
forge build
```

- [ ] **Step 4: Commit**

```bash
git add src/fci-token-vault/FciLongToken.sol src/fci-token-vault/FciShortToken.sol
git commit -m "feat(004): FciLongToken + FciShortToken — vault-controlled ERC-20s"
```

---

### Task 8: IFciTokenVault interface

**Files:**
- Create: `src/fci-token-vault/interfaces/IFciTokenVault.sol`

- [ ] **Step 1: Define interface**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

interface IFciTokenVault {
    event Mint(address indexed depositor, uint8 strikeIndex, uint256 amount);
    event RedeemPair(address indexed redeemer, uint8 strikeIndex, uint256 amount);
    event RedeemLong(address indexed redeemer, uint8 strikeIndex, uint256 amount, uint256 payout);
    event RedeemShort(address indexed redeemer, uint8 strikeIndex, uint256 amount, uint256 payout);
    event HWMUpdated(uint8 strikeIndex, uint128 newHwm, uint128 pIndex);

    function mint(uint8 strikeIndex, uint256 usdcAmount) external;
    function redeemPair(uint8 strikeIndex, uint256 tokenAmount) external;
    function redeemLong(uint8 strikeIndex, uint256 tokenAmount) external;
    function redeemShort(uint8 strikeIndex, uint256 tokenAmount) external;
    function poke(uint8 strikeIndex) external;

    function getLongValue(uint8 strikeIndex) external view returns (uint256 perTokenWad);
    function getShortValue(uint8 strikeIndex) external view returns (uint256 perTokenWad);
    function getHWM(uint8 strikeIndex) external view returns (uint128 hwm, uint64 lastUpdate);
    function strikeCount() external view returns (uint8);
    function strikePrice(uint8 index) external view returns (uint128);
}
```

- [ ] **Step 2: Compile**

```bash
forge build
```

- [ ] **Step 3: Commit**

```bash
git add src/fci-token-vault/interfaces/IFciTokenVault.sol
git commit -m "feat(004): IFciTokenVault interface — mint, redeem, poke, view functions"
```

---

### Task 9: FciTokenVault — core implementation

**Files:**
- Create: `src/fci-token-vault/FciTokenVault.sol`
- Test: `test/fci-token-vault/unit/FciTokenVault.unit.t.sol`

- [ ] **Step 1: Write failing test — mint deposits USDC and creates tokens**

```solidity
function test_mint_creates_paired_tokens() public {
    uint256 amount = 100e6; // 100 USDC (6 decimals)
    usdc.approve(address(vault), amount);
    vault.mint(0, amount);

    assertEq(vault.longToken(0).balanceOf(address(this)), amount);
    assertEq(vault.shortToken(0).balanceOf(address(this)), amount);
    assertEq(usdc.balanceOf(address(vault)), amount);
}
```

- [ ] **Step 2: Run — verify fails**

```bash
forge test --match-test test_mint_creates_paired_tokens -vv
```

- [ ] **Step 3: Implement FciTokenVault constructor + mint**

The constructor takes: oracle address, poolKey, collateral token, strike array, halfLife. Deploys LONG+SHORT token pairs per strike.

`mint` transfers USDC from caller, mints equal LONG+SHORT.

- [ ] **Step 4: Run — verify passes**

- [ ] **Step 5: Write failing test — redeemPair returns exact USDC**

```solidity
function test_redeemPair_returns_exact_usdc() public {
    uint256 amount = 100e6;
    usdc.approve(address(vault), amount);
    vault.mint(0, amount);

    vault.longToken(0).approve(address(vault), amount);
    vault.shortToken(0).approve(address(vault), amount);
    vault.redeemPair(0, amount);

    assertEq(usdc.balanceOf(address(this)), amount); // got USDC back
    assertEq(vault.longToken(0).balanceOf(address(this)), 0);
    assertEq(vault.shortToken(0).balanceOf(address(this)), 0);
}
```

- [ ] **Step 6: Implement redeemPair**

- [ ] **Step 7: Run — verify passes**

- [ ] **Step 8: Write failing test — redeemLong pays correct payoff**

```solidity
function test_redeemLong_pays_payoff() public {
    uint256 amount = 100e6;
    usdc.approve(address(vault), amount);
    vault.mint(0, amount);

    // Simulate oracle spike above strike
    _mockOracleDeltaPlus(highDeltaPlus);
    vault.poke(0);

    uint256 longValue = vault.getLongValue(0);
    assertGt(longValue, 0);

    vault.longToken(0).approve(address(vault), amount);
    vault.redeemLong(0, amount);

    uint256 expectedPayout = FixedPointMathLib.mulDiv(amount, longValue, WAD);
    assertEq(usdc.balanceOf(address(this)), expectedPayout);
}
```

- [ ] **Step 9: Implement redeemLong + redeemShort**

- [ ] **Step 10: Run all vault tests**

```bash
forge test --match-path "test/fci-token-vault/unit/FciTokenVault*" -vv
```

- [ ] **Step 11: Write failing test — poke updates HWM from oracle**

- [ ] **Step 12: Implement poke**

- [ ] **Step 13: Run — verify passes**

- [ ] **Step 14: Commit**

```bash
git add src/fci-token-vault/FciTokenVault.sol test/fci-token-vault/unit/FciTokenVault.unit.t.sol
git commit -m "feat(004): FciTokenVault — mint, redeemPair, redeemLong, redeemShort, poke"
```

---

### Task 10: Vault fuzz tests — critical invariants

**Files:**
- Test: `test/fci-token-vault/fuzz/FciTokenVault.fuzz.t.sol`

- [ ] **Step 1: Fuzz — USDC balance ≥ totalDeposits**

```solidity
function testFuzz_vault_solvent(uint256 mintAmount, uint256 redeemAmount) public {
    mintAmount = bound(mintAmount, 1e6, 1_000_000e6);
    usdc.approve(address(vault), mintAmount);
    vault.mint(0, mintAmount);

    redeemAmount = bound(redeemAmount, 0, mintAmount);
    vault.longToken(0).approve(address(vault), redeemAmount);
    vault.shortToken(0).approve(address(vault), redeemAmount);
    vault.redeemPair(0, redeemAmount);

    assertGe(usdc.balanceOf(address(vault)), vault.totalDeposits(0));
}
```

- [ ] **Step 2: Fuzz — longSupply == shortSupply after any sequence**

- [ ] **Step 3: Fuzz — redeemPair always returns exact amount**

- [ ] **Step 4: Run fuzz suite**

```bash
forge test --match-path "test/fci-token-vault/fuzz/FciTokenVault*" -vv
```

- [ ] **Step 5: Commit**

```bash
git add test/fci-token-vault/fuzz/FciTokenVault.fuzz.t.sol
git commit -m "test(004): vault fuzz — solvency, supply parity, pair redemption"
```

---

### Task 11: Full build + all tests green

- [ ] **Step 1: Run full test suite**

```bash
forge test --match-path "test/fci-token-vault/**" -vv
```

- [ ] **Step 2: Verify no compilation warnings**

```bash
forge build 2>&1 | grep -i warning
```

- [ ] **Step 3: Final commit if any cleanup needed**

```bash
git commit -m "chore(004): cleanup and all tests green"
```
