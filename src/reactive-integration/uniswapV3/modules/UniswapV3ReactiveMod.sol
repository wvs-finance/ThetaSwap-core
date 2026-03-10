// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IReactive} from "reactive-lib/interfaces/IReactive.sol";
import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {
    isSelfSync, topic0, emitter, logChainId,
    decodeTopic1AsAddress, decodeTopic2AsInt24, decodeTopic3AsInt24
} from "../../types/LogRecordExtMod.sol";
import {V3SwapData, V3MintData, V3BurnData, V3CollectData} from "../types/UniswapV3CallbackData.sol";
import {TickShadow, getTick, setTick} from "../types/TickShadow.sol";
import {RvmId, rvmIdPlaceHolder, toAddress} from "../../types/RvmId.sol";

// keccak256("Swap(address,address,int256,int256,uint160,uint128,int24)")
uint256 constant V3_SWAP_SIG = 0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67;
// keccak256("Mint(address,address,int24,int24,uint128,uint256,uint256)")
uint256 constant V3_MINT_SIG = 0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde;
// keccak256("Burn(address,int24,int24,uint128,uint256,uint256)")
uint256 constant V3_BURN_SIG = 0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c;
// keccak256("Collect(address,address,int24,int24,uint128,uint128)")
uint256 constant V3_COLLECT_SIG = 0x70935338e69775456a85ddef226c395fb668b63fa0115f5f20610b388e6ca9c0;
// keccak256("PoolRegistered(uint256,address)")
uint256 constant POOL_REGISTERED_SIG = 0x403a01572a6930b9303134960bb6e5d695084d389779d4554842553846135ff;
// keccak256("PoolUnregistered(uint256,address)")
uint256 constant POOL_UNREGISTERED_SIG = 0xf8a85b30c450aae09b266730946d2e1c61a36e77d194bf4e50205060a8163079;
uint64 constant CALLBACK_GAS_LIMIT = 1_000_000;
// uint8 constant UNISWAP_V3_REACTIVE_BEFORE_SWAP_FLAG =

// bytes memory hookData = buildHookData()
//             uniswapV3ReactiveFlags | beforeSwapTick


// ReactVM-side state. Isolated from destination chain.
struct UniswapV3ReactiveStorage {
    mapping(uint256 => mapping(address => bool)) poolWhitelist;
    mapping(uint256 => mapping(address => TickShadow)) tickShadow;
}

bytes32 constant UNISWAP_V3_REACTIVE_STORAGE_SLOT = keccak256("ThetaSwapReactive.vm.storage");

function uniswapV3ReactiveStorage() pure returns (UniswapV3ReactiveStorage storage s) {
    bytes32 slot = UNISWAP_V3_REACTIVE_STORAGE_SLOT;
    assembly {
        s.slot := slot
    }
}

function isWhitelisted(uint256 chainId_, address pool) view returns (bool) {
    return uniswapV3ReactiveStorage().poolWhitelist[chainId_][pool];
}

function setWhitelisted(uint256 chainId_, address pool, bool status) {
    uniswapV3ReactiveStorage().poolWhitelist[chainId_][pool] = status;
}

function getLastTick(uint256 chainId_, address pool) view returns (int24 tick, bool isSet) {
    (tick, isSet) = getTick(uniswapV3ReactiveStorage().tickShadow[chainId_][pool]);
}

function setLastTick(uint256 chainId_, address pool, int24 tick) {
    setTick(uniswapV3ReactiveStorage().tickShadow[chainId_][pool], tick);
}


function decodeV3Swap(IReactive.LogRecord calldata log) pure returns (V3SwapData memory) {
    // Swap: topic_1=sender(indexed), topic_2=recipient(indexed)
    // data: (int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick)
    (,,,, int24 tick) = abi.decode(log.data, (int256, int256, uint160, uint128, int24));
    return V3SwapData({pool: IUniswapV3Pool(log._contract), tickBefore: 0, tick: tick});
}

function decodeV3Mint(IReactive.LogRecord calldata log) pure returns (V3MintData memory) {
    // Mint: topic_1=owner(indexed), topic_2=tickLower(indexed), topic_3=tickUpper(indexed)
    // data: (address sender, uint128 amount, uint256 amount0, uint256 amount1)
    address owner = decodeTopic1AsAddress(log);
    int24 tickLower = decodeTopic2AsInt24(log);
    int24 tickUpper = decodeTopic3AsInt24(log);
    (, uint128 liquidity,,) = abi.decode(log.data, (address, uint128, uint256, uint256));
    return V3MintData({
        pool: IUniswapV3Pool(log._contract),
        owner: owner,
        tickLower: tickLower,
        tickUpper: tickUpper,
        liquidity: liquidity
    });
}

function decodeV3Burn(IReactive.LogRecord calldata log) pure returns (V3BurnData memory) {
    // Burn: topic_1=owner(indexed), topic_2=tickLower(indexed), topic_3=tickUpper(indexed)
    // data: (uint128 amount, uint256 amount0, uint256 amount1)
    address owner = decodeTopic1AsAddress(log);
    int24 tickLower = decodeTopic2AsInt24(log);
    int24 tickUpper = decodeTopic3AsInt24(log);
    (uint128 liquidity,,) = abi.decode(log.data, (uint128, uint256, uint256));
    return V3BurnData({
        pool: IUniswapV3Pool(log._contract),
        owner: owner,
        tickLower: tickLower,
        tickUpper: tickUpper,
        liquidity: liquidity
    });
}

