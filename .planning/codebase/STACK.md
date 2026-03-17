# Technology Stack

**Analysis Date:** 2026-03-17

## Languages

**Primary:**
- Solidity 0.8.26 - Smart contracts, hooks, protocol adapters, diamond facets
- Python 3.11+ (3.13 preferred) - Research, backtesting, econometric analysis, oracles

## Runtime

**Environment:**
- Node.js (implied by Forge + Git) - Foundry toolchain runtime
- Python 3.13 - Research and oracle execution

**Package Manager:**
- uv - Python package manager and virtual environment manager
  - Lockfile: Generated via `uv pip` (reproducible)
- npm/pnpm - Not explicitly used (not found in repo)

**Virtual Environment:**
- `uhi8/` directory - Python 3.13 venv managed by uv
  - Created via: `uv venv uhi8 --python 3.13`
  - Used for all Python execution

## Frameworks

**Core (Solidity):**
- Uniswap V4 Core - Hook system, PoolManager, StateLibrary, TickBitmap
  - Location: `lib/uniswap-hooks/lib/v4-core/`
  - Used in: FCI V2, reactive integration
- Uniswap V3 Core - Pool interfaces, oracle interfaces
  - Location: `lib/v3-core/`
  - Used in: V3 reactive facet, V3 event reading

**Hook Architecture:**
- MasterHook pattern (diamond proxy) - Fee Concentration Index V2
  - Implementation: `src/fee-concentration-index-v2/`
  - Facet pattern: Multiple protocol adapters via IFCIProtocolFacet
- Compose extensions - Hook composition framework
  - Location: `lib/hook-bazaar/contracts/lib/Compose/src/`
  - Used for modular hook stacking

**Testing (Solidity):**
- Foundry (Forge) - Solidity unit tests, fork tests, fuzz tests, invariant tests
  - Config: `foundry.toml` (profile: default, fuzz-heavy)
  - Test location: `test/fee-concentration-index-v2/`
  - Fuzz runs: 256 (default), 64 (heavy profile)

**Testing (Python):**
- pytest 7.0+ - Unit tests, integration tests
  - Config: `pyproject.toml` under `[tool.pytest.ini_options]`
  - Test location: `research/tests/`
- Jupyter notebooks - Data analysis, econometric modeling
  - Runner: `jupyter nbconvert` (headless execution)
  - Kernel: `thetaswap` kernel with PYTHONPATH pointing to `research/`

**Build/Dev:**
- Foundry - Solidity compilation, testing, deployment
  - EVM version: Cancun
  - via_ir: true (enables IR compilation pipeline)
  - ffi: true (enables Foreign Function Interface for Python oracles)
- Make - Project orchestration
  - Targets: `build`, `install`, `test`, `notebooks`, `verify-data`, `clean`
- Forge-std - Standard library for Foundry tests
  - Location: `lib/forge-std/`
- Kontrol - Formal verification framework (included via kontrol-cheatcodes)
  - Location: `lib/kontrol-cheatcodes/`

## Key Dependencies

**Critical (Solidity):**
- `v4-core/src/` (Uniswap V4) - Pool types, interfaces, StateLibrary
- `@uniswap/v3-core/` - V3 pool interfaces, oracle reading
- `@uniswap/v4-periphery/` - Permit2, PositionConfig
- `typed-uniswap-v4/` - Type-safe V4 wrappers (TickRange, SwapCount, BlockCount, FeeShareRatio)
- `reactive-lib/` - Reactive network protocol types and interfaces
- `solady/` - Gas-optimized utilities (FixedPointMathLib, LibCall)
- `@openzeppelin/contracts/` - Standard library (ERC20, etc.)

**Research/Oracle (Python):**
- `jax` 0.4+ - Numerical computing, JAX arrays for econometric models
- `numpy` 1.24+ - Array operations, numerical algorithms
- `scipy` 1.11+ - Scientific computing (hazard rates, duration analysis)
- `matplotlib` 3.7+ - Data visualization for research outputs
- `httpx` 0.27+ - Async HTTP client for The Graph queries, RPC calls
- `eth_abi` 5.0+ - Ethereum ABI encoding/decoding for oracles
- `pycryptodome` 3.20+ - Keccak-256 hashing for position keys
- `python-dotenv` 1.0+ - Environment variable loading

