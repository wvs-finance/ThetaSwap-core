// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;



import {FiscalPolicyBase} from "./base/FiscalPolicyBase.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {BaseHook} from "@uniswap/v4-periphery/src/utils/BaseHook.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {
    PoolId,
    PoolKey,
    PoolIdLibrary
} from "@uniswap/v4-core/src/types/PoolId.sol";
import {Address} from "@openzeppelin/contracts/utils/Address.sol";

contract UniswapFiscalPolicyBase is FiscalPolicyBase, BaseHook{
    using Address for address;
    
    constructor(IPoolManager _manager) FiscalPolicyBase(address(_manager)) BaseHook(_manager){}

    function _beforeInitialize(address, PoolKey calldata, uint160) internal virtual returns (bytes4) {
        PoolId poolId = poolKey.toId();
        require(address(taxStrategies[PoolId.unwrap(poolId)]) != address(0x00), "Tax Strategy has not been set");

    }

    function 


    











}
