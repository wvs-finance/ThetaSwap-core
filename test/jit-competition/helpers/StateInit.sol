// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// -- V4 Core --
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {PoolManager} from "@uniswap/v4-core/src/PoolManager.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "@uniswap/v4-core/src/types/PoolId.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {Hooks} from "@uniswap/v4-core/src/libraries/Hooks.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {StateLibrary} from "@uniswap/v4-core/src/libraries/StateLibrary.sol";

// -- V4 Test Routers --
import {PoolSwapTest} from "@uniswap/v4-core/src/test/PoolSwapTest.sol";
import {PoolModifyLiquidityTest} from "@uniswap/v4-core/src/test/PoolModifyLiquidityTest.sol";
// Import this ...
import {SwapParams, ModifyLiquidityParams} from "@uniswap/PoolOperation.sol";
// -- Panoptic IERC20Partial (no return values -- works with USDT etc) --
import {IERC20Partial} from "2025-12-panoptic/contracts/tokens/interfaces/IERC20Partial.sol";

// -- Forge --
// Note: We use address instead of Vm.Wallet in Accounts
// because Vm.Wallet is an interface struct that can't be stored in mappings easily.

// -- Model --
import {JitHook} from "../../src/JitHook.sol";
import {EntryIndex} from "../../src/EntryIndex.sol";
import {SimulationConfig} from "../../src/types/ModelParams.sol";
import {Capital} from "../../src/types/ModelTypes.sol";

// ============================================================================
// ModelSpec.sol -- Functional state initialization for JIT competition tests
//
// Pattern: Panoptic _cacheWorldState / _initAccounts adapted for our model.
// No inheritance. Diamond storage for ForkedState and ModelState.
// Free functions operate on storage structs.
//
// From NOTES.md:
//   1. Two pools with the same underlying
//   1.2. One of the tokens is a unit of account token (numeraire)
//   1.3. Token approval of routers, etc
//   1.4. Traders have no identity (address(this) on tests) -- we do not care
//        about their dynamics since all are uninformed. We care about the
//        induced flow following a mean-reversion.
// ============================================================================

// -- Pool Constants (moved out of SimulationConfig per user design) --

uint24 constant FEE = 3000; // 0.30%
int24 constant TICK_SPACING = 60;

// -- TickRange: packed int48 holding lower and upper ticks --

type TickRange is int48;

function tickLower(TickRange r) pure returns (int24) {
    // Mask lower 24 bits, then sign-extend to int24
    return int24(int48(uint48(TickRange.unwrap(r)) & 0xFFFFFF));
}

function tickUpper(TickRange r) pure returns (int24) {
    // Shift right 24 bits (unsigned to avoid sign extension), mask, sign-extend
    return int24(int48(uint48(uint48(TickRange.unwrap(r)) >> 24) & 0xFFFFFF));
}

function packTickRange(int24 lower, int24 upper) pure returns (TickRange) {
    // Mask each to 24 bits (unsigned) before packing to avoid sign pollution
    uint48 lo = uint48(uint24(lower));
    uint48 hi = uint48(uint24(upper)) << 24;
    return TickRange.wrap(int48(lo | hi));
}

// Default tick range: [-120, 120] (constant, no volatility)
TickRange constant TICK_RANGE = TickRange.wrap(int48(uint48(uint24(int24(-120))) | (uint48(uint24(int24(120))) << 24)));

// -- Accounts: LP roles per pool --

struct Accounts {
    // role => poolId => address
    // Roles: "jit", "plp", "plp2" (second passive on control pool)
    // New LPs added per swap round are "entrant_N"
    mapping(bytes32 => mapping(bytes32 => address)) addrs;
    uint256 nextEntrantId;
}

function getAccount(
    Accounts storage accts,
    string memory role,
    PoolId poolId
) view returns (address) {
    return accts.addrs[keccak256(bytes(role))][PoolId.unwrap(poolId)];
}

function setAccount(
    Accounts storage accts,
    string memory role,
    PoolId poolId,
    address addr
) {
    accts.addrs[keccak256(bytes(role))][PoolId.unwrap(poolId)] = addr;
}

// -- ForkedState: only things gotten from the fork --

struct ForkedState {
    IERC20Partial stableAsset; // numeraire token from fork
    IERC20Partial riskyAsset;  // risky token from fork
    IPositionManager positionManager;
    Currency currency0;        // sorted (V4 requirement)
    Currency currency1;
}

bytes32 constant FORKED_STATE_SLOT = keccak256("jit.competition.forked.state");

function getForkedState() pure returns (ForkedState storage $) {
    bytes32 position = FORKED_STATE_SLOT;
    assembly {
        $.slot := position
    }
}

function stableAsset() view returns (IERC20Partial) {
    return getForkedState().stableAsset;
}

function riskyAsset() view returns (IERC20Partial) {
    return getForkedState().riskyAsset;
}

function positionManager() ..
// -- ModelState: our constructions --

struct ModelState {
    Accounts accounts;
    ForkedState forkedState;
    mapping(bytes32 => PoolKey) markets;
    JitHook jitHook;
    EntryIndex entryIndex;
    SimulationConfig config;
}



bytes32 constant MODEL_STATE_SLOT = keccak256("jit.competition.model.state");

function getModelState() pure returns (ModelState storage $) {
    bytes32 position = MODEL_STATE_SLOT;
    assembly {
        $.slot := position
    }
}

function getForkedState() ...


function jitLiquiquidityParams(SwapParams) returns(ModifyLiquidityParams)


function getMarket(string memory id) view returns (PoolKey memory) {
    return getModelState().markets[keccak256(bytes(id))];
}

function setMarket(string memory id, PoolKey memory key) {
    bytes32 k = keccak256(bytes(id));
    ModelState storage $ = getModelState();
    $.markets[k] = key;
    $.marketIds[k] = PoolIdLibrary.toId(key);
}

function getMarketId(string memory id) view returns (PoolId) {
    return getModelState().marketIds[keccak256(bytes(id))];
}

// -- IStateInit interface --
// Encodes NOTES.md assumptions as setup steps:
//   1. Two pools with the same underlying
//   1.2. One token is numeraire
//   1.3. Token approvals for routers
//   1.4. Traders are address(this) -- no identity

interface IStateInit {
    /// @notice Full initialization sequence
    function init() external;

    /// @notice Fund all LP accounts with equal capital
    function fundAccounts() external;

    /// @notice Initialize both pools at same price
    function initPools() external;

    /// @notice Deploy JIT hook at correct V4 address
    function deployHook() external;
}



type LiquidityDelta is uint256;
//


===> JIT probability of arriaval is always 1

// This is embedded here 
library JITAlwaysArrive{
	
	function fillSwap(
		 SwapParams swapParams,
		 BeforeSwapDelta swapDelta,
	) returns (LiquidityDelta swapFulfilled){
	  	  positionManager.mintLiquidity(jitLiquidityParams(swapParams));
		 require(CurrencySettled(swapDelta, swapFulfilled) ...);
	}
}


enum TokenVesting{
     UNIFORM // default
}
struct TokenLaunch{
       TokenVesting       
}


function vest(TokenVesting vestingMethod){
	 assembly{
		switch vestingMethod:
		
		default 0x00:
			// uniformly distribute toke supply on ModelState accounts
	 }
}
