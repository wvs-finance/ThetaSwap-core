# FCI V2 Admin Upgradeability Design

**Date:** 2026-03-17
**Branch:** 008-uniswap-v3-reactive-integration
**Scope:** `src/fee-concentration-index-v2/` contracts only

## Problem

`UniswapV3Callback` and `UniswapV3Reactive` use `immutable` for cross-contract references (`fci`, `callback`) and `owner`. If any referenced contract is redeployed, the reactive contracts must also be redeployed. Both contracts hold ETH (gas reimbursement, SystemContract reserves) with no recovery mechanism — funds are stranded on redeploy.

## Goals

1. Make cross-contract references mutable (onlyOwner setters) so contracts survive upstream redeployments
2. Add fund recovery (`migrateFunds`) for clean transitions
3. Make ownership transferable on both contracts
4. Keep it simple — plain onlyOwner, no timelocks or two-step acceptance

## Non-Goals

- Upgrading the FCI V2 diamond or its facets (already flexible via `registerProtocolFacet`)
- Changing `LibOwner` itself
- Proxy/upgradeable patterns
- Anything in `src/reactive-integration/` (outdated)

---

## Design

### 1. New File: `AdminLib.sol`

**Path:** `src/fee-concentration-index-v2/modules/dependencies/AdminLib.sol`

A file of free functions following the project convention (no `library` keyword, same pattern as `LibOwner.sol`):

```
function migrateFunds(address payable to, uint256 balance)
```

- Caller passes `address(this).balance` (free functions cannot access `this`)
- Reverts with `NoFunds()` if balance is zero
- Transfers all ETH to `to` via low-level call
- Reverts with `TransferFailed()` if transfer fails
- Emits `FundsMigrated(to, amount)` in the calling contract's context

**File-level events:**
- `event FundsMigrated(address indexed to, uint256 amount)`

**File-level errors:**
- `error NoFunds()`
- `error MigrationTransferFailed()` — named to avoid collision with existing `TransferFailed` in consuming contracts

No storage. No ownership logic. Ownership is handled by `LibOwner` in each consuming contract.

---

### 2. UniswapV3Callback Changes

**File:** `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol`

#### Ownership
- Remove `address immutable owner`
- Use `LibOwner` (existing module at `modules/dependencies/LibOwner.sol`)
- Constructor calls `initOwner(msg.sender)`
- All `require(msg.sender == owner)` become `requireOwner()`
- Gains `transferOwnership(address)` from `LibOwner`

#### Mutable FCI Reference
- Remove `IHooks immutable fci`
- Replace with `IHooks fci` in storage
- Constructor sets initial value
- New function:
  ```
  function setFci(address newFci) external
  ```
  - `requireOwner()`
  - Reverts with `ZeroAddress()` if `newFci == address(0)`
  - Casts internally: `fci = IHooks(newFci)`
  - Emits `FciUpdated(oldFci, newFci)`

#### Fund Recovery
- New function:
  ```
  function migrateFunds(address payable to) external
  ```
  - `requireOwner()`
  - Delegates to `AdminLib.migrateFunds(to)`

#### Existing Admin Functions (unchanged)
- `setRvmId(address)` — already mutable, onlyOwner
- `setAuthorized(address, bool)` — already mutable, onlyOwner
- `pay(uint256)` — already guarded by `authorizedCallers`

#### Events Added
- `event FciUpdated(address indexed oldFci, address indexed newFci)`

#### Gas Impact
- `fci` reads in `unlockCallbackReactive` and `_handle*` functions change from code-embedded constant to SLOAD
- Negligible: callback path is not gas-sensitive (called by reactive proxy, gas reimbursed)

---

### 3. UniswapV3Reactive Changes

**File:** `src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol`

#### Ownership
- Remove `address immutable owner`
- Use `LibOwner`
- Constructor calls `initOwner(msg.sender)`
- All `require(msg.sender == owner)` become `requireOwner()`
- Gains `transferOwnership(address)` from `LibOwner`

#### Mutable Callback Reference
- Remove `address immutable callback`
- Replace with `address callback` in storage
- Constructor sets initial value
- New function:
  ```
  function setCallback(address newCallback) external
  ```
  - `requireOwner()`
  - Reverts with `ZeroAddress()` if `newCallback == address(0)`
  - Emits `CallbackUpdated(oldCallback, newCallback)`

#### Stays Immutable
- `ISubscriptionService immutable service` — system contract on Reactive Network, does not change
- `bool immutable vm` — chain detection flag, does not change

#### Fund Recovery
- New function:
  ```
  function migrateFunds(address payable to) external
  ```
  - `requireOwner()`
  - Delegates to `AdminLib.migrateFunds(to)`

#### Existing Admin Functions (unchanged)
- `registerPool(uint256, address)` — already onlyOwner + RN-only
- `unregisterPool(uint256, address)` — already onlyOwner + RN-only
- `fund()` — permissionless deposit to SystemContract

#### Events Added
- `event CallbackUpdated(address indexed oldCallback, address indexed newCallback)`

#### Gas Impact
- `callback` reads in `react()` change from code-embedded to SLOAD
- Negligible: reactive VM execution, gas is not user-facing

---

### 4. Summary of Changes

| Contract | Remove | Add | Unchanged |
|----------|--------|-----|-----------|
| **AdminLib** (new) | — | `migrateFunds`, `FundsMigrated`, `NoFunds`, `TransferFailed` | — |
| **UniswapV3Callback** | `immutable owner`, `immutable fci` | `LibOwner`, storage `fci`, `setFci`, `migrateFunds`, `FciUpdated` | `setRvmId`, `setAuthorized`, `pay`, `authorizedCallers`, `rvmId` |
| **UniswapV3Reactive** | `immutable owner`, `immutable callback` | `LibOwner`, storage `callback`, `setCallback`, `migrateFunds`, `CallbackUpdated` | `immutable service`, `immutable vm`, `registerPool`, `unregisterPool`, `fund` |

### 5. Shared Error

Both contracts add:
- `error ZeroAddress()` — used by `setFci` and `setCallback`

### 6. Error Signature Change

Both contracts currently define `error OnlyOwner()`. After switching to `LibOwner`, the revert changes to `OwnerUnauthorizedAccount()` (no parameters). Off-chain tooling matching on the old error selector must be updated.

### 7. Deployment Script Impact

Constructor external signatures are unchanged — neither contract currently accepts `owner` as a parameter (both already use `msg.sender`). Internal implementation changes from `owner = msg.sender` to `initOwner(msg.sender)`. `FeeConcentrationIndexBuilder.s.sol` needs no constructor arg changes.

### 8. Migration Path (Existing Deployments)

Existing deployed contracts cannot be upgraded. The new pattern applies to fresh deployments only. For existing deployments:
1. Deploy new `UniswapV3Callback` pointing to the existing FCI V2 diamond address
2. Deploy new `UniswapV3Reactive` pointing to the new callback
3. On the new Callback: call `setAuthorized` for the callback proxy address
4. On the new Reactive (RN instance): call `registerPool` for each tracked pool
5. (Optional) On the old Reactive: call `unregisterPool` to stop old subscriptions
6. The FCI V2 diamond itself needs no reconfiguration — the callback references the diamond, not the other way around
7. ETH in old contracts is unrecoverable (no `migrateFunds` on current versions)
