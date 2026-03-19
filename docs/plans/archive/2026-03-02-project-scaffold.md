# Project Scaffold Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up the clean project scaffold for LiquiditySupplyModelSimplest with all dependencies, directory structure, and empty type files that compile.

**Architecture:** Clean rewrite — delete old code, install new deps, create model-independent types in src/types/ and model-dependent types in src/liquidity-supply-model-simplest/types/. Test base in test/liquidity-supply-model-simplest/base/. All Mod files use file-level free functions (SCOP: no library keyword, no inheritance).

**Tech Stack:** Solidity 0.8.26, Foundry, Uniswap V4, Kontrol, Solady, Angstrom patterns

---

### Task 1: Delete Old Code

**Files:**
- Delete: `src/jit-competition/`
- Delete: `src/fee-variance/`
- Delete: `test/jit-competition/`
- Delete: `test/fee-variance/`
- Delete: `script/fee-variance/`
- Delete: `script/jit-competition/`

**Step 1: Remove old source, test, and script directories**

```bash
rm -rf src/jit-competition src/fee-variance
rm -rf test/jit-competition test/fee-variance
rm -rf script/fee-variance script/jit-competition
```

**Step 2: Verify src/, test/, script/ are empty**

```bash
ls src/ test/ script/
```

Expected: all three directories empty (no files listed)

**Step 3: Commit**

```bash
git add -A src/ test/ script/
git commit -m "chore: delete old code for clean rewrite

Old jit-competition and fee-variance code used library keyword
and other SCOP violations. Clean rewrite from DRAFT.md."
```

---

### Task 2: Install New Dependencies

**Step 1: Install Angstrom**

```bash
cd /home/jmsbpp/apps/ThetaSwap/thetaSwap-core-dev
forge install SorellaLabs/angstrom --no-commit
```

Expected: `lib/angstrom/` created

**Step 2: Install Bunni V2**

```bash
forge install Bunniapp/bunni-v2 --no-commit
```

Expected: `lib/bunni-v2/` created

**Step 3: Install Kontrol Cheatcodes**

```bash
forge install runtimeverification/kontrol-cheatcodes --no-commit
```

Expected: `lib/kontrol-cheatcodes/` created

**Step 4: Install Solady**

```bash
forge install Vectorized/solady --no-commit
```

Expected: `lib/solady/` created

**Step 5: Update V3 Core to branch 0.8**

```bash
cd lib/v3-core && git checkout 0.8 && cd ../..
```

Expected: v3-core now on 0.8 branch

**Step 6: Update V3 Periphery to branch 0.8**

```bash
cd lib/v3-periphery && git checkout 0.8 && cd ../..
```

Expected: v3-periphery now on 0.8 branch

**Step 7: Verify all libs present**

```bash
ls lib/
```

Expected: 2025-12-panoptic angstrom bunni-v2 forge-std kontrol-cheatcodes openzeppelin-contracts solady uniswap-hooks v3-core v3-periphery v4-core v4-periphery

**Step 8: Commit**

```bash
git add lib/ .gitmodules
git commit -m "chore: install angstrom, bunni-v2, kontrol-cheatcodes, solady; update v3 to 0.8"
```

---

### Task 3: Update Remappings

**Files:**
- Modify: `remappings.txt`

**Step 1: Write updated remappings**

Replace entire contents of `remappings.txt` with:

```
forge-std/=lib/forge-std/src/
@uniswap/v4-core/=lib/uniswap-hooks/lib/v4-core/
@uniswap/v4-periphery/=lib/uniswap-hooks/lib/v4-periphery/
@uniswap/v4-hooks/=lib/uniswap-hooks/src/base/
@uniswap/v3-core/=lib/v3-core/
@uniswap/v3-periphery/=lib/v3-periphery/
@openzeppelin/contracts/=lib/uniswap-hooks/lib/openzeppelin-contracts/contracts/
permit2/=lib/uniswap-hooks/lib/v4-periphery/lib/permit2/
solmate/=lib/uniswap-hooks/lib/v4-core/lib/solmate/
@panoptic-v2/=lib/2025-12-panoptic/
@angstrom/=lib/angstrom/contracts/src/
@bunni-v2/=lib/bunni-v2/src/
kontrol-cheatcodes/=lib/kontrol-cheatcodes/src/
solady/=lib/solady/src/
```

