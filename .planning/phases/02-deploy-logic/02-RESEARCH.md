# Phase 2: Deploy Logic - Research

**Researched:** 2026-03-17
**Domain:** Rust subprocess orchestration wrapping Foundry forge/cast for smart contract deployment
**Confidence:** HIGH — all critical facts verified by running Foundry v1.5.1 locally against anvil

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DEP-01 | Primary path runs `forge create UniswapV3Reactive --constructor-args <callback> --broadcast --legacy --value <value> --rpc-url <rpc> --private-key <key>` | Verified forge create accepts --legacy, --value, --broadcast, --json flags; arg order confirmed |
| DEP-02 | If forge create fails, fallback runs `cast send --create` with identical bytecode and constructor args | cast send --create verified working; bytecode from `out/UniswapV3Reactive.sol/UniswapV3Reactive.json` |
| DEP-03 | `--legacy` is only applied to forge create path, not cast send fallback | Verified: cast send uses EIP-1559 by default; --legacy applies only to forge create |
| DEP-04 | On startup, CLI checks forge and cast are on PATH; fails with actionable error if missing | Verified: `io::ErrorKind::NotFound` from `std::process::Command` is sufficient without `which` crate |
| DEP-05 | After successful deployment, CLI runs `cast receipt <txhash> status` and verifies success before printing output | Verified: `cast receipt <TXHASH> status` returns "1 (success)"; `cast receipt <TXHASH> --json` returns `{"status":"0x1",...}` |
| DEP-06 | `--constructor-args` placed last in forge create command | Verified Foundry issue #770; order must be: `forge create <CONTRACT> --rpc-url ... --private-key ... --broadcast --legacy --value ... --constructor-args <args...>` |
| OUT-01 | On success, stdout prints deployed contract address and tx hash (pipe-friendly) | `DeployOutput::fmt` already correct; must call `print!` not `println!` for last line |
| OUT-04 | No diagnostic noise on stdout — all logs/warnings go to stderr | forge create --json sends pure JSON to stdout, nothing to stderr; cast send --create --json same |
</phase_requirements>

---

## Summary

Phase 2 implements `Runner::deploy()`, the core of d2p. It orchestrates two subprocess strategies — `forge create` as primary and `cast send --create` as fallback — with receipt verification before emitting output. The phase has no CLI parsing (that is Phase 3); all logic is driven by `DeployParams` from Phase 1.

The critical open question from STATE.md — whether `forge create --json` produces structured JSON output — is now resolved: **in Foundry v1.5.1-stable, `forge create --json` produces clean JSON on stdout with exactly three fields: `deployer`, `deployedTo`, `transactionHash`**. This is not a log-formatter; it is a structured output flag. The implementation can use `serde_json` to parse directly.

The second open question — the bytecode source for `cast send --create` — is also resolved: bytecode lives at `{project_dir}/out/{ContractName}.sol/{ContractName}.json` under `.bytecode.object` (with `0x` prefix). The artifact exists from a prior `forge build` run, which d2p does not trigger. The `which` crate is not needed: `io::ErrorKind::NotFound` from `std::process::Command` gives a deterministic PATH-miss signal at near-zero dependency cost.

**Primary recommendation:** Use `forge create --json` for structured output parsing via `serde_json`. Use `cast send --create <BYTECODE> "constructor(address)" <callback>` for the fallback. Verify every deployment with `cast receipt <TXHASH> --json` and check `status == "0x1"` before printing output.

---

## Standard Stack

### Core (already in Cargo.toml)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `std::process::Command` | stdlib | Spawning forge/cast subprocesses | Sequential, blocking — correct for this use case. `.output()` captures both streams. |
| `serde_json` | 1.x | Parsing forge create --json and cast send --json output | forge create --json verified to produce clean, parseable JSON on stdout |
| `anyhow` | 1.x | Error propagation and context chaining | `fn deploy() -> anyhow::Result<DeployOutput>` — adds context at each layer |
| `thiserror` | 2.x | Typed `D2pError` variants | Already defined in Phase 1: `ProcessNotFound`, `NonZeroExit`, `ParseFailure` |

### Missing from Cargo.toml

