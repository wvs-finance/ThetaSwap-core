# Vault Standards Research Report: ERC-4626, Structured Products, and Paired-Token Vaults

Date: 2026-03-11
Branch: `004-fci-token-vault`
Author: Papa Bear (deep research)

---

## Executive Summary

This report evaluates whether ERC-4626 and related vault standards fit the FCI Token Vault design: a collateral-locked paired-mint vault that tokenizes a DeFi oracle index into LONG/SHORT ERC-20 tokens with power-squared payoff and decaying high-water mark.

**Key conclusion: ERC-4626 is a poor fit for this vault.** The standard assumes a single-share-token yield-bearing vault with a monotonic assets-to-shares exchange rate. Our design mints *two* tokens per deposit, has no yield accrual, and the payoff is directional (LONG gains, SHORT loses). The closest architectural precedent is the **Gnosis Conditional Tokens Framework** (used by Polymarket), which implements split/merge of collateral into paired outcome tokens with a conservation invariant.

However, ERC-4626 audit findings, inflation attack mitigations, and invariant testing patterns transfer directly to our vault's security posture. This report catalogs those patterns and provides actionable recommendations.

---

## 1. ERC-4626 Standard Analysis

### 1.1 Specification Overview

ERC-4626 (EIP-4626) defines a standard API for tokenized yield-bearing vaults. The core model:
- One underlying ERC-20 asset (e.g., USDC)
- One share token (the vault itself is the ERC-20)
- Deposit assets, receive shares; redeem shares, receive assets
- Exchange rate: `totalAssets() / totalSupply()` evolves over time as yield accrues

Key functions: `deposit()`, `mint()`, `withdraw()`, `redeem()`, with preview counterparts (`previewDeposit`, etc.) and conversion functions (`convertToShares`, `convertToAssets`).

