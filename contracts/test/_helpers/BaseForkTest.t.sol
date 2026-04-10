// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;


import {BaseTest} from "anstrong-test/_helpers/BaseTest.sol";
import {console2} from "forge-std/console2.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {IWETH} from "pendle/interfaces/IWETH.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolId} from "v4-core/src/types/PoolId.sol";
import "anstrong-test/_fork_references/Ethereum.sol" as EthereumForkData;

contract BaseForkTest is BaseTest {
    uint256 constant BLOCK_NUMBER_0 = EthereumForkData.AngstromAddresses.BLOCK_NUMBER_0;

    IWETH WETH;
    IERC20 USDC;
    IERC20 USDT;

    IPoolManager POOL_MANAGER;
    PoolId WETH_USDT;
    PoolId USDC_WETH;

    bool forked;

    modifier onlyForked() {
        if (forked) {
            console2.log("running forked test");
            _;
            return;
        }
        console2.log("skipping forked test");
    }

    function setUp() public virtual {
	try vm.envString("ALCHEMY_API_KEY") returns (string memory) {
	    vm.createSelectFork(vm.rpcUrl("mainnet"), BLOCK_NUMBER_0);

            WETH = IWETH(EthereumForkData.Tokens.WETH);
            USDC = IERC20(EthereumForkData.Tokens.USDC);
            USDT = IERC20(EthereumForkData.Tokens.USDT);

	    POOL_MANAGER = IPoolManager(EthereumForkData.UniswapAddresses.POOL_MANAGER);
            WETH_USDT = PoolId.wrap(EthereumForkData.AngstromAddresses.WETH_USDT);
            USDC_WETH = PoolId.wrap(EthereumForkData.AngstromAddresses.USDC_WETH);

	    forked = true;
	} catch {
	    console2.log("Skipping forked tests, no alchemy key found. Add ALCHEMY_API_KEY env var to .env to run forked tests.");
	}
    }
}
