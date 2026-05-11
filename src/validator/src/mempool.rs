//! Claim mempool and block producer.
//!
//! ClaimMempool collects incoming claims, scores each with S_con, and keeps
//! them sorted by score descending. BlockProducer drains the mempool when
//! either a minimum claim count or a timeout is reached, assembles a
//! StoredBlock, persists it, and publishes it to the network.
//!
//! Block assembly (DevDocs §5 / PoISV §3.5):
//!   hash        = SHA-256(sorted claim_ids + timestamp)
//!   psi         = compute_psi(error_vectors)   [stub: 1.0 until control set]
//!   weight      = psi * sum(s_con_scores)
//!   cumulative  = parent cumulative_weight + weight

use std::collections::BinaryHeap;
use std::cmp::Ordering;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use anyhow::Result;
use sha2::{Digest, Sha256};
use tokio::sync::mpsc;
use tokio::time::{interval, Instant};
use tracing::{info, warn};

use crate::config::ProtocolConfig;
use crate::network::{publish_block, OutboundMsg};
use crate::storage::{DagStore, StoredBlock, StoredClaim};
use crate::validation::compute_s_con;

// -- ScoredClaim --------------------------------------------------------------

/// A claim paired with its S_con score for heap ordering.
#[derive(Debug, Clone)]
pub struct ScoredClaim {
    pub claim: StoredClaim,
    pub score: f64,
}

// Max-heap by score (highest S_con first).
impl PartialEq for ScoredClaim {
    fn eq(&self, other: &Self) -> bool {
        self.score == other.score
    }
}
impl Eq for ScoredClaim {}
impl PartialOrd for ScoredClaim {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}
impl Ord for ScoredClaim {
    fn cmp(&self, other: &Self) -> Ordering {
        self.score
            .partial_cmp(&other.score)
            .unwrap_or(Ordering::Equal)
    }
}

// -- ClaimMempool -------------------------------------------------------------

/// Thread-safe mempool. Claims are scored on insertion and kept in a max-heap.
pub struct ClaimMempool {
    inner: Arc<Mutex<BinaryHeap<ScoredClaim>>>,
    cfg: ProtocolConfig,
}

impl ClaimMempool {
    pub fn new(cfg: ProtocolConfig) -> Self {
        Self {
            inner: Arc::new(Mutex::new(BinaryHeap::new())),
            cfg,
        }
    }

    /// Score `claim` with S_con against `corpus` and insert into the heap.
    /// Uses the stub embedder; swap in an ONNX embedder for production.
    pub fn insert(&self, claim: StoredClaim, corpus: &[&str]) {
        use crate::validation::stub_embed;
        let score = compute_s_con(&claim.statement, corpus, stub_embed, self.cfg.tau);
        let scored = ScoredClaim { claim, score };
        self.inner.lock().unwrap().push(scored);
    }

    /// Drain up to `max` claims from the heap (highest scores first).
    pub fn drain(&self, max: usize) -> Vec<ScoredClaim> {
        let mut heap = self.inner.lock().unwrap();
        let mut out = Vec::with_capacity(max.min(heap.len()));
        for _ in 0..max {
            match heap.pop() {
                Some(sc) => out.push(sc),
                None => break,
            }
        }
        out
    }

    /// Current number of pending claims.
    pub fn len(&self) -> usize {
        self.inner.lock().unwrap().len()
    }

    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Shared handle — clone to pass into the network receive path.
    pub fn handle(&self) -> Arc<Mutex<BinaryHeap<ScoredClaim>>> {
        self.inner.clone()
    }
}

// -- BlockProducer ------------------------------------------------------------

/// Assembles blocks from the mempool and publishes them.
///
/// Triggers when either:
///   - `min_claims` claims are pending, or
///   - `timeout` has elapsed since the last block (even with fewer claims).
pub struct BlockProducer {
    cfg: ProtocolConfig,
    mempool: Arc<ClaimMempool>,
    store: Arc<DagStore>,
    net_tx: mpsc::Sender<OutboundMsg>,
    /// Minimum claims before producing a block.
    pub min_claims: usize,
    /// Maximum wait before producing a block regardless of claim count.
    pub timeout: Duration,
    /// Corpus used for S_con scoring (stub: empty = score 0 for all).
    pub corpus: Vec<String>,
}