**Dev Tools (Python):**
- `pytest` 7.0+ - Test runner
- `jupyter` 1.0+ - Notebook IDE
- `nbconvert` 7.0+ - Notebook to script conversion
- `ipykernel` 6.0+ - Jupyter kernel for notebooks

**Git Submodules (not packages, but critical dependencies):**
- `lib/forge-std/` - Foundry standard library
- `lib/v4-core/` - Uniswap V4 core (via uniswap-hooks)
- `lib/v3-core/` - Uniswap V3 core
- `lib/v4-periphery/` - Uniswap V4 periphery
- `lib/v3-periphery/` - Uniswap V3 periphery
- `lib/hook-bazaar/` - MasterHook + Compose extensions
- `lib/reactive-lib/` - Reactive network protocol
- `lib/reactive-hooks/` - Reactive hook integrations
- `lib/typed-uniswap-v4/` - Type-safe V4 wrappers
- `lib/solady/` - Solady utilities library
- `lib/openzeppelin-contracts/` - OpenZeppelin contracts
- `lib/kontrol-cheatcodes/` - Kontrol formal verification support

## Configuration

**Environment:**
- Managed via `.env` file (not committed - listed in `.gitignore`)
- Key env vars (from `foundry.toml`):
  - `ALCHEMY_API_KEY` - For eth-mainnet, eth-sepolia RPC access
  - `ETHERSCAN_API_KEY` - For contract verification on Etherscan/BlockScout
  - `REACTIVE_RPC_URL` - Reactive network RPC endpoint
  - `GRAPH_API_KEY` - The Graph API key for subgraph queries (research only)
  - `SEPOLIA_RPC_URL` - Sepolia testnet RPC (used in fork tests)

**Build:**
- `foundry.toml` (lines 1-77):
  - Profile: `default` (standard compilation + testing)
  - Profile: `fuzz-heavy` (64 fuzz runs, increased memory)
  - EVM version: `cancun` (latest)
  - Solc: `0.8.26` explicit version
  - via_ir: `true` - IR compilation for optimization
  - ffi: `true` - Foreign Function Interface for Python oracle calls
  - fs_permissions: Read access to `research/data/fixtures/`, read-write to `broadcast/`
  - Remappings: 29 path aliases for cleaner imports (see lines 14-46)

- `pyproject.toml` (lines 1-35):
  - Build system: setuptools
  - Python requirement: >=3.11
  - Package discovery: `research/econometrics*`, `research/backtest*`
  - Pytest config: `--import-mode=importlib`

- `Makefile` (lines 1-52):
  - VENV: `uhi8`
  - Python: `uhi8/bin/python`
  - Primary targets: `build` (full pipeline), `install`, `test`, `notebooks`, `verify-data`

## Platform Requirements

**Development:**
- Git (with submodule support)
- Foundry (forge, cast, anvil) - installed via `foundry-rs/foundry-toolchain` GitHub action
- Python 3.13
- uv package manager
- Make
- POSIX shell (bash/zsh) for Makefile

**Production:**
- Deployment target: Ethereum mainnet, Sepolia testnet, Unichain mainnet, Unichain Sepolia
- Block explorer APIs: Etherscan, BlockScout
- RPC providers: Alchemy (for eth-mainnet, eth-sepolia, unichain*, unichain-sepolia), custom Reactive RPC
- The Graph API (research data only, not production runtime)

**Testnet Endpoints (from foundry.toml lines 50-56):**
- mainnet: `https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}`
- sepolia: `https://eth-sepolia.g.alchemy.com/v2/${ALCHEMY_API_KEY}`
- unichain: `https://unichain-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}`
- unichain_sepolia: `https://unichain-sepolia.g.alchemy.com/v2/${ALCHEMY_API_KEY}`
- reactive: `${REACTIVE_RPC_URL}` (custom endpoint)

---

*Stack analysis: 2026-03-17*
