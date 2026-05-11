//! GHOSTDAG consensus — parent selection and block weight.
//!
//! Reference: Sompolinsky, Wyborski, Zohar, AFT 2021.
//! Block weight: Weight(B) = Psi_B * sum_A S_con(A)  (PoISV §3.5 / DevDocs §5.2)
//!
//! Parent selection (simplified greedy GHOSTDAG):
//!   1. Collect the last `parent_candidate_window` blocks from the DAG.
//!   2. Rank by block_weight() descending.
//!   3. Return the top-k hashes (k = cfg.ghostdag_k).
//!
//! This is the greedy approximation used in Kaspa's reference implementation.
//! Full GHOSTDAG (blue-set computation) is Phase 4.

use anyhow::Result;
use tracing::warn;

use crate::config::ProtocolConfig;
use crate::storage::DagStore;

pub struct Ghostdag<'a> {
    pub cfg: ProtocolConfig,
    pub store: &'a DagStore,
}

impl<'a> Ghostdag<'a> {
    pub fn new(cfg: ProtocolConfig, store: &'a DagStore) -> Self {
        Self { cfg, store }
    }

    /// Weight(B) = Psi_B * sum_A S_con(A)
    pub fn block_weight(&self, psi: f64, s_cons: &[f64]) -> f64 {
        psi * s_cons.iter().sum::<f64>()
    }

    /// Select up to `cfg.ghostdag_k` parent hashes for a new block.
    ///
    /// Reads the last `cfg.parent_candidate_window` blocks, ranks them by
    /// `cumulative_weight` descending, and returns the top-k hashes.
    /// Returns an empty Vec if the DAG is empty (genesis block case).
    pub fn select_parents(&self) -> Vec<String> {
        match self.select_parents_inner() {
            Ok(parents) => parents,
            Err(e) => {
                warn!("select_parents failed, using empty parent list: {e}");
                Vec::new()
            }
        }
    }

    fn select_parents_inner(&self) -> Result<Vec<String>> {
        let window = self.cfg.parent_candidate_window;
        let k = self.cfg.ghostdag_k;

        let mut candidates = self.store.list_recent_blocks(window)?;

        // Sort by cumulative_weight descending — highest-weight chain tips first.
        candidates.sort_by(|a, b| {
            b.cumulative_weight
                .partial_cmp(&a.cumulative_weight)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        let parents: Vec<String> = candidates
            .into_iter()
            .take(k)
            .map(|b| b.hash)
            .collect();

        Ok(parents)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::storage::StoredBlock;
    use tempfile::TempDir;

    fn cfg() -> ProtocolConfig {
        ProtocolConfig::load().unwrap()
    }

    fn open_store(dir: &TempDir) -> DagStore {
        DagStore::open(dir.path()).unwrap()
    }

    fn block(hash: &str, weight: f64) -> StoredBlock {
        StoredBlock {
            hash: hash.to_string(),
            parent_hashes: vec![],
            timestamp: "2026-04-18T14:30:00Z".to_string(),
            psi: 1.0,
            cumulative_weight: weight,
            claim_ids: vec![],
            zk_proof: None,
        }
    }

    #[test]
    fn select_parents_empty_dag() {
        let dir = TempDir::new().unwrap();
        let store = open_store(&dir);
        let dag = Ghostdag::new(cfg(), &store);
        assert!(dag.select_parents().is_empty());
    }

    #[test]
    fn select_parents_returns_top_k_by_weight() {
        let dir = TempDir::new().unwrap();
        let store = open_store(&dir);
        store.save_block(&block("low",  1.0)).unwrap();
        store.save_block(&block("mid",  5.0)).unwrap();
        store.save_block(&block("high", 9.0)).unwrap();

        let mut cfg = cfg();
        cfg.ghostdag_k = 2;
        let dag = Ghostdag::new(cfg, &store);
        let parents = dag.select_parents();

        assert_eq!(parents.len(), 2);
        assert_eq!(parents[0], "high");
        assert_eq!(parents[1], "mid");
    }

    #[test]
    fn select_parents_respects_k_limit() {
        let dir = TempDir::new().unwrap();
        let store = open_store(&dir);
        for i in 0..10u32 {
            store.save_block(&block(&format!("b{i}"), i as f64)).unwrap();
        }
        let mut cfg = cfg();
        cfg.ghostdag_k = 3;
        let dag = Ghostdag::new(cfg, &store);
        assert_eq!(dag.select_parents().len(), 3);
    }

    #[test]
    fn block_weight_formula() {
        let dir = TempDir::new().unwrap();
        let store = open_store(&dir);
        let dag = Ghostdag::new(cfg(), &store);
        assert!((dag.block_weight(0.9, &[0.8, 0.7, 0.6]) - 0.9 * 2.1).abs() < 1e-10);
        assert_eq!(dag.block_weight(0.0, &[1.0, 1.0]), 0.0);
    }
}
