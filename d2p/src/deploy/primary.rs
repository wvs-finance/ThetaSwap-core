// primary.rs — forge create primary deployment strategy
// Source: verified against forge create --help and live local test on Foundry v1.5.1
//
// CRITICAL constraint (DEP-06, Foundry issue #770):
//   --constructor-args MUST be the last argument in the arg list.
//   Placing any flag after --constructor-args causes forge create to treat
//   subsequent flag names as constructor argument values.
//
// ENV constraint: ETH_RPC_URL is removed from subprocess environment.
//   If caller exports ETH_RPC_URL pointing to a different chain, some Foundry
//   versions use it instead of the explicit --rpc-url flag.
use crate::{
    deploy::{DeployOutput, DeployParams},
    errors::D2pError,
};

/// Deserialization target for `forge create --json` stdout.
///
/// Verified output shape on Foundry v1.5.1-stable:
/// `{"deployer":"0x...","deployedTo":"0x...","transactionHash":"0x..."}`
#[derive(serde::Deserialize)]
struct ForgeCreateJson {
    #[serde(rename = "deployedTo")]
    deployed_to: String,
    #[serde(rename = "transactionHash")]
    transaction_hash: String,
}

/// Run `forge create` with structured JSON output and return the deployed address + tx hash.
///
/// Fails with `D2pError::ProcessNotFound` if `forge` is not on PATH.
/// Fails with `D2pError::NonZeroExit` if forge exits non-zero.
/// Fails with `D2pError::ParseFailure` if stdout is not valid ForgeCreateJson.
pub fn run(params: &DeployParams) -> anyhow::Result<DeployOutput> {
    let args = build_args(params);

    let out = std::process::Command::new("forge")
        .args(&args)
        .current_dir(&params.project_dir)
        // Remove ETH_RPC_URL so it cannot shadow the explicit --rpc-url flag (Pitfall 6)
        .env_remove("ETH_RPC_URL")
        .output()
        .map_err(|e| match e.kind() {
            std::io::ErrorKind::NotFound => D2pError::ProcessNotFound("forge".to_string()),
            _ => D2pError::NonZeroExit {
                stderr: e.to_string(),
            },
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

/// Build the argument vector for `forge create`.
///
/// Arg order is critical (DEP-01, DEP-06):
///   [create, contract_path, --rpc-url, ..., --broadcast, --legacy, --value, ..., --json,
///    --constructor-args, callback]
///
/// --constructor-args MUST be last — it is variadic and forge treats everything after it
/// as constructor argument values.
fn build_args(params: &DeployParams) -> Vec<String> {
    vec![
        "create".to_string(),
        params.contract_path.clone(),
        "--rpc-url".to_string(),
        params.rpc_url.clone(),
        "--private-key".to_string(),
        params.private_key.clone(),
        "--broadcast".to_string(),
        "--legacy".to_string(),
        "--value".to_string(),
        params.value.clone(),
        "--json".to_string(),
        // LAST — variadic; must come after all other flags (Foundry issue #770)
        "--constructor-args".to_string(),
        params.callback.clone(),
    ]
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    fn test_params() -> DeployParams {
        DeployParams {
            rpc_url: "https://rpc.example.com".to_string(),
            private_key: "0xdeadbeef".to_string(),
            callback: "0xcallback000000000000000000000000000000".to_string(),
            value: "10react".to_string(),
            contract_path: "src/UniswapV3Reactive.sol:UniswapV3Reactive".to_string(),
            project_dir: PathBuf::from("/tmp"),
        }
    }

    /// DEP-06: "create" at index 0, contract_path at index 1,
    /// and the last three elements are "--constructor-args" + callback value.
    #[test]
    fn test_forge_args_order() {
        let args = build_args(&test_params());

        assert_eq!(args[0], "create", "index 0 must be 'create'");
        assert_eq!(
            args[1], "src/UniswapV3Reactive.sol:UniswapV3Reactive",
            "index 1 must be contract_path"
        );

        let len = args.len();
        assert_eq!(
            args[len - 2],
            "--constructor-args",
            "second-to-last must be '--constructor-args'"
        );
        assert_eq!(
            args[len - 1],
            "0xcallback000000000000000000000000000000",
            "last must be callback value"
        );
    }

    /// DEP-01: --legacy flag must be present in the arg vec.
    #[test]
    fn test_forge_args_contains_legacy() {
        let args = build_args(&test_params());
        assert!(
            args.iter().any(|a| a == "--legacy"),
            "build_args must include '--legacy'"
        );
    }

    /// DEP-01: --broadcast flag must be present in the arg vec.
    #[test]
    fn test_forge_args_contains_broadcast() {
        let args = build_args(&test_params());
        assert!(
            args.iter().any(|a| a == "--broadcast"),
            "build_args must include '--broadcast'"
        );
    }

    /// Structural test: ETH_RPC_URL must not appear as a string argument in build_args.
    /// The actual env_remove call is in run() — this test confirms build_args does not
    /// accidentally include "ETH_RPC_URL" as an arg string, which would be a separate bug.
    #[test]
    fn test_forge_args_no_env_inheritance() {
        let args = build_args(&test_params());
        assert!(
            !args.iter().any(|a| a == "ETH_RPC_URL"),
            "build_args must not include 'ETH_RPC_URL' as an argument string"
        );
    }

    /// JSON parsing: ForgeCreateJson deserializes camelCase fields correctly.
    #[test]
    fn test_parse_forge_json() {
        let json = r#"{"deployedTo":"0xABC","transactionHash":"0xDEF","deployer":"0x123"}"#;
        let parsed: ForgeCreateJson = serde_json::from_str(json)
            .expect("should deserialize valid forge create JSON");
        assert_eq!(parsed.deployed_to, "0xABC");
        assert_eq!(parsed.transaction_hash, "0xDEF");
    }
}
