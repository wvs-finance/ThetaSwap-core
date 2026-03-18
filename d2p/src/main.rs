mod cli;
mod deploy;
mod errors;

use anyhow::Context;
use clap::Parser;
use cli::{Cli, Commands, Protocol, TsCommands};
use deploy::{DeployParams, Runner};

fn main() {
    if let Err(e) = run() {
        eprintln!("error: {e:#}");
        std::process::exit(1);
    }
}

fn run() -> anyhow::Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Ts(ts) => match ts.command {
            TsCommands::Reactive(args) => {
                let contract_path = match args.protocol {
                    Protocol::UniswapV3 => "src/fee-concentration-index-v2/protocols/uniswap-v3/UniswapV3Reactive.sol:UniswapV3Reactive",
                };
                let project_dir = args.project.canonicalize()
                    .with_context(|| format!("project path does not exist: {}", args.project.display()))?;
                let params = DeployParams {
                    rpc_url: args.rpc_url,
                    private_key: args.private_key,
                    callback: args.callback,
                    value: args.value,
                    contract_path: contract_path.to_string(),
                    project_dir,
                };
                let output = Runner::new(params).deploy()?;
                println!("{output}");
                Ok(())
            }
        },
    }
}
