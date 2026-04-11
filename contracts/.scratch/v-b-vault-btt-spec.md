# VaultB (V_B) -- EVM-TDD Phase 1 (SPECIFY)

**Document type:** BTT Specification (Branching Tree Technique)
**Target file:** `contracts/src/vaults/VaultB.sol`
**Status:** SPECIFY -- no Solidity code changes in this phase
**Date:** 2026-04-09
**Depends on:** Solady ERC-4626 (`lib/solady/src/tokens/ERC4626.sol`), AngstromPoolObserver, PanopticPool OraclePack

---

## Overview

VaultB is the unit-of-account vault in the ThetaSwap Angstrom x Panoptic architecture. It
accepts asset1 deposits, mints V_B_shares (an ERC-20 share token), and exposes an
appreciating share price driven by a pluggable transformation T_B of Angstrom's
globalGrowth accumulator. V_B_shares serve as token1 of the V_A_shares/V_B_shares
Panoptic pool and expose `IRateProvider.getRate()` for Balancer/DeFi composability.

### Architecture Decision: Solady ERC-4626 Inheritance (Option C Hybrid)

VaultB inherits from Solady's ERC-4626 (527 lines, audited, handles inflation attacks via
virtual shares, asymmetric rounding, full preview/max function set). Custom logic is
approximately 50 lines: `totalAssets()` override + T_B call + safety bounds + governor +
IRateProvider. The rest of the ThetaSwap system uses Compose's free-function/diamond
pattern, but VaultB is a standalone vault -- the architectural inconsistency is contained
and deliberate.

### Four-Layer Model

| Layer | Responsibility | VaultB Role |
|---|---|---|
| L4: External Interface | ERC-4626 + IRateProvider | Exposes deposit/withdraw/mint/redeem, getRate() |
| L3: Safety Bounds | Monotonicity, floor, continuity cap | Guards against T_B manipulation or corruption |
| L2: Pluggable Transformation | T_B external contract | Computes rate from growth + price data |
| L1: Data Sources | AngstromPoolObserver, PanopticPool OraclePack | Read-only consumers, no writes |

---

## Inheritance

```
Solady ERC4626
  |-- Solady ERC20
  |     |-- name(), symbol(), decimals(), totalSupply(), balanceOf(), transfer(), ...
  |-- asset(), totalAssets(), deposit(), withdraw(), mint(), redeem(), ...
  |-- convertToShares(), convertToAssets(), preview*(), max*()
  |
VaultB is ERC4626, IRateProvider
  |-- totalAssets() [OVERRIDE -- the ONLY Solady override]
  |-- maxWithdraw() [OVERRIDE -- solvency bound]
  |-- maxRedeem()   [OVERRIDE -- solvency bound]
  |-- asset()       [OVERRIDE -- returns immutable asset1]
  |-- setTransformationFunction()  [custom, governor-only]
  |-- getRate()                    [custom, IRateProvider]
  |-- currentRate()                [custom, view helper]
```

### Solady Virtual Shares

VaultB uses Solady's virtual shares mechanism (`_useVirtualShares() returns true`) with
`_decimalsOffset() returns 0`. This adds 1 to both `totalSupply()` and `totalAssets()` in
conversion computations, mitigating the ERC-4626 inflation/donation attack at negligible
precision cost.

---

## Immutable Construction Parameters

| Parameter | Type | Slot | Purpose |
|---|---|---|---|
| `_asset1` | `address` | immutable | The deposit token (ERC-4626 underlying asset) |
| `_poolId` | `PoolId` | immutable | Which Angstrom pool's growth to track |
| `_observer` | `address` | immutable | AngstromPoolObserver -- growth data source |
| `_panopticPool` | `address` | immutable | PanopticPool -- price oracle for asset0->asset1 conversion |
| `_governor` | `address` | immutable | Can swap T_B (the transformation function contract) |

Note: `_governor` is immutable (not transferable). This is a deliberate trust-minimization
decision. Governor replacement requires deploying a new vault and migrating.

---

## Mutable State

| State | Type | Storage Slot | Mutated By |
|---|---|---|---|
| `transformationFunction` | `address` | computed (keccak) | Governor via `setTransformationFunction()` |
| `lastRate` | `uint256` | computed (keccak) | Internally by `totalAssets()` on successful bounded rate update |

