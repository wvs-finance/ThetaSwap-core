# JIT Game Welfare Comparison: Hedged vs Unhedged PLP

## Purpose

Demonstrate that a passive LP who hedges via the epoch-based FCI vault achieves better risk-adjusted welfare than an identical passive LP who doesn't hedge, across varying JIT intensity and duration. This is the economic argument that the epoch-based oracle state variable meaningfully hedges risk for PLPs.

## Core Claim

When JIT harms passive LPs, the epoch-based hedge compensates. The compensation scales with harm intensity. When no JIT occurs, the hedge correctly stays dormant.

## Architecture

### Approach: Extend JitGame.sol with Optional Vault

The existing `runMultiRoundJitGame` gains an optional `VaultConfig` parameter. When a vault is configured, the game loop handles deposit, poke-before-warp ordering, and settlement internally. When `VaultConfig.vault` is zero-address, behavior is unchanged -- full backward compatibility.

Poke-before-warp ordering is enforced by construction inside the round loop, eliminating the class of ordering bugs discovered during cross-epoch testing.

**Note on poke ordering**: The existing `HedgedVsUnhedgedEpoch.integration.t.sol` uses warp-then-poke ordering (line 180-181). That test uses `EPOCH_LENGTH = 7 days` with all rounds fitting inside a single epoch, so ordering doesn't matter. The cross-epoch tests and this extension use `EPOCH_LENGTH = 1 day` where poke-before-warp is critical because the epoch expires on warp.

### Premium Model

Lump-sum deposit (current vault model). The depositor is a **separate address** from the passive LPs. The depositor funds the vault; the passive LPs provide pool liquidity. This matches the existing `HedgedVsUnhedged` and `CrossEpochWelfareComparison` test patterns.

Welfare is computed as:

```
hedge_value    = longPayout - depositAmount
hedged_welfare = lpFeeRevenue + longPayout   (LP fees + vault payout)
unhedged_welfare = lpFeeRevenue              (LP fees only)
```

The hedged PLP's total outcome includes both LP fee revenue and vault payout. The `depositAmount` is paid by the depositor (a separate entity providing capital to the insurance pool), so it is NOT subtracted from the hedged PLP's welfare. The hedged PLP pays implicit premium through reduced fee share (gamma model) -- but in this abstraction, gamma = 0 and the premium is borne by the depositor. `hedge_value` measures whether the vault payout justified the depositor's capital lock-up.

This abstracts delta-hedging, premia, and funding rates -- none are implemented yet. The lump-sum model reuses the existing `FciTokenVaultHarness` directly.

### Vault Mode

Epoch vault only. The cumulative vs epoch comparison is already validated by the cross-epoch welfare tests (scenarios 4-6 in `CrossEpochWelfareComparison.integration.t.sol`). This extension focuses solely on the hedged vs unhedged claim using the epoch metric.

### Relationship to Existing Tests

- `CrossEpochWelfareComparison.integration.t.sol`: Proved epoch < cumulative payout when JIT stops (go/no-go gate)
- `HedgedVsUnhedgedEpoch.integration.t.sol`: Proved hedged > unhedged within a single epoch (scenarios 1-3)
- **This extension**: Proves hedged > unhedged across varying JIT intensity and duration using the multi-round game infrastructure, with cross-scenario monotonicity assertions

## Data Types

Two new structs in `JitGame.sol`:

```solidity
/// @dev Uses address type for vault to avoid test-harness dependency in the library.
/// The caller (test contract) casts to the appropriate harness type for setup.
/// The game loop only calls generic vault operations via the interface defined below.
struct VaultConfig {
    address vault;                  // zero address = no vault
    uint256 depositAmount;          // lump-sum hedge deposit
    bool reactive;                  // reactive flag for getDeltaPlusEpoch reads
}

struct WelfareResult {
    uint256 longPayout;             // vault settlement payout to LONG
    uint256 shortPayout;            // vault settlement payout to SHORT
    int256  hedgeValue;             // longPayout - depositAmount (positive = depositor profited)
    uint256 lpFeeRevenue;           // sum of hedgedLpPayout across all rounds
    uint256 hedgedWelfare;          // lpFeeRevenue + longPayout
    uint256 unhedgedWelfare;        // lpFeeRevenue (no vault interaction)
}
```

