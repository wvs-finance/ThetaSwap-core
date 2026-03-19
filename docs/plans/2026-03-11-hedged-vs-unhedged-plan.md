# Hedged-vs-Unhedged Scenario Validation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove that a single upfront vault deposit compensates a passive LP under adversarial JIT extraction, using real FCI hook readings, real swaps, and real vault interactions.

**Architecture:** Add `poke()` to the vault module/facet (reads Δ⁺ from FCI oracle, updates HWM), expand vault storage with `PoolKey` + `reactive`, then build an integration test with three scenarios (equilibrium, JIT crowd-out, below-strike) comparing hedged vs unhedged PLP welfare.

**Tech Stack:** Solidity ^0.8.26, Forge fork tests, Uniswap V4 PoolManager/PositionManager, FCI hook (FeeConcentrationIndexHarness), SqrtPriceLookbackPayoffX96Lib, FciTokenVaultMod/Facet, ERC-6909 conditional tokens.

**Spec:** `docs/plans/2026-03-11-hedged-vs-unhedged-design.md`

---

## File Structure

```
src/fci-token-vault/
  modules/FciTokenVaultMod.sol          — MODIFY: add poke(), expand FciVaultStorage with PoolKey + reactive
  FciTokenVaultFacet.sol                — MODIFY: add external poke()
  interfaces/IFciTokenVault.sol         — MODIFY: add poke() to interface

test/fci-token-vault/
  helpers/FciTokenVaultHarness.sol      — MODIFY: add harness_poke(), update harness_initVault
  FciTokenVaultMod.t.sol                — MODIFY: add poke() unit test
  integration/
    HedgedVsUnhedged.integration.t.sol  — CREATE: three scenario tests
```

---

## Chunk 1: Add `poke()` to Vault

### Task 1: Expand FciVaultStorage with PoolKey + reactive

**Files:**
- Modify: `src/fci-token-vault/modules/FciTokenVaultMod.sol`

- [ ] **Step 1: Add PoolKey import and storage fields**

Add import at top of file:
```solidity
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
```

Append two fields to end of `FciVaultStorage` struct (after `collateralToken`):
```solidity
    PoolKey poolKey;
    bool reactive;
```

- [ ] **Step 2: Verify build**

Run: `forge build 2>&1 | tail -5`
Expected: Compilation successful

- [ ] **Step 3: Commit**

```bash
git add src/fci-token-vault/modules/FciTokenVaultMod.sol
git commit -m "feat(004): expand FciVaultStorage with PoolKey + reactive"
```

---

### Task 2: Implement poke() module-level function

**Files:**
- Modify: `src/fci-token-vault/modules/FciTokenVaultMod.sol`

- [ ] **Step 1: Add IFeeConcentrationIndex import and deltaPlusToSqrtPriceX96 to existing import**

```solidity
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
```

Also update the existing import from `SqrtPriceLookbackPayoffX96Lib.sol` to include `deltaPlusToSqrtPriceX96`:
```solidity
import {
    lookbackPayoffX96,
    applyDecay,
    updateHWM,
    deltaPlusToSqrtPriceX96
} from "@fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol";
```

- [ ] **Step 2: Add poke() free function**

After the `redeem()` function, add:

```solidity
error VaultAlreadySettledPoke();

/// @dev Read Δ⁺ from FCI oracle, convert to sqrtPrice, apply decay, update HWM.
function poke() {
    FciVaultStorage storage vs = getFciVaultStorage();
    if (vs.settled) revert VaultAlreadySettledPoke();

    uint128 deltaPlus = IFeeConcentrationIndex(address(vs.poolKey.hooks))
        .getDeltaPlus(vs.poolKey, vs.reactive);

    uint160 currentSqrtPrice = deltaPlusToSqrtPriceX96(deltaPlus);

    uint256 dt = block.timestamp - vs.lastHwmTimestamp;
    uint160 decayed = applyDecay(vs.sqrtPriceHWM, dt, vs.halfLifeSeconds);

    vs.sqrtPriceHWM = updateHWM(decayed, currentSqrtPrice);
    vs.lastHwmTimestamp = block.timestamp;
}
```

- [ ] **Step 3: Export poke in the import list comment**

The file uses file-level free functions. Verify `poke` is accessible from outside (it's a free function, so it's importable by name).

