# Unichain Sepolia Deployment + Differential FCI Testing

**Date**: 2026-03-09
**Branch**: 003-reactive-integration
**Status**: Approved

## Goal

Differential testing of FCI deltaPlus computation across two parallel paths:

- **V4 / Unichain Sepolia**: FCI deployed as a direct V4 hook. Local computation via afterAddLiquidity/afterSwap/afterRemoveLiquidity callbacks.
- **V3 / Eth Sepolia**: Reactive adapter hears V3 Mint/Burn/Swap events on-chain. Reactive Network computes FCI via callback.

Same mock tokens, same pool parameters, same HD-derived accounts, same builder scenarios (equilibrium, mild, crowdout). Both paths must yield identical deltaPlus.

## Architecture

### Script Pipeline

```
script/deploy/
  DeployMockTokens.s.sol        -- 2 MockERC20s, mint 1M to deployer (chain-agnostic)
  FundAccounts.s.sol             -- transfer tokens + approve to PosMgr/Pool (chain-agnostic)
  DeployFCIHookV4.s.sol          -- HookMiner salt search + deploy FCI as V4 hook
  DeployReactiveAdapterV3.s.sol  -- deploy FCI + reactive adapter for V3
  CreatePoolV4.s.sol             -- PoolManager.initialize() with mock tokens + FCI hook
  CreatePoolV3.s.sol             -- deploy V3 mock pool with factory
```

### Execution Order

**Unichain Sepolia (V4):**

```bash
forge script DeployMockTokens        --broadcast --rpc-url unichain_sepolia
# update Deployments.sol with token addresses
forge script DeployFCIHookV4         --broadcast --rpc-url unichain_sepolia
# update Deployments.sol with FCI hook address
forge script CreatePoolV4            --broadcast --rpc-url unichain_sepolia
forge script FundAccounts            --broadcast --rpc-url unichain_sepolia
```

**Eth Sepolia (V3):**

```bash
forge script DeployMockTokens        --broadcast --rpc-url sepolia
# update Deployments.sol with token addresses
forge script DeployReactiveAdapterV3 --broadcast --rpc-url sepolia
# update Deployments.sol with adapter + FCI addresses
forge script CreatePoolV3            --broadcast --rpc-url sepolia
forge script FundAccounts            --broadcast --rpc-url sepolia
```

### State Management

All deployed addresses hardcoded in `script/utils/Deployments.sol`. No env vars for contract addresses. After each deploy script:

1. Script logs address via console2.log
2. Developer updates Deployments.sol with the real address
3. Commit
4. Next script reads from Deployments.sol via resolver functions

### Deployments.sol Structure

```
Chain IDs: SEPOLIA (11155111), UNICHAIN_SEPOLIA (1301)

Per-chain resolvers:
  resolveTokens(chainId)       -> (tokenA, tokenB)
  resolveDeployments(chainId)  -> Deployments struct (posMgr, poolMgr, swapRouter, fci)
  resolveV3(chainId)           -> (pool, adapter, fci)

Per-chain address functions:
  Tokens:     unichainSepoliaTokenA/B(), sepoliaTokenA/B()
  V4 infra:   unichainSepoliaPoolManager/PositionManager/SwapRouter/FCIHook()
  V3 infra:   sepoliaV3Pool/Adapter/FCI()
```

## Script Details

### DeployMockTokens.s.sol

- Uses solmate's MockERC20 (already in dependencies)
- Deploys 2 tokens: "ThetaSwap Token A" (TSA), "ThetaSwap Token B" (TSB), 18 decimals
- Mints 1M supply to deployer wallet (HD index 0)
- Logs currency ordering for PoolKey (currency0 < currency1)

### DeployFCIHookV4.s.sol

- Uses HookMiner from v4-periphery to find CREATE2 salt
- Hook flags: AFTER_ADD_LIQUIDITY | AFTER_SWAP | AFTER_REMOVE_LIQUIDITY
- Constructor arg: PoolManager address
- Post-deploy assertion verifies mined address matches

### CreatePoolV4.s.sol

- Reads token addresses + FCI hook from Deployments.sol
- Sorts tokens for currency0 < currency1
- PoolKey: fee=500, tickSpacing=10 (matches Constants.sol)
- Initial price: sqrtPriceX96 for 1:1 ratio
- Calls PoolManager.initialize(key, sqrtPriceX96)

### FundAccounts.s.sol

- Transfers 100k tokens (A + B) from deployer to lpPassive, lpSophisticated, swapper
- Approves tokens to PositionManager via Permit2 (V4) or directly to V3 pool
- Chain-agnostic: detects protocol from block.chainid

### DeployReactiveAdapterV3.s.sol

- Deploys FCI contract + ReactiveHookAdapter on Eth Sepolia
- Registers V3 pool with adapter
- Deploys ThetaSwapReactive on Reactive Network (Lasna)

### CreatePoolV3.s.sol

- Creates V3 pool via factory with mock tokens
- fee=500, matching V4 pool parameters

## Differential Testing

### Orchestration: differential-test.sh

Shell script that runs the same builder recipe on both chains:

```bash
SCENARIO=${1:-"buildEquilibrium"}

# V4: Unichain Sepolia (local FCI hook)
forge script FeeConcentrationIndexBuilderScript \
  --sig "$SCENARIO()" --broadcast --rpc-url unichain_sepolia

# V3: Eth Sepolia (reactive adapter)
forge script FeeConcentrationIndexBuilderScript \
  --sig "$SCENARIO()" --broadcast --rpc-url sepolia

# Wait for reactive callback
forge script ReadDeltaPlus --sig "poll()" --rpc-url sepolia

# Compare deltaPlus from both chains
forge script CompareDeltaPlus --rpc-url sepolia
```

### CompareDeltaPlus.s.sol

Read-only script that:
1. Forks both chains (Unichain Sepolia + Eth Sepolia)
2. Reads deltaPlus from FCI on each
3. Asserts exact equality

### Crowdout (multi-block)

Phased invocations with block-gap waits:

```bash
differential-test.sh buildCrowdoutPhase1
sleep 15  # wait for next block on both chains
differential-test.sh buildCrowdoutPhase2
sleep 15
TOKEN_A=<id> differential-test.sh buildCrowdoutPhase3
```

## Accounts

HD-derived from MNEMONIC env var (Accounts.sol):

| Index | Role              | Purpose                          |
|-------|-------------------|----------------------------------|
| 0     | deployer          | Deploys contracts, mints tokens  |
| 1     | lpPassive         | Passive LP (stays in pool)       |
| 2     | lpSophisticated   | Sophisticated LP (exits early)   |
| 3     | swapper           | Executes swaps to generate fees  |

All accounts need ETH for gas (faucet/manual transfer before scripts).

## Key Invariant

For any recipe R executed on both chains:

```
deltaPlus_V4(R) == deltaPlus_V3_reactive(R)
```

This validates that the reactive adapter produces identical FCI state to the direct V4 hook computation.