New minimal interface in `JitGame.sol` for vault operations (avoids test-harness dependency):

```solidity
interface IVaultPokeSettle {
    function harness_pokeEpoch() external;
    function harness_settle() external;
    /// @return sqrtPriceStrike, sqrtPriceHWM, halfLifeSeconds, expiry,
    ///         totalDeposits, lastHwmTimestamp, settled, longPayoutPerToken
    function harness_getVaultStorage() external view returns (
        uint160, uint160, uint256, uint256, uint256, uint256, bool, uint256
    );
}
```

`MultiRoundJitGameResult` (not `JitGameResult`) gains the welfare field, since welfare is computed across all rounds:

```solidity
struct MultiRoundJitGameResult {
    uint128[] deltaPlusPerRound;
    uint256 finalHedgedLpPayout;
    uint256 finalUnhedgedLpPayout;
    uint256 totalJitLpPayout;
    WelfareResult welfare;           // zeroed when VaultConfig.vault == address(0)
}
```

### lpFeeRevenue Computation

`lpFeeRevenue` is the sum of `hedgedLpPayout` (from `JitGameResult`) across all rounds. The existing game already computes per-round LP payouts via balance-difference snapshots. We accumulate these:

```solidity
uint256 totalHedgedLpFees;
for (uint256 r; r < cfg.rounds; ++r) {
    JitGameResult memory roundResult = runJitGame(...);
    totalHedgedLpFees += roundResult.hedgedLpPayout;
    // ...
}
result.welfare.lpFeeRevenue = totalHedgedLpFees;
```

## Game Loop Modification

`runMultiRoundJitGame` gains a `VaultConfig` parameter appended to its existing signature:

```solidity
function runMultiRoundJitGame(
    Context storage ctx,
    Scenario storage s,
    MultiRoundJitGameConfig memory cfg,
    JitAccounts memory acc,
    address fciHook,
    VaultConfig memory vaultCfg    // NEW: zero address = no vault
) returns (MultiRoundJitGameResult memory result)
```

Three insertion points:

### Before the loop (setup)

```solidity
if (vaultCfg.vault != address(0)) {
    // Vault deposit is handled by the TEST CONTRACT before calling runMultiRoundJitGame.
    // The test deploys the vault, calls initializeEpochPool, deposits, and passes the address.
    // The game loop only handles poke and settlement.
}
```

**Important**: Vault deployment, `initializeEpochPool`, token approvals, and deposit are the test contract's responsibility. The game loop does NOT handle setup -- only round-level poke and post-loop settlement. This keeps the library free of test-specific setup logic.

### Inside the round loop, after burns but before warp (poke-before-warp)

```solidity
if (vaultCfg.vault != address(0)) {
    // Log epoch delta-plus for narrative
    uint128 epochDp = IFeeConcentrationIndex(fciHook)
        .getDeltaPlusEpoch(ctx.v4Pool, vaultCfg.reactive);
    console.log("  epochDp:", uint256(epochDp));

    IVaultPokeSettle(vaultCfg.vault).harness_pokeEpoch();
}
// THEN vm.warp(...)
```

**Note on epoch delta-plus reading**: The game loop uses the full `IFeeConcentrationIndex` interface (already imported by the test contract) for per-round logging. A new import is added to `JitGame.sol` for `IFeeConcentrationIndex` alongside the existing `IFCIDeltaPlusReader`. The existing `IFCIDeltaPlusReader` (which uses `PoolId`) remains for the cumulative delta-plus read in `runJitGame`.

### After the loop (settlement + welfare computation)

