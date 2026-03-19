# Vault Client Integration Testing — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add facet-level, integration, and adversarial tests for the FCI token vault so every function clients call is covered — including events, view functions, multi-user flows, and edge cases.

**Architecture:** Three-layer test suite. Layer 1 = facet unit tests with DeltaPlusStub (no FCI). Layer 2 = integration tests with real FCI V1 + V4 pool. Layer 3 = adversarial & composition tests. Shared infrastructure: FacetDeployer (inherits all 3 facets), DeltaPlusStub, FCIFixture (swap point for future protocols).

**Tech Stack:** Solidity ^0.8.26, Forge (forge-std), Uniswap V4 core + periphery test helpers, FCI V1 (FeeConcentrationIndexHarness), MockERC20 (solmate)

**Spec:** `docs/superpowers/specs/2026-03-17-vault-client-integration-testing-design.md`

---

### Task 1: Production Code Fix — Add settled guard to CollateralCustodianFacet.deposit()

**Files:**
- Modify: `src/fci-token-vault/facets/CollateralCustodianFacet.sol:29`

- [ ] **Step 1: Verify the bug exists**

Run: `forge inspect CollateralCustodianFacet methods`
Confirm `deposit(uint256)` has no reference to `OraclePayoffStorage` or `settled`.

- [ ] **Step 2: Add the settled guard to deposit()**

In `src/fci-token-vault/facets/CollateralCustodianFacet.sol`, add the import and guard:

```solidity
// Add to existing imports:
import {
    getOraclePayoffStorage,
    VaultAlreadySettled
} from "@fci-token-vault/storage/OraclePayoffStorage.sol";
```

Inside `deposit()`, add as the first line after `reentrancyGuardEnter()`:

```solidity
if (getOraclePayoffStorage().settled) revert VaultAlreadySettled();
```

- [ ] **Step 3: Run existing tests to verify no regressions**

Run: `forge test --match-path "test/fci-token-vault/**" -v`
Expected: All existing tests pass (the harness already has this check, so existing integration tests are unaffected).

- [ ] **Step 4: Commit**

```bash
git add src/fci-token-vault/facets/CollateralCustodianFacet.sol
git commit -m "fix: add settled guard to CollateralCustodianFacet.deposit()

Deposits post-settlement would mint tokens that can never be redeemed
via the oracle path. The harness had this check but the production
facet did not. Fixes INV-015."
```

---

### Task 2: Create DeltaPlusStub

**Files:**
- Create: `test/fci-token-vault/fixtures/DeltaPlusStub.sol`

- [ ] **Step 1: Write DeltaPlusStub**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolKey} from "v4-core/src/types/PoolKey.sol";

/// @dev Minimal stub implementing IFeeConcentrationIndex.getDeltaPlusEpoch
/// for Layer 1 vault tests. Returns a configurable uint128.
contract DeltaPlusStub {
    uint128 public deltaPlusValue;

    function setDeltaPlus(uint128 v) external {
        deltaPlusValue = v;
    }

    function getDeltaPlusEpoch(PoolKey calldata, bool) external view returns (uint128) {
        return deltaPlusValue;
    }

    // Also implement getDeltaPlus for completeness (ProtocolAdapterLib exposes both).
    function getDeltaPlus(PoolKey calldata, bool) external view returns (uint128) {
        return deltaPlusValue;
    }
}
```

- [ ] **Step 2: Verify it compiles**

Run: `forge build`
Expected: Compiles without errors (DeltaPlusStub included).

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/fixtures/DeltaPlusStub.sol
git commit -m "test: add DeltaPlusStub for Layer 1 vault poke testing"
```

---

### Task 3: Create FacetDeployer

**Files:**
- Create: `test/fci-token-vault/fixtures/FacetDeployer.sol`

- [ ] **Step 1: Write FacetDeployer**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {CollateralCustodianFacet} from "@fci-token-vault/facets/CollateralCustodianFacet.sol";
import {OraclePayoffFacet} from "@fci-token-vault/facets/OraclePayoffFacet.sol";
import {ERC20WrapperFacade, WRAPPER_STORAGE_POSITION_SEED} from "@fci-token-vault/tokens/ERC20WrapperFacade.sol";
import {getCustodianStorage, CustodianStorage} from "@fci-token-vault/storage/CustodianStorage.sol";
import {getOraclePayoffStorage, OraclePayoffStorage} from "@fci-token-vault/storage/OraclePayoffStorage.sol";
import {protocolAdapterStorage, ProtocolAdapterStorage} from "@protocol-adapter/storage/ProtocolAdapterStorage.sol";
import {erc6909Mint, getERC6909Storage} from "@fci-token-vault/modules/dependencies/ERC6909Lib.sol";
import {getERC20Storage} from "@fci-token-vault/modules/dependencies/ERC20Lib.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";

