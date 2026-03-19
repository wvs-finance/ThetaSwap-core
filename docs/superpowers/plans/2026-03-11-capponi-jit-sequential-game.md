# Capponi JIT Sequential Game Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a parameterized Forge script that simulates the Period 1 Capponi JIT sequential game on an Anvil fork of Unichain Sepolia (V4), producing controllable delta-plus scenarios for vault hedge testing.

**Architecture:** New `JitGame.sol` module with types, wallet generation, and game execution as free functions. Thin `CapponiJITSequentialGame.s.sol` orchestrator script. Reuses existing mint/burn primitives from `Scenario.sol`, adds `executeSwapWithAmount` overload for parameterized trade size. Protocol-agnostic via `Protocol` enum dispatch.

**Tech Stack:** Solidity ^0.8.26, Forge scripts, Uniswap V4 (PoolManager, PositionManager, PoolSwapTest), forge-std (`Vm.Wallet`, `vm.randomUint`, `vm.deriveKey`, `vm.deal`), Anvil fork.

**Spec:** `docs/superpowers/specs/2026-03-11-capponi-jit-sequential-game-design.md`

---

## Chunk 1: Types and Wallet Generation

### Task 1: Define JitGame types

**Files:**
- Create: `foundry-script/simulation/JitGame.sol`

- [ ] **Step 1: Create JitGame.sol with structs and imports**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Vm} from "forge-std/Vm.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";

struct JitGameConfig {
    uint256 n;
    uint256 jitCapital;
    uint256 jitEntryProbability;
    uint256 tradeSize;
    bool zeroForOne;
    Protocol protocol;
}

struct JitGameResult {
    uint128 deltaPlus;
    uint256 hedgedLpPayout;
    uint256 unhedgedLpPayout;
    uint256 jitLpPayout;
    bool jitEntered;
}

struct JitAccounts {
    Vm.Wallet[] passiveLps;
    Vm.Wallet jitLp;
    Vm.Wallet swapper;
    uint256 hedgedIndex;
}
```

- [ ] **Step 2: Verify it compiles**

Run: `forge build`
Expected: PASS (no errors)

- [ ] **Step 3: Commit**

```bash
git add foundry-script/simulation/JitGame.sol
git commit -m "feat(simulation): add JitGame types — JitGameConfig, JitGameResult, JitAccounts"
```

### Task 2: Implement wallet generation

**Files:**
- Modify: `foundry-script/simulation/JitGame.sol`

- [ ] **Step 1: Write initJitAccounts function**

Add below the structs in `JitGame.sol`:

```solidity
import {DEFAULT_DERIVATION_PATH} from "@foundry-script/types/Accounts.sol";

function initJitAccounts(Vm vm, uint256 n) returns (JitAccounts memory acc) {
    require(n >= 2, "JitGame: N must be >= 2");
    string memory mnemonic = vm.envString("MNEMONIC");

    acc.passiveLps = new Vm.Wallet[](n);
    for (uint256 i; i < n; ++i) {
        acc.passiveLps[i] = vm.createWallet(
            vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, uint32(i)),
            string.concat("passiveLp", vm.toString(i))
        );
    }
    acc.jitLp = vm.createWallet(
        vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, uint32(n)),
        "jitLp"
    );
    acc.swapper = vm.createWallet(
        vm.deriveKey(mnemonic, DEFAULT_DERIVATION_PATH, uint32(n + 1)),
        "swapper"
    );
    acc.hedgedIndex = 0;
}
```

- [ ] **Step 2: Verify it compiles**

Run: `forge build`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add foundry-script/simulation/JitGame.sol
git commit -m "feat(simulation): add initJitAccounts — HD wallet generation for N passive LPs + JIT + swapper"
```

### Task 3: Write unit test for wallet generation

**Files:**
- Create: `test/simulation/JitGame.t.sol`

- [ ] **Step 1: Write the failing test**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {JitAccounts, JitGameConfig, JitGameResult, initJitAccounts} from
    "@foundry-script/simulation/JitGame.sol";