Removed:
- `@openzeppelin/=lib/openzeppelin-contracts/` (duplicate)
- `2025-12-panoptic/` (renamed to @panoptic-v2/)

**Step 2: Verify forge resolves remappings**

```bash
forge build --sizes 2>&1 | head -5
```

Expected: no "missing remapping" errors (may have other compile errors since src/ is empty, that's fine)

**Step 3: Commit**

```bash
git add remappings.txt
git commit -m "chore: update remappings — add angstrom, bunni-v2, solady, kontrol; rename panoptic"
```

---

### Task 4: Create Directory Structure

**Step 1: Create model-independent types directory**

```bash
mkdir -p src/types
```

**Step 2: Create model-dependent directories**

```bash
mkdir -p src/liquidity-supply-model-simplest/types
mkdir -p src/liquidity-supply-model-simplest/core-cfmm
mkdir -p src/liquidity-supply-model-simplest/jit-plp
mkdir -p src/liquidity-supply-model-simplest/entry-index
```

**Step 3: Create test directories**

```bash
mkdir -p test/liquidity-supply-model-simplest/base
mkdir -p test/liquidity-supply-model-simplest/helpers
```

**Step 4: Create spec directories**

```bash
mkdir -p specs/core-cfmm
mkdir -p specs/jit-plp
mkdir -p specs/entry-index
```

**Step 5: Create script directory**

```bash
mkdir -p script/liquidity-supply-model-simplest
```

**Step 6: Add .gitkeep files so empty dirs are tracked**

```bash
touch src/liquidity-supply-model-simplest/core-cfmm/.gitkeep
touch src/liquidity-supply-model-simplest/jit-plp/.gitkeep
touch src/liquidity-supply-model-simplest/entry-index/.gitkeep
touch test/liquidity-supply-model-simplest/helpers/.gitkeep
touch specs/core-cfmm/.gitkeep
touch specs/jit-plp/.gitkeep
touch specs/entry-index/.gitkeep
touch script/liquidity-supply-model-simplest/.gitkeep
```

**Step 7: Commit**

```bash
git add src/ test/ specs/ script/
git commit -m "chore: create directory scaffold for LiquiditySupplyModelSimplest"
```

---

### Task 5: Create Model-Independent Types (src/types/)

Each type is a UDVT + companion Mod file with file-level free functions. No library keyword. No comments in files.

**Files:**
- Create: `src/types/ReserveX.sol`
- Create: `src/types/ReserveXMod.sol`
- Create: `src/types/ReserveY.sol`
- Create: `src/types/ReserveYMod.sol`
- Create: `src/types/Liquidity.sol`
- Create: `src/types/LiquidityMod.sol`
- Create: `src/types/SqrtPriceX96.sol`
- Create: `src/types/SqrtPriceX96Mod.sol`
- Create: `src/types/TickIndex.sol`
- Create: `src/types/TickIndexMod.sol`
- Create: `src/types/FeeAccumX.sol`
- Create: `src/types/FeeAccumXMod.sol`
- Create: `src/types/FeeAccumY.sol`
- Create: `src/types/FeeAccumYMod.sol`
- Create: `src/types/FeeRevenue.sol`
- Create: `src/types/FeeRevenueMod.sol`
- Create: `src/types/Capital.sol`
- Create: `src/types/CapitalMod.sol`

**Step 1: Write ReserveX.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type ReserveX is uint256;
```

**Step 2: Write ReserveXMod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {ReserveX} from "./ReserveX.sol";

function unwrap(ReserveX x) pure returns (uint256) {
    return ReserveX.unwrap(x);
}

function isZero(ReserveX x) pure returns (bool) {
    return ReserveX.unwrap(x) == 0;
}

using {unwrap, isZero} for ReserveX global;
```

**Step 3: Write ReserveY.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type ReserveY is uint256;
```

**Step 4: Write ReserveYMod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {ReserveY} from "./ReserveY.sol";

function unwrap(ReserveY y) pure returns (uint256) {
    return ReserveY.unwrap(y);
}

function isZero(ReserveY y) pure returns (bool) {
    return ReserveY.unwrap(y) == 0;
}

using {unwrap, isZero} for ReserveY global;
```

**Step 5: Write Liquidity.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type Liquidity is uint128;
```

**Step 6: Write LiquidityMod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Liquidity} from "./Liquidity.sol";

function unwrap(Liquidity l) pure returns (uint128) {
    return Liquidity.unwrap(l);
}

function isZero(Liquidity l) pure returns (bool) {
    return Liquidity.unwrap(l) == 0;
}

using {unwrap, isZero} for Liquidity global;
```

**Step 7: Write SqrtPriceX96.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type SqrtPriceX96 is uint160;
```

**Step 8: Write SqrtPriceX96Mod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {SqrtPriceX96} from "./SqrtPriceX96.sol";

uint160 constant MIN_SQRT_PRICE = 4295128739;
uint160 constant MAX_SQRT_PRICE = 1461446703485210103287273052203988822378723970342;

error SqrtPriceOutOfBounds(uint160 raw);

function fromUint160(uint160 raw) pure returns (SqrtPriceX96) {
    if (raw < MIN_SQRT_PRICE) revert SqrtPriceOutOfBounds(raw);
    if (raw > MAX_SQRT_PRICE) revert SqrtPriceOutOfBounds(raw);
    return SqrtPriceX96.wrap(raw);
}

function unwrap(SqrtPriceX96 p) pure returns (uint160) {
    return SqrtPriceX96.unwrap(p);
}

using {unwrap} for SqrtPriceX96 global;
```

**Step 9: Write TickIndex.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type TickIndex is int24;
```

**Step 10: Write TickIndexMod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {TickIndex} from "./TickIndex.sol";

int24 constant MIN_TICK = -887272;
int24 constant MAX_TICK = 887272;

error TickOutOfBounds(int24 raw);

function fromInt24(int24 raw) pure returns (TickIndex) {
    if (raw < MIN_TICK) revert TickOutOfBounds(raw);
    if (raw > MAX_TICK) revert TickOutOfBounds(raw);
    return TickIndex.wrap(raw);
}

function unwrap(TickIndex t) pure returns (int24) {
    return TickIndex.unwrap(t);
}

using {unwrap} for TickIndex global;
```

**Step 11: Write FeeAccumX.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type FeeAccumX is uint256;
```

**Step 12: Write FeeAccumXMod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FeeAccumX} from "./FeeAccumX.sol";

function unwrap(FeeAccumX f) pure returns (uint256) {
    return FeeAccumX.unwrap(f);
}

function add(FeeAccumX a, FeeAccumX b) pure returns (FeeAccumX) {
    return FeeAccumX.wrap(FeeAccumX.unwrap(a) + FeeAccumX.unwrap(b));
}

using {unwrap, add as +} for FeeAccumX global;
```

**Step 13: Write FeeAccumY.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type FeeAccumY is uint256;
```

**Step 14: Write FeeAccumYMod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FeeAccumY} from "./FeeAccumY.sol";

function unwrap(FeeAccumY f) pure returns (uint256) {
    return FeeAccumY.unwrap(f);
}

function add(FeeAccumY a, FeeAccumY b) pure returns (FeeAccumY) {
    return FeeAccumY.wrap(FeeAccumY.unwrap(a) + FeeAccumY.unwrap(b));
}

using {unwrap, add as +} for FeeAccumY global;
```

**Step 15: Write FeeRevenue.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type FeeRevenue is uint256;
```

**Step 16: Write FeeRevenueMod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FeeRevenue} from "./FeeRevenue.sol";

function unwrap(FeeRevenue f) pure returns (uint256) {
    return FeeRevenue.unwrap(f);
}

function add(FeeRevenue a, FeeRevenue b) pure returns (FeeRevenue) {
    return FeeRevenue.wrap(FeeRevenue.unwrap(a) + FeeRevenue.unwrap(b));
}

using {unwrap, add as +} for FeeRevenue global;
```

**Step 17: Write Capital.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type Capital is uint256;
```

**Step 18: Write CapitalMod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Capital} from "./Capital.sol";

function unwrap(Capital c) pure returns (uint256) {
    return Capital.unwrap(c);
}

function add(Capital a, Capital b) pure returns (Capital) {
    return Capital.wrap(Capital.unwrap(a) + Capital.unwrap(b));
}

function sub(Capital a, Capital b) pure returns (Capital) {
    return Capital.wrap(Capital.unwrap(a) - Capital.unwrap(b));
}

function eq(Capital a, Capital b) pure returns (bool) {
    return Capital.unwrap(a) == Capital.unwrap(b);
}

using {unwrap, add as +, sub as -, eq} for Capital global;
```

**Step 19: Verify all types compile**

```bash
forge build
```

Expected: compiles clean, no errors

**Step 20: Commit**

```bash
git add src/types/
git commit -m "feat: add model-independent CFMM types (SCOP, no library keyword)"
```

---

### Task 6: Create Model-Dependent Types (src/liquidity-supply-model-simplest/types/)

**Files:**
- Create: `src/liquidity-supply-model-simplest/types/FeeRate.sol`
- Create: `src/liquidity-supply-model-simplest/types/FeeRateMod.sol`
- Create: `src/liquidity-supply-model-simplest/types/EntryCount.sol`
- Create: `src/liquidity-supply-model-simplest/types/EntryCountMod.sol`
- Create: `src/liquidity-supply-model-simplest/types/IndexValue.sol`
- Create: `src/liquidity-supply-model-simplest/types/IndexValueMod.sol`
- Create: `src/liquidity-supply-model-simplest/types/SwapVolume.sol`
- Create: `src/liquidity-supply-model-simplest/types/SwapVolumeMod.sol`
- Create: `src/liquidity-supply-model-simplest/types/FixedMarketPrice.sol`
- Create: `src/liquidity-supply-model-simplest/types/FixedMarketPriceMod.sol`
- Create: `src/liquidity-supply-model-simplest/types/SimulationConfig.sol`

**Step 1: Write FeeRate.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type FeeRate is uint24;
```

**Step 2: Write FeeRateMod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FeeRate} from "./FeeRate.sol";

uint24 constant MAX_FEE = 1000000;

error FeeAboveMax(uint24 raw);

function fromUint24(uint24 raw) pure returns (FeeRate) {
    if (raw > MAX_FEE) revert FeeAboveMax(raw);
    return FeeRate.wrap(raw);
}

function unwrap(FeeRate f) pure returns (uint24) {
    return FeeRate.unwrap(f);
}

using {unwrap} for FeeRate global;
```

**Step 3: Write EntryCount.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type EntryCount is uint256;
```

**Step 4: Write EntryCountMod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {EntryCount} from "./EntryCount.sol";

function unwrap(EntryCount n) pure returns (uint256) {
    return EntryCount.unwrap(n);
}

function increment(EntryCount n) pure returns (EntryCount) {
    return EntryCount.wrap(EntryCount.unwrap(n) + 1);
}

function isZero(EntryCount n) pure returns (bool) {
    return EntryCount.unwrap(n) == 0;
}

using {unwrap, increment, isZero} for EntryCount global;
```

**Step 5: Write IndexValue.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type IndexValue is uint256;
```

**Step 6: Write IndexValueMod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IndexValue} from "./IndexValue.sol";
import {EntryCount} from "./EntryCount.sol";

function unwrap(IndexValue v) pure returns (uint256) {
    return IndexValue.unwrap(v);
}

function fromEntryCount(EntryCount n) pure returns (IndexValue) {
    return IndexValue.wrap(EntryCount.unwrap(n));
}

using {unwrap} for IndexValue global;
```

**Step 7: Write SwapVolume.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

type SwapVolume is uint256;
```

**Step 8: Write SwapVolumeMod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {SwapVolume} from "./SwapVolume.sol";

function unwrap(SwapVolume v) pure returns (uint256) {
    return SwapVolume.unwrap(v);
}

function isZero(SwapVolume v) pure returns (bool) {
    return SwapVolume.unwrap(v) == 0;
}

using {unwrap, isZero} for SwapVolume global;
```

**Step 9: Write FixedMarketPrice.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";
import {SqrtPriceX96} from "../../types/SqrtPriceX96.sol";

struct FixedMarketPrice {
    SqrtPriceX96 lastPrice;
    PoolId referenceMarket;
}
```

**Step 10: Write FixedMarketPriceMod.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FixedMarketPrice} from "./FixedMarketPrice.sol";
import {PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";
import {SqrtPriceX96} from "../../types/SqrtPriceX96.sol";

function poolId(FixedMarketPrice memory fmp) pure returns (PoolId) {
    return fmp.referenceMarket;
}

function lastPrice(FixedMarketPrice memory fmp) pure returns (SqrtPriceX96) {
    return fmp.lastPrice;
}
```

**Step 11: Write SimulationConfig.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Capital} from "../../types/Capital.sol";

