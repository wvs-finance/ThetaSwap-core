// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script} from "forge-std/Script.sol";
import {Test, console2} from "forge-std/Test.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";

import {FeeConcentrationIndexV2} from "@fee-concentration-index-v2/FeeConcentrationIndexV2.sol";
import {UniswapV3Facet} from "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Facet.sol";
import {UniswapV3Callback} from "@fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Callback.sol";
import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {IUnlockCallback} from "v4-core/src/interfaces/callback/IUnlockCallback.sol";
import {UNISWAP_V3_REACTIVE} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";

import {IUniswapV3Pool} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import {IUniswapV3Factory} from "@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol";
import {V3CallbackRouter} from "@utils/V3CallbackRouter.sol";

import {Accounts, initAccounts} from "@utils/Accounts.sol";

/// @title UniswapV3 Reactive FCI V2 — Reproducible integration test
/// @notice Deploys FRESH tokens + V3 pool + FCI + reactive each run.
///         Fully self-contained and CI-reproducible.
///
/// Usage: ./scripts/run-v3-integration.sh
contract UniswapV3FCI_IntegrationScript is Script, Test {
    using PoolIdLibrary for PoolKey;

    address constant CALLBACK_PROXY = 0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA;
    address constant V3_FACTORY = 0x0227628f3F023bb0B980b67D528571c95c6DaC1c;
    uint160 constant SQRT_PRICE_1_1 = 79228162514264337593543950336; // sqrt(1) * 2^96
    string constant STATE_FILE = "broadcast/v3-integration-state.json";

    // ═══════════════════════════════════════════════════════════════
    //  Phase 1: Deploy FRESH tokens + V3 pool + FCI + Callback
    // ═══════════════════════════════════════════════════════════════

    function deploy() public {
        Accounts memory accts = initAccounts(vm);

        vm.startBroadcast(accts.deployer.privateKey);

        // 1. Fresh mock tokens
        MockERC20 tokenA = new MockERC20("TestA", "TA", 18);
        MockERC20 tokenB = new MockERC20("TestB", "TB", 18);
        // Sort: token0 < token1
        (MockERC20 token0, MockERC20 token1) = address(tokenA) < address(tokenB)
            ? (tokenA, tokenB)
            : (tokenB, tokenA);

        // 2. Fresh V3 pool (fee=500, tickSpacing=10)
        address v3Pool = IUniswapV3Factory(V3_FACTORY).createPool(address(token0), address(token1), 500);
        IUniswapV3Pool(v3Pool).initialize(SQRT_PRICE_1_1);

        // 3. V3 CallbackRouter for mint/swap
        V3CallbackRouter router = new V3CallbackRouter();

        // 4. Mint tokens to deployer + LP
        uint256 supply = 1_000_000e18;
        token0.mint(accts.deployer.addr, supply);
        token1.mint(accts.deployer.addr, supply);
        token0.mint(accts.lpPassive.addr, supply);
        token1.mint(accts.lpPassive.addr, supply);

        // 5. Approve router
        token0.approve(address(router), type(uint256).max);
        token1.approve(address(router), type(uint256).max);

        vm.stopBroadcast();

        // LP approves router too
        vm.startBroadcast(accts.lpPassive.privateKey);
        token0.approve(address(router), type(uint256).max);
        token1.approve(address(router), type(uint256).max);
        vm.stopBroadcast();

        // 6. Deploy FCI V2 + Facet + Callback
        vm.startBroadcast(accts.deployer.privateKey);

        FeeConcentrationIndexV2 fci = new FeeConcentrationIndexV2();
        UniswapV3Facet facet = new UniswapV3Facet();
        // rvmId = reactiveDeployer (index 4) — matches the Lasna reactive deployer
        UniswapV3Callback callback = new UniswapV3Callback{value: 0.1 ether}(
            address(fci), CALLBACK_PROXY, accts.reactiveDeployer.addr
        );

        fci.initialize(accts.deployer.addr);
        fci.registerProtocolFacet(UNISWAP_V3_REACTIVE, IFCIProtocolFacet(address(facet)));
        fci.setFacetFci(UNISWAP_V3_REACTIVE, IFeeConcentrationIndex(address(fci)));
        fci.setFacetProtocolStateView(UNISWAP_V3_REACTIVE, IProtocolStateView(v3Pool));
        facet.initialize(
            accts.deployer.addr,
            IProtocolStateView(v3Pool),
            IFeeConcentrationIndex(address(fci)),
            IUnlockCallback(address(callback))
        );

        PoolKey memory poolKey = facet.listen(abi.encode(IUniswapV3Pool(v3Pool)));
        fci.initializeEpochPool(poolKey, UNISWAP_V3_REACTIVE, 86400);

        vm.stopBroadcast();

        // Write state
        string memory json = string.concat(
            '{"fci":"', vm.toString(address(fci)),
            '","facet":"', vm.toString(address(facet)),
            '","callback":"', vm.toString(address(callback)),
            '","v3Pool":"', vm.toString(v3Pool),
            '","router":"', vm.toString(address(router)),
            '","token0":"', vm.toString(address(token0)),
            '","token1":"', vm.toString(address(token1)),
            '","deployer":"', vm.toString(accts.deployer.addr),
            '"}'
        );
        vm.writeFile(STATE_FILE, json);
        console2.log("FCI:      %s", address(fci));
        console2.log("Callback: %s", address(callback));
        console2.log("V3 Pool:  %s", v3Pool);
        console2.log("Router:   %s", address(router));
    }

    // ═══════════════════════════════════════════════════════════════
    //  Phase 2: Mint 2 LPs + Swap
    // ═══════════════════════════════════════════════════════════════

    function mint() public {
        Accounts memory accts = initAccounts(vm);
        string memory stateJson = vm.readFile(STATE_FILE);
        address v3Pool = vm.parseJsonAddress(stateJson, ".v3Pool");
        address router = vm.parseJsonAddress(stateJson, ".router");
        IUniswapV3Pool pool = IUniswapV3Pool(v3Pool);

        vm.startBroadcast(accts.deployer.privateKey);
        // LP0: deployer, 1e18 at [-60, 60]
        V3CallbackRouter(router).mint(pool, accts.deployer.addr, -60, 60, 1e18);
        vm.stopBroadcast();

        vm.startBroadcast(accts.lpPassive.privateKey);
        // LP1: lpPassive, 2e18 at [-60, 60]
        V3CallbackRouter(router).mint(pool, accts.lpPassive.addr, -60, 60, 2e18);
        vm.stopBroadcast();

        // Swap (deployer, oneForZero, generates fees for both LPs)
        vm.startBroadcast(accts.deployer.privateKey);
        V3CallbackRouter(router).swap(
            pool, accts.deployer.addr, false, -1e16,
            1461446703485210103287273052203988822378723970341 // MAX_SQRT_RATIO - 1
        );
        vm.stopBroadcast();

        console2.log("Mints (1e18 + 2e18) + swap done");
    }

    // ═══════════════════════════════════════════════════════════════
    //  Phase 3: Burn both LPs
    // ═══════════════════════════════════════════════════════════════

    function burn() public {
        Accounts memory accts = initAccounts(vm);
        string memory stateJson = vm.readFile(STATE_FILE);
        address v3Pool = vm.parseJsonAddress(stateJson, ".v3Pool");

        vm.broadcast(accts.deployer.privateKey);
        IUniswapV3Pool(v3Pool).burn(-60, 60, 1e18);

        vm.broadcast(accts.lpPassive.privateKey);
        IUniswapV3Pool(v3Pool).burn(-60, 60, 2e18);

        console2.log("Burns (1e18 + 2e18) done");
    }

    // ═══════════════════════════════════════════════════════════════
    //  Phase 4: Verify all FCI metrics
    // ═══════════════════════════════════════════════════════════════

    function verify() public {
        string memory stateJson = vm.readFile(STATE_FILE);
        address fciAddr = vm.parseJsonAddress(stateJson, ".fci");
        address facetAddr = vm.parseJsonAddress(stateJson, ".facet");
        address v3Pool = vm.parseJsonAddress(stateJson, ".v3Pool");
        FeeConcentrationIndexV2 fci = FeeConcentrationIndexV2(fciAddr);
        PoolKey memory poolKey = _buildPoolKey(v3Pool, fciAddr);

        (uint128 indexA, uint256 thetaSum, uint256 removedPosCount) = fci.getIndex(poolKey, UNISWAP_V3_REACTIVE);
        uint128 deltaPlus = fci.getDeltaPlus(poolKey, UNISWAP_V3_REACTIVE);
        uint128 atNull = fci.getAtNull(poolKey, UNISWAP_V3_REACTIVE);
        uint256 thetaSumDirect = fci.getThetaSum(poolKey, UNISWAP_V3_REACTIVE);
        uint128 epochDeltaPlus = fci.getDeltaPlusEpoch(poolKey, UNISWAP_V3_REACTIVE);
        address registeredFacet = address(fci.getRegisteredProtocolFacet(UNISWAP_V3_REACTIVE));

        console2.log("removedPosCount: %d", removedPosCount);
        console2.log("deltaPlus:       %s", vm.toString(uint256(deltaPlus)));
        console2.log("epochDeltaPlus:  %s", vm.toString(uint256(epochDeltaPlus)));
        console2.log("indexA:          %s", vm.toString(uint256(indexA)));
        console2.log("atNull:          %s", vm.toString(uint256(atNull)));

        assertEq(removedPosCount, 2, "removedPosCount must be 2");
        assertGt(uint256(deltaPlus), 0, "deltaPlus must be > 0");
        assertEq(uint256(epochDeltaPlus), uint256(deltaPlus), "epoch must equal cumulative");
        assertEq(thetaSumDirect, thetaSum, "getThetaSum != getIndex().thetaSum");
        assertEq(registeredFacet, facetAddr, "facet mismatch");
        if (indexA > atNull) {
            assertEq(uint256(deltaPlus), uint256(indexA - atNull), "deltaPlus != indexA - atNull");
        }

        console2.log("=== ALL ASSERTIONS PASSED ===");
    }

    function _buildPoolKey(address v3Pool, address fci) internal view returns (PoolKey memory) {
        return PoolKey({
            currency0: Currency.wrap(IUniswapV3Pool(v3Pool).token0()),
            currency1: Currency.wrap(IUniswapV3Pool(v3Pool).token1()),
            fee: IUniswapV3Pool(v3Pool).fee(),
            tickSpacing: IUniswapV3Pool(v3Pool).tickSpacing(),
            hooks: IHooks(fci)
        });
    }
}
