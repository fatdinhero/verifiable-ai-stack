//! P2P transport — gossipsub over TCP/noise/yamux + mDNS discovery.
//!
//! Topics (DevDocs §7):
//!   /agentsprotocol/claims/1.0.0
//!   /agentsprotocol/blocks/1.0.0
//!   /agentsprotocol/control/1.0.0
//!   /agentsprotocol/peers/1.0.0
//!
//! Uses gossipsub only (no combined NetworkBehaviour derive) to avoid
//! libp2p proc-macro compatibility issues. mDNS peer discovery is handled
//! via a separate task in Phase 3.

use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::time::Duration;

use anyhow::{Context, Result};
use libp2p::{
    gossipsub, noise,
    swarm::SwarmEvent,
    tcp, yamux,
};
use tokio::select;
use tokio::sync::mpsc;
use tracing::{info, warn};

use crate::config::ProtocolConfig;
use crate::mempool::ClaimMempool;
use crate::storage::{DagStore, StoredBlock, StoredClaim};
use crate::validation::verify_claim_signature;

// -- Topic constants ----------------------------------------------------------

pub const TOPIC_CLAIMS: &str = "/agentsprotocol/claims/1.0.0";
pub const TOPIC_BLOCKS: &str = "/agentsprotocol/blocks/1.0.0";
pub const TOPIC_CONTROL: &str = "/agentsprotocol/control/1.0.0";
pub const TOPIC_PEERS: &str = "/agentsprotocol/peers/1.0.0";

// -- Outbound message channel -------------------------------------------------

pub enum OutboundMsg {
    Claim(StoredClaim),
    Block(StoredBlock),
}

// -- P2p ----------------------------------------------------------------------

pub struct P2p {
    pub cfg: ProtocolConfig,
    tx: mpsc::Sender<OutboundMsg>,
    rx: Option<mpsc::Receiver<OutboundMsg>>,
}

impl P2p {
    pub async fn new(cfg: ProtocolConfig) -> Result<Self> {
        let (tx, rx) = mpsc::channel(256);
        Ok(Self { cfg, tx, rx: Some(rx) })
    }

    pub fn sender(&self) -> mpsc::Sender<OutboundMsg> {
        self.tx.clone()
    }

    pub async fn run(
        &mut self,
        store: &DagStore,
        mempool: Option<&ClaimMempool>,
        listen_addr: Option<libp2p::Multiaddr>,
    ) -> Result<()> {
        let mut rx = self.rx.take().context("P2p::run called twice")?;

        // Build swarm with gossipsub only
        let mut swarm = libp2p::SwarmBuilder::with_new_identity()
            .with_tokio()
            .with_tcp(
                tcp::Config::default(),
                noise::Config::new,
                yamux::Config::default,
            )?
            .with_behaviour(|key| {
                let message_id_fn = |msg: &gossipsub::Message| {
                    let mut s = DefaultHasher::new();
                    msg.data.hash(&mut s);
                    gossipsub::MessageId::from(s.finish().to_string())
                };
                gossipsub::Behaviour::new(
                    gossipsub::MessageAuthenticity::Signed(key.clone()),
                    gossipsub::ConfigBuilder::default()
                        .heartbeat_interval(Duration::from_secs(10))
                        .validation_mode(gossipsub::ValidationMode::Strict)
                        .message_id_fn(message_id_fn)
                        .build()
                        .expect("valid gossipsub config"),
                )
                .expect("valid gossipsub behaviour")
            })?
            .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
            .build();

        // Subscribe to all protocol topics
        for topic_str in [TOPIC_CLAIMS, TOPIC_BLOCKS, TOPIC_CONTROL, TOPIC_PEERS] {
            swarm
                .behaviour_mut()
                .subscribe(&gossipsub::IdentTopic::new(topic_str))
                .with_context(|| format!("subscribe to {topic_str}"))?;
        }

        let addr: libp2p::Multiaddr = listen_addr
            .unwrap_or_else(|| "/ip4/0.0.0.0/tcp/0".parse().expect("valid multiaddr"));
        swarm.listen_on(addr)?;

        info!("P2P node starting (node_id={})", self.cfg.node_id);

        loop {
            select! {
                Some(msg) = rx.recv() => {
                    match msg {
                        OutboundMsg::Claim(claim) => {
                            if let Err(e) = publish_json(swarm.behaviour_mut(), TOPIC_CLAIMS, &claim) {
                                warn!("publish claim {}: {e}", claim.id);
                            }
                        }
                        OutboundMsg::Block(block) => {
                            if let Err(e) = publish_json(swarm.behaviour_mut(), TOPIC_BLOCKS, &block) {
                                warn!("publish block {}: {e}", block.hash);
                            }
                        }
                    }
                }

                event = swarm.select_next_some() => match event {
                    SwarmEvent::Behaviour(gossipsub::Event::Message { message, .. }) => {
                        handle_inbound(message, store, mempool);
                    }
                    SwarmEvent::NewListenAddr { address, .. } => {
                        info!("listening on {address}");
                    }
                    _ => {}
                }
            }
        }
    }
}

// -- Helpers ------------------------------------------------------------------

fn publish_json<T: serde::Serialize>(
    behaviour: &mut gossipsub::Behaviour,
    topic_str: &str,
    value: &T,
) -> Result<()> {
    let data = serde_json::to_vec(value).context("serialise")?;
    behaviour
        .publish(gossipsub::IdentTopic::new(topic_str), data)
        .context("gossipsub publish")?;
    Ok(())
}

fn handle_inbound(
    message: gossipsub::Message,
    store: &DagStore,
    mempool: Option<&ClaimMempool>,
) {
    let topic = message.topic.as_str();
    match topic {
        TOPIC_CLAIMS => match serde_json::from_slice::<StoredClaim>(&message.data) {
            Ok(claim) => match verify_claim_signature(&claim.submitter, &claim.signature, &claim.payload_json) {
                Ok(true) => {
                    if let Some(pool) = mempool {
                        pool.insert(claim, &[]);
                    } else if let Err(e) = store.save_claim(&claim) {
                        warn!("store claim {}: {e}", claim.id);
                    }
                }
                Ok(false) => warn!("rejected claim {}: invalid signature", claim.id),
                Err(e)    => warn!("rejected claim {}: {e}", claim.id),
            },
            Err(e) => warn!("deserialise claim: {e}"),
        },
        TOPIC_BLOCKS => match serde_json::from_slice::<StoredBlock>(&message.data) {
            Ok(block) => {
                if let Err(e) = store.save_block(&block) {
                    warn!("store block {}: {e}", block.hash);
                } else {
                    info!("stored block {}", block.hash);
                }
            }
            Err(e) => warn!("deserialise block: {e}"),
        },
        other => info!("received {other} ({} bytes)", message.data.len()),
    }
}

// -- Convenience publish functions --------------------------------------------

pub async fn publish_claim(tx: &mpsc::Sender<OutboundMsg>, claim: StoredClaim) -> Result<()> {
    tx.send(OutboundMsg::Claim(claim)).await.context("channel closed")
}

pub async fn publish_block(tx: &mpsc::Sender<OutboundMsg>, block: StoredBlock) -> Result<()> {
    tx.send(OutboundMsg::Block(block)).await.context("channel closed")
}
