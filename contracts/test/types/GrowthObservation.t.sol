// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {BaseForkTest} from "anstrong-test/_helpers/BaseForkTest.t.sol";
import {AngstromAccumulatorConsumer} from "core/src/_adapters/AngstromAccumulatorConsumer.sol";
import {IAngstromAuth} from "core/src/interfaces/IAngstromAuth.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";

contract GrowthObservationTest is BaseForkTest {}

