# Cross-Epoch Welfare Comparison Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate epoch vs cumulative Δ⁺ welfare outcomes across epoch boundaries using dual-vault comparison — go/no-go gate for reactive dispatch.

**Architecture:** Single integration test with two `FciTokenVaultHarness` instances (cumulative + epoch) watching the same FCI hook and pool. Each round pokes both vaults before warping to the next epoch. 3 scenarios: JIT-then-clean, alternating, recovery.

**Tech Stack:** Solidity ^0.8.26, Foundry (forge), PosmTestSetup, FciTokenVaultHarness, FeeConcentrationIndexHarness, SqrtPriceLibrary

---

## File Structure

### New files:

| File | Responsibility |
|------|---------------|
| `test/fci-token-vault/integration/CrossEpochWelfareComparison.integration.t.sol` | Dual-vault integration test: 3 cross-epoch scenarios comparing cumulative vs epoch welfare |

### Existing files (read-only reference):

| File | Why |
|------|-----|
| `test/fci-token-vault/integration/HedgedVsUnhedged.integration.t.sol` | Pattern reference for setUp, helpers, scenario structure |
| `test/fci-token-vault/integration/HedgedVsUnhedgedEpoch.integration.t.sol` | Pattern reference for epoch-specific poke + initializeEpochPool |
| `test/fci-token-vault/helpers/FciTokenVaultHarness.sol` | Provides `harness_poke()` and `harness_pokeEpoch()` |
| `research/backtest/pnl.py` | PnL model: `hedge_value = payouts - γ * fees` |

---

## Chunk 1: Cross-Epoch Welfare Comparison Test

### Task 1: Write Test Infrastructure (setUp + helpers)

**Files:**
- Create: `test/fci-token-vault/integration/CrossEpochWelfareComparison.integration.t.sol`

- [ ] **Step 1: Write imports, constants, state variables, and setUp**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test, console} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
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

import {FeeConcentrationIndexHarness} from "../../fee-concentration-index/harness/FeeConcentrationIndexHarness.sol";
import {FCITestHelper} from "../../fee-concentration-index/helpers/FCITestHelper.sol";
import {SqrtPriceLibrary} from "foundational-hooks/src/libraries/SqrtPriceLibrary.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";

import {Context} from "@foundry-script/types/Context.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";
import {Scenario, mintPosition, burnPosition} from "@foundry-script/types/Scenario.sol";
import {executeSwapWithAmount} from "@foundry-script/simulation/JitGame.sol";
import "@foundry-script/utils/Constants.sol";

import {FciTokenVaultHarness} from "../helpers/FciTokenVaultHarness.sol";
import {LONG, SHORT} from "@fci-token-vault/modules/FciTokenVaultMod.sol";