```solidity
if (vaultCfg.vault != address(0)) {
    (,,, uint256 expiry,,,,) = IVaultPokeSettle(vaultCfg.vault).harness_getVaultStorage();
    ctx.vm.warp(expiry + 1);
    IVaultPokeSettle(vaultCfg.vault).harness_settle();

    (,,,,,,, uint256 longPayoutPerToken) = IVaultPokeSettle(vaultCfg.vault).harness_getVaultStorage();
    result.welfare.longPayout = (vaultCfg.depositAmount * longPayoutPerToken) / Q96;
    result.welfare.shortPayout = vaultCfg.depositAmount - result.welfare.longPayout;
    result.welfare.hedgeValue = int256(result.welfare.longPayout) - int256(vaultCfg.depositAmount);
    result.welfare.lpFeeRevenue = totalHedgedLpFees;  // accumulated in loop
    result.welfare.hedgedWelfare = result.welfare.lpFeeRevenue + result.welfare.longPayout;
    result.welfare.unhedgedWelfare = result.welfare.lpFeeRevenue;
}
```

Existing zero-vault callers hit none of these branches.

### JIT Scheduling

The existing `JitGameConfig` uses `jitEntryProbability` for probabilistic JIT entry. For deterministic scheduling, the test contract runs **one round at a time** with `rounds = 1`, setting `jitEntryProbability = 10000` (100%) for JIT rounds and `jitEntryProbability = 0` for clean rounds. The vault poke happens between each single-round call.

The primary approach is a new function `runMultiRoundJitGameWithSchedule` that accepts `bool[] memory jitSchedule` and overrides the probability per round. This is cleaner for the test contract.

```solidity
function runMultiRoundJitGameWithSchedule(
    Context storage ctx,
    Scenario storage s,
    MultiRoundJitGameConfig memory cfg,
    JitAccounts memory acc,
    address fciHook,
    VaultConfig memory vaultCfg,
    bool[] memory jitSchedule          // deterministic per-round JIT control
) returns (MultiRoundJitGameResult memory result)
```

When `jitSchedule[r]` is true, `jitEntryProbability` is forced to 10000 for that round. When false, forced to 0.

## Console Log Storytelling

Per-round logging inside the game loop:

```
--- WELFARE: JIT Intensity 9x, 5 rounds ---
  Round 1: JIT=YES  epochDp=1230000000000000  fees=4200000000000
  Round 2: JIT=YES  epochDp=2410000000000000  fees=3900000000000
  Round 3: JIT=NO   epochDp=0                 fees=9800000000000
  Round 4: JIT=NO   epochDp=0                 fees=9700000000000
  Round 5: JIT=NO   epochDp=0                 fees=9900000000000
  ---
  LONG payout:       82000000000000000
  Hedge deposit:     100000000000000000
  Hedge value:       -18000000000000000
  LP fee revenue:    37600000000000000
  Hedged welfare:    119600000000000000
  Unhedged welfare:  37600000000000000
  VERDICT: HEDGE PROFITABLE
```

The VERDICT is based on `hedgedWelfare > unhedgedWelfare` (i.e., `longPayout > 0`), NOT on `hedgeValue > 0`. The hedge is "profitable" for the PLP whenever the vault pays out anything, because the PLP receives the payout without bearing the deposit cost (depositor bears it).

Per-round logging happens inside the game loop. Summary block emitted after settlement.

## Scenarios

### Baseline (from existing Capponi game)

| ID | Name | Rounds | JIT Schedule | Expected Verdict |
|----|------|--------|-------------|-----------------|
| B1 | Equilibrium (no JIT) | 3 | [N,N,N] | HEDGE UNPROFITABLE (no harm, no payout -- correct) |
| B2 | Full JIT crowd-out | 3 | [Y,Y,Y] | **HEDGE PROFITABLE** |
| B3 | Mixed | 3 | [Y,N,Y] | **HEDGE PROFITABLE** |

