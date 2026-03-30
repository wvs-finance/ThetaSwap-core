// SPDX-License-Identifier: BUSL-1.1
pragma solidity >=0.8.20;



import '@cryptoalgebra/integral-core/contracts/interfaces/IAlgebraFactory.sol';
import '@cryptoalgebra/integral-core/contracts/interfaces/IAlgebraPool.sol';
import '@cryptoalgebra/integral-base-plugin/contracts/interfaces/plugins/IAlgebraStubPlugin.sol';
import '@cryptoalgebra/integral-core/contracts/libraries/Plugins.sol';
import '@cryptoalgebra/integral-core/contracts/interfaces/plugin/IAlgebraPlugin.sol';
import './libraries/FeeRevenuePerLiquidityX96Lib.sol';
import '@cryptoalgebra/integral-core/contracts/libraries/TickMath.sol';
import '@cryptoalgebra/integral-base-plugin/contracts/libraries/VolatilityOracle.sol';

uint256 constant UINT16_MODULO = 65536;

using VolatilityOracle for VolatilityOracle.Timepoint[UINT16_MODULO];

struct AlgebraFlairOracleStorage{
    VolatilityOracle.Timepoint[UINT16_MODULO] timepoints;
    bool isInitialized;
    uint8 pluginConfig;
    uint16 timepointIndex;
    uint32 lastTimepointTimestamp;
    uint160 feeRevenuePerLiquidityX96;
    address pool;
}

// @dev: keccak256('algebraFlairOracle.storage) 
bytes32 constant ALGEBRA_FLAIR_ORACLE_STORAGE_SLOT = 0x75e519346134d659beaab087003bdde14b11ca77c605cbb6991f8db3886da5b6;

function getAlgebraFlairOracleStorage() pure returns(AlgebraFlairOracleStorage storage $){
    bytes32 pos = ALGEBRA_FLAIR_ORACLE_STORAGE_SLOT;
    assembly("memory-safe"){
        $.slot := pos
    }
}

function getTimepoints() view returns (VolatilityOracle.Timepoint[UINT16_MODULO] storage){
    AlgebraFlairOracleStorage storage $ = getAlgebraFlairOracleStorage();
    return $.timepoints;
}

function writeTimepoint(int24 tick) {
    // single SLOAD
    uint16 _lastIndex = getTimepointIndex();
    uint32 _lastTimepointTimestamp = getLastTimepointTimestamp();
    bool _isInitialized = isInitialized();
    require(_isInitialized, 'Not initialized');

    uint32 currentTimestamp = uint32(block.timestamp);

    if (_lastTimepointTimestamp == currentTimestamp) return;

    (uint16 newLastIndex, uint16 newOldestIndex) = getTimepoints().write(
									_lastIndex,
									currentTimestamp,
									tick
    );

    setTimepointIndex(newLastIndex);
    setLastTimepointTimestamp(currentTimestamp);
}


function setPluginConfig(uint8 config) {
    AlgebraFlairOracleStorage storage $ = getAlgebraFlairOracleStorage();
    $.pluginConfig = config;
}

function getPluginConfig() view returns(uint8 config){
    AlgebraFlairOracleStorage storage $ = getAlgebraFlairOracleStorage();
    config = $.pluginConfig;
}

function setPool(IAlgebraPool pool) {
    AlgebraFlairOracleStorage storage $ = getAlgebraFlairOracleStorage();
    $.pool = address(pool);
}

function getPool() view returns(address){
    AlgebraFlairOracleStorage storage $ = getAlgebraFlairOracleStorage();
    return $.pool;
}

function getPluginInPool() view returns (address){
    return IAlgebraPool(getPool()).plugin();
}

function setFeeRevenuePerLiquidityX96(uint160 feeRevenuePerLiquidityX96) {
    AlgebraFlairOracleStorage storage $ = getAlgebraFlairOracleStorage();
    $.feeRevenuePerLiquidityX96 = feeRevenuePerLiquidityX96;
}