The `which` crate appears in STACK.md but is NOT in `d2p/Cargo.toml`. Decision: do NOT add it. `std::process::Command::new("forge").arg("--version").output()` returns `Err(e)` where `e.kind() == io::ErrorKind::NotFound` when forge is not on PATH. This is deterministic and requires zero additional dependencies. The PATH check becomes:

```rust
fn check_tool_on_path(name: &str) -> Result<(), D2pError> {
    match std::process::Command::new(name).arg("--version").output() {
        Ok(_) => Ok(()),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
            Err(D2pError::ProcessNotFound(name.to_string()))
        }
        Err(e) => Err(D2pError::ProcessNotFound(format!("{name}: {e}"))),
    }
}
```

**Installation:** No additions needed. Cargo.toml from Phase 1 is complete for Phase 2.

---

## Architecture Patterns

### Recommended Module Structure (Phase 2 additions)

```
d2p/src/
├── main.rs                 # Phase 1 skeleton — unchanged
├── errors.rs               # Phase 1 — D2pError — unchanged
├── deploy/
│   ├── mod.rs              # Phase 1: DeployParams, DeployOutput, Display — ADD Runner here
│   ├── primary.rs          # Phase 2 NEW: forge create invocation + JSON parsing
│   └── fallback.rs         # Phase 2 NEW: cast send --create + JSON parsing + bytecode read
```

### Pattern 1: forge create Primary Path

**What:** Run `forge create`, pass `--json`, parse stdout with `serde_json`.

**Critical arg ordering (DEP-06):** `--constructor-args` MUST be last. Verified against Foundry issue #770.

```rust
// Source: verified locally against Foundry v1.5.1-stable
fn build_forge_args(params: &DeployParams) -> Vec<String> {
    vec![
        "create".to_string(),
        params.contract_path.clone(),           // e.g. "src/.../UniswapV3Reactive.sol:UniswapV3Reactive"
        "--rpc-url".to_string(),    params.rpc_url.clone(),
        "--private-key".to_string(), params.private_key.clone(),
        "--broadcast".to_string(),
        "--legacy".to_string(),
        "--value".to_string(),      params.value.clone(),
        "--json".to_string(),
        // LAST — variadic, must come after all flags
        "--constructor-args".to_string(),
        params.callback.clone(),
    ]
}
```

**JSON output parsing:** Three fields, all present when exit code 0:

```rust
// Source: verified by running forge create --json --broadcast on anvil
#[derive(serde::Deserialize)]
struct ForgeCreateOutput {
    #[serde(rename = "deployedTo")]
    deployed_to: String,
    #[serde(rename = "transactionHash")]
    transaction_hash: String,
    // deployer field also present but not needed
}
```

**stdout/stderr separation:** `--json` sends only the JSON object to stdout. stderr is empty on success. Capture with `.output()`, parse `out.stdout`.

### Pattern 2: cast send --create Fallback Path

**What:** Read bytecode from forge artifact, pass to `cast send --create`, ABI-encode constructor args via cast's SIG+ARGS pattern.

**Bytecode source (resolved):** `{project_dir}/out/UniswapV3Reactive.sol/UniswapV3Reactive.json` at path `.bytecode.object`. The value includes the `0x` prefix — pass as-is to cast.

```rust
// Source: verified artifact structure locally
fn read_bytecode(project_dir: &std::path::Path, contract_name: &str) -> anyhow::Result<String> {
    let artifact_path = project_dir
        .join("out")
        .join(format!("{contract_name}.sol"))
        .join(format!("{contract_name}.json"));

    let content = std::fs::read_to_string(&artifact_path)
        .with_context(|| format!("artifact not found: {}", artifact_path.display()))?;

    let v: serde_json::Value = serde_json::from_str(&content)?;
    let bytecode = v["bytecode"]["object"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("bytecode.object missing from artifact"))?;

    Ok(bytecode.to_string())
}
```

**Cast send --create arg order (VERIFIED):** Flags come before `--create`; CODE is the first positional after `--create`; SIG and ARGS follow optionally.