/// @dev Test deployer that inherits all three vault facets so they share
/// one address and one diamond storage context. NOT a diamond proxy.
/// Used by all three test layers.
contract FacetDeployer is CollateralCustodianFacet, OraclePayoffFacet, ERC20WrapperFacade {

    /// @dev Initialize all diamond storage slots for testing.
    /// @param collateralToken USDC address (or MockERC20)
    /// @param depositCap 0 = unlimited
    /// @param sqrtPriceStrike Strike price in sqrtPriceX96
    /// @param expiry Vault expiry timestamp
    /// @param adapterSlot Diamond storage slot for ProtocolAdapterStorage
    /// @param fciEntryPoint DeltaPlusStub (L1) or real FCI hook (L2/L3)
    /// @param poolKey PoolKey for adapter (dummy for L1, real for L2/L3)
    /// @param reactive False for L1/V4 native, true for V3 reactive
    function init(
        address collateralToken,
        uint128 depositCap,
        uint160 sqrtPriceStrike,
        uint256 expiry,
        bytes32 adapterSlot,
        address fciEntryPoint,
        PoolKey calldata poolKey,
        bool reactive
    ) external {
        // Seed CustodianStorage
        CustodianStorage storage cs = getCustodianStorage();
        cs.collateralToken = collateralToken;
        cs.depositCap = depositCap;

        // Seed OraclePayoffStorage
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        os.sqrtPriceStrike = sqrtPriceStrike;
        os.expiry = expiry;
        os.adapterSlot = adapterSlot;

        // Seed ProtocolAdapterStorage at the adapter slot
        ProtocolAdapterStorage storage adapter = protocolAdapterStorage(adapterSlot);
        adapter.fciEntryPoint = IHooks(fciEntryPoint);
        adapter.poolKey = poolKey;
        adapter.reactive = reactive;
    }

    /// @dev Set the wrapped token ID for ERC20WrapperFacade testing.
    function initWrappedTokenId(uint256 tokenId) external {
        bytes32 slot = bytes32(WRAPPER_STORAGE_POSITION_SEED);
        assembly {
            sstore(slot, tokenId)
        }
    }

    /// @dev Mint ERC-6909 tokens directly (for test setup, bypasses custodian).
    function mintERC6909(address to, uint256 id, uint256 amount) external {
        erc6909Mint(to, id, amount);
    }

    /// @dev Read ERC-6909 balance (convenience for assertions).
    function erc6909BalanceOf(address owner, uint256 id) external view returns (uint256) {
        return getERC6909Storage().balanceOf[owner][id];
    }

    /// @dev Read ERC-20 balance (convenience for assertions).
    function erc20BalanceOf(address owner) external view returns (uint256) {
        return getERC20Storage().balanceOf[owner];
    }

    /// @dev Read vault storage (convenience for assertions).
    function getVaultStorage() external view returns (
        uint160 sqrtPriceStrike_,
        uint160 sqrtPriceHWM,
        uint256 expiry_,
        bool settled,
        uint256 longPayoutPerToken
    ) {
        OraclePayoffStorage storage os = getOraclePayoffStorage();
        return (os.sqrtPriceStrike, os.sqrtPriceHWM, os.expiry, os.settled, os.longPayoutPerToken);
    }

    /// @dev Force-set HWM for testing edge cases.
    function setHWM(uint160 hwm) external {
        getOraclePayoffStorage().sqrtPriceHWM = hwm;
    }

    /// @dev Receive ETH (needed if tests send ETH).
    receive() external payable {}
}
```

- [ ] **Step 2: Verify it compiles**

Run: `forge build`
Expected: Compiles without errors. No function selector collisions (all three facets have distinct selectors).

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/fixtures/FacetDeployer.sol
git commit -m "test: add FacetDeployer — inherits all 3 vault facets for integration testing"
```

---

### Task 4: Layer 1 — CollateralCustodianFacet Tests

