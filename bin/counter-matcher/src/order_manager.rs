use std::{collections::HashMap, sync::Arc};

use alloy_primitives::B256;
use angstrom_rpc::{api::OrderApiClient, types::OrderSubscriptionResult};
use angstrom_types::{
    matching::Ray,
    orders::CancelOrderRequest,
    sol_bindings::{RawPoolOrder, grouped_orders::AllOrders}
};
use itertools::Itertools;
use jsonrpsee::ws_client::WsClient;
use secp256k1::rand;
use sepolia_bundle_lander::env::ProviderType;
use testing_tools::type_generator::orders::UserOrderBuilder;

use crate::accounting::WalletAccounting;

/// holds orders that are currently being processed.
pub struct OrderManager {
    block_number: u64,
    wallets:      Vec<WalletAccounting>,
    provider:     Arc<ProviderType>,

    /// our active orders to the wallet that signed them.
    /// due to how we do accounting, we don't have to store the order
    active_orders: HashMap<B256, (usize, AllOrders)>,
    /// map of user order to our active counter order
    user_orders:   HashMap<B256, B256>,
    client:        Arc<WsClient>
}

impl OrderManager {
    pub fn new(
        block_number: u64,
        provider: Arc<ProviderType>,
        wallets: Vec<WalletAccounting>,
        client: Arc<WsClient>
    ) -> Self {
        Self {
            block_number,
            provider,
            wallets,
            client,
            active_orders: Default::default(),
            user_orders: Default::default()
        }
    }

    pub async fn shutdown(mut self) {
        tracing::info!("canceling all orders");
        let keys = self.user_orders.keys().cloned().collect_vec();
        for hash in keys {
            self.on_order_cancel(hash).await;
        }
    }

    pub async fn new_block(&mut self, block_number: u64) {
        for wallet in &mut self.wallets {
            wallet
                .update_balances_for_block(block_number, self.provider.clone())
                .await;
        }
        self.block_number = block_number;
    }

    pub async fn handle_event(&mut self, event: OrderSubscriptionResult) {
        tracing::info!(?event, "new event detected");
        match event {
            OrderSubscriptionResult::NewOrder(order) => {
                self.on_new_order(order).await;
            }
            OrderSubscriptionResult::FilledOrder(_, order) => self.on_filled_order(order).await,
            OrderSubscriptionResult::ExpiredOrder(hash) => {
                self.on_expired_order(hash.order_hash());
            }
            OrderSubscriptionResult::CancelledOrder(hash) => self.on_order_cancel(hash).await,
            _ => unreachable!()
        }
    }

    /// handles when a new order is pulled from the stream.
    pub async fn on_new_order(&mut self, order: AllOrders) {
        let hash = order.order_hash();
        if order.is_tob() || self.active_orders.contains_key(&hash) {
            // this is a order we placed
            return;
        }

        self.try_create_counter_order(&order).await;
    }

    pub fn on_expired_order(&mut self, hash: B256) {
        // we never have to worry about a user order
        // being expired as we match our expires to our counter orders
        if let Some((index, order)) = self.active_orders.remove(&hash) {
            tracing::info!(?hash, "our order expired");
            let wallet = &mut self.wallets[index];
            wallet.remove_order(order.token_in(), &hash);
            return;
        }

        // if not our order, remove user order.
        self.user_orders.remove(&hash);
    }

    /// if one of our order is filled. we will remove the pending allocation
    pub async fn on_filled_order(&mut self, order: AllOrders) {
        let hash = order.order_hash();
        if order.is_tob() {
            return;
        };

        // if its a user order. lets try to optimistically cancel ours
        self.on_order_cancel(hash).await;

        if let Some((index, _)) = self.active_orders.remove(&hash) {
            tracing::info!(?hash, "our order filled");
            let wallet = &mut self.wallets[index];
            wallet.remove_order(order.token_in(), &hash);
        }
    }

