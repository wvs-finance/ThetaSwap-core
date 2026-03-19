// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {FCIDifferentialBase, FCIContext} from "./FCIDifferentialBase.sol";

/// @title FCI V1 vs V2 Differential Test
/// @notice Runs identical scenarios on V1 and V2, asserts same FCI state.
contract FCIV1DiffFCIV2Test is FCIDifferentialBase {

    address lp2;

    function setUp() public override {
        super.setUp();
        lp2 = makeAddr("lp2");
        seedBalance(lp2);
        approvePosmFor(lp2);
        seedBalance(fciLP);
        approvePosmFor(fciLP);
    }

    // ── US3-A: sole provider, no swaps ──

    function test_diff_soleProvider_noSwaps() public {
        uint256 tidV1 = _mint(ctxV1, -60, 60, 1e18);
        uint256 tidV2 = _mint(ctxV2, -60, 60, 1e18);

        _burn(ctxV1, tidV1, -60, 60, 1e18);
        _burn(ctxV2, tidV2, -60, 60, 1e18);

        _assertStateEqual();
    }

    // ── US3-B: sole provider, one swap ──

    function test_diff_soleProvider_oneSwap() public {
        uint256 tidV1 = _mint(ctxV1, -60, 60, 1e18);
        uint256 tidV2 = _mint(ctxV2, -60, 60, 1e18);

        _doSwap(ctxV1, true, -100);
        _doSwap(ctxV2, true, -100);

        _burn(ctxV1, tidV1, -60, 60, 1e18);
        _burn(ctxV2, tidV2, -60, 60, 1e18);

        _assertStateEqual();
    }

    // ── US3-C: two equal LPs, one swap ──

    function test_diff_twoEqualLps_oneSwap() public {
        uint256 t1V1 = _mint(ctxV1, -60, 60, 1e18);
        uint256 t2V1 = _mintAs(ctxV1, lp2, -60, 60, 1e18);
        uint256 t1V2 = _mint(ctxV2, -60, 60, 1e18);
        uint256 t2V2 = _mintAs(ctxV2, lp2, -60, 60, 1e18);

        _doSwap(ctxV1, true, -100);
        _doSwap(ctxV2, true, -100);

        _burn(ctxV1, t1V1, -60, 60, 1e18);
        _burnAs(ctxV1, lp2, t2V1, -60, 60, 1e18);
        _burn(ctxV2, t1V2, -60, 60, 1e18);
        _burnAs(ctxV2, lp2, t2V2, -60, 60, 1e18);

        _assertStateEqual();
    }

    // ── US3-D: two unequal LPs, one swap ──

    function test_diff_twoUnequalLps_oneSwap() public {
        uint256 t1V1 = _mint(ctxV1, -60, 60, 1e18);
        uint256 t2V1 = _mintAs(ctxV1, lp2, -60, 60, 2e18);
        uint256 t1V2 = _mint(ctxV2, -60, 60, 1e18);
        uint256 t2V2 = _mintAs(ctxV2, lp2, -60, 60, 2e18);

        _doSwap(ctxV1, true, -100);
        _doSwap(ctxV2, true, -100);

        _burn(ctxV1, t1V1, -60, 60, 1e18);
        _burnAs(ctxV1, lp2, t2V1, -60, 60, 2e18);
        _burn(ctxV2, t1V2, -60, 60, 1e18);
        _burnAs(ctxV2, lp2, t2V2, -60, 60, 2e18);

        _assertStateEqual();
    }

    // ── US3-E: equal capital, different durations ──

    function test_diff_equalCapital_durationHeterogeneous() public {
        uint256 t1V1 = _mint(ctxV1, -60, 60, 1e18);
        uint256 t2V1 = _mintAs(ctxV1, lp2, -60, 60, 1e18);
        uint256 t1V2 = _mint(ctxV2, -60, 60, 1e18);
        uint256 t2V2 = _mintAs(ctxV2, lp2, -60, 60, 1e18);

        vm.roll(block.number + 1);
        _doSwap(ctxV1, true, -100);
        _doSwap(ctxV2, true, -100);

        vm.roll(block.number + 1);
        _burn(ctxV1, t1V1, -60, 60, 1e18);
        _burn(ctxV2, t1V2, -60, 60, 1e18);

        vm.roll(block.number + 1);
        _doSwap(ctxV1, false, -100);
        _doSwap(ctxV2, false, -100);

        vm.roll(block.number + 1);
        _burnAs(ctxV1, lp2, t2V1, -60, 60, 1e18);
        _burnAs(ctxV2, lp2, t2V2, -60, 60, 1e18);

        _assertStateEqual();
    }
}