**Files:**
- Create: `test/fci-token-vault/facet/CollateralCustodianFacet.t.sol`
- Read: `src/fci-token-vault/facets/CollateralCustodianFacet.sol`
- Read: `src/fci-token-vault/modules/CollateralCustodianMod.sol`
- Read: `src/fci-token-vault/storage/CustodianStorage.sol`
- Read: `src/fci-token-vault/storage/OraclePayoffStorage.sol`

This task creates 10 tests covering the CollateralCustodianFacet external API.

**Key references:**
- `LONG = 0`, `SHORT = 1` from `CollateralCustodianMod.sol:18-19`
- Events: `PairedMint(address indexed, uint256)`, `PairedBurn(address indexed, uint256)`
- Errors: `ZeroAmount`, `DepositCapExceeded`, `ReentrancyGuardReentrant`, `VaultAlreadySettled`

- [ ] **Step 1: Write the test file with setUp and all 10 tests**

The test deploys `FacetDeployer`, calls `init()` with a `DeltaPlusStub` for the adapter, funds alice with MockERC20, and tests each facet function. Each test asserts events via `vm.expectEmit`, checks balances via `vault.balanceOf()` and `vault.totalDeposited()`, and verifies USDC transfers via MockERC20 balance changes.

Tests to write (reference spec lines 42-52):
1. `test_deposit_mints_pair_and_transfers_usdc`
2. `test_redeemPair_burns_and_transfers_usdc`
3. `test_previewDeposit_returns_equal_amounts`
4. `test_balanceOf_reads_erc6909`
5. `test_deposit_zero_reverts`
6. `test_redeemPair_zero_reverts`
7. `test_deposit_exceeds_cap_reverts`
8. `test_deposit_reentrancy_reverts`
9. `test_redeemPair_reentrancy_reverts`
10. `test_redeemPair_after_settle_succeeds`

For reentrancy tests: create a `ReentrancyAttacker` contract that calls `vault.deposit()` or `vault.redeemPair()` from a fallback triggered by USDC transfer. Use a MockERC20 that calls back on `transfer`.

- [ ] **Step 2: Run tests to verify they pass**

Run: `forge test --match-path "test/fci-token-vault/facet/CollateralCustodianFacet.t.sol" -vv`
Expected: All 10 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/facet/CollateralCustodianFacet.t.sol
git commit -m "test(L1): CollateralCustodianFacet — 10 facet-level tests

Covers deposit, redeemPair, previewDeposit, balanceOf, zero-amount
reverts, cap enforcement, reentrancy guard, and post-settlement
redeemPair (intentionally allowed)."
```

---

### Task 5: Layer 1 — OraclePayoffFacet Tests

**Files:**
- Create: `test/fci-token-vault/facet/OraclePayoffFacet.t.sol`
- Read: `src/fci-token-vault/facets/OraclePayoffFacet.sol`
- Read: `src/fci-token-vault/modules/OraclePayoffMod.sol`
- Read: `src/fci-token-vault/storage/OraclePayoffStorage.sol`
- Read: `src/fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol`

This task creates 18 tests covering the OraclePayoffFacet external API.

**Key references:**
- Events: `HWMUpdated(uint160, uint160)`, `OracleSettlement(uint256, uint160)`, `RedeemLong(address indexed, uint256, uint256)`, `RedeemShort(address indexed, uint256, uint256)`
- Errors: `VaultNotExpired`, `VaultAlreadySettled`, `VaultAlreadySettledPoke`, `VaultNotSettled`, `ZeroAmount`
- `Q96 = SqrtPriceLibrary.Q96` from `foundational-hooks/src/libraries/SqrtPriceLibrary.sol`
- DeltaPlusStub wired into adapter slot for `poke()` testing

- [ ] **Step 1: Write the test file with setUp and all 18 tests**

The test deploys `FacetDeployer` + `DeltaPlusStub`, deposits via the custodian facet to create LONG/SHORT tokens, then tests the oracle payoff facet. For settlement tests: set DeltaPlusStub value → poke → `vm.warp` past expiry → settle.

Tests to write (reference spec lines 57-75):
1. `test_poke_emits_hwm_updated` — set stub to 1e18, call poke, assert HWMUpdated event
2. `test_poke_updates_hwm_monotonically` — poke with increasing values, verify HWM only goes up
3. `test_poke_zero_delta_plus_hwm_unchanged` — stub returns 0, verify no HWM change
4. `test_settle_emits_settlement` — warp past expiry, settle, assert OracleSettlement event + isSettled()
5. `test_payoffRatio_sums_to_Q96` — settle, verify longPerToken + shortPerToken == Q96
6. `test_redeemLong_burns_and_pays` — settle, redeemLong, verify LONG balance 0, SHORT unchanged, USDC payout, event
7. `test_redeemShort_burns_and_pays` — settle, redeemShort, verify SHORT balance 0, LONG unchanged, USDC payout, event
8. `test_previewLongPayout_matches_actual` — settle, preview then redeem, compare amounts
9. `test_previewShortPayout_matches_actual` — settle, preview then redeem, compare amounts
10. `test_settle_before_expiry_reverts` — VaultNotExpired
11. `test_redeemLong_before_settle_reverts` — VaultNotSettled
12. `test_redeemShort_before_settle_reverts` — VaultNotSettled
13. `test_poke_after_settle_reverts` — VaultAlreadySettledPoke
14. `test_previewLongPayout_before_settle_reverts` — VaultNotSettled
15. `test_previewShortPayout_before_settle_reverts` — VaultNotSettled
16. `test_payoffRatio_before_settle_reverts` — VaultNotSettled
17. `test_redeemLong_zero_reverts` — ZeroAmount
18. `test_redeemShort_zero_reverts` — ZeroAmount

- [ ] **Step 2: Run tests to verify they pass**

Run: `forge test --match-path "test/fci-token-vault/facet/OraclePayoffFacet.t.sol" -vv`
Expected: All 18 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/facet/OraclePayoffFacet.t.sol
git commit -m "test(L1): OraclePayoffFacet — 17 facet-level tests

Covers poke (HWM update, monotonicity, zero delta-plus), settle,
payoffRatio, redeemLong/Short (burns, payouts, events, preview match),
and all revert conditions (pre-settle, post-settle, zero amount).
18 test functions total."
```

