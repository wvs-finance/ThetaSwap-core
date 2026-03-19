# FCI Token Vault — Client Integration Testing Design

**Date:** 2026-03-17
**Branch:** 008-uniswap-v3-reactive-integration
**Status:** Approved design, pending implementation
**Spec review:** Passed (rev 2 — addressed C1, C2, I1–I4, S1–S5)

## Problem

The FCI token vault has strong coverage of payoff math (unit + fuzz + formal) and economic welfare properties (JitGame integration tests), but the actual contract surface that clients call is untested. Specifically:

- `CollateralCustodianFacet`, `OraclePayoffFacet`, and `ERC20WrapperFacade` are never tested directly — all tests go through harness contracts that bypass reentrancy guards, event emission, and CEI ordering.
- View functions (`previewLongPayout`, `previewShortPayout`, `payoffRatio`, `isSettled`, `totalDeposited`) are never exercised.
- No multi-user flows are tested.
- INV-014 (single-sided solvency) is deferred.
- ERC-20 wrapper composition (wrap → transfer → unwrap → redeem) is never tested.

The FCI protocol integration layer is actively evolving (V3 reactive on branch 008, future protocols). The testing strategy must accommodate backend changes without rewriting test logic.

## Design Decisions

1. **Real FCI V1** as the test backend — no mocks. FCI V1 is stable, its oracle interface (`IFeeConcentrationIndex`) is identical to V2, and the vault doesn't care which version produced the `uint128` Δ⁺.
2. **Actual facet contracts** — tests call the real `CollateralCustodianFacet`, `OraclePayoffFacet`, `ERC20WrapperFacade`. Not harnesses.
3. **Facets deployed standalone** — all three facets composed into a single contract via inheritance so they share diamond storage. Not behind a diamond proxy.
4. **Layered architecture** — three layers with increasing integration depth.
5. **FCIFixture as the swap point** — encapsulates FCI + V4 setup. When V2 + NativeV4Facet or V3 reactive is ready, write a new fixture. Test logic doesn't change.
6. **Additive** — existing tests (`unit/`, `fuzz/`, `kontrol/`, `integration/`) are untouched.
7. **Production code change required** — `CollateralCustodianFacet.deposit()` must add a `settled` guard. The current production code does NOT check `os.settled` before deposit. The harness (`FciTokenVaultHarness:43`) has this check, but the facet does not. This is a bug — deposits post-settlement would mint tokens backed by USDC that can never be redeemed via oracle path. Implementation must add `if (getOraclePayoffStorage().settled) revert VaultAlreadySettled();` to the facet's `deposit()`.
8. **`redeemPair` intentionally allowed post-settlement** — `redeemPair` bypasses the oracle entirely (returns exact USDC for LONG+SHORT pair). This is by design: a user holding both tokens can always exit risk-free regardless of vault state. Tests document this as intended behavior.

## Architecture

### Layer 1 — Facet Unit Tests

Test each facet in isolation. No FCI, no V4. Diamond storage pre-seeded via init helpers.

For `poke()` testing, a `DeltaPlusStub` contract implements `getDeltaPlusEpoch(PoolKey, bool) → uint128` with a configurable return value. Layer 1 wires it by: (1) deploying `DeltaPlusStub`, (2) writing a `ProtocolAdapterStorage` at the adapter slot with `fciEntryPoint = IHooks(address(stub))`, a dummy `poolKey`, and `reactive = false`. The `init()` function on `FacetDeployer` handles this wiring.

#### CollateralCustodianFacet.t.sol

| Test | Asserts |
|------|---------|
| `test_deposit_mints_pair_and_transfers_usdc` | LONG+SHORT balances, USDC transferred in, `PairedMint` event, `totalDeposited()` increased |
| `test_redeemPair_burns_and_transfers_usdc` | Both balances zero, USDC transferred out, `PairedBurn` event, `totalDeposited()` decreased |
| `test_previewDeposit_returns_equal_amounts` | Returns (amount, amount) |
| `test_balanceOf_reads_erc6909` | Correct per-user per-id balance |
| `test_deposit_zero_reverts` | `ZeroAmount` |
| `test_redeemPair_zero_reverts` | `ZeroAmount` |
| `test_deposit_exceeds_cap_reverts` | `DepositCapExceeded` |
| `test_deposit_reentrancy_reverts` | `ReentrancyGuardReentrant` |
| `test_redeemPair_reentrancy_reverts` | `ReentrancyGuardReentrant` |
| `test_redeemPair_after_settle_succeeds` | `redeemPair` is intentionally allowed post-settlement — risk-free exit regardless of vault state |

