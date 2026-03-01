// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

// ============================================================================
// Ethereum.sol -- Canonical mainnet addresses for forked anvil testing
//
// All addresses are Ethereum mainnet (chainId 1).
// Source: https://docs.uniswap.org/contracts/v4/deployments
//         https://etherscan.io
// ============================================================================

import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";
import {IAllowanceTransfer} from "permit2/src/interfaces/IAllowanceTransfer.sol";
import {IWETH9} from "@uniswap/v4-periphery/src/interfaces/external/IWETH9.sol";
import {IERC20Partial} from "2025-12-panoptic/contracts/tokens/interfaces/IERC20Partial.sol";

// -- Uniswap V4 Core --

IPoolManager constant POOL_MANAGER = IPoolManager(0x000000000004444c5dc75cB358380D2e3dE08A90);

// -- Uniswap V4 Periphery --

IPositionManager constant POSITION_MANAGER = IPositionManager(0xbD216513d74C8cf14cf4747E6AaA6420FF64ee9e);
address constant POSITION_DESCRIPTOR = 0xd1428BA554f4c8450b763a0b2040a4935C63f06c;
address constant V4_QUOTER = 0x52f0E24D1C21C8A0CB1e5a5dD6198556BD9E1203;
address constant STATE_VIEW = 0x7fFe42C4a5DEeA5b0fEc41C94c136Cf115597227;

// -- Uniswap Universal Router --

address constant UNIVERSAL_ROUTER = 0x66a9893cC07D91D95644aedd05D03f95e1dBA8af;

// -- Permit2 (deterministic, same on all EVM chains) --

IAllowanceTransfer constant PERMIT2 = IAllowanceTransfer(0x000000000022D473030F116dDEE9F6B43aC78BA3);

// -- Tokens --

IWETH9 constant WETH = IWETH9(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
IERC20Partial constant USDC = IERC20Partial(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48);
IERC20Partial constant USDT = IERC20Partial(0xdAC17F958D2ee523a2206206994597C13D831ec7);
IERC20Partial constant DAI = IERC20Partial(0x6B175474E89094C44Da98b954EedeAC495271d0F);
IERC20Partial constant WBTC = IERC20Partial(0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599);

// -- Uniswap V3 (reference pools for fork tests) --

address constant V3_FACTORY = 0x1F98431c8aD98523631AE4a59f267346ea31F984;
address constant V3_USDC_WETH_005 = 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640;
address constant V3_USDC_WETH_030 = 0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8;

// -- Fork block (recent mainnet block for deterministic tests) --

uint256 constant FORK_BLOCK = 21_000_000;
