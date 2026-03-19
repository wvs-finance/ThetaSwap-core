# Testing Patterns

**Analysis Date:** 2026-03-18

## Test Framework

**Runner:**
- Forge (Foundry) — version pinned via `foundry.toml` (`solc_version = "0.8.26"`, `evm_version = "cancun"`)
- Config: `foundry.toml`

**Assertion Library:**
- forge-std `Test` — `assertEq`, `assertGt`, `assertLe`, `assertTrue`, `assertFalse`, `assertGe`
- `vm.expectRevert(ErrorSelector.selector)` and `vm.expectEmit(...)` for negative and event tests

**Run Commands:**
```bash
# Run all tests
forge test

# Run specific module
forge test --match-path "test/fee-concentration-index-v2/**" -vv
forge test --match-path "test/fci-token-vault/**" -vv

# CI profile (no FFI, no fork)
forge test --profile ci

# Fuzz-heavy profile
forge test --profile fuzz-heavy

# Skip tests and scripts (build only)
forge build --profile lite
```

**Fuzz configuration (foundry.toml):**
- Default: `runs = 256`, `max_test_rejects = 65536`
- Fuzz-heavy: `runs = 64`, `max_test_rejects = 131072`
- Invariant: `runs = 64`, `depth = 32`, `fail_on_revert = false`

## Test File Organization

**Location:**
Tests are co-organized under `test/` with a directory structure mirroring feature modules, not co-located with source.

**Naming:**
- Unit tests: `ContractName.t.sol` or `ContractName.unit.t.sol` (e.g., `CollateralCustodianMod.t.sol`)
- Integration tests: `FeatureName.integration.t.sol` (e.g., `HedgedVsUnhedged.integration.t.sol`)
- Fuzz tests: `FeatureName.fuzz.t.sol` (e.g., `SqrtPriceLookbackPayoffX96.fuzz.t.sol`)
- Invariant tests: `FeatureName.fuzz.t.sol` (shares suffix with fuzz, by convention)
- Differential tests: `A_Diff_B.diff.t.sol` (e.g., `FCIV1DiffFCIV2.diff.t.sol`)
- Fork tests: `FeatureName.fork.t.sol`
- Formal/Kontrol proofs: `FeatureName.k.sol`
- Admin path tests: `ContractName.admin.t.sol` (e.g., `UniswapV3Callback.admin.t.sol`)
- Debug/development tests: `ContractName.Debug.t.sol` or `ContractNameDebug.t.sol`

**Structure:**
```
test/
├── fee-concentration-index/
│   ├── harness/            # FeeConcentrationIndexHarness.sol (exposes internals)
│   └── helpers/            # FCITestHelper.sol (shared action wrappers)
├── fee-concentration-index-v2/
│   ├── differential/       # FCIV1DiffFCIV2.diff.t.sol + FCIDifferentialBase.sol
│   ├── protocols/
│   │   ├── uniswap-v3/     # unit, admin, flow, mock, integration tests
│   │   │   ├── mocks/      # MockCallbackReceiver.sol
│   │   │   └── integration/
│   │   └── uniswapV4/      # integration tests
│   └── *.t.sol             # storage-level unit tests
├── fci-token-vault/
│   ├── adversarial/        # EdgeCasePayoffs.t.sol, VaultLifecycleGuards.t.sol, WrapRedeemComposition.t.sol
│   ├── facet/              # per-facet unit tests
│   ├── fixtures/           # FCIFixture.sol (shared fixture base), FacetDeployer.sol, DeltaPlusStub.sol
│   ├── fuzz/               # CustodianHandler.sol + CustodianInvariant.fuzz.t.sol
│   ├── helpers/            # FciTokenVaultHarness.sol, CustodianHarness.sol
│   ├── integration/        # multi-file lifecycle + JIT + payoff scenarios
│   ├── kontrol/            # formal proofs
│   └── unit/               # per-module unit tests
├── simulation/             # JIT game + Capponi fork simulations
└── utils/                  # tests for shared utils (Accounts, Pool, TokenPair)
```

## Test Structure

**Contract pattern:**
Every test file contains exactly one contract inheriting `Test` (or an abstract base). Test contract names follow `FeatureNameTest` or `FeatureNameFuzzTest` convention.

**Suite organization:**
```solidity
contract CollateralCustodianModTest is Test {
    CustodianModCaller caller;    // thin proxy contract for exercising free functions
    address alice = makeAddr("alice");

    function setUp() public {
        caller = new CustodianModCaller();
        caller.initStorage(address(1), 0);
    }

    /// @dev INV-001: deposit mints equal LONG + SHORT
    function test_deposit_mints_equal_pair() public { ... }

    /// @dev INV-005: zero amount reverts
    function test_deposit_zero_reverts() public { ... }
}
```

