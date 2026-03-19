# Sepolia Mock Pool FCI Harness Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy mock ERC20 tokens and a real V3 pool on Sepolia, then run a deterministic Mint→Swap→Burn sequence via a Foundry script that produces a known nonzero FCI index — verifiable by the reactive pipeline.

**Architecture:** A Foundry script contract (`FCIOracleHarness`) implements V3 mint/swap callbacks, interacts with the real Sepolia V3 Factory + Pool contracts, and executes a fixed scenario: 2 mints, N swaps, 1 burn. The deployer runs `cast send` calls sequentially. The reactive contract (already on Lasna) subscribes to the Sepolia pool and processes the events through the ReactVM→Adapter pipeline.

**Tech Stack:** Solidity ^0.8.26, Foundry (forge build + cast send), Uniswap V3 core interfaces, forge-std MockERC20

---

## Prerequisites (manual, not in script)

Before starting, these must be done via `cast send`:

1. **Deploy MockERC20 token0** — `forge create` or `cast send --create` with MockERC20 bytecode
2. **Deploy MockERC20 token1** — same, ensure token1 address > token0 address
3. **Call `initialize(name, symbol, decimals)` on each token** — and `mint` enough supply to deployer
4. **Create V3 pool** — `cast call` the Sepolia Factory `createPool(token0, token1, 500)` → get pool address
5. **Initialize pool** — `cast send pool "initialize(uint160)" sqrtPriceX96` at tick 0 (sqrtPriceX96 = 79228162514264337593543950336 = 2^96)
6. **Unregister mainnet pool** from reactive contract: `cast send $REACTIVE "unregisterPool(uint256,address)" 1 $V3_POOL --rpc-url $REACTIVE_RPC_URL`
7. **Register Sepolia pool** on reactive contract: `cast send $REACTIVE "registerPool(uint256,address)" 11155111 $SEPOLIA_POOL --rpc-url $REACTIVE_RPC_URL`

These are one-time setup. The script below is the repeatable harness.

---

### Task 1: Create the Foundry script contract

**Files:**
- Create: `script/reactive-integration/FCIOracleHarness.s.sol`
- Create: `script/reactive-integration/MockToken.sol`

**Step 1: Write MockToken.sol**

A minimal mintable ERC20 (we need `mint` to be public, MockERC20 from forge-std has `_mint` internal).

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {MockERC20} from "forge-std/mocks/MockERC20.sol";

contract MockToken is MockERC20 {
    function init(string memory name_, string memory symbol_) external {
        initialize(name_, symbol_, 18);
    }

    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }

    function _mint(address to, uint256 amount) internal {
        totalSupply += amount;
        balanceOf[to] += amount;
        emit Transfer(address(0), to, amount);
    }
}
```

**Step 2: Write FCIOracleHarness.s.sol**

The script contract implements both V3 callbacks and has a `run()` function that:

1. Approves tokens to the pool
2. Mints position A: tickLower=-100, tickUpper=100, liquidity=1e18
3. Mints position B: tickLower=-200, tickUpper=200, liquidity=1e18
4. Executes 5 swaps alternating direction (zeroForOne true/false) with small amounts
5. Collects fees on position A (to accumulate Collect events for the reactive pipeline)
6. Burns position A (liquidity=1e18) — triggers FCI term computation on the adapter

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script, console} from "forge-std/Script.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {IUniswapV3MintCallback} from "@uniswap/v3-core/contracts/interfaces/callback/IUniswapV3MintCallback.sol";
import {IUniswapV3SwapCallback} from "@uniswap/v3-core/contracts/interfaces/callback/IUniswapV3SwapCallback.sol";

contract FCIOracleHarness is Script, IUniswapV3MintCallback, IUniswapV3SwapCallback {
    IUniswapV3Pool public pool;
    IERC20 public token0;
    IERC20 public token1;

    // V3 tick constants
    int24 constant TICK_A_LOWER = -100;
    int24 constant TICK_A_UPPER = 100;
    int24 constant TICK_B_LOWER = -200;
    int24 constant TICK_B_UPPER = 200;
    uint128 constant LIQUIDITY = 1e18;
    uint256 constant SWAP_AMOUNT = 1e15; // small swap
    uint256 constant NUM_SWAPS = 5;

    // sqrt price limits for swaps
    uint160 constant MIN_SQRT_RATIO = 4295128739;
    uint160 constant MAX_SQRT_RATIO = 1461446703485210103287273052203988822378723970342;

    function run() external {
        address poolAddr = vm.envAddress("SEPOLIA_POOL");
        pool = IUniswapV3Pool(poolAddr);
        token0 = IERC20(pool.token0());
        token1 = IERC20(pool.token1());

        vm.startBroadcast();

        // 1. Mint position A: narrow range
        console.log("Minting position A: [%d, %d]", TICK_A_LOWER, TICK_A_UPPER);
        pool.mint(msg.sender, TICK_A_LOWER, TICK_A_UPPER, LIQUIDITY, "");

        // 2. Mint position B: wide range
        console.log("Minting position B: [%d, %d]", TICK_B_LOWER, TICK_B_UPPER);
        pool.mint(msg.sender, TICK_B_LOWER, TICK_B_UPPER, LIQUIDITY, "");

        // 3. Execute swaps
        for (uint256 i = 0; i < NUM_SWAPS; i++) {
            bool zeroForOne = (i % 2 == 0);
            console.log("Swap %d: zeroForOne=%s", i, zeroForOne ? "true" : "false");
            pool.swap(
                msg.sender,
                zeroForOne,
                int256(SWAP_AMOUNT),
                zeroForOne ? MIN_SQRT_RATIO + 1 : MAX_SQRT_RATIO - 1,
                ""
            );
        }

        // 4. Collect fees on position A (generates Collect event for reactive pipeline)
        pool.collect(
            msg.sender,
            TICK_A_LOWER,
            TICK_A_UPPER,
            type(uint128).max,
            type(uint128).max
        );

        // 5. Burn position A (generates Burn event → FCI term in adapter)
        console.log("Burning position A");
        pool.burn(TICK_A_LOWER, TICK_A_UPPER, LIQUIDITY);

        // 6. Collect burned tokens
        pool.collect(
            msg.sender,
            TICK_A_LOWER,
            TICK_A_UPPER,
            type(uint128).max,
            type(uint128).max
        );

        vm.stopBroadcast();

        console.log("Done. Check adapter getIndex() after ReactVM processes events.");
    }

    // -- V3 Callbacks --

    function uniswapV3MintCallback(
        uint256 amount0Owed,
        uint256 amount1Owed,
        bytes calldata
    ) external override {
        if (amount0Owed > 0) token0.transfer(msg.sender, amount0Owed);
        if (amount1Owed > 0) token1.transfer(msg.sender, amount1Owed);
    }

    function uniswapV3SwapCallback(
        int256 amount0Delta,
        int256 amount1Delta,
        bytes calldata
    ) external override {
        if (amount0Delta > 0) token0.transfer(msg.sender, uint256(amount0Delta));
        if (amount1Delta > 0) token1.transfer(msg.sender, uint256(amount1Delta));
    }
}
```

