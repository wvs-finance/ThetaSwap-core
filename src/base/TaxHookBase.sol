// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;


import {ERC1155} from "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import {ITaxHook} from "../interfaces/ITaxHook.sol";
import {BaseHook} from "@uniswap/v4-periphery/src/utils/BaseHook.sol";
import {
    Tax,
    TaxLibrary
} from "../types/Tax.sol";



abstract contract TaxHookBase is ITaxHook {
    using TaxLibrary for Tax;
    address immutable actionsRouter;



    mapping(bytes32 poolId => int256 taxCreditDelta) _taxCredit;
    mapping(bytes32 poolId => int256 taxRevenueDelta) _taxRevenue;

    // NOTE: THe invariant is that taxCredit == taxRevenue 
    
    constructor(address _actionRouter){
        actionRouter = _actionRouter;
    }

    function collectTaxRevenue(
        bytes32 poolId,
        bytes calldata taxRevenueData
    ) external{

    }

    function _onTaxRevenue(
        bytes32 poolId,
        bytes calldata taxRevenueData
    ) internal override;

    function credit(
        bytes32 poolId,
        bytes calldata creditData
    ) external{

    }

    function _onCredit(
        bytes32 poolId,
        bytes calldata creditData
    ) internal virtual;




    // NOTE: The pool id  maps one to one with the tokenId

}