---

### Task 6: Layer 1 — ERC20WrapperFacade Tests

**Files:**
- Create: `test/fci-token-vault/facet/ERC20WrapperFacade.t.sol`
- Read: `src/fci-token-vault/tokens/ERC20WrapperFacade.sol`
- Read: `src/fci-token-vault/modules/dependencies/ERC6909Lib.sol`
- Read: `src/fci-token-vault/modules/dependencies/ERC20Lib.sol`

This task creates 4 tests covering the ERC20WrapperFacade. Note: existing unit tests at `test/fci-token-vault/unit/ERC20WrapperFacade.t.sol` test through a `WrapperHarness`. These new tests are additive (Design Decision 6) and test through the `FacetDeployer` to exercise the real facet in a shared-storage context.

**Key references:**
- `getWrappedTokenId()` reads from `WRAPPER_STORAGE_POSITION_SEED` slot
- `InsufficientERC6909Balance(address, uint256, uint256, uint256)` error
- `ERC20InsufficientBalance(address, uint256, uint256)` from ERC20Lib

- [ ] **Step 1: Write the test file with setUp and 4 tests**

Tests (reference spec lines 80-84):
1. `test_wrap_converts_6909_to_erc20` — mint ERC-6909 via deployer, wrap, check both balances
2. `test_unwrap_converts_erc20_to_6909` — wrap then unwrap, check both balances
3. `test_wrap_insufficient_balance_reverts` — wrap more than balance, expect InsufficientERC6909Balance
4. `test_unwrap_insufficient_erc20_reverts` — unwrap more than ERC-20 balance, expect ERC20InsufficientBalance

Setup uses `FacetDeployer.initWrappedTokenId(0)` (LONG token) and `FacetDeployer.mintERC6909()` to seed balances.

- [ ] **Step 2: Run tests to verify they pass**

Run: `forge test --match-path "test/fci-token-vault/facet/ERC20WrapperFacade.t.sol" -vv`
Expected: All 4 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/facet/ERC20WrapperFacade.t.sol
git commit -m "test(L1): ERC20WrapperFacade — 4 facet-level tests

