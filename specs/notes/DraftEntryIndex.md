- queries used are written on the data/queries/ folder on the .sql file

# Index Accuracy

We are testing the FeeConcentrationIndex accuracy against real world data, this is in the form of fork testing.

For the simplest case we are gathering a sample of real world data on a V4 pool using the dune MCP on hardcoding the data on a json file. 

Then for the sampled data we are deployitn the FeeConventrationHarnesHook on thr rolled fork number were out fisrt sample observation is and asserting the index on the JSON matches the index gathered by the hook

- This approach is part of the 001-fee-concentration-index branch
- the test file goes on test/fee-concentration-index/fork/ directory and has extension .fork.t.sol

# Reactive Integration

We are testing FeeConcentrationIndex integration against real world data on V3 pools using reactive apporqaches to events. Since the reactive network does not have fork support. We are doing it with Somnia. 

This is the same approach as before but isntead of deploying a Hook we deploy the SomniaAdapater reactive contract that outputs the index and test that indeed reacts to events and preserves the accuracy.

We use the equivalent V3 pool sued for the test above whih is WETH/USDC 0.3 bps

- This approach is part of the 003-reactive-integration branch
- the test file goes on test/fee-concentration-index/integration/fork directory and has extension 
.integration.fork.t.sol

# Diamond Integration


- This approach is part of the 001-fee-concentration-index branch