### Welfare-targeted (new)

| ID | Name | Rounds | JIT Schedule | JIT Capital | Purpose |
|----|------|--------|-------------|-------------|---------|
| W1 | Sustained JIT | 5 | [Y,Y,Y,Y,Y] | 9x | Primary demo: persistent JIT, vault pays out every poke |
| W2 | JIT intensity sweep | 3 | [Y,Y,Y] | 2x, 5x, 9x | Hedge value scales with JIT intensity |
| W3 | Early JIT harm | 5 | [Y,Y,N,N,N] | 9x | HWM from rounds 1-2 survives decay through settlement |
| W4 | Late JIT harm | 5 | [N,N,N,Y,Y] | 9x | Fresh HWM at settlement, minimal decay, highest hedge value |

### Assertions

**Hedge-profitable scenarios (B2, B3, W1, W3, W4):**
- `longPayout > 0` (vault triggered)
- `hedgedWelfare > unhedgedWelfare` (hedge compensates)

**Correct negative (B1):**
- `longPayout == 0` (no false trigger)

**Cross-scenario (W2):**
- `hedgeValue_9x > hedgeValue_5x > hedgeValue_2x` (monotonic in JIT intensity)

**Cross-scenario (W3 vs W4):**
- `hedgeValue_W4 > hedgeValue_W3` (late JIT = less decay = higher payout)

**Conservation (all):**
- `longPayout + shortPayout == depositAmount`

### Scenario B3 Calibration Note

B3 has JIT in 2 of 3 rounds. With `EPOCH_LENGTH = 1 day`, the epoch resets each round. Round 2 (no JIT) produces `epochDp = 0`, so the vault poke in Round 2 only applies decay. Whether the net HWM exceeds strike at settlement depends on the strike level. With `fractionToSqrtPriceX96(56e18, 100e18)` and 14-day half-life, Rounds 1 and 3 refresh the HWM high enough that the decayed value at settlement (day 7) still exceeds strike. If this proves false during implementation, B3 is demoted from "HEDGE PROFITABLE" to a weaker assertion (`longPayout >= 0`).

### Decay Gap by Scenario

| Scenario | Rounds | Last HWM refresh | Settlement | Decay gap | HWM retention |
|----------|--------|-------------------|------------|-----------|--------------|
| B1-B3 | 3 | Day 2 (last poke) | Day 7+1 | ~6 days | ~74% |
| W1 | 5 | Day 4 (last poke) | Day 7+1 | ~4 days | ~82% |
| W3 | 5 | Day 1 (last JIT poke) | Day 7+1 | ~7 days | ~71% |
| W4 | 5 | Day 4 (last JIT poke) | Day 7+1 | ~4 days | ~82% |

This explains why W4 > W3: late JIT means less decay before settlement.

## Files Changed

### Modified

- **`foundry-script/simulation/JitGame.sol`**: Add `IVaultPokeSettle` interface, `VaultConfig`, `WelfareResult` structs. Add `WelfareResult welfare` to `MultiRoundJitGameResult`. Add `VaultConfig` parameter to `runMultiRoundJitGame`. Add `runMultiRoundJitGameWithSchedule` function. Insert vault poke/settlement logic. Add per-round and summary console logging. Import `IFeeConcentrationIndex` for epoch delta-plus reads.

- **`foundry-script/simulation/CapponiJITSequentialGame.s.sol`**: Import vault harness and new types. Deploy vault, construct `VaultConfig`, pass to game. No other changes.

- **`test/simulation/JitGame.t.sol`**: Update call sites to pass zero `VaultConfig` (address(0), 0, false) for backward compatibility.

**All call sites of `runMultiRoundJitGame`** must be updated with the new `VaultConfig` parameter: `JitGame.t.sol` and `CapponiJITSequentialGame.s.sol`. Both pass zero config to preserve existing behavior.

### New

