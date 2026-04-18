//! AgentsProtocol validator — main entry point (skeleton).
//!
//! Wires up the six modules: network, consensus, validation, zk, storage,
//! config. This is a Phase-1 skeleton: the structural layout compiles and
//! the `cargo check` gate on CI passes, but most functions are todo!().

mod config;
mod consensus;
mod network;
mod storage;
mod validation;
mod zk;

use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    let cfg = config::ProtocolConfig::load()?;
    let store = storage::DagStore::open(&cfg.data_dir)?;
    let validator = validation::Validator::new(cfg.clone());
    let consensus = consensus::Ghostdag::new(cfg.clone(), &store);
    let net = network::P2p::new(cfg.clone()).await?;

    tracing::info!("AgentsProtocol validator starting (node: {})", cfg.node_id);
    net.run(&consensus, &validator, &store).await?;
    Ok(())
}
