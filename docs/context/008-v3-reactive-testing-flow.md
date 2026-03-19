# 008 V3 Reactive FCI Testing Flow

## Pre-deployment Checklist

1. **Deployer balances**: Check Sepolia ETH + Lasna lREACT
   ```bash
   cast balance --rpc-url $SEPOLIA_RPC $DEPLOYER --ether
   cast balance --rpc-url $LASNA_RPC $DEPLOYER --ether
   ```

2. **Migrate funds from old contracts** (if upgrading):
   ```bash
   cast send $OLD_CALLBACK "migrateFunds(address)" $DEPLOYER
   cast send $OLD_REACTIVE "migrateFunds(address)" $DEPLOYER
   ```
   If only FCI changed: `callback.setFci(newFci)` — no redeploy needed.
   If only callback changed: `reactive.setCallback(newCallback)` — no redeploy needed.

## Deployment (10 steps)

1. Deploy FCI V2
2. Deploy V3 Facet
3. Deploy Callback (fund with **0.2+ SepETH** for pay() gas)
4. Deploy Reactive (fund with **10+ lREACT** for subscriptions)
5. `fci.initialize(deployer)`
6. `fci.registerProtocolFacet(0x52FF, facet)`
7. `facet.initialize(deployer, v3Pool, fci, callback)`
8. `fci.setFacetFci(0x52FF, fci)` + `fci.setFacetProtocolStateView(0x52FF, v3Pool)`
9. `facet.listen(abi.encode(v3Pool))` — registers pool, emits PoolAdded
10. `reactive.registerPool(11155111, v3Pool)` — subscribes to Swap/Mint/Burn

## Full Lifecycle Test

### Phase 1: Mint multiple LPs
```bash
# Deployer: 1e18 at [-100,100]
cast calldata "mint(address,address,int24,int24,uint128)" $POOL $DEPLOYER -100 100 1000000000000000000
# LP1: 5e18 at [-100,100] (different ratio = concentration)
cast calldata "mint(address,address,int24,int24,uint128)" $POOL $LP1 -100 100 5000000000000000000
```
Wait 30-50s for Mint callbacks to arrive.

### Phase 2: Generate fees via swaps
```bash
# zeroForOne: use MIN_SQRT_RATIO+1 = 4295128740
cast calldata "swap(address,address,bool,int256,uint160)" $POOL $DEPLOYER true -100000000000000 4295128740
# oneForZero: use MAX_SQRT_RATIO-1
cast calldata "swap(address,address,bool,int256,uint160)" $POOL $DEPLOYER false -100000000000000 $MAX_SQRT
```
Use small amounts (1e14) to avoid draining pool. Wait 30-50s for Swap callbacks.

### Phase 3: Burn (full exit triggers FCI accumulation)
```bash
# Burn deployer's FULL position
cast calldata "burn(int24,int24,uint128)" -100 100 1000000000000000000
```
**Important:** Must be a FULL burn (burnedLiq == posLiq). Partial burns are skipped by the partial-remove guard.

Wait 30-50s for Burn callback.

### Phase 4: Query FCI state
```bash
cast calldata "getDeltaPlus((address,address,uint24,int24,address),bytes2)" \
  "($TOKEN0,$TOKEN1,500,10,$FCI)" "0x52FF"

cast calldata "getIndex((address,address,uint24,int24,address),bytes2)" \
  "($TOKEN0,$TOKEN1,500,10,$FCI)" "0x52FF"
```

**Expected results:**
- `removedPosCount > 0` — burns are accumulating
- `thetaSum > 0` — FCI terms being added
- `deltaPlus > 0` — concentration detected (requires 2+ LPs with different x_k)
- With 1 LP: `deltaPlus = 0` (trivially uniform, x_k = 1)
- With deployer (1/6) + LP1 (5/6): `deltaPlus > 0` after LP1 burns

## Monitoring

### Check callback delivery
```bash
# Callback balance (decreases on each pay())
cast balance --rpc-url $SEPOLIA_RPC $CALLBACK --ether

# Proxy events for our callback
curl -s -X POST $SEPOLIA_RPC -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"fromBlock":"HEX","toBlock":"latest","address":"0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA","topics":[null,"0x000...CALLBACK_PADDED"]}]}'
```

### Check reactive balance
```bash
cast balance --rpc-url $LASNA_RPC $REACTIVE --ether
```
If 0 → callbacks stop. Fund with `cast send $REACTIVE "fund()" --value 10ether`.

### Trace callback execution
```bash
# Use cast run with Alchemy archive (requires paid tier for debug_trace)
ETH_RPC_URL=$SEPOLIA_RPC cast run $TX_HASH

# Or simulate with extracted calldata
cast call --from $PROXY --gas-limit 1000000 $CALLBACK $INNER_CALLDATA --trace
```

### Lasna Explorer
Check reactive tx processing at: https://lasna-explorer.rnk.dev/address/$REACTIVE

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| No callback events | Reactive out of lREACT | `reactive.fund{value: 10 ether}()` |
| Callback balance unchanged | Callback proxy not forwarding | Check proxy whitelist, verify rvmId matches |
| `removedPosCount` not incrementing | Partial-remove guard or posLiqBefore=0 | Check V3 position has same liq as burn amount; trace with cast run |
| `deltaPlus = 0` with 2+ LPs | Only 1 LP burned, or all LPs have same x_k | Need asymmetric burns (different liq ratios) |
| `WhitelistContract` event only | Normal — this IS the proxy success event on Sepolia testnet | |

## Key Addresses (Sepolia)

- Callback Proxy: `0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA`
- V3 Pool (fee=500): `0xF66da9dd005192ee584a253b024070c9A1A1F4FA`
- Token0: `0x3eEE766C0d9Ca7D1509e2493857449Ef65A62cF3`
- Token1: `0xdabc71B8cBBB062AC745Cc03DcEBd9C7B4d225b6`
- V3 CallbackRouter: `0x1284E9d71a87276d05abD860bD9990dce9Dd721E`
- Deployer: `0xe69228626E4800578D06a93BaaA595f6634A47C3`
- LP1 (index 1): `0xcBdAE57cd2722fB8e292A876BfC641D8C7faA887`
- Lasna RPC: `https://lasna-rpc.rnk.dev`

## Admin Operations (no-redeploy updates)

```bash
# If FCI V2 changes — update callback pointer
cast send $CALLBACK "setFci(address)" $NEW_FCI

# If callback changes — update reactive pointer
cast send $REACTIVE "setCallback(address)" $NEW_CALLBACK

# Recover funds before retiring a contract
cast send $OLD_CONTRACT "migrateFunds(address)" $DEPLOYER

# Transfer ownership
cast send $CONTRACT "transferOwnership(address)" $NEW_OWNER
```
