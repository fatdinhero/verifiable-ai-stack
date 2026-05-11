//! AgentsProtocol validator — main entry point.
//!
//! Startup sequence:
//!   1. Open RocksDB storage
//!   2. Create ClaimMempool (S_con-sorted)
//!   3. Spawn BlockProducer task (drains mempool, assembles + publishes blocks)
//!   4. Run P2P event loop (routes inbound claims to mempool, blocks to store)

mod config;
mod consensus;
mod mempool;
mod network;
mod storage;
mod validation;
mod zk;

use std::sync::Arc;

use anyhow::Result;

use mempool::{BlockProducer, ClaimMempool};

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt::init();

    let cfg = config::ProtocolConfig::load()?;

    // -- Storage --------------------------------------------------------------
    let store = Arc::new(storage::DagStore::open(&cfg.data_dir)?);

    // -- Mempool --------------------------------------------------------------
    let mempool = Arc::new(ClaimMempool::new(cfg.clone()));

    // -- Network --------------------------------------------------------------
    let mut net = network::P2p::new(cfg.clone()).await?;
    let net_tx = net.sender();

    // -- Block producer -------------------------------------------------------
    let producer = BlockProducer::new(
        cfg.clone(),
        Arc::clone(&mempool),
        Arc::clone(&store),
        net_tx,
    );
    tokio::spawn(async move {
        if let Err(e) = producer.run().await {
            tracing::error!("BlockProducer error: {e}");
        }
    });

    // -- P2P event loop (blocks until shutdown) -------------------------------
    tracing::info!("AgentsProtocol validator starting (node: {})", cfg.node_id);
    net.run(&store, Some(&mempool), None).await?;

    Ok(())
}