contract CrossEpochWelfareComparisonTest is PosmTestSetup, FCITestHelper {
    using PoolIdLibrary for PoolKey;

    Context ctx;
    Scenario scenario;
    FeeConcentrationIndexHarness fciHarness;
    FciTokenVaultHarness cumulativeVault;
    FciTokenVaultHarness epochVault;
    PoolId poolId;

    uint256 constant CAPITAL = 1e18;
    uint256 constant HEDGE_AMOUNT = 0.1e18;
    uint256 constant TRADE_SIZE = 1e15;
    uint256 constant JIT_CAPITAL = 9e18;
    uint256 constant ROUND_INTERVAL = 1 days;
    uint256 constant EPOCH_LENGTH = 1 days;

    address hedgedPlpAddr;
    uint256 hedgedPlpPk;
    address unhedgedPlpAddr;
    uint256 unhedgedPlpPk;
    address jitLpAddr;
    uint256 jitLpPk;
    address swapperAddr;
    uint256 swapperPk;
    address depositorAddr;
    uint256 depositorPk;

    function setUp() public {
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();
        deployAndApprovePosm(manager);

        fciLP = makeAddr("defaultLP");
        fciSwapper = address(this);
        fciSwapRouter = swapRouter;

        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
                | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
                | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
                | Hooks.BEFORE_SWAP_FLAG
                | Hooks.AFTER_SWAP_FLAG
        );
        bytes memory constructorArgs = abi.encode(address(lpm));
        (address hookAddress, bytes32 salt) = HookMiner.find(
            address(this), flags,
            type(FeeConcentrationIndexHarness).creationCode, constructorArgs
        );
        fciHarness = new FeeConcentrationIndexHarness{salt: salt}(lpm);
        require(address(fciHarness) == hookAddress, "hook address mismatch");

        (key, poolId) = initPool(
            currency0, currency1,
            IHooks(address(fciHarness)),
            3000, SQRT_PRICE_1_1
        );

        // Initialize epoch metric
        fciHarness.initializeEpochPool(key, EPOCH_LENGTH);

        ctx.vm = vm;
        ctx.v4Pool = key;
        ctx.v4PositionManager = address(lpm);
        ctx.v4SwapRouter = address(swapRouter);
        ctx.chainId = block.chainid;

        // Deploy TWO vaults with identical params
        uint160 strikePrice = SqrtPriceLibrary.fractionToSqrtPriceX96(30, 70);
        address collateral = Currency.unwrap(currency1);

        cumulativeVault = new FciTokenVaultHarness();
        cumulativeVault.harness_initVault(
            strikePrice, 14 days, block.timestamp + 7 days,
            key, false, collateral
        );

        epochVault = new FciTokenVaultHarness();
        epochVault.harness_initVault(
            strikePrice, 14 days, block.timestamp + 7 days,
            key, false, collateral
        );

        Vm.Wallet memory w;
        w = vm.createWallet("hedgedPlp");
        hedgedPlpAddr = w.addr; hedgedPlpPk = w.privateKey;
        w = vm.createWallet("unhedgedPlp");
        unhedgedPlpAddr = w.addr; unhedgedPlpPk = w.privateKey;
        w = vm.createWallet("jitLp");
        jitLpAddr = w.addr; jitLpPk = w.privateKey;
        w = vm.createWallet("swapper");
        swapperAddr = w.addr; swapperPk = w.privateKey;
        w = vm.createWallet("depositor");
        depositorAddr = w.addr; depositorPk = w.privateKey;

        _setupLP(hedgedPlpAddr);
        _setupLP(unhedgedPlpAddr);
        _setupLP(jitLpAddr);
        _setupSwapper(swapperAddr);
        seedBalance(depositorAddr);
    }
