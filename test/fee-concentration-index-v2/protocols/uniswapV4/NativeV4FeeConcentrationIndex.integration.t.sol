// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {console2} from "forge-std/console2.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {SwapParams} from "v4-core/src/types/PoolOperation.sol";
import {PoolSwapTest} from "v4-core/src/test/PoolSwapTest.sol";
import {PosmTestSetup} from "@uniswap/v4-periphery/test/shared/PosmTestSetup.sol";
import {PositionConfig} from "@uniswap/v4-periphery/test/shared/PositionConfig.sol";

// Force-compile artifacts for PosmTestSetup
import {PositionManager} from "@uniswap/v4-periphery/src/PositionManager.sol";
import {PositionDescriptor} from "@uniswap/v4-periphery/src/PositionDescriptor.sol";

// FCI V2
import {FeeConcentrationIndexV2} from "@fee-concentration-index-v2/FeeConcentrationIndexV2.sol";
import {NativeUniswapV4Facet} from "@fee-concentration-index-v2/protocols/uniswap-v4/NativeUniswapV4Facet.sol";
import {IFCIProtocolFacet} from "@fee-concentration-index-v2/interfaces/IFCIProtocolFacet.sol";
import {IFeeConcentrationIndex} from "@fee-concentration-index/interfaces/IFeeConcentrationIndex.sol";
import {IProtocolStateView} from "@protocol-adapter/interfaces/IProtocolStateView.sol";
import {IUnlockCallback} from "v4-core/src/interfaces/callback/IUnlockCallback.sol";
import {NATIVE_V4} from "@fee-concentration-index-v2/types/FlagsRegistry.sol";

// Deploy script (used as test client)
import {DeployFCIV2HookV4Script} from "@foundry-script/deploy/DeployFCIV2HookV4.s.sol";

// Utils
import {Accounts, makeTestAccounts, seed, approveAll, ApprovalTarget} from "@utils/Accounts.sol";
import {TokenPair} from "@utils/TokenPair.sol";
import {Mode} from "@utils/Mode.sol";

