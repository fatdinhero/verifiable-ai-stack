//! AgentsProtocol validator — main entry point.
//!
//! Wires up: config, storage, validation, consensus, network.
//! Phase 2: network event loop is live; zk and RPC are Phase 3.

mod config;
mod consensus;
mod network;
mod storage;
mod validation;
mod zk;

use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt::init();

    let cfg = config::ProtocolConfig::load()?;
    let store = storage::DagStore::open(&cfg.data_dir)?;
    let _validator = validation::Validator::new(cfg.clone());
    let _consensus = consensus::Ghostdag::new(cfg.clone(), &store);
    let mut net = network::P2p::new(cfg.clone()).await?;

    tracing::info!("AgentsProtocol validator starting (node: {})", cfg.node_id);
    net.run(&store, None).await?;
    Ok(())
}