```

- [ ] **Step 2: Write helper functions**

```solidity
    // ── Helpers ──

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

    function _depositToBothVaults(address plpAddr, uint256 amount) internal {
        vm.startPrank(plpAddr);
        IERC20(Currency.unwrap(currency1)).approve(address(cumulativeVault), amount);
        cumulativeVault.harness_deposit(plpAddr, amount);
        IERC20(Currency.unwrap(currency1)).approve(address(epochVault), amount);
        epochVault.harness_deposit(plpAddr, amount);
        vm.stopPrank();
    }

    uint256 constant JIT_ENTRY_OFFSET = 49;
    uint256 constant PASSIVE_EXIT_OFFSET = 50;

    /// @dev Run one round: LP entry → JIT → swap → burns → poke BOTH → warp.
    /// Critical: poke BEFORE warp so epoch vault reads within current epoch.
    function _runCrossEpochRound(bool jitEnters, uint256 jitCapital) internal {
        // Passive LP entry
        uint256 hTid = mintPosition(ctx, scenario, Protocol.UniswapV4, hedgedPlpPk, CAPITAL);
        uint256 uTid = mintPosition(ctx, scenario, Protocol.UniswapV4, unhedgedPlpPk, CAPITAL);

        vm.roll(block.number + JIT_ENTRY_OFFSET);

        uint256 jitTokenId;
        if (jitEnters) {
            jitTokenId = mintPosition(ctx, scenario, Protocol.UniswapV4, jitLpPk, jitCapital);
        }

        executeSwapWithAmount(ctx, Protocol.UniswapV4, swapperPk, ZERO_FOR_ONE, int256(TRADE_SIZE));

        vm.roll(block.number + 1);
        if (jitEnters) {
            burnPosition(ctx, Protocol.UniswapV4, jitLpPk, jitTokenId, jitCapital);
        }

        vm.roll(block.number + PASSIVE_EXIT_OFFSET);
        burnPosition(ctx, Protocol.UniswapV4, hedgedPlpPk, hTid, CAPITAL);
        burnPosition(ctx, Protocol.UniswapV4, unhedgedPlpPk, uTid, CAPITAL);

        // Log metrics BEFORE poke
        uint128 cumDp = IFeeConcentrationIndex(address(fciHarness)).getDeltaPlus(key, false);
        uint128 epochDp = IFeeConcentrationIndex(address(fciHarness)).getDeltaPlusEpoch(key, false);
        console.log("  Cumulative dp:", uint256(cumDp));
        console.log("  Epoch dp:     ", uint256(epochDp));

        // Poke BOTH vaults BEFORE warp (critical: epoch reads within current epoch)
        cumulativeVault.harness_poke();
        epochVault.harness_pokeEpoch();

        // THEN warp to cross epoch boundary
        vm.warp(block.timestamp + ROUND_INTERVAL);
    }

    /// @dev Settle vault and compute payouts. Returns (longPayout, shortPayout).
    function _settleVault(FciTokenVaultHarness v, uint256 depositAmount)
        internal
        returns (uint256 longPayout, uint256 shortPayout)
    {
        (,,, uint256 expiry,,,,) = v.harness_getVaultStorage();
        vm.warp(expiry + 1);
        v.harness_settle();
        (,,,,,,, uint256 longPayoutPerToken) = v.harness_getVaultStorage();
        longPayout = (depositAmount * longPayoutPerToken) / SqrtPriceLibrary.Q96;
        shortPayout = depositAmount - longPayout;
    }

    function _snapshotBal(address who) internal view returns (uint256 a, uint256 b) {
        a = IERC20(Currency.unwrap(currency0)).balanceOf(who);
        b = IERC20(Currency.unwrap(currency1)).balanceOf(who);
    }

    /// @dev Log welfare comparison following PnL model from research/backtest/pnl.py.
    /// Note: lpFeeRevenue sums token0+token1 balances — simplified metric for logging only.
    function _logWelfareComparison(
        uint256 cumLongPayout,
        uint256 epochLongPayout,
        uint256 lpFeeRevenue
    ) internal view {
        console.log("--- Welfare Comparison ---");
        console.log("LP fee revenue:", lpFeeRevenue);
        console.log("Cumulative LONG payout:", cumLongPayout);
        console.log("Epoch LONG payout:     ", epochLongPayout);
        // hedge_value = longPayout - HEDGE_AMOUNT (positive = hedge was worth it)
        if (cumLongPayout >= HEDGE_AMOUNT) {
            console.log("Cumulative hedge_value: +", cumLongPayout - HEDGE_AMOUNT);
        } else {
            console.log("Cumulative hedge_value: -", HEDGE_AMOUNT - cumLongPayout);
        }
        if (epochLongPayout >= HEDGE_AMOUNT) {
            console.log("Epoch hedge_value: +", epochLongPayout - HEDGE_AMOUNT);
        } else {
            console.log("Epoch hedge_value: -", HEDGE_AMOUNT - epochLongPayout);
        }
    }