struct SimulationConfig {
    Capital initialCapital;
    uint256 numSwaps;
    uint256 swapAmount;
    uint160 sqrtPriceX96;
}
```

**Step 12: Verify all types compile**

```bash
forge build
```

Expected: compiles clean

**Step 13: Commit**

```bash
git add src/liquidity-supply-model-simplest/types/
git commit -m "feat: add model-dependent types for LiquiditySupplyModelSimplest"
```

---

### Task 7: Create ForkUtils.sol

**Files:**
- Create: `test/liquidity-supply-model-simplest/helpers/ForkUtils.sol`

**Step 1: Write ForkUtils.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

struct ChainAddresses {
    address poolManager;
    address positionManager;
    address stateView;
    address v4Quoter;
    address v3Factory;
    address permit2;
    address weth;
    address usdc;
    address usdt;
    address dai;
    address wbtc;
    uint256 forkBlock;
}

function getChainAddresses(string memory chainName) pure returns (ChainAddresses memory) {
    bytes32 h = keccak256(abi.encodePacked(chainName));

    if (h == keccak256("ethereum")) {
        return ChainAddresses({
            poolManager: 0x000000000004444c5dc75cB358380D2e3dE08A90,
            positionManager: 0xbD216513d74C8cf14cf4747E6AaA6420FF64ee9e,
            stateView: 0x7fFE42C4a5DEeA5b0feC41Ee5a8E9cC2F7A7B263,
            v4Quoter: 0x52f0E24D1C21C8A0cB1e5a5dD6198556BD9E1203,
            v3Factory: 0x1F98431c8aD98523631AE4a59f267346ea31F984,
            permit2: 0x000000000022D473030F116dDEE9F6B43aC78BA3,
            weth: 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2,
            usdc: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48,
            usdt: 0xdAC17F958D2ee523a2206206994597C13D831ec7,
            dai: 0x6B175474E89094C44Da98b954EedeAC495271d0F,
            wbtc: 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599,
            forkBlock: 21_000_000
        });
    }

    revert("ForkUtils: unknown chain");
}

function poolManager(string memory chainName) pure returns (address) {
    return getChainAddresses(chainName).poolManager;
}

function positionManager(string memory chainName) pure returns (address) {
    return getChainAddresses(chainName).positionManager;
}

function stateView(string memory chainName) pure returns (address) {
    return getChainAddresses(chainName).stateView;
}

function v4Quoter(string memory chainName) pure returns (address) {
    return getChainAddresses(chainName).v4Quoter;
}

function v3Factory(string memory chainName) pure returns (address) {
    return getChainAddresses(chainName).v3Factory;
}

function permit2(string memory chainName) pure returns (address) {
    return getChainAddresses(chainName).permit2;
}

function weth(string memory chainName) pure returns (address) {
    return getChainAddresses(chainName).weth;
}

function usdc(string memory chainName) pure returns (address) {
    return getChainAddresses(chainName).usdc;
}

function usdt(string memory chainName) pure returns (address) {
    return getChainAddresses(chainName).usdt;
}

function dai(string memory chainName) pure returns (address) {
    return getChainAddresses(chainName).dai;
}

function wbtc(string memory chainName) pure returns (address) {
    return getChainAddresses(chainName).wbtc;
}

function forkBlock(string memory chainName) pure returns (uint256) {
    return getChainAddresses(chainName).forkBlock;
}
```

