# Compose ERC-4626 Facet vs Solady Inheritance: Tradeoff Analysis

Date: 2026-04-09

## Executive Summary

This analysis compares three architectural options for implementing V_B (the ThetaSwap vault contract): (A) building a native ERC-4626 facet on the Compose diamond framework, (B) inheriting from Solady's battle-tested ERC4626 abstract contract, and (C) a hybrid approach using Solady for V_B while keeping everything else in Compose. The recommendation is **Option C (Hybrid)** for the initial deployment, with a planned migration path to Option A once Compose's ERC-4626 ecosystem matures.

---

## Task 1 Findings: Compose's Mod/Facet Architecture

### Pattern Summary

Compose implements a two-layer architecture that completely eliminates Solidity inheritance:

**Layer 1 -- Mods (file-level free functions)**
- Declare storage structs, events, errors, and constants at file scope (outside any `contract` block)
- Define a `getStorage()` function that binds a storage struct to a deterministic slot via `keccak256("erc20")` (ERC-8042 pattern)
- Implement logic as free functions (e.g., `function transfer(...)`, `function mint(...)`) that call `getStorage()` internally
- These produce **no standalone bytecode** -- they are inlined or JUMPed into by the importing contract at compile time

Key files examined:
- `lib/Compose/src/token/ERC20/Transfer/ERC20TransferMod.sol` (lines 67-148): Storage at `keccak256("erc20")`, free functions `transfer()` and `transferFrom()`
- `lib/Compose/src/token/ERC20/Mint/ERC20MintMod.sol` (lines 31-68): Same storage slot, `mint()` free function
- `lib/Compose/src/token/ERC20/Burn/ERC20BurnMod.sol` (lines 39-83): Same storage slot, `burn()` free function
- `lib/Compose/src/token/ERC20/Approve/ERC20ApproveMod.sol` (lines 25-64): Same storage slot, `approve()` free function

**Layer 2 -- Facets (thin contract wrappers)**
- Standalone contracts that redeclare the same storage struct/slot and expose `external` functions
- Each facet includes an `exportSelectors()` function returning packed `bytes4` selectors for diamond registration
- Facets are deployed once, then reused by many diamonds via delegatecall

Key files examined:
- `lib/Compose/src/token/ERC20/Transfer/ERC20TransferFacet.sol` (lines 85-145): External `transfer()` and `transferFrom()`, plus `exportSelectors()`
- `lib/Compose/src/token/ERC20/Data/ERC20DataFacet.sol` (lines 40-71): External `totalSupply()`, `balanceOf()`, `allowance()`

**Diamond Dispatch (DiamondMod.sol)**
- Storage at `keccak256("erc8153.diamond")` mapping `bytes4 selector => FacetNode{facet address, prev, next}`
- `diamondFallback()` (line 344): looks up `msg.sig` in storage, gets facet address, does `delegatecall`
- Facet registration via `addFacets(address[] memory)` which calls `exportSelectors()` on each facet and stores selector-to-facet mappings
- Uses EIP-8153 (Facet-Based Diamonds), a newer variant of EIP-2535

### How State Is Separated from Logic

State lives in deterministic storage slots (ERC-8042). Multiple mods and facets declare the same struct at the same slot. They all read/write the same underlying storage because they execute via delegatecall in the diamond's context. No contract ever "owns" state -- the diamond address does.

### How External Functions Are Exposed

Facets are registered via `addFacets()` in the diamond's constructor. Each facet reports its selectors through `exportSelectors()`. The fallback handler dispatches incoming calls by looking up the selector in a mapping and delegatecalling the corresponding facet.

### How a New Facet (e.g., ERC-4626) Would Be Added

1. Create `ERC4626Storage` struct in a new storage namespace (e.g., `keccak256("erc4626")`) with `asset` address and any vault-specific state
2. Write mod files with free functions: `deposit()`, `withdraw()`, `mint()`, `redeem()`, `convertToShares()`, `convertToAssets()`, `totalAssets()`, `previewDeposit()`, etc.
3. These mods would import ERC20 mods (MintMod, BurnMod, TransferMod) for share token accounting
4. Write corresponding Facet contracts wrapping mods as external functions with `exportSelectors()`
5. Register the facet addresses in the diamond constructor alongside ERC20 facets