contract JitGameAccountsTest is Test {
    function test_initJitAccounts_generates_correct_count() public {
        uint256 n = 5;
        JitAccounts memory acc = initJitAccounts(vm, n);

        assertEq(acc.passiveLps.length, n, "should generate N passive LPs");
        assertTrue(acc.jitLp.addr != address(0), "JIT LP should have nonzero address");
        assertTrue(acc.swapper.addr != address(0), "swapper should have nonzero address");
        assertEq(acc.hedgedIndex, 0, "hedgedIndex should default to 0");
    }

    function test_initJitAccounts_all_addresses_unique() public {
        uint256 n = 10;
        JitAccounts memory acc = initJitAccounts(vm, n);

        for (uint256 i; i < n; ++i) {
            for (uint256 j = i + 1; j < n; ++j) {
                assertTrue(
                    acc.passiveLps[i].addr != acc.passiveLps[j].addr,
                    "passive LP addresses must be unique"
                );
            }
            assertTrue(
                acc.passiveLps[i].addr != acc.jitLp.addr,
                "passive LP must differ from JIT LP"
            );
            assertTrue(
                acc.passiveLps[i].addr != acc.swapper.addr,
                "passive LP must differ from swapper"
            );
        }
        assertTrue(acc.jitLp.addr != acc.swapper.addr, "JIT LP must differ from swapper");
    }

    function test_initJitAccounts_reverts_below_minimum() public {
        vm.expectRevert("JitGame: N must be >= 2");
        initJitAccounts(vm, 1);
    }

    function test_initJitAccounts_reverts_zero() public {
        vm.expectRevert("JitGame: N must be >= 2");
        initJitAccounts(vm, 0);
    }
}
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `MNEMONIC="test test test test test test test test test test test junk" forge test --match-path "test/simulation/JitGame.t.sol" -vv`
Expected: All 4 tests PASS

- [ ] **Step 3: Commit**

```bash
git add test/simulation/JitGame.t.sol
git commit -m "test(simulation): add JitGame accounts unit tests — count, uniqueness, revert guards"
```

---

## Chunk 2: executeSwapWithAmount and Funding

### Task 4: Add executeSwapWithAmount

**Files:**
- Modify: `foundry-script/simulation/JitGame.sol`

- [ ] **Step 1: Write executeSwapWithAmount function**

Add to `JitGame.sol`:

```solidity
import {Context} from "@foundry-script/types/Context.sol";
import {Protocol, isUniswapV3, isUniswapV4} from "@foundry-script/types/Protocol.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {SwapParams} from "v4-core/src/types/PoolOperation.sol";
import {PoolSwapTest} from "v4-core/src/test/PoolSwapTest.sol";
import {V3CallbackRouter} from "@reactive-integration/adapters/uniswapV3/V3CallbackRouter.sol";
import "@foundry-script/utils/Constants.sol";

function executeSwapWithAmount(
    Context storage ctx,
    Protocol protocol,
    uint256 pk,
    bool zeroForOne,
    int256 amountSpecified
) {
    address caller = ctx.vm.addr(pk);
    if (isUniswapV3(protocol)) {
        V3CallbackRouter router = V3CallbackRouter(ctx.v3Router);
        uint160 sqrtPriceLimit = zeroForOne
            ? TickMath.MIN_SQRT_PRICE + 1
            : TickMath.MAX_SQRT_PRICE - 1;
        ctx.vm.broadcast(pk);
        router.swap(ctx.v3Pool, caller, zeroForOne, amountSpecified, sqrtPriceLimit);
    } else {
        PoolSwapTest router = PoolSwapTest(ctx.v4SwapRouter);
        ctx.vm.broadcast(pk);
        router.swap(
            ctx.v4Pool,
            SwapParams({
                zeroForOne: zeroForOne,
                amountSpecified: amountSpecified,
                sqrtPriceLimitX96: zeroForOne
                    ? TickMath.MIN_SQRT_PRICE + 1
                    : TickMath.MAX_SQRT_PRICE - 1
            }),
            PoolSwapTest.TestSettings({takeClaims: false, settleUsingBurn: false}),
            ""
        );
    }
}
```

- [ ] **Step 2: Verify it compiles**

Run: `forge build`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add foundry-script/simulation/JitGame.sol
git commit -m "feat(simulation): add executeSwapWithAmount — parameterized trade size for JIT game"
```

### Task 5: Add funding helpers

**Files:**
- Modify: `foundry-script/simulation/JitGame.sol`

- [ ] **Step 1: Write fundJitAccounts function**

Add to `JitGame.sol`:

```solidity
import {IERC20} from "forge-std/interfaces/IERC20.sol";

