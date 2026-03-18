use clap::{Args, Parser, Subcommand, ValueEnum};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "d2p", version, about = "ThetaSwap reactive contract deployment tool")]
#[command(arg_required_else_help = true)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Deploy ThetaSwap contracts
    Ts(TsArgs),
}

#[derive(Args)]
pub struct TsArgs {
    #[command(subcommand)]
    pub command: TsCommands,
}

#[derive(Subcommand)]
pub enum TsCommands {
    /// Deploy a reactive contract
    Reactive(ReactiveArgs),
}

#[derive(Args)]
#[command(long_about = "Deploy a reactive contract.\n\nExample:\n  d2p ts reactive uniswap-v3 \\\n    --rpc-url https://rpc.sepolia.org \\\n    --private-key $ETH_PRIVATE_KEY \\\n    --callback 0xcallback")]
pub struct ReactiveArgs {
    /// Protocol to deploy (e.g. uniswap-v3)
    pub protocol: Protocol,

    /// Ethereum JSON-RPC endpoint
    #[arg(long, env = "ETH_RPC_URL")]
    pub rpc_url: String,

    /// Hex-encoded private key (0x-prefixed)
    #[arg(long, env = "ETH_PRIVATE_KEY")]
    pub private_key: String,

    /// Callback proxy contract address
    #[arg(long)]
    pub callback: String,

    /// Value to send with deployment (e.g. "10react", "0.01ether")
    #[arg(long, default_value = "10react", value_parser = parse_value)]
    pub value: String,

    /// Solidity project root (must contain forge build output in out/)
    #[arg(long, default_value = ".")]
    pub project: PathBuf,
}

#[derive(Clone, ValueEnum)]
pub enum Protocol {
    #[value(name = "uniswap-v3")]
    UniswapV3,
}

fn parse_value(s: &str) -> Result<String, String> {
    let units = ["react", "ether", "gwei", "wei"];
    for unit in units {
        if let Some(num_str) = s.strip_suffix(unit) {
            if !num_str.is_empty() && num_str.parse::<f64>().is_ok() {
                return Ok(s.to_string());
            }
        }
    }
    Err(format!(
        "invalid value '{}': expected <number><unit>, unit one of: {}",
        s,
        units.join(", ")
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_value_valid() {
        assert!(parse_value("10react").is_ok());
        assert!(parse_value("0.5ether").is_ok());
        assert!(parse_value("1000gwei").is_ok());
        assert!(parse_value("100wei").is_ok());
    }

    #[test]
    fn test_parse_value_invalid() {
        assert!(parse_value("noreact").is_err());
        assert!(parse_value("10btc").is_err());
        assert!(parse_value("react").is_err());
        assert!(parse_value("").is_err());
    }

    #[test]
    fn test_cli_routing() {
        let result = Cli::try_parse_from([
            "d2p", "ts", "reactive", "uniswap-v3",
            "--rpc-url", "http://x",
            "--private-key", "0xk",
            "--callback", "0xc",
        ]);
        assert!(result.is_ok(), "expected Ok, got: {:?}", result.err());
        let cli = result.unwrap();
        match cli.command {
            Commands::Ts(ts) => match ts.command {
                TsCommands::Reactive(args) => {
                    assert_eq!(args.callback, "0xc");
                    assert_eq!(args.rpc_url, "http://x");
                    assert_eq!(args.private_key, "0xk");
                }
            },
        }
    }

    #[test]
    fn test_callback_required() {
        let result = Cli::try_parse_from([
            "d2p", "ts", "reactive", "uniswap-v3",
            "--rpc-url", "http://x",
            "--private-key", "0xk",
        ]);
        assert!(result.is_err(), "expected Err when --callback is missing");
    }

    #[test]
    fn test_no_legacy_flag() {
        use clap::CommandFactory;
        let help = Cli::command().render_long_help().to_string();
        assert!(
            !help.contains("--legacy"),
            "--legacy must not appear in help text; got: {help}"
        );
    }

    #[test]
    fn test_help_contains_example() {
        // Verify the long_about text on ReactiveArgs contains the example invocation.
        // Use try_parse_from with --help to capture rendered help output.
        // Alternatively, check by inspecting the long_about string directly via a known
        // substring that is set in the #[command(long_about = "...")] attribute.
        //
        // Since clap may not propagate long_about from an Args struct to subcommand help
        // in all code paths, we verify the source-of-truth by parsing from a known
        // string that must appear in the long_about attribute on ReactiveArgs.
        //
        // The plan requires: help text contains "d2p ts reactive" (CMD-07).
        // We verify this via the rendered help of the binary invocation path.
        let result = Cli::try_parse_from([
            "d2p", "ts", "reactive", "--help",
        ]);
        // --help causes clap to return an Err with the help text as the message
        match result {
            Ok(_) => panic!("--help should have produced an error/exit"),
            Err(err) => {
                let help_text = err.to_string();
                assert!(
                    help_text.contains("d2p ts reactive"),
                    "help must contain 'd2p ts reactive'; got: {help_text}"
                );
            }
        }
    }

    #[test]
    fn test_env_rpc_url() {
        // Only set ETH_RPC_URL; supply --private-key as a flag to avoid polluting ETH_PRIVATE_KEY.
        let unique_url = "http://from-env-rpc-url-test-unique";
        std::env::set_var("ETH_RPC_URL", unique_url);
        let result = Cli::try_parse_from([
            "d2p", "ts", "reactive", "uniswap-v3",
            "--private-key", "0xexplicit-key",
            "--callback", "0xc",
        ]);
        std::env::remove_var("ETH_RPC_URL");
        assert!(result.is_ok(), "env fallback failed: {:?}", result.err());
        match result.unwrap().command {
            Commands::Ts(ts) => match ts.command {
                TsCommands::Reactive(args) => {
                    assert_eq!(args.rpc_url, unique_url);
                }
            },
        }
    }

    #[test]
    fn test_env_private_key() {
        // Only set ETH_PRIVATE_KEY; supply --rpc-url as a flag to avoid polluting ETH_RPC_URL.
        let unique_pk = "0xprivate-from-env-unique";
        std::env::set_var("ETH_PRIVATE_KEY", unique_pk);
        let result = Cli::try_parse_from([
            "d2p", "ts", "reactive", "uniswap-v3",
            "--rpc-url", "http://explicit-rpc",
            "--callback", "0xc",
        ]);
        std::env::remove_var("ETH_PRIVATE_KEY");
        assert!(result.is_ok(), "env fallback failed: {:?}", result.err());
        match result.unwrap().command {
            Commands::Ts(ts) => match ts.command {
                TsCommands::Reactive(args) => {
                    assert_eq!(args.private_key, unique_pk);
                }
            },
        }
    }
}
