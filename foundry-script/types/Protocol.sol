// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

enum Protocol {
    UniswapV3,
    UniswapV4
}

function isUniswapV3(Protocol p) pure returns (bool) {
    return p == Protocol.UniswapV3;
}

function isUniswapV4(Protocol p) pure returns (bool) {
    return p == Protocol.UniswapV4;
}
