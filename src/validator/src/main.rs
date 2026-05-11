//! AgentsProtocol validator — main entry point.
//!
//! Startup sequence:
//!   1. Open RocksDB storage
//!   2. Create ClaimMempool (S_con-sorted)
//!   3. Create P2p (gets net_tx sender)
//!   4. Spawn BlockProducer task (uses net_tx)
//!   5. Spawn RPC server task (axum, cfg.rpc_addr)
//!   6. Run P2P event loop

mod config;
mod consensus;
mod mempool;
mod network;
mod rpc;
mod storage;
mod validation;
mod zk;

use std::sync::Arc;

use anyhow::Result;
use crate::mempool::{BlockProducer, ClaimMempool};

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt::init();

    let cfg = config::ProtocolConfig::load()?;

    let store = Arc::new(storage::DagStore::open(&cfg.data_dir)?);
    let mempool = Arc::new(ClaimMempool::new(cfg.clone()));
    let mut net = network::P2p::new(cfg.clone()).await?;
    let net_tx = net.sender();

    // BlockProducer — drains mempool, assembles blocks, publishes via net_tx
    let producer = BlockProducer::new(
        cfg.clone(),
        Arc::clone(&mempool),
        Arc::clone(&store),
        net_tx,
    );
    tokio::spawn(async move {
        if let Err(e) = producer.run().await {
            tracing::error!("BlockProducer: {e}");
        }
    });

    // RPC server — submit_claim, get_block/:hash, status
    let rpc_state = rpc::AppState {
        node_id: cfg.node_id.clone(),
        store: Arc::clone(&store),
        mempool: Arc::clone(&mempool),
    };
    let rpc_addr = cfg.rpc_addr.clone();
    tokio::spawn(async move {
        if let Err(e) = rpc::serve(&rpc_addr, rpc_state).await {
            tracing::error!("RPC server: {e}");
        }
    });

    tracing::info!("AgentsProtocol validator starting (node: {})", cfg.node_id);
    let listen_addr = cfg.listen_addr.parse().ok();
    net.run(&store, Some(&mempool), listen_addr).await?;

    Ok(())
}