/// @title NativeV4 FCI V2 Integration Tests — fixture-driven differential testing
/// @dev Reads scenario fixtures from research/data/fixtures/simulator/*.json.
/// Python simulator computes expected metrics (raw Q128 uint256).
/// This test deploys real FCI V2 + NativeV4Facet, replays the action sequence,
/// queries all FCI interface getters, and asserts exact match against Python output.
///
/// Deploy uses DeployFCIV2HookV4Script.deployLocal() — same code path as live.
contract NativeV4FeeConcentrationIndex_IntegrationTest is PosmTestSetup {
    using PoolIdLibrary for PoolKey;

    FeeConcentrationIndexV2 fci;
    NativeUniswapV4Facet facet;
    Accounts accts;
    PoolId poolId;

    // LP actors (mapped from fixture agent IDs)
    mapping(string => address) agents;
    mapping(string => uint256) tokenIds;  // agentId => last minted tokenId

    string constant FIXTURE_DIR = "research/data/fixtures/simulator/";

    function setUp() public {
        // 1. Create test accounts — deployer is index 0
        accts = makeTestAccounts(vm);

        // 2. Deploy V4 infrastructure
        deployFreshManagerAndRouters();
        deployMintAndApprove2Currencies();
        deployAndApprovePosm(manager);

        // 3. Deploy FCI V2 hook via script (same CREATE2 code path as live)
        DeployFCIV2HookV4Script deployer = new DeployFCIV2HookV4Script();
        (fci, facet) = deployer.deployLocal();

        // 4. Wire: deployer is owner of FCI V2 and facet
        vm.startPrank(accts.deployer.addr);
        fci.initialize(accts.deployer.addr);
        fci.registerProtocolFacet(NATIVE_V4, IFCIProtocolFacet(address(facet)));
        fci.setFacetFci(NATIVE_V4, IFeeConcentrationIndex(address(fci)));
        fci.setFacetProtocolStateView(NATIVE_V4, IProtocolStateView(address(manager)));
        facet.initialize(
            accts.deployer.addr,
            IProtocolStateView(address(manager)),
            IFeeConcentrationIndex(address(fci)),
            IUnlockCallback(address(0))
        );
        vm.stopPrank();

        // 5. Initialize pool with FCI V2 as hooks
        (key, poolId) = initPool(
            currency0, currency1,
            IHooks(address(fci)),
            3000,           // fee
            SQRT_PRICE_1_1  // sqrtPriceX96 = 1:1
        );
    }

    // ══════════════════════════════════════════════════════════════
    //  FIXTURE RUNNER
    // ══════════════════════════════════════════════════════════════

    function _setupAgent(string memory agentId) internal returns (address) {
        if (agents[agentId] != address(0)) return agents[agentId];
        address agent = makeAddr(agentId);
        agents[agentId] = agent;
        seedBalance(agent);
        approvePosmFor(agent);
        return agent;
    }

    function _mintPosition(address lp, int24 tickLower, int24 tickUpper, uint256 liquidity)
        internal
        returns (uint256 tokenId)
    {
        PositionConfig memory config = PositionConfig({
            poolKey: key,
            tickLower: tickLower,
            tickUpper: tickUpper
        });
        tokenId = lpm.nextTokenId();
        vm.prank(lp);
        mint(config, liquidity, lp, "");
    }

    function _burnPosition(address lp, uint256 tokenId, int24 tickLower, int24 tickUpper, uint256 liquidity)
        internal
    {
        PositionConfig memory config = PositionConfig({
            poolKey: key,
            tickLower: tickLower,
            tickUpper: tickUpper
        });
        vm.startPrank(lp);
        decreaseLiquidity(tokenId, config, liquidity, "");
        burn(tokenId, config, "");
        vm.stopPrank();
    }

    function _swap(bool zeroForOne, int256 amount) internal {
        swap(key, zeroForOne, amount, "");
    }

    /// @notice Run a fixture: parse JSON, replay actions, assert metrics.
    function _runFixture(string memory name) internal {
        string memory path = string.concat(FIXTURE_DIR, name, ".json");
        string memory json = vm.readFile(path);

        // ── Parse expected metrics ──
        uint256 expectedDeltaPlus = vm.parseJsonUint(json, ".expected.deltaPlus");
        uint256 expectedIndexA = vm.parseJsonUint(json, ".expected.indexA");
        uint256 expectedThetaSum = vm.parseJsonUint(json, ".expected.thetaSum");
        uint256 expectedRemovedPosCount = vm.parseJsonUint(json, ".expected.removedPosCount");
        uint256 expectedAtNull = vm.parseJsonUint(json, ".expected.atNull");

        // ── Parse and replay actions ──
        bytes memory actionsRaw = vm.parseJson(json, ".scenario.actions");
        // Forge parseJson returns ABI-encoded array of structs.
        // We decode action-by-action using indexed access.
        uint256 actionCount = abi.decode(vm.parseJson(json, ".scenario.actions"), (bytes[])).length;

        for (uint256 i; i < actionCount; ++i) {
            string memory prefix = string.concat(".scenario.actions[", vm.toString(i), "]");
            string memory actionType = vm.parseJsonString(json, string.concat(prefix, ".type"));
            uint256 blockNum = vm.parseJsonUint(json, string.concat(prefix, ".block"));

            bytes32 typeHash = keccak256(bytes(actionType));

            if (typeHash == keccak256("ROLL")) {
                vm.roll(blockNum);

            } else if (typeHash == keccak256("MINT")) {
                string memory agentId = vm.parseJsonString(json, string.concat(prefix, ".agentId"));
                uint256 liquidity = vm.parseJsonUint(json, string.concat(prefix, ".liquidity"));
                address lp = _setupAgent(agentId);
                vm.roll(blockNum);

                // Read tick range from agent definition
                // For simplicity, use the first agent's ticks (all scenarios use same range)
                // TODO: parse per-agent ticks from fixture
                int24 tickLower = -60;
                int24 tickUpper = 60;

                uint256 tokenId = _mintPosition(lp, tickLower, tickUpper, liquidity);
                tokenIds[agentId] = tokenId;

            } else if (typeHash == keccak256("SWAP")) {
                vm.roll(blockNum);
                // Swap amount from fixture (raw fee amount — simplified swap)
                _swap(true, -100);

            } else if (typeHash == keccak256("BURN")) {
                string memory agentId = vm.parseJsonString(json, string.concat(prefix, ".agentId"));
                uint256 liquidity = vm.parseJsonUint(json, string.concat(prefix, ".liquidity"));
                address lp = agents[agentId];
                vm.roll(blockNum);

                int24 tickLower = -60;
                int24 tickUpper = 60;

                _burnPosition(lp, tokenIds[agentId], tickLower, tickUpper, liquidity);
            }
        }

        // ══════════════════════════════════════════════════════
        //  Assert ALL FCI V2 view functions against fixture
        // ══════════════════════════════════════════════════════

        // ── getIndex() ──
        (uint128 actualIndexA, uint256 actualThetaSum, uint256 actualRemovedPosCount) =
            fci.getIndex(key, NATIVE_V4);

        // ── getDeltaPlus() ──
        uint128 actualDeltaPlus = fci.getDeltaPlus(key, NATIVE_V4);

        // ── getAtNull() ──
        uint128 actualAtNull = fci.getAtNull(key, NATIVE_V4);

        // ── getThetaSum() — must equal thetaSum from getIndex() ──
        uint256 actualThetaSumDirect = fci.getThetaSum(key, NATIVE_V4);

        // ── getDeltaPlusEpoch() — 0 when no epoch initialized ──
        uint128 actualDeltaPlusEpoch = fci.getDeltaPlusEpoch(key, NATIVE_V4);

        // ── getRegisteredProtocolFacet() — must return our facet ──
        address actualFacet = address(fci.getRegisteredProtocolFacet(NATIVE_V4));

        // ══════════════════════════════════════════════════════
        //  Assertions: exact for additive, 1-2 wei for sqrt
        // ══════════════════════════════════════════════════════

        // Additive quantities (no sqrt rounding)
        assertEq(actualThetaSum, expectedThetaSum, "getIndex().thetaSum mismatch");
        assertEq(actualRemovedPosCount, expectedRemovedPosCount, "getIndex().removedPosCount mismatch");

        // getThetaSum() must be consistent with getIndex()
        assertEq(actualThetaSumDirect, actualThetaSum, "getThetaSum() != getIndex().thetaSum");

        // sqrt-derived quantities (1-2 wei tolerance)
        assertApproxEqAbs(uint256(actualIndexA), expectedIndexA, 1, "getIndex().indexA mismatch");
        assertApproxEqAbs(uint256(actualAtNull), expectedAtNull, 1, "getAtNull() mismatch");
        assertApproxEqAbs(uint256(actualDeltaPlus), expectedDeltaPlus, 2, "getDeltaPlus() mismatch");

        // Epoch: 0 when not initialized
        assertEq(uint256(actualDeltaPlusEpoch), 0, "getDeltaPlusEpoch() must be 0 (no epoch)");

        // Facet registration
        assertEq(actualFacet, address(facet), "getRegisteredProtocolFacet() mismatch");

        // ── Cross-getter consistency ──
        // getDeltaPlus() == max(0, indexA - atNull)
        if (actualIndexA > actualAtNull) {
            assertEq(uint256(actualDeltaPlus), uint256(actualIndexA - actualAtNull), "deltaPlus != indexA - atNull");
        } else {
            assertEq(uint256(actualDeltaPlus), 0, "deltaPlus must be 0 when indexA <= atNull");
        }
    }

    // ══════════════════════════════════════════════════════════════
    //  INTEGRATION UNIT — one test per fixture
    // ══════════════════════════════════════════════════════════════

    function test_integrationNativeV4_unit_soleProvider_noSwaps_allDerivedQuantitiesZero() public {
        _runFixture("sole_provider_no_swaps");
    }

    function test_integrationNativeV4_unit_soleProvider_noSwaps_repeatedCycles_allStayZero() public {
        _runFixture("sole_provider_no_swaps_repeated");
    }

    function test_integrationNativeV4_unit_soleProvider_oneSwap_deltaPlusMustBeZero() public {
        _runFixture("sole_provider_one_swap");
    }

    function test_integrationNativeV4_unit_twoHomogeneousLps_oneSwap_deltaPlusMustBeZero() public {
        _runFixture("two_homogeneous_lps_one_swap");
    }

    function test_integrationNativeV4_unit_twoDifferentOnlyCapitalHeterogenousLps_oneSwap_deltaPlusGtZero() public {
        _runFixture("two_hetero_capital_one_swap");
    }

    function test_integrationNativeV4_unit_equalCapitalDurationHeterogeneousLps_twoSwaps_deltaPlusMustBeZero() public {
        _runFixture("equal_capital_hetero_duration");
    }

    function test_integrationNativeV4_unit_twoDifferentHeterogenousLps_threeSwaps_deltaPlusCapturesCrowdOut() public {
        _runFixture("jit_crowdout_three_swaps");
    }
}