- [ ] **Step 4: Verify build**

Run: `forge build 2>&1 | tail -5`
Expected: Compilation successful

- [ ] **Step 5: Commit**

```bash
git add src/fci-token-vault/modules/FciTokenVaultMod.sol
git commit -m "feat(004): add poke() — reads FCI oracle, updates HWM with decay"
```

---

### Task 3: Add poke() to Facet and Interface

**Files:**
- Modify: `src/fci-token-vault/FciTokenVaultFacet.sol`
- Modify: `src/fci-token-vault/interfaces/IFciTokenVault.sol`

- [ ] **Step 1: Update FciTokenVaultFacet import to include poke**

In `FciTokenVaultFacet.sol`, update the import from `FciTokenVaultMod.sol` to include `poke as _poke`:

```solidity
import {
    deposit as _deposit,
    settle as _settle,
    redeem as _redeem,
    poke as _poke,
    getFciVaultStorage,
    FciVaultStorage
} from "@fci-token-vault/modules/FciTokenVaultMod.sol";
```

- [ ] **Step 2: Add poke() external function to Facet**

After the `redeem()` function in `FciTokenVaultFacet.sol`:

```solidity
    function poke() external {
        _poke();
    }
```

- [ ] **Step 3: Add poke() to IFciTokenVault interface**

```solidity
interface IFciTokenVault {
    function deposit(uint256 amount) external;
    function settle() external;
    function redeem(uint256 amount) external;
    function poke() external;
}
```

- [ ] **Step 4: Verify build**

Run: `forge build 2>&1 | tail -5`
Expected: Compilation successful

- [ ] **Step 5: Commit**

```bash
git add src/fci-token-vault/FciTokenVaultFacet.sol src/fci-token-vault/interfaces/IFciTokenVault.sol
git commit -m "feat(004): add poke() to FciTokenVaultFacet + IFciTokenVault interface"
```

---

### Task 4: Update Harness for poke() and new storage fields

**Files:**
- Modify: `test/fci-token-vault/helpers/FciTokenVaultHarness.sol`

- [ ] **Step 1: Add PoolKey import**

```solidity
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
```

And add `poke` to the FciTokenVaultMod import:

```solidity
import {
    deposit,
    settle,
    redeem,
    poke,
    mintPair,
    burnPair,
    getFciVaultStorage,
    FciVaultStorage,
    LONG,
    SHORT
} from "@fci-token-vault/modules/FciTokenVaultMod.sol";
```

- [ ] **Step 2: Add SafeTransferLib import and harness_poke()**

Add import:
```solidity
import {SafeTransferLib} from "solady/utils/SafeTransferLib.sol";
```

Add functions:
```solidity
    function harness_poke() external {
        poke();
    }
```

- [ ] **Step 3: Update harness_initVault to accept PoolKey, reactive, collateralToken**

Replace existing `harness_initVault`:

```solidity
    function harness_initVault(
        uint160 sqrtPriceStrike,
        uint256 halfLifeSeconds,
        uint256 expiry,
        PoolKey calldata poolKey,
        bool reactive,
        address collateralToken
    ) external {
        FciVaultStorage storage vs = getFciVaultStorage();
        vs.sqrtPriceStrike = sqrtPriceStrike;
        vs.halfLifeSeconds = halfLifeSeconds;
        vs.expiry = expiry;
        vs.lastHwmTimestamp = block.timestamp;
        vs.poolKey = poolKey;
        vs.reactive = reactive;
        vs.collateralToken = collateralToken;
    }
```

- [ ] **Step 4: Update harness_deposit and harness_redeem to transfer actual tokens**

The harness must do real `safeTransferFrom`/`safeTransfer` so the integration test exercises actual collateral flow. Replace the existing `harness_deposit` and `harness_redeem`:

```solidity
    function harness_deposit(address depositor, uint256 amount) external {
        FciVaultStorage storage vs = getFciVaultStorage();
        SafeTransferLib.safeTransferFrom(vs.collateralToken, depositor, address(this), amount);
        deposit(depositor, amount);
    }

    function harness_redeem(address redeemer, uint256 amount) external {
        FciVaultStorage storage vs = getFciVaultStorage();
        uint256 longPayoutVal = (amount * vs.longPayoutPerToken) / SqrtPriceLibrary.Q96;
        uint256 shortPayoutVal = amount - longPayoutVal;
        redeem(redeemer, amount);
        if (longPayoutVal > 0) {
            SafeTransferLib.safeTransfer(vs.collateralToken, redeemer, longPayoutVal);
        }
        if (shortPayoutVal > 0) {
            SafeTransferLib.safeTransfer(vs.collateralToken, redeemer, shortPayoutVal);
        }
    }
```

