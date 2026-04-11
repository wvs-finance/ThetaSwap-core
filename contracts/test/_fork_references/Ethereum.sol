// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {Angstrom} from "core/src/Angstrom.sol";

library Tokens {
    address internal constant WETH = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
    address internal constant USDT = address(0xdAC17F958D2ee523a2206206994597C13D831ec7);
    address internal constant USDC = address(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48);
}

library UniswapAddresses {
    address internal constant POOL_MANAGER = 0x000000000004444c5dc75cB358380D2e3dE08A90;
}

library AngstromAddresses {
    address internal constant ANGSTROM = 0x0000000aa232009084Bd71A5797d089AA4Edfad4;
    bytes32 internal constant USDC_WETH =
        0xe500210c7ea6bfd9f69dce044b09ef384ec2b34832f132baec3b418208e3a657;
    bytes32 internal constant WETH_USDT =
        0x90078845bceb849b171873cfbc92db8540e9c803ff57d9d21b1215ec158e79b3;

    uint256 internal constant BLOCK_NUMBER_0 = 22_972_937;

    uint24 internal constant FEE = 0x800000;
    uint24 internal constant TICK_SPACING = 10;
}