```rust
// Source: verified cast send --create --help and live test on anvil
fn build_cast_args(params: &DeployParams, bytecode: &str) -> Vec<String> {
    vec![
        "send".to_string(),
        "--rpc-url".to_string(),     params.rpc_url.clone(),
        "--private-key".to_string(), params.private_key.clone(),
        "--value".to_string(),       params.value.clone(),
        "--json".to_string(),
        // --create must come AFTER all flags — it is a subcommand, not a flag
        "--create".to_string(),
        bytecode.to_string(),
        // Constructor ABI encoding via cast's SIG+ARGS pattern
        "constructor(address)".to_string(),
        params.callback.clone(),
    ]
}
```

**NOTE on --legacy:** cast send does NOT accept `--legacy` in the same way forge create does. DEP-03 is correct — `--legacy` is omitted from the cast path. Cast uses EIP-1559 by default; Lasna accepts both.

**JSON output parsing:** cast send --create --json returns the full transaction receipt on stdout:

```rust
// Source: verified locally; status is "0x1" string when successful
#[derive(serde::Deserialize)]
struct CastSendOutput {
    #[serde(rename = "contractAddress")]
    contract_address: String,
    #[serde(rename = "transactionHash")]
    transaction_hash: String,
    status: String,  // "0x1" on success, "0x0" on revert
}
```

### Pattern 3: Receipt Verification (DEP-05)

After either path returns a tx hash, verify on-chain:

```rust
// Source: verified cast receipt --json output on anvil
// cast receipt --rpc-url <URL> <TXHASH> --json  -->  {"status":"0x1","contractAddress":"0x..."}
fn verify_receipt(tx_hash: &str, rpc_url: &str) -> anyhow::Result<String> {
    let out = std::process::Command::new("cast")
        .args(["receipt", "--rpc-url", rpc_url, tx_hash, "--json"])
        .output()
        .context("cast not found on PATH")?;

    if !out.status.success() {
        anyhow::bail!("cast receipt failed: {}", String::from_utf8_lossy(&out.stderr));
    }

    let stdout = String::from_utf8_lossy(&out.stdout);
    let v: serde_json::Value = serde_json::from_str(&stdout)
        .context("failed to parse cast receipt JSON")?;

    let status = v["status"].as_str().unwrap_or("0x0");
    if status != "0x1" {
        anyhow::bail!("transaction reverted (status={status})");
    }

    // contractAddress may be null for non-creation txs, but here it must exist
    let addr = v["contractAddress"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("no contractAddress in receipt"))?;

    Ok(addr.to_string())
}
```

**IMPORTANT:** `cast receipt <TXHASH> status` (positional field) returns `"1 (success)"` as plain text — NOT `"0x1"`. Use `--json` and parse `.status` to get `"0x1"` for reliable machine comparison.

### Pattern 4: PATH Check (DEP-04)

```rust
// Source: verified io::ErrorKind::NotFound behavior locally
fn check_prerequisites() -> anyhow::Result<()> {
    for tool in ["forge", "cast"] {
        match std::process::Command::new(tool).arg("--version").output() {
            Ok(_) => {},
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
                anyhow::bail!(
                    "{tool} not found on PATH — install Foundry: https://getfoundry.sh"
                );
            }
            Err(e) => anyhow::bail!("{tool}: {e}"),
        }
    }
    Ok(())
}
```

### Pattern 5: Runner::deploy() Orchestration

```rust
// Source: Phase 1 architecture decision + Phase 2 implementation
impl Runner {
    pub fn new(params: DeployParams) -> Self { Runner { params } }

    pub fn deploy(&self) -> anyhow::Result<DeployOutput> {
        check_prerequisites()?;

        match primary::run(&self.params) {
            Ok(out) => Ok(out),
            Err(e) => {
                eprintln!("[warn] forge create failed ({e}), retrying with cast send --create");
                fallback::run(&self.params)
            }
        }
    }
}
```

### Anti-Patterns to Avoid