Source: [EIP-4626 Specification](https://eips.ethereum.org/EIPS/eip-4626)

### 1.2 Why ERC-4626 Does NOT Fit Our Vault

| ERC-4626 Assumption | Our Vault Reality | Conflict |
|---------------------|-------------------|----------|
| Single share token | Two tokens (LONG + SHORT) per strike | Fundamental mismatch |
| Yield-bearing (exchange rate grows) | No yield; payoff is zero-sum redistribution | Wrong mental model |
| `totalAssets()` reflects vault holdings + yield | `totalAssets()` is always exactly `totalDeposits` | No exchange rate movement |
| `convertToShares(assets)` is meaningful | 1 USDC always produces 1 LONG + 1 SHORT | Conversion is trivial |
| Redemption returns proportional assets | LONG and SHORT redeem for different amounts based on HWM | Asymmetric payoff |
| Single redemption path | Three paths: redeemPair (risk-free), redeemLong, redeemShort | Multiple exit modes |

**Verdict:** Forcing our design into ERC-4626 would require either (a) ignoring one of the two tokens, or (b) creating two separate ERC-4626 vaults that share collateral -- both approaches introduce more complexity than they solve.

### 1.3 What Does Transfer from ERC-4626

Despite not using the standard, several ERC-4626 patterns are directly applicable:

1. **Rounding discipline**: Always round *against* the user (up on deposits, down on withdrawals). Our `computePayoff` must round LONG down and SHORT down, with any dust retained by the vault.
2. **Preview functions**: Exposing `getLongValue()` and `getShortValue()` as view functions mirrors ERC-4626's preview pattern and enables integrators to check payoffs before transacting.
3. **Approval-based burn**: Our LONG/SHORT tokens require approval before the vault can burn them on redemption, analogous to ERC-4626's share redemption flow.

### 1.4 ERC-4626 Alliance

The [ERC4626 Alliance](https://github.com/ERC4626-Alliance) maintains:

- **[ERC4626-Contracts](https://github.com/ERC4626-Alliance/ERC4626-Contracts)**: Router contracts for multicall-style vault interactions. The `ERC4626RouterBase` enables atomic multi-step vault operations. *Relevance to us*: The router pattern could inspire a multicall wrapper for mint + immediate LONG sale on a CFMM.
- **[erc4626.info](https://erc4626.info/)**: Resource hub with security advisories, live vault directory, and testing resources.
- **xERC4626**: Time-weighted reward distribution extension. Not relevant to our design.

### 1.5 Known Vulnerabilities and Attack Vectors

#### Inflation Attack (First-Depositor Attack)

**Mechanism**: Attacker deposits 1 wei, then donates a large amount directly to the vault. The exchange rate inflates so subsequent depositors receive 0 shares due to rounding.

**OpenZeppelin mitigation** (since v4.9): Virtual shares and virtual assets with a configurable decimal offset. The `_decimalsOffset()` function adds precision to the share representation, making the attack unprofitable.

Source: [OpenZeppelin: A Novel Defense Against ERC4626 Inflation Attacks](https://www.openzeppelin.com/news/a-novel-defense-against-erc4626-inflation-attacks)

**Relevance to our vault**: We are NOT vulnerable to this specific attack because we do not have an exchange rate. 1 USDC always mints exactly 1 LONG + 1 SHORT. There is no shares-to-assets ratio to inflate. However, the *principle* of virtual offsets for rounding protection is relevant to our payoff computation (see Section 4).

#### Donation Attack

**Mechanism**: Attacker sends tokens directly to the vault (not through `deposit()`), inflating `totalAssets()` without minting shares.

**Relevance to our vault**: If someone sends USDC directly to our vault contract, `totalDeposits` is unaffected (it tracks minted amounts, not balances). The invariant `USDC.balanceOf(vault) >= totalDeposits` would become `>` instead of `==`, which is safe -- the excess is unclaimable. We should NOT use `balanceOf` for payoff calculations; always use `totalDeposits` per strike.

#### Rounding Exploits

**Mechanism**: Repeated deposit/withdraw cycles that exploit rounding in the user's favor to drain the vault.

Source: [a16z ERC4626 Property Tests](https://github.com/a16z/erc4626-tests)

**Relevance**: Our `redeemLong` and `redeemShort` compute `payout = tokenAmount * longValuePerToken / WAD`. The division must round DOWN (toward zero) to prevent draining. Solady's `mulDiv` (not `mulDivUp`) is the correct choice here.

---

## 2. ERC-4626 Extensions and Alternatives

### 2.1 ERC-7540: Asynchronous Vaults

Source: [EIP-7540](https://eips.ethereum.org/EIPS/eip-7540)

Extends ERC-4626 with `requestDeposit()` / `requestRedeem()` for vaults where settlement is not atomic (e.g., RWA vaults with T+2 settlement).

**Relevance**: Not directly applicable. Our vault settles atomically. However, if we ever add a time-locked redemption window (e.g., allowing redemptions only after HWM cooldown), ERC-7540's request lifecycle pattern (Pending -> Claimable -> Claimed) would be a reference model.

### 2.2 ERC-7575: Multi-Asset Vaults

Source: [EIP-7575 via Centrifuge](https://docs.centrifuge.io/developer/protocol/architecture/vaults/)

Externalizes the ERC-20 share token from the ERC-4626 vault, enabling multiple assets to map to the same share or multiple shares to map to one vault.

**Relevance**: Closer to our architecture than vanilla ERC-4626 -- we have externalized LONG/SHORT tokens. But ERC-7575 still assumes a single-share-per-vault paradigm, just with external token contracts. It does not model paired tokens with opposing payoffs.

### 2.3 ERC-6909: Minimal Multi-Token Interface

Source: [EIP-6909](https://eips.ethereum.org/EIPS/eip-6909)

A gas-optimized alternative to ERC-1155 for managing multiple token IDs in a single contract. Used by Uniswap V4's PoolManager for claim tokens.

**Relevance**: An alternative to deploying separate ERC-20 contracts per (strike, side) pair. Instead of `FciLongToken` and `FciShortToken` as separate contracts, we could use ERC-6909 where each `(strikeIndex, side)` maps to a token ID. **Trade-off**: ERC-6909 tokens are not standard ERC-20s and cannot be directly listed on existing DEXs or used with ERC-20-native protocols. Since our design spec requires "standard ERC-20s" for CFMM composability, ERC-6909 is not suitable unless we add ERC-20 wrapper contracts (which negates the gas savings).

### 2.4 No ERC for Binary Options or Structured Products

There is no ratified ERC specifically for binary option vaults, paired-token minting, or structured product tokenization. The closest existing patterns are:
- Gnosis Conditional Tokens Framework (ERC-1155 based, see Section 3.1)
- Custom vault contracts (Ribbon, Opyn, etc.)

---

## 3. Structured Product Vaults in the Wild

### 3.1 Gnosis Conditional Tokens Framework / Polymarket (MOST RELEVANT)

**Repos**:
- [gnosis/conditional-tokens-contracts](https://github.com/gnosis/conditional-tokens-contracts)
- [Polymarket/ctf-exchange](https://github.com/Polymarket/ctf-exchange)
- [Polymarket/neg-risk-ctf-adapter](https://github.com/Polymarket/neg-risk-ctf-adapter)

**Architecture**: The Conditional Tokens Framework (CTF) is the closest architectural precedent to our vault:

| CTF Property | Our Vault Equivalent |
|-------------|---------------------|
| Split: lock collateral, mint YES + NO tokens | `mint()`: lock USDC, mint LONG + SHORT |
| Merge: burn YES + NO, unlock collateral | `redeemPair()`: burn LONG + SHORT, return USDC |
| 1 YES + 1 NO = 1 collateral unit (always) | 1 LONG + 1 SHORT = 1 USDC (always) |
| Resolution by oracle | HWM/payoff determines value split |
| ERC-1155 token IDs | ERC-20 separate contracts (for CFMM composability) |

**Key differences**:
- CTF resolves to binary outcome (0 or 1). Our payoff is continuous (0 to 1 via quadratic curve).
- CTF tokens are ERC-1155 (multi-token in one contract). Ours are standard ERC-20s for AMM listing.
- CTF has a single resolution event. Our HWM decays continuously -- the payoff changes over time.
- CTF uses `conditionId` + `indexSet` for position identification. We use `(pool, strikeIndex)`.

**ChainSecurity Audit Findings** (April 2024):
- Functional correctness rated HIGH
- Key finding: `approve()` return value not checked in NegRiskAdapter. Mitigation: use SafeERC20 for all token interactions.
- Observation: elliptic curve ID negation could create "all-purpose" tokens, but not exploitable within the framework.

Source: [ChainSecurity Polymarket Conditional Tokens Audit](https://old.chainsecurity.com/wp-content/uploads/2024/04/ChainSecurity_Polymarket_Conditional_Tokens_audit.pdf)

**Actionable takeaway**: Our `splitPosition` equivalent (`mint`) and `mergePosition` equivalent (`redeemPair`) should follow the CTF's pattern:
1. Transfer collateral first (CEI pattern)
2. Mint paired tokens
3. Emit event last

### 3.2 Opyn Squeeth: Power Perpetuals (RELEVANT for Payoff)

**Repos**:
- [opynfinance/squeeth-monorepo](https://github.com/opynfinance/squeeth-monorepo)
- [opynfinance/perp-vault-templates](https://github.com/opynfinance/perp-vault-templates)

**Architecture**: Squeeth implements ETH^2 -- a perpetual with quadratic payoff tracking the square of ETH price. This is the closest payoff-structure precedent to our power-squared design.

**Key mechanism**: Users deposit ETH collateral to mint `oSQTH` (WPowerPerp ERC-20). The token's value tracks ETH^2 via a funding rate mechanism. A `normalizationFactor` adjusts the debt ratio over time to account for funding payments.

**Relevance to our design**:

| Squeeth Property | Our Vault |
|-----------------|-----------|
| Payoff = ETH^2 | Payoff = ((HWM/p*)^2 - 1)^+ |
| Quadratic in underlying | Quadratic in oracle ratio |
| Funding rate adjusts value over time | HWM decay adjusts value over time |
| Collateralized minting (200% ETH) | Fully collateralized (1:1 USDC) |
| Single token (oSQTH) | Paired tokens (LONG + SHORT) |

**Key difference**: Squeeth has a single long token and uses funding to redistribute value. We split the economics into two tokens with zero-sum payoff. Our approach eliminates funding rate complexity at the cost of requiring a paired-token market.

**Security**: Audited by Trail of Bits and Akira. Insured by Sherlock.

Source: [Paradigm: Power Perpetuals](https://www.paradigm.xyz/2021/08/power-perpetuals)

### 3.3 Ribbon Finance / Aevo: Theta Vaults (CONTEXTUAL)

**Architecture**: Theta Vaults automate covered call and put selling strategies using Opyn oTokens:
1. Users deposit collateral (ETH or USDC)
2. Vault mints Opyn oTokens (ERC-20 representations of options contracts)
3. oTokens are sold via Gnosis Auction for premium
4. Premium reinvested as yield

Source: [Ribbon Finance Theta Vault Docs](https://docs.ribbon.finance/theta-vault/theta-vault)

**Relevance**: Limited. Ribbon is a yield-bearing vault that happens to use options. The vault itself is ERC-4626-compatible (single share token representing proportional claim on collateral + accrued premium). Our vault is fundamentally different -- no yield, paired tokens, oracle-driven payoff.

**Security note**: [OpenZeppelin audited Ribbon](https://blog.openzeppelin.com/ribbon-finance-audit). Key finding relevant to us: vault state transitions must be atomic and must handle the case where oracle values change between a user's preview and execution.

### 3.4 Lyra Finance / Derive: Options AMM (CONTEXTUAL)

**Repos**: [lyra-finance/lyra-vaults](https://github.com/lyra-finance/lyra-vaults) (DeltaShortStrategy.sol)

**Architecture**: Market Maker Vaults (MMVs) serve as counterparty to options traders. Uses Black-Scholes pricing on-chain. Delta hedging via Synthetix perps.

**Relevance**: Lyra's vault model is a pool-based AMM, not a paired-token mint. However, their on-chain risk calculation patterns (computing Greeks, managing exposure) inform how we might compute payoff sensitivity in view functions.

---

## 4. Vault Security Patterns

### 4.1 Inflation Attack Vectors (Our Exposure)

| Attack | ERC-4626 Vulnerable? | Our Vault Vulnerable? | Rationale |
|--------|---------------------|----------------------|-----------|
| First-depositor inflation | YES | NO | No exchange rate; 1 USDC = 1 LONG + 1 SHORT always |
| Donation attack | YES | NO* | We track `totalDeposits`, not `balanceOf`. *Excess USDC sent directly is unclaimable but harmless |
| Share price manipulation via flash loan | YES | NO | No shares, no price to manipulate |
| Rounding exploit on repeated deposit/redeem | YES | POSSIBLE | `redeemLong`/`redeemShort` divisions must round down |

### 4.2 Our Vault-Specific Attack Surface

**Oracle manipulation**: The primary attack vector. If `getDeltaPlus()` can be manipulated, HWM spikes, and LONG holders extract value from SHORT holders.

*Mitigation (already designed)*: The FCI oracle's `addTerm()` only fires on full position removal. Flash loans cannot add+remove in one block to move the index meaningfully. The cumulative `accumulatedSum` resists single-term domination.

**Rounding dust accumulation**: Over many `redeemLong`/`redeemShort` operations, rounding dust could accumulate in the vault. This is safe (vault is over-collateralized by the dust amount) but should be tested.

**Token supply desynchronization**: If a LONG or SHORT token transfer fails silently (fee-on-transfer token used as collateral, or LONG/SHORT somehow become fee-on-transfer), the `longToken.totalSupply() == shortToken.totalSupply()` invariant could break.

*Mitigation*: Use `SafeTransferLib` for all transfers. The LONG/SHORT tokens are vault-deployed standard ERC-20s with no fees. The collateral (USDC) should be validated at construction (check `decimals()`, etc.).

**Timestamp manipulation**: HWM decay depends on `block.timestamp`. Validators can manipulate timestamps by up to ~12 seconds. With a 14-day half-life, 12 seconds of manipulation is negligible (decay factor changes by ~0.000001%).

### 4.3 Invariants for Testing (Derived from ERC-4626 Audit Patterns)

These invariants are adapted from ERC-4626 property tests and CTF audit findings for our specific vault:

**Conservation invariants**:
1. `longToken.totalSupply(s) == shortToken.totalSupply(s)` for all strikes `s` -- paired mint/burn
2. `USDC.balanceOf(vault) >= sum(totalDeposits[s])` -- vault is never under-collateralized
3. `redeemPair(n)` always returns exactly `n` USDC -- risk-free unwinding
4. `redeemLong(n) + redeemShort(n) <= n` USDC -- rounding dust stays in vault (never overpay)

**Payoff invariants**:
5. `longValue + shortValue == WAD` for all HWM, strike combinations -- zero-sum
6. `longValue == 0` when `HWM <= strike` -- no payout below strike
7. `longValue` is monotonically non-decreasing in HWM
8. `longValue <= WAD` -- capped at 1 USDC per token

**HWM invariants**:
9. `applyDecay(h, t) <= h.maxPrice` for all `t > h.lastUpdate` -- decay never increases
10. `updateHWM` idempotent within same block
11. HWM monotonically non-increasing between oracle spikes (no new highs)

**Round-trip invariants** (adapted from a16z/erc4626-tests):
12. `mint(n); redeemPair(n)` returns exactly `n` USDC -- no profit, no loss
13. `mint(n); redeemLong(n) + redeemShort(n) <= n` USDC -- no free value creation

---

## 5. Vault Libraries and Tooling

### 5.1 Library Comparison

| Library | Inflation Mitigation | Rounding | Gas | Notes |
|---------|---------------------|----------|-----|-------|
| **OpenZeppelin ERC4626** | Virtual shares + decimal offset (since v4.9) | Configurable `Math.Rounding` parameter | Moderate | Most battle-tested; overkill for our use case |
| **Solmate ERC4626** | None built-in | Rounds up in `previewMint`/`previewWithdraw` | Low | Minimal, no virtual share protection |
| **Solady ERC4626** | Derived from OZ/Solmate | Uses `FixedPointMathLib.fullMulDiv` | Lowest | Gas-optimized; we already depend on Solady for `FixedPointMathLib` |

Source: [Solady ERC4626](https://github.com/Vectorized/solady/blob/main/src/tokens/ERC4626.sol), [Solmate ERC4626](https://github.com/transmissions11/solmate/blob/main/src/tokens/ERC4626.sol), [OpenZeppelin ERC4626](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/extensions/ERC4626.sol)

**Recommendation for our vault**: Do NOT inherit from any ERC-4626 implementation. Instead:
- Use **Solmate's `ERC20`** for the LONG/SHORT token contracts (already in the plan)
- Use **Solady's `FixedPointMathLib`** for all fixed-point arithmetic (already in the plan)
- Use **Solady's `SafeTransferLib`** for USDC transfers
- Write a custom vault contract that implements the CTF-inspired split/merge pattern

### 5.2 Testing Tooling

**[a16z/erc4626-tests](https://github.com/a16z/erc4626-tests)**: Property-based tests for ERC-4626 conformance. Not directly usable (we are not ERC-4626), but the testing *methodology* is exemplary:
- Round-trip tests: deposit then withdraw should not create or destroy value
- Preview accuracy: preview functions must not over-estimate returns
- Monotonicity: more assets deposited should yield more shares (analogous: higher HWM should yield higher LONG value)

**[Recon-Fuzz/vaults-fuzzing-example](https://github.com/Recon-Fuzz/vaults-fuzzing-example)**: Foundry invariant testing with handler pattern for ERC-4626 vaults. Demonstrates ghost variable tracking across stateful fuzz runs.

**[horsefacts/weth-invariant-testing](https://github.com/horsefacts/weth-invariant-testing)**: Clean example of Foundry invariant tests with `vm.prank` for multi-actor fuzzing. Directly applicable to our vault testing (multiple depositors at different strikes).

**[Recon-Fuzz/ERC4626Tester](https://github.com/Recon-Fuzz/ERC4626Tester)**: ERC4626 mock with functions to register yield and losses. Not directly applicable but demonstrates how to mock oracle-like value changes in fuzz tests.

**Recommendation**: Write a `FciTokenVaultHandler` for Foundry invariant testing that:
1. Tracks ghost variables: `ghost_totalMinted[strike]`, `ghost_totalRedeemed[strike]`
2. Uses `vm.prank` with bounded actor addresses to simulate multi-user scenarios
3. Mocks oracle values via `vm.mockCall` to simulate HWM spikes during fuzz runs
4. Asserts all 13 invariants listed in Section 4.3 after every handler call

### 5.3 Solady Utilities Already in Use

Our project already depends on Solady for `FixedPointMathLib`. Relevant functions for the vault:

- `mulDiv(x, y, d)`: Full-precision `(x * y) / d` without overflow. Used for payoff computation.
- `mulDivUp(x, y, d)`: Same but rounds up. Use for deposit-side calculations if needed.
- `expWad(x)`: Exponential function in WAD scale. Used for HWM decay: `e^(-lambda * elapsed)`.
- `lnWad(x)`: Natural log in WAD scale. Could be used for alternative decay parameterizations.

---

## 6. Specific Relevance to Our Design

### 6.1 Architectural Classification

Our vault is a **collateral-locked paired-token factory** with **oracle-driven continuous payoff**. It is:

- NOT a yield-bearing vault (no ERC-4626)
- NOT a prediction market (no binary resolution)
- NOT a perpetual (no funding rate)
- CLOSEST to a **perpetual binary option with continuous settlement** where the "option" is on an oracle-derived index

The closest existing pattern is the CTF split/merge with:
- Continuous payoff instead of binary resolution
- Power-squared payoff function instead of 0/1
- Decaying HWM instead of fixed expiry
- ERC-20 output instead of ERC-1155

### 6.2 Conservation Invariant: The Foundation

The invariant `1 LONG + 1 SHORT = 1 USDC` is the single most important property of the vault. It:
- Ensures the vault is always fully collateralized
- Enables risk-free arbitrage (anyone can mint paired tokens and sell one side)
- Makes `redeemPair` a guaranteed exit regardless of oracle state
- Mirrors the CTF's `splitPosition`/`mergePosition` conservation

This invariant must hold for ALL oracle values, ALL HWM states, and ALL rounding scenarios.

### 6.3 Payoff Function and Power Perpetuals

Our payoff `((HWM/p*)^2 - 1)^+` is a capped power-squared function. Compared to Squeeth's `ETH^2`:

| Property | Squeeth | Our LONG Payoff |
|----------|---------|-----------------|
| Power | 2 (quadratic) | 2 (quadratic) |
| Underlying | ETH price | FCI oracle ratio |
| Range | [0, infinity) | [0, 1] (capped) |
| Funding | Continuous funding rate | HWM decay (implicit funding) |
| Collateral | 200% ETH | 100% USDC (paired) |

The HWM decay acts as an implicit funding mechanism: as time passes without new concentration spikes, the decaying HWM reduces LONG value and increases SHORT value, transferring value from LONG holders to SHORT holders. This is economically similar to Squeeth's funding rate but implemented via deterministic decay rather than market-driven premium.

### 6.4 Recommendations

1. **Do NOT implement ERC-4626.** The standard creates more impedance mismatch than value. Our vault should be a custom contract with CTF-inspired mint/redeem semantics.

2. **Follow Gnosis CTF patterns for mint/redeem.** The split/merge architecture is proven at scale (Polymarket processes billions in volume). Adapt the CEI pattern: transfer collateral, then mint tokens, then emit events.

3. **Use Solady's `mulDiv` (not `mulDivUp`) for all payout calculations.** Rounding must always favor the vault to prevent drain attacks. Any dust from rounding accumulates in the vault and is unclaimable -- this is safe and correct.

4. **Implement all 13 invariants from Section 4.3 as fuzz tests.** Use the handler pattern from `horsefacts/weth-invariant-testing` with ghost variables. Target 10,000+ runs with depth 50+.

5. **Add a `donationGuard` check in view functions.** While donation attacks cannot harm our vault (we use `totalDeposits` not `balanceOf`), explicitly asserting `balanceOf >= totalDeposits` in getter functions catches any logic error that would violate solvency.

6. **Consider ERC-6909 for a future gas-optimized version.** If CFMM composability requirements change (e.g., Uniswap V4 hooks can trade ERC-6909 directly), a multi-token vault using ERC-6909 IDs instead of separate ERC-20 contracts would save significant gas on deployment and token management.

7. **Validate collateral token at construction.** Check that the collateral is a standard ERC-20 (not fee-on-transfer, not rebasing). Consider hardcoding USDC address rather than accepting arbitrary collateral.

---

## 7. Reference Implementations and Repos

### Directly Relevant

| Repository | Stars | Relevance | Key Pattern |
|-----------|-------|-----------|-------------|
| [gnosis/conditional-tokens-contracts](https://github.com/gnosis/conditional-tokens-contracts) | ~300+ | HIGH | Split/merge collateral into paired outcome tokens |
| [Polymarket/ctf-exchange](https://github.com/Polymarket/ctf-exchange) | ~200+ | HIGH | CTF exchange with atomic swaps between outcome tokens and collateral |
| [opynfinance/squeeth-monorepo](https://github.com/opynfinance/squeeth-monorepo) | ~200+ | MEDIUM | Power-squared payoff, WPowerPerp ERC-20, Controller pattern |
| [a16z/erc4626-tests](https://github.com/a16z/erc4626-tests) | ~200+ | HIGH (testing) | Property-based vault testing methodology |

### Libraries in Use

| Repository | Relevance | What We Use |
|-----------|-----------|-------------|
| [Vectorized/solady](https://github.com/Vectorized/solady) | CRITICAL | `FixedPointMathLib` (mulDiv, expWad), `SafeTransferLib` |
| [transmissions11/solmate](https://github.com/transmissions11/solmate) | HIGH | `ERC20` base for LONG/SHORT tokens |

### Testing References

| Repository | Relevance | Key Pattern |
|-----------|-----------|-------------|
| [Recon-Fuzz/vaults-fuzzing-example](https://github.com/Recon-Fuzz/vaults-fuzzing-example) | HIGH | Handler-pattern invariant testing for vaults |
| [horsefacts/weth-invariant-testing](https://github.com/horsefacts/weth-invariant-testing) | HIGH | Multi-actor invariant testing with vm.prank |
| [Recon-Fuzz/ERC4626Tester](https://github.com/Recon-Fuzz/ERC4626Tester) | MEDIUM | Oracle value mocking in fuzz tests |

### Contextual / Background

| Repository | Relevance | Key Insight |
|-----------|-----------|-------------|
| [ERC4626-Alliance/ERC4626-Contracts](https://github.com/ERC4626-Alliance/ERC4626-Contracts) | LOW | Router pattern for multicall vault interactions |
| [Polymarket/neg-risk-ctf-adapter](https://github.com/Polymarket/neg-risk-ctf-adapter) | MEDIUM | Adapter pattern for wrapping CTF with risk transformations |
| [opynfinance/perp-vault-templates](https://github.com/opynfinance/perp-vault-templates) | LOW | Perpetual vault strategy templates |

---

## 8. Standards and Specifications Referenced

| Standard | Status | Relevance |
|----------|--------|-----------|
| [EIP-4626](https://eips.ethereum.org/EIPS/eip-4626) | Final | NOT applicable (yield-bearing single-share vault) |
| [EIP-7540](https://eips.ethereum.org/EIPS/eip-7540) | Draft | NOT applicable (async settlement; ours is atomic) |
| [EIP-7575](https://eips.ethereum.org/EIPS/eip-7575) | Draft | Partially relevant (externalized share tokens) |
| [EIP-6909](https://eips.ethereum.org/EIPS/eip-6909) | Final | Future consideration (multi-token in single contract) |
| [EIP-7535](https://eips.ethereum.org/EIPS/eip-7535) | Draft | NOT applicable (native asset vaults) |

---

## 9. Audit and Security References

| Source | Key Finding | Relevance |
|--------|------------|-----------|
| [OpenZeppelin: ERC4626 Inflation Defense](https://www.openzeppelin.com/news/a-novel-defense-against-erc4626-inflation-attacks) | Virtual shares + decimal offset | Pattern for rounding protection |
| [OpenZeppelin: ERC4626 Exchange Rate Manipulation](https://www.openzeppelin.com/news/erc-4626-tokens-in-defi-exchange-rate-manipulation-risks) | External integration risks | Preview function accuracy |
| [ChainSecurity: Polymarket CTF Audit](https://old.chainsecurity.com/wp-content/uploads/2024/04/ChainSecurity_Polymarket_Conditional_Tokens_audit.pdf) | High functional correctness; approve return value check | Use SafeTransferLib; validate collateral token |
| [OpenZeppelin: Ribbon Finance Audit](https://blog.openzeppelin.com/ribbon-finance-audit) | Oracle timing between preview and execution | Poke-before-redeem pattern |
| [OZ GitHub Issue #3706](https://github.com/OpenZeppelin/openzeppelin-contracts/issues/3706) | Community discussion on inflation mitigations | Dead shares, virtual offsets, router-based slippage checks |
| [ERC-4626 Security (4626 Alliance)](https://erc4626.info/security/) | Comprehensive vulnerability catalog | First-depositor, reentrancy, fee-on-transfer, oracle manipulation, rounding drift |

---

## 10. Conclusion and Next Steps

### Architecture Decision: Custom Vault (NOT ERC-4626)

The FCI Token Vault should be implemented as a **custom collateral-locked paired-token factory**, drawing architectural patterns from the Gnosis Conditional Tokens Framework and security patterns from ERC-4626 audit findings.

### Implementation Priorities

1. **Conservation invariant first**: The `1 LONG + 1 SHORT = 1 USDC` property must be proven via fuzz testing before any other feature is built.
2. **Rounding discipline**: All payout divisions round DOWN (use `mulDiv`, never `mulDivUp`). Test that repeated single-token redemptions never drain more than `totalDeposits`.
3. **Oracle isolation**: The vault must be read-only with respect to the oracle. `poke()` reads but never writes to the oracle. Test that `poke()` reverts gracefully if the oracle reverts.
4. **Handler-pattern invariant tests**: Build a `FciTokenVaultHandler` with ghost variables for stateful fuzz testing, targeting all 13 invariants.

### What NOT to Build

- Do NOT wrap the vault in ERC-4626 compatibility. It adds complexity and misleads integrators about the vault's semantics.
- Do NOT use ERC-1155 for tokens. ERC-20 composability with existing CFMMs is a hard requirement.
- Do NOT add a funding rate mechanism. The HWM decay provides implicit funding without the complexity of Squeeth's normalization factor.
