# Testing Patterns

**Analysis Date:** 2026-03-17

## Test Framework

**Runner:**
- Forge (Foundry) for Solidity tests
- pytest for Python tests
- Config: `foundry.toml` with profiles for unit, fuzz, invariant

**Solidity Test Setup:**
```toml
[profile.default]
fuzz.runs = 256
invariant.runs = 64
invariant.depth = 32

[profile.fuzz-heavy]
fuzz.runs = 64
fuzz.max_test_rejects = 131072
```

**Python Test Setup:**
- Pytest runner: `uhi8/bin/pytest research/tests/ -v`
- Environment: PYTHONPATH must include `research/` directory
- Virtual environment: `uhi8/` (managed by `make`)

**Run Commands:**
```bash
# Forge unit + fork tests
forge test --match-path "test/fee-concentration-index/**" -vv

# Forge with heavy fuzz
forge test --profile fuzz-heavy

# Python tests
cd research && ../uhi8/bin/pytest tests/ -v

# Notebooks (headless)
make notebooks

# Coverage (Solidity)
forge coverage

# Data provenance
make verify-data
```

## Test File Organization

**Location — Solidity:**
- Co-located with source but under `test/` root
- Hierarchy mirrors source: `src/fee-concentration-index-v2/` → `test/fee-concentration-index-v2/`
- Subdirectories by test type: `unit/`, `integration/`, `fork/`, `fuzz/`, `differential/`
- Special tests: `kontrol/` for formal verification specs, `template/` for protocol adapter patterns

**Location — Python:**
- `research/tests/` root
- Subdirectories: `backtest/`, `econometrics/`, `data/`
- Test file: `test_<module>.py`

**Naming:**
- Solidity test files: `<Subject>.t.sol` with optional type: `<Subject>.<type>.t.sol`
  - Types: `unit`, `fork`, `fuzz`, `diff` (differential), `integration`, `k` (kontrol)
  - Examples: `FeeConcentrationIndexV2Full.integration.t.sol`, `DifferentialFCI.fork.t.sol`
- Python test files: `test_<module>.py`
  - Examples: `test_payoff.py`, `test_oracle_comparison.py`

**File Structure — Solidity:**
```
test/fee-concentration-index-v2/
├── protocols/
│   ├── uniswap-v3/
│   │   ├── integration/
│   │   │   └── FeeConcentrationIndexV2Full.integration.t.sol
│   │   └── differential/
│   │       └── FeeConcentrationIndexV4ReactiveV3.diff.t.sol
│   └── uniswap-v4/
├── fork/
│   ├── DifferentialFCI.fork.t.sol
│   └── FeeConcentrationIndexFull.fork.t.sol
├── template/
│   ├── ProtocolAdapterMod.t.sol
│   └── ProtocolAdapterStorage.t.sol
└── kontrol/
    └── PoolKeyExt.k.sol
```

**File Structure — Python:**
```
research/
├── tests/
│   ├── backtest/
│   │   ├── test_payoff.py
│   │   ├── test_calibrate.py
│   │   └── test_pnl.py
│   ├── econometrics/
│   └── data/
│       └── test_frozen_loaders.py
└── data/
    ├── scripts/
    │   ├── fci_oracle.py
    │   └── fci_epoch_oracle.py
    └── fixtures/
```

## Test Structure

**Suite Organization — Solidity:**
```solidity
contract FeeConcentrationIndexV2FullIntegrationTest is Test {
    using PoolIdLibrary for PoolKey;

    // ── State variables (test fixtures) ──
    Accounts accounts;
    IUniswapV3Pool v3Pool;
    FeeConcentrationIndexV2 fci;

    // ── Setup ──
    function setUp() public {
        // 1. Initialize test accounts
        // 2. Deploy mock contracts
        // 3. Set up initial state
    }

    // ── Test functions ──
    function test_registration_succeeds() public {
        // Arrange
        // Act
        // Assert
    }

    function test_integration_listenMustTriggerReactiveSubscriptions() public {
        // Multi-step test with comments marking phases
    }
}
```