**Step 3: Verify it compiles**

Run: `forge build --match-path "script/reactive-integration/FCIOracleHarness.s.sol"`
Expected: Success (compilation only, no deployment)

**Step 4: Commit**

```bash
git add script/reactive-integration/FCIOracleHarness.s.sol script/reactive-integration/MockToken.sol
git commit -m "feat: add FCI oracle harness script for Sepolia V3 pool"
```

---

### Task 2: Deploy mock tokens and create V3 pool on Sepolia

This task is executed via `cast send` commands (not the Foundry script).

**Step 1: Deploy MockToken0 and MockToken1**

```bash
source scripts/.env

# Build to get bytecode
forge build

# Deploy token A
TOKEN_A=$(cast send --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY" \
  --create "$(forge inspect script/reactive-integration/MockToken.sol:MockToken bytecode)" 2>&1 | grep contractAddress | awk '{print $2}')

# Deploy token B
TOKEN_B=$(cast send --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY" \
  --create "$(forge inspect script/reactive-integration/MockToken.sol:MockToken bytecode)" 2>&1 | grep contractAddress | awk '{print $2}')

# Sort: token0 < token1
# Compare addresses and assign accordingly
```

**Step 2: Initialize tokens and mint supply**

```bash
# Initialize token0
cast send "$TOKEN0" "init(string,string)" "Mock WETH" "mWETH" \
  --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY"

# Initialize token1
cast send "$TOKEN1" "init(string,string)" "Mock USDC" "mUSDC" \
  --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY"

# Mint 1000e18 of each to deployer
cast send "$TOKEN0" "mint(address,uint256)" "$DEPLOYER_ADDRESS" "1000000000000000000000" \
  --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY"

cast send "$TOKEN1" "mint(address,uint256)" "$DEPLOYER_ADDRESS" "1000000000000000000000" \
  --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY"
```

**Step 3: Create V3 pool via Factory**

```bash
FACTORY="0x0227628f3F023bb0B980b67D528571c95c6DaC1c"

cast send "$FACTORY" "createPool(address,address,uint24)(address)" \
  "$TOKEN0" "$TOKEN1" 500 \
  --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY"

# Get pool address
POOL=$(cast call "$FACTORY" "getPool(address,address,uint24)(address)" \
  "$TOKEN0" "$TOKEN1" 500 \
  --rpc-url "$SEPOLIA_RPC_URL")
```

**Step 4: Initialize pool at tick 0 (1:1 price)**

```bash
# sqrtPriceX96 for tick 0 = 2^96 = 79228162514264337593543950336
cast send "$POOL" "initialize(uint160)" "79228162514264337593543950336" \
  --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY"
```

**Step 5: Approve tokens to pool (for direct mint/swap callbacks)**