#### OraclePayoffFacet.t.sol

| Test | Asserts |
|------|---------|
| `test_poke_emits_hwm_updated` | `HWMUpdated` event with correct values (via DeltaPlusStub) |
| `test_poke_updates_hwm_monotonically` | HWM only increases across multiple pokes |
| `test_poke_zero_delta_plus_hwm_unchanged` | DeltaPlusStub returns 0 → HWM unchanged, no sqrtPrice computed |
| `test_settle_emits_settlement` | `OracleSettlement` event, `isSettled()` true |
| `test_payoffRatio_sums_to_Q96` | `longPerToken + shortPerToken == Q96` (arithmetic identity, documents the construction) |
| `test_redeemLong_burns_and_pays` | LONG balance zero, SHORT unchanged, USDC payout correct, `RedeemLong` event |
| `test_redeemShort_burns_and_pays` | SHORT balance zero, LONG unchanged, USDC payout correct, `RedeemShort` event |
| `test_previewLongPayout_matches_actual` | `previewLongPayout(amount) == actual USDC from redeemLong(amount)` |
| `test_previewShortPayout_matches_actual` | `previewShortPayout(amount) == actual USDC from redeemShort(amount)` |
| `test_settle_before_expiry_reverts` | `VaultNotExpired` |
| `test_redeemLong_before_settle_reverts` | `VaultNotSettled` |
| `test_redeemShort_before_settle_reverts` | `VaultNotSettled` |
| `test_poke_after_settle_reverts` | `VaultAlreadySettledPoke` |
| `test_previewLongPayout_before_settle_reverts` | `VaultNotSettled` |
| `test_previewShortPayout_before_settle_reverts` | `VaultNotSettled` |
| `test_payoffRatio_before_settle_reverts` | `VaultNotSettled` |
| `test_redeemLong_zero_reverts` | `ZeroAmount` |
| `test_redeemShort_zero_reverts` | `ZeroAmount` |

#### ERC20WrapperFacade.t.sol

| Test | Asserts |
|------|---------|
| `test_wrap_converts_6909_to_erc20` | ERC-6909 decreased, ERC-20 increased |
| `test_unwrap_converts_erc20_to_6909` | ERC-20 decreased, ERC-6909 increased |
| `test_wrap_insufficient_balance_reverts` | `InsufficientERC6909Balance` |
| `test_unwrap_insufficient_erc20_reverts` | ERC-20 burn reverts on insufficient balance |

### Layer 2 — Oracle Integration Tests

Facets + real FCI V1 + full V4 pool infrastructure. Tests the poke→HWM→settle→payoff pipeline through actual facet calls with genuine pool activity generating Δ⁺.

#### SingleUserLifecycle.integration.t.sol

Full lifecycle through facet external API:

1. Alice deposits USDC via `custodianFacet.deposit(amount)`
2. LP provides liquidity, JIT enters, swap occurs, JIT exits, LP exits — real Δ⁺ generated
3. `payoffFacet.poke()` — verify `HWMUpdated` event with real sqrtPrice
4. Repeat across 3 epochs
5. `vm.warp` past expiry → `payoffFacet.settle()`
6. Verify `payoffFacet.isSettled()`, `payoffFacet.payoffRatio()`, `payoffFacet.previewLongPayout(amount)`
7. `payoffFacet.redeemLong(amount)` → verify USDC payout matches preview
8. Verify `custodianFacet.totalDeposited()` decreased correctly
9. Conservation: longPayout + shortPayout == deposit

#### MultiUserLifecycle.integration.t.sol

Multi-user flows:

