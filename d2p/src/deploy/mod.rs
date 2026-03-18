pub mod primary;

use std::path::PathBuf;

/// All inputs required to attempt a deployment via any strategy.
#[derive(Debug)]
pub struct DeployParams {
    pub rpc_url: String,
    pub private_key: String,
    pub callback: String,
    pub value: String,
    pub contract_path: String,
    pub project_dir: PathBuf,
}

/// Successful deployment result — pipe-friendly two-line output.
#[derive(Debug)]
pub struct DeployOutput {
    pub address: String,
    pub tx_hash: String,
}

impl std::fmt::Display for DeployOutput {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "{}", self.address)?;
        write!(f, "{}", self.tx_hash)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_deploy_output_display() {
        let out = DeployOutput {
            address: "0xABC".to_string(),
            tx_hash: "0xDEF".to_string(),
        };
        assert_eq!(out.to_string(), "0xABC\n0xDEF");
    }

    #[test]
    fn test_deploy_params_debug() {
        let params = DeployParams {
            rpc_url: "https://rpc.example.com".to_string(),
            private_key: "0xdeadbeef".to_string(),
            callback: "0xcallback".to_string(),
            value: "10react".to_string(),
            contract_path: "src/UniswapV3Reactive.sol:UniswapV3Reactive".to_string(),
            project_dir: PathBuf::from("/tmp"),
        };
        let debug_str = format!("{:?}", params);
        assert!(debug_str.contains("rpc_url"));
        assert!(debug_str.contains("project_dir"));
    }
}