    pub async fn on_order_cancel(&mut self, hash: B256) {
        let Some(our_hash) = self.user_orders.remove(&hash) else { return };
        let Some((wallet, order)) = self.active_orders.remove(&our_hash) else { return };

        let order_wallet = &mut self.wallets[wallet];
        let addr = order_wallet.pk.address();
        let cancel_request = CancelOrderRequest::new(addr, our_hash, &order_wallet.pk);

        let cancel_res = self.client.cancel_order(cancel_request).await.unwrap();
        if !cancel_res {
            tracing::info!("failed to cancel order");
            return;
        }
        tracing::info!(?our_hash, "canceled our order");
        // remove the token in that we allocated to this order
        order_wallet.remove_order(order.token_in(), &our_hash);
    }

    // this order will be partial
    async fn try_create_counter_order(&mut self, placed_user_order: &AllOrders) {
        // calculate the flipped order token and amounts
        let price_1_0 = if placed_user_order.is_bid() {
            Ray::from(placed_user_order.limit_price()).inv_ray_round(true)
        } else {
            Ray::from(placed_user_order.limit_price())
        };

        let (token_in, token_out, mut amount_needed, mut price) = if !placed_user_order.exact_in() {
            (
                placed_user_order.token_out(),
                placed_user_order.token_in(),
                placed_user_order.amount(),
                Ray::from(placed_user_order.limit_price())
                    .inv_ray_round(!placed_user_order.is_bid())
            )
        } else {
            // is exact in. need to get amount out

            let amount = if placed_user_order.is_bid() {
                // one for zero
                price_1_0.inverse_quantity(placed_user_order.amount(), true)
            } else {
                // zero for 1
                price_1_0.quantity(placed_user_order.amount(), false)
            };

            (
                placed_user_order.token_out(),
                placed_user_order.token_in(),
                amount,
                // always other side.
                Ray::from(placed_user_order.limit_price())
                    .inv_ray_round(!placed_user_order.is_bid())
            )
        };
        // lower price to give more landing ops
        let pct = Ray::generate_ray_decimal(90, 2);
        price.mul_ray_assign(pct);

        // see if there is any wallet that can supply these amounts

        // will add an extra 10% to the amount
        amount_needed = (amount_needed as f64 * 1.1) as u128;
        // see if there is any wallet that can supply these amounts
        // will add an extra 5% to the amount

        let Some((wallet_index, wallet)) = self
            .wallets
            .iter_mut()
            .enumerate()
            // we randomize the order here so that we don't always use the same wallet, yet we will
            // check all of them
            .sorted_by_key(|(..)| rand::random::<usize>())
            .find(|(_, wallet)| wallet.can_support_amount(&token_in, amount_needed))
        else {
            tracing::info!(?placed_user_order, "no wallet has enough to support user order");
            return;
        };

        // order with deadline and nonce
        let order: AllOrders = if let Some(deadline) = placed_user_order.deadline() {
            let nonce = self.client.valid_nonce(wallet.pk.address()).await.unwrap();
            UserOrderBuilder::default()
                .partial()
                .standing()
                .nonce(nonce)
                .deadline(deadline)
                .exact_in(true)
                .amount(amount_needed)
                .asset_in(token_in)
                .asset_out(token_out)
                .min_price(price)
                .recipient(wallet.pk.address())
                .signing_key(Some(wallet.pk.clone()))
                .build()
        } else {
            UserOrderBuilder::default()
                .partial()
                .kill_or_fill()
                .exact_in(true)
                .amount(amount_needed)
                .asset_in(token_in)
                .asset_out(token_out)
                .min_price(price)
                .recipient(wallet.pk.address())
                .signing_key(Some(wallet.pk.clone()))
                .build()
        };

        let our_order_hash = order.order_hash();

        self.user_orders
            .insert(placed_user_order.order_hash(), our_order_hash);
        self.active_orders
            .insert(our_order_hash, (wallet_index, order.clone()));

        let res = self.client.send_order(order).await.unwrap();

        if !res.is_success {
            tracing::error!(?res, "failed to place counter order");

            self.active_orders.remove(&our_order_hash);
            self.user_orders.remove(&placed_user_order.order_hash());
            return;
        }
        tracing::info!(
            ?our_order_hash,
            user_hash = ?placed_user_order.order_hash(),
            "placed counter order"
        );

        // add order to wallet accounting
        wallet.add_order(token_in, our_order_hash, amount_needed);
    }
}