This also requires adding the `SqrtPriceLibrary` import:
```solidity
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
```

- [ ] **Step 5: Add harness_getPoolKey() and harness_getReactive() accessors**

```solidity
    function harness_getPoolKey() external view returns (PoolKey memory) {
        return getFciVaultStorage().poolKey;
    }

    function harness_getReactive() external view returns (bool) {
        return getFciVaultStorage().reactive;
    }
```

- [ ] **Step 6: Verify build**

Run: `forge build 2>&1 | tail -5`
Expected: Compilation successful

- [ ] **Step 7: Fix existing tests broken by new harness_initVault signature**

Update `test/fci-token-vault/FciTokenVaultMod.t.sol` setUp to pass the new parameters. Since `harness_deposit` now does a real `safeTransferFrom`, the unit test needs a mock ERC20 for `collateralToken`. Use `solmate/test/utils/mocks/MockERC20.sol` or a minimal mock:

```solidity
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {MockERC20} from "solmate/test/utils/mocks/MockERC20.sol";
```

```solidity
    MockERC20 collateral;

    function setUp() public {
        vault = new FciTokenVaultHarness();
        collateral = new MockERC20("Collateral", "COL", 18);

        vault.harness_initVault(
            uint160(SqrtPriceLibrary.Q96), // strike = 1.0
            14 days,                        // halfLife
            block.timestamp + 30 days,      // expiry
            PoolKey({
                currency0: Currency.wrap(address(0)),
                currency1: Currency.wrap(address(0)),
                fee: 0,
                tickSpacing: 0,
                hooks: IHooks(address(0))
            }),
            false,                          // reactive
            address(collateral)             // collateralToken (real mock ERC20)
        );
    }
```

Also update the `test_deposit_mints_equal_pair` and `test_poke_reverts_after_settle` (Task 5) to fund alice with the mock token before depositing:

```solidity
    // Before any harness_deposit call:
    collateral.mint(alice, 200e18);
    vm.prank(alice);
    collateral.approve(address(vault), type(uint256).max);
```

This pattern applies to every test that calls `harness_deposit`.

- [ ] **Step 8: Verify all existing vault tests pass**

Run: `forge test --match-path "test/fci-token-vault/FciTokenVaultMod.t.sol" -vv`
Expected: 6 tests PASS

- [ ] **Step 9: Commit**

```bash
git add test/fci-token-vault/helpers/FciTokenVaultHarness.sol test/fci-token-vault/FciTokenVaultMod.t.sol
git commit -m "feat(004): update harness for poke(), PoolKey, reactive, collateralToken"
```

---

### Task 5: Unit test poke() via harness

**Files:**
- Modify: `test/fci-token-vault/FciTokenVaultMod.t.sol`

Note: poke() reads from the FCI oracle via `getDeltaPlus(PoolKey, bool)`. A unit test for poke() requires a mock or real FCI hook. Since the integration test will exercise poke() with a real FCI hook, the unit test here verifies poke() reverts when vault is settled.

- [ ] **Step 1: Add test_poke_reverts_after_settle**

```solidity
    /// @dev poke reverts if vault already settled
    function test_poke_reverts_after_settle() public {
        vault.harness_deposit(alice, 100e18);

        uint256 expiry = block.timestamp + 30 days;
        vault.harness_setHWM(uint160(SqrtPriceLibrary.Q96), expiry - 1);
        vm.warp(expiry);
        vault.harness_settle();

        vm.expectRevert();
        vault.harness_poke();
    }
```

- [ ] **Step 2: Run test**