---

## Safety Bound Constants (Hardcoded, NOT Governor-Configurable)

| Constant | Type | Value | Rationale |
|---|---|---|---|
| `FLOOR_RATE` | `uint256` | `1e18` | 1:1 minimum -- no principal loss from transformation |
| `MAX_RATE_INCREASE_PER_CALL` | `uint256` | TBD during implementation | Limits rate jump per call. Depends on expected growth rate |

These are hardcoded constants, not governor-configurable, to minimize the trust surface.

---

## Errors

```
error Unauthorized();
error ZeroAddress();
```

`Unauthorized` -- raised by `setTransformationFunction` when `msg.sender != governor`.

`ZeroAddress` -- raised by `setTransformationFunction` when `newTB == address(0)`.

All other errors (DepositMoreThanMax, MintMoreThanMax, WithdrawMoreThanMax,
RedeemMoreThanMax) are inherited from Solady ERC-4626 and not overridden.

---

## Events

```
event TransformationFunctionUpdated(address indexed oldTB, address indexed newTB);
```

Emitted by `setTransformationFunction` on successful update. All deposit/withdraw events
are inherited from Solady ERC-4626 (`Deposit`, `Withdraw`).

---

## Interfaces Required (To Be Created)

### IRateProvider

```
interface IRateProvider {
    function getRate() external view returns (uint256);
}
```

Standard Balancer-compatible rate provider interface. Single view function returning an
18-decimal scaling factor.

### ITransformationFunction

```
interface ITransformationFunction {
    function computeRate(
        PoolId poolId,
        address observer,
        address panopticPool
    ) external view returns (uint256 rate);
}
```

The pluggable T_B interface. Stateless, no storage, no side effects. Returns rate in
18-decimal (asset1 per share unit). The implementation reads from the observer and
PanopticPool internally.

---

## Section 1: BTT Behavior Trees

### 1.1 Constructor

```
VaultB::constructor
├── when asset1 is address(0)
│   └── it should revert.
├── when observer is address(0)
│   └── it should revert.
├── when panopticPool is address(0)
│   └── it should revert.
├── when governor is address(0)
│   └── it should revert.
└── when all parameters are valid
    ├── it should set _asset1 as the immutable underlying asset.
    ├── it should set _poolId as the immutable pool identifier.
    ├── it should set _observer as the immutable observer address.
    ├── it should set _panopticPool as the immutable Panoptic pool address.
    ├── it should set _governor as the immutable governor address.
    ├── it should initialize lastRate to FLOOR_RATE (1e18).
    ├── it should initialize transformationFunction to address(0).
    └── it should set the ERC-20 name and symbol appropriately.
```

### 1.2 asset

```
VaultB::asset
└── it should return the immutable _asset1 address.
```

### 1.3 totalAssets (OVERRIDE -- core custom logic)

```
VaultB::totalAssets
├── given no T_B is set (transformationFunction == address(0))
│   └── it should return the raw deposited assets (rate = 1:1, using lastRate which is FLOOR_RATE).
└── given T_B is set (transformationFunction != address(0))
    ├── when T_B.computeRate() call reverts
    │   └── it should return totalAssets computed using the lastRate (fallback, no state change).
    └── when T_B.computeRate() call succeeds
        ├── when T_B returns a rate below the floor (< FLOOR_RATE)
        │   └── it should use FLOOR_RATE (1e18) and NOT update lastRate.
        ├── when T_B returns a rate below the lastRate (regression)
        │   └── it should use the lastRate (monotonicity guard) and NOT update lastRate.
        ├── when T_B returns a rate exceeding lastRate + MAX_RATE_INCREASE_PER_CALL
        │   └── it should use lastRate + MAX_RATE_INCREASE_PER_CALL (continuity cap) and update lastRate to the capped value.
        └── when T_B returns a rate within bounds [max(FLOOR_RATE, lastRate), lastRate + MAX_RATE_INCREASE_PER_CALL]
            ├── it should update lastRate to the new rate.
            └── it should return (actualBalance * rate) / 1e18.
```