1. Alice deposits 100e6, Bob deposits 200e6 — verify `totalDeposited() == 300e6`
2. Same JIT game → pokes across epochs → settle
3. Alice redeems LONG first → payout scales with her deposit
4. Bob redeems SHORT → payout is correct
5. Conservation per-user: Alice's longPayout + shortPayout == 100e6 (if she held both)
6. Cross-user solvency: `totalDeposited()` after all redemptions == 0
7. Partial redemption ordering: Alice redeems 50e6 LONG, then 50e6 more — same total as redeeming 100e6 at once
8. Independent redemption: Alice redeems only LONG, Bob redeems only SHORT — vault stays solvent

### Layer 3 — Adversarial & Composition Tests

#### VaultLifecycleGuards.t.sol

Lifecycle guards that require real FCI infrastructure or cross-facet composition. Simple revert tests (settle before expiry, redeem before settle, etc.) are covered in Layer 1. Layer 3 tests only scenarios that need the full stack or are not covered by Layer 1.

| Test | Asserts |
|------|---------|
| `test_deposit_after_settle_reverts` | Deposit blocked post-settlement (requires production code fix — see Design Decision 7) |
| `test_settle_twice_reverts` | `VaultAlreadySettled` — settle with real FCI-driven HWM, then attempt second settle |
| `test_full_lifecycle_state_transitions` | Complete state machine traversal through facet calls: deposit → poke → settle → redeemLong → redeemShort, verifying `isSettled()` transitions at each step |

#### EdgeCasePayoffs.t.sol

Payoff boundary conditions with real FCI:

| Test | Asserts |
|------|---------|
| `test_zero_hwm_settlement` | No pokes called → settle → `longPayoutPerToken == 0`, SHORT gets everything |
| `test_hwm_at_strike` | Poke produces sqrtPrice == strike → payoff == 0 |
| `test_maximum_delta_plus` | Extreme JIT → payoff caps at Q96, LONG gets all USDC |
| `test_poke_with_zero_delta_plus` | No pool activity in epoch → HWM unchanged |
| `test_single_sided_solvency` | Alice holds only LONG, Bob holds only SHORT (simulated off-chain transfer). Both redeem successfully. `totalDeposited()` ends at 0. (INV-014) |

#### WrapRedeemComposition.t.sol

ERC-20 wrapper + vault interaction:

| Test | Asserts |
|------|---------|
| `test_deposit_wrap_transfer_unwrap_redeem` | Full flow: deposit → wrap LONG → transfer to Bob → Bob unwraps → Bob redeems LONG after settlement |
| `test_wrap_unwrap_roundtrip` | Balances identical after wrap + unwrap |
| `test_redeem_with_wrapped_tokens_fails` | ERC-6909 balance is zero after wrap, direct redeem reverts |

## Test Infrastructure

### File Layout

```
test/fci-token-vault/
├── facet/                              # Layer 1
│   ├── CollateralCustodianFacet.t.sol
│   ├── OraclePayoffFacet.t.sol
│   └── ERC20WrapperFacade.t.sol
├── integration/                        # Layer 2 (new + existing)
│   ├── SingleUserLifecycle.integration.t.sol
│   ├── MultiUserLifecycle.integration.t.sol
│   ├── HedgedVsUnhedged.integration.t.sol
│   ├── JitGameWelfareComparison.integration.t.sol
│   └── PayoffPipeline.integration.t.sol
├── adversarial/                        # Layer 3
│   ├── VaultLifecycleGuards.t.sol
│   ├── EdgeCasePayoffs.t.sol
│   └── WrapRedeemComposition.t.sol
├── fixtures/                           # Shared infrastructure
│   ├── FCIFixture.sol
│   ├── FacetDeployer.sol
│   └── DeltaPlusStub.sol
├── helpers/                            # existing (untouched)
├── fuzz/                               # existing (untouched)
├── kontrol/                            # existing (untouched)
└── unit/                               # existing (untouched)
```

### FacetDeployer.sol

A contract that inherits all three facets so they share one address and one diamond storage context:

```solidity
contract FacetDeployer is CollateralCustodianFacet, OraclePayoffFacet, ERC20WrapperFacade {
    function init(
        address collateralToken,
        uint128 depositCap,
        uint160 sqrtPriceStrike,
        uint256 expiry,
        bytes32 adapterSlot,
        address fciEntryPoint,    // DeltaPlusStub for L1, real FCI for L2/L3
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
}
```

Layer 1 tests deploy `FacetDeployer` and call `init()` with a `DeltaPlusStub` address as `fciEntryPoint`. Layer 2/3 tests deploy `FacetDeployer` and call `init()` with the real FCI hook address, wired via `FCIFixture`. Layer 1 does NOT import `FCIFixture`.

### FCIFixture.sol

Encapsulates FCI V1 + V4 setup. Extends `PosmTestSetup`:

```solidity
contract FCIFixture is PosmTestSetup, FCITestHelper {
    FacetDeployer vault;
    FeeConcentrationIndexHarness fci;
    PoolKey poolKey;

    function deployFCI() internal { ... }
    function initEpoch(uint256 epochLength) internal { ... }
    function runSwap(uint256 swapperPk, int256 amount, bool zeroForOne) internal { ... }
    function mintLP(uint256 lpPk, uint256 liquidity) internal returns (uint256 tokenId) { ... }
    function burnLP(uint256 lpPk, uint256 tokenId, uint256 liquidity) internal { ... }
    function rollToNextEpoch() internal { ... }
}
```

This is the **swap point** for protocol changes. New fixture, same helpers, no test logic changes.

### DeltaPlusStub.sol

Minimal contract for Layer 1 `poke()` testing:

```solidity
contract DeltaPlusStub {
    uint128 public deltaPlusValue;
    function setDeltaPlus(uint128 v) external { deltaPlusValue = v; }
    function getDeltaPlusEpoch(PoolKey calldata, bool) external view returns (uint128) {
        return deltaPlusValue;
    }
}
```

## Coverage Map

| Gap | Layer | Test |
|-----|-------|------|
| Facets never tested directly | L1 | All facet tests |
| Events never asserted | L1 | Every mutation test asserts events |
| View functions never exercised | L1 + L2 | preview*, payoffRatio, isSettled, totalDeposited, balanceOf |
| Reentrancy guard in context | L1 | deposit + redeemPair reentrancy tests |
| Multi-user flows | L2 | MultiUserLifecycle |
| Preview matches actual payout | L1 + L2 | previewLongPayout == actual USDC |
| INV-014 single-sided solvency | L3 | EdgeCasePayoffs.test_single_sided_solvency |
| ERC-20 wrapper in user flow | L3 | WrapRedeemComposition |
| Zero-HWM settlement | L3 | EdgeCasePayoffs.test_zero_hwm_settlement |
| Post-settlement deposit blocked | L3 | VaultLifecycleGuards (requires production code fix) |

## Out of Scope

- Diamond proxy routing (facets tested standalone, not behind proxy)
- Gas benchmarking
- FCI V2 + NativeV4Facet integration (future fixture)
- V3 reactive integration (future fixture)
- Layer 4 invariant fuzzing (future: handler-based fuzz on FacetDeployer)
- New vault view functions (vault metadata, live payoff preview — separate design)

## Invariant Reference

From `specs/004-fci-token-vault/invariants.md`:

| INV | Tested By |
|-----|-----------|
| 001–009 | Existing: SqrtPriceLookbackPayoffX96.t.sol, .fuzz.t.sol, .k.sol |
| 010 | Existing: PayoffPipeline.integration.t.sol |
| 011 | Existing: HedgedVsUnhedged, JitGameWelfareComparison |
| 012 | L1: deposit tests, L2: multi-user conservation |
| 013 | L2: cross-user solvency (totalDeposited == 0 after all redemptions) |
| 014 | L3: EdgeCasePayoffs.test_single_sided_solvency |
| 015 | L3: VaultLifecycleGuards (deposit after settle blocked — requires production code fix to `CollateralCustodianFacet.deposit()`) |
| 016 | L1 + L3: settle before expiry reverts |
| 017 | L1 + L3: redeem before settle reverts |