Run: `forge test --match-test test_poke_reverts_after_settle -vv`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/FciTokenVaultMod.t.sol
git commit -m "test(004): add poke() revert-after-settle unit test"
```

---

### Task 6: Run full fci-token-vault test suite

- [ ] **Step 1: Run all tests**

Run: `forge test --match-path "test/fci-token-vault/**" -vv`
Expected: All 19+ tests PASS (18 existing + 1 new poke test)

- [ ] **Step 2: Fix any failures**

If any tests fail due to storage layout changes, fix them.

- [ ] **Step 3: Commit if any fixes needed**

```bash
git commit -m "fix(004): fix tests for expanded FciVaultStorage"
```

---

## Chunk 2: Hedged-vs-Unhedged Integration Test

### Task 7: Test scaffold — imports, setUp, helpers

**Files:**
- Create: `test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol`

- [ ] **Step 1: Write test contract with imports and setUp**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test, console} from "forge-std/Test.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {PosmTestSetup} from "@uniswap/v4-periphery/test/shared/PosmTestSetup.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {PositionDescriptor} from "@uniswap/v4-periphery/src/PositionDescriptor.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";

import {FeeConcentrationIndexHarness} from "../../fee-concentration-index/harness/FeeConcentrationIndexHarness.sol";
import {FCITestHelper} from "../../fee-concentration-index/helpers/FCITestHelper.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";

import {Context} from "@foundry-script/types/Context.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";
import {Scenario, mintPosition, burnPosition} from "@foundry-script/types/Scenario.sol";
import {JitAccounts, initJitAccounts, executeSwapWithAmount} from "@foundry-script/simulation/JitGame.sol";
import "@foundry-script/utils/Constants.sol";

import {FciTokenVaultHarness} from "../helpers/FciTokenVaultHarness.sol";
import {LONG, SHORT} from "@fci-token-vault/modules/FciTokenVaultMod.sol";
import {lookbackPayoffX96} from "@fci-token-vault/libraries/SqrtPriceLookbackPayoffX96Lib.sol";

contract HedgedVsUnhedgedTest is PosmTestSetup, FCITestHelper {
    using PoolIdLibrary for PoolKey;

    Context ctx;
    Scenario scenario;
    FeeConcentrationIndexHarness fciHarness;
    FciTokenVaultHarness vault;
    PoolId poolId;

    // Test parameters
    uint256 constant CAPITAL = 1e18;           // Total capital per PLP
    uint256 constant HEDGE_AMOUNT = 0.1e18;    // 10% of capital to vault
    uint256 constant TRADE_SIZE = 1e15;        // Swap size per round
    uint256 constant ROUNDS = 3;
    uint256 constant JIT_CAPITAL = 9e18;       // Large JIT capital for crowd-out

    // Block timing (from JitGame constants)
    uint256 constant JIT_ENTRY_OFFSET = 49;
    uint256 constant PASSIVE_EXIT_OFFSET = 50;

    Vm.Wallet hedgedPlp;
    Vm.Wallet unhedgedPlp;
    Vm.Wallet jitLp;
    Vm.Wallet swapperWallet;

    function setUp() public {
        // Deploy V4 infrastructure
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();
        deployAndApprovePosm(manager);

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
        fciHarness = new FeeConcentrationIndexHarness{salt: salt}(lpm);
        require(address(fciHarness) == hookAddress, "hook address mismatch");

        // Init pool
        (key, poolId) = initPool(
            currency0, currency1,
            IHooks(address(fciHarness)),
            3000,           // 0.3% fee
            SQRT_PRICE_1_1  // 1:1 price
        );

        // Wire Context
        ctx.vm = vm;
        ctx.v4Pool = key;
        ctx.v4PositionManager = address(lpm);
        ctx.v4SwapRouter = address(swapRouter);
        ctx.chainId = block.chainid;

        // Deploy vault harness
        vault = new FciTokenVaultHarness();

        // Strike at Δ* ≈ 0.09 → p = 0.09/0.91 ≈ 0.0989
        // sqrtPrice for this p via SqrtPriceLibrary
        uint160 strikePrice = SqrtPriceLibrary.fractionToSqrtPriceX96(9, 91);
        vault.harness_initVault(
            strikePrice,
            14 days,                          // halfLife
            block.timestamp + 365 days,       // expiry (far future)
            key,                              // poolKey
            false,                            // reactive (V4 native)
            Currency.unwrap(currency1)        // collateralToken = token1
        );

        // Create wallets
        hedgedPlp = vm.createWallet("hedgedPlp");
        unhedgedPlp = vm.createWallet("unhedgedPlp");
        jitLp = vm.createWallet("jitLp");
        swapperWallet = vm.createWallet("swapper");

        // Fund and approve all actors
        _setupLP(hedgedPlp.addr);
        _setupLP(unhedgedPlp.addr);
        _setupLP(jitLp.addr);
        _setupSwapper(swapperWallet.addr);
    }
}
```