**Critical implementation note on totalAssets semantics:** The return value represents the
total *claimable* value in asset1 terms, not the literal ERC-20 balance held by the vault.
When rate > 1e18, totalAssets() > balanceOf(asset1, address(this)). This is intentional --
it drives share price appreciation. However, it creates a solvency gap that must be handled
by `maxWithdraw` and `maxRedeem` overrides (see Section 1.5).

**View vs. state mutation:** ERC-4626 specifies that `totalAssets()` MUST NOT revert. The
function is declared `view` in Solady's interface. However, VaultB needs to update
`lastRate` on successful bounded rate changes. This creates a tension:

- Option A: `totalAssets()` is `view`, `lastRate` updates happen lazily in `_beforeWithdraw`
  and `_afterDeposit` hooks.
- Option B: `totalAssets()` is NOT `view` (breaks strict ERC-4626 but Solady allows it),
  and updates `lastRate` on every call.
- Option C (recommended): Internal `_computeBoundedRate()` is used by both `totalAssets()`
  (view, reads lastRate but does not write) and `_refreshRate()` (non-view, called in hooks,
  writes lastRate).

The BTT tree above describes the logical behavior. The implementation must choose one of
these options. **Option C is recommended** as it preserves strict ERC-4626 `view` compliance
while still ensuring monotonicity via hook-based updates.

Under Option C, the refined behavior is:

```
VaultB::_computeBoundedRate (internal, view)
├── given no T_B is set
│   └── it should return lastRate.
└── given T_B is set
    ├── when T_B.computeRate() reverts
    │   └── it should return lastRate.
    └── when T_B.computeRate() succeeds
        ├── when returned rate < FLOOR_RATE
        │   └── it should return max(FLOOR_RATE, lastRate).
        ├── when returned rate < lastRate
        │   └── it should return lastRate.
        ├── when returned rate > lastRate + MAX_RATE_INCREASE_PER_CALL
        │   └── it should return lastRate + MAX_RATE_INCREASE_PER_CALL.
        └── when returned rate is within bounds
            └── it should return the rate as-is.
```

```
VaultB::_refreshRate (internal, non-view, called from hooks)
├── it should call _computeBoundedRate().
└── when the computed rate > lastRate
    └── it should update lastRate to the computed rate.
```

```
VaultB::totalAssets (view, OVERRIDE)
├── it should call _computeBoundedRate() to get the current rate.
└── it should return (actualAssetBalance * rate) / 1e18.
```

### 1.4 setTransformationFunction

```
VaultB::setTransformationFunction
├── when caller is not governor
│   └── it should revert with Unauthorized().
└── when caller is governor
    ├── when newTB is address(0)
    │   └── it should revert with ZeroAddress().
    └── when newTB is non-zero
        ├── it should store the new T_B address in transformationFunction.
        ├── it should emit TransformationFunctionUpdated(oldTB, newTB).
        ├── it should NOT call _refreshRate().
        └── it should NOT affect the current lastRate.
```

### 1.5 maxWithdraw (OVERRIDE -- solvency bound)

**Why the override is needed:** Solady's default `maxWithdraw(owner)` returns
`convertToAssets(balanceOf(owner))` (line 348 of Solady ERC4626.sol). This uses
`totalAssets()` in the conversion, which may exceed the vault's actual asset1 balance
when rate > 1e18. A user could attempt to withdraw more asset1 than the vault holds,
causing a transfer revert.

```
VaultB::maxWithdraw
├── given the vault's actual asset1 balance >= convertToAssets(balanceOf(owner))
│   └── it should return convertToAssets(balanceOf(owner)) (same as Solady default).
└── given the vault's actual asset1 balance < convertToAssets(balanceOf(owner))
    └── it should return the vault's actual asset1 balance (solvency-limited).
```

Formal definition:
`maxWithdraw(owner) = min(convertToAssets(balanceOf(owner)), IERC20(asset()).balanceOf(address(this)))`

### 1.6 maxRedeem (OVERRIDE -- solvency bound)

Same solvency concern applies. `maxRedeem` must ensure the shares being redeemed do not
claim more assets than the vault holds.