```

- [ ] **Step 3: Verify compilation**

Run: `forge build`
Expected: Clean (existing lint warnings only).

- [ ] **Step 4: Commit infrastructure**

```bash
git add test/fci-token-vault/integration/CrossEpochWelfareComparison.integration.t.sol
git commit -m "test(004): cross-epoch welfare comparison — setUp + helpers"
```

---

### Task 2: Scenario 4 — JIT-Then-Clean

**Files:**
- Modify: `test/fci-token-vault/integration/CrossEpochWelfareComparison.integration.t.sol`

- [ ] **Step 1: Write Scenario 4 test**

Add after helpers:

```solidity
    // ── Scenario 4: JIT-Then-Clean (critical case) ──

    function test_scenario4_jit_then_clean() public {
        _depositToBothVaults(depositorAddr, HEDGE_AMOUNT);
        (uint256 hA0, uint256 hB0) = _snapshotBal(hedgedPlpAddr);

        console.log("=== SCENARIO 4: JIT-THEN-CLEAN ===");

        // Round 1: JIT enters
        console.log("Round 1 (JIT):");
        _runCrossEpochRound(true, JIT_CAPITAL);

        // Round 2: Clean (no JIT)
        console.log("Round 2 (clean):");
        _runCrossEpochRound(false, 0);

        // Round 3: Clean (no JIT)
        console.log("Round 3 (clean):");
        _runCrossEpochRound(false, 0);

        (uint256 hA1, uint256 hB1) = _snapshotBal(hedgedPlpAddr);
        uint256 lpFeeRevenue = (hA1 + hB1) - (hA0 + hB0);

        // Settle cumulative vault first (warp resets for epoch vault)
        (uint256 cumLongPayout, uint256 cumShortPayout) = _settleVault(cumulativeVault, HEDGE_AMOUNT);

        // Reset timestamp for epoch vault settlement (same expiry)
        (uint256 epochLongPayout, uint256 epochShortPayout) = _settleVault(epochVault, HEDGE_AMOUNT);

        _logWelfareComparison(cumLongPayout, epochLongPayout, lpFeeRevenue);

        // Assertions
        assertGt(cumLongPayout, 0, "cumulative should trigger from Round 1 JIT");
        assertLt(epochLongPayout, cumLongPayout, "epoch should pay less — JIT stopped after Round 1");
        assertEq(cumLongPayout + cumShortPayout, HEDGE_AMOUNT, "cumulative conservation");
        assertEq(epochLongPayout + epochShortPayout, HEDGE_AMOUNT, "epoch conservation");
    }
```

- [ ] **Step 2: Run Scenario 4**

Run: `forge test --match-test test_scenario4 -vv`
Expected: PASS. Epoch Δ⁺ resets in Rounds 2-3 (visible in logs). `epochLongPayout < cumLongPayout`.

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/integration/CrossEpochWelfareComparison.integration.t.sol
git commit -m "test(004): scenario 4 — JIT-then-clean cross-epoch welfare"
```

---

### Task 3: Scenario 5 — Alternating JIT/Clean

**Files:**
- Modify: `test/fci-token-vault/integration/CrossEpochWelfareComparison.integration.t.sol`

- [ ] **Step 1: Write Scenario 5 test**

```solidity
    // ── Scenario 5: Alternating JIT/Clean (responsiveness) ──

    function test_scenario5_alternating_jit_clean() public {
        _depositToBothVaults(depositorAddr, HEDGE_AMOUNT);
        (uint256 hA0, uint256 hB0) = _snapshotBal(hedgedPlpAddr);

        console.log("=== SCENARIO 5: ALTERNATING JIT/CLEAN ===");

        // Round 1: JIT
        console.log("Round 1 (JIT):");
        _runCrossEpochRound(true, JIT_CAPITAL);

        // Round 2: Clean
        console.log("Round 2 (clean):");
        _runCrossEpochRound(false, 0);

        // Round 3: JIT
        console.log("Round 3 (JIT):");
        _runCrossEpochRound(true, JIT_CAPITAL);

        // Round 4: Clean
        console.log("Round 4 (clean):");
        _runCrossEpochRound(false, 0);

        (uint256 hA1, uint256 hB1) = _snapshotBal(hedgedPlpAddr);
        uint256 lpFeeRevenue = (hA1 + hB1) - (hA0 + hB0);

        (uint256 cumLongPayout, uint256 cumShortPayout) = _settleVault(cumulativeVault, HEDGE_AMOUNT);
        (uint256 epochLongPayout, uint256 epochShortPayout) = _settleVault(epochVault, HEDGE_AMOUNT);

        _logWelfareComparison(cumLongPayout, epochLongPayout, lpFeeRevenue);

        // Assertions
        assertGt(cumLongPayout, 0, "cumulative should trigger");
        assertGt(epochLongPayout, 0, "epoch should trigger — JIT occurred in Rounds 1 & 3");
        assertLt(epochLongPayout, cumLongPayout, "epoch should pay less — doesn't over-count clean rounds");
        assertEq(cumLongPayout + cumShortPayout, HEDGE_AMOUNT, "cumulative conservation");
        assertEq(epochLongPayout + epochShortPayout, HEDGE_AMOUNT, "epoch conservation");
    }
```