function fundJitAccounts(
    Vm vm,
    JitAccounts memory acc,
    address tokenA,
    address tokenB,
    uint256 unitLiquidity,
    uint256 jitCapital
) {
    // Fund passive LPs: 1 unit each
    for (uint256 i; i < acc.passiveLps.length; ++i) {
        address lp = acc.passiveLps[i].addr;
        vm.deal(lp, 1 ether);
        deal(tokenA, lp, unitLiquidity);
        deal(tokenB, lp, unitLiquidity);
    }
    // Fund JIT LP
    address jit = acc.jitLp.addr;
    vm.deal(jit, 1 ether);
    deal(tokenA, jit, jitCapital);
    deal(tokenB, jit, jitCapital);
    // Fund swapper
    address sw = acc.swapper.addr;
    vm.deal(sw, 1 ether);
    deal(tokenA, sw, unitLiquidity * 10);
    deal(tokenB, sw, unitLiquidity * 10);
}
```

Note: `deal(address token, address to, uint256 amount)` is a forge-std `Test` cheatcode. Since `JitGame.sol` contains free functions (not a Test contract), we need to use `StdCheats.deal` or inline `vm.store`. The orchestrator script (which IS a Script) will handle funding via `deal` directly. **Revise**: Move `fundJitAccounts` into the orchestrator script instead, since it needs `deal()` from `StdCheats`.

```solidity
// In JitGame.sol, only add a validation function:
function validateJitConfig(JitGameConfig memory cfg) pure {
    require(cfg.n >= 2, "JitGame: N must be >= 2");
    require(cfg.jitEntryProbability <= 10000, "JitGame: probability must be <= 10000 bps");
    require(cfg.tradeSize > 0, "JitGame: tradeSize must be > 0");
}
```

- [ ] **Step 2: Verify it compiles**

Run: `forge build`
Expected: PASS

- [ ] **Step 3: Add validation test**

Add to `test/simulation/JitGame.t.sol`:

```solidity
import {validateJitConfig, JitGameConfig} from "@foundry-script/simulation/JitGame.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";

contract JitGameConfigTest is Test {
    function test_validateJitConfig_reverts_n_below_2() public {
        JitGameConfig memory cfg = JitGameConfig({
            n: 1, jitCapital: 1e18, jitEntryProbability: 5000,
            tradeSize: 1e18, zeroForOne: true, protocol: Protocol.UniswapV4
        });
        vm.expectRevert("JitGame: N must be >= 2");
        validateJitConfig(cfg);
    }

    function test_validateJitConfig_reverts_probability_over_10000() public {
        JitGameConfig memory cfg = JitGameConfig({
            n: 5, jitCapital: 1e18, jitEntryProbability: 10001,
            tradeSize: 1e18, zeroForOne: true, protocol: Protocol.UniswapV4
        });
        vm.expectRevert("JitGame: probability must be <= 10000 bps");
        validateJitConfig(cfg);
    }

    function test_validateJitConfig_reverts_zero_tradeSize() public {
        JitGameConfig memory cfg = JitGameConfig({
            n: 5, jitCapital: 1e18, jitEntryProbability: 5000,
            tradeSize: 0, zeroForOne: true, protocol: Protocol.UniswapV4
        });
        vm.expectRevert("JitGame: tradeSize must be > 0");
        validateJitConfig(cfg);
    }

    function test_validateJitConfig_accepts_valid() public pure {
        JitGameConfig memory cfg = JitGameConfig({
            n: 10, jitCapital: 5e18, jitEntryProbability: 7000,
            tradeSize: 1e18, zeroForOne: true, protocol: Protocol.UniswapV4
        });
        validateJitConfig(cfg);
    }
}
```

- [ ] **Step 4: Run tests**

Run: `MNEMONIC="test test test test test test test test test test test junk" forge test --match-path "test/simulation/JitGame.t.sol" -vv`
Expected: All tests PASS (previous 4 + new 4 = 8 total)

- [ ] **Step 5: Commit**

```bash
git add foundry-script/simulation/JitGame.sol test/simulation/JitGame.t.sol
git commit -m "feat(simulation): add validateJitConfig + executeSwapWithAmount"
```

---

## Chunk 3: Game Execution Core

### Task 6: Implement runJitGame

**Files:**
- Modify: `foundry-script/simulation/JitGame.sol`

- [ ] **Step 1: Write runJitGame function**

Add to `JitGame.sol`:

```solidity
import {Scenario, mintPosition, burnPosition} from "@foundry-script/types/Scenario.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";