```bash
# The harness contract (deployed in Task 3) needs token approvals.
# For now, approve the pool from the deployer EOA for manual testing:
cast send "$TOKEN0" "approve(address,uint256)" "$POOL" "$(cast max-uint)" \
  --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY"

cast send "$TOKEN1" "approve(address,uint256)" "$POOL" "$(cast max-uint)" \
  --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY"
```

**Step 6: Update scripts/.env with new addresses**

Add to `scripts/.env`:
```
SEPOLIA_POOL=<pool address>
MOCK_TOKEN0=<token0 address>
MOCK_TOKEN1=<token1 address>
```

**Step 7: Commit .env.example update**

```bash
git add scripts/.env.example
git commit -m "chore: add Sepolia mock pool env vars"
```

---

### Task 3: Register Sepolia pool on reactive contract

**Step 1: Unregister mainnet pool**

```bash
source scripts/.env

cast send "$REACTIVE_ADDRESS" "unregisterPool(uint256,address)" \
  1 "$V3_POOL" \
  --rpc-url "$REACTIVE_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY"
```

**Step 2: Register Sepolia pool**

```bash
cast send "$REACTIVE_ADDRESS" "registerPool(uint256,address)" \
  11155111 "$SEPOLIA_POOL" \
  --rpc-url "$REACTIVE_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY"
```

**Step 3: Verify subscription via rnk_getSubscribers**

```bash
curl -s -X POST 'https://lasna-rpc.rnk.dev/' \
  -H 'Content-Type: application/json' \
  -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"rnk_getSubscribers\",\"params\":[\"$REACTIVE_ADDRESS\"]}" \
  | python3 -m json.tool
```

Expected: 4 subscriptions (Swap, Mint, Burn, Collect) for chain 11155111 and the Sepolia pool address.

---

### Task 4: Deploy the harness contract and run the scenario

**Step 1: Deploy FCIOracleHarness on Sepolia**

```bash
source scripts/.env

HARNESS=$(cast send --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY" \
  --create "$(forge inspect script/reactive-integration/FCIOracleHarness.s.sol:FCIOracleHarness bytecode)" \
  | grep contractAddress | awk '{print $2}')
```

**Step 2: Transfer tokens to harness**

```bash
# Transfer 100e18 of each token to the harness
cast send "$MOCK_TOKEN0" "transfer(address,uint256)" "$HARNESS" "100000000000000000000" \
  --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY"

cast send "$MOCK_TOKEN1" "transfer(address,uint256)" "$HARNESS" "100000000000000000000" \
  --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY"
```

**Step 3: Run the scenario**

Since `forge script --broadcast` may have wallet issues, execute via `cast send`:

```bash
# Call run() on the harness
SEPOLIA_POOL=$SEPOLIA_POOL cast send "$HARNESS" "run()" \
  --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY" \
  --gas-limit 3000000
```

Alternative: If `forge script` works:
```bash
SEPOLIA_POOL=$SEPOLIA_POOL forge script \
  script/reactive-integration/FCIOracleHarness.s.sol:FCIOracleHarness \
  --rpc-url "$SEPOLIA_RPC_URL" --private-key "$DEPLOYER_PRIVATE_KEY" \
  --broadcast -vvvv
```

**Step 4: Verify events emitted**

```bash
# Check last 10 blocks for pool events
LATEST=$(cast block-number --rpc-url "$SEPOLIA_RPC_URL")
FROM=$((LATEST - 9))
cast logs --from-block $FROM --to-block $LATEST \
  --address "$SEPOLIA_POOL" \
  --rpc-url "$SEPOLIA_RPC_URL"
```

Expected: Mint, Swap, Collect, Burn events from the harness execution.

---

### Task 5: Verify reactive pipeline processes events

**Step 1: Wait for ReactVM processing (poll)**

```bash
# Poll every 30s for up to 10 minutes
for i in $(seq 1 20); do
  RESULT=$(cast call "$ADAPTER_ADDRESS" \
    "getIndex((address,address,uint24,int24,address))" \
    "($MOCK_TOKEN0,$MOCK_TOKEN1,500,10,$ADAPTER_ADDRESS)" \
    --rpc-url "$SEPOLIA_RPC_URL")

  if [ "$RESULT" != "0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" ]; then
    echo "FCI index received at attempt $i!"
    echo "$RESULT"
    break
  fi
  echo "Attempt $i: still zero, waiting 30s..."
  sleep 30
done
```

**Step 2: Decode the result**

```bash
# Parse the 3 words: indexA (uint128), thetaSum (uint256), posCount (uint256)
# Use the Python harness:
source scripts/.env
PYTHONPATH=research uhi8/bin/python -c "
from research.scripts.compare_fci import parse_index_response
idx, theta, pos = parse_index_response('$RESULT')
print(f'indexA:   {idx} ({idx:#x})')
print(f'thetaSum: {theta} ({theta:#x})')
print(f'posCount: {pos}')
"
```

Expected: `indexA > 0`, `posCount == 1` (position B remains), `thetaSum > 0`.

**Step 3: Commit final env updates**

```bash
git add scripts/.env.example
git commit -m "feat: Sepolia mock pool FCI harness verified"
```
