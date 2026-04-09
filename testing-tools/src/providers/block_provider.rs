use alloy_rpc_types::{Block, Transaction};
use tokio::sync::broadcast;
use tokio_stream::wrappers::BroadcastStream;

pub struct TestnetBlockProvider {
    tx: broadcast::Sender<(u64, Vec<Transaction>)>
}

impl Default for TestnetBlockProvider {
    fn default() -> Self {
        Self::new()
    }
}

impl TestnetBlockProvider {
    pub fn new() -> Self {
        let (tx, _) = broadcast::channel(1000);
        Self { tx }
    }

    pub fn subscribe_to_new_blocks(&self) -> BroadcastStream<(u64, Vec<Transaction>)> {
        BroadcastStream::new(self.tx.subscribe())
    }

    pub fn broadcast_block(&self, block: Block) {
        let block_num = block.header.number;
        let txs = block.transactions.as_transactions().unwrap().to_vec();

        let _ = self.tx.send((block_num, txs));
    }
}