uint256 constant UNIT_LIQUIDITY = 1e18;

function runJitGame(
    Context storage ctx,
    Scenario storage s,
    JitGameConfig memory cfg,
    JitAccounts memory acc
) returns (JitGameResult memory result) {
    validateJitConfig(cfg);

    // ── Step 2: Passive LP entry ──
    uint256[] memory passiveTokenIds = new uint256[](cfg.n);
    for (uint256 i; i < cfg.n; ++i) {
        passiveTokenIds[i] = mintPosition(
            ctx, s, cfg.protocol, acc.passiveLps[i].privateKey, UNIT_LIQUIDITY
        );
    }

    // ── Step 3: JIT decision ──
    uint256 jitTokenId;
    uint256 roll = ctx.vm.randomUint(0, 9999);
    if (roll < cfg.jitEntryProbability) {
        result.jitEntered = true;
        jitTokenId = mintPosition(
            ctx, s, cfg.protocol, acc.jitLp.privateKey, cfg.jitCapital
        );
    }

    // ── Step 4: Trade arrives ──
    executeSwapWithAmount(
        ctx, cfg.protocol, acc.swapper.privateKey, cfg.zeroForOne, int256(cfg.tradeSize)
    );

    // ── Step 5: JIT exit ──
    if (result.jitEntered) {
        // Record JIT payout via balance-delta
        address jitAddr = acc.jitLp.addr;
        (address tokenA, address tokenB) = resolveTokensFromCtx(ctx);
        uint256 jitBalABefore = IERC20(tokenA).balanceOf(jitAddr);
        uint256 jitBalBBefore = IERC20(tokenB).balanceOf(jitAddr);

        burnPosition(ctx, cfg.protocol, acc.jitLp.privateKey, jitTokenId, cfg.jitCapital);

        result.jitLpPayout = (IERC20(tokenA).balanceOf(jitAddr) - jitBalABefore)
            + (IERC20(tokenB).balanceOf(jitAddr) - jitBalBBefore);
    }

    // ── Step 6: Passive LP exit + fee tracking ──
    // Note: Payouts sum both token0 and token1 balance deltas as raw uint256.
    // This is valid for HHI/delta-plus since all LPs share the same tick range
    // and fee tier — relative shares are preserved regardless of token weighting.
    uint256[] memory payouts = new uint256[](cfg.n);
    for (uint256 i; i < cfg.n; ++i) {
        address lpAddr = acc.passiveLps[i].addr;
        (address tokenA, address tokenB) = resolveTokensFromCtx(ctx);
        uint256 balABefore = IERC20(tokenA).balanceOf(lpAddr);
        uint256 balBBefore = IERC20(tokenB).balanceOf(lpAddr);

        burnPosition(ctx, cfg.protocol, acc.passiveLps[i].privateKey, passiveTokenIds[i], UNIT_LIQUIDITY);

        payouts[i] = (IERC20(tokenA).balanceOf(lpAddr) - balABefore)
            + (IERC20(tokenB).balanceOf(lpAddr) - balBBefore);
    }

    result.hedgedLpPayout = payouts[acc.hedgedIndex];

    // Worst non-hedged LP
    uint256 minPayout = type(uint256).max;
    for (uint256 i; i < cfg.n; ++i) {
        if (i != acc.hedgedIndex && payouts[i] < minPayout) {
            minPayout = payouts[i];
        }
    }
    result.unhedgedLpPayout = minPayout;

    // ── Step 7: Measure delta-plus (inline HHI) ──
    result.deltaPlus = computeDeltaPlus(payouts, cfg.n);
}

/// @dev HHI-based delta-plus: sum((s_i)^2) - 1/N, where s_i = payout_i / totalPayout
/// Returns Q128 fixed-point to match existing FCI convention.
function computeDeltaPlus(uint256[] memory payouts, uint256 n) pure returns (uint128) {
    uint256 total;
    for (uint256 i; i < n; ++i) {
        total += payouts[i];
    }
    if (total == 0) return 0; // No fees accrued — equilibrium by default

    // HHI = sum(share_i^2), share_i = payout_i / total
    // We compute in 1e18 precision then convert to Q128
    uint256 hhi;
    for (uint256 i; i < n; ++i) {
        uint256 share = (payouts[i] * 1e18) / total;
        hhi += (share * share) / 1e18;
    }
    // delta-plus = HHI - 1/N (in 1e18)
    uint256 baseline = 1e18 / n;
    if (hhi <= baseline) return 0;
    uint256 deltaPlusE18 = hhi - baseline;

    // Convert to Q128: deltaPlusE18 * 2^128 / 1e18
    return uint128((deltaPlusE18 << 128) / 1e18);
}