Covers wrap, unwrap, insufficient ERC-6909 revert, insufficient ERC-20 revert."
```

---

### Task 7: Create FCIFixture

**Files:**
- Create: `test/fci-token-vault/fixtures/FCIFixture.sol`
- Read: `test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol` (reference for setup pattern)
- Read: `test/fee-concentration-index/helpers/FCITestHelper.sol`

This is the swap point for protocol backends. Encapsulates FCI V1 + V4 + FacetDeployer setup.

- [ ] **Step 1: Write FCIFixture**

The fixture extends `PosmTestSetup` and `FCITestHelper`. It:
1. Deploys V4 infrastructure (manager, routers, currencies, posm)
2. Deploys FCI V1 hook via HookMiner
3. Initializes pool and epoch
4. Deploys FacetDeployer and calls `init()` with real FCI as `fciEntryPoint`
5. Exposes helpers: `runJitRound()`, `setupLP()`, `setupSwapper()`, `depositToVault()`, `pokeVault()`, `settleVault()`

Pattern follows existing `HedgedVsUnhedged.integration.t.sol` setUp but is reusable.

- [ ] **Step 2: Verify it compiles**

Run: `forge build`
Expected: Compiles without errors.

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/fixtures/FCIFixture.sol
git commit -m "test: add FCIFixture — swap point for vault integration tests

Encapsulates FCI V1 + V4 pool + FacetDeployer setup. Layer 2/3 tests
inherit from this. New protocol backends (V2, V3 reactive) create a
new fixture with the same helper interface."
```

---

### Task 8: Layer 2 — SingleUserLifecycle Integration Test

**Files:**
- Create: `test/fci-token-vault/integration/SingleUserLifecycle.integration.t.sol`
- Read: `test/fci-token-vault/fixtures/FCIFixture.sol`

Full single-user lifecycle through the actual facet API with real FCI V1.

- [ ] **Step 1: Write the test**

The test inherits FCIFixture and exercises the complete lifecycle:
deposit → JIT rounds → poke per epoch → warp → settle → verify views → redeem → conservation.

Reference spec lines 90-102 for the exact flow.

Key assertions:
- `HWMUpdated` event emitted with real non-zero sqrtPrice after JIT rounds
- `isSettled()` transitions from false to true
- `payoffRatio()` returns valid Q96 values
- `previewLongPayout(amount)` matches actual USDC from `redeemLong(amount)`
- `totalDeposited()` decreases by correct payout amounts
- `longPayout + shortPayout == depositAmount` (conservation, allowing 1 wei rounding dust)

- [ ] **Step 2: Run test**

Run: `forge test --match-path "test/fci-token-vault/integration/SingleUserLifecycle.integration.t.sol" -vv`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/integration/SingleUserLifecycle.integration.t.sol
git commit -m "test(L2): SingleUserLifecycle — full facet-level lifecycle with real FCI

deposit → 3 JIT rounds → poke per epoch → settle → verify views →
redeemLong + redeemShort → conservation. All through actual facet API."
```

---

### Task 9: Layer 2 — MultiUserLifecycle Integration Test

**Files:**
- Create: `test/fci-token-vault/integration/MultiUserLifecycle.integration.t.sol`
- Read: `test/fci-token-vault/fixtures/FCIFixture.sol`

Multi-user flows with real FCI V1.

- [ ] **Step 1: Write the test**

Reference spec lines 104-115. Key tests:
1. `test_multi_user_deposit_and_total` — Alice 100e6, Bob 200e6, totalDeposited == 300e6
2. `test_multi_user_independent_redemption` — Alice redeems LONG, Bob redeems SHORT, vault stays solvent
3. `test_multi_user_cross_solvency` — All users redeem everything, totalDeposited == 0. Per-user conservation: Alice's longPayout + shortPayout == 100e6 (if she held both), Bob's == 200e6 (allowing 1 wei rounding dust per user).
4. `test_partial_redemption_ordering` — Alice redeems 50e6 LONG twice == same as 100e6 at once

- [ ] **Step 2: Run tests**

Run: `forge test --match-path "test/fci-token-vault/integration/MultiUserLifecycle.integration.t.sol" -vv`
Expected: All PASS.

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/integration/MultiUserLifecycle.integration.t.sol
git commit -m "test(L2): MultiUserLifecycle — multi-user deposit, redemption, solvency

Tests independent redemption, cross-user solvency (totalDeposited→0),
and partial redemption ordering with real FCI V1."
```

---

### Task 10: Layer 3 — VaultLifecycleGuards

**Files:**
- Create: `test/fci-token-vault/adversarial/VaultLifecycleGuards.t.sol`
- Read: `test/fci-token-vault/fixtures/FCIFixture.sol`

- [ ] **Step 1: Write the test**

Reference spec lines 119-127. Three tests that require real FCI or cross-facet composition:
1. `test_deposit_after_settle_reverts` — deposit → poke → settle → deposit again → VaultAlreadySettled
2. `test_settle_twice_reverts` — settle with real FCI HWM → second settle → VaultAlreadySettled
3. `test_full_lifecycle_state_transitions` — complete traversal verifying `isSettled()` at each step