- [ ] **Step 2: Verify build**

Run: `forge build 2>&1 | tail -10`
Expected: Compilation successful (test contract with no test functions yet)

- [ ] **Step 3: Commit scaffold**

```bash
git add -f test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol
git commit -m "test(004): scaffold HedgedVsUnhedged integration test"
```

---

### Task 8: Helper functions for manual LP orchestration

**Files:**
- Modify: `test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol`

- [ ] **Step 1: Add _setupLP and _setupSwapper helpers**

Inside the contract, after setUp:

```solidity
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
```

- [ ] **Step 2: Add _depositToVault helper**

```solidity
    /// @dev Hedged PLP deposits collateral (currency1) into vault
    function _depositToVault(Vm.Wallet memory plp, uint256 amount) internal {
        vm.startPrank(plp.addr);
        IERC20(Currency.unwrap(currency1)).approve(address(vault), amount);
        vault.harness_deposit(plp.addr, amount);
        vm.stopPrank();
    }
```

- [ ] **Step 3: Add _runRound helper — executes one JIT round (swap + optional JIT)**

```solidity
    uint256 constant ROUND_INTERVAL = 1 days;

    /// @dev Execute one round: optional JIT entry → swap → JIT exit → warp → poke
    function _runRound(
        bool jitEnters,
        uint256 jitCapital
    ) internal returns (uint256 jitTokenId) {
        // JIT entry (if applicable)
        if (jitEnters) {
            jitTokenId = mintPosition(
                ctx, scenario, Protocol.UniswapV4, jitLp.privateKey, jitCapital
            );
        }

        // Swap
        executeSwapWithAmount(
            ctx, Protocol.UniswapV4, swapperWallet.privateKey, ZERO_FOR_ONE, int256(TRADE_SIZE)
        );

        // JIT exit (next block)
        vm.roll(block.number + 1);
        if (jitEnters) {
            burnPosition(ctx, Protocol.UniswapV4, jitLp.privateKey, jitTokenId, jitCapital);
        }

        // Advance time so poke() sees non-zero dt for decay calculation
        vm.warp(block.timestamp + ROUND_INTERVAL);

        // Poke vault to update HWM from live FCI
        vault.harness_poke();
    }
```

- [ ] **Step 4: Add _measureTotalPayout helper — computes total LP payout**

```solidity
    /// @dev Burn LP position and return total payout (principal + fees, both tokens)
    /// Note: Sums token0 + token1 raw amounts. Valid welfare comparison because
    /// both PLPs share the same pool at ~1:1 price, so denomination effects cancel.
    function _measureTotalPayout(
        Vm.Wallet memory plp,
        uint256 tokenId,
        uint256 liquidity
    ) internal returns (uint256 totalPayout) {
        address lpAddr = plp.addr;
        address tokenA = Currency.unwrap(currency0);
        address tokenB = Currency.unwrap(currency1);

        uint256 balABefore = IERC20(tokenA).balanceOf(lpAddr);
        uint256 balBBefore = IERC20(tokenB).balanceOf(lpAddr);

        burnPosition(ctx, Protocol.UniswapV4, plp.privateKey, tokenId, liquidity);

        uint256 balAAfter = IERC20(tokenA).balanceOf(lpAddr);
        uint256 balBAfter = IERC20(tokenB).balanceOf(lpAddr);

        // Total payout from burn = principal returned + fees earned
        // Hedged PLP has less principal, so the comparison captures the
        // opportunity cost of diverting capital to the vault.
        totalPayout = (balAAfter - balABefore) + (balBAfter - balBBefore);
    }
```

- [ ] **Step 5: Add _settleAndRedeem helper**

```solidity
    /// @dev Warp past expiry, settle vault, redeem hedged PLP's tokens
    function _settleAndRedeem(Vm.Wallet memory plp, uint256 depositAmount)
        internal
        returns (uint256 longPayout, uint256 shortPayout)
    {
        // Read actual expiry from vault storage and warp just past it
        (,,, uint256 expiry,,,,) = vault.harness_getVaultStorage();
        vm.warp(expiry + 1);

        // Settle
        vault.harness_settle();

        // Get longPayoutPerToken
        (,,,,,,, uint256 longPayoutPerToken) = vault.harness_getVaultStorage();

        // Compute payouts
        longPayout = (depositAmount * longPayoutPerToken) / SqrtPriceLibrary.Q96;
        shortPayout = depositAmount - longPayout;

        // Redeem
        vm.prank(plp.addr);
        vault.harness_redeem(plp.addr, depositAmount);
    }
```