/// @dev Extract token addresses from Context. For V4, read from PoolKey.
/// Currency wraps address as bytes32 via Currency.wrap(). Unwrap reverses.
function resolveTokensFromCtx(Context storage ctx) view returns (address, address) {
    return (
        Currency.unwrap(ctx.v4Pool.currency0),
        Currency.unwrap(ctx.v4Pool.currency1)
    );
}
```

- [ ] **Step 2: Add Currency import**

```solidity
import {Currency} from "v4-core/src/types/Currency.sol";
```

- [ ] **Step 3: Verify it compiles**

Run: `forge build`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add foundry-script/simulation/JitGame.sol
git commit -m "feat(simulation): implement runJitGame — N-LP game with JIT entry, fee tracking, HHI delta-plus"
```

### Task 7: Unit test computeDeltaPlus

**Files:**
- Modify: `test/simulation/JitGame.t.sol`

- [ ] **Step 1: Write delta-plus computation tests**

Add to `test/simulation/JitGame.t.sol`:

```solidity
import {computeDeltaPlus} from "@foundry-script/simulation/JitGame.sol";

contract ComputeDeltaPlusTest is Test {
    /// All equal payouts → HHI = 1/N → delta-plus = 0
    function test_computeDeltaPlus_equilibrium() public pure {
        uint256[] memory payouts = new uint256[](4);
        payouts[0] = 100;
        payouts[1] = 100;
        payouts[2] = 100;
        payouts[3] = 100;
        uint128 dp = computeDeltaPlus(payouts, 4);
        assertEq(dp, 0, "equal payouts should give delta-plus = 0");
    }

    /// One LP gets everything → HHI = 1 → delta-plus = 1 - 1/N
    function test_computeDeltaPlus_monopoly() public pure {
        uint256[] memory payouts = new uint256[](4);
        payouts[0] = 1000;
        payouts[1] = 0;
        payouts[2] = 0;
        payouts[3] = 0;
        uint128 dp = computeDeltaPlus(payouts, 4);
        // delta-plus = 1 - 0.25 = 0.75 in Q128
        uint128 expected = uint128((75e16 << 128) / 1e18);
        // Allow 1 unit rounding
        assertApproxEqAbs(dp, expected, 1, "monopoly should give delta-plus ~ 0.75");
    }

    /// Zero total payout → delta-plus = 0
    function test_computeDeltaPlus_zero_total() public pure {
        uint256[] memory payouts = new uint256[](3);
        uint128 dp = computeDeltaPlus(payouts, 3);
        assertEq(dp, 0, "zero fees should give delta-plus = 0");
    }

    /// Two LPs, 1:2 split → HHI = (1/3)^2 + (2/3)^2 = 5/9
    /// delta-plus = 5/9 - 1/2 = 1/18 ≈ 0.0556
    function test_computeDeltaPlus_mild_concentration() public pure {
        uint256[] memory payouts = new uint256[](2);
        payouts[0] = 1e18;
        payouts[1] = 2e18;
        uint128 dp = computeDeltaPlus(payouts, 2);
        // 1/18 in Q128
        uint128 expected = uint128((uint256(1e18) / 18 << 128) / 1e18);
        assertApproxEqAbs(dp, expected, 1e30, "1:2 split should give delta-plus ~ 0.0556");
    }
}
```

- [ ] **Step 2: Run tests**