- [ ] **Step 2: Run tests**

Run: `forge test --match-path "test/fci-token-vault/adversarial/VaultLifecycleGuards.t.sol" -vv`
Expected: All 3 PASS.

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/adversarial/VaultLifecycleGuards.t.sol
git commit -m "test(L3): VaultLifecycleGuards — deposit-after-settle, settle-twice, state transitions"
```

---

### Task 11: Layer 3 — EdgeCasePayoffs

**Files:**
- Create: `test/fci-token-vault/adversarial/EdgeCasePayoffs.t.sol`
- Read: `test/fci-token-vault/fixtures/FCIFixture.sol`

- [ ] **Step 1: Write the test**

Reference spec lines 129-139. Five edge case tests:
1. `test_zero_hwm_settlement` — no pokes → settle → longPayoutPerToken == 0, SHORT gets everything
2. `test_hwm_at_strike` — poke with sqrtPrice == strike → payoff == 0
3. `test_maximum_delta_plus` — extreme JIT capital → payoff caps at Q96
4. `test_poke_with_zero_delta_plus` — no pool activity → HWM unchanged
5. `test_single_sided_solvency` — Alice holds only LONG (transferred SHORT to Bob via ERC-6909 operator), Bob holds only SHORT. Both redeem successfully. totalDeposited() ends at 0. (INV-014)

For test 5: use `FacetDeployer.mintERC6909()` to simulate the off-chain transfer, or use ERC-6909 `transferFrom` if available. Since ERC-6909 transfer isn't on the facet, use the deployer's direct mint to set up the imbalanced state: deposit as Alice → mint extra SHORT to Bob and burn Alice's SHORT via deployer helpers.

- [ ] **Step 2: Run tests**

Run: `forge test --match-path "test/fci-token-vault/adversarial/EdgeCasePayoffs.t.sol" -vv`
Expected: All 5 PASS.

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/adversarial/EdgeCasePayoffs.t.sol
git commit -m "test(L3): EdgeCasePayoffs — zero HWM, strike boundary, cap, zero delta-plus, INV-014 solvency"
```

---

### Task 12: Layer 3 — WrapRedeemComposition

**Files:**
- Create: `test/fci-token-vault/adversarial/WrapRedeemComposition.t.sol`
- Read: `test/fci-token-vault/fixtures/FacetDeployer.sol`

- [ ] **Step 1: Write the test**

Reference spec lines 141-149. Three composition tests. These can use Layer 1 setup (FacetDeployer + DeltaPlusStub, no FCIFixture needed) since they test cross-facet composition, not FCI integration.

1. `test_deposit_wrap_transfer_unwrap_redeem` — Alice deposits → wraps LONG → transfers ERC-20 to Bob (via deployer's ERC-20 transfer helper or direct storage manipulation) → Bob unwraps → settle → Bob redeems LONG. Verifies the full ERC-20 wrapper flow ends in correct USDC payout.

2. `test_wrap_unwrap_roundtrip` — deposit → wrap → unwrap → balances identical to pre-wrap

3. `test_redeem_with_wrapped_tokens_fails` — deposit → wrap all LONG → attempt redeemLong → reverts (ERC-6909 balance is 0 after wrapping)

- [ ] **Step 2: Run tests**

Run: `forge test --match-path "test/fci-token-vault/adversarial/WrapRedeemComposition.t.sol" -vv`
Expected: All 3 PASS.

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/adversarial/WrapRedeemComposition.t.sol
git commit -m "test(L3): WrapRedeemComposition — wrap/transfer/unwrap/redeem, roundtrip, wrapped-redeem-fails"
```

---

### Task 13: Run Full Suite and Verify Coverage

- [ ] **Step 1: Run all new tests**

Run: `forge test --match-path "test/fci-token-vault/facet/**" -v && forge test --match-path "test/fci-token-vault/integration/SingleUserLifecycle*" -v && forge test --match-path "test/fci-token-vault/integration/MultiUserLifecycle*" -v && forge test --match-path "test/fci-token-vault/adversarial/**" -v`

Expected: All tests pass across all three layers.

- [ ] **Step 2: Run existing tests to verify no regressions**

Run: `forge test --match-path "test/fci-token-vault/**" -v`

Expected: All existing tests (unit/, fuzz/, kontrol/, integration/) still pass alongside new tests.

- [ ] **Step 3: Final commit (if any fixups needed)**

Only if Step 1 or 2 revealed issues that required fixes.
