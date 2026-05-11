//! P2P transport — gossipsub over TCP/noise/yamux.
//!
//! Topics (DevDocs §7):
//!   /agentsprotocol/claims/1.0.0   — new claims (JSON)
//!   /agentsprotocol/blocks/1.0.0   — new blocks (JSON)
//!   /agentsprotocol/control/1.0.0  — control-set updates
//!   /agentsprotocol/peers/1.0.0    — peer discovery
//!
//! The event loop receives gossipsub messages and routes them to DagStore:
//!   claims topic  → DagStore::save_claim
//!   blocks topic  → DagStore::save_block

use std::hash::{Hash, Hasher};
use std::time::Duration;

use anyhow::{Context, Result};
use futures::StreamExt;
use libp2p::{
    gossipsub::{self, IdentTopic, MessageAuthenticity, ValidationMode},
    mdns,
    noise,
    swarm::{NetworkBehaviour, SwarmEvent},
    tcp, yamux, Multiaddr, SwarmBuilder,
};
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
    /// Sender half — clone this to publish claims/blocks from the RPC layer.
    tx: mpsc::Sender<OutboundMsg>,
    /// Receiver half — consumed by `run()`.
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
    ///
    /// Incoming claims are routed to `mempool` (if provided) or directly to
    /// `store.save_claim`. Incoming blocks go to `store.save_block`.
    /// mDNS peer discovery is handled automatically.
    pub async fn run(
        &mut self,
        store: &DagStore,
        mempool: Option<&ClaimMempool>,
        listen_addr: Option<Multiaddr>,
    ) -> Result<()> {
        // -- Build swarm ------------------------------------------------------
        let mut swarm = SwarmBuilder::with_new_identity()
            .with_tokio()
            .with_tcp(
                tcp::Config::default(),
                noise::Config::new,
                yamux::Config::default,
            )?
            .with_behaviour(|key| {
                // Gossipsub: message-id = SHA-256(source + seq_no + data)
                let msg_id_fn = |msg: &gossipsub::Message| {
                    let mut s = std::collections::hash_map::DefaultHasher::new();
                    msg.data.hash(&mut s);
                    gossipsub::MessageId::from(s.finish().to_string())
                };
                let gossipsub_cfg = gossipsub::ConfigBuilder::default()
                    .heartbeat_interval(Duration::from_secs(10))
                    .validation_mode(ValidationMode::Strict)
                    .message_id_fn(msg_id_fn)
                    .build()
                    .expect("valid gossipsub config");

                let gossipsub = gossipsub::Behaviour::new(
                    MessageAuthenticity::Signed(key.clone()),
                    gossipsub_cfg,
                )
                .expect("gossipsub behaviour");

                let mdns = mdns::tokio::Behaviour::new(
                    mdns::Config::default(),
                    key.public().to_peer_id(),
                )
                .expect("mdns behaviour");

                Ok(AgentsBehaviour { gossipsub, mdns })
            })?
            .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(60)))
            .build();

        // -- Subscribe to topics ----------------------------------------------
        for topic_str in [TOPIC_CLAIMS, TOPIC_BLOCKS, TOPIC_CONTROL, TOPIC_PEERS] {
            let topic = IdentTopic::new(topic_str);
            swarm
                .behaviour_mut()
                .gossipsub
                .subscribe(&topic)
                .with_context(|| format!("failed to subscribe to {topic_str}"))?;
        }

        // -- Listen -----------------------------------------------------------
        let addr: Multiaddr = listen_addr.unwrap_or_else(|| {
            "/ip4/0.0.0.0/tcp/0".parse().expect("valid multiaddr")
        });
        swarm.listen_on(addr)?;

        // -- Outbound channel -------------------------------------------------
        let mut rx = self.rx.take().context("P2p::run called twice")?;

        info!("P2P node starting (node_id={})", self.cfg.node_id);

        // -- Event loop -------------------------------------------------------
        loop {
            tokio::select! {
                // Outbound: publish claim or block
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

                // Inbound: swarm events
                event = swarm.next() => {
                    let Some(event) = event else { break };
                    match event {
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
                                swarm
                                    .behaviour_mut()
                                    .gossipsub
                                    .add_explicit_peer(&peer_id);
                            }
                        }
                        SwarmEvent::Behaviour(AgentsBehaviourEvent::Mdns(
                            mdns::Event::Expired(peers),
                        )) => {
                            for (peer_id, _) in peers {
                                swarm
                                    .behaviour_mut()
                                    .gossipsub
                                    .remove_explicit_peer(&peer_id);
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
        Ok(())
    }
}

// -- Helpers ------------------------------------------------------------------

/// Serialise `value` as JSON and publish to `topic`.
fn publish_json<T: serde::Serialize>(
    gossipsub: &mut gossipsub::Behaviour,
    topic_str: &str,
    value: &T,
) -> Result<()> {
    let data = serde_json::to_vec(value).context("serialise outbound message")?;
    let topic = IdentTopic::new(topic_str);
    gossipsub
        .publish(topic, data)
        .context("gossipsub publish")?;
    Ok(())
}

/// Route an inbound gossipsub message to the mempool (claims) or store.
/// Errors are logged and swallowed — a bad message must not crash the loop.
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
                    // Verify Ed25519 signature before accepting
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
            // Phase 3: control-set distribution and peer metadata
            info!("received {topic} message ({} bytes)", message.data.len());
        }
        other => warn!("unknown topic: {other}"),
    }
}

// -- Convenience publish functions (called from outside the event loop) -------

/// Publish a claim to the network via the outbound channel.
pub async fn publish_claim(tx: &mpsc::Sender<OutboundMsg>, claim: StoredClaim) -> Result<()> {
    tx.send(OutboundMsg::Claim(claim))
        .await
        .context("outbound channel closed")
}

/// Publish a block to the network via the outbound channel.
pub async fn publish_block(tx: &mpsc::Sender<OutboundMsg>, block: StoredBlock) -> Result<()> {
    tx.send(OutboundMsg::Block(block))
        .await
        .context("outbound channel closed")
}