- **Shell string interpolation:** Never `Command::new("sh").arg("-c").arg(format!(...))`. Private keys contain no shell-special chars, but this is a categorical rule. Use `.args([...])`.
- **`.status()` instead of `.output()`:** `.status()` does not capture stdout — forge JSON will be printed to terminal and lost. Always use `.output()`.
- **Parsing forge create text output instead of --json:** The text output (`Deployer: ...\nDeployed to: ...\nTransaction hash: ...`) is human-readable and subject to change. The `--json` flag is stable in v1.5.1. Use it.
- **Trusting cast send --create exit code alone:** The exit code 0 confirms broadcast, not on-chain success. Receipt verification is mandatory (DEP-05).
- **Inheriting full parent env:** Avoid forwarding `ETH_RPC_URL` to subprocess. If the caller has it set, it can override the explicit `--rpc-url` flag in some Foundry versions (Pitfall 1 from PITFALLS.md).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON parsing of forge/cast output | Custom string splitting on `:` separator | `serde_json::from_str` with typed struct | forge JSON has nested fields; string-split breaks on addresses containing colons |
| ABI encoding of constructor args | Manual hex-encode of address bytes | `cast send --create <CODE> "constructor(address)" <addr>` | cast handles ABI encoding correctly; edge cases with padding, checksums |
| Transaction receipt polling | Custom retry loop with `cast call` | `cast receipt <TXHASH> --json` | cast blocks until receipt available (default: 1 confirmation); no polling needed |
| PATH lookup | `std::env::var("PATH").split(':').find(...)` | `Command::new("forge").arg("--version").output()` + check `ErrorKind::NotFound` | OS handles PATH resolution; the `which` crate is also acceptable but not necessary |

**Key insight:** The combination of `forge create --json` + `cast send --create --json` + `cast receipt --json` gives three structured, parseable JSON outputs for the entire flow. No custom text parsing is required at any step.

---

## Common Pitfalls

### Pitfall 1: forge create --json Confused with Log Formatter

**What goes wrong:** The `--json` flag appears under "Display options" in `forge create --help`, leading developers to assume it formats human-readable logs as JSON (e.g., adding timestamps). This is wrong.

**Verified behavior (Foundry v1.5.1-stable):** `forge create --broadcast --json` writes a clean 3-field JSON object to stdout (`deployer`, `deployedTo`, `transactionHash`). Nothing is written to stderr. This is machine-parseable.

**How to avoid:** Always capture `.output().stdout`, not `.output().stderr`. Parse with `serde_json`. Fields: `deployedTo` (camelCase) and `transactionHash`.

### Pitfall 2: cast send --create Arg Ordering

**What goes wrong:** Placing `--rpc-url`, `--private-key`, or `--json` flags AFTER `--create` causes: `error: unexpected argument '--rpc-url' found`.

**Verified behavior:** `--create` is a subcommand of `cast send`, not a flag. All options must precede it. The bytecode is the first positional argument after `--create`. Constructor SIG and ARGS follow the bytecode.

**Correct order:**
```
cast send --rpc-url <URL> --private-key <KEY> --value <V> --json --create <BYTECODE> "constructor(address)" <ADDR>
```

### Pitfall 3: cast receipt Positional Field Returns Human String, Not Hex

**What goes wrong:** `cast receipt <TXHASH> status` returns `"1 (success)"` (a human string). Comparing it to `"0x1"` always fails.

**Verified behavior:** `cast receipt <TXHASH> --json` returns `{"status":"0x1",...}`. Use `--json` and parse the `status` field.

**How to avoid:** Use the `--json` receipt path. Parse `.status == "0x1"` for machine-readable success check. The positional field form is for human inspection only.

### Pitfall 4: --constructor-args Position in forge create

**What goes wrong:** Placing `--constructor-args` before other flags causes `forge create` to treat subsequent flag names as constructor arguments, producing "required arguments not provided: CONTRACT".

**Verified fix:** `--constructor-args` must be the last flag in the arg list. Always build the arg vector with `--constructor-args` appended at the end.

### Pitfall 5: Bytecode Artifact Missing When cast send --create Runs

**What goes wrong:** The fallback reads `out/UniswapV3Reactive.sol/UniswapV3Reactive.json` — but if `forge build` was never run from `project_dir`, this file does not exist. The fallback gets an IO error, not a deployment error.

**How to avoid:** In `fallback::run`, detect artifact-not-found separately from deployment failure. Return a distinct error message: "artifact not found at {path} — run `forge build` from {project_dir} first".

### Pitfall 6: Inheriting ETH_RPC_URL from Parent Environment