**Patterns:**
- Inherits from `Test` (forge-std)
- `setUp()` runs before each test; use `startBroadcast()` for deployment
- Test names: `test_<subject>_<condition>` or `testFuzz_<subject>`
- Prefix for readability: `test_integration_*`, `test_fork_*`, `testFuzz_*`
- State stored as contract fields initialized in `setUp()`
- Use `console2.log()` for debug output

**Suite Organization — Python:**
```python
def test_delta_to_price():
    """Unit test — simple assertion."""
    assert delta_to_price(0.0) == 0.0
    assert abs(delta_to_price(0.5) - 1.0) < 1e-9

def test_run_exit_payoff_returns_correct_type():
    """Integration test — result type and structure."""
    result = run_exit_payoff_backtest(
        SIMPLE_STATES, SIMPLE_POSITIONS, gamma=0.10, alpha=2.0,
        delta_star=0.09, initial_balance=1000.0,
    )
    assert isinstance(result, ExitPayoffResult)
    assert result.alpha == 2.0

def test_position_above_threshold_gets_payout():
    """Integration test with assertions on computed values."""
    result = run_exit_payoff_backtest(...)
    pos0 = result.position_results[0]
    assert pos0.max_delta_plus == 0.20
    assert pos0.payout > pos0.premium
```

**Patterns:**
- Test function: `test_<subject>_<condition>`
- Setup using helper functions (e.g., `_make_state()`)
- Assertions on final state, not intermediate steps
- Comments for complex scenarios (e.g., "Position 0: alive Jan 1-2, max Δ⁺ = 0.20")
- Frozen dataclasses as test fixtures simplify data construction

## Mocking

**Framework:**
- Solidity: `forge-std` vm cheatcodes + `MockERC20` from solmate
- Python: Simple dataclasses; immutability prevents mutation errors

**Mock Patterns — Solidity:**

**1. Mock Tokens:**
```solidity
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";

MockERC20 tokenA = new MockERC20("Token A", "TKA", 18);
MockERC20 tokenB = new MockERC20("Token B", "TKB", 18);
```

**2. Fork Testing:**
```solidity
vm.createSelectFork(vm.rpcUrl("sepolia"));  // Fork at latest block
// or
vm.createSelectFork(vm.rpcUrl("sepolia"), BLOCK_NUMBER);  // Fork at specific block
```

**3. Account Creation:**
```solidity
address deployer = makeAddr("deployer");
address lpPassive = makeAddr("lpPassive");
```

**4. State Manipulation:**
```solidity
vm.startBroadcast(deployer);
// Actions as deployer
vm.stopBroadcast();

vm.prank(sender);  // Next call as sender

vm.startPrank(sender);  // All calls as sender until stopPrank
// Multiple actions as sender
vm.stopPrank();
```

**5. Delegatecall Testing:**
```solidity
// Test verifies delegatecall target receives correct context
bytes32 result = abi.decode(
    LibCall.delegateCallContract(facet, abi.encodeCall(IFCIProtocolFacet.positionKey, (...))),
    (bytes32)
);
```

**What to Mock:**
- External protocols (V3 pools, V4 manager) → fork real instances
- Token transfers → use MockERC20 or deploy real tokens, fund from fork
- Events → assert via `forge-std` log matching or manual event parsing
- Accounts → use `makeAddr(name)` for deterministic addresses

**What NOT to Mock:**
- Storage access → use real diamond storage patterns; test storage isolation
- Delegatecall boundaries → ensure tests exercise actual delegatecall, not mocking
- Math libraries → use real FixedPointMathLib, test edge cases instead

**Mock Patterns — Python:**
```python
def _make_state(day: str, delta_plus: float, n_positions: int = 10,
                pool_daily_fee: float = 100.0) -> DailyPoolState:
    """Factory for test state."""
    return DailyPoolState(
        day=day, a_t_real=0.0, a_t_null=0.0,
        delta_plus=delta_plus, il=0.0,
        n_positions=n_positions, pool_daily_fee=pool_daily_fee,
    )

SIMPLE_STATES = [
    _make_state("2024-01-01", delta_plus=0.05),
    _make_state("2024-01-02", delta_plus=0.20),
]
```