function decodeV3Collect(IReactive.LogRecord calldata log) pure returns (V3CollectData memory) {
    // Collect: topic_1=owner(indexed), topic_2=tickLower(indexed), topic_3=tickUpper(indexed)
    // data: (address recipient, uint128 amount0, uint128 amount1)
    address owner = decodeTopic1AsAddress(log);
    int24 tickLower = decodeTopic2AsInt24(log);
    int24 tickUpper = decodeTopic3AsInt24(log);
    (, uint128 feeAmount0, uint128 feeAmount1) = abi.decode(log.data, (address, uint128, uint128));
    return V3CollectData({
        pool: IUniswapV3Pool(log._contract),
        owner: owner,
        tickLower: tickLower,
        tickUpper: tickUpper,
        feeAmount0: feeAmount0,
        feeAmount1: feeAmount1
    });
}

// function buildHookData(uint8 flag) pure returns(bytes memory hookData){
//     if (flag == UNISWAP_V3_REACTIVE_BEFORE_SWAP_FLAG){
// 	return abi.encode(UNISWAP_V3_REACTIVE_BEFORE_SWAP_FLAG)
//    }
// }

// Main routing function — called by ThetaSwapReactive.react().
function processLog(
    IReactive.LogRecord calldata log,
    address self,
    address adapter // callback
) {
    // Self-subscription sync: pool whitelist updates from RN instance
    if (isSelfSync(log, self)) {
        _handleSelfSync(log);
        return;
    }

    // Skip events from non-whitelisted pools
    if (!isWhitelisted(logChainId(log), emitter(log))) return;

    uint256 sig = topic0(log);

    // Reactive Network replaces the first address(0) arg with the actual RVM ID
    // before executing the callback on the destination chain.

    if (sig == V3_SWAP_SIG) {
        V3SwapData memory data = decodeV3Swap(log);
        uint256 chainId_ = logChainId(log);
        address pool = emitter(log);

        // Inject pre-swap tick from shadow state.
        // First swap: no previous tick → use post-swap tick as both (single-tick sweep).
        (int24 prevTick, bool isSet) = getLastTick(chainId_, pool);
        data.tickBefore = isSet ? prevTick : data.tick;
        setLastTick(chainId_, pool, data.tick);


	// writeCacheTick(uniswapV3Reactive(), tick)
	//                ----> this outputs the desired hookData
	// but this is the reactive VM
	// thus, we need
	// bytes memory hookData = buildHookData(flag)
	//             uniswapV3ReactiveFlags | beforeSwapTick | uniswapV3PoolAddress
	//
	// emit IReactive.Callback(
	//     chainId, uniswapV3ReactiveCallback, CALLBACK_GAS_LIMIT, abi.encodeCall(
	//                                                               IUniswapV3ReactiveCallback.unlock,
	//                                                               ( 
	//                                                                 RVM_ID_PLACEHOLDER->address(0)
	//                                                                 encodeAfterSwapCalldata
	//                                                                       data,
	//                                                                       hookData
	//                                                                   )
	//                                                                )
	//                                                             )
	//)
        emit IReactive.Callback(
            chainId_, adapter, CALLBACK_GAS_LIMIT,
            abi.encodeWithSignature("onV3Swap(address,(address,int24,int24))", address(0), data)
        );
    } else if (sig == V3_MINT_SIG) {
        V3MintData memory data = decodeV3Mint(log);
        emit IReactive.Callback(
            logChainId(log), adapter, CALLBACK_GAS_LIMIT,
            abi.encodeWithSignature("onV3Mint(address,(address,address,int24,int24,uint128))", address(0), data)
        );
    } else if (sig == V3_BURN_SIG) {
        // No longer deferred — onV3Burn reads fees directly from V3 pool.
        // Still skip zero-burns (fee-accounting only, liq==0) since they
        // don't represent actual position removal.
        V3BurnData memory data = decodeV3Burn(log);
        if (data.liquidity == 0) return;
        emit IReactive.Callback(
            logChainId(log), adapter, CALLBACK_GAS_LIMIT,
            abi.encodeWithSignature("onV3Burn(address,(address,address,int24,int24,uint128))", address(0), data)
        );
    }
    // V3_COLLECT_SIG: no-op — fees are read directly from V3 pool in onV3Burn
}

function _handleSelfSync(IReactive.LogRecord calldata log) {
    uint256 sig = topic0(log);
    // PoolRegistered/PoolUnregistered have both params indexed →
    // chainId is in topic_1, pool address is in topic_2 (not in data).
    if (sig == POOL_REGISTERED_SIG) {
        uint256 chainId_ = log.topic_1;
        address pool = address(uint160(log.topic_2));
        setWhitelisted(chainId_, pool, true);
    } else if (sig == POOL_UNREGISTERED_SIG) {
        uint256 chainId_ = log.topic_1;
        address pool = address(uint160(log.topic_2));
        setWhitelisted(chainId_, pool, false);
    }
}