**Step 2: Verify compiles**

```bash
forge build
```

Expected: compiles clean

**Step 3: Commit**

```bash
git add test/liquidity-supply-model-simplest/helpers/
git commit -m "feat: add ForkUtils with per-field chain address accessors"
```

---

### Task 8: Create Test Base Files

**Files:**
- Create: `test/liquidity-supply-model-simplest/base/StateInit.t.sol`
- Create: `test/liquidity-supply-model-simplest/base/HookDeployer.t.sol`

**Step 1: Write StateInit.t.sol (skeleton — setUp body is Phase 6 implementation work)**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {SimulationConfig} from "../../src/liquidity-supply-model-simplest/types/SimulationConfig.sol";
import {Capital} from "../../src/types/Capital.sol";

abstract contract LiquiditySupplyModelSimplestTest is Test {
    address constant TRADER = address(0xBEEF);

    SimulationConfig internal config;

    function setUp() public virtual {
        config = SimulationConfig({
            initialCapital: Capital.wrap(100e18),
            numSwaps: 10,
            swapAmount: 1e18,
            sqrtPriceX96: 79228162514264337593543950336
        });
    }
}
```

Note: TRADER cannot be address(this) in a constant since address(this) is not a compile-time constant in Solidity. Using a deterministic address. The full setUp with PoolManager, token deployment, LP funding, and router approvals will be implemented during Feature 1's Phase 6.

**Step 2: Write HookDeployer.t.sol (skeleton)**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {Hooks} from "@uniswap/v4-core/src/libraries/Hooks.sol";

abstract contract HookDeployer is Test {
    function jitHookFlags() internal pure returns (uint160) {
        return uint160(
            Hooks.BEFORE_SWAP_FLAG |
            Hooks.AFTER_SWAP_FLAG |
            Hooks.BEFORE_ADD_LIQUIDITY_FLAG |
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
        );
    }
}
```

