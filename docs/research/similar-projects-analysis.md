# Similar Projects Analysis: Paired Token Vaults, Hedging Hooks, and Derivative Primitives in DeFi

Date: 2026-03-12 | Branch: `004-fci-token-vault`

---

## Executive Summary

This report surveys 12 open-source projects implementing mechanisms similar to the ThetaSwap FCI Token Vault. The search covered Uniswap V4 hook projects, derivative protocols, vault standards, and custom CFMM implementations.

**Key findings:**

1. **Cork Protocol** is the closest architectural analog -- paired DS (Depeg Swap) + CT (Cover Token) minted from locked collateral, traded via a Uniswap V4 hook AMM. Their May 2025 exploit ($12M) provides critical security lessons.

2. **UMA's Long Short Pair (LSP)** is the purest precedent for the paired-mint pattern -- ~300 lines of code, deposits collateral, mints fungible LONG + SHORT ERC-20s, settles via oracle at expiry. Closest to our vault's core mechanics.

3. **Panoptic** uses ERC-1155 to encode multi-leg options with ERC-4626 CollateralTracker vaults.

4. **The ecosystem is converging on two patterns**: (a) ERC-20 pairs for simple binary outcomes (Cork, UMA), and (b) ERC-1155/ERC-6909 for multi-asset or multi-strike positions (Panoptic, V4 native). Our ERC-6909 with `LONG=0/SHORT=1` is well-aligned with V4's native accounting.

5. **No existing project combines** an HHI/concentration oracle, lookback payoff, and paired token vault. This is novel.

---

## 1. Projects Found (12 total)

### 1.1 Cork Protocol (Depeg Insurance on V4) -- RELEVANCE: HIGH

- **Tokens:** ERC-20 per type -- DS (Depeg Swap), CT (Cover Token), LP, LV, PRO (extended ERC-4626)
- **Pattern:** Deposit RA, receive paired DS + CT. 1 DS + 1 CT = 1 RA always (conservation invariant identical to ours)
- **V4 Hook:** CorkHook extends vanilla V4; handles DS/CT trading with yield-space bonding curves
- **Settlement:** Expiry-based with rollover
- **CRITICAL:** Exploited for $12M on May 28, 2025. Missing access control in `beforeSwap` let attacker spoof deposit data via crafted hook payloads. Lessons in Section 5.