```
VaultB::maxRedeem
├── given the vault's actual asset1 balance >= convertToAssets(balanceOf(owner))
│   └── it should return balanceOf(owner) (same as Solady default).
└── given the vault's actual asset1 balance < convertToAssets(balanceOf(owner))
    └── it should return convertToShares(actualAssetBalance) (solvency-limited shares).
```

Formal definition:
`maxRedeem(owner) = min(balanceOf(owner), convertToShares(IERC20(asset()).balanceOf(address(this))))`

### 1.7 getRate (IRateProvider)

```
VaultB::getRate
├── given totalSupply is zero (no deposits, but virtual shares exist)
│   └── it should return convertToAssets(1e18).
│       (With virtual shares: (1e18 * (totalAssets() + 1)) / (0 + 1) ~= totalAssets() + 1,
│        but totalAssets() is 0 when balance is 0, so ~= 1e18.)
└── given totalSupply is non-zero
    └── it should return convertToAssets(1e18).
```

Note: `getRate()` always delegates to `convertToAssets(1e18)`. The virtual shares mechanism
ensures this is well-defined even when totalSupply is zero.

### 1.8 currentRate (view helper)

```
VaultB::currentRate
└── it should return _computeBoundedRate().
```

This is a convenience accessor for off-chain consumers and integrating contracts that want
the current bounded rate without going through the ERC-4626 conversion math.

### 1.9 _afterDeposit hook (internal)

```
VaultB::_afterDeposit
└── it should call _refreshRate() to update lastRate if a higher bounded rate is available.
```

### 1.10 _beforeWithdraw hook (internal)

```
VaultB::_beforeWithdraw
└── it should call _refreshRate() to update lastRate if a higher bounded rate is available.
```

---

## Section 2: Algebraic Properties

These properties must hold for all reachable states and are candidates for fuzz/invariant
testing.

### P1: Rate-getRate Consistency

```
For all states:
  getRate() == convertToAssets(1e18)
```

This is structurally guaranteed by the implementation (getRate delegates to convertToAssets)
but should be fuzz-tested to catch any future divergence.

### P2: Monotonicity (Non-Decreasing Rate)

```
For any two transactions at t1 < t2:
  currentRate() at t2 >= currentRate() at t1
```

The `lastRate` storage variable is only updated to higher values. `_computeBoundedRate()`
never returns below `lastRate`. This property must hold regardless of T_B behavior,
including:
- T_B returning decreasing values
- T_B reverting
- T_B being swapped to a different contract
- T_B returning values below FLOOR_RATE

### P3: Floor (No Principal Loss)

```
For all states:
  currentRate() >= FLOOR_RATE (1e18)
```

Since `lastRate` is initialized to `FLOOR_RATE` and monotonicity holds (P2), the floor is
guaranteed. However, it should be independently tested as a belt-and-suspenders measure.

### P4: Deposit-Withdraw Round Trip (Rounding Favors Vault)

```
For any deposit amount d > 0:
  let shares = deposit(d, user)
  let assets = redeem(shares, user, user)
  assert assets <= d
```

This is the standard ERC-4626 rounding invariant. Solady handles it via `fullMulDiv`
(rounds down for shares-to-assets) and `fullMulDivUp` (rounds up for assets-to-shares in
previewWithdraw/previewMint). VaultB inherits this without modification.

### P5: T_B Independence at Swap Time

```
For any setTransformationFunction(newTB) call:
  let rateBefore = currentRate()    // read before the call
  setTransformationFunction(newTB)
  let rateAfter = currentRate()     // read after the call
  // rateAfter may differ from rateBefore (new T_B returns different rate)
  // BUT: lastRate is unchanged by setTransformationFunction itself
```

The `setTransformationFunction` call does NOT call `_refreshRate()`. The new T_B is only
consulted on the next `totalAssets()` read. The rate *may* change on the next read (if the
new T_B returns a different value), but `setTransformationFunction` itself does not mutate
`lastRate`.

### P6: Governor Isolation

```
For all functions f in VaultB:
  if f != setTransformationFunction:
    f does not check msg.sender == governor
    f does not modify transformationFunction
```

Only the governor can change T_B. No other state mutation is governor-controlled.

### P7: Solvency (maxWithdraw Bound)