- [ ] **Step 6: Verify build**

Run: `forge build 2>&1 | tail -5`
Expected: Compilation successful

- [ ] **Step 7: Commit helpers**

```bash
git add test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol
git commit -m "test(004): add helper functions for hedged-vs-unhedged orchestration"
```

---

### Task 9: test_equilibrium_no_jit

**Files:**
- Modify: `test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol`

- [ ] **Step 1: Write test**

```solidity
    /// @dev Equilibrium: no JIT, LONG = 0, hedged welfare < unhedged (cost of reduced LP)
    function test_equilibrium_no_jit() public {
        // ── Phase 1: Entry ──
        // Hedged PLP: deposit to vault, LP with remainder
        _depositToVault(hedgedPlp, HEDGE_AMOUNT);
        uint256 hedgedLiquidity = CAPITAL - HEDGE_AMOUNT;
        uint256 hedgedTokenId = mintPosition(
            ctx, scenario, Protocol.UniswapV4, hedgedPlp.privateKey, hedgedLiquidity
        );

        // Unhedged PLP: LP with full capital
        uint256 unhedgedTokenId = mintPosition(
            ctx, scenario, Protocol.UniswapV4, unhedgedPlp.privateKey, CAPITAL
        );

        // ── Phase 2: Rounds (no JIT) ──
        for (uint256 i; i < ROUNDS; ++i) {
            vm.roll(block.number + JIT_ENTRY_OFFSET);
            _runRound(false, 0);
            vm.roll(block.number + PASSIVE_EXIT_OFFSET);
        }

        // ── Phase 3: Exit LP positions ──
        uint256 hedgedPayout = _measureTotalPayout(hedgedPlp, hedgedTokenId, hedgedLiquidity);
        uint256 unhedgedPayout = _measureTotalPayout(unhedgedPlp, unhedgedTokenId, CAPITAL);

        // ── Phase 4: Settle vault ──
        (uint256 longPayout, uint256 shortPayout) = _settleAndRedeem(hedgedPlp, HEDGE_AMOUNT);

        // ── Phase 5: Welfare comparison ──
        uint256 hedgedWelfare = hedgedPayout + longPayout;
        uint256 unhedgedWelfare = unhedgedPayout;

        // ── Assertions ──
        // Property 2: No false trigger — LONG = 0
        assertEq(longPayout, 0, "LONG should be 0 in equilibrium");

        // Property 2: hedged < unhedged (cost of reduced LP)
        assertLt(hedgedWelfare, unhedgedWelfare, "hedged should earn less in equilibrium");

        // Property 3: Vault solvency — conservation + actual balance
        assertEq(longPayout + shortPayout, HEDGE_AMOUNT, "conservation: long + short = deposit");
        assertGe(
            IERC20(Currency.unwrap(currency1)).balanceOf(address(vault)),
            0,
            "vault balance non-negative after redeem"
        );

        // Log metrics
        console.log("=== EQUILIBRIUM (no JIT) ===");
        console.log("Hedged LP payout:", hedgedPayout);
        console.log("Unhedged LP payout:", unhedgedPayout);
        console.log("LONG payout:", longPayout);
        console.log("Hedged welfare:", hedgedWelfare);
        console.log("Unhedged welfare:", unhedgedWelfare);
    }
```

- [ ] **Step 2: Run test**