Run: `MNEMONIC="test test test test test test test test test test test junk" forge test --match-path "test/simulation/JitGame.t.sol" -vv`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add test/simulation/JitGame.t.sol
git commit -m "test(simulation): add computeDeltaPlus unit tests — equilibrium, monopoly, zero, mild"
```

---

## Chunk 4: Script Orchestrator

### Task 8: Rewrite CapponiJITSequentialGame.s.sol

**Files:**
- Modify: `foundry-script/simulation/CapponiJITSequentialGame.s.sol`

- [ ] **Step 1: Rewrite the orchestrator script**

Replace the entire file contents:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script, console} from "forge-std/Script.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";

import {Context} from "@foundry-script/types/Context.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";
import {Scenario} from "@foundry-script/types/Scenario.sol";
import {
    JitGameConfig,
    JitGameResult,
    JitAccounts,
    initJitAccounts,
    runJitGame,
    UNIT_LIQUIDITY
} from "@foundry-script/simulation/JitGame.sol";
import {
    resolveDeployments,
    Deployments,
    UNICHAIN_SEPOLIA,
    resolveTokens
} from "@foundry-script/utils/Deployments.sol";
import "@foundry-script/utils/Constants.sol";

contract CapponiJITSequentialGameScript is Script {
    Context ctx;
    Scenario scenario;

    function run(
        uint256 n,
        uint256 jitCapital,
        uint256 jitEntryProbability,
        uint256 tradeSize
    ) public {
        // ── 1. Fork ──
        vm.createSelectFork("unichain_sepolia");
        uint256 chainId = block.chainid;

        // ── 2. Build Context ──
        Deployments memory d = resolveDeployments(chainId, Protocol.UniswapV4);
        (address tokenA, address tokenB) = resolveTokens(chainId);

        ctx.vm = vm;
        ctx.v4PositionManager = d.positionManager;
        ctx.v4SwapRouter = d.swapRouter;
        ctx.chainId = chainId;

        // Build PoolKey — standard 0.30% fee tier, tick spacing 60
        ctx.v4Pool = PoolKey({
            currency0: Currency.wrap(tokenA),
            currency1: Currency.wrap(tokenB),
            fee: 3000,
            tickSpacing: 60,
            hooks: IHooks(address(0))
        });

        // ── 3. Build Config ──
        JitGameConfig memory cfg = JitGameConfig({
            n: n,
            jitCapital: jitCapital,
            jitEntryProbability: jitEntryProbability,
            tradeSize: tradeSize,
            zeroForOne: true,
            protocol: Protocol.UniswapV4
        });

        // ── 4. Generate and fund accounts ──
        JitAccounts memory acc = initJitAccounts(vm, n);
        _fundAccounts(acc, tokenA, tokenB, jitCapital);
        _approveAll(acc, tokenA, tokenB, d.positionManager, d.swapRouter);

        // ── 5. Run game ──
        JitGameResult memory result = runJitGame(ctx, scenario, cfg, acc);

        // ── 6. Emit results ──
        console.log("=== Capponi JIT Sequential Game Results ===");
        console.log("N (passive LPs):", n);
        console.log("JIT capital:", jitCapital);
        console.log("JIT entry prob (bps):", jitEntryProbability);
        console.log("Trade size:", tradeSize);
        console.log("JIT entered:", result.jitEntered);
        console.log("Delta-plus (Q128):", uint256(result.deltaPlus));
        console.log("Hedged LP payout:", result.hedgedLpPayout);
        console.log("Unhedged LP payout (worst):", result.unhedgedLpPayout);
        console.log("JIT LP payout:", result.jitLpPayout);
    }

    function _fundAccounts(
        JitAccounts memory acc,
        address tokenA,
        address tokenB,
        uint256 jitCapital
    ) internal {
        for (uint256 i; i < acc.passiveLps.length; ++i) {
            address lp = acc.passiveLps[i].addr;
            vm.deal(lp, 1 ether);
            deal(tokenA, lp, UNIT_LIQUIDITY);
            deal(tokenB, lp, UNIT_LIQUIDITY);
        }
        vm.deal(acc.jitLp.addr, 1 ether);
        deal(tokenA, acc.jitLp.addr, jitCapital);
        deal(tokenB, acc.jitLp.addr, jitCapital);

        vm.deal(acc.swapper.addr, 1 ether);
        deal(tokenA, acc.swapper.addr, UNIT_LIQUIDITY * 10);
        deal(tokenB, acc.swapper.addr, UNIT_LIQUIDITY * 10);
    }

    function _approveAll(
        JitAccounts memory acc,
        address tokenA,
        address tokenB,
        address positionManager,
        address swapRouter
    ) internal {
        for (uint256 i; i < acc.passiveLps.length; ++i) {
            _approveFor(acc.passiveLps[i].privateKey, tokenA, tokenB, positionManager);
        }
        _approveFor(acc.jitLp.privateKey, tokenA, tokenB, positionManager);
        _approveFor(acc.swapper.privateKey, tokenA, tokenB, swapRouter);
    }

    function _approveFor(
        uint256 pk,
        address tokenA,
        address tokenB,
        address spender
    ) internal {
        vm.startBroadcast(pk);
        IERC20(tokenA).approve(spender, type(uint256).max);
        IERC20(tokenB).approve(spender, type(uint256).max);
        vm.stopBroadcast();
    }
}
```

