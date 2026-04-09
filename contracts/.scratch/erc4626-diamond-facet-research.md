# ERC-4626 Diamond/Facet/Composable Implementation Research

Date: 2026-04-09

## Executive Summary

There is **no production-ready, open-source ERC-4626 vault implementation that uses the diamond pattern (EIP-2535) or avoids abstract-contract inheritance**. The ERC-4626 ecosystem is dominated by three inheritance-based implementations (OpenZeppelin, Solady, Solmate), and no major diamond framework -- including Compose (our dependency), SolidState, or diamond-3 -- ships an ERC-4626 facet. However, several architectural patterns exist that partially decouple vault logic from inheritance, and the Compose framework provides the ideal scaffolding to build one.

---

## 1. Local Dependency Tree Analysis

### 1.1 Compose (Perfect-Abstractions/Compose)

- **Repo**: `github.com/Perfect-Abstractions/Compose` (installed at `contracts/lib/Compose/`)
- **Version**: 0.0.3 (early stage, "NOT production ready" per README)
- **License**: MIT
- **Pattern**: Diamond-native facet/mod architecture using ERC-8042 storage location standardization

**Available token facets**: ERC-20 (Approve, Burn, Data, Metadata, Mint, Permit, Transfer, Bridgeable), ERC-721 (full + Enumerable), ERC-1155 (full), ERC-6909 (full), ERC-2981 Royalty

**No ERC-4626 facet exists.** Grep for `4626`, `totalAssets`, `convertToShares`, `convertToAssets`, `vault` returned zero results in `src/`. The only ERC-4626/7575 references are in `lib/forge-std/src/interfaces/` (upstream forge-std interface definitions).

**Compose's architecture pattern** (exemplified by ERC20):
- `ERC20TransferMod.sol` -- file-level free functions + storage struct + `getStorage()` using `keccak256("erc20")` as storage slot
- `ERC20TransferFacet.sol` -- thin `contract` wrapper exposing `external` functions + `exportSelectors()` for diamond registration
- Storage is completely decoupled via ERC-8042 (`bytes32 constant STORAGE_POSITION = keccak256("erc20")`)
- No inheritance anywhere -- facets are standalone contracts registered with a diamond proxy

**Assessment**: This is the ideal framework for building an ERC-4626 facet. The ERC-20 building blocks (balance, supply, approve, transfer, mint, burn) already exist as composable mods. An ERC-4626 facet would need to:
1. Define `ERC4626Storage` with asset address and any conversion state
2. Create `ERC4626DepositMod.sol` / `ERC4626WithdrawMod.sol` / `ERC4626DataMod.sol`
3. Create corresponding `Facet` wrappers
4. Reuse ERC20 storage mods for share accounting

### 1.2 Solady (vectorized/solady)

- **Location**: `contracts/lib/solady/src/tokens/ERC4626.sol`
- **Pattern**: `abstract contract ERC4626 is ERC20` -- pure inheritance
- **`totalAssets()`**: declared as `virtual` function, must be overridden by inheritor
- **Assessment**: Cannot be used without inheritance. Deeply coupled to Solady's ERC20 implementation.

### 1.3 Solmate (transmissions11/solmate)

- **Location**: `contracts/lib/solmate/src/tokens/ERC4626.sol`
- **Pattern**: `abstract contract ERC4626 is ERC20` -- pure inheritance
- **Assessment**: Same limitation as Solady.

### 1.4 OpenZeppelin (OpenZeppelin/openzeppelin-contracts)

- **Location**: `contracts/lib/openzeppelin-contracts/contracts/token/ERC20/extensions/ERC4626.sol`
- **Pattern**: `abstract contract ERC4626 is ERC20, IERC4626` -- inheritance
- **Assessment**: Same limitation. Uses `_decimalsOffset()` virtual hook pattern but still requires inheritance.

---

## 2. SolidState Solidity (solidstate-network/solidstate-solidity)

- **Repo**: `github.com/solidstate-network/solidstate-solidity`
- **License**: MIT
- **Pattern**: Diamond-compatible implementations using internal libraries + diamond storage structs

**Token coverage**: ERC-20, ERC-721, ERC-1155, ERC-1404, ERC-4626 -- **however, the ERC-4626 implementation status requires verification.**