**Step 3: Verify compiles**

```bash
forge build
```

Expected: compiles clean

**Step 4: Commit**

```bash
git add test/liquidity-supply-model-simplest/base/
git commit -m "feat: add StateInit and HookDeployer test base skeletons"
```

---

### Task 9: Create Empty Test Files

**Files:**
- Create: `test/liquidity-supply-model-simplest/CoreCfmm.kontrol.t.sol`
- Create: `test/liquidity-supply-model-simplest/CoreCfmm.fuzz.t.sol`
- Create: `test/liquidity-supply-model-simplest/JitPlp.kontrol.t.sol`
- Create: `test/liquidity-supply-model-simplest/JitPlp.fuzz.t.sol`
- Create: `test/liquidity-supply-model-simplest/EntryIndex.kontrol.t.sol`
- Create: `test/liquidity-supply-model-simplest/EntryIndex.fuzz.t.sol`

**Step 1: Write CoreCfmm.kontrol.t.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {LiquiditySupplyModelSimplestTest} from "./base/StateInit.t.sol";

contract CoreCfmmKontrolTest is LiquiditySupplyModelSimplestTest {

}
```

**Step 2: Write CoreCfmm.fuzz.t.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {LiquiditySupplyModelSimplestTest} from "./base/StateInit.t.sol";

contract CoreCfmmFuzzTest is LiquiditySupplyModelSimplestTest {

}
```