**Test function naming:**
- Happy path: `test_action_expectedOutcome` (e.g., `test_deposit_mints_equal_pair`)
- Revert path: `test_action_reverts` or `test_action_conditionReverts` (e.g., `test_deposit_zero_reverts`, `test_deposit_exceeds_cap_reverts`)
- Fuzz: `testFuzz_invariantDescription` (e.g., `testFuzz_deltaPlusMonotonic`)
- Invariant: `invariant_invariantDescription` (e.g., `invariant_totalDeposits_matches_ghost`)
- Formal proof: `prove_condition` (e.g., `prove_deltaPlusZero_returns_Q96`)
- Event tests: `test_action_emitsEventName` (e.g., `test_setFci_emitsFciUpdated`)

**Patterns:**
- `setUp()`: always public, deploys contracts, wires storage, labels addresses
- `makeAddr("label")` used universally for test addresses — never `address(1)`, `address(2)` for actors
- `vm.createWallet("label")` used when private keys are needed (script/multi-sig patterns)
- Storage initialization inside caller/harness contracts, not inside setUp directly

## Caller/Harness Pattern for Free Functions

Free functions (no `library`) cannot be tested directly. The project uses thin **caller contracts** that wrap them:

```solidity
contract CustodianModCaller {
    function doDeposit(address depositor, uint256 amount) external {
        custodianDeposit(depositor, amount);   // calls free function
    }
    function initStorage(address collateral, uint128 cap) external {
        CustodianStorage storage cs = getCustodianStorage();
        cs.collateralToken = collateral;
        cs.depositCap = cap;
    }
}
```

For hook contracts, a **harness** extends the production contract to expose internals:
- `test/fee-concentration-index/harness/FeeConcentrationIndexHarness.sol` — extends `FeeConcentrationIndex`
- `test/fci-token-vault/helpers/FciTokenVaultHarness.sol`
- `test/fci-token-vault/helpers/CustodianHarness.sol`

## Fixture Pattern (Shared Integration Setup)

Abstract fixture contracts group shared deployment logic for multi-test suites:

```solidity
abstract contract FCIFixture is PosmTestSetup, FCITestHelper {
    FacetDeployer public vault;
    FeeConcentrationIndexHarness public fciHarness;
    PoolId public poolId;

    function _deployFixture() internal {
        // Deploy V4 infra, FCI hook, pool, vault
    }

    function _runJitRound(...) internal { ... }    // scenario helper
    function _settleVault() internal { ... }        // lifecycle helper
}
```

Usage: concrete tests inherit the fixture and call `_deployFixture()` in `setUp()`.

Key fixtures:
- `test/fci-token-vault/fixtures/FCIFixture.sol` — FCI V1 + V4 pool + vault base
- `test/fci-token-vault/fixtures/FacetDeployer.sol` — vault diamond deployer
- `test/fci-token-vault/fixtures/DeltaPlusStub.sol` — stub FCI for controlled deltaPlus injection
- `test/fee-concentration-index-v2/differential/FCIDifferentialBase.sol` — V1 vs V2 parallel deployment

## Mocking

**Foundry cheatcodes:**
- `vm.etch(addr, bytecode)` — inject dummy code at address (e.g., mock reactive SystemContract)
- `vm.mockCall(addr, calldata, returndata)` — stub specific calls
- `vm.store(addr, slot, value)` — write raw storage slots (e.g., set ReactVM flag)
- `vm.prank(addr)` / `vm.startPrank(addr)` — impersonate callers
- `vm.expectRevert(selector)` — assert revert with specific error selector
- `vm.expectEmit(indexed, indexed, indexed, data)` — assert event emission

**Mock contracts:**
Minimal contracts used as stubs when a dependency needs code but no logic:

```solidity
contract MockSubscriptionService {
    fallback() external payable {}
    receive() external payable {}
}

contract RejectETH {}   // no receive — ETH transfers revert

contract DeltaPlusStub  // returns controlled deltaPlus value
```

Located in `test/fee-concentration-index-v2/protocols/uniswap-v3/mocks/` and `test/fci-token-vault/fixtures/`.

**What to mock:**
- Reactive Network SystemContract (always, in any test touching reactive contracts)
- ETH-rejector contracts (for negative fund-transfer tests)
- FCI stub when testing vault payoff logic in isolation

**What NOT to mock:**
- Uniswap V4 PoolManager — always deployed fresh via `PosmTestSetup.deployFreshManagerAndRouters()`
- ERC20 tokens — use `MockERC20` (Solmate) for full compliance
- FCI hook itself in integration/adversarial tests — use the harness with real logic