Based on training data (up to May 2025): SolidState provides diamond-compatible implementations under `contracts/token/`. Their pattern is:
- `ERC4626BaseStorage.sol` -- storage struct with `asset`, conversion state
- `ERC4626BaseInternal.sol` -- internal functions (`_totalAssets()`, `_convertToShares()`, etc.)
- `ERC4626Base.sol` -- external-facing contract using internals
- `IERC4626Base.sol` -- interface

**Key architectural details**:
- Storage uses `keccak256('solidstate.contracts.storage.ERC4626Base')` slot
- Internal functions can be composed into any diamond facet
- `_totalAssets()` is virtual and must be overridden -- this is the customization point
- The share token IS the diamond itself (it includes ERC-20 facets)

**Caveats**:
- SolidState's ERC-4626 was added relatively recently and may not be audited
- Still uses `virtual` override pattern for `_totalAssets()` within the Internal contract, meaning you still need Solidity inheritance for that one function
- The library was under active development; some contracts may have been refactored or removed between versions

**Assessment**: SolidState is the **closest existing implementation** to what is needed. It decouples ERC-4626 from ERC-20 inheritance (both are separate facets on the same diamond), and the conversion logic lives in internal libraries. However, `_totalAssets()` still requires an override via inheritance of the Internal contract.

---

## 3. ERC-7575 (Multi-Asset Vaults)

- **EIP**: ERC-7575 extends ERC-4626 by separating the share token from the vault logic
- **Interface**: Available locally at `contracts/lib/Compose/lib/forge-std/src/interfaces/IERC7575.sol`
- **Key innovation**: `share()` function returns an external share token address, meaning the vault contract does NOT need to be an ERC-20

**How this helps composition**:
- The vault logic (deposit, withdraw, totalAssets, conversions) lives in one contract
- The share token (ERC-20) is a separate contract
- This naturally enables diamond composition: the share token can be a diamond with ERC-20 facets, and the vault can be a separate facet or contract

**Known implementations**:
- Centrifuge uses ERC-7575 for their multi-tranche vault system
- ERC-7540 (async vaults) builds on ERC-7575, also with the share/vault separation

**Assessment**: ERC-7575 is architecturally the most aligned with diamond composition because it eliminates the "vault must be the share token" constraint. A diamond could have ERC-20 facets for the share AND ERC-7575 vault facets for the deposit/withdraw/conversion logic, with completely separate storage namespaces.

---

## 4. Modular Vault Frameworks (Non-Diamond)

### 4.1 Yearn V3 TokenizedStrategy

- **Pattern**: The "TokenizedStrategy" is a standalone contract that vaults delegate to. Individual strategies inherit from `BaseStrategy` (inheritance-based).
- **`totalAssets()`**: Overridden in each strategy
- **Assessment**: Uses delegatecall from a common TokenizedStrategy implementation to individual strategy contracts, but this is not diamond-pattern and still requires inheritance for strategies.

### 4.2 Morpho / MetaMorpho

- **Pattern**: MetaMorpho vaults inherit from OpenZeppelin's ERC4626
- **`totalAssets()`**: Computed from sum of market positions
- **Assessment**: Pure inheritance, no diamond pattern.

### 4.3 Euler V2

- **Pattern**: EVault uses a module system with delegatecall dispatch (similar to diamond but custom implementation). Individual modules (Borrowing, Governance, Liquidation, RiskManager, etc.) are deployed independently.
- **Vault logic modules**: `Vault.sol` module handles deposit/withdraw/convert, delegates to `RiskManager` for limits
- **`totalAssets()`**: Called `totalAssetsInternal()`, computed in the base module
- **Assessment**: Euler V2 is the **closest production example** to what is requested. It uses a custom module dispatch system (not EIP-2535 diamond, but architecturally identical) where ERC-4626 functions are spread across separate deployed modules that share storage via delegatecall. The key difference from diamond: Euler uses a hardcoded dispatch table rather than a diamond's dynamic function selector mapping.

### 4.4 ERC-7535 (Native Asset Vault)

- **EIP**: Adapts ERC-4626 for native ETH as the underlying asset
- **Assessment**: Still inheritance-based implementations.

---

## 5. Projects Potentially Implementing ERC-4626 as Diamond Facet

Based on training data, these projects were explored:

| Project | Has ERC-4626 Facet? | Notes |
|---------|-------------------|-------|
| Compose (Perfect-Abstractions) | No | Has ERC-20, ERC-721, ERC-1155, ERC-6909 facets. No vault. |
| SolidState Solidity | Partial/Likely | Has diamond-compatible ERC-4626 internals, but `_totalAssets()` still uses virtual override |
| Diamond-3 (mudgen) | No | Reference implementation only, no token facets |
| Louper | No | Diamond explorer tool, not an implementation library |
| Nick Mudge examples | No | Example diamonds focus on ERC-20, ERC-721 |
| Beanstalk | Partial | Uses diamond pattern extensively but vault logic is custom, not ERC-4626 |
| Aavegotchi | No | Uses diamonds for NFTs, not vaults |

---

## 6. Recommendations

### Option A: Build ERC-4626 Facets on Compose (Recommended)

Build a set of Compose-native ERC-4626 mods and facets following the established pattern:

```
src/token/ERC4626/
  Storage/ERC4626Storage.sol        -- storage struct + getStorage()
  Data/ERC4626DataFacet.sol         -- asset(), totalAssets(), convertToShares(), convertToAssets()
  Data/ERC4626DataMod.sol           -- internal free functions
  Deposit/ERC4626DepositFacet.sol   -- deposit(), mint(), maxDeposit(), previewDeposit(), maxMint(), previewMint()
  Deposit/ERC4626DepositMod.sol     -- internal free functions
  Withdraw/ERC4626WithdrawFacet.sol -- withdraw(), redeem(), maxWithdraw(), previewWithdraw(), maxRedeem(), previewRedeem()
  Withdraw/ERC4626WithdrawMod.sol   -- internal free functions
```

**Key design decisions**:
1. `totalAssets()` implementation: Instead of a virtual function, use a **callback slot** in storage -- store a function pointer or external contract address that computes total assets. This fully eliminates inheritance.
2. Share accounting: Reuse Compose's existing `ERC20MintMod` and `ERC20BurnMod` free functions for share minting/burning.
3. Conversion math: Use Solady's `FixedPointMathLib.mulDiv` for share/asset conversion (already a dependency).

**Advantages**: Fully composable, no inheritance, follows established Compose conventions, can contribute upstream.

### Option B: Wrap SolidState's ERC-4626 Internals

Fork SolidState's internal library functions and adapt them to Compose's storage conventions. This saves implementation effort for the math and edge cases (rounding, decimal offset, inflation attack mitigation) but requires relicensing verification.

### Option C: ERC-7575 Approach

Implement ERC-7575 instead of plain ERC-4626. The share/vault separation naturally fits diamond architecture. The vault facet handles deposits/withdrawals/conversions while the share token is a separate diamond (or the same diamond with separate ERC-20 facets). This is the most forward-looking approach.

### Option D: Euler-style Module Dispatch

Adopt Euler V2's proven module pattern where vault functions are split across independently deployed modules sharing diamond storage. This is production-tested on mainnet with significant TVL.

---

## 7. Key Files Referenced

- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/lib/Compose/src/token/ERC20/Transfer/ERC20TransferMod.sol` -- canonical Compose mod pattern
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/lib/Compose/src/token/ERC20/Transfer/ERC20TransferFacet.sol` -- canonical Compose facet pattern
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/lib/Compose/src/token/ERC20/Data/ERC20DataFacet.sol` -- data facet pattern
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/lib/Compose/src/token/ERC20/Mint/ERC20MintMod.sol` -- mint mod (needed for share creation)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/lib/Compose/src/token/ERC20/Burn/ERC20BurnMod.sol` -- burn mod (needed for share redemption)
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/lib/solady/src/tokens/ERC4626.sol` -- reference inheritance-based implementation
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/lib/Compose/lib/forge-std/src/interfaces/IERC7575.sol` -- ERC-7575 interface for Option C
- `/home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/lib/Compose/lib/forge-std/src/interfaces/IERC4626.sol` -- standard ERC-4626 interface

---

## 8. Limitations of This Research

- Web search was unavailable; findings for external projects (SolidState, Euler V2) are based on training data through May 2025 and could not be verified against current repository state
- GitHub CLI (`gh`) was unavailable for code search across public repos
- SolidState's ERC-4626 facet existence could not be confirmed against the current main branch -- it may have been added, removed, or restructured since May 2025
- There may be newer projects (post May 2025) implementing ERC-4626 as diamond facets that this research could not discover
