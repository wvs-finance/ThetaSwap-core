// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;


// note: It requires DelegateCallAuth


// when calls are coming from CallbackProxy, they are delegateCalls
// but when thinkiign about diamondIntegrations with masterHook, this also needs
// handling


// note: This goes inside uniswapV3/modules/
// struct UniswapV3ReactiveCallbackStorage{
//     IPoolManager poolManager;
//     IFeeConcentrationIndex fci;
// }
//
// bytes32 constant UNISWAP_V3_REACTIVE_CALLBACK_STORAGE_SLOT =
// function uniswapV3ReactiveCallbackStorage() pure returns(UniswapV3ReactiveCallbackStorage)
// function setPoolManager(IPoolManager)
// function getPoolManager() returns(IPoolManager)
// // note: setters and getters for FCI
// function setFCI(IFeeConcentrationIndex){}
// function getFCI() returns(IFeeConcentrationIndex){}
//
// note: This goes inside uniswapv3/ alone
// contract UniswapV3ReactiveCallbackFacet
//     address immutable public _self;
//
//     modifier onlyAuthCaller(){
// 	_;
//     }
//
//     function unlockWithSender(address sender,bytes calldata data) external{
// 	// note: This contract references the V4 poolManager
// 	// and calls unlock and then the afterSwap data arrives
// 	// through an empty swap call
//     }
//
//     function unlockWithSenderAndHookData(address sender, bytes calldata data, bytes calldata hookData)
// 	external {
//     }
//
//     constructor(){
// 	_self = address(this);
//     }
// }