## Invariant Fuzzing

Handler-based invariant testing pattern:

```solidity
// 1. Handler — contains ghost variables and bounds inputs
contract CustodianHandler is Test {
    uint256 public ghost_totalMinted;
    uint256 public ghost_totalRedeemed;
    address[] public actors;

    function deposit(uint256 actorSeed, uint256 amount) external {
        address actor = actors[actorSeed % actors.length];
        amount = bound(amount, 1, 1_000_000e6);
        custodianDeposit(actor, amount);
        ghost_totalMinted += amount;
    }
}

// 2. Invariant test — declares targetContract
contract CustodianInvariantTest is Test {
    CustodianHandler handler;

    function setUp() public {
        handler = new CustodianHandler();
        targetContract(address(handler));
    }

    function invariant_totalDeposits_matches_ghost() public view {
        assertEq(uint256(handler.getTotalDeposits()),
                 handler.ghost_totalMinted() - handler.ghost_totalRedeemed());
    }
}
```

**Ghost variable convention:** `ghost_<state_tracked>` (e.g., `ghost_totalMinted`, `ghost_totalRedeemed`).

**Actor seeding:** Bounded actor set (3 actors) derived via `actorSeed % actors.length`.

**Files:** `test/fci-token-vault/fuzz/CustodianHandler.sol` + `test/fci-token-vault/fuzz/CustodianInvariant.fuzz.t.sol`

## Differential Testing

**V1 vs V2 differential pattern:**

Abstract base deploys both versions with identical pool configs. Helpers dispatch to the correct version via an `FCIContext` struct:

```solidity
struct FCIContext {
    address hook;
    PoolKey key;
    PoolId poolId;
    bool isV2;
}

abstract contract FCIDifferentialBase is PosmTestSetup, FCITestHelper {
    FCIContext ctxV1;
    FCIContext ctxV2;

    function _assertStateEqual() internal view {
        // Compare all metrics across V1 and V2
    }
}
```

Concrete test calls identical scenario on both contexts, then calls `_assertStateEqual()`.

**Files:** `test/fee-concentration-index-v2/differential/FCIDifferentialBase.sol` + `test/fee-concentration-index-v2/differential/FCIV1DiffFCIV2.diff.t.sol`

## Python FFI Differential Testing

Some tests use Python FFI to compute expected values and compare against Solidity:

```toml
[profile.default]
ffi = true
fs_permissions = [{ access = "read", path = "research/data/fixtures" }]

[profile.ci]
ffi = false   # FFI disabled in CI
```

The Python simulator at `research/data/scripts/fci_oracle.py` generates JSON fixture files. The Solidity test reads them with `vm.readFile("research/data/fixtures/simulator/*.json")` and `vm.parseJsonAddress`.

**Files:** `test/fee-concentration-index-v2/protocols/uniswapV4/NativeV4FeeConcentrationIndex.integration.t.sol` reads from `research/data/fixtures/simulator/`.

## Integration Test Structure

**Multi-phase integration tests** (especially for live-network scenarios) use separate functions per phase, wired by a state JSON file:

```solidity
contract UniswapV3FCI_IntegrationScript is Script, Test {
    string constant STATE_FILE = "broadcast/v3-integration-state.json";

    function deploy() public {
        // Phase 1: Deploy fresh tokens + pool + FCI
        vm.writeFile(STATE_FILE, json);
    }

    function mint() public {
        string memory stateJson = vm.readFile(STATE_FILE);
        address v3Pool = vm.parseJsonAddress(stateJson, ".v3Pool");
        // Phase 2: mint + swap
    }

    function burn() public { ... }  // Phase 3
    function verify() public { ... } // Phase 4: assertions
}
```

**Files:** `test/fee-concentration-index-v2/protocols/uniswapV3/UniswapV3FeeConcentrationIndex.integration.t.sol`

## Formal Proofs (Kontrol)

Kontrol proofs use `prove_` prefix and `assert()` (not `assertEq`):

```solidity
contract SqrtPriceLookbackPayoffX96Proof is Test {
    /// @dev INV-002 (formal): δ⁺=0 ⟹ result = Q96
    function prove_deltaPlusZero_returns_Q96() public pure {
        uint160 result = deltaPlusToSqrtPriceX96(0);
        assert(result == uint160(SqrtPriceLibrary.Q96));
    }
}
```

**Files:** `test/fci-token-vault/kontrol/SqrtPriceLookbackPayoffX96.k.sol`

## Coverage

