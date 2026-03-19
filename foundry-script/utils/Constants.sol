// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Constants} from "v4-core/test/utils/Constants.sol";

int24 constant TICK_LOWER = -60;
int24 constant TICK_UPPER = 60;
uint24 constant TICK_SPACING = 10;
int256 constant AMOUNT_SPECIFIED = 100;
bool constant ZERO_FOR_ONE = true;
uint48 constant DEADLINE = type(uint48).max - 1; 