impl BlockProducer {
    pub fn new(
        cfg: ProtocolConfig,
        mempool: Arc<ClaimMempool>,
        store: Arc<DagStore>,
        net_tx: mpsc::Sender<OutboundMsg>,
    ) -> Self {
        let min_claims = cfg.min_claims_per_block;
        let timeout = Duration::from_secs(cfg.block_timeout_secs);
        Self {
            cfg,
            mempool,
            store,
            net_tx,
            min_claims,
            timeout,
            corpus: Vec::new(),
        }
    }

    /// Run the producer loop. Returns only on error or channel close.
    pub async fn run(self) -> Result<()> {
        let mut ticker = interval(Duration::from_secs(1));
        let mut last_block = Instant::now();

        info!(
            "BlockProducer started (min_claims={}, timeout={:?})",
            self.min_claims, self.timeout
        );

        loop {
            ticker.tick().await;

            let pending = self.mempool.len();
            let elapsed = last_block.elapsed();
            let timed_out = elapsed >= self.timeout && pending > 0;

            if pending >= self.min_claims || timed_out {
                match self.produce_block().await {
                    Ok(hash) => {
                        info!("produced block {hash} ({pending} claims)");
                        last_block = Instant::now();
                    }
                    Err(e) => warn!("block production failed: {e}"),
                }
            }
        }
    }

    /// Drain mempool, assemble block, persist, publish.
    async fn produce_block(&self) -> Result<String> {
        let scored = self.mempool.drain(self.cfg.max_claims_per_block);
        if scored.is_empty() {
            anyhow::bail!("mempool empty");
        }

        let timestamp = chrono::Utc::now().to_rfc3339();
        let claim_ids: Vec<String> = scored.iter().map(|sc| sc.claim.id.clone()).collect();
        let s_con_scores: Vec<f64> = scored.iter().map(|sc| sc.score).collect();

        // psi stub = 1.0 until control-set distribution is implemented (Phase 3)
        let psi = 1.0f64;
        let weight = psi * s_con_scores.iter().sum::<f64>();

        // hash = SHA-256(claim_ids joined + timestamp)
        let hash_input = format!("{}{}", claim_ids.join(","), timestamp);
        let hash = format!("{:x}", Sha256::digest(hash_input.as_bytes()));

        let block = StoredBlock {
            hash: hash.clone(),
            parent_hashes: vec![], // Phase 3: wire up GHOSTDAG parent selection
            timestamp,
            psi,
            cumulative_weight: weight,
            claim_ids,
        };

        self.store.save_block(&block)?;
        publish_block(&self.net_tx, block).await?;

        Ok(hash)
    }
}

// -- Tests --------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::ProtocolConfig;

    fn cfg() -> ProtocolConfig {
        ProtocolConfig::load().unwrap()
    }

    fn claim(id: &str, statement: &str) -> StoredClaim {
        StoredClaim {
            id: id.to_string(),
            protocol: "agentsprotocol".to_string(),
            version: "1.0".to_string(),
            timestamp: "2026-04-18T14:30:00Z".to_string(),
            submitter: "0xpubkey".to_string(),
            signature: "0xsig".to_string(),
            statement: statement.to_string(),
            payload_json: "{}".to_string(),
        }
    }

    #[test]
    fn mempool_insert_and_drain() {
        let pool = ClaimMempool::new(cfg());
        let corpus = ["The sky is blue.", "Water boils at 100C."];
        pool.insert(claim("c1", "The sky is blue."), &corpus);
        pool.insert(claim("c2", "Water boils at 100C."), &corpus);
        pool.insert(claim("c3", "unrelated xyz"), &corpus);

        assert_eq!(pool.len(), 3);
        let drained = pool.drain(10);
        assert_eq!(drained.len(), 3);
        assert!(pool.is_empty());

        // highest scores first
        assert!(drained[0].score >= drained[1].score);
        assert!(drained[1].score >= drained[2].score);
    }

    #[test]
    fn mempool_drain_respects_max() {
        let pool = ClaimMempool::new(cfg());
        let corpus: &[&str] = &[];
        for i in 0..10 {
            pool.insert(claim(&format!("c{i}"), "claim"), corpus);
        }
        let drained = pool.drain(4);
        assert_eq!(drained.len(), 4);
        assert_eq!(pool.len(), 6);
    }

    #[test]
    fn mempool_empty_drain_returns_empty() {
        let pool = ClaimMempool::new(cfg());
        assert_eq!(pool.drain(10).len(), 0);
    }

    #[test]
    fn scored_claim_ordering() {
        let high = ScoredClaim { claim: claim("h", "x"), score: 0.9 };
        let low  = ScoredClaim { claim: claim("l", "x"), score: 0.1 };
        assert!(high > low);
    }
}