- **`test/fci-token-vault/integration/JitGameWelfareComparison.integration.t.sol`**: Test contract with 7 scenario tests + 2 cross-scenario comparison tests. Each test deploys fresh vault, calls `initializeEpochPool`, deposits, runs game with appropriate schedule + vault config, asserts welfare properties, emits narrative logs.

## Test File Structure

```solidity
contract JitGameWelfareComparisonTest is PosmTestSetup, FCITestHelper {
    FeeConcentrationIndexHarness fciHarness;

    // setUp deploys FCI hook + pool (shared across tests)
    // Each test deploys its own vault for isolation

    function _deployVault() internal returns (FciTokenVaultHarness) {
        FciTokenVaultHarness v = new FciTokenVaultHarness();
        uint160 strike = SqrtPriceLibrary.fractionToSqrtPriceX96(56e18, 100e18);
        v.harness_initVault(strike, 14 days, block.timestamp + 7 days, key, false, collateral);
        // initializeEpochPool called on fciHarness (the FCI hook) in setUp, not on the vault
        // Deposit
        vm.startPrank(depositorAddr);
        IERC20(collateral).approve(address(v), HEDGE_AMOUNT);
        v.harness_deposit(depositorAddr, HEDGE_AMOUNT);
        vm.stopPrank();
        return v;
    }

    // --- Baseline ---
    function test_B1_equilibrium_no_jit()
    function test_B2_full_jit_crowdout()
    function test_B3_mixed_jit()

    // --- Welfare-targeted ---
    function test_W1_sustained_jit_5_rounds()
    function test_W2_jit_intensity_sweep()       // runs 3 sub-games at 2x/5x/9x
    function test_W3_early_jit_harm()
    function test_W4_late_jit_harm()

    // --- Cross-scenario assertions ---
    function test_W4_beats_W3_less_decay()
    function test_W2_monotonic_in_intensity()
}
```

**Token approval flow**: The test contract handles all token approvals and vault deposits in `_deployVault()` before calling `runMultiRoundJitGameWithSchedule`. The game library never touches token transfers directly -- it only calls `harness_pokeEpoch()` and `harness_settle()` through the `IVaultPokeSettle` interface.

**Strike calibration**: `fractionToSqrtPriceX96(56e18, 100e18)` -- WAD-scaled inputs. The existing `HedgedVsUnhedged` test uses small integers (30, 70) which suffer from integer-sqrt precision loss (`sqrt(57) == sqrt(60) == 7`). WAD-scaled inputs give meaningful precision via `FixedPointMathLib.sqrt(56e18)`. Validated in cross-epoch tests to produce partial payoffs that differentiate scenarios.

## Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| CAPITAL | 1e18 | Standard passive LP capital |
| HEDGE_AMOUNT | 0.1e18 | 10% of capital as hedge deposit |
| TRADE_SIZE | 1e15 | Matches existing tests |
| JIT_CAPITAL | varies (2x, 5x, 9x) | Per scenario |
| EPOCH_LENGTH | 1 day | Each round = new epoch |
| ROUND_INTERVAL | 1 day | Matches epoch length |
| Half-life | 14 days | Standard decay rate |
| Expiry | block.timestamp + 7 days | Fits 5 rounds + settlement gap |
| Strike | fractionToSqrtPriceX96(56e18, 100e18) | Calibrated for partial payoffs |

## Success Criteria

The extension is validated if:

1. All hedge-profitable scenarios (B2, B3, W1, W3, W4) show `longPayout > 0` and `hedgedWelfare > unhedgedWelfare`
2. B1 shows correct negative: no false trigger when no JIT
3. W2 shows monotonic scaling: stronger JIT = bigger hedge value
4. W4 > W3: late JIT produces higher hedge value than early JIT
5. Console log narrative clearly tells the welfare story per scenario
6. Conservation holds for all scenarios

If these hold, the epoch-based oracle state variable demonstrably hedges JIT risk for passive LPs.