```
For all states and all owners:
  maxWithdraw(owner) <= IERC20(asset()).balanceOf(address(this))
```

The vault never promises more withdrawable assets than it actually holds.

### P8: Continuity Cap

```
For any single _refreshRate() call:
  let newLastRate = lastRate after the call
  let oldLastRate = lastRate before the call
  assert newLastRate - oldLastRate <= MAX_RATE_INCREASE_PER_CALL
```

Rate cannot jump more than `MAX_RATE_INCREASE_PER_CALL` in a single update.

### P9: Fallback Stability

```
When T_B.computeRate() reverts:
  totalAssets() does not revert (ERC-4626 compliance: MUST NOT revert)
  currentRate() == lastRate (unchanged)
```

A reverting T_B must never cause totalAssets() to revert. The vault gracefully falls back
to `lastRate`.

---

## Section 3: Withdrawal Solvency Analysis

### The Problem

When rate > 1e18, `totalAssets()` reports a value larger than the actual asset1 balance in
the vault. For example:

- User deposits 100 asset1
- Rate appreciates to 1.5e18
- `totalAssets()` reports 150 asset1
- But the vault only holds 100 asset1

If a user tries to `withdraw(150, ...)`, the ERC-20 transfer of 150 asset1 would revert
because the vault only has 100.

### The Solution

Override `maxWithdraw` and `maxRedeem` to cap at the actual balance. This means:

1. Users can always withdraw up to the vault's actual balance (no revert on transfer).
2. If the vault is underfunded (totalAssets > actual balance), withdrawals are first-come-first-served.
3. The deficit represents "unrealized yield" -- the vault's totalAssets exceeds its holdings.

### Trust Assumption

The deficit is expected to be zero or very small in practice. The rate transformation T_B
is designed to reflect yield that accrues *within the Angstrom system* -- fee revenue that
the vault is entitled to claim. A future mechanism (fee sweep, keeper, or direct fee routing)
is expected to fund the vault with actual asset1 to cover the yield. This mechanism is
OUT OF SCOPE for VaultB's Phase 1 specification.

### Solvency Invariant for Fuzz Tests

```
For all states:
  sum(maxWithdraw(owner_i) for all owners) <= IERC20(asset()).balanceOf(address(this))
```

This is a stronger invariant than P7. It ensures the vault cannot promise more in aggregate
than it holds. Note that this may NOT hold in general because `maxWithdraw` is min-capped
per-owner, and the sum of per-owner mins does not necessarily equal the global min. The
implementer should evaluate whether a global solvency check is needed (e.g., a circuit
breaker) or whether per-owner capping is sufficient.

---

## Section 4: View vs. State Mutation Design (Option C Detail)

### The Tension

ERC-4626 declares `totalAssets()` as `view`. VaultB needs to persist `lastRate` updates
for monotonicity enforcement. These are incompatible.

### Resolution: Option C (Recommended)

Split the logic into three internal functions:

| Function | Visibility | Writes State | Called By |
|---|---|---|---|
| `_computeBoundedRate()` | `internal view` | No | `totalAssets()`, `currentRate()`, `_refreshRate()` |
| `_refreshRate()` | `internal` | Yes (lastRate) | `_afterDeposit()`, `_beforeWithdraw()` |
| `totalAssets()` | `public view override` | No | Solady's `convertToShares`, `convertToAssets`, `preview*` |

This means `lastRate` is only updated during deposit/withdraw/mint/redeem operations (via
hooks). Pure view calls (`convertToAssets`, `getRate`, off-chain reads) use the stale
`lastRate` from the most recent deposit/withdraw. This is acceptable because:

1. The rate is monotonically non-decreasing, so stale `lastRate` is a conservative lower bound.
2. Deposits and withdrawals (the operations that matter for real value transfer) always refresh.
3. Off-chain consumers get a slightly stale but safe rate.

### Edge Case: Long Periods Without Deposits/Withdrawals

If no deposit/withdraw occurs for an extended period, `lastRate` may significantly lag the
true rate from T_B. The first deposit/withdraw after a long gap would see a rate jump
(capped by `MAX_RATE_INCREASE_PER_CALL`). If the true rate has increased by more than
`MAX_RATE_INCREASE_PER_CALL`, multiple transactions may be needed to "catch up." This is
a known and acceptable trade-off: the continuity cap protects against manipulation at the
cost of delayed rate convergence.

