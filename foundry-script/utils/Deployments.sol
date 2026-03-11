// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Protocol, isUniswapV3, isUniswapV4} from "@foundry-script/types/Protocol.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";

// Chain IDs
uint256 constant SEPOLIA = 11155111;
uint256 constant UNICHAIN_SEPOLIA = 1301;

// ── Known deployment addresses ──
// Hardcoded per chain/protocol so .env only holds secrets (ALCHEMY_API_KEY, MNEMONIC).


type PoolRpt is bytes32;


// note: This returns the Pool deployed on a determined chain
function uniswapV4(PoolRpt, uint256 chainId) returns (PoolId){}
function uniswapV3(PoolRpt, uint256 chainId) returns (IUniswapV3Pool){
    // e.g for sepolia there is a pool already deployed on sepolia on .env
    // same needs to be done on v4 and v33 on unichain sepolia
}


struct Deployments {
    address positionManager;
    address poolManager;
    address swapRouter;
    IFeeConcentrationIndex fciIndex;
    // note: This is for the mockPool we already created on V3 sepolia. But with the same tokens need
    // equivalent for V4
    PoolRpt poolRpt;
}

// ── Sepolia V3 ──

function sepoliaV3Pool() pure returns (IUniswapV3Pool) {
    return IUniswapV3Pool(0xF66da9dd005192ee584a253b024070c9A1A1F4FA);
}

function sepoliaAdapter() pure returns (address) {
    return 0xA4539EbBc31cd11b8b404D989507d3112F04cB45;
}

function sepoliaFCI() pure returns (IFeeConcentrationIndex) {
    return IFeeConcentrationIndex(0xe24A74652067Ea5EF32Ee85d69Dc20d67E9220C0);
}

// ── Unichain Sepolia V4 ──

function unichainSepoliaPositionManager() pure returns (address) {
    return 0xf969Aee60879C54bAAed9F3eD26147Db216Fd664;
}

function unichainSepoliaPoolManager() pure returns (address) {
    return 0x00B036B58a818B1BC34d502D3fE730Db729e62AC;
}

function unichainSepoliaSwapRouter() pure returns (address) {
    return 0x9140a78c1A137c7fF1c151EC8231272aF78a99A4; // PoolSwapTest
}

function unichainSepoliaFCI() pure returns (IFeeConcentrationIndex) {
    return IFeeConcentrationIndex(address(0)); // TODO: deploy FCI on Unichain Sepolia
}

function unichainSepoliaFCIHook() pure returns (address) {
    return address(0); // TODO: fill after DeployFCIHookV4
}

// ── Ethereum Sepolia V4 ──

uint256 constant ETH_SEPOLIA = 11155111;

function ethSepoliaPositionManager() pure returns (address) {
    return 0x429ba70129df741B2Ca2a85BC3A2a3328e5c09b4;
}

function ethSepoliaPoolManager() pure returns (address) {
    return 0xE03A1074c86CFeDd5C142C4F04F1a1536e203543;
}

function ethSepoliaSwapRouter() pure returns (address) {
    return 0xb044e610beeb13cf56a319e41cE1F45826E55E84;
}

function ethSepoliaFCI() pure returns (IFeeConcentrationIndex) {
    return IFeeConcentrationIndex(address(0)); // TODO: deploy FCI on Eth Sepolia
}

function ethSepoliaFCIHook() pure returns (address) {
    return 0xc3e8Cb062EC61b40530aBea9Df9449F5b95987C0;
}

// ── Mock Tokens ──

function unichainSepoliaTokenA() pure returns (address) {
    return address(0); // TODO: fill after DeployMockTokens
}

function unichainSepoliaTokenB() pure returns (address) {
    return address(0); // TODO: fill after DeployMockTokens
}

function sepoliaTokenA() pure returns (address) {
    return 0x3eEE766C0d9Ca7D1509e2493857449Ef65A62cF3;
}

function sepoliaTokenB() pure returns (address) {
    return 0xdabc71B8cBBB062AC745Cc03DcEBd9C7B4d225b6;
}

function resolveTokens(uint256 chainId) pure returns (address tokenA, address tokenB) {
    if (chainId == UNICHAIN_SEPOLIA) {
        tokenA = unichainSepoliaTokenA();
        tokenB = unichainSepoliaTokenB();
    } else if (chainId == SEPOLIA) {
        tokenA = sepoliaTokenA();
        tokenB = sepoliaTokenB();
    } else {
        revert UnknownDeployment(chainId, Protocol.UniswapV3);
    }
}

// ── Resolvers ──

error UnknownDeployment(uint256 chainId, Protocol protocol);

function resolveDeployments(uint256 chainId, Protocol protocol)
    pure
    returns (Deployments memory d)
{
    if (chainId == UNICHAIN_SEPOLIA && isUniswapV4(protocol)) {
        d.positionManager = unichainSepoliaPositionManager();
        d.poolManager = unichainSepoliaPoolManager();
        d.swapRouter = unichainSepoliaSwapRouter();
        d.fciIndex = IFeeConcentrationIndex(unichainSepoliaFCIHook());
    } else if (chainId == SEPOLIA && isUniswapV4(protocol)) {
        d.positionManager = ethSepoliaPositionManager();
        d.poolManager = ethSepoliaPoolManager();
        d.swapRouter = ethSepoliaSwapRouter();
        d.fciIndex = IFeeConcentrationIndex(ethSepoliaFCIHook());
    } else {
        revert UnknownDeployment(chainId, protocol);
    }
}

function sepoliaV3Factory() pure returns (address) {
    return 0x0227628f3F023bb0B980b67D528571c95c6DaC1c;
}

function sepoliaV3CallbackRouter() pure returns (address) {
    return 0x1284E9d71a87276d05abD860bD9990dce9Dd721E;
}

function sepoliaReactiveAdapter() pure returns (address) {
    return 0xC1ED47e34E95fa74fCf0Ff9B4b75Dac99F1bFF23;
}

function sepoliaFreshV3Pool() pure returns (IUniswapV3Pool) {
    return IUniswapV3Pool(0xcB80f9b60627DF6915cc8D34F5d1EF11617b8Af8);
}

// ── Lasna (Reactive Network Testnet) ──

uint256 constant LASNA = 5318007;

function lasnaThetaSwapReactive() pure returns (address) {
    return 0x4072a68c549af7934296D57Fb3B834A9f11929d0;
}

function sepoliaCallbackProxy() pure returns (address) {
    return 0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA;
}

function resolveV3(uint256 chainId)
    pure
    returns (IUniswapV3Pool pool, address adapter, IFeeConcentrationIndex fci)
{
    if (chainId == SEPOLIA) {
        pool = sepoliaV3Pool();
        adapter = sepoliaAdapter();
        fci = sepoliaFCI();
    } else {
        revert UnknownDeployment(chainId, Protocol.UniswapV3);
    }
}