- [ ] **Step 2: Run Scenario 5**

Run: `forge test --match-test test_scenario5 -vv`
Expected: PASS. Epoch Δ⁺ oscillates (high/near-zero/high/near-zero).

- [ ] **Step 3: Commit**

```bash
git add test/fci-token-vault/integration/CrossEpochWelfareComparison.integration.t.sol
git commit -m "test(004): scenario 5 — alternating JIT/clean cross-epoch welfare"
```

---

### Task 4: Scenario 6 — Recovery After Initial JIT

**Files:**
- Modify: `test/fci-token-vault/integration/CrossEpochWelfareComparison.integration.t.sol`

- [ ] **Step 1: Write Scenario 6 test**

```solidity
    // ── Scenario 6: Recovery after initial JIT ──

    function test_scenario6_recovery_after_initial_jit() public {
        _depositToBothVaults(depositorAddr, HEDGE_AMOUNT);
        (uint256 hA0, uint256 hB0) = _snapshotBal(hedgedPlpAddr);

        console.log("=== SCENARIO 6: RECOVERY AFTER INITIAL JIT ===");

        // Round 1: JIT
        console.log("Round 1 (JIT):");
        _runCrossEpochRound(true, JIT_CAPITAL);

        // Rounds 2-5: Clean
        for (uint256 i = 2; i <= 5; ++i) {
            console.log("Round", i, "(clean):");
            _runCrossEpochRound(false, 0);
        }

        (uint256 hA1, uint256 hB1) = _snapshotBal(hedgedPlpAddr);
        uint256 lpFeeRevenue = (hA1 + hB1) - (hA0 + hB0);

        (uint256 cumLongPayout, uint256 cumShortPayout) = _settleVault(cumulativeVault, HEDGE_AMOUNT);
        (uint256 epochLongPayout, uint256 epochShortPayout) = _settleVault(epochVault, HEDGE_AMOUNT);

        _logWelfareComparison(cumLongPayout, epochLongPayout, lpFeeRevenue);

        // Assertions
        assertGt(cumLongPayout, 0, "cumulative never forgets");
        assertLt(epochLongPayout, cumLongPayout, "epoch recovers — pays less");
        assertLt(epochLongPayout, cumLongPayout / 2, "epoch payout significantly less, not marginal");
        assertEq(cumLongPayout + cumShortPayout, HEDGE_AMOUNT, "cumulative conservation");
        assertEq(epochLongPayout + epochShortPayout, HEDGE_AMOUNT, "epoch conservation");
    }
```

- [ ] **Step 2: Close the contract**

Add `}` to close the contract.

- [ ] **Step 3: Run all 3 scenarios**

Run: `forge test --match-path "test/fci-token-vault/integration/CrossEpochWelfareComparison*" -vv`
Expected: All 3 scenarios PASS. Per-round logs show epoch Δ⁺ resetting at boundaries while cumulative only grows.

- [ ] **Step 4: Run full regression**

Run: `forge test -v`
Expected: All tests pass. Zero regressions.

- [ ] **Step 5: Commit**

```bash
git add test/fci-token-vault/integration/CrossEpochWelfareComparison.integration.t.sol
git commit -m "test(004): scenario 6 — recovery after initial JIT + full cross-epoch welfare suite"
```

---

### Task 5: Analyze Results — Go/No-Go Decision

- [ ] **Step 1: Review logged welfare metrics**

Re-run with verbose output:

Run: `forge test --match-path "test/fci-token-vault/integration/CrossEpochWelfareComparison*" -vvv`

Check the logs for:
1. Epoch Δ⁺ resets to near-zero in clean rounds across all scenarios
2. `epochLongPayout < cumLongPayout` in all 3 scenarios
3. `epochHedgeValue < cumHedgeValue` — epoch doesn't overpay when JIT stops

- [ ] **Step 2: Document results**

Record the welfare metrics in the plan file or notes for go/no-go decision. If all success criteria from the spec hold → proceed to fork simulation and reactive dispatch. If not → report findings for design revision.
