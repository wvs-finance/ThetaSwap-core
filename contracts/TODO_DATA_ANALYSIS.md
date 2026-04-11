



## AI AGENTS:

We need to brainstorm a minimal API sucha that is fully compatible with calling [ffi](~/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/test/_helpers/BaseTest.sol:: L118) on [foundry fork tests](~/apps/ThetaSwap/thetaSwap-core-dev/.worktree/ranFromAngstrom/contracts/test/_helpers/BaseForkTest.t.sol)


From now the design constrains are that it MUST follow classic API priciples, and the same requirements as oother sessions about beiong 2 way reviewed and follow test driven developmnet. From now we ONLY concern with being able to query at a index and that IS it (e.g )



> NOTE: This example is for reference onyl. The agents and the process DO NOT touch any solidity files
```
function test__DifferentialFuzz__NumbersMatch(uint256 idxSeed) public {
	// note: dataSetLen() makes a ffi call to query the len of the data
	uint256 idx = bound(index , dataSetLen(poolId));
	// note: getBlockTimestamp(poolId, idx)  also uses ffi leveraging the ffi built API 
	uint48 blockTimestamp = parse(getBlockTimestamp(poolId, idx));
	// note: Same for globalGrowth
	uint256 offchainGlobalGrowth  = parserQ128.128ToQ128.128(getGlobalGrowth(poolId, blockTimestamp));	
	// note: Same for getBlockNumber
	uint32 blockNumber = parse(getBlockNumber(poolId ,idx));
	vm.rollFork(blockNumber);
	uint256 onChainGlobalGrowth = angstromComsumer.getGlobalGrowth(poolId);
	assertEq(onChainGlobalGrowth, offchainGlobalGrowth);
	
}
```

- Does the curent dataa schema and in general the data extracted allow to build this or we are missing information ?




--> NEXT 

To be ready to do data eploration on the data, just enough to tell its correcteness and cover basic EDA just usabale for the ffi fuzzing. This is to be done by a  combination of a data analysys agent and analytics reporter AND AS RESTRICTIONS IS on notebooks/ sub-dir growthGlobal.ipynb and the notebook MUST be able to read and detect the venv and run it s analysys on that kernel. From now we can focus on etting up the invorment ready to receive the data