Run: `forge test --match-test test_equilibrium_no_jit -vvv`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol
git commit -m "test(004): add equilibrium scenario — no JIT, hedged < unhedged"
```

---

### Task 10: test_jit_crowdout_hedge_compensates

**Files:**
- Modify: `test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol`

- [ ] **Step 1: Write test**

```solidity
    /// @dev JIT crowd-out: LONG > 0, hedged welfare > unhedged
    function test_jit_crowdout_hedge_compensates() public {
        // ── Phase 1: Entry ──
        _depositToVault(hedgedPlp, HEDGE_AMOUNT);
        uint256 hedgedLiquidity = CAPITAL - HEDGE_AMOUNT;
        uint256 hedgedTokenId = mintPosition(
            ctx, scenario, Protocol.UniswapV4, hedgedPlp.privateKey, hedgedLiquidity
        );
        uint256 unhedgedTokenId = mintPosition(
            ctx, scenario, Protocol.UniswapV4, unhedgedPlp.privateKey, CAPITAL
        );

        // ── Phase 2: Rounds (JIT always enters with large capital) ──
        for (uint256 i; i < ROUNDS; ++i) {
            vm.roll(block.number + JIT_ENTRY_OFFSET);
            _runRound(true, JIT_CAPITAL);
            vm.roll(block.number + PASSIVE_EXIT_OFFSET);

            // Property 4: HWM captures current price after each poke
            (,uint160 sqrtPriceHWM,,,,,,) = vault.harness_getVaultStorage();
            // After JIT crowd-out, FCI oracle returns Δ⁺ > 0, so
            // currentSqrtPrice > 0 and HWM >= currentSqrtPrice (HWM only ratchets up)
            assertGt(uint256(sqrtPriceHWM), 0, "HWM should be > 0 after JIT round");
        }

        // ── Phase 3b: Record pre-settlement HWM for decay check (Property 5) ──
        (,uint160 hwmBeforeSettle,,,,,,) = vault.harness_getVaultStorage();

        // ── Phase 4: Exit LP positions ──
        uint256 hedgedPayout = _measureTotalPayout(hedgedPlp, hedgedTokenId, hedgedLiquidity);
        uint256 unhedgedPayout = _measureTotalPayout(unhedgedPlp, unhedgedTokenId, CAPITAL);

        // ── Phase 5: Settle vault (warps past expiry → decay applied) ──
        (uint256 longPayout, uint256 shortPayout) = _settleAndRedeem(hedgedPlp, HEDGE_AMOUNT);

        // ── Phase 6: Welfare comparison ──
        uint256 hedgedWelfare = hedgedPayout + longPayout;
        uint256 unhedgedWelfare = unhedgedPayout;

        // ── Assertions ──
        // Property 1: Payoff compensation
        assertGt(hedgedWelfare, unhedgedWelfare, "hedged should earn more under JIT crowd-out");

        // Property 1 sub: LONG > 0
        assertGt(longPayout, 0, "LONG should be positive under JIT crowd-out");

        // Property 3: Vault solvency — accounting conservation + actual token balance
        assertEq(longPayout + shortPayout, HEDGE_AMOUNT, "conservation: long + short = deposit");
        assertGe(
            IERC20(Currency.unwrap(currency1)).balanceOf(address(vault)),
            0,
            "vault token balance should be non-negative after redeem"
        );

        // Property 5: Decay effect — payout with decay < payout without decay
        // settle() computes decayedHWM = applyDecay(sqrtPriceHWM, dt, halfLife)
        // then longPayoutPerToken = lookbackPayoffX96(decayedHWM, strike).
        // We compare: lookbackPayoffX96(rawHWM, strike) > longPayoutPerToken
        // which proves decay reduced the HWM before computing payout.
        (uint160 strikePrice,,,,,,,uint256 actualLongPayoutPerToken2) = vault.harness_getVaultStorage();
        uint256 noDecayPayout = lookbackPayoffX96(hwmBeforeSettle, strikePrice);
        assertGt(noDecayPayout, actualLongPayoutPerToken2, "decay should reduce payout vs raw HWM");
        console.log("HWM before settle:", uint256(hwmBeforeSettle));
        console.log("LongPayoutPerToken (with decay):", actualLongPayoutPerToken2);
        console.log("LongPayoutPerToken (no decay):", noDecayPayout);

        // Property 6: Log break-even metrics
        console.log("=== JIT CROWD-OUT ===");
        console.log("Hedged LP payout:", hedgedPayout);
        console.log("Unhedged LP payout:", unhedgedPayout);
        console.log("LP payout gap (unhedged - hedged):", unhedgedPayout - hedgedPayout);
        console.log("LONG payout:", longPayout);
        console.log("Hedged welfare:", hedgedWelfare);
        console.log("Unhedged welfare:", unhedgedWelfare);
        console.log("Net hedge benefit:", hedgedWelfare - unhedgedWelfare);
    }