**Step 3: Write JitPlp.kontrol.t.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {LiquiditySupplyModelSimplestTest} from "./base/StateInit.t.sol";

contract JitPlpKontrolTest is LiquiditySupplyModelSimplestTest {

}
```

**Step 4: Write JitPlp.fuzz.t.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {LiquiditySupplyModelSimplestTest} from "./base/StateInit.t.sol";

contract JitPlpFuzzTest is LiquiditySupplyModelSimplestTest {

}
```

**Step 5: Write EntryIndex.kontrol.t.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {LiquiditySupplyModelSimplestTest} from "./base/StateInit.t.sol";

contract EntryIndexKontrolTest is LiquiditySupplyModelSimplestTest {

}
```

**Step 6: Write EntryIndex.fuzz.t.sol**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {LiquiditySupplyModelSimplestTest} from "./base/StateInit.t.sol";

contract EntryIndexFuzzTest is LiquiditySupplyModelSimplestTest {

}
```

**Step 7: Verify all compiles and tests discover (even if 0 tests run)**

```bash
forge build && forge test --summary
```

Expected: compiles clean, 0 tests found (empty test contracts)

**Step 8: Commit**

```bash
git add test/liquidity-supply-model-simplest/
git commit -m "feat: add empty test files for all 3 features (kontrol + fuzz)"
```