**What goes wrong:** If the caller exports `ETH_RPC_URL` pointing to mainnet, and the subprocess inherits it, `forge create`'s internal RPC resolution may use it instead of the `--rpc-url` flag. (See PITFALLS.md Pitfall 1.)

**How to avoid:** Call `.env_remove("ETH_RPC_URL")` on the `Command` builder before spawning both forge and cast.

---

## Code Examples

### Complete primary.rs

```rust
// Source: verified against forge create --help and live local test on Foundry v1.5.1
use crate::{deploy::{DeployOutput, DeployParams}, errors::D2pError};
use anyhow::Context;

#[derive(serde::Deserialize)]
struct ForgeCreateJson {
    #[serde(rename = "deployedTo")]
    deployed_to: String,
    #[serde(rename = "transactionHash")]
    transaction_hash: String,
}

pub fn run(params: &DeployParams) -> anyhow::Result<DeployOutput> {
    let args = build_args(params);

    let out = std::process::Command::new("forge")
        .args(&args)
        .current_dir(&params.project_dir)
        .env_remove("ETH_RPC_URL")
        .output()
        .map_err(|e| match e.kind() {
            std::io::ErrorKind::NotFound =>
                D2pError::ProcessNotFound("forge".to_string()),
            _ => D2pError::NonZeroExit { stderr: e.to_string() },
        })?;

    if !out.status.success() {
        let stderr = String::from_utf8_lossy(&out.stderr).into_owned();
        return Err(D2pError::NonZeroExit { stderr }.into());
    }

    let stdout = String::from_utf8_lossy(&out.stdout);
    let parsed: ForgeCreateJson = serde_json::from_str(&stdout)
        .map_err(|e| D2pError::ParseFailure(format!("forge JSON: {e}")))?;

    Ok(DeployOutput {
        address: parsed.deployed_to,
        tx_hash: parsed.transaction_hash,
    })
}

fn build_args(params: &DeployParams) -> Vec<String> {
    // CRITICAL: --constructor-args must be LAST (Foundry issue #770)
    vec![
        "create".to_string(),
        params.contract_path.clone(),
        "--rpc-url".to_string(),     params.rpc_url.clone(),
        "--private-key".to_string(), params.private_key.clone(),
        "--broadcast".to_string(),
        "--legacy".to_string(),
        "--value".to_string(),       params.value.clone(),
        "--json".to_string(),
        "--constructor-args".to_string(),
        params.callback.clone(),
    ]
}
```

### Complete fallback.rs

```rust
// Source: verified cast send --create --help and live test on Foundry v1.5.1
use crate::{deploy::{DeployOutput, DeployParams}, errors::D2pError};
use anyhow::Context;

#[derive(serde::Deserialize)]
struct CastSendJson {
    #[serde(rename = "contractAddress")]
    contract_address: String,
    #[serde(rename = "transactionHash")]
    transaction_hash: String,
}

pub fn run(params: &DeployParams) -> anyhow::Result<DeployOutput> {
    let bytecode = read_bytecode(params)?;
    let args = build_args(params, &bytecode);

    let out = std::process::Command::new("cast")
        .args(&args)
        .current_dir(&params.project_dir)
        .env_remove("ETH_RPC_URL")
        .output()
        .map_err(|e| match e.kind() {
            std::io::ErrorKind::NotFound =>
                D2pError::ProcessNotFound("cast".to_string()),
            _ => D2pError::NonZeroExit { stderr: e.to_string() },
        })?;

    if !out.status.success() {
        let stderr = String::from_utf8_lossy(&out.stderr).into_owned();
        return Err(D2pError::NonZeroExit { stderr }.into());
    }

    let stdout = String::from_utf8_lossy(&out.stdout);
    let parsed: CastSendJson = serde_json::from_str(&stdout)
        .map_err(|e| D2pError::ParseFailure(format!("cast JSON: {e}")))?;

    Ok(DeployOutput {
        address: parsed.contract_address,
        tx_hash: parsed.transaction_hash,
    })
}

fn read_bytecode(params: &DeployParams) -> anyhow::Result<String> {
    // Contract name is the part after ':' in contract_path, e.g. "UniswapV3Reactive"
    let contract_name = params.contract_path
        .split(':').last()
        .ok_or_else(|| anyhow::anyhow!("invalid contract_path: {}", params.contract_path))?;

    let artifact = params.project_dir
        .join("out")
        .join(format!("{contract_name}.sol"))
        .join(format!("{contract_name}.json"));

    let content = std::fs::read_to_string(&artifact)
        .with_context(|| format!(
            "artifact not found at {} — run `forge build` from {} first",
            artifact.display(), params.project_dir.display()
        ))?;

    let v: serde_json::Value = serde_json::from_str(&content)?;
    let bytecode = v["bytecode"]["object"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("bytecode.object missing in {}", artifact.display()))?;

    Ok(bytecode.to_string())
}

fn build_args(params: &DeployParams, bytecode: &str) -> Vec<String> {
    // CRITICAL: all flags before --create; --create is a subcommand, not a flag
    // NOTE: no --legacy on fallback path (DEP-03)
    vec![
        "send".to_string(),
        "--rpc-url".to_string(),     params.rpc_url.clone(),
        "--private-key".to_string(), params.private_key.clone(),
        "--value".to_string(),       params.value.clone(),
        "--json".to_string(),
        "--create".to_string(),
        bytecode.to_string(),
        // cast ABI-encodes constructor args from SIG + positional ARGS
        "constructor(address)".to_string(),
        params.callback.clone(),
    ]
}
```