A keeper or pokeRate() function could be added in the future to periodically refresh the
rate without requiring user transactions. This is OUT OF SCOPE for Phase 1.

---

## Section 5: Integration Surface

### As ERC-4626 Vault

Standard ERC-4626 integrations (Yearn, Balancer, aggregators) can interact with VaultB
using the standard interface. The only non-standard behavior is the solvency-capped
`maxWithdraw`/`maxRedeem`, which compliant integrators should already handle (the spec
allows capped values).

### As IRateProvider (Balancer)

Balancer MetaStablePool and ComposableStablePool consume `IRateProvider.getRate()` to
adjust internal balances for rate-bearing tokens. VaultB exposes this directly.

**Invariant:** `getRate() == convertToAssets(1e18)` to within rounding.

### As Panoptic token1

V_B_shares are deposited into ct1 (CollateralTracker). ct1 treats V_B_shares as a standard
ERC-20 token and does not directly query VaultB's rate. The rate-bearing nature of V_B_shares
is reflected in ct1's CollateralTracker pricing via the Panoptic pool's TWAP oracle, not
by querying VaultB.

### User Flow

```
User                    VaultB                    ct1 (CollateralTracker)
  |                       |                           |
  |-- deposit(asset1) --> |                           |
  |<-- V_B_shares ------- |                           |
  |                       |                           |
  |-- approve(V_B_shares, ct1) ---------------------->|
  |-- deposit(V_B_shares) --------------------------->|
  |<-- ct1_shares ----------------------------------- |
```

---

## Section 6: Dependencies and External Calls

| Dependency | Call Site | Failure Mode | VaultB Response |
|---|---|---|---|
| Solady ERC-4626 | All ERC-4626 functions | N/A (inherited, audited) | N/A |
| `ITransformationFunction(T_B).computeRate()` | `_computeBoundedRate()` | Revert | Fallback to `lastRate` |
| `IERC20(asset1).balanceOf(address(this))` | `maxWithdraw()`, `maxRedeem()`, `totalAssets()` | Revert | Entire function reverts (ERC-20 must be well-behaved) |
| `IERC20(asset1).transfer()` / `transferFrom()` | Inherited from Solady `_deposit()` / `_withdraw()` | Revert | Transaction reverts (standard ERC-4626 behavior) |

Note: VaultB does NOT directly call AngstromPoolObserver or PanopticPool. Those calls are
delegated to the T_B contract. VaultB only calls `T_B.computeRate()` and passes the
`_poolId`, `_observer`, and `_panopticPool` immutables as parameters.

---

## Section 7: Test File Structure

```
test/vaults/VaultB.t.sol              -- Phase 2 concrete tests
test/vaults/VaultB.tree               -- BTT tree file (copy of Section 1)
test/vaults/mocks/MockTransformationFunction.sol  -- Controllable T_B mock
test/vaults/mocks/MockERC20.sol       -- Standard mock ERC-20 for asset1
```

### Mock Requirements

