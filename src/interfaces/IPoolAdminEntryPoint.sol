//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {IFiscalPolicy} from "./IFiscalPolicy.sol";


interface IPoolAdmin{
    
    function createCustomPool(
        bytes memory poolDeploymentData
    ) external;

    function pluginFiscalPolicy(
        bytes32 poolId, // NOTE: Each hook decodes this as needed
        IFiscalPolicy fiscalPolicy
    ) external;

    function pluginOracle(
        bytes32 poolId,
        ILPOracle oracle
    ) external;



}