Repository: [Cork-Technology/Depeg-swap](https://github.com/Cork-Technology/Depeg-swap) | Docs: [docs.cork.tech](https://docs.cork.tech/smart-contracts/v1/overview)

### 1.2 UMA Long Short Pair (LSP) -- RELEVANCE: VERY HIGH

- **Tokens:** Two standard ERC-20s per contract (LONG + SHORT)
- **Pattern:** Deposit `collateralPerPair` USDC, receive 1 LONG + 1 SHORT. Pre-settlement: 1L + 1S = collateral. Post-settlement: split by `expiryPercentLong` from oracle.
- **Settlement:** UMA Optimistic Oracle determines price; Financial Product Library maps to payout split (pluggable payoff function)
- **No AMM built in** -- tokens trade on external markets
- **~300 lines of code** -- the purest implementation of our core pattern

Repository: [UMAprotocol/launch-lsp](https://github.com/UMAprotocol/launch-lsp) | Docs: [LongShortPair](https://contracts.docs.umaproject.org/contracts/financial-templates/long-short-pair/LongShortPair)

### 1.3 Panoptic (Perpetual Options on Uniswap) -- RELEVANCE: MEDIUM

- **Tokens:** ERC-1155 semi-fungible (up to 4-leg options in 256-bit ID) + ERC-4626 CollateralTracker vaults
- **Pattern:** Relocates Uniswap liquidity (no synthetic mint). Long = liquidity away from spot; Short = toward spot.
- **V4:** Panoptic V1.1 supports V4 via SFPM (SemiFungiblePositionManager)
- **Premium:** Streaming, oracle-free, based on realized Uniswap fees

Repository: [panoptic-labs/panoptic-v1-core](https://github.com/panoptic-labs/panoptic-v1-core) | Whitepaper: [arxiv.org/abs/2204.14232](https://arxiv.org/html/2204.14232v3)

### 1.4 Opyn Squeeth (Power Perpetuals) -- RELEVANCE: MEDIUM-HIGH (payoff shape)

- **Token:** oSQTH (ERC-20) -- tracks ETH price^2
- **Pattern:** Asymmetric -- shorts deposit ETH collateral to mint oSQTH, sell on Uniswap. Not paired-mint.
- **Collateral:** 200% recommended; liquidation if under-collateralized
- **Perpetual** with implicit funding via normalization factor
- **Payoff:** `price^2` -- closest to our `(sqrtPriceHWM/sqrtPriceStrike)^4` in sqrtPrice space

Repository: [opynfinance/squeeth-monorepo](https://github.com/opynfinance/squeeth-monorepo)

### 1.5 Smilee Finance (Decentralized Volatility Products) -- RELEVANCE: MEDIUM

- **Tokens:** Internal positions (not separately tokenized). Earn Vaults (short vol) + Impermanent Gain (long vol)
- **Pattern:** Epoch-based -- deposits/withdrawals only at boundaries. Atomic Delta Hedge per trade.
- **Insight:** IL decomposed into options and recomposed into volatility payoffs

### 1.6 GammaSwap (Perpetual Options via LP Borrowing) -- RELEVANCE: LOW-MEDIUM

- **Tokens:** gETH yield tokens (ERC-20). Overcollateralized borrowing model, up to 90% LTV.
- **Dynamic fee scaling** based on volatility -- relevant for our future CFMM

### 1.7 EulerSwap (Lending-Integrated AMM on V4) -- RELEVANCE: MEDIUM (hook patterns)

- **V4 Hooks:** `afterAddLiquidity` deposits into lending; `beforeRemoveLiquidity` settles loans; `beforeSwap` JIT-borrows shortfalls
- **Up to 50x simulated liquidity depth** for pegged pairs

### 1.8 Primitive Finance RMM-01 (Replicating Market Maker) -- RELEVANCE: HIGH (Layer 3)

- **CFMM curve IS the payoff** -- trading function replicates Black-Scholes covered call
- **Oracle-free**: payoff emerges from the curve shape itself
- **Key for Layer 3:** Shows we could embed our power-squared payoff directly into an AMM curve via V4 return deltas

Repository: [primitivefinance/rmm-core](https://github.com/primitivefinance/rmm-core)

### 1.9 Bunni V2 -- RELEVANCE: LOW (market validation)

- Largest V4 hook (90%+ of V4 volume). ERC-20 vault shares. Re-hypothecation to lending protocols.

### 1.10 Arrakis Finance -- RELEVANCE: LOW-MEDIUM

- V4 hook for dynamic fees (MEV-aware). ERC-20 vault tokens. Reference for fee hooks.

### 1.11 Angstrom (Sorella Labs) -- RELEVANCE: LOW

- Fair pricing hook (same price per block). Related to JIT extraction measurement.

### 1.12 Perennial Finance -- RELEVANCE: LOW

- Perpetual derivatives engine. Dynamic funding rates. Multi-asset vaults managed by third parties.

---

## 2. Token Standard Choices

| Project | Standard | Reason |
|---------|----------|--------|
| Cork DS/CT | ERC-20 | External AMM tradability |
| UMA LSP | ERC-20 pair | Simplicity, external composability |
| Panoptic | ERC-1155 + ERC-4626 | Multi-leg encoding in single ID |
| Squeeth | ERC-20 | Single instrument |
| Bunni/Arrakis/Charm | ERC-20 vault shares | DeFi composability standard |
| Uniswap V4 native | ERC-6909 | Gas efficiency, multi-token |

**Pattern:** External tradability demands ERC-20. Internal accounting benefits from ERC-6909/ERC-1155.

**Recommendation for us:** Keep ERC-6909 (`LONG=0, SHORT=1`) internally. Add thin ERC-20 wrapper facades for Layer 3 CFMM tradability. This matches V4's own pattern.

---

## 3. Collateral/Vault Patterns

| Pattern | Projects | Characteristics |
|---------|----------|----------------|
| **A: Conservation Paired Mint** | Cork, UMA, **Ours** | L+S=D always. No liquidation. Simplest, safest. |
| B: Overcollateralized Mint | Squeeth, GammaSwap | Liquidation risk. Active management needed. |
| C: ERC-4626 Yield Vault | Panoptic, Euler, Bunni | Single-sided. Yield accrual. |
| D: Epoch-Based | Smilee, Perennial | Boundary deposits/withdrawals. Clean settlement. |

**Our position:** Pattern A is correct. The conservation invariant is our strongest safety property.

---

## 4. Hook Integration Patterns

| Pattern | Projects | Description |
|---------|----------|-------------|
| 1: AMM Extension | Cork, Arrakis, Bunni | Hook modifies swap/liquidity behavior |
| 2: Vault Bridge | EulerSwap | Hook moves assets between pool and vault |
| **3: Oracle/Data Source** | **Our FCI Hook** | Hook computes metrics read by external contracts |
| 4: Custom Accounting | V4 return deltas | Hook bypasses native pricing for custom CFMM |

**Now:** Pattern 3 (vault reads FCI hook). **Layer 3:** Pattern 4 (custom CFMM via return deltas, RMM-inspired).

---

## 5. Cork Protocol Exploit -- Critical Security Lessons

The $12M Cork hack (May 28, 2025) is directly relevant. Key takeaways:

1. **Access control on callbacks:** Cork's `beforeSwap` could be called by anyone when PoolManager was unlocked. **Our action:** `poke()` reads from `vs.poolKey.hooks` which is set at construction -- ensure immutability.

2. **Token flow validation:** Attacker created fake pool with own hook, minted derivatives without depositing. **Our action:** `deposit()` already pulls collateral via `safeTransferFrom` BEFORE minting -- correct ordering.

3. **Market creation permissiveness:** Cork allowed arbitrary redemption assets. **Our action:** Strike grid is immutable per deployment -- safer.

4. **Reentrancy via PoolManager unlock:** **Our action:** Add reentrancy guards for any future hook integration.

---

## 6. Payoff Mechanism Comparison

| Project | Payoff Shape | Settlement | Oracle |
|---------|-------------|------------|--------|
| **Ours** | Power-squared lookback: `((p_hwm/p*)^2 - 1)^+` | Expiry | FCI hook (behavioral) |
| Cork | Binary (depeg/no-depeg) | Expiry + rollover | Price feed |
| UMA LSP | Pluggable via library | Oracle at expiry | Optimistic Oracle |
| Panoptic | Streaming fee-based | Perpetual | Oracle-free |
| Squeeth | `price^2` continuous | Perpetual funding | TWAP |
| RMM-01 | Covered call replication | Expiry (time-decaying curve) | Oracle-free (in curve) |

**Our unique combination:** Power-squared payoff + lookback HWM + conservation paired-mint + behavioral oracle. No other project combines all four.

---

## 7. Key Learnings

1. **Paired-mint conservation is battle-tested** (Cork, UMA). Our `mintPair`/`burnPair` in `FciTokenVaultMod.sol` lines 51-59 follows this proven pattern.

2. **ERC-20 wrappers needed** for external composability. ERC-6909 internal + ERC-20 facades is the V4-native pattern.

3. **Oracle manipulation resistance is critical.** Our FCI hook's cumulative HHI with exit-only updates is stronger than Cork's exploited price feed.

4. **Power payoffs need overflow protection.** Our `FixedPointMathLib.mulDiv` usage for each squaring step is correct.

5. **Custom CFMM curves can embed payoffs** (Primitive RMM). Key insight for Layer 3: embed power-squared payoff directly into AMM trading function via V4 return deltas.

6. **Epoch vs. perpetual:** Smilee's epochs simplify settlement but add friction. Our continuous-mint + expiry is a good middle ground for v1.

---

## 8. Recommendations

1. **Token standard:** ERC-6909 internal + ERC-20 facades (matches V4 pattern)
2. **Vault pattern:** Conservation-based paired mint (Pattern A) -- do not change
3. **Hook integration:** Read-only oracle (Pattern 3) now, custom CFMM (Pattern 4) for Layer 3
4. **Security:** Apply Cork exploit lessons -- immutable oracle address, collateral-before-mint, reentrancy guards
5. **Settlement:** Expiry-based for v1; track Squeeth normalization factor and Smilee epochs for v2

---

## 9. Gap Analysis -- What We Do That Nobody Else Does

| Capability | Closest Analog | How We Differ |
|-----------|---------------|--------------|
| Fee concentration oracle (HHI-based) | None | Novel |
| Power-squared lookback payoff | Squeeth (P^2) | We add lookback HWM, apply to concentration not price |
| Paired LONG/SHORT from collateral | Cork, UMA LSP | Different underlying risk (JIT crowding vs. depeg/price) |
| JIT-specific hedge instrument | None | No existing protocol offers JIT extraction insurance |
| ERC-6909 in diamond storage | Uniswap V4 | V4 uses for pool claims; we use for derivative tokens |
| Oracle from hook behavior data | Cork (price feed) | Behavioral (LP actions), not price-based |

---

## Key Files Referenced

- `src/fci-token-vault/modules/FciTokenVaultMod.sol` -- paired mint/burn implementation (lines 51-59)
- `src/fci-token-vault/modules/dependencies/ERC6909Lib.sol` -- ERC-6909 diamond storage
- `src/fci-token-vault/FciTokenVaultFacet.sol` -- facet layer with collateral transfer + token operations
- `src/fci-token-vault/interfaces/IFciTokenVault.sol` -- vault interface
- `docs/plans/2026-03-10-fci-token-vault-design.md` -- full design spec
- `docs/research/vault-standards-research.md` -- companion report on ERC-4626

---

## Sources

All sources are listed inline per project. Key references include:
- [Cork Protocol Hack Analysis (Dedaub)](https://dedaub.com/blog/the-11m-cork-protocol-hack-a-critical-lesson-in-uniswap-v4-hook-security/)
- [UMA LSP Documentation](https://contracts.docs.umaproject.org/contracts/financial-templates/long-short-pair/LongShortPair)
- [Panoptic Whitepaper](https://arxiv.org/html/2204.14232v3)
- [Primitive RMM Research](https://github.com/primitivefinance/Research)
- [Uniswap V4 ERC-6909 Guide](https://docs.uniswap.org/contracts/v4/guides/ERC-6909)
- [Uniswap V4 Custom Accounting](https://docs.uniswap.org/contracts/v4/guides/custom-accounting)