**MockTransformationFunction** must support:
- Configurable return value for `computeRate()`
- Configurable revert behavior (revert on next call, revert always, revert never)
- Call counting (to verify T_B is/isn't called in specific scenarios)

**MockERC20** must support:
- Standard mint/burn/transfer
- Configurable decimals (to test non-18-decimal assets)

---

## Section 8: Open Questions for Implementation Phase

### Q1: totalAssets Computation Formula

The BTT tree specifies `(actualBalance * rate) / 1e18`. However, this means a deposit of
100 asset1 at rate 1e18 yields `totalAssets() = 100`. If rate increases to 1.5e18, then
`totalAssets() = 150`, but the vault still holds 100. The delta (50) represents unrealized
yield. Is this the intended semantic, or should totalAssets track cumulative deposits
separately from rate-based appreciation?

**Recommended:** Use `(actualBalance * rate) / 1e18`. The solvency gap is handled by
maxWithdraw/maxRedeem overrides. This is the simplest and most standard approach for
yield-bearing ERC-4626 vaults.

### Q2: MAX_RATE_INCREASE_PER_CALL Value

This constant is TBD. It depends on:
- Expected growth rate from Angstrom fee accumulation
- Block time (how frequently rate updates occur)
- Maximum acceptable manipulation window

Candidates: 1e14 (~0.01% per call), 1e15 (~0.1% per call), 1e16 (~1% per call).

### Q3: ERC-20 Name and Symbol

Suggested: `name() = "VaultB Shares"`, `symbol() = "vbSHARES"`. These may be parameterized
in the constructor or hardcoded. Decision deferred to implementation.

### Q4: Decimal Handling for Non-18-Decimal Assets

If asset1 has decimals != 18, the rate math needs adjustment. The `FLOOR_RATE` of 1e18
assumes 18-decimal rate representation regardless of underlying decimals. The Solady
`_underlyingDecimals()` override handles share/asset conversion correctly, but the rate
constants should be validated for non-18-decimal assets.

### Q5: Reentrancy

Solady ERC-4626 follows the checks-effects-interactions pattern (mint/burn before external
transfers in `_withdraw`, transfer before mint in `_deposit`). VaultB's `_refreshRate()`
makes an external call to T_B in the hooks. If T_B is malicious, it could reenter. Mitigation
options:
- T_B is a view call (staticcall), so reentrancy via T_B is impossible if enforced
- Add a reentrancy guard (Solady provides `ReentrancyGuard`)
- Rely on the governor trust assumption (governor sets T_B, so T_B is trusted)

**Recommended:** Enforce staticcall for T_B invocation. This structurally prevents reentrancy
without runtime gas cost.

---

## Section 9: Summary of Overrides from Solady ERC-4626

| Solady Function | Override? | Reason |
|---|---|---|
| `asset()` | Yes | Return immutable `_asset1` |
| `totalAssets()` | Yes | Core custom logic: rate transformation + safety bounds |
| `maxWithdraw()` | Yes | Solvency bound: cap at actual asset balance |
| `maxRedeem()` | Yes | Solvency bound: cap at shares convertible from actual balance |
| `_useVirtualShares()` | No (default true) | Inflation attack mitigation |
| `_decimalsOffset()` | No (default 0) | No additional offset needed |
| `_underlyingDecimals()` | Maybe | Only if asset1 is non-18-decimal |
| `_afterDeposit()` | Yes | Call `_refreshRate()` |
| `_beforeWithdraw()` | Yes | Call `_refreshRate()` |
| `deposit()` | No | Standard Solady logic |
| `withdraw()` | No | Standard Solady logic |
| `mint()` | No | Standard Solady logic |
| `redeem()` | No | Standard Solady logic |
| `convertToShares()` | No | Derived from totalAssets/totalSupply |
| `convertToAssets()` | No | Derived from totalAssets/totalSupply |
| `previewDeposit()` | No | Delegates to convertToShares |
| `previewMint()` | No | Uses fullMulDivUp |
| `previewWithdraw()` | No | Uses fullMulDivUp |
| `previewRedeem()` | No | Delegates to convertToAssets |
| `maxDeposit()` | No | Returns type(uint256).max |
| `maxMint()` | No | Returns type(uint256).max |

---

## Section 10: Error Taxonomy (Complete)

| Error | Selector | Source | Trigger |
|---|---|---|---|
| `Unauthorized()` | custom | `setTransformationFunction` | `msg.sender != governor` |
| `ZeroAddress()` | custom | `setTransformationFunction` | `newTB == address(0)` |
| `DepositMoreThanMax()` | `0xb3c61a83` | Solady, `deposit()` | `assets > maxDeposit(to)` |
| `MintMoreThanMax()` | `0x6a695959` | Solady, `mint()` | `shares > maxMint(to)` |
| `WithdrawMoreThanMax()` | `0x936941fc` | Solady, `withdraw()` | `assets > maxWithdraw(owner)` |
| `RedeemMoreThanMax()` | `0x4656425a` | Solady, `redeem()` | `shares > maxRedeem(owner)` |

Constructor revert errors (for zero-address parameters) should use the same `ZeroAddress()`
error or a dedicated `InvalidConstructorParameter()` error. Decision deferred to implementation.
