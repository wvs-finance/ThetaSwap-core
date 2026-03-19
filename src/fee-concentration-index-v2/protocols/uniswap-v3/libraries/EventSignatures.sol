// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {POOL_ADDED_SIG} from "@fee-concentration-index-v2/libraries/PoolAddedSig.sol";

// Uniswap V3 event topic0 signatures for Reactive Network subscriptions.
// Values are pre-calculated. Derivations shown in comments.

// keccak256("Swap(address,address,int256,int256,uint160,uint128,int24)")
uint256 constant V3_SWAP_SIG = 0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67;

// keccak256("Mint(address,address,int24,int24,uint128,uint256,uint256)")
uint256 constant V3_MINT_SIG = 0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde;

// keccak256("Burn(address,int24,int24,uint128,uint256,uint256)")
uint256 constant V3_BURN_SIG = 0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c;

// Self-sync event signatures (emitted by RN instance, consumed by ReactVM)

// keccak256("PoolRegistered(uint256,address)")
uint256 constant POOL_REGISTERED_SIG = 0x403a01572a6930b9303134960bb6e5d695084d389779d4554842553846135ffd;

// keccak256("PoolUnregistered(uint256,address)")
uint256 constant POOL_UNREGISTERED_SIG = 0xf8a85b30c450aae09b266730946d2e1c61a36e77d194bf4e50205060a8163079;

// ── Batch signature arrays ──

function selfSyncSigs() pure returns (uint256[] memory sigs) {
    sigs = new uint256[](2);
    sigs[0] = POOL_REGISTERED_SIG;
    sigs[1] = POOL_UNREGISTERED_SIG;
}

function v3PoolSigs() pure returns (uint256[] memory sigs) {
    sigs = new uint256[](3);
    sigs[0] = V3_SWAP_SIG;
    sigs[1] = V3_MINT_SIG;
    sigs[2] = V3_BURN_SIG;
}