function getFeeRevenuePerLiquidityX96() view returns(uint160 feeRevenuePerLiquidityX96){
    AlgebraFlairOracleStorage storage $ = getAlgebraFlairOracleStorage();
    feeRevenuePerLiquidityX96 = $.feeRevenuePerLiquidityX96;
}

function _setInitialized() {
    AlgebraFlairOracleStorage storage $ = getAlgebraFlairOracleStorage();
    $.isInitialized = true;
}

function isInitialized() view returns (bool){
     AlgebraFlairOracleStorage storage $ = getAlgebraFlairOracleStorage();
     return $.isInitialized;
}

function getLastTimepointTimestamp() view returns(uint32){
    AlgebraFlairOracleStorage storage $ = getAlgebraFlairOracleStorage();
    return $.lastTimepointTimestamp;
}

function getTimepointIndex() view returns (uint16) {
    AlgebraFlairOracleStorage storage $ = getAlgebraFlairOracleStorage();
    return $.timepointIndex;
}

function setTimepointIndex(uint16 _index) {
    AlgebraFlairOracleStorage storage $ = getAlgebraFlairOracleStorage();
    $.timepointIndex = _index;
}

function setLastTimepointTimestamp(uint32 _timepoint) {
    AlgebraFlairOracleStorage storage $ = getAlgebraFlairOracleStorage();
    $.lastTimepointTimestamp = _timepoint;
}

//  =====
// @dev uint8(1 << 6 | 1 |1 << 1 | 1 << 3) 
uint8 constant ALGEBRA_FLAIR_ORACLE_PLUGIN_CONFIG = 0x4b;

// @dev keccak256('ALGEBRA_BASE_PLUGIN_MANAGER')
bytes32 constant ALGEBRA_BASE_PLUGIN_MANAGER = 0x8e8000aba5b365c0be9685da1153f7f096e76d1ecfb42c050ae1e387aa65b4f5;



contract FlairOracleAlgebraV1{
     address private immutable ALGEBRA_POOL_FACTORY;
     address private immutable ALGEBRA_PLUGIN_FACTORY;
     address public immutable ALGEBRA_POOL;

     constructor(address _factory, address _pool, address _pluginFactory) {
	  ALGEBRA_POOL_FACTORY = _factory;
	  ALGEBRA_PLUGIN_FACTORY = _pluginFactory;
	  ALGEBRA_POOL = _pool;
	  setPluginConfig(ALGEBRA_FLAIR_ORACLE_PLUGIN_CONFIG);
     }

       function initializeOracle() external {
	 require(!isInitialized(), 'Already initialized');
	 require(getPluginInPool() == address(this), 'Plugin not attached');
	 (uint160 price, int24 tick, , , , ) = IAlgebraPoolState(getPool()).globalState();
	 require(price != 0, 'Pool is not initialized');

	 uint32 time = uint32(block.timestamp);
	 getTimepoints().initialize(time, tick);
	 setLastTimepointTimestamp(time);
	 _setInitialized();
       }


       function afterInitialize(
				address pool,
				uint160 sqrtPriceX96,
				int24 tick
       ) external returns (bytes4)
       {
	   
	   if (!Plugins.hasFlag(getPluginConfig(), Plugins.AFTER_INIT_FLAG)) revert('afterInitialize hook disabled');
	   uint160 feeRevenuePerLiquidityX96 = updateFeeRevenuePerLiquidityX96(
									       pool,
									       tick
	   );
	   setFeeRevenuePerLiquidityX96(feeRevenuePerLiquidityX96);
	   
	   int24 feeRevenuePerLiquidityTick = TickMath.getTickAtSqrtRatio(feeRevenuePerLiquidityX96);
	   writeTimepoint(feeRevenuePerLiquidityTick);
	   
	   return IAlgebraPlugin.afterInitialize.selector;
       }

}