---

### Task 10: Final Verification

**Step 1: Full build**

```bash
forge build
```

Expected: compiles clean, no errors, no warnings

**Step 2: Verify directory structure matches design**

```bash
find src/ test/ specs/ script/ -type f | sort
```

Expected output should match the design doc layout.

**Step 3: Verify no SCOP violations in new code**

```bash
grep -r "library " src/ || echo "No library keyword found"
grep -r " is " src/ --include="*.sol" | grep -v "// SPDX" | grep -v "type .* is" || echo "No inheritance found"
```

Expected: "No library keyword found" and "No inheritance found"

**Step 4: Verify imports work for key dependencies**

Create a temporary test file:

```bash
cat > /tmp/import_test.sol << 'EOF'
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {PoolManager} from "@uniswap/v4-core/src/PoolManager.sol";
import {PoolId} from "@uniswap/v4-core/src/types/PoolId.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {Test} from "forge-std/Test.sol";
EOF
```

```bash
forge build
```

Expected: compiles clean (the temp file won't be in src/ so won't compile, but the real imports in actual files should resolve)

**Step 5: Final commit with all scaffold complete**

```bash
git status
```

Expected: clean working tree (all committed in prior tasks)

If any uncommitted changes remain, commit them:

```bash
git add -A && git commit -m "chore: finalize project scaffold"
```

---

## Summary

| Task | What | Gate |
|---|---|---|
| 1 | Delete old code | src/, test/, script/ empty |
| 2 | Install deps | All 12 libs in lib/ |
| 3 | Update remappings | forge resolves all paths |
| 4 | Create dirs | Full tree matches design |
| 5 | Model-independent types | 9 UDVTs + 9 Mod files compile |
| 6 | Model-dependent types | 6 types + 5 Mod files compile |
| 7 | ForkUtils.sol | Per-field accessors compile |
| 8 | Test base files | StateInit + HookDeployer compile |
| 9 | Empty test files | 6 test files compile, 0 tests |
| 10 | Final verification | forge build clean, no SCOP violations |

## Next Steps

After this scaffold is complete, begin Feature 1 (core-cfmm) TDD cycle:
1. Phase 1: Spec Kit + TLA+ (extends ToyCLAMM2DirArb)
2. Phase 2: 19 mandatory CFMM invariants + feature-specific
3. Phase 3: Contract type files for core-cfmm
4. Phases 4-7: Proofs, static analysis, implement, verify