**Requirements:** No enforced coverage threshold.

**View Coverage:**
```bash
forge coverage --profile default
```

## Test Types

**Unit Tests:**
- Target: free functions, storage modules, individual contract methods
- Pattern: caller contract wrapping the module + `Test` inheritance
- Scope: one function/invariant per test method, labeled with `@dev INV-NNN:`
- Location: `test/*/unit/`, `test/fee-concentration-index-v2/*.t.sol`

**Admin Tests:**
- Target: admin-only functions (setFci, migrateFunds, transferOwnership)
- Pattern: deploy contract, test happy path + `vm.prank(notOwner)` + `vm.expectRevert`
- Location: `test/*/ContractName.admin.t.sol`

**Integration Tests:**
- Target: full lifecycle through multiple contracts (FCI hook + pool + vault)
- Pattern: inherits `PosmTestSetup` + `FCITestHelper`/`FCIFixture`, deploys full stack
- Uses `HookMiner.find()` to mine hook addresses with correct permission bits
- Location: `test/*/integration/*.integration.t.sol`

**Adversarial Tests:**
- Target: state-machine guard violations, settled-vault attacks, composition exploits
- Pattern: inherits `FCIFixture`, exercises negative paths with `vm.expectRevert`
- Location: `test/fci-token-vault/adversarial/`

**Fuzz Tests:**
- Target: mathematical properties and monotonicity invariants
- Pattern: `testFuzz_` prefix, `bound()` for all inputs
- Location: `test/*/FeatureName.fuzz.t.sol`

**Invariant Tests:**
- Target: system-level balance invariants (supply parity, totalDeposits accounting)
- Pattern: handler + ghost variables + `invariant_` function + `targetContract`
- Location: `test/*/fuzz/*Invariant.fuzz.t.sol`

**Differential Tests:**
- Target: V1 vs V2 behavioral equivalence across all FCI scenarios
- Pattern: dual-context base + scenario helpers + `_assertStateEqual()`
- Location: `test/fee-concentration-index-v2/differential/`

**Fork Tests:**
- Target: live Uniswap V3/V4 state, real fee growth reading
- Pattern: `vm.createSelectFork(...)`, reads from Alchemy RPC via env vars
- Location: `test/*/fork/` and `test/simulation/CapponiJITSequentialGame.fork.t.sol`

**E2E Tests (Forge Script as Test):**
- Pattern: `Script, Test` dual inheritance, multi-phase functions, state persisted to JSON
- Location: `test/fee-concentration-index-v2/protocols/uniswapV3/UniswapV3FeeConcentrationIndex.integration.t.sol`

## Common Patterns

**V4 Pool deployment in tests:**
```solidity
// Always use PosmTestSetup helpers
deployFreshManagerAndRouters();
deployMintAndApprove2Currencies();
deployAndApprovePosm(manager);

// Hook address mining for permission bits
(address hookAddr, bytes32 salt) = HookMiner.find(
    address(this), flags,
    type(FeeConcentrationIndex).creationCode,
    constructorArgs
);
FeeConcentrationIndex hook = new FeeConcentrationIndex{salt: salt}(address(manager));
require(address(hook) == hookAddr, "hook address mismatch");
```

**Prank pattern for multi-actor scenarios:**
```solidity
vm.startPrank(lp);
// multiple calls
vm.stopPrank();

// single call
vm.prank(lp);
someCall();
```

**Time/block manipulation:**
```solidity
vm.roll(block.number + JIT_ENTRY_OFFSET);   // advance blocks
vm.warp(block.timestamp + EPOCH_LENGTH);     // advance time
```

**Async revert testing:**
```solidity
vm.expectRevert(VaultAlreadySettled.selector);
vault.deposit(amount);

// With no specific selector (any revert)
vm.expectRevert();
callback.transferOwnership(makeAddr("x"));
```

**Event assertion:**
```solidity
vm.expectEmit(true, true, false, false);   // indexed1=true, indexed2=true, indexed3=false, data=false
emit UniswapV3Callback.FciUpdated(fci, newFci);
callback.setFci(newFci);
```

**Reactive contract setup (mock SystemContract):**
```solidity
address systemContract = 0x0000000000000000000000000000000000fffFfF;
vm.etch(systemContract, hex"00");            // give it code so extcodesize > 0
vm.mockCall(systemContract, bytes(""), abi.encode(true));  // all calls return true
```

**Raw storage write for flag injection:**
```solidity
bytes32 reactVmSlot = keccak256("reactive.reactVM");
vm.store(address(this), reactVmSlot, bytes32(uint256(1)));
```

---

*Testing analysis: 2026-03-18*