### ERC-4626 in Compose Repo

No ERC-4626 facet exists in the Compose source tree. Grepping for `4626`, `totalAssets`, `convertToShares`, `vault` across `lib/Compose/src/` returns zero results. The only 4626 references are in `lib/Compose/lib/forge-std/src/interfaces/IERC4626.sol` (upstream forge-std). Compose is at version 0.0.3 and explicitly states it is "NOT production ready."

---

## Task 2: Tradeoff Analysis

### Option A: Build ERC-4626 Facet on Compose

**What we would build:**
- `ERC4626Storage` struct at `keccak256("erc4626")` with: `address asset`, `address rateProvider` (T_B), `address governor`
- `ERC4626DepositMod.sol` -- `deposit()`, `mint()` free functions that call `ERC20MintMod.mint()` for shares
- `ERC4626WithdrawMod.sol` -- `withdraw()`, `redeem()` free functions that call `ERC20BurnMod.burn()` for shares
- `ERC4626AccountingMod.sol` -- `totalAssets()` (calls T_B), `convertToShares()`, `convertToAssets()`, preview functions, max functions
- `ERC4626DepositFacet.sol`, `ERC4626WithdrawFacet.sol`, `ERC4626DataFacet.sol` -- thin external wrappers
- Inflation attack mitigation: virtual shares implementation (reimplementing Solady's `_useVirtualShares` + `_decimalsOffset` logic)
- Rounding direction correctness across all 8 conversion/preview functions (deposits round down in shares, withdrawals round up)

**Estimated effort:** 3-5 weeks for implementation + comprehensive test suite. Additional 2-4 weeks for internal audit preparation.

**Pros:**
- Pure Compose pattern -- no inheritance anywhere in the system
- T_B is a storage slot value, swappable by governor -- no virtual override needed
- Maximum composability: other facets can import ERC4626Mods and extend vault behavior
- Diamond upgradeability: facets can be replaced without redeploying the whole contract
- Consistent architecture across the entire ThetaSwap system (ct0, ct1, observation modules, V_B all diamond-native)
- The ERC-20 share token building blocks already exist in Compose (balance, supply, approve, transfer, mint, burn)

**Cons:**
- **Security risk is the dominant concern.** ERC-4626 has a well-documented attack surface:
  - First depositor inflation attack (Solady mitigates with virtual shares at lines 90-98, 174-178)
  - Rounding direction errors across 8 interrelated functions (Solady handles asymmetric rounding at lines 220-296 with `fullMulDiv` vs `fullMulDivUp`)
  - Share price manipulation via direct asset transfer
  - Edge cases at zero supply, zero assets, max uint256 values
  - Decimal offset interactions with non-18-decimal tokens
- **No existing audited reference implementation** for diamond-pattern ERC-4626. SolidState's attempt still uses `virtual` overrides for `_totalAssets()` -- it doesn't fully escape inheritance
- **Compose itself is v0.0.3 and not production-ready** (stated explicitly in their docs). Building critical financial infrastructure on pre-release framework code compounds risk
- **Rounding correctness is subtle.** Solady's implementation uses 527 lines of carefully optimized assembly. Reimplementing this correctly in free-function style requires exceptional care
- **Testing burden is massive.** ERC-4626 conformance tests, inflation attack tests, rounding boundary tests, decimal edge cases, reentrancy scenarios, delegatecall interaction tests

### Option B: Inherit from Solady ERC-4626

**What we would build:**
```
contract ThetaVault is ERC4626 {
    address public rateProvider;   // T_B address
    address public governor;       // Can swap T_B
    address public immutable ASSET;

    function asset() public view override returns (address) { return ASSET; }
    function totalAssets() public view override returns (uint256) {
        return IRateProvider(rateProvider).totalAssets();
    }
    function setRateProvider(address newProvider) external {
        require(msg.sender == governor);
        rateProvider = newProvider;
    }
}
```

**Estimated effort:** 1-2 weeks including tests.

**Pros:**
- **Battle-tested.** Solady's ERC4626 is used in production by multiple protocols, audited, and gas-optimized with hand-tuned assembly
- **Inflation attack protection built in.** Virtual shares enabled by default (`_useVirtualShares() returns true` at line 97), with configurable decimal offset
- **All 8 conversion functions correctly implemented** with proper rounding direction (lines 167-296)
- **Edge cases handled.** Zero supply, zero assets, max values, decimal mismatches -- all covered
- **Minimal new code.** The vault shell is approximately 30-50 lines of Solidity. The only custom logic is `totalAssets()` calling T_B and the governor pattern for T_B swapping
- **Fast to implement and audit.** Auditors only need to review the override logic, not the vault mechanics
- **MIT licensed.** No licensing concerns

**Cons:**
- **Requires inheritance.** `ThetaVault is ERC4626 is ERC20` -- the share token is baked into the inheritance chain, not a separate Compose facet
- **Not a diamond facet.** V_B is a standalone contract at its own address. Cannot compose with other Compose facets in the same diamond
- **No diamond upgradeability.** If V_B needs a logic change, you need a proxy pattern on top of Solady, or a migration. Solady's ERC4626 was not designed for proxy usage (storage layout may not be compatible)
- **T_B swapping adds governor state** on top of Solady's base -- a thin but auditable addition
- **Architectural inconsistency.** If ct0, ct1, and observation modules are Compose diamonds, V_B being inheritance-based is the odd one out. This matters for developer experience and system-level reasoning

### Option C: Hybrid (Solady V_B + Compose for Everything Else)

**What this looks like:**
- V_B is a standalone contract inheriting Solady ERC4626, deployed at its own address
- ct0, ct1 are Compose diamonds (or Panoptic CTs)
- Storage modules (observation, EMA, growth tracking) are Compose-style free functions with diamond storage
- V_B reads totalAssets from T_B (an external call), but V_B itself is not part of any diamond
- The governor pattern for T_B swapping lives in V_B as a simple storage variable + access control

**Estimated effort:** 1-2 weeks for V_B, with the rest of the system on its own Compose-native timeline.

**Pros:**
- **Audited vault mechanics with minimal new code.** The highest-risk component (ERC-4626 share accounting, inflation protection, rounding) is Solady's battle-tested implementation
- **Compose for everything that benefits from composability.** Observation modules, EMA computation, growth tracking -- these are novel ThetaSwap logic that benefits from diamond upgradeability and modular composition
- **V_B is the simplest component in the system.** It's essentially a vault shell + external call to T_B. Spending 3-5 weeks building a diamond-native ERC-4626 for a component this simple is hard to justify
- **Minimal audit surface.** The only new audit scope is the `totalAssets()` override and T_B governor pattern -- perhaps 50 lines
- **Fastest path to deployment.** V_B can be production-ready while the more complex observation/oracle modules are still being developed

**Cons:**
- **Architectural inconsistency.** V_B is the one contract in the system that uses inheritance instead of diamonds. This is a real cost in developer cognitive load and system-level documentation
- **V_B cannot be upgraded via diamond pattern.** If the vault logic needs changes post-deployment, you need either: (a) deploy a new vault and migrate deposits, or (b) wrap V_B in a proxy. Neither is clean
- **Future integration friction.** If other facets need to directly interact with V_B's share accounting (e.g., a staking facet that reads share balances), they cannot import V_B's storage mods -- they must make external calls to V_B's address

---

## Comparative Matrix

| Criterion                    | A: Compose Native | B: Solady Inherit | C: Hybrid          |
|------------------------------|-------------------|-------------------|---------------------|
| Development time             | 5-9 weeks         | 1-2 weeks         | 1-2 weeks           |
| Audit surface (new code)     | ~800-1200 lines   | ~50 lines         | ~50 lines           |
| ERC-4626 security confidence | Low (unaudited)   | High (battle-tested) | High (battle-tested) |
| Architectural consistency    | Perfect           | Poor              | Acceptable          |
| Diamond upgradeability       | Yes               | No                | No (for V_B only)   |
| Compose composability        | Full              | None              | Partial             |
| Inflation attack protection  | Must reimplement  | Built-in          | Built-in            |
| Rounding correctness         | Must reimplement  | Proven            | Proven              |
| Production readiness         | Months away       | Weeks away        | Weeks away          |
| T_B pluggability             | Storage slot      | Storage variable  | Storage variable    |
| Long-term maintainability    | Best              | Adequate          | Good                |

---

## Recommendation

**Use Option C (Hybrid) for the initial deployment. Plan for Option A as a v2 migration once Compose stabilizes.**

### Rationale

The decision pivots on a single question: **where is the risk?**

V_B's core function is ERC-4626 share accounting -- a standard with well-documented security pitfalls that have been exhaustively addressed by Solady over years of production use. The ThetaSwap-specific innovation (T_B rate provider, observation oracles, growth tracking) lives in the *other* contracts, not in the vault shell. Building a from-scratch ERC-4626 implementation in a pre-release framework (Compose v0.0.3) for the one component that is essentially a solved problem would be allocating engineering and audit resources where they add the least value.

The architectural inconsistency of Option C is real but manageable. V_B has a narrow, well-defined interface (ERC-4626 + T_B governor). It does not need to share storage with other facets. It does not need diamond upgradeability (the vault logic is standard and unlikely to change; T_B swapping handles the one dimension of variability).

### Migration Path to Option A

When Compose reaches v1.0 and/or when/if the community produces an audited ERC-4626 facet:

1. Build and audit the Compose-native ERC-4626 facet
2. Deploy a new V_B diamond with the facet
3. Migrate deposits from the Solady V_B to the new diamond V_B (standard vault migration pattern)
4. Deprecate the Solady V_B

This gives us the safety of Solady now and the architectural purity of Compose later, without rushing either.

### Immediate Next Steps

1. Implement `ThetaVault is ERC4626` with `totalAssets()` override calling T_B
2. Add governor pattern for T_B address swapping with timelock
3. Write conformance test suite (ERC-4626 property tests, inflation attack tests)
4. Document the architectural decision and planned migration path
5. Open a Compose GitHub issue requesting ERC-4626 facet, referencing this analysis

---

## Appendix: Key File References

### Compose Architecture
- `contracts/lib/Compose/src/token/ERC20/Transfer/ERC20TransferMod.sol` -- Canonical mod pattern (free functions, ERC-8042 storage)
- `contracts/lib/Compose/src/token/ERC20/Transfer/ERC20TransferFacet.sol` -- Canonical facet pattern (external wrappers, exportSelectors)
- `contracts/lib/Compose/src/diamond/DiamondMod.sol` -- Diamond dispatch (selector mapping, delegatecall fallback)
- `contracts/lib/Compose/src/token/ERC20/Mint/ERC20MintMod.sol` -- Mint mod (would be imported by ERC-4626 deposit logic)
- `contracts/lib/Compose/src/token/ERC20/Burn/ERC20BurnMod.sol` -- Burn mod (would be imported by ERC-4626 withdraw logic)

### Solady ERC-4626
- `contracts/lib/solady/src/tokens/ERC4626.sol` -- 527 lines, abstract contract. Key sections:
  - Lines 90-98: Virtual shares configuration (inflation attack mitigation)
  - Lines 167-204: `convertToShares()` / `convertToAssets()` with virtual share math
  - Lines 220-296: Preview functions with asymmetric rounding (`fullMulDiv` vs `fullMulDivUp`)
  - Lines 376-437: `deposit()`, `mint()`, `withdraw()`, `redeem()` external functions
  - Lines 455-488: Internal `_deposit()` / `_withdraw()` with SafeTransferLib

### Compose Documentation
- `contracts/lib/Compose/website/docs/foundations/facets-and-modules.mdx` -- Facet vs mod pattern explanation
- `contracts/lib/Compose/website/docs/foundations/solidity-modules.mdx` -- Module definition, diamond constructor example
- `contracts/lib/Compose/website/docs/foundations/custom-facets.mdx` -- How to build custom facets using mods
- `contracts/lib/Compose/website/docs/foundations/diamond-contracts.mdx` -- Diamond architecture overview

### Existing Research
- `contracts/.scratch/erc4626-diamond-facet-research.md` -- Prior research confirming no production diamond ERC-4626 exists
