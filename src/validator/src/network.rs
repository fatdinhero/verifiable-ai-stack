//! P2P transport (libp2p) — skeleton.
//!
//! Topics defined in DevDocs Section 7:
//!   /agentsprotocol/claims/1.0.0
//!   /agentsprotocol/blocks/1.0.0
//!   /agentsprotocol/control/1.0.0
//!   /agentsprotocol/peers/1.0.0

use anyhow::Result;

use crate::config::ProtocolConfig;
use crate::consensus::Ghostdag;
use crate::storage::DagStore;
use crate::validation::Validator;

pub const TOPIC_CLAIMS: &str  = "/agentsprotocol/claims/1.0.0";
pub const TOPIC_BLOCKS: &str  = "/agentsprotocol/blocks/1.0.0";
pub const TOPIC_CONTROL: &str = "/agentsprotocol/control/1.0.0";
pub const TOPIC_PEERS: &str   = "/agentsprotocol/peers/1.0.0";

pub struct P2p { pub cfg: ProtocolConfig }

impl P2p {
    pub async fn new(cfg: ProtocolConfig) -> Result<Self> { Ok(Self { cfg }) }

    pub async fn run(
        &self, _consensus: &Ghostdag<'_>,
        _validator: &Validator, _store: &DagStore,
    ) -> Result<()> {
        tracing::warn!("network::P2p::run is a skeleton");
        Ok(())
    }
}