- [ ] **Step 2: Verify it compiles**

Run: `forge build`
Expected: PASS (may have warnings about unresolved tokens on Unichain Sepolia — that's fine, tokens are `address(0)` in Deployments.sol TODO)

- [ ] **Step 3: Commit**

```bash
git add foundry-script/simulation/CapponiJITSequentialGame.s.sol
git commit -m "feat(simulation): rewrite CapponiJITSequentialGame orchestrator — parameterized N-LP JIT game"
```

### Task 9: Integration test on Anvil fork

**Files:**
- Create: `test/simulation/CapponiJITSequentialGame.fork.t.sol`

- [ ] **Step 1: Write fork integration test**

This test deploys mock tokens on the Anvil fork, creates a V4 pool, and runs the full game. It validates the complete flow end-to-end.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test, console} from "forge-std/Test.sol";
import {Deployers} from "v4-core/test/utils/Deployers.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";

import {Context} from "@foundry-script/types/Context.sol";
import {Protocol} from "@foundry-script/types/Protocol.sol";
import {Scenario} from "@foundry-script/types/Scenario.sol";
import {
    JitGameConfig,
    JitGameResult,
    JitAccounts,
    initJitAccounts,
    runJitGame,
    UNIT_LIQUIDITY
} from "@foundry-script/simulation/JitGame.sol";
import "@foundry-script/utils/Constants.sol";

