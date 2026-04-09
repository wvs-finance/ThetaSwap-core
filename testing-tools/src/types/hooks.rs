use std::{future::Future, pin::Pin};

use super::config::DevnetConfig;
use crate::{controllers::enviroments::AngstromTestnet, providers::WalletProvider};

pub enum StateMachineHook<'a, C: Unpin> {
    Action(StateMachineActionHookFn<'a, C>),
    Check(StateMachineCheckHookFn<C>),
    CheckedAction(StateMachineCheckedActionHookFn<'a, C>)
}

/// execute an action on the testnet
pub type StateMachineActionHookFn<'a, C> = Box<
    dyn FnOnce(
        &'a mut AngstromTestnet<C, DevnetConfig, WalletProvider>
    ) -> Pin<Box<dyn Future<Output = eyre::Result<()>> + Send + 'a>>
>;

/// check something on the testnet
pub type StateMachineCheckHookFn<C> =
    Box<dyn FnOnce(&mut AngstromTestnet<C, DevnetConfig, WalletProvider>) -> eyre::Result<bool>>;

/// execute an action and check something on the testnet
pub type StateMachineCheckedActionHookFn<'a, C> = Box<
    dyn FnOnce(
        &'a mut AngstromTestnet<C, DevnetConfig, WalletProvider>
    ) -> Pin<Box<dyn Future<Output = eyre::Result<bool>> + Send + Sync + 'a>>
>;

pub(crate) trait HookResult: Sized {
    fn error(&self) -> Option<&eyre::ErrReport>;

    fn is_pass(&self) -> bool;

    fn fmt_result(self, i: usize, name: &'static str) {
        if let Some(e) = self.error() {
            tracing::error!(target: "devnet::state-machine", hook = i, name, "{:?}", e);
            panic!("{:?}", e.root_cause());
        }

        if self.is_pass() {
            tracing::info!(target: "devnet::state-machine", hook = i, name, "hook PASSED");
        } else {
            tracing::error!(target: "devnet::state-machine", hook = i, name, "hook FAILED");
            panic!()
        }
    }
}

impl HookResult for eyre::Result<()> {
    fn is_pass(&self) -> bool {
        self.is_ok()
    }

    fn error(&self) -> Option<&eyre::ErrReport> {
        self.as_ref().err()
    }
}

impl HookResult for eyre::Result<bool> {
    fn is_pass(&self) -> bool {
        matches!(self.as_ref(), Ok(true))
    }

    fn error(&self) -> Option<&eyre::ErrReport> {
        self.as_ref().err()
    }
}
