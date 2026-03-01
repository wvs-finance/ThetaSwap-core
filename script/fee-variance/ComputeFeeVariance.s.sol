// SPDX-License-Identifier: MIT
pragma solidity >=0.7.5 <0.9.0;
pragma abicoder v2;

import "forge-std/Script.sol";
import "../src/FeeVariance.sol";
import "@uniswap/v3-periphery/contracts/interfaces/INonfungiblePositionManager.sol";
import "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";

contract ComputeFeeVariance is Script {
    INonfungiblePositionManager constant NPM =
        INonfungiblePositionManager(0xC36442b4a4522E871399CD717aBDD847Ab11FE88);
    IUniswapV3Pool constant POOL =
        IUniswapV3Pool(0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640);

    function run() external {
        // Read tokenIds from FFI (position_registry.csv)
        string[] memory cmd = new string[](3);
        cmd[0] = "bash";
        cmd[1] = "-c";
        cmd[2] = "cut -d',' -f1 ../../data/position_registry.csv | tail -n +2 | tr '\\n' ','";
        bytes memory result = vm.ffi(cmd);

        // Parse comma-separated tokenIds
        uint256[] memory tokenIds = _parseTokenIds(string(result));

        // Compute fee variance at current fork block
        (uint256 varianceX128, uint256 numPositions) = FeeVariance.compute(
            NPM, POOL, tokenIds
        );

        // Emit results for the Python driver to parse
        console.log("FeeVariance:", varianceX128);
        console.log("Positions:", numPositions);
    }

    function _parseTokenIds(string memory csv) internal pure returns (uint256[] memory) {
        bytes memory b = bytes(csv);
        uint256 count = 0;
        for (uint256 i = 0; i < b.length; i++) {
            if (b[i] == ",") count++;
        }
        // Account for last element if no trailing comma
        if (b.length > 0 && b[b.length - 1] != ",") count++;
        if (count == 0) return new uint256[](0);

        uint256[] memory ids = new uint256[](count);
        uint256 idx = 0;
        uint256 num = 0;
        bool hasNum = false;

        for (uint256 i = 0; i < b.length; i++) {
            if (b[i] == "," || b[i] == "\n") {
                if (hasNum) {
                    ids[idx++] = num;
                    num = 0;
                    hasNum = false;
                }
            } else if (uint8(b[i]) >= 48 && uint8(b[i]) <= 57) {
                num = num * 10 + (uint8(b[i]) - 48);
                hasNum = true;
            }
        }
        // Last element
        if (hasNum && idx < count) {
            ids[idx++] = num;
        }

        // Trim to actual count
        uint256[] memory trimmed = new uint256[](idx);
        for (uint256 i = 0; i < idx; i++) {
            trimmed[i] = ids[i];
        }
        return trimmed;
    }
}
