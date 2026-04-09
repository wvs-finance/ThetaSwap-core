use std::{collections::HashMap, sync::Arc};

use alloy::{
    network::TransactionBuilder, providers::Provider, signers::local::PrivateKeySigner,
    sol_types::SolCall
};
use alloy_primitives::{Address, B256, TxKind};
use alloy_rpc_types::TransactionRequest;
use angstrom_types::primitive::AngstromSigner;
use sepolia_bundle_lander::env::ProviderType;

// fetch balances.
alloy::sol!(
    function balanceOf(address _owner) public view returns (uint256 balance);
);

/// 20% of our total token for the account can be used.
const MAX_AMOUNT_PER_TOKEN: f64 = 0.2;

/// used to see what wallet should create the orders
pub struct WalletAccounting {
    pub pk:              AngstromSigner<PrivateKeySigner>,
    tokens:              Vec<Address>,
    on_chain:            HashMap<Address, u128>,
    // token -> order_id -> amount
    pending_adjustments: HashMap<Address, HashMap<B256, u128>>
}

impl WalletAccounting {
    /// initializes the wallet with the curent
    pub async fn new(
        block_number: u64,
        pk: AngstromSigner<PrivateKeySigner>,
        tokens: Vec<Address>,
        provider: Arc<ProviderType>
    ) -> Self {
        let mut this = Self {
            pk,
            tokens,
            on_chain: Default::default(),
            pending_adjustments: Default::default()
        };
        this.update_balances_for_block(block_number, provider).await;

        this
    }

    pub async fn update_balances_for_block(
        &mut self,
        block_number: u64,
        provider: Arc<ProviderType>
    ) {
        let addr = self.pk.address();

        for token in &self.tokens {
            let balance = self
                .make_call(
                    provider.clone(),
                    block_number,
                    addr,
                    *token,
                    balanceOfCall::new((addr,))
                )
                .await;

            self.on_chain.insert(*token, balance.to::<u128>());
        }
    }

    pub fn add_order(&mut self, token: Address, order_id: B256, amount: u128) {
        self.pending_adjustments
            .entry(token)
            .or_default()
            .insert(order_id, amount);
    }

    pub fn remove_order(&mut self, token: Address, order_id: &B256) {
        self.pending_adjustments
            .entry(token)
            // should never be hit
            .or_default()
            .remove(order_id);
    }

    /// the order here is the counter matched order.
    /// NOTABLY, we have a max allocation of 20% of the balance of the account
    /// that can be swapped.
    pub fn can_support_amount(&self, token_in: &Address, amount: u128) -> bool {
        let funds = (self.available_funds(token_in) as f64 * MAX_AMOUNT_PER_TOKEN) as u128;

        funds >= amount
    }

    fn available_funds(&self, token: &Address) -> u128 {
        self.on_chain
            .get(token)
            .cloned()
            .map(|mut amount| {
                // take all values and then saturating_sub them;
                if let Some(pending) = self.pending_adjustments.get(token) {
                    pending.values().for_each(|am| {
                        amount = amount.saturating_sub(*am);
                    });
                }

                amount
            })
            .unwrap_or_default()
    }

    async fn make_call<TY: SolCall>(
        &self,
        provider: Arc<ProviderType>,
        block_number: u64,
        from: Address,
        target: Address,
        call: TY
    ) -> TY::Return {
        let bytes = provider
            .call(
                TransactionRequest::default()
                    .with_from(from)
                    .with_kind(TxKind::Call(target))
                    .with_input(call.abi_encode())
            )
            .block(block_number.into())
            .await
            .unwrap();
        TY::abi_decode_returns(&bytes).unwrap()
    }
}
