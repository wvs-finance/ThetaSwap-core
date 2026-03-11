// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test, console2} from "forge-std/Test.sol";
import {Hooks} from "v4-core/src/libraries/Hooks.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {SwapParams} from "v4-core/src/types/PoolOperation.sol";
import {PoolSwapTest} from "v4-core/src/test/PoolSwapTest.sol";

import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";
import {Actions} from "@uniswap/v4-periphery/src/libraries/Actions.sol";
import {Planner, Plan} from "@uniswap/v4-periphery/test/shared/Planner.sol";

import {IAllowanceTransfer} from "permit2/src/interfaces/IAllowanceTransfer.sol";
import {MockERC20} from "solmate/src/test/utils/mocks/MockERC20.sol";

import {FeeConcentrationIndex} from "@fee-concentration-index/FeeConcentrationIndex.sol";

/// @title DifferentialFCI Fork Test
/// @notice Dry-runs the full deploy + build pipeline on forked Unichain Sepolia state.
///         Validates the V4 local FCI hook path end-to-end: deploy tokens, mine hook
///         address, deploy FCI, init pool, run equilibrium scenario, assert deltaPlus = 0.
contract DifferentialFCIForkTest is Test {
    using PoolIdLibrary for PoolKey;
    using Planner for Plan;

    // ── Unichain Sepolia addresses ──
    address constant POOL_MANAGER = 0x00B036B58a818B1BC34d502D3fE730Db729e62AC;
    address constant POSITION_MANAGER = 0xf969Aee60879C54bAAed9F3eD26147Db216Fd664;
    address constant SWAP_ROUTER = 0x9140a78c1A137c7fF1c151EC8231272aF78a99A4;
    address constant PERMIT2 = 0x000000000022D473030F116dDEE9F6B43aC78BA3;

    // ── Pool parameters (from Constants.sol) ──
    int24 constant TICK_LOWER = -60;
    int24 constant TICK_UPPER = 60;
    uint24 constant TICK_SPACING = 10;
    int256 constant AMOUNT_SPECIFIED = 100;
    bool constant ZERO_FOR_ONE = true;
    uint48 constant DEADLINE = type(uint48).max - 1;
    uint160 constant SQRT_PRICE_1_1 = 79228162514264337593543950336;

    // ── Slippage bounds ──
    uint128 constant MAX_SLIPPAGE = type(uint128).max;
    uint128 constant MIN_SLIPPAGE = 0;

    // ── State ──
    IPoolManager poolManager;
    IPositionManager posMgr;
    PoolSwapTest swapRouter;

    MockERC20 tokenA;
    MockERC20 tokenB;
    Currency currency0;
    Currency currency1;

    FeeConcentrationIndex fci;
    PoolKey key;
    PoolId poolId;

    address deployer;
    address lpPassive;
    address lpSophisticated;
    address swapper;

    function setUp() public {
        vm.createSelectFork(vm.rpcUrl("unichain_sepolia"));

        poolManager = IPoolManager(POOL_MANAGER);
        posMgr = IPositionManager(POSITION_MANAGER);
        swapRouter = PoolSwapTest(SWAP_ROUTER);

        deployer = makeAddr("deployer");
        lpPassive = makeAddr("lpPassive");
        lpSophisticated = makeAddr("lpSophisticated");
        swapper = makeAddr("swapper");

        // ── 1. Deploy mock tokens ──
        vm.startPrank(deployer);
        tokenA = new MockERC20("Token A", "TKA", 18);
        tokenB = new MockERC20("Token B", "TKB", 18);
        vm.stopPrank();

        // Sort currencies: currency0 < currency1
        if (address(tokenA) < address(tokenB)) {
            currency0 = Currency.wrap(address(tokenA));
            currency1 = Currency.wrap(address(tokenB));
        } else {
            currency0 = Currency.wrap(address(tokenB));
            currency1 = Currency.wrap(address(tokenA));
        }

        // ── 2. Deploy FCI at a mined hook address ──
        uint160 flags = uint160(
            Hooks.AFTER_ADD_LIQUIDITY_FLAG
                | Hooks.BEFORE_SWAP_FLAG
                | Hooks.AFTER_SWAP_FLAG
                | Hooks.BEFORE_REMOVE_LIQUIDITY_FLAG
                | Hooks.AFTER_REMOVE_LIQUIDITY_FLAG
        );

        bytes memory constructorArgs = abi.encode(POOL_MANAGER);
        (address hookAddress, bytes32 salt) =
            _findHookSalt(address(this), flags, type(FeeConcentrationIndex).creationCode, constructorArgs);

        fci = new FeeConcentrationIndex{salt: salt}(POOL_MANAGER);
        require(address(fci) == hookAddress, "hook address mismatch");

        // ── 3. Initialize pool ──
        key = PoolKey({
            currency0: currency0,
            currency1: currency1,
            fee: 500,
            tickSpacing: int24(TICK_SPACING),
            hooks: IHooks(address(fci))
        });
        poolId = key.toId();

        poolManager.initialize(key, SQRT_PRICE_1_1);

        // ── 4. Fund test accounts ──
        uint256 supply = 100e18;
        _fundAccount(lpPassive, supply);
        _fundAccount(lpSophisticated, supply);
        _fundAccount(swapper, supply);

        // ── 5. Approve tokens through Permit2 to PositionManager ──
        _approvePermit2(lpPassive);
        _approvePermit2(lpSophisticated);

        // Swapper needs to approve tokens directly to the SwapRouter
        _approveSwapRouter(swapper);
    }

    // ═══════════════════════════════════════════════════════════════════
    // Test: Equilibrium scenario — deltaPlus must be 0
    //
    // mint A (1e18), mint B (1e18), swap, burn B, burn A
    // Both LPs have equal capital and same lifetime => deltaPlus = 0
    // ═══════════════════════════════════════════════════════════════════

    function test_fork_equilibrium_deltaPlusMustBeZero() public {
        uint256 liquidity = 1e18;

        // ── Mint A (lpPassive) ──
        uint256 tokenIdA = posMgr.nextTokenId();
        bytes memory mintA = _encodeMint(key, liquidity, lpPassive);
        vm.prank(lpPassive);
        posMgr.modifyLiquidities(mintA, DEADLINE);

        // ── Mint B (lpSophisticated) ──
        uint256 tokenIdB = posMgr.nextTokenId();
        bytes memory mintB = _encodeMint(key, liquidity, lpSophisticated);
        vm.prank(lpSophisticated);
        posMgr.modifyLiquidities(mintB, DEADLINE);

        // ── Swap ──
        vm.prank(swapper);
        swapRouter.swap(
            key,
            SwapParams({
                zeroForOne: ZERO_FOR_ONE,
                amountSpecified: AMOUNT_SPECIFIED,
                sqrtPriceLimitX96: TickMath.MIN_SQRT_PRICE + 1
            }),
            PoolSwapTest.TestSettings({takeClaims: false, settleUsingBurn: false}),
            ""
        );

        // ── Burn B (lpSophisticated) ──
        _burnPosition(lpSophisticated, tokenIdB, liquidity);

        // ── Burn A (lpPassive) ──
        _burnPosition(lpPassive, tokenIdA, liquidity);

        // ── Assert deltaPlus = 0 ──
        uint128 deltaPlus = fci.getDeltaPlus(key, false);
        assertEq(deltaPlus, 0, "deltaPlus must be 0: equilibrium scenario");

        // Log for visibility
        console2.log("deltaPlus (V4 path) =", uint256(deltaPlus));
    }

    // ═══════════════════════════════════════════════════════════════════
    // Internal helpers
    // ═══════════════════════════════════════════════════════════════════

    /// @dev Mint tokens and approve through ERC20 -> Permit2 -> PositionManager chain
    function _fundAccount(address account, uint256 amount) internal {
        vm.startPrank(deployer);
        MockERC20(Currency.unwrap(currency0)).mint(account, amount);
        MockERC20(Currency.unwrap(currency1)).mint(account, amount);
        vm.stopPrank();
    }

    /// @dev Approve tokens: account -> Permit2 (ERC20 approve), then Permit2 -> PositionManager
    function _approvePermit2(address account) internal {
        vm.startPrank(account);

        // ERC20 approve to Permit2
        MockERC20(Currency.unwrap(currency0)).approve(PERMIT2, type(uint256).max);
        MockERC20(Currency.unwrap(currency1)).approve(PERMIT2, type(uint256).max);

        // Permit2 allowance to PositionManager
        IAllowanceTransfer(PERMIT2).approve(
            Currency.unwrap(currency0), POSITION_MANAGER, type(uint160).max, type(uint48).max
        );
        IAllowanceTransfer(PERMIT2).approve(
            Currency.unwrap(currency1), POSITION_MANAGER, type(uint160).max, type(uint48).max
        );

        vm.stopPrank();
    }

    /// @dev Approve tokens directly to PoolSwapTest (swapper does not go through Permit2)
    function _approveSwapRouter(address account) internal {
        vm.startPrank(account);
        MockERC20(Currency.unwrap(currency0)).approve(SWAP_ROUTER, type(uint256).max);
        MockERC20(Currency.unwrap(currency1)).approve(SWAP_ROUTER, type(uint256).max);
        vm.stopPrank();
    }

    /// @dev Encode a MINT_POSITION action via Planner
    function _encodeMint(PoolKey memory k, uint256 liquidity, address recipient)
        internal
        pure
        returns (bytes memory)
    {
        Plan memory planner = Planner.init();
        planner.add(
            Actions.MINT_POSITION,
            abi.encode(k, TICK_LOWER, TICK_UPPER, liquidity, MAX_SLIPPAGE, MAX_SLIPPAGE, recipient, "")
        );
        return planner.finalizeModifyLiquidityWithClose(k);
    }

    /// @dev Encode a DECREASE_LIQUIDITY action via Planner
    function _encodeDecrease(PoolKey memory k, uint256 tokenId, uint256 liquidity)
        internal
        pure
        returns (bytes memory)
    {
        Plan memory planner = Planner.init();
        planner.add(
            Actions.DECREASE_LIQUIDITY,
            abi.encode(tokenId, liquidity, MIN_SLIPPAGE, MIN_SLIPPAGE, "")
        );
        return planner.finalizeModifyLiquidityWithClose(k);
    }

    /// @dev Encode a BURN_POSITION action via Planner
    function _encodeBurn(PoolKey memory k, uint256 tokenId)
        internal
        pure
        returns (bytes memory)
    {
        Plan memory planner = Planner.init();
        planner.add(Actions.BURN_POSITION, abi.encode(tokenId, MIN_SLIPPAGE, MIN_SLIPPAGE, ""));
        return planner.finalizeModifyLiquidityWithClose(k);
    }

    /// @dev Decrease liquidity then burn position (two-step)
    function _burnPosition(address lp, uint256 tokenId, uint256 liquidity) internal {
        vm.startPrank(lp);
        posMgr.modifyLiquidities(_encodeDecrease(key, tokenId, liquidity), DEADLINE);
        posMgr.modifyLiquidities(_encodeBurn(key, tokenId), DEADLINE);
        vm.stopPrank();
    }

    // ═══════════════════════════════════════════════════════════════════
    // HookMiner — inlined to avoid import-path issues across lib versions
    // ═══════════════════════════════════════════════════════════════════

    uint160 constant FLAG_MASK = Hooks.ALL_HOOK_MASK;
    uint256 constant MAX_LOOP = 160_444;

    function _findHookSalt(
        address deployer_,
        uint160 flags,
        bytes memory creationCode,
        bytes memory constructorArgs
    ) internal view returns (address hookAddress, bytes32 salt) {
        flags = flags & FLAG_MASK;
        bytes memory creationCodeWithArgs = abi.encodePacked(creationCode, constructorArgs);
        bytes32 initCodeHash = keccak256(creationCodeWithArgs);

        for (uint256 s; s < MAX_LOOP; s++) {
            hookAddress = address(
                uint160(
                    uint256(
                        keccak256(
                            abi.encodePacked(bytes1(0xFF), deployer_, bytes32(s), initCodeHash)
                        )
                    )
                )
            );
            if (uint160(hookAddress) & FLAG_MASK == flags && hookAddress.code.length == 0) {
                return (hookAddress, bytes32(s));
            }
        }
        revert("HookMiner: could not find salt");
    }
}
