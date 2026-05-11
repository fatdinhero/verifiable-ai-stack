//! P2P transport — gossipsub over TCP/noise/yamux + mDNS discovery.
//!
//! Topics (DevDocs §7):
//!   /agentsprotocol/claims/1.0.0   — new claims (JSON)
//!   /agentsprotocol/blocks/1.0.0   — new blocks (JSON)
//!   /agentsprotocol/control/1.0.0  — control-set updates
//!   /agentsprotocol/peers/1.0.0    — peer discovery
//!
//! Inbound claims are routed to ClaimMempool (if provided) after Ed25519
//! signature verification. Inbound blocks go to DagStore::save_block.

use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::time::Duration;

use anyhow::{Context, Result};
use libp2p::{
    gossipsub, mdns, noise,
    swarm::{NetworkBehaviour, SwarmEvent},
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

// -- Combined network behaviour -----------------------------------------------

#[derive(NetworkBehaviour)]
struct AgentsBehaviour {
    gossipsub: gossipsub::Behaviour,
    mdns: mdns::tokio::Behaviour,
}

// -- Outbound message channel -------------------------------------------------

/// Messages the application can send into the event loop.
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

    /// Returns a sender for publishing claims/blocks from outside the event loop.
    pub fn sender(&self) -> mpsc::Sender<OutboundMsg> {
        self.tx.clone()
    }

    /// Subscribe to all protocol topics, then run the event loop.
    pub async fn run(
        &mut self,
        store: &DagStore,
        mempool: Option<&ClaimMempool>,
        listen_addr: Option<libp2p::Multiaddr>,
    ) -> Result<()> {
        let mut rx = self.rx.take().context("P2p::run called twice")?;

        // -- Build swarm (mirrors official chat example) ----------------------
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
                let gossipsub_cfg = gossipsub::ConfigBuilder::default()
                    .heartbeat_interval(Duration::from_secs(10))
                    .validation_mode(gossipsub::ValidationMode::Strict)
                    .message_id_fn(message_id_fn)
                    .build()
                    .map_err(std::io::Error::other)?;

                let gossipsub = gossipsub::Behaviour::new(
                    gossipsub::MessageAuthenticity::Signed(key.clone()),
                    gossipsub_cfg,
                )?;
                let mdns = mdns::tokio::Behaviour::new(
                    mdns::Config::default(),
                    key.public().to_peer_id(),
                )?;
                Ok(AgentsBehaviour { gossipsub, mdns })
            })?
            .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
            .build();

        // -- Subscribe to topics ----------------------------------------------
        for topic_str in [TOPIC_CLAIMS, TOPIC_BLOCKS, TOPIC_CONTROL, TOPIC_PEERS] {
            let topic = gossipsub::IdentTopic::new(topic_str);
            swarm
                .behaviour_mut()
                .gossipsub
                .subscribe(&topic)
                .with_context(|| format!("failed to subscribe to {topic_str}"))?;
        }

        // -- Listen -----------------------------------------------------------
        let addr: libp2p::Multiaddr = listen_addr.unwrap_or_else(|| {
            "/ip4/0.0.0.0/tcp/0".parse().expect("valid multiaddr")
        });
        swarm.listen_on(addr)?;

        info!("P2P node starting (node_id={})", self.cfg.node_id);

        // -- Event loop -------------------------------------------------------
        loop {
            select! {
                Some(msg) = rx.recv() => {
                    match msg {
                        OutboundMsg::Claim(claim) => {
                            if let Err(e) = publish_json(
                                &mut swarm.behaviour_mut().gossipsub,
                                TOPIC_CLAIMS,
                                &claim,
                            ) {
                                warn!("publish claim {}: {e}", claim.id);
                            }
                        }
                        OutboundMsg::Block(block) => {
                            if let Err(e) = publish_json(
                                &mut swarm.behaviour_mut().gossipsub,
                                TOPIC_BLOCKS,
                                &block,
                            ) {
                                warn!("publish block {}: {e}", block.hash);
                            }
                        }
                    }
                }

                event = swarm.select_next_some() => match event {
                    SwarmEvent::Behaviour(AgentsBehaviourEvent::Gossipsub(
                        gossipsub::Event::Message { message, .. },
                    )) => {
                        handle_inbound(message, store, mempool);
                    }
                    SwarmEvent::Behaviour(AgentsBehaviourEvent::Mdns(
                        mdns::Event::Discovered(peers),
                    )) => {
                        for (peer_id, addr) in peers {
                            info!("mDNS discovered {peer_id} at {addr}");
                            swarm.behaviour_mut().gossipsub.add_explicit_peer(&peer_id);
                        }
                    }
                    SwarmEvent::Behaviour(AgentsBehaviourEvent::Mdns(
                        mdns::Event::Expired(peers),
                    )) => {
                        for (peer_id, _) in peers {
                            swarm.behaviour_mut().gossipsub.remove_explicit_peer(&peer_id);
                        }
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
    gossipsub: &mut gossipsub::Behaviour,
    topic_str: &str,
    value: &T,
) -> Result<()> {
    let data = serde_json::to_vec(value).context("serialise outbound message")?;
    let topic = gossipsub::IdentTopic::new(topic_str);
    gossipsub.publish(topic, data).context("gossipsub publish")?;
    Ok(())
}

fn handle_inbound(
    message: gossipsub::Message,
    store: &DagStore,
    mempool: Option<&ClaimMempool>,
) {
    let topic = message.topic.as_str();
    match topic {
        TOPIC_CLAIMS => {
            match serde_json::from_slice::<StoredClaim>(&message.data) {
                Ok(claim) => {
                    match verify_claim_signature(
                        &claim.submitter,
                        &claim.signature,
                        &claim.payload_json,
                    ) {
                        Ok(true) => {
                            if let Some(pool) = mempool {
                                pool.insert(claim, &[]);
                            } else if let Err(e) = store.save_claim(&claim) {
                                warn!("store claim {}: {e}", claim.id);
                            } else {
                                info!("stored inbound claim {}", claim.id);
                            }
                        }
                        Ok(false) => warn!("rejected claim {}: invalid signature", claim.id),
                        Err(e) => warn!("rejected claim {}: sig verify error: {e}", claim.id),
                    }
                }
                Err(e) => warn!("deserialise claim: {e}"),
            }
        }
        TOPIC_BLOCKS => {
            match serde_json::from_slice::<StoredBlock>(&message.data) {
                Ok(block) => {
                    if let Err(e) = store.save_block(&block) {
                        warn!("store block {}: {e}", block.hash);
                    } else {
                        info!("stored inbound block {}", block.hash);
                    }
                }
                Err(e) => warn!("deserialise block: {e}"),
            }
        }
        TOPIC_CONTROL | TOPIC_PEERS => {
            info!("received {topic} message ({} bytes)", message.data.len());
        }
        other => warn!("unknown topic: {other}"),
    }
}

// -- Convenience publish functions --------------------------------------------

pub async fn publish_claim(tx: &mpsc::Sender<OutboundMsg>, claim: StoredClaim) -> Result<()> {
    tx.send(OutboundMsg::Claim(claim))
        .await
        .context("outbound channel closed")
}

pub async fn publish_block(tx: &mpsc::Sender<OutboundMsg>, block: StoredBlock) -> Result<()> {
    tx.send(OutboundMsg::Block(block))
        .await
        .context("outbound channel closed")
}
