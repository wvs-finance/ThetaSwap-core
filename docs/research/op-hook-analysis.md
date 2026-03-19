# op-hook Architectural Analysis

**Date:** 2026-03-12
**Branch:** 004-fci-token-vault
**Source:** https://github.com/lababidi/op-hook

---

## 1. What op-hook Does

op-hook (branded "OpSwap") is an American-style options market deployed on Unichain. It uses a Uniswap V4 hook to replace the standard AMM swap path with a Black-Scholes pricing engine. When a user swaps through the pool, they are not trading against a constant-product curve — they are buying or selling fully-collateralized option tokens at a price computed on-chain from the Black-Scholes formula.

The collateral model is GreekFi-style: every option token minted is backed 1:1 by the underlying asset (WETH). The hook is the minter/burner of those tokens, so there is no separate option writer or counterparty.

---

## 2. Core Mechanism

### Hook-as-AMM via `beforeSwapReturnDelta`

Yes, op-hook is a hook-as-AMM. `getHookPermissions()` enables `beforeSwap: true` and `beforeSwapReturnDelta: true` and explicitly blocks all liquidity operations (`beforeAddLiquidity` reverts, `beforeDonate` reverts). There is no V4 AMM curve in use; the pool exists only as a routing surface.

The swap flow in `_beforeSwap`:

1. Reads `amountSpecified` from `SwapParams` (always negative, exact-input).
2. Determines direction: cash-for-option or option-for-cash.
3. Calls the internal Black-Scholes pricer to compute the exchange rate and output amount.
4. Uses V4 flash accounting: `poolManager.take` + `poolManager.sync` + mint/burn of option tokens + `poolManager.settle`.
5. Returns a `BeforeSwapDelta` that fully absorbs the swap so V4 does no further routing.

This is the same structural pattern as EulerSwap and Saucepoint's Constant Sum Swap.

### Pricing

`OptionPrice.sol` is a pure Solidity Black-Scholes implementation (d1/d2 via fixed-point ln, normCDF approximation, exp). Inputs: underlying spot from a Uniswap V3 pool via `slot0().sqrtPriceX96`; strike and expiration stored per option token at deploy time; volatility and risk-free rate hardcoded. V3 spot prices are not TWAPs — acknowledged as a prototype limitation.

---

## 3. Token Minting and Burning

The option token is an ERC-20 (`IOptionToken extends IERC20`). The hook calls `option.mint(amount)` JIT at swap time and `option.redeem(amount)` on the reverse path. The hook is the sole authorized minter; there is no permissionless LP.

- **Cash → Option:** hook mints options JIT, transfers them to PoolManager, pulls cash from PoolManager into itself.
- **Option → Cash:** hook takes options from PoolManager, transfers cash out to PoolManager, burns options via `redeem`.

Collateralization is enforced by the external GreekFi `IOptionToken` contract, which holds the WETH backing.

---

## 4. Vault Standard Used

| Contract | Standard | Role |
|---|---|---|
| `OptionPoolVault.sol` | ERC-4626 | LP deposit/withdraw scaffold for the USDC cash reserve |
| `OptionPool.sol` | Bespoke (cell-based) | Internal liquidity tracking with per-cell fee/credit/debt growth accumulators |

`OptionPoolVault` has lifecycle hooks (`_afterDeposit`, `_afterWithdraw`, etc.) left as virtual stubs — the integration with `OpHook` is incomplete. `OptionPool.sol` is an exploratory LP accounting design using a 64-cell bitmask model with `feeGrowthX128`, `creditGrowthX128`, and `debtGrowthX128` per cell; it is not referenced by `OpHook.sol`. In the deployed system the hook holds WETH directly and relies on the external GreekFi contract.

---

## 5. Architectural Comparison: op-hook vs. Paired LONG/SHORT Token Vault with FCI Oracle

| Dimension | op-hook | LONG/SHORT Vault + FCI Oracle |
|---|---|---|
| **Primary mechanism** | Hook-as-AMM: `beforeSwapReturnDelta` intercepts 100% of swaps, Black-Scholes prices the exchange | Hook-as-vault: swap triggers minting/burning of directional tokens whose value tracks LP IL exposure |
| **Price oracle** | Uniswap V3 spot (`sqrtPriceX96`) for underlying; on-chain Black-Scholes for option premium | FCI measures where fees are concentrated in the V4 tick range — encodes realized market stress, not a spot price |
| **What the issued token represents** | A fully-collateralized American put or call with fixed strike and expiration | A LONG or SHORT exposure to LP-range risk; value accrues/decays based on whether the pool stays in range |
| **Collateral model** | 1:1 WETH backing via GreekFi, held externally; hook is the sole minter | LP positions are the implicit collateral; the vault redistributes IL between LONG and SHORT holders |
| **Token standard** | ERC-20 option tokens (fungible per strike/expiration/type); ERC-4626 vault stub present but disconnected | Paired ERC-20 LONG/SHORT tokens with a custom CTF-inspired vault managing the reserve split |
| **Expiration / settlement** | Hard expiration enforced on-chain; OTM options expire worthless | No expiration — exposure is continuous; redeemed when LP removes liquidity |
| **Oracle manipulation surface** | High: spot V3 `slot0` is manipulable in a single block; volatility/rate are hardcoded | FCI is a historical fee-growth accumulator — harder to manipulate in a single block, but requires trust in V4 fee accounting integrity |
| **Liquidity model** | No LPs. Hook holds a unilateral cash reserve. Adding liquidity is permanently blocked. | LPs are the natural capital providers; the vault aligns LP incentives rather than replacing them |
| **Hook permissions** | `beforeSwap`, `beforeSwapReturnDelta`, `beforeAddLiquidity` (revert), `beforeDonate` (revert) | `afterAddLiquidity`, `afterRemoveLiquidity`, `beforeSwap` or `afterSwap` for FCI updates; does not need to intercept swap output |
| **Complexity / auditability** | High: on-chain Black-Scholes is a significant numerical surface; V3 spot feed is a known attack vector | Moderate: FCI accumulator math is simpler than Black-Scholes; risk surface is in index calibration and vault share accounting |
| **Deployed status** | Live on Unichain Mainnet (unaudited) | Research / development phase (branch 004) |

### Key Architectural Divergence

op-hook converts Uniswap V4 into a **derivatives exchange**. The hook is both the market-maker and the sole counterparty; it issues expiring claims against an external collateral pool. The FCI token vault design instead uses Uniswap V4 as the **underlying risk source**: the hook observes how fees concentrate across ticks (the FCI signal) and uses that to price and rebalance paired directional tokens that represent long/short exposure to LP range risk. The two projects share the `beforeSwapReturnDelta` structural pattern but apply it to fundamentally different financial primitives.

---

## Sources

- [lababidi/op-hook GitHub repository](https://github.com/lababidi/op-hook)
- `packages/foundry/contracts/OpHook.sol`
- `packages/foundry/contracts/IOptionToken.sol`
- `packages/foundry/contracts/OptionPoolVault.sol`
- `packages/foundry/contracts/OptionPool.sol`
- `packages/foundry/contracts/OptionPrice.sol`