**Fixture Data:**
- Pre-computed JSON snapshots: `research/data/fixtures/`
- Raw event logs: `research/data/raw/`
- Test data loaded at test start, not mutated during test
- Frozen dataclasses enforce immutability

## Fixtures and Factories

**Test Data — Solidity:**
- Loaded from fork state (Sepolia, Unichain Sepolia)
- Constants for deployed contract addresses:
  ```solidity
  address constant CALLBACK_PROXY = 0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA;
  address constant POOL_MANAGER = 0x00B036B58a818B1BC34d502D3fE730Db729e62AC;
  ```
- Mock token factories in setUp():
  ```solidity
  vm.startPrank(deployer);
  tokenA = new MockERC20("Token A", "TKA", 18);
  tokenB = new MockERC20("Token B", "TKB", 18);
  vm.stopPrank();
  ```
- Accounts struct: `Accounts accounts = initAccounts(vm);`
  - Fields: `deployer`, `lpPassive`, `lpSophisticated`, `swapper`
  - Source: `foundry-script/types/Accounts.sol`

**Test Data — Python:**
- Frozen dataclass instances built via helper functions
- File-level constants for test scenarios:
  ```python
  SIMPLE_STATES = [
      _make_state("2024-01-01", delta_plus=0.05),
      _make_state("2024-01-02", delta_plus=0.20),
  ]

  SIMPLE_POSITIONS = [
      {"burn_date": "2024-01-03", "blocklife": 14400},
      {"burn_date": "2024-01-02", "blocklife": 7200},
  ]
  ```
- Fixtures loaded from JSON: `research/data/fixtures/fci_weth_usdc_v4.json`
- Location: `research/data/fixtures/` (referenced in foundry.toml fs_permissions)

## Coverage

**Requirements:**
- No minimum enforced; target 80%+ for critical paths
- Integration tests + fork tests provide higher coverage than unit alone

**View Coverage:**
```bash
# Forge coverage report
forge coverage

# Export LCOV format
forge coverage --report lcov
```

**Coverage Gaps (Known):**
- Error paths: tested via fuzz rejects
- Edge cases: fork tests on real state verify real-world behavior
- Rarely-called functions: tagged with SCOP comments (standards as option)

## Test Types

**Unit Tests:**
- Scope: Single function or storage module in isolation
- Location: `test/*/unit/`
- Example: Test a free function in `FeeConcentrationIndexRegistryStorageMod.sol`
- No external calls; mock storage if needed
- Fast (~1ms per test)

**Integration Tests:**
- Scope: Multi-function flow within one protocol (e.g., V3 reactive flow)
- Location: `test/*/integration/`
- Example: `FeeConcentrationIndexV2Full.integration.t.sol`
- Deploys full stack (FCI V2, facet, callback)
- Exercises delegatecall boundaries
- Can be slow (10-60s per test)

**Fork Tests:**
- Scope: End-to-end against real forked chain state
- Location: `test/*/fork/`
- Example: `DifferentialFCI.fork.t.sol`
- Fork Sepolia or Unichain Sepolia
- Validates deployment + pool creation + initialization
- Verifies equilibrium: deltaPlus = 0 at equilibrium
- Slow (60-300s depending on scenario)

**Differential Tests:**
- Scope: Compare V4 local hook vs. V3 reactive adapter
- Location: `test/*/differential/`
- Example: `FeeConcentrationIndexV4ReactiveV3.diff.t.sol`
- Runs same operation on both protocols
- Asserts index values match
- Verifies cross-protocol consistency

**Fuzz Tests:**
- Scope: Property-based testing with random inputs
- Naming: `testFuzz_<property>`
- Config: 256 runs by default; `--profile fuzz-heavy` runs 64x with 131K rejects
- Example: Fuzz test that random swaps maintain deltaPlus in [0, 1]
- Forge generates inputs; test asserts invariant holds

**Invariant Tests:**
- Scope: Multi-function stateful fuzzing (call sequence)
- Naming: `invariant_<property>`
- Config: 64 runs, 32 depth by default
- Example: Invariant that total liquidity = sum of position liquidities
- Forge generates sequences; test checks invariant at each step

