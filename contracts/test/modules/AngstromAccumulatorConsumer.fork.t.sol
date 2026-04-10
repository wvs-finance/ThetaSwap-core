// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

import {BaseForkTest} from "anstrong-test/_helpers/BaseForkTest.t.sol";
import {AngstromAccumulatorConsumer} from "core/src/_adapters/AngstromAccumulatorConsumer.sol";
import {IAngstromAuth} from "core/src/interfaces/IAngstromAuth.sol";
import "anstrong-test/_fork_references/Ethereum.sol" as EthereumForkData;


contract AngstromAccumulatorConsumerForkTest is BaseForkTest {
    AngstromAccumulatorConsumer angstromAccumulatorConsumer;

    function setUp() public override {
	super.setUp();
	angstromAccumulatorConsumer = new AngstromAccumulatorConsumer(
								      IAngstromAuth(
										    EthereumForkData.AngstromAddresses.ANGSTROM
										    
								      ),
								      POOL_MANAGER
	);
    }
}