contract CapponiJITSequentialGameForkTest is Test, Deployers {
    Context ctx;
    Scenario scenario;

    function setUp() public {
        // Deploy fresh V4 infra (PoolManager, tokens, routers)
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();

        // Initialize pool
        (key,) = initPool(
            currency0,
            currency1,
            IHooks(address(0)),
            3000,
            TickMath.getSqrtPriceAtTick(0)
        );

        // Wire Context
        ctx.vm = vm;
        ctx.v4Pool = key;
        ctx.v4PositionManager = address(posm);
        ctx.v4SwapRouter = address(swapRouter);
        ctx.chainId = block.chainid;
    }

    function test_jitGame_equilibrium_no_jit_entry() public {
        uint256 n = 5;
        JitAccounts memory acc = initJitAccounts(vm, n);

        // Fund all accounts
        for (uint256 i; i < n; ++i) {
            address lp = acc.passiveLps[i].addr;
            vm.deal(lp, 1 ether);
            deal(Currency.unwrap(currency0), lp, UNIT_LIQUIDITY);
            deal(Currency.unwrap(currency1), lp, UNIT_LIQUIDITY);
            vm.prank(lp);
            IERC20(Currency.unwrap(currency0)).approve(address(posm), type(uint256).max);
            vm.prank(lp);
            IERC20(Currency.unwrap(currency1)).approve(address(posm), type(uint256).max);
        }
        // Fund swapper
        vm.deal(acc.swapper.addr, 1 ether);
        deal(Currency.unwrap(currency0), acc.swapper.addr, UNIT_LIQUIDITY * 10);
        deal(Currency.unwrap(currency1), acc.swapper.addr, UNIT_LIQUIDITY * 10);
        vm.prank(acc.swapper.addr);
        IERC20(Currency.unwrap(currency0)).approve(address(swapRouter), type(uint256).max);
        vm.prank(acc.swapper.addr);
        IERC20(Currency.unwrap(currency1)).approve(address(swapRouter), type(uint256).max);

        JitGameConfig memory cfg = JitGameConfig({
            n: n,
            jitCapital: 5e18,
            jitEntryProbability: 0,  // JIT never enters
            tradeSize: 1e15,
            zeroForOne: true,
            protocol: Protocol.UniswapV4
        });

        JitGameResult memory result = runJitGame(ctx, scenario, cfg, acc);

        assertFalse(result.jitEntered, "JIT should not enter at 0% probability");
        assertEq(result.jitLpPayout, 0, "JIT payout should be 0 when not entered");
        // With equal liquidity and no JIT, delta-plus should be ~0
        assertApproxEqAbs(result.deltaPlus, 0, 1e30, "delta-plus should be ~0 with equal LPs");
    }

    function test_jitGame_concentration_with_guaranteed_jit() public {
        uint256 n = 3;
        JitAccounts memory acc = initJitAccounts(vm, n);

        // Fund passive LPs
        for (uint256 i; i < n; ++i) {
            address lp = acc.passiveLps[i].addr;
            vm.deal(lp, 1 ether);
            deal(Currency.unwrap(currency0), lp, UNIT_LIQUIDITY);
            deal(Currency.unwrap(currency1), lp, UNIT_LIQUIDITY);
            vm.prank(lp);
            IERC20(Currency.unwrap(currency0)).approve(address(posm), type(uint256).max);
            vm.prank(lp);
            IERC20(Currency.unwrap(currency1)).approve(address(posm), type(uint256).max);
        }
        // Fund JIT LP
        vm.deal(acc.jitLp.addr, 1 ether);
        deal(Currency.unwrap(currency0), acc.jitLp.addr, 10e18);
        deal(Currency.unwrap(currency1), acc.jitLp.addr, 10e18);
        vm.prank(acc.jitLp.addr);
        IERC20(Currency.unwrap(currency0)).approve(address(posm), type(uint256).max);
        vm.prank(acc.jitLp.addr);
        IERC20(Currency.unwrap(currency1)).approve(address(posm), type(uint256).max);
        // Fund swapper
        vm.deal(acc.swapper.addr, 1 ether);
        deal(Currency.unwrap(currency0), acc.swapper.addr, UNIT_LIQUIDITY * 10);
        deal(Currency.unwrap(currency1), acc.swapper.addr, UNIT_LIQUIDITY * 10);
        vm.prank(acc.swapper.addr);
        IERC20(Currency.unwrap(currency0)).approve(address(swapRouter), type(uint256).max);
        vm.prank(acc.swapper.addr);
        IERC20(Currency.unwrap(currency1)).approve(address(swapRouter), type(uint256).max);

        JitGameConfig memory cfg = JitGameConfig({
            n: n,
            jitCapital: 10e18,
            jitEntryProbability: 10000,  // JIT always enters
            tradeSize: 1e15,
            zeroForOne: true,
            protocol: Protocol.UniswapV4
        });

        JitGameResult memory result = runJitGame(ctx, scenario, cfg, acc);

        assertTrue(result.jitEntered, "JIT should enter at 100% probability");
        assertTrue(result.jitLpPayout > 0, "JIT should earn fees");
        // JIT with 10x capital vs 1 unit each → significant extraction
        console.log("Delta-plus (Q128):", uint256(result.deltaPlus));
        console.log("JIT payout:", result.jitLpPayout);
        console.log("Hedged LP payout:", result.hedgedLpPayout);
        console.log("Unhedged LP payout:", result.unhedgedLpPayout);
    }
}
```

Note: This test uses `Deployers` from v4-core test utils which deploys fresh infrastructure locally (no fork needed). This is the correct approach for CI. The actual Unichain Sepolia fork is used only in the script orchestrator.

- [ ] **Step 2: Run fork integration tests**

Run: `MNEMONIC="test test test test test test test test test test test junk" forge test --match-path "test/simulation/CapponiJITSequentialGame.fork.t.sol" -vvv`
Expected: Both tests PASS. The second test should show non-zero delta-plus and JIT payout in logs.

- [ ] **Step 3: Commit**

```bash
git add test/simulation/CapponiJITSequentialGame.fork.t.sol
git commit -m "test(simulation): add CapponiJITSequentialGame integration tests — equilibrium + JIT concentration"
```

---

## Chunk 5: Final Verification

### Task 10: Full test suite and cleanup

- [ ] **Step 1: Run all simulation tests together**

Run: `MNEMONIC="test test test test test test test test test test test junk" forge test --match-path "test/simulation/*" -vv`
Expected: All tests PASS

- [ ] **Step 2: Run full project test suite to check for regressions**

Run: `forge test -vv`
Expected: No regressions in existing tests

- [ ] **Step 3: Verify compilation of the script invocation path**

Run: `forge build`
Expected: Clean build, no warnings

- [ ] **Step 4: Final commit with any cleanup**

```bash
git add -A
git commit -m "chore(simulation): final cleanup — Capponi JIT sequential game complete"
```