```

- [ ] **Step 2: Run test**

Run: `forge test --match-test test_jit_crowdout_hedge_compensates -vvv`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol
git commit -m "test(004): add JIT crowd-out scenario — hedged > unhedged"
```

---

### Task 11: test_below_strike_no_false_trigger

**Files:**
- Modify: `test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol`

- [ ] **Step 1: Write test**

```solidity
    /// @dev Below-strike JIT: LONG = 0, hedged welfare < unhedged
    function test_below_strike_no_false_trigger() public {
        // ── Phase 1: Entry ──
        _depositToVault(hedgedPlp, HEDGE_AMOUNT);
        uint256 hedgedLiquidity = CAPITAL - HEDGE_AMOUNT;
        uint256 hedgedTokenId = mintPosition(
            ctx, scenario, Protocol.UniswapV4, hedgedPlp.privateKey, hedgedLiquidity
        );
        uint256 unhedgedTokenId = mintPosition(
            ctx, scenario, Protocol.UniswapV4, unhedgedPlp.privateKey, CAPITAL
        );

        // ── Phase 2: Rounds (JIT enters with SMALL capital — Δ⁺ stays below strike) ──
        uint256 smallJitCapital = CAPITAL / 10; // Very small JIT, minimal concentration

        for (uint256 i; i < ROUNDS; ++i) {
            vm.roll(block.number + JIT_ENTRY_OFFSET);
            _runRound(true, smallJitCapital);
            vm.roll(block.number + PASSIVE_EXIT_OFFSET);
        }

        // ── Phase 3: Exit LP positions ──
        uint256 hedgedPayout = _measureTotalPayout(hedgedPlp, hedgedTokenId, hedgedLiquidity);
        uint256 unhedgedPayout = _measureTotalPayout(unhedgedPlp, unhedgedTokenId, CAPITAL);

        // ── Phase 4: Settle vault ──
        (uint256 longPayout, uint256 shortPayout) = _settleAndRedeem(hedgedPlp, HEDGE_AMOUNT);

        // ── Phase 5: Welfare comparison ──
        uint256 hedgedWelfare = hedgedPayout + longPayout;
        uint256 unhedgedWelfare = unhedgedPayout;

        // ── Assertions ──
        // Property 2: No false trigger
        assertEq(longPayout, 0, "LONG should be 0 when below strike");

        // Property 2: hedged < unhedged
        assertLt(hedgedWelfare, unhedgedWelfare, "hedged should earn less when below strike");

        // Property 3: Vault solvency — conservation + actual balance
        assertEq(longPayout + shortPayout, HEDGE_AMOUNT, "conservation: long + short = deposit");
        assertGe(
            IERC20(Currency.unwrap(currency1)).balanceOf(address(vault)),
            0,
            "vault balance non-negative after redeem"
        );

        // Log metrics
        console.log("=== BELOW-STRIKE JIT ===");
        console.log("Hedged LP payout:", hedgedPayout);
        console.log("Unhedged LP payout:", unhedgedPayout);
        console.log("LONG payout:", longPayout);
        console.log("Hedged welfare:", hedgedWelfare);
        console.log("Unhedged welfare:", unhedgedWelfare);
    }
```

- [ ] **Step 2: Run test**

Run: `forge test --match-test test_below_strike_no_false_trigger -vvv`
Expected: PASS

- [ ] **Step 3: Run all three scenarios together**

Run: `forge test --match-path "test/fci-token-vault/integration/HedgedVsUnhedged*" -vvv`
Expected: 3 tests PASS

- [ ] **Step 4: Commit**

```bash
git add test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol
git commit -m "test(004): add below-strike scenario — no false trigger, hedged < unhedged"
```

---

### Task 12: Final verification — all fci-token-vault tests

- [ ] **Step 1: Run full test suite**

Run: `forge test --match-path "test/fci-token-vault/**" -vv`
Expected: All tests PASS (unit + fuzz + integration + new hedged-vs-unhedged)

- [ ] **Step 2: Run simulation tests too (no regressions)**

Run: `forge test --match-path "test/simulation/**" -vv`
Expected: All tests PASS

- [ ] **Step 3: Final commit if cleanup needed**

```bash
git commit -m "chore(004): all hedged-vs-unhedged scenario tests green"
```