**Kontrol/Formal Verification:**
- Scope: Algebraic correctness proofs
- Location: `test/*/kontrol/`
- Language: K specification (`.k.sol`)
- Example: Prove `positionKey()` is deterministic

## Common Patterns

**Async Testing — Solidity:**
No async/await in Solidity tests. Sequential execution:
```solidity
function test_sequence_succeeds() public {
    // Step 1
    vm.startBroadcast(deployer);
    fci.registerProtocolFacet(...);
    vm.stopBroadcast();

    // Step 2
    vm.prank(lpPassive);
    (/* result */) = fci.afterAddLiquidity(...);

    // Assert result
    assertEq(result, expected);
}
```

**Async Testing — Python:**
No async either; test runs sequentially:
```python
def test_exit_payoff_backtest():
    result = run_exit_payoff_backtest(SIMPLE_STATES, SIMPLE_POSITIONS, ...)
    assert result.total_payouts > 0
```

**Error Testing — Solidity:**
```solidity
function test_revert_on_zero_address() public {
    vm.expectRevert(ZeroAddress.selector);
    callback = new UniswapV3Callback(address(0), PROXY, deployer);
}

function test_revert_on_already_registered() public {
    // First registration succeeds
    vm.prank(deployer);
    facet.listen(abi.encode(v3Pool));

    // Second registration reverts
    vm.expectRevert(abi.encodeWithSelector(PoolAlreadyRegistered.selector, poolId));
    vm.prank(deployer);
    facet.listen(abi.encode(v3Pool));
}
```

**Error Testing — Python:**
```python
def test_delta_to_price_infinite_at_one():
    assert delta_to_price(1.0) == float("inf")

def test_payoff_multiplier_floored_at_zero():
    # max_price <= p_star -> multiplier = 0
    result = payoff_multiplier(0.05, 0.10, 2.0)
    assert result == 0.0
```

**FFI Tests (Forge → External Script):**
```solidity
// Calls Python oracle to compute FCI state
bytes memory output = vm.ffi(
    abi.encodePacked(
        "python research/data/scripts/fci_oracle.py ",
        " --pool-address ", address(v3Pool),
        " --block-number ", block.number
    )
);
uint256 expectedIndex = abi.decode(output, (uint256));
assertEq(fci.getIndex(...), expectedIndex);
```

## Test Execution

**Solidity Tests — Standard:**
```bash
# All tests (unit + fork + integration)
forge test -vv

# Specific directory
forge test --match-path "test/fee-concentration-index-v2/**" -vv

# Specific test function
forge test --match "test_registration_succeeds" -vv

# Fork tests only
forge test --match-path "test/**/fork/**" -vv

# Fuzz tests only (heavy profile)
forge test --profile fuzz-heavy --match "testFuzz" -vv
```

**Python Tests — Standard:**
```bash
cd research && ../uhi8/bin/pytest tests/ -v

# Specific file
../uhi8/bin/pytest tests/backtest/test_payoff.py -v

# Specific test
../uhi8/bin/pytest tests/backtest/test_payoff.py::test_delta_to_price -v

# Show print output
../uhi8/bin/pytest tests/ -v -s

# Run with coverage
../uhi8/bin/pytest tests/ --cov=backtest --cov-report=html
```

**Notebooks (Headless):**
```bash
make notebooks

# Executed via Makefile which:
# 1. Creates temp directory
# 2. Runs jupyter nbconvert --execute for each .ipynb
# 3. Verifies all cells pass
```

## Data Provenance

**Fixture Management:**
- Raw data: `research/data/raw/` — never committed
- Fixtures: `research/data/fixtures/` — snapshots of computed state
- Verify: `make verify-data` runs `research/data/scripts/verify_provenance.py`

**Oracle Scripts (FFI):**
- `research/data/scripts/fci_oracle.py` — replays FCI math on raw V4 events
- `research/data/scripts/fci_epoch_oracle.py` — computes epoch snapshots
- Called from tests via `vm.ffi()` to verify on-chain computation
- Dependencies: pycryptodome (keccak256 hashing)

---

*Testing analysis: 2026-03-17*
