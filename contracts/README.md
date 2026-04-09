# Angstrom

This repository contains the core contracts for the Angstrom protocol. These
contracts enforce decisions made by the off-chain network.

For docs see [./docs](./docs/).


## Build Instructions

1. Ensure you have the foundry toolchain installed (otherwise get it from `https://getfoundry.sh/`)
2. Run `forge build`
3. Setup a python virtual environment under `.venv` (using uv: `uv venv .venv`)
4. Ensure the python packages from `requirements.txt` are installed into the environment (`source .venv/bin/activate && uv pip install -r requirements.txt`)
5. Run tests with `forge test --ffi`

### Alternative Python Environment
If you do not have Python 3.12 or simply want to use your global installation instead of a virtual
environment you can tweak what python executable is used for the FFI tests by:
1. Opening [`test/_helpers/BaseTest.sol`](./test/_helpers/BaseTest.sol)
2. Changing `args[0]` in `pythonRunCmd()` to a different path e.g.

```diff
function pythonRunCmd() internal pure returns (string[] memory args) {
    args = new string[](1);
--  args[0] = ".venv/bin/python3.12";
++  args[0] = "python3";
}
```

## Benchmark Numbers

### Total Cost

Amortized cost of `N` orders not including the ToB order cost.

- EFI = Exact Flash Order \w Internal Balances
- ESLn = Exact Standing Order \w Liquid Tokens (Nonce non-zero)

|Order Count|EFI (\w AMM)|EFI (No AMM)|ESLn (\w AMM)|ESLn (No AMM)|
|-----------|------------|------------|-------------|-------------|
| 1| 135.3k | 65.2k | 148.2k | 92.9k |
| 2| 77.3k | 42.3k | 90.3k | 62.6k |
| 3| 58.0k | 34.7k | 71.0k | 52.5k |
| 4| 48.4k | 30.8k | 61.3k | 47.5k |
| 5| 42.6k | 28.6k | 55.5k | 44.4k |
|10| 31.0k | 24.0k | 43.9k | 38.4k |
|20| 25.2k | 21.7k | 38.1k | 35.4k |
|50| 21.7k | 20.3k | 34.7k | 33.5k |