### Receipt Verifier

```rust
// Source: verified cast receipt --json on anvil; status field is "0x1" string
pub fn verify(tx_hash: &str, rpc_url: &str) -> anyhow::Result<()> {
    let out = std::process::Command::new("cast")
        .args(["receipt", "--rpc-url", rpc_url, tx_hash, "--json"])
        .output()
        .context("cast receipt: cast not found")?;

    if !out.status.success() {
        anyhow::bail!("cast receipt failed: {}", String::from_utf8_lossy(&out.stderr));
    }

    let v: serde_json::Value = serde_json::from_str(&String::from_utf8_lossy(&out.stdout))?;
    match v["status"].as_str() {
        Some("0x1") => Ok(()),
        Some(s) => anyhow::bail!("transaction reverted on-chain (status={s})"),
        None => anyhow::bail!("cast receipt JSON missing status field"),
    }
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Parse forge create text output with string-matching | `forge create --json` with `serde_json` | Foundry v0.2+ | Eliminates output-format breakage on Foundry updates |
| Single deploy path (forge create only) | Primary + fallback (forge create then cast send --create) | This project design decision | Handles Lasna/custom-RPC where forge create ignores --rpc-url |
| Trust exit code 0 as success | `cast receipt --json` status check | Best practice, always required | Catches on-chain constructor reverts |
| `which` crate for PATH check | `Command::new(tool).arg("--version")` + `ErrorKind::NotFound` | N/A — always stdlib-possible | Avoids adding a dependency for a 3-line check |

**Deprecated/outdated:**
- `cast receipt <TXHASH> status` (positional field): Returns human string `"1 (success)"` — do not parse programmatically. Use `--json` instead.
- Parsing `"Deployed to: 0x..."` from forge create text stdout: fragile; avoided by using `--json`.

---

## Open Questions

1. **value unit parsing (deferred to Phase 3)**
   - What we know: `DeployParams.value` is a raw string; `forge create --value` accepts `10ether`, `10000000000000000000` wei, etc. cast send `--value` accepts same format.
   - What's unclear: Does the user-supplied `"10react"` (REACT token units) need conversion to wei before passing to forge/cast? Or does Foundry handle custom unit labels?
   - Recommendation: Phase 2 passes `value` string through verbatim. Phase 3 (CLI) handles unit parsing/conversion before populating `DeployParams.value`. The value in DeployParams should always be wei by the time Phase 2 sees it.

2. **Contract path hardcoding vs config**
   - What we know: `DeployParams.contract_path` is set to `"src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol:UniswapV3Reactive"` by the caller (Phase 3).
   - What's unclear: Phase 2 does not know this path — it is provided by Phase 3 as part of `DeployParams`. This is correct by design.
   - Recommendation: Phase 2 does not need to know the path. Phase 3 hardcodes it per protocol enum variant.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Rust built-in test harness (`cargo test`) |
| Config file | none — `cargo test` requires no config file |
| Quick run command | `cd d2p && cargo test` |
| Full suite command | `cd d2p && cargo test -- --include-ignored` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEP-01 | forge create arg order is correct | unit | `cargo test test_forge_args_order` | Wave 0 |
| DEP-02 | fallback triggers when forge create exits non-zero | unit (mock) | `cargo test test_runner_fallback` | Wave 0 |
| DEP-03 | --legacy absent from cast send args | unit | `cargo test test_cast_args_no_legacy` | Wave 0 |
| DEP-04 | check_prerequisites errors on missing binary | unit | `cargo test test_path_check_missing` | Wave 0 |
| DEP-05 | receipt verification calls cast receipt --json | unit (mock) | `cargo test test_verify_receipt` | Wave 0 |
| DEP-06 | --constructor-args is last in forge arg list | unit | `cargo test test_constructor_args_last` | Wave 0 |
| OUT-01 | DeployOutput display is "address\ntxhash" | unit | `cargo test test_deploy_output_display` | EXISTS (Phase 1) |
| OUT-04 | No stdout pollution — only address+hash | unit | `cargo test test_output_no_noise` | Wave 0 |

### Sampling Rate

- **Per task commit:** `cd d2p && cargo test`
- **Per wave merge:** `cd d2p && cargo test -- --include-ignored`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `d2p/tests/integration.rs` — integration smoke test calling runner with mock forge/cast on PATH
- [ ] `d2p/src/deploy/primary.rs` — unit tests for `build_args` arg order (no subprocess spawn)
- [ ] `d2p/src/deploy/fallback.rs` — unit tests for `build_args`, `read_bytecode`, no `--legacy`
- [ ] `d2p/src/deploy/verify.rs` — unit tests for receipt status parsing

**Note:** Mock forge/cast for unit testing: place minimal shell scripts at a temp path and prepend to `Command` PATH. No external process spawn needed for arg-order tests — inspect the `Command` args directly before calling `.output()`.

---

## Sources

### Primary (HIGH confidence — verified by running locally)

- Foundry v1.5.1-stable CLI (`forge create --help`, `cast send --create --help`, `cast receipt --help`) — verified flag existence and output format
- `forge create --broadcast --json` on local anvil — confirmed stdout: `{"deployer":..., "deployedTo":..., "transactionHash":...}`
- `cast send --rpc-url ... --create <BYTECODE> "constructor(address)" <ADDR> --json` on local anvil — confirmed stdout: full receipt JSON with `contractAddress` and `transactionHash`
- `cast receipt <TXHASH> --json` on local anvil — confirmed `status: "0x1"` when successful
- `cast receipt <TXHASH> status` (positional) on local anvil — confirmed returns `"1 (success)"` human string
- `d2p/out/UniswapV3Reactive.sol/UniswapV3Reactive.json` — confirmed `.bytecode.object` path with `0x` prefix
- `std::process::Command` ErrorKind::NotFound — confirmed locally when binary absent from PATH

### Secondary (MEDIUM confidence)

- [Foundry issue #770](https://github.com/foundry-rs/foundry/issues/770) — `--constructor-args` position bug (MEDIUM: issue is from 2022, behavior verified by PITFALLS.md research)
- [Foundry issue #1976](https://github.com/foundry-rs/foundry/issues/1976) — `forge create --json` mixed output concern (MEDIUM: issue is old; current v1.5.1 behavior shows clean stdout)

### Tertiary (LOW confidence — not needed; resolved by primary verification)

- STACK.md recommendation for `which` crate (LOW: overridden by verified stdlib approach)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Cargo.toml complete; no additions needed
- forge create --json output format: HIGH — verified live on Foundry v1.5.1-stable
- cast send --create arg ordering: HIGH — verified live and confirmed by help text
- Bytecode artifact path: HIGH — confirmed structure of `out/UniswapV3Reactive.sol/UniswapV3Reactive.json`
- Receipt verification approach: HIGH — verified `cast receipt --json` returns `"status":"0x1"`
- Cast receipt positional field returning human string: HIGH — verified `"1 (success)"` exactly

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (stable domain; Foundry minor updates unlikely to break JSON output fields within 30 days)
